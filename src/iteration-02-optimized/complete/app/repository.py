"""Repository: every Cosmos call goes through here. Captures the RU charge
from the response headers so the service layer can surface it.

The repository is split by container, mirroring the iteration-2 design:

* ``CustomerOrdersRepository`` — single container, ``/customerId`` partition,
  two document ``type``s.
* ``ProductsRepository``       — single container, ``/categoryId`` partition.
"""

from __future__ import annotations

import json
import os
import urllib3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv

# Load /src/.env (copy /src/.env.example -> /src/.env on first run).
SRC_DIR = Path(__file__).resolve().parents[3]
load_dotenv(SRC_DIR / ".env")

EMULATOR_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
EMULATOR_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310DB-i2")

if not EMULATOR_ENDPOINT or not EMULATOR_KEY:
    raise RuntimeError(
        "COSMOS_ENDPOINT / COSMOS_KEY not set. "
        "Copy src/.env.example to src/.env, then re-run."
    )

CUSTOMER_ORDERS = "CustomerOrders"
PRODUCTS = "Products"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Result:
    """Wraps a query/read result so service callers can log RU charges,
    server-reported item count, and query metrics."""

    items: list[dict]
    request_charge: float
    item_count: int = 0
    query_metrics: str = ""


def _last_charge(container) -> float:
    return float(
        container.client_connection.last_response_headers.get(
            "x-ms-request-charge", 0.0
        )
    )


def _capture(container) -> dict:
    """Pull the three diagnostic headers off the most recent response:

    * ``x-ms-request-charge``        — RU cost
    * ``x-ms-item-count``            — number of docs the server returned
    * ``x-ms-documentdb-query-metrics`` — engine-level breakdown
      (retrieved/output doc counts, index hit count, timings)

    Returned as kwargs ready to splat into ``Result(items=..., **_capture(c))``.
    """
    h = container.client_connection.last_response_headers
    return {
        "request_charge": float(h.get("x-ms-request-charge", 0.0) or 0.0),
        "item_count":     int(h.get("x-ms-item-count", 0) or 0),
        "query_metrics":  h.get("x-ms-documentdb-query-metrics", "") or "",
    }


def get_client() -> CosmosClient:
    return CosmosClient(
        EMULATOR_ENDPOINT,
        credential=EMULATOR_KEY,
        connection_verify=False,
    )


def get_database():
    return get_client().get_database_client(DATABASE_NAME)


class CustomerOrdersRepository:
    """All reads/writes against the CustomerOrders container."""

    def __init__(self) -> None:
        self._container = get_database().get_container_client(CUSTOMER_ORDERS)

    # ---- reads ---------------------------------------------------------
    def get_customer_and_orders(self, customer_id: str) -> Result:
        """Single query — one partition — returns customer + all orders."""
        items = list(
            self._container.query_items(
                query="SELECT * FROM c WHERE c.customerId = @cid",
                parameters=[{"name": "@cid", "value": customer_id}],
                partition_key=customer_id,
                populate_query_metrics=True,
            )
        )
        return Result(items=items, **_capture(self._container))

    def get_customer_doc(self, customer_id: str) -> Result:
        """Point-read **only** the customer document.

        Both the document's ``id`` and its partition-key value are the
        customer id, so this is a 1.0 RU point read — it pulls a single
        document out of the partition instead of returning every order
        the customer has ever placed (the cost of which scales with
        partition size). Use this any time you only need the
        ``customer`` doc (e.g. to update ``orderSummary`` before a
        transactional batch).
        """
        try:
            item = self._container.read_item(
                item=customer_id, partition_key=customer_id
            )
            items = [item]
        except CosmosResourceNotFoundError:
            items = []
        return Result(items=items, **_capture(self._container))

    def get_recent_orders(self, customer_id: str, top: int = 5) -> Result:
        items = list(
            self._container.query_items(
                query=(
                    "SELECT TOP @n * FROM c WHERE c.customerId = @cid "
                    "AND c.type = 'order' ORDER BY c.orderDate DESC"
                ),
                parameters=[
                    {"name": "@n", "value": top},
                    {"name": "@cid", "value": customer_id},
                ],
                partition_key=customer_id,
                populate_query_metrics=True,
            )
        )
        return Result(items=items, **_capture(self._container))

    def get_order(self, customer_id: str, order_id: str) -> Result:
        try:
            item = self._container.read_item(
                item=order_id, partition_key=customer_id
            )
            items = [item]
        except CosmosResourceNotFoundError:
            items = []
        # Point reads don't surface item-count or query-metrics headers,
        # so _capture safely returns 0 / "" for those fields.
        return Result(items=items, **_capture(self._container))

    def get_order_via_query(self, customer_id: str, order_id: str) -> Result:
        """Fetch the same single document via a SQL query filtered by
        partition key + id. Functionally identical to ``get_order`` but
        goes through the query engine — included so callers can compare
        the RU charge against the point read.
        """
        items = list(
            self._container.query_items(
                query=(
                    "SELECT * FROM c WHERE c.customerId = @cid "
                    "AND c.id = @oid"
                ),
                parameters=[
                    {"name": "@cid", "value": customer_id},
                    {"name": "@oid", "value": order_id},
                ],
                partition_key=customer_id,
                populate_query_metrics=True,
            )
        )
        return Result(items=items, **_capture(self._container))

    # ---- writes --------------------------------------------------------
    def place_order_transactional(
        self,
        customer_id: str,
        customer_doc: dict,
        order_doc: dict,
    ) -> float:
        """Atomically update the customer's summary AND create the order.

        Both documents share ``customerId`` as their partition key, so a
        single transactional batch covers them.
        """
        batch = [
            ("upsert", (customer_doc,)),
            ("create", (order_doc,)),
        ]
        self._container.execute_item_batch(
            batch_operations=batch,
            partition_key=customer_id,
        )
        return _last_charge(self._container)


class ProductsRepository:
    """All reads/writes against the Products container."""

    def __init__(self) -> None:
        self._container = get_database().get_container_client(PRODUCTS)

    def list_in_category(self, category_id: str) -> Result:
        items = list(
            self._container.query_items(
                query=(
                    "SELECT c.productId, c.name, c.price, c.rating "
                    "FROM c WHERE c.categoryId = @cid ORDER BY c.price ASC"
                ),
                parameters=[{"name": "@cid", "value": category_id}],
                partition_key=category_id,
                populate_query_metrics=True,
            )
        )
        return Result(items=items, **_capture(self._container))

    def pick_a_few(self, category_id: str, n: int = 3) -> Result:
        items = list(
            self._container.query_items(
                query=(
                    "SELECT TOP @n c.productId, c.name, c.categoryId, c.price "
                    "FROM c WHERE c.categoryId = @cid"
                ),
                parameters=[
                    {"name": "@n", "value": n},
                    {"name": "@cid", "value": category_id},
                ],
                partition_key=category_id,
                populate_query_metrics=True,
            )
        )
        return Result(items=items, **_capture(self._container))

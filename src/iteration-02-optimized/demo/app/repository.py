"""Repository — DEMO skeleton.

The two repository classes wrap CustomerOrders and Products. Each method
should:

  * issue exactly one Cosmos call,
  * pass the right `partition_key=` so the query is in-partition,
  * capture x-ms-request-charge from the response headers so the service
    layer can print the RU cost.

See complete/app/repository.py for the reference implementation.
"""

from __future__ import annotations

import os
import urllib3
from dataclasses import dataclass
from pathlib import Path

from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load /src/.env (copy /src/.env.example -> /src/.env on first run).
SRC_DIR = Path(__file__).resolve().parents[3]
load_dotenv(SRC_DIR / ".env")

EMULATOR_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
EMULATOR_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310")

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
    items: list[dict]
    request_charge: float
    item_count: int = 0
    query_metrics: str = ""


def get_client() -> CosmosClient:
    return CosmosClient(
        EMULATOR_ENDPOINT,
        credential=EMULATOR_KEY,
        connection_verify=False,
    )


class CustomerOrdersRepository:
    def __init__(self) -> None:
        # TODO (demo): grab the CustomerOrders container client
        ...

    def get_customer_and_orders(self, customer_id: str) -> Result:
        # TODO (demo): single-partition query, return customer + orders
        return Result(items=[], request_charge=0.0)

    def get_order(self, customer_id: str, order_id: str) -> Result:
        # TODO (demo): point read on the order document
        return Result(items=[], request_charge=0.0)

    def place_order_transactional(
        self, customer_id: str, customer_doc: dict, order_doc: dict
    ) -> float:
        # TODO (demo): use execute_item_batch with two ops:
        #   ("upsert", (customer_doc,)) and ("create", (order_doc,))
        return 0.0


class ProductsRepository:
    def __init__(self) -> None:
        # TODO (demo): grab the Products container client
        ...

    def list_in_category(self, category_id: str) -> Result:
        # TODO (demo): single-partition query ordered by price ASC
        return Result(items=[], request_charge=0.0)

    def pick_a_few(self, category_id: str, n: int = 3) -> Result:
        # TODO (demo): TOP @n products in the category
        return Result(items=[], request_charge=0.0)

"""Iteration 3: run R-EXT-1, R-EXT-2, R-EXT-3 and (optionally) apply the
upgraded indexing policy to the iteration-2 containers.

    python complete/queries.py --apply-policy   # one-time: install composites
    python complete/queries.py                  # run the three queries
"""

from __future__ import annotations

import json
import os
import sys
import urllib3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load /src/.env (copy /src/.env.example -> /src/.env on first run).
SRC_DIR = Path(__file__).resolve().parents[2]
load_dotenv(SRC_DIR / ".env")

EMULATOR_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
EMULATOR_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310")

if not EMULATOR_ENDPOINT or not EMULATOR_KEY:
    raise RuntimeError(
        "COSMOS_ENDPOINT / COSMOS_KEY not set. "
        "Copy src/.env.example to src/.env, then re-run."
    )

POLICY_FILE = Path(__file__).resolve().parent / "indexing-policy.json"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _client():
    return CosmosClient(
        EMULATOR_ENDPOINT, credential=EMULATOR_KEY, connection_verify=False
    )


def _ru(container) -> float:
    return float(
        container.client_connection.last_response_headers.get(
            "x-ms-request-charge", 0.0
        )
    )


# Pull all three diagnostic headers off the most recent response.
# x-ms-request-charge          — RU cost
# x-ms-item-count              — server-reported result count
# x-ms-documentdb-query-metrics — engine breakdown (retrieved/output docs, timings)
_METRIC_KEYS = (
    "retrievedDocumentCount",
    "outputDocumentCount",
    "indexHitDocumentCount",
    "totalExecutionTimeInMs",
)


def _capture(container) -> tuple[float, int, str]:
    h = container.client_connection.last_response_headers
    ru = float(h.get("x-ms-request-charge", 0.0) or 0.0)
    count = int(h.get("x-ms-item-count", 0) or 0)
    metrics = h.get("x-ms-documentdb-query-metrics", "") or ""
    return ru, count, metrics


def _format_metrics(metrics: str) -> str:
    if not metrics:
        return ""
    parts = dict(p.split("=", 1) for p in metrics.split(";") if "=" in p)
    return " ".join(f"{k}={parts[k]}" for k in _METRIC_KEYS if k in parts)


def _print(label: str, ru: float, count: int) -> None:
    print(f"  [RU] {label:<55} {ru:>8.2f}  ({count} docs)")


def _print_q(label: str, ru: float, client_count: int, server_count: int,
             metrics: str) -> None:
    print(
        f"  [RU] {label:<55} {ru:>8.2f}  "
        f"(client={client_count} docs, server item-count={server_count})"
    )
    summary = _format_metrics(metrics)
    if summary:
        print(f"       metrics: {summary}")


# --- policy management --------------------------------------------------
def apply_policy() -> None:
    with POLICY_FILE.open("r", encoding="utf-8") as fh:
        policies = json.load(fh)
    db = _client().get_database_client(DATABASE_NAME)
    for container_name, policy in policies.items():
        c = db.get_container_client(container_name)
        props = c.read()
        props["indexingPolicy"] = policy
        db.replace_container(container=c, partition_key=props["partitionKey"],
                             indexing_policy=policy)
        print(f"Updated indexing policy on {container_name}: "
              f"{len(policy.get('compositeIndexes', []))} composite index(es)")


# --- queries ------------------------------------------------------------
def r_ext_1(db) -> None:
    print("\nR-EXT-1 — customer order history by date range")
    c = db.get_container_client("CustomerOrders")
    now = datetime.now(timezone.utc)
    end = now.isoformat()
    start = (now - timedelta(days=180)).isoformat()
    items = list(
        c.query_items(
            query=(
                "SELECT c.orderId, c.orderDate, c.totalAmount FROM c "
                "WHERE c.type = 'order' AND c.customerId = @cid "
                "AND c.orderDate >= @from AND c.orderDate < @to "
                "ORDER BY c.orderDate DESC"
            ),
            parameters=[
                {"name": "@cid", "value": "C00005"},
                {"name": "@from", "value": start},
                {"name": "@to", "value": end},
            ],
            partition_key="C00005",
            populate_query_metrics=True,
        )
    )
    ru, server_count, metrics = _capture(c)
    _print_q("orders for C00005 (last 180d, DESC)", ru, len(items), server_count, metrics)


def r_ext_2(db) -> None:
    print("\nR-EXT-2 — open-orders dashboard (cross-partition)")
    c = db.get_container_client("CustomerOrders")
    items = list(
        c.query_items(
            query=(
                "SELECT TOP 25 c.orderId, c.customerId, c.orderDate, c.totalAmount "
                "FROM c WHERE c.type = 'order' AND c.status = @s "
                "ORDER BY c.orderDate DESC"
            ),
            parameters=[{"name": "@s", "value": "Placed"}],
            enable_cross_partition_query=True,
            populate_query_metrics=True,
        )
    )
    ru, server_count, metrics = _capture(c)
    _print_q("top-25 Placed orders DESC", ru, len(items), server_count, metrics)


def r_ext_3(db) -> None:
    print("\nR-EXT-3 — products by rating DESC, price ASC")
    c = db.get_container_client("Products")
    items = list(
        c.query_items(
            query=(
                "SELECT c.productId, c.name, c.rating, c.price FROM c "
                "WHERE c.categoryId = @cid "
                "ORDER BY c.rating DESC, c.price ASC"
            ),
            parameters=[{"name": "@cid", "value": "CAT006"}],
            partition_key="CAT006",
            populate_query_metrics=True,
        )
    )
    ru, server_count, metrics = _capture(c)
    _print_q("products in CAT006 by rating/price", ru, len(items), server_count, metrics)


def main(argv: list[str]) -> int:
    if "--apply-policy" in argv:
        apply_policy()
        return 0

    db = _client().get_database_client(DATABASE_NAME)
    print("=" * 70)
    print("Iteration 3 — composite indexes")
    print("=" * 70)
    r_ext_1(db)
    r_ext_2(db)
    r_ext_3(db)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

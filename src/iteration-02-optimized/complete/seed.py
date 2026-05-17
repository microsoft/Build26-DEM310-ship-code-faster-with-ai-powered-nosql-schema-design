"""Iteration 2 seed: create CustomerOrders + Products and bulk-insert from
the master JSON.

    python complete/seed.py

Reshapes each master document into the iteration-2 layout:

    customers.json + orders.json -> CustomerOrders (type discriminator)
    products.json                -> Products       (partitioned by /categoryId)

The customer document also embeds an ``orderSummary`` rolled up from the
master orders so iteration-2 reads are truly single-doc.
"""

from __future__ import annotations

import json
from pathlib import Path

from azure.cosmos import PartitionKey

from app.repository import (
    CUSTOMER_ORDERS,
    DATABASE_NAME,
    PRODUCTS,
    get_client,
)

MASTER_DIR = Path(__file__).resolve().parents[2] / "sample-data" / "master"
POLICY_FILE = Path(__file__).resolve().parent / "indexing-policy.json"


def _load(name: str) -> list[dict]:
    with (MASTER_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _summary_for(customer_id: str, all_orders: list[dict]) -> dict:
    cust_orders = [o for o in all_orders if o["customerId"] == customer_id]
    if not cust_orders:
        return {"lifetimeOrders": 0, "lifetimeRevenue": 0.0, "lastOrderDate": None}
    return {
        "lifetimeOrders": len(cust_orders),
        "lifetimeRevenue": round(sum(o["totalAmount"] for o in cust_orders), 2),
        "lastOrderDate": max(o["orderDate"] for o in cust_orders),
    }


def main() -> None:
    client = get_client()
    db = client.create_database_if_not_exists(DATABASE_NAME)

    with POLICY_FILE.open("r", encoding="utf-8") as fh:
        policy = json.load(fh)

    customer_orders = db.create_container_if_not_exists(
        id=CUSTOMER_ORDERS,
        partition_key=PartitionKey(path="/customerId"),
        offer_throughput=400,
        indexing_policy=policy,
    )
    products = db.create_container_if_not_exists(
        id=PRODUCTS,
        partition_key=PartitionKey(path="/categoryId"),
        offer_throughput=400,
        indexing_policy=policy,
    )

    customers = _load("customers")
    orders = _load("orders")
    product_rows = _load("products")

    # --- CustomerOrders: customer docs (with embedded summary) ----------
    for c in customers:
        doc = {
            "id": c["customerId"],
            "type": "customer",
            **c,
            "orderSummary": _summary_for(c["customerId"], orders),
        }
        customer_orders.upsert_item(doc)

    # --- CustomerOrders: order docs (items embedded) --------------------
    for o in orders:
        doc = {"id": o["orderId"], "type": "order", **o}
        customer_orders.upsert_item(doc)

    # --- Products -------------------------------------------------------
    for p in product_rows:
        doc = {"id": p["productId"], "type": "product", **p}
        products.upsert_item(doc)

    print(
        f"Seeded CustomerOrders ({len(customers)} customers + {len(orders)} orders) "
        f"and Products ({len(product_rows)} items)"
    )


if __name__ == "__main__":
    main()

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
import sys
from pathlib import Path

from azure.cosmos import PartitionKey

# Ensure em-dashes and ellipses in console output render correctly on
# Windows PowerShell (default code page is not UTF-8).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

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
    print("=" * 70)
    print("Iteration 2 seed — CustomerOrders + Products")
    print("=" * 70)

    client = get_client()
    db = client.create_database_if_not_exists(DATABASE_NAME)
    print(f"  database ............... {DATABASE_NAME}")

    with POLICY_FILE.open("r", encoding="utf-8") as fh:
        policy = json.load(fh)
    print(f"  indexing-policy file ... {POLICY_FILE.name}")

    customer_orders = db.create_container_if_not_exists(
        id=CUSTOMER_ORDERS,
        partition_key=PartitionKey(path="/customerId"),
        offer_throughput=400,
        indexing_policy=policy,
    )
    print(f"  container .............. {CUSTOMER_ORDERS}  (PK=/customerId, RU/s=400)")
    products = db.create_container_if_not_exists(
        id=PRODUCTS,
        partition_key=PartitionKey(path="/categoryId"),
        offer_throughput=400,
        indexing_policy=policy,
    )
    print(f"  container .............. {PRODUCTS}  (PK=/categoryId, RU/s=400)")

    customers = _load("customers")
    orders = _load("orders")
    product_rows = _load("products")
    print(
        f"  master data ............ {len(customers)} customers, "
        f"{len(orders)} orders, {len(product_rows)} products"
    )

    print("\nLoading CustomerOrders…")
    # --- CustomerOrders: customer docs (with embedded summary) ----------
    for c in customers:
        doc = {
            "id": c["customerId"],
            "type": "customer",
            **c,
            "orderSummary": _summary_for(c["customerId"], orders),
        }
        customer_orders.upsert_item(doc)
    print(f"  upserted {len(customers):>4} customer docs (with embedded orderSummary)")

    # --- CustomerOrders: order docs (items embedded) --------------------
    for o in orders:
        doc = {"id": o["orderId"], "type": "order", **o}
        customer_orders.upsert_item(doc)
    print(f"  upserted {len(orders):>4} order    docs (items[] embedded)")

    # --- Products -------------------------------------------------------
    print("\nLoading Products…")
    for p in product_rows:
        doc = {"id": p["productId"], "type": "product", **p}
        products.upsert_item(doc)
    print(f"  upserted {len(product_rows):>4} product  docs")

    # --- Verify a sample of each shape ----------------------------------
    sample_cid = customers[0]["customerId"]
    sample_oid = next(
        (o["orderId"] for o in orders if o["customerId"] == sample_cid),
        None,
    )
    print("\nSample documents (verify embedded shapes):")
    cust = customer_orders.read_item(item=sample_cid, partition_key=sample_cid)
    print(
        f"  customer {sample_cid}: type={cust.get('type')!r}, "
        f"orderSummary.lifetimeOrders={cust.get('orderSummary', {}).get('lifetimeOrders')}, "
        f"orderSummary.lifetimeRevenue={cust.get('orderSummary', {}).get('lifetimeRevenue')}"
    )
    if sample_oid:
        order = customer_orders.read_item(item=sample_oid, partition_key=sample_cid)
        print(
            f"  order    {sample_oid}: type={order.get('type')!r}, "
            f"items={len(order.get('items', []))}, "
            f"totalAmount={order.get('totalAmount')}"
        )

    print()
    print(
        f"Seeded CustomerOrders ({len(customers)} customers + {len(orders)} orders) "
        f"and Products ({len(product_rows)} items)"
    )


if __name__ == "__main__":
    main()

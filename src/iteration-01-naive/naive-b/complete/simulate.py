"""Simulate the unbounded-array growth on a single customer document.

For each of N iterations:
  1. Read the customer doc (capture read RU + doc size).
  2. Build a new order with K line items pulled from the master catalog.
  3. Append the order to doc['orders'] and upsert the doc (capture upsert RU).

At the end, print a per-iteration table and a projection of how many more
iterations until the doc crosses the 2 MB Cosmos item limit.

Usage:
  python simulate.py                            # 50 iter, 50 items/order, customer C00005
  python simulate.py --iterations 30 --items-per-order 10 --customer C00003

Defaults push the document to ~315 KB across 50 iterations — large enough
that the classic Windows emulator's step-function RU billing becomes
visible (upsert RU climbs from ~16 RU to ~130 RU, read RU from 1 RU to
~10 RU). Smaller payloads stay below the first RU billing boundary
(~128 KB) and the growth is hidden behind fixed overhead.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

# Force UTF-8 stdout so non-ASCII characters render correctly under
# Windows PowerShell.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from azure.cosmos import exceptions

from shared import (
    CONTAINER_NAME,
    DATABASE_NAME,
    doc_size_bytes,
    get_client,
    last_ru,
    load_master,
)

ITEM_LIMIT_BYTES = 2 * 1024 * 1024   # Cosmos DB hard limit per item


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--customer", default="C00005",
                   help="customerId to grow (default: C00005)")
    p.add_argument("--iterations", type=int, default=50,
                   help="number of orders to append (default: 50)")
    p.add_argument("--items-per-order", type=int, default=50,
                   help="line items per appended order (default: 50)")
    return p.parse_args()


def build_order(order_seq: int, products: list[dict], items_per_order: int) -> dict:
    # Cycle through the catalog deterministically so re-runs match.
    chosen = [products[(order_seq * items_per_order + i) % len(products)]
              for i in range(items_per_order)]
    items = []
    total = 0.0
    for idx, p in enumerate(chosen, start=1):
        qty = 1 + (idx % 3)
        price = float(p.get("price", 0))
        items.append({
            "lineNumber": idx,
            "productId": p["productId"],
            "productName": p.get("name"),
            "unitPrice": price,
            "quantity": qty,
            "lineTotal": round(price * qty, 2),
        })
        total += price * qty

    order_id = f"O-SIM-{order_seq:05d}"
    return {
        "orderId": order_id,
        "orderDate": (datetime.now(timezone.utc)
                      - timedelta(days=20 - order_seq)).isoformat(),
        "status": "Placed",
        "subtotal": round(total, 2),
        "tax": round(total * 0.08, 2),
        "total": round(total * 1.08, 2),
        "items": items,
    }


def main() -> int:
    args = parse_args()

    client = get_client()
    try:
        db = client.get_database_client(DATABASE_NAME)
        container = db.get_container_client(CONTAINER_NAME)
        # Validate container exists by reading the seed doc once.
        container.read_item(item=args.customer, partition_key=args.customer)
    except exceptions.CosmosResourceNotFoundError:
        print(f"Customer '{args.customer}' not found in container "
              f"'{CONTAINER_NAME}'. Did you run `python seed.py` first?",
              file=sys.stderr)
        return 1

    products = load_master("products")

    print(f"\nGrowing customer '{args.customer}' for {args.iterations} "
          f"iterations ({args.items_per_order} items/order).\n")
    header = f"{'iter':>4}  {'doc KB':>8}  {'read RU':>8}  {'upsert RU':>10}  {'orders':>7}"
    print(header)
    print("-" * len(header))

    rows: list[tuple[int, float, float, float, int]] = []

    for i in range(1, args.iterations + 1):
        doc = container.read_item(item=args.customer,
                                  partition_key=args.customer)
        read_ru = last_ru(container)

        doc["orders"].append(build_order(i, products, args.items_per_order))
        container.upsert_item(doc)
        upsert_ru = last_ru(container)

        size_kb = doc_size_bytes(doc) / 1024.0
        rows.append((i, size_kb, read_ru, upsert_ru, len(doc["orders"])))
        print(f"{i:>4}  {size_kb:>8.2f}  {read_ru:>8.2f}  "
              f"{upsert_ru:>10.2f}  {len(doc['orders']):>7}")

    # Trend summary + projection to the 2 MB ceiling.
    print()
    first, last = rows[0], rows[-1]
    delta_kb = last[1] - first[1]
    delta_ru = last[3] - first[3]
    # Format deltas with an explicit sign so negative growth prints as
    # '-5.67' instead of the legacy '+-5.67'.
    def _signed(v: float) -> str:
        return f"{v:+.2f}"

    print(f"Growth across {args.iterations} iterations:")
    print(f"  doc size : {first[1]:.2f} KB  ->  {last[1]:.2f} KB   ({_signed(delta_kb)} KB)")
    print(f"  upsert RU: {first[3]:.2f}     ->  {last[3]:.2f}      ({_signed(delta_ru)} RU)")

    if args.iterations < 30 or args.items_per_order < 30:
        print(
            "\nNote: short / small-payload runs can show flat or even\n"
            "decreasing upsert RU because the doc stays under the\n"
            "emulator's first RU billing step (~128 KB). Re-run with\n"
            "defaults (--iterations 50 --items-per-order 50) to see the\n"
            "unbounded-array growth trend clearly."
        )

    per_iter_kb = delta_kb / max(args.iterations - 1, 1)
    if per_iter_kb > 0:
        remaining_kb = (ITEM_LIMIT_BYTES / 1024.0) - last[1]
        remaining_iters = int(remaining_kb / per_iter_kb)
        print(f"\nAt ~{per_iter_kb:.2f} KB / iteration this document will hit the")
        print(f"2 MB Cosmos item limit in ~{remaining_iters:,} more iterations.")
    else:
        print("\n(No measurable per-iteration growth — bump --items-per-order.)")

    print("\nThis is the unbounded-array anti-pattern. Iteration 2 splits the")
    print("orders into separate documents sharing the customerId partition key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

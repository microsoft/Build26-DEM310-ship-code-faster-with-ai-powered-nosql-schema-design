"""Deterministically build trimmed master JSON from AdventureWorksLT CSVs.

Usage
-----
    python -m sample_data.generate
    python generate.py
    python generate.py --seed 42 --customers 10 --orders-per-customer 20 \
                      --categories 5 --products-per-category 10 \
                      --max-lines-per-order 10

Output
------
Writes four JSON files to ``./master/``:

* ``customers.json``    -- ``--customers`` documents
* ``categories.json``   -- ``--categories`` documents
* ``products.json``     -- ``categories * products_per_category`` documents
* ``orders.json``       -- ``customers * orders_per_customer`` documents,
                          each with 1..``max_lines_per_order`` items[]

The output is the iteration-agnostic *master* shape. Each scenario's
``seed.py`` reshapes these documents into the container schema it needs.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE / "source"
MASTER_DIR = HERE / "master"

# Order dates are synthesized so the date-range read pattern (R-EXT-1)
# has useful results regardless of the historical SalesOrderHeader span.
ORDER_DATE_END = datetime(2026, 4, 30, tzinfo=timezone.utc)
ORDER_DATE_SPAN_DAYS = 730  # ~24 months


def _parse_decimal(raw: str) -> float:
    """AdventureWorksLT uses comma as the decimal separator inside quoted
    numeric fields (e.g. ``"1059,3100"``). Strip and convert."""
    raw = raw.strip().strip('"')
    if not raw:
        return 0.0
    return float(raw.replace(",", "."))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- customers --
def build_customers(rng: random.Random, count: int) -> list[dict[str, Any]]:
    rows = _read_csv(SOURCE_DIR / "Customer.csv")
    picked = rng.sample(rows, count)
    customers: list[dict[str, Any]] = []
    for row in picked:
        customers.append(
            {
                "customerId": f"C{int(row['CustomerID']):05d}",
                "title": row["Title"] or None,
                "firstName": row["FirstName"],
                "middleName": row["MiddleName"] or None,
                "lastName": row["LastName"],
                "companyName": row["CompanyName"] or None,
                "emailAddress": row["EmailAddress"],
                "phone": row["Phone"],
            }
        )
    customers.sort(key=lambda c: c["customerId"])
    return customers


# --------------------------------------------------------------- categories --
def build_categories(rng: random.Random, count: int) -> list[dict[str, Any]]:
    rows = _read_csv(SOURCE_DIR / "ProductCategory.csv")
    # Only categories that actually have products attached (= leaf categories).
    product_rows = _read_csv(SOURCE_DIR / "Product.csv")
    used_ids = {p["ProductCategoryID"] for p in product_rows if p["ProductCategoryID"]}
    leaves = [r for r in rows if r["ProductCategoryID"] in used_ids]
    picked = rng.sample(leaves, count)
    categories: list[dict[str, Any]] = []
    for row in picked:
        categories.append(
            {
                "categoryId": f"CAT{int(row['ProductCategoryID']):03d}",
                "name": row["Name"],
                "parentCategoryId": (
                    f"CAT{int(row['ParentProductCategoryID']):03d}"
                    if row["ParentProductCategoryID"]
                    else None
                ),
            }
        )
    categories.sort(key=lambda c: c["categoryId"])
    return categories


# ----------------------------------------------------------------- products --
def build_products(
    rng: random.Random,
    categories: list[dict[str, Any]],
    products_per_category: int,
) -> list[dict[str, Any]]:
    rows = _read_csv(SOURCE_DIR / "Product.csv")
    by_cat: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        cat = r["ProductCategoryID"]
        if not cat:
            continue
        by_cat.setdefault(cat, []).append(r)

    products: list[dict[str, Any]] = []
    for cat in categories:
        src_cat_id = cat["categoryId"][3:].lstrip("0") or "0"
        pool = by_cat.get(src_cat_id, [])
        if len(pool) < products_per_category:
            # Top up from any leaf category if a small one is short.
            extras_pool = [p for p in rows if p["ProductCategoryID"]]
            extras = rng.sample(extras_pool, products_per_category - len(pool))
            pool = pool + extras
        picked = rng.sample(pool, products_per_category)
        # Synthesize rating so R-EXT-3 has something to sort by.
        for row in picked:
            products.append(
                {
                    "productId": f"P{int(row['ProductID']):05d}",
                    "name": row["Name"],
                    "productNumber": row["ProductNumber"],
                    "color": row["Color"] or None,
                    "size": row["Size"] or None,
                    "price": round(_parse_decimal(row["ListPrice"]), 2),
                    "standardCost": round(_parse_decimal(row["StandardCost"]), 2),
                    "categoryId": cat["categoryId"],
                    "categoryName": cat["name"],
                    "rating": round(rng.uniform(3.0, 5.0), 2),
                }
            )
    products.sort(key=lambda p: (p["categoryId"], p["productId"]))
    return products


# ------------------------------------------------------------------- orders --
_STATUSES = ("InCart", "Placed", "Shipped", "Delivered", "Cancelled")


def build_orders(
    rng: random.Random,
    customers: list[dict[str, Any]],
    products: list[dict[str, Any]],
    orders_per_customer: int,
    max_lines_per_order: int,
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    order_seq = 1
    for cust in customers:
        for _ in range(orders_per_customer):
            offset = rng.randint(0, ORDER_DATE_SPAN_DAYS)
            order_date = ORDER_DATE_END - timedelta(days=offset)
            line_count = rng.randint(1, max_lines_per_order)
            picks = rng.sample(products, line_count)
            items: list[dict[str, Any]] = []
            for prod in picks:
                qty = rng.randint(1, 5)
                items.append(
                    {
                        "productId": prod["productId"],
                        "productName": prod["name"],
                        "categoryId": prod["categoryId"],
                        "quantity": qty,
                        "unitPrice": prod["price"],
                        "lineTotal": round(prod["price"] * qty, 2),
                    }
                )
            total = round(sum(it["lineTotal"] for it in items), 2)
            orders.append(
                {
                    "orderId": f"O{order_seq:07d}",
                    "customerId": cust["customerId"],
                    "orderDate": order_date.isoformat(),
                    "status": rng.choice(_STATUSES),
                    "totalAmount": total,
                    "items": items,
                }
            )
            order_seq += 1
    orders.sort(key=lambda o: (o["customerId"], o["orderDate"]))
    return orders


# ----------------------------------------------------------------- writeout --
def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260517)
    parser.add_argument("--customers", type=int, default=10)
    parser.add_argument("--orders-per-customer", type=int, default=20)
    parser.add_argument("--categories", type=int, default=5)
    parser.add_argument("--products-per-category", type=int, default=10)
    parser.add_argument("--max-lines-per-order", type=int, default=10)
    args = parser.parse_args(argv)

    rng = random.Random(args.seed)
    customers = build_customers(rng, args.customers)
    categories = build_categories(rng, args.categories)
    products = build_products(rng, categories, args.products_per_category)
    orders = build_orders(
        rng,
        customers,
        products,
        args.orders_per_customer,
        args.max_lines_per_order,
    )

    _write(MASTER_DIR / "customers.json", customers)
    _write(MASTER_DIR / "categories.json", categories)
    _write(MASTER_DIR / "products.json", products)
    _write(MASTER_DIR / "orders.json", orders)

    print(
        f"Wrote {len(customers)} customers, {len(categories)} categories, "
        f"{len(products)} products, {len(orders)} orders -> {MASTER_DIR}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

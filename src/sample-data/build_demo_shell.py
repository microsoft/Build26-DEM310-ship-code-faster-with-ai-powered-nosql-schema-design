"""Generate per-iteration ``demo-shell/seed-data/*.json`` artifacts.

Each iteration ships a ``demo-shell/`` folder with:

* ``seed-data/<Container>.json`` — the master JSON re-shaped into the
  exact document layout the iteration's containers expect. These are the
  files you would hand-upload via the Cosmos DB Data Explorer or stream
  into the Cosmos DB Shell with an ``items.upsert(...)`` loop.
* ``01-setup.cosmos.js`` — Cosmos DB Shell script that creates the
  database, the containers, and the indexing policies for that iteration.
* ``02-access-patterns.cosmos.js`` — Cosmos DB Shell script with one
  runnable snippet per access pattern so the speaker can demo each step
  manually.

This script only owns the **seed-data JSON** generation; the
``.cosmos.js`` scripts are authored by hand and committed alongside.

    python build_demo_shell.py        # regenerate all seed-data folders
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / "master"
SRC = ROOT.parent  # /src

ITERATIONS = {
    "iteration-01-naive/naive-a": "_emit_naive_a",
    "iteration-01-naive/naive-b": "_emit_naive_b",
    "iteration-02-optimized":     "_emit_iter_02",
    "iteration-03-composite-indexes": "_emit_iter_03",
}


def _load(name: str) -> list[dict]:
    with (MASTER / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"  wrote {path.relative_to(SRC.parent)}  ({len(data)} docs)")


# ---------------------------------------------------------------------------
# Iteration 1 — naive-a: five relational-style containers
# ---------------------------------------------------------------------------
def _emit_naive_a(out_dir: Path) -> None:
    customers = _load("customers")
    categories = _load("categories")
    products = _load("products")
    orders = _load("orders")

    cust_docs = [{"id": c["customerId"], **c} for c in customers]
    cat_docs = [{"id": c["categoryId"], **c} for c in categories]
    prod_docs = [{"id": p["productId"], **p} for p in products]

    order_docs = []
    item_docs = []
    for o in orders:
        items = o["items"]
        header = {k: v for k, v in o.items() if k != "items"}
        header["id"] = o["orderId"]
        header["lineCount"] = len(items)
        order_docs.append(header)
        for idx, item in enumerate(items, start=1):
            line_id = f"{o['orderId']}-L{idx:02d}"
            item_docs.append({
                "id": line_id,
                "orderItemId": line_id,
                "orderId": o["orderId"],
                "customerId": o["customerId"],
                **item,
            })

    _write(out_dir / "seed-data" / "Customers.json", cust_docs)
    _write(out_dir / "seed-data" / "ProductCategories.json", cat_docs)
    _write(out_dir / "seed-data" / "Products.json", prod_docs)
    _write(out_dir / "seed-data" / "Orders.json", order_docs)
    _write(out_dir / "seed-data" / "OrderItems.json", item_docs)


# ---------------------------------------------------------------------------
# Iteration 1 — naive-b: single container, unbounded-array anti-pattern
# ---------------------------------------------------------------------------
def _emit_naive_b(out_dir: Path) -> None:
    customers = _load("customers")
    docs = [{
        "id": c["customerId"],
        "customerId": c["customerId"],
        "type": "customer",
        "firstName": c.get("firstName"),
        "lastName": c.get("lastName"),
        "email": c.get("emailAddress"),
        "phone": c.get("phone"),
        "orders": [],          # the unbounded array, intentionally empty
    } for c in customers]
    _write(out_dir / "seed-data" / "CustomersWithEmbeddedOrders.json", docs)


# ---------------------------------------------------------------------------
# Iteration 2 — CustomerOrders (type discriminator) + Products
# ---------------------------------------------------------------------------
def _summary_for(customer_id: str, orders: list[dict]) -> dict:
    co = [o for o in orders if o["customerId"] == customer_id]
    if not co:
        return {"lifetimeOrders": 0, "lifetimeRevenue": 0.0, "lastOrderDate": None}
    return {
        "lifetimeOrders": len(co),
        "lifetimeRevenue": round(sum(o["totalAmount"] for o in co), 2),
        "lastOrderDate": max(o["orderDate"] for o in co),
    }


def _emit_iter_02(out_dir: Path) -> None:
    customers = _load("customers")
    orders = _load("orders")
    products = _load("products")

    co_docs = []
    for c in customers:
        co_docs.append({
            "id": c["customerId"],
            "type": "customer",
            **c,
            "orderSummary": _summary_for(c["customerId"], orders),
        })
    for o in orders:
        co_docs.append({"id": o["orderId"], "type": "order", **o})

    prod_docs = [{"id": p["productId"], "type": "product", **p} for p in products]

    _write(out_dir / "seed-data" / "CustomerOrders.json", co_docs)
    _write(out_dir / "seed-data" / "Products.json", prod_docs)


# ---------------------------------------------------------------------------
# Iteration 3 — same containers as iteration 2, no extra seed data needed
# ---------------------------------------------------------------------------
def _emit_iter_03(out_dir: Path) -> None:
    note = (out_dir / "seed-data" / "README.md")
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "# Iteration 3 — no separate seed data\n\n"
        "Iteration 3 keeps the iteration-2 container shape "
        "(`CustomerOrders` + `Products`) and only **changes the indexing "
        "policy** to add composite indexes. Use the seed data from "
        "`../../iteration-02-optimized/demo-shell/seed-data/`.\n",
        encoding="utf-8",
    )
    print(f"  wrote {note.relative_to(SRC.parent)}  (pointer)")


# ---------------------------------------------------------------------------
def main() -> None:
    for rel, fn_name in ITERATIONS.items():
        out_dir = SRC / rel / "demo-shell"
        print(f"\n{rel}/demo-shell/")
        globals()[fn_name](out_dir)


if __name__ == "__main__":
    main()

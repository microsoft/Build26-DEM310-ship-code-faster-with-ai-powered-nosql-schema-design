"""Iteration 1 seed: create 5 containers and bulk-insert from master JSON.

    python complete/seed.py

Reshapes the master JSON into the naive container layout:

    Customers          <- master/customers.json (one doc per customer)
    Orders             <- master/orders.json    (header only; items removed)
    OrderItems         <- exploded from master/orders.json items[]
    Products           <- master/products.json
    ProductCategories  <- master/categories.json
"""

from __future__ import annotations

from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError

from shared import (
    CONTAINERS,
    DATABASE_NAME,
    get_client,
    load_master,
)


def ensure_database_and_containers(client):
    db = client.create_database_if_not_exists(DATABASE_NAME)
    containers: dict = {}
    for name, pk_path in CONTAINERS:
        container = db.create_container_if_not_exists(
            id=name,
            partition_key=PartitionKey(path=pk_path),
            offer_throughput=400,
        )
        containers[name] = container
    return containers


def seed(containers) -> None:
    customers = load_master("customers")
    categories = load_master("categories")
    products = load_master("products")
    orders = load_master("orders")

    # --- Customers (id = customerId) ---------------------------------------
    for c in customers:
        doc = {"id": c["customerId"], **c}
        containers["Customers"].upsert_item(doc)

    # --- ProductCategories (id = categoryId) -------------------------------
    for cat in categories:
        doc = {"id": cat["categoryId"], **cat}
        containers["ProductCategories"].upsert_item(doc)

    # --- Products (id = productId) -----------------------------------------
    for p in products:
        doc = {"id": p["productId"], **p}
        containers["Products"].upsert_item(doc)

    # --- Orders header + OrderItems lines ----------------------------------
    for o in orders:
        items = o["items"]
        header = {k: v for k, v in o.items() if k != "items"}
        header["id"] = o["orderId"]
        header["lineCount"] = len(items)
        containers["Orders"].upsert_item(header)

        for idx, item in enumerate(items, start=1):
            line_id = f"{o['orderId']}-L{idx:02d}"
            line_doc = {
                "id": line_id,
                "orderItemId": line_id,
                "orderId": o["orderId"],
                "customerId": o["customerId"],
                **item,
            }
            containers["OrderItems"].upsert_item(line_doc)

    print(
        f"Seeded: {len(customers)} customers, {len(categories)} categories, "
        f"{len(products)} products, {len(orders)} orders, "
        f"{sum(len(o['items']) for o in orders)} order items"
    )


def main() -> None:
    client = get_client()
    containers = ensure_database_and_containers(client)
    seed(containers)


if __name__ == "__main__":
    main()

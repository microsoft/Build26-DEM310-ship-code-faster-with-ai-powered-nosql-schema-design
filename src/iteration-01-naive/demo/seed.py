"""Iteration 1 seed — DEMO skeleton.

Goal during the demo: stand up the naive 5-container layout and bulk-insert
from the master JSON.

Look at complete/seed.py if you get stuck.
"""

from __future__ import annotations

from azure.cosmos import PartitionKey

from shared import CONTAINERS, DATABASE_NAME, get_client, load_master


def ensure_database_and_containers(client):
    db = client.create_database_if_not_exists(DATABASE_NAME)

    # TODO (demo): loop over CONTAINERS and create each container with the
    # right partition key path. Return a dict {name: container_client}.
    containers: dict = {}
    return containers


def seed(containers) -> None:
    customers = load_master("customers")
    categories = load_master("categories")
    products = load_master("products")
    orders = load_master("orders")

    # TODO (demo): upsert customers, categories, and products. Each document
    # needs an `id` field — use the natural key (customerId, categoryId,
    # productId).

    # TODO (demo): split each order into a header doc (Orders container) and
    # one line doc per item (OrderItems container). Notice how unnatural this
    # feels — that's the point.

    print("seed.py: not implemented yet — see complete/seed.py")


def main() -> None:
    client = get_client()
    containers = ensure_database_and_containers(client)
    seed(containers)


if __name__ == "__main__":
    main()

"""Iteration 1 / naive-b seed: create the single anti-pattern container
and seed one document per customer, each with an EMPTY orders[] array.

simulate then grows the array on a chosen customer's document, iteration
by iteration.
"""

from __future__ import annotations

import sys

from azure.cosmos import PartitionKey, exceptions

from scripts._naive_b_shared import (
    CONTAINER_NAME,
    DATABASE_NAME,
    PARTITION_KEY,
    doc_size_bytes,
    get_client,
    load_master,
)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def ensure_database_and_container():
    client = get_client()
    db = client.create_database_if_not_exists(id=DATABASE_NAME)

    # Start clean each run so the growth simulation is deterministic.
    try:
        db.delete_container(CONTAINER_NAME)
        print(f"Dropped existing container '{CONTAINER_NAME}'")
    except exceptions.CosmosResourceNotFoundError:
        pass

    container = db.create_container(
        id=CONTAINER_NAME,
        partition_key=PartitionKey(path=PARTITION_KEY),
        offer_throughput=400,
    )
    print(f"Created container '{CONTAINER_NAME}' (PK={PARTITION_KEY})")
    return container


def seed(container):
    customers = load_master("customers")
    for c in customers:
        doc = {
            "id": c["customerId"],
            "customerId": c["customerId"],
            "type": "customer",
            "firstName": c.get("firstName"),
            "lastName": c.get("lastName"),
            "email": c.get("email"),
            "phone": c.get("phone"),
            "orders": [],          # <-- the unbounded array, intentionally
        }
        container.upsert_item(doc)

    print(f"Seeded {len(customers)} customer docs with empty orders[]")
    sample = container.read_item(item=customers[0]["customerId"],
                                  partition_key=customers[0]["customerId"])
    print(f"Initial doc size: {doc_size_bytes(sample)} bytes")


if __name__ == "__main__":
    container = ensure_database_and_container()
    seed(container)

"""Iteration 2 seed — DEMO skeleton.

Goal: create CustomerOrders (/customerId) and Products (/categoryId),
then bulk-insert from the master JSON in iteration-2 document shapes
(``type`` discriminator on CustomerOrders).

See complete/seed.py if you get stuck.
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


def _load(name: str) -> list[dict]:
    with (MASTER_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    client = get_client()
    db = client.create_database_if_not_exists(DATABASE_NAME)

    # TODO (demo): create CustomerOrders with PartitionKey(path="/customerId")
    # TODO (demo): create Products with PartitionKey(path="/categoryId")

    # TODO (demo): for each customer, upsert a {"type": "customer", ...} doc
    #              that embeds an orderSummary rolled up from their orders
    # TODO (demo): for each order, upsert a {"type": "order", ...} doc
    #              with items[] embedded
    # TODO (demo): for each product, upsert a {"type": "product", ...} doc

    print("seed.py: not implemented yet — see complete/seed.py")


if __name__ == "__main__":
    main()

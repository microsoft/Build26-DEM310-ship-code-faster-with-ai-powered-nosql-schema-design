"""Shared helpers for naive-b (the unbounded-array anti-pattern).

One container, one document per customer, all orders embedded.
"""

from __future__ import annotations

import json
import os
import urllib3
from pathlib import Path

from azure.cosmos import CosmosClient, PartitionKey

EMULATOR_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
EMULATOR_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# /src/sample-data/master from /src/iteration-01-naive/naive-b/complete/
MASTER_DIR = Path(__file__).resolve().parents[3] / "sample-data" / "master"

CONTAINER_NAME = "CustomersWithEmbeddedOrders"
PARTITION_KEY = "/customerId"


def get_client() -> CosmosClient:
    return CosmosClient(
        EMULATOR_ENDPOINT,
        credential=EMULATOR_KEY,
        connection_verify=False,
    )


def load_master(name: str) -> list[dict]:
    with (MASTER_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def doc_size_bytes(doc: dict) -> int:
    """Approximate the on-the-wire JSON size of the document."""
    return len(json.dumps(doc, separators=(",", ":")).encode("utf-8"))


def last_ru(container) -> float:
    return float(container.client_connection.last_response_headers.get(
        "x-ms-request-charge", 0.0
    ))

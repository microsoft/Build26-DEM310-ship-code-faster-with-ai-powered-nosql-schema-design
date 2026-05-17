"""Demo skeleton — fill in the gaps with the Cosmos DB Agent.

The complete reference lives in ../complete/shared.py.
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

MASTER_DIR = Path(__file__).resolve().parents[3] / "sample-data" / "master"

# TODO (demo): pick the single container name and partition key for the
# "one document per customer" anti-pattern.
CONTAINER_NAME = "CustomersWithEmbeddedOrders"
PARTITION_KEY = "/customerId"


def get_client() -> CosmosClient:
    return CosmosClient(EMULATOR_ENDPOINT, credential=EMULATOR_KEY,
                        connection_verify=False)


def load_master(name: str) -> list[dict]:
    with (MASTER_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def doc_size_bytes(doc: dict) -> int:
    # TODO (demo): return the JSON-encoded byte length of the doc.
    ...


def last_ru(container) -> float:
    # TODO (demo): pull "x-ms-request-charge" off the container's last
    # response headers.
    ...

"""Demo skeleton — fill in the gaps with the Cosmos DB Agent.

The complete reference lives in ../complete/shared.py.
"""

from __future__ import annotations

import json
import os
import urllib3
from pathlib import Path

from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Load /src/.env (copy /src/.env.example -> /src/.env on first run).
SRC_DIR = Path(__file__).resolve().parents[3]
load_dotenv(SRC_DIR / ".env")

EMULATOR_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
EMULATOR_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310")

if not EMULATOR_ENDPOINT or not EMULATOR_KEY:
    raise RuntimeError(
        "COSMOS_ENDPOINT / COSMOS_KEY not set. "
        "Copy src/.env.example to src/.env, then re-run."
    )

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

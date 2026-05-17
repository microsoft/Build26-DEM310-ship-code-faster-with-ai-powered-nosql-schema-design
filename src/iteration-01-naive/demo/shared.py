"""Same helpers as complete/shared.py — feel free to leave this file alone
during the demo. The interesting changes happen in seed.py and patterns.py.
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

MASTER_DIR = Path(__file__).resolve().parents[2] / "sample-data" / "master"

# TODO (demo): fill in the five containers and partition keys you want to
# create for the naive 1:1 port of the relational schema.
CONTAINERS: list[tuple[str, str]] = [
    # ("Customers", "/customerId"),
    # ...
]


def get_client() -> CosmosClient:
    return CosmosClient(
        EMULATOR_ENDPOINT,
        credential=EMULATOR_KEY,
        connection_verify=False,
    )


def load_master(name: str) -> list[dict]:
    with (MASTER_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def print_ru(label: str, ru: float, doc_count: int | None = None) -> None:
    suffix = f"  ({doc_count} docs)" if doc_count is not None else ""
    print(f"  [RU] {label:<45} {ru:>8.2f}{suffix}")

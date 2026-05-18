"""Same helpers as complete/shared.py — feel free to leave this file alone
during the demo. The interesting changes happen in seed.py and patterns.py.
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
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310DB-i1a")

if not EMULATOR_ENDPOINT or not EMULATOR_KEY:
    raise RuntimeError(
        "COSMOS_ENDPOINT / COSMOS_KEY not set. "
        "Copy src/.env.example to src/.env, then re-run."
    )

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MASTER_DIR = Path(__file__).resolve().parents[3] / "sample-data" / "master"

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


# See complete/shared.py for the full version with query-metrics parsing.
_METRIC_KEYS = (
    "retrievedDocumentCount",
    "outputDocumentCount",
    "indexHitDocumentCount",
    "totalExecutionTimeInMs",
)


def _format_metrics(metrics: str) -> str:
    if not metrics:
        return ""
    parts = dict(p.split("=", 1) for p in metrics.split(";") if "=" in p)
    return " ".join(f"{k}={parts[k]}" for k in _METRIC_KEYS if k in parts)


def print_query(label: str, ru: float, client_count: int,
                server_count: int | None, metrics: str | None) -> None:
    """Print RU + server-reported item count + a compact query-metrics line."""
    server = server_count if server_count is not None else client_count
    print(
        f"  [RU] {label:<45} {ru:>8.2f}"
        f"  (client={client_count} docs, server item-count={server})"
    )
    summary = _format_metrics(metrics or "")
    if summary:
        print(f"       metrics: {summary}")
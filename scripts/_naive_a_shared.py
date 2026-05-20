"""Shared helpers for iteration 1 / naive-a (the 5-container design).

Loads the master JSON, builds a Cosmos client pointed at the local emulator,
and centralises container/partition-key names so the seed and patterns
modules stay short.
"""

from __future__ import annotations

import json
import os
import urllib3
from pathlib import Path

from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Repo root is scripts/.. — /src/.env lives one level below it.
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
load_dotenv(SRC_DIR / ".env")

EMULATOR_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
EMULATOR_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DB", "Build26DEM310DB-i1a")

if not EMULATOR_ENDPOINT or not EMULATOR_KEY:
    raise RuntimeError(
        "COSMOS_ENDPOINT / COSMOS_KEY not set. "
        "Copy src/.env.example to src/.env (and edit if you are not using "
        "the default local emulator), then re-run."
    )

# The emulator uses a self-signed certificate. Silence the warning when
# running with verify=False.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MASTER_DIR = SRC_DIR / "sample-data" / "master"


# Container layout for iteration 1: one container per relational table,
# each partitioned by the obvious "id" column.
CONTAINERS: list[tuple[str, str]] = [
    ("Customers", "/customerId"),
    ("Orders", "/orderId"),
    ("OrderItems", "/orderId"),
    ("Products", "/productId"),
    ("ProductCategories", "/categoryId"),
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


# A handful of `x-ms-documentdb-query-metrics` fields worth surfacing during
# the demo. The full header is a verbose `key=value;key=value;...` blob.
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

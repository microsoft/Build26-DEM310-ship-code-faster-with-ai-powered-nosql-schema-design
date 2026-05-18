"""Iteration 3 queries — DEMO skeleton.

Goal: write each of the three extended access patterns and observe the
RU charge with and without the composite indexes from
``../complete/indexing-policy.json``.

See complete/queries.py for the reference implementation.
"""

from __future__ import annotations

import os
import sys
import urllib3
from pathlib import Path

from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load /src/.env (copy /src/.env.example -> /src/.env on first run).
SRC_DIR = Path(__file__).resolve().parents[2]
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


def _client():
    return CosmosClient(
        EMULATOR_ENDPOINT, credential=EMULATOR_KEY, connection_verify=False
    )


def r_ext_1(db) -> None:
    """Customer order history by date range — needs [type ASC, orderDate DESC]."""
    # TODO (demo): query CustomerOrders in-partition with date range + ORDER BY DESC.
    # Pass populate_query_metrics=True and capture x-ms-request-charge,
    # x-ms-item-count, and x-ms-documentdb-query-metrics from the response.
    print("R-EXT-1: not implemented")


def r_ext_2(db) -> None:
    """Open-orders dashboard — needs [status ASC, orderDate DESC]."""
    # TODO (demo): cross-partition query filtered by status, ORDER BY orderDate DESC.
    # MUST pass enable_cross_partition_query=True (and populate_query_metrics=True).
    print("R-EXT-2: not implemented")


def r_ext_3(db) -> None:
    """Products by rating DESC, price ASC — needs [rating DESC, price ASC]."""
    # TODO (demo): in-partition query on Products with populate_query_metrics=True.
    print("R-EXT-3: not implemented")


def main(argv: list[str]) -> int:
    db = _client().get_database_client(DATABASE_NAME)
    r_ext_1(db)
    r_ext_2(db)
    r_ext_3(db)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

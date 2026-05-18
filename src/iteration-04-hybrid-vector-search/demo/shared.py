"""Shared helpers for iteration 4 — DEMO skeleton.

Look at complete/shared.py if you get stuck. The complete version wraps:
  * DefaultAzureCredential + AAD-authenticated CosmosClient
  * AzureOpenAI client wired with `azure_ad_token_provider` (no keys)
  * a `capture(container)` helper that pulls
        x-ms-request-charge
        x-ms-item-count
        x-ms-documentdb-query-metrics
    off the last response, and a `print_query` helper that surfaces them.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

SRC_DIR = Path(__file__).resolve().parents[2]
load_dotenv(SRC_DIR / ".env")

COSMOS_ENDPOINT  = os.environ.get("COSMOS_ENDPOINT")
COSMOS_DB        = os.environ.get("COSMOS_DB", "Build26DEM310")
COSMOS_CONTAINER = os.environ.get("COSMOS_CONTAINER_I4", "ProductsRich")
FOUNDRY_ENDPOINT = os.environ.get("FOUNDRY_ENDPOINT")
EMBED_DEPLOYMENT = os.environ.get("FOUNDRY_EMBEDDING_DEPLOYMENT",
                                  "text-embedding-3-small")


# TODO (demo):
#   1. Build a DefaultAzureCredential.
#   2. Return a CosmosClient(url=..., credential=...) — no key argument.
def get_cosmos_client():
    raise NotImplementedError("see complete/shared.py")


# TODO (demo):
#   1. Wrap DefaultAzureCredential in get_bearer_token_provider with the
#      scope "https://cognitiveservices.azure.com/.default".
#   2. Return AzureOpenAI(azure_endpoint=..., api_version=...,
#                         azure_ad_token_provider=...)
def get_openai_client():
    raise NotImplementedError("see complete/shared.py")

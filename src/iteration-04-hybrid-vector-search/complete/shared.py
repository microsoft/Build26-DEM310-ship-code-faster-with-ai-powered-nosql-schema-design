"""Shared helpers for iteration 4 — keyless cloud Cosmos + Azure AI Foundry.

Everything goes through ``DefaultAzureCredential`` so the same code runs:
  * locally as the developer signed in via `az login`
  * in CI as a federated workload identity / service principal
  * in Azure as a managed identity

No keys, no connection strings. Both the Cosmos account and the Foundry
account are provisioned with ``disableLocalAuth: true`` — see infra/.
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load /src/.env. Iteration 4 reads its own block of variables (see
# /src/.env.example, section "Iteration 4 — cloud Cosmos DB + Azure AI Foundry").
SRC_DIR = Path(__file__).resolve().parents[2]
load_dotenv(SRC_DIR / ".env")

COSMOS_ENDPOINT       = os.environ.get("COSMOS_ENDPOINT")
COSMOS_DB             = os.environ.get("COSMOS_DB", "Build26DEM310DB-i4")
COSMOS_CONTAINER      = os.environ.get("COSMOS_CONTAINER_I4", "ProductsRich")
FOUNDRY_ENDPOINT      = os.environ.get("FOUNDRY_ENDPOINT")
EMBED_DEPLOYMENT      = os.environ.get("FOUNDRY_EMBEDDING_DEPLOYMENT",
                                       "text-embedding-3-small")
EMBED_DIMENSIONS      = int(os.environ.get("FOUNDRY_EMBEDDING_DIMENSIONS", "1536"))
CHAT_DEPLOYMENT       = os.environ.get("FOUNDRY_CHAT_DEPLOYMENT", "gpt-4o-mini")

# API version that supports embeddings + chat completions on AI Foundry.
AZURE_OPENAI_API_VERSION = os.environ.get(
    "FOUNDRY_API_VERSION", "2024-10-21"
)


def _require(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(
            f"{name} not set. Did you run infra/deploy.ps1 and paste the "
            "iteration-4 block from src/.env.example into src/.env?"
        )
    return value


def get_credential() -> DefaultAzureCredential:
    return DefaultAzureCredential()


def get_cosmos_client() -> CosmosClient:
    endpoint = _require("COSMOS_ENDPOINT", COSMOS_ENDPOINT)
    return CosmosClient(url=endpoint, credential=get_credential())


def get_openai_client() -> AzureOpenAI:
    endpoint = _require("FOUNDRY_ENDPOINT", FOUNDRY_ENDPOINT)
    # AzureOpenAI accepts an AAD token provider — no keys involved.
    token_provider = get_bearer_token_provider(
        get_credential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_ad_token_provider=token_provider,
    )


def embed(client: AzureOpenAI, text: str) -> list[float]:
    """Single-shot embedding. Use ``embed_batch`` for bulk seed."""
    resp = client.embeddings.create(model=EMBED_DEPLOYMENT, input=text)
    return resp.data[0].embedding


def embed_batch(client: AzureOpenAI, texts: list[str]) -> list[list[float]]:
    """text-embedding-3-* accepts arrays. One round-trip per batch."""
    resp = client.embeddings.create(model=EMBED_DEPLOYMENT, input=texts)
    # API returns results in request order.
    return [d.embedding for d in resp.data]


# ---- Diagnostic header capture (mirror of iterations 1-3) -----------------

_METRIC_KEYS = (
    "retrievedDocumentCount",
    "outputDocumentCount",
    "indexHitDocumentCount",
    "totalExecutionTimeInMs",
)


def capture(container) -> tuple[float, int, str]:
    """Pull RU + server item count + query-metrics headers off the last response."""
    h = container.client_connection.last_response_headers
    ru = float(h.get("x-ms-request-charge", 0.0) or 0.0)
    count = int(h.get("x-ms-item-count", 0) or 0)
    metrics = h.get("x-ms-documentdb-query-metrics", "") or ""
    return ru, count, metrics


def format_metrics(metrics: str) -> str:
    if not metrics:
        return ""
    parts = dict(p.split("=", 1) for p in metrics.split(";") if "=" in p)
    return " ".join(f"{k}={parts[k]}" for k in _METRIC_KEYS if k in parts)


def print_query(label: str, ru: float, client_count: int,
                server_count: int, metrics: str) -> None:
    print(
        f"  [RU] {label:<55} {ru:>8.2f}"
        f"  (client={client_count} docs, server item-count={server_count})"
    )
    summary = format_metrics(metrics)
    if summary:
        print(f"       metrics: {summary}")

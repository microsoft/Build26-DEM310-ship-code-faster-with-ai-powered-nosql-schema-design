"""Seed the ProductsRich container.

  * Loads the master products JSON from /src/sample-data/master/products.json
  * Synthesizes a marketing-blurb description per product (deterministic —
    no LLM call required) so the full-text index has something to chew on
  * Calls Azure OpenAI embeddings in batches to vectorize each description
  * Upserts the resulting documents (with /description and /embedding) into
    the cloud container provisioned by infra/main.bicep.

Run:
  python complete/seed.py

Re-running is safe — items are upserted by `id`.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from shared import (
    COSMOS_CONTAINER,
    COSMOS_DB,
    EMBED_DIMENSIONS,
    capture,
    embed_batch,
    get_cosmos_client,
    get_openai_client,
)

BATCH_SIZE = 16  # embeddings per API call

MASTER = (
    Path(__file__).resolve().parents[3]
    / "sample-data" / "master" / "products.json"
)


def synth_description(p: dict) -> str:
    """Deterministic marketing blurb so re-seeding is reproducible and the
    full-text index has something meaningful to score against."""
    bits = [
        f"The {p['name']} is a {p['categoryName'].lower()} product",
    ]
    if p.get("color"):
        bits.append(f"in {p['color'].lower()}")
    if p.get("size"):
        bits.append(f"size {p['size']}")
    bits.append(
        f"priced at ${p['price']:.2f}, with an average customer rating of "
        f"{p['rating']:.2f} out of 5."
    )
    bits.append(
        f"Product number {p['productNumber']} in the {p['categoryName']} "
        "category. Suitable for both casual riders and enthusiasts looking "
        "for reliability and performance."
    )
    return " ".join(bits)


def main() -> int:
    if not MASTER.exists():
        print(f"Missing master file: {MASTER}", file=sys.stderr)
        return 1

    print(f"Loading {MASTER.name}...")
    with MASTER.open("r", encoding="utf-8") as fh:
        products: list[dict] = json.load(fh)
    print(f"  -> {len(products)} products")

    # ---- describe + embed --------------------------------------------------
    print("Synthesizing descriptions...")
    descriptions = [synth_description(p) for p in products]

    print(f"Generating embeddings ({EMBED_DIMENSIONS}-dim) in batches of {BATCH_SIZE}...")
    oai = get_openai_client()
    embeddings: list[list[float]] = []
    t0 = time.perf_counter()
    for i in range(0, len(descriptions), BATCH_SIZE):
        chunk = descriptions[i : i + BATCH_SIZE]
        embeddings.extend(embed_batch(oai, chunk))
        print(f"  embedded {min(i + BATCH_SIZE, len(descriptions))}/{len(descriptions)}")
    elapsed = time.perf_counter() - t0
    print(f"  -> {len(embeddings)} embeddings in {elapsed:.1f}s")

    # ---- upsert ------------------------------------------------------------
    print(f"Upserting into {COSMOS_DB}.{COSMOS_CONTAINER}...")
    db = get_cosmos_client().get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_CONTAINER)

    total_ru = 0.0
    for p, desc, emb in zip(products, descriptions, embeddings):
        doc = {
            "id":                p["productId"],
            "productId":         p["productId"],
            "type":              "product",
            "name":              p["name"],
            "productNumber":     p["productNumber"],
            "color":             p.get("color"),
            "size":              p.get("size"),
            "price":             p["price"],
            "standardCost":      p["standardCost"],
            "categoryId":        p["categoryId"],
            "categoryName":      p["categoryName"],
            "rating":            p["rating"],
            "description":       desc,
            "descriptionTokens": max(1, len(desc.split())),
            "embedding":         emb,
        }
        container.upsert_item(doc)
        ru, _, _ = capture(container)
        total_ru += ru

    print(f"Done. Upsert RU total: {total_ru:.2f} ({total_ru / len(products):.2f} avg/doc)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

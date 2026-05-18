"""Seed ProductsRich — DEMO skeleton.

See complete/seed.py for the working version.
"""

from __future__ import annotations


def main() -> int:
    # TODO (demo):
    #   1. Load /src/sample-data/master/products.json
    #   2. Synthesize a description string per product (name + category +
    #      color + size + price). Determinism is fine — no LLM needed.
    #   3. Call AzureOpenAI.embeddings.create(model=EMBED_DEPLOYMENT,
    #      input=<list of descriptions>) in batches of ~16 to vectorize.
    #   4. Upsert each doc as
    #        { id, productId, ..., description, embedding }
    #      into the ProductsRich container. Re-runs should be idempotent.
    print("seed.py: not implemented (see complete/seed.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

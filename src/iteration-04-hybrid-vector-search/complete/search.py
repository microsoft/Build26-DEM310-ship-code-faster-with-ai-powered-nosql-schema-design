"""Iteration 4 access patterns: R-VEC-1, R-FTS-1, R-HYB-1.

Run:
  python complete/search.py

Prints per-query RU charge, server item count, and a compact query-metrics
summary so the demo can compare:
  * vector-only ranking      (R-VEC-1)
  * full-text-only ranking   (R-FTS-1)
  * hybrid RRF ranking       (R-HYB-1)
"""

from __future__ import annotations

import sys

from shared import (
    COSMOS_CONTAINER,
    COSMOS_DB,
    capture,
    embed,
    get_cosmos_client,
    get_openai_client,
    print_query,
)

TOP_K = 5

# Free-text query for vector / hybrid search.
QUERY_TEXT = "lightweight aluminum road bike, red"

# Keyword tokens for full-text / hybrid search.
KEYWORDS = ["aluminum", "red"]


def r_vec_1(container, qv: list[float]) -> None:
    print("\nR-VEC-1 - vector search: nearest neighbours by cosine distance")
    items = list(
        container.query_items(
            query=(
                "SELECT TOP @k c.productId, c.name, c.categoryId, "
                "VectorDistance(c.embedding, @qv) AS score "
                "FROM c "
                "ORDER BY VectorDistance(c.embedding, @qv)"
            ),
            parameters=[
                {"name": "@k", "value": TOP_K},
                {"name": "@qv", "value": qv},
            ],
            enable_cross_partition_query=True,
            populate_query_metrics=True,
        )
    )
    ru, server_count, metrics = capture(container)
    print_query(f"vector top-{TOP_K} for '{QUERY_TEXT}'", ru, len(items),
                server_count, metrics)
    for r in items:
        print(f"    {r['score']:.4f}  {r['productId']}  {r['name']}")


def r_fts_1(container) -> None:
    print(f"\nR-FTS-1 - full-text search: ALL of {KEYWORDS}")
    items = list(
        container.query_items(
            query=(
                "SELECT TOP @k c.productId, c.name, "
                "FullTextScore(c.description, @k1, @k2) AS score "
                "FROM c "
                "WHERE FullTextContainsAll(c.description, @k1, @k2) "
                "ORDER BY FullTextScore(c.description, @k1, @k2)"
            ),
            parameters=[
                {"name": "@k",  "value": TOP_K},
                {"name": "@k1", "value": KEYWORDS[0]},
                {"name": "@k2", "value": KEYWORDS[1]},
            ],
            enable_cross_partition_query=True,
            populate_query_metrics=True,
        )
    )
    ru, server_count, metrics = capture(container)
    print_query(f"FTS top-{TOP_K} for {KEYWORDS}", ru, len(items),
                server_count, metrics)
    for r in items:
        print(f"    {r['score']:.4f}  {r['productId']}  {r['name']}")


def r_hyb_1(container, qv: list[float]) -> None:
    print("\nR-HYB-1 - hybrid search: RRF over vector + full-text")
    items = list(
        container.query_items(
            query=(
                "SELECT TOP @k c.productId, c.name FROM c "
                "ORDER BY RANK RRF("
                "  VectorDistance(c.embedding, @qv), "
                "  FullTextScore(c.description, @k1, @k2)"
                ")"
            ),
            parameters=[
                {"name": "@k",  "value": TOP_K},
                {"name": "@qv", "value": qv},
                {"name": "@k1", "value": KEYWORDS[0]},
                {"name": "@k2", "value": KEYWORDS[1]},
            ],
            enable_cross_partition_query=True,
            populate_query_metrics=True,
        )
    )
    ru, server_count, metrics = capture(container)
    print_query(f"hybrid RRF top-{TOP_K}", ru, len(items),
                server_count, metrics)
    for r in items:
        print(f"    {r['productId']}  {r['name']}")


def main() -> int:
    print("=" * 70)
    print("Iteration 4 - hybrid + vector search")
    print("=" * 70)

    print(f"Embedding query: '{QUERY_TEXT}'")
    oai = get_openai_client()
    qv = embed(oai, QUERY_TEXT)

    db = get_cosmos_client().get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_CONTAINER)

    r_vec_1(container, qv)
    r_fts_1(container)
    r_hyb_1(container, qv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

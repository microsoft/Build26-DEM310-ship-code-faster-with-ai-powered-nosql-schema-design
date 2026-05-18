"""Iteration 4 search patterns — DEMO skeleton.

See complete/search.py for working SQL + parameter binding.
"""

from __future__ import annotations


def r_vec_1(container, qv) -> None:
    """Vector top-K by cosine distance."""
    # TODO (demo): SELECT TOP @k c.productId, c.name,
    #                     VectorDistance(c.embedding, @qv) AS score
    #              FROM c
    #              ORDER BY VectorDistance(c.embedding, @qv)
    # Pass enable_cross_partition_query=True and populate_query_metrics=True.
    print("R-VEC-1: not implemented")


def r_fts_1(container) -> None:
    """Full-text search: WHERE FullTextContainsAll(...) ORDER BY FullTextScore(...)."""
    # TODO (demo): use FullTextContainsAll(c.description, @k1, @k2) for the
    # filter and FullTextScore(c.description, @k1, @k2) for the ranking.
    print("R-FTS-1: not implemented")


def r_hyb_1(container, qv) -> None:
    """Hybrid RRF: combine vector + full-text rankings."""
    # TODO (demo):
    #   SELECT TOP @k ... FROM c
    #   ORDER BY RANK RRF(
    #     VectorDistance(c.embedding, @qv),
    #     FullTextScore(c.description, @k1, @k2)
    #   )
    print("R-HYB-1: not implemented")


def main() -> int:
    print("search.py: not implemented (see complete/search.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

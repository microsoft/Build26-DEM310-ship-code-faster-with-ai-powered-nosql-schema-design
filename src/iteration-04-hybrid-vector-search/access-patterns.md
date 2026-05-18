# Iteration 4 — Access patterns

Adds three semantic-search patterns to the iteration-02 product catalog.
All three run against a single new container, `ProductsRich`, which
mirrors `Products` but with three extra fields per document:

| Field | Type | Source |
| --- | --- | --- |
| `description` | string | Human-readable marketing blurb synthesized from `name`/`color`/`size`/`categoryName` at seed time. Indexed by the full-text policy. |
| `descriptionTokens` | int | Approximate token count, captured for cost-tracking demos. |
| `embedding` | float32[1536] | Output of `text-embedding-3-small` applied to `description`. Indexed by the vector policy as `quantizedFlat`, cosine distance. |

Partition key: `/categoryId` (same as `Products`).

---

## R-VEC-1 — Find products similar to a description

> "Show me bikes that look like *'lightweight aluminum road bike, red'*."

```sql
SELECT TOP @k c.productId, c.name, c.categoryId,
       VectorDistance(c.embedding, @qv) AS score
FROM c
ORDER BY VectorDistance(c.embedding, @qv)
```

* Cross-partition (no filter on `/categoryId`).
* Target RU: < 25 RU/query at this corpus size.
* `@qv` is the embedding of the user's query text, produced client-side
  by calling `text-embedding-3-small`.

## R-FTS-1 — Keyword search over descriptions

> "Match documents that contain both *'mountain'* and *'frame'*."

```sql
SELECT TOP @k c.productId, c.name,
       FullTextScore(c.description, "mountain", "frame") AS score
FROM c
WHERE FullTextContainsAll(c.description, "mountain", "frame")
ORDER BY FullTextScore(c.description, "mountain", "frame")
```

* Cross-partition.
* `FullTextScore` returns a BM25-style relevance score; `ORDER BY` it
  for relevance ranking.

## R-HYB-1 — Hybrid (RRF) ranking

> "Combine *'lightweight aluminum road bike, red'* (semantic) with
> *'aluminum'* and *'red'* (keywords) and rank by Reciprocal Rank Fusion."

```sql
SELECT TOP @k c.productId, c.name
FROM c
ORDER BY RANK RRF(
  VectorDistance(c.embedding, @qv),
  FullTextScore(c.description, "aluminum", "red")
)
```

* Cross-partition.
* RRF normalizes the two rankings without requiring tuned weights —
  ideal for "I want recall from semantic and precision from keywords".

---

## Why this iteration is optional

It demonstrates capabilities that are **not available in the local
Cosmos DB emulator** today. Treat iterations 1–3 as the core narrative;
add this on stage only if your audience cares about RAG / search /
recommendations and you have an Azure subscription you can spin a
resource group in.

# Iteration 4 — Hybrid + vector search (optional, cloud-only)

> This iteration **requires Azure**. The local Cosmos DB emulator does not
> support vector or full-text search today, so we provision a small cloud
> footprint via the included Bicep templates.

## What you'll do

1. Provision a Cosmos DB account (NoSQL, serverless) with the
   `EnableNoSQLVectorSearch` and `EnableNoSQLFullTextSearch` capabilities
   enabled, plus an Azure AI Foundry account with `gpt-4o-mini` and
   `text-embedding-3-small` deployed — all keyless, all via one Bicep
   deployment.
2. Run [`infra/deploy.ps1`](../../src/iteration-04-hybrid-vector-search/infra/deploy.ps1)
   and paste the printed `.env` block into `src/.env`.
3. Seed the `ProductsRich` container with embeddings.
4. Run three queries:
   * **R-VEC-1** — vector search via `VectorDistance()`
   * **R-FTS-1** — full-text search via `FullTextContainsAll` + `FullTextScore`
   * **R-HYB-1** — hybrid ranking via `ORDER BY RANK RRF(...)`

See
[`src/iteration-04-hybrid-vector-search/README.md`](../../src/iteration-04-hybrid-vector-search/README.md)
for the runbook and
[`access-patterns.md`](../../src/iteration-04-hybrid-vector-search/access-patterns.md)
for the SQL.

## Why it's optional

It demonstrates capabilities that are **not** in the local emulator and
that not every audience needs. Save it for sessions where the audience
cares about RAG / semantic search / recommendations.

## What carries over from iterations 1–3

* The same `[RU]` discipline — every query prints request-charge,
  server-reported item count, and a compact query-metrics summary.
* The same `/categoryId` partition-key pattern from iteration 2's
  `Products` container.
* The same "model the access pattern, then pick the index" workflow —
  here the new patterns drive a vector embedding policy + full-text
  policy + matching index entries (see
  [`infra/modules/cosmos.bicep`](../../src/iteration-04-hybrid-vector-search/infra/modules/cosmos.bicep)).

## Tear down

```powershell
az group delete --name rg-dem310-i4 --yes --no-wait
```

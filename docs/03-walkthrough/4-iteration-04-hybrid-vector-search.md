# Iteration 4 — Hybrid + vector search (optional, cloud-only)

> This iteration **requires Azure**. The local Cosmos DB emulator does not
> support vector or full-text search today, so we provision a small cloud
> footprint via the included Bicep templates.
>
> **Cosmos DB Agent Kit — why it matters here.** Iteration 4 stresses
> the kit's newest rule areas: **Indexing Strategies** for vector
> indexes (`quantizedFlat` vs `diskANN`, dimension/distance choices),
> **Data Modeling** for hybrid documents that carry both embeddings and
> text, and **Query Optimization** for `VectorDistance` + `FullTextScore`
> + `RANK RRF(...)` shapes. Ask the agent *"review my vector embedding
> policy and full-text policy on `ProductsRich`"* — the kit knows the
> current preview surface.
>
> **Observability.** The complete scripts in this iteration print the
> same RU + item-count + query-metrics triplet as iterations 1–3 plus
> the embedding token usage from Azure AI Foundry — so you can see both
> the Cosmos-side and the model-side cost of every hybrid query.
>
> Outside VS Code? `npx skills add AzureCosmosDB/cosmosdb-agent-kit`
> (see [setup step 3](../01-setup/3-vscode-agent.md)) brings the same
> rules into Claude Code, Gemini CLI, or JetBrains.

Product and merchandising teams want three new semantic patterns on
top of the iteration-2 `Products` container. The target document
shape, the right index types, and the infra surface that enables them
aren't obvious up front — the Agent Kit will work all of that out as
you go.

Drive the demo with the prompt sequence below; the
[Expected outcomes](#expected-outcomes--reference-key) section at the
bottom is the reference key for what the kit *should* propose. Skip it
on a first pass if you'd rather see the kit derive the answer without
anchoring on it.

## Demo flow — recommended Copilot prompts

Same six-step cadence as iterations 2 and 3, now adding semantic
capabilities on top of the iteration-2 `Products` container.

### Step 1 — Analyze the new requirements

```text
@cosmos Product and merchandising teams want three new patterns:

  R-VEC-1: "find products similar to this description" (semantic).
  R-FTS-1: "find products whose description matches these words".
  R-HYB-1: "best of both — keyword relevance + semantic similarity".

Given the iteration-2 Products container (partitioned by /categoryId),
recommend a target document shape that carries both an embedding and
text fields, and tell me which Cosmos DB for NoSQL features I need
(vector index type, full-text policy, hybrid RANK RRF) and the
tradeoffs of each choice.
```

### Step 2 — Generate the infrastructure

```text
@cosmos Produce a Bicep deployment that creates:
  - An Azure Cosmos DB for NoSQL account (serverless) with the
    EnableNoSQLVectorSearch and EnableNoSQLFullTextSearch capabilities.
  - A `ProductsRich` container partitioned by /categoryId with the
    vector embedding policy and full-text policy you recommended.
  - An Azure AI Foundry account with gpt-4o-mini and
    text-embedding-3-small deployments.
  - All access keyless (Entra ID + RBAC); no account keys, no connection
    strings. Output a .env block I can paste into src/.env.
```

Reference output: [`infra/`](../../src/iteration-04-hybrid-vector-search/infra/).

### Step 3 — Validate the deployed structures

```text
@cosmos After deployment, inspect the Cosmos DB account and confirm:
  - Both vector-search and full-text-search capabilities are enabled.
  - ProductsRich has the vector embedding policy on the field I named,
    with the dimensions and distance function I proposed.
  - The full-text policy is set on the right text fields.
  - The container's indexing policy includes the matching vector and
    full-text index entries.
Flag any drift between what I asked for and what is actually deployed.
```

### Step 4 — Seed embeddings and scaffold the search code

```text
@cosmos Generate seed.py and search.py for ProductsRich:
  - seed.py: read products, call text-embedding-3-small via Entra ID,
    upsert each product with its embedding and full-text fields.
  - search.py: three functions, one per R-VEC-1 / R-FTS-1 / R-HYB-1,
    each logging requestCharge, item count, query metrics, and the
    embedding token usage from Azure AI Foundry.
```

### Step 5 — Execute the three queries

```powershell
cd src/iteration-04-hybrid-vector-search
python complete/seed.py
python complete/search.py vec  "lightweight aluminum mountain bike for trails"
python complete/search.py fts  "helmet visor adjustable"
python complete/search.py hyb  "comfortable long-distance road bike saddle"
```

### Step 6 — Ask the agent to interpret the results

```text
@cosmos Here are the request charges, top-k results, and (for R-HYB-1)
the RRF rank fusion output for each query (paste them). For each one,
explain which feature dominated the result ordering, where the vector
index earned its cost, and whether the full-text policy is catching the
right fields. Recommend one tweak per query if you'd change anything.
```

## Why it's optional

It demonstrates capabilities that are **not** in the local emulator
and that aren't needed for every walkthrough. Run it when you care
about RAG / semantic search / recommendations on top of the
iteration-2 schema.

## What carries over from iterations 1–3

* The same `[RU]` discipline — every query prints request-charge,
  server-reported item count, and a compact query-metrics summary.
* The same `/categoryId` partition-key pattern from iteration 2's
  `Products` container.
* The same "model the access pattern, then pick the index" workflow —
  here the new patterns drive a vector embedding policy + full-text
  policy + matching index entries.

## Tear down

```powershell
az group delete --name rg-dem310-i4 --yes --no-wait
```

## Expected outcomes — reference key

> **Reference section.** This is what the Agent Kit *should* propose
> for this iteration. Skip it on a first pass if you'd rather see the
> kit derive the answer without anchoring on it.

### Expected deployment surface

1. Cosmos DB account (NoSQL, serverless) with the
   `EnableNoSQLVectorSearch` and `EnableNoSQLFullTextSearch` capabilities.
2. A `ProductsRich` container partitioned by `/categoryId` with a vector
   embedding policy and full-text policy on the description-bearing
   text fields.
3. An Azure AI Foundry account with `gpt-4o-mini` and
   `text-embedding-3-small` deployments.
4. All access keyless (Entra ID + RBAC) — no account keys, no
   connection strings.

Provisioned by [`infra/deploy.ps1`](../../src/iteration-04-hybrid-vector-search/infra/deploy.ps1);
the matching Bicep reference is in
[`infra/modules/cosmos.bicep`](../../src/iteration-04-hybrid-vector-search/infra/modules/cosmos.bicep).

### Expected query surface

Three queries on `ProductsRich`:

* **R-VEC-1** — vector search via `VectorDistance()`
* **R-FTS-1** — full-text search via `FullTextContainsAll` + `FullTextScore`
* **R-HYB-1** — hybrid ranking via `ORDER BY RANK RRF(...)`

Reference SQL is in
[`access-patterns.md`](../../src/iteration-04-hybrid-vector-search/access-patterns.md);
the end-to-end runbook is in
[`src/iteration-04-hybrid-vector-search/README.md`](../../src/iteration-04-hybrid-vector-search/README.md).

If the results you observe don't match the reference, use Step 6's
interpretation prompt to find out why — typical causes are an
undersized embedding model, a full-text policy that misses key fields,
or a vector index type chosen for the wrong dimensionality.

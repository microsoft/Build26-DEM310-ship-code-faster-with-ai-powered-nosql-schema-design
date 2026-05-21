# Iteration 4 — Hybrid + vector search (bonus-take home, cloud-only)

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

## The three new patterns

All three patterns run cross-partition against a new `ProductsRich`
container that mirrors iteration 2's `Products` but carries three
extra fields per document:

| Field | Type | Source |
| --- | --- | --- |
| `description` | string | Marketing blurb synthesized at seed time from `name` / `color` / `size` / `categoryName`. |
| `descriptionTokens` | int | Approximate token count, captured for cost-tracking. |
| `embedding` | float32[1536] | `text-embedding-3-small` applied to `description`. |

Partition key: `/categoryId` (same as `Products`). The container,
vector policy, full-text policy, and account capabilities don't yet
exist — the agent designs them in Step 1 and the Bicep generated in
Step 2 provisions them.

### R-VEC-1 — Semantic similarity

```sql
SELECT TOP @k c.productId, c.name, c.categoryId,
       VectorDistance(c.embedding, @qv) AS score
FROM c
ORDER BY VectorDistance(c.embedding, @qv)
```

`@qv` is the embedding of the user's query text, produced client-side
by calling `text-embedding-3-small`.

### R-FTS-1 — Keyword full-text search

```sql
SELECT TOP @k c.productId, c.name,
       FullTextScore(c.description, "mountain", "frame") AS score
FROM c
WHERE FullTextContainsAll(c.description, "mountain", "frame")
ORDER BY FullTextScore(c.description, "mountain", "frame")
```

`FullTextScore` returns a BM25-style relevance score.

### R-HYB-1 — Hybrid ranking (RRF)

```sql
SELECT TOP @k c.productId, c.name
FROM c
ORDER BY RANK RRF(
  VectorDistance(c.embedding, @qv),
  FullTextScore(c.description, "aluminum", "red")
)
```

RRF normalizes the two rankings without tuned weights — recall from
semantic, precision from keywords.

## Demo flow — recommended Copilot prompts

Three steps. Unlike iteration 3 (where an existing iteration-2 surface
gives the agent a baseline to measure against), iteration 4 must
*design* a new surface before any code can run. Step 1 produces that
design as a checkpoint file; Step 2 provisions it and validates the
deployed surface against the spec as a hard gate; Step 3 runs the
three queries and interprets the captured metrics.

### Step 1 — Propose the ProductsRich design

```text
@cosmos Read the "The three new patterns" section of
`docs/03-walkthrough/4-iteration-04-hybrid-vector-search.md` — it
defines R-VEC-1, R-FTS-1, R-HYB-1 with their SQL and the ProductsRich
field list (description, descriptionTokens, embedding).

Propose the full infra + data shape needed to serve these three
patterns on top of the iteration-2 catalog. Write the recommendation
to `iteration-04-output.md` at the repo root. Include:

  - Cosmos DB account capabilities (vector search, full-text search).
  - ProductsRich container: partition key and indexing policy.
  - Vector embedding policy: path, dimensions, distance function,
    index type (quantizedFlat vs diskANN) — with the tradeoff that
    drove the choice at this corpus size.
  - Full-text policy: which text path(s) it covers and why.
  - Azure AI Foundry: model deployments (embedding + chat), tier,
    region, keyless access plan (Entra ID + RBAC).

This file is a checkpoint: I will review it before Step 2 generates
Bicep from it.
```

> **Checkpoint.** Open `iteration-04-output.md` and confirm the design
> matches your intent. Edit the file (or re-prompt) until you're
> satisfied — Step 2's Bicep encodes exactly these choices.
>
> **Why is there an upfront design step here when iteration 3 dropped it?**
> Iteration 3 had a deployed iteration-2 surface to measure against and
> could drive composite-index choices from baseline RU. Iteration 4
> has no surface yet — Bicep needs a concrete target shape decided
> first. The evidence-driven feedback loop returns in Step 3.

### Step 2 — Provision, validate (hard gate), seed, scaffold queries

```text
@cosmos Read `iteration-04-output.md` and treat it as the source of
truth. Perform all of the following as a single workflow, and STOP if
any phase fails or any drift is detected:

  1. Generate Bicep under `src/iteration-04-hybrid-vector-search/infra/`
     that provisions exactly the surface described in
     `iteration-04-output.md`: Cosmos DB account capabilities,
     ProductsRich container with its partition key, vector embedding
     policy, full-text policy, indexing policy, and the Azure AI
     Foundry account with the listed model deployments. Keyless
     (Entra ID + RBAC) — no keys, no connection strings.

  2. Deploy the Bicep. Emit a `.env` block I can paste into `src/.env`.

  3. Inspect the deployed Cosmos DB account and Foundry account and
     compare against `iteration-04-output.md`. Verify capabilities,
     vector policy (path, dimensions, distance, index type), full-text
     policy paths, indexing policy entries, and model deployment names
     all match. If anything drifts from the spec, STOP HERE, report
     the drift, and do not proceed to seeding.

  4. Generate `scripts/seed_iteration_04.py`: read products from
     `src/sample-data/master/products.json`, call text-embedding-3-small
     via DefaultAzureCredential, upsert each product with its
     description + descriptionTokens + embedding. Log progress and
     total embedding tokens consumed to `logs/iter-04/seed.log`.

  5. Add three functions to `demo/app/queries.py` — one per R-VEC-1,
     R-FTS-1, R-HYB-1. Every function MUST log on each call:

       - requestCharge (RU) and item count.
       - Query metrics summary (same shape as iterations 1–3).
       - For R-VEC-1 and R-HYB-1: the VectorDistance score for each
         returned item.
       - For R-FTS-1 and R-HYB-1: the FullTextScore value for each
         returned item.
       - For R-HYB-1: a per-result RRF component breakdown — which
         signal (vector vs full-text) earned each rank slot.
       - Embedding tokens charged by Foundry for the query embedding
         (vec + hyb only).

     Extend the CLI:
     `python -m demo.app.queries {vec|fts|hyb} "<text>" [--log PATH]`.
     Run each subcommand once against a smoke query to confirm wiring.
```

> **Hard gate.** The drift check in phase 3 is the only validation
> the human needs here. If the agent reports drift, fix the Bicep or
> `iteration-04-output.md` and re-run Step 2. Do not run Step 3
> against a deployment that doesn't match the spec.

### Step 3 — Execute, interpret, recommend tweaks

```text
@cosmos Read the "The three new patterns" section of
`docs/03-walkthrough/4-iteration-04-hybrid-vector-search.md` for the
query shapes, then drive the demo end-to-end:

  1. Run all three queries, capturing per-query logs:

       python -u -m demo.app.queries vec \
         "lightweight aluminum mountain bike for trails" \
         --log logs/iter-04/vec.log
       python -u -m demo.app.queries fts \
         "helmet visor adjustable" \
         --log logs/iter-04/fts.log
       python -u -m demo.app.queries hyb \
         "comfortable long-distance road bike saddle" \
         --log logs/iter-04/hyb.log

  2. Read all three log files. For each query produce:

       - Top-3 results with their VectorDistance and/or FullTextScore.
       - Request charge (RU) and embedding tokens consumed.
       - Which signal dominated the ordering (vector, full-text, or
         RRF tie-break for hyb).

  3. Write `iteration-04-analysis.md` at the repo root with a
     comparison table:

       Query | Top-1 product | RU | Embedding tokens | Dominant signal

     Then recommend ONE specific tweak per query grounded in the
     captured metrics — for example, "R-FTS-1 missed 'helmet' results
     because the full-text policy only covers /description; extend it
     to /name", or "R-VEC-1 score range is tight (0.18-0.22), consider
     diskANN for better recall at this corpus size". Every
     recommendation must cite the measurement that motivated it.
```

> **Checkpoint.** `iteration-04-analysis.md` is the takeaway artifact.
> To apply a recommendation, update `iteration-04-output.md` and
> re-run Step 2 — the hard gate will confirm the new state matches the
> revised spec.

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

Reference SQL for all three is in [The three new patterns](#the-three-new-patterns)
above; the end-to-end runbook is in
[`src/iteration-04-hybrid-vector-search/README.md`](../../src/iteration-04-hybrid-vector-search/README.md).

If the results you observe don't match the reference, use Step 6's
interpretation prompt to find out why — typical causes are an
undersized embedding model, a full-text policy that misses key fields,
or a vector index type chosen for the wrong dimensionality.

# Iteration 3 — Composite indexes (optional)

Source code: [`/src/iteration-03-composite-indexes`](../../src/iteration-03-composite-indexes/)

> **Cosmos DB Agent Kit — why it matters here.** Iteration 3 leans on
> two skill categories: **Indexing Strategies** (when a composite index
> earns its cost vs an `ORDER BY` scan, ordering of paths, ASC/DESC
> semantics) and **Query Optimization** (matching the index to the
> query shape). Ask the agent things like *"propose composite indexes
> for these three new patterns and explain the RU saving"* — the kit
> will return the same `[type ASC, orderDate DESC]` shape used below.
>
> **Observability.** Every `queries.py` run prints the
> `indexHitDocumentCount` / `outputDocumentCount` ratio from query
> metrics — that's the diagnostic the kit teaches you to read when
> deciding whether an index policy change actually helped. Re-run
> before and after `--apply-policy` to see both numbers change together
> with the RU drop.
>
> Outside VS Code? `npx skills add AzureCosmosDB/cosmosdb-agent-kit`
> (see [setup step 3](../01-setup/3-vscode-agent.md)) brings the same
> rules into Claude Code, Gemini CLI, or JetBrains.

This iteration is the "we'd ship this next" stretch. After iteration 2
is in place, three new access patterns surface from production
telemetry. The question is whether the iteration-2 schema can serve
them efficiently — that's what the Agent Kit will work out in this
iteration.

Drive the demo with the prompt sequence below; the
[Expected outcomes](#expected-outcomes--reference-key) section at the
bottom is the reference key for what the kit *should* propose. Skip it
on a first pass if you'd rather see the kit derive the answer without
anchoring on it.

Full reference for the new patterns:
[`extended-access-patterns.md`](../../src/iteration-03-composite-indexes/complete/extended-access-patterns.md).

## Demo flow — recommended Copilot prompts

Same six-step cadence as iteration 2, applied to the new requirements:
analyze → propose → validate the deployed policy → update code/queries →
execute → interpret.

### Step 1 — Analyze the new requirements

```text
@cosmos Iteration 2 has shipped. Telemetry now shows three additional
patterns we didn't model for:

  R-EXT-1: customer order history filtered by date range, recent first.
  R-EXT-2: open-orders dashboard — all orders in status 'Placed',
           most recent first, across customers.
  R-EXT-3: products in a category, sorted by rating DESC then price ASC.

For each one, tell me whether the iteration-2 schema can serve it
efficiently as-is, and what (if anything) needs to change. Don't change
the partition keys.
```

### Step 2 — Propose the index changes

```text
@cosmos For each pattern that needs help, propose the minimum indexing
policy change — prefer composite indexes over re-partitioning or new
containers. Show me the merged indexing-policy.json for each container
and explain the ASC/DESC ordering for every composite path.
```

The agent should produce something equivalent to
[`indexing-policy.json`](../../src/iteration-03-composite-indexes/complete/indexing-policy.json).

### Step 3 — Validate the deployed policy

```text
@cosmos After I apply the new indexing policy, inspect both containers
and confirm the composite indexes are present and in the order I
proposed. Flag any drift.
```

### Step 4 — Update the queries

```text
@cosmos Add three query functions to queries.py — one per R-EXT-* pattern.
Use parameterized queries, keep them single-partition where possible
(R-EXT-1 and R-EXT-3 are; R-EXT-2 is intentionally cross-customer), and
log requestCharge, indexHitDocumentCount, outputDocumentCount, and a
short query-metrics summary on every call.
```

### Step 5 — Execute before and after

```powershell
cd src/iteration-03-composite-indexes
python complete/queries.py                   # before — ORDER BY scans
python complete/queries.py --apply-policy    # apply composite indexes
python complete/queries.py                   # after  — index-served
```

### Step 6 — Ask the agent to interpret the metrics

```text
@cosmos Here are the before/after numbers for each R-EXT pattern
(paste requestCharge, indexHitDocumentCount, outputDocumentCount).
Explain which composite index removed the in-memory sort, where the
indexHit/output ratio improved, and whether any pattern is still doing
more work than it should.
```

## Expected outcomes — reference key

> **Reference section.** This is what the Agent Kit *should* propose
> for this iteration. Skip it on a first pass if you'd rather see the
> kit derive the answer without anchoring on it.

### Expected composite indexes

| Container        | Composite index                            | Pattern it serves |
|------------------|--------------------------------------------|-------------------|
| `CustomerOrders` | `[type ASC, orderDate DESC]`               | R-EXT-1           |
| `CustomerOrders` | `[status ASC, orderDate DESC]`             | R-EXT-2           |
| `Products`       | `[rating DESC, price ASC]`                 | R-EXT-3           |

The full expected policy is in
[`indexing-policy.json`](../../src/iteration-03-composite-indexes/complete/indexing-policy.json).
`queries.py --apply-policy` reads that file, splits it per container,
and calls `replace_container(..., indexing_policy=...)` on each.

### Expected before/after

Re-run the queries before and after `--apply-policy`:

- **Request charge** drops on each R-EXT-* pattern once its composite
  index is in place.
- `indexHitDocumentCount` / `outputDocumentCount` ratio tightens — the
  index now returns close to only the rows you need, instead of the
  engine sorting in memory after the fact.

If the numbers you observe don't match, use Step 6's interpretation
prompt to find out which composite index didn't earn its cost.

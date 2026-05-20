# Iteration 3 — Composite indexes (optional)

Runtime code lives in [`demo/app/queries.py`](../../demo/app/queries.py)
and the apply/bench tooling in [`scripts/`](../../scripts/) per
[CONVENTIONS.md](./CONVENTIONS.md). The folder
[`src/iteration-03-composite-indexes/`](../../src/iteration-03-composite-indexes/)
is reference content only.

> Already have the iteration-3 solution checked in? Skip the prompts
> below and use the runbook in
> [`3-iteration-03-composite-indexes-complete.md`](./3-iteration-03-composite-indexes-complete.md)
> to run the combined before/after harness directly.

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

Write the full analysis and proposed index/design changes to
`iteration-03-output.md` at the repo root — include per-pattern
verdict, recommended composite indexes (with ASC/DESC ordering and
rationale), and any query-shape adjustments. This file is a checkpoint:
I will review it before moving on to Step 2.
```

> **Checkpoint.** Before continuing, open `iteration-03-output.md` and
> confirm the proposed indexing changes match your intent. Edit the
> file (or re-prompt the agent) until you're satisfied — Steps 2–6
> apply this plan.

### Step 2 — Apply and validate the index changes

Drive apply + validation from the checkpoint file so the deployed
policy is whatever you approved in Step 1 — no hardcoded container or
index specifics in this prompt:

```text
@cosmos Read `iteration-03-output.md` and use it as the source of truth.
For each affected container, start from the iteration-2 indexing policy
currently deployed on the emulator (fetch it live; do not assume) and
generate a merged `indexing-policy.json` that preserves every existing
included/excluded path and composite index from iteration 2 and adds
the new composite indexes (and any other index changes) described in
`iteration-03-output.md`. Do not drop or rewrite iteration-2 entries.
Apply the merged policy to the emulator. After apply, inspect each
container and confirm the resulting indexing policy is the union of the
iteration-2 baseline and the iteration-03-output.md additions — paths,
ASC/DESC ordering, and composite groupings. Flag any drift or any
iteration-2 entry that went missing.
```

The generated policy should be equivalent to
[`indexing-policy.json`](../../src/iteration-03-composite-indexes/complete/indexing-policy.json)
for the reference design — your file will reflect whatever
`iteration-03-output.md` specifies.

### Step 3 — Validate the deployed policy

```text
@cosmos After I apply the new indexing policy, inspect both containers
and confirm the composite indexes are present and in the order I
proposed. Flag any drift.
```

### Step 4 — Update the queries

```text
@cosmos Add three query functions to `demo/app/queries.py` — one per
R-EXT-* pattern. Use parameterized queries (R-EXT-1 and R-EXT-3 are; R-EXT-2 is intentionally
cross-customer),  log requestCharge, indexHitDocumentCount (if
emitted), outputDocumentCount, retrievedDocumentCount, and a short
query-metrics summary on every call. Expose a CLI:
`python -m demo.app.queries {r1|r2|r3|all} [--limit N] [--log PATH]`.
```

### Step 5 — Single combined before/after harness

Replace the manual revert/run/apply/run dance with one orchestrated
script so the log captures a clean, reproducible comparison.

```text
@cosmos Generate `scripts/bench_iteration_03.py` that runs the full
before/after cycle in one invocation:

  1. Apply the iteration-2 baseline indexing policy
     (no R-EXT composites). Wait for indexing to settle.
  2. Run every R-EXT-* query and capture per-call requestCharge plus
     the raw `x-ms-documentdb-query-metrics` headers. Tag the rows
     `label="before"`. Persist the raw capture to
     `logs/iter-03/bench-before.json`.
  3. Apply the iteration-3 policy (= iter-2 + the new composites from
     `iteration-03-output.md`). Wait for indexing to settle.
  4. Re-run the same queries; tag rows `label="after"`; persist to
     `logs/iter-03/bench-after.json`.
  5. Emit a markdown comparison table to stdout AND to
     `logs/iter-03/bench.log` with columns:
       Pattern | Before RU | After RU | Δ RU | Δ % |
       retrieved/output before | retrieved/output after | Verdict
     where Verdict is one of ✓ healthy / ⚠ partial / ✗ regression.
  

Do not change partition keys. Honour the apply scripts in `scripts/`
(`apply_iteration_02.py`, `apply_iteration_03.py`) rather than
re-implementing the policy merge. Handle the case where R-EXT-3
returns 400 BadRequest in the `before` pass (no composite supports
the 3-key ORDER BY) and record it as a graceful `before` failure
rather than aborting.
```

Run it:

```powershell
python -u -m scripts.bench_iteration_03
```

### Step 6 — Ask the agent to interpret the metrics

```text
@cosmos Read `logs/iter-03/bench.log` plus the raw captures
`logs/iter-03/bench-before.json` and `logs/iter-03/bench-after.json`.
For each R-EXT pattern, explain which composite index removed the
in-memory sort, where the retrieved/output ratio tightened, and
whether any pattern is still doing more work than it should. If
R-EXT-3 failed in the `before` pass with 400 BadRequest, explain
why (3-path composite + multi-key ORDER BY) and confirm the
workaround in `queries.py` is the correct one.
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

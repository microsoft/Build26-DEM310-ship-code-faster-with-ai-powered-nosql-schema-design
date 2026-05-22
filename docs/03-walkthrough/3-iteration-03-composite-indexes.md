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
> Outside Visual Studio Code? `npx skills add AzureCosmosDB/cosmosdb-agent-kit`
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

## The three new patterns

These are the queries production telemetry surfaced after iteration 2
shipped. Container layout and partition keys are unchanged from
iteration 2 — only the query shapes are new. **No index changes are
suggested here on purpose**; the agent will derive them from measured
baseline metrics in Step 3.

### R-EXT-1 — Customer order history by date range

> "Show me everything customer C00005 ordered in Q1 2026, most recent first."

```sql
SELECT * FROM c
WHERE  c.type = 'order'
  AND  c.customerId = @cid
  AND  c.orderDate >= @from
  AND  c.orderDate <  @to
ORDER  BY c.orderDate DESC
```

- Container: `CustomerOrders` (partition key `/customerId`)
- In-partition (filter on `customerId`).

### R-EXT-2 — Open-orders dashboard

> "List every order in `Placed` status across the platform, most recent first."

```sql
SELECT c.orderId, c.customerId, c.orderDate, c.totalAmount
FROM   c
WHERE  c.type = 'order'
  AND  c.status = @status
ORDER  BY c.orderDate DESC
```

- Container: `CustomerOrders` (partition key `/customerId`)
- Intentionally **cross-partition** — no `customerId` filter, by
  design, because it's an admin/ops dashboard view.

### R-EXT-3 — Product browsing by rating + price

> "Show me the highest-rated products in CAT006; for ties show the cheapest first."

```sql
SELECT c.productId, c.name, c.rating, c.price
FROM   c
WHERE  c.categoryId = @cid
ORDER  BY c.rating DESC, c.price ASC
```

- Container: `Products` (partition key `/categoryId`)
- In-partition. Two-column `ORDER BY` mixing DESC + ASC.

## Demo flow — recommended Copilot prompts

Three steps, evidence-driven: write queries (with index metrics on)
→ **baseline + analyze + propose** in one prompt → **apply +
validate + re-run + interpret** in one prompt.

The key shift from iteration 2: composite indexes are *justified by
observed RU, `retrieved/output` ratios, and Cosmos DB's own index
utilization metrics*, not guessed from the requirements text. R-EXT-3
will fail with **400 BadRequest** against the iter-2 baseline — that's
the point, and it's the most powerful teaching moment in this
iteration.

> **Why so few steps?** Earlier versions of this flow had separate
> "run the baseline" / "apply policy" / "re-run" PowerShell steps
> between each analysis prompt. The agent can invoke those commands
> itself as tool calls, and the drift check at the end of the apply
> phase is a hard gate — if the deployed policy doesn't match
> `iteration-03-output.md`, the agent stops and reports instead of
> re-running. One human checkpoint remains: review
> `iteration-03-output.md` after Step 2 before kicking off Step 3.

### Step 1 — Add the three query functions (with index metrics enabled)

```text
@cosmos Read the "The three new patterns" section of
`docs/03-walkthrough/3-iteration-03-composite-indexes.md`. It defines
three patterns — R-EXT-1, R-EXT-2, R-EXT-3 — with the exact SQL,
target container, partition key, and parameter shape for each.

Add one query function per pattern to `demo/app/queries.py`, using the
SQL exactly as written in that section. Use parameterized queries
(R-EXT-1 and R-EXT-3 take parameters; R-EXT-2 is intentionally
cross-partition by design).

Every call must enable Cosmos DB indexing metrics per
https://learn.microsoft.com/azure/cosmos-db/index-metrics?tabs=python:

  - Pass `populate_index_metrics=True` to `container.query_items(...)`.
  - After draining results, read
    `container.client_connection.last_response_headers
        ['x-ms-cosmos-index-utilization']`
    and log the decoded text. It contains four sections — Utilized
    Single Indexes, Potential Single Indexes, Utilized Composite
    Indexes, Potential Composite Indexes — each with an Index Impact
    Score (High / Low). The `Potential Composite Indexes` block is
    exactly the signal we'll use in Step 2 to propose composites.

For every call also log requestCharge, indexHitDocumentCount (if
emitted), outputDocumentCount, retrievedDocumentCount, and a short
query-metrics summary. Expose a CLI:
`python -m demo.app.queries {r1|r2|r3|all} [--limit N] [--log PATH]`.

Do NOT change indexing policy in this step. The queries must run
against whatever policy is currently deployed (iteration-2 baseline).
On 400 BadRequest, log the error (including any
`x-ms-cosmos-index-utilization` header the server returned) and
continue with the remaining patterns — do not abort the run.
```

> **SDK version note.** `populate_index_metrics` requires `azure-cosmos`
> **>= 4.6.0** (Python). The header is only returned when the query
> yields at least one item; record `index_utilization=None` for
> empty/erroring responses.

### Step 2 — Capture the baseline, analyze it, and propose composites

```text
@cosmos Run the baseline yourself, then analyze and propose:

  1. Execute `python -u -m demo.app.queries all
     --log logs/iter-03/baseline.log` against the deployed iteration-2
     policy. Expect R-EXT-1 and R-EXT-2 to succeed with high RU and
     `retrievedDocumentCount` ≫ `outputDocumentCount`; expect R-EXT-3
     to return 400 BadRequest because no composite supports its
     multi-key ORDER BY. None of those are failures of the run.

  2. Read `logs/iter-03/baseline.log` along with the
     "The three new patterns" section of
     `docs/03-walkthrough/3-iteration-03-composite-indexes.md` so you
     know each pattern's container and query shape.

  3. For each R-EXT pattern, combine three signals:
       a. RU charge and the retrieved/output ratio (how much work was
          wasted).
       b. The decoded `x-ms-cosmos-index-utilization` payload —
          specifically the "Potential Composite Indexes" section and
          its Index Impact Score (focus on High first; treat Low as
          advisory).
       c. For R-EXT-3, the 400 BadRequest and what its ORDER BY shape
          implies about the composite that *would* satisfy it.

  4. Produce two artifacts at the repo root:
       - `iteration-03-analysis.md`: per-pattern findings — observed
         RU, retrieved/output, the verbatim "Potential Composite
         Indexes" block, and a one-line diagnosis ("filter+sort done
         in memory", "ORDER BY unsupported", etc.).
       - `iteration-03-output.md`: proposed composite indexes per
         container, with path ordering, ASC/DESC, and a one-line
         rationale citing the specific metric or potential-index
         entry it answers (e.g. "R-EXT-2: retrieved 500 / output 20 +
         potential composite `/status ASC, /orderDate DESC` High →
         adopt as-is").

Don't change partition keys. `iteration-03-output.md` is a
checkpoint: I will review it before applying.
```

The generated proposal should converge on
[`indexing-policy.json`](../../src/iteration-03-composite-indexes/complete/indexing-policy.json)
for the reference design.

### Step 3 — Apply, validate, re-run, and interpret

```text
@cosmos Once I've approved `iteration-03-output.md`, run the full
apply-through-interpret cycle in one pass:

  1. **Merge.** Read `iteration-03-output.md` for the new composite
     indexes. Load the iteration-2 baseline indexing policy — the
     reference is at
     `src/iteration-02-optimized/complete/indexing-policy.json` (or
     read it live from the deployed containers on the emulator). For
     each affected container (the patterns section in
     `docs/03-walkthrough/3-iteration-03-composite-indexes.md` names
     `CustomerOrders` and `Products`), generate a merged
     `indexing-policy.json` that adds the new composites on top of
     the iter-2 baseline.

  2. **Apply.** Push the merged policy to the emulator and wait for
     indexing to settle.

  3. **Validate (hard gate).** Inspect each container and confirm
     the deployed policy is the exact union of the iteration-2
     baseline and the additions from `iteration-03-output.md` —
     paths, ASC/DESC ordering, and composite groupings. If you
     detect any drift, any missing iteration-2 entry, or any extra
     composite that wasn't approved, **STOP HERE**, report the
     drift, and do not proceed. Do not re-run the queries until I've
     reviewed and re-approved.

  4. **Re-run.** If validation passes, execute
     `python -u -m demo.app.queries all --log logs/iter-03/after.log`.
     R-EXT-3 should now succeed. R-EXT-1 and R-EXT-2 should show
     lower RU, a tightened retrieved/output ratio, and the
     previously-listed composites should now appear under "Utilized
     Composite Indexes" in the `x-ms-cosmos-index-utilization`
     payload instead of "Potential".

  5. **Interpret.** Compare `logs/iter-03/baseline.log` (iteration-2
     policy) and `logs/iter-03/after.log` (iteration-3 policy). For
     each R-EXT pattern, explain:

       - Which composite index removed the in-memory sort or
         cross-partition scan, citing the specific RU delta, the
         retrieved/output change, AND the migration of that index
         from "Potential Composite Indexes" (before) to "Utilized
         Composite Indexes" (after) in
         `x-ms-cosmos-index-utilization`.
       - Why R-EXT-3 went from 400 BadRequest → success (3-path
         composite enabling the multi-key ORDER BY).
       - Whether any pattern is still doing more work than it
         should — in particular, any new High-impact entries still
         showing under "Potential" in the `after` log are next-step
         candidates.

  6. Cross-check the interpretation against the findings in
     `iteration-03-analysis.md` — flag any diagnosis that turned out
     wrong.
```

> **Optional — reproducible artifact.** Once the prompt flow is dialed
> in, the runbook in
> [`3-iteration-03-composite-indexes-complete.md`](./3-iteration-03-composite-indexes-complete.md)
> wraps Steps 2 and 3 in a single `scripts/bench_iteration_03.py`
> harness for a clean, one-shot before/after capture.

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

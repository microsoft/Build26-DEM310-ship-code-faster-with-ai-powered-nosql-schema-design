# Iteration 3 — Runbook (execute the finished solution)

This is the **non-prompt** runbook for an already-checked-in iteration-3
solution. Use it to:

- Demo the composite-index before/after story without re-prompting the
  agent.
- Verify that prompt changes in
  [`3-iteration-03-composite-indexes.md`](./3-iteration-03-composite-indexes.md)
  still produce code that reproduces this reference run.

The runbook mirrors the interactive flow but collapses Steps 2 and 3
of that doc (baseline run + analyze + propose; apply + validate +
re-run + interpret) into a single reproducible harness,
`scripts/bench_iteration_03.py`.
The bench harness assumes `demo/app/queries.py` already enables
`populate_index_metrics=True` and captures the
`x-ms-cosmos-index-utilization` header per
https://learn.microsoft.com/azure/cosmos-db/index-metrics?tabs=python.

Layout assumed: see [CONVENTIONS.md](./CONVENTIONS.md).

---

## Prerequisites

- Iteration 2 already run end-to-end via
  [`2-iteration-02-optimized-complete.md`](./2-iteration-02-optimized-complete.md).
  Containers `CustomerOrders` and `Products` exist on the emulator
  with iter-2 data seeded and the iter-2 indexing policy deployed.
- `demo/app/queries.py` contains the three R-EXT-* functions and the
  `r1|r2|r3|all` CLI (produced by Step 1 of the interactive flow),
  including `populate_index_metrics=True` and capture of the
  `x-ms-cosmos-index-utilization` response header.
- `azure-cosmos` Python SDK >= 4.6.0 (required for
  `populate_index_metrics`).

---

## Step A — Manual baseline against the iter-2 policy (optional sanity check)

Mirrors the first half of Step 2 of the interactive flow. Skip if you
trust the bench harness to do the same capture.

```powershell
python -u -m demo.app.queries all --log logs/iter-03/preflight.log
```

R-EXT-1 and R-EXT-2 succeed but log high RU and
`retrievedDocumentCount` ≫ `outputDocumentCount`. Their
`x-ms-cosmos-index-utilization` payloads list the iter-3 composites
as **Potential Composite Indexes** with **High** impact score.
R-EXT-3 is expected to **fail with 400 BadRequest** — the 3-path
composite + multi-key `ORDER BY` is exactly the gap iter-3 closes.
`queries.py` logs the error and continues with the remaining
patterns.

## Step B — Combined before/after harness (the headline)

```powershell
python -u -m scripts.bench_iteration_03
```

What it does (= interactive Steps 2 → 3, automated):

1. Asserts the iter-2 baseline policy is deployed (no R-EXT
   composites). If not, applies it and waits for indexing to settle.
2. Runs every R-EXT-* query against the baseline policy with
   `populate_index_metrics=True`. Captures per-call requestCharge,
   raw `x-ms-documentdb-query-metrics`, AND the decoded
   `x-ms-cosmos-index-utilization` payload (Utilized / Potential,
   Single / Composite, Index Impact Score). Tags rows
   `label="before"`. Persists to `logs/iter-03/bench-before.json`.
   Records R-EXT-3's 400 BadRequest as a graceful `before` failure —
   **expected, not a regression**.
3. Applies the iter-3 policy (= iter-2 + the new composites from
   `iteration-03-output.md`). Waits for indexing to settle.
4. Re-runs the same queries; tags rows `label="after"`; persists to
   `logs/iter-03/bench-after.json`. R-EXT-3 now succeeds and the
   previously-Potential composites should now appear under Utilized
   Composite Indexes.
5. Writes a markdown comparison table to `logs/iter-03/bench.log`
   and stdout. Table includes a `potential→utilized` column that
   shows the migration of each composite between the before/after
   `x-ms-cosmos-index-utilization` payloads.
6. Exits non-zero only on a true regression (an `after` row that's
   worse than its `before` counterpart). R-EXT-3's `before` 400 →
   `after` success is **not** a regression.

### Expected `bench.log` shape

| Pattern  | Before RU | After RU | Δ RU  | Δ %    | retrieved/output before | retrieved/output after | Verdict |
|----------|-----------|----------|-------|--------|--------------------------|-------------------------|---------|
| R-EXT-1  | ~8        | ~3       | -5    | -60%   | 50 / 50 (sort in mem)    | 5 / 5                   | ✓ healthy |
| R-EXT-2  | ~25       | ~8       | -17   | -68%   | 500 / 20 (cross-part)    | 20 / 20                 | ✓ healthy |
| R-EXT-3  | 400 ERR   | ~3       | n/a   | n/a    | n/a                      | 10 / 10                 | ✓ healthy (newly viable) |

Exact RU depends on emulator build and seed size; what matters is the
order-of-magnitude shape and the `retrieved == output` flip.

## Step C — Verify final policy is exactly the iter-3 spec

```powershell
python -u -m scripts.apply_iteration_03
```

Expected: `drift==0`, both containers reported with these composites:

- `CustomerOrders`:
  `[/customerId ASC, /orderDate DESC]` **and**
  `[/status ASC, /orderDate DESC]`
- `Products`:
  `[/type ASC, /price ASC]` **and**
  `[/type ASC, /rating DESC, /price ASC]`

## Step D — One-shot agent recap

Mirrors the interpret phase of Step 3 of the interactive flow, but
reads the bench captures instead of the manual `baseline.log` /
`after.log` pair.

```text
@cosmos Read the "The three new patterns" section of
`docs/03-walkthrough/3-iteration-03-composite-indexes.md` for the
R-EXT pattern definitions, then read `logs/iter-03/bench.log` plus
the raw captures `logs/iter-03/bench-before.json` and
`logs/iter-03/bench-after.json`.
For each R-EXT pattern, explain:

  - Which composite index removed the in-memory sort or
    cross-partition scan, citing the specific RU delta, the
    retrieved/output change, AND its migration from "Potential
    Composite Indexes" (before) to "Utilized Composite Indexes"
    (after) in `x-ms-cosmos-index-utilization`.
  - Why R-EXT-3 went from 400 BadRequest → success (3-path composite
    enabling the multi-key ORDER BY).
  - Whether any pattern is still doing more work than it should —
    any High-impact entries still under "Potential" in the `after`
    capture are next-step candidates.

If an `iteration-03-analysis.md` checkpoint exists from the
interactive flow, cross-check observed results against its findings
and flag any diagnosis that turned out wrong.
```

---

## Files exercised by this runbook

| File                                     | Role                                                |
|------------------------------------------|-----------------------------------------------------|
| `scripts/apply_iteration_02.py`          | revert to iter-2 baseline policy (used by bench)    |
| `scripts/apply_iteration_03.py`          | apply iter-3 policy + drift check                   |
| `scripts/bench_iteration_03.py`          | single combined before/after harness                |
| `demo/app/queries.py`                    | R-EXT-1/2/3 implementations + `r1\|r2\|r3\|all` CLI |
| `demo/app/repository.py`                 | RU + raw metrics capture                            |
| `logs/iter-03/bench.log`                 | human-readable comparison                           |
| `logs/iter-03/bench-{before,after}.json` | raw response headers per call                       |

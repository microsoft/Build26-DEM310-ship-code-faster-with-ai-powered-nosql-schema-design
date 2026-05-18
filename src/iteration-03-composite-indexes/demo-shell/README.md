# Iteration 3 — Cosmos DB Shell demo

Cosmos DB Shell scripts for the **composite-indexes** iteration. No
container shape changes versus iteration 2 — only the indexing policy
is upgraded.

## Folder contents

| File | What it does |
|------|--------------|
| `01-apply-composite-indexes.cosmos.js` | Replaces the indexing policy on `CustomerOrders` and `Products` to add three composite indexes. |
| `02-extended-queries.cosmos.js`        | Runs R-EXT-1, R-EXT-2, R-EXT-3 with `populateIndexMetrics: true` and prints `requestCharge` + the engine's `indexMetrics` block per query. |
| `03-scenario-before-after.cosmos.js`   | Self-contained simulation: resets to the iteration-2 baseline policy, runs the three queries, applies the composite policy, re-runs the queries, then prints a RU before/after diff table. |
| `seed-data/README.md`                  | Pointer — uses iteration-2's seed data unchanged. |

There is **no separate seed data** for iteration 3. Run iteration-2's
`01-setup.cosmos.js` (or `complete/seed.py`) first so the containers
exist and are populated.

## Composite indexes added

| Container        | Composite index | Pattern it serves |
|------------------|-----------------|-------------------|
| `CustomerOrders` | `[type ASC, orderDate DESC]`   | R-EXT-1 — customer order history by date range |
| `CustomerOrders` | `[status ASC, orderDate DESC]` | R-EXT-2 — open-orders dashboard (cross-partition) |
| `Products`       | `[rating DESC, price ASC]`     | R-EXT-3 — products by rating then price |

See [extended-access-patterns.md](../complete/extended-access-patterns.md)
for the full rationale.

## How to demo

Pick one of the two flows below.

### Option A — One-paste before/after simulation (recommended on stage)

1. Make sure iteration-2 is set up (database, containers, seed). If not,
   run [iteration-02-optimized/demo-shell/01-setup.cosmos.js](../../iteration-02-optimized/demo-shell/01-setup.cosmos.js).
2. Paste `03-scenario-before-after.cosmos.js` and run it. The script:
   * forces both containers back to the baseline (no composites) policy,
   * runs R-EXT-1/2/3 once and captures RU + `indexMetrics`,
   * applies the composite policy,
   * re-runs the same three queries,
   * prints a side-by-side table with `RU before`, `RU after`, `delta %`,
     and the composite that the engine reports as utilized.

### Option B — Manual three-step walkthrough

1. (Optional baseline) Paste `02-extended-queries.cosmos.js` **before**
   applying the new policy. Each query prints its full `indexMetrics`
   block — point at the empty "Utilized Composite Indexes" section.
2. Paste `01-apply-composite-indexes.cosmos.js`. Wait a few seconds for
   the indexer to rebuild.
3. Paste `02-extended-queries.cosmos.js` again. Call out the lower
   `RU:` values and the composite now listed under "Utilized Composite
   Indexes" — that delta is the iteration-3 takeaway.

## Index metrics

All three scripts pass `populateIndexMetrics: true` on every query.
Cosmos returns an `indexMetrics` string on each response that lists:

* **Utilized Single Indexes** — which `/path/?` includes the engine read.
* **Utilized Composite Indexes** — the exact `[path ORDER, path ORDER]`
  pair the engine matched (empty before iteration 3 lands).
* **Potential Composite Indexes** — composites the engine *would* have
  used if they existed. Useful for future tuning.

`02-extended-queries.cosmos.js` prints the raw block;
`03-scenario-before-after.cosmos.js` collapses it to a one-line
"composite utilized" column in the diff table.

## Cross-reference

* [src/iteration-03-composite-indexes/complete/queries.py](../complete/queries.py) — Python equivalent (and the `--apply-policy` switch).
* [src/iteration-03-composite-indexes/complete/indexing-policy.json](../complete/indexing-policy.json) — canonical multi-container policy file.
* [src/iteration-03-composite-indexes/complete/extended-access-patterns.md](../complete/extended-access-patterns.md) — full rationale for each composite.
* [src/iteration-03-composite-indexes/README.md](../README.md) — full walkthrough.

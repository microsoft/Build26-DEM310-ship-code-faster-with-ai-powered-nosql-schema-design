# Iteration 3 — Cosmos DB Shell demo

Cosmos DB Shell scripts for the **composite-indexes** iteration. No
container shape changes versus iteration 2 — only the indexing policy
is upgraded.

## Folder contents

| File | What it does |
|------|--------------|
| `01-apply-composite-indexes.cosmos.js` | Replaces the indexing policy on `CustomerOrders` and `Products` to add three composite indexes. |
| `02-extended-queries.cosmos.js`        | Runs R-EXT-1, R-EXT-2, R-EXT-3 and prints `requestCharge` per query. |
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

1. Make sure iteration-2 is set up (database, containers, seed). If not,
   run [iteration-02-optimized/demo-shell/01-setup.cosmos.js](../../iteration-02-optimized/demo-shell/01-setup.cosmos.js).
2. (Optional baseline) Run `02-extended-queries.cosmos.js` **before**
   applying the new policy and note the RU values.
3. Paste `01-apply-composite-indexes.cosmos.js` and run it. Wait a few
   seconds for the indexer to rebuild.
4. Run `02-extended-queries.cosmos.js` again and call out the lower
   `RU:` values — that delta is the iteration-3 takeaway.

## Cross-reference

* [src/iteration-03-composite-indexes/complete/queries.py](../complete/queries.py) — Python equivalent (and the `--apply-policy` switch).
* [src/iteration-03-composite-indexes/complete/indexing-policy.json](../complete/indexing-policy.json) — canonical multi-container policy file.
* [src/iteration-03-composite-indexes/complete/extended-access-patterns.md](../complete/extended-access-patterns.md) — full rationale for each composite.
* [src/iteration-03-composite-indexes/README.md](../README.md) — full walkthrough.

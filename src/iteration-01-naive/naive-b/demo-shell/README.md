# Iteration 1 (naive-b) — Cosmos DB Shell demo

Cosmos DB Shell scripts for the **unbounded-array anti-pattern**. One
container, one document per customer, an `orders[]` array that grows
forever.

## Folder contents

| File | What it does |
|------|--------------|
| `01-setup.cosmos.js` | Creates database `Build26DEM310` and container `CustomersWithEmbeddedOrders` (PK `/customerId`). Seeds 10 customer docs with empty `orders[]`. |
| `02-simulate-unbounded-growth.cosmos.js` | Iteratively appends synthetic orders to one customer's `orders[]` array; prints doc size + read/upsert RU per iteration, then projects how many iterations until the 2 MB Cosmos item limit. |
| `seed-data/CustomersWithEmbeddedOrders.json` | The 10 starter customer docs (PK `/customerId`, `orders: []`). |

The script reads its product catalog from
`../../naive-a/demo-shell/seed-data/Products.json`, so run naive-a's
setup or just keep both `demo-shell/seed-data/` folders intact.

## How to demo

1. Open the Cosmos DB Shell against the **classic Windows emulator** (or
   any Cosmos DB account).
2. Paste `01-setup.cosmos.js` and run it. The container is **dropped and
   recreated** every time so the growth simulation is deterministic.
3. Paste `02-simulate-unbounded-growth.cosmos.js`. Watch the `KB` and
   `upsert RU` columns climb together — that's the headline.

> Tweak `ITERATIONS` (default 20) and `ITEMS_PER_ORDER` (default 5) at
> the top of `02-simulate-unbounded-growth.cosmos.js` if you want a
> bigger or smaller growth curve.

## Cross-reference

* [src/iteration-01-naive/naive-b/complete/seed.py](../complete/seed.py) — Python equivalent of `01-setup.cosmos.js`.
* [src/iteration-01-naive/naive-b/complete/simulate.py](../complete/simulate.py) — Python equivalent of `02-simulate-unbounded-growth.cosmos.js`.
* [src/iteration-01-naive/naive-b/README.md](../README.md) — full
  walkthrough.

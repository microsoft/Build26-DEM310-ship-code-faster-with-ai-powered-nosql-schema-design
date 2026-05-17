# Naive iteration 1 — two anti-patterns side by side

This folder shows the **two most common mistakes** a developer makes the
first time they port a relational order-management schema to Cosmos DB.

Both versions seed and query the same domain (customers, orders, items),
so attendees can compare RU and behavior directly.

| Sub-folder | Anti-pattern | What it demonstrates |
|------------|--------------|----------------------|
| [`naive-a/`](./naive-a/) | **1:1 relational port** — one container per table, each partitioned by its own id | Cross-partition reads on every join; place-order is N writes spread across 2 containers and is **not atomic** |
| [`naive-b/`](./naive-b/) | **Single document per customer** — all of a customer's orders live in one ever-growing `orders[]` array | **Unbounded array** anti-pattern: every write rewrites the whole document, RU and doc size grow linearly, and the doc will eventually hit the **2 MB Cosmos item limit** |

Iteration 2 ([`/src/iteration-02-optimized`](../iteration-02-optimized/))
fixes both at once: customers and orders live in the **same container**
(so place-order is one transactional batch) but as **separate documents**
sharing `/customerId` as the partition key (so the customer doc stays
small and orders are bounded).

## Recommended demo order

1. Run `naive-a` first — show the RU on the four access patterns from
   [`docs/02-scenario/2-access-patterns.md`](../../docs/02-scenario/2-access-patterns.md).
2. Run `naive-b/simulate.py` — show RU and doc-size growth across 20
   write iterations and project when the 2 MB ceiling hits.
3. Open the Cosmos DB Agent, paste both result sets, and ask for a
   redesign — you should land on iteration 2.

# 3. Volumetrics

Numbers used to size partitions, request units, and indexing. The demo
seeds a small slice of these volumes — but the agent's recommendations
are driven by the production projections.

| Entity                        | Production target | Demo seed |
|-------------------------------|-------------------|-----------|
| Customers                     | 1 M               | 10        |
| Categories                    | 50                | 5         |
| Products                      | 50 k              | 50        |
| Orders / customer / year      | 10–40             | 20        |
| Items / order                 | 1–10              | 1–10      |
| Avg order doc (iter 2)        | ~3–5 KB           | ~2 KB     |
| Avg customer doc (iter 2)     | ~1 KB             | ~0.5 KB   |
| Read RPS (P1+P2)              | 500 sustained     | n/a       |
| Write RPS (P3)                | 100 sustained     | n/a       |
| Retention                     | 7 years           | 7 years   |

## Partition-key analysis

- **`/customerId`** in `CustomerOrders` — high cardinality (1 M),
  workload skews to active customers (~10 k hot) but a single hot
  partition stays comfortably under the 20 GB / 10 k RU/s logical
  partition limit:
  - 40 orders/yr × 7 yr × 5 KB ≈ 1.4 MB per customer.
  - Even the busiest customer (10× the average) is 14 MB.
- **`/categoryId`** in `Products` — low cardinality (50) but each
  partition holds at most ~1 000 products, which is well under the limit
  and gives us in-partition reads for P4 and R-EXT-3.

## Why we deferred hierarchical partition keys

Hierarchical PK (`/customerId, /year`) would split the largest partitions
further once a customer exceeds ~10 GB. At the projected sizes that's
unlikely for the next 3 years, so we leave it as a documented next step
in [`/docs/04-takeaways.md`](../04-takeaways.md).

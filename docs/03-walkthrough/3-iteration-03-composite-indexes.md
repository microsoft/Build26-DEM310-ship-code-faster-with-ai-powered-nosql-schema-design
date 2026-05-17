# Iteration 3 — Composite indexes (optional)

Source code: [`/src/iteration-03-composite-indexes`](../../src/iteration-03-composite-indexes/)

This iteration is the "we'd ship this next" stretch. After iteration 2 is
live, three new access patterns surface from production telemetry. Each
one is already in-partition, but its `ORDER BY` clause needs a composite
index to stay efficient.

See [`extended-access-patterns.md`](../../src/iteration-03-composite-indexes/complete/extended-access-patterns.md)
for the SQL and rationale.

## Composite indexes added

| Container        | Composite index                            | Pattern it serves |
|------------------|--------------------------------------------|-------------------|
| `CustomerOrders` | `[type ASC, orderDate DESC]`               | R-EXT-1           |
| `CustomerOrders` | `[status ASC, orderDate DESC]`             | R-EXT-2           |
| `Products`       | `[rating DESC, price ASC]`                 | R-EXT-3           |

## Run it

```powershell
cd src/iteration-03-composite-indexes
python complete/queries.py --apply-policy    # one-time
python complete/queries.py
```

`queries.py --apply-policy` reads
[`indexing-policy.json`](../../src/iteration-03-composite-indexes/complete/indexing-policy.json),
splits it per container, and calls
`replace_container(..., indexing_policy=...)` on each.

Re-run the queries before and after `--apply-policy` to see the RU drop.

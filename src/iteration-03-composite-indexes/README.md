# Iteration 3 — Composite indexes for new access patterns (optional)

This iteration is the "we'd ship this next" stretch goal. After iteration 2
goes live, three new read patterns show up in production telemetry. They're
in-partition queries, so they don't fan out, but each one has a multi-field
`ORDER BY` that requires a composite index to stay efficient.

> **Time-permitting in the demo.** Default at-home content. The 23-minute
> session lands on iteration 2; this folder is referenced as the "next
> step" the Cosmos DB Agent suggests when you ask it _"what should we tune
> after we go live?"_.

## Extended access patterns

See [`complete/extended-access-patterns.md`](complete/extended-access-patterns.md).

| Pattern   | Query                                                                                              | Composite index it needs                                                                                          |
|-----------|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| R-EXT-1   | `WHERE type='order' AND customerId=? AND orderDate BETWEEN @from AND @to ORDER BY orderDate DESC` | `CustomerOrders`: `[type ASC, orderDate DESC]`                                                                    |
| R-EXT-2   | `WHERE type='order' AND status=? ORDER BY orderDate DESC` (cross-partition admin query)            | `CustomerOrders`: `[status ASC, orderDate DESC]`                                                                  |
| R-EXT-3   | `WHERE categoryId=? ORDER BY rating DESC, price ASC`                                                | `Products`: `[rating DESC, price ASC]`                                                                            |

## Folders

```text
iteration-03-composite-indexes/
├── complete/
│   ├── extended-access-patterns.md
│   ├── indexing-policy.json
│   └── queries.py             # runs R-EXT-1..3 and prints RU before/after
└── demo/
    └── queries.py             # skeleton with TODOs
```

## Run the complete solution

```powershell
cd src/iteration-03-composite-indexes
# 1. Apply the upgraded indexing policy to the iteration-2 containers:
python complete/queries.py --apply-policy

# 2. Run R-EXT-1, R-EXT-2, R-EXT-3 and watch the RU drop:
python complete/queries.py
```

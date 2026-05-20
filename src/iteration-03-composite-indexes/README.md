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

The runtime lives at the repo root in `demo/app/queries.py` plus the
bench harness at `scripts/bench_iteration_03.py` per
[CONVENTIONS.md](../../docs/03-walkthrough/CONVENTIONS.md). The runbook
with the expected before/after envelope is in
[`docs/03-walkthrough/3-iteration-03-composite-indexes-complete.md`](../../docs/03-walkthrough/3-iteration-03-composite-indexes-complete.md).

```powershell
# from repo root
# One-shot: revert to iter-2 baseline -> bench -> apply iter-3 policy -> bench -> diff table
python -u -m scripts.bench_iteration_03

# Drill-down: run a single R-EXT pattern after the policy is applied
python -u -m demo.app.queries r1 --log logs/iter-03/r1.log
python -u -m demo.app.queries r2 --log logs/iter-03/r2.log
python -u -m demo.app.queries r3 --log logs/iter-03/r3.log
```

The `src/iteration-03-composite-indexes/{complete,demo}/` folders are
reference content only — don't execute scripts from there.

# Iteration 1 — Naive port

Source code: [`/src/iteration-01-naive`](../../src/iteration-01-naive/)

## What we built

Five containers, each partitioned by the document's own id — exactly what
a developer who has just read "use a partition key" without looking at the
access patterns would type first.

| Container           | Partition key  |
|---------------------|----------------|
| `Customers`         | `/customerId`  |
| `Orders`            | `/orderId`     |
| `OrderItems`        | `/orderId`     |
| `Products`          | `/productId`   |
| `ProductCategories` | `/categoryId`  |

## Run it

```powershell
cd src/iteration-01-naive
python complete/seed.py
python complete/patterns.py
```

`patterns.py` prints the RU charge after each step. Capture the totals —
you'll compare them against iteration 2.

## What you should see

| Pattern                                 | Behavior on this layout                                       |
|-----------------------------------------|---------------------------------------------------------------|
| P1: customer + 5 recent orders          | Two cross-partition queries                                   |
| P2: order + items                       | One point read + one in-partition query in `OrderItems`       |
| P3: place an order                      | 1 + N writes spread across two containers — **not atomic**    |
| P4: products in a category sorted by price | Cross-partition query (Products is partitioned by `/productId`) |

## Live-coding tip

Run `demo/seed.py` and `demo/patterns.py` first — they're skeletons with
TODOs. Use the Cosmos DB Agent in chat to walk through the gaps. Reveal
`complete/` only if you run out of time.

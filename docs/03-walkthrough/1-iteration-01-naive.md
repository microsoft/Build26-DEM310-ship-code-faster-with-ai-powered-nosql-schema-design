# Iteration 1 — Naive port (two anti-patterns)

Source code: [`/src/iteration-01-naive`](../../src/iteration-01-naive/)

This iteration shows the **two most common ways** a developer ports an
order-management schema to Cosmos DB on the first try. Both are wrong,
in interestingly different ways — and iteration 2 fixes both at once.

## naive-a — 1:1 relational port

Source: [`/src/iteration-01-naive/naive-a`](../../src/iteration-01-naive/naive-a/)

Five containers, each partitioned by the document's own id — exactly what
a developer who just read "use a partition key" without looking at the
access patterns would type first.

| Container           | Partition key  |
|---------------------|----------------|
| `Customers`         | `/customerId`  |
| `Orders`            | `/orderId`     |
| `OrderItems`        | `/orderId`     |
| `Products`          | `/productId`   |
| `ProductCategories` | `/categoryId`  |

### Run it

```powershell
cd src/iteration-01-naive/naive-a
python complete/seed.py
python complete/patterns.py
```

`patterns.py` prints the RU charge after each step. Capture the totals —
you'll compare them against iteration 2.

### What you should see

| Pattern                                 | Behavior on this layout                                       |
|-----------------------------------------|---------------------------------------------------------------|
| P1: customer + 5 recent orders          | Two cross-partition queries                                   |
| P2: order + items                       | One point read + one in-partition query in `OrderItems`       |
| P3: place an order                      | 1 + N writes spread across two containers — **not atomic**    |
| P4: products in a category sorted by price | Cross-partition query (Products is partitioned by `/productId`) |

## naive-b — single document, unbounded array

Source: [`/src/iteration-01-naive/naive-b`](../../src/iteration-01-naive/naive-b/)

The other intuitive mistake: "a customer has many orders, so put the
orders on the customer." One container, one document per customer, every
order ever placed embedded in a growing `orders[]` array.

### Run it

```powershell
cd src/iteration-01-naive/naive-b
python complete/seed.py
python complete/simulate.py                              # 20 iterations, 5 items/order
python complete/simulate.py --iterations 20 --items-per-order 10
```

### What you should see

`simulate.py` picks one customer and, for 20 iterations, reads the doc,
appends one new order, and upserts the doc. It prints a per-iteration
table:

```text
iter    doc KB   read RU   upsert RU   orders
----    ------   -------   ---------   ------
   1      0.74      1.00       12.30        1
   2      1.42      1.00       14.10        2
   3      2.10      1.00       15.80        3
  ...
  20     13.60      2.10       42.40       20
```

Two trends, both bad:

1. **Upsert RU grows roughly linearly with the array.** Every write
   rewrites the whole document and reindexes the full array.
2. **Read RU grows too** — even reading the customer name pulls back the
   complete order history.

And then the brick wall: the doc will eventually cross Cosmos DB's
**2 MB item limit** and writes will start returning 413. The simulator
prints a projection of how many more iterations until that hits, given
the current per-iteration growth rate.

### Why this is the more dangerous of the two

`naive-a` is *slow* but it scales. `naive-b` works fine in dev with empty
data and then **stops working entirely** in production once a single
customer's history crosses the limit. It's the harder one to migrate out
of later because every consumer is reading "the customer document".

## Live-coding tip

Both `naive-a/demo/` and `naive-b/demo/` are skeletons with TODOs. Open
the Cosmos DB Agent in chat and walk through the gaps; reveal
`complete/` only if you run out of time. The punchline lands hardest if
you run `naive-b/complete/simulate.py` on stage and let the audience
watch the RU column climb.

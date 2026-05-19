# Iteration 1 — Manual-design anti-patterns

Source code: [`/src/iteration-01-naive`](../../src/iteration-01-naive/)

Before the Cosmos DB Agent Kit + GitHub Copilot enter the picture, this
iteration shows the **two most common mistakes** developers make when
hand-rolling a NoSQL schema from a relational mental model. Both are
real patterns observed in customer code; both are wrong, in
interestingly different ways; and iteration 2 — driven by the Agent Kit
— fixes both at once.

Think of this iteration as the *"what humans do unaided"* baseline. We
capture the RU charges here so the after-Agent-Kit numbers in iteration 2
have something concrete to beat.

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
python complete/simulate.py                              # defaults: 50 iterations, 50 items/order
python complete/simulate.py --iterations 20 --items-per-order 10
```

### What you should see

`simulate.py` picks one customer and, for `--iterations` rounds (default
50), reads the doc, appends one new order, and upserts the doc. It
prints a per-iteration table. With the defaults (50 iterations × 50
items/order) the tail of the run looks like:

```text
iter    doc KB    read RU   upsert RU   orders
----    ------    -------   ---------   ------
   1      6.65       1.00       69.05        1
  10     63.15       1.00       69.05       10
  20    126.27       2.10       89.04       20
  30    189.54       9.95      110.24       30
  40    252.61       9.95      131.81       40
  50    315.68       9.95      131.81       50
```

Two trends, both bad:

1. **Upsert RU grows roughly with the array.** Every write rewrites the
   whole document and reindexes the full array.
2. **Read RU grows too** — even reading the customer name pulls back the
   complete order history.

At the end of the run the simulator also prints a projection of how many
more iterations until the document crosses Cosmos DB's **2 MB item
limit** and writes start returning 413 — at the default item size, that
is roughly another ~270 iterations past iter 50.

### Why this is the more dangerous of the two

`naive-a` is *slow* but it scales. `naive-b` works fine in dev with empty
data and then **stops working entirely** in production once a single
customer's history crosses the limit. It's the harder one to migrate out
of later because every consumer is reading "the customer document".

## Hands-on tip

Both `naive-a/demo/` and `naive-b/demo/` are skeletons with TODOs —
filled in **by hand**, deliberately without the Cosmos DB Agent Kit, so
you see what these designs look like when they emerge from
intuition alone. The matching `complete/` folders are there as a
fallback if you run out of time. Running `naive-b/complete/simulate.py`
is the most visceral way to land the point: watch the RU column climb
in real time and project the day this design breaks.

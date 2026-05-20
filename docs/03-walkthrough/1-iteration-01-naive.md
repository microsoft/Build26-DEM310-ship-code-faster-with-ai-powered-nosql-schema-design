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

The runtime lives at the repo root in `scripts/` (see
[`src/iteration-01-naive/naive-a/README.md`](../../src/iteration-01-naive/naive-a/README.md)).
Each script writes its own log via `--log` so the filename always
matches the pattern that produced it — same convention used by
iteration 2, which makes the per-pattern logs directly comparable.

```powershell
# from repo root
python -u -m scripts.seed_iteration_01_naive_a --log logs/iter-01/seed.log

# Run all 4 patterns + P2b; each writes its own logs/iter-01/step5-P<N>.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern all
```

Need a single pattern (e.g. while iterating)? Pass `--pattern P2b --log
logs/iter-01/step5-P2b.log`. Each per-pattern log is kept small on
purpose: one banner, one `[RU]` line per Cosmos call, a 4-field
`metrics:` summary, and one curated `Result:` block — no full payload
dumps and no SDK request/response header noise. Capture the RU
totals; you'll compare them against `logs/iter-02/step5-P<N>.log` from
iteration 2.

### What you should see

| Pattern                                       | Behavior on this layout                                       |
|-----------------------------------------------|---------------------------------------------------------------|
| P1: customer + 5 recent orders                | Two cross-partition queries                                   |
| P2: order + items                             | One point read + one in-partition query in `OrderItems`       |
| P2b: same order, query vs. point read         | Quantifies the query→point-read RU gap on this layout         |
| P3: place an order                            | 1 + N writes spread across two containers — **not atomic**    |
| P4: products in a category sorted by price    | Cross-partition query (`Products` is partitioned by `/productId`) |

## naive-b — single document, unbounded array

Source: [`/src/iteration-01-naive/naive-b`](../../src/iteration-01-naive/naive-b/)

The other intuitive mistake: "a customer has many orders, so put the
orders on the customer." One container, one document per customer, every
order ever placed embedded in a growing `orders[]` array.

### Run it

Naive-b doesn't have a `scripts/` wrapper — it's a smaller, throwaway
demo whose only job is to make the unbounded-array failure mode
visible. The simulator is run directly, but logs still land under
`logs/iter-01/` to match the rest of the walkthrough.

```powershell
# from repo root
New-Item -ItemType Directory -Force logs/iter-01 | Out-Null
cd src/iteration-01-naive/naive-b
python -u complete/seed.py                                            2>&1 | Tee-Object -FilePath ../../../logs/iter-01/naive-b-seed.log
python -u complete/simulate.py                                        2>&1 | Tee-Object -FilePath ../../../logs/iter-01/naive-b-simulate-default.log     # defaults: 50 iterations, 50 items/order
python -u complete/simulate.py --iterations 10 --items-per-order 100  2>&1 | Tee-Object -FilePath ../../../logs/iter-01/naive-b-simulate-large-items.log
cd ../../..
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

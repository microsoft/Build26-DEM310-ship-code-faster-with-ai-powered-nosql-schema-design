# Iteration 1 — Naive port (the "anti-pattern")

This is the **starting point** for the demo. The data model is a 1:1 port of
the classic RDBMS relational schema: every table becomes its own Cosmos DB
container, partitioned by the most obvious column. This deliberately
reproduces the choices a developer makes when modelling a relational schema
in Cosmos DB without first considering access patterns or partitioning.

## Containers

| Container           | Partition key  | One document per |
|---------------------|----------------|------------------|
| `Customers`         | `/customerId`  | Customer         |
| `Orders`            | `/orderId`     | Order header     |
| `OrderItems`        | `/orderId`     | Order line item  |
| `Products`          | `/productId`   | Product          |
| `ProductCategories` | `/categoryId`  | Category         |

> Every container uses its own document's id as the partition key. This is
> the relational-developer reflex — it looks "safe" because every partition
> has exactly one document, but it makes every read pattern below pay extra.

## Folders

```text
src/iteration-01-naive/naive-a/
├── README.md         # this page
└── demo-shell/       # Cosmos DB Shell version of the same demo
    ├── 01-setup.cosmos.js
    ├── 02-access-patterns.cosmos.js
    └── seed-data/    # JSON regenerated from src/sample-data/master/
```

The Python runtime lives at the repo root in `scripts/` — there is no
per-iteration `complete/` or `demo/` folder for naive-a. The wrapper
scripts and their helper modules are co-located:

```text
scripts/
├── seed_iteration_01_naive_a.py        # entrypoint: seed the 5 containers
├── patterns_iteration_01_naive_a.py    # entrypoint: run P1..P4 + P2b
├── _naive_a_shared.py                  # client/config helpers
├── _naive_a_seed.py                    # seed logic
└── _naive_a_patterns.py                # P1..P4 implementations
```

## Run the complete solution

The runtime lives at the repo root in `scripts/` per
[CONVENTIONS.md](../../../docs/03-walkthrough/CONVENTIONS.md). The
block below is copy-paste-friendly — every line is a single, runnable
command, and each command writes its own log file:

```powershell
# from repo root — activate the venv created in docs/01-setup/4-python-env.md
.venv\Scripts\Activate.ps1          # PowerShell
# source .venv/bin/activate         # bash / zsh
pip install -r src/requirements.txt                                            # azure-cosmos

# 1. Seed the 5 naive containers
python -u -m scripts.seed_iteration_01_naive_a       --log logs/iter-01/seed.log

# 2. Run each access pattern individually (one log per pattern)
python -u -m scripts.patterns_iteration_01_naive_a --pattern P1  --log logs/iter-01/step5-P1.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P2  --log logs/iter-01/step5-P2.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P2b --log logs/iter-01/step5-P2b.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P3  --log logs/iter-01/step5-P3.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P4  --log logs/iter-01/step5-P4.log
```

Shortcut: `python -u -m scripts.patterns_iteration_01_naive_a --pattern all`
runs P1…P4 (plus P2b) in one process and writes the same five
`logs/iter-01/step5-P<N>.log` files.

`scripts/patterns_iteration_01_naive_a.py` prints, for each access
pattern, the documents returned and the **RU charge** reported by the
emulator, and writes one log file per pattern. Capture those numbers
— you'll compare them against the matching `logs/iter-02/step5-P<N>.log`
files from iteration 2.

## What to look for during the demo

| Pattern | Why it hurts here |
|---------|-------------------|
| P1: Get customer + recent orders | Two cross-partition queries (one in `Customers`, one in `Orders`) |
| P2: Get order + line items       | One point read + one cross-partition query in `OrderItems` |
| P2b: Compare query vs. point read for one order | Quantifies the query-point-reads gap on this layout |
| P3: Place a new order            | Header write in `Orders` and N writes in `OrderItems` — no atomic transaction |
| P4: List products in a category  | Cross-partition query in `Products` (it's partitioned by `/productId`) |

These are exactly the problems the agent-guided redesign in iteration 2
fixes.

## What you should see

A successful run of `scripts/patterns_iteration_01_naive_a.py` prints
one block per access pattern with the RU charge of every operation and
a `TOTAL` line. :

```text
======================================================================
Iteration 1 — naive 5-container design
======================================================================

P1 — Customer C00005 + 5 most recent orders
  [RU] query Customers by customerId                     <ru>  (1 docs)
  [RU] cross-partition query on Orders                   <ru>  (5 docs)
  [RU] TOTAL                                             <ru>

P2 — Order O0000001 with line items
  [RU] point read Order header                           <ru>  (1 docs)
  [RU] query OrderItems in partition                     <ru>  (N docs)
  [RU] TOTAL                                             <ru>

P3 — Place a new order for C00005
  [RU] cross-partition pick products                     <ru>  (3 docs)
  [RU] create Order header                               <ru>  (1 docs)
  [RU] create 3 OrderItem rows                           <ru>
  [RU] TOTAL (non-transactional!)                        <ru>

P4 — Products in category CAT006 (price ASC)
  [RU] cross-partition query on Products                 <ru>  (N docs)
```

Independent of the exact numbers, three things should stand out as you
read the output:

1. **P1 needs a cross-partition query.** Even though we only want one
   customer's recent orders, the `Orders` container is partitioned by
   `/orderId`, so the engine has to consider every partition just to find
   the five that belong to `C00005`. On a real account that overhead grows
   linearly with the number of physical partitions.
2. **P3 prints `(non-transactional!)`.** The header write and the line
   writes go to two different containers, so there is no way to commit
   them atomically — a crash between them leaves a half-placed order.
3. **P4 is also cross-partition** even though category is the whole
   filter, because `Products` is partitioned by `/productId`. The "obvious"
   relational key is the wrong choice for this query.

## Why this design is not recommended

The five-container, partition-by-id layout *works* — every query above
returns the right data — but it's a textbook anti-pattern for Azure Cosmos
DB. Here is what's actually wrong, mapped to the things you just observed:

### 1. Partition keys were chosen from the schema, not from the access patterns

Every container is keyed by its own primary id (`/customerId`, `/orderId`,
`/productId`, ...). That guarantees one document per logical partition,
which feels safe, but it means **no query can be answered inside a single
partition** unless you already know that id. The id is exactly the thing
the caller is *trying to find*, so the engine has to scan all partitions —
this is why P1 and P4 light up as cross-partition.

The right question is "what does the application *ask for*?", not "what is
the primary key in the relational source?". Iteration 2 partitions by
`/customerId` precisely because P1, P2, and P3 are all "give me things that
belong to this customer".

### 2. Related data is split across containers

Orders and their line items always travel together — there is no UI screen
or API response that returns one without the other. Splitting them into
`Orders` and `OrderItems` containers means:

- P2 needs two round trips (point read + query) where one read would do.
- P3 has to coordinate writes across containers it cannot transact over.

Cosmos DB's transactional batch API works on a single partition key inside
a single container. So as long as related items live in different
containers (or in the same container but under different partition keys),
**atomic multi-document writes are impossible**. That is why P3 prints
`TOTAL (non-transactional!)`: a failure after the header write leaves an
orphan order with no line items, and the application has to clean up
manually.

### 3. RU charges are higher than they need to be

Cross-partition queries pay a fixed overhead per physical partition plus
the cost of retrieving the matching documents. With only 10 customers
seeded the absolute numbers look small, but the *ratio* is what matters —
P1's cross-partition step costs ~2.5× the single-partition lookup, and
that gap widens linearly as the data grows. Iteration 2 brings P1 down to
a single point read by collocating recent orders with the customer.

### 4. No path to scale

Even if you accept the RU overhead today, this layout has nowhere to go:

- You can't switch a container's partition key after it's created — fixing
  P1 means migrating data into a new container.
- Adding new patterns (e.g. "all orders in the last 15 minutes") makes the
  problem worse: every new question is another cross-partition query.
- Reserved throughput is provisioned **per container**. Five containers
  means five RU budgets to size, monitor, and pay for — most of which are
  spent serving queries that should never have been cross-partition.

### Summary

The naive design is correct, readable, and familiar to anyone coming from
a relational background — and that's exactly why it's dangerous. It scales
the relational *cost model* onto a database that charges per partition
crossed and per byte read, with no transactional safety net across the
containers it encouraged you to create. Iteration 2 rebuilds the same four
access patterns on a single container partitioned by `/customerId`,
collapses P1 and P2 to single-partition reads, and makes P3 a true
transactional batch.

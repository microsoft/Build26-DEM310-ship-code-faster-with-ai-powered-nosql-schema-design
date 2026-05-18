# Iteration 1 — Naive port (the "anti-pattern")

This is the **starting point** for the demo. The data model is a 1:1 port of
the AdventureWorksLT relational schema: every table becomes its own Cosmos DB
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
iteration-01-naive/
├── complete/      # ready-to-run reference solution
│   ├── shared.py
│   ├── seed.py
│   └── patterns.py
└── demo/          # the same files with the interesting bits removed
    ├── shared.py  # (identical helper)
    ├── seed.py    # TODOs for partition key + bulk insert
    └── patterns.py# TODOs for each access-pattern query
```

## Run the complete solution

From the repo root:

```powershell
pip install -r src/requirements.txt        # azure-cosmos
cd src/iteration-01-naive
python complete/seed.py                    # creates containers + bulk inserts
python complete/patterns.py                # runs P1..P4 and prints RU charges
```

`patterns.py` prints, for each access pattern, the documents returned and
the **RU charge** reported by the emulator. Capture those numbers — you'll
compare them against iteration 2.

## What to look for during the demo

| Pattern | Why it hurts here |
|---------|-------------------|
| P1: Get customer + recent orders | Two cross-partition queries (one in `Customers`, one in `Orders`) |
| P2: Get order + line items       | One point read + one cross-partition query in `OrderItems` |
| P3: Place a new order            | Header write in `Orders` and N writes in `OrderItems` — no atomic transaction |
| P4: List products in a category  | Cross-partition query in `Products` (it's partitioned by `/productId`) |

These are exactly the problems the agent-guided redesign in iteration 2
fixes.

## What you should see

A successful run of `complete/patterns.py` prints one block per access
pattern with the RU charge of every operation and a `TOTAL` line. The
shape of the output looks like this (RU values are placeholders until the
run is captured against the classic Windows emulator — see the note
below):

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

> 📝 **About the RU numbers.** The captured RU values will be filled in
> from a run against the **classic Azure Cosmos DB emulator on Windows**,
> which reports differentiated, production-like RU charges. The vNext
> Linux preview emulator (Docker image
> `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview`)
> is convenient on macOS/Linux but currently reports a flat synthetic
> charge (~1.00 RU per request), so it is **not** the right target for
> reasoning about cost. Use it for connectivity and shape, the classic
> emulator (or a real Azure Cosmos DB account) for RU comparisons.

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

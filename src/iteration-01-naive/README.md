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

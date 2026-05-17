# Iteration 2 — Agent-guided redesign

Source code: [`/src/iteration-02-optimized`](../../src/iteration-02-optimized/)

## What the agent recommends

Open the Cosmos DB Agent with iteration 1's RU output, plus the
[access patterns](../02-scenario/2-access-patterns.md) and
[volumetrics](../02-scenario/3-volumetrics.md) pasted in. Ask:

> @cosmos given these four access patterns and projected volumes, propose
> a container layout that keeps most reads in a single partition and
> place-order atomic.

The agent should converge on:

1. **Collapse `Customers`, `Orders`, `OrderItems` → `CustomerOrders`**
   partitioned by `/customerId`, with a `type` discriminator (`customer`
   vs `order`).
2. **Embed `items[]` inside the order document** so P2 becomes a single
   point read.
3. **Embed `orderSummary` inside the customer document** so the
   customer-profile widget doesn't need an aggregation query.
4. **Repartition `Products` by `/categoryId`** so P4 stays in-partition.
5. **Use a transactional batch** for place-order — possible because the
   customer doc and the new order doc share the partition key.

## Run it

```powershell
cd src/iteration-02-optimized
python complete/seed.py
python -m complete.app.main get-customer C00005
python -m complete.app.main get-order   C00005 O0000003
python -m complete.app.main place-order C00005
python -m complete.app.main list-products CAT006
```

## Code layout — FastAPI-ready

```text
complete/app/
├── models.py       # Pydantic shapes
├── repository.py   # Cosmos calls + RU capture
├── service.py      # business logic (transactional batch lives here)
└── main.py         # argv -> service -> stdout
```

To expose the same logic over HTTP, add an `app/api.py` like:

```python
from fastapi import FastAPI
from .service import CustomerOrderService

api = FastAPI()
svc = CustomerOrderService()

@api.get("/customers/{cid}")
def get_customer(cid: str):
    return svc.get_customer_with_orders(cid)
```

No edits to `service.py` or `repository.py` are required.

## The punchline

For every pattern, compare RU between iterations:

| Pattern | Iter 1 (typical)                         | Iter 2 (typical)                                    |
|---------|------------------------------------------|-----------------------------------------------------|
| P1      | 2 cross-partition queries ≈ 8–15 RU       | 1 single-partition query ≈ 2–4 RU                   |
| P2      | 1 point read + 1 in-partition query       | 1 point read only                                   |
| P3      | 1 + N non-transactional writes            | 1 transactional batch (customer + order)            |
| P4      | Cross-partition query ≈ 6–10 RU           | Single-partition query ≈ 2–3 RU                     |

(Exact numbers depend on emulator build and seed size — what matters is
the order-of-magnitude shape.)

# Iteration 2 — Agent-guided redesign (`CustomerOrders` + `Products`)

This is the iteration that the Cosmos DB Agent in VS Code guides you toward
once it sees iteration 1's RU charges and the access patterns in
[`/docs/02-scenario/2-access-patterns.md`](../../docs/02-scenario/2-access-patterns.md).
The five containers collapse to two, and a `type` discriminator lets a
single container hold both customer profiles and orders for the same
customer in the **same logical partition**.

## Containers

| Container        | Partition key   | Documents in it                                                       |
|------------------|-----------------|-----------------------------------------------------------------------|
| `CustomerOrders` | `/customerId`   | `type:"customer"` (one per customer) and `type:"order"` (N per customer) |
| `Products`       | `/categoryId`   | `type:"product"` (one per product, partitioned by category)          |

### Document shapes

```jsonc
// type: "customer"  — one per customer
{
  "id": "C00005",
  "type": "customer",
  "customerId": "C00005",
  "firstName": "...", "lastName": "...", "email": "...",
  "orderSummary": {
    "lifetimeOrders": 20,
    "lifetimeRevenue": 481_321.40,
    "lastOrderDate": "2026-04-12T..."
  }
}
```

```jsonc
// type: "order"  — one per order, items embedded
{
  "id": "O0000003",
  "type": "order",
  "customerId": "C00005",       // partition key
  "orderId":   "O0000003",
  "orderDate": "2024-05-30T...",
  "status":    "Placed",
  "totalAmount": 30861.24,
  "items": [
    { "productId": "P00751", "productName": "Road-150 Red, 48",
      "quantity": 5, "unitPrice": 3578.27, "lineTotal": 17891.35 },
    /* ... */
  ]
}
```

```jsonc
// type: "product"  — one per product
{
  "id": "P00751",
  "type": "product",
  "productId":   "P00751",
  "categoryId":  "CAT006",      // partition key
  "name": "Road-150 Red, 48",
  "price": 3578.27,
  "rating": 4.97
}
```

## Why this is better

| Pattern | What changes vs iteration 1 |
|---------|------------------------------|
| P1: Get customer + recent orders | **One query, one partition** — `SELECT * FROM c WHERE c.customerId = @cid` returns the customer doc *and* their orders. |
| P2: Get order + line items       | **One point read** — items are embedded in the order document. |
| P2b: Point read vs in-partition query for the same doc | **~3× cheaper** — `read_item(id, pk)` lands at ~1.00 RU; the equivalent `SELECT * FROM c WHERE c.customerId=@cid AND c.id=@oid` pays ~2.9 RU for query parsing/planning even though both return the exact same single document. Lesson: **if you know id + partition key, never use a query.** Run `python -m demo.app.main compare-reads C00005 O0000001` to see it. |
| P3: Place a new order            | **One transactional batch** — update the customer's `orderSummary` and create the order atomically (same partition key). |
| P4: List products in a category  | **In-partition query** — `Products` is partitioned by `/categoryId`. |

## Folders

```text
iteration-02-optimized/
├── complete/
│   ├── app/                    # FastAPI-ready layout
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models for the new shapes
│   │   ├── repository.py       # Cosmos calls (read/write/query) + RU capture
│   │   ├── service.py          # business logic + transactional batch
│   │   └── main.py             # CLI entry point: argv -> service -> stdout
│   ├── seed.py                 # reshape master JSON -> 2 containers
│   ├── migrate_from_01.py      # one-shot migration from iteration 1
│   └── indexing-policy.json    # basic indexing policy (no composites yet)
└── demo/
    ├── app/
    │   ├── __init__.py
    │   ├── models.py           # skeleton
    │   ├── repository.py       # skeleton
    │   ├── service.py          # skeleton
    │   └── main.py             # skeleton
    └── seed.py                 # skeleton
```

## Run the complete solution

The runtime lives at the repo root in `demo/app/` per
[CONVENTIONS.md](../../docs/03-walkthrough/CONVENTIONS.md). The runbook
with the expected RU envelope is in
[`docs/03-walkthrough/2-iteration-02-optimized-complete.md`](../../docs/03-walkthrough/2-iteration-02-optimized-complete.md).

```powershell
# from repo root
python -u -m scripts.apply_iteration_02                                   # create containers + iter-2 policy
python -u -m demo.app.main seed             --log logs/iter-02/seed.log   # load src/sample-data/master/*.json
python -u -m demo.app.main get-customer   C00005           --log logs/iter-02/step5-P1.log
python -u -m demo.app.main get-order      C00005 O0000001  --log logs/iter-02/step5-P2.log
python -u -m demo.app.main compare-reads  C00005 O0000001  --log logs/iter-02/step5-P2b.log
python -u -m demo.app.main place-order    C00005           --log logs/iter-02/step5-P3.log
python -u -m demo.app.main list-products  CAT006           --log logs/iter-02/step5-P4.log
```

The `src/iteration-02-optimized/{complete,demo}/` folders are reference
content only — don't execute scripts from there.

## FastAPI later

`app/service.py` is HTTP-framework-agnostic. To expose the same logic over
HTTP, add an `app/api.py` like:

```python
from fastapi import FastAPI
from .service import CustomerOrderService
api = FastAPI()
svc = CustomerOrderService()

@api.get("/customers/{cid}")
def get_customer(cid: str):
    return svc.get_customer_with_orders(cid)
```

No changes to `service.py` or `repository.py` are required.

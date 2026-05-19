# Iteration 2 — Agent-guided redesign

Source code: [`/src/iteration-02-optimized`](../../src/iteration-02-optimized/)

> **Cosmos DB Agent Kit — why it matters here.** Iteration 2 is the
> turning point where modeling decisions stop being intuition and become
> rule-driven. The [Agent Kit](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)
> activates four skill categories on this content: **Data Modeling**
> (embed vs reference), **Partition Key Design** (cardinality + access
> pattern fit), **Query Optimization** (RU reduction), and **SDK Best
> Practices** (singleton client, transactional batch, retry). If you're
> not on VS Code, install it with
> `npx skills add AzureCosmosDB/cosmosdb-agent-kit` (see
> [setup step 3](../01-setup/3-vscode-agent.md)) and the same prompts
> below work with Claude Code, Gemini CLI, or Copilot in JetBrains.
>
> **Observability built in.** The kit's Monitoring & Diagnostics rules
> are why every example script logs `requestCharge`, `x-ms-item-count`,
> and `x-ms-documentdb-query-metrics` — the same triplet you'll see
> printed by `repository.py`. That's how you spot a database request or query regression directly in the code.

Start with original business context, the access patterns and observe demo flow using the prompt sequence below and let the Agent Kit derive the new schema and generate or update code as you go. The [Expected outcomes](#expected-outcomes--reference-key) section at the
bottom of this page is the reference key; skip it on the first run if
you want to see what the kit proposes without anchoring on the answer.

## Demo flow — recommended Copilot prompts

This is the prompt sequence to walk through. Each prompt builds on the
previous one: problem statement → design → validate the deployed shapes
→ seed → scaffold code → execute and compare.

### Step 1 — From problem statement to target design

Paste iteration 1's RU output and the scenario links into the agent:

```text
@cosmos Here is what we have today:

- The team is porting from SQL Server to Azure Cosmos DB. It works, but team suspect the design won't hold up under production load and not sure it is optimal.
- Five containers ported 1:1 from a SQL schema (see iteration-01-naive).
- Access patterns P1–P4 in docs/02-scenario/2-access-patterns.md.
- Volumetrics in docs/02-scenario/3-volumetrics.md.
- Captured RU per pattern from naive-a/patterns.py.

Propose optimal Cosmos DB NoSQL container and indexing data model design based on Cosmos DB best practices and account for production volumes and TPS (include tables-container mappings and rationale).
Explain each container partition-key choice and show the target JSON
shape for each container Entity document type (highlight if there is colocation of Entities and explain why).
```

### Step 2 — Validate the deployed container structures
Create proposed containers and ask the agent to verify they match the
proposed design:

```text
@cosmos Create containers based on proposed design.
Inspect the local emulator account and confirm:
  - A container named `CustomerOrders` exists, partitioned by /customerId.
  - A container named `Products` exists, partitioned by /categoryId.
  - Validate indexing policy (we'll tune in iteration 3 for additional requirements).
Report any drift between what I proposed and what is actually deployed.
```

### Step 3 — Seed and validate data shapes

```text
@cosmos Generate a seed script that loads 10 customers, 5 categories,
50 products, and ~20 orders per customer from the AdventureWorksLT CSVs
in _remove-before-publish/AdventureWorksLT/ into the two new containers.
Use the `type` discriminator on CustomerOrders. After seeding, query the
emulator and show me one customer document and one order document so I
can verify the embedded shapes are right.
```

Use `complete/seed.py` as the reference output — the agent should
produce something equivalent.

### Step 4 — Scaffold the application code

```text
@cosmos Generate a small Python package with this layout:

  complete/app/
  ├── models.py       # Pydantic shapes for customer + order + item
  ├── repository.py   # Cosmos calls that capture and log requestCharge
  ├── service.py      # business logic; P3 must use a transactional batch
  └── main.py         # argv -> service -> stdout

Follow the Agent Kit's SDK Best Practices rules: singleton CosmosClient,
async where appropriate, retry on 429, and log requestCharge +
x-ms-item-count + a compact query-metrics summary on every call.
```

### Step 5 — Execute and capture RU

```powershell
cd src/iteration-02-optimized
python complete/seed.py
python -m complete.app.main get-customer C00005   # P1
python -m complete.app.main get-order   C00005 O0000003   # P2
python -m complete.app.main compare-reads C00005 O0000003 # P2b: point read vs query
python -m complete.app.main place-order C00005             # P3
python -m complete.app.main list-products CAT006           # P4
```

> **P2b — why the point read wins.** `compare-reads` fetches the same
> single document two ways: the SDK's `read_item(id, partition_key)`
> (~1.0 RU) and an equivalent in-partition SQL query
> `WHERE c.customerId=@cid AND c.id=@oid` (~2.9 RU). Both return one
> document from one partition; the query still pays ~3× the RU because
> it goes through the query engine (parsing, planning, item-count and
> metrics headers) instead of dispatching a direct GET against the
> replica's primary index. The takeaway baked into iteration 2's
> schema choice: when you know id + partition key, reach for the
> point-read API.

### Step 6 — Ask the agent to interpret the results

```text
@cosmos Here are the RU charges per pattern from iteration 1 and
iteration 2 (paste both). For each pattern, explain which design choice
(partition key, embedding, transactional batch, repartitioning) drove
the delta, and flag any pattern where the gain is smaller than expected.
```

## Code layout — FastAPI-ready (reference)

The package scaffolded in Step 4 lands at this shape:

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

## Expected outcomes — reference key

> **Reference section.** This is what the Cosmos DB Agent Kit *should*
> propose for this iteration. Use it to validate the recommendations
> and RU numbers you observe when you run the demo flow above. Skip it
> on a first pass if you'd rather see the kit derive the answer without
> anchoring on it.

### Recommended container design (expected)

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

### Expected RU comparison

For every pattern, compare observed RU between iterations:

| Pattern | Iter 1 (typical)                         | Iter 2 (expected)                                   |
|---------|------------------------------------------|-----------------------------------------------------|
| P1      | 2 cross-partition queries ≈ 8–15 RU       | 1 single-partition query ≈ 2–4 RU                   |
| P2      | 1 point read + 1 in-partition query       | 1 point read only                                   |
| P3      | 1 + N non-transactional writes            | 1 transactional batch (customer + order)            |
| P4      | Cross-partition query ≈ 6–10 RU           | Single-partition query ≈ 2–3 RU                     |

Exact numbers depend on emulator build and seed size — what matters is
the order-of-magnitude shape. If the numbers you observe don't match,
use Step 6's interpretation prompt to find out why.

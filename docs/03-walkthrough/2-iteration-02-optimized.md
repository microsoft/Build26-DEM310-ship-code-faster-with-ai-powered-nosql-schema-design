# Iteration 2 — Agent-guided redesign

Runtime code lives in [`demo/app/`](../../demo/app/) and one-shot scripts
in [`scripts/`](../../scripts/) per the layout in
[CONVENTIONS.md](./CONVENTIONS.md). The folder
[`src/iteration-02-optimized/`](../../src/iteration-02-optimized/) is
reference content only — point attendees there for snippets, not for
execution.

> Already have the iteration-2 solution checked in? Skip the prompts
> below and use the runbook in
> [`2-iteration-02-optimized-complete.md`](./2-iteration-02-optimized-complete.md)
> to execute the finished code directly.

> **Cosmos DB Agent Kit — why it matters here.** Iteration 2 is the
> turning point where modeling decisions stop being intuition and become
> rule-driven. The [Azure Cosmos DB Agent Kit](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)
> activates several skill categories on this content: **Data Modeling**
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

Initial starter Prompt for Copilot:

```text
@cosmos Here is current state of the project and goals:

The team is porting application from Relational Database to Azure Cosmos DB. It works, but team suspect the design won't hold up under production load and not sure it is optimal.
- Five containers ported 1:1 from a RDBMS schema (see iteration-01-naive).
- Access patterns P1–P4 in docs/02-scenario/2-access-patterns.md.
- Volumetrics in docs/02-scenario/3-volumetrics.md.
- Captured RU per pattern from naive-a/patterns.py for comparison.

Propose optimal Cosmos DB NoSQL containers and indexing data model design based on Cosmos DB best practices and account for production volumes and TPS (include tables-container mappings and rationale).
Explain each container partition-key choice and show the target JSON
shape for each container Entity document type (highlight if there is colocation of Entities and explain why).

Write the full recommendation to `iteration-02-output.md` at the repo
root — include the container/partition-key mapping, target JSON shapes,
indexing notes, and the rationale for each choice. This file is a
checkpoint: I will review it before moving on to Step 2.
```

> **Checkpoint.** Before continuing, open `iteration-02-output.md` and
> confirm the proposed design matches your intent. Edit the file (or
> re-prompt the agent) until you're satisfied — every later step is
> built on top of this design.

### Step 2 — Create and validate the deployed container structures

Drive creation and validation from the checkpoint file so the deployed
shape is whatever you approved in Step 1 — no hardcoded names or keys
in this prompt:

```text
@cosmos Read `iteration-02-output.md` and use it as the source of truth.
For every container described there, create it in the local emulator
with the partition key and indexing policy specified in the file.
Then inspect the emulator account and confirm each container exists
exactly as described — name, partition key path, and indexing policy.
Report any drift between `iteration-02-output.md` and what is actually
deployed.
```

### Step 3 — Seed and validate data shapes

```text
@cosmos Generate and run a seed script at `scripts/seed_iteration_02.py` that converts the canonical sample data (--customers 10 --orders-per-customer 20  --categories 5 --products-per-category 10 --max-lines-per-order 10) from `src/sample-data/source/*.csv` into JSON docs based on final Document JSON models per Container/Entity combinations defined in `iteration-02-output.md`, persist generated JSON files in `src/sample-data/tmp` and load generated JSON docs to the new created containers based on mapping. Persist generated 
Write the seed run log to `logs/iter-02/seed.log`. After seeding, query
the emulator and show me one customer document and one order document
so I can verify the embedded shapes are right.
```


### Step 4 — Scaffold the application code

```text
@cosmos Generate a small Python package at `demo/app/` with this layout:

  demo/app/
  ├── models.py       # Pydantic shapes 
  ├── repository.py   # Cosmos calls that capture and log requestCharge
  ├── service.py      # business logic; P3 must use a transactional batch
  └── main.py         # argv -> service -> stdout

Follow the Agent Kit's SDK Best Practices rules: singleton CosmosClient,
async where appropriate, retry on 429, and log requestCharge +
x-ms-item-count + a compact query-metrics summary on every call as curated output.

Patterns to be covered: P1, P2, P2b (compare-reads), P3, P4, use  IDs (C00005, O0000003, CAT006) to match log comparisons with other iterations. Iteration should have a benchmark script `scripts/patterns_iteration_NN_<variant>.py` with --pattern {P1|P2|P2b|P3|P4|all} and --log <path>; logs go to logs/iter-NN/step5-P<N>.log . Output is curated only: banner + [RU] lines + 4-field metrics: line + a final Result: key/value block. Silence azure/azure.cosmos/urllib3/aiohttp loggers to WARNING. Demo modules expose _query(...) (returns (rows, ru, n, metrics)) and pX(...) (returns a dict). 

```

### Step 5 — Execute and capture RU

The runtime CLI lives at `demo/app/main.py` and writes each call's
RU + query-metrics line via the `demo.repo` logger. Pass `--log` so
the script owns its filename (no `Tee-Object` mismatch between
command and file name).

```powershell
# Execute all scripts from repo root
python -u -m demo.app.main get-customer   C00005               --log logs/iter-02/step5-P1.log    # P1
python -u -m demo.app.main get-order      C00005 O0000003      --log logs/iter-02/step5-P2.log    # P2
python -u -m demo.app.main compare-reads  C00005 O0000003      --log logs/iter-02/step5-P2b.log   # P2b
python -u -m demo.app.main place-order    C00005               --log logs/iter-02/step5-P3.log    # P3
python -u -m demo.app.main list-products  CAT006               --log logs/iter-02/step5-P4.log    # P4
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
@cosmos Read the per-pattern logs under `logs/iter-02/`
(step5-P1.log, step5-P2.log, step5-P2b.log, step5-P3.log,
step5-P4.log) and, if available, the equivalent iteration-1 logs
under `logs/iter-01/`. These contain the per-pattern request charges
and query-metrics summaries. For each pattern, compare iteration 1
vs iteration 2 and explain which design choice (partition key,
embedding, transactional batch, repartitioning) drove the delta.
Flag any pattern where the gain is smaller than expected. Produce a
markdown table with columns: `Pattern | Iter 1 RU/s | Iter 2 RU/s | Δ Delta % |
Driver | Verdict`.
List which Azure Cosmos DB Agent Kit best practices and skills were used in this session.
```

## Code layout — FastAPI-ready (reference)

The package scaffolded in Step 4 lands at this shape (see
[CONVENTIONS.md](./CONVENTIONS.md) for the full repo layout):

```text
demo/app/
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
| P3      | 1 + N non-transactional writes            | 1 point read (customer doc) + 1 transactional batch (upsert customer + create order) |
| P4      | Cross-partition query ≈ 6–10 RU           | Single-partition query ≈ 2–3 RU                     |

Exact numbers depend on emulator build and seed size — what matters is
the order-of-magnitude shape. If the numbers you observe don't match,
use Step 6's interpretation prompt to find out why.

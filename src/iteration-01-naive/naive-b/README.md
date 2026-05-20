# naive-b — unbounded-array anti-pattern

**Anti-pattern under test:** keep one document per customer in a single
container; embed *every* order the customer ever places inside a growing
`orders[]` array on that document. Each new order is a read-modify-write
upsert of the whole document.

This is intuitive ("a customer has many orders → put them on the
customer") and **wrong**. It runs into three concrete problems:

1. **Write RU grows with the doc** — every upsert rewrites the entire
   document and reindexes the full array. On the classic Windows emulator
   the cost grows in **step-function jumps tied to the underlying ~128 KB
   billing block**, with a slower per-iteration linear climb visible
   between steps once the doc passes ~250 KB.
2. **Read RU grows with the doc** — even fetching the customer's name
   pulls back every order ever placed. Read RU climbs from 1 RU at
   ~1 KB to ~10 RU at ~315 KB and ~40 RU past 700 KB.
3. **The 2 MB item limit is a hard ceiling.** Cosmos DB will reject an
   upsert that pushes the document over 2 MB with a 413 error. There is
   no graceful degradation — the customer can't place an order anymore.

## What `simulate.py` does

Picks one customer (`C00005` by default), then for **N iterations**
(default 50):

1. Reads the current customer doc and prints its size **and read RU**.
2. Appends one new order (with K line items copied from the master
   catalog, default 50) to the `orders[]` array.
3. Upserts the document and captures the upsert's RU charge.

At the end it prints a table — iteration, document size in KB, **read
RU**, upsert RU, order count — plus a projection of how many more
iterations the doc has before it crosses the 2 MB ceiling.

> **Why the new 50 × 50 defaults?** The original 20 × 5 profile kept the
> document under ~30 KB, which is below the emulator's first RU billing
> boundary. In that range upsert RU is dominated by fixed overhead and
> can even *fall* across iterations — the exact opposite of the demo
> punchline. 50 iterations × 50 items/order pushes the document to
> ~315 KB and crosses three billing boundaries, so the step-function
> growth is visible from the first run.

## Folders

```text
src/iteration-01-naive/naive-b/
├── README.md         # this page
└── demo-shell/       # Cosmos DB Shell version of the same demo
    ├── 01-setup.cosmos.js
    ├── 02-simulate-unbounded-growth.cosmos.js
    └── seed-data/    # JSON regenerated from src/sample-data/master/
```

The Python runtime lives at the repo root in `scripts/` — there is no
per-iteration `complete/` or `demo/` folder for naive-b. The wrapper
scripts and their helper modules are co-located:

```text
scripts/
├── seed_iteration_01_naive_b.py        # entrypoint: seed the embedded-array container
├── simulate_iteration_01_naive_b.py    # entrypoint: grow the orders[] array
├── _naive_b_shared.py                  # client/config helpers
├── _naive_b_seed.py                    # seed logic
└── _naive_b_simulate.py                # growth-simulation logic
```

## Run it

The runtime lives at the repo root in `scripts/` per
[CONVENTIONS.md](../../../docs/03-walkthrough/CONVENTIONS.md). Every
step is a `python -m scripts.<name>` invocation and each script writes
its own log via `--log` — same convention used by naive-a and
iteration 2.

```powershell
# from repo root
# 1. Seed the container with 10 customers and empty orders[]
python -u -m scripts.seed_iteration_01_naive_b     --log logs/iter-01/naive-b-seed.log

# 2. Run the 50-iteration growth simulation (default: 50 items/order)
python -u -m scripts.simulate_iteration_01_naive_b --log logs/iter-01/naive-b-simulate-default.log
```

To make the growth even more dramatic (and slower — expect ~3 minutes),
bump the per-order item count or iteration count:

```powershell
python -u -m scripts.simulate_iteration_01_naive_b --iterations 100 --items-per-order 100 --log logs/iter-01/naive-b-simulate-large-items.log
```

Expected shape of the output with default parameters (RU values from
the classic Windows emulator):

```
iter    doc KB   read RU   upsert RU   orders
   1      6.65      1.00       69.05        1   <- one-time index init
   2     12.96      1.14       15.67        2   <- steady state begins
  10     63.41      2.19       26.67       10
  20    126.48      4.76       53.05       20   <- 1st billing-block step
  30    189.54      9.95      110.24       30   <- 2nd step
  40    252.61      9.95      110.24       40
  50    315.68      9.95      131.81       50   <- 3rd step
```

## What attendees should walk away with

- "Put many-of inside the one-of" feels right and is the single most
  expensive mistake to fix later.
- Both **write** and **read** RU grow with the size of the embedded
  array — not just storage cost.
- The 2 MB item limit will end the conversation eventually. The right
  question isn't "how do I shrink the array?", it's "should this array
  exist on this document at all?"

The answer in iteration 2: split the array into separate documents that
share the partition key.

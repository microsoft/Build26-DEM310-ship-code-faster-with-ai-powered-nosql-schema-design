# Source code

All the runnable assets for **DEM310 — Ship code faster with AI-powered
NoSQL schema design**. Walk through the three iterations in order; each one
has a `complete/` folder you can run and a `demo/` folder with the
interesting bits removed for live-coding.

## Layout

```text
src/
├── requirements.txt
├── sample-data/                    # AdventureWorksLT -> trimmed master JSON
│   ├── source/                     # raw CSVs (regeneration input)
│   ├── generate.py                 # deterministic generator
│   └── master/                     # generated JSON consumed by every iteration
├── iteration-01-naive/             # 5 containers, 1:1 port of the SQL schema
│   ├── complete/                   #   shared.py, seed.py, patterns.py
│   └── demo/                       #   same files with TODOs
├── iteration-02-optimized/         # CustomerOrders + Products (agent-guided)
│   ├── complete/
│   │   ├── app/                    #   FastAPI-ready: models / repository / service / main
│   │   ├── seed.py
│   │   ├── migrate_from_01.py
│   │   └── indexing-policy.json
│   └── demo/                       #   same shape, skeleton
└── iteration-03-composite-indexes/ # optional stretch: 3 new access patterns
    ├── complete/                   #   extended-access-patterns.md, queries.py, policy
    └── demo/
```

## Prerequisites

1. Python 3.10+
2. The local Cosmos DB emulator running on `https://localhost:8081`
   (see [`/docs/01-setup`](../docs/01-setup/)).
3. `pip install -r src/requirements.txt`

## Quick start

```powershell
pip install -r src/requirements.txt

# 1) iteration 1 — feel the pain
cd src/iteration-01-naive
python complete/seed.py
python complete/patterns.py

# 2) iteration 2 — the agent-guided redesign
cd ../iteration-02-optimized
python complete/seed.py
python -m complete.app.main get-customer C00005
python -m complete.app.main place-order C00005

# 3) iteration 3 (optional) — composite indexes
cd ../iteration-03-composite-indexes
python complete/queries.py --apply-policy
python complete/queries.py
```

Compare the `[RU]` lines from iteration 1 vs iteration 2 — that's the
demo's punchline.

## FastAPI later

`iteration-02-optimized/complete/app/` is laid out so adding an `api.py`
that calls `service.CustomerOrderService` is the only change required to
expose the same logic over HTTP. There is no FastAPI dependency today
because the demo runs from the command line.

## Sample data

`sample-data/master/` is committed so attendees can seed Cosmos DB without
running the generator. Re-generate only if you want a different size:

```powershell
cd src/sample-data
python generate.py --customers 25 --orders-per-customer 50
```

See [`sample-data/README.md`](./sample-data/README.md) for details.

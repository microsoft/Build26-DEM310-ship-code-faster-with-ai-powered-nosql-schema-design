# Source code

All the runnable assets for **DEM310 — Ship code faster with AI-powered
NoSQL schema design**. Walk through the three iterations in order; each one
has a `complete/` folder you can run and a `demo/` folder with the
interesting bits removed so you can fill them in yourself.

## Layout

```text
src/
├── requirements.txt
├── .env.example                    # copy to .env; loaded by every script
├── sample-data/                    # Sample CSVs (classic RDBMS schema) -> trimmed master JSON
│   ├── source/                     # raw CSVs (regeneration input)
│   ├── generate.py                 # deterministic generator
│   └── master/                     # generated JSON consumed by every iteration
├── iteration-01-naive/             # 5 containers, 1:1 port of the SQL schema
│   ├── naive-a/                    #   relational-style access patterns
│   │   ├── complete/               #     shared.py, seed.py, patterns.py
│   │   ├── demo/                   #     same files with TODOs
│   │   └── demo-shell/             #     Cosmos DB Shell .cosmos.js + per-container JSON
│   └── naive-b/                    #   unbounded-array anti-pattern
│       ├── complete/               #     shared.py, seed.py, simulate.py
│       ├── demo/                   #     same files with TODOs
│       └── demo-shell/             #     Cosmos DB Shell .cosmos.js + per-container JSON
├── iteration-02-optimized/         # CustomerOrders + Products (agent-guided)
│   ├── complete/
│   │   ├── app/                    #   FastAPI-ready: models / repository / service / main
│   │   ├── seed.py
│   │   ├── migrate_from_01.py
│   │   └── indexing-policy.json
│   ├── demo/                       #   same shape, skeleton
│   └── demo-shell/                 #   Cosmos DB Shell .cosmos.js + per-container JSON
└── iteration-03-composite-indexes/ # optional stretch: 3 new access patterns
│   ├── complete/                   #   extended-access-patterns.md, queries.py, policy
│   ├── demo/
│   └── demo-shell/                 #   Cosmos DB Shell .cosmos.js (policy + queries)
└── iteration-04-hybrid-vector-search/ # optional, cloud-only: vector + FTS + RRF
    ├── README.md                   #   runbook (provision, seed, search)
    ├── access-patterns.md          #   R-VEC-1 / R-FTS-1 / R-HYB-1
    ├── requirements.txt            #   azure-identity + openai (additive)
    ├── infra/                      #   parameterized Bicep + deploy.ps1
    │   └── modules/                #     cosmos / foundry / rbac
    ├── complete/                   #   keyless: shared / seed / search
    └── demo/                       #   skeletons with TODOs
```

## Prerequisites

1. Python 3.10+
2. The local Cosmos DB emulator running on `https://localhost:8081`
   (see [`/docs/01-setup`](../docs/01-setup/)).
3. `pip install -r src/requirements.txt`
4. Copy [`.env.example`](./.env.example) to `src/.env` — every Python
   entry point loads it via `python-dotenv` to pick up
   `COSMOS_ENDPOINT` / `COSMOS_KEY` / `COSMOS_DB`. The defaults already
   point at the local emulator; edit only if you target a different
   profile (Linux vNext, real Azure account, alt DB name). `.env` is
   gitignored — never commit it.

   ```powershell
   Copy-Item src/.env.example src/.env   # PowerShell
   # cp src/.env.example src/.env        # bash / zsh
   ```

## Quick start

The runnable surface is the **Model A working tree** at the repo root
(`demo/app/` runtime + `scripts/` one-shots). The per-iteration
`src/iteration-NN-*/complete/` and `demo/` trees are **reference
content** for session attendees — see
[`docs/03-walkthrough/CONVENTIONS.md`](../docs/03-walkthrough/CONVENTIONS.md)
for the canonical layout. Each iteration also has a
`docs/03-walkthrough/N-iteration-NN-*-complete.md` runbook with the
same commands and an expected-RU envelope.

```powershell
# from repo root
pip install -r src/requirements.txt

# 1) iteration 1 — feel the pain
python -u -m scripts.seed_iteration_01_naive_a
python -u -m scripts.patterns_iteration_01_naive_a

# 2) iteration 2 — the agent-guided redesign
python -u -m scripts.apply_iteration_02
python -u -m demo.app.main seed
python -u -m demo.app.main get-customer C00005
python -u -m demo.app.main place-order   C00005

# 3) iteration 3 (optional) — composite indexes (single before/after harness)
python -u -m scripts.bench_iteration_03

# 4) iteration 4 (optional, cloud-only) — vector + full-text + hybrid search
#    Provisions a small Azure footprint via Bicep — see
#    src/iteration-04-hybrid-vector-search/README.md.
python -u -m scripts.seed_iteration_04
python -u -m demo.app.queries vec "lightweight aluminum mountain bike for trails"
```

Compare the `[RU]` lines from iteration 1 vs iteration 2 — that's the
demo's punchline.

## Manual demos via the Cosmos DB Shell

Every iteration also ships a `demo-shell/` folder with:

* `seed-data/<Container>.json` — the master JSON reshaped into the exact
  document layout that iteration's containers expect.
* `01-setup.cosmos.js` — creates database, containers, and indexing
  policies inside the Cosmos DB Shell.
* `02-access-patterns.cosmos.js` (or `02-simulate-...` / `02-extended-queries.cosmos.js`)
  — one runnable block per access pattern with `requestCharge` printed.

Use these when you want to call out individual operations interactively
without driving the Python CLI. See each iteration's
[`demo-shell/README.md`](./iteration-01-naive/naive-a/demo-shell/README.md)
for setup and walkthrough.

To regenerate the per-container JSON after editing `sample-data/master/`:

```powershell
cd src/sample-data
python build_demo_shell.py
```

## FastAPI later

`demo/app/service.py` is HTTP-framework-agnostic and laid out so adding
an `demo/app/api.py` that calls `service.CustomerOrderService` is the
only change required to expose the same logic over HTTP. There is no
FastAPI dependency today because the demo runs from the command line.

## Sample data

`sample-data/master/` is committed so attendees can seed Cosmos DB without
running the generator. Re-generate only if you want a different size:

```powershell
cd src/sample-data
python generate.py --customers 25 --orders-per-customer 50
```

See [`sample-data/README.md`](./sample-data/README.md) for details.

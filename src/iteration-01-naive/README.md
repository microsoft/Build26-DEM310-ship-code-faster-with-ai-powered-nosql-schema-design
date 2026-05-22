# Naive iteration 1 — two anti-patterns side by side

This folder shows the **two most common mistakes** a developer makes the
first time they port a relational order-management schema to Cosmos DB.

Both versions seed and query the same domain (customers, orders, items),
so attendees can compare RU and behavior directly.

| Sub-folder | Anti-pattern | What it demonstrates |
|------------|--------------|----------------------|
| [`naive-a/`](./naive-a/) | **1:1 relational port** — one container per table, each partitioned by its own id | Cross-partition reads on every join; place-order is N writes spread across 2 containers and is **not atomic** |
| [`naive-b/`](./naive-b/) | **Single document per customer** — all of a customer's orders live in one ever-growing `orders[]` array | **Unbounded array** anti-pattern: every write rewrites the whole document, RU and doc size grow linearly, and the doc will eventually hit the **2 MB Cosmos item limit** |

Iteration 2 ([`/src/iteration-02-optimized`](../iteration-02-optimized/))
fixes both at once: customers and orders live in the **same container**
(so place-order is one transactional batch) but as **separate documents**
sharing `/customerId` as the partition key (so the customer doc stays
small and orders are bounded).

## Recommended demo order

Both flavors run from the repo-root `scripts/` folder — there is no
per-iteration `complete/` or `demo/` for iteration 1. The block below
is copy-paste-friendly: every line is a single, runnable command, and
each command writes its own log file.

```powershell
# from repo root — activate the venv created in docs/01-setup/4-python-env.md
.venv\Scripts\Activate.ps1          # PowerShell
# source .venv/bin/activate         # bash / zsh
pip install -r src/requirements.txt

# --- naive-a: 5-container relational port -----------------------------
python -u -m scripts.seed_iteration_01_naive_a                          --log logs/iter-01/seed.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P1         --log logs/iter-01/step5-P1.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P2         --log logs/iter-01/step5-P2.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P2b        --log logs/iter-01/step5-P2b.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P3         --log logs/iter-01/step5-P3.log
python -u -m scripts.patterns_iteration_01_naive_a --pattern P4         --log logs/iter-01/step5-P4.log

# --- naive-b: unbounded embedded-array growth -------------------------
python -u -m scripts.seed_iteration_01_naive_b                          --log logs/iter-01/naive-b-seed.log
python -u -m scripts.simulate_iteration_01_naive_b                      --log logs/iter-01/naive-b-simulate-default.log
```

Shortcut: `python -u -m scripts.patterns_iteration_01_naive_a --pattern all`
runs P1…P4 (plus P2b) in one process and writes the same five log files.

Then open the Cosmos DB Agent, paste both result sets, and ask for a
redesign — you should land on iteration 2.

See [`naive-a/README.md`](./naive-a/README.md) and
[`naive-b/README.md`](./naive-b/README.md) for the per-flavor
walkthroughs and what to look for in the output.

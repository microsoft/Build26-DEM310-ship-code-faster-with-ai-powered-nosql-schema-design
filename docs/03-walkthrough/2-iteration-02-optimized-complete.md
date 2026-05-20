# Iteration 2 — Runbook (execute the finished solution)

This is the **non-prompt** runbook for an already-checked-in iteration-2
solution. Use it to:

- Demo iteration 2 end-to-end without re-prompting the agent.
- Verify that prompt changes in
  [`2-iteration-02-optimized.md`](./2-iteration-02-optimized.md) still
  produce code that behaves like this reference run.

Layout assumed: see [CONVENTIONS.md](./CONVENTIONS.md).

---

## Prerequisites (one-time)

1. Cosmos DB emulator running on `https://localhost:8081` (well-known
   key). See [setup step 2](../01-setup/2-cosmos-emulator.md).
2. Python venv with `src/requirements.txt` installed
   ([setup step 4](../01-setup/4-python-env.md)).
3. `src/.env` populated with the emulator URI + key.

```powershell
# from repo root
. .venv/Scripts/Activate.ps1
pip install -r src/requirements.txt
```

---

## Step A — Create / refresh containers (iter-2 baseline policy)

```powershell
python -u -m scripts.apply_iteration_02
```

Expected: `drift==0`, two containers reported:

- `CustomerOrders` partitioned by `/customerId`, composite index
  `[/customerId ASC, /orderDate DESC]`.
- `Products` partitioned by `/categoryId`, composite index
  `[/type ASC, /price ASC]`.

## Step B — Seed canonical sample data

```powershell
python -u -m demo.app.main seed --log logs/iter-02/seed.log
```

Loads from `src/sample-data/master/*.json`. Expected counts on stdout
(±depending on master/ regen):

| Container        | Docs |
|------------------|------|
| `CustomerOrders` | ~510 (10 customers + ~500 orders) |
| `Products`       | ~50  |

## Step C — Run every access pattern

```powershell
python -u -m demo.app.main get-customer   C00005          --log logs/iter-02/step5-P1.log
python -u -m demo.app.main get-order      C00005 O0000003 --log logs/iter-02/step5-P2.log
python -u -m demo.app.main compare-reads  C00005 O0000003 --log logs/iter-02/step5-P2b.log
python -u -m demo.app.main place-order    C00005          --log logs/iter-02/step5-P3.log
python -u -m demo.app.main list-products  CAT006          --log logs/iter-02/step5-P4.log
```

### Expected RU envelope (emulator)

| Pattern | What runs                          | RU (typical)      | Health signal |
|---------|------------------------------------|-------------------|---------------|
| P1      | single-partition query             | 2–4               | `retrieved==output`, `indexUtil=1.0` |
| P2      | point read                         | ~1.0              | n/a (read_item) |
| P2b     | point read + 1 in-partition query  | 1.0 + ~2.9        | shows ~3× penalty of going through query engine |
| P3      | point read + transactional batch   | ~1.0 + ~10–15     | one batch, no orphans |
| P4      | single-partition query             | 2–3               | `indexUtil=1.0` |

If numbers drift more than 2× from the table above, the seed shape
likely diverged from the iter-2 design — re-run Step A then Step B.

## Step D — One-shot agent recap

```text
@cosmos Read every log under `logs/iter-02/` and the expected envelope
in `docs/03-walkthrough/2-iteration-02-optimized-complete.md`. Confirm
each pattern landed in its envelope and call out any drift.
```

---

## Files exercised by this runbook

| File                                     | Role                            |
|------------------------------------------|---------------------------------|
| `scripts/apply_iteration_02.py`          | container + policy apply, drift check |
| `demo/app/main.py`                       | CLI entry point                 |
| `demo/app/service.py`                    | P1–P4 business logic            |
| `demo/app/repository.py`                 | Cosmos calls, RU/metrics capture |
| `demo/app/models.py`                     | Pydantic shapes                 |
| `src/sample-data/master/*.json`          | canonical seed data             |

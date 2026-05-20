# Iteration 3 — Runbook (execute the finished solution)

This is the **non-prompt** runbook for an already-checked-in iteration-3
solution. Use it to:

- Demo the composite-index before/after story without re-prompting the
  agent.
- Verify that prompt changes in
  [`3-iteration-03-composite-indexes.md`](./3-iteration-03-composite-indexes.md)
  still produce code that reproduces this reference run.

Layout assumed: see [CONVENTIONS.md](./CONVENTIONS.md).

---

## Prerequisites

- Iteration 2 already run end-to-end via
  [`2-iteration-02-optimized-complete.md`](./2-iteration-02-optimized-complete.md).
  Containers `CustomerOrders` and `Products` exist on the emulator
  with iter-2 data seeded.

---

## Step A — Sanity-check the iter-2 baseline (optional)

```powershell
python -u -m scripts.apply_iteration_02
python -u -m demo.app.queries all --log logs/iter-03/preflight.log
```

R-EXT-3 is expected to **fail with 400 BadRequest** in the iter-2
baseline — the 3-path composite + multi-key `ORDER BY` is exactly the
gap iter-3 closes. The script logs this gracefully and continues.

## Step B — Combined before/after harness (the headline)

```powershell
python -u -m scripts.bench_iteration_03
```

What it does:

1. Applies iter-2 baseline policy (no R-EXT composites).
2. Captures `bench-before.json` for every R-EXT-* query.
3. Applies iter-3 policy (= iter-2 + new composites).
4. Captures `bench-after.json` for every R-EXT-* query.
5. Writes a markdown comparison table to `logs/iter-03/bench.log`
   AND stdout.
6. Exits non-zero on regression.

### Expected `bench.log` shape

| Pattern  | Before RU | After RU | Δ RU  | Δ %    | retrieved/output before | retrieved/output after | Verdict |
|----------|-----------|----------|-------|--------|--------------------------|-------------------------|---------|
| R-EXT-1  | ~8        | ~3       | -5    | -60%   | 50 / 50 (sort in mem)    | 5 / 5                   | ✓ healthy |
| R-EXT-2  | ~25       | ~8       | -17   | -68%   | 500 / 20 (cross-part)    | 20 / 20                 | ✓ healthy |
| R-EXT-3  | 400 ERR   | ~3       | n/a   | n/a    | n/a                      | 10 / 10                 | ✓ healthy (newly viable) |

Exact RU depends on emulator build and seed size; what matters is the
order-of-magnitude shape and the `retrieved == output` flip.

## Step C — Verify final policy is exactly the iter-3 spec

```powershell
python -u -m scripts.apply_iteration_03
```

Expected: `drift==0`, both containers reported with these composites:

- `CustomerOrders`:
  `[/customerId ASC, /orderDate DESC]` **and**
  `[/status ASC, /orderDate DESC]`
- `Products`:
  `[/type ASC, /price ASC]` **and**
  `[/type ASC, /rating DESC, /price ASC]`

## Step D — One-shot agent recap

```text
@cosmos Read `logs/iter-03/bench.log` plus the raw captures
`logs/iter-03/bench-before.json` and `logs/iter-03/bench-after.json`.
Compare them and explain which composite index removed the in-memory
sort, where the retrieved/output ratio tightened, and confirm
R-EXT-3's 400 BadRequest in the `before` pass is the documented
3-path multi-key ORDER BY limitation.
```

---

## Files exercised by this runbook

| File                                     | Role                                    |
|------------------------------------------|-----------------------------------------|
| `scripts/apply_iteration_02.py`          | revert to iter-2 baseline policy        |
| `scripts/apply_iteration_03.py`          | apply iter-3 policy + drift check       |
| `scripts/bench_iteration_03.py`          | single combined before/after harness    |
| `demo/app/queries.py`                    | R-EXT-1/2/3 implementations             |
| `demo/app/repository.py`                 | RU + raw metrics capture                |
| `logs/iter-03/bench.log`                 | human-readable comparison               |
| `logs/iter-03/bench-{before,after}.json` | raw response headers per call           |

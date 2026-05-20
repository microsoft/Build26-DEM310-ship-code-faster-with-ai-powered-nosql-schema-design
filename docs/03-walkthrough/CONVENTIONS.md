# Conventions — generated code, logs, and artefacts

This document defines **where things go** for every iteration in this
walkthrough. Every prompt in `2-iteration-02-optimized.md` /
`3-iteration-03-composite-indexes.md` /
`4-iteration-04-hybrid-vector-search.md` targets the layout below so
the agent has no ambiguity about output paths.

---

## 1. Repository layout (Model A — single working tree)

We use a **single working tree** at the repo root for code that is
actually executed during the demo, and the per-iteration folders
under `src/iteration-NN-*/` are **reference content for session
attendees** (READMEs + reference snippets) — not the runtime.

```
<repo-root>/
├── demo/app/                              ← RUNTIME CODE (canonical)
│   ├── models.py                          ← Pydantic shapes
│   ├── repository.py                      ← all Cosmos calls + RU/metrics capture
│   ├── service.py                         ← business logic (P1–P4)
│   ├── queries.py                         ← R-EXT-1/2/3 (iter 3) + R-VEC/FTS/HYB (iter 4)
│   └── main.py                            ← CLI: `python -m demo.app.main <pattern> ...`
│
├── scripts/                               ← one-shot tooling (apply / seed / bench)
│   ├── apply_iteration_02.py              ← iter-2 baseline policy
│   ├── apply_iteration_03.py              ← iter-3 = iter-2 + new composites
│   ├── seed_iteration_02.py               ← load master JSON into containers
│   └── bench_iteration_03.py              ← single combined before/after harness
│
├── src/iteration-NN-*/                    ← SESSION CONTENT (reference only)
│   └── README.md                          ← points to demo/app/ and scripts/
│
├── src/sample-data/master/*.json          ← CANONICAL SEED DATA (load this)
├── src/sample-data/source/*.csv           ← upstream CSVs (regen master with generate.py)
│
├── docs/                                  ← published walkthrough
│   └── 03-walkthrough/
│       ├── 2-iteration-02-optimized.md            ← prompts (what to ask the agent)
│       ├── 2-iteration-02-optimized-complete.md   ← runbook for the finished solution
│       ├── 3-iteration-03-composite-indexes.md
│       ├── 3-iteration-03-composite-indexes-complete.md
│       ├── 4-iteration-04-hybrid-vector-search.md
│       └── CONVENTIONS.md                          ← this file
│
├── iteration-NN-output.md                 ← per-iteration design checkpoint (gitignored)
└── logs/                                  ← all generated artefacts (gitignored)
    ├── iter-02/
    └── iter-03/
```

### Rules

| Concern                            | Goes in                                          |
|------------------------------------|--------------------------------------------------|
| New runtime Python module          | `demo/app/`                                      |
| New one-shot script (apply / seed / bench) | `scripts/`                                |
| Design checkpoint markdown         | `iteration-NN-output.md` at repo root            |
| Run output (logs, JSON dumps)      | `logs/iter-NN/...`                               |
| Reference content for attendees    | `src/iteration-NN-*/` (README only — link to `demo/app/`) |
| Canonical seed data                | `src/sample-data/master/*.json` (load this)      |
| Upstream raw data                  | `src/sample-data/source/*.csv` (regen master via `generate.py`) |

The stub `*.py` files currently sitting under
`src/iteration-NN-*/{demo,complete}/` are **legacy** and should either
be deleted or rewritten as a one-line `from demo.app.queries import *`
shim. Do not edit them as part of an iteration — they will drift from
the runtime.

---

## 2. Sample-data source of truth

```
src/sample-data/
├── source/                ← raw CSVs from AdventureWorksLT
│   ├── Customer.csv
│   ├── SalesOrderHeader.csv
│   ├── SalesOrderDetail.csv
│   ├── Product.csv
│   └── ProductCategory.csv
├── generate.py            ← deterministic CSV → JSON build step
└── master/                ← CANONICAL: load these into containers
    ├── customers.json
    ├── orders.json
    ├── products.json
    └── categories.json
```

**Seed scripts must load from `master/*.json`.** The CSVs in `source/`
are the upstream feed; running `python src/sample-data/generate.py`
re-builds `master/`. If you ever ask the agent to "load sample data",
say *from `src/sample-data/master/*.json`* — never the CSVs directly,
or you'll get one-off parsers that miss the derived fields
(`lastOrderAt`, `lifetimeOrderCount`, embedded `items[]`, denormalized
`categoryName`).

---

## 3. Log and artefact naming

All generated output goes under `logs/iter-NN/`. The directory is in
`.gitignore`; nothing in it ships.

### Standard filenames

| Iteration | Artefact                                  | Path                                                  |
|-----------|-------------------------------------------|-------------------------------------------------------|
| iter 2    | seed run                                  | `logs/iter-02/seed.log`                               |
| iter 2    | per-pattern run                           | `logs/iter-02/step5-P<N>.log` (P1/P2/P2b/P3/P4)       |
| iter 3    | combined before/after harness output      | `logs/iter-03/bench.log`                              |
| iter 3    | raw before/after JSON capture             | `logs/iter-03/bench-{before,after}.json`              |
| iter 4    | seed run                                  | `logs/iter-04/seed.log`                               |
| iter 4    | per-pattern run                           | `logs/iter-04/step5-{vec,fts,hyb}.log`                |

**Filenames bind to content.** The script writes its own file via a
`--log <path>` flag rather than relying on `Tee-Object`. This avoids
the (real) failure mode where `iteration-02-step5-P3.log` was created
by a command that actually ran P4. If you must tee on the command
line, **always** check that the filename matches the command's
pattern argument before stepping forward.

### Log line format

Every Cosmos call should print one line of this shape (the
`demo.repo` logger in `demo/app/repository.py` already does this):

```
[RU] <label> <RU>  count=<N>  metrics: retrievedDocumentCount=N outputDocumentCount=N indexHitDocumentCount=N totalExecutionTimeInMs=N.NN
```

Add a one-token health verdict at the end where the script can
compute it (`retrieved == output` plus `indexUtilizationRatio == 1.0`
⇒ `✓ healthy`).

Every multi-call run ends with a `TOTAL` line:

```
[RU] TOTAL (<N> call(s))  <sum>
```

### What `bench_*.py` writes

A bench (before/after) script should write **both**:

1. A human-readable comparison block to `logs/iter-NN/bench.log`
   (markdown table on stdout, tee'd to disk).
2. The raw per-call response headers as JSON to
   `logs/iter-NN/bench-{before,after}.json` for post-mortem.

---

## 4. Design checkpoints — `iteration-NN-output.md`

Every iteration whose Step 1 is "propose a design" writes that
proposal to `iteration-NN-output.md` at the repo root. The file is
deliberately at the root (not under `docs/`) for two reasons:

1. It is **review-and-iterate scratch space** between presenter and
   agent; it is not part of the published walkthrough.
2. It is **gitignored**, so each presenter generates their own.

When an iteration is finalized for inclusion in the published session
content, the contents move into the matching
`docs/03-walkthrough/N-iteration-NN-*-complete.md` runbook and the
root file is deleted.

---

## 5. Prompt-authoring rules

When writing a prompt in a walkthrough doc:

1. **Specify the absolute target path** for any file the agent must
   create or modify (`demo/app/queries.py`, not "queries.py").
2. **Specify the log destination** (`logs/iter-NN/<name>.log`) — the
   agent will pass it through to the script.
3. **State hard constraints up front in a fenced block** — e.g.
   *"don't change partition keys, don't add containers, don't change
   doc shapes"*. The iter-3 design prompt did this and it kept the
   work tightly scoped.
4. **State the completion criterion**: "Done when: drift==0 AND every
   call logs RU+metrics AND the bench file exists at
   `logs/iter-03/bench.log`."
5. **For comparisons, pre-specify the table shape** so the agent
   doesn't re-invent it: *"Produce a markdown table with columns
   `Pattern | Before RU | After RU | Δ | indexUtil | Verdict`."*
6. **Reference the predecessor checkpoint by absolute path** when an
   iteration builds on a previous one
   (`@cosmos Read iteration-02-output.md ...`).

"""Iteration-2 runtime app.

Layout per `docs/03-walkthrough/CONVENTIONS.md` (Model A): the live demo
runs out of `demo/app/` at the repo root. `src/iteration-02-optimized/`
holds the reference content the slides quote from but is not executed.

The package is intentionally small:

* `models.py`     — Pydantic shapes for the iter-2 documents.
* `repository.py` — Cosmos calls. Singleton `CosmosClient`, 429-aware
                    retry policy, a single `_query()` helper that pulls
                    `x-ms-request-charge`, `x-ms-item-count` and the
                    `x-ms-documentdb-query-metrics` header off every
                    response.
* `service.py`    — Business logic. `p1`..`p4` plus `p2b`. P3 is a
                    transactional batch (read customer, prepend the
                    new order to `orderSummary[]`, upsert customer +
                    create order in one batch, all in `customerId`'s
                    partition).
* `main.py`       — argv -> service -> stdout. Silences noisy
                    `azure.*`/`urllib3`/`aiohttp` loggers and routes
                    curated output to a log via `--log`.
"""

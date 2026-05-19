# Sample data

This folder contains:

| Path                  | What it is                                                       |
|-----------------------|------------------------------------------------------------------|
| `source/`             | Raw sample CSV exports from a classic RDBMS schema (input to the generator) |
| `generate.py`         | Deterministic script that builds the trimmed master JSON         |
| `master/`             | Generated JSON used by every iteration's `seed.py`               |
| `build_demo_shell.py` | Reshapes `master/` into each iteration's `demo-shell/seed-data/` |

The `master/` files are committed so attendees can seed Cosmos DB without
running the generator first. Regenerate them only if you want a different
size or layout.

## Master shape

```text
master/
├── customers.json    # 10 documents
├── categories.json   # 5 documents
├── products.json     # 50 documents (10 per category)
└── orders.json       # 200 documents (20 per customer, 1-10 items each)
```

The master files are *iteration-agnostic*. Each iteration's `seed.py`
re-shapes them into the container layout it needs (e.g. iteration 1 keeps
them split across five containers, iteration 2 embeds order items inside
the order document and the customer summary inside the customer document).

## Regenerate

```powershell
cd src/sample-data
python generate.py                                  # defaults: seed=20260517
python generate.py --customers 25 --orders-per-customer 50
```

Run `python generate.py --help` for all flags.

## Regenerate the per-iteration shell artifacts

`build_demo_shell.py` reshapes `master/` into each iteration's
`demo-shell/seed-data/<Container>.json` files (the exact document layout
each container expects). Run it after re-generating `master/`:

```powershell
cd src/sample-data
python build_demo_shell.py
```

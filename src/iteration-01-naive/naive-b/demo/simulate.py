"""Demo skeleton for the unbounded-array growth simulator.

The complete reference lives in ../complete/simulate.py.

Steps to implement live:
  1. Pick a customer id (default: C00005).
  2. For 20 iterations:
       a. Read the customer doc + capture read RU and size.
       b. Append one new order (with a few items from master/products.json)
          to doc['orders'].
       c. Upsert the doc + capture upsert RU.
  3. Print a per-iteration table and project when the document will hit
     the 2 MB Cosmos item limit.
"""

from __future__ import annotations

from shared import CONTAINER_NAME, DATABASE_NAME, get_client


def main() -> int:
    # TODO (demo): implement the 20-iteration grow-and-upsert loop and
    # print a per-iteration table of (iteration, doc KB, read RU,
    # upsert RU). End with the 2 MB projection.
    ...
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Wrapper: seed the iteration-1 naive-b (single embedded array) container.

Runtime entrypoint per `docs/03-walkthrough/CONVENTIONS.md`:

    python -u -m scripts.seed_iteration_01_naive_b --log logs/iter-01/naive-b-seed.log

Drops and recreates `CustomersWithEmbeddedOrders`, then seeds 10
customer docs with empty `orders[]` arrays. simulate_iteration_01_naive_b
then grows one customer's array iteration by iteration.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETE_DIR = REPO_ROOT / "src" / "iteration-01-naive" / "naive-b" / "complete"
sys.path.insert(0, str(COMPLETE_DIR))

from scripts._logsetup import attach_log  # noqa: E402

import seed as naive_b_seed  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--log",
        default="logs/iter-01/naive-b-seed.log",
        help="path to write the run log (default: logs/iter-01/naive-b-seed.log)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    attach_log(args.log)  # atexit handles flush + close
    print("=" * 70)
    print("Iteration 1 / naive-b — seed CustomersWithEmbeddedOrders")
    print("=" * 70)
    container = naive_b_seed.ensure_database_and_container()
    naive_b_seed.seed(container)
    print(f"\nLog written to {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

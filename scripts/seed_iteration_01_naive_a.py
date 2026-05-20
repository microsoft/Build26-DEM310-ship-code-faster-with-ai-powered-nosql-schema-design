"""Seed the iteration-1 naive-a (5-container) layout.

Runtime entrypoint per `docs/03-walkthrough/CONVENTIONS.md`:

    python -u -m scripts.seed_iteration_01_naive_a --log logs/iter-01/seed.log
"""

from __future__ import annotations

import argparse

from scripts import _naive_a_seed
from scripts._logsetup import attach_log


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--log",
        default="logs/iter-01/seed.log",
        help="path to write the run log (default: logs/iter-01/seed.log)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    attach_log(args.log)  # atexit handles flush + close
    print("=" * 70)
    print("Iteration 1 / naive-a — seed 5 naive containers")
    print("=" * 70)
    _naive_a_seed.main()
    print(f"\nLog written to {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

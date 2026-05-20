"""Wrapper: simulate the iteration-1 naive-b unbounded-array growth.

Runtime entrypoint per `docs/03-walkthrough/CONVENTIONS.md`:

    python -u -m scripts.simulate_iteration_01_naive_b --log logs/iter-01/naive-b-simulate-default.log
    python -u -m scripts.simulate_iteration_01_naive_b --iterations 100 --items-per-order 100 --log logs/iter-01/naive-b-simulate-large-items.log

Forwards CLI args (--customer / --iterations / --items-per-order) to
`src/iteration-01-naive/naive-b/complete/simulate.py:main()` so the
demo and reference content stay in lock-step.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETE_DIR = REPO_ROOT / "src" / "iteration-01-naive" / "naive-b" / "complete"
sys.path.insert(0, str(COMPLETE_DIR))

from scripts._logsetup import attach_log  # noqa: E402

import simulate as naive_b_simulate  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--customer", default="C00005",
                   help="customerId to grow (default: C00005)")
    p.add_argument("--iterations", type=int, default=50,
                   help="number of orders to append (default: 50)")
    p.add_argument("--items-per-order", type=int, default=50,
                   help="line items per appended order (default: 50)")
    p.add_argument(
        "--log",
        default="logs/iter-01/naive-b-simulate-default.log",
        help="path to write the run log (default: logs/iter-01/naive-b-simulate-default.log)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    attach_log(args.log)  # atexit handles flush + close
    print("=" * 70)
    print("Iteration 1 / naive-b — simulate unbounded-array growth")
    print("=" * 70)

    # Hand the underlying simulate.py exactly the argv it expects.
    # Its parse_args() ignores anything else on sys.argv.
    sys.argv = [
        "simulate.py",
        "--customer", args.customer,
        "--iterations", str(args.iterations),
        "--items-per-order", str(args.items_per_order),
    ]
    rc = naive_b_simulate.main()
    print(f"\nLog written to {args.log}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

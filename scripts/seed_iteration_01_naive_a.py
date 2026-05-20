"""Wrapper: seed the iteration-1 naive-a (5-container) layout.

Runtime entrypoint per `docs/03-walkthrough/CONVENTIONS.md`:

    python -u -m scripts.seed_iteration_01_naive_a --log logs/iter-01/seed.log

Imports the reference seeding logic from
`src/iteration-01-naive/naive-a/complete/seed.py` so this script and
the per-iteration reference content stay in lock-step.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the naive-a/complete folder importable as flat modules
# (`shared`, `seed`). The reference content there is intentionally not
# laid out as a package, so we splice it onto sys.path.
REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETE_DIR = REPO_ROOT / "src" / "iteration-01-naive" / "naive-a" / "complete"
sys.path.insert(0, str(COMPLETE_DIR))

from scripts._logsetup import attach_log  # noqa: E402

import seed as naive_a_seed  # noqa: E402


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
    naive_a_seed.main()
    print(f"\nLog written to {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

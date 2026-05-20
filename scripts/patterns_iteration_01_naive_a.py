"""Wrapper: run iteration-1 naive-a access patterns (P1..P4 + P2b).

Runtime entrypoint per `docs/03-walkthrough/CONVENTIONS.md`:

    python -u -m scripts.patterns_iteration_01_naive_a --pattern all
    python -u -m scripts.patterns_iteration_01_naive_a --pattern P1  --log logs/iter-01/step5-P1.log
    python -u -m scripts.patterns_iteration_01_naive_a --pattern P2b --log logs/iter-01/step5-P2b.log

Modes
-----
* ``--pattern all``      : run P1, P2, P2b, P3, P4 in order. Each
                           pattern writes its own log under
                           ``logs/iter-01/step5-P<N>.log`` (any
                           ``--log`` value is ignored in this mode so
                           per-pattern filenames always match content).
* ``--pattern P<N>``     : run a single pattern. Default log path is
                           ``logs/iter-01/step5-P<N>.log`` unless
                           ``--log`` overrides it.

P2b is implemented here (not in
``src/iteration-01-naive/naive-a/complete/patterns.py``) — it
intentionally re-issues P2's order lookup as both a SQL query and a
point read so attendees can read the RU gap straight off the screen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETE_DIR = REPO_ROOT / "src" / "iteration-01-naive" / "naive-a" / "complete"
sys.path.insert(0, str(COMPLETE_DIR))

from scripts._logsetup import attach_log  # noqa: E402

import patterns as naive_a_patterns  # noqa: E402
from shared import DATABASE_NAME, get_client, print_query, print_ru  # noqa: E402

# Demo IDs — must match those used in
# src/iteration-01-naive/naive-a/complete/patterns.py:main().
SAMPLE_CUSTOMER = "C00005"
SAMPLE_ORDER = "O0000001"
SAMPLE_CATEGORY = "CAT006"

ALL_PATTERNS = ("P1", "P2", "P2b", "P3", "P4")


def _p2b_query_vs_point_read(db, order_id: str) -> None:
    """Same order, two ways: SQL query vs point read. Print both RUs."""
    print(f"\nP2b — Order {order_id}: query vs. point read")
    orders = db.get_container_client("Orders")

    items, ru_q, count, metrics = naive_a_patterns._query(
        orders,
        "SELECT * FROM c WHERE c.orderId = @oid",
        [{"name": "@oid", "value": order_id}],
        partition_key=order_id,
    )
    print_query("SQL query by orderId (in partition)", ru_q, len(items), count, metrics)

    orders.read_item(item=order_id, partition_key=order_id)
    ru_p = float(orders.client_connection.last_response_headers.get(
        "x-ms-request-charge", 0.0
    ))
    print_ru("point read same Order header", ru_p, 1)

    delta = ru_q - ru_p
    print_ru(f"DELTA query - point ({delta:+.2f} RU)", delta)


_DISPATCH = {
    "P1":  lambda db: naive_a_patterns.p1_customer_with_recent_orders(db, SAMPLE_CUSTOMER),
    "P2":  lambda db: naive_a_patterns.p2_order_with_items(db, SAMPLE_ORDER, SAMPLE_CUSTOMER),
    "P2b": lambda db: _p2b_query_vs_point_read(db, SAMPLE_ORDER),
    "P3":  lambda db: naive_a_patterns.p3_place_order(db, SAMPLE_CUSTOMER),
    "P4":  lambda db: naive_a_patterns.p4_products_in_category(db, SAMPLE_CATEGORY),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--pattern",
        choices=("all", *ALL_PATTERNS),
        default="all",
        help="which access pattern to run (default: all)",
    )
    p.add_argument(
        "--log",
        default=None,
        help=(
            "log path. Ignored when --pattern=all (each pattern always "
            "writes logs/iter-01/step5-P<N>.log so filename matches "
            "content). Default for a single pattern: "
            "logs/iter-01/step5-P<N>.log."
        ),
    )
    return p.parse_args()


def _run_one(pattern: str, log_path: str) -> None:
    # Note: when --pattern=all we call this multiple times in one
    # process. Each call swaps sys.stdout/stderr to a fresh _Tee onto
    # the next log file; the previous file is not closed until process
    # exit (atexit closes them all in LIFO order). That's fine — the
    # files don't overlap because writes only happen between attach_log
    # calls.
    attach_log(log_path)
    print("=" * 70)
    print(f"Iteration 1 / naive-a — access pattern {pattern}")
    print("=" * 70)
    client = get_client()
    db = client.get_database_client(DATABASE_NAME)
    _DISPATCH[pattern](db)
    print(f"\nLog written to {log_path}")


def main() -> int:
    args = parse_args()

    if args.pattern == "all":
        for pat in ALL_PATTERNS:
            _run_one(pat, f"logs/iter-01/step5-{pat}.log")
        return 0

    log_path = args.log or f"logs/iter-01/step5-{args.pattern}.log"
    _run_one(args.pattern, log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

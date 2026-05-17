"""CLI entry point — `python -m complete.app.main <verb> [args...]`.

Available verbs:

    get-customer   <customerId>
    get-order      <customerId> <orderId>
    place-order    <customerId> [categoryId]
    list-products  <categoryId>

The CLI is intentionally tiny: parse argv, hand off to the service, pretty-
print the result. No argparse, no click — when FastAPI is wired in later,
`api.py` will call the same service methods.
"""

from __future__ import annotations

import json
import sys

from .service import CustomerOrderService


def _dump(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    verb = argv[1]
    svc = CustomerOrderService()

    try:
        if verb == "get-customer" and len(argv) == 3:
            _dump(svc.get_customer_with_orders(argv[2]))
        elif verb == "get-order" and len(argv) == 4:
            _dump(svc.get_order(argv[2], argv[3]))
        elif verb == "place-order" and len(argv) in (3, 4):
            category = argv[3] if len(argv) == 4 else "CAT006"
            _dump(svc.place_order(argv[2], category))
        elif verb == "list-products" and len(argv) == 3:
            _dump(svc.list_products(argv[2]))
        else:
            print(__doc__)
            return 2
    except Exception as exc:  # noqa: BLE001 - CLI top-level
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

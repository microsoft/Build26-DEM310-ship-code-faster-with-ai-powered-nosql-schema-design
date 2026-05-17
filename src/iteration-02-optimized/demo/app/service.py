"""Service layer — DEMO skeleton.

Goal: same business logic as iteration 1, but driven by the new repository
that only does single-partition reads/writes. The transactional batch in
``place_order`` is the headline change.

See complete/app/service.py for the reference implementation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .repository import CustomerOrdersRepository, ProductsRepository


def _print_ru(label: str, ru: float, count: int | None = None) -> None:
    suffix = f"  ({count} docs)" if count is not None else ""
    print(f"  [RU] {label:<45} {ru:>8.2f}{suffix}")


class CustomerOrderService:
    def __init__(self) -> None:
        self.customer_orders = CustomerOrdersRepository()
        self.products = ProductsRepository()

    def get_customer_with_orders(self, customer_id: str) -> dict[str, Any]:
        # TODO (demo): one query -> split items by `type` into customer + orders
        return {}

    def get_order(self, customer_id: str, order_id: str) -> dict[str, Any]:
        # TODO (demo): one point read on the order document
        return {}

    def place_order(self, customer_id: str, category_id: str = "CAT006") -> dict[str, Any]:
        # TODO (demo):
        #   1. pick products (in-partition on /categoryId)
        #   2. read the customer's partition to get current summary
        #   3. build the order doc + updated customer doc
        #   4. call repository.place_order_transactional(...)
        return {}

    def list_products(self, category_id: str) -> list[dict]:
        # TODO (demo): in-partition query ordered by price ASC
        return []

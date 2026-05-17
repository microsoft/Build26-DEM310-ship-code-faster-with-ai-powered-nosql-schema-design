"""Service layer: business logic. HTTP-framework-free so FastAPI can wrap
the same methods later without changes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import Customer, Order, OrderItem, OrderSummary
from .repository import (
    CustomerOrdersRepository,
    ProductsRepository,
)


def _print_ru(label: str, ru: float, count: int | None = None) -> None:
    suffix = f"  ({count} docs)" if count is not None else ""
    print(f"  [RU] {label:<45} {ru:>8.2f}{suffix}")


class CustomerOrderService:
    def __init__(self) -> None:
        self.customer_orders = CustomerOrdersRepository()
        self.products = ProductsRepository()

    # ---- P1 -------------------------------------------------------------
    def get_customer_with_orders(self, customer_id: str) -> dict[str, Any]:
        result = self.customer_orders.get_customer_and_orders(customer_id)
        _print_ru("query CustomerOrders (single partition)", result.request_charge,
                  len(result.items))
        customer = next(
            (d for d in result.items if d.get("type") == "customer"), None
        )
        orders = sorted(
            (d for d in result.items if d.get("type") == "order"),
            key=lambda o: o["orderDate"],
            reverse=True,
        )
        return {"customer": customer, "orders": orders[:5]}

    # ---- P2 -------------------------------------------------------------
    def get_order(self, customer_id: str, order_id: str) -> dict[str, Any]:
        result = self.customer_orders.get_order(customer_id, order_id)
        _print_ru("point read order (items embedded)", result.request_charge,
                  len(result.items))
        return result.items[0] if result.items else {}

    # ---- P3 -------------------------------------------------------------
    def place_order(self, customer_id: str, category_id: str = "CAT006") -> dict[str, Any]:
        # Pick a few products from the requested category.
        picks = self.products.pick_a_few(category_id, n=3)
        _print_ru("pick products (single partition)", picks.request_charge,
                  len(picks.items))

        items = [
            OrderItem(
                productId=p["productId"],
                productName=p["name"],
                categoryId=p["categoryId"],
                quantity=2,
                unitPrice=p["price"],
                lineTotal=round(p["price"] * 2, 2),
            )
            for p in picks.items
        ]
        total = round(sum(it.lineTotal for it in items), 2)

        # Read the current customer doc so we can roll up the summary.
        existing = self.customer_orders.get_customer_and_orders(customer_id)
        _print_ru("re-read customer partition for summary",
                  existing.request_charge, len(existing.items))
        customer_doc = next(
            (d for d in existing.items if d.get("type") == "customer"), None
        )
        if customer_doc is None:
            raise ValueError(f"customer {customer_id} not found")

        now = datetime.now(timezone.utc).isoformat()
        order_id = f"O{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        order = Order(
            id=order_id,
            customerId=customer_id,
            orderId=order_id,
            orderDate=now,
            status="Placed",
            totalAmount=total,
            items=items,
        )

        summary = customer_doc.get("orderSummary", {}) or {}
        customer_doc["orderSummary"] = OrderSummary(
            lifetimeOrders=int(summary.get("lifetimeOrders", 0)) + 1,
            lifetimeRevenue=round(
                float(summary.get("lifetimeRevenue", 0.0)) + total, 2
            ),
            lastOrderDate=now,
        ).model_dump()

        ru = self.customer_orders.place_order_transactional(
            customer_id=customer_id,
            customer_doc=customer_doc,
            order_doc=order.model_dump(),
        )
        _print_ru("transactional batch (customer + order)", ru, 2)
        return {"orderId": order_id, "totalAmount": total}

    # ---- P4 -------------------------------------------------------------
    def list_products(self, category_id: str) -> list[dict]:
        result = self.products.list_in_category(category_id)
        _print_ru("query Products (single partition)", result.request_charge,
                  len(result.items))
        return result.items

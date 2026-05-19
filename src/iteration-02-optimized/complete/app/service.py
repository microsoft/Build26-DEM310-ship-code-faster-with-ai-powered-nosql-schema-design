"""Service layer: business logic. HTTP-framework-free so FastAPI can wrap
the same methods later without changes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import Customer, Order, OrderItem, OrderSummary
from .repository import (
    CustomerOrdersRepository,
    ProductsRepository,
    Result,
)


# Fields we surface from `x-ms-documentdb-query-metrics`. The header is a
# `key=value;key=value;...` blob with ~30 entries — we pick the four that
# tell the RU story (retrieved vs output docs, index hits, total time).
_METRIC_KEYS = (
    "retrievedDocumentCount",
    "outputDocumentCount",
    "indexHitDocumentCount",
    "totalExecutionTimeInMs",
)


def _format_metrics(metrics: str) -> str:
    if not metrics:
        return ""
    parts = dict(p.split("=", 1) for p in metrics.split(";") if "=" in p)
    return " ".join(f"{k}={parts[k]}" for k in _METRIC_KEYS if k in parts)


def _print_ru(label: str, ru: float, count: int | None = None) -> None:
    suffix = f"  ({count} docs)" if count is not None else ""
    print(f"  [RU] {label:<45} {ru:>8.2f}{suffix}")


def _print_query(label: str, result: Result) -> None:
    """Print RU + server-reported item count + a compact metrics summary."""
    print(
        f"  [RU] {label:<45} {result.request_charge:>8.2f}"
        f"  (client={len(result.items)} docs, server item-count={result.item_count})"
    )
    summary = _format_metrics(result.query_metrics)
    if summary:
        print(f"       metrics: {summary}")


class CustomerOrderService:
    def __init__(self) -> None:
        self.customer_orders = CustomerOrdersRepository()
        self.products = ProductsRepository()

    # ---- P1 -------------------------------------------------------------
    def get_customer_with_orders(self, customer_id: str) -> dict[str, Any]:
        result = self.customer_orders.get_customer_and_orders(customer_id)
        _print_query("query CustomerOrders (single partition)", result)
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

    # ---- P2b ------------------------------------------------------------
    def compare_order_reads(
        self, customer_id: str, order_id: str
    ) -> dict[str, Any]:
        """Fetch the same single document two ways — point read vs
        in-partition SQL query — and print both RU charges so attendees
        can see the SDK's read_item() advantage over a SELECT that
        targets the exact same id + partition key.
        """
        point = self.customer_orders.get_order(customer_id, order_id)
        _print_ru(
            "point read   read_item(id, pk)",
            point.request_charge,
            len(point.items),
        )

        query = self.customer_orders.get_order_via_query(customer_id, order_id)
        _print_query(
            "query        WHERE customerId=@cid AND id=@oid", query
        )

        delta = query.request_charge - point.request_charge
        ratio = (
            query.request_charge / point.request_charge
            if point.request_charge
            else 0.0
        )
        print(
            f"  [RU] {'difference (query - point)':<45} "
            f"{delta:>+8.2f}  ({ratio:.1f}x)"
        )
        return {
            "orderId": order_id,
            "pointReadRU": point.request_charge,
            "queryRU": query.request_charge,
            "deltaRU": round(delta, 2),
            "ratio": round(ratio, 2),
        }

    # ---- P3 -------------------------------------------------------------
    def place_order(self, customer_id: str, category_id: str = "CAT006") -> dict[str, Any]:
        # Pick a few products from the requested category.
        picks = self.products.pick_a_few(category_id, n=3)
        _print_query("pick products (single partition)", picks)

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

        # P3 is a *read + transactional batch* pattern, not a single
        # write. We need the current `orderSummary` on the customer doc
        # so we can roll the new order into it, then upsert the customer
        # and create the order in one batch on the same partition key.
        #
        # The read MUST be filtered to a single document — a point read
        # by `id` + partition key — instead of a partition-wide
        # `SELECT * WHERE customerId = @cid`. The unfiltered query would
        # return every order in the partition (cost scales with partition
        # size, ~3–4 RU on a 20-order customer, much more in production);
        # the point read is a fixed ~1.0 RU regardless of how many orders
        # the customer has.
        existing = self.customer_orders.get_customer_doc(customer_id)
        _print_ru(
            "point read customer doc (filtered by id+pk)",
            existing.request_charge,
            len(existing.items),
        )
        customer_doc = existing.items[0] if existing.items else None
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
        _print_ru("transactional batch (upsert customer + create order)",
                  ru, 2)
        return {"orderId": order_id, "totalAmount": total}

    # ---- P4 -------------------------------------------------------------
    def list_products(self, category_id: str) -> list[dict]:
        result = self.products.list_in_category(category_id)
        _print_query("query Products (single partition)", result)
        return result.items

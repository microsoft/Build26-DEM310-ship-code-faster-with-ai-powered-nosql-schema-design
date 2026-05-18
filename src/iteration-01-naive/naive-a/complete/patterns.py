"""Iteration 1 access patterns: run P1..P4 against the naive design and
print the RU charge for each step.

    python complete/patterns.py

P1 — Get customer profile + their 5 most recent orders
P2 — Get one order with its line items
P3 — Place a new order (header + N item writes)
P4 — List all products in a category (sorted by price)

The patterns are written to mirror what a developer would naturally write
against the relational-style layout. They are intentionally NOT optimal;
that's the point of the demo.
"""

from __future__ import annotations

from datetime import datetime, timezone

from shared import DATABASE_NAME, get_client, print_query, print_ru


def _query(container, query, params=None, partition_key=None):
    """Run a SQL query and return (items, ru, server_item_count, query_metrics).

    When no ``partition_key`` is supplied we explicitly opt-in to a fan-out
    query via ``enable_cross_partition_query=True`` so the SDK won't quietly
    swallow the request. ``populate_query_metrics=True`` makes Cosmos return
    the ``x-ms-documentdb-query-metrics`` response header with the engine
    breakdown (retrieved/output doc counts, index lookup time, etc.).
    """
    kwargs = {
        "query": query,
        "parameters": params or [],
        "populate_query_metrics": True,
    }
    if partition_key is not None:
        kwargs["partition_key"] = partition_key
    else:
        kwargs["enable_cross_partition_query"] = True
    items = list(container.query_items(**kwargs))
    headers = container.client_connection.last_response_headers
    ru = float(headers.get("x-ms-request-charge", 0.0) or 0.0)
    count = int(headers.get("x-ms-item-count", 0) or 0)
    metrics = headers.get("x-ms-documentdb-query-metrics", "") or ""
    return items, ru, count, metrics


def p1_customer_with_recent_orders(db, customer_id: str) -> None:
    print(f"\nP1 — Customer {customer_id} + 5 most recent orders")
    customers = db.get_container_client("Customers")
    orders = db.get_container_client("Orders")

    cust, ru1, n1, m1 = _query(
        customers,
        "SELECT * FROM c WHERE c.customerId = @cid",
        [{"name": "@cid", "value": customer_id}],
    )
    print_query("query Customers by customerId", ru1, len(cust), n1, m1)

    recent, ru2, n2, m2 = _query(
        orders,
        (
            "SELECT TOP 5 * FROM c WHERE c.customerId = @cid "
            "ORDER BY c.orderDate DESC"
        ),
        [{"name": "@cid", "value": customer_id}],
    )
    print_query("cross-partition query on Orders", ru2, len(recent), n2, m2)
    print_ru("TOTAL", ru1 + ru2)


def p2_order_with_items(db, order_id: str, customer_id: str) -> None:
    print(f"\nP2 — Order {order_id} with line items")
    orders = db.get_container_client("Orders")
    items_c = db.get_container_client("OrderItems")

    header = orders.read_item(item=order_id, partition_key=order_id)
    ru1 = float(orders.client_connection.last_response_headers.get(
        "x-ms-request-charge", 0.0
    ))
    print_ru("point read Order header", ru1, 1)

    items, ru2, n2, m2 = _query(
        items_c,
        "SELECT * FROM c WHERE c.orderId = @oid",
        [{"name": "@oid", "value": order_id}],
        partition_key=order_id,
    )
    print_query("query OrderItems in partition", ru2, len(items), n2, m2)
    print_ru("TOTAL", ru1 + ru2)


def p3_place_order(db, customer_id: str) -> None:
    print(f"\nP3 — Place a new order for {customer_id}")
    orders = db.get_container_client("Orders")
    items_c = db.get_container_client("OrderItems")
    products = db.get_container_client("Products")

    # Grab a couple of products to put in the cart.
    cart_products, ru_q, n_q, m_q = _query(
        products,
        "SELECT TOP 3 c.productId, c.name, c.price FROM c",
    )
    print_query("cross-partition pick products", ru_q, len(cart_products), n_q, m_q)

    new_order_id = f"O{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    header = {
        "id": new_order_id,
        "orderId": new_order_id,
        "customerId": customer_id,
        "orderDate": datetime.now(timezone.utc).isoformat(),
        "status": "Placed",
        "totalAmount": round(sum(p["price"] * 2 for p in cart_products), 2),
        "lineCount": len(cart_products),
    }
    orders.create_item(header)
    ru_h = float(orders.client_connection.last_response_headers.get(
        "x-ms-request-charge", 0.0
    ))
    print_ru("create Order header", ru_h, 1)

    ru_items_total = 0.0
    for idx, prod in enumerate(cart_products, start=1):
        line_id = f"{new_order_id}-L{idx:02d}"
        items_c.create_item(
            {
                "id": line_id,
                "orderItemId": line_id,
                "orderId": new_order_id,
                "customerId": customer_id,
                "productId": prod["productId"],
                "productName": prod["name"],
                "quantity": 2,
                "unitPrice": prod["price"],
                "lineTotal": round(prod["price"] * 2, 2),
            }
        )
        ru_items_total += float(
            items_c.client_connection.last_response_headers.get(
                "x-ms-request-charge", 0.0
            )
        )
    print_ru(f"create {len(cart_products)} OrderItem rows", ru_items_total)
    print_ru("TOTAL (non-transactional!)", ru_q + ru_h + ru_items_total)


def p4_products_in_category(db, category_id: str) -> None:
    print(f"\nP4 — Products in category {category_id} (price ASC)")
    products = db.get_container_client("Products")
    rows, ru, n, m = _query(
        products,
        (
            "SELECT c.productId, c.name, c.price FROM c "
            "WHERE c.categoryId = @cid ORDER BY c.price ASC"
        ),
        [{"name": "@cid", "value": category_id}],
    )
    print_query("cross-partition query on Products", ru, len(rows), n, m)


def main() -> None:
    client = get_client()
    db = client.get_database_client(DATABASE_NAME)

    # Pick stable demo IDs that exist in the seeded data.
    sample_customer = "C00005"
    sample_order = "O0000001"
    sample_category = "CAT006"

    print("=" * 70)
    print("Iteration 1 — naive 5-container design")
    print("=" * 70)

    p1_customer_with_recent_orders(db, sample_customer)
    p2_order_with_items(db, sample_order, sample_customer)
    p3_place_order(db, sample_customer)
    p4_products_in_category(db, sample_category)


if __name__ == "__main__":
    main()

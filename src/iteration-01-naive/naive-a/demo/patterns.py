"""Iteration 1 access patterns — DEMO skeleton.

For each pattern, write the SQL/SDK calls the naive design forces you to
make, then read the RU charge off the response headers and print it.

Look at complete/patterns.py if you get stuck.
"""

from __future__ import annotations

from shared import DATABASE_NAME, get_client, print_query, print_ru


def p1_customer_with_recent_orders(db, customer_id: str) -> None:
    """Get the customer profile and their 5 most recent orders."""
    # TODO (demo):
    #   1. Query Customers WHERE customerId = @cid
    #   2. Query Orders WHERE customerId = @cid ORDER BY orderDate DESC, TOP 5
    #      (cross-partition — pass enable_cross_partition_query=True)
    #   3. Pass populate_query_metrics=True on every query_items call
    #   4. Read x-ms-request-charge, x-ms-item-count, and
    #      x-ms-documentdb-query-metrics from each response, then print
    #      with print_query(label, ru, client_count, server_count, metrics)
    print(f"\nP1 — Customer {customer_id} (not implemented)")


def p2_order_with_items(db, order_id: str, customer_id: str) -> None:
    """Get one order with its line items."""
    # TODO (demo):
    #   1. Point read on Orders (partition key = orderId)
    #   2. Query OrderItems WHERE orderId = @oid (partition key = orderId)
    print(f"\nP2 — Order {order_id} (not implemented)")


def p3_place_order(db, customer_id: str) -> None:
    """Place a new order: header + N line items, non-transactional."""
    # TODO (demo):
    #   1. Pick a few products (cross-partition query on Products — pass
    #      enable_cross_partition_query=True and populate_query_metrics=True)
    #   2. create_item on Orders for the header
    #   3. create_item on OrderItems for each line
    #   4. Notice there's no atomic transaction here. Why is that a problem?
    print(f"\nP3 — Place order for {customer_id} (not implemented)")


def p4_products_in_category(db, category_id: str) -> None:
    """List all products in a category, sorted by price ASC."""
    # TODO (demo):
    #   Query Products WHERE categoryId = @cid ORDER BY price ASC
    #   (Notice: Products is partitioned by /productId, so this is
    #    cross-partition — set enable_cross_partition_query=True and
    #    populate_query_metrics=True, then print with print_query.)
    print(f"\nP4 — Products in category {category_id} (not implemented)")


def main() -> None:
    client = get_client()
    db = client.get_database_client(DATABASE_NAME)

    sample_customer = "C00005"
    sample_order = "O0000001"
    sample_category = "CAT006"

    print("=" * 70)
    print("Iteration 1 — naive 5-container design (demo)")
    print("=" * 70)

    p1_customer_with_recent_orders(db, sample_customer)
    p2_order_with_items(db, sample_order, sample_customer)
    p3_place_order(db, sample_customer)
    p4_products_in_category(db, sample_category)


if __name__ == "__main__":
    main()

"""Migrate iteration-1's five containers into iteration-2's two containers.

Reads from:  Customers, Orders, OrderItems, Products, ProductCategories
Writes to:   CustomerOrders, Products

This script is here so you can demonstrate the schema move *in place* — the
agent guides you to the new layout, then this script proves the data can
be re-shaped without leaving Cosmos DB.

    python complete/migrate_from_01.py
"""

from __future__ import annotations

from collections import defaultdict

from azure.cosmos import PartitionKey

from app.repository import (
    CUSTOMER_ORDERS,
    DATABASE_NAME,
    PRODUCTS,
    get_client,
)


def main() -> None:
    client = get_client()
    db = client.get_database_client(DATABASE_NAME)

    src_customers = db.get_container_client("Customers")
    src_orders = db.get_container_client("Orders")
    src_items = db.get_container_client("OrderItems")
    src_products = db.get_container_client("Products")

    target_co = db.create_container_if_not_exists(
        id=CUSTOMER_ORDERS,
        partition_key=PartitionKey(path="/customerId"),
        offer_throughput=400,
    )
    target_products = db.create_container_if_not_exists(
        id=PRODUCTS,
        partition_key=PartitionKey(path="/categoryId"),
        offer_throughput=400,
    )

    # 1) collect items grouped by orderId so we can embed them
    items_by_order: dict[str, list[dict]] = defaultdict(list)
    for it in src_items.query_items(
        query="SELECT * FROM c", enable_cross_partition_query=True
    ):
        items_by_order[it["orderId"]].append(
            {
                "productId": it["productId"],
                "productName": it.get("productName"),
                "categoryId": it.get("categoryId"),
                "quantity": it["quantity"],
                "unitPrice": it["unitPrice"],
                "lineTotal": it["lineTotal"],
            }
        )

    # 2) build summaries per customer from orders
    orders_by_customer: dict[str, list[dict]] = defaultdict(list)
    for o in src_orders.query_items(
        query="SELECT * FROM c", enable_cross_partition_query=True
    ):
        orders_by_customer[o["customerId"]].append(o)

    # 3) write customer + order documents to CustomerOrders
    customer_count = 0
    order_count = 0
    for c in src_customers.query_items(
        query="SELECT * FROM c", enable_cross_partition_query=True
    ):
        cid = c["customerId"]
        cust_orders = orders_by_customer.get(cid, [])
        target_co.upsert_item(
            {
                "id": cid,
                "type": "customer",
                "customerId": cid,
                "firstName": c.get("firstName"),
                "lastName": c.get("lastName"),
                "emailAddress": c.get("emailAddress"),
                "phone": c.get("phone"),
                "companyName": c.get("companyName"),
                "orderSummary": {
                    "lifetimeOrders": len(cust_orders),
                    "lifetimeRevenue": round(
                        sum(o["totalAmount"] for o in cust_orders), 2
                    ),
                    "lastOrderDate": max(
                        (o["orderDate"] for o in cust_orders), default=None
                    ),
                },
            }
        )
        customer_count += 1
        for o in cust_orders:
            target_co.upsert_item(
                {
                    "id": o["orderId"],
                    "type": "order",
                    "customerId": cid,
                    "orderId": o["orderId"],
                    "orderDate": o["orderDate"],
                    "status": o.get("status"),
                    "totalAmount": o["totalAmount"],
                    "items": items_by_order.get(o["orderId"], []),
                }
            )
            order_count += 1

    # 4) products -> partitioned by /categoryId
    product_count = 0
    for p in src_products.query_items(
        query="SELECT * FROM c", enable_cross_partition_query=True
    ):
        target_products.upsert_item({"id": p["productId"], "type": "product", **p})
        product_count += 1

    print(
        f"Migrated: {customer_count} customers, {order_count} orders, "
        f"{product_count} products"
    )


if __name__ == "__main__":
    main()

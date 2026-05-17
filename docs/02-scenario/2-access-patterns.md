# 2. Access patterns

These are the four patterns the team supports today, plus the three new
ones that show up in production telemetry after iteration 2 ships. The
agent uses this list to recommend the iteration-2 schema in the demo.

| ID     | Pattern                                                              | Volume          | Latency budget | Notes                                |
|--------|----------------------------------------------------------------------|-----------------|----------------|--------------------------------------|
| **P1** | Get a customer and their 5 most recent orders                        | ~50 % of reads  | <100 ms        | Hot path on the order-history screen |
| **P2** | Get one order with its line items                                    | ~25 % of reads  | <100 ms        | Order-detail page                    |
| **P3** | Place a new order: order header + N line items                       | All writes      | <250 ms        | Must be atomic                       |
| **P4** | List all products in a category, sorted by price ASC                 | ~20 % of reads  | <200 ms        | Catalog browse                       |

## Extended access patterns (iteration 3 — optional)

Captured from production telemetry once iteration 2 is live. They are
in-partition queries (cheap) but their multi-column `ORDER BY` clauses
need composite indexes to stay efficient.

| ID         | Pattern                                                                                  | Composite index it needs                          |
|------------|------------------------------------------------------------------------------------------|---------------------------------------------------|
| **R-EXT-1**| Customer order history filtered by date range, most recent first                          | `CustomerOrders`: `[type ASC, orderDate DESC]`    |
| **R-EXT-2**| Open-orders dashboard: all orders in `Placed` status, most recent first (cross-partition) | `CustomerOrders`: `[status ASC, orderDate DESC]`  |
| **R-EXT-3**| Products in a category sorted by `rating DESC` then `price ASC`                           | `Products`:        `[rating DESC, price ASC]`     |

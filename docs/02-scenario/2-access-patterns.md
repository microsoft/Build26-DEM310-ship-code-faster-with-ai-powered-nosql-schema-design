# 2. Access patterns

These are the four patterns the team supports today, plus the three new
ones that show up in production telemetry once the redesign ships. The
agent uses this list as one of its primary inputs when recommending the
target schema in the demo.

| ID     | Pattern                                                              | Volume          | Latency budget | Notes                                |
|--------|----------------------------------------------------------------------|-----------------|----------------|--------------------------------------|
| **P1** | Get a customer and their 5 most recent orders                        | ~50 % of reads  | <100 ms        | Hot path on the order-history screen |
| **P2** | Get one order with its line items                                    | ~25 % of reads  | <100 ms        | Order-detail page                    |
| **P3** | Place a new order: order header + N line items                       | All writes      | <250 ms        | Must be atomic                       |
| **P4** | List all products in a category, sorted by price ASC                 | ~20 % of reads  | <200 ms        | Catalog browse                       |

## Extended access patterns (optional, post-launch)

Captured from production telemetry once the redesign is live. They show
up later in the demo as a follow-on optimization.

| ID         | Pattern                                                                                  |
|------------|------------------------------------------------------------------------------------------|
| **R-EXT-1**| Customer order history filtered by date range, most recent first                          |
| **R-EXT-2**| Open-orders dashboard: all orders in `Placed` status, most recent first (cross-customer)  |
| **R-EXT-3**| Products in a category sorted by `rating DESC` then `price ASC`                           |

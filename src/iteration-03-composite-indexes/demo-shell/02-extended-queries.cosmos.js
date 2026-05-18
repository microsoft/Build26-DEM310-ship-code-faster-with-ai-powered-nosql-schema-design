// =============================================================================
// Iteration 3 — 02-extended-queries.cosmos.js
//
// Runs the three extended access patterns from
// src/iteration-03-composite-indexes/complete/queries.py. Each block is
// independently runnable — paste, run, call out the printed RU charge.
//
// Run AFTER 01-apply-composite-indexes.cosmos.js so the composite indexes
// are in place; otherwise the queries fall back to in-memory sorts and
// the RU numbers will look closer to the un-indexed baseline.
// =============================================================================

const db = cosmos.database("Build26DEM310");

// -----------------------------------------------------------------------------
// R-EXT-1 — Customer order history by date range
//   In-partition (filter on /customerId). Composite [type ASC, orderDate DESC]
//   lets the index serve the ORDER BY directly.
// -----------------------------------------------------------------------------
console.log("\nR-EXT-1 — customer order history by date range");

const customerId = "C00005";
const now  = new Date();
const from = new Date(now.getTime() - 180 * 86400_000).toISOString();
const to   = now.toISOString();

const r1 = await db
  .container("CustomerOrders")
  .items.query({
    query:
      "SELECT c.orderId, c.orderDate, c.totalAmount FROM c " +
      "WHERE c.type = 'order' AND c.customerId = @cid " +
      "AND c.orderDate >= @from AND c.orderDate < @to " +
      "ORDER BY c.orderDate DESC",
    parameters: [
      { name: "@cid",  value: customerId },
      { name: "@from", value: from       },
      { name: "@to",   value: to         },
    ],
    partitionKey: customerId,
  })
  .fetchAll();
console.log(`orders for ${customerId} (last 180d, DESC):`,
            r1.resources.length, "doc(s), RU:", r1.requestCharge);


// -----------------------------------------------------------------------------
// R-EXT-2 — Open-orders dashboard (cross-partition by design)
//   No /customerId filter. Composite [status ASC, orderDate DESC] removes
//   the in-memory sort that otherwise dominates the cost.
// -----------------------------------------------------------------------------
console.log("\nR-EXT-2 — open-orders dashboard");

const r2 = await db
  .container("CustomerOrders")
  .items.query({
    query:
      "SELECT TOP 25 c.orderId, c.customerId, c.orderDate, c.totalAmount " +
      "FROM c WHERE c.type = 'order' AND c.status = @s " +
      "ORDER BY c.orderDate DESC",
    parameters: [{ name: "@s", value: "Placed" }],
  })
  .fetchAll();
console.log("top-25 Placed orders DESC:",
            r2.resources.length, "doc(s), RU:", r2.requestCharge);


// -----------------------------------------------------------------------------
// R-EXT-3 — Products by rating DESC, price ASC inside a category
//   In-partition (filter on /categoryId). Composite [rating DESC, price ASC]
//   serves the two-column ORDER BY without a sort step.
// -----------------------------------------------------------------------------
console.log("\nR-EXT-3 — products by rating DESC, price ASC");

const categoryId = "CAT006";
const r3 = await db
  .container("Products")
  .items.query({
    query:
      "SELECT c.productId, c.name, c.rating, c.price FROM c " +
      "WHERE c.categoryId = @cid " +
      "ORDER BY c.rating DESC, c.price ASC",
    parameters: [{ name: "@cid", value: categoryId }],
    partitionKey: categoryId,
  })
  .fetchAll();
console.log(`products in ${categoryId} by rating/price:`,
            r3.resources.length, "doc(s), RU:", r3.requestCharge);


// -----------------------------------------------------------------------------
// Talking points
//   * Before the policy upgrade these three queries spend most of their RU
//     on a server-side sort. After it, the composite index pre-sorts the
//     candidates and the queries become "scan -> emit".
//   * R-EXT-2 stays cross-partition on purpose — that's the cost of an
//     admin "show me everything Placed" view. The composite index keeps
//     the per-partition work small.
//   * Re-run with the old policy to see the delta, or compare against the
//     numbers in src/iteration-03-composite-indexes/complete/queries.py.
// -----------------------------------------------------------------------------

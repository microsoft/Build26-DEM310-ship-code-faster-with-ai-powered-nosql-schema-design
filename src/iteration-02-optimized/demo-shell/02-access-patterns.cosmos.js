// =============================================================================
// Iteration 2 — 02-access-patterns.cosmos.js
//
// Manual demo of P1–P4 against the optimized two-container layout.
// Compare each block's RU charge with the iteration-1 (naive-a) equivalents.
// =============================================================================

const db = cosmos.database("Build26DEM310");

const customerId = "C00005";
const orderId    = "O0000001";
const categoryId = "CAT006";

// -----------------------------------------------------------------------------
// P1 — Customer profile + 5 most recent orders
//   SINGLE partition query: customer doc and all order docs share the
//   /customerId partition. No fan-out.
// -----------------------------------------------------------------------------
console.log(`\nP1 — Customer ${customerId} + 5 most recent orders`);

const p1 = await db
  .container("CustomerOrders")
  .items.query({
    query: "SELECT TOP 5 * FROM c WHERE c.customerId = @cid " +
           "AND c.type = 'order' ORDER BY c.orderDate DESC",
    parameters: [{ name: "@cid", value: customerId }],
    partitionKey: customerId,
  })
  .fetchAll();
console.log("Recent orders (single partition):", p1.resources.length, "doc(s),",
            "RU:", p1.requestCharge);


// -----------------------------------------------------------------------------
// P2 — One order with its line items
//   POINT READ. Items are embedded — no second container, no second hop.
// -----------------------------------------------------------------------------
console.log(`\nP2 — Order ${orderId} with embedded line items`);

const p2 = await db
  .container("CustomerOrders")
  .item(orderId, customerId)
  .read();
console.log("Point read (items embedded), RU:", p2.requestCharge,
            ", item count:", (p2.resource?.items?.length ?? 0));


// -----------------------------------------------------------------------------
// P3 — Place a new order, atomically
//   `execute_item_batch` updates the customer summary AND creates the order
//   doc in ONE transactional batch (same /customerId partition).
// -----------------------------------------------------------------------------
console.log(`\nP3 — Place a new order for ${customerId} (transactional batch)`);

// Pick a few products from the requested category — single partition because
// Products is partitioned by /categoryId.
const picks = await db
  .container("Products")
  .items.query({
    query: "SELECT TOP 3 c.productId, c.name, c.categoryId, c.price FROM c " +
           "WHERE c.categoryId = @cid",
    parameters: [{ name: "@cid", value: categoryId }],
    partitionKey: categoryId,
  })
  .fetchAll();
console.log("Picks (single partition):", picks.resources.length, "doc(s),",
            "RU:", picks.requestCharge);

const items = picks.resources.map(p => ({
  productId: p.productId,
  productName: p.name,
  categoryId: p.categoryId,
  quantity: 2,
  unitPrice: p.price,
  lineTotal: Math.round(p.price * 2 * 100) / 100,
}));
const total = Math.round(items.reduce((s, it) => s + it.lineTotal, 0) * 100) / 100;

// Read the existing customer doc so we can roll up the summary.
const existing = await db
  .container("CustomerOrders")
  .item(customerId, customerId)
  .read();
const customerDoc = existing.resource;
const summary = customerDoc.orderSummary || { lifetimeOrders: 0, lifetimeRevenue: 0, lastOrderDate: null };
const now = new Date().toISOString();

customerDoc.orderSummary = {
  lifetimeOrders: (summary.lifetimeOrders || 0) + 1,
  lifetimeRevenue: Math.round(((summary.lifetimeRevenue || 0) + total) * 100) / 100,
  lastOrderDate: now,
};

const newOrderId = "O" + now.replace(/[-:.TZ]/g, "").slice(0, 14);
const orderDoc = {
  id: newOrderId,
  type: "order",
  orderId: newOrderId,
  customerId: customerId,
  orderDate: now,
  status: "Placed",
  totalAmount: total,
  items: items,
};

const batch = await db
  .container("CustomerOrders")
  .items.batch(
    [
      { operationType: "Upsert", resourceBody: customerDoc },
      { operationType: "Create", resourceBody: orderDoc   },
    ],
    customerId   // partition key for the whole batch
  );
console.log("Transactional batch (customer + order), RU:", batch.requestCharge,
            ", statusCode:", batch.statusCode);


// -----------------------------------------------------------------------------
// P4 — Products in a category, ordered by price ASC
//   SINGLE partition query — Products is partitioned by /categoryId.
// -----------------------------------------------------------------------------
console.log(`\nP4 — Products in category ${categoryId} (price ASC)`);

const p4 = await db
  .container("Products")
  .items.query({
    query: "SELECT c.productId, c.name, c.price, c.rating FROM c " +
           "WHERE c.categoryId = @cid ORDER BY c.price ASC",
    parameters: [{ name: "@cid", value: categoryId }],
    partitionKey: categoryId,
  })
  .fetchAll();
console.log("Products (single partition):", p4.resources.length, "doc(s),",
            "RU:", p4.requestCharge);


// -----------------------------------------------------------------------------
// Talking points
//   * P1 is single-partition because the PK now matches the access pattern.
//   * P2 is one point read — items live on the order doc.
//   * P3 is atomic — both writes go to the same /customerId partition.
//   * P4 is single-partition because Products' PK is /categoryId, not /productId.
//   * Iteration 3 (next) keeps the same shape but adds composite indexes so
//     the ORDER BY in P1/P4 stops scanning beyond what it returns.
// -----------------------------------------------------------------------------

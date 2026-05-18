// =============================================================================
// Iteration 1 (naive-a) — 02-access-patterns.cosmos.js
//
// Manual demo script. Each block is independently runnable in the
// Cosmos DB Shell. After every query the shell prints `x-ms-request-charge`
// in the response headers — that's the RU number to call out on stage.
//
// The patterns mirror src/iteration-01-naive/naive-a/complete/patterns.py
// so the audience can compare what the shell sees vs. what the Python
// service does.
// =============================================================================

const db = cosmos.database("Build26DEM310DB-i1a");

const customerId = "C00005";
const orderId    = "O0000001";
const categoryId = "CAT006";

// -----------------------------------------------------------------------------
// P1 — Customer profile + 5 most recent orders
//   2 round-trips, the Orders query is cross-partition (Orders is
//   partitioned by /orderId, not /customerId).
// -----------------------------------------------------------------------------
console.log(`\nP1 — Customer ${customerId} + 5 most recent orders`);

const p1Customer = await db
  .container("Customers")
  .items.query({
    query: "SELECT * FROM c WHERE c.customerId = @cid",
    parameters: [{ name: "@cid", value: customerId }],
  })
  .fetchAll();
console.log("Customers:", p1Customer.resources.length, "doc(s),",
            "RU:", p1Customer.requestCharge);

const p1Orders = await db
  .container("Orders")
  .items.query({
    query: "SELECT TOP 5 * FROM c WHERE c.customerId = @cid " +
           "ORDER BY c.orderDate DESC",
    parameters: [{ name: "@cid", value: customerId }],
  })
  .fetchAll();   // cross-partition: Orders is PK'd on /orderId
console.log("Orders (cross-partition):", p1Orders.resources.length, "doc(s),",
            "RU:", p1Orders.requestCharge);


// -----------------------------------------------------------------------------
// P2 — One order with its line items
//   1 point read + 1 single-partition query (OrderItems PK'd on /orderId).
// -----------------------------------------------------------------------------
console.log(`\nP2 — Order ${orderId} with line items`);

const p2Header = await db
  .container("Orders")
  .item(orderId, orderId)
  .read();
console.log("Order header point read, RU:", p2Header.requestCharge);

const p2Items = await db
  .container("OrderItems")
  .items.query({
    query: "SELECT * FROM c WHERE c.orderId = @oid",
    parameters: [{ name: "@oid", value: orderId }],
    partitionKey: orderId,
  })
  .fetchAll();
console.log("OrderItems in partition:", p2Items.resources.length, "doc(s),",
            "RU:", p2Items.requestCharge);


// -----------------------------------------------------------------------------
// P3 — Place a new order
//   3 writes spanning TWO containers (Orders + OrderItems). There is no way
//   to commit them atomically — a crash between them leaves a half-placed
//   order. This is the headline anti-pattern of iteration 1.
// -----------------------------------------------------------------------------
console.log(`\nP3 — Place a new order for ${customerId}`);

const cart = await db
  .container("Products")
  .items.query({
    query: "SELECT TOP 3 c.productId, c.name, c.price FROM c",
  })
  .fetchAll();   // cross-partition pick from Products (PK'd on /productId)
console.log("Cart picks (cross-partition):", cart.resources.length, "doc(s),",
            "RU:", cart.requestCharge);

const newOrderId = "O" + new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
const header = {
  id: newOrderId,
  orderId: newOrderId,
  customerId: customerId,
  orderDate: new Date().toISOString(),
  status: "Placed",
  totalAmount: Math.round(cart.resources.reduce((s, p) => s + p.price * 2, 0) * 100) / 100,
  lineCount: cart.resources.length,
};
const p3Header = await db.container("Orders").items.create(header);
console.log("Create Order header, RU:", p3Header.requestCharge);

let p3ItemsRu = 0;
for (let i = 0; i < cart.resources.length; i++) {
  const p = cart.resources[i];
  const lineId = `${newOrderId}-L${String(i + 1).padStart(2, "0")}`;
  const res = await db.container("OrderItems").items.create({
    id: lineId,
    orderItemId: lineId,
    orderId: newOrderId,
    customerId: customerId,
    productId: p.productId,
    productName: p.name,
    quantity: 2,
    unitPrice: p.price,
    lineTotal: Math.round(p.price * 2 * 100) / 100,
  });
  p3ItemsRu += res.requestCharge;
}
console.log(`Create ${cart.resources.length} OrderItem rows, RU:`, p3ItemsRu);
console.log("⚠️  Two-container write — NOT atomic. Talk about it.");


// -----------------------------------------------------------------------------
// P4 — Products in a category, ordered by price ASC
//   Cross-partition fan-out because Products is PK'd on /productId, not
//   /categoryId. The "obvious" relational key is the wrong choice here.
// -----------------------------------------------------------------------------
console.log(`\nP4 — Products in category ${categoryId} (price ASC)`);

const p4 = await db
  .container("Products")
  .items.query({
    query: "SELECT c.productId, c.name, c.price FROM c " +
           "WHERE c.categoryId = @cid ORDER BY c.price ASC",
    parameters: [{ name: "@cid", value: categoryId }],
  })
  .fetchAll();
console.log("Products (cross-partition):", p4.resources.length, "doc(s),",
            "RU:", p4.requestCharge);


// -----------------------------------------------------------------------------
// Talking points
//   * P1 + P4 are cross-partition because the PK choice was "the row's own id"
//     instead of "what we query by".
//   * P3 is non-transactional — two containers means no batch.
//   * Compare these RU numbers with iteration 2's `02-access-patterns.cosmos.js`.
// -----------------------------------------------------------------------------

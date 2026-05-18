// =============================================================================
// Iteration 2 — 01-setup.cosmos.js
//
// Creates database `Build26DEM310DB-i2` with TWO containers:
//
//   CustomerOrders  /customerId   — customer docs AND order docs share the
//                                   same partition; a single `type` field
//                                   distinguishes them. Items are embedded
//                                   on the order doc.
//   Products        /categoryId   — products partitioned by category so the
//                                   "products in category" query is single-
//                                   partition.
//
// The indexing policy is tightened: only the paths we actually filter or
// sort on are indexed. Everything else (including the giant `items[]`
// array) is excluded.
// =============================================================================

const DB_NAME = "Build26DEM310DB-i2";

await cosmos.databases.createIfNotExists({ id: DB_NAME });
const db = cosmos.database(DB_NAME);

const indexingPolicy = {
  indexingMode: "consistent",
  automatic: true,
  includedPaths: [
    { path: "/customerId/?" },
    { path: "/type/?" },
    { path: "/orderDate/?" },
    { path: "/status/?" },
    { path: "/categoryId/?" },
    { path: "/price/?" },
    { path: "/rating/?" }
  ],
  excludedPaths: [
    { path: "/*" },
    { path: "/items/*" },
    { path: "/\"_etag\"/?" }
  ],
  compositeIndexes: []
};

await db.containers.createIfNotExists({
  id: "CustomerOrders",
  partitionKey: { paths: ["/customerId"] },
  indexingPolicy: indexingPolicy,
  throughput: 400
});
console.log("container ready: CustomerOrders (pk=/customerId)");

await db.containers.createIfNotExists({
  id: "Products",
  partitionKey: { paths: ["/categoryId"] },
  indexingPolicy: indexingPolicy,
  throughput: 400
});
console.log("container ready: Products (pk=/categoryId)");

// -----------------------------------------------------------------------------
// Seed
// -----------------------------------------------------------------------------
const customerOrders = require("./seed-data/CustomerOrders.json");
for (const doc of customerOrders) {
  await db.container("CustomerOrders").items.upsert(doc);
}
console.log(`seeded CustomerOrders: ${customerOrders.length} docs ` +
            "(customers + orders, type-discriminated)");

const products = require("./seed-data/Products.json");
for (const doc of products) {
  await db.container("Products").items.upsert(doc);
}
console.log(`seeded Products: ${products.length} docs`);

console.log("\nIteration 2 setup complete.");
console.log("Next: 02-access-patterns.cosmos.js");

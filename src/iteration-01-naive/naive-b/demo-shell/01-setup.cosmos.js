// =============================================================================
// Iteration 1 (naive-b) — 01-setup.cosmos.js
//
// Creates one container with an empty `orders[]` array on each customer doc.
// 03-simulate-unbounded-growth.cosmos.js will append synthetic orders into
// that array, iteration by iteration, until you can see the doc grow
// without bound — the anti-pattern the demo is calling out.
// =============================================================================

const DB_NAME = "Build26DEM310DB-i1b";
const CONTAINER = "CustomersWithEmbeddedOrders";

await cosmos.databases.createIfNotExists({ id: DB_NAME });
const db = cosmos.database(DB_NAME);

// Drop and recreate so the growth simulation is deterministic.
try {
  await db.container(CONTAINER).delete();
  console.log(`dropped existing ${CONTAINER}`);
} catch (_) { /* not found is fine */ }

await db.containers.create({
  id: CONTAINER,
  partitionKey: { paths: ["/customerId"] },
  // Default indexing — the point of this iteration is the DOC SHAPE,
  // not the index policy.
  indexingPolicy: {
    indexingMode: "consistent",
    automatic: true,
    includedPaths: [{ path: "/*" }],
    excludedPaths: [{ path: "/\"_etag\"/?" }]
  },
  throughput: 400
});
console.log(`created ${CONTAINER} (pk=/customerId)`);

// Seed the customer documents with an empty orders[] array.
const customers = require("./seed-data/CustomersWithEmbeddedOrders.json");
for (const doc of customers) {
  await db.container(CONTAINER).items.upsert(doc);
}
console.log(`seeded ${customers.length} customer docs with orders[] = []`);

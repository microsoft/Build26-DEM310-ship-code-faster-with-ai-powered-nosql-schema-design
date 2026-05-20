// =============================================================================
// Iteration 1 (naive-a) — 01-setup.cosmos.js
//
// Run inside the **Cosmos DB Shell** (Visual Studio Code → Cosmos DB extension
// → "Open in Cosmos DB Shell"). Connects to whichever account/emulator the
// shell is attached to.
//
// Creates: database `Build26DEM310DB-i1a` with five relational-style containers,
// each partitioned by the obvious "id" column and using the default indexing
// policy (everything indexed).
// =============================================================================

const DB_NAME = "Build26DEM310DB-i1a";

await cosmos.databases.createIfNotExists({ id: DB_NAME });
const db = cosmos.database(DB_NAME);

const containers = [
  { id: "Customers",         partitionKey: { paths: ["/customerId"] } },
  { id: "Orders",            partitionKey: { paths: ["/orderId"]    } },
  { id: "OrderItems",        partitionKey: { paths: ["/orderId"]    } },
  { id: "Products",          partitionKey: { paths: ["/productId"]  } },
  { id: "ProductCategories", partitionKey: { paths: ["/categoryId"] } },
];

// Default ("naive") indexing policy: index everything, no excludes,
// no composite indexes. This is exactly what makes iteration 1 expensive.
const defaultIndexingPolicy = {
  indexingMode: "consistent",
  automatic: true,
  includedPaths: [{ path: "/*" }],
  excludedPaths: [{ path: "/\"_etag\"/?" }]
};

for (const c of containers) {
  await db.containers.createIfNotExists({
    id: c.id,
    partitionKey: c.partitionKey,
    indexingPolicy: defaultIndexingPolicy,
    throughput: 400
  });
  console.log(`container ready: ${c.id}  (pk=${c.partitionKey.paths[0]})`);
}

// -----------------------------------------------------------------------------
// Seed the containers from seed-data/*.json.
//
// The Cosmos DB Shell exposes Node-style `require` for files in the workspace.
// If your shell flavour does not support it, run
// `python -u -m scripts.seed_iteration_01_naive_a` from the repo root
// instead — it reads the same JSON and upserts via the azure-cosmos SDK.
// -----------------------------------------------------------------------------
const seed = {
  Customers:         require("./seed-data/Customers.json"),
  ProductCategories: require("./seed-data/ProductCategories.json"),
  Products:          require("./seed-data/Products.json"),
  Orders:            require("./seed-data/Orders.json"),
  OrderItems:        require("./seed-data/OrderItems.json"),
};

for (const [name, docs] of Object.entries(seed)) {
  const container = db.container(name);
  for (const doc of docs) {
    await container.items.upsert(doc);
  }
  console.log(`seeded ${name}: ${docs.length} docs`);
}

console.log("\nIteration 1 (naive-a) setup complete.");
console.log("Next: 02-access-patterns.cosmos.js");

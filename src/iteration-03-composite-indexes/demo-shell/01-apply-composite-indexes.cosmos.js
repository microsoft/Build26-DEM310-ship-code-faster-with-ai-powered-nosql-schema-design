// =============================================================================
// Iteration 3 — 01-apply-composite-indexes.cosmos.js
//
// Iteration 3 keeps the iteration-2 container layout (CustomerOrders +
// Products) and only **upgrades the indexing policy** to add the composite
// indexes needed for the three extended access patterns:
//
//   R-EXT-1 — customer order history by date range
//             needs [type ASC, orderDate DESC] on CustomerOrders
//   R-EXT-2 — open-orders dashboard across all customers
//             needs [status ASC, orderDate DESC] on CustomerOrders
//   R-EXT-3 — products by rating DESC, price ASC inside a category
//             needs [rating DESC, price ASC] on Products
//
// Prerequisite: iteration-2 setup has already run. If not, paste
// ../../iteration-02-optimized/demo-shell/01-setup.cosmos.js first.
//
// Replacing the policy triggers a background index rebuild — wait a few
// seconds before running 02-extended-queries.cosmos.js so the composites
// are usable.
// =============================================================================

const db = cosmos.database("Build26DEM310DB-i3");

const customerOrdersPolicy = {
  indexingMode: "consistent",
  automatic: true,
  includedPaths: [
    { path: "/customerId/?" },
    { path: "/type/?" },
    { path: "/orderDate/?" },
    { path: "/status/?" }
  ],
  excludedPaths: [
    { path: "/items/*" },
    { path: "/\"_etag\"/?" }
  ],
  compositeIndexes: [
    [
      { path: "/type",      order: "ascending"  },
      { path: "/orderDate", order: "descending" }
    ],
    [
      { path: "/status",    order: "ascending"  },
      { path: "/orderDate", order: "descending" }
    ]
  ]
};

const productsPolicy = {
  indexingMode: "consistent",
  automatic: true,
  includedPaths: [
    { path: "/categoryId/?" },
    { path: "/price/?" },
    { path: "/rating/?" }
  ],
  excludedPaths: [
    { path: "/\"_etag\"/?" }
  ],
  compositeIndexes: [
    [
      { path: "/rating", order: "descending" },
      { path: "/price",  order: "ascending"  }
    ]
  ]
};

// Replace the policy on each container in place. The Cosmos DB Shell
// surfaces this as `replace` on the container resource.
const coContainer = db.container("CustomerOrders");
const coProps = (await coContainer.read()).resource;
coProps.indexingPolicy = customerOrdersPolicy;
await coContainer.replace(coProps);
console.log(`updated CustomerOrders: ${customerOrdersPolicy.compositeIndexes.length} composite index(es)`);

const prContainer = db.container("Products");
const prProps = (await prContainer.read()).resource;
prProps.indexingPolicy = productsPolicy;
await prContainer.replace(prProps);
console.log(`updated Products: ${productsPolicy.compositeIndexes.length} composite index(es)`);

console.log("\nGive the indexer a few seconds to rebuild, then run");
console.log("02-extended-queries.cosmos.js");

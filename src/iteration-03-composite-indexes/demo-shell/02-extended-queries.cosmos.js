// =============================================================================
// Iteration 3 — 02-extended-queries.cosmos.js
//
// Runs the three extended access patterns from
// src/iteration-03-composite-indexes/complete/queries.py with index metrics
// enabled. Each block is independently runnable — paste, run, then call
// out the printed RU charge **and** the index-utilization summary.
//
// Run AFTER 01-apply-composite-indexes.cosmos.js so the composite indexes
// are in place; otherwise the queries fall back to in-memory sorts and
// the index-metrics output will show the composite as "not utilized".
//
// For a full before/after sweep in a single paste, see
// 03-scenario-before-after.cosmos.js.
// =============================================================================

const db = cosmos.database("Build26DEM310DB-i3");

// -----------------------------------------------------------------------------
// Helper — run a query with index metrics on and pretty-print the result.
//
// `populateIndexMetrics: true` asks the gateway to return an
// `indexMetrics` string describing which indexes were considered, which
// were utilized, and the impact of each. We surface the raw string so
// attendees can see exactly what the engine picked.
// -----------------------------------------------------------------------------
async function runWithMetrics(label, container, spec, options) {
  const opts = Object.assign({ populateIndexMetrics: true }, options || {});
  const res  = await db.container(container).items.query(spec, opts).fetchAll();

  const utilized = /Utilized Composite Indexes\s*[\r\n]+\s*([^\r\n]*)/i.exec(
    res.indexMetrics || ""
  );

  console.log(`\n${label}`);
  console.log(`  docs: ${res.resources.length}   RU: ${res.requestCharge.toFixed(2)}`);
  console.log(`  composite utilized: ${utilized && utilized[1].trim() ? utilized[1].trim() : "(none)"}`);
  if (res.indexMetrics) {
    console.log("  --- indexMetrics ---");
    console.log(res.indexMetrics.split("\n").map((l) => "  " + l).join("\n"));
  } else {
    console.log("  (no indexMetrics returned — shell flavour may not surface them)");
  }
  return res;
}

// -----------------------------------------------------------------------------
// R-EXT-1 — Customer order history by date range
//   In-partition (filter on /customerId). Composite [type ASC, orderDate DESC]
//   lets the index serve the ORDER BY directly.
// -----------------------------------------------------------------------------
const customerId = "C00005";
const now  = new Date();
const from = new Date(now.getTime() - 180 * 86400_000).toISOString();
const to   = now.toISOString();

await runWithMetrics(
  "R-EXT-1 — customer order history by date range",
  "CustomerOrders",
  {
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
  },
  { partitionKey: customerId }
);


// -----------------------------------------------------------------------------
// R-EXT-2 — Open-orders dashboard (cross-partition by design)
//   No /customerId filter. Composite [status ASC, orderDate DESC] removes
//   the in-memory sort that otherwise dominates the cost.
// -----------------------------------------------------------------------------
await runWithMetrics(
  "R-EXT-2 — open-orders dashboard (cross-partition)",
  "CustomerOrders",
  {
    query:
      "SELECT TOP 25 c.orderId, c.customerId, c.orderDate, c.totalAmount " +
      "FROM c WHERE c.type = 'order' AND c.status = @s " +
      "ORDER BY c.orderDate DESC",
    parameters: [{ name: "@s", value: "Placed" }],
  }
);


// -----------------------------------------------------------------------------
// R-EXT-3 — Products by rating DESC, price ASC inside a category
//   In-partition (filter on /categoryId). Composite [rating DESC, price ASC]
//   serves the two-column ORDER BY without a sort step.
// -----------------------------------------------------------------------------
const categoryId = "CAT006";
await runWithMetrics(
  "R-EXT-3 — products by rating DESC, price ASC",
  "Products",
  {
    query:
      "SELECT c.productId, c.name, c.rating, c.price FROM c " +
      "WHERE c.categoryId = @cid " +
      "ORDER BY c.rating DESC, c.price ASC",
    parameters: [{ name: "@cid", value: categoryId }],
  },
  { partitionKey: categoryId }
);


// -----------------------------------------------------------------------------
// Talking points
//   * `indexMetrics` lists "Utilized Single Indexes" and "Utilized Composite
//     Indexes". Before the policy upgrade the composite section is empty
//     and the RU charge includes a server-side sort step.
//   * After 01-apply-composite-indexes.cosmos.js runs, the composite block
//     shows the exact `[path ORDER, path ORDER]` pair the engine picked
//     and the RU drops.
//   * R-EXT-2 stays cross-partition on purpose — that's the cost of an
//     admin "show me everything Placed" view. The composite index keeps
//     the per-partition work small.
//   * For a side-by-side baseline vs composite run with a diff table,
//     paste 03-scenario-before-after.cosmos.js instead.
// -----------------------------------------------------------------------------

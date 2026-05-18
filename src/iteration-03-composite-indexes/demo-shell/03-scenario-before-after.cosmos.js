// =============================================================================
// Iteration 3 — 03-scenario-before-after.cosmos.js
//
// Self-contained "what do composite indexes actually buy us?" simulation.
//
// Flow (paste-and-run as a single block):
//   1. Force CustomerOrders + Products back to the **iteration-2 baseline
//      policy** (no compositeIndexes). Wait briefly for the indexer.
//   2. Run R-EXT-1 / R-EXT-2 / R-EXT-3 with `populateIndexMetrics: true`
//      and capture RU + indexMetrics. This is the "before" pass.
//   3. Apply the **iteration-3 composite policy** to both containers.
//      Wait briefly for the indexer.
//   4. Re-run the same three queries. This is the "after" pass.
//   5. Print a side-by-side table: RU before / RU after / delta / composite
//      that the engine reports as utilized.
//
// Prerequisites:
//   * iteration-2 data is seeded (run
//     ../../iteration-02-optimized/demo-shell/01-setup.cosmos.js first).
//   * The shell is in `Build26DEM310DB-i3`.
//
// Re-runnable — it always resets to baseline before the "before" pass,
// so the comparison is honest no matter what the policy looked like.
// =============================================================================

const db = cosmos.database("Build26DEM310DB-i3");

// -----------------------------------------------------------------------------
// Policies — baseline (iteration-2) and composite (iteration-3).
// Keep both definitions next to each other so the audience can diff them
// visually on the slide.
// -----------------------------------------------------------------------------
const baselineCustomerOrders = {
  indexingMode: "consistent",
  automatic: true,
  includedPaths: [
    { path: "/customerId/?" },
    { path: "/type/?" },
    { path: "/orderDate/?" },
    { path: "/status/?" },
  ],
  excludedPaths: [
    { path: "/items/*" },
    { path: "/\"_etag\"/?" },
  ],
  compositeIndexes: [],
};

const baselineProducts = {
  indexingMode: "consistent",
  automatic: true,
  includedPaths: [
    { path: "/categoryId/?" },
    { path: "/price/?" },
    { path: "/rating/?" },
  ],
  excludedPaths: [
    { path: "/\"_etag\"/?" },
  ],
  compositeIndexes: [],
};

const compositeCustomerOrders = Object.assign({}, baselineCustomerOrders, {
  compositeIndexes: [
    [
      { path: "/type",      order: "ascending"  },
      { path: "/orderDate", order: "descending" },
    ],
    [
      { path: "/status",    order: "ascending"  },
      { path: "/orderDate", order: "descending" },
    ],
  ],
});

const compositeProducts = Object.assign({}, baselineProducts, {
  compositeIndexes: [
    [
      { path: "/rating", order: "descending" },
      { path: "/price",  order: "ascending"  },
    ],
  ],
});

// -----------------------------------------------------------------------------
// Replace the indexing policy on a container in place. Returns the new
// container properties so the caller can confirm the change landed.
// -----------------------------------------------------------------------------
async function setPolicy(containerName, policy) {
  const c     = db.container(containerName);
  const props = (await c.read()).resource;
  props.indexingPolicy = policy;
  await c.replace(props);
  console.log(
    `  ${containerName}: composites=${policy.compositeIndexes.length}`
  );
}

// -----------------------------------------------------------------------------
// Wait `seconds` for the indexer to catch up after a policy change. Cosmos
// rebuilds in the background; the queries still succeed during the rebuild
// but their RU/indexMetrics may be partially old until it finishes.
// -----------------------------------------------------------------------------
async function waitForIndexer(seconds) {
  console.log(`  waiting ${seconds}s for indexer rebuild...`);
  await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

// -----------------------------------------------------------------------------
// Run one query with index metrics on and return a compact summary record.
// We parse the "Utilized Composite Indexes" line out of `indexMetrics` so
// the comparison table can show, per pattern, *which* composite the
// engine picked (or "(none)" when the policy doesn't have one).
// -----------------------------------------------------------------------------
async function runOne(container, spec, options) {
  const opts = Object.assign({ populateIndexMetrics: true }, options || {});
  const res  = await db.container(container).items.query(spec, opts).fetchAll();
  const m    = /Utilized Composite Indexes\s*[\r\n]+\s*([^\r\n]*)/i.exec(
    res.indexMetrics || ""
  );
  return {
    ru:         res.requestCharge,
    docs:       res.resources.length,
    composite:  m && m[1].trim() ? m[1].trim() : "(none)",
    metrics:    res.indexMetrics || "",
  };
}

// -----------------------------------------------------------------------------
// Query specs — the same three patterns runWithMetrics uses in 02-...
// Defined once so "before" and "after" run literally the same SQL.
// -----------------------------------------------------------------------------
const customerId = "C00005";
const categoryId = "CAT006";
const now  = new Date();
const from = new Date(now.getTime() - 180 * 86400_000).toISOString();
const to   = now.toISOString();

const patterns = [
  {
    label:     "R-EXT-1 — customer order history (in-partition)",
    container: "CustomerOrders",
    spec: {
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
    options: { partitionKey: customerId },
  },
  {
    label:     "R-EXT-2 — open-orders dashboard (cross-partition)",
    container: "CustomerOrders",
    spec: {
      query:
        "SELECT TOP 25 c.orderId, c.customerId, c.orderDate, c.totalAmount " +
        "FROM c WHERE c.type = 'order' AND c.status = @s " +
        "ORDER BY c.orderDate DESC",
      parameters: [{ name: "@s", value: "Placed" }],
    },
    options: {},
  },
  {
    label:     "R-EXT-3 — products by rating DESC, price ASC (in-partition)",
    container: "Products",
    spec: {
      query:
        "SELECT c.productId, c.name, c.rating, c.price FROM c " +
        "WHERE c.categoryId = @cid " +
        "ORDER BY c.rating DESC, c.price ASC",
      parameters: [{ name: "@cid", value: categoryId }],
    },
    options: { partitionKey: categoryId },
  },
];

// -----------------------------------------------------------------------------
// Phase 1 — reset to baseline policy.
// -----------------------------------------------------------------------------
console.log("\n=== STEP 1: Reset to iteration-2 baseline policy ===");
await setPolicy("CustomerOrders", baselineCustomerOrders);
await setPolicy("Products",       baselineProducts);
await waitForIndexer(8);

// -----------------------------------------------------------------------------
// Phase 2 — "before" pass. Capture per-pattern RU + indexMetrics summary.
// -----------------------------------------------------------------------------
console.log("\n=== STEP 2: Run queries with BASELINE indexes ===");
const before = [];
for (const p of patterns) {
  const r = await runOne(p.container, p.spec, p.options);
  console.log(
    `  ${p.label}\n    RU=${r.ru.toFixed(2)}  composite=${r.composite}  docs=${r.docs}`
  );
  before.push(r);
}

// -----------------------------------------------------------------------------
// Phase 3 — apply composite policy.
// -----------------------------------------------------------------------------
console.log("\n=== STEP 3: Apply iteration-3 composite policy ===");
await setPolicy("CustomerOrders", compositeCustomerOrders);
await setPolicy("Products",       compositeProducts);
await waitForIndexer(15);

// -----------------------------------------------------------------------------
// Phase 4 — "after" pass.
// -----------------------------------------------------------------------------
console.log("\n=== STEP 4: Re-run queries with COMPOSITE indexes ===");
const after = [];
for (const p of patterns) {
  const r = await runOne(p.container, p.spec, p.options);
  console.log(
    `  ${p.label}\n    RU=${r.ru.toFixed(2)}  composite=${r.composite}  docs=${r.docs}`
  );
  after.push(r);
}

// -----------------------------------------------------------------------------
// Phase 5 — side-by-side diff. The "delta %" column is the headline number
// for the iteration-3 slide.
// -----------------------------------------------------------------------------
console.log("\n=== STEP 5: Before vs After ===");
console.log(
  "Pattern".padEnd(54) +
    "RU before".padStart(11) +
    "RU after".padStart(11) +
    "delta %".padStart(10) +
    "  composite (after)"
);
console.log("-".repeat(120));
for (let i = 0; i < patterns.length; i++) {
  const b = before[i].ru;
  const a = after[i].ru;
  const delta = b > 0 ? ((a - b) / b) * 100 : 0;
  console.log(
    patterns[i].label.padEnd(54) +
      b.toFixed(2).padStart(11) +
      a.toFixed(2).padStart(11) +
      (delta >= 0 ? "+" : "") + delta.toFixed(1).padStart(9) +
      "  " + after[i].composite
  );
}

console.log("\nNotes:");
console.log("  * Negative delta % == cheaper after the composite was added.");
console.log("  * If the 'composite (after)' column shows '(none)' on a row,");
console.log("    the indexer probably hadn't finished rebuilding — re-run");
console.log("    just Step 4 in a moment.");
console.log("  * For the raw indexMetrics text per query (not just the");
console.log("    one-line summary), paste 02-extended-queries.cosmos.js.");

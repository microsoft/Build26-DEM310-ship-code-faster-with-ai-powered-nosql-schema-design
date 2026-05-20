// =============================================================================
// Iteration 1 (naive-b) — 02-simulate-unbounded-growth.cosmos.js
//
// Mirrors scripts/_naive_b_simulate.py inside the
// Cosmos DB Shell. For N iterations:
//   1. Read the customer doc (capture read RU + JSON size).
//   2. Append a synthetic order with K items to doc.orders[].
//   3. Upsert the doc (capture upsert RU).
//
// Watch BOTH the doc size and the upsert RU climb every iteration. That's
// the unbounded-array anti-pattern in action.
//
// Twiddle CUSTOMER_ID / ITERATIONS / ITEMS_PER_ORDER to taste.
// =============================================================================

const DB = "Build26DEM310DB-i1b";
const CONTAINER = "CustomersWithEmbeddedOrders";
const CUSTOMER_ID = "C00005";
const ITERATIONS = 20;
const ITEMS_PER_ORDER = 5;
const ITEM_LIMIT_BYTES = 2 * 1024 * 1024;   // Cosmos DB per-item hard limit

const db = cosmos.database(DB);
const container = db.container(CONTAINER);

// Pick a deterministic slice of the master product catalog.
const products = require("../../naive-a/demo-shell/seed-data/Products.json");

function buildOrder(seq) {
  const items = [];
  let total = 0;
  for (let i = 1; i <= ITEMS_PER_ORDER; i++) {
    const p = products[(seq * ITEMS_PER_ORDER + i) % products.length];
    const qty = 1 + (i % 3);
    items.push({
      lineNumber: i,
      productId: p.productId,
      productName: p.name,
      unitPrice: p.price,
      quantity: qty,
      lineTotal: Math.round(p.price * qty * 100) / 100,
    });
    total += p.price * qty;
  }
  return {
    orderId: `O-SIM-${String(seq).padStart(5, "0")}`,
    orderDate: new Date(Date.now() - (20 - seq) * 86400_000).toISOString(),
    status: "Placed",
    subtotal: Math.round(total * 100) / 100,
    tax: Math.round(total * 8) / 100,
    total: Math.round(total * 108) / 100,
    items: items,
  };
}

function sizeBytes(doc) {
  return new TextEncoder().encode(JSON.stringify(doc)).length;
}

console.log(`\nGrowing ${CUSTOMER_ID} for ${ITERATIONS} iterations ` +
            `(${ITEMS_PER_ORDER} items/order).\n`);
console.log(" iter    KB    read RU   upsert RU   orders");
console.log(" ----  ------  -------   ---------   ------");

const rows = [];
for (let i = 1; i <= ITERATIONS; i++) {
  const read = await container.item(CUSTOMER_ID, CUSTOMER_ID).read();
  const doc = read.resource;
  const readRu = read.requestCharge;

  doc.orders.push(buildOrder(i));
  const up = await container.items.upsert(doc);
  const upsertRu = up.requestCharge;

  const kb = sizeBytes(doc) / 1024;
  rows.push({ i, kb, readRu, upsertRu, orders: doc.orders.length });
  console.log(
    ` ${String(i).padStart(4)}  ${kb.toFixed(2).padStart(6)}  ` +
    `${readRu.toFixed(2).padStart(7)}   ${upsertRu.toFixed(2).padStart(9)}   ` +
    `${String(doc.orders.length).padStart(6)}`
  );
}

const first = rows[0], last = rows[rows.length - 1];
const deltaKb = last.kb - first.kb;
const deltaRu = last.upsertRu - first.upsertRu;

console.log(`\nGrowth across ${ITERATIONS} iterations:`);
console.log(`  doc size : ${first.kb.toFixed(2)} KB -> ${last.kb.toFixed(2)} KB  (+${deltaKb.toFixed(2)} KB)`);
console.log(`  upsert RU: ${first.upsertRu.toFixed(2)} -> ${last.upsertRu.toFixed(2)}  (+${deltaRu.toFixed(2)} RU)`);

const perIterKb = deltaKb / Math.max(ITERATIONS - 1, 1);
if (perIterKb > 0) {
  const remainingKb = (ITEM_LIMIT_BYTES / 1024) - last.kb;
  const remainingIters = Math.floor(remainingKb / perIterKb);
  console.log(
    `\nAt ~${perIterKb.toFixed(2)} KB / iteration this document will hit the\n` +
    `2 MB Cosmos item limit in ~${remainingIters.toLocaleString()} more iterations.`
  );
}

console.log("\nThis is the unbounded-array anti-pattern. Iteration 2 splits");
console.log("the orders into separate documents that share the customerId");
console.log("partition key — read cost stays flat as history grows.");

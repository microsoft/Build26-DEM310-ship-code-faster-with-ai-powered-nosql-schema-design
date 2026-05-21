# Takeaways

The demo collapses a lot of decisions into focused outcomes.

## 1. In NoSQL - Access Patterns, not tables drive Optimal Design

The single biggest mistake when moving from a relational store to Cosmos
DB or apply Relational Data Modeling principles to NoSQL is to translate tables as 1:1 into containers and primary keys to partition
keys without optimization by access patterns. Inventory **how the data is read and written** before you finalize NoSQL document models — every other decision falls out of that.

## 2. Co-locate what you read (and write - but not UPDATE) together

If a single screen needs a customer plus their orders, those documents
should share a partition key. Embed `items[]` inside the order document
when N is bounded and the items aren't reused.
**Avoid frequent updates on large documents and unbounded arrays anti-patterns.**

## 3. Use a `type` discriminator to combine related shapes where possible
Azure Cosmos DB NoSQL provide schema flexibility - use it!
A single container can hold multiple document shapes if they share a
partition key. The `type` field is the discriminator that lets you filter
and pivot in queries. 

## 4. Transactional batches enabled by shared partition key

Place-order is atomic in iteration 2 because the customer doc and the
order doc both live in `customerId`'s partition. That's the architectural
unlock for the entire "single roundtrip, two writes" pattern.

## 5. Composite indexes pay off when `ORDER BY` has more than one column or complex repdicate filters

`includedPaths` covers single-column sorts and equality filters. The
moment your query says `ORDER BY x, y` (or even `WHERE a = ? ORDER BY b`),
add a composite — it removes the in-memory sort. See iteration 3.

## What we deferred

- **Hierarchical partition keys (HPK).** `/customerId, /year` would help
  when a single customer's history exceeds 10 GB. At the projected sizes
  the flat `/customerId` partition is fine for the next ~3 years.
- **Change feed and materialized views.** Useful for product search
  facets, analytics rollups, and event sourcing — out of scope here.
- **Multi-region writes.** Consider Multi-Region writes if your
  e-commerce application requires a 99.999% write availability SLA.

## Where to go next

- [Cosmos DB modeling guidance on Microsoft Learn](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)
- [Cosmos DB Agent in VS Code](https://learn.microsoft.com/azure/cosmos-db/extensions/vscode-extension)
- [Indexing policies reference](https://learn.microsoft.com/azure/cosmos-db/index-policy)
- aka.ms/build26-next-steps

# 1. Business context

The demo's storyline is intentionally familiar so the modeling decisions
are the only thing competing for the audience's attention.

## The product

A **bike-shop e-commerce backend** based on the AdventureWorksLT schema:

- Customers shop the catalog (products and categories).
- They build a cart and place orders.
- Orders move through statuses (`InCart` → `Placed` → `Shipped` →
  `Delivered`, with `Cancelled` as a side branch).

## The team's situation

The team is porting from SQL Server to Azure Cosmos DB. Their first commit
copies the relational schema 1:1 — one container per table, each
partitioned by the primary-key column. It works, but RU charges look high
even at demo volume.

Today they're going to:

1. Run the read patterns against the naive layout and capture RU.
2. Open the Cosmos DB Agent and walk through the [access patterns](./2-access-patterns.md)
   and [volumetrics](./3-volumetrics.md).
3. Apply the agent's recommendations — collapse five containers into two,
   embed `items[]`, use a `type` discriminator, switch the partition keys.
4. Re-run the patterns and compare RU.

That before/after RU comparison is the demo's punchline.

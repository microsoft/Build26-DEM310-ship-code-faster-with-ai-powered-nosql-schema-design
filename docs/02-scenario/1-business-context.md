# 1. Business context

The demo's storyline is intentionally familiar so the modeling decisions
are the only thing competing for the audience's attention.

## The product

A **bike-shop e-commerce backend** based on the AdventureWorksLT schema:

- Customers shop the catalog (**products** and **categories**).
- They build a cart and place orders.
- Orders move through statuses (`InCart` → `Placed` → `Shipped` →
  `Delivered`, with `Cancelled` as a side branch).

## The starting point

The team is porting from SQL Server to Azure Cosmos DB. Their first commit
copies the relational schema 1:1 — one container per table, each
partitioned by the primary-key column. It works, but RU charges look high
even at demo volume, and they suspect the design won't hold up under
production load.

## The goal

Arrive at an **optimal Azure Cosmos DB for NoSQL design** — one whose
shape is driven by the requirements documented in  [access patterns](./2-access-patterns.md) and [volumetrics](./3-volumetrics.md), not just the source SQL schema — and get there **quickly**, with the help of  [Azure Cosmos DB Agent Kit](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)
and GitHub Copilot doing the heavy lifting on the NoSQL data modeling, container partition-key design, embedding vs referencing, and query-optimization decisions.

The before/after RU comparison that comes out the other side is the
demo's payoff — but you'll see *how* the design changes, and *why*, as
part of the walkthrough.



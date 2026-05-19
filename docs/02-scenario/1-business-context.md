# 1. Business context

The demo's storyline is intentionally familiar so the modeling decisions
are the only thing competing for your attention.

## The product

A **bike-shop e-commerce backend** based on the classic RDBMS schema:

- Customers shop the catalog (**products** and **categories**).
- Customer place **orders** which go through different status and stored as **Order** and **LineItems**.
- Customer also has a **Customer** profile domain with personal info.

## The starting point

The team is tasked to modernize application from Relational Datrabase to Azure Cosmos DB. Their first commit
copies the relational schema 1:1 — one container per table, each
partitioned by the primary-key column. It works, but code looks too complex, RU charges look high even at demo volume for many multi-hop queries, and they suspect the design won't hold up under production load.

## The goal

Arrive at an **optimal Azure Cosmos DB for NoSQL design** and make sure new design is scalable for production requirements documented in  [access patterns](./2-access-patterns.md) and [volumetrics](./3-volumetrics.md), and not just using the source SQL schema — and get there **faster**. Leverage  [Azure Cosmos DB Agent Kit](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)
and GitHub Copilot to accelerate and improve dessisions on NoSQL data modeling, container partition-key design, embedding vs referencing, and query-optimization decisions as well as automate application code refactoring.

The before/after RU comparison that comes out the other side is the
demo's payoff — but you'll see *how* the design changes, and *why*, as
part of the walkthrough.



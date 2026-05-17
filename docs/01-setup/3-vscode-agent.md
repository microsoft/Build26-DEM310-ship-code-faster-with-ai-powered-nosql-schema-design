# 3. VS Code + Cosmos DB Agent

The demo uses two VS Code extensions:

1. **Azure Databases (Cosmos DB) extension** — adds the *Cosmos DB Shell*
   and registers the *Cosmos DB Agent* that GitHub Copilot Chat can invoke.
2. **GitHub Copilot Chat** — chat surface where you talk to the agent.

## Install

In VS Code: open the Extensions view (Ctrl+Shift+X) and install both.

Confirm they're enabled:

- The **Azure** activity bar icon shows a **Cosmos DB** node.
- Opening Copilot Chat lets you `@` the **Cosmos DB Agent**.

## Connect to the emulator

1. Open the Cosmos DB Shell from the command palette: *Cosmos DB: Open Shell*.
2. Choose **Connect to emulator** (or paste the endpoint + key manually).
3. Run `db.databases.list()` — you should see an empty result until the
   first seed script runs.

## Talk to the agent

Open Copilot Chat and try, for example:

> @cosmos given these four access patterns: (1) get a customer and their
> 5 most recent orders, (2) get an order with its line items, (3) place an
> order, (4) list all products in a category — and these container shapes,
> what should I change to keep most reads single-partition?

Continue with [4 — Python environment](./4-python-env.md).

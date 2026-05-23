# 3. Visual Studio Code + Cosmos DB Agent

The demo uses two Visual Studio Code extensions:

1. **Azure Databases (Cosmos DB) extension** — adds the *Cosmos DB Shell*
   and registers the *Cosmos DB Agent* that GitHub Copilot Chat can invoke.
2. **GitHub Copilot Chat** — chat surface where you talk to the agent.

## Install

In Visual Studio Code: open the Extensions view (Ctrl+Shift+X) and install both.

Confirm they're enabled:

- The **Azure** activity bar icon shows a **Cosmos DB** node.
- Opening Copilot Chat lets you `@` the **Cosmos DB Agent**.

## Not using Visual Studio Code? Install the Cosmos DB Agent Kit instead

The [**Azure Cosmos DB Agent Kit**](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)
([repo](https://github.com/AzureCosmosDB/cosmosdb-agent-kit)) is an open-source
collection of [Agent Skills](https://agentskills.io/) that teaches
**any** Agent Skills–compatible assistant the same Cosmos DB best
practices the Visual Studio Code agent uses — partition-key design, RU
optimization, modeling, indexing, SDK patterns, and monitoring.

It works with:

- **GitHub Copilot** in Visual Studio, JetBrains IDEs, Eclipse, Xcode
- **Claude Code** (Anthropic CLI)
- **Gemini CLI** (Google CLI)
- Any other Agent Skills–compatible tool

Prerequisite: **Node.js + npx**.

Install once, globally for your shell user:

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

That's it — the skill activates automatically when your assistant
detects a Cosmos DB task. Use the same prompts you'd use against the VS
Code agent (the ones in [iteration 2's walkthrough](../03-walkthrough/2-iteration-02-optimized.md)
are a good warm-up).

Keep it current periodically with the same command — `npx skills update`
updates in place.

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

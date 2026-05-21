# 🚀 Get Started

**This repo is where attendees go to continue their learning after your session — and your Copilot agent will help you set it up.**

### Step 1: Open your repo

Open this repo in a **Codespace** (click the green **Code** button → **Create a Codespace**) — or clone it locally. Then open **GitHub Copilot Chat**.

### Step 2: Add your content

Give the agent something to work with. Drag files into the Explorer panel — session abstracts, outlines, screenshots, notes — and drop them in one of two places:

| Where to put it | What goes there | Who sees it |
|---|---|---|
| **`_remove-before-publish/`** | Internal reference materials (abstracts, outlines, screenshots, planning docs) | **Copilot only** — never published |
| **`/docs/`, `/src/`, or repo root** | Lab instructions, demo code, sample data, getting-started guides | **Attendees** — published with the repo |

> 💡 Not sure? Start by dropping your session abstract or outline into `_remove-before-publish/`. The agent will figure out what to do with it.

### Step 3: Ask the Agent

Once your content is in the repo, use these three phrases with Copilot to build out your session repo:

| Phrase to use with Copilot | What it does | When to run it |
|---|---|---|
| **"Help me get started"** | Sets up session title, description, outcomes, and owners | After you've added your session abstract or outline to the repo |
| **"Help me refine content"** | Organizes your session content into the repo | Each time you add or update content |
| **"Help me finalize"** | Final review, cleanup, and publication prep | When you're ready to publish |

> 💡 **These three phrases are just the starting point.** Copilot can do much more — try asking it to brainstorm next steps for attendees, generate code samples, or build out your repo structure. Don't be afraid to put it in plan mode and ask for what you need.

---

<a name="start-building"></a>
<br>
<p align="center">
<img src="img/banner-build-26.png" alt="Microsoft Build 2026" width="1200"/>
</p>

# [Microsoft Build 2026](https://build.microsoft.com)

## 🔥 DEM310: Ship code faster with AI-powered NoSQL schema design

### Session Description

NoSQL schema design is hard—denormalization decisions, partition key selection, and data modeling patterns require expertise. Use GitHub Copilot and the new Azure Cosmos DB Agent Kit to accelerate development with AI-assisted schema generation, query optimization suggestions, and refactoring recommendations. Iterate rapidly with the new Mac/Linux emulator for local testing. Demo shows schema evolution across three iterations in 30 minutes versus days of manual design.

### 🚀 Getting started

If you'd like to follow along with this demo at your own pace:

1. **Clone this repository**

   ```
   git clone https://github.com/microsoft/Build26-DEM310.git
   ```

2. **Install the Azure Cosmos DB emulator (local, free)**
   - Recommended: install the **classic Azure Cosmos DB Emulator** for Windows from [Install and develop locally with the Azure Cosmos DB Emulator](https://learn.microsoft.com/azure/cosmos-db/emulator). It reports differentiated, production-like RU charges, which is what makes the iteration-to-iteration comparison in this demo land.
   - Cross-platform alternative (preview): the [Linux Docker emulator](https://learn.microsoft.com/azure/cosmos-db/how-to-develop-emulator#install-the-emulator) (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview`) runs on Windows, macOS, and Linux — useful for connectivity, but it currently returns a flat synthetic RU per request, so prefer the classic emulator when comparing iterations.
   - **Validate:** start the emulator container and confirm the Data Explorer loads at `https://localhost:8081/_explorer/index.html`.

3. **Install the Azure Cosmos DB extension for Visual Studio Code (preferred path for the Agent Kit and Shell)**
   - Install the extension following the steps in [Azure Cosmos DB for NoSQL best practices in GitHub Copilot for Visual Studio Code — Step 1: Install required extensions](https://learn.microsoft.com/azure/cosmos-db/github-copilot-visual-studio-code-best-practices#step-1-install-required-extensions). The same extension is documented in [Use Visual Studio Code to connect and query Azure Cosmos DB instances](https://learn.microsoft.com/azure/cosmos-db/visual-studio-code-extension).
   - The extension bundles the **Azure Cosmos DB Agent Kit** (AI-assisted schema design with GitHub Copilot and Cosmos SDK coding best practices) and the **Azure Cosmos DB Shell** (interactive querying). If you use CLI or other tool. If you use Copilot CLI or other tools - install [Azure Cosmos DB Agent Kit](https://github.com/AzureCosmosDB/cosmosdb-agent-kit) manually or link it to your repo.
   - **Validate:** open the Azure Cosmos DB view in the Activity Bar and connect to the local emulator account from step 2.

4. **Try the Azure Cosmos DB Shell against the emulator**
   - Open the Shell from the Azure Cosmos DB extension — see [Azure Cosmos DB Shell Visual Studio Code extension](https://learn.microsoft.com/azure/cosmos-db/shell/visual-studio-code).
   - **Validate:** connect to the emulator started in step 2, create a database, and list databases to confirm end-to-end connectivity.

5. **Walk through the three schema-evolution iterations covered in the demo**
   - Install Python deps: `pip install -r src/requirements.txt`
   - **Drive the demo from the walkthrough scenario.** Follow the four-section flow below — *Setup → Scenario → Walkthrough → Takeaways*. Each iteration page is a prompt-first script: feed the listed Copilot prompts to the Cosmos DB Agent Kit in order, let the agent propose the design, generate the seed/queries, and capture the RU numbers.
     1. [Setup](./docs/01-setup/) — prerequisites, emulator, VS Code + agent, Python env.
     2. [Scenario](./docs/02-scenario/) — the inputs you paste into the agent in Step 1 of every iteration. Each one is a worked example you can lift for your own domain (reusable templates: [access-patterns-template.md](./docs/access-patterns-template.md), [volumetrics-template.md](./docs/volumetrics-template.md)):
        - [Business context](./docs/02-scenario/1-business-context.md) — bike-shop e-commerce backend on a classic RDBMS schema, the "why" the agent needs.
        - [Access patterns](./docs/02-scenario/2-access-patterns.md) — P1–P4 (the four core patterns) plus R-EXT-1/2/3 (the post-launch extensions used in iteration 3).
        - [Volumetrics](./docs/02-scenario/3-volumetrics.md) — document counts, sizes, and TPS estimates that drive the partition-key and indexing recommendations.
     3. **Walkthrough — run these in order:**
        - [Iteration 1 — Naive port](./docs/03-walkthrough/1-iteration-01-naive.md) (baseline)
        - [Iteration 2 — Agent-guided redesign](./docs/03-walkthrough/2-iteration-02-optimized.md) (AI copilot optimized)
        - [Iteration 3 — Composite indexes (optional)](./docs/03-walkthrough/3-iteration-03-composite-indexes.md)
        - [Iteration 4 — Hybrid + vector search (take home, cloud-only)](./docs/03-walkthrough/4-iteration-04-hybrid-vector-search.md)
     4. [Takeaways](./docs/04-takeaways.md) — what to remember after you close the laptop.
   - **Reference code (for validation / fallback only).** The matching `src/iteration-XX-*/complete/` folders are *not* the primary driver — they're the reference solution to validate against, or to copy from if you run out of time. The matching `demo/` folders are the same files with TODOs for hands-on practice.
     - [`src/iteration-01-naive/`](./src/iteration-01-naive/) — `naive-a/` (1:1 relational port) and `naive-b/` (unbounded-array anti-pattern with growth simulator)
     - [`src/iteration-02-optimized/`](./src/iteration-02-optimized/) — agent-guided redesign (CustomerOrders + Products)
     - [`src/iteration-03-composite-indexes/`](./src/iteration-03-composite-indexes/) — composite indexes for new access patterns
     - [`src/iteration-04-hybrid-vector-search/`](./src/iteration-04-hybrid-vector-search/) — **cloud-only**: requires an Azure Cosmos DB account and Azure AI Foundry / Azure OpenAI (not supported by the local emulator)

### 🧠 Learning Outcomes

By the end of this demo, you will be able to:

- Use GitHub Copilot and the Azure Cosmos DB Agent Kit to generate and evolve NoSQL schemas with AI assistance.
- Apply AI-recommended patterns for partition key selection, denormalization, and query optimization.
- Iterate rapidly against a local Azure Cosmos DB emulator (classic Windows emulator for RU-accurate comparisons; cross-platform Linux preview also available).

### 💬 Keep Learning with Copilot

Try these prompts with GitHub Copilot to explore the topics from this demo. Open Copilot Chat in VS Code (`Ctrl+Alt+I` on Windows/Linux, `Cmd+Shift+I` on Mac), paste a prompt, and see what you learn. Try connecting the [Microsoft Learn MCP Server](#-microsoft-learn-mcp-server) for the latest official documentation.

Use these as a starting point — or write your own!

1. **Recommend a container layout from access patterns** — the move from iteration 1 to iteration 2:

   ```
   I'm modeling an e-commerce backend on Azure Cosmos DB for NoSQL. Access patterns: (1) get a customer plus their 5 most recent orders, (2) get one order with line items, (3) place an order (1 header + N items, must be atomic), (4) list products in a category sorted by price. Using the Microsoft Learn MCP Server for current best practices, propose a container layout (containers, partition keys, embedded vs separate documents) that keeps most reads single-partition and place-order in a transactional batch. Show me the resulting JSON shape for one customer and one order.
   ```

2. **Spot the unbounded-array anti-pattern** — what `naive-b` demonstrates:

   ```
   Review this Azure Cosmos DB design: one document per customer, with an `orders` array that grows every time the customer places an order. Each new order does a read-modify-upsert of the whole document. Using the Microsoft Learn MCP Server, explain (a) why the upsert RU charge grows over time, (b) what hard limit this design will hit, and (c) the cleanest way to refactor it without changing the partition key.
   ```

3. **Re-evaluate the design for cross-partition access and Black Friday scale** — the stretch beyond iteration 3:

   ```
   I have an Azure Cosmos DB for NoSQL container `CustomerOrders` partitioned by /customerId. It handles single-customer reads and place-order writes well, but I now also need cross-partition access patterns: (a) "all orders placed in the last 15 minutes across all customers" for a live operations dashboard, (b) "top-selling products in the last hour" for merchandising. Using the Microsoft Learn MCP Server, walk me through a what-if for Black Friday: 50x normal traffic, ~1.5M orders/minute globally, heavy concurrent reads on the same hot products. For each cross-partition query, recommend whether to solve it with indexing, a secondary container materialized from the change feed, a separate analytical path, or a different partition key — and explain the RU and latency tradeoffs of each option at that scale.
   ```

### 💻 Technologies Used

1. [Azure Cosmos DB for NoSQL — Data modeling](https://learn.microsoft.com/azure/cosmos-db/modeling-data)
1. [Azure Cosmos DB Agent Kit for AI coding assistants](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)
1. [Azure Cosmos DB emulator (local development)](https://learn.microsoft.com/azure/cosmos-db/how-to-develop-emulator)
1. [Azure Cosmos DB Shell](https://learn.microsoft.com/azure/cosmos-db/shell/overview)
1. [GitHub Copilot Chat in Visual Studio Code](https://learn.microsoft.com/visualstudio/ide/visual-studio-github-copilot-chat)

### 📚 Resources and Next Steps

| Resource | Description |
|:---------|:------------|
| [Welcome to Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/) | **Start here.** Why Azure Cosmos DB for NoSQL: a globally distributed, schema-flexible database with single-digit-millisecond latency, elastic scale, and SLA-backed throughput — the foundation everything in this demo builds on |
| [Azure Cosmos DB extension for Visual Studio Code](https://learn.microsoft.com/azure/cosmos-db/visual-studio-code-extension) | Bundles the Azure Cosmos DB Agent Kit (AI-assisted schema design with GitHub Copilot) and the Azure Cosmos DB Shell — the central tool used throughout the demo |
| [Azure Cosmos DB for NoSQL best practices in GitHub Copilot for Visual Studio Code](https://learn.microsoft.com/azure/cosmos-db/github-copilot-visual-studio-code-best-practices) | Step-by-step guidance for using the Agent Kit with GitHub Copilot — installation, prompts, and recommended workflow |
| [Azure Cosmos DB Shell](https://learn.microsoft.com/azure/cosmos-db/shell/overview) | Cross-platform interactive shell for exploring and managing Azure Cosmos DB databases |
| [Data modeling in Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/modeling-data) | The reference page behind iteration 2 — embed vs reference, denormalization patterns, partition-key choice |
| [Transactional batch operations in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/transactional-batch) | The batch API the optimized place-order in iteration 2 uses |
| [Indexing policies — composite indexes](https://learn.microsoft.com/azure/cosmos-db/index-policy#composite-indexes) | The feature iteration 3 turns on for multi-column `ORDER BY` queries |
| [Azure Cosmos DB service quotas — per-item limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#per-item-limits) | The 2 MB item ceiling that the unbounded-array simulator (`naive-b`) drives toward |
| [Hierarchical partition keys (unlimited logical partition storage)](https://learn.microsoft.com/azure/cosmos-db/hierarchical-partition-keys-unlimited-scale) | The deferred next step called out in `04-takeaways.md` for customers whose history grows past 10 GB |
| [https://aka.ms/build26-next-steps](https://aka.ms/build26-next-steps) | Explore lab and session repos to further your learning from Microsoft Build |


### 🌟 Microsoft Learn MCP Server

The Microsoft Learn MCP Server gives your AI agent direct access to Microsoft's official documentation — grounded, up-to-date answers about the products and services covered in this session.

**VS Code** — One click installation: 

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Microsoft_Learn_MCP-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=microsoft-learn&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Flearn.microsoft.com%2Fapi%2Fmcp%22%7D)


**GitHub Copilot CLI** — Run this to install the Learn MCP Server as a plugin:
```
/plugin install microsoftdocs/mcp
```

For more info, other clients, and to post questions, visit the [Learn MCP Server repo](https://aka.ms/learnmcp).

## Content Owners

<!-- TODO: Add yourself as a content owner
1. Change the src in the image tag to {your github url}.png
2. Change INSERT NAME HERE to your name
3. Change the github url in the final href to your url. -->

<table>
<tr>
    <td align="center"><a href="http://github.com/sesmyrnov">
        <img src="https://github.com/sesmyrnov.png" width="100px;" alt="Sergiy Smyrnov"/><br />
        <sub><b>Sergiy Smyrnov</b></sub></a><br />
            <a href="https://github.com/sesmyrnov" title="talk">📢</a>
    </td>
    <td align="center"><a href="http://github.com/MarkoHot">
        <img src="https://github.com/MarkoHot.png" width="100px;" alt="Marko Hotti"/><br />
        <sub><b>Marko Hotti</b></sub></a><br />
            <a href="https://github.com/MarkoHot" title="talk">📢</a>
    </td>
</tr></table>

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

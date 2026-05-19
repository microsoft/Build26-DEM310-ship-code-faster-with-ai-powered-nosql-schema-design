# 1. Prerequisites

| Tool                                      | Why                                         |
|-------------------------------------------|---------------------------------------------|
| **Python 3.10+**                          | Runs the seed and pattern scripts            |
| **VS Code**                               | Hosts the Cosmos DB extension and Copilot    |
| **Cosmos DB extension for VS Code**       | Provides the **Cosmos DB Agent** and the **Cosmos DB Shell** |
| **Azure Cosmos DB Agent Kit** ([docs](https://learn.microsoft.com/azure/cosmos-db/gen-ai/agent-kit)) | Standalone AI coding assistant integration for Azure Cosmos DB — usable on its own with any MCP-capable client if you'd rather not install the VS Code extension |
| **GitHub Copilot Chat**                   | Lets the agent generate code in the editor   |
| **Cosmos DB emulator** (local)            | Zero-cost target for the demo containers     |
| **git**                                   | To clone this repo                           |

A free Azure account is **not** required for the demo — everything runs
against the local emulator. If you want to run the same code against
production Azure Cosmos DB, swap the `COSMOS_ENDPOINT` and `COSMOS_KEY`
environment variables before running the scripts.

Continue with [2 — Cosmos DB emulator](./2-cosmos-emulator.md).

# 2. Cosmos DB emulator

The demo runs against the local Azure Cosmos DB emulator. The **classic
Windows emulator** is the recommended target — it reports differentiated,
production-like RU charges, which is the whole point of comparing the
three iterations side by side. The Linux Docker preview is fine for
connectivity and shape, but it currently reports a flat synthetic charge
per request and is not suitable for RU comparisons (see
*Additional references* at the bottom).

## Install — classic Windows emulator (recommended)

1. Download and install the Azure Cosmos DB Emulator MSI from
   [Install and develop locally with the Azure Cosmos DB Emulator](https://learn.microsoft.com/azure/cosmos-db/emulator).
2. Start it from the Start menu — the tray icon turns green when the
   service is ready and a browser tab opens the Data Explorer at
   `https://localhost:8081/_explorer/index.html`.
3. (Optional, recommended for this demo) reset and start with a higher
   partition count so the cross-partition queries in iteration 1 really do
   span multiple partitions:

   ```powershell
   & "$env:ProgramFiles\Azure Cosmos DB Emulator\CosmosDB.Emulator.exe" /Shutdown
   & "$env:ProgramFiles\Azure Cosmos DB Emulator\CosmosDB.Emulator.exe" /ResetDataPath
   & "$env:ProgramFiles\Azure Cosmos DB Emulator\CosmosDB.Emulator.exe" /NoUI /PartitionCount=10
   ```

The SDK endpoint is `https://localhost:8081` (HTTPS, self-signed cert).
The seed and pattern scripts handle the cert with `connection_verify=False`.

## Validate

Test [Azure Cosmos DB Emulator](https://localhost:8081/_explorer/index.html) and do to Explorer to validate view.


> The emulator ships with a **well-known** primary key:
> `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`
> It is baked into [`src/.env.example`](../../src/.env.example) — copy
> that file to `src/.env` once and you're done. Override `COSMOS_ENDPOINT`
> / `COSMOS_KEY` in `src/.env` if you point at a different emulator or a
> real Azure Cosmos DB account. See
> [4 — Python environment](./4-python-env.md) for details.

## Additional references

- [Azure Cosmos DB Linux emulator (vNext preview)](https://learn.microsoft.com/azure/cosmos-db/how-to-develop-emulator)
  — Docker image
  `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview`.
  Cross-platform (Windows / macOS / Linux), gateway on
  `http://localhost:8081`, data explorer on `https://localhost:1234`. Good
  for verifying the code runs on macOS/Linux; **not** recommended for the
  RU comparison story because it currently returns a flat synthetic
  charge per request. To use it, set `COSMOS_ENDPOINT=http://localhost:8081`
  in `src/.env`.
- [Develop locally using the Azure Cosmos DB emulator](https://learn.microsoft.com/azure/cosmos-db/how-to-develop-emulator)
  — top-level Microsoft Learn page covering both emulators.

Continue with [3 — Visual Studio Code + Cosmos DB Agent](./3-vscode-agent.md).

# 2. Cosmos DB emulator

The demo runs against the local Azure Cosmos DB emulator. Three install
options — pick whichever matches your platform.

## Option A — Docker (cross-platform, recommended)

```powershell
docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview
docker run --detach --publish 8081:8081 --publish 1234:1234 `
    --name cosmosdb `
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview
```

The emulator's data explorer is available at `https://localhost:1234`; the
SDK endpoint is `https://localhost:8081`.

## Option B — Windows installer

Download from the Microsoft Learn page on the Cosmos DB emulator and run
the MSI. The shortcut starts the service and opens the explorer in your
default browser.

## Option C — macOS / Linux native

Use the Linux emulator container — same image as Option A.

## Validate

```powershell
python -c "import urllib3, requests; urllib3.disable_warnings(); print(requests.get('https://localhost:8081/_explorer/emulator.pem', verify=False).status_code)"
```

A response of `200` means the emulator is reachable.

> The emulator ships with a **well-known** primary key:
> `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`
> The seed and pattern scripts default to it. Override via the
> `COSMOS_ENDPOINT` and `COSMOS_KEY` environment variables.

Continue with [3 — VS Code + Cosmos DB Agent](./3-vscode-agent.md).

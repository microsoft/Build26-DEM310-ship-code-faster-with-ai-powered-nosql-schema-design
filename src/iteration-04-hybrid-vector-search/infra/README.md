# Iteration 4 — Infrastructure

Parameterized Bicep + a PowerShell wrapper to spin up everything the
hybrid + vector demo needs in **one resource group**:

| Resource | Module | Purpose |
| --- | --- | --- |
| Cosmos DB account (serverless) + DB + `ProductsRich` container | [`modules/cosmos.bicep`](./modules/cosmos.bicep) | Vector + full-text search container, local auth disabled |
| Azure AI Foundry account + chat + embedding deployments | [`modules/foundry.bicep`](./modules/foundry.bicep) | Embeddings + (optional) chat for the demo, local auth disabled |
| Role assignments | [`modules/rbac.bicep`](./modules/rbac.bicep) | Cosmos DB Operator (control) + Cosmos DB Built-in Data Contributor (data) + Cognitive Services OpenAI User |

All keys are off — every Python call authenticates via
`DefaultAzureCredential`.

## Deploy

```powershell
az login
az account set --subscription <your-subscription-id>

cd src/iteration-04-hybrid-vector-search/infra
./deploy.ps1 -ResourceGroup rg-dem310-i4 -Location eastus2
```

The script:

1. Resolves the signed-in user's object ID (override with `-PrincipalId`).
2. Creates the resource group if it doesn't exist.
3. Runs `az deployment group create` against [`main.bicep`](./main.bicep)
   using [`main.bicepparam`](./main.bicepparam) for defaults.
4. Prints the four lines to paste into `src/.env`.

## Parameters

All parameters live in [`main.bicepparam`](./main.bicepparam). Override
any of them on the command line, for example:

```powershell
./deploy.ps1 -ResourceGroup rg-dem310-i4 -Location eastus2 -NameSuffix mydemo
```

Or call `az` directly:

```powershell
az deployment group create `
  -g rg-dem310-i4 `
  -f main.bicep `
  -p main.bicepparam `
  -p nameSuffix=mydemo `
  -p principalId=$(az ad signed-in-user show --query id -o tsv) `
  -p chatModelName=gpt-4o-mini `
  -p embeddingModelName=text-embedding-3-small
```

### Required parameters

| Name | Description |
| --- | --- |
| `principalId` | Entra ID object ID of the user/SP that will run the demo. Gets the three role assignments above. |

### Optional parameters (with defaults)

| Name | Default | Notes |
| --- | --- | --- |
| `nameSuffix` | `dem310x` | 3–8 lowercase chars suffixed to every resource name |
| `location` | `eastus2` | Must support Cosmos vector+FTS and your model SKUs |
| `databaseName` | `Build26DEM310DB-i4` | |
| `containerName` | `ProductsRich` | |
| `embeddingDimensions` | `1536` | Must match the embedding model below |
| `chatDeploymentName` / `chatModelName` / `chatModelVersion` | `gpt-4o-mini` / `gpt-4o-mini` / `2024-07-18` | |
| `embeddingDeploymentName` / `embeddingModelName` / `embeddingModelVersion` | `text-embedding-3-small` / `text-embedding-3-small` / `1` | |
| `principalType` | `User` | Use `ServicePrincipal` for a managed identity / SP |

## Tear down

```powershell
az group delete --name rg-dem310-i4 --yes --no-wait
```

## Notes

* **Region availability matters.** The `EnableNoSQLVectorSearch` and
  `EnableNoSQLFullTextSearch` capabilities and the `gpt-4o-mini` /
  `text-embedding-3-small` SKUs are all available in `eastus2` at time of
  writing. If you change region, double-check the
  [Cosmos vector docs](https://learn.microsoft.com/azure/cosmos-db/nosql/vector-search)
  and the
  [Azure OpenAI model availability matrix](https://learn.microsoft.com/azure/ai-services/openai/concepts/models).
* **Cosmos DB data-plane RBAC vs Azure RBAC.** The "Built-in Data
  Contributor" role on Cosmos is **not** a standard Azure RBAC role —
  it's assigned via the `Microsoft.DocumentDB/.../sqlRoleAssignments`
  resource type. The Bicep module handles this for you.
* **RBAC propagation.** Both Azure RBAC and Cosmos SQL RBAC assignments
  can take 30–60 seconds to propagate. If your first run of `seed.py`
  hits a 401/403, wait a minute and retry.

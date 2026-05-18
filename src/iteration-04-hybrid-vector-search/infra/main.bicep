// =============================================================================
// DEM310 iteration 4 — resource-group-scope orchestrator
//
// Provisions:
//   * Azure Cosmos DB for NoSQL account (serverless) with the Vector Search
//     and Full-Text Search capabilities enabled; local auth disabled.
//   * The Build26DEM310 database with a single ProductsRich container that
//     carries both a Vector Embedding Policy and a Full-Text Policy.
//   * An Azure AI Foundry (Cognitive Services / AIServices kind) account
//     with two model deployments: a chat model and an embedding model.
//     Local auth disabled.
//   * Role assignments that grant the demo principal:
//       - control-plane:  Cosmos DB Operator on the Cosmos account
//                         (lets the demo create DBs / containers / policies
//                          via the management API at runtime if desired)
//       - data-plane:     Cosmos DB Built-in Data Contributor (SQL RBAC)
//                         on the Cosmos account (lets the demo read/write
//                         items, create containers via the data plane)
//       - Foundry:        Cognitive Services OpenAI User on the AI account
//                         (lets the demo call chat + embedding endpoints)
//
// Deploy with:
//   ./deploy.ps1 -ResourceGroup rg-dem310-i4 -Location eastus2
//
// Or directly:
//   az group create -n rg-dem310-i4 -l eastus2
//   az deployment group create \
//     -g rg-dem310-i4 \
//     -f main.bicep \
//     -p main.bicepparam \
//     -p principalId=$(az ad signed-in-user show --query id -o tsv)
// =============================================================================

targetScope = 'resourceGroup'

@description('Short suffix appended to every resource name to keep them globally unique. Lowercase letters/digits, 3-8 chars.')
@minLength(3)
@maxLength(8)
param nameSuffix string

@description('Azure region for every resource. Must support Cosmos DB vector + FTS and the requested AI Foundry models.')
param location string = resourceGroup().location

@description('Cosmos DB database name created inside the account.')
param databaseName string = 'Build26DEM310'

@description('Container that will hold the embedding + description-bearing product documents.')
param containerName string = 'ProductsRich'

@description('Dimensions of the embedding model output. Must match the model below — text-embedding-3-small => 1536.')
param embeddingDimensions int = 1536

@description('Name of the chat completion deployment.')
param chatDeploymentName string = 'gpt-4o-mini'

@description('Underlying chat model.')
param chatModelName string = 'gpt-4o-mini'

@description('Chat model version. Pick the latest GA version available in your region.')
param chatModelVersion string = '2024-07-18'

@description('Name of the embedding deployment.')
param embeddingDeploymentName string = 'text-embedding-3-small'

@description('Underlying embedding model.')
param embeddingModelName string = 'text-embedding-3-small'

@description('Embedding model version.')
param embeddingModelVersion string = '1'

@description('Object ID of the Entra ID principal (user, group, or service principal) that will run the demo and therefore needs RBAC. Get yours with: az ad signed-in-user show --query id -o tsv')
param principalId string

@description('Principal type for the role assignments.')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'User'

// -----------------------------------------------------------------------------
// Modules
// -----------------------------------------------------------------------------

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    accountName:         'cosmos-${nameSuffix}'
    location:            location
    databaseName:        databaseName
    containerName:       containerName
    embeddingDimensions: embeddingDimensions
  }
}

module foundry 'modules/foundry.bicep' = {
  name: 'foundry'
  params: {
    accountName:             'aif-${nameSuffix}'
    location:                location
    chatDeploymentName:      chatDeploymentName
    chatModelName:           chatModelName
    chatModelVersion:        chatModelVersion
    embeddingDeploymentName: embeddingDeploymentName
    embeddingModelName:      embeddingModelName
    embeddingModelVersion:   embeddingModelVersion
  }
}

module rbac 'modules/rbac.bicep' = {
  name: 'rbac'
  params: {
    cosmosAccountName:  cosmos.outputs.accountName
    foundryAccountName: foundry.outputs.accountName
    principalId:        principalId
    principalType:      principalType
  }
  dependsOn: [
    cosmos
    foundry
  ]
}

// -----------------------------------------------------------------------------
// Outputs — drop these into src/.env
// -----------------------------------------------------------------------------
output cosmosEndpoint       string = cosmos.outputs.endpoint
output cosmosAccountName    string = cosmos.outputs.accountName
output cosmosDatabaseName   string = databaseName
output cosmosContainerName  string = containerName
output foundryEndpoint      string = foundry.outputs.endpoint
output chatDeploymentName   string = chatDeploymentName
output embeddingDeploymentName string = embeddingDeploymentName
output embeddingDimensions  int    = embeddingDimensions

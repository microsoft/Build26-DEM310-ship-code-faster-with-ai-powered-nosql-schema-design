// =============================================================================
// Role assignments for the DEM310 iteration-4 demo principal.
//
//   Cosmos DB account
//     * Control plane (Azure RBAC):
//         Cosmos DB Operator  (230815da-be43-4aae-9cb4-875f7bd000aa)
//         — lets the principal manage the account (create / delete DBs,
//         containers, indexing policies) without granting access to data.
//     * Data plane (Cosmos DB SQL RBAC):
//         Cosmos DB Built-in Data Contributor
//         (00000000-0000-0000-0000-000000000002)
//         — lets the principal read/write items and create containers via
//         the data plane. This is what the Python SDK uses.
//
//   Azure AI Foundry account
//     * Cognitive Services OpenAI User
//       (5e0bd9bd-7b93-4f28-af87-19fc36ad61bd)
//       — lets the principal call /chat/completions and /embeddings.
// =============================================================================

@description('Existing Cosmos DB account name (provisioned by cosmos.bicep).')
param cosmosAccountName string

@description('Existing AI Foundry account name (provisioned by foundry.bicep).')
param foundryAccountName string

@description('Object ID of the Entra ID principal to grant access to.')
param principalId string

@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string

// Built-in role definition IDs.
var cosmosOperatorRoleId           = '230815da-be43-4aae-9cb4-875f7bd000aa'
var cosmosBuiltInDataContributorId = '00000000-0000-0000-0000-000000000002'
var openAiUserRoleId               = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' existing = {
  name: cosmosAccountName
}

resource foundry 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: foundryAccountName
}

// ---- Cosmos control plane: Cosmos DB Operator -------------------------------
resource cosmosOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: cosmos
  name: guid(cosmos.id, principalId, cosmosOperatorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cosmosOperatorRoleId)
    principalId: principalId
    principalType: principalType
  }
}

// ---- Cosmos data plane: Built-in Data Contributor (SQL RBAC) ----------------
// Note: this is a Cosmos-DB-specific RBAC system distinct from Azure RBAC.
// The role assignment lives as a child of the Cosmos account.
resource cosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-12-01-preview' = {
  parent: cosmos
  name: guid(cosmos.id, principalId, cosmosBuiltInDataContributorId)
  properties: {
    // Account-wide scope so the principal can create databases + containers.
    scope: cosmos.id
    principalId: principalId
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/${cosmosBuiltInDataContributorId}'
  }
}

// ---- Foundry: Cognitive Services OpenAI User --------------------------------
resource foundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, principalId, openAiUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: principalId
    principalType: principalType
  }
}

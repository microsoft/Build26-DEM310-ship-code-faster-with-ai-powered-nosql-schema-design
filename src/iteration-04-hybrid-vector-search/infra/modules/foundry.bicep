// =============================================================================
// Azure AI Foundry (Cognitive Services / kind=AIServices) with one chat
// deployment and one embedding deployment. Local auth disabled — Entra-ID
// only — so a `Cognitive Services OpenAI User` role assignment (granted by
// rbac.bicep) is required for the demo principal to call the endpoints.
// =============================================================================

@description('Foundry account name. 2-64 chars, lowercase letters/digits/hyphens, globally unique within Cognitive Services.')
@minLength(2)
@maxLength(64)
param accountName string

param location string
param chatDeploymentName string
param chatModelName string
param chatModelVersion string
param embeddingDeploymentName string
param embeddingModelName string
param embeddingModelVersion string

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
    // Keyless: force AAD for every call.
    disableLocalAuth: true
  }
}

// Chat completion deployment.
resource chat 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: chatDeploymentName
  sku: {
    // Global Standard keeps demo costs in check; bump if you need more TPM.
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
  }
}

// Embedding deployment. Sequenced after `chat` because Cognitive Services
// only accepts one deployment mutation at a time on a given account.
resource embedding 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: embeddingDeploymentName
  sku: {
    name: 'Standard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
  }
  dependsOn: [ chat ]
}

output accountName string = account.name
output endpoint    string = account.properties.endpoint

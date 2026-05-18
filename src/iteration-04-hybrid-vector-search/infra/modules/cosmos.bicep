// =============================================================================
// Cosmos DB for NoSQL — vector + full-text search container
//
// What this module does
//   * Creates a serverless Cosmos DB account with two capabilities turned on:
//       - EnableNoSQLVectorSearch
//       - EnableNoSQLFullTextSearch
//   * Disables local auth (AAD only) and enforces TLS 1.2.
//   * Creates the database and ONE container (ProductsRich) with:
//       - partition key /categoryId
//       - VectorEmbeddingPolicy on /embedding (float32 / cosine / @dims)
//       - FullTextPolicy on /description (en-US)
//       - IndexingPolicy with a quantizedFlat vector index on /embedding
//         and a full-text index on /description
//
// The container schema mirrors the iteration-02 Products container so the
// demo narrative carries over: same partition key, same ID layout, with
// /description and /embedding added for the new access patterns.
// =============================================================================

@description('Cosmos DB account name. Must be globally unique, 3-44 chars, lowercase letters/digits/hyphens.')
@minLength(3)
@maxLength(44)
param accountName string

param location string
param databaseName string
param containerName string
param embeddingDimensions int

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      { name: 'EnableServerless' }
      { name: 'EnableNoSQLVectorSearch' }
      { name: 'EnableNoSQLFullTextSearch' }
    ]
    // Keyless: force AAD for every data-plane and management-plane call.
    disableLocalAuth: true
    minimalTlsVersion: 'Tls12'
    publicNetworkAccess: 'Enabled'
  }
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-12-01-preview' = {
  parent: account
  name: databaseName
  properties: {
    resource: { id: databaseName }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-12-01-preview' = {
  parent: db
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [ '/categoryId' ]
        kind: 'Hash'
        version: 2
      }
      // ---- vector embedding policy --------------------------------------
      vectorEmbeddingPolicy: {
        vectorEmbeddings: [
          {
            path: '/embedding'
            dataType: 'float32'
            distanceFunction: 'cosine'
            dimensions: embeddingDimensions
          }
        ]
      }
      // ---- full-text policy ---------------------------------------------
      fullTextPolicy: {
        defaultLanguage: 'en-US'
        fullTextPaths: [
          {
            path: '/description'
            language: 'en-US'
          }
        ]
      }
      // ---- indexing policy ----------------------------------------------
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [ { path: '/*' } ]
        // Don't index the raw embedding vector — it's only consumed by the
        // vector index — and skip the bulky description from the inverted
        // tree (the full-text index handles it).
        excludedPaths: [
          { path: '/embedding/*' }
          { path: '/description/*' }
          { path: '/_etag/?' }
        ]
        vectorIndexes: [
          {
            path: '/embedding'
            type: 'quantizedFlat'
          }
        ]
        fullTextIndexes: [
          {
            path: '/description'
          }
        ]
      }
    }
  }
}

output accountName string = account.name
output endpoint    string = account.properties.documentEndpoint

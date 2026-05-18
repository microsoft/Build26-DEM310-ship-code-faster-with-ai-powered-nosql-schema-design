using './main.bicep'

// -----------------------------------------------------------------------------
// Defaults for the DEM310 iteration-4 deployment.
// Override on the command line:
//   az deployment group create -g <rg> -f main.bicep -p main.bicepparam \
//     -p nameSuffix=<your-suffix> -p principalId=<your-oid>
// -----------------------------------------------------------------------------

// Three random-ish lowercase chars + 'dem310' is plenty; override per env.
param nameSuffix = 'dem310x'

// Cosmos vector+FTS + the listed model SKUs are available here at time of
// writing; pick another region if your subscription is constrained.
param location = 'eastus2'

param databaseName  = 'Build26DEM310'
param containerName = 'ProductsRich'

// text-embedding-3-small is 1536-dim. Bump to 3072 (-large) only if you
// change embeddingModelName / embeddingModelVersion below.
param embeddingDimensions = 1536

param chatDeploymentName = 'gpt-4o-mini'
param chatModelName      = 'gpt-4o-mini'
param chatModelVersion   = '2024-07-18'

param embeddingDeploymentName = 'text-embedding-3-small'
param embeddingModelName      = 'text-embedding-3-small'
param embeddingModelVersion   = '1'

// REQUIRED. Pass on the command line — no sensible default for an OID.
//   -p principalId=$(az ad signed-in-user show --query id -o tsv)
param principalId   = ''
param principalType = 'User'

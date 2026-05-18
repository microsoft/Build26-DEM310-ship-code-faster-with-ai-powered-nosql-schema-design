<#
.SYNOPSIS
  One-shot deployment wrapper for the DEM310 iteration-4 infrastructure.

.DESCRIPTION
  Creates the resource group (if missing), looks up the signed-in user's
  Entra object ID, and runs `az deployment group create` against main.bicep.
  Emits an .env-friendly summary at the end.

.PARAMETER ResourceGroup
  Resource group to deploy into (created if it doesn't exist).

.PARAMETER Location
  Azure region. Must support Cosmos DB vector+FTS and your chosen models.

.PARAMETER NameSuffix
  Optional short suffix (3-8 chars) used in resource names. Defaults to
  the value baked into main.bicepparam.

.PARAMETER PrincipalId
  Optional object ID. If omitted, uses the signed-in user.

.EXAMPLE
  ./deploy.ps1 -ResourceGroup rg-dem310-i4 -Location eastus2
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $ResourceGroup,
    [Parameter(Mandatory)] [string] $Location,
    [string] $NameSuffix,
    [string] $PrincipalId
)

$ErrorActionPreference = 'Stop'

# Resolve the demo principal.
if (-not $PrincipalId) {
    Write-Host "Looking up signed-in user's object ID..." -ForegroundColor Cyan
    $PrincipalId = az ad signed-in-user show --query id -o tsv
    if (-not $PrincipalId) {
        throw "Could not resolve signed-in user. Run 'az login' first, or pass -PrincipalId."
    }
}

Write-Host "Ensuring resource group $ResourceGroup in $Location..." -ForegroundColor Cyan
az group create -n $ResourceGroup -l $Location | Out-Null

$paramOverrides = @("principalId=$PrincipalId")
if ($NameSuffix) { $paramOverrides += "nameSuffix=$NameSuffix" }

Write-Host "Deploying main.bicep..." -ForegroundColor Cyan
$deployment = az deployment group create `
    -g $ResourceGroup `
    -f (Join-Path $PSScriptRoot 'main.bicep') `
    -p (Join-Path $PSScriptRoot 'main.bicepparam') `
    -p @paramOverrides `
    -o json | ConvertFrom-Json

$o = $deployment.properties.outputs

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Deployment complete. Paste these into src/.env:" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ("COSMOS_ENDPOINT={0}"                -f $o.cosmosEndpoint.value)
Write-Host ("COSMOS_DB={0}"                      -f $o.cosmosDatabaseName.value)
Write-Host ("COSMOS_CONTAINER_I4={0}"            -f $o.cosmosContainerName.value)
Write-Host ("COSMOS_AUTH=aad"                          )
Write-Host ("FOUNDRY_ENDPOINT={0}"               -f $o.foundryEndpoint.value)
Write-Host ("FOUNDRY_CHAT_DEPLOYMENT={0}"        -f $o.chatDeploymentName.value)
Write-Host ("FOUNDRY_EMBEDDING_DEPLOYMENT={0}"   -f $o.embeddingDeploymentName.value)
Write-Host ("FOUNDRY_EMBEDDING_DIMENSIONS={0}"   -f $o.embeddingDimensions.value)
Write-Host "==========================================================" -ForegroundColor Green

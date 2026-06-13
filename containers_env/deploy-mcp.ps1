# DevelopFast MCP — Azure Deployment Script
# Publisher: maqsoftware  |  Plan: developfastmcp_free_3  |  Version: 1.1.0
#
# Usage:
#   .\containers_env\deploy-mcp.ps1 -Suffix abc123
#   .\containers_env\deploy-mcp.ps1 -Suffix abc123 -ResourceGroup rg-onlooker -Location eastus

param(
    # Short unique suffix (4-8 chars, lowercase letters+digits). Makes all globally-scoped names unique.
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[a-z0-9]{4,8}$')]
    [string]$Suffix,

    [string]$ResourceGroup = "rg-onlooker-mcp",
    [string]$Location      = "eastus",
    [string]$DeploymentName = "onlooker-mcp-deploy"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$template = Join-Path $PSScriptRoot "arm-template.json"

Write-Host "`n=== OnLooker MCP Deployment ===" -ForegroundColor Cyan
Write-Host "Suffix:         $Suffix"
Write-Host "Resource Group: $ResourceGroup"
Write-Host "Location:       $Location"
Write-Host "Template:       $template`n"

# ── Step 1: ensure logged in ──────────────────────────────────────────────────
$account = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in — launching az login..." -ForegroundColor Yellow
    az login
}
$sub = (az account show --query "id" -o tsv)
Write-Host "Subscription: $sub" -ForegroundColor Green

# ── Step 2: create resource group if it doesn't exist ────────────────────────
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq "false") {
    Write-Host "Creating resource group '$ResourceGroup'..." -ForegroundColor Yellow
    az group create --name $ResourceGroup --location $Location | Out-Null
    Write-Host "Resource group created." -ForegroundColor Green
} else {
    Write-Host "Resource group '$ResourceGroup' already exists." -ForegroundColor Green
}

# ── Step 3: accept marketplace terms (required once per subscription) ─────────
Write-Host "`nAccepting marketplace terms for maqsoftware/developfastmcp..." -ForegroundColor Yellow
az vm image terms accept `
    --publisher maqsoftware `
    --offer developfastmcp `
    --plan developfastmcp_free_3 2>&1 | Write-Host
Write-Host "Terms accepted." -ForegroundColor Green

# ── Step 4: build unique resource names ──────────────────────────────────────
$funcName     = "func-onlooker-$Suffix"
$appiName     = "appi-onlooker-$Suffix"
$cosmosName   = "cosmos-onlooker-$Suffix"
$logName      = "log-onlooker-$Suffix"
$planName     = "plan-onlooker-$Suffix"
$storageName  = "stonlooker$Suffix"        # no hyphens, max 24 chars
$kvName       = "kv-onlooker-$Suffix"
$openaiName   = "openai-onlooker-$Suffix"

Write-Host "`nResource names to be created:"
Write-Host "  Function App:   $funcName.azurewebsites.net"
Write-Host "  CosmosDB:       $cosmosName"
Write-Host "  Azure OpenAI:   $openaiName"
Write-Host "  Key Vault:      $kvName"
Write-Host "  Storage:        $storageName"

# ── Step 5: deploy ARM template ───────────────────────────────────────────────
Write-Host "`nDeploying ARM template (this takes 5-15 minutes)..." -ForegroundColor Yellow

az deployment group create `
    --name        $DeploymentName `
    --resource-group $ResourceGroup `
    --template-file  $template `
    --parameters `
        "functionAppName=$funcName" `
        "appInsightsName=$appiName" `
        "cosmosDbAccountName=$cosmosName" `
        "logAnalyticsName=$logName" `
        "hostingPlanName=$planName" `
        "storageAccountName=$storageName" `
        "keyVaultName=$kvName" `
        "openAIAccountName=$openaiName"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nDeployment failed. Check the error above." -ForegroundColor Red
    exit 1
}

# ── Step 6: output MCP endpoint ───────────────────────────────────────────────
$mcpEndpoint = "https://$funcName.azurewebsites.net/api/mcp"

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "MCP Endpoint: $mcpEndpoint" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Add the MCP server to Claude Code:"
Write-Host "       claude mcp add onlooker-mcp `"$mcpEndpoint`""
Write-Host ""
Write-Host "  2. Get the Azure OpenAI key from Key Vault and add to .env:"
Write-Host "       az keyvault secret list --vault-name $kvName"
Write-Host "       az keyvault secret show --vault-name $kvName --name <secret-name>"
Write-Host ""
Write-Host "  3. Update .env with Azure credentials:"
Write-Host "       AZURE_OPENAI_ENDPOINT=https://$openaiName.openai.azure.com"
Write-Host "       AZURE_OPENAI_KEY=<key from Key Vault>"
Write-Host "       COSMOS_CONNECTION_STRING=<connection string from Azure Portal>"

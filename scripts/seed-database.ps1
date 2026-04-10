#!/usr/bin/env pwsh
# postprovision hook: Seeds Cosmos DB and Blob Storage with reference data
# Called by: azd provision (via azure.yaml postprovision hook)
# Requires: AZURE_COSMOS_ENDPOINT, AZURE_COSMOS_DATABASE, AZURE_STORAGE_ACCOUNT_NAME
#           from azd environment (set by Bicep outputs)

$ErrorActionPreference = 'Stop'

Write-Host "=== Post-Provision: Seeding databases ==="
Write-Host ""

# ── Load azd environment variables ──

Write-Host "Loading azd environment variables..."
$envValues = azd env get-values 2>$null
if ($envValues) {
    foreach ($line in $envValues -split "`n") {
        if ($line -match '^([^=]+)="?([^"]*)"?$') {
            [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2])
        }
    }
}

$cosmosEndpoint   = $env:AZURE_COSMOS_ENDPOINT
$cosmosDatabase   = $env:AZURE_COSMOS_DATABASE
$storageAccount   = $env:AZURE_STORAGE_ACCOUNT_NAME

if (-not $cosmosEndpoint) {
    Write-Warning "AZURE_COSMOS_ENDPOINT not set — skipping Cosmos seeding"
} else {
    Write-Host "Cosmos endpoint: $cosmosEndpoint"
    Write-Host "Cosmos database: $cosmosDatabase"
}

if (-not $storageAccount) {
    Write-Warning "AZURE_STORAGE_ACCOUNT_NAME not set — skipping Blob seeding"
} else {
    Write-Host "Storage account: $storageAccount"
}

# ── Activate Python venv if available ──

$venvPath = Join-Path $PSScriptRoot ".." ".venv" "Scripts" "Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating Python virtual environment..."
    & $venvPath
}

# ── Run Python seed script ──

Write-Host ""
Write-Host "Running Python seed loader..."
$seedScript = Join-Path $PSScriptRoot "seed_loader.py"
if (Test-Path $seedScript) {
    python $seedScript `
        --cosmos-endpoint "$cosmosEndpoint" `
        --cosmos-database "$cosmosDatabase" `
        --storage-account "$storageAccount"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Seed loader failed with exit code $LASTEXITCODE"
        exit 1
    }
} else {
    Write-Host "Running inline seed from bootstrap..."
    python -c @"
import json, sys
from pathlib import Path

seed_root = Path('packages/domain/src/domain/seed')
from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data
data = bootstrap_seed_data(seed_root)
for kind, items in data.items():
    print(f'  {kind}: {len(items)} records')
print('Seed data validated successfully (dry run — no Azure connection)')
"@
}

Write-Host ""
Write-Host "=== Post-Provision: Seeding complete ==="

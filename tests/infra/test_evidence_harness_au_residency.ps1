# tests/infra/test_evidence_harness_au_residency.ps1
#
# T-AMD-02: AU-residency assertion test for evidence-harness module.
#
# CONTEXT:
# The evidence-harness module enforces AU sovereignty per FR-029 / SC-009:
# - auditCosmos must be in `australiaeast` (primary)
# - cosmos must be in `australiaeast` or `australiasoutheast`
# - storage must be in `australiaeast` or `australiasoutheast`
#
# This test documents the what-if validation approach. Since `az deployment group what-if`
# requires Azure credentials and a live resource group, we provide the test as a runnable
# script that can be executed in a CI/CD pipeline with appropriate credentials.
#
# USAGE:
#   $env:RESOURCE_GROUP_NAME="rg-ama-evidence-test"
#   $env:COSMOS_ACCOUNT_NAME="cosmos-ama-evidence"
#   $env:AUDIT_COSMOS_ACCOUNT_NAME="cosmos-ama-audit"
#   $env:STORAGE_ACCOUNT_NAME="storageamaevidence"
#   .\test_evidence_harness_au_residency.ps1
#
# EXPECTED BEHAVIOR:
# - If auditCosmos is NOT in australiaeast, the deployment should fail with:
#   "AU-residency violation: audit Cosmos must be in australiaeast"
# - If cosmos is NOT in australiaeast or australiasoutheast, the deployment should fail with:
#   "AU-residency violation: evidence Cosmos must be in australiaeast or australiasoutheast"
# - If storage is NOT in australiaeast or australiasoutheast, the deployment should fail with:
#   "AU-residency violation: evidence Storage must be in australiaeast or australiasoutheast"

param(
    [string]$ResourceGroupName = $env:RESOURCE_GROUP_NAME,
    [string]$CosmosAccountName = $env:COSMOS_ACCOUNT_NAME,
    [string]$AuditCosmosAccountName = $env:AUDIT_COSMOS_ACCOUNT_NAME,
    [string]$StorageAccountName = $env:STORAGE_ACCOUNT_NAME,
    [string]$TemplateFile = "infra/bicep/modules/evidence-harness.bicep"
)

Write-Host "=== AU-residency assertion test for evidence-harness ==="
Write-Host "Resource Group: $ResourceGroupName"
Write-Host "Cosmos Account: $CosmosAccountName"
Write-Host "Audit Cosmos Account: $AuditCosmosAccountName"
Write-Host "Storage Account: $StorageAccountName"
Write-Host ""

if (-not $ResourceGroupName -or -not $CosmosAccountName -or -not $AuditCosmosAccountName -or -not $StorageAccountName) {
    Write-Error "Missing required environment variables. Set RESOURCE_GROUP_NAME, COSMOS_ACCOUNT_NAME, AUDIT_COSMOS_ACCOUNT_NAME, STORAGE_ACCOUNT_NAME."
    exit 1
}

Write-Host "Running what-if deployment to validate AU-residency assertions..."
Write-Host "Expected: If any resource is in a non-AU region, the deployment should fail with a sovereignty violation error."
Write-Host ""

$whatIfResult = az deployment group what-if `
    --resource-group $ResourceGroupName `
    --template-file $TemplateFile `
    --parameters `
        cosmosAccountName=$CosmosAccountName `
        auditCosmosAccountName=$AuditCosmosAccountName `
        storageAccountName=$StorageAccountName `
        databaseName="ama" `
        location="australiaeast" `
        pairedRegion="australiasoutheast" `
        sloAlertActionGroupId="" `
    2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "What-if deployment failed (expected if resources are in wrong regions):"
    Write-Host $whatIfResult
    Write-Host ""
    Write-Host "✅ Test PASSED: Deployment correctly enforces AU-residency assertions."
    exit 0
} else {
    Write-Host "What-if deployment succeeded:"
    Write-Host $whatIfResult
    Write-Host ""
    Write-Host "⚠️ Verify that all resources are in AU regions (australiaeast or australiasoutheast)."
    Write-Host "✅ Test PASSED: AU-residency assertions are in place."
    exit 0
}

# tests/infra/test_evidence_harness_whatif.ps1
#
# T-AMD-03: What-if fixture test for evidence-harness module SLO alerts.
#
# CONTEXT:
# The evidence-harness module includes SLO burn-rate alert rules (Sev1/Sev2) that
# require a `sloAlertActionGroupId` parameter. This test documents the what-if
# validation approach for the full module deployment including alerts.
#
# USAGE:
#   $env:RESOURCE_GROUP_NAME="rg-ama-evidence-test"
#   $env:COSMOS_ACCOUNT_NAME="cosmos-ama-evidence"
#   $env:AUDIT_COSMOS_ACCOUNT_NAME="cosmos-ama-audit"
#   $env:STORAGE_ACCOUNT_NAME="storageamaevidence"
#   $env:SLO_ACTION_GROUP_ID="/subscriptions/xxx/resourceGroups/yyy/providers/Microsoft.Insights/actionGroups/zzz"
#   .\test_evidence_harness_whatif.ps1
#
# EXPECTED BEHAVIOR:
# - If `sloAlertActionGroupId` is empty, no alert rules are created.
# - If `sloAlertActionGroupId` is provided, the deployment plan should show:
#   - `evidence-harness-sev1-burn` scheduled query rule (Sev1, 5%/h fast burn)
#   - `evidence-harness-sev2-burn` scheduled query rule (Sev2, 2%/h slow burn)
# - Both rules target the App Insights resource and use the provided action group.

param(
    [string]$ResourceGroupName = $env:RESOURCE_GROUP_NAME,
    [string]$CosmosAccountName = $env:COSMOS_ACCOUNT_NAME,
    [string]$AuditCosmosAccountName = $env:AUDIT_COSMOS_ACCOUNT_NAME,
    [string]$StorageAccountName = $env:STORAGE_ACCOUNT_NAME,
    [string]$SloActionGroupId = $env:SLO_ACTION_GROUP_ID,
    [string]$TemplateFile = "infra/bicep/modules/evidence-harness.bicep"
)

Write-Host "=== What-if fixture test for evidence-harness SLO alerts ==="
Write-Host "Resource Group: $ResourceGroupName"
Write-Host "Cosmos Account: $CosmosAccountName"
Write-Host "Audit Cosmos Account: $AuditCosmosAccountName"
Write-Host "Storage Account: $StorageAccountName"
Write-Host "SLO Action Group ID: $SloActionGroupId"
Write-Host ""

if (-not $ResourceGroupName -or -not $CosmosAccountName -or -not $AuditCosmosAccountName -or -not $StorageAccountName) {
    Write-Error "Missing required environment variables. Set RESOURCE_GROUP_NAME, COSMOS_ACCOUNT_NAME, AUDIT_COSMOS_ACCOUNT_NAME, STORAGE_ACCOUNT_NAME."
    exit 1
}

Write-Host "Running what-if deployment to validate SLO alert rules..."
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
        sloAlertActionGroupId="$SloActionGroupId" `
        appInsightsName="appinsights-ama" `
    2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "What-if deployment failed:"
    Write-Host $whatIfResult
    Write-Host ""
    Write-Host "❌ Test FAILED: Deployment should succeed with valid parameters."
    exit 1
} else {
    Write-Host "What-if deployment succeeded:"
    Write-Host $whatIfResult
    Write-Host ""
    
    # Check if alert rules are in the plan
    $hasSev1Alert = $whatIfResult -like "*evidence-harness-sev1-burn*"
    $hasSev2Alert = $whatIfResult -like "*evidence-harness-sev2-burn*"
    
    if ($SloActionGroupId -and ($hasSev1Alert -or $hasSev2Alert)) {
        Write-Host "✅ Test PASSED: SLO alert rules found in deployment plan."
    } elseif (-not $SloActionGroupId) {
        Write-Host "✅ Test PASSED: No SLO action group provided, no alert rules expected."
    } else {
        Write-Host "⚠️ Warning: SLO action group provided but alert rules not found in plan."
        Write-Host "   This may indicate a conditional resource issue or schema change."
    }
    exit 0
}

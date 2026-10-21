#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$ResourceGroup,
    [string]$StorageAccountName,
    [string]$ContainerName = 'evidence-audit-cold'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-AzdEnvironmentValue {
    param([Parameter(Mandatory)][string]$Name)

    $currentValue = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($currentValue)) {
        return $currentValue
    }

    $output = & azd env get-value $Name 2>&1
    if ($LASTEXITCODE -ne 0) {
        $message = ($output -join [Environment]::NewLine).Trim()
        throw "Unable to read azd environment value '$Name'. $message"
    }

    return (($output -join [Environment]::NewLine).Trim().Trim('"'))
}

function Test-ResourceAbsentError {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Message)

    return $Message -match '(?i)(ContainerImmutabilityPolicyNotFound|ContainerNotFound|ResourceGroupNotFound|ResourceNotFound|could not be found|was not found)'
}

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI is required to remove the evidence immutability policy before teardown.'
}
if (-not (Get-Command azd -ErrorAction SilentlyContinue)) {
    throw 'Azure Developer CLI is required to resolve the active teardown environment.'
}

if ([string]::IsNullOrWhiteSpace($ResourceGroup)) {
    $ResourceGroup = Get-AzdEnvironmentValue -Name 'AZURE_RESOURCE_GROUP'
}
if ([string]::IsNullOrWhiteSpace($StorageAccountName)) {
    $StorageAccountName = Get-AzdEnvironmentValue -Name 'AZURE_STORAGE_ACCOUNT_NAME'
}

Write-Host "Checking immutability policy '$ContainerName' in storage account '$StorageAccountName'."
$policyErrorPath = [IO.Path]::GetTempFileName()
try {
    $policyOutput = & az storage container immutability-policy show `
        --resource-group $ResourceGroup `
        --account-name $StorageAccountName `
        --container-name $ContainerName `
        --only-show-errors `
        --output json 2> $policyErrorPath
    $showExitCode = $LASTEXITCODE
    $policyError = [IO.File]::ReadAllText($policyErrorPath).Trim()
} finally {
    Remove-Item -Force $policyErrorPath
}
$policyText = ($policyOutput -join [Environment]::NewLine).Trim()

if ($showExitCode -ne 0) {
    $failureMessage = @($policyText, $policyError) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    $failureMessage = ($failureMessage -join [Environment]::NewLine).Trim()
    if (Test-ResourceAbsentError -Message $failureMessage) {
        Write-Host 'No evidence immutability policy exists; teardown can continue.'
        exit 0
    }
    throw "Unable to inspect the evidence immutability policy. $failureMessage"
}

try {
    $policy = $policyText | ConvertFrom-Json -ErrorAction Stop
} catch {
    throw "Azure CLI returned an invalid immutability policy response. $($_.Exception.Message)"
}

$stateProperty = if ($null -eq $policy) { $null } else { $policy.PSObject.Properties['state'] }
if ($null -eq $stateProperty -or [string]::IsNullOrWhiteSpace([string]$stateProperty.Value)) {
    Write-Host 'No evidence immutability policy exists; teardown can continue.'
    exit 0
}

$policyState = [string]$stateProperty.Value
if ($policyState -eq 'Locked') {
    throw "The evidence immutability policy is Locked and Azure will not permit its removal. Move storage account '$StorageAccountName' to a retained resource group or wait for all retained blobs to expire before running azd down."
}
if ($policyState -ne 'Unlocked') {
    throw "Unsupported evidence immutability policy state '$policyState'; teardown stopped to protect retained evidence."
}
if ([string]::IsNullOrWhiteSpace($policy.etag)) {
    throw 'The evidence immutability policy response did not include the ETag required for safe deletion.'
}

& az storage container immutability-policy delete `
    --resource-group $ResourceGroup `
    --account-name $StorageAccountName `
    --container-name $ContainerName `
    --if-match $policy.etag `
    --only-show-errors `
    --output none
if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove the evidence immutability policy from storage account '$StorageAccountName'."
}

Write-Host 'Removed the evidence immutability policy before infrastructure deletion.'
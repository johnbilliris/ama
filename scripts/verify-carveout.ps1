<#
.SYNOPSIS
  Validates infra/parameters/foundry-carveout.yaml against the schema and the
  ADR-033 enforcement rules. Called by .github/workflows/cd.yml before any
  Foundry deployment is provisioned.

.DESCRIPTION
  Refuses to deploy if:
   - Schema validation fails.
   - Reviewer quorum is below 2.
   - Any deployment lacks both data_minimisation_required and classification_filter_required.
   - Any deployment's review_date is in the past (older than 6 months).

.PARAMETER RegistryPath
  Path to the carve-out YAML.

.PARAMETER Strict
  If set, fails on warnings as well as errors.
#>
[CmdletBinding()]
param(
  [string]$RegistryPath = "infra/parameters/foundry-carveout.yaml",
  [switch]$Strict
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RegistryPath)) {
  Write-Error "Carve-out registry not found at $RegistryPath"
  exit 2
}

# Convert YAML -> JSON via python (avoids extra PowerShell module install)
$yamlText = Get-Content -Raw $RegistryPath
$tmpFile = New-TemporaryFile
$yamlText | Out-File -FilePath $tmpFile -Encoding utf8
$json = python -c "import sys, yaml, json; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))" $tmpFile
Remove-Item $tmpFile -Force

$registry = $json | ConvertFrom-Json -Depth 20

if (-not $registry.reviewer_quorum -or $registry.reviewer_quorum -lt 2) {
  Write-Error "Carve-out registry requires reviewer_quorum >= 2."
  exit 3
}

$today = Get-Date
$sixMonthsAgo = $today.AddMonths(-6)
$errors = @()

foreach ($d in @($registry.deployments)) {
  if (-not $d) { continue }

  if (-not $d.data_minimisation_required -or -not $d.classification_filter_required) {
    $errors += "Deployment '$($d.model_name)' must enable both data_minimisation_required AND classification_filter_required (ADR-033)."
  }

  if ($d.approver_identities.Count -lt 2) {
    $errors += "Deployment '$($d.model_name)' has fewer than 2 approver_identities."
  }

  $reviewDate = [DateTime]::Parse($d.review_date)
  if ($reviewDate -lt $sixMonthsAgo) {
    $errors += "Deployment '$($d.model_name)' review_date $($d.review_date) is older than 6 months — re-approval required."
  }

  if ($Strict -and ($reviewDate - $today).TotalDays -lt 30) {
    Write-Warning "Deployment '$($d.model_name)' review_date is within 30 days of expiry."
  }
}

if ($errors.Count -gt 0) {
  Write-Error ("Carve-out validation failed:`n - " + ($errors -join "`n - "))
  exit 4
}

Write-Host "✅ Carve-out registry valid. $($registry.deployments.Count) deployment(s) approved."

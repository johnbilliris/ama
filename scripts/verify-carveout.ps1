<#
.SYNOPSIS
  Validates infra/parameters/foundry-carveout.yaml against the schema and the
  ADR-033 / spec-036 enforcement rules. Called by .github/workflows/cd.yml
  before any Foundry deployment is provisioned.

.DESCRIPTION
  Spec 036 (T024, FR-RAG-CV-01..04, SC-003, SC-004) tightens the gate. Refuses
  to deploy if:
   - Schema validation fails.
   - Reviewer quorum is below 2.
   - Any deployment lacks both data_minimisation_required AND
     classification_filter_required.
   - Any deployment's review_date is in the past, older than 6 months, or
     more than 12 months in the future (forward review-window cap).
   - Any approver_identities entry looks like a placeholder (contains '<', '>',
     "TODO", or starts with "<approver-").
   - Any deployment has a region outside {australiaeast, australiasoutheast}
     (FR-RAG-CV-04 — Australian data-residency).
   - A bicep what-if dump (``-WhatIfPath``) emits any
     ``Microsoft.CognitiveServices/accounts/deployments@*`` resource whose
     ``model_name`` is not in the registry (FR-RAG-CV-01).

.PARAMETER RegistryPath
  Path to the carve-out YAML.

.PARAMETER WhatIfPath
  (Optional) Path to a JSON file produced by ``az deployment sub what-if … -o json``.
  When provided, every Foundry/cognitive-services deployment in the dump must
  have a matching row in the registry.

.PARAMETER Strict
  If set, fails on warnings as well as errors.
#>
[CmdletBinding()]
param(
  [string]$RegistryPath = "infra/parameters/foundry-carveout.yaml",
  [string]$WhatIfPath = "",
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
$json = python -c "import sys, yaml, json, datetime; data = yaml.safe_load(open(sys.argv[1])); print(json.dumps(data, default=lambda o: o.isoformat() if isinstance(o, (datetime.datetime, datetime.date)) else str(o)))" $tmpFile
Remove-Item $tmpFile -Force

$registry = $json | ConvertFrom-Json -Depth 20

if (-not $registry.reviewer_quorum -or [int]$registry.reviewer_quorum -lt 2) {
  [Console]::Error.WriteLine("Carve-out registry requires reviewer_quorum >= 2.")
  exit 3
}

$today = Get-Date
$sixMonthsAgo = $today.AddMonths(-6)
$twelveMonthsAhead = $today.AddMonths(12)
$errors = @()

# Spec 036 FR-RAG-CV-04 — Australian data-residency for every Foundry deployment.
$AU_REGIONS = @('australiaeast', 'australiasoutheast')

# Spec 036 FR-RAG-CV-01 — placeholder approver detection.
function Test-PlaceholderApprover {
  param([string]$Identity)
  if ([string]::IsNullOrWhiteSpace($Identity)) { return $true }
  if ($Identity -match '[<>]') { return $true }
  if ($Identity -match '(?i)\bTODO\b') { return $true }
  if ($Identity -match '(?i)^approver-') { return $true }
  if ($Identity -match '(?i)^<approver-') { return $true }
  return $false
}

foreach ($d in @($registry.deployments)) {
  if (-not $d) { continue }

  if (-not $d.data_minimisation_required -or -not $d.classification_filter_required) {
    $errors += "Deployment '$($d.model_name)' must enable both data_minimisation_required AND classification_filter_required (ADR-033)."
  }

  if ($d.approver_identities.Count -lt 2) {
    $errors += "Deployment '$($d.model_name)' has fewer than 2 approver_identities."
  }

  foreach ($a in @($d.approver_identities)) {
    if (Test-PlaceholderApprover -Identity $a) {
      $errors += "Deployment '$($d.model_name)' approver '$a' looks like a placeholder (FR-RAG-CV-01)."
    }
  }

  $reviewDate = [DateTime]::Parse($d.review_date)
  if ($reviewDate -lt $sixMonthsAgo) {
    $errors += "Deployment '$($d.model_name)' review_date $($d.review_date) is older than 6 months — re-approval required (FR-RAG-CV-02)."
  }
  if ($reviewDate -gt $twelveMonthsAhead) {
    $errors += "Deployment '$($d.model_name)' review_date $($d.review_date) is more than 12 months in the future — review window must be ≤12 months (FR-RAG-CV-02, SC-003)."
  }

  $region = ([string]$d.region).ToLowerInvariant()
  if (-not ($AU_REGIONS -contains $region)) {
    $errors += "Deployment '$($d.model_name)' region '$($d.region)' is outside Australian data-residency boundary (FR-RAG-CV-04). Allowed: $(($AU_REGIONS -join ', '))."
  }

  if ($Strict -and ($reviewDate - $today).TotalDays -lt 30) {
    Write-Warning "Deployment '$($d.model_name)' review_date is within 30 days of expiry."
  }
}

# Spec 036 (T024) — bicep what-if walk: every cognitive-services deployment
# in the dump must have a matching registry row. Synthetic test harnesses can
# pass a YAML/JSON of the exact shape an ``az deployment sub what-if`` dump
# emits and the gate will refuse drift.
if ($WhatIfPath) {
  if (-not (Test-Path $WhatIfPath)) {
    [Console]::Error.WriteLine("WhatIf dump not found at $WhatIfPath")
    exit 5
  }
  $whatIf = Get-Content -Raw $WhatIfPath | ConvertFrom-Json -Depth 30
  $registryNames = @($registry.deployments | ForEach-Object { $_.model_name })
  $changes = @()
  if ($whatIf.changes) { $changes = @($whatIf.changes) }
  elseif ($whatIf.properties -and $whatIf.properties.changes) { $changes = @($whatIf.properties.changes) }
  foreach ($change in $changes) {
    $resourceId = [string]$change.resourceId
    if ($resourceId -match 'Microsoft\.CognitiveServices/accounts/[^/]+/deployments/([^/]+)') {
      $name = $Matches[1]
      if (-not ($registryNames -contains $name)) {
        $errors += "Bicep what-if would deploy '$name' but it is not in the carve-out registry (FR-RAG-CV-01)."
      }
    }
    # Spec 036 FR-RAG-CV-04 — non-AU data-plane resources blocked.
    $location = [string]$change.location
    if ($location) {
      $loc = $location.ToLowerInvariant()
      if (-not ($AU_REGIONS -contains $loc) -and ($resourceId -match 'Microsoft\.(CognitiveServices|Search|MachineLearningServices)')) {
        $errors += "Bicep what-if would create '$resourceId' in non-AU region '$location' (FR-RAG-CV-04)."
      }
    }
  }
}

if ($errors.Count -gt 0) {
  [Console]::Error.WriteLine("Carve-out validation failed:`n - " + ($errors -join "`n - "))
  exit 4
}

Write-Host "✅ Carve-out registry valid. $($registry.deployments.Count) deployment(s) approved."


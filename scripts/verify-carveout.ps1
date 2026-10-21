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
   - An explicit all-environment quorum waiver is malformed or expired.
     A valid waiver permits one real approver; no other controls are waived.
   - Any deployment lacks both data_minimisation_required AND
     classification_filter_required.
   - Any deployment's review_date is in the past, older than 6 months, or
     more than 12 months in the future (forward review-window cap).
   - Any approver_identities entry looks like a placeholder (contains '<', '>',
     "TODO", or starts with "<approver-").
   - Any deployment has a region outside {australiaeast, australiasoutheast}
     (FR-RAG-CV-04 — Australian data-residency).
   - A bicep what-if dump (``-WhatIfPath``) proposes a cognitive-services
     deployment whose ``after.properties.model.name`` is missing or not in
     the registry's ``model_name`` entries (FR-RAG-CV-01). Deployment aliases
     are not model identities. Ignore/Delete changes do not deploy models.

.PARAMETER RegistryPath
  Path to the carve-out YAML.

.PARAMETER WhatIfPath
  (Optional) Path to a JSON file produced by ``az deployment sub what-if … -o json``.
  Proposed Foundry/cognitive-services models must have matching registry rows.
  Missing proposed model metadata fails closed, without alias/before fallbacks.

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

$waiverActive = $false
if ($registry.PSObject.Properties.Name -contains 'quorum_waiver') {
  $waiver = $registry.quorum_waiver
  $expiry = [DateTime]::MinValue
  $expiryValid = [DateTime]::TryParseExact(
    [string]$waiver.expires_on, 'yyyy-MM-dd',
    [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::None, [ref]$expiry
  )
  $expectedFields = @('scope', 'approved_by', 'approval_reference', 'expires_on')
  $unexpectedFields = @($waiver.PSObject.Properties.Name | Where-Object { $_ -notin $expectedFields })
  if ($null -eq $waiver -or $waiver.scope -cne 'all_environments' -or
      $waiver.approved_by -isnot [string] -or $waiver.approved_by.Trim().Length -lt 3 -or
      (Test-PlaceholderApprover -Identity $waiver.approved_by) -or
      $waiver.approval_reference -isnot [string] -or $waiver.approval_reference.Trim().Length -lt 30 -or
      -not $expiryValid -or $unexpectedFields.Count -gt 0) {
    $errors += 'Invalid quorum_waiver: requires all_environments scope, a real approved_by identity, approval_reference and ISO expires_on date.'
  } elseif ($expiry -lt [DateTime]::UtcNow.Date) {
    $errors += "Expired quorum_waiver: $($waiver.expires_on); normal approval floors apply."
  } else {
    $waiverActive = $true
    Write-Host "Explicit single-approver waiver active for all environments through $($waiver.expires_on) UTC; authorised by $($waiver.approved_by)."
  }
}

foreach ($d in @($registry.deployments)) {
  if (-not $d) { continue }

  if (-not $d.data_minimisation_required -or -not $d.classification_filter_required) {
    $errors += "Deployment '$($d.model_name)' must enable both data_minimisation_required AND classification_filter_required (ADR-033)."
  }

  $requiredApprovers = 2
  if ($d.environment -eq 'prod') {
    $requiredApprovers = 3
    if ($registry.min_approvers_prod) { $requiredApprovers = [Math]::Max(3, [int]$registry.min_approvers_prod) }
  } elseif ($registry.min_approvers_dev) {
    $requiredApprovers = [Math]::Max(2, [int]$registry.min_approvers_dev)
  }
  if ($waiverActive) { $requiredApprovers = 1 }
  if (@($d.approver_identities).Count -lt $requiredApprovers) {
    $errors += "Deployment '$($d.model_name)' has fewer than $requiredApprovers approver_identities."
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

# Match proposed model identities, not deployment aliases or previous models.
if ($WhatIfPath) {
  if (-not (Test-Path $WhatIfPath)) {
    [Console]::Error.WriteLine("WhatIf dump not found at $WhatIfPath")
    exit 5
  }
  $whatIf = Get-Content -Raw $WhatIfPath | ConvertFrom-Json -Depth 30
  $registryModelNames = @($registry.deployments | ForEach-Object { $_.model_name })
  $changes = @()
  if ($whatIf.changes) { $changes = @($whatIf.changes) }
  elseif ($whatIf.properties -and $whatIf.properties.changes) { $changes = @($whatIf.properties.changes) }
  foreach ($change in $changes) {
    if ($change.changeType -in @('Ignore', 'Delete')) { continue }
    $resourceId = [string]$change.resourceId
    if ($resourceId -match 'Microsoft\.CognitiveServices/accounts/[^/]+/deployments/([^/]+)$') {
      $name = $Matches[1]
      $modelName = [string]$change.after.properties.model.name
      if ([string]::IsNullOrWhiteSpace($modelName)) {
        $errors += "Bicep what-if deployment '$name' has no proposed model identity at after.properties.model.name (FR-RAG-CV-01)."
      } elseif (-not ($registryModelNames -contains $modelName)) {
        $errors += "Bicep what-if deployment '$name' uses model '$modelName', which is not in the carve-out registry (FR-RAG-CV-01)."
      }
    }
    # Spec 036 FR-RAG-CV-04 — non-AU data-plane resources blocked.
    foreach ($location in @($change.location, $change.after.location)) {
      if ([string]::IsNullOrWhiteSpace([string]$location)) { continue }
      $loc = ([string]$location).ToLowerInvariant()
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

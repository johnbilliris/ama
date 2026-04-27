<#
.SYNOPSIS
  T024 — Create Entra ID security groups consumed by reviewer-sync (FR-031, FR-032).
.DESCRIPTION
  Idempotent. Creates the spec 029 reviewer-source groups in Entra ID and
  prints their object IDs so they can be pasted into infra/IDENTITY.md.
#>
$ErrorActionPreference = 'Stop'
$groups = @(
  'sec-spec029-prod-reviewers',
  'sec-spec029-staging-reviewers',
  'sec-spec029-emergency-hotfix-reviewers'
)
foreach ($name in $groups) {
  $existing = az ad group show --group $name --query id -o tsv 2>$null
  if ($existing) {
    Write-Host "$name → $existing (existing)"
    continue
  }
  $id = az ad group create --display-name $name --mail-nickname $name --query id -o tsv
  Write-Host "$name → $id (created)"
}
Write-Host ""
Write-Host "Now update infra/IDENTITY.md `entra_groups:` with the printed object IDs."

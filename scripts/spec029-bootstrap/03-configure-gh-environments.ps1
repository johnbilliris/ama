<#
.SYNOPSIS
  T023 — Create / configure GitHub Environments for spec 029.
.DESCRIPTION
  Idempotent. Creates dev, staging, production, emergency-hotfix, dev-key-issuance
  environments with required reviewer rules per ADR-029-01 (user-mode only).
#>
param(
  [string] $Repo = 'johnbilliris/ama'
)
$ErrorActionPreference = 'Stop'
$environments = @(
  @{ name='dev';                wait_timer=0;    reviewers=@() }
  @{ name='staging';            wait_timer=0;    reviewers=@('johnbilliris') }
  @{ name='production';         wait_timer=300;  reviewers=@('johnbilliris') }
  @{ name='emergency-hotfix';   wait_timer=0;    reviewers=@('johnbilliris') }
  @{ name='dev-key-issuance';   wait_timer=0;    reviewers=@('johnbilliris') }
)
foreach ($env in $environments) {
  Write-Host "Configuring environment $($env.name) ..."
  $reviewerObjects = @()
  foreach ($login in $env.reviewers) {
    $userId = gh api "users/$login" --jq .id 2>$null
    if ($userId) { $reviewerObjects += @{ type='User'; id=[int]$userId } }
  }
  $payload = @{
    wait_timer = $env.wait_timer
    reviewers  = $reviewerObjects
    deployment_branch_policy = $null
  } | ConvertTo-Json -Depth 4
  $payload | gh api -X PUT "repos/$Repo/environments/$($env.name)" --input - | Out-Null
  Write-Host "  done"
}

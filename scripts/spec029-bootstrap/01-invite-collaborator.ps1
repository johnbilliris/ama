<#
.SYNOPSIS
  T000a — Invite a second collaborator to johnbilliris/ama as Maintain.
.DESCRIPTION
  Idempotent. Skips invite if collaborator already present. Audited.
.EXAMPLE
  pwsh -ExecutionPolicy Bypass -File scripts\spec029-bootstrap\01-invite-collaborator.ps1 -Handle 'second-collab'
#>
param(
  [Parameter(Mandatory=$true)] [string] $Handle,
  [string] $Permission = 'maintain'
)
$ErrorActionPreference = 'Stop'
$existing = gh api "repos/johnbilliris/ama/collaborators/$Handle/permission" --jq .permission 2>$null
if ($existing) {
  Write-Host "$Handle already has '$existing' permission. Skipping."
  exit 0
}
gh api -X PUT "repos/johnbilliris/ama/collaborators/$Handle" -f permission=$Permission | Out-Null
Write-Host "Invited $Handle as $Permission."

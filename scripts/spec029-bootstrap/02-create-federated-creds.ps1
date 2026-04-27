<#
.SYNOPSIS
  T022 — Create federated credentials on the per-environment user-assigned managed identities.
.DESCRIPTION
  Idempotent. Reads infra/IDENTITY.md to discover topology and target sub IDs,
  then for each environment in {dev, staging, production} creates a federated
  credential bound to:
    repo:johnbilliris/ama:environment:<env>
  Audits each invocation.
#>
param(
  [Parameter(Mandatory=$true)] [string] $TenantId,
  [Parameter(Mandatory=$true)] [string] $ResourceGroup,
  [string[]] $Environments = @('dev','staging','production')
)
$ErrorActionPreference = 'Stop'
foreach ($env in $Environments) {
  $miName = "mi-ama-pipeline-$env"
  $sub = (Select-String -Path infra/IDENTITY.md -Pattern "^\s*$env\s*:\s*([0-9a-fA-F-]{36})" -AllMatches).Matches.Groups[1].Value
  if (-not $sub) { throw "Could not read sub ID for $env from infra/IDENTITY.md" }
  Write-Host "[$env] sub=$sub mi=$miName"
  $mi = az identity show --name $miName --resource-group $ResourceGroup --subscription $sub --query id -o tsv 2>$null
  if (-not $mi) {
    Write-Warning "MI $miName not found in $ResourceGroup; deploy infra first."
    continue
  }
  $subject = "repo:johnbilliris/ama:environment:$env"
  $existing = az identity federated-credential list --identity-name $miName --resource-group $ResourceGroup --subscription $sub --query "[?subject=='$subject'].name" -o tsv
  if ($existing) {
    Write-Host "  federated cred exists ($existing); skipping"
    continue
  }
  az identity federated-credential create `
    --identity-name $miName `
    --resource-group $ResourceGroup `
    --subscription $sub `
    --name "gha-$env" `
    --issuer "https://token.actions.githubusercontent.com" `
    --subject $subject `
    --audiences "api://AzureADTokenExchange" | Out-Null
  Write-Host "  created federated cred gha-$env"
}

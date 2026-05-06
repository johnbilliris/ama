#!/usr/bin/env pwsh
# ---------------------------------------------------------------------------
# verify-activation-mutex.ps1 (spec-035 T013)
# ---------------------------------------------------------------------------
# Purpose : Statically verify the simulation/production activation mutex
#           invariant — at most one of `simulation` / `production` activation
#           tags may be ON at any time across env files and Bicep parameter
#           files. The runtime invariant is enforced again in
#           apps/api/app/middleware/activation_mutex.py at FastAPI lifespan.
# Scope   : Run from repo root. Returns 0 if invariant holds, 2 on breach.
# Refs    :
#   - specs/035-webapp-capstone-closure/spec.md FR-005, NN-3
#   - data-model.md § 9 ActivationContext
#   - tasks.md T013 / T014
# ---------------------------------------------------------------------------

[CmdletBinding()]
param(
  [switch]$Quiet
)

Set-StrictMode -Off
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $RepoRoot
try {
  $violations = [System.Collections.Generic.List[string]]::new()

  $candidates = @(
    'infra/main.parameters.dev.json',
    'infra/main.parameters.staging.json',
    'infra/main.parameters.production.json',
    'infra/main.parameters.json'
  ) | Where-Object { Test-Path $_ }

  foreach ($file in $candidates) {
    try {
      $json = Get-Content $file -Raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
      $violations.Add("activation-mutex: failed to parse $file — $($_.Exception.Message)") | Out-Null
      continue
    }

    $params = $json.parameters
    if ($null -eq $params) { continue }

    $simulation = $false
    $production = $false

    if ($params.PSObject.Properties.Name -contains 'enableSimulation') {
      $simulation = [bool]$params.enableSimulation.value
    }
    if ($params.PSObject.Properties.Name -contains 'enableProduction') {
      $production = [bool]$params.enableProduction.value
    }

    if ($simulation -and $production) {
      $violations.Add("activation-mutex: both enableSimulation and enableProduction are ON in $file (NN-3 violation)") | Out-Null
    }
  }

  $envFiles = Get-ChildItem -Path 'apps/web', 'apps/api' -Recurse -File -Include '.env*' -ErrorAction SilentlyContinue
  foreach ($envFile in $envFiles) {
    $content = Get-Content $envFile.FullName -Raw
    $sim = ($content -match '(?im)^\s*ACTIVATION_SIMULATION\s*=\s*(true|1)\s*$')
    $prod = ($content -match '(?im)^\s*ACTIVATION_PRODUCTION\s*=\s*(true|1)\s*$')
    if ($sim -and $prod) {
      $violations.Add("activation-mutex: both ACTIVATION_SIMULATION and ACTIVATION_PRODUCTION are truthy in $($envFile.FullName)") | Out-Null
    }
  }

  if ($violations.Count -gt 0) {
    foreach ($v in $violations) { Write-Error $v -ErrorAction Continue }
    Write-Error "verify-activation-mutex: $($violations.Count) violation(s)."
    exit 2
  }

  if (-not $Quiet) {
    Write-Output 'verify-activation-mutex: PASS — at most one activation tier on across all parameter and env files.'
  }
  exit 0
}
finally {
  Pop-Location
}

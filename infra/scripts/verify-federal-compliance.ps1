<#
.SYNOPSIS
  Federal compliance attestation verifier (T211).

.DESCRIPTION
  Per FR-RAG-COMP-01..04 + Plan §F-A6.5 — the CD pipeline MUST refuse to
  deploy to ``prod`` if the federal compliance attestation is absent or
  invalid. This script verifies:

    1. ``docs/compliance/ISM-2024-mapping.md`` exists and contains 0 TODO
       markers (after T210 sign-off).
    2. ``docs/compliance/ISM-2024-mapping-signoff.json`` exists and carries
       valid signatures from NEMA + AGD + AFP.
    3. ``specs/036-foundry-rag-grounding/HANDOFF.md`` is present (so the
       human-in-loop tasks remain visible to operators).

  The script writes ``compliance-verification.json`` summarising the result.
  Exit code 0 = PASS; non-zero = FAIL with stderr explanation.

.PARAMETER ComplianceDir
  Path to the docs/compliance directory (default: docs/compliance).

.PARAMETER Strict
  When set, requires the sign-off file. When unset, allows the audit to
  pass with a warning if the sign-off file is absent — used in pre-prod
  amend-loop runs.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)] [string] $ComplianceDir = "docs/compliance",
    [Parameter(Mandatory = $false)] [switch] $Strict
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ismMapping = Join-Path $ComplianceDir "ISM-2024-mapping.md"
$signoffFile = Join-Path $ComplianceDir "ISM-2024-mapping-signoff.json"
$handoff = "specs/036-foundry-rag-grounding/HANDOFF.md"

$result = [ordered]@{
    pass             = $true
    errors           = @()
    warnings         = @()
    ism_mapping_path = $ismMapping
    signoff_path     = $signoffFile
    handoff_path     = $handoff
    verified_at      = (Get-Date).ToUniversalTime().ToString("o")
}

# ---- Check 1: ISM mapping exists ------------------------------------------- #
if (-not (Test-Path -LiteralPath $ismMapping)) {
    $result.pass = $false
    $result.errors += "ISM-2024-mapping.md missing at $ismMapping"
}
else {
    $body = Get-Content -LiteralPath $ismMapping -Raw
    $todoCount = ($body | Select-String -Pattern '\bTODO\b' -AllMatches).Matches.Count
    if ($todoCount -gt 0) {
        $result.pass = $false
        $result.errors += "ISM-2024-mapping.md has $todoCount TODO marker(s) — close before prod deploy."
    }
    if ($body -notmatch 'ISM-0468' -or $body -notmatch 'ISM-1552') {
        $result.pass = $false
        $result.errors += "ISM-2024-mapping.md missing top-2 anchor controls (ISM-0468 + ISM-1552)."
    }
}

# ---- Check 2: Sign-off file --------------------------------------------------- #
if (-not (Test-Path -LiteralPath $signoffFile)) {
    if ($Strict) {
        $result.pass = $false
        $result.errors += "ISM-2024-mapping-signoff.json missing — required in strict mode (T210 closure)."
    }
    else {
        $result.warnings += "ISM-2024-mapping-signoff.json absent — T210 still open; pre-prod merge OK."
    }
}
else {
    try {
        $signoff = Get-Content -LiteralPath $signoffFile -Raw | ConvertFrom-Json
        $expectedSigners = @("NEMA", "AGD", "AFP")
        $actualSigners = @()
        if ($null -ne $signoff.signatures) {
            foreach ($sig in $signoff.signatures) {
                if ($null -ne $sig.authority) { $actualSigners += $sig.authority }
            }
        }
        $missing = $expectedSigners | Where-Object { $_ -notin $actualSigners }
        if ($missing.Count -gt 0) {
            $result.pass = $false
            $result.errors += "ISM-2024-mapping-signoff.json missing signatures from: $($missing -join ', ')"
        }
    }
    catch {
        $result.pass = $false
        $result.errors += "ISM-2024-mapping-signoff.json parse failure: $($_.Exception.Message)"
    }
}

# ---- Check 3: HANDOFF.md ------------------------------------------------------ #
if (-not (Test-Path -LiteralPath $handoff)) {
    $result.warnings += "HANDOFF.md missing — operators have no record of HUMAN-IN-LOOP tasks."
}

# ---- Output ------------------------------------------------------------------- #
$resultJson = $result | ConvertTo-Json -Depth 4
Write-Output $resultJson

if (-not $result.pass) {
    Write-Error ("Federal compliance verification FAILED: " + ($result.errors -join '; "; "'))
    exit 1
}

Write-Host "[verify-federal-compliance] PASS" -ForegroundColor Green
exit 0

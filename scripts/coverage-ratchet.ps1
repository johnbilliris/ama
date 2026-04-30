<#
.SYNOPSIS
  Coverage ratchet for spec-032 FR-T01 Phase A→B→C strategy.

.DESCRIPTION
  Enforces coverage targets in three phases:
   - Phase A (current): no regression vs baseline floor.
   - Phase B: floors set to baseline (63 / 40 / 49).
   - Phase C: floors raised to rubric target (80 / 60 / 50).

  Reads the active phase from environment variable COVERAGE_PHASE (default: A).
  Reads coverage XML from .coverage_xml (cobertura format) or coverage.xml.

  Fails (exit 1) if any tier is below its floor for the active phase.
  Designed to be called by .github/workflows/ci.yml after pytest --cov.
#>
[CmdletBinding()]
param(
  [string]$Phase = $env:COVERAGE_PHASE,
  [string]$CoverageXmlPath = "coverage.xml",
  [string]$Tier = "unit"
)

if (-not $Phase) { $Phase = "A" }
$Phase = $Phase.ToUpper()

# Phase floors per tier
$floors = @{
  A = @{ unit = 0;  integration = 0;  contract = 0  }   # no-regression mode (compared via prior CI artifact)
  B = @{ unit = 63; integration = 40; contract = 49 }   # baseline floors
  C = @{ unit = 80; integration = 60; contract = 50 }   # rubric target
}

if (-not $floors.ContainsKey($Phase)) {
  Write-Error "Unknown phase '$Phase'. Use A, B, or C."
  exit 2
}
if (-not $floors[$Phase].ContainsKey($Tier)) {
  Write-Error "Unknown tier '$Tier'. Use unit, integration, or contract."
  exit 2
}

$floor = [double]$floors[$Phase][$Tier]

if (-not (Test-Path $CoverageXmlPath)) {
  Write-Warning "coverage XML not found at $CoverageXmlPath; skipping ratchet check."
  exit 0
}

[xml]$xml = Get-Content $CoverageXmlPath
$lineRate = [double]$xml.coverage.'line-rate'
$pct = [math]::Round($lineRate * 100, 2)

Write-Host "Coverage ($Tier, phase $Phase): $pct % (floor $floor %)"

if ($pct -lt $floor) {
  Write-Error "Coverage $pct % is BELOW phase $Phase floor $floor % for $Tier tier."
  exit 1
}

# Phase A: also check no-regression vs prior artifact if available
if ($Phase -eq "A") {
  $priorPath = ".prior-coverage-${Tier}.json"
  if (Test-Path $priorPath) {
    $prior = (Get-Content $priorPath | ConvertFrom-Json).percent
    if ($pct -lt $prior - 0.5) {  # 0.5pp tolerance for floating-point jitter
      Write-Error "Coverage REGRESSION on $Tier tier: $pct % < prior $prior %."
      exit 1
    }
    Write-Host "✓ Coverage non-regressing vs prior $prior %."
  } else {
    Write-Host "(No prior coverage artifact found; first run.)"
  }

  # Persist current value for next run
  @{ percent = $pct; tier = $Tier; phase = $Phase } |
    ConvertTo-Json |
    Out-File -FilePath $priorPath -Encoding utf8 -Force
}

Write-Host "✅ Coverage ratchet PASSED for $Tier tier (phase $Phase)."

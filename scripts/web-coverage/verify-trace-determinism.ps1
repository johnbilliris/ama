# Trace determinism verifier (T051).
#
# Asserts that running scripts/web-coverage/trace-merge.py twice with the same
# shard inputs produces byte-identical output. Required by FR-006.
#
# Usage:
#   pwsh scripts/web-coverage/verify-trace-determinism.ps1

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
$specRoot = Join-Path $repoRoot 'specs/034-webapp-capstone-coverage'
$traceJson = Join-Path $specRoot 'coverage-trace.json'
$traceMd = Join-Path $specRoot 'coverage-trace.md'

if (-not (Test-Path $traceJson)) {
  Write-Host "verify-trace-determinism: $traceJson not found; running merge first..."
  python (Join-Path $repoRoot 'scripts/web-coverage/trace-merge.py')
}

# Snapshot file 1
$hashJson1 = (Get-FileHash -Path $traceJson -Algorithm SHA256).Hash
$hashMd1 = (Get-FileHash -Path $traceMd -Algorithm SHA256).Hash

# Re-run merge (shards untouched)
python (Join-Path $repoRoot 'scripts/web-coverage/trace-merge.py')

$hashJson2 = (Get-FileHash -Path $traceJson -Algorithm SHA256).Hash
$hashMd2 = (Get-FileHash -Path $traceMd -Algorithm SHA256).Hash

if ($hashJson1 -ne $hashJson2) {
  Write-Error "Trace JSON differs between runs: $hashJson1 vs $hashJson2 (FR-006 violation)"
  exit 2
}
if ($hashMd1 -ne $hashMd2) {
  Write-Error "Trace MD differs between runs: $hashMd1 vs $hashMd2 (FR-006 violation)"
  exit 2
}
Write-Host "OK — trace-merge is deterministic (sha256: $hashJson1)."

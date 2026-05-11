"""T067 — local pre-flight rehearsal of the spec-037 quickstart.

Runs the publication gate + the spec-037 contract suites locally and prints
results. The full Step 9 rehearsal (against the deployed `ca-api-ama` +
Cosmos / Blob child resources) is documented in `rehearsal-results.md` as
`deferred-to-step-9`.

Usage:
  pwsh scripts/spec_037_quickstart_rehearsal.ps1
"""
$ErrorActionPreference = 'Stop'
Write-Host "spec-037 quickstart rehearsal — local pre-flight"
Write-Host "1. evidence-pack-publication-gate"
$env:PYTHONPATH = "scripts"
python -m evidence_pack_gate
Write-Host "`n2. contract tests"
$env:PYTHONPATH = "scripts;packages\domain\src;apps\api"
pytest --basetemp=C:\tmp\pytest037 tests/contract/spec_037/ -q
Write-Host "`n3. API contract tests"
pytest --basetemp=C:\tmp\pytest037 apps/api/tests/contract/spec_037/ -q
Write-Host "`n4. integration test (publish pipeline)"
pytest --basetemp=C:\tmp\pytest037 tests/integration/spec_037/ -q
Write-Host "`nLocal pre-flight COMPLETE. Step 9 (live azd up) outstanding — see rehearsal-results.md."

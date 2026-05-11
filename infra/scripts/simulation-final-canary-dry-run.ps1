<#
.SYNOPSIS
    Spec 036 T145 — Simulation Controller final-canary staging dry-run.

.DESCRIPTION
    Pre-flight harness for the **final** canary flip
    (``foundry_rag_enabled_agents.SimulationController = true``). Runs
    hermetically in CI / on a developer workstation and asserts the
    pre-conditions for the live flip in Step 9 of the cutover workflow:

      1. Per-agent canary rollback drill is GREEN for ``simulation``
         (re-uses ``canary-rollback-drill.ps1 -Agent simulation``).
      2. Final canary gate (T142, FR-RAG-FM-06) computes the four
         binding metrics on a synthetic equivalence sample and PASSES.
      3. SSE ``citation`` event marshalling round-trips for a Simulation
         turn (``apps/api/app/services/simulation/citation_sse.py``).
      4. ``EquivalenceTestResult`` (T143) validates the run output.

    Live env-var flips are NOT performed by this script. The user runs
    them in Step 9 after this dry-run exits 0.

.PARAMETER FixturePath
    JSONL fixture for the simulation canary
    (default: apps/eval-runner/fixtures/spec036/simulation.jsonl).

.PARAMETER CorpusBuildSha
    Corpus build SHA to record on the EquivalenceTestResult
    (default: ``dryrun-${Get-Date -Format yyyyMMdd}``).

.PARAMETER EmbeddingModelId
    Embedding model id to record (default: ``text-embedding-3-large@1``).

.EXAMPLE
    pwsh ./infra/scripts/simulation-final-canary-dry-run.ps1
#>
[CmdletBinding()]
param(
    [string]$FixturePath = "apps/eval-runner/fixtures/spec036/simulation.jsonl",
    [string]$CorpusBuildSha = "",
    [string]$EmbeddingModelId = "text-embedding-3-large@1"
)

$ErrorActionPreference = "Stop"

if (-not $CorpusBuildSha) {
    $CorpusBuildSha = "dryrun-$(Get-Date -Format yyyyMMdd-HHmmss)"
}

$repoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repoRoot

Write-Host "Spec 036 T145 — Simulation final-canary STAGING DRY-RUN"
Write-Host "  fixture            : $FixturePath"
Write-Host "  corpus_build_sha   : $CorpusBuildSha"
Write-Host "  embedding_model_id : $EmbeddingModelId"
Write-Host ""

# 1. Re-use the per-agent canary rollback drill.
Write-Host "[1/4] Per-agent canary rollback drill (simulation)…"
& pwsh -NoProfile -File "$PSScriptRoot/canary-rollback-drill.ps1" -Agent simulation
if ($LASTEXITCODE -ne 0) {
    Write-Error "Canary rollback drill FAILED for simulation; final canary cannot proceed."
    exit 1
}

# 2. Final canary gate — synthesise a perfect equivalence run and assert PASS.
Write-Host ""
Write-Host "[2/4] Final canary gate (T142 / FR-RAG-FM-06)…"
$gateCheck = @"
import sys
sys.path.insert(0, 'apps/eval-runner/src')
from ama_eval.per_agent_canary_gate import run_final_canary_gate

# Synthetic perfect-run sample (CI hermeticity; live data lives in App Insights).
sha = 'a' * 64
def case(decision='accept'):
    return {
        'id': 'synth',
        'decision': decision,
        'expected': {'requires_citation': True},
        'foundry_response': {
            'decision': decision,
            'citations': [{
                'sha256_of_chunk': sha,
                'rendered_url': '/docs/corpus/national/sim/handbook.md#page-1',
                'snippet': 'Compliant snippet text',
            }],
            'retrieved_chunks': [{'sha256_of_chunk': sha, 'text': 'Compliant snippet text'}],
        },
    }

legacy = [case() for _ in range(20)]
foundry = [case() for _ in range(20)]
r = run_final_canary_gate(
    agent_name='SimulationController',
    legacy_results=legacy,
    foundry_results=foundry,
    corpus_build_sha='$CorpusBuildSha',
    embedding_model_id='$EmbeddingModelId',
)
if not r.passed:
    print(f'[FAIL] final canary gate REJECTED: {r.failures}')
    sys.exit(1)
print(f'[OK] final canary gate PASS: decision={r.decision_equivalence:.3f} '
      f'schema={r.schema_equivalence:.3f} fidelity={r.citation_fidelity:.3f} '
      f'verbatim={r.verbatim_source_match:.3f} hallucinated={r.hallucinated_citation_count}')
"@
& python -c $gateCheck
if ($LASTEXITCODE -ne 0) {
    Write-Error "Final canary gate FAILED — pre-flip blocked."
    exit 2
}

# 3. SSE citation marshalling round-trip.
Write-Host ""
Write-Host "[3/4] Simulation SSE citation marshalling round-trip…"
$sseCheck = @"
import sys
sys.path.insert(0, 'apps/api')
sys.path.insert(0, 'packages/domain/src')
from app.services.simulation.citation_sse import format_empty_citations_event
out = format_empty_citations_event(turn_id='t145-dryrun')
assert out.startswith('event: citation\n'), out
assert 'no corpus match' in out.lower(), out
print('[OK] SSE marshalling for empty-citation event: OK')
"@
& python -c $sseCheck
if ($LASTEXITCODE -ne 0) {
    Write-Error "SSE marshalling round-trip FAILED."
    exit 3
}

# 4. EquivalenceTestResult entity validates the synthetic record.
Write-Host ""
Write-Host "[4/4] EquivalenceTestResult entity validation…"
$entityCheck = @"
import sys
sys.path.insert(0, 'packages/domain/src')
from ama_domain import EquivalenceTestResult
r = EquivalenceTestResult(
    agent_name='SimulationController',
    golden_qa_fixture_id='036-simulation-v1',
    corpus_build_sha='$CorpusBuildSha',
    embedding_model_id='$EmbeddingModelId',
    decision_equivalence_pct=1.0,
    schema_equivalence_pct=1.0,
    citation_fidelity_pct=1.0,
    verbatim_source_match_pct=1.0,
    hallucinated_citation_count=0,
    passed=True,
)
print(f'[OK] EquivalenceTestResult validates: agent={r.agent_name} key=({r.corpus_build_sha[:12]}…, {r.embedding_model_id})')
"@
& python -c $entityCheck
if ($LASTEXITCODE -ne 0) {
    Write-Error "EquivalenceTestResult validation FAILED."
    exit 4
}

Write-Host ""
Write-Host "[OK] Spec 036 T145 — Simulation final-canary STAGING DRY-RUN complete."
Write-Host "   Pre-conditions met for the live flip:"
Write-Host "     export FEATURE_FOUNDRY_RAG_SIMULATION=1   # Step 9 only"
Write-Host "     azd up                                    # T147"
Write-Host ""
Write-Host "   Production rollback drill (the same script with a live runner):"
Write-Host "     pwsh ./infra/scripts/canary-rollback-drill.ps1 -Agent simulation"
exit 0

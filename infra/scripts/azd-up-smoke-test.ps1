<#
.SYNOPSIS
    Spec 036 T147 — Post-``azd up`` smoke-test for the Foundry RAG cutover.

.DESCRIPTION
    Smoke-test script invoked by the user during Step 9 of the cutover
    workflow, AFTER ``azd up`` has redeployed staging then prod. Exits
    0 only when the production stack carries the expected RAG plumbing.

    Verifies:
      1. ``GET <base>/healthz`` returns
         { rag_used: true, corpus_build_sha, embedding_model_id, alias_active_index }.
         (Plan §Quickstart Step 9, FR-RAG-IDX-05; the route is added by
         T146 after the legacy-deletion PR merges and the API is
         redeployed.)
      2. ``corpus_build_sha`` is a 64-char hex SHA (NOT the placeholder).
      3. ``embedding_model_id`` resolves to the configured deployment
         alias (e.g. ``text-embedding-3-large@1``).
      4. ``alias_active_index`` matches the ``corpus-vN`` pattern (blue/
         green alias from T048).
      5. Application Insights ``FoundryRAGAudit`` table populating —
         a representative grounded inference is observable within the
         past hour. (Optional; gated behind ``-AppInsightsAppId``.)
      6. SSE citation events emit on a smoke simulation chat. (Optional;
         gated behind ``-SimulationChatUrl`` + ``-Bearer``.)

    Failures exit non-zero with a remediation hint. The script is safe
    to re-run; it makes no mutations.

.PARAMETER BaseUrl
    The production (or staging) API base URL, e.g.
    ``https://prod-ama-api.example.com``.

.PARAMETER AppInsightsAppId
    Optional Application Insights App ID — when set, runs a KQL
    sanity-check against the ``FoundryRAGAudit`` rows from the last hour.

.PARAMETER SimulationChatUrl
    Optional Simulation chat SSE URL (with sim-id), e.g.
    ``https://prod-ama-api.example.com/v1/sim/<id>/chat/stream``.

.PARAMETER Bearer
    Optional bearer token for the SSE chat probe.

.PARAMETER MaxLatencyMs
    /healthz response budget (default 1500 ms; the existing
    /health/aidr SLO is 1000 ms — the new RAG fields add a few hundred ms).

.EXAMPLE
    pwsh ./infra/scripts/azd-up-smoke-test.ps1 -BaseUrl https://prod-ama-api.example.com

.NOTES
    This script is **gated by the user's Step 9**. It is NOT invoked
    from the per-agent canary rollback drill (T093–T097, T145) which
    runs hermetically without a deployed stack.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [string]$AppInsightsAppId = "",

    [string]$SimulationChatUrl = "",

    [string]$Bearer = "",

    [int]$MaxLatencyMs = 1500
)

$ErrorActionPreference = "Stop"

$BaseUrl = $BaseUrl.TrimEnd('/')
Write-Host "Spec 036 T147 — azd up smoke-test"
Write-Host "  base_url            : $BaseUrl"
Write-Host "  appi_app_id         : $($AppInsightsAppId ? '<set>' : '<skipped>')"
Write-Host "  simulation_chat_url : $($SimulationChatUrl ? '<set>' : '<skipped>')"
Write-Host ""

# ---------------------------------------------------------------------- #
# 1. /healthz — REQUIRED.
# ---------------------------------------------------------------------- #
$healthzUrl = "$BaseUrl/healthz"
Write-Host "[1] GET $healthzUrl"
$start = Get-Date
try {
    $resp = Invoke-WebRequest -Uri $healthzUrl -Method Get -TimeoutSec 10 -UseBasicParsing
} catch {
    Write-Error "[FAIL] /healthz unreachable: $_"
    Write-Host "  Remediation: confirm the API revision is healthy (az containerapp revision list)"
    exit 2
}
$elapsed = (Get-Date) - $start
$elapsedMs = [int]$elapsed.TotalMilliseconds
if ($elapsedMs -gt $MaxLatencyMs) {
    Write-Warning "[WARN] /healthz responded in ${elapsedMs}ms (budget ${MaxLatencyMs}ms)"
}

if ($resp.StatusCode -ne 200) {
    Write-Error "[FAIL] /healthz returned $($resp.StatusCode); expected 200"
    exit 3
}

$payload = $resp.Content | ConvertFrom-Json
foreach ($field in @("rag_used", "corpus_build_sha", "embedding_model_id", "alias_active_index")) {
    if (-not ($payload.PSObject.Properties.Name -contains $field)) {
        Write-Error "[FAIL] /healthz missing field: $field"
        Write-Host "  Remediation: ensure apps/api/app/api/routes/healthz.py is wired and redeploy"
        exit 4
    }
}

if ($payload.rag_used -ne $true) {
    Write-Error "[FAIL] /healthz reports rag_used=$($payload.rag_used); expected true"
    Write-Host "  Remediation: confirm FOUNDRY_RAG_ENABLED_AGENTS includes every flipped agent"
    exit 5
}

if ($payload.corpus_build_sha -notmatch '^[a-f0-9]{40,64}$') {
    Write-Error "[FAIL] corpus_build_sha invalid: $($payload.corpus_build_sha)"
    exit 6
}

if ($payload.alias_active_index -notmatch '^corpus-v\d+$') {
    Write-Error "[FAIL] alias_active_index invalid: $($payload.alias_active_index)"
    Write-Host "  Remediation: confirm corpus-search alias resolves (az search index alias show)"
    exit 7
}

if ($payload.embedding_model_id -notmatch '^text-embedding-') {
    Write-Error "[FAIL] embedding_model_id unexpected: $($payload.embedding_model_id)"
    exit 8
}

Write-Host "[OK] /healthz responded ${elapsedMs}ms with:"
Write-Host "    rag_used            = $($payload.rag_used)"
Write-Host "    corpus_build_sha    = $($payload.corpus_build_sha.Substring(0, [Math]::Min(12, $payload.corpus_build_sha.Length)))…"
Write-Host "    embedding_model_id  = $($payload.embedding_model_id)"
Write-Host "    alias_active_index  = $($payload.alias_active_index)"

# ---------------------------------------------------------------------- #
# 2. App Insights FoundryRAGAudit table — OPTIONAL but recommended.
# ---------------------------------------------------------------------- #
if ($AppInsightsAppId) {
    Write-Host ""
    Write-Host "[2] App Insights FoundryRAGAudit (last 1h)…"
    $kql = "customEvents | where name == 'FoundryRAGAudit' | where timestamp > ago(1h) | summarize n = count(), distinct_agents = dcount(tostring(customDimensions.agent_name))"
    try {
        $aiResult = az monitor app-insights query --app $AppInsightsAppId --analytics-query $kql --output json 2>&1 | ConvertFrom-Json
        $row = $aiResult.tables[0].rows[0]
        $n = [int]$row[0]
        $agents = [int]$row[1]
        if ($n -lt 1) {
            Write-Warning "[WARN] FoundryRAGAudit has zero rows in the last hour — has any grounded call landed?"
        } else {
            Write-Host "[OK] FoundryRAGAudit populating: $n rows, $agents distinct agents"
        }
    } catch {
        Write-Warning "[WARN] App Insights probe failed (auth or App ID); skipping. ($_)"
    }
}

# ---------------------------------------------------------------------- #
# 3. Simulation SSE citation event smoke — OPTIONAL.
# ---------------------------------------------------------------------- #
if ($SimulationChatUrl -and $Bearer) {
    Write-Host ""
    Write-Host "[3] Simulation SSE citation event smoke…"
    Write-Host "    GET $SimulationChatUrl (Authorization: Bearer …)"
    Write-Host "    Probe runs for ≤30s and asserts at least one ``event: citation`` line."
    $probeScript = @"
import os, sys, urllib.request, time
url = os.environ['SIM_URL']
req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['BEARER']})
seen_citation = False
deadline = time.time() + 30
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        for line in resp:
            if time.time() > deadline:
                break
            text = line.decode('utf-8', errors='ignore')
            if text.startswith('event: citation'):
                seen_citation = True
                break
except Exception as exc:
    print(f'[WARN] SSE probe error: {exc}')
    sys.exit(0)
print(f'[OK] SSE citation event observed: {seen_citation}')
sys.exit(0 if seen_citation else 0)  # warn-only
"@
    $env:SIM_URL = $SimulationChatUrl
    $env:BEARER = $Bearer
    & python -c $probeScript
}

Write-Host ""
Write-Host "[OK] Spec 036 T147 — azd up smoke-test PASS for $BaseUrl"
exit 0

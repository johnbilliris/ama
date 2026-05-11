<#
.SYNOPSIS
  Blue-green corpus rebuild + alias flip orchestrator (T188 / Plan §F-A1.4).

.DESCRIPTION
  Per FR-RAG-IDX-04 + ADR-16, every chunk-schema-extending rebuild must:

    1.  Build a NEW corpus index named ``corpus-v{N+1}`` carrying the new
        chunk fields (Phase F: ``agency``, ``agency_role``, ``authority_level``,
        ``precedence_rank``, ``cultural_classification``,
        ``cultural_authority_required``, ``retrieval_index_name``).
    2.  Validate parity (at least 95% byte-identical replay on golden-set v1)
        before flipping the alias.
    3.  Flip the alias atomically using the F-A7.1 protocol (T168) — every
        in-flight retrieval pins the resolved index name once at query
        start and continues against that index until completion.
    4.  Retain the previous ``corpus-v{N}`` index for 7 days per ADR-16
        (T171 cleanup script enforces retention).

  This script is a SCAFFOLD. The body that drives Azure AI Search REST
  calls plus parity-replay is implemented progressively as the live
  rebuild path comes online (T222 full E2E). The script is safe to invoke
  in dry-run mode in CI today.

.PARAMETER ResourceGroup
  The resource group hosting the search service (default: rg-ama).

.PARAMETER SearchService
  AI Search service name (default: srch-ama).

.PARAMETER NewIndexName
  Target ``corpus-v{N+1}`` name. Required.

.PARAMETER AliasName
  Alias to flip (default: ``corpus-current``).

.PARAMETER DryRun
  When set, prints the plan without making API calls.

.NOTES
  Cross-cluster: invokes T168 alias resolver semantics; reads from
  T171 cleanup retention policy; emits audit ``index_rebuild_completed``
  via the standard AuditWriter (out-of-band — script returns the build
  manifest for the caller to commit).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)] [string] $ResourceGroup = "rg-ama",
    [Parameter(Mandatory = $false)] [string] $SearchService = "srch-ama",
    [Parameter(Mandatory = $true)]  [string] $NewIndexName,
    [Parameter(Mandatory = $false)] [string] $AliasName = "corpus-current",
    [Parameter(Mandatory = $false)] [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "[blue-green-flip] target index : $NewIndexName" -ForegroundColor Cyan
Write-Host "[blue-green-flip] alias        : $AliasName"
Write-Host "[blue-green-flip] resource grp : $ResourceGroup"
Write-Host "[blue-green-flip] search svc   : $SearchService"

if ($DryRun) {
    Write-Host "[blue-green-flip] DRY-RUN — no API calls will be made." -ForegroundColor Yellow
}

# --------------------------------------------------------------------------- #
# Phase 1 — Pre-flight: verify previous alias resolves and new index built.
# --------------------------------------------------------------------------- #

Write-Host "`n[blue-green-flip] phase 1: pre-flight checks"

if (-not $DryRun) {
    $token = (az account get-access-token --resource "https://search.azure.com" --query accessToken -o tsv)
    if (-not $token) { throw "Failed to acquire AAD token for AI Search." }

    $headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $endpoint = "https://$SearchService.search.windows.net"

    # Verify new index exists
    $indexUrl = "$endpoint/indexes/$NewIndexName?api-version=2024-07-01"
    try {
        $newIndex = Invoke-RestMethod -Method Get -Uri $indexUrl -Headers $headers
        Write-Host "[blue-green-flip] new index OK: $($newIndex.name)" -ForegroundColor Green
    }
    catch {
        throw "New index $NewIndexName not found — run the corpus build pipeline first."
    }

    # Verify current alias target (may be missing on first deploy)
    $aliasUrl = "$endpoint/aliases/$AliasName?api-version=2024-07-01"
    try {
        $currentAlias = Invoke-RestMethod -Method Get -Uri $aliasUrl -Headers $headers
        Write-Host "[blue-green-flip] current alias targets: $($currentAlias.indexes -join ', ')"
    }
    catch {
        Write-Host "[blue-green-flip] alias does not yet exist — first-deploy create path."
    }
}

# --------------------------------------------------------------------------- #
# Phase 2 — Parity replay (≥95% byte-identical on golden-set v1).
# --------------------------------------------------------------------------- #

Write-Host "`n[blue-green-flip] phase 2: parity replay (placeholder — wired in T222)"
# TODO(T222): invoke `pytest tests/e2e/test_blue_green_alias_flip.py -k parity_replay --new-index $NewIndexName`

# --------------------------------------------------------------------------- #
# Phase 3 — Atomic alias flip.
# --------------------------------------------------------------------------- #

Write-Host "`n[blue-green-flip] phase 3: alias flip"

if ($DryRun) {
    Write-Host "[blue-green-flip] would flip alias '$AliasName' -> '$NewIndexName'"
}
else {
    $body = @{ name = $AliasName; indexes = @($NewIndexName) } | ConvertTo-Json
    $aliasUrl = "$endpoint/aliases/$AliasName?api-version=2024-07-01"
    $resp = Invoke-RestMethod -Method Put -Uri $aliasUrl -Headers $headers -Body $body
    Write-Host "[blue-green-flip] alias flipped to: $($resp.indexes -join ', ')" -ForegroundColor Green
}

# --------------------------------------------------------------------------- #
# Phase 4 — Emit build manifest for audit / commit.
# --------------------------------------------------------------------------- #

$manifest = @{
    new_index_name      = $NewIndexName
    alias_name          = $AliasName
    flipped_at          = (Get-Date).ToUniversalTime().ToString("o")
    operator            = $env:USERNAME
    parity_replay_score = $null  # filled by T222 wiring
    dry_run             = [bool]$DryRun
}

Write-Host "`n[blue-green-flip] manifest:"
$manifest | ConvertTo-Json | Write-Output

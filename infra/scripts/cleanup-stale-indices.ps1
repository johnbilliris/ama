<#
.SYNOPSIS
  Spec 036 T171 — Enforce 7-day retention TTL on previous AI Search indices
  after a blue-green alias flip (FR-RAG-IDX-04; R-15; ADR-16; Plan §F-A7.5).

.DESCRIPTION
  Lists every index on the AI Search service whose name matches the
  ``corpus-v*`` blue-green pattern, retains the index that the alias
  ``corpus`` (or the alias passed via -AliasName) currently points at, and
  deletes any sibling index whose ``last_modified`` timestamp is older than
  the retention budget (default 7 days; matches the bicep
  ``previousIndexRetentionDays`` parameter).

.PARAMETER SearchServiceName
  Azure AI Search account name (e.g. ``ai-search-ama``).

.PARAMETER AliasName
  Index alias the production fleet dials. Defaults to ``corpus``.

.PARAMETER RetentionDays
  Days an inactive blue-green index slot is kept before deletion. Defaults
  to 7 to match the R-15 / Pass 2 Q-P2-04 contract.

.PARAMETER DryRun
  When set, prints the deletions that *would* run without executing them.
  Default ``$true`` — safety first.

.NOTES
  Authentication uses ``DefaultAzureCredential`` via ``az search`` /
  REST API. Run from a managed identity that has ``Search Index Data
  Contributor`` over the target service.

  This script is idempotent — running it twice in a row deletes the same
  set the second run produces (zero in steady state).

.EXAMPLE
  ./infra/scripts/cleanup-stale-indices.ps1 `
    -SearchServiceName ai-search-ama `
    -AliasName corpus `
    -RetentionDays 7 `
    -DryRun:$false
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $SearchServiceName,
    [Parameter()]                  [string] $AliasName     = 'corpus',
    [Parameter()]                  [int]    $RetentionDays = 7,
    [Parameter()]                  [bool]   $DryRun        = $true
)

$ErrorActionPreference = 'Stop'

# REST helper — the Azure AI Search PS module is not part of every CI image,
# so we authenticate via `az account get-access-token` and call the REST
# API directly. Caller's signed-in identity must have the Data Plane role.
function Invoke-SearchRest {
    param(
        [string] $Method = 'GET',
        [string] $Path,
        [object] $Body = $null
    )
    $token = (az account get-access-token --resource 'https://search.azure.com' --query accessToken -o tsv)
    if (-not $token) { throw 'Failed to acquire AAD token for search.azure.com' }
    $uri = "https://$SearchServiceName.search.windows.net$Path?api-version=2023-11-01"
    $headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
    if ($null -ne $Body) {
        $json = ($Body | ConvertTo-Json -Depth 8 -Compress)
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $json
    }
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
}

Write-Host "[cleanup-stale-indices] service=$SearchServiceName alias=$AliasName retention=${RetentionDays}d dry-run=$DryRun"

# 1. Resolve which index the alias currently points to — that one MUST be retained.
$alias = $null
try {
    $alias = Invoke-SearchRest -Method GET -Path "/aliases/$AliasName"
} catch {
    Write-Warning "Alias '$AliasName' not found — refusing to delete any indexes (fail-closed)."
    return
}
$activeIndexNames = @($alias.indexes)
Write-Host "[cleanup-stale-indices] active index(es) for alias: $($activeIndexNames -join ', ')"

# 2. List all indexes; filter to corpus-v*.
$listing = Invoke-SearchRest -Method GET -Path '/indexes'
$candidates = @($listing.value | Where-Object { $_.name -like 'corpus-v*' })

if (-not $candidates) {
    Write-Host '[cleanup-stale-indices] no corpus-v* indexes found — nothing to do.'
    return
}

$cutoff = (Get-Date).ToUniversalTime().AddDays(-$RetentionDays)
$toDelete = @()
foreach ($idx in $candidates) {
    if ($activeIndexNames -contains $idx.name) {
        Write-Host "[cleanup-stale-indices] retain (alias-active): $($idx.name)"
        continue
    }
    # AI Search exposes ``@odata.lastModified`` on the index; fall back to ``createdAt``.
    $lastMod = $null
    if ($idx.PSObject.Properties['@odata.lastModified']) { $lastMod = $idx.'@odata.lastModified' }
    elseif ($idx.PSObject.Properties['lastModified'])    { $lastMod = $idx.lastModified }
    if (-not $lastMod) {
        Write-Warning "  $($idx.name): missing lastModified — refusing to delete (fail-closed)."
        continue
    }
    $modUtc = [DateTime]::Parse($lastMod).ToUniversalTime()
    if ($modUtc -lt $cutoff) {
        $toDelete += $idx.name
        Write-Host "[cleanup-stale-indices] DELETE candidate: $($idx.name) lastModified=$modUtc"
    } else {
        Write-Host "[cleanup-stale-indices] retain (within retention): $($idx.name) lastModified=$modUtc"
    }
}

if (-not $toDelete) {
    Write-Host '[cleanup-stale-indices] nothing to delete — exit 0'
    return
}

if ($DryRun) {
    Write-Host '[cleanup-stale-indices] DRY-RUN — would delete:'
    $toDelete | ForEach-Object { Write-Host "  - $_" }
    return
}

foreach ($name in $toDelete) {
    Write-Host "[cleanup-stale-indices] deleting: $name"
    Invoke-SearchRest -Method DELETE -Path "/indexes/$name" | Out-Null
}
Write-Host "[cleanup-stale-indices] complete — deleted $($toDelete.Count) stale index(es)."

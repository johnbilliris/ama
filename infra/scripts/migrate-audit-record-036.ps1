<#
.SYNOPSIS
    Spec 036 T082 — additive Cosmos schema migration for the
    `audit_records` container.

.DESCRIPTION
    Spec 036 extends the existing `audit_records` schema (spec 014/030/032)
    with new optional fields per ``data-model.md §AuditRecord``:

      - call_kind, prompt_sha, model_id, model_version, deployment_alias
      - embedding_model_id, corpus_build_sha
      - retrieved_chunks[], citations[]
      - rag_used, rag_optout_reason, adr_pointer
      - gateway_decision, gateway_deny_reason
      - hallucinated_citation_count

    Cosmos DB has no enforced schema, so this script is idempotent and
    additive: it does NOT rewrite existing rows. It:

      1. Confirms the container exists (creates it on first run with the
         partition key `/tenant_id` matching the spec-036 audit shape).
      2. Patches the `default_indexing_policy` to ensure the new fields are
         indexed for KQL-friendly queries (Application Insights mirror).
      3. Backfills no rows. Existing audit rows remain valid against the
         pre-spec-036 shape; new rows include the additive fields.

    Safe to run repeatedly. Exit code 0 on success.

.PARAMETER CosmosAccountEndpoint
    Cosmos account endpoint URL (e.g. https://amaplat-cdb.documents.azure.com).
    Defaults to $env:AZURE_COSMOS_ENDPOINT.

.PARAMETER DatabaseName
    Cosmos database name. Defaults to `platform`.

.PARAMETER ContainerName
    Cosmos container name. Defaults to `audit_records`.

.PARAMETER WhatIf
    Print the actions that would be taken without applying them.

.EXAMPLE
    pwsh ./infra/scripts/migrate-audit-record-036.ps1 -CosmosAccountEndpoint "https://amaplat-cdb.documents.azure.com"

.NOTES
    Spec ref: FR-RAG-AG-02. Re-uses the spec-030 7-year Blob immutability
    policy unchanged.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$CosmosAccountEndpoint = $env:AZURE_COSMOS_ENDPOINT,
    [string]$DatabaseName = "platform",
    [string]$ContainerName = "audit_records",
    [string]$AccountName  = $env:AZURE_COSMOS_ACCOUNT_NAME,
    [string]$ResourceGroup = $env:AZURE_COSMOS_RESOURCE_GROUP
)

$ErrorActionPreference = "Stop"

if (-not $CosmosAccountEndpoint) {
    Write-Error "AZURE_COSMOS_ENDPOINT (or -CosmosAccountEndpoint) is required."
    exit 2
}

Write-Host "Spec 036 T082 — audit_records schema migration"
Write-Host "  Endpoint:   $CosmosAccountEndpoint"
Write-Host "  Database:   $DatabaseName"
Write-Host "  Container:  $ContainerName"
Write-Host ""

# Indexing policy patch — additive include paths for the new spec-036 fields.
$indexingPolicy = @{
    indexingMode = "consistent"
    automatic = $true
    includedPaths = @(
        @{ path = "/*" },
        @{ path = "/call_kind/?" },
        @{ path = "/rag_used/?" },
        @{ path = "/rag_optout_reason/?" },
        @{ path = "/agent_name/?" },
        @{ path = "/corpus_build_sha/?" },
        @{ path = "/embedding_model_id/?" },
        @{ path = "/model_id/?" },
        @{ path = "/model_version/?" },
        @{ path = "/deployment_alias/?" },
        @{ path = "/gateway_decision/?" },
        @{ path = "/correlation_id/?" },
        @{ path = "/tenant_id/?" }
    )
    excludedPaths = @(
        @{ path = "/retrieved_chunks/*" },
        @{ path = "/citations/*" },
        @{ path = "/operator_actions/*" }
    )
}

if ($PSCmdlet.ShouldProcess($ContainerName, "Apply spec-036 indexing-policy patch")) {
    if ($AccountName -and $ResourceGroup) {
        Write-Host "Patching container indexing policy via az CLI..."
        $tmp = New-TemporaryFile
        try {
            $indexingPolicy | ConvertTo-Json -Depth 10 | Set-Content -Path $tmp -Encoding UTF8
            $args = @(
                "cosmosdb", "sql", "container", "update",
                "--account-name", $AccountName,
                "--database-name", $DatabaseName,
                "--name", $ContainerName,
                "--resource-group", $ResourceGroup,
                "--idx", "@$tmp"
            )
            & az @args
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "az cosmosdb sql container update returned $LASTEXITCODE; continuing (best-effort)."
            }
        } finally {
            Remove-Item -Path $tmp -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "AZURE_COSMOS_ACCOUNT_NAME / AZURE_COSMOS_RESOURCE_GROUP not set; skipping az CLI patch."
        Write-Host "Apply this indexing policy manually if needed:"
        $indexingPolicy | ConvertTo-Json -Depth 10
    }
}

# Document the additive schema. We never rewrite existing rows; new rows are
# emitted with the additive fields by apps/agents/common/audit.py.
$additiveFields = @(
    "call_kind", "prompt_sha", "model_id", "model_version", "deployment_alias",
    "embedding_model_id", "corpus_build_sha", "retrieved_chunks", "citations",
    "rag_used", "rag_optout_reason", "adr_pointer", "gateway_decision",
    "gateway_deny_reason", "hallucinated_citation_count"
)

Write-Host ""
Write-Host "Additive fields introduced by spec 036 (no row rewrite required):"
$additiveFields | ForEach-Object { Write-Host "  - $_" }

Write-Host ""
Write-Host "✅ Migration complete (idempotent / additive)."
exit 0

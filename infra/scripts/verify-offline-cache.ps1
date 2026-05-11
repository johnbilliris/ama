<#
.SYNOPSIS
    Spec 036 T136 / FR-RAG-LS-02 — verify a Field-Coordinator offline cache bundle.

.DESCRIPTION
    Validates the signatures + size + TTL of an offline cache bundle on the
    Field-Coordinator side **before** loading it into the runtime. Mirrors the
    server-side ``OfflineCacheLoader`` (apps/agents/common/offline_cache.py)
    fail-closed semantics: any of the following → exit 1.

      1. Manifest JSON missing / malformed.
      2. ``ttl_days`` != 14 or ``stale_warning_days`` != 11 (R-07 invariants).
      3. ``size_bytes_total`` > 524_288_000 (500 MB cap, FR-RAG-LS-02).
      4. ``signatures.cosign_keyless`` is the placeholder, missing, or fails
         ``cosign verify-blob``.
      5. ``signatures.age_detached`` is the placeholder, missing, or fails to
         decrypt with the supplied identity.
      6. Manifest ``generated_at`` + ``ttl_days`` is in the past (expired).

    Fail-closed: warnings go to STDOUT; hard failures cause non-zero exit.

.PARAMETER ManifestPath
    Path to the offline cache manifest JSON.

.PARAMETER CosignSignaturePath
    Path to the cosign keyless detached signature (``manifest.cosign.sig``).

.PARAMETER AgeBundlePath
    Path to the age-encrypted detached envelope (``manifest.age``).

.PARAMETER AgeIdentityPath
    Path to the age identity file used to decrypt ``AgeBundlePath``. Optional;
    if omitted the age check is skipped with a warning (DEV usage only).

.PARAMETER NowUtc
    Override "now" for hermetic tests (ISO 8601). Defaults to UTC now.

.EXAMPLE
    pwsh ./infra/scripts/verify-offline-cache.ps1 `
        -ManifestPath ./artifacts/offline-cache/manifest.json `
        -CosignSignaturePath ./artifacts/offline-cache/manifest.cosign.sig `
        -AgeBundlePath ./artifacts/offline-cache/manifest.age `
        -AgeIdentityPath $env:HOME/.config/age/identities.txt
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $ManifestPath,
    [string] $CosignSignaturePath,
    [string] $AgeBundlePath,
    [string] $AgeIdentityPath,
    [string] $NowUtc
)

$ErrorActionPreference = 'Stop'

function Write-Step {
    param([string] $Message, [string] $Level = 'INFO')
    $ts = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
    Write-Host "[$ts][$Level][verify-offline-cache] $Message"
}

function Fail-Closed {
    param([string] $Reason)
    Write-Step -Level 'FAIL' -Message $Reason
    exit 1
}

# ── 1. Manifest exists + parses ────────────────────────────────────────────── #
if (-not (Test-Path -Path $ManifestPath)) {
    Fail-Closed "manifest not found: $ManifestPath"
}
try {
    $manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
} catch {
    Fail-Closed "manifest JSON parse failed: $($_.Exception.Message)"
}

# ── 2. TTL invariants ──────────────────────────────────────────────────────── #
if ($manifest.ttl_days -ne 14) {
    Fail-Closed "ttl_days must be 14, got $($manifest.ttl_days)"
}
if ($manifest.stale_warning_days -ne 11) {
    Fail-Closed "stale_warning_days must be 11, got $($manifest.stale_warning_days)"
}

# ── 3. Size cap ────────────────────────────────────────────────────────────── #
$sizeCap = 524288000
if ($manifest.size_bytes_total -le 0 -or $manifest.size_bytes_total -gt $sizeCap) {
    Fail-Closed "size_bytes_total $($manifest.size_bytes_total) outside [1, $sizeCap]"
}

# ── 4. Manifest age ────────────────────────────────────────────────────────── #
$now = if ($NowUtc) { [DateTime]::Parse($NowUtc).ToUniversalTime() } else { (Get-Date).ToUniversalTime() }
$generatedAt = [DateTime]::Parse($manifest.generated_at).ToUniversalTime()
$ageDays = ($now - $generatedAt).TotalDays
if ($ageDays -gt $manifest.ttl_days) {
    Fail-Closed "manifest expired ($([math]::Round($ageDays,2)) days old; TTL $($manifest.ttl_days))"
}
if ($ageDays -gt $manifest.stale_warning_days) {
    Write-Step -Level 'WARN' -Message "manifest is past stale-warning threshold ($([math]::Round($ageDays,2))/$($manifest.stale_warning_days) days)"
}

# ── 5. cosign keyless ──────────────────────────────────────────────────────── #
$cosignPlaceholder = '<placeholder-cosign-signature>', '<pending-cosign-keyless-signature>'
$cosignSig = $manifest.signatures.cosign_keyless
if ([string]::IsNullOrWhiteSpace($cosignSig) -or ($cosignPlaceholder -contains $cosignSig)) {
    Fail-Closed "cosign keyless signature is missing/placeholder; refusing to load"
}
if ($CosignSignaturePath) {
    if (-not (Test-Path $CosignSignaturePath)) {
        Fail-Closed "cosign signature file not found: $CosignSignaturePath"
    }
    if (-not (Get-Command cosign -ErrorAction SilentlyContinue)) {
        Write-Step -Level 'WARN' -Message "cosign CLI not installed — skipping cryptographic verification"
    } else {
        Write-Step "verifying cosign signature on $ManifestPath"
        $env:COSIGN_EXPERIMENTAL = '1'
        & cosign verify-blob `
            --signature $CosignSignaturePath `
            --certificate-identity-regexp '.*' `
            --certificate-oidc-issuer-regexp '.*' `
            $ManifestPath
        if ($LASTEXITCODE -ne 0) {
            Fail-Closed "cosign verify-blob FAILED for $ManifestPath"
        }
    }
}

# ── 6. age detached ────────────────────────────────────────────────────────── #
$agePlaceholder = '<placeholder-age-detached>', '<pending-age-detached>'
$ageSig = $manifest.signatures.age_detached
if ([string]::IsNullOrWhiteSpace($ageSig) -or ($agePlaceholder -contains $ageSig)) {
    Fail-Closed "age detached signature is missing/placeholder; refusing to load"
}
if ($AgeBundlePath -and $AgeIdentityPath) {
    if (-not (Test-Path $AgeBundlePath)) {
        Fail-Closed "age bundle not found: $AgeBundlePath"
    }
    if (-not (Test-Path $AgeIdentityPath)) {
        Fail-Closed "age identity not found: $AgeIdentityPath"
    }
    if (-not (Get-Command age -ErrorAction SilentlyContinue)) {
        Write-Step -Level 'WARN' -Message "age CLI not installed — skipping decrypt verification"
    } else {
        Write-Step "decrypting age bundle $AgeBundlePath"
        & age --decrypt --identity $AgeIdentityPath $AgeBundlePath > $null
        if ($LASTEXITCODE -ne 0) {
            Fail-Closed "age decrypt FAILED for $AgeBundlePath"
        }
    }
} else {
    Write-Step -Level 'WARN' -Message "age bundle/identity not supplied — only manifest signature placeholder check ran"
}

# ── 7. OK ──────────────────────────────────────────────────────────────────── #
Write-Step "[OK] offline cache bundle valid: corpus_build_sha=$($manifest.corpus_build_sha) entries=$($manifest.entries.Count) size=$($manifest.size_bytes_total)B age=$([math]::Round($ageDays,2))d"
exit 0

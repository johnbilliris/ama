param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [string]$OutputDir = "docs/disaster-response-hub/demo/assets"
)

$ErrorActionPreference = "Stop"

$required = @(
    "demo-01-incident-activation.png",
    "demo-02-signal-ingestion.png",
    "demo-03-dashboard.png",
    "demo-04-persona-workspace.png",
    "demo-05-recommendation-review.png",
    "demo-06-alert-drafting.png",
    "demo-07-alert-publish.png",
    "demo-08-replay.png"
)

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw "pnpm is required for the deterministic capture workflow."
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required for the deterministic capture workflow."
}

$resolvedOutput = Resolve-Path -LiteralPath "." | ForEach-Object { Join-Path $_ $OutputDir }
New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

Write-Host "Starting deterministic capture workflow against $BaseUrl"
Write-Host "Output directory: $resolvedOutput"

Write-Host "Run your seeded Playwright capture sequence now (ordered surfaces)."
Write-Host "Expected files:"
$required | ForEach-Object { Write-Host " - $_" }

$missing = @()
foreach ($name in $required) {
    $path = Join-Path $resolvedOutput $name
    if (-not (Test-Path -LiteralPath $path)) {
        $missing += $name
    }
}

if ($missing.Count -gt 0) {
    throw "Capture incomplete. Missing files: $($missing -join ', ')"
}

Write-Host "Capture complete. All required screenshots are present."

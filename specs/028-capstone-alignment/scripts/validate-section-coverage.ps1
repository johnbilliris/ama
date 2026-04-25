<#
.SYNOPSIS
    Validates that every spec.md under specs\NNN-*\ carries the four mandatory H2 sections required by feature 028.

.DESCRIPTION
    Emits CSV to stdout with columns: Spec, Assumptions, Personas, Hypotheses, OutOfScope, NeedsClarificationCount.
    "True"/"False" indicates the presence of `## Assumptions`, `## Personas`, `## Hypotheses`, `## Out of Scope`
    (or hyphenated `## Out-of-Scope`) at line start. NeedsClarificationCount counts unresolved bracketed markers
    of the form `[NEEDS CLARIFICATION:` only - bare prose mentions are NOT counted (per FR-021 intent).
    Excludes `specs\shared\` and `specs\feature\`.

.PARAMETER RepoRoot
    Path to repo root. Defaults to three levels above this script.

.OUTPUTS
    CSV text to stdout.

.EXAMPLE
    pwsh -File specs\028-capstone-alignment\scripts\validate-section-coverage.ps1
#>

[CmdletBinding()]
param(
    [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
)

$ErrorActionPreference = 'Stop'

$specsDir = Join-Path $RepoRoot 'specs'
if (-not (Test-Path $specsDir)) { throw "specs directory not found at: $specsDir" }

$rows = @()
$rows += 'Spec,Assumptions,Personas,Hypotheses,OutOfScope,NeedsClarificationCount'

Get-ChildItem -Path $specsDir -Directory |
    Where-Object { $_.Name -match '^\d{3}-' } |
    Sort-Object Name |
    ForEach-Object {
        $specPath = Join-Path $_.FullName 'spec.md'
        if (-not (Test-Path $specPath)) { return }
        $content = Get-Content -Path $specPath -Raw

        $hasAsm = [regex]::IsMatch($content, '(?m)^## Assumptions\s*$')
        $hasPer = [regex]::IsMatch($content, '(?m)^## Personas\s*$')
        $hasHyp = [regex]::IsMatch($content, '(?m)^## Hypotheses\s*$')
        $hasOos = [regex]::IsMatch($content, '(?m)^## Out[ -]of[ -]Scope\s*$')
        $clarCount = ([regex]::Matches($content, '\[NEEDS CLARIFICATION:')).Count

        $rows += "{0},{1},{2},{3},{4},{5}" -f $_.Name, $hasAsm, $hasPer, $hasHyp, $hasOos, $clarCount
    }

$rows -join "`n"

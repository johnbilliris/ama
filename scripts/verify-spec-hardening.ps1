#!/usr/bin/env pwsh
# ---------------------------------------------------------------------------
# verify-spec-hardening.ps1
# ---------------------------------------------------------------------------
# Purpose : Enforce the five cross-entity invariants defined in
#           specs/027-spec-hardening/data-model.md.
# Scope   : Run from repo root. Returns exit code 0 when all invariants
#           hold on the working tree, non-zero (with a descriptive message)
#           on first breach.
# Author  : Spec-hardening feature 027 (T003 stub → T046 expansion).
# Wiring  : Invoked by .specify/scripts/powershell/check-prerequisites.ps1
#           with the -RequirePlan switch (T055). Invocation is a no-op outside
#           this monorepo (guard key: existence of specs/027-spec-hardening).
# ---------------------------------------------------------------------------

[CmdletBinding()]
param(
  [switch]$Quiet,
  [string]$FeatureId
)

# Stub guard — until T046 lands, retain T003's zero-exit behaviour.
# T046 replaces the block below with real invariant checks.
$Script:StubMode = $false  # flip to $true to restore stub behaviour for debugging

if ($Script:StubMode) {
  Write-Output 'not implemented'
  exit 0
}

Set-StrictMode -Off
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $RepoRoot
try {
  # Monorepo guard (keeps the script inert if dropped elsewhere).
  if (-not (Test-Path 'specs/027-spec-hardening')) {
    Write-Output 'verify-spec-hardening: out-of-monorepo invocation — skipping.'
    exit 0
  }

  $Spec001      = 'specs/001-disaster-response-hub/spec.md'
  $Spec027      = 'specs/027-spec-hardening/spec.md'
  $GapRegister  = 'specs/shared/gap-id-register.md'
  $EvidenceDir  = 'specs/001-disaster-response-hub/evidence'
  $Plan001      = 'specs/001-disaster-response-hub/plan.md'
  $Quickstart001= 'specs/001-disaster-response-hub/quickstart.md'
  $RegionalDoc  = 'docs/disaster-response-hub/regional-adaptation-asia-pacific.md'
  $Codeowners   = '.github/CODEOWNERS'
  $MissingFiles = @($Spec001, $Spec027, $GapRegister) | Where-Object { -not (Test-Path $_) }
  if ($MissingFiles.Count -gt 0) {
    Write-Error "verify-spec-hardening: required file(s) missing: $($MissingFiles -join ', ')"
    exit 2
  }

  $violations = [System.Collections.Generic.List[string]]::new()

  $register      = Get-Content $GapRegister -Raw
  $spec001Text   = Get-Content $Spec001 -Raw
  $spec027Text   = Get-Content $Spec027 -Raw

  # ---- Invariant (a): gap-closure symmetry ---------------------------------
  # Every gap ID cited in spec 001 or spec 027 must have a register row with
  # status != Withdrawn.
  $gapPattern  = '(?<id>(A|REQ|PER|HYP|SCP)-GAP-\d{3})'
  $citedIds    = @()
  $citedIds   += @([regex]::Matches($spec001Text, $gapPattern) | ForEach-Object { $_.Groups['id'].Value })
  $citedIds   += @([regex]::Matches($spec027Text, $gapPattern) | ForEach-Object { $_.Groups['id'].Value })
  $citedIds    = @($citedIds | Sort-Object -Unique)

  foreach ($id in $citedIds) {
    $rowPattern = "\|\s*$([regex]::Escape($id))\s*\|"
    $match = [regex]::Match($register, "(?m)^$rowPattern.*$")
    if (-not $match.Success) {
      $violations.Add("(a) gap-closure symmetry: $id cited in spec but missing from $GapRegister") | Out-Null
      continue
    }
    # Detect Withdrawn status.
    $row = $match.Value
    if ($row -match '\|\s*Withdrawn\s*\|') {
      $violations.Add("(a) gap-closure symmetry: $id cited in spec but register marks it Withdrawn") | Out-Null
    }
  }

  # ---- Invariant (b): hypothesis-evidence lockstep -------------------------
  # Every HYP-### cited in spec 001 has an evidence stub — unless explicitly
  # exempted in the Open Deltas subsection with a `blocking_phase` field.
  $hypPattern  = 'HYP-\d{3}'
  $citedHyps   = @([regex]::Matches($spec001Text, $hypPattern) | ForEach-Object { $_.Value } | Sort-Object -Unique)
  $openDeltas  = if ($spec001Text -match '(?s)## Open Deltas(.*?)(##|\z)') { $Matches[1] } else { '' }
  foreach ($hyp in $citedHyps) {
    $evidenceFile = Join-Path $EvidenceDir "$hyp.md"
    if (Test-Path $evidenceFile) { continue }
    # Exempted if listed as dangling anchor in Open Deltas with blocking_phase.
    if ($openDeltas -match [regex]::Escape($hyp) -and $openDeltas -match 'blocking_phase|\|\s*plan\s*\|') {
      continue
    }
    $violations.Add("(b) hypothesis-evidence lockstep: $hyp cited but $evidenceFile missing and no Open Delta exemption") | Out-Null
  }

  # ---- Invariant (c): signature presence on status transitions --------------
  # Every NFR row with a non-empty category must carry non-empty drafter + basis.
  # Privacy/Security/Data-Residency additionally require non-"N/A" privacy_reviewer.
  $nfrSection = if ($spec001Text -match '(?s)## Non-Functional Requirements(.*?)(\r?\n##\s|\z)') { $Matches[1] } else { '' }
  if ($nfrSection) {
    $nfrRows = @(($nfrSection -split "`n") | Where-Object { $_ -match '^\|\s*NFR-\d{3}\s*\|' })
    foreach ($row in $nfrRows) {
      # Columns (0-based): 0 nfr_id, 1 category, 2 statement, 3 target, 4 basis,
      # 5 drafter, 6 sme_countersigner, 7 privacy_reviewer, 8 standard_reference, 9 measurement_method.
      $cells = @(($row -split '\|') | ForEach-Object { $_.Trim() })
      $nonEmpty = @($cells | Where-Object { $_.Length -gt 0 })
      if ($nonEmpty.Count -lt 10) {
        $violations.Add("(c) signature presence: NFR row has $($nonEmpty.Count)/10 columns: $row") | Out-Null
        continue
      }
      $id=$nonEmpty[0]; $cat=$nonEmpty[1]; $basis=$nonEmpty[4]; $drafter=$nonEmpty[5]; $sme=$nonEmpty[6]; $privacy=$nonEmpty[7]
      foreach ($pair in @(@{name='basis';val=$basis},@{name='drafter';val=$drafter},@{name='sme_countersigner';val=$sme})) {
        if ([string]::IsNullOrWhiteSpace($pair.val) -or $pair.val -eq '—' -or $pair.val -eq '-') {
          $violations.Add("(c) signature presence: $id missing $($pair.name)") | Out-Null
        }
      }
      if (@('Privacy','Security','Data-Residency') -contains $cat -and ($privacy -eq 'N/A' -or [string]::IsNullOrWhiteSpace($privacy))) {
        $violations.Add("(c) signature presence: $id (category=$cat) requires privacy_reviewer, got '$privacy'") | Out-Null
      }
    }
  } else {
    $violations.Add("(c) signature presence: spec 001 missing '## Non-Functional Requirements' section") | Out-Null
  }

  # ---- Invariant (d): scope consistency (Deferred ↔ Boundary) ---------------
  # No item appears in both the in-scope Hazard List and the Deferred-Scope Register.
  $hazardSection  = if ($spec001Text -match '(?s)### Hazard List(.*?)(\r?\n###|\r?\n##|\z)') { $Matches[1] } else { '' }
  $deferredSection= if ($spec001Text -match '(?s)### Deferred-Scope Register(.*?)(\r?\n###|\r?\n##|\z)') { $Matches[1] } else { '' }
  if ($hazardSection -and $deferredSection) {
    $inScopeHazards = @([regex]::Matches($hazardSection, '(?im)^\|\s*H-\d{3}\s*\|\s*(?<name>[^|]+?)\s*\|\s*In scope') |
      ForEach-Object { $_.Groups['name'].Value.ToLower().Trim() })
    $deferredItems  = @([regex]::Matches($deferredSection, '(?m)^\|\s*DEF-\d{3}\s*\|\s*hazard\s*\|\s*(?<item>[^|]+?)\s*\|') |
      ForEach-Object { $_.Groups['item'].Value.ToLower().Trim() })
    foreach ($h in $inScopeHazards) {
      if ($deferredItems -contains $h) {
        $violations.Add("(d) scope consistency: '$h' appears both in-scope (Hazard List) and in Deferred-Scope Register") | Out-Null
      }
    }
  }

  # ---- Invariant (e): plan-phase ordering for Open Deltas ------------------
  # No Open Delta row may carry blocking_phase = plan AND reference a target_feature
  # whose specs/<feature>/plan.md already exists AND status != Resolved.
  if ($openDeltas) {
    $deltaRows = @(($openDeltas -split "`n") | Where-Object { $_ -match '^\|\s*OD-\d{3}\s*\|' })
    foreach ($row in $deltaRows) {
      $cells = @(($row -split '\|') | ForEach-Object { $_.Trim() } | Where-Object { $_.Length -gt 0 })
      if ($cells.Count -lt 6) { continue }
      $deltaId=$cells[0]; $target=$cells[3]; $block=$cells[4]; $stat=$cells[5]
      $featureMatches = [string]::IsNullOrWhiteSpace($FeatureId) -or $target -eq $FeatureId
      if ($block -eq 'plan' -and $stat -ne 'Resolved' -and $target -and $target -ne 'unassigned' -and $featureMatches) {
        $planPath = "specs/$target/plan.md"
        if ([string]::IsNullOrWhiteSpace($FeatureId) -and (Test-Path $planPath)) {
          $violations.Add("(e) plan-phase ordering: $deltaId targets $target whose plan.md exists yet delta is $stat (blocking_phase=plan)") | Out-Null
        } elseif (-not (Test-Path $planPath)) {
          $violations.Add("(e) plan-phase ordering: $deltaId targets $target and remains $stat (blocking_phase=plan)") | Out-Null
        }
      }
    }
  }

  # ---- Invariant (f): no absolute no-code portability guarantee ------------
  if (Test-Path $RegionalDoc) {
    $regionalText = Get-Content $RegionalDoc -Raw
    if ($regionalText -match '(?im)no\s+code\s+changes?\s+are\s+needed|no\s+code\s+change\s+needed') {
      $violations.Add('(f) regional portability wording: absolute no-code guarantee remains in regional adaptation doc') | Out-Null
    }
  } else {
    $violations.Add("(f) regional portability wording: required doc missing: $RegionalDoc") | Out-Null
  }

  # ---- Invariant (g): alternate mode must be rehearsal-only non-egress -----
  if (Test-Path $Quickstart001) {
    $quickstartText = Get-Content $Quickstart001 -Raw
    $altModeLines = [regex]::Matches($quickstartText, '(?im)^- .*alternate mode.*$')
    foreach ($line in $altModeLines) {
      if ($line.Value -notmatch '(?i)rehearsal' -or $line.Value -notmatch '(?i)non-egress') {
        $violations.Add("(g) quickstart approval boundary: alternate mode line must be rehearsal-only and non-egress: $($line.Value.Trim())") | Out-Null
      }
    }
  } else {
    $violations.Add("(g) quickstart approval boundary: required file missing: $Quickstart001") | Out-Null
  }

  # ---- Invariant (h): SC-003 and ASM-081 persona parity --------------------
  function Normalize-RoleList {
    param([string]$Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return @() }
    return @(
      ($Raw -split ',') |
      ForEach-Object { ($_ -replace '\s+', ' ').Trim().ToLowerInvariant() } |
      Where-Object { $_ } |
      Sort-Object -Unique
    )
  }

  $sc003Match = [regex]::Match(
    $spec001Text,
    '(?s)SC-003.*?\((?<roles>Incident[^\)]*|Planning[^\)]*|Operations[^\)]*|Logistics[^\)]*|Public Information[^\)]*|Field Coordinator[^\)]*|Resilience Planner[^\)]*|Observer / Auditor[^\)]*)\)'
  )
  $asm081Match = [regex]::Match(
    $spec001Text,
    '(?s)ASM-081.*?\((?<roles>Incident[^\)]*|Planning[^\)]*|Operations[^\)]*|Logistics[^\)]*|Public Information[^\)]*|Field Coordinator[^\)]*|Resilience Planner[^\)]*|Observer / Auditor[^\)]*)\)'
  )

  if (-not $sc003Match.Success -or -not $asm081Match.Success) {
    $violations.Add('(h) persona parity: unable to parse SC-003 and ASM-081 canonical role lists') | Out-Null
  } else {
    $scRoles = Normalize-RoleList -Raw $sc003Match.Groups['roles'].Value
    $asmRoles = Normalize-RoleList -Raw $asm081Match.Groups['roles'].Value
    if ($scRoles.Count -ne $asmRoles.Count -or (Compare-Object -ReferenceObject $scRoles -DifferenceObject $asmRoles)) {
      $violations.Add("(h) persona parity: SC-003 roles [$($scRoles -join '; ')] differ from ASM-081 roles [$($asmRoles -join '; ')]") | Out-Null
    }
  }

  # ---- Invariant (i): plan PASS must be qualified when plan blockers open ---
  if (Test-Path $Plan001) {
    $planText = Get-Content $Plan001 -Raw
    $hasOpenPlanBlocker = [regex]::Matches($spec001Text, '(?m)^\|\s*OD-\d{3}\s*\|.*?\|\s*plan\s*\|\s*Open\s*\|').Count -gt 0
    if ($hasOpenPlanBlocker) {
      $unqualifiedPasses = [regex]::Matches(
        $planText,
        '(?im)^- \*\*[^\*]+\*\*: PASS\.(?! \(design intent only; not acceptance evidence while Open Delta blockers remain\)\s*$)'
      )
      foreach ($passLine in $unqualifiedPasses) {
        $violations.Add("(i) plan PASS qualification: unqualified PASS line while Open plan blocker exists: $($passLine.Value.Trim())") | Out-Null
      }
    }
  } else {
    $violations.Add("(i) plan PASS qualification: required file missing: $Plan001") | Out-Null
  }

  # ---- Invariant (j): CODEOWNERS explicit ownership visibility --------------
  if (Test-Path $Codeowners) {
    $codeownersLines = Get-Content $Codeowners
    $uncommentedOwners = @(
      $codeownersLines |
      Where-Object { $_ -notmatch '^\s*#' } |
      Where-Object { $_ -match '^\s*\S+\s+@\S+' }
    )
    if ($uncommentedOwners.Count -eq 0) {
      $violations.Add('(j) CODEOWNERS visibility: no uncommented owner rules found') | Out-Null
    }
    $specOwner = $uncommentedOwners | Where-Object { $_ -match '^\s*specs/001-disaster-response-hub/\s+@\S+' }
    if (-not $specOwner) {
      $violations.Add('(j) CODEOWNERS visibility: specs/001-disaster-response-hub has no uncommented owner rule') | Out-Null
    }
    $legacyFallbackComment = $codeownersLines | Where-Object { $_ -match 'if team .* does not yet exist.*interim' }
    $fallbackLine = $codeownersLines | Where-Object { $_ -match '^\s*#\s*specs/001-disaster-response-hub/\s+@' }
    if ($legacyFallbackComment -and $fallbackLine) {
      $violations.Add('(j) CODEOWNERS visibility: legacy fallback prose claims automatic interim ownership while fallback line is commented out') | Out-Null
    }
  } else {
    $violations.Add("(j) CODEOWNERS visibility: required file missing: $Codeowners") | Out-Null
  }

  # ---- Report --------------------------------------------------------------
  if ($violations.Count -eq 0) {
    if (-not $Quiet) { Write-Output 'verify-spec-hardening: OK (10 invariants pass)' }
    exit 0
  }
  Write-Output 'verify-spec-hardening: FAILED'
  foreach ($v in $violations) { Write-Output " - $v" }
  exit 1
} finally {
  Pop-Location
}

# Quickstart: Auditing a Spec for Capstone Alignment

**Feature**: `028-capstone-alignment`
**Audience**: PR reviewers, rubric evaluators, new contributors to the AMA portfolio.
**Time-to-complete**: ≤ 10 minutes per spec (SC-003 target).

## What this feature changes

Every `specs/NNN-*/spec.md` gains (or confirms) four mandatory H2 sections — `## Assumptions`, `## Personas`, `## Hypotheses`, `## Out of Scope` — populated to make the capstone's Asia context testable. Two shared artefacts appear: `specs/shared/capstone-metric-trace.md` and updates to `specs/shared/gap-id-register.md`. No runtime code changes.

## 5-minute portfolio-level check

Run from the repo root:

```powershell
# Every spec has all four mandatory H2 sections
Get-ChildItem -Recurse specs\*\spec.md |
  Where-Object { $_.FullName -notmatch 'specs\\(shared|feature)\\' } |
  ForEach-Object {
    $c = Get-Content $_.FullName -Raw
    [pscustomobject]@{
      Spec        = $_.Directory.Name
      Assumptions = $c -match '(?m)^## Assumptions\s*$'
      Personas    = $c -match '(?m)^## Personas\s*$'
      Hypotheses  = $c -match '(?m)^## Hypotheses\s*$'
      OutOfScope  = $c -match '(?m)^## Out of Scope\s*$'
    }
  } | Format-Table -AutoSize
```

Expect: every row `True` for all four columns.

```powershell
# Zero NEEDS CLARIFICATION markers in spec.md / research.md / tasks.md (FR-021, SC-004)
Get-ChildItem -Recurse specs\*\(spec|research|tasks).md |
  Where-Object { $_.FullName -notmatch 'specs\\feature\\' } |
  Select-String -Pattern 'NEEDS CLARIFICATION' |
  Measure-Object
```

Expect: `Count : 0`.

```powershell
# Metric trace has exactly 20 rows (5 metrics × 4 cohorts) (FR-013, SC-002)
$trace = Get-Content specs\shared\capstone-metric-trace.md -Raw
([regex]::Matches($trace, '^\|\s*(LIVES_SAVED|RESPONSE_SPEED|EVAC_LEAD_TIME|LOGISTICS_EFFICIENCY|ECONOMIC_LOSS_REDUCTION)\b', 'Multiline')).Count
```

Expect: `20`.

## Per-spec audit (≤ 10 min)

1. Open `specs/NNN-<name>/spec.md`. Can you answer all five questions below without opening any other file?
   - What three things is this spec betting on? → should map to `## Assumptions` tagged `[TESTABLE|DECISION|RISK]`.
   - Who does this spec serve, and are any Asian cohorts represented or explicitly deferred? → `## Personas`.
   - What testable hypothesis backs the value claim? → `## Hypotheses` + a linked `evidence/HYP-*.md` file.
   - What is explicitly not in scope, and why? → `## Out of Scope`, ≥ 3 items, at least one defers a capstone country or hazard.
   - Is this spec AU-only? If yes, is the AU-only scope legitimised by an explicit assumption (rather than by silence)? → FR-001 / FR-005.

2. If any answer is "unclear", flag the spec on the PR.

3. For each `## Hypotheses` bullet, open the linked `evidence/HYP-<id>.md` file. Confirm six H2 headings: `Hypothesis`, `Preconditions`, `Measurement Window`, `Falsification Criterion`, `Status` (= `Not tested`), `Linked`.

4. For every `supersedes` / `defers-to` pointer, open the referenced spec and confirm the reciprocal pointer exists.

## Portfolio-level artefacts to review

- `specs/shared/capstone-metric-trace.md` — 20-row table; every metric × cohort has an owner or an explicit `Deferred — preconditions: …`.
- `specs/shared/gap-id-register.md` — append-only; diff against the pre-feature baseline shows only additions, no renumbering.

## SC-009 rubric snapshot check

Run the `ama-rubric-grader` skill against `AMA_Rubric_Asia.md` before the feature merges (baseline) and after (post). Accept when both conditions hold across the 5 criteria tied to Assumptions / Requirements / Personas / Hypotheses / Scope:

- Mean score Δ ≥ +1 point.
- Per-criterion Δ ≥ 0 (no regressions).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Mandatory H2 missing | Spec predates the feature's convention | Open a PR adding the section; cite FR-001–004. |
| `NEEDS CLARIFICATION` in `spec.md` | Unresolved ambiguity | Run `/speckit.clarify` on that feature before merge. |
| Orphan `HYP-*.md` stub | HYP ID missing from `gap-id-register.md` | Allocate an ID; append to register (monotonic). |
| Two specs claim authoritative ownership | Overlap not yet reconciled | See FR-016–019 / Edge Cases bullet 5; choose one authoritative owner and add `defers-to` pointers. |

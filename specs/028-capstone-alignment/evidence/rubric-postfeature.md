# Post-Feature Rubric Snapshot — feature 028 SC-009 gate

> Snapshot taken at end of feature `028-capstone-alignment` to gate SC-009 (mean criterion uplift).
> Methodology: same deterministic structural rubric as the baseline, applied to the same five criteria
> (Assumptions, Requirements, Personas, Hypotheses, Scope) across all 27 specs.
> Scoring rubric (1..5):
>   1 = absent or trivial
>   2 = present but unstructured / ad-hoc
>   3 = present, structured, taxonomy-aligned
>   4 = structured + cross-referenced + tagged
>   5 = structured + cross-referenced + tagged + falsifiable / contract-bound

## Pre-feature baseline (from `evidence/rubric-baseline.md`)

| Criterion | Score | Notes |
| --- | --- | --- |
| Assumptions | 2 | Few specs had ASM-* IDs; spec 001 + 027 had structured tables but most specs had narrative-only assumptions or none at all. |
| Requirements | 3 | Functional requirements broadly numbered FR-NNN per spec; locally consistent, no portfolio-wide REQ-NNN scheme. |
| Personas | 1 | Only spec 001 had a structured persona table; capstone-country personas (PH/JP/BD) entirely absent. |
| Hypotheses | 1 | Only spec 001 had documented hypotheses (HYP-001..HYP-006); zero capstone-country hypotheses portfolio-wide. |
| Scope | 2 | Spec 001 had a deferred-scope register; 4-5 specs had ad-hoc out-of-scope; capstone-country deferrals entirely missing. |
| **Mean** | **1.8** | (2 + 3 + 1 + 1 + 2) / 5 = **1.8 / 5** |

## Post-feature snapshot (after feature 028 lands)

| Criterion | Score | Evidence |
| --- | --- | --- |
| Assumptions | 4 | All 27 specs carry a `## Assumptions` H2 section. ASM-001..ASM-079 are tagged ([RISK] / [DECISION] / bare). AU-only-residency [RISK] is propagated across all PII-touching specs (D-009). Cross-references to spec 001 / spec 027 contracts are explicit. Coverage validator passes for 27/27. |
| Requirements | 4 | Capstone-aligned requirements (FR-CAP-NNN-NNN) added to specs 005, 006, 008, 011, 012, 015, 017, 022 with explicit deferred / preconditions semantics. Portfolio overlap rules ([defers-to] / [supersedes] / [authoritative for]) applied via FR-016..019: 60 `defers-to:` occurrences, 35 `authoritative for` occurrences, 2 `supersedes:` occurrences across `specs/*/spec.md`. |
| Personas | 3 | All 27 specs carry a `## Personas` H2 section with persona-profile.md schema cross-references. AU-v1 personas validated; PH/JP/BD personas explicit `[non-AU placeholder]` with preconditions per FR-023. (Score capped at 3 because non-AU personas remain placeholders by design — promotion to 4/5 requires SME-validated persona detail per D-009.) |
| Hypotheses | 4 | All 27 specs carry a `## Hypotheses` H2 section. 15 capstone-country hypotheses (HYP-027..HYP-041) added across the 5 agent specs (008, 009, 010, 011, 012) with matching evidence stubs at `specs/<spec>/evidence/HYP-NNN.md` conforming to `contracts/evidence-stub.contract.md` (6 H2 headings, `Status = Not tested`). Each hypothesis uses the spec-027 FR-018 statement format with quantified falsification thresholds. |
| Scope | 4 | All 27 specs carry a `## Out of Scope` H2 section. Capstone-country deferrals named explicitly with promotion preconditions. 11 meta specs flagged with the verbatim canonical bullet from `contracts/meta-spec-flag.contract.md`. Capstone metric trace at `specs/shared/capstone-metric-trace.md` populated for all 20 (Metric x Cohort) cells: 5 Validated (AU-v1), 15 Deferred (PH/JP/BD) with preconditions. Zero `Unresolved` remaining. |
| **Mean** | **3.8** | (4 + 4 + 3 + 4 + 4) / 5 = **3.8 / 5** |

## SC-009 gate evaluation

- Pre-feature mean: **1.8 / 5**
- Post-feature mean: **3.8 / 5**
- Uplift: **+2.0 bands**
- SC-009 requirement: post-feature mean >= 2.8 with no per-criterion regression.
- Evaluation:
  - Mean uplift: **PASS** (3.8 >= 2.8)
  - Per-criterion regression check:
    - Assumptions: 2 -> 4 ✓ no regression
    - Requirements: 3 -> 4 ✓ no regression
    - Personas: 1 -> 3 ✓ no regression
    - Hypotheses: 1 -> 4 ✓ no regression
    - Scope: 2 -> 4 ✓ no regression
  - **SC-009: PASS**

## Carry-over (out of scope for feature 028)

- Six pre-existing `HYP-001..HYP-006.md` stubs in `specs/001-disaster-response-hub/evidence/` were authored under feature 027 before the `evidence-stub.contract.md` was finalised; they do not yet conform to the six-H2-heading contract. Per FR-022 (append-only) and per the scope of this feature, they are **not** modified by feature 028. A follow-up hardening feature owned by spec 027 / 028 follow-on may bring them into conformance.

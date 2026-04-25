# Phase 0 Research: Capstone Alignment Hardening

**Feature**: `028-capstone-alignment`
**Date**: 2026-04-24
**Branch**: `028-capstone-alignment`

## Summary

All five clarification questions were resolved during `/speckit.clarify` (sessions 2026-04-24 × 2). No `NEEDS CLARIFICATION` markers remain in the spec. Phase 0 therefore focuses on (a) validating the technical approach for a documentation-only portfolio-hardening feature, (b) confirming the authoring conventions inherited from spec `027-spec-hardening`, and (c) surfacing best-practice patterns for cross-spec traceability artefacts.

---

## Decisions

### D-001: Feature is documentation-only; zero runtime code changes

- **Decision**: This feature produces only Markdown edits under `specs/` and `specs/shared/`. No changes to `apps/web`, `apps/api`, `apps/agents`, `packages/`, `infra/`, or `scripts/`.
- **Rationale**: Spec FR-022 (append-only), FR-021 (zero `NEEDS CLARIFICATION`), and the explicit Out-of-Scope bullet "Rewriting working code in `apps/`, `packages/`, `infra/`, or `scripts/`" make this unambiguous. The three ambient runtimes (Next.js dashboard, FastAPI coordination API, Python autonomous agents) are **described by** the specs this feature hardens but are not **modified by** it.
- **Alternatives considered**:
  - *Combined doc + code pass* — rejected: expands blast radius, breaks reviewability, and conflicts with SC-003 (≤10-minute reviewer audit).
  - *Deferring docs until code changes land* — rejected: the capstone grading window demands portfolio-level alignment now; code changes are downstream of taxonomy decisions.

### D-002: Taxonomy and ID register inherited from spec 027

- **Decision**: Reuse spec 001 / spec 027 conventions exactly — `[TESTABLE|DECISION|RISK]` assumption tags, `ASM-###/HYP-###/PER-###/SCP-###/REQ-###` ID families in `specs/shared/gap-id-register.md`, persona YAML contract at `specs/027-spec-hardening/contracts/persona-profile.md`, hypothesis statement format from spec-027 FR-018.
- **Rationale**: Append-only (FR-022) is only possible if IDs extend the existing register. Reviewers already understand the 027 taxonomy; introducing a second taxonomy would violate SC-003.
- **Alternatives considered**:
  - *New monotonic register scoped to 028* — rejected: splits source of truth.
  - *Per-spec local IDs* — rejected: defeats cross-spec traceability (SC-002, FR-013).

### D-003: Capstone metric trace is a single static Markdown table

- **Decision**: `specs/shared/capstone-metric-trace.md` is one Markdown table with fixed columns `Metric | Country Cohort | SC Owner | HYP Owner | Baseline | Measurement Method | Status`, exactly 20 rows (5 metrics × 4 cohorts: AU-v1, PH, JP, BD). `Status ∈ {Validated, Deferred, Unresolved}`. `SC Owner` / `HYP Owner` cells cite `<spec>:<ID>` (e.g., `001:SC-004`) or literal `Deferred — preconditions: …`.
- **Rationale**: Clarified in Q3 (Session 2026-04-24). Grep-testable (SC-002, SC-007). Avoids YAML/JSON tooling cost for a document humans read in PR review.
- **Alternatives considered**:
  - *YAML front-matter + prose* — rejected: higher authoring cost, harder to diff.
  - *Per-metric sub-file* — rejected: explodes file count for no reviewer benefit.

### D-004: Language-code identifiers deferred to per-spec `research.md`

- **Decision**: Spec 008's language-pack FR (FR-006 of this feature) mandates "≥1 non-English language pack per capstone country" without locking BCP-47 codes. Identifier selection (Filipino vs Tagalog, Bengali locale variant, dialect coverage) is decided in the owning spec's own `research.md` when that feature is picked up.
- **Rationale**: Clarified in Q2. Locking codes now risks later contradiction with native-speaker / NPC / JMA guidance not yet sourced; deferring keeps the hardening feature stable.
- **Alternatives considered**:
  - *Lock `fil-PH`, `ja-JP`, `bn-BD`* — rejected: premature; PH has `tl-PH` + regional variants, BD has `bn-BD` vs `bn-IN` contention.
  - *Defer to spec 008 entirely* — rejected: breaks the "every agent spec gets ≥1 hypothesis per capstone country" (FR-011) triangulation.

### D-005: Recovery phase authoritative owner = spec 018

- **Decision**: Spec 018 (`aidr-guidance-integration`) is the authoritative owner of recovery-phase indicators, triggers, and phase-exit criteria. Spec 001 DEF-015 and spec 011 resource-recovery behaviour carry `defers-to: 018` pointers.
- **Rationale**: Clarified in Q1. Spec 018 is the only spec whose charter already cites the Community Recovery Handbook (2018) and the four recovery environments (Social / Built / Economic / Natural) — a direct match with constitution §VII-A/VII-B.
- **Alternatives considered**:
  - *Spec 001 as owner* — rejected: 001 is the roll-up and already carries DEF-015 (deferred).
  - *Spec 011 as owner* — rejected: 011 scopes resource allocation, not recovery phase as such.

### D-006: Evidence-stub schema is six fixed H2 headings

- **Decision**: Every new `evidence/HYP-*.md` stub uses exactly these H2 headings with minimum content: `## Hypothesis`, `## Preconditions` (≥2), `## Measurement Window`, `## Falsification Criterion` (≥1 quantified), `## Status` (= `Not tested`), `## Linked`.
- **Rationale**: Clarified in Q5. Fixed schema keeps SC-005 grep-testable, matches spec-027 FR-020 evidence-pack rule, keeps stub authoring cost ~10 minutes each.
- **Alternatives considered**:
  - *Free-form stubs* — rejected: Q5 option A — not grep-testable.
  - *Full YAML front-matter* — rejected: Q5 option C — disproportionate authoring cost for 15+ stubs.

### D-007: SC-009 rubric uplift = composite gate (Δmean ≥ 1 ∧ per-criterion Δ ≥ 0)

- **Decision**: SC-009 passes iff both conditions hold across the 5 rubric criteria tied to Assumptions / Requirements / Personas / Hypotheses / Scope: (i) mean score increases by ≥1 point vs baseline; (ii) no single criterion regresses.
- **Rationale**: Clarified in Q6. Prevents single-criterion strength masking regressions; reproducible via `ama-rubric-grader` skill against `AMA_Rubric_Asia.md`.

### D-008: Meta-spec / critical-path partition is final and closed

- **Decision**: Delivery-hygiene / meta specs: `003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028`. Capstone-critical-path specs: `001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023`. Partition is complete (16 + 11 = 27), disjoint, and closed for this feature.
- **Rationale**: Clarified in Q4. Complete partition lets FR-020 be checked by set comparison.

### D-009: AU-only-residency vs capstone sovereign-data — documented-but-unresolved

- **Decision**: The contradiction between constitution NON-NEGOTIABLE #2 ("All data MUST remain within Australian borders") and capstone Asia-framing (PH DPA 2012, JP APPI, BD DPA 2023 each imply in-country or sovereign-approved data handling) is documented as a `[RISK]` assumption in every spec touching PII, and named in this feature's Out-of-Scope as "not resolved here". Resolution requires a capstone-reinterpretation decision owned outside spec 028.
- **Rationale**: FR-022 (append-only) and the Out-of-Scope bullet make it explicit that this feature cannot overturn the constitution. Capturing the contradiction as a `[RISK]` assumption preserves auditability (constitution §IV) while not pretending the tension is solved.
- **Alternatives considered**:
  - *Resolve here* — rejected: constitution amendment requires project-lead approval (constitution §Governance), outside this feature's charter.
  - *Ignore* — rejected: violates SC-004 (no vague placeholders) and hides known material risk.

---

## Best-practice patterns applied

### P-001: Append-only ID register

Matches spec-027 FR-020 monotonicity; aligns with the "lessons management" quality gate (constitution §Quality Gates) — every new ASM/HYP reflects a lesson identified during the hardening pass.

### P-002: Per-spec evidence co-location

Evidence stubs live under `specs/NNN-*/evidence/HYP-*.md`, **not** centralised. This keeps the owning spec's review context self-contained (SC-003 ≤10-min audit) and mirrors the pattern already established by `027-spec-hardening/contracts/`.

### P-003: Country-cohort cells over free-form country prose

`Country Cohort ∈ {AU-v1, PH, JP, BD}` as a closed enum across the trace artefact, the metric trace, and every new hypothesis. Forces reviewers to triangulate by cohort rather than skim prose.

### P-004: Capstone hazard × constitution hazard union is explicit

The capstone adds typhoon (PH), earthquake (JP), riverine/cyclone-driven flood (BD). Constitution §III already covers cyclone, flood, earthquake generically. The hardening treats the capstone hazards as country-scoped instances of the constitution hazards, not new hazard classes — this avoids hazard-taxonomy drift in spec 012 (risk assessment).

---

## Unknowns resolved

| Original unknown | Resolution | Where resolved |
| --- | --- | --- |
| Recovery phase authoritative owner | Spec 018 (`aidr-guidance-integration`) | Clarification Q1; D-005 |
| BCP-47 codes for PH/JP/BD language packs | Deferred to per-spec `research.md` | Clarification Q2; D-004 |
| `capstone-metric-trace.md` schema | Fixed 7-column Markdown table, 20 rows | Clarification Q3; D-003 |
| Meta-spec list completeness | `003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028` | Clarification Q4; D-008 |
| Evidence-stub minimum content | Six fixed H2 headings | Clarification Q5; D-006 |
| SC-009 uplift threshold | Composite gate | Clarification Q6; D-007 |

**Result**: zero remaining `NEEDS CLARIFICATION` markers. Phase 0 exit gate satisfied.

---

## References

- `capstone.md` lines 32–41 (five success metrics; Asia regional specificity)
- `.specify/memory/constitution.md` v1.1.0 (especially §II-A, §V, §VI, §VII, §VIII, NON-NEGOTIABLE #1–#5)
- `specs/001-disaster-response-hub/spec.md` lines 103, 108, 441–446, 463–481
- `specs/027-spec-hardening/spec.md` (FR-018 hypothesis format; FR-020 evidence-pack rule; `contracts/persona-profile.md`)
- `specs/shared/gap-id-register.md` (monotonic ID source of truth)
- `AMA_Rubric_Asia.md` (SC-009 measurement surface)

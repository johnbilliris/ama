# Feature 028 — Always-Emit Decision File (T065)

> Per FR-021: this file is emitted at end of feature regardless of outcome. Captures the as-built decisions, the four documented tensions, and the residency / capstone-reinterpretation deferral.

## Outcome

**LANDED** — feature 028 closed with all SC-001..SC-009 gates passing (see `evidence/rubric-postfeature.md` for SC-009).

## Decisions reaffirmed at close

- **D-001 (documentation-only)**: feature 028 made append-only edits to `specs/` and `specs/shared/`. No runtime code, infrastructure, or schema changes. Validated by `git diff` review at PR.
- **D-005 (recovery-phase authority)**: spec `018-aidr-guidance-integration` is authoritative for recovery-phase indicators, triggers, and phase-exit criteria. Spec 001 DEF-015 and spec 011 carry the reciprocal `defers-to: 018` pointer. Verified by T046 and the overlap-rules audit.
- **D-009 (capstone-reinterpretation deferred)**: AU-only data residency (constitution NON-NEGOTIABLE #2; `australiaeast` / `australiasoutheast` only) is in tension with the capstone Asia framing (PH/JP/BD sovereign data handling). This feature **does NOT resolve** the tension; it tags it as `[RISK]` in the Assumptions of every PII-touching spec (24 specs), and defers resolution to a constitution-level amendment owned outside this feature.

## Open tensions documented (not resolved by feature 028)

1. **AU-only-residency vs capstone Asia framing** (D-009 above) — surfaced as `[RISK]` in 24 PII-touching specs and as a SCP item in spec 001 (SCP-080).
2. **Capstone-country hypothesis falsifiability gap** — 15 capstone-country HYPs (HYP-027..HYP-041) are `Status = Not tested` with evidence stubs in place; falsification cannot occur until D-009 clears AND per-cohort preconditions clear (data-sharing MoUs, language-pack QA, exercise packs).
3. **Persona placeholders** — non-AU personas (PH/JP/BD) carry `status: placeholder` per FR-023; SME validation requires the same D-009 + per-country engagement gate to clear.
4. **Pre-existing HYP-001..HYP-006 stub conformance** — six pre-existing stubs in spec 001 do not conform to the contract finalised in feature 028. Carry-over.

## Validation gates closed

| Gate | Result | Evidence |
| --- | --- | --- |
| SC-001 (≥3 ASM/PER/HYP/SCP per spec where applicable) | PASS | T058 validator: 27/27 specs True/True/True/True. |
| SC-002 (capstone metric trace populated, 0 Unresolved) | PASS | `specs/shared/capstone-metric-trace.md`: 20 rows, 5 Validated, 15 Deferred, 0 Unresolved. |
| SC-003 (per-spec AU vs capstone-country deferral explicit) | PASS | 24 specs carry capstone-country `[DEFERRED]` SCP entries with named preconditions; 11 meta specs flagged. |
| SC-004 (overlap rules reciprocal) | PASS | T044/T045/T046: spec 006 ↔ spec 008, spec 008 ↔ spec 018, spec 001/011 ↔ spec 018. |
| SC-005 (HYP evidence stubs conform) | PASS for new stubs (15/15). 6 pre-existing stubs documented as carry-over. |
| SC-006 (zero NEEDS CLARIFICATION introduced) | PASS | Validator reports 0 across all 27 specs. |
| SC-007 (gap-id register monotonic, append-only) | PASS | ASM 1..79, HYP 1..41, PER 1..76, SCP 1..82. PER/HYP reservations bumped from 50 to 100 by T060 to keep monotonic. |
| SC-008 (11 meta specs flagged) | PASS | All 11 meta specs carry the verbatim canonical bullet (count = 1 each). |
| SC-009 (rubric mean uplift) | PASS | Pre = 1.8 / 5 → Post = 3.8 / 5 (+2.0 bands), no per-criterion regression. |

## Sign-off

- Authoring: bulk-author scripts (`apply-us1-hardening.ps1`, `apply-us2-hypotheses.ps1`) plus targeted edits for spec 001 (T008) and spec 027 (T009).
- Validation: `validate-section-coverage.ps1`, overlap-rules grep audit, gap-id-register monotonicity check, HYP-stub structural validation, meta-flag count audit, post-feature rubric snapshot.
- Critique: rubber-duck pass and `/speckit.analyze` were not blocking-required at this checkpoint per plan.md (documentation-only feature). They MAY be performed before PR merge as additional confidence.

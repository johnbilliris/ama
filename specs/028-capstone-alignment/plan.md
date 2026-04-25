# Implementation Plan: Capstone Alignment Hardening Across AMA Specs

**Branch**: `028-capstone-alignment` | **Date**: 2026-04-24 | **Spec**: [`specs/028-capstone-alignment/spec.md`](./spec.md)
**Input**: Feature specification from `/specs/028-capstone-alignment/spec.md`

## Summary

Harden the 27-spec AMA portfolio so every spec under `specs/NNN-*/` carries testable **Assumptions, Personas, Hypotheses, and Out-of-Scope** sections aligned to the Asia-framed `capstone.md` brief (PH typhoons, JP earthquakes, BD floods, multilingual alerts, sovereign privacy regimes). Introduce a single cross-portfolio metric-trace artefact (`specs/shared/capstone-metric-trace.md`) and an evidence-stub contract so the five capstone success metrics each have named SC and HYP owners per country cohort.

**Approach**: documentation-only, append-only edits to Markdown under `specs/` and `specs/shared/`. No runtime code, no infrastructure, no schema changes. The three ambient AMA runtimes (Next.js dashboard, FastAPI coordination API, Python autonomous agents) are *described by* the specs this feature hardens but are *not modified by* this feature. All six clarification questions (sessions 2026-04-24 × 2) are resolved in [`research.md`](./research.md); zero `NEEDS CLARIFICATION` markers remain.

## Technical Context

**Language/Version**: N/A — documentation-only feature. (Portfolio-wide ambient stack, for reviewer context only: Python 3.12 (FastAPI API + agents), TypeScript / Next.js 16 (web dashboard), Bicep (infra). This feature does not edit any of these.)
**Primary Dependencies**: `specs/shared/gap-id-register.md` (monotonic ID source); `specs/027-spec-hardening/contracts/persona-profile.md` (YAML persona schema); `capstone.md` (authoritative brief); `AMA_Rubric_Asia.md` (SC-009 measurement surface); `ama-rubric-grader` skill (SC-009 automation).
**Storage**: N/A — Markdown files under version control only.
**Testing**: Grep + regex assertions on Markdown structure (see [`quickstart.md`](./quickstart.md)); row-count / column-schema validation on `capstone-metric-trace.md`; rubric-grader skill for SC-009.
**Target Platform**: Git repository; human reviewers on GitHub PRs.
**Project Type**: documentation / specification portfolio.
**Performance Goals**: reviewer audit time ≤ 10 minutes per spec (SC-003).
**Constraints**: append-only ID register (FR-022); zero `NEEDS CLARIFICATION` markers in `spec.md`/`research.md`/`tasks.md` (FR-021, SC-004); zero edits to code under `apps/`, `packages/`, `infra/`, `scripts/`.
**Scale/Scope**: 27 spec folders; 5 capstone metrics × 4 country cohorts = 20 trace rows; ≥15 new capstone-country-scoped hypotheses (SC-005); ~15 new evidence stubs.

## Constitution Check

*Gate: must pass before Phase 0 research. Re-checked after Phase 1 design.*

Constitution `v1.1.0` applies. This feature's Markdown-only scope makes most runtime gates non-applicable, but the *outcomes* of this hardening must preserve constitutional alignment of the specs it touches.

| Constitution clause | Applicability to this feature | Status |
| --- | --- | --- |
| §I Primacy of life & harm reduction | Reflected in SC-002 prioritising `LIVES_SAVED` as a first-class capstone metric and in the `HYP-###` evidence contract's falsification criteria. | ✅ Pass |
| §II Eleven AEMA principles | The hardened assumptions/hypotheses must remain consistent with the AEMA principles already in spec 001 / spec 018. Feature adds no new principle; augments country cohorts only. | ✅ Pass |
| §II-A AIIMS functional alignment | Preserved — spec 018 is confirmed authoritative owner of recovery (D-005) and keeps AIIMS authority. No agent responsibilities are renamed. | ✅ Pass |
| §III Multi-hazard, multi-agency | Strengthened — capstone hazards (typhoon/earthquake/flood per country) are now explicit cohort-scoped instances of the existing hazard taxonomy in spec 012 (P-004). | ✅ Pass |
| §IV Transparency & auditability | Strengthened — every new ASM/HYP gets a monotonic ID in `specs/shared/gap-id-register.md`; every HYP gets a structured evidence stub (FR-015, D-006). | ✅ Pass |
| §V Warning & public information | Language-pack FR (FR-006) preserves AWS nested model and ten warning principles by deferring to spec 008 / spec 010 (D-004). No conflict. | ✅ Pass |
| §VI Evacuation framework | Unchanged. Capstone metric `EVAC_LEAD_TIME` (24 h earlier evacuation) now has named SC/HYP owners per cohort. | ✅ Pass |
| §VII Recovery support | Authoritative recovery-phase owner = spec 018 (D-005, FR-018) — consistent with constitution §VII-A Community Recovery Handbook alignment. | ✅ Pass |
| §VIII Cloud platform & infrastructure | No infra change. Spec 017 adds a deferred FR for region-per-country topology; current AU-region default retained (FR-010). | ✅ Pass |
| NON-NEGOTIABLE #1 Human-in-the-loop | No automation is introduced. | ✅ Pass |
| NON-NEGOTIABLE #2 Data sovereignty (AU regions only) | ⚠️ **Documented tension**. Capstone (Asia framing) implies PH/JP/BD sovereign-data handling; constitution mandates AU-only residency. This feature **documents this contradiction** (D-009) as a `[RISK]` assumption in every spec touching PII and flags it in Out-of-Scope. It **does not resolve** the contradiction — resolution requires a capstone-reinterpretation decision owned outside this feature (constitution §Governance). | ⚠️ Documented, not resolved |
| NON-NEGOTIABLE #3 Privacy by design | Strengthened via FR-007 naming AU / JP / PH / BD privacy regimes as deferred-scope in spec 005. | ✅ Pass |
| NON-NEGOTIABLE #4 Interoperability (CAP/EDXL/GeoJSON/OpenAPI) | Unchanged; not touched by this feature. | ✅ Pass |
| NON-NEGOTIABLE #5 Graceful degradation | Unchanged. | ✅ Pass |
| Quality Gates — lint / tests / PR review | Markdown-only; PR requires ≥1 reviewer approval per §Governance. No new CI step required. | ✅ Pass |

**Gate decision**: **Pass with one documented tension** (NON-NEGOTIABLE #2). The tension is surfaced, justified (requires constitution-level amendment outside this feature's charter), and captured as a `[RISK]` assumption rather than hidden. Recorded in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/028-capstone-alignment/
├── plan.md                                     # This file (/speckit.plan output)
├── research.md                                 # Phase 0 output — 9 decisions + patterns
├── data-model.md                               # Phase 1 output — documentation entities
├── quickstart.md                               # Phase 1 output — reviewer audit steps
├── spec.md                                     # Feature spec (clarified)
├── checklists/
│   └── requirements.md                         # Quality checklist (all pass)
└── contracts/                                  # Phase 1 output
    ├── capstone-metric-trace.contract.md       # Schema for specs/shared/capstone-metric-trace.md
    ├── evidence-stub.contract.md               # Schema for evidence/HYP-*.md stubs
    └── meta-spec-flag.contract.md              # Required Out-of-Scope bullet for meta specs
```

### Source Code (repository root)

No source code changes. The existing repo layout is preserved unchanged:

```text
apps/
├── web/                    # Next.js 16 dashboard                 (untouched)
├── api/                    # FastAPI coordination API             (untouched)
└── agents/                 # Python autonomous agents             (untouched)

packages/
├── domain/                 # Pydantic domain models               (untouched)
└── ui/                     # Shared React components              (untouched)

infra/                      # Bicep templates                       (untouched)
scripts/                                                            (untouched)
tests/                                                              (untouched)

specs/
├── 001-disaster-response-hub/        ↕ edited (Out-of-Scope + defers-to pointers per FR-018)
├── 002..026/                         ↕ each gains mandatory H2 sections per FR-001..004
├── 027-spec-hardening/               ↕ FR-019 stale-028 reference replaced
├── 028-capstone-alignment/           ✚ this feature
├── shared/
│   ├── capstone-metric-trace.md      ✚ new artefact (20 rows)
│   └── gap-id-register.md            ↕ append new ASM/HYP/PER/SCP/REQ IDs
└── feature/                          ⨯ not edited (stale duplicates — Out-of-Scope)

capstone.md                                                         (untouched, authoritative)
AMA_Rubric_Asia.md                                                  (untouched, authoritative)
```

**Structure Decision**: documentation-only. Edits are contained to `specs/NNN-*/spec.md` (26 specs), `specs/028-capstone-alignment/*` (this feature's artefacts), `specs/shared/capstone-metric-trace.md` (new), `specs/shared/gap-id-register.md` (append-only). All three runtime apps, all packages, all infra, and all existing tests remain byte-identical.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| NON-NEGOTIABLE #2 (data sovereignty) tension documented-but-unresolved | The capstone's Asia framing is fundamentally incompatible with an AU-only residency constraint. Making the tension **visible** (as a `[RISK]` assumption in every affected spec) is a prerequisite for any future capstone-reinterpretation decision. | *Resolving it here* requires a constitution amendment which per §Governance needs explicit project-lead approval — outside this feature's charter. *Ignoring it* would let a known material risk propagate silently through Asia-framed hypotheses, violating §IV auditability and SC-004. |
| Adding a new shared artefact (`capstone-metric-trace.md`) rather than scattering the mapping across spec-001 | The capstone is judged on the **portfolio** meeting five metrics, not any single spec. A single-location trace is the only way SC-002 is grep-verifiable in < 1 minute by rubric evaluators. | *Embedding the trace in spec 001* couples 001's version cadence to every future metric promotion and reintroduces the reviewer-navigation cost the trace is designed to eliminate. |

## Post-Design Constitution Re-Check

After Phase 1 artefact generation, the constitution check result is **unchanged**. The contracts (`capstone-metric-trace.contract.md`, `evidence-stub.contract.md`, `meta-spec-flag.contract.md`) formalise — but do not expand — the scope already cleared by the initial gate. The documented data-sovereignty tension remains captured in Complexity Tracking and will reappear as a `[RISK]` assumption in every PII-touching spec during `/speckit.tasks`. No gate escalation required.

## Progress Tracking

- [x] Phase 0 research complete (9 decisions, 4 patterns, 6 unknowns → all resolved)
- [x] Phase 1 design complete (data-model.md, 3 contracts, quickstart.md)
- [x] Constitution gate passed (one documented tension, Complexity Tracking updated)
- [x] Agent context file refreshed via `update-agent-context.ps1 -AgentType copilot`
- [ ] Phase 2 tasks — owned by `/speckit.tasks` (NOT produced by `/speckit.plan`)

## Artefact index

| Artefact | Path | Phase |
| --- | --- | --- |
| Feature spec | `specs/028-capstone-alignment/spec.md` | Input |
| Quality checklist | `specs/028-capstone-alignment/checklists/requirements.md` | Input |
| Research & decisions | `specs/028-capstone-alignment/research.md` | 0 |
| Data model | `specs/028-capstone-alignment/data-model.md` | 1 |
| Contract — metric trace | `specs/028-capstone-alignment/contracts/capstone-metric-trace.contract.md` | 1 |
| Contract — evidence stub | `specs/028-capstone-alignment/contracts/evidence-stub.contract.md` | 1 |
| Contract — meta-spec flag | `specs/028-capstone-alignment/contracts/meta-spec-flag.contract.md` | 1 |
| Quickstart (reviewer audit) | `specs/028-capstone-alignment/quickstart.md` | 1 |

## Suggested next command

`/speckit.tasks` — decompose Phase 2 work into dependency-ordered, per-spec tasks (26 spec-edit tasks + 1 metric-trace task + 1 gap-id-register task + ~15 evidence-stub tasks + 1 SC-009 rubric baseline-snapshot task + 1 post-feature rubric-snapshot task).

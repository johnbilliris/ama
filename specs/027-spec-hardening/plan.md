# Implementation Plan: Capstone Specification Hardening

**Branch**: `027-spec-hardening` | **Date**: 2026-04-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/027-spec-hardening/spec.md`

## Summary

Feature 027 is a **documentation-hardening** feature that amends `specs/001-disaster-response-hub/spec.md` to resolve the 40 gaps raised by the critical review (A-GAP / REQ-GAP / PER-GAP / HYP-GAP / SCP-GAP) and 10 clarifications recorded in this feature's Clarifications section. It produces no runtime code in this branch. Its three deliverable artefact classes are:

1. **Normative content inside spec 001** — new Assumptions register, NFRs, Personas cross-reference, Hypotheses register, Scope subsections (v1 Primary Jurisdiction, Deferred-Scope Register, Autonomy Boundary Table, Hazard List, Citizen-Surface List, Upstream/Downstream Integrations), Status-transition Authority subsection, Changelog (FR-033) with a pointer to the 027 Traceability Table, and an Open Deltas subsection.
2. **Shared governance artefacts** — `specs/shared/gap-id-register.md` (FR-036), `.github/CODEOWNERS` entry for `specs/001-disaster-response-hub/` (FR-034), and per-hypothesis Evidence Pack stubs at `specs/<owning-feature>/evidence/<HYP-ID>.md` (FR-020).
3. **Change-record content inside spec 027** — the canonical Traceability Table (FR-031), referenced from spec 001 by anchor; and the Open Deltas subsection seeded from the spec-001 contradiction sweep (FR-032).

The subject runtime stack of the hardened spec (which 027 amends but does not build) remains as already defined in `specs/001-disaster-response-hub/plan.md`: a Next.js/TypeScript web dashboard on Azure App Service, a FastAPI/Python 3.12 coordination API on Azure Container Apps, Python-based Microsoft Agent Framework agents on Azure Container Apps, backed by Azure Cosmos DB + Blob + Cache for Redis, all in Azure Australia East / Australia Southeast. 027 sharpens the requirements describing that stack; it does not change any runtime code.

## Technical Context

**Language/Version**: Markdown (CommonMark + GitHub-flavoured Markdown); no runtime language used by this feature.
**Primary Dependencies**:

- Spec-Kit PowerShell toolchain (`.specify/scripts/powershell/*.ps1`) for plan/task/clarify lifecycle;
- GitHub CODEOWNERS mechanism for the FR-034 countersign attribution;
- `markdownlint-cli2` (already available via `pnpm` workspace) for spec-file lint gates;
- Git + GitHub PR review as the only enforcement surface.

**Storage**: Git (version-controlled markdown under `specs/` and `.github/`). No database, no blob store.

**Testing**:

- Markdown lint on every file authored/amended by this feature.
- A repo-local verification script (Phase 2 task) that checks:
  (a) every A-GAP / REQ-GAP / PER-GAP / HYP-GAP / SCP-GAP ID cited in spec 001 or 027 appears in `specs/shared/gap-id-register.md` with status ≠ *Withdrawn*;
  (b) every HYP-### cited in spec 001 has a corresponding `specs/001-disaster-response-hub/evidence/HYP-###.md` stub on disk, **unless the citation is explicitly listed as a dangling anchor in the spec 001 § Open Deltas subsection with a `blocking_phase` field** — such exemptions are permitted only between a citation-insert task and its paired stub-creation task in the same PR and MUST be cleared before `/speckit.implement` starts;
  (c) every NFR in spec 001 carries drafter + basis + countersign fields (FR-035);
  (d) no Open Delta with a `target-feature` field references a feature whose `plan.md` already exists (FR-032 deadline).
- Link-check (relative paths only) via `markdown-link-check` or equivalent.

**Target Platform**: GitHub repository / Spec-Kit workflow. No deployable target.

**Project Type**: Documentation change with shared-register side-effects. Non-code feature operating across three directories: `specs/001-disaster-response-hub/`, `specs/027-spec-hardening/`, and `specs/shared/` + `.github/`.

**Performance Goals**: N/A. Review-experience target (SC-001): a new reviewer can answer four capstone-alignment questions within one read of spec 001.

**Constraints**:

- Must not modify runtime code (`apps/`, `packages/`, `infra/`) in this feature branch — any code-level follow-up is logged as an Open Delta with a `target-feature` ID per FR-032.
- Must not create a second hardening taxonomy — 028 owns cross-spec propagation (Clarification 1).
- Must not duplicate the Traceability Table — canonical copy lives in 027, spec 001 carries a pointer row (Clarification 10, FR-031).
- All status-bearing artefacts (Assumption / Hypothesis / Persona) require the dual-signature governance defined in FR-034.
- Gap-ID allocation must be monotonic across the monorepo (FR-036).

**Scale/Scope**: 36 Functional Requirements × amendments to 1 source spec + 2 shared artefacts; **≥ 6 Hypotheses (one per FR-019 theme) → ≥ 6 Evidence Pack stubs**; **18 validated Personas** (7 operational + 2 executive + 5 community + 2 adversarial + 2 accessibility-operator) × 1 jurisdiction (Australia) at v1; Deferred-Scope Register carries **3 deferred jurisdictions + 7 deferred hazards** (every Constitution Principle III hazard not promoted into v1).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate Review

- **I. Primacy of Life and Harm Reduction** — PASS. Hardening sharpens FR-011 (medical triage / shelter / utility / SAR scope), FR-012 (misinformation), and FR-025 (autonomy boundary table) so life-safety recommendations carry explicit HITL or advisory-only classifications. No requirement is weakened.
- **II. National EM Principles / II-A AIIMS Alignment** — PASS. Personas register (FR-015) enumerates AIIMS operational roles (Incident Controller, Ops Officer, Logistics Lead, PIO, Field Coordinator, Resilience Planner, Auditor) and SC-004 makes their coverage testable. The Spec's §Scope/§Assumptions now name AIIMS explicitly as the v1 coordination frame.
- **III. Multi-Hazard, Multi-Agency Design** — PASS (with explicit deferral). FR-024 now requires every Principle III hazard not promoted into v1 scope (earthquake, tsunami, extreme heat, pandemic/biosecurity, CBRN, space weather, cyber-physical) to be carried in the Deferred-Scope Register with rationale, extensibility evidence, and promotion preconditions. No Principle III hazard is silently excluded.
- **IV. Transparency and Auditability** — PASS. FR-013 mandates audit retention duration, format, and recoverability SLO; FR-033 records a dated changelog; FR-034 requires dual signatures for status transitions; FR-020 mandates Evidence Packs for every hypothesis; FR-036 mandates a monotonic gap-ID register. All contribute to a stronger audit trail for the subject platform.
- **V. Warning and Public Information (incl. AWS, Ten Principles, Total Warning System)** — PASS. FR-009 requires CAP 1.2 interoperability; FR-025 classifies *Public alert publication* in the autonomy-boundary table; FR-012 covers misinformation detection with operator-visible evidence. The hardened spec is consistent with AWS nesting and the Ten Warning Principles; where it is not, the contradictions are tabled as Open Deltas per FR-032.
- **VI. Evacuation Framework** — PASS. FR-025 classifies *Evacuation routing* explicitly; FR-015 includes Field Coordinator and Logistics Lead personas; vulnerable-population archetypes (CALD, accessibility-impaired, tourist) are mandated in FR-015(c)(d)(e).
- **VII. Recovery Support** — PASS. FR-027 requires the Spec to state whether Recovery (PPRR) is in-scope for v1 and, if not, to describe the hand-off contract. No recovery claims are smuggled in without scope declaration.
- **VIII. Cloud Platform and Infrastructure** — N/A to this feature (no infra change); constraint preserved unchanged in spec 001 and re-asserted by the §Scope hardening (FR-029 upstream/downstream integrations enumeration keeps Azure Australia East/Southeast in scope).

### Non-Negotiable Requirements

1. **Human-in-the-loop** — PASS. FR-025 autonomy boundary table is mandated; Clarification 2 (FR-034) requires dual signatures for any status transition.
2. **Data sovereignty** — PASS. FR-006 mandates in-region storage and cross-border transfer rules; no hardening content relaxes the Australian-region floor.
3. **Privacy by design** — PASS. FR-006 normative privacy NFRs; FR-035 requires privacy-reviewer countersign on privacy/legal NFRs.
4. **Interoperability** — PASS. FR-009 names CAP 1.2, EDXL-DE, and Sendai indicators as interoperability NFRs.
5. **Graceful degradation** — PASS. Preserved from spec 001; hardening neither weakens nor removes the requirement.

**Result**: PASS. No violations; no entry needed in Complexity Tracking.

### Post-Design Gate Review (see Phase 1 artefacts)

- **I, IV, V** — REVIEWED. `data-model.md` schemas for Assumption, NFR, Persona, Hypothesis, Evidence Pack, Open Delta preserve drafter/countersigner/basis/evidence fields required by FR-034 and FR-035. No schema admits a status transition without the signatures.
- **II-A AIIMS** — REVIEWED. Persona schema carries `aiims_function` as a required enum spanning the six AIIMS functions (Control / Intelligence / Planning / Operations / Logistics / Public Information) plus two sentinel values for non-AIIMS roles (`Non-AIIMS-Community`, `Non-AIIMS-Governance`); SC-004 still requires at least one persona per AIIMS function, testable by inspection.
- **VIII Cloud Platform** — REVIEWED. No design artefact in this feature touches Azure resources.
- **Non-Negotiable #4 (Interoperability)** — REVIEWED. `contracts/` carries the NFR-row template that explicitly requires a `standard_reference` field citing CAP 1.2, EDXL-DE, or Sendai where applicable.

**Result**: PASS. No new violations introduced by Phase 1 design.

## Project Structure

### Documentation (this feature)

```text
specs/027-spec-hardening/
├── plan.md                 # This file
├── research.md             # Phase 0 output
├── data-model.md           # Phase 1 output — markdown schemas for state-bearing entities
├── quickstart.md           # Phase 1 output — walkthrough for planner / test lead / UX lead
├── contracts/              # Phase 1 output — templates authored by this feature
│   ├── assumption-row.md           # FR-001 row template
│   ├── nfr-row.md                  # FR-004 / FR-035 row template
│   ├── persona-profile.md          # FR-015 / FR-016 profile template
│   ├── hypothesis-row.md           # FR-018 / FR-020 row template
│   ├── evidence-pack-stub.md       # FR-020 stub template
│   ├── open-delta-row.md           # FR-032 row template
│   ├── traceability-row.md         # FR-031 row template
│   ├── gap-id-register-row.md      # FR-036 row template
│   └── codeowners-entry.md         # FR-034 CODEOWNERS fragment
└── tasks.md                # Phase 2 output — NOT created by /speckit.plan
```

### Side-effect directories (created or modified by this feature's tasks)

```text
specs/001-disaster-response-hub/
├── spec.md                         # Amended: new §Assumptions, §NFRs, §Personas cross-reference,
│                                   #          §Hypotheses, §Scope hardening subsections, §Changelog
│                                   #          pointer to 027 Traceability Table, §Open Deltas
└── evidence/                       # Created: stub files per hypothesis (HYP-001.md .. HYP-###.md)

specs/shared/
└── gap-id-register.md              # Created: monotonic register seeded with current review gap IDs

.github/
└── CODEOWNERS                      # Amended or created: entry for specs/001-disaster-response-hub/

scripts/
└── verify-spec-hardening.ps1       # Created: invariant-enforcement script (see §Testing); CI gate

# Root-level lint config touched only if the existing rules break on new spec files:
└── .markdownlint.jsonc             # Amended only if necessary (scope-limited exceptions for specs/ tables)

specs/027-spec-hardening/
└── checklists/requirements.md      # Created: reviewer checklist referenced by §Evaluation Method
```

### Source Code (repository root)

Not applicable. This feature produces no changes under `apps/`, `packages/`, `infra/`, `data/`, `scripts/`, `tests/`, or any runtime path.

The subject runtime stack that spec 001 describes (and that 027 amends the requirements for) remains:

```text
apps/
├── web/      # Next.js 16 + TypeScript dashboard (Azure App Service) — unchanged in 027
├── api/      # FastAPI + Python 3.12 coordination API (Azure Container Apps) — unchanged in 027
└── agents/   # Python Microsoft Agent Framework specialists (Azure Container Apps) — unchanged in 027

packages/
├── domain/   # Pydantic v2 shared models — unchanged in 027
└── ui/       # Shared React components — unchanged in 027

infra/       # Bicep Azure resources, Australia East / Southeast — unchanged in 027
```

**Structure Decision**: Documentation-led feature with narrowly scoped write locations. Primary writes: `specs/001-disaster-response-hub/`, `specs/027-spec-hardening/`, `specs/shared/`, `.github/CODEOWNERS`. Tooling writes (non-runtime): `scripts/verify-spec-hardening.ps1` (CI invariant gate), `.markdownlint.jsonc` (lint-config tweaks only if existing rules break on new spec files), and `specs/027-spec-hardening/checklists/requirements.md` (reviewer checklist referenced by §Evaluation Method). No runtime directory (`apps/`, `packages/`, `infra/`, `data/`, `tests/`) is touched; any runtime implication surfaces as an Open Delta with a `target-feature` ID per FR-032.

## Complexity Tracking

*Not required — Constitution Check passed with no violations.*

---

## Phase status

- **Phase 0 (research)**: complete — see `research.md`.
- **Phase 1 (design & contracts)**: complete — see `data-model.md`, `contracts/*`, `quickstart.md`.
- **Phase 2 (tasks)**: NOT started — run `/speckit.tasks` next.

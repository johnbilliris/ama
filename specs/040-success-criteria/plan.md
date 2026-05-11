# Implementation Plan: Measurable Success-Criteria Evidence Harness

**Branch**: `040-success-criteria` | **Date**: 2026-05-11
**Spec**: [`specs/040-success-criteria/spec.md`](./spec.md)
**Input**: Feature specification at `/specs/040-success-criteria/spec.md`

## Summary

Build a six-pillar **prototype evidence harness** that demonstrates the
AMA prototype's five capstone success criteria (lives saved, response
time, evacuation lead-time, logistics efficiency, economic-loss
reduction — owned by spec 015) are *measurable*, end-to-end and
audit-traceably, without making any production claim.

Technical approach: a single backend service
`apps/api/app/services/evidence/` with six pillar sub-modules, fronted
by a new `governance/evidence/` route in the existing Next.js
`PersonaWorkspace` shell, persisted in seven new AU-region Cosmos DB
containers plus a 7-year cold-archive Blob, deployed via one new
Bicep module wired into `infra/bicep/main.bicep`. Replay reuses the
existing simulation engine (specs 007/024/026); confidence bands use a
bootstrap-95 % CI helper; LLM use is summarisation-only via the
existing `apps/agents/common/llm_client.py`. Zero new languages, zero
new chart libraries, zero new UI primitives (FR-013 / FR-034).

## Technical Context

**Language/Version**: Python 3.12 (backend) + TypeScript 5.8 (frontend) + Bicep (IaC)
**Primary Dependencies**: FastAPI + Pydantic v2 (backend), Next.js 14 + the existing `PersonaWorkspace` shell (frontend), Azure SDK for Python (Cosmos + Blob), `apps/agents/common/llm_client.py` and `…/retrieval_client.py` (LLM-assisted summarisation only — D6)
**Storage**: Azure Cosmos DB SQL API in `australiaeast` (primary) + `australiasoutheast` (paired DR) — seven containers; Azure Storage Blob (Cool tier, 7-year immutability lock) for audit cold-archive
**Testing**: `pytest` (contract + integration under `tests/contract/` and `tests/integration/`), Playwright + axe-core for the frontend WCAG 2.2 AA + 8-language render
**Target Platform**: Azure Container Apps (existing `ca-api-ama` for backend, `ca-agents-ama` retains agent runtimes — no new containers); Next.js SSR/ISR served via the existing web app
**Project Type**: Web service + web frontend (extension of existing AMA monorepo)
**Performance Goals**: Evidence-endpoint availability ≥99.5 %; replay job success rate ≥98 %; metric freshness ≤60 s (App Insights); SC-005 audit-walk under 3 minutes; SC-002 measurement-method lookup under 2 minutes
**Constraints**: AU-only data residency for KPI / scenario / audit data (FR-029); life-safety > efficiency in any rollup ranking (FR-006); advisory-only outputs (FR-030); CAP/EDXL/GeoJSON/OpenAPI-compatible export (FR-031); graceful degradation under any single signal-source failure (FR-027 / FR-032); reuse-only — no new chart libraries / UI primitives / language assets / simulation engines (FR-013 / FR-034 / FR-037)
**Scale/Scope**: Five capstone KPIs × seven canonical scenarios × two run modes; ~7 capability causal chains (specs 008–012, 036, 036-sim-agent-extend); 8-language Public Information render; ≥7-year audit retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version: **v1.2.0** (file: `.specify/memory/constitution.md`).

| # | Principle / Gate                                     | Spec FR / SC anchor                | Plan compliance                                                                                                                                                  | Pass? |
| - | ---------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| 1 | I. Primacy of Life and Harm Reduction                | FR-006, FR-024, FR-030             | `IndicatorDefinition.life_safety_tier` ranks life-safety above efficiency in every rollup; low-confidence signals MUST be advisory-only and reduced-fidelity     | ✅    |
| 2 | II. National Emergency Management Principles (AEMA) | FR-001, FR-031                     | KPI ladder maps to AIIMS functions + incident levels (FR-003); exports are CAP/EDXL/GeoJSON/OpenAPI-compatible                                                   | ✅    |
| 3 | II-A. AIIMS Functional Alignment                     | FR-003                             | Indicator decomposition by AIIMS function (Control, Intelligence, Planning, Operations, Logistics, Public Information) is required at write-time                | ✅    |
| 4 | III. Multi-Hazard, Multi-Agency Design               | FR-011                             | Canonical scenario set covers bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR                                                            | ✅    |
| 5 | IV. Transparency and Auditability                    | FR-023..FR-026, SC-005             | Append-only `evidence_audit` Cosmos container + 7-year Blob immutability; trace endpoint walks signal → model → recommendation → human decision → outcome       | ✅    |
| 6 | V. Warning and Public Information                    | FR-037, SC-013                     | Public Information KPI render reuses `apps/web/src/lib/i18n/language-packs.ts` for 8 channels (English + 5 ABS-Census + Auslan + ≥1 First-Nations); WCAG 2.2 AA | ✅    |
| 7 | AU Sovereignty                                       | FR-029, SC-009                     | Cosmos + Blob pinned to `australiaeast`/`australiasoutheast`; non-AU signals refused at write and refusal recorded in `evidence_audit`                          | ✅    |
| 8 | Advisory-only / human-in-the-loop                    | FR-030                             | No autonomous action — all endpoints return advisory data; `ProblemDetails.ama_advisory_only=true`                                                              | ✅    |
| 9 | Graceful degradation                                 | FR-027, FR-032                     | Replay endpoint accepts `allow_degraded_mode`; reduced-fidelity flags propagate to scorecards; chaos drills validate three failure modes                         | ✅    |
|10 | Reuse-only / no new primitives                       | FR-013, FR-034, FR-035, FR-036     | No new sim engine (reuses 007/024/026); reuses governance dashboard shell + i18n catalogue; consumes spec-030 LLM eval outputs; contributes to spec-037 pack    | ✅    |
|11 | Capstone exclusion                                   | FR-033, SC-011                     | Plan includes a §"Capstone-trace tagging step" recording the row text to be appended to `specs/shared/capstone-metric-trace.md`                                  | ✅    |

**Result**: All gates pass. **No violations** → `Complexity Tracking`
section below is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/040-success-criteria/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 — D1..D14 decisions + rationale
├── data-model.md        # Phase 1 — Cosmos containers + Pydantic v2 models
├── quickstart.md        # Phase 1 — local dev / test / deploy walkthrough
├── contracts/
│   └── openapi.evidence-harness.yaml   # Phase 1 — six endpoints + healthz
└── tasks.md             # Phase 2 — produced by /speckit.tasks (NOT by /speckit.plan)
```

### Source Code (repository root)

```text
apps/
├── api/
│   ├── Dockerfile                                  # REUSED (no changes)
│   └── app/
│       └── services/
│           └── evidence/                           # NEW — single backend module
│               ├── __init__.py
│               ├── router.py                       # FastAPI router prefix /api/v1/evidence
│               ├── health.py                       # /healthz/evidence
│               ├── models/                         # Pydantic v2 models per data-model.md
│               │   ├── kpi.py
│               │   ├── signal.py
│               │   ├── scorecard.py
│               │   ├── chain.py
│               │   ├── benchmark.py
│               │   └── audit.py
│               ├── kpi_ladder/                     # Pillar A
│               ├── measurement/                    # Pillar B
│               │   └── confidence.py               # bootstrap-95 % CI helper (reuses spec-030 pattern)
│               ├── simulation/                     # Pillar C — orchestrator over specs 007/024/026
│               ├── impact/                         # Pillar D
│               ├── benchmarks/                     # Pillar E
│               └── instrumentation/                # Pillar F — signal ingest + audit
└── web/
    ├── src/
    │   ├── app/
    │   │   └── governance/
    │   │       └── evidence/                       # NEW — sibling to executive/, dashboard/, data-sources/
    │   │           ├── page.tsx                    # PersonaWorkspace shell w/ 6 tabs
    │   │           └── _tabs/                      # KpiLadderTab, MeasurementTab, ReplayTab, ImpactTab, BenchmarkTab, AuditTab
    │   └── lib/
    │       └── i18n/
    │           └── language-packs.ts               # REUSED (no new language assets) — FR-037
    └── tests/
        └── playwright/
            └── governance/
                └── evidence.spec.ts                # NEW — WCAG 2.2 AA + 8-language render

packages/
└── domain/
    └── src/
        ├── domain/
        │   └── models/
        │       └── evidence_*.py                   # NEW Python twins (reuse pattern)
        └── evidence/
            └── *.ts                                # NEW TS twins matching Pydantic schema

infra/
└── bicep/
    ├── main.bicep                                  # EDITED — adds module + enableEvidenceHarness param
    └── modules/
        └── evidence-harness.bicep                  # NEW — 7 Cosmos containers + cold-archive Blob + AppI workbook

tests/
├── contract/
│   ├── test_evidence_kpi_ladder.py                 # NEW — validates against contracts/openapi.evidence-harness.yaml
│   ├── test_evidence_measurement_method.py
│   ├── test_evidence_replay.py
│   ├── test_evidence_causal_chain.py
│   ├── test_evidence_benchmarks.py
│   ├── test_evidence_audit.py
│   └── test_evidence_healthz.py
└── integration/
    ├── test_replay_determinism.py                  # SC-004 — ±2 % rel / ±1 unit, ≥95 % reproduction
    ├── test_baseline_vs_ama_delta.py               # SC-003 — 7 scenarios × 5 KPIs
    ├── test_imputation_rule.py                     # FR-008 — forward-impute + small-sample gate
    ├── test_au_region_refusal.py                   # FR-029 / SC-009
    └── test_audit_append_only.py                   # FR-025

specs/
└── shared/
    └── capstone-metric-trace.md                    # EDITED — append non-capstone-critical-path row (FR-033 / SC-011)
```

**Structure Decision**: Web-application layout extending the existing
AMA monorepo. Backend code is a single new module under
`apps/api/app/services/evidence/` (mirrors `services/eval`,
`services/governance`, `services/simulation`, `services/ingestion`).
Frontend code is a single new route under
`apps/web/src/app/governance/evidence/` (sibling to the existing
`executive`, `dashboard`, and `data-sources` routes), reusing the
`PersonaWorkspace` shell and the `language-packs.ts` i18n catalogue.
IaC is a single new Bicep module under `infra/bicep/modules/`,
following the AVM-first policy in
`.github/instructions/bicep-code-best-practices.instructions.md`.

## Phase 0 — Outline & Research

Output: [`research.md`](./research.md). Fourteen decisions D1..D14
recorded with rationale and alternatives considered. **No `NEEDS
CLARIFICATION` items remain** — every spec clarification was resolved
inside the spec itself (Round 1 + Round 2 in `Session 2026-05-11`),
and every technical choice cites either the spec, the constitution, or
a concrete reuse target in the existing codebase.

## Phase 1 — Design & Contracts

Outputs:

- [`data-model.md`](./data-model.md) — nine Key Entities mapped to
  seven Cosmos containers with partition keys and Pydantic v2 model
  signatures; cross-entity invariants for AU sovereignty, life-safety
  primacy, advisory-only banner, and append-only audit.
- [`contracts/openapi.evidence-harness.yaml`](./contracts/openapi.evidence-harness.yaml)
  — OpenAPI 3.1 covering all six published endpoints
  (`/api/v1/evidence/{kpi-ladder,measurement-method,scenarios/{id}/replay,causal-chains/{id},benchmarks/{kpi_id},audit/{value_id}}`)
  plus `/healthz/evidence`.
- [`quickstart.md`](./quickstart.md) — local dev, test, deploy, chaos
  drill, and the don't-do list of constitution + reuse non-negotiables.

### Agent context update

After plan acceptance, run:

```powershell
.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot
```

This appends the spec-040 (originally Spec-038) technologies to the active Copilot context
file (preserves manual edits between markers, only adds new
technology). No new technology is introduced; the script will record
the new `apps/api/app/services/evidence/` module path and the new
`apps/web/src/app/governance/evidence/` route path so downstream
agents can find them.

### Post-design Constitution re-check

Re-evaluating the gates table after Phase 1 with the data-model and
contracts in hand:

| Gate                      | Re-check after Phase 1                                                                                                              | Pass? |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----- |
| AU sovereignty (FR-029)   | Cosmos + Blob region pinned in Bicep; data-model invariant rejects non-AU writes; OpenAPI `Signal.region` is enum-restricted        | ✅    |
| Life-safety primacy       | `IndicatorDefinition.life_safety_tier` is mandatory enum; rollup endpoint contract sorts by tier first                              | ✅    |
| Advisory-only             | `ProblemDetails.ama_advisory_only=true`; `DeltaScorecard.advisory_only=true` default                                                | ✅    |
| Append-only audit         | `evidence_audit` Cosmos rejects PATCH/DELETE at Manager tier; `kpi_amendment_recorded` is the only mutation pattern                 | ✅    |
| Graceful degradation      | `ReplayRequest.allow_degraded_mode`; `reduced_fidelity` flag on `KpiDelta` and `Signal`; chaos drills (D12)                          | ✅    |
| Reuse-only                | No new chart libs, primitives, language assets, or sim engines surface in the data model or contracts                               | ✅    |
| Capstone exclusion        | Plan §"Capstone-trace tagging step" + quickstart §7 carry the verbatim row to be appended                                           | ✅    |

**Result**: All gates still pass post-design. No `Complexity Tracking`
entries required.

## Phase 2 — Stop here

Per the speckit.plan contract, this command stops after Phase 1
planning. `tasks.md` is produced by `/speckit.tasks` against the
artefacts above and is not created here.

## Capstone-trace tagging step (FR-033 / SC-011)

The implementing PR (or the first task in `tasks.md`) MUST append the
following row at the end of the *"Spec-level capstone-criticality
flags"* table in `specs/shared/capstone-metric-trace.md`, mirroring the
existing spec-037 row:

```markdown
| `specs/040-success-criteria/` | non-capstone-critical-path / delivery-hygiene | `specs/040-success-criteria/spec.md` FR-033 + SC-011 | spec-040 (originally Spec-038) produces a measurement *harness* that demonstrates the prototype's capstone success criteria are measurable; it does NOT itself contribute a capstone success-criterion metric and MUST be excluded from capstone-metric attribution roll-ups (precedent: spec-037 FR-020). |
```

This single-line edit satisfies SC-011 and is the only change required
to `specs/shared/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| _(none)_  | _(n/a)_    | _(n/a)_                              |

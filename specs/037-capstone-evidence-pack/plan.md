# Implementation Plan: Capstone Evidence Pack — Residual Rubric Gap Closure

**Branch**: `037-capstone-evidence-pack` | **Date**: 2026-05-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from [`specs/037-capstone-evidence-pack/spec.md`](./spec.md)

## Summary

Spec-037 closes the five residual rubric gaps identified in the Step 0 review by publishing five durable, evidence-bearing, version-controlled artefacts — Systematic Risk Register, Adoption Roadmap, Executive KPI Surface, Responsible AI Register, and Feature-to-Value Ledger + Decision/Tradeoff Log — and by exposing the Executive KPI Surface as a thin read-only Next.js page composed from the existing `apps/web/src/app/governance/` shell delivered by spec-035. The pack is **delivery-hygiene** (`028-capstone-alignment` FR-020): it proves value already shipped by specs 001–036 against the assessment rubric and **does not directly contribute a capstone success-criterion metric**.

The technical approach is deliberately minimalist and **introduces zero net-new Azure resources**. The five artefacts are Markdown + JSON sidecars stored in-repo under `docs/` and `specs/shared/`, validated by JSON Schema (draft 2020-12) under `packages/schemas/spec_037/`, and published through a new CI job `evidence-pack-publication-gate` that extends `.github/workflows/ci.yml`. A small set of read-only FastAPI routes under `apps/api/app/api/routes/governance/evidence_pack.py` serve the artefacts to the new `apps/web/src/app/governance/executive/` page; both reuse the existing JWT/AppRole middleware, append-only audit writer pattern, and the existing Container App `ca-api-ama` + App Service `app-ama-zo6bb5` revisions in `rg-ama` (AU East). Two new App Insights custom metrics — `evidence_pack.publication.duration_seconds` and `evidence_pack.manual_row_ratio` — emit through the existing OpenTelemetry pipeline.

The four spec-clarifications captured in [`spec.md` § Clarifications](./spec.md#clarifications) lock the contract surface: **Q1** locks the manual-stub provenance contract (`provenance: manual` + named owner + review cadence + automation_target + `manual_row_count` counter); **Q2** treats the `036-sim-agent-extend` telemetry-injection agent as a full production AI component for RAI scope (4 frameworks × 8 principles, no reduction for the simulation watermark); **Q3** locks the new `apps/web/src/app/governance/executive/` route as the host shell with no net-new UI primitives; **Q4** locks the per-artefact `manual_row_ratio ≤ 0.5` cap with a named-auditor sign-off override path enforced by the publication CI gate. The synthesised 17-persona technical-cohort input (`<session>/files/step4-tech-synthesis.md`) is honoured directly in [research.md](./research.md) as the source for the chosen schema, IA, web-shell composition, CI-gate, and provenance-measurement strategies.

## Technical Context

**Language/Version**:

- Web: TypeScript 5.8, Next.js 15 (App Router), React 19, Node.js ≥ 20
- API: Python 3.12, FastAPI (existing), Pydantic v2
- Schema tooling: `jsonschema>=4.21` (draft 2020-12), `pyyaml`
- Tests: pytest (API + schema), Vitest (web unit), Playwright (read-only smoke), `@axe-core/playwright`

**Primary Dependencies**:

- Web: existing governance shell from spec-035 (`PersonaWorkspace`, audit-row read primitives) under [`apps/web/src/app/governance/dashboard/`](../../apps/web/src/app/governance/dashboard/); `@azure/msal-react` for Entra bearer; **no new chart libraries, no new UI primitives**
- API: FastAPI, Pydantic v2, `azure-identity`, the existing append-only audit pattern at [`apps/api/app/services/simulation/audit_writer.py`](../../apps/api/app/services/simulation/audit_writer.py)
- Shared: [`packages/domain/src/domain/models/`](../../packages/domain/src/domain/models/) (Pydantic v2 models), [`packages/schemas/`](../../packages/schemas/) — new `spec_037/` directory mirroring the established `spec_035/` and `spec_036/` layout

**Storage**:

- **Source of truth**: in-repo Markdown + JSON pairs under `docs/risk-register/`, `docs/governance-hub/{adoption-roadmap,executive-kpi,rai-register,feature-value-ledger}/`, and `specs/shared/feature-value-ledger.{md,json}` — append-only via git history
- **Read API cache (optional, no net-new account)**: existing Cosmos DB `cosmos-ama-zo6bb5`, database `disaster-hub`, **new container `evidence_pack_artefact_cache`** partitioned by `/artefact_id` for low-latency read fan-out to the executive page; populated synchronously from the in-repo source at publication time. Append-only at the data layer per [Constitution NN-1 carve-out](../../.specify/memory/constitution.md) and the precedent from spec-035
- **Immutable artefact archive**: existing Blob storage account in `rg-ama` (extend; do not create new account); a new container `evidence-pack-archive` with immutability policy retains a per-publish snapshot tagged with `publication_id` and `manual_row_ratio`
- **Audit**: every publish, override, and read of a `manual_row_ratio > 0.5` artefact appends to the existing Cosmos audit-timeline container via the established audit-writer pattern; no PII is persisted (FR-005)
- **Key Vault**: existing `kv-ama-*`; no new secrets required (publication signing reuses the spec-035 PDF-signing key only if FR-029 export needs cryptographic provenance — see ADR-037-04)

**Testing**:

- API contract tests under `apps/api/tests/contract/spec_037/` validating each new `/api/governance/evidence-pack/*` route against the OpenAPI snippet in `contracts/openapi.evidence-pack.yaml`
- Schema tests under `tests/contract/spec_037/test_schemas.py` validating each artefact JSON sidecar against `packages/schemas/spec_037/*.schema.json`
- Publication-gate tests under `tests/contract/spec_037/test_publication_gate.py` asserting (a) `manual_row_ratio` recomputation is correct, (b) `> 0.5` without `auditor_signoff` fails, (c) `> 0.5` with complete `auditor_signoff` passes, (d) link-checker rejects broken back-citations (FR-008/FR-009)
- Web unit tests (Vitest) for the executive page rendering of the manual-row ratio strip and stale-telemetry banner (FR-021, FR-023)
- Playwright smoke at `tests/e2e/web-coverage/governance-executive.spec.ts` — read-only, axe-core, keyboard-only path, ARIA live-region announcement of `manual_row_ratio` updates (NN-3, FR-021)
- BDD traceability: each FR-001..FR-038 + SC-001..SC-011 maps to at least one test id in `tests/contract/spec_037/_traceability.csv`

**Target Platform**:

- Production: existing Container App `ca-api-ama` (FastAPI) and App Service `app-ama-zo6bb5` (Next.js) in `rg-ama`, AU East, AVM-deployed via [`infra/main.bicep`](../../infra/main.bicep)
- CI: GitHub Actions on `ubuntu-latest`; new job `evidence-pack-publication-gate` extends [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) with pnpm + uv + the schema/link/cap/sign-off checks
- Browser: evergreen Chromium / Firefox / Safari 16.4+; same support matrix as spec-035

**Project Type**: Multi-runtime web platform (Next.js dashboard + FastAPI coordination API + in-repo Markdown/JSON evidence artefacts). pnpm + uv monorepo with apps under [`apps/`](../../apps/), shared packages under [`packages/`](../../packages/).

**Performance Goals**:

- Executive KPI page p95 first-meaningful-content ≤ 1.5 s on the existing App Service plan (no new chart libraries means budget is comfortably met from existing baselines)
- `evidence_pack.publication.duration_seconds` median ≤ 60 s, p95 ≤ 180 s, alert if p95 > 300 s
- Publication-gate CI job wall-clock ≤ 3 minutes on `ubuntu-latest` (schema + link + cap + sign-off checks)
- Read-API p95 ≤ 200 ms per artefact retrieval (Cosmos cache; cold-source fallback ≤ 1.5 s)

**Constraints**:

- AU-region data residency for all regulated platform data ([Constitution NN-1](../../.specify/memory/constitution.md)); no Foundry carve-out is invoked by this spec — the Foundry RAG client appears only as an RAI-Register row, not as a runtime dependency
- Append-only audit ([Constitution NN-2](../../.specify/memory/constitution.md), [FR-005](./spec.md#functional-requirements)) — published rows are immutable; corrections via dated revision rows
- WCAG 2.2 AA on the executive page ([Constitution NN-3](../../.specify/memory/constitution.md), [FR-021](./spec.md#functional-requirements))
- Multilingual baseline inherits from spec-035; this spec adds no new language assets
- Graceful degradation ([Constitution NN-5](../../.specify/memory/constitution.md), [FR-023](./spec.md#functional-requirements)) — page renders "stale as of <timestamp>" when upstream telemetry is unavailable
- TDD ([QG-1](../../.specify/memory/constitution.md)) — every FR-001..FR-038 lands behind a failing test first
- AVM-first IaC — no hand-rolled `Microsoft.*` resources; the Cosmos container + Blob container are configured via the existing AVM-composed Bicep modules in [`infra/`](../../infra/), respecting [`bicep-policy-compliance.instructions.md`](../../.github/instructions/bicep-policy-compliance.instructions.md) and [`bicep-code-best-practices.instructions.md`](../../.github/instructions/bicep-code-best-practices.instructions.md)
- **No net-new Azure resources** — Container App, App Service, Cosmos account, Blob account, App Insights, Key Vault are all reused; the only infra delta is two child resources (one Cosmos container, one Blob container) and two App Insights custom metrics

**Scale/Scope**:

- 5 artefacts × 1 schema + 1 OpenAPI snippet + 1 publication-gate metadata schema = 6 schema files
- ~36 spec rows in the Feature-Value Ledger (specs 001–036)
- ~11 ADR rows in the Tradeoff Log (current count under [`docs/aidr/decisions/`](../../docs/aidr/decisions/))
- ~9 AI-component rows × 4 frameworks × 8 principles = 288 RAI cells minimum
- 6 risk categories × ≥1 row + extension of `RISK-AOAI-001` = ≥7 risk rows at v1; expected 20–30 at first publish
- 1 new web route, 4 new read-only API endpoints, 1 new CI job, 0 new Azure resources

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution clause | Status | Justification |
|---|---|---|
| **I. Primacy of Life** | ✅ PASS | Read-only evidence pack; introduces no agent decisioning. The Adoption-Roadmap rollback criteria explicitly preserve life-safety defaults (FR-017). |
| **II. National EM Principles + AIIMS** | ✅ PASS | Adoption Roadmap is sequenced by AIIMS-aligned cohorts; RAI Register treats AIIMS-mapped sub-agents as in-scope components (FR-024). |
| **III. Multi-Hazard, Multi-Agency** | ✅ PASS | Roadmap covers all 8 jurisdictions + Commonwealth; KPI surface is hazard-agnostic. |
| **IV. Transparency & Auditability** | ✅ PASS — STRENGTHENED | Every artefact carries provenance + back-citations; every publish appends to the Cosmos audit-timeline; manual rows are explicitly tagged. |
| **V. Warning & Public Information** | N/A | No public-facing warning content is generated by this spec. |
| **VI. Evacuation Framework** | N/A | No evacuation-decisioning surface. |
| **VII. Recovery Support** | N/A | Recovery KPIs are referenced from existing spec-021 / spec-030 sources, not redefined. |
| **VIII. Cloud Platform** | ✅ PASS | All-Azure, AVM-first, Bicep-extended (no hand-rolled `Microsoft.*`), CI/CD via GitHub Actions, no net-new services. |
| **NN-1 Human-in-the-loop** | ✅ PASS | Manual-stub override (FR-038) requires named-auditor sign-off; publication gate enforces it in CI. |
| **NN-1 Data sovereignty (AU)** | ✅ PASS | All persistence is AU-East (Cosmos `cosmos-ama-zo6bb5`, Blob in `rg-ama`, App Insights AU). No Foundry carve-out invoked. |
| **NN-2 Privacy by design** | ✅ PASS | No PII in artefact rows; back-citations are spec/ADR/role-name only; audit log carries no PII (FR-005). |
| **NN-3 Interoperability (WCAG 2.2 AA)** | ✅ PASS | axe-core in CI; ARIA live-region for the manual-row ratio; keyboard-only path; 400% zoom & high-contrast smoke tests. |
| **NN-4 Multilingual baseline** | ✅ PASS — INHERITED | The executive page inherits the spec-035 i18n shell without adding new language assets. |
| **NN-5 Graceful degradation** | ✅ PASS | Page renders "stale as of <timestamp>" on telemetry outage (FR-023); read-API fall-back order is Cosmos cache → in-repo source. |
| **QG-1 TDD** | ✅ PASS | Every FR/SC mapped to a failing test in `tests/contract/spec_037/_traceability.csv` before implementation. |
| **QG-2 IaC What-If review** | ✅ PASS | The two child-resource additions go through the existing `infra/main.bicep` what-if pipeline. |
| **QG-3 Lessons management** | ✅ PASS | The Feature-Value Ledger + Tradeoff Log institutionalise lessons capture across specs 001–036. |
| **`028-capstone-alignment` FR-020 self-flag** | ✅ PASS | Spec self-flags as "non-capstone-critical-path / delivery-hygiene" (FR-007); plan reaffirms and adds `specs/shared/capstone-metric-trace.md` row. |
| **`governance-discovery.instructions.md`** | ✅ PASS | Any governance-constraint additions (e.g., the publication gate as a constraint) are produced under that instruction; see [research.md](./research.md) RES-04. |
| **AVM-first / Bicep policy** | ✅ PASS | Bicep changes (one Cosmos child container + one Blob child container) reuse AVM modules; PSRule run via existing `ps-rule.yaml`. |

**Gate result**: PASS for Phase 0. Re-check after Phase 1: PASS (no design choice introduces new violations; see § Re-evaluation below).

## Project Structure

### Documentation (this feature)

```text
specs/037-capstone-evidence-pack/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — 5 research notes
├── data-model.md        # Phase 1 — entity model for the 5 artefacts + publication-gate
├── quickstart.md        # Phase 1 — operator walk-through
├── contracts/
│   ├── openapi.evidence-pack.yaml             # Read-only API surface
│   ├── risk-register.schema.json              # Artefact 1
│   ├── adoption-roadmap.schema.json           # Artefact 2
│   ├── executive-kpi-surface.schema.json      # Artefact 3
│   ├── responsible-ai-register.schema.json    # Artefact 4
│   ├── feature-value-ledger.schema.json       # Artefact 5
│   └── publication-gate-metadata.schema.json  # Cross-cutting publication metadata
└── tasks.md             # (Phase 2 output — created by /speckit.tasks)
```

### Source Code (repository root)

```text
apps/
├── api/
│   ├── app/
│   │   ├── api/routes/governance/             # NEW directory
│   │   │   └── evidence_pack.py               # NEW — 4 read-only endpoints
│   │   ├── services/governance/               # NEW — publication + cap-check service
│   │   │   ├── evidence_pack_publisher.py
│   │   │   └── manual_row_ratio.py
│   │   └── services/simulation/audit_writer.py  # REUSED
│   └── tests/contract/spec_037/               # NEW
│       ├── test_evidence_pack_routes.py
│       ├── test_publication_gate.py
│       └── _traceability.csv
└── web/
    └── src/app/governance/
        ├── dashboard/                         # REUSED (spec-035)
        └── executive/                         # NEW
            ├── page.tsx                       # Server Component, composes existing shell
            ├── _components/
            │   ├── ManualRowRatioStrip.tsx    # Live-region accessible
            │   └── KpiLadder.tsx              # Reuses PersonaWorkspace primitives
            └── __tests__/                     # Vitest

packages/
├── domain/src/domain/models/                  # NEW Pydantic v2 models (extend, do not refactor)
│   ├── evidence_pack_artefact.py
│   ├── risk_row.py
│   ├── adoption_wave.py
│   ├── kpi_row.py
│   ├── rai_row.py
│   ├── feature_value_row.py
│   ├── tradeoff_row.py
│   └── publication_gate_metadata.py
└── schemas/spec_037/                          # NEW — JSON Schema draft 2020-12 (mirrors)

docs/
├── risk-register/
│   ├── index.md                               # NEW — roll-up sorted by residual score
│   ├── schema.json                            # symlink/copy of contracts/risk-register.schema.json
│   ├── RISK-AOAI-001.md                       # PRESERVED — must remain valid under new schema
│   └── RISK-*.md                              # NEW — ≥1 per category × 6 categories
├── governance-hub/
│   ├── index.md                               # EXTENDED — link to 5 artefacts
│   ├── adoption-roadmap/
│   │   ├── roadmap.md                         # NEW
│   │   └── roadmap.json                       # NEW
│   ├── executive-kpi/
│   │   ├── surface.md                         # NEW
│   │   └── surface.json                       # NEW
│   ├── rai-register/
│   │   ├── responsible-ai-register.md         # NEW
│   │   └── responsible-ai-register.json       # NEW
│   └── feature-value-ledger/
│       └── tradeoff-log.md                    # NEW (paired ADR log)
├── governance-dashboard.md                    # EXTENDED — deprecation banner
├── governance-hub/observability/{slo,metrics-catalogue}.md  # EXTENDED — deprecation banners
└── aidr/decisions/
    └── adr-037-*.md                           # NEW — 4 ADRs (see § Decisions)

specs/shared/
├── capstone-metric-trace.md                   # EXTENDED — adds spec-037 self-flag row
├── feature-value-ledger.md                    # NEW
└── feature-value-ledger.json                  # NEW

infra/
└── main.bicep                                 # EXTENDED — 2 child resources, 0 new top-level resources

.github/
├── workflows/ci.yml                           # EXTENDED — new job `evidence-pack-publication-gate`
└── instructions/                              # PRESERVED — honoured, not modified

tests/
├── contract/spec_037/                         # NEW
│   ├── test_schemas.py
│   └── test_publication_gate.py
└── e2e/web-coverage/
    └── governance-executive.spec.ts           # NEW Playwright smoke
```

**Structure Decision**: Multi-runtime web-platform layout consistent with spec-035 and spec-036. The five artefacts live as Markdown + JSON pairs in-repo (single source of truth, append-only via git history); the FastAPI surface and Next.js page are thin read-only veneers that compose existing primitives. The `packages/schemas/spec_037/` directory mirrors the established `spec_035/` and `spec_036/` layouts so contract-tests and Pydantic codegen pick up new schemas with no tooling changes.

## Phase 0 — Research output

Five research notes are produced in [`research.md`](./research.md), one per non-trivial decision:

- **RES-01** Schema strategy — JSON Schema draft 2020-12 + Pydantic v2; extend the `signal-envelope.schema.*` governance pattern (Data Engineer persona).
- **RES-02** Governance-Hub IA — flat-per-artefact directory layout vs. nested; chosen flat-per-artefact under `docs/governance-hub/<artefact>/{name}.{md,json}` with a single index extension (UX Designer + Compliance Auditor personas).
- **RES-03** Web-shell composition — Server Component page that composes `PersonaWorkspace` + audit-row primitives; **no new chart libraries** (UX Designer + Software Developer personas; honours spec-035 Q1 + Clarification 3).
- **RES-04** CI gate strategy — extend `.github/workflows/ci.yml` with a single matrix-free job that runs (1) schema-validation, (2) link-check, (3) `manual_row_ratio` recomputation + cap, (4) `auditor_signoff` completeness; failures block PR merge (Infrastructure/DevOps + QA personas; honours `governance-discovery.instructions.md`).
- **RES-05** `manual_row_ratio` measurement strategy — server-side recomputation at publish time from the JSON sidecar (not client-trusted); ratio surfaced both in artefact metadata and as the App Insights custom metric `evidence_pack.manual_row_ratio` (SRE + Compliance Auditor personas).

All `NEEDS CLARIFICATION` markers from the spec are resolved (Clarifications Q1–Q4); **no open clarifications remain**.

## Phase 1 — Design & Contracts

Phase 1 produces:

- [`data-model.md`](./data-model.md) — entity model for the seven row-types (`RiskRow`, `AdoptionWave`, `KpiRow`, `RaiRow`, `FeatureValueRow`, `TradeoffRow`, `PublicationGateMetadata`) plus the cross-cutting `EvidencePackArtefact` envelope with the `manual_row_count` / `total_row_count` / `manual_row_ratio` / `auditor_signoff` block.
- [`contracts/`](./contracts/) — one OpenAPI snippet (`openapi.evidence-pack.yaml`) for the four read-only routes plus six JSON Schemas (one per artefact + one for the publication-gate metadata).
- [`quickstart.md`](./quickstart.md) — operator walk-through: how to add a new risk row, how to publish an artefact, how to obtain auditor sign-off when `manual_row_ratio > 0.5`, how to verify the page renders against the API.
- Agent context — `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` is run to add Spec-037-specific context (Pydantic v2 evidence-pack models, JSON Schema draft 2020-12, executive page composition, publication-gate semantics) to the GitHub Copilot context file, preserving manual additions between markers.

## Re-evaluation of Constitution Check (post-design)

After Phase 1 design completion, the Constitution Check is re-run:

- No new violations introduced. The two new App Insights custom metrics (`evidence_pack.publication.duration_seconds`, `evidence_pack.manual_row_ratio`) emit through the existing OpenTelemetry sink in AU East and contain no PII (NN-1, NN-2 preserved).
- The Cosmos `evidence_pack_artefact_cache` container and Blob `evidence-pack-archive` container are AU-East child resources of accounts already in `rg-ama`; AVM modules cover both (NN-1 + Cloud Platform Principle VIII preserved).
- Append-only semantics are enforced at three layers — git history (in-repo source), Cosmos audit-timeline (publish events), Blob immutability policy (per-publish snapshot) — strengthening Principle IV without violating any other clause.
- No new top-level Azure resources; no AVM-bypass; no hand-rolled `Microsoft.*` types.

**Post-design gate result**: PASS.

## Complexity Tracking

> Filled only where Constitution Check could plausibly be challenged.

| Apparent complexity | Why retained | Simpler alternative rejected because |
|---|---|---|
| New Cosmos container `evidence_pack_artefact_cache` | Read-API p95 ≤ 200 ms target; in-repo cold-read from a Container App revision is consistently 800–1 200 ms | "Read directly from git" rejected: violates p95 budget and couples the Container App to git checkout state |
| New Blob container `evidence-pack-archive` (immutability policy) | Constitution Principle IV (auditability) + FR-005 require immutable per-publish snapshots auditors can independently verify; git history alone is mutable by force-push and rebase | "Git history only" rejected: a force-push could rewrite history; immutability policy on Blob is a tamper-evident second copy |
| Two new App Insights custom metrics | SRE persona requirement: publication-gate failure rate + manual_row_ratio per artefact must be alertable; no existing metric carries this signal | "Reuse existing metrics" rejected: would require parsing free-text log lines, fragile and slow |

No constitution-clause violations are claimed; the table above documents intentional design choices that avoid the trap of "everything must be in-repo" while preserving tamper-evidence and SLO-bearing observability.

## Plan Decisions and ADR Roadmap

The following plan-level decisions are recorded in this plan and promoted to ADRs under [`docs/aidr/decisions/`](../../docs/aidr/decisions/):

| ID | Decision | Rationale | ADR |
|---|---|---|---|
| **PD-037-01** | Markdown + JSON sidecar pair per artefact, JSON Schema draft 2020-12, validated in CI | Text-first matches the "evidence in git" principle; JSON sidecar enables the executive page + automated checks | `adr-037-01-text-first-evidence-pack.md` |
| **PD-037-02** | Reuse existing governance shell; new route `apps/web/src/app/governance/executive/`; **no new chart libraries** | Honours spec-035 Q1 + this spec's Clarification 3; preserves SC-009 ("zero net-new dashboards") | `adr-037-02-executive-shell-reuse.md` |
| **PD-037-03** | Per-artefact `manual_row_ratio ≤ 0.5` cap; override via named-auditor sign-off recorded in metadata; enforced in CI | Honours this spec's Clarification 4 (FR-038) and the `Validated`/`Deferred`/`Unresolved` precedent in `specs/shared/capstone-metric-trace.md` | `adr-037-03-manual-evidence-cap.md` |
| **PD-037-04** | Append-only at three layers: git history + Cosmos audit-timeline + Blob immutability policy snapshot | Single layer (git) is force-push-mutable; three layers give tamper-evident provenance auditors can verify independently | `adr-037-04-three-layer-append-only.md` |
| **PD-037-05** | RAI scope includes `036-sim-agent-extend` as a full production AI component (no reduction for simulation watermark) | Honours this spec's Clarification 2 + `036-sim-agent-extend` FR-066 (production-grade idempotency on `/inject-telemetry`) | Recorded in `responsible-ai-register.md` rationale block; no separate ADR needed |
| **PD-037-06** | Zero net-new top-level Azure resources; only two child resources (1 Cosmos container + 1 Blob container) and 2 App Insights custom metrics | Honours `028-capstone-alignment` FR-020 "non-capstone-critical-path / delivery-hygiene" budget discipline; SC-009 enforced | Recorded in `infra/main.bicep` what-if review notes |

ADR drafts are produced as part of Phase 2 (`/speckit.tasks`); this plan locks the decision text above.

## Validation against spec FRs and SCs

The plan covers every FR and SC in the spec:

| Coverage | Plan element |
|---|---|
| FR-001..FR-009 (cross-cutting) | Project Structure + research RES-01/RES-04 + ADR PD-037-01/PD-037-04 |
| FR-010..FR-014 (Risk Register) | `docs/risk-register/` layout; `risk-register.schema.json`; `RISK-AOAI-001.md` preserved |
| FR-015..FR-018 (Adoption Roadmap) | `docs/governance-hub/adoption-roadmap/`; `adoption-roadmap.schema.json` |
| FR-019..FR-023 (Executive KPI Surface) | `docs/governance-hub/executive-kpi/` + `apps/web/src/app/governance/executive/` + `executive-kpi-surface.schema.json` + ADR PD-037-02 |
| FR-024..FR-029 (RAI Register) | `docs/governance-hub/rai-register/` + `responsible-ai-register.schema.json` + PD-037-05 |
| FR-030..FR-034 (Feature-Value Ledger + Tradeoff Log) | `specs/shared/feature-value-ledger.{md,json}` + `docs/governance-hub/feature-value-ledger/tradeoff-log.md` |
| FR-035..FR-038 (Governance lifecycle) | RES-04 + RES-05 + ADR PD-037-03 + CI job `evidence-pack-publication-gate` |
| SC-001..SC-011 | Test traceability in `apps/api/tests/contract/spec_037/_traceability.csv` and `tests/contract/spec_037/_traceability.csv` |

**Unresolved gaps**: none identified. All four spec clarifications are folded into the plan; all FRs and SCs map to a planned artefact, schema, route, page primitive, or CI check.

---

*Plan generated by `/speckit.plan` on 2026-05-11. Phase 2 (`tasks.md`) is **not** produced by this command — run `/speckit.tasks` next.*

## Re-evaluation — post-Polish (T069)

**Result**: PASS — post-polish.

- Constitution invariant: git diff --quiet HEAD~9 -- .specify/memory/constitution.md returns 0 (constitution is byte-identical to its pre-spec-037 state — no edits).
- Net-new top-level Azure resources: 0 (PD-037-06 + SC-009 honoured). Bicep delta is exactly 1 Cosmos child container (vidence_pack_artefact_cache), 1 Blob child container (vidence-pack-archive with immutability policy), and 2 App Insights custom metrics emitted via the existing OpenTelemetry pipeline.
- All Phase 0..8 constitution-clause checks remain at PASS (no design choice introduced new violations).
- `infra/main.bicep` what-if note (PD-037-06): `2 child resources, 0 top-level resources, 2 custom metrics`. Live `az deployment sub what-if` runs in Step 9 (`azd up` redeploy) per orchestrator authorisation.


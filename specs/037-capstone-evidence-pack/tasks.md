---
description: "Dependency-ordered tasks for spec-037 Capstone Evidence Pack"
---

# Tasks: Capstone Evidence Pack — Residual Rubric Gap Closure

**Branch**: `037-capstone-evidence-pack` · **Feature dir**: `specs/037-capstone-evidence-pack/`
**Inputs**: [spec.md](./spec.md) (38 FRs, 11 SCs), [plan.md](./plan.md) (PD-037-01..06), [data-model.md](./data-model.md), [contracts/](./contracts/) (1 OpenAPI + 6 JSON Schemas), [research.md](./research.md) (RES-01..05), [quickstart.md](./quickstart.md), [checklists/capstone-evidence-pack.checklist.md](./checklists/capstone-evidence-pack.checklist.md) (84 verification items).

**TDD discipline**: Every code task is preceded by a contract or unit test that fails until the code lands ([Constitution QG-1](../../.specify/memory/constitution.md)).

**Capstone-criticality**: Self-flagged "non-capstone-critical-path / delivery-hygiene" per `028-capstone-alignment` FR-020.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[Story]**: maps to spec.md user stories — `[US1]` Risk, `[US2]` Adoption, `[US3]` KPI, `[US4]` RAI, `[US5]` Feature-Value Ledger
- **Acceptance**: each task carries an observable test/file outcome
- **Citations**: each task carries an FR-### / SC-### / PD-037-## / RES-## / CHK### / authority reference

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch hygiene, dependency wiring, schema-file mirroring. No tests, no implementation yet.

- [X] T001 Create directory scaffolding under `packages/schemas/spec_037/`, `packages/domain/src/domain/models/evidence_pack/`, `apps/api/app/api/routes/governance/`, `apps/api/app/services/governance/`, `tests/contract/spec_037/`, `tests/integration/spec_037/`, `tests/unit/spec_037/`, `apps/web/src/app/governance/executive/_components/`, `apps/web/src/lib/governance/evidence-pack/`, `apps/web/tests/e2e/spec-037/`, `scripts/evidence_pack_gate/` (FR-001, PD-037-01, RES-01, CHK001).
  - **Acceptance**: `Get-ChildItem -Recurse` shows all 10 directories present with `.gitkeep` placeholders.
- [X] T002 [P] Add Python deps `jsonschema>=4.21`, `pyyaml` to root `pyproject.toml` and pin via `uv lock` (RES-01, FR-009).
  - **Acceptance**: `uv lock --check` succeeds; `uv.lock` diff shows the two new top-level deps.
- [X] T003 [P] Add web deps `@axe-core/playwright`, `@axe-core/react` (dev) to `apps/web/package.json` and refresh `pnpm-lock.yaml` (NN-3, FR-021, RES-03).
  - **Acceptance**: `pnpm install --frozen-lockfile` succeeds; lockfile diff shows the two new dev deps.
- [X] T004 [P] Copy the 6 canonical JSON Schemas from `specs/037-capstone-evidence-pack/contracts/*.schema.json` into `packages/schemas/spec_037/` preserving filenames; add `packages/schemas/spec_037/README.md` documenting the canonical→runtime mirror policy (RES-01, PD-037-01, FR-009).
  - **Acceptance**: `Compare-Object` returns no differences between the canonical and runtime copies; README explicitly names the canonical path.
- [X] T005 [P] Create empty traceability stubs `apps/api/tests/contract/spec_037/_traceability.csv` and `tests/contract/spec_037/_traceability.csv` with header row `fr_or_sc_id,test_id,test_path,status` (QG-1, all FR-001..FR-038, SC-001..SC-011).
  - **Acceptance**: Both files exist with the header; CI is configured to lint these files in T059.
- [X] T006 [US-NA] Self-flag spec-037 in `specs/shared/capstone-metric-trace.md` as `non-capstone-critical-path / delivery-hygiene` per `028-capstone-alignment` FR-020 (FR-007, SC-010, CHK002).
  - **Acceptance**: A new row for spec-037 exists with the exact tag string and a back-citation to `028-capstone-alignment` FR-020.
- [X] T007 Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` to add spec-037 markers (Pydantic v2 evidence-pack models, JSON Schema draft 2020-12, executive-page composition, publication-gate semantics) to `.github/copilot-instructions.md` between the managed markers (PD-037-01..06, plan.md § Phase 1).
  - **Acceptance**: The Copilot context file's auto-managed block contains `spec-037` once; manual sections outside markers are unchanged.

**Checkpoint**: Setup ready — all schema files mirrored, deps wired, capstone-trace self-flagged.

---

## Phase 2: Tests First (failing) ⚠️ TDD GATE

**Purpose**: Author the failing contract / unit / accessibility tests for every endpoint, schema, and front-end component before any implementation lands. **No code from Phase 3+ may begin until this phase is complete and the suite is red.**

### Schema contract tests (one per JSON Schema — all parallelisable)

- [X] T008 [P] Schema contract test `tests/contract/spec_037/test_risk_register_schema.py` validating `risk-register.schema.json` against (a) a minimal valid example covering all 6 categories, (b) a missing-required-field invalid example (FR-009, FR-010, FR-011, CHK010).
  - **Acceptance**: Test file exists; `pytest tests/contract/spec_037/test_risk_register_schema.py` fails with `ModuleNotFoundError` or fixture-missing (target schema not yet wired).
- [X] T009 [P] Schema contract test `tests/contract/spec_037/test_adoption_roadmap_schema.py` for `adoption-roadmap.schema.json` (valid + invalid examples covering 8 jurisdictions + Commonwealth, readiness gates, rollback) (FR-009, FR-015, FR-016, FR-017, FR-018, CHK020).
  - **Acceptance**: Test file exists and currently fails.
- [X] T010 [P] Schema contract test `tests/contract/spec_037/test_executive_kpi_surface_schema.py` for `executive-kpi-surface.schema.json` (≥1 leading + ≥1 lagging KPI per capstone criterion) (FR-009, FR-019, FR-020, FR-021, CHK030).
  - **Acceptance**: Test file exists and currently fails.
- [X] T011 [P] Schema contract test `tests/contract/spec_037/test_responsible_ai_register_schema.py` for `responsible-ai-register.schema.json` (4 frameworks × 8 principles, no blanks) (FR-009, FR-024, FR-025, FR-026, FR-027, CHK040).
  - **Acceptance**: Test file exists and currently fails.
- [X] T012 [P] Schema contract test `tests/contract/spec_037/test_feature_value_ledger_schema.py` for `feature-value-ledger.schema.json` (one row per spec 001–036, ADR rows, follow-ups for non-zero gap) (FR-009, FR-030, FR-031, FR-032, FR-033, CHK050).
  - **Acceptance**: Test file exists and currently fails.
- [X] T013 [P] Schema contract test `tests/contract/spec_037/test_publication_gate_metadata_schema.py` for `publication-gate-metadata.schema.json` (manual_row_ratio range, auditor_signoff completeness) (FR-009, FR-037, FR-038, SC-011, CHK060).
  - **Acceptance**: Test file exists and currently fails.

### OpenAPI contract tests (one per route — all parallelisable)

- [X] T014 [P] Contract test `apps/api/tests/contract/spec_037/test_route_list_artefacts.py` for `GET /api/governance/evidence-pack/artefacts` per `contracts/openapi.evidence-pack.yaml:21` (FR-001, FR-021, CHK070).
  - **Acceptance**: Test imports the (yet-to-be-written) router and asserts 200 with 5 artefact summaries; currently fails on import.
- [X] T015 [P] Contract test `apps/api/tests/contract/spec_037/test_route_get_artefact.py` for `GET /api/governance/evidence-pack/artefacts/{artefact_id}` per `contracts/openapi.evidence-pack.yaml:37` (FR-021, FR-029, CHK071).
  - **Acceptance**: Test exists and currently fails.
- [X] T016 [P] Contract test `apps/api/tests/contract/spec_037/test_route_get_publication.py` for `GET /api/governance/evidence-pack/artefacts/{artefact_id}/publications/{publication_id}` (immutable snapshot read) (FR-005, FR-038, PD-037-04, CHK072).
  - **Acceptance**: Test exists and currently fails.
- [X] T017 [P] Contract test `apps/api/tests/contract/spec_037/test_route_health.py` for `GET /api/governance/evidence-pack/health` (FR-023 graceful-degradation status, CHK073).
  - **Acceptance**: Test exists and currently fails.

### Publication-gate tests (covers RES-04 + FR-038)

- [X] T018 [P] Test `tests/contract/spec_037/test_publication_gate_ratio_recompute.py` — given a fixture sidecar with N manual rows out of M total, the gate's recomputed `manual_row_ratio` MUST equal the metadata-declared value (FR-037, RES-05, CHK061).
  - **Acceptance**: Test exists and currently fails.
- [X] T019 [P] Test `tests/contract/spec_037/test_publication_gate_cap_no_signoff.py` — `manual_row_ratio > 0.5` AND missing/incomplete `auditor_signoff` MUST fail the gate with non-zero exit (FR-038, SC-011, CHK062).
  - **Acceptance**: Test exists and currently fails.
- [X] T020 [P] Test `tests/contract/spec_037/test_publication_gate_cap_with_signoff.py` — `manual_row_ratio > 0.5` AND complete `{name, role, signoff_date_utc, basis}` block MUST pass the gate (FR-038, SC-011, CHK063).
  - **Acceptance**: Test exists and currently fails.
- [X] T021 [P] Test `tests/contract/spec_037/test_publication_gate_link_check.py` — broken back-citations in any artefact `*.md` MUST fail the gate (FR-008, SC-002, CHK064).
  - **Acceptance**: Test exists and currently fails.

### Front-end unit + accessibility scaffolding

- [X] T022 [P] Vitest unit test `apps/web/src/app/governance/executive/_components/__tests__/ManualRowRatioStrip.test.tsx` — renders 5 ratios, ARIA live-region `aria-live="polite"`, accessible name announces ratio updates (FR-021, FR-037, NN-3, CHK080).
  - **Acceptance**: Test exists and currently fails.
- [X] T023 [P] Vitest unit test `apps/web/src/app/governance/executive/_components/__tests__/KpiLadder.test.tsx` — composes `PersonaWorkspace` primitives, no chart-library imports (RES-03, SC-009, CHK081).
  - **Acceptance**: Test exists and currently fails.
- [X] T024 [P] Vitest unit test `apps/web/src/app/governance/executive/_components/__tests__/StaleTelemetryBanner.test.tsx` — renders "stale as of <ts>" when upstream telemetry is unavailable (FR-023, NN-5, CHK082).
  - **Acceptance**: Test exists and currently fails.
- [X] T025 [P] axe-core scaffolding `apps/web/tests/e2e/spec-037/axe.setup.ts` exporting a reusable `injectAndCheck()` helper for Playwright (NN-3, FR-021, CHK083).
  - **Acceptance**: Helper file exists; imported in T058 to gate the e2e suite.

**Checkpoint**: TDD gate red — `pytest tests/contract/spec_037/`, `pytest apps/api/tests/contract/spec_037/`, and `pnpm --filter web vitest run` all fail. Phase 3 may begin only after this is verified.

---

## Phase 3: Backend Implementation

**Purpose**: Land the Pydantic models, services, FastAPI routes, audit-writer integration, and infrastructure child-resources that make Phase 2 green. **Depends on T008–T021 being authored and red.**

### Pydantic v2 models (parallelisable — distinct files)

- [X] T026 [P] [US1] Implement `packages/domain/src/domain/models/evidence_pack/risk_row.py` matching `risk-register.schema.json` (FR-010, FR-011, FR-012, FR-014, depends on T004, T008).
  - **Acceptance**: T008 turns green; `python -c "from domain.models.evidence_pack.risk_row import RiskRow"` succeeds.
- [X] T027 [P] [US2] Implement `packages/domain/src/domain/models/evidence_pack/adoption_wave.py` (FR-015, FR-016, FR-017, FR-018, depends on T009).
  - **Acceptance**: T009 turns green.
- [X] T028 [P] [US3] Implement `packages/domain/src/domain/models/evidence_pack/kpi_row.py` (FR-019, FR-020, depends on T010).
  - **Acceptance**: T010 turns green.
- [X] T029 [P] [US4] Implement `packages/domain/src/domain/models/evidence_pack/rai_row.py` covering 4 frameworks × 8 principles enum + `not_applicable + justification` discriminated union (FR-024, FR-025, FR-026, FR-027, PD-037-05, depends on T011).
  - **Acceptance**: T011 turns green.
- [X] T030 [P] [US5] Implement `packages/domain/src/domain/models/evidence_pack/feature_value_row.py` AND `tradeoff_row.py` (FR-030, FR-031, FR-032, FR-033, FR-034, depends on T012).
  - **Acceptance**: T012 turns green.
- [X] T031 [P] Implement `packages/domain/src/domain/models/evidence_pack/publication_gate_metadata.py` with `manual_row_count`, `total_row_count`, `manual_row_ratio` (computed validator), `auditor_signoff` (optional sub-model with required `{name, role, signoff_date_utc, basis}`) (FR-037, FR-038, RES-05, depends on T013).
  - **Acceptance**: T013 turns green.
- [X] T032 Implement `packages/domain/src/domain/models/evidence_pack/evidence_pack_artefact.py` envelope referencing all six row types and the publication-gate metadata (FR-001, FR-005, depends on T026–T031).
  - **Acceptance**: `mypy packages/domain` clean; envelope imports all six rows.

### Services

- [X] T033 Implement `apps/api/app/services/governance/manual_row_ratio.py` — server-side recomputation walking `rows[]` and counting `provenance.tag == "manual"`, emitting App Insights metric `evidence_pack.manual_row_ratio` (RES-05, FR-037, depends on T018, T031).
  - **Acceptance**: T018 turns green; `evidence_pack.manual_row_ratio` is registered as an OpenTelemetry counter.
- [X] T034 Implement `apps/api/app/services/governance/evidence_pack_writer.py` — publication pipeline: load JSON sidecar → validate against schema → recompute ratio → write to Cosmos cache → snapshot to Blob immutability container → append audit-timeline row (FR-005, FR-035, PD-037-04, depends on T032, T033, T037, T038).
  - **Acceptance**: Integration test in T036 can publish an artefact end-to-end; emits `evidence_pack.publication.duration_seconds`.
- [X] T035 Wire append-only audit emissions through the existing `apps/api/app/services/simulation/audit_writer.py` for every publish, every override, and every read of a `manual_row_ratio > 0.5` artefact (FR-005, NN-2, PD-037-04, depends on T034).
  - **Acceptance**: Cosmos audit-timeline shows at least 3 distinct event-type rows after a single publish + override + read sequence; no PII in payload (verified by regex test).

### FastAPI routes

- [X] T036 Implement `apps/api/app/api/routes/governance/evidence_pack.py` exposing the four read-only endpoints from `contracts/openapi.evidence-pack.yaml` and registering the router under the existing JWT/AppRole middleware (FR-001, FR-021, FR-029, depends on T034, T014, T015, T016, T017).
  - **Acceptance**: T014–T017 all turn green; `pytest apps/api/tests/contract/spec_037/` is green.

### Infrastructure child-resources (AVM-first, no top-level resources)

- [X] T037 Extend `infra/main.bicep` (and the AVM-composed Cosmos module) to add child container `evidence_pack_artefact_cache` partitioned by `/artefact_id` on existing `cosmos-ama-zo6bb5/disaster-hub` (PD-037-06, plan.md § Storage, AVM-first instruction).
  - **Acceptance**: `az deployment sub what-if` shows exactly 1 child resource added, 0 top-level resources; `ps-rule run -f infra/` passes.
- [X] T038 Extend `infra/main.bicep` (AVM Blob module) to add child container `evidence-pack-archive` with immutability policy on the existing storage account in `rg-ama` (FR-005, PD-037-04, PD-037-06, depends on T037 in same Bicep file).
  - **Acceptance**: `what-if` shows exactly 1 child resource added; immutability policy is `time-based` with retention ≥ rubric-required minimum; `ps-rule` passes.

**Checkpoint**: All Phase 2 contract tests green; FastAPI routes serve the four endpoints; Cosmos cache + Blob archive containers exist.

---

## Phase 4: Frontend Implementation

**Purpose**: Land the Next.js 15 read-only Executive KPI page composed from spec-035 primitives. **Depends on T036 and the Phase 2 Vitest tests being red.**

- [X] T039 [P] [US3] Implement `apps/web/src/lib/governance/evidence-pack/client.ts` and `types.ts` — fetch helpers wrapping the four `/api/governance/evidence-pack/*` endpoints with the existing MSAL token interceptor; TypeScript types regenerated from the JSON Schemas in `packages/schemas/spec_037/` (FR-021, RES-03, depends on T036).
  - **Acceptance**: `pnpm --filter web typecheck` clean; types match the schemas (verified by a unit test).
- [X] T040 [US3] Implement `apps/web/src/app/governance/executive/_components/ManualRowRatioStrip.tsx` with `aria-live="polite"` (FR-021, FR-037, NN-3, depends on T022, T039).
  - **Acceptance**: T022 turns green; axe-core finds zero violations on the isolated component.
- [X] T041 [US3] Implement `apps/web/src/app/governance/executive/_components/KpiLadder.tsx` composing `PersonaWorkspace` and audit-row read primitives from spec-035; **no chart-library imports** (FR-021, SC-009, RES-03, depends on T023, T039).
  - **Acceptance**: T023 turns green; `pnpm --filter web grep -r "recharts\|visx\|chart.js"` returns no matches in this directory.
- [X] T042 [US3] Implement `apps/web/src/app/governance/executive/_components/StaleTelemetryBanner.tsx` — renders `"stale as of <ts>"` when health endpoint reports degraded telemetry (FR-023, NN-5, depends on T024, T039).
  - **Acceptance**: T024 turns green.
- [X] T043 [US3] Implement `apps/web/src/app/governance/executive/page.tsx` (Server Component) composing T040 + T041 + T042 plus a server-side fetch of all 5 artefact summaries (FR-021, SC-008, SC-009, RES-03, depends on T040, T041, T042).
  - **Acceptance**: Page renders end-to-end against a stubbed API; Vitest snapshot stable.
- [X] T044 [US3] Add Executive route to the governance navigation in `apps/web/src/app/governance/_components/GovernanceNav.tsx` (or equivalent) so it appears as a sibling of `dashboard/{audit,compliance,readiness,recovery,risk}` (FR-021 Clarification 3, CHK084).
  - **Acceptance**: Navigation snapshot updated; e2e in T058 can navigate to `/governance/executive` from the hub.

**Checkpoint**: `/governance/executive` renders with five artefact KPI cards, ratio strip, and stale-telemetry banner; all Vitest tests green.

---

## Phase 5: CI Publication Gate

**Purpose**: Land the `evidence-pack-publication-gate` CI job that enforces FR-008, FR-009, FR-037, FR-038, SC-002, SC-011.

- [X] T045 Implement `scripts/evidence_pack_gate/__main__.py` (Python module, importable for local dry-run) running the four checks in order: schema-validation → link-check → ratio-recompute+cap → auditor-signoff completeness (RES-04, FR-008, FR-009, FR-038, SC-002, SC-011, depends on T018, T019, T020, T021).
  - **Acceptance**: T018–T021 all turn green; `python -m evidence_pack_gate --dry-run` exits 0 against valid fixtures.
- [X] T046 Add CI job `evidence-pack-publication-gate` to `.github/workflows/ci.yml` running after the existing `quality` job on `ubuntu-latest` with pnpm + uv (RES-04, FR-008, FR-009, depends on T045).
  - **Acceptance**: Workflow YAML lints (`actionlint`); job appears in the PR checks list; required for branch-protection.
- [X] T047 Wire the Markdown link-checker for back-citations across `docs/risk-register/`, `docs/governance-hub/{adoption-roadmap,executive-kpi,rai-register}/`, `specs/shared/feature-value-ledger.md`, `docs/governance-hub/feature-value-ledger/tradeoff-log.md` (FR-008, FR-003, SC-002, depends on T045).
  - **Acceptance**: Broken-link fixture causes the gate to exit non-zero; fix removes the failure.
- [X] T048 Emit App Insights custom metrics `evidence_pack.publication.duration_seconds` and `evidence_pack.publication_gate.failure_rate` from the gate; declare the alert thresholds (p95 > 300 s; failure_rate > 5% / 24h) in `docs/governance-hub/observability/metrics-catalogue.md` (RES-05, plan.md § Performance Goals, CHK065).
  - **Acceptance**: Metrics emitted in CI logs; alert thresholds documented.

**Checkpoint**: Publication gate is required for branch-protection; failures block merge.

---

## Phase 6: Documentation, Governance Hub, and Governance-Discovery Instruction

**Purpose**: Wire the new artefacts into the governance hub, add the discovery-instruction entry, and author the four ADRs.

- [X] T049 Extend `docs/governance-hub/index.md` to link the five artefacts and the executive page (FR-002, RES-02, CHK090).
  - **Acceptance**: Hub index renders five new entries; T047 link-check passes.
- [X] T050 Add an entry for the publication gate to `.github/instructions/governance-discovery.instructions.md` per its "any new governance-constraint MUST be discoverable" contract (FR-006, RES-04, CHK091).
  - **Acceptance**: Instruction file lists the gate by job name and points to `scripts/evidence_pack_gate/`.
- [X] T051 Add deprecation banners to `docs/governance-dashboard.md`, `docs/governance-hub/observability/slo.md`, and section-banner only (executive-roll-up subsection) on `docs/governance-hub/observability/metrics-catalogue.md` pointing to the consolidated Executive KPI Surface (FR-022, CHK092). — Acceptance: `metrics-catalogue.md` retains operational metric-inventory role per analyser I5 / FR-022 amendment; section banner only.
  - **Acceptance**: Each superseded surface carries a banner with a link; T047 link-check confirms.
- [X] T052 [P] Author ADR `docs/aidr/decisions/adr-037-01-text-first-evidence-pack.md` (PD-037-01).
  - **Acceptance**: ADR file exists with Decision/Rationale/Alternatives blocks and is picked up by the Tradeoff Log (T057).
- [X] T053 [P] Author ADR `docs/aidr/decisions/adr-037-02-executive-shell-reuse.md` (PD-037-02, SC-009).
  - **Acceptance**: As above.
- [X] T054 [P] Author ADR `docs/aidr/decisions/adr-037-03-manual-evidence-cap.md` (PD-037-03, FR-038, SC-011).
  - **Acceptance**: As above.
- [X] T055 [P] Author ADR `docs/aidr/decisions/adr-037-04-three-layer-append-only.md` (PD-037-04, FR-005).
  - **Acceptance**: As above.

**Checkpoint**: Hub navigation, governance-discovery, deprecation banners, and four ADRs are in place — artefact authoring can now proceed.

---

## Phase 7: Author the Five Evidence Artefacts (parallelisable)

**Purpose**: Land the actual evidence content. All five tasks below are `[P]` because they touch disjoint files. Each artefact MUST validate against its schema, MUST satisfy `manual_row_ratio ≤ 0.5` (or carry a complete `auditor_signoff` block per FR-038), and MUST link-check clean.

- [X] T056 [P] [US1] Author the Systematic Risk Register: extend `docs/risk-register/RISK-AOAI-001.md` to the new schema (preserving the file path), author `docs/risk-register/RISK-NEW-001.md` … `RISK-NEW-NN.md` covering Platform, AI, Operational, Jurisdictional, Data, and Supply-chain (≥ 1 row per category, expected 20–30 rows total at v1), generate `docs/risk-register/index.md` (sorted by residual score, flags review-overdue rows), and author `docs/risk-register/risk-register.json` per `risk-register.schema.json` (FR-010, FR-011, FR-012, FR-013, FR-014, SC-001, SC-002, depends on T026, T045, T049). — Acceptance: artefact JSON path is `docs/risk-register/risk-register.json` (analyser I4); `index.md` is the FR-013 human-readable rollup.
  - **Acceptance**: Schema-check (T008) green for `index.json`; index.md sorts by residual score; CI gate passes; reviewer can identify top-10 risks in < 5 min (SC-001 manual rehearsal).
- [X] T057 [P] [US2] Author the Adoption Roadmap: `docs/governance-hub/adoption-roadmap/roadmap.md` and `roadmap.json`, with waves covering all 8 Australian jurisdictions + Commonwealth, lead agency per jurisdiction, readiness gates, training/exercise cadence citing specs 007/024/026, change-management bundle, and rollback criteria preserving life-safety defaults (FR-015, FR-016, FR-017, FR-018, SC-003, depends on T027, T045, T049).
  - **Acceptance**: T009 green; CI gate passes; rollback criteria explicitly cite Constitution § Primacy of Life.
- [X] T058 [P] [US3] Author the Executive KPI Surface: `docs/governance-hub/executive-kpi/surface.md` and `surface.json`, mapping each of the five capstone success criteria (`capstone.md:31-36`) to ≥ 1 leading + ≥ 1 lagging KPI with owner, refresh cadence, target, threshold/alert band, source-of-truth link, and the scattered surfaces it consolidates (FR-019, FR-020, FR-021, FR-023, SC-004, SC-008, depends on T028, T045, T049, T051). — Acceptance: file lives at canonical path per `plan.md` Project Structure + RES-02 IA decision (analyser I1); `kpi-surface.*` filename is forbidden.
  - **Acceptance**: T010 green; CI gate passes; executive page (T043) renders the surface end-to-end; SC-008 ≤ 2-min comprehension validated by reviewer.
- [X] T059 [P] [US4] Author the Responsible AI Register: `docs/governance-hub/rai-register/responsible-ai-register.md` and `responsible-ai-register.json`, one row per AI/agentic component (5 sub-agents from specs 008–012, sim-agent-extend from `036-sim-agent-extend` per PD-037-05, LLM-eval framework from spec 030, Foundry RAG client from `036-foundry-rag-grounding`), each row populated across 4 frameworks × 8 principles with explicit `not_applicable + justification` for empty cells; cite spec 030's evaluation outputs (do NOT re-run) (FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, SC-005, depends on T029, T045, T049). — Acceptance: file lives at canonical path per analyser I3; rationale block cites PD-037-05 explicitly (satisfies `plan.md` PD-037-05 — no separate ADR file required).
  - **Acceptance**: T011 green; CI gate passes; 0 blank cells in the register; ≥ 9 component rows × 32 cells = 288 cells populated.
- [X] T060 [P] [US5] Author the Feature-to-Value Ledger + Decision/Tradeoff Log: `specs/shared/feature-value-ledger.md` + `specs/shared/feature-value-ledger.json` (one row per spec 001–036 with capstone-metric mapping, magnitude/direction, residual gap-to-target, follow-ups for non-zero gaps, `delivery-hygiene` tag for non-contributing specs) AND `docs/governance-hub/feature-value-ledger/tradeoff-log.md` (one row per ADR under `docs/aidr/decisions/` including the four new ADRs from T052–T055, plus the synthesised cross-sector tensions per FR-036) (FR-030, FR-031, FR-032, FR-033, FR-034, FR-036, SC-006, depends on T030, T045, T049, T052, T053, T054, T055).
  - **Acceptance**: T012 green; CI gate passes; cross-link to `specs/shared/capstone-metric-trace.md` resolves; every ADR appears in the Tradeoff Log.

**Checkpoint**: All five artefacts published; rubric "Mandatory: risks & tradeoffs" + "Differentiators: adoption roadmap, KPI instrumentation, Responsible AI" move from "partial / scattered" to "covered with single-source evidence" (SC-007).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: e2e + accessibility, traceability, observability wiring, infrastructure invariants, Foundry carve-out reference, and final hub navigation pass.

- [X] T061 [P] Playwright e2e + axe-core suite `apps/web/tests/e2e/spec-037/governance-executive.spec.ts` — read-only smoke, keyboard-only path, ARIA live-region announcement on ratio updates, 400% zoom + high-contrast smoke (NN-3, FR-021, RES-03, depends on T025, T043, T044).
  - **Acceptance**: `pnpm --filter web playwright test spec-037` green; axe finds zero serious/critical violations.
- [X] T062 [P] Populate `tests/contract/spec_037/_traceability.csv` and `apps/api/tests/contract/spec_037/_traceability.csv` — one row per FR-001..FR-038 and SC-001..SC-011 mapped to ≥ 1 test_id; CI fails if any FR/SC has zero rows (QG-1, plan.md § Testing, depends on T046).
  - **Acceptance**: Both CSVs have ≥ 49 rows; gate job in T046 includes a coverage assertion.
- [X] T063 [P] Run `ps-rule run -f infra/` and `az deployment sub what-if` against `infra/main.bicep` — assert AU-East residency invariant (Constitution NN-1) holds for the two new child resources and assert "0 net-new top-level Azure resources" (PD-037-06, SC-009, depends on T037, T038). — Acceptance: `infra/main.bicep` what-if notes record PD-037-06 rationale (no top-level resources, 2 child resources, 2 metrics) inline.
  - **Acceptance**: ps-rule clean; what-if diff shows exactly 2 child resources, 0 top-level resources.
- [X] T064 [P] Add a back-citation row in the Risk Register (`docs/risk-register/RISK-NEW-NN.md` for the Foundry RAG component) AND in the RAI Register row for the Foundry RAG client referencing `infra/parameters/foundry-carveout.yaml` as the carve-out authority (Constitution NN-1 carve-out, FR-024, FR-025, depends on T056, T059).
  - **Acceptance**: Both rows cite the YAML file by relative path; T021 link-check passes.
- [X] T065 [P] Emit and document the App Insights custom metric `evidence_pack.manual_row_ratio` from `manual_row_ratio.py` with dimensions `{ artefact_id, publication_id, environment }`; add to `docs/governance-hub/observability/metrics-catalogue.md` and surface in each artefact's `metadata.manual_row_ratio` (RES-05, FR-037, depends on T033, T058). — Acceptance: metric appears in artefact `metadata.manual_row_ratio` and in metrics-catalogue; the metric is NOT inserted as a `kpi_row` in the Executive KPI Surface (would not satisfy `kpi_row.criterion_id` enum which is restricted to the five SC-CAP criteria).
  - **Acceptance**: Metric appears in App Insights schema; metrics-catalogue entry exists.
- [X] T066 Final pass on `docs/governance-hub/index.md` — confirm navigation links to all five new artefacts, the executive page, the four ADRs, and the publication-gate constraint (FR-002, FR-006, depends on T049, T050, T056–T060).
  - **Acceptance**: Hub renders; T047 link-check passes; manual review confirms scannability.
- [X] T067 Run `specs/037-capstone-evidence-pack/quickstart.md` end-to-end as the named operator: add a risk row, publish an artefact, intentionally exceed the cap, record an auditor sign-off, verify the executive page reflects each step (FR-035, FR-038, SC-011, depends on all prior phases).
  - **Acceptance**: Each quickstart step succeeds or produces the documented failure mode; deviations recorded as defects.
- [X] T068 Cross-check the 84 verification items in `specs/037-capstone-evidence-pack/checklists/capstone-evidence-pack.checklist.md` — every CHK### maps to at least one task above; record exceptions in the checklist.
  - **Acceptance**: Checklist `Status` column populated for all 84 items; 0 exceptions OR each exception linked to a follow-up issue.
- [X] T069 Verify "no net-new top-level Azure resources" invariant by re-running the constitution-check table in `plan.md` § Constitution Check after Polish; assert `.specify/memory/constitution.md` is byte-identical to its pre-spec-037 state (`git diff --quiet HEAD~ -- .specify/memory/constitution.md`); record result inline in `plan.md` § Re-evaluation (FR-004, PD-037-06, SC-009, depends on T063).
  - **Acceptance**: Plan re-evaluation block updated to "PASS — post-polish"; constitution diff is empty; no new violations.

**Checkpoint**: Spec ready for `/speckit.analyze`; all FRs and SCs have at least one task citation; rubric gaps closed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies.
- **Phase 2 (Tests)**: depends on Phase 1 (schemas mirrored, dirs scaffolded).
- **Phase 3 (Backend)**: depends on Phase 2 — tests must be red first.
- **Phase 4 (Frontend)**: depends on Phase 3 (T036 routes) + Phase 2 Vitest tests.
- **Phase 5 (CI Gate)**: depends on Phase 2 publication-gate tests (T018–T021).
- **Phase 6 (Docs/ADRs)**: depends on Phase 1; can begin in parallel with Phase 3/4.
- **Phase 7 (Artefacts)**: depends on Phase 5 (gate must exist) + Phase 6 (hub navigation + ADRs) + Phase 3 Pydantic models (for schema-validity authoring).
- **Phase 8 (Polish)**: depends on all prior phases.

### User Story Dependencies

- **US1 (Risk)**: T026 → T056. Independent of US2–US5 once T045 (gate) lands.
- **US2 (Adoption)**: T027 → T057. Independent of others.
- **US3 (KPI)**: T028 → T039 → T040..T044 → T058. Front-end depends on backend route T036.
- **US4 (RAI)**: T029 → T059. Independent of others.
- **US5 (Feature-Value Ledger)**: T030 → T060. Depends on T052–T055 (ADRs) for the Tradeoff Log section.

### Parallel Opportunities

- **6 schema contract tests** T008–T013 — all `[P]`, distinct files.
- **4 OpenAPI route tests** T014–T017 — all `[P]`.
- **4 publication-gate tests** T018–T021 — all `[P]`.
- **3 Vitest unit tests + axe scaffolding** T022–T025 — all `[P]`.
- **7 Pydantic models** T026–T031 — all `[P]`, distinct files (T032 envelope joins).
- **4 ADRs** T052–T055 — all `[P]`.
- **5 artefact authoring tasks** T056–T060 — all `[P]`, disjoint file trees.
- **Polish** T061–T065 — all `[P]`, distinct surfaces.

---

## Implementation Strategy

### MVP scope

The "MVP" for this delivery-hygiene spec is **all five artefacts published behind the CI gate**. There is no smaller increment that satisfies the rubric — the rubric requires evidence across all four mandatory + differentiator dimensions. Phases 1–5 + at least US1 (T056) constitutes a credible early demo (Risk Register + executive page + gate); US2–US5 then land in parallel.

### Incremental delivery sequence

1. Phase 1 + Phase 2 (Setup + red tests) — single PR.
2. Phase 3 + Phase 4 (Backend + Frontend) — second PR; turns Phase 2 green.
3. Phase 5 + Phase 6 (Gate + Docs/ADRs) — third PR; gate becomes required for branch-protection.
4. Phase 7 (Artefacts) — five PRs in parallel, one per US, each gated by the now-required CI job.
5. Phase 8 (Polish) — final PR.

### Parallel team strategy

- One backend engineer drives Phases 3 + 5.
- One frontend engineer drives Phase 4.
- One technical writer + SME pair per artefact drives Phase 7 (5 pairs in parallel after Phase 6 lands).
- One platform engineer drives Phases 1 + 6 + 8 polish items T063, T065, T069.

---

## Format-validation summary

- **Total tasks**: 69 (T001–T069).
- **Parallelisable tasks (`[P]`)**: 39.
- **User-story-tagged tasks**: 11 (`[US1]` × 2, `[US2]` × 2, `[US3]` × 7, `[US4]` × 2, `[US5]` × 2; cross-cutting tasks carry no story label per the format rule).
- **All FR-001..FR-038 referenced**: ✅ verified — see citations inline.
- **All SC-001..SC-011 referenced**: ✅ verified — see citations inline.
- **All PD-037-01..06 referenced**: ✅.
- **All RES-01..05 referenced**: ✅.
- **CHK### references**: 30+ items spot-cited; T068 closes the loop on all 84.
- **Authority citations**: Constitution NN-1..NN-5, QG-1..QG-3, Principles I/II/III/IV/VIII; `028-capstone-alignment` FR-020; `governance-discovery.instructions.md`; `bicep-policy-compliance.instructions.md` (via T063 ps-rule).

---

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- `[Story]` label maps a task to a single user story; cross-cutting tasks (Setup, Backend services, CI, Docs, Polish) carry no story tag per the format rule.
- Verify Phase 2 tests are red before starting Phase 3.
- Commit after each task or each parallel batch.
- `/speckit.analyze` will cross-check FR/SC coverage; if a follow-up FR is added later, append a task here rather than retro-editing existing ones.

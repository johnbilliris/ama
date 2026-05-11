---
description: "Task list for spec-038 Measurable Success-Criteria Evidence Harness"
---

# Tasks: Measurable Success-Criteria Evidence Harness (spec 038)

**Branch**: `038-success-criteria`
**Input**: `specs/038-success-criteria/{spec.md, plan.md, research.md, data-model.md, contracts/openapi.evidence-harness.yaml, quickstart.md, checklists/success-criteria.md}`
**Tests**: REQUESTED — contract + integration + Playwright/axe-core (per plan §Project Structure and quickstart §4).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase (different files, no in-phase dependencies).
- **[Story]**: User story tag (US1..US7) where the task delivers a vertical slice of that story.
- **[MANUAL]**: Task NOT to be executed by `/speckit.implement`; reserved for human action (e.g. PR-review-time edits to shared registry files, per spec-037 precedent).
- **Pillar IDs**: `T-A* = Pillar A KPI Model`, `T-B* = Pillar B Measurement Framework`, `T-C* = Pillar C Simulation Logic`, `T-D* = Pillar D Expected Impact`, `T-E* = Pillar E Benchmarks`, `T-F* = Pillar F Instrumentation`. `T-S* = Setup/IaC`, `T-G* = SRE/governance & cross-cutting`, `T-Z* = Polish`.
- Every task cites the FR / SC / CHK it satisfies in trailing brackets so traceability survives task split/merge.

---

## Phase 1: Setup (Shared Infrastructure) — `T-S*`

**Purpose**: Cosmos containers, Blob cold archive, Bicep wiring, base FastAPI router scaffold, frontend route stub. Blocks every pillar.

- [X] T-S01 Add `infra/bicep/modules/evidence-harness.bicep` declaring 7 Cosmos SQL containers (`kpi_ladder` PK `/kpi_id`, `kpi_signals` PK `/scenario_id`, `delta_scorecards` PK `/scenario_id`, `causal_chains` PK `/capability_id`, `benchmark_register` PK `/kpi_id`, `evidence_audit` PK `/audit_id`, `evidence_audit_dlq` PK `/audit_id`) + 1 Blob container `evidence-audit-cold` (Cool tier, 7-year immutability lock) via `avm/res/storage/storage-account` + 1 App Insights workbook `evidence-harness-slo`; pin to `australiaeast` w/ `australiasoutheast` paired DR. [FR-029, FR-025, SC-009, CHK045, CHK051]
- [X] T-S02 Wire `evidence-harness.bicep` into `infra/bicep/main.bicep` behind new `enableEvidenceHarness` parameter (default `true` for non-prod); ensure posture-policy-set rejects non-AU regions. [FR-029, SC-009, CHK045]
- [X] T-S03 [P] Add `apps/api/scripts/seed_evidence_containers.py` (idempotent CLI for local Cosmos emulator seeding of the 7 containers). [Quickstart §1]
- [X] T-S04 [P] Add Pydantic v2 base models package skeleton at `apps/api/app/services/evidence/models/__init__.py` and stub files `kpi.py`, `signal.py`, `scorecard.py`, `chain.py`, `benchmark.py`, `audit.py` per data-model.md. [data-model.md §all, FR-002, FR-024]
- [X] T-S05 [P] Add domain twins skeleton `packages/domain/src/domain/models/evidence_*.py` and `packages/domain/src/evidence/*.ts` referenced by data-model.md §intro. [FR-034, plan.md §Project Structure]
- [X] T-S06 Create FastAPI router scaffold `apps/api/app/services/evidence/router.py` mounting prefix `/api/v1/evidence` and `apps/api/app/services/evidence/health.py` exposing `/healthz/evidence` (HEAD-pings the 7 Cosmos containers + Blob container reachable). [Research D1, D13, contracts: `healthzEvidence`]
- [X] T-S07 [P] Add Next.js route stub `apps/web/src/app/governance/evidence/page.tsx` mounting the existing `PersonaWorkspace` shell with six empty tab slots (KPI Ladder, Measurement Method, Replay Scorecard, Impact Chains, Benchmarks, Audit Trace). [FR-034, SC-012, Research D7]
- [X] T-S08 [P] Add resilience-wrapped Cosmos client factory at `apps/api/app/services/evidence/_clients.py` reusing the shared retry/circuit-breaker helpers from `services/governance` (no new resilience primitives). [Research D9, FR-034]
- [X] T-S09 [P] Add correlation-ID middleware glue (reuse existing) so every `/api/v1/evidence/*` response emits `x-ama-correlation-id`; add unit assertion. [Research D9, Quickstart §2]
- [X] T-S10 [P] Reuse `apps/agents/common/llm_client.py` and `…/retrieval_client.py` adapter under `apps/api/app/services/evidence/_summariser.py` (summarisation-only, deterministic prompt, no scoring/routing). [FR-030, FR-036, Research D6]

**Checkpoint**: Containers, Bicep, router scaffold, frontend stub, and shared clients in place. All pillar phases unblocked.

---

## Phase 2: Foundational (Blocking Prerequisites) — `T-S11..T-S15`

**Purpose**: Cross-pillar invariants every story depends on — region guard, advisory-only banner, append-only audit guard, life-safety ranker, bootstrap-CI helper.

- [X] T-S11 Implement AU-region write guard in `apps/api/app/services/evidence/_guards.py` (rejects non-AU `region` field at write time, emits `evidence_audit` entry with `kind="non_au_signal_refused"`, returns RFC-7807 ProblemDetails). [FR-029, SC-009, CHK045]
- [X] T-S12 Implement append-only audit Manager guard in `apps/api/app/services/evidence/instrumentation/audit_manager.py` (rejects PATCH/DELETE; amendments persisted as new entry with `kind="kpi_amendment_recorded"` + `references["original_id"]`). [FR-025, CHK046, CHK054]
- [X] T-S13 Implement life-safety primacy ranker `apps/api/app/services/evidence/kpi_ladder/rank.py` (sorts `IndicatorDefinition.life_safety_tier == "life_safety"` ahead of `"efficiency"` regardless of magnitude). [FR-006, CHK006]
- [X] T-S14 Implement bootstrap-95% CI helper `apps/api/app/services/evidence/measurement/confidence.py` (NumPy resampling, default ≥1,000 resamples; <1,000 → ±1 SD with `small-sample` label). Reuses spec-030 pattern. [FR-009, FR-010, Research D5, CHK013, CHK014]
- [X] T-S15 Implement advisory-only banner emitter on the `ProblemDetails` response model and on `DeltaScorecard`/`Signal` (`advisory_only=true` default; `low`-band signals MUST be advisory-only AND reduced-fidelity). [FR-024, FR-030, data-model.md cross-entity invariants]

**Checkpoint**: Guards and shared computation primitives ready. User-story phases (3..9) may now proceed in parallel where staffing permits.

---

## Phase 3: User Story 1 — Risk-Manager KPI Ladder (Pillar A, P1) 🎯 MVP

**Goal**: Versioned KPI ladder with all 9 attributes per indicator, AIIMS-function + incident-level decomposition, risk-adjusted twin, life-safety ranking — published via `GET /api/v1/evidence/kpi-ladder`.

**Independent test**: Inspect ladder; for any of the five SC-CAP-015-001..005 verify ≥1 leading + ≥1 lagging indicator with all 9 attributes, both adjusted/unadjusted variants, AIIMS + incident-level tags, and that life-safety tier sorts above efficiency.

### Tests for US1 (write first, watch them fail)

- [X] T-A01 [P] [US1] Contract test `tests/contract/test_evidence_kpi_ladder.py` validating `getKpiLadder` request/response schemas + 409 on `include_risk_adjusted=true` with missing matrix, against `contracts/openapi.evidence-harness.yaml`. [FR-001..FR-006, SC-001, CHK001..CHK011]
- [X] T-A02 [P] [US1] Integration test `tests/integration/test_kpi_ladder_versioning.py` asserting publish creates new doc + supersedes prior version + prior remains retrievable. [FR-005, US1 Acceptance #2, CHK030 (versioning)]
- [X] T-A03 [P] [US1] Integration test `tests/integration/test_manual_share_block.py` asserting publication blocked when manual share > 50 % unless `auditor_signoff_recorded` audit row exists. [FR-028, SC-010, US1 Acceptance #3]

### Implementation for US1

- [X] T-A04 [P] [US1] Implement Pydantic v2 models `IndicatorDefinition`, `ConfidenceBandRule`, `RiskAdjustment`, `KpiLadderView` in `apps/api/app/services/evidence/models/kpi.py` per data-model.md §1. [FR-002, FR-004, CHK003..CHK011]
- [X] T-A05 [US1] Implement `kpi_ladder/repository.py` (Cosmos read/write + version monotonicity check + transactional `superseded_by` link). [FR-005, CHK030]
- [X] T-A06 [US1] Implement `kpi_ladder/manager.py` (publish flow: validates ≥1 leading + ≥1 lagging per `capstone_sc_id`; manual-share gate; risk-adjusted twin computation `value × (L×C)/25`). [FR-001, FR-004, FR-028, SC-001, SC-010, CHK001, CHK002, CHK010]
- [X] T-A07 [US1] Implement `kpi_ladder/router.py` `GET /api/v1/evidence/kpi-ladder` (filters: `capstone_sc_id`, `include_risk_adjusted`); returns 409 with Edge Case #5 message when adjusted requested but matrix missing. [contracts: `getKpiLadder`, FR-004]
- [X] T-A08 [P] [US1] Implement frontend `KpiLadderTab` in `apps/web/src/app/governance/evidence/_tabs/KpiLadderTab.tsx` reusing existing `PersonaWorkspace` table primitives — no new chart libs. [SC-012, FR-034, US1]
- [X] T-A09 [P] [US1] Playwright case in `apps/web/tests/playwright/governance/evidence.spec.ts` walking the KPI Ladder tab and verifying 9 attribute columns + risk-adjusted toggle. [SC-001, US1 Independent Test]

**Checkpoint**: US1 fully functional and demoable independently — MVP-ready.

---

## Phase 4: User Story 2 — Executive Measurement-Method Document (Pillar B, P1)

**Goal**: Single Measurement-Method document published via `GET /api/v1/evidence/measurement-method` with plain-language definitions for each of the five capstone metrics, the start/end signals, the missing-timestamp rule, the bootstrap-CI rule, and the calibration method.

**Independent test**: Executive opens the document and finds, in <2 minutes without referencing other docs, the definition + start/end signals + unit + confidence-band rule for any chosen capstone metric.

### Tests for US2

- [X] T-B01 [P] [US2] Contract test `tests/contract/test_evidence_measurement_method.py` validating `getMeasurementMethod` schemas (markdown + json formats). [FR-007..FR-010, SC-002]
- [X] T-B02 [P] [US2] Integration test `tests/integration/test_imputation_rule.py` exercising forward-impute + label + CI exclusion + >10 % small-sample gate. [FR-008, CHK015..CHK017]

### Implementation for US2

- [X] T-B03 [US2] Implement deterministic Measurement-Method renderer `apps/api/app/services/evidence/measurement/renderer.py` (composes ladder + bootstrap config + canonical chain semantics into markdown; LLM summarisation only via `_summariser.py` for prose blocks). [FR-007, FR-009, Research D6]
- [X] T-B04 [US2] Implement `measurement/imputation.py` (forward-impute from next-adjacent event in call→dispatch→arrival→control→clear chain; tag `missing-timestamp` + `reduced-fidelity`; >10 % rows → `small_sample` flag + auditor-signoff gate). [FR-008, FR-027, CHK015..CHK017]
- [X] T-B05 [US2] Implement `measurement/router.py` `GET /api/v1/evidence/measurement-method?format={markdown|json}`. [contracts: `getMeasurementMethod`]
- [X] T-B06 [P] [US2] Implement frontend `MeasurementTab.tsx` rendering the markdown via existing prose primitive; sticky table-of-contents for the five metrics. [SC-002, US2]

**Checkpoint**: US2 reads Measurement-Method end-to-end without other docs.

---

## Phase 5: User Story 3 — Resilience-Planner Replay & Delta Scorecard (Pillar C, P1)

**Goal**: Run any of the 7 canonical scenarios in baseline + AMA-assisted modes via `POST /api/v1/evidence/scenarios/{scenario_id}/replay`, get a per-KPI delta scorecard with confidence bands and a `meets target?` flag, deterministic to the documented tolerance.

**Independent test**: Run bushfire seed `S1` twice; deltas reproduce within ±2 % rel OR ±1 abs unit; degraded-mode run still returns values for every KPI.

### Tests for US3

- [X] T-C01 [P] [US3] Contract test `tests/contract/test_evidence_replay.py` validating `replayScenario` request/response + `allow_degraded_mode` semantics. [FR-011..FR-016]
- [X] T-C02 [P] [US3] Integration test `tests/integration/test_baseline_vs_ama_delta.py` covering all 7 canonical scenarios × 5 capstone KPIs (SC-003). [SC-003, CHK022, CHK024]
- [X] T-C03 [P] [US3] Integration test `tests/integration/test_replay_determinism.py` asserting ≥95 % of repetitions reproduce within ±2 % rel / ±1 abs unit; divergent runs surface, not hide. [FR-016, SC-004, CHK020]

### Implementation for US3

- [X] T-C04 [P] [US3] Implement Pydantic models `Signal`, `CanonicalEventChain`, `ConfidenceScore` in `apps/api/app/services/evidence/models/signal.py` per data-model.md §2 (with AU-region enum + low-band advisory-only invariant). [FR-024, FR-029, CHK010]
- [X] T-C05 [P] [US3] Implement Pydantic models `KpiDelta`, `DeterminismCheck`, `DeltaScorecard` in `apps/api/app/services/evidence/models/scorecard.py` per data-model.md §3 (must contain exactly the 5 capstone KPIs). [FR-015, SC-003]
- [X] T-C06 [US3] Implement `simulation/orchestrator.py` calling existing spec-026 warp-playback API with seed pair (baseline / AMA-assisted); captures emitted signals into `kpi_signals`. NO new sim engine. [FR-013, FR-014, Research D4]
- [X] T-C07 [US3] Implement `simulation/scorecard_builder.py` computing per-KPI deltas + confidence bands (uses T-S14 helper) + determinism check (≥2 repeats, tolerance ±2 % rel OR ±1 abs unit) + `meets_target` flag + `reduced_fidelity` propagation. [FR-015, FR-016, FR-027, SC-004]
- [X] T-C08 [US3] Implement `simulation/router.py` `POST /api/v1/evidence/scenarios/{scenario_id}/replay` with body `{seed, run_pair_id, repetitions, allow_degraded_mode}`. [contracts: `replayScenario`, FR-027, FR-032]
- [X] T-C09 [US3] Persist canonical scenario catalogue (bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR) in `simulation/scenarios.py` (string registry only — actual scenario assets owned by spec 007). [FR-011, CHK022]
- [X] T-C10 [P] [US3] Implement frontend `ReplayTab.tsx` with scenario picker, seed input, mode toggle, scorecard table reusing existing badge primitives for `reduced_fidelity` / `small_sample` / `diverged`. [SC-012, US3 Acceptance #3]

**Checkpoint**: US3 produces baseline-vs-AMA scorecards for all 7 scenarios, reproducible to tolerance.

---

## Phase 6: User Story 4 — Auditor End-to-End Trace (Pillar F, P1)

**Goal**: Audit any KPI value via `GET /api/v1/evidence/audit/{value_id}` and walk signal → model → recommendation → human-decision → outcome inside one view; append-only.

**Independent test**: Auditor picks any KPI value at random and walks the full chain in <3 minutes; amendments preserve original.

### Tests for US4

- [X] T-F01 [P] [US4] Contract test `tests/contract/test_evidence_audit.py` validating `getAuditTraceForValue` schema and 5-step chain coverage. [FR-026, SC-005]
- [X] T-F02 [P] [US4] Integration test `tests/integration/test_audit_append_only.py` asserting PATCH/DELETE rejected; amendment recorded as new entry preserving original. [FR-025, CHK046]
- [X] T-F03 [P] [US4] Integration test `tests/integration/test_au_region_refusal.py` asserting non-AU `region` rejected at write + `non_au_signal_refused` audit entry created. [FR-029, SC-009, CHK045]

### Implementation for US4

- [X] T-F04 [P] [US4] Implement `AuditEntry` + `AuditKind` in `apps/api/app/services/evidence/models/audit.py` per data-model.md §6 (10 audit kinds enumerated). [FR-025, FR-026, FR-027..FR-029]
- [X] T-F05 [US4] Implement `instrumentation/signal_ingest.py` (write-path for `kpi_signals`; enforces AU-region guard T-S11; emits `signal_ingested` audit entry; refuses & logs non-AU). [FR-023, FR-024, FR-029, SC-009]
- [X] T-F06 [US4] Implement `instrumentation/audit_repository.py` (Cosmos write + change-feed publisher to Blob cold-archive at age 90 d, marking `archived_to_blob=true`). [FR-025, Research D3]
- [X] T-F07 [US4] Implement `instrumentation/router.py` `GET /api/v1/evidence/audit/{value_id}` (falls through to Blob index when record older than 90 d; returns 5-step chain or `degraded_mode_entered` for any missing step). [contracts: `getAuditTraceForValue`, SC-005]
- [X] T-F08 [US4] Implement degraded-mode handlers (`FR-027` / `FR-032`): reduced-fidelity flag propagation through ingest → scorecard → audit; `degraded_mode_entered` audit entry on each degraded ingest cycle. [FR-027, FR-032, SC-008]
- [X] T-F09 [P] [US4] Implement frontend `AuditTab.tsx` rendering the 5-step chain in a single panel reusing existing timeline primitives. [SC-005, SC-012, US4]

**Checkpoint**: Any published KPI value walks end-to-end in one view; audit log immutable + cold-archived.

---

## Phase 7: User Story 5 — Architect/Principal-Engineer Causal Chains (Pillar D, P2)

**Goal**: Per-capability causal chain (capability → KPI(s) moved → expected magnitude → assumptions → threats to validity → originating-spec citation) published via `GET /api/v1/evidence/causal-chains/{capability_id}`.

**Independent test**: Pick any capability (specs 008–012, 036, 036-sim-agent-extend); chain names ≥1 KPI moved, magnitude w/ units, ≥1 assumption, ≥1 threat, citation back to origin spec.

### Tests for US5

- [X] T-D01 [P] [US5] Contract test `tests/contract/test_evidence_causal_chain.py` validating `getCausalChain` schema. [FR-017..FR-019, SC-006]
- [X] T-D02 [P] [US5] Integration test `tests/integration/test_causal_chain_coverage.py` asserting every capability id (specs 008, 009, 010, 011, 012, 036, 036-sim-agent-extend) has ≥1 published chain w/ valid `originating_spec_path`. [SC-006]

### Implementation for US5

- [X] T-D03 [P] [US5] Implement `CausalChain`, `Assumption`, `ThreatToValidity` in `apps/api/app/services/evidence/models/chain.py` per data-model.md §4. [FR-017, FR-018, FR-019]
- [X] T-D04 [US5] Implement `impact/repository.py` + `impact/manager.py` (publish + supersede; validates `originating_spec_path` starts with `specs/` and resolves on disk). [FR-018, SC-006]
- [X] T-D05 [US5] Implement `impact/router.py` `GET /api/v1/evidence/causal-chains/{capability_id}`. [contracts: `getCausalChain`]
- [X] T-D06 [US5] Seed initial 7 causal-chain documents (one per capability listed above) sourced from each origin spec's stated KPI claims; mark unresolved assumptions per FR-019. [FR-017, FR-019, SC-006]
- [X] T-D07 [P] [US5] Implement frontend `ImpactTab.tsx` showing capability → KPI graph (reuses existing list primitive — NO new graph lib) with unresolved-assumption badge. [SC-012, FR-019]

**Checkpoint**: 100 % of AMA capabilities have a published chain with required fields.

---

## Phase 8: User Story 6 — Sector Benchmark Render (Pillar E, P3)

**Goal**: Per-jurisdiction benchmark render via `GET /api/v1/evidence/benchmarks/{kpi_id}?jurisdiction=…`; distinguish external benchmark from prototype baseline; mark unavailable benchmarks "not available" while still surfacing prototype baseline.

**Independent test**: For NSW Ambulance + mass-casualty scenario, the response shows NSW Pri-1 benchmark, prototype baseline, and AMA-assisted value, each labelled distinctly.

### Tests for US6

- [X] T-E01 [P] [US6] Contract test `tests/contract/test_evidence_benchmarks.py` validating `getBenchmarksForKpi` schema + `not_available` semantics. [FR-020..FR-022, SC-007]
- [X] T-E02 [P] [US6] Integration test `tests/integration/test_benchmark_register_coverage.py` asserting every `kpi_id` in the ladder has ≥1 entry; missing external benchmark → `not_available=true` AND a sibling `prototype_baseline` entry exists. [SC-007]

### Implementation for US6

- [X] T-E03 [P] [US6] Implement `BenchmarkEntry` model in `apps/api/app/services/evidence/models/benchmark.py` per data-model.md §5. [FR-020..FR-022]
- [X] T-E04 [US6] Implement `benchmarks/repository.py` + `benchmarks/manager.py` (publish + retrieve filtered by jurisdiction). [FR-020, FR-021]
- [X] T-E05 [US6] Implement `benchmarks/router.py` `GET /api/v1/evidence/benchmarks/{kpi_id}` with `jurisdiction` query. [contracts: `getBenchmarksForKpi`]
- [X] T-E06 [US6] Seed benchmark register entries enumerated in FR-020 (AFAC FDI/FFDI, BoM lead-time, NSW/VIC/QLD/SA/WA/ACT/NT/TAS ambulance Pri-1, FRNSW/FRV/SAMFS structural-fire turnout, SES flood-rescue + sandbag, police evacuation, ICAO ARFF, SAIDI/SAIFI, AIIMS span-of-control). [FR-020, SC-007]
- [X] T-E07 [P] [US6] Implement frontend `BenchmarkTab.tsx` with jurisdiction picker; renders external + prototype-baseline rows distinctly. [SC-007, US6 Acceptance #1]

**Checkpoint**: Sector readers see jurisdiction-aware benchmark vs prototype values.

---

## Phase 9: User Story 7 — Public-Information Officer 8-Language Render (Pillar A/F crossover, P3)

**Goal**: Public-Information KPI render covering alert reach, behavioural-impact proxy, multilingual coverage; ≥8 language channels per canonical scenario from the existing `language-packs.ts` catalogue; rendered views pass WCAG 2.2 AA.

**Independent test**: Open Public Information view for cyclone scenario; reach + behavioural-impact + multilingual indicators each have formula/unit/baseline/provenance; multilingual indicator shows ≥8 language channels including Auslan + ≥1 First-Nations language; axe-core scan passes.

### Tests for US7

- [X] T-A10 [P] [US7] Playwright + axe-core test in `apps/web/tests/playwright/governance/evidence.spec.ts` asserting ≥8 language channels render and WCAG 2.2 AA passes for all 6 tabs. [FR-037, SC-013, CHK054, CHK056]
- [X] T-A11 [P] [US7] Integration test `tests/integration/test_public_information_indicators.py` asserting reach + behavioural-impact-proxy + multilingual-coverage indicators exist with required attributes for the cyclone scenario. [FR-002, FR-037, US7 Acceptance #1]

### Implementation for US7

- [X] T-A12 [US7] Add Public Information indicator definitions (alert reach, behavioural-impact proxy, multilingual coverage) into the seeded KPI ladder (Pillar A) with `aiims_function="PublicInformation"`. [FR-002, FR-003, FR-037]
- [X] T-A13 [US7] Wire frontend `KpiLadderTab` Public Information slice to iterate `apps/web/src/lib/i18n/language-packs.ts` (REUSE — no new language assets) for the 8 channels (English plain-Grade-8 + Mandarin + Arabic + Vietnamese + Cantonese + Punjabi + Auslan + ≥1 jurisdiction-appropriate First-Nations language). [FR-037, SC-013, FR-013, FR-034]
- [X] T-A14 [US7] Add WCAG 2.2 AA conformance fixes (focus order, ARIA roles, contrast) to Public Information render — reuses existing accessibility primitives. [SC-013, FR-034]

**Checkpoint**: All 7 user stories independently functional.

---

## Phase 10: SRE / SLO / Chaos / Observability — `T-G*`

**Purpose**: SLO workbook, burn-rate alerts, three staged chaos experiments validating FR-027 / FR-032.

- [X] T-G01 Author `evidence-harness-slo` workbook contents (SLIs: endpoint availability ≥99.5 %, replay-job success ≥98 %, metric freshness ≤60 s) and check it into `infra/bicep/modules/evidence-harness.bicep` or sibling JSON. [Research D12, Plan §Constraints]
- [X] T-G02 Add burn-rate alerts at 2 %/h (informational) and 5 %/h (page-out) for each SLI. [Research D12]
- [X] T-G03 [P] Implement chaos experiment 1 — Cosmos 429 throttle on `kpi_signals` — at `apps/api/scripts/chaos_evidence.py --experiment cosmos_429`. Verify replay retries + degraded-mode flag. [FR-027, FR-032, Research D12]
- [X] T-G04 [P] Implement chaos experiment 2 — AOAI timeout during Measurement-Method summarisation — verify document still renders deterministic content with "summary unavailable" reduced-fidelity tag. [FR-027, FR-036, Research D12]
- [X] T-G05 [P] Implement chaos experiment 3 — App Insights ingestion lag — verify SLO dashboard surfaces freshness breach alert without dropping evidence. [FR-027, Research D12]
- [X] T-G06 [P] Document chaos drill runbook in `docs/sre/evidence-harness-chaos.md` with rollback steps. [Research D12]
- [X] T-G07 Wire RED metrics (Rate, Errors, Duration) emission for every endpoint via shared instrumentation; assert presence in App Insights `requests` table within 60 s. [Research D9, Quickstart §2]
- [X] T-G08 [P] Add `/healthz/evidence` contract test `tests/contract/test_evidence_healthz.py` (pings 7 Cosmos containers + Blob). [contracts: `healthzEvidence`, Research D13]

---

## Phase 11: Polish & Cross-Cutting — `T-Z*`

- [X] T-Z01 [P] Update `apps/api/openapi.json` build to include the new `/api/v1/evidence/*` paths from `specs/038-success-criteria/contracts/openapi.evidence-harness.yaml`. [FR-031]
- [X] T-Z02 [P] Add CAP/EDXL/GeoJSON-compatible export option to scorecard endpoint where applicable. [FR-031]
- [X] T-Z03 [P] Add per-pillar README index at `apps/api/app/services/evidence/README.md` linking each pillar module to its FR/SC anchors. [Plan §Project Structure]
- [X] T-Z04 [P] Run quickstart.md §2–§5 end-to-end against dev subscription; capture output for spec-037 evidence pack contribution. [FR-035, Quickstart]
- [X] T-Z05 [P] Run full test pyramid (`uv run pytest tests/contract/test_evidence_*.py tests/integration/test_*.py -v` + Playwright/axe-core) and attach junit report. [Plan §Testing]
- [X] T-Z06 [P] Re-validate the 11 constitution gates from `plan.md` post-implementation; record results in PR description. [Plan §Constitution Check]
- [X] T-Z07 [P] Verify Terraform parity decision per Research D10: if spec-035/037 Terraform mirrors are present, add `infra/terraform/modules/evidence-harness.tf`; otherwise file follow-up issue and link from PR.
- [ ] T-Z08 [MANUAL] Append the FR-033 / SC-011 capstone-trace row at the end of the *"Spec-level capstone-criticality flags"* table in `specs/shared/capstone-metric-trace.md`, mirroring the spec-037 row (verbatim text in `plan.md` §"Capstone-trace tagging step"). **Not auto-implemented by `/speckit.implement`** — applied at PR-review time per spec-037 precedent. [FR-033, SC-011, Plan §Capstone-trace tagging step, Research D14]

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup `T-S01..T-S10`)** → no deps.
- **Phase 2 (Foundational `T-S11..T-S15`)** → depends on Phase 1; **BLOCKS** all user-story phases.
- **Phase 3 US1 (`T-A01..T-A09`)** → depends on Phase 2.
- **Phase 4 US2 (`T-B01..T-B06`)** → depends on Phase 2; consumes ladder from US1 at runtime but may be implemented in parallel against test fixtures.
- **Phase 5 US3 (`T-C01..T-C10`)** → depends on Phase 2; consumes ladder + bootstrap helper.
- **Phase 6 US4 (`T-F01..T-F09`)** → depends on Phase 2; consumes signals from US3 at runtime; tests use fixtures.
- **Phase 7 US5 (`T-D01..T-D07`)** → depends on Phase 2; references KPI IDs from US1 at seed time.
- **Phase 8 US6 (`T-E01..T-E07`)** → depends on Phase 2; references KPI IDs from US1 at seed time.
- **Phase 9 US7 (`T-A10..T-A14`)** → depends on Phase 3 (extends US1 KPI ladder + frontend tab).
- **Phase 10 SRE/Chaos (`T-G*`)** → depends on at least one user-story phase reaching working endpoints (US3 is the richest exerciser of degraded-mode).
- **Phase 11 Polish (`T-Z*`)** → depends on all desired user stories.

### Within each user story

- Tests authored first (must FAIL before implementation).
- Models → repository → manager → router → frontend tab.
- Each story is independently demoable at its checkpoint.

### Parallel opportunities

- All `[P]` tasks within Phase 1, Phase 2, Phase 11 can run concurrently (different files).
- Once Phase 2 completes, Phases 3–8 can proceed in parallel by separate developers; Phase 9 follows Phase 3.
- Within US1 / US3 / US4, all `[P]`-marked tests can be authored in parallel; all `[P]`-marked models in parallel.

---

## Parallel Example: Kicking off MVP after Setup

```bash
# After T-S01..T-S15 complete, launch US1 tests + models in parallel:
Task: "T-A01 Contract test for /evidence/kpi-ladder"
Task: "T-A02 Integration test for ladder versioning"
Task: "T-A03 Integration test for manual-share block"
Task: "T-A04 Pydantic models in services/evidence/models/kpi.py"
Task: "T-A08 Frontend KpiLadderTab.tsx"
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 + Phase 2 (Setup + Foundational) — **CRITICAL gate**.
2. Phase 3 US1 (KPI ladder) — demoable to a Risk Manager.
3. **STOP & VALIDATE** SC-001, SC-010, SC-012 against the live ladder.
4. Apply T-Z08 capstone-trace row at PR-review time before merge.

### Incremental delivery

1. Setup + Foundational → Foundation ready.
2. + US1 (KPI ladder) → Demo to Risk Manager (MVP).
3. + US2 (Measurement Method) → Demo to Executive.
4. + US3 (Replay scorecard) → Demo to Resilience Planner — headline replay capability.
5. + US4 (Audit trace) → Demo to Auditor — closes governance loop.
6. + US5/US6/US7 in any order — completes pillar coverage.
7. + Phase 10 SRE/Chaos + Phase 11 Polish before final spec-037 evidence-pack contribution.

### Parallel team strategy

| Dev | Stream                         | Phases     |
| --- | ------------------------------ | ---------- |
| A   | Backend pillars + replay       | 3, 5, 7    |
| B   | Backend audit + benchmark      | 4, 6, 8    |
| C   | Frontend tabs + i18n + a11y    | 3.UI, 4.UI, 5.UI, 6.UI, 7.UI, 8.UI, 9 |
| D   | SRE + chaos + IaC              | 1.IaC, 10  |

---

## Format Validation

All tasks above conform to: `- [ ] [TaskID] [P?] [Story?] Description with file path` and cite the FR / SC / CHK they satisfy. The single `[MANUAL]` task (`T-Z08`) is explicitly excluded from `/speckit.implement` execution and applied at PR review per spec-037 precedent.

## Summary

- **Total tasks**: 84 (`T-S01..T-S15` = 15 + `T-A01..T-A14` = 14 + `T-B01..T-B06` = 6 + `T-C01..T-C10` = 10 + `T-D01..T-D07` = 7 + `T-E01..T-E07` = 7 + `T-F01..T-F09` = 9 + `T-G01..T-G08` = 8 + `T-Z01..T-Z08` = 8).
- **Per user story**: US1 = 9 (Phase 3) + 5 (US7 extension under Phase 9) — Phase 9 (T-A10..T-A14) extends the Pillar A ladder for the PIO render. US2 = 6; US3 = 10; US4 = 9; US5 = 7; US6 = 7; US7 = 5. Cross-cutting: Setup 10 + Foundational 5 + SRE/Chaos 8 + Polish 8 = 31.
- **Parallel opportunities**: 38 tasks marked `[P]` across phases.
- **Manual tasks**: 1 (`T-Z08` capstone-trace row append — deferred to PR review per spec-037 precedent).
- **Suggested MVP**: Phases 1 + 2 + 3 (Setup + Foundational + US1 KPI ladder) — demonstrates the most-asked-for artefact (the ladder) and unlocks every downstream pillar.


---

## Cycle 2 Amendment Tasks — `T-AMD-*`

**Scope**: FR-038..FR-050, SC-014..SC-022, AMD-01..AMD-13. Original `T-S/A/B/C/D/E/F/G/Z*` tasks remain authoritative for FR-001..FR-037 and are NOT regenerated.
**Inputs**: `spec.md` (FR-038..FR-050, SC-014..SC-022, AMD-01..AMD-13, Clarifications §Session 2026-05-11 Cycle 2 R1+R2), `plan-amendments-cycle-2.md` (D15..D28), `data-model.md` (Cycle 2 invariants delta), `contracts/openapi.evidence-harness.yaml` (new 422/409/503 + `getPublicInformationRender`), `checklists/amendments-cycle-2.md` (CHK069..CHK152).
**Format reminder**: `- [ ] [TaskID] [P?] Description with file path [FR / SC / CHK / D-decision / openapi.operationId]`. No `[MANUAL]` tasks in this cycle. Story tags omitted because amendments cut across all original user stories.

### Phase AMD-1: Bicep / IaC hardening (sequential — same file)

- [X] T-AMD-01 Replace `84*30` arithmetic with literal `2555` days and add `immutabilityPolicyState: 'Locked'` on the `evidence-audit-cold` blob container in `infra/bicep/modules/evidence-harness.bicep`; assert via `test/bicep/evidence-harness.tests.bicep` that the compiled ARM emits `immutabilityPeriodSinceCreationInDays: 2555`. [FR-038, SC-014, AMD-01, CHK069..CHK072, D15]
- [X] T-AMD-02 Add `existing` references for the bound Cosmos account, Storage account, and App Insights component in `infra/bicep/modules/evidence-harness.bicep` and add `assert` blocks failing the deployment when `.location ∉ {'australiaeast','australiasoutheast'}` for the general evidence path; **additionally constrain the audit Cosmos account specifically to `australiaeast` only** (single-region requirement per Cycle 2 R2-Q2 / CHK105 — needed so per-operation `consistency_level=Strong` in T-AMD-05 remains compatible with FR-029 + FR-043, since multi-region Strong is forbidden by Cosmos). Update `infra/bicep/main.bicep` to pass the resource IDs. Include a `what-if` fixture under `tests/infra/test_evidence_harness_au_residency.ps1` that points the module at a deliberately mis-located bound resource and asserts the produced error message contains `AU-residency violation` (covers SC-019). [FR-043, FR-044, SC-019, AMD-06, CHK097..CHK100, CHK105, D20, R2-Q2]
- [X] T-AMD-03 Add SLO workbook resource + 30-day rolling-window query + 1h burn-rate Sev1 alert (5 %/h budget burn) and Sev2 alert (2 %/h) in `infra/bicep/modules/evidence-harness.bicep`; introduce required (no default) `sloAlertActionGroupId` parameter wired into both alert rules; thread the parameter through `infra/bicep/main.bicep`. [FR-046, SC-021, AMD-09, CHK115..CHK124, D23]

### Phase AMD-2: Backend audit hardening (parallel — different files)

- [X] T-AMD-04 [P] Implement Cosmos change-feed → immutable Blob mirror as a Container Apps job in `infra/bicep/modules/evidence-harness.bicep` (job definition) + processor `apps/api/app/services/evidence/jobs/audit_mirror.py` reusing the change-feed iterator pattern from `infra/bicep/modules/eval/eval-platform.bicep:390`; emit checkpoint to `evidence_audit_dlq` on failure. [FR-040, SC-016, AMD-03, CHK078..CHK079, D17]
- [X] T-AMD-05 [P] Wrap every `evidence_audit` write in `apps/api/app/services/evidence/audit_writer.py` with a per-operation `consistency_level=Strong` override and a 3-attempt exponential backoff (250 ms / 1 s / 4 s); on final failure raise → FastAPI exception handler returns RFC 7807 ProblemDetails with `status=503`, `title=audit-write-unavailable`, `type=https://ama.example/errors/audit-write-unavailable`. [FR-044, SC-020a, AMD-07, CHK101..CHK108, D21, R2 Q2]
- [X] T-AMD-06 [P] Add a FastAPI dependency in `apps/api/app/services/evidence/router.py` rejecting `PATCH`/`DELETE`/`PUT` on any path beginning with `/api/v1/evidence/audit/` with HTTP 409 ProblemDetails (`title=audit-record-immutable`, `type=https://ama.example/errors/audit-record-immutable`); register the same handler for the read-only audit subrouter. [FR-040, SC-016, AMD-03, CHK073..CHK077, D17, R1 Q2, openapi: `rejectAuditPatch`, `rejectAuditDelete`]

### Phase AMD-3: Backend healthz (single file)

- [X] T-AMD-07 Replace the hardcoded `evidence-audit-cold=True` line in `apps/api/app/services/evidence/health.py` with real probes: enumerate all 7 Cosmos containers (HEAD), Blob `evidence-audit-cold` (HEAD + `immutabilityPolicy` get), change-feed processor lease, and App Insights ingestion (recent telemetry sample). Mark Cosmos + Blob + change-feed processor as **critical** (any down → HTTP 503), App Insights as **non-critical** (down → HTTP 200 with `degraded: true`). [FR-045, SC-020b, AMD-08, CHK109..CHK114, D22, R1 Q1, openapi: `healthzEvidence`]

### Phase AMD-4: Backend client lifecycle (single file)

- [X] T-AMD-08 Restrict the in-memory fallback path in `apps/api/app/services/evidence/_clients.py` to execute only when `os.environ.get("AMA_TEST_MODE") == "1"`; in production, raise `RuntimeError("FR-042: Azure Cosmos / Blob / App Insights configuration missing — refusing to start with in-memory fallback")` so app startup fails fast. Add a `pytest` fixture toggle in `apps/api/tests/conftest.py` exposing `AMA_TEST_MODE=1` for unit tests only. [FR-042, SC-018, AMD-05, CHK093..CHK096, D19]

### Phase AMD-5: Backend Pydantic strictness + TS twin (parallel)

- [X] T-AMD-09 [P] Add `model_config = ConfigDict(extra="forbid")` to every Pydantic v2 model under `apps/api/app/services/evidence/models/*.py` (kpi.py, signal.py, scorecard.py, chain.py, benchmark.py, audit.py); register a global FastAPI exception handler in `apps/api/app/services/evidence/router.py` mapping `ValidationError` → RFC 7807 ProblemDetails with `status=422`, `title=request-body-extra-fields`, including the offending field path. [FR-047, SC-022a, AMD-10, CHK125..CHK130, D24, R2 Q1]
- [X] T-AMD-10 [P] Update the type-only TypeScript twin under `packages/domain/src/evidence/index.ts` so every interface mirrors the Pydantic schemas exactly (no extra optional fields); add an OpenAPI parity contract test `tests/contract/test_openapi_ts_parity.py` asserting field-name + nullability parity per D25. [FR-047, SC-022a, AMD-10, CHK127..CHK129, D25]

### Phase AMD-6: KPI ladder risk-adjustment default

- [X] T-AMD-11 Make `risk_adjustment` a required field on `IndicatorDefinition` in `apps/api/app/services/evidence/models/kpi.py`; in `apps/api/app/services/evidence/seed/kpi_ladder_seed.py` default any indicator missing risk-adjustment input to `RiskAdjustment(likelihood=3, consequence=3, provenance="manual", auditor_signoff_required=True)` and increment the manual-share counter so defaulted rows count toward the FR-028 ≤ 50 % manual-share cap; update `tests/integration/test_kpi_ladder_seed.py` accordingly. [FR-041, SC-017, AMD-04, CHK087..CHK092, D18, R1 Q4]

### Phase AMD-7: Benchmark register seed expansion

- [X] T-AMD-12 Replace the generic seed in `apps/api/app/services/evidence/seed/benchmark_register_seed.py` with ≥ 32 jurisdictional rows (8 Australian jurisdictions × ≥ 4 categories: fire / ambulance / SES / police) + ≥ 5 cross-sector rows (BoM warning classes, NEMA COMDISPLAN, ICAO ARFF, SAIDI / SAIFI, AIIMS span-of-control). Each row carries a `CitationRef(org, document, year, url)`; rows without a citation are tagged `provenance="manual"`; assert ≤ 50 % manual share at seed time (raise on violation). [FR-049, SC-022c, AMD-12, CHK135..CHK140, D27]

### Phase AMD-8: i18n fallback signalling

- [X] T-AMD-13 Add an `Optional[str] language_fallback_used` field to every API response model that returns translated content (`PublicInformationRender`, `IndicatorDescription`, `BenchmarkRow.label_translations`); populate it whenever the language-pack lookup falls back to English, with the requested-but-missing locale tag as the value. **Also append a corresponding `kind="language_fallback_used"` row to `evidence_audit` (per data-model.md Cycle 2 invariants delta — `AuditEntry.language_fallback_used` field).** Update `apps/web/src/app/governance/evidence/_tabs/LanguageFallbackBadge.tsx` (new) and render the badge wherever the field is non-null. [FR-048, SC-022b, AMD-11, CHK131..CHK134, D26]

### Phase AMD-9: Public Information render endpoint

- [X] T-AMD-14 Implement `GET /api/v1/evidence/public-information/{scenario_id}` in `apps/api/app/services/evidence/router.py` returning the 8-language render (English plain-Grade-8 + Mandarin + Arabic + Vietnamese + Cantonese + Punjabi + Auslan + ≥ 1 First-Nations language) by calling `apps/api/app/services/evidence/public_information.py`; include an `auslan_asset_status` field (`available` | `auslan-asset-missing`) — `auslan-asset-missing` permitted as a deferred state for the four non-mandatory canonical scenarios (urban-fire, mass-casualty, hazmat, marine SAR) per FR-039. Cyclone, bushfire and flood MUST report `available`. **Add contract test `tests/contract/test_public_information_render.py` asserting 200-schema parity with `getPublicInformationForScenario` in `contracts/openapi.evidence-harness.yaml` and that `language_fallback_used` is present on fallback / absent otherwise (covers SC-022(b) negative-case gap).** [FR-039, FR-048, SC-015, SC-022b, AMD-02, CHK080..CHK086, CHK134, D16, R1 Q3, openapi: `getPublicInformationForScenario`]

### Phase AMD-10: Frontend live-data wiring (sequential per file, [P] across files)

- [X] T-AMD-15 [P] In `apps/web/src/app/governance/evidence/page.tsx` and the seven tab components under `apps/web/src/app/governance/evidence/_tabs/*Tab.tsx` (`KpiLadderTab`, `MeasurementTab`, `ReplayTab`, `ImpactTab`, `BenchmarkTab`, `AuditTab`, `PublicInformationChannels` — actual file names per `apps/web/src/app/governance/evidence/_tabs/`), replace every stub/placeholder constant with a SWR/React-Query fetch against the corresponding `/api/v1/evidence/*` endpoint; surface degraded / small-sample / manual-provenance / reduced-fidelity states inline; remove dead stub modules. **Add Playwright assertion in `apps/web/tests/playwright/governance/evidence.spec.ts` that every tab issues a fetch to its corresponding `/api/v1/evidence/*` endpoint on first mount (covers SC-022(d) "every tab fetches live data" requirement, not a sampled subset).** [FR-050, SC-022d, AMD-13, CHK141..CHK145, D28]
- [X] T-AMD-16 [P] In `apps/web/src/app/governance/evidence/_tabs/KpiLadderTab.tsx`, render risk-adjusted **and** unadjusted KPI values side-by-side (two columns: `Raw` / `Risk-adjusted (L×C)`) with the `RiskAdjustment.provenance` shown as a chip; flag `auditor_signoff_required=true` rows with the existing `ManualSignoffBadge`. [FR-041, SC-017, AMD-04, CHK091..CHK092, D18]

### Phase AMD-11: Frontend accessibility — Auslan + axe (parallel)

- [X] T-AMD-17 [P] In `apps/web/src/app/governance/evidence/_tabs/PublicInformationChannels.tsx`, render either an Auslan video URL (when `auslan_asset_status=available` — mandatory for cyclone, bushfire, flood per FR-039) **or** a captioned still image with sign-language description text + transcript (when `auslan-asset-missing` — permitted only for urban-fire, mass-casualty, hazmat, marine SAR); show the `auslan-asset-missing` badge whenever the deferred state applies and tag the row `provenance: manual` per FR-039 / CHK082. [FR-039, SC-015, AMD-02, CHK080..CHK086, R1 Q3]
- [X] T-AMD-18 [P] Extend `apps/web/tests/playwright/governance/evidence.spec.ts` with a Public-Information-tab axe-core scan asserting **zero** serious/critical violations, and a Flesch-Kincaid grade-level check on the rendered English plain-language string asserting `≤ 8.0` using the existing `apps/web/src/lib/text/readability.ts` helper. [FR-039, SC-015, AMD-02, CHK083..CHK086]

### Phase AMD-12: Tests — contract + integration (parallel — different files)

- [X] T-AMD-19 [P] Add contract test `tests/contract/test_evidence_extra_fields_rejected.py` POSTing one extra unknown field to every write endpoint defined in `specs/038-success-criteria/contracts/openapi.evidence-harness.yaml` and asserting HTTP 422 + ProblemDetails `title=request-body-extra-fields`. [FR-047, SC-022a, AMD-10, CHK125..CHK130]
- [X] T-AMD-20 [P] Add integration test `tests/integration/test_audit_immutability.py` issuing PATCH and DELETE against a known audit doc id and asserting HTTP 409 + ProblemDetails `title=audit-record-immutable`. [FR-040, SC-016, AMD-03, CHK073..CHK079, R1 Q2]
- [X] T-AMD-21 [P] Add integration test `tests/integration/test_audit_503_paths.py` covering (a) AU-region refusal with simulated audit-write failure → 503 `audit-write-unavailable`, and (b) `/healthz/evidence` returning 503 when a critical store (Cosmos / Blob / change-feed processor) is forced offline via fake-client injection. [FR-044, FR-045, SC-020a, SC-020b, AMD-07, AMD-08, CHK101..CHK114, R2 Q2]
- [X] T-AMD-22 [P] Add contract test `tests/contract/test_benchmark_seed_coverage.py` loading the seeded `benchmark_register` container and asserting ≥ 32 jurisdictional rows (8 jurisdictions × ≥ 4 categories) + ≥ 5 cross-sector rows + every non-manual row carries a non-null `CitationRef` + manual share ≤ 50 %. [FR-049, SC-022c, AMD-12, CHK135..CHK140]
- [X] T-AMD-23 [P] Add unit test `apps/api/tests/unit/test_clients_failfast.py` asserting that importing `apps.api.app.services.evidence._clients` with `AMA_TEST_MODE` unset and Azure env vars missing raises `RuntimeError` containing the literal substring `FR-042`; also verify the in-memory fallback IS taken when `AMA_TEST_MODE=1`. [FR-042, SC-018, AMD-05, CHK093..CHK096]

### Phase AMD-13: SRE — SLO workbook + alert deployment verification

- [X] T-AMD-24 Add `tests/infra/test_evidence_harness_whatif.ps1` running `az deployment group what-if` against `infra/bicep/modules/evidence-harness.bicep` with a fixture `sloAlertActionGroupId` and asserting the change-set contains: 1× workbook (`evidence-harness-slo`), 1× Sev1 burn-rate alert (5 %/h, 1h window), 1× Sev2 burn-rate alert (2 %/h, 1h window), and that omitting `sloAlertActionGroupId` causes the deployment to fail validation. [FR-046, SC-021, AMD-09, CHK115..CHK124, D23]

### Phase AMD-14: Polish

- [X] T-AMD-25 Run `pytest apps/api/tests tests/contract tests/integration`, `pnpm --filter @ama/web test:playwright`, and `az bicep build infra/bicep/modules/evidence-harness.bicep`; re-run constitution gate from `plan-amendments-cycle-2.md §Constitution Check`; commit all amendment work with `Co-authored-by: Copilot <copilot@github.com>` trailer; update `tasks.md` to mark each `T-AMD-*` `[X]` only after its target test/check is green. [AMD-13, CHK146..CHK152]

---

## Cycle 2 Amendment Summary

- **Total amendment tasks**: 25 (`T-AMD-01..T-AMD-25`).
- **Per amendment (AMD-01..AMD-13)**: AMD-01→T-AMD-01; AMD-02→T-AMD-14, T-AMD-17, T-AMD-18; AMD-03→T-AMD-04, T-AMD-06, T-AMD-20; AMD-04→T-AMD-11, T-AMD-16; AMD-05→T-AMD-08, T-AMD-23; AMD-06→T-AMD-02; AMD-07→T-AMD-05, T-AMD-21; AMD-08→T-AMD-07, T-AMD-21; AMD-09→T-AMD-03, T-AMD-24; AMD-10→T-AMD-09, T-AMD-10, T-AMD-19; AMD-11→T-AMD-13; AMD-12→T-AMD-12, T-AMD-22; AMD-13→T-AMD-15, T-AMD-25.
- **Parallel opportunities**: 14 tasks marked `[P]` (T-AMD-04..06, 09, 10, 15..23 in their respective phases).
- **Manual tasks**: 0 — all amendment tasks are auto-executable by `/speckit.implement`.
- **Dependency notes**: AMD-1 phase tasks (T-AMD-01..03) edit the same Bicep file → sequential. T-AMD-04 depends on T-AMD-01/02 for the IaC hosting the Container Apps job. T-AMD-09 should land before T-AMD-19 (extra-fields contract test). T-AMD-11 should land before T-AMD-16 (frontend renders the new required field). T-AMD-25 runs last.
- **Suggested execution order**: AMD-1 → AMD-2/3/4 in parallel → AMD-5/6/7/8/9 in parallel → AMD-10/11 → AMD-12/13 → AMD-14.

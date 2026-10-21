# Changelog

All notable changes to this repo are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/) once a `1.0.0` tag is cut.

## [Unreleased]

### Added (spec 036 — Cycle 5 amendment cycle)
- **`tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control`** — two case-insensitive absence assertions appended (`pks/<tenant_id>` and `partition path` via `.lower()` + plain `in`). F-TECH-4-01 regression guard against future re-paste of the Cycle 3 partition-path wording into the Bicep role-assignment comment block (A5-01 / F-TECH-4-01 / `spec.md:5656-5673`).

### Changed (spec 036 — Cycle 5 amendment cycle)
- **`infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`** — Bicep preamble rewrite consolidating with the Cycle 4 A4-02 sub-block at L317-327; four-clause ordering per Pass 1 Q1 (database-level scope → compensating defence-in-depth → joint enforcement → `[backlog issue: #84]`). Removes the stale Cycle 3 *"smoke-tenant partition path"* lead sentence and the illustrative `/colls/<container>/pks/<tenant_id>` resolution. The actual `scope:` expression at L328 (`scope: '${account.id}/dbs/${databaseName}'`) is byte-identical to the Cycle 4 baseline; runtime RBAC behaviour is unchanged (A5-01 / `spec.md:5067-5096`).
- **`tests/contract/test_smoke_tenant_isolation.py:173, 253`** — `test_bicep_comment_block_documents_compensating_control` prose disposition promoted OPTIONAL → REQUIRED per Pass 2 Q1; collapses the Cycle 4 Pass 2 Q4 minimal-3399 / FULL-3400 posture split into a single 3400 posture binding for all subsequent cycles. No `pytest.mark.*` decorator added or removed — the runtime disposition is unchanged (the test was already collected unconditionally at Cycle 4 close per `tasks.md:2527`) (A5-01 / `spec.md:5498-5586`).

### Added (spec 036 — Cycle 4 amendment cycle)
- **`tests/contract/test_sli_kql_runtime_validity.py`** — author-time KQL column-resolution-validity walker, parametric across Z1–Z7. The walker hard-fails on `union` and on any column reference that does not resolve to a base-table column (`requests`, `customEvents`, `customMetrics`, `traces`, `AuditEntries_CL`, `AzureDiagnostics`), an explicit `let`/`extend`/`summarize-LHS` binding, or a `customDimensions["…"]` lookup. Per PD-C4-01 (`specs/036-sim-agent-extend/plan.md:788-1010`), the walker is regex/lexer-based (no Kusto AST parser dependency); failure messages name the SLI id, the unresolved column, the pipe-clause line number, and the full canonicalised KQL. Strengthens FR-073 (A4-01 / `spec.md:3875-3895`).
- **GitHub backlog issue [#84](https://github.com/johnbilliris/ama/issues/84)** — Cosmos data-plane RBAC API 2024-08-15 partition-scope upgrade tracker for the `Simulation.Coordinator` role assignment (currently database-level — compensating defence-in-depth control). Filed via T-AA55; back-fills the placeholder in `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` and `infra/bicep/modules/cosmos-simulation-containers.bicep` (A4-02 / `spec.md:3896-3915`).

### Changed (spec 036 — Cycle 4 amendment cycle)
- **Z7 KQL — symmetric `extend model_deployment` line added** at `infra/observability/sli-kql.json` (Z7 entry `slis[6].kql`) and `specs/036-sim-agent-extend/contracts/sli-thresholds.md` §6b (between the existing `extend tenant_id` and `where env == "staging"` clauses). The pre-fix Z7 KQL referenced `model_deployment` in `summarize ... by model_deployment` without an upstream `extend` — Application Insights would have rejected the query at runtime (`SemanticError: Failed to resolve column reference 'model_deployment'`). The byte-equality contract test (`tests/contract/test_sli_kql_canonical_match.py`) missed the defect because both files drifted symmetrically; the new `test_sli_kql_runtime_validity.py` catches this class of defect (A4-01 / FR-073 strengthening / `spec.md:3875-3895`).
- **ADR-036-011:172-173 in-place wording revision** — three-clause acknowledgement that the `Simulation.Coordinator` role assignment is **database-level** (`scope: '${account.id}/dbs/${databaseName}'`) because the Cosmos data-plane RBAC API 2024-08-15 does not yet expose a `partitionKey` selector; the database-level scope is a **compensating defence-in-depth control** rather than a partition-level guarantee, with tenant isolation jointly enforced at the KQL query-time filter, the `customDimensions["tenant_id"]` envelope discriminator, and the Pass-1 Q2 isolation guarantees (i)–(v). The Cycle 4 amendment sub-section appended at L478+ by `/speckit.plan` is preserved verbatim (A4-02 / Pass-1 Q5 / `spec.md:3896-3915`).
- **`tests/contract/test_smoke_tenant_isolation.py` REQUIRED + OPTIONAL extensions** — REQUIRED: `test_smoke_role_assignment_scope_is_database_level` asserts the literal `scope: '${account.id}/dbs/${databaseName}'` in the Bicep render (per Pass-2 Q4 minimal posture +1 test; A4-02 / `spec.md:4679-4814`). OPTIONAL (FULL posture): `test_bicep_comment_block_documents_compensating_control` asserts the Bicep comment block at `infra/bicep/modules/cosmos-simulation-containers.bicep` documents both the *compensating defence-in-depth* wording AND the backlog issue identifier (A4-02 / `spec.md:3896-3915`).
- **`spec.md:961-966` mirror correction** — Cycle 3 Pass-1 Q2 isolation-guarantee item (v) wording mirror marked as superseded by A4-02 via in-place strikethrough annotation; cross-references the corrected ADR-036-011:172-173 wording. Four sibling lock-zone mirrors (`plan.md:682`, `tasks.md:1929`, `quality.md:367`, `quality.md:528`) are preserved verbatim per immutability discipline and known-stale per A4-02 supersession.

### Breaking changes (spec 036 — Cycle 2 amendment cycle)
- **OpenAPI v0.2.x → v0.3.0** — `TelemetryInjectionAck.triggered_sub_agents` items change from `string` to `TriggeredSubAgent` object `{correlation_id, dispatch_status, sub_agent, trigger_source}` (A2-01 / FR-067). Migration recipe in `specs/036-sim-agent-extend/contracts/openapi-changelog.md`.
- **OpenAPI v0.3.0** — `TelemetryInjectionAck.degraded_dispatch` (boolean) added as a required field (A2-04 / FR-068).
- **Audit-envelope `sub_agent` enum** — 7-kebab `{communication, evacuation, health, monitoring, logistics, operations, planning, resource-allocation, risk-assessment}` → 9-PascalCase `{Comms, Evac, Health, Intel, Logistics, Operations, Planning, Resource, Risk}` for new writes; historical kebab rows remain readable via the `_KEBAB_TO_PASCAL` shim in `apps/api/app/services/simulation/audit_writer.py` (A2-07).
- **Audit-envelope entry types** — 24 → 25 (NEW: `signal_pipeline.dispatch_failed` for the degraded-dispatch handler at `apps/api/app/api/routes/simulations_036.py:316-345`; previously a silent-swallow site) (A2-04 / FR-068).

### Added (spec 036 — Cycle 2 amendment cycle)
- **ADR-036-010** — Cycle 2 amendment cycle (hybrid OTel, degraded dispatch, Z6/Z7 SLIs) at `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md`.
- **Per-subscriber `correlation_id` + hybrid OTel TraceContext propagation** in the signal-pipeline orchestrator (`apps/api/app/services/simulation/signal_pipeline_orchestrator.py`); `SubscriberDispatchOutcome` dataclass surfaces `{acknowledged, failed, timed_out}` per subscriber (A2-01 / FR-067).
- **Degraded-dispatch handler** at `simulations_036.py:316-345` — replaces the Cycle 1 silent-swallow site; classifies per-subscriber outcomes, populates `triggered_sub_agents` with one entry per attempted subscriber (lex-sorted by PascalCase `sub_agent`), sets `degraded_dispatch=true`, writes exactly one `signal_pipeline.dispatch_failed` envelope per `injection_correlation_id`, returns HTTP 202 (A2-04 / FR-068).
- **5 s `DISPATCH_ACK_TIMEOUT_SECONDS`** constant + per-subscriber dispatch ack deadline (`apps/api/app/services/simulation/dispatch_status.py`) (A2-01 / FR-067).
- **RFC 8785 JCS byte-equality** between HTTP 202 body `triggered_sub_agents` array and `details.triggered_sub_agents` audit envelope array — CHK135 = highest-risk checklist item (A2-04).
- **Z6 SLI** — P95 sub-agent reply latency, partitioned by model (`gpt-4o` warn=4000 ms / breach=5000 ms; gpt-4o-mini warn=1500 ms / breach=2000 ms); KQL in `infra/observability/sli-kql.json` with `sample_count` column (A2-02 / FR-069).
- **Z7 SLI** — map-overlay drift error budget (alert when `drift_budget_pct < 99.5 %`); inverse semantics handled in `tests/staging_gates.py::assert_sli_thresholds()`.
- **`MIN_SAMPLES_PER_SLI_24H = 30`** sample-floor constant in `tests/staging_gates.py`; staging promotion fails closed (`StagingPromotionRefused`) if any SLI has <30 samples in the 24 h window (A2-02 / FR-069).
- **Bicep alerts + Azure Monitor workbook** for Z6 + Z7 (`infra/bicep/modules/observability-alerts.bicep`, `infra/bicep/modules/observability-workbook-sim-slis.bicep`) (A2-02 / FR-069).
- **Synthetic smoke-injection release-gate exercise** — runs in `tnt-stg-smoke` tenant as `Simulation.Coordinator`, 5 categories × 8 events ≥ 40 floor; mitigates CHK117 / CHK137.
- **`SPEC_036_PROBLEM_JSON_ROUTES` allow-list** + middleware (`apps/api/app/middleware/spec_036_routes.py`) — 5 routes emit RFC 9457 problem+json on 4xx + 5xx (A2-05).
- **`contracts/openapi-changelog.md`** — durable migration ledger for OpenAPI version bumps; v0.3.0 is the first row (A2-08).
- **`evacuation` cascade alias** + `_MATRIX_TO_ROLE` (PascalCase→kebab-case) translation in `cascade_orchestrator.py` (A2-03).

### Changed (spec 036 — Cycle 2 amendment cycle)
- **Cascade fan-out** — single source of truth is now `CASCADE_MATRIX` (`packages/domain/src/domain/sim_cascade_matrix.py`); `apps/api/app/config/cascade_rules.yaml` `fan_out_rules:` block REMOVED. Build-time guard at `tests/contract/test_cascade_yaml_no_fan_out_rules.py` fails on regression (A2-03 / FR-070).
- **Allocator-only `sequence_number`** — `apps/api/app/services/simulation/audit_writer.py` now drops any caller-supplied `sequence_number` from the `details` dict and emits a WARNING log; allocator-assigned value is injected for the schemas that declare `sequence_number` in their required list (A2-06 / FR-048 strengthened).
- **Removed** placeholder `"sequence_number": 1` literal at `cascade_orchestrator.py:225-235` (A2-06).

### Added (spec 036 — Microsoft Foundry-Based RAG Grounding)
- Microsoft-Foundry-based retrieval grounding seam (`apps/agents/common/foundry_chat_client.py`, `apps/agents/maf_runtime/chat_client.py`, `apps/api/app/services/simulation/controller_service.py`) — every prompt-bearing call site retrieves before inference; AAD-only auth via `https://cognitiveservices.azure.com/.default` (FR-RAG-FM-01..07).
- Carve-out enforcement (`infra/parameters/foundry-carveout.{yaml,schema.json}` + `scripts/verify-carveout.ps1`) — every Foundry deployment is gated through the registry per Constitution §NN-2 Amendment 1.2.0; data-plane resources stay in AU East / AU Southeast (FR-RAG-CV-01..04).
- Corpus ingest container job (`apps/ingest-runner/`) wired into `azd postprovision` with idempotent re-run skip on unchanged entries (FR-RAG-IDX-01..05, SC-005).
- Blue-green AI Search index lifecycle (`infra/modules/ai-search-blue-green.bicep` + alias `corpus-search` over `corpus-v{N}` ↔ `corpus-v{N+1}`) with <60 s alias flip (FR-RAG-IDX-04).
- Shared `RetrievalService` port + `Citation` envelope + `AuditRecord` extensions (`packages/domain/src/ama_domain/`) — citations on every recommendation card and SSE turn; audit carries `retrieved_chunks[]`, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `rag_used`, `rag_optout_reason`, `gateway_decision` (FR-RAG-AG-01..06).
- `EquivalenceTestResult` entity (`packages/domain/src/ama_domain/equivalence_test_result.py`, T143) — extends spec-033 FR-023 shape with `citation_fidelity`, `verbatim_source_match`, `corpus_build_sha`, `embedding_model_id`.
- Final canary gate (`apps/eval-runner/src/ama_eval/per_agent_canary_gate.run_final_canary_gate`, T142) — decision-equivalence ≥ 95 % AND schema-equivalence == 100 % AND citation-fidelity ≥ 0.7 AND verbatim-source-match ≥ 0.9, keyed by `(corpus_build_sha, embedding_model_id)` (FR-RAG-FM-06, SC-011).
- Compliance audit byte-replay automation (`tests/audit/audit_replay_fidelity.kql` + `tests/contract/test_audit_replay_fidelity.py`, T144) — sampled SC-011 ≥ 95 % reproduction across one-month rolling window with KQL alert on dip.
- Dual-signed offline cache bundle for Field-Coordinator-aligned devices (`apps/ingest-runner/src/ama_ingest/offline_bundle.py` + `infra/scripts/verify-offline-cache.ps1`) with cosign keyless + age detached signatures, 14-day TTL, 11-day stale warning, fail-closed signature checks (FR-RAG-LS-02, R-07).
- Nine RAG-OPTOUT carve-outs (`# RAG-OPTOUT [FR-RAG-NS-NN]` markers + ADR files under `docs/decisions/036-foundry-rag-grounding/`) with CI lint at `tools/lint/check_rag_optout_bindings.py` blocking new opt-outs without ADR (FR-RAG-NS-01..09).
- 50-query multi-jurisdiction golden set (`apps/eval-runner/fixtures/spec036/multi_jurisdiction.jsonl`) covering ACT/NSW/NT/QLD/SA/TAS/VIC/WA/national/AIDR jurisdiction-disambiguated retrieval.
- Game-day runbook (`docs/runbooks/036-foundry-rag-gameday.md`) + Step-9 cutover runbook (`docs/runbooks/036-foundry-rag-step9-cutover.md`) + Simulation final-canary dry-run script (`infra/scripts/simulation-final-canary-dry-run.ps1`) + post-`azd up` smoke-test (`infra/scripts/azd-up-smoke-test.ps1`).
- Application Insights alerts module (`infra/bicep/modules/foundry-rag-cutover-alerts.bicep`) — gateway-deny, citation-drop, offline-cache-TTL (Alert 3 / equivalence-regression retired in ADR-20 §Q-P6-03 cleanup; audit-replay-fidelity covered by `tests/audit/audit_replay_fidelity.kql` outside this module).

### Changed (spec 036)
- All five decision agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) plus Simulation Controller chat (spec 024) migrated from Azure OpenAI to Microsoft Foundry behind the spec-029 progressive-delivery feature flag `FOUNDRY_RAG_ENABLED_AGENTS`.
- `apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py`, and `apps/api/app/services/simulation/controller_service.py` invoke the Foundry seam exclusively; AAD-only auth (FR-RAG-FM-04). The legacy `AZURE_OPENAI_*` env-var seam is retained only as a hermetic-test fallback and is no longer set by production Bicep (ADR-20 §Q-P6-03).
- Citation cards on every operator surface (`packages/ui/CitationCard.tsx`) + Simulation SSE stream emits `event: citation` per grounded turn with the `licence_mode`-aware snippet rule (R-11).

### Removed (spec 036, ADR-20 §Q-P6-03 — post-cutover cleanup)
- `AZURE_OPENAI_ENDPOINT` env-var compatibility seam — `infra/main.bicep`, `infra/modules/communication-agent.bicep`, and root `.env.example` no longer reference the legacy var; Foundry callers consume `AZURE_AI_PROJECT_ENDPOINT` exclusively.
- `LEGACY_AZURE_OPENAI=1` rollback escape hatch — the flag is removed from all production code paths; `apps/eval-runner/src/ama_eval/per_agent_canary_gate.py` is preserved as the corpus-rebuild regression gate (decision-equivalence ≥ 0.95, schema-equivalence == 1.0, citation-fidelity ≥ 1.0) keyed by `(corpus_build_sha, embedding_model_id)`.
- Per-agent canary equivalence-regression telemetry — Alert 3 in `infra/bicep/modules/foundry-rag-cutover-alerts.bicep` (`decision_equivalence` custom dimension) was retired; the file now ships three alerts (gateway-deny, citation-drop, offline-cache-TTL).
- `pytest.mark.skip` on `tests/contract/test_no_openai_imports.py` — the FR-RAG-FM-04 lint is **binding**: any `from openai import AzureOpenAI` / `AsyncAzureOpenAI` in `apps/` (outside the eval-runner allowlist) fails CI unless the import carries an inline `# noqa: AMA-FM04` marker with a spec-reference comment.

### Deprecated (spec 036)
- Legacy `from openai import AzureOpenAI` / `AsyncAzureOpenAI` import path in `apps/agents/common/llm_client.py` and `apps/agents/maf_runtime/chat_client.py` — fully removed from production code paths; preserved only as a hermetic-test fallback inside `_init_legacy_client` and via `# noqa: AMA-FM04` markers in modules that use the OpenAI SDK as an OpenAI-compatible transport to Foundry embeddings (`apps/agents/common/foundry_query_embedder.py`, `apps/ingest-runner/src/ama_ingest/embedder.py`, `apps/api/app/services/simulation/controller_service.py`). `tests/contract/test_no_openai_imports.py` is now a binding lint.
- `infra/modules/azure-openai.bicep` — deprecation header added in Phase B; the module continues to provision Foundry (AIServices) model deployments via the unchanged Cognitive Services deployment resource type, no rename pending.

### Added (spec 035 — Webapp capstone closure)
- 9 operator panels (FR-001..FR-008): IC approval card (T036), AWS warning composer (T037), audit timeline (T038), risk matrix (T039), planning IAP (T042), span-of-control warning (T043), field-coordinator offline (T041), resilience handover-PDF (T044), classifier-mask banner (T046).
- 13 sector workspaces under `apps/web/src/app/(operations)/sectors/` covering FR-014..FR-024 / FR-029 across SAPOL, SES SA, DFES WA (cultural-safety + iron-ore-haul), AT TAS island isolation, TasPol multilingual, AFP ACT precinct, SES ACT, NTES multilingual, SJA NT tropical, BoM broadcast, NEMA DACC JATWC, and the utility/insurance recovery sector.
- Cultural-safety subsystem (T053, FR-016, NN-4): elder-routing + 90-second-timeout decision service with closed-set outcomes `cultural_safety_timeout_override` / `cultural_safety_held` and AWS-level allowlist for IC overrides.
- Language pack registry (T050, NN-4 v1 baseline): Simplified Chinese + 5 ATSI community packs with reviewer-required fallback chain, wired into the PIO composer (T073).
- Recovery dashboard extension (T063..T065, FR-024 + SC-005): claims-velocity dashboard, FR-024 built/economic recovery environments, Sendai counterfactual ratio + threshold warning, claims-velocity dollars-paid / dollars-lodged timeline.
- US-3 reusable subsystems (T050..T052): cultural-safety panel, infrastructure overlay (iron-ore haul road, port critical, island logistics, federal precinct), claims-velocity dashboard.
- Cross-cutting horizontals (US-5): SovereigntyBanner with carve-out badge (T069), Foundry carve-out registry (T070, FR-029) + 90-day CI review gate (T071, `.github/workflows/foundry-carveout-review.yml`), generalised offline subsystem registration via `(operations)/layout.tsx` (T072), multilingual fallback chain wiring (T073).
- Audit observability (T078): `ama.audit.outcome` OTEL span attribute helper in `apps/api/app/observability/audit_span.py`, emitted by the cultural-safety service so every closed-set outcome is searchable in Application Insights.
- Architecture diagrams (T079): middleware stack + offline-replay flow in `docs/architecture/spec-035-middleware-and-offline.md`.

### Added (spec 032 — Rubric Improvements, in progress)
- 9-step speckit orchestration artefacts under `specs/032-rubric-improvements/` (spec, plan, research, data-model, quickstart, contracts, two checklists, tasks, analysis).
- `.pre-commit-config.yaml` with ruff/mypy/import-linter/gitleaks/bicep-lint hooks (FR-Q04, T001).
- `tests/README.md` describing each test tier (FR-T06, T002).
- `CONTRIBUTING.md` covering branch model + spec-driven workflow (FR-DOC04, T003).
- `CHANGELOG.md` (this file) (FR-DOC05, T004).
- `.github/dependabot.yml` weekly updates for Dockerfiles + GitHub Actions (FR-D02, T005).

### Changed
- README agent table to include `dependency-notifier` as a first-class agent (FR-AG04, T010).

## [Earlier history]

See `git log` and `specs/*/spec.md` for prior feature deliveries (specs 001–031).

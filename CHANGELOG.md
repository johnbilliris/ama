# Changelog

All notable changes to this repo are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/) once a `1.0.0` tag is cut.

## [Unreleased]

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
- Application Insights alerts module (`infra/bicep/modules/foundry-rag-cutover-alerts.bicep`) — gateway-deny, citation-drop, equivalence-regression, offline-cache-TTL, audit-replay-fidelity.

### Changed (spec 036)
- All five decision agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) plus Simulation Controller chat (spec 024) migrated from Azure OpenAI to Microsoft Foundry behind the spec-029 progressive-delivery feature flag `FOUNDRY_RAG_ENABLED_AGENTS`.
- `apps/agents/common/llm_client.py` and `apps/agents/maf_runtime/chat_client.py` and `apps/api/app/services/simulation/controller_service.py` now invoke the Foundry seam by default and fall back to the legacy Azure-OpenAI client only when `LEGACY_AZURE_OPENAI=1` (rollback hatch retained until T146 atomic-deletion PR merges).
- Citation cards on every operator surface (`packages/ui/CitationCard.tsx`) + Simulation SSE stream emits `event: citation` per grounded turn with the `licence_mode`-aware snippet rule (R-11).

### Deprecated (spec 036)
- Legacy `from openai import AzureOpenAI` / `AsyncAzureOpenAI` import path in `apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py`, `apps/api/app/services/simulation/controller_service.py` — removal pending T146 atomic-deletion PR (`036-legacy-deletion` branch). The `pytest.mark.skip` on `tests/contract/test_no_openai_imports.py` is removed atomically with the legacy-client deletion.
- `infra/modules/azure-openai.bicep` — deprecation header added in Phase B; relocated to `infra/modules/legacy/` by T146.
- `LEGACY_AZURE_OPENAI=1` escape hatch — dropped by T146 once Simulation final canary (T145) is green.

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

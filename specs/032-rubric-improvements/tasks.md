# Tasks: AMA Rubric Improvements (032)

**Feature**: 75-item rubric uplift to Excellent (5).
**Branch**: `032-rubric-improvements`
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Research**: [research.md](./research.md)
**Cross-stream prerequisites**: see `plan.md` "Cross-stream hard dependencies".

> Notation: `[P]` = parallelisable with peers in the same phase. `[BLOCKS:Tnnn]` = downstream tasks blocked. `[ML]` = must-land for correctness/security in this feature; `[EV]` = evidence/maturity, may slip to a follow-up PR per the Top-5 schedule-risk split in `plan.md`. Each task lists target files.

## Phase 1 — Setup (T001–T010)

- [X] **T001** [P] Add `.pre-commit-config.yaml` mirroring CI gates (ruff lint+format, mypy, import-linter, gitleaks, bicep-lint). [→ FR-Q04] · `/.pre-commit-config.yaml`
- [X] **T002** [P] Create `tests/README.md` describing each tier (unit, integration, contract, simulation, benchmark, devops, e2e, load, chaos, security) with run command + expected runtime. [→ FR-T06] · `/tests/README.md`
- [X] **T003** [P] Create `CONTRIBUTING.md` covering env-branch model + spec-driven workflow. [→ FR-DOC04] · `/CONTRIBUTING.md`
- [X] **T004** [P] Create `CHANGELOG.md` (Keep-a-Changelog format) seeded with the 032 entry. [→ FR-DOC05] · `/CHANGELOG.md`
- [X] **T005** [P] Add `.github/dependabot.yml` group for Dockerfiles + GitHub Actions weekly. [→ FR-D02] · `/.github/dependabot.yml`
- [X] **T006** Promote spec 030 status from Draft → Approved (via PR comment evidence + status edit in spec 030's spec.md). [→ FR-I01] · `/specs/030-llm-eval-framework/spec.md`
- [X] **T007** Verify spec 031 status — this feature DOES NOT modify spec 031; just records the dependency state. [→ FR-C01 (verify), cross-stream prereq] · `/specs/032-rubric-improvements/plan.md` (verify checkbox)
- [X] **T008** [P] Resolve placeholder Entra group object IDs in `IDENTITY.md`, `setup-oidc-azure.yml`, `identity_consistency.rego` (real IDs OR env-resolved variables). [→ FR-I05] · `/infra/IDENTITY.md`, `/.github/actions/setup-oidc-azure/action.yml`, `/infra/policy/rego/identity_consistency.rego`
- [X] **T009** [P] Create checklist folders for downstream specs (placeholder for traceability matrix). [→ FR-T07] · `/specs/032-rubric-improvements/traceability.md`
- [X] **T010** Update root `README.md` agent table to include `dependency-notifier` as first-class. [→ FR-AG04] · `/README.md`

## Phase 2 — Foundation (T011–T030)

ADRs and spikes that gate downstream work. **Stream 0**.

- [X] **T011** Author **ADR-032** — OIDC supersession of ADR-031: status, decision, consequences, two-stage migration plan. [→ FR-S02a] · `/docs/aidr/decisions/adr-032-oidc-supersession.md`
- [X] **T012** Author **ADR-033** — Phi shadow boundary + classification-aware filter (PII + PSPF + sensitive-operational). [→ FR-AI03, NN-2] · `/docs/aidr/decisions/adr-033-phi-shadow-boundary.md`
- [X] **T013** Author **ADR-034** — Adopt `pybreaker` (replace hand-rolled circuit breaker). [→ FR-P03] · `/docs/aidr/decisions/adr-034-pybreaker-adoption.md`
- [X] **T014** Author **ADR-035** — Cosign keyless prompt-artifact signing. [→ FR-AI09] · `/docs/aidr/decisions/adr-035-cosign-keyless-prompts.md`
- [X] **T015** Author **ADR-036** — Azure AI Search S1 RAG over docs/aidr/. [→ FR-AI01] · `/docs/aidr/decisions/adr-036-aisearch-rag.md`
- [X] **T016** **Kill-switch propagation spike** — prototype Cosmos change-feed → Service Bus topic → agent watcher; measure end-to-end latency over 100 toggles; confirm ≤ 30 s P99 OR document new SLO. [→ FR-AG05, blocks T201–T204] · `/docs/spikes/T016-killswitch-propagation.md` + scratch code
- [X] **T017** Create Foundry **carve-out registry skeleton** + JSON schema. [→ FR-AI03a, NN-2] · `/infra/parameters/foundry-carveout.yaml` + `/infra/parameters/foundry-carveout.schema.json`
- [X] **T018** Add CD validator: refuse to deploy any model deployment absent from carve-out registry. [→ FR-AI03a] · `/.github/workflows/cd.yml` step + `/scripts/verify-carveout.ps1`
- [X] **T019** Create classification taxonomy doc (PII / PSPF-marked / sensitive-operational). [→ FR-AI03] · `/docs/safety/classification-taxonomy.md`
- [X] **T020** Create `/docs/governance-hub/index.md` consolidated nav stub linking the three existing hubs. [→ FR-DOC03] · `/docs/governance-hub/index.md`
- [X] **T021** Create C4 system + container diagrams seed (PlantUML/Structurizr-style Markdown). [→ FR-A01] · `/docs/architecture/c4/system.md`, `/docs/architecture/c4/container.md`
- [X] **T022** Create Cosmos partitioning math doc + per-tenant RU budget table. [→ FR-A02] · `/docs/architecture/cosmos-partitioning.md`
- [X] **T023** Create per-agent scale-out targets section in main.bicep header comment + module references. [→ FR-A03] · `/infra/main.bicep`
- [X] **T024** Create Monitoring → Risk Assessment → Communication sequence diagram (Mermaid `sequenceDiagram`) including dead-letter + recovery cycles. [→ FR-A04] · `/docs/architecture/sequence/monitoring-risk-comms.md`
- [X] **T025** Create `slo.md` with the SLI catalogue per FR-O06 + error budgets + paging severity. [→ FR-O06, FR-O09] · `/docs/observability/slo.md`
- [X] **T026** Create `metrics-catalogue.md` listing every customMetric per data-model.md E-07. [→ FR-O02] · `/docs/observability/metrics-catalogue.md`
- [X] **T027** Create decision-rights matrix doc (per agent: decide vs escalate). [→ FR-AG01] · `/docs/agents/decision-rights.md`
- [X] **T028** Create prompt library README + cosign manifest. [→ FR-AI05] · `/packages/prompts/README.md`, `/packages/prompts/cosign.manifest.yaml`
- [X] **T029** Create `INDEXING-LICENCE-NOTE.md` + `LICENCE-INVENTORY.md` (per-handbook table; default to metadata-only until Compliance + SA sign-off). [→ FR-AI01] · `/docs/aidr/INDEXING-LICENCE-NOTE.md`, `/docs/aidr/LICENCE-INVENTORY.md`
- [X] **T030** Create exercise-schedule doc (quarterly LLM rehearsal + biannual chaos). [→ FR-D05] · `/docs/disaster-response-hub/evaluation/exercise-schedule.md`

## Phase 3 — User Story 7 (Hygiene) — Stream 1 (T101–T120)

**Goal**: CI enforces strict typing, import boundaries, formatting, ratcheting coverage, secret scan, SHA-pinning. **Independent test**: introduce deliberate violations of each gate; CI fails on each.

- [X] **T101** [P] Add `mypy.ini` strict configuration. [→ FR-Q01] · `/mypy.ini`
- [X] **T102** [P] Add `import-linter` config in `pyproject.toml` with the `agents MUST NOT import api` rule + extension hook for further rules. [→ FR-Q02] · `/pyproject.toml`
- [X] **T103** [P] Add `ruff format --check` step to `ci.yml`. [→ FR-Q03] · `/.github/workflows/ci.yml`
- **T104** [P] Run `ruff format` once across the repo to absorb baseline. [→ FR-Q03] · `apps/`, `packages/`, `tests/`
- [X] **T105** Add `mypy --strict` step to `ci.yml`. [→ FR-Q01] · `/.github/workflows/ci.yml`
- [X] **T106** Add `import-linter` step to `ci.yml`. [→ FR-Q02] · `/.github/workflows/ci.yml`
- [X] **T107** Add `pytest --cov` ratcheting Phase A enforcement (no regression vs prior run). [→ FR-T01 Phase A] · `/.github/workflows/ci.yml` + `/scripts/coverage-ratchet.ps1`
- [X] **T108** Add CodeQL workflow (Python + JavaScript/TypeScript). [→ FR-S03] · `/.github/workflows/codeql.yml`
- [X] **T109** Add `.github/workflows/security-scan.yml` with PSRule for Bicep + gitleaks. [→ FR-T04, FR-S03] · `/.github/workflows/security-scan.yml`
- [X] **T110** SHA-pin sweep: replace every `uses:` tag reference with the equivalent commit SHA across all workflows + actions. [→ FR-C03] · `/.github/workflows/*.yml`, `/.github/actions/*/action.yml`

## Phase 4 — Stream 2 — agents/common refactor (T201–T220)

- [X] **T201** Create `apps/agents/common/resilience/` with re-exports for `circuit_breaker`, `retry`, `dead_letter`, `handoff_retry`. [→ FR-A05/Q05] · `/apps/agents/common/resilience/__init__.py` etc.
- [X] **T202** Create `apps/agents/common/safety/` with `content_safety`, `redaction`, `prompt_validator`, **`classification`** (NEW per critique). [→ FR-A05/Q05, FR-AI03] · `/apps/agents/common/safety/__init__.py` etc.
- [X] **T203** Create `apps/agents/common/lifecycle/` with `heartbeat`, `killswitch`, `autonomy_eval`, `degraded_mode`. [→ FR-A05/Q05, FR-AG02, FR-AG05] · `/apps/agents/common/lifecycle/__init__.py` etc.
- **T204** Move + re-export the 18 existing modules; preserve compat shim. Run full unit + integration tests. [→ FR-A05] · `/apps/agents/common/`
- [X] **T205** Implement `LlmFallbackStrategy` (Strategy pattern) — abstract base + `PrimaryStrategy`, `SecondaryStrategy`, `TemplateFallbackStrategy`. Wire into `_generate_with_fallback`. [→ FR-P01] · `/apps/agents/common/safety/` and `/apps/agents/llm/strategies.py`
- [X] **T206** Replace circuit breaker with `pybreaker` behind existing `CircuitBreaker` Protocol. [→ FR-P03] · `/apps/agents/common/resilience/circuit_breaker.py`
- [X] **T207** Externalise budget tracker to Cosmos container `llm_budgets` (PK `/scope`). [→ FR-P02] · `/apps/agents/llm/budget_tracker.py`
- [X] **T208** Promote AIIMS_MAPPING to typed registry with per-jurisdiction overrides. [→ FR-P05] · `/apps/agents/aiims_mapping.py` → `/apps/agents/aiims_registry.py`
- [X] **T209** Implement classification-aware sensitive-content filter for the model gateway + Phi shadow gate. [→ FR-AI03, NN-2] · `/apps/agents/common/safety/classification.py`

## Phase 5 — User Story 1 (Audit, provenance, integrity) — Stream 3 (T301–T330)

**Goal**: every recommendation carries full provenance; audit ledger has cryptographic continuity; integrity-check runs on demand.

- **T301** Add `RecommendationProvenance` Pydantic model (E-01 fields). [→ FR-AI02, US1] · `/packages/domain/src/domain/models/recommendation.py`
- **T302** Add `RagCitation` model (E-02). [→ FR-AI01] · `/packages/domain/src/domain/models/rag_citation.py`
- **T303** Add `AuditSegment` model + repository (E-03) with hash chain. [→ US1] · `/packages/domain/src/domain/models/audit_segment.py`, `/apps/api/app/repositories/audit_segment_repository.py`
- **T304** Implement segment hashing (SHA-256 over canonical JSON + prev_segment_hash). [→ US1] · `/apps/api/app/services/audit_integrity_service.py`
- **T305** Add integrity-check job runner. [→ US1] · `/apps/api/app/jobs/audit_integrity_job.py` + Cron in Container Apps
- **T306** Add `GET /api/health/audit-integrity` endpoint per contracts/openapi-delta.yaml. [→ US1] · `/apps/api/app/api/routes/health.py`
- **T307** Add `GET /api/recommendations/{id}/why-fired` endpoint. [→ US1] · `/apps/api/app/api/routes/recommendations_provenance.py`
- **T308** Wire prompt SHA + model version + deployment alias capture into `_generate_with_fallback` path. [→ FR-AI02] · `/apps/agents/llm/llm_client.py`
- **T309** Implement PII hash-redaction validator (deny by default; allow-list). [→ FR-O05] · `/apps/api/app/middleware/pii_redaction_validator.py` + `/scripts/pii-canary-scan.ps1`
- **T310** Add "why fired" panel React component + page. [→ US1] · `/apps/web/src/components/recommendations/WhyFiredPanel.tsx`, `/apps/web/src/app/recommendations/[id]/why-fired/page.tsx`
- **T311** Saga / Process Manager doc for the multi-agent approval workflow. [→ FR-P04] · `/docs/agents/saga-approval-workflow.md`

## Phase 6 — User Story 2 (Security & sovereignty) — Stream 4 (T401–T440)

**Goal**: 100% of probes from public networks rejected on data planes; CodeQL + Defender + Sentinel green; OIDC re-introduced.

- [X] **T401** Bicep: Cosmos Private Endpoint + private DNS + `publicNetworkAccess=Disabled` for production. [→ FR-S01, FR-C05] · `/infra/main.bicep`, `/infra/modules/private-endpoints.bicep`
- [X] **T402** Bicep: Cosmos CMK encryption with Key Vault Premium HSM key + Azure Policy rotation 90d. [→ FR-S05] · `/infra/main.bicep`, `/infra/modules/cosmos-cmk.bicep`
- [X] **T403** Bicep: Storage CMK + Private Endpoint. [→ FR-S05, FR-S01] · `/infra/modules/storage.bicep`
- [X] **T404** Bicep: AOAI Private Endpoint + private DNS + public access disabled. [→ FR-AI06] · `/infra/modules/azure-openai.bicep`
- [X] **T405** Bicep: **AI Content Safety Private Endpoint** + private DNS. [→ FR-AI06] · `/infra/modules/content-safety.bicep`
- [X] **T406** Bicep: **Azure AI Search Private Endpoint** + private DNS. [→ FR-AI01, FR-AI06] · `/infra/modules/ai-search.bicep`
- [X] **T407** Bicep: Defender for Cloud Standard tier on AKS/Container Apps/Cosmos/Storage/Key Vault/ACR/AI services. [→ FR-S04] · `/infra/modules/defender.bicep`
- [X] **T408** [ML] Bicep: Microsoft Sentinel onto existing Log Analytics workspace + 2 priority analytics rules (`KeyVaultAnomalousAccess`, `CosmosFirewallChange`). Must-land subset per Top-5 split; full rule set is `[EV]`. [→ FR-S04] · `/infra/modules/sentinel.bicep`
- **T409** OPA: `autonomy_dial.rego` policy. [→ FR-AG02] · `/infra/policies/autonomy_dial.rego`
- **T410** OPA: `killswitch.rego` policy. [→ FR-AG05] · `/infra/policies/killswitch.rego`
- **T411** OPA: `prompt_signing.rego` policy. [→ FR-AI09] · `/infra/policies/prompt_signing.rego`
- **T412** OPA: `foundry_carveout.rego` policy + CI hook validates `infra/parameters/foundry-carveout.yaml`. [→ FR-AI03a, NN-2] · `/infra/policies/foundry_carveout.rego`
- **T413** [ML] ADR-032 Stage-2 OIDC migration — dev environment only (BLOCKED until spec 031 prereq met). [→ FR-S02b] · `/.github/actions/setup-oidc-azure/action.yml`, `/.github/workflows/cd.yml`
- **T414** [EV] Stage-2 staging migration (BLOCKED until 7-day dev soak passes). [→ FR-S02b] · same
- **T415** [EV] Stage-2 production migration (BLOCKED until 7-day staging soak passes). [→ FR-S02b] · same
- **T416** Probe job: synthetic public-IP probe of Cosmos / Storage / AOAI / Content Safety / AI Search; assert all reject; results to App Insights. [→ US2 acceptance] · `/.github/workflows/public-network-probe.yml`

## Phase 7 — User Story 3 (Observability + SLOs) — Stream 5 (T501–T540)

**Goal**: SLO dashboard live; OTel traces end-to-end; synthetic probes green; PII redaction enforced.

- [X] **T501** Add `azure-monitor-opentelemetry` dependency to `apps/api`, `apps/agents`, `apps/ingestion`, `apps/eval-runner`. [→ FR-O07] · `pyproject.toml` per app
- [X] **T502** Add OTel bootstrap module per app (single import, configures resource attributes per contracts/otel-attributes.yaml). [→ FR-O07] · `/apps/{api,agents,ingestion,eval-runner}/observability/otel.py`
- **T503** Add OTel attribute-injecting middleware (FastAPI). [→ FR-O07] · `/apps/api/app/middleware/otel_middleware.py`
- **T504** Add OTel span attributes for LLM calls, handoffs, audit segments per contracts. [→ FR-O07] · `/apps/agents/llm/llm_client.py`, `/apps/agents/common/resilience/handoff_retry.py`
- **T505** Bicep: per-tier retention split (audit / operational / security / eval) with separate Log Analytics tables OR retention overrides. [→ FR-O01] · `/infra/modules/monitoring.bicep`
- **T506** Bicep: Action Group with paging severity routing P1–P5. [→ FR-O09] · `/infra/modules/monitoring.bicep`
- [X] **T507** [ML] Bicep: App Insights availability tests — 1 endpoint × 5 locations (must-land subset). Full 4-endpoint × 5-location matrix is `[EV]`. [→ FR-O10] · `/infra/modules/availability-tests.bicep`
- [X] **T508** [ML] Bicep: Workbook JSON — Executive Governance Health (must-land subset). [→ FR-O04] · `/infra/modules/workbooks/executive-governance.json`
- [X] **T509** [EV] Bicep: Workbook JSON — LLM Cost Burn-down (evidence). [→ FR-O04] · `/infra/modules/workbooks/llm-cost.json`
- **T510** [EV] Bicep: Workbook JSON — Agent Flow + Dead-Letter (evidence). [→ FR-O04, FR-O08] · `/infra/modules/workbooks/agent-flow.json`
- **T511** Implement `MetricDefinition` registry + customMetric emitter for token cost, dead-letter depth, killswitch lag. [→ FR-O02, FR-O03] · `/apps/api/app/observability/metrics.py`
- **T512** Wire `llm.cost.aud_micros` + `llm.budget.warning` customMetrics. [→ FR-O03] · `/apps/agents/llm/llm_mixin.py`

## Phase 8 — User Story 4 (AI quality) — Stream 6 (T601–T640)

- **T601** Bicep: Azure AI Search S1 (prod) / Basic (dev/staging) AU East — depends on T406 PE wiring. [→ FR-AI01] · `/infra/modules/ai-search.bicep`
- **T602** Embedding ingestion job for `docs/aidr/` (gated to handbooks with positive licence inventory). [→ FR-AI01] · `/apps/eval-runner/scripts/aidr_index_ingest.py`
- [X] **T603** `RagService` retrieval API (hybrid BM25 + vector). [→ FR-AI01] · `/apps/api/app/services/rag_service.py`
- **T604** Citation injection in prompts; recommendation card displays handbook + page. [→ FR-AI01, FR-AI02] · `/apps/agents/llm/strategies.py`, `/apps/web/src/components/recommendations/RecommendationCard.tsx`
- **T605** Prompt registry under `packages/prompts/` with semver folders + cosign manifest. [→ FR-AI05] · `/packages/prompts/`
- [X] **T606** Cosign keyless sign workflow `.github/workflows/prompts-publish.yml`. [→ FR-AI09] · `/.github/workflows/prompts-publish.yml`
- **T607** Cosign verify step in `cd.yml`. [→ FR-AI09] · `/.github/workflows/cd.yml`
- **T608** Phi shadow path in `apps/eval-runner` writing `shadow=true` recommendations to Cosmos (BLOCKED until T209 + T017 + T018 land). [→ FR-AI03] · `/apps/eval-runner/shadow.py`
- **T609** Structured-output validation enforcement: scan all `_generate_with_fallback` call sites; fail any without `response_model`. [→ FR-AI04] · ruff custom rule + `/scripts/validate-structured-output.ps1`
- **T610** Eval-baseline gates wired to CI (PR check fails any below-threshold change). [→ FR-T09 + spec 030] · `/.github/workflows/eval-pr-gate.yml`
- **T611** [ML] Publish v1 5,000-case dataset subset gating CI (must-land); track ramp to 5,000 in `eval-dataset/v1/manifest.json`. Full 5,000 cases is `[EV]` (evidence; may slip per Top-5 split). [→ FR-I02] · `/eval-dataset/v1/`

## Phase 9 — User Story 5 (Multi-agent maturity) — Stream 7 (T701–T740)

- [X] **T701** `JurisdictionPolicy` Cosmos container + repository. [→ FR-AG02] · `/apps/api/app/repositories/jurisdiction_policy_repository.py`
- [X] **T702** YAML loader for `infra/parameters/jurisdiction-policies/*.yaml` → Cosmos at deploy. [→ FR-AG02] · `/scripts/load-jurisdiction-policies.py`
- [X] **T703** `AutonomyDial` service consumed by every agent decision gate. [→ FR-AG02] · `/apps/agents/common/lifecycle/autonomy_eval.py`
- [X] **T704** `KillSwitch` Cosmos container + change-feed publisher → Service Bus topic (per T016 spike). [→ FR-AG05] · `/apps/api/app/repositories/killswitch_repository.py` + `/apps/api/app/jobs/killswitch_publisher.py`
- **T705** Agent-side kill-switch watcher (Service Bus subscription) with in-flight handoff drain. [→ FR-AG05] · `/apps/agents/common/lifecycle/killswitch.py`
- [X] **T706** Heartbeat metric `agent.killswitch.lag_seconds` emission + SLO entry. [→ FR-AG05, FR-O02] · `/apps/agents/common/lifecycle/heartbeat.py`
- **T707** API `POST /agents/{id}/killswitch` with Entra+role+justification+dual-approval semantics per FR-AG05a. [→ FR-AG05a, NN-1] · `/apps/api/app/api/routes/agents.py`
- **T708** API `POST /agents/{id}/autonomy` with same governance controls. [→ FR-AG02, NN-1] · `/apps/api/app/api/routes/agents.py`
- **T709** State-graph generator (Mermaid stateDiagram-v2 from agent config). [→ FR-AG06] · `/apps/agents/tools/render_state_graph.py`
- **T710** Reflection feedback loop: post-approval outcome → eval training-data store. [→ FR-AG07] · `/apps/api/app/services/reflection_feedback_service.py`
- **T711** Per-handoff timeouts in `HandoffChainDefinition`. [→ FR-AG08] · `/apps/agents/common/resilience/handoffs.py`
- **T712** Consensus-event detector + `ConsensusEvent` write. [→ FR-AG09] · `/apps/api/app/services/consensus_detector.py`
- **T713** AAR gap-summary generator on every ScenarioRun completion. [→ FR-AG10] · `/apps/api/app/services/aar_gap_summary.py`
- **T714** Recommendation `why fired` trace artifact (input signals + threshold passed) — wired into Stream 3 endpoint. [→ FR-AG03] · `/apps/api/app/services/why_fired_service.py`

## Phase 10 — User Story 6 (CI/CD + perf + day-2) — Stream 8 (T801–T840)

- **T801** Verify spec 031 landed (cross-stream prereq); update plan checkbox. [→ FR-C01 verify] · `/specs/032-rubric-improvements/plan.md`
- **T802** Remove `continue-on-error: true` on benchmark step + define numeric regression thresholds. [→ FR-R01, FR-R02] · `/.github/workflows/ci.yml`
- [X] **T803** Add `nightly-load.yml` workflow targeting staging. [→ FR-T05, FR-R02] · `/.github/workflows/nightly-load.yml`
- [X] **T804** Author capacity model doc. [→ FR-R03] · `/docs/architecture/capacity-model.md`
- **T805** Bicep: Cosmos autoscale max-RU caps per container. [→ FR-R04] · `/infra/main.bicep`
- [X] **T806** Bicep: Azure Chaos Studio targets + experiments. [→ FR-R05] · `/infra/modules/chaos-studio.bicep`
- [X] **T807** Add `chaos-quarterly.yml` workflow (staging-only). [→ FR-R05, FR-T03] · `/.github/workflows/chaos-quarterly.yml`
- **T808** [ML] Bicep: Cosmos PITR (continuous backup mode 7-day). [→ FR-D04] · `/infra/main.bicep`
- [X] **T809** [ML] Author DR/BCP runbook (RPO ≤ 15 min, RTO ≤ 60 min, AU Southeast failover steps). [→ FR-D01] · `/docs/operator-runbooks/dr-bcp.md`
- [X] **T810** [ML] Author Cosmos backup/restore runbook. [→ FR-D04] · `/docs/operator-runbooks/cosmos-backup-restore.md`
- [X] **T811** [EV] Author model-rollback runbook (deployment alias flip). [→ FR-AI07] · `/docs/operator-runbooks/model-rollback.md`
- [X] **T812** [EV] Author cost-report template tied to `llm_mixin.py` budget output. [→ FR-D03] · `/docs/operator-runbooks/cost-reporting.md`
- **T813** Pin every Container Apps Dockerfile base image to a digest; Dependabot watches Dockerfiles. [→ FR-D02] · `/apps/*/Dockerfile`, `/.github/dependabot.yml`
- [X] **T814** DORA dashboard publisher GitHub Action — daily aggregator → App Insights customMetrics. [→ FR-C04] · `/.github/workflows/dora-metrics.yml`
- [X] **T815** Author progressive-delivery doc (post spec 031). [→ FR-C02] · `/docs/ci-cd/progressive-delivery.md`
- [X] **T816** Author DORA metrics doc. [→ FR-C04] · `/docs/ci-cd/dora-metrics.md`
- [X] **T817** Document AOAI quota request path. [→ FR-AI08] · `/docs/operator-runbooks/aoai-quota.md`
- [X] **T818** [ML] Add `dr-drill.yml` workflow (manual + scheduled monthly). [→ FR-D01, FR-R05] · `/.github/workflows/dr-drill.yml`
- **T819** [EV] Add canary deployment for new model versions (or migrate equivalent gate into simplified pipeline). [→ FR-AI10] · `/.github/workflows/cd.yml`

## Phase 11 — User Story 8 (Documentation) — Stream 9 (T901–T930)

- **T901** Record + link 60-second walkthrough video in README. [→ FR-DOC01] · `/README.md`
- **T902** Next.js route hosting Redoc at `/api-docs`. [→ FR-DOC02] · `/apps/web/src/app/api-docs/page.tsx`
- **T903** Consolidate the three governance/eval doc hubs under `/docs/governance-hub/`. [→ FR-DOC03] · `/docs/governance-hub/`
- [X] **T904** Web Vitest tier scaffold + first 5 tests. [→ FR-T02] · `/apps/web/__tests__/`, `/apps/web/vitest.config.ts`
- [X] **T905** Add Playwright e2e spec for the operator critical journey. [→ FR-I03] · `/apps/web/e2e/operator-journey.spec.ts`
- **T906** Author `tests/contract/CONTRIBUTING.contract.md` contributor guide. [→ FR-T08] · `/tests/contract/CONTRIBUTING.contract.md`
- **T907** Per-spec requirement→test traceability matrix template + 032's matrix. [→ FR-T07] · `/specs/032-rubric-improvements/traceability.md`
- **T908** Cross-link post-exercise-survey outcomes to test cases. [→ FR-T10] · `/docs/disaster-response-hub/evaluation/post-exercise-survey.md`
- **T909** Encode spec-030 acceptance criteria as concrete pytest IDs once eval framework lands. [→ FR-T09] · `/tests/eval/`
- **T910** Update `apps/ingestion/` operator runbook coverage. [→ FR-I04] · `/docs/operator-runbooks.md`

## Phase 12 — Polish (T1001–T1010)

- **T1001** Run full `pre-commit run --all-files` and fix any drift.
- **T1002** Run `ruff check apps tests packages` (canonical) and fix.
- **T1003** Run `mypy --strict apps packages` and fix.
- **T1004** Run `python -m pytest tests/unit tests/integration tests/contract -q --tb=line --cov` and ensure coverage gates pass.
- **T1005** Validate every FR has a closing entry in the traceability matrix (T907).
- **T1006** Update `CHANGELOG.md` with the 032 entry covering all merged deliverables.
- **T1007** Final rubber-duck review of the implementation.
- **T1008** Run `azd auth login` + `azd up` against the dev environment (Step 9 prep).
- **T1009** Tag the merge commit `v032-rubric-improvements`.
- **T1010** Trigger spec 032 status promotion: Draft → Approved.

## Dependency Graph (high-level)

```
Phase 1 (T001-T010) ──┐
                      ▼
Phase 2 (T011-T030) ──┐  ◄── ADRs + spike + carve-out + docs scaffold
                      ▼
Phase 3 (T101-T110) ──┐  ◄── Stream 1 hygiene (parallelisable internally)
                      ▼
Phase 4 (T201-T209) ──┐  ◄── Stream 2 refactor (depends on Phase 3)
                      ▼
┌──────────┬──────────┬──────────┬──────────┬──────────┐
▼          ▼          ▼          ▼          ▼          ▼
Phase 5    Phase 6    Phase 7    Phase 8    Phase 9    Phase 10/11
(US1)      (US2)      (US3)      (US4)      (US5)      (US6,7,8)
```

Cross-cuts:
- Phase 6 OIDC tasks (T413–T415) gated by spec 031 prereq.
- Phase 8 RAG ingest (T602) gated by Phase 6 PE (T406) + Phase 2 licence inventory (T029).
- Phase 8 Phi shadow (T608) gated by Phase 4 classification (T209) + Phase 2 carve-out (T017, T018).
- Phase 9 kill-switch tasks (T704–T707) gated by Phase 2 spike (T016).
- Phase 10 spec-031 verification (T801) gated externally.

## Per-User-Story Independent Test Criteria

| US | Independent test |
|---|---|
| US1 | Replay a stored ScenarioRun → assert provenance + integrity-check + ledger-hash + "why fired" panel. |
| US2 | From public network, probe Cosmos/Storage/AOAI/Content Safety/AI Search → 100% rejected. From inside VNet → succeed. OIDC migrated. |
| US3 | Trigger a synthetic incident; SLO Workbook updates within 1 min; trace tree end-to-end; SLO breach pages. |
| US4 | Eval harness against `eval-dataset/v1` → scorecards meet baseline; structured-output validation 100%; cosign verify in cd.yml. |
| US5 | Engage a kill-switch via API (with dual-approval in prod); propagation ≤ 30 s; consensus event recorded; AAR gap summary present. |
| US6 | Force regional failover drill in staging → traffic shifts within RTO; benchmark gate fails on regression; nightly load runs. |
| US7 | Introduce deliberate violations of strict typing, illegal import, unformatted file, coverage regression → CI fails on each. |
| US8 | First-time reviewer reaches video, API docs, SLO doc, CONTRIBUTING, CHANGELOG, tests/README in < 60 s, zero broken links. |

## Total task count

**~115 tasks** across 12 phases. Streams 0–2 (T001–T209) are Phase 1–4 foundation. P1 user stories (US1–US4) span Phases 5–8. P2 (US5–US7) Phases 9–11. P3 (US8) absorbed into Phase 11. Polish in Phase 12.

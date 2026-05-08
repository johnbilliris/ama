---
description: "Dependency-ordered task list for spec 036 — Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat"
---

# Tasks: Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat

**Branch**: `036-foundry-rag-grounding` | **Date**: 2026-05-08 | **Spec**: [`spec.md`](./spec.md) | **Plan**: [`plan.md`](./plan.md)
**Inputs**: [`research.md`](./research.md) (16 R-NN decisions), [`data-model.md`](./data-model.md) (10 entities), [`contracts/`](./contracts/) (6 contract artefacts), [`quickstart.md`](./quickstart.md), [`spec.md`](./spec.md) (43 FRs, 8 USs, 12 SCs), persona memos at `personas-input/{operational,sectors-*,technical-*}.md`.

**Tests**: Tests are mandatory in this spec (Constitution §Quality Gates + spec 030 test pyramid). Every FR carries ≥ 1 test task. Tests within a phase MUST be authored (red) before the implementation tasks they cover (green).

**Format**: `- [ ] T### [P?] Description (file path + FR/R/SC/US references)` — `[P]` marks tasks that are parallel-safe (different files / no incomplete deps). Phases A–E run **sequentially** (per plan.md §Phasing); within a phase, `[P]` tasks may run concurrently. Phase 0 is the cross-cutting setup phase.

---

## Front-matter — task metrics

| Bucket | Count |
|---|---|
| **Total tasks** | **140** |
| Phase 0 (Setup) | 6 |
| Phase A (Foundry seam + carve-out enforcement) | 21 |
| Phase B (Corpus ingest + blue-green index) | 28 |
| Phase C (Shared retrieval + per-agent grounding + simulation grounding) | 44 |
| Phase D (RAG-OPTOUT + offline cache + multi-jurisdiction QA) | 28 |
| Phase E (Final cutover + chaos game-day cadence) | 13 |
| **Parallel-safe `[P]` tasks** | **93** |

| FR family | Tasks (impl + test) | Total |
|---|---|---|
| FM (Foundry migration; FR-RAG-FM-01..07) | impl 9 + test 5 | **14** |
| CV (Carve-out enforcement; FR-RAG-CV-01..04) | impl 6 + test 4 | **10** |
| IDX (Corpus ingest + index; FR-RAG-IDX-01..08) | impl 13 + test 9 | **22** |
| AG (Agent retrieval + citations; FR-RAG-AG-01..06) | impl 12 + test 9 | **21** |
| NS (RAG opt-outs; FR-RAG-NS-01..09) | impl 11 + test 2 | **13** |
| SIM (Simulation grounding; FR-RAG-SIM-01..06) | impl 5 + test 3 | **8** |
| LS (Life-safety + offline cache; FR-RAG-LS-01..03) | impl 7 + test 4 | **11** |
| Cross-cutting (setup, persona, polish, eval, replay) | — | **43** |

| User Story | Coverage |
|---|---|
| US1 — Grounded recommendations + citations (P1) | T060–T081, T137–T140 |
| US2 — All Foundry endpoints, no Azure-OpenAI in code (P1) | T015–T029, T090–T094, T130–T131 |
| US3 — Simulation grounding via SSE (P1) | T068, T083–T086, T130 |
| US4 — Corpus indexed with licence-mode (P1) | T031–T060 |
| US5 — Pipeline-only opt-outs documented (P2) | T100–T120 |
| US6 — Field Coordinator offline cache (P2) | T102–T104, T121–T126 |
| US7 — Multi-agency jurisdiction-disambiguated retrieval (P2) | T065, T074, T125 |
| US8 — ATSI/CALD/accessibility warning composition (P3) | T067, T082, T105, T124 |

**MVP scope** (suggested): Phases 0 + A + B + C1–C7 + first canary (T090) — delivers US1+US2 partial+US3+US4 and proves the seam end-to-end on the Monitoring agent before a wider canary. Defer Phases D + E until after the first agent flip is stable.

---

## Phase 0 — Setup & shared scaffolding

**Purpose**: shared dependencies, packages and traceability stubs that every subsequent phase consumes. **Blocks** Phases A–E.

- [X] T001 [P] Add `azure-ai-inference`, `presidio-analyzer`, `presidio-anonymizer`, `azure-search-documents`, `tenacity` to `apps/agents/pyproject.toml` and `apps/api/pyproject.toml`; pin minor versions; run `uv lock`. (R-01)
- [X] T002 [P] Scaffold new `apps/ingest-runner/` package: `pyproject.toml`, `src/ama_ingest/__init__.py`, `Dockerfile` (python:3.13-slim), `tests/{unit,integration}/__init__.py`. Wire into root `pnpm-workspace.yaml` / `pyproject.toml` workspace. (FR-RAG-IDX-01, R-08)
- [X] T003 [P] Install `age` CLI in dev container (`/.devcontainer/Dockerfile`) and CI runner (`.github/actions/setup/action.yml`); document in `quickstart.md` §1. (FR-RAG-LS-02, R-04)
- [X] T004 [P] Create empty pydantic-v2 modules under `packages/domain/src/ama_domain/`: `retrieval.py`, `citation.py`, `offline_cache.py` (NEW); reserve extension hooks in `audit_record.py`. Re-export from `packages/domain/src/ama_domain/__init__.py`. (data-model.md §Schema-mirror)
- [X] T005 [P] Mirror the three JSON Schemas under `packages/schemas/`: `citation-envelope.json`, `audit-record-llm-call.json`, `offline-cache-manifest.json` — copy the contracts files verbatim and add a `tests/contract/test_schema_mirror_parity.py` that asserts byte-equality with `specs/036-foundry-rag-grounding/contracts/`. (data-model.md §Schema-mirror)
- [X] T006 Run `scripts/update-agent-context.ps1 -AgentType copilot` to append the spec-036 stanza to `.github/agents/copilot-instructions.md`; commit only the diff. (Plan §Project Structure)

**Checkpoint 0**: workspace builds, `uv lock` passes, `pnpm -w build` passes, schemas mirrored.

---

## Phase A — Foundry seam + carve-out enforcement (M1)

**Goal G1 partial + G2 complete.** Lands the constructor-injectable seam, the three Foundry call-site migrations (kept dual-runnable behind spec-029 FF), and the carve-out CD gate. **Spec-014 fallback chain remains intact** (FR-RAG-FM-06 — legacy `AzureOpenAI` import path stays importable until E1).

### A — Tests (write red first)

- [X] T010 [P] Contract test `tests/contract/test_foundry_chat_client.py` — assert `FoundryChatClient` Protocol shape, `chat_complete` and `chat_complete_stream` signatures, `FoundryResponse` / `FoundryStreamChunk` immutability (frozen dataclass), forbidden imports list. (contracts/foundry-chat-client.md, FR-RAG-FM-07, R-01)
- [X] T011 [P] Contract test `tests/contract/test_no_openai_imports.py` (skip-marked `pytest.mark.skip(reason="binds atomically with E1 / FR-RAG-FM-06")`) — asserts zero `from openai import AzureOpenAI`, `AsyncAzureOpenAI`, or `OpenAIChatClient(... mode="azure_openai" ...)` in `apps/` (allowlist: `apps/agents/common/llm_client.py` legacy path, `tests/`, `docs/`). Skip removed in T131. (FR-RAG-FM-04, SC-002)
- [X] T012 [P] Entity test `tests/contract/test_carveout_registry_entry.py` — load every row in `infra/parameters/foundry-carveout.yaml`, validate against `infra/parameters/foundry-carveout.schema.json`, assert `data_minimisation_required: true`, `classification_filter_required: true`, `len(approver_identities) >= 2`, `review_date <= today + 365d`. (CarveoutRegistryEntry; FR-RAG-CV-01..02)
- [X] T013 [P] Integration test `tests/integration/test_carveout_enforcement.py` — synthesise four CD-failure cases: (i) deployment missing from registry, (ii) `review_date` expired, (iii) placeholder `approver_identities`, (iv) `australiacentral` data-plane resource. `verify-carveout.ps1` MUST exit non-zero on each. (FR-RAG-CV-01..04, SC-003, SC-004)
- [X] T014 [P] Integration test `tests/integration/test_data_minimisation_gateway.py` — Presidio PII redaction (e.g. `0412 345 678` → `<PHONE>`); PSPF marking detection (`OFFICIAL: SENSITIVE`, `PROTECTED`, `SECRET`, `TOP SECRET`); sensitive-operational-content regex; deny → `audit.gateway_decision == "deny"` with reason; allow → log only. (FR-RAG-CV-03)
- [X] T015 [P] Equivalence-gate harness test `tests/integration/test_fr023_per_agent_gate.py` — given a per-agent golden Q&A fixture, assert ≥ 95% decision-equivalence + 100% schema-equivalence (reuses spec-033 FR-023 logic). Used by every canary task T090–T094, T130. (FR-RAG-FM-06, spec-033)

### A — Implementation

- [X] T016 Create `apps/agents/common/foundry_chat_client.py` with the Protocol exactly as specified in [`contracts/foundry-chat-client.md`](./contracts/foundry-chat-client.md) §1: `FoundryResponse`, `FoundryStreamChunk` frozen dataclasses; `ChatComplete` / `ChatCompleteStream` type aliases; `@runtime_checkable FoundryChatClient` Protocol with sync + async methods. (FR-RAG-FM-07, R-01)
- [X] T017 Implement `LiveFoundryChatClient` in same file — wraps `azure.ai.inference.ChatCompletionsClient` (sync) and `azure.ai.inference.aio.ChatCompletionsClient` (async/streaming). MUST authenticate via `DefaultAzureCredential` against scope `https://cognitiveservices.azure.com/.default`; MUST raise `AssertionError` if any caller passes `api_key=`. Token cache via `ChainedTokenCredential` with 5-min TTL. (FR-RAG-FM-05, R-01)
- [X] T018 Migrate `apps/agents/common/llm_client.py` from `openai.AzureOpenAI` to the new seam: constructor accepts `chat_complete: ChatComplete | None = None`; default constructs `LiveFoundryChatClient`; **preserve the existing `_generate_with_fallback` template-fallback chain unchanged** (Constitution §I; FR-RAG-FM-06). Legacy import path stays importable behind a `LEGACY_AZURE_OPENAI=1` env flag for canary backout. (FR-RAG-FM-01, FR-RAG-FM-06)
- [X] T019 Migrate `apps/agents/maf_runtime/chat_client.py`: keep the existing `build_azure_openai_chat_client` factory **signature** (zero call-site churn) but build a Foundry-backed `OpenAIChatClient` shim that proxies through the same seam. (FR-RAG-FM-02)
- [X] T020 Migrate `apps/api/app/services/simulation/controller_service.py` line ~368 from `from openai import AsyncAzureOpenAI` to the new async Foundry client; inject `chat_complete_stream` seam; **do not modify `controller_prompt.md`** (OOS-6). (FR-RAG-FM-03)
- [X] T021 [P] Extend `apps/agents/common/llm_config.py` with `AZURE_AI_PROJECT_ENDPOINT` (Foundry endpoint URL) and `AZURE_AI_PROJECT_DEPLOYMENTS` (CSV of `modelId@version=deploymentName`); add typed Pydantic `Settings` class; cite `apps/eval-runner/src/ama_eval/foundry_client.py` as the pattern source. (FR-RAG-FM-01, R-01)
- [X] T022 Create `apps/agents/common/model_gateway.py` — Presidio analyzer pipeline (PII), PSPF-marking regex (`OFFICIAL`, `OFFICIAL: SENSITIVE`, `PROTECTED`, `SECRET`, `TOP SECRET`), sensitive-operational-content classifier (allow-list of safe topics; default deny). Gateway is invoked **before any non-AU Foundry call** (deployment region read from carve-out registry); deny → audit `gateway_decision: "deny"` + `reason`; allow → continue. (FR-RAG-CV-03)
- [X] T023 Wire `model_gateway.apply()` into `LiveFoundryChatClient.chat_complete` / `chat_complete_stream` for any deployment whose registry row has `region != australiaeast|australiasoutheast`. (FR-RAG-CV-03, FR-RAG-CV-04)
- [X] T024 Extend `scripts/verify-carveout.ps1` to: (i) walk every `Microsoft.CognitiveServices/accounts/deployments@*` resource emitted by `bicep what-if` and require a matching registry row, (ii) fail on `review_date <= today`, (iii) fail on missing or placeholder (`TODO`, `<approver-1>`) `approver_identities`, (iv) fail on any data-plane resource whose location is not `australiaeast` / `australiasoutheast`. (FR-RAG-CV-01, -02, -04, SC-003, SC-004)
- [X] T025 Materialise the missing `infra/policy/rego/foundry_carveout.rego` referenced by the YAML header — single OPA rule that mirrors the registry schema. (FR-RAG-CV-01)
- [X] T026 Wire `scripts/verify-carveout.ps1` into `.github/workflows/cd.yml` as a `pre-plan-apply` blocking step; cache OPA conftest binary across runs. (FR-RAG-CV-02)
- [X] T027 [P] Populate `infra/parameters/foundry-carveout.yaml` with the production rows: AU East chat (`gpt-4o-mini@2024-07-18`, `gpt-4o@2024-08-06`), AU East embedding (`text-embedding-3-large@1`), and any non-AU exception (defaults to none). Each row carries two non-placeholder `approver_identities` (Security Engineer + Compliance Auditor) and `review_date: today + 12 months`. (FR-RAG-CV-01, SC-003)
- [X] T028 [P] Wire spec-029 progressive-delivery feature flag `foundry_rag_enabled_agents` (per-agent boolean map: `MonitoringAgent`, `RiskAssessmentAgent`, `EvacuationAgent`, `ResourceAllocationAgent`, `CommunicationAgent`, `SimulationController`) into `packages/domain/feature_flags.py` and the existing FF schema/runtime; default all `false`. (FR-RAG-FM-06, spec-029, R-12)
- [X] T029 [P] Extend `apps/eval-runner/src/ama_eval/` with a `per_agent_canary_gate.py` CLI that: (i) reads `foundry_rag_enabled_agents`, (ii) runs the per-agent golden Q&A, (iii) emits an `EquivalenceTestResult` (spec-033 FR-023 shape extended) with `decision_equivalence`, `schema_equivalence`, `citation_fidelity` placeholder, (iv) exits non-zero on < 95% / < 100%. (FR-RAG-FM-06, spec-033 FR-023, R-13, EquivalenceTestResult entity)
- [X] T030 [P] Add Application Insights `FoundryRAGCutover` custom table + KQL alert `count() where rag_used == false and agent in (flipped_agents)` ≥ 1 in 5min → page on-call. Persona-anchor: SRE-memo Top-9. (FR-RAG-FM-06, R-12)

**Checkpoint A**: all three migration anchors compile against the new seam; CD gate fails on synthetic carve-out gap; FR-023 harness runs green on a fixed regression suite; no agent flipped yet.

---

## Phase B — Corpus ingest + blue-green index (M2)

**Goal G3 complete.** Lands `apps/ingest-runner` Container Apps Job, the single jurisdiction-faceted index, the blue-green alias + 4-signal parity gate, and the licence-inventory lint.

### B — Tests (write red first)

- [X] T031 [P] Contract test `tests/contract/test_ingest_pipeline.py` — assert idempotency (unchanged corpus → 0 embedding calls), provenance-on-every-chunk, single-`embedding_model_id`-per-index invariant, parity-gate signal contract. (contracts/ingest-pipeline.md, FR-RAG-IDX-04, R-04, R-05)
- [X] T032 [P] Integration test `tests/integration/test_idempotent_ingest.py` — re-run ingest on unchanged `docs/corpus/` against staging AI Search; assert 0 re-embeds + 0 index writes + ≤ 10% cold-start runtime. (FR-RAG-IDX-04, SC-005)
- [X] T033 [P] Integration test `tests/integration/test_blue_green_alias_flip.py` — embedding-model swap → fresh `corpus-v{N+1}` build → parity gate PASS → alias flip < 60s → old index retained 7 days. (FR-RAG-IDX-04, R-05, R-15)
- [X] T034 [P] Integration test `tests/integration/test_blue_green_parity_gate_fail.py` — synthesise a regression that fails each of the 4 parity signals (chunk-count delta > 5%, cost ratio > 1.3×, FR-023 < 95%, mixed `embedding_model_id`); assert flip is HALTED in each case. (FR-RAG-IDX-04, R-05)
- [X] T035 [P] Entity test `tests/integration/test_corpus_entry_validation.py` — every `source.json` under `docs/corpus/**` validates against the CorpusEntry schema (data-model.md §CorpusEntry). (CorpusEntry; FR-RAG-IDX-01, -02, -07)
- [X] T036 [P] Entity test `tests/integration/test_chunk_index_invariants.py` — every Chunk doc carries `{jurisdiction, topic, page, sha256_of_chunk, source_url, retrieved_at, licence_mode, corpus_build_sha, embedding_model_id}`; missing fields → fail. (Chunk; FR-RAG-IDX-02, -03, -04)
- [X] T037 [P] Integration test `tests/integration/test_licence_mode_partition.py` — 100% `full-text` body-indexed; 100% `metadata-only` metadata-only-indexed; 0 `excluded` chunks reachable via search. (FR-RAG-IDX-02, SC-006)
- [X] T038 [P] Integration test `tests/integration/test_capacity_alert.py` — synthesise 70% utilisation; assert AI Search alert fires; assert `chunk_size_tokens` histogram recorded. (FR-RAG-IDX-08, R-10)
- [X] T039 [P] Integration test `tests/integration/test_indexing_licence_inventory_lint.py` — drift between `source.json` and `INDEXING-LICENCE-INVENTORY.md` → CI fail. (FR-RAG-IDX-07)

### B — Implementation

- [X] T040 Create `apps/ingest-runner/src/ama_ingest/__main__.py` CLI — entrypoint `python -m ama_ingest [--full | --incremental | --dry-run]`; reads env per `quickstart.md` §4. (FR-RAG-IDX-01, R-08)
- [X] T041 [P] `apps/ingest-runner/src/ama_ingest/chunker.py` — H2 page-boundary split + 1024-token cap + 10% sliding overlap + atomic table/code-block preservation; emit `chunk_size_tokens` histogram + truncation-rate gauge; alert on > 0.5%. (FR-RAG-IDX-02, R-04, R-10)
- [X] T042 [P] `apps/ingest-runner/src/ama_ingest/embedder.py` — calls `text-embedding-3-large` @ 3072 dims via `LiveFoundryChatClient`; tenacity retry on 429/503; per-call cost telemetry. (FR-RAG-IDX-02, R-02)
- [X] T043 [P] `apps/ingest-runner/src/ama_ingest/licence_filter.py` — three-mode gating: `full-text` (body+embed), `metadata-only` (title+URL+summary, no body, no body embedding), `excluded` (skip before embedding budget touched); deploy-time warning if any agent prompt template references an `excluded` source. (FR-RAG-IDX-02, SC-006)
- [X] T044 [P] `apps/ingest-runner/src/ama_ingest/indexer.py` — blue-green write to `corpus-v{N+1}`; alias flip helper; SHA-skip idempotency (`if existing_doc.sha256 == source.sha256: skip`); writes provenance fields per FR-RAG-IDX-03. (FR-RAG-IDX-03, -04, R-15)
- [X] T045 [P] `apps/ingest-runner/src/ama_ingest/manifest.py` — emits `corpus_build_sha` (sha256 of `git ls-tree HEAD docs/corpus/`); cosign keyless (Sigstore + GitHub OIDC) signs the manifest at build time per spec 032 FR-AI09. (FR-RAG-IDX-03, FR-RAG-LS-02 prep)
- [X] T046 [P] `apps/ingest-runner/src/ama_ingest/parity_gate.py` — 4-signal gate per ingest-pipeline.md §3.3: chunk-count delta ±5%, cost ratio ≤ 1.3×, FR-023 ≥ 95%, single-`embedding_model_id` invariant. Halt flip on any fail; emit `topic.corpus-build-complete` with per-signal breakdown. (FR-RAG-IDX-04, R-05)
- [X] T047 [P] `apps/ingest-runner/src/ama_ingest/offline_bundle.py` — emit per-build ≤ 500 MB cache bundle + cosign manifest signature + `age` detached signature; hand off to T121 for fail-closed verification. (FR-RAG-LS-02, R-04, R-07)
- [X] T048 Create `infra/modules/ai-search-blue-green.bicep` — wraps the existing `ai-search.bicep` module; `aliasName`, `currentIndexName`, `nextIndexName` parameters; outputs `aliasFlipReady` boolean. **Reuses** the existing module per R-15 (no replacement). (FR-RAG-IDX-04, R-15)
- [X] T049 Extend `infra/modules/ai-search.bicep` with `jurisdictionValues` (`act,nsw,nt,qld,sa,tas,vic,wa,national,aidr`), `vectorDimensions: 3072`, `licenceModeValues` (`full-text,metadata-only`), capacity alert at 70%. (FR-RAG-IDX-06, -08)
- [X] T050 Wire `ingest-runner` as a Container Apps Job in `infra/main.bicep`; pass `embeddingDeploymentName`, AAD workload identity, AI Search managed identity assignment, Service Bus output binding `topic.corpus-build-complete`. (FR-RAG-IDX-01, -05, -06)
- [X] T051 Confirm AI Search service deploys with `publicNetworkAccess: 'disabled'` + Private Endpoint in AU East subnet + no cross-region replication. (FR-RAG-IDX-06)
- [X] T052 [P] Create `scripts/seed_ingest.py` — `azd postprovision` hook that invokes the ingest-runner job, polls Service Bus for completion, sets `CORPUS_BUILD_SHA` env on Container Apps revisions. (FR-RAG-IDX-05)
- [X] T053 [P] Create `.github/workflows/corpus-ingest.yml` — triggered by `docs/corpus/**` push and on a nightly schedule; invokes the ingest-runner job; emits `corpus_build_sha` artefact. (FR-RAG-IDX-05)
- [X] T054 [P] Author `docs/corpus/INDEXING-LICENCE-INVENTORY.md` — machine-checked inventory mirroring spec-032 AIDR `LICENCE-INVENTORY.md` pattern; one row per `source.json` with `(jurisdiction, topic, licence_mode, source_url, last_verified)`. (FR-RAG-IDX-07)
- [X] T055 Add CI step in `.github/workflows/ci.yml` that runs `T039` inventory lint on every PR. (FR-RAG-IDX-07)
- [X] T056 [P] Wire ingest-runner audit emission to Cosmos `audit_records` (one record per embedding call) per FR-RAG-AG-02 + R-13 (45-day operational + 7-year archive). (FR-RAG-AG-02, R-13, ingest-pipeline.md §6)
- [X] T057 [P] Add ingest-runner pre-flight check that calls `verify-carveout.ps1 --check-deployment $EMBEDDING_DEPLOYMENT` — fail-closed before any embedding call. (FR-RAG-CV-01, ingest-pipeline.md §3.7)
- [X] T058 [P] Add `infra/modules/azure-openai.bicep` deprecation tag (`metadata.deprecated = '036-foundry-rag-grounding'`) — kept legacy for canary fallback; deletion deferred to E1. (FR-RAG-FM-06)

**Checkpoint B**: `azd up` provisions AI Search + Container Apps Job; first ingest runs and produces `corpus-v1`; re-run yields 0 re-embeds (SC-005); blue-green alias flip works against staging.

---

## Phase C — Shared retrieval + per-agent grounding + simulation grounding (M3)

**Goal G1 complete + G4 partial.** Lands `RetrievalService`, the audit-record extension, the citation envelope on every recommendation card and SSE turn, hallucinated-citation suppression, the Communication-agent ATSI/CALD/Auslan retrieval, simulation-chat grounding, and the per-agent canary flips for Monitoring → Risk Assessment → Evacuation → Resource Allocation → Communication.

### C — Tests (write red first)

- [ ] T060 [P] Contract test `tests/contract/test_retrieval_service.py` — `RetrievalService` Protocol shape; `RetrievalRequest` / `RetrievalResult` / `RetrievedChunk` schema validation; jurisdiction-union semantics (own ∪ national ∪ aidr); RRF default vector 0.7 / lexical 0.3; empty-result handling; classification-ceiling enforcement. (contracts/retrieval-service.md, FR-RAG-AG-01, FR-RAG-AG-04, R-03, R-06)
- [ ] T061 [P] Contract test `tests/contract/test_citation_envelope.py` — round-trip JSON Schema 2020-12 validation against `contracts/citation-envelope.json`; required fields: `jurisdiction`, `topic`, `page`, `source_url`, `sha256_of_chunk`, `confidence`. (FR-RAG-AG-03, FR-RAG-SIM-02, R-11, R-16)
- [ ] T062 [P] Contract test `tests/contract/test_audit_record_shape.py` — round-trip JSON Schema 2020-12 validation against `contracts/audit-record-llm-call.json`; required fields per FR-RAG-AG-02; opt-out shape: `rag_used == false` requires `rag_optout_reason` + `adr_pointer`. (FR-RAG-AG-02, FR-RAG-NS-01..09, FR-RAG-SIM-04, R-13)
- [ ] T063 [P] Entity test `tests/contract/test_retrieval_request_response.py` — pydantic-v2 round-trip; `min_length=1` jurisdictions; `top_k ∈ [1, 20]`; `classification_max == "OFFICIAL"`. (RetrievalRequest/RetrievalResult)
- [ ] T064 [P] Entity test `tests/contract/test_citation_entity.py` — pydantic-v2 round-trip; `confidence ∈ [0.0, 1.0]`; forbids `text` when `licence_mode == "metadata-only"`. (Citation)
- [ ] T065 [P] Integration test `tests/integration/test_jurisdiction_disambiguation.py` — curated 50-query persona-driven set covering NSW–VIC border (RFS vs CFA-VIC; FRNSW vs FRV), NT–QLD cyclone (NTES vs SES-QLD), ACT–NSW handoff (ACT RFS vs NSW RFS, AFP-ACT vs NSW Police), DFES-WA single-agency edge cases; assert 0 silent conflations. (FR-RAG-AG-04, SC-010, US7, R-03)
- [ ] T066 [P] Integration test `tests/integration/test_hallucinated_citation_suppression.py` — 200-prompt jailbreak/hallucination suite; assert 0 hallucinated citations rendered to operators; `hallucinated_citation_count` audit field populated. (FR-RAG-AG-05, SC-007, R-10)
- [ ] T067 [P] Integration test `tests/integration/test_communication_agent_atsi_cald.py` — vulnerable-population scenario (e.g. NSW NW flood with high CALD census + 2 ATSI communities) → retrieval surfaces ATSI/CALD/Auslan/Easy-Read/TIS-National corpus entries before composition. (FR-RAG-AG-06, US8)
- [ ] T068 [P] Integration test `tests/integration/test_simulation_sse_citation.py` — drive a simulation chat turn → assert SSE `citation` event emitted per grounded reply (FR-RAG-SIM-02); assert empty-result emits `citations: []` + "no corpus match" note (FR-RAG-SIM-03); assert audit shape per FR-RAG-SIM-04; assert spec-024 rate-limit / comms-block / tenant-isolation / approval workflow preserved (FR-RAG-SIM-05); assert latency p95 ≤ 1.3 × spec-024 baseline. (FR-RAG-SIM-01, FR-RAG-SIM-02, FR-RAG-SIM-03, FR-RAG-SIM-04, FR-RAG-SIM-05, FR-RAG-SIM-06, SC-007, SC-012)
- [ ] T069 [P] Integration test `tests/integration/test_audit_replay.py` — given `(corpus_build_sha, prompt_sha, model_version, retrieved_chunks_set)`, replay reproduces byte-identical retrieval inputs ≥ 95% across one-month window. (FR-RAG-AG-02, SC-011, R-13)
- [ ] T070 [P] Integration test `tests/integration/test_classification_ceiling.py` — request with `classification_max` ≠ `OFFICIAL` → `RetrievalService.retrieve` raises `ClassificationCeilingError`. (FR-RAG-NS-07, contracts/retrieval-service.md §2.5)

### C — Implementation: domain models + retrieval

- [ ] T071 [P] Implement `packages/domain/src/ama_domain/retrieval.py` — `RetrievalRequest`, `RetrievalResult`, `RetrievedChunk`, `Jurisdiction`, `LicenceMode` (data-model.md §RetrievalRequest, §RetrievalResult). (RetrievalRequest, RetrievalResult entities)
- [ ] T072 [P] Implement `packages/domain/src/ama_domain/citation.py` — Citation pydantic-v2 mirror of `contracts/citation-envelope.json`. (Citation entity, R-11)
- [ ] T073 [P] Extend `packages/domain/src/ama_domain/audit_record.py` — additive fields per data-model.md §AuditRecord: `retrieved_chunks: list[RetrievedChunkRef]`, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `rag_used: bool`, `rag_optout_reason: str | None`, `gateway_decision: Literal["allow","deny","redact"]`, `hallucinated_citation_count: int`, `adr_pointer: str | None`. (AuditRecord entity, FR-RAG-AG-02, R-13)
- [ ] T074 [P] Implement `packages/domain/src/ama_domain/offline_cache.py` — pydantic-v2 mirror of `contracts/offline-cache-manifest.json`; dual-signature fields. (OfflineCacheManifest entity, FR-RAG-LS-02)
- [ ] T075 Create `apps/agents/common/retrieval_client.py` — `AzureSearchRetrievalService(RetrievalService)` implementing the Protocol; uses `azure-search-documents` async client + Foundry-embedded query vectors (via injected `chat_complete` seam); RRF (decision [R-06](./research.md): default vector 0.7 / lexical 0.3); top-k default 5 (configurable per agent). (FR-RAG-AG-01, R-06)
- [ ] T076 Add jurisdiction-union expansion in `AzureSearchRetrievalService.retrieve()` — input `jurisdictions=["nsw"]` → effective filter `jurisdiction in ("nsw","national","aidr")`. (FR-RAG-AG-04, R-03, US7)
- [ ] T077 Add classification-ceiling check in `AzureSearchRetrievalService.retrieve()` — `request.classification_max != "OFFICIAL"` → raise `ClassificationCeilingError` (FR-RAG-NS-07). (FR-RAG-NS-07)
- [ ] T078 [P] Per-agent quota governance (R-09): emit `Foundry.TokensPerSecond` metric tagged with `agent_name`; configure Application Insights alert at 80% of per-agent budget; budgets recorded in `infra/parameters/foundry-agent-quotas.yaml`. (R-09)
- [ ] T079 [P] Cache layer: add 5-minute LRU cache on `(corpus_build_sha, query_text, jurisdictions)` key; emit `cache_hit` boolean on `RetrievalResult`. (R-06)

### C — Implementation: citations + audit + hallucination filter

- [ ] T080 [P] Create `apps/agents/common/citation_filter.py` — validates every emitted citation against the live `RetrievalResult.chunks[].sha256_of_chunk` set; mismatched → suppress in card + log `hallucinated_citation` event + downgrade confidence ≥ threshold (planning default 1; revisited per agent in T090–T094) (R-10). (FR-RAG-AG-05, R-10, R-16)
- [ ] T081 Extend `apps/agents/common/audit.py` — write `retrieved_chunks[]`, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `rag_used`, `rag_optout_reason`, `gateway_decision`, `hallucinated_citation_count` on every LLM call (incl. simulation). Append-only Cosmos write + Blob archive (existing 7-year immutability policy reused from spec 030). (FR-RAG-AG-02, FR-RAG-SIM-04, R-13)
- [ ] T082 Add Cosmos `audit_records` container schema migration script `infra/scripts/migrate-audit-record-036.ps1` — additive fields only; preserve existing rows. (FR-RAG-AG-02)
- [ ] T083 Wire `RetrievalService` + `chat_complete` seam + extended `audit.write()` into agent constructors via `apps/agents/maf_runtime/agents/_factory.py` — every grounded agent (`MonitoringAgent`, `RiskAssessmentAgent`, `EvacuationAgent`, `ResourceAllocationAgent`, `CommunicationAgent`) receives the seam in its `__init__`. (FR-RAG-AG-01)
- [ ] T084 [P] Create `packages/ui/src/CitationCard.tsx` — citation rendering with link to `rendered_url` (Markdown) + `source_url` (PDF); confidence badge with WCAG 2.2 AA contrast; collapsible panel with ARIA labels; jurisdiction labels expanded for screen readers ("New South Wales" not "NSW") per Accessibility memo §51–54. (FR-RAG-AG-03, R-14)
- [ ] T085 [P] Create `packages/ui/src/DegradedModeBadge.tsx` (initial scaffold; details land in D4) — banner + stale-cache age countdown. (FR-RAG-LS-02, R-14)
- [ ] T086 Wire `<CitationCard />` into recommendation-card components in `apps/web/src/components/recommendations/`. (FR-RAG-AG-03)
- [ ] T087 [P] Modify Communication agent prompt construction in `apps/agents/.../communication.py` to issue an explicit retrieval call surfacing ATSI / CALD / Auslan / Easy-Read / TIS-National corpus entries before warning composition; gate the resulting draft for human approval (FR-RAG-LS-01, FR-RAG-LS-03). (FR-RAG-AG-06, US8)

### C — Implementation: simulation grounding

- [ ] T088 Create `apps/api/app/services/simulation/citation_sse.py` — SSE `citation` event marshalling per `contracts/citation-envelope.json` shape. (FR-RAG-SIM-02, R-11)
- [ ] T089 Wire `RetrievalService` (the same shared client as the agents) into `controller_service.py` before each chat-turn inference; emit `citation` SSE event(s); on empty result emit `citations: []` + a "no corpus match — recommend operator verification" note; preserve spec-024 rate-limit / comms-block / tenant-isolation / approval workflow unchanged. (FR-RAG-SIM-01, FR-RAG-SIM-02, FR-RAG-SIM-03, FR-RAG-SIM-05)
- [ ] T090 Add simulation audit entries with `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `corpus_build_sha`, `retrieved_chunks[]` (equivalent to FR-RAG-AG-02). (FR-RAG-SIM-04, R-13)
- [ ] T091 Verify scripted-scenario timeline path bypasses `RetrievalService` and emits `# RAG-OPTOUT [FR-RAG-NS-06]` marker; `rag_used: false`, `rag_optout_reason: "scripted-scenario"`. (FR-RAG-SIM-06, FR-RAG-NS-06)

### C — Implementation: per-agent canary flips (R-12 sequencing)

- [ ] T092 [P] Author per-agent golden Q&A fixtures under `apps/eval-runner/fixtures/spec036/{monitoring,risk,evacuation,resource,communication,simulation}.jsonl` — keyed by `(corpus_build_sha, embedding_model_id)`; each fixture asserts decision + schema + expected citation. (FR-RAG-FM-06, R-12, FR-RAG-AG-05 prep)
- [ ] T093 **Canary 1 — Monitoring** (R-12 step 1): flip `foundry_rag_enabled_agents.MonitoringAgent=true` in staging; run `per_agent_canary_gate.py` → assert ≥ 95% decision-equivalence + 100% schema-equivalence; assert spec-014 fallback chain still serves on synthetic Foundry 503; **execute rollback drill** (flip back, assert no audit gap, no operator-visible silencing). Roll out to prod only after staging passes. (FR-RAG-FM-06, R-12, US2)
- [ ] T094 **Canary 2 — Risk Assessment** (R-12 step 2): same gate + rollback drill. (FR-RAG-FM-06, R-12)
- [ ] T095 **Canary 3 — Evacuation** (R-12 step 3): same gate + rollback drill. (FR-RAG-FM-06, R-12)
- [ ] T096 **Canary 4 — Resource Allocation** (R-12 step 4): same gate + rollback drill. (FR-RAG-FM-06, R-12)
- [ ] T097 **Canary 5 — Communication** (R-12 step 5): same gate + rollback drill; explicit ATSI/CALD/Auslan retrieval-coverage assertion (FR-RAG-AG-06, US8). (FR-RAG-FM-06, FR-RAG-AG-06, R-12)
- [ ] T098 [P] Bi-weekly parity-tests review per Risk R11 — automated CI report comparing per-agent legacy-path output vs Foundry-path output on the per-agent fixture; review thread in PR. (FR-RAG-FM-06, Risk R11)
- [ ] T099 [P] Add KQL audit-trail completeness query `tests/audit/audit_trail_completeness.kql` — monthly count of `rag_used` field absent grouped by agent; alert on > 0. Persona-anchor: Compliance Auditor + SRE-memo. (FR-RAG-AG-02, Risk R8)
- [ ] T100 [P] Citation-fidelity assertion in `apps/eval-runner` — extend per-agent canary gate with `citation_fidelity ≥ 0.7` AND `verbatim-source-match` (Phase E3 binds this; introduced here as a non-blocking signal). (FR-RAG-AG-05, Risk R3, Quality-memo R2)
- [ ] T101 [P] WAVE + screen-reader pre-GA accessibility audit checklist for `<CitationCard />` and `<DegradedModeBadge />` — gate before T130. (R-14, Accessibility memo §45–69, Risk R13)
- [ ] T102 [P] Operator persona scenario: NSW DPE Inspector audit-replay in ≤ 60s per recommendation. Persona-anchor: `personas-input/sectors-eastern.md`, `personas-input/operational.md`. (SC-001, SC-011)
- [ ] T103 [P] Operator persona scenario: TAS SES + WA DFES single-agency edge case — verify `DFES-WA` does not silently conflate with state RFS sub-units. Persona-anchor: `personas-input/sectors-southern-western.md`. (FR-RAG-AG-04, SC-010)

**Checkpoint C**: 5/6 grounded surfaces flipped (Monitoring → Communication); Simulation Controller still on legacy path; FR-023 ≥ 95% on each agent; 0 hallucinated citations on 200-prompt suite.

---

## Phase D — RAG-OPTOUT carve-outs + offline cache + multi-jurisdiction QA (M4)

**Goal G4 complete + G5 complete.** Lands the 9 RAG-OPTOUT ADRs + lint, the dual-signed offline cache, the degraded-mode UI, the curated 50-query disambiguation suite, and the hallucinated-citation hardening.

### D — Tests (write red first)

- [ ] T110 [P] Contract test `tests/contract/test_rag_optout_lint.py` — walk every Python module under `apps/agents/` and `apps/api/app/services/`; find `# RAG-OPTOUT [FR-RAG-NS-NN]` markers; assert (i) each marker has a matching `docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-*.md` ADR, (ii) every non-grounded production call site (any `chat_complete` / `LLMClient.generate_response` not preceded by a `retrieval.retrieve` call within the same function body) carries the marker OR is explicitly whitelisted. (FR-RAG-NS-08, SC-008)
- [ ] T111 [P] Entity test `tests/contract/test_rag_optout_adr.py` — every ADR file conforms to the RagOptoutAdr schema (data-model.md §RagOptoutAdr): `Context`, `Decision`, `Audit-log shape`, `Code-comment marker`, `Consequences`. (RagOptoutAdr entity)
- [ ] T112 [P] Integration test `tests/integration/test_offline_cache.py` — cosign + age dual signature verification (fail-closed on either signature failure); 14-day TTL; 11-day "warning" badge; queued offline audit reconciled within 60s with original timestamps preserved on reconnect. (FR-RAG-LS-02, R-04, R-07, SC-009)
- [ ] T113 [P] Contract test `tests/contract/test_offline_cache_manifest.py` — round-trip JSON Schema 2020-12 validation against `contracts/offline-cache-manifest.json`. (FR-RAG-LS-02)
- [ ] T114 [P] Entity test `tests/contract/test_offline_cache_manifest_entity.py` — pydantic-v2 round-trip on OfflineCacheManifest. (OfflineCacheManifest entity)
- [ ] T115 [P] E2E Playwright `tests/e2e/citation_rendering.spec.ts` — Risk Manager + Simulation citation cards visible, expandable, screen-reader friendly. (FR-RAG-AG-03, R-14, Accessibility memo)
- [ ] T116 [P] E2E Playwright `tests/e2e/degraded_mode_badge.spec.ts` — stale-corpus + offline-cache-active + retrieval-unavailable banner UI states. (FR-RAG-LS-02, R-14)
- [ ] T117 [P] Integration test `tests/integration/test_human_approval_preserved.py` — RAG-grounded warning draft + human approval both present in audit; Quality Gates preserved. (FR-RAG-LS-01, FR-RAG-LS-03)

### D — Implementation: nine RAG-OPTOUT ADRs

- [ ] T118 [P] Author `docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md` — Dependency Notifier is a structured-signal pipeline. (FR-RAG-NS-01)
- [ ] T119 [P] Author `02-rag-optout-bom-live.md` — Monitoring agent BoM live-feed path. (FR-RAG-NS-02)
- [ ] T120 [P] Author `03-rag-optout-ga-live.md` — Risk Assessment agent GA seismic-feed path. (FR-RAG-NS-03)
- [ ] T121 [P] Author `04-rag-optout-planning-collection.md` — Planning Officer-aligned pure-data-collection paths. (FR-RAG-NS-04)
- [ ] T122 [P] Author `05-rag-optout-logistics-transactional.md` — Logistics-aligned transactional resource-movement paths. (FR-RAG-NS-05)
- [ ] T123 [P] Author `06-rag-optout-scenario-execution.md` — Resilience Planner scenario-execution paths. (FR-RAG-NS-06; FR-RAG-SIM-06)
- [ ] T124 [P] Author `07-rag-optout-classified.md` — Classified content (ADF DACC > OFFICIAL, AFP classified annex). (FR-RAG-NS-07; Constitution §NN-2)
- [ ] T125 [P] Author `08-rag-optout-ci-lint.md` — ADR for the lint mechanism itself. (FR-RAG-NS-08)
- [ ] T126 [P] Author `09-rag-optout-observer-auditor.md` — Observer-Auditor non-decision paths (read-only, audit-replay, integrity verification). (FR-RAG-NS-09; Quality-memo §No-RAG Opt-Out Audit Trail)

### D — Implementation: opt-out markers + lint binding

- [ ] T127 Apply `# RAG-OPTOUT [FR-RAG-NS-NN]` markers to all 9 production opt-out call sites across `apps/agents/` and `apps/api/`. (FR-RAG-NS-01..09, SC-008)
- [ ] T128 Wire `tests/contract/test_rag_optout_lint.py` into `.github/workflows/ci.yml` as a blocking step. (FR-RAG-NS-08, Quality Gates)

### D — Implementation: offline cache + degraded-mode UI

- [ ] T129 Create `apps/agents/common/offline_cache.py` — verifier loads ≤ 500 MB per-device bundle; **fail-closed** on either signature failure (cosign keyless or `age` detached); 14-day hard TTL; emit `offline_cache_load.success|fail` audit; mode-aware retrieval reads from `OfflineCacheManifest` chunks. (FR-RAG-LS-02, R-04, R-07)
- [ ] T130 Implement `OfflineCacheRetrievalService` (RetrievalService implementation, contracts/retrieval-service.md §1 alt-impl) — reads from signed offline manifest; injected by Field-Coordinator-aligned agent runtime when no AI Search reachability. (FR-RAG-LS-02)
- [ ] T131 [P] Implement queued offline audit replay — local SQLite spool; on reconnect drain to Cosmos within 60s, preserve original timestamps. (FR-RAG-LS-02, SC-009)
- [ ] T132 [P] Telemetry gauge `offline_cache_ttl_days_remaining` + alert at < 3 days; pre-deploy 30-day extended TTL via spec-029 FF override (`field_deployment_extended_ttl: true`) for declared field deployments. (R-07, Quality-memo R3)
- [ ] T133 [P] Build `<DegradedModeBadge />` final implementation in `packages/ui/` — surfaces stale-cache age, offline-cache-active, retrieval-unavailable banner; WCAG 2.2 AA conformance; jurisdiction labels expanded for screen readers. (FR-RAG-LS-02, R-14, Accessibility memo)

### D — Implementation: multi-jurisdiction QA + hallucination hardening

- [ ] T134 [P] Build curated 50-query persona-driven test set `tests/integration/test_jurisdiction_disambiguation.py` (extends T065 fixture) — covers NSW–VIC border, NT–QLD cyclone crossing, ACT–NSW handoff, DFES-WA single-agency, plus 30 additional persona-driven cases sourced from `personas-input/sectors-{commonwealth,crosssector,eastern,southern-western,territories}.md`. (FR-RAG-AG-04, SC-010, US7)
- [ ] T135 [P] Tune hallucinated-citation downgrade threshold per agent (R-10): per-agent `confidence_downgrade_threshold` in `infra/parameters/foundry-agent-quotas.yaml`; default 1; revisit Communication agent post-canary. (FR-RAG-AG-05, R-10)
- [ ] T136 [P] Wire `offline_bundle.py` into ingest-runner schedule — emit per-build offline-cache bundle to Blob `offline-cache-bundles/`; OIDC-signed manifest + `age`-detached signature. (FR-RAG-LS-02, T047)
- [ ] T137 Persona traceability check task — verify every "Top 10" / "Top 5" item from each of the 9 persona memos at `personas-input/{operational,sectors-commonwealth,sectors-crosssector,sectors-eastern,sectors-southern-western,sectors-territories,technical-architecture,technical-delivery,technical-quality}.md` maps to ≥ 1 task in this file (link out via cross-reference index). Output a report `specs/036-foundry-rag-grounding/persona-traceability.md`. (Plan §Phasing anchors)

**Checkpoint D**: all 9 ADRs landed; lint blocks new opt-outs without ADR; offline cache fully signed + reconciles in 60s; 50-query disambiguation suite passes.

---

## Phase E — Final cutover + chaos game-day cadence (M5)

**Goal G6 complete.** The PR that flips the **last** agent ALSO atomically: (a) deletes the legacy Azure-OpenAI path, (b) binds the FR-RAG-FM-04 lint, (c) removes/legacy-tags the legacy Bicep, (d) collapses `_generate_with_fallback` to its template-only branch.

- [ ] T138 [P] **Game-Day 1** (monthly cadence): blue-green alias flip under load + offline-cache fallback under simulated AI Search 503; runbook `docs/runbooks/036-foundry-rag-gameday.md`. (FR-RAG-IDX-04, FR-RAG-LS-02, R7, SRE-memo Top-9)
- [ ] T139 [P] **Game-Day 2** (monthly): offline cache fallback (Field Coordinator deployment + 14-day TTL countdown). (FR-RAG-LS-02, Risk R5)
- [ ] T140 [P] **Game-Day 3** (quarterly): multi-agent canary sequencing under cascading Foundry quota exhaustion; assert spec-014 template fallback covers every agent without silencing. (FR-RAG-FM-06, Risk R2, R-12)
- [ ] T141 [P] Author `docs/runbooks/036-foundry-rag-gameday.md` covering Game-Days 1/2/3 + post-incident replay-within-48h template. (SRE-memo Top-9, R-15-related)
- [ ] T142 Extend `apps/eval-runner` final canary gate query: `decision-equivalence ≥ 95% AND schema-equivalence == 100% AND citation-fidelity ≥ 0.7 AND verbatim-source-match` — keyed by `(corpus_build_sha, embedding_model_id)`. (FR-RAG-FM-06, FR-RAG-AG-05, SC-011, R-13, Quality-memo Top-6)
- [ ] T143 EquivalenceTestResult entity test `tests/contract/test_equivalence_test_result.py` — extends spec-033 FR-023 shape with `citation_fidelity`, `verbatim_source_match`, `corpus_build_sha`, `embedding_model_id`. (EquivalenceTestResult entity, FR-RAG-FM-06)
- [ ] T144 Compliance audit byte-replay automation — sampled SC-011 ≥ 95% reproduction across one-month rolling window; KQL alert on dip. (SC-011, FR-RAG-AG-02, Compliance-memo)
- [ ] T145 **Canary 6 (final) — Simulation Controller**: flip `foundry_rag_enabled_agents.SimulationController=true`; assert FR-023 ≥ 95% on simulation golden Q&A; assert SSE `citation` events emit per grounded turn; rollback drill in staging. (FR-RAG-FM-06, FR-RAG-SIM-01..06, R-12)
- [ ] T146 **Atomic legacy-deletion PR (FR-RAG-FM-04 binds)**: in a single PR — (a) delete the `openai.AzureOpenAI` import path from `apps/agents/common/llm_client.py`, (b) remove the `pytest.mark.skip` from `tests/contract/test_no_openai_imports.py` (T011) so the lint becomes binding, (c) move `infra/modules/azure-openai.bicep` to `infra/modules/legacy/` (per spec-032 deprecation pattern), (d) collapse `_generate_with_fallback` to its template-only branch (Foundry-side regression now degrades to template, never to Azure-OpenAI), (e) drop the `LEGACY_AZURE_OPENAI` env flag. CI MUST pass with all lints binding. (FR-RAG-FM-04, FR-RAG-FM-06, SC-002, Plan §Phase E1, Risk R5)
- [ ] T147 Run `azd up` redeploy in staging then prod — verify `/healthz` endpoint returns `{rag_used: true, corpus_build_sha: <sha>, embedding_model_id: text-embedding-3-large@1, alias_active_index: corpus-vN}`; verify Application Insights `FoundryRAGAudit` table populating; verify SSE citation events on a smoke simulation chat. (Plan §Quickstart Step 9, FR-RAG-IDX-05, FR-RAG-SIM-02)
- [ ] T148 Run quickstart.md end-to-end (§1–§11) on a clean dev environment; capture validation output and append to `specs/036-foundry-rag-grounding/quickstart-validation.md`. (quickstart.md)
- [ ] T149 Final docs sweep: update `README.md` Spec-036 entry; update `CHANGELOG.md`; verify all checklist items in `checklists/{requirements,migration,compliance}.md` are ticked or have a tracking issue. (Plan §Cross-references)
- [ ] T150 Run `/speckit.analyze` to validate cross-artefact consistency before opening the merge PR. (Next-command recommendation)

**Checkpoint E**: zero `from openai` imports in production; spec-014 fallback chain template-only; FR-023 ≥ 95% on every agent + simulation; quickstart validation passes; chaos game-day cadence live.

---

## Dependencies & execution order

### Phase ordering (sequential)

```text
Phase 0 → Phase A → Phase B → Phase C → Phase D → Phase E
```

### Within-phase parallelism

- All `[P]`-marked tasks in the same phase are parallel-safe (different files / no incomplete deps in that phase).
- Within Phase C the canary tasks **T093 → T097** are strictly sequential (one agent flips per sprint per Plan §C8); T145 (Simulation) is the final canary in Phase E.
- Tests within each phase MUST go red **before** the matching implementation tasks land (Quality Gates).
- T146 (legacy-deletion PR) depends on T145 (final canary green) — Plan §E1 atomic-binding rule.

### Critical-path tasks (block multiple phases)

| Task | Blocks |
|---|---|
| T016, T017 (FoundryChatClient + Live impl) | All of Phase A migrations + Phase C retrieval (consumes seam) |
| T028 (`foundry_rag_enabled_agents` FF) | Every canary T093–T097, T145 |
| T029 (per-agent canary gate harness) | Every canary T093–T097, T145 |
| T044 (indexer) | All of Phase C retrieval |
| T045 (manifest + cosign) | T047 offline bundle + T129 verifier |
| T071–T074 (domain models) | All of Phase C + Phase D |
| T127 (markers applied) | T128 lint binding + T146 |
| T145 (final Simulation canary) | T146 atomic legacy-deletion PR |

### Parallel-execution example — Phase C ADRs + retrieval scaffolding

```bash
# Once T071–T074 land, the following can run concurrently:
git worktree add ../wt-citation-card    # T084 [P]
git worktree add ../wt-degraded-badge   # T085 [P]
git worktree add ../wt-jurisdiction-50q # T065 [P]
git worktree add ../wt-hallucination    # T066 + T080 [P]
```

---

## Implementation strategy

### MVP first (US1 + US2-partial + US3 + US4)

1. Complete **Phase 0** (Setup & scaffolding) → workspace builds clean.
2. Complete **Phase A** (Foundry seam + carve-out enforcement) — does **not** flip any agent, only lands the seam + CD gate.
3. Complete **Phase B** (Corpus ingest + blue-green index) — `corpus-v1` published, idempotent re-runs verified.
4. Land **C1–C7 + first canary T093 (Monitoring)** — proves end-to-end grounding on one agent under spec-029 FF + spec-033 FR-023 gate.
5. **STOP and VALIDATE**: Monitoring agent emits citations on grounded paths in prod; rollback drill executed in staging; chaos Game-Day 2 dry-run.

### Incremental delivery (per-agent canaries)

1. T094 (Risk) → STOP / VALIDATE → demo.
2. T095 (Evacuation) → STOP / VALIDATE → demo.
3. T096 (Resource) → STOP / VALIDATE → demo.
4. T097 (Communication, with US8 ATSI/CALD coverage) → STOP / VALIDATE → demo.
5. Phase D in parallel with the slower canaries (different files / different teams).
6. T145 (Simulation, final canary) → T146 atomic legacy-deletion PR.

### Parallel-team strategy

- Team A — Phase A migrations (T016–T030).
- Team B — Phase B ingest + blue-green (T031–T058).
- Team C — Phase C retrieval + UI (T060–T091, T101).
- Team D — Phase D ADRs + offline cache + a11y (T110–T137).
- SRE/QA — Phase E game-day runbooks + final canary (T138–T150).

---

## Cross-reference index

### Functional Requirements → tasks

| FR | Implementation task(s) | Test task(s) |
|---|---|---|
| FR-RAG-FM-01 | T018, T021 | T010 |
| FR-RAG-FM-02 | T019 | T010 |
| FR-RAG-FM-03 | T020, T089 | T010, T068 |
| FR-RAG-FM-04 | T011 (skip→bind), T146 | T011 |
| FR-RAG-FM-05 | T017, T021 | T010 |
| FR-RAG-FM-06 | T028, T029, T030, T093–T097, T145, T146 | T015, T143 |
| FR-RAG-FM-07 | T016, T017 | T010 |
| FR-RAG-CV-01 | T024, T025, T027, T057 | T012, T013 |
| FR-RAG-CV-02 | T024, T026 | T012, T013 |
| FR-RAG-CV-03 | T022, T023 | T014 |
| FR-RAG-CV-04 | T023, T024 | T013 |
| FR-RAG-IDX-01 | T002, T040, T050 | T035 |
| FR-RAG-IDX-02 | T041, T042, T043 | T031, T036, T037 |
| FR-RAG-IDX-03 | T044, T045, T056 | T036 |
| FR-RAG-IDX-04 | T044, T046, T048 | T031, T032, T033, T034 |
| FR-RAG-IDX-05 | T050, T052, T053, T147 | T032 |
| FR-RAG-IDX-06 | T049, T051 | — (deploy-time CI) |
| FR-RAG-IDX-07 | T054, T055 | T039 |
| FR-RAG-IDX-08 | T044, T049 | T038 |
| FR-RAG-AG-01 | T075, T076, T083 | T060 |
| FR-RAG-AG-02 | T073, T081, T082 | T062, T069, T099 |
| FR-RAG-AG-03 | T072, T084, T086 | T061, T064, T115 |
| FR-RAG-AG-04 | T076, T134 | T065 |
| FR-RAG-AG-05 | T080, T100, T135, T142 | T066 |
| FR-RAG-AG-06 | T087 | T067 |
| FR-RAG-NS-01 | T118, T127 | T110 |
| FR-RAG-NS-02 | T119, T127 | T110 |
| FR-RAG-NS-03 | T120, T127 | T110 |
| FR-RAG-NS-04 | T121, T127 | T110 |
| FR-RAG-NS-05 | T122, T127 | T110 |
| FR-RAG-NS-06 | T091, T123, T127 | T110 |
| FR-RAG-NS-07 | T077, T124, T127 | T070, T110 |
| FR-RAG-NS-08 | T125, T128 | T110 |
| FR-RAG-NS-09 | T126, T127 | T110 |
| FR-RAG-SIM-01 | T089 | T068 |
| FR-RAG-SIM-02 | T088, T089 | T061, T068 |
| FR-RAG-SIM-03 | T089 | T068 |
| FR-RAG-SIM-04 | T090 | T062, T068 |
| FR-RAG-SIM-05 | T089 (preserve) | T068 |
| FR-RAG-SIM-06 | T091, T123 | T068 |
| FR-RAG-LS-01 | T087, T089 | T117 |
| FR-RAG-LS-02 | T047, T074, T085, T129–T133, T136 | T112, T113, T114, T116 |
| FR-RAG-LS-03 | T087 | T117 |

### Research decisions → tasks

| R-NN | Tasks |
|---|---|
| R-01 (Foundry SDK + AAD scope) | T001, T016, T017, T021 |
| R-02 (Embedding model + dims) | T042, T049 |
| R-03 (Single index + jurisdiction filter) | T060, T065, T076 |
| R-04 (Chunking strategy) | T003, T031, T041, T129 |
| R-05 (Parity gate signals) | T031, T033, T034, T046 |
| R-06 (Hybrid retrieval + RRF + cache) | T060, T075, T079 |
| R-07 (Offline cache stale-age + sig) | T112, T129, T132 |
| R-08 (ingest-runner as new Container Apps Job) | T002, T040 |
| R-09 (Per-agent quota budget) | T078 |
| R-10 (Hallucinated-citation downgrade) | T038, T041, T066, T080, T135 |
| R-11 (Citation envelope wire shape) | T061, T072, T088 |
| R-12 (Canary sequencing order) | T028, T030, T093–T097, T140, T145 |
| R-13 (Embedding-call audit shape) | T056, T069, T073, T081, T142, T144 |
| R-14 (UX choices — cards + banner + a11y) | T084, T085, T101, T115, T116, T133 |
| R-15 (Bicep wrapper for blue-green) | T044, T048, T141 |
| R-16 (Confidence model) | T064, T072, T080 |

### Contract files → tasks

| Contract | Implementation tasks | Contract test |
|---|---|---|
| `contracts/retrieval-service.md` | T075, T076, T077 | T060 |
| `contracts/foundry-chat-client.md` | T016, T017 | T010 |
| `contracts/ingest-pipeline.md` | T040–T046 | T031 |
| `contracts/citation-envelope.json` | T072 | T061, T064 |
| `contracts/audit-record-llm-call.json` | T073, T081 | T062 |
| `contracts/offline-cache-manifest.json` | T074, T129 | T113, T114 |

### Entities → tasks

| Entity | Implementation | Entity test |
|---|---|---|
| CorpusEntry | T040, T054 (read-only) | T035 |
| Chunk | T044 | T036 |
| RetrievalRequest | T071 | T063 |
| RetrievalResult | T071 | T063 |
| Citation | T072 | T064 |
| AuditRecord | T073, T081, T082 | T062 |
| CarveoutRegistryEntry | T024, T025, T027 | T012 |
| OfflineCacheManifest | T074, T129 | T114 |
| RagOptoutAdr | T118–T126 | T111 |
| EquivalenceTestResult | T029, T142 | T143 |

### Persona-memo coverage

| Memo | Anchored tasks |
|---|---|
| `technical-architecture.md` (Top-1/2/3/4/5/8/9) | T016, T044, T048, T060, T075, T078, T140 |
| `technical-delivery.md` (Top-1..10) | T018, T020, T024, T026, T040–T053, T093–T097, T146 |
| `technical-quality.md` (Top-1..10) | T010, T015, T029, T060, T066, T099, T101, T138–T142 |
| `operational.md` | T065, T087, T097, T102, T117 |
| `sectors-commonwealth.md` | T065, T134 |
| `sectors-crosssector.md` | T065, T134 |
| `sectors-eastern.md` | T065, T102, T134 |
| `sectors-southern-western.md` | T103, T134 |
| `sectors-territories.md` | T065, T134 |
| Persona traceability output | T137 |

### Risk register → tasks

| Risk | Mitigation tasks |
|---|---|
| R1 (embedding-model drift) | T034, T046 (signal 4) |
| R2 (Foundry quota exhaustion) | T078, T030, T140 |
| R3 (citation hallucination) | T080, T100, T135, T142 |
| R4 (offline-cache integrity) | T003, T112, T129 |
| R5 (agent silencing during cutover) | T018, T028, T029, T139, T146 |
| R6 (offline-cache stale-age policy) | T132 |
| R7 (alias flip timeout under load) | T033, T138 |
| R8 (audit-trail incompleteness) | T062, T099, T144 |
| R9 (seam leakage to prod) | T010 |
| R10 (chunking truncation) | T038, T041 |
| R11 (backward-compat debt) | T098, T146 |
| R12 (carve-out registry drift) | T012, T013, T024 |
| R13 (citation a11y regression) | T084, T101, T115, T116, T133 |

### Success Criteria → tasks

| SC | Tasks |
|---|---|
| SC-001 (100% citation on grounded paths) | T086, T093–T097, T102 |
| SC-002 (0 OpenAI imports post-cutover) | T011, T146 |
| SC-003 (registry coverage) | T013, T024, T027 |
| SC-004 (no non-AU data plane) | T013, T024 |
| SC-005 (idempotent ingest ≤ 10%) | T032 |
| SC-006 (licence-mode honoured) | T037, T043 |
| SC-007 (sim 0 fabricated citations) | T066, T068 |
| SC-008 (RAG-OPTOUT lint enforced) | T110, T128 |
| SC-009 (offline reconciled in 60s) | T112, T131 |
| SC-010 (50-query disambiguation) | T065, T134 |
| SC-011 (audit byte-replay ≥ 95%) | T069, T144 |
| SC-012 (sim latency ≤ 30% growth) | T068 |

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks within the same phase.
- Every task is concrete enough that `/speckit.implement` can execute it without further clarification (file paths + FR/R-NN refs explicit).
- Tests precede implementation **within each phase** (red-green-refactor); the canary tasks T093–T097 + T145 are gated on the equivalence harness running green.
- T011 + T146 form the **atomic FR-RAG-FM-04 binding pair** — the lint test is created skip-marked in Phase A and made binding only inside the same PR that deletes the legacy client (Plan §Phase E1).
- T030 + T093–T097 + T145 are the spec-029 FF + spec-033 FR-023 wiring path — every flip carries an explicit rollback drill assertion.
- The `from openai` import lint (T011) carries an allowlist for opt-out paths (`tests/`, `docs/`, `apps/eval-runner/` historical references) per FR-RAG-NS-08 design.

---

*End of tasks.md — **Next command**: `/speckit.analyze` (cross-artefact consistency + readiness gate).*

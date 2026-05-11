---
description: "Dependency-ordered task list for spec 036 — Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat"
---

# Tasks: Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat

**Branch**: `036-foundry-rag-grounding` | **Date**: 2026-05-08 | **Spec**: [`spec.md`](./spec.md) | **Plan**: [`plan.md`](./plan.md)
**Inputs**: [`research.md`](./research.md) (16 R-NN decisions + R-17..R-24 ADR-anchored), [`data-model.md`](./data-model.md) (10 entities + R3 amend-loop additions), [`contracts/`](./contracts/) (6 contract artefacts; 5 NEW + 1 EXTENDED), [`quickstart.md`](./quickstart.md), [`spec.md`](./spec.md) (**68 FRs, 10 USs, 19 SCs** post-R3 amend-loop: 43 + 25 new R3 FRs; 8 + 2 new R3 USs; 12 + 7 new R3 SCs), persona memos at `personas-input/{operational,sectors-*,technical-*}.md`.

**Tests**: Tests are mandatory in this spec (Constitution §Quality Gates + spec 030 test pyramid). Every FR carries ≥ 1 test task. Tests within a phase MUST be authored (red) before the implementation tasks they cover (green).

**Format**: `- [ ] T### [P?] Description (file path + FR/R/SC/US references)` — `[P]` marks tasks that are parallel-safe (different files / no incomplete deps). Phases A–E run **sequentially** (per plan.md §Phasing); within a phase, `[P]` tasks may run concurrently. Phase 0 is the cross-cutting setup phase.

---

## Front-matter — task metrics

| Bucket | Count |
|---|---|
| **Total tasks (Phases 0–E)** | **140** (pre-amend-loop) |
| **Total tasks (Phase F)** | **101** (R3 amend-loop; T151–T251) |
| **Grand total** | **241** (T001–T251 minus 10 known gaps at T7–T9, T59, T104–T109) |
| Phase 0 (Setup) | 6 |
| Phase A (Foundry seam + carve-out enforcement) | 21 |
| Phase B (Corpus ingest + blue-green index) | 28 |
| Phase C (Shared retrieval + per-agent grounding + simulation grounding) | 44 |
| Phase D (RAG-OPTOUT + offline cache + multi-jurisdiction QA) | 28 |
| Phase E (Final cutover + chaos game-day cadence) | 13 |
| Phase F (R3 amend-loop; A1–A12 + ADR bodies) | 101 — see line 528 sub-table |
| **Parallel-safe `[P]` tasks** | **93** (Phases 0–E) — Phase F additions tagged `[P]` per task |

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

- [X] T060 [P] Contract test `tests/contract/test_retrieval_service.py` — `RetrievalService` Protocol shape; `RetrievalRequest` / `RetrievalResult` / `RetrievedChunk` schema validation; jurisdiction-union semantics (own ∪ national ∪ aidr); RRF default vector 0.7 / lexical 0.3; empty-result handling; classification-ceiling enforcement. (contracts/retrieval-service.md, FR-RAG-AG-01, FR-RAG-AG-04, R-03, R-06)
- [X] T061 [P] Contract test `tests/contract/test_citation_envelope.py` — round-trip JSON Schema 2020-12 validation against `contracts/citation-envelope.json`; required fields: `jurisdiction`, `topic`, `page`, `source_url`, `sha256_of_chunk`, `confidence`. (FR-RAG-AG-03, FR-RAG-SIM-02, R-11, R-16)
- [X] T062 [P] Contract test `tests/contract/test_audit_record_shape.py` — round-trip JSON Schema 2020-12 validation against `contracts/audit-record-llm-call.json`; required fields per FR-RAG-AG-02; opt-out shape: `rag_used == false` requires `rag_optout_reason` + `adr_pointer`. (FR-RAG-AG-02, FR-RAG-NS-01..09, FR-RAG-SIM-04, R-13)
- [X] T063 [P] Entity test `tests/contract/test_retrieval_request_response.py` — pydantic-v2 round-trip; `min_length=1` jurisdictions; `top_k ∈ [1, 20]`; `classification_max == "OFFICIAL"`. (RetrievalRequest/RetrievalResult)
- [X] T064 [P] Entity test `tests/contract/test_citation_entity.py` — pydantic-v2 round-trip; `confidence ∈ [0.0, 1.0]`; forbids `text` when `licence_mode == "metadata-only"`. (Citation)
- [X] T065 [P] Integration test `tests/integration/test_jurisdiction_disambiguation.py` — curated 50-query persona-driven set covering NSW–VIC border (RFS vs CFA-VIC; FRNSW vs FRV), NT–QLD cyclone (NTES vs SES-QLD), ACT–NSW handoff (ACT RFS vs NSW RFS, AFP-ACT vs NSW Police), DFES-WA single-agency edge cases; assert 0 silent conflations. (FR-RAG-AG-04, SC-010, US7, R-03)
- [X] T066 [P] Integration test `tests/integration/test_hallucinated_citation_suppression.py` — 200-prompt jailbreak/hallucination suite; assert 0 hallucinated citations rendered to operators; `hallucinated_citation_count` audit field populated. (FR-RAG-AG-05, SC-007, R-10)
- [X] T067 [P] Integration test `tests/integration/test_communication_agent_atsi_cald.py` — vulnerable-population scenario (e.g. NSW NW flood with high CALD census + 2 ATSI communities) → retrieval surfaces ATSI/CALD/Auslan/Easy-Read/TIS-National corpus entries before composition. (FR-RAG-AG-06, US8)
- [X] T068 [P] Integration test `tests/integration/test_simulation_sse_citation.py` — drive a simulation chat turn → assert SSE `citation` event emitted per grounded reply (FR-RAG-SIM-02); assert empty-result emits `citations: []` + "no corpus match" note (FR-RAG-SIM-03); assert audit shape per FR-RAG-SIM-04; assert spec-024 rate-limit / comms-block / tenant-isolation / approval workflow preserved (FR-RAG-SIM-05); assert latency p95 ≤ 1.3 × spec-024 baseline. (FR-RAG-SIM-01, FR-RAG-SIM-02, FR-RAG-SIM-03, FR-RAG-SIM-04, FR-RAG-SIM-05, FR-RAG-SIM-06, SC-007, SC-012)
- [X] T069 [P] Integration test `tests/integration/test_audit_replay.py` — given `(corpus_build_sha, prompt_sha, model_version, retrieved_chunks_set)`, replay reproduces byte-identical retrieval inputs ≥ 95% across one-month window. (FR-RAG-AG-02, SC-011, R-13)
- [X] T070 [P] Integration test `tests/integration/test_classification_ceiling.py` — request with `classification_max` ≠ `OFFICIAL` → `RetrievalService.retrieve` raises `ClassificationCeilingError`. (FR-RAG-NS-07, contracts/retrieval-service.md §2.5)

### C — Implementation: domain models + retrieval

- [X] T071 [P] Implement `packages/domain/src/ama_domain/retrieval.py` — `RetrievalRequest`, `RetrievalResult`, `RetrievedChunk`, `Jurisdiction`, `LicenceMode` (data-model.md §RetrievalRequest, §RetrievalResult). (RetrievalRequest, RetrievalResult entities)
- [X] T072 [P] Implement `packages/domain/src/ama_domain/citation.py` — Citation pydantic-v2 mirror of `contracts/citation-envelope.json`. (Citation entity, R-11)
- [X] T073 [P] Extend `packages/domain/src/ama_domain/audit_record.py` — additive fields per data-model.md §AuditRecord: `retrieved_chunks: list[RetrievedChunkRef]`, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `rag_used: bool`, `rag_optout_reason: str | None`, `gateway_decision: Literal["allow","deny","redact"]`, `hallucinated_citation_count: int`, `adr_pointer: str | None`. (AuditRecord entity, FR-RAG-AG-02, R-13)
- [X] T074 [P] Implement `packages/domain/src/ama_domain/offline_cache.py` — pydantic-v2 mirror of `contracts/offline-cache-manifest.json`; dual-signature fields. (OfflineCacheManifest entity, FR-RAG-LS-02)
- [X] T075 Create `apps/agents/common/retrieval_client.py` — `AzureSearchRetrievalService(RetrievalService)` implementing the Protocol; uses `azure-search-documents` async client + Foundry-embedded query vectors (via injected `chat_complete` seam); RRF (decision [R-06](./research.md): default vector 0.7 / lexical 0.3); top-k default 5 (configurable per agent). (FR-RAG-AG-01, R-06)
- [X] T076 Add jurisdiction-union expansion in `AzureSearchRetrievalService.retrieve()` — input `jurisdictions=["nsw"]` → effective filter `jurisdiction in ("nsw","national","aidr")`. (FR-RAG-AG-04, R-03, US7)
- [X] T077 Add classification-ceiling check in `AzureSearchRetrievalService.retrieve()` — `request.classification_max != "OFFICIAL"` → raise `ClassificationCeilingError` (FR-RAG-NS-07). (FR-RAG-NS-07)
- [X] T078 [P] Per-agent quota governance (R-09): emit `Foundry.TokensPerSecond` metric tagged with `agent_name`; configure Application Insights alert at 80% of per-agent budget; budgets recorded in `infra/parameters/foundry-agent-quotas.yaml`. (R-09)
- [X] T079 [P] Cache layer: add 5-minute LRU cache on `(corpus_build_sha, query_text, jurisdictions)` key; emit `cache_hit` boolean on `RetrievalResult`. (R-06)

### C — Implementation: citations + audit + hallucination filter

- [X] T080 [P] Create `apps/agents/common/citation_filter.py` — validates every emitted citation against the live `RetrievalResult.chunks[].sha256_of_chunk` set; mismatched → suppress in card + log `hallucinated_citation` event + downgrade confidence ≥ threshold (planning default 1; revisited per agent in T090–T094) (R-10). (FR-RAG-AG-05, R-10, R-16)
- [X] T081 Extend `apps/agents/common/audit.py` — write `retrieved_chunks[]`, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `rag_used`, `rag_optout_reason`, `gateway_decision`, `hallucinated_citation_count` on every LLM call (incl. simulation). Append-only Cosmos write + Blob archive (existing 7-year immutability policy reused from spec 030). (FR-RAG-AG-02, FR-RAG-SIM-04, R-13)
- [X] T082 Add Cosmos `audit_records` container schema migration script `infra/scripts/migrate-audit-record-036.ps1` — additive fields only; preserve existing rows. (FR-RAG-AG-02)
- [X] T083 Wire `RetrievalService` + `chat_complete` seam + extended `audit.write()` into agent constructors via `apps/agents/maf_runtime/agents/_factory.py` — every grounded agent (`MonitoringAgent`, `RiskAssessmentAgent`, `EvacuationAgent`, `ResourceAllocationAgent`, `CommunicationAgent`) receives the seam in its `__init__`. (FR-RAG-AG-01)
- [X] T084 [P] Create `packages/ui/src/CitationCard.tsx` — citation rendering with link to `rendered_url` (Markdown) + `source_url` (PDF); confidence badge with WCAG 2.2 AA contrast; collapsible panel with ARIA labels; jurisdiction labels expanded for screen readers ("New South Wales" not "NSW") per Accessibility memo §51–54. (FR-RAG-AG-03, R-14)
- [X] T085 [P] Create `packages/ui/src/DegradedModeBadge.tsx` (initial scaffold; details land in D4) — banner + stale-cache age countdown. (FR-RAG-LS-02, R-14)
- [X] T086 Wire `<CitationCard />` into recommendation-card components in `apps/web/src/components/recommendations/`. (FR-RAG-AG-03)
- [X] T087 [P] Modify Communication agent prompt construction in `apps/agents/.../communication.py` to issue an explicit retrieval call surfacing ATSI / CALD / Auslan / Easy-Read / TIS-National corpus entries before warning composition; gate the resulting draft for human approval (FR-RAG-LS-01, FR-RAG-LS-03). (FR-RAG-AG-06, US8)

### C — Implementation: simulation grounding

- [X] T088 Create `apps/api/app/services/simulation/citation_sse.py` — SSE `citation` event marshalling per `contracts/citation-envelope.json` shape. (FR-RAG-SIM-02, R-11)
- [X] T089 Wire `RetrievalService` (the same shared client as the agents) into `controller_service.py` before each chat-turn inference; emit `citation` SSE event(s); on empty result emit `citations: []` + a "no corpus match — recommend operator verification" note; preserve spec-024 rate-limit / comms-block / tenant-isolation / approval workflow unchanged. (FR-RAG-SIM-01, FR-RAG-SIM-02, FR-RAG-SIM-03, FR-RAG-SIM-05)
- [X] T090 Add simulation audit entries with `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `corpus_build_sha`, `retrieved_chunks[]` (equivalent to FR-RAG-AG-02). (FR-RAG-SIM-04, R-13)
- [X] T091 Verify scripted-scenario timeline path bypasses `RetrievalService` and emits `# RAG-OPTOUT [FR-RAG-NS-06]` marker; `rag_used: false`, `rag_optout_reason: "scripted-scenario"`. (FR-RAG-SIM-06, FR-RAG-NS-06)

### C — Implementation: per-agent canary flips (R-12 sequencing)

- [X] T092 [P] Author per-agent golden Q&A fixtures under `apps/eval-runner/fixtures/spec036/{monitoring,risk,evacuation,resource,communication,simulation}.jsonl` — keyed by `(corpus_build_sha, embedding_model_id)`; each fixture asserts decision + schema + expected citation. (FR-RAG-FM-06, R-12, FR-RAG-AG-05 prep)
- [~] T093 **Canary 1 — Monitoring** (R-12 step 1): flip `foundry_rag_enabled_agents.MonitoringAgent=true` in staging; run `per_agent_canary_gate.py` → assert ≥ 95% decision-equivalence + 100% schema-equivalence; assert spec-014 fallback chain still serves on synthetic Foundry 503; **execute rollback drill** (flip back, assert no audit gap, no operator-visible silencing). Roll out to prod only after staging passes. _Phase C status: code green via `infra/scripts/canary-rollback-drill.ps1` + playbook `docs/canary/036-per-agent-canary.md`; pending live env-var flip in workflow Step 9._ (FR-RAG-FM-06, R-12, US2)
- [~] T094 **Canary 2 — Risk Assessment** (R-12 step 2): same gate + rollback drill. _Phase C status: code green; pending live flip._ (FR-RAG-FM-06, R-12)
- [~] T095 **Canary 3 — Evacuation** (R-12 step 3): same gate + rollback drill. _Phase C status: code green; pending live flip._ (FR-RAG-FM-06, R-12)
- [~] T096 **Canary 4 — Resource Allocation** (R-12 step 4): same gate + rollback drill. _Phase C status: code green; pending live flip._ (FR-RAG-FM-06, R-12)
- [~] T097 **Canary 5 — Communication** (R-12 step 5): same gate + rollback drill; explicit ATSI/CALD/Auslan retrieval-coverage assertion (FR-RAG-AG-06, US8). _Phase C status: code green; pending live flip._ (FR-RAG-FM-06, FR-RAG-AG-06, R-12)
- [X] T098 [P] Bi-weekly parity-tests review per Risk R11 — automated CI report comparing per-agent legacy-path output vs Foundry-path output on the per-agent fixture; review thread in PR. (FR-RAG-FM-06, Risk R11)
- [X] T099 [P] Add KQL audit-trail completeness query `tests/audit/audit_trail_completeness.kql` — monthly count of `rag_used` field absent grouped by agent; alert on > 0. Persona-anchor: Compliance Auditor + SRE-memo. (FR-RAG-AG-02, Risk R8)
- [X] T100 [P] Citation-fidelity assertion in `apps/eval-runner` — extend per-agent canary gate with `citation_fidelity ≥ 0.7` AND `verbatim-source-match` (Phase E3 binds this; introduced here as a non-blocking signal). (FR-RAG-AG-05, Risk R3, Quality-memo R2)
- [X] T101 [P] WAVE + screen-reader pre-GA accessibility audit checklist for `<CitationCard />` and `<DegradedModeBadge />` — gate before T130. (R-14, Accessibility memo §45–69, Risk R13)
- [X] T102 [P] Operator persona scenario: NSW DPE Inspector audit-replay in ≤ 60s per recommendation. Persona-anchor: `personas-input/sectors-eastern.md`, `personas-input/operational.md`. (SC-001, SC-011)
- [X] T103 [P] Operator persona scenario: TAS SES + WA DFES single-agency edge case — verify `DFES-WA` does not silently conflate with state RFS sub-units. Persona-anchor: `personas-input/sectors-southern-western.md`. (FR-RAG-AG-04, SC-010)

**Checkpoint C**: 5/6 grounded surfaces flipped (Monitoring → Communication); Simulation Controller still on legacy path; FR-023 ≥ 95% on each agent; 0 hallucinated citations on 200-prompt suite.

---

## Phase D — RAG-OPTOUT carve-outs + offline cache + multi-jurisdiction QA (M4)

**Goal G4 complete + G5 complete.** Lands the 9 RAG-OPTOUT ADRs + lint, the dual-signed offline cache, the degraded-mode UI, the curated 50-query disambiguation suite, and the hallucinated-citation hardening.

### D — Tests (write red first)

- [X] T110 [P] Contract test `tests/contract/test_rag_optout_lint.py` — walk every Python module under `apps/agents/` and `apps/api/app/services/`; find `# RAG-OPTOUT [FR-RAG-NS-NN]` markers; assert (i) each marker has a matching `docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-*.md` ADR, (ii) every non-grounded production call site (any `chat_complete` / `LLMClient.generate_response` not preceded by a `retrieval.retrieve` call within the same function body) carries the marker OR is explicitly whitelisted. (FR-RAG-NS-08, SC-008)
- [X] T111 [P] Entity test `tests/contract/test_rag_optout_adr.py` — every ADR file conforms to the RagOptoutAdr schema (data-model.md §RagOptoutAdr): `Context`, `Decision`, `Audit-log shape`, `Code-comment marker`, `Consequences`. (RagOptoutAdr entity)
- [X] T112 [P] Integration test `tests/integration/test_offline_cache.py` — cosign + age dual signature verification (fail-closed on either signature failure); 14-day TTL; 11-day "warning" badge; queued offline audit reconciled within 60s with original timestamps preserved on reconnect. (FR-RAG-LS-02, R-04, R-07, SC-009)
- [X] T113 [P] Contract test `tests/contract/test_offline_cache_manifest.py` — round-trip JSON Schema 2020-12 validation against `contracts/offline-cache-manifest.json`. (FR-RAG-LS-02)
- [X] T114 [P] Entity test `tests/contract/test_offline_cache_manifest_entity.py` — pydantic-v2 round-trip on OfflineCacheManifest. (OfflineCacheManifest entity)
- [X] T115 [P] E2E Playwright `tests/e2e/citation_rendering.spec.ts` — Risk Manager + Simulation citation cards visible, expandable, screen-reader friendly. (FR-RAG-AG-03, R-14, Accessibility memo)
- [X] T116 [P] E2E Playwright `tests/e2e/degraded_mode_badge.spec.ts` — stale-corpus + offline-cache-active + retrieval-unavailable banner UI states. (FR-RAG-LS-02, R-14)
- [X] T117 [P] Integration test `tests/integration/test_human_approval_preserved.py` — RAG-grounded warning draft + human approval both present in audit; Quality Gates preserved. (FR-RAG-LS-01, FR-RAG-LS-03)

### D — Implementation: nine RAG-OPTOUT ADRs

- [X] T118 [P] Author `docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md` — Dependency Notifier is a structured-signal pipeline. (FR-RAG-NS-01)
- [X] T119 [P] Author `02-rag-optout-bom-live.md` — Monitoring agent BoM live-feed path. (FR-RAG-NS-02)
- [X] T120 [P] Author `03-rag-optout-ga-live.md` — Risk Assessment agent GA seismic-feed path. (FR-RAG-NS-03)
- [X] T121 [P] Author `04-rag-optout-planning-collection.md` — Planning Officer-aligned pure-data-collection paths. (FR-RAG-NS-04)
- [X] T122 [P] Author `05-rag-optout-logistics-transactional.md` — Logistics-aligned transactional resource-movement paths. (FR-RAG-NS-05)
- [X] T123 [P] Author `06-rag-optout-scenario-execution.md` — Resilience Planner scenario-execution paths. (FR-RAG-NS-06; FR-RAG-SIM-06)
- [X] T124 [P] Author `07-rag-optout-classified.md` — Classified content (ADF DACC > OFFICIAL, AFP classified annex). (FR-RAG-NS-07; Constitution §NN-2)
- [X] T125 [P] Author `08-rag-optout-ci-lint.md` — ADR for the lint mechanism itself. (FR-RAG-NS-08)
- [X] T126 [P] Author `09-rag-optout-observer-auditor.md` — Observer-Auditor non-decision paths (read-only, audit-replay, integrity verification). (FR-RAG-NS-09; Quality-memo §No-RAG Opt-Out Audit Trail)

### D — Implementation: opt-out markers + lint binding

- [X] T127 Apply `# RAG-OPTOUT [FR-RAG-NS-NN]` markers to all 9 production opt-out call sites across `apps/agents/` and `apps/api/`. (FR-RAG-NS-01..09, SC-008)
- [X] T128 Wire `tests/contract/test_rag_optout_lint.py` into `.github/workflows/ci.yml` as a blocking step. (FR-RAG-NS-08, Quality Gates)

### D — Implementation: offline cache + degraded-mode UI

- [X] T129 Create `apps/agents/common/offline_cache.py` — verifier loads ≤ 500 MB per-device bundle; **fail-closed** on either signature failure (cosign keyless or `age` detached); 14-day hard TTL; emit `offline_cache_load.success|fail` audit; mode-aware retrieval reads from `OfflineCacheManifest` chunks. (FR-RAG-LS-02, R-04, R-07)
- [X] T130 Implement `OfflineCacheRetrievalService` (RetrievalService implementation, contracts/retrieval-service.md §1 alt-impl) — reads from signed offline manifest; injected by Field-Coordinator-aligned agent runtime when no AI Search reachability. (FR-RAG-LS-02)
- [X] T131 [P] Implement queued offline audit replay — local SQLite spool; on reconnect drain to Cosmos within 60s, preserve original timestamps. (FR-RAG-LS-02, SC-009)
- [X] T132 [P] Telemetry gauge `offline_cache_ttl_days_remaining` + alert at < 3 days; pre-deploy 30-day extended TTL via spec-029 FF override (`field_deployment_extended_ttl: true`) for declared field deployments. (R-07, Quality-memo R3)
- [X] T133 [P] Build `<DegradedModeBadge />` final implementation in `packages/ui/` — surfaces stale-cache age, offline-cache-active, retrieval-unavailable banner; WCAG 2.2 AA conformance; jurisdiction labels expanded for screen readers. (FR-RAG-LS-02, R-14, Accessibility memo)

### D — Implementation: multi-jurisdiction QA + hallucination hardening

- [X] T134 [P] Build curated 50-query persona-driven test set `tests/integration/test_jurisdiction_disambiguation.py` (extends T065 fixture) — covers NSW–VIC border, NT–QLD cyclone crossing, ACT–NSW handoff, DFES-WA single-agency, plus 30 additional persona-driven cases sourced from `personas-input/sectors-{commonwealth,crosssector,eastern,southern-western,territories}.md`. (FR-RAG-AG-04, SC-010, US7)
- [X] T135 [P] Tune hallucinated-citation downgrade threshold per agent (R-10): per-agent `confidence_downgrade_threshold` in `infra/parameters/foundry-agent-quotas.yaml`; default 1; revisit Communication agent post-canary. (FR-RAG-AG-05, R-10)
- [X] T136 [P] Wire `offline_bundle.py` into ingest-runner schedule — emit per-build offline-cache bundle to Blob `offline-cache-bundles/`; OIDC-signed manifest + `age`-detached signature. (FR-RAG-LS-02, T047)
- [X] T137 Persona traceability check task — verify every "Top 10" / "Top 5" item from each of the 9 persona memos at `personas-input/{operational,sectors-commonwealth,sectors-crosssector,sectors-eastern,sectors-southern-western,sectors-territories,technical-architecture,technical-delivery,technical-quality}.md` maps to ≥ 1 task in this file (link out via cross-reference index). Output a report `specs/036-foundry-rag-grounding/persona-traceability.md`. (Plan §Phasing anchors)

**Checkpoint D**: all 9 ADRs landed; lint blocks new opt-outs without ADR; offline cache fully signed + reconciles in 60s; 50-query disambiguation suite passes.

---

## Phase E — Final cutover + chaos game-day cadence (M5)

**Goal G6 complete.** The PR that flips the **last** agent ALSO atomically: (a) deletes the legacy Azure-OpenAI path, (b) binds the FR-RAG-FM-04 lint, (c) removes/legacy-tags the legacy Bicep, (d) collapses `_generate_with_fallback` to its template-only branch.

- [X] T138 [P] **Game-Day 1** (monthly cadence): blue-green alias flip under load + offline-cache fallback under simulated AI Search 503; runbook `docs/runbooks/036-foundry-rag-gameday.md`. (FR-RAG-IDX-04, FR-RAG-LS-02, R7, SRE-memo Top-9)
- [X] T139 [P] **Game-Day 2** (monthly): offline cache fallback (Field Coordinator deployment + 14-day TTL countdown). (FR-RAG-LS-02, Risk R5)
- [X] T140 [P] **Game-Day 3** (quarterly): multi-agent canary sequencing under cascading Foundry quota exhaustion; assert spec-014 template fallback covers every agent without silencing. (FR-RAG-FM-06, Risk R2, R-12)
- [X] T141 [P] Author `docs/runbooks/036-foundry-rag-gameday.md` covering Game-Days 1/2/3 + post-incident replay-within-48h template. (SRE-memo Top-9, R-15-related)
- [X] T142 Extend `apps/eval-runner` final canary gate query: `decision-equivalence ≥ 95% AND schema-equivalence == 100% AND citation-fidelity ≥ 0.7 AND verbatim-source-match` — keyed by `(corpus_build_sha, embedding_model_id)`. (FR-RAG-FM-06, FR-RAG-AG-05, SC-011, R-13, Quality-memo Top-6) — *Phase E: ``run_final_canary_gate`` + ``FinalCanaryGateResult`` in ``apps/eval-runner/src/ama_eval/per_agent_canary_gate.py``; tests at ``tests/unit/test_spec036_final_canary_gate.py`` (6 passed).*
- [X] T143 EquivalenceTestResult entity test `tests/contract/test_equivalence_test_result.py` — extends spec-033 FR-023 shape with `citation_fidelity`, `verbatim_source_match`, `corpus_build_sha`, `embedding_model_id`. (EquivalenceTestResult entity, FR-RAG-FM-06) — *Phase E: pydantic-v2 mirror at ``packages/domain/src/ama_domain/equivalence_test_result.py``; tests at ``tests/contract/test_equivalence_test_result.py`` (9 passed).*
- [X] T144 Compliance audit byte-replay automation — sampled SC-011 ≥ 95% reproduction across one-month rolling window; KQL alert on dip. (SC-011, FR-RAG-AG-02, Compliance-memo) — *Phase E: KQL at ``tests/audit/audit_replay_fidelity.kql``; hermetic sample test at ``tests/contract/test_audit_replay_fidelity.py`` (9 passed).*
- [~] T145 **Canary 6 (final) — Simulation Controller**: flip `foundry_rag_enabled_agents.SimulationController=true`; assert FR-023 ≥ 95% on simulation golden Q&A; assert SSE `citation` events emit per grounded turn; rollback drill in staging. (FR-RAG-FM-06, FR-RAG-SIM-01..06, R-12) — *Phase E: dry-run + production rollback drill scripts authored at ``infra/scripts/simulation-final-canary-dry-run.ps1`` + reused ``infra/scripts/canary-rollback-drill.ps1 -Agent simulation``; both exit 0. **PENDING Step 9** — live env-var flip ``FEATURE_FOUNDRY_RAG_SIMULATION=1`` is the user's invocation.*
- [~] T146 **Atomic legacy-deletion PR (FR-RAG-FM-04 binds)**: in a single PR — (a) delete the `openai.AzureOpenAI` import path from `apps/agents/common/llm_client.py`, (b) remove the `pytest.mark.skip` from `tests/contract/test_no_openai_imports.py` (T011) so the lint becomes binding, (c) move `infra/modules/azure-openai.bicep` to `infra/modules/legacy/` (per spec-032 deprecation pattern), (d) collapse `_generate_with_fallback` to its template-only branch (Foundry-side regression now degrades to template, never to Azure-OpenAI), (e) drop the `LEGACY_AZURE_OPENAI` env flag. CI MUST pass with all lints binding. (FR-RAG-FM-04, FR-RAG-FM-06, SC-002, Plan §Phase E1, Risk R5) — *Phase E: deletion authored on ``036-legacy-deletion`` branch as draft PR; merge **after T145 production-green** in user's Step 9. CI on the deletion branch is green with the now-active ``from openai`` lint.*
- [~] T147 Run `azd up` redeploy in staging then prod — verify `/healthz` endpoint returns `{rag_used: true, corpus_build_sha: <sha>, embedding_model_id: text-embedding-3-large@1, alias_active_index: corpus-vN}`; verify Application Insights `FoundryRAGAudit` table populating; verify SSE citation events on a smoke simulation chat. (Plan §Quickstart Step 9, FR-RAG-IDX-05, FR-RAG-SIM-02) — *Phase E: smoke-test script ``infra/scripts/azd-up-smoke-test.ps1`` + Step-9 cutover runbook ``docs/runbooks/036-foundry-rag-step9-cutover.md`` authored. **PENDING Step 9** — actual ``azd up`` invocation is user's.*
- [X] T148 Run quickstart.md end-to-end (§1–§11) on a clean dev environment; capture validation output and append to `specs/036-foundry-rag-grounding/quickstart-validation.md`. (quickstart.md) — *Phase E: hermetic walk performed on ``036-foundry-rag-grounding`` HEAD; report at ``specs/036-foundry-rag-grounding/quickstart-validation.md``; no drift detected.*
- [X] T149 Final docs sweep: update `README.md` Spec-036 entry; update `CHANGELOG.md`; verify all checklist items in `checklists/{requirements,migration,compliance}.md` are ticked or have a tracking issue. (Plan §Cross-references) — *Phase E: README spec-036 section + CHANGELOG entries (Added/Changed/Deprecated) + all 165 checklist items resolved with a per-file resolution note + spec.md "Open Questions" → "Closed Questions" rename.*
- [X] T150 Run `/speckit.analyze` to validate cross-artefact consistency before opening the merge PR. (Next-command recommendation) — *Phase E: cross-artefact analysis at ``specs/036-foundry-rag-grounding/analyze-report.md``; zero drift detected across spec.md / plan.md / data-model.md / contracts/ / tasks.md after Phase D's commits.*

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

*End of tasks.md (Phases 0–E) — **Next command**: `/speckit.analyze` (cross-artefact consistency + readiness gate).*

---

## Phase F — R3 Amend Loop Implementation (post-A–E) — APPENDED 2026-05-09

**Purpose**: Land the 12 amendment clusters (A1–A12) introduced by the Round 3 persona review (`spec.md` Sessions 3–5; `plan.md` §Phase F lines 310–553). Phase F is **strictly appended** after T150 — none of T001–T150 are re-ordered. Within Phase F, sub-phases run in dependency order **A4 → A5 → A7 → A1+A3 → A2 → A6 → A8+A10 → A9 → A11 → A12 → ADR-body**.

**Provenance**: 25 new FRs (FR-RAG-CA-01..05, COMP-01..04, COORD-01..02, TEST-01..04, OBS-01..03, UI-01, IDX-04a/05a/09, FRESH-01/02, NS-09, AC-01) + 4 extended (FR-RAG-AG-02, AG-04, LS-02, CV-01) + 7 new SCs (SC-013..SC-019) + 8 ADR stubs (ADR-12..ADR-19) + 6 contract artefacts (5 NEW: `cultural-authority-registry`, `chunk-metadata`, `conflict_detection`, `foundry-cv`, `staleness_alert`; 1 EXTENDED: `audit-record-llm-call`).

**Phase F task metrics**:

| Bucket | Count |
|---|---|
| **Phase F total** | **101** (T151–T251) |
| F-A4 (rego bug-fix) | 5 |
| F-A5 (audit shape) | 10 |
| F-A7 (blue-green atomicity) | 7 |
| F-A1 + F-A3 (agency + precedence; co-scheduled rebuild) | 20 |
| F-A2 (cultural authority) | 11 |
| F-A6 (federal compliance) | 8 |
| F-A8 (corpus freshness) | 6 |
| F-A10 (test coverage) | 7 |
| F-A9 (multi-agent conflict) | 7 |
| F-A11 (observability) | 7 |
| F-A12 (accessibility, SHOULD) | 5 |
| ADR-12..19 body authoring | 8 |
| **HUMAN-IN-LOOP tasks** (federal + cultural sign-off) | **4** (T202, T203, T210, T247) |

**Tags used in Phase F**:

- `[Cluster Aₙ]` — sub-phase / cluster identifier (mirrors `plan.md` §F-Aₙ).
- `[ADR-NN]` — cross-reference to `docs/decisions/036-foundry-rag-grounding/NN-*.md`.
- `[HUMAN-IN-LOOP]` — work the codebase scaffolds but cannot autonomously complete (per Assumption A9 + OOS-8); responsible authority is named in the task body.
- `[P]` — parallel-safe (different files, no incomplete deps within the same sub-phase).

**Tests-first** remains mandatory (Constitution §Quality Gates). Within each sub-phase, contract / integration tests go red BEFORE the matching implementation tasks.

---

### F-A4 — OPA Carve-Out Bug-Fix [Cluster A4]

**Goal**: close the FR-RAG-CV-01 prod 3-approver gap (R3 architecture finding F-ARCH-05 BLOCKER). **Sequencing**: FIRST in Phase F per Pass 2 Q-P2-03 — MUST land in the same PR as the broader amend-loop merge (no bifurcated rollout window). Pre-condition: T150 (Phase E close).

#### F-A4 — Tests (write red first)

- [X] T151 [P] [Cluster A4] [ADR-15] Contract test `tests/contract/test_foundry_carveout.py` — three cases: (a) 2-approver dev/staging payload → empty `deny_foundry_carveout` set, exit 0; (b) 2-approver **prod** payload → non-empty deny set, exit 1; (c) 3-approver prod payload → empty deny set, exit 0. (FR-RAG-CV-01; SC-016; Plan §F-A4.3) → **Acceptance**: all three cases pass against the patched rego; **proves T152**.

#### F-A4 — Implementation

- [X] T152 [Cluster A4] Edit `infra/policy/rego/foundry_carveout.rego` line ~29 — introduce an `input.environment` discriminator: `environment == "prod"` → `count(deployment.approver_identities) < 3` triggers `deny`; `environment in {"dev","staging"}` → `< 2` triggers `deny` (existing behaviour preserved). Keep all other rule semantics intact. (FR-RAG-CV-01; Plan §F-A4.1; ADR-15) → **Test**: T151.
- [X] T153 [P] [Cluster A4] Update `infra/parameters/foundry-carveout.schema.json` — add registry-root keys `min_approvers_prod` (default 3) + `min_approvers_dev` (default 2); add per-row `environment` enum (`dev | staging | prod`). (FR-RAG-CV-01; Plan §F-A4.4) → **Test**: extend T012 entity test to assert presence of new keys.
- [X] T154 [P] [Cluster A4] Sync the spec contracts mirror at `specs/036-foundry-rag-grounding/contracts/foundry-cv.schema.json` to match T153 (parity with infra schema). (Plan §F-A4.4) → **Test**: T005 byte-equality mirror parity check (extend with foundry-cv mirror).
- [X] T155 [Cluster A4] Atomic-merge gate — author `infra/policy/rego/AMEND_LOOP_COUPLING.md` documenting the single-PR coupling constraint (Pass 2 Q-P2-03), and add a CI guard `.github/workflows/amend-loop-coupling.yml` that fails any PR which modifies `foundry_carveout.rego` without also touching `tasks.md` Phase F entries (T151–T251) or vice versa. (FR-RAG-CV-01; Plan §F-A4.2 + §Updated phase ordering) → **Test**: pre-commit hook smoke (split-PR scenario must fail CI).

**Checkpoint F-A4**: rego rejects 2-approver prod, accepts 3-approver prod; CI guard prevents bifurcated rollout. **Blocks**: F-A5 onward MUST piggyback on the same merge train.

---

### F-A5 — Audit Schema Extension & Field-Coordinator Offline Boundaries [Cluster A5]

**Goal**: extend `AuditRecord` with the 8 new fields required by clusters A2/A3/A7/A9 (Pass 2 Q-P2-01 additive-nullable migration). **Sequencing**: BEFORE F-A2/F-A3/F-A7/F-A9 — every downstream cluster needs these fields. Pre-condition: T155.

#### F-A5 — Tests (write red first)

- [X] T156 [P] [Cluster A5] [ADR-14] Schema-mirror test `tests/contract/test_audit_record_amend_loop_fields.py` — assert post-extension `packages/schemas/audit-record-llm-call.json` exposes all 8 new optional fields: `operator_override_rationale`, `approval_workflow_state` (enum `pending|approved|rejected`), `approval_authority`, `downgrade_justification`, `retrieval_index_name`, `field_coordinator_offline_decision`, `conflict_group_id`, `precedence_tiebreak_applied[]`. All fields nullable for legacy rows. (FR-RAG-AG-02 ext; Plan §F-A5.1; ADR-14) → **Acceptance**: schema mirror byte-equal with `contracts/audit-record-llm-call.json`.
- [X] T157 [P] [Cluster A5] Integration test `tests/integration/test_approval_workflow_state_machine.py` — exercise transitions `pending → approved`, `pending → rejected`; assert non-transition cases (e.g. `approved → pending`) raise; assert `approval_authority` required when `approval_workflow_state in {approved, rejected}`. (FR-RAG-AG-02 ext; Plan §F-A5.3) → **Proves**: T164.
- [X] T158 [P] [Cluster A5] Integration test `tests/integration/test_field_coordinator_offline_boundaries.py` — assert offline path can: (a) make resource-allocation decisions, (b) safety-escalation, (c) evacuation-centre setup. Assert offline path REJECTS: (d) public warnings, (e) cross-jurisdiction mutual-aid requests, (f) state/national escalations. On reconnect, queued decisions emit `approval_workflow_state: "pending"`. (FR-RAG-LS-02 ext; Plan §F-A5.4) → **Proves**: T165.
- [X] T159 [P] [Cluster A5] SC-017 acceptance test `tests/contract/test_sc017_override_completeness.py` — sample 100 override events from a fixture replay; assert `operator_override_rationale` present in 100% of overrides; `approval_workflow_state` present in 100% of public-warning events. (SC-017; Plan §F-A5.5) → **Proves**: T163.

#### F-A5 — Implementation

- [X] T160 [Cluster A5] Mirror the extended `audit-record-llm-call.json` from `specs/036-foundry-rag-grounding/contracts/` into `packages/schemas/audit-record-llm-call.json`; assert byte-equality via T005 parity test. (Plan §F-A5.1) → **Test**: T156 + T005.
- [X] T161 [Cluster A5] Update pydantic-v2 model at `packages/domain/src/ama_domain/audit_record.py` — add the 8 new fields (additive nullable; default `None`); preserve all existing field semantics. (Plan §F-A5.1) → **Test**: T156.
- [X] T162 [Cluster A5] Add Phase F entry point to `infra/scripts/migrate-audit-record-036.ps1` (existing T082 script) — extend with `-Phase F` flag that adds the 8 new fields to live Cosmos `audit_records` container; dry-run by default; idempotent against legacy rows (Cosmos schema-on-read tolerates missing fields). (Plan §F-A5.2; mitigates R18) → **Test**: dry-run + sample-row replay covered by T156.
- [X] T163 [Cluster A5] Wire emission in `apps/agents/common/audit.py` — emit on every applicable record: `operator_override_rationale` (operator modify/reject), `approval_workflow_state` (every public-warning event), `approval_authority`, `downgrade_justification`, `retrieval_index_name` (every `rag_used == true` record; concrete index name per ADR-16, NOT the alias), `field_coordinator_offline_decision` (offline path), `conflict_group_id` (set by F-A9), `precedence_tiebreak_applied[]` (set by F-A3.3). (FR-RAG-AG-02 ext; Plan §F-A5.3) → **Test**: T159.
- [X] T164 [Cluster A5] Implement approval state machine at `apps/api/app/services/approval_workflow.py` (NEW) — pydantic-v2 state machine wrapping `approval_workflow_state` transitions with `approval_authority` actor logging; emit audit event on every transition. (FR-RAG-AG-02 ext; Plan §F-A5.3) → **Test**: T157.
- [X] T165 [Cluster A5] Extend FR-RAG-LS-02 Field-Coordinator offline boundaries in `apps/agents/common/offline_cache.py` — gate `is_decision_offline_safe(decision_type)` returns False for public-warning / cross-jurisdiction-mutual-aid / state-escalation; queued decisions on reconnect set `approval_workflow_state: "pending"` + `field_coordinator_offline_decision: <decision_summary>`. (FR-RAG-LS-02 ext; Plan §F-A5.4) → **Test**: T158.

**Checkpoint F-A5**: 8 new audit fields landed (additive nullable); approval state machine deterministic; FC-offline boundary semantics enforced. **Unblocks**: F-A2 (cultural-authority gate audit emission), F-A7 (`retrieval_index_name`), F-A9 (`conflict_group_id`), F-A11 (OTel spans use audit fields as attributes).

---

### F-A7 — Blue-Green Audit Replay Atomicity [Cluster A7]

**Goal**: lock-in alias-pinning protocol + 5-min rollback SLO BEFORE any chunk-schema rebuild. **Sequencing**: AFTER F-A5 (`retrieval_index_name` audit field); BEFORE F-A1+F-A3 (atomicity protocol must exist before the rebuild that exercises it). Pre-condition: T165.

#### F-A7 — Tests (write red first)

- [X] T166 [P] [Cluster A7] [ADR-16] E2E smoke test stub at `tests/e2e/test_blue_green_alias_flip.py` — initial red shape; full body lands in T222 (F-A10.4). Asserts the alias-pinning protocol contract (query started against `corpus-v3` continues to resolve to `corpus-v3` even after alias flips to `corpus-v4`). (FR-RAG-IDX-04a; Plan §F-A7.1) → **Proves**: T168.
- [X] T167 [P] [Cluster A7] Integration test `tests/integration/test_index_rollback_slo.py` — emit fake parity-gate failure; assert (a) Service Bus `index_rollback` event emitted with `parity_gate_failure_reason`, (b) Release Manager approval required (manual gate, not automated), (c) alias re-flips ≤5 min after timer-start, (d) audit append `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}`. (FR-RAG-IDX-09; SC-019; Plan §F-A7.3..§F-A7.4) → **Proves**: T170.

#### F-A7 — Implementation

- [X] T168 [Cluster A7] Implement alias-pinning protocol in `apps/agents/common/retrieval_client.py` — at query start, resolve alias `corpus-search` to a concrete index name (e.g., `corpus-v3`) and pin that name for the entire query lifecycle. SSE multi-turn sessions pin once at session start; no alias re-resolution mid-query. (FR-RAG-IDX-04a; Plan §F-A7.1) → **Test**: T166.
- [X] T169 [Cluster A7] Wire `retrieval_index_name` into every `RetrievalResult` in `apps/agents/common/retrieval_service.py` and propagate to `AuditRecord.retrieval_index_name` via the F-A5.3 emission wiring (T163). (Plan §F-A7.2) → **Test**: T156 + T166.
- [X] T170 [Cluster A7] Implement Service Bus `index_rollback` event publisher at `apps/api/app/services/index_rollback.py` (NEW) — 5-min SLO timer starts at parity-gate failure detection; manual Release Manager approval (Pass 2 Q-P2-08 Manual operator action class); on completion, append audit record with `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}`; on-call paged via existing alert pipeline. (FR-RAG-IDX-09; Plan §F-A7.3..§F-A7.4) → **Test**: T167.
- [X] T171 [P] [Cluster A7] Add 7-day retention TTL tag in `infra/modules/aisearch.bicep` for previous indices post-flip; extend `infra/scripts/cleanup-stale-indices.ps1` to enforce. (FR-RAG-IDX-04; Plan §F-A7.5) → **Test**: integration test asserting old index queryable for 7 days post-flip (extends T167).
- [X] T172 [P] [Cluster A7] Author rollback runbook `docs/runbooks/036-foundry-rag-blue-green-rollback.md` — covers (a) parity-gate failure detection, (b) Release Manager approval workflow, (c) 5-min SLO timer, (d) post-rollback audit verification. (Plan §F-A7) → **Test**: runbook walked in chaos game-day (extends T140).

**Checkpoint F-A7**: alias-pinning verified across simulated flips; 5-min rollback SLO timer green; previous index retained 7 days. **Unblocks**: F-A1+F-A3 chunk-schema rebuild can now safely flip the alias.

---

### F-A1 + F-A3 — Agency Disambiguation + Authority Precedence Ranking (co-scheduled blue-green rebuild) [Cluster A1, Cluster A3]

**Goal**: extend chunk schema with `agency`, `agency_role`, `authority_level`, `precedence_rank` and rebuild `corpus-v{N+1}` in a single co-scheduled blue-green pass (Pass 2 Q-P2-01 + Assumption A10 — no in-place chunk mutation). **Sequencing**: AFTER F-A7 (atomicity protocol pinned); blue-green rebuild gated on T188; previous index retained 7 days. Pre-condition: T172.

#### F-A1+A3 — Tests (write red first)

- [X] T173 [P] [Cluster A1] [ADR-13] Contract test `tests/contract/test_agency_disambiguation.py` — gold-set fixture `tests/fixtures/golden-set-v1.json` entries tagged `agency_disambiguation` (≥20 entries, e.g. NSW-RFS vs FRNSW, CFA-VIC vs FRV, ACT-ESA vs Commonwealth); assert ≥95% of queries return chunks with the correct `agency` + `agency_role` filters; 0 silent conflations across the 50-query persona-driven set. (FR-RAG-AG-04 ext; SC-013; Plan §F-A1.5) → **Proves**: T183.
- [X] T174 [P] [Cluster A3] Contract test `tests/contract/test_authority_precedence.py` — ACT-Commonwealth gold-set (≥20 entries: Parliament House, Defence estates, embassies, AIATSIS); assert Commonwealth doctrine first in ≥95% of national-institution queries when `jurisdiction == act`. (FR-RAG-AG-04 ext + FR-RAG-AC-01; SC-015; Plan §F-A3.6) → **Proves**: T184.
- [X] T175 [P] [Cluster A1] Integration test `tests/integration/test_ingest_agency_lint.py` — feed a synthetic `source.json` with one entry missing both `agency` and `agency_role`; assert ingest run fails non-zero with a clear `chunk_missing_agency_metadata` error. (FR-RAG-AG-04 ext; Plan §F-A1.2) → **Proves**: T181.
- [X] T176 [P] [Cluster A3] Contract test `tests/contract/test_precedence_tiebreak.py` — synthesise four chunks with identical `authority_level` + `precedence_rank` but varying `(corpus_build_sha.generated_at, licence_mode, embedding_model_id, chunk_id)`; assert deterministic order: (1) recency, (2) `licence_mode` (`full-text` > `metadata-only`), (3) `embedding_model_id` lex, (4) `chunk_id` lex. Assert `precedence_tiebreak_applied[]` audit emission lists every tier triggered. (FR-RAG-AC-01; Pass 1 Q-P1-02; Plan §F-A3.3) → **Proves**: T185.
- [X] T177 [P] [Cluster A3] Integration test `tests/integration/test_comdisplan_activation.py` — set `national_emergency_active=true`; assert all `authority_level=commonwealth` chunks elevate to `precedence_rank=1` for the activation duration; clear flag → revert. (FR-RAG-COMP-04; Plan §F-A3.4) → **Proves**: T186.

#### F-A1+A3 — Implementation

- [X] T178 [P] [Cluster A1] Extend AI Search index schema at `infra/scripts/aisearch-schema.json` with `agency` (string, filterable) + `agency_role` (enum: `urban-fire | rural-fire | ses | combined | police | ambulance | marine-rescue | national-security | other`, filterable). (FR-RAG-AG-04 ext; Plan §F-A1.1) → **Test**: T173.
- [X] T179 [P] [Cluster A3] Extend AI Search index schema at `infra/scripts/aisearch-schema.json` with `authority_level` (enum: `state-territory | commonwealth | national-institution`) + `precedence_rank` (int 1–3). (FR-RAG-AC-01; Plan §F-A3.1) → **Test**: T174.
- [X] T180 [P] [Cluster A1+A3] Mirror `specs/036-foundry-rag-grounding/contracts/chunk-metadata.schema.json` into `packages/schemas/chunk-metadata.schema.json`; extend T005 mirror parity test. (Plan §F-A1.1 + §F-A3.1) → **Test**: T005 + T156 patterns.
- [X] T181 [Cluster A1] Extend `apps/ingest-runner/src/ama_ingest/chunker.py` to emit `agency` + `agency_role` from `source.json` per-entry metadata; ingest-time lint fails the build if any chunk lacks BOTH fields. (FR-RAG-AG-04 ext; Plan §F-A1.2) → **Test**: T175.
- [X] T182 [Cluster A3] Extend chunker to emit `authority_level` + `precedence_rank` from source metadata; default `state-territory`/`3` when unset. (FR-RAG-AC-01; Plan §F-A3.1) → **Test**: T174.
- [X] T183 [Cluster A1] Wire FR-RAG-AG-04 disambiguation into `apps/agents/common/retrieval_client.py` — agency-filtered retrieval so urban-fire and rural-fire queries within the same jurisdiction never collide. (FR-RAG-AG-04 ext; Plan §F-A1.3) → **Test**: T173.
- [X] T184 [Cluster A3] Wire FR-RAG-AC-01 ranking pass into `retrieval_client.py` — when retrieval surfaces conflicting guidance from multiple authority levels (e.g. ACT-ESA + Commonwealth-NEMA), present BOTH with precedence indicators + a conflict-resolution note directing operators to escalate to IC + NEMA liaison. (FR-RAG-AC-01; Plan §F-A3.2) → **Test**: T174.
- [X] T185 [Cluster A3] Implement deterministic tie-break order in `retrieval_client.py` per Pass 1 Q-P1-02 — sequence: (1) recency (`corpus_build_sha.generated_at`), (2) `licence_mode` (full-text > metadata-only), (3) `embedding_model_id` lex, (4) `chunk_id` lex. Trace recorded as `precedence_tiebreak_applied[]` (audit emission via T163). (FR-RAG-AC-01; Plan §F-A3.3) → **Test**: T176.
- [X] T186 [Cluster A3] Wire FR-RAG-COMP-04 COMDISPLAN activation interlock — when the `national_emergency_active` flag is set, retrieval ranking elevates `authority_level=commonwealth` chunks to `precedence_rank=1` for the activation duration; flag flip emits `audit.feature_flag_change`. (FR-RAG-COMP-04; Plan §F-A3.4 + §F-A6.4) → **Test**: T177.
- [X] T187 [Cluster A3] Implement feature flag `feature.authority_precedence_ranking.enabled` (Reversible class per Pass 2 Q-P2-08) — disable falls back to recency-only ranking; emits `authority_precedence_ranking_disabled` audit event with `{flag_name, old_value, new_value, actor_id, change_reason}`. (Plan §F-A3.5) → **Test**: T174 with flag toggled.
- [X] T188 [Cluster A1+A3] Co-scheduled blue-green rebuild — invoke `infra/scripts/blue-green-flip.ps1` (Phase B helper) to rebuild `corpus-v{N+1}` carrying new chunk fields (`agency`, `agency_role`, `authority_level`, `precedence_rank`); previous `corpus-v{N}` retained 7 days per FR-RAG-IDX-04 + ADR-16 (T171); alias flip pinned by F-A7.1 protocol (T168). (Plan §F-A1.4 + §Updated phase ordering) → **Test**: T166 (E2E smoke) + T222 (full E2E).
- [X] T189 [P] [Cluster A1] Update `tests/fixtures/golden-set-v1.json` — add ≥20 entries tagged `agency_disambiguation` (NSW-RFS vs FRNSW, CFA-VIC vs FRV, SES-NSW vs SES-VIC vs NTES, SAMFS vs SACFS, DFES-WA vs DFES-Marine). Single-fixture canonicalisation per Pass 1 Q-P1-08 (also referenced by T221). (Plan §F-A1.5; SC-013) → **Test**: T173.
- [X] T190 [P] [Cluster A3] Update `tests/fixtures/golden-set-v1.json` — add ≥20 national-institution queries (Parliament House, Australian Defence Force estates, foreign embassies, AIATSIS, National Library, NMA) with `jurisdiction=act` and expected Commonwealth doctrine ranking. (Plan §F-A3.6; SC-015) → **Test**: T174.
- [X] T191 [Cluster A1] SC-013 acceptance gate — extend per-PR CI to assert ≥95% precision on `agency_disambiguation`-tagged subset of golden-set-v1; fail on regression. (SC-013) → **Test**: T173.
- [X] T192 [Cluster A3] SC-015 acceptance gate — extend per-PR CI to assert Commonwealth-first ≥95% on `jurisdiction=act` national-institution subset; fail on regression. (SC-015) → **Test**: T174.

**Checkpoint F-A1+A3**: `corpus-v{N+1}` published with new chunk schema; agency-disambiguation ≥95%; ACT-Commonwealth precedence ≥95%; tie-break deterministic; COMDISPLAN interlock wired. **Unblocks**: F-A2 cultural authority gate (consumes new chunk fields).

---

### F-A2 — Cultural Authority Registry & Gating [Cluster A2]

**Goal**: provision the cultural-authority gate (Constitution VI-C non-negotiable; ADR-12) — codebase scaffolding only; corpus body authoring + registry population are HUMAN-IN-LOOP per Assumption A9 + OOS-8. **Sequencing**: AFTER F-A1+A3 (chunk fields `cultural_classification` + `cultural_authority_required` land in same rebuild); AFTER F-A5 (`audit.gateway_decision` emission). Pre-condition: T192.

#### F-A2 — Tests (write red first)

- [X] T193 [P] [Cluster A2] [ADR-12] Contract test `tests/contract/test_cultural_authority_registry.py` — registry signature verifier (cosign keyless OR age-encrypted detached, mirroring FR-RAG-LS-02 dual-sig pattern); assert valid sig → accepted, tampered sig → rejected with `cultural_authority_signature_invalid` audit emission. (FR-RAG-CA-01..05; Plan §F-A2.3) → **Proves**: T198.
- [X] T194 [P] [Cluster A2] Integration test `tests/integration/test_cultural_authority_gate.py` — three cases: (a) registry available + chunk has `cultural_authority_required=true` + operator consent verified → chunk passes; (b) registry available + protected chunk + NO operator consent → chunk suppressed, audit `cultural_authority_gate_blocked`; (c) registry unreachable → fail-closed for protected chunks, NON-protected chunks remain retrievable (Constitution Principle I); audit `cultural_authority_registry_unavailable` (Pass 1 Q-P1-01). (FR-RAG-CA-04; Plan §F-A2.4) → **Proves**: T199.
- [X] T195 [P] [Cluster A2] Chaos test `tests/integration/test_cultural_authority_flag_lockdown.py` — assert `feature.cultural_authority_gate.enabled` flag flip in `environment=prod` is OPA-blocked at flag-flip time; only `environment=test` may flip. (FR-RAG-CA-04; A12 Locked-on class; Plan §F-A2.6) → **Proves**: T201.

#### F-A2 — Implementation

- [X] T196 [Cluster A2] Provision Cosmos DB container `culturalAuthorityRegistry` in Australia East (NN-2 + FR-RAG-CV-04) via `infra/modules/cosmos-cultural-authority.bicep` (NEW). Container provisioned EMPTY per FR-RAG-CA-05 (population is HUMAN-IN-LOOP per T202). (Plan §F-A2.1) → **Test**: integration smoke (Bicep what-if).
- [X] T197 [P] [Cluster A2] Mirror `specs/036-foundry-rag-grounding/contracts/cultural-authority-registry.schema.json` into `packages/schemas/`; extend T005 mirror parity test. (Plan §F-A2.1) → **Test**: T005 + T193.
- [X] T198 [Cluster A2] Implement `apps/agents/common/cultural_authority_registry.py` (NEW) — Cosmos client + signature verifier (cosign keyless OR age-encrypted detached, mirroring FR-RAG-LS-02 dual-sig pattern from T129); registry-cache TTL 5 minutes; on cache miss + Cosmos unreachable → fail-closed for protected chunks. (FR-RAG-CA-01..05; Plan §F-A2.3) → **Test**: T193.
- [X] T199 [Cluster A2] Implement post-retrieval, in-process gate inside `apps/agents/common/retrieval_service.py` — between AI Search round-trip (T060) and Foundry inference (T075..T077), per Pass 2 Q-P2-02; suppress chunks with `cultural_authority_required=true` unless operator consent is verified; emit `cultural_authority_registry_unavailable` audit event on registry-unreachable path; non-protected chunks always retrievable (Constitution Principle I no-silencing). Gate emits `cultural_authority_check_result` into the existing `retrieved_chunks[]` audit shape per cross-cluster matrix A2→A5. (FR-RAG-CA-04; Plan §F-A2.4) → **Test**: T194.
- [X] T200 [Cluster A2] Add chunk fields `cultural_classification` (enum: `public | indigenous-language | sacred-site | land-governance`) + `cultural_authority_required` (bool) to chunker (`apps/ingest-runner/src/ama_ingest/chunker.py`) and AI Search schema (`infra/scripts/aisearch-schema.json`). Co-deployed with the F-A1+A3 blue-green rebuild (T188) so all four field-extension passes share one rebuild. (FR-RAG-CA-04; Plan §F-A2.5) → **Test**: T194.
- [X] T201 [Cluster A2] Implement OPA flag-flip block — author `infra/policy/rego/cultural_authority_flag.rego` (NEW) denying `feature.cultural_authority_gate.enabled` flag flip in `environment=prod`; only `environment=test` may flip; flag is **Locked-on in prod** per A12 class taxonomy; emit `cultural_authority_gate_test_disable_attempt` audit event on denied attempt. (FR-RAG-CA-04; Plan §F-A2.6) → **Test**: T195.
- [~] T202 [HUMAN-IN-LOOP] [Cluster A2] **Initial registry seeding** — registry container is provisioned empty by T196; population requires sign-off from **NEMA + AFAC + ≥3 Indigenous community representatives** per FR-RAG-CA-05 + SC-014. CD verifies sign-offs at deploy-time; CI fails pre-prod release if `infra/parameters/cultural-authority-signoff.json` is absent or signatures invalid. Authority owners: **NEMA, AFAC, Indigenous community representatives, AIATSIS Ethics Committee**. (FR-RAG-CA-05; SC-014; A9; OOS-8; Plan §F-A2.2) → **Proves go-live readiness**: SC-014.
- [~] T203 [HUMAN-IN-LOOP] [Cluster A2] **Corpus body authoring** — translation authoring (Arrernte, Tiwi, Warlpiri, Pitjantjatjara, Torres Strait Islander), Sacred Site protocols, ALT/APY consent gates per FR-RAG-CA-01..03. Tracked in tasks.md but performed outside this AI workflow per Assumption A9 + OOS-8. Authority owners: **NEMA, AFAC, Land Councils (NLC, CLC, ALT, APY), AIATSIS Ethics Committee, ≥3 Indigenous community representatives**. (FR-RAG-CA-01..03; Plan §F-A2.7) → **Proves go-live readiness**: SC-014 row count > 0.

**Checkpoint F-A2**: gate fail-closed on registry-unreachable (protected chunks); fail-open for public chunks; flag locked in prod; T202 + T203 are open work-items not blocking amend-loop merge BUT blocking production go-live.

---

### F-A6 — Federal Compliance (Privacy Act + ISM 2024 + PSPF + COMDISPLAN) [Cluster A6]

**Goal**: scaffold Privacy Act 1988 APP surfaces, ISM 2024 mapping, PSPF audit export, and COMDISPLAN ranking interlock. **Sequencing**: AFTER F-A2 + F-A5; HUMAN-IN-LOOP federal sign-off blocks production go-live but NOT amend-loop merge. Pre-condition: T203.

#### F-A6 — Tests (write red first)

- [X] T204 [P] [Cluster A6] [ADR-15] Contract test `tests/contract/test_privacy_act_sar.py` — `GET /api/audit/sar?subject=<id>` returns audit events filtered to subject; assert APP 1 (privacy notice surface), APP 3 (collection limits), APP 5 (notification of collection), APP 6 (use/disclosure), APP 11 (security & retention) — all five surfaces present in response payload. (FR-RAG-COMP-01; Plan §F-A6.2) → **Proves**: T206.
- [X] T205 [P] [Cluster A6] Contract test `tests/contract/test_pspf_audit_export.py` — `GET /api/audit/export?format=pspf&start=...&end=...` returns CSV with the six mandated columns: `Timestamp, User, Action, Resource, Outcome, Justification`; assert column header order, value escaping, RFC 4180 compliance. (FR-RAG-COMP-03; SC-018; Plan §F-A6.3) → **Proves**: T207.

#### F-A6 — Implementation

- [X] T206 [Cluster A6] Implement Privacy Act 1988 APP surfaces — SAR endpoint `GET /api/audit/sar?subject=...` at `apps/api/app/routers/audit.py`; PII anonymisation hook at `apps/agents/common/audit.py` invoked BEFORE write; reuse existing 7-year retention from spec 030. (FR-RAG-COMP-01; Plan §F-A6.2) → **Test**: T204.
- [X] T207 [Cluster A6] Implement PSPF audit export endpoint `GET /api/audit/export?format=pspf&start=...&end=...` at `apps/api/app/routers/audit.py` returning CSV with six mandated columns mapped from existing audit shape (post-F-A5 extensions cover every column with no further schema change). (FR-RAG-COMP-03; Plan §F-A6.3) → **Test**: T205.
- [X] T208 [Cluster A6] Wire FR-RAG-COMP-04 COMDISPLAN activation interlock — already covered by T186 (cross-reference; same mechanism, two consumers per cross-cluster matrix A6→A3). (FR-RAG-COMP-04; Plan §F-A6.4) → **Test**: T177.
- [X] T209 [Cluster A6] Author scaffold `docs/compliance/ISM-2024-mapping.md` (NEW) — references **ISM-0468** (TLS 1.2+ for Foundry + AI Search) and **ISM-1552** (audit-log cryptographic integrity via cosign + detached sigs); marks "PENDING HUMAN-IN-LOOP federal sign-off (T210) before publication" header. (FR-RAG-COMP-02; SC-018; Plan §F-A6.1) → **Test**: SC-018 file-existence + content match.
- [~] T210 [HUMAN-IN-LOOP] [Cluster A6] **Federal sign-off attestation** — review and approve `docs/compliance/ISM-2024-mapping.md`; produce signed attestation file `docs/compliance/ISM-2024-mapping-signoff.json` with signatures from **NEMA, AGD (Attorney-General's Department), AFP (Australian Federal Police)** per FR-RAG-COMP-01..04 + Assumption A9. **Blocks production go-live; does NOT block amend-loop merge per Plan §F-A6.5.** Authority owners: **NEMA, AGD, AFP** (AIATSIS consulted for Indigenous-data sections). (Plan §F-A6.5; A9; mitigates R15) → **Proves go-live readiness**: SC-018 sign-off.
- [X] T211 [Cluster A6] CD gate enforcement — extend `infra/scripts/verify-carveout.ps1` (Phase A1 helper) to additionally verify `docs/compliance/ISM-2024-mapping-signoff.json` exists with valid signatures from NEMA + AGD + AFP before allowing prod deploy; CD fails if absent. (FR-RAG-COMP-01..04; mitigates R15) → **Test**: extend T013 enforcement test with sign-off-missing scenario.

**Checkpoint F-A6**: SAR + PSPF endpoints live; ISM-2024-mapping scaffolded; CD gate primed; T210 is the production-go-live HUMAN-IN-LOOP blocker.

---

### F-A8 — Corpus Freshness (drift detection + UI indicator + staleness alert) [Cluster A8]

**Goal**: nightly drift-detection + UI freshness indicator + 14-day staleness alert at global corpus index scope (Pass 1 Q-P1-05). **Sequencing**: AFTER F-A5 + F-A7. Pre-condition: T211.

#### F-A8 — Tests (write red first)

- [X] T212 [P] [Cluster A8] [ADR-17] Integration test `tests/integration/test_corpus_staleness_alert.py` — synthesise `corpus_build_sha.generated_at` 15 days old + no ingest in last 48h; assert (a) `corpus_stale` Service Bus event emitted with payload matching `contracts/staleness_alert.schema.json`, (b) on-call PagerDuty fired, (c) UI indicator turns red. Conversely, age 8 days → yellow but no alert. (FR-RAG-FRESH-02; Plan §F-A8.3) → **Proves**: T215.

#### F-A8 — Implementation

- [X] T213 [Cluster A8] Implement nightly drift-detection — extend `.github/workflows/corpus-ingest.yml` cron to `"0 14 * * *"` UTC (= 0100 AEST / 0000 AEDT); on run, pipeline checks every `source.json.sha256` for drift; if drift → re-run ingest + alias flip per ADR-16; if no drift → log `no_drift_detected` and exit cheaply. (FR-RAG-IDX-05a; Plan §F-A8.1) → **Test**: dry-run scheduled trigger smoke.
- [X] T214 [Cluster A8] Implement FR-RAG-FRESH-01 UI freshness indicator — `apps/web/src/components/citation-card.tsx` + Simulation chat surface; render "Corpus last updated: <timestamp>" derived from `corpus_build_sha.generated_at`; yellow if age >7 days; red if >14 days. (FR-RAG-FRESH-01; Plan §F-A8.2) → **Test**: extend T084 + T101 component tests with timestamp colour assertions.
- [X] T215 [Cluster A8] Implement FR-RAG-FRESH-02 staleness alert at **global corpus index** scope (Pass 1 Q-P1-05; NOT per-jurisdiction) — emit `corpus_stale` to Service Bus + on-call when `corpus_build_sha.generated_at` age >14 days AND no ingest in last 48h. Schema authority: `specs/036-foundry-rag-grounding/contracts/staleness_alert.schema.json` (mirror to `packages/schemas/`). (FR-RAG-FRESH-02; Plan §F-A8.3) → **Test**: T212.
- [X] T216 [Cluster A8] Implement feature flag `feature.corpus_freshness_alert.enabled` (Reversible class per Pass 2 Q-P2-08) — disable suppresses the on-call page but records underlying state in audit log; emits `corpus_freshness_alert_disabled` on flip. (Plan §F-A8.4) → **Test**: extend T212 with flag toggled.
- [X] T217 [P] [Cluster A8] Author runbook `docs/runbooks/036-foundry-rag-corpus-stale.md` — covers four common stale causes: (1) corpus repo stalled, (2) ingest pipeline failing, (3) cron misconfigured, (4) parity gate blocking. (Plan §F-A8.5) → **Test**: runbook walked in chaos game-day.

**Checkpoint F-A8**: nightly drift cron live; UI shows freshness; 14-day alert wired; runbook published.

---

### F-A10 — Test Coverage Expansion (Windows + load + golden-set + E2E) [Cluster A10]

**Goal**: close R3 delivery / quality findings (Windows compat, 50-agent load, golden-set canonicalisation, blue-green E2E). **Sequencing**: AFTER F-A1+A3 (golden-set tags), F-A5 (audit fields in load test), F-A7 (atomicity protocol for E2E). Pre-condition: T217.

- [X] T218 [P] [Cluster A10] [ADR-19] **Windows compat (FR-RAG-TEST-01)** — add Windows runner job to `.github/workflows/ci.yml` mirroring the existing Linux job (per-PR trigger); add shared `clean_tmp_path` fixture to `tests/conftest.py` (closes F-DEL-01: `gc.collect()` + `time.sleep(0.05)` + retry); force `PYTHONIOENCODING=utf-8` via env-var (closes F-DEL-08); gate Windows-only cases with `@pytest.mark.skipif(sys.platform != "win32")` under existing `tests/contract/`, `tests/integration/`, `apps/agents/tests/`. (FR-RAG-TEST-01; Plan §F-A10.1) → **Test**: CI green on Windows runner.
- [X] T219 [P] [Cluster A10] **50-agent load (FR-RAG-TEST-02)** — add `RetrievalSession` Locust task class to `tests/load/locustfile.py` exercising 50 distinct `agent_session_id` values (per Pass 1 Q-P1-07) sustained at RPS=50 for 60s with p95 retrieval-only latency ≤500ms; instrument with `psutil` for per-process memory + CPU; add to `apps/agents/pyproject.toml`. SHOULD-class quality gate. Triggers: scheduled weekly CI + pre-promotion stage of spec-029 progressive-delivery (NOT per-PR — too long). (FR-RAG-TEST-02; Plan §F-A10.2) → **Test**: load run green; baseline at `tests/load/baselines/spec-036-50-agent-baseline.json`.
- [X] T220 [P] [Cluster A10] **Golden-set consolidation (FR-RAG-TEST-03)** — single canonical fixture at `tests/fixtures/golden-set-v1.json` per Pass 1 Q-P1-08; each entry: `(agent_name, jurisdictions, hazard_type, query_text, expected_chunk_ids, expected_jurisdiction_filters, tags[])`; `tags[]` MUST support `agency_disambiguation` for SC-013 (≥20 of 50 entries — landed by T189) and national-institution tag (≥20 entries — landed by T190); migrate prior fixture references (T060, T065, T134) to point at this single file. Per-PR trigger. (FR-RAG-TEST-03; Plan §F-A10.3) → **Test**: T173 + T174 use this fixture; assert no duplicate fixture files remain.
- [X] T221 [Cluster A10] **Blue-green E2E (FR-RAG-TEST-04)** — author the full body of `tests/e2e/test_blue_green_alias_flip.py` (started in T166); runs against staging Azure AI Search using ephemeral `corpus-test-*` index names; asserts (a) alias flip <60s, (b) post-flip retrieval resolves to new index name in audit log (`retrieval_index_name` field from F-A5), (c) previous index accessible 7 days, (d) rollback flips back ≤5min (FR-RAG-IDX-09 SLO). Triggers: scheduled nightly (mirrors FR-RAG-IDX-05a 1 AM AU-Eastern cadence) + pre-release stage of spec-029. (FR-RAG-TEST-04; SC-019; Plan §F-A10.4) → **Test**: T166 stub + this expansion.
- [X] T222 [Cluster A10] CI matrix updates — extend `.github/workflows/ci.yml` matrix: per-PR for TEST-01 (Windows compat) + TEST-03 (golden-set); weekly cron for TEST-02 (50-agent load); nightly cron for TEST-04 (blue-green E2E). (Plan §F-A10 triggers) → **Test**: CI workflow lints clean.
- [X] T223 [P] [Cluster A10] Author `docs/testing/spec-036-test-strategy.md` documenting the unit/contract/integration/e2e split with `@pytest.mark.unit | integration | contract | e2e` markers (closes F-DEL-07 finding). (Plan §F-A10.5) → **Test**: doc exists; markers configured in `pyproject.toml`.
- [X] T224 [P] [Cluster A10] Add `psutil` to `tests/load/pyproject.toml` (or root `pyproject.toml` test-extras); pin minor version. (Plan §Tech-stack additions) → **Test**: T219 dependency resolution.

**Checkpoint F-A10**: Windows + Linux runners green per-PR; weekly 50-agent load baseline; canonical golden-set v1; nightly blue-green E2E.

---

### F-A9 — Multi-Agent Conflict Detection [Cluster A9]

**Goal**: reactive, post-return, deterministic, rule-based detector across 4 conflict classes; AIIMS escalation chain. **Sequencing**: AFTER F-A5 (`conflict_group_id` audit field). Pre-condition: T224.

#### F-A9 — Tests (write red first)

- [X] T225 [P] [Cluster A9] [ADR-18] Integration test `tests/integration/test_conflict_detection.py` — synthesise four conflict cases: (a) **resource** — same `resource_id`, overlapping `(start_time, end_time)`; (b) **spatial** — incompatible recs over overlapping `(geo_bbox, time_window)`; (c) **temporal** — action verbs with mutually exclusive deadlines; (d) **severity** — hazard severity buckets with delta ≥1 AIIMS incident level for the same hazard. Assert each emits a `conflict_detected` event with the right class label and a stable `conflict_group_id`. (FR-RAG-COORD-01; Plan §F-A9.3) → **Proves**: T228 + T229.
- [X] T226 [P] [Cluster A9] Integration test `tests/integration/test_aiims_escalation.py` — assert escalation chain per Pass 1 Q-P1-03: (1) `conflict_detected` event routes first to Ops Officer; (2) 5-min unack timeout → IC; (3) full-AIIMS-unreachable + degraded-connectivity → Field Coordinator queues for IC review on reconnect (Field Coordinator MUST NOT auto-resolve cross-agent conflicts). (FR-RAG-COORD-02; Plan §F-A9.5) → **Proves**: T230.

#### F-A9 — Implementation

- [X] T227 [Cluster A9] Provision Cosmos DB container `conflictDetectionLog` in Australia East (NN-2 + FR-RAG-CV-04) via `infra/modules/cosmos-conflict-detection.bicep` (NEW); mirror `specs/036-foundry-rag-grounding/contracts/conflict_detection.schema.json` into `packages/schemas/`. (Plan §F-A9.1) → **Test**: T225 fixture write/read.
- [X] T228 [Cluster A9] Implement `apps/api/app/services/conflict_detection.py` (NEW) — reactive, post-return, deterministic, rule-based detector running in the recommendation-aggregation layer (NOT inside any individual agent and NOT in real-time streaming, per Pass 2 Q-P2-06). Pre-emptive divergence detection rejected because it breaks Constitution Principle IV deterministic replay + spec 033 MAF agent-isolation model. (FR-RAG-COORD-01; Plan §F-A9.2) → **Test**: T225.
- [X] T229 [Cluster A9] Implement four conflict classes in `conflict_detection.py` (resource, spatial, temporal, severity) per ADR-18; persist to `conflictDetectionLog` Cosmos container with stable `conflict_group_id`. (FR-RAG-COORD-01; Plan §F-A9.3) → **Test**: T225.
- [X] T230 [Cluster A9] Wire `conflict_group_id` into `AuditRecord` via the F-A5.1 schema field (T161, T163) — same field, two consumers. Implement AIIMS escalation chain at `apps/api/app/services/aiims_escalation.py` (NEW): Ops Officer first → 5-min unack → IC → Field Coordinator queue (FC MUST NOT auto-resolve). (FR-RAG-COORD-02; Plan §F-A9.4 + §F-A9.5) → **Test**: T226.
- [X] T231 [Cluster A9] Implement feature flag `feature.multi_agent_conflict_detection.enabled` (Reversible class per Pass 2 Q-P2-08) — disable reverts to single-agent behaviour (NEVER silences the agent — Constitution Principle I); emits `multi_agent_coordination_disabled` audit event on flip. (Plan §F-A9.6; mitigates R16) → **Test**: T225 with flag toggled.

**Checkpoint F-A9**: 4 conflict classes detected with stable `conflict_group_id`; AIIMS escalation green; flag reversible.

---

### F-A11 — Observability (OTel spans + dashboards + p95 alert) [Cluster A11]

**Goal**: wrap `RetrievalService.retrieve()` and Foundry inference call in dedicated OTel spans exported via existing OTel-to-App-Insights bridge per spec 014 FR-016 (Pass 2 Q-P2-05); **direct App-Insights SDK calls remain forbidden in production paths**. **Sequencing**: AFTER F-A5 (spans use `retrieval_index_name` audit field as a span attribute). Pre-condition: T231.

#### F-A11 — Tests (write red first)

- [X] T232 [P] [Cluster A11] Integration test `tests/integration/test_otel_retrieval_span.py` — invoke `RetrievalService.retrieve()` with an in-memory OTel span recorder; assert (a) span name `retrieval.retrieve`, (b) histogram `retrieval_latency_ms`, (c) histogram `retrieval_chunk_count`, (d) counter `retrieval_error_rate`, (e) tags `agent_name`, `jurisdiction`, `hazard_type`, (f) span attribute `retrieval_index_name`, (g) shared `correlation_id` with the Foundry inference span. (FR-RAG-OBS-01; Plan §F-A11.1 + §F-A11.2) → **Proves**: T234 + T235.

#### F-A11 — Implementation

- [X] T233 [Cluster A11] Add `opentelemetry-sdk`, `opentelemetry-instrumentation-azure-search-documents`, `opentelemetry-exporter-azure-monitor` to `apps/agents/pyproject.toml` and `apps/api/pyproject.toml`; pin minor versions; run `uv lock`. (Plan §Tech-stack additions; F-A11) → **Test**: import smoke.
- [X] T234 [Cluster A11] Wrap `RetrievalService.retrieve()` in `apps/agents/common/retrieval_service.py` in a dedicated OTel span emitting `retrieval_latency_ms` (histogram, p50/p95/p99), `retrieval_chunk_count` (histogram), `retrieval_error_rate` (counter); tags: `agent_name`, `jurisdiction`, `hazard_type`; transport via existing OTel-to-App-Insights bridge per spec 014 FR-016 — direct App-Insights SDK calls forbidden. (FR-RAG-OBS-01; Plan §F-A11.1) → **Test**: T232.
- [X] T235 [Cluster A11] Wrap the Foundry inference call (in `apps/agents/common/foundry_chat_client.py` + `apps/agents/maf_runtime/middleware/otel_middleware.py`) in a SEPARATE OTel span emitting `foundry_inference_latency_ms` so retrieval-only (Pass 1 Q-P1-06) and end-to-end (SC-012) SLOs are independently observable; both spans share the same `correlation_id` for trace stitching. (Plan §F-A11.2; closes F-ARCH-15 + F-DEL-06) → **Test**: T232.
- [X] T236 [Cluster A11] Wrap ingest pipeline in OTel spans at `apps/ingest-runner/src/ama_ingest/__main__.py` emitting `ingest_duration_seconds` (gauge), `chunks_processed` (counter), `embedding_calls` (counter), `ingest_errors` (counter). (FR-RAG-OBS-02; Plan §F-A11.3) → **Test**: ingest-run integration smoke.
- [X] T237 [P] [Cluster A11] Author Grafana dashboard `infra/dashboards/foundry-rag-ingest.json` (FR-RAG-OBS-02) AND Application Insights workbook `infra/bicep/modules/foundry-rag-success-criteria-dashboard.bicep` with tiles for SC-001..SC-019 (closes F-QA-03). (Plan §F-A11.3 + §F-A11.5) → **Test**: dashboard JSON lints clean; Bicep what-if green.
- [X] T238 [Cluster A11] Implement FR-RAG-OBS-03 latency alert — alert if **retrieval-only** p95 >500ms for >5 min (degraded performance; not a hard failure per Pass 1 Q-P1-06); Foundry inference governed independently by SC-012; both reported as separate App Insights metrics. Wire alert in `infra/bicep/modules/foundry-rag-alerts.bicep`. (FR-RAG-OBS-03; Plan §F-A11.4; mitigates R17) → **Test**: alert fires on synthetic 600ms p95 fixture; clears on recovery.

**Checkpoint F-A11**: dual OTel spans live; ingest metrics flow; SLO alert fires at retrieval-only p95 >500ms; SC dashboard published.

---

### F-A12 — Accessibility (WCAG 2.2 AA on `<CitationCard />`) [Cluster A12, SHOULD-class]

**Goal**: close R3 delivery memo F-DEL-05 keyboard-focus-trap finding on `<CitationCard />`. **Sequencing**: LAST in Phase F (per plan recommended ordering); UI components consume audit + metric fields landed earlier. Pre-condition: T238.

#### F-A12 — Tests (write red first)

- [X] T239 [P] [Cluster A12] Accessibility lint test `tests/web/src/components/citation/citation-card.axe.test.tsx` (jest-axe preferred) — assert WCAG 2.2 AA compliance on `<CitationCard />` rendered in default + expanded states; warn-only initially per F-A12.5. (FR-RAG-UI-01; Plan §F-A12.4) → **Proves**: T241 + T242.
- [X] T240 [P] [Cluster A12] Keyboard-accessibility tests at `tests/web/src/components/citation/citation-card.test.tsx` (Testing-Library) — assert (1) collapsible header `<button>` is in tab order, (2) `Enter` toggles expand/collapse, (3) `Space` toggles, (4) `aria-expanded` reflects state, (5) `aria-controls` references the body element id. (FR-RAG-UI-01; Plan §F-A12.1) → **Proves**: T241.

#### F-A12 — Implementation

- [X] T241 [Cluster A12] Refactor `<CitationCard />` at `apps/web/src/components/citation-card.tsx` — wrap collapsible header in `<button>` with `onClick`, `aria-expanded`, `aria-controls`, visible focus ring (`focus-visible:ring-2`); add `aria-label="Cite: <jurisdiction>/<topic>/handbook.md#page-N"` on each citation row; on grounded recommendation render, fire `aria-live="polite"` announcement: "Grounded recommendation with N citations". (FR-RAG-UI-01; Plan §F-A12.1..§F-A12.3) → **Test**: T240.
- [X] T242 [P] [Cluster A12] Add `jest-axe` (preferred) — alternative `pa11y` if jest-axe coverage is insufficient — to the existing UI-test pipeline at `apps/web/__tests__/` and `packages/ui/__tests__/`; gate at CI as a SHOULD (warn-only initially per F-A12.5; not blocking Step 9). Trigger: per-PR. (FR-RAG-UI-01; Plan §F-A12.4 + §Tech-stack additions) → **Test**: T239.
- [X] T243 [P] [Cluster A12] Author accessibility audit baseline at `docs/accessibility/spec-036-citation-card-baseline.md` documenting WCAG 2.2 AA conformance level achieved + known gaps + remediation roadmap; cross-reference R13 risk register update. (FR-RAG-UI-01; mitigates R13) → **Test**: doc exists.

**Checkpoint F-A12**: `<CitationCard />` keyboard-accessible; jest-axe lint warn-only; baseline doc published.

---

### F-ADR — ADR Body Authoring (8 stubs) [Cross-cluster]

**Goal**: author full bodies for ADR-12..ADR-19 stubs (currently scaffolded in `/speckit.plan`-phase). Mirrors prior Phase D ADR-authoring tasks T118–T126. **Sequencing**: parallelisable with each cluster's implementation — each ADR can be authored in parallel once its anchor cluster's tests are red.

- [X] T244 [P] [ADR-12] [Cluster A2] Author full body for `docs/decisions/036-foundry-rag-grounding/12-cultural-authority-gating.md` — Status, Context (Constitution VI-C non-negotiable; Indigenous Data Sovereignty; OOS-8), Decision (post-retrieval in-process gate, fail-closed for protected, registry-cache TTL 5 min, OPA flag-flip lock), Consequences, Cross-refs (FR-RAG-CA-01..05, T193–T203). → **Test**: ADR-12 file exists with non-stub Status section.
- [X] T245 [P] [ADR-13] [Cluster A1, A3] Author full body for `docs/decisions/036-foundry-rag-grounding/13-authority-precedence-ranking.md` — agency disambiguation + tie-break order (Pass 1 Q-P1-02), COMDISPLAN interlock, audit emission. (FR-RAG-AG-04 ext + FR-RAG-AC-01; T173–T192) → **Test**: ADR-13 file exists with non-stub Status section.
- [X] T246 [P] [ADR-14] [Cluster A5] Author full body for `docs/decisions/036-foundry-rag-grounding/14-approval-workflow-audit.md` — additive-nullable migration (Pass 2 Q-P2-01), 8 new fields rationale, Field-Coordinator offline boundaries. (FR-RAG-AG-02 ext + FR-RAG-LS-02 ext; T156–T165) → **Test**: ADR-14 file exists with non-stub Status section.
- [~] T247 [HUMAN-IN-LOOP] [ADR-15] [Cluster A6] Author full body for `docs/decisions/036-foundry-rag-grounding/15-federal-compliance-mapping.md` — Privacy Act 1988 APP 1/3/5/6/11 surfaces, ISM 2024 controls (ISM-0468, ISM-1552), PSPF audit-export, COMDISPLAN ranking. **Body publication requires HUMAN-IN-LOOP federal sign-off (NEMA + AGD + AFP) per A9 — same gate as T210.** Authority owners: **NEMA, AGD, AFP** (AIATSIS consulted). (FR-RAG-COMP-01..04; T204–T211) → **Test**: ADR-15 file exists with non-stub Status section + signed-attestation footer.
- [X] T248 [P] [ADR-16] [Cluster A7] Author full body for `docs/decisions/036-foundry-rag-grounding/16-blue-green-atomicity.md` — alias-pinning protocol, 5-min rollback SLO, Manual operator action class (Pass 2 Q-P2-08), 7-day previous-index retention. (FR-RAG-IDX-04a + FR-RAG-IDX-09; T166–T172) → **Test**: ADR-16 file exists with non-stub Status section.
- [X] T249 [P] [ADR-17] [Cluster A8] Author full body for `docs/decisions/036-foundry-rag-grounding/17-corpus-freshness.md` — nightly drift cron rationale, 14-day staleness alert at global-index scope (Pass 1 Q-P1-05), Reversible flag class. (FR-RAG-IDX-05a + FR-RAG-FRESH-01/02; T212–T217) → **Test**: ADR-17 file exists with non-stub Status section.
- [X] T250 [P] [ADR-18] [Cluster A9] Author full body for `docs/decisions/036-foundry-rag-grounding/18-multi-agent-conflict.md` — reactive post-return detector rationale (Pass 2 Q-P2-06), 4-class taxonomy, AIIMS escalation chain (Pass 1 Q-P1-03), Reversible flag. (FR-RAG-COORD-01/02; T225–T231) → **Test**: ADR-18 file exists with non-stub Status section.
- [X] T251 [P] [ADR-19] [Cluster A10] Author full body for `docs/decisions/036-foundry-rag-grounding/19-test-coverage-windows.md` — Windows-runner expansion, 50-agent Locust harness, golden-set v1 canonicalisation (Pass 1 Q-P1-08), per-PR/weekly/nightly cadence rationale. (FR-RAG-TEST-01..04; T218–T224) → **Test**: ADR-19 file exists with non-stub Status section.

**Checkpoint F-ADR**: 7 of 8 ADR bodies authored (ADR-12, 13, 14, 16, 17, 18, 19); ADR-15 body PENDING federal sign-off (T210/T247 HUMAN-IN-LOOP gate).

---

## Phase F — Dependencies & cross-references

### Sub-phase ordering (sequential within Phase F)

```text
T150 (Phase E close)
  ↓
F-A4 (T151–T155, single-PR coupled with amend-loop merge)
  ↓
F-A5 (T156–T165, audit shape — blocks A2/A3/A7/A9)
  ↓
F-A7 (T166–T172, atomicity protocol before any chunk-schema rebuild)
  ↓
F-A1+F-A3 (T173–T192, co-scheduled blue-green rebuild of corpus-v{N+1})
  ↓
F-A2 (T193–T203, cultural-authority gate; T202+T203 are HUMAN-IN-LOOP go-live blockers)
  ↓
F-A6 (T204–T211, federal compliance scaffolding; T210 HUMAN-IN-LOOP go-live blocker)
  ↓
F-A8 (T212–T217) + F-A10 (T218–T224)   [parallel-safe between sub-phases]
  ↓
F-A9 (T225–T231, requires F-A5 conflict_group_id field)
  ↓
F-A11 (T232–T238, OTel spans use audit fields as attributes)
  ↓
F-A12 (T239–T243, SHOULD-class — last because UI consumes earlier-landed metric+audit fields)
  ↓
F-ADR (T244–T251, parallel with each anchoring cluster's implementation)
```

### Cluster → tasks (Phase F)

| Cluster | Tasks | Count | Anchored ADR |
|---|---|---|---|
| A1 (agency disambiguation) | T173, T175, T178, T181, T183, T189, T191 | 7 | ADR-13 |
| A2 (cultural authority) | T193–T203 | 11 | ADR-12 |
| A3 (authority precedence) | T174, T176, T177, T179, T182, T184, T185, T186, T187, T190, T192 | 11 | ADR-13 |
| A1+A3 (shared rebuild) | T180, T188 | 2 | ADR-13 |
| A4 (rego bug-fix) | T151–T155 | 5 | (FR-RAG-CV-01 only) |
| A5 (audit shape) | T156–T165 | 10 | ADR-14 |
| A6 (federal compliance) | T204–T211 | 8 | ADR-15 |
| A7 (blue-green atomicity) | T166–T172 | 7 | ADR-16 |
| A8 (corpus freshness) | T212–T217 | 6 | ADR-17 |
| A9 (multi-agent conflict) | T225–T231 | 7 | ADR-18 |
| A10 (test coverage) | T218–T224 | 7 | ADR-19 |
| A11 (observability) | T232–T238 | 7 | (FR-RAG-OBS-01..03 only) |
| A12 (accessibility) | T239–T243 | 5 | (FR-RAG-UI-01 only) |
| ADR body authoring | T244–T251 | 8 | ADR-12..ADR-19 |
| **Phase F total** | T151–T251 | **101** | |

### HUMAN-IN-LOOP escalation paths (Phase F)

| Task | Authority owners | What is required | Blocks |
|---|---|---|---|
| T202 | NEMA + AFAC + ≥3 Indigenous community representatives + AIATSIS Ethics Committee | Initial registry seeding (registry container provisioned empty by T196; population requires sign-off) | Production go-live (SC-014); does NOT block amend-loop merge |
| T203 | NEMA + AFAC + Land Councils (NLC, CLC, ALT, APY) + AIATSIS Ethics Committee + ≥3 Indigenous community representatives | Corpus body authoring (Indigenous-language translations, Sacred Site protocols, ALT/APY consent gates) | Production go-live (FR-RAG-CA-01..03); does NOT block amend-loop merge |
| T210 | NEMA + AGD + AFP (AIATSIS consulted) | Federal sign-off attestation on `docs/compliance/ISM-2024-mapping.md`; produce `ISM-2024-mapping-signoff.json` | Production go-live (SC-018); does NOT block amend-loop merge |
| T247 | NEMA + AGD + AFP | ADR-15 body publication requires the same federal sign-off as T210 | ADR-15 body publication only; ADR-15 stub already landed |

### Cross-cluster blockers (explicit)

| Constraint | Source | Impact on numbering |
|---|---|---|
| A4 (rego) MUST land in same PR as Phase F merge | Pass 2 Q-P2-03 | T151–T155 are the FIRST Phase F tasks; CI guard at T155 enforces single-PR coupling |
| A5 (audit shape) BEFORE A2/A3/A7/A9 | Cross-cluster matrix lines 522–528 | T156–T165 precede T166+ |
| A7 (atomicity) BEFORE A1+A3 chunk-schema rebuild | Cross-cluster matrix line 526 | T166–T172 precede T188 (rebuild) |
| A1+A3 co-scheduled blue-green rebuild | Plan §F-A1.4 + §Updated phase ordering | T188 is the single rebuild trigger consumed by both clusters |
| A11 (OTel) AFTER A5 | Cross-cluster matrix line 530 | T232+ precede nothing inside Phase F but consume A5 fields |
| A6 federal sign-off (T210, T247) → blocks production go-live, NOT amend-loop merge | Plan §F-A6.5 + R15 | Marked HUMAN-IN-LOOP; CD gate at T211 enforces |
| A2 corpus body / registry seeding (T202, T203) → blocks production go-live | OOS-8 + A9 | Marked HUMAN-IN-LOOP; CD gate at T196 + signoff verification enforces |
| A10 test fixtures reference A1/A3/A5/A7 | Plan §F-A10 | T220 (golden-set v1) consolidates fixtures landed in T189 + T190; T221 (E2E) requires T168 (alias pinning) and T169 (`retrieval_index_name`) |

### Phase F FR → tasks

| FR | Implementation task(s) | Test task(s) |
|---|---|---|
| FR-RAG-CV-01 (extended; prod 3-approver) | T152, T153, T154, T155, T211 | T151 |
| FR-RAG-AG-02 (extended; new audit fields) | T161, T163, T164 | T156, T157, T159 |
| FR-RAG-AG-04 (extended; agency disambig) | T178, T181, T183, T189, T191 | T173, T175 |
| FR-RAG-AC-01 | T179, T182, T184, T185, T190, T192 | T174, T176 |
| FR-RAG-LS-02 (extended; FC offline boundary) | T165 | T158 |
| FR-RAG-CA-01..05 | T196, T197, T198, T199, T200, T201, T202, T203 | T193, T194, T195 |
| FR-RAG-COMP-01..04 | T206, T207, T208 (→ T186), T209, T210, T211 | T204, T205 |
| FR-RAG-COORD-01/02 | T227, T228, T229, T230, T231 | T225, T226 |
| FR-RAG-FRESH-01/02 | T214, T215, T216, T217 | T212 |
| FR-RAG-IDX-04a | T168, T169, T171 | T166, T167 |
| FR-RAG-IDX-05a | T213 | T212 |
| FR-RAG-IDX-09 | T170, T172 | T167, T221 |
| FR-RAG-OBS-01..03 | T233, T234, T235, T236, T237, T238 | T232 |
| FR-RAG-TEST-01..04 | T218, T219, T220, T221, T222, T223, T224 | tests are the deliverables |
| FR-RAG-UI-01 (SHOULD) | T241, T242, T243 | T239, T240 |

### Phase F SC → tasks

| SC | Tasks |
|---|---|
| SC-013 (≥95% agency-disambiguation) | T173, T189, T191 |
| SC-014 (cultural-authority sign-off) | T196, T202, T203 |
| SC-015 (≥95% Commonwealth-first ACT) | T174, T190, T192 |
| SC-016 (3-approver prod / 2-approver dev) | T151, T152, T153, T155 |
| SC-017 (100% override audit completeness) | T159, T161, T163 |
| SC-018 (ISM-2024 + PSPF export) | T205, T207, T209, T210, T211 |
| SC-019 (blue-green ≤5min rollback) | T167, T168, T169, T170, T221 |

### Phase F Risk → mitigation tasks

| Risk | Mitigation tasks |
|---|---|
| R14 (cultural-authority partial population) | T196, T201, T202, T203 |
| R15 (federal compliance attestation slip) | T209, T210, T211, T247 |
| R16 (multi-agent conflict false positives) | T229, T231 |
| R17 (OTel bridge degradation) | T234, T235, T237, T238 |
| R18 (legacy nullable rows leak) | T156, T161, T162 |
| R7 update (alias flip cutover timeout) | T167, T170, T172 |
| R13 update (citation a11y regression) | T239, T240, T241, T242, T243 |

---

## Phase F — Implementation strategy notes

- **Single-PR merge constraint**: F-A4 (T151–T155) MUST land in the same PR as the Phase F merge. CI guard at T155 enforces.
- **HUMAN-IN-LOOP boundary**: T202, T203, T210, T247 are tracked here but performed outside this AI workflow. They block production go-live, NOT amend-loop merge. CD gates at T196 (registry seeding) + T211 (federal sign-off) are the binding enforcement points.
- **Co-scheduled rebuild**: F-A1 + F-A3 share a single blue-green rebuild pass (T188); chunk-schema field additions for F-A2 (T200) co-deploy in the same rebuild. F-A7 atomicity protocol (T168) is the prerequisite that makes this safe.
- **Reversibility classes**: every amend-loop flag follows Pass 2 Q-P2-08 — `cultural_authority_gate.enabled` is **Locked-on in prod** (T201 OPA-blocks flips); `authority_precedence_ranking.enabled`, `corpus_freshness_alert.enabled`, `multi_agent_conflict_detection.enabled` are **Reversible** (≤5-min flip via spec-029 FR-008); `index_rollback` is **Manual operator action** (T170 5-min SLO + Release Manager approval).
- **Phase F tests**: every cluster has at least one red-first test task (T151, T156–T159, T166–T167, T173–T177, T193–T195, T204–T205, T212, T225–T226, T232, T239–T240). Implementation tasks reference the proving test in their `→ Test:` annotation.

---

*End of Phase F appendix — total Phase F tasks = **101** (T151–T251); grand total tasks.md = **T001–T251 with 10 known gaps at T7–T9, T59, T104–T109 ⇒ 241 distinct task IDs**. **Next command** after Phase F implementation: re-run `/speckit.analyze` to validate cross-artefact consistency post-amend-loop.*


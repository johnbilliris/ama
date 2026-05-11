# Spec 036 — Cross-Artefact Consistency Analysis (T150)

**Date**: 2026-05-08
**Scope**: Manual cross-reference walk between `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `contracts/` after Phase D close. Substitutes for a recursive `/speckit.analyze` invocation per Phase E execution rules.
**Result**: ✅ **No drift detected**. Every FR / SC / Entity / Contract referenced in any one artefact resolves cleanly across the others. Spec is shippable pending the user's Step 9 cutover (T145, T146, T147 partials).

---

## 1 — Functional-Requirement coverage matrix

All **43 FR-RAG-** functional requirements referenced by `spec.md` are bound to ≥ 2 tasks in `tasks.md` (so each has at least one test task and one implementation task). The minimum-coverage row is FR-RAG-NS-09 / FR-RAG-FM-02 / FR-RAG-FM-03 etc. at 2 mentions, which is the expected lower bound for a single-FR carve-out (one test, one impl/lint). The headline coverage rows are FR-RAG-FM-06 (22 mentions — the master canary-gate FR threading every per-agent canary task) and FR-RAG-LS-02 (16 mentions — the offline-cache FR threading the entire Phase D bundle).

| FR group | FRs in spec | All bound? | Phase coverage |
|---|---|---|---|
| FM (Foundry migration) | FM-01..07 (7) | ✅ | Phase 0 (T001–T015) + Phase A (T028–T065 migrations) + Phase E T146 (legacy deletion) |
| CV (Carve-out enforcement) | CV-01..04 (4) | ✅ | Phase 0 (T011 lint) + Phase B carveout-registry tasks |
| IDX (Indexing / corpus build) | IDX-01..08 (8) | ✅ | Phase B (T058 ai-search.bicep blue-green; T060 ingest-runner; T065 corpus_build_sha) |
| AG (Agent grounding) | AG-01..06 (6) | ✅ | Phase C (T078–T092 RetrievalService + citation filter + audit) |
| NS (RAG-opt-out carve-outs) | NS-01..09 (9) | ✅ | Phase B + Phase D (T138 RAG-OPTOUT lint + 9 ADRs) |
| SIM (Simulation grounding) | SIM-01..06 (6) | ✅ | Phase C (T085–T088 simulation grounding) + Phase E T142, T145 |
| LS (Life-safety / offline) | LS-01..03 (3) | ✅ | Phase D (T120–T140 offline cache + dual signature) |

**Verdict**: zero unbound FRs.

---

## 2 — Success-Criteria coverage matrix

All **12 SC-** success criteria are bound to ≥ 2 tasks. SC-011 has the broadest binding (6 mentions) reflecting its role as the byte-replay reproduction floor; SC-001 (corpus-coverage), SC-012 (latency p95) sit at 2 mentions each which is the expected floor for objective-only criteria measured by single eval-runner tasks.

| SC | What it measures | Tasks bound |
|---|---|---|
| SC-001 | Corpus coverage of every recommendation | 2 |
| SC-002 | No legacy `from openai` imports | 3 |
| SC-003 | 50-query golden parity | 4 |
| SC-004 | Citation envelope present every grounded turn | 3 |
| SC-005 | Hallucinated citation rate < 1% | 3 |
| SC-006 | Carveout registry coverage | 3 |
| SC-007 | RAG-opt-out comment density | 3 |
| SC-008 | Offline cache integrity (dual sig) | 3 |
| SC-009 | Offline cache TTL enforcement | 3 |
| SC-010 | Multi-jurisdiction disambiguation | 4 |
| SC-011 | Audit byte-replay ≥ 95% | 6 (Phase E T144 KQL alert closes the loop) |
| SC-012 | Simulation latency ≤ +30% p95 | 2 |

**Verdict**: zero unbound SCs.

---

## 3 — Entity coverage matrix

`data-model.md` declares 13 entities. Every entity has at least one schema mirror under `contracts/` or `packages/domain/` and at least one Phase A–E test that exercises its invariants.

| Entity | Schema mirror | Test anchor | Status |
|---|---|---|---|
| CorpusEntry | reuses `docs/corpus/*/manifest.json` | `tests/contract/test_corpus_manifest.py` | ✅ |
| Chunk | `infra/modules/ai-search.bicep` index schema | `tests/integration/test_ingest_runner_chunks.py` | ✅ |
| RetrievalRequest | `contracts/retrieval-service.md` | `tests/contract/test_retrieval_request_shape.py` | ✅ |
| RetrievalResult | `contracts/retrieval-service.md` | `tests/contract/test_retrieval_result_shape.py` | ✅ |
| Citation | `contracts/citation-envelope.json` | `tests/contract/test_citation_envelope.py` + Phase C citation filter | ✅ |
| AuditRecord (LLM-call) | `contracts/audit-record-llm-call.json` | `tests/contract/test_audit_record_llm_call.py` + Phase E T144 byte-replay | ✅ |
| CarveoutRegistryEntry | `data/carveout_registry.json` schema | `tests/contract/test_carveout_registry.py` | ✅ |
| OfflineCacheManifest | `contracts/offline-cache-manifest.json` | `tests/contract/test_offline_cache_manifest.py` + `infra/scripts/verify-offline-cache.ps1` | ✅ |
| RagOptoutAdr | `docs/decisions/036-foundry-rag-grounding/0?-rag-optout-*.md` (×9) | `tools/lint/check_rag_optout_bindings.py` | ✅ |
| EquivalenceTestResult | `packages/domain/src/ama_domain/equivalence_test_result.py` | `tests/contract/test_equivalence_test_result.py` (Phase E T143, 9 passed) | ✅ |
| FoundryClient (alias) | `apps/eval-runner/src/ama_eval/foundry_client.py` reference impl | `tests/contract/test_foundry_chat_client.py` | ✅ |
| FinalCanaryGateResult (NEW Phase E) | `apps/eval-runner/src/ama_eval/per_agent_canary_gate.py` | `tests/unit/test_spec036_final_canary_gate.py` (Phase E T142, 6 passed) | ✅ |
| RagOptoutContext (subset of AuditRecord) | inlined into AuditRecord JSON schema | `tests/integration/test_rag_optout_audit_path.py` | ✅ |

**Verdict**: zero unbound entities. EquivalenceTestResult (T143) and FinalCanaryGateResult (T142) were the two Phase E additions; both are now schema-mirrored and tested.

---

## 4 — Contract coverage matrix

| Contract file | Producer | Consumer(s) | Validating test |
|---|---|---|---|
| `contracts/audit-record-llm-call.json` | RetrievalService + agent runtime | App Insights `FoundryRAGAudit` table; replay tooling | `tests/contract/test_audit_record_llm_call.py` + Phase E `tests/contract/test_audit_replay_fidelity.py` (9 passed) |
| `contracts/citation-envelope.json` | Citation filter (Phase C) | Agent SSE; Simulation SSE; Audit log | `tests/contract/test_citation_envelope.py` + integration test for SSE citation events |
| `contracts/foundry-chat-client.md` | `apps/agents/common/llm_client.py` (after T146); `apps/eval-runner/src/ama_eval/foundry_client.py` reference | All agents; Simulation; eval-runner | `tests/contract/test_foundry_chat_client.py` |
| `contracts/ingest-pipeline.md` | `apps/ingest-runner` | AI Search index `corpus-vN` | `tests/integration/test_ingest_runner_*` |
| `contracts/offline-cache-manifest.json` | Build pipeline (cosign keyless + age detached sig) | Field-Coordinator devices via `infra/scripts/verify-offline-cache.ps1` | `tests/contract/test_offline_cache_manifest.py` + smoke run |
| `contracts/retrieval-service.md` | `apps/agents/common/retrieval_service.py` | All RAG-binding agents | `tests/contract/test_retrieval_service.py` + integration tests per agent |

**Verdict**: every contract has a producer, consumer(s), and a validating test. Zero orphans.

---

## 5 — Tasks ↔ Plan phase alignment

`plan.md` declares **Phase 0, A, B, C, D, E** with task ranges. `tasks.md` mirrors those phase headers. Cross-check:

| Plan phase | Plan task range | tasks.md actual range | Match? |
|---|---|---|---|
| Phase 0 (foundations) | T001–T015 | T001–T015 | ✅ |
| Phase A (per-agent migration scaffolding) | T016–T065 | T016–T065 | ✅ |
| Phase B (corpus + index) | T066–T077 | T066–T077 | ✅ |
| Phase C (RetrievalService + citation + canaries 1–5) | T078–T108 + T093–T097 partial | T078–T108 + T093–T097 `[~]` | ✅ |
| Phase D (offline cache + RAG-OPTOUT lint + ADRs) | T109–T141 | T109–T141 | ✅ |
| Phase E (final canary, deletion, sweep, analyze) | T142–T150 | T142–T150 | ✅ |

**Verdict**: zero phase-numbering drift. Phase C has 5 declared partials (T093–T097 — per-agent live env-var flips) and Phase E has 3 partials (T145, T146, T147 — Simulation flip, atomic legacy deletion, azd up). All partial markers carry the explicit "pending Step 9" rationale.

---

## 6 — Spec-cross-reference integrity

`spec.md` cites the following sister specs; each citation is honoured in `plan.md` references and `tasks.md` task-binding columns:

- **Spec 014** (template fallback chain) — preserved via FR-RAG-FM-06 and the "collapse `_generate_with_fallback` to template-only" requirement on T146.
- **Spec 024** (simulation chat baseline + SSE) — extended by FR-RAG-SIM-01..06 + `apps/api/app/services/simulation/controller_service.py` migration.
- **Spec 029** (progressive-delivery feature flags) — gates the per-agent canary cut-overs (T093–T097, T145).
- **Spec 032** (cosign keyless signing) — reused by FR-RAG-LS-02 dual-signature offline cache.
- **Spec 033** (FR-023 equivalence test) — extended by EquivalenceTestResult (T143) with `citation_fidelity` + `verbatim_source_match` + `corpus_build_sha` + `embedding_model_id`.
- **Constitution Principles I–VI** — every FR carries the principle anchor in its rationale clause.

**Verdict**: zero broken sister-spec references.

---

## 7 — Outstanding "Open Questions" / Clarifications

`spec.md` § "Closed Questions" (renamed from "Open Questions" by T149) — **all** Pass-1 (3 items) and Pass-2 (4 items) clarifications struck-through and marked Resolved 2026-05-08. **None** outstanding at Phase E close.

---

## 8 — Drift hotspots checked, none found

Manually walked the following high-risk drift surfaces:

1. **`embedding_model_id` shape**: spec says `text-embedding-3-large@1`; plan.md, data-model.md, smoke-test (`infra/scripts/azd-up-smoke-test.ps1`), `EquivalenceTestResult` test fixtures, and `corpus_build_sha` audit field all use the identical literal. ✅ no drift.
2. **Index alias naming**: spec FR-RAG-IDX-04 says `corpus-vN`; ai-search.bicep uses `corpus-v\d+` regex; smoke-test asserts `corpus-v\d+`; ingest-runner emits `corpus-v{N+1}`. ✅ no drift.
3. **AAD scope**: spec FR-RAG-FM-05 says `https://cognitiveservices.azure.com/.default`; `apps/eval-runner/src/ama_eval/foundry_client.py` and Phase A migrations use the same scope literally. ✅ no drift.
4. **Canary equivalence thresholds**: spec FR-RAG-FM-06 says `≥ 95% decision-equivalence + 100% schema-equivalence`; `per_agent_canary_gate.py` uses `DECISION_EQUIVALENCE_MIN = 0.95` + `SCHEMA_EQUIVALENCE_MIN = 1.00`; T142 final-gate adds `citation_fidelity ≥ 0.7` + `verbatim_source_match ≥ 0.9` (matching FR-RAG-AG-05). EquivalenceTestResult pydantic model duplicates these constants — flagged in module docstring as deliberate split (domain package can't import eval-runner). ✅ no drift; the duplication is intentional and documented.
5. **Offline-cache TTL**: spec FR-RAG-LS-02 says 14 days; `OfflineCacheManifest.ttl_days` defaults to 14; `verify-offline-cache.ps1` enforces 14. ✅ no drift.
6. **Per-agent feature-flag map**: spec mentions `foundry_rag_enabled_agents.{Monitoring,RiskAssessment,Evacuation,ResourceAllocation,Communication,SimulationController}`; the canary tasks T093–T097 + T145 cover all 6 in the same order. ✅ no drift.

---

## 9 — Tally

- 43 / 43 FRs covered
- 12 / 12 SCs covered
- 13 / 13 entities covered
- 6 / 6 contracts validated
- 6 / 6 plan phases aligned with tasks.md
- 6 / 6 sister-spec citations honoured
- 0 / 0 outstanding clarifications

**Final analyze verdict**: ✅ **PASS**. Spec 036 is internally consistent, fully bound, and shippable pending the user's Step 9 cutover. No remediation required before merge to `main`.

---

## 10 — Recommended next step (per spec instruction)

The user's workflow next step is **Step 8: Persona Round 3 review** — surface any meritorious findings for the amend loop. After Round 3 sign-off:

- Step 9a — flip `FEATURE_FOUNDRY_RAG_SIMULATION=1` in production (closes T145)
- Step 9b — review and merge the `036-legacy-deletion` draft PR (closes T146)
- Step 9c — `azd up` redeploy + run `infra/scripts/azd-up-smoke-test.ps1` (closes T147)

After Step 9c green, all 140 tasks transition from `[~]` to `[X]` and the spec is shipped.

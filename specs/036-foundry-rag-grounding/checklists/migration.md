# Migration & Citation-Contract Quality Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the OpenAI → Foundry migration, the contract-test seam, and the end-to-end citation contract are specified to a level a reviewer can verify before planning.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion checklists**:
- [requirements.md](./requirements.md) — Spec quality fundamentals
- [compliance.md](./compliance.md) — Constitution / residency / opt-out / index-lifecycle / offline-cache

> **Scope of this file**: The three coverage areas where *runtime safety of the cutover and the audit trail* depend on the spec being unambiguous: **Migration Safety** (Coverage Area 3), **Test Instrumentation** (Coverage Area 5), and **Citation Contract End-to-End** (Coverage Area 2).

> **Item numbering**: Continues from `requirements.md` (CHK083+).

## Migration Safety *(Coverage Area 3)*

> **Authority**: User input bullet 3 — "FR-RAG-FM-06 cutover canary + spec-033 FR-023 equivalence + spec-029 feature flag wiring are checkable."

- [ ] CHK083 Does FR-RAG-FM-06 explicitly bind the cutover to **spec-029 progressive-delivery feature flags** by spec ID (not just by mechanism description)? [Traceability, Spec §FR-RAG-FM-06 vs `specs/029-progressive-delivery-pipeline/spec.md`]
- [ ] CHK084 Does FR-RAG-FM-06 explicitly bind the per-agent canary gate to **spec-033 FR-023 equivalence** (≥ 95% decision-equivalence on categorical output fields + 100% schema-equivalence on populated fields), citing the spec-033 ID? [Traceability, Spec §FR-RAG-FM-06 vs `specs/033-maf-adoption/spec.md` §FR-023]
- [ ] CHK085 Does FR-RAG-FM-06 require the **spec-014 `_generate_with_fallback` template-fallback chain** to remain intact across the entire migration window, so any Foundry-side regression downgrades to template fallback rather than silencing the agent (Constitution Principle I)? [Coverage, Spec §FR-RAG-FM-06 vs `specs/014-azure-openai-integration/spec.md`]
- [ ] CHK086 Is the **lint-binds-atomically-in-final-PR** semantics (FR-RAG-FM-04 vs FR-RAG-FM-06) testable from a CI history — i.e., does the spec make clear the lint MUST NOT fire on in-flight per-agent canaries while legacy imports are still required? [Acceptance Criteria, Spec §FR-RAG-FM-04 / §FR-RAG-FM-06]
- [ ] CHK087 Are **rollback requirements** defined for a per-agent canary that fails its FR-023 equivalence gate after partial rollout (does the feature flag flip back? Does the legacy client become the active path? Are queued audit entries reconciled?)? [Recovery, Gap, Spec §FR-RAG-FM-06]
- [ ] CHK088 Is "decision-equivalence on categorical output fields" defined either inline OR by clean reference to spec-033 FR-023's enumeration (escalate/suppress/enrich, hazard severity bucket, evacuation stage, alert approval-required flag) — without re-defining? [Clarity, Spec §FR-RAG-FM-06 vs `specs/033-maf-adoption/spec.md` §FR-023]
- [ ] CHK089 Are **migration-window observability requirements** specified — i.e., which dashboards / metrics / alerts indicate canary health per agent, and how a Principal Engineer notices when the canary is degrading? [Gap, Spec §FR-RAG-FM-06]
- [ ] CHK090 Does the spec specify the **cutover ordering** across the six agents + simulation, or explicitly defer to planning while preserving the no-silencing invariant? [Clarity, Spec §FR-RAG-FM-06]
- [ ] CHK091 Is the **gateway behaviour during cutover** specified for the case where a Foundry deployment in the carve-out registry is mid-rotation (deprecated `review_date` in 12 hours but a canary is still running)? [Edge Case, Gap, Spec §FR-RAG-CV-02 vs §FR-RAG-FM-06]
- [ ] CHK092 Is the **migration audit trail** specified — does every per-agent flip emit a structured event (which agent, which canary cohort, FR-023 result, model_id, model_version, deployment_alias) so post-mortem analysis is deterministic? [Coverage, Gap, Spec §FR-RAG-FM-06 vs Constitution Principle IV]

## Test Instrumentation *(Coverage Area 5)*

> **Authority**: User input bullet 5 — "FR-RAG-FM-07 constructor-injectable Foundry seam is exercised by contract tests without hitting the live endpoint."

- [ ] CHK093 Does FR-RAG-FM-07 **explicitly enumerate** which contract tests MUST be runnable with the constructor-injected `chat_complete` callable: citation attachment (FR-RAG-AG-03), retrieval-then-inference sequencing (FR-RAG-AG-01 → AG-02), hallucinated-citation suppression (FR-RAG-AG-05), simulation `citation` SSE emission (FR-RAG-SIM-02), and RAG-opt-out audit paths (FR-RAG-NS-01..09)? [Coverage, Spec §FR-RAG-FM-07]
- [ ] CHK094 Is the **`FoundryResponse`-shaped payload** that the test seam returns specified in enough detail that a `FakeFoundryClient` is implementable from the spec alone (without reading the Azure AI Inference SDK)? [Clarity, Spec §FR-RAG-FM-07]
- [ ] CHK095 Is the **prohibition on monkey-patching the Azure AI Inference SDK transport** explicit in FR-RAG-FM-07 — i.e., the spec forbids tests from reaching into the SDK internals? [Clarity, Spec §FR-RAG-FM-07]
- [ ] CHK096 Does FR-RAG-FM-07 cover **all three migrated call sites** by name (`apps/agents/common/llm_client.py`, MAF `chat_client` factory in `apps/agents/maf_runtime/chat_client.py`, simulation `controller_service` in `apps/api/app/services/simulation/controller_service.py`)? [Coverage, Spec §FR-RAG-FM-07 vs §FR-RAG-FM-01..03]
- [ ] CHK097 Is the requirement that **production wiring uses the real SDK transport** AND that **tests must NOT need a live Foundry endpoint** measurable from a CI test-suite log (e.g., a CI assertion that no test pulls a Foundry token at runtime)? [Acceptance Criteria, Spec §FR-RAG-FM-07]
- [ ] CHK098 Is the test-seam's **relationship to the eval-runner reference** (`apps/eval-runner/src/ama_eval/foundry_client.py`'s docstring `"Designed so unit tests can substitute a fake by injecting a different chat_complete callable"`) cited by name so contributors can copy the proven pattern? [Traceability, Spec §FR-RAG-FM-07 vs `apps/eval-runner/src/ama_eval/foundry_client.py`]
- [ ] CHK099 Are the **constructor signatures** (or the optional callable parameter name) consistent enough across the three migrated call sites that a single fixture can drive all three — or does each site have its own contract? [Consistency, Spec §FR-RAG-FM-07]
- [ ] CHK100 Is there a **negative-test requirement** — i.e., the spec mandates a test that asserts the production path refuses to start when the injected callable is `None` AND no Foundry deployment is configured? [Gap, Spec §FR-RAG-FM-07]

## Citation Contract End-to-End *(Coverage Area 2)*

> **Authority**: User input bullet 2 — "Token shape `<jurisdiction>/<topic>/handbook.md#page-N` is testable from agent log → Cosmos audit doc → Risk Manager UI → Simulation chat panel."

- [ ] CHK101 Is the citation token shape `<jurisdiction>/<topic>/handbook.md#page-N` defined with **each segment's value space** specified (jurisdiction enum from FR-RAG-IDX-08, topic taxonomy source, page integer constraints) so the token is parseable by both code and humans? [Clarity, Spec §FR-RAG-AG-03]
- [ ] CHK102 Is the **agent-log → Cosmos audit doc** projection of citations specified — which fields land where, embedded vs referenced storage, and whether the page number is stored as integer or string? [Clarity, Spec §FR-RAG-AG-02]
- [ ] CHK103 Is the **Risk Manager UI rendering** of citations (the destination for the recommendation card link to rendered Markdown + original PDF URL per FR-RAG-AG-03) specified at requirement level (link target, fallback when PDF URL is unreachable)? [Coverage, Spec §FR-RAG-AG-03]
- [ ] CHK104 Is the **Simulation chat panel citation surface** (SSE `citation` event payload schema) specified field-for-field in FR-RAG-SIM-02 and **consistent** with the agent recommendation card's citation token shape per FR-RAG-AG-03? [Consistency, Spec §FR-RAG-SIM-02 vs §FR-RAG-AG-03]
- [ ] CHK105 Is the **end-to-end testability** of the citation contract (agent log → audit doc → UI → SSE) addressable by the FR-RAG-FM-07 test seam without a live Foundry endpoint — i.e., the citation can be asserted at every hop in a hermetic test? [Test Instrumentation, Spec §FR-RAG-FM-07 vs §FR-RAG-AG-03]
- [ ] CHK106 Are requirements defined for **citation rendering when the cited page span crosses pages** (e.g., `#page-N..M`) or when a chunk has **no page anchor** (e.g., front-matter chunks, table-of-contents chunks)? [Edge Case, Gap, Spec §FR-RAG-AG-03]
- [ ] CHK107 Is the **hallucinated-citation suppression** behaviour (FR-RAG-AG-05) testable end-to-end — i.e., the output is muted in the recommendation card AND a `hallucinated_citation` log entry is written AND confidence is downgraded? [Acceptance Criteria, Spec §FR-RAG-AG-05]
- [ ] CHK108 Is the **`sha256_of_chunk`** field defined as the SHA-256 of the chunk text only, or of the chunk + metadata — and is that consistent across FR-RAG-IDX-03, FR-RAG-AG-02, and FR-RAG-SIM-02? [Clarity, Spec §FR-RAG-IDX-03 / §FR-RAG-AG-02 / §FR-RAG-SIM-02]
- [ ] CHK109 Is the **`source_url`** field semantics specified — does it point to the rendered Markdown page anchor, the original PDF URL, both, or is it publisher-canonical only? [Clarity, Spec §FR-RAG-SIM-02 / §Key Entities `Citation`]
- [ ] CHK110 Is the **citation rendering for `mode: metadata-only` entries** specified — can a citation point to a metadata-only entry, and if so, what does the page anchor look like (since there is no body to anchor into)? [Edge Case, Gap, Spec §FR-RAG-IDX-02 vs §FR-RAG-AG-03]
- [ ] CHK111 Is the **`corpus_build_sha`** propagation specified end-to-end (chunk → retrieval result → audit record → simulation SSE) so deterministic replay (SC-011) is reproducible? [Traceability, Spec §FR-RAG-IDX-03 / §FR-RAG-AG-02 / §FR-RAG-SIM-04 / §SC-011]
- [ ] CHK112 Is the **`embedding_model_id`** propagation specified end-to-end so that historical audit entries can prove which embedding model grounded each recommendation (relevant when cross-checking a blue-green flip per FR-RAG-IDX-04)? [Traceability, Spec §FR-RAG-IDX-03 / §FR-RAG-AG-02 vs §FR-RAG-IDX-04]
- [ ] CHK113 Is there a defined behaviour for **citations that no longer resolve** (the cited handbook entry has been moved to `mode: excluded` post-decision, or the corpus_build_sha is no longer indexed) — does the audit reconstruction view degrade gracefully? [Edge Case, Gap, Spec §FR-RAG-AG-02]

## Notes

- **Item count (this file)**: 31 items across 3 sections (CHK083-CHK113).
- **Cross-references**: Items in this file frequently cite spec-029 (`specs/029-progressive-delivery-pipeline/spec.md`), spec-033 (`specs/033-maf-adoption/spec.md`), and the eval-runner reference (`apps/eval-runner/src/ama_eval/foundry_client.py`). Reviewers should have those open.
- **Why these three areas live together**: All three are *test-time validations of a runtime invariant*. The migration cutover (Area 3), the test seam (Area 5), and the citation contract (Area 2) are jointly checkable from CI without a live Foundry endpoint — that joint checkability is itself a quality property of the spec.
- **Numbering continues** in [compliance.md](./compliance.md) at CHK114.

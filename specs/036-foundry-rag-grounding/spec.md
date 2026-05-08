# Feature Specification: Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat

**Feature Branch**: `036-foundry-rag-grounding`
**Created**: 2026-05-08
**Status**: Draft
**Input**: User description: "A large volume of corpus data has been identified and stored in `docs/corpus/`. All judgements need to be grounded with this context. Provide a Microsoft Foundry-based RAG implementation; migrate existing OpenAI deployments to Foundry; index the corpus in Azure; deploy via azd / CI-CD; have all agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Dependency Notifier, Communication) interact with the LLM endpoint to ensure life-safety fitness; and extend the simulation chat to use the same corpus."

> **Persona consultation note** — Inputs from operational personas (10 AIIMS roles in `personas-input/operational.md`), eastern-state sector personas (15 agencies in `personas-input/sectors-eastern.md`), southern/western personas (12 agencies in `personas-input/sectors-southern-western.md`), territory personas (12 agencies in `personas-input/sectors-territories.md`), Commonwealth personas (11 agencies in `personas-input/sectors-commonwealth.md`), and cross-sector personas (8 cohorts in `personas-input/sectors-crosssector.md`) — 68 personas across 6 memos — were consulted prior to drafting. Their cross-cutting requirements drive the user stories, FRs, edge cases, and acceptance criteria below: life-safety primacy, AIIMS provenance, jurisdiction-disambiguated citations, ATSI/CALD/Auslan accessibility, NERAG-grounded risk, append-only auditability, degraded-connectivity offline cache, and explicit RAG-carve-outs for live forecast / seismic / classified / pure-collection paths.

---

## Relationship to Existing Specs *(authoritative — extends, supersedes, references)*

This feature **extends** the AIDR-only RAG scope first introduced in spec
[032 *Rubric Improvements*](../032-rubric-improvements/spec.md) (FR-AI01..FR-AI10) to the **whole** of `docs/corpus/` (national + every state/territory + Commonwealth + agency operational doctrine + hazard-specialty material), and **migrates** the production model plane from Azure OpenAI to Microsoft Foundry. It does **not** redefine the Foundry carve-out registry: this spec **reuses** spec 032's `FR-AI03a` mechanism at `infra/parameters/foundry-carveout.yaml` and tightens it so every Foundry deployment landed by this feature is recorded there before deploy.

| Spec | Relationship |
|---|---|
| 014 Azure OpenAI Integration | **Migrated** — `apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py`, and `apps/api/app/services/simulation/controller_service.py` move from Azure OpenAI to Microsoft Foundry endpoints with managed identity. Spec 014 remains historical record. |
| 018 AIDR Guidance Integration / 019 AIDR Additional Guidances | **Referenced** — already-spec'd AIDR doctrine integration is reused as the gold-standard exemplar. Not redone. |
| 024 Simulation Control & Chat Orchestration | **Extended** — the Simulation Controller chat acquires the same corpus grounding, citation surfacing, and Foundry endpoint as the operational agents. Tenant isolation, comms-block, and approval semantics from 024 are preserved unchanged. |
| 032 Rubric Improvements | **Extended** — FR-AI01 (AIDR-only index) is widened to the whole corpus; FR-AI03a (carve-out registry) is reused as the deployment gate; FR-AI06 (private endpoints) and FR-AI09 (cosign signing) are inherited unchanged. |
| 030 LLM Evaluation Framework | **Referenced** — Foundry `eval-runner/foundry_client.py` is the reference wrapper for the new client; eval gates remain the regression detector for grounded recommendations. |
| 033 Microsoft Agent Framework Adoption | **Referenced** — MAF `chat_client` factory is the migration target for agent calls. |

---

## Clarifications

### Session 2026-05-08

- Q: Which Microsoft Foundry inference SDK and AAD token scope MUST the migrated client use? → A: **Azure AI Inference SDK** (`azure-ai-inference` Python package) with `AZURE_AI_PROJECT_ENDPOINT` (Foundry endpoint) and `AZURE_AI_PROJECT_DEPLOYMENTS` (CSV of `modelId@version=deploymentName`) — mirroring `apps/eval-runner/src/ama_eval/foundry_client.py`. AAD token scope `https://cognitiveservices.azure.com/.default` via `DefaultAzureCredential`, preserving the existing `_AOAI_TOKEN_SCOPE` constant already used by `apps/agents/maf_runtime/chat_client.py` and `apps/agents/common/llm_client.py`. *(Authority: eval-runner foundry_client.py + spec 032 FR-AI03a + Constitution §NN-2.)*
- Q: Which Foundry-hosted embedding model, vector dimension, and per-jurisdiction partitioning approach MUST the corpus index use? → A: **`text-embedding-3-large` at 3072 vector dimensions** (v1 default; higher-fidelity justified by life-safety content per Constitution §I and corpus doctrine-density). **Single** Azure AI Search index with `jurisdiction`, `topic`, and `licence_mode` filter fields — NOT per-jurisdiction index proliferation. The `jurisdiction` field is valued from `{act, nsw, nt, qld, sa, tas, vic, wa, national, aidr}`; jurisdiction-scoped queries (e.g. a NSW agent) MUST union own-jurisdiction + `national` + `aidr` to surface cross-jurisdictional doctrine deterministically. Re-evaluate sizing after first ingest with autoscale alert at 70% capacity. *(Authority: spec 032 FR-AI01 finalisation + sectors-eastern/southern-western/territories memo themes on jurisdiction disambiguation; preserves FR-AI06 single-index economics.)*
- Q: What is the binding offline-cache footprint cap for Field Coordinator-aligned devices, and which signing chain governs degraded-connectivity verification? → A: Upper bound **≤ 500 MB per device** (covers AIDR + national doctrine + each jurisdiction's most-cited handbooks with growth headroom). **Dual signature**: (1) the master `corpus_build.sha256` manifest is signed at build time using spec 032 FR-AI09 cosign keyless (Sigstore + GitHub OIDC); (2) the offline cache bundle additionally carries an **age-encrypted detached signature** using the tenant's offline public-key set so Field Coordinators can verify integrity without OIDC connectivity. Cache TTL **14 days**; an audit-logged refresh MUST occur on next online re-sync. *(Authority: spec 032 FR-AI09 cosign baseline + Constitution §IV auditability of every decision in degraded mode + Field Coordinator persona memo on degraded-connectivity autonomy.)*

### Session 2026-05-08 (Pass 2)

- Q: How MUST the OpenAI → Foundry inference-plane migration be sequenced and gated to avoid silencing agents or the simulation chat during cutover? → A: **Per-agent canary behind a spec-029 progressive-delivery feature flag**, gated per agent by the spec-033 **FR-023 equivalence test** (≥ 95% decision-equivalence on categorical output fields + 100% schema-equivalence). The spec-014 `_generate_with_fallback` template-fallback chain remains intact across the entire migration window. The legacy Azure-OpenAI client remains importable in production paths until the final agent flips; the FR-RAG-FM-04 lint becomes binding atomically in the same PR that deletes the legacy client. *(Authority: spec 033 FR-012b cutover gate + FR-023 equivalence + spec 029 progressive delivery; spec 014 fallback chain; Constitution Principle I no-silencing.)*
- Q: When the Foundry-hosted embedding deployment id changes (model upgrade or carve-out re-bind), what re-embed strategy and SLA MUST the ingest pipeline follow so retrieval is never silenced and the "no co-existence in one index" guarantee holds? → A: **Blue-green parallel index** — build `corpus-v{N+1}` against the new embedding model in a fresh AI Search index; agents query via an alias; the alias flips atomically only when ingest completes and a parity gate passes; the previous index is retained for **7 days** for rollback. **SLA**: cold rebuild ≤ 24h; alias flip < 60s. Each index hosts exactly one embedding-model id, so old and new vectors never coexist within a single index. The `(corpus_build_sha, embedding_model_id)` pair is recorded on every chunk for cross-build provenance. *(Authority: spec 032 FR-AI06 single-index economics; Constitution Principle I no-silencing; reuses `infra/modules/ai-search.bicep` per the AVM-first / module-reuse default. Resolves the internal Edge Case contradiction previously present at the "Embedding model version change" bullet.)*
- Q: How MUST the migrated Foundry client expose a test seam so contract tests can verify citation-attachment, retrieval-then-inference sequencing, hallucinated-citation suppression, and RAG-opt-out audit paths without hitting a live Foundry endpoint? → A: **Constructor injection of a `chat_complete` callable** mirroring `apps/eval-runner/src/ama_eval/foundry_client.py` (whose module docstring states: *"Designed so unit tests can substitute a fake by injecting a different `chat_complete` callable"*). `LLMClient`, the MAF `chat_client` factory, and the simulation `controller_service` MUST accept an optional injected callable returning a `FoundryResponse`-shaped payload; production wires the real Azure AI Inference SDK transport. Tests MUST NOT need to monkey-patch SDK internals. *(Authority: `apps/eval-runner/src/ama_eval/foundry_client.py` docstring + existing pytest fixture patterns under `apps/api/tests` and `apps/agents/tests`; Compliance Auditor + Principal Engineer personas.)*
- Q: Should an explicit RAG-opt-out FR be added for the Observer-Auditor non-decision (read-only / audit-replay / verification) path? → A: **Yes — add FR-RAG-NS-09 (Observer-Auditor non-decision)**. The CI-lint clause keeps its existing **FR-RAG-NS-08** ID so every `# RAG-OPTOUT [FR-RAG-NS-NN]` code comment and ADR cross-reference authored against this spec remains stable. New ADR file `docs/decisions/036-foundry-rag-grounding/09-rag-optout-observer-auditor.md` captures the rationale: read-only inspection paths do not invoke RAG because the audit log already carries the original decision-time `retrieved_chunks[]` + `corpus_build_sha` + `prompt_sha` + `model_version` (per FR-RAG-AG-02); re-grounding on a replay would inflate cost, pollute the audit chain with second-order retrievals, and introduce a hallucination surface absent from the original decision. *(Authority: `personas-input/operational.md` "Observer-Auditor non-decision" RAG-not-suitable carve-out, surfaced in the spec 036 References list line 342 but missing from the FR list — Pass 2 closes that gap.)*

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Every agent recommendation is grounded in the Australian disaster-management corpus and cites its sources (Priority: P1)

An Incident Controller, Risk Manager, or Observer-Auditor reviewing any agent recommendation must see the **exact corpus chunks** that grounded it (jurisdiction, source document, page number), and must be able to verify that the LLM did not invent doctrine not present in the corpus. The five "decision-making" agents — Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication — invoke a shared retrieval client before every prompt-bearing inference call, attach licence-mode-aware retrieved snippets to the system context, and emit citations of the form `<jurisdiction>/<topic>/handbook.md#page-N` on every recommendation card and in every audit-log entry. The Dependency Notifier — a structured-signal pipeline — explicitly opts out of RAG with code-level rationale.

**Why this priority**: Constitution **Principle I (Primacy of Life)** and **Principle IV (Transparency & Auditability)** are non-negotiable. Operational personas (Incident Commander, Risk Manager, Observer-Auditor) and sector personas (every state SES as primary flood/storm combat agency, NSW RFS vs FRNSW urban/rural disambiguation, NTES cyclone doctrine, ARC humanitarian principles) cannot trust the platform if recommendations are not traceable to authoritative source. Commonwealth personas (NEMA COMDISPLAN, AFP/ADF authority boundaries) explicitly require corpus-grounded escalation reasoning. Without grounded citations, the platform fails Australian jurisdictional readiness regardless of any other capability.

**Independent Test**: Replay a stored ScenarioRun with a representative incident (NSW bushfire crossing into VIC). Open any recommendation and verify (a) the recommendation card lists at least one citation in `<jurisdiction>/<topic>/handbook.md#page-N` form, (b) each citation resolves to an actual page in the rendered handbook, (c) the audit-log entry for the underlying LLM call records the same citations plus the corpus-build SHA active at inference time, (d) Monitoring/Risk/Evacuation/ResourceAllocation/Communication audit entries each contain a non-empty `retrieved_chunks[]` field, (e) Dependency Notifier audit entries contain a non-empty `rag_optout_reason` field instead.

**Acceptance Scenarios**:

1. **Given** an active bushfire incident with NSW and VIC impact areas, **When** the Risk Assessment agent issues a hazard prediction, **Then** the recommendation card cites at least one NSW RFS doctrine page **and** at least one CFA-VIC doctrine page (or a CFA-FRV boundary page), and the audit record contains the retrieved chunk IDs, the corpus-build SHA, and the prompt SHA.
2. **Given** a tropical cyclone affecting the NT and northern QLD, **When** the Evacuation agent recommends shelter and route options, **Then** the citations include NTES cyclone doctrine **and** SES-QLD storm-surge doctrine, and any vulnerable-population reference cites Constitution VI-C and the relevant ATSI / CALD corpus entry.
3. **Given** the Communication agent drafts a multilingual public-information piece, **When** the draft is finalised, **Then** the cited corpus entries include AIDR Public Information & Warnings doctrine, ARC multilingual / Auslan / Easy-Read protocols, and (where the impact area overlaps Indigenous communities) the corresponding NT / WA / SA Indigenous-liaison entry; **and** the draft is watermarked `DRAFT — REQUIRES IC APPROVAL`.
4. **Given** the Dependency Notifier emits a structured downstream signal, **When** the audit record is written, **Then** it carries `rag_used=false` and `rag_optout_reason="structured-signal-pipeline; deterministic provisioning per FR-RAG-NS-01"`, and no LLM call is made.
5. **Given** a tampered audit entry where the `retrieved_chunks[]` field has been altered post-write, **When** the integrity check runs, **Then** the system flags the break, refuses to publish further recommendations from the affected window, and pages the Observer-Auditor.

---

### User Story 2 — Production agent and simulation traffic runs on Microsoft Foundry endpoints with no Azure OpenAI dependency in code (Priority: P1)

A Security Engineer, Principal Engineer, or Platform Operator must be able to deploy the platform end-to-end with **zero** Azure-OpenAI client paths in production code and **zero** API-key authentication. The three call sites — `apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py`, and `apps/api/app/services/simulation/controller_service.py` — invoke Microsoft Foundry inference endpoints via managed identity (Entra ID). Every Foundry deployment is recorded in the `infra/parameters/foundry-carveout.yaml` registry (per spec 032 FR-AI03a) with model name, region, business justification, approver identities, and review date; CD refuses to deploy any deployment not in the registry. Data persistence remains 100% in Australia East / Australia Southeast as required by Constitution Non-Negotiable #2 (Data Sovereignty + Microsoft Foundry carve-out, Amendment 1.2.0).

**Why this priority**: Constitution Non-Negotiable #2 is binding, and the carve-out for Foundry model-hosting endpoints is bounded to the inference resource only. Without a coherent migration, the simulation controller (which still imports `from openai import AsyncAzureOpenAI`) leaves the platform with two model planes, two failure modes, and two security postures. The Executive Leader, Compliance Auditor, and Security Engineer personas all require a single, attestable Foundry plane before production go-live.

**Independent Test**: From a fresh clone, `grep -r "from openai" apps/` and `grep -r "AzureOpenAI" apps/` return zero matches in production paths (test fixtures and migration ADR are exempt); CI fails any PR that re-introduces them. Run `azd up` and verify (a) every Foundry deployment in the resulting deployment manifest is present in `infra/parameters/foundry-carveout.yaml` with non-placeholder approver identities; (b) every agent and the simulation controller authenticate using `DefaultAzureCredential` against `https://cognitiveservices.azure.com/.default` (or the Foundry-equivalent scope) — no `api_key` parameter set; (c) data-plane resources (Cosmos, Storage, Service Bus, Event Grid, App Insights, Log Analytics, Key Vault, ACR, audit/evidence stores) all resolve to Australia East or Australia Southeast.

**Acceptance Scenarios**:

1. **Given** the production deployment, **When** any agent calls its LLM client, **Then** the call traverses a Foundry endpoint authenticated via managed identity; no `AZURE_OPENAI_API_KEY` is read at runtime.
2. **Given** a CD pipeline run, **When** the deploy step starts, **Then** the carve-out check reads `infra/parameters/foundry-carveout.yaml`, validates every Foundry deployment in the Bicep/azd plan against it, and **fails the deploy** if any deployment is missing or has an expired `review_date`.
3. **Given** the simulation chat, **When** a Coordinator sends a message, **Then** the SSE stream is produced by a Foundry-backed chat client (not `AsyncAzureOpenAI`), carries a `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, and (per Story 3) `citations[]`.
4. **Given** any production data-plane resource in the deployment plan, **When** the region is anything other than `australiaeast` or `australiasoutheast`, **Then** the deploy fails before resource creation.
5. **Given** a model-gateway request, **When** the prompt or response payload contains PII or PSPF-marked content destined for a non-AU Foundry endpoint, **Then** the gateway either redacts/masks per the data-minimisation policy or denies transit and emits an auditable `gateway.deny` event (per Constitution NN-2 Amendment 1.2.0).

---

### User Story 3 — Simulation chat is grounded in the same corpus and surfaces citations through the SSE stream (Priority: P1)

An Exercise Coordinator using the Simulations page (spec 024) chats with the Simulation Controller in natural language. The Controller, hardened by its existing system prompt + tool manifest, now also retrieves from the corpus before each inference, attaches retrieved snippets to its context, and emits a `citation` SSE event for each grounded claim it makes. When the Coordinator asks "what AIIMS span-of-control applies to a Level 2 incident with 9 functional leads?", the Controller cites the AIDR Incident Management Handbook page; when asked "what cyclone category triggers NTES Furious-50 alerts?", it cites NTES doctrine. The Controller refuses to invent corpus references — if no relevant passage exists, it says so explicitly and recommends an authoritative external lookup. Existing tenant-isolation and synthetic-comms-block guarantees from spec 024 remain unchanged.

**Why this priority**: The Resilience Planner persona requires grounded scenario authoring; the Public Information Officer requires watermarked, citation-bearing draft warnings inside simulations; Observer-Auditor requires the same provenance bar in simulation as in live operations. Without grounding, simulation rehearsals can drift from authoritative doctrine and produce false confidence in operator readiness. **Note** the Resilience Planner memo's guard: RAG must support **preparedness analysis**, not **scenario execution scripts** — predetermined scenario timelines remain deterministic.

**Independent Test**: Open a simulation. Send a doctrine-style prompt ("what flood-warning escalation thresholds does SES-NSW use?"). Verify (a) at least one `citation` SSE event arrives with a corpus reference, (b) the cited page resolves and the substance of the response matches it, (c) the audit-log entry for the simulation chat turn contains the same citations plus `prompt_sha`, `model_id`, `model_version`, `deployment_alias`. Send an out-of-corpus prompt ("what does ABC's policy say about X?"). Verify the Controller declines to fabricate a citation and the SSE stream surfaces `citations: []` with an explanatory note.

**Acceptance Scenarios**:

1. **Given** an active simulation, **When** the Coordinator sends a doctrine question, **Then** the SSE stream includes both the natural-language reply and one or more `citation` events, each carrying `{jurisdiction, topic, page, source_url, sha256_of_chunk}`.
2. **Given** the Coordinator drafts a public warning inside a simulation, **When** the Controller produces the draft, **Then** the draft is watermarked `SIMULATION — DO NOT DISTRIBUTE`, cites AIDR Public Information & Warnings doctrine, and is hard-blocked from external dissemination by the existing PublicationService.
3. **Given** a question for which the corpus has no relevant passage, **When** the Controller responds, **Then** it does **not** invent a citation, emits `citations: []`, and includes an explicit "no corpus match — recommend operator verification" note.
4. **Given** a Resilience Planner running a scripted scenario timeline, **When** scripted events fire, **Then** the script executes deterministically (no RAG round-trip), but the surrounding chat-mode answers remain RAG-grounded.

---

### User Story 4 — Corpus is indexed in Azure with licence-mode-aware behaviour (Priority: P1)

A Solution Architect, Compliance Auditor, or AI/ML Engineer must be able to deploy the corpus index via `azd up` and CD with **no manual steps**. The pipeline reads `docs/corpus/` (which exposes `source.json` provenance + `handbook.md` page-aligned Markdown for every entry — see `docs/corpus/README.md`) and:

- For entries with `mode: full-text` (e.g. CC-BY-4.0 Australian Government publications): chunk the page-aligned Markdown, embed via the Foundry-hosted embedding model, and index into Azure AI Search **with full body searchable**.
- For entries with `mode: metadata-only`: index title, URL, summary, jurisdiction, topic — **no body, no embeddings of body**.
- For entries with `mode: excluded`: do not index at all; refuse retrieval; emit a deploy-time warning if such an entry is referenced from any agent prompt template.

Re-running ingest is idempotent: unchanged corpus entries (matched by `sha256`) are not re-embedded, are not re-indexed, and contribute zero index churn. The corpus-build SHA at ingest time is recorded so audit logs can prove which corpus version grounded each historical recommendation.

**Why this priority**: Constitution Principle IV (Auditability) and Non-Negotiable #2 (Data Sovereignty) demand provable provenance and AU residency. The corpus README's licence model is the contract: violating it (e.g. embedding `metadata-only` body content) is a redistribution-rights breach. Without idempotent ingest, every CD run wastes embedding spend and inflates index churn. Without per-entry licence enforcement, the platform cannot be deployed into agencies that demand publisher-rights traceability (NEMA, all SES agencies, RFDS).

**Independent Test**: Run ingest twice in succession against an unchanged `docs/corpus/`. Verify the second run reports zero new chunks, zero new embeddings, zero index updates — and total runtime ≤ 10% of the first run. Mutate a single page in one `mode: full-text` entry, re-run; verify only that entry's chunks are re-indexed. Add a new `mode: metadata-only` entry; verify the title/URL appear in the index but no body chunks. Add a `mode: excluded` entry; verify it does not appear in the index and that any retrieval query that would match it returns nothing.

**Acceptance Scenarios**:

1. **Given** the corpus contains entries in all three licence modes, **When** ingest completes, **Then** Azure AI Search contains body chunks for `full-text` entries only, metadata documents for `full-text` and `metadata-only` entries, and zero documents for `excluded` entries.
2. **Given** an unchanged corpus, **When** `azd up` re-runs the postprovision step, **Then** the ingest job logs `unchanged_entries=N skipped=N reindexed=0` and exits successfully.
3. **Given** a corpus entry whose `source.json.sha256` differs from the indexed copy, **When** ingest runs, **Then** that entry alone is re-chunked, re-embedded, re-indexed; other entries are skipped.
4. **Given** the deployed index, **When** a retrieval query runs from the agents, **Then** every returned chunk carries `{jurisdiction, topic, page, sha256_of_chunk, corpus_build_sha}` so the citation can be reconstructed deterministically.
5. **Given** a `mode: excluded` source listed in any agent prompt template, **When** CI lints the prompt-template repo, **Then** CI fails with a clear "excluded source referenced" error.

---

### User Story 5 — Pipeline-only agents that should not invoke RAG are explicitly carved out and documented (Priority: P2)

A Principal Engineer or Compliance Auditor reviewing the agent fleet must see, in code and in the design-decision record, **which** agents (or which paths inside an agent) deliberately do **not** use RAG and **why**. The Dependency Notifier — a structured-signal pipeline — opts out entirely; pure-collection paths inside the Planning Officer-aligned agent opt out; live-data paths into BoM and GA opt out; ADF DACC paths above OFFICIAL classification opt out (per Constitution NN-2 + Commonwealth persona memo). Each opt-out is reflected by (a) a code comment at the call-site naming the FR ID and rationale, (b) an entry in an architecture decision record (ADR), and (c) the agent's audit log emitting `rag_used=false` with the `rag_optout_reason` populated.

**Why this priority**: The Dependency Notifier persona-aligned guidance is explicit: introducing RAG into a deterministic structured-signal pipeline adds non-determinism, latency, and a hallucination surface for what is essentially a fan-out signal. Likewise, BoM / GA live data paths and Planning Officer pure-collection paths should remain deterministic per their persona memos, and **Observer-Auditor read-only / audit-replay paths must not re-ground** (the original decision-time provenance already lives in the audit log per FR-RAG-AG-02 — re-grounding would pollute the chain and add a hallucination surface absent from the original decision; see FR-RAG-NS-09). Documenting this is itself a Constitution Principle IV obligation (Transparency).

**Independent Test**: Inspect every agent module and confirm that any call site that intentionally bypasses RAG has a comment in the form `# RAG-OPTOUT [FR-RAG-NS-NN]: <reason>` and that the corresponding ADR (`docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-<agent>.md`) exists with the rationale, the persona memo citation, and the named approver. Confirm the agent's audit log entries on those paths populate `rag_used=false` and `rag_optout_reason`.

**Acceptance Scenarios**:

1. **Given** the Dependency Notifier emits a downstream signal, **When** the audit record is written, **Then** `rag_used=false` and `rag_optout_reason="structured-signal-pipeline (FR-RAG-NS-01)"`.
2. **Given** the Monitoring agent's BoM live-feed path, **When** a forecast tile is updated, **Then** the path bypasses RAG and the audit entry references `FR-RAG-NS-02` (BoM live API authority).
3. **Given** the Risk Assessment agent's GA seismic-feed path, **When** a magnitude-update arrives, **Then** the path bypasses RAG and the audit entry references `FR-RAG-NS-03` (GA live seismic authority).
4. **Given** a Planning Officer-aligned data-collection-only path, **When** raw signals are accumulated, **Then** RAG is not invoked and the audit entry references `FR-RAG-NS-04`.
5. **Given** a future contributor introduces a new agent, **When** they omit the RAG-OPTOUT comment + ADR for any non-grounded path, **Then** code review and CI lint fail.

---

### User Story 6 — Degraded-connectivity offline cache for Field Coordinator-aligned grounding (Priority: P2)

A Field Coordinator-aligned agent operating in a degraded-connectivity zone (Kimberley, Pilbara, Far North NT, remote SA, King/Flinders Islands, etc.) retains a small, signed, locally-cached subset of the corpus — hazard thresholds, safety escalation criteria, sector boundaries, AIIMS span-of-control, evacuation centre setup checklists. Decisions made offline are logged with corpus references and, on reconnection, are reconciled with the live audit store with the timestamp preserved. The cache is never silently extended; its content is governed by a versioned manifest.

**Why this priority**: Field Coordinator (operational), DFES-WA, NTES, NTPF, Bushfires NT, SES-TAS (Furneaux/King Islands), and SAPOL Far North personas all flag degraded connectivity as a first-class requirement. Without offline grounding, life-safety decisions in remote zones must rely on un-grounded local heuristics — a Constitution Principle I + IV failure.

**Independent Test**: Disable network egress from a Field Coordinator-aligned process. Send it a hazard-threshold or evacuation-centre-setup query. Verify (a) it answers with a corpus citation drawn from the local cache, (b) the answer is bounded to the cached topics and refuses to speculate beyond them, (c) decisions made while offline are queued; (d) on reconnect, the queued audit entries appear in the central store with their original timestamps and corpus citations preserved.

**Acceptance Scenarios**:

1. **Given** a network outage, **When** a Field Coordinator-aligned query about evacuation-centre setup arrives, **Then** the agent answers from the offline cache with citations to AIDR Evacuation Planning Handbook pages and refuses to extend beyond cached topics.
2. **Given** an offline-decision audit entry, **When** connectivity is restored, **Then** the entry appears in the central audit store with original timestamp, citations, and a `sync_lag_seconds` value.

---

### User Story 7 — Multi-agency, jurisdiction-disambiguated retrieval (Priority: P2)

When a query touches more than one jurisdiction (NSW–VIC border bushfire, NT–QLD cyclone crossing, ACT–NSW handoff), the retrieval layer returns chunks **labelled** by jurisdiction so an agent never silently conflates urban-fire authority (FRNSW) with rural-fire authority (NSW RFS), or NSW SES with NTES, or AFP-ACT-policing with state police. Citation rendering preserves the agency owner ("Fire and Rescue NSW primary source" vs "RFS primary source", "NTES — primary combat for tropical cyclones", "DFES-WA — single combined agency"). For sector-bordering combat-agency designations (every state SES being primary for flood/storm; CFA-VIC vs FRV; QFD with QPS for evacuation enforcement), retrieval must surface both the primary source and the handoff partner per the corpus.

**Why this priority**: Eastern, southern/western, and territory persona memos converge on the same risk: "do not let RAG conflate FRNSW with RFS, do not let SES become a generic acronym, do not let DFES-WA be split into NSW-style sub-agencies." A multi-jurisdiction incident with even one mis-attributed citation produces a Constitution Principle IV breach and an inter-agency trust failure.

**Independent Test**: Issue a query for "rural fire suppression, NSW + ACT border". Verify the returned chunks list NSW RFS as primary source and ACT RFS as the cross-jurisdictional partner; verify FRNSW-urban chunks are not returned. Issue a query "tropical cyclone, NT + QLD". Verify NTES + SES-QLD appear as primary combat agencies, with BoM cyclone-category doctrine as supporting reference; verify ABF / ASA / ADF entries appear only as escalation references, not primary.

**Acceptance Scenarios**:

1. **Given** a NSW–VIC border bushfire query, **When** retrieval runs, **Then** chunks include both NSW RFS and CFA-VIC primary sources, FRNSW urban chunks are not returned for rural queries, and the cited handoff doctrine names IC unification thresholds.
2. **Given** a query about "evacuation enforcement authority", **When** retrieval runs, **Then** results respect AFP-vs-ACT-Policing concurrent jurisdiction in the ACT and state-police authority elsewhere, and the citations name the legislative source.
3. **Given** a cross-sector query touching transport closures + utility de-energisation, **When** retrieval runs, **Then** results include the jurisdiction-specific transport authority (TfNSW / DoT VIC / DTMR / Main Roads WA / etc.) **and** the corresponding utility (Ausgrid, AusNet, Energex, Western Power) per the corpus.

---

### User Story 8 — ATSI / CALD / accessibility-aware retrieval for warning composition (Priority: P3)

When the Communication agent composes a public warning that touches an Aboriginal/Torres Strait Islander community, a CALD-dense area, or a vulnerable cohort (people with disability, older persons, tourists, people in institutional care — Constitution VI-C), retrieval surfaces the relevant ATSI-language guidance, ARC multilingual / Easy-Read / Auslan protocols, TIS-National coordination procedures, and culturally-safe-messaging doctrine from the corpus. The PIO persona's request is non-negotiable: "alert *content* may be RAG-drafted with corpus backing; *approval* remains with IC."

**Why this priority**: Constitution Principle V (Warning and Public Information) and VI-C (Vulnerable Populations); operational PIO + cross-sector Community NGOs / Health / Local Government persona memos. Without this, multilingual / accessible warnings risk being un-grounded and inconsistent across jurisdictions.

**Acceptance Scenarios**:

1. **Given** an impact area overlapping a known Aboriginal community in NT or WA, **When** the Communication agent drafts a warning, **Then** retrieval surfaces the relevant Indigenous-liaison / language-considerations corpus entry and the draft is gated for human approval before any language-specific transformation.
2. **Given** a draft warning, **When** Auslan / Easy-Read / TIS-National protocols are required, **Then** the corresponding ARC corpus entries are cited and the draft includes the accessibility annotation.

---

### Edge Cases

- **Corpus mid-update during ingest**: a CI run starts re-rendering a handbook (`pdf_to_md.py`) while ingest is streaming. The ingest tool must read from a frozen `corpus_build_sha` snapshot, never from a half-written `handbook.md`.
- **Foundry quota exhaustion in Australia East**: the carve-out registry permits a non-AU model deployment for inference only; agents and the simulation controller must transparently route to it via the model gateway, **only** if (a) the carve-out entry is current, (b) data-minimisation strips PII / PSPF before egress, and (c) the audit entry records `region`, `carveout_entry_id`, `policy_decision`. Storage / Cosmos / Service Bus / Event Grid / Application Insights / Log Analytics / Key Vault / ACR / audit / evidence remain in Australia East/Southeast.
- **Embedding model version change**: a future change to the embedding-model deployment id MUST trigger a **blue-green rebuild** per FR-RAG-IDX-04 — a fresh AI Search index `corpus-v{N+1}` is built against the new embedding model, agents query via an alias, the alias flips atomically only after ingest completes and a parity gate passes, and the previous index is retained for 7 days for rollback. Each AI Search index hosts exactly one embedding-model id, so old and new vectors never coexist within a single index. The `(corpus_build_sha, embedding_model_id)` pair is recorded on every chunk for cross-build provenance; the alias is the single source of truth for which index agents query at any moment.
- **Citation mismatch**: an LLM returns text with a citation that does not appear in the retrieved chunk set. The platform must flag this, not display the citation, and emit a `hallucinated_citation` audit event.
- **Excluded source crept into a prompt template**: CI lint must catch this before merge; runtime must defensively refuse the prompt with a clear error if the lint is bypassed.
- **Simulation chat asks about a `mode: excluded` source**: the Controller must reply that the source is not indexed and may not be cited.
- **Agent runs without an LLM endpoint configured**: agents fail closed (per spec 014 / 033 pattern) with a clear error; they MUST NOT silently degrade to ungrounded heuristics.
- **Offline cache stale**: if the cached corpus-build SHA is older than the manifest's stale threshold, the agent MUST surface a "cache stale" badge alongside any answer drawn from it; the audit entry records the cache age.
- **Operator asks "why did the agent recommend X?"** — auditor opens the audit entry and sees `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `corpus_build_sha`, `retrieved_chunks[]` (with `chunk_id`, `sha256`, `jurisdiction`, `topic`, `page`), and the model output. Reproduction is deterministic given the same inputs and same SHAs.
- **Classification boundary**: any agent path that could carry SECRET / OFFICIAL:Sensitive / PSPF-marked content (ADF DACC above OFFICIAL, AFP classified annexes per Commonwealth persona memo) MUST refuse RAG and route to the offline DACC operations centre — enforced by the model gateway's classification filter.

---

## Requirements *(mandatory)*

### Functional Requirements — Foundry migration

- **FR-RAG-FM-01**: System MUST migrate `apps/agents/common/llm_client.py` from `openai.AzureOpenAI` to a Microsoft Foundry inference client built on the **Azure AI Inference SDK** (`azure-ai-inference` Python package) using managed identity (Entra ID). The client MUST read `AZURE_AI_PROJECT_ENDPOINT` for the Foundry endpoint and `AZURE_AI_PROJECT_DEPLOYMENTS` (CSV of `modelId@version=deploymentName`) for the deployment map, mirroring `apps/eval-runner/src/ama_eval/foundry_client.py`. API-key authentication MUST be removed. *(Driven by all operational personas requiring grounded, auditable LLM access; supersedes spec 014. Resolved in Clarifications 2026-05-08.)*
- **FR-RAG-FM-02**: System MUST migrate `apps/agents/maf_runtime/chat_client.py` from `agent_framework_openai.OpenAIChatClient` (Azure OpenAI mode) to the Foundry-equivalent chat client behind the same factory function signature, so MAF Agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) keep their constructor contract. *(Driven by spec 033 MAF Adoption.)*
- **FR-RAG-FM-03**: System MUST migrate `apps/api/app/services/simulation/controller_service.py` from `from openai import AsyncAzureOpenAI` to a Foundry-compatible async client. The simulation Controller's existing system prompt + tool manifest at `apps/api/app/services/simulation/controller_prompt.md` (per spec 024) is preserved. *(Driven by Resilience Planner + PIO + Exercise Coordinator personas.)*
- **FR-RAG-FM-04**: System MUST forbid Azure-OpenAI imports in production paths. CI MUST fail any PR that re-introduces `from openai import AzureOpenAI`, `AsyncAzureOpenAI`, or `agent_framework_openai.OpenAIChatClient(... mode="azure_openai" ...)` outside of (a) historical specs, (b) the migration ADR, (c) explicitly-marked test fixtures. *(Driven by Security Engineer + Principal Engineer personas.)*
- **FR-RAG-FM-05**: System MUST authenticate every Foundry call via `DefaultAzureCredential` against the AAD token scope **`https://cognitiveservices.azure.com/.default`** (the existing scope already used by `apps/agents/common/llm_client.py` and `apps/agents/maf_runtime/chat_client.py` — preserved across the migration under Constitution §NN-2). No `api_key=` kwarg may be passed in any production path. *(Constitution Principle IV; Constitution NN-2. Resolved in Clarifications 2026-05-08.)*
- **FR-RAG-FM-06**: The OpenAI → Foundry inference-plane migration MUST follow a **per-agent canary behind a spec-029 progressive-delivery feature flag**, gated per agent by the spec-033 **FR-023 equivalence test** (≥ 95% decision-equivalence on categorical output fields + 100% schema-equivalence). The spec-014 `_generate_with_fallback` template-fallback chain MUST remain intact across the entire migration window so any Foundry-side regression downgrades to template fallback rather than silencing the agent. The legacy Azure-OpenAI client MUST remain importable in production code paths until the final agent flips; the FR-RAG-FM-04 lint becomes binding atomically in the same PR that deletes the legacy client (so the lint never blocks an in-flight per-agent canary). *(Driven by Constitution Principle I no-silencing; spec 033 FR-012b cutover gate + FR-023 equivalence; spec 029 feature-flag mechanism; spec 014 fallback chain. Resolved in Clarifications 2026-05-08 Pass 2.)*
- **FR-RAG-FM-07**: The migrated Foundry client (`apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py` factory, and `apps/api/app/services/simulation/controller_service.py`) MUST expose a **constructor-injectable `chat_complete` callable seam** mirroring `apps/eval-runner/src/ama_eval/foundry_client.py` (whose module docstring states: *"Designed so unit tests can substitute a fake by injecting a different `chat_complete` callable"*). Contract tests for citation attachment (FR-RAG-AG-03), retrieval-then-inference sequencing (FR-RAG-AG-01 → AG-02), hallucinated-citation suppression (FR-RAG-AG-05), simulation `citation` SSE emission (FR-RAG-SIM-02), and RAG-opt-out audit paths (FR-RAG-NS-01..09) MUST be runnable hermetically by passing a `FakeFoundryClient` (or a callable returning a `FoundryResponse`-shaped payload) into the production class — without monkey-patching the Azure AI Inference SDK transport and without a live Foundry endpoint. *(Driven by Principal Engineer + Compliance Auditor personas; mirrors the eval-runner reference pattern. Resolved in Clarifications 2026-05-08 Pass 2.)*

### Functional Requirements — Foundry carve-out enforcement (reuse spec 032)

- **FR-RAG-CV-01**: System MUST reuse the spec-032 FR-AI03a carve-out registry at `infra/parameters/foundry-carveout.yaml`. Every Foundry deployment landed by this feature MUST appear in the registry with `model_name`, `region`, `business_justification`, `approver_identities[]` (non-placeholder Entra IDs), and `review_date` (≤ 12 months out). *(Constitution NN-2 Amendment 1.2.0.)*
- **FR-RAG-CV-02**: CD MUST refuse to deploy any Foundry deployment whose `(model_name, region)` is not present in the registry, or whose `review_date` has passed. The check MUST run before the Bicep / azd plan is applied; failure messages MUST name the offending deployment. *(Constitution NN-2.)*
- **FR-RAG-CV-03**: The model gateway MUST enforce data-minimisation on prompts and responses traversing any non-AU Foundry deployment: PII redaction, PSPF-marking detection, and a sensitive-operational-content filter. Payloads failing the filter MUST be denied transit; the deny event is audited with `gateway.deny.reason`. *(Constitution NN-2 Amendment 1.2.0.)*
- **FR-RAG-CV-04**: System MUST NOT persist regulated platform data outside Australia. All data-plane resources (Cosmos, Storage, Service Bus, Event Grid, Application Insights, Log Analytics, Key Vault, ACR, audit / evidence stores) MUST be in Australia East or Australia Southeast. CD MUST fail if any data-plane resource resolves to a non-AU region. *(Constitution NN-2.)*

### Functional Requirements — Corpus indexing (whole `docs/corpus/` tree)

- **FR-RAG-IDX-01**: System MUST ingest the **whole** `docs/corpus/` tree (national + every state/territory + Commonwealth + agency operational doctrine + hazard-specialty material), reusing the existing `infra/modules/ai-search.bicep` AI Search module. *(Driven by every sector persona memo's "Index … from `docs/corpus/<jurisdiction>/`" ask.)*
- **FR-RAG-IDX-02**: System MUST honour per-source licence modes from `source.json`:
  - `mode: full-text` → chunk page-aligned `handbook.md`, embed via the Foundry-hosted embedding model **`text-embedding-3-large` at 3072 vector dimensions** (v1 default — higher-fidelity choice justified by life-safety content per Constitution Principle I and the doctrine-density of the corpus), index body + metadata.
  - `mode: metadata-only` → index title, URL, summary, jurisdiction, topic; do NOT embed or store body content.
  - `mode: excluded` → do not index at all; refuse to ground on it.
  *(`docs/corpus/README.md` "Licence and indexing model". Resolved in Clarifications 2026-05-08.)*
- **FR-RAG-IDX-03**: Each indexed document MUST carry `{jurisdiction, topic, page, sha256_of_chunk, source_url, retrieved_at, licence_mode, corpus_build_sha, embedding_model_id}`. *(Provenance per Constitution IV; cited by Observer-Auditor + Compliance Auditor + Risk Manager personas.)*
- **FR-RAG-IDX-04**: Ingest MUST be idempotent: an entry whose `source.json.sha256` matches the indexed copy MUST be skipped (no re-chunk, no re-embed, no re-index). A change to the embedding-model deployment id MUST trigger a **blue-green rebuild**: a new AI Search index `corpus-v{N+1}` (provisioned via the existing `infra/modules/ai-search.bicep`) is built against the new embedding model; agents query via an alias; the alias flips atomically only when ingest completes and a parity gate passes; the previous index is retained for **7 days** for rollback. **SLA**: cold rebuild ≤ 24h; alias flip < 60s. Each index MUST host exactly one embedding-model id, preserving the no-coexistence guarantee from the corresponding Edge Case bullet. *(Driven by cost-control + Solution Architect persona; Constitution Principle I no-silencing. Re-embed strategy resolved in Clarifications 2026-05-08 Pass 2.)*
- **FR-RAG-IDX-05**: Ingest MUST run automatically in `azd postprovision` and in CD after infrastructure deploy. Manual invocation must remain possible for backfills. *(Driven by Principal Engineer + Solution Architect personas; satisfies the user input's "deployment (azd, CI/CD) must take this corpus data and store it".)*
- **FR-RAG-IDX-06**: Azure AI Search service hosting the index MUST be Private-Endpoint-only with no public network access, in Australia East, with no cross-region replication. SKU sizing inherits spec 032 (Standard S1 prod, Basic dev/staging) unless adjusted in planning. *(Constitution NN-2 + spec 032 FR-AI06.)*
- **FR-RAG-IDX-07**: A reference / inventory file `docs/corpus/INDEXING-LICENCE-INVENTORY.md` MUST list every indexed source with publisher, edition, citation URL, redistribution rights, and `mode`; it MUST be machine-checked against `source.json` files in CI. *(Driven by Compliance Auditor persona; mirrors spec 032's `LICENCE-INVENTORY.md` for AIDR.)*
- **FR-RAG-IDX-08**: The corpus MUST be indexed into a **single** Azure AI Search index with `jurisdiction`, `topic`, and `licence_mode` filter fields — NOT per-jurisdiction index proliferation. The `jurisdiction` field is valued from `{act, nsw, nt, qld, sa, tas, vic, wa, national, aidr}`. Jurisdiction-scoped retrieval (e.g. a NSW agent) MUST union own-jurisdiction + `national` + `aidr` results so cross-jurisdictional doctrine surfaces deterministically (per User Story 7 disambiguation). Index sizing MUST be re-evaluated after first ingest; an autoscale alert MUST fire at 70% capacity. *(Driven by sectors-eastern + sectors-southern-western + sectors-territories memo themes on jurisdiction disambiguation; preserves FR-AI06 single-index economics. Resolved in Clarifications 2026-05-08.)*

### Functional Requirements — Shared retrieval client + per-agent grounding

- **FR-RAG-AG-01**: System MUST provide a shared retrieval client invoked by all five decision-making agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) before each prompt-bearing inference call. Retrieval inputs include the agent name, current incident jurisdiction(s), hazard type, and free-text question; outputs include up to N chunks with full provenance metadata. *(Driven by IC + Operations + Risk Manager + PIO personas; "every agent must be grounded".)*
- **FR-RAG-AG-02**: Each grounded agent's audit-log entry MUST record the `retrieved_chunks[]` (with `chunk_id`, `sha256`, `jurisdiction`, `topic`, `page`), `corpus_build_sha`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `embedding_model_id`. *(Driven by Observer-Auditor; Constitution Principle IV.)*
- **FR-RAG-AG-03**: Recommendations surfaced to operators MUST cite at least one corpus reference of the form `<jurisdiction>/<topic>/handbook.md#page-N` when grounded. The recommendation card MUST link to the rendered Markdown page and the original PDF URL. *(Driven by every operational + sector persona memo; mirrors spec 032 FR-AI01 widening.)*
- **FR-RAG-AG-04**: The retrieval layer MUST disambiguate jurisdiction in returned chunks (per User Story 7) so urban-fire (e.g. FRNSW, FRV, SAMFS) and rural-fire (e.g. NSW RFS, CFA-VIC, SACFS, Bushfires NT) are not conflated; SES jurisdiction is preserved (NSW SES vs SES VIC vs SES QLD vs SES-SA vs SES-TAS vs NTES vs ACT SES); and DFES-WA is treated as a single combined agency, not split. *(Driven by sectors-eastern + sectors-southern-western + sectors-territories memos.)*
- **FR-RAG-AG-05**: Grounded agents MUST NOT fabricate citations. If a citation appears in LLM output but does not match any retrieved chunk in that call, the platform MUST suppress the citation in the rendered card, log a `hallucinated_citation` event, and (above a configurable threshold) downgrade confidence. *(Driven by Risk Manager + Observer-Auditor + PIO personas.)*
- **FR-RAG-AG-06**: Where a corpus entry exists for ATSI / CALD / Auslan / Easy-Read / TIS-National guidance and the impact area triggers it (per User Story 8), retrieval MUST surface that entry to the Communication agent before the warning is composed. *(Driven by PIO + ARC + Community NGOs + Health + Local Government personas; Constitution V + VI-C.)*

### Functional Requirements — Pipeline / live-feed / classified RAG-opt-outs (NOT-suitable carve-outs)

- **FR-RAG-NS-01**: Dependency Notifier is a structured-signal pipeline; it MUST NOT invoke RAG. The call site MUST carry the comment `# RAG-OPTOUT [FR-RAG-NS-01]: structured-signal pipeline; deterministic provisioning per persona memo`. The audit log MUST record `rag_used=false`, `rag_optout_reason="structured-signal-pipeline"`. ADR `docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md` MUST exist. *(Driven by user-input "Dependency Notifier" pipeline note + Logistics + Planning personas' "NOT suitable" guidance.)*
- **FR-RAG-NS-02**: Monitoring agent's BoM live-feed path MUST NOT invoke RAG; live forecasts come from BoM operational APIs at runtime. The corpus is used only for *historical* event playback and *doctrinal* reasoning, not live forecast issuance. ADR `02-rag-optout-bom-live.md` MUST exist. *(Driven by sectors-commonwealth memo: "BoM agent primarily executes current forecasts … RAG grounding inadequate for real-time forecasting".)*
- **FR-RAG-NS-03**: Risk Assessment agent's GA seismic-feed path MUST NOT invoke RAG; live seismic data comes from GA APIs at runtime. ADR `03-rag-optout-ga-live.md` MUST exist. *(Driven by sectors-commonwealth memo: "GA's core function is continuous seismic monitoring … Live seismic data unsuitable for Foundry RAG".)*
- **FR-RAG-NS-04**: Planning Officer-aligned agents' pure-data-collection paths MUST NOT invoke RAG; collection remains deterministic and auditable. RAG is reserved for *analysis* paths within the same agent. ADR `04-rag-optout-planning-collection.md` MUST exist. *(Driven by operational Planning Officer memo: "If Planning Officer is performing pure data collection (no analysis), RAG may be redundant".)*
- **FR-RAG-NS-05**: Logistics-aligned transactional resource-movement paths MUST NOT invoke RAG; deterministic provisioning rules apply. ADR `05-rag-optout-logistics-transactional.md` MUST exist. *(Driven by operational Logistics Officer memo: "If Logistics Officer is executing transactional resource movements (no decision inference), use deterministic provisioning rules instead of RAG".)*
- **FR-RAG-NS-06**: Resilience Planner scenario-execution paths MUST run from predetermined scripts without RAG round-trips during the scenario. RAG remains available for preparedness *analysis* and post-scenario AAR generation. ADR `06-rag-optout-scenario-execution.md` MUST exist. *(Driven by operational Resilience Planner memo: "NOT grounded by RAG during scenario execution".)*
- **FR-RAG-NS-07**: Any agent path that may carry classified content (ADF DACC > OFFICIAL, AFP classified annex) MUST refuse RAG and route to the offline DACC operations centre per Constitution NN-2 carve-out language. The model gateway's classification filter enforces this. ADR `07-rag-optout-classified.md` MUST exist. *(Driven by sectors-commonwealth memo for ADF + AFP.)*
- **FR-RAG-NS-08**: CI MUST lint that every non-grounded path in production agent code carries a `# RAG-OPTOUT [FR-RAG-NS-NN]` comment and a corresponding ADR file. CI fails any PR that introduces a non-grounded path without both. *(Driven by Compliance Auditor persona.)*
- **FR-RAG-NS-09**: Observer-Auditor non-decision paths (read-only inspection, audit replay, integrity verification, dashboard recomputation against historical decisions) MUST NOT invoke RAG. The existing audit log already carries the original decision-time `retrieved_chunks[]`, `corpus_build_sha`, `prompt_sha`, `model_id`, `model_version`, and `deployment_alias` (per FR-RAG-AG-02), so re-grounding on replay would (a) inflate embedding + retrieval cost, (b) pollute the audit chain with second-order retrievals, and (c) introduce a hallucination surface absent from the original decision. The call site MUST carry the comment `# RAG-OPTOUT [FR-RAG-NS-09]: read-only audit/inspection path; original decision provenance suffices`. The audit log MUST record `rag_used=false`, `rag_optout_reason="observer-auditor-replay"`. ADR `docs/decisions/036-foundry-rag-grounding/09-rag-optout-observer-auditor.md` MUST exist. The CI lint at FR-RAG-NS-08 covers this clause unchanged (its `[FR-RAG-NS-NN]` matcher is pattern-based). *(Driven by `personas-input/operational.md` Observer-Auditor "non-decision" RAG-not-suitable carve-out; Constitution Principle IV. Resolved in Clarifications 2026-05-08 Pass 2.)*

### Functional Requirements — Simulation chat grounding (extends spec 024)

- **FR-RAG-SIM-01**: The Simulation Controller MUST invoke the same shared retrieval client as the operational agents (FR-RAG-AG-01) before each chat-turn inference call. *(User input: "Extend the simulation functionality to use the same corpus data".)*
- **FR-RAG-SIM-02**: The simulation chat SSE stream MUST emit a `citation` event for each grounded claim with `{jurisdiction, topic, page, source_url, sha256_of_chunk}`. The UI is responsible for rendering, but the protocol is server-controlled. *(Driven by Resilience Planner + Observer-Auditor + PIO personas.)*
- **FR-RAG-SIM-03**: When no corpus chunk is relevant, the Controller MUST emit `citations: []` and a "no corpus match — recommend operator verification" note. The Controller MUST NOT fabricate citations. *(Driven by Risk Manager + Observer-Auditor.)*
- **FR-RAG-SIM-04**: Simulation chat audit entries MUST include `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `corpus_build_sha`, `retrieved_chunks[]` — equivalent to FR-RAG-AG-02. *(Constitution Principle IV.)*
- **FR-RAG-SIM-05**: Simulation rate limits, comms-block, tenant isolation, and approval workflow from spec 024 are preserved unchanged. Watermarking of any draft warning composed inside a simulation (`SIMULATION — DO NOT DISTRIBUTE`) is preserved. *(Driven by spec 024 PIO acceptance; Constitution Principle V.)*
- **FR-RAG-SIM-06**: When a Resilience Planner runs a *scripted* scenario timeline, the scripted events fire deterministically without RAG round-trips (per FR-RAG-NS-06). Free-form chat answers in the same simulation remain grounded. *(Driven by Resilience Planner memo carve-out.)*

### Functional Requirements — Approval, life-safety, and degraded-mode

- **FR-RAG-LS-01**: RAG grounding MUST NOT replace human approval authority for safety-critical decisions (public alert release, evacuation orders, resource conflicts, escalations). RAG provides *context* and *options*; humans retain veto. *(Constitution Principle I; cross-cutting theme in operational persona memo.)*
- **FR-RAG-LS-02**: Field Coordinator-aligned agents MUST support an offline corpus cache (per User Story 6) seeded with hazard thresholds, safety-escalation criteria, sector boundaries, AIIMS span-of-control, evacuation centre setup checklists. The cache MUST be bounded to **≤ 500 MB per device** (covers AIDR + national doctrine + each jurisdiction's most-cited handbooks with growth headroom). The cache manifest is versioned and **dual-signed**: (a) the master `corpus_build.sha256` manifest is signed at build time using spec 032 FR-AI09 **cosign keyless** (Sigstore + GitHub OIDC); (b) the cache bundle additionally carries an **age-encrypted detached signature** using the tenant's offline public-key set so Field Coordinators can verify integrity in degraded-connectivity mode without OIDC connectivity. Cache **TTL is 14 days**; on the next online re-sync an **audit-logged refresh** MUST occur. Agents refuse to extend beyond cached topics while offline. On reconnect, queued audit entries are reconciled with original timestamps preserved. *(Driven by FC + DFES-WA + NTES + SES-TAS + SAPOL Far North personas; Constitution Principle IV auditability of every decision in degraded mode. Resolved in Clarifications 2026-05-08.)*
- **FR-RAG-LS-03**: Public-facing outputs (warnings, dashboards, maps) drawn from RAG-grounded recommendations remain subject to human review (Constitution Quality Gates). The audit chain MUST capture both the LLM-grounded draft and the human-approved final. *(Driven by IC + PIO; Constitution Quality Gates.)*

### Key Entities

- **CorpusEntry** — A single source's `{handbook.md, source.json, images/}` tuple. Carries `jurisdiction`, `topic`, `mode (full-text|metadata-only|excluded)`, `sha256`, `retrieved_at`, `publisher`, `edition`, `licence`, `etag`, `last_modified`. Source of truth: `docs/corpus/`.
- **Chunk** — A retrieval unit produced from a `full-text` `handbook.md`. Carries `chunk_id`, `corpus_entry_id`, `page`, `sha256_of_chunk`, `tokens`, `embedding`, `embedding_model_id`, `corpus_build_sha`, `licence_mode`.
- **RetrievalRequest** — `{agent_name, jurisdictions[], hazard_type, query_text, top_k, classification_max}`. Emitted by every grounded agent and by the simulation Controller.
- **RetrievalResult** — `{chunks[], retrieval_latency_ms, embedding_model_id, corpus_build_sha, classification_filter_applied}`.
- **Citation** — `{jurisdiction, topic, page, source_url, sha256_of_chunk}`. Emitted on recommendation cards and in the simulation chat SSE stream.
- **AuditRecord (LLM-call)** — `{call_id, agent_name, prompt_sha, model_id, model_version, deployment_alias, corpus_build_sha, retrieved_chunks[], rag_used (bool), rag_optout_reason (nullable), gateway_decision, hallucinated_citation_count, output_tokens, output_text_hash, operator_actions[]}`. Append-only; integrity-verified.
- **CarveoutRegistryEntry** — `{model_name, region, business_justification, approver_identities[], review_date}` (per spec 032 FR-AI03a). Source of truth: `infra/parameters/foundry-carveout.yaml`.
- **OfflineCacheManifest** — `{version, generated_at, corpus_build_sha, signature, entries[]}`. The signed list of corpus chunks shipped to Field Coordinator-aligned processes.
- **RagOptoutAdr** — A markdown ADR under `docs/decisions/036-foundry-rag-grounding/` naming the FR ID, the persona memo citation, the named approver, and the rationale.
- **EquivalenceTestResult** — Per-agent canary-gate outcome record (extends spec-033 FR-023 shape) with `decision_equivalence` (≥ 0.95), `schema_equivalence` (== 1.0), `citation_fidelity` (≥ 0.7 from Phase E3), `verbatim_source_match`, `corpus_build_sha`, `embedding_model_id`. Source of truth: `apps/eval-runner/` artefacts. Authoritative shape: [`data-model.md`](./data-model.md) §EquivalenceTestResult.

---

## Assumptions

- **A1**: `docs/corpus/` is built and maintained by the existing pipeline at `scripts/disaster_corpus/` (`fetch.py` / `pdf_to_md.py` / `build.py` / `manifest.py` / `aidr_backfill.py`). This spec does **not** modify that pipeline (out of scope).
- **A2**: `infra/modules/ai-search.bicep` and `infra/bicep/modules/eval/foundry-deployments.bicep` already exist and are reused. Any deltas needed for this spec are additive.
- **A3**: The carve-out registry file `infra/parameters/foundry-carveout.yaml` already exists (per spec 032) with its companion `foundry-carveout.schema.json`. This spec populates it for the new Foundry deployments and tightens CD enforcement; it does not redefine the schema.
- **A4**: Microsoft Foundry inference endpoints, accessed via the **Azure AI Inference SDK** (`azure-ai-inference`), expose token-streaming chat-completion-equivalent APIs sufficient to back (a) the agent `LLMClient.generate_response` interface, (b) the MAF `OpenAIChatClient` factory replacement, (c) the simulation controller's `client.chat.completions.create(stream=True, tools=[...])` shape. Any gap requires a planning-stage adapter shim in the Foundry client wrapper, modelled on `apps/eval-runner/src/ama_eval/foundry_client.py`. *(Resolved in Clarifications 2026-05-08.)*
- **A5**: AIDR handbook indexing rights from spec 032's `INDEXING-LICENCE-NOTE.md` extend to indexing the AIDR portion of `docs/corpus/aidr/`. State / territory / Commonwealth / agency entries each carry their own `licence` field in `source.json`; per-entry compliance is the contract.
- **A6**: Constitution Non-Negotiable #2 Amendment 1.2.0 (Foundry carve-out) is the binding policy; any agent or operator who needs to widen it requires an explicit Constitution amendment, not a spec deviation.
- **A7**: Spec 024's tenant-isolation, comms-block, and approval semantics for the simulation are unchanged. This spec only **adds** corpus grounding to the simulation chat; it does not alter rate limits, role gating, or PublicationService egress controls.
- **A8**: Foundry-hosted embedding model is **`text-embedding-3-large` at 3072 vector dimensions** (Resolved in Clarifications 2026-05-08; see FR-RAG-IDX-02). Token-per-chunk parameters are tuned at planning time within that embedding-model commitment.

---

## Out of Scope

- **OOS-1**: Modifying prompt-template content beyond adding RAG context blocks at the call sites. Prompt rewrites belong to follow-on work.
- **OOS-2**: Replacing Azure AI Content Safety. Content Safety remains in place; RAG-grounded outputs continue to traverse the existing validator.
- **OOS-3**: Changing the corpus build pipeline at `scripts/disaster_corpus/`. Sourcing, fetching, conversion, and manifest generation are unchanged.
- **OOS-4**: Adding new corpus sources. The corpus content is the input; source curation belongs to a separate change.
- **OOS-5**: Replacing or redefining spec 032's carve-out registry mechanism. This spec **populates and gates against** that registry; it does not redesign it.
- **OOS-6**: Replacing the simulation Controller's system prompt + tool manifest (spec 024's `controller_prompt.md`). Only the inference plane and grounding hooks change.
- **OOS-7**: Live integration with BoM / GA / DACC operational APIs. Those remain runtime calls per FR-RAG-NS-02 / -03 / -07; building or replacing those clients is not in scope.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of agent recommendations from Monitoring, Risk Assessment, Evacuation, Resource Allocation, and Communication carry at least one corpus citation when invoked on grounded paths; sampled audit reconstruction succeeds in ≤ 60 seconds per recommendation. *(User Story 1.)*
- **SC-002**: 0 occurrences of `from openai import AzureOpenAI`, `from openai import AsyncAzureOpenAI`, or `OpenAIChatClient(... mode="azure_openai" ...)` in production paths after migration; CI fails any reintroduction. *(User Story 2.)*
- **SC-003**: 100% of Foundry deployments referenced by the deployment plan are present in `infra/parameters/foundry-carveout.yaml` with non-placeholder approver identities and a `review_date` ≤ 12 months out; CD fails on violation. *(User Story 2; FR-RAG-CV-01/02.)*
- **SC-004**: 0 production data-plane resources resolve outside `australiaeast` / `australiasoutheast`; CD fails on violation. *(User Story 2; FR-RAG-CV-04.)*
- **SC-005**: Re-running ingest against an unchanged `docs/corpus/` produces 0 re-embeddings and 0 index churn, and completes in ≤ 10% of the cold-start runtime. *(User Story 4; FR-RAG-IDX-04.)*
- **SC-006**: 100% of `mode: full-text` entries are body-indexed; 100% of `mode: metadata-only` entries are metadata-only-indexed; 0 `mode: excluded` entries appear in the index. CI verifies on every deploy. *(User Story 4; FR-RAG-IDX-02.)*
- **SC-007**: 100% of simulation chat turns that produce a grounded reply emit at least one `citation` SSE event with valid corpus provenance; 0 fabricated citations across a 200-prompt jailbreak / hallucination test suite. *(User Story 3; FR-RAG-SIM-02/03.)*
- **SC-008**: Every non-grounded path in production agent code carries a `# RAG-OPTOUT [FR-RAG-NS-NN]` comment AND a corresponding ADR file; CI lint enforces this on every PR. *(User Story 5; FR-RAG-NS-08.)*
- **SC-009**: Field Coordinator-aligned offline-mode answers are 100% drawn from cached corpus citations; queued audit entries on reconnect appear in the central store within 60 seconds and preserve their original timestamps. *(User Story 6; FR-RAG-LS-02.)*
- **SC-010**: For multi-jurisdiction queries, retrieval surfaces jurisdiction-disambiguated chunks (e.g., FRNSW vs NSW RFS, SES NSW vs SES VIC vs NTES) with 0 silent conflations across a curated 50-query persona-driven test set. *(User Story 7; FR-RAG-AG-04.)*
- **SC-011**: Corpus-build-SHA + prompt-SHA + model-version + retrieved-chunks-set together permit deterministic audit reproduction of any historical recommendation; sampled reproduction yields byte-identical retrieval inputs ≥ 95% of the time across a one-month replay window. *(Constitution Principle IV; User Story 1.)*
- **SC-012**: Operator-perceived chat-turn latency in the simulation increases by ≤ 30% relative to the pre-grounding baseline at the 95th percentile, accommodating the retrieval round-trip. *(User Story 3; spec 024 baseline.)*

---

## Closed Questions

> All three original `[NEEDS CLARIFICATION]` markers were resolved in the **2026-05-08 Pass 1** clarification session, and four additional residual ambiguities surfaced by **Pass 2** (cutover sequencing, embedding rebuild SLA, test seam, Observer-Auditor carve-out) were resolved in the same day's **Pass 2** session — see the **Clarifications** section above. **None remain outstanding** at Phase E close (T149 / 2026-05-08); spec is shippable.

**Pass 1 (2026-05-08) — original `[NEEDS CLARIFICATION]` markers**

- ~~Foundry inference SDK + token-scope~~ → **Resolved (2026-05-08)** — Azure AI Inference SDK (`azure-ai-inference`); env vars `AZURE_AI_PROJECT_ENDPOINT` + `AZURE_AI_PROJECT_DEPLOYMENTS`; AAD scope `https://cognitiveservices.azure.com/.default`. See FR-RAG-FM-01, FR-RAG-FM-05, A4.
- ~~Embedding model choice + vector dimensions + per-jurisdiction partitioning~~ → **Resolved (2026-05-08)** — `text-embedding-3-large` @ 3072 dims; single Azure AI Search index with `jurisdiction` / `topic` / `licence_mode` filter fields; jurisdiction-scoped queries union own-jurisdiction + `national` + `aidr`. See FR-RAG-IDX-02, FR-RAG-IDX-08, A8.
- ~~Offline cache footprint + signing~~ → **Resolved (2026-05-08)** — ≤ 500 MB per device; dual signature (cosign keyless per spec 032 FR-AI09 + age-encrypted detached signature); 14-day TTL with audit-logged refresh on re-sync. See FR-RAG-LS-02.

**Pass 2 (2026-05-08) — residual ambiguities found by deeper taxonomy scan**

- ~~OpenAI → Foundry cutover sequencing (no FR previously bound the migration to spec-033 FR-023 equivalence + spec-029 feature flags)~~ → **Resolved (2026-05-08 Pass 2)** — per-agent canary behind spec-029 feature flag, gated by spec-033 FR-023 equivalence (≥ 95% decision-equivalence + 100% schema-equivalence); spec-014 `_generate_with_fallback` chain intact across the migration window; FR-RAG-FM-04 lint binds atomically in the PR that deletes the legacy OpenAI client. See **FR-RAG-FM-06**.
- ~~Embedding-model rebuild SLA + internal contradiction at the "Embedding model version change" Edge Case (the bullet simultaneously said "must not coexist in the same index" AND "joint partition keys")~~ → **Resolved (2026-05-08 Pass 2)** — blue-green parallel index strategy; alias flip < 60s; cold rebuild SLA ≤ 24h; old index retained 7 days for rollback; each index hosts exactly one embedding-model id. See **FR-RAG-IDX-04** (rewritten) and the corresponding Edge Case bullet (rewritten).
- ~~No FR previously required the migrated Foundry client to expose a stub seam, so contract tests for citation attachment / hallucinated-citation suppression / RAG-opt-out audit paths could not run hermetically~~ → **Resolved (2026-05-08 Pass 2)** — constructor-injectable `chat_complete` callable mirroring `apps/eval-runner/src/ama_eval/foundry_client.py`. See **FR-RAG-FM-07**.
- ~~Observer-Auditor "non-decision" RAG-not-suitable carve-out was named in the personas list (References line 342) but had no corresponding FR-RAG-NS-* clause~~ → **Resolved (2026-05-08 Pass 2)** — added **FR-RAG-NS-09** (Observer-Auditor non-decision); CI-lint anchor remains at FR-RAG-NS-08 to preserve all existing `# RAG-OPTOUT [FR-RAG-NS-NN]` code-comment cross-references.

---

## References

### Constitution

- `.specify/memory/constitution.md` — Principle I (Primacy of Life), Principle IV (Transparency & Auditability), Principle V (Warning and Public Information), VI-C (Vulnerable Populations), Non-Negotiable #2 (Data sovereignty + Microsoft Foundry carve-out, Amendment 1.2.0), Quality Gates.

### Corpus

- `docs/corpus/README.md` — licence modes, `source.json` provenance, `handbook.md` page rendering, AIDR exemplar shape.
- `docs/corpus/MANIFEST.md` — auto-generated inventory of every entry.

### Persona memos consulted

- `personas-input/operational.md` — 10 AIIMS personas, including explicit RAG-not-suitable carve-outs (Planning collection-only, Logistics transactional, Resilience-Planner scenario-execution, Observer-Auditor non-decision).
- `personas-input/sectors-eastern.md` — NSW (FRNSW, MRNSW, NSW Ambulance, NSW RFS, NSWPF, SES NSW), VIC (Ambulance Victoria, CFA, FRV, SES VIC, VicPol), QLD (QAS, QFD, QPS, SES QLD); jurisdiction-disambiguation discipline.
- `personas-input/sectors-southern-western.md` — SA (SAAS, SACFS, SAMFS, SAPOL, SES-SA), WA (DFES-WA single combined agency, SJA-WA, WAPOL), TAS (AT, SES-TAS, TASPOL).
- `personas-input/sectors-territories.md` — ACT (ACTAS, ESA, ACT F&R, ACT Policing, ACT RFS, AFP-ACT, ACT SES), NT (Bushfires NT, NTES, NTFRS, NTPF, SJA-NT); Indigenous-liaison + degraded-connectivity emphasis.
- `personas-input/sectors-commonwealth.md` — ABF, ADF (DACC + classification carve-out), AFP, ARC, ASA, BoM (live forecasts: RAG-not-suitable), GA (live seismic: RAG-not-suitable), NEMA, RFDS, SJA-Nat, Surf Lifesaving.
- `personas-input/sectors-crosssector.md` — Community NGOs, Health, Local Government, State Government, Territory Government, Transport, Utility, Volunteer.

### Existing related specs

- `specs/014-azure-openai-integration/spec.md` — origin of `LLMClient`, MI auth, `_generate_with_fallback`. Migrated by this spec.
- `specs/018-aidr-guidance-integration/spec.md`, `specs/019-aidr-additional-guidances/spec.md` — referenced.
- `specs/024-simulation-control-chat/spec.md` — Simulation Controller; extended by this spec.
- `specs/030-llm-eval-framework/spec.md` — eval gates; reference foundry client.
- `specs/032-rubric-improvements/spec.md` — FR-AI01..FR-AI10 (especially FR-AI03a carve-out registry, FR-AI06 private endpoints, FR-AI09 cosign signing); extended by this spec.
- `specs/033-maf-adoption/spec.md` — MAF adoption; chat-client factory referenced by FR-RAG-FM-02.

### Existing infrastructure to reuse

- `infra/modules/ai-search.bicep` — AI Search module.
- `infra/bicep/modules/eval/foundry-deployments.bicep` — Foundry deployment module.
- `infra/parameters/foundry-carveout.yaml` + `foundry-carveout.schema.json` — registry (per spec 032).
- `apps/eval-runner/src/ama_eval/foundry_client.py` — reference Foundry client wrapper.
- `scripts/disaster_corpus/` — corpus build pipeline (untouched).

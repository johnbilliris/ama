# Static Implementation Audit: Foundry RAG Grounding

## Verdict

**Implementation is not complete at the reviewed revision.** This report records 26 open remediation tasks:
21 P1 security/correctness/composition findings followed by five P2 integration/evidence findings. No runtime,
deployment, model-quality, performance or human-approval success is claimed.

Coverage: **241 original tasks, 68 FRs, 19 SCs, 38 acceptance scenarios, 342 checklist items**. Additional coverage
includes ten explicit edges, twelve assumptions, eight exclusions, forty clarification decisions, twenty-four research
decisions, forty persona concerns, fifteen quoted R3 findings, six plan goals, five milestones, eighteen risks and
eighteen checkpoints. Task statuses: **44 IMPLEMENTED, 155 PARTIAL, 19 CONFLICT, 3 MISSING, 6 SUPERSEDED,
14 UNVERIFIED**. Original states are preserved independently of these findings.

The principal blockers are ungrounded mounted agent paths, bypassable transit/consent controls, explicitly public
Search configuration, unsafe ingest/promotion/provenance, disconnected audit/offline/coordination consumers, and
acceptance gates that compare authored or empty data. Existing typed contracts, jurisdiction union, helper assertions,
ADR bodies and component accessibility work are credited where supported. Hard-cutover supersession is limited to
the explicitly retired activation mechanism; it does not waive grounding, safety, audit or index-lifecycle obligations.

## Scope and Evidence Boundary

- Review date: 2026-09-14.
- Specification: `036-foundry-rag-grounding` only, not the other specification numbered 036.
- Expected and observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (read-only Git metadata).
- No report existed at the start. The initial worktree had untracked audit artifacts; no tracked modifications were reported.
- Only this report may be written. Other implementation-review reports are excluded from evidence and delegation.
- Method: static source, configuration, test-assertion, and recorded-artifact inspection only.
- No SDK/application imports, tests, verifier scripts, builds, package installation, model/retrieval calls,
  browsers, servers, cloud queries, deployments, runtime/debug calls, or external approvals are performed.
- IMPLEMENTED means supported source or authored artifact, not demonstrated execution. Outcome claims without
  attributable evidence remain UNVERIFIED. Original checkbox state is retained independently of audit status.
- Remediation and validation instructions below are future work, not actions performed by this audit.

The governing contract is [Review Contract](../001-spec-implementation-audit/README.md#L11), with
[repository review instructions](../../.github/instructions/code-review.instructions.md#L12).

## Verified Composition

The current [infrastructure switch](../../infra/main.bicep#L242) defaults to enabled. The historical
indexing deferral in [Session 6](spec.md#L94) is not evidence of current absence or deployment success.
[ADR 20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L29)
explicitly retires gradual chat-plane activation; it retains regression and corpus blue-green obligations.

The initial no-retrieval hypothesis is supported by the actual [container startup](../../apps/agents/Dockerfile#L48),
[dispatcher inference](../../apps/agents/dispatcher/agent.py#L209), and the independently available
[base MAF run path](../../apps/agents/maf_runtime/agents/_factory.py#L265). A configurable retrieval helper
is not equivalent to a mandatory pre-inference call in either execution path.

## Inputs and Reading Coverage

All 32 original local files were read in full across this review and isolated read-only delegates:
7,203 source lines / 736,058 bytes. Long specification lines 333 and 342 were recovered without truncation.
No delegate read another implementation-review report or modified files. The following inventory excludes this report.

| Input | Lines | Role |
| --- | ---: | --- |
| [spec.md](spec.md#L1) | 557 | All stories, FRs, SCs, six clarification blocks, assumptions and exclusions |
| [tasks.md](tasks.md#L1) | 947 | All 241 definitions, states, checkpoints and Phase F appendix |
| [plan.md](plan.md#L1) | 553 | Goals, topology, phases, risks and appended amendment plan |
| [research.md](research.md#L1) | 387 | R-01 through R-24, deferrals and amendment decisions |
| [data-model.md](data-model.md#L1) | 506 | Original and amended entities and invariants |
| [quickstart.md](quickstart.md#L1) | 444 | All setup, execution and amendment instructions, read only |
| [quickstart-validation.md](quickstart-validation.md#L1) | 148 | Historical stub-environment account and deferred live steps |
| [HANDOFF.md](HANDOFF.md#L1) | 91 | External authority work and acceptance blockers |
| [persona-traceability.md](persona-traceability.md#L1) | 109 | Forty concerns across nine memo groups |
| [analyze-report.md](analyze-report.md#L1) | 162 | Authored cross-artifact review, not independent execution proof |
| [contracts/audit-record-llm-call.json](contracts/audit-record-llm-call.json#L1) | 391 | Audit shape and appended invariants |
| [contracts/chunk-metadata.schema.json](contracts/chunk-metadata.schema.json#L1) | 212 | Agency, authority and protection metadata |
| [contracts/citation-envelope.json](contracts/citation-envelope.json#L1) | 103 | Citation wire contract |
| [contracts/conflict_detection.schema.json](contracts/conflict_detection.schema.json#L1) | 174 | Conflict evidence and resolution contract |
| [contracts/cultural-authority-registry.schema.json](contracts/cultural-authority-registry.schema.json#L1) | 85 | Consent contract |
| [contracts/foundry-chat-client.md](contracts/foundry-chat-client.md#L1) | 334 | Inference seam, errors and metadata |
| [contracts/foundry-cv.schema.json](contracts/foundry-cv.schema.json#L1) | 123 | Registry contract |
| [contracts/ingest-pipeline.md](contracts/ingest-pipeline.md#L1) | 234 | Ingestion, lifecycle, parity, audit and snapshot contract |
| [contracts/offline-cache-manifest.json](contracts/offline-cache-manifest.json#L1) | 129 | Signed cache contract |
| [contracts/retrieval-service.md](contracts/retrieval-service.md#L1) | 290 | Retrieval port, limits, errors and deferred REST surface |
| [contracts/staleness_alert.schema.json](contracts/staleness_alert.schema.json#L1) | 137 | Freshness event contract |
| [checklists/requirements.md](checklists/requirements.md#L1) | 200 | Original requirements checklist plus amendments |
| [checklists/migration.md](checklists/migration.md#L1) | 114 | Migration, citation and amendment checklist |
| [checklists/compliance.md](checklists/compliance.md#L1) | 157 | Original and appended governance obligations |
| [checklists/cultural-authority-protocols.md](checklists/cultural-authority-protocols.md#L1) | 76 | Consent and human authority |
| [checklists/federal-compliance-mapping.md](checklists/federal-compliance-mapping.md#L1) | 65 | Privacy, ISM, PSPF and COMDISPLAN |
| [checklists/audit-and-approval-workflow.md](checklists/audit-and-approval-workflow.md#L1) | 74 | Audit, approval, offline authority and migration |
| [checklists/multi-agent-coordination.md](checklists/multi-agent-coordination.md#L1) | 71 | Conflicts and manual escalation |
| [checklists/test-coverage-windows.md](checklists/test-coverage-windows.md#L1) | 66 | Platform, load, fixture and E2E obligations |
| [checklists/observability.md](checklists/observability.md#L1) | 60 | Metrics, transport and SLOs |
| [checklists/accessibility.md](checklists/accessibility.md#L1) | 63 | UI SHOULD requirements and review |
| [checklists/README.md](checklists/README.md#L1) | 141 | Checklist maps and review instructions; no item definitions |

Additional directly associated inputs include all referenced ADR bodies under
[docs/decisions/036-foundry-rag-grounding](../../docs/decisions/036-foundry-rag-grounding),
the cited compliance/accessibility/test/runbook artifacts, source configuration, providers, consumers and assertions.
Applicable review/Python fact-grounding/Bicep/Cosmos guidance was read; operational skill steps were not executed.
Searches for referenced original and R3 persona memo filenames/locations found no repository copies. The forty
local traceability concerns remain reviewable, but consultation and original memo completeness are UNVERIFIED.

Negative findings below use bounded searches of the named owning files plus `apps/**/*.py`, relevant `packages/`,
`apps/web/src/`, `infra/**/*.bicep`, `.github/workflows/`, `scripts/`, `tools/lint/` and corresponding test homes.
Relocated helpers and the alternate infrastructure graph were inspected before declaring a path unmounted or missing.
No platform capability, SDK serialization success, performance, actual deployed posture, or human approval is inferred
from configuration, comments, checkboxes, fake providers or an authored success label.

## Findings and Open Remediation

### P1: Non-AU Payload Controls Can Be Bypassed

- [ ] AUD-036-RAG-001 Enforce minimisation on complete inference and embedding envelopes

**Affected:** FR-RAG-CV-03/04, FR-RAG-NS-07, FR-RAG-FM-05, T014, T022, T023, T057; US2.5 and the quota/classification edges.
**Expected versus observed:** All non-AU prompts and responses require current registry policy, minimisation and audited denial.
The [shared gateway boundary](../../apps/agents/common/foundry_chat_client.py#L362) skips unknown regions and checks
only string user messages. System grounding, tool/history content and responses are not covered. The simulation
[history assembly](../../apps/api/app/services/simulation/controller_service.py#L568) can reintroduce the original
message after redacting only its forwarded copy. This is a source-level transit risk, not evidence that a leak occurred.
**Developer:** Validate the fully assembled envelope immediately before every transport call, including embeddings;
reject unresolved/expired policy, apply response controls, and durably record redaction/denial without logging protected
payloads. Preserve tenant isolation, tool-loop semantics, Content Safety and explicit template degradation; do not route
classified material through a fallback endpoint. Inventory all SDK adapters rather than repairing only the helper.
**Tester:** Extend [gateway tests](../../tests/integration/test_data_minimisation_gateway.py#L30) and
[simulation SSE tests](../../tests/integration/test_simulation_sse_citation.py#L1) using injected recording transports.
Cover clean AU and approved non-AU traffic, history-replayed PII, protected system/tool content, structured messages,
unknown regions, expired registry rows, response PII and embedding requests. Assert denied content never reaches a
transport and each attempt has a correlated, minimised audit event.
**Future-only validation:** After a prepared isolated Python environment and transport injection are available,
`pytest -q tests/integration/test_data_minimisation_gateway.py tests/integration/test_simulation_sse_citation.py`.
No live credentials/network are needed for these contract assertions. Expected: complete-envelope allow/redact/deny cases pass.
**Completion:** Every production transport uses the same enforceable policy boundary; all negative cases prove zero
forbidden transit and durable denial evidence. Non-AU runtime/deployment compliance remains separately UNVERIFIED.

### P1: Decision-Agent Grounding Is Not Composed Into Actual Execution

- [ ] AUD-036-RAG-002 Ground every mounted decision-agent inference path

**Affected:** FR-RAG-AG-01/02/03, FR-RAG-FM-01/02/06/07, FR-RAG-LS-01/03, T018, T019, T028, T083,
T087, T093, T094, T095, T096, T097, SC-001; US1 and US8.
**Expected versus observed:** Five decision agents must retrieve before prompt-bearing inference. The deployed
[dispatcher](../../apps/agents/dispatcher/agent.py#L209) calls its SDK directly and returns empty citations.
[Simulation subagents](../../apps/api/app/services/simulation/sub_agents/_base.py#L35) consume this dispatcher.
The [MAF facade](../../apps/agents/maf_runtime/agents/_factory.py#L265) also invokes inference without its retrieval helper;
the inspected per-agent overrides do not supply a grounded replacement. Grounding flags alone cannot change this.
**Developer:** Introduce the mandatory retrieve/augment/infer/filter/audit boundary in the actual handler composition
and each supported legacy/MAF mode. Carry authenticated incident, jurisdiction, tenant and classification context.
Preserve public output schemas, Content Safety and template fallback. Emit explicit kill-switch/error provenance;
do not mark ungrounded responses as grounded or restore the superseded canary activation requirement.
Wire Communication inclusion retrieval before drafting and correct its request-contract mismatch at
[grounding helper](../../apps/agents/communication/grounding.py#L83).
**Tester:** Extend [executor tests](../../tests/unit/test_executor_base.py#L1),
[Communication pipeline tests](../../tests/unit/test_communication_pipeline.py#L1) and
[inclusion tests](../../tests/integration/test_communication_agent_atsi_cald.py#L78).
For each of the five real handlers assert ordered retrieve-before-infer calls, authoritative citations and audit metadata.
Exercise legacy/MAF modes, missing endpoint, 503, empty retrieval, kill-switch, denied classification and ATSI/CALD/Auslan
requests. Assert human approval remains required and no placeholder delegate is treated as model evidence.
**Future-only validation:** With all external adapters replaced at constructor boundaries,
`pytest -q tests/unit/test_executor_base.py tests/unit/test_communication_pipeline.py tests/integration/test_communication_agent_atsi_cald.py`.
Extend these existing homes to cover dispatcher composition; verify discovery before claiming all five agents covered.
**Completion:** Mounted production handlers and supported alternate modes demonstrate the full ordered chain and
truthful no-match/degraded behavior through assertions; actual model quality remains a separate evidence gate.

### P1: Cultural Protection and Consent Verification Are Not Enforced

- [ ] AUD-036-RAG-003 Bind protected retrieval to verified tenant and council consent

**Affected:** FR-RAG-CA-01/02/03/04/05, FR-RAG-AG-02/04, T181, T193, T194, T195, T196, T198,
T199, T200, T201, SC-014; US9.1/2 and Session 4/5 consent obligations.
**Expected versus observed:** Protected chunks require current community consent after retrieval and before inference.
The [ingest caller](../../apps/ingest-runner/src/ama_ingest/__main__.py#L372) omits protection metadata and
[retrieval projection](../../apps/agents/common/retrieval_client.py#L325) discards it. The
[standalone gate](../../apps/agents/common/cultural_authority_gate.py#L49) has no production caller in the searched
agent/API Python paths. The [registry](../../apps/agents/common/cultural_authority_registry.py#L203) accepts signatures
without an injected verifier, and its consent check does not bind the requested council, tenant or grant start time.
**Developer:** Preserve protection fields for full-text and metadata-only entries; enforce the gate on fresh and cached
results using authenticated operator/tenant/council context. Require real trusted signature verification, current grants,
effective revocations and cache invalidation. Keep public doctrine available when registry access fails. Resolve registry
renewal uniqueness constraints and mount the registry in the active infrastructure graph. Enforce locked-on policy at
the real production flag mutation boundary. Community content and sign-off remain human work, never synthetic substitutes.
**Tester:** Extend [registry tests](../../tests/contract/test_cultural_authority_registry.py#L47),
[gate tests](../../tests/integration/test_cultural_authority_gate.py#L55), and
[lockdown tests](../../tests/integration/test_cultural_authority_flag_lockdown.py#L24).
Use genuine signed canonical fixtures for valid matching consent, tampering, untrusted keys, wrong tenant/council,
future/expired/revoked grants, warm-cache revocation and unavailable registry. Drive shared retrieval and assert protected
text is absent from model inputs, citations and logs; public results remain. Test actual OPA, not copied Python rules.
**Future-only validation:** In a prepared offline test environment with trusted test keys and pinned OPA,
`pytest -q tests/contract/test_cultural_authority_registry.py tests/integration/test_cultural_authority_gate.py tests/integration/test_cultural_authority_flag_lockdown.py`.
Expected: unauthorised content is consistently suppressed and correlated consent decisions are recorded.
**Completion:** The real retrieval/flag/provider composition enforces all consent boundaries; human corpus approval
and deployed registry population stay UNVERIFIED until independently attributable evidence exists.

### P1: Active Search Configuration Contradicts Private-Only Access

- [ ] AUD-036-RAG-004 Wire private Search networking and service-scoped identities

**Affected:** FR-RAG-IDX-06/08, FR-RAG-CV-04, T048, T049, T050, T051, SC-004.
**Expected versus observed:** Search must be private-endpoint-only in AU East. The selected
[root module call](../../infra/main.bicep#L302) passes empty subnet/DNS identifiers and disables the
public-network restriction. Entra authentication does not replace network isolation. The
[writer role](../../infra/main.bicep#L351) is resource-group scoped. Actual deployed posture is UNVERIFIED.
**Developer:** Connect private endpoint, DNS and Container Apps VNet reachability in the active root graph; preserve
AU persistence, single-index economics and reader/writer separation. Reuse repository modules and obey recorded
governance constraints, AVM rules and approvals in a future IaC change; do not solve connectivity by public access.
**Tester:** Extend [capacity/config tests](../../tests/integration/test_capacity_alert.py#L1) and
[carve-out enforcement tests](../../tests/integration/test_carveout_enforcement.py#L1) with root-composition fixtures:
valid private AU graph, blank subnet/DNS, public override, non-AU location and over-broad writer assignment.
Assert selected parameters, private links and least-privilege role scopes, not merely module defaults.
**Future-only validation:** With pytest and read-only template fixtures, run
`pytest -q tests/integration/test_capacity_alert.py tests/integration/test_carveout_enforcement.py` after adding
these assertions. A later separately authorised private-network staging check is required for reachability.
**Completion:** The selected graph cannot produce a public production Search endpoint; role and network assertions
pass, and deployment/reachability evidence is attributed separately.

### P1: Deployment Checks Do Not Validate Effective Production Policy

- [ ] AUD-036-RAG-005 Bind resolved deployment policy and signed production gates

**Affected:** FR-RAG-CV-01/02/04, FR-RAG-CA-05, FR-RAG-COMP-01/02, T012, T013, T024, T025, T026,
T027, T057, T151, T152, T153, T154, T155, T202, T210, T211, SC-003/004/014/016/018.
**Expected versus observed:** [CD](../../.github/workflows/cd.yml#L211) calls the verifier without resolved
plan/environment input. The [checker](../../scripts/verify-carveout.ps1#L89) accepts two approvers and does not reject
every expired review; its optional location walker covers only part of the required data plane. Current
[model defaults](../../infra/modules/azure-openai.bicep#L29) do not match the three-row
[registry](../../infra/parameters/foundry-carveout.yaml#L21). The [OPA discriminator](../../infra/policy/rego/foundry_carveout.rego#L49)
trusts optional row environment rather than the actual deploy target. The relocated
[federal checker](../../infra/scripts/verify-federal-compliance.ps1#L82) checks signer labels, not cryptographic
approval, and is not called by the inspected workflows. Cultural/federal attestations are absent.
**Developer:** Validate resolved model/version/region/deployment and target environment before apply. Reject missing,
unknown, expired, placeholder or duplicate approvers; enforce three distinct prod and two dev/staging authorities.
Cover every required persistence resource and nested deployment location. Reconcile both registry schemas, fail
closed for unknown environment, and bind cryptographically verified cultural/federal approvals to the release/corpus
being approved. Preserve authority separation; software must not generate real approvals. Restore actual PR coupling
checks rather than manual-only workflows. Coordinate with AUD-036-RAG-023 for selected deployment inputs.
**Tester:** Extend [registry assertions](../../tests/contract/test_carveout_registry_entry.py#L47),
[real-policy test home](../../tests/contract/test_foundry_carveout.py#L75) and
[enforcement tests](../../tests/integration/test_carveout_enforcement.py#L1). Include yesterday-expired valid AU rows,
prod target with dev/missing row environment, distinct/duplicate identities, actual deployment-name/model-name
differences, nested non-AU data-plane resources, missing/tampered/wrong-release sign-offs, and the three quorum cases.
**Future-only validation:** Prepared Python, PowerShell, pinned OPA and recorded plan/signature fixtures are required;
`pytest -q tests/contract/test_carveout_registry_entry.py tests/contract/test_foundry_carveout.py tests/integration/test_carveout_enforcement.py`.
Expected: actual OPA executes with no Python semantic fallback; invalid releases fail before any apply step.
**Completion:** Active CD and flag/deployment gates enforce the effective policy and signature authority chain;
real human approvals and live compliance are still independently evidenced.

### P1: Licence Defaults and Revocation Leave Body Content Reachable

- [ ] AUD-036-RAG-006 Enforce explicit rights decisions and reconcile revoked index content

**Affected:** FR-RAG-IDX-01/02/07, T035, T037, T039, T043, T054, T055, SC-006; US4 and excluded-source edges.
**Expected versus observed:** [Missing mode defaults to full-text](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L38),
while the corpus policy is conservative. Static inventory found 146 of 155 sources omit mode; this is a policy ambiguity,
not a legal conclusion about their publishers. Excluded sources are skipped without deleting previous indexed bodies;
metadata-only replacement uses different keys. [SHA-only skip](../../apps/ingest-runner/src/ama_ingest/indexer.py#L280)
can preserve stale rights metadata. [Inventory lint](../../tools/lint/check_licence_inventory.py#L87) compares membership
and mode, not all rights/provenance columns. Excluded-source prompt lint and defensive runtime refusal are not established.
**Developer:** Obtain explicit per-source rights decisions, use a fail-closed conservative default, and reconcile
exclusion, downgrade, deletion and page removal against the active index. Never embed metadata-only body content.
Machine-check publisher, edition, URL, redistribution rights and verification state; enforce excluded references both
at prompt lint and at the runtime boundary. Preserve the existing corpus pipeline/OOS-3 and do not author new sources.
**Tester:** Extend [licence partition tests](../../tests/integration/test_licence_mode_partition.py#L83),
[inventory lint tests](../../tests/integration/test_indexing_licence_inventory_lint.py#L1) and
[corpus-entry tests](../../tests/integration/test_corpus_entry_validation.py#L65).
Start with a populated index; apply full-text-to-metadata, excluded, deleted-page, rights-only and URL-only changes.
Assert no revoked body/search/vector residue, zero forbidden embedding calls and rejected excluded template references.
**Future-only validation:** With deterministic in-memory external adapters but production ingest logic,
`pytest -q tests/integration/test_licence_mode_partition.py tests/integration/test_indexing_licence_inventory_lint.py tests/integration/test_corpus_entry_validation.py`.
Expected: transition and unknown-rights cases fail safely, not just fresh three-mode fixtures.
**Completion:** Current and formerly indexed material obey effective rights; inventory and runtime refusal cover all modes.

### P1: Live Ingestion Does Not Enforce Entry Idempotency or Model Rebuild Isolation

- [ ] AUD-036-RAG-007 Persist active build identity and skip unchanged entries before embedding

**Affected:** FR-RAG-IDX-03/04, A10, T031, T032, T033, T036, T040, T042, T044, T181, T182,
T188, T200, SC-005/006; model/schema-change and mid-update edges.
**Expected versus observed:** The [live alias provider](../../apps/ingest-runner/src/ama_ingest/live_clients.py#L316)
does not recover the active embedding model. [CLI rebuild selection](../../apps/ingest-runner/src/ama_ingest/__main__.py#L258)
therefore misses ordinary live incremental model changes; schema versions are not rebuild discriminators.
[Embedding precedes SHA skip](../../apps/ingest-runner/src/ama_ingest/__main__.py#L387), so unchanged entries are
re-chunked/re-embedded. The [idempotency test](../../tests/integration/test_idempotent_ingest.py#L113) expressly allows
this and relaxes the 10% timing condition. Writing into an active mixed-model index can damage retrieval before a later gate fails.
**Developer:** Persist and read active model/schema/build identity; compare entry identity before chunking or embedding.
Use a fresh target for model or required-schema changes, with no in-place active-index mutation. Account for rights and
metadata changes from AUD-036-RAG-006, and co-deploy cultural fields before the single amended rebuild.
**Tester:** Extend [idempotency tests](../../tests/integration/test_idempotent_ingest.py#L55),
[model-swap tests](../../tests/integration/test_blue_green_alias_flip.py#L53) and
[chunk invariants](../../tests/integration/test_chunk_index_invariants.py#L113) through production live-provider adapters
using recorded Search responses. Assert unchanged zero chunking/embedding/writes, single changed entry only, cold model
state recovery, schema-only rebuild, and no active-index writes before promotion.
**Future-only validation:** Prepared pytest/runner/domain dependencies and recorded provider fixtures;
`pytest -q tests/integration/test_idempotent_ingest.py tests/integration/test_blue_green_alias_flip.py tests/integration/test_chunk_index_invariants.py`.
A later measured warm/cold benchmark must meet the 10% criterion; static assertions do not prove its runtime.
**Completion:** Idempotency is enforced before expenditure and every model/schema change builds an isolated target.

### P1: Promotion Accepts Invented Baselines and Partial Uploads

- [ ] AUD-036-RAG-008 Gate promotion on complete measured parity evidence

**Affected:** FR-RAG-IDX-04/09, R-05, T029, T031, T033, T034, T044, T046, T100, T142, T188, SC-019.
**Expected versus observed:** [Promotion inputs](../../apps/ingest-runner/src/ama_ingest/__main__.py#L439) supply old
count/cost zero and decision equivalence 1.0, not measured old/new results. Schema equivalence and amended error/quality
conditions are not all enforced. [Upload failures](../../apps/ingest-runner/src/ama_ingest/live_clients.py#L223) are
logged and partial success is accepted; homogeneity samples only 1,000 documents. The manual
[flip script](../../infra/scripts/blue-green-flip.ps1#L106) has a placeholder parity phase before its real alias update.
**Developer:** Require attributable, nonempty measured inputs with schema equivalence, complete write acknowledgement
and exhaustive model homogeneity; fail on missing/NaN/empty evidence. Reconcile the research/contract/amendment gate
definitions under AUD-036-RAG-013, including error ratio and quality delta. Emit durable per-signal failure evidence;
never replace missing measurements with a passing constant or let a manual path bypass the gate.
**Tester:** Extend [parity failure tests](../../tests/integration/test_blue_green_parity_gate_fail.py#L100) and
[ingest contract tests](../../tests/contract/test_ingest_pipeline.py#L81). Cover each threshold just below/at/above,
missing baseline, empty regression fixture, partial batch failure, mixed model after document 1,000, interrupted build
and schema mismatch. Assert no alias PUT and a durable failure record on every invalid case.
**Future-only validation:** Prepared runner/test dependencies with recording upload/alias adapters;
`pytest -q tests/integration/test_blue_green_parity_gate_fail.py tests/contract/test_ingest_pipeline.py`.
Expected: all invalid promotions halt and valid complete evidence permits one atomic update.
**Completion:** Every promotion path consumes the same complete gate evidence; operational quality/timing remain separately measured.

### P1: Alias Pinning and Cache Provenance Do Not Control the Queried Index

- [ ] AUD-036-RAG-009 Bind search clients and cache entries to concrete index provenance

**Affected:** FR-RAG-IDX-04a, FR-RAG-AG-01/02/04, T060, T075, T079, T166, T168, T169, T221, SC-011/019.
**Expected versus observed:** [Alias resolution](../../apps/agents/common/retrieval_client.py#L644) falls back to the
alias; the [Search client](../../apps/agents/common/retrieval_client.py#L681) still targets that alias even when a
concrete name is supplied. [Cache identity](../../apps/agents/common/retrieval_client.py#L757) omits index/model and
other result-affecting request context, then [cached chunks are relabelled](../../apps/agents/common/retrieval_client.py#L891)
with newly resolved provenance. Defaults can stamp a zero build SHA. Public-corpus sharing alone is not proof of a
confidential tenant leak, but protected/operator-aware results require isolation before rollout.
**Developer:** Resolve once per agreed query lifecycle, instantiate both search arms against the concrete target,
validate build/model metadata and preserve it on cache hits. Key/invalidate caches for index/model/schema, top-k,
tenant/operator protection scope, incident/ranking flags and other filters. Resolve session-versus-query pinning
contradictions explicitly without breaking post-rollback new-query guarantees.
**Tester:** Extend [retrieval contracts](../../tests/contract/test_retrieval_service.py#L1) and
[blue-green E2E home](../../tests/e2e/test_blue_green_alias_flip.py#L1) with nonempty recorded SDK responses.
Change aliases between vector/lexical calls and between cached queries; assert both actual client targets, unchanged
fill provenance, distinct top-k/tenant/consent results and no zero-SHA success.
**Future-only validation:** Prepared pytest/async dependencies and recording Search factories;
`pytest -q tests/contract/test_retrieval_service.py tests/e2e/test_blue_green_alias_flip.py` after replacing the
unfinished live body and isolating network-free cases. Separately authorised staging is needed for real atomicity timing.
**Completion:** Concrete query identity, returned chunks and recorded provenance agree across every flip/cache boundary.

### P1: Rollback and Seven-Day Retention Lack Operational Consumers

- [ ] AUD-036-RAG-010 Mount authenticated rollback and flip-relative retention

**Affected:** FR-RAG-IDX-04/04a/09, T167, T170, T171, T172, T188, T221, T248, SC-019.
**Expected versus observed:** [Rollback service](../../apps/api/app/services/index_rollback.py#L126) has injected
callbacks but no mounted production caller in the bounded API/application search. Approval is a nonempty string,
not an authenticated Release Manager decision. Retention is represented in memory; the
[cleanup script](../../infra/scripts/cleanup-stale-indices.ps1#L96) uses index modification age rather than time since flip.
**Developer:** Connect parity-failure detection to durable Service Bus event/timer, authenticated manual approval,
concrete alias update, append-only completion record and on-call notification. Persist old-index retain-until from
promotion; schedule safe cleanup that excludes active/in-flight/rollback targets. Preserve manual authority and
do not reinstate superseded automatic rollback from the earlier research decision.
**Tester:** Extend [rollback tests](../../tests/integration/test_index_rollback_slo.py#L66) with authenticated role,
durable bus/alias/audit adapters: valid release approval, missing/wrong role, duplicate event, failure after alias PUT,
299/300/301-second deadlines, old-but-newly-retired indices and active index protection.
**Future-only validation:** Prepared pytest and recorded event/clock/provider fixtures;
`pytest -q tests/integration/test_index_rollback_slo.py`. Later isolated staging must prove all new queries use the old
index and the audit completion lands within five minutes of event emission, with seven-day accessibility.
**Completion:** Operationally reachable manual rollback and retention are durable, idempotent and independently measurable.

### P1: Snapshot Identity and Chunk Integrity Are Not End-to-End

- [ ] AUD-036-RAG-011 Produce immutable corpus snapshots and validated chunk provenance

**Affected:** FR-RAG-IDX-01/02/03/04, R-04/13, T031, T035, T036, T040, T041, T045, T056, SC-005/006/011.
**Expected versus observed:** [Manifest hashing](../../apps/ingest-runner/src/ama_ingest/manifest.py#L79) uses declared
source hashes while the [workflow](../../.github/workflows/corpus-ingest.yml#L85) hashes Git-tree output. Representative
source hashes identify PDFs, not rendered handbooks; live reads are not a frozen validated snapshot.
[CLI settings](../../apps/ingest-runner/src/ama_ingest/__main__.py#L124) ignore the job's build-SHA environment value.
Indexed provenance lacks required `retrieved_at`. [Word-based hard splitting](../../apps/ingest-runner/src/ama_ingest/chunker.py#L360)
does not guarantee the tokenizer cap or table/fence integrity; the cross-page flag describes later chunks on the same page.
**Developer:** Establish one canonical source/snapshot/build identity, verify frozen inputs before indexing, record all
required provenance and reject half-written or mismatched content. Preserve the corpus builder and source curation
boundaries. Enforce token limits on emitted chunks, handle oversized atomic blocks explicitly, and implement actual
cross-page duplication/anchors. Use AUD-036-RAG-012 for durable per-embedding-call evidence and 022 for real size telemetry.
**Tester:** Extend [ingest contract tests](../../tests/contract/test_ingest_pipeline.py#L81),
[entry validation](../../tests/integration/test_corpus_entry_validation.py#L65) and
[chunk invariants](../../tests/integration/test_chunk_index_invariants.py#L113). Cover PDF-versus-Markdown hash mismatch,
concurrent source mutation, licence-only changes, fixed build SHA, Unicode multi-token words, CRLF, oversized tables/fences,
multi-page sentences and missing provenance. Assert snapshot consistency, post-tokenizer bounds and resolvable page anchors.
**Future-only validation:** Prepared runner dependencies and the production tokenizer, with recorded corpus fixtures;
`pytest -q tests/contract/test_ingest_pipeline.py tests/integration/test_corpus_entry_validation.py tests/integration/test_chunk_index_invariants.py`.
Expected: corrupt/unstable inputs fail before writes and every emitted document satisfies the reconciled contract.
**Completion:** Build identity deterministically identifies the exact licensed, bounded, page-aligned material used.

### P1: Durable Per-Call Audit and Tamper Response Are Missing From Mounted Paths

- [ ] AUD-036-RAG-012 Persist complete per-call audit with integrity and recovery

**Affected:** FR-RAG-AG-02, FR-RAG-SIM-04, FR-RAG-LS-03, FR-RAG-COMP-01/02, T056, T062, T069,
T073, T081, T082, T090, T099, T102, T144, T159, T163, SC-001/011/017; US1.5 and replay edges.
**Expected versus observed:** The [mounted controller](../../apps/api/app/api/routes/simulation_chat.py#L44) has no
extended writer. [MAF middleware](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L213) records fingerprints
without required chunk provenance. The [spec writer](../../apps/agents/common/audit.py#L103) expects environment names
different from selected deployment, does not normalise Cosmos `id`, catches persistence errors and never uses its archive
URI. [Ingestion](../../apps/ingest-runner/src/ama_ingest/__main__.py#L335) defaults to an in-memory aggregate rather than
durable per-embedding-call records. No connected signing/tamper-publication-stop/paging path was found for these records.
**Developer:** Wire one validated durable writer at every inference/embedding/deny/empty/opt-out boundary, with actual
deployment identity, complete augmented prompt hash, token accounting, concrete index/build/chunk provenance and
operator actions. Preserve tenant partitions and immutable history. Provide idempotent acknowledgements, bounded
durable retries, seven-year archive/integrity verification and an explicit compromised-window publication stop plus
Observer-Auditor page. Do not silently acknowledge failed storage or equate telemetry with the audit store.
**Tester:** Extend [audit-shape tests](../../tests/contract/test_audit_record_shape.py#L150),
[replay tests](../../tests/integration/test_audit_replay.py#L95), and
[override completeness](../../tests/contract/test_sc017_override_completeness.py#L111). Drive actual handlers through
success, tool rounds, no match, denied transit, SDK failure and persistence failure. Assert durable IDs, correct hashes,
archive calls and deduplication; tamper with chunk/hash/operator evidence and assert publication blocking and paging.
Use recorded historical mixed-generation fixtures for replay, not builder-generated equality alone.
**Future-only validation:** Prepared pytest with recording Cosmos/archive adapters and signed test records;
`pytest -q tests/contract/test_audit_record_shape.py tests/integration/test_audit_replay.py tests/contract/test_sc017_override_completeness.py`.
A later authorised one-month sample must measure 95% replay and 60-second reconstruction; neither was executed here.
**Completion:** All call outcomes have durable, reconstructible evidence and tested integrity/recovery behavior.

### P1: Duplicate and Incompatible Contracts Defeat Additive Migration

- [ ] AUD-036-RAG-013 Reconcile versioned contracts without rewriting historical evidence

**Affected:** FR-RAG-AG-02/04, FR-RAG-IDX-03/04/04a/09, FR-RAG-CA-04, FR-RAG-LS-02,
T004, T005, T062, T071, T073, T074, T082, T113, T114, T154, T156, T160, T161, T162, T180,
T197, T227, T246; A3/10/12 and all contract amendments.
**Expected versus observed:** The [audit contract](contracts/audit-record-llm-call.json#L166) declares eight properties
twice; later offline-string/tie-break definitions override earlier boolean/nullable forms while
[Invariant 8](contracts/audit-record-llm-call.json#L320) still tests boolean true. The
[domain model](../../packages/domain/src/ama_domain/audit_record.py#L182) does not support every promised legacy-null
case and requires an index name on old grounded rows. The chunk, consent and conflict contracts disagree with their
data-model descriptions; Foundry contract and infrastructure registry schema are not parity mirrors. Exact byte equality
of seven other mirrors is supported, but does not resolve semantic contradictions.
**Developer:** Agree canonical versioned shapes and explicit migration precedence; reject duplicate JSON keys.
Separate tolerant historical reads from strict new writes, support offline provenance and nullable legacy additions,
and preserve existing immutable rows. Resolve parity-signal variants, query-versus-session pinning, 14/30-day cache
override, hot retention, consent scopes/signatures and conflict lifecycle under explicit decisions, not convenient defaults.
Keep source amendments and evidence history intact until separately authorised maintenance; this audit changes neither.
**Tester:** Extend [mirror parity](../../tests/contract/test_schema_mirror_parity.py#L24),
[amendment-field tests](../../tests/contract/test_audit_record_amend_loop_fields.py#L51) and
[manifest entity tests](../../tests/contract/test_offline_cache_manifest_entity.py#L58) with duplicate-key rejection,
all legacy absent/null combinations, new strict failures, offline pending decisions, contract/model round trips and
all amended mirrors. Assert original serialized legacy rows remain unchanged during migration/replay.
**Future-only validation:** Prepared JSON Schema/Pydantic test environment;
`pytest -q tests/contract/test_schema_mirror_parity.py tests/contract/test_audit_record_amend_loop_fields.py tests/contract/test_offline_cache_manifest_entity.py`.
Expected: one unambiguous schema per version and compatible legacy reads; migration execution needs separate approval.
**Completion:** Models, schemas, producers, consumers and documented invariants agree without destructive backfill.

### P1: Actual Approval Routes Do Not Use the New State and Audit Controls

- [ ] AUD-036-RAG-014 Enforce durable approval transitions and draft-to-final provenance

**Affected:** FR-RAG-LS-01/03, FR-RAG-AG-02, T087, T117, T157, T158, T159, T163, T164,
T165, SC-017; public-warning and override scenarios.
**Expected versus observed:** The [mounted recommendation route](../../apps/api/app/api/routes/recommendations.py#L16)
uses [RecommendationService](../../apps/api/app/services/recommendation_service.py#L18), which directly changes status.
The separate [ApprovalWorkflow](../../apps/api/app/services/approval_workflow.py#L140) is an uncalled in-memory state
helper. Existing Communication approval mechanisms are real, but the new rationale/authority/downgrade record chain is
not supplied by them. [Approval-preservation tests](../../tests/integration/test_human_approval_preserved.py#L30)
manually add an approval dictionary rather than invoking the production decision boundary.
**Developer:** Connect authenticated IC/PIO authority, immutable draft/final IDs, validated rationale and guarded
pending-to-terminal transitions to actual approval/publication routes. Handle concurrency, rejection, edits and incident
downgrades durably; prevent stale or duplicate approvals and ensure offline decisions remain pending on reconnect.
Preserve simulation external-publication blocking and human veto; no RAG result itself grants release authority.
**Tester:** Extend [workflow tests](../../tests/integration/test_approval_workflow_state_machine.py#L26),
[approval preservation](../../tests/integration/test_human_approval_preserved.py#L30) and
[SC-017 assertions](../../tests/contract/test_sc017_override_completeness.py#L111).
Drive mounted routes with authorised approval/rejection, wrong role/tenant, missing rationale, concurrent decisions,
terminal-to-pending retry, changed draft and offline reconnection. Assert actor-bound durable audit of both draft and final.
**Future-only validation:** Prepared API/pytest dependencies with authenticated principal and persistence fixtures;
`pytest -q tests/integration/test_approval_workflow_state_machine.py tests/integration/test_human_approval_preserved.py tests/contract/test_sc017_override_completeness.py`.
Expected: invalid transitions/releases fail before side effects and complete audit fields accompany valid transitions.
**Completion:** The production publication and approval boundaries enforce, not merely describe, human authority.

### P1: Ranking Controls and Reliable Confidence Never Reach Live Retrieval

- [ ] AUD-036-RAG-015 Apply agency and incident-scoped authority ranking before result selection

**Affected:** FR-RAG-AG-04/06, FR-RAG-AC-01, FR-RAG-COMP-04, T060, T065, T071, T075, T103,
T134, T173, T174, T175, T176, T177, T178, T179, T181, T182, T183, T184, T185, T186,
T187, T189, T190, T191, T192, T208, SC-010/013/015; US7/8/10, R-06/16 and A12.
**Expected versus observed:** [Live retrieval](../../apps/agents/common/retrieval_client.py#L746) applies jurisdiction
union and weighted RRF, but the agency, precedence and COMDISPLAN helpers have no production callers in the bounded
application/package search. [Projection](../../apps/agents/common/retrieval_client.py#L293) drops amended metadata;
request shape lacks incident/operator/agency context. The COMDISPLAN flag is process-global. Dictionary deduplication
uses representation rather than stable chunk ID, and batch-relative confidence gives the top weak/metadata hit 1.0.
**Developer:** Preserve all source metadata, carry authoritative incident/hazard/agency/tenant activation scope, and
filter/rank before top-k truncation so primary and handoff doctrine remain available. Apply deterministic recency,
licence, agreed model-version and chunk-ID ties with audit trace; disabling precedence must use recency-only ranking
without silencing. Deduplicate by chunk identity and implement the agreed conservative similarity/coherence/licence
confidence rather than batch-maximum confidence. Invalidate scoped caches on activation/consent changes.
**Tester:** Extend [agency tests](../../tests/contract/test_agency_disambiguation.py#L44),
[authority tests](../../tests/contract/test_authority_precedence.py#L44),
[tie-break tests](../../tests/contract/test_precedence_tiebreak.py#L81) and
[COMDISPLAN tests](../../tests/integration/test_comdisplan_activation.py#L42) through production retrieval.
Use rural/urban NSW, CFA/FRV, DFES combined, NT/QLD, ACT national versus residential and cross-sector handoff fixtures.
Assert positive/negative agencies, both authorities, exact ties, incident-limited activation, flag/cache reversals,
same-ID/different-score fusion and metadata-only confidence cap. Measure the required tagged subsets, not expected labels.
**Future-only validation:** Prepared retrieval dependencies and canonical recorded corpus fixtures;
`pytest -q tests/contract/test_agency_disambiguation.py tests/contract/test_authority_precedence.py tests/contract/test_precedence_tiebreak.py tests/integration/test_comdisplan_activation.py`.
Expected: zero silent conflations in 50 cases and at least 95% measured precision in each required subset.
**Completion:** Real retrieval and its audit/UI metadata enforce jurisdiction, agency and authority meaning deterministically.

### P1: Offline Bundle Production and Signature Verification Are Incomplete

- [ ] AUD-036-RAG-016 Produce and authenticate actual offline payload bytes

**Affected:** FR-RAG-LS-02, FR-RAG-COMP-02, T003, T045, T047, T074, T112, T113, T114,
T129, T136, SC-009; offline integrity and key-rotation obligations.
**Expected versus observed:** [Bundle construction](../../apps/ingest-runner/src/ama_ingest/offline_bundle.py#L137)
creates estimated offsets and placeholder signatures, not the referenced binary payload. Its
[CLI input](../../apps/ingest-runner/src/ama_ingest/offline_bundle_cli.py#L63) requires chunks absent from the ingest
summary. [Workflow signing](../../.github/workflows/corpus-ingest.yml#L203) does not replace embedded placeholders;
age encrypts the manifest rather than authenticating a detached author signature. The
[verifier script](../../infra/scripts/verify-offline-cache.ps1#L114) can warn/skip missing tools or keys and still succeed.
No mounted real-verifier/bundle-download adapter was found.
**Developer:** Serialize bounded actual payloads with accurate offsets and signed canonical hashes; bind manifest,
bundle, tenant and trusted signer identity. Require both specified verification chains and reject missing tools,
keys, signatures or mismatched bytes. Encryption alone is not author authentication. Connect build publication and
device loading without weakening keyless issuer/identity constraints or inventing community approval.
**Tester:** Extend [offline integration](../../tests/integration/test_offline_cache.py#L1) and
[manifest tests](../../tests/contract/test_offline_cache_manifest.py#L46) with producer-to-loader fixtures, real trusted
test signatures, wrong author/tenant/key, tampered body/offset/manifest, missing cosign/age material and actual oversize
payloads. Assert either signature failure prevents all retrieval; missing payload cannot pass a manifest-only check.
**Future-only validation:** Prepared test environment, real signing/verifying tools and offline trusted test materials;
`pytest -q tests/integration/test_offline_cache.py tests/contract/test_offline_cache_manifest.py` after wiring these cases.
No production keys or network are needed for the hermetic verification suite.
**Completion:** The produced downloadable cache is byte-complete and cryptographically authenticated fail-closed.

### P1: Offline Runtime and Reconciliation Do Not Enforce Decision Boundaries

- [ ] AUD-036-RAG-017 Wire bounded offline retrieval and acknowledged reconnect recovery

**Affected:** FR-RAG-LS-02, FR-RAG-AG-02, T112, T129, T130, T131, T132, T158, T165, SC-009; US6.
**Expected versus observed:** [Offline retrieval](../../apps/agents/common/offline_cache.py#L233) takes first matching
jurisdictions, ignores question/topic and does not recheck TTL/classification after load; its default reader is a metadata
stub. No operational fallback or [decision-gate](../../apps/agents/common/offline_cache.py#L428) consumer was found.
[Queue drain](../../apps/agents/common/offline_cache.py#L340) deletes on a non-raising sink return even though the
audit writer swallows failures, and a hung sink can exceed its deadline. The reconnect path lacks sync lag, refresh audit
and IC review; its queue builder excludes some decisions that also require review.
**Developer:** Mount reachability fallback with the real verified body reader from AUD-036-RAG-016; enforce current
TTL, classification, consent and supported topics on every read. Gate actual dispatch for allowed local allocations,
safety escalation and centre setup; forbid warnings, cross-jurisdiction aid and state/national escalation offline.
Queue all required decisions as pending review, retry by stable IDs, delete only after durable acknowledgement, enforce
per-write deadlines and record original timestamps, sync lag and refreshed corpus. Resolve any signed 30-day exception
explicitly with AUD-036-RAG-013 rather than silently overriding the 14-day contract.
**Tester:** Extend [offline tests](../../tests/integration/test_offline_cache.py#L206) and
[Field Coordinator tests](../../tests/integration/test_field_coordinator_offline_boundaries.py#L27): warm service
crossing day 14, unsupported topic, classified request, registry outage, actual body citation, all allowed/forbidden
decisions, reconnect partial failure/restart/duplicate acknowledgement and hung sink. Assert no lost rows or premature
operational release, preserved timestamps, sync lag, IC-pending review and refresh audit.
**Future-only validation:** Prepared pytest with verified fixture bundles, controllable clocks and acknowledged sink;
`pytest -q tests/integration/test_offline_cache.py tests/integration/test_field_coordinator_offline_boundaries.py`.
A later authorised connectivity drill must measure central-store arrival within 60 seconds.
**Completion:** Real degraded operation stays within cached doctrine and authority limits, with durable recoverable reconciliation.

### P1: Conflict Detection and Escalation Are Detached and Unsafe to Wire Unchanged

- [ ] AUD-036-RAG-018 Integrate scoped deterministic conflicts and authenticated human resolution

**Affected:** FR-RAG-COORD-01/02, FR-RAG-LS-01/02, T225, T226, T227, T228, T229, T230,
T231, T250; A12 and all four amended conflict classes.
**Expected versus observed:** The [real aggregation](../../apps/agents/maf_runtime/workflow/builder.py#L142) has no
conflict detector. [Detector inputs](../../apps/api/app/services/conflict_detection.py#L93) lack incident/tenant/hazard
identity; IDs are random, evidence drops inputs, and temporal/severity matching is narrower than the spec.
[Acknowledgement](../../apps/api/app/services/aiims_escalation.py#L122) immediately resolves, accepts unrelated/repeated
choices and checks Field Coordinator authority by a name prefix. Timer/persistence/paging adapters have no mounted callers.
**Developer:** Invoke deterministic post-return rules at the shared aggregation boundary without importing API services
into agents. Validate scoped resources, geometry/time windows, verbs and hazard levels; use replay-stable/idempotent IDs
and persist full evidence plus both recommendation/audit links. Separate acknowledgement from resolution, enforce
authenticated Ops Officer/IC roles, run a durable five-minute unacknowledged timer and queue unreachable offline conflicts
for IC review. Reversible flags must audit changes and never auto-resolve or silence agents.
**Tester:** Extend [conflict tests](../../tests/integration/test_conflict_detection.py#L45) and
[AIIMS tests](../../tests/integration/test_aiims_escalation.py#L58) through aggregation: all four positive classes,
disjoint/adjacent windows, different tenant/incident/hazard, reordered/replayed inputs, warning-versus-withhold,
299/300-second timeout, wrong-role actor, arbitrary accepted IDs, duplicate resolution and full disconnection.
Assert stable evidence, Ops-first then IC escalation, pending offline review and no AI resolution.
**Future-only validation:** Prepared pytest/API/domain dependencies and durable callback/clock fixtures;
`pytest -q tests/integration/test_conflict_detection.py tests/integration/test_aiims_escalation.py`.
Expected: scoped deterministic detection and authorised lifecycle transitions, not isolated positive helper matches.
**Completion:** Actual multi-agent outputs and operator UI/audit records share an enforceable manual conflict lifecycle.

### P1: Simulation Grounding and Citation Publication Can Misrepresent the Answer

- [ ] AUD-036-RAG-019 Validate claim citations before publishing every grounded inference

**Affected:** FR-RAG-AG-03/05, FR-RAG-SIM-01/02/03/04/05/06, T061, T066, T068, T080, T088,
T089, T090, T091, T100, T135, SC-001/007/012; citation mismatch and excluded/no-match edges.
**Expected versus observed:** The [controller request](../../apps/api/app/services/simulation/controller_service.py#L613)
uses process-wide jurisdiction/hazard defaults rather than the simulation's incident context and retrieves only once
before a multi-round tool inference loop. [Output streams immediately](../../apps/api/app/services/simulation/controller_service.py#L692);
later citations are synthesized from retrieved chunks, not validated against claims. The shared
[filter](../../apps/agents/common/citation_filter.py#L63) has no production caller and accepts forged URL/page/snippet
metadata if a valid SHA is reused. A no-match event is emitted only when retrieval was configured; the streamed answer
itself is not forced to decline unsupported doctrine. Audit is optional and only on nonempty retrieval.
**Developer:** Use authenticated simulation incident/hazard/jurisdiction/operator context; ensure every prompt-bearing
inference receives the correct grounded context while preserving agreed index pinning. Canonicalize citations from
retrieved metadata, validate inline references/claim associations before release, suppress hallucinations and apply
the configured confidence policy with audit. Distinguish unavailable, opted-out, excluded and no-match paths visibly;
never attach all retrieved chunks as proof of every model claim. Preserve SSE compatibility, allowlisted tools,
rate limits, simulation watermark/PublicationService blocking and deterministic scripted execution.
**Tester:** Extend [SSE tests](../../tests/integration/test_simulation_sse_citation.py#L1),
[hallucination tests](../../tests/integration/test_hallucinated_citation_suppression.py#L129) and
[controller safety tests](../../tests/unit/test_simulation_controller_safety.py#L1).
Drive the production controller with injected stream/retrieval boundaries, multi-tool rounds, NSW/NT/ACT contexts,
empty/unavailable/excluded queries, inline invented references and valid-SHA/forged-metadata citations. Assert no invalid
reference reaches any event, explicit verification notes, per-call provenance and no external publication.
**Future-only validation:** Prepared pytest/API dependencies and recording streaming adapters;
`pytest -q tests/integration/test_simulation_sse_citation.py tests/integration/test_hallucinated_citation_suppression.py tests/unit/test_simulation_controller_safety.py`.
Expected: all 200 meaningful adversarial inputs exercise the real output path, not a repeated fixed citation pair.
**Completion:** Published citations are authoritative and attributable to the specific grounded response; no-match or failure
cannot masquerade as grounded advice. Model-quality and latency measurements remain separate future evidence.

### P1: Production Model Resolution and the Required Transport Contract Diverge

- [ ] AUD-036-RAG-020 Repair tier resolution and reconcile the Foundry SDK contract

**Affected:** FR-RAG-FM-01/02/03/04/05/06/07, T001, T010, T011, T016, T017, T018, T019,
T020, T021, T027, T028, T058, T146, SC-002; A4 and Session 6.
**Expected versus observed:** [Tier resolution](../../apps/agents/common/llm_config.py#L132) returns a tier alias when
an explicit tier deployment exists, but the [MAF factory](../../apps/agents/maf_runtime/chat_client.py#L71) then looks
that alias up in a model/version CSV. Current Bicep supplies the explicit tier variables, so this configuration can fail
before MAF construction. Several production paths use OpenAI SDKs against Foundry endpoints despite the specified
Inference SDK and limited exceptions; the [lint](../../tests/contract/test_no_openai_imports.py#L74) accepts arbitrary
`AMA-FM04: allow` comments and misses dynamic imports. That is a contract conflict, not proof the endpoint is Azure OpenAI.
The shared [transport](../../apps/agents/common/foundry_chat_client.py#L397) does not enforce its timeout or retain full
tool payloads; MAF/controller do not expose the required callable seam. Metadata/safety/correlation projection is incomplete.
**Developer:** Share a typed resolver across all adapters with explicit deployment precedence and actual model/version
identity. Preserve constructor compatibility and managed identity/audience; reconcile SDK exceptions by explicit
repository authority or implement the required SDK, rather than broadening lint silently. Support sync/async/tool-only
and partial-stream payloads, deadline/error mapping and safety/correlation metadata. Retain template degradation and
historical replay compatibility; do not restore superseded activation canaries or mislabel missing configuration as success.
**Tester:** Extend [model routing](../../tests/contract/test_llm_model_routing.py#L29),
[chat contract](../../tests/contract/test_foundry_chat_client.py#L1) and
[import lint](../../tests/contract/test_no_openai_imports.py#L1) with deployed tier variables, duplicate model keys,
missing deployment, disallowed auth, injected sync/stream callables, tool-only responses, midstream failure, timeout,
actual deployment identity and production-marked/dynamic import fixtures.
**Future-only validation:** Prepared dependencies pinned compatibly with Python 3.12 and existing MAF/OTel constraints;
`pytest -q tests/contract/test_llm_model_routing.py tests/contract/test_foundry_chat_client.py tests/contract/test_no_openai_imports.py`.
Expected: selected configurations construct the intended adapter without legacy fallthrough and contract-negative cases fail.
**Completion:** All three migration anchors obey one explicit, testable SDK/auth/configuration/metadata contract.

### P1: Fresh Deployments and Scheduled Ingestion Are Not Connected End-to-End

- [ ] AUD-036-RAG-023 Connect ingest image delivery, lifecycle hooks and durable completion

**Affected:** FR-RAG-IDX-01/04/05/05a, T002, T040, T050, T052, T053, T055, T056, T136,
T147, T213, T222; US4.2 and A2.
**Expected versus observed:** [azd hooks](../../azure.yaml#L14) invoke database seeds rather than the new Search
job. Selected CD does not publish/start that job's image. [Corpus workflow](../../.github/workflows/corpus-ingest.yml#L17)
is manual-only, uses a different job-name pattern from root parameters, and does not short-circuit no-drift work.
[Job startup](../../scripts/seed_ingest.py#L72) ignores requested mode; its
[live SHA lookup](../../scripts/seed_ingest.py#L139) returns None and revision-stamping failures are ignored.
Service Bus resources/configuration do not establish a mounted completion publisher or consumer.
**Developer:** Wire image build/version publication, selected resource outputs, validated mode arguments, postprovision/CD
invocation, durable execution-correlated completion, SHA propagation and failure-aware revision updates. Restore actual
corpus-push/nightly triggers and no-drift exit; include deletions and metadata changes. Correct timezone handling for
01:00 Australia Eastern including daylight savings. Preserve current database seeds and fail closed on missing corpus
artifacts without deploying a half-wired retrieval stack. Compose consent/conflict/alert dependencies in the selected root,
not only an unused alternate template. Integrate the safety gates in 004/005/007/008/010/011/016.
**Tester:** Extend [ingest contract tests](../../tests/contract/test_ingest_pipeline.py#L1) and
[idempotency tests](../../tests/integration/test_idempotent_ingest.py#L1) with recorded workflow/CLI/provider fixtures:
fresh deploy, warm deploy, malformed/default args, wrong name, job failure/timeout, duplicate/unrelated completion,
missing manifest, SHA mismatch, revision-update failure, no drift and deleted entry. Assert actual mode/name correlation,
failure propagation and no silent zero-SHA activation.
**Future-only validation:** Prepared runner/test dependencies and read-only workflow fixtures;
`pytest -q tests/contract/test_ingest_pipeline.py tests/integration/test_idempotent_ingest.py` after adding lifecycle
coverage. A later explicitly authorised staging azd/CD deployment is prerequisite to claiming automatic ingest delivery.
**Completion:** Both supported deployment paths deliver a measured, gated corpus build and activate only its proven provenance.

### P2: Operator Surfaces Do Not Consume Grounding and Degradation Events

- [ ] AUD-036-RAG-021 Render canonical citations and freshness on mounted operator pages

**Affected:** FR-RAG-AG-03, FR-RAG-AC-01, FR-RAG-SIM-02/03/05, FR-RAG-FRESH-01,
FR-RAG-LS-02, FR-RAG-UI-01, T084, T085, T086, T101, T115, T116, T133, T214,
T239, T240, T241, T242, T243; US1/3/10.
**Expected versus observed:** The [shared card](../../packages/ui/src/components/citation/citation-card.tsx#L120)
has supported keyboard/ARIA work and the [recommendation wrapper](../../apps/web/src/components/recommendations/recommendation-card.tsx#L75)
has a live-region announcement. Neither wrapper nor the freshness component has a production page consumer in the bounded
web-source search. The [SSE event union](../../apps/web/src/lib/api/simulation_chat.ts#L12) omits `citation`, and
[applyEvent](../../apps/web/src/components/simulation-chat-pane.tsx#L484) has no citation branch or stored citation field.
Only a count from subagent tool results is displayed. Existing E2E files target fixture routes/selectors that do not
match the actual card/simulation surface and are skipped without BASE_URL.
**Developer:** Add backward-compatible citation/no-match/degraded/freshness events and persistence to the existing chat
client and mounted pages. Reuse the accessible card; supply canonical page/PDF links, agency/authority labels, tie traces,
conflict notes and actual manifest timestamps. Preserve citations across history reload and transcripts. Handle missing
page/URL, duplicate IDs, metadata-only snippets, zero/suppressed citations and disabled precedence without invented sources.
Keep WCAG SHOULD classification, but do not call an unmounted component an accessible workflow.
**Tester:** Extend [chat-pane unit tests](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L1),
[card keyboard tests](../../apps/web/tests/web/src/components/citation/citation-card.test.tsx#L30), and the existing
[citation E2E](../../tests/e2e/citation_rendering.spec.ts#L23)/[degraded E2E](../../tests/e2e/degraded_mode_badge.spec.ts#L37)
homes. Assert real event consumption/reload/export, handbook and PDF targets, suppressed/missing sources, 7/14-day edges,
offline/unavailable states, keyboard focus and non-colour status; use actual route fixtures rather than fictional pages.
**Future-only validation:** Prepared pnpm dependencies;
`pnpm --filter @ama/web exec vitest run tests/unit/spec_036/simulation-chat-pane.test.tsx tests/web/src/components/citation`.
Later browser tests require corrected discovery, an authorised local/staging server and deterministic route fixtures;
manual screen-reader/contrast review is separately attributable evidence, not performed here.
**Completion:** Actual operator workflows display and preserve validated grounding with accessible degradation and provenance.

### P2: Metrics, Quotas and Freshness Alerts Are Primarily In-Memory Scaffolding

- [ ] AUD-036-RAG-022 Connect real telemetry and policy-driven operational alerts

**Affected:** FR-RAG-OBS-01/02/03, FR-RAG-FRESH-02, FR-RAG-IDX-08, R-09/10, T030, T038,
T041, T078, T099, T132, T135, T212, T215, T216, T232, T233, T234, T235, T236,
T237, T238, SC-012; A12.
**Expected versus observed:** [Telemetry emission](../../apps/agents/common/otel_telemetry.py#L77) records optional
in-memory data but has no production OTel forwarding. Retrieval duration includes other work, swallowed Search errors
miss the counter, and jurisdiction tags tend to name the union's first member. [Ingest instrumentation](../../apps/ingest-runner/src/ama_ingest/__main__.py#L188)
reads nonexistent result counters. [Capacity alert](../../infra/modules/ai-search.bicep#L177) measures SearchLatency against
70 without an action group rather than utilization. Declared per-agent quotas/downgrade thresholds lack runtime readers.
[Freshness emission](../../apps/api/app/services/corpus_freshness.py#L139) has no scheduler/state consumer, no per-build
deduplication and still emits bus alerts while disabled. Workbook/alert modules sit in the alternate graph and the
workbook has three mislabelled SC tiles, not all nineteen.
**Developer:** Use actual OTel tracer/meter instruments and the existing exporter bridge; measure retrieval-only and
inference/end-to-end spans separately with propagated correlation and full request tags. Export correct ingest counters,
size/truncation and configured quota/TTL signals; enforce agreed per-agent budgets without silencing. Mount capacity,
audit-completeness, freshness and latency rules/action groups in the selected graph. Use authoritative global manifest
age/last ingest, deduplicated breach/recovery and audited reversible suppression of both page and bus alert.
**Tester:** Extend [OTel tests](../../tests/integration/test_otel_retrieval_span.py#L73),
[capacity tests](../../tests/integration/test_capacity_alert.py#L57) and
[freshness tests](../../tests/integration/test_corpus_staleness_alert.py#L87) using real in-memory OTel SDK exporters
driven by production retrieval/streaming/ingest. Assert Search failure counters, correlated tags, unequal agent budgets,
70% capacity edges, 500ms sustained/recovery, 14-day/48-hour edges, repeated build assessments and disabled alerts.
**Future-only validation:** Prepared compatible OTel SDK/exporter dependencies and recording alert sinks;
`pytest -q tests/integration/test_otel_retrieval_span.py tests/integration/test_capacity_alert.py tests/integration/test_corpus_staleness_alert.py`.
Expected: real emitted instruments and correct routed/deduplicated alerts; cloud delivery is later separately verified.
**Completion:** Dashboards and alerts consume production signals with defined scopes rather than hardcoded/example values.

### P2: Test Labels and Empty Regression Runners Do Not Prove Acceptance

- [ ] AUD-036-RAG-024 Replace self-confirming fixtures with consumer-level acceptance gates

**Affected:** FR-RAG-TEST-01/02/03/04, FR-RAG-FM-07, FR-RAG-NS-08/09, SC-001 through SC-019;
T006, T010, T015, T029, T031, T032, T033, T035, T036, T038, T060, T065, T066, T067,
T068, T069, T092, T098, T100, T102, T103, T110, T111, T128, T134, T138, T139, T140,
T142, T143, T144, T151, T173, T174, T189, T190, T191, T192, T218, T219, T220, T221,
T222, T223, T224 and the test tasks cross-referenced by the other findings.
**Expected versus observed:** [Golden fixture](../../tests/fixtures/golden-set-v1.json#L6) has 42 entries, zero `tags`,
twenty agency labels and twenty authority labels, only nine ACT/Commonwealth examples, and lacks the required
request/expected-chunk fields. [The regression CLI](../../apps/eval-runner/src/ama_eval/per_agent_canary_gate.py#L228)
supplies no real runners; empty results can compare equal and absent citations can count as fidelity.
[The 200-prompt suite](../../tests/integration/test_hallucinated_citation_suppression.py#L129) ignores prompt content.
[Live blue-green test](../../tests/e2e/test_blue_green_alias_flip.py#L218) is unfinished. The
[load harness](../../tests/load/locustfile.py#L109) targets an unmounted/deferred route, can accept 4xx, randomly reuses
sessions and does not establish sustained 50 RPS; its baseline is empty. Some unit/E2E homes are outside selected CI
discovery. [Opt-out lint](../../tools/lint/check_rag_optout_bindings.py#L57) checks existing markers rather than detecting
new ungrounded calls; [ADR 01](../../docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md#L29)
contradicts required notifier audit emission.
**Developer:** Preserve genuine domain/helper assertions, but inject only external boundaries while testing mounted
orchestration. Require nonempty actual old/new outputs and grounded citation/source-match checks. Author the canonical
50 request-shaped entries with correct agency/ACT subsets and source anchors; eliminate duplicate fixture definitions.
Discover ungrounded calls with reviewed forwarding exceptions and canonical opt-out audit/ADR vocabulary. Restore
per-PR Windows/golden, weekly/pre-promotion load and nightly/pre-release staging lanes; align runner versions and markers.
**Tester:** Reuse [final-gate tests](../../tests/unit/test_spec036_final_canary_gate.py#L1),
[parity-report tests](../../tests/unit/test_spec036_parity_report.py#L1),
[opt-out lint tests](../../tests/contract/test_rag_optout_lint.py#L1), the agency/authority/integration and load homes
already cited. Reject empty/NaN outputs, wrong source sets, fabricated references and missing paths. Assert fifty stable
session IDs, one outstanding request per session, 4xx/5xx failure and measured thresholds; test real OPA rather than a
Python substitute. Synthetic fixtures must be labelled and never stored as live measured baselines.
**Future-only validation:** Prepared Python/pnpm test environments and corrected discovery;
`pytest --collect-only -q tests/contract tests/integration tests/unit tests/e2e` followed by the specific suites above
only after their adapters are hermetic. Live staging/load/equivalence runs require separate authorisation and baseline
inputs. Expected: exact relevant collection, meaningful failures and attributable complete measured artifacts.
**Completion:** Every acceptance gate can fail for the real defect it claims to detect; execution evidence names SHA,
fixture/build/model, environment, command, skips and output. Test authoring itself is not a passing runtime outcome.

### P2: Compliance Export Routes Are Unmounted and Their Data Adapter Is Invalid

- [ ] AUD-036-RAG-026 Mount authorised privacy and PSPF export against real audit records

**Affected:** FR-RAG-COMP-01/03, FR-RAG-AG-02, T204, T205, T206, T207, SC-018; APP and export checklist obligations.
**Expected versus observed:** [API composition](../../apps/api/app/api/router.py#L56) omits the compliance router.
Its [adapter](../../apps/api/app/api/routes/audit_compliance.py#L68) imports/calls absent repository interfaces and
turns errors into empty successful responses. Handlers lack explicit tenant/subject role checks. The
[CSV mapping](../../apps/api/app/api/routes/audit_compliance.py#L132) does not use actual `timestamp_utc`, approval,
override/downgrade or gateway fields. APP labels are not PII consent/anonymisation controls. Since routes are unmounted,
this is not a demonstrated exposed endpoint or data leak.
**Developer:** Integrate an authorised tenant/subject-bounded audit read interface, correct timestamp/outcome/justification
mapping, pagination/streaming and explicit unavailable failures. Enforce SAR identity/observer permissions before mount;
validate date limits and classification, minimise PII before durable writes and protect export access. Preserve the six
ordered PSPF columns and RFC 4180 escaping. Qualified privacy/ISM sign-off remains human work under 005/025.
**Tester:** Extend [SAR tests](../../tests/contract/test_privacy_act_sar.py#L29) and
[PSPF tests](../../tests/contract/test_pspf_audit_export.py#L27) through the actual router with stored audit fixtures:
authorised subject, 401/403, cross-tenant/subject denial, unavailable repository, date-boundary/large export, Unicode,
quotes/newlines/formula-like content and legacy-null fields. Assert correct real-data columns and no free-text PII leakage.
**Future-only validation:** Prepared API/pytest dependencies and principal/persistence fixtures;
`pytest -q tests/contract/test_privacy_act_sar.py tests/contract/test_pspf_audit_export.py`.
Expected: valid authorised CSV/SAR content, denied unauthorised access and non-success on repository failure.
**Completion:** Mounted routes deliver faithful, bounded, protected audit data rather than empty scaffold responses.

### P2: Authored Closure and Persona Evidence Overstate Completion

- [ ] AUD-036-RAG-025 Reconcile traceability and collect attributable acceptance evidence

**Affected:** T006, T027, T051, T093, T094, T095, T096, T097, T098, T101, T102, T103,
T137, T138, T139, T140, T141, T145, T146, T147, T148, T149, T150, T188, T202,
T203, T209, T210, T217, T223, T243, T244, T245, T246, T247, T248, T249, T250, T251;
all outcome SCs, A9/11, OOS-8 and 342 review/checklist obligations.
**Expected versus observed:** [Historical quickstart](quickstart-validation.md#L3) is a stub walk at another revision
with deferred live steps and excluded collection errors, not verification of this SHA. [Analysis](analyze-report.md#L29)
mislabels several SCs; [checklist index](checklists/README.md#L6) says 339 rather than 342. Persona traceability includes
undefined FR references and changed task meanings; original consultation memos are not available in the bounded search.
[Handoff](HANDOFF.md#L9) names different federal authorities from T210/T247. The four external tasks remain `[~]`;
an ADR body, automated reviewer label or placeholder identity is not a signed human decision.
**Developer:** After separately authorised changes, reconcile current counts, stable references, hard-cutover scope,
gate/confidence/TTL/retention conflicts and provenance terminology without retroactively claiming execution. Preserve
the original task states and all supported source work. Locate/version original persona/review inputs or explicitly
record their absence; resolve the forty local concerns and additional precision/accessibility asks. Establish evidence
ownership for deployments, first-ingest sizing, model results, performance, replay, game days, accessibility and human
community/federal sign-off. Never synthesize approval or rename fake results as live evidence.
**Tester:** Reuse [replay fidelity](../../tests/contract/test_audit_replay_fidelity.py#L1),
[final canary gate](../../tests/unit/test_spec036_final_canary_gate.py#L1) and the cited UI/load/integration homes.
Review fixture/build/model attribution, real command output, dates, skips, exclusions and genuine authority signatures.
Reject missing source memos, mismatched SHA, empty measurements and unapproved publications as completed acceptance.
**Future-only validation:** Read-only ID/link/schema checks may precede any execution. In a prepared environment,
`pytest -q tests/contract/test_audit_replay_fidelity.py tests/unit/test_spec036_final_canary_gate.py` is only a source-test
gate; separately authorised recorded deployments, model/retrieval evaluations, monthly/quarterly drills, 48-hour
post-incident replay and qualified human reviews are prerequisite to outcome completion.
**Completion:** Every closure claim is bounded and attributable; unresolved external approvals, unavailable inputs and
unmeasured SCs remain explicitly UNVERIFIED rather than being auto-ticked.

## Original Task Coverage

There are 241 task definitions: 229 originally `[X]` and 12 `[~]`. Checked X/x is equivalent below.
No definition has an unchecked or absent checkbox, and no task suffix occurs in this source; parsing still accepts suffixes.
Dependency notes and cross-reference repetitions are not definitions. The ten undefined numbers are T007, T008, T009,
T059, T104, T105, T106, T107, T108 and T109; no rows are invented for them.
IMPLEMENTED test/document rows mean the stated assertions/artifact are authored, never that they ran or were approved.
SUPERSEDED canary rows apply only to activation sequencing explicitly retired by ADR 20; retained regression, inclusion,
audit and no-silencing obligations remain assigned to the listed follow-ups.

### Phases 0 Through E

| Original task | Original state | Status | Evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | PARTIAL | [Agent dependencies](../../apps/agents/pyproject.toml#L1) and [API dependencies](../../apps/api/pyproject.toml#L1) differ from required Presidio/minor pins; lock execution unverified. | AUD-036-RAG-020 |
| T002 | [x] | PARTIAL | [Runner package](../../apps/ingest-runner/pyproject.toml#L1) exists; [root metadata](../../pyproject.toml#L1) lacks requested workspace integration; delivery incomplete. | AUD-036-RAG-023 |
| T003 | [x] | PARTIAL | [CI setup](../../.github/workflows/ci.yml#L45) installs age; named devcontainer/setup-action homes absent after inventory search. | AUD-036-RAG-016 |
| T004 | [x] | IMPLEMENTED | [Domain re-exports](../../packages/domain/src/ama_domain/__init__.py#L23) and retrieval/citation/cache modules exist. | - |
| T005 | [x] | IMPLEMENTED | [Parity assertions](../../tests/contract/test_schema_mirror_parity.py#L24); seven declared raw mirrors are byte-identical. Semantic defects are separate. | AUD-036-RAG-013 |
| T006 | [x] | UNVERIFIED | [Spec stanza](../../.github/agents/copilot-instructions.md#L60) exists; historical generator invocation/commit not attributable from this text. | AUD-036-RAG-025 |
| T010 | [x] | PARTIAL | [Protocol tests](../../tests/contract/test_foundry_chat_client.py#L1) do not enforce all three injectable constructors or complete stream contract. | AUD-036-RAG-020 |
| T011 | [x] | CONFLICT | [Import lint](../../tests/contract/test_no_openai_imports.py#L74) widens production exemptions and misses dynamic imports. | AUD-036-RAG-020 |
| T012 | [x] | PARTIAL | [Registry tests](../../tests/contract/test_carveout_registry_entry.py#L47) omit effective prod environment/quorum assertions. | AUD-036-RAG-005 |
| T013 | [x] | PARTIAL | [Enforcement tests](../../tests/integration/test_carveout_enforcement.py#L1) use weak/confounded expiry and limited residency fixtures. | AUD-036-RAG-005 |
| T014 | [x] | PARTIAL | [Gateway tests](../../tests/integration/test_data_minimisation_gateway.py#L30) exercise helper text, not full envelope/history/response transit. | AUD-036-RAG-001 |
| T015 | [x] | PARTIAL | [Equivalence harness](../../tests/integration/test_fr023_per_agent_gate.py#L1) uses supplied outputs; real regression CLI defaults empty runners. | AUD-036-RAG-024 |
| T016 | [x] | IMPLEMENTED | [Shared contract](../../apps/agents/common/foundry_chat_client.py#L1) defines frozen response/delta types, aliases and runtime-checkable protocol. | - |
| T017 | [x] | PARTIAL | [Live wrapper](../../apps/agents/common/foundry_chat_client.py#L397) provides SDK/AAD paths but lacks enforced deadline/full payload and explicit token-cache contract. | AUD-036-RAG-020 |
| T018 | [x] | PARTIAL | [LLM client](../../apps/agents/common/llm_client.py#L193) has callable injection/Foundry selection; metadata and grounded composition remain incomplete. | AUD-036-RAG-002, AUD-036-RAG-020 |
| T019 | [x] | PARTIAL | [MAF factory](../../apps/agents/maf_runtime/chat_client.py#L71) retains signature but has resolver disagreement and no required shared seam. | AUD-036-RAG-020 |
| T020 | [x] | CONFLICT | [Controller transport](../../apps/api/app/services/simulation/controller_service.py#L482) uses AsyncAzureOpenAI against Foundry, not the specified injected Inference SDK seam. | AUD-036-RAG-020 |
| T021 | [x] | PARTIAL | [Configuration](../../apps/agents/common/llm_config.py#L132) exists as dataclass/CSV logic, not requested Settings; consumers disagree on tier aliases. | AUD-036-RAG-020 |
| T022 | [x] | PARTIAL | [Gateway helper](../../apps/agents/common/model_gateway.py#L1) handles markings/PII but not the complete safe-topic/default-deny and audited envelope policy. | AUD-036-RAG-001 |
| T023 | [x] | PARTIAL | [Gateway invocation](../../apps/agents/common/foundry_chat_client.py#L362) bypasses unknown policy and uncovered payload roles/adapters. | AUD-036-RAG-001 |
| T024 | [x] | PARTIAL | [Verifier](../../scripts/verify-carveout.ps1#L89) has expiry, effective-coordinate and residency coverage gaps. | AUD-036-RAG-005 |
| T025 | [x] | PARTIAL | [OPA rules](../../infra/policy/rego/foundry_carveout.rego#L49) exist but use optional row environment and are not active CD policy evaluation. | AUD-036-RAG-005 |
| T026 | [x] | PARTIAL | [Pre-provision step](../../.github/workflows/cd.yml#L211) exists without required plan/environment/OPA inputs. | AUD-036-RAG-005 |
| T027 | [x] | CONFLICT | [Registry](../../infra/parameters/foundry-carveout.yaml#L21) has older model rows/two approvers versus current GPT-5.4 and prod quorum. | AUD-036-RAG-005 |
| T028 | [x] | PARTIAL | [Facade flags](../../apps/agents/maf_runtime/agents/_factory.py#L196) exist; actual dispatch does not enforce grounding or disable provenance. | AUD-036-RAG-002 |
| T029 | [x] | PARTIAL | [CLI](../../apps/eval-runner/src/ama_eval/per_agent_canary_gate.py#L228) compares empty default runners and accepts empty fixtures. | AUD-036-RAG-024 |
| T030 | [x] | PARTIAL | [Cutover alerts](../../infra/bicep/modules/foundry-rag-cutover-alerts.bicep#L1) are authored; required table/production signal/consumer evidence is incomplete. | AUD-036-RAG-022 |
| T031 | [x] | PARTIAL | [Ingest contract tests](../../tests/contract/test_ingest_pipeline.py#L81) prove helper constants/write skipping, not pre-embedding idempotency/full provenance. | AUD-036-RAG-007, AUD-036-RAG-011 |
| T032 | [x] | PARTIAL | [Warm-run test](../../tests/integration/test_idempotent_ingest.py#L113) allows re-embedding and relaxes timing beyond 10%. | AUD-036-RAG-007 |
| T033 | [x] | PARTIAL | [Alias tests](../../tests/integration/test_blue_green_alias_flip.py#L53) inject model/alias state and do not prove live retention/provider behavior. | AUD-036-RAG-007, AUD-036-RAG-009 |
| T034 | [x] | IMPLEMENTED | [Four synthetic gate failures](../../tests/integration/test_blue_green_parity_gate_fail.py#L100) assert aborted promotion; real inputs remain a separate gap. | AUD-036-RAG-008 |
| T035 | [x] | PARTIAL | [Source validation](../../tests/integration/test_corpus_entry_validation.py#L65) enumerates real records but permits absent mode/empty URLs. | AUD-036-RAG-006 |
| T036 | [x] | PARTIAL | [Chunk tests](../../tests/integration/test_chunk_index_invariants.py#L113) omit retrieved-at and amended metadata enforcement. | AUD-036-RAG-011 |
| T037 | [x] | PARTIAL | [Mode fixtures](../../tests/integration/test_licence_mode_partition.py#L83) cover fresh partitioning, not revocation/downgrade residue. | AUD-036-RAG-006 |
| T038 | [x] | PARTIAL | [Capacity tests](../../tests/integration/test_capacity_alert.py#L57) exercise helper thresholds, not the deployed alert metric/action group. | AUD-036-RAG-022 |
| T039 | [x] | PARTIAL | [Inventory lint tests](../../tests/integration/test_indexing_licence_inventory_lint.py#L1) do not enforce all rights/provenance column drift. | AUD-036-RAG-006 |
| T040 | [x] | PARTIAL | [CLI](../../apps/ingest-runner/src/ama_ingest/__main__.py#L124) exists; argument/default-provider/build-SHA and delivery contracts diverge. | AUD-036-RAG-007, AUD-036-RAG-023 |
| T041 | [x] | PARTIAL | [Chunk splitting](../../apps/ingest-runner/src/ama_ingest/chunker.py#L360) is not a hard token/atomic-block guarantee; statistics are local. | AUD-036-RAG-011, AUD-036-RAG-022 |
| T042 | [x] | CONFLICT | [Embedder](../../apps/ingest-runner/src/ama_ingest/embedder.py#L217) has MI/retries/dimension checks but uses AzureOpenAI rather than the bound SDK. | AUD-036-RAG-020 |
| T043 | [x] | CONFLICT | [Mode filter](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L38) defaults missing rights to full-text; existing exclusions remain indexed. | AUD-036-RAG-006 |
| T044 | [x] | PARTIAL | [Indexer](../../apps/ingest-runner/src/ama_ingest/indexer.py#L280) writes/skips chunks but does not enforce full lifecycle/state/reconciliation. | AUD-036-RAG-006, AUD-036-RAG-007, AUD-036-RAG-008 |
| T045 | [x] | PARTIAL | [Manifest](../../apps/ingest-runner/src/ama_ingest/manifest.py#L79) has deterministic hashing without agreed frozen identity and mounted signing chain. | AUD-036-RAG-011, AUD-036-RAG-016 |
| T046 | [x] | PARTIAL | [Gate inputs](../../apps/ingest-runner/src/ama_ingest/__main__.py#L439) substitute constants for measured parity and do not publish durable completion. | AUD-036-RAG-008, AUD-036-RAG-023 |
| T047 | [x] | PARTIAL | [Bundle builder](../../apps/ingest-runner/src/ama_ingest/offline_bundle.py#L137) emits manifest/estimated offsets, not authenticated payload bytes. | AUD-036-RAG-016 |
| T048 | [x] | PARTIAL | [Wrapper](../../infra/modules/ai-search-blue-green.bicep#L113) reuses Search; name-based readiness is not lifecycle/parity enforcement. | AUD-036-RAG-004, AUD-036-RAG-008 |
| T049 | [x] | PARTIAL | [Search module](../../infra/modules/ai-search.bicep#L177) has parameters but wrong capacity metric and no notification wiring. | AUD-036-RAG-004, AUD-036-RAG-022 |
| T050 | [x] | PARTIAL | [Job composition](../../infra/main.bicep#L321) supplies resources/identity; active image, durable sinks and completion flow are incomplete. | AUD-036-RAG-023 |
| T051 | [x] | CONFLICT | [Root Search call](../../infra/main.bicep#L302) enables public access and passes empty private networking. No live posture was queried. | AUD-036-RAG-004 |
| T052 | [x] | PARTIAL | [Seed runner](../../scripts/seed_ingest.py#L72) starts/polls but ignores mode and cannot retrieve live SHA. | AUD-036-RAG-023 |
| T053 | [x] | PARTIAL | [Workflow](../../.github/workflows/corpus-ingest.yml#L17) is manual-only with job-name/artifact-transfer gaps. | AUD-036-RAG-023 |
| T054 | [x] | PARTIAL | [Inventory](../../docs/corpus/INDEXING-LICENCE-INVENTORY.md#L5) covers current entries but lacks required publisher/edition/verification information. | AUD-036-RAG-006 |
| T055 | [x] | IMPLEMENTED | [PR inventory step](../../.github/workflows/ci.yml#L63) is binding; T039 owns the weaker lint semantics. | - |
| T056 | [x] | MISSING | [CLI audit defaults](../../apps/ingest-runner/src/ama_ingest/__main__.py#L335) are in-memory aggregate; no durable per-call Cosmos/archive sink in runner/provider search. | AUD-036-RAG-012 |
| T057 | [x] | PARTIAL | [Python preflight](../../apps/ingest-runner/src/ama_ingest/carveout_preflight.py#L103) runs but lacks effective prod quorum and complete transit policy. | AUD-036-RAG-005 |
| T058 | [x] | CONFLICT | [Named module](../../infra/modules/azure-openai.bicep#L4) is now canonical Foundry composition, not the requested deprecated legacy artifact; reconcile explicitly. | AUD-036-RAG-020, AUD-036-RAG-025 |
| T060 | [x] | PARTIAL | [Retrieval tests](../../tests/contract/test_retrieval_service.py#L1) check fake semantics/constants rather than full real hybrid/pinning chain. | AUD-036-RAG-009, AUD-036-RAG-015 |
| T061 | [x] | IMPLEMENTED | [Citation-envelope assertions](../../tests/contract/test_citation_envelope.py#L57) cover schema and round-trip shape. | - |
| T062 | [x] | IMPLEMENTED | [Audit assertions](../../tests/contract/test_audit_record_shape.py#L150) cover original grounded/opt-out/embedding/deny shapes; amended conflicts are separate. | AUD-036-RAG-013 |
| T063 | [x] | IMPLEMENTED | [Request/result tests](../../tests/contract/test_retrieval_request_response.py#L20) assert round trips, jurisdiction minimum, top-k and classification ceiling. | - |
| T064 | [x] | IMPLEMENTED | [Citation entity tests](../../tests/contract/test_citation_entity.py#L46) assert confidence/licence/URL/hash constraints. | - |
| T065 | [x] | PARTIAL | [Fifty generated cases](../../tests/integration/test_jurisdiction_disambiguation.py#L55) test fake jurisdiction labels, not real agency/border retrieval. | AUD-036-RAG-015, AUD-036-RAG-024 |
| T066 | [x] | PARTIAL | [Adversarial suite](../../tests/integration/test_hallucinated_citation_suppression.py#L129) repeats a fixed citation pair independent of prompt. | AUD-036-RAG-019, AUD-036-RAG-024 |
| T067 | [x] | PARTIAL | [Inclusion tests](../../tests/integration/test_communication_agent_atsi_cald.py#L78) preload topic-labelled fake chunks instead of driving drafting helper. | AUD-036-RAG-002 |
| T068 | [x] | PARTIAL | [SSE tests](../../tests/integration/test_simulation_sse_citation.py#L1) do not establish mounted streaming/tenant/approval/latency acceptance. | AUD-036-RAG-019, AUD-036-RAG-024 |
| T069 | [x] | PARTIAL | [Replay checks](../../tests/integration/test_audit_replay.py#L95) compare synthetic hashes, not one-month historical retrieval inputs. | AUD-036-RAG-012, AUD-036-RAG-025 |
| T070 | [x] | PARTIAL | [Ceiling tests](../../tests/integration/test_classification_ceiling.py#L55) use attribute fakes, not classification propagation through real inference. | AUD-036-RAG-001 |
| T071 | [x] | PARTIAL | [Request model](../../packages/domain/src/ama_domain/retrieval.py#L113) supports base fields but lacks amended agency/consent/incident context. | AUD-036-RAG-003, AUD-036-RAG-015 |
| T072 | [x] | IMPLEMENTED | [Citation model](../../packages/domain/src/ama_domain/citation.py#L21) implements the original typed licence/confidence contract. | - |
| T073 | [x] | PARTIAL | [Audit model](../../packages/domain/src/ama_domain/audit_record.py#L182) has base fields but violates additive legacy/offline semantics. | AUD-036-RAG-013 |
| T074 | [x] | IMPLEMENTED | [Offline manifest model](../../packages/domain/src/ama_domain/offline_cache.py#L50) has original signature fields and bounds; cryptography is separate. | - |
| T075 | [x] | PARTIAL | [Live retrieval](../../apps/agents/common/retrieval_client.py#L746) has async Search/query embedding/RRF but incorrect provenance, ranking and failure semantics. | AUD-036-RAG-009, AUD-036-RAG-015 |
| T076 | [x] | IMPLEMENTED | [Retrieval filters](../../apps/agents/common/retrieval_client.py#L746) union own jurisdiction with national/AIDR for both arms. | - |
| T077 | [x] | IMPLEMENTED | [Retrieval guard](../../apps/agents/common/retrieval_client.py#L746) rejects non-OFFICIAL request attributes before search; envelope transit is separate. | - |
| T078 | [x] | PARTIAL | [Quota YAML](../../infra/parameters/foundry-agent-quotas.yaml#L25) lacks runtime consumer/token-rate instrument; fixed QPS is not the declared budget. | AUD-036-RAG-022 |
| T079 | [x] | PARTIAL | [LRU key](../../apps/agents/common/retrieval_client.py#L757) omits result-affecting context and relabels old provenance. | AUD-036-RAG-009 |
| T080 | [x] | PARTIAL | [SHA filter](../../apps/agents/common/citation_filter.py#L63) is detached and accepts forged metadata with a valid SHA. | AUD-036-RAG-019 |
| T081 | [x] | PARTIAL | [Writer](../../apps/agents/common/audit.py#L103) lacks mounted complete per-call/acknowledged archive integrity path. | AUD-036-RAG-012 |
| T082 | [x] | PARTIAL | [Migration script](../../infra/scripts/migrate-audit-record-036.ps1#L100) avoids row rewrite but best-effort policy update/default database do not establish live migration. | AUD-036-RAG-013 |
| T083 | [x] | PARTIAL | [Facade run](../../apps/agents/maf_runtime/agents/_factory.py#L265) does not consume its injected retrieval/audit dependencies. | AUD-036-RAG-002 |
| T084 | [x] | IMPLEMENTED | [Relocated shared card](../../packages/ui/src/components/citation/citation-card.tsx#L70) renders source links/licence-aware quote, confidence and ARIA. | AUD-036-RAG-021 |
| T085 | [x] | IMPLEMENTED | [Shared badge](../../packages/ui/src/components/citation/degraded-mode-badge.tsx#L1) supplies the requested initial UI scaffold. | - |
| T086 | [x] | PARTIAL | [Recommendation wrapper](../../apps/web/src/components/recommendations/recommendation-card.tsx#L40) composes card/badge but has no mounted page caller. | AUD-036-RAG-021 |
| T087 | [x] | PARTIAL | [Inclusion helper](../../apps/agents/communication/grounding.py#L83) is uncalled and sends invalid request fields before drafting. | AUD-036-RAG-002 |
| T088 | [x] | IMPLEMENTED | [SSE marshalling](../../apps/api/app/services/simulation/citation_sse.py#L1) authors citation and empty-result event formatting. | - |
| T089 | [x] | PARTIAL | [Controller retrieval](../../apps/api/app/services/simulation/controller_service.py#L613) uses environment context and does not enforce all-round grounding/no-match output. | AUD-036-RAG-019 |
| T090 | [x] | PARTIAL | [Audit branch](../../apps/api/app/services/simulation/controller_service.py#L873) is optional, nonempty-only and not injected by mounted route. | AUD-036-RAG-012 |
| T091 | [x] | PARTIAL | [Warp scheduler](../../apps/api/app/services/warp_scheduler.py#L130) is deterministic; marker/audit is instead prose on offline chat, not scripted dispatch. | AUD-036-RAG-019, AUD-036-RAG-024 |
| T092 | [x] | PARTIAL | [Agent fixture](../../apps/eval-runner/fixtures/spec036/monitoring.jsonl#L1) and sibling files are authored; no actual measured baseline/candidate runners are supplied. | AUD-036-RAG-024 |
| T093 | [~] | SUPERSEDED | [ADR 20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L29) retires Monitoring activation; regression/fallback evidence remains required. | AUD-036-RAG-002, AUD-036-RAG-024 |
| T094 | [~] | SUPERSEDED | [Session 6](spec.md#L98) retires Risk activation; it does not attest a rollback drill or equivalence result. | AUD-036-RAG-002, AUD-036-RAG-024 |
| T095 | [~] | SUPERSEDED | [Session 6](spec.md#L98) retires Evacuation activation; no-silencing/regression obligations remain. | AUD-036-RAG-002, AUD-036-RAG-024 |
| T096 | [~] | SUPERSEDED | [Session 6](spec.md#L98) retires Resource activation; no-silencing/regression obligations remain. | AUD-036-RAG-002, AUD-036-RAG-024 |
| T097 | [~] | SUPERSEDED | [Session 6](spec.md#L98) retires Communication activation only; inclusion/fallback assertions remain incomplete. | AUD-036-RAG-002, AUD-036-RAG-024 |
| T098 | [x] | PARTIAL | [Parity report tests](../../tests/unit/test_spec036_parity_report.py#L1) exist; automated real comparisons and biweekly human review are not demonstrated. | AUD-036-RAG-024, AUD-036-RAG-025 |
| T099 | [x] | PARTIAL | [Completeness KQL](../../tests/audit/audit_trail_completeness.kql#L17) is authored, but timestamp/table/alert producer linkage is incomplete. | AUD-036-RAG-012, AUD-036-RAG-022 |
| T100 | [x] | PARTIAL | [Final gate](../../apps/eval-runner/src/ama_eval/per_agent_canary_gate.py#L283) has fidelity thresholds but empty evidence can pass; live attribution absent. | AUD-036-RAG-024 |
| T101 | [x] | UNVERIFIED | [Accessibility baseline](../../docs/accessibility/spec-036-citation-card-baseline.md#L22) is authored; WAVE/screen-reader pre-GA review and gate are not established. | AUD-036-RAG-021, AUD-036-RAG-025 |
| T102 | [x] | UNVERIFIED | [Replay test](../../tests/integration/test_audit_replay.py#L95) is synthetic; no attributable DPE operator 60-second reconstruction evidence. | AUD-036-RAG-012, AUD-036-RAG-025 |
| T103 | [x] | PARTIAL | [DFES case](../../tests/integration/test_jurisdiction_disambiguation.py#L118) excludes other jurisdictions in a fake, not actual single-agency doctrine conflation. | AUD-036-RAG-015 |
| T110 | [x] | PARTIAL | [Binding lint](../../tools/lint/check_rag_optout_bindings.py#L57) validates present markers only, missing undeclared inference calls. | AUD-036-RAG-024 |
| T111 | [x] | IMPLEMENTED | [ADR structure tests](../../tests/contract/test_rag_optout_adr.py#L59) assert original required sections; human approval/content correctness is separate. | - |
| T112 | [x] | PARTIAL | [Offline tests](../../tests/integration/test_offline_cache.py#L206) use boolean signatures/list drain, not authentic production fallback/recovery. | AUD-036-RAG-016, AUD-036-RAG-017 |
| T113 | [x] | IMPLEMENTED | [Manifest schema tests](../../tests/contract/test_offline_cache_manifest.py#L46) assert original shape/bounds/signature presence. | - |
| T114 | [x] | IMPLEMENTED | [Manifest entity tests](../../tests/contract/test_offline_cache_manifest_entity.py#L58) cover round trip/immutability/invalid input. | - |
| T115 | [x] | PARTIAL | [Citation E2E](../../tests/e2e/citation_rendering.spec.ts#L23) targets unmatched fixtures/selectors and skips without BASE_URL. | AUD-036-RAG-021 |
| T116 | [x] | PARTIAL | [Badge E2E](../../tests/e2e/degraded_mode_badge.spec.ts#L37) likewise does not exercise actual mounted degraded workflows. | AUD-036-RAG-021 |
| T117 | [x] | PARTIAL | [Approval test](../../tests/integration/test_human_approval_preserved.py#L30) manually adds approval data instead of enforcing production transitions. | AUD-036-RAG-014 |
| T118 | [x] | CONFLICT | [Notifier ADR](../../docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md#L29) explicitly omits mandatory opt-out audit. | AUD-036-RAG-024 |
| T119 | [x] | IMPLEMENTED | [BoM ADR](../../docs/decisions/036-foundry-rag-grounding/02-rag-optout-bom-live.md#L24) body/rationale exists; live audit behavior assessed separately. | - |
| T120 | [x] | IMPLEMENTED | [GA ADR](../../docs/decisions/036-foundry-rag-grounding/03-rag-optout-ga-live.md#L23) body exists; operational outcomes unverified. | - |
| T121 | [x] | IMPLEMENTED | [Planning ADR](../../docs/decisions/036-foundry-rag-grounding/04-rag-optout-planning-collection.md#L23) authors collection/analysis separation. | - |
| T122 | [x] | IMPLEMENTED | [Logistics ADR](../../docs/decisions/036-foundry-rag-grounding/05-rag-optout-logistics-transactional.md#L24) authors deterministic transactional boundary. | - |
| T123 | [x] | IMPLEMENTED | [Scenario ADR](../../docs/decisions/036-foundry-rag-grounding/06-rag-optout-scenario-execution.md#L26) authors scripted-versus-chat distinction. | - |
| T124 | [x] | CONFLICT | [Classified ADR](../../docs/decisions/036-foundry-rag-grounding/07-rag-optout-classified.md#L32) audit vocabulary disagrees with canonical contract. | AUD-036-RAG-013, AUD-036-RAG-024 |
| T125 | [x] | PARTIAL | [Lint ADR](../../docs/decisions/036-foundry-rag-grounding/08-rag-optout-ci-lint.md#L15) describes structural checks, not complete non-grounded-call detection. | AUD-036-RAG-024 |
| T126 | [x] | CONFLICT | [Observer ADR](../../docs/decisions/036-foundry-rag-grounding/09-rag-optout-observer-auditor.md#L23) reason differs from required observer-auditor-replay. | AUD-036-RAG-013, AUD-036-RAG-024 |
| T127 | [x] | CONFLICT | [Marker lint](../../tools/lint/check_rag_optout_bindings.py#L57) and marker-optional ADR disagree with mandatory call-site/audit coverage. | AUD-036-RAG-024 |
| T128 | [x] | IMPLEMENTED | [CI lint lane](../../.github/workflows/ci.yml#L63) binds the existing opt-out checker; checker insufficiency is T110. | AUD-036-RAG-024 |
| T129 | [x] | PARTIAL | [Cache loader](../../apps/agents/common/offline_cache.py#L171) validates callback outcomes, not a mounted authentic signature/content chain. | AUD-036-RAG-016 |
| T130 | [x] | PARTIAL | [Offline service](../../apps/agents/common/offline_cache.py#L233) lacks real fallback consumer, topic/TTL/classification enforcement. | AUD-036-RAG-017 |
| T131 | [x] | PARTIAL | [SQLite drain](../../apps/agents/common/offline_cache.py#L340) is persistent locally but lacks durable ack/reconnect/refresh guarantees. | AUD-036-RAG-017 |
| T132 | [x] | PARTIAL | [TTL helper](../../apps/agents/common/offline_cache.py#L391) lacks connected gauge/alert and signed 30-day override semantics. | AUD-036-RAG-013, AUD-036-RAG-022 |
| T133 | [x] | PARTIAL | [Badge implementation](../../packages/ui/src/components/citation/degraded-mode-badge.tsx#L1) exists without real operator state/consumer integration. | AUD-036-RAG-021 |
| T134 | [x] | PARTIAL | [Inline 50-case suite](../../tests/integration/test_jurisdiction_disambiguation.py#L55) persists alongside incomplete canonical fixture and does not test doctrine. | AUD-036-RAG-015, AUD-036-RAG-024 |
| T135 | [x] | PARTIAL | [Per-agent thresholds](../../infra/parameters/foundry-agent-quotas.yaml#L25) are authored but not consumed by the production citation filter. | AUD-036-RAG-019, AUD-036-RAG-022 |
| T136 | [x] | PARTIAL | [Bundle workflow](../../.github/workflows/corpus-ingest.yml#L203) lacks compatible manifest, bytes, signature binding and Blob publication. | AUD-036-RAG-016, AUD-036-RAG-023 |
| T137 | [x] | PARTIAL | [Forty concern map](persona-traceability.md#L17) exists but original memos are absent and several mappings/IDs are incorrect. | AUD-036-RAG-025 |
| T138 | [x] | UNVERIFIED | [Game-day runbook](../../docs/runbooks/036-foundry-rag-gameday.md#L1) is not attributable execution under load/failure. | AUD-036-RAG-025 |
| T139 | [x] | UNVERIFIED | [Runbook](../../docs/runbooks/036-foundry-rag-gameday.md#L1) and helper tests do not establish an actual offline TTL game day. | AUD-036-RAG-025 |
| T140 | [x] | UNVERIFIED | [Game-day procedure](../../docs/runbooks/036-foundry-rag-gameday.md#L1) is authored; cascade/no-silencing regression exercise remains unproved after activation supersession. | AUD-036-RAG-024, AUD-036-RAG-025 |
| T141 | [x] | IMPLEMENTED | [Runbook body](../../docs/runbooks/036-foundry-rag-gameday.md#L1) covers the drill/replay procedures; performance of them is separate. | AUD-036-RAG-025 |
| T142 | [x] | PARTIAL | [Final gate](../../apps/eval-runner/src/ama_eval/per_agent_canary_gate.py#L283) implements metrics but permits empty pairs and lacks actual production evidence. | AUD-036-RAG-024 |
| T143 | [x] | IMPLEMENTED | [Equivalence entity tests](../../tests/contract/test_equivalence_test_result.py#L1) cover added fidelity/source/build/model fields. | - |
| T144 | [x] | PARTIAL | [Fidelity KQL](../../tests/audit/audit_replay_fidelity.kql#L1) and [synthetic tests](../../tests/contract/test_audit_replay_fidelity.py#L1) do not establish sampled real replay/alerting. | AUD-036-RAG-012, AUD-036-RAG-025 |
| T145 | [~] | SUPERSEDED | [ADR 20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L29) retires final Simulation activation; SSE/regression/drill obligations remain. | AUD-036-RAG-019, AUD-036-RAG-024 |
| T146 | [~] | CONFLICT | [Import exceptions](../../tests/contract/test_no_openai_imports.py#L74) remain; ADR 20 changes coupling/cleanup timing, not the SDK requirement by itself. | AUD-036-RAG-020, AUD-036-RAG-025 |
| T147 | [~] | UNVERIFIED | [Step-9 runbook](../../docs/runbooks/036-foundry-rag-step9-cutover.md#L1) is not this SHA's staging/prod deployment or health/SSE measurement. | AUD-036-RAG-023, AUD-036-RAG-025 |
| T148 | [x] | UNVERIFIED | [Quickstart account](quickstart-validation.md#L3) is a stub walk at 9faa7bf, with live steps deferred and collection exclusions. | AUD-036-RAG-025 |
| T149 | [x] | PARTIAL | [Resolution note](checklists/requirements.md#L146) auto-closes original items, but 177 appended checks and traceability conflicts remain. | AUD-036-RAG-025 |
| T150 | [x] | UNVERIFIED | [Analysis output](analyze-report.md#L29) exists but mislabels SCs; claimed zero-drift execution is not established at this SHA. | AUD-036-RAG-025 |

### Phase F

| Original task | Original state | Status | Evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T151 | [x] | PARTIAL | [Quorum tests](../../tests/contract/test_foundry_carveout.py#L75) can substitute Python when OPA is absent; effective target environment is untested. | AUD-036-RAG-005 |
| T152 | [x] | CONFLICT | [OPA policy](../../infra/policy/rego/foundry_carveout.rego#L49) uses optional row environment, not mandatory target `input.environment`. | AUD-036-RAG-005 |
| T153 | [x] | IMPLEMENTED | [Infrastructure registry schema](../../infra/parameters/foundry-carveout.schema.json#L12) adds the requested quorum keys/environment enum; enforcement is separate. | - |
| T154 | [x] | CONFLICT | [Spec registry schema](contracts/foundry-cv.schema.json#L1) and infrastructure schema differ in version/environment/conditional requirements. | AUD-036-RAG-005, AUD-036-RAG-013 |
| T155 | [x] | PARTIAL | [Coupling workflow](../../.github/workflows/amend-loop-coupling.yml#L10) is manual-only and not bidirectionally blocking PR changes. | AUD-036-RAG-005 |
| T156 | [x] | PARTIAL | [Amendment tests](../../tests/contract/test_audit_record_amend_loop_fields.py#L51) miss duplicate keys and exempt nullable-array compatibility. | AUD-036-RAG-013 |
| T157 | [x] | IMPLEMENTED | [State-machine tests](../../tests/integration/test_approval_workflow_state_machine.py#L26) assert pending/terminal/missing-authority transitions for the local helper. | - |
| T158 | [x] | PARTIAL | [Offline-boundary tests](../../tests/integration/test_field_coordinator_offline_boundaries.py#L27) exercise predicates/builders, not dispatch/reconnect review. | AUD-036-RAG-017 |
| T159 | [x] | PARTIAL | [Override tests](../../tests/contract/test_sc017_override_completeness.py#L111) construct 100 records; do not sample actual override/public-warning events. | AUD-036-RAG-012, AUD-036-RAG-014 |
| T160 | [x] | IMPLEMENTED | [Relocated audit mirror](../../packages/schemas/spec_036/audit-record-llm-call.json#L1) is byte-identical to the spec contract, including its independently reported defects. | AUD-036-RAG-013 |
| T161 | [x] | CONFLICT | [Model amendments](../../packages/domain/src/ama_domain/audit_record.py#L182) disagree on nullable ties/offline decision and legacy index requirement. | AUD-036-RAG-013 |
| T162 | [x] | PARTIAL | [Phase F script](../../infra/scripts/migrate-audit-record-036.ps1#L153) exists but is not dry-run by default and can warn/succeed on failures. | AUD-036-RAG-013 |
| T163 | [x] | PARTIAL | [Audit builder/writer](../../apps/agents/common/audit.py#L103) exposes fields without all applicable production event consumers. | AUD-036-RAG-012, AUD-036-RAG-014 |
| T164 | [x] | PARTIAL | [ApprovalWorkflow](../../apps/api/app/services/approval_workflow.py#L140) mutates local state; mounted routes use a different service. | AUD-036-RAG-014 |
| T165 | [x] | PARTIAL | [Offline gate](../../apps/agents/common/offline_cache.py#L428) is not invoked at dispatch; reconnect queue omits some safe decisions requiring review. | AUD-036-RAG-017 |
| T166 | [x] | PARTIAL | [Alias test stub](../../tests/e2e/test_blue_green_alias_flip.py#L1) checks resolver strings, not concrete Search-client targets. | AUD-036-RAG-009 |
| T167 | [x] | PARTIAL | [Rollback tests](../../tests/integration/test_index_rollback_slo.py#L66) use injected clocks/approval strings, not authenticated operational SLO evidence. | AUD-036-RAG-010 |
| T168 | [x] | PARTIAL | [Resolver](../../apps/agents/common/retrieval_client.py#L644) does not bind the live client to the concrete index. | AUD-036-RAG-009 |
| T169 | [x] | PARTIAL | [Result field](../../packages/domain/src/ama_domain/retrieval.py#L155) exists; cache/client provenance can label a different actual index. | AUD-036-RAG-009, AUD-036-RAG-012 |
| T170 | [x] | PARTIAL | [Rollback helper](../../apps/api/app/services/index_rollback.py#L126) has no mounted bus/approval/alias/audit provider composition. | AUD-036-RAG-010 |
| T171 | [x] | PARTIAL | [Cleanup](../../infra/scripts/cleanup-stale-indices.ps1#L96) uses modification age, not persisted retirement time, and is not scheduled. | AUD-036-RAG-010 |
| T172 | [x] | PARTIAL | [Rollback runbook](../../docs/runbooks/036-foundry-rag-blue-green-rollback.md#L35) is authored but operational timer/tooling assertions are not fulfilled. | AUD-036-RAG-010, AUD-036-RAG-025 |
| T173 | [x] | PARTIAL | [Agency tests](../../tests/contract/test_agency_disambiguation.py#L44) check labels/minimal counts rather than measured retrieval precision. | AUD-036-RAG-015, AUD-036-RAG-024 |
| T174 | [x] | PARTIAL | [Authority tests](../../tests/contract/test_authority_precedence.py#L44) assert expected fixture ranks, not actual Commonwealth-first results. | AUD-036-RAG-015, AUD-036-RAG-024 |
| T175 | [x] | PARTIAL | [Ingest agency tests](../../tests/integration/test_ingest_agency_lint.py#L34) call a validator directly; actual CLI does not invoke it. | AUD-036-RAG-003, AUD-036-RAG-015 |
| T176 | [x] | CONFLICT | [Tie-break assertions](../../tests/contract/test_precedence_tiebreak.py#L81) encode ascending model IDs against the newer-first requirement. | AUD-036-RAG-013, AUD-036-RAG-015 |
| T177 | [x] | PARTIAL | [COMDISPLAN tests](../../tests/integration/test_comdisplan_activation.py#L42) call global-flag helpers, not incident-scoped retrieval. | AUD-036-RAG-015 |
| T178 | [x] | IMPLEMENTED | [Live index declaration](../../apps/ingest-runner/src/ama_ingest/live_clients.py#L155) and [schema](../../infra/scripts/aisearch-schema.json#L23) contain agency fields. Population is T181. | - |
| T179 | [x] | IMPLEMENTED | [Index fields](../../apps/ingest-runner/src/ama_ingest/live_clients.py#L155) declare authority/rank; source propagation remains T182. | - |
| T180 | [x] | IMPLEMENTED | [Relocated chunk mirror](../../packages/schemas/spec_036/chunk-metadata.schema.json#L1) is byte-identical to the spec contract. | - |
| T181 | [x] | PARTIAL | [Chunker metadata parameters](../../apps/ingest-runner/src/ama_ingest/chunker.py#L178) exist; CLI passes none and does not enforce metadata lint. | AUD-036-RAG-003, AUD-036-RAG-015 |
| T182 | [x] | PARTIAL | [Chunk defaults](../../apps/ingest-runner/src/ama_ingest/chunker.py#L178) are not the promised authority/rank defaults; source values are omitted. | AUD-036-RAG-015 |
| T183 | [x] | PARTIAL | [Agency helper](../../apps/agents/common/retrieval_client.py#L345) exists but is not called by production retrieval. | AUD-036-RAG-015 |
| T184 | [x] | PARTIAL | [Retrieval return](../../apps/agents/common/retrieval_client.py#L816) has no integrated precedence/both-source/conflict-note pass. | AUD-036-RAG-015, AUD-036-RAG-021 |
| T185 | [x] | CONFLICT | [Tie helper](../../apps/agents/common/retrieval_client.py#L382) is uncalled and model ordering disagrees with newer-first semantics. | AUD-036-RAG-015 |
| T186 | [x] | PARTIAL | [Elevation helper](../../apps/agents/common/retrieval_client.py#L553) lacks incident/hazard/tenant activation and production caller. | AUD-036-RAG-015 |
| T187 | [x] | PARTIAL | [Flag setter](../../apps/agents/common/retrieval_client.py#L473) is process-local and controls no live ranking consumer/distributed audit chain. | AUD-036-RAG-015 |
| T188 | [x] | UNVERIFIED | [Flip script](../../infra/scripts/blue-green-flip.ps1#L106) has a placeholder parity phase; no attributable co-scheduled metadata rebuild exists. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-025 |
| T189 | [x] | PARTIAL | [Golden data](../../tests/fixtures/golden-set-v1.json#L6) has twenty agency scenarios but no required tags/request/expected-chunk shape. | AUD-036-RAG-024 |
| T190 | [x] | PARTIAL | [Golden data](../../tests/fixtures/golden-set-v1.json#L6) has twenty authority labels, only nine ACT/Commonwealth entries, not twenty qualifying queries. | AUD-036-RAG-024 |
| T191 | [x] | MISSING | [CI selection](../../.github/workflows/ci.yml#L133) runs label tests; no measured 95% agency-precision gate found in workflows/tests. | AUD-036-RAG-024 |
| T192 | [x] | MISSING | [Authority assertions](../../tests/contract/test_authority_precedence.py#L44) compare authored expectations; no measured Commonwealth-first gate found. | AUD-036-RAG-024 |
| T193 | [x] | PARTIAL | [Signature tests](../../tests/contract/test_cultural_authority_registry.py#L47) inject booleans instead of verifying authentic signed records. | AUD-036-RAG-003 |
| T194 | [x] | PARTIAL | [Gate tests](../../tests/integration/test_cultural_authority_gate.py#L55) exercise detached helpers, not live retrieval/model/cache consumers. | AUD-036-RAG-003 |
| T195 | [x] | PARTIAL | [Lockdown tests](../../tests/integration/test_cultural_authority_flag_lockdown.py#L24) use Python semantics, not actual OPA/flag mutation. | AUD-036-RAG-003 |
| T196 | [x] | PARTIAL | [Registry module composition](../../infra/bicep/main.bicep#L494) is in the alternate root, not selected azd graph; deployment unverified. | AUD-036-RAG-003, AUD-036-RAG-023 |
| T197 | [x] | IMPLEMENTED | [Relocated consent schema mirror](../../packages/schemas/spec_036/cultural-authority-registry.schema.json#L1) is byte-identical. | - |
| T198 | [x] | PARTIAL | [Registry client](../../apps/agents/common/cultural_authority_registry.py#L175) caches/fetches but lacks mandatory real verification and tenant/council/start-time binding. | AUD-036-RAG-003 |
| T199 | [x] | PARTIAL | [Post-filter helper](../../apps/agents/common/cultural_authority_gate.py#L49) is not invoked in shared retrieval. | AUD-036-RAG-003 |
| T200 | [x] | PARTIAL | [Ingest caller](../../apps/ingest-runner/src/ama_ingest/__main__.py#L372) omits cultural fields despite declared schema parameters. | AUD-036-RAG-003, AUD-036-RAG-007 |
| T201 | [x] | PARTIAL | [OPA deny rule](../../infra/policy/rego/cultural_authority_flag.rego#L28) has no production flag-flip enforcement consumer. | AUD-036-RAG-003 |
| T202 | [~] | UNVERIFIED | [Human handoff](HANDOFF.md#L20) leaves initial registry seeding/sign-off open; no signed population evidence established. | AUD-036-RAG-005, AUD-036-RAG-025 |
| T203 | [~] | UNVERIFIED | [External authoring boundary](tasks.md#L676) remains open; community-authored translated/protected corpus completeness cannot be inferred. | AUD-036-RAG-025 |
| T204 | [x] | PARTIAL | [SAR tests](../../tests/contract/test_privacy_act_sar.py#L29) test APP labels, not subject-bounded authorised mounted reads. | AUD-036-RAG-026 |
| T205 | [x] | PARTIAL | [CSV tests](../../tests/contract/test_pspf_audit_export.py#L27) assert escaping/order but not actual endpoint/producer mapping. | AUD-036-RAG-026 |
| T206 | [x] | PARTIAL | [Compliance adapter](../../apps/api/app/api/routes/audit_compliance.py#L68) is unmounted and calls absent repository methods; anonymisation/consent controls absent. | AUD-036-RAG-026 |
| T207 | [x] | PARTIAL | [CSV projection](../../apps/api/app/api/routes/audit_compliance.py#L132) ignores actual timestamp/authority/rationale fields and is not mounted. | AUD-036-RAG-026 |
| T208 | [x] | PARTIAL | [COMDISPLAN helper](../../apps/agents/common/retrieval_client.py#L553) is the same unconsumed global mechanism as T186. | AUD-036-RAG-015 |
| T209 | [x] | IMPLEMENTED | [ISM mapping scaffold](../../docs/compliance/ISM-2024-mapping.md#L3) names controls and explicitly pending human sign-off; not compliance proof. | AUD-036-RAG-025 |
| T210 | [~] | UNVERIFIED | [Handoff](HANDOFF.md#L9) and [T210](tasks.md#L697) leave federal approval open and disagree on authority chain. | AUD-036-RAG-005, AUD-036-RAG-025 |
| T211 | [x] | PARTIAL | [Relocated verifier](../../infra/scripts/verify-federal-compliance.ps1#L87) checks names only and is not called by selected CD. | AUD-036-RAG-005 |
| T212 | [x] | PARTIAL | [Staleness tests](../../tests/integration/test_corpus_staleness_alert.py#L87) use list callbacks, not actual scheduling/page/UI or deduplication. | AUD-036-RAG-022 |
| T213 | [x] | PARTIAL | [Workflow](../../.github/workflows/corpus-ingest.yml#L17) retains dormant drift logic without nightly/push triggers or no-drift gating. | AUD-036-RAG-023 |
| T214 | [x] | PARTIAL | [Freshness component](../../apps/web/src/components/corpus/CorpusFreshnessIndicator.tsx#L67) implements bands but has no card/chat consumer or manifest feed. | AUD-036-RAG-021 |
| T215 | [x] | PARTIAL | [Assessment/emission](../../apps/api/app/services/corpus_freshness.py#L139) lacks production state/scheduler/sinks and per-build deduplication. | AUD-036-RAG-022 |
| T216 | [x] | PARTIAL | [Freshness emission](../../apps/api/app/services/corpus_freshness.py#L139) suppresses paging only; bus alert and incomplete flag provenance remain. | AUD-036-RAG-022 |
| T217 | [x] | IMPLEMENTED | [Stale runbook](../../docs/runbooks/036-foundry-rag-corpus-stale.md#L11) describes four causes; a walked game day is unverified. | AUD-036-RAG-025 |
| T218 | [x] | PARTIAL | [Windows job](../../.github/workflows/ci.yml#L174) and [cleanup fixture](../../tests/conftest.py#L26) exist; specific Windows ingest/cache parity not proven. | AUD-036-RAG-024 |
| T219 | [x] | PARTIAL | [Load task](../../tests/load/locustfile.py#L109) has route/session/rate/status flaws and [empty baseline](../../tests/load/baselines/spec-036-50-agent-baseline.json#L16). | AUD-036-RAG-024 |
| T220 | [x] | PARTIAL | [Canonical file](../../tests/fixtures/golden-set-v1.json#L6) is only 42 malformed-for-contract entries; inline and sibling fixtures remain. | AUD-036-RAG-024 |
| T221 | [x] | PARTIAL | [Live E2E body](../../tests/e2e/test_blue_green_alias_flip.py#L218) explicitly fails; in-process label/timing tests do not prove staging Search. | AUD-036-RAG-009, AUD-036-RAG-024 |
| T222 | [x] | PARTIAL | [CI](../../.github/workflows/ci.yml#L174) has Windows/golden lanes; required actual nightly/pre-release and meaningful load bindings incomplete. | AUD-036-RAG-023, AUD-036-RAG-024 |
| T223 | [x] | PARTIAL | [Test strategy](../../docs/testing/spec-036-test-strategy.md#L25) authors taxonomy but advertises unsupported cadence/live coverage. | AUD-036-RAG-024, AUD-036-RAG-025 |
| T224 | [x] | PARTIAL | [Load extras](../../pyproject.toml#L38) declare psutil with a multi-major interval, not the requested minor pin. | AUD-036-RAG-024 |
| T225 | [x] | PARTIAL | [Four conflict tests](../../tests/integration/test_conflict_detection.py#L45) lack real aggregation/scoped identity/replay-stable negative assertions. | AUD-036-RAG-018 |
| T226 | [x] | PARTIAL | [Escalation tests](../../tests/integration/test_aiims_escalation.py#L58) call helpers, not durable timers/authenticated role workflows. | AUD-036-RAG-018 |
| T227 | [x] | PARTIAL | [Relocated conflict mirror](../../packages/schemas/spec_036/conflict_detection.schema.json#L1) matches; Cosmos module is only alternate-root composed. | AUD-036-RAG-018, AUD-036-RAG-023 |
| T228 | [x] | PARTIAL | [Detector](../../apps/api/app/services/conflict_detection.py#L93) exists without actual recommendation-aggregation caller. | AUD-036-RAG-018 |
| T229 | [x] | PARTIAL | [Optional conflict sink](../../apps/api/app/services/conflict_detection.py#L300) is not durable scoped evidence persistence; IDs/rules require repair. | AUD-036-RAG-018 |
| T230 | [x] | PARTIAL | [Escalation](../../apps/api/app/services/aiims_escalation.py#L122) conflates ack/resolution and lacks actual audit-row linkage/authenticated timers. | AUD-036-RAG-018 |
| T231 | [x] | PARTIAL | [Conflict service](../../apps/api/app/services/conflict_detection.py#L1) uses process-local optional flag hooks, not active progressive-delivery controls. | AUD-036-RAG-018 |
| T232 | [x] | PARTIAL | [OTel test](../../tests/integration/test_otel_retrieval_span.py#L73) manually nests recorder contexts rather than driving production exporter/correlation. | AUD-036-RAG-022 |
| T233 | [x] | PARTIAL | [Dependencies](../../apps/agents/pyproject.toml#L1) include compatible OTel pieces but differ from named instrumentation/minor pins; lock execution unverified. | AUD-036-RAG-022 |
| T234 | [x] | PARTIAL | [Telemetry shim](../../apps/agents/common/otel_telemetry.py#L77) does not export production metrics despite retrieval wrapper. | AUD-036-RAG-022 |
| T235 | [x] | PARTIAL | [Sync wrapper](../../apps/agents/common/foundry_chat_client.py#L437) is instrumented only into the shim; streaming/correlation coverage incomplete. | AUD-036-RAG-022 |
| T236 | [x] | PARTIAL | [Ingest metrics](../../apps/ingest-runner/src/ama_ingest/__main__.py#L188) use nonexistent counters/unavailable bridge in runner image. | AUD-036-RAG-022 |
| T237 | [x] | PARTIAL | [Workbook](../../infra/bicep/modules/foundry-rag-success-criteria-dashboard.bicep#L50) has three mislabeled tiles, not nineteen; [Grafana](../../infra/dashboards/foundry-rag-ingest.json#L1) lacks errors/signal wiring. | AUD-036-RAG-022 |
| T238 | [x] | PARTIAL | [Alert module](../../infra/bicep/modules/foundry-rag-alerts.bicep#L28) is authored without active-root data/action wiring; fixed inference threshold is not relative SC-012. | AUD-036-RAG-022 |
| T239 | [x] | IMPLEMENTED | [Relocated axe tests](../../apps/web/tests/web/src/components/citation/citation-card.axe.test.tsx#L39) scan collapsed/expanded states in warn-only mode. | - |
| T240 | [x] | IMPLEMENTED | [Keyboard tests](../../apps/web/tests/web/src/components/citation/citation-card.test.tsx#L30) assert tab/Enter/Space/ARIA state at component scope. | - |
| T241 | [x] | IMPLEMENTED | [Card toggle](../../packages/ui/src/components/citation/citation-card.tsx#L120) and [live region](../../apps/web/src/components/recommendations/recommendation-card.tsx#L75) are authored; mounting is separate. | AUD-036-RAG-021 |
| T242 | [x] | IMPLEMENTED | [Warn-only CI lane](../../.github/workflows/ci.yml#L227) and [axe dependency](../../apps/web/package.json#L48) reuse existing Vitest tools. | - |
| T243 | [x] | PARTIAL | [Baseline](../../docs/accessibility/spec-036-citation-card-baseline.md#L22) has a roadmap; claimed manual contrast/screen-reader outcomes are unverified. | AUD-036-RAG-021, AUD-036-RAG-025 |
| T244 | [x] | IMPLEMENTED | [ADR 12](../../docs/decisions/036-foundry-rag-grounding/12-cultural-authority-gating.md#L16) body exists; its claimed operational consent wiring is not proof. | AUD-036-RAG-025 |
| T245 | [x] | IMPLEMENTED | [ADR 13](../../docs/decisions/036-foundry-rag-grounding/13-authority-precedence-ranking.md#L20) authors the intended ranking/tie rationale. | - |
| T246 | [x] | CONFLICT | [ADR 14](../../docs/decisions/036-foundry-rag-grounding/14-approval-workflow-audit.md#L23) eight-field list/offline boolean disagrees with later schemas/tasks. | AUD-036-RAG-013 |
| T247 | [~] | UNVERIFIED | [ADR 15](../../docs/decisions/036-foundry-rag-grounding/15-federal-compliance-mapping.md#L8) remains a stub without federal signed publication authority. | AUD-036-RAG-025 |
| T248 | [x] | IMPLEMENTED | [ADR 16](../../docs/decisions/036-foundry-rag-grounding/16-blue-green-atomicity.md#L20) authors pinning/manual rollback/retention; execution is separate. | - |
| T249 | [x] | IMPLEMENTED | [ADR 17](../../docs/decisions/036-foundry-rag-grounding/17-corpus-freshness.md#L16) body exists; current scheduler claims/timezone require reconciliation. | AUD-036-RAG-025 |
| T250 | [x] | CONFLICT | [ADR 18](../../docs/decisions/036-foundry-rag-grounding/18-multi-agent-conflict.md#L22) narrows detector semantics and endorses identity-prefix authority. | AUD-036-RAG-018, AUD-036-RAG-025 |
| T251 | [x] | PARTIAL | [ADR 19](../../docs/decisions/036-foundry-rag-grounding/19-test-coverage-windows.md#L24) is authored but fixture floors/cadence/outcome claims do not match evidence. | AUD-036-RAG-024, AUD-036-RAG-025 |

## Requirement Coverage

All 68 original FR definitions are listed, including IDX-04a and IDX-05a. No separately numbered NFRs exist;
nonfunctional and unnumbered obligations are accounted below. Status describes inspected source support. Every actual
model/retrieval/runtime/performance/security/deployment/human-review outcome remains UNVERIFIED without attributable
evidence, even where an implementation or assertion is present. SHOULD outcomes are not silently promoted to MUST.

| Requirement | Status | Evidence and remaining obligation | Follow-up |
| --- | --- | --- | --- |
| FR-RAG-FM-01 | CONFLICT | [Definition](spec.md#L295); [LLM adapter](../../apps/agents/common/llm_client.py#L193) has Foundry config/seam but current transport exceptions and actual dispatcher bypass conflict with required SDK/grounding. | AUD-036-RAG-002, AUD-036-RAG-020 |
| FR-RAG-FM-02 | PARTIAL | [Definition](spec.md#L296); [MAF factory](../../apps/agents/maf_runtime/chat_client.py#L71) preserves signature but not shared seam or explicit-tier resolution. | AUD-036-RAG-020 |
| FR-RAG-FM-03 | CONFLICT | [Definition](spec.md#L297); [controller](../../apps/api/app/services/simulation/controller_service.py#L482) keeps direct AsyncAzureOpenAI and lacks injectable stream seam. | AUD-036-RAG-020 |
| FR-RAG-FM-04 | CONFLICT | [Definition](spec.md#L298); [lint](../../tests/contract/test_no_openai_imports.py#L74) accepts broader production exceptions than the requirement. | AUD-036-RAG-020 |
| FR-RAG-FM-05 | IMPLEMENTED | [Definition](spec.md#L299); [controller AAD construction](../../apps/api/app/services/simulation/controller_service.py#L530) and inspected live transports use DefaultAzureCredential/cognitive scope, not API keys. Actual authentication is UNVERIFIED. | - |
| FR-RAG-FM-06 | PARTIAL | [Original](spec.md#L300), [explicit amendment](spec.md#L98); activation canary is superseded, but real kill-switch audit/fallback/regression controls remain incomplete. | AUD-036-RAG-002, AUD-036-RAG-020, AUD-036-RAG-024 |
| FR-RAG-FM-07 | PARTIAL | [Definition](spec.md#L301); [shared seam](../../apps/agents/common/foundry_chat_client.py#L1) exists but MAF/controller lack required constructor-callable transport injection. | AUD-036-RAG-020 |
| FR-RAG-CV-01 | CONFLICT | [Definition](spec.md#L305); [registry/policy](../../infra/policy/rego/foundry_carveout.rego#L49) does not enforce authoritative prod quorum/current effective model inventory. | AUD-036-RAG-005 |
| FR-RAG-CV-02 | PARTIAL | [Definition](spec.md#L306); [CD call](../../.github/workflows/cd.yml#L211) lacks plan/environment and strict expired-review checking. | AUD-036-RAG-005 |
| FR-RAG-CV-03 | PARTIAL | [Definition](spec.md#L307); [gateway boundary](../../apps/agents/common/foundry_chat_client.py#L362) covers only selected user strings, not all prompts/responses/adapters. | AUD-036-RAG-001 |
| FR-RAG-CV-04 | PARTIAL | [Definition](spec.md#L308); [checker](../../scripts/verify-carveout.ps1#L89) does not cover every resolved data-plane service; deployed locations unqueried. | AUD-036-RAG-004, AUD-036-RAG-005 |
| FR-RAG-IDX-01 | PARTIAL | [Definition](spec.md#L312); [CLI](../../apps/ingest-runner/src/ama_ingest/__main__.py#L124) scans corpus but source metadata/rights and automatic delivery are incomplete. | AUD-036-RAG-006, AUD-036-RAG-011, AUD-036-RAG-023 |
| FR-RAG-IDX-02 | CONFLICT | [Definition](spec.md#L313); [mode default](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L38), revoked-content residue and actual chunking/SDK diverge. | AUD-036-RAG-006, AUD-036-RAG-011, AUD-036-RAG-020 |
| FR-RAG-IDX-03 | PARTIAL | [Definition](spec.md#L318); [chunk projection](../../apps/agents/common/retrieval_client.py#L293) omits metadata and build identity/retrieved-at are not trustworthy end-to-end. | AUD-036-RAG-009, AUD-036-RAG-011 |
| FR-RAG-IDX-04 | PARTIAL | [Definition](spec.md#L319); [live state](../../apps/ingest-runner/src/ama_ingest/live_clients.py#L316) cannot detect all model/schema rebuilds; pre-embedding skip and measured gates are absent. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-010 |
| FR-RAG-IDX-04a | PARTIAL | [Definition](spec.md#L320); [Search construction](../../apps/agents/common/retrieval_client.py#L681) still queries alias; result label is not actual pinning. | AUD-036-RAG-009 |
| FR-RAG-IDX-05 | PARTIAL | [Definition](spec.md#L321); [azd hooks](../../azure.yaml#L14) do not invoke new ingest job; live completion/SHA lookup is incomplete. | AUD-036-RAG-023 |
| FR-RAG-IDX-05a | PARTIAL | [Definition](spec.md#L322); [workflow](../../.github/workflows/corpus-ingest.yml#L17) is manual-only; drift output does not gate subsequent work. | AUD-036-RAG-023 |
| FR-RAG-IDX-06 | CONFLICT | [Definition](spec.md#L323); [active root](../../infra/main.bicep#L302) explicitly permits public Search without private subnet/DNS wiring. | AUD-036-RAG-004 |
| FR-RAG-IDX-07 | PARTIAL | [Definition](spec.md#L324); [inventory lint](../../tools/lint/check_licence_inventory.py#L87) omits required rights/URL detail and all-column drift. | AUD-036-RAG-006 |
| FR-RAG-IDX-08 | PARTIAL | [Definition](spec.md#L325); jurisdiction union/single alias exist; [capacity alert](../../infra/modules/ai-search.bicep#L177) uses wrong metric and first-ingest sizing is unverified. | AUD-036-RAG-004, AUD-036-RAG-022 |
| FR-RAG-IDX-09 | PARTIAL | [Definition](spec.md#L326); [rollback helper](../../apps/api/app/services/index_rollback.py#L126) lacks authenticated operational/event/timer/retention composition. | AUD-036-RAG-008, AUD-036-RAG-010 |
| FR-RAG-AG-01 | PARTIAL | [Definition](spec.md#L330); [dispatcher](../../apps/agents/dispatcher/agent.py#L209) and [MAF run](../../apps/agents/maf_runtime/agents/_factory.py#L265) bypass retrieval. | AUD-036-RAG-002 |
| FR-RAG-AG-02 | PARTIAL | [Definition](spec.md#L331); [writer](../../apps/agents/common/audit.py#L103) is not the complete durable mounted per-call/operator chain; schema compatibility conflicts remain. | AUD-036-RAG-012, AUD-036-RAG-013, AUD-036-RAG-014 |
| FR-RAG-AG-03 | PARTIAL | [Definition](spec.md#L332); [card](../../packages/ui/src/components/citation/citation-card.tsx#L70) is authored but real responses/pages do not supply/render canonical citations. | AUD-036-RAG-002, AUD-036-RAG-019, AUD-036-RAG-021 |
| FR-RAG-AG-04 | PARTIAL | [Definition](spec.md#L333); [agency/ranking helpers](../../apps/agents/common/retrieval_client.py#L345) are disconnected and projection loses metadata/tie trace. | AUD-036-RAG-009, AUD-036-RAG-015 |
| FR-RAG-AG-05 | PARTIAL | [Definition](spec.md#L334); [filter](../../apps/agents/common/citation_filter.py#L63) is uncalled and trusts SHA with forged metadata. | AUD-036-RAG-019 |
| FR-RAG-AG-06 | PARTIAL | [Definition](spec.md#L335); [inclusion helper](../../apps/agents/communication/grounding.py#L83) is uncalled and request-incompatible. | AUD-036-RAG-002, AUD-036-RAG-015 |
| FR-RAG-CA-01 | UNVERIFIED | [Human authoring requirement](spec.md#L339); [open T203](tasks.md#L676) does not establish community-authored language corpus or approvals. | AUD-036-RAG-003, AUD-036-RAG-025 |
| FR-RAG-CA-02 | UNVERIFIED | [Definition](spec.md#L340); [human handoff](HANDOFF.md#L20) leaves Sacred Site protocols/consultation unproved; plumbing alone is not content. | AUD-036-RAG-003, AUD-036-RAG-025 |
| FR-RAG-CA-03 | UNVERIFIED | [Definition](spec.md#L341); [T203](tasks.md#L676) leaves ALT/APY/Tiwi governance content and consent authorisation open. | AUD-036-RAG-003, AUD-036-RAG-025 |
| FR-RAG-CA-04 | PARTIAL | [Definition](spec.md#L342); [gate](../../apps/agents/common/cultural_authority_gate.py#L49) is detached and registry verification/scope can fail open. | AUD-036-RAG-003 |
| FR-RAG-CA-05 | UNVERIFIED | [Definition](spec.md#L343); [T202](tasks.md#L675) remains external; required cultural approvals/population are absent and CD gate incomplete. | AUD-036-RAG-005, AUD-036-RAG-025 |
| FR-RAG-AC-01 | PARTIAL | [Definition](spec.md#L347); [retrieval](../../apps/agents/common/retrieval_client.py#L816) and unmounted card lack both-authority presentation/tie trace/conflict note. | AUD-036-RAG-015, AUD-036-RAG-021 |
| FR-RAG-NS-01 | CONFLICT | [Definition](spec.md#L351); [deterministic notifier](../../apps/agents/common/dependency_notifier.py#L4) makes no LLM call, but [ADR](../../docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md#L29) omits required audit reason. | AUD-036-RAG-012, AUD-036-RAG-024 |
| FR-RAG-NS-02 | PARTIAL | [Definition](spec.md#L352); [BoM ADR](../../docs/decisions/036-foundry-rag-grounding/02-rag-optout-bom-live.md#L24) preserves live-feed opt-out rationale; actual call-site audit completeness not established. | AUD-036-RAG-012, AUD-036-RAG-024 |
| FR-RAG-NS-03 | PARTIAL | [Definition](spec.md#L353); [GA ADR](../../docs/decisions/036-foundry-rag-grounding/03-rag-optout-ga-live.md#L23) exists; live data remains distinct but complete opt-out audit is unsupported. | AUD-036-RAG-012, AUD-036-RAG-024 |
| FR-RAG-NS-04 | PARTIAL | [Definition](spec.md#L354); [collection ADR](../../docs/decisions/036-foundry-rag-grounding/04-rag-optout-planning-collection.md#L23) is authored; deterministic collection does not prove emitted canonical reasons. | AUD-036-RAG-012, AUD-036-RAG-024 |
| FR-RAG-NS-05 | PARTIAL | [Definition](spec.md#L355); [transaction ADR](../../docs/decisions/036-foundry-rag-grounding/05-rag-optout-logistics-transactional.md#L24) supports separation, not full operational audit coverage. | AUD-036-RAG-012, AUD-036-RAG-024 |
| FR-RAG-NS-06 | PARTIAL | [Definition](spec.md#L356); [script scheduler](../../apps/api/app/services/warp_scheduler.py#L130) avoids retrieval but marker/audit is not at actual script dispatch. | AUD-036-RAG-019, AUD-036-RAG-024 |
| FR-RAG-NS-07 | PARTIAL | [Definition](spec.md#L357); [classification gateway](../../apps/agents/common/model_gateway.py#L1) exists without full-envelope enforcement/audited offline DACC routing. | AUD-036-RAG-001, AUD-036-RAG-024 |
| FR-RAG-NS-08 | PARTIAL | [Definition](spec.md#L358); [lint](../../tools/lint/check_rag_optout_bindings.py#L57) cannot detect an unmarked ungrounded call. | AUD-036-RAG-024 |
| FR-RAG-NS-09 | CONFLICT | [Definition](spec.md#L359); [Observer ADR](../../docs/decisions/036-foundry-rag-grounding/09-rag-optout-observer-auditor.md#L23) reason/required audit do not match canonical replay semantics. | AUD-036-RAG-012, AUD-036-RAG-024 |
| FR-RAG-SIM-01 | PARTIAL | [Definition](spec.md#L363); [controller](../../apps/api/app/services/simulation/controller_service.py#L613) auto-wires shared retrieval but with process defaults and incomplete per-inference context. | AUD-036-RAG-019 |
| FR-RAG-SIM-02 | PARTIAL | [Definition](spec.md#L364); [SSE construction](../../apps/api/app/services/simulation/controller_service.py#L826) lists retrieved citations without claim validation; web ignores the event. | AUD-036-RAG-019, AUD-036-RAG-021 |
| FR-RAG-SIM-03 | PARTIAL | [Definition](spec.md#L365); [empty-event branch](../../apps/api/app/services/simulation/controller_service.py#L826) does not constrain streamed unsupported doctrine or unconfigured retrieval. | AUD-036-RAG-019 |
| FR-RAG-SIM-04 | PARTIAL | [Definition](spec.md#L366); [optional audit](../../apps/api/app/services/simulation/controller_service.py#L873) is not injected and hashes only forwarded question. | AUD-036-RAG-012 |
| FR-RAG-SIM-05 | PARTIAL | [Definition](spec.md#L367); [role/rate guards](../../apps/api/app/api/routes/simulation_chat.py#L58) and [watermark tool](../../apps/api/app/services/simulation/controller_service.py#L959) exist; full grounded-path tenant/approval/egress acceptance is unverified. | AUD-036-RAG-014, AUD-036-RAG-019, AUD-036-RAG-024 |
| FR-RAG-SIM-06 | PARTIAL | [Definition](spec.md#L368); [script path](../../apps/api/app/services/warp_scheduler.py#L130) is deterministic while surrounding chat grounding remains incomplete. | AUD-036-RAG-019 |
| FR-RAG-LS-01 | PARTIAL | [Definition](spec.md#L372); [approval service](../../apps/api/app/services/recommendation_service.py#L18) does not compose all new audit/terminal/manual conflict controls. | AUD-036-RAG-014, AUD-036-RAG-018 |
| FR-RAG-LS-02 | PARTIAL | [Definition](spec.md#L373); [cache/spool](../../apps/agents/common/offline_cache.py#L233) helpers lack authenticated payload, runtime bounds and acknowledged reconnection. | AUD-036-RAG-016, AUD-036-RAG-017 |
| FR-RAG-LS-03 | PARTIAL | [Definition](spec.md#L374); [actual approval route](../../apps/api/app/api/routes/recommendations.py#L16) lacks complete grounded draft/final actor linkage. | AUD-036-RAG-012, AUD-036-RAG-014 |
| FR-RAG-COMP-01 | PARTIAL | [Definition](spec.md#L378); [compliance scaffold](../../apps/api/app/api/routes/audit_compliance.py#L68) is unmounted; APP labels do not prove consent, minimisation, SAR or retention. | AUD-036-RAG-012, AUD-036-RAG-026 |
| FR-RAG-COMP-02 | PARTIAL | [Definition](spec.md#L379); [ISM mapping](../../docs/compliance/ISM-2024-mapping.md#L3) is pending human sign-off; actual integrity/retention proof absent. | AUD-036-RAG-005, AUD-036-RAG-012, AUD-036-RAG-025 |
| FR-RAG-COMP-03 | PARTIAL | [Definition](spec.md#L380); [export](../../apps/api/app/api/routes/audit_compliance.py#L132) has CSV scaffold but no working mounted authorised source mapping. | AUD-036-RAG-026 |
| FR-RAG-COMP-04 | PARTIAL | [Definition](spec.md#L381); [global elevation helper](../../apps/agents/common/retrieval_client.py#L553) is not incident-scoped or used in retrieval. | AUD-036-RAG-015 |
| FR-RAG-FRESH-01 | PARTIAL | [Definition](spec.md#L385); [indicator](../../apps/web/src/components/corpus/CorpusFreshnessIndicator.tsx#L67) is unmounted with no canonical manifest timestamp feed. | AUD-036-RAG-021 |
| FR-RAG-FRESH-02 | PARTIAL | [Definition](spec.md#L386); [alert helper](../../apps/api/app/services/corpus_freshness.py#L139) lacks scheduled state/deduplication and complete disabled behavior. | AUD-036-RAG-022 |
| FR-RAG-COORD-01 | PARTIAL | [Definition](spec.md#L390); [detector](../../apps/api/app/services/conflict_detection.py#L93) is detached and lacks scope/replay-stable evidence. | AUD-036-RAG-018 |
| FR-RAG-COORD-02 | PARTIAL | [Definition](spec.md#L391); [escalation](../../apps/api/app/services/aiims_escalation.py#L122) lacks authenticated roles, separate acknowledgement/resolution and durable timer/queue. | AUD-036-RAG-018 |
| FR-RAG-TEST-01 | PARTIAL | [Definition](spec.md#L395); [Windows CI](../../.github/workflows/ci.yml#L174) exists without complete platform-specific ingest/cache assertions and attributable execution. | AUD-036-RAG-024 |
| FR-RAG-TEST-02 | PARTIAL | [Definition](spec.md#L396); [load task](../../tests/load/locustfile.py#L109) does not implement stable fifty sessions/50 RPS or meaningful response/baseline gates. Performance is SHOULD, harness obligations remain MUST. | AUD-036-RAG-024 |
| FR-RAG-TEST-03 | PARTIAL | [Definition](spec.md#L397); [fixture](../../tests/fixtures/golden-set-v1.json#L6) has 42 entries/zero tags instead of required fifty request-shaped cases. | AUD-036-RAG-024 |
| FR-RAG-TEST-04 | PARTIAL | [Definition](spec.md#L398); [staging test](../../tests/e2e/test_blue_green_alias_flip.py#L218) is unfinished; label-only fixtures cannot prove real four-part lifecycle. | AUD-036-RAG-009, AUD-036-RAG-024 |
| FR-RAG-OBS-01 | PARTIAL | [Definition](spec.md#L402); [telemetry shim](../../apps/agents/common/otel_telemetry.py#L77) has no actual OTel provider forwarding; scope/tags/correlation incomplete. | AUD-036-RAG-022 |
| FR-RAG-OBS-02 | PARTIAL | [Definition](spec.md#L403); [ingest wrapper](../../apps/ingest-runner/src/ama_ingest/__main__.py#L188) reads wrong counters and dashboard lacks complete live signals. | AUD-036-RAG-022 |
| FR-RAG-OBS-03 | PARTIAL | [Definition](spec.md#L404); [alerts](../../infra/bicep/modules/foundry-rag-alerts.bicep#L28) are not active-graph/data-pipeline wired to the required separate SLOs. | AUD-036-RAG-022 |
| FR-RAG-UI-01 | PARTIAL | [Definition](spec.md#L408); [keyboard/ARIA](../../packages/ui/src/components/citation/citation-card.tsx#L120) and warn-only axe work exist; mounted workflow/manual WCAG evidence is absent. SHOULD retained. | AUD-036-RAG-021, AUD-036-RAG-025 |

## Success Criteria Coverage

Each numeric runtime outcome is UNVERIFIED; PARTIAL/CONFLICT below additionally identifies an inspectable implementation
or gate defect. No authored baseline, mock suite, schema mirror or successful dictionary operation is treated as a live result.

| Success criterion | Status | Evidence and measurement limit | Follow-up |
| --- | --- | --- | --- |
| SC-001 | PARTIAL | [Source](spec.md#L459); [dispatcher](../../apps/agents/dispatcher/agent.py#L209) returns empty citations; no real 100% citation or 60-second reconstruction sample. | AUD-036-RAG-002, AUD-036-RAG-012, AUD-036-RAG-021 |
| SC-002 | CONFLICT | [Source](spec.md#L460); [production import](../../apps/api/app/services/simulation/controller_service.py#L482) and broadened lint contradict zero forbidden occurrences. | AUD-036-RAG-020 |
| SC-003 | CONFLICT | [Source](spec.md#L461); [registry](../../infra/parameters/foundry-carveout.yaml#L21) does not match current defaults/effective quorum; deployment approval coverage unproved. | AUD-036-RAG-005 |
| SC-004 | UNVERIFIED | [Source](spec.md#L462); [verifier](../../scripts/verify-carveout.ps1#L89) is incomplete; no deployed resource query/plan execution was performed. | AUD-036-RAG-005, AUD-036-RAG-025 |
| SC-005 | PARTIAL | [Source](spec.md#L463); [embedding-before-skip](../../apps/ingest-runner/src/ama_ingest/__main__.py#L387) contradicts zero re-embedding; no valid 10% warm/cold measurement. | AUD-036-RAG-007 |
| SC-006 | PARTIAL | [Source](spec.md#L464); [rights defaults](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L38) and revoked-index residue defeat full three-mode guarantee. | AUD-036-RAG-006 |
| SC-007 | PARTIAL | [Source](spec.md#L465); [immediate stream](../../apps/api/app/services/simulation/controller_service.py#L692) is unfiltered; repeated fake pairs do not prove zero fabrication on 200 prompts. | AUD-036-RAG-019, AUD-036-RAG-024 |
| SC-008 | PARTIAL | [Source](spec.md#L466); [marker-only lint](../../tools/lint/check_rag_optout_bindings.py#L57) cannot enforce all non-grounded call sites. | AUD-036-RAG-024 |
| SC-009 | PARTIAL | [Source](spec.md#L467); [cache/spool](../../apps/agents/common/offline_cache.py#L340) lacks real fallback/reconnect acknowledgement; 60 seconds unmeasured. | AUD-036-RAG-016, AUD-036-RAG-017 |
| SC-010 | UNVERIFIED | [Source](spec.md#L468); [fake 50-case suite](../../tests/integration/test_jurisdiction_disambiguation.py#L55) does not measure doctrine/agency conflation. | AUD-036-RAG-015, AUD-036-RAG-024 |
| SC-011 | UNVERIFIED | [Source](spec.md#L469); [synthetic replay](../../tests/integration/test_audit_replay.py#L95) is not an attributable one-month historical sample. | AUD-036-RAG-009, AUD-036-RAG-012, AUD-036-RAG-025 |
| SC-012 | UNVERIFIED | [Source](spec.md#L470); [stub validation](quickstart-validation.md#L54) supplies no real pre-grounding/current p95 chat baseline. | AUD-036-RAG-022, AUD-036-RAG-024, AUD-036-RAG-025 |
| SC-013 | UNVERIFIED | [Source](spec.md#L471); [fixture-label tests](../../tests/contract/test_agency_disambiguation.py#L44) do not measure 95% retrieval precision; required tagged subset absent. | AUD-036-RAG-015, AUD-036-RAG-024 |
| SC-014 | UNVERIFIED | [Source](spec.md#L472); [external task](tasks.md#L675) leaves registry population and genuine authority signatures open. | AUD-036-RAG-003, AUD-036-RAG-005, AUD-036-RAG-025 |
| SC-015 | UNVERIFIED | [Source](spec.md#L473); [expected-rank tests](../../tests/contract/test_authority_precedence.py#L44) are not measured national-institution retrieval. | AUD-036-RAG-015, AUD-036-RAG-024 |
| SC-016 | PARTIAL | [Source](spec.md#L474); [quorum tests](../../tests/contract/test_foundry_carveout.py#L75) can use Python substitute; target-prod policy discriminator is wrong. | AUD-036-RAG-005 |
| SC-017 | PARTIAL | [Source](spec.md#L475); [100 builder fixtures](../../tests/contract/test_sc017_override_completeness.py#L111) do not prove all actual override/public-warning events. | AUD-036-RAG-012, AUD-036-RAG-014 |
| SC-018 | PARTIAL | [Source](spec.md#L476); ISM scaffold exists but [export route](../../apps/api/app/api/routes/audit_compliance.py#L132) is unmounted/incorrect and sign-off absent. | AUD-036-RAG-005, AUD-036-RAG-026 |
| SC-019 | PARTIAL | [Source](spec.md#L477); [alias label](../../apps/agents/common/retrieval_client.py#L644) does not pin actual queries; rollback timing/retention unproved. | AUD-036-RAG-009, AUD-036-RAG-010, AUD-036-RAG-024 |

## Acceptance Scenario Coverage

The 38 review keys US1.1 through US10.4 below denote original story-local scenario numbers, not new requirements.

| Scenario | Status | Expected observation and evidence limit | Follow-up |
| --- | --- | --- | --- |
| US1.1 | PARTIAL | [NSW/VIC risk scenario](spec.md#L118): both RFS/CFA sources and audit hashes; [dispatcher](../../apps/agents/dispatcher/agent.py#L209) is ungrounded. | AUD-036-RAG-002, AUD-036-RAG-015 |
| US1.2 | PARTIAL | [NT/QLD cyclone scenario](spec.md#L119): NTES/SES-QLD plus VI-C/ATSI/CALD; [retrieval](../../apps/agents/common/retrieval_client.py#L746) lacks inclusion/agency integration. | AUD-036-RAG-003, AUD-036-RAG-015 |
| US1.3 | PARTIAL | [Multilingual warning](spec.md#L120): AIDR/ARC/Indigenous sources and IC-approval watermark; [inclusion helper](../../apps/agents/communication/grounding.py#L83) is detached. | AUD-036-RAG-002, AUD-036-RAG-014 |
| US1.4 | CONFLICT | [Notifier audit](spec.md#L121): no LLM is supported by [notifier](../../apps/agents/common/dependency_notifier.py#L4), but reason strings/ADR omission disagree. | AUD-036-RAG-012, AUD-036-RAG-024 |
| US1.5 | MISSING | [Tamper response](spec.md#L122): no connected integrity-break/publication-stop/Observer page in [spec writer](../../apps/agents/common/audit.py#L103) or its bounded consumer search. | AUD-036-RAG-012 |
| US2.1 | PARTIAL | [Managed-identity agent request](spec.md#L136): AAD construction exists; actual Foundry call/provider identity and grounding are not proven by [dispatcher source](../../apps/agents/dispatcher/agent.py#L209). | AUD-036-RAG-002, AUD-036-RAG-020 |
| US2.2 | PARTIAL | [CD registry failure](spec.md#L137): [CD invocation](../../.github/workflows/cd.yml#L211) lacks effective plan/current-date/environment enforcement. | AUD-036-RAG-005 |
| US2.3 | PARTIAL | [Simulation metadata/SSE](spec.md#L138): [controller](../../apps/api/app/services/simulation/controller_service.py#L873) omits required metadata on normal wire events and has optional audit. | AUD-036-RAG-012, AUD-036-RAG-019, AUD-036-RAG-020 |
| US2.4 | PARTIAL | [Non-AU precreate denial](spec.md#L139): [checker](../../scripts/verify-carveout.ps1#L89) does not cover complete resolved data-plane resources. | AUD-036-RAG-005 |
| US2.5 | PARTIAL | [PII/PSPF denial](spec.md#L140): [history assembly](../../apps/api/app/services/simulation/controller_service.py#L568) can resend original text after redaction. | AUD-036-RAG-001 |
| US3.1 | PARTIAL | [Doctrine reply/citation events](spec.md#L154): server lists retrieval results but [web event handler](../../apps/web/src/components/simulation-chat-pane.tsx#L484) ignores citations. | AUD-036-RAG-019, AUD-036-RAG-021 |
| US3.2 | PARTIAL | [Simulated warning](spec.md#L155): [tool](../../apps/api/app/services/simulation/controller_service.py#L959) watermarks and returns published=false; complete grounded output/publication guard acceptance not established. | AUD-036-RAG-014, AUD-036-RAG-019 |
| US3.3 | PARTIAL | [Out-of-corpus refusal](spec.md#L156): [empty citation event](../../apps/api/app/services/simulation/controller_service.py#L826) does not force explicit refusal in unfiltered streamed answer. | AUD-036-RAG-019, AUD-036-RAG-021 |
| US3.4 | PARTIAL | [Script/chat separation](spec.md#L157): [scheduler](../../apps/api/app/services/warp_scheduler.py#L130) avoids RAG; adjacent chat grounding remains incomplete. | AUD-036-RAG-019 |
| US4.1 | PARTIAL | [Three-mode index](spec.md#L177): [mode handling](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L38) has unsafe absent-mode and populated-index transitions. | AUD-036-RAG-006 |
| US4.2 | PARTIAL | [Unchanged azd rerun](spec.md#L178): [azd](../../azure.yaml#L14) does not call new ingest hook; [embedding](../../apps/ingest-runner/src/ama_ingest/__main__.py#L387) occurs before skip. | AUD-036-RAG-007, AUD-036-RAG-023 |
| US4.3 | PARTIAL | [Changed source only](spec.md#L179): [indexer](../../apps/ingest-runner/src/ama_ingest/indexer.py#L280) skips by chunk body, not complete pre-embed entry identity. | AUD-036-RAG-006, AUD-036-RAG-007 |
| US4.4 | PARTIAL | [Returned provenance](spec.md#L180): [projection](../../apps/agents/common/retrieval_client.py#L293) can use incomplete/default build/index metadata. | AUD-036-RAG-009, AUD-036-RAG-011 |
| US4.5 | PARTIAL | [Excluded-template lint](spec.md#L181): [licence helper](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L1) does not establish blocking production CI plus bypass-resistant runtime refusal. | AUD-036-RAG-006 |
| US5.1 | CONFLICT | [Notifier reason](spec.md#L195) differs from US1.4/FR wording; [ADR](../../docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md#L29) omits the field. | AUD-036-RAG-013, AUD-036-RAG-024 |
| US5.2 | PARTIAL | [BoM live opt-out](spec.md#L196): [ADR](../../docs/decisions/036-foundry-rag-grounding/02-rag-optout-bom-live.md#L24) is authored, not actual complete forecast-tile audit evidence. | AUD-036-RAG-012, AUD-036-RAG-024 |
| US5.3 | PARTIAL | [GA live opt-out](spec.md#L197): [ADR](../../docs/decisions/036-foundry-rag-grounding/03-rag-optout-ga-live.md#L23) is not an attributable magnitude-update audit record. | AUD-036-RAG-012, AUD-036-RAG-024 |
| US5.4 | PARTIAL | [Pure collection](spec.md#L198): [ADR](../../docs/decisions/036-foundry-rag-grounding/04-rag-optout-planning-collection.md#L23) describes no-RAG but complete path-level reason emission unproved. | AUD-036-RAG-012, AUD-036-RAG-024 |
| US5.5 | PARTIAL | [New ungrounded contributor path](spec.md#L199): [marker-only lint](../../tools/lint/check_rag_optout_bindings.py#L57) misses unmarked calls. | AUD-036-RAG-024 |
| US6.1 | PARTIAL | [Offline centre setup](spec.md#L213): [cache service](../../apps/agents/common/offline_cache.py#L233) has no real fallback/body/topic closure. | AUD-036-RAG-016, AUD-036-RAG-017 |
| US6.2 | PARTIAL | [Reconnect audit](spec.md#L214): [drain](../../apps/agents/common/offline_cache.py#L340) preserves timestamps but lacks durable ack/sync-lag/live-store path. | AUD-036-RAG-017 |
| US7.1 | PARTIAL | [Rural border doctrine](spec.md#L228): [RRF-only retrieval](../../apps/agents/common/retrieval_client.py#L746) does not enforce RFS/CFA without FRNSW plus IC unification handoff. | AUD-036-RAG-015 |
| US7.2 | PARTIAL | [ACT police authority](spec.md#L229): [unused agency helper](../../apps/agents/common/retrieval_client.py#L345) cannot establish concurrent/legislative-source disambiguation. | AUD-036-RAG-015 |
| US7.3 | PARTIAL | [Transport and utility sources](spec.md#L230): [fixture labels](../../tests/integration/test_jurisdiction_disambiguation.py#L55) do not establish paired real agency doctrine. | AUD-036-RAG-015, AUD-036-RAG-024 |
| US8.1 | PARTIAL | [Community-triggered warning](spec.md#L242): [inclusion helper](../../apps/agents/communication/grounding.py#L83) is not used before transformation/approval. | AUD-036-RAG-002, AUD-036-RAG-003, AUD-036-RAG-014 |
| US8.2 | PARTIAL | [Accessible protocol citations](spec.md#L243): [fake topic test](../../tests/integration/test_communication_agent_atsi_cald.py#L78) does not prove ARC/Auslan/Easy-Read/TIS output annotations. | AUD-036-RAG-002, AUD-036-RAG-015 |
| US9.1 | PARTIAL | [No-consent suppression](spec.md#L255): [gate](../../apps/agents/common/cultural_authority_gate.py#L49) is not on shared retrieval/cache path. | AUD-036-RAG-003 |
| US9.2 | PARTIAL | [Council-scoped consent](spec.md#L256): [registry](../../apps/agents/common/cultural_authority_registry.py#L175) does not bind requested council/tenant/grant start with real signature. | AUD-036-RAG-003 |
| US9.3 | UNVERIFIED | [Production cultural approval](spec.md#L257): [T202](tasks.md#L675) is external/open; names or placeholders cannot establish NEMA/AFAC/three representatives' approval. | AUD-036-RAG-005, AUD-036-RAG-025 |
| US10.1 | PARTIAL | [NSW rural query](spec.md#L269): [agency filter](../../apps/agents/common/retrieval_client.py#L345) has no production caller; expected RFS/not-FRNSW not demonstrated. | AUD-036-RAG-015 |
| US10.2 | PARTIAL | [Sydney urban query](spec.md#L270): [retrieval](../../apps/agents/common/retrieval_client.py#L746) lacks operative agency-role constraint. | AUD-036-RAG-015 |
| US10.3 | PARTIAL | [Parliament House precedence](spec.md#L271): [global helper](../../apps/agents/common/retrieval_client.py#L553) does not rank the actual incident query. | AUD-036-RAG-015 |
| US10.4 | PARTIAL | [Conflicting authority card](spec.md#L272): [wrapper](../../apps/web/src/components/recommendations/recommendation-card.tsx#L40) is unmounted and lacks required precedence/conflict trace. | AUD-036-RAG-015, AUD-036-RAG-021 |

## Checklist Accounting

All 342 original CHK definitions are accounted individually. There are 165 checked and 177 unchecked originals.
CHK IDs are globally unique at this revision, but file identity and exact line are retained. The checklist README has
no item definitions. Its claim of 339 omits the three appended backfill items. No original checklist was changed.

These are predominantly tests of the specification's English, as their preambles say. IMPLEMENTED here credits a
documented constraint/traceability link or authored artifact, not operational compliance. PARTIAL/CONFLICT identifies
an incomplete or contradictory answer to the question; runtime and human-review claims without proof are UNVERIFIED.
The linked item provides its exact question; the cited follow-up contains owning source and concrete remediation.

### Requirements Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [x] | PARTIAL | [Item](checklists/requirements.md#L17): anchors are explicit; amendments add detailed implementation choices beyond the original claim. | AUD-036-RAG-025 |
| CHK002 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L19): stories state user value and life-safety needs. | - |
| CHK003 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L20): operational stories explain stakeholder purpose. | - |
| CHK004 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L21): mandatory sections exist, including renamed Closed Questions. | - |
| CHK005 | [x] | PARTIAL | [Item](checklists/requirements.md#L25): resolutions are authored; later contract conflicts invalidate blanket closure. | AUD-036-RAG-013, AUD-036-RAG-025 |
| CHK006 | [x] | CONFLICT | [Item](checklists/requirements.md#L26): stale 43-FR/seven-family count; actual 68/fifteen and ambiguous contracts. | AUD-036-RAG-025 |
| CHK007 | [x] | PARTIAL | [Item](checklists/requirements.md#L27): numerical criteria exist, but nineteen rather than twelve; measured gates incomplete. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK008 | [x] | PARTIAL | [Item](checklists/requirements.md#L28): several SCs prescribe OPA/schema/path details rather than only outcomes. | AUD-036-RAG-025 |
| CHK009 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L29): all 38 scenarios use Given/When/Then. | - |
| CHK010 | [x] | CONFLICT | [Item](checklists/requirements.md#L30): ten explicit edges, not the claimed twelve. | AUD-036-RAG-025 |
| CHK011 | [x] | CONFLICT | [Item](checklists/requirements.md#L31): actual eight exclusions/twelve assumptions, not seven/eight. | AUD-036-RAG-025 |
| CHK012 | [x] | PARTIAL | [Item](checklists/requirements.md#L32): most dependencies inspectable; persona inputs and platform assumptions unproved. | AUD-036-RAG-025 |
| CHK013 | [x] | PARTIAL | [Item](checklists/requirements.md#L36): acceptance targets exist; incompatible contracts/gate definitions prevent complete clarity. | AUD-036-RAG-013 |
| CHK014 | [x] | CONFLICT | [Item](checklists/requirements.md#L37): coverage expanded to ten stories; six-agent/eight-story summary is stale. | AUD-036-RAG-025 |
| CHK015 | [x] | PARTIAL | [Item](checklists/requirements.md#L38): source ties stories to SCs, but analysis and task mappings drift. | AUD-036-RAG-025 |
| CHK016 | [x] | PARTIAL | [Item](checklists/requirements.md#L39): same qualified implementation-detail issue as CHK001. | AUD-036-RAG-025 |
| CHK017 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L43): embedding model and 3072 dimensions explicitly bound. | - |
| CHK018 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L44): SDK and cognitive-services token scope explicitly named; current SDK exceptions are separate conflict. | AUD-036-RAG-020 |
| CHK019 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L45): 95% categorical/100% schema regression definition retained after hard cutover. | AUD-036-RAG-024 |
| CHK020 | [x] | CONFLICT | [Item](checklists/requirements.md#L46): research, ingest contract and rollback amendment name different parity signals. | AUD-036-RAG-008, AUD-036-RAG-013 |
| CHK021 | [x] | PARTIAL | [Item](checklists/requirements.md#L47): default/agent thresholds authored, but not consumed or measured. | AUD-036-RAG-019, AUD-036-RAG-022 |
| CHK022 | [x] | PARTIAL | [Item](checklists/requirements.md#L48): examples exist; complete payload/default-deny semantics are not enforced. | AUD-036-RAG-001 |
| CHK023 | [x] | CONFLICT | [Item](checklists/requirements.md#L49): warning/14-day/30-day override and signed-manifest contracts need reconciliation. | AUD-036-RAG-013, AUD-036-RAG-017 |
| CHK024 | [x] | PARTIAL | [Item](checklists/requirements.md#L50): quantitative thresholds exist, but count/sample attribution is stale/incomplete. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK025 | [x] | PARTIAL | [Item](checklists/requirements.md#L51): 70% not implemented against a valid utilization metric. | AUD-036-RAG-022 |
| CHK026 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L55): spec edge and IDX-04 explicitly agree on blue-green/no mixed models. | AUD-036-RAG-007 |
| CHK027 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L56): jurisdiction enum and union are consistent in the authored requirement. | - |
| CHK028 | [x] | PARTIAL | [Item](checklists/requirements.md#L57): envelope can represent references; actual prompt/SSE/UI formatting and validation diverge. | AUD-036-RAG-019, AUD-036-RAG-021 |
| CHK029 | [x] | PARTIAL | [Item](checklists/requirements.md#L58): numeric matcher admits NS-09; no complete unmarked-call discovery. | AUD-036-RAG-024 |
| CHK030 | [x] | CONFLICT | [Item](checklists/requirements.md#L59): amended audit lists/schema/model and mounted simulation emission disagree. | AUD-036-RAG-012, AUD-036-RAG-013 |
| CHK031 | [x] | SUPERSEDED | [Item](checklists/requirements.md#L60): activation-coupled lint timing explicitly replaced by Session 6; zero-import policy remains unresolved. | AUD-036-RAG-020, AUD-036-RAG-025 |
| CHK032 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L61): three migration anchor filenames are consistently identified. | - |
| CHK033 | [x] | CONFLICT | [Item](checklists/requirements.md#L62): original/amended entities contain incompatible fields/nullability. | AUD-036-RAG-013 |
| CHK034 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L66): source SCs cite stories/FRs; historical analysis mislabels them separately. | AUD-036-RAG-025 |
| CHK035 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L67): scenarios name observable artifacts/actions. | - |
| CHK036 | [x] | PARTIAL | [Item](checklists/requirements.md#L68): independent tests exist for US1-US7, absent for US8-US10. | AUD-036-RAG-025 |
| CHK037 | [x] | PARTIAL | [Item](checklists/requirements.md#L69): thresholds are written, but several real gates absent or self-confirming. | AUD-036-RAG-024 |
| CHK038 | [x] | PARTIAL | [Item](checklists/requirements.md#L70): p95/relative baseline identified, no attributable pre-grounding measurement/window fixture. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK039 | [x] | PARTIAL | [Item](checklists/requirements.md#L71): month/95% stated; sample definition and actual historical reproduction incomplete. | AUD-036-RAG-012, AUD-036-RAG-025 |
| CHK040 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L75): five decision agents, notifier and simulation are covered in story text. | - |
| CHK041 | [x] | PARTIAL | [Item](checklists/requirements.md#L76): ten explicit edges plus amendment interactions; not twelve enumerated mapped edges. | AUD-036-RAG-025 |
| CHK042 | [x] | PARTIAL | [Item](checklists/requirements.md#L77): quota fallback policy written; current full-envelope/registry audit path absent. | AUD-036-RAG-001, AUD-036-RAG-005 |
| CHK043 | [x] | PARTIAL | [Item](checklists/requirements.md#L78): tamper/publication/page appears in US1.5 but lacks complete controlling implementation/FR gate. | AUD-036-RAG-012 |
| CHK044 | [x] | PARTIAL | [Item](checklists/requirements.md#L79): rollback intent defined; actual retained state/promotion recovery incomplete. | AUD-036-RAG-008, AUD-036-RAG-010 |
| CHK045 | [x] | CONFLICT | [Item](checklists/requirements.md#L80): expired/stale/extended-cache and no-silencing behavior need an explicit reconciled boundary. | AUD-036-RAG-013, AUD-036-RAG-017 |
| CHK046 | [x] | PARTIAL | [Item](checklists/requirements.md#L81): revocation question remains material; existing body documents survive mode changes. | AUD-036-RAG-006 |
| CHK047 | [x] | PARTIAL | [Item](checklists/requirements.md#L82): fake-production rejection is proposed in risk controls, not established at actual composition. | AUD-036-RAG-020, AUD-036-RAG-024 |
| CHK048 | [x] | PARTIAL | [Item](checklists/requirements.md#L83): partial ingestion/upload failure is not atomically prevented from promotion. | AUD-036-RAG-007, AUD-036-RAG-008 |
| CHK049 | [x] | UNVERIFIED | [Item](checklists/requirements.md#L87): operational themes are written; original memo consultation unavailable. | AUD-036-RAG-025 |
| CHK050 | [x] | UNVERIFIED | [Item](checklists/requirements.md#L88): sector themes exist; original agency memos not found in bounded search. | AUD-036-RAG-025 |
| CHK051 | [x] | UNVERIFIED | [Item](checklists/requirements.md#L89): Commonwealth themes/opt-outs cited, not independently attributable consultation. | AUD-036-RAG-025 |
| CHK052 | [x] | UNVERIFIED | [Item](checklists/requirements.md#L90): cross-sector summaries cannot prove completeness without source memos. | AUD-036-RAG-025 |
| CHK053 | [x] | PARTIAL | [Item](checklists/requirements.md#L91): explicit opt-out mapping exists but audit vocabulary/marker-optional ADRs conflict. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK054 | [x] | UNVERIFIED | [Item](checklists/requirements.md#L92): no-orphan original persona coverage cannot be established from missing inputs. | AUD-036-RAG-025 |
| CHK055 | [x] | PARTIAL | [Item](checklists/requirements.md#L93): agency cases specified, original memo provenance and actual ranking incomplete. | AUD-036-RAG-015, AUD-036-RAG-025 |
| CHK056 | [x] | PARTIAL | [Item](checklists/requirements.md#L94): cross-sector scenarios exist, but actual paired retrieval/complete memo evidence absent. | AUD-036-RAG-015, AUD-036-RAG-025 |
| CHK057 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L95): named classified agencies/levels explicitly bounded in FR-NS-07. Runtime enforcement remains partial. | AUD-036-RAG-001 |
| CHK058 | [x] | PARTIAL | [Item](checklists/requirements.md#L96): offline autonomy is written; original memo and mounted decision/reconnect behavior incomplete. | AUD-036-RAG-017, AUD-036-RAG-025 |
| CHK059 | [x] | PARTIAL | [Item](checklists/requirements.md#L97): inclusion asks appear in AG-06/US8; actual pre-draft retrieval is absent. | AUD-036-RAG-002 |
| CHK060 | [x] | PARTIAL | [Item](checklists/requirements.md#L101): registry reuse explicit, but amended schema/version/quorum parity diverges. | AUD-036-RAG-005, AUD-036-RAG-013 |
| CHK061 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L102): private-only requirement inherited explicitly; selected configuration contradicts it. | AUD-036-RAG-004 |
| CHK062 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L103): predecessor migration/historical status explicitly recorded. | - |
| CHK063 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L104): simulation extension explicitly preserves prior safeguards. Integrated proof remains unverified. | AUD-036-RAG-019 |
| CHK064 | [x] | PARTIAL | [Item](checklists/requirements.md#L105): factory signature retained but callable seam/configuration contract is not. | AUD-036-RAG-020 |
| CHK065 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L106): eval-runner reference wrapper explicitly cited. | - |
| CHK066 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L107): relationship section preserves predecessor IDs and extends scope explicitly. | - |
| CHK067 | [x] | PARTIAL | [Item](checklists/requirements.md#L108): spec029 cited; current local flags lack its complete mutation/audit behavior. | AUD-036-RAG-002, AUD-036-RAG-015 |
| CHK068 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L112): exclusions identify concrete boundaries; stale count is separately tracked. | AUD-036-RAG-025 |
| CHK069 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L113): added grounding context distinguished from prompt rewrite. | - |
| CHK070 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L114): ingest rebuild need not modify corpus builder; retain this boundary in repairs. | AUD-036-RAG-011 |
| CHK071 | [x] | CONFLICT | [Item](checklists/requirements.md#L115): registry reuse asserted while amended schema/root requirements diverge. | AUD-036-RAG-005, AUD-036-RAG-013 |
| CHK072 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L116): controller prompt/tool preservation is explicitly separate from retrieval hooks. | - |
| CHK073 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L117): live BoM/GA/DACC client replacement explicitly excluded. | - |
| CHK074 | [x] | PARTIAL | [Item](checklists/requirements.md#L118): follow-on/human boundaries written, but authoritative tracking/evidence incomplete. | AUD-036-RAG-025 |
| CHK075 | [x] | PARTIAL | [Item](checklists/requirements.md#L119): in-scope plumbing versus excluded content/registry redesign needs amendment reconciliation. | AUD-036-RAG-013, AUD-036-RAG-025 |
| CHK076 | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L123): stable FR family/number IDs, including suffixes, are retained. | - |
| CHK077 | [x] | PARTIAL | [Item](checklists/requirements.md#L124): headings cover fifteen families; seven-family summary stale. | AUD-036-RAG-025 |
| CHK078 | [x] | CONFLICT | [Item](checklists/requirements.md#L125): later cutover answers are not reconciled with original FM-06 body and task narrative. | AUD-036-RAG-020, AUD-036-RAG-025 |
| CHK079 | [x] | CONFLICT | [Item](checklists/requirements.md#L126): no-open-question claim conflicts with measurable schema/gate/authority ambiguities. | AUD-036-RAG-013, AUD-036-RAG-025 |
| CHK080 | [x] | PARTIAL | [Item](checklists/requirements.md#L127): platform assumptions/sign-offs/persona inputs are not established by file existence. | AUD-036-RAG-025 |
| CHK081 | [x] | PARTIAL | [Item](checklists/requirements.md#L128): authority citations are authored; missing original memos prevent full attribution. | AUD-036-RAG-025 |
| CHK082 | [x] | PARTIAL | [Item](checklists/requirements.md#L129): entities referenced but original/amended field counts and consumer linkage differ. | AUD-036-RAG-013 |
| CHK297 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L159): US9/US10 are explicitly P1; no requirement here is silently demoted. | - |
| CHK298 | [ ] | MISSING | [Item](checklists/requirements.md#L160): US9/US10 lack the requested independent-test sections. | AUD-036-RAG-025 |
| CHK299 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L161): seven added SCs cite their FR/story sources. | - |
| CHK300 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L165): new family headings are present. | - |
| CHK301 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L166): pre-amend identifiers are retained; new suffix/new family additions do not renumber them. | - |
| CHK302 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L170): OOS-8 distinguishes human content from in-scope plumbing. | - |
| CHK303 | [ ] | PARTIAL | [Item](checklists/requirements.md#L171): named surfaces exist but migration, flag and actual authority assumptions remain unproved. | AUD-036-RAG-013, AUD-036-RAG-025 |
| CHK304 | [ ] | PARTIAL | [Item](checklists/requirements.md#L172): written authority pointers exist; missing R3 source memos limit attribution. | AUD-036-RAG-025 |
| CHK305 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L176): A11 lists eight amended ADRs matching the FR references. | - |
| CHK306 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L177): marker/stub/body ownership is explicitly recorded. | - |
| CHK307 | [ ] | PARTIAL | [Item](checklists/requirements.md#L181): Q-P1/Q-P2 targets are logged; unresolved cross-artifact conflicts remain. | AUD-036-RAG-013, AUD-036-RAG-025 |
| CHK308 | [ ] | PARTIAL | [Item](checklists/requirements.md#L182): amendment interactions have FRs, but the explicit edge section and implementation do not close them. | AUD-036-RAG-003, AUD-036-RAG-009, AUD-036-RAG-018 |
| CHK309 | [ ] | CONFLICT | [Item](checklists/requirements.md#L186): random conflict IDs, mutable cache provenance and incompatible audit schemas undermine replay determinism. | AUD-036-RAG-009, AUD-036-RAG-013, AUD-036-RAG-018 |
| CHK340 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L192): IDX-01 precisely names the corpus tree; indexing completeness still partial. | AUD-036-RAG-006, AUD-036-RAG-023 |
| CHK341 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L193): inventory path/columns/CI obligation explicit; implemented checker is narrower. | AUD-036-RAG-006 |
| CHK342 | [ ] | IMPLEMENTED | [Item](checklists/requirements.md#L194): scripted/no-RAG versus free-chat/grounded distinction explicitly specified. | AUD-036-RAG-019 |

### Migration Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK083 | [x] | SUPERSEDED | [Item](checklists/migration.md#L18): gradual activation flag binding retired by Session 6, not regression/kill-switch semantics. | AUD-036-RAG-002, AUD-036-RAG-025 |
| CHK084 | [x] | PARTIAL | [Item](checklists/migration.md#L19): FR023 bar retained, real nonempty candidate/baseline gate missing. | AUD-036-RAG-024 |
| CHK085 | [x] | PARTIAL | [Item](checklists/migration.md#L20): legacy fallback exists, but actual dispatcher/MAF grounding path does not preserve all intended controls. | AUD-036-RAG-002, AUD-036-RAG-020 |
| CHK086 | [x] | SUPERSEDED | [Item](checklists/migration.md#L21): original atomic activation/deletion sequencing explicitly replaced; SDK zero-import conflict remains. | AUD-036-RAG-020, AUD-036-RAG-025 |
| CHK087 | [x] | UNVERIFIED | [Item](checklists/migration.md#L22): no actual staging rollback/no-audit-gap drill established. | AUD-036-RAG-025 |
| CHK088 | [x] | IMPLEMENTED | [Item](checklists/migration.md#L23): categorical equivalence and schema thresholds defined; measurement absent. | AUD-036-RAG-024 |
| CHK089 | [x] | PARTIAL | [Item](checklists/migration.md#L24): health signals/alerts authored, active data/export chain incomplete. | AUD-036-RAG-022 |
| CHK090 | [x] | SUPERSEDED | [Item](checklists/migration.md#L25): specified canary ordering retired explicitly, not inferred from missing machinery. | AUD-036-RAG-025 |
| CHK091 | [x] | PARTIAL | [Item](checklists/migration.md#L26): rotation/current permissions do not bind all transports or actual deployment plan. | AUD-036-RAG-001, AUD-036-RAG-005 |
| CHK092 | [x] | PARTIAL | [Item](checklists/migration.md#L27): current kill-switch changes lack complete durable flag/provenance events. | AUD-036-RAG-002, AUD-036-RAG-012 |
| CHK093 | [x] | PARTIAL | [Item](checklists/migration.md#L33): protocol/fake tests exist; all consumers are not exercised via the promised seam. | AUD-036-RAG-020, AUD-036-RAG-024 |
| CHK094 | [x] | PARTIAL | [Item](checklists/migration.md#L34): base response types exist but tools/safety/deployment/correlation projection incomplete. | AUD-036-RAG-020 |
| CHK095 | [x] | PARTIAL | [Item](checklists/migration.md#L35): sync injection works; controller/MAF do not provide required transport injection. | AUD-036-RAG-020 |
| CHK096 | [x] | PARTIAL | [Item](checklists/migration.md#L36): all three anchors exist, but real dispatcher adds another unchecked transport path. | AUD-036-RAG-002, AUD-036-RAG-020 |
| CHK097 | [x] | PARTIAL | [Item](checklists/migration.md#L37): some artifacts label hermetic/live; fake pass claims still overstate acceptance. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK098 | [x] | IMPLEMENTED | [Item](checklists/migration.md#L38): reference injection design is explicit in contract. | AUD-036-RAG-020 |
| CHK099 | [x] | PARTIAL | [Item](checklists/migration.md#L39): constructors do not expose one consistent callable/streaming seam. | AUD-036-RAG-020 |
| CHK100 | [x] | PARTIAL | [Item](checklists/migration.md#L40): absent endpoint can select offline/ungrounded modes without required explicit failure provenance. | AUD-036-RAG-002, AUD-036-RAG-020 |
| CHK101 | [x] | PARTIAL | [Item](checklists/migration.md#L46): defined citation segments are not verified against every emitted claim. | AUD-036-RAG-019 |
| CHK102 | [x] | PARTIAL | [Item](checklists/migration.md#L47): optional audit projection does not match all mounted output paths. | AUD-036-RAG-012 |
| CHK103 | [x] | PARTIAL | [Item](checklists/migration.md#L48): card links exist but absent/expired/page-missing source fallback unproved. | AUD-036-RAG-021 |
| CHK104 | [x] | PARTIAL | [Item](checklists/migration.md#L49): SSE citation events are ignored by the real chat handler. | AUD-036-RAG-021 |
| CHK105 | [x] | PARTIAL | [Item](checklists/migration.md#L50): no complete hermetic retrieve/infer/filter/audit/UI chain. | AUD-036-RAG-019, AUD-036-RAG-024 |
| CHK106 | [x] | PARTIAL | [Item](checklists/migration.md#L51): genuine cross-page/missing-anchor handling not enforced by current chunker/card. | AUD-036-RAG-011, AUD-036-RAG-021 |
| CHK107 | [x] | PARTIAL | [Item](checklists/migration.md#L52): standalone SHA filter is not publication-time suppression. | AUD-036-RAG-019 |
| CHK108 | [x] | CONFLICT | [Item](checklists/migration.md#L53): PDF/source, rendered body, build and projected chunk hashes are not reconciled. | AUD-036-RAG-011, AUD-036-RAG-013 |
| CHK109 | [x] | PARTIAL | [Item](checklists/migration.md#L54): URL fields defined but forged-metadata/empty URL and runtime resolution remain. | AUD-036-RAG-019, AUD-036-RAG-021 |
| CHK110 | [x] | PARTIAL | [Item](checklists/migration.md#L55): entity/card restrict snippets; source rights defaults/revocation still bypass intended contract. | AUD-036-RAG-006 |
| CHK111 | [x] | PARTIAL | [Item](checklists/migration.md#L56): build SHA differs across workflow/manifest/default live projection. | AUD-036-RAG-009, AUD-036-RAG-011 |
| CHK112 | [x] | PARTIAL | [Item](checklists/migration.md#L57): embedding identity/cost/per-call provenance not durably emitted. | AUD-036-RAG-011, AUD-036-RAG-012 |
| CHK113 | [x] | PARTIAL | [Item](checklists/migration.md#L58): historical source unavailability/replay fallback lacks a complete preserved snapshot path. | AUD-036-RAG-011, AUD-036-RAG-012 |
| CHK310 | [ ] | PARTIAL | [Item](checklists/migration.md#L87): authority/agency metadata dropped before actual card/SSE display. | AUD-036-RAG-015, AUD-036-RAG-021 |
| CHK311 | [ ] | PARTIAL | [Item](checklists/migration.md#L88): tie trace not integrated through retrieval/audit/UI. | AUD-036-RAG-012, AUD-036-RAG-015 |
| CHK312 | [ ] | PARTIAL | [Item](checklists/migration.md#L89): protected-content suppression notice lacks a real gated UI consumer. | AUD-036-RAG-003, AUD-036-RAG-021 |
| CHK313 | [ ] | PARTIAL | [Item](checklists/migration.md#L93): concrete index/build pair may be default/relabeled rather than actual query identity. | AUD-036-RAG-009 |
| CHK314 | [ ] | PARTIAL | [Item](checklists/migration.md#L94): conflict recommendations/audit IDs not propagated to mounted UI. | AUD-036-RAG-018, AUD-036-RAG-021 |
| CHK315 | [ ] | PARTIAL | [Item](checklists/migration.md#L98): amendments tested as helpers, not end-to-end constructor seams. | AUD-036-RAG-020, AUD-036-RAG-024 |
| CHK316 | [ ] | PARTIAL | [Item](checklists/migration.md#L102): activation superseded, mixed-schema regression remains and is unproved. | AUD-036-RAG-013, AUD-036-RAG-024 |
| CHK317 | [ ] | PARTIAL | [Item](checklists/migration.md#L103): retained kill-switch/inference audit fields are not emitted on all real paths. | AUD-036-RAG-002, AUD-036-RAG-012 |
| CHK318 | [ ] | CONFLICT | [Item](checklists/migration.md#L104): legacy-null/schema equivalence contradicted by new required index and non-null ties. | AUD-036-RAG-013 |
| CHK319 | [ ] | PARTIAL | [Item](checklists/migration.md#L108): mutable process flags do not supply required durable actor/change-reason trail. | AUD-036-RAG-012, AUD-036-RAG-015, AUD-036-RAG-018 |

### Compliance Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK114 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L18): NN-2 is explicitly the governing authority. | - |
| CHK115 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L19): life-safety/no-silencing authority is explicit. | - |
| CHK116 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L20): auditability authority is explicitly cited. | - |
| CHK117 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L21): warning/public-information authority cited. | - |
| CHK118 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L22): vulnerable-population authority cited. | - |
| CHK119 | [x] | PARTIAL | [Item](checklists/compliance.md#L23): effective deployment/current registry pointer missing for some actual transport paths. | AUD-036-RAG-001, AUD-036-RAG-005 |
| CHK120 | [x] | PARTIAL | [Item](checklists/compliance.md#L24): life-safety citation requirements written but dispatcher/UI do not expose doctrine. | AUD-036-RAG-002, AUD-036-RAG-021 |
| CHK121 | [x] | PARTIAL | [Item](checklists/compliance.md#L25): degraded/error/deny/rollback paths lack complete durable audit emission. | AUD-036-RAG-012, AUD-036-RAG-017 |
| CHK122 | [x] | CONFLICT | [Item](checklists/compliance.md#L26): original and amended registry schemas/policy disagree. | AUD-036-RAG-005, AUD-036-RAG-013 |
| CHK123 | [x] | PARTIAL | [Item](checklists/compliance.md#L27): required services listed; checker does not validate all resolved resources. | AUD-036-RAG-005 |
| CHK124 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L28): A6 explicitly forbids widening the inference-only carve-out by interpretation. | - |
| CHK125 | [x] | PARTIAL | [Item](checklists/compliance.md#L29): public-output review stated but actual draft/final actor chain incomplete. | AUD-036-RAG-014 |
| CHK126 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L35): Search requirement explicitly narrows location to Australia East. | AUD-036-RAG-004 |
| CHK127 | [x] | CONFLICT | [Item](checklists/compliance.md#L36): active root permits public access despite private-only claim. | AUD-036-RAG-004 |
| CHK128 | [x] | UNVERIFIED | [Item](checklists/compliance.md#L37): no deployed replication evidence; required plan/resource posture gate incomplete. | AUD-036-RAG-004, AUD-036-RAG-005 |
| CHK129 | [x] | PARTIAL | [Item](checklists/compliance.md#L38): complete current registry policy not enforced at every transport. | AUD-036-RAG-001, AUD-036-RAG-005 |
| CHK130 | [x] | PARTIAL | [Item](checklists/compliance.md#L39): both directions required; response/system/tool/history coverage absent. | AUD-036-RAG-001 |
| CHK131 | [x] | PARTIAL | [Item](checklists/compliance.md#L40): region/carve-out/decision/reason are not durably present on all denied calls. | AUD-036-RAG-001, AUD-036-RAG-012 |
| CHK132 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L41): regulated-data categories explicitly named in authority/scope. Actual compliance unverified. | AUD-036-RAG-005 |
| CHK133 | [x] | PARTIAL | [Item](checklists/compliance.md#L42): precreation denial required but CD lacks complete resolved plan validation. | AUD-036-RAG-005 |
| CHK134 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L48): nine ADR references/bodies exist; content conflicts are separately assessed. | AUD-036-RAG-024 |
| CHK135 | [x] | PARTIAL | [Item](checklists/compliance.md#L49): matcher shape specified, but marker-optional ADR and incomplete call inventory disagree. | AUD-036-RAG-024 |
| CHK136 | [x] | CONFLICT | [Item](checklists/compliance.md#L50): notifier/Observer/classified reason strings differ among story, ADR and schema. | AUD-036-RAG-013, AUD-036-RAG-024 |
| CHK137 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L51): NS-09 fits the existing numeric matcher; total call coverage is a separate defect. | AUD-036-RAG-024 |
| CHK138 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L52): ADR names/IDs enumerated and preserved. | - |
| CHK139 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L53): read-only/replay/verification/dashboard scope explicitly named. | - |
| CHK140 | [x] | UNVERIFIED | [Item](checklists/compliance.md#L54): memo citations authored but source memos unavailable. | AUD-036-RAG-025 |
| CHK141 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L55): no-regrounding cost/provenance/hallucination rationale is explicit. | - |
| CHK142 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L56): NS-08 stability explicitly retained when NS-09 was added. | - |
| CHK143 | [x] | PARTIAL | [Item](checklists/compliance.md#L57): opt-out fields present but schema vocabulary/actual emissions disagree. | AUD-036-RAG-013, AUD-036-RAG-024 |
| CHK144 | [x] | PARTIAL | [Item](checklists/compliance.md#L58): new-path failure requirement is stated but marker-only lint cannot enforce it. | AUD-036-RAG-024 |
| CHK145 | [x] | IMPLEMENTED | [Item](checklists/compliance.md#L64): blue-green-only model changes specified; live provider does not enforce them. | AUD-036-RAG-007 |
| CHK146 | [x] | PARTIAL | [Item](checklists/compliance.md#L65): 24-hour rebuild target lacks actual measured frozen-snapshot lifecycle. | AUD-036-RAG-011, AUD-036-RAG-025 |
| CHK147 | [x] | PARTIAL | [Item](checklists/compliance.md#L66): under-60-second atomicity specified but actual Search queries remain alias-bound. | AUD-036-RAG-009 |
| CHK148 | [x] | PARTIAL | [Item](checklists/compliance.md#L67): cleanup exists without flip-relative durable retention/schedule. | AUD-036-RAG-010 |
| CHK149 | [x] | CONFLICT | [Item](checklists/compliance.md#L68): parity signal sets/thresholds differ across authoritative local inputs. | AUD-036-RAG-008, AUD-036-RAG-013 |
| CHK150 | [x] | PARTIAL | [Item](checklists/compliance.md#L69): cache/query/build provenance is not preserved faithfully across flips. | AUD-036-RAG-009, AUD-036-RAG-011 |
| CHK151 | [x] | UNVERIFIED | [Item](checklists/compliance.md#L70): no attributable first-ingest/two-index capacity sizing evidence; alert metric is wrong. | AUD-036-RAG-022, AUD-036-RAG-025 |
| CHK152 | [x] | PARTIAL | [Item](checklists/compliance.md#L71): later manual rollback authority explicit; actual service/events/role gate detached. | AUD-036-RAG-010 |
| CHK153 | [x] | PARTIAL | [Item](checklists/compliance.md#L72): intent separates within-version idempotency/rebuilds; real live-state handling does not. | AUD-036-RAG-007 |
| CHK154 | [x] | PARTIAL | [Item](checklists/compliance.md#L73): single-model guard samples only part of index and follows unsafe writes. | AUD-036-RAG-007, AUD-036-RAG-008 |
| CHK155 | [x] | PARTIAL | [Item](checklists/compliance.md#L79): manifest estimates are not actual signed payload/device footprint enforcement. | AUD-036-RAG-016 |
| CHK156 | [x] | CONFLICT | [Item](checklists/compliance.md#L80): age encryption does not establish an authenticated detached author signature. | AUD-036-RAG-013, AUD-036-RAG-016 |
| CHK157 | [x] | PARTIAL | [Item](checklists/compliance.md#L81): TTL checked only on load; automatic audited refresh/reconnect is not composed. | AUD-036-RAG-017 |
| CHK158 | [x] | PARTIAL | [Item](checklists/compliance.md#L82): closed topic list specified but offline retrieval ignores question/topic. | AUD-036-RAG-017 |
| CHK159 | [x] | PARTIAL | [Item](checklists/compliance.md#L83): timestamp-preserving spool exists without durable central ack/sync-lag/review. | AUD-036-RAG-017 |
| CHK160 | [x] | PARTIAL | [Item](checklists/compliance.md#L84): key rotation/manifest approval/provisioning chain is not operationally established. | AUD-036-RAG-016, AUD-036-RAG-025 |
| CHK161 | [x] | CONFLICT | [Item](checklists/compliance.md#L85): 11-day cache warning, 7/14-day corpus UI and optional 30-day override need distinct signed semantics. | AUD-036-RAG-013, AUD-036-RAG-017 |
| CHK162 | [x] | PARTIAL | [Item](checklists/compliance.md#L86): unsupported offline-topic refusal is not implemented at actual retrieval. | AUD-036-RAG-017 |
| CHK163 | [x] | PARTIAL | [Item](checklists/compliance.md#L87): callback checks exist but verifier script can skip a missing chain and succeed. | AUD-036-RAG-016 |
| CHK164 | [x] | PARTIAL | [Item](checklists/compliance.md#L88): dual fields declared; manifest/producer/consumer authenticated byte binding incomplete. | AUD-036-RAG-013, AUD-036-RAG-016 |
| CHK165 | [x] | PARTIAL | [Item](checklists/compliance.md#L89): unequal-expiry/key-availability behavior lacks real verification fixtures/policy. | AUD-036-RAG-016 |
| CHK320 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L121): prod-three/dev-two rule explicitly in FR-CV-01. | AUD-036-RAG-005 |
| CHK321 | [ ] | CONFLICT | [Item](checklists/compliance.md#L122): unknown/missing row environments fall to dev semantics rather than fail closed on target. | AUD-036-RAG-005 |
| CHK322 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L123): concrete Rego source path is cited; historical line numbers are not proof of behavior. | - |
| CHK323 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L124): test home named and present. | AUD-036-RAG-005 |
| CHK324 | [ ] | PARTIAL | [Item](checklists/compliance.md#L125): same-PR constraint exists but current manual workflow does not enforce real PR coupling. | AUD-036-RAG-005 |
| CHK325 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L126): the three documented exit-code/quorum scenarios agree; actual policy execution unverified. | AUD-036-RAG-005 |
| CHK326 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L132): concrete query pinning is a MUST, not optional guidance. | AUD-036-RAG-009 |
| CHK327 | [ ] | CONFLICT | [Item](checklists/compliance.md#L133): required current index field versus nullable legacy/offline contract is inconsistent. | AUD-036-RAG-013 |
| CHK328 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L134): Service Bus emission explicitly starts rollback clock. | AUD-036-RAG-010 |
| CHK329 | [ ] | CONFLICT | [Item](checklists/compliance.md#L135): calls three listed failure conditions four; parity definitions/sample windows disagree. | AUD-036-RAG-008, AUD-036-RAG-013 |
| CHK330 | [ ] | PARTIAL | [Item](checklists/compliance.md#L136): rollback shape written but durable standard audit integration absent. | AUD-036-RAG-010, AUD-036-RAG-012 |
| CHK331 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L137): later manual approval rule and A12 agree; supersedes earlier automatic research branch. | AUD-036-RAG-010 |
| CHK332 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L138): SC-019 explicitly references the pinning invariant. | AUD-036-RAG-009 |
| CHK333 | [ ] | PARTIAL | [Item](checklists/compliance.md#L144): workflow named but schedule absent and UTC/AEST conversion incorrect in prose. | AUD-036-RAG-023, AUD-036-RAG-025 |
| CHK334 | [ ] | PARTIAL | [Item](checklists/compliance.md#L145): deletion/revocation drift can leave indexed residue. | AUD-036-RAG-006, AUD-036-RAG-023 |
| CHK335 | [ ] | PARTIAL | [Item](checklists/compliance.md#L146): no-drift output is not a durable observable completion or short-circuit. | AUD-036-RAG-011, AUD-036-RAG-023 |
| CHK336 | [ ] | CONFLICT | [Item](checklists/compliance.md#L147): UI and alert definitions differ on inclusive thresholds/17-day red example; need explicit distinction. | AUD-036-RAG-013, AUD-036-RAG-022 |
| CHK337 | [ ] | IMPLEMENTED | [Item](checklists/compliance.md#L148): global-index rather than per-partition scope is explicitly justified. | - |
| CHK338 | [ ] | PARTIAL | [Item](checklists/compliance.md#L149): alert schema exists, but routing/audit callbacks are unmounted and not deduplicated. | AUD-036-RAG-022 |
| CHK339 | [ ] | PARTIAL | [Item](checklists/compliance.md#L150): disabled alerts still publish to bus and flip audit is incomplete. | AUD-036-RAG-022 |

### Cultural Authority Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK166 | [ ] | IMPLEMENTED | [Item](checklists/cultural-authority-protocols.md#L24): in-scope plumbing and external body authoring explicitly separated. | - |
| CHK167 | [ ] | CONFLICT | [Item](checklists/cultural-authority-protocols.md#L25): authority/sign-off lists differ across FR, SC and handoff. | AUD-036-RAG-005, AUD-036-RAG-025 |
| CHK168 | [ ] | UNVERIFIED | [Item](checklists/cultural-authority-protocols.md#L26): named language needs exist; genuine translated corpus inventory/approval not established. | AUD-036-RAG-025 |
| CHK169 | [ ] | IMPLEMENTED | [Item](checklists/cultural-authority-protocols.md#L27): OOS-8 binds non-autonomous content authoring. | - |
| CHK170 | [ ] | CONFLICT | [Item](checklists/cultural-authority-protocols.md#L33): registry scope/signature fields differ in schema/data model/quickstart. | AUD-036-RAG-013 |
| CHK171 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L34): actual consent is not tenant/council/grant-start scoped. | AUD-036-RAG-003 |
| CHK172 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L35): AU registry module exists only in alternate graph; actual persistence unverified. | AUD-036-RAG-003, AUD-036-RAG-023 |
| CHK173 | [ ] | UNVERIFIED | [Item](checklists/cultural-authority-protocols.md#L36): provision-empty/populate-by-authority intent explicit; no deployed/populated evidence. | AUD-036-RAG-025 |
| CHK174 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L37): verifier/renewal/revocation authority is incomplete and default signatures accepted. | AUD-036-RAG-003 |
| CHK175 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L43): post-retrieval placement specified; helper is not called by shared retrieval. | AUD-036-RAG-003 |
| CHK176 | [ ] | IMPLEMENTED | [Item](checklists/cultural-authority-protocols.md#L44): pre-retrieval and Foundry-side consent placement explicitly rejected. | - |
| CHK177 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L45): five agents/controller do not inherit a mounted cultural gate. | AUD-036-RAG-002, AUD-036-RAG-003 |
| CHK178 | [ ] | IMPLEMENTED | [Item](checklists/cultural-authority-protocols.md#L46): no operator-specific Search-index proliferation required by design. | - |
| CHK179 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L52): protected classes defined but metadata is omitted/dropped in actual pipeline. | AUD-036-RAG-003 |
| CHK180 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L53): unavailable event exists only in uncalled helper/optional audit sink. | AUD-036-RAG-003, AUD-036-RAG-012 |
| CHK181 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L54): public continuity intended; real selective fail-closed chain not connected. | AUD-036-RAG-003 |
| CHK182 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L55): warm-cache revocation/effective record selection not established. | AUD-036-RAG-003, AUD-036-RAG-009 |
| CHK183 | [ ] | CONFLICT | [Item](checklists/cultural-authority-protocols.md#L56): denied/blocked/check-result audit vocabulary and real emission disagree. | AUD-036-RAG-003, AUD-036-RAG-013 |
| CHK184 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L62): separate cultural gate required but not enforced in active CD. | AUD-036-RAG-005 |
| CHK185 | [ ] | UNVERIFIED | [Item](checklists/cultural-authority-protocols.md#L63): three genuine community representative signatures not available. | AUD-036-RAG-005, AUD-036-RAG-025 |
| CHK186 | [ ] | PARTIAL | [Item](checklists/cultural-authority-protocols.md#L69): Rego lock exists without production flag-flip invocation. | AUD-036-RAG-003 |

### Federal Compliance Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK187 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L23): five APP labels/mapping authored; consent/minimisation/access behavior not thereby proven. | AUD-036-RAG-026 |
| CHK188 | [ ] | UNVERIFIED | [Item](checklists/federal-compliance-mapping.md#L24): seven-year retention reference is not actual connected archive/retention evidence. | AUD-036-RAG-012, AUD-036-RAG-025 |
| CHK189 | [ ] | CONFLICT | [Item](checklists/federal-compliance-mapping.md#L25): handoff versus task/spec approval authorities differ. | AUD-036-RAG-005, AUD-036-RAG-025 |
| CHK190 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L26): SAR route scaffold unmounted, invalid adapter/subject filtering. | AUD-036-RAG-026 |
| CHK191 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L27): actual operator PII collection/minimisation boundary is not established by response strings. | AUD-036-RAG-001, AUD-036-RAG-026 |
| CHK192 | [ ] | IMPLEMENTED | [Item](checklists/federal-compliance-mapping.md#L33): ISM-0468/1552 explicitly referenced as scoped controls. Qualified mapping approval remains unverified. | AUD-036-RAG-025 |
| CHK193 | [ ] | IMPLEMENTED | [Item](checklists/federal-compliance-mapping.md#L34): ISM mapping scaffold exists and is explicitly pending approval. | - |
| CHK194 | [ ] | UNVERIFIED | [Item](checklists/federal-compliance-mapping.md#L35): no genuine signed federal attestation establishes approval. | AUD-036-RAG-005, AUD-036-RAG-025 |
| CHK195 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L36): broader ISM compliance cannot be inferred from two control labels. | AUD-036-RAG-025 |
| CHK196 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L37): signing/integrity claims lack a complete durable audit chain. | AUD-036-RAG-012, AUD-036-RAG-016 |
| CHK197 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L43): endpoint contract defined; router is not mounted. | AUD-036-RAG-026 |
| CHK198 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L44): CSV mapping misses producer timestamp/authority/rationale fields. | AUD-036-RAG-026 |
| CHK199 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L45): export handler has no explicit authenticated observer/tenant checks; must add before mounting. | AUD-036-RAG-026 |
| CHK200 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L46): bounded/paginated/streamed large audit export not established. | AUD-036-RAG-026 |
| CHK201 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L47): export classification/minimisation must be enforced beyond local CSV escaping. | AUD-036-RAG-026 |
| CHK202 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L53): assumed incident activation authority is not wired to global helper. | AUD-036-RAG-015 |
| CHK203 | [ ] | IMPLEMENTED | [Item](checklists/federal-compliance-mapping.md#L54): COMDISPLAN is explicitly a ranking change, not a RAG exemption. | - |
| CHK204 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L55): activation/ACT precedence interaction absent from live retrieval. | AUD-036-RAG-015 |
| CHK205 | [ ] | PARTIAL | [Item](checklists/federal-compliance-mapping.md#L56): clearing a process boolean is not scoped deactivation/cache/audit recovery. | AUD-036-RAG-009, AUD-036-RAG-015 |
| CHK206 | [ ] | UNVERIFIED | [Item](checklists/federal-compliance-mapping.md#L57): real authorised NEMA activation source/ownership not established. | AUD-036-RAG-015, AUD-036-RAG-025 |

### Audit and Approval Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK207 | [ ] | CONFLICT | [Item](checklists/audit-and-approval-workflow.md#L20): duplicate amended audit properties and incompatible types. | AUD-036-RAG-013 |
| CHK208 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L21): enum specified; actual approval route bypasses state helper. | AUD-036-RAG-014 |
| CHK209 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L22): concrete index/build pair is not reliable in cache/live providers. | AUD-036-RAG-009, AUD-036-RAG-011 |
| CHK210 | [ ] | CONFLICT | [Item](checklists/audit-and-approval-workflow.md#L23): key entities/contracts/model/ADR-14 are not synchronized. | AUD-036-RAG-013 |
| CHK211 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L29): modification/rejection events do not consistently invoke amended writer. | AUD-036-RAG-012, AUD-036-RAG-014 |
| CHK212 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L30): rationale length/meaning varies, and free-text PII is not reliably minimised. | AUD-036-RAG-013, AUD-036-RAG-026 |
| CHK213 | [ ] | UNVERIFIED | [Item](checklists/audit-and-approval-workflow.md#L31): hundred builder records are not actual override completeness evidence. | AUD-036-RAG-014, AUD-036-RAG-024 |
| CHK214 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L32): PSPF Justification does not map actual override/downgrade fields. | AUD-036-RAG-026 |
| CHK215 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L38): local transition rules exist but real service overwrites status outside them. | AUD-036-RAG-014 |
| CHK216 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L39): authenticated IC/PIO actor linkage and terminal concurrency not established. | AUD-036-RAG-014 |
| CHK217 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L40): all public-warning path approval state not covered by actual emission. | AUD-036-RAG-014 |
| CHK218 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L41): incident-level downgrade justification is optional data, not connected controlling workflow. | AUD-036-RAG-014 |
| CHK219 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L42): grounded draft and approved final are not durably linked by actor/event identity. | AUD-036-RAG-012, AUD-036-RAG-014 |
| CHK220 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L48): offline permissions implemented only in uncalled predicate/queue helper. | AUD-036-RAG-017 |
| CHK221 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L49): reconnect requires pending IC review but no operational consumer/SLA queue exists. | AUD-036-RAG-017 |
| CHK222 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L50): offline conflicts are not routed through durable IC-review chain. | AUD-036-RAG-018 |
| CHK223 | [ ] | CONFLICT | [Item](checklists/audit-and-approval-workflow.md#L51): TTL exceptions and decision authority are not consistently represented/enforced. | AUD-036-RAG-013, AUD-036-RAG-017 |
| CHK224 | [ ] | CONFLICT | [Item](checklists/audit-and-approval-workflow.md#L57): required legacy index/null restrictions violate promised schema-on-read tolerance. | AUD-036-RAG-013 |
| CHK225 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L58): missing/null combinations not all asserted; tie array is exempted. | AUD-036-RAG-013 |
| CHK226 | [ ] | UNVERIFIED | [Item](checklists/audit-and-approval-workflow.md#L59): no attributable mixed-generation historical replay sample. | AUD-036-RAG-012, AUD-036-RAG-025 |
| CHK227 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L65): audit lock-on stated, yet optional/uninjected writers bypass recording. | AUD-036-RAG-012 |
| CHK228 | [ ] | PARTIAL | [Item](checklists/audit-and-approval-workflow.md#L66): complete actor/old/new/reason flag event not durably emitted by every setter. | AUD-036-RAG-012, AUD-036-RAG-015, AUD-036-RAG-018 |
| CHK229 | [ ] | UNVERIFIED | [Item](checklists/audit-and-approval-workflow.md#L67): qualified audit/compliance change sign-off not established. | AUD-036-RAG-025 |

### Coordination Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK230 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L20): reactive post-return helper exists but actual aggregation never calls it. | AUD-036-RAG-018 |
| CHK231 | [ ] | IMPLEMENTED | [Item](checklists/multi-agent-coordination.md#L21): preemptive inference-time divergence explicitly rejected. | - |
| CHK232 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L22): owning aggregation boundary not actually connected; API helper placement needs dependency-safe integration. | AUD-036-RAG-018 |
| CHK233 | [ ] | IMPLEMENTED | [Item](checklists/multi-agent-coordination.md#L23): isolation/replay rationale explicitly documented. | - |
| CHK234 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L29): four rules exist but missing scope, tuples and reproducible persisted inputs. | AUD-036-RAG-018 |
| CHK235 | [ ] | CONFLICT | [Item](checklists/multi-agent-coordination.md#L30): severity compares hazard type without the required same-hazard identity. | AUD-036-RAG-018 |
| CHK236 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L31): verb table/deadline test does not cover the warning-versus-withhold example. | AUD-036-RAG-018 |
| CHK237 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L32): disjoint/scoped/false-positive boundaries insufficiently asserted. | AUD-036-RAG-018, AUD-036-RAG-024 |
| CHK238 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L33): canonical input model lacks tenant/incident/hazard IDs. | AUD-036-RAG-018 |
| CHK239 | [ ] | CONFLICT | [Item](checklists/multi-agent-coordination.md#L39): random UUID/group identity is not replay-stable/idempotent. | AUD-036-RAG-018 |
| CHK240 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L40): durable event/ack/resolution lifecycle and standard audit links absent. | AUD-036-RAG-018 |
| CHK241 | [ ] | UNVERIFIED | [Item](checklists/multi-agent-coordination.md#L41): no actual replay evidence; random IDs contradict deterministic reconstruction. | AUD-036-RAG-018, AUD-036-RAG-025 |
| CHK242 | [ ] | IMPLEMENTED | [Item](checklists/multi-agent-coordination.md#L47): Ops Officer first, then IC explicitly specified. | AUD-036-RAG-018 |
| CHK243 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L48): manually invoked timeout helper is not durable five-minute unack timer. | AUD-036-RAG-018 |
| CHK244 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L49): FC no-auto-resolution is written but actor-name-prefix checks are not real role enforcement. | AUD-036-RAG-018 |
| CHK245 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L50): timeout event not delivered through a mounted persisted escalation path. | AUD-036-RAG-018 |
| CHK246 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L56): human-only intent explicit; actual role-resolved lifecycle absent. | AUD-036-RAG-018 |
| CHK247 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L57): acknowledgement immediately resolves and accepts unrelated/repeated IDs. | AUD-036-RAG-018 |
| CHK248 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L63): process flag is not audited reversible progressive-delivery control. | AUD-036-RAG-018 |
| CHK249 | [ ] | PARTIAL | [Item](checklists/multi-agent-coordination.md#L64): no-silencing fallback requirement clear, real coordinated/disabled workflow unproved. | AUD-036-RAG-018 |

### Test Coverage Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK250 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L20): Windows paths/encoding/newlines named but real platform-specific ingest/cache coverage incomplete. | AUD-036-RAG-024 |
| CHK251 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L21): markers/cleanup exist, not complete equivalent platform assertions. | AUD-036-RAG-024 |
| CHK252 | [ ] | IMPLEMENTED | [Item](checklists/test-coverage-windows.md#L22): Windows PR job is authored in CI; its outcome is unverified. | AUD-036-RAG-024 |
| CHK253 | [ ] | IMPLEMENTED | [Item](checklists/test-coverage-windows.md#L23): test homes/fixtures use existing directories; no new fixture directory required. | - |
| CHK254 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L29): random session selection does not guarantee fifty stable concurrent sessions. | AUD-036-RAG-024 |
| CHK255 | [ ] | UNVERIFIED | [Item](checklists/test-coverage-windows.md#L30): no nonempty 50-RPS/60-second/p95/memory/CPU baseline. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK256 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L31): request/session cache defeating not enforced by actual retrieval cache/harness. | AUD-036-RAG-009, AUD-036-RAG-024 |
| CHK257 | [ ] | IMPLEMENTED | [Item](checklists/test-coverage-windows.md#L32): performance SHOULD retained; harness MUST obligations remain binding. | - |
| CHK258 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L33): existing Locust harness reused but points to deferred/unmounted route and accepts 4xx. | AUD-036-RAG-024 |
| CHK259 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L39): canonical file exists alongside old inline/sibling fixture definitions. | AUD-036-RAG-024 |
| CHK260 | [ ] | CONFLICT | [Item](checklists/test-coverage-windows.md#L40): golden entries lack required request fields/expected chunk IDs/tags. | AUD-036-RAG-024 |
| CHK261 | [ ] | CONFLICT | [Item](checklists/test-coverage-windows.md#L41): forty-two not fifty entries; twenty scenario labels are not required tagged subsets. | AUD-036-RAG-024 |
| CHK262 | [ ] | MISSING | [Item](checklists/test-coverage-windows.md#L42): canonical fixture has zero `tags` fields at this SHA. | AUD-036-RAG-024 |
| CHK263 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L43): persona mapping references old fixtures/undefined FRs. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK264 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L49): four lifecycle assertions are labels/dictionary timings; live test unfinished. | AUD-036-RAG-009, AUD-036-RAG-010, AUD-036-RAG-024 |
| CHK265 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L50): ephemeral staging isolation specified but no completed live case. | AUD-036-RAG-024 |
| CHK266 | [ ] | UNVERIFIED | [Item](checklists/test-coverage-windows.md#L51): staging smoke/load runtime not measured by actual operations. | AUD-036-RAG-024, AUD-036-RAG-025 |
| CHK267 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L52): rollback completion lacks operational alias/audit timer guarantees. | AUD-036-RAG-010 |
| CHK268 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L58): Windows/golden lanes exist, nightly/promotion bindings incomplete. | AUD-036-RAG-023, AUD-036-RAG-024 |
| CHK269 | [ ] | PARTIAL | [Item](checklists/test-coverage-windows.md#L59): delivery stage names in prose do not establish actual pre-promotion/pre-release checks. | AUD-036-RAG-023, AUD-036-RAG-024 |

### Observability Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK270 | [ ] | PARTIAL | [Item](checklists/observability.md#L20): OTel is required but current shim only records optional in-memory lists. | AUD-036-RAG-022 |
| CHK271 | [ ] | IMPLEMENTED | [Item](checklists/observability.md#L21): direct App Insights SDK emission is explicitly forbidden; missing real exporter is not compliance proof. | AUD-036-RAG-022 |
| CHK272 | [ ] | IMPLEMENTED | [Item](checklists/observability.md#L22): heartbeat/resilience instrumentation precedents are named. | - |
| CHK273 | [ ] | PARTIAL | [Item](checklists/observability.md#L23): existing bridge is an assumption, not a connected spec-RAG producer/export chain. | AUD-036-RAG-022 |
| CHK274 | [ ] | PARTIAL | [Item](checklists/observability.md#L29): types/units named but wrong counters and timing boundaries defeat them. | AUD-036-RAG-022 |
| CHK275 | [ ] | PARTIAL | [Item](checklists/observability.md#L30): tags lose actual requested jurisdictions/session context. | AUD-036-RAG-022 |
| CHK276 | [ ] | PARTIAL | [Item](checklists/observability.md#L31): retrieval wrapper exists, SDK errors/cache/embedding timing not measured as specified. | AUD-036-RAG-022 |
| CHK277 | [ ] | PARTIAL | [Item](checklists/observability.md#L37): sync wrapper only; production streaming span integration incomplete. | AUD-036-RAG-022 |
| CHK278 | [ ] | PARTIAL | [Item](checklists/observability.md#L38): shared correlation in manually nested test is not propagated by actual transports/consumers. | AUD-036-RAG-022 |
| CHK279 | [ ] | PARTIAL | [Item](checklists/observability.md#L39): retrieval-only versus relative end-to-end SLO distinction written but instrumentation/alerts differ. | AUD-036-RAG-022 |
| CHK280 | [ ] | PARTIAL | [Item](checklists/observability.md#L45): ingest metrics read nonexistent attributes and lack exporter in runner image. | AUD-036-RAG-022 |
| CHK281 | [ ] | PARTIAL | [Item](checklists/observability.md#L46): dashboard/workbook authored without complete SC tiles/selected graph/data producers. | AUD-036-RAG-022 |
| CHK282 | [ ] | PARTIAL | [Item](checklists/observability.md#L47): swallowed Search/upload failures do not consistently increment useful error categories. | AUD-036-RAG-008, AUD-036-RAG-022 |
| CHK283 | [ ] | PARTIAL | [Item](checklists/observability.md#L53): sustained five-minute p95 rule is not fed/mounted as required. | AUD-036-RAG-022 |
| CHK284 | [ ] | IMPLEMENTED | [Item](checklists/observability.md#L54): 300ms target versus 500ms enforced alert rationale explicitly recorded. | - |

### Accessibility Checklist

| Item | Original state | Status | Source question and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK285 | [ ] | IMPLEMENTED | [Item](checklists/accessibility.md#L20): SHOULD retained in FR/Phase F; audit does not turn it into a blocking measured MUST. | - |
| CHK286 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L21): card/wrapper components exist but not mounted operator grounding workflow. | AUD-036-RAG-021 |
| CHK287 | [ ] | IMPLEMENTED | [Item](checklists/accessibility.md#L27): shared card has source-oriented aria label and expanded jurisdiction names. | AUD-036-RAG-021 |
| CHK288 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L28): missing/zero page or unavailable source fallback not covered on real pages. | AUD-036-RAG-021 |
| CHK289 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L34): positive citation-count live region exists; no mounted zero/no-match announcement. | AUD-036-RAG-021 |
| CHK290 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L35): suppression has no real accessible event/notice chain. | AUD-036-RAG-019, AUD-036-RAG-021 |
| CHK291 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L41): precedence/conflict data and accessible notes are not integrated. | AUD-036-RAG-015, AUD-036-RAG-021 |
| CHK292 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L42): timestamp/non-colour component is authored but no actual freshness feed/display. | AUD-036-RAG-021 |
| CHK293 | [ ] | IMPLEMENTED | [Item](checklists/accessibility.md#L48): component keyboard tests cover tab/Enter/Space/ARIA. Workflow reachability remains separate. | AUD-036-RAG-021 |
| CHK294 | [ ] | PARTIAL | [Item](checklists/accessibility.md#L49): operator modal/focus-return interactions not demonstrated by isolated card tests. | AUD-036-RAG-021 |
| CHK295 | [ ] | IMPLEMENTED | [Item](checklists/accessibility.md#L55): warn-only axe lane/deferred quality classification is explicit. | AUD-036-RAG-025 |
| CHK296 | [ ] | UNVERIFIED | [Item](checklists/accessibility.md#L56): no attributable qualified manual accessibility approval. | AUD-036-RAG-025 |

## Additional Constraints and Edges

The following review keys do not invent original task/FR IDs. They enumerate unnumbered source obligations and preserve
the original A/OOS identifiers. Their coverage is additional to the 68-FR/19-SC/38-scenario matrices.

| Constraint | Status | Exact source and assessment | Follow-up |
| --- | --- | --- | --- |
| A1 | IMPLEMENTED | [Assumption](spec.md#L427): corpus build pipeline is the input/source boundary, not a feature to rewrite in remediation. Its operational availability is UNVERIFIED. | AUD-036-RAG-011, AUD-036-RAG-025 |
| A2 | PARTIAL | [Assumption](spec.md#L428): existing module reuse occurs, but active/alternate graphs and claimed additive topology are not fully composed. | AUD-036-RAG-004, AUD-036-RAG-023 |
| A3 | CONFLICT | [Assumption](spec.md#L429): schema unchanged/reused claim conflicts with differing amended registry schema semantics. | AUD-036-RAG-005, AUD-036-RAG-013 |
| A4 | UNVERIFIED | [Assumption](spec.md#L430): SDK streaming/tool compatibility is a platform assumption; actual adapters diverge and no SDK/runtime call was made. | AUD-036-RAG-020 |
| A5 | UNVERIFIED | [Assumption](spec.md#L431): AIDR/per-publisher indexing rights need attributable review; missing-mode defaults are not legal authorisation. | AUD-036-RAG-006, AUD-036-RAG-025 |
| A6 | IMPLEMENTED | [Assumption](spec.md#L432): inference exemption cannot be widened without constitutional authority. Report tasks preserve this restriction. | AUD-036-RAG-005 |
| A7 | PARTIAL | [Assumption](spec.md#L433): role/rate/tool/watermark code persists; integrated grounded tenant/comms/approval preservation remains unverified. | AUD-036-RAG-014, AUD-036-RAG-019, AUD-036-RAG-024 |
| A8 | IMPLEMENTED | [Assumption](spec.md#L434): embedding model and 3072 dimension commitment are explicit and dimensional checks authored. Actual hosting/output UNVERIFIED. | AUD-036-RAG-020 |
| A9 | UNVERIFIED | [Assumption](spec.md#L435): community/federal sign-offs are explicitly external and not present as attributable approvals. | AUD-036-RAG-005, AUD-036-RAG-025 |
| A10 | CONFLICT | [Assumption](spec.md#L436): nullable reads, isolated schema rebuild and empty-then-approved registry are not matched by current producers/contracts. | AUD-036-RAG-003, AUD-036-RAG-007, AUD-036-RAG-013 |
| A11 | PARTIAL | [Assumption](spec.md#L437): eight ADR lifecycle targets exist; ADR-15 remains pending and some bodies conflict with contracts. | AUD-036-RAG-013, AUD-036-RAG-025 |
| A12 | PARTIAL | [Assumption](spec.md#L438): locked/reversible/manual taxonomy authored, but active flag mutation/audit/manual role behavior incomplete. | AUD-036-RAG-003, AUD-036-RAG-010, AUD-036-RAG-015, AUD-036-RAG-018, AUD-036-RAG-022 |
| OOS-1 | IMPLEMENTED | [Exclusion](spec.md#L444): prompt rewrites remain outside authorised repair scope; grounding blocks alone are intended additions. | - |
| OOS-2 | PARTIAL | [Exclusion](spec.md#L445): Content Safety must remain; direct dispatcher/MAF paths require preserving actual validator/fallback composition. | AUD-036-RAG-002, AUD-036-RAG-019 |
| OOS-3 | IMPLEMENTED | [Exclusion](spec.md#L446): corpus source/fetch/render builder changes excluded; future fixes belong in ingest consumers. | AUD-036-RAG-011 |
| OOS-4 | IMPLEMENTED | [Exclusion](spec.md#L447): no new corpus sources authored by this audit; curation requires separately owned work. | AUD-036-RAG-025 |
| OOS-5 | CONFLICT | [Exclusion](spec.md#L448): reuse versus schema/version redesign needs explicit authority rather than contradictory schema mirrors. | AUD-036-RAG-005, AUD-036-RAG-013 |
| OOS-6 | IMPLEMENTED | [Exclusion](spec.md#L449): preserve controller prompt/tools; this audit proposes transport/grounding enforcement without prompt replacement. | AUD-036-RAG-019, AUD-036-RAG-020 |
| OOS-7 | IMPLEMENTED | [Exclusion](spec.md#L450): live BoM/GA/DACC clients are not new implementation deliverables; audit opt-out boundaries only. | AUD-036-RAG-024 |
| OOS-8 | IMPLEMENTED | [Exclusion](spec.md#L451): Indigenous-content body authoring and genuine consent remain human-owned, not autonomous completion. | AUD-036-RAG-025 |
| EDGE-01 | PARTIAL | [Frozen mid-update ingest](spec.md#L278): mutable reads/hash meanings do not enforce a single immutable snapshot. | AUD-036-RAG-011 |
| EDGE-02 | PARTIAL | [AU quota exhaustion](spec.md#L279): current registry/full-envelope minimisation/audited fallback not enforced by all transports. | AUD-036-RAG-001, AUD-036-RAG-005, AUD-036-RAG-022 |
| EDGE-03 | PARTIAL | [Model change](spec.md#L280): live state cannot reliably trigger isolated rebuild/promotion/retention. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-010 |
| EDGE-04 | PARTIAL | [Citation mismatch](spec.md#L281): model text streams before canonical citation suppression/audit. | AUD-036-RAG-019 |
| EDGE-05 | PARTIAL | [Excluded prompt source](spec.md#L282): binding excluded-reference CI plus defensive runtime rejection is not established. | AUD-036-RAG-006 |
| EDGE-06 | PARTIAL | [Excluded simulation source](spec.md#L283): explicit forbidden-source refusal not enforced on unfiltered chat output. | AUD-036-RAG-006, AUD-036-RAG-019 |
| EDGE-07 | CONFLICT | [Missing endpoint](spec.md#L284): explicit fail-closed requirement conflicts with silent offline/ungrounded configuration fallthrough and no-silencing interpretation. | AUD-036-RAG-002, AUD-036-RAG-013, AUD-036-RAG-020 |
| EDGE-08 | PARTIAL | [Stale cache](spec.md#L285): badge component exists but runtime TTL/retrieval/age-audit/feed is incomplete. | AUD-036-RAG-017, AUD-036-RAG-021 |
| EDGE-09 | PARTIAL | [Explain a recommendation](spec.md#L286): full augmented prompt/model/chunk/output durable provenance and historical replay not established. | AUD-036-RAG-009, AUD-036-RAG-012 |
| EDGE-10 | PARTIAL | [Classification boundary](spec.md#L287): request-attribute check alone cannot enforce complete envelope/offline DACC routing. | AUD-036-RAG-001, AUD-036-RAG-024 |
| N-01 | PARTIAL | [Plan performance](plan.md#L24): 24h cold rebuild, 60s alias/reconcile and 10% warm run remain unmeasured; helpers not proof. | AUD-036-RAG-007, AUD-036-RAG-010, AUD-036-RAG-017, AUD-036-RAG-025 |
| N-02 | UNVERIFIED | [Plan local cache target](plan.md#L24): 50ms offline lookup target lacks real body/cache benchmark. | AUD-036-RAG-017, AUD-036-RAG-025 |
| N-03 | PARTIAL | [Retrieval quotas/errors](contracts/retrieval-service.md#L144): QPS/timeout/error/status and deferred REST assumptions differ from used provider/load path. | AUD-036-RAG-020, AUD-036-RAG-022, AUD-036-RAG-024 |
| N-04 | PARTIAL | [Chunking guarantee](research.md#L44): 1024 tokens, 10% overlap, atomic blocks/cross-page duplication and size/truncation metrics not fully implemented. | AUD-036-RAG-011, AUD-036-RAG-022 |
| N-05 | PARTIAL | [No-silencing/authority](plan.md#L25): explicit template fallback and human veto must coexist with honest ungrounded/error evidence, not fake grounded success. | AUD-036-RAG-002, AUD-036-RAG-014, AUD-036-RAG-019 |
| N-06 | UNVERIFIED | [Test-first policy](tasks.md#L10): current source cannot establish historical red-before-green order, lock/build execution or 95% seam coverage. | AUD-036-RAG-024, AUD-036-RAG-025 |
| N-07 | PARTIAL | [Injection safety risk](plan.md#L271): fake-client leakage prevention at actual production composition not established. | AUD-036-RAG-020, AUD-036-RAG-024 |
| N-08 | UNVERIFIED | [Drill cadence](plan.md#L252): monthly/quarterly game days and replay within 48h are procedures, not attributable completed exercises. | AUD-036-RAG-025 |
| N-09 | PARTIAL | [Retention](research.md#L216): 45/90-day hot retention and embedding-call fields conflict; connected immutable seven-year archive absent. | AUD-036-RAG-012, AUD-036-RAG-013 |
| N-10 | PARTIAL | [Signed offline scope](contracts/offline-cache-manifest.json#L34): 14-day fixed TTL versus 30-day exception and actual device/signature bytes require resolution. | AUD-036-RAG-013, AUD-036-RAG-016, AUD-036-RAG-017 |
| N-11 | PARTIAL | [Public warning watermarks](spec.md#L120): IC-approval and simulation non-distribution labels must be preserved on actual outputs, not only tool templates. | AUD-036-RAG-014, AUD-036-RAG-019 |
| N-12 | UNVERIFIED | [Source-link review](checklists/migration.md#L48): valid live PDF/handbook anchors, recovery on unavailability and manual accessibility unmeasured. | AUD-036-RAG-011, AUD-036-RAG-021, AUD-036-RAG-025 |

## Clarification and Amendment Accounting

All 40 Q&A definitions are accounted, including 19 unnumbered original/R3 questions and 21 named Q-P1/Q-P2/Q-P6
questions. Review keys S1/S2/S3 identify the original unnumbered bullets. There are no source `R3-P1` or `R3-P2`
checklist IDs to invent. Closed Questions repeats these decisions; it does not create new obligations or proof.

| Amendment | Status | Source and implementation consequence | Follow-up |
| --- | --- | --- | --- |
| S1-01 | CONFLICT | [SDK/scope decision](spec.md#L32): Inference SDK bound; actual production exceptions require reconciliation. | AUD-036-RAG-020 |
| S1-02 | PARTIAL | [Embedding/index decision](spec.md#L33): 3072/single-index/union exists, quality/capacity/actual embedding identity incomplete. | AUD-036-RAG-007, AUD-036-RAG-022 |
| S1-03 | PARTIAL | [Cache signing/size/TTL](spec.md#L34): real payload/dual authentication/refresh absent. | AUD-036-RAG-016, AUD-036-RAG-017 |
| S2-01 | SUPERSEDED | [Canary decision](spec.md#L38) explicitly replaced by Session 6/ADR 20; regression and no-silencing retained. | AUD-036-RAG-002, AUD-036-RAG-024 |
| S2-02 | PARTIAL | [Model rebuild decision](spec.md#L39): still binding; live state/promotion/pinning/retention incomplete. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-009, AUD-036-RAG-010 |
| S2-03 | PARTIAL | [Callable seam](spec.md#L40): sync helper only, not all three actual constructors/streams. | AUD-036-RAG-020 |
| S2-04 | PARTIAL | [Observer opt-out](spec.md#L41): stable NS-08/09 IDs retained, audit reasons/lint behavior inconsistent. | AUD-036-RAG-024 |
| S3-A1 | PARTIAL | [Agency fields](spec.md#L47): declarations exist without ingest/retrieval consumer enforcement. | AUD-036-RAG-015 |
| S3-A2 | PARTIAL | [Cultural authority](spec.md#L48): protected metadata/consent gate detached; content and approvals human/unverified. | AUD-036-RAG-003, AUD-036-RAG-025 |
| S3-A3 | PARTIAL | [ACT precedence](spec.md#L49): uncalled ranking helper and incomplete qualifying fixture. | AUD-036-RAG-015, AUD-036-RAG-024 |
| S3-A4 | CONFLICT | [Approver tightening](spec.md#L50): target-prod three-approver rule not enforced by current row-derived policy. | AUD-036-RAG-005 |
| S3-A5 | PARTIAL | [Audit/offline boundaries](spec.md#L51): fields/predicates authored, actual approval/spool consumers missing. | AUD-036-RAG-012, AUD-036-RAG-014, AUD-036-RAG-017 |
| S3-A6 | PARTIAL | [Federal controls](spec.md#L52): pending mapping and unmounted exports do not satisfy compliance. | AUD-036-RAG-005, AUD-036-RAG-026 |
| S3-A7 | PARTIAL | [Alias atomicity](spec.md#L53): concrete labels not actual pinned clients; rollback detached. | AUD-036-RAG-009, AUD-036-RAG-010 |
| S3-A8 | PARTIAL | [Freshness](spec.md#L54): workflow/alert/component helpers are not composed. | AUD-036-RAG-021, AUD-036-RAG-022, AUD-036-RAG-023 |
| S3-A9 | PARTIAL | [Conflict controls](spec.md#L55): no real aggregation/role/timer consumer. | AUD-036-RAG-018 |
| S3-A10 | PARTIAL | [Test expansion](spec.md#L56): Windows scaffolding exists, meaningful golden/load/staging gates incomplete. | AUD-036-RAG-024 |
| S3-A11 | PARTIAL | [Observability](spec.md#L57): recorder shim not actual exporter/alert chain. | AUD-036-RAG-022 |
| S3-A12 | PARTIAL | [Accessibility](spec.md#L58): component work supported, mounted/manual outcome unverified; SHOULD retained. | AUD-036-RAG-021, AUD-036-RAG-025 |
| Q-P1-01 | PARTIAL | [Registry fail-closed](spec.md#L64): schema/auth/scope/gate unavailable path not enforced by actual retrieval. | AUD-036-RAG-003, AUD-036-RAG-013 |
| Q-P1-02 | CONFLICT | [Tie order](spec.md#L65): helper ordering/audit integration disagree; cache provenance also mutable. | AUD-036-RAG-009, AUD-036-RAG-015 |
| Q-P1-03 | PARTIAL | [Ops-to-IC escalation](spec.md#L66): auth/timer/offline queue not operationally mounted. | AUD-036-RAG-018 |
| Q-P1-04 | PARTIAL | [Rollback timer/completion](spec.md#L67): precise requirement exists; durable bus/alias/audit completion incomplete. | AUD-036-RAG-010 |
| Q-P1-05 | PARTIAL | [Global freshness](spec.md#L68): scope preserved in helper; scheduler/deduplication/state delivery incomplete. | AUD-036-RAG-022, AUD-036-RAG-023 |
| Q-P1-06 | PARTIAL | [Retrieval-only p95](spec.md#L69): actual timing includes other work and stream correlation/export incomplete. | AUD-036-RAG-022 |
| Q-P1-07 | PARTIAL | [Fifty sessions](spec.md#L70): harness cannot guarantee stable session cardinality/one request each/50 RPS. | AUD-036-RAG-024 |
| Q-P1-08 | PARTIAL | [Fixture consolidation](spec.md#L71): explicitly supersedes separate agency fixture, but required canonical tags/shape/count and consumer migration incomplete. | AUD-036-RAG-024 |
| Q-P2-01 | CONFLICT | [Three-tier migration](spec.md#L77): additive reads, schema rebuild and empty consent registry not consistently enforced. | AUD-036-RAG-003, AUD-036-RAG-007, AUD-036-RAG-013 |
| Q-P2-02 | PARTIAL | [Gate placement](spec.md#L78): intended post-retrieval gate is a detached helper rather than mandatory shared path. | AUD-036-RAG-003 |
| Q-P2-03 | PARTIAL | [Quorum/coupled PR](spec.md#L79): real OPA/target environment/PR coupling not established by optional Python tests/manual workflow. | AUD-036-RAG-005 |
| Q-P2-04 | PARTIAL | [Fixture/trigger homes](spec.md#L80): relocated UI/test homes credited, but meaningful nightly/pre-promotion/live paths absent. | AUD-036-RAG-024 |
| Q-P2-05 | PARTIAL | [OTel bridge](spec.md#L81): actual producer/export transport is missing; direct manual recorder tests insufficient. | AUD-036-RAG-022 |
| Q-P2-06 | PARTIAL | [Deterministic post-return rules](spec.md#L82): helper misses scope/verbs/stable evidence and no consumer calls it. | AUD-036-RAG-018 |
| Q-P2-07 | PARTIAL | [ADR lifecycle](spec.md#L83): body/stub artifacts exist, with ADR-15 pending and several schema/body conflicts. | AUD-036-RAG-013, AUD-036-RAG-025 |
| Q-P2-08 | PARTIAL | [Flag classes](spec.md#L84): locked/reversible/manual rules not enforced at actual distributed changes with full audit provenance. | AUD-036-RAG-003, AUD-036-RAG-010, AUD-036-RAG-015, AUD-036-RAG-018, AUD-036-RAG-022 |
| Q-P6-01 | PARTIAL | [Retained regression](spec.md#L98): canary activation retired explicitly; empty CLI runners and signal/alert wiring do not satisfy retained regression. | AUD-036-RAG-022, AUD-036-RAG-024 |
| Q-P6-02 | PARTIAL | [Kill-switch reinterpretation](spec.md#L99): prod env flags set but actual handlers ignore grounding pipeline/disable audit. | AUD-036-RAG-002 |
| Q-P6-03 | CONFLICT | [Legacy cleanup timing](spec.md#L100): deferred cleanup is not authority for arbitrary current OpenAI-SDK lint exceptions; reconcile zero-import requirement. | AUD-036-RAG-020, AUD-036-RAG-025 |
| Q-P6-04 | PARTIAL | [Indexing schedule note](spec.md#L101): old false-switch/Service Bus deferral not current truth; root now true but lifecycle remains incomplete, not superseded. | AUD-036-RAG-023, AUD-036-RAG-025 |
| Q-P6-05 | PARTIAL | [New provider discriminator](spec.md#L102): always-Foundry claim not supported by every actual new durable audit record; historical compatibility retained. | AUD-036-RAG-012, AUD-036-RAG-013 |

## Research and Data Contracts

R-NN here denotes research decisions, not plan risk numbers; R-20 is federal research, not hard-cutover ADR 20.
Decision prose is preserved as authored output, while the status below assesses its implementation/consistency.

| Decision | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| R-01 | CONFLICT | [SDK/scope](research.md#L10): identity scope supported; production SDK exceptions violate bound choice. | AUD-036-RAG-020 |
| R-02 | IMPLEMENTED | [Embedding dimensions](research.md#L22): declared 3072/model commitment and dimension guards exist; actual model service unverified. | AUD-036-RAG-020 |
| R-03 | PARTIAL | [Single index/union](research.md#L34): union supported, actual agency/source metadata/quality incomplete. | AUD-036-RAG-015 |
| R-04 | PARTIAL | [Chunking](research.md#L44): word splitting/false cross-page flag do not meet token/atomicity/overlap/zero-truncation target. | AUD-036-RAG-011 |
| R-05 | CONFLICT | [Parity](research.md#L61): plus/minus 1%, sampling and quality differ from ingest contract plus/minus 5%/cost/equivalence. The stated 100-sample allocation totals 84. Automatic rollback portion explicitly replaced by R-21. | AUD-036-RAG-008, AUD-036-RAG-013 |
| R-06 | PARTIAL | [Hybrid/cache](research.md#L82): weighted fusion exists but ID dedup, cache context and semantic/confidence guarantees incomplete. | AUD-036-RAG-009, AUD-036-RAG-015 |
| R-07 | CONFLICT | [Offline expiry](research.md#L100): 11/14/30-day semantics not consistently signed/enforced at every query. | AUD-036-RAG-013, AUD-036-RAG-017 |
| R-08 | PARTIAL | [Job choice](research.md#L120): new package/job exists, active hooks/image/completion composition incomplete. | AUD-036-RAG-023 |
| R-09 | PARTIAL | [Quota governance](research.md#L135): TPM/70%/90% design differs from T078 80%/contract QPS; configured runtime budget not consumed. | AUD-036-RAG-013, AUD-036-RAG-022 |
| R-10 | PARTIAL | [Citation downgrade](research.md#L149): global helper threshold differs from unconsumed per-agent settings and real outputs are unfiltered. | AUD-036-RAG-019, AUD-036-RAG-022 |
| R-11 | PARTIAL | [Envelope](research.md#L163): original schema/model/card authored; actual SSE/claims/metadata-only/no-match consumers incomplete. | AUD-036-RAG-019, AUD-036-RAG-021 |
| R-12 | SUPERSEDED | [Canary order](research.md#L193): production activation sequencing explicitly retired by Session 6; regression/drills remain. | AUD-036-RAG-024, AUD-036-RAG-025 |
| R-13 | CONFLICT | [Embedding audit](research.md#L216): per-call fields/hot retention differ from schema and runner uses in-memory aggregate. | AUD-036-RAG-012, AUD-036-RAG-013 |
| R-14 | PARTIAL | [Cards/banners](research.md#L230): reusable accessible components exist, not mounted stateful workflows/manual review proof. | AUD-036-RAG-021, AUD-036-RAG-025 |
| R-15 | PARTIAL | [Wrapper reuse](research.md#L249): existing Search reused, but selected networking/parity/retention wiring incomplete. | AUD-036-RAG-004, AUD-036-RAG-008, AUD-036-RAG-010 |
| R-16 | CONFLICT | [Confidence model](research.md#L269): minimum similarity/coherence/licence safety replaced by batch-relative maximum normalization. | AUD-036-RAG-015 |
| R-17 | PARTIAL | [Consent ADR decision](research.md#L324): in-process gate/signature/cache design not enforced by actual retrieval. | AUD-036-RAG-003 |
| R-18 | PARTIAL | [Authority ranking](research.md#L330): standalone helpers do not implement live precedence/tie/flag/audit behavior. | AUD-036-RAG-015 |
| R-19 | CONFLICT | [Additive audit](research.md#L336): current duplicate keys/nullability/model invariants violate agreed migration. | AUD-036-RAG-013 |
| R-20 | PARTIAL | [Federal mapping](research.md#L342): scaffold exists; real exports/sign-off gate absent, human approval unverified. | AUD-036-RAG-005, AUD-036-RAG-026 |
| R-21 | PARTIAL | [Manual rollback](research.md#L348): explicitly replaces automatic rollback; actual authenticated event/timer/retention consumer absent. | AUD-036-RAG-010 |
| R-22 | PARTIAL | [Freshness](research.md#L354): global helper/component exist but no active scheduled/disabled/deduplicated flow. | AUD-036-RAG-021, AUD-036-RAG-022, AUD-036-RAG-023 |
| R-23 | PARTIAL | [Conflict lifecycle](research.md#L360): detached narrowed detector/weak actor checks fail intended deterministic human resolution. | AUD-036-RAG-018 |
| R-24 | PARTIAL | [Test coverage](research.md#L366): Windows and fixture artifacts exist, meaningful collection/load/E2E/acceptance incomplete. | AUD-036-RAG-024 |
| Research deferral: golden composition | PARTIAL | [Deferred work](research.md#L311): required meaningful canonical fixture not completed. | AUD-036-RAG-024 |
| Research deferral: RRF A/B | UNVERIFIED | [Deferred work](research.md#L311): no attributable RRF A/B result accepted; current 0.7/0.3 is authored configuration. | AUD-036-RAG-015, AUD-036-RAG-025 |
| Research deferral: model drift alerts | PARTIAL | [Deferred work](research.md#L311): homogeneity/actual embedding-version alert/export incomplete. | AUD-036-RAG-008, AUD-036-RAG-022 |
| Research deferral: monthly queries | PARTIAL | [Deferred work](research.md#L311): KQL authored but real producer/table/alert/review linkage not established. | AUD-036-RAG-012, AUD-036-RAG-022, AUD-036-RAG-025 |

| Entity or contract obligation | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| CorpusEntry | PARTIAL | [Entity](data-model.md#L27): 155 entries inspected; absent mode/empty URLs/hash meaning/rights validation remain incomplete. | AUD-036-RAG-006, AUD-036-RAG-011 |
| Chunk | CONFLICT | [Entity](data-model.md#L55), [amendment](data-model.md#L423): projection/source metadata missing; closed schema omits required retrieved-at and inconsistently requires query-time index. | AUD-036-RAG-003, AUD-036-RAG-011, AUD-036-RAG-013 |
| RetrievalRequest | PARTIAL | [Entity](data-model.md#L96): original fields work, amended authenticated incident/council/agency context cannot be represented. | AUD-036-RAG-003, AUD-036-RAG-015 |
| RetrievalResult | PARTIAL | [Entity](data-model.md#L121): default/relabeled index/build metadata not actual query provenance. | AUD-036-RAG-009 |
| Citation | PARTIAL | [Entity](data-model.md#L141): original model/schema guards exist; authoritative output membership/metadata and display incomplete. | AUD-036-RAG-019, AUD-036-RAG-021 |
| AuditRecord | CONFLICT | [Entity](data-model.md#L167), [amendment](data-model.md#L440): eight duplicated fields, incompatible offline type and legacy null restrictions. | AUD-036-RAG-012, AUD-036-RAG-013 |
| CarveoutRegistryEntry | CONFLICT | [Entity](data-model.md#L215): current model rows, target environment, schema version and quorum disagree. | AUD-036-RAG-005, AUD-036-RAG-013 |
| OfflineCacheManifest | PARTIAL | [Entity](data-model.md#L244): original bounds/shape exist, real authenticated payload/TTL exception/reader chain absent. | AUD-036-RAG-013, AUD-036-RAG-016, AUD-036-RAG-017 |
| RagOptoutAdr | CONFLICT | [Entity](data-model.md#L294): nine bodies exist, but reason strings and optional marker/audit claims contradict required shape. | AUD-036-RAG-024 |
| EquivalenceTestResult | PARTIAL | [Entity](data-model.md#L337): model/tests exist, actual measured runner results cannot be inferred from empty pass convention. | AUD-036-RAG-024 |
| CulturalAuthorityRegistryEntry | CONFLICT | [Added entity](data-model.md#L457): scope/signature representation differs from contract; actual verifier/scope incomplete. | AUD-036-RAG-003, AUD-036-RAG-013 |
| ConflictDetectionLogEntry | CONFLICT | [Added entity](data-model.md#L476): schema/implementation states/history/evidence/accepted-ID nullability disagree. | AUD-036-RAG-013, AUD-036-RAG-018 |
| Relationship/mirror/migration invariants | PARTIAL | [Relationships](data-model.md#L362), [mirror matrix](data-model.md#L380), [migration](data-model.md#L495): seven raw mirrors match, but disconnected consumers and incompatible semantics remain. | AUD-036-RAG-013 |
| Foundry protocol errors/tools/timeout | PARTIAL | [Contract](contracts/foundry-chat-client.md#L1): actual wrappers do not meet all sync/async/tool/error/metadata requirements. | AUD-036-RAG-020 |
| Retrieval port/REST/quota contract | PARTIAL | [Contract](contracts/retrieval-service.md#L1): Python service exists; deferred/unmounted REST cannot be treated as load-tested production retrieval. | AUD-036-RAG-009, AUD-036-RAG-015, AUD-036-RAG-024 |
| Ingest snapshot/parity/per-call contract | PARTIAL | [Contract](contracts/ingest-pipeline.md#L1): actual state/gates/signatures/completion do not satisfy ordered contract. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-011, AUD-036-RAG-012, AUD-036-RAG-023 |
| Staleness alert boundary/schema | CONFLICT | [Contract](contracts/staleness_alert.schema.json#L44): inclusive age/last-success semantics, 17-day red and 16.6-day red example disagree with other scope text. | AUD-036-RAG-013, AUD-036-RAG-022 |

## Persona and Review Obligations

All forty concerns in the local persona-traceability artifact are retained below using `P<section>.<row>` review keys.
Original memo completeness, actual consultation, and named reviewer authority remain UNVERIFIED: original and R3
persona memo/triage files were not found by bounded exact-filename/location/content searches excluding other reports.
No additional inferred persona requirement is claimed as an original FR. Undefined `FR-RAG-UX-04`/`FR-RAG-OB-04`
references and misnumbered task links must be reconciled, not silently accepted as supersession.

| Concern | Status | Source and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| P1.1 | PARTIAL | [Doctrine citations](persona-traceability.md#L21): actual dispatcher/MAF/citation publication bypasses the full chain. | AUD-036-RAG-002, AUD-036-RAG-019 |
| P1.2 | PARTIAL | [Satellite-outage cache](persona-traceability.md#L22): helpers lack signed body/fallback/renewal/reconnect consumers. | AUD-036-RAG-016, AUD-036-RAG-017 |
| P1.3 | CONFLICT | [Deterministic collection](persona-traceability.md#L23): no-RAG intent supported; code-marker-optional claim contradicts NS-08. | AUD-036-RAG-024, AUD-036-RAG-025 |
| P1.4 | PARTIAL | [Degradation visibility](persona-traceability.md#L24): undefined UX FR; component exists without actual event/page consumer. | AUD-036-RAG-021, AUD-036-RAG-025 |
| P1.5 | UNVERIFIED | [Byte replay](persona-traceability.md#L25): wrong cited FR/task mapping and synthetic replay cannot prove historical reconstruction. | AUD-036-RAG-012, AUD-036-RAG-025 |
| P2.1 | PARTIAL | [National/AIDR handoff](persona-traceability.md#L31): union implemented, actual doctrine relevance and obsolete fixture references not resolved. | AUD-036-RAG-015, AUD-036-RAG-024 |
| P2.2 | PARTIAL | [Classified exclusion](persona-traceability.md#L32): full envelope/transport classification bypasses remain. | AUD-036-RAG-001 |
| P2.3 | CONFLICT | [Broadcast preemption audit](persona-traceability.md#L33): undefined OB FR and wrong quota/TTL task links do not prove that specific audit path. | AUD-036-RAG-012, AUD-036-RAG-025 |
| P2.4 | CONFLICT | [CIC deterministic cascade](persona-traceability.md#L34): notifier remains deterministic, but marker-optional/ADR task mapping and audit emission disagree. | AUD-036-RAG-024, AUD-036-RAG-025 |
| P2.5 | PARTIAL | [Tenant quotas](persona-traceability.md#L35): source settings are per-agent and unconsumed; per-tenant visibility/enforcement unproved. | AUD-036-RAG-022, AUD-036-RAG-025 |
| P3.1 | PARTIAL | [Infrastructure signals](persona-traceability.md#L41): no-LLM notifier supported; mandatory opt-out audit/actual path lint not. | AUD-036-RAG-012, AUD-036-RAG-024 |
| P3.2 | UNVERIFIED | [Multi-hazard cascade thresholds](persona-traceability.md#L42): named old fixture is not attributable RAG correlation/threshold evidence. | AUD-036-RAG-015, AUD-036-RAG-024, AUD-036-RAG-025 |
| P3.3 | PARTIAL | [Read-only energy telemetry](persona-traceability.md#L43): intended NS-09 rationale exists, canonical audit/ADR mapping incomplete. | AUD-036-RAG-024, AUD-036-RAG-025 |
| P3.4 | PARTIAL | [Health/CALD warnings](persona-traceability.md#L44): inclusion helper uncalled and fixture-only topics do not prove drafting. | AUD-036-RAG-002, AUD-036-RAG-015 |
| P4.1 | PARTIAL | [NSW/VIC agencies](persona-traceability.md#L50): actual agency filter is disconnected despite jurisdiction union. | AUD-036-RAG-015 |
| P4.2 | UNVERIFIED | [Section-44 source](persona-traceability.md#L51): real source/claim citation and thresholds not proven by old fixture label. | AUD-036-RAG-015, AUD-036-RAG-019, AUD-036-RAG-025 |
| P4.3 | PARTIAL | [AEST timestamps](persona-traceability.md#L52): undefined UX FR and unmounted badge; actual timezone/absolute-relative display unproved. | AUD-036-RAG-021, AUD-036-RAG-025 |
| P4.4 | UNVERIFIED | [Storm-surge/dam coordination](persona-traceability.md#L53): source-specific doctrinal assertions not exercised by real retrieval. | AUD-036-RAG-015, AUD-036-RAG-024 |
| P5.1 | PARTIAL | [Interpreter Service](persona-traceability.md#L59): specific inclusion/consent before drafting not composed. | AUD-036-RAG-002, AUD-036-RAG-003 |
| P5.2 | UNVERIFIED | [APY heatwave](persona-traceability.md#L60): approved protected source and actual appropriate retrieval absent as evidence. | AUD-036-RAG-003, AUD-036-RAG-015, AUD-036-RAG-025 |
| P5.3 | PARTIAL | [DFES combined](persona-traceability.md#L61): fake jurisdiction exclusion is not agency-modeling proof. | AUD-036-RAG-015, AUD-036-RAG-024 |
| P5.4 | UNVERIFIED | [CFS/TFS refuge](persona-traceability.md#L62): meaningful source-backed retrieval cases not established. | AUD-036-RAG-015, AUD-036-RAG-024 |
| P6.1 | UNVERIFIED | [NT Code Blue](persona-traceability.md#L68): labelled fixtures do not prove actual cyclone shelter thresholds. | AUD-036-RAG-015, AUD-036-RAG-024 |
| P6.2 | PARTIAL | [Tiwi cultural risk](persona-traceability.md#L69): protection metadata/consent not carried through live retrieval. | AUD-036-RAG-003, AUD-036-RAG-015 |
| P6.3 | UNVERIFIED | [Remote resupply MOU](persona-traceability.md#L70): specific approved doctrine and coordination acceptance unproved. | AUD-036-RAG-015, AUD-036-RAG-018, AUD-036-RAG-025 |
| P6.4 | PARTIAL | [ACT/NSW smoke handoff](persona-traceability.md#L71): jurisdiction union supported; actual authority/agency partner matching incomplete. | AUD-036-RAG-015 |
| P7.1 | PARTIAL | [Reversible grounding](persona-traceability.md#L77): flags are now kill-switches, but real handler/audit behavior incomplete. | AUD-036-RAG-002 |
| P7.2 | PARTIAL | [Hermetic transport seam](persona-traceability.md#L78): required injection missing in MAF/controller despite fake tests. | AUD-036-RAG-020, AUD-036-RAG-024 |
| P7.3 | PARTIAL | [ADR-backed opt-outs](persona-traceability.md#L79): bodies/markers exist, new unmarked paths can bypass lint. | AUD-036-RAG-024 |
| P7.4 | PARTIAL | [Blue-green replay](persona-traceability.md#L80): wrapper exists; actual alias/provider/gate/pinning not complete. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-009 |
| P7.5 | PARTIAL | [Grounded/opt-out observability](persona-traceability.md#L81): undefined OB FR; real producer/workbook/table chain incomplete. | AUD-036-RAG-022, AUD-036-RAG-025 |
| P8.1 | PARTIAL | [Opt-out drift CI](persona-traceability.md#L87): marker-only lint does not discover new ungrounded inference. | AUD-036-RAG-024 |
| P8.2 | UNVERIFIED | [Rollback drill](persona-traceability.md#L88): activation sequencing superseded but actual retained regression/no-silencing drill unproved. | AUD-036-RAG-024, AUD-036-RAG-025 |
| P8.3 | UNVERIFIED | [Quarterly exhaustion](persona-traceability.md#L89): authored game-day runbook is not execution evidence. | AUD-036-RAG-017, AUD-036-RAG-025 |
| P8.4 | PARTIAL | [Golden gate](persona-traceability.md#L90): empty default runners pass; required meaningful fixture/candidate outputs absent. | AUD-036-RAG-024 |
| P9.1 | CONFLICT | [Operator-wide WCAG ask](persona-traceability.md#L96): broader than current UI-01 SHOULD/component scope and references undefined UX FR; no explicit resolution found. | AUD-036-RAG-021, AUD-036-RAG-025 |
| P9.2 | CONFLICT | [Precision at least 0.85](persona-traceability.md#L97): not the meaning of SC-007/FR-CV-03; no measured 50-query precision evidence or explicit supersession. | AUD-036-RAG-024, AUD-036-RAG-025 |
| P9.3 | PARTIAL | [Per-agent downgrade](persona-traceability.md#L98): configured thresholds have no live consumer/retuning evidence. | AUD-036-RAG-019, AUD-036-RAG-022 |
| P9.4 | PARTIAL | [Spool 60-second SLA](persona-traceability.md#L99): local spool exists, no acknowledged bounded central drain. | AUD-036-RAG-017 |
| P9.5 | UNVERIFIED | [Embedding golden parity](persona-traceability.md#L100): required actual model/build-keyed golden results are not produced. | AUD-036-RAG-008, AUD-036-RAG-024 |

The plan references fifteen R3 finding identifiers without their original review memos. Their quoted local obligations
are accounted, but the original reviewer conclusions, counts of 85 personas/89 findings/34 accepted findings and
consultation provenance are UNVERIFIED. The scope is not extended to unrelated implementations or other audit reports.

| Quoted review finding | Status | Local source and scoped response | Follow-up |
| --- | --- | --- | --- |
| F-ARCH-05 | PARTIAL | [Prod quorum blocker](plan.md#L345): current target-environment enforcement incomplete. | AUD-036-RAG-005 |
| F-ARCH-02 | PARTIAL | [Atomicity concern](plan.md#L378): concrete labels do not pin actual query clients. | AUD-036-RAG-009 |
| F-ARCH-03 | PARTIAL | [Cross-flip replay](plan.md#L378): cache/build/audit lineage remains unreliable. | AUD-036-RAG-009, AUD-036-RAG-012 |
| F-ARCH-14 | CONFLICT | [Legacy-null risk](plan.md#L463): schema/model retain incompatible legacy fields. | AUD-036-RAG-013 |
| F-ARCH-15 | PARTIAL | [Separate latency](plan.md#L416): missing actual producer/export/streaming correlation. | AUD-036-RAG-022 |
| F-DEL-01 | PARTIAL | [Windows cleanup](plan.md#L407): fixture/job authored; complete Windows-specific behavior not proven. | AUD-036-RAG-024 |
| F-DEL-05 | PARTIAL | [Keyboard focus](plan.md#L425): component toggle tests supported; actual operator-page reachability remains missing. | AUD-036-RAG-021 |
| F-DEL-06 | PARTIAL | [Telemetry integration](plan.md#L416): recorder shim does not export real instrument data. | AUD-036-RAG-022 |
| F-DEL-07 | PARTIAL | [Test taxonomy](plan.md#L413): documentation/markers exist; real discovery and acceptance semantics incomplete. | AUD-036-RAG-024 |
| F-DEL-08 | PARTIAL | [Encoding](plan.md#L407): UTF-8 environment/fixture work exists, actual cross-platform corpus assertions incomplete. | AUD-036-RAG-024 |
| F-PERF-02 | UNVERIFIED | [Concurrency](plan.md#L407): no attributable meaningful fifty-session measurement. | AUD-036-RAG-024, AUD-036-RAG-025 |
| F-TEST-01 | PARTIAL | [Fixture/test persistence](plan.md#L407): canonical file incomplete and old definitions remain. | AUD-036-RAG-024 |
| F-QA-03 | PARTIAL | [SC dashboard](plan.md#L422): authored workbook lacks nineteen correctly mapped measured tiles. | AUD-036-RAG-022 |
| F-SRE-01 | PARTIAL | [Freshness](plan.md#L388): actual drift schedule/signal/page chain absent. | AUD-036-RAG-022, AUD-036-RAG-023 |
| F-SRE-02 | PARTIAL | [False conflicts](plan.md#L461): disconnected detector lacks scope/false-positive/reversible-control proof. | AUD-036-RAG-018 |

### Plan Accountability

Each plan goal, milestone, risk and task checkpoint is accounted; a PASS heading is an authored assessment, not proof.
Risk identifiers below are prefixed `Plan-` to distinguish them from R-NN research decisions.

| Plan item | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| G1 | PARTIAL | [Inference migration](plan.md#L187): adapters/auth exist, SDK/seam/configuration contract conflicts remain. | AUD-036-RAG-020 |
| G2 | PARTIAL | [Policy/residency](plan.md#L188): checks lack resolved target data/signature enforcement. | AUD-036-RAG-004, AUD-036-RAG-005 |
| G3 | PARTIAL | [Whole corpus](plan.md#L189): ingestion exists without safe rights/state/parity/lifecycle completion. | AUD-036-RAG-006, AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-023 |
| G4 | PARTIAL | [Grounded fleet/chat](plan.md#L190): actual handlers/filter/audit/UI do not compose full chain. | AUD-036-RAG-002, AUD-036-RAG-012, AUD-036-RAG-019, AUD-036-RAG-021 |
| G5 | PARTIAL | [Opt-outs/offline](plan.md#L191): original artifacts exist, enforced audit/lint/cache/reconnect incomplete. | AUD-036-RAG-016, AUD-036-RAG-017, AUD-036-RAG-024 |
| G6 | SUPERSEDED | [Canary activation goal](plan.md#L192): Session 6 explicitly replaces activation mechanism, not no-silencing/regression obligations. | AUD-036-RAG-002, AUD-036-RAG-024, AUD-036-RAG-025 |
| M1 | PARTIAL | [Seam/gates milestone](plan.md#L196): authored pieces do not satisfy all real providers/current policy. | AUD-036-RAG-005, AUD-036-RAG-020 |
| M2 | UNVERIFIED | [First index publish](plan.md#L197): no attributable complete first-ingest/build/quality evidence. | AUD-036-RAG-007, AUD-036-RAG-023, AUD-036-RAG-025 |
| M3 | PARTIAL | [Fleet/simulation milestone](plan.md#L198): activation portion retired; real grounding and SSE consumers incomplete. | AUD-036-RAG-002, AUD-036-RAG-019, AUD-036-RAG-021 |
| M4 | PARTIAL | [Offline/QA milestone](plan.md#L199): signatures, bounds and genuine disambiguation acceptance incomplete. | AUD-036-RAG-016, AUD-036-RAG-017, AUD-036-RAG-024 |
| M5 | PARTIAL | [Closure/drills milestone](plan.md#L200): hard-cutover supersession limited; zero-import and actual cadence evidence unresolved. | AUD-036-RAG-020, AUD-036-RAG-025 |
| Plan-R1 | PARTIAL | [Embedding drift](plan.md#L263): actual live model state and exhaustive homogeneity gate incomplete. | AUD-036-RAG-007, AUD-036-RAG-008 |
| Plan-R2 | PARTIAL | [Quota exhaustion](plan.md#L264): activation sequencing retired; actual budget/filtered fallback/no-silencing remains. | AUD-036-RAG-001, AUD-036-RAG-002, AUD-036-RAG-022 |
| Plan-R3 | PARTIAL | [Hallucinated citation](plan.md#L265): filtering detached; synthetic gate cannot establish fidelity. | AUD-036-RAG-019, AUD-036-RAG-024 |
| Plan-R4 | PARTIAL | [Offline integrity](plan.md#L266): dual signature/payload authentication incomplete. | AUD-036-RAG-016 |
| Plan-R5 | PARTIAL | [Silencing](plan.md#L267): migration mechanism superseded, real fallback/kill-switch audit still needs enforcement. | AUD-036-RAG-002, AUD-036-RAG-020 |
| Plan-R6 | CONFLICT | [Staleness](plan.md#L268): 30-day exception not reconciled with signed 14-day manifest and query-time checks. | AUD-036-RAG-013, AUD-036-RAG-017 |
| Plan-R7 | PARTIAL | [Original timeout risk](plan.md#L269), [amended risk](plan.md#L467): actual query pinning/manual rollback/retention not operational. | AUD-036-RAG-009, AUD-036-RAG-010 |
| Plan-R8 | PARTIAL | [Audit gaps](plan.md#L270): durable per-call handlers/tables/alerts incomplete. | AUD-036-RAG-012, AUD-036-RAG-022 |
| Plan-R9 | PARTIAL | [Fake production seam](plan.md#L271): no full startup/provider validation or meaningful nonempty real-regression inputs. | AUD-036-RAG-020, AUD-036-RAG-024 |
| Plan-R10 | PARTIAL | [Chunk truncation](plan.md#L272): word splitting violates token/block guarantee and metrics not exported. | AUD-036-RAG-011, AUD-036-RAG-022 |
| Plan-R11 | PARTIAL | [Compatibility debt](plan.md#L273): actual providers remain diverse and tests cannot establish real parity; activation portions retired. | AUD-036-RAG-020, AUD-036-RAG-024 |
| Plan-R12 | PARTIAL | [Registry/licence drift](plan.md#L274): effective model registry and revoked-content index reconciliation incomplete. | AUD-036-RAG-005, AUD-036-RAG-006 |
| Plan-R13 | PARTIAL | [Original accessibility](plan.md#L275), [amended risk](plan.md#L468): component keyboard tests supported, actual workflow/manual evaluation unverified. | AUD-036-RAG-021, AUD-036-RAG-025 |
| Plan-R14 | UNVERIFIED | [Partial cultural population](plan.md#L459): human corpus/registry signatures/population not established. | AUD-036-RAG-003, AUD-036-RAG-005, AUD-036-RAG-025 |
| Plan-R15 | UNVERIFIED | [Federal attestation](plan.md#L460): real approval absent and authority list conflicts. | AUD-036-RAG-005, AUD-036-RAG-025 |
| Plan-R16 | PARTIAL | [False conflict risk](plan.md#L461): unscoped rules/IDs and detached consumer require repair. | AUD-036-RAG-018 |
| Plan-R17 | PARTIAL | [OTel degradation](plan.md#L462): actual bridge producer/export absent. | AUD-036-RAG-022 |
| Plan-R18 | CONFLICT | [Legacy row leakage](plan.md#L463): new validation contradicts additive absent/null tolerance. | AUD-036-RAG-013 |
| Checkpoint-0 | UNVERIFIED | [Build/lock/schema checkpoint](tasks.md#L69): raw mirrors supported; actual build/lock execution not performed or attributed. | AUD-036-RAG-024, AUD-036-RAG-025 |
| Checkpoint-A | PARTIAL | [Seam/CD/equivalence](tasks.md#L104): wrappers present; meaningful provider/gate validation incomplete. | AUD-036-RAG-005, AUD-036-RAG-020, AUD-036-RAG-024 |
| Checkpoint-B | UNVERIFIED | [Provision/ingest checkpoint](tasks.md#L146): actual first publish, no-reembed and staging flip not established. | AUD-036-RAG-007, AUD-036-RAG-023, AUD-036-RAG-025 |
| Checkpoint-C | PARTIAL | [Fleet canary/SSE checkpoint](tasks.md#L213): activation superseded, retained grounding/equivalence/fabrication promises incomplete. | AUD-036-RAG-002, AUD-036-RAG-019, AUD-036-RAG-024 |
| Checkpoint-D | PARTIAL | [Opt-out/offline/QA](tasks.md#L264): ADRs exist; complete lint, signed payload/reconcile and real fifty-query result absent. | AUD-036-RAG-016, AUD-036-RAG-017, AUD-036-RAG-024 |
| Checkpoint-E | CONFLICT | [Zero-import/final gate](tasks.md#L286): current exceptions and empty pass convention contradict closure; actual drills unverified. | AUD-036-RAG-020, AUD-036-RAG-024, AUD-036-RAG-025 |
| Checkpoint-F-A4 | PARTIAL | [Quorum/coupling](tasks.md#L574): target environment and real PR gates not enforced. | AUD-036-RAG-005 |
| Checkpoint-F-A5 | CONFLICT | [Audit/offline approval](tasks.md#L598): schema incompatibility and detached controls remain. | AUD-036-RAG-013, AUD-036-RAG-014, AUD-036-RAG-017 |
| Checkpoint-F-A7 | PARTIAL | [Pinning/rollback](tasks.md#L619): real concrete clients, event/timer/retention incomplete. | AUD-036-RAG-009, AUD-036-RAG-010 |
| Checkpoint-F-A1+A3 | UNVERIFIED | [Amended rebuild/ranking](tasks.md#L653): no genuine metadata rebuild or measured agency/ACT precision. | AUD-036-RAG-007, AUD-036-RAG-015, AUD-036-RAG-024 |
| Checkpoint-F-A2 | PARTIAL | [Consent checkpoint](tasks.md#L678): gate/default verification fail open in actual composition; human blockers retained. | AUD-036-RAG-003, AUD-036-RAG-025 |
| Checkpoint-F-A6 | PARTIAL | [Federal checkpoint](tasks.md#L700): SAR/PSPF are not mounted and actual sign-off CD gate absent. | AUD-036-RAG-005, AUD-036-RAG-026 |
| Checkpoint-F-A8 | PARTIAL | [Freshness checkpoint](tasks.md#L720): schedule/real UI/global alert consumer absent. | AUD-036-RAG-021, AUD-036-RAG-022, AUD-036-RAG-023 |
| Checkpoint-F-A10 | PARTIAL | [Test checkpoint](tasks.md#L736): authored lanes/tests not meaningful measured baseline/real E2E evidence. | AUD-036-RAG-024 |
| Checkpoint-F-A9 | PARTIAL | [Conflict checkpoint](tasks.md#L757): actual aggregation, stable IDs and authentic manual escalation absent. | AUD-036-RAG-018 |
| Checkpoint-F-A11 | PARTIAL | [Telemetry checkpoint](tasks.md#L778): recorder shim/wrong counters/inactive graph not live metrics/dashboard. | AUD-036-RAG-022 |
| Checkpoint-F-A12 | PARTIAL | [Accessibility checkpoint](tasks.md#L797): component tests supported, mounted/user-reviewed conformance unverified. | AUD-036-RAG-021, AUD-036-RAG-025 |
| Checkpoint-F-ADR | PARTIAL | [ADR checkpoint](tasks.md#L814): seven bodies plus pending ADR-15 exist; body semantics and sign-offs not all consistent/proven. | AUD-036-RAG-013, AUD-036-RAG-025 |

Phase sequencing, cross-cluster matrices and hypothesis closure are assessed against the same controlling defects.
The T188 rebuild is placed before T200's supposedly co-deployed cultural fields; T166/T188 refer to T222 as full E2E,
but T221 owns that body. Tests reference fixtures scheduled later. Same-PR coupling and subsequent-PR descriptions
must be reconciled without changing original evidence in this audit. All these obligations map to
AUD-036-RAG-007, AUD-036-RAG-013, AUD-036-RAG-024 and AUD-036-RAG-025.

### Recorded Reviews and Quickstart

| Record or review obligation | Status | Source and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| Analysis 1: FR coverage | CONFLICT | [Section](analyze-report.md#L9): stale 43-FR totals, wrong task identities and mere mention counts do not prove all producers/tests. | AUD-036-RAG-025 |
| Analysis 2: SC coverage | CONFLICT | [Section](analyze-report.md#L27): SC-003 through SC-009 meanings differ from original definitions; twelve-SC count stale. | AUD-036-RAG-025 |
| Analysis 3: entity coverage | CONFLICT | [Section](analyze-report.md#L50): thirteen claimed entities/paths do not match ten original plus two added catalogue and actual mirrors. | AUD-036-RAG-013, AUD-036-RAG-025 |
| Analysis 4: contracts | PARTIAL | [Section](analyze-report.md#L74): named producers/consumers/test files are not proof of actual composition; schemas can match while invalid semantically. | AUD-036-RAG-013, AUD-036-RAG-024 |
| Analysis 5: phases | CONFLICT | [Section](analyze-report.md#L89): task ranges/identities do not match actual definitions and omit later amendments. | AUD-036-RAG-025 |
| Analysis 6: cross-spec references | PARTIAL | [Section](analyze-report.md#L106): references are authored, not proof of inherited fallback/policy/test behavior; no other review report used. | AUD-036-RAG-025 |
| Analysis 7: closed questions | CONFLICT | [Section](analyze-report.md#L121): later contract/supersession/authority conflicts refute blanket no-outstanding-questions claim. | AUD-036-RAG-013, AUD-036-RAG-025 |
| Analysis 8.1: model literal | PARTIAL | [Hotspot](analyze-report.md#L129): fixed embedding literal does not establish live indexed model identity. | AUD-036-RAG-007, AUD-036-RAG-011 |
| Analysis 8.2: alias naming | CONFLICT | [Hotspot](analyze-report.md#L130): concrete corpus-vN name is not the corpus-search alias; labels do not prove pinning. | AUD-036-RAG-009, AUD-036-RAG-025 |
| Analysis 8.3: token scope | IMPLEMENTED | [Hotspot](analyze-report.md#L131): inspected credential code uses the named audience; real authentication remains UNVERIFIED. | - |
| Analysis 8.4: thresholds | PARTIAL | [Hotspot](analyze-report.md#L132): thresholds exist but zero-case/default-runner pass is not equivalence evidence. | AUD-036-RAG-024 |
| Analysis 8.5: offline TTL | CONFLICT | [Hotspot](analyze-report.md#L133): 30-day exception, query-time expiry and skip-success verification invalidate uniformity claim. | AUD-036-RAG-013, AUD-036-RAG-016, AUD-036-RAG-017 |
| Analysis 8.6: feature map | SUPERSEDED | [Hotspot](analyze-report.md#L134): activation ordering replaced explicitly by Session 6; real kill-switch behavior still incomplete. | AUD-036-RAG-002, AUD-036-RAG-025 |
| Analysis 9: no-remediation tally | CONFLICT | [Tally](analyze-report.md#L140): source defects and expanded counts invalidate shippable/no-remediation conclusion. | AUD-036-RAG-025 |
| Analysis 10: next actions | SUPERSEDED | [Actions](analyze-report.md#L154): activation sequence replaced by hard cutover; embedded commands were not executed. | AUD-036-RAG-025 |
| Quickstart prerequisites/setup | UNVERIFIED | [Prerequisites](quickstart.md#L9), [setup](quickstart.md#L27): prior uv/pnpm/ruff/build claims not rerun; no package installation/import/build allowed. | AUD-036-RAG-020, AUD-036-RAG-024, AUD-036-RAG-025 |
| Quickstart 2 | UNVERIFIED | [Identity login](quickstart.md#L50): authentication never attempted in this audit. | AUD-036-RAG-025 |
| Quickstart 3 | UNVERIFIED | [Provisioning](quickstart.md#L66): real deployment not attempted; selected root still has composition defects. | AUD-036-RAG-004, AUD-036-RAG-005, AUD-036-RAG-023 |
| Quickstart 4 | PARTIAL | [Local ingest](quickstart.md#L98): described CLI/provider/build contract differs from actual arguments/state; no invocation performed. | AUD-036-RAG-007, AUD-036-RAG-011, AUD-036-RAG-023 |
| Quickstart 5 | PARTIAL | [Agent run](quickstart.md#L124): flags do not make real dispatcher/MAF handler ground its inference. | AUD-036-RAG-002 |
| Quickstart 6 | PARTIAL | [Simulation](quickstart.md#L146): server hooks exist, full validated citation/audit/UI flow incomplete. | AUD-036-RAG-012, AUD-036-RAG-019, AUD-036-RAG-021 |
| Quickstart 7 | PARTIAL | [Test pyramid](quickstart.md#L196): some discovery/fixtures/gates differ; no tests executed. | AUD-036-RAG-024 |
| Quickstart 8 | PARTIAL | [Opt-out addition](quickstart.md#L223): existing lint cannot catch a missing marker on a new inference path. | AUD-036-RAG-024 |
| Quickstart 9 | PARTIAL | [Blue-green rebuild](quickstart.md#L237): real live state/parity/alias lifecycle not established; no script executed. | AUD-036-RAG-007, AUD-036-RAG-008, AUD-036-RAG-010 |
| Quickstart 10 | PARTIAL | [Offline deployment](quickstart.md#L267): bundle/signature/actual reader pipeline incomplete; no verifier run. | AUD-036-RAG-016, AUD-036-RAG-017 |
| Quickstart 11 | UNVERIFIED | [Audit replay](quickstart.md#L288): no actual one-month historical data/reproduction timing examined through runtime. | AUD-036-RAG-012, AUD-036-RAG-025 |
| Quickstart troubleshooting | PARTIAL | [Troubleshooting](quickstart.md#L319): recipes are instructions, not evidence; actual missing wiring must be corrected first. | AUD-036-RAG-023, AUD-036-RAG-025 |
| Quickstart 12 | CONFLICT | [Cultural seeding](quickstart.md#L350): scope/signature example differs from contract; actual human seeding remains unimplemented/unapproved. | AUD-036-RAG-003, AUD-036-RAG-013, AUD-036-RAG-025 |
| Quickstart 13 | PARTIAL | [Concurrency](quickstart.md#L377): wrong harness success/session/rate semantics and empty baseline prevent promised result. | AUD-036-RAG-024 |
| Quickstart 14 | PARTIAL | [Staging alias E2E](quickstart.md#L397): body unfinished; resolver/dictionary tests are not live smoke evidence. | AUD-036-RAG-009, AUD-036-RAG-024 |
| Quickstart 15 | PARTIAL | [WCAG verification](quickstart.md#L414): component assertions exist, actual mounted/manual conformance not established. | AUD-036-RAG-021, AUD-036-RAG-025 |
| Historical test counts/CI table | UNVERIFIED | [Recorded 3067/11/461s and exclusions](quickstart-validation.md#L119): attributed only to the authored older stub walk, not re-executed or independent current-SHA evidence. | AUD-036-RAG-025 |
| Historical smoke/sign-off | UNVERIFIED | [Automated sign-off](quickstart-validation.md#L143): verifier dry-run success is not cryptographic/cloud/human approval. | AUD-036-RAG-016, AUD-036-RAG-025 |
| Handoff T202/T203 | UNVERIFIED | [Human handoff](HANDOFF.md#L19): seeder raises NotImplementedError; actual authorised corpus/registry population not established. | AUD-036-RAG-003, AUD-036-RAG-005, AUD-036-RAG-025 |
| Handoff T210/T247 | CONFLICT | [Authority table](HANDOFF.md#L9): OAIC/ASD/AGD/owner differs from tasks NEMA/AGD/AFP; named endpoint/ADR paths drift. | AUD-036-RAG-005, AUD-036-RAG-025, AUD-036-RAG-026 |
| Handoff CD claims | PARTIAL | [Required checks](HANDOFF.md#L70): stated gates not wired into active CD; signatures/mapping/ADR publication remain blockers. | AUD-036-RAG-005 |
| Checklist resolution notes | CONFLICT | [Original closure](checklists/requirements.md#L146): presence/auto-ticking is not delivery; 177 appended items remain unchecked and substantive gaps persist. | AUD-036-RAG-025 |
| Checklist README coverage map | CONFLICT | [Index](checklists/README.md#L6): actual 342 definitions rather than 339; all three backfill items included here. | AUD-036-RAG-025 |
| Constitution PASS/complexity claims | UNVERIFIED | [Design gate](plan.md#L31), [complexity](plan.md#L281): authored PASS does not prove actual safe/grounded/private/audited behavior or human approval. | AUD-036-RAG-025 |

## Verification and Limits

The following checks were executed only as read-only text/inventory/integrity checks on this report and its cited inputs:

- Exact 241 original task definitions/states, suffix-capable matching and checked X/x equivalence: PASS.
  Dependency-note/cross-reference repetitions were excluded. No task IDs or source states were changed.
- Exact 68 FR and 19 SC definitions, with no missing/extra/duplicate coverage rows: PASS.
- Exact 38 story-local acceptance definitions and 342 checklist IDs/states, including all embedded appendices: PASS.
- Twenty-six unique unchecked `AUD-036-RAG-NNN` definitions, valid follow-up references and all six required task
  instruction fields (affected, expected/observed, developer, tester, future validation, completion): PASS.
- Balanced relative Markdown link parsing, including parentheses in path syntax, existing local targets and every
  single `#L` anchor within file bounds: PASS. No proposed nonexistent file is linked as evidence.
- Additional edge/assumption/exclusion/research/clarification/persona/goal/milestone/risk/checkpoint/review counts: PASS.
- Seven declared schema mirrors: raw byte parity supported. Eight duplicate audit-schema property names were found;
  semantic validation is not inferred from parity and remains an explicit remediation item.
- Read-only Git metadata matched expected HEAD; tracked diff was empty. The only authorised write was this report.
- Report editor diagnostics: the sole MD047 final-newline warning was corrected by EOF-only formatting; no product
  diagnostics, tests, SDK imports, verifier scripts, builds, servers, browsers, cloud queries or deployments were run.

External blockers remain: unavailable original persona/R3 memo evidence; incomplete real corpus/model/retrieval and
staging/load/replay artifacts; qualified community/federal sign-offs; manually attributable accessibility and game-day
reviews. T202, T203, T210 and T247 cannot be completed by software or this audit. Platform assumptions about endpoint
compatibility, identity, network, cryptographic trust, actual data residency/retention and deployed resources are
UNVERIFIED until separately authorised validation supplies attributable evidence.

All developer/tester commands in this report are future-only instructions with prerequisites, not actions executed here.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 036 Foundry RAG only. Three parallel technical reviews examined
complete-envelope minimisation, retrieval/index lifecycle, and carve-out/consent/audit composition. The unknown-region
fail-open hypothesis is already falsified by the shared Foundry client, which raises configuration failure when the region
is unresolved and requires a gateway for non-AU requests. The proposed alias-pinning fix could not be applied safely
because no current retrieval-service implementation seam exists in the workspace; only the contract test is present.

Remaining open work includes complete history/system/tool/embedding minimisation, mandatory retrieval in mounted paths,
citation validation, index lifecycle/freshness/offline cache, cultural authority and carve-out registries, durable denial
audit, deployment composition, performance, and human/provider evidence.

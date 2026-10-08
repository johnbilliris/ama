# Monitoring Agent Implementation Audit

**Review date:** 2026-09-11  
**Source revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (local HEAD verified)  
**Mode:** Fresh-context, review-only STATIC audit.  
**Disposition:** Not implementation-complete. Critical integration and safety boundaries are not established.

## Scope and Evidence Rules

This report covers **69/69 original tasks**, **41/41 requirements** (29 FR, 4 NFR, 8 SC),
**23/23 numbered acceptance scenarios**, **6/6 edge cases**, **10/10 amendment identifiers**
(3 PER, 4 HYP, 3 SCP), **74/74 checklist items**, and the plan's **20/20 constitution-gate claims**.
All 69 original tasks are checked `[X]`; all 74 local checklist items are unchecked `[ ]`.
The task document's summary says 66, but its actual entries are T001 through T069. The entries,
not that summary, determine this audit's denominator. There are **34 open remediation tasks** below.

Only this report was authored. Original specifications, tasks, evidence, application code, infrastructure,
the central audit index, branches, and commits are outside the edit boundary. Other implementation-audit
reports were not used. Existing untracked reports were left alone. No application imports, product tests,
builds, deployments, cloud-resource queries, fixes, or delegation were performed. Commands in reviewed
documents were read as evidence, never executed. Terminal use was limited to Git metadata and text-only
indexing/document validation. Public reference documentation was consulted for session and cancellation
semantics; it is not evidence of deployed configuration or successful execution.

The evidence statuses follow the [Review Contract](../001-spec-implementation-audit/README.md#L15):

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | The specific scoped behavior or authored artifact is supported by inspected source; no test-run or deployment success is implied. |
| PARTIAL | Some behavior exists, but an identified obligation is missing or contradicted. |
| MISSING | The required behavior/artifact was not found after the connected and renamed-path search described below. |
| CONFLICT | Current requirements, design decisions, or implementation disagree and need an explicit owner decision. |
| UNVERIFIED | Execution, measurement, sign-off, or deployed state cannot be established from available evidence. |
| SUPERSEDED | Requires an explicit replacement/retirement reference; a newer filename alone is insufficient. |

### Inputs Read in Full

- [spec.md](spec.md), including both 2026-04-11 clarification sessions, personas, hypotheses, scope deferrals,
  and the feature-028 country amendments.
- [tasks.md](tasks.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
  and [quickstart.md](quickstart.md).
- [contracts/signal-processing.md](contracts/signal-processing.md),
  [contracts/health-endpoint.md](contracts/health-endpoint.md), and [contracts/telemetry.md](contracts/telemetry.md).
- [checklists/requirements.md](checklists/requirements.md) and all three local evidence files:
  [evidence/HYP-033.md](evidence/HYP-033.md), [evidence/HYP-034.md](evidence/HYP-034.md),
  [evidence/HYP-035.md](evidence/HYP-035.md). No other local review record was present in the directory inventory.
- [Constitution](../../.specify/memory/constitution.md#L1), including its bounded model-hosting carve-out;
  [code review instructions](../../.github/instructions/code-review.instructions.md#L1),
  [commenting instructions](../../.github/instructions/code-commenting.instructions.md#L1),
  [Bicep instructions](../../.github/instructions/bicep-code-best-practices.instructions.md#L1),
  [Bicep policy instructions](../../.github/instructions/bicep-policy-compliance.instructions.md#L1),
  and the Python fact-grounded, Cosmos DB best-practices, and Microsoft documentation skills.
  No root Copilot instruction file was present at the advertised conventional location.
- Amendment references: [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1),
  [hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1),
  [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1), and the relocated
  [post-feature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L1).
  These are original associated evidence records, not other implementation audits.

### Connected Paths and Negative-Claim Search

| Path investigated | Controlling evidence and result |
| --- | --- |
| Deployed process | [azure.yaml:9](../../azure.yaml#L9) selects the root infrastructure; [Dockerfile:48](../../apps/agents/Dockerfile#L48) starts the dispatcher. [Dispatcher:189](../../apps/agents/dispatcher/agent.py#L189) creates only health and question-invocation routes, not the monitoring worker or association API. |
| Legacy monitoring | [Entry point:571](../../apps/agents/monitoring/agent.py#L571) constructs an agent without a repository or LLM and starts HTTP. [Pipeline:46](../../apps/agents/monitoring/pipeline.py#L46) defaults to memory-only audit and no delivery callback. No production construction/call of `SignalProcessingPipeline` was found in the searched applications. |
| Ingestion to monitoring | [API ingestion:13](../../apps/api/app/api/routes/signals.py#L13) stores a signal; [worker factory:208](../../apps/ingestion/worker.py#L208) injects blob/dedup services, not monitoring; [base pipeline:191](../../apps/api/app/services/ingestion/pipeline_base.py#L191) has optional persistence but no monitoring publish step. |
| Alternative runtime | [MAF monitoring:25](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) calls summary/builder directly. [Workflow:89](../../apps/agents/maf_runtime/workflow/builder.py#L89) advances to risk assessment regardless of monitoring's decision. The [common handoff deprecation notice](../../apps/agents/common/handoffs.py#L1) documents replacement intent, not preservation of spec-010 safety invariants. |
| Simulation subscription | [Orchestrator:232](../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L232) publishes synthetic events. [Registry:24](../../apps/api/app/services/simulation/subscriber_registry.py#L24) routes hazards to Risk/Evac/Resource/Planning, not monitoring. [Monitoring adapter:9](../../apps/api/app/services/simulation/sub_agents/monitoring_adapter.py#L9) sends a question to the dispatcher, not a normalized signal. |
| IoT alternative | [Adapter:119](../../apps/agents/monitoring/iot_adapter.py#L119) emits a different flattened schema. [Tests:52](../../tests/unit/test_iot_adapter.py#L52) assert that schema, not `SignalEnvelope` validation or monitoring processing. No connected webhook-to-monitoring-pipeline caller was found. |
| Retrospective persistence | Both signal repositories were inspected. The [API repository:18](../../apps/api/app/repositories/signal_repository.py#L18) lacks association methods; the [domain repository:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120) provides them with incompatible arguments and an empty Cosmos update branch. |
| Delivery and notifications | [Shared retry:124](../../apps/agents/common/handoffs.py#L124), [EventBus:28](../../apps/api/app/services/event_bus.py#L28), [handoff listing:8](../../apps/api/app/api/handoffs.py#L8), and [dead-letter routes:24](../../apps/api/app/api/routes/dead_letters.py#L24) exist. No monitoring callback/subscriber joins those stores; the pipeline's default dead-letter callback returns only a string. |
| Renamed infrastructure | [monitoring-agent.bicep:43](../../infra/bicep/monitoring-agent.bicep#L43) contains the intended container and queue. The similarly named [monitoring.bicep:1](../../infra/bicep/monitoring.bicep#L1) is generic observability. Neither deployment root references the agent module. |
| Renamed tests/evaluations | Inspected all named monitoring unit/contract tests, handoff/storage tests, the [benchmark](../../tests/benchmark/test_pipeline_performance.py#L189), [MAF equivalence test](../../tests/equivalence/test_monitoring_equivalence.py#L26) and its recorded fixture, synthetic signal integration tests, IoT tests, and the [Foundry monitoring fixture](../../apps/eval-runner/fixtures/spec036/monitoring.jsonl#L1). None substitutes for the missing Cosmos/Service Bus monitoring integration or sustained-load harnesses. |

Searches covered relevant Python under `apps`, `packages`, and `tests`, monitoring-specific names and
call sites, `infra` module references and queue/container names, and evaluation fixtures. They included
`process_signal`, `SignalProcessingPipeline`, `MonitoringAgent`, association methods, subscriber registration,
Service Bus clients, telemetry names, dead-letter callbacks, and the moved infrastructure/test surfaces.
An initially broad editor search timed out and was replaced with narrower completed searches. `rg` was
unavailable; editor searches and read-only Node text indexing were used. Absence claims are bounded to
this revision and these repository surfaces, not to uninspected external deployments.

## Prioritized Findings

| Priority | Follow-up | Finding and concrete impact |
| --- | --- | --- |
| P0 | AUD-001 | No connected production signal intake/worker; arrivals do not reach the six-stage monitoring path. |
| P0 | AUD-002 | Direct builder and MAF workflow bypass credibility/triage decisions; unsafe or ineligible signals can progress to risk assessment on those paths. |
| P0 | AUD-003 | Tenant identity is caller-supplied/default-live and caches are unscoped; simulation can affect live decisions or routing. |
| P0 | AUD-004 | Association endpoint has no Managed Identity authorization or trusted incident/tenant check; an exposed instance permits unauthorized reassociation attempts. |
| P1 | AUD-005 | Association repository signature mismatch, empty Cosmos update, missing spatial/CAS guards prevent correct association. |
| P1 | AUD-006 | Handoffs/DLQs are not durably connected to delivery or commander notifications. |
| P1 | AUD-007 | Free-text summaries, incomplete safety validation, and discarded filter metadata undermine safe structured outputs. |
| P1 | AUD-008 | Substring classification accepts invalid responses such as `not credible`; unexpected responses are mislabeled as timeouts. |
| P1 | AUD-009 | Blocked/held signals have no implemented persisted status/review workflow. |
| P1 | AUD-010 | Earthquake/tsunami producer and stored category contracts disagree with the escalation set. |
| P1 | AUD-011 | API ingestion invents `incident-default`, defeating the null-incident guard. |
| P1 | AUD-012 | Summary is generated twice, so the audited summary can differ from the handoff. |
| P1 | AUD-013 | Synchronous, repeated LLM calls and an ignored transport timeout violate the designed latency budget. |
| P1 | AUD-014 | Rule-based fallback lacks the required reduced-confidence annotation. |
| P1 | AUD-015 | No time-driven freshness monitoring or missing-source confidence adjustment is connected. |
| P1 | AUD-016 | Memory/ephemeral spill can lose audits; no automatic recovery flush is connected. |
| P1 | AUD-017 | Flush can reorder records, stall on duplicate-create conflicts, and report misleading status. |
| P1 | AUD-018 | Receipt/negative decisions, evaluated inputs, provenance, full handoff linkage, and terminal result are incomplete. |
| P1 | AUD-019 | Incident declaration does not trigger association; association audit is one synthetic batch record. |
| P1 | AUD-020 | Health reports configuration and zero queue depth, not dependency readiness. |
| P1 | AUD-021 | Required monitoring metrics, stage traces, correlation propagation, and named events are absent. |
| P1 | AUD-022 | Seven monitoring-specific alert conditions are not configured. |
| P1 | AUD-023 | Monitoring infrastructure module is orphaned; queue-depth scaling/serverless assumptions are not wired. |
| P1 | AUD-024 | Create-only application behavior does not enforce append-only access or prove retention in deployment. |
| P1 | AUD-025 | Paired independent regional operation is unproved and conflicts with replication/global-hosting assumptions. |
| P1 | AUD-026 | Core configuration and audit-model invariants are not enforced. |
| P1 | AUD-027 | Mock prompt tests do not establish credibility-role isolation or injection resistance. |
| P1 | AUD-028 | Required monitoring Cosmos integration assertions are missing. |
| P1 | AUD-029 | Required broker/association integration assertions are missing. |
| P1 | AUD-030 | Bushfire test exercises only signal generation, not monitoring's decision chain. |
| P1 | AUD-031 | Sustained throughput and timing outcomes are unverified; the benchmark reuses a deduplicated ID. |
| P1 | AUD-032 | No representative labeled misinformation evaluation establishes the <5% false-positive target. |
| P1 | AUD-034 | Per-process dedup is not restart-safe and marks work before a terminal durable outcome. |
| P2 | AUD-033 | Quickstart, checklist/gate completion, and amendment validation claims need evidence and conflict resolution. |

## Remediation Plan

All tasks below are **unchecked, unexecuted, and prospective**. A task's tester instructions are separate
from its developer work. Tests must exercise the owning implementation, not only a helper or fabricated
expected output. Existing test paths are linked; absent paths are explicitly marked **proposed**.
Command identifiers refer to the future-only command/prerequisite catalogue after the coverage tables.
No remediation in this section is authorization to perform product work during this audit.

### AUD-001: Connect the Operational Signal Worker

- [ ] AUD-001 (P0) Establish an actual ingestion-to-monitoring execution path.

**Affected:** T029, T036, T043, T060, T063; FR-001, FR-010, FR-020; NFR-002; SC-001, SC-002, SC-006; EC-06.

**Expected versus observed / impact:** Normalized messages must be consumed, processed, audited, and settled.
[Dockerfile:48](../../apps/agents/Dockerfile#L48) starts a question dispatcher; its
[routes:200](../../apps/agents/dispatcher/agent.py#L200) neither subscribe nor mount the legacy monitoring app.
The [legacy entry point:571](../../apps/agents/monitoring/agent.py#L571) also starts no pipeline.
[Ingestion:191](../../apps/api/app/services/ingestion/pipeline_base.py#L191) ends in optional storage/audit,
not a monitoring publication. A working unit pipeline therefore does not deliver the operational feature.

**Developer instructions:** Own the startup/composition boundary in the existing dispatcher/monitoring entry
points and ingestion base/factory. Decide and document a supported worker entry point without replacing the
simulation question API. Wire one configured pipeline with the real signal repository, audit container, LLM,
trusted tenant context, receiver, and risk-delivery callback. Publish stable signal IDs and session/trace metadata
after persistence; settle messages only after a durable terminal outcome. Add shutdown/lock-renewal behavior.

**Tester instructions:** Reuse [_make_valid_signal](../../tests/unit/test_monitoring_pipeline.py#L23), but drive
the actual publisher and worker startup in the proposed `tests/integration/test_monitoring_service_bus.py`.
Positive: a valid fire signal yields one persisted handoff and audit chain. Negative: malformed message is
audited/rejected without killing the worker. Edge: restart between receipt and settlement causes safe redelivery,
and startup failure cannot advertise operational readiness.

**Dependencies / future validation:** AUD-002, AUD-003, AUD-006, AUD-016, AUD-023, AUD-034; F-SB with P-BROKER/P-PY.
**Acceptance:** A transport-driven test reaches the real pipeline without directly calling `process_signal`,
proves settlement semantics, and the documented production command instantiates those same dependencies.

### AUD-002: Enforce Credibility and Triage Gates Across Runtimes

- [ ] AUD-002 (P0) Prevent direct/MAF paths from bypassing monitoring decisions.

**Affected:** T020, T024, T027, T028, T033, T035, T036, T040, T069; FR-004 through FR-012;
SC-002, SC-003; US2-AS1 through US2-AS4; EC-02, EC-03.

**Expected versus observed / impact:** Every escalated signal must be evaluated before downstream work.
[Builder:89](../../apps/agents/monitoring/agent.py#L89) does not inspect `validationStatus`.
[MAF legacy:25](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) calls that builder directly, and
[workflow:89](../../apps/agents/maf_runtime/workflow/builder.py#L89) invokes risk assessment unconditionally.
[The alleged blocking test:62](../../tests/contract/test_monitoring_escalation.py#L62) discards the builder's return.
The local pipeline's correct ordering does not protect these other callable paths.

**Developer instructions:** Make validated, tenant-bound processing outcomes the sole authority for handoff
creation and workflow transitions. Keep a low-level builder internal or require a validated decision context.
MAF legacy/maf/shadow paths must preserve blocked/held/suppressed outcomes and must not let model text decide
whether mandatory code gates execute. Apply evaluation to escalated non-social signals too. Preserve explicitly
documented legacy fallback compatibility while replacing its unsafe direct use.

**Tester instructions:** Extend [classification contracts:40](../../tests/contract/test_monitoring_escalation.py#L40)
and the real workflow tests. Assert a risk executor spy is never called for misinformation, unavailable/timeout/
unexpected classification, low effective confidence, unsupported category, or absent incident. Positive: credible
eligible input calls it exactly once. Edge: escalated IoT, all five categories, and each runtime flag mode.

**Dependencies / future validation:** AUD-008, AUD-009; F-MISINFO/F-PIPELINE/F-MAF with P-PY.
**Acceptance:** No supported entry point reaches risk assessment unless the deterministic safety and escalation
gates permit it; tests assert downstream calls and persisted decisions, not classification strings alone.

### AUD-003: Carry Trusted Tenant Scope Through Every Stage

- [ ] AUD-003 (P0) Bind tenant, signal, incident, cache, and routing identities.

**Affected:** T029, T031, T032, T035, T036, T046, T048; FR-001, FR-015, FR-029; EC-04, EC-05.

**Expected versus observed / impact:** Simulation and live signals must never influence one another.
[process_signal:366](../../apps/agents/monitoring/pipeline.py#L366) trusts an independent `tenant_id="live"`
argument; the [input model:25](../../apps/api/app/validators/signal_envelope.py#L25) carries no tenant identity.
[Dedup:107](../../apps/agents/monitoring/pipeline.py#L107) keys only by signal ID, and
[freshness:36](../../apps/agents/monitoring/freshness.py#L36) only by source ID.
[MAF:25](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) constructs a live scope. A simulation
duplicate can suppress live processing, and simulation freshness can change live operational state.

**Developer instructions:** Own scope validation at the transport/agent boundary, not just repository queries.
Require authenticated or broker-verified tenant metadata and compare it to signal/incident ownership; reject
mismatches and missing scope outside explicit local fixtures. Key dedup/freshness by tenant and region as well as
entity ID. Include tenant-qualified scope in handoffs and propagate it unchanged into the risk consumer.
Do not silently map unknown simulation tenant formats to live.

**Tester instructions:** Extend [pipeline tests:129](../../tests/unit/test_monitoring_pipeline.py#L129) with
same signal/source/incident IDs in live and two distinct simulations. Positive: independent scoped processing.
Negative: forged body tenant and foreign incident are rejected with an audit. Edge: MAF fallback, replay, and
source recovery in one tenant leave the other tenant's cache, freshness, handoff, and records unchanged.

**Dependencies / future validation:** AUD-001, AUD-004, AUD-005, AUD-034; F-PIPELINE/F-SB with P-PY/P-BROKER.
**Acceptance:** Isolation tests compare actual cache/store/delivery effects in both directions; no default-live
conversion occurs on production ingress and all outbound scope keys agree with trusted context.

### AUD-004: Authorize and Validate Retrospective Association Requests

- [ ] AUD-004 (P0) Enforce the association API's identity and error contract.

**Affected:** T042, T045, T046, T049; FR-013, FR-015, FR-016; health contract; CHK053, CHK064, CHK065.

**Expected versus observed / impact:** The [contract:82](contracts/health-endpoint.md#L82) requires Managed
Identity service authentication. [Route:345](../../apps/agents/monitoring/agent.py#L345) has none, accepts
arbitrary incident/tenant strings, and uses a request default of 24 rather than the configured default.
Invalid requests follow FastAPI's default validation behavior instead of the specified 400, and exception
messages are returned under `detail`. An exposed legacy app would accept unauthenticated mutation requests.

**Developer instructions:** Add service-token audience/issuer/expiry validation and an authorized role/dependency;
bind tenant and incident access to that identity. Keep the probe unauthenticated. Validate nonblank IDs and
bounded positive lookback values; use configuration when omitted. Return the agreed 400/503 public shape,
sanitized messages, and distinguish unavailable repository from successful zero matches. Do not assume
internal ingress is authorization.

**Tester instructions:** Use actual [create_app:225](../../apps/agents/monitoring/agent.py#L225) in association
contract tests, overriding only the identity verifier for positive cases. Assert 401/403 for absent/expired/wrong-
audience identities and foreign scope, 400 for invalid fields, config default propagation, 200 for valid zero/many,
and sanitized 503 on storage failure. Verify denied requests do not call the repository or create associations.

**Dependencies / future validation:** AUD-003, AUD-005; F-ASSOC/F-SB with P-PY and later P-IDENTITY.
**Acceptance:** Authenticated permitted scope is required for every association mutation, errors match the
published contract, and no internal exception or credential material is exposed.

### AUD-005: Make Retrospective Association Correct and Durable

- [ ] AUD-005 (P1) Repair repository compatibility, scoped matching, and atomic updates.

**Affected:** T045, T046, T048, T049; FR-013, FR-014, FR-015, FR-016; US4-AS1 through US4-AS4; SC-004.

**Expected versus observed / impact:** [Agent:202](../../apps/agents/monitoring/agent.py#L202) passes `tenant_id`
to [query_unassociated:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120), which
accepts `scope`. Its memory query ignores scope; [update:148](../../packages/domain/src/domain/repositories/signal_repository.py#L148)
does nothing for Cosmos and has no tenant or null-state precondition. No location comparison is performed.
The caller increments counts after that no-op. Direct query/update errors escape rather than returning the
documented safe result. Existing [storage tests:95](../../tests/contract/test_signal_storage.py#L95) use memory only.

**Developer instructions:** Define one repository interface shared with ingestion and monitoring. Pass scope,
jurisdiction, cutoff, and explicit incident geometry/matching policy consistently. Implement Cosmos updates
using the true hierarchical partition values and optimistic concurrency; update only still-unassociated records
in the authorized scope. Keep memory behavior semantically identical. Count confirmed successful changes,
handle partial failures honestly, and preserve already-associated signals. Reconcile the safe-error function
contract with the HTTP 503 contract without masking partial completion.

**Tester instructions:** Extend [association contracts:48](../../tests/contract/test_incident_association.py#L48)
and [storage contracts:50](../../tests/contract/test_signal_storage.py#L50) with the real agent and repository.
Assert five eligible links, exclusion at 30 hours/outside geometry/wrong jurisdiction/wrong tenant, preservation
of pre-associated signals, exact cutoff behavior, concurrent competing incidents, retries, and query/update failure.

**Dependencies / future validation:** AUD-003, AUD-004, AUD-019; F-ASSOC/F-COSMOS with P-PY/P-COSMOS.
**Acceptance:** No signature error/no-op path remains; returned counts equal persisted unique changes and
race/failure tests cannot overwrite another incident or cross scope.

### AUD-006: Persist Delivery Outcomes and Surface Dead Letters

- [ ] AUD-006 (P1) Connect durable handoff delivery, retry, DLQ, and commander visibility.

**Affected:** T035, T036, T052, T063; FR-010, FR-011, FR-020, FR-021; US1-AS5, US6-AS4; CHK004, CHK038, CHK068.

**Expected versus observed / impact:** [Pipeline:64](../../apps/agents/monitoring/pipeline.py#L64) fabricates a
dead-letter ID and [triage:289](../../apps/agents/monitoring/pipeline.py#L289) skips delivery when its callback is
absent. [EventBus:37](../../apps/api/app/services/event_bus.py#L37) and
[DLQ listing:24](../../apps/api/app/api/routes/dead_letters.py#L24) use different unconnected stores.
[Retry tests:38](../../tests/integration/test_handoff_retry.py#L38) assert a returned ID, not durable visibility.
A created event or a string callback therefore does not establish delivery or notification.

**Developer instructions:** Own the monitoring delivery adapter and shared handoff boundary. Persist the complete
event, source signal reference, tenant-qualified scope, and attempt outcomes; connect one real retry/dead-letter
store and commander notification route. Resolve the terminology conflict between three retries and the shared
helper's three total attempts; document creation versus delivery SLA boundaries. Make notification failure
recoverable and redelivery idempotent. Preserve the explicit MAF replacement/fallback contract.

**Tester instructions:** Extend [retry tests:6](../../tests/integration/test_handoff_retry.py#L6) and
[handoff-chain test:5](../../tests/integration/test_handoff_chain.py#L5) with the actual monitoring adapter.
Positive: transient error then success, correct payload and timestamps. Negative: permanent failure results in a
queryable DLQ and commander alert. Edge: callback failure, timeout, duplicate acknowledgment, restart, and
manual redelivery cannot create duplicate risk work or silently lose the notification.

**Dependencies / future validation:** AUD-001, AUD-003, AUD-018, AUD-021, AUD-022; F-HANDOFF/F-SB with P-PY/P-BROKER.
**Acceptance:** Every created handoff has a durable terminal or pending-retry state, with a measurable,
tenant-scoped commander-visible record for every exhausted delivery.

### AUD-007: Enforce Safe Structured Downstream Output

- [ ] AUD-007 (P1) Close content-safety and structured-output gaps.

**Affected:** T029, T034, T038, T069; FR-003, FR-026, FR-028; US3-AS2; CHK005, CHK006, CHK020, CHK050, CHK067.

**Expected versus observed / impact:** FR-003 permits only structured classification fields, but
[summary:53](../../apps/agents/monitoring/agent.py#L53) adds unrestricted `llm_summary` text derived from raw
payload. It calls [validate:106](../../apps/agents/common/content_safety.py#L106) without locale or a 200-character
limit, ignores `review_flag`, and performs no downstream PII/factual validation. Azure validation returns before
locale checking; keyword fallback checks only two terms. [LLM response conversion:214](../../apps/agents/common/llm_client.py#L214)
does not preserve the Foundry safety-filter flag. Prompt/completion RAI policies do exist in
[model infrastructure:145](../../infra/modules/azure-openai.bicep#L145); their deployment is unverified.

**Developer instructions:** Resolve the structured-only versus narrative-summary design conflict with the owner,
then enforce a versioned allowlisted output schema. Validate final downstream output for the agreed locale,
length, PII, and harmful/misleading content, independent of Azure filter availability. Preserve filter/fallback
metadata and route uncertain validation to the specified conservative outcome. Do not treat field names or a
keyword-only pass as proof of safe contents; sanitize fallback fields too.

**Tester instructions:** Strengthen [summary tests:149](../../tests/unit/test_monitoring_pipeline.py#L149) to assert
actual output and audit contents. Positive: safe metadata survives. Negative: PII, wrong language, excessive
length, filtered partial completion, and unsafe text never enter a handoff. Edge: unavailable safety service,
empty output, malicious metadata, and injected validator must yield the exact fallback and safety audit.

**Dependencies / future validation:** AUD-012, AUD-018, AUD-027, AUD-033; F-SAFETY/F-PIPELINE with P-PY; P-MODEL later.
**Acceptance:** Every propagated output meets the approved schema and safety checks; failures are explicit,
auditable, and do not leak raw user content.

### AUD-008: Parse Classifications Exactly and Preserve Failure Reasons

- [ ] AUD-008 (P1) Make the credibility parser fail closed on invalid classifications.

**Affected:** T023, T024, T026, T027, T028, T033; FR-007, FR-008; SC-002, SC-003; EC-03.

**Expected versus observed / impact:** Only three exact classifications are valid.
[agent.py:163](../../apps/agents/monitoring/agent.py#L163) uses substring membership: `not credible`/`incredible`
can pass, while `not misinformation` can be blocked. [pipeline.py:240](../../apps/agents/monitoring/pipeline.py#L240)
relabels unexpected responses as `llm_timeout`. Current [unexpected-response test:104](../../tests/contract/test_monitoring_escalation.py#L104)
covers only a phrase containing none of the valid words.

**Developer instructions:** Use a strict normalized enum parser or a constrained response schema. Separate
timeout, service unavailability, content filtering, malformed result, and unexpected text in the result/audit
contract. Keep suspicious penalty distinct and clamp effective confidence consistently. Retain evaluated input
references and bounded diagnostic detail without logging raw sensitive output.

**Tester instructions:** Parameterize the actual evaluation/pipeline path with all valid words, casing/whitespace,
negated phrases, substrings, mixed words, punctuation policy, empty/non-string/malformed responses, raised
exceptions, and timeout. Assert the exact classification/reason, no downstream handoff for invalid outcomes,
and one appropriate decision record. Confirm suspicious confidence is penalized exactly once.

**Dependencies / future validation:** AUD-018, AUD-026; F-MISINFO/F-PIPELINE with P-PY.
**Acceptance:** No response outside the approved enum becomes credible or misinformation merely by substring;
stored reasons distinguish each failure mode and invalid outcomes are held.

### AUD-009: Persist Blocked and Held Signals for Review

- [ ] AUD-009 (P1) Implement durable misinformation status and human-review disposition.

**Affected:** T026, T033, T036; FR-005, FR-006, FR-008, FR-012, FR-020; US2-AS1, US2-AS3; SC-003; CHK041, CHK042, CHK065.

**Expected versus observed / impact:** [Misinformation stage:168](../../apps/agents/monitoring/pipeline.py#L168)
only writes a decision and stops. No signal-store update or durable review item is created. The
[Signal status enum:28](../../packages/domain/src/domain/models/signal.py#L28) cannot represent
`misinformation_flagged`. A held log entry in an in-memory audit buffer is not an actionable preserved signal.

**Developer instructions:** Extend the owning signal/status contract compatibly and persist the original signal
with its review disposition, classification, reason, scope, and input reference. Define the authorized review
owner, queue/API, resolution states, and re-evaluation policy; do not silently release on model recovery.
Clarify whether flagged/held records are excluded from retrospective association. Preserve source evidence
under the approved privacy/access policy rather than copying it into unrestricted output.

**Tester instructions:** Extend [classification contracts:40](../../tests/contract/test_monitoring_escalation.py#L40)
through the real pipeline/repository. Assert misinformation status read-back, held item visibility after restart,
zero delivery for all holds, and unchanged signal ID/provenance. Edge: repeated hold, duplicate review response,
unauthorized reviewer, and persistence failure must not lose the signal or auto-escalate it.

**Dependencies / future validation:** AUD-003, AUD-008, AUD-016, AUD-028, AUD-033; F-MISINFO/F-COSMOS with P-PY/P-COSMOS.
**Acceptance:** Every blocked/held input is durably retrievable with correct scope/status and an auditable,
authorized next action; no storage schema rejects the required status.

### AUD-010: Align Hazard Categories From Feed to Escalation

- [ ] AUD-010 (P1) Preserve earthquake and tsunami semantics across ingestion, storage, and monitoring.

**Affected:** T007, T021, T022, T037, T040, T063; FR-001, FR-009, FR-019; US1-AS1; SC-001.

**Expected versus observed / impact:** [Monitoring categories:35](../../apps/agents/monitoring/agent.py#L35)
include earthquake/tsunami, but [earthquake normalization:56](../../apps/ingestion/pipelines/ga_earthquakes.py#L56)
sets `geohazard`; [GeoJSON mapping:14](../../apps/ingestion/normalisers/geojson_normaliser.py#L14) does likewise.
[Signal:11](../../packages/domain/src/domain/models/signal.py#L11) accepts neither specific category. Tsunami
inherits [BoM normalization:21](../../apps/ingestion/normalisers/bom_xml_normaliser.py#L21), whose category map
has no tsunami entry. Hand-authored category tests therefore do not prove feed-originated hazard escalation.

**Developer instructions:** Agree a canonical hazard taxonomy with spec-006 owners and preserve hazard subtype
and true source provenance while maintaining stored-record compatibility. Map eligible hazard subtypes explicitly;
do not escalate every generic geohazard indiscriminately. Update producers, domain/schema consumers, and
monitoring together. Avoid labeling a substituted feed as another authority without provenance disclosure.

**Tester instructions:** Use [GA fixture:46](../../tests/contract/test_geojson_normaliser.py#L46) and real normalizers,
then store and process the resulting envelope. Assert earthquake and tsunami escalation when effective confidence
and incident conditions pass; generic unrelated geohazards must not escalate. Edge: legacy stored `geohazard`,
unknown subtype, and correct category/source identity in audit and risk handoff.

**Dependencies / future validation:** AUD-001, AUD-018; F-INGEST/F-PIPELINE with P-PY, then F-SB.
**Acceptance:** Actual normalized eligible hazards survive storage and reach the correct gate without manual
test-side category rewriting, with an explicit migration/compatibility rule.

### AUD-011: Preserve Null Incident Association at Intake

- [ ] AUD-011 (P1) Stop creating an implicit incident merely to store a signal.

**Affected:** T035, T037, T045, T063; FR-001, FR-012, FR-013; US1-AS3, US4-AS1.

**Expected versus observed / impact:** A high-confidence signal without an incident must remain unassociated.
[Authoritative ingestion:12](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12) replaces null
with `incident-default` and creates an active incident. [Community ingestion:8](../../apps/api/app/services/ingestion/community_ingestion.py#L8)
delegates to it. The [pipeline null test:89](../../tests/unit/test_monitoring_pipeline.py#L89) bypasses this route.
Once intake is connected, that invented association defeats the required no-handoff guard and corrupts history.

**Developer instructions:** Preserve `incidentId=None` through API ingestion and persistence. Separate authorized
incident declaration/association from normalization; do not auto-create a default incident. Use a real scoped
association service only when its documented criteria match. Keep accepted signals available for later association.

**Tester instructions:** Add an API-to-store-to-monitoring case using a high-confidence null-incident envelope.
Assert no incident creation and no handoff, but successful signal retention. Positive: an explicit authorized
incident remains associated. Edge: empty/unknown/closed incident policy must be explicit rather than coerced to
the default; subsequent retrospective association links the same signal ID.

**Dependencies / future validation:** AUD-001, AUD-005, AUD-019; F-INGEST/F-ASSOC with P-PY.
**Acceptance:** No ingestion path fabricates incident association, and the null-incident acceptance scenario
holds at the real API boundary as well as in the helper test.

### AUD-012: Generate and Validate One Summary Per Signal

- [ ] AUD-012 (P1) Reuse the exact audited summary in the handoff.

**Affected:** T029, T034, T035, T038, T039; FR-002, FR-003, FR-020, FR-026, FR-028; US3-AS3, US6-AS4.

**Expected versus observed / impact:** [process_signal:395](../../apps/agents/monitoring/pipeline.py#L395)
discards `_summarise`'s return; [builder:111](../../apps/agents/monitoring/agent.py#L111) invokes summarization
again for the handoff. With a model, the audit can describe one output and downstream receive another.
The pipeline's [content-safety dependency:62](../../apps/agents/monitoring/pipeline.py#L62) is never used by the
agent it constructs, so injecting stricter validation into the pipeline has no effect.

**Developer instructions:** Pass a typed validated summary/result from stage 5 into stage 6. Use one shared
configured validator and preserve its safety metadata; do not re-prompt inside a low-level event builder.
Keep a clearly documented compatibility adapter for existing builder callers without reopening AUD-002.

**Tester instructions:** Strengthen [summary tests:164](../../tests/unit/test_monitoring_pipeline.py#L164) using an
LLM with different successive outputs and a strict injected validator. Assert exactly one summary request,
byte-equivalent audited/downstream summary, one validation of the final text, and correct fallback reuse.
Edge: interleaved signals must preserve their own metadata and must not share mutable summaries.

**Dependencies / future validation:** AUD-002, AUD-007, AUD-018; F-PIPELINE/F-SAFETY with P-PY.
**Acceptance:** One authoritative summary exists per processing attempt, its validation configuration is honored,
and audit/handoff content cannot diverge through a second generation.

### AUD-013: Bound End-to-End LLM and Processing Latency

- [ ] AUD-013 (P1) Make time budgets enforceable without blocking other signals or probes.

**Affected:** T023, T034, T035, T036, T043, T068; FR-006, FR-007, FR-023, FR-025; NFR-001;
SC-001, SC-005, SC-007; CHK003, CHK013, CHK019, CHK030, CHK037, CHK051, CHK068.

**Expected versus observed / impact:** Evaluation has a wait timeout at
[agent.py:150](../../apps/agents/monitoring/agent.py#L150), but the underlying synchronous call can continue.
[Summary:70](../../apps/agents/monitoring/agent.py#L70) runs synchronously on the processing loop, twice for
eligible signals. [LLMClient:144](../../apps/agents/common/llm_client.py#L144) defaults to 30 seconds; the
[Foundry client:397](../../apps/agents/common/foundry_chat_client.py#L397) accepts `timeout_s` but does not pass
it to `client.complete`. Source does not enforce the contract's 500 ms summary/5 s total budget.

**Developer instructions:** Own the agent/client boundary and shared transport timeout. Use cancellable async I/O
or bounded off-loop work with a real SDK timeout and concurrency budget. Propagate remaining deadlines through
classification, summary, safety, audit, and handoff creation; define delivery retries separately. On deadline,
produce the appropriate hold/fallback and preserve durable processing state. Prevent abandoned threads from
exhausting capacity or delaying unrelated source processing.

**Tester instructions:** Use controlled slow/failing transports rather than live calls for deterministic tests.
Assert prompt deadline propagation, classification timeout/hold, summary fallback, one generation, and an
independent heartbeat/health request progressing during slow I/O. Edge: repeated timeouts, rate limits, cancellation,
and simultaneous sources. Measure the full connected path separately under F-LOAD, not a mocked microbenchmark.

**Dependencies / future validation:** AUD-012, AUD-016, AUD-020, AUD-031; F-PIPELINE/F-LOAD with P-PY/P-PERF.
**Acceptance:** Deterministic tests prove nonblocking bounded decisions; recorded representative measurements
establish the applicable 5-second, 10-second, and 1-second criteria.

### AUD-014: Annotate and Reduce Confidence on LLM Fallback

- [ ] AUD-014 (P1) Expose loss of LLM enrichment in rule-based decisions.

**Affected:** T034, T035, T038; FR-017, FR-023, FR-024; US5; CHK017.

**Expected versus observed / impact:** [summarize_signal:53](../../apps/agents/monitoring/agent.py#L53) returns
the same base fields when the LLM is absent/fails, with no reduced-confidence annotation. The
[handoff confidence:100](../../apps/agents/monitoring/agent.py#L100) remains raw confidence times freshness
minus suspicious penalty. [Fallback tests:191](../../tests/unit/test_monitoring_pipeline.py#L191) check only
`signal_count`; operators/downstream agents cannot distinguish missing enrichment from full capability.

**Developer instructions:** Define the fallback annotation and approved confidence adjustment using the existing
configuration where appropriate. Preserve raw, freshness-adjusted, suspicious-adjusted, and final confidence
without double penalties. Mark fallback reason/generation method in audit and downstream structured metadata.
Resolve FR-024's threshold-only wording against FR-009's effective-confidence rule explicitly.

**Tester instructions:** Assert both annotation and numeric decision confidence for absent client, transport failure,
timeout, and empty model response; compare with a successful enrichment control. Edge: threshold equality after
the adjustment, zero confidence, simultaneous freshness and suspicious penalties, and recovery on a later signal.
No escalated signal may use fallback to bypass its required human-review hold.

**Dependencies / future validation:** AUD-008, AUD-012, AUD-026, AUD-033; F-PIPELINE with P-PY.
**Acceptance:** Every non-escalated fallback is distinguishable and conservative according to an approved formula;
the audit and handoff carry the same final confidence and reason.

### AUD-015: Detect Silent Sources and Recover Correctly

- [ ] AUD-015 (P1) Connect scheduled freshness assessment and missing-source confidence effects.

**Affected:** T010, T012, T032, T041, T043, T051, T052; FR-017, FR-018, FR-023; US5-AS1 through US5-AS3; SC-005.

**Expected versus observed / impact:** [check_staleness:104](../../apps/agents/monitoring/freshness.py#L104)
has no production caller in the inspected paths. [First update:58](../../apps/agents/monitoring/freshness.py#L58)
always starts healthy even for low freshness; no expected-source registry detects sources that never send.
Time-based changes are not audited, and triage only multiplies the current signal's freshness, not missing-source
coverage. [Offline recovery test:41](../../tests/unit/test_monitoring_freshness.py#L41) manually sets offline status.

**Developer instructions:** Schedule scoped freshness checks independently of arrivals, seed expected sources,
and emit every degradation/recovery transition with downtime and confidence impact. Handle first-low signals,
source-kind aliases, exact threshold boundaries, long gaps, and recovery. Define the approved missing-source
weighting and combine it with signal freshness without treating a fresh remaining source as complete evidence.

**Tester instructions:** Replace manual state mutation with a controlled clock and scheduler-driven tests in
[freshness tests:6](../../tests/unit/test_monitoring_freshness.py#L6) and
[pipeline freshness tests:231](../../tests/unit/test_monitoring_pipeline.py#L231). Positive: timely signals stay
healthy; negative: silence reaches degraded/offline at each source-type threshold; edge: first-low, never-seen,
long gap, recovery at 0.5, tenant isolation, and uninterrupted processing of another source. Assert events/audits.

**Dependencies / future validation:** AUD-001, AUD-003, AUD-014, AUD-021; F-FRESH/F-PIPELINE/F-LOAD with P-PY/P-PERF.
**Acceptance:** Source loss and recovery are observable without another arrival, confidence reflects missing
coverage, and remaining sources meet the documented continuation target.

### AUD-016: Prevent Audit Loss Across Outages and Restart

- [ ] AUD-016 (P1) Make audit buffering durable and recovery automatic.

**Affected:** T013, T014, T015, T016, T018, T019, T036; FR-020, FR-021, FR-022, FR-023; SC-006; CHK040.

**Expected versus observed / impact:** [AuditWriter:29](../../apps/agents/monitoring/audit.py#L29) receives no
default Cosmos container, keeps its secondary tier in memory, and
[spill failure:101](../../apps/agents/monitoring/audit.py#L101) only logs before returning. No startup/shutdown/
scheduled flush is connected in monitoring. [Dockerfile:44](../../apps/agents/Dockerfile#L44) runs a non-root user;
the default spill path has no provisioned writable persistent mount. A restart or disk failure can lose decisions.

**Developer instructions:** Wire a managed-identity container client explicitly and make durability status part of
processing settlement. Provide a bounded persistent journal/outbox or equivalent approved durable fallback,
provision its writable storage, and recover it at startup. Add retry/backoff flush scheduling and safe shutdown;
do not silently accept a record when all tiers fail. Preserve life-safety degradation without pretending an
unwritten audit succeeded. Document capacity in decisions, not signals, since one signal emits several records.

**Tester instructions:** Extend [audit spill tests:94](../../tests/unit/test_monitoring_audit.py#L94) with real file
failure and restart cases. Assert survival after Cosmos outage, capacity exhaustion, process reconstruction,
read-only/full disk, and recovery; compare accepted decision IDs with persisted/journaled IDs. Verify settlement
is not acknowledged on total audit durability failure and unrelated source handling follows the approved policy.

**Dependencies / future validation:** AUD-001, AUD-017, AUD-024, AUD-028; F-AUDIT/F-COSMOS with P-PY/P-COSMOS.
**Acceptance:** No accepted decision disappears across tested outages/restarts, and recovery runs automatically
without a manual call to an otherwise unused helper.

### AUD-017: Make Audit Replay Ordered and Idempotent

- [ ] AUD-017 (P1) Repair flush ordering, metadata, conflict handling, and backlog status.

**Affected:** T013, T016, T017, T018, T019; FR-021, FR-022; SC-006; data-model flush contract.

**Expected versus observed / impact:** [write:42](../../apps/agents/monitoring/audit.py#L42) can persist newer
records before backlog and sets `flush_source="direct"` after serialization. [flush:109](../../apps/agents/monitoring/audit.py#L109)
continues to file records after memory failure and past failed file lines. Duplicate-create conflicts can block
memory replay indefinitely; file rewrite is not atomic. [status:167](../../apps/agents/monitoring/audit.py#L167)
uses historical spill counters and does not inspect retained files. Current tests assert counts, not replay order.

**Developer instructions:** Define monotonic replay ordering across all tiers and serialize annotations before
writes. Treat a confirmed same-ID/same-content existing record as an idempotent acknowledgment without updating
it; surface same-ID/different-content conflicts. Stop/retain the remaining ordered backlog on failure, use atomic
journal compaction, and compute health from actual outstanding state. Preserve append-only destination semantics.

**Tester instructions:** Expand [flush tests:131](../../tests/unit/test_monitoring_audit.py#L131) using captured
serialized documents and predetermined timestamps. Assert exact order and metadata for memory+file+new writes,
midstream failure, partial flush, duplicate acknowledgment, conflicting duplicate, malformed line, restart during
compaction, and complete recovery. Healthy status must require an empty durable backlog and working storage.

**Dependencies / future validation:** AUD-016, AUD-028; F-AUDIT/F-COSMOS with P-PY/P-COSMOS.
**Acceptance:** Replay never loses/reorders acknowledged decisions or mutates existing destination records;
metadata and health match persisted/backlog reality after every tested branch.

### AUD-018: Complete the Decision and Provenance Chain

- [ ] AUD-018 (P1) Record all decisions, exact inputs/outputs, and origin linkage.

**Affected:** T004, T026, T030, T031, T033, T034, T035, T036, T039, T067;
FR-008, FR-010, FR-019, FR-020, FR-021; US6-AS1, US6-AS2, US6-AS4; SC-006.

**Expected versus observed / impact:** [process_signal:366](../../apps/agents/monitoring/pipeline.py#L366)
records no receipt and always returns `None`; [triage:306](../../apps/agents/monitoring/pipeline.py#L306) returns
without a negative decision reason. Credible/suspicious/held records omit the evaluated content/reference, and
handoff audit outputs omit the full payload. [Builder:111](../../apps/agents/monitoring/agent.py#L111) omits
signal IDs/provenance; [risk retrieval:174](../../apps/agents/risk_assessment/pipeline.py#L174) then fabricates
synthetic input when IDs are missing. [T067 test:293](../../tests/unit/test_monitoring_pipeline.py#L293) only
checks category/sourceKind, not the supplied provenance.

**Developer instructions:** Define receipt, terminal negative/hold/failure, and successful decision records with
actual signal ID, tenant/incident scope, raw and adjusted confidence, immutable evaluated-input reference,
reason, and exact output. Add origin signal IDs and approved provenance fields/references to the downstream
contract; retrieve real evidence at risk assessment. Return a typed terminal outcome usable by settlement.
Reconcile receipt/negative types with the documented nine-value enum rather than overloading `discarded`.

**Tester instructions:** Replace buffer-depth-only [audit assertions:203](../../tests/unit/test_monitoring_pipeline.py#L203)
with exact ordered decision sets and content assertions for every stage exit. Include all classification outcomes,
all negative gates, malformed/duplicate inputs, delivery failure, provenance/location/time retention, and handoff-ID
to source-ID lookup. Compare real downstream retrieval with the original signal, not a synthetic substitute.

**Dependencies / future validation:** AUD-003, AUD-006, AUD-009, AUD-012, AUD-016, AUD-026, AUD-033;
F-PIPELINE/F-COSMOS with P-PY/P-COSMOS.
**Acceptance:** Independent ingress IDs reconcile to all required persisted decisions and real source evidence;
audit/handoff output and terminal processing result agree for every branch.

### AUD-019: Connect Incident Triggers and Per-Signal Association Audits

- [ ] AUD-019 (P1) Record each real association and establish its authorized trigger.

**Affected:** T045, T047, T049; FR-013, FR-016, FR-020, FR-021; US4-AS1, US6-AS3; CHK011.

**Expected versus observed / impact:** [Declaration route:20](../../apps/api/app/api/routes/incidents.py#L20)
only invokes resource governance; no monitoring association trigger appears in the searched callers.
[associate route:360](../../apps/agents/monitoring/agent.py#L360) writes one record with
`signal_id="association-<incident>"`, not one per updated signal. Direct association writes only logs.
The incident timeline cannot reconstruct which early signals were linked or why.

**Developer instructions:** Define the authoritative declaration event/API integration with incident ID, trusted
tenant, jurisdiction, geometry, and idempotency token. Trigger association after authorized declaration without
coupling it to an unrelated simulation-throttling shortcut. Persist an `associated` audit per successful update
with real signal ID, incident ID, cutoff/lookback, scope, and matching rationale; emit a separate batch summary
only as supplemental telemetry. Preserve partial-success facts on retries/errors.

**Tester instructions:** Extend [association contracts:48](../../tests/contract/test_incident_association.py#L48)
and proposed broker/API integration. Assert one trigger per declaration, five unique association audits for five
updates, none for skipped/pre-associated/foreign-scope records, and no duplicate audit/update after retry.
Edge: failed third update must not erase the first two successful associations from reported evidence.

**Dependencies / future validation:** AUD-003, AUD-004, AUD-005, AUD-018; F-ASSOC/F-SB with P-PY/P-BROKER.
**Acceptance:** Declaration-to-association is connected and every counted change is reconstructible from a
real-signal audit entry, including partial and repeated runs.

### AUD-020: Report Real Readiness and Probe Failure

- [ ] AUD-020 (P1) Replace health placeholders with bounded operational observations.

**Affected:** T042, T043, T044; FR-024, FR-025; SC-007; EC-06; health response/status contract.

**Expected versus observed / impact:** [Health:274](../../apps/agents/monitoring/agent.py#L274) uses
`configured` outside the contract enum, reports queue depth 0, invents a current check time/zero latency, and
returns HTTP 200 even for unhealthy. Missing writer/tracker defaults healthy. The deployed
[dispatcher health:200](../../apps/agents/dispatcher/agent.py#L200) has a different three-field schema.
[Tests:163](../../tests/contract/test_monitoring_escalation.py#L163) assert keys, not observations or status logic.

**Developer instructions:** Share readiness state with the actual worker. Collect bounded/cached LLM reachability,
freshness, broker queue depth, and audit durability checks with truthful timestamps and stale-check handling.
Implement <1000/1000-5000/>5000 queue states. Separate liveness from readiness and reconcile LLM-only outage
with FR-024's permitted rule-based processing. Wire Container Apps probes to meaningful failure status codes.

**Tester instructions:** Exercise the deployed app factory with controlled dependency adapters. Assert each enum,
type, timestamp age, queue boundary (999, 1000, 5000, 5001), audit tier, LLM failure/slow/recovery, missing
configuration, and mixed conditions. Assert probe status codes and <=1 second response while checks are slow.
The existing [benchmark client:28](../../tests/benchmark/conftest.py#L28) creates an unconfigured legacy app,
so it cannot establish deployed readiness.

**Dependencies / future validation:** AUD-001, AUD-013, AUD-015, AUD-017, AUD-023, AUD-033; F-HEALTH/F-LOAD with P-PY/P-PERF.
**Acceptance:** Health accurately represents the running pipeline and failure affects readiness as documented;
dependency latency cannot block the probe beyond its budget.

### AUD-021: Implement the Monitoring Telemetry Contract

- [ ] AUD-021 (P1) Emit all required metrics, traces, correlations, and custom events.

**Affected:** T030, T031, T032, T050, T051, T052, T054, T055; FR-020; NFR-003; telemetry contract.

**Expected versus observed / impact:** [Pipeline:17](../../apps/agents/monitoring/pipeline.py#L17) imports no
OTel instrumentation and [accessors:426](../../apps/agents/monitoring/pipeline.py#L426) expose only in-process
counters. No root/stage spans, broker-parent input, named events, or metric dimension assertions exist.
Conditional [Azure Monitor setup:15](../../apps/agents/monitoring/agent.py#L15) and shared Foundry spans do not
implement monitoring's end-to-end contract. Operators cannot measure loss, latency, or degradation reliably.

**Developer instructions:** Add a monitoring telemetry surface following neighboring agent conventions, then
instrument every outcome and failure/finally path. Implement the 13 instruments and eight events listed in the
contract assessment below, including audit/health metrics outside `pipeline.py`. Propagate incoming trace context
and correlation IDs into LLM, audit, handoff/retries; attach signal, tenant, category, source type, and decision.
Define bounded cardinality and privacy-safe diagnostic fields.

**Tester instructions:** Use an in-memory OTel reader/exporter and captured event sink in
[pipeline tests:203](../../tests/unit/test_monitoring_pipeline.py#L203) and audit/health tests. Assert names,
types, units, values, dimensions, parent-child relationships, and all eight event payloads. Positive: complete
trace for success. Negative/edge: validation, duplicate, timeout, spill, partial flush, recovery, and DLQ still emit
correct metrics without sensitive raw payloads or cross-tenant dimensions.

**Dependencies / future validation:** AUD-006, AUD-015 through AUD-020; F-TELEMETRY with P-PY, then P-OBS.
**Acceptance:** Contract-complete captured telemetry matches real decision counts and can be correlated from
broker receipt to terminal outcome; a checked task or logger message is not sufficient.

### AUD-022: Configure Actionable Monitoring Alerts

- [ ] AUD-022 (P1) Wire all seven contract alert conditions to approved operations channels.

**Affected:** T053, T060; FR-011, FR-023; NFR-003; CHK004, CHK010; telemetry alert table.

**Expected versus observed / impact:** [Config:15](../../apps/agents/monitoring/config.py#L15) has no alert
threshold configuration. [Generic observability:76](../../infra/modules/monitoring.bicep#L76) alerts on HTTP
errors/duration and simulation errors, not monitoring classifications, queue depth, backlog, or dead letters.
The renamed generic module does not satisfy the seven requested alerts.

**Developer instructions:** Define thresholds/windows in one owned configuration and deploy matching metric/log
alerts with correct instrument names/units. Cover misinformation >10/min for 5 minutes, >5 LLM timeouts/min,
audit backlog >0 and >8000, any dead letter, p95 latency >4000 ms, and queue depth >5000. Connect real,
approved action-group destinations, deduplication/recovery behavior, tenant context, and ownership runbooks.
Follow policy/AVM procedures in a later authorized infrastructure change; do not use placeholder destinations.

**Tester instructions:** Add focused infrastructure/telemetry contract assertions and later controlled alert
exercises. Positive: each condition triggers its expected severity and channel. Negative: below threshold and
non-monitoring traffic do not trigger. Edge: equality, full rolling window, recovery, repeated events, and different
tenants. Assert a dead letter reaches a commander-visible destination, not merely an event sink.

**Dependencies / future validation:** AUD-006, AUD-021, AUD-023; F-IAC with P-IAC, then P-OBS/P-IDENTITY.
**Acceptance:** Seven deployed definitions match instrument semantics and approved notification evidence exists;
deployment and notification results remain UNVERIFIED until that later exercise.

### AUD-023: Compose Monitoring Infrastructure and Queue Scaling

- [ ] AUD-023 (P1) Wire the renamed agent module into the real deployment topology.

**Affected:** T056, T057, T058, T059, T060; FR-001, FR-021, FR-022; NFR-002.

**Expected versus observed / impact:** [monitoring-agent.bicep:43](../../infra/bicep/monitoring-agent.bicep#L43)
defines the right audit key and session queue, but neither root references it. The actual
[agents scale block:1180](../../infra/main.bicep#L1180) only sets min/max replicas, despite a comment claiming
per-agent queue scaling. The agent module defines no Container App. Serverless is only a comment on a child
container referencing an account not configured as serverless by the roots. Conditional role declarations do not
prove the running worker has broker access.

**Developer instructions:** Own both the actual root selected by `azure.yaml` and any supported alternate root.
Wire the renamed module, signal publisher/receiver identities, configured queue name, audit client settings,
probe definitions, persistent audit storage, and queue-depth scaling. Resolve 100-message task threshold versus
the later root comment's 50 and select an explicit maximum. Choose account throughput mode coherently;
do not infer it from omitted container options. Apply discovered policy/AVM rules under separate authorization.

**Tester instructions:** Add parsed-template assertions for root reachability, queue sessions, threshold, min/max,
scaler identity, environment names, no-TTL container/key, and role scopes. Negative: missing names/identities
must not silently deploy an apparently operational worker. Edge: each supported environment and scaled-out
instance must resolve the same intended tenant-safe transport resources.

**Dependencies / future validation:** AUD-001, AUD-020, AUD-024, AUD-025, AUD-034; F-IAC with P-IAC; live checks later.
**Acceptance:** The actual deployment graph contains and configures the monitoring resources and scale rule;
comments, orphan modules, or provisioned unrelated Service Bus topics do not count.

### AUD-024: Enforce Audit Retention and Append-Only Access

- [ ] AUD-024 (P1) Align durable audit permissions with the no-update/no-delete requirement.

**Affected:** T013, T019, T056, T059; FR-021, FR-022; CHK007, CHK008, CHK040.

**Expected versus observed / impact:** [Writer:65](../../apps/agents/monitoring/audit.py#L65) correctly uses
`create_item`, and [container:43](../../infra/bicep/monitoring-agent.bicep#L43) omits TTL. However,
[agent role:94](../../infra/bicep/monitoring-agent.bicep#L94) and
[root role:904](../../infra/main.bicep#L904) grant account-wide Data Contributor. Those declarations are not an
append-only enforcement boundary; no live retention/permission proof was inspected.

**Developer instructions:** Define the approved writer/reader/administrative trust boundary and minimum data
actions needed for create/read-metadata without update/delete, scoped to the audit container where supported.
Document any platform limitation and explicit compensating immutable control rather than claiming Cosmos is
automatically WORM. Verify no TTL override and preserve incident-scoped retrieval with pagination. Coordinate
retention/cost policy without silently adding expiry to this specification's infinite-retention audit.

**Tester instructions:** Extend proposed Cosmos integration and IaC checks: create/read succeeds, mutation/deletion
by the agent identity is denied or blocked by the approved enforceable boundary, duplicate create cannot replace
content, partition-scoped reads do not cross tenants, and metadata shows no expiry. Include recovery writes and
large incident query pagination. Use a disposable account/container and never attempt these checks on real audit data.

**Dependencies / future validation:** AUD-016, AUD-017, AUD-023, AUD-028; F-COSMOS/F-IAC with P-COSMOS/P-IAC/P-IDENTITY.
**Acceptance:** Append-only behavior is enforced and evidenced at its stated trust boundary, not merely by the
currently called method; deployed retention remains separately evidenced.

### AUD-025: Resolve and Prove Regional Independence

- [ ] AUD-025 (P1) Define a consistent AU primary/DR and model-hosting policy.

**Affected:** T056 through T060; NFR-004; FR-015, FR-023, FR-024; CHK048, CHK054, CHK055, CHK060; SCP-026.

**Expected versus observed / impact:** Spec-010 requires independent regional processing, while the plan's
resource table proposes Cosmos replication. [Actual root:78](../../infra/main.bicep#L78) permits only Australia
East for primary location and supplies no complete monitoring DR stack. Model
[SKU defaults:72](../../infra/modules/azure-openai.bicep#L72) allow GlobalStandard; an AU account location alone
does not establish AU-only inference. [Gateway:362](../../apps/agents/common/foundry_chat_client.py#L362)
bypasses minimization for an unset region. The constitutional hosting carve-out is conditional, not a waiver
of signal/audit/telemetry residency or spec-010 independence.

**Developer instructions:** Resolve whether spec-010 requires strict per-region data isolation or governed failover
replication; record an authorized amendment before altering that promise. Define independent stores, queues,
cache scopes, identities, and region-bound LLM behavior or conservative DR fallback. Validate regional/model
configuration explicitly, including unknown regions and applicable named carve-out approval. Do not broaden
the constitutional exception through default model selection.

**Tester instructions:** Add two-region configuration/partition contract tests with identical signal IDs and
incidents. Assert region A cannot read/affect B, unknown region fails safely, non-AU model transit follows approved
minimization, and DR with no LLM holds escalated signals while preserving annotated rule-based processing.
Later measure failover under approved RPO/RTO criteria; source templates are not deployment evidence.

**Dependencies / future validation:** AUD-003, AUD-014, AUD-023, AUD-027, AUD-033; F-IAC with P-IAC; P-REGION later.
**Acceptance:** One approved policy resolves the contradictions, and paired deployment/isolation/fallback evidence
demonstrates it without unapproved data movement.

### AUD-026: Enforce Configuration and Decision-Model Invariants

- [ ] AUD-026 (P1) Validate the original twelve settings and durable decision shape.

**Affected:** T001, T004, T005, T006, T008, T009, T025, T066; FR-007, FR-009, FR-013, FR-018, FR-021, FR-029; CHK025, CHK044, CHK073.

**Expected versus observed / impact:** All twelve settings are read, but
[post-init:88](../../apps/agents/monitoring/config.py#L88) validates only later LLM options, not core thresholds,
windows/capacity, or reasoning length. [Decision model:59](../../apps/agents/monitoring/models.py#L59) allows
empty scope/reason, arbitrary confidence/classification strings, mutable records, and unbounded reasoning.
[Scope key:35](../../apps/agents/monitoring/pipeline.py#L35) uses an eight-hex-digit suffix rather than the
research's hash modulo 16. Config tests override only three variables.

**Developer instructions:** Define finite/range/positive-duration validation and startup failure behavior for all
original settings. Enforce required audit scope/identity/reason, bounded confidence and reasoning, and allowed
classification/safety/flush values. Preserve compatibility through explicit versioning, not silent coercion.
Apply the configured summary limit; resolve and implement the documented unassociated partition bucket count.
Correct import-time/frozen-config prose to match construction-time environment reads.

**Tester instructions:** Extend [models/config tests:50](../../tests/unit/test_monitoring_models.py#L50) with every
setting override, absent/default values, NaN/infinity, negative/zero windows/capacity, invalid enum/blank identity,
reasoning boundary and serialization round-trip. Assert deterministic scoped bucket mapping and exactly the
approved bucket range. Edge: fallback plus suspicious penalties cannot create negative stored confidence.

**Dependencies / future validation:** AUD-018, AUD-033; F-MODELS/F-AUDIT with P-PY.
**Acceptance:** Invalid operational configuration is rejected predictably at startup, and accepted audit records
meet the documented schema and partition contract without relying on caller discipline.

### AUD-027: Verify Credibility Prompt Isolation at the Real Client Boundary

- [ ] AUD-027 (P1) Separate trusted instructions from untrusted signal content and test resistance.

**Affected:** T020, T023, T034, T069; FR-027, FR-028; CHK012, CHK050, CHK067.

**Expected versus observed / impact:** [Agent evaluation:140](../../apps/agents/monitoring/agent.py#L140)
concatenates role instructions and raw payload into one prompt. The actual
[client:180](../../apps/agents/common/llm_client.py#L180) adds a generic emergency-response system message,
including an anti-injection instruction, but not the precise credibility-classifier contract.
[Security test:208](../../tests/contract/test_monitoring_escalation.py#L208) uses a constant mock response and
asserts a substring in the user prompt; it never inspects the real system/user message separation or resistance.
No successful injection is claimed by this static audit; the protection claim is unverified.

**Developer instructions:** Own a versioned credibility system instruction, constrained output schema, and
explicit untrusted-data serialization at the shared client boundary. Minimize payload sent to inference and
preserve gateway/filter-denial outcomes. Apply equivalent boundaries to summary and MAF paths; do not use
the existence of a general system prompt as a security guarantee. Retain prompt version/hash for replay.

**Tester instructions:** Test the actual `LLMClient` with an injected transport that captures messages: assert
trusted classification instructions are system-scoped and adversarial content stays data. Cover instructions
inside nested payloads, role delimiters, encoded/long text, prompt-filter refusal, and malformed completion.
Then run a separately approved adversarial model evaluation; mock returns cannot prove model behavior.

**Dependencies / future validation:** AUD-002, AUD-007, AUD-008, AUD-025, AUD-032; F-SAFETY with P-PY; P-MODEL later.
**Acceptance:** Deterministic tests prove boundary enforcement, and a versioned adversarial evaluation documents
residual risk without equating a mock assertion to injection prevention.

### AUD-028: Add the Missing Cosmos Audit Integration Harness

- [ ] AUD-028 (P1) Verify actual monitoring audit serialization, partitioning, and recovery.

**Affected:** T019; T013 through T018, T056, T059; FR-021, FR-022; SC-006.

**Expected versus observed / impact:** T019 names an emulator integration test, but no equivalent monitoring
Cosmos test was found after filename/import/assertion searches. [Audit tests:24](../../tests/unit/test_monitoring_audit.py#L24)
use `MagicMock.create_item`; [storage tests:27](../../tests/contract/test_signal_storage.py#L27) use an in-memory
signal repository, not the monitoring decision container. Those cannot catch SDK, partition, permissions,
duplicate-create, or replay incompatibilities.

**Developer instructions:** Create the **proposed** `tests/integration/test_monitoring_cosmos_audit.py`, using
the existing [_make_record helper pattern](../../tests/unit/test_monitoring_audit.py#L8), an explicitly selected
emulator/disposable container, and the actual `AuditWriter`. Add opt-in setup/cleanup and clear skip reasons;
do not replace the write/read-back path with a mocked container. Keep identity enforcement checks separable
from emulator capabilities and prevent accidental production execution.

**Tester instructions:** Assert serialized fields/enum/time values, direct annotations, incident and unassociated
partition routing, tenant isolation, no TTL, memory/file recovery, chronological order, idempotent replay, and
corrupt/partial failure behavior. Positive create/read-back must compare full records; negative permission/partition
and conflict cases must fail as intended. Record environment, SDK version, source revision, and test output later.

**Dependencies / future validation:** AUD-016, AUD-017, AUD-018, AUD-024, AUD-026; F-COSMOS with P-PY/P-COSMOS.
**Acceptance:** A runnable non-mock integration harness covers all T019 obligations and later execution evidence
is attached; this audit leaves that execution UNVERIFIED.

### AUD-029: Add Broker and Association Integration Assertions

- [ ] AUD-029 (P1) Verify transport-driven intake and HTTP association against real owning code.

**Affected:** T049, T063; FR-001, FR-010, FR-011, FR-013 through FR-016; SC-001, SC-004.

**Expected versus observed / impact:** The named monitoring Service Bus test is absent. The
[handoff-chain test:5](../../tests/integration/test_handoff_chain.py#L5) subscribes a local no-op function;
[synthetic integration:74](../../tests/integration/test_signal_pipeline_e2e_036.py#L74) exercises a different
simulation publisher, and [risk fan-out:34](../../tests/integration/test_risk_assessment_auto_fanout.py#L34)
injects its runner. None consumes spec-010's session queue or asserts `/associate` updates.

**Developer instructions:** Create the **proposed** `tests/integration/test_monitoring_service_bus.py` with
separate broker and HTTP association groups. Reuse the real worker composition, repository, and health app;
mock only explicitly external inference when isolating transport. Provision session-capable disposable messaging
and test stores through approved test setup, with production-protection guards and observable cleanup.

**Tester instructions:** Publish a real envelope with session ID, tenant, stable signal ID, and trace context;
assert receipt, processing, durable decision, handoff, and settlement. Negative: invalid/foreign-scope/held inputs
must not deliver. Edge: lock loss, repeat after restart, DLQ failure and recovery. For HTTP, seed five eligible
records, invoke authorized association, and compare response counts with actual persisted updates and audits.

**Dependencies / future validation:** AUD-001 through AUD-006, AUD-019, AUD-023, AUD-028, AUD-034;
F-SB with P-PY/P-BROKER/P-COSMOS/P-IDENTITY.
**Acceptance:** Both T049 and T063 have assertion-complete integration paths that cannot pass through a local
no-op subscriber or an in-memory count alone.

### AUD-030: Exercise Monitoring in the Bushfire Scenario

- [ ] AUD-030 (P1) Extend the existing scenario to verify the full decision chain.

**Affected:** T062; T027, T039, T041, T067; FR-004, FR-009, FR-015, FR-019, FR-020; US1, US2, US3, US5, US6.

**Expected versus observed / impact:** [Bushfire tests:17](../../tests/simulation/test_bushfire_scenario.py#L17)
test FFDI generation and schema keys only. No monitoring pipeline, misinformation classification, handoff,
audit reconciliation, or tenant boundary is exercised. The phase-9 completion claim has no equivalent scenario
assertion body at this revision.

**Developer instructions:** Extend the existing scenario file rather than replacing the generator tests. Feed
generator output through real normalization/storage/monitoring and a controlled risk consumer, using deterministic
time and scoped fixtures. Keep external LLM/broker details isolated where appropriate, but do not mock away
the monitoring stage decisions. Include realistic degraded and misinformation cases alongside the happy path.

**Tester instructions:** Assert the complete sequence: first receipt, duplicate discard, freshness update,
classification before escalation, one safe summary, correct effective confidence/handoff, and exact audit chain.
Negative: misinformation and LLM outage hold/block without risk work. Edge: low freshness, two tenants with
same IDs, recovery, no incident followed by association, and original provenance preserved.

**Dependencies / future validation:** AUD-002, AUD-003, AUD-009, AUD-010 through AUD-019; F-SCENARIO with P-PY.
**Acceptance:** The existing bushfire scenario now invokes monitoring and its assertions fail when any required
pipeline stage is bypassed, not merely when a generated dictionary lacks a key.

### AUD-031: Build Representative Load and Timing Evidence

- [ ] AUD-031 (P1) Measure sustained monitoring throughput and all timing criteria honestly.

**Affected:** T023, T043, T064, T068; NFR-001; SC-001, SC-004, SC-005, SC-007; CHK033 through CHK037, CHK039, CHK052, CHK056.

**Expected versus observed / impact:** No five-minute/1,000-signals-per-minute monitoring load test was found.
[Benchmark:189](../../tests/benchmark/test_pipeline_performance.py#L189) repeatedly uses `bench-001` with a
session-scoped deduplicator, no LLM, memory audit, and a no-op delivery function. After its first iteration it can
measure dedup instead of the full path. No inspected artifact establishes the four timing outcomes or throughput.

**Developer instructions:** Create the **proposed** `tests/simulation/test_monitoring_load.py` and repair benchmark
input lifecycle. Use unique IDs and a representative category/source/escalation mix, sustained arrivals of at least
1,000/minute for five minutes, and separately reported full-path versus duplicate/fallback latencies. Add measured
association scale, outage continuation, and health probes under concurrent work. Define hardware, services,
queue boundaries, warmup, percentiles versus per-signal SLA, and loss reconciliation before running.

**Tester instructions:** Assert all 5,000+ inputs have terminal outcomes, eligible handoff creation meets the
approved 5-second criterion, >=90% eligible association within 30 seconds, unaffected processing within 10 seconds
of detected outage, and health <=1 second. Include slow model/audit, peak bursts, multi-instance/restart, and DR
fallback. Record source revision, workload, counts, latency distributions, failures, and resource usage.

**Dependencies / future validation:** AUD-001, AUD-005, AUD-013, AUD-015, AUD-018, AUD-020, AUD-023, AUD-029;
F-LOAD with P-PY/P-PERF, then approved staging resources.
**Acceptance:** Reproducible measurements, not a fixture benchmark or source-existence claim, establish each
target; failures remain explicit and are not hidden by duplicate work or skipped tests.

### AUD-032: Establish Labeled Credibility Evaluation

- [ ] AUD-032 (P1) Measure misinformation accuracy and false positives on representative data.

**Affected:** T027, T028, T069; FR-004 through FR-008, FR-027; SC-008; CHK033.

**Expected versus observed / impact:** [Contract tests:40](../../tests/contract/test_monitoring_escalation.py#L40)
program the answer into a mock. The [Foundry fixture:1](../../apps/eval-runner/fixtures/spec036/monitoring.jsonl#L1)
contains five doctrine/retrieval questions, not labeled social-post truth. The
[equivalence fixture:1](../../tests/equivalence/fixtures/monitoring/smoke-fire-escalate.json#L1) stores matching
outputs and is not a model invocation. None demonstrates SC-008's <5% false-positive rate.

**Developer instructions:** Define a versioned, licensed, privacy-reviewed disaster-social dataset with ground-truth
labels, sampling composition, adjudication method, and held/suspicious treatment. Add an evaluation harness
that calls the actual classifier and records model/prompt/filter/config versions. Proposed dataset:
`tests/fixtures/monitoring-credibility.jsonl`; proposed harness: `tests/contract/test_monitoring_credibility_evaluation.py`.
Keep deterministic parser tests separate from stochastic accuracy/security evaluation.

**Tester instructions:** Include credible community reports lacking official corroboration, confirmed recycled/
false reports, mixed hazards/locales, benign emergency vocabulary, and adversarial text. Report confusion matrix,
credible denominator, false-positive rate, misinformation blocking/recall, hold rate, and uncertainty with a justified
sample size. Negative: insufficient labels/empty dataset/unavailable model must not yield PASS. Edge: exact 5%
fails the strict <5% criterion; human adjudication and privacy approval must be recorded.

**Dependencies / future validation:** AUD-007, AUD-008, AUD-027; F-EVAL with P-MODEL/P-DATA/P-PY.
**Acceptance:** Reproducible labeled evaluation establishes <5% false positives without suppressing credible
community intelligence; model resistance and measured accuracy remain UNVERIFIED until execution.

### AUD-033: Reconcile Documentation and Completion Claims

- [ ] AUD-033 (P2) Correct stale instructions and obtain bounded review/measurement evidence.

**Affected:** T064, T065, T066; all FR/NFR/SC traceability; all CHK items; PER-022, PER-023, PER-024;
HYP-008, HYP-033, HYP-034, HYP-035; SCP-025, SCP-026, SCP-027.

**Expected versus observed / impact:** [Quickstart:107](quickstart.md#L107) expects 0.9 rather than 0.855 for
its configured confidence/freshness and invokes the unsafe builder for misinformation. Its cwd/test/env examples
do not match current packaging, identity auth, or dispatcher startup. [Task summary:336](tasks.md#L336) says
66, not 69. [Plan gates:37](plan.md#L37) and T064/T065 assert completion without corresponding local run/sign-off
records. HYP-008's named stub is absent; the relocated rubric snapshot is portfolio structural scoring, not a
per-spec consultation/SME validation record. Country evidence explicitly says Not tested.

**Developer instructions:** In a later authorized documentation change, reconcile the conflicts listed below,
update quickstart for current supported entry points and identity configuration, and repair task-summary and
evidence references without retroactively inventing passes. Track decisions for unspecified checklist gaps;
retain country deferrals until their preconditions clear. Separate authored design answers from completed
checks, reviewer approvals, test execution, measurements, and deployment facts.

**Tester instructions:** After product fixes, run each corrected verification in a clean declared environment and
record command, revision, timestamp, expected/actual result, and explicit skips. Independently reconcile all
69 task rows, 41 requirements, scenarios, and the 16 highlighted checklist resolutions. Verify named SME/
practitioner review provenance rather than copying a `validated` label; do not promote country hypotheses.

**Dependencies / future validation:** Relevant AUD-001 through AUD-032 and AUD-034; F-DOC/P-REVIEW, with product
commands only under their separate prerequisites. **Acceptance:** Documentation matches supported code and
each completion claim links to appropriate, revision-bound evidence or remains openly UNVERIFIED/DEFERRED.

### AUD-034: Make Deduplication Safe for Retry and Scale-Out

- [ ] AUD-034 (P1) Tie idempotency to durable processing outcomes, not only process memory.

**Affected:** T009, T011, T031, T036, T057, T063, T068; FR-029, FR-015; NFR-002; EC-04, EC-06; CHK014, CHK024, CHK046.

**Expected versus observed / impact:** [Dedup:35](../../apps/agents/monitoring/dedup.py#L35) is an in-process
check-and-mark, and [pipeline:126](../../apps/agents/monitoring/pipeline.py#L126) marks before any later audit,
classification, or delivery succeeds. A failed attempt can be discarded on retry; a restarted/second instance
has no previous state. Session affinity in [research task 8](research.md#L143) does not ensure the same process
owns a session after lock release/restart. The service supports locks/state, not permanent process affinity.

**Developer instructions:** Define scoped in-progress/terminal idempotency state and a recovery lease, using
durable state or an equivalent proven broker/outbox design. Complete the dedup record only with the terminal
durable outcome; recover abandoned attempts without double delivery. Define TTL equality and bounded eviction
semantics. Preserve fast local caching as an optimization, not the cross-instance authority, and coordinate
message/session IDs with AUD-001/AUD-003.

**Tester instructions:** Extend [dedup tests:6](../../tests/unit/test_monitoring_dedup.py#L6) using a controlled
clock, plus broker integration. Positive: one processing outcome for repeats inside the window. Negative:
different tenant/region IDs must not collide. Edge: exact expiry, eviction while pending, concurrent processes,
lock transfer, restart, and failure after mark but before audit/delivery must recover without loss or duplicate work.

**Dependencies / future validation:** AUD-001, AUD-003, AUD-006, AUD-016; F-FRESH/F-SB with P-PY/P-BROKER.
**Acceptance:** Idempotency survives retries and worker replacement, with exactly one intended durable effect
per scoped signal/window and explicit audit of duplicates.

## Requirement Coverage

All FR/NFR/SC identifiers have separate rows. Runtime, measurement, sign-off, and deployment evidence is not
inferred from source. Pure rule implementation may be IMPLEMENTED even when the larger ingress path is not;
the follow-up column identifies the integration limitation.

| ID | Status | Implementation and actual test evidence | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Validator:25](../../apps/api/app/validators/signal_envelope.py#L25) and [validation tests:225](../../tests/unit/test_monitoring_models.py#L225) exist; [dispatcher:189](../../apps/agents/dispatcher/agent.py#L189) has no signal consumer, and producer taxonomy differs. | AUD-001, AUD-003, AUD-010, AUD-029 |
| FR-002 | PARTIAL | [Summary:53](../../apps/agents/monitoring/agent.py#L53) produces required metadata; [tests:149](../../tests/unit/test_monitoring_pipeline.py#L149) mostly assert counters and the output is regenerated before handoff. | AUD-001, AUD-012 |
| FR-003 | CONFLICT | Structured-only [spec:128](spec.md#L128) versus narrative [summary:79](../../apps/agents/monitoring/agent.py#L79); [tests:178](../../tests/unit/test_monitoring_pipeline.py#L178) do not assert raw-content absence. | AUD-007, AUD-033 |
| FR-004 | PARTIAL | [Conditional pipeline gate:176](../../apps/agents/monitoring/pipeline.py#L176) exists; [MAF:25](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) bypasses it; [tests:44](../../tests/contract/test_monitoring_escalation.py#L44) call evaluation alone. | AUD-002, AUD-027 |
| FR-005 | PARTIAL | [Blocked decision:183](../../apps/agents/monitoring/pipeline.py#L183) stops the local pipeline; [Signal:28](../../packages/domain/src/domain/models/signal.py#L28) lacks flagged status; [test:62](../../tests/contract/test_monitoring_escalation.py#L62) omits no-handoff assertion. | AUD-002, AUD-009 |
| FR-006 | PARTIAL | [No-client result:136](../../apps/agents/monitoring/agent.py#L136) and [hold:240](../../apps/agents/monitoring/pipeline.py#L240) exist; [test:98](../../tests/contract/test_monitoring_escalation.py#L98) does not prove durable review. | AUD-002, AUD-009, AUD-013 |
| FR-007 | PARTIAL | [Parser:163](../../apps/agents/monitoring/agent.py#L163) uses substrings; [penalty test:116](../../tests/contract/test_monitoring_escalation.py#L116) asserts numeric gate effect, but invalid-text cases are incomplete. | AUD-008, AUD-026 |
| FR-008 | PARTIAL | [Classification records:168](../../apps/agents/monitoring/pipeline.py#L168) exist, but unexpected outcomes are mislabeled and direct evaluations are unrecorded; [tests:203](../../tests/unit/test_monitoring_pipeline.py#L203) only count buffers. | AUD-002, AUD-008, AUD-018 |
| FR-009 | PARTIAL | [Five-category effective gate:100](../../apps/agents/monitoring/agent.py#L100) and [tests:130](../../tests/contract/test_monitoring_escalation.py#L130) support the local predicate; real earthquake normalization emits geohazard and MAF advances regardless. | AUD-001, AUD-002, AUD-010, AUD-014 |
| FR-010 | PARTIAL | [Builder:111](../../apps/agents/monitoring/agent.py#L111) creates event fields; [success test:67](../../tests/unit/test_monitoring_pipeline.py#L67) checks target/incident only; tenant-qualified scope, origin linkage, and persistence are incomplete. | AUD-003, AUD-006, AUD-018 |
| FR-011 | PARTIAL | [Shared retry:124](../../apps/agents/common/handoffs.py#L124) has backoff/time cap; [tests:38](../../tests/integration/test_handoff_retry.py#L38) return a synthetic DLQ ID. No monitoring-to-notification connection. | AUD-006, AUD-022, AUD-033 |
| FR-012 | PARTIAL | [Null gate:108](../../apps/agents/monitoring/agent.py#L108) and [test:89](../../tests/unit/test_monitoring_pipeline.py#L89) exist; [intake:13](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L13) fabricates incident-default. | AUD-009, AUD-011 |
| FR-013 | PARTIAL | [Association:185](../../apps/agents/monitoring/agent.py#L185) computes cutoff, but incompatible repository call/no spatial match/no declaration trigger; [existing tests:48](../../tests/contract/test_incident_association.py#L48) cover another service. | AUD-004, AUD-005, AUD-019 |
| FR-014 | PARTIAL | [Query:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120) filters null; [update:148](../../packages/domain/src/domain/repositories/signal_repository.py#L148) has no scoped CAS and no Cosmos implementation; [test:106](../../tests/contract/test_signal_storage.py#L106) is memory-only. | AUD-005, AUD-028 |
| FR-015 | PARTIAL | [Tenant argument:366](../../apps/agents/monitoring/pipeline.py#L366) is not validated; [memory association query:140](../../packages/domain/src/domain/repositories/signal_repository.py#L140) ignores scope. [Isolation test:72](../../tests/contract/test_signal_storage.py#L72) tests only query-by-incident. | AUD-003, AUD-004, AUD-005, AUD-034 |
| FR-016 | PARTIAL | [Counter:207](../../apps/agents/monitoring/agent.py#L207) counts returned updates, including the repository no-op path; no actual `/associate` count/read-back test found. [Storage test:106](../../tests/contract/test_signal_storage.py#L106) is not that endpoint. | AUD-005, AUD-019, AUD-029 |
| FR-017 | IMPLEMENTED | [Gate:100](../../apps/agents/monitoring/agent.py#L100) multiplies freshness; [tests:260](../../tests/unit/test_monitoring_pipeline.py#L260) assert high raw confidence with low effective confidence does not escalate. Missing-source aggregation is separately FR-023. | AUD-001, AUD-015 |
| FR-018 | PARTIAL | [Tracker:40](../../apps/agents/monitoring/freshness.py#L40) supports thresholds/transitions; [tests:68](../../tests/unit/test_monitoring_freshness.py#L68) assert defaults, but first-low and scheduled silence detection are incomplete. | AUD-015, AUD-021 |
| FR-019 | PARTIAL | [Envelope:37](../../apps/api/app/validators/signal_envelope.py#L37) retains provenance; [handoff:111](../../apps/agents/monitoring/agent.py#L111) drops its origin reference and [T067:293](../../tests/unit/test_monitoring_pipeline.py#L293) checks no provenance value. | AUD-010, AUD-018 |
| FR-020 | PARTIAL | [Pipeline:366](../../apps/agents/monitoring/pipeline.py#L366) emits several records, not receipt/every terminal negative/time-driven event; [audit tests:223](../../tests/unit/test_monitoring_pipeline.py#L223) assert only a lower-bound count. | AUD-016, AUD-018, AUD-019, AUD-021 |
| FR-021 | PARTIAL | [Record model:59](../../apps/agents/monitoring/models.py#L59) has fields, but scope/reason validity, full inputs/output, durable wiring, and direct metadata are incomplete; [model tests:85](../../tests/unit/test_monitoring_models.py#L85) check only selected values. | AUD-017, AUD-018, AUD-024, AUD-026, AUD-028 |
| FR-022 | PARTIAL | [create_item:73](../../apps/agents/monitoring/audit.py#L73) and [no-TTL module:43](../../infra/bicep/monitoring-agent.bicep#L43) support intent; [role:94](../../infra/bicep/monitoring-agent.bicep#L94) is broad and module is orphaned. [Tests:24](../../tests/unit/test_monitoring_audit.py#L24) do not inspect deployed policy. | AUD-016, AUD-017, AUD-023, AUD-024, AUD-028 |
| FR-023 | PARTIAL | [Freshness:104](../../apps/agents/monitoring/freshness.py#L104) is not scheduled and [confidence:100](../../apps/agents/monitoring/agent.py#L100) ignores missing other sources; [test:244](../../tests/unit/test_monitoring_pipeline.py#L244) checks buffer growth, not outage continuation. | AUD-013, AUD-014, AUD-015, AUD-031 |
| FR-024 | PARTIAL | [Fallback:84](../../apps/agents/monitoring/agent.py#L84) exists without reduced annotation; [test:191](../../tests/unit/test_monitoring_pipeline.py#L191) asserts processing count only. | AUD-002, AUD-013, AUD-014 |
| FR-025 | PARTIAL | [Health:274](../../apps/agents/monitoring/agent.py#L274) has placeholder values and invalid configured status; [tests:163](../../tests/contract/test_monitoring_escalation.py#L163) check fields only; actual dispatcher differs. | AUD-001, AUD-020 |
| FR-026 | PARTIAL | [Safety call:77](../../apps/agents/monitoring/agent.py#L77) does not establish PII/factual safety or honor fallback review flags; [test:227](../../tests/contract/test_monitoring_escalation.py#L227) uses a predetermined blocked word. | AUD-007, AUD-027, AUD-032 |
| FR-027 | PARTIAL | [Shared system prompt:180](../../apps/agents/common/llm_client.py#L180) includes a general anti-injection instruction; [test:208](../../tests/contract/test_monitoring_escalation.py#L208) never checks the real role boundary or model resistance. | AUD-027, AUD-032 |
| FR-028 | PARTIAL | [RAI policies:145](../../infra/modules/azure-openai.bicep#L145) and [validator:106](../../apps/agents/common/content_safety.py#L106) exist; locale, output limits, filter propagation, and production execution remain incomplete/unverified. [Summary tests:149](../../tests/unit/test_monitoring_pipeline.py#L149) are insufficient. | AUD-007, AUD-012, AUD-027 |
| FR-029 | PARTIAL | [TTL cache:16](../../apps/agents/monitoring/dedup.py#L16) and [tests:6](../../tests/unit/test_monitoring_dedup.py#L6) support single-process dedup only; tenant collision, pre-terminal marking, restart/scale-out remain. | AUD-003, AUD-034 |
| NFR-001 | UNVERIFIED | [Benchmark:189](../../tests/benchmark/test_pipeline_performance.py#L189) repeats one ID with no real services; no sustained 1,000/min monitoring harness/result found. | AUD-013, AUD-031 |
| NFR-002 | PARTIAL | [ACA:1109](../../infra/main.bicep#L1109) exists, but [scale:1180](../../infra/main.bicep#L1180) has no broker rule; module/session cache does not prove multi-instance behavior. Deployment is UNVERIFIED. | AUD-001, AUD-023, AUD-034 |
| NFR-003 | PARTIAL | [Azure Monitor bootstrap:15](../../apps/agents/monitoring/agent.py#L15) is conditional; [pipeline counters:426](../../apps/agents/monitoring/pipeline.py#L426) are not exported instruments and no telemetry assertion body exists. | AUD-021, AUD-022 |
| NFR-004 | CONFLICT | [AU-only primary parameter:78](../../infra/main.bicep#L78), [GlobalStandard default:72](../../infra/modules/azure-openai.bicep#L72), and the plan's replicated DR do not establish independent paired processing. Live residency/DR results are UNVERIFIED. | AUD-025, AUD-033 |
| SC-001 | UNVERIFIED | [Synchronous summary:70](../../apps/agents/monitoring/agent.py#L70) lacks budget enforcement; [benchmark:189](../../tests/benchmark/test_pipeline_performance.py#L189) is not representative end-to-end measurement. | AUD-001, AUD-010, AUD-013, AUD-031 |
| SC-002 | UNVERIFIED | No 100% reconciliation evidence; [MAF direct builder:25](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) is a source-level counterexample to mandatory evaluation. [Classification tests:40](../../tests/contract/test_monitoring_escalation.py#L40) do not test every path. | AUD-002, AUD-018, AUD-029 |
| SC-003 | UNVERIFIED | [Local hold:240](../../apps/agents/monitoring/pipeline.py#L240) is not durable review proof and other entry points bypass it; [no-client test:98](../../tests/contract/test_monitoring_escalation.py#L98) asserts a string. | AUD-002, AUD-009, AUD-029 |
| SC-004 | UNVERIFIED | [Association:202](../../apps/agents/monitoring/agent.py#L202) has a repository mismatch; no 90%/30-second connected measurement. [Storage tests:95](../../tests/contract/test_signal_storage.py#L95) have no timing/scale assertions. | AUD-005, AUD-019, AUD-029, AUD-031 |
| SC-005 | UNVERIFIED | [Time-driven tracker:104](../../apps/agents/monitoring/freshness.py#L104) is unconnected; [freshness tests:231](../../tests/unit/test_monitoring_pipeline.py#L231) do not detect silence or measure continued processing. | AUD-013, AUD-015, AUD-031 |
| SC-006 | UNVERIFIED | [Audit loss path:101](../../apps/agents/monitoring/audit.py#L101) and [incomplete record assertions:203](../../tests/unit/test_monitoring_pipeline.py#L203) prevent an evidence-backed 100% reconciliation claim. | AUD-016, AUD-017, AUD-018, AUD-019, AUD-028 |
| SC-007 | UNVERIFIED | [Configured-only health:274](../../apps/agents/monitoring/agent.py#L274) and [unconfigured benchmark fixture:28](../../tests/benchmark/conftest.py#L28) do not establish real <=1-second readiness/restart detection. | AUD-013, AUD-020, AUD-031 |
| SC-008 | UNVERIFIED | [Constant-mock tests:44](../../tests/contract/test_monitoring_escalation.py#L44) and [five retrieval prompts:1](../../apps/eval-runner/fixtures/spec036/monitoring.jsonl#L1) provide no labeled-post false-positive result. | AUD-008, AUD-027, AUD-032 |

## Acceptance and Edge-Case Coverage

`USn-ASm` identifies the original story and its numbered scenario; `EC-01` through `EC-06` identify the
original edge-case bullets in order. These are report trace labels, not new specification requirements.

| Scenario | Status | Expected behavior and inspected evidence | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | Eligible category/confidence/incident must hand off. [Gate:100](../../apps/agents/monitoring/agent.py#L100), [all-category test:148](../../tests/contract/test_monitoring_escalation.py#L148); actual feeds/worker/MAF do not preserve the full path. Raw-confidence scenario wording also differs from FR-009. | AUD-001, AUD-002, AUD-010, AUD-033 |
| US1-AS2 | IMPLEMENTED | Low confidence must not hand off. [Gate:100](../../apps/agents/monitoring/agent.py#L100) and [negative test:79](../../tests/unit/test_monitoring_pipeline.py#L79) support the local predicate; transport verification remains future. | AUD-001, AUD-029 |
| US1-AS3 | PARTIAL | Null incident blocks the [builder:108](../../apps/agents/monitoring/agent.py#L108) and [test:89](../../tests/unit/test_monitoring_pipeline.py#L89), but real API intake replaces null. | AUD-011, AUD-029 |
| US1-AS4 | PARTIAL | Infrastructure is rejected by [builder:105](../../apps/agents/monitoring/agent.py#L105) and [test:156](../../tests/contract/test_monitoring_escalation.py#L156); MAF workflow still invokes risk unconditionally. | AUD-002 |
| US1-AS5 | PARTIAL | [Event fields:26](../../apps/agents/common/handoffs.py#L26) exist; [delivery test:67](../../tests/unit/test_monitoring_pipeline.py#L67) does not prove persistence, tenant scope, or full payload. | AUD-003, AUD-006, AUD-018 |
| US2-AS1 | PARTIAL | [Blocked branch:183](../../apps/agents/monitoring/pipeline.py#L183) stops locally; flagged signal persistence and no-handoff assertion are absent in [test:62](../../tests/contract/test_monitoring_escalation.py#L62). | AUD-002, AUD-009 |
| US2-AS2 | PARTIAL | [Credible branch:220](../../apps/agents/monitoring/pipeline.py#L220) proceeds; [test:44](../../tests/contract/test_monitoring_escalation.py#L44) checks only classification, not eligible delivery and audit. | AUD-002, AUD-018, AUD-029 |
| US2-AS3 | PARTIAL | [No-client:136](../../apps/agents/monitoring/agent.py#L136) and [test:98](../../tests/contract/test_monitoring_escalation.py#L98) support local hold reason, not durable human review across all paths. | AUD-002, AUD-009 |
| US2-AS4 | IMPLEMENTED | [Exact escalated guard:176](../../apps/agents/monitoring/pipeline.py#L176) skips Tier 2 for non-escalated signals; [normal pipeline:67](../../tests/unit/test_monitoring_pipeline.py#L67) processes validated input without an evaluator. Dedicated no-call assertion is still needed. | AUD-002, AUD-029 |
| US3-AS1 | IMPLEMENTED | [Base summary:55](../../apps/agents/monitoring/agent.py#L55) contains category/sourceKind/incidentId. [Existing test:153](../../tests/unit/test_monitoring_pipeline.py#L153) is weak but source directly implements metadata extraction. | AUD-012 |
| US3-AS2 | CONFLICT | [Narrative enrichment:79](../../apps/agents/monitoring/agent.py#L79) may propagate raw-derived text; [safety test:178](../../tests/unit/test_monitoring_pipeline.py#L178) asserts no output contents. | AUD-007, AUD-033 |
| US3-AS3 | PARTIAL | Fresh summary dictionaries exist at [agent:55](../../apps/agents/monitoring/agent.py#L55), but repeated generation and blocking calls have no concurrent-isolation assertion; [tests:149](../../tests/unit/test_monitoring_pipeline.py#L149). | AUD-012, AUD-013 |
| US4-AS1 | PARTIAL | [Association loop:202](../../apps/agents/monitoring/agent.py#L202) cannot call the domain repository correctly; [storage tests:95](../../tests/contract/test_signal_storage.py#L95) do not declare an incident or associate five through the agent. | AUD-005, AUD-019, AUD-029 |
| US4-AS2 | PARTIAL | [Cutoff:201](../../apps/agents/monitoring/agent.py#L201) and [query:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120) implement time intent; no 30-hour/cutoff-boundary agent assertion, and call mismatch prevents execution. | AUD-005, AUD-029 |
| US4-AS3 | PARTIAL | [Null query:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120) excludes associated records, but [update:148](../../packages/domain/src/domain/repositories/signal_repository.py#L148) has no atomic precondition; [test:106](../../tests/contract/test_signal_storage.py#L106) covers a simple memory update only. | AUD-005 |
| US4-AS4 | PARTIAL | [Absent repository:198](../../apps/agents/monitoring/agent.py#L198) returns zero; exceptions from configured repositories escape the function. HTTP catches them, but that is not the independent function guarantee. | AUD-004, AUD-005 |
| US5-AS1 | PARTIAL | [Effective gate:100](../../apps/agents/monitoring/agent.py#L100) accounts for low freshness; [first tracker update:58](../../apps/agents/monitoring/freshness.py#L58) records no concern; [test:244](../../tests/unit/test_monitoring_pipeline.py#L244) checks only record count. | AUD-015, AUD-018 |
| US5-AS2 | PARTIAL | [Staleness helper:104](../../apps/agents/monitoring/freshness.py#L104) exists but is unscheduled; [test:87](../../tests/unit/test_monitoring_freshness.py#L87) invokes it manually and does not assert other-source continuation. | AUD-013, AUD-015, AUD-031 |
| US5-AS3 | PARTIAL | [Recovery transition:79](../../apps/agents/monitoring/freshness.py#L79) and [test:30](../../tests/unit/test_monitoring_freshness.py#L30) support state recovery; named recovery event/downtime and full pipeline assertions are missing. | AUD-015, AUD-021 |
| US6-AS1 | PARTIAL | [Model:59](../../apps/agents/monitoring/models.py#L59) supports fields, but [pipeline:366](../../apps/agents/monitoring/pipeline.py#L366) misses receipt/terminal negatives; [tests:203](../../tests/unit/test_monitoring_pipeline.py#L203) do not reconcile decision contents. | AUD-016, AUD-018, AUD-026 |
| US6-AS2 | PARTIAL | [Classification records:168](../../apps/agents/monitoring/pipeline.py#L168) include raw content only for misinformation; other outcomes omit it and unexpected is mislabeled. [Tests:40](../../tests/contract/test_monitoring_escalation.py#L40) inspect strings only. | AUD-008, AUD-018 |
| US6-AS3 | PARTIAL | [Association audit:360](../../apps/agents/monitoring/agent.py#L360) uses a synthetic batch signal ID; no per-associated-signal audit test exists in [association tests:48](../../tests/contract/test_incident_association.py#L48). | AUD-019, AUD-029 |
| US6-AS4 | PARTIAL | [Triage audit:312](../../apps/agents/monitoring/pipeline.py#L312) references handoff ID but not full payload; [provenance test:293](../../tests/unit/test_monitoring_pipeline.py#L293) misses original signal linkage. | AUD-006, AUD-012, AUD-018 |
| EC-01 | IMPLEMENTED | Threshold equality uses `>=` at [agent:107](../../apps/agents/monitoring/agent.py#L107); [formula tests:133](../../tests/contract/test_monitoring_escalation.py#L133) use 0.81, so add an exact-0.8 regression assertion. | AUD-026, AUD-029 |
| EC-02 | PARTIAL | [Stage 4:176](../../apps/agents/monitoring/pipeline.py#L176) evaluates all escalated sources, but [MAF prompt:1](../../apps/agents/maf_runtime/agents/monitoring.yaml#L1) restricts its instruction to social and direct paths bypass it. | AUD-002, AUD-027 |
| EC-03 | PARTIAL | Unexpected text is held only after substring tests at [agent:163](../../apps/agents/monitoring/agent.py#L163); [unexpected test:104](../../tests/contract/test_monitoring_escalation.py#L104) misses valid-word-containing invalid responses. | AUD-008 |
| EC-04 | PARTIAL | [Per-process cache:16](../../apps/agents/monitoring/dedup.py#L16) and [duplicate test:141](../../tests/unit/test_monitoring_pipeline.py#L141) cover sequential duplicates, not tenant collision/concurrent workers/restart or failed partial work. | AUD-003, AUD-034 |
| EC-05 | PARTIAL | [Query memory path:140](../../packages/domain/src/domain/repositories/signal_repository.py#L140) ignores tenant; [isolation test:72](../../tests/contract/test_signal_storage.py#L72) exercises a different query. | AUD-003, AUD-005 |
| EC-06 | UNVERIFIED | [Legacy health:274](../../apps/agents/monitoring/agent.py#L274) always returns 200 and no worker is connected; no monitoring restart/redelivery test or platform proof was found. | AUD-001, AUD-020, AUD-029, AUD-034 |

## Original Task Coverage

The original checkbox state is reproduced, not changed. Each original ID appears exactly once here.
For MISSING test extensions, links point to the existing test that was inspected or the controlling source;
an absent historical filename is not presented as an evidence link.

| Original ID | Original state | Status | Implementation / actual test evidence and limitation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Config:15](../../apps/agents/monitoring/config.py#L15) reads all twelve original variables/defaults; [tests:172](../../tests/unit/test_monitoring_models.py#L172) check most defaults and three overrides. Validation/complete override coverage is separate. | AUD-026 |
| T002 | [X] | IMPLEMENTED | [DecisionType:24](../../apps/agents/monitoring/models.py#L24), [exact nine-value assertion:12](../../tests/unit/test_monitoring_models.py#L12). Receipt semantics still need contract reconciliation. | AUD-018, AUD-033 |
| T003 | [X] | IMPLEMENTED | [Enums:38](../../apps/agents/monitoring/models.py#L38), [exact enum assertions:39](../../tests/unit/test_monitoring_models.py#L39). | None |
| T004 | [X] | PARTIAL | [Decision model:59](../../apps/agents/monitoring/models.py#L59) has the fields; [tests:53](../../tests/unit/test_monitoring_models.py#L53) permit absent required-context values, no bounds/immutability proof. | AUD-018, AUD-026 |
| T005 | [X] | IMPLEMENTED | [Freshness model:90](../../apps/agents/monitoring/models.py#L90), [construction tests:114](../../tests/unit/test_monitoring_models.py#L114). Runtime tracking is separately incomplete. | AUD-015, AUD-026 |
| T006 | [X] | IMPLEMENTED | [Buffer model:107](../../apps/agents/monitoring/models.py#L107), [field tests:143](../../tests/unit/test_monitoring_models.py#L143). | AUD-026 |
| T007 | [X] | IMPLEMENTED | [Field validators:11](../../apps/api/app/validators/signal_envelope.py#L11), [negative range/blank assertions:233](../../tests/unit/test_monitoring_models.py#L233). Broader producer taxonomy is not tested here. | AUD-010 |
| T008 | [X] | PARTIAL | [Model/config tests:9](../../tests/unit/test_monitoring_models.py#L9) contain real assertions but omit several override, invalid-model, boundary, and buffer metadata invariants. | AUD-026 |
| T009 | [X] | IMPLEMENTED | [TTL service:16](../../apps/agents/monitoring/dedup.py#L16) provides both methods and eviction; [tests:6](../../tests/unit/test_monitoring_dedup.py#L6) exercise the scoped single-process component, not scale-out correctness. | AUD-003, AUD-034 |
| T010 | [X] | PARTIAL | [Tracker:40](../../apps/agents/monitoring/freshness.py#L40) and [staleness:104](../../apps/agents/monitoring/freshness.py#L104) implement transitions, but first-low is healthy and time checks are unconnected. | AUD-015 |
| T011 | [X] | PARTIAL | [Tests:6](../../tests/unit/test_monitoring_dedup.py#L6) cover first/duplicate/after-expiry/eviction; no exact-window, concurrent, failed-attempt, or restart assertion. | AUD-034 |
| T012 | [X] | PARTIAL | [Freshness tests:6](../../tests/unit/test_monitoring_freshness.py#L6) manually set offline; no actual degraded-to-offline assertion or complete threshold timing matrix. | AUD-015 |
| T013 | [X] | IMPLEMENTED | [Writer/create:42](../../apps/agents/monitoring/audit.py#L42), [call assertion:24](../../tests/unit/test_monitoring_audit.py#L24) implement the injectable direct-write component; production client and serialized annotation remain follow-ups. | AUD-001, AUD-017, AUD-028 |
| T014 | [X] | IMPLEMENTED | [Bounded buffer:75](../../apps/agents/monitoring/audit.py#L75), [failure tests:53](../../tests/unit/test_monitoring_audit.py#L53). Durability on restart is not implied. | AUD-016 |
| T015 | [X] | PARTIAL | [JSONL spill:85](../../apps/agents/monitoring/audit.py#L85), [spill test:94](../../tests/unit/test_monitoring_audit.py#L94); critical log only, failures swallowed, no persistent mount/alert integration. | AUD-016, AUD-021, AUD-022 |
| T016 | [X] | PARTIAL | [Flush:109](../../apps/agents/monitoring/audit.py#L109), [tests:131](../../tests/unit/test_monitoring_audit.py#L131); no chronological failure-order or duplicate-conflict assertions, no scheduled recovery. | AUD-016, AUD-017 |
| T017 | [X] | PARTIAL | [Status:167](../../apps/agents/monitoring/audit.py#L167), [tests:198](../../tests/unit/test_monitoring_audit.py#L198); retained files and historical spill counters make status unreliable. | AUD-017, AUD-020 |
| T018 | [X] | PARTIAL | [Audit tests:21](../../tests/unit/test_monitoring_audit.py#L21) cover nominal tiers but not exact ordering, lost acknowledgments, disk failure, or complete recovery state. | AUD-016, AUD-017 |
| T019 | [X] | MISSING | No monitoring emulator harness found; [mock write test:24](../../tests/unit/test_monitoring_audit.py#L24) and [memory repository test:27](../../tests/contract/test_signal_storage.py#L27) are not equivalents. | AUD-028 |
| T020 | [X] | IMPLEMENTED | [Evaluation call:150](../../apps/agents/monitoring/agent.py#L150) matches [LLMClient signature:144](../../apps/agents/common/llm_client.py#L144); [prompt-call test:208](../../tests/contract/test_monitoring_escalation.py#L208) checks purpose. | AUD-027 |
| T021 | [X] | IMPLEMENTED | [Five-category set:35](../../apps/agents/monitoring/agent.py#L35), [all-category assertion:148](../../tests/contract/test_monitoring_escalation.py#L148). Actual feed taxonomy remains a separate integration conflict. | AUD-010 |
| T022 | [X] | IMPLEMENTED | [Effective computation:100](../../apps/agents/monitoring/agent.py#L100), [formula/low-freshness tests:133](../../tests/contract/test_monitoring_escalation.py#L133). | AUD-014 |
| T023 | [X] | IMPLEMENTED | [wait_for:150](../../apps/agents/monitoring/agent.py#L150), [timeout test:76](../../tests/contract/test_monitoring_escalation.py#L76) support awaited timeout behavior; transport/thread and whole-pipeline budgets remain incomplete. | AUD-013 |
| T024 | [X] | PARTIAL | [Unexpected handling:163](../../apps/agents/monitoring/agent.py#L163), [test:104](../../tests/contract/test_monitoring_escalation.py#L104); substring-valid invalid answers evade the intended hold. | AUD-002, AUD-008 |
| T025 | [X] | IMPLEMENTED | [Penalty selection:201](../../apps/agents/monitoring/pipeline.py#L201) and [handoff test:116](../../tests/contract/test_monitoring_escalation.py#L116) implement a distinct configurable suspicious penalty. Audit clamping/config bounds need strengthening. | AUD-008, AUD-026 |
| T026 | [X] | PARTIAL | [Evaluation audit branches:168](../../apps/agents/monitoring/pipeline.py#L168) exist only in pipeline, mislabel unexpected result, omit some evaluated inputs, and do not persist review status. | AUD-008, AUD-009, AUD-018 |
| T027 | [X] | PARTIAL | [Six classification tests:40](../../tests/contract/test_monitoring_escalation.py#L40) assert strings and a manually supplied penalty, not complete pass/block/hold delivery effects. | AUD-002, AUD-008, AUD-009 |
| T028 | [X] | MISSING | [Existing misinformation tests:52](../../tests/contract/test_misinformation_detector.py#L52) exercise only [Tier-1 detector:8](../../apps/api/app/services/ingestion/misinformation_detector.py#L8); no required Tier-2 fail-closed extension found. | AUD-002, AUD-008, AUD-032 |
| T029 | [X] | PARTIAL | [Pipeline constructor:46](../../apps/agents/monitoring/pipeline.py#L46) accepts dependencies, but its validator is disconnected from its agent and no production caller constructs it. | AUD-001, AUD-012 |
| T030 | [X] | PARTIAL | [Validation:79](../../apps/agents/monitoring/pipeline.py#L79) audits rejection; [test:133](../../tests/unit/test_monitoring_pipeline.py#L133) checks an internal count, not emitted validation metric. | AUD-018, AUD-021 |
| T031 | [X] | PARTIAL | [Dedup stage:107](../../apps/agents/monitoring/pipeline.py#L107), [test:141](../../tests/unit/test_monitoring_pipeline.py#L141); no exported metric, scoped key, or partial-failure recovery. | AUD-003, AUD-021, AUD-034 |
| T032 | [X] | PARTIAL | [Freshness stage:133](../../apps/agents/monitoring/pipeline.py#L133) records arrival-driven transitions only; [test:244](../../tests/unit/test_monitoring_pipeline.py#L244) checks growth, not required custom events. | AUD-015, AUD-021 |
| T033 | [X] | PARTIAL | [Stage 4:168](../../apps/agents/monitoring/pipeline.py#L168) wires classification/penalty/stop locally, but strict outcomes, durable review, and alternate-path gate coverage are absent. | AUD-002, AUD-008, AUD-009 |
| T034 | [X] | PARTIAL | [Stage 5:262](../../apps/agents/monitoring/pipeline.py#L262), [tests:149](../../tests/unit/test_monitoring_pipeline.py#L149); repeated generation, incomplete validator/annotation, and blocking calls remain. | AUD-007, AUD-012, AUD-013, AUD-014 |
| T035 | [X] | PARTIAL | [Triage:289](../../apps/agents/monitoring/pipeline.py#L289) builds events and optionally retries; [test:67](../../tests/unit/test_monitoring_pipeline.py#L67) delivers to a list. No real persistence/DLQ/notification wiring. | AUD-003, AUD-006, AUD-012, AUD-018 |
| T036 | [X] | PARTIAL | [Orchestrator:366](../../apps/agents/monitoring/pipeline.py#L366) calls six stages but always returns None and has no top-level outcome/error/settlement handling. [Tests:129](../../tests/unit/test_monitoring_pipeline.py#L129) accept None. | AUD-001, AUD-013, AUD-018, AUD-034 |
| T037 | [X] | IMPLEMENTED | [Tests:63](../../tests/unit/test_monitoring_pipeline.py#L63) assert positive delivery and all requested negative category/confidence/incident paths at the in-process boundary. | AUD-001, AUD-029 |
| T038 | [X] | PARTIAL | [Tests:149](../../tests/unit/test_monitoring_pipeline.py#L149) usually assert signal_count only, including a supposed blocked keyword not in the current fallback denylist. | AUD-007, AUD-012, AUD-014 |
| T039 | [X] | PARTIAL | [Tests:203](../../tests/unit/test_monitoring_pipeline.py#L203) count buffers for three paths, not exact decisions across every classification/freshness/triage outcome. | AUD-018 |
| T040 | [X] | IMPLEMENTED | [Contract tests:130](../../tests/contract/test_monitoring_escalation.py#L130) assert effective confidence, low-freshness rejection, and five categories; producer/runtime gaps remain separately tracked. | AUD-002, AUD-010 |
| T041 | [X] | PARTIAL | [Pipeline freshness tests:231](../../tests/unit/test_monitoring_pipeline.py#L231) cover score update/record-count growth only, not elapsed degraded/offline/recovery sequence. | AUD-015 |
| T042 | [X] | PARTIAL | [FastAPI health:274](../../apps/agents/monitoring/agent.py#L274) replaces the handler but violates value/status contract and is not the deployed app. | AUD-001, AUD-020 |
| T043 | [X] | PARTIAL | [Health:274](../../apps/agents/monitoring/agent.py#L274) reads tracker/writer if injected, but neither LLM ping nor Service Bus queue depth is implemented. | AUD-001, AUD-020 |
| T044 | [X] | PARTIAL | [Health tests:163](../../tests/contract/test_monitoring_escalation.py#L163) assert field presence only, not types/enums/status matrix/queue thresholds. | AUD-020 |
| T045 | [X] | PARTIAL | [Association route:345](../../apps/agents/monitoring/agent.py#L345) delegates and formats count, but lacks auth, config default propagation, and compatible repository behavior. | AUD-004, AUD-005 |
| T046 | [X] | PARTIAL | [Tenant argument:205](../../apps/agents/monitoring/agent.py#L205) is incompatible with [repository scope:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120); memory query/update are unscoped. | AUD-003, AUD-005 |
| T047 | [X] | PARTIAL | [Batch record:360](../../apps/agents/monitoring/agent.py#L360) is not the required per-signal association audit. | AUD-019 |
| T048 | [X] | MISSING | [Association contract tests:48](../../tests/contract/test_incident_association.py#L48) cover the initial ingestion service, not retrospective tenant/cutoff scenarios. | AUD-005, AUD-019 |
| T049 | [X] | MISSING | No monitoring `/associate` integration assertion found; [repository test:106](../../tests/contract/test_signal_storage.py#L106) does not call the endpoint or verify its count/audit. | AUD-029 |
| T050 | [X] | MISSING | [Pipeline imports:17](../../apps/agents/monitoring/pipeline.py#L17) and [process body:366](../../apps/agents/monitoring/pipeline.py#L366) contain no required root/child spans; shared Foundry span is not equivalent. | AUD-021 |
| T051 | [X] | MISSING | [Internal accessors:426](../../apps/agents/monitoring/pipeline.py#L426) are not the thirteen exported, dimensioned instruments from [telemetry contract:9](contracts/telemetry.md#L9). | AUD-021 |
| T052 | [X] | MISSING | [Pipeline:133](../../apps/agents/monitoring/pipeline.py#L133) and [audit logs:75](../../apps/agents/monitoring/audit.py#L75) do not emit the eight named custom-event contracts. | AUD-021 |
| T053 | [X] | MISSING | [Config:15](../../apps/agents/monitoring/config.py#L15) lacks thresholds; [generic alerts:76](../../infra/modules/monitoring.bicep#L76) are different conditions. | AUD-022 |
| T054 | [X] | MISSING | [process_signal:366](../../apps/agents/monitoring/pipeline.py#L366) accepts no broker trace parent/correlation input and emits no root span attributes. | AUD-001, AUD-021 |
| T055 | [X] | MISSING | [Test file:1](../../tests/unit/test_monitoring_pipeline.py#L1) names T055 only in its header; inspected bodies never capture exported metrics or dimensions. | AUD-021 |
| T056 | [X] | PARTIAL | Renamed [container:43](../../infra/bicep/monitoring-agent.bicep#L43) has key/no TTL, but is not wired and does not configure serverless account mode. | AUD-023, AUD-024 |
| T057 | [X] | PARTIAL | Renamed [queue:78](../../infra/bicep/monitoring-agent.bicep#L78) requires sessions; no connected publisher/receiver/root module proves signal-ID sessions or effective dedup affinity. | AUD-001, AUD-023, AUD-034 |
| T058 | [X] | MISSING | [Actual scale:1180](../../infra/main.bicep#L1180) and [alternate ACA:335](../../infra/bicep/main.bicep#L335) contain no monitoring Service Bus depth rule. | AUD-023 |
| T059 | [X] | PARTIAL | [Conditional roles:94](../../infra/bicep/monitoring-agent.bicep#L94) exist; module is orphaned, no live receiver proof, and audit contributor scope exceeds append-only intent. | AUD-023, AUD-024 |
| T060 | [X] | MISSING | [Alternate root:40](../../infra/bicep/main.bicep#L40) and [actual root:165](../../infra/main.bicep#L165) reference generic monitoring, not the agent resource module. | AUD-023 |
| T061 | [X] | IMPLEMENTED | [Agent dependencies:15](../../apps/agents/pyproject.toml#L15) declare tenacity and azure-cosmos; installation/build success was not assessed by execution. | None |
| T062 | [X] | MISSING | [Bushfire assertions:17](../../tests/simulation/test_bushfire_scenario.py#L17) cover generator/shape only, not the requested full monitoring pipeline extension. | AUD-030 |
| T063 | [X] | MISSING | No monitoring broker harness found; [local EventBus test:5](../../tests/integration/test_handoff_chain.py#L5) and [different synthetic pipeline test:74](../../tests/integration/test_signal_pipeline_e2e_036.py#L74) are not substitutes. | AUD-029 |
| T064 | [X] | UNVERIFIED | No local execution record; [quickstart:107](quickstart.md#L107) has a contradicted confidence assertion and unsafe builder-based blocking example. | AUD-033 |
| T065 | [X] | UNVERIFIED | [Plan resolution table:148](plan.md#L148) is authored design, while [checklist:1](checklists/requirements.md#L1) remains entirely unchecked and implementation gaps persist. | AUD-033 |
| T066 | [X] | PARTIAL | New modules have docstrings/loggers, but [constructor:41](../../apps/agents/monitoring/agent.py#L41) and [app factory:225](../../apps/agents/monitoring/agent.py#L225) retain untyped boundaries and stale explanatory claims. No lint/type execution proof. | AUD-026, AUD-033 |
| T067 | [X] | PARTIAL | [Provenance test:293](../../tests/unit/test_monitoring_pipeline.py#L293) supplies rich provenance but only asserts category/sourceKind; [handoff:111](../../apps/agents/monitoring/agent.py#L111) omits the required origin evidence. | AUD-018 |
| T068 | [X] | MISSING | No named/equivalent sustained monitoring load harness; [benchmark:189](../../tests/benchmark/test_pipeline_performance.py#L189) has repeated dedup ID, mock dependencies, and no 5,000-signal loss/SLA assertions. | AUD-031 |
| T069 | [X] | PARTIAL | [Security tests:204](../../tests/contract/test_monitoring_escalation.py#L204) assert a prompt substring or conditional keyword fallback, not actual trusted message boundaries or model resistance. | AUD-007, AUD-027, AUD-032 |

## Contract and Amendment Assessment

### Pipeline, Model, and HTTP Contracts

| Obligation | Assessment and exact evidence | Follow-up |
| --- | --- | --- |
| Six stages in the required order | Authored in [process_signal:366](../../apps/agents/monitoring/pipeline.py#L366), but unconnected worker and alternate bypass prevent end-to-end conformance. | AUD-001, AUD-002 |
| Input rejection and duplicate discard | Both create local audit records; exported metrics and retry-safe terminal outcomes are missing at [pipeline:79](../../apps/agents/monitoring/pipeline.py#L79). | AUD-018, AUD-021, AUD-034 |
| Misinformation must precede summary/triage | Holds for the local pipeline, not [MAF:25](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) or public builder. | AUD-002, AUD-008 |
| Rule-based fallback with reduced annotation | Metadata fallback exists, annotation does not at [agent:53](../../apps/agents/monitoring/agent.py#L53). | AUD-014 |
| Latency budget: 5/1/1/3000/500/500 ms stages | Source has one outer evaluation wait, not a whole-pipeline deadline; [summary:70](../../apps/agents/monitoring/agent.py#L70) blocks. No measurement proves budget. | AUD-013, AUD-031 |
| Raw, effective, freshness confidence and record metadata | Fields exist at [models:59](../../apps/agents/monitoring/models.py#L59); incomplete stage inputs, negative values before clamp, blank required context, and late direct-write annotation remain. | AUD-017, AUD-018, AUD-026 |
| Unassociated partition has 16 synthetic buckets | [Scope helper:35](../../apps/agents/monitoring/pipeline.py#L35) uses an eight-hex hash suffix, not modulo 16. This is a design/source conflict, not a claim of measured hot partitioning. | AUD-026, AUD-033 |
| Append-only and infinite retention | Create-only method and no-TTL declaration exist, but enforcement/deployment and journal loss guarantees do not. | AUD-016, AUD-024, AUD-028 |
| Recovery flush order and annotations | [Flush:109](../../apps/agents/monitoring/audit.py#L109) fails strict ordering/replay guarantees on partial failures. | AUD-017 |
| Healthy/degraded/offline transition rules | [Tracker:104](../../apps/agents/monitoring/freshness.py#L104) requires external polling and can need another check to move a long-silent healthy source through degraded to offline; no scheduler/audit exists. | AUD-015 |
| GET /health schema/status matrix | Placeholder queue, invalid configured enum, no actual connectivity, and HTTP 200 even unhealthy at [health:274](../../apps/agents/monitoring/agent.py#L274). | AUD-020 |
| POST /associate identity/default/error schema | Unauthenticated route, hardcoded request lookback default, inconsistent 400/503 shape and raw exception detail at [route:345](../../apps/agents/monitoring/agent.py#L345). | AUD-004, AUD-005 |
| Retrospective DB error returns zero safely | Absent dependency returns zero; configured dependency errors escape [function:185](../../apps/agents/monitoring/agent.py#L185); partial updates need an explicit count/error policy. | AUD-005 |
| Configuration read once at startup | Values are read per [dataclass construction:15](../../apps/agents/monitoring/config.py#L15), not module import as its header says; separate default config instances can diverge from an injected agent. | AUD-012, AUD-026 |

### Every Required Instrument

All rows below are **MISSING as monitoring-specific emitted instruments**. Generic Azure SDK/HTTP telemetry,
Foundry inference spans, logger messages, and integer properties are not equivalents. Evidence is the full
[pipeline:17](../../apps/agents/monitoring/pipeline.py#L17),
[audit writer:26](../../apps/agents/monitoring/audit.py#L26),
[health:274](../../apps/agents/monitoring/agent.py#L274), and all named monitoring test bodies.
AUD-021 owns implementation and assertions; AUD-022 owns alert consumption.

| Metric | Required type/unit and specific gap |
| --- | --- |
| signal_processing_latency | Histogram/ms; elapsed time is logged only for the non-early-return path. |
| escalation_rate | Counter/count per window; only an in-memory escalation counter exists. |
| misinformation_detection_rate | Counter/count per window; only an in-memory misinformation counter exists. |
| degradation_events | Counter/count; no monitoring instrument for arrival or timer transitions. |
| handoff_success_rate | Gauge/ratio; local property exists, not an exported instrument. |
| signal_validation_failures_total | Counter/count; local increment is not metric emission. |
| dedup_discards_total | Counter/count; local increment is not metric emission. |
| llm_evaluation_latency | Histogram/ms; shared client timing is not monitoring stage latency with required dimensions. |
| llm_timeout_count | Counter/count; timeout log/result only. |
| audit_buffer_depth | Gauge/count; writer property only. |
| audit_buffer_file_spills | Counter/count; private historical count/log only. |
| health_check_latency | Histogram/ms; not emitted by health. |
| effective_confidence_distribution | Histogram/ratio; computation/audit fields only. |

All metrics require category, source_type, decision, and tenant_id dimensions with an explicit not-applicable
policy for operational checks. The stage contract also names `data_source_freshness`, and the alert table
references `processing_queue_depth`; neither is in the thirteen-instrument table nor emitted by monitoring.
Resolve these two additional obligations under AUD-021/AUD-033 rather than silently dropping them.

| Custom event | Required properties/trigger not implemented as that event |
| --- | --- |
| MisinformationBlocked | signal_id, category, source_kind on blocked classification. |
| SignalHeldForReview | signal_id and exact unavailable/timeout/unexpected reason. |
| DataSourceDegraded | data_source_id, source_type, prior/new status for time- or arrival-driven degradation. |
| DataSourceRecovered | data_source_id, source_type, downtime_minutes. |
| HandoffDeadLettered | durable handoff_id, incident_id, failure_reason. |
| AuditBufferActivated | buffer_depth, trigger_error on activation. |
| AuditBufferFlushed | records_flushed, flush_source after durable replay. |
| RetrospectiveAssociation | incident_id, jurisdiction_id, actual signals_associated. |

The required trace hierarchy is also absent: `signal_processing` root; `input_validation`, `dedup_check`,
`freshness_assessment`, conditional `misinformation_evaluation/llm_call`, `signal_summarisation/llm_call` and
`content_safety_validation`, `confidence_triage/handoff_creation/handoff_delivery/retry_attempt_N`, and
`audit_record_write/buffer_flush`. The pipeline takes no incoming broker trace parent. Shared inference-only
spans are credited as existing adjacent behavior, not full trace conformance.

### Amendment Identifiers

| ID | Status | Assessment / evidence | Follow-up |
| --- | --- | --- | --- |
| PER-022 | UNVERIFIED | [Spec:262](spec.md#L262) labels a cross-reference validated but contains no named SME/practitioner/date satisfying the [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1). No sign-off is inferred. | AUD-033 |
| PER-023 | UNVERIFIED | [Spec:263](spec.md#L263) references technical actors, not a local validation record or every-change consultation history. | AUD-033 |
| PER-024 | IMPLEMENTED | Explicit placeholder/preconditions at [spec:264](spec.md#L264); this is an authored deferral, not validated PH/JP/BD persona delivery. | AUD-033 |
| HYP-008 | UNVERIFIED | [Spec:270](spec.md#L270) names an absent HYP-HYP-008 stub; renamed [rubric-postfeature:1](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) reports portfolio structure, not this hypothesis's consultation/per-spec outcome. | AUD-033 |
| HYP-033 | UNVERIFIED | [Evidence:19](evidence/HYP-033.md#L19) says Not tested; licensing, PH validator, D-009 and seasonal measurements are not established here. Stub format is authored. | AUD-033 |
| HYP-034 | UNVERIFIED | [Evidence:19](evidence/HYP-034.md#L19) says Not tested; JP licensing/validator/D-009 and latency/availability proof remain deferred. | AUD-033 |
| HYP-035 | UNVERIFIED | [Evidence:19](evidence/HYP-035.md#L19) says Not tested; BD agreement/validator/D-009 and monsoon availability proof remain deferred. | AUD-033 |
| SCP-025 | IMPLEMENTED | [Spec:276](spec.md#L276) explicitly defers country variants pending named governance/calibration prerequisites; no new country implementation is required by this audit. | AUD-033 |
| SCP-026 | PARTIAL | [Spec:277](spec.md#L277) forbids unilateral constitutional changes, but AU/DR/hosting tensions need an explicit risk/decision record respecting the current constitution. | AUD-025, AUD-033 |
| SCP-027 | IMPLEMENTED | [Spec:278](spec.md#L278) names arbitration and defers recovery/warning ownership. Recovery catalogue/M&E endpoints in monitoring are not counted as spec-010 signal-triage delivery. | AUD-033 |

## Local Checklist and Review-Claim Assessment

Every CHK item is originally unchecked. The following table assesses the question/design answer separately
from the implementation and does not retroactively tick it. A design deferral is not a missing implementation
obligation unless the local specification separately requires the behavior. AUD-033 owns unresolved policy/
specification decisions; concrete implementation follow-ups are also named. The 16 items highlighted by the
plan are included individually, not treated as completed because their resolution table exists.

| Checklist ID | Original state | Independent assessment and evidence | Follow-up |
| --- | --- | --- | --- |
| CHK001 | [ ] | Design resolves boundary validation; [validator:25](../../apps/api/app/validators/signal_envelope.py#L25) exists, but actual intake is disconnected and failure telemetry incomplete. | AUD-001, AUD-021, AUD-033 |
| CHK002 | [ ] | [Plan:148](plan.md#L148) explicitly defers priority queuing and chooses FIFO; do not invent a priority implementation requirement. Operational FIFO still needs transport proof. | AUD-001, AUD-033 |
| CHK003 | [ ] | Design defers a separate v1 concurrency limit; [threaded evaluation:150](../../apps/agents/monitoring/agent.py#L150) can leave underlying work running. Throughput/resource budget unverified. | AUD-013, AUD-031, AUD-033 |
| CHK004 | [ ] | Required commander surfacing lacks channel/ack/SLA definition and connected [DLQ callback:64](../../apps/agents/monitoring/pipeline.py#L64). | AUD-006, AUD-022, AUD-033 |
| CHK005 | [ ] | [Base summary:55](../../apps/agents/monitoring/agent.py#L55) supplies a fallback, but narrative allowance and safety metadata interpretation conflict with structured-only output. | AUD-007, AUD-014, AUD-033 |
| CHK006 | [ ] | [Validator:163](../../apps/agents/common/content_safety.py#L163) is not a PII/misleading-content taxonomy; policy and assertions incomplete. | AUD-007, AUD-027, AUD-033 |
| CHK007 | [ ] | [Data model](data-model.md) and research define scope/bucketing; [helper:35](../../apps/agents/monitoring/pipeline.py#L35) differs from modulo-16 design. | AUD-024, AUD-026, AUD-033 |
| CHK008 | [ ] | Plan explicitly defers archival; no TTL is declared in [module:43](../../infra/bicep/monitoring-agent.bicep#L43). Deployment/cost stewardship remains unverified, not permission to add expiry. | AUD-024, AUD-033 |
| CHK009 | [ ] | [Update:148](../../packages/domain/src/domain/repositories/signal_repository.py#L148) lacks compare-and-set or concurrent-incident resolution. | AUD-005, AUD-033 |
| CHK010 | [ ] | Health contract defines queue thresholds, task says scaler 100, root comment says 50; [actual scale:1180](../../infra/main.bicep#L1180) has no queue rule. | AUD-020, AUD-023, AUD-033 |
| CHK011 | [ ] | [Declaration:20](../../apps/api/app/api/routes/incidents.py#L20) does not trigger retrospective matching; trigger contract is unresolved. | AUD-019, AUD-033 |
| CHK012 | [ ] | Prompts are inline [agent:140](../../apps/agents/monitoring/agent.py#L140); no monitoring decision prompt-version/replay assertion exists. | AUD-027, AUD-033 |
| CHK013 | [ ] | Research allocates 3 seconds; [wait:150](../../apps/agents/monitoring/agent.py#L150) bounds awaiting, not all transport/summary work. | AUD-013, AUD-033 |
| CHK014 | [ ] | [Cache:16](../../apps/agents/monitoring/dedup.py#L16) is process-local; no monitoring restart/settlement proof. | AUD-001, AUD-034, AUD-033 |
| CHK015 | [ ] | [Config:62](../../apps/agents/monitoring/config.py#L62) supplies version text; semantics/update policy and revision-bound runs remain unverified. | AUD-026, AUD-033 |
| CHK016 | [ ] | Multiplicative formula is implemented at [agent:100](../../apps/agents/monitoring/agent.py#L100), but it does not quantify missing other-source coverage. | AUD-014, AUD-015, AUD-033 |
| CHK017 | [ ] | Existing fallback factor setting is not applied in [summary/triage:53](../../apps/agents/monitoring/agent.py#L53); approved annotation/formula missing. | AUD-014, AUD-033 |
| CHK018 | [ ] | [Association:185](../../apps/agents/monitoring/agent.py#L185) has no geometry input/matching; jurisdiction plus location precision is not resolved operationally. | AUD-005, AUD-033 |
| CHK019 | [ ] | Timeout outcome exists; [Foundry:397](../../apps/agents/common/foundry_chat_client.py#L397) ignores the supplied transport timeout. | AUD-008, AUD-013, AUD-033 |
| CHK020 | [ ] | [Validator:106](../../apps/agents/common/content_safety.py#L106) supports optional locale but monitoring supplies none; expected locale remains unspecified in local contract. | AUD-007, AUD-033 |
| CHK021 | [ ] | Data model defines four transitions; [tracker:104](../../apps/agents/monitoring/freshness.py#L104) is unconnected to timers and tests miss actual offline transition. | AUD-015, AUD-033 |
| CHK022 | [ ] | Arrival recovery exists at [freshness:79](../../apps/agents/monitoring/freshness.py#L79); bounded recovery/event latency is unmeasured. | AUD-015, AUD-031, AUD-033 |
| CHK023 | [ ] | [Config:33](../../apps/agents/monitoring/config.py#L33) reads per-type environment settings; all override/alias cases are not asserted. | AUD-015, AUD-026, AUD-033 |
| CHK024 | [ ] | Research's permanent session-affinity assumption is unsound across owner replacement; [cache:16](../../apps/agents/monitoring/dedup.py#L16) is not durable. | AUD-034, AUD-033 |
| CHK025 | [ ] | Max reasoning config exists, but [record:75](../../apps/agents/monitoring/models.py#L75) does not enforce/use the limit. | AUD-026, AUD-033 |
| CHK026 | [ ] | Document/config defaults agree at [config:33](../../apps/agents/monitoring/config.py#L33); drift assertions over all sources are still future. | AUD-015, AUD-026, AUD-033 |
| CHK027 | [ ] | Current spec and [penalty branch:201](../../apps/agents/monitoring/pipeline.py#L201) supersede the checklist's historical fail-open premise; full-pipeline differential assertion is missing. | AUD-008, AUD-033 |
| CHK028 | [ ] | [Monitoring set:35](../../apps/agents/monitoring/agent.py#L35) matches spec, but [domain enum:11](../../packages/domain/src/domain/models/signal.py#L11) and normalizers do not. | AUD-010, AUD-033 |
| CHK029 | [ ] | The 1-second targets agree in prose; [health:274](../../apps/agents/monitoring/agent.py#L274) does not perform real checks, so timing proof is not established. | AUD-020, AUD-031, AUD-033 |
| CHK030 | [ ] | 3-second await partially resolves design latency; [summary:70](../../apps/agents/monitoring/agent.py#L70) and duplicate generation exceed the designed boundary risk. | AUD-012, AUD-013, AUD-033 |
| CHK031 | [ ] | Fail-open text is stale relative to current spec; [substring parser:163](../../apps/agents/monitoring/agent.py#L163) and output safety still leave concrete gaps. | AUD-007, AUD-008, AUD-033 |
| CHK032 | [ ] | [Nine-value enum:24](../../apps/agents/monitoring/models.py#L24) includes discarded/validation_failed but not receipt or terminal negative triage types demanded by full decision accounting. | AUD-018, AUD-033 |
| CHK033 | [ ] | No labeled monitoring social set found; [retrieval fixture:1](../../apps/eval-runner/fixtures/spec036/monitoring.jsonl#L1) is not SC-008 data. | AUD-032, AUD-033 |
| CHK034 | [ ] | 90% association target has no inspected rationale/measurement; [update:148](../../packages/domain/src/domain/repositories/signal_repository.py#L148) is not implemented for Cosmos. | AUD-005, AUD-031, AUD-033 |
| CHK035 | [ ] | No scheduler calls [staleness:104](../../apps/agents/monitoring/freshness.py#L104); detection and continuation measurement boundaries remain unresolved. | AUD-015, AUD-031, AUD-033 |
| CHK036 | [ ] | [Counter-only audit tests:203](../../tests/unit/test_monitoring_pipeline.py#L203) are not an independent ingress-to-audit reconciler. | AUD-018, AUD-028, AUD-033 |
| CHK037 | [ ] | Research chooses receipt-to-creation; [pipeline:289](../../apps/agents/monitoring/pipeline.py#L289) may await delivery retries. Formal SLA/test boundary needs alignment. | AUD-006, AUD-013, AUD-031, AUD-033 |
| CHK038 | [ ] | [Retry helper:124](../../apps/agents/common/handoffs.py#L124) exists; actual downstream outage/DLQ/queue behavior is unconnected. Proactive circuit-breaker requirement remains a design choice. | AUD-006, AUD-033 |
| CHK039 | [ ] | [Association loop:207](../../apps/agents/monitoring/agent.py#L207) is sequential with no batch-scale assertion or paging/performance proof. | AUD-005, AUD-031, AUD-033 |
| CHK040 | [ ] | [Three tiers:42](../../apps/agents/monitoring/audit.py#L42) exist but do not guarantee no loss or scheduled/ordered recovery. | AUD-016, AUD-017, AUD-028, AUD-033 |
| CHK041 | [ ] | [Held record:240](../../apps/agents/monitoring/pipeline.py#L240) is not a review release/re-evaluation workflow. | AUD-009, AUD-033 |
| CHK042 | [ ] | [Association query:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120) has no disposition filter; flagged status is not representable. | AUD-005, AUD-009, AUD-033 |
| CHK043 | [ ] | Input accepts one category at [validator:28](../../apps/api/app/validators/signal_envelope.py#L28); multi-hazard representation is an unresolved design question, not implicitly delivered. | AUD-010, AUD-033 |
| CHK044 | [ ] | Startup-only is the declared design; [config construction:15](../../apps/agents/monitoring/config.py#L15) reads per instance, not import. No hot-reload requirement is added. | AUD-026, AUD-033 |
| CHK045 | [ ] | [Range validators:47](../../apps/api/app/validators/signal_envelope.py#L47) reject out-of-range scores; tests lack a full exact 0/1/0.8 and penalty boundary matrix. | AUD-026, AUD-033 |
| CHK046 | [ ] | [Eviction:24](../../apps/agents/monitoring/dedup.py#L24) uses strict less-than, retaining equality; [test:29](../../tests/unit/test_monitoring_dedup.py#L29) only tests after expiry. | AUD-034, AUD-033 |
| CHK047 | [ ] | Local pipeline orders evaluation first at [process:389](../../apps/agents/monitoring/pipeline.py#L389); direct/MAF paths and full downstream assertions remain unsafe/incomplete. | AUD-002, AUD-029, AUD-033 |
| CHK048 | [ ] | [Association query:120](../../packages/domain/src/domain/repositories/signal_repository.py#L120) has no region scope; actual independent stores/failover isolation unproved. | AUD-025, AUD-033 |
| CHK049 | [ ] | [Builder:108](../../apps/agents/monitoring/agent.py#L108) checks only nonblank incident; closed-incident policy is unspecified. Initial-ingestion [closed test:105](../../tests/contract/test_incident_association.py#L105) is not a monitoring gate. | AUD-004, AUD-011, AUD-033 |
| CHK050 | [ ] | Prompt filtering denial is collapsed into generic failure at [agent:181](../../apps/agents/monitoring/agent.py#L181); exact safe/audit handling is untested. | AUD-007, AUD-027, AUD-033 |
| CHK051 | [ ] | Pipeline contract gives stage budgets; [early returns:383](../../apps/agents/monitoring/pipeline.py#L383) lack recorded full latency. Non-escalation measurement unverified. | AUD-013, AUD-021, AUD-031, AUD-033 |
| CHK052 | [ ] | [ACA resources:1139](../../infra/main.bicep#L1139) declare a budget but no load/cost ceiling measurement; document required capacity versus defaults. | AUD-023, AUD-031, AUD-033 |
| CHK053 | [ ] | HTTP contract requires service identity, but [associate:345](../../apps/agents/monitoring/agent.py#L345) has no authorization; private deployment/auth secrets policy is not proven by internal ingress. | AUD-004, AUD-023, AUD-024, AUD-033 |
| CHK054 | [ ] | [Global model SKU:72](../../infra/modules/azure-openai.bicep#L72) and [gateway:362](../../apps/agents/common/foundry_chat_client.py#L362) need explicit residency/config approval, not region-name inference. | AUD-025, AUD-027, AUD-033 |
| CHK055 | [ ] | No spec-010 RPO/RTO/failover evidence; plan replication and strict independence conflict. [Root primary:78](../../infra/main.bicep#L78). | AUD-025, AUD-033 |
| CHK056 | [ ] | No local availability target/evidence beyond health/continuation requirements; [health:274](../../apps/agents/monitoring/agent.py#L274) cannot prove uptime. | AUD-020, AUD-031, AUD-033 |
| CHK057 | [ ] | [Envelope:25](../../apps/api/app/validators/signal_envelope.py#L25), [domain Signal:7](../../packages/domain/src/domain/models/signal.py#L7), IoT and MAF use incompatible shapes without a versioned compatibility boundary. | AUD-001, AUD-010, AUD-026, AUD-033 |
| CHK058 | [ ] | [Generic logs:21](../../infra/modules/monitoring.bicep#L21) declare 90 days, but no monitoring sampling/retention/cost policy or deployed proof is established. | AUD-021, AUD-022, AUD-033 |
| CHK059 | [ ] | [Worker factory:208](../../apps/ingestion/worker.py#L208) omits repository/audit/association injection and [producer:56](../../apps/ingestion/pipelines/ga_earthquakes.py#L56) conflicts with escalation categories. | AUD-001, AUD-010, AUD-011, AUD-033 |
| CHK060 | [ ] | Research asserts Australian model availability; no quota/deployment proof was queried. Current [model declarations:29](../../infra/modules/azure-openai.bicep#L29) also differ from historical GPT-4o assumptions. | AUD-025, AUD-033 |
| CHK061 | [ ] | [Handoffs:1](../../apps/agents/common/handoffs.py#L1) is explicitly deprecated and [safety API:106](../../apps/agents/common/content_safety.py#L106) has evolved; compatibility must be tested, not assumed from filenames. | AUD-002, AUD-006, AUD-007, AUD-033 |
| CHK062 | [ ] | [Builder:114](../../apps/agents/monitoring/agent.py#L114) targets risk assessment for signal triage. Other recovery/warning paths are separately owned; no unilateral new recipient should be inferred. | AUD-002, AUD-033 |
| CHK063 | [ ] | [Ingestion trust defaults:18](../../apps/api/app/services/ingestion/pipeline_base.py#L18) exist upstream, but exact governance assignment enforcement in monitoring is not separately defined. Record responsibility, do not infer approval. | AUD-001, AUD-010, AUD-033 |
| CHK064 | [ ] | [TenantContext:6](../../apps/api/app/core/tenant_context.py#L6) exists elsewhere but is not consumed by monitoring ingress or association authorization. | AUD-003, AUD-004, AUD-005, AUD-033 |
| CHK065 | [ ] | [Held branch:240](../../apps/agents/monitoring/pipeline.py#L240) has no reviewer role/interface/SLA or release policy. | AUD-009, AUD-033 |
| CHK066 | [ ] | Current specification explicitly selects fail-closed, resolving the historical prose conflict; [builder:89](../../apps/agents/monitoring/agent.py#L89) still bypasses the check. | AUD-002, AUD-008, AUD-033 |
| CHK067 | [ ] | Current FR-028 requires both model filtering and ContentSafetyValidator; [RAI module:145](../../infra/modules/azure-openai.bicep#L145) exists but validation metadata and locale paths remain incomplete. | AUD-007, AUD-027, AUD-033 |
| CHK068 | [ ] | [Shared retry:139](../../apps/agents/common/handoffs.py#L139) counts total attempts; pipeline elapsed includes awaited delivery. Creation/retry SLA semantics need agreement. | AUD-006, AUD-013, AUD-033 |
| CHK069 | [ ] | [Audit scope:35](../../apps/agents/monitoring/pipeline.py#L35) includes tenant; [handoff scope:115](../../apps/agents/monitoring/agent.py#L115) uses incident alone. | AUD-003, AUD-018, AUD-033 |
| CHK070 | [ ] | Current spec and [effective gate:100](../../apps/agents/monitoring/agent.py#L100) resolve raw-confidence-only design; US1/SC-001/quickstart wording still needs reconciliation and missing-source effect is absent. | AUD-014, AUD-015, AUD-033 |
| CHK071 | [ ] | This report maps all 23 scenarios; original spec has story numbering but no FR-to-scenario trace matrix. [Spec:10](spec.md#L10). | AUD-033 |
| CHK072 | [ ] | [Plan gate table:37](plan.md#L37) is authored traceability to an older principle numbering, not execution proof under the [current constitution](../../.specify/memory/constitution.md#L1). | AUD-033 |
| CHK073 | [ ] | [Data model](data-model.md) consolidates twelve parameters, but later LLM settings, output limits, alerts, and applied invariants diverge. | AUD-021, AUD-026, AUD-033 |
| CHK074 | [ ] | [Spec:5](spec.md#L5) remains Draft; checked tasks/plan PASS labels are not approved delivery or SME sign-off. | AUD-033 |

### Twenty Constitution-Gate Claims

All twenty plan rows claim PASS and the post-design paragraph claims a second pass. Those authored claims
are **UNVERIFIED as reviews/executions**. Their static support is assessed individually below. This is not a
re-grading of the constitution or the AMA rubric, and it does not inherit another report's conclusions.

| Plan gate | Static support / limitation | Follow-up |
| --- | --- | --- |
| 1: Life-safety escalation / fail-closed | [Gate:100](../../apps/agents/monitoring/agent.py#L100) exists; alternate bypass and no 5-second proof. | AUD-002, AUD-013, AUD-031 |
| 2: Human override / hold | [Hold:240](../../apps/agents/monitoring/pipeline.py#L240) is a record, not durable review or override workflow. | AUD-009 |
| 3: Explanations | [Records:59](../../apps/agents/monitoring/models.py#L59) have fields; evaluated inputs, exact outputs, and complete decisions absent. | AUD-018, AUD-026 |
| 4: Safe low-confidence/stale fallback | Effective multiplication exists, fallback annotation and missing-source effect do not. [Agent:100](../../apps/agents/monitoring/agent.py#L100). | AUD-014, AUD-015 |
| 5: Explicit handoffs | [Event:26](../../apps/agents/common/handoffs.py#L26) has confidence/time; persistence/scope/delivery wiring absent. | AUD-003, AUD-006 |
| 6: No silent state changes | [Association:207](../../apps/agents/monitoring/agent.py#L207) logs rather than per-signal audit; other paths omit decisions. | AUD-018, AUD-019 |
| 7: AIIMS / recommendation boundary | Monitoring targets risk rather than external action, but [MAF workflow:89](../../apps/agents/maf_runtime/workflow/builder.py#L89) advances irrespective of gate; operational approval unverified. | AUD-002, AUD-033 |
| 8: Provenance | [T067 assertion:293](../../tests/unit/test_monitoring_pipeline.py#L293) does not verify actual metadata retention. | AUD-018 |
| 9: Authoritative preference | Category/source fields exist; [GA normalization:56](../../apps/ingestion/pipelines/ga_earthquakes.py#L56) changes hazard category and substituted-source labeling needs clarity. | AUD-010 |
| 10: Freshness | [Tracker:104](../../apps/agents/monitoring/freshness.py#L104) is not scheduled or tenant-isolated. | AUD-003, AUD-015 |
| 11: Misinformation | [Parser:163](../../apps/agents/monitoring/agent.py#L163) is permissive; builder/MAF bypass. | AUD-002, AUD-008, AUD-032 |
| 12: Data minimization | [LLM summary:79](../../apps/agents/monitoring/agent.py#L79) is not limited to structured fields. | AUD-007 |
| 13: AU residency | [GlobalStandard:72](../../infra/modules/azure-openai.bicep#L72) and unknown-region gateway behavior require evidence/policy resolution. | AUD-025 |
| 14: Tenant isolation | [process_signal:366](../../apps/agents/monitoring/pipeline.py#L366) trusts default-live/out-of-band scope and uses shared caches. | AUD-003, AUD-005, AUD-034 |
| 15: Prompt injection | [Mock test:208](../../tests/contract/test_monitoring_escalation.py#L208) is not a real boundary/resistance test. | AUD-027, AUD-032 |
| 16: Content safety | [Validator call:77](../../apps/agents/monitoring/agent.py#L77) omits locale and ignores review metadata. | AUD-007 |
| 17: Azure / regional hosting | Azure templates exist; orphan monitoring module and absent independent DR leave delivery unverified. [Root:1109](../../infra/main.bicep#L1109). | AUD-023, AUD-025 |
| 18: Partial-outage resilience | [Spill:85](../../apps/agents/monitoring/audit.py#L85) can fail silently and source/model paths can block. | AUD-013, AUD-015, AUD-016 |
| 19: Append-only audit | [create_item:73](../../apps/agents/monitoring/audit.py#L73) supports intent, not no-loss or enforced immutability/deployed retention. | AUD-016, AUD-017, AUD-024 |
| 20: WAF observability/scaling/security | [Counters:426](../../apps/agents/monitoring/pipeline.py#L426) are not exported metrics; queue scaling and endpoint auth absent. | AUD-004, AUD-021, AUD-022, AUD-023 |

### Conflicts Requiring Explicit Decisions

1. FR-003/US3 prohibit unprocessed narrative propagation, whereas stage 5/plan request LLM-enriched summaries.
   Define the approved output schema rather than claiming both interpretations are delivered.
2. FR-009 uses effective confidence, while US1/SC-001 and the quickstart sometimes describe raw confidence.
   FR-024's threshold-only fallback and FR-023's missing-source adjustment also require one unambiguous formula.
3. FR-020 demands receipt/all decisions, but the nine-value enum omits receipt/negative triage types; the handoff
   error table suggests updating status while audit events are append-only. Event append and mutable delivery
   state must be distinguished.
4. Three retries versus three total attempts, and creation versus delivered-handoff timing, need one authoritative
   definition. The source must not silently decide the business SLA.
5. FR-025's reachable-LLM health and the contract's unhealthy-on-unreachable table conflict with FR-024's continuing
   rule-based operation. Separate readiness/liveness and allowed degraded processing.
6. NFR-004 independent regions conflicts with the plan's replicated Cosmos design and historical regional-model
   assumptions. The later constitutional hosting carve-out is bounded and does not automatically resolve it.
7. Research assumes permanent Service Bus process affinity and 16 unassociated hash buckets; implementation
   provides neither durable affinity nor that bucket function. Queue scaling values also differ (task 100/root comment 50).
8. Data model/input assumptions delegate normalization, while boundary-validation tasks intentionally add defensive
   checks. Preserve that defense explicitly and reconcile domain hazard/status schemas instead of rejecting needed states.
9. The telemetry stage/alerts name two instruments outside the thirteen-item table. Choose their schema and
   source; do not count undocumented generic SDK metrics as substitutes.
10. Original task and local review PASS claims do not prove execution; stale fail-open checklist wording should
    be updated through change control, without modifying historical evidence to manufacture approval.

## Future Validation Catalogue

**None of the following product commands were executed in this audit.** These are instructions for later
authorized remediation. Run from repository root, not the quickstart's nested agent directory. Do not execute
a proposed test path until its owning task creates it. Never substitute a zero-tests/skip-only result for PASS.

### Prerequisites

| ID | Required before future execution |
| --- | --- |
| P-PY | Approved Python 3.12+ environment with API/agent/domain dependencies and pytest/pytest-asyncio installed; [tests/conftest.py:10](../../tests/conftest.py#L10) supplies root/API/agent import paths. Isolate ambient cloud credentials and use controlled clocks/temporary storage for unit tests. No installs were done here. |
| P-COSMOS | Explicit emulator or disposable test account/database/container with `/incident_scope_key`, no TTL, correct SDK mode, private credential injection, cleanup ownership, and production-target refusal. Managed-identity permission tests require a separately authorized test identity, not an emulator claim. |
| P-BROKER | Disposable session-capable Service Bus environment, real producer/receiver/worker wiring, trusted tenant/session/correlation metadata, lock/restart control, durable test stores, and production-queue refusal. |
| P-IDENTITY | Approved test token verifier/identity, audience/issuer/role rules, incident-to-tenant ownership fixtures, and both permitted and denied principals. No tokens or secrets in test output/report. |
| P-IAC | Approved later IaC change, Bicep tooling, dependency/module restore, current governance constraints, AVM discovery and any exception approval, explicit supported roots/environment values. Live what-if/deployment requires separate authorization; no policy discovery/build occurred here. |
| P-OBS | Authorized disposable telemetry workspace/action group with approved destinations, known sampling/retention, captured metric/event schema, and notification recipients who consent to the exercise. |
| P-PERF | Representative hardware, worker count, unique workload/arrival schedule, measured external-dependency profile, agreed SLA boundaries, loss reconciler, and output location outside original evidence. No background traffic to production. |
| P-MODEL | Approved model deployment and data-minimization/filter configuration, pinned model/prompt versions, rate/budget cap, inference authorization, and explicit test-only output retention. |
| P-DATA | Licensed/de-identified labeled social corpus, adjudication and sample-size method, operator/safety review, and no real personal material in published output. |
| P-REGION | Authorized paired isolated test deployments, clear independence/replication decision, region-bound stores/queues/model policy, and approved failover exercise/RPO/RTO. |
| P-REVIEW | Named specification/operations/security owners, independent reviewer, version-bound execution and sign-off records, and preservation of deferred country preconditions. |

### Commands and Expected Assertions

| ID | FUTURE command | Expected result / ownership |
| --- | --- | --- |
| F-MODELS | `python -m pytest tests/unit/test_monitoring_models.py -q` | All original setting bindings and accepted/rejected model invariants asserted; AUD-026. |
| F-PIPELINE | `python -m pytest tests/unit/test_monitoring_pipeline.py -q` | Real stage ordering, all terminal outcomes, one summary, exact audit/provenance and scoped effects; not counters alone. |
| F-MISINFO | `python -m pytest tests/contract/test_monitoring_escalation.py tests/contract/test_misinformation_detector.py -q` | Strict parser, every evaluator outcome, no-handoff/hold persistence, genuine Tier-2 extensions; AUD-002/AUD-008/AUD-009. |
| F-SAFETY | `python -m pytest tests/contract/test_monitoring_escalation.py tests/unit/test_monitoring_pipeline.py -q -k "safety or injection or summar"` | Actual output and system/user boundary assertions for safe/fallback/refusal paths; model attack resistance requires P-MODEL evaluation too. |
| F-FRESH | `python -m pytest tests/unit/test_monitoring_dedup.py tests/unit/test_monitoring_freshness.py -q` | Controlled-clock transition/TTL edges, no cross-scope influence; scale/restart proof additionally needs F-SB. |
| F-AUDIT | `python -m pytest tests/unit/test_monitoring_audit.py -q` | Exact documents/order/backlog/metadata under disk, Cosmos, replay, and restart failures. |
| F-ASSOC | `python -m pytest tests/contract/test_incident_association.py tests/contract/test_signal_storage.py -q` | Agent-to-real-repository interface, tenant/geometry/cutoff/CAS correctness, auth and per-signal audit extensions. |
| F-HEALTH | `python -m pytest tests/contract/test_monitoring_escalation.py -q -k health` | Actual schema/value/status matrix, real dependency adapters, bounded cached check timing; deployed probe exercise separate. |
| F-HANDOFF | `python -m pytest tests/integration/test_handoff_retry.py tests/integration/test_handoff_chain.py -q` | Monitoring delivery adapter, durable event/DLQ, real visibility and scoped retry/idempotency assertions, not a local no-op. |
| F-INGEST | `python -m pytest tests/contract/test_geojson_normaliser.py tests/contract/test_signal_storage.py tests/unit/test_monitoring_pipeline.py -q` | Producer-to-store-to-monitoring categories, provenance, and null incident preserved; assertions added under AUD-010/AUD-011. |
| F-MAF | `python -m pytest tests/equivalence/test_monitoring_equivalence.py tests/integration/test_workflow_crash_recovery.py -q` | Added actual runtime/gate assertions across flag modes; static fixture equivalence alone must not establish conformance. |
| F-TELEMETRY | `python -m pytest tests/unit/test_monitoring_pipeline.py tests/unit/test_monitoring_audit.py tests/contract/test_monitoring_escalation.py -q` | Captured 13+resolved supplemental instruments, eight events, dimensions and parent-child trace assertions; no exporter network needed for unit proof. |
| F-COSMOS | `python -m pytest tests/integration/test_monitoring_cosmos_audit.py -q` | **Proposed path**, created by AUD-028; non-mock write/read-back/partition/replay/retention assertions under P-COSMOS. |
| F-SB | `python -m pytest tests/integration/test_monitoring_service_bus.py -q` | **Proposed path**, created by AUD-029; real broker intake and authorized association count/update/audit proof. |
| F-SCENARIO | `python -m pytest tests/simulation/test_bushfire_scenario.py -q` | Extended scenario invokes the complete monitoring chain and checks safety/tenancy/audit, not only the generator. |
| F-LOAD | `python -m pytest tests/simulation/test_monitoring_load.py -q` | **Proposed path**, created by AUD-031; >=5,000 unique signals over >=5 minutes, required SLA/outage/health/association/loss metrics. |
| F-EVAL | `python -m pytest tests/contract/test_monitoring_credibility_evaluation.py -q` | **Proposed path**, created by AUD-032; labeled model evaluation with explicit denominator/confusion matrix, <5% false positives, no empty/skip-only PASS. |
| F-IAC | `bicep build infra/main.bicep --stdout` and `bicep build infra/bicep/main.bicep --stdout` | Later compilation only after P-IAC; inspect compiled reachability, scaling, role, key/TTL and region assertions. Compilation alone is not deployment or policy proof. |
| F-DOC | Read-only task/requirement/link reconciliation plus corrected quickstart verification under the applicable prerequisites | AUD-033: every claimed result links to command/revision/time/output or remains UNVERIFIED; original evidence is not rewritten to simulate execution. |

The inspected [CI test step](../../.github/workflows/ci.yml#L142) runs contract/integration tests, not the
monitoring unit/simulation suites, while its benchmark step does not repair the repeated-ID problem. As part of
the relevant future test tasks, make monitoring unit/contract/scenario gates explicit and use opt-in lanes for
broker/emulator/load/model exercises. A configured CI step is not evidence it ran successfully at this revision.

## Review Closure and Limits

This is a complete static inventory and remediation plan, not a safety certification or a claim that the
application currently works. Measured SC outcomes, cloud configuration/permissions, region isolation,
notification receipt, human review/sign-off, model accuracy, and actual test execution remain UNVERIFIED.
No percentage of runtime completeness is inferred from checked tasks or source-file counts.

Immediate report-only validation must check: one coverage row per original task with the original checkbox,
one row per FR/NFR/SC, all 23 scenario labels, all six edge cases, all amendment and CHK identifiers, 34 unique
unchecked AUD tasks with resolvable follow-up IDs, existing relative link targets and valid source line anchors,
editor diagnostics, and a final newline. These checks validate this document only; they do not execute any
future command above or close any remediation.

Public semantic references consulted, without accessing Azure resources:
[Service Bus session ownership/state](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
[Python 3.12 asyncio timeout/thread behavior](https://docs.python.org/3.12/library/asyncio-task.html), and
[running future cancellation](https://docs.python.org/3.12/library/concurrent.futures.html).
The authoritative acceptance contract for this review remains the local specification and its explicit amendments.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 010 only. Three parallel technical reviews examined worker
composition/triage safety, tenant and runtime integration, and observability/evidence. The existing monitoring logic
was not broadly rewritten because the controlling unresolved defect is architectural: the deployed dispatcher does
not subscribe to normalized signals or invoke the six-stage monitoring pipeline, and the MAF path can bypass those
gates. The focused source behavior itself is covered by the existing tests.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| Monitoring triage/escalation | Source-level behavior passes focused tests. | `python -m pytest tests/unit/test_monitoring_pipeline.py tests/contract/test_monitoring_escalation.py -q` returned `40 passed` with two dependency deprecation warnings. |
| AUD-001 / AUD-002 / AUD-003 | Production integration remains open. | `azure.yaml`/Docker launch the dispatcher, not the monitoring worker; normalized ingestion is not connected to the monitoring pipeline, and alternate MAF paths can bypass triage/tenant gates. A supported broker/runtime composition decision is required before implementation. |
| AUD-004–AUD-034 | Partial or evidence-gated. | Association, durable broker/DLQ, freshness scheduling, append-only audit, monitoring-specific alerts, infrastructure wiring, load, misinformation accuracy, and live/SME evidence remain open or unverified. |

The attempted equivalence command referenced a nonexistent path, `tests/integration/test_monitoring_equivalence.py`,
so no result is claimed for it. No product runtime, deployment, broker, cloud, human, or performance evidence was
created in this pass.

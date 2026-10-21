# Implementation Audit: 003 Rubric Gap Closure

## Scope and Limitations

- Review date: **2026-09-11**. Source revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**.
- Review-only, standalone static audit under the [Review Contract](../001-spec-implementation-audit/README.md#L10).
  Tracked implementation content was compared with the supplied revision; the comparison showed no source drift.
  Other implementation-review reports and the central audit inventory were not used as implementation evidence.
- Only this report was authored. Original tasks, source, configuration, evidence, and the central index are unchanged.
  No application imports, tests, builds, installations, servers, cloud operations, commits, branches, or delegation
  were performed. Commands below are **future instructions**, not executed remediation.
- Coverage: **53/53 original tasks**, **30/30 FRs**, **13/13 SCs**, **27/27 acceptance scenarios**, all **10 edge cases**,
  and the appended ASM/PER/HYP/SCP items. The spec defines **no numbered NFRs**; its nonfunctional constraints are
  separately accounted for below. Coverage is not a completion percentage.
- All eight feature-local artifacts were read in full: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md),
  [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md),
  [contracts/openapi-addendum.yaml](contracts/openapi-addendum.yaml), and
  [checklists/requirements.md](checklists/requirements.md). T051, T052, T053 and the spec's later governance sections
  are included, not treated as optional amendments.
- Guidance applied: [constitution](../../.specify/memory/constitution.md),
  [review priorities](../../.github/instructions/code-review.instructions.md),
  [review checklist](../../.github/instructions/references/code-review-checklists.md),
  [Bicep guidance](../../.github/instructions/bicep-code-best-practices.instructions.md), and
  [policy guidance](../../.github/instructions/bicep-policy-compliance.instructions.md).
- Historical execution evidence examined: [March rehearsal record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L7),
  [live runbook](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md#L1), their actual test bodies,
  and the associated demo/KPI instruments. Authored PASS prose is not a current run artifact or human sign-off.
- The separately reviewed [004 artifact directory](../004-rubric-gap-closure/) is **not presumed to supersede 003**.
  Its review conclusions were not consumed. Actual replacements were traced where source names them: the
  [legacy handoff deprecation](../../apps/agents/common/handoffs.py#L1),
  [MAF workflow implementation](../../apps/agents/maf_runtime/workflow/builder.py#L63),
  [Foundry migration decision](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L30),
  [current LLM configuration](../../apps/agents/common/llm_config.py#L1), and
  [azd infrastructure selection](../../azure.yaml#L8). A renamed mechanism does not retire its behavioral obligations.
- Source inspection establishes reachable logic and assertion strength, not live latency, reliability, CI duration,
  deployed permissions, notification delivery, human comprehension, or a rubric score. No new rubric grading was
  performed. The later presentation was inspected as ZIP/XML only, not rendered or accepted by a human.
- Negative findings are scoped to the named paths and tracked-source searches described below. Existing package
  versions were not installed or security-scanned. Public package documentation corroborated benchmark semantics;
  it was not used as evidence that this repository passes a check.

## Evidence Statuses

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Inspected source fully supports the scoped behavior or authored artifact; execution is not implied. |
| PARTIAL | Some implementation exists, but a named obligation or meaningful assertion is missing. |
| MISSING | Required behavior/artifact absent after the stated replacement search. |
| CONFLICT | Source, requirements, or instructions disagree and need an explicit resolution. |
| UNVERIFIED | Static evidence cannot establish an execution, measurement, deployment, or human approval claim. |
| SUPERSEDED | Explicit source documents replacement of the specific mechanism, not blanket retirement of this spec. |

## Connected-Path Findings

These are shared-code findings independently relevant to this spec. Each row links to an unchecked task below.
P1 means a security, safety, data-loss, or materially broken acceptance path; P2 means an important delivery or
verification gap. Findings are ordered by impact, not by original checkbox state.

| Priority | Finding and concrete evidence | Follow-up |
| --- | --- | --- |
| P1 | Dead-letter list/resolve and handoff reads ignore caller tenant; resolution trusts a body-supplied persona. [Global query](../../apps/api/app/services/dead_letter_service.py#L41), [route](../../apps/api/app/api/dead_letters.py#L20), [RBAC scope](../../apps/api/app/middleware/rbac_check.py#L32). | AUD-001 |
| P1 | Publishing accepts `pending_approval`; approving a recommendation creates an already-approved English-only alert without drafting/content review. [Publish predicate](../../apps/api/app/services/public_alert_service.py#L48), [approval mutation](../../apps/api/app/services/recommendation_service.py#L29). | AUD-002 |
| P1 | `POST /api/signals` stores data but starts no Monitoring-to-Risk-to-Communication chain. No production `EventBus()` construction was found in the tracked API/agents/ingestion search. [Entrypoint](../../apps/api/app/api/routes/signals.py#L12), [store-only implementation](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12). | AUD-003 |
| P1 | Monitoring handoffs omit the real signal identifier; Risk can invent a `synth-*` signal and append citations after generation. Prompts do not supply the original incident evidence in the compatibility path. [Handoff](../../apps/agents/monitoring/agent.py#L112), [retrieval fallback](../../apps/agents/risk_assessment/pipeline.py#L169), [recommendation](../../apps/agents/risk_assessment/agent.py#L408). | AUD-004 |
| P1 | Retry helper does not consult target circuit state, enforce an elapsed 300-second deadline, or own idempotent delivery. Pipeline defaults fabricate a dead-letter ID. [Retry](../../apps/agents/common/handoffs.py#L124), [callback defaults](../../apps/agents/monitoring/pipeline.py#L64). | AUD-005, AUD-006 |
| P1 | Storage/cache retry is an unused RuntimeError decorator; permanent ingestion failures do not flow to the feature DLQ. Multiple disconnected memory stores cannot provide durable operator recovery. [Retry definition](../../apps/api/app/middleware/resilience.py#L82), [feature store](../../apps/api/app/services/state_store.py#L23), [second API store](../../apps/api/app/api/routes/dead_letters.py#L15). | AUD-006 |
| P1 | Error handlers reflect HTTP/permission exception text and generate IDs independently of response middleware; route-less 404/405 and newer envelopes do not uniformly satisfy ErrorResponse. [Handlers](../../apps/api/app/middleware/error_handler.py#L147), [header generation](../../apps/api/app/middleware/resilience.py#L60). | AUD-007 |
| P1 | Arabic, Vietnamese, Greek, and Italian checks accept any nonempty text; Azure safety success skips language validation; a previously safety-fallback block can later be relabelled `passed`. [Language checks](../../apps/agents/common/content_safety.py#L95), [early return](../../apps/agents/common/content_safety.py#L118), [second safety pass](../../apps/agents/communication/pipeline.py#L375). | AUD-008 |
| P1 | The spec's Bicep entrypoint accepts arbitrary regions and leaves API/agent dependency bindings incomplete; the newer root template does not fix all identity/network obligations. [Legacy location](../../infra/bicep/main.bicep#L3), [current registry credentials](../../infra/main.bicep#L1020), [azd selection](../../azure.yaml#L8). | AUD-020 |
| P2 | Token overage is trimmed to 80% of characters, not to the token limit; input budgets and final appended citations are not checked. [Trimming](../../apps/agents/common/llm_mixin.py#L125), [test](../../tests/contract/test_token_budget.py#L4). | AUD-009 |
| P2 | Foundry `timeout_s` is unused at the SDK call; six sequential translations plus back-translations have no whole-draft deadline. [SDK call](../../apps/agents/common/foundry_chat_client.py#L397), [translation loop](../../apps/agents/communication/translator.py#L38). | AUD-010 |
| P2 | Incoming request ID is not propagated through agents/Foundry; deployment metadata falls back to a model key; the logging test logs its own expected text. [Wrapper](../../apps/agents/common/llm_client.py#L176), [test-owned log](../../tests/contract/test_llm_logging.py#L9). | AUD-011 |
| P2 | Domain models omit required bounds/state transitions, and runtime snake_case responses do not match camelCase published contracts. [Models](../../packages/domain/src/domain/models/model_deployment.py#L6), [wire contract](../../packages/schemas/openapi.yaml#L243), [runtime resolve](../../apps/api/app/api/dead_letters.py#L10). | AUD-012, AUD-013 |
| P2 | CI omits simulation/unit suites from the general gate, excludes feature-branch pushes, and provides no ten-minute bound on the principal quality job. [Triggers](../../.github/workflows/ci.yml#L3), [test command](../../.github/workflows/ci.yml#L131). | AUD-014 |
| P2 | CI benchmark suppresses comparison failure when `CI` is set; measurements are sequential agent-health medians, not the required concurrent dashboard/read p95. [Hook](../../tests/benchmark/conftest.py#L85), [benchmark](../../tests/benchmark/test_api_performance.py#L16). | AUD-015 |
| P2 | Load report treats absolute Failure Count as throughput, merges endpoint p95 values, and returns passing zeros for empty input. [Report](../../tests/load/report.py#L11). | AUD-016 |
| P2 | Dashboard load calls health; nightly job suppresses pytest failures instead of invoking the 1,000-operator Locust workload. Other load workflows target different scenarios. [User](../../tests/load/locustfile.py#L19), [nightly](../../.github/workflows/nightly-load.yml#L44). | AUD-017 |
| P2 | Docker dependency layers include source before installation; quickstart uses the wrong build context; API image omits the MAF package its workflow routes lazily import. [Dockerfile](../../apps/api/Dockerfile#L3), [lazy import](../../apps/api/app/api/routes/workflow_runs.py#L65), [instructions](quickstart.md#L61). | AUD-018 |
| P2 | Health reports configured endpoints as healthy without contacting them; its degraded branch cannot be reached through `_dependency_status`. [Health](../../apps/api/app/api/health.py#L10). | AUD-019 |
| P2 | The purported p99 rule aggregates Maximum; defaults send alerts to example destinations and no receiver delivery evidence is supplied. [Rule](../../infra/bicep/monitoring.bicep#L117), [targets](../../infra/bicep/monitoring.bicep#L10). | AUD-021 |
| P2 | Demo screen references are placeholders, the timing budget sums to exactly 300 seconds, and KPI cells are targets rather than a paired measured result. [Walkthrough](../../docs/disaster-response-hub/demo/walkthrough.md#L3), [timing](../../docs/disaster-response-hub/demo/walkthrough.md#L43), [deck](../../docs/disaster-response-hub/demo/executive-deck.md#L17). | AUD-022 |
| P2 | Checked completion claims exceed their evidence: historical PASS prose has no linked raw reports; current live rehearsal asserts only Risk and still gates on legacy configuration. [Record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L7), [live test](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L6). | AUD-023, AUD-024 |
| P2 | Design/checklist claims are inconsistent: retries versus attempts; three handoffs for a two-edge chain; stronger execution claims than their tests; unsubstantiated persona/hypothesis validation. [Quickstart](quickstart.md#L98), [checklist](checklists/requirements.md#L19), [amendments](spec.md#L259). | AUD-025 |
| P2 | Handoff API records omit confidence/payload/linkage, failures are not inserted into the list, and the operator dashboard does not consume the feature handoff ledger. [Recorder](../../apps/api/app/services/event_bus.py#L46), [reader](../../apps/api/app/api/handoffs.py#L7), [dashboard](../../apps/api/app/services/dashboard_service.py#L48). | AUD-026 |

### Replacement and Absence Search

The audit followed route registration into handlers, stores, agent pipelines, delivery helpers, and test assertion
bodies. Searches covered tracked API, agents, ingestion, ingest-runner, web, tests, workflows, and relevant docs for
`EventBus`, `deliver_handoff_with_retry`, handoff builders, `HANDOFF_EVENTS`, `TIMELINE_EVENTS`,
`retry_transient_dependency_call`, `DeadLetterService`, `generate_report`, and the original feature identifier.

- [MAF workflow](../../apps/agents/maf_runtime/workflow/builder.py#L92) explicitly drives steps and checkpoints, but
  the signal POST does not invoke it. Its [communication legacy branch](../../apps/agents/maf_runtime/agents/communication_agent.py#L32)
  constructs an empty alert. Its [API audit reader](../../apps/api/app/api/routes/workflow_runs.py#L156) returns an
  empty list. These are not evidence of the 003 end-to-end chain or timeline contract.
- The shipped [dispatcher](../../apps/agents/dispatcher/agent.py#L205) answers individual simulation questions;
  its communication response is not a six-language PublicAlert and it does not consume the feature event bus.
- [CommunicationProcessingPipeline](../../apps/agents/communication/pipeline.py#L93) and
  [MultilingualTranslator](../../apps/agents/communication/translator.py#L25) are real renamed/expanded implementation,
  so absence of a class named `CommunicationAgent` is not itself a missing-implementation finding.
- The second [dead-letter API](../../apps/api/app/api/routes/dead_letters.py#L15) uses a separate dictionary;
  [its registration follows the feature router](../../apps/api/app/api/router.py#L75), while both declare the same GET
  path. The [later DLQ tests](../../tests/unit/test_dead_letter_lifecycle.py#L15) exercise yet another store interface,
  not the feature API's tenant protection or automatic routing.
- [Simulation load assertions](../../tests/load/assert_locust_thresholds.py#L19) target `inject-telemetry` at 5 seconds;
  [workflow capacity](../../tests/load/test_workflow_capacity.py#L90) uses five in-memory runs;
  [map overlay tests](../../tests/load/test_sc010_map_overlay_slo.py#L80) read synthetic timings. None replaces the
  dashboard/read/50,000-successful-signals-per-hour measurement.
- The [newer live demo runbook](../../docs/ama-presentation/AMA_Live_Demo_Instructions.md#L1) and
  [61-slide presentation](../../docs/ama-presentation/AMA_Capstone_Disaster_Response_Hub.pptx) were checked as candidate
  replacements. ZIP inspection found 36 media entries, so this report does not claim that the repository has no deck
  or images. No explicit 003 replacement mapping, current screen-by-screen acceptance, or paired measured KPI pack
  was established. A projected rubric self-assessment is not an evaluator result.
- No linked raw March pytest/Playwright logs, feature-specific successful live rehearsal, or the referenced
  `HYP-HYP-001.md` evidence stub was found in the associated evaluation/evidence scope. That filename is a
  **missing referenced artifact**, not an existing link. No wider claim of repository-wide absence is made.

## Open Remediation Tasks

All 26 tasks below are **unchecked and unexecuted**. They are instructions for separately authorised developers
and testers. Future command references V01-V10 are defined after the coverage tables. Existing test locations are
reused; any new fixture, screenshot, report, or approval record is explicitly described as proposed.

Dependency references denote integration/co-validation dependencies, including mutually coupled changes; they are
not an acyclic implementation schedule. Resolve AUD-025 contract decisions first. Establish model/API/tenant
boundaries (AUD-012, AUD-013, AUD-001), then coordinate delivery/storage/safety/observability repairs before closing
the end-to-end chain (AUD-003, AUD-026). CI, load, container, and infrastructure work can be prepared independently
but must validate the repaired runtime. Demo/live-rehearsal acceptance follows those repairs; AUD-023 is the final
evidence gate, not a prerequisite that would create a circular completion dependency.

### AUD-001: Enforce Tenant and Operator Boundaries

- [X] **AUD-001 (P1)**. Affects T003, T005, T029, T042; FR-013, FR-025; US3-AS3, US7-AS4;
  [tenant-scoped contract](contracts/openapi-addendum.yaml#L21).
- **Expected versus observed:** list and resolve are caller-scoped; instead
  [query_entries](../../apps/api/app/services/dead_letter_service.py#L41) scans all records and
  [resolve_entry](../../apps/api/app/services/dead_letter_service.py#L61) accepts any known ID and claimed persona.
  [Handoff reads](../../apps/api/app/api/handoffs.py#L7) likewise ignore tenant. Middleware creates a context but the
  [RBAC protected prefixes](../../apps/api/app/middleware/rbac_check.py#L32) do not include these paths.
- **Impact:** cross-tenant incident payload disclosure and unauthorised mutation of recovery evidence.
- **Developer instructions:** require authenticated operational permissions, derive persona from verified claims,
  enforce tenant plus incident ownership in repository reads and mutations, and make pagination totals tenant-local.
  Do not trust query/body tenant or persona identifiers. Preserve management-route compatibility through AUD-013.
- **Tester instructions:** extend [test_dead_letter_api.py](../../tests/contract/test_dead_letter_api.py#L24) using
  TestClient and the feature service; create proposed tenant-A/tenant-B fixtures in that existing file. Positive:
  own-tenant list/resolve; negative: foreign ID, forged persona, anonymous request; edge: identical incident IDs in
  separate tenants, filtered total/offset, already-resolved item. Assert no foreign payload or counts leak.
- **Dependencies / future checks:** AUD-012 and AUD-013 for schema/storage agreement; V01, V04.
- **Acceptance:** every list/get/resolve enforces caller-derived scope before data access; denied requests cause no
  mutation and return the documented safe status. Deployed authentication remains a separate V09 evidence gate.

### AUD-002: Restore Alert-Specific Human Approval

- [X] **AUD-002 (P1)**. Affects T014, T039, T049, T050; FR-002, FR-006; US1-AS2, US6-AS1;
  Constitution NON-NEGOTIABLE #1 and public-output review gate.
- **Expected versus observed:** reviewed safe multilingual content is approved before publication;
  [record_approval](../../apps/api/app/services/recommendation_service.py#L29) creates an approved English-only alert,
  and [publishability](../../apps/api/app/services/public_alert_service.py#L48) allows `pending_approval`.
  The [publish route](../../apps/api/app/api/routes/alerts.py#L35) adds no alert-version approval check.
- **Impact:** the authoritative API can mark unreviewed content published; integration with a real channel would
  carry that invalid authorisation forward. This is a static state-transition finding, not a claim that a live
  notification was sent during the audit.
- **Developer instructions:** keep recommendation approval distinct from approval of an immutable alert version;
  draft through the real communication pipeline, retain safety/generation metadata, and require verified approver
  authority for the exact version before publish/deliver. Do not bypass the human gate to satisfy automatic chaining.
- **Tester instructions:** extend [test_quickstart_rehearsals.py](../../tests/simulation/test_quickstart_rehearsals.py#L20)
  and [test_communication_llm.py](../../tests/contract/test_communication_llm.py#L4). Positive: review then publish the
  six-language version; negative: pending approval, unsafe draft, forged approver; edge: edit after approval,
  duplicate publish, concurrent approval, simulation delivery suppression. Assert no publication without a matching
  recorded decision and no automatic upgrade from recommendation approval to alert approval.
- **Dependencies / future checks:** AUD-001, AUD-003, AUD-008, AUD-013; V01, V02, V04.
- **Acceptance:** pending/unreviewed/stale-approved content is rejected; an authorised reviewed version alone can
  transition to published, with traceable approver and content version.

### AUD-003: Connect the Automatic Incident Chain

- [X] **AUD-003 (P1)**. Affects T006, T013, T014, T025, T026, T030, T033, T050; FR-001, FR-002,
  FR-011, FR-012; SC-005.
- **Expected versus observed:** a high-risk accepted signal automatically generates/stores a recommendation and
  draft. [Signal ingestion](../../apps/api/app/api/routes/signals.py#L12) calls a
  [store-only service](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12). Legacy pipelines require
  injected delivery functions, and the MAF runner is not called by that route. The original
  [chain test](../../tests/integration/test_handoff_chain.py#L5) dispatches to a function that returns `None`.
- **Impact:** checked orchestration tasks do not provide the central live-incident user journey.
- **Developer instructions:** select the documented active orchestration owner, connect the real ingestion
  entrypoint to tenant-scoped typed dispatch, wire Risk and Communication consumers, and persist outputs into the
  repositories used by API readers. Acknowledge delivery only after required persistence; do not silently swallow
  assessment/recommendation/alert write failures. Preserve explicit human publication approval.
- **Tester instructions:** rewrite the existing chain test to POST a validated signal, use real agent/pipeline
  bodies with only model/network boundaries faked, and fetch resulting recommendations, drafts, and handoffs.
  Positive: both automatic edges; negative: low-risk input and rejected delivery; edge: two tenants, duplicate
  signal, persistence failure after model success. Assert payload lineage and no direct test seeding of outputs.
- **Dependencies / future checks:** AUD-001, AUD-004, AUD-005, AUD-006, AUD-026; V01, V02.
- **Acceptance:** the publicly supported entrypoint reaches both real consumers and API-visible stored outputs
  without a manual runner call; SC-005 timing requires the separate V09 rehearsal evidence.

### AUD-004: Ground Risk Explanations in Real Signal Evidence

- [X] **AUD-004 (P1)**. Affects T013, T015, T025, T030; FR-001; SC-001; US1-AS1.
- **Expected versus observed:** explanations use incident signal context and true source IDs;
  [Monitoring's payload](../../apps/agents/monitoring/agent.py#L112) supplies neither the ingested ID nor its full
  evidence. [Risk retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) can synthesize a signal when IDs are
  absent; [recommend_public_alert](../../apps/agents/risk_assessment/agent.py#L408) sends IDs alone and appends a
  reference after generation. [T015's test](../../tests/contract/test_risk_assessment_llm.py#L4) accepts fallback.
- **Impact:** a cited-looking explanation can lack grounded reasoning or cite an invented signal identifier.
- **Developer instructions:** propagate stored signal IDs, retrieve authorised source content/provenance/freshness,
  include a bounded evidence snapshot in the model request, and validate returned citations against that snapshot.
  Distinguish deterministic appended references from model-generated citations and label missing evidence explicitly.
- **Tester instructions:** use [test_risk_assessment_llm.py](../../tests/contract/test_risk_assessment_llm.py#L4) and
  the existing chain test. Positive: mocked model receives specific evidence and returns `llm` plus valid citations;
  negative: fabricated citation, template-only completion, missing source; edge: contradictory/community/stale signals,
  empty list, duplicate IDs. Assert actual prompt content and citation membership, not substring presence alone.
- **Dependencies / future checks:** AUD-003, AUD-009, AUD-011; V01, V02, V09.
- **Acceptance:** no synthetic ID is represented as an ingested citation; evidence-bearing model success is tested
  strictly. A recorded sample denominator establishes the 95% SC-001 outcome separately from unit assertions.

### AUD-005: Make Handoff Delivery Circuit-Aware and Idempotent

- [X] **AUD-005 (P1)**. Affects T006, T023, T027, T031; FR-014; US3-AS4; edge case EC-06.
- **Expected versus observed:** bounded retries respect target health and avoid duplicate effects.
  [deliver_handoff_with_retry](../../apps/agents/common/handoffs.py#L124) never checks a target circuit, uses the
  window merely as an individual sleep cap, sets `next_retry_at` to now, and has no duplicate claim mechanism.
  [EventBus](../../apps/api/app/services/event_bus.py#L37) treats the first exception as permanent and no subscriber
  as an empty result. [T031](../../tests/integration/test_handoff_retry.py#L42) tests only two synthetic attempts.
- **Impact:** premature loss, retries against unavailable targets, and duplicate safety-critical side effects.
- **Developer instructions:** resolve attempts-versus-retries in AUD-025; enforce a monotonic total deadline,
  target-scoped circuit decisions, scheduled next retry time, cancellation and persistence-aware acknowledgement.
  Use atomic tenant/handoff idempotency claims and retain retryable failures without finalising dedup prematurely.
- **Tester instructions:** extend [test_handoff_retry.py](../../tests/integration/test_handoff_retry.py#L6) with fake
  clocks/sleeps and a real circuit object; integrate DLQ storage rather than returning a dummy ID. Positive: recovery
  on last allowed attempt; negative: open circuit, timeout, exhausted deadline; edge: zero/invalid budgets, no
  subscriber, duplicate concurrent deliveries, write success followed by lost ACK. Verify one logical result and
  exact attempt schedule without real five-minute sleeps.
- **Dependencies / future checks:** AUD-006, AUD-012, AUD-025, AUD-026; V02.
- **Acceptance:** bounded documented attempts, no delivery while disallowed by circuit, one durable terminal state,
  and one logical side effect per tenant/handoff; the originator and operator can observe failure.

### AUD-006: Wire Dependency Retries and Durable Failure Recovery

- [X] **AUD-006 (P1)**. Affects T004, T005, T006, T027, T041, T042, T044; FR-024, FR-025; SC-010;
  US7-AS1, US7-AS4; EC-09.
- **Expected versus observed:** actual Cosmos/Redis transient calls retry and permanent ingestion/event failures
  enter a recoverable store. [Decorator](../../apps/api/app/middleware/resilience.py#L82) aliases RuntimeError and
  has no production callers; [dashboard Cosmos call](../../apps/api/app/services/dashboard_service.py#L9) catches
  failures without it; [cache](../../apps/api/app/services/governance_cache.py#L9) remains memory-backed.
  [Pipeline callback](../../apps/agents/risk_assessment/pipeline.py#L78) returns an invented DLQ ID, while
  [T044](../../tests/integration/test_retry_dead_letter.py#L20) manually inserts a failure.
- **Impact:** transient faults become missing data/errors and failed payloads can be lost on restart or across replicas.
- **Developer instructions:** put retry policy on the actual selected repository/cache adapters, classify concrete
  retryable SDK statuses/exceptions, coordinate SDK and application attempts, and fail permanent faults promptly.
  Unify feature/operator stores behind a tenant-scoped durable adapter with a local fake. Route exhausted operations
  automatically with the original safe payload, correlation, incident, reason, and count; add bounded retention,
  pending-age alerts, and genuine replay/escalation semantics without overwriting the original payload with notes.
- **Tester instructions:** reuse [test_retry_dead_letter.py](../../tests/integration/test_retry_dead_letter.py#L5)
  and [test_dead_letter_api.py](../../tests/contract/test_dead_letter_api.py#L24). Positive: SDK transient faults
  recover within the agreed three attempts; negative: auth/schema errors are not retried; edge: DLQ write failure,
  restart/reload, repeated replay, retention boundary, full store. Assert API-triggered automatic DLQ creation and
  resolution effects; measure the 90% claim on a defined fault population, not one passing function.
- **Dependencies / future checks:** AUD-001, AUD-005, AUD-012, AUD-013; V01, V02, V09.
- **Acceptance:** connected storage/cache calls exercise the policy; failures survive process replacement and remain
  tenant-scoped, observable, and replayable; no unbounded silent accumulation or false replay-success marking.

### AUD-007: Make Error Responses Safe and Consistent

- [X] **AUD-007 (P1)**. Affects T040, T043; FR-023; SC-009; US7-AS2.
- **Expected versus observed:** every failure has one valid correlation ID and a non-leaking category/status body.
  [HTTP/permission handlers](../../apps/api/app/middleware/error_handler.py#L162) return raw exception details;
  [resilience middleware](../../apps/api/app/middleware/resilience.py#L60) and handlers mint separate IDs when absent.
  The handler registers FastAPI HTTPException rather than the framework's route-less HTTP exception base. Newer
  [problem responses](../../apps/api/app/middleware/error_handler.py#L111) deliberately use a different contract.
- **Impact:** internal text can reach clients and incident correlation breaks precisely on failure paths.
- **Developer instructions:** establish a validated request-scoped UUID once, propagate it into headers/logs/body,
  map known user-safe messages explicitly, and keep diagnostic details only in protected telemetry. Cover router and
  middleware-originated failures. Honour explicitly versioned RFC 9457 routes without reverting newer contracts;
  reconcile their scope through AUD-025.
- **Tester instructions:** expand [test_error_responses.py](../../tests/contract/test_error_responses.py#L5).
  Positive: known safe 4xx; negative: raised 5xx/permission text containing a synthetic secret marker is absent;
  edge: unknown route, wrong method, malformed JSON, 401/403/429/503, invalid incoming UUID, missing ID and nested
  middleware error. Assert header/body equality, UUID validity, status/category, and no traceback/internal text.
- **Dependencies / future checks:** AUD-011, AUD-013, AUD-025; V01, V04.
- **Acceptance:** the full failure matrix follows its explicit contract with one correlation ID and no sensitive
  detail, not merely the single validation-error assertion currently tested.

### AUD-008: Validate Every Language and Preserve Safety Failure State

- [X] **AUD-008 (P1)**. Affects T011, T012, T014, T016, T017; FR-002, FR-006; SC-002; EC-01.
- **Expected versus observed:** every public block matches its requested language and failed content remains
  flagged. [Language detection](../../apps/agents/common/content_safety.py#L95) is vacuous for four languages;
  [Azure validation](../../apps/agents/common/content_safety.py#L118) returns before language checking.
  [Stage 7](../../apps/agents/communication/pipeline.py#L375) can validate replacement text and reset its safety
  result, hiding the earlier failure. The [six-language contract test](../../tests/contract/test_communication_llm.py#L4)
  is unconditionally skipped.
- **Impact:** wrong-language or inadequately checked public information can be presented as validated.
- **Developer instructions:** run language and length checks regardless of safety provider, use meaningful language
  detection and reviewed plain-language templates, preserve per-block original safety outcome through aggregation,
  and retain worst-case `safety_fallback`/`failed_with_fallback`. Do not relabel English emergency fallback as a
  translated message; surface translation-unavailable separately. Keep evidence logging protected through AUD-011.
- **Tester instructions:** use the existing communication contract, [translator tests](../../tests/unit/test_communication_translator.py#L1),
  and [safety tests](../../tests/unit/test_content_safety_pipeline.py#L86). Positive: valid samples for all six
  languages; negative: English under ar/vi/el/it and unsafe input; edge: mixed scripts, legitimate Unicode English,
  Azure success with wrong language, one failed block followed by a safe replacement, missing template.
- **Dependencies / future checks:** AUD-002, AUD-010, AUD-011; V01.
- **Acceptance:** all six real blocks are checked, an earlier safety rejection cannot become a clean pass, and the
  active public-alert test runs with explicit model-success and fallback cases.

### AUD-009: Enforce Real Input and Output Token Budgets

- [X] **AUD-009 (P2)**. Affects T007, T012, T018; FR-003; US1-AS4.
- **Expected versus observed:** configurable budgets hold at request and returned-output boundaries.
  [Trimming](../../apps/agents/common/llm_mixin.py#L125) retains 80% of characters with an 80-character floor, so it
  cannot establish a token bound; no input-token limit is applied. Agent call sites use fixed output constants and
  append references after this step. [T018](../../tests/contract/test_token_budget.py#L4) asserts only shorter text.
- **Impact:** cost/latency overages remain possible and truncated content may lose essential warning meaning.
- **Developer instructions:** use the selected model's supported token accounting, enforce configured input/output
  ceilings, preserve required citation/action fields, and bound any re-request. Recheck the final returned content
  after added references. Keep actual usage separate from allowed/retained usage and log the overage with correlation.
- **Tester instructions:** extend the existing token-budget test with a fake tokenizer/model response. Positive:
  below/exact configured budget; negative: severe overage and input overflow; edge: CJK, tiny budgets, missing usage,
  post-generation citation append, truncated structured content. Assert final token count or explicit fallback,
  bounded retry count, and an actual production overage log.
- **Dependencies / future checks:** AUD-004, AUD-011, AUD-012; V01.
- **Acceptance:** all active call paths honour configuration and no returned successful content exceeds its budget;
  failures yield a safe labelled fallback rather than arbitrary character clipping.

### AUD-010: Bound Model Failure and Complete-Draft Latency

- [X] **AUD-010 (P2)**. Affects T012, T014, T016, T017; FR-004; SC-002, SC-003; EC-02.
- **Expected versus observed:** failed calls produce a fallback within two seconds and all six draft blocks within
  30 seconds. [Foundry chat_complete](../../apps/agents/common/foundry_chat_client.py#L397) accepts `timeout_s` but
  calls `client.complete(**kwargs)` without it. [Translator](../../apps/agents/communication/translator.py#L38)
  sequentially generates six blocks with default per-call timeouts, then [back-translates](../../apps/agents/communication/pipeline.py#L335).
  Original tests assert neither deadline.
- **Impact:** an unavailable/throttled model can block incident response and accumulate work despite fallback code.
- **Developer instructions:** enforce a caller-owned monotonic deadline across transport retries and the complete
  draft, propagate remaining time, cancel abandoned work, and use bounded concurrency where safe. Resolve whether
  SC-003 includes outage detection time in AUD-025; do not silently redefine the latency denominator.
- **Tester instructions:** extend fallback/communication tests with clock-controlled delayed SDK responses.
  Positive: six complete outputs within budget; negative: hung transport and 429 storm; edge: circuit opens midway,
  one slow language, back-translation timeout, late completion after cancellation. Verify zero lost drafts,
  no orphaned work, and elapsed bounds rather than immediate mocked exceptions alone.
- **Dependencies / future checks:** AUD-008, AUD-009, AUD-025; V01, V09.
- **Acceptance:** configured deadlines reach the actual transport and total operation, with labelled complete
  fallback outputs and measured two-/30-second acceptance evidence on the agreed workload.

### AUD-011: Preserve Correlation, Deployment, and Safety Evidence

- [X] **AUD-011 (P2)**. Affects T010, T012, T013, T014, T017, T019; FR-005, FR-006; US1-AS3.
- **Expected versus observed:** the same request correlation and actual deployment appear across model request,
  response, usage, latency, failure, and protected safety evidence. [Wrapper](../../apps/agents/common/llm_client.py#L176)
  omits correlation on the Foundry call; [Foundry](../../apps/agents/common/foundry_chat_client.py#L436) creates a new
  ID and returns deployment in `raw`, while the wrapper looks for a nonexistent `deployment_id` attribute.
  Agent callers omit request correlation and [T019's stub](../../tests/contract/test_llm_logging.py#L9) writes its
  own successful log. Safety failure returns replacement content without preserving flagged-content evidence.
- **Impact:** model usage and unsafe-output incidents cannot reliably be joined to an operator request or deployment.
- **Developer instructions:** propagate a request/operation context through agents and transport, return canonical
  resolved deployment metadata, and emit production logs for every terminal outcome. Store flagged content only in
  a restricted, AU-resident, minimised evidence channel with retention; never expose it through ordinary responses
  or general logs. Preserve model filter flags instead of discarding provider safety metadata.
- **Tester instructions:** replace the test-owned logger with an injected transport only. Assert actual logged ID,
  deployment, both usage counters, latency and failure category; inspect request headers/context. Negative: mismatch
  or missing deployment and safety rejection; edge: no incoming ID, provider-generated ID, empty completion,
  flagged content containing a synthetic PII marker. Verify protected evidence and public-log redaction separately.
- **Dependencies / future checks:** AUD-007, AUD-008, AUD-010, AUD-026; V01, V02, V09.
- **Acceptance:** one trace joins request to final output; logs report the deployed model, not merely a tier key;
  protected post-hoc safety evidence exists without leaking sensitive content.

### AUD-012: Enforce Domain Invariants

- [X] **AUD-012 (P2)**. Affects T003, T007, T023, T024, T045; corresponding [data-model rules](data-model.md#L5).
- **Expected versus observed:** positive token/time/load bounds, nonempty failure context, valid handoff transitions,
  and consistent measured outcomes are enforced. [ModelDeployment](../../packages/domain/src/domain/models/model_deployment.py#L6)
  permits HTTP and nonpositive budgets; [DeadLetterEntry](../../packages/domain/src/domain/models/dead_letter_entry.py#L10)
  permits empty payload/strings; [handoff model](../../apps/agents/common/handoffs.py#L26) uses unbounded floats/strings;
  [LoadTestResult](../../packages/domain/src/domain/models/load_test_result.py#L6) has no relational validators.
- **Impact:** malformed state can be recorded as delivered, safe, or passing and exported as credible evidence.
- **Developer instructions:** add strict field and cross-field constraints from the existing design, including
  status transitions through domain methods, tenant-scope consistency, retry maximums, ordered percentiles, request
  count consistency, allowed environment and measured pass/fail agreement. Keep JSON alias changes in AUD-013.
- **Tester instructions:** add cases in the existing feature contract tests and load-report test surface. Positive:
  valid boundary objects; negative: HTTP endpoint, zero budgets, empty failure payload, confidence outside 0-1,
  arbitrary status, negative counts; edge: retry count equals max, timezone-aware times, p50=p95=p99, 0/100% errors,
  forbidden resolved-to-pending or delivered-to-retrying transition. Do not substitute later DLQ model tests.
- **Dependencies / future checks:** AUD-005, AUD-013, AUD-016; V01, V03.
- **Acceptance:** every validation rule in the eleven design entities/modifications is either executable or has an
  explicit non-runtime representation; impossible states fail at their owning boundary.

### AUD-013: Reconcile the Published API with Runtime JSON

- [X] **AUD-013 (P2)**. Affects T003, T008, T009, T023, T029, T034, T042, T048; all addendum endpoints/schemas.
- **Expected versus observed:** advertised camelCase fields/filters work. [Contract resolve body](contracts/openapi-addendum.yaml#L80)
  requires `resolvedByPersonaId`, but [runtime input](../../apps/api/app/api/dead_letters.py#L10) requires
  `resolved_by_persona_id`. `entryType`/`incidentId` filters are ignored as unknown query parameters; defaults and
  enums differ; model dumps emit snake_case. Handoff dictionaries omit required confidence. Two GET DLQ routes
  are registered against separate stores. API prefix and `openai` to `foundry` evolution are not reflected consistently.
- **Impact:** generated clients fail valid requests or silently receive unfiltered/incomplete data.
- **Developer instructions:** choose and document compatible wire names, use explicit aliases/response models,
  merge duplicate route ownership, and synchronize source-of-truth schema with runtime. Preserve intentional newer
  versioned contracts, and document migration instead of silently reverting them.
- **Tester instructions:** extend [test_dead_letter_api.py](../../tests/contract/test_dead_letter_api.py#L24),
  [test_error_responses.py](../../tests/contract/test_error_responses.py#L5), and handoff tests. Positive: canonical
  camelCase list/resolve round-trip; negative: invalid enums/unknown filters; edge: default pending filter, paging
  boundaries, missing required output field, duplicate OpenAPI operation, UUID format. Validate actual responses
  against the checked-in schema, including Recommendation, PublicAlert and TimelineEvent additions.
- **Dependencies / future checks:** AUD-001, AUD-007, AUD-012, AUD-026; V01, V04.
- **Acceptance:** all four endpoint contracts and seven schema/addendum families match real requests/responses;
  no shadowed route or undocumented mixed casing remains.

### AUD-014: Restore Full CI Coverage and Trigger Semantics

- [X] **AUD-014 (P2)**. Affects T020, T049, T051; FR-007, FR-008, FR-009, FR-010; SC-004; EC-03.
- **Expected versus observed:** every push/PR runs the required suites and hard quality gates within ten minutes.
  [Triggers](../../.github/workflows/ci.yml#L3) cover four named push branches and PRs to main;
  [python-test](../../.github/workflows/ci.yml#L131) runs only contract/integration. Existing ruff, TypeScript, web
  build and named steps are credited; general simulation/unit coverage is not. Main quality job lacks a timeout.
  [Branch protection](../../.github/branch-protection.json#L2) explicitly says it is descriptive only.
- **Impact:** regressions in omitted acceptance suites can merge; CI duration and merge prevention are unproven.
- **Developer instructions:** align triggers/suite manifest with FR-007 and explicitly separate credentialed tests
  from mandatory hermetic ones; bound external dependency steps and job duration, parallelise where needed, and
  retain granular stage results on failure/skip. Apply required checks only through an authorised repository admin.
- **Tester instructions:** reuse [ci_workflow fixtures](../../tests/devops/conftest.py#L37) and the structured YAML
  assertions in [test_cd_workflow.py](../../tests/devops/test_cd_workflow.py#L16), adding CI-specific cases without
  changing unrelated CD semantics. Use the suite inventory in [pyproject.toml](../../pyproject.toml#L40).
  Positive: feature push and PR select all required tests;
  negative: deliberate test/lint/type/build failure blocks; edge: hanging install, skipped live tests, cancelled job,
  missing status check. Capture real run/check evidence later, not a YAML-only claim.
- **Dependencies / future checks:** AUD-015, AUD-023, AUD-025; V05, V09.
- **Acceptance:** all required suites/gates are selected on agreed events, no required failure is swallowed, and
  current run evidence proves the ten-minute bound and actual merge restriction.

### AUD-015: Make the Lightweight p95 Benchmark Blocking

- [X] **AUD-015 (P2)**. Affects T021, T022; FR-030; SC-004, SC-012; US8-AS3.
- **Expected versus observed:** about 50 concurrent dashboard/signal requests produce p95 checks in under 60 seconds.
  [Current file](../../tests/benchmark/test_api_performance.py#L16) sequentially benchmarks agent health endpoints;
  [comparison](../../tests/benchmark/compare_benchmarks.py#L177) uses median, ignores `slo_pass` when deciding
  failure, and allows missing/current-empty evidence; [hook](../../tests/benchmark/conftest.py#L85) disables failure in CI.
- **Impact:** a PR with a material API latency regression can appear green.
- **Developer instructions:** restore the scoped concurrent API workload, compute p95 from actual samples, enforce
  absolute SLO and baseline regression rules in CI, fail closed on missing/invalid required samples, and budget
  startup/warmup/measurement below 60 seconds. Keep unrelated agent benchmarks in their own tier if necessary.
- **Tester instructions:** reuse the existing benchmark file, [fixtures](../../tests/benchmark/conftest.py#L25),
  and [comparison helper](../../tests/benchmark/compare_benchmarks.py#L127). Positive: representative baseline;
  negative: injected slow p95 and `CI=true`; edge: first run above absolute SLO, removed metric, corrupt/empty JSON,
  median passes while tail fails, concurrency actually reaching 50. Assert process failure and elapsed budget.
- **Dependencies / future checks:** AUD-014, AUD-016; V03, V05.
- **Acceptance:** a deliberate p95 regression fails the same CI command used on PRs; metadata labels and printed
  warnings alone cannot satisfy the gate.

### AUD-016: Correct Performance Report Mathematics

- [X] **AUD-016 (P2)**. Affects T045, T047; FR-029; SC-012; US8-AS2; EC-08.
- **Expected versus observed:** per-target measured latency, successful ingestion throughput and error ratio
  determine pass/fail. [generate_report](../../tests/load/report.py#L11) shares a maximum p95 across all rows,
  compares Failure Count to 1, calls that `signal_throughput_50k_hr`, ignores time/RPS, and passes empty input.
  It also uses `<=` where the spec says latency `<`.
- **Impact:** zero traffic can pass, two failures among 100,000 requests can fail incorrectly, and very low
  throughput can pass as long as it has no errors.
- **Developer instructions:** validate CSV/JSON schema, select exact scenario/request names, compute successful
  signals/hour from observed duration or rate, calculate failures/requests, and keep independent p95s. Reject
  missing/NaN/negative/zero-sample metrics and record counts, duration, concurrency, environment, revision, and thresholds
  in validated LoadTestResult records. Preserve unit labels and strict boundary semantics.
- **Tester instructions:** add proposed input fixtures beside the existing [report](../../tests/load/report.py#L1)
  and tests in the existing load test area. Positive: 50,000 successful signals/hour and passing p95; negative:
  empty/header-only data, slow dashboard, low throughput, 1% boundary; edge: many requests with two failures,
  aggregate row versus endpoint rows, milliseconds/seconds, decimal CSV, malformed numbers, shared-environment noise.
- **Dependencies / future checks:** AUD-012, AUD-017, AUD-025; V03, V06.
- **Acceptance:** mathematically independently checked fixtures demonstrate correct pass/fail for every target;
  absence of evidence never becomes a passing measurement.

### AUD-017: Run the Required Staging Load Scenario

- [X] **AUD-017 (P2)**. Affects T046; FR-028, FR-030; SC-012; US8-AS1; EC-08.
- **Expected versus observed:** 1,000 simultaneous operators plus controlled burst ingestion run nightly/manually.
  [DashboardUser](../../tests/load/locustfile.py#L19) reads health; [nightly workflow](../../.github/workflows/nightly-load.yml#L44)
  invokes pytest with `|| true`. The 200-injection and 50-agent retrieval workflows test different workloads, not
  the stated dashboard/read/ingestion contract.
- **Impact:** no trustworthy capacity validation protects the documented platform scale.
- **Developer instructions:** implement scenario-specific real dashboard reads and realistic authorised signal
  payloads, seed a known dataset, control arrival rate independently of user count, select explicit Locust user
  classes, and invoke the corrected report with failure propagation. Use an approved isolated staging target and
  capture host capacity/contention/warmup; do not send this load to production by default.
- **Tester instructions:** reuse [locustfile.py](../../tests/load/locustfile.py#L19) and
  [threshold helper pattern](../../tests/load/assert_locust_thresholds.py#L19). Positive: staged 1,000-user plateau
  with at least 50,000 successful signals/hour; negative: denied ingestion, overloaded API, missing dashboard row;
  edge: ramp-up versus steady-state statistics, one user class absent, auth expiry, contention and retries.
- **Dependencies / future checks:** AUD-014, AUD-016, AUD-020; V06 and separately authorised V09.
- **Acceptance:** scheduled/manual workflow actually invokes the relevant Locust scenario, archives raw metrics
  and a valid per-target report, and fails on a breach without `|| true` or synthetic substitute measurements.

### AUD-018: Deliver Reproducible and Complete Container Images

- [X] **AUD-018 (P2)**. Affects T032, T033; FR-015, FR-016, FR-017; SC-006; EC-04.
- **Expected versus observed:** both images run required application paths, reuse dependency layers on code-only
  changes, and build reproducibly. Both Dockerfiles copy code before pip install. [API copy set](../../apps/api/Dockerfile#L19)
  excludes `maf_runtime`, while [workflow routes](../../apps/api/app/api/routes/workflow_runs.py#L65) import it on
  requests. [Agent copy set](../../apps/agents/Dockerfile#L4) also omits MAF despite
  [wheel configuration](../../apps/agents/pyproject.toml#L58). Both install floating minimum-version dependencies.
  [Quickstart commands](quickstart.md#L61) use app directories instead of the root context required by COPY.
- **Impact:** a passing health probe can conceal missing runtime features; ordinary source edits reinstall all
  dependencies and external package changes can alter/fail builds.
- **Developer instructions:** audit the selected startup and route import closure, package required modules/assets,
  install reproducibly resolved dependencies before code-copy layers, and document root build contexts. Retain
  non-root users, secret exclusions, and correct ports. Do not add real credentials to images.
- **Tester instructions:** reuse [service metadata fixtures](../../tests/devops/conftest.py#L130); proposed new
  `tests/devops/test_feature003_container_smoke.py` is a future test path, not existing evidence. Positive: root
  build, non-root UID, API health and workflow route, dispatcher invocation and API reachability; negative: omitted
  package/asset and credential file in context; edge: clean/incremental rebuild, dependency cache unavailable,
  reproducible rebuild and frozen-package source unavailable. Inspect layers and image history as well as HTTP 200.
- **Dependencies / future checks:** AUD-003, AUD-013, AUD-019; V07 after explicit developer/tester authorisation.
- **Acceptance:** complete runtime paths work in both images, secrets are absent, dependency layer remains cached
  for code-only edits, and recorded clean/incremental timings meet five-/two-minute limits.

### AUD-019: Report Dependency Health Truthfully

- [X] **AUD-019 (P2)**. Affects T034; FR-015; SC-006; US4-AS1.
- **Expected versus observed:** configured-but-unavailable dependencies cause an honest degraded response and
  in-memory backends report stub. [Health helper](../../apps/api/app/api/health.py#L10) only tests environment-variable
  presence. No probe returns unavailable, so the degraded branch cannot be exercised by actual dependency status.
  The Foundry key rename is explicitly documented and is not itself a regression.
- **Impact:** readiness and operator diagnostics can claim healthy service during a dependency outage.
- **Developer instructions:** distinguish cheap liveness from bounded cached readiness probes against the actual
  configured adapters, use current environment names, avoid generating model content per probe, and document which
  optional failures degrade rather than stop service. Preserve credential-free health output.
- **Tester instructions:** reuse the [create_app/TestClient setup](../../tests/contract/test_error_responses.py#L1)
  for proposed health cases in that existing API boundary test file. Positive: stub and healthy adapters;
  negative: configured unreachable Cosmos/cache/model; edge: mixed states, probe timeout,
  failed authentication, cached stale result and missing optional dependency. Assert status fields, bounds, and no
  endpoint credentials in responses.
- **Dependencies / future checks:** AUD-006, AUD-013, AUD-018; V01, V07.
- **Acceptance:** dependency values reflect inspected adapter/probe state, outage is distinguishable from stub,
  and container/readiness behavior matches the documented contract.

### AUD-020: Resolve Infrastructure Entrypoints and Security Wiring

- [ ] **AUD-020 (P1)**. Affects T035; FR-018, FR-019, FR-020; SC-007; US5-AS1, US5-AS2, US5-AS3; EC-05.

> **2026-09-15 remediation status:** GOVERNANCE-BLOCKED. The selected `AI Impact Analyzer`
> subscription returned zero assignments from both scoped and unscoped Azure Policy API queries,
> but Azure Portal count parity and management-group inheritance remain unverified. No Bicep was
> changed. See [governance constraints](04-governance-constraints.md).

- **Expected versus observed:** the documented deployment provisions connected AU-resident resources with
  inter-service identity and least privilege. [Spec entrypoint](../../infra/bicep/main.bicep#L3) has no AU allowlist;
  API/agent dependency environment wiring is incomplete; only selected diagnostics/RBAC are present. The active
  [root template](../../infra/main.bicep#L80) improves AU validation, model deployments, endpoint wiring and RBAC,
  but still configures registry username/password secrets, public data planes, and no Redis identity assignment.
- **Impact:** following the spec versus azd yields different security/runtime outcomes; default deployment need
  not satisfy this feature's connected environment or least-privilege acceptance.
- **Developer instructions:** explicitly reconcile the two maintained entrypoints, share or retire the old path
  only with documented authority, enforce the constitution's bounded model-hosting carve-out rather than a generic
  region escape, and wire service endpoints, data-plane roles and diagnostics end-to-end. Prefer verified modules
  per repository policy, remove arbitrary security-ignore/default targeting, and consult current governance
  constraints through a separately authorised infrastructure review. Do not change policy to accommodate code.
- **Tester instructions:** extend [parameter tests](../../tests/devops/test_parameter_files.py#L64) using
  [parameter/region fixtures](../../tests/devops/conftest.py#L48) and reviewed parameter sets. The
  [infra test directory](../../infra/tests/) contains only a placeholder, not an existing executable suite.
  Positive: all required resource types/deployments and identities in AU; negative: non-AU data store, missing role, placeholder image,
  forbidden public access; edge: permitted named model carve-out, partial deployment/re-run, optional module disabled,
  resource-name collisions, denied dependency access. Inspect expanded resources and inter-service access, not just
  identity property existence.
- **Dependencies / future checks:** AUD-018, AUD-021, AUD-025; V08 and separately authorised V09.
- **Acceptance:** one explicit supported path satisfies provisioning, residency, identity and monitoring contracts;
  reviewed what-if/policy evidence names revision, parameters and resource graph without secret material.

### AUD-021: Make Alert Semantics and Notification Evidence Real

- [ ] **AUD-021 (P2)**. Affects T036, T037; FR-026, FR-027; SC-011; US7-AS3; EC-07.

> **2026-09-15 remediation status:** GOVERNANCE-BLOCKED. Correcting the p99 query and receiver
> contract changes the same Bicep surface as AUD-020. Those edits remain blocked until effective
> inherited policy and Portal parity are verified. No notification delivery evidence is claimed.

- **Expected versus observed:** a validated p99 latency alert and error alert reach a real operational target.
  [Latency rule](../../infra/bicep/monitoring.bicep#L117) labels p99 but aggregates Maximum; the
  [current module](../../infra/modules/monitoring.bicep#L108) retains that behavior. Default receivers are examples,
  not validated operational destinations. A configured action group does not prove a five-minute notification SLA.
- **Impact:** misleading alert semantics and a configured-looking but unproven response channel.
- **Developer instructions:** use the intended percentile metric/query or explicitly amend the threshold contract,
  require an enabled approved receiver, validate HTTPS/address configuration, and provide receiver failure visibility
  and escalation. Bind application telemetry to these alert scopes, preserving least privilege and no leaked URLs.
- **Tester instructions:** reuse the assertion structure in
  [test_observability_alerts_bicep.py](../../tests/devops/test_observability_alerts_bicep.py#L13), adding specific
  checks for both feature monitoring modules rather than treating its different SLI rules as 003 coverage.
  Positive: valid target and controlled breach; negative: empty/example/invalid target and unreachable webhook; edge: maximum
  spike without p99 breach, p99 sustained breach, recovery, duplicate notifications and receiver delay. Verify both
  rules link the right action group; later record threshold-to-receipt timestamps, not only rule creation.
- **Dependencies / future checks:** AUD-011, AUD-020, AUD-023; V08, V09.
- **Acceptance:** rule math matches its name and requirement; at least one operational receiver is configured and
  delivery/failure escalation is evidenced within the agreed five-minute measurement boundary.

### AUD-022: Complete the Demo Evidence Pack

- [X] **AUD-022 (P2)**. Affects T038, T039; FR-021, FR-022; SC-008; US6-AS1, US6-AS2, US6-AS3; EC-10.
- **Expected versus observed:** an annotated, reproducible under-five-minute incident story and executive
  before/after deck. [Walkthrough](../../docs/disaster-response-hub/demo/walkthrough.md#L3) lists eight screenshot
  placeholders and its budget totals 300 seconds. [Deck KPI table](../../docs/disaster-response-hub/demo/executive-deck.md#L17)
  lists targets without paired measurements. Later presentation assets exist but are not mapped as full replacement.
- **Impact:** evaluators cannot independently inspect the claimed journey or distinguish measured impact from targets.
- **Developer instructions:** finish or explicitly designate the canonical screenplay/deck, add proposed current
  annotated screenshots/GIFs to the existing demo directory, map all eight surfaces to revisions and scenario steps,
  and include actual paired KPI evidence or clearly label unavailable outcomes. Correct timing to strictly under
  300 seconds and document an update trigger when UI changes. Preserve the accepted screenplay option; video is not
  newly required by this audit.
- **Tester instructions:** use [baseline procedures](../../docs/disaster-response-hub/evaluation/baseline-metrics.md#L7),
  [survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L23), and current demo links. Positive:
  complete timed two-jurisdiction bushfire story; negative: missing image, obsolete screen, target passed off as
  measurement; edge: offline rendering, non-technical comprehension, small-screen screenshots, fallback display.
- **Dependencies / future checks:** AUD-002, AUD-003, AUD-026; V10 and human acceptance via V09.
- **Acceptance:** all major screens have reviewed current annotations, KPI sources identify paired runs, a human
  reviewer records comprehension, and measured walkthrough duration is below five minutes.

### AUD-023: Replace Completion Prose with Revision-Bound Evidence

- [X] **AUD-023 (P2)**. Affects T049, T050, T051, T052; SC-001 through SC-013; plan/checklist execution claims.
- **Expected versus observed:** every claimed execution/outcome is reproducible and attributable. The
  [March record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L7) reports
  31 Python and six Playwright passes without raw artifacts/revision and explicitly records the live gate as skipped.
  Neither that narrative nor a projected slide score proves all thirteen criteria at the audited revision.
- **Impact:** stakeholders may accept a completed checklist whose central measured outcomes were never established.
- **Developer instructions:** keep historical evidence intact; define a per-SC evidence manifest with revision,
  command, environment, fixture IDs, denominators, artifact hashes, outcome and known skips. Proposed run artifacts
  belong under the existing evaluation directory. Separate source-supported readiness from human/cloud/runtime
  completion and do not retroactively relabel synthetic results as live.
- **Tester instructions:** after relevant repairs, execute the scoped/full gates under separate authority and retain
  raw pytest/Playwright/CI/container/load/what-if/notification outputs. Positive: evidence joins to the candidate
  revision; negative: skipped live test, stale report, missing denominator; edge: rerun, changed model/dataset,
  partial suite, unsigned human claim. SC-013 requires an authorised independent evaluation, not this static audit.
- **Dependencies / future checks:** AUD-001 through AUD-022 where applicable, AUD-024, AUD-026; V01-V10.
- **Acceptance:** every SC has traceable pass/fail/unverified evidence; incomplete external/human criteria remain
  explicitly open. Do not alter the original task checkboxes as part of this review.

### AUD-024: Repair the Live Rehearsal Contract and Gate

- [X] **AUD-024 (P2)**. Affects T002, T050, T052, T053; SC-001, SC-002, SC-003, SC-005; quickstart steps 1-9.
- **Expected versus observed:** the gated rehearsal exercises real Risk and Communication generation and the
  incident journey. [Runbook](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md#L7) asks for
  legacy key variables, while [configuration](../../apps/agents/common/llm_config.py#L34) uses Foundry/AAD and
  [test](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L6) skips unless legacy variables exist, then
  invokes Risk only. It does not assert communication, chain, approval, six languages, or deadlines.
- **Impact:** a correct Foundry-only setup can skip and an incomplete Risk-only pass can be mistaken for rehearsal.
- **Developer instructions:** align the runbook and opt-in gate with the selected current authentication/deployment
  configuration; invoke the actual connected journey and retain per-step outcomes. Explicitly fail a requested live
  rehearsal whose prerequisites are missing; do not demand API keys when managed identity is authoritative.
- **Tester instructions:** extend the existing live and hermetic rehearsal files. Positive: current Foundry setup
  performs both model purposes; negative: missing credentials/deployment, any fallback when model success is required;
  edge: throttling, safe fallback step, two jurisdictions/three source types, matching timeline count and final
  human-approved publication. Use an approved isolated tenant; never print tokens/keys or contact public channels.
- **Dependencies / future checks:** AUD-002, AUD-003, AUD-008, AUD-010, AUD-011, AUD-025; V02, V09.
- **Acceptance:** the gate tests the documented workflow with current configuration, distinguishes skipped from
  passed, and produces revision-bound evidence while T052 remains unverified until genuinely executed.

### AUD-025: Resolve Design Contradictions and Unsupported Review Claims

- [x] **AUD-025 (P2)**. Affects T027, T031, T034, T035, T038, T049, T050, T053; all checklist/gate claims,
  ASM-001, ASM-002, ASM-003, PER-001, PER-002, PER-003, HYP-001, SCP-001, SCP-002, SCP-003, SCP-004.
- **Expected versus observed:** one testable contract and attributable review evidence. Spec says three retries;
  tasks/data model describe three attempts/count limits. [Quickstart step 7](quickstart.md#L98) says three handoffs
  but names two edges; its 100-user smoke is not the 1,000-user criterion. The location assumption conflicts with the
  [bounded constitution](../../.specify/memory/constitution.md#L244). The
  [HYP evidence link](spec.md#L275) is missing, and appended validated-persona/consultation labels lack local sign-off.
- **Impact:** developers and testers can satisfy incompatible interpretations and call unsupported outcomes complete.
- **Developer instructions:** obtain owner decisions within the existing spec/plan/quickstart (no new feature spec),
  clarify retries/deadlines/event cardinality/region exceptions, and bind explicit replacements such as Foundry and
  RFC 9457. Correct inappropriate inherited FR references in persona/hypothesis prose. Link existing authentic
  consultation/persona evidence or label it unverified; a proposed HYP evidence record must be clearly new until created.
- **Tester instructions:** verify each item ID in the review tables below against its own evidence. Positive:
  one consistent acceptance interpretation; negative: blanket PASS, missing stub, unsigned approval; edge: original
  versus amended requirements, different spec's identically numbered FR/SC, stale rubric baseline, 004 name collision.
  Do not invoke new grading just to fill an implementation-audit table.
- **Dependencies / future checks:** domain-owner decisions, AUD-023; V10.
- **Acceptance:** every contradiction has a scoped signed resolution; human/external claims remain UNVERIFIED until
  evidence is supplied; no blanket supersession or post-hoc checkbox completion.
- **Status note (2026-09-15):** automatable cross-document contradictions were reconciled in feature-local artifacts; external owner consultation/sign-off evidence remains explicitly UNVERIFIED.

### AUD-026: Expose the Real Handoff Lifecycle and Timeline

- [X] **AUD-026 (P2)**. Affects T006, T024, T028, T029, T030; FR-013, FR-014; SC-005; US3-AS3, US3-AS4.
- **Expected versus observed:** every handoff, including failed/retrying delivery, links to its timeline and operator
  state. [EventBus success record](../../apps/api/app/services/event_bus.py#L46) omits confidence, payload and timeline
  reference; its failure branch writes no HANDOFF_EVENTS entry. [API](../../apps/api/app/api/handoffs.py#L7) can only
  filter what is in that dictionary. [Dashboard](../../apps/api/app/services/dashboard_service.py#L48) has no handoff
  projection; tracked web search found no consumer of this feature endpoint. No active `llm_call` TimelineEvent
  producer was found despite the post-design claim.
- **Impact:** delivery failures and generation provenance remain invisible or incomplete in the incident audit path.
- **Developer instructions:** record a single typed lifecycle per tenant/handoff, link one logical TimelineEvent,
  update retry/delivery/failure fields consistently, and project it through API/dashboard consumers. Preserve source,
  target, scope, confidence, bounded safe summary and linked DLQ ID. Add LLM/fallback timeline events where claimed.
  Do not record every unrelated event-bus publish as an agent handoff.
- **Tester instructions:** extend the existing chain/retry tests and existing web E2E area. Positive: delivered
  chain visible through API/UI; negative: failed subscriber appears failed/dead-lettered, not absent; edge: duplicate
  publish, multiple subscribers, retry then success, same incident in two tenants, long/sensitive payload summary.
  Assert exact linkage/cardinality and fields, not merely `event_type == 'handoff'`.
- **Dependencies / future checks:** AUD-001, AUD-003, AUD-005, AUD-006, AUD-011, AUD-013; V02, V04, V09.
- **Acceptance:** source and target outcomes are visible and traceable for every lifecycle state without duplicates
  or tenant leakage; real consumers read the same ledger the delivery path writes.

## Task Coverage

Each row represents exactly one original task. Original state is copied, not amended. Evidence includes the
task anchor and actual controlling implementation/assertions. Follow-up IDs are not completion claims.

| Original ID | Original checkbox | Evidence status | Actual inspected evidence and assessment | Follow-up IDs |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Task](tasks.md#L22); all four dependencies in [API project](../../apps/api/pyproject.toml#L19) and [agent project](../../apps/agents/pyproject.toml#L14). Installation success is not implied. | AUD-018, AUD-023 |
| T002 | [X] | SUPERSEDED | [Task](tasks.md#L23); [current example](../../apps/agents/.env.example#L5), [explicit config migration](../../apps/agents/common/llm_config.py#L1), [accepted migration decision](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L30). Only the legacy environment mechanism is replaced. | AUD-024, AUD-025 |
| T003 | [X] | PARTIAL | [Task](tasks.md#L33); [DeadLetterEntry fields](../../packages/domain/src/domain/models/dead_letter_entry.py#L10) exist, but nonempty/bound/state rules and wire aliases are absent. | AUD-001, AUD-012, AUD-013 |
| T004 | [X] | IMPLEMENTED | [Task](tasks.md#L34); [import and DEAD_LETTERS dictionary](../../apps/api/app/services/state_store.py#L4) implement the specified local store. Durability is not established by this task. | AUD-006 |
| T005 | [X] | PARTIAL | [Task](tasks.md#L35); [CRUD/filter/resolve bodies](../../apps/api/app/services/dead_letter_service.py#L11) exist; tenant filtering, durable replay and immutable original payload do not. | AUD-001, AUD-006, AUD-013 |
| T006 | [X] | PARTIAL | [Task](tasks.md#L36); [publish/subscribe](../../apps/api/app/services/event_bus.py#L28) dispatch and record failures, but no-subscriber, transient classification, active composition and lifecycle are incomplete. | AUD-003, AUD-005, AUD-006, AUD-026 |
| T007 | [X] | PARTIAL | [Task](tasks.md#L52); [model](../../packages/domain/src/domain/models/model_deployment.py#L6) contains fields but not HTTPS-only, positive budgets, timeout bounds or public-safety-policy validation. | AUD-009, AUD-012 |
| T008 | [X] | IMPLEMENTED | [Task](tasks.md#L53); [Recommendation generation fields](../../packages/domain/src/domain/models/recommendation.py#L19) implement the scoped model addition. Runtime provenance/wire correctness remains separate. | AUD-011, AUD-013 |
| T009 | [X] | IMPLEMENTED | [Task](tasks.md#L54); [PublicAlert fields](../../packages/domain/src/domain/models/public_alert.py#L44) provide generation/model/safety state. Active drafting/publishing bypasses are not credited here. | AUD-002, AUD-008, AUD-013 |
| T010 | [X] | PARTIAL | [Task](tasks.md#L58); [dual-purpose client](../../apps/agents/common/llm_client.py#L144) calls a real SDK boundary, but Foundry correlation, resolved deployment and timeout handling are incomplete. | AUD-010, AUD-011 |
| T011 | [X] | PARTIAL | [Task](tasks.md#L59); [safety validator](../../apps/agents/common/content_safety.py#L95) checks length/keywords, but four language checks are only nonempty checks and provider success skips them. | AUD-008 |
| T012 | [X] | PARTIAL | [Task](tasks.md#L60); [mixin](../../apps/agents/common/llm_mixin.py#L64) implements fallbacks, not real input/final-output token bounds, whole-operation deadlines or complete failure evidence. | AUD-008, AUD-009, AUD-010, AUD-011 |
| T013 | [X] | PARTIAL | [Task](tasks.md#L64); [recommendation generation](../../apps/agents/risk_assessment/agent.py#L310) uses the mixin and fields; [compatibility path](../../apps/agents/risk_assessment/agent.py#L408) lacks actual signal context and propagated request identity. | AUD-003, AUD-004, AUD-011 |
| T014 | [X] | PARTIAL | [Task](tasks.md#L65); renamed [translator](../../apps/agents/communication/translator.py#L38) and [pipeline](../../apps/agents/communication/pipeline.py#L298) generate blocks, but [API approval](../../apps/api/app/services/recommendation_service.py#L29) bypasses them. | AUD-002, AUD-003, AUD-008, AUD-010 |
| T015 | [X] | PARTIAL | [Task](tasks.md#L69); [assertion body](../../tests/contract/test_risk_assessment_llm.py#L4) permits template/safety fallback and tests a post-appended citation, not required model success or a 95% sample. | AUD-004, AUD-023 |
| T016 | [X] | PARTIAL | [Task](tasks.md#L70); [test](../../tests/contract/test_communication_llm.py#L4) is unconditionally skipped, uses a removed class, allows fallback and has no timing assertion. | AUD-008, AUD-010, AUD-023 |
| T017 | [X] | PARTIAL | [Task](tasks.md#L71); [fallback tests](../../tests/contract/test_llm_fallback.py#L4) assert generation labels only; no two-second, zero-loss, correlation or flagged-evidence assertions. | AUD-008, AUD-010, AUD-011 |
| T018 | [X] | PARTIAL | [Task](tasks.md#L72); [test](../../tests/contract/test_token_budget.py#L4) asserts fewer characters and still reports 400 output tokens, not the configured 280-token bound or overage log. | AUD-009 |
| T019 | [X] | PARTIAL | [Task](tasks.md#L73); [test-owned logging stub](../../tests/contract/test_llm_logging.py#L9) prints expected values; no real client/header propagation is checked. | AUD-011 |
| T020 | [X] | PARTIAL | [Task](tasks.md#L89); [named gates](../../.github/workflows/ci.yml#L59), [test selection](../../.github/workflows/ci.yml#L131), [triggers](../../.github/workflows/ci.yml#L3) omit specified suites/events and lack required duration evidence. | AUD-014, AUD-023 |
| T021 | [X] | PARTIAL | [Task](tasks.md#L90); [CI benchmark step](../../.github/workflows/ci.yml#L148) exists but [hook](../../tests/benchmark/conftest.py#L85) disables regression failure under CI. | AUD-015 |
| T022 | [X] | PARTIAL | [Task](tasks.md#L91); [replacement benchmark bodies](../../tests/benchmark/test_api_performance.py#L16) measure sequential agent health, not concurrent dashboard/signal p95. | AUD-015 |
| T023 | [X] | PARTIAL | [Task](tasks.md#L107); [handoff model](../../apps/agents/common/handoffs.py#L26) has lifecycle fields but no enum/bounds/scope-transition enforcement. | AUD-005, AUD-012, AUD-013 |
| T024 | [X] | PARTIAL | [Task](tasks.md#L108); [TimelineEvent](../../packages/domain/src/domain/models/timeline_event.py#L7) adds enum values; handoff payload remains an unconstrained dictionary and actual linkage is incomplete. | AUD-012, AUD-026 |
| T025 | [X] | PARTIAL | [Task](tasks.md#L112); [high-risk builder](../../apps/agents/monitoring/agent.py#L89) and [optional delivery](../../apps/agents/monitoring/pipeline.py#L331) exist, but ingestion does not invoke them and real signal IDs are omitted. | AUD-003, AUD-004 |
| T026 | [X] | PARTIAL | [Task](tasks.md#L113); [numeric threshold builder](../../apps/agents/risk_assessment/agent.py#L462) and [pipeline escalation](../../apps/agents/risk_assessment/pipeline.py#L512) exist; no connected active consumer/store path is established. | AUD-003 |
| T027 | [X] | PARTIAL | [Task](tasks.md#L114); [retry loop](../../apps/agents/common/handoffs.py#L124) lacks circuit lookup, total-window enforcement and guaranteed durable DLQ callback. | AUD-005, AUD-006, AUD-025 |
| T028 | [X] | PARTIAL | [Task](tasks.md#L115); [timeline append](../../apps/api/app/services/event_bus.py#L60) records selected fields only on this unconnected bus, not every actual handoff with stable linkage. | AUD-026 |
| T029 | [X] | PARTIAL | [Task](tasks.md#L116); [registered reader](../../apps/api/app/api/handoffs.py#L7) filters a dictionary with incomplete success-only records; no tenant check or enum validation. | AUD-001, AUD-013, AUD-026 |
| T030 | [X] | PARTIAL | [Task](tasks.md#L120); [test](../../tests/integration/test_handoff_chain.py#L5) has one no-op handler, one event and no real agents, second edge, timing or output assertion. | AUD-003, AUD-026 |
| T031 | [X] | PARTIAL | [Task](tasks.md#L121); [tests](../../tests/integration/test_handoff_retry.py#L6) exercise exceptions with short custom windows and dummy DLQ IDs, not circuit state/300-second schedule/stored entry contents. | AUD-005, AUD-006 |
| T032 | [X] | PARTIAL | [Task](tasks.md#L137); [API image](../../apps/api/Dockerfile#L1) is multistage/non-root with a health command; code precedes install and runtime module closure/build timing remain incomplete/unverified. | AUD-018, AUD-023 |
| T033 | [X] | PARTIAL | [Task](tasks.md#L138); [agent image](../../apps/agents/Dockerfile#L1) is multistage/non-root and launches dispatcher, not the connected full workflow; dependency caching and packaging remain incomplete. | AUD-003, AUD-018, AUD-023 |
| T034 | [X] | PARTIAL | [Task](tasks.md#L139); [health](../../apps/api/app/api/health.py#L10) returns stub/healthy from configuration only; [ADR](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L63) documents the Foundry rename. | AUD-019, AUD-025 |
| T035 | [X] | CONFLICT | [Task](tasks.md#L155); [old template](../../infra/bicep/main.bicep#L3) and [active template selection](../../azure.yaml#L8) disagree on supported provisioning/configuration; partial replacement does not prove the old task's security contract. | AUD-020, AUD-021, AUD-025 |
| T036 | [X] | PARTIAL | [Task](tasks.md#L156); [action group](../../infra/bicep/monitoring.bicep#L54) links both rules but defaults to example targets with no operational validity/delivery evidence. | AUD-021 |
| T037 | [X] | PARTIAL | [Task](tasks.md#L157); [complete criterion](../../infra/bicep/monitoring.bicep#L117) uses Maximum rather than p99; no reviewed validation artifact supplied. | AUD-021, AUD-023 |
| T038 | [X] | PARTIAL | [Task](tasks.md#L173); [screenplay](../../docs/disaster-response-hub/demo/walkthrough.md#L3) names all workflow steps/placeholders, but no annotated images and timing totals five minutes rather than under five. | AUD-022, AUD-025 |
| T039 | [X] | PARTIAL | [Task](tasks.md#L174); [deck](../../docs/disaster-response-hub/demo/executive-deck.md#L11) has architecture bullets and target KPI table, not a measured annotated eight-surface evidence pack. | AUD-022 |
| T040 | [X] | PARTIAL | [Task](tasks.md#L190); [handlers](../../apps/api/app/middleware/error_handler.py#L147) cover selected exceptions but reflect details and do not share a validated UUID with middleware. | AUD-007, AUD-025 |
| T041 | [X] | PARTIAL | [Task](tasks.md#L191); [retry definition](../../apps/api/app/middleware/resilience.py#L82) is not attached to actual state/cache operations and does not classify SDK transient faults. | AUD-006 |
| T042 | [X] | PARTIAL | [Task](tasks.md#L192); [routes](../../apps/api/app/api/dead_letters.py#L20) are registered but names/defaults/scoping differ and duplicate management store is disconnected. | AUD-001, AUD-006, AUD-013 |
| T043 | [X] | PARTIAL | [Task](tasks.md#L196); [test](../../tests/contract/test_error_responses.py#L5) asserts one 422 body, not all failure modes, UUID agreement or leakage protection. | AUD-007 |
| T044 | [X] | PARTIAL | [Task](tasks.md#L197); [tests](../../tests/integration/test_retry_dead_letter.py#L5) call a local decorated function and manually insert a DLQ row; no API fault path or 90% denominator. | AUD-006, AUD-023 |
| T045 | [X] | PARTIAL | [Task](tasks.md#L213); [LoadTestResult](../../packages/domain/src/domain/models/load_test_result.py#L6) has fields but no ranges/consistency rules and is not used by the feature report. | AUD-012, AUD-016 |
| T046 | [X] | PARTIAL | [Task](tasks.md#L217); [Locust users](../../tests/load/locustfile.py#L19) issue requests but dashboard is health and required workload/concurrency/threshold execution is absent from the nightly path. | AUD-017 |
| T047 | [X] | PARTIAL | [Task](tasks.md#L218); [report body](../../tests/load/report.py#L11) is present but computes wrong quantities and passes missing evidence. | AUD-016 |
| T048 | [X] | PARTIAL | [Task](tasks.md#L228); [added schemas/paths](../../packages/schemas/openapi.yaml#L243) are authored but not synchronized with actual snake_case JSON, defaults, required fields or newer error/health variants. | AUD-013, AUD-025 |
| T049 | [X] | UNVERIFIED | [Task](tasks.md#L229); [historical execution narrative](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L7) lacks raw current-revision artifacts and does not establish all 13 SCs. | AUD-023 |
| T050 | [X] | PARTIAL | [Task](tasks.md#L230); [record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L14) cites [simulation test](../../tests/simulation/test_quickstart_rehearsals.py#L20), which manually seeds recommendation/alert and does not exercise the LLM chain. | AUD-023, AUD-024, AUD-025 |
| T051 | [X] | UNVERIFIED | [Task](tasks.md#L231); [six-pass Playwright narrative](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L11) has no linked trace/JUnit/run/revision evidence. | AUD-023 |
| T052 | [ ] | UNVERIFIED | [Task](tasks.md#L232); [explicit skip](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L17) and [current gate](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L13) do not prove credentialed execution. No cloud lookup was performed. | AUD-023, AUD-024 |
| T053 | [X] | PARTIAL | [Task](tasks.md#L233); [runbook](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md#L7) and [test body](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L17) exist but disagree about both agents and current authentication. | AUD-024 |

## Requirement Coverage

### Functional Requirements

| ID | Status | Evidence and gap | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Requirement](spec.md#L168); [Risk generation](../../apps/agents/risk_assessment/agent.py#L310) exists, but [synthetic retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) and disconnected ingestion weaken grounding. | AUD-003, AUD-004 |
| FR-002 | PARTIAL | [Requirement](spec.md#L169); [translator](../../apps/agents/communication/translator.py#L38) has six-language iteration; [approval service](../../apps/api/app/services/recommendation_service.py#L29) bypasses it. | AUD-002, AUD-003, AUD-008, AUD-010 |
| FR-003 | PARTIAL | [Requirement](spec.md#L170); [character trimming](../../apps/agents/common/llm_mixin.py#L125) is not a configurable final token limit. | AUD-009 |
| FR-004 | PARTIAL | [Requirement](spec.md#L171); [template fallback](../../apps/agents/common/llm_mixin.py#L186) exists, but active paths/deadlines/zero-loss are not uniformly enforced. | AUD-003, AUD-006, AUD-010 |
| FR-005 | PARTIAL | [Requirement](spec.md#L172); [client](../../apps/agents/common/llm_client.py#L176) loses original correlation/resolved deployment; [logging test](../../tests/contract/test_llm_logging.py#L9) is mock-owned. | AUD-011 |
| FR-006 | PARTIAL | [Requirement](spec.md#L173); [safety pass](../../apps/agents/communication/pipeline.py#L375) can erase prior failed outcome; protected flagged evidence and actual approval-path safety are incomplete. | AUD-002, AUD-008, AUD-011 |
| FR-007 | PARTIAL | [Requirement](spec.md#L177); [CI test selection](../../.github/workflows/ci.yml#L131) excludes simulation and feature-branch pushes. | AUD-014 |
| FR-008 | IMPLEMENTED | [Requirement](spec.md#L178); [ruff](../../.github/workflows/ci.yml#L59) and [TypeScript](../../.github/workflows/ci.yml#L141) are failing stages with no continue-on-error. Runtime results remain unverified. | AUD-023 |
| FR-009 | IMPLEMENTED | [Requirement](spec.md#L179); [web-build stage](../../.github/workflows/ci.yml#L144) runs the actual workspace build. | AUD-023 |
| FR-010 | IMPLEMENTED | [Requirement](spec.md#L180); [named CI stages](../../.github/workflows/ci.yml#L131) use the specified stage-name representation from [PipelineStage](data-model.md#L154). Actual PR visibility/run remains external evidence. | AUD-014, AUD-023 |
| FR-011 | PARTIAL | [Requirement](spec.md#L184); [builder](../../apps/agents/monitoring/agent.py#L89) exists but [ingest](../../apps/api/app/api/routes/signals.py#L12) never invokes dispatch. | AUD-003, AUD-004 |
| FR-012 | PARTIAL | [Requirement](spec.md#L185); [Risk threshold/handoff](../../apps/agents/risk_assessment/agent.py#L462) exists with optional delivery, not a fully connected automatic path. | AUD-003 |
| FR-013 | PARTIAL | [Requirement](spec.md#L186); [timeline append](../../apps/api/app/services/event_bus.py#L60) is incomplete/unconnected and the [API](../../apps/api/app/api/handoffs.py#L7) has no tenant boundary. | AUD-001, AUD-026 |
| FR-014 | PARTIAL | [Requirement](spec.md#L187); [retry](../../apps/agents/common/handoffs.py#L124) does not enforce circuit/window/durable routing semantics. | AUD-005, AUD-006, AUD-025 |
| FR-015 | PARTIAL | [Requirement](spec.md#L191); [API image](../../apps/api/Dockerfile#L1) has non-root startup and health command but lacks complete runtime route dependencies and execution proof. | AUD-018, AUD-019, AUD-023 |
| FR-016 | PARTIAL | [Requirement](spec.md#L192); [agent image](../../apps/agents/Dockerfile#L25) launches non-root dispatcher; intended connected worker functionality and full package closure are incomplete. | AUD-003, AUD-018, AUD-023 |
| FR-017 | PARTIAL | [Requirement](spec.md#L193); [API builder](../../apps/api/Dockerfile#L3) and [agent builder](../../apps/agents/Dockerfile#L3) use stages but copy source before dependency install. | AUD-018 |
| FR-018 | IMPLEMENTED | [Requirement](spec.md#L197); [application resources](../../infra/bicep/main.bicep#L50) and [active stack](../../infra/main.bicep#L493) define hosting/database/cache/storage/model resources; connectivity/security are separately assessed. | AUD-020, AUD-023 |
| FR-019 | CONFLICT | [Requirement](spec.md#L198); [legacy free region parameter](../../infra/bicep/main.bicep#L3) contrasts with [root AU allowlist](../../infra/main.bicep#L80) and later bounded model exception. | AUD-020, AUD-025 |
| FR-020 | PARTIAL | [Requirement](spec.md#L199); [root identities/endpoints](../../infra/main.bicep#L1007) improve wiring but registry credentials, Redis identity and broad networking remain. | AUD-020 |
| FR-021 | PARTIAL | [Requirement](spec.md#L203); [screenplay](../../docs/disaster-response-hub/demo/walkthrough.md#L3) covers headings, not complete annotated evidence and current timed acceptance. | AUD-022 |
| FR-022 | PARTIAL | [Requirement](spec.md#L204); [deck](../../docs/disaster-response-hub/demo/executive-deck.md#L17) has target KPIs and no embedded screen evidence; later deck is not an established full replacement. | AUD-022 |
| FR-023 | PARTIAL | [Requirement](spec.md#L208); [error handlers](../../apps/api/app/middleware/error_handler.py#L147) do not cover every failure safely/consistently. | AUD-007, AUD-013, AUD-025 |
| FR-024 | PARTIAL | [Requirement](spec.md#L209); [unused retry helper](../../apps/api/app/middleware/resilience.py#L82) does not wrap active repository/cache calls. | AUD-006 |
| FR-025 | PARTIAL | [Requirement](spec.md#L210); [service](../../apps/api/app/services/dead_letter_service.py#L11) stores explicit calls, but [ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12) has no permanent-failure route. | AUD-001, AUD-006 |
| FR-026 | PARTIAL | [Requirement](spec.md#L211); [action group](../../infra/bicep/monitoring.bicep#L54) is linked but real valid recipient/delivery evidence is absent. | AUD-021 |
| FR-027 | PARTIAL | [Requirement](spec.md#L212); [latency criterion](../../infra/bicep/monitoring.bicep#L117) is filled but Maximum is not p99 and validation is unverified. | AUD-021, AUD-023 |
| FR-028 | PARTIAL | [Requirement](spec.md#L216); [Locust bodies](../../tests/load/locustfile.py#L19) do not measure real dashboard under required configured concurrency. | AUD-017 |
| FR-029 | PARTIAL | [Requirement](spec.md#L217); [report math](../../tests/load/report.py#L11) does not compute the named targets. | AUD-016 |
| FR-030 | PARTIAL | [Requirement](spec.md#L218); [CI bypass](../../tests/benchmark/conftest.py#L85) and [nightly command](../../.github/workflows/nightly-load.yml#L44) do not implement blocking p95/full load. | AUD-014, AUD-015, AUD-017 |

### Success Criteria

The quickstart acceptance checks QAC-01 through QAC-13 map one-to-one to these rows in their listed order.
Source-supported mechanisms do not prove the numeric or external outcome.

| ID | Status | Actual evidence versus required measurement | Follow-up |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | [95% requirement](spec.md#L241); [T015 body](../../tests/contract/test_risk_assessment_llm.py#L4) accepts fallback and has no sample denominator; [QAC-01](quickstart.md#L106) is a proposed check. | AUD-004, AUD-023, AUD-024 |
| SC-002 | PARTIAL | [Six-language/30s requirement](spec.md#L242); [skipped test](../../tests/contract/test_communication_llm.py#L4), [sequential translator](../../apps/agents/communication/translator.py#L38); [QAC-02](quickstart.md#L107) omits timing. | AUD-002, AUD-008, AUD-010, AUD-024 |
| SC-003 | PARTIAL | [Two-second/zero-loss requirement](spec.md#L243); [immediate exception test](../../tests/contract/test_llm_fallback.py#L4) does not measure time/loss; [ignored timeout](../../apps/agents/common/foundry_chat_client.py#L397); [QAC-03](quickstart.md#L108). | AUD-006, AUD-010, AUD-023 |
| SC-004 | PARTIAL | [All suites/10min/merge gate](spec.md#L244); [CI selection](../../.github/workflows/ci.yml#L131), [descriptive protection](../../.github/branch-protection.json#L2); [QAC-04](quickstart.md#L109) lacks run evidence. | AUD-014, AUD-015, AUD-023 |
| SC-005 | PARTIAL | [Automatic chain/30s](spec.md#L245); [one no-op handoff test](../../tests/integration/test_handoff_chain.py#L5), [store-only ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12); [QAC-05](quickstart.md#L110). | AUD-003, AUD-005, AUD-026 |
| SC-006 | UNVERIFIED | [Build/run/health/non-root](spec.md#L246); [API](../../apps/api/Dockerfile#L1) and [agents](../../apps/agents/Dockerfile#L1) define intent, but no audited build/runtime artifacts; [QAC-06](quickstart.md#L111). | AUD-018, AUD-019, AUD-023 |
| SC-007 | UNVERIFIED | [What-if outcome](spec.md#L247); [templates](../../infra/bicep/main.bicep#L1) have unresolved contract gaps and no supplied reviewed what-if result; [QAC-07](quickstart.md#L112). | AUD-020, AUD-023 |
| SC-008 | PARTIAL | [Demo/paired KPIs](spec.md#L248); [placeholder screenplay](../../docs/disaster-response-hub/demo/walkthrough.md#L3), [target-only table](../../docs/disaster-response-hub/demo/executive-deck.md#L17); [QAC-08](quickstart.md#L113) reduces acceptance to existence. | AUD-022, AUD-023 |
| SC-009 | PARTIAL | [All safe errors](spec.md#L249); [one 422 test](../../tests/contract/test_error_responses.py#L5) cannot establish [all handlers](../../apps/api/app/middleware/error_handler.py#L147); [QAC-09](quickstart.md#L114). | AUD-007 |
| SC-010 | UNVERIFIED | [90% recovery](spec.md#L250); [single decorated function](../../tests/integration/test_retry_dead_letter.py#L5) has no SDK fault population or rate; [QAC-10](quickstart.md#L115). | AUD-006, AUD-023 |
| SC-011 | UNVERIFIED | [Five-minute receipt](spec.md#L251); [action-group source](../../infra/bicep/monitoring.bicep#L54) cannot establish delivery; [QAC-11](quickstart.md#L116) incorrectly substitutes configuration. | AUD-021, AUD-023 |
| SC-012 | PARTIAL | [Load/CI outcomes](spec.md#L252); [incorrect report](../../tests/load/report.py#L11), [CI bypass](../../tests/benchmark/conftest.py#L85), [nightly suppression](../../.github/workflows/nightly-load.yml#L48); [QAC-12](quickstart.md#L117). | AUD-015, AUD-016, AUD-017, AUD-023 |
| SC-013 | UNVERIFIED | [60/60 requirement](spec.md#L253); [deck](../../docs/disaster-response-hub/demo/executive-deck.md#L42) calls for future evaluation; [QAC-13](quickstart.md#L118) provides no independent result. No score assigned here. | AUD-023, AUD-025 |

### Nonfunctional Constraints

There are zero original `NFR-*` definitions. NC IDs below are audit labels for explicit unnumbered constraints,
not newly invented feature requirements.

| Audit label | Original constraint | Status and actual evidence | Follow-up |
| --- | --- | --- | --- |
| NC-01 | [Plan: dashboard <2s p95, reads <500ms, ingestion 50k/hour](plan.md#L20) | PARTIAL: [report](../../tests/load/report.py#L11) cannot measure them. | AUD-015, AUD-016, AUD-017 |
| NC-02 | [Plan: hazard visibility <60s](plan.md#L20) | UNVERIFIED: [store-only ingest](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12); no signal-to-visible assertion in original chain test. | AUD-003, AUD-026, AUD-023 |
| NC-03 | [Plan: CI <10min, benchmark <60s](plan.md#L20) | PARTIAL: [five-minute benchmark timeout](../../.github/workflows/ci.yml#L148) and no measured whole-CI bound. | AUD-014, AUD-015 |
| NC-04 | [Plan: 1,000 operators, 100+ organisations](plan.md#L22) | UNVERIFIED: [load users](../../tests/load/locustfile.py#L19) and [nightly](../../.github/workflows/nightly-load.yml#L44) do not establish representative scale. | AUD-017, AUD-023 |
| NC-05 | [Plan: six languages and human safety review](plan.md#L21) | PARTIAL: [English-only approved alert](../../apps/api/app/services/recommendation_service.py#L29), [weak language check](../../apps/agents/common/content_safety.py#L95). | AUD-002, AUD-008 |
| NC-06 | [Plan: AU-only residency and managed identity](plan.md#L21) | CONFLICT: [old free location](../../infra/bicep/main.bicep#L3), [new allowlist](../../infra/main.bicep#L80), bounded constitutional model exception. | AUD-020, AUD-025 |
| NC-07 | [Container clean <5min, incremental <2min](spec.md#L82) | UNVERIFIED: [source before dependency layer](../../apps/api/Dockerfile#L4); no build timing artifact. | AUD-018, AUD-023 |
| NC-08 | [No embedded secrets and non-root](plan.md#L21) | PARTIAL: [USER](../../apps/api/Dockerfile#L38) and [.dockerignore](../../.dockerignore#L7) support intent; no final-image scan was run. | AUD-018, AUD-023 |
| NC-09 | [Graceful degradation and failed-handoff recovery](plan.md#L21) | PARTIAL: [fallback helper](../../apps/agents/common/llm_mixin.py#L202) exists, but [placeholder DLQ callback](../../apps/agents/monitoring/pipeline.py#L64) is not durable recovery. | AUD-005, AUD-006, AUD-010 |

## Acceptance Scenario Coverage

AS IDs below identify original numbered scenarios within each user story. No scenario is collapsed into a range.

| Scenario | Status | Requirement evidence and actual implementation/assertion | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Scenario](spec.md#L30); [Risk prompt](../../apps/agents/risk_assessment/agent.py#L408) and [loose assertion](../../tests/contract/test_risk_assessment_llm.py#L4) do not establish real evidence-grounded model output. | AUD-003, AUD-004 |
| US1-AS2 | PARTIAL | [Scenario](spec.md#L31); [approval service](../../apps/api/app/services/recommendation_service.py#L29) creates English-only content; [contract test](../../tests/contract/test_communication_llm.py#L4) is skipped. | AUD-002, AUD-008 |
| US1-AS3 | PARTIAL | [Scenario](spec.md#L32); [fallback](../../apps/agents/common/llm_mixin.py#L186) labels output but receives no propagated correlation in agent call sites. | AUD-010, AUD-011 |
| US1-AS4 | PARTIAL | [Scenario](spec.md#L33); [trim](../../apps/agents/common/llm_mixin.py#L125) and [test](../../tests/contract/test_token_budget.py#L4) check characters rather than final tokens. | AUD-009 |
| US2-AS1 | PARTIAL | [Scenario](spec.md#L47); [CI triggers](../../.github/workflows/ci.yml#L3) and [suite list](../../.github/workflows/ci.yml#L131) omit required events/suites. | AUD-014 |
| US2-AS2 | PARTIAL | [Scenario](spec.md#L48); named test/lint/build stages fail, but [benchmark failure suppression](../../tests/benchmark/conftest.py#L85) is an explicit exception. Actual PR enforcement unverified. | AUD-014, AUD-015, AUD-023 |
| US2-AS3 | UNVERIFIED | [Scenario](spec.md#L49); [branch protection file](../../.github/branch-protection.json#L2) is documentation, not applied configuration or a passing PR. | AUD-023 |
| US3-AS1 | PARTIAL | [Scenario](spec.md#L63); [builder](../../apps/agents/monitoring/agent.py#L89) exists; [ingest route](../../apps/api/app/api/routes/signals.py#L12) does not start it. | AUD-003, AUD-004 |
| US3-AS2 | PARTIAL | [Scenario](spec.md#L64); [threshold builder](../../apps/agents/risk_assessment/agent.py#L462) requires an externally composed delivery path. | AUD-003 |
| US3-AS3 | PARTIAL | [Scenario](spec.md#L65); [bus timeline](../../apps/api/app/services/event_bus.py#L60) is not the ledger of all active paths; [no-op test](../../tests/integration/test_handoff_chain.py#L5) omits fields/linkage. | AUD-001, AUD-026 |
| US3-AS4 | PARTIAL | [Scenario](spec.md#L66); [retry helper](../../apps/agents/common/handoffs.py#L124) omits circuit/deadline; [failure branch](../../apps/api/app/services/event_bus.py#L88) does not update handoff listing. | AUD-005, AUD-006, AUD-026 |
| US4-AS1 | UNVERIFIED | [Scenario](spec.md#L80); [API Dockerfile](../../apps/api/Dockerfile#L1) supports security/startup intent, not an executed image health check. | AUD-018, AUD-019, AUD-023 |
| US4-AS2 | PARTIAL | [Scenario](spec.md#L81); [dispatcher entrypoint](../../apps/agents/dispatcher/__main__.py#L1) starts a server, not a proven connected incident worker/API round-trip. | AUD-003, AUD-018, AUD-023 |
| US4-AS3 | PARTIAL | [Scenario](spec.md#L82); [source-dependent install layer](../../apps/agents/Dockerfile#L4) defeats code-only dependency caching; timings unverified. | AUD-018 |
| US5-AS1 | UNVERIFIED | [Scenario](spec.md#L96); [old template](../../infra/bicep/main.bicep#L1) and [active selection](../../azure.yaml#L8) exist but no reviewed what-if outcome was supplied. | AUD-020, AUD-023 |
| US5-AS2 | PARTIAL | [Scenario](spec.md#L97); [API diagnostic](../../infra/bicep/main.bicep#L369) exists, with more [root diagnostics](../../infra/main.bicep#L1364), but full selected-stack wiring/deployment not established. | AUD-020 |
| US5-AS3 | PARTIAL | [Scenario](spec.md#L98); [root container registry credentials](../../infra/main.bicep#L1020) and public planes contradict all-inter-service-identity/least-privilege claims. | AUD-020 |
| US6-AS1 | PARTIAL | [Scenario](spec.md#L112); [screenplay timing](../../docs/disaster-response-hub/demo/walkthrough.md#L43) totals 300s; annotated current two-jurisdiction story unverified. | AUD-022 |
| US6-AS2 | PARTIAL | [Scenario](spec.md#L113); [deck targets](../../docs/disaster-response-hub/demo/executive-deck.md#L17) are not paired before/after results; no executive review record. | AUD-022, AUD-023 |
| US6-AS3 | PARTIAL | [Scenario](spec.md#L114); [eight placeholders](../../docs/disaster-response-hub/demo/walkthrough.md#L3) do not establish current annotated coverage; later deck credited only as candidate. | AUD-022 |
| US7-AS1 | PARTIAL | [Scenario](spec.md#L128); [unused helper](../../apps/api/app/middleware/resilience.py#L82) and [local-function test](../../tests/integration/test_retry_dead_letter.py#L5) are not a real dependency recovery path. | AUD-006 |
| US7-AS2 | PARTIAL | [Scenario](spec.md#L129); [error handlers](../../apps/api/app/middleware/error_handler.py#L162) can expose exception text and conflicting correlation IDs. | AUD-007 |
| US7-AS3 | UNVERIFIED | [Scenario](spec.md#L130); [action group](../../infra/bicep/monitoring.bicep#L54) provides configuration, not target receipt evidence. | AUD-021, AUD-023 |
| US7-AS4 | PARTIAL | [Scenario](spec.md#L131); [EventBus DLQ creation](../../apps/api/app/services/event_bus.py#L97) omits original request correlation/incident association, and ingestion is disconnected. | AUD-006, AUD-011 |
| US8-AS1 | PARTIAL | [Scenario](spec.md#L145); [health-as-dashboard load](../../tests/load/locustfile.py#L19) and [nightly pytest](../../.github/workflows/nightly-load.yml#L44) do not run the stated 1,000-user workload. | AUD-017 |
| US8-AS2 | PARTIAL | [Scenario](spec.md#L146); [report](../../tests/load/report.py#L11) mislabels failure count and merges measurements. | AUD-016 |
| US8-AS3 | PARTIAL | [Scenario](spec.md#L147); [CI hook](../../tests/benchmark/conftest.py#L85) deliberately does not fail on regressions. | AUD-014, AUD-015 |

### Explicit Edge Cases

| Audit ID | Original edge case | Status and evidence | Follow-up |
| --- | --- | --- | --- |
| EC-01 | Harmful/biased/nonsensical generated alert | PARTIAL: [spec](spec.md#L151), [two-keyword/language checks](../../apps/agents/common/content_safety.py#L65), [safety label flow](../../apps/agents/communication/pipeline.py#L375). | AUD-008, AUD-011 |
| EC-02 | Model throttling/backlog | PARTIAL: [spec](spec.md#L152), [legacy 429 retry](../../apps/agents/common/llm_client.py#L259), [unbounded Foundry call](../../apps/agents/common/foundry_chat_client.py#L397). | AUD-010 |
| EC-03 | Hanging CI dependency stage | PARTIAL: [spec](spec.md#L153), [unbounded principal job](../../.github/workflows/ci.yml#L14); separate jobs have longer unrelated timeouts. | AUD-014 |
| EC-04 | Yanked Python dependency on rebuild | PARTIAL: [spec](spec.md#L154), [floating project dependencies](../../apps/agents/pyproject.toml#L10), [pip install](../../apps/agents/Dockerfile#L13). | AUD-018 |
| EC-05 | Partial infrastructure deployment | UNVERIFIED: [spec](spec.md#L155), [two entrypoints](../../azure.yaml#L8); no scoped interrupted-deployment/reconciliation evidence. | AUD-020, AUD-023 |
| EC-06 | Concurrent duplicate handoff delivery | PARTIAL: [spec](spec.md#L156), [bus dispatch](../../apps/api/app/services/event_bus.py#L37), [pipeline check-then-dedup](../../apps/agents/communication/pipeline.py#L174) do not establish atomic end-to-end delivery. | AUD-005 |
| EC-07 | Unreachable action-group receiver | UNVERIFIED: [spec](spec.md#L157), [receiver definitions](../../infra/bicep/monitoring.bicep#L54) contain no delivery/secondary-escalation evidence. | AUD-021 |
| EC-08 | Contended load environment | UNVERIFIED: [spec](spec.md#L158), [report](../../tests/load/report.py#L11) records no environment/duration/concurrency quality controls. | AUD-016, AUD-017 |
| EC-09 | Unbounded dead-letter growth | PARTIAL: [spec](spec.md#L159), [global dictionary](../../apps/api/app/services/state_store.py#L23), [service](../../apps/api/app/services/dead_letter_service.py#L11) have no retention/pending-age policy. | AUD-006 |
| EC-10 | Demo stale after UI change | UNVERIFIED: [spec](spec.md#L160), [screen placeholders](../../docs/disaster-response-hub/demo/walkthrough.md#L3) and [newer runbook](../../docs/ama-presentation/AMA_Live_Demo_Instructions.md#L1) lack 003 freshness acceptance. | AUD-022 |

## Review and Checklist Claims

### Specification Checklist

CQ/RC/RD labels below are audit item IDs assigned in original order; all original checklist boxes are `[x]`.
They assess the claim itself, not a substitute rubric score.

| Item ID | Original claim | Assessment | Evidence / follow-up |
| --- | --- | --- | --- |
| CQ-01 | No implementation details | CONFLICT: inherently technical scope is acknowledged, but the absolute claim exceeds that qualification. | [Item](checklists/requirements.md#L9), [FastAPI/Docker/Bicep requirements](spec.md#L191); AUD-025. |
| CQ-02 | Focused on user value/business needs | IMPLEMENTED as authored intent, not measured benefit. | [Item](checklists/requirements.md#L11), [story rationale](spec.md#L20). |
| CQ-03 | Written for nontechnical stakeholders | CONFLICT: note changes the audience to developers/platform engineers; executive deliverable remains incomplete. | [Item/note](checklists/requirements.md#L12), [deck](../../docs/disaster-response-hub/demo/executive-deck.md#L17); AUD-022, AUD-025. |
| CQ-04 | Mandatory sections complete | IMPLEMENTED structurally. | [Item](checklists/requirements.md#L14), [spec sections](spec.md#L18), [requirements](spec.md#L162). |
| RC-01 | No NEEDS CLARIFICATION markers | IMPLEMENTED lexically; it does not resolve the contradictions found. | [Item](checklists/requirements.md#L18), [clarifications](spec.md#L8); AUD-025 for unresolved semantics. |
| RC-02 | Testable and unambiguous | CONFLICT: attempts/retries and three-versus-two handoffs disagree. | [Item](checklists/requirements.md#L19), [FR-014](spec.md#L187), [T027](tasks.md#L114), [quickstart](quickstart.md#L98); AUD-025. |
| RC-03 | Success criteria measurable | PARTIAL: numeric targets exist, but denominators, timing boundaries and measurement harnesses are incomplete. | [Item](checklists/requirements.md#L20), [SC definitions](spec.md#L241), [report math](../../tests/load/report.py#L11); AUD-016, AUD-023, AUD-025. |
| RC-04 | Technology-agnostic success criteria | PARTIAL: explicit subject-matter exceptions are documented; Azure/CI-specific measurements remain. | [Item/note](checklists/requirements.md#L21), [SC-007](spec.md#L247); AUD-025. |
| RC-05 | Acceptance scenarios defined | IMPLEMENTED as authored scenarios: all 27 reviewed above. | [Item](checklists/requirements.md#L23), [story acceptance](spec.md#L28). |
| RC-06 | Edge cases identified | IMPLEMENTED as a list: all ten reviewed above, not all handled. | [Item](checklists/requirements.md#L24), [edge list](spec.md#L149). |
| RC-07 | Scope clearly bounded | PARTIAL: delivery hygiene/deferred countries explicit, but legacy/current mechanism authority unresolved. | [Item](checklists/requirements.md#L25), [SCP](spec.md#L283), [active infra](../../azure.yaml#L8); AUD-025. |
| RC-08 | Dependencies/assumptions identified | PARTIAL: present, with incompatible region assumption and unverified consultation evidence. | [Item](checklists/requirements.md#L26), [assumptions](spec.md#L230), [ASM](spec.md#L259); AUD-025. |
| RD-01 | All FRs have clear acceptance criteria | PARTIAL: trace matrix exists but substitutes existence/configuration for outcome evidence in several SCs. | [Item](checklists/requirements.md#L30), [SC matrix](tasks.md#L383), [QAC-11](quickstart.md#L116); AUD-023, AUD-025. |
| RD-02 | Scenarios cover primary flows | IMPLEMENTED as design coverage of eight stories; current implementation gaps are separate. | [Item](checklists/requirements.md#L31), [stories](spec.md#L20). |
| RD-03 | Feature meets measurable outcomes | UNVERIFIED and contradicted by specific implementation gaps; no all-SC run evidence. | [Item](checklists/requirements.md#L32), [live skip](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L17); AUD-023. |
| RD-04 | No implementation details leak | CONFLICT: repeats CQ-01's absolute assertion despite qualified technical subject matter. | [Item](checklists/requirements.md#L33), [FR-015](spec.md#L191); AUD-025. |

The [checklist's final "All items pass" assertion](checklists/requirements.md#L37) is **UNVERIFIED as a completion
claim** and inconsistent with the explicit PARTIAL/CONFLICT items above (AUD-023, AUD-025).

### Constitution Gates in the Plan

All fourteen source items are labelled PASS. IDs distinguish the pre-research and post-design versions individually.

| Gate ID | Claim | Assessment and actual evidence | Follow-up |
| --- | --- | --- | --- |
| PRE-01 | [Life Safety First](plan.md#L30) | PARTIAL: [pending-approval publication](../../apps/api/app/services/public_alert_service.py#L48) contradicts assured human review. | AUD-002, AUD-008 |
| PRE-02 | [Clear agent roles](plan.md#L31) | PARTIAL: [builders](../../apps/agents/monitoring/agent.py#L89) are typed but [ingestion](../../apps/api/app/api/routes/signals.py#L12) is unconnected. | AUD-003 |
| PRE-03 | [Provenance and freshness](plan.md#L32) | PARTIAL: [synthetic evidence fallback](../../apps/agents/risk_assessment/pipeline.py#L169) and [lost correlation](../../apps/agents/common/llm_client.py#L176). | AUD-004, AUD-011 |
| PRE-04 | [Privacy/security/region](plan.md#L33) | PARTIAL: non-root declarations exist; [unscoped DLQ](../../apps/api/app/services/dead_letter_service.py#L41) and [free location](../../infra/bicep/main.bicep#L3) contradict full assurance. | AUD-001, AUD-020 |
| PRE-05 | [Multilingual accessibility](plan.md#L34) | PARTIAL: [translator](../../apps/agents/communication/translator.py#L38) exists, [language detection](../../apps/agents/common/content_safety.py#L95) insufficient. | AUD-008, AUD-022 |
| PRE-06 | [Azure/AU cloud platform](plan.md#L35) | PARTIAL: Azure resources authored; [region input](../../infra/bicep/main.bicep#L3) is not enforced in the documented old path. | AUD-020, AUD-025 |
| PRE-07 | [Quality/operational readiness](plan.md#L36) | PARTIAL: [CI omitted suites](../../.github/workflows/ci.yml#L131), [benchmark bypass](../../tests/benchmark/conftest.py#L85). | AUD-014, AUD-015, AUD-023 |
| POST-01 | [Safety/provenance/failure recovery](plan.md#L119) | PARTIAL: model fields exist; [approval bypass](../../apps/api/app/services/recommendation_service.py#L29) and [memory DLQ](../../apps/api/app/services/state_store.py#L23) remain. | AUD-002, AUD-006 |
| POST-02 | [All transitions auditable](plan.md#L120) | PARTIAL: [bus success/failure records](../../apps/api/app/services/event_bus.py#L46) lack complete lifecycle linkage and active-path coverage. | AUD-026 |
| POST-03 | [Transparent model calls/timeline](plan.md#L121) | PARTIAL: [metadata extraction](../../apps/agents/common/llm_client.py#L193) misidentifies Foundry deployment; no active `llm_call` timeline writer found. | AUD-011, AUD-026 |
| POST-04 | [HTTPS validation/tenant privacy](plan.md#L122) | CONFLICT: [HttpUrl-only model](../../packages/domain/src/domain/models/model_deployment.py#L6) is not HTTPS-only; [DLQ service](../../apps/api/app/services/dead_letter_service.py#L41) does not scope tenant. | AUD-001, AUD-012, AUD-020 |
| POST-05 | [Six languages and fallback support](plan.md#L123) | PARTIAL: [generic fallback](../../apps/agents/communication/translator.py#L207) is English for every language without templates; API bypasses translator. | AUD-002, AUD-008 |
| POST-06 | [All resources Azure/AU](plan.md#L124) | PARTIAL: Azure-only resource kinds exist, but [old location](../../infra/bicep/main.bicep#L3) lacks restriction and live provisioning is unverified. | AUD-020, AUD-023 |
| POST-07 | [Test-first and full gates](plan.md#L125) | UNVERIFIED as execution/review: [no-op chain test](../../tests/integration/test_handoff_chain.py#L5) and [live skip](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L17) cannot establish gate passage. | AUD-023, AUD-025 |

[No constitution violations](plan.md#L115) is not supported as a blanket current-implementation claim. No reviewer
identity, reviewed revision, or authentic human approval artifact accompanies these PASS labels in this feature.
This audit does not infer that the historical design review never occurred; its execution is UNVERIFIED (AUD-023).

### Research Decisions and Design Contracts

The research records describe decisions, not package execution or deployment evidence.

| Item | Status | Concrete assessment | Follow-up |
| --- | --- | --- | --- |
| R-01 SDK/dual model | SUPERSEDED for SDK mechanism | [Decision](research.md#L3), [Foundry replacement](../../apps/agents/common/llm_client.py#L1); dual purpose still required and implemented in configuration. | AUD-011, AUD-024 |
| R-02 Shared mixin | PARTIAL | [Decision](research.md#L13), [mixin](../../apps/agents/common/llm_mixin.py#L16); guarantees incomplete. | AUD-008, AUD-009, AUD-010, AUD-011 |
| R-03 Rule-based safety | PARTIAL | [Decision](research.md#L22), [validator](../../apps/agents/common/content_safety.py#L95); real language validation missing. | AUD-008 |
| R-04 Tenacity retry | PARTIAL | [Decision](research.md#L31), [unattached decorator](../../apps/api/app/middleware/resilience.py#L82). | AUD-006 |
| R-05 In-memory event bus | PARTIAL | [Decision](research.md#L40), [bus](../../apps/api/app/services/event_bus.py#L28); in-memory broker is allowed, but unconnected dispatch is not. | AUD-003, AUD-005, AUD-026 |
| R-06 Locust load | PARTIAL | [Decision](research.md#L49), [workload](../../tests/load/locustfile.py#L19); wrong dashboard and missing required execution. | AUD-017 |
| R-07 pytest-benchmark gate | PARTIAL | [Decision](research.md#L59), [CI bypass](../../tests/benchmark/conftest.py#L85). | AUD-015 |
| R-08 Multistage images | PARTIAL | [Decision](research.md#L68), [builder ordering](../../apps/api/Dockerfile#L3); stages exist, caching/reproducibility incomplete. | AUD-018 |
| R-09 Main plus monitoring | CONFLICT | [Decision](research.md#L77), [azd root choice](../../azure.yaml#L8); documented old and active paths diverge. | AUD-020, AUD-025 |
| R-10 Annotated screenplay | PARTIAL | [Decision](research.md#L87), [placeholders](../../docs/disaster-response-hub/demo/walkthrough.md#L3); screenplay option accepted, not fully delivered. | AUD-022 |
| R-11 Email/webhook action groups | PARTIAL | [Decision](research.md#L96), [targets](../../infra/bicep/monitoring.bicep#L54); configured examples are not operational receipts. | AUD-021 |
| DM-01 ModelDeployment | PARTIAL | [Rules](data-model.md#L5), [runtime](../../packages/domain/src/domain/models/model_deployment.py#L6): fields, not bounds/security enforcement. | AUD-009, AUD-012 |
| DM-02 AgentHandoffEvent | PARTIAL | [Rules](data-model.md#L35), [runtime](../../apps/agents/common/handoffs.py#L26): missing transition/scope enforcement. | AUD-005, AUD-012, AUD-026 |
| DM-03 DeadLetterEntry | PARTIAL | [Rules](data-model.md#L83), [runtime](../../packages/domain/src/domain/models/dead_letter_entry.py#L10): missing nonempty/tenant boundary; transition partly in service. | AUD-001, AUD-006, AUD-012 |
| DM-04 LoadTestResult | PARTIAL | [Rules](data-model.md#L117), [runtime](../../packages/domain/src/domain/models/load_test_result.py#L6): unchecked relational values and unused report model. | AUD-012, AUD-016 |
| DM-05 PipelineStage | IMPLEMENTED as CI representation | [Rules](data-model.md#L154), [named stages](../../.github/workflows/ci.yml#L131); no separate persisted model required. | AUD-014, AUD-023 for execution |
| DM-06 ContainerDefinition | PARTIAL | [Rules](data-model.md#L175), [API](../../apps/api/Dockerfile#L1), [agents](../../apps/agents/Dockerfile#L1): declared security with unverified image contents/runtime. | AUD-018 |
| DM-07 AlertActionGroup | PARTIAL | [Rules](data-model.md#L200), [module](../../infra/bicep/monitoring.bicep#L54): no target validation or receipt evidence. | AUD-021 |
| DM-08 Recommendation modification | PARTIAL | [Rules](data-model.md#L230), [model](../../packages/domain/src/domain/models/recommendation.py#L19): fields exist, active generation/serialization provenance gaps. | AUD-004, AUD-011, AUD-013 |
| DM-09 TimelineEvent modification | PARTIAL | [Rules](data-model.md#L241), [model](../../packages/domain/src/domain/models/timeline_event.py#L7), [writer](../../apps/api/app/services/event_bus.py#L60): incomplete actual-event coverage. | AUD-026 |
| DM-10 PublicAlert modification | PARTIAL | [Rules](data-model.md#L256), [API alert creation](../../apps/api/app/services/recommendation_service.py#L29): does not populate six-language LLM draft. | AUD-002, AUD-008, AUD-013 |
| DM-11 EventBus modification | PARTIAL | [Rules](data-model.md#L267), [dispatch](../../apps/api/app/services/event_bus.py#L37): error classification, state and connection gaps. | AUD-003, AUD-005, AUD-006 |
| API-01 GET dead-letters | PARTIAL | [Contract](contracts/openapi-addendum.yaml#L17), [route](../../apps/api/app/api/dead_letters.py#L20): naming/default/enums/tenancy mismatch. | AUD-001, AUD-013 |
| API-02 Resolve dead-letter | PARTIAL | [Contract](contracts/openapi-addendum.yaml#L68), [route](../../apps/api/app/api/dead_letters.py#L41): body alias, persona and replay semantics mismatch. | AUD-001, AUD-006, AUD-013 |
| API-03 GET handoffs | PARTIAL | [Contract](contracts/openapi-addendum.yaml#L107), [reader](../../apps/api/app/api/handoffs.py#L7): incomplete record/status/scoping. | AUD-001, AUD-013, AUD-026 |
| API-04 GET health | PARTIAL | [Contract](contracts/openapi-addendum.yaml#L132), [health](../../apps/api/app/api/health.py#L20): source shape exists with documented prefix/provider changes, configured does not imply healthy. | AUD-013, AUD-019 |
| API-05 ErrorResponse | PARTIAL | [Contract](contracts/openapi-addendum.yaml#L163), [handler](../../apps/api/app/middleware/error_handler.py#L147): correlation/leak/exception coverage gaps. | AUD-007, AUD-013 |
| API-06 DeadLetterEntry schema | PARTIAL | [Published schema](../../packages/schemas/openapi.yaml#L711), [runtime model](../../packages/domain/src/domain/models/dead_letter_entry.py#L10): casing/enums/bounds mismatch. | AUD-012, AUD-013 |
| API-07 AgentHandoffEvent schema | PARTIAL | [Published schema](../../packages/schemas/openapi.yaml#L755), [stored dictionary](../../apps/api/app/services/event_bus.py#L48): required confidence absent. | AUD-012, AUD-013, AUD-026 |
| API-08 ModelDeployment schema | PARTIAL | [Published schema](../../packages/schemas/openapi.yaml#L803), [runtime](../../packages/domain/src/domain/models/model_deployment.py#L6): casing and validation mismatch. | AUD-012, AUD-013 |
| API-09 Recommendation addendum | PARTIAL | [Published schema](../../packages/schemas/openapi.yaml#L513), [dashboard model_dump](../../apps/api/app/services/dashboard_service.py#L48): snake_case generation/token keys. | AUD-013 |
| API-10 PublicAlert addendum | PARTIAL | [Published schema](../../packages/schemas/openapi.yaml#L656), [publish dump](../../apps/api/app/api/routes/alerts.py#L35): snake_case fields and differing active agent model. | AUD-013 |
| API-11 TimelineEvent addition | PARTIAL | [Published schema](../../packages/schemas/openapi.yaml#L840), [runtime](../../packages/domain/src/domain/models/timeline_event.py#L7): enum added, wire/typed payload assurance incomplete. | AUD-012, AUD-013, AUD-026 |

### Original Completion Checkpoints and Execution Records

| Claim ID | Claim | Assessment and evidence | Follow-up |
| --- | --- | --- | --- |
| CP-FOUNDATION | Foundation ready | PARTIAL: [tasks](tasks.md#L38), [unscoped feature store](../../apps/api/app/services/dead_letter_service.py#L41). | AUD-001, AUD-006 |
| CP-US1 | LLM outputs with safety/fallback complete | PARTIAL: [tasks](tasks.md#L75), [skipped communication test](../../tests/contract/test_communication_llm.py#L4). | AUD-003, AUD-008, AUD-010, AUD-011 |
| CP-US2 | All PR gates block failures | PARTIAL: [tasks](tasks.md#L93), [CI suppression](../../tests/benchmark/conftest.py#L85). | AUD-014, AUD-015 |
| CP-US3 | Automatic chaining/audit complete | PARTIAL: [tasks](tasks.md#L123), [no-op chain assertion](../../tests/integration/test_handoff_chain.py#L5). | AUD-003, AUD-026 |
| CP-US4 | Images build within budgets and pass health | UNVERIFIED: [tasks](tasks.md#L141), [Dockerfile](../../apps/api/Dockerfile#L1), no linked build logs. | AUD-018, AUD-023 |
| CP-US5 | AU managed-identity what-if passed | UNVERIFIED: [tasks](tasks.md#L159), [old template](../../infra/bicep/main.bicep#L3), no reviewed output. | AUD-020, AUD-023 |
| CP-US6 | Demo evaluator materials complete | PARTIAL: [tasks](tasks.md#L176), [placeholder screens](../../docs/disaster-response-hub/demo/walkthrough.md#L3). | AUD-022 |
| CP-US7 | Structured errors/retry/DLQ complete | PARTIAL: [tasks](tasks.md#L199), [unused retry](../../apps/api/app/middleware/resilience.py#L82), [single 422 test](../../tests/contract/test_error_responses.py#L5). | AUD-006, AUD-007 |
| CP-US8 | Load targets validated | PARTIAL: [tasks](tasks.md#L220), [invalid report](../../tests/load/report.py#L11). | AUD-016, AUD-017 |
| HIST-01 | 31 Python tests PASS | UNVERIFIED historical execution: [record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L8) has no raw output/revision; not a current test result. | AUD-023 |
| HIST-02 | Six Playwright tests PASS | UNVERIFIED historical execution: [record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L11) has no trace/JUnit/run artifact. | AUD-023 |
| HIST-03 | Quickstart simulation PASS | PARTIAL: [record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L14); [test](../../tests/simulation/test_quickstart_rehearsals.py#L58) inserts recommendation/alert manually. | AUD-023, AUD-024 |
| HIST-04 | Live rehearsal SKIP | IMPLEMENTED as an honest authored limitation; successful live execution remains UNVERIFIED. [Record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L17), [gate](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L13). | AUD-024 |
| HIST-05 | Serial Playwright needed locally | UNVERIFIED operational observation without raw timing/contention evidence. [Note](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L25). | AUD-023 |
| LIVE-01 | Both agents pass real rehearsal | CONFLICT: [runbook expectation](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md#L28) versus [Risk-only body](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L17). | AUD-024 |
| LIVE-02 | API-key prerequisites match runtime | CONFLICT: [runbook](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md#L7) versus [AAD client](../../apps/agents/common/llm_client.py#L107) and Foundry config. | AUD-024 |
| DEMO-01 | Major UI screenshots exist | PARTIAL: [walkthrough placeholders](../../docs/disaster-response-hub/demo/walkthrough.md#L3); later deck contains media but lacks an accepted per-screen 003 mapping. | AUD-022 |
| DEMO-02 | Before/after KPI comparison | UNVERIFIED measurement: [target deck](../../docs/disaster-response-hub/demo/executive-deck.md#L17), [sample KPI CSV](../../docs/disaster-response-hub/evaluation/kpi-template.csv#L1). Sample rows are not independently attributable exercise evidence. | AUD-022, AUD-023 |
| DEMO-03 | Under-five-minute story | CONFLICT: [duration entries](../../docs/disaster-response-hub/demo/walkthrough.md#L43) total exactly 300 seconds. | AUD-022, AUD-025 |
| DEMO-04 | Executive/nontechnical comprehension | UNVERIFIED: [survey instrument](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L23) is blank; [UX threshold](../../docs/disaster-response-hub/evaluation/ux-rubric.md#L18) is a procedure, not responses. | AUD-022, AUD-023 |
| DEMO-05 | Paired response/evacuation/resource/UX outcomes | UNVERIFIED: [baseline procedures](../../docs/disaster-response-hub/evaluation/baseline-metrics.md#L7) define measurement; no signed paired 003 pack. CSV example lead-time improvements are 3.5h and 5h, not 24h. | AUD-022, AUD-023 |
| OPS-01 | Scheduled rehearsals/drills occurred | UNVERIFIED: [schedule](../../docs/disaster-response-hub/evaluation/exercise-schedule.md#L7) lists owners/cadence, not completed executions. | AUD-023 |

### Quickstart Instructions and Rehearsal

The phase item IDs below identify each original numbered instruction explicitly. They are authored instructions,
not evidence that test-first development or validation was performed.

| Instruction IDs | Assessment | Evidence / follow-up |
| --- | --- | --- |
| QA-1, QA-2, QA-3, QA-4, QA-5, QA-6 | PARTIAL implementation; test-first chronology UNVERIFIED. | [Phase A](quickstart.md#L33), [weak LLM tests](../../tests/contract/test_risk_assessment_llm.py#L4), [skipped Communication](../../tests/contract/test_communication_llm.py#L4); AUD-004, AUD-008, AUD-009, AUD-010, AUD-023. |
| QB-1, QB-2, QB-3, QB-4, QB-5 | PARTIAL: actual bus/helper exists, automatic chain and retries/timeline acceptance absent. | [Phase B](quickstart.md#L42), [chain test](../../tests/integration/test_handoff_chain.py#L5); AUD-003, AUD-005, AUD-026. |
| QC-1, QC-2, QC-3, QC-4 | PARTIAL: named stages exist, triggers/benchmark and actual PR restriction unproven. | [Phase C](quickstart.md#L50), [CI](../../.github/workflows/ci.yml#L3); AUD-014, AUD-015, AUD-023. |
| QD-1, QD-2, QD-3, QD-4 | PARTIAL/UNVERIFIED execution: Dockerfiles exist; root context is required, contrary to QD-3. | [Phase D](quickstart.md#L57), [azd context](../../azure.yaml#L33), [API Dockerfile](../../apps/api/Dockerfile#L3); AUD-018, AUD-023. |
| QE-1, QE-2, QE-3, QE-4 | PARTIAL/UNVERIFIED deployment: templates/rules authored; no valid what-if or target receipt evidence. | [Phase E](quickstart.md#L64), [monitoring](../../infra/bicep/monitoring.bicep#L117); AUD-020, AUD-021, AUD-023. |
| QF-1, QF-2, QF-3, QF-4 | PARTIAL: error/retry tests do not exercise all actual boundaries or automatic failure capture. | [Phase F](quickstart.md#L71), [test](../../tests/integration/test_retry_dead_letter.py#L5); AUD-006, AUD-007. |
| QG-1, QG-2, QG-3 | PARTIAL/CONFLICT: 100-user smoke command lacks specified file/host and is not the 1,000-user acceptance workload. | [Phase G](quickstart.md#L78), [report](../../tests/load/report.py#L11); AUD-016, AUD-017, AUD-025. |
| QH-1, QH-2, QH-3 | PARTIAL: screenplay/deck outlines exist, current annotated screen/KPI pack does not. | [Phase H](quickstart.md#L84), [demo](../../docs/disaster-response-hub/demo/walkthrough.md#L3); AUD-022. |

| Rehearsal item | Status | Evidence and gap | Follow-up |
| --- | --- | --- | --- |
| QR-01 | PARTIAL | [Two-jurisdiction bushfire seed](quickstart.md#L92); [recorded test](../../tests/simulation/test_quickstart_rehearsals.py#L32) uses a single-jurisdiction weather/flood flow. | AUD-024 |
| QR-02 | PARTIAL | [Three sources](quickstart.md#L93); [test POST](../../tests/simulation/test_quickstart_rehearsals.py#L34) supplies one authoritative signal. | AUD-024 |
| QR-03 | PARTIAL | [Automatic Monitoring escalation](quickstart.md#L94); [ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12) only stores. | AUD-003 |
| QR-04 | PARTIAL | [Real Risk output](quickstart.md#L95); [test seed](../../tests/simulation/test_quickstart_rehearsals.py#L59) supplies explanation directly. | AUD-004, AUD-024 |
| QR-05 | PARTIAL | [Second automatic edge](quickstart.md#L96); [no-op chain test](../../tests/integration/test_handoff_chain.py#L11) has no Communication invocation. | AUD-003, AUD-024 |
| QR-06 | PARTIAL | [Six draft languages](quickstart.md#L97); [approval service](../../apps/api/app/services/recommendation_service.py#L29) builds only en-AU. | AUD-002, AUD-008, AUD-024 |
| QR-07 | CONFLICT | [Three handoffs naming two](quickstart.md#L98); [single-event assertion](../../tests/integration/test_handoff_chain.py#L30) establishes neither count. | AUD-025, AUD-026 |
| QR-08 | PARTIAL | [Failure/fallback timeline](quickstart.md#L99); [fallback tests](../../tests/contract/test_llm_fallback.py#L4) omit timeline and the rehearsal does not simulate this step. | AUD-010, AUD-024, AUD-026 |
| QR-09 | PARTIAL | [Approve/publish under 30s](quickstart.md#L100); [rehearsal approval](../../tests/simulation/test_quickstart_rehearsals.py#L80) uses seeded output with no timing or alert-specific approval assertion. | AUD-002, AUD-010, AUD-024 |

### Later Governance Amendments

These do not silently expand this audit into country deployment or new rubric grading.

| Item | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| ASM-001 | IMPLEMENTED as scope declaration | [AU-v1/open risk](spec.md#L259) and [country deferral](spec.md#L283) authored; not a claim of deployed AU compliance. | AUD-020 for implementation |
| ASM-002 | UNVERIFIED | [Consultation claim](spec.md#L260) names product-owner/QA involvement, but no feature-local attributable consultation record. No new delegation performed to fabricate one. | AUD-025 |
| ASM-003 | IMPLEMENTED as convention reference | [Reference](spec.md#L261) adopts existing numbering/persona schema; inherited unrelated FR references elsewhere need correction. | AUD-025 |
| PER-001 | UNVERIFIED validation | [Validated AIIMS personas](spec.md#L267) are cross-references, not feature-specific human validation evidence. | AUD-025 |
| PER-002 | UNVERIFIED validation | [Validated technical actors](spec.md#L268) names a catalogue, not proof of completed review of this implementation. | AUD-025 |
| PER-003 | IMPLEMENTED as explicit placeholder | [Non-AU placeholder/preconditions](spec.md#L269) is honest deferral, not a validated persona set. | AUD-025 for preserving boundary |
| HYP-001 | UNVERIFIED; referenced stub MISSING | [Hypothesis](spec.md#L275) points to absent `HYP-HYP-001.md`; [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1) is portfolio structural evidence, not this implementation's measured score delta. | AUD-025, AUD-023 |
| SCP-001 | IMPLEMENTED as deferral | [Country prerequisites](spec.md#L283) remain out of scope; their satisfaction was not asserted or checked through cloud/human operations. | AUD-025 for trace maintenance |
| SCP-002 | PARTIAL | [No constitutional changes here](spec.md#L284) is explicit, but location/approval tensions still require documented resolution. | AUD-002, AUD-020, AUD-025 |
| SCP-003 | IMPLEMENTED as authority rule | [Defers-to 018/008](spec.md#L285) does not name 004-rubric-gap-closure as a replacement; behavioral obligations remain unless explicitly retired. | AUD-025 |
| SCP-004 | IMPLEMENTED as meta classification | [Meta scope](spec.md#L286) and [shared ledger row](../shared/feature-value-ledger.md#L16) classify delivery hygiene, not implementation success. | AUD-025 for stale wording only |

## Future Validation Instructions

**Nothing in this section was executed.** All product, test, build, browser, cloud, or human operations need a
separately authorised developer/tester session. The current audit only validates this Markdown document.
Use the repository's current dependency workflow; do not copy legacy API keys into source. Capture the revision,
environment, fixture identities, tool versions, commands, skipped cases, and raw artifacts for each future check.

| ID | Prerequisites and future command/procedure | Expected result |
| --- | --- | --- |
| V01 | Python 3.12 with existing API/agent test dependencies, no real model endpoints in hermetic tests. `python -m pytest tests/contract/test_risk_assessment_llm.py tests/contract/test_communication_llm.py tests/contract/test_llm_fallback.py tests/contract/test_token_budget.py tests/contract/test_llm_logging.py tests/contract/test_error_responses.py tests/contract/test_dead_letter_api.py tests/unit/test_content_safety_pipeline.py tests/unit/test_communication_translator.py -q` after strengthening these bodies. | Positive/negative/edge assertions above pass; no unconditional skip hides required Communication behavior; SDK/network fakes do not replace domain logic or write expected logs. |
| V02 | Same hermetic prerequisites, fake retry clocks, clean tenant-scoped stores. `python -m pytest tests/integration/test_handoff_chain.py tests/integration/test_handoff_retry.py tests/integration/test_retry_dead_letter.py tests/simulation/test_quickstart_rehearsals.py -q`. | Actual connected API/agent chain, retry, DLQ and approval boundaries pass; no direct pre-seeding of expected recommendations/drafts. |
| V03 | Corrected benchmark/report harness, stable runner and reviewed baselines; proposed report-math fixture tests in existing test area. `python -m pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q` is the current command to repair/verify, not proof it is already a <60s gate. | Required p95/SLO failures exit nonzero including under `CI=true`; missing/empty evidence fails; all report units/formulas are correct. |
| V04 | API running only in an authorised test session; runtime OpenAPI snapshot versus [published schema](../../packages/schemas/openapi.yaml), TestClient-based request/response schema assertions. Use V01/V02 plus proposed expanded contract cases in those existing files. | Canonical aliases/defaults/enums/statuses/required fields and tenant errors agree; route list contains no duplicate conflicting GET DLQ handlers. |
| V05 | Python and current pinned Node/pnpm from [CI](../../.github/workflows/ci.yml#L20); dependency installation separately authorised. `ruff check apps tests packages`; `pnpm --filter ./apps/web exec tsc --noEmit`; `pnpm --filter ./apps/web build`; full selected hermetic pytest suites after trigger/suite repair. | Each required failure blocks; all originally required suites run on agreed events. Current-revision CI logs demonstrate duration and actual required-check enforcement. |
| V06 | Authorised isolated staging, seeded representative incident/organisations, approved load credentials/capacity, corrected scenario/runner and safe output directory. Future driver: `locust -f tests/load/locustfile.py DashboardUser BurstIngestionUser --headless --users 1000 --spawn-rate 100 --run-time 10m --host <approved-staging-url> --csv <approved-output-prefix>`, with concurrency/arrival mix calibrated before use. Run corrected report CLI once introduced (proposed CLI, not currently implemented). | Steady-state 1,000 operators, dashboard p95 <2,000ms, read p95 <500ms, successful signals/hour >=50,000, error rate <1%; raw data and scenario names retained; controlled regression fails. |
| V07 | Authorised Docker daemon, resolved reproducible dependencies, isolated network, no embedded credentials. Local ARM64 only: `docker build --platform linux/arm64 -f apps/api/Dockerfile -t drh-api:audit .`; `docker build --platform linux/arm64 -f apps/agents/Dockerfile -t drh-agents:audit .`. Then inspect/run images in the separately authorised session and repeat after a code-only change. | Non-root UID, correct health and real workflow routes, agent/API reachability, expected assets, no secret-bearing layers, dependency-cache reuse, <5min clean/<2min incremental evidence. |
| V08 | Bicep CLI and approved module versions; authorised infrastructure reviewer resolves AUD-020 first. Offline future checks: `bicep build infra/main.bicep --stdout` and the retained old entrypoint if still supported. Use the existing [what-if procedure](quickstart.md#L69) only in a separately authorised Azure session with explicit subscription, AU resource group and reviewed parameters. | No compile diagnostics, policy violations or unexpected non-AU data resources; identity bindings/endpoints/diagnostics and action-group criteria match the selected deployment. |
| V09 | Explicit authority for credentialed/cloud/human verification. Execute repaired [live rehearsal](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md), genuine CI PR checks, approved what-if, notification breach/receipt exercise, paired performance/KPI study, and independent human/rubric acceptance as needed. No secrets in artifacts. | Each measured/external SC has revision-bound evidence with denominators, timestamps, approvals and limitations; unperformed items remain UNVERIFIED. |
| V10 | Documentation-only authoring/review; current UI/diagram assets and legitimate owner decisions. Check local links, per-task/per-requirement coverage, nine rehearsal items, 16 checklist items, 14 plan gates, and all declared deferrals. | Internally consistent contracts, labelled targets versus results, current annotated demo, all referenced evidence real, no retroactive task checkbox edits. |

Supplementary package semantics were checked against
[pytest-benchmark comparison documentation](https://pytest-benchmark.readthedocs.io/en/latest/comparing.html),
[benchmark usage](https://pytest-benchmark.readthedocs.io/en/latest/usage.html), and
[Locust headless execution](https://docs.locust.io/en/stable/running-without-web-ui.html).
These distinguish recorded statistics from explicit failing gates. A Google lookup returned an interstitial and
one older Locust statistics URL returned 404; neither was used as evidence.

## Document Validation

The first action immediately after the report was written was the required document-only validation, in parallel
with editor diagnostics. It identified two out-of-bounds line anchors, an unescaped Markdown table pipe, and a
missing final newline. Only this report was corrected; the repeated document check passed and editor diagnostics
reported no errors. A final reference-precision pass corrected adjacent-section anchors and named reusable test helpers.

- Original task coverage: **53/53**, exactly one row per ID, original checkboxes unchanged.
- Requirement/scenario coverage: **30/30 FRs**, **13/13 SCs**, **27/27 acceptance scenarios**; zero original NFR IDs.
- Remediation: **26 unique AUD tasks**, all unchecked, with defined follow-up references.
- Local links: existing relative targets and in-bounds single-line source anchors checked; proposed new paths are labelled.
- Formatting: editor diagnostics checked, Markdown table defect corrected, final newline present.
- Scope: document checks only. **No product tests/builds, cloud operations, or remediation were executed.**

All remediation remains unchecked and unexecuted.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 003 only. Three parallel technical reviews inspected the
current runtime, CI/infrastructure, and evidence/contract surfaces. No source edit was required for the reviewed
handoff lifecycle because the current tree already contains the remediation implementation: tenant-bucketed
handoffs, confidence and correlation fields, attempt/retry counters, payload redaction, timeline linkage,
dead-letter linkage, authenticated protected routes, and dashboard projection data.

| Area | Current result | Validation / limitation |
| --- | --- | --- |
| AUD-001 / AUD-003 / AUD-005 / AUD-006 | Current source and tests contain tenant-scoped EventBus records, two-edge signal workflow chaining, bounded attempt/retry fields, failure dead-lettering, and timeline linkage. | Source inspection plus existing handoff integration coverage; full API contract execution is blocked by the unrelated missing `IngestionProcessingResult` import in `apps/api/app/services/ingestion/community_ingestion.py`. |
| AUD-013 / AUD-026 | Handoff API exposes status filtering and contract fields; `DashboardService._handoff_projection` consumes the same tenant-scoped ledger and exposes status counts, recent records, retry state, and linkage IDs. | Existing wire-contract tests cover delivered/failed records; 5 focused tests passed, 7 API contract tests errored during collection on the unrelated import defect. |
| AUD-019 / AUD-022–025 | Review agents found the health, demo/evidence validators, live-gate opt-in, and consistency tooling source-complete; the current evidence remains execution-, human-, deployment-, or measurement-gated. | Static source evidence only; no live Foundry rehearsal, load run, notification receipt, human acceptance, or deployment proof was created. |
| AUD-020 / AUD-021 | Legacy Bicep topology and monitoring receiver/p99 concerns remain governance- or policy-blocked and were not changed without current policy/owner authorization. | Keep open; what-if, policy, deployment, receiver delivery, and Azure inventory evidence remain UNVERIFIED. |

No product or infrastructure edits were made in this pass because the actionable current handoff implementation was
already present and the remaining gaps require unrelated import repair, governance decisions, or external/live proof.

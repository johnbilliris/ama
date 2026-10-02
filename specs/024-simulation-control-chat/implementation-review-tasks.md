# Static Implementation Audit: Simulation Control & Chat Orchestration

## Scope and Evidence Boundary

- Review date: **2026-09-14**.
- Assigned specification: **024-simulation-control-chat only**.
- Expected source revision: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`, verified with read-only Git metadata.
- Scoped `git diff --name-status HEAD` found no tracked changes in reviewed source/configuration/spec
  inputs; `git ls-files --others --exclude-standard` found only this new report in those paths.
- Method: static inspection of source, configuration, test assertions, and authored local evidence.
  No product tests, builds, imports, servers, browsers, package installation, cloud operations, or approvals
  were executed. Commands below are future instructions, not execution evidence.
- Only this report is modified. No other implementation-review report is an input. No delegation,
  source/specification/task edits, index changes, branch creation, or commits are part of this review.
- The original task list contains **no checkbox markers**. Task coverage preserves this as `none`;
  it does not manufacture checked or unchecked implementation states.
- Status vocabulary follows the [Review Contract](../001-spec-implementation-audit/README.md#L11):
  `IMPLEMENTED`, `PARTIAL`, `MISSING`, `CONFLICT`, `UNVERIFIED`, `SUPERSEDED`.
  `IMPLEMENTED` supports authored source behavior only, not successful execution or deployment.

## Complete Local Inputs

The complete contents of the following local documents were inspected:

- [Specification and embedded amendments](spec.md).
- [Original tasks](tasks.md).
- [Implementation plan](plan.md).
- [Research](research.md).
- [Data model](data-model.md).
- [Chat contract](contracts/simulation-chat-api.md).
- [Control contract](contracts/simulation-control-api.md).
- [Quickstart](quickstart.md).
- [Requirements checklist](checklists/requirements.md).
- [Safety and readiness checklist](checklists/simulation-safety.md).
- [Authored cohort review](review-report.md).
- [Authored analysis report](analysis-report.md).

Review rules: [code-review instructions](../../.github/instructions/code-review.instructions.md)
and [detailed review checklist](../../.github/instructions/references/code-review-checklists.md).
Python findings use static producer/caller evidence; no interpreter, importability, or runtime outcome
is inferred from source inspection.

## Prioritized Findings

**Conclusion:** The feature is partially implemented and is not supported as release-ready by static
evidence. The server tool-name allow-list, six-role HTTP wiring, prompt hash, chat persistence path,
streaming UI and clock-aware pause/resume are real code, but they do not close the safety and end-to-end
obligations. There are **18 independent open follow-ups**; no fixed finding quota was used.

| Priority | Finding | Evidence | Follow-up |
| --- | --- | --- | --- |
| Critical | Chat accepts a broad/default role without membership or primary ownership | [Route](../../apps/api/app/api/routes/simulation_chat.py#L59), [default identity](../../apps/api/app/middleware/auth_middleware.py#L11) | AUD-024-002 |
| Critical | Public egress wrapper is disconnected and fails open on missing context/GET | [Guard](../../apps/api/app/clients/outbound_http.py#L64), [publication equivalent](../../apps/api/app/services/public_alert_service.py#L82) | AUD-024-003 |
| Critical | Raw PII is persisted and replayed around current-message minimization | [Persistence](../../apps/api/app/services/simulation/controller_service.py#L346), [model input](../../apps/api/app/services/simulation/controller_service.py#L588) | AUD-024-006 |
| High | Seed tool bypasses confirmation and only animates counters | [Seed handler](../../apps/api/app/services/simulation/controller_service.py#L990) | AUD-024-001 |
| High | Lifecycle/Stop/cancellation/report paths are not unified | [UI Stop](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L262), [state graph](../../packages/domain/src/domain/models/simulation_tenant.py#L15) | AUD-024-004 |
| High | NEMA throttle never constrains chat or emits required notification | [Governor](../../apps/api/app/services/resource_governor.py#L75), [tool check](../../apps/api/app/services/simulation/controller_service.py#L761) | AUD-024-005 |
| High | Provenance cannot reconstruct complete tool/turn/transition chains | [Recorder](../../apps/api/app/services/simulation_event_recorder.py#L137) | AUD-024-007 |
| High | Durable retention, cursor paging and conversation isolation are incomplete | [Repository](../../apps/api/app/repositories/sim_chat_history_repository.py#L116), [container](../../infra/main.bicep#L680) | AUD-024-008 |
| High | Process-local quota does not protect shared capacity | [Limiter](../../apps/api/app/services/simulation/rate_limiter.py#L16) | AUD-024-009 |
| High | Agent handlers lack current operational data/citations and connected progress | [Dispatcher](../../apps/agents/dispatcher/agent.py#L209) | AUD-024-010 |
| High | Scenario tools bypass validation and use city lookup instead of Maps | [Handler](../../apps/api/app/services/simulation/controller_service.py#L990) | AUD-024-011 |
| High | No simulated-warning approval disposition or complete watermarked export | [Chat/export](../../apps/web/src/components/simulation-chat-pane.tsx#L205) | AUD-024-012 |
| High | Main Disaster Map has no simulation lifecycle overlay | [Map host](../../apps/web/src/app/page.tsx#L102) | AUD-024-013 |
| High | Outage is not read-only and SSE/history/cancel contracts drift | [Client](../../apps/web/src/lib/api/simulation_chat.ts#L26), [input](../../apps/web/src/components/simulation-chat-pane.tsx#L303) | AUD-024-014 |
| High | Required adversarial/fuzz/journey tests and PR/nightly gates are missing | [Safety tests](../../tests/unit/test_simulation_controller_safety.py#L46), [CI](../../.github/workflows/ci.yml#L138) | AUD-024-016 |
| Important | Accessible live chat, real map audit and test discovery are incomplete | [A11y test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L19) | AUD-024-015 |
| Important | Telemetry, operational docs, capacity and release evidence are incomplete | [Configuration](../../apps/api/app/core/settings.py#L26), [azd](../../azure.yaml#L9) | AUD-024-017 |
| Important | Review/checklist/persona/hypothesis assertions are not acceptance proof | [Historical review](review-report.md#L48), [hypothesis](spec.md#L452) | AUD-024-018 |

## Open Remediation

The following IDs retain their discovery order for stability. The priority-ordered table above is the
triage order; all remediation items below are open. Future commands are consolidated later in this report.

### Authorization Does Not Protect the Chat Boundary

- [ ] AUD-024-002 Enforce authenticated membership and coordinator ownership on every simulation operation

**Priority:** Critical, release-blocking. **Affected:** A1/A3, FR-001, FR-025, FR-035;
T040, T050, T051, T061, T073; US1, US2, US4 scenario 4.

**Expected:** Verified Entra authentication, simulation membership, distinct Coordinator/Observer roles,
and exactly one primary coordinator authorize writes. Observers can read but never send or control.

**Observed:** [Chat POST](../../apps/api/app/api/routes/simulation_chat.py#L59) and
[history GET](../../apps/api/app/api/routes/simulation_chat.py#L101) check only the broad
[SimulationUser role](../../apps/api/app/core/auth.py#L13); neither checks membership, existence,
terminal state, or primary ownership. [Default claims](../../apps/api/app/middleware/auth_middleware.py#L11)
grant anonymous callers that role. The [production RBAC prefix list](../../apps/api/app/middleware/rbac_check.py#L32)
does not include simulation routes. [Tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L47)
only logs a non-member, and [application wiring](../../apps/api/app/main.py#L55) passes it no repository.
An application-level caller can therefore address another `sim-*` history or submit work without the
required coordinator claim. External ingress/EasyAuth enforcement was not inspected live and is not
assumed to repair these application checks. A token containing only either specified role is not the
role this implementation accepts.

**Developer direction and ownership:** Repair the route dependencies, claims normalization, and frontend
permission propagation together. Use verified subject/object IDs, explicit simulation membership, a
durable compare-and-swap primary-owner claim and an authorized handover operation. Fail closed for
missing identity outside an explicitly isolated local fixture mode. Preserve existing SimulationUser
clients only through an explicit, documented migration; never infer Coordinator from general membership.

**Tester direction:** Extend [history tests](../../tests/unit/test_sim_chat_history.py#L52) with route-level
tests rather than repository-only partition assertions. Use two simulations, coordinator/observer/non-member
principals, absent headers, forged headers, unknown IDs and simultaneous handovers. Assert 401/403/404 as
appropriate, no model invocation or writes on denial, one successful owner transfer, and Observer read-only UI.

**Completion criteria:** Every mutation enforces role, membership and current primary ownership;
transcript reads cannot cross membership boundaries; no default production privilege; handover races
cannot yield two primary owners. Future validation commands will be consolidated below.

### The Egress Gate Is Not an End-to-End Safety Boundary

- [ ] AUD-024-003 Connect fail-closed public egress enforcement to every transport and publication receipt

**Priority:** Critical, release-blocking. **Affected:** A4, FR-019, FR-020, FR-021, SC-002;
T010, T011, T012, T013, T014, T083; all US5 scenarios; US3 scenario 3.

**Expected:** Every simulated public message is blocked before transport, returns the required blocked
result, and records channel, audience, body hash and reason. The second gate is independently effective.

**Observed:** The [wrapped GET](../../apps/api/app/clients/outbound_http.py#L92) bypasses `_guard`;
the [guard](../../apps/api/app/clients/outbound_http.py#L64) also returns on missing/invalid context.
The [chat route](../../apps/api/app/api/routes/simulation_chat.py#L28) constructs a raw HTTP client and
the [adapter base](../../apps/api/app/services/simulation/sub_agents/_base.py#L59) calls it directly.
The relocated [PublicAlertService.publish](../../apps/api/app/services/public_alert_service.py#L66)
mutates publication state without checking tenant provenance; its
[delivery guard](../../apps/api/app/services/public_alert_service.py#L88) returns an ordinary
`published (simulation)` dictionary rather than `410 SIM_EGRESS_BLOCKED` or a synthetic-delivery record.
[Current channel adapters](../../apps/api/app/services/public_alert_service.py#L29) only build payload
dictionaries. This is not evidence of a real leak, but neither are these stubs proof of protection for
ACS/SMS/email/broadcast/social/CAP transports.

**Developer direction and compatibility:** Centralize public-transport classification and originating
tenant provenance, including queued/background requests. Bind both publication and transport layers to
the synthetic-delivery writer. Make missing context fail closed for public egress. Cover all HTTP methods,
redirects and body forms. Explicitly distinguish approved internal agent/Maps/model traffic from public
communications so the safety fix does not disable required Azure-only simulation operations. Do not use
a blanket bypass flag to reconcile that design conflict.

**Tester direction:** Extend [existing wrapper tests](../../tests/unit/test_simulation_controller_safety.py#L76)
with transport spies on the actual publication and adapter paths, not just direct `_guard` calls. Include
all six channels, live versus simulation provenance, missing context, GET-with-side-effect, redirects,
empty JSON and binary bodies, queue replay and recording failure. Assert zero public transport calls and
one durable, correctly hashed receipt per attempted message; independently prove each gate.

**Completion criteria:** The 10,000-message test covers real registered boundaries with assert-on-call
transports, receipts are complete, and approved internal service traffic still works. No claim of test
execution or real delivery is made here.

### Confirmation Must Precede Scenario Work

- [ ] AUD-024-001 Enforce confirmed scenario authoring before starting or mutating an exercise

**Priority:** High. **Affected:** FR-005, FR-008, FR-009; US1 acceptance scenarios 1, 2, and 4;
T033, T034, T040, T062, T063.

**Expected:** The first chat response is an unconfirmed, validated scenario card. No seeding or
state-changing work occurs until an authorized coordinator explicitly confirms it.

**Observed:** The [seed handler](../../apps/api/app/services/simulation/controller_service.py#L990)
sets `confirmed=True` and schedules `_ingest_synthetic_signals` immediately. Both the
[prompt](../../apps/api/app/services/simulation/controller_prompt.md#L24) and
[tool description](../../apps/api/app/services/simulation/controller_tools.py#L17) explicitly say not to
ask for confirmation. The [counter helper](../../apps/api/app/services/simulation/controller_service.py#L1096)
permits `Paused` as well as `Active`; it increments a display counter instead of creating BOM/IoT
signals or initial Monitoring/Planning/Resource Allocation work. This is a server-side confirmation
bypass and delivery gap, not merely a model-compliance concern.

**Developer direction:** Make proposal, validation, confirmation, and execution separate server-enforced
steps; bind confirmation to the scenario revision and authorized primary coordinator. Preserve tenant
isolation and reject stale confirmations. Never infer approval from a model-generated argument.

**Tester direction:** Extend [controller safety tests](../../tests/unit/test_simulation_controller_safety.py#L1)
and [chat component tests](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L1). Exercise
an unconfirmed Katoomba card, explicit confirmation, duplicate/stale approval, two coordinators, Stop
racing approval, invalid tool arguments, and a later spot-fire append. Assert no pre-approval queue/write,
one real tenant-scoped signal schedule after approval, all three initial agent records, the full card
fields, and no live-partition changes. Future command groups C01/C02/C03/C06/C07 apply.

**Completion criteria:** A proposed card cannot enqueue work or change state; one explicit, authorized,
revision-matched confirmation produces one execution. Negative and concurrency fixtures must prove this.

### Pause and Stop Are Not the Contracted Lifecycle

- [ ] AUD-024-004 Unify lifecycle state, pause quiescence, stop cancellation and final reporting

**Priority:** High. **Affected:** FR-001, FR-002, FR-003, FR-036; T002, T040, T041,
T050, T061, T065, T082, T086; US2 scenarios 1-3; idle and browser-reopen edge cases.

**Expected:** Draft-to-active requires confirmation; pause is idempotent and forbids tasking; stop is
terminal, cancels tracked work with `cancelled-by-stop`, releases resources, disables chat, and queues
a report containing the final audit reference. Resume does not replay previously delivered signals.

**Observed:** The [state enum/transition graph](../../packages/domain/src/domain/models/simulation_tenant.py#L15)
has Provisioning/Active/Paused/Archiving/Archived/Deleted, not draft/ended. The
[creation path](../../apps/api/app/services/simulation_service.py#L89) activates immediately.
[Pause](../../apps/api/app/services/simulation_service.py#L131) rejects an already-paused tenant.
The [UI Stop handler](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L262) calls archive and sets
local `Archiving` even though [archive](../../apps/api/app/services/simulation_service.py#L191) finishes
as `Archived`. Chat receives only `tenantId`, not status or permissions. The
[chat dispatcher](../../apps/api/app/services/simulation/controller_service.py#L324) does not check
lifecycle state, and its tool stop returns a pending-confirmation note without executing control.
A [later cancellation registry](../../apps/api/app/services/simulation/cancellation.py#L38) exists;
its existence does not demonstrate that the chat invocation tasks are registered or cancelled by UI Stop.

**Developer direction and compatibility:** Establish one authoritative lifecycle across the original
tenant routes, later lifecycle state store, scheduler and chat. Define/migrate existing stored states
without deleting archives or replay evidence. Reject tasking while paused/terminal but allow paused notes;
register all in-flight work with a durable cancellation/lease strategy for multiple replicas. Generate
one final report job with audit reference on terminal stop; propagate actual returned state to all clients.

**Tester direction:** Extend [lifecycle tests](../../tests/unit/test_simulation_service.py#L90) and
[controller safety tests](../../tests/unit/test_simulation_controller_safety.py#L1) with mounted-route coverage. Use
draft/unconfirmed, Active, Paused, terminal and archived fixtures; repeated pause/stop; Stop racing a
delayed agent; duplicate completion; two tabs; and paused seed requests. Assert no new signals/tasking
while paused, no terminal restart, one report, cancelled-by-stop outcomes, released locks, and disabled
chat after refresh. Include no-chat intervals just below/at/above 24 hours, recent-chat reset, a stopped
tenant and coordinator notification; implement an idle timer distinct from wall-clock expiry/archive.
Do not substitute a direct cancellation-helper test for the mounted control route.

**Completion criteria:** All original control responses, transitions, cancellation outcomes, and report
creation are proven through the mounted API and page. Later-feature aliases must be explicitly reconciled,
not silently used to waive the original contract.

### Input Minimization Is Bypassed by Transcript Replay

- [ ] AUD-024-006 Scrub and safety-check every model-bound message before persistence or inference

**Priority:** Critical, release-blocking. **Affected:** FR-005, FR-010, FR-024; T030, T033,
T084; PII, unsafe-response and prompt-exfiltration edge cases; CHK013/014/031.

**Expected:** PII is removed before storing/transmitting chat, the operator is warned, and input/output
safety controls independently prevent prohibited real-world instructions. Residency exceptions, if any,
must not bypass those controls.

**Observed:** The [raw user turn is persisted first](../../apps/api/app/services/simulation/controller_service.py#L346).
The [gateway only examines the current message](../../apps/api/app/services/simulation/controller_service.py#L568),
and import failure sets it to `None`. The [model message list then replays raw history](../../apps/api/app/services/simulation/controller_service.py#L588),
including that just-persisted turn, before appending the filtered copy. Even when the non-AU gateway
redacts the current message, its raw duplicate reaches the assembled request. The
[gateway's AU branch](../../apps/agents/common/model_gateway.py#L194) deliberately returns the original
text. The controller's short regex list and provider error handling are not calls to the existing
[ContentSafetyValidator](../../apps/agents/common/content_safety.py#L57), nor a server-side check on
streamed assistant content. The prompt's instruction to ignore PII does not redact stored bytes.

**Developer direction and compatibility:** Establish one explicit, fail-closed preprocessing boundary
for all replayed history, current input, retrieval input and sub-agent questions; persist only approved
redacted content and safe metadata. Eliminate duplicated current messages. Connect applicable input
and output safety policies without blocking legitimate simulated emergency language. Validate the
authorized inference region/exception before transmitting; migrate or restrict access to already stored
raw turns without silently altering their recorded hashes.

**Tester direction:** Extend [history tests](../../tests/unit/test_sim_chat_history.py#L68) and
[controller safety tests](../../tests/unit/test_simulation_controller_safety.py#L46). Capture the entire
mock model request for first and later turns containing synthetic AU phone/email/name fixtures, including
history written before remediation. Assert no raw PII in storage, playback previews, model input or
sub-agent input; one current-user message; visible redaction notice; no call when the gateway fails or
an exception is unauthorized. Test malicious model output independently of input regex matching.

**Completion criteria:** Privacy and safety invariants hold in AU and permitted inference-exception
paths, for every turn and tool, including replay and dependency failure. Actual regional deployment and
human authorization remain unverified until separately evidenced.

### NEMA Throttle Does Not Reach Chat Enforcement or Notification

- [ ] AUD-024-005 Apply the NEMA Level-3 policy to live chat tools and notify every connected coordinator

**Priority:** High, release-blocking for SC-008. **Affected:** FR-004, FR-040, SC-008;
T042, T064, T082; US2 scenario 4; CHK020/021.

**Expected:** Within five seconds of a NEMA Level-3 declaration, simulations continue in throttled
mode, only summarise_state/pause/stop are allowed, and a non-dismissible banner, toast and audit event
explain the degradation. Start also honors the contracted Level-3 conflict response.

**Observed:** [ResourceGovernor.declare_incident](../../apps/api/app/services/resource_governor.py#L75)
updates throttle flags, but the [declaration route](../../apps/api/app/api/routes/incidents.py#L20)
has no NEMA/level input. The [controller tool check](../../apps/api/app/services/simulation/controller_service.py#L761)
uses a static allow-list and never reads throttle state. The chat pane does not handle `banner.throttle`;
the page's throttle display is a value from its initial tenant fetch, not a live banner or toast.
Searches of the simulation service/routes, resource governor and simulation UI found no emission of the
contracted banner or a dynamic three-tool restriction. A stored throttle flag is not this behavior.

**Developer direction and compatibility:** Connect an authenticated, tenant-aware declaration source
to a shared policy state consulted before each tool execution, including in-flight streamed tool requests.
Publish current throttle state on connect/reconnect and changes while idle. Reuse the governor without
pausing the exercise or throttling live operations. Resolve the contract's pause-versus-throttle wording
using the clarification that explicitly says throttle without pause.

**Tester direction:** Extend the [controller safety suite](../../tests/unit/test_simulation_controller_safety.py#L17)
with a mounted declaration/chat sequence, delayed model tool calls and two clients. Assert only the three
allowed tools execute after declaration, denied tools leave no state change, exactly attributed audit
events exist, and the banner cannot be dismissed. Measure the five-second bound in a separately authorized
environment; a fake-clock unit result is not operational latency evidence.

**Completion criteria:** The complete declaration-to-tool-to-banner path is wired, state survives
reconnect and replicas, and measured evidence demonstrates the bound without affecting live work.

### The Audit Trail Cannot Reconstruct Every Turn and Invocation

- [ ] AUD-024-007 Persist complete correlated turns, tool results and lifecycle provenance

**Priority:** High. **Affected:** FR-002, FR-007, FR-013, FR-014, FR-037, SC-004;
T001, T004, T030, T032, T033, T035, T041, T090; CHK008/010/024/028.

**Expected:** One correlation chain joins the ingress request, user/assistant turns, model/version and
prompt/tool-manifest version, tool arguments/results, sub-agent provenance, downstream changes and
actor/reason/timestamp for every transition, including refusal, cancellation and error.

**Observed:** The route accepts `correlation_id` but does not pass it onward.
[Persistence](../../apps/api/app/services/simulation/controller_service.py#L223) allocates a fresh ID
instead of the streamed `turn_id`; user/tool records omit the model. On the Foundry path only a seed
card is persisted as a tool turn, while [other tool results stay in the temporary model message list](../../apps/api/app/services/simulation/controller_service.py#L801).
The [event recorder](../../apps/api/app/services/simulation_event_recorder.py#L138) records tool name,
outcome and zero/default latency, not arguments, result, turn ID or correlation ID. State-change payloads
omit actor and reason. The adapter returns prompt/model/invocation provenance but the controller drops it.
Unknown-tool refusal is streamed without a durable typed `tool_denied` record. Prompt-file hashing exists,
but does not bind the separate tool schema version. Failed/aborted streams can leave a user-only history.

**Developer direction and compatibility:** Adopt one canonical event/correlation identity across SSE,
history, tool invocation and downstream records; persist the complete schema-valid outcome at every exit.
Carry sub-agent metadata rather than inventing local substitutes. Bind hashes to the exact redacted
content and versioned prompt/tool definition used. Make audit failure policy explicit, visible and
recoverable; retain the existing playback format through an adapter or versioned migration.

**Tester direction:** Extend [history tests](../../tests/unit/test_sim_chat_history.py#L68) and the existing
[audit-writer test file](../../apps/api/tests/test_audit_writer.py#L1). Capture multi-tool streams, unknown
tools, malformed results, refusal, cancellation, model failure and handover. Assert a deterministic
join from request correlation through every persisted turn and tool to state changes, exact content
hashes, model versions and prompt/tool hashes, with no tool results existing only in memory.

**Completion criteria:** The full audit can reconstruct successful and failed scenarios without relying
on UI log text, process memory, or synthesized provenance. Every original audit field has an assertion.

### Retention and Durable Paging Are Not the Required Store Contract

- [ ] AUD-024-008 Implement two-year durable retention and bounded coordinator-scoped transcript access

**Priority:** High. **Affected:** FR-007, FR-025, FR-030, FR-031; T001, T003, T004,
T050, T088; browser-reopen and multiple-coordinator edges; CHK028/030/031/032.

**Expected:** Chat, invocations and blocked-delivery artifacts remain durably tenant-scoped for
63,072,000 seconds, are automatically purged, and support async cursor paging. Coordinators have
separate conversations with a shared authorized audit trail.

**Observed:** [sim-chat infrastructure](../../infra/main.bicep#L680) has `/tenant_id` and a replay index
but no `defaultTtl`; [SimChatTurn](../../packages/domain/src/domain/models/sim_chat_turn.py#L12) has no
item TTL. The [repository](../../apps/api/app/repositories/sim_chat_history_repository.py#L69) uses
non-atomic `MAX(sequence)+1`, synchronous Cosmos calls, and process-local fallbacks on read/write failure.
[list_turns](../../apps/api/app/repositories/sim_chat_history_repository.py#L116) reads the entire
partition before truncating its tail and has no cursor or actor filter. History fallback writes are not
merged back after a healthy Cosmos read. [Synthetic delivery defaults](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L115)
use memory for the feature record; a later canonical audit writer is an additional best-effort path,
not proof that all three original stores have retention. Neither original tool nor delivery repository
contract is supplied by the chat history repository alone.

**Developer direction and compatibility:** Reuse the existing Cosmos and canonical audit capabilities
where they fully satisfy the schema instead of duplicating containers merely to match historical names.
Document an explicit mapping/migration for all three logical stores, TTL/indexes and original fields.
Use atomic sequence allocation, async bounded queries, opaque continuation tokens and coordinator
conversation keys. Define durable retry/backpressure rather than silently losing failed writes. Do not
purge active evidence early when archiving, and reconcile nightly Parquet export retention with deletion.

**Tester direction:** Extend [repository tests](../../tests/unit/test_sim_chat_history.py#L30) using
in-memory and production-interface fixtures, concurrent writers, two coordinators in one sim, two sims,
write failure followed by recovery, multi-page histories, and TTL boundaries just before/after two years.
Assert no duplicate sequence, no missing replay, no cross-conversation leak, stable cursors and correct
purge configuration. Actual TTL expiry requires a separately authorized integration environment.

**Completion criteria:** All logical artifact stores have a verified durable mapping, retention and
purge policy; paging is bounded; concurrency and recovery tests preserve order and isolation.

### Rate Limits Are Process-Local and the Aggregate Tenant Key Is Unresolved

- [ ] AUD-024-009 Enforce shared atomic chat quotas with explicit retry semantics

**Priority:** High. **Affected:** FR-026, FR-038; T020, T033, T080; CHK015;
research R4 and the plan's horizontal-scale limits.

**Expected:** Atomic shared limits of 30 messages/min/user/sim and 120/min/owning tenant survive
replica changes; rejected submissions return the contractual rate-limit signal and retry information.

**Observed:** [RateLimiter](../../apps/api/app/services/simulation/rate_limiter.py#L16) stores token
buckets in Python dictionaries and keys both quotas by the simulation `tenant_id`; the controller never
passes a distinct simulation or owning-tenant key. Restarting or using another replica resets/duplicates
capacity. [Rejection](../../apps/api/app/services/simulation/controller_service.py#L333) is an SSE error
on an otherwise 200 response, without Retry-After. The [existing test](../../tests/unit/test_simulation_controller_safety.py#L39)
tests a single limiter's three-message burst, not the tenant aggregate, refill or concurrency.
The spec's simulation-as-tenant model and wording 'across all simulations in that tenant' need an explicit
owner-key resolution; treating every simulation ID as the aggregate silently weakens that clause.

**Developer direction and compatibility:** Use the approved shared Redis capability with atomic
dual-bucket reservation, bounded key expiry and documented outage behavior. Resolve the owning tenant
from trusted identity, not caller input. Reconcile HTTP-versus-SSE error timing and return retry metadata
without consuming additional model quota. Keep later telemetry-injection success-only budgets distinct
unless an explicit compatible policy says they share chat quotas.

**Tester direction:** Extend [rate-limiter tests](../../tests/unit/test_simulation_controller_safety.py#L39)
with clock-controlled refill, 30/31 and 120/121 boundaries, different users/sims/owning tenants, two limiter
instances over one fake Redis interface, restart, concurrency and Redis failure. Assert quota isolation,
one atomic reservation per accepted chat and no provider call after rejection.

**Completion criteria:** Limits hold across workers and simulations with agreed key semantics, and
clients receive actionable retry information. Record future Redis integration outcomes separately.

### Six Registered Roles Do Not Yet Provide Operational Sub-agent State

- [ ] AUD-024-010 Connect Controller queries to substantive tenant-scoped agent results and visible progress

**Priority:** High. **Affected:** FR-011, FR-012, FR-013, FR-014, SC-001, SC-003;
T032, T033, T082; US1 scenario 2, all US3 scenarios; timeout/network/unknown-agent edges.

**Expected:** Monitoring, Planning, Resource Allocation, Communication, Evacuation and Risk Assessment
return their actual current simulation output with inspectable identifiers, correlated provenance,
visible progress, a 120-second hard timeout and cached degraded fallback.

**Observed:** [Production adapter registration](../../apps/api/app/services/simulation/sub_agent_invoker.py#L148)
and [internal hostname provisioning](../../infra/main.bicep#L1066) exist. However, the
[dispatched handler](../../apps/agents/dispatcher/agent.py#L209) supplies only a role prompt and question
to a generic model, does not read simulation signals/IAP/resources or call the existing operational
services, and [always returns empty citations](../../apps/agents/dispatcher/agent.py#L269).
Its textual '(degraded)' fallback is returned as a normal 200 reply without a degraded field; the adapter
therefore treats it as success. The route passes no soft-ack callback to the invoker. Offline tool.call
is emitted after awaiting the reply. The timeout handler returns an error summary, not cached state.
`list_participants` and `summarise_state` return dashboard instructions instead of underlying data.

**Developer direction and compatibility:** Keep the registered role aliases and internal host boundary,
but connect each role to its actual tenant-scoped service/repository output and trusted citations. Define
typed degraded/error/provenance fields end-to-end. Connect progress before waiting, cancellation via
AUD-024-004, and bounded last-known-state caches keyed by simulation and agent. Do not replace missing
operational data with plausible model claims. Return real participant/state information through the two
corresponding tools. Validate unknown IDs without echoing unsanitized exceptions or external identifiers.

**Tester direction:** Extend [invoker tests](../../apps/api/tests/test_sub_agent_invoker.py#L29) and
[route wiring test](../../apps/api/tests/test_simulation_chat_controller_wiring.py#L22) beyond registry
membership. Seed distinct IAP/resource/monitoring data for two simulations; assert the correct tenant's
identifiers survive to the rendered answer and no live records appear. Test six roles, aliases, unknown
role, empty/malformed response, 30-second progress, 120-second timeout, unavailable host and cache age.
Assert progress precedes the response and degraded states cannot be recorded as successful tasking.

**Completion criteria:** The three US3 examples return substantive inspectable records from the actual
services, all six roles work through the mounted Controller, and slow/failing agents preserve safe,
observable behavior. Real P95 measurements remain a separate future gate.

### Location Resolution and Tool Argument Validation Are Missing from Execution

- [ ] AUD-024-011 Validate scenario arguments and resolve locations through Azure Maps with explicit fallback

**Priority:** High. **Affected:** FR-008, FR-009, FR-032; T001, T021, T031, T034, T080;
US1 scenarios 1/4; NSW/VIC/QLD/territory and cross-sector cohort obligations.

**Expected:** Validated hazard/time/conditions/AWS level and jurisdiction-aware resolved geometry are
shown before confirmation. No Maps match or timeout requires explicit coordinator lat/lon, not guessing.

**Observed:** [Tool JSON parsing](../../apps/api/app/services/simulation/controller_service.py#L747)
falls back to `{}` and does not validate against Pydantic/JSON schemas. The
[seed handler](../../apps/api/app/services/simulation/controller_service.py#L990) accepts arbitrary
strings, uses `_geocode_au`'s small hard-coded city table and emits `lng/lat/resolver=builtin`, which is
not the [declared GeoJSON location model](../../packages/domain/src/domain/models/sim_scenario_card.py#L10).
Unknown places still produce a confirmed card with null coordinates and `ingestion_started=True`.
The [map fallback](../../apps/web/src/components/simulation-map.tsx#L173) uses jurisdiction capitals,
which can materially mislocate an exercise. No production location-resolver call was found in the
controller, simulation service folder, or its route. A hazard enum alone does not implement jurisdictional
terminology, combat-agency boundaries, conditions or landmark resolution.

**Developer direction and compatibility:** Use the existing domain model as the execution boundary,
with strict enums, timezone-aware time, bounded coordinates and condition validation. Wire approved
Azure Maps read traffic under the egress policy from AUD-024-003; support ambiguity and zero-result/timeout
states. Preserve explicit user coordinates and their resolver provenance. Version the SSE/frontend card
shape rather than retaining incompatible dictionary/model definitions.

**Tester direction:** Extend [controller safety tests](../../tests/unit/test_simulation_controller_safety.py#L1)
and [map tests](../../apps/web/tests/unit/spec_036/simulation-map.test.tsx#L1). Fixtures: Katoomba NSW,
Leeton Showground, Darwin cyclone, ambiguous Richmond, unknown locality, zero/timeout Maps results,
valid manual point, reversed/out-of-range/NaN coordinates, invalid hazard/AWS tier, malformed tool JSON,
timezone offsets and all nine hazards. Assert no confirmed execution on invalid or unresolved data,
correct geographic provenance, and every scenario parameter displayed before approval.

**Completion criteria:** Validated cards and map coordinates agree; fallback explicitly asks for lat/lon;
no guessed capital or model-provided confirmation is treated as resolved scenario execution.

### Warning Approval and Export Do Not Provide a Safe Artifact Workflow

- [ ] AUD-024-012 Add simulated warning disposition and enforce watermarks in every rendered and exported artifact

**Priority:** High. **Affected:** FR-005, FR-022, FR-030, FR-033; T062, T066, T088;
US3 scenario 2; CHK006/007; operational PIO requirements.

**Expected:** A valid AWS warning is previewed with the exact [FR-022 watermark](spec.md#L321)
(`SIMULATION \u2014 DO NOT DISTRIBUTE`, with the escape decoded to U+2014); Approve/Discard records a simulation-only
disposition, Approve pins `would-have-published`, and all preview/export formats retain the watermark.

**Observed:** The [warning tool](../../apps/api/app/services/simulation/controller_service.py#L955)
now prefixes its return value server-side, partially addressing old review O-2. But the model's streamed
prose can omit that result, and [message rendering](../../apps/web/src/components/simulation-chat-pane.tsx#L330)
does not force the full watermark or expose warning Approve/Discard. Searches of the simulation
controller/routes/UI and alert service found no `would-have-published` disposition path. Later
watermark guard modules are not called by this path. The
[export action](../../apps/web/src/components/simulation-chat-pane.tsx#L205) downloads currently loaded
user/assistant messages as Markdown only: no HTML bundle, enforced watermark, full paged transcript,
tool/audit lineage, or dedicated PDF/email preview protection.

**Developer direction and compatibility:** Persist a typed warning draft and immutable approval/
discard disposition under the simulation, with authorized confirmation tied to the draft hash. Render
and export the server-owned artifact, never only a model paraphrase. Reuse the existing watermark guards
and AWS model where appropriate, and keep publication disabled at both gates. Deliver safe printable
HTML plus Markdown with complete accessible transcript/provenance; escape HTML and sanitize links.

**Tester direction:** Extend [chat component tests](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L1)
and [watermark guard tests](../../apps/api/tests/test_watermark_guards.py#L1). Test Advice/Watch and Act/
Emergency Warning, model text omitting or altering the watermark, forged approval, duplicate approval,
discard, malicious HTML, long transcripts and restored history. Assert exact watermark in UI, HTML,
Markdown and any available PDF/email previews, one `would-have-published` audit event, zero public calls,
and no approval from an observer. Missing new artifact routes/tests must be labeled proposed.

**Completion criteria:** Every artifact surface carries the exact warning watermark regardless of model
behavior, approval is auditable and simulation-only, and exports contain the complete authorized transcript.

### Disaster Map Has No Simulation Lifecycle Layer

- [ ] AUD-024-013 Add authorized simulation overlays, lifecycle legend and deep links to the Disaster Map

**Priority:** High. **Affected:** FR-015, FR-016, FR-017, FR-018, FR-029; T070, T071,
T072, T073; all four US4 scenarios; SC-006/007; CHK033-037/040/041.

**Expected:** The live map concurrently shows live incidents and active/paused/ended simulations with
striped translucent styles, persistent accessible SIM badges, state legend, summary/deep link, observer
read-only access, and a >24-hour-ended filter/toggle.

**Observed:** [The old map URL redirects](../../apps/web/src/app/disasters/page.tsx#L3) to the
[homepage](../../apps/web/src/app/page.tsx#L102), which loads incidents only and opens an incident
sidebar. [The map API](../../apps/api/app/api/routes/incidents_map.py#L111) queries only incidents;
no simulation-overlay route or feed was found among the mounted simulation routes. The separate detail
[SimulationMap](../../apps/web/src/components/simulation-map.tsx#L146) reuses incident markers, maps
Paused to active, and adds `[SIM]` to titles. Its optional later-feature overlay-events input is not
passed by the detail page. None of this supplies the required lifecycle legend or ended-age toggle on
the live map. This is absence after tracing relocation, not a missing historical filename alone.

**Developer direction and compatibility:** Add a tenant-authorized overlay source under the current
map host, preserve existing live marker/filter behavior and never mix simulation records into live
incidents. Use authoritative ended timestamps and geometry; label states with text/pattern as well as
color. Wire the summary panel/deep link and apply Observer restrictions from AUD-024-002. Keep later
hazard-overlay types compatible but distinct from the simulation lifecycle overlay.

**Tester direction:** Extend [existing SimulationMap tests](../../apps/web/tests/unit/spec_036/simulation-map.test.tsx#L1)
and the [map accessibility suite](../../apps/web/tests/a11y/simulation-map-non-point.test.tsx#L89).
Use one live incident plus active/paused/ended sims at different and overlapping coordinates; timestamps
23:59:59, exactly 24 hours, and older; coordinator/observer/non-member; refresh/toggle/filter combinations.
Assert persistent SIM labels, paused amber/pattern style, live opacity unchanged, correct hidden/show
behavior, and read-only deep-link navigation. Add actual map-host browser assertions under its configured
test directory; component mocks do not prove visual distinction or timing.

**Completion criteria:** All four US4 scenarios hold on the current `/` map, including accessibility,
age boundaries and authorization. The >=95% first-glance usability outcome needs recorded human results.

### Chat Transport and Degradation Diverge from the Contract

- [ ] AUD-024-014 Align SSE, transcript and cancellation contracts and expose a read-only outage state

**Priority:** High, release-blocking for FR-034. **Affected:** FR-011, FR-025, FR-034;
T033, T050, T060, T062, T087; chat contract; OpenAI outage and tab-close edges.

**Expected:** The documented POST/GET/cancel surfaces and event shapes work with authenticated clients;
errors are coherent, cancellation is server-observable, and model outage makes chat read-only with a
banner while controls, map and cached agent state stay usable.

**Observed:** [The route](../../apps/api/app/api/routes/simulation_chat.py#L58) supplies POST plus
`/chat/history` and `/chat/health`, not contracted GET `/chat?after=...` or POST `/chat/cancel`.
The [configured API prefix](../../apps/api/app/core/settings.py#L10) is `/api`, while the local
contracts specify `/api/v1`. The [client](../../apps/web/src/lib/api/simulation_chat.ts#L26) has no bearer
or correlation header and hand-parses only LF blank-line framing; CRLF frames are not separated and
EOF leftovers are dropped. The reducer ignores throttle/progress and most tool-result details.
[Textarea/quick-action enablement](../../apps/web/src/components/simulation-chat-pane.tsx#L287)
depends on `isStreaming`, not outage/observer/terminal state. OpenAI errors become message bubbles and
input re-enables. Missing endpoint silently selects offline mode. Health returns `azure-or-offline`
and a hash without a provider-availability or tool-manifest version check.

**Developer direction and compatibility:** Publish and implement one versioned contract or a documented
compatibility adapter for original callers. Reuse the shared auth transport; use a proven SSE parser or
fully cover framing/cancellation. Make offline demonstration mode explicit and separate from production
outage; preserve provider-independent controls/data. Expose typed availability, progress and terminal
states, cancellation acknowledgment and retry policy without disclosing raw provider exceptions.

**Tester direction:** Extend [chat component tests](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L1)
and place a **proposed** route contract test under the existing tests/contract directory. Cases: split UTF-8,
CRLF/LF, multi-line data, malformed JSON, partial EOF, 401/403/404/409/429/503, missing SDK, disconnect,
cancel racing Stop, backend recovery and history paging. Assert event ID consistency, no silent loss,
read-only outage with banner, functioning pause/stop/map/cached agent data, and authenticated transport.

**Completion criteria:** One coherent contract is exercised at mounted HTTP and UI boundaries; outage
does not masquerade as normal offline chat and cannot disable independent safety controls.

### Accessibility Claims Do Not Cover the Actual Chat and Map Workflow

- [ ] AUD-024-015 Complete accessible chat announcements and verify the full detail and overlay experience

**Priority:** Important. **Affected:** FR-028, FR-029, SC-007; T065, T066, T085;
plan viewport/control-layout commitments; CHK038-042.

**Expected:** WCAG 2.2 AA automated and manual coverage, polite streaming announcements, keyboard
navigation/focus, reduced motion, non-color state labels and >=4.5:1 legend contrast across supported
desktop/tablet/minimum-360px layouts.

**Observed:** The textarea is labeled and native controls support keyboard input, but the
[message list](../../apps/web/src/components/simulation-chat-pane.tsx#L258) has no log role/polite live
region for replies. Collapsible page headings implement Enter only, not Space. The
[map risk badge](../../apps/web/src/components/simulation-map.tsx#L302) renders white text on bright
yellow/orange; no contrast measurement is retained. The
[page-level accessibility test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L19) visits the
simulation list, accepts missing receipts as a gap annotation, and is outside the
[configured Playwright test directory](../../apps/web/playwright.config.cts#L4). The included Vitest
map test stubs the map and checks labels, not axe or actual map contrast. No full human audit is evidenced.

**Developer direction and compatibility:** Add restrained accessible announcement semantics, focus and
keyboard parity to the real components; preserve existing readable status text and visible focus styles,
and add reduced-motion treatment where needed. Test 360px, tablet and desktop layouts, long text, loading, outage, paused and terminal
states. Avoid describing absent shared ChatShell filenames as a defect when the composed component can
meet the same requirements; fix behavior rather than add needless abstraction.

**Tester direction:** Extend [the existing chat tests](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L1)
and relocate/register the existing browser accessibility test. Require an actual simulated reply and
overlay before axe runs, test Tab/Shift-Tab/Enter/Space/focus restoration, reduced motion, screen-reader
SIM expansion, contrast and no clipping. Record tool/version/viewport/results plus a dated human audit;
do not mark a role-attribute unit test as a full WCAG pass.

**Completion criteria:** The intended page-level tests are collected and fail if required surfaces are
absent; automated and manual results cover all supported states with zero critical findings.

### The Required Regression Suites and Measured Gates Are Not Present

- [ ] AUD-024-016 Add effective Controller safety and end-to-end gates with the required CI cadence

**Priority:** High. **Affected:** FR-027, FR-039, SC-001 through SC-008;
T080, T081, T082, T083, T084, T085, T086, T087, T093; quality and release checklists.

**Expected:** Every specified behavior has assertions at the real boundary; 10,000 public-egress cases
prove zero calls, >=200 adversarial prompts achieve >=99% refusal/safety on simulation PRs and nightly
main, regressions block merge, and performance/usability measurements have attributable evidence.

**Observed:** The [024 safety tests](../../tests/unit/test_simulation_controller_safety.py#L17) contain
four regex-friendly refusal cases, a burst test and direct wrapper tests. The later
[200-prompt test](../../tests/integration/test_hallucinated_citation_suppression.py#L115) never passes
the prompts to the Controller; it repeats a constructed citation-filter assertion. The
[egress contract test](../../tests/contract/test_egress_block.py#L46) checks policy text and optionally
host connectivity, not 10,000 tenant-scoped publication attempts. Main
[CI Python tests](../../.github/workflows/ci.yml#L138) select contract/integration directories, omitting
these root unit tests and API-local wiring/invoker tests. The
[simulation sweep](../../.github/workflows/simulation-stub-sweep.yml#L3) and
[load workflow](../../.github/workflows/simulation-load-test.yml#L4) are manual, not the required PR/nightly
jailbreak/egress jobs. The found [playback E2E](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L19)
tests evaluator idempotency, not chat-confirm-start-query-pause-stop. Branch protection JSON explicitly
describes itself as non-enforcing documentation.

**Developer/tester direction:** Reuse the named existing suites from each remediation task, add a
**proposed** feature contract/integration suite and adversarial corpus, and wire their exact paths into
CI. Resolve the T093 50-prompt PR subset conflict against FR-039/CHK011's >=200 requirement explicitly;
the safer default is the full required suite. Add positive in-scope prompts alongside adversarial
role-switch/exfiltration/tool-fabrication/PII/unsafe-action cases, malformed/unknown tools, six public
channels and all lifecycle/RBAC/degradation scenarios. Assert calls/state/receipts, not just filenames,
mock registration, textual 'simulation' or a model-written refusal claim. CI should fail on missing tests,
missing corpus cases and threshold regressions, and use no real public destinations.

**Completion criteria:** Test collection lists the intended cases, PR and nightly gates execute them,
required checks are demonstrably enforced, and retained results are tied to a commit/configuration.
SC timing, 10,000-message outcomes, >=95% operator discrimination and manual WCAG results remain
UNVERIFIED until actually measured; this audit did not run them.

### Observability and Operational Readiness Are Incomplete

- [ ] AUD-024-017 Wire simulation telemetry and alerts and publish accurate deployment and leak-response guidance

**Priority:** Important. **Affected:** FR-023, FR-024, FR-034; T090, T091, T092, T100,
T101; plan SLO/capacity/operations commitments; CHK029/046-050.

**Expected:** Every simulation operation carries tenant_id/simulation/tool/sub-agent dimensions;
workbook and egress/refusal/rate-limit alerts are connected to actual emissions; current Azure-only
configuration and clean-environment prerequisites are documented; a usable leak runbook and Controller
health/version surface exist. The plan supports 10 active sims and 50 observers with stated SLOs.

**Observed:** [Application Insights bootstrapping](../../apps/api/app/main.py#L12) and
[API environment settings](../../infra/main.bicep#L1037) exist. Feature logs embed tenant text but do not
universally emit the required structured dimensions. The later
[egress alert](../../infra/bicep/modules/observability-alerts.bicep#L158) watches event names/dimensions
not emitted by the chat's logging path and is not proof of the three original alerts/workbook. The
[azd entrypoint](../../azure.yaml#L9) is infra/main, so nested infrastructure is not assumed deployed
without a reachable module reference. The local quickstart still configures old OpenAI variables and
three historical container names, while current code uses Foundry variables and sim-chat. The
[README](../../README.md#L1) has no 024 chat section/link in the bounded search; neither requested nor
referenced egress-leak runbook exists under docs/runbooks. Health does not report actual availability.
The [concurrency validator](../../apps/api/app/validators/simulation_validators.py#L11) enforces a
configured limit, and the [original service test](../../tests/unit/test_simulation_service.py#L54)
expects rejection after three creations, not the plan's ten-simulation capacity.

**Developer direction and compatibility:** Instrument the actual request/tool/sub-agent/public-egress
paths and connect alerts/workbook to those fields; separate expected blocks from confirmed leaks.
Document current Foundry identity/region, Maps, Cosmos, Redis and test-mode prerequisites without
retaining obsolete success claims. Add a **proposed** docs/runbooks/sim-egress-leak.md with containment,
transport shutdown, evidence preservation, notification/escalation, tenant impact and recovery criteria.
Reconcile the concurrency default/observer limit/SLOs with product and safety constraints rather than
silently raising quotas. Keep Azure Policy and AU data-storage requirements intact.

**Tester direction:** Extend [observability source tests](../../tests/devops/test_observability_alerts_bicep.py#L1)
and [resource governor tests](../../tests/unit/test_resource_governor.py#L20); capture real emitted
attributes through a fake exporter and match them to alert queries. Check 10-active/50-observer and
boundary fixtures only after capacity policy is agreed. Validate documentation links/config names,
health degraded/version states and recovery checklist completeness. Any future deployment, alert test,
performance drill or human approval requires separate authorization and retained results.

**Completion criteria:** Telemetry schema, alert queries and deployed-entrypoint reachability agree;
current operational docs exist; capacity and SLO evidence is attributable; no deployment or approval is
claimed solely from Bicep, prose or a checked planning gate.

### Authored Reviews and Amendments Do Not Establish Acceptance

- [ ] AUD-024-018 Reconcile specification conflicts and attach attributable review and hypothesis evidence

**Priority:** Important. **Affected:** ASM-071/072/073, PER-064/065/066, HYP-022;
local analysis/cohort review, plan constitution gates, requirements and safety checklists; T084, T093,
T100, T101 where documentation claims differ from delivery.

**Expected:** Original obligations, later amendments, persona validation, consultation and measured
outcomes have explicit authoritative resolutions and evidence. A scope label or MVP note does not
retroactively complete a mandatory requirement.

**Observed:** [The cohort review](review-report.md#L13) claims a nonexistent spec Deferred section and
says T032 permits stubs, whereas [T032](tasks.md#L31) requires service/equivalent adapters. Its
[deferred backlog](review-report.md#L48) and [aggregate test-pass claim](review-report.md#L55) have no
associated run artifacts in the assigned folder. The analysis report's '100% FR coverage' means task
mapping, not delivery. Sixteen requirement-quality items are checked, all 50 readiness items are open.
[PER assertions](spec.md#L444) do not contain the SME/practitioner evidence required by the
[persona schema](../027-spec-hardening/contracts/persona-profile.md#L16). The named
HYP-HYP-022.md evidence stub is absent; retained [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1)
and [postfeature](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) snapshots are portfolio-wide
structural assessments, not a spec-024 consultation experiment or independent human validation.

**Developer/documentation direction:** Preserve historical claims as historical, add a dated resolution
record tying each unresolved item to current owners/evidence, and correct references without rewriting
prior results. Resolve pause-notes versus later reject-all-chat wording, terminal ended versus archive,
50-versus-200 PR prompts, aggregate tenant keys, and blocked-public versus permitted-internal HTTP.
Explicit later Foundry/warp additions can be credited only for the clauses they replace. Non-AU personas
remain placeholders until D-009/SME prerequisites are fulfilled; do not invent approvals or run interviews
as part of a code-only task. A new hypothesis stub is **proposed**, not existing evidence.

**Tester/reviewer direction:** Use the complete coverage/checklist matrices below as a review agenda.
Attach per-commit tool output, configuration, human name/role/date where applicable, per-spec hypothesis
scores and falsification assessment. Verify every linked artifact exists and reports the claimed scope;
retain unknown outcomes as UNVERIFIED. No agent assertion substitutes for an authorized human sign-off.

**Completion criteria:** Contradictions have explicit approved dispositions, every claim has appropriate
evidence type, and HYP-022/persona validation is either demonstrated or honestly left open with prerequisites.

## Requirement Coverage

All 40 original FRs appear once below, including FR-028/029/030 which occur after FR-040 in the source.
Compound requirements retain all their clauses in the evidence/linked remediation, not just their titles.

| Requirement | Original obligation | Status | Concrete evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| FR-001 | Start/Pause/Resume/Stop with Coordinator role | PARTIAL | [Page controls](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L423) have pause/resume/archive-backed Stop, no Start or role gating; [backend role](../../apps/api/app/core/auth.py#L13) is SimulationUser. | AUD-024-001, AUD-024-002, AUD-024-004 |
| FR-002 | Draft/active/paused/ended state graph; actor/time/reason | CONFLICT | [State graph](../../packages/domain/src/domain/models/simulation_tenant.py#L15) and [recorder](../../apps/api/app/services/simulation_event_recorder.py#L153) lack the specified states and actor/reason provenance. | AUD-024-004, AUD-024-007 |
| FR-003 | Ended is terminal | MISSING | [Model](../../packages/domain/src/domain/models/simulation_tenant.py#L54) has no ended state; archive is not an explicit approved replacement. | AUD-024-004 |
| FR-004 | NEMA Level-3 throttle and banner | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L75) updates flags; no wired chat restriction or declaration-to-banner path. | AUD-024-005 |
| FR-005 | Azure Controller; role/scope lock, eight tools, confirmation, watermark | CONFLICT | [Prompt](../../apps/api/app/services/simulation/controller_prompt.md#L17) retains scope/watermark but explicitly removes confirmation; [Foundry migration](../036-foundry-rag-grounding/spec.md#L21) preserves approval semantics. | AUD-024-001, AUD-024-006, AUD-024-012 |
| FR-006 | Server independently enforces tool allow-list | IMPLEMENTED | [Controller membership check](../../apps/api/app/services/simulation/controller_service.py#L761) refuses names outside [registry](../../apps/api/app/services/simulation/controller_tools.py#L1), independent of model prose. Argument/state/authorization defects are separately recorded. | - |
| FR-007 | Every user/assistant/tool-call/tool-result audit, content hash, model/version | PARTIAL | [Persistence](../../apps/api/app/services/simulation/controller_service.py#L223) saves some turns with hashes; complete calls/results/model versions and durable failure outcomes are absent. | AUD-024-007, AUD-024-008 |
| FR-008 | English, all jurisdictions/nine hazards/conditions | PARTIAL | [Tool schemas](../../apps/api/app/services/simulation/controller_tools.py#L23) enumerate hazards; actual handler trusts strings and small built-in place list, with no jurisdiction/condition validation. | AUD-024-001, AUD-024-011 |
| FR-009 | Full structured card before confirmation/seeding | CONFLICT | [Seed handler](../../apps/api/app/services/simulation/controller_service.py#L990) auto-confirms; [card renderer](../../apps/web/src/components/simulation-chat-pane.tsx#L442) reduces it to hazard/place/level. | AUD-024-001, AUD-024-011 |
| FR-010 | Refuse and log real action, jailbreak, exfiltration and off-topic requests | PARTIAL | [Regex refusal](../../apps/api/app/services/simulation/controller_service.py#L62) covers a few patterns; no complete input/output safety or typed refusal trail. | AUD-024-006, AUD-024-007, AUD-024-016 |
| FR-011 | Streaming replies and sub-agent progress | PARTIAL | [Token SSE](../../apps/api/app/services/simulation/controller_service.py#L698) exists; [soft-ack hook](../../apps/api/app/services/simulation/sub_agent_invoker.py#L79) is not supplied by the chat route. | AUD-024-010, AUD-024-014 |
| FR-012 | Invoke six existing agents in sim tenant context | PARTIAL | [Adapters](../../apps/api/app/services/simulation/sub_agent_invoker.py#L148) pass tenant context, but [dispatcher](../../apps/agents/dispatcher/agent.py#L209) asks a generic model without operational state/services. | AUD-024-010 |
| FR-013 | Correlate chat, invocation, response and downstream changes | PARTIAL | [Event helper](../../apps/api/app/services/simulation_event_recorder.py#L137) retains only tool name/outcome/latency; accepted ingress correlation and returned invocation metadata are dropped. | AUD-024-007 |
| FR-014 | Aggregate plain-language outputs with inspectable citations | PARTIAL | [Model tool loop](../../apps/api/app/services/simulation/controller_service.py#L807) aggregates text, but [dispatcher](../../apps/agents/dispatcher/agent.py#L269) returns no operational citations. | AUD-024-007, AUD-024-010 |
| FR-015 | Distinct active/paused/ended overlays with SIM badge on Disaster Map | MISSING | [Actual map host](../../apps/web/src/app/page.tsx#L102) loads only incidents; separate detail map is not the required combined layer. | AUD-024-013 |
| FR-016 | Legend for simulation states | MISSING | [Map composition](../../apps/web/src/app/page.tsx#L243) has no simulation-state legend or data input. | AUD-024-013 |
| FR-017 | Overlay click opens summary and simulation deep link | MISSING | [Marker callback/sidebar](../../apps/web/src/app/page.tsx#L131) selects incidents, not simulations. | AUD-024-013 |
| FR-018 | Hide ended >24h by default with reveal toggle | MISSING | [Map host](../../apps/web/src/app/page.tsx#L76) contains no ended simulation source/time filter/toggle. | AUD-024-013 |
| FR-019 | Block every simulated public channel | PARTIAL | [Delivery guard](../../apps/api/app/services/public_alert_service.py#L88) blocks one in-process path but transport integration and originating-record provenance are incomplete. | AUD-024-003 |
| FR-020 | Every block has hash/channel/audience/reason receipt | PARTIAL | [Receipt builder](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L32) has fields, but real publication guard does not call it and durable feature store is not wired. | AUD-024-003, AUD-024-008 |
| FR-021 | Independent outbound HTTP wrapper gate | PARTIAL | [Wrapper](../../apps/api/app/clients/outbound_http.py#L64) guards writes only, fails open for absent context and is not used by production callers. | AUD-024-003 |
| FR-022 | Watermark all warning drafts/PDF/email previews | PARTIAL | [Warning tool](../../apps/api/app/services/simulation/controller_service.py#L955) prefixes its return; model text and exports are not enforced. | AUD-024-012 |
| FR-023 | App Insights tenant_id and simulation=true on all sim operations | PARTIAL | [Monitor setup](../../apps/api/app/main.py#L12) exists; feature logs and recorder paths do not universally attach these dimensions. | AUD-024-017 |
| FR-024 | Australian transcript/sub-agent data sovereignty | PARTIAL | [Constitution carve-out](../../.specify/memory/constitution.md#L245) explicitly narrows inference-only exception; [raw replay](../../apps/api/app/services/simulation/controller_service.py#L588) breaks minimization. AU persistent storage remains mandatory; deployment is UNVERIFIED. | AUD-024-006, AUD-024-008, AUD-024-017 |
| FR-025 | Observer read-only detail/transcript/audit | CONFLICT | [Chat history](../../apps/api/app/api/routes/simulation_chat.py#L101) demands SimulationUser and lacks membership; [page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L590) has no read-only permission input. | AUD-024-002, AUD-024-014 |
| FR-026 | Default 30 messages/min/user | PARTIAL | [Limiter](../../apps/api/app/services/simulation/rate_limiter.py#L16) provides local token buckets, not shared enforcement. | AUD-024-009 |
| FR-027 | CI red-team regression tests | PARTIAL | [Four refusal cases](../../tests/unit/test_simulation_controller_safety.py#L46) exist; [CI test selection](../../.github/workflows/ci.yml#L138) excludes this root unit suite. | AUD-024-016 |
| FR-028 | WCAG 2.2 AA, keyboard, labels, reduced motion | PARTIAL | [Labeled input](../../apps/web/src/components/simulation-chat-pane.tsx#L303) and native buttons exist; replies lack polite announcements and full page audit is unproven. | AUD-024-015 |
| FR-029 | Legend contrast >=4.5:1 and spoken simulation badge | MISSING | [Map composition](../../apps/web/src/app/page.tsx#L243) has no lifecycle overlay/legend; detail labels do not establish this requirement. | AUD-024-013, AUD-024-015 |
| FR-030 | Printable/export-friendly transcript | PARTIAL | [Markdown export](../../apps/web/src/components/simulation-chat-pane.tsx#L205) exists; full transcript, HTML bundle and invariant watermark are incomplete. | AUD-024-008, AUD-024-012 |
| FR-031 | Two-year retention then automatic purge | MISSING | [Container](../../infra/main.bicep#L680) and [turn model](../../packages/domain/src/domain/models/sim_chat_turn.py#L12) have no applicable TTL. | AUD-024-008 |
| FR-032 | Azure Maps resolution or explicit lat/lon fallback | MISSING | [Handler](../../apps/api/app/services/simulation/controller_service.py#L1003) uses a city lookup; unresolved coordinates do not stop confirmation/seeding. | AUD-024-011 |
| FR-033 | Approve pins would-have-published; no transmit | MISSING | [Chat rendering](../../apps/web/src/components/simulation-chat-pane.tsx#L330) has no draft approval/discard; no disposition writer found in bounded simulation/public-alert search. | AUD-024-012 |
| FR-034 | Model outage makes chat read-only, independent controls/data work | CONFLICT | [Error reducer](../../apps/web/src/components/simulation-chat-pane.tsx#L553) only changes message text; [input](../../apps/web/src/components/simulation-chat-pane.tsx#L303) re-enables after stream. | AUD-024-014 |
| FR-035 | One primary coordinator; observer/handover flow | MISSING | [Tenant model](../../packages/domain/src/domain/models/simulation_tenant.py#L37) has creator/participants but no primary-owner claim; original routes expose no handover. | AUD-024-002 |
| FR-036 | Stop cancels in-flight queries with cancelled-by-stop; safe completion allowed | MISSING | [UI Stop](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L262) archives; [registry](../../apps/api/app/services/simulation/cancellation.py#L38) has no production registration callers in inspected API code. | AUD-024-004 |
| FR-037 | Versioned prompt/tools; hash every turn | PARTIAL | [Startup prompt load/hash](../../apps/api/app/services/simulation/controller_service.py#L125) and turn hash exist; separate manifest binding and all-outcome provenance are incomplete. | AUD-024-007 |
| FR-038 | 30/min/user/sim and 120/min/owning tenant | PARTIAL | [Dictionary keys](../../apps/api/app/services/simulation/rate_limiter.py#L22) use sim tenant and user; aggregate owner key and shared atomic storage are absent. | AUD-024-009 |
| FR-039 | >=200 prompts every simulation PR and nightly main; blocking regression | CONFLICT | [T093](tasks.md#L88) says 50 on PR; neither named CI lane exists; [citation loop](../../tests/integration/test_hallucinated_citation_suppression.py#L115) is not a Controller jailbreak run. | AUD-024-016, AUD-024-018 |
| FR-040 | Non-dismissible NEMA banner, toast, audit and three-tool restriction | MISSING | [Static tool check](../../apps/api/app/services/simulation/controller_service.py#L761) and chat event reducer have no throttle-state branch. | AUD-024-005 |

## Success-Criterion Coverage

UNVERIFIED in this table means the quantitative outcome has not been demonstrated; it does not excuse
the concrete implementation gaps in the accompanying evidence.

| Criterion | Original target | Status | Evidence and measurement limitation | Follow-up |
| --- | --- | --- | --- | --- |
| SC-001 | Chat-only viable start to initial tasking <90s | UNVERIFIED | [Auto-confirm/counter path](../../apps/api/app/services/simulation/controller_service.py#L990) is not viable scenario/tasking delivery; no timed original journey result. | AUD-024-001, AUD-024-010, AUD-024-016 |
| SC-002 | 100% blocked, zero real deliveries in 10,000 attempts | UNVERIFIED | [Direct wrapper tests](../../tests/unit/test_simulation_controller_safety.py#L76) are not the 10,000-message/channel proof; disconnected boundaries remain. | AUD-024-003, AUD-024-016 |
| SC-003 | 95% routine agent replies <=10s end-to-end | UNVERIFIED | [Agent handler](../../apps/agents/dispatcher/agent.py#L225) calls a model with a 60s timeout; no P95 result for actual operational state queries. | AUD-024-010, AUD-024-016, AUD-024-017 |
| SC-004 | Recover 100% of turns/tools/transitions with full provenance | PARTIAL | [Event payloads](../../apps/api/app/services/simulation_event_recorder.py#L137) omit complete tool results/correlation/actor; fallback memory can lose turns. | AUD-024-007, AUD-024-008 |
| SC-005 | >=99% refusal/safety over >=200 adversarial prompts in CI | UNVERIFIED | [Four input cases](../../tests/unit/test_simulation_controller_safety.py#L46) and [citation-only loop](../../tests/integration/test_hallucinated_citation_suppression.py#L115) do not establish this rate. | AUD-024-006, AUD-024-016 |
| SC-006 | >=95% first-glance sim/live discrimination by operators | UNVERIFIED | [Map host](../../apps/web/src/app/page.tsx#L243) lacks combined simulation overlays; no attributable operator study found in feature documents/evidence. | AUD-024-013, AUD-024-016 |
| SC-007 | Automated plus manual WCAG 2.2 AA; zero critical findings | UNVERIFIED | [Page test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L19) is uncollected under current config and tolerates missing chat; no manual audit evidence. | AUD-024-015, AUD-024-016 |
| SC-008 | NEMA throttle <=5s and no sim interference with live work | UNVERIFIED | [Governor flag update](../../apps/api/app/services/resource_governor.py#L75) has no connected chat enforcement/notification or latency/isolation measurement. | AUD-024-005, AUD-024-016 |

## Acceptance Scenarios

Accounting: US1 has 4, US2 has 4, US3 has 3, US4 has 4, US5 has 3, totaling **18**.
IDs below are audit-local labels for the original story/scenario ordinals; no original scenario is omitted.

| Scenario | Expected acceptance | Status | Evidence and gap | Follow-up |
| --- | --- | --- | --- | --- |
| US1-AS1 | Coordinator receives full Katoomba card <=8s while draft | CONFLICT | [Handler](../../apps/api/app/services/simulation/controller_service.py#L990) confirms immediately; [tenant creation](../../apps/api/app/services/simulation_service.py#L89) is Active; 8s unmeasured. | AUD-024-001, AUD-024-002, AUD-024-011, AUD-024-016 |
| US1-AS2 | Confirm & Start activates, streams sim BOM/IoT, three agent actions <=30s | MISSING | [Seed helper](../../apps/api/app/services/simulation/controller_service.py#L1081) increments counters, not signals/tasking; no confirmation UI/start route. | AUD-024-001, AUD-024-004, AUD-024-010 |
| US1-AS3 | Malformed/real-world request is helpfully refused and audited | PARTIAL | [Patterns](../../apps/api/app/services/simulation/controller_service.py#L62) cover selected phrases, not all malformed/off-topic requests or malicious model outputs. | AUD-024-006, AUD-024-007, AUD-024-016 |
| US1-AS4 | Add a southern spot fire to active scenario, live data unchanged | PARTIAL | [Seed handler](../../apps/api/app/services/simulation/controller_service.py#L990) emits another card/counter task, not a tenant-scoped timeline append. | AUD-024-001, AUD-024-011 |
| US2-AS1 | Pause stops new signals/tasking, allows notes, paused map style | CONFLICT | [Counter helper](../../apps/api/app/services/simulation/controller_service.py#L1096) accepts Paused; chat ungated; detail map maps Paused to active. | AUD-024-004, AUD-024-013, AUD-024-018 |
| US2-AS2 | Resume continues from paused state without replay | PARTIAL | [Clock-aware resume](../../apps/api/app/services/simulation_service.py#L150) exists; original chat seeding is not a signal scheduler and no full journey/no-replay proof exists. | AUD-024-004, AUD-024-016 |
| US2-AS3 | Stop ends, stops emitters/releases locks/disables input/creates report | MISSING | [Stop UI](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L262) archives; [report generation](../../apps/api/app/services/exercise_report_service.py#L31) is a separate on-demand service. | AUD-024-004, AUD-024-007 |
| US2-AS4 | Live NEMA Level-3 throttles without pausing and shows banner | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L75) changes flags only; no live banner/three-tool enforcement. | AUD-024-005 |
| US3-AS1 | Planning IAP summary <=10s with clickable identifier | PARTIAL | [Dispatcher](../../apps/agents/dispatcher/agent.py#L209) returns role-framed model text and empty citations, not current IAP. | AUD-024-010, AUD-024-016 |
| US3-AS2 | AWS watermarked PIO draft; Approve/Discard stays sim-only | PARTIAL | [Warning tool](../../apps/api/app/services/simulation/controller_service.py#L955) watermarks a string; no validated approval/disposition UI or durable draft path. | AUD-024-012 |
| US3-AS3 | Real integration intercepted with synthetic-delivery receipt | PARTIAL | [Publication equivalent](../../apps/api/app/services/public_alert_service.py#L82) returns a simulation dictionary, not the canonical receipt; wrapper is not a universal boundary. | AUD-024-003 |
| US4-AS1 | Live plus active simulation shown distinctly with both legend entries | MISSING | [Homepage data loader](../../apps/web/src/app/page.tsx#L102) fetches only incidents. | AUD-024-013 |
| US4-AS2 | Paused overlay is desaturated amber with SIM PAUSED text | MISSING | [Detail marker conversion](../../apps/web/src/components/simulation-map.tsx#L162) maps Paused to active; no lifecycle layer on main map. | AUD-024-013 |
| US4-AS3 | Ended >24h hidden by default; toggle reveals | MISSING | [Map page](../../apps/web/src/app/page.tsx#L76) has no ended input/time predicate/toggle. | AUD-024-013 |
| US4-AS4 | Observer clicks overlay and gets read-only details | MISSING | No overlay deep link and [role guard](../../apps/api/app/core/auth.py#L13) does not recognize the specified Observer role. | AUD-024-002, AUD-024-013 |
| US5-AS1 | Sim SMS receives 410 SIM_EGRESS_BLOCKED and audit receipt | CONFLICT | [Delivery return](../../apps/api/app/services/public_alert_service.py#L94) is a normal simulation result; no 410/receipt path. | AUD-024-003 |
| US5-AS2 | Broadcast stopped by HTTP wrapper before network | PARTIAL | [Wrapper](../../apps/api/app/clients/outbound_http.py#L64) can block a direct write, but integration/callers and missing-context behavior do not establish broadcast protection. | AUD-024-003 |
| US5-AS3 | Every one of 100/min outbound attempts has hash/channel/reason | PARTIAL | [Receipt service](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L32) can create records; no all-channel connected path/durable paging or 100-message assertion. | AUD-024-003, AUD-024-008, AUD-024-016 |

The five **Independent Test** descriptions are additional composite obligations, not extra numbered
acceptance scenarios:

| Composite | Status | Accounting and evidence | Follow-up |
| --- | --- | --- | --- |
| US1-IT | PARTIAL | Card/active/signals/three tasking records/map <=10s must be checked together; [current seeder](../../apps/api/app/services/simulation/controller_service.py#L990) is insufficient. | AUD-024-001, AUD-024-010, AUD-024-013, AUD-024-016 |
| US2-IT | PARTIAL | Pause/resume emitter quiescence <=5s, terminal Stop and disabled input: [lifecycle service](../../apps/api/app/services/simulation_service.py#L131) only supplies part. | AUD-024-004, AUD-024-016 |
| US3-IT | PARTIAL | Planning/tankers/PIO queries must all yield substantive correct-agent output and request/response audit; [dispatcher](../../apps/agents/dispatcher/agent.py#L209) has no operational data lookup. | AUD-024-007, AUD-024-010, AUD-024-012 |
| US4-IT | MISSING | Sim plus live rendering, style, badge and spoken 'simulation' require the [actual map host](../../apps/web/src/app/page.tsx#L243). | AUD-024-013, AUD-024-015 |
| US5-IT | PARTIAL | SMS/email/broadcast/social zero delivery plus payload/channel receipt: [unit wrapper test](../../tests/unit/test_simulation_controller_safety.py#L76) is not a channel integration test. | AUD-024-003, AUD-024-016 |

## Edge Cases

| Edge | Original obligation | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| EC-01 | Unsafe/jailbroken tool output refused by server allow-list | PARTIAL | [Unknown names refused](../../apps/api/app/services/simulation/controller_service.py#L761); allowed-tool arguments, confirmation, output safety and state still insufficient. | AUD-024-001, AUD-024-006, AUD-024-011 |
| EC-02 | Unknown sub-agent gives sanitized error with no tasking | PARTIAL | [Invoker unknown-agent branch](../../apps/api/app/services/simulation/sub_agent_invoker.py#L98) avoids invocation; it echoes the unknown ID and lacks full sanitized/audited contract assertions. | AUD-024-007, AUD-024-010 |
| EC-03 | PII redacted with warning and Australian boundary | CONFLICT | [Raw history](../../apps/api/app/services/simulation/controller_service.py#L346) is stored/replayed; current-message-only gateway does not close the boundary. | AUD-024-006 |
| EC-04 | Closing/reopening restores authoritative server snapshot | PARTIAL | [History hydration](../../apps/web/src/components/simulation-chat-pane.tsx#L79) and server clock exist; best-effort storage, local objectives, truncated history and no lifecycle subscription remain. | AUD-024-004, AUD-024-008, AUD-024-014 |
| EC-05 | >30s acknowledgment/progress; 120s graceful timeout | PARTIAL | [Invoker timeout](../../apps/api/app/services/simulation/sub_agent_invoker.py#L109) exists; callback is not wired to chat and offline tool event arrives after waiting. | AUD-024-010, AUD-024-014 |
| EC-06 | Partition uses cached last-known state and marks degraded | MISSING | [Adapter errors](../../apps/api/app/services/simulation/sub_agents/_base.py#L71) return empty/degraded summaries, not cached state. | AUD-024-010 |
| EC-07 | Multiple coordinators: control arbitration, separate transcripts, shared audit | CONFLICT | Original last-write-wins conflicts with FR-035 primary ownership; [history](../../apps/api/app/repositories/sim_chat_history_repository.py#L116) is per tenant, not coordinator. | AUD-024-002, AUD-024-008, AUD-024-018 |
| EC-08 | Active >24h without chat auto-pauses with notification | MISSING | [Expiry service](../../apps/api/app/services/simulation_service.py#L231) archives by expiry; no last-chat idle auto-pause/notification found in lifecycle/controller/governor paths. | AUD-024-004 |

## Original Task Coverage

There are **49** original IDs, no suffix IDs in this task list, and **zero checkbox markers**.
`none` preserves that authored state; it does not mean unchecked or complete. The required five columns
are task ID, original checkbox state, evidence status, concrete evidence, and open follow-up IDs.

| Task | Original checkbox state | Status | Concrete evidence links/explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | none | PARTIAL | [Chat](../../packages/domain/src/domain/models/sim_chat_turn.py#L12), [tool](../../packages/domain/src/domain/models/sim_tool_invocation.py#L28), [card](../../packages/domain/src/domain/models/sim_scenario_card.py#L21), [delivery](../../packages/domain/src/domain/models/sim_synthetic_delivery.py#L10) models exist; optional audit fields, absent TTL and unwired card/tool validation prevent full data-model conformance. | AUD-024-007, AUD-024-008, AUD-024-011 |
| T002 | none | CONFLICT | [Transition map](../../packages/domain/src/domain/models/simulation_tenant.py#L15) omits draft/ended and allows direct Active-to-Archiving. | AUD-024-004 |
| T003 | none | PARTIAL | [Relocated sim-chat container](../../infra/main.bicep#L680) has tenant partition/index, no two-year TTL; no matching three-store migration in scoped infra/scripts/tooling search. | AUD-024-008 |
| T004 | none | PARTIAL | [History repository](../../apps/api/app/repositories/sim_chat_history_repository.py#L29) provides synchronous append/tail, not three async cursor-paged stores; later audit infrastructure does not supply missing chat lineage. | AUD-024-007, AUD-024-008 |
| T010 | none | PARTIAL | [HTTP wrapper](../../apps/api/app/clients/outbound_http.py#L39) blocks guarded simulation writes, but GET/missing context/caller integration are gaps. | AUD-024-003 |
| T011 | none | PARTIAL | [Receipt service](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L27) builds hashed records and attempts canonical audit; default feature repository is memory. | AUD-024-003, AUD-024-008 |
| T012 | none | PARTIAL | [PublicAlertService](../../apps/api/app/services/public_alert_service.py#L82) is the located equivalent; its gate does not call receipt service or return contracted 410. | AUD-024-003 |
| T013 | none | MISSING | [Raw production HTTP](../../apps/api/app/api/routes/simulation_chat.py#L28), [adapter call](../../apps/api/app/services/simulation/sub_agents/_base.py#L59), [basic Ruff rules](../../ruff.toml#L13); no custom raw-client lint found in tools/scripts/workflows. | AUD-024-003, AUD-024-016 |
| T014 | none | PARTIAL | [Existing middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) sets context for some requests but defaults paths to live, logs non-members and is wired without repository. | AUD-024-002, AUD-024-003 |
| T020 | none | PARTIAL | [Two local token buckets](../../apps/api/app/services/simulation/rate_limiter.py#L16) exist; no Redis/shared atomics or owner-tenant aggregate. | AUD-024-009 |
| T021 | none | MISSING | [Built-in geocoder](../../apps/api/app/services/simulation/controller_service.py#L1003) is not Azure Maps or explicit lat/lon fallback; no relocated resolver call found. | AUD-024-011 |
| T030 | none | CONFLICT | [Versioned prompt](../../apps/api/app/services/simulation/controller_prompt.md#L17) contains scope/refusal/tool/watermark rules but explicitly denies required confirmation. | AUD-024-001, AUD-024-006, AUD-024-007 |
| T031 | none | PARTIAL | [Registry](../../apps/api/app/services/simulation/controller_tools.py#L12) supplies JSON schemas and allow-list; Pydantic argument validation is not used and later advertised tools lack matching handlers. | AUD-024-001, AUD-024-011, AUD-024-018 |
| T032 | none | PARTIAL | [Production registry](../../apps/api/app/services/simulation/sub_agent_invoker.py#L148) reaches [dispatcher](../../apps/agents/dispatcher/agent.py#L209); no actual current operational service data or citations. | AUD-024-010 |
| T033 | none | PARTIAL | [Controller](../../apps/api/app/services/simulation/controller_service.py#L324) streams/dispatches and hashes prompt; confirmation, safety, audit, progress, quota and typed errors incomplete. | AUD-024-001, AUD-024-006, AUD-024-007, AUD-024-009, AUD-024-010, AUD-024-014 |
| T034 | none | PARTIAL | [Domain card](../../packages/domain/src/domain/models/sim_scenario_card.py#L21) exists but [handler](../../apps/api/app/services/simulation/controller_service.py#L990) constructs incompatible unchecked dictionaries. | AUD-024-001, AUD-024-011 |
| T035 | none | PARTIAL | [Unknown tool branch](../../apps/api/app/services/simulation/controller_service.py#L761) refuses and feeds model result; stock visible refusal and complete tool_denied audit not guaranteed. | AUD-024-006, AUD-024-007 |
| T040 | none | PARTIAL | [Mounted tenant controls](../../apps/api/app/api/routes/simulations.py#L283) offer pause/resume/archive, not confirmed start/terminal stop/handover; later duplicate routes are not a reconciled contract. | AUD-024-001, AUD-024-002, AUD-024-004 |
| T041 | none | PARTIAL | [Cancellation helper](../../apps/api/app/services/simulation/cancellation.py#L38) and [abort caller](../../apps/api/app/api/routes/simulations_036.py#L527) exist, but chat work is not registered and UI Stop never calls them. | AUD-024-004 |
| T042 | none | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L75) updates flags only; no Controller three-tool branch or banner SSE emission. | AUD-024-005 |
| T050 | none | PARTIAL | [POST/history](../../apps/api/app/api/routes/simulation_chat.py#L58) are registered; original GET transcript/cursor and POST cancel are absent. | AUD-024-002, AUD-024-008, AUD-024-014 |
| T051 | none | CONFLICT | [Guard](../../apps/api/app/api/dependencies/rbac.py#L12) requires SimulationUser, not Coordinator/Observer/primary claim; chat reads lack membership. | AUD-024-002 |
| T052 | none | PARTIAL | [Router registration](../../apps/api/app/api/router.py#L68) includes chat and existing controls; contracted start/stop/handover/cancel have no registered equivalent. | AUD-024-004, AUD-024-014 |
| T060 | none | PARTIAL | [Typed client](../../apps/web/src/lib/api/simulation_chat.ts#L26) exists; hand parser instead of eventsource-parser, auth/correlation/CRLF/EOF behavior incomplete. | AUD-024-014 |
| T061 | none | PARTIAL | [Composed controls](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L423) show status and three verbs; no Start, top sticky control bar, role/primary gating or contracted Stop. | AUD-024-001, AUD-024-002, AUD-024-004 |
| T062 | none | PARTIAL | [Chat pane](../../apps/web/src/components/simulation-chat-pane.tsx#L45) streams and shows tool/card hints; no confirmation or warning Approve/Discard/disposition, lifecycle gating or outage read-only state. | AUD-024-001, AUD-024-012, AUD-024-014 |
| T063 | none | MISSING | [Card chip](../../apps/web/src/components/simulation-chat-pane.tsx#L406) announces seeded instead of complete card/Confirm & Start; no relocated approval interaction. | AUD-024-001, AUD-024-011 |
| T064 | none | MISSING | [Event reducer](../../apps/web/src/components/simulation-chat-pane.tsx#L483) lacks banner.throttle handling and no dedicated connected banner found. | AUD-024-005 |
| T065 | none | PARTIAL | [Detail page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L285) preserves lists, adds right chat/map and side controls; role/state/a11y/layout commitments incomplete. | AUD-024-002, AUD-024-004, AUD-024-015 |
| T066 | none | PARTIAL | [Relocated private message renderer](../../apps/web/src/components/simulation-chat-pane.tsx#L330) exists and later SimBadge is reused; specified accessible reusable shell/message/full-watermark behavior is incomplete. | AUD-024-012, AUD-024-015 |
| T070 | none | MISSING | [Incident map route](../../apps/api/app/api/routes/incidents_map.py#L111) serves incidents, no simulation lifecycle source among mounted routes. | AUD-024-013 |
| T071 | none | PARTIAL | [Detail map](../../apps/web/src/components/simulation-map.tsx#L146) supplies [SIM] marker titles and optional later overlays, not active/paused/ended styling on main Disaster Map. | AUD-024-013 |
| T072 | none | MISSING | [Main map](../../apps/web/src/app/page.tsx#L243) has no simulation legend or ended-age toggle. | AUD-024-013 |
| T073 | none | MISSING | [Main sidebar](../../apps/web/src/app/page.tsx#L263) is incident-only; no simulation deep link with Observer read-only handling. | AUD-024-002, AUD-024-013 |
| T080 | none | PARTIAL | [Safety tests](../../tests/unit/test_simulation_controller_safety.py#L17) cover registry/burst/wrapper; no actual scenario validation/location fallback/replica quota coverage. | AUD-024-003, AUD-024-009, AUD-024-011, AUD-024-016 |
| T081 | none | MISSING | No original chat SSE/control contract test in scoped test inventory; [wiring test](../../apps/api/tests/test_simulation_chat_controller_wiring.py#L22) asserts only registered role names. | AUD-024-016 |
| T082 | none | PARTIAL | [Lifecycle unit tests](../../tests/unit/test_simulation_service.py#L90) and [governor tests](../../tests/unit/test_resource_governor.py#L34) are not mounted chat-to-stop/throttle/handover integration. | AUD-024-002, AUD-024-004, AUD-024-005, AUD-024-010, AUD-024-016 |
| T083 | none | MISSING | [Direct egress unit](../../tests/unit/test_simulation_controller_safety.py#L76) and [policy canary](../../tests/contract/test_egress_block.py#L46) do not implement 10,000 mocked public-message attempts. | AUD-024-003, AUD-024-016 |
| T084 | none | PARTIAL | [Four refusal cases](../../tests/unit/test_simulation_controller_safety.py#L46); later 200-loop only tests citation filtering, no Controller >=99% safety rate. | AUD-024-006, AUD-024-016 |
| T085 | none | PARTIAL | [Uncollected page test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L19) tolerates absent receipt; [included map label tests](../../apps/web/tests/a11y/simulation-map-non-point.test.tsx#L89) use a stubbed map. | AUD-024-015, AUD-024-016 |
| T086 | none | MISSING | [Found playback E2E](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L19) calls evaluator idempotency, not the original coordinator journey; bounded searches found no confirm-card journey. | AUD-024-016 |
| T087 | none | MISSING | [Error display](../../apps/web/src/components/simulation-chat-pane.tsx#L553) shows friendly text but no 503-driven read-only/degradation test or state. | AUD-024-014, AUD-024-016 |
| T088 | none | PARTIAL | [Markdown export](../../apps/web/src/components/simulation-chat-pane.tsx#L205) omits HTML bundle, enforced watermark, complete paged audit transcript. | AUD-024-008, AUD-024-012 |
| T090 | none | PARTIAL | [Monitor initialization](../../apps/api/app/main.py#L12) and feature logging exist, not universal required custom dimensions. | AUD-024-007, AUD-024-017 |
| T091 | none | PARTIAL | [Later observability alert](../../infra/bicep/modules/observability-alerts.bicep#L158) is not the specified workbook/refusal-rate/quota trio and emitting/reachable deployment path is incomplete. | AUD-024-017 |
| T092 | none | PARTIAL | [azd manifest](../../azure.yaml#L9) and [Foundry env](../../infra/main.bicep#L1037) exist; [quickstart](quickstart.md#L10) uses obsolete variables/containers and lacks current readiness prerequisites. | AUD-024-017, AUD-024-018 |
| T093 | none | CONFLICT | [Task's 50-prompt PR subset](tasks.md#L88) conflicts with FR-039/CHK011; [CI](../../.github/workflows/ci.yml#L138) and manual simulation workflows do not provide required lanes. | AUD-024-016, AUD-024-018 |
| T100 | none | MISSING | [Root README](../../README.md#L1) lacks a Simulations Chat section/link in the literal-file search; local quickstart alone does not satisfy a root entrypoint. | AUD-024-017 |
| T101 | none | MISSING | No leak-response runbook in docs/runbooks or searched operator/configuration docs; [later alert](../../infra/bicep/modules/observability-alerts.bicep#L169) references another absent runbook. | AUD-024-017 |

## Unnumbered and Amendment Coverage

Labels CL, CO, TC, NF, EN and OS below are audit-local accounting labels for original unnumbered
obligations, not newly invented product requirements. No separate SCP-* requirement is declared in
this spec; its actual scope bullets and the ASM/PER/HYP additions are all accounted for below.

### Clarifications

| Item | Original decision | Status | Evidence and follow-up |
| --- | --- | --- | --- |
| CL-01 | Stop cancels in-flight, cancelled-by-stop, idempotent completion allowed | PARTIAL | [Registry](../../apps/api/app/services/simulation/cancellation.py#L38) exists but not registered by chat/Stop. AUD-024-004/007. |
| CL-02 | Versioned startup prompt/tool manifest hash on every turn | PARTIAL | [Prompt startup](../../apps/api/app/services/simulation/controller_service.py#L125) hashes prompt; full manifest/all-outcome audit incomplete. AUD-024-007. |
| CL-03 | 30/user/sim and 120/tenant rate limits | PARTIAL | [Limiter](../../apps/api/app/services/simulation/rate_limiter.py#L16) is local; owning-tenant key ambiguous. AUD-024-009/018. |
| CL-04 | Every simulation PR plus nightly main; >=200; block regressions | CONFLICT | [T093](tasks.md#L88) uses 50 PR prompts, while required lanes do not exist. AUD-024-016/018. |
| CL-05 | NEMA banner/toast/audit and only summarize/pause/stop | MISSING | [Static dispatch](../../apps/api/app/services/simulation/controller_service.py#L761) ignores throttle. AUD-024-005. |

### Assumptions and Personas

| Item | Status | Evidence, qualification and follow-up |
| --- | --- | --- |
| A1 | PARTIAL | Existing [tenant provisioning](../../apps/api/app/services/simulation_service.py#L40) is reused, but [chat membership checks](../../apps/api/app/api/routes/simulation_chat.py#L59) are not preserved. AUD-024-002. |
| A2 | SUPERSEDED | Only the legacy Azure OpenAI deployment/configuration assumption is replaced by [explicit Foundry migration](../036-foundry-rag-grounding/spec.md#L19) and [bounded inference carve-out](../../.specify/memory/constitution.md#L245). Persistent AU storage and safety remain mandatory; availability is UNVERIFIED. AUD-024-006/017. |
| A3 | CONFLICT | [Specified role split](spec.md#L55) versus [SimulationUser-only guard](../../apps/api/app/core/auth.py#L13); Observer/primary semantics not implemented. AUD-024-002. |
| A4 | PARTIAL | [Publication equivalent](../../apps/api/app/services/public_alert_service.py#L82) blocks by request context but does not create the required receipt. AUD-024-003. |
| A5 | PARTIAL | [Existing map](../../apps/web/src/app/page.tsx#L102) is reused, but tenant-scoped simulation layer is not connected. AUD-024-013. |
| A6 | SUPERSEDED | Future acceleration is explicitly implemented by [warp feature's default-1x decision](../026-sim-warp-playback/spec.md#L16); original wall-clock default remains compatible. No waiver of 024 lifecycle safety. |
| ASM-071 | PARTIAL | [AU-v1 scope](spec.md#L436) and [D-009 deferral](../028-capstone-alignment/evidence/decision-record.md#L14) are authored; deployed AU residency not independently verified. AUD-024-006/017/018. |
| ASM-072 | UNVERIFIED | [Consultation commitment](spec.md#L437) and local cohort review exist, but no attributable per-change ux-designer/product-owner-ba consultation transcript is attached. AUD-024-018. |
| ASM-073 | IMPLEMENTED | [Taxonomy/schema deferral](spec.md#L438) explicitly references the [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1); this is a documentation delegation, not schema-validation success. |
| PER-064 | UNVERIFIED | [AU persona reference](spec.md#L444) points to [root persona roles](../001-disaster-response-hub/spec.md#L169), which say concrete SME identities are recorded during review; no spec-specific signed validation supplied. AUD-024-018. |
| PER-065 | UNVERIFIED | [Technical persona reference](spec.md#L445) points to [actor catalogue](../004-actor-github-agents/spec.md#L88); catalogue existence is not named/date-stamped validation. AUD-024-018. |
| PER-066 | IMPLEMENTED | [Non-AU placeholder](spec.md#L446) explicitly retains D-009/SME prerequisites; [decision record](../028-capstone-alignment/evidence/decision-record.md#L20) confirms deferral. This status credits the authored boundary only, not country delivery or interviews. |
| HYP-022 | UNVERIFIED | [Hypothesis](spec.md#L452) is falsifiable, but its named stub is absent from the three-file evidence directory. [Postfeature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L3) is portfolio structural scoring, not a 024-specific consultation/causal test. AUD-024-018. |

### Operational and Sector Cohorts

Every original cohort row is assessed. Later jurisdiction/feed helpers were considered as neighboring
artifacts; the Controller's traced generic dispatcher does not call them, so their existence is not
treated as delivered conversational behavior.

| Item | Original cohort asks | Status | Current evidence and follow-up |
| --- | --- | --- | --- |
| CO-01 | AIIMS command/control/coordination, no real orders, full provenance, Observer view, PIO watermark | PARTIAL | [Scope prompt](../../apps/api/app/services/simulation/controller_prompt.md#L3) exists; authorization, real-state coordination, complete audit and all-artifact watermark gaps remain. AUD-024-002/003/007/010/012. |
| CO-02 | NSW terminology, SFAZ/LGA/RFS districts, combat-agency mapping | PARTIAL | [Katoomba/city lookup](../../apps/api/app/services/simulation/controller_service.py#L1041) and hazard labels exist; no Controller jurisdiction/agency-boundary resolution. AUD-024-010/011. |
| CO-03 | VIC CFA/FRV boundaries, warning categories, Code Red modelling | PARTIAL | [Generic parameters](../../apps/api/app/services/simulation/controller_tools.py#L46) accept free-form input; no validated jurisdiction-specific planning path. AUD-024-010/011. |
| CO-04 | QLD cyclone categories and storm tide/surge selectable in chat | PARTIAL | [Cyclone enum/parameters](../../packages/domain/src/domain/models/sim_scenario_card.py#L25) exist, but conditions are unvalidated/unseeded and hidden in the card chip. AUD-024-001/011. |
| CO-05 | SA/WA/TAS/NT/ACT parity, DFES combined agency, NT cyclone | PARTIAL | [Eight centroids](../../apps/web/src/components/simulation-map.tsx#L35) are authored; centroids and generic model replies do not prove correct agency/parity outcomes. AUD-024-010/011/013. |
| CO-06 | BOM synthetic weather, simulated NEMA escalation, sim-only ADF DACC | PARTIAL | [Counter seeder](../../apps/api/app/services/simulation/controller_service.py#L1081) is not a BOM source/timeline; NEMA policy disconnected. AUD-024-001/003/005/010. |
| CO-07 | Multi-organization interoperability, V/Line and Leeton EvacCentre language | PARTIAL | [Participants](../../apps/api/app/api/routes/simulations.py#L239) store OIDs, but Controller lacks structured organization/landmark/tasking resolution. AUD-024-002/010/011. |
| CO-08 | Technical safety/AI/a11y/test constraints delegated to plan | PARTIAL | All 17 plan commitments are separately assessed below; authoring a cohort table is not proof of delivery. AUD-024-015/016/017/018. |

### Technical Cohorts and Nonfunctional Constraints

| Item | Original commitment | Status | Evidence and follow-up |
| --- | --- | --- | --- |
| TC-01 | Solution Architect: reuse tenant/model deployment, no new model infrastructure | PARTIAL | [Service reuse](../../apps/api/app/services/simulation_service.py#L24) and [Foundry migration](../036-foundry-rag-grounding/spec.md#L19) exist; scenario/lifecycle contract incomplete. AUD-024-001/004. |
| TC-02 | Azure Architect: AU region, private endpoint, Key Vault configuration | PARTIAL | [Current infrastructure](../../infra/main.bicep#L1037) uses managed identity/Foundry configuration; old API-key assumption is superseded, deployed AU/private-path evidence unverified. AUD-024-006/017. |
| TC-03 | AI/ML: prompt hash, input/output content safety, enforced function calls | PARTIAL | [Prompt hash](../../apps/api/app/services/simulation/controller_service.py#L125) and name check exist, not complete safety or schema validation. AUD-024-006/007/011. |
| TC-04 | API: versioned POST SSE and control routes | PARTIAL | [Chat route](../../apps/api/app/api/routes/simulation_chat.py#L58), actual /api prefix and missing original GET/cancel/start/stop/handover differ. AUD-024-004/014. |
| TC-05 | Security: independent transport gate, verified tenant claim, RBAC everywhere | PARTIAL | [Wrapper](../../apps/api/app/clients/outbound_http.py#L64) and [route](../../apps/api/app/api/routes/simulation_chat.py#L59) lack connected fail-closed guarantees. AUD-024-002/003. |
| TC-06 | Data: three logical stores, two-year TTL, channel/time index | PARTIAL | [sim-chat](../../infra/main.bicep#L680) is the only original-store equivalent with visible infrastructure; other records/TTL/indexes incomplete. AUD-024-008. |
| TC-07 | SRE: P95 <=10s chat/0.5s controls, 1% monthly error budget, quarterly model-outage drill | UNVERIFIED | [Timeout code](../../apps/api/app/services/simulation/sub_agent_invoker.py#L109) is not latency/error-budget/drill evidence. AUD-024-014/016/017. |
| TC-08 | DevOps: CI jailbreak and documented OpenAI/Maps variables | PARTIAL | [Current env wiring](../../infra/main.bicep#L1037) exists; original quickstart and CI cadence are stale/incomplete. AUD-024-016/017. |
| TC-09 | UX: 420px right chat, sticky top controls, design tokens, reduced motion | CONFLICT | [CSS](../../apps/web/src/app/globals.css#L2805) uses 380px/340px and stacked mobile layout; [controls](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L423) are in sidebar, not sticky top. AUD-024-015/018. |
| TC-10 | QA: pytest/Playwright, tool contracts, jailbreak tests | PARTIAL | [Safety cases](../../tests/unit/test_simulation_controller_safety.py#L17) and [component assertions](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L14) are narrower than original requirements. AUD-024-016. |
| TC-11 | Accessibility: polite Controller replies and axe in CI | PARTIAL | [Chat list](../../apps/web/src/components/simulation-chat-pane.tsx#L258) lacks live region; page axe test not collected. AUD-024-015/016. |
| TC-12 | Compliance: documented retention, residency attestation, audit export | PARTIAL | [Export](../../apps/web/src/components/simulation-chat-pane.tsx#L205) and authored retention prose exist; TTL, full audit and attributable attestation absent. AUD-024-008/012/017/018. |
| TC-13 | Principal Engineer: no raw requests/httpx; lint rule | MISSING | [Raw adapter HTTP](../../apps/api/app/services/simulation/sub_agents/_base.py#L59) and [Ruff rules](../../ruff.toml#L13) contradict the obligation. AUD-024-003/016. |
| TC-14 | Chaos: sub-agent failure, OpenAI 429, egress bypass | PARTIAL | [Timeout helper test](../../apps/api/tests/test_sub_agent_invoker.py#L37) is not the full mounted fault-injection set. AUD-024-003/010/014/016. |
| TC-15 | Container: reuse API image and configured OTel | PARTIAL | [azd services](../../azure.yaml#L29) reuse images; [Monitor init](../../apps/api/app/main.py#L12) exists, but complete sim telemetry is not established. AUD-024-017. |
| TC-16 | Product/BA: SC-001..008 mapped to acceptance tests | PARTIAL | [Analysis matrix](analysis-report.md#L5) maps FRs to tasks, not all SCs to effective measured tests. AUD-024-016/018. |
| TC-17 | Developer: thin routes/services/repositories and Pydantic | PARTIAL | Layers/models exist, but [seed dictionary](../../apps/api/app/services/simulation/controller_service.py#L990) bypasses validation and [history repository](../../apps/api/app/repositories/sim_chat_history_repository.py#L116) blocks/unbounds reads. AUD-024-007/008/011. |

| Item | Additional original plan/research/entity constraint | Status | Evidence and follow-up |
| --- | --- | --- | --- |
| NF-01 | Scenario-card P95 <=8s | UNVERIFIED | No measured path; [handler](../../apps/api/app/services/simulation/controller_service.py#L990) is not validated scenario authoring. AUD-024-001/011/016. |
| NF-02 | Control reaction <=500ms/P95 <=0.5s | UNVERIFIED | [Pause path](../../apps/api/app/services/simulation_service.py#L131) awaits storage, no timing evidence. AUD-024-004/016/017. |
| NF-03 | Egress decision P99 <=5ms | UNVERIFIED | [Guard](../../apps/api/app/clients/outbound_http.py#L74) awaits recording; no measured percentile. AUD-024-003/016/017. |
| NF-04 | <=10 active sims; <=50 observers; one primary | CONFLICT | [Default cap](../../apps/api/app/core/settings.py#L26) is three; no 50-observer/primary-owner enforcement. AUD-024-002/017. |
| NF-05 | Desktop/tablet/minimum 360px and non-overlapping controls | UNVERIFIED | [Responsive CSS](../../apps/web/src/app/globals.css#L3691) exists; browser/layout audit was not executed. AUD-024-015. |
| NF-06 | Data persists only in Australia East/Southeast | UNVERIFIED | [Constitution](../../.specify/memory/constitution.md#L245) preserves storage restriction; no deployment/residency inspection authorized. AUD-024-006/017. |
| NF-07 | Nightly AU Blob Parquet audit export from research R8 | MISSING | [Research R8](research.md#L45) promises this; current [browser export](../../apps/web/src/components/simulation-chat-pane.tsx#L205) is not a scheduled Parquet archive. No matching job in scoped workflows/scripts. AUD-024-008/012/017. |
| NF-08 | Parallel sub-agent aggregation, 10s soft deadline/120s hard cap | PARTIAL | [Invoker](../../apps/api/app/services/simulation/sub_agent_invoker.py#L109) has 120s cap and optional 5s callback; Controller executes calls sequentially. Timing/30s edge/plan soft-deadline wording needs reconciliation. AUD-024-010/018. |
| NF-09 | Existing tenant isolation is not weakened by chat | CONFLICT | [Chat route](../../apps/api/app/api/routes/simulation_chat.py#L59) omits the participant check used by tenant-detail routes. AUD-024-002. |
| NF-10 | No additional external model providers; Azure only | IMPLEMENTED | [Foundry client construction](../../apps/api/app/services/simulation/controller_service.py#L540) uses Azure identity/endpoint; offline branch is deterministic, not another provider. Availability/minimization remain separate gaps. |
| EN-01 | Simulation entity: scenario/participants/draft-active-paused-ended | PARTIAL | [Tenant model](../../packages/domain/src/domain/models/simulation_tenant.py#L37) has scenario/participants but incompatible states. AUD-024-004. |
| EN-02 | Scenario card: location/time/hazard/conditions/AWS level and authorized confirmation | PARTIAL | [Model](../../packages/domain/src/domain/models/sim_scenario_card.py#L21) exists; actual card shape/validation/confirmation differ. AUD-024-001/011. |
| EN-03 | Chat turn: role/content/model/tenant/time/hash/tool linkage | PARTIAL | [Turn model](../../packages/domain/src/domain/models/sim_chat_turn.py#L12) exists; fields/linkage/full auditing incomplete. AUD-024-007/008. |
| EN-04 | Tool invocation: allow-list/args/context/agent/result/latency/outcome | PARTIAL | [Invocation model](../../packages/domain/src/domain/models/sim_tool_invocation.py#L28) is not instantiated by the chat path. AUD-024-007/011. |
| EN-05 | Synthetic delivery: channel/audience/hash/reason/time/tenant | PARTIAL | [Builder](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L32) supplies shape, not every-call/durable guarantee. AUD-024-003/008. |
| EN-06 | Map overlay: ID/state style/geometry/linked simulation | PARTIAL | [Detail markers](../../apps/web/src/components/simulation-map.tsx#L146) exist but no main-map lifecycle overlay entity/source. AUD-024-013. |

### Scope and Replacement Decisions

| Item | Original boundary | Status | Evidence and interpretation |
| --- | --- | --- | --- |
| OS-01 | Delivery-hygiene/meta feature, not capstone critical-path owner | IMPLEMENTED | [Scope amendment](spec.md#L411) is authored. It does not lower any MUST or release-blocking safety obligation; AUD-024-018 preserves that distinction. |
| OS-02 | Accelerated playback deferred | SUPERSEDED | [Later warp feature](../026-sim-warp-playback/spec.md#L16) explicitly adds acceleration and preserves default 1x; only this deferral is replaced. |
| OS-03 | Non-English chat input deferred | IMPLEMENTED | [Original boundary](spec.md#L414) remains scoped to English; later localized helper artifacts are not required to prove this feature's English acceptance. |
| OS-04 | External role-play without Entra accounts remains outside this feature | IMPLEMENTED | [Boundary](spec.md#L415) is authored; anonymous write permission is not an acceptable implementation of that exclusion. AUD-024-002. |
| OS-05 | Realistic crowdsourced social injects deferred; synthetic only | IMPLEMENTED | [Boundary](spec.md#L417) is authored; no requirement to invent real social activity. Public outbound safety still applies. |
| OS-06 | Non-Azure model providers excluded | IMPLEMENTED | [Foundry client](../../apps/api/app/services/simulation/controller_service.py#L540) remains Azure-native under explicit migration. |

Only the limited replacement clauses above are marked SUPERSEDED. The
[Foundry relationship table](../036-foundry-rag-grounding/spec.md#L21) explicitly preserves 024 tenant
isolation, approval and comms-block. The later
[lifecycle clarification](../036-sim-agent-extend/spec.md#L3103) strengthens pause/abort but does not
retire original terminal reporting/cancellation guarantees. Its reject-all-paused-chat wording conflicts
with 024's note allowance and requires an explicit product resolution (AUD-024-018); it is not silently
selected as authority. No other specification implementation report was read.

## Checklist and Review Evidence

### Safety and Readiness Checklist

All **50** original [readiness items](checklists/simulation-safety.md#L9) remain authored `[ ]`.
The state below is copied, not changed. A static IMPLEMENTED result is never a mark of checklist
completion; outcome/performance/deployment/sign-off items remain UNVERIFIED without their evidence.

| Item | Original checkbox | Status | Static assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | CONFLICT | [Publication equivalent](../../apps/api/app/services/public_alert_service.py#L82) returns a normal sim result, not 410. | AUD-024-003 |
| CHK002 | [ ] | PARTIAL | [Wrapper guard](../../apps/api/app/clients/outbound_http.py#L64) misses GET and missing-context cases; no caller adoption. | AUD-024-003 |
| CHK003 | [ ] | UNVERIFIED | [Channel adapters](../../apps/api/app/services/public_alert_service.py#L29) build dictionaries; no all-transport integration proof. | AUD-024-003, AUD-024-016 |
| CHK004 | [ ] | UNVERIFIED | [Direct wrapper test](../../tests/unit/test_simulation_controller_safety.py#L76) is not 10,000-message fuzz evidence. | AUD-024-016 |
| CHK005 | [ ] | PARTIAL | [Receipt fields](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L32) exist but are not recorded at each publication boundary. | AUD-024-003, AUD-024-008 |
| CHK006 | [ ] | PARTIAL | [Warning tool](../../apps/api/app/services/simulation/controller_service.py#L955) prefixes text; all-renderer/PDF/email coverage absent. | AUD-024-012 |
| CHK007 | [ ] | MISSING | [Chat rendering](../../apps/web/src/components/simulation-chat-pane.tsx#L330) has no warning Approve or would-have-published record. | AUD-024-012 |
| CHK008 | [ ] | PARTIAL | [Prompt hash](../../apps/api/app/services/simulation/controller_service.py#L125) exists; all-record and manifest binding incomplete. | AUD-024-007 |
| CHK009 | [ ] | IMPLEMENTED | [Server name check](../../apps/api/app/services/simulation/controller_service.py#L761) independently enforces registry. This does not imply argument/RBAC/confirmation safety. | - |
| CHK010 | [ ] | PARTIAL | [Unknown-tool branch](../../apps/api/app/services/simulation/controller_service.py#L761) refuses but does not persist complete tool_denied evidence. | AUD-024-007 |
| CHK011 | [ ] | CONFLICT | [T093](tasks.md#L88) says 50 PR prompts; no wired >=200 PR/nightly Controller suite. | AUD-024-016, AUD-024-018 |
| CHK012 | [ ] | UNVERIFIED | [Four refusal cases](../../tests/unit/test_simulation_controller_safety.py#L46) cannot establish >=99% curated-suite performance. | AUD-024-016 |
| CHK013 | [ ] | PARTIAL | [Input regexes](../../apps/api/app/services/simulation/controller_service.py#L62) and prompt cover examples, not all unsafe requests/model outputs. | AUD-024-006, AUD-024-007 |
| CHK014 | [ ] | CONFLICT | [Raw persistence/replay](../../apps/api/app/services/simulation/controller_service.py#L346) bypasses PII minimization. | AUD-024-006 |
| CHK015 | [ ] | PARTIAL | [Local buckets](../../apps/api/app/services/simulation/rate_limiter.py#L16) lack distributed/owner-tenant semantics and retry-after. | AUD-024-009 |
| CHK016 | [ ] | CONFLICT | [State graph](../../packages/domain/src/domain/models/simulation_tenant.py#L15) is Provisioning/Active/Paused/Archiving/Archived/Deleted. | AUD-024-004 |
| CHK017 | [ ] | CONFLICT | [SimulationUser guard](../../apps/api/app/core/auth.py#L13) is not Coordinator enforcement. | AUD-024-002 |
| CHK018 | [ ] | MISSING | [Tenant model](../../packages/domain/src/domain/models/simulation_tenant.py#L37) has no primary-owner/handover contract; no race test. | AUD-024-002 |
| CHK019 | [ ] | MISSING | [UI Stop](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L262) does not cancel registered chat tasks; there are no registration callers. | AUD-024-004 |
| CHK020 | [ ] | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L75) has flags, no timed declaration/banner proof. | AUD-024-005, AUD-024-016 |
| CHK021 | [ ] | MISSING | [Static allow-list check](../../apps/api/app/services/simulation/controller_service.py#L761) does not narrow during NEMA throttle. | AUD-024-005 |
| CHK022 | [ ] | MISSING | [Expiry service](../../apps/api/app/services/simulation_service.py#L231) archives, not 24h idle pause/notification. | AUD-024-004 |
| CHK023 | [ ] | PARTIAL | [Six adapters](../../apps/api/app/services/simulation/sub_agent_invoker.py#L148) exist but [dispatcher](../../apps/agents/dispatcher/agent.py#L209) does not query operational state. | AUD-024-010 |
| CHK024 | [ ] | PARTIAL | [Recorder](../../apps/api/app/services/simulation_event_recorder.py#L137) drops request/response/correlation metadata. | AUD-024-007 |
| CHK025 | [ ] | PARTIAL | [Dispatcher replies](../../apps/agents/dispatcher/agent.py#L269) have no citations for aggregation. | AUD-024-010 |
| CHK026 | [ ] | PARTIAL | [Unknown-agent branch](../../apps/api/app/services/simulation/sub_agent_invoker.py#L98) refuses invocation but needs sanitized/audited end-to-end assertions. | AUD-024-007, AUD-024-010 |
| CHK027 | [ ] | PARTIAL | [Timeout](../../apps/api/app/services/simulation/sub_agent_invoker.py#L111) is degraded; route progress/cache/typed propagation incomplete. | AUD-024-010, AUD-024-014 |
| CHK028 | [ ] | PARTIAL | [Turn store](../../apps/api/app/services/simulation/controller_service.py#L223) plus event previews cannot reconstruct all actions. | AUD-024-007, AUD-024-008 |
| CHK029 | [ ] | PARTIAL | [Monitor setup](../../apps/api/app/main.py#L12) exists, not every-operation custom dimensions. | AUD-024-017 |
| CHK030 | [ ] | MISSING | [Container](../../infra/main.bicep#L680) lacks TTL; no purge assertion for original three logical stores. | AUD-024-008 |
| CHK031 | [ ] | UNVERIFIED | [AU storage rule](../../.specify/memory/constitution.md#L245) is normative; actual deployed regions and data persistence were not queried. | AUD-024-006, AUD-024-017 |
| CHK032 | [ ] | CONFLICT | [History endpoint](../../apps/api/app/api/routes/simulation_chat.py#L101) uses the same role as writes and omits membership/Observer semantics. | AUD-024-002 |
| CHK033 | [ ] | PARTIAL | [Detail markers](../../apps/web/src/components/simulation-map.tsx#L146) show SIM titles, not required main-map lifecycle styles. | AUD-024-013 |
| CHK034 | [ ] | MISSING | [Main map composition](../../apps/web/src/app/page.tsx#L243) has no lifecycle legend/contrast proof. | AUD-024-013, AUD-024-015 |
| CHK035 | [ ] | MISSING | [Sidebar](../../apps/web/src/app/page.tsx#L263) links incidents only. | AUD-024-013 |
| CHK036 | [ ] | MISSING | [Map state](../../apps/web/src/app/page.tsx#L76) has no ended-age filter/toggle. | AUD-024-013 |
| CHK037 | [ ] | PARTIAL | [Live map](../../apps/web/src/app/page.tsx#L243) remains separate, but sim/live coexistence and non-displacement are not proven with the required layer absent. | AUD-024-013, AUD-024-016 |
| CHK038 | [ ] | UNVERIFIED | [Uncollected axe test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L19) is not a full automated/manual audit. | AUD-024-015, AUD-024-016 |
| CHK039 | [ ] | PARTIAL | [Textarea label/key handler](../../apps/web/src/components/simulation-chat-pane.tsx#L303) and [focus CSS](../../apps/web/src/app/globals.css#L2777) exist; complete keyboard/assistive workflow unverified. | AUD-024-015 |
| CHK040 | [ ] | PARTIAL | [Detail map label](../../apps/web/src/components/simulation-map.tsx#L290) exists; persistent lifecycle SIM badge on main map is missing. | AUD-024-013, AUD-024-015 |
| CHK041 | [ ] | MISSING | Required striped lifecycle layer/reduced-motion branch is not implemented in [main map](../../apps/web/src/app/page.tsx#L243); static detail labels are not that behavior. | AUD-024-013, AUD-024-015 |
| CHK042 | [ ] | PARTIAL | [Status pills](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L303) have text; all map badges/states still need implemented/tested parity. | AUD-024-013, AUD-024-015 |
| CHK043 | [ ] | CONFLICT | [Input enablement](../../apps/web/src/components/simulation-chat-pane.tsx#L303) depends only on streaming, not provider outage. | AUD-024-014 |
| CHK044 | [ ] | MISSING | [Built-in lookup](../../apps/api/app/services/simulation/controller_service.py#L1003) has no Maps failure-to-manual-point workflow. | AUD-024-011 |
| CHK045 | [ ] | MISSING | [Sub-agent failure](../../apps/api/app/services/simulation/sub_agents/_base.py#L71) returns empty/error, not cached last-known state. | AUD-024-010 |
| CHK046 | [ ] | PARTIAL | [Foundry env](../../infra/main.bicep#L1037) is declared; original Maps/content-safety/region expectations and deployment docs need reconciliation. | AUD-024-017 |
| CHK047 | [ ] | UNVERIFIED | [Original review](review-report.md#L57) explicitly deferred deployment; no clean-env deployment was performed/verified here. | AUD-024-017, AUD-024-018 |
| CHK048 | [ ] | PARTIAL | [Health route](../../apps/api/app/api/routes/simulation_chat.py#L92) returns prompt hash and constant backend string, not actual availability/tool version. | AUD-024-014, AUD-024-017 |
| CHK049 | [ ] | MISSING | [Alert runbook reference](../../infra/bicep/modules/observability-alerts.bicep#L169) does not resolve to an existing leak runbook in the scoped documentation search. | AUD-024-017 |
| CHK050 | [ ] | PARTIAL | [Report service](../../apps/api/app/services/exercise_report_service.py#L31) is called on GET, not queued by Stop; default blob dependency is absent. | AUD-024-004, AUD-024-007 |

### Requirements Quality Checklist

These **16** unnumbered items were all checked in the original document. Q-01..Q-16 preserve their
order. IMPLEMENTED here can mean a complete authored section, not product readiness or successful review.

| Item | Original checkbox | Original assertion | Status | Assessment and evidence |
| --- | --- | --- | --- | --- |
| Q-01 | [x] | No implementation details except Azure policy choice | CONFLICT | [FR-021/037](spec.md#L319) specify an HTTP wrapper and repository file layout; claiming no implementation detail is too strong. AUD-024-018. |
| Q-02 | [x] | User value/business focus | IMPLEMENTED | [Five stories](spec.md#L78) explain exercise authoring/control/coordination/map/safety outcomes. |
| Q-03 | [x] | Nontechnical stakeholder readability | PARTIAL | Stories are readable, but [requirements](spec.md#L267) include tool identifiers/HTTP/storage detail requiring glossary/context. AUD-024-018. |
| Q-04 | [x] | Mandatory sections complete | IMPLEMENTED | [Specification](spec.md#L8) includes overview/scenarios/requirements/entities/success/scope/dependencies plus amendments. |
| Q-05 | [x] | No NEEDS CLARIFICATION markers | IMPLEMENTED | Complete assigned spec has no unresolved placeholder marker; this does not resolve semantic contradictions. |
| Q-06 | [x] | Testable and unambiguous requirements | CONFLICT | [Rate scope](spec.md#L352), [terminal model](data-model.md#L73), [T093](tasks.md#L88) and note/primary-owner conflicts need explicit decisions. AUD-024-018. |
| Q-07 | [x] | Measurable success criteria | IMPLEMENTED | [Eight SCs](spec.md#L391) state quantitative thresholds. Measurement evidence is separately UNVERIFIED. |
| Q-08 | [x] | Outcome-focused technology-agnostic SCs | IMPLEMENTED | [SC section](spec.md#L391) states time/safety/audit/usability/accessibility outcomes; no test result inferred. |
| Q-09 | [x] | Acceptance scenarios defined | IMPLEMENTED | All 18 scenarios exist and are accounted for above. [First set](spec.md#L100). |
| Q-10 | [x] | Edge cases identified | IMPLEMENTED | All eight [edges](spec.md#L232) are authored and audited individually. |
| Q-11 | [x] | Scope clearly bounded | PARTIAL | [Scope bullets](spec.md#L409) exist; [MVP review deferrals](review-report.md#L48) are inconsistent with unchanged mandatory requirements. AUD-024-018. |
| Q-12 | [x] | Dependencies/assumptions identified | IMPLEMENTED | [Dependencies](spec.md#L421), A1-A6 and ASM-071..073 are explicit; validity is separately assessed. |
| Q-13 | [x] | All FRs have clear acceptance criteria | PARTIAL | Forty FRs are stated, but ownership, pause semantics and some nonfunctional gates need reconciled fixtures/decisions. [FR-035](spec.md#L344); AUD-024-016/018. |
| Q-14 | [x] | Five stories span primary P1/P2 flows | IMPLEMENTED | [Story headings](spec.md#L78) cover the original five flows; runtime coverage is a different question. |
| Q-15 | [x] | Feature meets measured outcomes | UNVERIFIED | No SC measurement evidence accompanies the [checked claim](checklists/requirements.md#L29); current source has concrete gaps. AUD-024-016/018. |
| Q-16 | [x] | No implementation details leak into spec | CONFLICT | Same explicit implementation detail as Q-01; [FR-037](spec.md#L349) names the runtime file/hash design. AUD-024-018. |

### Authored Cohort Review and Analysis

The [historical review](review-report.md#L1) contains **16** cohort findings, seven backlog bullets,
aggregate test/import/typecheck success claims and an explicit deployment deferral. It is evidence of
authored review content, not proof of independent approval, execution or current behavior.

| Original item | Status | Current assessment and follow-up |
| --- | --- | --- |
| O-1 | PARTIAL | Confirmation/start defect remains and prompt now explicitly auto-seeds; AUD-024-001/004. [Current handler](../../apps/api/app/services/simulation/controller_service.py#L990). |
| O-2 | PARTIAL | [Warning tool](../../apps/api/app/services/simulation/controller_service.py#L955) now adds watermark server-side, but downstream prose/export/approval still incomplete; AUD-024-012. |
| O-3 | CONFLICT | Stubs are no longer the entire adapter story: [production registry](../../apps/api/app/services/simulation/sub_agent_invoker.py#L148) is wired, but [dispatcher](../../apps/agents/dispatcher/agent.py#L209) is not operational data integration. Claimed T032 MVP permission is absent; AUD-024-010/018. |
| O-4 | UNVERIFIED | Human language-complexity review was accepted as a rationale, but no human record exists in local feature evidence. Do not invent a new automatic-readability requirement; AUD-024-012/018. |
| S-1 | PARTIAL | [Offline parser](../../apps/api/app/services/simulation/controller_service.py#L1119) extracts a small subset, not complete AFDRS conditions/validated NSW scenario; AUD-024-011. |
| S-2 | PARTIAL | [Hazard enum](../../packages/domain/src/domain/models/sim_scenario_card.py#L25) covers the list, not cyclone/flood parameter/pathway behavior; AUD-024-011. |
| S-3 | MISSING | Throttle banner emission still absent from [controller](../../apps/api/app/services/simulation/controller_service.py#L324); AUD-024-005. |
| S-4 | MISSING | [list_participants tool](../../apps/api/app/services/simulation/controller_service.py#L976) still returns a dashboard note, not participant data; AUD-024-010. |
| T-1 | PARTIAL | [Allow-list](../../apps/api/app/services/simulation/controller_service.py#L761) exists; no required Controller 200-case/nightly evidence; AUD-024-016. |
| T-2 | CONFLICT | [Cosmos chat repo](../../apps/api/app/repositories/sim_chat_history_repository.py#L29) now exists, but three-container/retention claim is incomplete and old review names wrong artifacts; AUD-024-008/018. |
| T-3 | IMPLEMENTED | [StreamingResponse](../../apps/api/app/api/routes/simulation_chat.py#L84) is the explicit authored library substitution; absence of sse-starlette alone is not a delivery defect. SSE semantics remain AUD-024-014. |
| T-4 | CONFLICT | [Limiter](../../apps/api/app/services/simulation/rate_limiter.py#L16) remains process-local; a single Azure region does not imply one process/replica. Redis deferral does not waive T020; AUD-024-009/018. |
| T-5 | PARTIAL | A later [minimization gateway](../../apps/agents/common/model_gateway.py#L179) exists, but raw replay/AU bypass leave original PII requirement unmet; AUD-024-006. |
| T-6 | PARTIAL | [Feature logs](../../apps/api/app/services/simulation/synthetic_delivery_service.py#L60) exist; universal dimensions/audit success are not established; AUD-024-007/017. |
| T-7 | PARTIAL | [Safety tests](../../tests/unit/test_simulation_controller_safety.py#L17) exist, no full HTTP SSE/confirmation/cancellation suite; AUD-024-016. |
| T-8 | UNVERIFIED | Import smoke/tsc and the 1623+157+366 aggregate pass claim have no retained per-run evidence in this feature folder; nothing was rerun. AUD-024-016/018. |

Backlog bullets 1-7 map respectively to AUD-024-001/004, AUD-024-012, AUD-024-005,
AUD-024-010, AUD-024-016, AUD-024-006, and AUD-024-014/016. A 20-prompt seed proposed by old
backlog item 5 does not satisfy >=200 prompts. The claimed plan session todos/Deferred section were not
found in the complete assigned plan/spec. The [analysis report](analysis-report.md#L5) maps all FRs to
tasks and adds T087/T088/T093; its A1-A3 gap-fill resolutions are authored work allocation only, A4 leaves
the current state enum unresolved, and A5's equivalent-service permission does not authorize fabricated
agent state. Its two outstanding risks (jailbreak corpus fidelity and Cosmos index/query profiling)
remain open under AUD-024-016 and AUD-024-008. Deployment remains UNVERIFIED, not retrospectively done.

### Planning Constitution Gates

All nine original rows say PASS. This table evaluates the claim, not the constitution itself.

| Gate | Authored state | Status | Current assessment |
| --- | --- | --- | --- |
| PC-01 | PASS | PARTIAL | Human approval is not enforced on scenario/warning flows; [seed handler](../../apps/api/app/services/simulation/controller_service.py#L990), AUD-024-001/012. No real delivery asserted. |
| PC-02 | PASS | UNVERIFIED | AU deployment/residency not inspected; explicit inference-only carve-out and raw replay gap, AUD-024-006/017. [Constitution](../../.specify/memory/constitution.md#L245). |
| PC-03 | PASS | CONFLICT | [Raw turn storage](../../apps/api/app/services/simulation/controller_service.py#L346) and absent [TTL](../../infra/main.bicep#L680) contradict privacy/retention claim, AUD-024-006/008. |
| PC-04 | PASS | PARTIAL | FastAPI/GeoJSON/domain AWS models exist, but actual unchecked card/warning/contracts diverge, AUD-024-011/012/014. [Card model](../../packages/domain/src/domain/models/sim_scenario_card.py#L21). |
| PC-05 | PASS | CONFLICT | [Chat input](../../apps/web/src/components/simulation-chat-pane.tsx#L303) is not read-only on outage; no cached agent fallback, AUD-024-010/014. |
| PC-06 | PASS | IMPLEMENTED | [Azure model client](../../apps/api/app/services/simulation/controller_service.py#L540) and declared Azure infrastructure follow Azure-native choice; runtime deployment not implied. |
| PC-07 | PASS | PARTIAL | [Event recorder](../../apps/api/app/services/simulation_event_recorder.py#L137) lacks full provenance; AUD-024-007/008. |
| PC-08 | PASS | PARTIAL | [Warning model](../../packages/domain/src/domain/models/public_alert.py#L52) validates tiers, but chat warning execution does not use it; AUD-024-012. |
| PC-09 | PASS | PARTIAL | [CI](../../.github/workflows/ci.yml#L138) exists, but original safety/journey/a11y paths and measured gates are not complete; AUD-024-016. |

### Applicable Reviewer Checklist

The 29 checklist obligations in the [review reference](../../.github/instructions/references/code-review-checklists.md)
were applied to this feature only. These are reviewer assessments, not new original product tasks.

| Item | Obligation | Status | Evidence and assessment |
| --- | --- | --- | --- |
| RC-01 | Code style/conventions | PARTIAL | Existing layered names/styles retained; [unchecked dict execution](../../apps/api/app/services/simulation/controller_service.py#L990) bypasses local domain pattern. |
| RC-02 | Meaningful names | IMPLEMENTED | [Service/tool/model names](../../apps/api/app/services/simulation/controller_tools.py#L12) expose intent; no style-only remediation added. |
| RC-03 | Focused functions/modules | PARTIAL | [Controller](../../apps/api/app/services/simulation/controller_service.py#L487) combines provider, retrieval, privacy, audit, tools and transport; concrete gaps tracked, not a gratuitous refactor. |
| RC-04 | Avoid duplication | PARTIAL | [Current user persisted](../../apps/api/app/services/simulation/controller_service.py#L346) then [replayed and appended](../../apps/api/app/services/simulation/controller_service.py#L588); independent state stores also drift. |
| RC-05 | Manage complexity | PARTIAL | Central registry helps, but control state/authorization do not reach dispatch. [Tool check](../../apps/api/app/services/simulation/controller_service.py#L761). |
| RC-06 | Error handling | PARTIAL | [Repository fallback](../../apps/api/app/repositories/sim_chat_history_repository.py#L106) hides lost durability; provider/outage semantics incomplete. |
| RC-07 | No untracked dead code/unfinished claims | PARTIAL | [Cancellation registration](../../apps/api/app/services/simulation/cancellation.py#L38) and watermark helpers have no chat callers; readiness claims overstate wiring. |
| RC-08 | No sensitive data in logs/storage | CONFLICT | [Raw PII persistence/replay](../../apps/api/app/services/simulation/controller_service.py#L346) violates intended minimization. No secrets are reproduced in this report. |
| RC-09 | Validate all inputs | PARTIAL | [Tool JSON](../../apps/api/app/services/simulation/controller_service.py#L747) bypasses advertised model validation. |
| RC-10 | Parameterized database queries | IMPLEMENTED | [History query](../../apps/api/app/repositories/sim_chat_history_repository.py#L73) binds tenant via parameters/partition key. Scope is this reviewed query path only. |
| RC-11 | Authentication and authorization | CONFLICT | [Chat route](../../apps/api/app/api/routes/simulation_chat.py#L59) lacks verified role/membership/primary checks. |
| RC-12 | Dependency security/current versions | UNVERIFIED | [API manifest](../../apps/api/pyproject.toml#L10) and [web manifest](../../apps/web/package.json#L21) inspected; no vulnerability scan, install, resolution or external advisory lookup authorized. |
| RC-13 | Appropriate new-code coverage | PARTIAL | [Safety unit suite](../../tests/unit/test_simulation_controller_safety.py#L17) lacks full behavior/CI collection. |
| RC-14 | Focused test names | IMPLEMENTED | [History tests](../../tests/unit/test_sim_chat_history.py#L30) name their actual repository behaviors. Claims of wider safety remain separate. |
| RC-15 | Edge/error coverage | PARTIAL | [Invoker timeout tests](../../apps/api/tests/test_sub_agent_invoker.py#L37) exist, not full route/gateway/control races. |
| RC-16 | Test isolation/determinism | PARTIAL | [API fixture](../../apps/api/tests/conftest.py#L38) enables test mode; global singletons/live env still require explicit isolation and transport mocks for safety tests. |
| RC-17 | No vacuous pass conditions | PARTIAL | [A11y test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L37) can lack a receipt; [200-loop](../../tests/integration/test_hallucinated_citation_suppression.py#L115) does not exercise the prompts. |
| RC-18 | Avoid memory/query performance defects | PARTIAL | [History read](../../apps/api/app/repositories/sim_chat_history_repository.py#L116) fetches all turns and buckets do not expire. |
| RC-19 | Appropriate caching | PARTIAL | History window exists; [sub-agent error](../../apps/api/app/services/simulation/sub_agents/_base.py#L71) lacks last-known-state cache. |
| RC-20 | Efficient algorithms/data structures | PARTIAL | Set-based allow-list is appropriate; non-atomic MAX+1/all-history reads need improvement. [Repository](../../apps/api/app/repositories/sim_chat_history_repository.py#L69). |
| RC-21 | Resource cleanup | PARTIAL | [Invoker](../../apps/api/app/services/simulation/sub_agent_invoker.py#L129) cancels soft-ack tasks; shared route HTTP client and model/credential lifecycle have no explicit shutdown in inspected path. |
| RC-22 | Established architecture/patterns | PARTIAL | Routes/services/models reused, but disconnected safety helpers and duplicate state owners violate intended boundary. [Router order](../../apps/api/app/api/router.py#L68). |
| RC-23 | Separation of concerns | PARTIAL | [Generic dispatcher](../../apps/agents/dispatcher/agent.py#L209) substitutes model advice for operational state; controllers should adapt actual services. |
| RC-24 | No architectural violations | PARTIAL | [Direct raw HTTP](../../apps/api/app/services/simulation/sub_agents/_base.py#L59) bypasses specified egress design. |
| RC-25 | Dependency direction | PARTIAL | [Seed helper](../../apps/api/app/services/simulation/controller_service.py#L1090) imports route singleton back into service; typed dependency injection preferable during related repair. |
| RC-26 | Public API documentation | PARTIAL | [Local contracts](contracts/simulation-chat-api.md#L5) are authored but differ from mounted endpoints/DTOs. |
| RC-27 | Explain complex behavior | PARTIAL | [Review](review-report.md#L48) describes deferrals, but claims obsolete stubs/permissions; operational docs need current semantics. |
| RC-28 | README updated | MISSING | No [root README](../../README.md#L1) Simulations Chat entry. |
| RC-29 | Breaking-change documentation | PARTIAL | [Foundry migration](../036-foundry-rag-grounding/spec.md#L19) is explicit, but [024 quickstart](quickstart.md#L10) remains stale. |

## Bounded Search and Evidence Limits

Negative findings were bounded to the owning code paths and then searched for renamed or relocated
behavior. They are not claims that no similarly named function exists anywhere in the repository.

| Scope | Searched/read surfaces and result |
| --- | --- |
| S-01 Control/auth | Mounted router order; simulation_chat, simulations and simulations_036 routes; tenant/auth/Entra/RBAC middleware; principal, tenant/state, cancellation and lifecycle/report services. Found later abort/role helpers, but no original chat membership/primary claim, confirmed Start, connected Stop cancellation or handover. |
| S-02 Public egress | API client/service/middleware files, simulation adapters, public alert routes/model/service; Python publication/wrapper/receipt identifier searches in API/agents plus file-name search. Located PublicAlertService equivalent; wrapper usage is confined to its definition/tests and is not universal production enforcement. |
| S-03 Scenario/geocoding | Complete controller/prompt/tools/card models, detail-card/map rendering; resolver/seed names across API simulation files and tools/scripts. Located city lookup, not connected Azure Maps/confirmation/synthetic-signal pipeline. |
| S-04 Audit/storage | Chat/history/receipt/recorder and later typed AuditWriter; all infrastructure Bicep matches for original logical store names, sim-chat/sim-events/63072000; migration/tooling searches. Located sim-chat, not complete original retention/paging/provenance mapping. |
| S-05 Map/UI | /disasters redirect, homepage loader/sidebar, incidents/map route, detail page/map/chat components, CSS and shared-map consumers; simulation overlay/ended-toggle search. Located later optional overlay helpers, not the required combined map lifecycle layer. |
| S-06 Safety/CI | Root tests unit/contract/integration/e2e and API/web tests; filenames and assertions for chat/control/egress/jailbreak; all workflow name/content searches; CI, manual simulation workflows, Ruff, pytest/Vitest/Playwright config and branch-protection metadata. Located narrow/alternate tests, not required fuzz/jailbreak/journey gates. |
| S-07 Documentation | Complete 12 local spec documents; literal root README; docs/runbooks inventory and searched operator/configuration docs; infrastructure alerts/env/azd. No requested or referenced leak runbook/current 024 onboarding link located. |
| S-08 Amendments | Explicit relationship/lifecycle/default-speed clauses in linked Foundry/sim-extension/warp specs, constitution, persona schema and named rubric evidence. No other implementation-review-tasks report was read; only replacements explicitly documented are credited. |
| S-09 Hypothesis | Listed all files in the named 028 evidence folder (decision-record, rubric-baseline, rubric-postfeature) and searched the exact HYP-022 filename family. Named HYP-HYP-022.md stub not present; portfolio scores not promoted to a 024 outcome. |

All current-state findings are static. None demonstrate deployed network reachability, actual public
delivery, Azure availability, data-plane region, automatic purge completion, race reproduction, measured
latency, successful CI execution or human approval. No model/provider invocation, package import, test
collection/execution, browser, build or cloud query was used. Ripgrep was unavailable, so provided search
tools and read-only PowerShell were used. The Python fact-grounded-coding and Cosmos best-practices
skills were read for evidence discipline; runtime-specific claims remain UNVERIFIED. Bicep security/
policy instructions were read for the inspected infrastructure; no policy discovery or deployment ran.

## Future Validation Instructions

**All commands below are future-only. None were executed during this audit.** They are remediation
instructions, not a request to run tests now. Run them only in a separately authorized development/test
session after the necessary source changes. Never send test messages to real public destinations.

Common prerequisites: supported Python 3.12+, existing project dependencies and editable API/agent
packages, Node/pnpm/browser dependencies already installed by an authorized maintainer, cleanly scoped
test configuration, synthetic tenant/persona data, fake clocks and explicit mock transports. Clear or
override production Azure/Foundry/Cosmos endpoints and credentials in the test environment; importing
the current route creates clients, and the old direct egress test must first acquire an assert-on-call
transport. Do not rely solely on AMA_TEST_MODE to prevent network I/O. The root and API-local
[pytest bootstraps](../../tests/conftest.py#L10) / [API bootstrap](../../apps/api/tests/conftest.py#L28)
must both be honored. No installation command is part of this audit.

### C01 Domain and Local Safety

Applies to AUD-024-001..009 and AUD-024-011. Extend the existing files first with the exact fixtures and
assertions specified in each task. Expected: explicit pass/fail on roles, confirmation, model arguments,
state/idle rules, quota keys, audit hashes/TTL and transport blocks; no live calls, hidden skips or fallback
successes. A fake-clock result proves logic, not measured production latency.

```powershell
pytest tests/unit/test_simulation_controller_safety.py tests/unit/test_sim_chat_history.py tests/unit/test_simulation_service.py tests/unit/test_resource_governor.py -q
```

### C02 Actual Adapter and Audit Wiring

Applies to AUD-024-002/004/007/010/012. Test production-interface registration with mocked HTTP/model/
Cosmos seams, not merely available role names. Expected: six substantive tenant-specific results,
preserved citations/provenance, progress before timeout, proper cancellation and durable warning receipt.

```powershell
pytest apps/api/tests/test_simulation_chat_controller_wiring.py apps/api/tests/test_sub_agent_invoker.py apps/api/tests/test_audit_writer.py apps/api/tests/test_watermark_guards.py -q
```

### C03 Mounted Contracts and Integration

Applies to AUD-024-001/002/003/004/005/007/008/009/010/011/014. **Proposed test files**:
tests/contract/test_simulation_chat_sse.py and tests/integration/test_simulation_control_chat.py.
Prefer extending suitable existing tests before adding them, but do not claim these proposed paths exist.
Prerequisites: mount the actual application with fake provider/store transports and authenticate synthetic
Coordinator/Observer/non-member principals; do not test only directly called route functions.
Expected: exact 18 acceptance scenarios and eight edge cases, coherent SSE/HTTP errors, full correlation,
start/stop/handover policy, NEMA restrictions and no live writes. Run collection first and fail if absent.

```powershell
pytest tests/contract/test_simulation_chat_sse.py tests/integration/test_simulation_control_chat.py --collect-only -q
pytest tests/contract/test_simulation_chat_sse.py tests/integration/test_simulation_control_chat.py -q
```

### C04 Public Egress Fuzz

Applies to AUD-024-003/008/016. **Proposed original-task path**: tests/security/egress_block/test_fuzz.py.
Prerequisites: register the fuzz marker, inject fail-on-real-network transports at both gates and actual
publication adapters, seed six channels, all body forms/context failures and separate live control cases.
Expected: exactly 10,000 sim attempts, zero public transport invocations, one complete durable receipt
per attempt with independently computed hash/channel/audience/reason; legitimate internal calls preserved.

```powershell
pytest tests/security/egress_block -q -m fuzz
```

### C05 Controller Adversarial Suite

Applies to AUD-024-006/016/018. **Proposed original-task path**: tests/security/jailbreak/test_suite.py
with a curated >=200-prompt corpus and positive in-scope controls. Prerequisites: deterministic server
enforcement tests with malformed/malicious model fixtures first; a separately approved Azure-hosted
evaluation environment is needed for an actual model refusal-rate claim. The corpus must cover role
changes, exfiltration, indirect injection, unsafe real-world action, allowed-tool argument attacks and PII.
Expected: >=99% safe/refusal with zero executed prohibited actions, all prompts actually exercised,
with PR + nightly-main workflows and enforced required checks. Neither citation-filter repetitions nor
regex-only mock pass results establish the hosted-model metric.

```powershell
pytest tests/security/jailbreak -q
```

### C06 Frontend Components

Applies to AUD-024-001/002/005/011/012/013/014/015. Prerequisites: current
[Vitest configuration](../../apps/web/vitest.config.ts#L19), shared UI resolution, mocked typed SSE/
history and role/state/outage fixtures. Expected: full scenario card/confirmation, disabled unauthorized
actions, unclosable NEMA banner, safe warning approval/export, accessible streaming, real outage state
and all lifecycle/24-hour map boundaries. Structural component tests do not certify map pixels or WCAG.

```powershell
pnpm --filter @ama/web exec vitest run tests/unit/spec_036/simulation-chat-pane.test.tsx tests/unit/spec_036/simulation-map.test.tsx tests/a11y/simulation-map-non-point.test.tsx
```

### C07 Browser and Accessibility Journey

Applies to AUD-024-001/002/004/005/010/012/013/014/015/016. **Proposed collected path**:
tests/e2e/simulation-control-chat.spec.ts. Move/register the existing watermark test under the configured
test directory rather than leaving it uncollected. Prerequisites: separately authorized local servers
and browsers; [Playwright configuration](../../apps/web/playwright.config.cts#L18) starts API/web servers
and may reuse occupied ports, so verify isolation first. Expected: coordinator create/propose/confirm/
start/query/pause/resume/stop journey; Observer read-only and handover; one live plus active/paused/ended
sim on the actual homepage; keyboard/contrast/reduced-motion/axe at 360px, tablet and desktop; provider
outage without losing controls. The test must fail if no chat, card, warning or overlay is rendered.

```powershell
pnpm --filter @ama/web exec playwright test simulation-control-chat.spec.ts --project=chromium
pnpm --filter @ama/web exec playwright test simulation-control-chat.spec.ts --project=mobile
```

### C08 Observability and Operations

Applies to AUD-024-005/008/016/017. Prerequisites: fake telemetry exporter, schema-valid event fixtures,
reachable root infrastructure-module graph and agreed capacity/retention policy. Expected: every required
dimension emitted, alert queries match events, all original alert/workbook responsibilities covered,
10-simulation/50-observer policy explicitly resolved, current docs/health/runbook consistent.

```powershell
pytest tests/devops/test_observability_alerts_bicep.py tests/unit/test_resource_governor.py -q
Select-String -LiteralPath README.md -Pattern 'Simulations Chat','024-simulation-control-chat'
```

Infrastructure compilation, what-if, deployment, live alert firing, residency/TTL measurements and
human operational approvals require separate explicit authorization. Follow the current Azure deployment
procedure only then; this audit's original CHK047 and historical deferred deployment remain UNVERIFIED.

### C09 Measured Outcomes and Review Closure

Applies to AUD-024-016/017/018 and all quantitative SCs. No existing 024 measurement command was located;
do not invent one as an existing gate. A **proposed** tests/performance/test_simulation_control_slos.py
can host a measured, approved environment harness once the functional path exists. It must retain raw
durations, count/sample policy, deployment/revision/region, load (including supported concurrency),
and compute card P95 <=8s, query P95 <=10s, control P95 <=0.5s, egress P99 <=5ms, 90s onboarding,
five-second pause/resume/NEMA windows and the 1% monthly error budget with the correct observation period.

```powershell
pytest tests/performance/test_simulation_control_slos.py -q
```

Prerequisites: separate authorization for any runtime/cloud/load exercise, no real public transport,
defined measurement windows and equivalent baselines. Expected: actual percentile/counter evidence,
not sleeps or fabricated timings. Human >=95% sim/live recognition, manual WCAG review, actual
required-check enforcement, residency attestation and HYP-022/persona approvals require named/date-stamped
records; no shell command alone proves them. Proposed fixtures/stubs must remain labeled as such.

## Completion and Audit Validation

Close a remediation item only when its developer behavior, positive/negative/edge fixtures, compatibility
decision, collected tests, measured evidence where required, and completion criteria are all satisfied.
Preserve original task/checklist states until an authorized implementation review explicitly changes them.
Dependency order: resolve safety/identity/confirmation and lifecycle first; connect audit/storage and
quota/agent/state paths; then complete map/warning/degradation/a11y and run the required gates. Review
decisions must not be used as undocumented waivers of safety requirements.

Report-only validation consists of exact original ID/state comparisons, all FR/SC/scenario/edge rows,
every readiness/quality/review/plan/amendment row, 18 unique unchecked AUD IDs, local Markdown link
targets/line bounds, Markdown table/fence integrity, and editor diagnostics on this file. These checks
validate the report, not the implementation. No product execution is part of that validation.

**Validation receipt (2026-09-14):** Exact coverage/state comparisons passed for 49 tasks (32 PARTIAL,
13 MISSING, 4 CONFLICT; all original checkbox markers absent), 40 FRs, 8 SCs, 18 acceptance scenarios,
8 edge cases, 5 independent tests, 50 readiness items, 16 quality items, 16 authored review findings,
9 plan gates and 29 reviewer-checklist obligations. All clarification, cohort, technical, nonfunctional,
entity, scope, assumption, persona and hypothesis rows passed uniqueness/accounting checks. The
18 remediation IDs are unique and unchecked. All 537 local Markdown links and line bounds, and all
table column counts/code fences, passed. Editor validation identified a trailing-newline-only issue;
the final report edit corrects it and is followed by repeat text-integrity and editor checks.

No blocker prevented this static audit. Product tests, measured outcomes, deployments and human approvals
remain deliberately unexecuted/unverified under the review contract.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 024 only. Three parallel technical reviews examined simulation
authorization, public egress enforcement, and PII/persistence/lifecycle behavior. The source-completable egress defect
was corrected: `SimAwareHttpClient.get` now invokes the same fail-closed guard used by POST, PUT, PATCH, and DELETE,
so the wrapper no longer provides an unguarded GET transport path.

Validation: `python -m pytest tests/contract/test_egress_block.py -q` returned `3 passed, 3 skipped` (staging-only
canaries remain unexecuted).

Remaining open work includes trusted coordinator/membership authorization, publication-state ordering, PII-redacted
history, durable transcript isolation, stop/cancel races, shared rate limits, map lifecycle integration, CI fuzz gates,
deployment, performance, and human safety evidence.

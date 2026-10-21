# Spec 033 Implementation Review Tasks

## Review Metadata

- Review date: 2026-09-14.
- Scope: only spec 033, Microsoft Agent Framework adoption, and source evidence needed to assess it.
- Expected and read-only verified HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Method: fresh, isolated static review. No other implementation-review reports read; no nested agents.
- Write boundary: this report only. Existing untracked audit artifacts remain untouched.
- Limits: no SDK or application imports, product tests, verifiers, builds, runtime, cloud calls,
  installations, deployments, approvals, branch changes, or commits. Developer and tester work is future-only.
- Contract: [Review Contract](../001-spec-implementation-audit/README.md#L11) and
  [code-review rules](../../.github/instructions/code-review.instructions.md#L1).

**Assessment:** The feature is not demonstrated as adopted end to end. Real SDK `Agent` construction,
typed models, middleware, repositories, definitions, API/UI scaffolding, ADRs and test assertions exist.
They do not establish production workflow composition, recoverability, approval integration, equivalent
agent behavior, immutable audit coverage or the claimed cutover outcomes.

**Coverage inventory:** 88 original tasks (all `[X]`), 33 FR identifiers, zero separately numbered NFRs,
10 SC identifiers, 17 acceptance scenarios, eight edge cases and 16 original checklist checkboxes.
Performance/nonfunctional obligations are included under their FR/SC and unnumbered design constraints.
No local amendment, persona appendix, hypothesis appendix, implementation evidence bundle or prior
review report exists beyond the original 14-file inventory. Task actor assignments are assessed as
required contributions, not signatures or evidence that an actor performed a review.

Applicable guidance loaded: the full review contract, code-review instructions and their detailed
checklist, Python fact-grounded coding skill, Cosmos DB best-practices skill, and both Bicep instructions.
Only their static-review portions were used. No runtime-dependent conclusion was manufactured to
replace the prohibited execution or external approval work.

## Original Inputs Read In Full

The original local inventory contains 14 files; there was no pre-existing report to preserve.

| Input | Purpose |
| --- | --- |
| [spec.md](spec.md#L1) | Clarifications, stories, requirements, success criteria, edge cases, scope and dependencies |
| [tasks.md](tasks.md#L1) | Every original task, suffix ID, success clause, phase gate and review obligation |
| [plan.md](plan.md#L1) | Composition, performance, constraints and constitutional gate claims |
| [research.md](research.md#L1) | R1-R10 decisions and four implementation refinements |
| [data-model.md](data-model.md#L1) | Seven entities, transitions, relationships and validation rules |
| [quickstart.md](quickstart.md#L1) | Nine procedures, expected results and diagnostic queries |
| [requirements checklist](checklists/requirements.md#L1) | Sixteen checked quality/readiness claims and validation notes |
| [agent-definition contract](contracts/agent-definition.schema.yaml#L1) | Configuration, output types, middleware and tool pins |
| [workflow-run contract](contracts/workflow-run.schema.json#L1) | Run fields, seven states and conditional invariants |
| [checkpoint contract](contracts/checkpoint.schema.json#L1) | Per-run sequence, opaque state and pending requests |
| [audit contract](contracts/audit-entry.schema.json#L1) | Fingerprints, identities, outcomes and tool records |
| [tool-registration contract](contracts/tool-registration.schema.json#L1) | Versioned bindings and registration provenance |
| [operator API contract](contracts/workflow-runs.api.md#L1) | Six endpoints, authorization, tenancy, caching and error envelopes |
| [HITL envelope](contracts/hitl-request.envelope.md#L1) | Existing approval integration, crash safety and non-bypassability |

## Explicit Replacements

The ADRs are relocated, not absent. [ADR-033-02](../../docs/corpus/aidr/decisions/adr-033-02-cosmos-checkpoint-storage.md#L24)
replaces the custom checkpoint subclass with SDK storage. [ADR-033-03](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L28)
replaces the literal RequestPort approach with a custom gate/listener. These are implementation-choice
replacements, not evidence that checkpointing, recovery, approved publication or retention is complete.
The remaining ADRs and relocated runbooks are assessed below. No blanket supersession is inferred from
newer source comments, matching wrappers or unchecked/checked task states.

[Foundry ADR 20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L27)
explicitly replaces the Azure OpenAI-to-Foundry **chat-plane** migration/canary decision. It explains
the current endpoint factory and grounding flags; it does not retire spec 033's MAF runtime adoption,
workflow durability, independent `FEATURE_MAF_RUNTIME_*` controls or behavior-preserving fallback.
The source-backed use of `Agent` instead of the older `ChatAgent` name is recorded in
[ADR-033-01](../../docs/corpus/aidr/decisions/adr-033-01-azure-openai-chat-client.md#L9).
The separately numbered [Phi shadow ADR](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L1)
belongs to spec 032 and is Proposed; it is not a replacement or completion record for this feature.

[CODEOWNERS](../../.github/CODEOWNERS#L27) explicitly records retirement of the spec-029 progressive-delivery
footprint by spec 031. Therefore references to that historical mechanism require reconciliation with
the current deployment path, not automatic recreation of unrelated retired machinery. That retirement
does not waive spec 033's independent runtime flags, retention controls or cutover evidence requirements.

## Prioritized Findings

| Priority | Finding and decisive evidence | Follow-up |
| --- | --- | --- |
| CRITICAL | Workflow reads/cancel lack the required authorization and tenant boundary: [route](../../apps/api/app/api/routes/workflow_runs.py#L77), [cancel](../../apps/api/app/api/routes/workflow_runs.py#L170), [Entra prefixes](../../apps/api/app/middleware/entra_auth.py#L37), [RBAC prefixes](../../apps/api/app/middleware/rbac_check.py#L32). Packaging failure or an unknown perimeter is not an authorization control. | AUD-033-002 |
| CRITICAL | Checkpoint construction/storage failures are suppressed; no restore path consumes saved state: [builder](../../apps/agents/maf_runtime/workflow/builder.py#L186). | AUD-033-001 |
| CRITICAL | The approval bridge accepts unproven decision dictionaries, does not connect to the existing approval workflow, and has no durable decision-consumption/publication path: [listener](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L245), [real approval payload](../../apps/agents/communication/approval.py#L43). No actual unapproved production publish was observed or asserted. | AUD-033-005 |
| CRITICAL | Safety rejection precedes the audit/telemetry layers; successful audit persistence is optional and invocation metadata is missing: [chain](../../apps/agents/maf_runtime/agents/_factory.py#L81), [short-circuit](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L63), [writer](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L119). | AUD-033-008 |
| CRITICAL | Run uniqueness is a read followed by an unrelated create, and status updates have no ETag/CAS or append-only history: [create](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L110), [replace](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L292). | AUD-033-006 |
| CRITICAL | Four legacy facades manufacture records/plans instead of invoking the legacy processing pipeline; warning invariance is reduced to keywords: [risk facade](../../apps/agents/maf_runtime/agents/risk_assessment_agent.py#L25), [communication facade](../../apps/agents/maf_runtime/agents/communication_agent.py#L31), [prompt assertion](../../tests/unit/test_communication_prompt_invariant.py#L47). | AUD-033-004 |
| CRITICAL | Audit persistence targets the wrong configuration/database and lacks a proven append-only role/policy chain: [audit endpoint](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L94), [active database](../../infra/main.bicep#L603), [agent role assignment](../../infra/main.bicep#L904), [policy](../../infra/policy/rego/deny_audit_delete.rego#L6). | AUD-033-009 |
| IMPORTANT | Real SDK agents exist, but the workflow/executors are manual, the deployed host ignores MAF flags, both images omit the package, and executor shadow mode never calls MAF: [executor](../../apps/agents/maf_runtime/workflow/executors/_base.py#L149), [dispatch](../../apps/agents/maf_runtime/workflow/executors/_base.py#L214), [image](../../apps/agents/Dockerfile#L4), [host](../../apps/agents/dispatcher/agent.py#L189), [API image](../../apps/api/Dockerfile#L22). | AUD-033-003 |
| IMPORTANT | Retry elapsed time is checked only after a call fails; raw client/parser errors escape and schema mismatch is classified as generic Failed: [budget](../../apps/agents/maf_runtime/workflow/executors/_base.py#L88), [parse](../../apps/agents/maf_runtime/agents/_factory.py#L281), [workflow catch](../../apps/agents/maf_runtime/workflow/builder.py#L172). | AUD-033-007 |
| IMPORTANT | Observability bootstrap has no runtime caller, correlation is disconnected, reconciliation compares env constants, and approval/state metrics have no working producer-to-query chain: [bootstrap](../../apps/agents/maf_runtime/observability.py#L27), [reconciliation](../../apps/api/app/api/routes/admin/reconciliation.py#L76). | AUD-033-010 |
| IMPORTANT | Operator history/metrics endpoints return placeholders; the page ignores state selection, lacks refresh, and cannot form the correct trace link: [history](../../apps/api/app/api/routes/workflow_runs.py#L147), [page](../../apps/web/src/app/operations/workflows/page.tsx#L27), [trace identifier](../../apps/web/src/components/workflow/WorkflowRunDetail.tsx#L29). | AUD-033-011 |
| IMPORTANT | MCP version validation can substitute a fabricated v1; the factory binds no tools, legacy routing swallows failures, and the server uses mock geometry rather than the existing route engine: [version fallback](../../apps/agents/maf_runtime/mcp/routing_tool.py#L151), [facade](../../apps/agents/maf_runtime/agents/evacuation_agent.py#L32), [server](../../tools/routing_mcp_server/server.py#L20). | AUD-033-012 |
| IMPORTANT | Equivalence never invokes either implementation, passes empty corpora, ignores real decision-field differences, and does not validate equal schema shapes: [runner](../../apps/agents/maf_runtime/equivalence/runner.py#L31), [scorer](../../apps/agents/maf_runtime/equivalence/scorers.py#L125), [zero-case assertion](../../tests/unit/test_equivalence_scorers.py#L88). | AUD-033-013 |
| IMPORTANT | Dashboard baseline is empty; compatibility snapshots inspect model declarations/schema text rather than actual legacy and MAF outputs: [snapshot](../../tests/contract/snapshots/existing_dashboard_fields.json#L6), [test](../../tests/contract/test_audit_telemetry_fields_no_regression.py#L28). | AUD-033-014 |
| IMPORTANT | Capacity uses five-at-a-time calls, not the required windows; the baseline and capture script contain fixed values, not measurements: [load branch](../../tests/load/test_workflow_capacity.py#L59), [placeholder](../../tests/load/baselines/legacy_baseline.json#L4), [capture script](../../scripts/capture_legacy_baseline.sh#L15). | AUD-033-015 |
| IMPORTANT | The watchdog measures time since last step, not continuous run age, scans a bounded prefix, and has no scheduled runtime caller: [watchdog](../../apps/agents/maf_runtime/workflow/duration_watchdog.py#L40), [scan](../../apps/agents/maf_runtime/workflow/duration_watchdog.py#L55). | AUD-033-016 |
| IMPORTANT | Checked completion is unsupported by required execution/review artifacts; quickstart flags/files drift; main CI does not run the MAF unit guards; report JSON ignore rule is absent: [quickstart](quickstart.md#L1), [CI](../../.github/workflows/ci.yml#L131), [ignore rules](../../.gitignore#L1), [polish claims](tasks.md#L522). | AUD-033-017 |

### Checkpoint Compatibility Detail

The [builder](../../apps/agents/maf_runtime/workflow/builder.py#L186) suppresses every checkpoint failure;
[initialization](../../apps/agents/maf_runtime/workflow/builder.py#L49) can substitute volatile storage.
It creates fresh runs and drives steps directly, with no restore path, pending-request checkpoint,
sequence management or last-checkpoint update. The [storage wrapper](../../apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py#L38)
calls `save_checkpoint`/`load_checkpoint`. Local installed SDK source, inspected without imports,
instead provides [save/load with workflow_name documents](../../.venv/Lib/site-packages/agent_framework_azure_cosmos/_checkpoint_storage.py#L203).
Its [checkpoint constructor](../../.venv/Lib/site-packages/agent_framework/_workflows/_checkpoint.py#L31)
requires `workflow_name` and `graph_signature_hash`, not the builder's `workflow_id` and
`executor_states` constructor arguments. This compatibility finding is bounded to locally installed
core 1.2.2 / Cosmos 1.0.0b260429, confirmed by their local distribution metadata. The committed
[lock](../../apps/agents/uv.lock#L42) instead resolves core/OpenAI 1.3.0, Cosmos 1.0.0b260507 and MCP 1.27.1;
the [image install](../../apps/agents/Dockerfile#L13) and CI use dependency ranges rather than that lock.
Compatibility of a differently resolved/deployed SDK is UNVERIFIED. [Retention](../../apps/agents/maf_runtime/checkpoint/retention.py#L41) has no caller in agent/API
source and defaults to a different database from the checkpoint factory. The
[crash test](../../tests/integration/test_workflow_crash_recovery.py#L32) tests a happy path and an injected
exception, not a killed process, restore or 100 trials. Follow-up: AUD-033-001.

## Open Remediation

All commands in this section are **future instructions**, not an audit execution log. Before running
them, a later developer/tester must prepare an isolated test environment, install the agreed locked
dependencies through the normal project process, and use non-production fixtures. Model calls, real
fault/load exercises, deployments and human reviews require their own later authorization; none is
requested or performed here. Existing test files are linked; any new test function belongs in the
named existing home unless a path is explicitly marked **proposed**.

- [ ] AUD-033-001 Enforce durable checkpoint writes and recover the complete workflow state

  **Affected:** FR-006, FR-007, FR-012a, SC-002; T004, T008, T018, T019, T043, T048, T049;
  US2-1 and the checkpoint-store/mid-approval restart edge cases.

  **Expected / observed / impact:** Persist complete state before advancing; resume without rerunning
  completed work. Instead, [checkpoint errors are suppressed](../../apps/agents/maf_runtime/workflow/builder.py#L186),
  the available SDK interface is mismatched, and no restart path consumes durable state. An incident
  can progress without recoverable context. The accepted SDK-storage replacement does not waive the
  original per-run partition, sequence, pending-request or post-terminal retention obligations.

  **Developer, future only:** Own the [builder](../../apps/agents/maf_runtime/workflow/builder.py#L61),
  [storage adapter](../../apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py#L28),
  [retention helper](../../apps/agents/maf_runtime/checkpoint/retention.py#L41) and repository terminal
  transitions. With the real-workflow composition repair, pin and adapt the supported SDK interface;
  reconcile its workflow-name document model with the spec's per-run schema explicitly. Persist graph
  state, messages, executor outputs, pending approval identity and original deadline; atomically expose
  a valid last-checkpoint reference. Do not silently substitute in-memory storage for production faults.
  Raise the canonical correlated storage error and alert before any later step. Connect restart/resume
  and terminal stamping to the actual runtime; preserve checkpoints throughout active/operator-held
  runs and for at least 30 days after terminality. Keep the existing regulated store and authentication.

  **Tester, future only:** Extend [crash-recovery tests](../../tests/integration/test_workflow_crash_recovery.py#L1)
  and [repository tests](../../tests/unit/test_workflow_run_uniqueness.py#L1), with new test functions in
  those existing homes. Use a persistent fake/approved emulator adapter, two runtime instances, and
  step counters. Assert successful state round-trip, monotonic per-run sequences, no re-execution after
  risk or either parallel branch, retained paused deadline, and correct terminal TTL. Inject constructor,
  read, write, partial-branch and retention failures; assert no subsequent side effect, typed context,
  visible alert, and no volatile fallback. A valid empty corpus or a swallowed exception cannot count as
  a recovery trial.

  **Future validation:** After the compatible SDK and isolated persistent test fixture are prepared,
  run `python -m pytest tests/integration/test_workflow_crash_recovery.py tests/unit/test_workflow_run_uniqueness.py -q`.
  Expected: assertions cover actual restore and failure barriers. Separately perform the required 100
  real fault-injection trials in the future approved validation environment; record at least 99 successful
  resumes and zero repeated completed steps. No such execution occurred in this audit.

  **Done:** A persisted checkpoint is a prerequisite to progression; restart and HITL restore use it;
  storage/schema/retention contracts agree; both focused assertions and the required recovery evidence
  are retained against the reviewed implementation revision.

- [ ] AUD-033-002 Enforce operator authorization and tenant isolation on every workflow endpoint

  **Affected:** FR-011, FR-014, FR-024, FR-025; T025, T051, T052; operator API authorization,
  tenancy, no-store and mutation-audit clauses; US2-5 and US3-1.

  **Expected / observed / impact:** Only authorized operators read their tenant's runs; only commanders
  cancel with an audited reason. [Routes](../../apps/api/app/api/routes/workflow_runs.py#L77) never consult
  the caller, the tenant query argument is unused, and [cancel](../../apps/api/app/api/routes/workflow_runs.py#L170)
  has no role check. Global Entra/RBAC prefix lists exclude this route family. The general
  [auth layer](../../apps/api/app/middleware/auth_middleware.py#L18) supplies anonymous/default claims, not
  enforcement. Read/get/cancel can cross the intended boundary when storage is available. No claim is
  made about an uninspected cloud perimeter.

  **Developer, future only:** Own this router, its repository queries and the existing auth/tenant
  adapters. Resolve identity from the established verified principal, enforce EmergencyOperator reads
  and EmergencyCommander mutation semantics, and scope every lookup/page/history/metric query before
  fetching data. Reject tenant override attempts; use not-found semantics for foreign run IDs. Preserve
  the existing identity model. Set no-store on all responses and persist the cancellation actor, reason,
  timestamp and correlation as `operator.workflow_action`; the current `if False` drops the reason.
  Coordinate with AUD-033-006, AUD-033-009 and AUD-033-011; packaging repair is not a substitute for auth.

  **Tester, future only:** Extend [API contract tests](../../tests/contract/test_workflow_run_api.py#L1)
  using two tenants, same-looking incident IDs, anonymous/operator/commander principals and paginated
  fixtures. Assert unauthenticated rejection, forbidden operator cancel, commander success, foreign-ID
  404, no foreign list/history/metric rows, no-store even on errors, and a single attributed cancel audit.
  Test terminal cancel 409 and storage failure without pretending an empty list means success.

  **Future validation:** With fake verified principals and tenant-scoped stores, run
  `python -m pytest tests/contract/test_workflow_run_api.py -q`. Expected: both positive authorized
  operations and negative cross-tenant/role cases are asserted, not only response-key presence.
  **Done:** Every endpoint is authorization- and tenant-scoped through the real router; mutation audits
  retain the justification; no client-supplied identity or tenant can expand access.

- [ ] AUD-033-003 Connect a real SDK workflow and preserve independent migration modes

  **Affected:** FR-001, FR-002, FR-005, FR-006, FR-022, FR-026; SC-001, SC-010;
  T001, T002, T007, T012, T015, T027, T029, T031, T033, T035, T042, T043, T069, T070, T072.

  **Expected / observed / impact:** Named agents must run through one real framework host and workflow.
  [SDK Agent construction](../../apps/agents/maf_runtime/agents/_factory.py#L90) is real, but
  [executors](../../apps/agents/maf_runtime/workflow/executors/_base.py#L149) do not subclass SDK Executor,
  [the builder](../../apps/agents/maf_runtime/workflow/builder.py#L61) is a direct step runner, and
  [production dispatch](../../apps/agents/dispatcher/agent.py#L212) calls a separate client. Both image
  recipes omit the MAF package. Executor shadow only runs legacy; facade shadow awaits MAF on the
  response path; invalid flags are caught and silently converted to legacy. Flag flips do not establish
  migration of actual caller traffic.

  **Developer, future only:** Wire the existing five behavior owners through actual SDK executors and
  WorkflowBuilder at the production composition boundary, preserving the current transport/API and
  downstream handoff contracts. Package MAF, definitions and required dependencies in the agent and
  API images; reconcile lockfile, SDK interfaces and import namespaces without optional memory fallbacks.
  Select each agent independently at dispatch, implement true shadow comparison without changing the
  legacy result or blocking its response on shadow work, and reject malformed flags visibly. Integrate
  rollback with the existing progressive-delivery mechanism and a whole-workflow disable path. Do not
  retire legacy until AUD-033-004/AUD-033-013/AUD-033-015 pass. Support the agreed sixth-agent example
  through the factory/configuration contract, not a separate toy class. Complete or explicitly resolve
  the missing reports-package initializer obligation from T002.

  **Tester, future only:** Extend [executor tests](../../tests/unit/test_executor_base.py#L1),
  [workflow tests](../../tests/integration/test_workflow_crash_recovery.py#L1) and the
  [no-op home](../../tests/integration/no_op_agent/test_no_op_inherits_middleware.py#L1). Use a real SDK
  graph and controlled chat/storage transports; assert every agent's legacy/maf/shadow dispatch, a mixed
  run, typo rejection, no duplicate side effects, nonblocking shadow failure, restore hooks and rollback
  at the next step. Inspect the built image contents in a later packaging gate. Do not mock the factory,
  graph or executor classes being proved.

  **Future validation:** After locked SDK/image composition is fixed, run
  `python -m pytest tests/unit/test_executor_base.py tests/integration/test_workflow_crash_recovery.py tests/integration/no_op_agent -q`.
  Expected: tests exercise the production composition path and real framework boundaries without live
  model dependency. **Done:** Actual traffic and isolated calls share the same framework implementation;
  every documented flag changes the intended owner and retains a working legacy escape path.

- [ ] AUD-033-004 Restore real legacy parity and the unchanged warning contract

  **Affected:** FR-001, FR-002, FR-003, FR-022, FR-023, FR-024, FR-024a, FR-026; SC-001;
  T026, T027, T028, T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T040, T040b;
  US1-1, US1-2, US1-4 and the no-new-capabilities/model-tier/scope constraints.

  **Expected / observed / impact:** Migration must preserve actual decisions, populated fields, prompt
  and consumer contracts. The [risk facade](../../apps/agents/maf_runtime/agents/risk_assessment_agent.py#L25)
  fabricates a decision record instead of a [HazardAssessment](../../apps/agents/risk_assessment/agent.py#L76).
  Evacuation/allocation/communication return ID-only plan/alert constructions, bypassing their real
  pipelines. Monitoring constructs a fresh agent without its configured LLM and does not run the full
  misinformation path. The builder sends a plain `_DuckEnvelope` that
  [run_maf](../../apps/agents/maf_runtime/agents/_factory.py#L265) stringifies instead of serializing its
  signal fields. Downstream steps run unconditionally, including after a suppressed triage result.
  The new [communication prompt](../../apps/agents/maf_runtime/agents/communication.yaml#L8) is not guarded
  by byte equality; the [test](../../tests/unit/test_communication_prompt_invariant.py#L47) only requires
  tokens. T040b's qualified superset wording does not authorize replacing an unchanged prompt body.
  The definition also selects `reasoning`, while the existing
  [translation/drafting path](../../apps/agents/communication/translator.py#L142) selects `drafting`.

  **Developer, future only:** Adapt the established Monitoring, RiskAssessment, Evacuation,
  ResourceAllocation and Communication pipeline entry points, with their dependency configuration,
  original typed inputs, lifecycle, suppression/enrichment decisions and downstream handoffs intact.
  Map outputs at explicit compatibility boundaries; do not substitute audit-record models for business
  output models merely to satisfy a facade schema. Serialize complete signal data and honor conditional
  handoffs. Identify and freeze the authoritative legacy warning prompt/template composition; retain its
  byte-equal body and populated output fields or record a future explicit contract resolution before
  changing it. Preserve current model tiers and the existing Foundry endpoint work; do not restore an
  obsolete provider simply because the original plan named it. Dependencies: AUD-033-003 and AUD-033-013.

  **Tester, future only:** Expand all five existing [equivalence tests](../../tests/equivalence/test_monitoring_equivalence.py#L24)
  and [prompt invariant tests](../../tests/unit/test_communication_prompt_invariant.py#L47). Use existing
  real input fixtures including spec-025 audit cases, configured legacy dependency fakes, contradictory/
  stale signals, suppress/enrich decisions, blocked routes, resource shortfalls and multilingual drafts.
  Assert real pipeline calls, nonempty expected business output, conditional downstream invocation,
  identical populated fields, and byte equality of the approved prompt body. A one-character prompt
  mutation must fail even if every warning keyword remains present.

  **Future validation:** With representative legacy inputs and a controlled model transport, run
  `python -m pytest tests/equivalence tests/unit/test_communication_prompt_invariant.py -q`.
  Expected: actual legacy and migrated invocation pairs are compared, never prewritten equal outputs.
  **Done:** All five fallbacks are real behavior-preserving delegates; warning content/schema invariance
  and real consumer compatibility are proved before any cutover.

- [ ] AUD-033-005 Connect durable HITL decisions to the existing approval authority

  **Affected:** FR-008, FR-009, FR-010, FR-014, FR-024; SC-003, SC-008;
  T005, T035, T045, T046, T047, T048, T048b, T048c, T056; US2-2, US2-3, US2-4;
  paused-crash, simultaneous-decision and resumed-safety-rejection edge cases.

  **Expected / observed / impact:** A recorded spec-008 decision is the only way to resume publication.
  The [bridge envelope](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L124) differs from
  [the existing flat approval payload](../../apps/agents/communication/approval.py#L43) and from the
  [actual ApprovalRequest model](../../apps/agents/communication/agent.py#L42), which is an HTTP body.
  The decision queue is only a constant; no subscriber or durable decision lookup is wired. The listener
    accepts arbitrary dictionaries without checking provenance/identity, updates only run status, and
  swallows resume failure. `rejected` follows the cancel branch but still meets `outcome != "reject"`
  for the optional callback. No authenticated publish-to-Completed path exists. UUIDv5 request IDs are
  useful, but lookup injection, sequential conflict tests and a queue-envelope count are not crash-safe
  or concurrent approval evidence. Existing spec-008 modify creates a new pending-review version,
  whereas this listener treats modify as a resume authorization.

  The existing [commander queue declaration](../../infra/modules/communication-agent.bicep#L142) sets
  `requiresDuplicateDetection: false`, and its module declares `communication-decisions` rather than
  the assumed `approval_decisions`. No active main-template reference to that module was found. These
  are source/configuration facts, not assertions about the current deployed queues or containers.

  **Developer, future only:** Own the bridge and its production listener composition, using the existing
  approval workflow/store/queues and authority, not a parallel identity model. Reconcile the real envelope
  and modification/reapproval contract explicitly. Persist request, draft version and original deadline
  before external effects; set broker dedup identity; durably consume only recorded authorized decisions.
  Apply one decision with AUD-033-006 concurrency control and audit both competing attempts. Restore
  checkpoints on approve/modify as allowed by the existing policy, publish only the authorized version,
  record completion, and never resume a rejection alias. Reuse escalation timers/chain/maxima, reconcile
  elapsed time after restart, notify the commander on safety rejection, and expose exhausted escalation
  as NeedsOperatorDecision. Treat transport/lookup failure as a recoverable fault, not proof of delivery.
  Coordinate with AUD-033-001, AUD-033-008 and AUD-033-010.

  **Tester, future only:** Extend [HITL tests](../../tests/integration/test_hitl_round_trip.py#L1),
  [guard tests](../../tests/unit/test_send_response_call_sites.py#L31) and
  [workflow tests](../../tests/integration/test_workflow_crash_recovery.py#L1). Use the real approval
  schema plus stub broker/store transports, not a made-up decision-only authority. Assert authorized
  approve and allowed modification publish exactly once; reject/rejected, forged/missing identity,
  wrong-tenant/stale-version and non-queue decisions publish zero times. Interleave two persistent clients
  at a barrier; assert one resume, typed conflict and two audit attempts. Crash before/after each publish,
  decision write and checkpoint; assert stable request/deadline and no duplicate notification. Advance
  the real timer through every level and maximum; assert no auto-approval. Remove one decision from a
  published-event fixture and require the no-orphan-publication check to fail.

  **Future validation:** After durable request/decision fixtures are available, run
  `python -m pytest tests/integration/test_hitl_round_trip.py tests/integration/test_workflow_crash_recovery.py tests/unit/test_send_response_call_sites.py -q`.
  Expected: real integration boundaries are exercised and both unauthorized paths and duplicate side
  effects fail. **Done:** Every public publish is attributable to one durable authorized decision;
  reject, timeout, concurrent decisions and restart preserve the existing commander policy.

- [ ] AUD-033-006 Make run creation and state history atomic and auditable

  **Affected:** FR-011, FR-011a, FR-011b, FR-012, FR-012c; T014, T016, T042b, T044, T048b, T051;
  one-run-per-incident clarification, WorkflowRun validation and concurrency edge cases.

  **Expected / observed / impact:** Uniqueness and transitions must hold across replicas, with prior-run
  linkage and immutable history. [Create](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L110)
  queries and inserts separately, treating query failures as no active run. The memory lock covers only
  individual operations, not the check-plus-insert. [Status update](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L255)
  replaces without an ETag and returns success on same-state writes; there is no append-only transition
  record. Prior linkage is caller-optional and the builder never supplies it. NeedsOperatorDecision is
  inactive in the data model, although FR-011a permits a successor only after a terminal state; that can
  admit a successor while the old held run remains resumable. Current-step/last-checkpoint fields are
  not advanced at each builder step. Failure context and invalid-transition audit are not enforced.

  **Developer, future only:** Implement an atomic incident-scoped run reservation/transactional batch
  and conditional status updates, preserving the agreed partition contract and tenant boundary. Fail
  closed on store faults. Resolve the held-run/supersession conflict explicitly: close the prior run as
  permitted before creating/linking its successor, and prevent two resumable owners. Append immutable
  attributed transition history in the same durable operation; maintain current step, checkpoint,
  terminal timestamp and meaningful failure/operator context. Make cancellation stop later side effects,
  not only change a document. Preserve the seven externally visible states and existing API consumers.
  Dependencies: AUD-033-001, AUD-033-002, AUD-033-005 and AUD-033-009.

  **Tester, future only:** Extend [uniqueness tests](../../tests/unit/test_workflow_run_uniqueness.py#L1)
  and [state tests](../../tests/unit/test_run_state_transitions.py#L1). Use distinct clients and interleave
  lookup/create and read/replace operations, not sequential calls to one in-memory object. Assert one
  active owner, typed loser, no create after a failed uniqueness query, correct terminal/prior linkage,
  held-run exclusion, immutable ordered history, ETag conflict and no post-cancel step. Cover every
  allowed transition plus null failure context, invalid pending state and foreign-tenant lookup.

  **Future validation:** With a transaction-capable fake plus later approved emulator concurrency lane,
  run `python -m pytest tests/unit/test_workflow_run_uniqueness.py tests/unit/test_run_state_transitions.py tests/integration/test_hitl_round_trip.py -q`.
  Expected: concurrency is actually interleaved and history is inspected. **Done:** Persisted invariants
  hold across independent clients, including held runs and cancellation; no read/modify/write race can
  admit duplicate ownership or silently erase a state transition.

- [ ] AUD-033-007 Enforce hard retry deadlines and normalize failures at the invocation boundary

  **Affected:** FR-003, FR-004, FR-012, FR-011b; T011b, T012, T018, T027, T029, T031, T033, T035,
  T042b, T042c, T074b; US1-3, US2-5 and output-schema-change edge case.

  **Expected / observed / impact:** Three attempts and 30 seconds are hard defaults with typed,
  correlated failures. [Budget code](../../apps/agents/maf_runtime/workflow/executors/_base.py#L88)
  awaits each call without a deadline and checks elapsed time only after exceptions. A hanging or slow
  success can exceed the cap. Client and [parser](../../apps/agents/maf_runtime/agents/_factory.py#L281)
  exceptions escape unmapped; parser validation occurs before executor validation. The builder catches
  schema mismatch as generic Failed rather than NeedsOperatorDecision. The error hierarchy is real,
  but merely defining its classes does not normalize the actual failure paths.

  **Developer, future only:** Use one canonical invocation boundary around configuration, provider,
  tools, parsing and output validation, retaining the actual correlation/run context. Map the agreed
  SDK version's errors to canonical classes; preserve nonretryable content-filter/quota/version/schema
  failures. Apply a monotonic total deadline to the call and backoff, never starting another attempt
  after it expires; validate finite positive overrides. Route malformed output to NeedsOperatorDecision
  and deterministic exhausted retry to Failed with field/step context and an audit entry. Do not leak
  raw validation payloads into logs. Keep legacy fallback compatibility explicit with AUD-033-004.

  **Tester, future only:** Extend [executor tests](../../tests/unit/test_executor_base.py#L1),
  [error tests](../../tests/unit/test_maf_runtime_errors.py#L1) and the existing workflow test. Test a
  never-returning call, late success, repeated rate limits/5xx, nonretryable failures, parse-invalid JSON,
  missing/nested fields, zero/negative/NaN/infinite overrides and a deadline reached during backoff.
  Assert elapsed upper bound, exact attempt count, cancellation, preserved correlation, correct run state
  and one sanitized failure audit. Exercise actual parser/client adapters, not only a synthetic `_Sample`.

  **Future validation:** With deterministic fake clock/transports, run
  `python -m pytest tests/unit/test_executor_base.py tests/unit/test_maf_runtime_errors.py tests/unit/test_maf_runtime_error_imports.py tests/integration/test_workflow_crash_recovery.py -q`.
  Expected: timing and state assertions fail when the deadline or schema routing is removed.
  **Done:** No invocation outlives its configured budget, and every exposed failure obeys the canonical
  typed/correlated contract without changing documented nonretryable policy.

- [ ] AUD-033-008 Make safety and immutable audit coverage unavoidable for every invocation

  **Affected:** FR-013, FR-014, FR-015, FR-020; SC-004, SC-005, SC-010;
  T020, T020b, T021, T022, T027, T029, T031, T033, T035, T057, T061, T064, T065;
  US3-1, US3-2, US3-3 and pending-approval safety-rejection edge case.

  **Expected / observed / impact:** Every success, rejection and failure must have a valid immutable
  audit, including isolated/new agents. The [declared chain](../../apps/agents/maf_runtime/agents/_factory.py#L81)
  puts safety before audit; local SDK [sequential middleware dispatch](../../.venv/Lib/site-packages/agent_framework/_middleware.py#L790)
  confirms that a safety raise prevents the downstream audit/OTel call for the inspected 1.2.2 version.
  The facade supplies no incident/run metadata; audit defaults to `unknown`/`isolated`, violating the
  required UUID-linked schema. Correlation is generated independently of the actual span. Writer errors
  are logged and dropped. Resumed rejection only sets metadata flags with no consumer. The no-op test
  manually nests middleware, uses an agent name outside the schema enum, and asserts neither schema
  validity, safety verdict nor captured span. Shadow output also writes raw input/output JSONL outside
  the fingerprinted audit path, without an inspected minimization/retention contract.

  **Developer, future only:** Own the factory invocation boundary and three middleware modules. Make
  audit surround safety and invocation, seed real incident/tenant/run/trace context, capture failures
  including blocked/allow-list/tool/version outcomes, and define valid isolated/sixth-agent identities.
  Preserve deterministic fingerprints; never persist raw input/output or unsanitized error payloads as
  audit metadata. Provide durable buffering/hold behavior for audit-store faults with visible backlog
  reconciliation, not silent loss. Preserve existing circuit-breaker degraded review flags and make
  empty/unscannable input behavior explicit. Connect a resumed rejection to the agreed alert/run state
  and commander notification, resolving the Cancelled/failure_reason schema conflict. Remove or govern
  raw shadow persistence. Strengthen the single-writer guard to cover aliases/configured container
  clients and actual writes. Dependencies: AUD-033-005, AUD-033-009 and AUD-033-010.

  **Tester, future only:** Extend [no-op tests](../../tests/integration/no_op_agent/test_no_op_inherits_middleware.py#L62)
  and [writer guard](../../tests/unit/test_audit_writer_uniqueness.py#L20). Instantiate the real factory
  with controlled safety/provider/storage transports. For all five agents and the sixth/isolated case,
  assert schema-valid immutable audit, deterministic key-order fingerprints, matching trace context,
  success, blocked input with zero business calls, degraded safety review, tool/version failure, and
  durable audit-failure handling. Resume a paused alert into rejection and assert terminal/held state,
  reason and one commander notification. Scan emitted artifacts for a seeded personal-data sentinel.

  **Future validation:** After contract-compatible context and storage fixtures are prepared, run
  `python -m pytest tests/integration/no_op_agent tests/unit/test_audit_writer_uniqueness.py tests/integration/test_hitl_round_trip.py -q`.
  Expected: removing audit around safety or a second writer makes assertions fail. **Done:** The actual
  shared invocation path, including early rejection and store failure, cannot silently lose audit or
  bypass safety; documented privacy and degraded-mode behavior hold without per-agent boilerplate.

- [ ] AUD-033-009 Align deployed storage configuration and enforce audit retention controls

  **Affected:** FR-006, FR-012a, FR-014, FR-025; T004, T008, T009, T010, T011, T016, T017,
  T018, T019, T020; NN-2/NN-3 and independent checkpoint/audit-retention constraints.

  **Expected / observed / impact:** Stores must use the existing deployed account/database with
  independent automatic retention and enforced immutable audit access. The
  [active database](../../infra/main.bicep#L603) is `disaster-hub`; workflow/tool repositories and checkpoint
  factory default to `platform`. The [agent environment](../../infra/main.bicep#L1139) supplies
  `COSMOS_ENDPOINT`/`COSMOS_DATABASE`, but the checkpoint selector and audit writer require
  `AZURE_COSMOS_ENDPOINT` and the latter reads another database variable. The active template creates
  workflow containers, not `audit_entries`. [Checkpoint default TTL](../../infra/bicep/modules/cosmos-workflow.bicep#L60)
  is positive; omission of per-item TTL is not the explicitly disabled active-run retention posture the
  ADR claims. Terminal stamping is uncalled. The [Rego rule](../../infra/policy/rego/deny_audit_delete.rego#L6)
  expects permissions inline on role assignments, while
  [real assignments](../../infra/main.bicep#L904) reference role definitions at account scope. It ignores
  inherited/wildcard rights and replacement/update, exposes a named `deny_audit_delete` rule rather than
  a demonstrated gate entrypoint, and has no caller found in the CI workflows. A posture YAML label
  does not enforce seven-year retention or deny destructive access.

  **Developer, future only:** Align one validated configuration source across images, repositories,
  audit/checkpoint adapters and deployment outputs. Provision/reference the actual required containers
  in the existing regulated account; fail closed when required settings are absent. Reconcile the
  accepted SDK's document and partition model before deploying immutable partition/unique-key changes.
  Disable item expiry while a run is nonterminal; start the 30-day clock after terminality, independently
  of the audit window. Implement the agreed append-only data-plane permissions, no-delete/no-replace
  retention boundary and deployment policy evaluation including role definitions, inherited scope and
  wildcard grants. Reuse current policy/AVM/governance conventions; do not weaken existing policies or
  migrate regulated data without a separately approved plan. Coordinate with AUD-033-001/AUD-033-008.

  **Tester, future only:** Extend [repository tests](../../tests/unit/test_workflow_run_uniqueness.py#L1),
  [tool registration tests](../../tests/unit/test_tool_registration_repository.py#L1) and
  [audit-writer checks](../../tests/unit/test_audit_writer_uniqueness.py#L1) with controlled configuration
  and store fixtures. Cover deployed env names, missing endpoint/database, lookup/write failure, long
  active/held runs, exactly terminal plus 30 days, and independent seven-year audit retention. Proposed
  new policy fixture home: `infra/tests/maf-audit-retention/` (not existing evidence). Test direct and
  inherited delete/update/upsert/wildcard roles and positive/no/default item TTL, requiring the canonical
  gate to reject unsafe fixtures and accept the least-privilege policy.

  **Future validation:** After the policy entrypoint and compiled-template fixture are prepared, run
  the three named existing pytest files and `opa test infra/policy/rego -v`; wire any added policy tests
  into that invocation. Expected: fail-closed configuration and the unsafe policy/retention fixtures
  fail their negative assertions. Later deployment validation must inspect the actual target policy and
  role state; this audit did not compile Bicep or query Azure. **Done:** Application settings, deployed
  schema, retention and effective data-plane permissions agree and are automatically enforced.

- [ ] AUD-033-010 Connect telemetry and daily reconciliation to real invocation evidence

  **Affected:** FR-014, FR-016, FR-017, FR-020; SC-004, SC-005, SC-008, SC-009, SC-010;
  T013, T022, T057, T058, T060, T068; US3-4, US3-5 and telemetry-outage edge case.

  **Expected / observed / impact:** Every step/tool must link to a parent workflow trace and emit the
  expected model/token/latency fields; daily reconciliation must read real counts and persist a result.
  [Bootstrap](../../apps/agents/maf_runtime/observability.py#L27) is defined but not called in the inspected
  runtime. [OTel middleware](../../apps/agents/maf_runtime/middleware/otel_middleware.py#L44) only adds
  supplied context, which the caller omits; it does not explicitly provide model/token/latency metrics
  or a workflow-state producer. Its span creation/context exit is outside the attribute-write guard.
  [Reconciliation](../../apps/api/app/api/routes/admin/reconciliation.py#L76) compares three environment
  integers, defaulting to zero, and does not query stores, persist reports, count workflow steps or run
  on a schedule. No MAF state/agent workbook panels or wired duration/version alerts were found.
  Arithmetic-only [tests](../../tests/unit/test_reconciliation.py#L1) cannot establish gap detection.

  **Developer, future only:** Initialize the existing Azure Monitor pipeline once at the actual host;
  retain managed-identity auth and avoid a parallel telemetry backend. Establish one parent trace and
  propagate context across SDK agents, checkpoints, approvals and MCP calls. Emit model identity,
  input/output tokens for every LLM-backed step, latency, outcomes, workflow state and approval metrics,
  using explicit adapters where the pinned SDK's conventions differ. Read true invocation/audit/span/
  step counts with a defined window, tenant/agent grouping and late-arrival policy; persist reconciliation
  documents and page on real gaps. Register its daily schedule and the required workbook/alert modules.
  Do not treat absent sources or exporter failure as a zero-gap result. Keep execution safe during
  exporter outages; enforce audit durability separately through AUD-033-008/AUD-033-009.

  **Tester, future only:** Extend [reconciliation tests](../../tests/unit/test_reconciliation.py#L1),
  [no-op integration](../../tests/integration/no_op_agent/test_no_op_inherits_middleware.py#L62) and
  [dashboard regression tests](../../tests/contract/test_existing_dashboards_no_regression.py#L28).
  Use an in-memory exporter, fake Monitor queries and durable audit fixture with known per-agent totals.
  Assert startup idempotence, trace-parent identity, actual tokens/model, workflow-state and approval
  transitions, missing/extra audit/span rows, delayed ingestion, zero traffic vs unavailable sources,
  report persistence and alert dimensions. Throw during span start/export/end and confirm one business
  invocation with a separately retained audit. Validate all five agents plus the sixth example.

  **Future validation:** After a real query-adapter fixture and exporter are wired, run
  `python -m pytest tests/unit/test_reconciliation.py tests/integration/no_op_agent tests/contract/test_existing_dashboards_no_regression.py -q`.
  Expected: injected emission gaps fail reconciliation and all field assertions inspect emitted data.
  Schedule execution, dashboard population and five-minute alert delivery remain later environment
  gates. **Done:** Counts come from actual sources, gaps cannot silently report healthy, and every step
  is traceable through the existing telemetry pipeline.

- [ ] AUD-033-011 Complete operator history, metrics, filtering and timely workflow views

  **Affected:** FR-011, FR-011b, FR-017, FR-024; SC-008, SC-009;
  T025, T051, T052, T053, T054, T055, T056b, T059; operator API contract and US2-5/US3-5.

  **Expected / observed / impact:** Operators need real checkpoints/audit/metrics, state filters and a
  paused-run view within ten seconds. [History endpoints](../../apps/api/app/api/routes/workflow_runs.py#L147)
  always return empty arrays; [metrics](../../apps/api/app/api/routes/workflow_runs.py#L121) always return
  zero. Multi-status pagination discards continuation and query validation is incomplete. The
  [client](../../apps/web/src/lib/api/workflow-runs.ts#L44) cannot send continuation or established auth
  context. [The page](../../apps/web/src/app/operations/workflows/page.tsx#L27) ignores `state`, selects
  only among its first 100 results, has no polling/push refresh and supplies no trace URL callback.
  [Detail](../../apps/web/src/components/workflow/WorkflowRunDetail.tsx#L29) uses audit document ID rather
  than correlation ID. Tabs are links with tab roles but no complete tablist/panel keyboard pattern.
  The four-window metric control exists, but its values are not backed by data.

  **Developer, future only:** Complete all six API contracts against tenant-scoped durable stores and
  the existing Monitor query helper, with no-store, validated enums/limits, consistent error envelopes
  and stable continuation behavior. Preserve public field names and add explicit schema adapters for
  SDK checkpoint internals. Reuse the established authenticated client. Apply the URL state filter,
  fetch a selected run outside the first page, support pagination, render held/failure reasons, use the
  actual trace correlation field and configure a safe trace link. Add bounded polling/push to meet the
  ten-second paused-state target, with loading/error/stale/empty states and usable accessible state/window
  controls. Keep the page under operations and the metrics beside run detail. Dependencies:
  AUD-033-002, AUD-033-006, AUD-033-010 and AUD-033-014.

  **Tester, future only:** Extend [API tests](../../tests/contract/test_workflow_run_api.py#L1) and
  [interface E2E tests](../../tests/e2e/interface-coverage.spec.ts#L349), using the existing
  [workflow page object](../../tests/e2e/web-coverage/_support/pages/operations.workflows.po.ts#L8).
  Seed all seven states, two tenants, more than 100 runs, 50-plus checkpoints, audit correlations and
  nonzero metrics for each window. Assert state navigation actually filters, direct deep links work,
  pages have no duplicates, missing/foreign run IDs do not reveal histories, trace URL uses correlation
  rather than document ID, and a paused update is visible within ten seconds. Require keyboard and axe
  checks for these actual controls and do not accept HTTP 500 as a successful workflow page.

  **Future validation:** After the API/data fixtures and browser environment are prepared, run
  `python -m pytest tests/contract/test_workflow_run_api.py -q` and
  `pnpm --filter @ama/web exec playwright test ../../tests/e2e/interface-coverage.spec.ts --project=chromium --grep "Operations workflows"`.
  Update that existing workflow case to include the concrete assertions above. A later web type/build
  gate is also required. **Done:** Real scoped histories/metrics and every visible control work; paused
  state and trace navigation are demonstrably timely and accessible.

- [ ] AUD-033-012 Integrate authenticated MCP discovery and real routing with enforced version pins

  **Affected:** FR-018, FR-019, FR-019a, FR-020, FR-021, FR-025; SC-006;
  T006, T017, T030, T031, T062, T063, T064, T065, T066, T067, T068;
  US4-1, US4-2, US4-3 and malformed-tool-response edge case.

  **Expected / observed / impact:** The agent must discover and invoke a real independently deployed
  routing tool with allowed major version, managed identity and linked audit/telemetry. The
  [factory](../../apps/agents/maf_runtime/agents/_factory.py#L90) passes no tools and does not resolve
  `tool_allow_list`. [Lookup](../../apps/agents/maf_runtime/mcp/allow_list.py#L51) picks the first registration
  by tool name, ignoring the YAML major when multiple versions are bound. The client caches that entry,
  [guesses v1](../../apps/agents/maf_runtime/mcp/routing_tool.py#L151) if accessors are absent and probes
  `call`/`invoke` without a verified connection/discovery lifecycle. It only checks that a result is a
  dictionary, so malformed structured data can pass. Auth is not supplied to the tool; internal ingress
  and an outbound identity do not prove authenticated callers. Evacuation calls routing only in the
  legacy method behind `MAF_USE_ROUTING_TOOL`, discards its result and swallows ToolFailure. The
  [server](../../tools/routing_mcp_server/server.py#L20) returns a straight-line mock and empty closures;
  `SERVER_VERSION` is used for logging, not explicitly bound to protocol metadata. Its FastMCP startup
  compatibility is UNVERIFIED for the resolved MCP version. The routing and alert Bicep modules exist
  but no deployment caller was found. Tests replace both SDK protocol helpers with functions.

  **Developer, future only:** Bind allowed tools in the real Agent factory, intersecting the definition's
  `(tool, major)` pin with authorized registrations, and use the supported pinned SDK MCP lifecycle for
  initialize/discovery/call/close. Refuse absent/invalid server semver, version mismatch and malformed
  results; never guess a version or output. Normalize transport errors and propagate run/trace context
  into audit/metrics. Enforce managed-identity authentication at client and server; preserve internal
  ingress. Wrap the existing [RouteComputer](../../apps/agents/evacuation/router.py#L55)/road data rather
  than mock geometry, preserve closure/capacity semantics, and consume its result in the plan. Publish
  actual server version/capabilities with additive-within-major evolution tests. Wire the existing
  routing/alert modules and registration process to deployment, using repository policy/AVM conventions;
  registration must fail closed rather than print a successful in-memory seed. Dependencies:
  AUD-033-003, AUD-033-008, AUD-033-009 and AUD-033-010.

  **Tester, future only:** Extend [MCP tests](../../tests/integration/test_mcp_routing_tool.py#L1) and
  [registration tests](../../tests/unit/test_tool_registration_repository.py#L1). Use real SDK protocol
  parsing with an isolated local MCP transport/server fixture and existing road-network fixtures.
  Assert allowed v1 success with a usable route, v1 additive discovery without agent edits, explicit v2
  opt-in, missing/invalid semver, removal/type-narrowing rejection, revoked or unbound tool blocked before
  network, cross-agent pins, unauthorized caller, timeout/DNS/error envelope/invalid JSON/wrong fields,
  and one correlated tool record/alert. Block the only road and require no fabricated route. Verify
  actual startup and serverInfo in the later runtime lane, not a substituted helper result.

  **Future validation:** With locked MCP dependencies and controlled server/road/auth fixtures, run
  `python -m pytest tests/integration/test_mcp_routing_tool.py tests/unit/test_tool_registration_repository.py -q`.
  Expected: real initialize/discovery and typed result/error assertions pass. Later deployment, seed-row
  and alert delivery evidence must be captured separately. **Done:** At least one real agent consumes
  real routing through authenticated MCP; invalid versions/results fail closed with no fabricated plan.

- [ ] AUD-033-013 Make equivalence a non-vacuous comparison of real agent invocations

  **Affected:** FR-023, FR-003, FR-022, FR-024a; SC-001, SC-005, SC-010;
  T023, T024, T036, T037, T038, T039, T040, T040b, T041, T057, T061, T069.

  **Expected / observed / impact:** Cutover requires representative legacy-versus-MAF invocation results,
  at least 95% categorical equality and exactly matching valid populated schema fields. The
  [runner](../../apps/agents/maf_runtime/equivalence/runner.py#L31) only reads prewritten output pairs,
  skips malformed files and accepts missing corpora. [Scoring](../../apps/agents/maf_runtime/equivalence/scorers.py#L125)
  uses fictional/top-level categorical names, skips absent legacy categorical fields, ignores nested
  fields/types and added populated fields, and returns PASS for zero cases. The single
  [monitoring pair](../../tests/equivalence/fixtures/monitoring/smoke-fire-escalate.json#L1) is hand-authored
  equal output; the other four fixture directories are absent. Main CI explicitly permits this bootstrap
  PASS. No committed per-agent result reports were found.

  **Developer, future only:** Make the harness invoke the real configured legacy and migrated surfaces
  over referenced existing unit/integration/contract plus spec-025 fixtures; record source/fixture/model/
  revision provenance. Define categorical paths from the actual output models, validate both schemas,
  compare equal populated field paths recursively, and exclude only agreed free-text values. Reject
  malformed/missing/duplicate fixtures, absent categorical observations, skipped invocation and empty
  cutover corpora. Retain the explicitly requested zero-case `--dry-run` only as labeled bootstrap that
  cannot authorize cutover. Have per-agent CI gates fail for inadequate evidence and produce retained
  Markdown reports. Coordinate with AUD-033-004/AUD-033-007; do not recapture or bless weak fixtures here.

  **Tester, future only:** Extend [scorer tests](../../tests/unit/test_equivalence_scorers.py#L1) and all
  five existing equivalence modules. Assert exactly 19/20 categorical matches passes, 18/20 fails, and
  one invalid schema/missing or extra populated nested field fails. Mutate the real monitoring `decision`
  and risk severity fields; they must be observed. Cover changed free text only, missing categorical
  data, zero cases, invalid JSON, mismatched counts, duplicate IDs, provider failure and dry-run exclusion.
  Spy only transports/dependencies, not the two behavior owners; assert each was invoked for every case.

  **Future validation:** After restoring representative fixtures and controlled invocation transports,
  run `python -m pytest tests/unit/test_equivalence_scorers.py tests/equivalence -q`.
  Expected: each agent has a nonzero sourced corpus and a revision-bound report; deliberate behavior
  or schema mutations block its cutover. **Done:** Neither prewritten identical outputs nor empty data
  can make a migration eligible; all five actual implementations satisfy the documented thresholds.

- [ ] AUD-033-014 Replace empty declaration snapshots with observed compatibility contracts

  **Affected:** FR-017, FR-024, FR-024a; SC-009; T009b, T024b, T040b, T060, T060b.

  **Expected / observed / impact:** Every operator response, audit document and dashboard-consumed
  attribute must retain its pre-MAF fields. [Snapshot capture](../../tests/contract/test_audit_telemetry_fields_no_regression.py#L28)
  collects locally declared BaseModels, including request bodies, silently skips failed imports and
  misses actual dict/imported/nested responses. Its audit source is the new schema, not legacy records.
  The [dashboard snapshot](../../tests/contract/snapshots/existing_dashboard_fields.json#L1) is empty;
  [the regression test](../../tests/contract/test_existing_dashboards_no_regression.py#L28) skips it.
  The collector's repository-root calculation is correct, but its default dashboard directory is not
  the real workbook location. Its regexes miss existing query forms/dotted keys.
  Current tests therefore cannot catch a removed emitted field despite intact schema/query text.

  **Developer, future only:** Capture independently sourced pre-cutover responses, documents and emitted
  attributes for every operator contract and existing query. Fix discovery to the actual
  [workbooks](../../infra/modules/workbooks/llm-cost.json#L1) and infrastructure query assets; use structured
  JSON parsing and documented query-field extraction. Preserve baseline provenance and fail on empty,
  missing or unreadable capture input. Compare actual MAF output for each of the five agents against
  these baselines; additions permitted by FR-024 do not relax FR-024a's unchanged warning output set.
  Keep snapshot updates explicit and reviewed; do not regenerate a baseline automatically on a failing
  PR. Dependencies: AUD-033-004, AUD-033-008, AUD-033-010 and AUD-033-011.

  **Tester, future only:** Extend [field regression tests](../../tests/contract/test_audit_telemetry_fields_no_regression.py#L93)
  and [dashboard tests](../../tests/contract/test_existing_dashboards_no_regression.py#L28) with real emitted
  output fixtures. Assert every route response and each agent's required telemetry/audit field is populated;
  remove/rename one emitted field while keeping model and query text unchanged and require failure.
  Include imported models, dict responses, nested fields, bracketed/dotted KQL attributes, an unreadable
  source and empty baseline. Approved additive compatibility must pass; warning-field drift must fail.

  **Future validation:** With independently preserved legacy snapshots and emitters wired, run
  `python -m pytest tests/contract/test_audit_telemetry_fields_no_regression.py tests/contract/test_existing_dashboards_no_regression.py tests/unit/test_communication_prompt_invariant.py -q`.
  Expected: zero skips/auto-generated baselines, nonempty source coverage and deliberate mutation failure.
  **Done:** Compatibility gates verify actual consumer-visible values/fields for all five agents and
  cannot pass because their baseline or source enumeration is empty.

- [ ] AUD-033-015 Build real recovery and capacity evidence before enabling cutover

  **Affected:** FR-012b, FR-023; SC-002, SC-007; T041, T049, T050, T069, T071, T075.

  **Expected / observed / impact:** At least 25 active runs sustained, 50 burst for 60 minutes, 99/100
  successful restores and at most 10% latency regression must be measured. The
  [full load branch](../../tests/load/test_workflow_capacity.py#L59) runs five batches of five and no timed
  steady/burst windows; its smoke is sequential. Its repository-root and artifact-path calculations
  are correct. [Baseline metadata](../../tests/load/baselines/legacy_baseline.json#L4)
  declares placeholder values, and [capture](../../scripts/capture_legacy_baseline.sh#L15) writes those
  constants with a timestamp without workload execution. The named crash test does not restart anything.
  No MAF results directory or performance evidence was found. Checked T071/T075 are not measurements.

  **Developer, future only:** With AUD-033-001/AUD-033-003/AUD-033-013 complete, implement the same
  representative hazard profile for real legacy and MAF timing. Keep at least 25 active runs
  through the agreed sustained window (T050 specifies 30 minutes), then 50 during the full 60-minute burst;
  include recovery checks at capacity. Measure signal receipt to ready-for-approval consistently, not
  human dwell time. Capture p50/p95/p99, throughput, failures, environment, revision, concurrency/time
  evidence and per-trial diagnostics. Reject placeholder/stale/wrong-environment baseline data and wire
  the per-environment gate before a flag flip. Do not claim success from a timestamped shape-only file.

  **Tester, future only:** Extend [load harness](../../tests/load/test_workflow_capacity.py#L48) and
  [crash harness](../../tests/integration/test_workflow_crash_recovery.py#L1). Unit-check active concurrency
  and time-window accounting with a fake clock, then run the real future isolated capacity environment.
  Inject process termination at random boundaries, either parallel branch and HITL pause; count each
  completed step once. Assert >=99/100 restores, zero workflow loss, measured duration/concurrency bands,
  <=1.10 baseline p95 and no error masking. Deliberately introduce >10% delay, missing trials and
  placeholder baseline metadata; each must block promotion.

  **Future validation:** After baseline capture is a real measurement and the approved environment is
  provisioned, set `MAF_LOAD_FULL=1` and run
  `python -m pytest tests/load/test_workflow_capacity.py tests/integration/test_workflow_crash_recovery.py -q`.
  These are later long-running runtime tests, explicitly not run here. Expected: revision-bound real
  artifacts meeting every band and recovery threshold. **Done:** Cutover cannot proceed without complete,
  reproducible baseline, capacity and fault-injection evidence from the required environment.

- [ ] AUD-033-016 Schedule the run-duration guard against continuous elapsed time

  **Affected:** FR-011, FR-011b, FR-012c; T015, T044; eighth clarification and maximum-duration edge case.

  **Expected / observed / impact:** A continuously nonterminal run older than 72 hours must automatically
  move to NeedsOperatorDecision with elapsed time and last-completed step. The
  [watchdog](../../apps/agents/maf_runtime/workflow/duration_watchdog.py#L40) instead reads `last_step_at`,
  which status transitions reset. A run can exceed the total duration while making intermittent progress.
  It scans only the first 200 rows per state, has no caller/schedule found, logs no structured elapsed
  reason, and uses `MAF_DURATION_CAP_HOURS`/`MAF_WATCHDOG_INTERVAL_SECONDS` outside the specified prefix.
  Its [tests](../../tests/unit/test_duration_watchdog.py#L20) check 71h59m and 73h only, not continuous age,
  exact boundary, overrides, backlog coverage or visible alerting.

  **Developer, future only:** Resolve the spec's continuous-duration rule versus task/data-model
  last-step wording explicitly, retaining FR-012c's safety outcome. Use an immutable start/continuous
  interval timestamp, traverse all eligible runs with pagination, validate finite positive configured
  limits under the agreed prefix, and register the five-minute task in the actual host/scheduler.
  Conditionally transition once, retain elapsed duration and last completed step, and emit an observable
  operator alert without auto-cancel/complete. Dependencies: AUD-033-006 and AUD-033-010.

  **Tester, future only:** Extend [watchdog tests](../../tests/unit/test_duration_watchdog.py#L1) using
  a fake clock and paginated store. Assert 72h-epsilon, exactly 72h and +1s; a recent step in a 73-hour
  run; an old last-step but new continuous interval; AwaitingApproval; already-held/terminal runs;
  environment override, malformed limit, 201-plus rows, scheduler invocation, repeated scans and a
  concurrent terminal decision. Require one correctly attributed alert and no terminal auto-action.

  **Future validation:** Once the scheduler and clock adapter exist, run
  `python -m pytest tests/unit/test_duration_watchdog.py tests/unit/test_run_state_transitions.py -q`.
  Expected: full elapsed-age/boundary/pagination assertions plus scheduled invocation coverage.
  **Done:** Every eligible long run is surfaced automatically and exactly once with useful context;
  progress or pagination cannot postpone the continuous-duration guard indefinitely.

- [ ] AUD-033-017 Reconcile completion claims, executable guidance and required review evidence

  **Affected:** T001, T003, T004, T005, T006, T007, T009, T010, T020b, T024b, T041, T047, T053,
  T054, T056, T057, T061, T066, T067, T068, T069, T070, T071, T072, T073, T074, T074b, T075, T076;
  SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008, SC-009, SC-010 and phase/review gates.

  **Expected / observed / impact:** Completed tasks require substantive assertions and separate proof of
  execution/review. Every original task is checked, but no local final validation/analyze/sign-off
  artifacts exist, reports are absent, and the baseline openly disclaims measurement. The
  [quickstart](quickstart.md#L1) uses missing fixtures/scripts, unsupported `--input`/`--resume`/
  `--emit-report` CLI options and directory-relative commands that cannot run as written. There is no
  Last Validated section. The cutover/rollback documents are authored but dry-run/co-sign claims are
  unverified. The `.gitkeep` exists, but the [ignore rules](../../.gitignore#L1) do not exclude equivalence
  JSON; raw shadow JSONL also lacks a defined policy. Main CI runs contract/integration and equivalence,
  not the spec's unit guards or its full capacity gate. The other workflow unit lanes target unrelated
  evaluation/spec-035 packages. No evidence authorizes relaxing these original success clauses.

  **Developer, future only:** After the behavior repairs, update the feature's specifications/contracts,
  ADR references, quickstart and playbooks through a later authorized documentation change. Record
  explicit resolutions for SDK-storage/HITL names, held-run uniqueness, duration clock, warning-body
  invariance and strict document schemas; preserve original history. Align commands with real CLI args,
  existing curated fixtures and working directories. Retain Markdown cutover reports, deliberately
  ignore raw JSON as required, and govern shadow artifacts. Wire focused unit/contract/equivalence and
  policy gates plus the separately authorized environment load gate into CI/cutover. Strengthen static
  guards to test actual forbidden behavior, not just one literal string. Do not mark developer/tester or
  actor work complete in this review-only change.

  **Tester/reviewer, future only:** After all required repairs, execute the nine quickstart procedures
  in the intended dev environment and record command, revision, time, result and artifacts. Independently
  rehearse per-agent shadow/maf/rollback, measure the five-minute target, and attach real nonempty reports.
  Have the specified security/compliance/architecture/SRE/QA/public-information/commander contributors
  review their affected gates; record actual identities and decisions rather than agent-role labels.
  Run the required spec-plan-task consistency review and resolve/accept findings with justification.
  Mutation-check unit guards, compatibility, unauthorized publication and cutover evidence rejection.
  Existing homes: [executor](../../tests/unit/test_executor_base.py#L1),
  [guard](../../tests/unit/test_send_response_call_sites.py#L31),
  [API](../../tests/contract/test_workflow_run_api.py#L1),
  [equivalence](../../tests/equivalence/test_monitoring_equivalence.py#L24) and
  [capacity](../../tests/load/test_workflow_capacity.py#L48) suites.

  **Future validation:** In the later prepared environment, run the original required lint/type/build
  gates and `python -m pytest tests/unit tests/integration tests/contract tests/equivalence -q --tb=line`,
  followed by AUD-033-015's separately authorized capacity/recovery lane and the corrected quickstart.
  Expected: no skipped/empty false-green gates; signed revision-bound outcomes and remaining exceptions
  clearly recorded. **Done:** Authored artifacts, static implementation, executed validation, environment
  state and human approval are distinguishable; all completion claims have the required evidence.

## Original Task Traceability

Each original checkbox below is copied verbatim, not endorsed. IMPLEMENTED means the scoped authored
artifact/behavior is supported by source, not that its named command was executed. PARTIAL includes a
specific missing obligation; UNVERIFIED is used for execution, measured outcome or review claims not
established by local artifacts. SUPERSEDED requires the cited explicit replacement. `none` in the last
column means no separate implementation follow-up for that authored task. All original tasks here have
a checkbox, so no original-state cell needs `none`.

| Original task | Original state | Status | Source/test evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | PARTIAL | [Dependency declarations](../../apps/agents/pyproject.toml#L30) add MAF/OpenAI/Cosmos/MCP; [ADR](../../docs/corpus/aidr/decisions/adr-033-01-azure-openai-chat-client.md#L46) explains excluding azure-ai. Ranges, a different lock resolution and image installs do not prove the requested installed/import-smoke state. | AUD-033-003, AUD-033-017 |
| T002 | [X] | PARTIAL | [Runtime initializer](../../apps/agents/maf_runtime/__init__.py#L1) and agent/workflow/executor/checkpoint/middleware/MCP/repository/equivalence packages exist; reports contains a gitkeep, not the requested reports-package initializer. Image omission prevents packaged adoption. | AUD-033-003 |
| T003 | [X] | IMPLEMENTED | Relocated [ADR-033-01](../../docs/corpus/aidr/decisions/adr-033-01-azure-openai-chat-client.md#L1) has Status/Context/Decision/Consequences/References, checkpoint rationale and the Learn URL. Authored decision, not an SDK execution record. | none |
| T004 | [X] | IMPLEMENTED | Relocated [ADR-033-02](../../docs/corpus/aidr/decisions/adr-033-02-cosmos-checkpoint-storage.md#L1) records SDK-storage replacement, run partition, TTL and audit deny-delete intent. Its operational claims need the separate storage fixes. | AUD-033-001, AUD-033-009 |
| T005 | [X] | PARTIAL | [ADR-033-03](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L28) explicitly replaces RequestPort and describes metadata, but asserted existing queues/store/envelope do not match [approval source](../../apps/agents/communication/approval.py#L43); no full verified mapping/review evidence. | AUD-033-005, AUD-033-017 |
| T006 | [X] | IMPLEMENTED | Relocated [ADR-033-04](../../docs/corpus/aidr/decisions/adr-033-04-mcp-streamable-http.md#L1) records transport and rejected alternatives. It is not proof of actual MCP runtime integration. | none |
| T007 | [X] | IMPLEMENTED | Root [ruff includes](../../ruff.toml#L6) and [mypy scope](../../pyproject.toml#L81) include apps, so MAF is covered despite configuration living outside the named subproject. No lint/typecheck was run; CI typecheck is advisory. | AUD-033-017 |
| T008 | [X] | PARTIAL | [Three container resources](../../infra/bicep/modules/cosmos-workflow.bicep#L34) exist with named partitions/TTL; SDK document shape, retention and current database/config integration disagree. Bicep compilation/deployment is UNVERIFIED. | AUD-033-001, AUD-033-009 |
| T009 | [X] | PARTIAL | [Main module call](../../infra/main.bicep#L818) uses the existing account and database; main location is AU East only. Module container-name outputs are not exposed as main outputs. Required what-if/no-unrelated-delta outcome is UNVERIFIED. | AUD-033-009, AUD-033-017 |
| T009b | [X] | PARTIAL | [Snapshot test](../../tests/contract/test_audit_telemetry_fields_no_regression.py#L28) and relocated-name [snapshot](../../tests/contract/snapshots/api_audit_telemetry_fields.json#L1) exist, but inspect local model declarations/new schema, not every real legacy/MAF response and audit/span output. | AUD-033-014 |
| T010 | [X] | PARTIAL | Rule relocated to [policy/rego](../../infra/policy/rego/deny_audit_delete.rego#L6); it reads inline permissions from assignments, does not cover inherited/wildcard rights or mutation, and no executable policy gate/fixtures were found. | AUD-033-009, AUD-033-017 |
| T011 | [X] | PARTIAL | [Posture matrix](../../infra/policy/posture-matrix.yaml#L11) declares permanent audit retention. [Policy-set module](../../infra/bicep/modules/posture-policy-set.bicep#L34) lists unrelated built-in IDs, not a consumed audit-deny rule; PR enforcement unproved. | AUD-033-009 |
| T011b | [X] | IMPLEMENTED | [Canonical hierarchy](../../apps/agents/maf_runtime/errors.py#L29) and [payload/unique-code tests](../../tests/unit/test_maf_runtime_errors.py#L52) cover the required classes, correlation/run fields and retry sets. Actual call normalization remains separate. | AUD-033-007 |
| T012 | [X] | PARTIAL | [Factory](../../apps/agents/maf_runtime/chat_client.py#L80) uses LLMClientConfig and a cognitive-services bearer provider. Endpoint choice is explicitly replaced by [ADR 20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L27); actual version/tier construction tests are absent in the scoped test search. | AUD-033-003, AUD-033-007 |
| T013 | [X] | PARTIAL | [Bootstrap](../../apps/agents/maf_runtime/observability.py#L27) has a lock/idempotence guard and Azure Monitor setup, but no runtime caller or synthetic resource-attribute assertion was found; setup failures are permanently marked done. | AUD-033-010 |
| T014 | [X] | IMPLEMENTED | [Seven-state enum/transition matrix](../../apps/agents/maf_runtime/workflow/run_state.py#L26) and [enumerated tests](../../tests/unit/test_run_state_transitions.py#L18) implement the data-model transitions. Cross-document held-run conflict and durable history are separate. | AUD-033-006 |
| T015 | [X] | PARTIAL | [Flag reader](../../apps/agents/maf_runtime/feature_flags.py#L46) handles legacy/maf/shadow/default/error, but callers swallow invalid modes, no progressive-delivery wiring/tests were found, and additional routing/watchdog flags break the prefix rule. | AUD-033-003, AUD-033-016 |
| T016 | [X] | PARTIAL | [Repository](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L76) has CRUD/state validation; uniqueness is non-atomic and [tests](../../tests/unit/test_workflow_run_uniqueness.py#L20) are sequential memory calls, not a transactional fake. | AUD-033-006, AUD-033-009 |
| T017 | [X] | PARTIAL | [Registration repository](../../apps/agents/maf_runtime/repositories/tool_registration_repository.py#L67) and [tests](../../tests/unit/test_tool_registration_repository.py#L24) cover sequential duplicate refusal/major retention; errors and invalid docs are not normalized/validated, and lookup does not honor YAML major selection. | AUD-033-009, AUD-033-012 |
| T018 | [X] | PARTIAL | [Wrapper](../../apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py#L28) follows the explicit SDK replacement but calls methods absent in the inspected local SDK; no required round-trip/failure-barrier/alert test was found. | AUD-033-001 |
| T019 | [X] | PARTIAL | [Stamp helper](../../apps/agents/maf_runtime/checkpoint/retention.py#L41) writes Cosmos `ttl`, not the task's `_ttl`, and is uncalled; active no-expiry/terminal-clock behavior is neither wired nor asserted. | AUD-033-001, AUD-033-009 |
| T020 | [X] | PARTIAL | [Audit middleware](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L173) fingerprints and classifies exceptions but loses pre-audit rejection/context and drops failed writes. No dedicated comprehensive audit assertion suite was found. | AUD-033-008, AUD-033-009 |
| T020b | [X] | PARTIAL | [Static guard](../../tests/unit/test_audit_writer_uniqueness.py#L20) scans only literal `get_container_client("audit_entries")`; configured/aliased writers and raw shadow output evade it, and the main CI suite does not run it. | AUD-033-008, AUD-033-017 |
| T021 | [X] | PARTIAL | [Middleware](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L63) wraps the existing validator/circuit breaker and blocks, but blocked audit, degraded review recording and pending-alert cancellation/notification are not connected. | AUD-033-008 |
| T022 | [X] | PARTIAL | [Span wrapper](../../apps/agents/maf_runtime/middleware/otel_middleware.py#L44) adds run/step and optional parent, but metadata is unseeded; no real in-memory-exporter/all-attribute/outage assertions were found. | AUD-033-010 |
| T023 | [X] | PARTIAL | [Scorer](../../apps/agents/maf_runtime/equivalence/scorers.py#L125) and [threshold tests](../../tests/unit/test_equivalence_scorers.py#L1) implement rate arithmetic; wrong categorical paths, one-way shallow schema comparison, no validation and empty PASS weaken the rule. | AUD-033-013 |
| T024 | [X] | PARTIAL | [CLI](../../apps/agents/maf_runtime/equivalence/runner.py#L62) writes MD/JSON and supports dry-run; it loads output pairs instead of replaying either agent, skips invalid fixtures and has no capture provenance. | AUD-033-013 |
| T024b | [X] | PARTIAL | [Collector](../../apps/agents/maf_runtime/equivalence/dashboard_snapshot.py#L76) exists with a correct repository root; [committed snapshot](../../tests/contract/snapshots/existing_dashboard_fields.json#L6) is empty and collection targets the wrong dashboard location. Pre-cutover timing/determinism execution unverified. | AUD-033-014 |
| T025 | [X] | SUPERSEDED | Intermediate 501 placeholders are explicitly replaced by [T051](tasks.md#L394). [Six routes](../../apps/api/app/api/routes/workflow_runs.py#L76) are registered in the [API router](../../apps/api/app/api/router.py#L96); current contract completion remains partial. | AUD-033-002, AUD-033-011 |
| T026 | [X] | IMPLEMENTED | [Monitoring definition](../../apps/agents/maf_runtime/agents/monitoring.yaml#L1) has reasoning, existing MonitoringDecisionRecord reference, all middleware and empty tool list. Authored configuration is present; invocation parity is assessed under T027/T036. | AUD-033-004 |
| T027 | [X] | PARTIAL | [Monitoring facade](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L22) uses the shared SDK factory and stdin CLI, but its legacy delegate omits configured LLM/full triage and the MAF input becomes a stringified duck object; isolated audit is not assured. | AUD-033-003, AUD-033-004, AUD-033-008 |
| T028 | [X] | IMPLEMENTED | [Risk definition](../../apps/agents/maf_runtime/agents/risk_assessment.yaml#L1) declares required config/middleware and a real model reference. Business output/consumer parity is not established by that declaration. | AUD-033-004 |
| T029 | [X] | PARTIAL | [Risk facade](../../apps/agents/maf_runtime/agents/risk_assessment_agent.py#L25) manufactures RiskAssessmentDecisionRecord instead of invoking [generate_assessment](../../apps/agents/risk_assessment/agent.py#L76) for HazardAssessment. | AUD-033-004 |
| T030 | [X] | IMPLEMENTED | [Evacuation definition](../../apps/agents/maf_runtime/agents/evacuation.yaml#L1) declares existing EvacuationPlan, required middleware and routing v1. Tool connection/behavior is separately incomplete. | AUD-033-004, AUD-033-012 |
| T031 | [X] | PARTIAL | [Evacuation facade](../../apps/agents/maf_runtime/agents/evacuation_agent.py#L32) returns a minimal plan, does not call [the real pipeline](../../apps/agents/evacuation/agent.py#L123), and discards optional routing results/failures. | AUD-033-004, AUD-033-012 |
| T032 | [X] | IMPLEMENTED | [Resource definition](../../apps/agents/maf_runtime/agents/resource_allocation.yaml#L1) has required config and existing ResourceDeploymentPlan type. Declaration alone does not match resources or preserve legacy output. | AUD-033-004 |
| T033 | [X] | PARTIAL | [Resource facade](../../apps/agents/maf_runtime/agents/resource_allocation_agent.py#L25) creates an ID-only model rather than [processing the handoff](../../apps/agents/resource_allocation/agent.py#L174) through inventory/matching/versioning/audit. | AUD-033-004 |
| T034 | [X] | CONFLICT | [Communication YAML](../../apps/agents/maf_runtime/agents/communication.yaml#L8) creates a new prompt and uses reasoning; [legacy generation](../../apps/agents/communication/translator.py#L117) composes different prompts and uses drafting. FR-024a/no-tier-change is not satisfied. | AUD-033-004 |
| T035 | [X] | PARTIAL | [Communication facade](../../apps/agents/maf_runtime/agents/communication_agent.py#L31) returns a default draft model and retains its TODO. Shared SDK run exists, but real drafting/side-effect assertion and integrated HITL are incomplete. | AUD-033-004, AUD-033-005 |
| T036 | [X] | PARTIAL | [Monitoring test](../../tests/equivalence/test_monitoring_equivalence.py#L24) scores one equal stored [smoke pair](../../tests/equivalence/fixtures/monitoring/smoke-fire-escalate.json#L1). No representative invocation corpus or committed report. | AUD-033-013 |
| T037 | [X] | PARTIAL | [Risk test](../../tests/equivalence/test_risk_assessment_equivalence.py#L14) scores pairs; the risk fixture directory/reports are absent in the scoped inventory, producing empty PASS. | AUD-033-013 |
| T038 | [X] | PARTIAL | [Evacuation test](../../tests/equivalence/test_evacuation_equivalence.py#L14) uses the same empty-pass loader; no evacuation corpus/report or invocation assertion. | AUD-033-013 |
| T039 | [X] | PARTIAL | [Resource test](../../tests/equivalence/test_resource_allocation_equivalence.py#L14) has no representative corpus/report and never runs either behavior owner. | AUD-033-013 |
| T040 | [X] | PARTIAL | [Communication test](../../tests/equivalence/test_communication_equivalence.py#L18) has no draft corpus/report and cannot establish populated-field invariance. | AUD-033-013, AUD-033-004 |
| T040b | [X] | CONFLICT | [Prompt test](../../tests/unit/test_communication_prompt_invariant.py#L47) checks only required tokens and never compares legacy bytes or populated fields. A single-character change retaining tokens need not fail. | AUD-033-004, AUD-033-014 |
| T041 | [X] | PARTIAL | [CI equivalence step](../../.github/workflows/ci.yml#L104) runs the suite but expressly permits zero cases and does not bind representative output/report evidence to a cutover. | AUD-033-013, AUD-033-017 |
| T042 | [X] | PARTIAL | [Shared base](../../apps/agents/maf_runtime/workflow/executors/_base.py#L149) and five thin subclasses exist; no SDK Executor inheritance, shadow MAF call, actual state capture or per-executor three-mode/restore assertion. | AUD-033-003, AUD-033-001 |
| T042b | [X] | PARTIAL | [Validator](../../apps/agents/maf_runtime/workflow/executors/_base.py#L53) and [sample assertions](../../tests/unit/test_executor_base.py#L25) detect missing fields, but actual parser raises first and workflow maps all failures to Failed, not NeedsOperatorDecision/audited schema context. | AUD-033-007 |
| T042c | [X] | PARTIAL | [Retry helper](../../apps/agents/maf_runtime/workflow/executors/_base.py#L88) and [fast retry tests](../../tests/unit/test_executor_base.py#L43) bound attempts for synthetic errors, not a hanging call's total elapsed time or full provider taxonomy/override/state outcomes. | AUD-033-007 |
| T043 | [X] | PARTIAL | [Manual runner](../../apps/agents/maf_runtime/workflow/builder.py#L89) chains five facades and a gate, not WorkflowBuilder. It attempts four checkpoint calls, swallows failure, lacks resume/conditional legacy edges and `--shadow`; normal return is AwaitingApproval, not the claimed Completed with >=6 checkpoints. | AUD-033-001, AUD-033-003, AUD-033-004 |
| T044 | [X] | CONFLICT | [Watchdog](../../apps/agents/maf_runtime/workflow/duration_watchdog.py#L40) follows task last-step timing but conflicts with FR-012c continuous age; no schedule, full scan, elapsed context or exact-boundary/override/alert assertions. | AUD-033-016 |
| T045 | [X] | CONFLICT | [Header](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L1) asserts discovered spec-008 semantics, but [actual request model](../../apps/agents/communication/agent.py#L42) and [broker payload](../../apps/agents/communication/approval.py#L43) differ; contract drift was not reconciled. | AUD-033-005 |
| T046 | [X] | PARTIAL | Accepted gate/listener substitute exists in [HITL module](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L165), but no real decision subscriber, durable lookup, resume/publication or envelope-compatible round trip; [test](../../tests/integration/test_hitl_round_trip.py#L105) checks status only. | AUD-033-005 |
| T047 | [X] | PARTIAL | [Static tests](../../tests/unit/test_send_response_call_sites.py#L31) guard literal references/queue strings only inside MAF, not the entire repo or authorization/publication behavior; SDK name replacement is explicit but security proof remains incomplete. | AUD-033-005, AUD-033-017 |
| T048 | [X] | PARTIAL | [Injected lookup](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L191) and [idempotence test](../../tests/integration/test_hitl_round_trip.py#L75) skip a publish with a supplied decision; no default durable lookup, restore, timer reconciliation or consumed resume result. | AUD-033-001, AUD-033-005 |
| T048b | [X] | PARTIAL | Relocated [sequential decision test](../../tests/integration/test_hitl_round_trip.py#L160) rejects the second already-resolved call; no simultaneous persistent-client interleaving, atomic decision, two-attempt audit or resume-once assertion. | AUD-033-005, AUD-033-006 |
| T048c | [X] | MISSING | [HITL test header](../../tests/integration/test_hitl_round_trip.py#L1) names T048c but contains no timer/escalation assertions. Existing [approval escalation](../../apps/agents/communication/approval.py#L107) is not called by MAF; scoped tests contain no MAF timeout/max-chain case. | AUD-033-005 |
| T049 | [X] | PARTIAL | [Crash test](../../tests/integration/test_workflow_crash_recovery.py#L1) exercises normal pause, two incidents and an exception; no killed process, checkpoint restoration, random boundary or 100-trial accounting. | AUD-033-001, AUD-033-015 |
| T050 | [X] | PARTIAL | [Load test](../../tests/load/test_workflow_capacity.py#L48) is flag-skipped and its full branch runs only five at once without 30/60-minute windows or a 50-run burst. Paths are correct; baseline is placeholder and results absent. | AUD-033-015 |
| T051 | [X] | PARTIAL | [API implementation](../../apps/api/app/api/routes/workflow_runs.py#L77) has list/get/cancel, but histories/metrics are placeholders, auth/tenancy/audit/no-store and strict contracts are missing. [Tests](../../tests/contract/test_workflow_run_api.py#L22) assert only partial shapes. | AUD-033-002, AUD-033-011 |
| T052 | [X] | PARTIAL | [Typed client](../../apps/web/src/lib/api/workflow-runs.ts#L1) implements six fetch functions with no-store; it omits auth/continuation, drops audit correlation and hardcodes a localhost fallback. No full contract/typecheck execution evidence. | AUD-033-002, AUD-033-011 |
| T053 | [X] | PARTIAL | [List](../../apps/web/src/components/workflow/WorkflowRunList.tsx#L29) renders all seven labels/counts; the page never passes selectedStatus, tab semantics/keyboard behavior are incomplete and no focused axe assertion was found. | AUD-033-011 |
| T054 | [X] | PARTIAL | [Detail](../../apps/web/src/components/workflow/WorkflowRunDetail.tsx#L23) renders pause/failure/history scaffolding, but trace ID source and caller wiring are wrong, held context is absent, and four-state/50-checkpoint Storybook/assertion evidence was not found. | AUD-033-011 |
| T055 | [X] | PARTIAL | [Server page](../../apps/web/src/app/operations/workflows/page.tsx#L22) composes list/detail/metrics but ignores state, cannot deep-link beyond the first 100 rows and has no timed refresh; build/runtime evidence is UNVERIFIED. | AUD-033-003, AUD-033-011 |
| T056 | [X] | MISSING | [Workflow test](../../tests/integration/test_workflow_crash_recovery.py#L32) counts commander envelopes, not `alert.published` versus durable decisions. No bidirectional invariant fixture/test found in tests or API tests. Reject decisions also require explicit semantics rather than assuming every decision publishes. | AUD-033-005, AUD-033-017 |
| T056b | [X] | PARTIAL | [Metrics component](../../apps/web/src/components/workflow/ApprovalGateMetrics.tsx#L23) has default 24h and is composed beside detail; all displayed values depend on the unconditional zero API, and no meaningful metrics assertion exists. | AUD-033-010, AUD-033-011 |
| T057 | [X] | PARTIAL | [No-op example](../../tests/integration/no_op_agent/test_no_op_inherits_middleware.py#L27) is a custom toy with manual middleware nesting, no YAML/real factory/SDK Agent and no safety-verdict/trace/schema assertion; no-op name is outside the contracts. | AUD-033-003, AUD-033-008 |
| T058 | [X] | PARTIAL | [Function](../../apps/api/app/api/routes/admin/reconciliation.py#L76) reads env counts and emits a best-effort metric; no source queries, Cosmos report persistence, schedule or real gap/alert test. | AUD-033-010 |
| T059 | [X] | PARTIAL | [Window selector](../../apps/web/src/components/workflow/ApprovalGateMetrics.tsx#L21) switches 1h/24h/7d/30d without reload, but no real historical view/data or four-window numeric assertions support the success clause. | AUD-033-011 |
| T060 | [X] | MISSING | Infra-wide Bicep/JSON/KQL search found no `ai.agent.name`/`workflow.run.state` panels; existing [LLM workbook](../../infra/modules/workbooks/llm-cost.json#L1) is not their replacement. New panels/deployed population are unproved. | AUD-033-010, AUD-033-014 |
| T060b | [X] | PARTIAL | [Regression test](../../tests/contract/test_existing_dashboards_no_regression.py#L28) skips empty baseline and compares query fields, not emitted per-agent data; removing a MAF attribute can remain undetected. | AUD-033-014 |
| T061 | [X] | PARTIAL | [Worked README](../../apps/agents/maf_runtime/middleware/README.md#L1) gives a single-file policy diff; its recommended equivalence suite does not invoke the changed policy, so uniformity/proof-of-example is not established. | AUD-033-008, AUD-033-013 |
| T062 | [X] | PARTIAL | [FastMCP server](../../tools/routing_mcp_server/server.py#L13) and [package](../../tools/routing_mcp_server/pyproject.toml#L5) exist; route/closure tools are explicit stubs, protocol version not bound and startup/package layout compatibility unverified. | AUD-033-012 |
| T063 | [X] | PARTIAL | [Wrapper](../../apps/agents/maf_runtime/mcp/routing_tool.py#L70) handles selected errors but fabricates missing version, probes SDK accessors and accepts any dict. [Tests](../../tests/integration/test_mcp_routing_tool.py#L72) substitute protocol helpers, not actual MCP lifecycle. | AUD-033-012 |
| T064 | [X] | PARTIAL | [Resolver](../../apps/agents/maf_runtime/mcp/allow_list.py#L35) filters repository bound_agents; it does not intersect YAML major pins or bind tools in Agent, and refusal audit is not wired. | AUD-033-008, AUD-033-012 |
| T065 | [X] | CONFLICT | [YAML routing v1](../../apps/agents/maf_runtime/agents/evacuation.yaml#L30) is declarative only; [tool use](../../apps/agents/maf_runtime/agents/evacuation_agent.py#L45) is in legacy mode, discards route and swallows failures; executor has no tool-specific failure handling. | AUD-033-012 |
| T066 | [X] | PARTIAL | [Routing Container App](../../infra/bicep/modules/routing-mcp.bicep#L35) declares internal ingress and identity, but no deployment caller/image build/auth binding found in azure.yaml/infra/workflows. Required what-if result is UNVERIFIED. | AUD-033-012, AUD-033-017 |
| T067 | [X] | UNVERIFIED | [Seeder CLI](../../scripts/register_mcp_tool.py#L18) exists and can print a memory-only registration; no executed seed/document evidence proves the required durable row or resolver result. | AUD-033-012, AUD-033-017 |
| T068 | [X] | PARTIAL | [Alert module](../../infra/bicep/modules/maf-tool-alerts.bicep#L23) has a five-minute query/action-group parameter but no deployment caller or matching structured emitter was found; actual alert/on-call delivery is UNVERIFIED. | AUD-033-010, AUD-033-012 |
| T069 | [X] | PARTIAL | Relocated [playbook](../../docs/corpus/aidr/runbooks/maf-cutover-playbook.md#L1) covers shadow/maf/rollback and report/load prerequisites; no independent rehearsal/co-signed PR evidence and current gates/runtime do not support it. | AUD-033-003, AUD-033-015, AUD-033-017 |
| T070 | [X] | PARTIAL | Relocated [rollback guide](../../docs/corpus/aidr/runbooks/maf-rollback.md#L1) exists, but real legacy dispatch and measured <5-minute rollback are not established. | AUD-033-003, AUD-033-004, AUD-033-017 |
| T071 | [X] | UNVERIFIED | [Baseline](../../tests/load/baselines/legacy_baseline.json#L4) explicitly states never captured; [script](../../scripts/capture_legacy_baseline.sh#L15) emits constants instead of a 60-minute workload. Authored numbers are not performance evidence. | AUD-033-015 |
| T072 | [X] | IMPLEMENTED | [Handoff docstring](../../apps/agents/common/handoffs.py#L1) is deprecated with builder/playbook pointers; functions remain. This is banner/preservation evidence, not proof that workflow edges supersede them operationally. | AUD-033-003, AUD-033-004 |
| T073 | [X] | UNVERIFIED | [Quickstart](quickstart.md#L1) has no Last Validated record; named fixtures/script and CLI flags drift. No nine-section dev execution record exists in the local feature inventory. | AUD-033-017 |
| T074 | [X] | PARTIAL | Reports directory contains gitkeep; [root ignore file](../../.gitignore#L1) has no required equivalence `*.json` exclusion. No tracked Markdown reports were found. | AUD-033-017 |
| T074b | [X] | PARTIAL | [AST gate](../../tests/unit/test_maf_runtime_error_imports.py#L23) detects direct/named Exception subclasses, but not raw raised built-ins/SDK normalization or aliases, and MAF unit guards are absent from main CI discovery. | AUD-033-007, AUD-033-017 |
| T075 | [X] | UNVERIFIED | [CI source](../../.github/workflows/ci.yml#L131) runs a narrower suite and advisory typing; no local full lint/test/equivalence/dev-capacity run artifact establishes this task. This audit ran none of those commands. | AUD-033-015, AUD-033-017 |
| T076 | [X] | UNVERIFIED | [Analyze task](tasks.md#L562) is checked, but no local analyze report, zero-High result or justified Medium acceptance was found. Contradictions listed in this report remain unresolved. | AUD-033-017 |

## Requirement And Success-Criterion Coverage

There are no separately numbered NFRs. The capacity, latency, retention, security, resilience,
accessibility and operational obligations remain covered here and in the design/contract ledgers.

| Requirement | Status | Implementation/test evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Requirement](spec.md#L109); five facades share [SDK Agent construction](../../apps/agents/maf_runtime/agents/_factory.py#L90), but the deployed dispatcher does not route to them and legacy delegates are not equivalent behavior owners. | AUD-033-003, AUD-033-004 |
| FR-002 | PARTIAL | [Requirement](spec.md#L110); [definition loader](../../apps/agents/maf_runtime/agents/_factory.py#L45) reads prompts/tier/schema and requires safety/audit names, but omits full validation/tool binding and hardcodes the middleware set. | AUD-033-003, AUD-033-004, AUD-033-012 |
| FR-003 | PARTIAL | [Requirement](spec.md#L111); [Pydantic parse](../../apps/agents/maf_runtime/agents/_factory.py#L281) and [executor validation](../../apps/agents/maf_runtime/workflow/executors/_base.py#L53) exist; business schemas/consumer mapping and typed malformed-output routing remain incomplete. | AUD-033-004, AUD-033-007 |
| FR-004 | PARTIAL | [Requirement](spec.md#L112); [hierarchy/tests](../../tests/unit/test_maf_runtime_errors.py#L52) are substantive but client/config/parser/SDK failures do not all flow through that hierarchy or retain the workflow correlation. | AUD-033-007 |
| FR-005 | PARTIAL | [Requirement](spec.md#L113); [stdin facade CLI](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L51) allows isolated calls, but default legacy does not prove real MAF, expected fixture interface or isolated audit contract. | AUD-033-003, AUD-033-004, AUD-033-008 |
| FR-006 | PARTIAL | [Requirement](spec.md#L117); [runner](../../apps/agents/maf_runtime/workflow/builder.py#L89) orders steps and tries checkpoints; no SDK workflow, correct persisted state, durability barrier or pending-HITL checkpoint. | AUD-033-001, AUD-033-003 |
| FR-007 | MISSING | [Requirement](spec.md#L118); no restore/resume caller in scoped source; [CLI](../../apps/agents/maf_runtime/workflow/builder.py#L244) creates new runs and offers no resume flag. [Crash test](../../tests/integration/test_workflow_crash_recovery.py#L1) contains no restart. | AUD-033-001, AUD-033-015 |
| FR-008 | PARTIAL | [Requirement](spec.md#L119); [gate](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L199) sets AwaitingApproval and sends a request, but no authenticated durable decision-to-publication path establishes non-bypassability. | AUD-033-005 |
| FR-009 | CONFLICT | [Requirement](spec.md#L120); [listener](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L245) does not verify or persist authority/decision/time/modification and does not delegate to [existing approval](../../apps/agents/communication/approval.py#L152). Modify semantics/envelopes disagree. | AUD-033-005 |
| FR-010 | MISSING | [Requirement](spec.md#L121); existing [timer/escalation](../../apps/agents/communication/approval.py#L89) is unconnected to the MAF gate and its tests contain no MAF timeout/chain/max/never-auto-approve assertions. | AUD-033-005 |
| FR-011 | PARTIAL | [Requirement](spec.md#L122); [API](../../apps/api/app/api/routes/workflow_runs.py#L77) lists/gets records, but history is empty, progress fields stale, access unscoped and UI filtering/refresh incomplete. | AUD-033-002, AUD-033-006, AUD-033-011 |
| FR-011a | CONFLICT | [Requirement](spec.md#L123); [repository](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L110) is non-atomic, prior linkage optional, and inactive-but-resumable NeedsOperatorDecision permits a successor despite the terminal-only rule. | AUD-033-006 |
| FR-011b | PARTIAL | [Requirement](spec.md#L124); [enum/matrix](../../apps/agents/maf_runtime/workflow/run_state.py#L26) matches seven names, but append-only transition history, meaningful held context and working operator state filters are absent. | AUD-033-006, AUD-033-007, AUD-033-011 |
| FR-012 | PARTIAL | [Requirement](spec.md#L125); [budget](../../apps/agents/maf_runtime/workflow/executors/_base.py#L88) counts attempts but does not time-bound an awaited call; provider failures can bypass classification and state/audit context. | AUD-033-007 |
| FR-012a | CONFLICT | [Requirement](spec.md#L126); [positive checkpoint TTL](../../infra/bicep/modules/cosmos-workflow.bicep#L60), [uncalled terminal helper](../../apps/agents/maf_runtime/checkpoint/retention.py#L41), mismatched database and ineffective audit-role/policy chain contradict automatic independent retention. | AUD-033-001, AUD-033-009 |
| FR-012b | UNVERIFIED | [Requirement](spec.md#L127); [load source](../../tests/load/test_workflow_capacity.py#L59) does not implement the required sustained/burst windows; no capacity evidence or per-environment gate result exists. | AUD-033-015 |
| FR-012c | CONFLICT | [Requirement](spec.md#L128); [watchdog](../../apps/agents/maf_runtime/workflow/duration_watchdog.py#L40) uses idle-since-step age rather than continuous run age, lacks schedule/full pagination and elapsed-context alert. | AUD-033-016 |
| FR-013 | PARTIAL | [Requirement](spec.md#L132); [safety middleware](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L63) applies on SDK calls but the actual legacy/mixed/inactive production paths do not inherit an unavoidable audited safety boundary. | AUD-033-003, AUD-033-008 |
| FR-014 | PARTIAL | [Requirement](spec.md#L133); [audit process](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L173) fingerprints and writes finally, but early rejection bypasses it, default IDs violate schema, storage failures drop entries and immutability is not enforced. | AUD-033-008, AUD-033-009 |
| FR-015 | PARTIAL | [Requirement](spec.md#L134); [shared factory](../../apps/agents/maf_runtime/agents/_factory.py#L81) centralizes declarations; [sixth-agent test](../../tests/integration/no_op_agent/test_no_op_inherits_middleware.py#L62) manually wires a different path and cannot prove inheritance. | AUD-033-003, AUD-033-008 |
| FR-016 | PARTIAL | [Requirement](spec.md#L135); [OTel wrapper](../../apps/agents/maf_runtime/middleware/otel_middleware.py#L44) creates spans, but actual run/parent propagation, model/token attributes, latency metrics/logs and startup wiring are not established. | AUD-033-010 |
| FR-017 | PARTIAL | [Requirement](spec.md#L136); [regression check](../../tests/contract/test_existing_dashboards_no_regression.py#L28) skips an empty snapshot and does not inspect per-agent emitted fields; existing telemetry queries are outside capture scope. | AUD-033-010, AUD-033-014 |
| FR-018 | PARTIAL | [Requirement](spec.md#L140); [SDK tool construction](../../apps/agents/maf_runtime/mcp/routing_tool.py#L63) and FastMCP scaffold exist, but real discovery/invocation, agent binding and real routing are not connected. | AUD-033-012 |
| FR-019 | PARTIAL | [Requirement](spec.md#L141); [bound-agent filtering](../../apps/agents/maf_runtime/mcp/allow_list.py#L35) exists, but definition allow-list is not consumed and enforcement/audit is only in an optional routing wrapper. | AUD-033-012 |
| FR-019a | PARTIAL | [Requirement](spec.md#L142); [version check](../../apps/agents/maf_runtime/mcp/routing_tool.py#L70) compares an integer prefix but guesses v1 on missing discovery, ignores YAML major selection, and lacks additive-contract/actual alert assertions. | AUD-033-012 |
| FR-020 | MISSING | [Requirement](spec.md#L143); [audit context](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L50) allocates an empty tool list with no invocation producer/append path found; tool calls have hardcoded correlation strings and no linked spans/audits. | AUD-033-008, AUD-033-010, AUD-033-012 |
| FR-021 | PARTIAL | [Requirement](spec.md#L144); [typed timeout/unreachable checks](../../apps/agents/maf_runtime/mcp/routing_tool.py#L111) cover selected errors, not valid structured MCP results; evacuation swallows failures and server fabricates mock routes. | AUD-033-012 |
| FR-022 | PARTIAL | [Requirement](spec.md#L148); [mode dispatch](../../apps/agents/maf_runtime/workflow/executors/_base.py#L214) exists, but actual traffic is unconnected, shadow does not call MAF and fallbacks do not preserve real legacy behavior. ADR 20 does not retire this runtime migration requirement. | AUD-033-003, AUD-033-004 |
| FR-023 | PARTIAL | [Requirement](spec.md#L149); [runner/scorer](../../apps/agents/maf_runtime/equivalence/runner.py#L31) compare stored pairs with empty PASS, not representative real invocations or exact schema-valid populated paths. | AUD-033-013 |
| FR-024 | PARTIAL | [Requirement](spec.md#L150); [field test](../../tests/contract/test_audit_telemetry_fields_no_regression.py#L28) snapshots declarations/new schema, not all old and new emitted fields; operator errors, approval envelope and business-output contracts drift. | AUD-033-004, AUD-033-005, AUD-033-011, AUD-033-014 |
| FR-024a | CONFLICT | [Requirement](spec.md#L151); [new prompt](../../apps/agents/maf_runtime/agents/communication.yaml#L8) and [keyword test](../../tests/unit/test_communication_prompt_invariant.py#L47) do not enforce unchanged legacy bytes or populated output fields. | AUD-033-004, AUD-033-014 |
| FR-025 | PARTIAL | [Requirement](spec.md#L152); [chat credential](../../apps/agents/maf_runtime/chat_client.py#L42), Cosmos and Service Bus constructors use managed-identity-compatible credentials. MCP client/server auth is not wired; inherited [local safety key path](../../apps/agents/common/content_safety.py#L73) remains an exception to the strict wording, not proof of a newly introduced production key. Deployed identity state is UNVERIFIED. | AUD-033-009, AUD-033-012, AUD-033-017 |
| FR-026 | PARTIAL | [Requirement](spec.md#L153); [flags](../../apps/agents/maf_runtime/feature_flags.py#L46) and [rollback guide](../../docs/corpus/aidr/runbooks/maf-rollback.md#L1) exist, but active runtime disable/real per-agent legacy rollback is not connected or proved. | AUD-033-003, AUD-033-004, AUD-033-017 |
| SC-001 | UNVERIFIED | [Criterion](spec.md#L169); five definitions/facades exist but [image/startup](../../apps/agents/Dockerfile#L4) excludes MAF and no reviewed artifact proves all five run on it. Retained legacy code/docstrings are not cutover evidence. | AUD-033-003, AUD-033-004, AUD-033-017 |
| SC-002 | UNVERIFIED | [Criterion](spec.md#L170); [crash-test assertions](../../tests/integration/test_workflow_crash_recovery.py#L32) do not execute restore or 100 fault trials; no measured >=99/100 result exists. | AUD-033-001, AUD-033-015 |
| SC-003 | UNVERIFIED | [Criterion](spec.md#L171); no continuous publication-to-decision reconciliation fixture/run evidence. [Approval-envelope count](../../tests/integration/test_workflow_crash_recovery.py#L32) is not proof of zero unapproved public alerts. | AUD-033-005, AUD-033-017 |
| SC-004 | UNVERIFIED | [Criterion](spec.md#L172); [reconciliation](../../apps/api/app/api/routes/admin/reconciliation.py#L76) defaults to env zeros, has no schedule/persistence/real queries and cannot establish 100% audit/trace coverage. | AUD-033-008, AUD-033-010 |
| SC-005 | PARTIAL | [Criterion](spec.md#L173); [worked single-file diff](../../apps/agents/maf_runtime/middleware/README.md#L9) is authored but the recommended equivalence test never invokes the policy, and no completed uniformity demonstration exists. | AUD-033-008, AUD-033-013 |
| SC-006 | PARTIAL | [Criterion](spec.md#L174); [MCP wrapper](../../apps/agents/maf_runtime/mcp/routing_tool.py#L35) is not bound to SDK Agent tools, the server uses mocks and no real authenticated routing-consumption evidence exists. | AUD-033-012 |
| SC-007 | UNVERIFIED | [Criterion](spec.md#L175); [baseline](../../tests/load/baselines/legacy_baseline.json#L4) explicitly is not captured; load profile is insufficient and no measured <=10% result at 25 sustained exists. | AUD-033-015 |
| SC-008 | PARTIAL | [Criterion](spec.md#L176); [metrics UI](../../apps/web/src/components/workflow/ApprovalGateMetrics.tsx#L23) exists, but data is hardcoded zero and [page](../../apps/web/src/app/operations/workflows/page.tsx#L27) has no automatic paused-state refresh/10-second proof. | AUD-033-010, AUD-033-011 |
| SC-009 | UNVERIFIED | [Criterion](spec.md#L177); [empty baseline](../../tests/contract/snapshots/existing_dashboard_fields.json#L6) and source-only query comparison cannot prove dashboard rendering/no field gaps after any agent cutover. | AUD-033-010, AUD-033-014 |
| SC-010 | PARTIAL | [Criterion](spec.md#L178); [toy no-op](../../tests/integration/no_op_agent/test_no_op_inherits_middleware.py#L27) has no Agent Definition YAML and bypasses the real factory; new-agent enum/metadata/schema constraints remain unresolved. | AUD-033-003, AUD-033-008 |

## Acceptance Scenarios

`USn-m` are report labels for story n's original scenario m, not new original requirement IDs.
The four independent-test narratives are included in the corresponding scenario and outcome coverage.

| Scenario | Status | Expected outcome and actual evidence | Follow-up |
| --- | --- | --- | --- |
| US1-1 | PARTIAL | [Signal-to-triage equivalence](spec.md#L33): [facade](../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25) only summarizes/builds a handoff; one stored equal pair is not new-surface legacy equivalence. | AUD-033-004, AUD-033-013 |
| US1-2 | PARTIAL | [Repeated invocation equivalence/audit structure](spec.md#L34): scorer excludes free-text values but does not run either agent; audit identity/context is missing on actual calls. | AUD-033-004, AUD-033-008, AUD-033-013 |
| US1-3 | PARTIAL | [Uniform outage error](spec.md#L35): canonical classes exist, but [raw SDK/parse call](../../apps/agents/maf_runtime/agents/_factory.py#L265) has no comprehensive typed/correlated mapping and early errors can bypass audit. | AUD-033-007, AUD-033-008 |
| US1-4 | PARTIAL | [Per-agent configuration change](spec.md#L36): YAML prompt/tier is consumed centrally, but real legacy behavior, output schema and tools are not preserved by configuration alone. | AUD-033-003, AUD-033-004, AUD-033-012 |
| US2-1 | MISSING | [Crash after risk, no re-execution](spec.md#L50): no actual restart/restore path; [test](../../tests/integration/test_workflow_crash_recovery.py#L1) only covers manual-run happy/failure cases. | AUD-033-001, AUD-033-015 |
| US2-2 | PARTIAL | [Draft pauses/notifies/no public output](spec.md#L51): [gate](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L199) changes state/sends an envelope, but real commander chain, durable pause and authorized publication are not integrated. | AUD-033-005 |
| US2-3 | PARTIAL | [Approve/modify/reject audit and elapsed time](spec.md#L52): [listener](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L245) accepts dicts and changes status, without durable authority/modification/time record, measured dwell or completion. | AUD-033-005, AUD-033-010 |
| US2-4 | MISSING | [Timeout escalation without auto-approval](spec.md#L53): [existing timer](../../apps/agents/communication/approval.py#L89) is not invoked from the MAF path; named T048c header has no timeout assertions. | AUD-033-005 |
| US2-5 | PARTIAL | [Bounded retries and inspectable failure](spec.md#L54): [budget](../../apps/agents/maf_runtime/workflow/executors/_base.py#L88) has no hard elapsed cap; generic failure/unfinished API hide step-specific and schema context. | AUD-033-006, AUD-033-007, AUD-033-011 |
| US3-1 | PARTIAL | [Every invocation immutable required-field audit](spec.md#L68): [audit middleware](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L173) exists but pre-audit safety failures, invalid isolated run IDs and dropped storage errors create gaps. | AUD-033-008, AUD-033-009 |
| US3-2 | PARTIAL | [Safety blocks before business logic and audits](spec.md#L69): [safety raise](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L63) blocks business logic but precedes the audit layer in the actual factory chain. | AUD-033-008 |
| US3-3 | PARTIAL | [Consistent service-outage degradation](spec.md#L70): [validator](../../apps/agents/common/content_safety.py#L106) reuses circuit-breaker keyword fallback; MAF drops its review/verdict details and does not prove behavior across all agent modes. | AUD-033-008 |
| US3-4 | PARTIAL | [Per-step span metadata and parent](spec.md#L71): [span wrapper](../../apps/agents/maf_runtime/middleware/otel_middleware.py#L44) lacks supplied workflow context and verified model/token/latency fields. | AUD-033-010 |
| US3-5 | UNVERIFIED | [Complete agent/workflow dashboard traces](spec.md#L72): no deployed evidence and [regression test](../../tests/contract/test_existing_dashboards_no_regression.py#L28) skips the empty baseline. | AUD-033-010, AUD-033-014 |
| US4-1 | PARTIAL | [Structured tool result with shared audit/telemetry](spec.md#L86): [client](../../apps/agents/maf_runtime/mcp/routing_tool.py#L111) validates only dict-ness; no agent tool binding or populated invocation audit list. | AUD-033-008, AUD-033-012 |
| US4-2 | PARTIAL | [Bounded typed unreachable failure and uniform policy](spec.md#L87): helper-level timeout tests use substituted functions; [evacuation fallback](../../apps/agents/maf_runtime/agents/evacuation_agent.py#L45) discards ToolFailure rather than applying a surfaced policy. | AUD-033-007, AUD-033-012 |
| US4-3 | PARTIAL | [Tool-only additive discovery within allow-list](spec.md#L88): no actual discovery/additive compatibility test; [version fallback](../../apps/agents/maf_runtime/mcp/routing_tool.py#L151) can invent v1 and first-name lookup ignores the YAML pin. | AUD-033-012 |

## Edge Cases

`EC-01` through `EC-08` are audit labels in the original bullet order.

| Edge case | Status | Expected/observed evidence | Follow-up |
| --- | --- | --- | --- |
| EC-01 | MISSING | [Crash while HITL-paused](spec.md#L94): stable UUIDv5 is implemented, but no pending-request checkpoint/restore, original timer reconciliation, durable decision lookup or duplicate-notification test is connected. | AUD-033-001, AUD-033-005 |
| EC-02 | PARTIAL | [Simultaneous commanders](spec.md#L95): [sequential conflict assertion](../../tests/integration/test_hitl_round_trip.py#L160) cannot prove concurrent first-write-wins; repository lacks CAS and both attempts are not audited. | AUD-033-005, AUD-033-006 |
| EC-03 | CONFLICT | [Checkpoint store unavailable](spec.md#L96): [builder](../../apps/agents/maf_runtime/workflow/builder.py#L186) deliberately suppresses the error and continues; initializer can choose memory. | AUD-033-001 |
| EC-04 | PARTIAL | [Telemetry pipeline unavailable](spec.md#L97): [bootstrap](../../apps/agents/maf_runtime/observability.py#L27) and attribute writes tolerate failures, but no full exporter/span-start/end failure assertion proves unchanged agent correctness. | AUD-033-010 |
| EC-05 | PARTIAL | [Malformed MCP response](spec.md#L98): [client](../../apps/agents/maf_runtime/mcp/routing_tool.py#L111) rejects non-dict only; invalid dict fields/envelopes and SDK errors are not covered; failure audit is absent. | AUD-033-012 |
| EC-06 | MISSING | [Safety rejects pending alert](spec.md#L99): [middleware](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L79) sets metadata but no caller consumes it to reject/cancel with reason and notify the commander. | AUD-033-005, AUD-033-008 |
| EC-07 | CONFLICT | [Maximum continuous run duration](spec.md#L100): [watchdog](../../apps/agents/maf_runtime/workflow/duration_watchdog.py#L40) uses last-step idle time and is not scheduled; elapsed-duration/last-completed-step context is missing. | AUD-033-016 |
| EC-08 | PARTIAL | [Output schema changes](spec.md#L101): [helper](../../apps/agents/maf_runtime/workflow/executors/_base.py#L53) exists, but actual parser exceptions and generic workflow catch do not provide the required contract violation/NeedsOperatorDecision/audit path. | AUD-033-007 |

## Contracts And Data Model

All seven contracts and every data-model entity/validation section were read in full. This ledger
includes unnumbered wire constraints, not only the FR labels printed on the contracts.

| Contract/entity | Status | Assessment of fields, invariants and consumers | Follow-up |
| --- | --- | --- | --- |
| Agent Definition | PARTIAL | [Schema](contracts/agent-definition.schema.yaml#L1), [entity](data-model.md#L11), [loader](../../apps/agents/maf_runtime/agents/_factory.py#L45): all five YAMLs supply required fields and actual Pydantic references; loader verifies selected presence/name/safety-audit bindings, not full enum/types/unique tool pins/additionalProperties. The declared tool list is not consumed, and the closed five-name enums conflict with the sixth-agent proof. | AUD-033-003, AUD-033-004, AUD-033-008, AUD-033-012 |
| Workflow Run | CONFLICT | [Schema](contracts/workflow-run.schema.json#L1), [entity/transitions](data-model.md#L40), [repository](../../apps/agents/maf_runtime/repositories/workflow_run_repository.py#L76): id/run_id UUID aliases, tenant, timestamps, current step and optional links are created. Active ownership excludes a resumable held state; terminal-only successor rule is not enforced, prior_run_id is optional, updates lack conditional history, current_step/last_checkpoint_id are not advanced, and Failed can lack context. Schema only permits failure_reason on Failed, conflicting with T021's Cancelled reason and meaningful NeedsOperatorDecision context; data-model calls it string while schema declares object. Raw SDK/Cosmos metadata is not adapted to additionalProperties=false. | AUD-033-001, AUD-033-002, AUD-033-006, AUD-033-007, AUD-033-017 |
| Checkpoint | CONFLICT | [Schema](contracts/checkpoint.schema.json#L1), [entity](data-model.md#L131), [factory](../../apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py#L61): contract requires UUID id/run_id, per-run unique monotonic sequence, step, object-valued executor state, constrained pending requests and taken_at. Inspected SDK uses workflow_name/graph signature/state/messages/timestamp and save/load methods. Builder constructs neither the declared application contract nor the local SDK contract correctly; pending pause, history links, restore and terminal retention are absent. Accepted SDK replacement needs an explicit compatible storage/API schema decision, not silent drift. | AUD-033-001, AUD-033-009 |
| Audit Entry | PARTIAL | [Schema](contracts/audit-entry.schema.json#L1), [entity](data-model.md#L177), [writer](../../apps/agents/maf_runtime/middleware/audit_middleware.py#L173): timestamps, model tier, fingerprints, outcomes and optional failure/tool fields are authored. Missing context yields isolated/non-UUID run IDs, unrelated correlation and empty tool lists; no-op lies outside name enum, early safety failures escape and writes can be dropped. Required immutability, retention, real model identity and parent linkage remain unproved. Keeping approver identity in the existing approval record is correct design only if that record is actually integrated. | AUD-033-005, AUD-033-008, AUD-033-009, AUD-033-010 |
| Tool Registration | PARTIAL | [Schema](contracts/tool-registration.schema.json#L1), [entity](data-model.md#L209), [repository](../../apps/agents/maf_runtime/repositories/tool_registration_repository.py#L67): composite IDs, major, URL, bound_agents, description and registration timestamps/actor are created; sequential duplicate refusal is tested. URI/name/major/agent uniqueness and real actor are not enforced, lookup failures are treated as absent, multiple bound majors are ambiguous and actual advertised-semver/additive compatibility is not validated. CLI default actor `cli` and memory-only success do not prove a durable authorized seed. | AUD-033-009, AUD-033-012 |
| Operator REST API | PARTIAL | [Contract](contracts/workflow-runs.api.md#L1), [router](../../apps/api/app/api/routes/workflow_runs.py#L77): all six endpoints are registered and some limits/windows checked. Repeatable status exists, but multistatus pages lose continuation/order; tenant claims, read/cancel groups, no-store and mutation audit are not enforced. Checkpoints/audit/metrics return placeholders, unknown history runs are not checked, reason is discarded, and errors use the existing camel-case middleware envelope rather than the contract's snake-case envelope. Resolve compatibility explicitly rather than breaking established consumers. | AUD-033-002, AUD-033-006, AUD-033-010, AUD-033-011, AUD-033-014 |
| HITL Envelope / Approval Decision | CONFLICT | [Envelope](contracts/hitl-request.envelope.md#L1), [entity](data-model.md#L156), [real approval](../../apps/agents/communication/approval.py#L43): custom gate replacement is explicit, but alert message/tier/channels/languages/incident and metadata mapping do not match the real existing payload. Authenticated queue provenance, recorded identity/time/modifications, durable subscriber/lookup, resume, approved publication, original-deadline reconciliation and both-attempt audit are missing. Existing modify requires renewed pending review; request and broker dedup assumptions conflict. Literal send_response naming is superseded, its non-bypassable authority requirement is not. | AUD-033-001, AUD-033-005, AUD-033-006, AUD-033-008 |
| Telemetry Span / Entity Links | PARTIAL | [Span entity](data-model.md#L234) and [relationships](data-model.md#L259) require run-to-prior, checkpoint, pending approval, audit, trace and tool-registration links. Current middleware creates a span but does not establish those full relationships or every ai.agent/model/token/tool attribute; no real daily reconciliation or verified dashboard consumer chain exists. | AUD-033-001, AUD-033-005, AUD-033-010, AUD-033-012, AUD-033-014 |

## Clarifications And Unnumbered Constraints

The labels in this section are audit-only labels for the original prose obligations. They do not add
new product scope. All performance statements remain unverified until measured; source existence is
not proof of regional placement, identity roles, external approvals or production state.

| Item | Status | Original obligation and assessment | Follow-up |
| --- | --- | --- | --- |
| Q1 | CONFLICT | [Clarification](spec.md#L12): one active run, re-escalation only after closure, all runs preserved. Non-atomic create and held-run/successor conflict; prior linkage and immutable transition history incomplete. | AUD-033-006 |
| Q2 | PARTIAL | [Clarification](spec.md#L13): exactly seven operator-visible states. Enum exists; history/context/state filtering do not meet the full operator contract. | AUD-033-006, AUD-033-011 |
| Q3 | CONFLICT | [Clarification](spec.md#L14): 30-day checkpoint and seven-year online audit policies independent. Actual TTL/config/permission/schedule chain does not enforce those policies. | AUD-033-001, AUD-033-009 |
| Q4 | CONFLICT | [Clarification](spec.md#L15): inherit spec-008 identity and authority unchanged. Bridge does not use its actual approval workflow/schema and admits unproven decision dicts. | AUD-033-005 |
| Q5 | PARTIAL | [Clarification](spec.md#L16): >=95% categorical and 100% schema equality, free text excluded. Current one-way shallow/empty-pair scoring does not implement that gate. | AUD-033-013 |
| Q6 | UNVERIFIED | [Clarification](spec.md#L17): 25 sustained/50 burst without recovery/latency regression. No conforming load or fault measurement evidence. | AUD-033-015 |
| Q7 | PARTIAL | [Clarification](spec.md#L18): major-version tool pins with additive-only minor evolution. First-name lookup, guessed version and missing actual discovery/compatibility tests undermine it. | AUD-033-012 |
| Q8 | CONFLICT | [Clarification](spec.md#L19): configurable 72-hour run cap to NeedsOperatorDecision. Code measures idle step age, is unscheduled and omits useful elapsed context. | AUD-033-016 |
| A1 | PARTIAL | [Assumption](spec.md#L182): preserve managed identity/no API-key fallback for services. Constructors support managed identity but MCP caller auth is absent and inherited local content-safety key behavior needs an explicit boundary; no cloud auth state inspected. | AUD-033-009, AUD-033-012, AUD-033-017 |
| A2 | PARTIAL | [Assumption](spec.md#L183): Cosmos remains durable store. Chosen backend agrees, but active configuration/document/partition/durability mismatch prevents proving usable storage. | AUD-033-001, AUD-033-009 |
| A3 | CONFLICT | [Assumption](spec.md#L184): existing AIIMS chain/store establishes approver identity. Actual source/store/queue declarations differ from the assumed envelope and no listener delegates to the real workflow. | AUD-033-005 |
| A4 | PARTIAL | [Assumption](spec.md#L185): reuse existing OTel-to-Insights, not a parallel stack. Existing exporter is selected, but MAF setup and actual trace/metric/query links are not connected. | AUD-033-010 |
| A5 | PARTIAL | [Assumption](spec.md#L186): mixed migrated/legacy workflow under feature flags. Helpers exist but production composition, true shadow and real rollback delegates do not. | AUD-033-003, AUD-033-004 |
| A6 | PARTIAL | [Assumption](spec.md#L187): source corpora from existing tests plus spec-025. Only one invented stored pair exists, not referenced representative inputs replayed through the agents. | AUD-033-013 |
| A7 | PARTIAL | [Assumption](spec.md#L188): routing is the first required separate tool; additional tools are optional. First-tool code exists but uses stubs and is not wired; no extra tool scope is proposed by this audit. | AUD-033-012 |
| OOS1 | CONFLICT | [No new capabilities/prompts/output decisions](spec.md#L192): facade records/default plans and new warning prompt/tier do not preserve legacy decision logic. | AUD-033-004 |
| OOS2 | PARTIAL | [No provider/tier replacement](spec.md#L193): chat-plane choice is explicitly superseded by ADR 20, not by this audit. Existing selections still must be preserved; communication reasoning differs from legacy drafting and needs resolution. | AUD-033-004, AUD-033-017 |
| OOS3 | CONFLICT | [No AIIMS semantics change](spec.md#L194): modification/reapproval and inferred approval-envelope assumptions disagree with the real owner. Repair integration, not a new authority model. | AUD-033-005 |
| OOS4 | PARTIAL | [No audit/telemetry replatform](spec.md#L195): Cosmos/Insights choice retained; wrong database/config and absent enforcement must be repaired within existing services. | AUD-033-009, AUD-033-010 |
| OOS5 | IMPLEMENTED | [No workflow designer](spec.md#L196): inspected web code is operator read/manage UI, not a low-code authoring product. | none |
| OOS6 | IMPLEMENTED | [Only five named agents migrated](spec.md#L197): the examined new factory targets those names; sixth agent is a required test proof, not permission to migrate planning/incident-management. No unrelated agent changes proposed. | none |
| DEP1 | CONFLICT | [Spec-008 dependency](spec.md#L201): source-read approval owner is not the envelope/decision-store bridge the plan assumes. Existing authority must remain authoritative. | AUD-033-005 |
| DEP2 | PARTIAL | [Spec-025 fixtures](spec.md#L202): repository fixture reuse is required, but equivalence runner only reads paired outputs and its corpus lacks those references. | AUD-033-013 |
| DEP3 | CONFLICT | [Spec-029 rollout mechanism](spec.md#L203): CODEOWNERS explicitly records its retirement by spec 031. Reconcile the dependency with current CI/CD while retaining spec-033 behavior/evidence controls; no blanket waiver found. | AUD-033-003, AUD-033-009, AUD-033-017 |
| DEP4 | PARTIAL | [Existing OTel pipeline](spec.md#L204): exporter code exists but new startup/parent linkage/data queries are unconnected. | AUD-033-010 |
| DEP5 | UNVERIFIED | [Existing Entra configuration](spec.md#L205): static constructors/templates inspected; actual subscriptions, roles, token audiences and deployment identity state were not queried. | AUD-033-009, AUD-033-012, AUD-033-017 |
| DEP6 | UNVERIFIED | [Available Cosmos account](spec.md#L206): active template references the existing account and database; real provisioning/reachability/retention state unqueried. | AUD-033-001, AUD-033-009, AUD-033-017 |
| P1 | PARTIAL | [AU workload/storage/telemetry sovereignty](plan.md#L60): main location restricts AU East and tool modules allow the AU pair. Actual state and named model carve-out enforcement/approvals are UNVERIFIED; raw shadow artifacts require explicit privacy/retention control. | AUD-033-008, AUD-033-009, AUD-033-017 |
| P2 | PARTIAL | [Managed identity for every dependency](plan.md#L62): SDK constructor support is not complete authorization; MCP inbound/outbound auth and effective audit role scope are incomplete. | AUD-033-009, AUD-033-012 |
| P3 | CONFLICT | [Delegate identity/authorization](plan.md#L63): metadata wrapping alone does not delegate to the real approval authority. | AUD-033-005 |
| P4 | PARTIAL | [Client-side checkpointable agent state](plan.md#L64): chosen OpenAIChatClient is real and the no-server-session choice is recorded, but Agent sessions/state are not captured by an actual workflow. Endpoint pivot is explicitly documented separately. | AUD-033-001, AUD-033-003 |
| P5 | PARTIAL | [Equivalence-gated per-agent cutover](plan.md#L65): CI is wired to an empty-pass comparison, not invocation evidence. | AUD-033-013 |
| P6 | PARTIAL | [No extra/intermediate operator states](plan.md#L66): enum matches, but durable transitions, held state, context and UI semantics are incomplete. | AUD-033-006, AUD-033-011 |
| P7 | CONFLICT | [Repository-enforced transactional uniqueness](plan.md#L67): current create is query-plus-insert and same-state update can conceal a racing decision. | AUD-033-006 |
| P8 | UNVERIFIED | [Scale/performance/storage estimates](plan.md#L69): five agents/one graph/one tool are intended topology; steps/incidents/day/checkpoint counts/storage horizon are estimates, not observed capacity or retention evidence. | AUD-033-001, AUD-033-009, AUD-033-015 |
| P9 | PARTIAL | [Three-runtimes/project layout](plan.md#L12): monorepo/API/web/agents layout exists; current images/startup do not deploy MAF. Expected Python/Next tooling presence is declaration evidence, not completed build/import verification. | AUD-033-003, AUD-033-017 |
| P10 | UNVERIFIED | [Agent-context update](plan.md#L278): planning names an update-agent-context action, but no local execution record establishes it; not run by this review. | AUD-033-017 |
| P11 | PARTIAL | [Bicep rules](../../.github/instructions/bicep-code-best-practices.instructions.md#L1) and [policy rules](../../.github/instructions/bicep-policy-compliance.instructions.md#L1): spec modules use raw declarations; AVM availability/approved exceptions and target-policy compliance are not established by this audit. No resource generation, policy discovery or approval request occurred. | AUD-033-009, AUD-033-012, AUD-033-017 |

## Research Decision Assessment

| Decision/refinement | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| R1 | PARTIAL | [MAF selection](research.md#L11): dependencies and actual Agent construction exist, but graph/durable/HITL/tool integration is not delivered. | AUD-033-003 |
| R2 | PARTIAL | [Custom SDK executors/graph](research.md#L23): executor class names exist without SDK inheritance and builder does not construct a framework graph. | AUD-033-001, AUD-033-003 |
| R3 | SUPERSEDED | [Original endpoint choice](research.md#L34) is replaced only for chat-plane migration by [ADR 20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L27). OpenAIChatClient/managed-identity/client-side-state intent remains; actual workflow state capture is incomplete. | AUD-033-001, AUD-033-003 |
| R4 | SUPERSEDED | [Custom subclass decision](research.md#L46) explicitly replaced by [SDK-storage ADR](../../docs/corpus/aidr/decisions/adr-033-02-cosmos-checkpoint-storage.md#L24). The current wrapper/schema/retention is still partial. | AUD-033-001, AUD-033-009 |
| R5 | SUPERSEDED | [Literal RequestPort design](research.md#L59) explicitly replaced by [custom gate/listener ADR](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L28). Durable authorized approval semantics are not superseded. | AUD-033-005 |
| R6 | PARTIAL | [MCP transport](research.md#L70): real SDK class/FastMCP scaffold exists but discovery/auth/version/result/routing behavior is incomplete. | AUD-033-012 |
| R7 | PARTIAL | [Startup telemetry](research.md#L82): helper has no runtime caller or per-agent evidence establishing existing exporter/query compatibility. | AUD-033-010 |
| R8 | PARTIAL | [Immutable audit mechanism](research.md#L92): declarative retention policy exists but actual role/CI consumption does not enforce the proposed immutability. | AUD-033-009 |
| R9 | PARTIAL | [Fixture replay/equivalence](research.md#L103): implemented loader only compares stored pairs and can pass missing/invalid corpora. | AUD-033-013 |
| R10 | PARTIAL | [Migration flags/shadow](research.md#L114): helpers exist; actual dispatch, background comparison, current deployment mechanism and valid legacy fallback are not proven. | AUD-033-003, AUD-033-004, AUD-033-017 |
| Refinement: retry tuning | PARTIAL | [Documented default](research.md#L129) is exponential backoff, three attempts/30 seconds. Code uses fixed sleep and no hard call deadline; no approved per-agent tuning or all-override test is recorded. | AUD-033-007 |
| Refinement: OTel names | PARTIAL | [Attribute reconciliation](research.md#L130) is deferred to cutover; current snapshot is empty and no emitted-field compatibility proof exists. | AUD-033-010, AUD-033-014 |
| Refinement: state layout | PARTIAL | [Layout iteration](research.md#L131) has visible components but broken selected-state propagation and no accessible/timely-state proof. | AUD-033-011 |
| Refinement: tool governance | UNVERIFIED | [PR/CODEOWNERS default](research.md#L132) is not backed by a tool-registration ownership rule in [current CODEOWNERS](../../.github/CODEOWNERS#L27); no registration review/sign-off is recorded. | AUD-033-012, AUD-033-017 |

## Checklist Evidence

The original checklist has 16 `[x]` items. `CHK-033-nnn` below are audit labels in the original order;
they are not new original task IDs. A written quality criterion can be IMPLEMENTED while the product
behavior it describes is incomplete. All original checkbox states remain unchanged.

| Checklist item | Original state | Status | Assessment/evidence | Follow-up |
| --- | --- | --- | --- | --- |
| CHK-033-001 | [x] | CONFLICT | [No implementation details](checklists/requirements.md#L9): body includes source paths, schemas and RequestInfoEvent timing, notably [FR-024a](spec.md#L151)/[SC-008](spec.md#L176), not only the Input quotation. | AUD-033-017 |
| CHK-033-002 | [x] | IMPLEMENTED | [Business/user-value focus](checklists/requirements.md#L10): four story narratives explain operational value, safety, compliance and extensibility. | none |
| CHK-033-003 | [x] | PARTIAL | [Nontechnical audience](checklists/requirements.md#L11): story narratives are accessible, but detailed SDK/schema/path/flag clauses require technical interpretation. | AUD-033-017 |
| CHK-033-004 | [x] | IMPLEMENTED | [Mandatory sections](checklists/requirements.md#L12): stories, scenarios, edge cases, requirements, entities, outcomes, assumptions, scope and dependencies are present. | none |
| CHK-033-005 | [x] | IMPLEMENTED | [No clarification markers](checklists/requirements.md#L16): no unresolved marker occurs in spec; eight answered clarifications exist. This does not resolve the later cross-artifact contradictions. | none |
| CHK-033-006 | [x] | CONFLICT | [Testable/unambiguous](checklists/requirements.md#L17): continuous-vs-idle duration, held-run activity, warning prompt equality, failure context and approval modification semantics disagree across artifacts/source. | AUD-033-004, AUD-033-005, AUD-033-006, AUD-033-016, AUD-033-017 |
| CHK-033-007 | [x] | IMPLEMENTED | [Measurable SCs](checklists/requirements.md#L18): numerical rate/latency/capacity targets and worked-example criteria are authored. Measurement is UNVERIFIED, separately assessed per SC. | none |
| CHK-033-008 | [x] | PARTIAL | [Technology-agnostic SCs](checklists/requirements.md#L19): business outcomes predominate, but SC-008 names RequestInfoEvent and several SCs prescribe code/runtime surfaces. | AUD-033-017 |
| CHK-033-009 | [x] | IMPLEMENTED | [Acceptance scenarios defined](checklists/requirements.md#L20): all 17 numbered scenarios are present and separately assessed above. | none |
| CHK-033-010 | [x] | IMPLEMENTED | [Edge cases identified](checklists/requirements.md#L21): all eight original bullets are present and separately assessed above. | none |
| CHK-033-011 | [x] | IMPLEMENTED | [Bounded scope](checklists/requirements.md#L22): five agents/four adoption areas, six explicit exclusions and one required routing tool are stated. | none |
| CHK-033-012 | [x] | IMPLEMENTED | [Dependencies/assumptions identified](checklists/requirements.md#L23): seven assumptions and six dependencies are documented; their truth/completion is assessed separately, not certified by this checkbox. | none |
| CHK-033-013 | [x] | PARTIAL | [All FRs have clear acceptance](checklists/requirements.md#L27): major flows are covered, but state/clock/prompt/approval contradictions and incomplete tests prevent treating all acceptance boundaries as settled. | AUD-033-005, AUD-033-006, AUD-033-013, AUD-033-017 |
| CHK-033-014 | [x] | IMPLEMENTED | [Primary flows covered by scenarios](checklists/requirements.md#L28): four stories cover agents, durable/HITL workflow, cross-cutting controls and tools. They do not prove those flows run. | none |
| CHK-033-015 | [x] | UNVERIFIED | [Feature meets measurable outcomes](checklists/requirements.md#L29): no real fault/capacity/cutover/telemetry/publication evidence establishes this assertion; baseline explicitly is placeholder. | AUD-033-015, AUD-033-017 |
| CHK-033-016 | [x] | CONFLICT | [No implementation leaks](checklists/requirements.md#L30): same counterexamples as CHK-033-001; checklist notes do not remove code-specific body constraints. | AUD-033-017 |

Checklist validation notes were also read: (1) the claim that framework terms occur only in Input is
overstated; (2) business-outcome framing is generally supported but SC-008 retains a SDK event name;
(3) no unresolved marker is present, but documented defaults are not verified implementation decisions;
(4) the rule that incomplete items require follow-up is guidance, not proof that all checked items were
reviewed. No independent reviewer identity, review date/result artifact or measurement is attached to
this checklist beyond its authored creation metadata.

## Constitutional Review And Phase Gates

The plan marks every constitutional row PASS both initially and post-design. These are authored design
claims, not independent human sign-offs or runtime evidence. All 15 rows are assessed here.

| Plan review row | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| CG-1: Primacy of life | PARTIAL | [Plan claim](plan.md#L85): intended HITL/durability exists as design; checkpoint suppression, approval integration and fake legacy plans contradict completion. | AUD-033-001, AUD-033-004, AUD-033-005 |
| CG-2: National principles | PARTIAL | [Plan claim](plan.md#L86): common flow and audit scaffolds exist, but coordination/audit completeness not guaranteed. | AUD-033-003, AUD-033-008 |
| CG-3: AIIMS alignment | CONFLICT | [Plan claim](plan.md#L87): real approval schema/modify authority is not inherited by the bridge. | AUD-033-005 |
| CG-4: Multi-hazard/agency | PARTIAL | [Plan claim](plan.md#L88): definitions are broadly hazard-neutral; no representative equivalence corpus proves behavior preservation or multi-agency isolation. | AUD-033-002, AUD-033-004, AUD-033-013 |
| CG-5: Transparency/audit | PARTIAL | [Plan claim](plan.md#L89): fingerprints and UI declarations exist; audit loss, absent state history and env-only reconciliation defeat completeness. | AUD-033-006, AUD-033-008, AUD-033-010 |
| CG-6: Warning/public information | CONFLICT | [Plan claim](plan.md#L90): prompt/body/tier and approval contracts drift; keyword tests do not protect the ten principles or unchanged output. | AUD-033-004, AUD-033-005 |
| CG-7: Evacuation framework | CONFLICT | [Plan claim](plan.md#L91): facade returns a minimal plan and mock route instead of preserving the real planning/routing pipeline. | AUD-033-004, AUD-033-012 |
| CG-8: Recovery support | PARTIAL | [Plan claim](plan.md#L92): [recovery/lessons helpers](../../apps/agents/common/handoffs.py#L70) remain, but no corresponding edges exist in the manual new workflow. Preserved file is not preserved consumer routing. | AUD-033-003, AUD-033-004 |
| CG-9: Azure infrastructure | PARTIAL | [Plan claim](plan.md#L93): declared Azure/MAF components exist, but image inclusion, settings, deployed composition and target policy gates remain incomplete/unverified. | AUD-033-003, AUD-033-009, AUD-033-012 |
| CG-NN1: HITL | PARTIAL | [Plan claim](plan.md#L94): pause is implemented but durable authorized decision/publication and no-orphan audit are not. | AUD-033-005 |
| CG-NN2: Sovereignty | UNVERIFIED | [Plan claim](plan.md#L95): AU-only main location/template intent is visible; current cloud placement, carve-out approval and effective service identities were not queried. | AUD-033-009, AUD-033-017 |
| CG-NN3: Privacy | PARTIAL | [Plan claim](plan.md#L96): fingerprints are real, but raw shadow artifacts, unfiltered error text and lost audit are not protected by the asserted complete control chain. | AUD-033-008, AUD-033-009 |
| CG-NN4: Interoperability | PARTIAL | [Plan claim](plan.md#L97): schemas/SDK tools exist; actual edge payloads, approval envelope, field compatibility and MCP version/result contracts drift. CAP/EDXL preservation is not established by default alert construction. | AUD-033-004, AUD-033-005, AUD-033-012, AUD-033-014 |
| CG-NN5: Degradation | CONFLICT | [Plan claim](plan.md#L98): checkpoint errors are ignored, fallbacks are not real pipelines, and routing failures are swallowed. | AUD-033-001, AUD-033-004, AUD-033-012 |
| CG-QG: Quality gates | PARTIAL | [Plan claim](plan.md#L99): CI equivalence step exists, but empty corpora, omitted unit guards, missing policy invocation and placeholder performance evidence can remain green. | AUD-033-013, AUD-033-014, AUD-033-015, AUD-033-017 |

The [initial PASS](plan.md#L108), [post-design PASS](plan.md#L286) and empty complexity-violation table
are UNVERIFIED as completed independent reviews. Design statements do not prove the failure boundaries
they describe. No external approvals were sought in this audit.

| Phase/review obligation | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| PG-1: Setup | PARTIAL | [Setup tasks](tasks.md#L45): dependencies/packages/relocated ADRs authored; SDK import/install/lint/commit checkpoint not established by static inspection. | AUD-033-003, AUD-033-017 |
| PG-2: Foundation | PARTIAL | [Foundation](tasks.md#L90): helpers/contracts present; atomicity, storage, safety/audit, snapshots and policy prerequisites are not complete, so the blocking gate is not proved. | AUD-033-001, AUD-033-006, AUD-033-008, AUD-033-009, AUD-033-014 |
| PG-3: US1 MVP | UNVERIFIED | [Agent/equivalence phase](tasks.md#L222): no five-agent invocation reports or 24-hour shadow/cutover evidence; default legacy scaffolds do not prove MVP eligibility. | AUD-033-003, AUD-033-004, AUD-033-013 |
| PG-4: US2 | UNVERIFIED | [Workflow/HITL phase](tasks.md#L323): no real durable workflow, authenticated end-to-end approval, 99/100 restores, capacity/latency or day-one visibility measurement. | AUD-033-001, AUD-033-005, AUD-033-011, AUD-033-015 |
| PG-5: US3 | UNVERIFIED | [Uniformity phase](tasks.md#L439): manual no-op test and env-count arithmetic are not cross-agent safety/audit/OTel, daily reconciliation or completed worked-example evidence. | AUD-033-008, AUD-033-010, AUD-033-014 |
| PG-6: US4 | UNVERIFIED | [MCP phase](tasks.md#L479): server/client/infra scaffolds exist, but real routing integration, deployed seed, protocol errors and alert delivery are unverified. | AUD-033-012 |
| PG-7: Polish | UNVERIFIED | [Polish](tasks.md#L522): no separate engineer rehearsal, <5-minute rollback, real baseline, nine-section quickstart validation, full-suite result or analyze acceptance artifact. | AUD-033-015, AUD-033-017 |

Required actor labels in the actual task entries (excluding the format-template example) are:
accessibility-tester, ai-ml-engineer, api-architect, azure-principal-architect, chaos-engineer,
compliance-auditor, data-engineer, docker-container-engineer, incident-commander, infrastructure-devops,
logistics-officer, nswpf, observer-auditor, principal-engineer, public-information-officer,
qa-test-engineer, risk-manager, security-engineer, ses-nsw, software-developer, solution-architect,
speckit.analyze, sre-engineer, transport and ux-designer. All 25 are role assignments, not attestations.
The task-specific technical/operational contributions, security/compliance/architecture reviews,
accessibility verification, SRE/platform lead production co-signs and independent rollback/quickstart
rehearsals remain future work unless separately documented evidence is produced. No appended persona
or hypothesis task block exists in the local specification; these role obligations are not omitted.

## Artifact And Execution Evidence

| Artifact/review input | Status | What it proves and what it does not | Follow-up |
| --- | --- | --- | --- |
| Four relocated MAF ADRs | PARTIAL | All four were read fully. They record authored decisions and explicit SDK/HITL replacements. Accepted labels and hypothetical consequences do not prove actor participation, working adapters or deployed outcomes. | AUD-033-001, AUD-033-005, AUD-033-012, AUD-033-017 |
| Cutover and rollback guides | PARTIAL | Both relocated guides were read fully; they state stages, report/load prerequisites and authority. No separate-engineer rehearsal/co-signed PR or measured rollback record accompanies them. | AUD-033-003, AUD-033-015, AUD-033-017 |
| Equivalence corpus/reports | PARTIAL | Five tests, one monitoring README/pair and [gitkeep](../../apps/agents/maf_runtime/equivalence/reports/.gitkeep#L1) exist and were read. README explicitly defers real fixtures to shadow cutover; gitkeep's claim that JSON is ignored is not implemented in root ignore rules. Four corpora and all per-agent Markdown results are absent in the scoped inventory. | AUD-033-013, AUD-033-017 |
| Field snapshots | PARTIAL | Both committed JSON snapshots were read fully. API snapshot includes request models and the new audit schema; dashboard fields are empty. They do not prove pre-MAF emitted-field coverage or deterministic capture execution. | AUD-033-014 |
| Capacity baseline/capture | UNVERIFIED | Baseline and capture script read fully: placeholder constants, not a run. No MAF result artifacts, sustained/burst windows or fault-injection diagnostics were found in named result/report locations. | AUD-033-015 |
| Unit/integration/contract tests | PARTIAL | Tests are inspected assertion source only. Real enum/error/threshold/lookup assertions are credited; no execution result is claimed. Existing tests commonly use memory repositories without clearing endpoint env vars; later test lanes need explicit isolated transports to avoid unintended cloud reads. | AUD-033-001, AUD-033-005, AUD-033-007, AUD-033-008, AUD-033-012, AUD-033-017 |
| Web tests | PARTIAL | Interface smoke accepts 500 for workflows; the page object tolerates error chrome; capstone outcome tests call evaluator/audit APIs and merely label the workflows route. No focused state/window/history/refresh/trace/axe proof is present. | AUD-033-011 |
| Quickstart sections 1 and 2 | CONFLICT | [Install/isolated agent](quickstart.md#L8): dependencies differ from current locked/resolved choices, cwd repeats apps/agents, `--input` is not parsed by the stdin CLI, and named examples/sample fixtures were not found. No execution record. | AUD-033-003, AUD-033-004, AUD-033-017 |
| Quickstart sections 3 and 4 | CONFLICT | [Workflow/approve](quickstart.md#L49): fixture is absent, manual workflow lacks correct persistence, approval script is absent and actual decision/publication integration is not wired. | AUD-033-001, AUD-033-005, AUD-033-017 |
| Quickstart section 5 | CONFLICT | [Crash recovery](quickstart.md#L84): no long-running fixture or supported `--resume`; no verified restore path. | AUD-033-001, AUD-033-017 |
| Quickstart sections 6 and 7 | CONFLICT | [Tool/equivalence](quickstart.md#L110): registration CLI exists, but real tool use is unwired and example absent; `--emit-report` is not a runner option and its working-directory fixture root differs from the documented invocation. | AUD-033-012, AUD-033-013, AUD-033-017 |
| Quickstart sections 8 and 9 | PARTIAL | [Cutover/UI](quickstart.md#L150): flags and page exist, but active composition and data/refresh/filtering do not satisfy the stated results. No 24-hour shadow, staged capacity or live dashboard verification. | AUD-033-003, AUD-033-011, AUD-033-015, AUD-033-017 |
| Quickstart KQL/code index | PARTIAL | [Queries/index](quickstart.md#L184) are authored examples; corresponding workflow/approval/audit telemetry producers are absent/unverified, and historical paths/API names drift. | AUD-033-010, AUD-033-017 |
| Worked middleware example | PARTIAL | [README](../../apps/agents/maf_runtime/middleware/README.md#L1) is an authored single-file diff, not an executed demonstration; its verification command reads canned outputs and cannot observe a policy change. | AUD-033-008, AUD-033-013 |
| CI, lock and packaging | PARTIAL | CI/root tooling, both image recipes, package metadata and relevant lock entries read. Declared core/OpenAI >=1.2.2 differs from lock 1.3.0 and root installed 1.2.2. Images/CI use pip ranges, not frozen lock; installed SDK inspection is bounded local evidence only. Full dependency security/advisory state and install/build results are UNVERIFIED. | AUD-033-003, AUD-033-017 |
| Infrastructure/policies | PARTIAL | Container/role/env/module source and relocated Rego were read; active settings differ, policy is not consumed, routing/alert/approval support modules are unreferenced from main. No Bicep build, what-if, role query, seed, alert delivery or deployment evidence is claimed. | AUD-033-009, AUD-033-012, AUD-033-017 |
| Analyze/approval outcomes | UNVERIFIED | T076 and checklist/plan PASS wording are assertions without a local completed analysis or attributable approval result. The current CODEOWNERS file does not certify requested reviews or externally enforced branch protection. | AUD-033-017 |

## Negative-Search Scope

Searches were read-only and excluded other implementation-review reports. `rg` was unavailable and
workspace search timed out; scoped PowerShell file enumeration/Select-String and direct file reads were
used instead. No absence claim is based only on an old filename.

| Scope label | Searched scope and controlling surfaces | Result/boundary |
| --- | --- | --- |
| NS-01 | Full recursive local spec-033 inventory, including hidden files, plus all 14 originals read fully | No original review, amendment, appended persona/hypothesis file, extra checklist or local evidence bundle beyond the listed inputs. The newly authored report is the only added local file. |
| NS-02 | Agent and API Python source, alternate package/script/tool callers; terms AmaWorkflow, WorkflowBuilder, MAF facades, feature flags, HitlDecisionListener, stamp_terminal, duration_watchdog, setup_observability_once | No active production graph/restore/decision subscriber/retention/bootstrap/watchdog caller. Matching names in definitions/docstrings and CLI/test entry points were distinguished from production calls; the real Docker dispatcher was read. |
| NS-03 | Entire tests Python source plus API tests and source-identifier searches for middleware, checkpoint, retry, validation, approval decisions, publication and escalation | Relocated retry/validation assertions are in test_executor_base; resume/concurrent claims in test_hitl_round_trip were read. No actual 100-trial restore, MAF timeout/escalation, bidirectional publish-decision, complete middleware/SDK-storage assertions were found. Legacy tests are not proof of new integration. |
| NS-04 | All MAF package files, tool server, existing evacuation routing source and tests; definition/resolver/client/server/consumer chain | SDK symbols exist but tools are not passed to Agent, version fallback is synthetic, legacy routing discards outcomes and no shared tool-audit producer exists. Current installed interfaces were used only for explicitly bounded compatibility facts. |
| NS-05 | All infrastructure Bicep and relevant JSON/KQL, main module/env/role graph, azure.yaml and all workflow YAML gate references | Containers wired to disaster-hub; routing-mcp/maf-tool-alerts/communication-agent/posture-policy-set lack main calls. No decision queue/audit_entries declaration or MAF agent/state panels found in the searched IaC; real deployed state remains UNVERIFIED. |
| NS-06 | docs recursive names for 033/MAF plus decision-content searches; no other spec implementation reports | Four MAF ADRs and two runbooks relocated to docs/corpus/aidr were read fully. ADR 20 and CODEOWNERS give narrowly scoped replacements. Phi ADR belongs to spec 032; no blanket retirement of spec 033 behavior/evidence found. |
| NS-07 | tests/equivalence recursively, runtime equivalence/reports including gitkeep, tests/load/baselines/results, both contract snapshots, middleware/server READMEs and capture/registration scripts | One stored monitoring pair, four absent corpora, no Markdown reports or MAF results, empty dashboard snapshot and explicit placeholder baseline. No seed/cutover/latency/recovery/sign-off outcome was inferred from scaffolding. |
| NS-08 | Web source, tests/e2e, all Python tests, apps/web test directories and configured Vitest discovery | Relevant interface/page-object/outcome tests read; no working selected-state propagation, polling, trace-link wiring or focused workflow component assertions. Broad tests do not replace the missing behavior checks. |
| NS-09 | Source-described quickstart examples across tests/fixtures, apps/agents and scripts, plus actual CLI parsers and current root ignore rules | Named flood/long-running/monitoring/routing sample files and approve_alert script not found; stdin and runner flags differ. No required equivalence-JSON ignore rule appears in the inspected root file. |

## Final Static Validation

**Receipt, 2026-09-14:** report-only PowerShell text/path checks and editor diagnostics passed.

| Gate | Result |
| --- | --- |
| Revision | HEAD matches `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`, verified read-only before and after inspection. |
| Original tasks | 88 distinct rows, all exact original IDs (including suffixes) and case-preserved `[X]` states; no collapsed ranges or omitted tasks. |
| Requirement coverage | All 33 FRs and 10 SCs matched the original identifier set; zero separately numbered NFRs. |
| Scenario/edge coverage | All 17 exact story/scenario labels and eight edge cases accounted for. |
| Checklists/reviews | All 16 original `[x]` checklist items matched in order; 15 constitutional rows, seven phase gates, ten research decisions and all clarification/scope/dependency ledgers present. |
| Follow-ups | 17 unique stable AUD-033 IDs, every task unchecked, all references resolve to a detailed future-only developer/tester task. |
| Evidence links | All 570 local links resolve to existing files within the workspace and valid single-line anchors, across 138 distinct evidence files; no proposed path is represented as existing evidence. |
| Report text | ASCII; no remaining in-progress ledger placeholders; source-path inference and duplicate-paragraph mistakes found during drafting were corrected before final validation. |
| Diagnostics | `get_errors` reports no errors for this report. No source-file diagnostics, product tests, verifier scripts, builds or runtime execution were used. |
| Write scope | No tracked file differs from HEAD. Within spec 033, only this new report is present as an untracked addition; original specification/tasks/checklists/evidence and the audit index remain untouched. |

Original-task status totals: 11 IMPLEMENTED, 63 PARTIAL, 3 MISSING, 5 CONFLICT, 5 UNVERIFIED and
1 SUPERSEDED. These are source-review assessments, not endorsements of the original checked boxes.

**Remaining blockers:** the report is complete, but MAF production composition, durable recovery,
approval authority/integration, tenant/role enforcement, equivalent behavior, immutable audit and real
MCP routing require the documented repairs. SDK resolution beyond the explicitly inspected local
version, performance/capacity, migration execution, deployed resources, alert delivery and human
sign-offs remain UNVERIFIED. No implementation, test run, model/cloud call, deployment, approval,
branch change or commit was performed as part of this audit.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 033 only. Three parallel technical reviews examined workflow
authorization, checkpoint/HITL durability, and MAF equivalence/tooling. The source-completable route-boundary defect was
corrected: `/api/workflow_runs` is now included in both Entra authentication and RBAC protected-prefix registries.

Validation: `python -m pytest tests/integration/test_rbac_enforcement_036.py -q` returned `15 passed` (2 existing
deprecation warnings).

Remaining open work includes trusted membership/tenant authorization, durable checkpoint restore, HITL approval-store
integration, append-only audit, CAS run uniqueness, production MAF composition, legacy equivalence, MCP routing,
telemetry, capacity, deployment, and human/provider evidence.

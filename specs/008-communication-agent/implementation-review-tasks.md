# Spec 008 Implementation Review and Remediation Tasks

## Review Boundary

- Review date: **2026-09-11**.
- Reviewed source revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**; local HEAD matched this revision.
- Scope: [spec.md](spec.md), including both clarification sessions and all appended amendments, and its implementation dependencies.
- Contract: [Review Contract](../001-spec-implementation-audit/README.md#L13).
- This is an independent, static, review-only continuation. No other implementation-review-tasks reports were read. No delegation, branch, commit, central-index update, source change, test execution, import, build, benchmark, deployment, or cloud-resource query was performed.
- Sole authored artifact: this report. Existing untracked audit artifacts were left untouched. No specification-specific memory was retained for another review.
- Coverage: **64 original tasks**, all originally `[x]`; **61 requirement rows** (43 base FRs including FR-006a, 4 capstone FRs, 3 NFRs, 11 SCs); **32 acceptance scenarios**; **9 edge cases**; **10 additional persona/hypothesis/scope amendment rows**. All **72 CHK questions**, **16 quality-checklist claims**, **23 plan gates**, and **14 research decisions** are assessed below.
- Follow-ups: **38**, all unchecked. P0 means a safety/security blocker; P1 means significant delivery, correctness, or availability work; P2 means supporting validation, configuration, or governance work. Priorities are not claims of observed production incidents.

### Evidence Semantics

`IMPLEMENTED` means inspected source supports the full stated behavior or authored artifact, not that it ran successfully. `PARTIAL` means specific obligations remain. `MISSING` is used only after the scoped searches recorded below. `CONFLICT` means requirements or behavior disagree. `UNVERIFIED` means execution, outcome, approval, or deployment is not established. `SUPERSEDED` requires explicit replacement evidence; a similarly named helper is insufficient. Deferred country functionality is not classified as missing merely because it is deferred.

### Inputs Read

The complete local input set was read: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [contracts/communication-pipeline.md](contracts/communication-pipeline.md), [contracts/health-endpoint.md](contracts/health-endpoint.md), [contracts/telemetry.md](contracts/telemetry.md), [checklists/communication-agent.md](checklists/communication-agent.md), [checklists/requirements.md](checklists/requirements.md), [evidence/HYP-027.md](evidence/HYP-027.md), [evidence/HYP-028.md](evidence/HYP-028.md), and [evidence/HYP-029.md](evidence/HYP-029.md). The two lines truncated by the file viewer were separately read in full as text.

Applicable guidance included the [constitution](../../.specify/memory/constitution.md), [code-review instructions](../../.github/instructions/code-review.instructions.md), [review checklist reference](../../.github/instructions/references/code-review-checklists.md), [Bicep instructions](../../.github/instructions/bicep-code-best-practices.instructions.md), and [policy-compliance instructions](../../.github/instructions/bicep-policy-compliance.instructions.md). The Python fact-grounded coding skill was read; its runtime/debugger steps were not used because this audit explicitly prohibits execution. No claim about installed dependencies, interpreter diagnostics, live SDK responses, or deployed authentication is made.

### Traced Paths and Negative-Search Scope

| Evidence scope | Actual path inspected and conclusion |
| --- | --- |
| S1: Legacy communication runtime | [package entrypoint](../../apps/agents/communication/__main__.py#L1) imports the module and then does nothing; [create_app](../../apps/agents/communication/agent.py#L111) requires injected services, while initialization only occurs in that module's own main guard. [Pipeline](../../apps/agents/communication/pipeline.py#L93) reaches a logging-only approval stage. All communication modules were inventoried; controlling implementations and associated unit assertions were read. |
| S2: Replacement runtime | [legacy handoff deprecation](../../apps/agents/common/handoffs.py#L1) explicitly points to MAF. [MAF facade](../../apps/agents/maf_runtime/agents/communication_agent.py#L31), [factory](../../apps/agents/maf_runtime/agents/_factory.py#L265), [workflow](../../apps/agents/maf_runtime/workflow/builder.py#L149), and [HITL publisher/listener](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L65) were inspected. MAF supplies a queue publisher and parked workflow, but does not demonstrate the full Spec 008 drafting, escalation, or delivery contract. The default communication legacy facade returns an empty v1 alert, not the legacy pipeline. |
| S3: Deployed-image alternative | [azure.yaml](../../azure.yaml#L8) selects the root infrastructure and shared agent image. [Dockerfile](../../apps/agents/Dockerfile#L43) launches the dispatcher. [Dispatcher](../../apps/agents/dispatcher/agent.py#L187) handles role-specific simulation questions, not handoffs or PublicAlert delivery. It is not evidence that the 8084 communication service is running. |
| S4: Dashboard/API alternative | [Composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L24) calls [publishAlert](../../apps/web/src/lib/api/alerts.ts#L3), [API routes](../../apps/api/app/api/routes/alerts.py#L35), and [PublicAlertService](../../apps/api/app/services/public_alert_service.py#L55). Its different domain model, flat English content, publication states, and payload-only adapters do not supply Spec 008's full multilingual lifecycle. [Warning builder](../../apps/agents/communication/warning_builder.py#L61) and [chain route](../../apps/api/app/api/routes/warning_chain.py#L29) provide separate AWS warning functionality; they are credited, not mistaken for ca-version history. |
| S5: Tests and renamed files | Searched tracked tests, applications, tools, and scripts for CommunicationProcessingPipeline, CommunicationAgent, deliver_approved_alert, request_approval, escalation, expiry, versioning, and communication queue/container names. Planned handoff/schema/reproducibility contract tests and the three disaster scenarios exist under [tests/unit](../../tests/unit/), not their planned directories. No communication Cosmos integration test was found; queue references lead to [MAF HITL tests](../../tests/integration/test_hitl_round_trip.py#L51), not an intake consumer test. No product tests were run. |
| S6: Infrastructure | Searched tracked infrastructure for communication-agent.bicep references, communication queue/container names, port 8084, and regional configuration. [Standalone module](../../infra/modules/communication-agent.bicep#L71) declares resources, but no other tracked infrastructure file invokes it. Root and nested Bicep entrypoints and azure.yaml were included in that search. This establishes disconnected source, not absence of already-deployed resources. |
| S7: Templates and evidence | Parsed all six files under [data/alert-templates](../../data/alert-templates/) as JSON text. Each has 22 entries and the same 19 hazard/type combinations. Searched local evidence and targeted docs/agents, docs/testing, docs/attestations, docs/observability, tests, and CODEOWNERS references for communication execution/approval evidence. No qualifying Spec 008 execution log or template approval record was identified. [Benchmark](../../tests/benchmark/test_pipeline_performance.py#L165) is authored but is not a measurement result. |
| S8: Amendments | Followed only explicit authority/evidence pointers: [Spec 006 pointer](../006-data-ingestion-storage/spec.md#L254), [Spec 018 authority](../018-aidr-guidance-integration/spec.md#L343), and [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L39). A scoped filename search of the latter evidence folder found no promised HYP-HYP-006.md stub or renamed *006* evidence file. No other audit report was consulted. |

## Prioritized Findings and Open Tasks

Every task below is future work for a separately authorized developer/tester. Existing paths are linked as evidence; paths labelled **proposed** do not yet exist. Validation command labels refer to the future-only command catalogue later in this report.

### AUD-008-001: Authenticate and Authorize Alert Actions and Reads

- [x] AUD-008-001 Enforce trusted commander identity and tenant-scoped authorization on every alert action and read.

**Priority/status:** P0 / MISSING authorization on the standalone service. **Affected:** FR-019, FR-020, FR-040, FR-041, SC-003; T025, T026, T027, T031, T053; US2-AS1/AS2/AS3, US7-AS2.

**Expected/actual/impact:** [Approval contract](contracts/health-endpoint.md#L73) requires a commander JWT. [Approve](../../apps/agents/communication/agent.py#L217), reject, modify, cancel, and reads accept no identity dependency or middleware; user ID and role come from the body. [Endpoint test](../../tests/unit/test_communication_endpoints.py#L79) expressly posts without credentials and expects success. Any reachable caller can impersonate a commander or read/modify alert content. S1/S4 were searched; API middleware is not inherited by this separate FastAPI app.

**Developer:** Own [agent.py](../../apps/agents/communication/agent.py#L111) and the shared approved authentication boundary. Validate signature, issuer, audience, expiry, role, and tenant before lookup or mutation. Derive audit identity from verified claims; do not trust body-supplied identity. Cover all GET and POST routes and error envelopes without exposing another tenant's record existence.

**Tester:** Extend [endpoint tests](../../tests/unit/test_communication_endpoints.py#L78) with signed test tokens and fake key resolution. Assert authorized commander success; missing, expired, wrong-audience, forged, noncommander, mismatched-body, and foreign-tenant requests cause zero store/provider mutations. Apply the same matrix to modify/cancel/read/status, including whitespace rejection justification. Future `V-AUTH`.

**Dependencies/completion:** Coordinate with AUD-008-003 and AUD-008-011. Complete when every reachable alert route rejects untrusted authority and persisted audit identity matches verified claims; network isolation alone is insufficient.

### AUD-008-002: Make Human Approval a Non-Bypassable Delivery Invariant

- [x] AUD-008-002 Require a persisted, version-specific human approval at all publication and delivery boundaries.

**Priority/status:** P0 / CONFLICT. **Affected:** FR-019, FR-020, FR-021, SC-003; T025, T028, T029, T030; US2-AS1/AS2, US3-AS1.

**Expected/actual/impact:** [deliver_approved_alert](../../apps/agents/communication/pipeline.py#L586) unconditionally changes any supplied alert to delivering. [Delivery service](../../apps/agents/communication/delivery.py#L56) does not inspect approval status. Its [tests](../../tests/unit/test_communication_delivery.py#L20) construct drafting alerts. Separately, [API publication validation](../../apps/api/app/services/public_alert_service.py#L47) permits pending_approval and trusts a persona ID. MAF's [static invariant test](../../tests/unit/test_send_response_call_sites.py#L31) searches only maf_runtime, so it does not protect these routes. Source demonstrates bypasses, not actual public sends.

**Developer:** Guard the lowest shared send boundary and API publication service. Resolve approved version and approver from durable state, atomically claim the transition, and reject other states. Remove the pending_approval publication allowance or route it through verified human approval. Preserve cancellation and supersession races; never infer approval from generation output or a caller-set enum.

**Tester:** In [delivery tests](../../tests/unit/test_communication_delivery.py#L20), [pipeline tests](../../tests/unit/test_communication_pipeline.py#L85), and [endpoint tests](../../tests/unit/test_communication_endpoints.py#L78), test every lifecycle state, forged approved objects, stale versions, cancellation races, repeated approve, and MAF/API entrypoints. Assert zero provider calls without durable approval and exactly one authorized transition. Future `V-AUTH`, `V-DELIVERY`, `V-PIPELINE`.

**Dependencies/completion:** AUD-008-001, AUD-008-009, AUD-008-011, AUD-008-022. Complete when no alternate route or direct helper invocation can bypass version-bound authorization.

### AUD-008-003: Close Simulation and Tenant Isolation Gaps

- [x] AUD-008-003 Use canonical tenant isolation for delivery, deduplication, versions, data reads, and all audit events.

**Priority/status:** P0 / CONFLICT. **Affected:** FR-003, FR-015, FR-033, FR-040, FR-041, NFR-003; T013, T016, T018, T020, T029, T038, T046, T057, T058; EC-03.

**Expected/actual/impact:** [TenantContext](../../apps/api/app/core/tenant_context.py#L13) defines simulation as tenant_id != live; [delivery](../../apps/agents/communication/delivery.py#L66) only recognizes the simulation prefix. A non-live UUID can reach SMS/push branches. [Dedup keys](../../apps/agents/communication/dedup.py#L42) omit tenant, [version assignment](../../apps/agents/communication/versioning.py#L42) has no tenant input, and [safety/back-translation audit calls](../../apps/agents/communication/pipeline.py#L335) omit tenant and correlation, falling back to live in [audit helper](../../apps/agents/communication/pipeline.py#L658). [Simulation test](../../tests/unit/test_communication_delivery.py#L170) covers only simulation-test.

**Developer:** Make validated tenant context mandatory end to end. Deny real delivery for every non-live/unknown context; do not depend on name prefixes. Partition dedup and version counters by tenant plus incident, validate scope-key/record ownership, and propagate context to safety, approval, delivery, and degradation audits. Reuse canonical semantics without importing the entire API runtime into agents.

**Tester:** Use live, UUID simulation, simulation-prefixed, empty, and unknown tenants sharing identical incident/handoff IDs. Inject provider spies and tenant-aware storage fakes; assert zero real simulation sends, independent counters/caches, no live audit contamination, and no cross-tenant reads. Extend [delivery](../../tests/unit/test_communication_delivery.py#L168), [handoff](../../tests/unit/test_communication_handoff.py#L7), [audit](../../tests/unit/test_communication_audit.py#L18), and [version tests](../../tests/unit/test_communication_versioning.py#L11). Future `V-ISOLATION`.

**Dependencies/completion:** Required before wiring providers or intake. Complete when all three runtime alternatives preserve tenant boundaries and simulation records are explicitly distinguishable from actual receipt evidence.

### AUD-008-004: Replace No-Op Delivery With Receipt-Backed Adapters

- [x] AUD-008-004 Implement configured SMS, targeted push, and EAS adapters that cannot report a skipped send as delivered.

**Priority/status:** P0 / PARTIAL. **Affected:** FR-026, FR-027, FR-029, FR-037, SC-004; T002, T028, T029, T030, T049; US3-AS1/AS2/AS4, US8-AS3.

**Expected/actual/impact:** [SMS](../../apps/agents/communication/delivery.py#L208) sends to segment IDs with hard-coded EmergencyAlert sender and ignores results; absent clients just log. [Push](../../apps/agents/communication/delivery.py#L224) has no segment targeting. [Broadcast](../../apps/agents/communication/delivery.py#L236) never performs HTTP and skips non-en-AU records while reporting success. [Retry wrapper](../../apps/agents/communication/delivery.py#L161) treats any nonthrowing return as delivered. [Agent dependencies](../../apps/agents/pyproject.toml#L10) contain SMS and numpy but not the requested push SDK. This is false delivery accounting, not verified dissemination.

**Developer:** Own delivery adapters and composition. Resolve segment recipients through existing external registries without taking ownership of contact databases; use approved sender identity and targeted push registrations/tags. Perform authenticated EAS POST with en-AU content for every eligible segment, regardless of that segment's preference. Inspect provider acceptance/failure results, preserve receipt identifiers, and distinguish unconfigured, simulated, accepted, failed, and confirmed outcomes. Select a supported push integration rather than blindly adding an unverified package name.

**Tester:** Extend [delivery tests](../../tests/unit/test_communication_delivery.py#L88) with strict provider fakes, partial SMS result failures, rejected responses without exceptions, missing configuration, invalid targets, non-English segments, and webhook timeouts. Assert exact payload/target/language and that no skipped path is delivered. Future `V-DELIVERY`; later sandbox receipt verification only after separate authorization.

**Dependencies/completion:** AUD-008-001, AUD-008-002, AUD-008-003, AUD-008-014, AUD-008-015. Complete when success is backed by the agreed segment-level provider evidence and all unavailable adapters fail truthfully.

### AUD-008-005: Deduplicate Recipients Without Dropping Whole Populations

- [x] AUD-008-005 Replace zone-level segment suppression with overlap-aware recipient/channel deduplication.

**Priority/status:** P0 / CONFLICT. **Affected:** FR-022, FR-023, FR-024, FR-027, SC-004; T028, T029, T032, T033, T062; CHK041; US4-AS2/AS3.

**Expected/actual/impact:** [Deduplicator](../../apps/agents/communication/delivery.py#L118) groups solely by zone_level and suppresses every lower-priority segment. One hospital can suppress the general population of unrelated level-1 polygons. Equal-priority overlapping segments are not deduplicated. [Test](../../tests/unit/test_communication_delivery.py#L142) asserts this incorrect whole-segment behavior rather than shared-recipient semantics.

**Developer:** Use actual zone identity/geometry and opaque recipient memberships, not severity-level equality, to resolve overlapping recipients per alert version and channel. Keep highest-priority guidance for shared recipients while delivering to each segment's nonoverlapping remainder. Preserve all segment metadata and dedup reasons for review; do not count suppressed populations as reached.

**Tester:** Add disjoint same-level polygons, partial overlap, nested hospital/general populations, equal-priority overlap, different channels/languages, and empty intersections to [delivery tests](../../tests/unit/test_communication_delivery.py#L140). Assert each intended recipient gets one message per channel, all nonoverlapping recipients remain, critical guidance wins, and receipt denominators reflect actual reach. Future `V-DELIVERY`.

**Dependencies/completion:** AUD-008-004 and AUD-008-016. Complete when dedup preserves intended population coverage and never replaces a whole zone with a facility merely because their level matches.

### AUD-008-006: Establish a Runnable, Explicit Communication Runtime

- [x] AUD-008-006 Connect the chosen runtime to the full communication pipeline and document the retained compatibility entrypoint.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-001, FR-019, FR-038, FR-039; T001, T018, T019, T024, T064; US1-AS1, EC-09.

**Expected/actual/impact:** [Package launcher](../../apps/agents/communication/__main__.py#L1) does not start a service; [package exports](../../apps/agents/communication/__init__.py#L3) omit CommunicationAgent. [Module-only bootstrap](../../apps/agents/communication/agent.py#L428) injects neither storage nor providers and keeps approval separate. [MAF legacy facade](../../apps/agents/maf_runtime/agents/communication_agent.py#L31) creates an empty v1, while [dispatcher](../../apps/agents/dispatcher/agent.py#L73) answers simulation questions. S1-S3 found no replacement delivering the complete contract.

**Developer:** Choose and record whether Spec 008 is served through MAF, the retained FastAPI service, or an explicit adapter. Reuse the actual drafting/validation/persistence/approval components; do not build a second unconnected pipeline. Provide a real lifespan with dependency initialization/shutdown and consumer lifecycle. Preserve the requested public API or explicitly migrate its callers; align package launch, container command, health port, and operator instructions.

**Tester:** Replace the [skipped six-language test](../../tests/contract/test_communication_llm.py#L4) with a real entrypoint contract using injected dependencies. Test startup/shutdown and one canonical producer handoff reaching persisted pending_review plus notification; assert no provider send before approval. Verify the MAF legacy path is not an empty model and the image entrypoint uses the chosen service. Future `V-PIPELINE`, `V-INTEGRATION`, `V-QUICKSTART`.

**Dependencies/completion:** Coordinate AUD-008-007 through AUD-008-013 and AUD-008-031; no public delivery until P0 tasks close. Complete when an operator can invoke the documented runtime and observe the full draft-to-review handoff.

### AUD-008-007: Validate and Retrieve Real Upstream Provenance

- [x] AUD-008-007 Reject invalid handoffs and missing incident/recommendation/assessment data while preserving transient redelivery.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-001, FR-002, FR-004, FR-033, FR-039; T012, T018, T019, T020, T024; EC-01/EC-07/EC-09.

**Expected/actual/impact:** [Intake](../../apps/agents/communication/pipeline.py#L174) checks target and dedup but not source, payload contract, or incident existence. [Retrieval](../../apps/agents/communication/pipeline.py#L225) swallows all read failures and fabricates data from payload defaults; no incident store exists in its constructor. [Upstream producer](../../apps/agents/risk_assessment/agent.py#L462) supplies camelCase IDs, unlike [pipeline fixtures](../../tests/unit/test_communication_pipeline.py#L16). Referenced assessment ownership/supersession is not checked, and a failed store read is treated like valid data.

**Developer:** Introduce a validated communication-boundary payload with required nonempty IDs, trusted source/target and tenant consistency. Retrieve the incident, recommendation, and assessment using their actual repository contracts; verify linkage and snapshot immutable inputs. Reject missing records with reasoned audit/dead-letter policy, but abandon/retry transient dependency failures. Surface superseded-assessment warnings and recheck at approval. Define receipt acknowledgement versus completion so the 5-second acknowledgement claim does not permit lost processing.

**Tester:** Extend [handoff tests](../../tests/unit/test_communication_handoff.py#L7) and [pipeline intake tests](../../tests/unit/test_communication_pipeline.py#L58) with real producer-shaped fixtures; wrong source/target, missing IDs, empty IDs, nonexistent incident, mismatched incident/tenant, missing references, stale/superseded assessment, 404 versus timeout, and valid confidence below the upstream expected threshold. Assert no invented references/content on retrieval failure and correct reject versus retry behavior. Future `V-PIPELINE`, `V-INTEGRATION`.

**Dependencies/completion:** AUD-008-003, AUD-008-008, AUD-008-009. Complete when every accepted draft has resolvable, same-scope provenance and failed infrastructure never silently substitutes an invented assessment.

### AUD-008-008: Make Deduplication Compatible With Recovery and Updates

- [x] AUD-008-008 Distinguish completed duplicates from failed attempts and legitimate incident updates.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-003, FR-017, FR-018, FR-039, SC-005; T009, T013, T018, T035, T037; US1-AS4, US5-AS1, EC-02.

**Expected/actual/impact:** [Cache methods](../../apps/agents/communication/dedup.py#L42) mark IDs seen before retrieval/persistence succeeds. The [pipeline](../../apps/agents/communication/pipeline.py#L174) marks incident/hazard from payload, but the real upstream handoff contains no hazard_type, making general the common key. A failed attempt or changed assessment can then be discarded for 30 minutes. The specification simultaneously requires same-incident dedup and successive versions; [TTL tests](../../tests/unit/test_communication_dedup.py#L73) do not test failure/retry or changing assessments.

**Developer:** Resolve duplicate-versus-update identity with AUD-008-037. Use separate in-flight/completed reservations, release or retry failed processing, and key semantic duplicates by authoritative assessment/version/change intent after retrieval. Keep tenant isolation and fail-open cache capacity semantics; protect durable exactly-once effects against at-least-once messaging without blocking corrections or all-clear.

**Tester:** Inject failures after intake, retrieval, persistence, and notification; redeliver same handoff and assert eventual completion without duplicate effects. Test new assessment within TTL, real duplicate, exact TTL boundary, capacity eviction, restart, same incident in two tenants, and correction/all-clear exceptions. Extend [dedup](../../tests/unit/test_communication_dedup.py#L11) and [pipeline](../../tests/unit/test_communication_pipeline.py#L58). Future `V-PIPELINE`, `V-ISOLATION`.

**Dependencies/completion:** AUD-008-007, AUD-008-009, AUD-008-022, AUD-008-037. Complete when retries cannot be lost to an early cache insertion and documented updates remain possible inside the window.

### AUD-008-009: Persist the Complete Alert Aggregate Reliably

- [x] AUD-008-009 Persist alerts, segment snapshots, and status changes durably before reporting success.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-002, FR-015, FR-016, FR-023, FR-027, FR-033; T017, T018, T030, T034, T053, T058.

**Expected/actual/impact:** [Stage 8](../../apps/agents/communication/pipeline.py#L455) stores segment IDs but never assigns segment.alert_id or persists their records; failed alert writes at line 543 are only logged and processing continues. Status changes in [delivery](../../apps/agents/communication/pipeline.py#L586) are not persisted to the alert store. [GET](../../apps/agents/communication/agent.py#L392) reads only the approval dictionary. A returned created alert can be unrecoverable, and a restart loses review state and audience targeting.

**Developer:** Own pipeline storage boundaries and repositories. Persist immutable content plus resolvable audience snapshots and tenant-scoped status metadata; make creation failure visible and retryable. Do not supersede existing alerts before the replacement is safely committed. Read current state/history from the same durable aggregate used for decisions; maintain backward compatibility with the alternate domain model through an explicit mapping, not ad hoc dictionary copies.

**Tester:** Extend [pipeline tests](../../tests/unit/test_communication_pipeline.py#L85) with strict container fakes and crash/restart checkpoints; verify alert/segment foreign keys, no success on write failure, no lost previous version, read-after-restart, and persisted publication timestamps. Add **proposed** tests/integration/test_communication_cosmos.py only if no suitable existing storage test is adopted. Future `V-PIPELINE`, `V-INTEGRATION`.

**Dependencies/completion:** AUD-008-003, AUD-008-022. Complete when accepted alerts can be retrieved with their exact audiences and statuses after process replacement and failed writes cannot masquerade as success.

### AUD-008-010: Connect Review Notification and the Commander Dashboard

- [x] AUD-008-010 Deliver a complete review request to the actual commander workflow and display the persisted draft in the dashboard.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-019, FR-020, FR-031, SC-009; T023, T024, T025, T027, T034; US1-AS1, US2-AS1/AS3/AS4.

**Expected/actual/impact:** [Stage 9](../../apps/agents/communication/pipeline.py#L575) only logs; no caller starts [request_approval](../../apps/agents/communication/approval.py#L44) for produced drafts. The helper sends segment IDs, not reviewable segment details, and swallows publish failure. [Composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L19) renders hard-coded English content and publishes through another API. [MAF gate](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L202) supplies a real publisher alternative, but defaults/failures can become in-memory entries; no integration here transfers the complete Spec 008 draft and audience to the dashboard.

**Developer:** Use one durable approval-request/outbox contract shared with MAF where retained. Include all content, safety/quality flags, audiences, channels, provenance, stale-assessment warning, and commander assignment. Publish failures must remain pending/retryable rather than logged as notified. Bind dashboard previews and actions to the persisted alert version; do not show generic copy or claim delivery merely after publication.

**Tester:** Extend [endpoint tests](../../tests/unit/test_communication_endpoints.py#L78) and [HITL tests](../../tests/integration/test_hitl_round_trip.py#L51) with a six-language draft and complete segments, including one flagged translation. Exercise queue outage/recovery, duplicate request, dashboard reload, and approval of the exact previewed version. Assert published envelope contents and measured notification timestamp. Future `V-AUTH`, `V-INTEGRATION`, `V-WEB`.

**Dependencies/completion:** AUD-008-001, AUD-008-006, AUD-008-009. Complete when real pipeline output becomes reviewable without manually seeding private dictionaries and failed notification cannot be counted as delivered.

### AUD-008-011: Persist Commander Decisions With First-Write-Wins

- [x] AUD-008-011 Make approve, reject, and cancel durable conditional transitions with complete action metadata.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-016, FR-020, FR-033; T022, T023, T025, T026, T027, T058; US2-AS1/AS2, US7-AS2.

**Expected/actual/impact:** [process_approval](../../apps/agents/communication/approval.py#L155) mutates a process-local object before storage and uses unconditional upsert unless an etag is provided. [Endpoint](../../apps/agents/communication/agent.py#L217) never supplies that etag. Reject omits approved_at; cancel never persists. The [double-approval test](../../tests/unit/test_communication_approval.py#L205) is sequential and dictionary-only, not a two-worker conditional-write test.

**Developer:** Read durable alert plus etag in the tenant scope, validate transition and justification, perform a supported conditional storage operation, and only then publish the result/update caches. Return 409 with current status and actioning identity on conflict. Persist trusted actor, action, role, timestamp, and reason for each outcome. Do not leave local state changed after failed writes or permit an approval to overwrite a rejection.

**Tester:** In [approval tests](../../tests/unit/test_communication_approval.py#L33) and [endpoint tests](../../tests/unit/test_communication_endpoints.py#L78), use two workflow instances sharing a conditional fake store. Race approve/reject/cancel, inject storage failure, retry, restart, and test missing/blank justifications. Assert one winner, deterministic 409 details, unchanged loser state, and full durable timestamps. Future `V-AUTH`, `V-INTEGRATION`.

**Dependencies/completion:** AUD-008-001, AUD-008-009, AUD-008-022. Complete when concurrent decisions cannot silently overwrite one another and all action metadata survives restart.

### AUD-008-012: Make Commander Modifications Safe New Versions

- [x] AUD-008-012 Route modifications through validated versioning, refreshed review, and durable persistence.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-007, FR-016, FR-020; T022, T023, T026, T027, T036; US2-AS3, US5-AS4.

**Expected/actual/impact:** [create_modified_version](../../apps/agents/communication/approval.py#L220) increments alert.version locally, accepts arbitrary content-block fields, retains old quality/provenance/expiry metadata, and only inserts into the private pending dictionary. It neither persists nor requests approval. [Modify endpoint](../../apps/agents/communication/agent.py#L307) exposes this directly; no modify test exists in the inspected endpoint suite.

**Developer:** Allocate through the authoritative counter, whitelist editable content/audience fields, record modification_reason and trusted actor, and preserve the immutable original. Revalidate changed text and cross-language consistency without labelling commander edits as previously checked LLM output. Refresh creation/expiry and affected quality metadata; persist the new aggregate and submit it for review. Ensure terminal versions and stale editors have explicit behavior.

**Tester:** Extend [approval](../../tests/unit/test_communication_approval.py#L33) and [endpoint](../../tests/unit/test_communication_endpoints.py#L78) homes for six-language overrides, audience changes, invalid field injection, oversize content, concurrent modification, old expiry, and terminal-state requests. Assert unchanged original bytes, distinct reserved ID, refreshed metadata, review notification, and no inherited approval. Future `V-AUTH`, `V-VERSION`.

**Dependencies/completion:** AUD-008-009, AUD-008-010, AUD-008-019, AUD-008-022. Complete when every modification yields a persisted, safe, separately reviewable version without collisions or stale approval claims.

### AUD-008-013: Implement Durable, Policy-Aligned Escalation

- [x] AUD-008-013 Start and recover approval deadlines using the real commander chain and the Spec 018 authority contract.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-042, FR-CAP-008-003, FR-020, FR-032; T022, T023, T024, T046, T056; CHK016/CHK017/CHK019/CHK070.

**Expected/actual/impact:** [request_approval](../../apps/agents/communication/approval.py#L44) ignores commander_chain and does not start the timer. [Escalation](../../apps/agents/communication/approval.py#L108) invents commander-level IDs, keeps only local timers/history, and logs a critical hold without a durable flag or audit record. [Amendment](spec.md#L366) defers timeout authority to Spec 018; the legacy hard-coded policy is not mapped to that authority. The code does avoid auto-approval, which is a real partial safeguard.

**Developer:** Read real incident command-chain policy, schedule durable deadlines when notification succeeds, recover them after restart, and atomically check pending state before escalation. Persist destination, elapsed time, history, maximum-level hold and review priority; cancel deadlines on terminal actions. Use the portfolio timeout policy or obtain an explicit governance resolution. Never auto-approve at any exhaustion level.

**Tester:** Extend [approval tests](../../tests/unit/test_communication_approval.py#L236) and [HITL round trip](../../tests/integration/test_hitl_round_trip.py#L51) using a controlled clock, actual chain fixture, missing commander, all three levels, approval-at-deadline race, restart, and queue outage. Assert exact destination, durable critical hold, one escalation per deadline, correct audit identity, and no send authorization. Future `V-AUTH`, `V-INTEGRATION`.

**Dependencies/completion:** AUD-008-010, AUD-008-011, AUD-008-037. Complete when an unanswered review reliably reaches the policy-selected next human and exhaustion remains visibly pending.

### AUD-008-014: Decouple Channel Retries and Make Sends Idempotent

- [x] AUD-008-014 Schedule channels independently with bounded retries and stable delivery-operation identities.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-024, FR-026, FR-030, FR-037, NFR-001; T028, T029, T047, T049; US3-AS3, US8-AS3; CHK048/CHK050.

**Expected/actual/impact:** [Nested delivery loop](../../apps/agents/communication/delivery.py#L79) awaits each segment/channel before starting the next, so SMS backoff delays push/broadcast. [Retry](../../apps/agents/communication/delivery.py#L161) uses synchronous SDK calls, generates new record IDs on repeated delivery, never sets in_progress, and only sets health false, never true on recovery. No provider idempotency key addresses an accepted send whose acknowledgement is lost.

**Developer:** Use bounded asynchronous channel workers with independent retries, preserving critical-recipient initiation priority. Use a durable alert-version/tenant/channel/recipient operation key and provider idempotency/reconciliation where available. Record pending, in-progress, retrying and final outcomes consistently, honor configured retry counts beyond the default, clear stale failure reasons on recovery, and emit degradation/recovery notifications.

**Tester:** Add barrier-controlled provider fakes to [delivery tests](../../tests/unit/test_communication_delivery.py#L107). SMS must wait/fail while push and broadcast start independently; assert 1+3 attempts and 1/2/4 backoff, zero retries on success, max-retry overrides, ambiguous success then retry, restart/replay, and recovered channel health. Future `V-DELIVERY`.

**Dependencies/completion:** AUD-008-004, AUD-008-005, AUD-008-015. Complete when one channel's latency cannot hold others and redelivery cannot duplicate already accepted sends.

### AUD-008-015: Report True Aggregate Delivery and Failure State

- [x] AUD-008-015 Persist truthful alert-level delivery state and expose actual per-channel/segment records to commanders.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-027, FR-030, FR-031, FR-037, SC-004, SC-010; T028, T030, T031, T047, T049; EC-06.

**Expected/actual/impact:** [Aggregation](../../apps/agents/communication/pipeline.py#L586) marks an empty result set delivered, all failures partially_delivered, and sets published_at even with no success. [Status endpoint](../../apps/agents/communication/agent.py#L405) always returns pending/zero counts for any ID, omits records, and never reads a store. All-channel failure is not surfaced with critical urgency or left retryable as specified.

**Developer:** Separate authorization/lifecycle state from delivery outcome where needed; resolve the absent alert failed enum through AUD-008-037. Persist attempts and aggregate only meaningful receipts, treating no eligible targets and all failures explicitly. Record actual first initiation/completion timestamps, supported retryability, per-channel health, and commander notifications. Implement tenant-aware status lookup with 404 and the full contract's records/counts/percentage.

**Tester:** Extend [delivery tests](../../tests/unit/test_communication_delivery.py#L54), [pipeline tests](../../tests/unit/test_communication_pipeline.py#L85), and [endpoint tests](../../tests/unit/test_communication_endpoints.py#L205): all succeed, one fail, all fail, pending/in-progress, zero segments, dedup-only, partial receipt, unknown/foreign ID, and recovery retry. Assert exact numerator/denominator, no false published_at, critical failure visibility, and preserved approval authority. Future `V-DELIVERY`, `V-AUTH`.

**Dependencies/completion:** AUD-008-004, AUD-008-009, AUD-008-014, AUD-008-037. Complete when the dashboard can distinguish actual delivery, partial delivery, failed delivery, and simulation without inferred success.

### AUD-008-016: Target Minority Languages and Verified Vulnerable Populations

- [x] AUD-008-016 Produce complete geographic, vulnerability, and language subsegments with operational guidance and data-gap disclosure.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-007, FR-022, FR-023, FR-024, FR-025; T032, T033, T034, T060, T062; US4-AS1/AS2/AS3/AS4.

**Expected/actual/impact:** [Language assignment](../../apps/agents/communication/segmentation.py#L134) selects only the dominant language, so the required 15% zh-Hans subgroup receives no preferred-language segment. [Facility logic](../../apps/agents/communication/segmentation.py#L104) trusts zone_level without spatial membership, ignores the zones argument, and adds no facility-specific guidance. Missing data flags exist but do not become the required alert summary; defaults can invent an empty level-1 zone. [Test](../../tests/unit/test_communication_segmentation.py#L91) only checks a 60% majority.

**Developer:** Resolve demographic/vulnerability inputs from authoritative, freshness-aware repositories and real evacuation geometry. Partition populations by language proportions with en-AU fallback, preserve unique zones, validate facility inclusion, and attach actionable facility guidance. Keep estimations traceable and bounded; surface per-zone missing/stale data to the commander. Persist snapshots through AUD-008-009.

**Tester:** Extend [segmentation tests](../../tests/unit/test_communication_segmentation.py#L11) with three polygons, 80-resident aged care, facilities inside/outside/boundary, 15% zh-Hans plus vi, unknown preference, partial zone data, stale demographics, and no zones. Assert counts, critical priority, guidance, language fallback, estimation totals, and summary warnings. Future `V-SEGMENT`, `V-SCENARIO`.

**Dependencies/completion:** AUD-008-007, AUD-008-009, AUD-008-005. Complete when minority groups and vulnerable facilities are targeted without dropping general populations or hiding missing-data limitations.

### AUD-008-017: Guarantee Approved Template Coverage at Startup

- [x] AUD-008-017 Complete the template matrix and fail safely when approved operational fallback content is unavailable.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-005, FR-007, FR-014, FR-017, FR-036, SC-005; T003, T004, T014, T019, T048; US1-AS3, EC-04.

**Expected/actual/impact:** S7 found 22 entries/19 hazard-type combinations per language, not the requested 28 combinations. Missing in every file: flood/shelter_in_place; storm/shelter_in_place and all_clear; earthquake/shelter_in_place, all_clear, general_warning; tsunami/shelter_in_place, all_clear, general_warning. Only moderate/severe severities exist; real fixtures use high/extreme. [Loader](../../apps/agents/communication/templates.py#L128) falls back to generic English on unmatched keys without the required visible translation-unavailable suffix. [Bootstrap](../../apps/agents/communication/agent.py#L440) catches missing templates and continues. [Image](../../apps/agents/Dockerfile#L29) does not copy the template directory.

**Developer:** Define a reviewed canonical hazard/severity/type mapping and complete all required operational combinations in six languages. Validate entry schema, duplicates, language codes, placeholders and interpolated bounds at startup; package assets in the actual image. Keep a genuine missing-language en-AU fallback visibly labelled, but do not classify unreviewed generic text as pre-approved. Fail readiness/startup when no approved fallback exists, according to the resolved safety policy.

**Tester:** Add template cases to [translator](../../tests/unit/test_communication_translator.py#L86) and [pipeline](../../tests/unit/test_communication_pipeline.py#L85) homes using tmp_path JSON fixtures. Cover the full matrix, all-clear hazards, high/extreme mapping, missing file/entry, malformed object/list, wrong language, duplicate key, oversized placeholder, and absent assets. Assert correct localized action and fail-fast behavior. Future `V-CONTENT`, `V-QUICKSTART`.

**Dependencies/completion:** AUD-008-036 for human approval; AUD-008-031 for packaging. Complete when every supported input has an approved operational fallback and missing assets cannot silently produce mislabeled English alerts.

### AUD-008-018: Preserve Safety Failure Semantics Through Fallback

- [x] AUD-008-018 Carry original safety results forward and select fallback by the actual alert/change type.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-010, FR-011, FR-012, FR-014, FR-017, FR-032; T010, T018, T038, T039, T040; US1-AS2, US6-AS1/AS2/AS3/AS4.

**Expected/actual/impact:** [LLM mixin](../../apps/agents/common/llm_mixin.py#L154) already replaces unsafe output and returns a safety_fallback label but not its specific reason. [Translator](../../apps/agents/communication/translator.py#L190) stores the aggregate result as failure reason. [Stage 7](../../apps/agents/communication/pipeline.py#L375) revalidates safety_fallback text, can turn the original failure into passed, and hard-codes evacuation fallback at line 419. That can change a shelter/all-clear instruction or lose a correction prefix. Validator exceptions bubble to the outer handoff rejection rather than the documented safe degradation. Template-only overall passed disagrees with per-block not_checked.

**Developer:** Keep original result, reason, length and fallback provenance in a typed generation result. Validate each LLM output once at the agreed boundary and aggregate the worst actual result without laundering failures. Preserve hazard, alert type, change type and correction prefix when replacing content; approved templates must remain exempt from repeat validation. Handle validator unavailability with an explicit safe template/not_checked outcome, not a dropped alert.

**Tester:** Extend [pipeline tests](../../tests/unit/test_communication_pipeline.py#L85) and [translator tests](../../tests/unit/test_communication_translator.py#L112) at the LLM-client boundary, not by replacing the whole safety wrapper. Test one/all-six failures, blocked keyword, wrong language, excess length, safety_fallback that passes on recheck, unavailable validator, and shelter/correction/all-clear failures. Assert unchanged triggering reason, correct action, no duplicate checks, and pending_review. Future `V-CONTENT`.

**Dependencies/completion:** AUD-008-017, AUD-008-019, AUD-008-026. Complete when commander previews and audits accurately distinguish safe LLM output, unsafe output replaced by templates, and unchecked pre-approved templates.

### AUD-008-019: Enforce All Required Multilingual Safety Checks

- [x] AUD-008-019 Apply language, factual-instruction, tone, and culturally appropriate safety checks on every retained LLM variant.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-007, FR-010, FR-013, SC-002; T010, T018, T038, T039; US6-AS2/AS3, EC-04.

**Expected/actual/impact:** [Shared validator](../../apps/agents/common/content_safety.py#L98) returns immediately after successful Azure moderation, bypassing expected-language validation. Its [language heuristic](../../apps/agents/common/content_safety.py#L87) accepts any nonempty ar/vi/el/it text and rejects non-ASCII Australian English. Factual and tone helpers exist later in that file but [communication stage 7](../../apps/agents/communication/pipeline.py#L375) never invokes them. Provider moderation alone does not establish the specification's accurate instructions, panic/tone, cultural, or language requirements. This is shared-code impact independently required by Spec 008, not a finding copied from another audit.

**Developer:** Separate local language/length checks from provider moderation so success in one layer cannot bypass another. Use an agreed multilingual detector and reviewed culturally sensitive/panic/instruction criteria; ground factual validation in the retrieved assessment and approved warning tier. Preserve degraded-review flags from keyword fallback, and retain approved-template exemption. Use shared APIs without weakening other agents' existing checks.

**Tester:** Add communication-specific cases in [pipeline](../../tests/unit/test_communication_pipeline.py#L85) and [translator](../../tests/unit/test_communication_translator.py#L112) suites: Azure moderation passes English labelled zh-Hans/ar; legitimate Unicode en-AU; mismatched location/hazard; advice using emergency tone; misleading instructions; multilingual culturally reviewed negative fixtures. Assert every mandatory check participates and only the failing variants fall back. Future `V-CONTENT` plus existing shared-validator regression tests selected by the tester.

**Dependencies/completion:** AUD-008-007, AUD-008-018, AUD-008-036. Complete when each required safety category has an explicit rule/fixture and provider availability does not disable language or factual checks.

### AUD-008-020: Implement Real Back-Translation Quality and Outage Semantics

- [x] AUD-008-020 Compare real back-translations with semantic embeddings and represent unavailable checks without fabricated scores.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-006, FR-006a, FR-036, FR-039; T010, T015, T018, T047, T050; R-002; CHK052.

**Expected/actual/impact:** [Similarity](../../apps/agents/communication/translator.py#L274) is word-frequency cosine, explicitly rejected in spirit by the semantic requirement. [Back-translation](../../apps/agents/communication/translator.py#L228) ignores action_items, can compare fallback English to itself, and on exception returns 0.5 plus a review flag instead of skipping unavailable measurement. [Pipeline](../../apps/agents/communication/pipeline.py#L335) treats the score as measured quality. [Tests](../../tests/unit/test_communication_translator.py#L12) verify word overlap, not an embedding service or outage behavior.

**Developer:** Use the current sanctioned embedding client/model and complete title/body/actions comparison. Inspect the back-translation generation result before scoring; unavailable back-translation or embeddings must produce an explicit unmeasured state, degradation audit, and no measured-failure penalty. Apply 0.9 only to actual below-threshold results, expose per-language review/penalty metadata, and preserve nonblocking human review. Resolve the plan's conflicting template-on-embedding-outage wording through AUD-008-037.

**Tester:** In [translator](../../tests/unit/test_communication_translator.py#L112) and [pipeline](../../tests/unit/test_communication_pipeline.py#L85) homes, inject known vectors, semantic paraphrases, reversed instructions, omitted actions, thresholds 0.849/0.85/0.851, empty/zero embeddings, back-translation fallback, and outage/recovery. Assert no false perfect score, no penalty for unavailable measurement, and exact audit/flag propagation. Future `V-CONTENT`.

**Dependencies/completion:** AUD-008-018, AUD-008-026, AUD-008-037. Complete when the quality score represents the specified measurement and missing measurement cannot masquerade as success or failure.

### AUD-008-021: Apply Freshness Penalties Only When Data Is Stale

- [x] AUD-008-021 Derive freshness from assessment age and preserve deterministic conditional confidence stacking.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-006a, FR-036; T010, T015, T018, T047, T048.

**Expected/actual/impact:** [Stage 8 line 472](../../apps/agents/communication/pipeline.py#L472) always uses freshness_penalty_factor, regardless of age; assessment data is not passed to the confidence calculation. Fresh handoffs lose 10% confidence, and missing/stale timestamps are not distinguished. [Arithmetic tests](../../tests/unit/test_communication_translator.py#L39) prove multiplication but not activation conditions.

**Developer:** Pass the immutable assessment timestamp/freshness evidence to confidence computation, define the staleness threshold and missing-time policy, and use factor 1.0 unless the relevant condition is triggered. Retain order freshness/back-translation/fallback and record original confidence plus factors and reasons. Reconcile confidence_base versus upstream confidence explicitly.

**Tester:** Extend [pipeline tests](../../tests/unit/test_communication_pipeline.py#L85) and [confidence tests](../../tests/unit/test_communication_translator.py#L39) with fresh, exactly-at-threshold, stale, missing, future and timezone-offset timestamps. Assert fresh upstream 0.9 stays 0.9 without other penalties, stale becomes 0.81, and combined penalties apply once. Future `V-CONTENT`, `V-PIPELINE`.

**Dependencies/completion:** AUD-008-007, AUD-008-020, AUD-008-037. Complete when every penalty can be reconstructed from recorded conditions and fresh data is not penalized by default.

### AUD-008-022: Reserve Versions Atomically Across Workers and Tenants

- [x] AUD-008-022 Use a tenant-scoped conditional counter and stop issuing unreserved versions after conflicts.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-015, FR-016, FR-040, FR-041; T011, T016, T022, T036, T057, T058; US1-AS4, US5-AS4.

**Expected/actual/impact:** [assign_version](../../apps/agents/communication/versioning.py#L42) keys by incident only, writes the incident as tenant_id in counter documents, and after retries calls [_fallback_version](../../apps/agents/communication/versioning.py#L127), which returns current+1 without reserving it or returns 1 on failure. Concurrent workers can receive the same version. The if_match call shape must also be proven against the chosen Cosmos adapter; permissive objects are not SDK evidence. [Version tests](../../tests/unit/test_communication_versioning.py#L11) only use local counters.

**Developer:** Add mandatory tenant scope, align counter partition with public-alerts, and use a supported conditional replace/create API. Retry only actual conflict cases with bounded jitter; after exhaustion return a retryable error rather than an unreserved number. Use the same allocator for handoffs and commander changes; preserve immutable alert creation and avoid unconditional status upserts.

**Tester:** Extend [version tests](../../tests/unit/test_communication_versioning.py#L11) using an etag-enforcing fake and **proposed** Cosmos integration test from AUD-008-009. Exercise concurrent first-create, 412 conflicts, retry exhaustion, timeout, restart, and identical incident IDs across tenants. Assert unique monotonic reserved IDs and no alert creation after failed reservation. Future `V-VERSION`, `V-INTEGRATION`.

**Dependencies/completion:** AUD-008-003, AUD-008-009. Complete when every returned version is durably reserved exactly once in the correct scope.

### AUD-008-023: Implement Explicit Update and Correction Lifecycle

- [x] AUD-008-023 Create immutable updates/corrections and resolve approved-alert supersession timing explicitly.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-016, FR-017, FR-018; T035, T036, T037, T061; US1-AS4, US2-AS4, US5-AS1/AS2/AS4.

**Expected/actual/impact:** [Stage 8](../../apps/agents/communication/pipeline.py#L455) trusts change_type instead of deriving update from history, turns absent change_summary/reference into the literal string None, and supersedes the previous alert before replacement persistence. [supersede_previous](../../apps/agents/communication/versioning.py#L138) mutates approved/delivering states despite US2-AS4. [Lifecycle helpers](../../apps/agents/communication/versioning.py#L179) return IDs only; they do not construct the required records. Correction-title generation exists, but [prefix tests](../../tests/unit/test_communication_translator.py#L86) only assert a local dictionary is nonempty.

**Developer:** Derive initial/update from authoritative history, validate explicit correction requests/references, build meaningful change summaries, and preserve original content. Obtain a governance decision on FR-018 versus US2-AS4 before changing supersession timing; replacement persistence and review must not silently retire an approved warning. Preserve correction identification in every language after safety fallback and retain full approval/history metadata.

**Tester:** Extend [version tests](../../tests/unit/test_communication_versioning.py#L58), [translator tests](../../tests/unit/test_communication_translator.py#L86), and [bushfire scenario](../../tests/unit/test_bushfire_alert_scenario.py#L19). Exercise v1-v4, actual translated prefixes, missing/literal-None references, failed replacement writes, concurrent drafts, approved predecessor and correction rejection. Assert original bytes remain and only policy-authorized state transitions occur. Future `V-VERSION`, `V-SCENARIO`.

**Dependencies/completion:** AUD-008-008, AUD-008-009, AUD-008-018, AUD-008-022, AUD-008-037. Complete when updates and corrections have correct lineage, review, titles and resolved supersession behavior.

### AUD-008-024: Scope All-Clear to the Original Audience and Threat

- [x] AUD-008-024 Generate all-clear from the referenced alert, retain its audience, and require confirmation for active sub-zone warnings.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-017, FR-020; T035, T036, T037, T061; US5-AS3, EC-08.

**Expected/actual/impact:** [All-clear helper](../../apps/agents/communication/versioning.py#L199) allocates an ID only. [Pipeline drafting](../../apps/agents/communication/pipeline.py#L298) defaults alert_type to evacuation independently of change_type. No path retrieves the original audience, validates active sub-zones, or supersedes the referenced alert after confirmed all-clear delivery. The separate [AWS build_all_clear](../../apps/agents/communication/warning_builder.py#L139) is English-only on a different model and is not a replacement for these obligations. S1/S2/S4/S5 searched.

**Developer:** Resolve the original same-tenant alert and immutable audience snapshot, select dedicated hazard-specific all-clear templates, and explicitly warn/require commander confirmation when sub-zone alerts remain. Prevent cross-incident, cancelled or already terminal references from silently clearing unrelated warnings. Supersede only the referenced scope after the agreed successful delivery threshold; do not invent unconditional return-to-safety instructions when official restrictions remain.

**Tester:** Extend [bushfire scenario](../../tests/unit/test_bushfire_alert_scenario.py#L19) and [version tests](../../tests/unit/test_communication_versioning.py#L75): changed current demographics, original audience retention, active sub-zone, absent confirmation, cross-tenant/reference mismatch, rejected/cancelled original, partial/all-channel failure. Assert correct all-clear text, review, targeting and post-delivery supersession. Future `V-VERSION`, `V-SCENARIO`.

**Dependencies/completion:** AUD-008-009, AUD-008-015, AUD-008-017, AUD-008-023, AUD-008-037. Complete when an all-clear cannot silently clear a still-active sub-zone or target a newly recomputed audience.

### AUD-008-025: Enforce Time-Based Expiry and Durable History

- [x] AUD-008-025 Schedule expiry from persisted deadlines and expose complete immutable incident version history.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-016, FR-017, FR-018, FR-038; T035, T036, T037, T053; US5-AS4; CHK024/CHK029.

**Expected/actual/impact:** [expire_alert](../../apps/agents/communication/versioning.py#L209) never checks time and has no production caller in S5. [History helper](../../apps/agents/communication/versioning.py#L234) exists, but [agent GET](../../apps/agents/communication/agent.py#L392) exposes only local pending objects, not history. No periodic expiry job was found; [test](../../tests/unit/test_communication_versioning.py#L106) only expects empty history with no Cosmos.

**Developer:** Implement a restart-safe scheduler or repository operation that evaluates expires_at in UTC and transitions eligible alerts exactly once. Keep superseded and expired independent terminal reasons, obey resolved pre-delivery expiry policy, and preserve all historical content/approvals. Expose tenant-scoped ordered version history through the chosen API and dashboard.

**Tester:** In [version tests](../../tests/unit/test_communication_versioning.py#L88), use a controlled clock and durable fake store: just before/at/after 24h, configured TTL, restart, superseded/cancelled/rejected records, concurrent replacement, and versions v1-v4. Assert no premature expiry, idempotent transition, reason audit, and full chronological retrieval. Future `V-VERSION`, `V-AUTH`.

**Dependencies/completion:** AUD-008-009, AUD-008-022, AUD-008-023, AUD-008-037. Complete when expiry is time-driven rather than caller-driven and history remains queryable after restart.

### AUD-008-026: Make Audit Coverage Complete and Correlated

- [x] AUD-008-026 Emit structured audit records for every real processing decision and reconcile expected records by handoff/alert.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-032, FR-033, FR-035, SC-006; T012, T017, T024, T029, T038, T045, T046, T048, T049, T050, T051; US7-AS1/AS2/AS3/AS4.

**Expected/actual/impact:** [Stage 11](../../apps/agents/communication/pipeline.py#L637) emits a second handoff_received record, not reconciliation or flush. [Audit helper](../../apps/agents/communication/pipeline.py#L658) permits absent generation/duration/correlation. Source lacks real emissions for multiple declared types, including template_fallback, content_safety_failure, delivery_initiated, escalation_triggered and health_status_changed in their owning paths; logger/custom events do not substitute for decision records. Delivery audits contain channel/status but not segment, language, retry details, content or approval mode. [Audit tests](../../tests/unit/test_communication_audit.py#L18) only prove generic writer calls.

**Developer:** Define expected decisions per accepted/rejected/degraded path and use a shared correlation envelope through asynchronous approval/delivery. Include IDs, trusted actor/action metadata, per-language original safety results, generation/model/config/input versions, stage duration, outbound audience/content/channel/approval mode, retry outcomes, and degradation/recovery transitions. Reconcile against stored record IDs/counts; do not count two received events as complete coverage. Avoid unnecessary recipient PII.

**Tester:** Extend [pipeline](../../tests/unit/test_communication_pipeline.py#L85), [audit](../../tests/unit/test_communication_audit.py#L18), and [scenario](../../tests/unit/test_cyclone_alert_scenario.py#L15) homes with a capturing append-only store. Assert exact expected decision sets for success, rejection, dedup, mixed safety, escalation, each attempt outcome and recovery; remove one record and prove reconciliation detects it. Future `V-AUDIT`, `V-SCENARIO`.

**Dependencies/completion:** AUD-008-003 and each owning workflow fix. Complete when every real state-changing/quality decision is reconstructible with same-tenant handoff/alert linkage and omissions are detected.

### AUD-008-027: Recover Audit Buffers Without Loss or False Health

- [x] AUD-008-027 Integrate reliable three-tier replay, truthful tier accounting, and auditable recovery transitions.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-033, FR-034, FR-039; T041, T042, T043, T044, T045, T051, T052; US7-AS4, US8-AS4.

**Expected/actual/impact:** [Writer](../../apps/agents/communication/audit.py#L42) uses create_item and bounded memory/file fallback, which is real source support. But direct flush_source is set after the persisted write; [flush](../../apps/agents/communication/audit.py#L108) continues to the file after an older memory record fails, rewrites the spill file nonatomically, and does not handle already-written duplicate IDs as successful replay. No pipeline recovery/periodic caller exists. [_file_spill_count](../../apps/agents/communication/audit.py#L165) never resets, buffer_depth excludes file records, and tier changes are logs rather than audit records.

**Developer:** Preserve append-only primary semantics with idempotent replay by stable record ID. Resume chronologically, stop at failed older writes where ordering is required, and safely retain spill content through crash/partial rewrite. Add periodic/recovery flush lifecycle, include live file depth, update tier after actual draining, and emit transition records without recursive failure loops. Make unrecoverable local write failure visible, not silently swallowed.

**Tester:** Extend [audit tests](../../tests/unit/test_communication_audit.py#L111) with controlled primary failure/recovery, small buffer, old spill file on restart, disk-full/permission errors, duplicate Cosmos IDs after ambiguous acknowledgement, and crash during replay. Assert stable IDs, no lost/duplicated decisions, chronological order, correct direct annotations, accurate memory+file depth, recovery health and transition audits. Future `V-AUDIT`.

**Dependencies/completion:** AUD-008-026, AUD-008-029. Complete when all buffered records can recover durably and health reflects the actual outstanding backlog.

### AUD-008-028: Make the Capacity Limit Nonblocking and Testable

- [x] AUD-008-028 Run drafting and delivery asynchronously with bounded admission and correct overload responses.

**Priority/status:** P1 / PARTIAL. **Affected:** NFR-001, FR-001, FR-038, SC-001, SC-007; T005, T019, T052, T055; CHK035/CHK038/CHK039.

**Expected/actual/impact:** [HTTP handler](../../apps/agents/communication/agent.py#L186) creates an asyncio semaphore but calls synchronous process_handoff inside the event loop. The [translator](../../apps/agents/communication/translator.py#L38) and provider calls are synchronous; the admission check alone does not establish 50 concurrent operations or responsive health. No load assertion checks the 51st request or event-loop fairness in the inspected endpoint/pipeline tests.

**Developer:** Use a genuinely asynchronous pipeline/client boundary or a bounded executor compatible with the service lifecycle; do not rely on private semaphore fields as the only admission control. Keep en-AU-first translation within each alert while allowing independent alerts and channels to progress. Distinguish queued from active/completed work, release capacity on every failure/cancellation, and return stable 429/retry semantics without acknowledging away queued work.

**Tester:** Extend [endpoint](../../tests/unit/test_communication_endpoints.py#L46) and [pipeline](../../tests/unit/test_communication_pipeline.py#L85) tests with barrier-controlled fake dependencies: 50 active distinct alerts, 51st rejected, completion frees capacity, cancellation/failure releases slots, and /health responds while all drafts wait. Later measure under V-PERFORMANCE; unit behavior first with `V-PIPELINE`.

**Dependencies/completion:** AUD-008-006, AUD-008-007, AUD-008-014, AUD-008-033. Complete when concurrency is demonstrated independently of mock-fast execution and overload cannot starve health or lose handoffs.

### AUD-008-029: Report Real Dependency Health and Recovery

- [x] AUD-008-029 Replace hard-coded health with bounded observed checks and current operational counts.

**Priority/status:** P1 / CONFLICT. **Affected:** FR-034, FR-037, FR-038, FR-039, SC-007; T047, T049, T051, T052; US8-AS2/AS3/AS4, EC-09.

**Expected/actual/impact:** [Health](../../apps/agents/communication/agent.py#L140) hard-codes LLM/Cosmos/SMS/push healthy, uses processed_count as queue depth, and fixes delivery/dedup counts at zero. It never returns 503 for critical outage and publishes writer health words instead of either documented tier enum. No owner invokes comprehensive recovery detection; channel flags never restore. [Health tests](../../tests/unit/test_communication_endpoints.py#L46) only check 200/version/hash.

**Developer:** Implement cached/bounded dependency probes and truthful unavailable/not-configured states; compute status from the resolved contract, not constant defaults. Report pending approvals, active deliveries, pending queue depth, dedup size and actual audit tier. Detect healthy/unhealthy transitions with downtime and audit/custom events; resume work/flush on recovery. Do not perform long remote calls synchronously in /health.

**Tester:** Add a health matrix for each failed dependency, all channels down, Cosmos down, missing configuration, probes timing out, backlog after recovery and counts across admission/completion. Assert exact status/HTTP code/tier/last_checked fields and one recovery event. Extend [endpoint tests](../../tests/unit/test_communication_endpoints.py#L46); future `V-AUTH`, `V-AUDIT`, `V-PERFORMANCE`.

**Dependencies/completion:** AUD-008-013, AUD-008-015, AUD-008-027, AUD-008-028, AUD-008-037. Complete when health no longer reports readiness for unavailable/uninitialized dependencies and responds within the measured SLA.

### AUD-008-030: Instrument Actual Metrics, Events, and SLA Boundaries

- [x] AUD-008-030 Wire the telemetry exporter and all required measurements/events to real processing transitions.

**Priority/status:** P1 / PARTIAL. **Affected:** NFR-002, SC-001, SC-004, SC-006, SC-009, SC-010, SC-011; T045, T051, T054, T055, T056.

**Expected/actual/impact:** [Telemetry definitions](../../apps/agents/communication/telemetry.py#L112) exist, but several names/types differ from the contract, including success counts instead of rates, approval_wait_time seconds instead of milliseconds, and active-alert names. Most approval/delivery/degradation instruments and event helpers are not called. [Pipeline draft timing](../../apps/agents/communication/pipeline.py#L298) excludes template/back-translation/safety stages; placeholder alert IDs are emitted. No exporter initialization appears in the communication bootstrap. Active/pending counters only increment in the pipeline.

**Developer:** Initialize the sanctioned exporter/resource once in the chosen runtime, propagate message correlation, and align names, units, labels, denominators and gauge semantics with the contract. Emit real stage and per-language/channel spans plus all 17 events at their owners. Measure stages 4-7, stages 1-9, notification, approval wait, first send and first completion separately; explicitly exclude approval wait from end-to-end. Record delay events without dropping alerts and keep identifiers/cardinality/PII controlled.

**Tester:** Use an in-memory telemetry exporter/fake meter in existing [pipeline](../../tests/unit/test_communication_pipeline.py#L85), [delivery](../../tests/unit/test_communication_delivery.py#L54), and [approval](../../tests/unit/test_communication_approval.py#L33) tests. Assert instrument schema, spans/correlation, balanced active/pending gauges, correct latency intervals, rates with denominators, events on failure/recovery, and no pending placeholder IDs after creation. Future `V-TELEMETRY`.

**Dependencies/completion:** AUD-008-010, AUD-008-013, AUD-008-014, AUD-008-026, AUD-008-028, AUD-008-037. Complete when every contract signal has a demonstrated emitting path and an operational alert-rule owner; definitions alone do not close this task.

### AUD-008-031: Connect and Correct the Deployment Contract

- [ ] AUD-008-031 Compose a deployable communication runtime with its resources, identity, configuration, scaling, and regional boundaries.

**Priority/status:** P1 / PARTIAL source; deployed state UNVERIFIED. **Affected:** NFR-001, NFR-003, FR-026, FR-034, FR-038; T002, T019, T063, T064.

**Expected/actual/impact:** S6 finds [communication-agent.bicep](../../infra/modules/communication-agent.bicep#L71) only as a standalone declaration. It has three /tenant_id containers with no TTL and two queues, but [env](../../infra/modules/communication-agent.bicep#L189) supplies mismatched service names, broadcast rather than emergency_broadcast, and no EAS/SMS/push configuration. [Scaling](../../infra/modules/communication-agent.bicep#L209) explicitly replaces queue scaling with HTTP concurrency. Its identity lacks local ACR-pull/ACS grants in the inspected module and uses broad cognitive-services scope; role IDs/actual grants require later validation. [Image command](../../apps/agents/Dockerfile#L48) starts dispatcher on 8080 and omits template assets. No regional isolation is established by an unrestricted location parameter.

**Developer:** After choosing the runtime, compose the module or documented replacement from the active infrastructure entrypoint. Reconcile ports/image assets and environment names with the actual constructors; configure sender/push/EAS and durable volumes if file fallback is retained. Apply repository AVM/policy/least-privilege rules, verified role definitions, AU resource locations, scoped data/queue boundaries and the resolved queue-depth scale policy. Do not infer permission from a declared managed identity or weaken current Azure policy to fit the module.

**Tester:** Later inspect the compiled resource graph and what-if under separate authorization, checking three containers/retention, named queues, correct image/port/probes, target env, identity scopes, ACR access, approved channel credentials, scale-out >10 and scale-in <3 for 5 minutes or an approved replacement. Verify regional independence with isolated fixtures; no live test in this audit. Future `V-INFRA`, then `V-QUICKSTART` only after all P0 gates close.

**Dependencies/completion:** AUD-008-006, AUD-008-017, AUD-008-028, AUD-008-029, AUD-008-037. Complete when active deployment composition actually provisions/starts the intended service and later authorized evidence verifies it; standalone Bicep is not deployment proof.

### AUD-008-032: Preserve Actionable Multilingual Channel Content

- [x] AUD-008-032 Format SMS/push/broadcast without discarding critical actions and compute SMS segmentation for actual encoding.

**Priority/status:** P1 / PARTIAL. **Affected:** FR-007, FR-028, FR-029; T028, T029, T060, T061; US3-AS1/AS2/AS4, EC-05.

**Expected/actual/impact:** [Formatter](../../apps/agents/communication/delivery.py#L251) slices the start of title/body/actions to 612 characters, potentially dropping all actions and help; it appends no full-alert link. [SMS count](../../apps/agents/communication/delivery.py#L208) always divides by 153, including a 160-character GSM-7 single message, and ignores Unicode encoding despite six-language content and Unicode punctuation. Push excludes action_items, and broadcast does not switch to the English block. [Length test](../../tests/unit/test_communication_delivery.py#L67) only asserts a maximum.

**Developer:** Establish channel contracts that preserve hazard/location/action/help, reserve space for an approved details link where required, and use actual GSM-7/UCS-2/provider encoding semantics rather than claiming four parts for every 612-character message. Keep the complete source content immutable. Align push/broadcast payload constraints, actual language_used, and receipt metadata. Resolve research R-005's rejection of links versus FR-028 through AUD-008-037.

**Tester:** Extend [SMS/broadcast tests](../../tests/unit/test_communication_delivery.py#L54) for 153/160/161 boundaries, Chinese/Arabic/accented content, extension characters, long URLs, long location/title, actions at the end, and missing preferred language. Assert emergency action/help remain, payload plus link fits, accurate encoding/part count, actual en-AU broadcast, and push action content. Future `V-DELIVERY`.

**Dependencies/completion:** AUD-008-004, AUD-008-017, AUD-008-037. Complete when recipients retain operational instructions within real channel constraints, not just a passing string-length assertion.

### AUD-008-033: Validate Configuration and Output Invariants

- [x] AUD-008-033 Enforce supported configuration ranges, primary-language ordering, and complete alert/entity validation.

**Priority/status:** P2 / PARTIAL. **Affected:** FR-005, FR-008, FR-015, FR-020, FR-023, FR-027, FR-033, NFR-001; T005, T006, T007, T008, T010, T015, T021.

**Expected/actual/impact:** [Config](../../apps/agents/communication/config.py#L98) validates only later LLM fields; list fields remain mutable despite frozen dataclass and empty/invalid languages/channels, negative capacity/thresholds and excessive escalation levels are accepted. [Translator order](../../apps/agents/communication/translator.py#L58) follows supplied CSV order, so en-AU may not be first. [Models](../../apps/agents/communication/models.py#L250) permit empty content/segments/channels and empty provenance; the declared state-transition table is not enforced on assignment. Per-language score/language, delivery-attempt bounds and required audit metadata are incompletely constrained. [Model test](../../tests/unit/test_communication_models.py#L456) positively asserts empty content is valid.

**Developer:** Define startup ranges and cross-field constraints, normalize en-AU to first (or reject invalid order), require approved language resources, and make collection configuration truly immutable. Validate operational PublicAlert completeness independently of any draft-building convenience type. Enforce allowed transitions at mutation boundaries and constraints for scores, languages, references, attempts, nonempty reasons and audit metadata. Preserve explicit empty intermediate types only where they cannot reach persistence/review/delivery.

**Tester:** Extend [config](../../tests/unit/test_communication_config.py#L11) and [model](../../tests/unit/test_communication_models.py#L403) tests with every documented parameter, zero/negative/out-of-range values, CSV reordering/duplicates, missing en-AU, unsupported language/channel, list mutation, empty alerts, invalid scores/attempts, rejected-state metadata and JSON round trips. Assert hashes change with every active setting and operational invariants reject invalid records. Future `V-MODELS`, `V-CONTENT`.

**Dependencies/completion:** AUD-008-022, AUD-008-037. Complete when configuration fails early for impossible operation and invalid/intermediate records cannot enter the durable approval/delivery workflow.

### AUD-008-034: Replace Assertion Gaps With Connected Contract and Scenario Tests

- [x] AUD-008-034 Complete the original test obligations using actual entrypoints and precise assertions, retaining relocated test homes.

**Priority/status:** P2 / PARTIAL; Cosmos/intake integration assertions MISSING in S5. **Affected:** T007, T008, T009, T010, T011, T012, T020, T021, T022, T027, T028, T032, T035, T038, T041, T047, T057, T058, T059, T060, T061, T062; all base FRs and US1-US8 acceptance coverage.

**Expected/actual/impact:** Existing tests deserve credit but many contradict task descriptions: [pipeline](../../tests/unit/test_communication_pipeline.py#L86) uses one language/no stores; [handoff](../../tests/unit/test_communication_handoff.py#L34) accepts evacuation and omits required references; [correction test](../../tests/unit/test_communication_translator.py#L89) asserts constants; [bushfire](../../tests/unit/test_bushfire_alert_scenario.py#L47) lacks its four-version sequence; [flood](../../tests/unit/test_flood_alert_scenario.py#L123) accepts success or failure. [MAF HITL](../../tests/integration/test_hitl_round_trip.py#L51) uses in-memory queues and a mock draft, not the intake/receipt pipeline. [ATSI test](../../tests/integration/test_communication_agent_atsi_cald.py#L83) tests FakeRetrievalService directly; [WCAG test](../../tests/integration/test_alert_template_wcag.py#L13) tests another seed directory. None establish Spec 008's missing obligations.

**Developer:** Implement fixes before declaring their original tasks complete; avoid replacing domain logic with test mocks. Retain relocated unit files unless a deliberate test taxonomy change is approved. Introduce adapter contract tests for SDK/storage shapes and an integrated draft-review-deliver harness with strict fake external boundaries. Add **proposed** tests/integration/test_communication_service_bus.py and tests/integration/test_communication_cosmos.py only where no current home fits.

**Tester:** Use canonical risk handoffs, six distinct language fixtures, real template loader, tenant-aware conditional stores, a deterministic clock and captureable providers. Implement all 32 acceptance scenarios and nine edges below with exact positive/negative assertions; cover original missing concurrency, escalation, recovery, safety, versioning and receipt conditions. Cyclone must traverse hospital targeting/approval/delivery/audit; bushfire v1-update-correction-all-clear; flood minority-language/dedup/LLM-outage recovery. Future all relevant `V-*` suites; record collected/skipped cases explicitly.

**Dependencies/completion:** Depends on each relevant behavioral follow-up, not a license to weaken tests to current defects. Complete when every original test task has mapped executable assertions and skipped/in-memory-only tests are not counted as live integration proof.

### AUD-008-035: Obtain Reproducibility, Performance, and Quickstart Evidence

- [ ] AUD-008-035 Collect version-bound execution evidence for all success criteria and the full quickstart after correcting the harness.

**Priority/status:** P2 / UNVERIFIED. **Affected:** SC-001 through SC-011, NFR-001, NFR-003; T057, T058, T059, T060, T061, T062, T064; HYP-006.

**Expected/actual/impact:** No local execution/sign-off record proves these outcomes. [Benchmark fixture](../../tests/benchmark/test_pipeline_performance.py#L165) shares a dedup cache and uses an unconfigured MagicMock translator; [benchmark call](../../tests/benchmark/test_pipeline_performance.py#L219) repeatedly sends one ID without asserting an alert, so later iterations can measure discard. [Reproducibility test](../../tests/unit/test_communication_reproducibility.py#L13) proves two empty counters assign v1, not deterministic six-language output/input snapshots. T064's checkbox is not evidence that the [nonstarting quickstart](quickstart.md#L148) ran.

**Developer:** Fix the measurement harness to use distinct accepted handoffs or explicitly reset controlled state, assert successful complete outputs, freeze input/template/config/model versions, and separate mock-fast timings from sandbox timings. Add source-stage/notification/first-delivery timestamps and approval-wait exclusion. Repair quickstart commands only under later authorization, using the chosen runtime and current configuration.

**Tester:** After behavioral gates close, record revision, environment, dependency/model/template versions, commands, collected/passed/skipped tests, per-stage p50/p95/p99, 50-concurrent/51st-overload observations, 95% reach within 5 minutes, zero outage drops, health <=1s, notification <=5s, initiation <=10s, E2E <=60s excluding review wait, and reconciliation counts. Run a structured commander exercise for >=90% clarity/actionability/targeting, retaining sample size and approvals. Future `V-PERFORMANCE`, `V-QUICKSTART`, `V-EXERCISE`; no fabricated approvals or retrospective checkbox edits.

**Dependencies/completion:** All relevant implementation fixes and AUD-008-034/AUD-008-037. Complete only with inspectable, attributable records; a benchmark file, passing stub, or task checkmark is not completion evidence.

### AUD-008-036: Establish Template and Amendment Sign-Off Evidence

- [ ] AUD-008-036 Record verifiable operational approval and amendment preconditions without promoting deferred work prematurely.

**Priority/status:** P2 / UNVERIFIED. **Affected:** FR-014, FR-036, FR-CAP-008-001/002, SC-008; T003, T004, T064; PER-016/017/018, HYP-006/027/028/029, SCP-019/020/021; CHK014/CHK068/CHK072.

**Expected/actual/impact:** [Research governance](research.md#L86) requires PR-reviewed pre-approved templates, but S7 found no template-specific approver/revision evidence. The six JSON files do not prove native-language or operational review. [Local HYP records](evidence/HYP-027.md#L17) say Not tested, and the [rubric hypothesis](spec.md#L350) points to a stub absent in S8. Persona validated labels and aggregate baseline text are not interview, consultation, or post-change grading evidence.

**Developer:** Define owners and an offline change-control record that binds template content/hash/version to operational and native-language approvals. Preserve non-AU preconditions, country-specific safety/a11y review and >=1% back-translation audit obligations; do not enable packs merely because a seed fixture exists. Repair/link the missing HYP-006 evidence stub in a later authorized documentation change, preserving its untested status until measured.

**Tester:** Review actual PR/approval records for every used template family, native-language equivalence and accessibility criteria, not only schema presence. Confirm deferred PH/JP/BD work stays disabled until recorded D-009/regulatory/SME gates clear; country measurements must meet their own windows and falsification thresholds. Compare named pre/post rubric evidence and persona validation records. Future `V-EXERCISE` and document-only governance review; no new delegation in this audit.

**Dependencies/completion:** AUD-008-017, AUD-008-035, AUD-008-037. Complete when approval and amendment statuses have attributable evidence or remain explicitly unverified/deferred without unsupported completion claims.

### AUD-008-037: Resolve Conflicting Requirements and Stale Review Claims

- [ ] AUD-008-037 Obtain an explicit contract resolution and correct documentation traceability in a later authorized change.

**Priority/status:** P2 / CONFLICT. **Affected:** FR-003, FR-006, FR-006a, FR-014, FR-016, FR-017, FR-018, FR-028, FR-030, FR-038, FR-042, NFR-001, FR-CAP-008-003; T005, T022, T028, T035, T037, T050, T052, T055, T063, T064; all review claims assessed below.

**Expected/actual/impact:** [FR-018](spec.md#L219) says supersede on creation while [US2-AS4](spec.md#L68) protects an approved version; FR-003 incident/hazard suppression conflicts with successive versions. [Pipeline budgets](contracts/communication-pipeline.md#L11) allocate 1+15+5+3=24s to drafting but label it <=20s, and stages 1-9 sum to 40s rather than 35s. [Research R-005](research.md#L53) rejects URL truncation required by FR-028. The plan says use template on embedding outage while research/tasks say retain LLM text unmeasured. All-channel failed is requested without an AlertStatus value. FR-038 uses primary/secondary/tertiary, the health contract cosmos/memory/file, and quickstart shows degraded when the contract says unhealthy. T005 says 26 config variables whereas the data-model table enumerates 24; telemetry says 23 metrics while its table contains 22. Template schema omits the alert_type key that selection requires. Several plan CHK citations refer to unrelated original questions.

**Developer:** Have the designated requirements/operational owners choose explicit behavior and document rationale, current runtime/cutover contract, full config/schema/status mapping, SDK naming, and Spec 018 timeout ownership. Reconcile all affected acceptance criteria, examples, checklists, plan gates and tests in a later authorized scope; do not rewrite original evidence during this audit. Keep NN human-approval and tenant safeguards unchanged while resolving ambiguity.

**Tester:** Independently cross-check every resolved rule against this report's coverage tables. Verify arithmetic, enum membership, exact original checklist numbering, template selection keys, future commands and task counts; require approval evidence for behavior-changing resolutions. Document-review validation is future `V-DOCS`; no product test can settle a governance contradiction by itself.

**Dependencies/completion:** This is a prerequisite for ambiguous lifecycle/SLA/health/escalation fixes. Complete when one consistent, approved acceptance contract exists and stale PASS statements are backed or explicitly qualified.

### AUD-008-038: Ground Draft Content and Enforce the Real Output Budget

- [x] AUD-008-038 Carry the complete safety-relevant source context into scoped prompts and enforce token limits without dropping essential instructions.

**Priority/status:** P2 / PARTIAL. **Affected:** FR-006, FR-007, FR-008, FR-009, FR-013; T010, T015, T018, T038; EC-04; US1-AS1, US6-AS1.

**Expected/actual/impact:** [Primary prompt](../../apps/agents/communication/translator.py#L116) includes hazard/severity/type/location but omits provided time, severity detail, wind, help and recommendation rationale. It hard-codes 180 in prose despite configurable budget. [Shared system prompt](../../apps/agents/common/llm_client.py#L185) is general emergency response, not specifically alert drafting. [Token trimming](../../apps/agents/common/llm_mixin.py#L124) removes 20% of characters rather than proving the configured token maximum; parsing at [translator line 160](../../apps/agents/communication/translator.py#L160) can discard fields/extra separators before final validation. A title/body skeleton does not establish what/where/when/do/help or injection resistance.

**Developer:** Build an explicit typed drafting context from validated provenance, keep untrusted source fields separate from role instructions, and scope all generation/back-translation prompts to the required task. Ensure the en-AU reference carries complete factual content for translations. Use a supported token-count/structured-generation policy with an actionable fallback when truncation would corrupt instructions; preserve max-token, length and safety semantics rather than independently slicing arbitrary fields.

**Tester:** Extend [translator tests](../../tests/unit/test_communication_translator.py#L112) and [pipeline tests](../../tests/unit/test_communication_pipeline.py#L85) with prompt-capture fixtures, malicious instructions in location/summary, Unicode/token-heavy output, missing delimiters, extra delimiters, truncated action/help, and nondefault budgets. Assert full supplied facts enter the scoped request, all variants preserve them, unsafe or incoherent output falls back, and the final token/character budgets are met. Future `V-CONTENT`; shared-mixin regression checks must be selected because other agents use it.

**Dependencies/completion:** AUD-008-007, AUD-008-017, AUD-008-018, AUD-008-019, AUD-008-033. Complete when actionable factual content and actual output budgets are verified at the generation boundary, not inferred from a prompt string.

## Remediation Outcome (2026-09-17)

- **Implemented source findings:** 34 of 38.
- **Open:** AUD-008-031 is governance-blocked; AUD-008-035 and AUD-008-036 require external execution/human evidence; AUD-008-037 requires owner approval of the recorded contract resolution.
- **Security and ownership:** Entra JWT validation, service/commander role checks, canonical tenant binding, tenant-partitioned dedup/version/audit state, and persisted version-specific approval are enforced before side effects.
- **Workflow and durability:** The runnable service now validates authoritative handoffs, persists complete alert aggregates and approval outbox records, recovers notification/deadline/audit work, applies ETag transitions, and exposes actual history and delivery records.
- **Delivery and safety:** Configured ACS, targeted push, and authenticated EAS paths inspect receipts; overlap handling preserves nonshared recipients; templates, multilingual safety, semantic back-translation, freshness, lifecycle, and channel formatting are fail-closed or explicitly unmeasured.
- **Validation:** The complete communication source suite passed 382 tests with two upstream Starlette/AnyIO deprecation warnings. Focused web integration passed 2 tests. The corrected benchmark is dependency-blocked because `pytest-benchmark` is unavailable locally. Browser, staging, provider, load, and human-review evidence remain unverified.

## Original Task Coverage

Every original checkbox is preserved as `[x]` below. These are historical task states, not completion endorsements. Each task has its own row; no ranges stand in for individual tasks. Referenced follow-up IDs are the unchecked actions above.

| Original task | Original state | Review status | Concrete source/test evidence and remaining obligation | Follow-up IDs |
| --- | --- | --- | --- | --- |
| T001 | [x] | PARTIAL | [Package](../../apps/agents/communication/__init__.py#L3) exports config/version, not CommunicationAgent; [skipped contract](../../tests/contract/test_communication_llm.py#L4) acknowledges absence. | AUD-008-006, AUD-008-034 |
| T002 | [x] | PARTIAL | [Dependencies](../../apps/agents/pyproject.toml#L10) declare SMS/numpy; push SDK/integration is absent in S1/S3; installation not verified. | AUD-008-004, AUD-008-031 |
| T003 | [x] | PARTIAL | [en-AU entries](../../data/alert-templates/en-AU.json#L1): 22 templates/19 of 28 hazard-type combinations; operational approval not established. | AUD-008-017, AUD-008-036 |
| T004 | [x] | PARTIAL | [zh-Hans entries](../../data/alert-templates/zh-Hans.json#L1) and five-language S7 inventory match 19 combinations; no proof of reviewed semantic equivalence. | AUD-008-017, AUD-008-036 |
| T005 | [x] | PARTIAL | [Config](../../apps/agents/communication/config.py#L20) reads/hashes values but lacks operational range validation/connection binding; [tests](../../tests/unit/test_communication_config.py#L11) cover a subset. | AUD-008-031, AUD-008-033, AUD-008-037 |
| T006 | [x] | PARTIAL | [Models](../../apps/agents/communication/models.py#L25) define enums/entities; [empty content allowed](../../apps/agents/communication/models.py#L300), required metadata and transition enforcement incomplete. | AUD-008-033 |
| T007 | [x] | PARTIAL | [Enum/model tests](../../tests/unit/test_communication_models.py#L29) are substantive but assert empty content valid and only inspect transition constants; no complete validation/serialization matrix. | AUD-008-033, AUD-008-034 |
| T008 | [x] | PARTIAL | [Config tests](../../tests/unit/test_communication_config.py#L11) test defaults/CSV/hash, not every parameter/change, missing required services or collection immutability. | AUD-008-033, AUD-008-034 |
| T009 | [x] | PARTIAL | [Dedup tests](../../tests/unit/test_communication_dedup.py#L11) cover keys, TTL and size; not restart/failure retry, actual LRU access or tenant/update boundaries. | AUD-008-003, AUD-008-008, AUD-008-034 |
| T010 | [x] | PARTIAL | [Translator tests](../../tests/unit/test_communication_translator.py#L12) cover word cosine/arithmetic; [prefix assertions](../../tests/unit/test_communication_translator.py#L89) do not call translator. No full translation/embedding/outage/order suite. | AUD-008-018, AUD-008-020, AUD-008-021, AUD-008-033, AUD-008-038 |
| T011 | [x] | PARTIAL | [Version tests](../../tests/unit/test_communication_versioning.py#L11) use local counters only; no etag, conflict exhaustion or concurrent storage assertions. | AUD-008-022, AUD-008-034 |
| T012 | [x] | PARTIAL | [Pipeline tests](../../tests/unit/test_communication_pipeline.py#L58) check target/dedup plus a mocked one-language draft; retrieval, templates, safety failure, persistence and stage audit assertions absent. | AUD-008-007, AUD-008-009, AUD-008-018, AUD-008-026, AUD-008-034 |
| T013 | [x] | PARTIAL | [Dedup source](../../apps/agents/communication/dedup.py#L24) implements bounded TTL insertion caches; lacks tenant keys and successful-processing semantics; hits do not refresh LRU order. | AUD-008-003, AUD-008-008 |
| T014 | [x] | PARTIAL | [Loader](../../apps/agents/communication/templates.py#L36) parses/interpolates with missing-value warnings; schema/complete matrix/ultimate fallback safety and image assets incomplete. | AUD-008-017, AUD-008-036 |
| T015 | [x] | PARTIAL | [Translator](../../apps/agents/communication/translator.py#L38) uses shared mixin and default en-AU-first; [word cosine](../../apps/agents/communication/translator.py#L274) and outage behavior contradict embeddings/skip requirements. | AUD-008-020, AUD-008-021, AUD-008-033, AUD-008-038 |
| T016 | [x] | PARTIAL | [Counter](../../apps/agents/communication/versioning.py#L42) has OCC-shaped code but wrong tenant partition and unreserved fallback versions. | AUD-008-003, AUD-008-022, AUD-008-023 |
| T017 | [x] | IMPLEMENTED | [Audit primary](../../apps/agents/communication/audit.py#L65) uses create_item with tenant-bearing record; [test](../../tests/unit/test_communication_audit.py#L19) asserts create. This narrow writer artifact exists; production wiring is separate. | AUD-008-009, AUD-008-026, AUD-008-027 |
| T018 | [x] | PARTIAL | [Pipeline](../../apps/agents/communication/pipeline.py#L93) has staged orchestration but unchecked intake, fallback provenance, incomplete persistence, logging-only review and audit finalization. | AUD-008-006, AUD-008-007, AUD-008-009, AUD-008-010, AUD-008-018, AUD-008-026 |
| T019 | [x] | PARTIAL | [Factory/handler](../../apps/agents/communication/agent.py#L111) exists; [launcher](../../apps/agents/communication/__main__.py#L1) no-op, no intake consumer in S1/S2, blocking semaphore-protected processing. | AUD-008-006, AUD-008-007, AUD-008-028, AUD-008-031 |
| T020 | [x] | PARTIAL | Relocated [handoff tests](../../tests/unit/test_communication_handoff.py#L7) check generic model, permit evacuation source and omit required IDs; no pipeline dedup/tenant assertions. | AUD-008-003, AUD-008-007, AUD-008-034 |
| T021 | [x] | PARTIAL | Relocated [schema tests](../../tests/unit/test_communication_alert_schema.py#L15) test minimal drafting model/roundtrip, not produced six-language pending_review and all provenance/quality fields. | AUD-008-033, AUD-008-034 |
| T022 | [x] | PARTIAL | [Approval tests](../../tests/unit/test_communication_approval.py#L33) cover in-memory approve/reject/cancel; no modify/escalation/two-worker OCC. | AUD-008-011, AUD-008-012, AUD-008-013, AUD-008-034 |
| T023 | [x] | PARTIAL | [Workflow](../../apps/agents/communication/approval.py#L44) has request/timer/helpers; unused chain, no durable timer, unconditional write branch and local modifications. | AUD-008-010, AUD-008-011, AUD-008-012, AUD-008-013 |
| T024 | [x] | PARTIAL | [Stage 9](../../apps/agents/communication/pipeline.py#L575) logs request; no publication, initial timer or superseded-assessment warning. MAF publisher does not close this integration. | AUD-008-007, AUD-008-010, AUD-008-013 |
| T025 | [x] | PARTIAL | [Approve/reject](../../apps/agents/communication/agent.py#L217) exist; no JWT, etag, delivery trigger or exact response contract. | AUD-008-001, AUD-008-002, AUD-008-010, AUD-008-011 |
| T026 | [x] | PARTIAL | [Modify/cancel](../../apps/agents/communication/agent.py#L307) exist but trust body actor and only change local state; metadata/response/new review incomplete. | AUD-008-001, AUD-008-011, AUD-008-012 |
| T027 | [x] | PARTIAL | [Endpoint tests](../../tests/unit/test_communication_endpoints.py#L78) check basic 200/404/422/cancel409; no JWT, modify, concurrent approval or audit assertions. | AUD-008-001, AUD-008-011, AUD-008-012, AUD-008-034 |
| T028 | [x] | PARTIAL | [Delivery tests](../../tests/unit/test_communication_delivery.py#L54) test strings/order and current incorrect dedup; no real retry independence/provider response/aggregate failure assertions. | AUD-008-002, AUD-008-004, AUD-008-005, AUD-008-014, AUD-008-015, AUD-008-032 |
| T029 | [x] | PARTIAL | [Delivery service](../../apps/agents/communication/delivery.py#L56) supplies records/retry structure but no-op providers, lossy dedup, serial sends and narrow simulation guard. | AUD-008-002, AUD-008-003, AUD-008-004, AUD-008-005, AUD-008-014, AUD-008-032 |
| T030 | [x] | PARTIAL | [Delivery stage](../../apps/agents/communication/pipeline.py#L586) has no approval caller/guard, false aggregation, late timestamp, no alert-status persistence. | AUD-008-002, AUD-008-009, AUD-008-015, AUD-008-026 |
| T031 | [x] | PARTIAL | [Status endpoint](../../apps/agents/communication/agent.py#L405) is a zero-valued placeholder without authorization, lookup, records or real channel summary. | AUD-008-001, AUD-008-015 |
| T032 | [x] | PARTIAL | [Segmentation tests](../../tests/unit/test_communication_segmentation.py#L11) cover zone mapping/basic flags/majority language; no minority proportions, geometry, guidance, size/overlap correctness. | AUD-008-005, AUD-008-016, AUD-008-034 |
| T033 | [x] | PARTIAL | [Segmenter](../../apps/agents/communication/segmentation.py#L38) exists; dominant-language-only targeting, unverified facility geography and no specific guidance. | AUD-008-016 |
| T034 | [x] | PARTIAL | [Stage 3](../../apps/agents/communication/pipeline.py#L271) invokes segmenter but demographics come from payload; segment persistence/review summaries are not wired. | AUD-008-007, AUD-008-009, AUD-008-010, AUD-008-016 |
| T035 | [x] | PARTIAL | [Lifecycle tests](../../tests/unit/test_communication_versioning.py#L58) assert returned tuples, not persisted four-version lifecycle, all-clear audience, expiry or history. | AUD-008-023, AUD-008-024, AUD-008-025, AUD-008-034 |
| T036 | [x] | PARTIAL | [Lifecycle helpers](../../apps/agents/communication/versioning.py#L179) allocate IDs only; expiry ignores deadlines; history method lacks operational read integration. | AUD-008-022, AUD-008-023, AUD-008-024, AUD-008-025 |
| T037 | [x] | PARTIAL | [Stage 8](../../apps/agents/communication/pipeline.py#L455) trusts payload change flags; no automatic update derivation, original-audience all-clear, or expiry scheduler. | AUD-008-008, AUD-008-023, AUD-008-024, AUD-008-025 |
| T038 | [x] | MISSING | S5 and the complete [pipeline test file](../../tests/unit/test_communication_pipeline.py#L1) contain no specified per-language safety/fallback audit test suite; shared moderation helpers are not equivalent coverage. | AUD-008-018, AUD-008-019, AUD-008-034 |
| T039 | [x] | PARTIAL | [Stage 7](../../apps/agents/communication/pipeline.py#L375) checks text but rechecks safety fallback, loses reason, substitutes evacuation and lacks complete decision records. | AUD-008-018, AUD-008-019, AUD-008-026 |
| T040 | [x] | PARTIAL | [Translator](../../apps/agents/communication/translator.py#L147) uses mixin fallback and per-language labels; reason/provenance are not preserved and pipeline can overwrite results. | AUD-008-018 |
| T041 | [x] | PARTIAL | [Audit tests](../../tests/unit/test_communication_audit.py#L18) cover basic tiers/flush; not restart ordering, transition records, duplicate replay, complete decision set or real reconciliation. | AUD-008-026, AUD-008-027, AUD-008-034 |
| T042 | [x] | PARTIAL | [Memory buffering](../../apps/agents/communication/audit.py#L74) and bounded deque exist; transition audit absent, record buffered_at only applied on flush. | AUD-008-026, AUD-008-027 |
| T043 | [x] | PARTIAL | [Spill](../../apps/agents/communication/audit.py#L84) appends JSONL and logs critical; depth excludes file, restart accounting/transition audit incomplete. | AUD-008-027 |
| T044 | [x] | PARTIAL | [flush](../../apps/agents/communication/audit.py#L108) drains manually but has no recovery caller, chronological/duplicate/crash hazards and stale tier count. | AUD-008-027, AUD-008-029 |
| T045 | [x] | PARTIAL | [Finalization](../../apps/agents/communication/pipeline.py#L637) logs duration as another handoff_received; no expected/actual reconciliation or flush. | AUD-008-026, AUD-008-027, AUD-008-030 |
| T046 | [x] | PARTIAL | [Audit helper/callers](../../apps/agents/communication/pipeline.py#L658) implement some events, not all 18 owner paths or required metadata; default live contaminates context. | AUD-008-003, AUD-008-026 |
| T047 | [x] | MISSING | Complete [pipeline tests](../../tests/unit/test_communication_pipeline.py#L1) and S5 contain no specified mixed-outage/recovery suite; basic writer/record tests do not replace it. | AUD-008-014, AUD-008-018, AUD-008-020, AUD-008-027, AUD-008-029, AUD-008-034 |
| T048 | [x] | PARTIAL | [Mixin fallback](../../apps/agents/common/llm_mixin.py#L197) and [penalties](../../apps/agents/communication/pipeline.py#L472) exist; template assets/recovery/template_fallback audit not complete. | AUD-008-017, AUD-008-021, AUD-008-026, AUD-008-029 |
| T049 | [x] | PARTIAL | [Retry failure health](../../apps/agents/communication/delivery.py#L197) sets channel false; serial scheduling, commander notification and recovery tracking absent. | AUD-008-014, AUD-008-015, AUD-008-029 |
| T050 | [x] | CONFLICT | [Back-translation](../../apps/agents/communication/translator.py#L228) uses no embeddings and fabricates 0.5 on error, contrary to skipping unmeasurable comparisons without penalty. | AUD-008-020, AUD-008-037 |
| T051 | [x] | MISSING | S1/S5 inspected dependency paths and [event definition](../../apps/agents/communication/telemetry.py#L401) but found no comprehensive transition tracking/recovery call sites. | AUD-008-027, AUD-008-029, AUD-008-030 |
| T052 | [x] | PARTIAL | [Health](../../apps/agents/communication/agent.py#L140) has shape/hash but constant readiness/wrong counts/no503; [tests](../../tests/unit/test_communication_endpoints.py#L46) do not exercise outages. | AUD-008-029, AUD-008-037 |
| T053 | [x] | PARTIAL | [GET alert](../../apps/agents/communication/agent.py#L392) returns private in-memory objects with no JWT or durable read/history. | AUD-008-001, AUD-008-009, AUD-008-025 |
| T054 | [x] | PARTIAL | [OTel definitions](../../apps/agents/communication/telemetry.py#L112) provide tracer/meter/no-ops; no communication exporter initialization or incoming Service Bus correlation integration. | AUD-008-006, AUD-008-030 |
| T055 | [x] | PARTIAL | [Metric namespace](../../apps/agents/communication/telemetry.py#L272) has many definitions; wrong names/types/units and uncalled instruments; draft timing excludes required stages. | AUD-008-030, AUD-008-035, AUD-008-037 |
| T056 | [x] | PARTIAL | [Event emitter](../../apps/agents/communication/telemetry.py#L337) defines helpers but not all real emitters; placeholders/missing attributes and recovery/escalation/delivery calls absent. | AUD-008-013, AUD-008-026, AUD-008-029, AUD-008-030 |
| T057 | [x] | PARTIAL | Relocated [reproducibility tests](../../tests/unit/test_communication_reproducibility.py#L9) prove config hashes/empty-counter IDs, not content, snapshots, model revisions or tenant query isolation. | AUD-008-003, AUD-008-022, AUD-008-034, AUD-008-035 |
| T058 | [x] | MISSING | S5/S7 found no communication container/OCC/status persistence integration assertions; [local counter tests](../../tests/unit/test_communication_versioning.py#L11) and generic writer mocks are not substitutes. | AUD-008-009, AUD-008-011, AUD-008-022, AUD-008-034 |
| T059 | [x] | PARTIAL | [MAF HITL tests](../../tests/integration/test_hitl_round_trip.py#L51) exercise an in-memory approval queue; no communication intake consumer/ack/dead-letter lifecycle test found in S5/S7. | AUD-008-006, AUD-008-007, AUD-008-010, AUD-008-034 |
| T060 | [x] | PARTIAL | Relocated [cyclone tests](../../tests/unit/test_cyclone_alert_scenario.py#L15) check draft/count/zone mapping; no hospital targeting, real approval, provider receipts or audit completeness. | AUD-008-016, AUD-008-034 |
| T061 | [x] | PARTIAL | Relocated [bushfire tests](../../tests/unit/test_bushfire_alert_scenario.py#L19) check a draft/zone/SMS length, not initial-update-correction-all-clear with approval at each version. | AUD-008-023, AUD-008-024, AUD-008-025, AUD-008-034 |
| T062 | [x] | PARTIAL | Relocated [flood tests](../../tests/unit/test_flood_alert_scenario.py#L23) check basic zone/record presence, not zh-Hans/vi, outage recovery or overlap preservation. | AUD-008-005, AUD-008-016, AUD-008-034 |
| T063 | [x] | PARTIAL | [Standalone Bicep](../../infra/modules/communication-agent.bicep#L71) contains resource artifacts but no composition caller in S6, wrong channels/scale policy and incomplete bindings; deployment UNVERIFIED. | AUD-008-031, AUD-008-037 |
| T064 | [x] | UNVERIFIED | [Quickstart](quickstart.md#L148) is authored but no run log exists in S7; module launch, class example and image target contradict source. | AUD-008-006, AUD-008-031, AUD-008-035, AUD-008-037 |

## Requirement Coverage

SC status distinguishes source support from unproven numerical or human outcomes. Capstone authority pointers are assessed as authored governance artifacts, not proof of the deferred capabilities.

| Requirement ID | Status | Concrete evidence / limitation | Follow-up IDs |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Intake](../../apps/agents/communication/pipeline.py#L174) checks target/dedup; no full payload/source/incident validation or connected consumer/ack deadline. | AUD-008-006, AUD-008-007, AUD-008-028 |
| FR-002 | PARTIAL | [Retrieval](../../apps/agents/communication/pipeline.py#L225) optional reads become payload fabrications on any error; references are not verified. | AUD-008-007, AUD-008-009 |
| FR-003 | CONFLICT | [TTL cache](../../apps/agents/communication/dedup.py#L42) exists; early insertion loses retries, tenant omitted, same-incident update semantics contradictory. | AUD-008-003, AUD-008-008, AUD-008-037 |
| FR-004 | MISSING | [Intake](../../apps/agents/communication/pipeline.py#L174) and constructor in S1/S2 have no incident-existence check or incident-store binding. | AUD-008-007 |
| FR-005 | PARTIAL | [Language loop](../../apps/agents/communication/translator.py#L38) defaults to six; missing resources/config order can yield English or no primary. | AUD-008-017, AUD-008-033 |
| FR-006 | CONFLICT | [Mixin call](../../apps/agents/communication/translator.py#L147) uses default temperature 0; [quality](../../apps/agents/communication/translator.py#L274) is word cosine, not semantic embeddings; per-language penalty provenance absent. | AUD-008-020, AUD-008-038, AUD-008-037 |
| FR-006a | CONFLICT | [Confidence](../../apps/agents/communication/pipeline.py#L472) always penalizes freshness; no staleness condition/input. | AUD-008-020, AUD-008-021 |
| FR-007 | PARTIAL | [Templates](../../data/alert-templates/en-AU.json#L3) have action/help structures; [prompt](../../apps/agents/communication/translator.py#L116), minority targeting and SMS slicing do not preserve complete equivalent facts. | AUD-008-016, AUD-008-017, AUD-008-032, AUD-008-038 |
| FR-008 | PARTIAL | [Loop](../../apps/agents/communication/translator.py#L58) references en-AU only when encountered first; CSV reordering is not guarded. | AUD-008-033, AUD-008-038 |
| FR-009 | PARTIAL | [Token trimming](../../apps/agents/common/llm_mixin.py#L124) is a character reduction, not assured token-budget enforcement. | AUD-008-038 |
| FR-010 | PARTIAL | [Wrapper safety](../../apps/agents/common/llm_mixin.py#L154) and [stage 7](../../apps/agents/communication/pipeline.py#L375) execute, but language/factual/tone scope and fallback results are incomplete. | AUD-008-018, AUD-008-019 |
| FR-011 | PARTIAL | [Fallback](../../apps/agents/communication/pipeline.py#L414) exists but uses evacuation regardless of request and drops on validator exceptions. | AUD-008-018 |
| FR-012 | CONFLICT | [Aggregation](../../apps/agents/communication/pipeline.py#L385) can report passed after wrapper safety_fallback; template-only overall/per-block results disagree. | AUD-008-018, AUD-008-037 |
| FR-013 | PARTIAL | [Shared system prompt](../../apps/agents/common/llm_client.py#L185) resists embedded instructions in prose but is not drafting-specific; no full negative-path assurance. | AUD-008-019, AUD-008-038 |
| FR-014 | PARTIAL | [Loader](../../apps/agents/communication/templates.py#L36) plus six files exist; matrix/startup/fallback safety and offline approval proof incomplete. | AUD-008-017, AUD-008-018, AUD-008-036 |
| FR-015 | CONFLICT | [Counter fallback](../../apps/agents/communication/versioning.py#L127) returns an unreserved value after conflicts; tenant scope wrong. | AUD-008-003, AUD-008-022 |
| FR-016 | PARTIAL | [Creation](../../apps/agents/communication/pipeline.py#L543) uses create_item, but approval/status writes and model mutation boundaries do not enforce immutable version semantics. | AUD-008-009, AUD-008-011, AUD-008-012, AUD-008-023, AUD-008-033 |
| FR-017 | PARTIAL | [Correction prefix](../../apps/agents/communication/translator.py#L101) exists; [lifecycle helpers](../../apps/agents/communication/versioning.py#L179) do not implement full records/audiences/all-clear. | AUD-008-018, AUD-008-023, AUD-008-024, AUD-008-025 |
| FR-018 | CONFLICT | [Supersession](../../apps/agents/communication/versioning.py#L138) before new persistence conflicts with protected approved predecessor in US2-AS4. | AUD-008-023, AUD-008-037 |
| FR-019 | PARTIAL | [Stage 8](../../apps/agents/communication/pipeline.py#L517) sets pending_review; [alternative publication](../../apps/api/app/services/public_alert_service.py#L47) and direct delivery bypass durable human authority. | AUD-008-001, AUD-008-002, AUD-008-006, AUD-008-010 |
| FR-020 | PARTIAL | [Workflow](../../apps/agents/communication/approval.py#L155) implements local actions, not trusted actor/durable etag/full preview/connected dashboard/modification review. | AUD-008-001, AUD-008-010, AUD-008-011, AUD-008-012 |
| FR-021 | CONFLICT | [Delivery entry](../../apps/agents/communication/pipeline.py#L586) sets delivering without checking approved; service has no guard. | AUD-008-002 |
| FR-042 | PARTIAL | [Escalation](../../apps/agents/communication/approval.py#L91) exists but is not started, persists no deadline, uses invented commanders; amendment redirects policy authority. | AUD-008-013, AUD-008-037 |
| FR-022 | PARTIAL | [Segmenter](../../apps/agents/communication/segmentation.py#L38) uses synthetic payload zones/dominant language rather than complete geographic/minority targeting. | AUD-008-007, AUD-008-016 |
| FR-023 | PARTIAL | [Audience model](../../apps/agents/communication/models.py#L188) has fields, but geometry/channel completeness and durable segment snapshots are not enforced. | AUD-008-009, AUD-008-016, AUD-008-033 |
| FR-024 | PARTIAL | [Priority sort](../../apps/agents/communication/delivery.py#L151) puts critical first; [dedup](../../apps/agents/communication/delivery.py#L118) drops populations and independent channel priority unproven. | AUD-008-005, AUD-008-014, AUD-008-016 |
| FR-025 | PARTIAL | [Flags/defaults](../../apps/agents/communication/segmentation.py#L187) exist but no per-zone data-source diagnosis or alert-summary disclosure. | AUD-008-016 |
| FR-026 | PARTIAL | [Adapters](../../apps/agents/communication/delivery.py#L208) are incomplete/no-op, broadcast lacks HTTP; receipts/retries/targeting unproven. | AUD-008-004, AUD-008-014 |
| FR-027 | PARTIAL | [Record creation](../../apps/agents/communication/delivery.py#L94) exists but pending/in-progress durability, attempt/receipt truth and idempotency incomplete. | AUD-008-004, AUD-008-009, AUD-008-014, AUD-008-015 |
| FR-028 | CONFLICT | [Formatting](../../apps/agents/communication/delivery.py#L251) slices without link or actionable preservation; research contradicts link requirement; Unicode count wrong. | AUD-008-032, AUD-008-037 |
| FR-029 | CONFLICT | [Broadcast](../../apps/agents/communication/delivery.py#L236) skips non-English segments instead of sending en-AU; no webhook. | AUD-008-004, AUD-008-032 |
| FR-030 | CONFLICT | [Retry loop](../../apps/agents/communication/delivery.py#L161) is serial across channels; [aggregate](../../apps/agents/communication/pipeline.py#L599) mishandles all failed/empty. | AUD-008-014, AUD-008-015, AUD-008-037 |
| FR-031 | MISSING | [Delivery-status](../../apps/agents/communication/agent.py#L405) returns constant zero data; S1/S4 contain no integrated commander receipt metrics. | AUD-008-015 |
| FR-032 | PARTIAL | [Pipeline audit calls](../../apps/agents/communication/pipeline.py#L658) cover only some steps; declared enums/custom events are not decision emissions. | AUD-008-026, AUD-008-027 |
| FR-033 | PARTIAL | [Audit create_item](../../apps/agents/communication/audit.py#L65) supports append-only, but absent correlation/metadata and recovery gaps remain. | AUD-008-003, AUD-008-026, AUD-008-027, AUD-008-033 |
| FR-034 | PARTIAL | [Three tiers](../../apps/agents/communication/audit.py#L42) exist; no automatic safe flush, accurate file depth or transition records; tier naming conflicted. | AUD-008-027, AUD-008-029, AUD-008-037 |
| FR-035 | PARTIAL | [Delivery audits](../../apps/agents/communication/pipeline.py#L620) record channel/status only, not full audience/content/time/approval-mode envelope. | AUD-008-026 |
| FR-036 | PARTIAL | [Fallback](../../apps/agents/common/llm_mixin.py#L197) and [0.8 factor](../../apps/agents/communication/pipeline.py#L478) exist; incomplete approved templates, audit decision and recovery. | AUD-008-017, AUD-008-021, AUD-008-026, AUD-008-029 |
| FR-037 | PARTIAL | [Delivery failures](../../apps/agents/communication/delivery.py#L197) mark unhealthy but delays other channels and lacks specific commander failure/recovery surfacing. | AUD-008-004, AUD-008-014, AUD-008-015, AUD-008-029 |
| FR-038 | PARTIAL | [Health response](../../apps/agents/communication/agent.py#L140) exists but reports invented readiness and wrong counters/tier; actual 8084 runtime not established. | AUD-008-006, AUD-008-029, AUD-008-037 |
| FR-039 | PARTIAL | [Exception handling](../../apps/agents/communication/pipeline.py#L158) returns None on pipeline failure, data outages invent payload data, recovery missing. | AUD-008-007, AUD-008-008, AUD-008-018, AUD-008-027, AUD-008-029 |
| FR-040 | CONFLICT | [Prefix guard](../../apps/agents/communication/delivery.py#L66) conflicts with [canonical non-live semantics](../../apps/api/app/core/tenant_context.py#L13). | AUD-008-003 |
| FR-041 | PARTIAL | [Alert tenant](../../apps/agents/communication/pipeline.py#L533) propagates, but safety audits default live and counters/reads lack validated tenant context. | AUD-008-003, AUD-008-009 |
| NFR-001 | PARTIAL | [Semaphore](../../apps/agents/communication/agent.py#L126) surrounds synchronous work; [HTTP scaler](../../infra/modules/communication-agent.bicep#L209) is not queue scaling; no capacity run evidence. | AUD-008-028, AUD-008-031, AUD-008-035 |
| NFR-002 | PARTIAL | [Telemetry](../../apps/agents/communication/telemetry.py#L112) defines signals but many names/types/emitters/exporter bindings are incomplete. | AUD-008-030 |
| NFR-003 | UNVERIFIED | [Module location](../../infra/modules/communication-agent.bicep#L4) is a parameter, not proof of independent Australian deployments; S6 contains no composed regional communication topology. | AUD-008-003, AUD-008-031, AUD-008-035 |
| SC-001 | UNVERIFIED | [Draft timing](../../apps/agents/communication/pipeline.py#L298) excludes required stages; [benchmark](../../tests/benchmark/test_pipeline_performance.py#L219) cannot establish 20s/35s. | AUD-008-028, AUD-008-030, AUD-008-035, AUD-008-037 |
| SC-002 | UNVERIFIED | [Safety wrapper](../../apps/agents/common/llm_mixin.py#L154) is source support, not executed 100% coverage across chosen runtime; incomplete validation/recovery semantics. | AUD-008-018, AUD-008-019, AUD-008-034, AUD-008-035 |
| SC-003 | CONFLICT | [Direct delivery](../../apps/agents/communication/delivery.py#L56) and [pending publication](../../apps/api/app/services/public_alert_service.py#L47) permit paths without verified commander authorization. | AUD-008-001, AUD-008-002, AUD-008-035 |
| SC-004 | UNVERIFIED | [No-op sends](../../apps/agents/communication/delivery.py#L208), lossy targeting and no measured provider outcomes cannot prove 95% reach in 5min. | AUD-008-004, AUD-008-005, AUD-008-015, AUD-008-035 |
| SC-005 | UNVERIFIED | [Fallback source](../../apps/agents/common/llm_mixin.py#L197) exists; no zero-drop outage timing run and approved fallback matrix incomplete. | AUD-008-008, AUD-008-017, AUD-008-035 |
| SC-006 | UNVERIFIED | [Finalization](../../apps/agents/communication/pipeline.py#L637) does not reconcile; no 100% audit reconciliation evidence. | AUD-008-026, AUD-008-027, AUD-008-035 |
| SC-007 | UNVERIFIED | [Health](../../apps/agents/communication/agent.py#L140) has no measured <=1s evidence; blocking work and wrong outage status remain. | AUD-008-028, AUD-008-029, AUD-008-035 |
| SC-008 | UNVERIFIED | [Survey requirement](spec.md#L300) has no commander sample, responses, or sign-off in S7/local evidence. | AUD-008-035, AUD-008-036 |
| SC-009 | UNVERIFIED | [Stage 9](../../apps/agents/communication/pipeline.py#L575) is logging-only; no observed <=5s delivery notification. | AUD-008-010, AUD-008-030, AUD-008-035 |
| SC-010 | UNVERIFIED | [Approve endpoint](../../apps/agents/communication/agent.py#L217) does not trigger delivery; no initiation timestamp/<=10s evidence. | AUD-008-010, AUD-008-015, AUD-008-035 |
| SC-011 | UNVERIFIED | [E2E metric definition](../../apps/agents/communication/telemetry.py#L142) lacks complete emitting path/approval-wait exclusion and measured <=60s first completion. | AUD-008-030, AUD-008-035, AUD-008-037 |
| FR-CAP-008-001 | UNVERIFIED | [Deferred language packs](spec.md#L363) and [country evidence](evidence/HYP-027.md#L6) retain unproven prerequisites; not classified as missing implementation. | AUD-008-036 |
| FR-CAP-008-002 | UNVERIFIED | [Deferred misinformation rule](spec.md#L365) is authored; no country classifier/English-baseline outcome proof in local evidence. | AUD-008-036 |
| FR-CAP-008-003 | IMPLEMENTED | [Defers-to pointer](spec.md#L366) has reciprocal [Spec 018 authority](../018-aidr-guidance-integration/spec.md#L343); runtime timeout mapping remains separate FR-042 work. | AUD-008-013, AUD-008-037 |
| FR-CAP-008-004 | IMPLEMENTED | [Supersedes pointer](spec.md#L367) reciprocates [Spec 006 FR-024](../006-data-ingestion-storage/spec.md#L254). Only authority relocation is established. | AUD-008-037 |

## Acceptance Scenario Coverage

AS identifiers below are local review labels for the numbered scenarios; the specification does not assign separate AS IDs. Each row maps one original scenario, in order, without merging scenarios.

| Scenario | Status | Expected outcome versus inspected evidence | Follow-up IDs |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Spec US1](spec.md#L38): six-language pending_review with demographics/provenance. [Pipeline test](../../tests/unit/test_communication_pipeline.py#L86) uses one language/no stores; [cyclone](../../tests/unit/test_cyclone_alert_scenario.py#L89) checks count only. | AUD-008-006, AUD-008-007, AUD-008-009, AUD-008-016, AUD-008-034 |
| US1-AS2 | PARTIAL | [Safety fallback](../../apps/agents/communication/pipeline.py#L375) exists but can lose original failure reason and alert type; no per-language pipeline assertion. | AUD-008-018, AUD-008-019 |
| US1-AS3 | PARTIAL | [Mixin](../../apps/agents/common/llm_mixin.py#L197) returns template_fallback; approved matrix and degradation audit incomplete. | AUD-008-017, AUD-008-026, AUD-008-035 |
| US1-AS4 | CONFLICT | [Dedup](../../apps/agents/communication/pipeline.py#L196) suppresses same-incident updates; [counter](../../apps/agents/communication/versioning.py#L127) can issue duplicate versions. | AUD-008-008, AUD-008-022, AUD-008-023, AUD-008-037 |
| US2-AS1 | PARTIAL | [Local approve test](../../tests/unit/test_communication_approval.py#L33) covers status/actor, not trusted JWT, durable timestamp/audit and delivery integration. | AUD-008-001, AUD-008-002, AUD-008-010, AUD-008-011 |
| US2-AS2 | PARTIAL | [Reject test](../../tests/unit/test_communication_approval.py#L85) checks reason/status; rejection timestamp/auth/persistence and global no-send invariant incomplete. | AUD-008-001, AUD-008-002, AUD-008-011 |
| US2-AS3 | PARTIAL | [Modify helper](../../apps/agents/communication/approval.py#L220) creates a local copy, not a safely reserved/persisted/review-notified version. | AUD-008-012 |
| US2-AS4 | CONFLICT | [supersede_previous](../../apps/agents/communication/versioning.py#L138) includes approved and delivering, opposite this scenario's protected predecessor. | AUD-008-023, AUD-008-037 |
| US3-AS1 | PARTIAL | [Record loop](../../apps/agents/communication/delivery.py#L94) exists but no approved guard, durable pending records or real provider-backed delivery. | AUD-008-002, AUD-008-004, AUD-008-009, AUD-008-015 |
| US3-AS2 | PARTIAL | [Language selection](../../apps/agents/communication/delivery.py#L80) uses preferred language, but target is segment ID and minority segments are not constructed. | AUD-008-004, AUD-008-016, AUD-008-032 |
| US3-AS3 | PARTIAL | [Retries](../../apps/agents/communication/delivery.py#L161) exist, but serial channel blocking, failure surfacing and detailed audit assertions incomplete. | AUD-008-014, AUD-008-015, AUD-008-026 |
| US3-AS4 | CONFLICT | [Broadcast](../../apps/agents/communication/delivery.py#L236) skips zh-Hans segments and reports success; [test](../../tests/unit/test_communication_delivery.py#L90) only checks record presence. | AUD-008-004, AUD-008-032 |
| US4-AS1 | IMPLEMENTED | [Zone mapping](../../apps/agents/communication/segmentation.py#L24) creates one supplied-zone segment per level with immediate/watch/advisory; [tests](../../tests/unit/test_communication_segmentation.py#L11) assert mapping. Upstream geometry sourcing is separately partial. | AUD-008-016 |
| US4-AS2 | PARTIAL | [Facility segment](../../apps/agents/communication/segmentation.py#L104) records population/critical flag; no verified inclusion or facility-specific guidance. | AUD-008-005, AUD-008-016 |
| US4-AS3 | CONFLICT | [Dominant-language max](../../apps/agents/communication/segmentation.py#L153) does not create the 15% zh-Hans subgroup or a secondary-language representation. | AUD-008-016 |
| US4-AS4 | PARTIAL | [Default/flags](../../apps/agents/communication/segmentation.py#L187) exist; log plus commander-facing limited-segmentation summary absent. | AUD-008-016 |
| US5-AS1 | PARTIAL | [Stage 8](../../apps/agents/communication/pipeline.py#L503) relies on payload change_type and missing summary becomes string None; automatic update/history contract incomplete. | AUD-008-008, AUD-008-023 |
| US5-AS2 | PARTIAL | [Prefix logic](../../apps/agents/communication/translator.py#L101) exists, but full correction request/reference/review path and tests are incomplete. | AUD-008-018, AUD-008-023 |
| US5-AS3 | PARTIAL | [All-clear helper](../../apps/agents/communication/versioning.py#L199) only allocates an ID; original targeting and post-delivery supersession absent. | AUD-008-024 |
| US5-AS4 | PARTIAL | [History helper](../../apps/agents/communication/versioning.py#L234) queries when injected, but no durable end-to-end history/API with all action metadata. | AUD-008-009, AUD-008-011, AUD-008-025 |
| US6-AS1 | PARTIAL | [Stage 7](../../apps/agents/communication/pipeline.py#L375) retains passing text; shared provider branch/language gaps and no focused positive six-language assertions. | AUD-008-019, AUD-008-034 |
| US6-AS2 | PARTIAL | [Wrapper fallback](../../apps/agents/common/llm_mixin.py#L159) exists, but reason becomes aggregate text and can be overwritten by pipeline recheck. | AUD-008-018 |
| US6-AS3 | PARTIAL | [Keyword-path language heuristic](../../apps/agents/common/content_safety.py#L91) detects no Chinese; Azure success skips that check and audit reason propagation fails. | AUD-008-018, AUD-008-019 |
| US6-AS4 | PARTIAL | [Mixed/worst generation](../../apps/agents/communication/pipeline.py#L490) exists, but all-six failures can lose safety_result and validator failure can drop the handoff. | AUD-008-017, AUD-008-018, AUD-008-034 |
| US7-AS1 | PARTIAL | [Audit envelope](../../apps/agents/communication/pipeline.py#L658) omits recommendation ID, generation metadata and correlation on several stages. | AUD-008-003, AUD-008-026 |
| US7-AS2 | PARTIAL | [Approval audit](../../apps/agents/communication/agent.py#L234) is free-text/untrusted identity, not the complete durable structured action record. | AUD-008-001, AUD-008-011, AUD-008-026 |
| US7-AS3 | PARTIAL | [Delivery audit](../../apps/agents/communication/pipeline.py#L620) lacks full segment/language/retry/failure detail per attempt. | AUD-008-014, AUD-008-026 |
| US7-AS4 | PARTIAL | [Tier fallback](../../apps/agents/communication/audit.py#L42) is present, but transitions are log lines and replay/recovery is not integrated. | AUD-008-026, AUD-008-027 |
| US8-AS1 | PARTIAL | [Fallback generation](../../apps/agents/common/llm_mixin.py#L197) plus 0.8 stacking exist; complete approved templates/template_fallback decision absent. | AUD-008-017, AUD-008-021, AUD-008-026 |
| US8-AS2 | PARTIAL | Shared circuit-breaker retries can resume LLM generation, but [recovery event helper](../../apps/agents/communication/telemetry.py#L401) has no communication recovery-tracker caller. | AUD-008-029, AUD-008-030 |
| US8-AS3 | PARTIAL | [Failure flag](../../apps/agents/communication/delivery.py#L205) exists; no independent start or concrete commander failure detail. | AUD-008-014, AUD-008-015, AUD-008-029 |
| US8-AS4 | PARTIAL | [Manual flush test](../../tests/unit/test_communication_audit.py#L111) exists; no automatic recovery detection/caller or crash-safe ordered replay. | AUD-008-027, AUD-008-029 |

## Edge Case Coverage

EC identifiers are review labels for the nine bullets under [Edge Cases](spec.md#L174), in original order.

| Edge case | Status | Evidence and required distinction | Follow-up IDs |
| --- | --- | --- | --- |
| EC-01 | CONFLICT | Missing recommendation should reject; [retrieval](../../apps/agents/communication/pipeline.py#L225) invents fallback data instead. | AUD-008-007 |
| EC-02 | PARTIAL | Duplicate ID discard exists in [cache](../../apps/agents/communication/dedup.py#L42); failed attempts/tenant/update distinctions are not safe. | AUD-008-003, AUD-008-008 |
| EC-03 | CONFLICT | [Simulation prefix](../../apps/agents/communication/delivery.py#L66) misses canonical non-live UUID tenants and audit context. | AUD-008-003 |
| EC-04 | PARTIAL | [Character trimming](../../apps/agents/common/llm_mixin.py#L124) plus limited language checks do not guarantee coherent bounded instructions. | AUD-008-018, AUD-008-019, AUD-008-038 |
| EC-05 | PARTIAL | [SMS slicing](../../apps/agents/communication/delivery.py#L251) obeys a length but can drop action/help and miscount Unicode parts. | AUD-008-032 |
| EC-06 | CONFLICT | [All-failed aggregate](../../apps/agents/communication/pipeline.py#L599) becomes partially_delivered, sets publication time and lacks critical/retry outcome. | AUD-008-015, AUD-008-037 |
| EC-07 | MISSING | No superseded-assessment warning/recheck in [retrieval](../../apps/agents/communication/pipeline.py#L225), [approval](../../apps/agents/communication/approval.py#L155), or alternatives searched in S1/S2/S4. | AUD-008-007, AUD-008-010 |
| EC-08 | MISSING | No active-sub-zone confirmation path in [all-clear helper](../../apps/agents/communication/versioning.py#L199), pipeline or alternate AWS helper in S1/S4/S5. | AUD-008-024 |
| EC-09 | UNVERIFIED | [No-op launcher](../../apps/agents/communication/__main__.py#L1), incorrect health and unconnected consumer prevent source proof of restart/redelivery; hosting behavior was not queried. | AUD-008-006, AUD-008-007, AUD-008-029, AUD-008-031, AUD-008-035 |

## Amendment Coverage

The four FR-CAP rows are already individually covered in the requirement table. These ten rows cover every other declared amendment ID; none is inferred completed from another specification's audit.

| Amendment ID | Status | Authored claim and evidence assessment | Follow-up IDs |
| --- | --- | --- | --- |
| PER-016 | UNVERIFIED | [Validated AU persona cross-reference](spec.md#L342) is authored, but no local interviews/exercise approval evidence proves validation. | AUD-008-036 |
| PER-017 | UNVERIFIED | [Actor-catalogue reference](spec.md#L343) is not evidence those actors reviewed every implementation change. | AUD-008-036 |
| PER-018 | UNVERIFIED | [Non-AU placeholder](spec.md#L344) explicitly depends on D-009 and SME validation; do not treat placeholder as delivered persona capability. | AUD-008-036 |
| HYP-006 | UNVERIFIED | [Rubric hypothesis](spec.md#L350) has an aggregate [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L39); promised local-to-028 evidence stub absent in S8 and no post-change per-spec result establishes improvement. | AUD-008-035, AUD-008-036 |
| SCP-019 | IMPLEMENTED | [Deferred-country scope boundary](spec.md#L356) states regulatory/SME gates. Their satisfaction is not inferred. | AUD-008-036 |
| SCP-020 | IMPLEMENTED | [Constitution boundary](spec.md#L357) is explicit; this audit makes no constitutional change or carve-out expansion. Operational compliance remains covered separately. | AUD-008-036, AUD-008-037 |
| SCP-021 | PARTIAL | [Authority clause](spec.md#L358) exists but includes a self-deferral to 008 and ambiguous portfolio references; escalation ownership needs an explicit runtime mapping. | AUD-008-013, AUD-008-037 |
| HYP-027 | UNVERIFIED | [PH evidence](evidence/HYP-027.md#L1) is a complete authored stub, Status Not tested; MoU/native-review/D-009 and seasonal >=85%/latency claims unproven. | AUD-008-036 |
| HYP-028 | UNVERIFIED | [JP evidence](evidence/HYP-028.md#L1) says Not tested; no >=85% quality or <=5s p95 results, licensing/native review or D-009 sign-off. | AUD-008-036 |
| HYP-029 | UNVERIFIED | [BD evidence](evidence/HYP-029.md#L1) says Not tested; no >=80% quality or <=60s p95 results, MoU/native review or D-009 sign-off. | AUD-008-036 |

## Checklist and Review Evidence Assessment

### Original 72-Item Requirements Checklist

Every item in [checklists/communication-agent.md](checklists/communication-agent.md) is originally `[ ]`. The document explicitly evaluates requirements quality, not execution. The status below evaluates whether its question is resolved by inspected documents/source; it does not mark the original checklist. Evidence links in the associated follow-up supply implementation detail.

| Checklist ID | Original state | Status | Assessment of the actual numbered question | Follow-up IDs |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | [Pipeline contract](contracts/communication-pipeline.md#L99) defines missing/malformed startup behavior; bootstrap catches missing assets and continues. | AUD-008-017 |
| CHK002 | [ ] | CONFLICT | [Research R-001](research.md#L5) requires sequential reference generation; [budget](contracts/communication-pipeline.md#L11) totals do not fit labelled SLA. | AUD-008-028, AUD-008-035, AUD-008-037 |
| CHK003 | [ ] | PARTIAL | [Stage 5 contract](contracts/communication-pipeline.md#L120) defines mixed failures; actual audit/recovery/per-language failure preservation incomplete. | AUD-008-018, AUD-008-026 |
| CHK004 | [ ] | PARTIAL | [Quickstart](quickstart.md#L45) names text-embedding-3-small; active code uses word vectors, no embedding-model provenance. | AUD-008-020, AUD-008-035 |
| CHK005 | [ ] | PARTIAL | [interpolate](../../apps/agents/communication/templates.py#L109) strips control/HTML characters but not validated field lengths or instruction content; generic fallback bypasses it. | AUD-008-017, AUD-008-038 |
| CHK006 | [ ] | IMPLEMENTED | [interpolate](../../apps/agents/communication/templates.py#L109) explicitly substitutes unknown and warns for absent values; authored contract agrees. | AUD-008-017 |
| CHK007 | [ ] | MISSING | S1/local contracts specify configurable languages but no supported upper bound or SLA scaling policy beyond six. | AUD-008-033, AUD-008-037 |
| CHK008 | [ ] | PARTIAL | Actual question is measurable semantic equivalence, not missing-language fallback as cited by plan/tasks. Embedding and human evidence incomplete. | AUD-008-020, AUD-008-036, AUD-008-037 |
| CHK009 | [ ] | PARTIAL | [Validator keywords](../../apps/agents/common/content_safety.py#L64) are only terror/hate; no complete multilingual approved category coverage. | AUD-008-019, AUD-008-036 |
| CHK010 | [ ] | PARTIAL | [Language heuristic](../../apps/agents/common/content_safety.py#L87) is explicit but inadequate for four languages and bypassed after Azure success. | AUD-008-019 |
| CHK011 | [ ] | MISSING | Reviewed operational cultural-insensitivity criteria/fixtures absent in local contracts and S7; moderation categories alone do not resolve this. | AUD-008-019, AUD-008-036 |
| CHK012 | [ ] | PARTIAL | Shared tone helper exists, but its communication integration and accepted panic-phrasing examples are incomplete. | AUD-008-019, AUD-008-038 |
| CHK013 | [ ] | PARTIAL | [Model limits](../../apps/agents/communication/models.py#L152) exist; fully interpolated template/block bounds and safe oversize behavior unspecified/inconsistent. | AUD-008-017, AUD-008-018, AUD-008-033 |
| CHK014 | [ ] | PARTIAL | [R-008](research.md#L86) says git PR approval, not named operational/native approvers or evidence/cadence. | AUD-008-036 |
| CHK015 | [ ] | PARTIAL | Documents distinguish outage/safety fallback; [stage 7](../../apps/agents/communication/pipeline.py#L375) launders original safety outcomes. | AUD-008-018 |
| CHK016 | [ ] | PARTIAL | [R-004](research.md#L40) gives 15min/3 levels; actual durable timer/policy authority and cascading behavior incomplete. | AUD-008-013, AUD-008-037 |
| CHK017 | [ ] | PARTIAL | [R-004 chain](research.md#L51) says incident-management hierarchy; helper ignores supplied commander_chain and fabricates IDs. | AUD-008-013 |
| CHK018 | [ ] | PARTIAL | [R-014](research.md#L154) resolves first-write-wins in prose; actual endpoint omits etag and tests are sequential local calls. | AUD-008-011, AUD-008-022 |
| CHK019 | [ ] | PARTIAL | Max-depth/no-auto-approve is stated and no auto-approve code exists; critical hold/deadline/chain not durable. | AUD-008-013 |
| CHK020 | [ ] | PARTIAL | [Cancel contract](contracts/health-endpoint.md#L253) permits only pre-delivery; in-flight title wording differs, persistence/race guards incomplete. | AUD-008-002, AUD-008-011, AUD-008-037 |
| CHK021 | [ ] | PARTIAL | [Review payload contract](contracts/communication-pipeline.md#L205) exists; actual helper only supplies audience IDs and dashboard shows static copy. | AUD-008-010 |
| CHK022 | [ ] | MISSING | Local approval outage policy does not specify durable retry/outbox; helper logs and swallows errors. | AUD-008-010, AUD-008-013 |
| CHK023 | [ ] | PARTIAL | [Modify contract](contracts/health-endpoint.md#L181) specifies a new version; helper bypasses durable allocation/review. | AUD-008-012 |
| CHK024 | [ ] | PARTIAL | [R-011](research.md#L121) resolves independent terminal states; expiry helper ignores time and scheduler absent. | AUD-008-025 |
| CHK025 | [ ] | PARTIAL | [Cancel contract](contracts/health-endpoint.md#L253) defines states, but trusted actor, durable cancel and race behavior remain. | AUD-008-001, AUD-008-011 |
| CHK026 | [ ] | CONFLICT | Status-only supersession is allowed, but timing differs between FR-017, FR-018 and US2-AS4; needs an explicit rule. | AUD-008-023, AUD-008-024, AUD-008-037 |
| CHK027 | [ ] | MISSING | All-clear with superseded/cancelled original has no validated runtime/contract path in S1/S4. | AUD-008-024, AUD-008-037 |
| CHK028 | [ ] | PARTIAL | [Data model](data-model.md#L17) requires change_summary but no meaningful diff/why policy; code accepts string None. | AUD-008-023, AUD-008-037 |
| CHK029 | [ ] | PARTIAL | Monotonic history is specified, but no operational pagination/version-growth policy or full history access. | AUD-008-025, AUD-008-037 |
| CHK030 | [ ] | PARTIAL | OCC retries are specified; [unreserved fallback](../../apps/agents/communication/versioning.py#L127) violates the uniqueness obligation. | AUD-008-022 |
| CHK031 | [ ] | PARTIAL | [R-007](research.md#L75) resolves multiplication order; activation conditions and per-language quality penalties are wrong/incomplete. | AUD-008-020, AUD-008-021 |
| CHK032 | [ ] | CONFLICT | SC-001 includes stages 4-7; contract sum is 24s, code measures only stage 5. | AUD-008-030, AUD-008-035, AUD-008-037 |
| CHK033 | [ ] | CONFLICT | [R-012](research.md#L132) discusses 60s but first initiation/completion and 35s/40s subtotals disagree. | AUD-008-030, AUD-008-035, AUD-008-037 |
| CHK034 | [ ] | CONFLICT | Multipart GSM-7 is documented; multilingual Unicode and FR-028 link-preserving truncation remain unaddressed. | AUD-008-032, AUD-008-037 |
| CHK035 | [ ] | CONFLICT | Actual question concerns queue depth versus concurrent work, not SLA arithmetic as plan cites; health uses total processed count. | AUD-008-028, AUD-008-029, AUD-008-037 |
| CHK036 | [ ] | PARTIAL | Segment-level 95% metric exists in prose; receipts/denominator/dedup reach are not validly implemented or measured. | AUD-008-005, AUD-008-015, AUD-008-035 |
| CHK037 | [ ] | UNVERIFIED | SC-008 survey is specified, but no sample/protocol/result proves the 90% operator rating. | AUD-008-035, AUD-008-036 |
| CHK038 | [ ] | UNVERIFIED | Capacity 50/429 is stated; no load test proving fair concurrent progress was found. | AUD-008-028, AUD-008-035 |
| CHK039 | [ ] | PARTIAL | Normal-operation health <=1s is specified; load definition and observed bound absent. | AUD-008-029, AUD-008-035, AUD-008-037 |
| CHK040 | [ ] | MISSING | [Stage 11](../../apps/agents/communication/pipeline.py#L637) has no actual reconciliation algorithm/query. | AUD-008-026 |
| CHK041 | [ ] | CONFLICT | [R-006](research.md#L64) requires recipient-level highest-priority dedup, code suppresses whole same-level segments. | AUD-008-005 |
| CHK042 | [ ] | PARTIAL | Actual question asks demographic source/schema/freshness, not just missing-data flags; pipeline trusts payload and picks dominant language. | AUD-008-007, AUD-008-016, AUD-008-037 |
| CHK043 | [ ] | MISSING | No estimate-versus-receipt accuracy/reconciliation policy in local contracts or segmenter. | AUD-008-015, AUD-008-016, AUD-008-037 |
| CHK044 | [ ] | PARTIAL | [Sort](../../apps/agents/communication/delivery.py#L151) uses critical then zone level; equal-priority tie/overlap/channel effects incomplete. | AUD-008-005, AUD-008-014 |
| CHK045 | [ ] | PARTIAL | New segmentation can be computed but no durable immutable audience-version snapshot or update/all-clear linkage. | AUD-008-009, AUD-008-016, AUD-008-023, AUD-008-024 |
| CHK046 | [ ] | PARTIAL | Title/body push shape exists, no targeted provider contract/action retention/payload bounds. | AUD-008-004, AUD-008-032 |
| CHK047 | [ ] | MISSING | EAS URL is specified; payload/auth/receipt contract and actual POST absent in S1/S4. | AUD-008-004, AUD-008-037 |
| CHK048 | [ ] | PARTIAL | Critical-first source exists; serial channels and whole-zone dedup prevent proof of intended across-channel reach/order. | AUD-008-005, AUD-008-014 |
| CHK049 | [ ] | MISSING | [SMS formatter](../../apps/agents/communication/delivery.py#L251) appends no link or reservation for it. | AUD-008-032, AUD-008-037 |
| CHK050 | [ ] | MISSING | No stable recipient/channel/version idempotency key or ambiguous-success reconciliation in delivery. | AUD-008-014 |
| CHK051 | [ ] | IMPLEMENTED | Actual question is confidence below upstream 0.7: [Assumptions](spec.md#L308) explicitly trusts upstream filtering. Plan/tasks incorrectly cite it for embeddings. | AUD-008-007, AUD-008-037 |
| CHK052 | [ ] | CONFLICT | Actual embedding-outage question is resolved differently by plan versus [R-002](research.md#L27); code fabricates score 0.5. | AUD-008-020, AUD-008-037 |
| CHK053 | [ ] | CONFLICT | [Retrieval contract](contracts/communication-pipeline.md#L57) requires retry on Cosmos outage; code invents data/ignores persistence failure. | AUD-008-007, AUD-008-009 |
| CHK054 | [ ] | MISSING | Superseded-assessment warning is required but no retrieval/approval check found in S1/S4. | AUD-008-007, AUD-008-010 |
| CHK055 | [ ] | MISSING | No specified operational timezone localization for content; [stage 4](../../apps/agents/communication/pipeline.py#L286) copies strings/default wording. | AUD-008-038, AUD-008-037 |
| CHK056 | [ ] | PARTIAL | [Cache eviction](../../apps/agents/communication/dedup.py#L42) is fail-open at capacity; restart duplicate side effects and replay/update safety untested. | AUD-008-008 |
| CHK057 | [ ] | PARTIAL | [Telemetry contract](contracts/telemetry.md#L44) gives per-language p95 1s; code measures entire safety stage only. | AUD-008-030, AUD-008-035 |
| CHK058 | [ ] | MISSING | No channel throughput/rate-limit contract or 50-alert load-to-send capacity proof. | AUD-008-004, AUD-008-014, AUD-008-035, AUD-008-037 |
| CHK059 | [ ] | CONFLICT | Actual question is regional replication policy, not JWT as plan/tasks claim; NFR-003 independent regions not mapped to active deployment. | AUD-008-031, AUD-008-037 |
| CHK060 | [ ] | PARTIAL | [Container table](data-model.md#L380) specifies no TTL; independent expiry/manual retention and actual deployed policy remain unverified. | AUD-008-025, AUD-008-031, AUD-008-035 |
| CHK061 | [ ] | CONFLICT | Actual auto-scaling question is resolved in R-010 but [Bicep](../../infra/modules/communication-agent.bicep#L209) uses HTTP, not queue depth. | AUD-008-031, AUD-008-037 |
| CHK062 | [ ] | MISSING | Actual question is approval authentication/security, not auto-scaling as plan/tasks claim; standalone routes have no JWT checks. | AUD-008-001, AUD-008-037 |
| CHK063 | [ ] | PARTIAL | [Risk producer](../../apps/agents/risk_assessment/agent.py#L462) supplies camelCase IDs, but communication fixtures/intake do not enforce that contract. | AUD-008-007, AUD-008-034 |
| CHK064 | [ ] | MISSING | No concrete demographic governance/freshness source binding in pipeline; dependency prose is not a data adapter. | AUD-008-007, AUD-008-016 |
| CHK065 | [ ] | CONFLICT | [Canonical tenant](../../apps/api/app/core/tenant_context.py#L13) and delivery prefix disagree; boundary-violation handling is unsafe. | AUD-008-003 |
| CHK066 | [ ] | PARTIAL | Evacuation polygons are mentioned in FR-022 but absent from explicit dependency list/data retrieval integration. | AUD-008-007, AUD-008-016, AUD-008-037 |
| CHK067 | [ ] | PARTIAL | [API contract](contracts/health-endpoint.md#L181) exists; dashboard uses flat static preview/other publication API, no connected live review refresh. | AUD-008-010 |
| CHK068 | [ ] | UNVERIFIED | Git PR governance is a design decision, not template-specific approval identities/revisions. | AUD-008-036 |
| CHK069 | [ ] | PARTIAL | Segment-level tracking scope is explicit, but payload-only adapters and false-success records do not define valid segment receipt semantics. | AUD-008-004, AUD-008-015, AUD-008-037 |
| CHK070 | [ ] | PARTIAL | Escalated enum exists; process_approval always writes human_approved and no resolved escalation-mode semantics. | AUD-008-011, AUD-008-013, AUD-008-037 |
| CHK071 | [ ] | PARTIAL | Defaults/env pattern exists; operational ranges, required endpoint validation and exact parameter counts differ. | AUD-008-031, AUD-008-033, AUD-008-037 |
| CHK072 | [ ] | PARTIAL | Plain-language label exists but no Spec 008 accessibility acceptance rubric/sign-off; seed WCAG test addresses different templates. | AUD-008-032, AUD-008-035, AUD-008-036 |

### Sixteen Checked Quality Claims

QC IDs are local labels for the 16 originally checked items in [checklists/requirements.md](checklists/requirements.md#L8), in order. The final statement All items pass validation is an authored assertion, not proof of a human review or implementation run.

| Claim | Original state | Status | Evidence assessment | Follow-up IDs |
| --- | --- | --- | --- | --- |
| QC01 No implementation details | [x] | CONFLICT | FR-006/009/015 explicitly prescribe SDK method, token enforcement and Cosmos etags; checklist caveat does not remove those details. | AUD-008-037 |
| QC02 User value/business needs | [x] | IMPLEMENTED | Eight stories explain public-warning/commander value and independent tests. | AUD-008-037 |
| QC03 Nontechnical stakeholder wording | [x] | PARTIAL | User stories are readable; FRs contain implementation-specific mechanics and unresolved vocabulary. | AUD-008-037 |
| QC04 Mandatory sections completed | [x] | IMPLEMENTED | Scenarios, requirements, entities, success criteria and assumptions exist in the fully read spec. | AUD-008-037 |
| QC05 No clarification markers | [x] | IMPLEMENTED | No unresolved NEEDS CLARIFICATION marker in the original spec; this does not mean no ambiguity. | AUD-008-037 |
| QC06 Testable/unambiguous requirements | [x] | CONFLICT | Supersession, dedup/update, outage, all-failed state and health-tier conflicts remain. | AUD-008-037 |
| QC07 Measurable success criteria | [x] | PARTIAL | Numerical targets exist but denominator, load conditions, survey sample and budget arithmetic need resolution. | AUD-008-035, AUD-008-037 |
| QC08 Technology-agnostic success criteria | [x] | PARTIAL | Outcome focus exists; stage-specific/token/service qualifications and budget references remain technical. | AUD-008-037 |
| QC09 Acceptance scenarios defined | [x] | IMPLEMENTED | Exactly 32 numbered scenarios are authored; execution is not established. | AUD-008-034, AUD-008-035 |
| QC10 Edge cases identified | [x] | IMPLEMENTED | Nine explicit edge bullets exist; several lack implementation. | AUD-008-034 |
| QC11 Scope clearly bounded | [x] | PARTIAL | Scope/deferred-country clauses exist, but broadcast integration and overlapping lifecycle authority need resolution. | AUD-008-037 |
| QC12 Dependencies/assumptions identified | [x] | PARTIAL | Dependency list exists; evacuation-zone source, operational service contracts and retained runtime mapping incomplete. | AUD-008-007, AUD-008-037 |
| QC13 All FRs have clear acceptance | [x] | PARTIAL | Stories cover main flows, not complete escalation, provenance, runtime and conflict cases. | AUD-008-034, AUD-008-037 |
| QC14 Scenarios cover primary flows | [x] | IMPLEMENTED | Eight stories cover draft/review/send/target/version/safety/audit/degrade. This is document coverage only. | AUD-008-034 |
| QC15 Feature meets measurable outcomes | [x] | UNVERIFIED | No local measurement/exercise/sign-off record establishes SC-001 through SC-011. | AUD-008-035 |
| QC16 No implementation details leak | [x] | CONFLICT | Same explicit methods/storage/concurrency prescriptions as QC01; cannot be treated as a verified quality pass. | AUD-008-037 |

### Plan Gate Claims

All 23 pre-design gates in [plan.md](plan.md#L49) say PASS, and [post-design review](plan.md#L77) claims all 23 passed again. No reviewer identity/date-specific signed output beyond authored prose proves either review occurred. Each row below assesses both occurrences of the claim.

| Gate | Status | Source-based assessment | Follow-up IDs |
| --- | --- | --- | --- |
| PG01 Life safety/SLA/critical-first | PARTIAL | Critical sort exists; lossy dedup, missing guidance and unmeasured timings defeat full claim. | AUD-008-005, AUD-008-016, AUD-008-035 |
| PG02 Human override/emergency stop | CONFLICT | Unauthenticated actions and unguarded delivery/publication remain. | AUD-008-001, AUD-008-002 |
| PG03 Commander explanations | PARTIAL | Draft fields exist, but complete review notification/dashboard binding absent. | AUD-008-007, AUD-008-010 |
| PG04 Stale/low-confidence degradation | CONFLICT | Always-on freshness and false quality scores; incomplete approved fallbacks. | AUD-008-017, AUD-008-020, AUD-008-021 |
| PG05 Explicit validated handoffs | PARTIAL | Generic handoff model exists; source/payload/references and consumer not wired. | AUD-008-006, AUD-008-007 |
| PG06 No silent mutations | PARTIAL | Mutable local alerts, unconditional writes and incomplete audit transitions remain. | AUD-008-009, AUD-008-011, AUD-008-026 |
| PG07 AIIMS human approval | CONFLICT | A helper/different API can publish/deliver without durable authorized approval. | AUD-008-002 |
| PG08 Provenance | PARTIAL | IDs present but fallback can invent references and audits omit key fields. | AUD-008-007, AUD-008-026 |
| PG09 Freshness | CONFLICT | Conditional staleness assessment absent; default penalty always applied. | AUD-008-021 |
| PG10 Versioned reproducible output | PARTIAL | Local ID sequence exists; reservation fallback/races and no replay evidence. | AUD-008-022, AUD-008-035 |
| PG11 Data minimization | PARTIAL | Segment-level model avoids direct contact fields, but actual provider target resolution and full audit privacy contracts incomplete. | AUD-008-004, AUD-008-026 |
| PG12 Regional residency/isolation | UNVERIFIED | Uncomposed module/parameter is not deployed region or isolation evidence. | AUD-008-031, AUD-008-035 |
| PG13 Tenant isolation | CONFLICT | Non-live prefix mismatch plus live-default audit and counter/dedup scope gaps. | AUD-008-003 |
| PG14 Prompt protection | PARTIAL | General system warning/character sanitation exist; complete scoped input and layered checks missing. | AUD-008-019, AUD-008-038 |
| PG15 Accessible multilingual content | PARTIAL | Six-language assets exist but matrix, minority targeting, SMS actions and review evidence incomplete. | AUD-008-016, AUD-008-017, AUD-008-032, AUD-008-036 |
| PG16 Safety/template governance | PARTIAL | Wrapper checks output; failure metadata, layers and offline approval proof incomplete. | AUD-008-018, AUD-008-019, AUD-008-036 |
| PG17 Three-channel independent delivery | CONFLICT | Broadcast is a log, missing clients succeed, retries are serial. | AUD-008-004, AUD-008-014 |
| PG18 Outbound logging | PARTIAL | Delivery audit lacks audience/content/language/approval-mode details. | AUD-008-026 |
| PG19 Azure/AU platform | UNVERIFIED | Azure resources are authored, not evidence of complete operational AU-only deployment. | AUD-008-031, AUD-008-035 |
| PG20 Resilience | PARTIAL | Fallback/buffer code exists; single failures can discard work or fake success and recovery is absent. | AUD-008-007, AUD-008-008, AUD-008-027, AUD-008-029 |
| PG21 Append-only audit | PARTIAL | Primary create_item/no TTL declarations support intent; completeness/replay/operational persistence unproven. | AUD-008-026, AUD-008-027 |
| PG22 WAF/observability/scaling/security | PARTIAL | Definitions exist, but unused metrics, wrong scaler and absent commander authentication remain. | AUD-008-001, AUD-008-030, AUD-008-031 |
| PG23 Scenario tests/reproducibility | PARTIAL | Relocated tests exist but do not execute full requested scenarios or establish outcomes. | AUD-008-034, AUD-008-035 |

The post-design six supporting statements (multipart SMS, capped escalation, compound penalties, delivery dedup, JWT and PR-governed templates) are individually addressed by AUD-008-032, AUD-008-013, AUD-008-021, AUD-008-005, AUD-008-001 and AUD-008-036. The claim No Constitution Check violations is therefore unsupported as an implementation conclusion. Historical principle numbering also no longer matches the current constitution; preserve the versioned context rather than silently treating old section numbers as current authority.

### Research, Contract, and Evidence Claims

| Research ID | Status | Decision versus implementation/evidence | Follow-up IDs |
| --- | --- | --- | --- |
| R-001 | PARTIAL | Sequential en-AU-first defaults and temperature 0 exist; config order and deterministic live model output not proven. | AUD-008-033, AUD-008-035 |
| R-002 | CONFLICT | Semantic embeddings/skip outage specified; word overlap/0.5 substitution implemented. | AUD-008-020 |
| R-003 | PARTIAL | LLM wrapper validates; safety-fallback templates are revalidated and original outcome is lost. | AUD-008-018, AUD-008-019 |
| R-004 | PARTIAL | No auto-approval source is positive; real chain, initial timer, durable hold and timeout authority absent. | AUD-008-013 |
| R-005 | CONFLICT | GSM-7 four-part assumption does not cover multilingual encoding; rejection of link truncation conflicts with FR-028. | AUD-008-032, AUD-008-037 |
| R-006 | CONFLICT | Recipient overlap dedup is not same-level whole-segment suppression. | AUD-008-005 |
| R-007 | PARTIAL | Multiplication order exists; stale-data activation and measured back-translation condition do not. | AUD-008-020, AUD-008-021 |
| R-008 | PARTIAL | Git-managed JSON assets exist; full matrix/visible missing-language fallback and PR sign-off proof incomplete. | AUD-008-017, AUD-008-036 |
| R-009 | MISSING | No commander JWT verification in the standalone approval/read routes. | AUD-008-001 |
| R-010 | CONFLICT | Queue-depth scaling design is replaced by HTTP scaling without a Spec 008 acceptance resolution. | AUD-008-031, AUD-008-037 |
| R-011 | PARTIAL | Enum distinction exists but actual timed expiry/lifecycle/history integration incomplete. | AUD-008-023, AUD-008-025 |
| R-012 | CONFLICT | Draft/stage totals and initiation-versus-completion arithmetic disagree; no latency measurements prove targets. | AUD-008-030, AUD-008-035, AUD-008-037 |
| R-013 | PARTIAL | segment_count exists but <=160 single-part and multilingual encoding are not implemented correctly. | AUD-008-032 |
| R-014 | PARTIAL | OCC-shaped helper exists; endpoints omit etag and conflict test does not race durable writes. | AUD-008-011, AUD-008-022 |

- The 11-stage contract is authored, not an execution trace. Stages 1/2/8 have validation/durability defects, stage 9 is a stub, stage 10 is not invoked on approval, and stage 11 does not reconcile. Individual obligations map to AUD-008-006 through AUD-008-030.
- All eight pipeline invariants are assessed: human approval (002), all LLM checks (018/019), every-step audit (026), independent channels (014), always-available approved templates (017), dual dedup (005/008), conditional deterministic penalties (020/021), and simulation no-send (003).
- The health/API contract's seven routes are authored. /health is partial (029); approve/reject are partial (001/011); modify/cancel are partial (012/011); GET alert is local-only (009/025); delivery-status is a placeholder (015). Required error envelopes/409 conflict details and authentication remain incomplete.
- The telemetry contract contains **22 enumerated metric rows**, despite plan/T055 prose claiming 23, plus **17 custom events** and **8 alerting rules**. Definitions are not emitting paths or provisioned rules. AUD-008-030/AUD-008-037 require an exact reconciled signal inventory and later exporter/rule evidence.
- All eleven phase checkpoint statements in [tasks.md](tasks.md) claim operational completion, tests pass or working behavior. They are not run records: Phase 1 assets/approval (017/036); Phase 2 models/config (033); Phases 3-10 map to the eight story coverage tables; Phase 11 integration/deployment/quickstart (031/034/035). The TDD instruction to write failing tests first has no retained red/green execution evidence in S7.
- [Quickstart](quickstart.md) setup, expected logs, sample health, class-based draft example, integration/scenario paths and Docker target are instructions, not observations. The module launcher is a no-op, CommunicationAgent is absent, relocated test paths differ, and the shared Dockerfile has no communication target. T064 remains UNVERIFIED, not automatically missing.
- The three local HYP stubs are authored artifacts with explicit Not tested status. Country-specific thresholds, legal prerequisites, native review and D-009 clearance remain unverified; no implementation work is authorized by this audit solely to remove that status.

## Future Validation Catalogue

**Nothing in this section was executed.** Later agents need separate authorization for source/test changes and any service, deployment, benchmark or human-exercise work. All Python commands below run from the repository root in a selected Python 3.12+ environment containing root development extras and the agent/API dependencies required by the selected test. [tests/conftest.py](../../tests/conftest.py#L10) supplies repository import paths; installation and interpreter selection must be verified by that tester. Clear production endpoints/credentials for hermetic tests and inject fakes at external boundaries. Never point public SMS/push/EAS tests at real recipients.

| Label | Future command or procedure | Prerequisites and expected assertions |
| --- | --- | --- |
| V-AUTH | `uv run pytest tests/unit/test_communication_endpoints.py tests/unit/test_communication_approval.py -q` | Implement auth with test signing keys/fake validation and shared conditional store. Assert all route permissions, tenant boundaries, state conflicts, full metadata/error contracts, modify/reject/cancel and exact send gating. No network calls. |
| V-PIPELINE | `uv run pytest tests/unit/test_communication_pipeline.py tests/unit/test_communication_handoff.py tests/unit/test_communication_dedup.py -q` | Canonical risk-producer payloads, strict store fakes, real pipeline and deterministic clock. Assert retrieval/reject/retry/dedup semantics, six-language review aggregate, 50/51 admission and no premature delivery. |
| V-ISOLATION | `uv run pytest tests/unit/test_communication_delivery.py tests/unit/test_communication_handoff.py tests/unit/test_communication_versioning.py tests/unit/test_communication_audit.py -q` | Add live/non-live UUID/prefixed/invalid tenants and repeated IDs in separate partitions. Assert zero non-live provider calls and no cross-scope reads/counters/dedup/audits. |
| V-DELIVERY | `uv run pytest tests/unit/test_communication_delivery.py tests/unit/test_communication_endpoints.py -q` | Approved durable fixtures, recipient sets/polygons and strict SMS/push/EAS fakes. Assert actual provider request/response semantics, overlap-preserving one-send behavior, independent retries, encoding/actionable content and exact aggregates. |
| V-SEGMENT | `uv run pytest tests/unit/test_communication_segmentation.py -q` | Three real polygons, disjoint same-level zones, 80-person aged-care and minority-language demographic fixtures. Assert geography, proportions, guidance, estimates and missing-data disclosures. |
| V-CONTENT | `uv run pytest tests/unit/test_communication_translator.py tests/unit/test_communication_pipeline.py tests/contract/test_communication_llm.py -q` | Unskip/replace obsolete class test; inject LLM/embedding/moderation at client boundary, not the entire wrapper. Use all six language templates and safety negatives. Assert real embeddings/skip semantics, conditional penalties, failure provenance, all-clear/correction actions, prompt scope and actual budgets. |
| V-VERSION | `uv run pytest tests/unit/test_communication_versioning.py tests/unit/test_communication_approval.py tests/unit/test_bushfire_alert_scenario.py -q` | Etag-enforcing shared fake store, controlled UTC clock, tenant-scoped counter and resolved supersession policy. Assert reserved unique versions, immutable originals, safe edits, all-clear scope, expiry/history and restart behavior. |
| V-AUDIT | `uv run pytest tests/unit/test_communication_audit.py tests/unit/test_communication_pipeline.py -q` | Capture append-only store, tmp_path spill, controllable disk/storage failures and clock. Assert all expected decision types/fields, same-tenant correlation, chronological idempotent replay and accurate tier/depth transitions. |
| V-MODELS | `uv run pytest tests/unit/test_communication_models.py tests/unit/test_communication_config.py tests/unit/test_communication_alert_schema.py -q` | Complete operational schemas/configuration matrix and known valid fixtures. Assert positive serialization plus all invalid bounds, missing fields, collections, state transitions and hash changes. |
| V-TELEMETRY | `uv run pytest tests/unit/test_communication_pipeline.py tests/unit/test_communication_delivery.py tests/unit/test_communication_approval.py -q` | Add capture meter/tracer assertions in these existing homes. Verify reconciled metric/event inventory, balanced gauges, units, correlation and exact latency windows; mocking instrumentation away is not a pass. |
| V-SCENARIO | `uv run pytest tests/unit/test_cyclone_alert_scenario.py tests/unit/test_bushfire_alert_scenario.py tests/unit/test_flood_alert_scenario.py -q` | Strengthen relocated scenarios using full six-language pipeline, durable fakes and approved-target provider spies. Assert cyclone end-to-end, bushfire v1-v4, flood minority-targeting/overlap/outage and complete audit. |
| V-INTEGRATION | `uv run pytest tests/integration/test_hitl_round_trip.py -q`; after authored, `uv run pytest tests/integration/test_communication_cosmos.py tests/integration/test_communication_service_bus.py -q` | The latter paths are **proposed**, not present evidence. Use strict protocol fakes first, then separately authorized isolated Cosmos/Service Bus resources for actual SDK partition/etag/ack/dead-letter/receipt contracts. Record which mode ran and all skips. No public dissemination. |
| V-WEB | Later run the existing web test runner for the alert-composer flow after selecting its actual existing E2E home. | Mock or isolated authenticated API with six-language persisted preview; validate version-specific approve/reject/modify, stale warning, failed queue/delivery display and no hard-coded actor/content. Tester must inspect package scripts before choosing an exact runner command. |
| V-PERFORMANCE | `uv run pytest tests/benchmark/test_pipeline_performance.py -k communication --benchmark-only`; `uv run pytest tests/unit/test_communication_reproducibility.py -q` | First fix duplicate-only/unchecked benchmark and expand reproducibility assertions. Mock results are not operational SLA evidence. Later authorized load run: 50 independent alerts, all stages/receipts, controlled model/template/config versions, approval wait excluded, p50/p95/p99 and drop/reach denominators recorded. |
| V-INFRA | Later run the repository's Bicep validation and authorized what-if workflow against the actual composed entrypoint. | Consult current Azure policy/AVM/role guidance first; no commands are fabricated here for unknown subscription/resource group. Assert resource reachability, tenant partitions/retention, AU locations, identity permissions, exact env/channel/port/probes, queue scaling and cross-region boundaries. Record compiled/what-if evidence separately from actual deployment. |
| V-QUICKSTART | After repairs, `uv run python -m communication` from the documented agent workspace and `Invoke-RestMethod http://localhost:8084/health` in a separate shell. | Only if that runtime/port is retained; otherwise use the explicitly approved replacement instructions. Capture startup/shutdown, six approved templates, true health/degradation and a sandbox handoff-review-delivery trace. Commands must not use production recipients. |
| V-EXERCISE | Structured operator/native-language review with version-bound approval records and a retained survey/evidence record. | Obtain human consent/authority and approved scenarios. Report sample size, >=90% clarity/actionability/targeting results, accessibility/native review, country preconditions and HYP measurement windows. Do not substitute synthetic ratings for people. |
| V-DOCS | Text-only cross-reference, coverage, arithmetic, schema/enum and Markdown-link validation. | Preserve original evidence until a separately authorized documentation change; all conflicting decisions need explicit owner sign-off. Recheck 64 original IDs, 61 requirements, 32 scenarios, 9 edges, amendments and checklist numbering. |

## Document Validation and Limitations

Text-only validation passed: **64/64 original task rows with exact checkbox states, 61/61 requirement rows, 32/32 acceptance scenarios, 9/9 edge cases, 10/10 additional amendment IDs, 72/72 CHK rows, 16/16 quality claims, 23/23 plan gates, and 14/14 research decisions**. All **38 remediation tasks are unchecked**, have unique stable IDs and separate developer/tester/completion fields, and every follow-up reference resolves to a defined task. All **280 unique local Markdown links resolve**, including checks that cited line numbers are within their target files. Editor `get_errors` reported **no errors** after correcting the report's initial Markdown label/newline warnings. The text checker's quality/gate label pattern was also corrected; no original document was changed. These checks validate the document, not application behavior or semantic correctness of a runtime claim.

Remaining limitations are intentional: no runtime/type-check/SDK execution, installed-environment verification, benchmark, live receipt, cloud-resource observation, PR approval lookup, human survey or deployment evidence was obtained. Provider behavior and requested outcomes remain unverified where source alone cannot prove them. Searches were limited to the recorded implementation/test/infrastructure/evidence scopes, not other audit reports or undisclosed external systems. This report does not authorize implementation, public messages, changed task checkboxes, or promotion of deferred country capabilities.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 008 only. Three parallel technical reviews examined
authentication/approval/isolation, runtime/persistence/delivery, and versioning/escalation/audit. The current source
has substantial partial remediation, including tenant-aware repositories, guarded delivery checks, ETag-aware storage,
and approval queue publishing. No safe local edit was applied because the remaining highest-risk gaps cross runtime
composition and external contracts: there is no communication Service Bus intake consumer, approval can still fall
back to in-memory decisions in tests/runtime paths, crash recovery is incomplete, and the composed Azure deployment
does not prove this service is selected.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| AUD-008-001 / 002 / 003 / 007 / 008 / 011 | Partial source remediation. | Current code includes token/tenant-aware helpers, persisted approval checks, scoped repositories, dedup reservations, and conditional storage support; assigned-commander enforcement, canonical scope validation, durable-only approval, crash recovery, and alternate API/MAF path convergence remain open. |
| AUD-008-004 / 006 / 009 / 010 / 014–017 | Partial or disconnected runtime. | Delivery adapters and runtime composition exist, but provider receipts, queue intake, durable aggregate/read-after-restart, dashboard integration, and complete overlap/segmentation evidence remain unverified. |
| AUD-008-012–038 | Contract/evidence-gated. | Versioning, escalation policy, template semantics, accessibility/native-language review, performance, infrastructure reachability, Azure identity, provider credentials, and human approval evidence require explicit owner/provider/deployment validation. |

No public delivery, live Service Bus/Cosmos/Entra/provider operation, Azure deployment, human template approval, or
performance measurement was performed. The report remains open despite substantial source remediation.

### 2026-09-19 Continuation Validation

The core local communication surfaces were executed after the shared ingestion/import repairs:
`test_communication_delivery.py`, `test_communication_pipeline.py`, `test_communication_approval.py`, and
`test_communication_endpoints.py` returned `102 passed, 2 warnings`. No additional source patch was needed in these
surfaces. Queue intake, durable cross-process approval/recovery, composed deployment, provider receipts, performance,
and human approval evidence remain open.

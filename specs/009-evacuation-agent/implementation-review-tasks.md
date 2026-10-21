# Evacuation Agent Implementation Review and Remediation Tasks

## Review Scope

- Review date: **2026-09-11**.
- Reviewed source revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**, confirmed against local HEAD.
- Scope: specification **009-evacuation-agent**, including its amendments and the actual producers, consumers,
  shared runtime, storage configuration, and test assertions needed to evaluate its obligations.
- Authority: [Review Contract](../001-spec-implementation-audit/README.md#L13).
- This is an independent, static, review-only audit. No other implementation-review report was read or used.
  No product tests, imports, builds, benchmarks, deployments, cloud queries, or external approvals were performed.
  No original document, checklist, task state, source, test, infrastructure, or central inventory was changed.
  No branch, commit, or delegation was created. This report is the sole authored artifact.
- Tracked source was clean at review start; unrelated untracked audit artifacts were left untouched.
- Coverage inventory: **59 original tasks, all originally [x]; 40 FRs, 2 NFRs, 10 SCs; 25 acceptance scenarios;
  9 edge cases; 14 amendment IDs; 100 originally unchecked checklist items**.
- Findings below are source-backed defects or explicitly qualified evidence gaps, not claims of observed runtime
  failures. Every future command requires separate developer/tester authorization. No runtime success is inferred.

### Inputs Read

Read in full: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md),
[contracts/evacuation-pipeline.md](contracts/evacuation-pipeline.md),
[contracts/health-endpoint.md](contracts/health-endpoint.md), [contracts/telemetry.md](contracts/telemetry.md),
[checklists/requirements.md](checklists/requirements.md), [evidence/HYP-030.md](evidence/HYP-030.md),
[evidence/HYP-031.md](evidence/HYP-031.md), and [evidence/HYP-032.md](evidence/HYP-032.md).
These are all 13 files inventoried in the target folder before this report; no separate local review record exists.

Applied the [code-review instructions](../../.github/instructions/code-review.instructions.md),
[constitution](../../.specify/memory/constitution.md), and applicable
[Bicep review baseline](../../.github/instructions/bicep-code-best-practices.instructions.md) and
[policy constraints](../../.github/instructions/bicep-policy-compliance.instructions.md).
The Python fact-grounded-coding skill was read; only source facts were collected because execution is prohibited.
No claim is made about interpreter state, installed SDK behavior, live policy compliance, or deployment state.

Read every task-named evacuation source and test file. Additional inspected paths include the upstream
[HazardAssessment](../../packages/domain/src/domain/models/hazard_assessment.py#L7),
[handoff producer](../../apps/agents/risk_assessment/agent.py#L491), shared
[handoffs](../../apps/agents/common/handoffs.py#L1),
[LLM mixin](../../apps/agents/common/llm_mixin.py#L62),
[content safety](../../apps/agents/common/content_safety.py#L111), MAF facade and executor,
dispatcher, stage-management API, rehearsal service, telemetry, packaging, and relevant local infrastructure.
Linked [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md) and
[post-feature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md) were inspected only to assess HYP-007.

### Status Semantics

| Status | Interpretation in this report |
| --- | --- |
| IMPLEMENTED | Inspected source supports the scoped behavior or authored artifact; execution is not implied. |
| PARTIAL | A substantive subset exists, with a stated missing or contradictory obligation. |
| MISSING | Required behavior/artifact was not found after the documented scoped search. |
| CONFLICT | Specification, design decisions, task instructions, or behavior disagree. |
| UNVERIFIED | Execution, performance, approval, exercise result, or deployment cannot be established. |
| SUPERSEDED | Explicit repository evidence establishes replacement; replacement completeness is assessed separately. |

## Executive Assessment

**Not implementation-complete.** The repository contains substantial graph, zone, transport, timeline, and audit
code, but several safety-critical connections are absent or contradicted. Checked original tasks do not establish
delivery. The most serious findings are ignored hazard-capacity adjustments, acceptance of incomplete assessments,
unauthenticated commander actions, broken immutable override semantics, and lost/inverted emergency dispositions.

Positive source evidence includes the package/version export, declared Shapely dependency, the requested sample
network and facilities, deterministic neighbor traversal, explicit pre-existing road closure exclusion, basic
four-category vehicle estimation, the literal clearance formula and 1.5 multiplier, template fallback, and
append-only primary audit writes. These do not establish end-to-end safety or readiness.

### Actual Execution Paths and Replacement Search

| Path | Inspected controlling behavior | Assessment |
| --- | --- | --- |
| Standalone agent | [agent.py](../../apps/agents/evacuation/agent.py#L712) and [package entrypoint](../../apps/agents/evacuation/__main__.py#L26) construct an agent without stores/population/facilities, then start HTTP only. | Consumer exists but is not started; dependency bootstrap is absent. AUD-009-006. |
| Direct pipeline | [process_handoff](../../apps/agents/evacuation/pipeline.py#L111) reaches ten nominal stages; most tests invoke it with no external stores. | Meaningful implementation, but unsafe intake, zone preparation, incomplete persistence/audit, and reduced output contracts. |
| Container runtime | [Dockerfile](../../apps/agents/Dockerfile#L48) starts dispatcher; [dispatch handler](../../apps/agents/dispatcher/agent.py#L210) produces text, not EvacuationPlan. | This is a simulation conversation surface, not a replacement for deterministic evacuation planning. |
| MAF replacement | [deprecation notice](../../apps/agents/common/handoffs.py#L1), [workflow](../../apps/agents/maf_runtime/workflow/builder.py#L131), [executor dispatch](../../apps/agents/maf_runtime/workflow/executors/_base.py#L202), [facade](../../apps/agents/maf_runtime/agents/evacuation_agent.py#L32). | Legacy handoff transport is explicitly SUPERSEDED as an architectural mechanism, but the facade constructs an empty v1 plan. Optional routing output is logged, not attached. |
| MAF model path | [factory](../../apps/agents/maf_runtime/agents/_factory.py#L269) sends input to the model and parses a plan. | Does not invoke graph computation; it cannot substitute for FR-005's graph-only routing. AUD-009-006. |
| Web evacuation API | [stage routes](../../apps/api/app/api/routes/evacuation.py#L83) call [stage state machine](../../apps/agents/evacuation/stages.py#L37). | Decision/Warning/Withdrawal/Shelter/Return state management is not the five population phases or a persisted route-plan review endpoint. |
| Rehearsal | [rehearsal service](../../apps/api/app/services/rehearsal_orchestrator.py#L31) calls [review](../../apps/agents/evacuation/agent.py#L261). | Returns canned corridor advice, not the handoff pipeline or reproducibility comparison. |

Negative searches used tracked-file searches over `apps/agents`, `apps/api`, `infra`, relevant `tests`, `docs`,
`.github/workflows`, and the target folder. No other audit report was searched or opened. Specifically:

- Searches for `run_consumer`, `EvacuationAgent`, and `EvacuationProcessingPipeline` found no application call
  starting the evacuation consumer; the alternate paths above were followed before reporting the gap.
- `compute_zones_multi_hazard`, `detect_material_change`, `can_recover_from_shelter`, and
  `generate_route_rationale_template` have definitions/tests but no executable application caller using them
  for the required behavior in the inspected agent/API paths.
- Searches for `EvacuationPlan`, `EvacuationDecisionRecord`, `evacuation-plans`, and `evacuation-decisions`
  in the API and storage declarations found no owned-plan review/history or audit-query API. Stage records,
  workflow checkpoints, emergency-plans, and generic governance/evidence containers were inspected as alternatives.
- Literal searches for `evacuation-plans`, `evacuation-decisions`, and `evacuation-handoffs` in local infrastructure
  and workflows found no corresponding deployment declarations. This is not a claim about deployed resources.
- The HYP-007 named evidence file was absent; the linked evidence directory and HYP-007 references in local
  evidence/docs were searched. Aggregate rubric snapshots are not a per-spec consultation/approval record.
- No local target execution log, signed commander survey, or measured 50-plan/30-second/15-second result was found.
  General load and paired-exercise tests were inspected and are not proof of this pipeline's outcomes.

## Prioritized Open Remediation Tasks

All 36 tasks below remain **unchecked**. P0 is safety/security critical; P1 blocks reliable delivery; P2 addresses
required evidence or design governance. Task IDs are stable within this audit. Developer and tester instructions
are separate; tests and commands described here are **future work only**.

### AUD-009-001

- [x] **AUD-009-001 (P0): Apply hazard closures and effective capacities to the graph actually routed.**

**Affected**: FR-005, FR-006, FR-009c, FR-009d, SC-003; T008, T015, T018, T020, T025, T028, T059; US1-AS2, US2-AS1.
**Expected / actual / impact**: Zone 1 closes roads and Zones 2/3 retain 50%/75% capacity.
[Stage 4](../../apps/agents/evacuation/pipeline.py#L597) ignores the return from
[apply_zone_capacity_reduction](../../apps/agents/evacuation/zones.py#L154), which constructs copies.
It then examines the unchanged input list and only applies closures, never reduced capacities. Routes can therefore
cross the computed danger area and use optimistic capacities. [Tests](../../tests/unit/test_evacuation_zones.py#L260)
assert the helper's returned copy, not the pipeline graph.
**Developer instructions**: Consume the returned edge state and route on a per-plan effective graph containing both
closures and adjusted capacities. Preserve external closures and avoid accumulating reductions across plans or tenants.
Resolve partial-Zone-1 policy under AUD-009-036 before changing boundary semantics.
**Tester instructions**: Extend [pipeline tests](../../tests/unit/test_evacuation_pipeline.py#L70) and zone/router tests.
Use a small graph with an unsafe shortcut, a safe bypass, one road per zone, and an explicit external closure.
Assert actual routed capacities 0/500/750 for a 1,000-capacity baseline, exclusion of the shortcut, and unchanged base
data after repeated/live/simulation processing. Run future V-ROUTE and V-PIPE.
**Dependencies / completion**: AUD-009-014, AUD-009-036 for zone policy; complete when persisted route choices and
timelines demonstrably use adjusted capacities and tests fail if the helper return is discarded.

### AUD-009-002

- [x] **AUD-009-002 (P0): Reject invalid handoffs and adapt the real upstream assessment contract.**

**Affected**: FR-001, FR-002, FR-004, FR-019, SC-002; T020, T022, T024; US1-AS1/AS4; EC-01.
**Expected / actual / impact**: Both referenced records must exist, with valid hazard geography.
[Intake](../../apps/agents/evacuation/pipeline.py#L383) only checks target and duplicate ID;
[retrieval](../../apps/agents/evacuation/pipeline.py#L448) substitutes payload/default bushfire/high/1,000-person data
on missing assessment or read failure. It never retrieves the recommendation. The real
[upstream model](../../packages/domain/src/domain/models/hazard_assessment.py#L7) nests area/type/time horizon in
`hazard_map`; [Stage 3](../../apps/agents/evacuation/pipeline.py#L516) looks at top-level keys instead.
The [producer](../../apps/agents/risk_assessment/agent.py#L491) sends references, not the enriched payload used in tests.
**Developer instructions**: Add a validated intake adapter using the shared handoff envelope and canonical
HazardAssessment/Recommendation records. Enforce source, target, IDs, incident/tenant agreement, valid nonempty
geometry, and required hazard attributes. Reject true absence/malformed records with a reasoned audit; retain
transiently unavailable work for recovery rather than inventing assessment facts. Preserve upstream confidence.
**Tester instructions**: Use actual serialized upstream models in
[handoff contract tests](../../tests/contract/test_evacuation_handoff.py#L111) and pipeline tests, with strict scoped
stores. Cover valid nested hazard_map, missing recommendation, missing assessment/map, wrong source, empty IDs,
malformed geometry, tenant mismatch, 404 versus timeout, and malicious payload overrides. Assert no plan on rejection,
the exact rejection reason, and actual upstream area/type/time/confidence on success. Future V-INTAKE and V-PIPE.
**Dependencies / completion**: AUD-009-008, AUD-009-023, AUD-009-026; complete when a real producer-shaped handoff works
without extra test-only fields and incomplete records cannot produce a plan.

### AUD-009-003

- [x] **AUD-009-003 (P0): Enforce authenticated commander authority and tenant scope on control actions.**

**Affected**: FR-022, FR-024, FR-025; T041, T042, T043, T044; US6-AS3, US7-AS1/AS3; CHK047, CHK091.
**Expected / actual / impact**: Commander identity, role, and incident authority must be trusted and auditable.
[Request models](../../apps/agents/evacuation/agent.py#L323) accept arbitrary user/role/justification strings;
[create_app](../../apps/agents/evacuation/agent.py#L360) installs no authentication/authorization dependency.
Replan omits identity/justification entirely. Any caller reaching these endpoints can assert authority; this audit
does not assert that the internal service is internet-exposed.
**Developer instructions**: Bind authenticated identity and authorized incident/tenant scope to both endpoints,
reject body identity spoofing, require a nonblank justification, and authorize each action before lookup/mutation.
Reuse the repository's identity boundary rather than create a separate trust convention. Do not default unknown
tenant context to live for privileged actions; preserve emergency human-approval boundaries.
**Tester instructions**: Extend [endpoint tests](../../tests/unit/test_evacuation_endpoints.py#L74) with authenticated
commander, unauthenticated caller, noncommander, commander from another tenant/incident, forged role/user fields,
blank/whitespace justification, and replayed authorization. Assert denial before any persistence/audit-as-success,
trusted identity in accepted audit, and no cross-tenant reads. Future V-CONTROL with test identity fixtures only.
**Dependencies / completion**: Coordinate the shared auth boundary independently of other audits; AUD-009-004 and
AUD-009-010 must use it. Complete when every control action is scoped and authorized by server-trusted identity.

### AUD-009-004

- [x] **AUD-009-004 (P0): Make commander overrides real, immutable, and concurrency-safe.**

**Affected**: FR-017, FR-022, FR-023, FR-024, FR-029; T006, T012, T041, T043; US6-AS3, US8-AS2.
**Expected / actual / impact**: Status transitions act on an existing scoped plan; modifications create a linked new
version. [Override lookup](../../apps/agents/evacuation/agent.py#L529) incorrectly uses `plan_id` as partition key.
`modify` maps to proposed, but none of the allowed transition sets permits that target, so stored-plan modification
is rejected. The later [mutation block](../../apps/agents/evacuation/agent.py#L554) would update the original document
with unvalidated fields and unconditional upsert; without Cosmos the endpoint reports success without any plan.
The response lacks `new_version_plan_id`, and metadata omits structured role/action/original routes.
**Developer instructions**: Use trusted tenant/incident lookup, fail unavailable/missing store distinctly, validate
action-specific changes, clone a new numbered plan for route/zone/phase edits, and recompute dependent data. Enforce
ETag conflicts on permitted status-only updates; preserve original content and append the full override audit.
**Tester instructions**: Replace the no-store success fixture in endpoint tests with strict partition/ETag storage.
Cover all six actions, every terminal state, zone/route/phase modifications, empty modifications, unknown fields,
simultaneous commanders, and replan races. Assert 404/409/422 as contracted, original bytes preserved except permitted
status metadata, linked new version returned, and complete original/modified/user/role/reason/time audit. V-CONTROL.
**Dependencies / completion**: AUD-009-003, AUD-009-011, AUD-009-013, AUD-009-023, AUD-009-026; complete when no action can
claim success without a committed authorized change and `modify` cannot overwrite its source version.

### AUD-009-005

- [x] **AUD-009-005 (P0): Preserve correct emergency, shelter, and time-deficit dispositions in the plan and audit.**

**Affected**: FR-014, FR-015, FR-019, FR-028, SC-005; T032, T033, T034, T047, T053, T059;
US4-AS2, US8-AS3; EC-04, EC-07.
**Expected / actual / impact**: No-route immediate threats require maximum-urgency escalation; safe shelter and
partially unclearable populations need explicit instructions. [Estimator](../../apps/agents/evacuation/timeline.py#L266)
returns `recommended=False` for emergencies, but [Stage 7](../../apps/agents/evacuation/pipeline.py#L799) retains only
`recommended=True`. Later emergency telemetry loops over those shelter cases and tests nonexistent route key
`zone_number`, rather than using the emergency result. Immediate threats lose their structured disposition while
safe shelter can emit emergency events. Zero capacity also yields zero clearance time, and deficits only become
assumption text; no structured remaining-population shelter result is created.
**Developer instructions**: Carry one explicit disposition per zone through persistence: evacuation, shelter,
partial evacuation, or emergency escalation. Preserve urgency, affected population, prerequisites, and building,
supplies, and communication requirements. Route emergency notification through an authorized operator/services
integration without autonomously issuing public orders. Never represent blocked movement as zero-time clearance.
**Tester instructions**: Extend timeline, pipeline, flood simulation, and audit tests. Use blocked zones with known
safe and imminent horizons, unknown horizon, viable-but-too-slow routes, mixed clearable/unclearable zones, and a
later reopened route. Assert one correctly classified disposition/audit per zone, no safe-shelter false emergency,
an actual urgent notification boundary for imminent threat, remaining populations, and reduced confidence for deficits.
Exercise exact threshold boundaries after AUD-009-036. Future V-TIME, V-PIPE, and V-SCENARIO.
**Dependencies / completion**: AUD-009-002, AUD-009-009, AUD-009-021, AUD-009-023, AUD-009-036; complete when emergency and
deficit information survives retrieval intact and cannot be replaced by a reassuring zero-duration plan.

### AUD-009-006

- [x] **AUD-009-006 (P1): Connect the operational entrypoint and replacement runtimes to deterministic planning.**

**Affected**: FR-001, FR-005, FR-010, FR-019, FR-025, FR-035; NFR-001; T020, T021, T030, T044, T057.
**Expected / actual / impact**: A started agent receives trusted work with configured dependencies.
[Standalone startup](../../apps/agents/evacuation/__main__.py#L26) injects no Cosmos/population/facility data and starts
no consumer or road load. [Dockerfile](../../apps/agents/Dockerfile#L48) starts dispatcher instead. The
[MAF legacy path](../../apps/agents/maf_runtime/agents/evacuation_agent.py#L32) creates an empty v1 plan and discards
optional routing output; [MAF generation](../../apps/agents/maf_runtime/agents/_factory.py#L269) parses model-generated
plans without Dijkstra. [Rehearsal review](../../apps/agents/evacuation/agent.py#L261) remains canned advice.
**Developer instructions**: Establish one explicit supported bootstrap/adapter path with scoped stores, reference
data, intake lifecycle, shutdown, and road readiness. Make the MAF executor delegate deterministic domain planning
and use the model only for validated narrative. Preserve dispatcher conversational compatibility, but do not
misrepresent its text result or the stage API as a completed route plan. Document legacy retirement explicitly.
**Tester instructions**: Extend pipeline/Service Bus tests and
[equivalence test](../../tests/equivalence/test_evacuation_equivalence.py#L16) to invoke real adapters with hermetic
dependencies, not prewritten output pairs. Assert all supported modes produce nonempty required plan data or an
explicit rejection, and routing output is actually used. Test boot/stop, missing dependencies, and simulation scope.
Future V-PIPE, V-BROKER, and V-RUNTIME after bootstrap repair.
**Dependencies / completion**: AUD-009-002, AUD-009-023, AUD-009-030; shared runtime owners must preserve other agents'
contracts. Complete when the configured application path reaches the same safety-checked planner as focused tests.

### AUD-009-007

- [x] **AUD-009-007 (P1): Implement durable handoff acknowledgement and recoverable broker failures.**

**Affected**: FR-001, FR-002, FR-003, FR-035, SC-008; T021, T022, T055; EC-05, EC-08.
**Expected / actual / impact**: Intake acknowledgement must meet five seconds independently of planning, with
at-least-once recovery. [Consumer](../../apps/agents/evacuation/agent.py#L655) completes only after synchronous plan
processing and dead-letters every exception, including transient failures. There is no lock renewal, durable intake
boundary, reconnect loop, or rejection audit for malformed raw JSON. A swallowed plan-write failure can be completed
as successful work. [Broker tests](../../tests/integration/test_evacuation_service_bus.py#L179) do not call this loop.
**Developer instructions**: Define acknowledgement versus durable processing completion, capture receive timing,
and preserve work before early acknowledgement. Add bounded transient retry/redelivery, poison-message rejection,
lock management, cancellation, reconnect, and idempotent completion. Do not blindly acknowledge before durability.
**Tester instructions**: Drive `run_consumer` or its replacement through strict broker doubles in the existing
Service Bus test home; cover malformed payload, slow 30-second processing, lock expiry, timeout, connection loss,
restart after durable intake, duplicate delivery, and persistence failure. Assert intended completion/abandon/dead-letter
calls, rejection audit, measured intake boundary, and eventual one-plan outcome. Future V-BROKER; actual service
integration needs separately approved isolated infrastructure and results artifacts.
**Dependencies / completion**: AUD-009-006, AUD-009-008, AUD-009-012; complete when transient failure never permanently
discards valid work and acknowledgement timing is measured separately from generation.

### AUD-009-008

- [x] **AUD-009-008 (P1): Make idempotency tenant-aware and safe across failure, concurrency, and replicas.**

**Affected**: FR-003, FR-025, FR-035; NFR-001; T009, T016, T024, T044, T046, T055; EC-05, EC-06.
**Expected / actual / impact**: Duplicate delivery must not create duplicate plans or suppress unrelated tenant work.
[Deduplicator](../../apps/agents/evacuation/dedup.py#L35) is unsynchronized, process-local, keyed only by handoff ID, and
marks work seen before validation/persistence finishes. Another replica can process the same handoff; failed work
can be discarded on retry; identical IDs across tenants interfere. The
[concurrency test](../../tests/unit/test_evacuation_dedup.py#L126) explicitly uses sequential calls.
**Developer instructions**: Preserve the useful TTL helper where appropriate, but add an atomic scoped processing
claim/completion contract for the supported multi-instance path. Key by trusted tenant and handoff identity, recover
abandoned claims, and distinguish completed duplicate work from retryable failed processing. Bound eviction safely.
**Tester instructions**: Extend dedup, pipeline, broker, and reproducibility tests with two independent workers,
same ID in two tenants, simultaneous claims, TTL boundary, failed-store retry, crash/restart, and cache saturation.
Assert one committed plan for duplicates, independent tenant outcomes, a duplicate-discard audit, and retryability
until durable success. Future V-INTAKE and V-BROKER; no sleeping is needed in unit tests when time is injected.
**Dependencies / completion**: AUD-009-003, AUD-009-007, AUD-009-012; complete when delivery guarantees hold across
the actual horizontal-scaling topology, not merely one in-memory object.

### AUD-009-009

- [x] **AUD-009-009 (P1): Replace replan success placeholders with actual recomputation and persisted versions.**

**Affected**: FR-014, FR-016, FR-017, FR-018, FR-028, SC-001, SC-010; T032, T035, T037, T038, T042, T047;
US2-AS3, US5-AS1/AS2.
**Expected / actual / impact**: Changed conditions must produce a revised, reviewable plan.
[process_replan](../../apps/agents/evacuation/agent.py#L191) has `pass` blocks for road changes, routes, transport,
timeline, version, persistence, and audit, yet reports material change and emits PlanUpdated with the old version.
Its change summary compares the same plan to itself. Recovery events contain an empty new route ID.
**Developer instructions**: Load the scoped active plan and current source snapshots, apply changes, recompute
affected stages, preserve unaffected routes when valid, generate a real diff, assign/persist a new proposed version,
and write `plan_updated` with canonical trigger IDs. Only mark the replan successful after durable completion.
**Tester instructions**: Extend replanner, pipeline, endpoint, and flood scenario tests using a persisted v1 and
strict stores. Close one used road, expand geography, worsen severity, delay progress, and reopen a sheltered route.
Assert changed safe paths, preserved unaffected paths, new ID/version, full change summary, canonical
`shelter_to_evacuation_recovery`, no empty route IDs, and real audit. Future V-REPLAN and V-PIPE.
**Dependencies / completion**: AUD-009-001, AUD-009-005, AUD-009-010, AUD-009-011, AUD-009-013; complete when events and
responses describe an actually stored new plan rather than placeholder span execution.

### AUD-009-010

- [x] **AUD-009-010 (P1): Enforce material-change trigger semantics and the manual replan HTTP contract.**

**Affected**: FR-014, FR-016, FR-018, FR-022; T035, T036, T038, T042, T043; US5-AS3; CHK031-037, CHK079.
**Expected / actual / impact**: Replan only for relevant changes, merge concurrent triggers, and return 202/404/429
with actor justification and previous-plan/audit IDs. [Trigger evaluation](../../apps/agents/evacuation/replanner.py#L66)
ignores current-plan routes; any supplied closure triggers. Percentages and recovery are trusted caller assertions.
[Endpoint](../../apps/agents/evacuation/agent.py#L619) passes no current plan, defaults manual=false, returns 200 even
when rate-limited, and has no actor/justification/contract `road_closures`. Material comparison and trigger merging
exist as helpers but are not used by the execution path; same-count route/transport changes are poorly compared.
**Developer instructions**: Derive area/progress/severity deltas from versioned data; intersect closures with active
routes, handle stale/out-of-order events, and atomically coalesce triggers per tenant/incident. Compare actual route
paths, assembly areas, transport, zones, and timeline. Implement contract request/response/status semantics and an
audited no-change decision without consuming a plan version. Resolve rate-limit/SLA policy via AUD-009-036.
**Tester instructions**: Extend [replanner tests](../../tests/unit/test_evacuation_replanner.py#L11) and
[endpoint tests](../../tests/unit/test_evacuation_endpoints.py#L142): unrelated closure, exactly/just above 10% and 30%,
lower/equal severity, missing/terminal active plan, simultaneous changes, same-count route replacement, stale update,
and manual request with actor. Assert no version for no-change, one version for merged changes, 202/404/429, and IDs.
Future V-REPLAN and V-CONTROL.
**Dependencies / completion**: AUD-009-003, AUD-009-009, AUD-009-013, AUD-009-036; complete when trigger decisions are
derived from trusted current state and HTTP clients can reliably distinguish accepted, unchanged, and throttled work.

### AUD-009-011

- [x] **AUD-009-011 (P1): Remove unreserved version fallback and prove optimistic concurrency with the real SDK.**

**Affected**: FR-017, FR-023, FR-025; T010, T017, T037, T041, T054; US1-AS3.
**Expected / actual / impact**: Every persisted version must be uniquely reserved and monotonically increasing per
tenant/incident. [Counter](../../apps/agents/evacuation/versioning.py#L39) returns 1 repeatedly without a store; after
retry exhaustion [fallback](../../apps/agents/evacuation/versioning.py#L130) returns an unreserved current+1 or 1.
Two callers can therefore obtain the same version. Tests explicitly accept this fallback and use a custom
`replace_item(..., if_match=...)` fake; actual SDK conditional-write behavior was not executed or established here.
**Developer instructions**: Use the installed Cosmos SDK's documented ETag/match-condition mechanism and typed
status handling. Reserve versions atomically, distinguish first-create races, and fail/retry recoverably when
reservation cannot be obtained. Remove the misleading UUID-fallback claim; never fabricate a collision-free number.
**Tester instructions**: Extend [versioning tests](../../tests/unit/test_evacuation_versioning.py#L67) and Cosmos
integration tests with two writers, initial 404/409 race, stale ETag, all retries exhausted, timeout, existing high
counter, and identical incidents across tenants. Assert unique reservations, no persisted fallback collision, and
correct conditional headers against a separately approved emulator/service. Future V-STORE.
**Dependencies / completion**: AUD-009-008, AUD-009-012; complete when every committed plan's version corresponds to
a successful scoped reservation and concurrency behavior is backed by nonpermissive tests and later SDK evidence.

### AUD-009-012

- [x] **AUD-009-012 (P1): Do not report or acknowledge plan persistence failures as completed plans.**

**Affected**: FR-017, FR-019, FR-028, FR-035, SC-001, SC-008; T020, T024, T054, T055; EC-08.
**Expected / actual / impact**: A completed plan remains retrievable even across transient storage failure.
[Persistence](../../apps/agents/evacuation/pipeline.py#L1079) logs exceptions, appends an assumption after the plan
summary was already built, increments active count, and returns success. There is no plan buffer/recovery mechanism
analogous to audit buffering. The broker then completes the message.
**Developer instructions**: Make persistence outcome explicit. Preserve a validated plan/work item durably for retry,
or surface a retryable failure before acknowledgement; do not count, audit as persisted, or return success for an
uncommitted plan. Handle reserved-version gaps explicitly and recover idempotently after uncertain writes.
**Tester instructions**: In pipeline and Cosmos/Broker tests, inject 429/503/timeout, accepted-write/lost-response,
restart before completion, and absent store. Assert no false persisted event/count, no lost message, readable plan
after recovery, and no duplicate content/version. Future V-STORE, V-BROKER, and V-PIPE with strict write receipts.
**Dependencies / completion**: AUD-009-007, AUD-009-008, AUD-009-011; complete when a successful outcome always has
a durable retrievable plan and transient failures retain work without falsely claiming completion.

### AUD-009-013

- [x] **AUD-009-013 (P1): Implement approved-plan-safe supersession, history, and expiry.**

**Affected**: FR-017, FR-022, FR-023, FR-024; T006, T012, T020, T024, T037, T041; US1-AS3, US5-AS1.
**Expected / actual / impact**: Plan lifecycle must preserve approved authority and immutable history.
[Stage 9](../../apps/agents/evacuation/pipeline.py#L948) creates proposed records but never selects/supersedes previous
versions; [model](../../apps/agents/evacuation/models.py#L231) omits valid_until; active counters never decrement.
The main spec's immediate supersession wording conflicts with research's approved-until-new-approval rule.
**Developer instructions**: Obtain the AUD-009-036 lifecycle decision, then implement scoped latest/active/history
selection, guarded status transitions, approval-driven supersession, and time-horizon expiry. Keep proposed updates
from revoking an approved plan, preserve original content, and derive active counts from lifecycle state.
**Tester instructions**: Extend models, pipeline, endpoint, and Cosmos tests for proposed v1 to proposed v2,
approved v1 plus proposed v2, approval/rejection of v2, pause/resume/cancel, expiry boundary, and concurrent approvals.
Assert one authoritative approved plan, queryable immutable history, permitted transitions only, and correct counts.
Future V-CONTROL and V-STORE.
**Dependencies / completion**: AUD-009-004, AUD-009-011, AUD-009-023, AUD-009-036; complete when lifecycle rules are
consistent across stored records, API responses, active queries, and audits.

### AUD-009-014

- [x] **AUD-009-014 (P1): Assign each population and physical origin to the correct evacuation zone once.**

**Affected**: FR-009a, FR-009b, FR-010, FR-013, FR-015; T008, T015, T020, T032, T034; US4-AS1.
**Expected / actual / impact**: Zone cohorts/phases must not double-count residents or route from unrelated locations.
[Zone computation](../../apps/agents/evacuation/zones.py#L47) estimates population separately in three nested polygons,
so Zone 1 residents also count in Zones 2 and 3. [Origin search](../../apps/agents/evacuation/pipeline.py#L1242) similarly
reuses inner nodes; [Stage 5](../../apps/agents/evacuation/pipeline.py#L671) falls back to the first network node when
none match. Vulnerable counts are always 15%, ignoring available vulnerable estimates.
**Developer instructions**: Distinguish nested hazard envelopes from exclusive population/phase membership, using
highest-priority assignment and authoritative population/facility estimates. Do not fabricate a physically unrelated
origin; explicitly report uncovered geography or a verified staging connector. Preserve total population accounting.
**Tester instructions**: Add pipeline/zone tests with a known inner population, outer-only populations, holes,
boundary points, a zone outside the network, and non-15% vulnerable data. Assert no duplicate people/origins, exact
aggregate totals, Zone 1 priority, and an explicit no-coverage disposition rather than a route from the first node.
Future V-ROUTE and V-TIME.
**Dependencies / completion**: AUD-009-002, AUD-009-036; complete when per-zone and phase totals reconcile to the
unique affected population and every route origin is geographically justified.

### AUD-009-015

- [x] **AUD-009-015 (P1): Connect multi-hazard geometry and hazard-specific zone derivation to planning.**

**Affected**: FR-009a, FR-009c, FR-009d, FR-016; T008, T015, T020, T035; CHK011-015.
**Expected / actual / impact**: All active hazards must shape zones/routing, with highest severity in overlaps.
[Multi-hazard helper](../../apps/agents/evacuation/zones.py#L96) exists but has no application caller; Stage 3 consumes
one polygon. [Buffers](../../apps/agents/evacuation/zones.py#L25) are fixed degrees for all hazards, without passing
hazard characteristics. A second active hazard can be omitted entirely.
**Developer instructions**: Supply all active incident-scoped hazard geometries and documented type/severity
parameters to zone derivation; handle union/MultiPolygon and metric-distance projection deliberately. Apply the
agreed overlap policy to the merged output and persist the actual merged affected area/snapshots.
**Tester instructions**: Extend zone and pipeline tests beyond `len(zones)==3`: overlapping and disjoint hazards,
mixed severity/type, newly added hazard, invalid/empty polygon, and equivalent geometries at different latitudes.
Assert actual union coverage, highest-severity classification, excluded dangerous paths, and persisted merged area.
Future V-ROUTE and V-REPLAN.
**Dependencies / completion**: AUD-009-002, AUD-009-001, AUD-009-036; complete when an additional active hazard changes
the real plan and geospatial assumptions are measured and documented rather than only described in helper comments.

### AUD-009-016

- [x] **AUD-009-016 (P1): Implement hazard-specific routing preferences rather than only closure-reason filters.**

**Affected**: FR-005, FR-008, FR-009; T026, T028, T056, T058, T059; US2-AS1.
**Expected / actual / impact**: Routes must account for fire/wind, inland shelter, elevation/flood exposure, damaged
infrastructure, and tsunami exposure. [Hazard strategies](../../apps/agents/evacuation/router.py#L371) only filter
preassigned reason strings; route weights use distance/capacity with no direction/elevation/coast/perimeter inputs.
No two-kilometre fire exclusion is computed and destinations are not screened for hazard suitability.
**Developer instructions**: Add validated hazard attributes/reference data and explicit deterministic exclusion and
preference rules for all five types. Carry reasons into the plan. When necessary data is missing, disclose the gap
and degrade rather than label ordinary shortest paths hazard-aware. Do not delegate safety path selection to an LLM.
**Tester instructions**: In router tests and three existing simulation homes, build graphs with a shorter dangerous
path and longer safe path. Cover fire perimeter and wind reversal, coastal/inland cyclone shelters, higher/lower
flood destinations, damaged earthquake links, and tsunami elevation. Assert actual waypoint/destination choices,
correct closure reasons, and safe missing-data behavior. Future V-ROUTE and V-SCENARIO.
**Dependencies / completion**: AUD-009-001, AUD-009-015, AUD-009-020, AUD-009-036; complete when hazard inputs change
computed choices according to documented rules, not just explanatory labels.

### AUD-009-017

- [x] **AUD-009-017 (P1): Conserve population and shared capacity across evacuation corridors.**

**Affected**: FR-005, FR-007, FR-009, FR-013; T018, T025, T027, T028, T032; US2-AS2.
**Expected / actual / impact**: Population is distributed across feasible corridors without double-counting capacity.
[Router](../../apps/agents/evacuation/router.py#L100) assigns the entire zone population to every origin/destination
pair; [distribution](../../apps/agents/evacuation/router.py#L402) only adjusts alternatives for one pair. Shared edges
are counted repeatedly by [timeline aggregation](../../apps/agents/evacuation/timeline.py#L231). Utilisation is capped
at 100, has no assigned-person count, and the configured congestion threshold is not applied to a flag.
**Developer instructions**: Allocate unique people across routes/destinations, account for shared bottlenecks and
existing traffic load, expose allocation and uncapped utilisation, and apply the configured strict greater-than
threshold. Use consistent persons/vehicle/time-window units; preserve deterministic capacity-safe tie-breaking.
**Tester instructions**: Replace the permissive [multipath assertion](../../tests/unit/test_evacuation_router.py#L154)
with exact allocation invariants on two disjoint corridors, a shared choke point, multiple origins/destinations,
excess demand, odd population rounding, and exactly 80%/just above/custom threshold. Assert population conservation,
no invented aggregate capacity, explicit overload, and appropriate phased delays. Future V-ROUTE and V-TIME.
**Dependencies / completion**: AUD-009-014, AUD-009-018, AUD-009-021, AUD-009-036; complete when route allocations and
timeline capacities reconcile across the entire plan, not independently optimistic origin/destination pairs.

### AUD-009-018

- [x] **AUD-009-018 (P1): Restore structured route fields, exclusion explanations, and per-route rationale.**

**Affected**: FR-006, FR-009, FR-018, FR-019, FR-020; T006, T012, T018, T019, T023, T027, T028, T039.
**Expected / actual / impact**: Each route exposes normal/loaded travel, utilisation/risk, vehicle suitability, path,
destination, and explanation. [Route model](../../apps/agents/evacuation/models.py#L136) has waypoints and one integer
travel time but omits several required fields. Suitability is embedded in a name, exclusions are limited to ten,
and [rationale template](../../apps/agents/evacuation/templates.py#L80) has no application caller. Summary counts do
not list unavailable roads/reasons, so commanders cannot inspect the required rationale.
**Developer instructions**: Publish a complete typed route contract or explicit compatible alias layer; keep machine
fields separate from display text. Include all excluded roads with actual causes, both travel estimates, a true
congestion flag, and grounded selection rationale. Preserve current client fields during a documented migration.
**Tester instructions**: Extend model/schema/router/pipeline tests to assert the required serialized fields, units,
vehicle booleans, ordered connected path, and actual closure reasons. Include more than ten closures, missing reason,
unsealed/accessible edges, zero routes, and same-count changed routes. Assert no truncated safety inventory and
per-route explanations linked to actual computations. Future V-MODEL and V-ROUTE.
**Dependencies / completion**: AUD-009-016, AUD-009-017, AUD-009-025; complete when contract assertions cover full routes,
not just list initialization or nonempty names.

### AUD-009-019

- [x] **AUD-009-019 (P1): Preserve actionable transport requests and correctly scope vulnerable groups.**

**Affected**: FR-010, FR-011, FR-012, FR-015, FR-032, SC-004; T029, T030, T031; US3-AS1/AS2/AS3, US6-AS2; EC-03.
**Expected / actual / impact**: Requests carry individual counts, pickup/destination, priority, vehicle quantity,
zone, and considerations. [Transport model](../../apps/agents/evacuation/models.py#L163) retains only category,
vehicle, quantity/trips, and notes. [Coordinator](../../apps/agents/evacuation/transport.py#L131) serializes the missing
fields into text. [Facility assignment](../../apps/agents/evacuation/transport.py#L168) assigns even a valid
out-of-area facility to the outermost zone after no containment match; Zone 3 still gets mandatory requests.
The timeline ignores transport requirements, and missing facilities produce no required data-gap assumption.
**Developer instructions**: Use typed per-facility requests with stable IDs and correct vehicle counts/trips,
preserve critical/immediate/high priority and supervision/medical requirements, exclude genuinely out-of-area
facilities, distinguish invalid geometry from no match, and honor Zone 3 advisory policy. Connect actual vulnerable
counts to phases and the Resource Allocation request boundary without directly dispatching vehicles.
**Tester instructions**: Extend [transport tests](../../tests/unit/test_evacuation_transport.py#L117), pipeline and
scenario tests with 40 wheelchair users, 200 students, medical/aged-care cohorts, multiple zones, an outside facility,
missing data, and advisory-only Zone 3. Assert 10 accessible vehicles/four buses, structured locations/priorities,
supervision notes, no silently dropped group, and no dispatcher call. Future V-TRANSPORT and V-SCENARIO.
**Dependencies / completion**: AUD-009-014, AUD-009-020, AUD-009-021, AUD-009-023; complete when a downstream planner
can consume requests without parsing prose and the affected-group inventory reconciles to transport coverage.

### AUD-009-020

- [x] **AUD-009-020 (P1): Select reachable, accessible, hazard-safe assembly areas within capacity.**

**Affected**: FR-005, FR-008, FR-010, FR-011, FR-019; T018, T026, T029, T030; US1-AS1, US3-AS1; CHK081, CHK097.
**Expected / actual / impact**: Destination selection must support the assigned population and vehicle needs.
[Router](../../apps/agents/evacuation/router.py#L100) tries every assembly area without occupancy or hazard screening;
[transport](../../apps/agents/evacuation/transport.py#L200) chooses Euclidean nearest, not a reachable suitable route.
[Stage 9](../../apps/agents/evacuation/pipeline.py#L978) marks every area as having shelter and considers any
accessibility feature sufficient for accessibility. No assembly-capacity exhaustion warning is produced.
**Developer instructions**: Share a validated destination allocator across route and transport planning, considering
capacity, occupancy, route reachability, hazard safety, vehicle accessibility, and known shelter facilities. Persist
assigned zones/population and unresolved demand. Never fabricate shelter availability from an absent field.
**Tester instructions**: Add router/transport/pipeline cases for a nearer inaccessible/unreachable/full destination,
a farther suitable one, all areas full, absent assembly data, and cross-zone shared capacity. Assert the safe feasible
destination or explicit unmet need/commander warning, without losing vulnerable requests. Future V-ROUTE/V-TRANSPORT.
**Dependencies / completion**: AUD-009-016, AUD-009-017, AUD-009-019; complete when route and transport destinations
agree and capacity/accessibility claims are supported by reference data and allocation assertions.

### AUD-009-021

- [x] **AUD-009-021 (P1): Implement modeled phase transitions and complete timeline components.**

**Affected**: FR-009b, FR-013, FR-015, FR-019; T032, T033, T034; US4-AS1/AS3; CHK025-030, CHK067-068.
**Expected / actual / impact**: The next phase starts at the earlier configured time or 50% modeled departure
threshold; times include explicit mobilisation/travel/clearance. [Estimator](../../apps/agents/evacuation/timeline.py#L202)
always waits the full previous duration. Thresholds are prose only, travel/mobilisation are not typed phase fields,
distance is an arithmetic rather than capacity-weighted mean, and transport input is unused.
**Developer instructions**: After resolving units/order policy, compute departure-rate-based transition times,
overlapping capacity-aware phases, explicit start/completion/mobilisation/travel values, and vulnerable-only transport
buffer. Retain the documented no-GPS model; do not introduce real-time tracking. Handle zero-population phases cleanly.
**Tester instructions**: Extend [timeline tests](../../tests/unit/test_evacuation_timeline.py#L84) with cases where
each trigger wins, changed factors, zero-population phases, unequal route capacities/distances, shared corridors,
and actual vulnerable demand. Assert exact phase start/completion times, conservation, 1.5 buffer applied only where
intended, and no unjustified zone-order reversal. Future V-TIME.
**Dependencies / completion**: AUD-009-005, AUD-009-014, AUD-009-017, AUD-009-019, AUD-009-036; complete when changing
transition parameters changes calculated times, not merely descriptions.

### AUD-009-022

- [x] **AUD-009-022 (P1): Make replay outputs deterministic and test actual route selections.**

**Affected**: FR-026, FR-027, SC-006; T027, T045, T046; US7-AS2; CHK007, CHK049.
**Expected / actual / impact**: Equal inputs/configuration must reproduce route selections, timeline, and transport.
[Router](../../apps/agents/evacuation/router.py#L316) assigns random route IDs and sorts equal-travel routes by those
IDs. Edge traversal is stable, but output identity/order is not, and congestion/distance tie criteria are absent.
[Reproducibility test](../../tests/contract/test_evacuation_reproducibility.py#L55) only compares counts and sorted
distances/travel values; different paths of equal length could pass. It does not compare phases or transport.
**Developer instructions**: Define stable route identity and canonical ordering from scoped origin/destination/path;
implement documented tie-break semantics and compare replay outputs excluding only explicitly volatile metadata.
Preserve deterministic algorithmic results independently of narrative-model variation.
**Tester instructions**: Extend reproducibility/router tests with equal-cost/equal-time distinct paths, changed
input ordering, repeated fresh processes, multiple origins and facilities, and one material data/config change.
Assert exact waypoints/destinations/order, full phase timings, and typed transport requests, not sorted scalar
surrogates. Future V-REPLAY; snapshot correspondence is verified under AUD-009-023.
**Dependencies / completion**: AUD-009-017, AUD-009-018, AUD-009-019, AUD-009-021, AUD-009-023; complete when replay
comparisons can detect a wrong equal-length route and stable identities do not generate false change reports.

### AUD-009-023

- [x] **AUD-009-023 (P1): Restore the complete plan envelope and trustworthy provenance/snapshots.**

**Affected**: FR-004, FR-017, FR-019, FR-021, FR-025, FR-027, SC-002; T005, T006, T012, T023, T044, T046;
US1-AS1, US6-AS1, US7-AS3.
**Expected / actual / impact**: Plans include full area/hazard/time, assumptions, traceability, generation/configuration
version, snapshot references, and required sections. [Model](../../apps/agents/evacuation/models.py#L231) permits a
two-field empty plan and lacks top-level affected_area, assumptions, change_summary, generation_method,
configuration_version and valid_until. [Traceability](../../apps/agents/evacuation/models.py#L196) omits recommendation
and input signal IDs; [Stage 9](../../apps/agents/evacuation/pipeline.py#L1012) can lose even the handoff assessment ID.
Population snapshot is only a record count; facility/assembly snapshots are absent; mutable closure state does not
change [road hash](../../apps/agents/evacuation/road_network.py#L160). Plan ID validation does not enforce agreement
with incident/version. No owned-plan retrieval endpoint exposes this information for commander review.
**Developer instructions**: Add a complete validated compatible plan envelope and scoped retrieval/history surface.
Preserve all upstream IDs and actual hazard horizon, structured assumptions and simulation label; hash/version the
actual effective road/population/facility/assembly/config inputs. Reject inconsistent identifiers and missing
safety-critical fields rather than accepting an empty plan. Keep secrets out of hashes exposed to users.
**Tester instructions**: Extend [schema tests](../../tests/contract/test_evacuation_plan_schema.py#L40), pipeline,
endpoint, and replay tests with real serialized plans, missing required data, mismatched plan IDs, same-count changed
population/facility records, changed closures, cross-tenant identical incidents, and retrieval of historical versions.
Assert full fields, all source IDs, content-sensitive snapshots, visible simulation label, and no live-query leakage.
Future V-MODEL, V-STORE, V-REPLAY.
**Dependencies / completion**: AUD-009-002, AUD-009-003, AUD-009-013, AUD-009-018, AUD-009-019; complete when retrieved
plans are self-contained and replay inputs can be reconstructed, not merely identified by list lengths.

### AUD-009-024

- [x] **AUD-009-024 (P1): Implement road/population freshness degradation and honest generic guidance.**

**Affected**: FR-021, FR-031, FR-032, FR-035, SC-008; T007, T014, T019, T020, T029, T039, T050;
EC-02, EC-03, EC-09.
**Expected / actual / impact**: Last-known-good roads are usable only within the data freshness window, otherwise
hazard-appropriate generic guidance and immediate-review flags are required. [Staleness](../../apps/agents/evacuation/road_network.py#L164)
measures time since load, not source update; reloading the April fixture makes it appear fresh. Stage 4 does not act
on stale data. Missing roads yield no routes but [template](../../apps/agents/evacuation/templates.py#L44) still claims
safe hazard-avoiding passages; missing facilities/population do not create the required explicit gaps/confidence loss.
**Developer instructions**: Track validated source timestamps and a real last-known-good snapshot; distinguish
unavailable/fresh-cache/stale/no-cache paths. Persist precise data-age/gap assumptions and reduced confidence.
Provide type-specific generic guidance without claiming computed routes or known absence of vulnerable people.
**Tester instructions**: Add road/pipeline/transport/template cases for fresh cache, just-expired cache, stale source
reloaded now, failed refresh, no roads, no facilities, and stale population. Assert no outdated computed guidance,
hazard-specific safe fallback, persistent data-age/review flags, non-dropped handoffs, and complete degradation audit.
Future V-ROUTE, V-PIPE, V-TRANSPORT.
**Dependencies / completion**: AUD-009-005, AUD-009-012, AUD-009-023, AUD-009-025; complete when outage plans explicitly
communicate what is unknown and confidence reflects data quality, not only model availability.

### AUD-009-025

- [x] **AUD-009-025 (P1): Ground summaries in actual plan decisions and preserve content-safety outcomes.**

**Affected**: FR-020, FR-021, FR-033, FR-036; T019, T039, T040; US1-AS2, US6-AS1, US8-AS3.
**Expected / actual / impact**: Narrative must match computed safety decisions and identify generation/fallback.
[Summary stage](../../apps/agents/evacuation/pipeline.py#L837) sends only hazard/population/counts to one reasoning
call, not paths, deadlines, exclusions, transport details, or shelter outcomes. Template confidence is prepared
before the 0.8 reduction; assumptions are appended to an already length-limited summary and may be lost.
The shared [mixin](../../apps/agents/common/llm_mixin.py#L155) does validate normal LLM output and replace failures,
but success is labelled `llm`, not the target contract's `ai_assisted`; keyword fallback review metadata is not
propagated. No evacuation test asserts safety replacement or the final summary's factual consistency.
**Developer instructions**: Build summaries/rationales from validated full plan facts after confidence/disposition
calculation, separate structured assumptions from display limits, and adapt shared generation labels explicitly.
Preserve content-safety fallback/audit and degraded validator review flags. Do not widen model control over routing.
**Tester instructions**: Inject deterministic LLM/validator doubles in pipeline tests for success, exception,
blocked text, empty output, validator outage, lengthy exclusions/assumptions, and low initial confidence. Assert unsafe
text never persists, canonical generation_method, exactly one 0.8 reduction, narrative/score consistency, no omitted
urgent warnings, and a content_safety_failure record. Future V-PIPE and V-MODEL; no live model calls in unit tests.
**Dependencies / completion**: AUD-009-005, AUD-009-018, AUD-009-023, AUD-009-024; shared mixin changes must preserve
other agents' response contracts. Complete when narrative safety matches structured data on success and fallback.

### AUD-009-026

- [x] **AUD-009-026 (P1): Implement canonical audit content, completeness reconciliation, and scoped queries.**

**Affected**: FR-028, FR-029, FR-030, SC-002, SC-007; T006, T012, T024, T047, T048, T049, T054; US8-AS1/AS2/AS3.
**Expected / actual / impact**: Every actual processing decision must be reconstructable and queryable.
[Audit model](../../apps/agents/evacuation/models.py#L292) lacks canonical constraints/replanning triggers/request
counts and upstream recommendation/assessment IDs; many fields default to empty/zero. Summary and persistence both
emit plan_generated, but health changes and real plan updates are not recorded. Override audit has no incident or
scoped partition. [Finalisation](../../apps/agents/evacuation/pipeline.py#L1120) only flushes and checks tier: it never
reconciles expected steps. No audit query implementation was found in inspected evacuation or API paths.
**Developer instructions**: Reconcile the 22-versus-23-field document inconsistency explicitly, then implement the
canonical typed audit envelope with applicable domain details and trusted identity/scope. Track expected/observed
steps per handoff, emit precise stage durations and completeness warnings, and expose authorized incident/plan/type/
time-range retrieval in chronological order. Preserve append-only primary writes and immutable historical records.
**Tester instructions**: Extend audit/pipeline/Cosmos tests with success, rejection, duplicate, degradation, override,
replan, health transition, and intentionally suppressed audit write. Assert exact expected decisions, meaningful
fields, canonical trigger names, correct scope, reconciliation failure on omission, and combined query filters with
time boundaries/pagination and cross-tenant negatives. Future V-AUDIT and V-STORE.
**Dependencies / completion**: AUD-009-004, AUD-009-009, AUD-009-023, AUD-009-036; complete when a reviewer can reconstruct
every decision and omitted processing records are detected rather than masked by a healthy writer.

### AUD-009-027

- [x] **AUD-009-027 (P1): Prevent silent audit loss and make recovery ordering/status trustworthy.**

**Affected**: FR-028, FR-029, FR-034, FR-035; T011, T049; US8-AS3.
**Expected / actual / impact**: Buffered/file audit records survive failures and flush without loss or false health.
[File spill](../../apps/agents/evacuation/audit.py#L89) catches disk failure and loses the unbuffered record while
returning normally. [Flush](../../apps/agents/evacuation/audit.py#L113) can flush later file entries after memory failure,
rewrites/unlinks the spill without writer synchronization, and does not handle accepted-write/retry conflicts.
Direct flush_source is set after serialization; cumulative file-spill count never resets, so status can stay degraded
after successful recovery. Existing [recovery tests](../../tests/unit/test_evacuation_audit.py#L131) do not assert these.
**Developer instructions**: Design a bounded loss-aware durable spill protocol, serialize metadata before writes,
coordinate append/drain, preserve chronological order and retry identity, and handle idempotent 409 after uncertain
success. Surface exhausted storage as an explicit operational failure, not successful audit completion; derive tier
status from pending work. Ensure the nonroot container has a writable durable spill location.
**Tester instructions**: Use temporary directories and a capacity-one buffer in audit tests. Inject disk full/permission
errors, intermittent Cosmos failure, partial flush, accepted-write/lost-response, concurrent append/flush, and restart
with existing spill. Assert exact record IDs/count/order, retained unflushed records, annotations, and healthy recovery
only after all pending work drains. Future V-AUDIT; durability on restart requires later isolated storage validation.
**Dependencies / completion**: AUD-009-012, AUD-009-026, AUD-009-030; complete when each write is durably accepted or
explicitly failed and recovery cannot silently drop or misreport audit records.

### AUD-009-028

- [x] **AUD-009-028 (P1): Make health bounded, state-based, and connected to actual intake/storage readiness.**

**Affected**: FR-028, FR-034, FR-035; T021, T050, T057; EC-08.
**Expected / actual / impact**: Six truthful checks must return within one second.
[Health](../../apps/agents/evacuation/agent.py#L380) performs a synchronous live LLM generation per request without a
one-second bound. Cosmos is considered healthy merely when an injected object exists; last-write state is never
updated. Queue depth stays zero and cannot become offline; active count only increases; source load time is omitted.
An HTTP 200 unhealthy body also cannot by itself make the Docker curl probe fail.
**Developer instructions**: Cache asynchronously maintained dependency outcomes/timestamps, distinguish process
liveness from readiness, connect queue connectivity/depth and committed active-plan state, and expose all contracted
check metadata. Align platform probes with the contract's 200/body semantics or obtain an explicit contract change.
**Tester instructions**: Extend [health tests](../../tests/unit/test_evacuation_endpoints.py#L39) with slow/offline LLM,
queue disconnect, 19/20 depth, 39/40 active count, Cosmos write failure/recovery, stale/unloaded roads, and audit tiers.
Assert no dependency call blocks the request, correct overall state/metadata, and a measured sub-second response in
later isolated runtime checks. Future V-CONTROL and V-RUNTIME.
**Dependencies / completion**: AUD-009-006, AUD-009-013, AUD-009-024, AUD-009-027; complete when health reflects actual
capability, not object existence or initialized counters, and probes drive the intended recovery behavior.

### AUD-009-029

- [x] **AUD-009-029 (P1): Correct telemetry semantics and connect spans, export, and alerts.**

**Affected**: NFR-002, FR-034, SC-001, SC-010; T051, T052, T053; CHK088-090.
**Expected / actual / impact**: All metrics/events/spans must describe real work and support alerts.
[Pipeline](../../apps/agents/evacuation/pipeline.py#L197) reads nonexistent `capacity_utilisation_pct`,
`vulnerability_category`, and `estimated_vehicles`; actual fields are congestion_risk_pct, category, and
quantity_required. [Audit tier](../../apps/agents/evacuation/pipeline.py#L342) reverses memory/file mappings;
[success rate](../../apps/agents/evacuation/pipeline.py#L356) is always 1 after success and override_rate is not updated.
Nested graph/LLM spans are absent, replan spans wrap no work, and events often have blank IDs or require an active
span not provided by the endpoint. [Telemetry](../../apps/agents/evacuation/telemetry.py#L319) otherwise drops events.
No exporter initialization was found in the evacuation/dispatcher entrypoints or evacuation-specific alert rules
in searched local infrastructure. Broader platform telemetry is not proof of these signals.
**Developer instructions**: Map instruments to typed domain fields and lifecycle outcomes, implement actual
aggregation/denominators, populate tenant/incident correlation, instrument real nested stages, and emit the 12 events
with real identifiers. Bind the exporter via supported bootstrap and instantiate the 12 documented alert rules or
explicitly document an equivalent shared rule mapping; preserve AU data-residency controls.
**Tester instructions**: Add recording-meter/tracer/exporter doubles to existing pipeline/endpoint tests. Assert
correct values for mixed success/rejection, medical requests, >80% congestion, all audit tiers, supersession,
overrides, and failed replan/persistence. Verify required parent-child spans and event properties, and text-validate
alert rule expressions against real instrument names. Future V-TELEMETRY; alert firing evidence needs later approval.
**Dependencies / completion**: AUD-009-005, AUD-009-009, AUD-009-013, AUD-009-018, AUD-009-019, AUD-009-028;
complete when counters and alerts measure real completed domain work, not placeholder calls.

### AUD-009-030

- [ ] **AUD-009-030 (P1): Provision and package the supported evacuation runtime and scaling dependencies.**

**Affected**: FR-001, FR-025, FR-028, FR-034; NFR-001; T021, T044, T050, T054, T055, T057; plan infrastructure phase.
**Expected / actual / impact**: Local deployment definitions must connect stores, intake, reference assets, writable
audit spill, and queue-depth scaling. [Agents resource](../../infra/main.bicep#L1109) points to the generic 8080 image
with only min/max replicas and no evacuation queue rule. [Storage](../../infra/main.bicep#L603) and related modules
do not declare the named evacuation plan/audit containers; the simulation Event Hub
[scaling module](../../infra/bicep/modules/container-apps-scaling.bicep#L30) is not the required handoff-queue policy.
[Dockerfile](../../apps/agents/Dockerfile#L28) does not copy the road/population data or provision the configured
`/var/log/evacuation-agent` path for appuser. Local source cannot establish live infrastructure or AU residency.
**Developer instructions**: After AUD-009-006 chooses the supported runtime, connect the correct scoped storage
containers, intake channel, managed identities, reference assets, probes, writable durable spill, and queue-based
scaling. Follow AVM-first and existing policy/region constraints; do not weaken policy or assume the generic dispatcher
provides these resources. Explicitly document any shared-resource equivalence.
**Tester instructions**: Later platform reviewers should inspect rendered configuration, package contents, identity
scope, partitions/retention, probes, and scaling policy with approved tools; then test isolated boot, 50-plan load,
scale-out/restart, and recovery. No build/what-if/deployment command was executed here. Use future V-RUNTIME and
V-CAPACITY only after infrastructure readiness approval; collect attributable deployment evidence separately.
**Dependencies / completion**: AUD-009-006, AUD-009-008, AUD-009-011, AUD-009-027, AUD-009-028; complete when source
configuration and independently verified environment both support the declared runtime, not a comment-only scale table.

### AUD-009-031

- [ ] **AUD-009-031 (P1): Validate safety configuration and commit road loads atomically.**

**Affected**: FR-003, FR-005, FR-013, FR-015, FR-016, FR-031; T005, T007, T013, T014; CHK002, CHK050, CHK060.
**Expected / actual / impact**: Invalid domain settings/network data must be rejected without corrupting last-good
state. [Config validation](../../apps/agents/evacuation/config.py#L105) only validates LLM fields; negative buffers,
TTL, population percentages, and timing factors remain valid constructor inputs. Config environment names differ
from quickstart names. [Loader](../../apps/agents/evacuation/road_network.py#L97) assigns `_data` before size/geometry
validation, so failed loads can leave `is_loaded=True` with empty/old indices. IDs, topology, coordinates, and
nonnegative capacity/distance are not comprehensively validated.
**Developer instructions**: Add bounded domain validation and a documented environment alias/migration policy,
including all output-affecting version inputs. Validate a complete candidate graph before atomically replacing
current indices/hash/timestamp. Reject duplicate IDs, dangling references, bad geometry/coordinates, negative
weights/capacities, invalid assembly references, and oversize graphs; retain the last-good graph on refresh failure.
**Tester instructions**: Extend [config tests](../../tests/unit/test_evacuation_config.py#L148) and
[loader tests](../../tests/unit/test_evacuation_road_network.py#L106): invalid bounds/types, env precedence, direct
constructor validation, 1,000/1,001 nodes, 5,000/5,001 edges, invalid refresh after valid load, duplicate IDs/dangling
edges, and degenerate geometry. Assert explicit errors, no false loaded state, and stable previous snapshot. V-MODEL/V-ROUTE.
**Dependencies / completion**: AUD-009-023, AUD-009-024, AUD-009-036; complete when invalid settings/data cannot silently
change safety decisions or leave readiness claiming a usable graph after failed validation.

### AUD-009-032

- [ ] **AUD-009-032 (P1): Replace self-confirming mocks and weak scenario assertions with contract-level tests.**

**Affected**: T012-T017, T022-T024, T028, T031, T034, T038, T043, T046, T049, T054-T056, T058, T059;
FR-001-FR-036, NFR-001-NFR-002, SC-002-SC-008 (test coverage, not a claim of execution).
**Expected / actual / impact**: Tests should falsify missing required behavior. The
[Cosmos mock](../../tests/integration/test_evacuation_cosmos.py#L20) ignores partition keys/query filters and overwrites
duplicate IDs; [broker tests](../../tests/integration/test_evacuation_service_bus.py#L179) implement a different loop.
Schema tests construct incomplete plans; scenario fixtures use live scope with no facilities or persisted assessment.
[Bushfire route assertion](../../tests/simulation/test_bushfire_evacuation_scenario.py#L68) accepts every possible count.
Replanner tests prove trigger strings, not stored changes; audit tests do not reconcile stages or query filters.
**Developer instructions**: Supply injectable boundaries, strict storage/broker doubles, typed producer fixtures,
deterministic clocks/IDs, and clear unit-versus-service integration separation. Do not weaken contracts to retain
passing tests and do not delete legitimate shared test coverage while adapting schemas.
**Tester instructions**: Implement the cases specified in AUD-009-001 through AUD-009-031 in the existing named test
homes. Add true simulation tenant fixtures, 40-person disability/200-student cohorts, wind/elevation/closure data,
persisted assessments, active v1 plans, and fault injection. Assert paths, allocations, dispositions, immutable
versions, scoped reads, and required audit fields rather than only counts/text presence. Run the future validation
matrix only after repairs; preserve command, revision, environment, output, and fixture identities as new evidence.
**Dependencies / completion**: Relevant behavior fixes first; complete when each repaired invariant has a regression
assertion that fails on the reviewed source. Passing execution remains UNVERIFIED until a later tester records it.

### AUD-009-033

- [ ] **AUD-009-033 (P1): Produce measured initial/replan/health and 50-plan capacity evidence.**

**Affected**: FR-001, FR-034; NFR-001; SC-001, SC-010; T021, T037, T050-T053, T057; CHK036, CHK071, CHK074, CHK082-085.
**Expected / actual / impact**: Five-second acknowledgement, 30-second initial plans, 15-second replans, sub-second
health, and 50 concurrent plans need measured evidence. [SLA counters](../../apps/agents/evacuation/pipeline.py#L346)
exist, but persistence failure can count as success and replan measures placeholders. The inspected
[workflow capacity test](../../tests/load/test_workflow_capacity.py#L47) is a different workflow with batches of five;
its smoke runs are sequential. [Paired lead-time test](../../tests/simulation/test_sc003_evacuation_lead.py#L22) exercises
a separate paired-exercise harness, not evidence of this pipeline's 15-second update or 24-hour decision benefit.
**Developer instructions**: Establish instrumentation boundaries and an isolated representative workload using
real repaired planner/storage adapters, worst-case supported graph, varying facilities, and actual replans.
**Tester instructions**: Extend the existing load-test home with clearly named evacuation-specific cases; preserve
unrelated workflow tests. Exercise 50 simultaneous incidents, burst replans, slow dependencies, health under load,
and an intentional SLA breach. Capture p50/p95/p99 and individual breach events with receipt/commit timestamps,
configuration, resources, dataset, and revision. Assert no drops, correct outputs, and completion despite breaches.
Future V-CAPACITY after AUD-009-030 approval; this audit does not certify the thresholds or scaling outcome.
**Dependencies / completion**: AUD-009-006, AUD-009-007, AUD-009-009, AUD-009-012, AUD-009-028, AUD-009-029, AUD-009-032;
complete only with attributable measured results, not fixture-derived or comment-stated timings.

### AUD-009-034

- [ ] **AUD-009-034 (P2): Validate commander usability with the required structured exercise survey.**

**Affected**: FR-019, FR-020; SC-009; T039, T057; US6-AS1/AS2; CHK071, CHK073, PER-019.
**Expected / actual / impact**: At least 90% of incident commanders rate plans clear, actionable, and traceable.
[SC-009](spec.md#L316) defines the target, but no local survey instrument, participant denominator, responses, or
signed result was found in the target evidence/docs search. Template headings and aggregate AMA rubric scores do not
establish commander usability. Status is UNVERIFIED, not failed or MISSING execution.
**Developer instructions**: Deliver a reviewable plan surface with the complete structured information and prepare
a privacy-conscious exercise/survey protocol, without claiming users have approved it.
**Tester instructions**: A later authorized facilitator must define participants/sample size/scoring, run AU-v1
bushfire/cyclone/flood exercises, include degraded/replanned/vulnerable transport cases, and collect clarity,
actionability, and traceability scores plus denominator and dissenting feedback. Retain consent/approver identity
and revision-specific results. V-SURVEY is a human protocol, not an automated test substituting for responses.
**Dependencies / completion**: AUD-009-018 through AUD-009-025, AUD-009-032; complete only when the documented survey
meets the 90% target or an explicit failed result and remediation are recorded honestly.

### AUD-009-035

- [ ] **AUD-009-035 (P2): Repair the quickstart and obtain non-retrospective execution evidence for T057.**

**Affected**: T005, T021, T050, T057; FR-001, FR-034; SC-001; plan/task checkpoint completion claims.
**Expected / actual / impact**: The guide must be runnable and its claimed end-to-end validation attributable.
[Quickstart](quickstart.md#L17) changes into apps/agents but then references root-relative data/tests; it names
`data/road-network.json`, while the supplied fixture has another path. Its Cosmos/Service Bus variables do not match
EvacuationConfig, its expected health is not startup behavior, and its Docker recipe starts the dispatcher on 8080,
not the promised 8082 agent. No T057 run log is present. This report does not uncheck or rewrite the original task.
**Developer instructions**: After runtime/config decisions, update the guide in a later authorized implementation
change with correct working directory, environment, data loading, store prerequisites, and actual startup behavior.
Clearly distinguish local doubles from service-backed operation and current commands from historical instructions.
**Tester instructions**: From a clean approved environment, follow the repaired guide literally; verify all six
health checks, send a producer-shaped handoff, retrieve its persisted proposed plan, check full traceability, and
exercise a duplicate and a degraded dependency. Record commands/outputs/revision/dataset and any setup correction
as new evidence, never backfill the April sample response as a run. Future V-RUNTIME, V-INTAKE, V-STORE.
**Dependencies / completion**: AUD-009-006, AUD-009-023, AUD-009-028, AUD-009-030, AUD-009-031; complete when the guide
works as written and an independent tester records the result. Historical execution remains UNVERIFIED.

### AUD-009-036

- [ ] **AUD-009-036 (P2): Resolve safety contract conflicts and substantiate amendment/review claims.**

**Affected**: FR-009b/FR-009c/FR-009d, FR-013-FR-017, FR-028-FR-029; T005, T006, T008, T010, T032, T037;
ASM-022-025, PER-019-021, HYP-007/HYP-030/HYP-031/HYP-032, SCP-022-024; local checklist/design claims.
**Expected / actual / impact**: Requirements must agree before implementation decisions are treated as approved.
[US4-AS3](spec.md#L92) says outer zones first, while FR-009b/FR-015 say inner first. FR-009d says avoid all hazard
zones, whereas Zones 2/3 remain traversable with reduced capacity. Conservative Zone-1 intersection closure can
remove all exits from Zone 1. Supersession differs between main spec and research task 5. Timeline units mix persons,
vehicles/hour, and distance; the immediate-threat threshold differs for sudden hazards between pipeline contract
and code. Thirty-second throttling can prevent a 15-second urgent update. The named 22-field audit schema lists
23 fields; task/config counts and plan's 14/15 decision-type descriptions disagree. Research's latitude/longitude
GeoJSON example is inconsistent with the working sample. These are CONFLICTs, not permissions to choose silently.
**Developer instructions**: Obtain authorized domain/product decisions on each contradiction and record explicit
precedence, units, thresholds, scoped safety exceptions, and compatible schema migration in later approved changes.
Reconcile stale constitution/actor references without modifying constitutional authority here. Locate or create
the missing HYP-007 evidence artifact only as explicitly proposed future work; preserve existing evidence/states.
Keep PH/JP/BD deferred until D-009, data agreements, and SME approvals actually clear.
**Tester instructions**: Turn each approved decision into boundary cases in the named route/timeline/version/audit
tests. Independently verify actor consultation records, persona validation provenance, and per-spec rubric evidence;
aggregate structural scores do not prove HYP-007. Assess every checklist item below against the approved documents,
retaining honest unchecked/UNVERIFIED states when approval or measurement is absent. No grading, approval, or
country exercise was performed in this audit. Future V-DOC and V-SURVEY only after separate authorization.
**Dependencies / completion**: Domain/incident-command, product, security, and shared-runtime owners as appropriate;
complete when conflicting obligations have documented authorized precedence and amendment claims have traceable
evidence or explicitly remain deferred/unverified. This task does not authorize scope expansion to country variants.

## Original Task Coverage

Original IDs and states are taken verbatim from [tasks.md](tasks.md#L30). Each original ID has exactly one row.
An IMPLEMENTED test row credits authored assertions only. Follow-up IDs identify remaining behavior or evidence work;
they do not imply a historical checkbox was changed. Table order preserves T058/T059 before T057 as in the original.

| Original task | Original state | Status | Concrete source/test evidence and remaining obligation | Follow-up IDs |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | [Package export/version](../../apps/agents/evacuation/__init__.py#L3) includes public agent and 0.1.0. | None |
| T002 | [x] | IMPLEMENTED | [Declared dependency](../../apps/agents/pyproject.toml#L22) is shapely>=2.0.0; installation is not inferred. | None |
| T003 | [x] | IMPLEMENTED | [Network fixture](../../data/road-networks/far-north-qld-sample.json#L1), statically parsed: 50 nodes, 120 edges, five assembly areas; [count assertions](../../tests/unit/test_evacuation_road_network.py#L21). | None |
| T004 | [x] | IMPLEMENTED | [Population fixture](../../data/population/sample-population.json#L7), statically parsed: 15 facilities, 12 population areas, all four categories. | None |
| T005 | [x] | PARTIAL | [Frozen config](../../apps/agents/evacuation/config.py#L15) reads most defaults/hash but lacks domain validation and aligned service variables. | AUD-009-031, AUD-009-035, AUD-009-036 |
| T006 | [x] | PARTIAL | [Models](../../apps/agents/evacuation/models.py#L110) and enums exist; reduced route/transport/phase/plan/audit fields and no enforced lifecycle. | AUD-009-004, AUD-009-013, AUD-009-018, AUD-009-019, AUD-009-021, AUD-009-023, AUD-009-026 |
| T007 | [x] | PARTIAL | [Loader](../../apps/agents/evacuation/road_network.py#L97) parses/graphs/closes roads; freshness is load age, failed validation is non-atomic, hashes omit changes. | AUD-009-023, AUD-009-024, AUD-009-031 |
| T008 | [x] | PARTIAL | [Zones](../../apps/agents/evacuation/zones.py#L47) buffer/classify/union; pipeline ignores adjusted edges, double-counts nested populations, and never calls union. | AUD-009-001, AUD-009-014, AUD-009-015 |
| T009 | [x] | IMPLEMENTED | [TTL cache](../../apps/agents/evacuation/dedup.py#L19) implements the named local in-memory helper; system-wide safety is separate. | AUD-009-008 |
| T010 | [x] | PARTIAL | [Counter](../../apps/agents/evacuation/versioning.py#L39) retries conflicts but returns unreserved fallback versions. | AUD-009-011 |
| T011 | [x] | PARTIAL | [Audit tiers](../../apps/agents/evacuation/audit.py#L42) exist; spill loss, flush ordering/races, and status recovery remain. | AUD-009-027 |
| T012 | [x] | PARTIAL | [Model tests](../../tests/unit/test_evacuation_models.py#L161) cover basic IDs/confidence/enums, not full embedded contracts or lifecycle invariants. | AUD-009-004, AUD-009-013, AUD-009-023, AUD-009-026, AUD-009-032 |
| T013 | [x] | PARTIAL | [Config tests](../../tests/unit/test_evacuation_config.py#L10) cover defaults/selected overrides/hash equality, not invalid domain bounds or full hash sensitivity. | AUD-009-031, AUD-009-032 |
| T014 | [x] | IMPLEMENTED | [Loader tests](../../tests/unit/test_evacuation_road_network.py#L21) author the task's sample parse/graph, >1,000 nodes, geometry, closures, and load-age checks; source-age/recovery extensions still needed. | AUD-009-024, AUD-009-031 |
| T015 | [x] | PARTIAL | [Zone tests](../../tests/unit/test_evacuation_zones.py#L260) assert returned Zone-1 copy, not pipeline graph; multi-hazard tests check count, not union/population correctness. | AUD-009-001, AUD-009-014, AUD-009-015, AUD-009-032 |
| T016 | [x] | PARTIAL | [Dedup tests](../../tests/unit/test_evacuation_dedup.py#L126) explicitly substitute sequential access for concurrency. | AUD-009-008, AUD-009-032 |
| T017 | [x] | PARTIAL | [Counter tests](../../tests/unit/test_evacuation_versioning.py#L67) use permissive SDK fake and accept unsafe exhaustion-to-1 behavior. | AUD-009-011, AUD-009-032 |
| T018 | [x] | PARTIAL | [Dijkstra](../../apps/agents/evacuation/router.py#L188) avoids explicitly closed/nonpositive edges; returned fields, hazard integration, and allocation are incomplete. | AUD-009-001, AUD-009-017, AUD-009-018 |
| T019 | [x] | PARTIAL | [Templates](../../apps/agents/evacuation/templates.py#L13) exist; rationale helper is disconnected and diffs/unsafe fallback wording lack required facts. | AUD-009-018, AUD-009-024, AUD-009-025 |
| T020 | [x] | PARTIAL | [Ten-stage path](../../apps/agents/evacuation/pipeline.py#L111) exists with unsafe retrieval/zone preparation and no durable failure outcome or reconciliation. | AUD-009-001, AUD-009-002, AUD-009-012, AUD-009-026 |
| T021 | [x] | PARTIAL | [Agent](../../apps/agents/evacuation/agent.py#L74) and [consumer](../../apps/agents/evacuation/agent.py#L655) exist; startup never connects them or stores/data. | AUD-009-006, AUD-009-007, AUD-009-030 |
| T022 | [x] | PARTIAL | [Handoff tests](../../tests/contract/test_evacuation_handoff.py#L111) validate envelope fields, not source/payload/record existence or rejection/duplicate audits. | AUD-009-002, AUD-009-007, AUD-009-008, AUD-009-032 |
| T023 | [x] | PARTIAL | [Plan tests](../../tests/contract/test_evacuation_plan_schema.py#L40) accept initialized empty lists and omit several mandatory fields/trace IDs. | AUD-009-018, AUD-009-023, AUD-009-032 |
| T024 | [x] | PARTIAL | [Pipeline tests](../../tests/unit/test_evacuation_pipeline.py#L51) use no stores and enriched payloads; no missing-assessment rejection, stored v2, or step audit assertions. | AUD-009-002, AUD-009-012, AUD-009-013, AUD-009-026, AUD-009-032 |
| T025 | [x] | PARTIAL | [Alternatives](../../apps/agents/evacuation/router.py#L122) exist; distribution is per pair and omits total/shared-capacity accounting. | AUD-009-017 |
| T026 | [x] | PARTIAL | [Hazard filters](../../apps/agents/evacuation/router.py#L371) match reason strings only, without directional/elevation/perimeter strategy. | AUD-009-016, AUD-009-020 |
| T027 | [x] | PARTIAL | [Route construction](../../apps/agents/evacuation/router.py#L282) caps an integer risk estimate and embeds suitability in text; threshold/tie rules incomplete. | AUD-009-017, AUD-009-018, AUD-009-022 |
| T028 | [x] | PARTIAL | [Router assertions](../../tests/unit/test_evacuation_router.py#L154) require >=1 multipath result and 0-100 risk, not all five hazard strategies or exact ties/thresholds. | AUD-009-016, AUD-009-017, AUD-009-018, AUD-009-032 |
| T029 | [x] | PARTIAL | [Coordinator](../../apps/agents/evacuation/transport.py#L74) maps four categories/counts but flattens details, assigns outside facilities, and omits missing-data warning. | AUD-009-019, AUD-009-020, AUD-009-024 |
| T030 | [x] | IMPLEMENTED | [Stage 6](../../apps/agents/evacuation/pipeline.py#L711) invokes coordinator and [plan build](../../apps/agents/evacuation/pipeline.py#L1056) stores a separate transport list. Domain completeness remains separate. | AUD-009-019, AUD-009-020 |
| T031 | [x] | PARTIAL | [Transport tests](../../tests/unit/test_evacuation_transport.py#L117) cover ceiling/type mapping; lack full structured fields, out-of-zone, missing-data assumptions, and multi-zone supervision cases. | AUD-009-019, AUD-009-020, AUD-009-032 |
| T032 | [x] | PARTIAL | [Timeline](../../apps/agents/evacuation/timeline.py#L44) uses formula/buffer/five phases, not modeled earliest transition or full dispositions/recovery execution. | AUD-009-005, AUD-009-009, AUD-009-021 |
| T033 | [x] | PARTIAL | [Stage 7](../../apps/agents/evacuation/pipeline.py#L766) wires estimator but discards emergency results and only embeds warnings in summary text. | AUD-009-005, AUD-009-021, AUD-009-023 |
| T034 | [x] | PARTIAL | [Timeline tests](../../tests/unit/test_evacuation_timeline.py#L196) check a deficit string and helper recovery boolean, not persisted shelter/recovery or transition timing. | AUD-009-005, AUD-009-009, AUD-009-021, AUD-009-032 |
| T035 | [x] | PARTIAL | [Replanner](../../apps/agents/evacuation/replanner.py#L66) detects supplied trigger values; active-route filtering/incremental recompute/full diff are absent. | AUD-009-009, AUD-009-010 |
| T036 | [x] | PARTIAL | [Rate limiter](../../apps/agents/evacuation/replanner.py#L150) is local; material comparator/merge helpers are not used by actual processing. | AUD-009-008, AUD-009-010 |
| T037 | [x] | PARTIAL | [Agent replan](../../apps/agents/evacuation/agent.py#L191) has placeholder recompute/version/persist/audit blocks but emits PlanUpdated. | AUD-009-009, AUD-009-013 |
| T038 | [x] | PARTIAL | [Replan tests](../../tests/unit/test_evacuation_replanner.py#L11) check trigger strings/helpers, not revised stored plans, 429, or canonical recovery audit. | AUD-009-009, AUD-009-010, AUD-009-032 |
| T039 | [x] | PARTIAL | [AIIMS templates](../../apps/agents/evacuation/templates.py#L13) have headings/truncation, but factual route/shelter content and detailed diffs are incomplete. | AUD-009-018, AUD-009-025 |
| T040 | [x] | PARTIAL | [Stage 8](../../apps/agents/evacuation/pipeline.py#L837) invokes safe shared fallback and 0.8 reduction; narrative inputs, label adaptation, and safety tests incomplete. | AUD-009-025 |
| T041 | [x] | PARTIAL | [Override](../../apps/agents/evacuation/agent.py#L500) lacks trusted authority, uses wrong partition, blocks stored modify, and has no clone/conditional update. | AUD-009-003, AUD-009-004, AUD-009-013 |
| T042 | [x] | PARTIAL | [Replan endpoint](../../apps/agents/evacuation/agent.py#L619) returns 200 trigger evaluation, without contracted identity/202/404/429/previous plan/audit IDs. | AUD-009-003, AUD-009-009, AUD-009-010 |
| T043 | [x] | PARTIAL | [Endpoint tests](../../tests/unit/test_evacuation_endpoints.py#L74) accept no-store overrides and boolean rate limiting; no real transition/404/409 matrix. | AUD-009-003, AUD-009-004, AUD-009-010, AUD-009-032 |
| T044 | [x] | PARTIAL | [Pipeline scope](../../apps/agents/evacuation/pipeline.py#L125) formats tenant:incident writes, but input/control scope validation and isolation queries are absent. | AUD-009-003, AUD-009-008, AUD-009-023 |
| T045 | [x] | PARTIAL | [Neighbor sort](../../apps/agents/evacuation/router.py#L223) is stable; random route IDs/order and required congestion/distance ties remain. | AUD-009-022 |
| T046 | [x] | PARTIAL | [Replay tests](../../tests/contract/test_evacuation_reproducibility.py#L55) compare sorted distances/travel, not paths/phases/transport or tenant isolation. | AUD-009-008, AUD-009-022, AUD-009-023, AUD-009-032 |
| T047 | [x] | PARTIAL | [Audit writer calls](../../apps/agents/evacuation/pipeline.py#L1173) lack canonical domain fields; real update/health decisions and complete override scope are absent. | AUD-009-005, AUD-009-009, AUD-009-026 |
| T048 | [x] | MISSING | [Stage 10](../../apps/agents/evacuation/pipeline.py#L1120) flushes/checks health, with no expected-step reconciliation or audit query implementation in searched agent/API paths. | AUD-009-026 |
| T049 | [x] | PARTIAL | [Audit tests](../../tests/unit/test_evacuation_audit.py#L131) cover basic tiers/flush but not required annotations, all-type completeness/querying, or loss/race recovery. | AUD-009-026, AUD-009-027, AUD-009-032 |
| T050 | [x] | PARTIAL | [Health](../../apps/agents/evacuation/agent.py#L380) has six keys but synchronous model ping, unmaintained queue/write state, and wrong active semantics. | AUD-009-028 |
| T051 | [x] | PARTIAL | [Root/stage spans](../../apps/agents/evacuation/pipeline.py#L117) exist; required nested and cross-agent context/instrumented replan work do not. | AUD-009-009, AUD-009-029 |
| T052 | [x] | PARTIAL | [Metric definitions](../../apps/agents/evacuation/telemetry.py#L145) exist; call sites use wrong fields/tiers and false success denominator. | AUD-009-029 |
| T053 | [x] | PARTIAL | [Twelve event helpers](../../apps/agents/evacuation/telemetry.py#L329) exist; absent spans/blank IDs/inverted emergency and stub updates prevent required evidence. | AUD-009-005, AUD-009-009, AUD-009-029 |
| T054 | [x] | PARTIAL | [Cosmos tests](../../tests/integration/test_evacuation_cosmos.py#L20) exercise a dictionary ignoring partition/filter/conflict semantics, not required OCC/time-range integration. | AUD-009-011, AUD-009-012, AUD-009-026, AUD-009-032 |
| T055 | [x] | PARTIAL | [Service Bus tests](../../tests/integration/test_evacuation_service_bus.py#L179) drive a copied loop, not actual consumer acknowledgment/error behavior. | AUD-009-007, AUD-009-008, AUD-009-032 |
| T056 | [x] | PARTIAL | [Cyclone scenario](../../tests/simulation/test_cyclone_evacuation_scenario.py#L54) asserts basic model/mobilisation/phases, not inland paths/transport/isolated tenant. | AUD-009-016, AUD-009-019, AUD-009-032 |
| T058 | [x] | PARTIAL | [Bushfire scenario](../../tests/simulation/test_bushfire_evacuation_scenario.py#L68) allows >=0 routes and does not assert wind/fire closure or aged-care transport. | AUD-009-001, AUD-009-016, AUD-009-019, AUD-009-032 |
| T059 | [x] | PARTIAL | [Flood scenario](../../tests/simulation/test_flood_evacuation_scenario.py#L54) lacks higher-ground, flood-cut, Zone-2 reduction, and persisted deficit/shelter assertions. | AUD-009-001, AUD-009-005, AUD-009-016, AUD-009-032 |
| T057 | [x] | UNVERIFIED | [Quickstart](quickstart.md#L87) supplies commands/example output, not attributable execution; source/path/config issues also exist. | AUD-009-033, AUD-009-035 |

## Requirement Coverage

One row per normative FR/NFR/SC, including all four suffixed FR-009 IDs. Partial source does not establish a runtime
percentage, latency, approval, or deployment. Success-criterion measurements remain unverified unless stated otherwise.

| Requirement | Status | Evidence and gap | Follow-up IDs |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Consumer](../../apps/agents/evacuation/agent.py#L655) exists but is unstarted and completes after processing, not measured five-second intake. | AUD-009-006, AUD-009-007, AUD-009-033 |
| FR-002 | CONFLICT | [Retrieval](../../apps/agents/evacuation/pipeline.py#L448) falls back instead of rejecting missing assessment; no recommendation verification. | AUD-009-002 |
| FR-003 | PARTIAL | [TTL helper](../../apps/agents/evacuation/dedup.py#L35) handles local duplicates, not replicas/retry/tenant collisions. | AUD-009-008 |
| FR-004 | PARTIAL | [Stage 3](../../apps/agents/evacuation/pipeline.py#L504) expects flat geography unlike [upstream HazardMap](../../packages/domain/src/domain/models/hazard_assessment.py#L7). | AUD-009-002, AUD-009-023 |
| FR-005 | PARTIAL | [Dijkstra](../../apps/agents/evacuation/router.py#L188) and static graph exist; actual runtime, load/vehicle/hazard constraints and capacity propagation incomplete. | AUD-009-001, AUD-009-006, AUD-009-016, AUD-009-017 |
| FR-006 | PARTIAL | [Closed-edge skip](../../apps/agents/evacuation/router.py#L231) works for explicit closures; hazard changes and full exclusion narrative do not. | AUD-009-001, AUD-009-018 |
| FR-007 | PARTIAL | [Distribution](../../apps/agents/evacuation/router.py#L402) lacks global allocation/shared-capacity accounting and explicit configured flag. | AUD-009-017 |
| FR-008 | PARTIAL | [Five reason filters](../../apps/agents/evacuation/router.py#L371) do not implement direction/elevation/shelter/perimeter strategies. | AUD-009-016, AUD-009-020 |
| FR-009 | PARTIAL | [Reduced route](../../apps/agents/evacuation/models.py#L136) omits normal/loaded split, structured suitability and rationale fields. | AUD-009-018 |
| FR-009a | PARTIAL | [Buffers](../../apps/agents/evacuation/zones.py#L47) are generic and population/origin memberships overlap. | AUD-009-014, AUD-009-015 |
| FR-009b | CONFLICT | [Five phase order](../../apps/agents/evacuation/timeline.py#L89) is inner-first; [US4-AS3](spec.md#L92) says outer-first; capacity exceptions not specified/implemented. | AUD-009-014, AUD-009-021, AUD-009-036 |
| FR-009c | PARTIAL | [Helper](../../apps/agents/evacuation/zones.py#L154) computes reductions, [caller](../../apps/agents/evacuation/pipeline.py#L597) discards them. | AUD-009-001, AUD-009-036 |
| FR-009d | CONFLICT | [Union helper](../../apps/agents/evacuation/zones.py#L96) disconnected; all-zone avoidance conflicts with reduced-capacity traversal. | AUD-009-015, AUD-009-036 |
| FR-010 | PARTIAL | [Category mapping](../../apps/agents/evacuation/transport.py#L24) exists; outside-facility fallback and invented vulnerable proportion remain. | AUD-009-014, AUD-009-019 |
| FR-011 | PARTIAL | [Vehicle counts](../../apps/agents/evacuation/transport.py#L124) exist; requests lose structured pickup/individual/priority/destination fields. No direct dispatch found. | AUD-009-019, AUD-009-020 |
| FR-012 | IMPLEMENTED | [Plan transport list](../../apps/agents/evacuation/models.py#L249) is distinct from routes; [Stage 6](../../apps/agents/evacuation/pipeline.py#L711) populates it. | AUD-009-019 (request completeness) |
| FR-013 | PARTIAL | [Literal formula](../../apps/agents/evacuation/timeline.py#L206) and multiplier exist; weighted metrics, typed components and phase capacity incomplete. | AUD-009-017, AUD-009-021, AUD-009-036 |
| FR-014 | PARTIAL | [Shelter decision](../../apps/agents/evacuation/timeline.py#L266) exists; emergency discarded, deficit not structured, recovery only helper. | AUD-009-005, AUD-009-009 |
| FR-015 | PARTIAL | [Five phases](../../apps/agents/evacuation/timeline.py#L89) exist; sequential full-duration starts contradict earliest trigger; Zone 3 transport not advisory-only. | AUD-009-019, AUD-009-021 |
| FR-016 | PARTIAL | [Trigger helper](../../apps/agents/evacuation/replanner.py#L66) not tied to current sources/routes; real updates/no-change policy absent. | AUD-009-009, AUD-009-010 |
| FR-017 | CONFLICT | [Counter](../../apps/agents/evacuation/versioning.py#L39) has unreserved fallback; [Stage 9](../../apps/agents/evacuation/pipeline.py#L948) lacks supersession; approval precedence conflicts. | AUD-009-011, AUD-009-012, AUD-009-013, AUD-009-036 |
| FR-018 | PARTIAL | [Diff template](../../apps/agents/evacuation/templates.py#L124) compares counts/confidence, not paths/assembly/timeline details; replan compares old to itself. | AUD-009-009, AUD-009-010, AUD-009-018 |
| FR-019 | PARTIAL | [Plan model](../../apps/agents/evacuation/models.py#L231) is permissive and omits mandatory envelope/trace/snapshot sections. | AUD-009-018, AUD-009-019, AUD-009-021, AUD-009-023 |
| FR-020 | PARTIAL | [AIIMS template](../../apps/agents/evacuation/templates.py#L13) has headings but can contradict no-route/deficit state and lose warnings. | AUD-009-025, AUD-009-034 |
| FR-021 | PARTIAL | [Score categorization](../../apps/agents/evacuation/models.py#L93) exists; [summary confidence](../../apps/agents/evacuation/pipeline.py#L918) only adjusts model fallback, not source data quality. | AUD-009-023, AUD-009-024, AUD-009-025 |
| FR-022 | PARTIAL | [Override endpoint](../../apps/agents/evacuation/agent.py#L500) lacks trusted authority and correct modification/scope/metadata semantics. | AUD-009-003, AUD-009-004 |
| FR-023 | CONFLICT | [Override mutation](../../apps/agents/evacuation/agent.py#L554) has no version clone; modify transition is blocked for stored plans. | AUD-009-004, AUD-009-011, AUD-009-013 |
| FR-024 | PARTIAL | [New plans proposed](../../apps/agents/evacuation/pipeline.py#L1060); no direct public/vehicle execution found, but approval authority/persistence is not enforced. | AUD-009-003, AUD-009-004 |
| FR-025 | PARTIAL | [Scope key](../../apps/agents/evacuation/pipeline.py#L128) labels writes; endpoint/dedup/default context and absence of scoped query tests leave isolation incomplete. | AUD-009-003, AUD-009-008, AUD-009-023 |
| FR-026 | PARTIAL | [Stable neighbor traversal](../../apps/agents/evacuation/router.py#L223) coexists with UUID sort/identity; tests do not compare full outcomes. | AUD-009-022 |
| FR-027 | PARTIAL | [Snapshot creation](../../apps/agents/evacuation/pipeline.py#L1027) uses record count and omits facility/assembly/effective closures; config only in nested versions. | AUD-009-023 |
| FR-028 | PARTIAL | [Audit tiers](../../apps/agents/evacuation/audit.py#L42) exist; canonical fields, several decisions, reconciliation, and robust recovery absent. | AUD-009-026, AUD-009-027 |
| FR-029 | PARTIAL | [Primary create_item](../../apps/agents/evacuation/audit.py#L70) is append-only; record defaults/schema and override provenance do not meet canonical obligations. | AUD-009-004, AUD-009-026, AUD-009-036 |
| FR-030 | MISSING | No audit retrieval implementation in searched agent/API paths; [AuditWriter](../../apps/agents/evacuation/audit.py#L26) only writes/flushes. Mock query returns all records. | AUD-009-026 |
| FR-031 | PARTIAL | [is_stale](../../apps/agents/evacuation/road_network.py#L164) uses load age; stale cache policy and hazard-specific degraded plan not implemented. | AUD-009-024 |
| FR-032 | PARTIAL | [Empty facilities](../../apps/agents/evacuation/transport.py#L96) skip transport, but required incomplete/gap/review notes are absent. | AUD-009-019, AUD-009-024 |
| FR-033 | PARTIAL | [Fallback reduction](../../apps/agents/evacuation/pipeline.py#L920) is multiplicative 0.8; template/narrative confidence and plan-envelope generation metadata disagree. | AUD-009-025, AUD-009-023 |
| FR-034 | PARTIAL | [Health](../../apps/agents/evacuation/agent.py#L380) has six checks but lacks bounded truthful readiness/queue/store state. | AUD-009-028, AUD-009-033 |
| FR-035 | PARTIAL | [Audit/LLM fallbacks](../../apps/agents/evacuation/pipeline.py#L1120) exist; counter errors abort, persistence failure can lose work, stale/generic handling incomplete. | AUD-009-007, AUD-009-012, AUD-009-024, AUD-009-027 |
| FR-036 | PARTIAL | [Mixin safety replacement](../../apps/agents/common/llm_mixin.py#L155) exists and pipeline audits failures; review metadata/contract coverage is incomplete, alternate runtime bypasses planner. | AUD-009-006, AUD-009-025, AUD-009-032 |
| NFR-001 | PARTIAL | [Deployment scale](../../infra/main.bicep#L1180) has only replica limits; shared mutable/local state and no measured 50-plan execution. | AUD-009-008, AUD-009-030, AUD-009-033 |
| NFR-002 | PARTIAL | [Telemetry instruments](../../apps/agents/evacuation/telemetry.py#L145) exist but values, emitting paths, export/alerts are incomplete. | AUD-009-029 |
| SC-001 | UNVERIFIED | [Breach counter](../../apps/agents/evacuation/pipeline.py#L351) exists, but no measured committed initial/replan outcomes; replan is a placeholder. | AUD-009-009, AUD-009-012, AUD-009-033 |
| SC-002 | PARTIAL | [Traceability](../../apps/agents/evacuation/models.py#L196) lacks recommendation/signal references; no 100% trace evidence. | AUD-009-002, AUD-009-023, AUD-009-026 |
| SC-003 | PARTIAL | [Explicit closure test](../../tests/unit/test_evacuation_router.py#L106) asserts no closed waypoint, but no hazard-prepared pipeline assertion; 100% outcome unverified. | AUD-009-001, AUD-009-016, AUD-009-032 |
| SC-004 | PARTIAL | [Transport helper tests](../../tests/unit/test_evacuation_transport.py#L54) cover four categories; no complete affected-group reconciliation in real plans. | AUD-009-019, AUD-009-020, AUD-009-032 |
| SC-005 | PARTIAL | [Deficit string test](../../tests/unit/test_evacuation_timeline.py#L196) does not establish zone shelter dispositions/confidence; pipeline loses urgent data. | AUD-009-005, AUD-009-021 |
| SC-006 | PARTIAL | [Replay test](../../tests/contract/test_evacuation_reproducibility.py#L55) compares scalar surrogates, not actual paths/phases/transport; execution unverified. | AUD-009-022, AUD-009-023, AUD-009-032 |
| SC-007 | MISSING | [Finalisation](../../apps/agents/evacuation/pipeline.py#L1120) contains no reconciliation; full required audit evidence cannot be derived. | AUD-009-026 |
| SC-008 | UNVERIFIED | [Road failure catch](../../apps/agents/evacuation/pipeline.py#L576) permits degraded continuation, but zero-drop outage/recovery outcome has no measured evidence. | AUD-009-007, AUD-009-012, AUD-009-024, AUD-009-032 |
| SC-009 | UNVERIFIED | [Target](spec.md#L316) exists; no inspected commander survey instrument/responses/result. | AUD-009-034 |
| SC-010 | UNVERIFIED | [Replan timing](../../apps/agents/evacuation/agent.py#L246) measures placeholder work; no actual revised-plan latency or 24-hour benefit evidence. | AUD-009-009, AUD-009-010, AUD-009-033 |

## Acceptance Scenario Coverage

AS identifiers below label the original numbered scenarios, not new requirements. Each has its own row.

| Scenario | Status | Expected outcome versus concrete evidence | Follow-up IDs |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Original](spec.md#L41): complete flood plan from references; [pipeline tests](../../tests/unit/test_evacuation_pipeline.py#L70) use invented enriched payload/no stores and reduced envelope. | AUD-009-002, AUD-009-006, AUD-009-023 |
| US1-AS2 | PARTIAL | [Original](spec.md#L42): assessment road closures/explanation; [Stage 4](../../apps/agents/evacuation/pipeline.py#L597) ignores computed closure data. | AUD-009-001, AUD-009-018 |
| US1-AS3 | CONFLICT | [Original](spec.md#L43): increasing versions/supersession; [counter fallback](../../apps/agents/evacuation/versioning.py#L130) unreserved and research protects approved versions. | AUD-009-011, AUD-009-013, AUD-009-036 |
| US1-AS4 | CONFLICT | [Original](spec.md#L44): reject missing assessment; [retrieval](../../apps/agents/evacuation/pipeline.py#L481) builds defaults instead. | AUD-009-002 |
| US2-AS1 | PARTIAL | [Original](spec.md#L58): two open corridors with reason for third exclusion; [router tests](../../tests/unit/test_evacuation_router.py#L106) only inspect returned waypoints. | AUD-009-001, AUD-009-018 |
| US2-AS2 | PARTIAL | [Original](spec.md#L59): distributed loads and >80% flags; [distribution](../../apps/agents/evacuation/router.py#L402) has no plan-wide allocation. | AUD-009-017 |
| US2-AS3 | MISSING | [Original](spec.md#L60): revised route/version/diff; [replan path](../../apps/agents/evacuation/agent.py#L191) does none of those operations. | AUD-009-009, AUD-009-010 |
| US3-AS1 | PARTIAL | [Original](spec.md#L74): 40 wheelchair users, vehicles/pickup/immediate; [mapping/counts](../../apps/agents/evacuation/transport.py#L124) work but fields flatten into notes. | AUD-009-019, AUD-009-020 |
| US3-AS2 | PARTIAL | [Original](spec.md#L75): 200 students, buses, school pickup/supervision; [coordinator](../../apps/agents/evacuation/transport.py#L131) builds notes, scenario integration absent. | AUD-009-019, AUD-009-032 |
| US3-AS3 | PARTIAL | [Original](spec.md#L76): separate critical medical needs; [category tests](../../tests/unit/test_evacuation_transport.py#L54) cover ambulance mapping, not complete destination/scheduling. | AUD-009-019, AUD-009-020 |
| US4-AS1 | PARTIAL | [Original](spec.md#L90): 5,000 residents, zone clearance/components; [timeline](../../apps/agents/evacuation/timeline.py#L44) lacks weighted metrics and unique cohorts. | AUD-009-014, AUD-009-017, AUD-009-021 |
| US4-AS2 | PARTIAL | [Original](spec.md#L91): deficit and shelter by zone; [test](../../tests/unit/test_evacuation_timeline.py#L196) only asserts an assumption string. | AUD-009-005, AUD-009-023 |
| US4-AS3 | CONFLICT | [Original](spec.md#L92) says outer-first; [phase definitions](../../apps/agents/evacuation/timeline.py#L89) and FR-015 say inner-first, starts also wrong. | AUD-009-021, AUD-009-036 |
| US5-AS1 | MISSING | [Original](spec.md#L106): expansion reroute/version/diff/supersession; [agent](../../apps/agents/evacuation/agent.py#L191) only reports triggers. | AUD-009-009, AUD-009-013 |
| US5-AS2 | MISSING | [Original](spec.md#L107): affected-route update within window; [trigger](../../apps/agents/evacuation/replanner.py#L66) ignores active-route membership and no recompute follows. | AUD-009-009, AUD-009-010, AUD-009-033 |
| US5-AS3 | PARTIAL | [Original](spec.md#L108): no redundant version and valid-plan audit; [comparator](../../apps/agents/evacuation/replanner.py#L180) is unused and new handoffs always enter full generation. | AUD-009-009, AUD-009-010 |
| US6-AS1 | PARTIAL | [Original](spec.md#L122): retrieve complete human-reviewable plan; [model](../../apps/agents/evacuation/models.py#L231) omits fields and API only exposes stages. | AUD-009-018, AUD-009-023, AUD-009-025 |
| US6-AS2 | PARTIAL | [Original](spec.md#L123): distinct prioritized accessibility transport; [plan list](../../apps/agents/evacuation/models.py#L249) is separate, priority/location are only prose. | AUD-009-019 |
| US6-AS3 | CONFLICT | [Original](spec.md#L124): justified immutable route override; [endpoint](../../apps/agents/evacuation/agent.py#L529) has wrong scope and no clone. | AUD-009-003, AUD-009-004 |
| US7-AS1 | PARTIAL | [Original](spec.md#L138): simulation invisible to live queries; [scope formatting](../../apps/agents/evacuation/pipeline.py#L128) exists, isolation test/queries do not. | AUD-009-003, AUD-009-008, AUD-009-023 |
| US7-AS2 | PARTIAL | [Original](spec.md#L139): identical routes/timelines; [replay assertions](../../tests/contract/test_evacuation_reproducibility.py#L55) omit actual paths/timelines/transport. | AUD-009-022, AUD-009-023 |
| US7-AS3 | PARTIAL | [Original](spec.md#L140): explicit simulation label/tenant in all records; [plan model](../../apps/agents/evacuation/models.py#L257) has tenant field but no visible label and override audit defaults live. | AUD-009-003, AUD-009-004, AUD-009-023 |
| US8-AS1 | PARTIAL | [Original](spec.md#L154): handoff/assessment/recommendation/plan audit; [audit model](../../apps/agents/evacuation/models.py#L292) omits upstream IDs and completeness. | AUD-009-026 |
| US8-AS2 | PARTIAL | [Original](spec.md#L155): original/modified route and actor/role/reason/time; [override audit](../../apps/agents/evacuation/agent.py#L584) only has prose actor data with missing incident/scope. | AUD-009-004, AUD-009-026 |
| US8-AS3 | PARTIAL | [Original](spec.md#L156): degradation/fallback/confidence audit; [finalisation](../../apps/agents/evacuation/pipeline.py#L1120) records audit-tier degradation but omits other complete outcomes. | AUD-009-024, AUD-009-025, AUD-009-026, AUD-009-027 |

## Edge Cases and Clarifications

EC identifiers label the nine original bullets in order. These are not added scope.

| Edge case | Status | Evidence and remaining behavior | Follow-up IDs |
| --- | --- | --- | --- |
| EC-01 | CONFLICT | [Missing assessment](spec.md#L162) should reject; [Stage 2](../../apps/agents/evacuation/pipeline.py#L448) substitutes defaults. | AUD-009-002 |
| EC-02 | PARTIAL | [Road outage](spec.md#L163): loader age/cache/generic guidance/review/confidence incomplete in [Stage 4](../../apps/agents/evacuation/pipeline.py#L566). | AUD-009-024, AUD-009-025 |
| EC-03 | PARTIAL | [No vulnerable data](spec.md#L164): coordinator skips but required assumptions/local-contact verification warning absent. | AUD-009-019, AUD-009-024 |
| EC-04 | PARTIAL | [All roads closed](spec.md#L165): helper shelter/emergency exists, [Stage 7](../../apps/agents/evacuation/pipeline.py#L799) drops emergency outcome. | AUD-009-005 |
| EC-05 | PARTIAL | [Duplicate delivery](spec.md#L166): local TTL works; replicas, failures and tenant collisions not safe. | AUD-009-007, AUD-009-008 |
| EC-06 | PARTIAL | [Simulation handoff](spec.md#L167): key propagation exists, but control/dedup/retrieval isolation and labels incomplete. | AUD-009-003, AUD-009-008, AUD-009-023 |
| EC-07 | PARTIAL | [Clearance exceeds horizon](spec.md#L168): string warning without persisted remaining-zone shelter or data-quality confidence. | AUD-009-005, AUD-009-021, AUD-009-023 |
| EC-08 | UNVERIFIED | [Unhealthy restart/redelivery](spec.md#L169): no execution evidence; [consumer](../../apps/agents/evacuation/agent.py#L655) permanently dead-letters exceptions, health is unconnected. | AUD-009-007, AUD-009-028, AUD-009-030 |
| EC-09 | PARTIAL | [Old population](spec.md#L170): [zone fallback](../../apps/agents/evacuation/zones.py#L200) invents area-based estimates without age/gap/confidence disclosure. | AUD-009-014, AUD-009-024 |

The 13 clarification answers are also accounted for: graph-only routing (AUD-009-006/016/018); concentric zones
(014/015); five replan triggers (009/010); shelter versus emergency (005/036); baseline timeline and vulnerable
buffer (021); static JSON (T003/T007/031); geospatial classification (001/036); multi-hazard union (015); phase
sequence/transitions (019/021); version format/OCC (011/013); health checks (028); metrics (029); four commander
override capabilities (003/004). Research changed some details; conflicting changes are not silently treated as
approved amendments.

## Amendment Coverage

The later sections are part of the reviewed spec, not optional appendix material. Deferred country functionality is
not classified as missing AU-v1 implementation. Authored placeholders are distinguished from validated outcomes.

| Amendment ID | Status | Evidence and assessment | Follow-up IDs |
| --- | --- | --- | --- |
| ASM-022 | IMPLEMENTED | [AU-v1 scope assumption](spec.md#L323) explicitly defers PH/JP/BD; operational/regulatory outcome is not established. | AUD-009-036 |
| ASM-023 | UNVERIFIED | [Actor-consultation decision](spec.md#L324) names planning/operations/resilience agents; no local invocation/sign-off evidence inspected. No delegation performed here. | AUD-009-036 |
| ASM-024 | IMPLEMENTED | [Taxonomy/schema deferral](spec.md#L325) is authored and IDs present; cross-reference validity does not prove runtime compliance. | AUD-009-036 |
| ASM-025 | UNVERIFIED | [Open residency risk](spec.md#L326) remains explicit; actual region/data handling and external D-009 resolution not established by this audit. | AUD-009-030, AUD-009-036 |
| PER-019 | UNVERIFIED | [Validated label](spec.md#L332) is a cross-reference, not a local SME/persona validation record. | AUD-009-034, AUD-009-036 |
| PER-020 | UNVERIFIED | [Actor-catalogue validated label](spec.md#L333) does not establish consultation or reviewer approval for this implementation. | AUD-009-036 |
| PER-021 | IMPLEMENTED | [Non-AU placeholder](spec.md#L334) explicitly requires D-009 and SME validation; not promoted by this audit. | AUD-009-036 (preserve preconditions) |
| HYP-007 | UNVERIFIED | [Hypothesis](spec.md#L340) links an absent HYP-HYP-007 artifact; [aggregate snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L24) is not per-spec causal/consultation evidence. | AUD-009-036 |
| SCP-022 | IMPLEMENTED | [Country scope deferral](spec.md#L346) explicitly names data/legal/actor gates; no country implementation is demanded here. | AUD-009-036 |
| SCP-023 | IMPLEMENTED | [Constitutional boundary](spec.md#L347) is stated; no constitutional change made in this audit. | AUD-009-036 |
| SCP-024 | IMPLEMENTED | [Authority deferrals](spec.md#L348) preserve warning/recovery ownership; shared-code dependencies are noted without relying on other audits. | AUD-009-036 |
| HYP-030 | UNVERIFIED | [PH evidence](evidence/HYP-030.md#L17) explicitly Not tested; licensed topology/tabletop/D-009 prerequisites not evidenced as cleared. | AUD-009-036 |
| HYP-031 | UNVERIFIED | [JP evidence](evidence/HYP-031.md#L17) explicitly Not tested; no measured 60-second/120-second recommendation outcome. | AUD-009-036 |
| HYP-032 | UNVERIFIED | [BD evidence](evidence/HYP-032.md#L16) explicitly Not tested; no observed lead-time uplift or licensed CPP topology clearance. | AUD-009-036 |

## Checklist and Review-Claim Assessment

### Requirements Checklist: All 100 Items

The original [checklist](checklists/requirements.md#L12) explicitly tests **requirements quality**, not implementation.
All original states below remain `[ ]`. IMPLEMENTED here means a design answer exists; it is not reviewer sign-off.
PARTIAL/MISSING describe the design answer or its specified evidence, not automatically absent product execution.
All unresolved design issues are owned by AUD-009-036, with implementation follow-ups identified where relevant.

| Checklist ID | Original state | Status | Independent assessment and follow-up |
| --- | --- | --- | --- |
| CHK001 | [ ] | IMPLEMENTED | Research task 9 explains Dijkstra versus A*/Bellman-Ford; no measured optimality result implied. |
| CHK002 | [ ] | PARTIAL | Research/model give JSON fields but differ on assembly ID/timestamps/coordinate order and lack valid ranges. AUD-009-031/036. |
| CHK003 | [ ] | PARTIAL | Closure enum exists; hazard-specific extra reasons are collapsed in router. AUD-009-016/018. |
| CHK004 | [ ] | PARTIAL | 80% is specified/configurable; rationale/intermediate handling and actual flag enforcement incomplete. AUD-009-017/036. |
| CHK005 | [ ] | PARTIAL | Five strategy descriptions exist, measurable directional/elevation rules absent. AUD-009-016/036. |
| CHK006 | [ ] | PARTIAL | Data-model lists route units/fields; precision and actual serialization disagree. AUD-009-018/036. |
| CHK007 | [ ] | IMPLEMENTED | Pipeline contract defines congestion then distance tie-break; actual algorithm follow-up AUD-009-022. |
| CHK008 | [ ] | MISSING | No calibrated current/load traffic model in target design; code hardcodes 30 km/h. AUD-009-017/021/036. |
| CHK009 | [ ] | IMPLEMENTED | Pipeline contract budgets five seconds initial and three seconds incremental routing; measurements unverified. AUD-009-033. |
| CHK010 | [ ] | PARTIAL | Polygon buffering describes noncircular boundaries, but origins/zone exits and exclusive populations unresolved. AUD-009-014/036. |
| CHK011 | [ ] | MISSING | No approved per-hazard metric buffer widths in target docs; code uses generic degrees. AUD-009-015/036. |
| CHK012 | [ ] | CONFLICT | Research asserts millimetre precision on EPSG:4326 without a metric projection/tolerance model. AUD-009-015/036. |
| CHK013 | [ ] | CONFLICT | Research says any intersected highest-severity zone; Stage-4 table/FR-009c emphasize fully-contained Zone 1. AUD-009-001/036. |
| CHK014 | [ ] | PARTIAL | Union/highest severity stated; active incident reclassification not connected. AUD-009-009/015. |
| CHK015 | [ ] | PARTIAL | WGS84 named, but valid geometry/resolution/projection acceptance incomplete. AUD-009-031/036. |
| CHK016 | [ ] | MISSING | No detailed zone-override recomputation contract; current modify cannot execute. AUD-009-004/014/036. |
| CHK017 | [ ] | PARTIAL | Four categories defined for MVP; broader current constitutional vulnerable cohorts need explicit scope reconciliation. AUD-009-019/036. |
| CHK018 | [ ] | UNVERIFIED | Authoritative registry/freshness availability assumed, not evidenced by synthetic facilities. AUD-009-024/036. |
| CHK019 | [ ] | IMPLEMENTED | Data-model documents bus/wheelchair/ambulance/medical capacities; accessible-bus detail needs alignment. AUD-009-019/036. |
| CHK020 | [ ] | PARTIAL | Priority map and five phases are stated separately; actual transport-phase scheduling absent. AUD-009-019/021. |
| CHK021 | [ ] | PARTIAL | Dispatch belongs to spec 011, but unmet request/shortage handling not explicit. AUD-009-019/036. |
| CHK022 | [ ] | IMPLEMENTED | FR-011 and Out of Scope clearly separate request from dispatch. No direct vehicle dispatch found. |
| CHK023 | [ ] | PARTIAL | Route suitability required but implemented as name text and not transport feasibility. AUD-009-018/020. |
| CHK024 | [ ] | PARTIAL | Supervision note required; quantified supervision ratio/validation not defined. AUD-009-019/036. |
| CHK025 | [ ] | IMPLEMENTED | Research task 2 defines estimated departure/time model without GPS; calculations remain AUD-009-021. |
| CHK026 | [ ] | PARTIAL | 1.2 configurable factor exists; justification and jurisdiction calibration not specified. AUD-009-021/036. |
| CHK027 | [ ] | PARTIAL | Time fallback implies progress, but safe blocked-phase handling/zero throughput unresolved. AUD-009-005/021/036. |
| CHK028 | [ ] | PARTIAL | FR-015 says advisory/no mandatory transport; coordinator still generates Zone-3 requests. AUD-009-019. |
| CHK029 | [ ] | PARTIAL | Earliest-transition wording implies overlap, but shared-corridor scheduling is undefined. AUD-009-017/021/036. |
| CHK030 | [ ] | CONFLICT | Inner-first rule with undefined capacity exception and outer-first US4-AS3. AUD-009-021/036. |
| CHK031 | [ ] | PARTIAL | Polygon area increase implied; metric/geographic computation and trust of reported percentage unspecified. AUD-009-010/015. |
| CHK032 | [ ] | PARTIAL | Delay trigger stated; authoritative progress reporting/measurement interface absent. AUD-009-010/036. |
| CHK033 | [ ] | PARTIAL | Design says merge simultaneous triggers; atomic scheduling and actual usage absent. AUD-009-009/010. |
| CHK034 | [ ] | CONFLICT | OCC retries documented, but UUID fallback contradicts numeric IDs and implementation returns unreserved values. AUD-009-011/036. |
| CHK035 | [ ] | PARTIAL | Required diff dimensions are listed; template/actual replan omit most. AUD-009-009/010/018. |
| CHK036 | [ ] | UNVERIFIED | Incremental budget is authored; no actual incremental path or measured SLA. AUD-009-009/033. |
| CHK037 | [ ] | CONFLICT | 30-second rate limit specified, with no priority policy reconciling urgent 15-second SLA. AUD-009-010/036. |
| CHK038 | [ ] | PARTIAL | Structural integrity/supplies/comms named, hazard-specific measurable suitability absent. AUD-009-005/036. |
| CHK039 | [ ] | CONFLICT | Contract uses twice mobilisation; code uses fixed 2h/4h and different boundary semantics. AUD-009-005/036. |
| CHK040 | [ ] | PARTIAL | Shelter intent exists; building capacity/locations/procedures not structured in output. AUD-009-005/020. |
| CHK041 | [ ] | MISSING | No maximum-urgency notification channel/contract found in scoped design/implementation. AUD-009-005/036. |
| CHK042 | [ ] | IMPLEMENTED | Research task 3 and amended FR-014 explicitly define recovery/canonical trigger; execution remains AUD-009-009. |
| CHK043 | [ ] | PARTIAL | Four override groups and six actions exist; assembly/transport edit policy not fully reconciled. AUD-009-004/036. |
| CHK044 | [ ] | PARTIAL | Justification required by wording, no nonblank validation or policy detail. AUD-009-003/036. |
| CHK045 | [ ] | IMPLEMENTED | Data-model gives paused-to-approved/cancelled/superseded; enforcement remains AUD-009-004/013. |
| CHK046 | [ ] | MISSING | No coherent override/replan concurrency resolution beyond generic 409 description. AUD-009-004/011/013/036. |
| CHK047 | [ ] | PARTIAL | Commander role named; trusted per-action/incident authorization absent. AUD-009-003/036. |
| CHK048 | [ ] | MISSING | No concrete post-override stakeholder notification/update contract. AUD-009-004/013/036. |
| CHK049 | [ ] | PARTIAL | Stable edge ordering requested; randomized output ordering and surrogate replay assertions remain. AUD-009-022. |
| CHK050 | [ ] | PARTIAL | Config table/hash exists; exact counted set/agent version/input hashes inconsistent. AUD-009-023/031/036. |
| CHK051 | [ ] | IMPLEMENTED | DataSnapshot design names road/population/facility/assembly versions; actual snapshots incomplete. AUD-009-023. |
| CHK052 | [ ] | PARTIAL | Defers to spec 007 while plan/audit TTL none; scoped lifecycle/archive responsibilities need clarification. AUD-009-023/036. |
| CHK053 | [ ] | PARTIAL | Tenant key format and stage validation stated; control/dedup/retrieval do not enforce it end to end. AUD-009-003/008/023. |
| CHK054 | [ ] | IMPLEMENTED | Research task 8 specifies tiers/triggers/flush; robustness requires AUD-009-027. |
| CHK055 | [ ] | CONFLICT | Merged field list exists but contains 23 fields labelled 22; actual audit model differs further. AUD-009-026/036. |
| CHK056 | [ ] | PARTIAL | No TTL/infinite retention authored; archival/legal validation and deployed retention unverified. AUD-009-026/030/036. |
| CHK057 | [ ] | MISSING | No audit query latency objective in local requirements/contracts; retrieval itself absent. AUD-009-026/036. |
| CHK058 | [ ] | PARTIAL | Milliseconds and stages named; some audit durations zero and finalisation has no reconciliation timing. AUD-009-026/029. |
| CHK059 | [ ] | CONFLICT | 1,000/5,000 limits specified; research says warning while task/test reject; timing estimate unmeasured. AUD-009-031/033/036. |
| CHK060 | [ ] | PARTIAL | Six-hour config present; input validation and source-age interpretation incomplete. AUD-009-024/031. |
| CHK061 | [ ] | PARTIAL | Hazard examples exist in FR-031; actual no-network template does not provide those safe degraded outputs. AUD-009-024/025. |
| CHK062 | [ ] | IMPLEMENTED | SC-010 quantifies the update window as 15 seconds; achievement remains UNVERIFIED. AUD-009-033. |
| CHK063 | [ ] | IMPLEMENTED | Research task 4/FR-033 unambiguously choose multiplicative 0.8; final summary consistency remains AUD-009-025. |
| CHK064 | [ ] | PARTIAL | Templates authored but safety approval/effective warning preservation unverified/incomplete. AUD-009-025/034. |
| CHK065 | [ ] | PARTIAL | Seven states/expiry concept documented; expiry not in model or processing. AUD-009-013. |
| CHK066 | [ ] | PARTIAL | Intake/plan budgets are separate in design, not consumer timing. AUD-009-007/033. |
| CHK067 | [ ] | CONFLICT | Amendment changes density to absolute population; persons versus vehicles/hour times distance still lacks calibrated units. AUD-009-017/021/036. |
| CHK068 | [ ] | PARTIAL | Buffer applies to transport by wording; phase representation and mixed mobilisation/travel semantics need alignment. AUD-009-021/036. |
| CHK069 | [ ] | IMPLEMENTED | Static MVP versus future live GIS scope is explicit; no live GIS delivery demanded in this audit. |
| CHK070 | [ ] | PARTIAL | Dedup is by handoff ID, not assessment ID; failure/replica/scoped-key semantics are incomplete. AUD-009-008. |
| CHK071 | [ ] | PARTIAL | Quantitative targets are authored; no attributable outcome runs or survey evidence. AUD-009-032/033/034. |
| CHK072 | [ ] | PARTIAL | Some criteria qualify data availability, but 100% audit/transport guarantees under degradation remain unsupported. AUD-009-019/026/027/036. |
| CHK073 | [ ] | UNVERIFIED | SC-009 has no local participant/instrument/result evidence. AUD-009-034. |
| CHK074 | [ ] | PARTIAL | Receipt-to-persist wording exists; actual timing includes later audit and may follow failed persist. AUD-009-012/029/033. |
| CHK075 | [ ] | PARTIAL | All 25 scenarios authored; ordering/supersession conflicts and omitted test assertions remain. AUD-009-032/036. |
| CHK076 | [ ] | MISSING | No complete crash/partial-plan recovery protocol in target implementation/design. AUD-009-007/008/012. |
| CHK077 | [ ] | PARTIAL | Audit fallback specified; plan/counter/assessment dependency outage handling contradictory. AUD-009-002/012/027. |
| CHK078 | [ ] | MISSING | No explicit safety policy for commander-forced evacuation without viable route. AUD-009-003/004/005/036. |
| CHK079 | [ ] | MISSING | No ordered/versioned road-update ingestion policy; caller-supplied closure strings lack timestamps. AUD-009-010/036. |
| CHK080 | [ ] | CONFLICT | Research task 5 protects approved plan; main FR-017 broadly supersedes on creation. AUD-009-013/036. |
| CHK081 | [ ] | PARTIAL | Pipeline error table requires exhausted assembly warning; allocation/warning not implemented. AUD-009-020. |
| CHK082 | [ ] | UNVERIFIED | Fifty-plan target has no workload/resource measurement evidence for this pipeline. AUD-009-033. |
| CHK083 | [ ] | PARTIAL | Main-template comment says queue >20; actual agent scale block has no such rule. AUD-009-030. |
| CHK084 | [ ] | MISSING | No evacuation cold-start bound/prewarm policy in local design beyond generic platform assumptions. AUD-009-030/033/036. |
| CHK085 | [ ] | PARTIAL | One-second target stated; LLM probe is blocking and HTTP-200 unhealthy semantics need probe alignment. AUD-009-028. |
| CHK086 | [ ] | IMPLEMENTED | AU residency is explicit in constitution/plan; actual scoped services and residency remain UNVERIFIED. AUD-009-030. |
| CHK087 | [ ] | PARTIAL | DR region/resources listed, but evacuation-specific RPO/RTO/recovery evidence not established. AUD-009-030/036. |
| CHK088 | [ ] | PARTIAL | Telemetry contract has 12 thresholds, not an explicit rule mapping for every metric; deployment not found. AUD-009-029. |
| CHK089 | [ ] | PARTIAL | Alert windows defined for selected metrics; complete aggregation/window semantics missing. AUD-009-029/036. |
| CHK090 | [ ] | PARTIAL | Trace parent/correlation hierarchy authored; executable context propagation/nested work incomplete. AUD-009-029. |
| CHK091 | [ ] | MISSING | Local control contract names role but no enforced authentication/authorization boundary. AUD-009-003. |
| CHK092 | [ ] | PARTIAL | Shared validator has rules/fallback; evacuation does not preserve degraded review metadata or test all paths. AUD-009-025. |
| CHK093 | [ ] | PARTIAL | Plan claims aggregate minimization; facility locations/overrides and snapshot privacy classification not substantiated. AUD-009-023/036. |
| CHK094 | [ ] | PARTIAL | Dependency specs named; actual upstream nested HazardMap contradicts consumer expectations. AUD-009-002/006. |
| CHK095 | [ ] | UNVERIFIED | At-least-once assumed, but actual consumer loop/recovery and other update-message idempotency unproven. AUD-009-007/008/010. |
| CHK096 | [ ] | PARTIAL | Five hazard defaults configured; jurisdiction-specific calibration lacks an input/contract. AUD-009-021/031/036. |
| CHK097 | [ ] | PARTIAL | Sample assembly areas exist; missing/unreachable/full registry behavior incomplete. AUD-009-020/024. |
| CHK098 | [ ] | PARTIAL | Checklist says 36 FRs, but suffixed zone requirements make 40; this audit maps all 40. AUD-009-036. |
| CHK099 | [ ] | IMPLEMENTED | Nine edge bullets are mapped individually above; implementation/evidence gaps remain explicit. |
| CHK100 | [ ] | IMPLEMENTED | FR-009a-d are identifiable and covered separately; no range collapse in normative coverage. |

### Plan Constitution Gates

The [plan's 20 PASS labels](plan.md#L43) and post-design "no regressions" assertion are authored design claims,
not dated execution/sign-off evidence. Current constitution numbering also differs from some old labels.

| Gate | Status | Assessment |
| --- | --- | --- |
| G01 | PARTIAL | Life-safety SLA/shelter intent exists; actual emergency propagation/zone closure fails. AUD-009-001/005/033. |
| G02 | PARTIAL | Override/stop endpoints exist without complete authority/version semantics. AUD-009-003/004. |
| G03 | PARTIAL | Explanations exist but lack required facts/traceability and can lose warnings. AUD-009-023/025. |
| G04 | PARTIAL | LLM fallback implemented; stale/absent road/population handling incomplete. AUD-009-024. |
| G05 | PARTIAL | Explicit handoff model exists; actual producer/consumer shape and bootstrap not joined. AUD-009-002/006. |
| G06 | PARTIAL | Versioned model exists; original modification/history guarantees not enforced. AUD-009-004/013. |
| G07 | PARTIAL | New plans proposed and no direct order execution; trusted approval still absent. AUD-009-003/004. |
| G08 | PARTIAL | Road hash exists; actual input snapshots/IDs incomplete. AUD-009-023. |
| G09 | PARTIAL | Freshness helper measures load age, not source age or permitted cached use. AUD-009-024. |
| G10 | PARTIAL | OCC/tie-break helper code exists; safe versions/full replay assertions incomplete. AUD-009-011/022. |
| G11 | UNVERIFIED | Aggregate fixtures are authored; broader production minimization/classification has no target review evidence. AUD-009-023/036. |
| G12 | UNVERIFIED | AU region intent is explicit; actual service/data placement not queried or certified. AUD-009-030. |
| G13 | PARTIAL | Scoped keys written but controls/dedup/queries/tests not complete. AUD-009-003/008/023. |
| G14 | PARTIAL | LLM safety wrapper exists; prompt facts/degraded validator semantics and alternate path gaps remain. AUD-009-006/025. |
| G15 | PARTIAL | Main mixin validates narrative; no full evacuation safety contract test/evidence. AUD-009-025/032. |
| G16 | UNVERIFIED | Azure resource descriptions are not attributable deployment/region evidence. AUD-009-030. |
| G17 | PARTIAL | Three-tier audit/LLM fallback exists but plan durability/file loss protection incomplete. AUD-009-012/027. |
| G18 | PARTIAL | Primary create-only audit source is positive; missing fields/query/reconciliation/durability remain. AUD-009-026/027. |
| G19 | PARTIAL | WAF/scale/observability intent exists; runtime metrics/rules/measurements incomplete. AUD-009-029/030/033. |
| G20 | PARTIAL | Three scenario files exist; substantive hazard/transport/isolation assertions incomplete, execution unverified. AUD-009-032. |

No local named approver, approval timestamp, or review transcript was found proving the pre/post-design gate review
actually occurred. The source-supported findings above also prevent treating the PASS table as implementation evidence.

### Research, Checkpoints, and Evidence Claims

| Claim or record | Assessment |
| --- | --- |
| Research task 1: canonical audit consolidation | Authored, but 22/23 field count and actual model differ; AUD-009-026/036. |
| Research task 2: no-GPS phase estimation | Authored valid scope decision, not implemented transition calculation; AUD-009-021. |
| Research task 3: shelter recovery | Authored amended requirement, helper only; real replan/persist/audit absent; AUD-009-009. |
| Research task 4: multiplicative confidence | Source implements 0.8; final narrative/record consistency and test evidence incomplete; AUD-009-025. |
| Research task 5: existing approved plan | Authored authority-preserving rule, conflicts with broad supersession text and is not implemented; AUD-009-013/036. |
| Research task 6: network schema/sample | Sample delivered; schema examples differ from actual field/coordinate conventions; AUD-009-031/036. |
| Research task 7: Shapely precision/overlap | Library operations exist; precision/projection and Zone-1 exit policy need domain resolution; AUD-009-001/015/036. |
| Research task 8: proven three-tier pattern | Code exists; word "proven" is not execution evidence and current loss/recovery defects remain; AUD-009-027. |
| Research task 9: algorithm choice | Rationale authored; capacity/tie correctness still needs meaningful tests; AUD-009-017/022/032. |
| Research task 10: <10ms graph claim | Unsupported estimate, not a stored benchmark; warning-versus-reject inconsistency also exists; AUD-009-031/033/036. |
| Tasks Phase 1 checkpoint | Package/dependency/fixtures authored; actual dependency installation unverified. |
| Tasks Phase 2 checkpoint | Models/helpers/tests authored, not all validation/OCC/audit guarantees supported. AUD-009-011/023/026/031. |
| Tasks US1 checkpoint | Direct mock pipeline produces reduced plans; trusted complete persisted flow not established. AUD-009-002/006/012. |
| Tasks US2 checkpoint | Graph routing exists, hazard preparation/strategy/allocation incomplete. AUD-009-001/016/017/018. |
| Tasks US3 checkpoint | Vehicle helper exists, complete actionable transport incomplete. AUD-009-019/020. |
| Tasks US4 checkpoint | Formula/phases exist, transitions and safety dispositions incomplete. AUD-009-005/021. |
| Tasks US5 checkpoint | Placeholder replan is not delivery within 15 seconds. AUD-009-009/033. |
| Tasks US6 checkpoint | Summary/endpoints exist, commander control and complete narrative remain incomplete. AUD-009-003/004/025. |
| Tasks US7 checkpoint | Scope fields and scalar replay assertions are not isolation/reproducibility proof. AUD-009-008/022/023. |
| Tasks US8 checkpoint | Audit writer exists, not complete/no-loss/queryable audit. AUD-009-026/027. |
| Tasks Phase 11 "integration tests passing" | No local execution artifacts prove the claim; authored mocks and weak scenarios are assessed above. AUD-009-032/033/035. |
| Quickstart expected JSON | Example, not health execution; no receipt or environment/revision identifies a run. T057 UNVERIFIED. |
| Plan references "19 tests", data-model "14 entities", config "21 parameters" | Counts/definitions are inconsistent with listed files/entities/parameters; do not use them as coverage totals. AUD-009-036. |
| Local HYP-030/031/032 evidence | Correctly states Not tested with external preconditions; no promotion to validated outcome. |
| HYP-007 and rubric snapshots | Named local-linked artifact absent after scoped search; aggregate 1.8-to-3.8 rubric narrative does not prove this spec's actor consultation or causal uplift. AUD-009-036. |
| Later stage/equivalence/load/paired tests | Distinct authored surfaces, not proof of this feature's route correctness, 50 actual plans, 15-second replans, or commander satisfaction. |

## Future Validation Matrix

**None of these commands ran in this audit.** These commands are instructions for later authorized agents after the
corresponding fixes. Run from repository root in a selected Python 3.12+ environment with agent/API/domain dependencies
and root development extras installed. [Test setup](../../tests/conftest.py#L10) adds workspace import paths; the
[root configuration](../../pyproject.toml#L43) defines markers and import mode. Unit tests must inject model/service
doubles and remove live credentials; use temporary audit paths. Do not let a default LLM client contact cloud services.
Do not interpret mock-only tests as service-backed integration. No new code/test/evidence path is claimed to exist.

| Validation ID | Future command or procedure | Prerequisites and expected assertions |
| --- | --- | --- |
| V-MODEL | `python -m pytest tests/unit/test_evacuation_models.py tests/unit/test_evacuation_config.py tests/contract/test_evacuation_plan_schema.py -q` | Full repaired schemas/config; reject inconsistent IDs/invalid bounds, require fields, preserve alias compatibility. |
| V-INTAKE | `python -m pytest tests/contract/test_evacuation_handoff.py tests/unit/test_evacuation_dedup.py -q` | Strict producer-shaped/scoped fixtures; rejection and replay/failure/tenant cases from AUD-009-002/008. |
| V-PIPE | `python -m pytest tests/unit/test_evacuation_pipeline.py -q` | Strict injected stores/LLM/clock; actual geography, adjusted capacities, persisted plan and full audit; no false success. |
| V-ROUTE | `python -m pytest tests/unit/test_evacuation_road_network.py tests/unit/test_evacuation_zones.py tests/unit/test_evacuation_router.py -q` | Small known graphs plus 50/120 sample; exact safe paths/capacities/population/ties/hazard strategies, atomic refresh. |
| V-TRANSPORT | `python -m pytest tests/unit/test_evacuation_transport.py -q` | Typed facilities/destinations; exact counts/locations/priority/zone and unmet-need handling. |
| V-TIME | `python -m pytest tests/unit/test_evacuation_timeline.py -q` | Approved units/threshold policy; exact earliest phase timing, buffer, capacity and shelter/emergency dispositions. |
| V-REPLAN | `python -m pytest tests/unit/test_evacuation_replanner.py tests/unit/test_evacuation_pipeline.py -q` | Stored active v1 and trusted updates; actual v2/diff/recovery or audited no-change, coalescing/rate-limit behavior. |
| V-CONTROL | `python -m pytest tests/unit/test_evacuation_endpoints.py -q` | Identity fixtures, scoped ETag store, no live LLM; full actions/status errors, immutable edits, bounded health. |
| V-STORE | `python -m pytest tests/unit/test_evacuation_versioning.py tests/integration/test_evacuation_cosmos.py -q` | First strict doubles; later explicitly isolated approved Cosmos/emulator with /incident_scope_key. Assert OCC, filters, immutable history, retry durability; retain separate execution receipts. |
| V-BROKER | `python -m pytest tests/integration/test_evacuation_service_bus.py -q` | Drive real consumer adapter; strict broker doubles, then separately approved isolated broker; correct durable acknowledgment/retry/dead-letter behavior. |
| V-REPLAY | `python -m pytest tests/contract/test_evacuation_reproducibility.py -q` | Complete fixed snapshots, distinct live/simulation tenants, deterministic clock; exact path/timeline/transport comparisons and isolation queries. |
| V-AUDIT | `python -m pytest tests/unit/test_evacuation_audit.py tests/unit/test_evacuation_pipeline.py -q` | Capacity-one buffer/temp spill/strict store; no-loss recovery, chronology, scope, annotations, and deliberate missing-step detection. |
| V-TELEMETRY | `python -m pytest tests/unit/test_evacuation_pipeline.py tests/unit/test_evacuation_endpoints.py -q` | Add recording instruments/exporters first; assert all contract metrics/events, meaningful IDs, hierarchy and actual outcomes. Existing tests alone do not do this. |
| V-SCENARIO | `python -m pytest tests/simulation/test_cyclone_evacuation_scenario.py tests/simulation/test_bushfire_evacuation_scenario.py tests/simulation/test_flood_evacuation_scenario.py -q` | Repaired true simulation tenants, persisted hazards/facilities, known safe/dangerous roads; meaningful non-vacuous route/transport/shelter assertions. |
| V-RUNTIME | `python -m evacuation.agent` then `Invoke-RestMethod http://localhost:8082/health` | Future repaired standalone bootstrap only; inject isolated services/reference paths. Verify receipt, six actual health checks, plan retrieval/override/replan and clean shutdown. Container runtime may have a different approved entrypoint; do not assume this command tests the dispatcher. |
| V-CAPACITY | `python -m pytest tests/load/test_workflow_capacity.py -k evacuation -q` | **Proposed test selector, not present yet**. Add actual 50-plan/30s/15s/sub-second cases under AUD-009-033; no selected tests is a failure, not success. Isolated approved environment and measured artifacts required. |
| V-SURVEY | Facilitated commander exercise and structured survey; no automated substitute. | Approved participant/protocol/consent, usable repaired plans, 90% target and denominator; record real outcomes without rewriting existing evidence. |
| V-DOC | Text-only ID/link/contract comparison, then authorized domain/actor review. | Resolve AUD-009-036 decisions, document source/reviewer/date, keep deferred countries explicit and original evidence intact. |

Infrastructure build/what-if/deployment and actual cloud validation remain later platform work, subject to applicable
skills, policy discovery, and explicit approval. No command here grants permission to change infrastructure or records.
Any proposed new evidence or test artifact must be clearly marked proposed in that later work until it exists.

## Cross-Spec Impact and Completion Order

- Intake adaptation affects the shared handoff/HazardAssessment contract and Risk Assessment producer; do not
  silently change their payloads to match enriched evacuation test fixtures.
- Runtime repair affects MAF executors, dispatcher packaging, and simulation/rehearsal callers. Preserve their
  independent public schemas and explain the difference between conversation, process stages, and deterministic plans.
- Transport requests belong to evacuation; vehicle dispatch belongs to Resource Allocation. Public warnings belong
  to Communication. Emergency operator notification must preserve those authority boundaries.
- Tenant/auth, Cosmos conditional writes, LLM safety metadata, and telemetry are shared concerns. Their impacts here
  were established from inspected code, not inherited from other specification audits.
- Resolve AUD-009-036 safety precedence before conflicting algorithm/lifecycle changes. Then address P0 intake,
  graph, controls, and dispositions; connect runtime/durability; complete planning/provenance/audit; finally obtain
  actual integration, load, quickstart, and human exercise evidence. Existing checkboxes must not be retroactively
  treated as proof of those future activities.

## Document Validation Receipt

Text-only validation on 2026-09-11 passed for this report:

| Check | Result |
| --- | --- |
| Original task IDs and exact original checked states | 59 expected, 59 individual rows; all original [x] states preserved. |
| Normative requirement IDs | 52 expected, 52 individual rows: 40 FRs, 2 NFRs, 10 SCs. |
| Acceptance scenarios | 25 expected, 25 individual rows. |
| Edge cases and amendment IDs | 9/9 edge cases and 14/14 amendment rows. |
| Original checklist IDs and states | 100/100 individual rows; all original [ ] states preserved. |
| Open remediation tasks | 36/36 unique IDs; every remediation box unchecked; no undefined full follow-up ID. |
| Local Markdown targets and line bounds | 341 links checked; all targets exist and referenced line numbers are in bounds. |
| Duplicate or unexpected coverage rows | None. |

The initial editor check found one MD047 trailing-newline warning; this report received a newline-only formatting
repair together with this receipt. Product tests and all runtime/deployment/sign-off outcomes remain UNVERIFIED.

## 2026-09-19 Continuation Remediation

The evacuation API contract fixture now explicitly enables the guarded trusted-test identity path and sends a test
incident-controller principal. This removes dependence on ambient authentication configuration while preserving the
production rule that forwarded test identities are rejected. The combined evacuation stage and API contract slice
returns `41 passed, 2 warnings`.

This repair validates the existing protected stage-management contract only. Deterministic planner runtime
composition, durable plan/decision persistence, queue intake, deployment, performance, exercise, and human approval
evidence remain open as documented above.

# Resource Allocation Agent: Implementation Review and Remediation Tasks

**Review date:** 2026-09-11  
**Source revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Method:** Fresh, isolated, static code-versus-specification review.  
**Disposition:** Not ready to claim end-to-end delivery. Safety-critical workflow and persistence gaps remain.  
**Coverage:** 70 original tasks; 50 requirements/success criteria, including FR-031a; 29 acceptance scenarios; 9 edge cases; 13 clarification decisions; 13 numbered amendment obligations; 48 allocation checklist items; 16 generic checklist items; 20 pre/post-design gate claims.  
**Follow-ups:** 41 unchecked tasks, AUD-011-001 through AUD-011-041.

## 1. Scope, Inputs, and Evidence Limits

The governing [Review Contract](../001-spec-implementation-audit/README.md#L13) was read in full. Only this report was authored. Original task states, source, design artifacts, evidence, and the audit index were not changed. No feature, branch, or commit was created. No delegation occurred. No product tests, builds, imports, deployments, cloud-resource queries, or external approval requests were performed.

`git rev-parse HEAD` matched the revision above. A read-only `git diff --name-only HEAD` check over the reviewed source families and original spec folder reported no tracked differences. This establishes the inspected tracked-source baseline, not deployment state or runtime correctness. Workspace text search timed out; `rg` was unavailable. Scoped tracked-file searches used `git grep` and `git ls-files`, supplemented by direct reads. Negative conclusions below name their scope; they are not claims about uninspected systems.

### Complete Local Inputs

All 14 pre-existing files in this feature folder were read completely:

- [spec.md](spec.md#L1), including both clarification sessions and all appended assumptions, personas, hypotheses, scope statements, and recovery cross-references.
- [tasks.md](tasks.md#L1), including all 70 task descriptions, dependency ordering, test-first instructions, checkpoints, and delivery strategy.
- [plan.md](plan.md#L1), [research.md](research.md#L1), [data-model.md](data-model.md#L1), and [quickstart.md](quickstart.md#L1).
- [contracts/allocation-pipeline.md](contracts/allocation-pipeline.md#L1), [contracts/health-endpoint.md](contracts/health-endpoint.md#L1), and [contracts/telemetry.md](contracts/telemetry.md#L1).
- [checklists/allocation.md](checklists/allocation.md#L1) and [checklists/requirements.md](checklists/requirements.md#L1).
- [evidence/HYP-036.md](evidence/HYP-036.md#L1), [evidence/HYP-037.md](evidence/HYP-037.md#L1), and [evidence/HYP-038.md](evidence/HYP-038.md#L1).

Associated authoritative inputs included the [constitution](../../.specify/memory/constitution.md#L1), [persona-profile contract](../027-spec-hardening/contracts/persona-profile.md#L1), [hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1), and the allocation call site's [transactional RAG opt-out ADR](../../docs/decisions/036-foundry-rag-grounding/05-rag-optout-logistics-transactional.md#L1). The code-review and Bicep instructions and Python fact-grounded-coding skill were loaded. Python runtime and SDK behavior not established by static source remain unverified; no interpreter setup or application import was attempted.

No sibling implementation audit report was used. A historical rubric baseline named by the specification was not used to infer current implementation or approval. The source assertions in all 19 originally named test files were inspected, plus the related [MAF equivalence test](../../tests/equivalence/test_resource_allocation_equivalence.py#L17). A checked task, test filename, mock response, schema-shaped fixture, or authored approval statement is not execution evidence.

### Status Legend

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Full scoped behavior or authored artifact is supported by inspected source; execution is not implied. |
| PARTIAL | Some behavior exists, but a specific required part is absent or contradicted. |
| MISSING | Required behavior or artifact was not found after the stated relocation/source search. |
| CONFLICT | Requirements, task directions, or current behavior disagree and need explicit resolution. |
| UNVERIFIED | Source cannot establish execution, measurement, approval, or deployed state. |
| SUPERSEDED | Explicit repository evidence identifies a replacement; this does not automatically retire related functional obligations. |

### Connected Paths and Relocation Checks

| Surface | Concrete evidence and conclusion |
| --- | --- |
| Standalone worker | [agent.py:112](../../apps/agents/resource_allocation/agent.py#L112) constructs the legacy pipeline; [agent.py:428](../../apps/agents/resource_allocation/agent.py#L428) starts HTTP only, without constructing Cosmos clients or a message receiver. Source searches covered tracked `apps/agents`, `apps/api`, `packages`, `infra`, the deployment manifest, and workflow definitions. No external construction of `ResourceAllocationAgent` or `AllocationProcessingPipeline` was found in those runtime surfaces. |
| Actual deployment selection | [azure.yaml:38](../../azure.yaml#L38) selects the shared agents image; [Dockerfile:48](../../apps/agents/Dockerfile#L48) starts `dispatcher`; [infra/main.bicep:1109](../../infra/main.bicep#L1109) serves agents on 8080. The [dispatcher invoke handler](../../apps/agents/dispatcher/agent.py#L215) returns narrative replies, not persisted deployment plans. |
| Relocated MAF path | [resource_executor.py:8](../../apps/agents/maf_runtime/workflow/executors/resource_executor.py#L8) resolves through [_base.py:177](../../apps/agents/maf_runtime/workflow/executors/_base.py#L177) to [ResourceAllocationMafAgent.run_legacy](../../apps/agents/maf_runtime/agents/resource_allocation_agent.py#L25), which returns an empty v1 plan. MAF mode uses [_factory.py:267](../../apps/agents/maf_runtime/agents/_factory.py#L267) to ask a model for the output object, with [no allocation tools](../../apps/agents/maf_runtime/agents/resource_allocation.yaml#L30). Neither path supplies algorithmic matching, ownership, or durable plan lifecycle. |
| Simulation adapter | [resource_allocation_adapter.py:10](../../apps/api/app/services/simulation/sub_agents/resource_allocation_adapter.py#L10) forwards a question to the dispatcher; it is not a relocated implementation of this spec's allocation pipeline. |
| Upstream producer | [risk_assessment/agent.py:520](../../apps/agents/risk_assessment/agent.py#L520) emits reference IDs and a summary, not complete coordination-task records. [TransportRequirement](../../apps/agents/evacuation/models.py#L163) and [TransportHandoffPayload](../../apps/agents/common/handoff_payloads.py#L17) use snake_case fields unlike this pipeline's camelCase payload. No allocation-side adapter consuming that typed payload was found. |
| Lifecycle and telemetry relocation | Searches for `process_status_update`, `release_incident_resources`, `distribute_proportionally`, and `resource_allocation.telemetry` in the runtime scopes above found the standalone definitions but no connected lifecycle/proportional/telemetry caller. [pipeline.py:895](../../apps/agents/resource_allocation/pipeline.py#L895) only writes a final record; it does not reconcile or flush. |
| Infrastructure relocation | Searches for the allocation module, its queue, and both container names found declarations in [resource-allocation.bicep](../../infra/modules/resource-allocation.bicep#L63), but no invoking module or runtime container lookup in the checked deployment paths. The alternative simulation scaler is commented out at [infra/bicep/main.bicep:591](../../infra/bicep/main.bicep#L591); it does not establish allocation-queue scaling. |
| Amendment relocation | Tracked persona filenames were found under [operational/logistics-officer.agent.md](../../.github/agents/operational/logistics-officer.agent.md#L1), [operational/operations-officer.agent.md](../../.github/agents/operational/operations-officer.agent.md#L1), and [operational/resilience-planner.agent.md](../../.github/agents/operational/resilience-planner.agent.md#L1), not the asserted technical location. Exact and nearby `HYP*009*` filename searches in feature 028 evidence, and the full local evidence inventory, found no referenced HYP-009 stub. Presence of persona definitions is not consultation evidence. |

## 2. Prioritized Findings

### P0: Safety, Authority, and Data Integrity

1. **Overrides falsely report success and trust caller-supplied identity.** [agent.py:382](../../apps/agents/resource_allocation/agent.py#L382) checks only action/justification, writes an audit record, and returns success without loading or changing a plan. No JWT dependency is present. [Endpoint assertions](../../tests/unit/test_resource_allocation_endpoints.py#L17) exercise unseeded plans without authentication and only check response fields. Commanders could believe approval, cancellation, or reassignment occurred when it did not. Follow-ups: AUD-011-002, AUD-011-003.
2. **Mixed-demand allocation can choose the wrong resource type or subtype.** [pipeline.py:531](../../apps/agents/resource_allocation/pipeline.py#L531) unions per-demand eligible lists. [matcher.py:102](../../apps/agents/resource_allocation/matcher.py#L102) then scores every union member for each demand, while [scoring.py:68](../../apps/agents/resource_allocation/scoring.py#L68) omits type compatibility. A nearby minibus with `passenger_transport` can satisfy a bus demand when both enter the union. The [type tests](../../tests/unit/test_resource_allocation_scoring.py#L111) call only the separate helper. Follow-up: AUD-011-005.
3. **Planning does not reserve or persist resource ownership.** [matcher.py:39](../../apps/agents/resource_allocation/matcher.py#L39) prevents reuse only inside one call. [pipeline.py:836](../../apps/agents/resource_allocation/pipeline.py#L836) never transitions assigned inventory. Later incident plans can reuse the same resource; no persistence-time ownership check closes the scoring/commit race. Follow-ups: AUD-011-004, AUD-011-017.
4. **Approved plans can be silently superseded, even if replacement storage fails.** [pipeline.py:855](../../apps/agents/resource_allocation/pipeline.py#L855) supersedes both proposed and approved plans without an approval gate or ETag condition. It runs before replacement creation; [pipeline.py:836](../../apps/agents/resource_allocation/pipeline.py#L836) swallows write errors and returns success to the caller. Follow-ups: AUD-011-014, AUD-011-015.
5. **Version exhaustion bypasses concurrency guarantees.** [versioning.py:138](../../apps/agents/resource_allocation/versioning.py#L138) returns `current_version + 1` without reserving it, or 1 on read failure. Different workers can receive the same version. [Version tests](../../tests/unit/test_resource_allocation_versioning.py#L16) use only local counters and do not exercise Cosmos conflicts. Follow-up: AUD-011-013.
6. **Deployment and replacement paths do not deliver the specified allocation workflow.** The standalone [startup](../../apps/agents/resource_allocation/agent.py#L428) has no queue intake or durable-client composition. The selected dispatcher is narrative-only, the [MAF fallback](../../apps/agents/maf_runtime/agents/resource_allocation_agent.py#L25) is empty, and MAF model generation bypasses the algorithm-only decision boundary. This is not merely a missing historical filename. Follow-ups: AUD-011-001, AUD-011-033.
7. **Missing records and fabricated demand context are accepted.** [pipeline.py:162](../../apps/agents/resource_allocation/pipeline.py#L162) checks only a nonempty incident ID. [pipeline.py:232](../../apps/agents/resource_allocation/pipeline.py#L232) fabricates recommendation data from the payload and tolerates absent assessments. [pipeline.py:349](../../apps/agents/resource_allocation/pipeline.py#L349) falls back to Sydney coordinates and an invented generic demand. Life-safety prioritisation and provenance can therefore be wrong while the plan appears valid. Follow-ups: AUD-011-006, AUD-011-008.

### P1: Missing Operational Guarantees

- **Global prioritisation and reallocation are disconnected.** [pipeline.py:275](../../apps/agents/resource_allocation/pipeline.py#L275) creates a fresh queue for one handoff; extracted demands all have its incident ID. The [cross-incident stage](../../apps/agents/resource_allocation/pipeline.py#L603) cannot discover other active incidents and emits empty allocations/recommendations even when called with synthetic contention. The proportional helper sums quantity, unlike the research decision's unmet-demand count. AUD-011-010, AUD-011-011, AUD-011-012, AUD-011-021.
- **Transport integration is only a synthetic-payload path.** No typed producer adapter, superseded-plan lookup, assignment-level transport references, inventory assignment, or transport audit event is connected. Wheelchair capability on a `bus` in the [sample inventory](../../data/resource-inventories/sample-inventory.json#L59) is excluded by a demand subtype of `wheelchair_accessible`. AUD-011-009.
- **Simulation isolation is incomplete.** Labels and plan partition keys exist, but a single inventory is shared, local version/dedup keys omit tenant scope, and [status handling](../../apps/agents/resource_allocation/agent.py#L178) hardcodes `live`. Lack of all plan-triggered inventory writes is not evidence of simulation isolation. AUD-011-007, AUD-011-016, AUD-011-022.
- **Lifecycle, operational flags, and degraded data handling are incomplete.** An expiry timestamp is not an expiry worker. No connected closure, resource-availability, or destroyed-resource replan trigger was found. Hours are not accumulated, stock units conflict between docs/config, and stale age is recorded without stale-data confidence penalties. AUD-011-018, AUD-011-019, AUD-011-020, AUD-011-021, AUD-011-025, AUD-011-026.
- **Summaries can misstate the operational situation.** The normal template receives `plan=None`; it reports incident `unknown` and version 1. The transport template omits partial deficits and calls proposed resources "dispatched". The LLM receives counts rather than the assignments/locations/hazard evidence. Shared content safety exists, but allocation audit/validation metadata is omitted. AUD-011-027, AUD-011-028.
- **Audit recoverability and completeness are not established.** Required event kinds and decision payload fields are absent from connected writes. File-spill exceptions are swallowed; recovery is not scheduled; partial memory failures can be followed by later file writes; duplicate-create conflicts can block replay. No allocation query/reconciliation surface was found in the stated runtime search. AUD-011-029, AUD-011-030.
- **Health and telemetry can mask failure.** [agent.py:287](../../apps/agents/resource_allocation/agent.py#L287) always labels LLM connectivity healthy and omits queue/plan/demand counts. [telemetry.py:91](../../apps/agents/resource_allocation/telemetry.py#L91) declares instruments but no connected allocation caller emits them. AUD-011-031, AUD-011-032.

### P2: Verification and Contract Debt

- Models accept inconsistent confidence labels, invalid quantities/shortfalls, and unordered timelines; snapshot hashes omit allocation-affecting fields. AUD-011-023, AUD-011-024.
- Test-first history and runtime pass claims are unverified. Unit/contract assertions omit promised negative/concurrency cases. Both integration files contain unconditional `pytest.skip`; the scenario fixtures do not establish all advertised behaviors. AUD-011-034, AUD-011-035, AUD-011-036.
- SLAs, 30 concurrent plans, efficiency uplift, commander satisfaction, and quickstart execution have no qualifying evidence in the reviewed local records. Design/readiness checkmarks cannot supply it. AUD-011-037, AUD-011-038, AUD-011-039, AUD-011-040.
- Version fallback, priority taxonomies, proportionality, auth/action names, stock units, SLA interpretation, and amended governance need explicit contract reconciliation. The 30% target was described as aspirational in research, not demonstrated or formally removed. AUD-011-041.

## 3. Open Remediation Tasks

These are instructions for later authorized work, not changes made by this audit. Preserve the algorithm-only allocation boundary, append-only decision history, AU data-persistence boundary, tenant isolation, and commander approval. Public contract changes require explicit resolution rather than silently rewriting the original spec. Test cases below belong in the named existing test homes; additional cases/fixtures are proposed additions, not existing proof. V1-V9 refer to the future-only validation matrix in section 8.

### Runtime and Safety

- [ ] AUD-011-001 [P0] Connect one authoritative allocation runtime and its intake.
  **Obligations:** FR-001, FR-005, FR-014, FR-026, FR-036; T023, T024, T046; US1 and US3.
  **Expected / actual / impact:** A running worker consumes validated handoffs and status signals with durable dependencies. [Startup](../../apps/agents/resource_allocation/agent.py#L428), [MAF fallback](../../apps/agents/maf_runtime/agents/resource_allocation_agent.py#L25), and [MAF generation](../../apps/agents/maf_runtime/agents/_factory.py#L267) instead expose disconnected HTTP, an empty plan, or model-decided output. Allocation requests need not reach the algorithm.
  **Developer:** Own composition in agent startup, the MAF facade/executor, and [Dockerfile](../../apps/agents/Dockerfile#L48). Resolve the documented MAF replacement with AUD-011-041; inject inventory, stores, dedup, audit, and a bounded intake lifecycle. Implement success settlement, retriable failures, poison-message rejection, shutdown and backpressure. Do not let the model choose assignments or claim physical dispatch.
  **Tester positive:** In [Service Bus test home](../../tests/integration/test_resource_allocation_service_bus.py#L20), feed real serialized Risk Assessment and Evacuation payloads through the selected entrypoint; assert nonempty algorithmic results and durable IDs.
  **Tester negative:** Malformed/untrusted payload goes to rejection/dead-letter handling; store failure does not acknowledge successful planning.
  **Tester edge:** Slow planning beyond the intake acknowledgement target, consumer restart, empty queue, and 31 pending incidents retain work without double settlement.
  **Dependencies / validation:** AUD-011-006, AUD-011-007, AUD-011-015, AUD-011-033, AUD-011-041; V4, V8.
  **Acceptance:** Deployment-selected entrypoints exercise the same verified allocation service; no empty-plan or narrative substitute counts as delivery.

- [ ] AUD-011-002 [P0] Implement truthful commander override mutations.
  **Obligations:** FR-024, FR-025, FR-026; T039, T040, T041, T042; US5-AS1, US5-AS2, US5-AS3.
  **Expected / actual / impact:** [Override handler](../../apps/agents/resource_allocation/agent.py#L382) returns success without plan lookup, status transition, assignment change, or new version; commanders receive false confirmation.
  **Developer:** Own the handler and pipeline override service. Load the tenant-scoped plan, validate action/detail combinations and current status, and implement all seven operations. Modification actions create a linked new version and recompute matching/shortfalls/timelines as appropriate; status actions change only permitted status fields. Release only relevant pending assignments on rejection/cancellation. Return real version and audit IDs.
  **Tester positive:** Extend [endpoint tests](../../tests/unit/test_resource_allocation_endpoints.py#L17) with a seeded proposed plan and two demands; read back every mutation, provenance link, and original version.
  **Tester negative:** Missing plan, missing action details, incompatible manual resource, and illegal terminal-state transitions yield the documented errors, not success.
  **Tester edge:** Reassign the last matching resource, remove the only assignment, approve twice, and race two modifications; assert consistent shortfalls and no historical content mutation.
  **Dependencies / validation:** AUD-011-003, AUD-011-004, AUD-011-013, AUD-011-015, AUD-011-041; V3, V4.
  **Acceptance:** Success is returned only after the requested durable state change and corresponding immutable audit record exist.

- [ ] AUD-011-003 [P0] Authenticate, authorize, and tenant-scope overrides.
  **Obligations:** FR-024, FR-025, FR-027; T040, T042, T048; CHK040; research decision 12.
  **Expected / actual / impact:** [Research](research.md#L239) requires trusted commander claims; [handler](../../apps/agents/resource_allocation/agent.py#L382) trusts body `user_id`/`role` and lacks authentication. Both authority and audit attribution are spoofable.
  **Developer:** Own endpoint dependencies and the trusted ingress boundary. Validate or consume cryptographically verified claims, derive identity/role from them, authorize the plan's incident/tenant, and default auth on. Permit dev disabling only in explicitly isolated nonproduction contexts; do not trust arbitrary forwarded headers or JSON identity.
  **Tester positive:** In [endpoint tests](../../tests/unit/test_resource_allocation_endpoints.py#L17), use a signed commander fixture and assert claim-derived audit identity.
  **Tester negative:** Missing, expired, wrong-issuer/audience, noncommander, cross-tenant tokens, and forged body claims are refused before audit-success or plan writes.
  **Tester edge:** An authorized commander with several incident scopes cannot approve an out-of-scope incident; disabling auth must not enable a production/live bypass.
  **Dependencies / validation:** Resolve `commander` versus `incident_commander` under AUD-011-041; V3, V8. Actual ingress authentication remains a separately authorized check.
  **Acceptance:** Every successful override has verified subject, authority, tenant, incident, and mandatory justification.

- [ ] AUD-011-004 [P0] Commit resource ownership atomically with allocation.
  **Obligations:** FR-010, FR-011, FR-013, FR-014; T018, T022, T023, T028, T033, T069; CHK009, CHK031.
  **Expected / actual / impact:** [Matcher](../../apps/agents/resource_allocation/matcher.py#L39) has only per-call exclusion; [persistence](../../apps/agents/resource_allocation/pipeline.py#L836) leaves inventory available. A scarce ambulance can appear in multiple active plans.
  **Developer:** Own inventory ownership and pipeline persistence. Recheck type, capabilities, operational status, tenant, and ownership at commit with conditional writes or a documented concurrency protocol. Reserve/assign resources durably, record previous/new status and trigger, and release or reconcile failed provisional claims. Preserve approved allocations unless explicitly authorized.
  **Tester positive:** In [matcher tests](../../tests/unit/test_resource_allocation_matcher.py#L61) and [Cosmos tests](../../tests/integration/test_resource_allocation_cosmos.py#L20), allocate one fully capable ambulance and assert its recorded incident and assignment state.
  **Tester negative:** A second incident cannot claim it; a resource destroyed between scoring and commit cannot appear as successfully assigned.
  **Tester edge:** Two independent workers compete for one resource; exactly one ownership commit succeeds and the other plan reports a shortfall/retry without overwriting the winner.
  **Dependencies / validation:** AUD-011-013, AUD-011-015, AUD-011-017, AUD-011-022; V2, V4.
  **Acceptance:** No duplicate active ownership exists across calls, replicas, restarts, or tenants, and every state change is audited.

- [ ] AUD-011-005 [P0] Recheck pair eligibility inside the matcher.
  **Obligations:** FR-011, FR-012, SC-003; T009, T012, T016, T022, T027, T028; US2-AS1, US2-AS2.
  **Expected / actual / impact:** [Union construction](../../apps/agents/resource_allocation/pipeline.py#L531) loses demand-specific eligibility. [compute_score](../../apps/agents/resource_allocation/scoring.py#L68) checks capabilities/status but not category/subtype, despite the unused [type helper](../../apps/agents/resource_allocation/scoring.py#L49).
  **Developer:** Own matcher candidate filtering and scoring. Enforce category/subtype, all capabilities, tenant/incident reservation, status, valid position and return-window policy for each pair, including direct matcher calls. Keep the existing scoring formula and deterministic tie order for eligible pairs.
  **Tester positive:** Extend [matcher tests](../../tests/unit/test_resource_allocation_matcher.py#L61) with a farther bus and closer minibus sharing `passenger_transport`, plus demands for both; the bus demand must get the bus.
  **Tester negative:** Wrong category/subtype with identical capabilities must score as ineligible; an empty capability list must not bypass type constraints.
  **Tester edge:** Multi-demand union, exact equal scores, zero-distance candidates, and partially met requests preserve strict compatibility and explicit shortfalls.
  **Dependencies / validation:** AUD-011-009, AUD-011-017, AUD-011-024; V1, V2, V3.
  **Acceptance:** Every persisted assignment is independently verifiable against its matched demand, not merely membership of the union pool.

- [ ] AUD-011-006 [P0] Validate real incident and upstream records before planning.
  **Obligations:** FR-001, FR-002, FR-004, FR-006, SC-002; T014, T023, T026; US1-AS4; EC-01; CHK032.
  **Expected / actual / impact:** [Stage 1](../../apps/agents/resource_allocation/pipeline.py#L162) accepts any nonempty incident ID; [stage 2](../../apps/agents/resource_allocation/pipeline.py#L232) does not read recommendations and tolerates missing assessments. Nonexistent or closed incidents can receive invented plans.
  **Developer:** Own boundary validation and scoped incident/recommendation/assessment retrieval. Distinguish malformed input, not-found data, closed incidents, and transient outages. Do not convert missing authoritative records into successful summary-derived plans. Reject with specific audit reasons; route transient failures to the documented retry/degradation policy.
  **Tester positive:** Extend [pipeline validation tests](../../tests/unit/test_resource_allocation_pipeline.py#L90) and [handoff contracts](../../tests/contract/test_resource_allocation_handoff.py#L11) with store fixtures containing mutually linked records.
  **Tester negative:** Nonempty nonexistent ID, closed incident, missing/wrong-tenant recommendation or assessment, bad payload type, and mismatched references produce no plan or ownership write.
  **Tester edge:** A retrievable but incomplete record versus a timed-out read yields distinguishable, recoverable results and audit types.
  **Dependencies / validation:** AUD-011-001, AUD-011-007, AUD-011-022, AUD-011-026, AUD-011-041; V3, V4.
  **Acceptance:** No plan is labelled traceable solely because it echoes unchecked input IDs.

- [ ] AUD-011-007 [P1] Make deduplication success-aware and tenant-safe.
  **Obligations:** FR-003, FR-027, FR-036, SC-009; T008, T015, T023, T048; EC-04.
  **Expected / actual / impact:** [is_duplicate](../../apps/agents/resource_allocation/dedup.py#L35) marks first sight immediately; [stage 1](../../apps/agents/resource_allocation/pipeline.py#L194) calls it before later failures. Retries after OCC/store failure can be discarded, while local state provides no multiworker guarantee and omits tenant identity.
  **Developer:** Own dedup and pipeline settlement. Separate in-flight claim from successful completion, release/retry failed claims, use tenant-scoped keys, enforce concurrency safety and bounded TTL, and reconcile restarts/replicas with durable completion evidence. Keep duplicate-discard auditing.
  **Tester positive:** In [dedup tests](../../tests/unit/test_resource_allocation_dedup.py#L18), one successful handoff followed by redelivery yields one plan and one discard record.
  **Tester negative:** A failed first attempt must remain processable; equal IDs from different tenants must not suppress each other.
  **Tester edge:** Concurrent deliveries, process restart, exact TTL boundary, cache-capacity eviction, and exception after version assignment cannot cause loss or duplicate effects.
  **Dependencies / validation:** AUD-011-015, AUD-011-022; V2, V3, V4.
  **Acceptance:** Dedup prevents duplicate effects without suppressing unfinished work.

### Demand, Transport, and Cross-Incident Behavior

- [ ] AUD-011-008 [P0] Extract authoritative, complete geolocated demands.
  **Obligations:** FR-006, FR-007, FR-012, FR-014; T014, T017, T023, T029; US1-AS1, US1-AS2.
  **Expected / actual / impact:** [Extraction](../../apps/agents/resource_allocation/pipeline.py#L349) ignores retrieved recommendation content, uses keyword/substrings and default Sydney coordinates, and invents an emergency-responder demand. [Assessment task parsing](../../apps/agents/resource_allocation/pipeline.py#L418) can supply `location=None` to a dict field and double-count summary/task descriptions.
  **Developer:** Own normalization of coordination tasks and assessment affected areas. Preserve source task IDs, category/subtype, required capabilities, units, quantities, task priority, incident severity and original request time. Use an explicit missing-location policy; do not fabricate coordinates or needs. Handle all four categories and reconcile duplicate descriptions.
  **Tester positive:** Extend [demand tests](../../tests/unit/test_resource_allocation_pipeline.py#L126) with structured flood tasks for all categories, explicit quantities and Brisbane coordinates.
  **Tester negative:** Ambiguous prose, missing geometry, invalid quantity, and unrelated substrings must not create invented bus/personnel needs or substitute Sydney.
  **Tester edge:** Summary plus structured copy of one task produces one demand; multiple distinct same-subtype tasks remain distinct and none disappears.
  **Dependencies / validation:** AUD-011-006, AUD-011-010, AUD-011-024; V3, V5.
  **Acceptance:** Every output demand maps to an authoritative input obligation, and every valid input demand is represented with its actual location and priority context.

- [ ] AUD-011-009 [P1] Connect and reconcile evacuation transport contracts.
  **Obligations:** FR-005, FR-008, FR-014, SC-005; T026, T030, T031, T032, T033; all US3 scenarios; EC-06; CHK029, CHK045.
  **Expected / actual / impact:** [Consumer](../../apps/agents/resource_allocation/pipeline.py#L313) accepts only synthetic camelCase records, unlike [actual entity fields](../../apps/agents/evacuation/models.py#L163) and [typed payload](../../apps/agents/common/handoff_payloads.py#L17). It neither looks up evacuation versions nor carries per-assignment transport IDs. Wheelchair-equipped buses fail exact subtype matching.
  **Developer:** Own producer-consumer adaptation without silently breaking either contract. Map vehicle category versus capability, quantities, pickup points, original priority/time, destination context and requirement IDs. Resolve superseded plans to the latest active version; explicitly reject/hold when none exists. Put the resolved evacuation/requirement references on each dispatch assignment and emit transport audit events. Keep recommendations proposed.
  **Tester positive:** In [handoff contracts](../../tests/contract/test_resource_allocation_handoff.py#L11) and [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L126), serialize actual producer models and request four wheelchair vehicles from six positioned capable resources.
  **Tester negative:** A bus without wheelchair capability, obsolete requirement absent from the current plan, and superseded plan with no active successor must not dispatch.
  **Tester edge:** Six available buses for ten requested yields six assignments and an explicit four-bus deficit; critical/immediate/high ordering follows the ratified mapping with complete assignment references.
  **Dependencies / validation:** AUD-011-004, AUD-011-005, AUD-011-006, AUD-011-027, AUD-011-041; V3, V4, V5.
  **Acceptance:** Real upstream payloads reach compatible resources and current-plan traceability, not just synthetic schema construction.

- [ ] AUD-011-010 [P1] Maintain a consolidated, fully ordered demand queue.
  **Obligations:** FR-007, FR-009, FR-021, SC-004; T010, T017, T023, T036.
  **Expected / actual / impact:** [Fresh queue per handoff](../../apps/agents/resource_allocation/pipeline.py#L275) and [sort key](../../apps/agents/resource_allocation/priority.py#L134) do not retain other incidents, represent severity separately, compute proximity, or use the upstream timestamp. Unknown priorities become moderate without the research-prescribed warning.
  **Developer:** Own queue lifetime and normalized demand metadata. Insert/remove/close demands across active incidents within a tenant. Apply the ratified single-incident and cross-incident order, with real severity, candidate proximity and request timestamps. Respect approved ownership and ensure arrival order cannot override life safety.
  **Tester positive:** Extend [priority tests](../../tests/unit/test_resource_allocation_priority.py#L79) with reverse-arrival Tier 1/2/3 demands and distinct urgency/severity.
  **Tester negative:** Unknown priorities must not gain unintended precedence; closed or completed demands must not recur.
  **Tester edge:** Equal urgency with different severity, equal severity with different distances, and final timestamp ties use the specified discriminator, not a default zero-distance or processing clock.
  **Dependencies / validation:** AUD-011-008, AUD-011-022, AUD-011-041; V2, V3, V5.
  **Acceptance:** Connected allocation always uses the tenant's full ordered pending demand set and records the decisive ordering fields.

- [ ] AUD-011-011 [P1] Implement meaningful cross-incident trade-offs and guarded reallocation.
  **Obligations:** FR-013, FR-021, FR-023, SC-004; T022, T034, T035, T036; US4-AS1, US4-AS2; US8-AS3.
  **Expected / actual / impact:** [Contention detection](../../apps/agents/resource_allocation/matcher.py#L252) compares category only. [Stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) gets single-incident demands and emits empty per-incident allocation and recommendation lists. Commanders cannot see donor losses or approve a real proposed transfer.
  **Developer:** Own matcher cross-incident analysis using active scoped plans, all unmet demands and donor-resource eligibility. Identify only genuinely contested compatible capacity, compare actual tiers/severity, quantify donor gaps and recipient gain, and emit source/destination/resource-level recommendations. Approval must precede ownership changes; retain/update donor plan history through the approved workflow.
  **Tester positive:** Extend [contention tests](../../tests/unit/test_resource_allocation_matcher.py#L184) and [multi-incident tests](../../tests/simulation/test_multi_incident_scenario.py#L62) with critical life-safety demand and an eligible lower-tier donor resource.
  **Tester negative:** Different subtypes/capabilities, a higher-priority donor, or denied approval must not cause transfer.
  **Tester edge:** Three incidents, insufficient capacity, simultaneous recommendations for one donor, and partial approvals yield explicit noncontradictory gain/loss records.
  **Dependencies / validation:** AUD-011-002, AUD-011-004, AUD-011-010, AUD-011-014; V2, V3, V5.
  **Acceptance:** Every recommendation states who gains, who loses, why, and what remains unmet; no silent reassignment occurs.

- [ ] AUD-011-012 [P1] Apply the true-tie proportional allocation rule.
  **Obligations:** FR-022; T010, T034, T037; US4-AS3; EC-09; research decision 8.
  **Expected / actual / impact:** [distribute_proportionally](../../apps/agents/resource_allocation/priority.py#L178) is disconnected, sums requested quantities rather than unmet-demand count, and does not verify equal tier/severity/population. The rule tested is not the documented rule.
  **Developer:** Own the tie branch in the connected cross-incident matcher. Resolve the population-versus-unmet-count conflict, identify genuine ties, use only unmet demand, and allocate integer resources with a deterministic remainder rule. Include the ratio and losses in the trade-off explanation; flag affected commanders.
  **Tester positive:** Extend [proportional tests](../../tests/unit/test_resource_allocation_priority.py#L139) with five unmet demand records versus three and eight compatible resources.
  **Tester negative:** Five units in one demand versus one unit in another must not masquerade as five-versus-one unmet records under the count rule; unequal severity must not invoke proportional allocation.
  **Tester edge:** Odd resource count, zero demand, zero inventory, fulfilled demands and three-way equal ties preserve deterministic totals without over-allocation.
  **Dependencies / validation:** AUD-011-010, AUD-011-011, AUD-011-041; V2, V5.
  **Acceptance:** The connected result and rationale match the ratified proportional rule and exhaust no more than the available pool.

### Persistence, State, and Lifecycle

- [ ] AUD-011-013 [P0] Fail safely on version-counter contention.
  **Obligations:** FR-015, SC-007; T013, T019; CHK037; research decision 7.
  **Expected / actual / impact:** [Counter exhaustion](../../apps/agents/resource_allocation/versioning.py#L48) falls through to an unreserved version; local counters ignore tenant scope. Research explicitly forbids UUID fallback, while task text also requests it.
  **Developer:** Own versioning and its pipeline error contract. Use verified SDK ETag preconditions, handle concurrent create/replace conflicts, bounded exponential jitter, and propagate an exhausted-conflict result without assigning a guessed number. Scope local/test counters consistently. Do not change public plan IDs to UUID suffixes without resolving the conflict.
  **Tester positive:** Extend [version tests](../../tests/unit/test_resource_allocation_versioning.py#L16) with a fake enforcing ETags, then exercise actual conditional writes in [Cosmos tests](../../tests/integration/test_resource_allocation_cosmos.py#L31).
  **Tester negative:** Repeated 412 or failed fallback read returns no version/plan and leaves the handoff retryable.
  **Tester edge:** Two workers create the first counter, concurrent increments, duplicate incident IDs in different tenants, and exhausted retries never produce the same reserved version.
  **Dependencies / validation:** AUD-011-007, AUD-011-022, AUD-011-041; V2, V4. SDK-call acceptance is unverified until that future integration check.
  **Acceptance:** Each successful version is uniquely reserved in the correct scope; retries never degrade into an uncommitted integer.

- [ ] AUD-011-014 [P0] Protect approved plans and conditional supersession.
  **Obligations:** FR-013, FR-015, FR-025, FR-026; T023, T039, T041; US1-AS3, US5-AS4.
  **Expected / actual / impact:** [Supersession](../../apps/agents/resource_allocation/pipeline.py#L855) replaces approved records without review or concurrency conditions. An approved operational plan can disappear when new information arrives.
  **Developer:** Own plan lifecycle persistence. New information creates a separate proposed version while retaining the approved plan until an authorized transition. Supersede only eligible prior proposed versions after a safe replacement commit. Use conditional status-only mutations and audit old/new version links; never overwrite original demand/assignment content.
  **Tester positive:** In [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L173), store proposed v1 then v2; retain immutable content and the appropriate superseded status.
  **Tester negative:** Approved v1 must remain approved when v2 is merely generated; a racing commander approval must not be overwritten.
  **Tester edge:** Replacement write failure, missing historical versions, stale ETag and cancellation concurrent with replanning leave a consistent authoritative plan.
  **Dependencies / validation:** AUD-011-002, AUD-011-013, AUD-011-015, AUD-011-041; V3, V4.
  **Acceptance:** Supersession cannot remove commander-approved authority without a recorded authorized decision.

- [ ] AUD-011-015 [P0] Preserve plans and retry work across store failures.
  **Obligations:** FR-014, FR-015, FR-034, FR-036, SC-009; T023, T024, T064; pipeline stage 8 contract.
  **Expected / actual / impact:** [Persistence](../../apps/agents/resource_allocation/pipeline.py#L836) catches every exception; [finalization](../../apps/agents/resource_allocation/pipeline.py#L895) still records plan generation. No durable pending-plan retry or recovery is connected, and earlier supersession can already have occurred.
  **Developer:** Own the commit result and retry/recovery protocol. Distinguish generated, durably committed and queued-for-retry outcomes, retain a recoverable plan/claim until persistence succeeds, and settle the message accordingly. Keep audit degradation independent of plan durability. Ensure restart recovery does not reserve resources twice.
  **Tester positive:** Extend [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L173) with a successful plan-store round trip.
  **Tester negative:** Fail create/replace writes and assert no false success, irreversible supersession or completed dedup marker.
  **Tester edge:** Store recovers after process restart, partial commit, duplicate create response, and exhausted capacity must reconcile once without losing the plan.
  **Dependencies / validation:** AUD-011-004, AUD-011-007, AUD-011-013, AUD-011-014, AUD-011-030; V3, V4.
  **Acceptance:** Every accepted handoff has a durable plan or recoverable, visibly pending work item; outages do not silently drop it.

- [ ] AUD-011-016 [P1] Process complete, ordered, tenant-scoped status signals.
  **Obligations:** FR-018, FR-027, FR-030, SC-001; T043, T044, T046; US6-AS1, US6-AS2.
  **Expected / actual / impact:** [Status handler](../../apps/agents/resource_allocation/agent.py#L178) ignores event time/category/tenant, uses `live`, and applies location/capacity only after a state change. A consumption-only update or returning resource can remain incorrectly attributed.
  **Developer:** Own status intake and inventory mutation. Validate the full signal, scope the resource, use ordered event identity/time, distinguish state transitions from capacity/location updates, clear ownership when return completes, and persist/audit previous and new values with the actual trigger. Route real status messages to this handler.
  **Tester positive:** Extend [inventory tests](../../tests/unit/test_resource_allocation_inventory.py#L71) through the agent handler using a complete assigned/en-route/deployed sequence and consumption-only signal.
  **Tester negative:** Invalid category, missing timestamp, stale event, wrong tenant and unauthorized restored-resource signal cannot mutate inventory.
  **Tester edge:** Duplicate timestamps, equal-status capacity updates, location-only updates and returning-to-available must retain correct provenance without stale incident assignment.
  **Dependencies / validation:** AUD-011-001, AUD-011-017, AUD-011-022, AUD-011-029; V2, V3, V4.
  **Acceptance:** Valid updates are applied once with event provenance, while invalid/out-of-order signals leave state unchanged and explain why.

- [ ] AUD-011-017 [P1] Complete state-machine and reservation eligibility rules.
  **Obligations:** FR-010, FR-011, FR-018; T011, T016, T018, T043; CHK021, CHK030, CHK034, CHK039.
  **Expected / actual / impact:** [Transition table](../../apps/agents/resource_allocation/inventory.py#L33) cannot mark available stock unavailable and permits restored availability without checking commander authority. Same-incident reserved resources pass [eligibility](../../apps/agents/resource_allocation/inventory.py#L175) but score zero in [config](../../apps/agents/resource_allocation/config.py#L150). Return ETA is not represented or checked.
  **Developer:** Own inventory transitions and pair eligibility. Ratify broken-available-resource and recall semantics, enforce authorized restoration, audit every transition, reconcile reservation scoring, and preserve the demand return-window prerequisite unless explicitly amended. Do not use direct state assignments to bypass validation.
  **Tester positive:** Extend [state tests](../../tests/unit/test_resource_allocation_inventory.py#L71) with reserved-to-assigned/released, available-to-broken, and authorized restoration.
  **Tester negative:** General matching cannot use another incident's reservation; unapproved restoration/recall and late-return candidates are rejected.
  **Tester edge:** Return exactly at the demand deadline, reservation expiry during scoring, and a reserved candidate with otherwise maximum score have explicit outcomes.
  **Dependencies / validation:** AUD-011-003, AUD-011-004, AUD-011-016, AUD-011-041; V1, V2.
  **Acceptance:** State acceptance, eligibility and score agree, and active invalid resources cannot remain allocatable.

- [ ] AUD-011-018 [P1] Compute operational limits from real status history.
  **Obligations:** FR-019; T011, T043, T045; US6-AS2, US6-AS3; CHK017.
  **Expected / actual / impact:** [Flagging](../../apps/agents/resource_allocation/inventory.py#L137) trusts prefilled deployment hours, accumulates flags without clearing them, and has no mechanical-issue path. Stock value `20` in quickstart is compared as a ratio against a default `0.2` setting. Fatigue and replenishment advice can be missing or constantly active.
  **Developer:** Own deployment-time accumulation/reset, consumption bounds and flag recalculation. Restrict rotation to applicable personnel, ingest explicit mechanical condition, normalize threshold units, and clear flags after rest/replenishment/repair. Expose flagged resources and replacements to the next plan, not just eligible-resource scans.
  **Tester positive:** In [flag tests](../../tests/unit/test_resource_allocation_inventory.py#L152), use an injected clock and deployment start time, 19/100 stock, and a mechanical fault signal.
  **Tester negative:** 12 hours exactly, 20/100 stock, negative capacity and a vehicle without a fault must not trigger inappropriate flags.
  **Tester edge:** Rest/redeploy, replenishment back above threshold, zero initial stock, and the documented environment override give correct flag reset and thresholds.
  **Dependencies / validation:** AUD-011-016, AUD-011-025; V2, V3, V5.
  **Acceptance:** Rotation, replenishment and degradation reflect current measured conditions and are visible in allocation outputs.

- [ ] AUD-011-019 [P1] Expose complete utilisation queries.
  **Obligations:** FR-020; T018, T045, T050, T057; US6-AS4.
  **Expected / actual / impact:** [compute_utilisation](../../apps/agents/resource_allocation/inventory.py#L258) returns global counts only, with no per-type/per-incident grouping, resource filter/query interface, active/expired plan counts, or separate en-route count in the returned totals.
  **Developer:** Own utilisation aggregation and its authorized read surface. Return consistent state totals, per-type percentages, incident assignments, flag detail and relevant plan counts, respecting tenant/location/type filters. Keep public naming and percentage-versus-ratio units documented.
  **Tester positive:** Extend [utilisation tests](../../tests/unit/test_resource_allocation_inventory.py#L303) with all four categories, two incidents, available/en-route/deployed states and flagged personnel/supplies.
  **Tester negative:** Another tenant's resources must not appear; malformed filters must not broaden access.
  **Tester edge:** Empty pool, all resources reserved/unavailable, zero denominator and expired plans preserve consistent totals and percentages.
  **Dependencies / validation:** AUD-011-004, AUD-011-018, AUD-011-020, AUD-011-022; V2, V3.
  **Acceptance:** Commanders can answer all FR-020 and US6-AS4 questions using actual scoped data.

- [ ] AUD-011-020 [P1] Execute expiry, closure, and resource-release lifecycle.
  **Obligations:** FR-009, FR-024, FR-026; T018, T039, T041, T050, T055; CHK005, CHK008, CHK032.
  **Expected / actual / impact:** [Generation](../../apps/agents/resource_allocation/pipeline.py#L647) sets expiry but no timer/query performs it. [Bulk release](../../apps/agents/resource_allocation/inventory.py#L228) is uncalled and bypasses state audit. Pending plans and claims can outlive their incidents indefinitely.
  **Developer:** Own a restart-safe lifecycle trigger and scoped plan/resource release. Expire only unapproved overdue proposals, cancel applicable plans on closure, close demands, and release only resources actually held by those plans. Do not free a resource already reassigned/approved elsewhere. Keep originals queryable and audit each state change.
  **Tester positive:** Extend [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L173) and [bulk-release tests](../../tests/unit/test_resource_allocation_inventory.py#L273) with a clock crossing four hours and an incident-closure signal.
  **Tester negative:** Approved plan, nonexpired proposal, other incident/tenant and replaced ownership must remain unchanged.
  **Tester edge:** Restart after missed expiry, duplicate closure, concurrent approval at expiry and partially dispatched resources yield an explicit safe transition policy.
  **Dependencies / validation:** AUD-011-002, AUD-011-004, AUD-011-014, AUD-011-016; V2, V3, V4.
  **Acceptance:** Expiry and closure are connected, idempotent effects with truthful plan/resource counts, not timestamp-only metadata.

- [ ] AUD-011-021 [P1] Trigger replanning on availability and resource loss.
  **Obligations:** FR-012, FR-018, FR-019, FR-023; T038, T044, T046; CHK011, CHK033; EC-08.
  **Expected / actual / impact:** [Status processing](../../apps/agents/resource_allocation/agent.py#L178) does not query unmet demands, invalidate dependent assignments, or schedule replanning. Restored capacity stays unused and destroyed resources can remain in active recommendations.
  **Developer:** Own status-to-replan scheduling and persistent unmet demand state. Match newly available capacity across active incidents, flag plans dependent on lost resources, generate a new proposed version, and preserve approved authority until reviewed. Coalesce duplicate triggers to avoid version churn.
  **Tester positive:** In [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L126), approve a partial plan, then return a matching resource; assert a new proposal covers the deficit.
  **Tester negative:** An irrelevant resource or closed incident must not trigger a plan; lost resources cannot remain silently valid.
  **Tester edge:** Destroy an assigned resource mid-plan, restore several resources together, and redeliver status signals; assert one coherent replan and correct donor/recipient gaps.
  **Dependencies / validation:** AUD-011-010, AUD-011-011, AUD-011-014, AUD-011-016, AUD-011-020; V3, V5.
  **Acceptance:** Both capacity gains and losses lead to auditable, approval-preserving allocation updates.

### Isolation, Models, and Degradation

- [ ] AUD-011-022 [P0] Enforce tenant boundaries in every allocation state store.
  **Obligations:** FR-027; T026, T047, T048; all US7 scenarios; EC-05.
  **Expected / actual / impact:** [Agent inventory](../../apps/agents/resource_allocation/agent.py#L135) is shared for every handoff; [local counters](../../apps/agents/resource_allocation/versioning.py#L58) use incident ID alone; [status audit](../../apps/agents/resource_allocation/agent.py#L225) chooses `live`; assignments have no tenant field. Partition labels alone do not isolate simulation from operational inventory.
  **Developer:** Own tenant context across intake, inventory snapshots, demand queue, versions, dedup, plan/audit storage, status signals and queries. Validate event tenant/scope agreement, maintain separate simulation inventory state and block cross-tenant reads/mutations. Make all nested records unambiguously scoped through explicit identity or enforced parent contracts.
  **Tester positive:** Extend [reproducibility contracts](../../tests/contract/test_resource_allocation_reproducibility.py#L77) with live and two simulation tenants sharing identical incident/resource/handoff IDs.
  **Tester negative:** Plan, override, status and utilisation queries must not read or alter another tenant; conflicting tenant/scope input is rejected.
  **Tester edge:** Interleave plan generation, returns, cancellation, audit flush and process recovery across those tenants; assert distinct counters and inventories.
  **Dependencies / validation:** AUD-011-003, AUD-011-007, AUD-011-013, AUD-011-016; V3, V4, V5.
  **Acceptance:** Isolation is demonstrated through attempted cross-boundary effects, not through a test that merely constructs a tenant-labelled handoff.

- [ ] AUD-011-023 [P1] Record replay-complete snapshots and deterministic assignments.
  **Obligations:** FR-028, FR-029, SC-007; T047, T049.
  **Expected / actual / impact:** [Inventory hash](../../apps/agents/resource_allocation/inventory.py#L311) omits coordinates, capabilities, subtype, capacity and ownership; [config hash](../../apps/agents/resource_allocation/config.py#L174) omits travel/mobilisation settings. Demands are snapshotted after mutation, generated IDs/clocks vary, and no recoverable full inventory reference is retained.
  **Developer:** Own canonical input capture and stable semantic identifiers. Capture immutable pre-match demands, complete inventory or a durable content-addressed reference, all decision-affecting configuration and original timestamps. Keep matching deterministic and separate explicitly nondeterministic metadata from replay assertions. Retain the shared zero-temperature summary setting without allowing LLM output to determine assignments.
  **Tester positive:** Extend [reproducibility tests](../../tests/contract/test_resource_allocation_reproducibility.py#L77) to replay frozen input and compare exact demand-to-resource identities, ranking and scoring parameters, not sorted scores alone.
  **Tester negative:** Change only location, capabilities, subtype, capacity, ownership or travel speed; the appropriate snapshot/config digest must change.
  **Tester edge:** Permuted inventory order, equal-score candidates, restart, and identical semantic inputs with different run IDs produce the defined identical allocation result.
  **Dependencies / validation:** AUD-011-008, AUD-011-010, AUD-011-024; V1, V3, V5.
  **Acceptance:** A reviewer can reconstruct the decision inputs and obtain the same allocation, not just verify a 64-character hash.

- [ ] AUD-011-024 [P1] Enforce model invariants at the boundaries.
  **Obligations:** FR-006, FR-010, FR-011, FR-014, FR-017, FR-031; T005, T006, T025.
  **Expected / actual / impact:** [Models](../../apps/agents/resource_allocation/models.py#L139) default most required data, accept invalid quantities/positions/status strings, and do not enforce shortfall/timeline equations. [_derive_confidence_level](../../apps/agents/resource_allocation/models.py#L338) simply returns the supplied value; a low score can be labelled high.
  **Developer:** Own schema validation for finite coordinates/scores, required references, positive quantities, bounded capacity, allowed statuses, consistent plan ID/version, derived confidence, expiry order and timeline/shortfall arithmetic. Define quantity units for supplies/facilities. Reject incoherent input before matching and reject invalid persisted outputs without mutating originals.
  **Tester positive:** Extend [model tests](../../tests/unit/test_resource_allocation_models.py#L100) and [plan contracts](../../tests/contract/test_resource_allocation_plan_schema.py#L24) with complete valid records for each category.
  **Tester negative:** Omitted references, NaN/infinite or out-of-range coordinates, negative quantities, contradictory shortfalls, arbitrary assignment status and score/label mismatch must fail or normalize according to the ratified contract.
  **Tester edge:** Confidence 0.4/0.7, zero capacity, exact mobilisation-only travel, expiration equality and assignment to an unknown demand are asserted explicitly.
  **Dependencies / validation:** AUD-011-025, AUD-011-041; V1, V3.
  **Acceptance:** Invalid data cannot look contract-compliant solely because optional/default fields were serialized.

- [ ] AUD-011-025 [P1] Validate configuration and reconcile units and connections.
  **Obligations:** T002, T004, T007; FR-003, FR-011, FR-017, FR-019, FR-034; research/data-model configuration tables.
  **Expected / actual / impact:** [Config validation](../../apps/agents/resource_allocation/config.py#L123) validates only LLM settings; zero distance floor, invalid weights/windows and stock ratios are accepted. Cosmos/Service Bus/auth parameters required by T004 are absent. Quickstart's `REPLENISHMENT_THRESHOLD_PERCENT=20` conflicts with the code's ratio `0.2`.
  **Developer:** Own typed configuration and runtime composition. Validate finite positive distance/speed/window/capacity values and bounded factors; explicitly define percent versus ratio conversion, recognized connection variable names, and fail-closed auth defaults. Avoid multiple unused LLM settings or untracked decision-affecting configuration. Preserve intentional fixed availability=1.0 through an explicit documented decision.
  **Tester positive:** Extend [config tests](../../tests/unit/test_resource_allocation_config.py#L16) with all required defaults and documented overrides, including transport speeds and stock threshold conversion.
  **Tester negative:** Invalid strings, zero/negative distance floor or audit capacity, out-of-range ratios and unknown connection/auth values are rejected with clear errors.
  **Tester edge:** Minimum/maximum valid settings, missing optional variables, unit migration and all hash-relevant changes are covered.
  **Dependencies / validation:** AUD-011-001, AUD-011-023, AUD-011-041; V1, V8.
  **Acceptance:** Documented configuration is consumed and validated consistently; following quickstart cannot silently change 20% into 2000%.

- [ ] AUD-011-026 [P1] Apply truthful inventory and dependency degradation.
  **Obligations:** FR-034, FR-036, SC-009; T059; research decision 4; CHK018.
  **Expected / actual / impact:** [Stage 4](../../apps/agents/resource_allocation/pipeline.py#L531) only reads in-memory resources. [Plan confidence](../../apps/agents/resource_allocation/pipeline.py#L647) applies only summary fallback penalty; [staleness](../../apps/agents/resource_allocation/pipeline.py#L824) is recorded but never governs eligibility or confidence. Old/partial inventory can appear authoritative.
  **Developer:** Own inventory refresh/snapshot recovery and degradation classification. Track last-known-good age and partial-read state, use snapshots only under the ratified staleness policy, expose uncertainty and unmet demand, and apply independent multiplicative penalties. Distinguish absent required references from transient dependency failure; do not blanket-swallow faults.
  **Tester positive:** Extend [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L173) with full inventory, a recent cached snapshot during outage, and combined stale/partial/template conditions.
  **Tester negative:** Missing or over-window snapshot cannot yield an apparently fresh high-confidence allocation; failure must not silently discard a handoff.
  **Tester edge:** Exactly 30 minutes, clock skew, partial categories, empty inventory and dependency recovery produce explicit, auditable results.
  **Dependencies / validation:** AUD-011-006, AUD-011-015, AUD-011-025, AUD-011-030, AUD-011-041; V3, V4.
  **Acceptance:** Degraded plans state which data is stale/missing and use the configured confidence factors without compromising recoverability.

- [ ] AUD-011-027 [P1] Ground summaries in actual plan facts and deficits.
  **Obligations:** FR-012, FR-014, FR-016, FR-026; T020, T029, T030, T058; US1-AS1, US3-AS3; CHK012, CHK016, CHK043.
  **Expected / actual / impact:** [Summary construction](../../apps/agents/resource_allocation/pipeline.py#L749) passes `plan=None` to [normal templates](../../apps/agents/resource_allocation/templates.py#L13); [transport templates](../../apps/agents/resource_allocation/templates.py#L124) omit partial shortages and say "dispatched". The model sees counts but not the actual resources, destination, hazard reasoning or trade-off details.
  **Developer:** Own summary context and all four template generators. Supply incident/version, assignments, destination, hazard references, priorities, exclusions, operational flags, shortfalls and trade-offs as structured facts. Clearly distinguish proposed from approved/dispatched; render partial transport deficits and actionable mutual-aid advice. Apply a defined readable AIIMS terminology policy.
  **Tester positive:** Extend [summary tests](../../tests/unit/test_resource_allocation_pipeline.py#L228) with v3 Brisbane flood, named resources, pickup points and four missing buses; inspect both prompt input and fallback text.
  **Tester negative:** Summary must not claim dispatch for a proposed plan, invent an unknown incident/version or hide a positive shortfall.
  **Tester edge:** Empty inventory, many assignments, long identifiers, multiple gaps and reserved resources remain understandable and complete within the agreed output limits.
  **Dependencies / validation:** AUD-011-008, AUD-011-009, AUD-011-011, AUD-011-018, AUD-011-041; V3, V5, V7.
  **Acceptance:** Commanders can understand what, where, why, approval state and remaining gaps from both AI and fallback summaries.

- [ ] AUD-011-028 [P1] Preserve content-safety and fallback provenance.
  **Obligations:** FR-016, FR-030, FR-033, FR-037; T055, T058, T060.
  **Expected / actual / impact:** [LLMCallMixin](../../apps/agents/common/llm_mixin.py#L64) does invoke validation and returns safety/template fallback. [Allocation generation](../../apps/agents/resource_allocation/pipeline.py#L647) preserves the method and 0.8 penalty, but omits safety-failure/degradation decision records and validation metadata. The shared validator can itself degrade to keyword checks.
  **Developer:** Own allocation interpretation of the shared mixin result. Keep runtime checks before persistence, record content-safety failure, dependency degradation, validator mode/review flag and chosen fallback, and retain approved-template behavior. Preserve algorithmic assignments on all LLM failures; do not claim the RAG opt-out ADR proves factual grounding or approval.
  **Tester positive:** In [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L228), inject safe model text and assert validated summary inclusion with provenance.
  **Tester negative:** Inject a failed safety result or LLM exception; assert template replacement, exact method, 0.8 confidence factor and required audit event without persisting rejected text.
  **Tester edge:** Safety service outage with keyword fallback, open circuit breaker and combined stale-data penalties propagate truthful review/degradation metadata.
  **Dependencies / validation:** AUD-011-026, AUD-011-027, AUD-011-029; V3.
  **Acceptance:** Fallback output remains available while the audit explains precisely why and how validation degraded.

### Audit and Observability

- [ ] AUD-011-029 [P1] Complete canonical audit payloads, reconciliation, and queries.
  **Obligations:** FR-030, FR-031, FR-032, SC-008; T021, T042, T055, T056; all US8 scenarios.
  **Expected / actual / impact:** [_write_audit](../../apps/agents/resource_allocation/pipeline.py#L922) omits scoring detail, candidate/exclusion counts and input/assignment payloads; [record model](../../apps/agents/resource_allocation/models.py#L348) lacks several FR-031 fields. Required transport, exclusion, expiry, degradation and safety event paths are not connected; finalization is not reconciliation. Override audit has no before/after assignment or valid incident scope.
  **Developer:** Own canonical records, stage/event emitters and authorized audit queries. Reconcile the 26-field design with FR-031, write immutable decision-level facts for every processing branch, include source/destination transfer gaps and exact override before/after values, and implement incident/plan/type/resource/time filters. Reconcile processed handoffs and expected stage records, not just count all records.
  **Tester positive:** Extend [audit tests](../../tests/unit/test_resource_allocation_audit.py#L31) and [pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L90) with a complete allocation/override/status/reallocation sequence and assert each mandatory field/event/filter.
  **Tester negative:** Intentionally omit a stage record, attempt overwrite/delete, or cross-tenant query; reconciliation/access controls must reject or report the discrepancy.
  **Tester edge:** Rejected and duplicate handoffs, zero assignments, multiple resource exclusions and time-range boundaries remain queryable and attributable.
  **Dependencies / validation:** AUD-011-002, AUD-011-009, AUD-011-011, AUD-011-016, AUD-011-022, AUD-011-024, AUD-011-030; V3, V4.
  **Acceptance:** Every required event is reconstructable with the actual decision inputs, not merely a plan-generated message or enum member.

- [ ] AUD-011-030 [P1] Make audit buffering recoverable, ordered, and loss-aware.
  **Obligations:** FR-031a, FR-036, SC-008, SC-009; T051, T052, T053, T054, T056; CHK006, CHK038.
  **Expected / actual / impact:** [Write/spill](../../apps/agents/resource_allocation/audit.py#L42) falls through three tiers, but [file-spill failure](../../apps/agents/resource_allocation/audit.py#L84) is swallowed. [Flush](../../apps/agents/resource_allocation/audit.py#L108) is uncalled, can proceed to later file records after memory failure, and treats duplicate-create responses as failures. File size is unbounded and buffer/file recovery state is not restart-safe or fully reflected in health.
  **Developer:** Own scheduled recovery and the storage protocol. Preserve original IDs, chronological ordering and durable retry state; make duplicate creates idempotent; use safe file rotation/atomic recovery, bounded capacity and explicit failure signaling. Record degradation transitions, annotate before serialization, and report tier/backlog accurately. Keep audit data and durable spill storage in authorized AU/tenant boundaries.
  **Tester positive:** Extend [audit tests](../../tests/unit/test_resource_allocation_audit.py#L102) with capacity 2, memory plus JSONL records and recovered Cosmos; assert every exact record ID and annotation in timestamp order.
  **Tester negative:** Disk-full/permission failures, duplicate 409s, malformed lines and a failing first memory record must not silently lose data or falsely declare healthy.
  **Tester edge:** Restart with a nonempty spill file, partial recovery, interleaved new writes and rotation boundaries retain all unflushed records once.
  **Dependencies / validation:** AUD-011-001, AUD-011-022, AUD-011-025; V3, V4.
  **Acceptance:** Recovery is exercised through a connected trigger and every accepted audit record has a durable or explicitly recoverable state.

- [ ] AUD-011-031 [P1] Wire the full telemetry contract to behavior.
  **Obligations:** NFR-002, SC-001; T061, T062, T063; all metrics, span hierarchy, custom events and alerts in the telemetry contract.
  **Expected / actual / impact:** [Telemetry declarations](../../apps/agents/resource_allocation/telemetry.py#L91) and [event methods](../../apps/agents/resource_allocation/telemetry.py#L389) have no connected allocation callers. Several declared gauges are counters/histograms; event properties differ. Latency is logged but no allocation/status/cross-incident SLA-breach event is emitted.
  **Developer:** Own instrumentation in each pipeline/status/override/lifecycle stage and the telemetry registry. Connect all 29 metrics, all 10 events, the complete nested span trees, upstream correlation and current-state gauge semantics. Correct event properties and `record_confidence` recording into fulfilment rate. Configure the 10 authored alert rules and document how every additional metric can be alerted on.
  **Tester positive:** Extend [pipeline](../../tests/unit/test_resource_allocation_pipeline.py#L90), [endpoint](../../tests/unit/test_resource_allocation_endpoints.py#L17), and [audit](../../tests/unit/test_resource_allocation_audit.py#L31) test homes with in-memory metric/span exporters and a fake clock.
  **Tester negative:** Rejected handoffs must not count as successful plans; no-op exporter mode must not break processing; an alert cannot be accepted against a never-emitted series.
  **Tester edge:** Exact 5/15/30-second boundaries, partial/retried work, high queue depth and recovery emit correctly tagged metrics and events once.
  **Dependencies / validation:** AUD-011-001, AUD-011-019, AUD-011-020, AUD-011-021, AUD-011-029; V3, V6, V8.
  **Acceptance:** Test exporters observe the contract through real entrypoints, and later authorized monitoring checks show the intended series/alerts.

- [ ] AUD-011-032 [P1] Return truthful health and readiness contracts.
  **Obligations:** FR-035, FR-036; T057; CHK028; EC-07.
  **Expected / actual / impact:** [Health response](../../apps/agents/resource_allocation/agent.py#L287) is a list instead of the contract's named object, always calls the LLM healthy, omits plan/demand/queue counts, and infers Cosmos health from an audit tier initialized as healthy even without a client.
  **Developer:** Own cached dependency checks and response models. Report actual inventory freshness, LLM/data-store readiness, active plans, pending demands, queue depth/status and numeric audit tier/backlog. Distinguish genuine inability to process from safe degradation; apply bounded checks and connect hosting probes without restart loops during LLM-only failure.
  **Tester positive:** Extend [health tests](../../tests/unit/test_resource_allocation_endpoints.py#L131) with healthy injected dependencies and validate every named field.
  **Tester negative:** No queue, no initialized worker, or no inventory plus offline store must not appear healthy; LLM-only outage must remain degraded rather than falsely healthy/unhealthy.
  **Tester edge:** Audit-only buffering, stale cache, slow probes and backpressure preserve the specified response timing and appropriate status.
  **Dependencies / validation:** AUD-011-001, AUD-011-019, AUD-011-026, AUD-011-030, AUD-011-041; V3, V6, V8.
  **Acceptance:** Health reflects measured capabilities and contract shape, and cannot conceal an absent worker or dependency.

- [ ] AUD-011-033 [P1] Connect compliant infrastructure to the selected worker.
  **Obligations:** NFR-001, FR-031a, FR-035; T069; plan infrastructure/region/security gates.
  **Expected / actual / impact:** [Standalone module](../../infra/modules/resource-allocation.bicep#L63) declares the correct partitions and an identity, but is unreferenced by the selected deployment. Its [scaler](../../infra/modules/resource-allocation.bicep#L163) is HTTP rather than queue-depth; shared [Dockerfile](../../apps/agents/Dockerfile#L48) starts another service and omits the sample inventory. Identity declarations do not establish usable role grants or runtime configuration.
  **Developer:** Own deployment composition, image/startup selection, data-container access, queue/status routing, authenticated queue-depth scaling, matching ports/probes, identity roles and durable spill storage. Follow the loaded AVM-first/naming/tagging/policy instructions; obtain current governance constraints and any required raw-resource exception in a later authorized infrastructure session. Preserve AU persistence and the constitution's bounded model-hosting carve-out.
  **Tester positive:** Use the later authorized infrastructure workflow to validate the selected module and resulting worker/configuration; extend [integration tests](../../tests/integration/test_resource_allocation_service_bus.py#L20) for both message sources and correct identities.
  **Tester negative:** Missing identity permission, wrong image port, absent inventory/containers, or HTTP traffic with a growing message queue must be detected as readiness/scaling failures.
  **Tester edge:** Scale-out with 30 active incidents, scale-in during processing, restart with audit backlog and region constraints retain ownership and work.
  **Dependencies / validation:** AUD-011-001, AUD-011-004, AUD-011-013, AUD-011-030, AUD-011-032, AUD-011-041; V4, V8. No cloud check or build was performed here.
  **Acceptance:** A reviewed deployment path actually starts the authoritative worker with queue-based capacity, correct scoped stores and enforceable identity/access controls.

### Verification and Governance

- [ ] AUD-011-034 [P2] Replace assertion gaps in unit and contract coverage.
  **Obligations:** T006, T007, T008, T009, T010, T011, T012, T013, T014, T025, T026, T027, T030, T034, T039, T043, T047, T051.
  **Expected / actual / impact:** [Model tests](../../tests/unit/test_resource_allocation_models.py#L291) supply valid equations rather than reject invalid ones; [override tests](../../tests/unit/test_resource_allocation_endpoints.py#L17) never read stored plans; [replay tests](../../tests/contract/test_resource_allocation_reproducibility.py#L77) compare counts/scores. Advertised concurrency, negative/schema and state assertions are missing.
  **Developer:** Own test fixtures in the existing named unit/contract files, not parallel replacement suites. Use stateful stores that enforce ETags/partitions and assert durable effects, exact IDs, event fields and negative branches. Remove conditional assertions that can silently avoid the behavior. Ensure sample-file absence fails rather than passes. Record future red/green evidence; do not claim test-first history retroactively.
  **Tester positive:** Trace every original test obligation to an assertion and execute V1-V3 after the functional fixes; compare nonempty expected values.
  **Tester negative:** Apply controlled wrong-type, no-op-override, missing-audit and constant-hash mutations locally in a later authorized test session; the corresponding tests must fail.
  **Tester edge:** Include 0/0.05/0.1/1 km, antipodes, invalid config, exact thresholds, concurrent dedup/OCC, ties and reserved resources with independent fixtures.
  **Dependencies / validation:** Relevant AUD-011-001 through AUD-011-032 fixes, specifically the obligations each assertion covers; V1, V2, V3.
  **Acceptance:** All promised cases have nonvacuous assertions, and reports distinguish authored tests, passing runs and historical test-first evidence.

- [ ] AUD-011-035 [P2] Implement actual storage and messaging integration tests.
  **Obligations:** T064, T065; FR-001, FR-003, FR-015, FR-027, FR-031a.
  **Expected / actual / impact:** [Cosmos tests](../../tests/integration/test_resource_allocation_cosmos.py#L20) and [Service Bus tests](../../tests/integration/test_resource_allocation_service_bus.py#L20) unconditionally skip in every body. Setting their environment variables cannot make them validate integration.
  **Developer:** Replace those stub bodies with real boundary exercises; use isolated approved emulators/test accounts and deterministic cleanup of test-owned data. Cover create/read, append-only records, ETag conflict, status transitions, tenant partitions, actual serialization, settlement, poison handling and consumer lifecycle. Reconcile configuration names rather than leaving mismatched skip gates.
  **Tester positive:** Under explicitly approved prerequisites, run V4 and assert both sources traverse the real consumer and actual plan/audit records are read back.
  **Tester negative:** Verify 412/409, storage outage, malformed messages, forbidden mutation and wrong-tenant reads fail as specified.
  **Tester edge:** Concurrent counter creation, lost acknowledgement, restart/redelivery and recovery run without unconditional skips or duplicate side effects.
  **Dependencies / validation:** AUD-011-001, AUD-011-004, AUD-011-007, AUD-011-013, AUD-011-015, AUD-011-022, AUD-011-030; V4.
  **Acceptance:** Test runs exercise integration and report explicit environment skips only when prerequisites truly are absent.

- [ ] AUD-011-036 [P2] Make scenario fixtures demonstrate the intended behaviors.
  **Obligations:** T066, T067, T068; US1, US2, US3, US4, US6, US7, US8; plan scenario gate.
  **Expected / actual / impact:** [Flood tests](../../tests/simulation/test_flood_allocation_scenario.py#L106) check mostly existence/confidence. [Bushfire tests](../../tests/simulation/test_bushfire_allocation_scenario.py#L89) allow any assignment; fire fixtures lack the required `firefighting` capability. [Multi-incident fixtures](../../tests/simulation/test_multi_incident_scenario.py#L22) give the ambulance only one of two required capabilities, making the overlap assertion vacuous.
  **Developer:** Extend the existing three scenario files with matching capability/location fixtures and exact expected allocation/audit outcomes. Add cyclone/accessible-transport coverage in an existing appropriate scenario home or a clearly proposed new case. Exercise connected queues, approval-preserving transfer, true ties, rotation and isolated replay.
  **Tester positive:** Run flood, bushfire, cyclone/transport and two/three-incident fixtures with known expected resource IDs and counts; require nonempty contested assignments where intended.
  **Tester negative:** Wrong-type substitutes, missing fire resources, silent deficits, double ownership and missing audit stages must fail assertions.
  **Tester edge:** Equal-priority odd-sized pools, exhausted inventory, critical arrival after lower-tier approval, return after 12 hours and interleaved simulation/live work are covered.
  **Dependencies / validation:** AUD-011-005, AUD-011-008, AUD-011-009, AUD-011-010, AUD-011-011, AUD-011-012, AUD-011-018, AUD-011-022, AUD-011-029; V5.
  **Acceptance:** Scenario names correspond to asserted operational outcomes, not merely nonempty plan objects.

- [ ] AUD-011-037 [P2] Measure SLAs, concurrency, backpressure and recovery.
  **Obligations:** SC-001, NFR-001, NFR-002, FR-001, FR-035, FR-036; T046, T057, T061, T062, T069, T070; CHK010, CHK023, CHK028, CHK042.
  **Expected / actual / impact:** No reviewed allocation measurement establishes 5-second acknowledgement/status processing, 15-second allocation, 30-second cross-incident processing, 1-second health, or 30 concurrent plans. The nearby [delivery benchmark](../../tests/benchmark/test_pipeline_latency.py#L24) is not an allocation-load measurement.
  **Developer:** Extend the existing benchmark home with real allocation-entrypoint workloads, measured inventory/demand sizes, injected delays and clear queue/processing timestamps. Ratify absolute versus p95 SLAs and combined-plan budgets. Preserve completion with delay events when thresholds are exceeded, and define overload/backpressure behavior.
  **Tester positive:** Run V6 on documented hardware with at least 30 concurrently active incidents and representative resource/demand counts; retain p50/p95/p99 and raw result evidence.
  **Tester negative:** Inject slow LLM/store, consumer outage and 31-plus backlog; assert delay events, retained work, bounded memory and correct readiness rather than silent loss.
  **Tester edge:** Exact threshold boundaries, scale/restart, empty inventory and three-way analysis distinguish allocation, status, intake and health clocks.
  **Dependencies / validation:** AUD-011-001, AUD-011-015, AUD-011-026, AUD-011-031, AUD-011-032, AUD-011-033; V6.
  **Acceptance:** Scoped measured runs establish the ratified targets with workload/prerequisites/revision documented; no runtime guarantee is inferred from a constant or comment.

- [ ] AUD-011-038 [P2] Establish and measure the efficiency baseline.
  **Obligations:** SC-006; CHK025; research decision 11; HYP-036, HYP-037, HYP-038 only after their explicit preconditions.
  **Expected / actual / impact:** [SC-006](spec.md#L311) measures time-to-arrival and fulfilment, while [research](research.md#L220) calls 30% aspirational and measures time-to-assignment. Local hypothesis files are not measured results.
  **Developer:** Own the evaluation protocol and evidence capture under later authorization. Resolve the metric/target conflict, use paired manual/assisted exercises with identical scenario/inventory and defined clocks, and record uncertainty and adverse outcomes. Keep country-specific claims deferred until licensing, D-009 and cohort gates clear.
  **Tester positive:** Use at least three scenarios per disaster type per the research protocol; retain baseline and assisted timings, denominators, inventories, configuration and revision.
  **Tester negative:** An easier assisted inventory, missing arrival times, changed scenario or failed threshold must not be recorded as achieved uplift.
  **Tester edge:** Zero baseline fulfilment, partial allocations, outliers and missing observations have declared handling and confidence intervals.
  **Dependencies / validation:** AUD-011-036, AUD-011-037, AUD-011-041; V7, V9.
  **Acceptance:** The agreed efficiency measure has reproducible comparative evidence or is explicitly reported unmet/unverified; aspirational wording is not a pass.

- [ ] AUD-011-039 [P2] Obtain actual commander usability evidence.
  **Obligations:** SC-010; CHK026, CHK043; PER-025, PER-026.
  **Expected / actual / impact:** The [90% criterion](spec.md#L321) has no survey responses, sample-size protocol or authenticated participant evidence in the reviewed feature records. Authored persona status is not practitioner validation.
  **Developer:** Own a versioned 5-point clarity/priority-justification/decision-confidence survey, sampling rules, accessible presentation and privacy-preserving response capture. Define the rating threshold and denominator in advance. Keep reviewer/participant consent and approvals outside automated inference.
  **Tester positive:** Conduct a later authorized exercise with actual eligible commanders and blinded scenario outputs; calculate whether at least 90% meet the agreed criterion.
  **Tester negative:** Proxy-only participants, duplicates, nonresponses, missing rubric dimensions or cherry-picked responses must not silently increase the pass rate.
  **Tester edge:** Small samples, accessibility accommodations, mixed languages and withdrawn responses retain a transparent denominator and uncertainty statement.
  **Dependencies / validation:** AUD-011-027, AUD-011-036, AUD-011-041; V7, V9.
  **Acceptance:** A traceable human exercise record, not a generated assertion, establishes satisfaction or records the unmet target.

- [ ] AUD-011-040 [P2] Repair quickstart prerequisites and record a future rehearsal.
  **Obligations:** T003, T004, T024, T070; quickstart setup/run/health/handoff/test steps.
  **Expected / actual / impact:** [Quickstart](quickstart.md#L16) repeatedly changes into `apps/agents` but references root-relative tests/inventory, assumes startup launches a queue consumer, uses inconsistent connection names and a stock threshold of 20, and describes a different inventory size/location mix. The contract test it calls only constructs a model.
  **Developer:** Own quickstart documentation after the runtime contract is resolved. State a single working directory, actual dependency/dev-test installation, safe isolated credentials, exact consumed environment names, correct inventory path/count and a real message submission/readback workflow. Distinguish direct pipeline tests from integration. Do not retroactively check T070.
  **Tester positive:** In a clean approved environment, follow each revised instruction verbatim; capture selected interpreter, dependency versions, real health body, handoff, persisted plan, audit and exact command outcomes.
  **Tester negative:** Missing prerequisites, invalid inventory path, disconnected queue and absent store must visibly fail/degrade, not appear as a successful rehearsal.
  **Tester edge:** Windows paths, root versus agent-directory invocation, fallback-only mode and repeated runs must be explicit and reproducible.
  **Dependencies / validation:** AUD-011-001, AUD-011-025, AUD-011-032, AUD-011-033, AUD-011-035; V8.
  **Acceptance:** A new dated rehearsal record establishes which steps ran and passed; the original unchecked task is preserved until separately approved change control.

- [ ] AUD-011-041 [P2] Resolve contract conflicts and substantiate review/amendment claims.
  **Obligations:** All research/checklist/design gates assessed in sections 6-7; T004, T013, T017, T019, T031, T032, T040, T048, T069, T070; ASM-030, ASM-031, ASM-032, PER-025, PER-026, PER-027, HYP-009, HYP-036, HYP-037, HYP-038, SCP-028, SCP-029, SCP-030.
  **Expected / actual / impact:** The [plan gate claims](plan.md#L42), [generic readiness checkmarks](checklists/requirements.md#L7) and [amendments](spec.md#L324) exceed available evidence. The referenced HYP-009 stub is absent in the scoped filename search. Technical-persona references have relocated operational definitions; presence is not consultation.
  **Developer:** Own later governed specification/research/contract corrections, not unilateral implementation interpretation. Resolve UUID-versus-409 versioning; separate urgency/severity and immediate mapping; count/quantity/population proportionality; reservation/return rules; `add`/`remove` versus `add_resource`/`remove_resource`; commander role names; percentage units; health shape; SLA scope; stage-2 rejection/degradation; audit fields/order; and arrival-versus-assignment uplift. Reconcile stale constitutional section numbers with the current constitution and bounded model-hosting carve-out. Repair the HYP-009 evidence reference/stub under its owning change-control rules; retain untested country hypotheses.
  **Tester positive:** Review all coverage rows and the evidence-stub/persona contracts against the resulting governed artifacts and actual reviewer identities/dates.
  **Tester negative:** Missing SME/practitioner approval, proxy-only persona validation, unlicensed country data, unresolved D-009 or absent baseline cannot be promoted to validated/completed.
  **Tester edge:** Conflicting external references, renamed persona files and partially approved amendment cohorts remain explicitly scoped; recovery authority stays with spec 018 and warning authority with spec 008.
  **Dependencies / validation:** Human owner/architect and authorized operational reviewers; V9. This audit neither delegates consultation nor edits any original artifact.
  **Acceptance:** Each resolved policy has a consistent authoritative statement and evidence link; remaining unknowns stay visibly open without fabricated sign-off.

## 4. Requirement and Success-Criterion Coverage

Original requirements are [FRs](spec.md#L178), [NFRs](spec.md#L251), and [success criteria](spec.md#L311). Every ID has one row. IMPLEMENTED rows establish only the named source behavior, not runtime SLA or approval evidence.

| ID | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Stage 1](../../apps/agents/resource_allocation/pipeline.py#L162) checks source/target and dedup; no connected raw-message validation/consumer or measured acknowledgement. | AUD-011-001, AUD-011-006, AUD-011-037 |
| FR-002 | PARTIAL | [Stage 2](../../apps/agents/resource_allocation/pipeline.py#L232) fabricates recommendation data and tolerates unavailable assessment; no recommendation store lookup. | AUD-011-006 |
| FR-003 | PARTIAL | [TTL cache](../../apps/agents/resource_allocation/dedup.py#L35) and [discard audit](../../apps/agents/resource_allocation/pipeline.py#L194) exist; failed work is marked seen and keys lack tenant/replica coordination. | AUD-011-007 |
| FR-004 | PARTIAL | [Validation](../../apps/agents/resource_allocation/pipeline.py#L204) checks nonempty string, not incident-store existence/status. | AUD-011-006 |
| FR-005 | PARTIAL | [Transport extraction](../../apps/agents/resource_allocation/pipeline.py#L313) handles synthetic camelCase arrays; [producer payload](../../apps/agents/common/handoff_payloads.py#L17) is different and not adapted. | AUD-011-001, AUD-011-009 |
| FR-006 | PARTIAL | [Demand extraction](../../apps/agents/resource_allocation/pipeline.py#L349) and four-category models exist; structured source, quantities/location/urgency completeness is not preserved. | AUD-011-008, AUD-011-024 |
| FR-007 | PARTIAL | [Tier classifier](../../apps/agents/resource_allocation/priority.py#L61) and [queue order](../../apps/agents/resource_allocation/priority.py#L134) implement tier/urgency; actual category and independent hazard severity are absent. | AUD-011-008, AUD-011-010 |
| FR-008 | CONFLICT | [Mapping](../../apps/agents/resource_allocation/priority.py#L49) follows [research](research.md#L170), collapsing immediate and critical; FR text states a strict critical/immediate/high order. Tier 1 extraction exists. | AUD-011-009, AUD-011-041 |
| FR-009 | PARTIAL | [Stage 3](../../apps/agents/resource_allocation/pipeline.py#L275) sorts one handoff only; no persistent consolidated active-incident demand lifecycle. | AUD-011-010, AUD-011-020 |
| FR-010 | PARTIAL | [Inventory model](../../apps/agents/resource_allocation/models.py#L267) and [transition service](../../apps/agents/resource_allocation/inventory.py#L91) exist; ownership persistence, all-state loss, authorization and audit are incomplete. | AUD-011-004, AUD-011-016, AUD-011-017 |
| FR-011 | PARTIAL | [Scoring](../../apps/agents/resource_allocation/scoring.py#L68) has Haversine/floor/capability/factors; union-pool type enforcement, return window and valid positions are missing. | AUD-011-005, AUD-011-017, AUD-011-024 |
| FR-012 | PARTIAL | [Shortfalls](../../apps/agents/resource_allocation/matcher.py#L216) and valid-demand status updates exist; upstream omissions and [transport summary](../../apps/agents/resource_allocation/templates.py#L124) hide some deficits. | AUD-011-008, AUD-011-009, AUD-011-027 |
| FR-013 | PARTIAL | [Availability factors](../../apps/agents/resource_allocation/config.py#L150) exclude assigned status; no durable ownership or approval-backed cross-incident transfer workflow. | AUD-011-004, AUD-011-011, AUD-011-014 |
| FR-014 | PARTIAL | [Plan construction](../../apps/agents/resource_allocation/pipeline.py#L647) supplies most fields and proposed status, but input/summary correctness, durable save and live entrypoint are incomplete. | AUD-011-001, AUD-011-008, AUD-011-015, AUD-011-027 |
| FR-015 | CONFLICT | [OCC fallback](../../apps/agents/resource_allocation/versioning.py#L138) is unsafe; [supersession](../../apps/agents/resource_allocation/pipeline.py#L855) includes approved plans, conflicting with US5-AS4 and conditional immutability. | AUD-011-013, AUD-011-014, AUD-011-015, AUD-011-041 |
| FR-016 | PARTIAL | [Shared safety/fallback](../../apps/agents/common/llm_mixin.py#L64) is connected to legacy summaries; [summary context](../../apps/agents/resource_allocation/pipeline.py#L749) lacks facts, and MAF mode makes decisions with the model. | AUD-011-001, AUD-011-027, AUD-011-028 |
| FR-017 | IMPLEMENTED | [Travel estimator](../../apps/agents/resource_allocation/scoring.py#L129), [assignment construction](../../apps/agents/resource_allocation/matcher.py#L159) and [timelines](../../apps/agents/resource_allocation/pipeline.py#L802) calculate mobilisation plus configurable travel for valid inputs; [speed assertions](../../tests/unit/test_resource_allocation_scoring.py#L224) exist. | AUD-011-024 for boundary validation |
| FR-018 | PARTIAL | [Status handler](../../apps/agents/resource_allocation/agent.py#L178) applies some transitions; full signal, event time, same-status updates, durable state and routing are incomplete. | AUD-011-016, AUD-011-017 |
| FR-019 | PARTIAL | [Flag service](../../apps/agents/resource_allocation/inventory.py#L137) reads static hours/capacity; no live accumulation, mechanical reporting, clear-on-recovery or next-plan replacement. | AUD-011-018, AUD-011-021 |
| FR-020 | PARTIAL | [Utilisation](../../apps/agents/resource_allocation/inventory.py#L258) has aggregate totals/flags but not per-type/per-incident queries. | AUD-011-019 |
| FR-021 | PARTIAL | [Queue helper](../../apps/agents/resource_allocation/priority.py#L134) and [stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) lack connected multi-incident severity/proximity/time and quantified losses. | AUD-011-010, AUD-011-011 |
| FR-022 | PARTIAL | [Proportional helper](../../apps/agents/resource_allocation/priority.py#L178) is uncalled and measures quantity, not the research decision's unmet demand count or genuine tie conditions. | AUD-011-012, AUD-011-041 |
| FR-023 | MISSING | [Stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) leaves recommendation and allocation lists empty; no donor-plan/approval service found in the connected paths and relocation scope. | AUD-011-011 |
| FR-024 | PARTIAL | [Override endpoint](../../apps/agents/resource_allocation/agent.py#L382) validates action/justification and logs user text, but applies no action or verified identity. | AUD-011-002, AUD-011-003 |
| FR-025 | PARTIAL | [OverrideMetadata](../../apps/agents/resource_allocation/models.py#L199) exists and [audit uses create](../../apps/agents/resource_allocation/audit.py#L65); no linked override version or before/after assignment record is created. | AUD-011-002, AUD-011-029 |
| FR-026 | PARTIAL | [Generated plans](../../apps/agents/resource_allocation/pipeline.py#L647) default proposed and physical dispatch is absent; approval does not function, approved plans are auto-superseded, and summary says dispatched. | AUD-011-002, AUD-011-014, AUD-011-027 |
| FR-027 | PARTIAL | [Plan scope](../../apps/agents/resource_allocation/pipeline.py#L91) propagates tenant labels; shared inventory, local counters/dedup and live-only status audit do not enforce isolation. | AUD-011-022 |
| FR-028 | PARTIAL | [Tie ordering](../../apps/agents/resource_allocation/matcher.py#L133) is deterministic for supplied candidates; generated demand/assignment IDs and clocks vary and full replay equivalence is not asserted. | AUD-011-023, AUD-011-034 |
| FR-029 | PARTIAL | [InputSnapshot construction](../../apps/agents/resource_allocation/pipeline.py#L696) exists; [hash](../../apps/agents/resource_allocation/inventory.py#L311) omits decision inputs and no full recoverable inventory snapshot is retained. | AUD-011-023 |
| FR-030 | PARTIAL | [Stage records](../../apps/agents/resource_allocation/pipeline.py#L922) omit multiple required event branches; enums alone do not emit audit. | AUD-011-028, AUD-011-029 |
| FR-031 | PARTIAL | [Decision model](../../apps/agents/resource_allocation/models.py#L348) and [writes](../../apps/agents/resource_allocation/pipeline.py#L922) lack required demands/assignments and populated scoring/exclusion/duration provenance. | AUD-011-024, AUD-011-029 |
| FR-031a | PARTIAL | [Three-tier write](../../apps/agents/resource_allocation/audit.py#L42) and [manual flush](../../apps/agents/resource_allocation/audit.py#L108) exist; scheduled ordered recovery, loss handling and transition auditing do not. | AUD-011-030, AUD-011-032 |
| FR-032 | MISSING | [AuditWriter](../../apps/agents/resource_allocation/audit.py#L26) is write/status only and [HTTP app](../../apps/agents/resource_allocation/agent.py#L266) exposes health/override only; no allocation audit filters found in named runtime searches. | AUD-011-029 |
| FR-033 | IMPLEMENTED | [Summary fallback](../../apps/agents/resource_allocation/pipeline.py#L749) and [confidence update](../../apps/agents/resource_allocation/pipeline.py#L683) preserve template_fallback and multiply base confidence by configured 0.8; shared mixin supports outages. | AUD-011-028 for missing event provenance; execution remains unverified |
| FR-034 | MISSING | [Inventory query](../../apps/agents/resource_allocation/pipeline.py#L531) has no store recovery/staleness policy; [age computation](../../apps/agents/resource_allocation/pipeline.py#L824) is metadata only. Searched the entire allocation package and connected adapters. | AUD-011-026 |
| FR-035 | PARTIAL | [Health](../../apps/agents/resource_allocation/agent.py#L287) lacks required fields and real checks and conflicts with the named-object contract. Timing unmeasured. | AUD-011-032, AUD-011-037 |
| FR-036 | PARTIAL | [LLM fallback](../../apps/agents/common/llm_mixin.py#L64) and audit buffering support some failures; version/store/input and recovery paths can raise, lose work or report false persistence. | AUD-011-001, AUD-011-007, AUD-011-015, AUD-011-026, AUD-011-030 |
| FR-037 | PARTIAL | [Shared validation](../../apps/agents/common/llm_mixin.py#L149) replaces unsafe text and labels safety_fallback; allocation does not persist the required failure audit/provenance. | AUD-011-028 |
| NFR-001 | PARTIAL | [Module scale](../../infra/modules/resource-allocation.bicep#L163) is HTTP-based and disconnected; no 30-plan workload result inspected. | AUD-011-001, AUD-011-033, AUD-011-037 |
| NFR-002 | PARTIAL | [29 metric declarations](../../apps/agents/resource_allocation/telemetry.py#L94) are not emitted by the allocation stages; alerts/traces and gauge semantics remain incomplete. | AUD-011-031 |
| SC-001 | UNVERIFIED | [Final duration log](../../apps/agents/resource_allocation/pipeline.py#L895) is not latency evidence; no full allocation/status/cross-incident measurements or breach-event assertions. | AUD-011-031, AUD-011-037 |
| SC-002 | PARTIAL | [Traceability fields](../../apps/agents/resource_allocation/pipeline.py#L712) echo IDs but do not prove existing input records; transport linkage is incomplete. | AUD-011-006, AUD-011-009, AUD-011-029 |
| SC-003 | PARTIAL | [Scorer](../../apps/agents/resource_allocation/scoring.py#L68) enforces all capabilities but not per-pair type in the union pool. A concrete wrong-subtype counterexample is described above. | AUD-011-005 |
| SC-004 | PARTIAL | [Stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) does not see existing incident demand/ownership; no 100% priority-compliance result is established. | AUD-011-010, AUD-011-011, AUD-011-036 |
| SC-005 | PARTIAL | [Transport path](../../apps/agents/resource_allocation/pipeline.py#L313) normalizes priorities locally but real producer intake, assignments/state/audit and simultaneous-request tests are incomplete. | AUD-011-009, AUD-011-036 |
| SC-006 | CONFLICT | [Research baseline](research.md#L220) uses aspirational time-to-assignment versus spec time-to-arrival; no paired exercise outcome is established by local evidence. | AUD-011-038, AUD-011-041 |
| SC-007 | PARTIAL | [Replay tests](../../tests/contract/test_resource_allocation_reproducibility.py#L77) compare counts/sorted scores, not exact assignment identities/rankings or changed-field snapshot sensitivity. | AUD-011-023, AUD-011-034 |
| SC-008 | PARTIAL | [Finalization](../../apps/agents/resource_allocation/pipeline.py#L895) does not reconcile stage records; [flush tests](../../tests/unit/test_resource_allocation_audit.py#L102) assert memory counts only. | AUD-011-029, AUD-011-030 |
| SC-009 | PARTIAL | [Store failure path](../../apps/agents/resource_allocation/pipeline.py#L836) suppresses write errors and dedup suppresses retriable work; outage drop-rate evidence is absent. | AUD-011-007, AUD-011-015, AUD-011-026, AUD-011-037 |
| SC-010 | UNVERIFIED | [Criterion](spec.md#L321) is stated, but no qualifying commander responses, sampling protocol or exercise approval exists in the reviewed local evidence. | AUD-011-039 |

## 5. Scenario, Edge, and Original Task Coverage

### Acceptance Scenarios

AS numbering follows each story's original list. Each row also identifies its original FR/SC intent so scenario-to-requirement tracing is explicit. All scenario test execution remains unverified.

| Scenario | Status | Original obligation and source/test evidence | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | FR-001, FR-002, FR-014; SC-001, SC-002. [Plan generation tests](../../tests/unit/test_resource_allocation_pipeline.py#L173) cover object fields; actual intake, references, storage and factual summary are incomplete. | AUD-011-001, AUD-011-006, AUD-011-008, AUD-011-015, AUD-011-027 |
| US1-AS2 | PARTIAL | FR-006, FR-007; SC-004. [Queue tests](../../tests/unit/test_resource_allocation_priority.py#L79) assert supplied tiers/urgency, not authoritative coordination tasks plus hazard severity. | AUD-011-008, AUD-011-010 |
| US1-AS3 | PARTIAL | FR-015; SC-002. [Version tests](../../tests/unit/test_resource_allocation_versioning.py#L16) are local; [supersession](../../apps/agents/resource_allocation/pipeline.py#L855) is unsafe under failure/concurrency. | AUD-011-013, AUD-011-014, AUD-011-015 |
| US1-AS4 | MISSING | FR-002, FR-030; SC-002, SC-008. [Retrieval](../../apps/agents/resource_allocation/pipeline.py#L232) does not reject missing recommendation/assessment; no required negative assertion found in pipeline tests. | AUD-011-006 |
| US2-AS1 | PARTIAL | FR-011, FR-017; SC-003. [Closest-resource test](../../tests/unit/test_resource_allocation_matcher.py#L61) covers one demand/two resources; three-of-five tankers and strict mixed-pool typing are untested. | AUD-011-005, AUD-011-034 |
| US2-AS2 | PARTIAL | FR-011, FR-012; SC-003. [Capability helper](../../apps/agents/resource_allocation/scoring.py#L38) and [shortfalls](../../apps/agents/resource_allocation/matcher.py#L216) exist; no end-to-end hazmat incompatibility assertion. | AUD-011-005, AUD-011-034 |
| US2-AS3 | IMPLEMENTED | FR-011; SC-003, SC-007. [Capability-count tie assertions](../../tests/unit/test_resource_allocation_matcher.py#L148) and [scored sort](../../apps/agents/resource_allocation/matcher.py#L133) support the researched binary-match tiebreak. | AUD-011-034 for wider tie-boundary coverage |
| US2-AS4 | PARTIAL | FR-013; SC-004. [Factors](../../apps/agents/resource_allocation/config.py#L150) exclude already-assigned status, but previous planning never sets ownership and no guarded transfer workflow exists. | AUD-011-004, AUD-011-011 |
| US3-AS1 | PARTIAL | FR-005, FR-008, FR-010, FR-011; SC-005. [Transport test](../../tests/unit/test_resource_allocation_pipeline.py#L126) asserts source_type only; no four-of-six selection/status proof and sample subtype mismatch. | AUD-011-004, AUD-011-009 |
| US3-AS2 | PARTIAL | FR-008; SC-005. [Priority mapping tests](../../tests/unit/test_resource_allocation_priority.py#L30) do not exercise simultaneous ambulance/bus requests through a global queue. | AUD-011-009, AUD-011-010 |
| US3-AS3 | PARTIAL | FR-012, FR-016; SC-005. Matcher computes deficit; [transport summary](../../apps/agents/resource_allocation/templates.py#L124) suppresses a partial four-bus shortage. | AUD-011-009, AUD-011-027 |
| US3-AS4 | PARTIAL | FR-005, FR-014; SC-002. [Plan traceability](../../apps/agents/resource_allocation/pipeline.py#L712) exists, but [assignment model](../../apps/agents/resource_allocation/models.py#L246) has no evacuation/requirement identity. | AUD-011-009 |
| US4-AS1 | MISSING | FR-009, FR-021; SC-004. [Single-handoff queue](../../apps/agents/resource_allocation/pipeline.py#L275) cannot allocate from both incidents by severity as required. | AUD-011-010, AUD-011-011 |
| US4-AS2 | MISSING | FR-013, FR-023; SC-004. [Trade-off stage](../../apps/agents/resource_allocation/pipeline.py#L603) does not inspect donors or produce approval-backed transfers/source-plan reductions. | AUD-011-011, AUD-011-014 |
| US4-AS3 | CONFLICT | FR-022; SC-004. Story uses population/proximity; [research](research.md#L152) chooses unmet-demand count; [unused helper](../../apps/agents/resource_allocation/priority.py#L178) uses quantity. | AUD-011-012, AUD-011-041 |
| US5-AS1 | MISSING | FR-024, FR-025; SC-008. [Override](../../apps/agents/resource_allocation/agent.py#L382) creates no changed version; [test](../../tests/unit/test_resource_allocation_endpoints.py#L17) checks only response. | AUD-011-002, AUD-011-003, AUD-011-029 |
| US5-AS2 | MISSING | FR-024, FR-026; SC-008. [Approve response](../../apps/agents/resource_allocation/agent.py#L382) never loads/transitions a plan. | AUD-011-002 |
| US5-AS3 | MISSING | FR-024; SC-008. [Cancel response](../../apps/agents/resource_allocation/agent.py#L382) does not cancel or call the [release helper](../../apps/agents/resource_allocation/inventory.py#L228). | AUD-011-002, AUD-011-020 |
| US5-AS4 | CONFLICT | FR-015, FR-026; SC-002. [Automatic supersession](../../apps/agents/resource_allocation/pipeline.py#L855) explicitly includes approved plans, contrary to this scenario. | AUD-011-014, AUD-011-041 |
| US6-AS1 | PARTIAL | FR-018; SC-001, SC-008. [Status handler](../../apps/agents/resource_allocation/agent.py#L178) performs some transitions/audit but lacks connected intake, source timestamp and proper scope. | AUD-011-016 |
| US6-AS2 | PARTIAL | FR-018, FR-019; SC-006. [Capacity/flags](../../apps/agents/resource_allocation/inventory.py#L249) exist but same-status updates, ratio units and recovery are not handled. | AUD-011-016, AUD-011-018, AUD-011-025 |
| US6-AS3 | PARTIAL | FR-019; SC-006. [Flag test](../../tests/unit/test_resource_allocation_inventory.py#L152) supplies 13 hours manually; no elapsed-time tracking or replacement recommendation. | AUD-011-018, AUD-011-021 |
| US6-AS4 | PARTIAL | FR-020; SC-006. [Aggregate query](../../apps/agents/resource_allocation/inventory.py#L258) omits type/incident grouping and detailed flagged-resource outputs. | AUD-011-019 |
| US7-AS1 | PARTIAL | FR-027; SC-002. [Scope label](../../apps/agents/resource_allocation/pipeline.py#L91) exists but no cross-tenant storage/inventory boundary assertion is in [contracts](../../tests/contract/test_resource_allocation_reproducibility.py#L77). | AUD-011-022 |
| US7-AS2 | PARTIAL | FR-028, FR-029; SC-007. [Replay test](../../tests/contract/test_resource_allocation_reproducibility.py#L77) compares counts/sorted scores; complete inputs/identities are not preserved. | AUD-011-023 |
| US7-AS3 | PARTIAL | FR-027; SC-002, SC-008. Plan tenant exists; [assignment records](../../apps/agents/resource_allocation/models.py#L246) lack scope and [templates](../../apps/agents/resource_allocation/templates.py#L13) lack explicit simulation labeling. | AUD-011-022, AUD-011-027 |
| US8-AS1 | PARTIAL | FR-030, FR-031; SC-008. [Writes](../../apps/agents/resource_allocation/pipeline.py#L922) do not include all recommendation/assessment/input/scoring references for each processing step. | AUD-011-029 |
| US8-AS2 | PARTIAL | FR-024, FR-025, FR-031; SC-008. [Override audit](../../apps/agents/resource_allocation/agent.py#L400) includes body identity/justification but no actual original/modified assignment and no verified authority. | AUD-011-002, AUD-011-003, AUD-011-029 |
| US8-AS3 | MISSING | FR-021, FR-023, FR-031; SC-008. [Stage 6 audit](../../apps/agents/resource_allocation/pipeline.py#L633) is a generic count, not an actual source/destination/resource/priority/gap record. | AUD-011-011, AUD-011-029 |

### Edge Cases

EC IDs are report-local identifiers in the original [edge-case order](spec.md#L164).

| Edge | Status | Expected behavior and evidence | Follow-up |
| --- | --- | --- | --- |
| EC-01 | MISSING | Missing recommendation must reject/audit; [stage 2](../../apps/agents/resource_allocation/pipeline.py#L232) constructs it from payload instead. | AUD-011-006 |
| EC-02 | PARTIAL | Empty inventory yields [all-unmet matching](../../tests/unit/test_resource_allocation_matcher.py#L169), but no explicit empty-inventory audit/attention state and transport summary omits detailed deficits. | AUD-011-027, AUD-011-029 |
| EC-03 | PARTIAL | [Assigned status factor](../../apps/agents/resource_allocation/config.py#L150) and mutual-aid shortfall exist; persistent priority/ownership and source-plan protection do not. | AUD-011-004, AUD-011-011 |
| EC-04 | PARTIAL | [Dedup](../../apps/agents/resource_allocation/dedup.py#L35) discards repeats but also unfinished work, without tenant/replica guarantees. | AUD-011-007 |
| EC-05 | PARTIAL | [Plan scope](../../apps/agents/resource_allocation/pipeline.py#L91) is labelled, but isolation of inventory, status and nested records is unproven/incomplete. | AUD-011-022 |
| EC-06 | MISSING | Superseded evacuation reference must resolve current active version; [evacuation branch](../../apps/agents/resource_allocation/pipeline.py#L266) returns payload without lookup. | AUD-011-009 |
| EC-07 | PARTIAL | [Health](../../apps/agents/resource_allocation/agent.py#L287) exists; queue readiness/restart/redelivery behavior is disconnected and no failure-recovery run is established. | AUD-011-001, AUD-011-032, AUD-011-033, AUD-011-037 |
| EC-08 | PARTIAL | [Transition table](../../apps/agents/resource_allocation/inventory.py#L33) handles some unavailable transitions, but no assignment invalidation or affected-demand replan is connected. | AUD-011-017, AUD-011-021 |
| EC-09 | PARTIAL | [Proportional helper](../../apps/agents/resource_allocation/priority.py#L178) is uncalled and does not check severity/population or document commander-review ties. | AUD-011-012 |

### Original Task Coverage

Original checkboxes are preserved verbatim from [tasks.md](tasks.md#L26): 69 `[X]` and one `[ ]`. Each status assesses the whole original task, including its enumerated sub-obligations. A PARTIAL test task means assertions were authored but promised cases are absent; MISSING integration tasks have named files but no executable integration assertions. None is a claim about a test run.

| Task | Original | Status | Evidence | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Package export](../../apps/agents/resource_allocation/__init__.py#L3) exports ResourceAllocationAgent. | None for export; runtime is AUD-011-001 |
| T002 | [X] | IMPLEMENTED | [Agent dependencies](../../apps/agents/pyproject.toml#L15) declare tenacity, azure-cosmos and azure-servicebus. Installation is not claimed. | None |
| T003 | [X] | IMPLEMENTED | [Sample inventory](../../data/resource-inventories/sample-inventory.json#L1) represents all requested categories/subtypes with coordinates, capabilities, capacity and status. It is 23 items in Sydney-area locations, unlike quickstart prose. | AUD-011-040 for documentation mismatch |
| T004 | [X] | PARTIAL | [Config](../../apps/agents/resource_allocation/config.py#L15) has scoring/travel/lifecycle/audit defaults; no required Cosmos/Service Bus/auth fields and conflicting threshold/fixed-availability semantics. | AUD-011-025, AUD-011-041 |
| T005 | [X] | PARTIAL | [Models](../../apps/agents/resource_allocation/models.py#L29) provide enums/entities; [confidence derivation](../../apps/agents/resource_allocation/models.py#L338), quantity invariants and full field validation are incomplete. | AUD-011-024, AUD-011-029 |
| T006 | [X] | PARTIAL | [Model tests](../../tests/unit/test_resource_allocation_models.py#L40) check enums/helpers/valid examples; no invalid shortfall, required-field, confidence-model derivation or lifecycle rejection suite. | AUD-011-024, AUD-011-034 |
| T007 | [X] | PARTIAL | [Config tests](../../tests/unit/test_resource_allocation_config.py#L16) cover defaults and four overrides, not all settings/invalid type and range cases. | AUD-011-025, AUD-011-034 |
| T008 | [X] | PARTIAL | [Dedup tests](../../tests/unit/test_resource_allocation_dedup.py#L18) cover first/repeat/expiry/size; no concurrent or failure/retry coverage. | AUD-011-007, AUD-011-034 |
| T009 | [X] | PARTIAL | [Scoring tests](../../tests/unit/test_resource_allocation_scoring.py#L147) cover common factors and zero floor, not 0.05/0.1/1 km/full arithmetic or mixed-pool type rejection. | AUD-011-005, AUD-011-034 |
| T010 | [X] | PARTIAL | [Priority tests](../../tests/unit/test_resource_allocation_priority.py#L30) cover maps/tier/urgency/helper ratios; severity/proximity/time and genuine tie conditions are absent. | AUD-011-010, AUD-011-012, AUD-011-034 |
| T011 | [X] | PARTIAL | [Inventory tests](../../tests/unit/test_resource_allocation_inventory.py#L71) omit reservation-owner matching, bad location, mechanical and audit checks; one assertion rejects available-to-unavailable. | AUD-011-017, AUD-011-018, AUD-011-034 |
| T012 | [X] | PARTIAL | [Matcher tests](../../tests/unit/test_resource_allocation_matcher.py#L61) cover closest/partial/tie/empty, not strict mixed types or approved cross-call ownership protection. | AUD-011-004, AUD-011-005, AUD-011-034 |
| T013 | [X] | CONFLICT | [Tests](../../tests/unit/test_resource_allocation_versioning.py#L16) only use local counters; task requests UUID fallback contrary to [research's explicit prohibition](research.md#L132). | AUD-011-013, AUD-011-034, AUD-011-041 |
| T014 | [X] | PARTIAL | [Pipeline tests](../../tests/unit/test_resource_allocation_pipeline.py#L90) check empty ID/source/target and object presence, not actual missing records, durable stages or per-stage audit. | AUD-011-006, AUD-011-015, AUD-011-029, AUD-011-034 |
| T015 | [X] | IMPLEMENTED | [TTL cache](../../apps/agents/resource_allocation/dedup.py#L16) provides configurable first-seen checks and automatic eviction as locally specified. | AUD-011-007 for connected retry/concurrency safety |
| T016 | [X] | PARTIAL | [Scoring functions](../../apps/agents/resource_allocation/scoring.py#L21) exist; type helper is not used in scoring, reserved factor/window and invalid-position handling are incomplete. | AUD-011-005, AUD-011-017, AUD-011-024 |
| T017 | [X] | PARTIAL | [Priority services](../../apps/agents/resource_allocation/priority.py#L49) exist but unknown maps to moderate, global metadata is missing, and proportionality uses quantity. | AUD-011-010, AUD-011-012, AUD-011-041 |
| T018 | [X] | PARTIAL | [Inventory manager](../../apps/agents/resource_allocation/inventory.py#L44) loads and mutates local state; audit, ownership, exact location validation, per-type usage and connected release are absent. | AUD-011-004, AUD-011-016, AUD-011-017, AUD-011-019, AUD-011-020 |
| T019 | [X] | CONFLICT | [Versioning](../../apps/agents/resource_allocation/versioning.py#L48) attempts OCC but unsafe integer fallback implements neither research's 409 nor task's contradictory UUID/409 instructions. | AUD-011-013, AUD-011-041 |
| T020 | [X] | PARTIAL | [Four generators](../../apps/agents/resource_allocation/templates.py#L13) exist; connected template lacks actual plan context and transport deficits/approval wording. | AUD-011-027 |
| T021 | [X] | IMPLEMENTED | [Audit write](../../apps/agents/resource_allocation/audit.py#L65) uses create_item and serialized incident_scope_key with failure fallback. Canonical completeness/query obligations are separate. | AUD-011-029, AUD-011-030 for later obligations |
| T022 | [X] | PARTIAL | [Greedy matcher](../../apps/agents/resource_allocation/matcher.py#L39) assigns and explains shortfalls but omits pair-type rechecks and meaningful cross-incident ownership analysis. | AUD-011-004, AUD-011-005, AUD-011-011 |
| T023 | [X] | PARTIAL | [Nine-stage orchestrator](../../apps/agents/resource_allocation/pipeline.py#L91) exists; record validation, data retrieval, global demands, persistence and audit guarantees are incomplete. | AUD-011-006, AUD-011-008, AUD-011-010, AUD-011-014, AUD-011-015, AUD-011-029 |
| T024 | [X] | PARTIAL | [Agent composition](../../apps/agents/resource_allocation/agent.py#L112) and HTTP factory exist; startup has no store/consumer wiring and deployed/MAF paths are not equivalent. | AUD-011-001, AUD-011-033 |
| T025 | [X] | PARTIAL | [Schema tests](../../tests/contract/test_resource_allocation_plan_schema.py#L24) construct a fixture/round trip; no invalid contract or actual pipeline timeline consistency assertions. | AUD-011-024, AUD-011-034 |
| T026 | [X] | PARTIAL | [Handoff tests](../../tests/contract/test_resource_allocation_handoff.py#L11) assert assigned fixture values, not invalid boundaries, real producer serialization or tenant-to-plan propagation. | AUD-011-006, AUD-011-009, AUD-011-022, AUD-011-034 |
| T027 | [X] | PARTIAL | [Scored candidates](../../apps/agents/resource_allocation/matcher.py#L102) and [assignment builder](../../apps/agents/resource_allocation/matcher.py#L159) populate rationale/travel; tie annotation is only on the first tied candidate and mixed type selection remains possible. | AUD-011-005, AUD-011-034 |
| T028 | [X] | PARTIAL | [Sort](../../apps/agents/resource_allocation/matcher.py#L133) prefers capability count/ID and excludes status-assigned via score; actual plan ownership is never established and no approval-backed reallocation exists. | AUD-011-004, AUD-011-011 |
| T029 | [X] | IMPLEMENTED | [Matcher status/shortfall updates](../../apps/agents/resource_allocation/matcher.py#L84) retain every supplied valid demand with fulfilled/partial/unmet and mutual-aid text. Upstream extraction and transport rendering remain separate defects. | AUD-011-008, AUD-011-027 |
| T030 | [X] | PARTIAL | [Transport unit case](../../tests/unit/test_resource_allocation_pipeline.py#L126) asserts only source_type; promised ranking/status/deficit/references/superseded-plan assertions are absent. | AUD-011-009, AUD-011-034 |
| T031 | [X] | CONFLICT | [Extraction](../../apps/agents/resource_allocation/pipeline.py#L313) uses `transport_requirement`, as data model specifies, versus task's `source_type=evacuation`; real-payload and assignment traceability remain partial. | AUD-011-009, AUD-011-041 |
| T032 | [X] | IMPLEMENTED | [Evacuation mapping](../../apps/agents/resource_allocation/priority.py#L39) maps immediate/critical to critical and high to high, used by the transport path; strict spec wording still needs reconciliation. | AUD-011-041 |
| T033 | [X] | PARTIAL | [Capability inference](../../apps/agents/resource_allocation/pipeline.py#L516) exists, but wheelchair subtype mismatch, inventory assignment and transport_dispatched audit remain unresolved. | AUD-011-004, AUD-011-009 |
| T034 | [X] | PARTIAL | [Contention tests](../../tests/unit/test_resource_allocation_matcher.py#L184) check incident sets only, not severity, donor losses, approvals, true ties or three-way behavior. | AUD-011-011, AUD-011-012, AUD-011-034 |
| T035 | [X] | PARTIAL | [Stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) creates an object with commander flag but empty allocations/recommendations and no real multi-incident input. | AUD-011-010, AUD-011-011 |
| T036 | [X] | MISSING | [Matcher](../../apps/agents/resource_allocation/matcher.py#L252) has category contention only; no connected tier/severity/proximity/time cross-incident assignment or transfer audit was found after relocation checks. | AUD-011-010, AUD-011-011 |
| T037 | [X] | PARTIAL | [Relocated proportional helper](../../apps/agents/resource_allocation/priority.py#L178) exists, but is uncalled, quantity-based and not reflected in trade-offs or review flags. | AUD-011-012 |
| T038 | [X] | MISSING | [Status handler](../../apps/agents/resource_allocation/agent.py#L178) returns after audit without checking unmet demand or scheduling reallocation; runtime search found no other caller/trigger. | AUD-011-021 |
| T039 | [X] | PARTIAL | [Endpoint tests](../../tests/unit/test_resource_allocation_endpoints.py#L17) check response success, not modifications, immutable history, resource release or protected approval. | AUD-011-002, AUD-011-014, AUD-011-034 |
| T040 | [X] | PARTIAL | [HTTP override](../../apps/agents/resource_allocation/agent.py#L382) exists but omits auth, plan/action-detail validation, actual new-plan response fields and required state errors. | AUD-011-002, AUD-011-003, AUD-011-041 |
| T041 | [X] | MISSING | No override service occurs in the complete [pipeline](../../apps/agents/resource_allocation/pipeline.py#L62); the handler only records a claim. Related MAF/dispatcher paths do not implement it. | AUD-011-002, AUD-011-014, AUD-011-020 |
| T042 | [X] | PARTIAL | [Override record](../../apps/agents/resource_allocation/agent.py#L400) has user/role/justification but no actual before/after assignment, valid scope or authorized subject. | AUD-011-002, AUD-011-003, AUD-011-029 |
| T043 | [X] | PARTIAL | [Inventory assertions](../../tests/unit/test_resource_allocation_inventory.py#L71) cover helper transitions/flags, not full signals, capacity updates and per-transition audit fields. | AUD-011-016, AUD-011-018, AUD-011-034 |
| T044 | [X] | PARTIAL | [Status processing](../../apps/agents/resource_allocation/agent.py#L178) mutates on valid transition, but ignores timestamp/tenant, misses same-state updates and hardcodes audit scope. | AUD-011-016 |
| T045 | [X] | PARTIAL | [Capacity/flag methods](../../apps/agents/resource_allocation/inventory.py#L137) exist in combined form; elapsed deployment, mechanical input, flag clearing and per-incident utilisation are absent. | AUD-011-018, AUD-011-019 |
| T046 | [X] | MISSING | Only the [status method definition](../../apps/agents/resource_allocation/agent.py#L178) was found in tracked runtime callers; no message subscription, availability-trigger wiring or status SLA enforcement. | AUD-011-001, AUD-011-016, AUD-011-021, AUD-011-037 |
| T047 | [X] | PARTIAL | [Replay contract](../../tests/contract/test_resource_allocation_reproducibility.py#L77) checks counts/sorted scores/hash shape, not identity/ranking equality or live-versus-simulation effects. | AUD-011-022, AUD-011-023, AUD-011-034 |
| T048 | [X] | PARTIAL | [Plan scope propagation](../../apps/agents/resource_allocation/pipeline.py#L91) exists; inventory isolation, local key scoping and nested-record tenant identity do not. | AUD-011-022 |
| T049 | [X] | PARTIAL | [Shared mixin default](../../apps/agents/common/llm_mixin.py#L74) is temperature 0; [snapshot](../../apps/agents/resource_allocation/pipeline.py#L696) lacks replay-complete inputs and stable assignment identifiers. | AUD-011-023 |
| T050 | [X] | PARTIAL | [Plan construction](../../apps/agents/resource_allocation/pipeline.py#L647) sets four-hour expiry; no executing expiry/release/audit worker or active/expired counts. [Test](../../tests/unit/test_resource_allocation_pipeline.py#L173) checks only the timestamp delta. | AUD-011-019, AUD-011-020 |
| T051 | [X] | PARTIAL | [Audit tests](../../tests/unit/test_resource_allocation_audit.py#L31) check mocks/buffer counts; file contents, chronological replay, annotations, all event types and reconciliation are not asserted. | AUD-011-029, AUD-011-030, AUD-011-034 |
| T052 | [X] | IMPLEMENTED | [Bounded deque/write fallback](../../apps/agents/resource_allocation/audit.py#L29) and [buffer timestamp wrapper](../../apps/agents/resource_allocation/audit.py#L74) implement the memory tier locally. | AUD-011-030 for recovery/loss guarantees |
| T053 | [X] | PARTIAL | [JSONL spill](../../apps/agents/resource_allocation/audit.py#L84) exists; no rotation/size management or reliable handling of failed file writes. | AUD-011-030 |
| T054 | [X] | PARTIAL | [Flush helper](../../apps/agents/resource_allocation/audit.py#L108) exists under another name, but is not scheduled/recovery-triggered and does not guarantee chronology or idempotent replay. | AUD-011-030 |
| T055 | [X] | PARTIAL | [Audit helper](../../apps/agents/resource_allocation/pipeline.py#L922) emits some stages; transport/exclusions/expiry/degradation/safety and actual overrides/reallocation are incomplete. | AUD-011-009, AUD-011-020, AUD-011-028, AUD-011-029 |
| T056 | [X] | PARTIAL | [Finalization](../../apps/agents/resource_allocation/pipeline.py#L895) writes one final record without reconciliation/discrepancy detection/degradation transitions; health tier is incomplete. | AUD-011-029, AUD-011-030, AUD-011-032 |
| T057 | [X] | PARTIAL | [Health](../../apps/agents/resource_allocation/agent.py#L287) is structurally different, incomplete and optimistic about dependencies; no timing evidence. | AUD-011-032, AUD-011-037 |
| T058 | [X] | IMPLEMENTED | [Summary fallback](../../apps/agents/resource_allocation/pipeline.py#L749) uses preapproved template text and [generation](../../apps/agents/resource_allocation/pipeline.py#L683) applies the configured 0.8 penalty. | AUD-011-027, AUD-011-028 for content/provenance |
| T059 | [X] | MISSING | [Stage 4](../../apps/agents/resource_allocation/pipeline.py#L531) and [staleness helper](../../apps/agents/resource_allocation/pipeline.py#L824) do not implement last-known-good policy, stale confidence or beyond-window degradation. | AUD-011-026 |
| T060 | [X] | PARTIAL | [Shared validator call](../../apps/agents/common/llm_mixin.py#L149) replaces unsafe outputs; no allocation content_safety_failure decision event. | AUD-011-028 |
| T061 | [X] | MISSING | [Tracer helper](../../apps/agents/resource_allocation/telemetry.py#L43) is authored, but no allocation-stage/status root or child instrumentation/correlation is connected in the named search scope. | AUD-011-031 |
| T062 | [X] | MISSING | [Metric declarations](../../apps/agents/resource_allocation/telemetry.py#L94) exist but are not emitted by the allocation runtime; declaration alone does not fulfil the task. | AUD-011-031 |
| T063 | [X] | MISSING | [Event emitter](../../apps/agents/resource_allocation/telemetry.py#L389) is uncalled and event property sets differ from contract. | AUD-011-031 |
| T064 | [X] | MISSING | [Cosmos test bodies](../../tests/integration/test_resource_allocation_cosmos.py#L20) unconditionally skip; no persistence, OCC, lifecycle or partition assertions. | AUD-011-035 |
| T065 | [X] | MISSING | [Service Bus test bodies](../../tests/integration/test_resource_allocation_service_bus.py#L20) unconditionally skip; no serialization/settlement/lifecycle assertions. | AUD-011-035 |
| T066 | [X] | PARTIAL | [Flood tests](../../tests/simulation/test_flood_allocation_scenario.py#L106) assert plan/nonempty assignments/confidence, not extraction priority/proximity/shortfall/audit completeness. | AUD-011-036 |
| T067 | [X] | PARTIAL | [Bushfire tests](../../tests/simulation/test_bushfire_allocation_scenario.py#L89) only need some assignment; fire capability fixtures, rotation and real summary assertions are absent. | AUD-011-036 |
| T068 | [X] | PARTIAL | [Multi-incident tests](../../tests/simulation/test_multi_incident_scenario.py#L62) omit tiebreak/trade-off/proportional/approval assertions and allow vacuous no-overlap. | AUD-011-036 |
| T069 | [X] | PARTIAL | [Module](../../infra/modules/resource-allocation.bicep#L63) authors containers/queue/identity but is not wired; HTTP scaler, image/startup/port/config mismatch and policy/runtime proof remain. | AUD-011-001, AUD-011-033 |
| T070 | [ ] | UNVERIFIED | [Quickstart](quickstart.md#L1) is an instruction artifact, not an execution record; no rehearsal was run and its commands/assumptions are inconsistent with source. | AUD-011-040 |

## 6. Clarifications, Amendments, and Associated Contracts

### Clarification Decisions

CL IDs follow the five questions in the [first session](spec.md#L10), then eight in [pass 2](spec.md#L18).

| Decision | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| CL-01 | IMPLEMENTED | Four resource categories/subtypes are represented by [models](../../apps/agents/resource_allocation/models.py#L81) and [sample inventory](../../data/resource-inventories/sample-inventory.json#L1). | AUD-011-024 for validation/units |
| CL-02 | PARTIAL | [Greedy scoring](../../apps/agents/resource_allocation/matcher.py#L39) exists, but strict pair eligibility and active ownership are not enforced. Linear programming remains out of scope. | AUD-011-004, AUD-011-005 |
| CL-03 | PARTIAL | [Stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) lacks connected four-level comparison and quantified losses. | AUD-011-010, AUD-011-011 |
| CL-04 | UNVERIFIED | 15/5/30-second targets are authored; [duration log](../../apps/agents/resource_allocation/pipeline.py#L895) is not a measured pass. | AUD-011-037 |
| CL-05 | PARTIAL | [Three tiers](../../apps/agents/resource_allocation/audit.py#L42) exist; required audit fields, connected recovery and durability are incomplete. | AUD-011-029, AUD-011-030 |
| CL-06 | PARTIAL | [State machine](../../apps/agents/resource_allocation/inventory.py#L33) exists with unavailable/reservation/authorization/audit gaps. | AUD-011-016, AUD-011-017 |
| CL-07 | IMPLEMENTED | [Binary all-capabilities match](../../apps/agents/resource_allocation/scoring.py#L38) and [tests](../../tests/unit/test_resource_allocation_scoring.py#L69) support the stated MVP algorithm. | AUD-011-005 for independent type safeguard |
| CL-08 | IMPLEMENTED | [Haversine](../../apps/agents/resource_allocation/scoring.py#L21) and [distance tests](../../tests/unit/test_resource_allocation_scoring.py#L34) implement straight-line distance; road optimization is not required. | AUD-011-024 for invalid-position boundaries |
| CL-09 | PARTIAL | [Versioning](../../apps/agents/resource_allocation/versioning.py#L48) preserves ID format but bypasses safe reservation on exhaustion. | AUD-011-013 |
| CL-10 | PARTIAL | [Health](../../apps/agents/resource_allocation/agent.py#L287) omits active/pending/queue counts and truthful dependency state. | AUD-011-032 |
| CL-11 | PARTIAL | [Metrics registry](../../apps/agents/resource_allocation/telemetry.py#L94) contains names but connected emissions/alerts are missing. | AUD-011-031 |
| CL-12 | PARTIAL | [Legacy mixin](../../apps/agents/common/llm_mixin.py#L64) gives rationale-only fallback with 0.8 penalty; [MAF mode](../../apps/agents/maf_runtime/agents/_factory.py#L267) instead generates the plan object. | AUD-011-001, AUD-011-027, AUD-011-028 |
| CL-13 | PARTIAL | [Matcher](../../apps/agents/resource_allocation/matcher.py#L84) retains valid supplied demands; extraction and transport-summary losses remain. | AUD-011-008, AUD-011-027 |

### Numbered Amendment Obligations

These appended obligations are assessed separately from core feature delivery. Country hypotheses remain deferred, not failed core-MVP requirements.

| ID | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| ASM-030 | IMPLEMENTED | [AU-v1/deferred-country statement](spec.md#L328) is authored and consistent with the explicitly deferred local evidence. No deployed-country compliance is claimed. | AUD-011-041 for prerequisite/approval provenance |
| ASM-031 | UNVERIFIED | [Consultation requirement](spec.md#L329) names logistics, operations and resilience actors. [Operational persona definition](../../.github/agents/operational/logistics-officer.agent.md#L1) relocation is verified by filenames, not consultation receipts. | AUD-011-041 |
| ASM-032 | PARTIAL | [Convention declaration](spec.md#L330) cites the [persona schema](../027-spec-hardening/contracts/persona-profile.md#L5); numbered IDs exist but profile/validation evidence is not co-located or established by cross-reference alone. | AUD-011-041 |
| PER-025 | UNVERIFIED | [Validated assertion](spec.md#L336) is a cross-reference, not a dated named SME/practitioner record satisfying the [schema](../027-spec-hardening/contracts/persona-profile.md#L33). | AUD-011-039, AUD-011-041 |
| PER-026 | UNVERIFIED | [Actor-catalogue assertion](spec.md#L337) does not establish validation or technical/operational relocation consistency. | AUD-011-041 |
| PER-027 | IMPLEMENTED | [Non-AU placeholder](spec.md#L338) explicitly retains D-009 and SME prerequisites. No country validation is claimed. | AUD-011-041 before any promotion |
| HYP-009 | MISSING | [Hypothesis](spec.md#L344) references `specs/028-capstone-alignment/evidence/HYP-HYP-009.md`; exact and nearby HYP*009* searches in feature 028 evidence and local evidence found no stub. Rubric uplift and consultation are also unverified. | AUD-011-041 |
| SCP-028 | IMPLEMENTED | [Country deferral](spec.md#L350) explicitly retains D-009, regulatory/data-sharing gates and named actor sign-off; no implementation of deferred country capabilities is required now. | AUD-011-041 before scope promotion |
| SCP-029 | IMPLEMENTED | [Non-negotiable boundary](spec.md#L351) is authored; no constitution amendment was made by this feature review. Plan gate wording predates the current constitution. | AUD-011-041 for reference reconciliation |
| SCP-030 | IMPLEMENTED | [Authority deferral](spec.md#L352) names governed arbitration, spec 018 recovery and spec 008 communications ownership. | AUD-011-041 for any future dispute |
| HYP-036 | UNVERIFIED | [PH evidence](evidence/HYP-036.md#L1) meets the authored six-heading stub structure and explicitly says Not tested; carrier licensing, exercise pack and D-009 are preconditions, not established facts. | AUD-011-038, AUD-011-041 |
| HYP-037 | UNVERIFIED | [JP evidence](evidence/HYP-037.md#L1) is a complete authored Not tested stub; licensed networks, exercise pack and D-009 remain prerequisites. | AUD-011-038, AUD-011-041 |
| HYP-038 | UNVERIFIED | [BD evidence](evidence/HYP-038.md#L1) is a complete authored Not tested stub; river/road licensing, exercise pack and D-009 are unverified. | AUD-011-038, AUD-011-041 |

The unnumbered [feature-028 recovery cross-reference](spec.md#L355) is IMPLEMENTED as an authored deferral to spec 018, not implementation or approval of recovery behavior. The [current constitution](../../.specify/memory/constitution.md#L1) changes section numbering and permits only a bounded, approved model-hosting carve-out; it does not lift AU persistence requirements. The [RAG ADR](../../docs/decisions/036-foundry-rag-grounding/05-rag-optout-logistics-transactional.md#L1) has an authored Accepted/approver statement, but no external sign-off or actual upstream grounding was established in this audit. It does not supersede algorithmic matching or commander approval. The legacy messaging mechanism is explicitly **SUPERSEDED** in [common/handoffs.py:1](../../apps/agents/common/handoffs.py#L1) by MAF executors, but the functional obligations of spec 011 are not thereby retired; the replacement paths were inspected and remain incomplete.

### Research and Contract Reconciliation

| Input obligation | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- |
| Research 1: weights/floor | PARTIAL | [Decision](research.md#L9) is implemented for defaults in [scoring](../../apps/agents/resource_allocation/scoring.py#L68); configurable zero/negative floor remains unsafe. | AUD-011-005, AUD-011-025 |
| Research 2: availability/static-dynamic boundary | CONFLICT | [Step factor](research.md#L26) replaces decay, but FR-011 still has return-window eligibility; dynamic intake/persistence is disconnected. | AUD-011-001, AUD-011-017, AUD-011-041 |
| Research 3: travel/mobilisation | IMPLEMENTED | [Travel defaults](research.md#L43) match [estimator](../../apps/agents/resource_allocation/scoring.py#L129) and tests for valid inputs. | AUD-011-024, AUD-011-025 for boundaries |
| Research 4: confidence stacking | PARTIAL | [Penalty table](research.md#L68) has base and stale/partial/fallback rules; [generation](../../apps/agents/resource_allocation/pipeline.py#L647) applies only fallback. | AUD-011-026 |
| Research 5: lifecycle/releases/reallocation | PARTIAL | [Decision](research.md#L94) has complete intent; [release helper](../../apps/agents/resource_allocation/inventory.py#L228) is uncalled and queue lifecycle is absent. | AUD-011-010, AUD-011-020, AUD-011-021 |
| Research 6: expiry | PARTIAL | [Decision](research.md#L111) is represented by a timestamp only; no executing expiry/release/audit path. | AUD-011-020 |
| Research 7: OCC/409, no UUID | CONFLICT | [Decision](research.md#L132) conflicts with T013/T019/plan fallback instructions and [unsafe integer fallback](../../apps/agents/resource_allocation/versioning.py#L138). | AUD-011-013, AUD-011-041 |
| Research 8: same-score/true-tie rules | PARTIAL | [Decision](research.md#L152): same-score sorting exists; unmet-count proportionality is not wired and helper uses quantity. | AUD-011-005, AUD-011-012 |
| Research 9: normalization/unknown | CONFLICT | [Decision](research.md#L170) requires unknown->low plus warning; [function](../../apps/agents/resource_allocation/priority.py#L49) returns moderate silently. Strict immediate order also needs ratification. | AUD-011-010, AUD-011-041 |
| Research 10: own-incident reservations | PARTIAL | [Decision](research.md#L201) allows reserved incident eligibility; [scoring factor](../../apps/agents/resource_allocation/config.py#L150) excludes all reserved resources. | AUD-011-017 |
| Research 11: efficiency methodology | CONFLICT | [Aspirational assignment-time measure](research.md#L220) does not satisfy the original arrival-time target or provide execution evidence. | AUD-011-038, AUD-011-041 |
| Research 12: role authentication | MISSING | [JWT requirement](research.md#L239) is not enforced at the [override endpoint](../../apps/agents/resource_allocation/agent.py#L382); source-scoped auth/ingress composition was checked. | AUD-011-003 |
| Pipeline stages 1 and 2 | PARTIAL | [Stage contract](contracts/allocation-pipeline.md#L17) is contradicted by incomplete input/store validation and missing transport version lookup. | AUD-011-001, AUD-011-006, AUD-011-009 |
| Pipeline stages 3, 4 and 5 | PARTIAL | [Stage implementations](../../apps/agents/resource_allocation/pipeline.py#L275) have local ordering/matching/shortfalls, but incorrect source normalization, cross-demand eligibility and ownership. | AUD-011-004, AUD-011-005, AUD-011-008, AUD-011-010 |
| Pipeline stage 6 | PARTIAL | [Stage](../../apps/agents/resource_allocation/pipeline.py#L603) constructs an empty trade-off shell, not cross-incident allocation. | AUD-011-011, AUD-011-012 |
| Pipeline stages 7, 8 and 9 | PARTIAL | [Plan build/persist/finalize](../../apps/agents/resource_allocation/pipeline.py#L647) misses truthful summaries, safe commit and reconciliation. | AUD-011-013, AUD-011-014, AUD-011-015, AUD-011-023, AUD-011-027, AUD-011-029 |
| Pipeline budgets/error table/status flow | PARTIAL | [Contract](contracts/allocation-pipeline.md#L1) defines behavior, not measured execution. Missing-record rejection, closed-incident release, superseded evacuation lookup, mid-plan OCC, retries and status signal routing remain gaps. | AUD-011-006, AUD-011-009, AUD-011-016, AUD-011-020, AUD-011-037 |
| Data model entities and relationships | PARTIAL | [Entity contract](data-model.md#L1) has handoff, plan, demands, assignments, inventory, audit and embedded types; [source models](../../apps/agents/resource_allocation/models.py#L139) mostly exist but omit invariants, snapshots/provenance and durable relationships. | AUD-011-023, AUD-011-024, AUD-011-029 |
| Health schema/status/codes | PARTIAL | [Contract](contracts/health-endpoint.md#L9) expects named checks and genuine processing-failure rules; [endpoint](../../apps/agents/resource_allocation/agent.py#L287) returns an incomplete optimistic list. | AUD-011-032 |
| Override schema/actions/errors | CONFLICT | [Contract](contracts/health-endpoint.md#L76) uses add/remove and trusted commander claims; task/code use add_resource/remove_resource and body role. No actual mutation or 404/409 path. | AUD-011-002, AUD-011-003, AUD-011-041 |

### Telemetry Contract Obligations

All rows below assess connected emission, not just declarations. The entire [telemetry contract](contracts/telemetry.md#L1) and [source registry/emitter](../../apps/agents/resource_allocation/telemetry.py#L91) were inspected. No allocation runtime imports/calls were found in the source search. All rows require AUD-011-031; runtime and alert measurements additionally require AUD-011-037/AUD-011-033.

| Obligation | Status | Assessment |
| --- | --- | --- |
| Processing metrics | MISSING | `allocation_latency`, `plan_count`, `handoff_intake_count`, `handoff_rejected_count`, `duplicate_discard_count`, `sla_breach_count`, `status_update_latency` are declared but not emitted from connected behavior. |
| Matching metrics | MISSING | `resource_matching_time`, `demand_fulfilment_rate`, `shortfall_count`, `resource_utilization_rate`, `unmet_demand_count` are unconnected. Required gauges are represented as histograms/counter; `record_confidence` writes to fulfilment rate. |
| Cross-incident metrics | MISSING | `cross_incident_conflicts`, `cross_incident_reallocation_count`, `cross_incident_analysis_latency` are declared but not emitted from actual cross-incident processing. |
| Override metrics | MISSING | `override_count`, `override_rate`, `plan_approval_latency` have no mutation-backed calls; override rate is a histogram rather than a current ratio. |
| Degradation metrics | MISSING | `fallback_mode_activations`, `content_safety_failures`, `audit_buffer_depth`, `audit_tier`, `degradation_events` do not reflect connected allocation events/current state. |
| Version/lifecycle metrics | MISSING | `plan_versions_per_incident`, `version_conflict_retries`, `active_plans_gauge`, `plan_expired_count`, `transport_dispatch_latency`, `handoff_success_rate` are declared but unconnected; current/max/average and ratio semantics are not supplied. |
| Handoff span tree and correlation | MISSING | No connected root, validate_handoff, retrieve_data/cosmos_read, identify_demands/normalise_priority, query_inventory/filter_eligible, match_resources/compute_score/greedy_assign, cross_incident_analysis/trade_off_analysis, generate_plan/assign_version/compute_timelines/llm_call-or-template_fallback/content_safety_check, persist_plan/cosmos_write or write_audit span tree. Parent handoff span/correlation is not forwarded by summary call. |
| Status span tree | MISSING | No connected process_status_update root, validate_transition, apply_status, check_operational_flags, trigger_reallocation or write_audit children. |
| Custom events | MISSING | HandoffReceived, PlanGenerated, ShortfallDetected, CrossIncidentConflict, ReallocationRecommended, OverrideApplied, PlanExpired, DegradationEvent, SLABreach, VersionConflict helpers are uncalled. Several property sets omit source_agent, version/demand_count, resolution, aggregate resource_count, age_hours, tier or pipeline_type required by the contract. |
| Alert: allocation SLA warning | MISSING | No connected allocation p95 >15,000ms for 5 minutes rule/series was found in the checked allocation module or deployment references. |
| Alert: sustained allocation SLA | MISSING | No connected allocation p95 >15,000ms for 15 minutes critical scale-out rule/series established. |
| Alert: cross-incident SLA | MISSING | No connected cross-incident p95 >30,000ms for 5 minutes warning rule/series established. |
| Alert: high shortfall | MISSING | No connected fulfilment ratio <0.5 for 15 minutes warning rule/series established. |
| Alert: LLM unavailable | MISSING | No connected >10 fallback activations in 5 minutes warning rule/series established. |
| Alert: audit degradation | MISSING | No connected tier 2/3 for 5 minutes critical rule/series established. |
| Alert: audit capacity | MISSING | No connected memory depth >8,000 critical rule/series established. |
| Alert: override rate | MISSING | No connected override ratio >0.5 for 30 minutes warning rule/series established. |
| Alert: no plans | MISSING | No connected zero plans for 10 minutes during an active incident rule/series established. |
| Alert: version churn | MISSING | No connected >10 versions per incident warning rule/series established. |

No assertion is made that unrelated shared alerts do not exist. The missing claim is specifically for these named allocation metrics/thresholds and their runtime linkage.

## 7. Review and Checklist Evidence Assessment

### Allocation Checklist: All 48 Obligations

All original [allocation checklist](checklists/allocation.md#L15) items are `[ ]`; [plan resolutions](plan.md#L163) are authored decisions, not evidence that runtime behavior or peer review passed. The evidence/status below assesses each question rather than copying its checkbox.

| Item | Original | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | [Research weights](research.md#L9) and [config](../../apps/agents/resource_allocation/config.py#L15) specify urgency weights; independent severity and tier-order enforcement remain incomplete. | AUD-011-010, AUD-011-025 |
| CHK002 | [ ] | CONFLICT | [Research step factor](research.md#L26) is explicit; FR-011 still requires return-window eligibility and estimated-return context absent from models. | AUD-011-017, AUD-011-041 |
| CHK003 | [ ] | IMPLEMENTED | [Research speeds](research.md#L43) and [travel estimator](../../apps/agents/resource_allocation/scoring.py#L129) define/use configurable defaults. | AUD-011-025 for validation |
| CHK004 | [ ] | PARTIAL | [Confidence formula](research.md#L68) is defined; [generation](../../apps/agents/resource_allocation/pipeline.py#L647) omits stale and partial penalties. | AUD-011-026 |
| CHK005 | [ ] | PARTIAL | [Lifecycle decision](research.md#L94) exists; [queue](../../apps/agents/resource_allocation/priority.py#L151) has no removal/close/reallocation lifecycle. | AUD-011-010, AUD-011-020 |
| CHK006 | [ ] | PARTIAL | [Audit container](../../infra/modules/resource-allocation.bicep#L82) omits TTL as designed; archival/capacity management and recoverable spill retention are absent. | AUD-011-030, AUD-011-033 |
| CHK007 | [ ] | PARTIAL | [Event contract](contracts/telemetry.md#L1) describes some changes, but no connected plan-status publication or real override state change exists. | AUD-011-002, AUD-011-031, AUD-011-041 |
| CHK008 | [ ] | PARTIAL | [Four-hour decision](research.md#L111) is authored; [plan test](../../tests/unit/test_resource_allocation_pipeline.py#L173) checks only expiry timestamp. | AUD-011-020 |
| CHK009 | [ ] | PARTIAL | [Plan OCC resolution](research.md#L132) does not solve inventory mutation between [scoring](../../apps/agents/resource_allocation/matcher.py#L102) and commit. | AUD-011-004, AUD-011-013 |
| CHK010 | [ ] | MISSING | [Pipeline entry](../../apps/agents/resource_allocation/pipeline.py#L91) and startup have no bounded consumer/backpressure control; no >30-plan handling policy in local design resolves it. | AUD-011-001, AUD-011-037, AUD-011-041 |
| CHK011 | [ ] | MISSING | [Status method](../../apps/agents/resource_allocation/agent.py#L178) does not invalidate/replan a previously approved assignment that becomes unavailable. | AUD-011-021 |
| CHK012 | [ ] | PARTIAL | [Templates](../../apps/agents/resource_allocation/templates.py#L13) give section examples but omit truthful context/partial transport deficits and agreed readability limits. | AUD-011-027, AUD-011-041 |
| CHK013 | [ ] | MISSING | No batching/sequential concurrency policy is defined or connected in [pipeline entry](../../apps/agents/resource_allocation/pipeline.py#L91); versioning alone does not decide it. | AUD-011-001, AUD-011-010, AUD-011-041 |
| CHK014 | [ ] | CONFLICT | [Research](research.md#L152) chooses unmet count; [helper](../../apps/agents/resource_allocation/priority.py#L178) uses quantity; story refers to population/proximity. | AUD-011-012, AUD-011-041 |
| CHK015 | [ ] | PARTIAL | [TradeOffAnalysis model](../../apps/agents/resource_allocation/models.py#L178) defines structure, but [stage 6](../../apps/agents/resource_allocation/pipeline.py#L603) leaves substantive lists empty. | AUD-011-011 |
| CHK016 | [ ] | PARTIAL | [Current constitution](../../.specify/memory/constitution.md#L37) defines AIIMS functions; templates/prompt merely request consistency and local docs do not bind a tested glossary/readability policy. | AUD-011-027, AUD-011-041 |
| CHK017 | [ ] | MISSING | [Status input](../../apps/agents/resource_allocation/agent.py#L178) has no mechanical-fault signal/threshold handling; existing flag list is not a reporting mechanism. | AUD-011-018 |
| CHK018 | [ ] | CONFLICT | [Research confidence](research.md#L68), staleness contract and FR-034 differ on beyond-window use; [config](../../apps/agents/resource_allocation/config.py#L78) lacks bounds. | AUD-011-025, AUD-011-026, AUD-011-041 |
| CHK019 | [ ] | PARTIAL | [Shared validator](../../apps/agents/common/content_safety.py#L108) specifies safety/length/keyword fallback; factual evidence is not supplied by allocation and validator degradation provenance is lost. | AUD-011-027, AUD-011-028 |
| CHK020 | [ ] | CONFLICT | [Research mapping](research.md#L170) is explicit and used; strict priority wording and the [MAF five-level prompt](../../apps/agents/maf_runtime/agents/resource_allocation.yaml#L12) still disagree. | AUD-011-001, AUD-011-010, AUD-011-041 |
| CHK021 | [ ] | PARTIAL | [Own-incident reservation filter](../../apps/agents/resource_allocation/inventory.py#L175) exists but [availability factor](../../apps/agents/resource_allocation/config.py#L150) removes it at scoring. | AUD-011-017 |
| CHK022 | [ ] | PARTIAL | [Trade-off flag](../../apps/agents/resource_allocation/pipeline.py#L623) requires approval in data only; no implemented common approval/transfer mechanism. | AUD-011-002, AUD-011-011 |
| CHK023 | [ ] | PARTIAL | [Pipeline budget contract](contracts/allocation-pipeline.md#L1) states 15/30-second branches, but actual stage timing/selection and absolute-versus-p95 semantics remain unresolved. | AUD-011-031, AUD-011-037, AUD-011-041 |
| CHK024 | [ ] | CONFLICT | [Canonical class](../../apps/agents/common/handoffs.py#L26) is located and explicitly deprecated for MAF; historical spec attributions do not describe the working replacement. | AUD-011-001, AUD-011-041 |
| CHK025 | [ ] | CONFLICT | [Baseline protocol](research.md#L220) is authored, with different clock/aspirational target than SC-006; no qualifying outcome is established. | AUD-011-038, AUD-011-041 |
| CHK026 | [ ] | UNVERIFIED | [SC-010](spec.md#L321) has a 5-point intent but no local sampling/response evidence to establish 90% satisfaction. | AUD-011-039 |
| CHK027 | [ ] | PARTIAL | [Telemetry contract](contracts/telemetry.md#L1) supplies 10 thresholds; source emissions and connected allocation alert definitions are absent in the inspected module/deployment paths. | AUD-011-031, AUD-011-033 |
| CHK028 | [ ] | PARTIAL | [Health contract](contracts/health-endpoint.md#L9) states normal-operation 1 second; degraded-bound bounds and actual timing are not established. | AUD-011-032, AUD-011-037, AUD-011-041 |
| CHK029 | [ ] | MISSING | [Transport retrieval](../../apps/agents/resource_allocation/pipeline.py#L266) never checks for latest active plan, including the no-successor case. | AUD-011-009 |
| CHK030 | [ ] | CONFLICT | Checklist premise that deployed/en_route can directly become available disagrees with the [data model](data-model.md#L1) and [transition table](../../apps/agents/resource_allocation/inventory.py#L33). Recall impact policy is absent. | AUD-011-016, AUD-011-017, AUD-011-041 |
| CHK031 | [ ] | MISSING | [Contention](../../apps/agents/resource_allocation/matcher.py#L252) has no shared conditional reservation for simultaneous transfer recommendations. | AUD-011-004, AUD-011-011 |
| CHK032 | [ ] | PARTIAL | [Closure decision](research.md#L94) exists; [validation](../../apps/agents/resource_allocation/pipeline.py#L162) does not read incident status and release remains uncalled. | AUD-011-006, AUD-011-020 |
| CHK033 | [ ] | MISSING | [Status handler](../../apps/agents/resource_allocation/agent.py#L178) does not trigger reallocation; no relocated runtime caller found. | AUD-011-021 |
| CHK034 | [ ] | PARTIAL | [Tests](../../tests/unit/test_resource_allocation_inventory.py#L71) check available-to-reserved, not full reservation lifecycle/scope/audit/assignment scoring. | AUD-011-017, AUD-011-034 |
| CHK035 | [ ] | IMPLEMENTED | [Default floor](../../apps/agents/resource_allocation/scoring.py#L95) and [co-location test](../../tests/unit/test_resource_allocation_scoring.py#L147) prevent default zero-distance infinity. | AUD-011-025, AUD-011-034 for configured/near-floor boundaries |
| CHK036 | [ ] | PARTIAL | [Location filter](../../apps/agents/resource_allocation/inventory.py#L219) accepts a single coordinate; [scorer](../../apps/agents/resource_allocation/scoring.py#L79) defaults the other to zero and does not validate ranges. | AUD-011-008, AUD-011-024 |
| CHK037 | [ ] | CONFLICT | [Research](research.md#L132) says bounded jitter then 409; [fallback](../../apps/agents/resource_allocation/versioning.py#L138) returns an unreserved number; tasks also mention UUID fallback. | AUD-011-013, AUD-011-041 |
| CHK038 | [ ] | IMPLEMENTED | [Bounded buffer](../../apps/agents/resource_allocation/audit.py#L29) defines 10,000 default capacity and file spill when full; recoverability is separate. | AUD-011-030 |
| CHK039 | [ ] | PARTIAL | [Transition validation](../../apps/agents/resource_allocation/inventory.py#L91) rejects/logs invalid transitions but does not create the required durable anomaly/trigger record. | AUD-011-016, AUD-011-017, AUD-011-029 |
| CHK040 | [ ] | MISSING | [Auth decision](research.md#L239) is not enforced in [override handler](../../apps/agents/resource_allocation/agent.py#L382). | AUD-011-003 |
| CHK041 | [ ] | PARTIAL | [Constitution non-negotiables](../../.specify/memory/constitution.md#L261) establish privacy/residency; local audit spill and plan handling lack an allocation-specific sensitivity/access/retention proof. Deployed encryption is unverified. | AUD-011-003, AUD-011-030, AUD-011-033, AUD-011-041 |
| CHK042 | [ ] | UNVERIFIED | [30-plan goal](plan.md#L26) does not bound inventory/demand size or demonstrate the matcher at representative scale. | AUD-011-037 |
| CHK043 | [ ] | PARTIAL | [Plain-language requirement](spec.md#L178) and templates exist; no tested readability/accessibility or multi-format acceptance protocol is established. | AUD-011-027, AUD-011-039, AUD-011-041 |
| CHK044 | [ ] | PARTIAL | [JSON loader](../../apps/agents/resource_allocation/inventory.py#L52) establishes static state and [status helper](../../apps/agents/resource_allocation/agent.py#L178) exists, but dynamic messaging/recovery linkage is absent. | AUD-011-001, AUD-011-016 |
| CHK045 | [ ] | CONFLICT | [Real transport entity](../../apps/agents/evacuation/models.py#L163) and [typed payload](../../apps/agents/common/handoff_payloads.py#L17) do not match the [consumer schema](../../apps/agents/resource_allocation/pipeline.py#L313); no adapter found. | AUD-011-009, AUD-011-041 |
| CHK046 | [ ] | PARTIAL | [Spec out-of-scope](spec.md#L289) excludes physical dispatch, and none was found; operational status signal source/authority is unspecified/unconnected and templates imply dispatched resources. | AUD-011-016, AUD-011-027, AUD-011-041 |
| CHK047 | [ ] | PARTIAL | Stories/FR/SC exist, but original [test assertions](../../tests/unit/test_resource_allocation_pipeline.py#L90) do not trace all behavior. This report supplies static mappings, not passing acceptance evidence. | AUD-011-034, AUD-011-036, AUD-011-041 |
| CHK048 | [ ] | PARTIAL | Original FR/SC/task IDs exist; acceptance scenarios lack globally explicit IDs. Report-local AS/EC IDs provide review tracing but original bidirectional test mapping is not established. | AUD-011-034, AUD-011-041 |

### Generic Requirements Checklist: All 16 Obligations

RQ IDs correspond to the original [generic checklist](checklists/requirements.md#L7) in order. Original `[x]` means authored pass claim, not verified outcome.

| Item | Original | Status | Assessment | Follow-up |
| --- | --- | --- | --- | --- |
| RQ-01 | [x] | CONFLICT | "No implementation details" conflicts with [spec requirements](spec.md#L178) explicitly naming the scoring formula, Cosmos, environment variables and endpoint. | AUD-011-041 |
| RQ-02 | [x] | IMPLEMENTED | [Stories](spec.md#L29) explain commander/life-safety value. This is document quality, not delivery. | None |
| RQ-03 | [x] | PARTIAL | User narratives are readable, but [technical requirements](spec.md#L178) and inconsistent domain terms are not consistently nontechnical. | AUD-011-027, AUD-011-041 |
| RQ-04 | [x] | IMPLEMENTED | [Specification](spec.md#L1) contains mandatory stories, requirements and measurable-outcome sections. | None |
| RQ-05 | [x] | IMPLEMENTED | No NEEDS CLARIFICATION placeholders remain in the specification; substantive conflicts still exist. | AUD-011-041 for conflicts, not missing markers |
| RQ-06 | [x] | CONFLICT | [Version, tie, threshold and baseline directions](research.md#L132) disagree with tasks/spec/code; blanket unambiguity is unsupported. | AUD-011-041 |
| RQ-07 | [x] | PARTIAL | [SC numeric targets](spec.md#L311) exist, but efficiency clock and survey/sample protocols are unresolved. | AUD-011-037, AUD-011-038, AUD-011-039 |
| RQ-08 | [x] | PARTIAL | Outcomes are mostly user-focused, but [SCs](spec.md#L311) depend on unresolved pipeline/reproducibility measurement conventions. | AUD-011-023, AUD-011-037, AUD-011-041 |
| RQ-09 | [x] | IMPLEMENTED | All eight stories have explicit acceptance lists: 29 scenarios in [spec.md](spec.md#L29). Source completeness differs. | AUD-011-034, AUD-011-036 for coverage |
| RQ-10 | [x] | IMPLEMENTED | Nine [edge cases](spec.md#L164) are identified as authored obligations. | See edge coverage |
| RQ-11 | [x] | PARTIAL | [Original scope](spec.md#L289) and [country deferrals](spec.md#L346) are explicit, but runtime replacement and amended recovery/actor references require reconciliation. | AUD-011-001, AUD-011-041 |
| RQ-12 | [x] | IMPLEMENTED | [Assumptions/dependencies](spec.md#L275) are listed; upstream contract compatibility and external preconditions are not proven by that list. | AUD-011-009, AUD-011-041 |
| RQ-13 | [x] | PARTIAL | [FRs](spec.md#L178) include cases beyond original acceptance tests, including audit query, staleness, concurrency and telemetry. | AUD-011-034, AUD-011-041 |
| RQ-14 | [x] | IMPLEMENTED | [Eight stories](spec.md#L29) cover primary business flows as narratives. They do not establish implemented workflows. | AUD-011-036 |
| RQ-15 | [x] | UNVERIFIED | "Feature meets measurable outcomes" has no associated execution, comparative baseline or commander survey evidence in local records. | AUD-011-037, AUD-011-038, AUD-011-039, AUD-011-040 |
| RQ-16 | [x] | CONFLICT | Repeated "No implementation details leak" claim conflicts with [FR implementation prescriptions](spec.md#L178). | AUD-011-041 |

### Plan Gates, Review Claims, and Evidence

The [pre-design table](plan.md#L42) marks all 20 gates PASS. The [post-design paragraph](plan.md#L67) asserts all 20 were reevaluated. No separate dated execution/reviewer receipts were present among the 14 local input files. The following rows assess each obligation for both claims; no PASS glyph is treated as proof. Section labels in the old plan do not match the current constitution.

| Gate | Status | Evidence-backed assessment of pre/post claim | Follow-up |
| --- | --- | --- | --- |
| PG-01 | PARTIAL | Life-safety priority helpers exist, but actual demand severity/global allocation and measured 15s are incomplete. [Queue](../../apps/agents/resource_allocation/priority.py#L134). | AUD-011-008, AUD-011-010, AUD-011-037 |
| PG-02 | PARTIAL | Override endpoint is authored but changes no plan and has no authenticated emergency-stop/cancellation effect. [Handler](../../apps/agents/resource_allocation/agent.py#L382). | AUD-011-002, AUD-011-003 |
| PG-03 | PARTIAL | [Templates](../../apps/agents/resource_allocation/templates.py#L13) provide some explanations but not complete factual context/transport shortfalls. | AUD-011-027 |
| PG-04 | PARTIAL | LLM fallback works in source, but [plan confidence](../../apps/agents/resource_allocation/pipeline.py#L647) ignores stale/partial inventory and no complete degraded-data path exists. | AUD-011-026 |
| PG-05 | PARTIAL | [Handoff class](../../apps/agents/common/handoffs.py#L26) exists; real source payload/consumer integration is incomplete and replacement is not equivalent. | AUD-011-001, AUD-011-006, AUD-011-009 |
| PG-06 | PARTIAL | [Supersession](../../apps/agents/resource_allocation/pipeline.py#L855) is unconditional and audit lacks full state transitions/decision facts. | AUD-011-004, AUD-011-014, AUD-011-029 |
| PG-07 | PARTIAL | [Plans default proposed](../../apps/agents/resource_allocation/pipeline.py#L647), but commander authority is not enforced by functioning approval and a required-approval-level field is absent. | AUD-011-002, AUD-011-003, AUD-011-024 |
| PG-08 | PARTIAL | [InputSnapshot](../../apps/agents/resource_allocation/pipeline.py#L696) is not replay-complete and its hash omits crucial resource/configuration fields. | AUD-011-023 |
| PG-09 | PARTIAL | [Age helper](../../apps/agents/resource_allocation/pipeline.py#L824) records age but neither enforces freshness nor adjusts confidence. | AUD-011-026 |
| PG-10 | PARTIAL | [Version fallback](../../apps/agents/resource_allocation/versioning.py#L138) and weak [replay assertions](../../tests/contract/test_resource_allocation_reproducibility.py#L77) contradict full concurrency/reproducibility assurance. | AUD-011-013, AUD-011-023 |
| PG-11 | PARTIAL | [Inventory data](../../data/resource-inventories/sample-inventory.json#L1) is equipment/organization-oriented, but override user IDs/justifications and LLM prompts need scoped privacy controls. No privacy review is evidenced. | AUD-011-003, AUD-011-028, AUD-011-041 |
| PG-12 | UNVERIFIED | [Module location parameter](../../infra/modules/resource-allocation.bicep#L4) and plan region statements do not prove AU deployed residency, especially spill/audit stores. | AUD-011-033, AUD-011-041 |
| PG-13 | PARTIAL | [Tenant label](../../apps/agents/resource_allocation/pipeline.py#L91) exists; shared inventory/status/counters violate the claimed complete boundary. | AUD-011-022 |
| PG-14 | PARTIAL | [Safety validation](../../apps/agents/common/llm_mixin.py#L149) exists, but counts-only prompt lacks factual grounding and prompt-injection-specific allocation acceptance evidence is absent. | AUD-011-027, AUD-011-028 |
| PG-15 | PARTIAL | Shared content validation/fallback is supported; allocation-specific failure provenance and all replacement-path boundaries are incomplete. [Mixin](../../apps/agents/common/llm_mixin.py#L64). | AUD-011-001, AUD-011-028 |
| PG-16 | UNVERIFIED | [Azure module](../../infra/modules/resource-allocation.bicep#L40) is an authored artifact, not a deployed state/region/DR record. Current constitution has a narrowly bounded model-hosting carve-out. | AUD-011-033, AUD-011-041 |
| PG-17 | PARTIAL | [Audit buffering](../../apps/agents/resource_allocation/audit.py#L42) and LLM fallback exist; plan retry, stale inventory, durable spill recovery and queue resilience are incomplete. | AUD-011-015, AUD-011-026, AUD-011-030 |
| PG-18 | PARTIAL | [create_item](../../apps/agents/resource_allocation/audit.py#L65) and no-TTL declaration support append-only intent, not storage-enforced immutability, complete records or recoverability. | AUD-011-029, AUD-011-030, AUD-011-033 |
| PG-19 | PARTIAL | [Observability registry](../../apps/agents/resource_allocation/telemetry.py#L91), identity and scaling declarations exist but are not connected proof of WAF/identity/monitoring compliance. | AUD-011-031, AUD-011-033 |
| PG-20 | PARTIAL | [Flood](../../tests/simulation/test_flood_allocation_scenario.py#L106), [bushfire](../../tests/simulation/test_bushfire_allocation_scenario.py#L89) and [multi-incident](../../tests/simulation/test_multi_incident_scenario.py#L62) tests are authored with incomplete assertions; no allocation cyclone/reproducibility acceptance run is established. | AUD-011-036, AUD-011-037 |

Other review/checklist claims assessed:

- The task prerequisite checkmarks mean design files were authored, not that their conclusions passed an independent review. All those files were located and read; conflicting decisions are tracked in AUD-011-041.
- Every phase checkpoint claiming "fully functional", "operational", "fully isolated" or "all 16 decision types covered" is **PARTIAL**, as demonstrated by the corresponding task/requirement rows. Enum membership is not event emission.
- The instructions to write failing tests first, pass lint/unit/integration before merge, perform infrastructure what-if, obtain reviewer approval and consult actors are **UNVERIFIED** historical/process claims. No such actions were executed or invented in this audit.
- The plan's inherited "stub-only" issue is no longer the full source description: the legacy [agent](../../apps/agents/resource_allocation/agent.py#L106) and pipeline have substantial code. However, newer [MAF fallback](../../apps/agents/maf_runtime/agents/resource_allocation_agent.py#L25) and dispatcher paths remain insufficient. Neither filenames nor old issue descriptions were used as proof of absence.
- All three country hypothesis files satisfy the six required headings, explicit Not tested status, multiple preconditions, quantified falsification, and owning-spec link as **IMPLEMENTED authored stubs**. Their measured outcomes, licenses, D-009 clearance and SME approval are **UNVERIFIED**. Only an authorized governed change can promote those statuses.

## 8. Future Validation Commands and Prerequisites

**None of the commands in this section ran during the audit.** Use a later explicitly authorized implementation/validation session. Start from repository root. Select/configure Python 3.12+ through the workspace Python-environment tools before any Python execution. The selected environment must contain root dev dependencies plus agent dependencies from [pyproject.toml](../../pyproject.toml#L26) and [apps/agents/pyproject.toml](../../apps/agents/pyproject.toml#L9). Use its fully qualified executable, represented below by `$SelectedPython`; do not guess or install packages as part of this review. [tests/conftest.py](../../tests/conftest.py#L10) adds repository/agent paths.

Hermetic unit/contract runs must inject fake LLM/store/clock clients and use temporary spill paths without inherited production credentials. Integration, real-worker rehearsal, exercise measurement and deployment validation require separate user approval, isolated test tenants/resources and test-owned data. Secrets must be supplied directly through secure environment tooling, never written to a report.

| ID | Future-only command or procedure | Prerequisites and expected results |
| --- | --- | --- |
| V1 | `& $SelectedPython -m pytest tests/unit/test_resource_allocation_models.py tests/unit/test_resource_allocation_config.py tests/unit/test_resource_allocation_scoring.py tests/contract/test_resource_allocation_plan_schema.py -q` | After model/config/matching fixes; assert all required fields/invariants and finite formula boundaries, not only valid self-constructed fixtures. |
| V2 | `& $SelectedPython -m pytest tests/unit/test_resource_allocation_dedup.py tests/unit/test_resource_allocation_priority.py tests/unit/test_resource_allocation_inventory.py tests/unit/test_resource_allocation_matcher.py tests/unit/test_resource_allocation_versioning.py -q` | Stateful ETag fake, injectable clock, multi-incident/tenant fixtures; assert exact choices, no duplicate ownership, correct reservation/return rules and fail-closed OCC. |
| V3 | `& $SelectedPython -m pytest tests/unit/test_resource_allocation_pipeline.py tests/unit/test_resource_allocation_endpoints.py tests/unit/test_resource_allocation_audit.py tests/contract/test_resource_allocation_handoff.py tests/contract/test_resource_allocation_reproducibility.py -q` | Seeded stores and trusted-token fixtures; inspect actual persisted changes, identity/scope, event payloads, safety/outage branches and exact replay results. |
| V4 | `& $SelectedPython -m pytest tests/integration/test_resource_allocation_cosmos.py tests/integration/test_resource_allocation_service_bus.py -m integration -q -rs` | Replace unconditional skips first. Approved emulator/test services, aligned endpoint names, identities and cleanup; real create/read/conditional writes, consumer settlement and isolation must execute with no unconditional skips. Current files cannot establish this result. |
| V5 | `& $SelectedPython -m pytest tests/simulation/test_flood_allocation_scenario.py tests/simulation/test_bushfire_allocation_scenario.py tests/simulation/test_multi_incident_scenario.py -q` | Correct resource capabilities and locations; add the proposed cyclone/accessible-transport cases before claiming full scenario coverage. Assert nonvacuous exact allocations, shortfalls, donor impacts, approval gates and audit reconciliation. |
| V6 | `& $SelectedPython -m pytest tests/benchmark/test_pipeline_latency.py -k resource_allocation -q -rs` | Proposed allocation benchmark cases must first be added to this existing home. Today the selector does not establish allocation-load coverage; zero selected cases is not a pass. Later run at least 30 incidents with declared pool sizes, real timestamps and injected failure load; retain raw p50/p95/p99 and breach events. |
| V7 | Governed paired manual/assisted exercises and commander survey, following AUD-011-038 and AUD-011-039 | No runnable measurement command is claimed to exist in the reviewed local artifacts. Implement/approve the protocol, then record exact future runner/version, nine-or-more paired scenarios across disaster types, survey denominator, uncertainty and results. |
| V8 | Later clean-environment quickstart rehearsal and approved infrastructure preflight | Repair quickstart and resolve the deployment-selected runtime first. Use repository Azure prepare/validate procedures, current governance discovery, AVM guidance and explicit cloud authorization before deriving/building/deploying anything. Record the exact subsequent commands and outcomes; do not treat this report as a deployment instruction or approval. |
| V9 | Document-only traceability, persona/evidence-schema review and human sign-off verification | Review all original IDs, acceptance mappings and checklist decisions. Validate hypothesis headings/statuses and actual SME/practitioner identities/dates. Keep D-009/country gates and unresolved baseline/HYP-009 evidence open. |

Existing test homes are deliberately reused. Proposed fixture additions include: a valid mixed bus/minibus inventory; fully capable contested ambulance; known Brisbane/Blue Mountains coordinates; frozen clocks; independent tenant-scoped stores; an ETag-enforcing fake; store/disk-failure sequences; signed commander claims; actual producer payloads; a true-tie five-versus-three unmet-demand set; and paired manual/assisted exercise records. These fixtures were not generated or executed here.

## 9. Report-Only Validation and Handoff

Report validation is limited to comparing original task/requirement/amendment/checklist IDs and checkbox states against this document, checking scenario/edge/clarification/gate row counts, verifying existing local link targets and line bounds, confirming all AUD follow-ups are unique and unchecked, and requesting editor diagnostics for this report only. Product success is not inferred from document validation.

This review does not certify runtime behavior, SDK compatibility, installed dependencies, JWT ingress enforcement, deployments, identity permissions, AU residency, load/performance, statistical uplift, commander satisfaction, actor consultation, PR approval, or execution of any original task. It records concrete source support and gaps at the pinned revision and leaves the original evidence unchanged.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 011 only. Three parallel technical reviews examined allocation
safety/ownership, lifecycle/telemetry, and evidence/infrastructure. The source-completable matcher defect was fixed:
candidate scoring now enforces resource type and subtype compatibility before applying the greedy score, preventing a
nearer incompatible vehicle from satisfying a demand after candidate-pool unioning.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| AUD-011-005 | Source fix complete for matcher eligibility. | Added a mixed minibus/ambulance regression case; `python -m pytest tests/unit/test_resource_allocation_scoring.py tests/unit/test_resource_allocation_matcher.py -q` returned `43 passed`. |
| AUD-011-001–004 / 006–009 | Open P0 safety/runtime work. | Disconnected deployment runtime, unauthenticated no-op overrides, uncommitted resource ownership, version fallback, and fabricated upstream context remain; no durable broker/Cosmos evidence was created. |
| AUD-011-010–041 | Partial or evidence-gated. | Cross-incident allocation, lifecycle/status, audit/telemetry, infrastructure wiring, load, commander approval, scenario, and human/SME evidence remain open or unverified. |

No deployment, identity, persistence, broker, performance, or human approval evidence was produced. This pass is a
narrow algorithmic eligibility correction, not end-to-end allocation readiness.

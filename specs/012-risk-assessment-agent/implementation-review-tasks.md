# Risk Assessment Agent: Implementation Review and Open Tasks

**Review date:** 2026-09-11  
**Reviewed revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Method:** Fresh, isolated, static source and test-assertion review.  
**Disposition:** Not ready to claim implementation completion or operational acceptance.

## Scope and Evidence Rules

This report follows the complete [Review Contract](../001-spec-implementation-audit/README.md#L13).
It covers **69 original tasks** (68 `[X]`, one `[ ]`), **52 requirements and success criteria**
(42 FR, two NFR, eight SC), **22 acceptance scenarios**, **seven edge cases**, all appended amendments,
**102 checklist obligations**, and both declarations of the plan's **21 constitution gates**.
There are **33 open remediation tasks**, all unchecked. Original checkboxes are historical input, not proof.

The checked-out HEAD matched the requested revision. A read-only diff of the reviewed risk implementation,
shared agent code, domain models, risk tests, infrastructure, and original 012 artifacts against that revision
returned no changed paths. Only this report is authored by this audit. No source, original spec, task list,
checklist, evidence, index, branch, or commit was changed. No delegation was used.

No product tests, builds, application imports, benchmarks, deployments, external approvals, or cloud-resource
queries were performed. The Python fact-grounded coding skill was applied with the evidence ladder limited
to source inspection by the user's execution boundary. No interpreter, SDK-runtime behavior, deployed
configuration, or measured service outcome is asserted from source alone. Repository code-review and Bicep
review instructions were read; this is not a policy-discovery or infrastructure-generation exercise.

The audit-control contract was the only implementation-audit input. No sibling implementation review was
used. Original, explicitly referenced design/review evidence is distinguished below from independent proof
that its assertions were executed or approved.

### Complete Local Inputs

| Input | Assessment |
| --- | --- |
| [spec.md](spec.md#L1) | Read in full, including three clarification sessions and all appended ASM/PER/HYP/SCP and country amendments. |
| [tasks.md](tasks.md#L1) | Read in full, including test-first instructions, checkpoints, dependencies, and the unchecked quickstart task. |
| [plan.md](plan.md#L1) | Read in full: two gate declarations, checklist resolutions, phases, resource design, and five historical implementation issues. |
| [research.md](research.md#L1) | All nine decisions read; decisions are authored design evidence, not production validation. |
| [data-model.md](data-model.md#L1) | All entities, relationships, validation rules, lifecycle rules, mappings, and configuration entries read. |
| [contracts/assessment-pipeline.md](contracts/assessment-pipeline.md#L1) | All eight stages, error paths, and latency budgets read. |
| [contracts/health-endpoint.md](contracts/health-endpoint.md#L1) | Health status/schema/SLA and override request/response/conflict semantics read. |
| [contracts/telemetry.md](contracts/telemetry.md#L1) | All metric, alert, event, and trace obligations read. The actual metric table enumerates 19 metrics, despite prose claiming 20. |
| [quickstart.md](quickstart.md#L1) | All setup, environment, launch, verification, testing, and container instructions read, not executed. |
| [checklists/requirements.md](checklists/requirements.md#L1) | All 102 items read; all original boxes are unchecked. |
| [evidence/HYP-039.md](evidence/HYP-039.md#L1) | PH calibration stub; explicitly Not tested. |
| [evidence/HYP-040.md](evidence/HYP-040.md#L1) | JP calibration stub; explicitly Not tested. |
| [evidence/HYP-041.md](evidence/HYP-041.md#L1) | BD calibration stub; explicitly Not tested. |

Associated originals inspected include the [current constitution](../../.specify/memory/constitution.md#L1),
[persona contract](../027-spec-hardening/contracts/persona-profile.md#L1),
[hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1),
the specifically linked [portfolio rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1),
and the relocated [MAF cutover playbook](../../docs/corpus/aidr/runbooks/maf-cutover-playbook.md#L1).
The baseline is an authored portfolio-wide snapshot, not a measured per-012 improvement or an independent
approval. The named HYP-010 stub and post-feature rubric comparator were not located.

### Status Legend

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Full scoped behavior or authored artifact is supported by inspected source. Not a test-pass or deployment claim. |
| PARTIAL | Some support exists, but a specified obligation is missing or contradicted. |
| MISSING | Required behavior/artifact was not found in the named search scope after checking relocation. |
| CONFLICT | Original artifacts or current behavior disagree and require an explicit decision. |
| UNVERIFIED | Source cannot establish execution, measurement, approval, or deployed state. |
| SUPERSEDED | Reserved for an explicitly documented replacement/retirement; a renamed helper alone is insufficient. |

An IMPLEMENTED helper/test task does not promote its enclosing workflow to IMPLEMENTED. For example,
the numeric communication threshold is present, but a reachable, durable delivery path is not established.

### Relocation and Negative-Finding Scope

| Scope | Search and controlling path inspected | Result |
| --- | --- | --- |
| S1: local artifacts | Entire 012 folder, including contracts/checklists/evidence. | Thirteen original files; no local implementation report, approval record, load result, survey result, or execution log was an input. |
| S2: risk implementation | All tracked paths under `apps/agents/risk_assessment`; full agent, pipeline, config, models, correlation, severity, versioning, audit, dedup, templates, telemetry, handler, extrapolation, and hazard-map implementations inspected. | Real helpers exist; the deficiencies below are connected-behavior findings, not filename assumptions. |
| S3: host and replacements | Searches across agent/API source for pipeline construction, agent imports, store/queue names, lifecycle and recovery methods; followed dispatcher, MAF executor/facade/factory/workflow, Monitoring producer, signal repository, recommendation service/routes, and risk UI bridge. | No production construction of `AssessmentProcessingPipeline` found. Dispatcher and UI bridge are different behaviors. MAF facade does not delegate to the pipeline. |
| S4: tests | Risk-named unit, contract, integration, simulation and equivalence tests; newer auto-fanout/extrapolation tests included. | Original test homes exist. Several assertions test mocks/helpers instead of the claimed production operation. |
| S5: deployment/operations | Tracked `infra`, agent container/build metadata, `docs`, and `.github/workflows` searched for risk module/queue/container/metric references; root agent deployment and isolated risk module inspected. | Risk module is authored but no deployment caller was found. No risk metric alert wiring found in this scope. |
| S6: amendment evidence | Local and 028 evidence plus repository-wide filename searches for HYP-010 variants and the named rubric comparator. | Neither HYP-010 stub nor post-feature comparator found; existing HYP-039/040/041 stubs are not missing. |

The initial workspace regex search timed out and `rg` was unavailable. Searches were completed with
read-only PowerShell and tracked-file `git grep`, excluding sibling implementation reports. S2/S3 searches
for expiry, recommendation lineage, audit recovery callers, and safety/version metric emitters found only
field/helper declarations where noted below. Missing claims are limited to these searched sources, not to
unqueried deployed resources.

## Highest-Impact Findings

| Priority | Finding and direct evidence | Follow-up |
| --- | --- | --- |
| P1 | The container starts [dispatcher](../../apps/agents/Dockerfile#L48), whose [invoke route](../../apps/agents/dispatcher/agent.py#L207) answers simulation questions. The standalone [risk entrypoint](../../apps/agents/risk_assessment/agent.py#L808) starts only an HTTP app. Neither wires the specified queue/pipeline/stores. | AUD-012-001, AUD-012-027 |
| P1 | [Intake validation](../../apps/agents/risk_assessment/pipeline.py#L97) checks target and dedup only. There is no incident lookup. The [Monitoring payload](../../apps/agents/monitoring/agent.py#L111) omits signal IDs and the [receiver fallback](../../apps/agents/risk_assessment/pipeline.py#L169) invents fresh signal evidence. | AUD-012-002, AUD-012-003, AUD-012-004 |
| P1 | [Correlation](../../apps/agents/risk_assessment/correlation.py#L60) flags all-stale data but [assessment generation](../../apps/agents/risk_assessment/agent.py#L76) and [escalation](../../apps/agents/risk_assessment/pipeline.py#L512) ignore the flag. A single confidence-1.0/freshness-0.1 signal stays 1.0 before fallback and 0.8 after it, above the public-alert threshold. This is a static counterexample, not an executed test. | AUD-012-005 |
| P1 | [Version fallback](../../apps/agents/risk_assessment/versioning.py#L127) returns an unreserved next integer, not a unique suffix. [Persistence exceptions](../../apps/agents/risk_assessment/pipeline.py#L415) are logged while processing continues; recommendation IDs use a process-local counter. | AUD-012-006, AUD-012-007, AUD-012-010 |
| P1 | [Override](../../apps/agents/risk_assessment/agent.py#L714) trusts request-supplied identity/role, reads with the recommendation ID as partition key, mutates/upserts the original, and can return success with no store or audit writer. | AUD-012-008, AUD-012-009 |
| P1 | [Contradiction detection](../../apps/agents/risk_assessment/correlation.py#L143) groups only by hazard parameter, labels sources by trust kind, and has no geographic boundary. [Audit](../../apps/agents/risk_assessment/pipeline.py#L288) records zero confidence values rather than pair-specific adjustments. | AUD-012-011, AUD-012-022 |
| P1 | [Validity is populated](../../apps/agents/risk_assessment/agent.py#L114), but no scoped expiry/supersession worker or escalation freshness guard was found. [Safety fallback metadata](../../apps/agents/common/llm_mixin.py#L151) is not converted into required risk audit/review events. | AUD-012-012, AUD-012-013 |
| P2 | [Health](../../apps/agents/risk_assessment/agent.py#L631) calls the LLM synchronously and hardcodes queue depth/status. [Audit recovery](../../apps/agents/risk_assessment/audit.py#L113) has no production caller; metric registries and mock tests do not establish observability or recovery. | AUD-012-023, AUD-012-025, AUD-012-026 |

The MAF shared-code risk is separate from these local defects: its [legacy risk facade](../../apps/agents/maf_runtime/agents/risk_assessment_agent.py#L25)
constructs only a default-heavy decision record, while the [MAF path](../../apps/agents/maf_runtime/agents/_factory.py#L266)
parses LLM output into that same audit schema. The [workflow](../../apps/agents/maf_runtime/workflow/builder.py#L132)
unconditionally starts evacuation/resource processing. Its [risk prompt](../../apps/agents/maf_runtime/agents/risk_assessment.yaml#L10)
uses five severity buckets rather than the specified four. The replacement exists, but does not establish
retirement or preservation of 012's assessment, recommendation, threshold, persistence, and audit obligations.

## Open Remediation Tasks

These are instructions for later implementation and testing, not changes made in this audit. Priorities
are P1 safety/data-integrity/delivery blockers, P2 completion and verification gaps, and P3 documentation
and evidence maintenance. Dependencies are explicit; independent work need not wait for unrelated tasks.

### Shared Tester Fixtures and Command Rules

Reuse the existing `_make_handoff`, `_signal`, `_make_recommendation`, `RecordingAuditWriter`, `monkeypatch`,
`MagicMock`/`AsyncMock`, and `tmp_path` homes linked in each task. Proposed fixture extensions are:

- **FX-1:** Same incident, named BoM/GA/IoT/social sources, stable IDs, fixed UTC timestamps, coordinates,
  confidence/freshness, provenance, risk direction/parameter, and population; fresh/stale variants.
- **FX-2:** Two incidents with colliding signal IDs and identical handoff IDs in live and simulation contexts;
  a store double that enforces partition and returned-document tenant/incident ownership.
- **FX-3:** Stateful Cosmos-compatible fake with create-only uniqueness, partition checks, conditional writes,
  404/409/412/outage injection, restart state, and an operation log. SDK/emulator verification is a later gate.
- **FX-4:** LLM and safety fakes installed before agent construction: success, partial citation, empty response,
  timeout, unsafe output, validator outage, recovery, and deterministic recorded responses. No real model call.
- **FX-5:** Real consumer adapter with fake receiver/sender and an **async** delivery spy; complete, abandon,
  retry, dead-letter, cancellation, and elapsed time are observable.
- **FX-6:** Authenticated commander/non-commander/cross-tenant principals, recommendations with etags and
  prior versions, signed-off template fixtures, fixed clock, and malicious modification-field attempts.
- **FX-7:** Bounded audit buffer plus temporary spill files, process restart, duplicate acknowledgments,
  corrupt line, partial recovery, and disk-write failure.

Command families V1-V6 are defined in the future-validation section. All commands require later authorization,
a prepared test environment, explicit fake dependencies for hermetic runs, and isolation from live tenants.

### AUD-012-001: Connect a Real Intake and Processing Host

- [ ] AUD-012-001 **P1: Wire the selected production host to the complete risk workflow.**

**Original obligations:** FR-001, FR-005, FR-017, FR-028; T020, T021, T022, T065.
**Expected/actual/impact:** A Monitoring handoff must reach the assessment pipeline and durable dependencies.
The [standalone entrypoint](../../apps/agents/risk_assessment/agent.py#L808) supplies only an agent/config to
`create_app`; the container's [dispatcher](../../apps/agents/dispatcher/agent.py#L207) performs Q&A instead.
The [MAF facade](../../apps/agents/maf_runtime/agents/risk_assessment_agent.py#L25) is not a pipeline delegate.
S2/S3/S5 found no risk Service Bus consumer or production pipeline construction. Helpers alone cannot deliver US1.
**Developer:** Select and document the supported host with the runtime owner; compose receiver, incident/signal
stores, assessment/recommendation containers, durable version counter, audit writer, and downstream sender.
Start/stop intake with application lifecycle; preserve dispatcher/MAF contracts for their existing callers.
Do not declare the original behavior retired without an explicit approved replacement decision.
**Tester positive:** Extend [Service Bus tests](../../tests/integration/test_risk_assessment_service_bus.py#L111)
with FX-5 invoking the actual adapter and FX-3; assert persisted assessment/recommendations/audit and settlement.
**Tester negative:** Missing required store or receiver must not advertise working intake or acknowledge lost work.
**Tester edge:** Cancellation/restart during processing leaves work recoverable; exercise legacy/MAF flag modes.
**Dependencies/acceptance:** Coordinate with AUD-012-031 and AUD-012-027; V2/V4. One documented reachable path
must satisfy the full input-to-persistence-to-delivery contract, not a test-local imitation.

### AUD-012-002: Validate Incident and Handoff Boundaries

- [ ] AUD-012-002 **P1: Reject malformed, wrong-source, and unknown-incident handoffs with audit evidence.**

**Original obligations:** FR-001, FR-004; US1; edge EC-01; T013, T021.
**Expected/actual/impact:** [Validation](../../apps/agents/risk_assessment/pipeline.py#L97) accepts an already-built
model and checks target/dedup, but not incident existence, allowed source, confidence bounds, or payload shape.
No incident repository is injected. Orphaned or malformed inputs can be treated as valid assessments.
**Developer:** Own validation at the real deserialization boundary and pipeline boundary; inject incident lookup,
validate the nested summary/list shape, enforce source/target semantics, and audit safe rejection metadata.
Define unknown versus temporarily unavailable incident-store behavior and resolve the two rejection event spellings.
**Tester positive:** In [pipeline tests](../../tests/unit/test_risk_assessment_pipeline.py#L55), use a valid
Monitoring handoff and an existing incident fixture; assert one intake record and continued processing.
**Tester negative:** Missing incident, wrong source/target, invalid JSON, out-of-range confidence, or non-object
`signalSummary` yields rejection evidence and no assessment or recommendation.
**Tester edge:** Closed incident and incident-store outage follow an approved policy, not an assumed existence result.
**Dependencies/acceptance:** AUD-012-001, AUD-012-031; V1/V2. All rejection cases are observable and non-escalating.

### AUD-012-003: Enforce Tenant and Incident Ownership

- [ ] AUD-012-003 **P1: Bind reads, writes, counters, and handoffs to validated tenant/incident context.**

**Original obligations:** FR-010c, FR-027; US5-AS3; EC-05; T021, T046.
**Expected/actual/impact:** [Signal reads](../../apps/agents/risk_assessment/pipeline.py#L199) use incident ID alone;
[normalization](../../apps/agents/risk_assessment/pipeline.py#L258) drops returned scope. `tenant_id` can override
the inbound tenant in [processing](../../apps/agents/risk_assessment/pipeline.py#L648), and the escalation block
recognizes only names starting with `sim`. Tenant labels on output are not proof of isolated inputs.
**Developer:** Use the established tenant model and store partition contract, validate returned ownership, reject
conflicting context, and require matching downstream scope. Preserve single-incident processing; do not correlate
unrelated incidents. Key idempotency/version state by validated scope, not an unqualified handoff ID.
**Tester positive:** Extend [handoff contracts](../../tests/contract/test_risk_assessment_handoff.py#L92) and
[pipeline tests](../../tests/unit/test_risk_assessment_pipeline.py#L118) with FX-2; assert independent records.
**Tester negative:** Foreign-scope signal, forged scope key, and simulation input plus explicit live override fail closed.
**Tester edge:** A simulation tenant without a `sim` prefix and repeated IDs across tenants never reach a live sender.
**Dependencies/acceptance:** AUD-012-002, AUD-012-004, AUD-012-010; V1/V2. Assert actual store keys and sender calls,
not only propagated fields or a delivery counter with no sender attached.

### AUD-012-004: Retrieve Real Signals and Apply Missing-Input Penalties

- [ ] AUD-012-004 **P1: Repair the Monitoring-to-risk signal contract and remove fabricated production evidence.**

**Original obligations:** FR-002, FR-005, FR-025, FR-032; US1-AS3/AS4, US7-AS3; T010, T013, T020, T021, T055.
**Expected/actual/impact:** [Monitoring summary](../../apps/agents/monitoring/agent.py#L52) has no signal IDs.
[Risk retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) synthesizes fresh, increasing signals with
empty provenance when IDs/store are absent. Partial read failures increment a local count that never reaches
confidence computation. For two requested signals and one confidence-0.9 survivor, fallback can leave 0.72
instead of a missing-input-adjusted 0.36, crossing the alert threshold.
**Developer:** Carry stable source IDs upstream; adapt the real [signal repository](../../apps/api/app/repositories/signal_repository.py#L60)
without creating an agents-to-API import dependency. Preserve canonical source identity, freshness, timestamps,
location, hazard parameters, payload, and provenance. Return retrieved and missing IDs plus requested count;
apply the agreed proportional penalty before escalation. Restrict synthetic inputs to explicit fixtures/simulation.
**Tester positive:** Extend [pipeline retrieval tests](../../tests/unit/test_risk_assessment_pipeline.py#L90) with FX-1/FX-3
and the actual Monitoring producer; assert original IDs and exact normalized facts.
**Tester negative:** One/all unavailable reads lower confidence and audit the actual missing IDs; no invented provenance.
**Tester edge:** Empty ID list, repeated references, malformed signal data, and mixed returned ownership remain distinguishable.
**Dependencies/acceptance:** AUD-012-002, AUD-012-003; V1/V2. Available evidence is used without disguising missing evidence.

### AUD-012-005: Make Staleness an Escalation Safety Gate

- [ ] AUD-012-005 **P1: Force all-stale assessments low and prevent every downstream escalation.**

**Original obligations:** FR-007, FR-015, FR-016; US1-AS3; EC-02; T010, T015, T020, T054.
**Expected/actual/impact:** [Correlation](../../apps/agents/risk_assessment/correlation.py#L103) records `all_stale`
without lowering its weighted mean. [Generation](../../apps/agents/risk_assessment/agent.py#L96) ignores the flag,
and [escalation](../../apps/agents/risk_assessment/pipeline.py#L512) checks neither staleness nor an assessment hold.
The named [low-confidence test](../../tests/unit/test_risk_assessment_correlation.py#L69) asserts only the flag.
**Developer:** Apply a conservative final confidence/category rule for all-stale/zero-available inputs; persist the
reason and enforce the hold ahead of every target, including task-based resource allocation. Make stale IDs appear
on both LLM and template summaries. Extrapolation boosts must not remove a safety hold.
**Tester positive:** Fresh FX-1 inputs retain the expected numeric thresholds in the existing correlation/pipeline homes.
**Tester negative:** All freshness values below 0.5 produce `low` and zero async sender calls even with confidence 1.0
and coordination tasks. Verify the complete returned recommendation/handoff sets, not just counters.
**Tester edge:** Exactly 0.5 is not stale; zero freshness, mixed freshness, custom thresholds, and extrapolation remain bounded.
**Dependencies/acceptance:** AUD-012-004, AUD-012-017, AUD-012-019; V1/V2. The static counterexample above must regress.

### AUD-012-006: Allocate Durable Monotonic Assessment Versions

- [ ] AUD-012-006 **P1: Replace unreserved version fallback with a concurrency-safe allocation policy.**

**Original obligations:** FR-006; US1-AS2; T012, T017, T020, T062.
**Expected/actual/impact:** [No-store mode](../../apps/agents/risk_assessment/versioning.py#L39) always returns 1.
[Contention fallback](../../apps/agents/risk_assessment/versioning.py#L127) reads current+1 without reserving it,
or returns 1. Concurrent workers can claim the same assessment ID; the promised UUID suffix is absent and itself
conflicts with the integer/monotonic model. SDK conditional-write semantics are not proved by unrestricted mocks.
**Developer:** Resolve the integer/UUID contract, then allocate within the tenant/incident/type persistence boundary
using the SDK's supported conditional operation. Preserve create-only assessment versions; handle first-create
409, 412, outage, and exhausted contention explicitly. Never report a non-reserved integer as a durable allocation.
**Tester positive:** Extend [version tests](../../tests/unit/test_risk_assessment_versioning.py#L17) with stateful FX-3;
successive and independent-scope allocations are unique and monotonic.
**Tester negative:** Exhausted conflicts or inaccessible counter cannot silently collide or overwrite an assessment.
**Tester edge:** Parallel first writers, restart, and 100 same-incident requests; validate actual SDK etag preconditions later.
**Dependencies/acceptance:** AUD-012-003, AUD-012-031; V1/V2/V4. Every persisted assessment has one uniquely reserved version.

### AUD-012-007: Preserve Assessment and Recommendation Durability

- [ ] AUD-012-007 **P1: Stop reporting durable completion after failed writes and make recommendation IDs restart-safe.**

**Original obligations:** FR-005, FR-006, FR-017, FR-024, FR-034; T019, T020, T028, T029, T036, T062.
**Expected/actual/impact:** [Assessment writes](../../apps/agents/risk_assessment/pipeline.py#L415) and
[recommendation writes](../../apps/agents/risk_assessment/pipeline.py#L461) catch exceptions and continue into
escalation/completed status. [Recommendation sequencing](../../apps/agents/risk_assessment/agent.py#L66) resets
per process. Multiple assessments can reference lost recommendations or duplicate IDs after restart.
**Developer:** Make persistence outcomes explicit; provide a durable pending/outbox/retry path for dependency
failure that continues safe intake without falsely claiming persistence. Allocate recommendation identity/version
from durable scoped context. Persist below-threshold recommendations in an actual human-review-readable store.
**Tester positive:** Use FX-3/FX-5 in [Cosmos tests](../../tests/integration/test_risk_assessment_cosmos.py#L65);
read the real assessment/recommendation documents back and assert their links and create-only writes.
**Tester negative:** Failed create, 409, or missing store must not yield an untraceable delivered handoff or completed success.
**Tester edge:** Retry after partial persistence and process restart preserves one logical recommendation and all prior versions.
**Dependencies/acceptance:** AUD-012-001, AUD-012-006, AUD-012-024; V2/V4. Recovery reconciles records and deliveries without loss.

### AUD-012-008: Authenticate and Scope Human Overrides

- [ ] AUD-012-008 **P1: Require authenticated commander authority and a real scoped recommendation for overrides.**

**Original obligations:** FR-037, FR-029; health contract; CHK075/CHK076/CHK097; T058.
**Expected/actual/impact:** [Override](../../apps/agents/risk_assessment/agent.py#L714) has no authentication/role
dependency; identity and role come from the request. It reads with `partition_key=recommendation_id`, not
`incident_scope_key`, and returns 200 when storage/audit dependencies are absent. These are unsafe authorization
and false-success semantics in the standalone app; deployed exposure was not tested.
**Developer:** Derive user/role/tenant from trusted authentication, authorize incident-command scope, obtain the
correct partition, validate nonempty justification, and reject missing dependencies. Do not return an audit ID
as if persisted unless the operation has a durable audit outcome. Preserve API error compatibility deliberately.
**Tester positive:** Extend [endpoint tests](../../tests/unit/test_risk_assessment_endpoints.py#L171) with FX-6/FX-3;
authorized same-scope approval updates the correct record and audit fields.
**Tester negative:** Anonymous, non-commander, forged-body identity, foreign tenant, and absent recommendation/store are rejected.
**Tester edge:** Same recommendation ID in two partitions and whitespace justification cannot bypass authorization.
**Dependencies/acceptance:** AUD-012-003, AUD-012-007; V1/V2. Replace the test that celebrates success without a store.

### AUD-012-009: Implement Immutable Modification and Conflict Handling

- [ ] AUD-012-009 **P1: Create linked recommendation versions instead of mutating the original on modify.**

**Original obligations:** FR-037, FR-038; T006, T058; override contract 409 behavior.
**Expected/actual/impact:** [Current override writes](../../apps/agents/risk_assessment/agent.py#L749) directly update
the original, allow arbitrary `doc.update(modifications)`, then upsert without an etag. `modified` is not a valid
[Recommendation status](../../packages/domain/src/domain/models/recommendation.py#L7), and no lineage field exists.
Approval identity, scope, and immutable evidence can be overwritten by arbitrary modifications.
**Developer:** Whitelist modifiable business fields; retain identity/scope/approval metadata; store a new linked,
versioned recommendation for modify. Use optimistic concurrency for permitted status changes. Record structured
override user/role/justification/time in an append-only audit entry and define treatment of already-created handoffs.
**Tester positive:** FX-6 modify in the existing endpoint/Cosmos homes creates a valid new version linked to unchanged content.
**Tester negative:** Stale etag returns 409; attempts to modify IDs, tenant, audit metadata, or unsupported status fail.
**Tester edge:** Two simultaneous commanders and a recommendation whose handoff is already active follow the agreed recall policy.
**Dependencies/acceptance:** AUD-012-008, AUD-012-021, AUD-012-031; V1/V2/V4. Original versions remain reconstructible.

### AUD-012-010: Make Idempotency Safe Under Retry and Scale-Out

- [ ] AUD-012-010 **P1: Distinguish in-flight, completed, and retryable handoffs across workers.**

**Original obligations:** FR-003, FR-034, NFR-001; EC-03; T009, T014, T021.
**Expected/actual/impact:** [Dedup](../../apps/agents/risk_assessment/dedup.py#L35) is a non-atomic in-process
check/insert, populated before processing succeeds. Worker restart/cross-instance delivery bypasses it, while a
failure can suppress a legitimate retry for ten minutes. The new [event handler](../../apps/agents/risk_assessment/handler.py#L95)
also records its dedup key before invoking the supplied runner.
**Developer:** Implement atomic, scope-qualified idempotency with an explicit processing lifecycle appropriate
to at-least-once transport. Preserve configurable TTL and allow recovery after failure without repeating committed
effects. Coordinate dedup retention with persistence and delivery identity.
**Tester positive:** Extend [dedup tests](../../tests/unit/test_risk_assessment_dedup.py#L8) and pipeline tests with FX-3;
repeat completed deliveries produce one assessment and a duplicate audit entry.
**Tester negative:** Two concurrent workers may not both commit; a retry after failure may not be silently discarded.
**Tester edge:** Exact TTL boundary, capacity eviction, restart, and identical IDs in separate scopes have explicit behavior.
**Dependencies/acceptance:** AUD-012-003, AUD-012-007; V1/V2. Add real concurrency assertions absent from T009's test source.

### AUD-012-011: Preserve Contradictory Evidence and Human Review

- [ ] AUD-012-011 **P1: Detect geographically relevant contradictions and retain both named perspectives.**

**Original obligations:** FR-011, FR-012, FR-013; US4; T037, T038, T039, T040, T041.
**Expected/actual/impact:** [Detector](../../apps/agents/risk_assessment/correlation.py#L143) uses only hazard
parameter and direction; source names are `source_kind`. The [normalizer](../../apps/agents/risk_assessment/pipeline.py#L258)
loses location and source identity. [Summary enrichment](../../apps/agents/risk_assessment/agent.py#L159) can be
skipped merely because LLM text says "contradiction". [Recommendation templates](../../apps/agents/risk_assessment/templates.py#L72)
ignore their assessment-summary argument. Distinct places can conflict and true disagreeing agencies disappear.
**Developer:** Normalize and group by validated incident, geographic area, and parameter; preserve provider names
and directions. Apply one multiplicative penalty, store review state and each pair, and require both perspectives
in every relevant recommendation. A review flag need not invent a different numeric escalation threshold.
**Tester positive:** FX-1 opposing BoM/IoT pairs in [correlation tests](../../tests/unit/test_risk_assessment_correlation.py#L106)
produce exact pairs, names, one 0.7 factor, and review metadata through persisted recommendations.
**Tester negative:** Different area/incident/parameter and consistent trajectories do not produce false contradictions.
**Tester edge:** Three-way conflict, stale/fresh disagreement, same trust class/different providers, and LLM omission.
**Dependencies/acceptance:** AUD-012-003, AUD-012-004, AUD-012-022; V1/V2. Pair-specific audit includes actual before/after confidence.

### AUD-012-012: Preserve Safety and Degradation Decisions

- [ ] AUD-012-012 **P1: Carry content-safety and dependency recovery outcomes into persisted risk decisions.**

**Original obligations:** FR-028, FR-031, FR-034, FR-035, FR-036; US7-AS1/AS2; EC-04; T020, T051, T053, T056.
**Expected/actual/impact:** The [mixin](../../apps/agents/common/llm_mixin.py#L64) validates LLM text and returns
fallback/review metadata, but the agent discards much of it. No risk `content_safety_failure` audit emission or
LLM recovery state was found. [Keyword safety fallback](../../apps/agents/common/content_safety.py#L166) requests
review even when passing; this flag is lost. The shared system prompt is emergency-general, not risk-scoped.
**Developer:** Preserve safety method/failure/review/error metadata, emit required risk audit entries for assessment
and recommendation calls, and record recovery transitions. Scope prompts to risk assessment and treat supplied
signal content as data. Define validator-unavailable behavior explicitly without bypassing the approved safety policy.
**Tester positive:** FX-4 success produces safe, traceable records; timeout then success produces degradation and recovery.
**Tester negative:** Extend [LLM contracts](../../tests/contract/test_risk_assessment_llm.py#L4) and pipeline tests:
unsafe or empty text never enters a record/handoff, and a safety failure has structured audit evidence.
**Tester edge:** Validator outage, keyword-only review flag, recommendation-only failure, and instruction-like signal text.
**Dependencies/acceptance:** AUD-012-011, AUD-012-022, AUD-012-031; V1/V2. Signed-off templates still skip runtime safety as specified.

### AUD-012-013: Implement Assessment Expiry and History

- [ ] AUD-012-013 **P1: Enforce expiry/supersession and exclude inactive assessments from new escalation.**

**Original obligations:** FR-005, FR-006, FR-010b; EC-02; T005, T020, T033, T034, T036, T062.
**Expected/actual/impact:** [Generation](../../apps/agents/risk_assessment/agent.py#L114) creates `valid_until` and
always sets active. S2/S3 found no lifecycle updater/history query; [escalation](../../apps/agents/risk_assessment/pipeline.py#L512)
does not inspect status/time. [Status testing](../../tests/integration/test_risk_assessment_cosmos.py#L201) copies a model,
not stored lifecycle state. Old assessments can drive new protective-action handoffs.
**Developer:** Add scoped lifecycle transitions, queryable ordered history, and a final status/time guard before
dispatch. Keep non-status content immutable. Resolve whether a newer version supersedes immediately or at expiry,
and define notification for already-active handoffs without silently broadening 012's downstream ownership.
**Tester positive:** FX-3/fixed clock in existing Cosmos/pipeline homes preserves history and transitions correctly.
**Tester negative:** Expired/superseded records never generate new handoffs, including task-based resource allocation.
**Tester edge:** Exact expiry instant, simultaneous newer version, incident/type separation, configurable durations.
**Dependencies/acceptance:** AUD-012-006, AUD-012-007, AUD-012-031; V1/V2/V4. The lifecycle is exercised through production code.

### AUD-012-014: Complete Scenario and Severity Semantics

- [ ] AUD-012-014 **P2: Derive scenario policy from incident/geography and reconcile fallback severity mappings.**

**Original obligations:** FR-010, FR-010a, FR-010d, FR-031; T011, T016, T020.
**Expected/actual/impact:** [Severity computation](../../apps/agents/risk_assessment/severity.py#L62) recognizes
disaster type only if already supplied on a signal. Direct earthquake/tsunami/cyclone/flood categories can default
to moderate. It has no incident/geographic scenario selection; the 50,000-population cutoff is code-defined.
The [fallback category table](data-model.md#L254) also disagrees with FR-031 for geohazard.
**Developer:** Establish named, reviewed AU scenario parameters for the five required hazards, derive them from
incident/geography, make type mapping/validity configurable as required, and use a reconciled fallback policy.
Keep data quality/confidence distinct from impact severity and expose the population/source rationale.
**Tester positive:** Extend [severity tests](../../tests/unit/test_risk_assessment_severity.py#L20) through the pipeline
for NSW/VIC bushfire, QLD/NT cyclone, QLD/NSW flood, national earthquake, and coastal tsunami.
**Tester negative:** Unknown/mismatched category or location must not silently claim an authoritative scenario model.
**Tester edge:** Confidence 0.399/0.4, population 49,999/50,000, missing population, and severity floor/ceiling.
**Dependencies/acceptance:** AUD-012-002, AUD-012-004, AUD-012-031; V1/V2. Reviewed parameters, not raw signal order, select policy.

### AUD-012-015: Ground Summaries and Enforce Every Citation

- [ ] AUD-012-015 **P2: Include complete evidence and final reasoning in assessment and recommendation text.**

**Original obligations:** FR-005, FR-008, FR-009, FR-018; SC-002; T018, T020, T025, T027.
**Expected/actual/impact:** [Assessment citation repair](../../apps/agents/risk_assessment/agent.py#L156) and
[legacy recommendation repair](../../apps/agents/risk_assessment/agent.py#L438) run only when no ID appears, so a
partially cited output remains incomplete. The assessment prompt includes IDs/severity/confidence but not the
actual hazard measurements, locations, freshness, provenance, or assumptions required to explain impact.
**Developer:** Feed a bounded, trusted evidence context into the risk prompt; append each missing ID individually
on every supported path. Carry stale/conflicting/unverified-input annotations into final text. Replace the legacy
API's invented 0.85/high/empty-assessment context with a validated assessment or explicitly limited compatibility contract.
**Tester positive:** Extend [LLM contracts](../../tests/contract/test_risk_assessment_llm.py#L4) and replay/pipeline tests
with FX-4 outputs citing all and only one of several input IDs; assert every contributor remains traceable.
**Tester negative:** Omitted facts may not be represented as supplied measurements or fabricated modelled impact.
**Tester edge:** Prefix-like IDs (`sig-1`, `sig-10`), long ID lists, no signals, and model output containing a stale summary.
**Dependencies/acceptance:** AUD-012-004, AUD-012-011, AUD-012-012; V1/V2. Both public and legacy surfaces satisfy the chosen contract.

### AUD-012-016: Generate Evidence-Based Recommendation Types

- [ ] AUD-012-016 **P2: Implement coordination generation, task-based triggers, and approval configuration.**

**Original obligations:** FR-017, FR-019, FR-021, FR-022, FR-024; US3; T028, T030, T031, T032, T033, T034, T036.
**Expected/actual/impact:** [Type selection](../../apps/agents/risk_assessment/agent.py#L271) never adds coordination.
[Coordination detection](../../apps/agents/risk_assessment/agent.py#L380) treats certain categories as tasks without
task evidence. [Resource handoffs](../../apps/agents/risk_assessment/agent.py#L520) check only recommendation type.
Approval level is hardcoded, and no route-risk assessment is derived by the category map.
**Developer:** Define structured coordination evidence and multi-agency triggers; generate the required types
from assessment facts, including route threats, and distinguish recommendation creation from escalation eligibility.
Read per-type approval overrides with a safe default. Retain numeric public-alert/evacuation thresholds already present.
**Tester positive:** Extend [escalation contracts](../../tests/contract/test_risk_assessment_escalation.py#L128) with real
assessment generation: route risk/high/0.6; public alert/0.7; low-confidence but fresh coordination tasks.
**Tester negative:** No tasks means no resource handoff; moderate/0.59 evacuation and unsupported types remain for review.
**Tester edge:** Empty task list, false flags, multiple generated types, custom approval level, and all-stale tasks held by AUD-012-005.
**Dependencies/acceptance:** AUD-012-005, AUD-012-007, AUD-012-014, AUD-012-031; V1/V2. Types, task evidence, and routing agree.

### AUD-012-017: Keep Degraded Text, Scores, and Methods Consistent

- [ ] AUD-012-017 **P2: Finalize penalties before rendering and define recommendation-only fallback behavior.**

**Original obligations:** FR-007, FR-031, FR-032; US7; T054, T055, T056.
**Expected/actual/impact:** [Template creation](../../apps/agents/risk_assessment/agent.py#L118) precedes the 20%
penalty/severity recomputation. The summary can show pre-penalty confidence/severity while fields show different
values. Recommendation generation makes another independent LLM call and can diverge in method from the assessment.
Extrapolation can add confidence after penalties; partial missing inputs have no penalty at all.
**Developer:** Define raw, intermediate, and final scores; apply missing-input, contradiction, fallback, and stale
safety policy exactly once in the approved order. Render text from final values and preserve per-call generation
metadata. Decide how recommendation-only fallback affects its confidence without silently changing FR-031.
**Tester positive:** FX-4 in the existing pipeline/reproducibility homes checks 0.8 x 0.7 x 0.8 = 0.448 before any
explicitly authorized extra adjustment; text and fields match.
**Tester negative:** Pre-penalty high text with medium/low fields and repeated fallback penalty application are rejected.
**Tester edge:** Crossing 0.4/0.6/0.7, recovery between assessment and recommendation, and extrapolation under stale holds.
**Dependencies/acceptance:** AUD-012-004, AUD-012-005, AUD-012-012, AUD-012-031; V1/V2. Every adjustment is explainable and audited.

### AUD-012-018: Store Replay-Complete Inputs and Configuration

- [ ] AUD-012-018 **P2: Make persisted snapshots sufficient to reconstruct semantic outputs.**

**Original obligations:** FR-025, FR-026; SC-004; US5; T042, T043, T044, T045.
**Expected/actual/impact:** [Snapshot](../../apps/agents/risk_assessment/agent.py#L202) stores a selected subset,
omitting risk direction/parameter, population/coordination payload, location, disaster type, and active threshold
values. Prompt version is hardcoded. [Hashing](../../apps/agents/risk_assessment/config.py#L123) does not describe
all active inputs; [extrapolation](../../apps/agents/risk_assessment/extrapolation.py#L67) substitutes wall time for
missing timestamps. Temperature zero is correctly inherited from the shared mixin, but is not full reproducibility.
**Developer:** Persist a versioned complete normalized snapshot, resolved policy/config values, model/deployment
and prompt versions, and explicit clock/order semantics. Hash canonical active configuration; record separate
model revisions. Provide replay from stored evidence, not caller-supplied duplicate inputs.
**Tester positive:** Extend [replay contracts](../../tests/contract/test_risk_assessment_reproducibility.py#L126) using
FX-1/FX-4: reconstruct from snapshot only and match category, severity, confidence level, and recommendation types.
**Tester negative:** A population/task/direction/prompt/config change must be captured and attributable.
**Tester edge:** Missing/equal timestamps, reordered inputs, model upgrade, template replay, and restart.
**Dependencies/acceptance:** AUD-012-004, AUD-012-014, AUD-012-017, AUD-012-031; V1/V2. No unrecorded input controls semantic output.

### AUD-012-019: Complete Source Trust and Freshness Correlation

- [ ] AUD-012-019 **P2: Connect trust/diversity evidence and resolve freshness cancellation semantics.**

**Original obligations:** FR-007, FR-011, FR-014, FR-015; T010, T015, T020; CHK018-CHK024 obligations.
**Expected/actual/impact:** [Weights](../../apps/agents/risk_assessment/config.py#L106) support three literal kinds;
[correlation](../../apps/agents/risk_assessment/correlation.py#L60) computes diversity/unverified reliance, but the
pipeline does not persist/render them. Unknown kinds use social weight without being counted as unverified.
The documented normalized formula cancels freshness for a single signal or equal-freshness inputs, conflicting
with the narrative that stale inputs reduce confidence.
**Developer:** Map governed trust kinds to explicit weights and identities, handle unknown/unverified kinds,
define geographic/handoff correlation scope and diversity contribution, and document the freshness policy decision.
Preserve the published formula unless changed through governance; do not hide a semantic change in a helper.
**Tester positive:** Use [correlation tests](../../tests/unit/test_risk_assessment_correlation.py#L34) with exact
weighted results for authoritative/IoT/social fixtures and persisted source-analysis annotations.
**Tester negative:** Unknown/crowd-dominated evidence cannot be labelled authoritative or silently lose its warning.
**Tester edge:** Single source, duplicate sources, all equal freshness, zero denominator, and invalid/nonfinite inputs.
**Dependencies/acceptance:** AUD-012-004, AUD-012-005, AUD-012-031; V1/V2. Confidence behavior and explanatory metadata agree.

### AUD-012-020: Attach and Validate Structured Hazard Maps

- [ ] AUD-012-020 **P2: Connect spatial output to the assessment contract without conflating severity scales.**

**Original obligations:** HazardAssessment/HazardMap entities; FR-010d; T005, T020; CHK071/CHK072/CHK073.
**Expected/actual/impact:** [HazardMapGenerator](../../apps/agents/risk_assessment/hazard_map.py#L29) exists, but S3
found no production caller and [assessment construction](../../apps/agents/risk_assessment/agent.py#L229) omits it.
The helper expects numeric severity 1-5, while the domain expects four named levels; it returns a Feature, not
the complete embedded map contract. [Model tests](../../tests/unit/test_risk_assessment_models.py#L249) accept
latitude/longitude dictionaries as "GeoJSON".
**Developer:** Assign ownership of geometry/population sources, validate coordinate system and Polygon output,
adapt severity explicitly, and populate confidence, time horizon, hazard type and population evidence. Keep web
rendering and detailed evacuation routing out of scope.
**Tester positive:** Extend existing model/pipeline tests with known AU points/polygons and a sourced population fixture.
**Tester negative:** Invalid/unclosed geometry, absent coordinates, unsupported severity, or unsourced population
must not become a plausible map centred on zero coordinates.
**Tester edge:** Disjoint geometry, empty inputs, coastal extents, and optional population/time horizon consistency.
**Dependencies/acceptance:** AUD-012-004, AUD-012-014, AUD-012-021, AUD-012-031; V1/V2. Stored maps satisfy the agreed entity shape.

### AUD-012-021: Enforce Data and Configuration Invariants

- [ ] AUD-012-021 **P2: Validate derived fields, related-incident metadata, lifecycle state, and configuration bounds.**

**Original obligations:** FR-007, FR-010b, FR-010c, FR-017, FR-029; T003, T004, T005, T006, T007, T008.
**Expected/actual/impact:** [HazardAssessment](../../packages/domain/src/domain/models/hazard_assessment.py#L18)
allows missing validity and confidence-level disagreement; [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L7)
lacks related-incident/lineage metadata. [Audit models](../../apps/agents/risk_assessment/models.py#L89) default
mandatory context to blanks. [Config validation](../../apps/agents/risk_assessment/config.py#L93) validates new LLM
settings but not core weights, thresholds, durations, or buffer capacity.
**Developer:** Enforce producer-boundary invariants with deliberate backward compatibility for older shared model
callers; add required optional metadata without enabling cross-incident correlation. Validate finite ranges,
nonnegative durations/capacities, categorical derivation, and supported transitions; avoid silently clamping bad evidence.
**Tester positive:** Extend [model tests](../../tests/unit/test_risk_assessment_models.py#L203) and
[config tests](../../tests/unit/test_risk_assessment_config.py#L73) with full records and all documented overrides.
**Tester negative:** Inconsistent level/score, absent required scoped context, invalid geometry and out-of-range/nonfinite config fail.
**Tester edge:** Confidence boundaries, legacy minimal records under an explicit compatibility policy, unknown optional variables.
**Dependencies/acceptance:** AUD-012-009, AUD-012-031; V1. Shared consumers remain compatible under a documented migration boundary.

### AUD-012-022: Reconcile Complete Structured Audit Records

- [ ] AUD-012-022 **P2: Record required processing decisions and verify completeness per handoff.**

**Original obligations:** FR-028, FR-029, SC-006; US4-AS2, US6; T004, T019, T040, T041, T051, T052.
**Expected/actual/impact:** [Finalization](../../apps/agents/risk_assessment/pipeline.py#L773) measures duration but
does not reconcile stage records. [Contradiction audit](../../apps/agents/risk_assessment/pipeline.py#L288) uses
zero confidence and no pair identities. Many records have default duration/version/model/signal context; downstream
audit uses the inbound ID rather than a structured outbound-event link. Recovery/safety decisions are absent.
**Developer:** Establish the canonical schema against FR-029, add explicit outbound event and structured override
metadata, record factual durations/rationale and intermediate scores, and reconcile required stage/branch records
against persisted or durably buffered outcomes. Log actionable discrepancies, not unconditional completed status.
**Tester positive:** Extend [pipeline](../../tests/unit/test_risk_assessment_pipeline.py#L118) and
[bushfire audit tests](../../tests/simulation/test_bushfire_risk_assessment.py#L183) with an expected per-handoff decision ledger.
**Tester negative:** Drop/duplicate a required record; finalization must detect the discrepancy. No unsafe raw LLM text in audit.
**Tester edge:** Rejection, duplicate, no contradiction, partial signals, multiple recommendations/targets, dead letter, recovery, override.
**Dependencies/acceptance:** AUD-012-007, AUD-012-011, AUD-012-012, AUD-012-024; V1/V2. Every applicable step has valid causal links.

### AUD-012-023: Make Audit Buffer Recovery Durable and Ordered

- [ ] AUD-012-023 **P2: Wire recovery and prevent spill/flush failures from losing or misordering audit evidence.**

**Original obligations:** FR-029, FR-030, FR-034; T047, T048, T049, T050.
**Expected/actual/impact:** [Writer](../../apps/agents/risk_assessment/audit.py#L42) creates records append-only,
but sets `flush_source=direct` after writing. Spill failures only log and no rotation exists. [Flush](../../apps/agents/risk_assessment/audit.py#L113)
continues into files after a memory failure and past failed file lines, lacks a caller, and treats duplicate-create
replay as failure. Buffered memory is not durable across restart; file-spill health never resets its cumulative count.
**Developer:** Add scheduled/recovery/shutdown ownership, durable ordered queue semantics, safe bounded rotation,
duplicate-safe create verification, and failure-visible backpressure. Define annotations before serialization and
report remaining backlog accurately. Provision a writable durable spill location for the non-root container.
**Tester positive:** FX-7 in [audit tests](../../tests/unit/test_risk_assessment_audit.py#L94) drains all tiers in causal order,
with exact annotation values and no updates/deletes to stored audit events.
**Tester negative:** Disk full, partial Cosmos recovery, corrupt line, or lost acknowledgment may not drop later/earlier records silently.
**Tester edge:** Restart during flush, simultaneous write/flush, capacity boundary, rotation, duplicate create, and recovery health.
**Dependencies/acceptance:** AUD-012-001, AUD-012-022, AUD-012-027; V1/V2/V4. Reconciliation proves zero logical record loss.

### AUD-012-024: Deliver and Surface Real Dead Letters

- [ ] AUD-012-024 **P2: Wire bounded asynchronous delivery and durable operator-visible failure handling.**

**Original obligations:** FR-020, FR-021, FR-022, FR-023, FR-024; SC-007; US6-AS3; T029, T030c, T035, T036.
**Expected/actual/impact:** [Retry helper](../../apps/agents/common/handoffs.py#L124) exists with 0.5/1-second sleeps
and three total attempts, not three retries after the first attempt. [Pipeline defaults](../../apps/agents/risk_assessment/pipeline.py#L49)
have no sender and a dead-letter callback that only returns a string. Pending handoffs can be returned without delivery.
**Developer:** Resolve attempt terminology, inject an async sender and real dead-letter persistence/operator surface,
carry outbound IDs and delivery status into structured audit, and bound delivery independently from assessment timing.
Retain safe processing when a downstream agent is unavailable; do not confuse handoff creation with delivery.
**Tester positive:** FX-5 in existing escalation/pipeline/Service Bus homes verifies exact attempts, backoff, payload and one successful delivery.
**Tester negative:** All attempts fail -> one durable dead letter and commander-visible record; below-threshold records are retained, not sent.
**Tester edge:** Timeout after remote acceptance, cancellation, async callback errors, and multiple targets under the 15-second budget.
**Dependencies/acceptance:** AUD-012-001, AUD-012-007, AUD-012-013, AUD-012-031; V1/V2/V4. Operator retrieval proves failure is surfaced.

### AUD-012-025: Report Real, Bounded Health

- [ ] AUD-012-025 **P2: Replace placeholder queue/store health and remove unbounded request-time probing.**

**Original obligations:** FR-033, FR-034; EC-06; T057; complete health contract.
**Expected/actual/impact:** [Health](../../apps/agents/risk_assessment/agent.py#L631) makes a synchronous LLM call
with the client's default timeout, infers signal health from object presence, and always reports queue 0/healthy.
The unhealthy queue branch is unreachable. Current [endpoint tests](../../tests/unit/test_risk_assessment_endpoints.py#L57)
do not inject queue outage or prove a one-second bound.
**Developer:** Own background/cached bounded checks with freshness timestamps, real queue depth/connectivity,
store health and audit backlog. Preserve degraded versus unhealthy distinctions and wire probe behavior to actual
readiness/liveness without restarting on an LLM-only outage. Report probe execution failure explicitly.
**Tester positive:** Existing endpoint tests plus fake clock/check providers validate the full response and normal sub-second response.
**Tester negative:** Offline queue reports unhealthy, slow LLM cannot block health, absent store is not healthy.
**Tester edge:** Stale cached check, audit spill recovery, queue backpressure, and checker failure -> contract-appropriate status/code.
**Dependencies/acceptance:** AUD-012-001, AUD-012-023, AUD-012-027; V1/V4. Restart/redelivery behavior requires later platform evidence.

### AUD-012-026: Emit the Contracted Telemetry and Alerts

- [ ] AUD-012-026 **P2: Connect metric values, causal traces, custom events, and alert configuration.**

**Original obligations:** NFR-002; T059, T060, T061; full telemetry contract.
**Expected/actual/impact:** [Registry](../../apps/agents/risk_assessment/telemetry.py#L85) declares 19 risk metrics,
but six gauges and safety/version counters have no risk emission path. Gauges are represented as up/down counters.
Nested LLM/safety/version/delivery spans and outbound parent propagation are absent; VersionConflict is declared
but not called. [Tests](../../tests/unit/test_risk_assessment_telemetry.py#L67) mostly assert that calls do not raise.
**Developer:** Emit meaningful sampled/ratio values, required stage/child spans, inbound/outbound correlation,
and all seven event types. Configure the exporter on the selected host and wire the eight specified alert policies
with bounded cardinality. Count attempts/intake/rejections accurately, not just successful transitions.
**Tester positive:** Capture an in-memory OTel exporter in the existing telemetry/pipeline homes; assert names, units,
values, dimensions, parentage and event fields through real processing, including version contention.
**Tester negative:** Missing exporter or no-op provider cannot be treated as evidence of delivered metrics; alert fixtures exercise breach states.
**Tester edge:** Ratio denominator zero, repeated gauge observations, tenant separation, exceptions, and high-cardinality incident labels.
**Dependencies/acceptance:** AUD-012-001, AUD-012-022, AUD-012-024, AUD-012-025, AUD-012-027; V1/V4. See detailed contract ledger below.

### AUD-012-027: Integrate Infrastructure and Queue-Based Scaling

- [ ] AUD-012-027 **P2: Make infrastructure, container startup, identity, and queue scaling describe one deployable service.**

**Original obligations:** NFR-001; FR-001, FR-029, FR-030, FR-033; T065; plan regional/security obligations.
**Expected/actual/impact:** [Risk module](../../infra/modules/risk-assessment.bicep#L63) declares containers/queue,
but S5 found no caller. Its [HTTP scaler](../../infra/modules/risk-assessment.bicep#L181) contradicts queue-based
scaling; it targets 8081 while the supplied [container](../../apps/agents/Dockerfile#L46) starts dispatcher on 8080.
The module has Cosmos/receiver grants but no shown sender or registry-pull grant for that identity. Runtime store,
queue, database and quickstart environment names differ; audit spill is not provisioned.
**Developer:** Align the selected host/image/port/health probes and settings, invoke the module from the authoritative
deployment or formally document a replacement, supply least-privilege sender/receiver/Cosmos/registry access,
queue-depth scaling, and durable spill. Validate AU storage/telemetry/DR boundaries and current, bounded model
carve-out policy; do not infer an unapproved non-AU exemption or rewrite policy. Follow repository AVM/policy gates
when a later implementation is authorized.
**Tester positive:** Later static/IaC and isolated staging checks confirm module inclusion, container startup, queue scaling,
identity access, partition keys and no audit TTL against deployment outputs.
**Tester negative:** Wrong image port, absent sender/pull grant, non-AU regulated storage, or unwired settings fail readiness.
**Tester edge:** Scale-out/restart, registry image pull, DR without LLM, and non-root spill permissions.
**Dependencies/acceptance:** AUD-012-001, AUD-012-023, AUD-012-025, AUD-012-031; V4. No infrastructure was compiled or deployed here.

### AUD-012-028: Replace Vacuous and Mislabelled Test Coverage

- [ ] AUD-012-028 **P2: Exercise production operations and assert the actual requirements in existing test homes.**

**Original obligations:** T007, T008, T009, T010, T011, T012, T013, T030b, T030c, T037, T042, T047, T062, T063, T064.
**Expected/actual/impact:** [Pipeline tests](../../tests/unit/test_risk_assessment_pipeline.py#L118) use nonnegative
counters/conditional assertions. [Cosmos tests](../../tests/integration/test_risk_assessment_cosmos.py#L65) write
audit records under assessment/recommendation names. [Service Bus tests](../../tests/integration/test_risk_assessment_service_bus.py#L111)
call `complete()` themselves. The [bushfire fixture](../../tests/simulation/test_bushfire_risk_assessment.py#L148)
passes a synchronous callback to an awaited delivery helper. Passing these helpers would not establish end-to-end delivery.
**Developer:** Repair the specific suites alongside their owning fixes; use stateful bounded fakes and actual adapters,
install LLM/safety fakes before construction, enforce no-network hermetic tests, and preserve meaningful negative assertions.
Retain existing test files; propose new fixtures only where an existing home cannot represent the case.
**Tester positive:** Run V1/V2 after repair and verify operation logs/read-back plus complete audit/outbound sets.
**Tester negative:** Deliberately omit persistence, delivery, penalty, or one audit stage and verify the focused assertion fails.
**Tester edge:** Async/sync contract misuse, simulated outage/restart, exactly-at-threshold input, and absent optional dependency.
**Dependencies/acceptance:** Respective AUD-012-001 through AUD-012-027 fixes, referenced individually by their test cases;
no broad test pass substitutes for missing assertions. Red-before-fix evidence must be captured prospectively, not invented.

### AUD-012-029: Establish Measured Latency and Capacity Acceptance

- [ ] AUD-012-029 **P2: Measure the actual 5/10/15-second boundaries and 100-assessment concurrency target.**

**Original obligations:** NFR-001; SC-001, SC-005, SC-007; T022, T059, T060, T065, T066; CHK009/CHK067/CHK098/CHK102.
**Expected/actual/impact:** The [pipeline](../../apps/agents/risk_assessment/pipeline.py#L648) is synchronous across
retrieval, generation, multiple recommendation calls, delivery and audit. Each generation has its own timeout;
the final timer includes downstream work. No measured risk load result is present in local evidence. The newer
[staging fan-out test](../../tests/integration/test_risk_assessment_auto_fanout.py#L113) unconditionally skips.
**Developer:** Define timestamps and approved load profile; instrument receipt/ack, durable assessment completion,
downstream delivery, rejection/drop accounting and outage recovery. Bound or schedule dependencies without
abandoning slow assessments. Add realistic load coverage in existing integration/simulation homes or explicitly
proposed load fixtures after implementation is ready.
**Tester positive:** V3/V4 later measures at least 100 concurrent assessments, normal and LLM-outage workloads,
and records p50/p95/p99 and exact sample counts for each boundary.
**Tester negative:** Slow stores/LLM/downstream cause an SLA breach event with actual duration, not silent loss or fabricated success.
**Tester edge:** Burst/ramp/sustained load, queue backlog, worker restart, and all-stale/missing inputs under load.
**Dependencies/acceptance:** AUD-012-001, AUD-012-007, AUD-012-024, AUD-012-026, AUD-012-027, AUD-012-031.
Retain reproducible measurements and prove zero handoff drop in the specified outage window.

### AUD-012-030: Supply Domain and Commander Evaluation Evidence

- [ ] AUD-012-030 **P2: Define and execute the labelled contradiction and explanation-clarity acceptance gates.**

**Original obligations:** SC-003, SC-008; CHK001/CHK008/CHK028/CHK080/CHK082; T066 validation dependency.
**Expected/actual/impact:** [Contradiction tests](../../tests/unit/test_risk_assessment_correlation.py#L106) cover a
few synthetic directions, not a labelled geographic benchmark. [SC-008](spec.md#L279) requires a commander survey;
no sample, rubric anchors, responses or measured result appears in the local artifacts. Country calibration stubs
are not evidence of AU hazard-prediction accuracy.
**Developer:** With authorized domain reviewers, define labelled AU cases, geographical negatives, sampling and
refresh policy, and an explicit clarity/traceability/decision-confidence rubric and minimum survey cohort. Resolve
prediction-accuracy questions as requirements decisions rather than inventing numerical targets in implementation.
**Tester positive:** Extend existing correlation/simulation homes with labelled fixtures, compute detection >=95%,
and later record >=90% qualifying commander ratings with denominators and rubric interpretation.
**Tester negative:** Geographic false positives, missing citations, stale explanation values, and below-threshold results fail the gate.
**Tester edge:** Small sample bias, different AU hazards/providers, ambiguous trajectories, and dissenting human ratings.
**Dependencies/acceptance:** AUD-012-011, AUD-012-014, AUD-012-015, AUD-012-017, AUD-012-031; V5. No survey or approval was performed here.

### AUD-012-031: Resolve Conflicting Contracts Before Behavior Changes

- [ ] AUD-012-031 **P2: Record authoritative resolutions for conflicting version, timing, confidence, and runtime contracts.**

**Original obligations:** All clarification amendments; FR-006, FR-007, FR-010b, FR-019, FR-022, FR-029, FR-031;
T017, T022, T031, T034, T043, T050, T058, T060; plan/checklist gates.
**Expected/actual/impact:** The [research](research.md#L49), [data model](data-model.md#L90),
[pipeline contract](contracts/assessment-pipeline.md#L17), [task list](tasks.md#L1) and
[clarifications](spec.md#L281) disagree on important boundaries. The current constitution and replacement runtime
introduce further scope changes that cannot be resolved by a checked box or code comment.
**Developer:** Obtain owner decisions on integer versus UUID fallback, old versus type-qualified IDs, ack versus
completion, immediate versus expiry-time supersession, freshness cancellation, RA task evidence, zero-confidence
holds, override lifecycle, canonical audit fields, semantic versus exact replay, and three retries versus attempts.
Reconcile eight-stage documentation with the added extrapolation stage, 19 versus 20 metrics, and current AU model
carve-out/change-control rules. Do not change original artifacts as part of this audit.
**Tester positive:** V6 later verifies each decision maps to one requirement, contract and executable acceptance case.
**Tester negative:** Unresolved contradictions block completion; MAF/dispatcher/UI presence cannot be used as an implicit waiver.
**Tester edge:** Backward-compatible callers, governed default changes, old evidence retention, and cross-spec ownership disputes.
**Dependencies/acceptance:** Product/architecture/domain/security owners as appropriate. Decisions are approved and versioned,
with amended behavior traceable to specific tests; no retrospective approvals or checkbox changes by this report.

### AUD-012-032: Correct and Actually Rehearse the Quickstart

- [ ] AUD-012-032 **P3: Repair launch/settings/path instructions and capture a real end-to-end rehearsal.**

**Original obligations:** T066; complete quickstart; US1 and operational acceptance.
**Expected/actual/impact:** [Quickstart launch](quickstart.md#L64) promises a queue consumer that startup does not
create. Repeated `cd apps/agents` and test paths reference repository-root tests from the wrong location; the named
contract pipeline test is absent in S4, while [unit pipeline tests](../../tests/unit/test_risk_assessment_pipeline.py#L1)
exist. Its [settings](quickstart.md#L29) differ from current runtime/infra names and databases.
**Developer:** After host fixes, document one working directory, approved configuration/authentication, explicit
offline versus integration mode, correct ports, real fixture submission, durable output retrieval and cleanup.
Keep keys out of evidence and preserve the honest unchecked historical execution state.
**Tester positive:** V1/V2/V4 later runs the corrected rehearsal from a clean prepared environment and captures commands,
timestamps, revision, output record IDs and expected health/intake/recommendation/audit results.
**Tester negative:** Missing prerequisites or disconnected stores must be visible, not accepted as healthy synthetic success.
**Tester edge:** Offline fallback, PowerShell paths, restart, no live credentials, and rollback/cleanup of isolated fixtures.
**Dependencies/acceptance:** AUD-012-001, AUD-012-007, AUD-012-025, AUD-012-027, AUD-012-028. T066 stays UNVERIFIED until actual evidence exists.

### AUD-012-033: Repair Evidence Traceability Without Inventing Approval

- [ ] AUD-012-033 **P3: Link real review/validation records and repair the missing HYP-010 evidence chain.**

**Original obligations:** ASM-034/ASM-035, PER-028/PER-029, HYP-010, SCP-031/SCP-032/SCP-033; T053, T066;
all plan gate declarations and checklist review obligations.
**Expected/actual/impact:** [Plan gates](plan.md#L46) say PASS and [research](research.md#L156) calls the buffer
pattern production-validated, but no execution/sign-off attachment is provided locally. Templates assert
pre-approval in a docstring. [HYP-010](spec.md#L330) names an absent, nonconforming `HYP-HYP-010.md` stub;
the referenced [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1) is portfolio-wide and the
named comparator was not found. "Validated" persona cross-references do not supply practitioner attestation.
**Developer:** Repair the evidence chain through the owning governance feature, attach actual revision-bound
actor/SME/security/template reviews and execution artifacts where available, and label missing approval explicitly.
Use the evidence and persona contracts, preserve historical originals, and keep PH/JP/BD scope deferred until its
named gates clear. Do not fabricate consultation logs, survey results, or per-012 rubric scores.
**Tester positive:** V6 later verifies every claimed approval has identity, role, date, revision/scope and a resolvable
artifact; HYP-010 links to a valid stub and an attributable comparison.
**Tester negative:** Checked boxes, filename matches, proxy-only persona claims, and portfolio scores cannot pass as individual validation.
**Tester edge:** Conditional/expired approvals, dissent, changed configuration, and deferred hypothesis promotion by a later feature.
**Dependencies/acceptance:** AUD-012-030, AUD-012-031 and authorized reviewers. Existing country stubs remain Not tested unless genuine
measurements and the separate promotion process justify a change.

## Requirement and Success-Criterion Coverage

Every original FR, NFR and SC has one row. Evidence describes the strongest inspected source support and the
remaining gap; numerical outcome claims remain unverified without measurements.

| ID | Status | Evidence and gap | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Intake](../../apps/agents/risk_assessment/pipeline.py#L97) lacks real consumer/schema/incident boundary and measured acknowledgment. | AUD-012-001, AUD-012-002, AUD-012-029 |
| FR-002 | PARTIAL | [Retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) reads supplied IDs only if injected; actual producer omits IDs and fallback fabricates signals. | AUD-012-003, AUD-012-004 |
| FR-003 | PARTIAL | [TTL cache](../../apps/agents/risk_assessment/dedup.py#L35) works sequentially; not atomic/durable across workers or failure retries. | AUD-012-010 |
| FR-004 | MISSING | S2/S3: [validation](../../apps/agents/risk_assessment/pipeline.py#L97) has no incident lookup/dependency. Rejected event spelling also differs across originals. | AUD-012-002, AUD-012-031 |
| FR-005 | PARTIAL | [Assessment fields](../../apps/agents/risk_assessment/agent.py#L229) exist; fabricated/partial input, persistence and semantic impact gaps remain. | AUD-012-004, AUD-012-007, AUD-012-014, AUD-012-015 |
| FR-006 | CONFLICT | [Version fallback](../../apps/agents/risk_assessment/versioning.py#L127) is unreserved; UUID research versus integer model/old clarification unresolved. | AUD-012-006, AUD-012-031 |
| FR-007 | PARTIAL | [Weighted mean](../../apps/agents/risk_assessment/correlation.py#L60) and [level helper](../../apps/agents/risk_assessment/models.py#L72) exist; diversity/stale/missing integration and derived validation incomplete. | AUD-012-005, AUD-012-017, AUD-012-019, AUD-012-021 |
| FR-008 | PARTIAL | [Mixin](../../apps/agents/common/llm_mixin.py#L64) provides safety/fallback; risk prompt lacks evidence context and reachable integration. | AUD-012-001, AUD-012-012, AUD-012-015 |
| FR-009 | PARTIAL | [Summary repair](../../apps/agents/risk_assessment/agent.py#L156) accepts partial citations. | AUD-012-015 |
| FR-010 | PARTIAL | [Default mappings](../../apps/agents/risk_assessment/severity.py#L11) present; per-incident configuration and upstream extra categories not reconciled. | AUD-012-014 |
| FR-010a | PARTIAL | [Disaster severity table](../../apps/agents/risk_assessment/severity.py#L34) present; no incident/geographic scenario policy selection. | AUD-012-014, AUD-012-030 |
| FR-010b | PARTIAL | [Validity calculation](../../apps/agents/risk_assessment/agent.py#L114) exists; no scoped lifecycle/query/escalation guard found. | AUD-012-013, AUD-012-031 |
| FR-010c | PARTIAL | [Assessment related IDs](../../packages/domain/src/domain/models/hazard_assessment.py#L48) exist; recommendation metadata and input ownership checks missing. | AUD-012-003, AUD-012-021 |
| FR-010d | PARTIAL | [Severity](../../apps/agents/risk_assessment/severity.py#L62) uses category/confidence/population; calibrated scenario boundaries and source justification absent. | AUD-012-014, AUD-012-020 |
| FR-011 | PARTIAL | [Weighted formula](../../apps/agents/risk_assessment/correlation.py#L60) implemented; geography and governed source mapping incomplete. | AUD-012-011, AUD-012-019 |
| FR-012 | PARTIAL | [Pairs](../../apps/agents/risk_assessment/correlation.py#L143) exist; names are kinds, geography missing, recommendation perspectives not enforced. | AUD-012-011 |
| FR-013 | PARTIAL | [Single penalty](../../apps/agents/risk_assessment/correlation.py#L199) present; durable review/pair audit incomplete. | AUD-012-011, AUD-012-022 |
| FR-014 | PARTIAL | [Unverified flag](../../apps/agents/risk_assessment/correlation.py#L118) not rendered/persisted; unknown kinds are not flagged consistently. | AUD-012-019 |
| FR-015 | PARTIAL | [Stale IDs](../../apps/agents/risk_assessment/correlation.py#L93) and template note present; LLM summary lacks enforced stale annotations. | AUD-012-005, AUD-012-019 |
| FR-016 | MISSING | S2/S3: [generation](../../apps/agents/risk_assessment/agent.py#L76) and [dispatch](../../apps/agents/risk_assessment/pipeline.py#L512) do not consume all-stale safety flag. | AUD-012-005 |
| FR-017 | PARTIAL | [Generator](../../apps/agents/risk_assessment/agent.py#L309) fills primary fields; coordination unreachable, legacy context invented, durability incomplete. | AUD-012-007, AUD-012-015, AUD-012-016 |
| FR-018 | PARTIAL | [Generic generator](../../apps/agents/risk_assessment/agent.py#L352) appends missing IDs; [legacy API](../../apps/agents/risk_assessment/agent.py#L438) does not repair partial citations. | AUD-012-015 |
| FR-019 | PARTIAL | [Recommendation construction](../../apps/agents/risk_assessment/agent.py#L359) defaults correctly but has no per-type environment override. | AUD-012-016 |
| FR-020 | PARTIAL | [Numeric builder](../../apps/agents/risk_assessment/agent.py#L462) and [contract assertions](../../tests/contract/test_risk_assessment_escalation.py#L31) support threshold/payload; delivery host missing. | AUD-012-001, AUD-012-024 |
| FR-021 | PARTIAL | [Evacuation builder](../../apps/agents/risk_assessment/agent.py#L491) supports thresholds/payload; route policy, inactive-assessment guards and host incomplete. | AUD-012-013, AUD-012-016, AUD-012-024 |
| FR-022 | PARTIAL | [Resource builder](../../apps/agents/risk_assessment/agent.py#L520) is type-based, not actual coordination-task-based. | AUD-012-016, AUD-012-024 |
| FR-023 | PARTIAL | [Retry helper](../../apps/agents/common/handoffs.py#L124) exists; attempts/retries conflict and durable commander-visible dead letters unwired. | AUD-012-024, AUD-012-031 |
| FR-024 | PARTIAL | [No-escalation branch](../../apps/agents/risk_assessment/pipeline.py#L635) logs human review without proving persistence; RA task gate weak. | AUD-012-007, AUD-012-016 |
| FR-025 | PARTIAL | [Snapshot](../../apps/agents/risk_assessment/agent.py#L202) omits controlling facts/config values/model revision. | AUD-012-018 |
| FR-026 | PARTIAL | [Default temperature zero](../../apps/agents/common/llm_mixin.py#L64) supported; wall-clock-dependent extrapolation and incomplete replay prevent full source claim. | AUD-012-018, AUD-012-031 |
| FR-027 | PARTIAL | [Output scope](../../apps/agents/risk_assessment/pipeline.py#L41) and prefix guard exist, but input/override/partition enforcement incomplete. | AUD-012-003 |
| FR-028 | PARTIAL | [Pipeline audit writes](../../apps/agents/risk_assessment/pipeline.py#L826) cover core branches, not all safety/recovery/success steps. | AUD-012-012, AUD-012-022 |
| FR-029 | PARTIAL | [Canonical model](../../apps/agents/risk_assessment/models.py#L89) exists; mandatory context defaults, field-set conflict, duration/causal links incomplete. | AUD-012-022, AUD-012-031 |
| FR-030 | PARTIAL | [create_item](../../apps/agents/risk_assessment/audit.py#L70) and [no-TTL declaration](../../infra/modules/risk-assessment.bicep#L101) support intent; durable wired persistence/recovery not established. | AUD-012-023, AUD-012-027 |
| FR-031 | CONFLICT | [20% adjustment](../../apps/agents/risk_assessment/agent.py#L143) present; fallback category tables/text/severity and later confidence boost differ from strict rule-only wording. | AUD-012-014, AUD-012-017, AUD-012-031 |
| FR-032 | PARTIAL | [Retrieval catches](../../apps/agents/risk_assessment/pipeline.py#L199) permit survivors, but missing fraction/IDs are not carried into confidence/audit. | AUD-012-004 |
| FR-033 | PARTIAL | [Health schema](../../apps/agents/risk_assessment/agent.py#L631) exists; queue/store checks and one-second bound unsupported. | AUD-012-025 |
| FR-034 | PARTIAL | [Fallback](../../apps/agents/common/llm_mixin.py#L64) and audit tiers exist; counter/store/delivery recovery and no-loss semantics incomplete. | AUD-012-007, AUD-012-012, AUD-012-023, AUD-012-024 |
| FR-035 | PARTIAL | [Safety validation](../../apps/agents/common/llm_mixin.py#L151) replaces rejected output; required risk audit and review metadata are not propagated. | AUD-012-012, AUD-012-033 |
| FR-036 | PARTIAL | [System prompt](../../apps/agents/common/llm_client.py#L177) rejects embedded instructions but is not risk-specific; no inspected adversarial risk contract assertions. | AUD-012-012, AUD-012-015 |
| FR-037 | PARTIAL | [Override](../../apps/agents/risk_assessment/agent.py#L714) handles actions but lacks trusted identity, correct partition, durable structured metadata and fail-closed behavior. | AUD-012-008, AUD-012-009, AUD-012-022 |
| FR-038 | MISSING | S2/S3: [override upsert](../../apps/agents/risk_assessment/agent.py#L749) modifies the original; no linked recommendation version path found. | AUD-012-009 |
| NFR-001 | PARTIAL | [Risk scaler](../../infra/modules/risk-assessment.bicep#L181) is HTTP-based; host is unwired and no 100-concurrent measured assessment result inspected. | AUD-012-001, AUD-012-027, AUD-012-029 |
| NFR-002 | PARTIAL | [Telemetry registry](../../apps/agents/risk_assessment/telemetry.py#L85) is only partly emitted; gauges, nested spans, exporter/alerts require verification. | AUD-012-026 |
| SC-001 | UNVERIFIED | [Final timer/SLA logging](../../apps/agents/risk_assessment/pipeline.py#L773) exists but no actual receipt-to-persistence measurement. | AUD-012-029 |
| SC-002 | PARTIAL | [Any-ID guard](../../apps/agents/risk_assessment/agent.py#L156) violates all-input traceability; no 100% reconciliation evidence. | AUD-012-004, AUD-012-015, AUD-012-022 |
| SC-003 | UNVERIFIED | [Synthetic direction tests](../../tests/unit/test_risk_assessment_correlation.py#L106) do not measure a labelled geographic >=95% detection set. | AUD-012-011, AUD-012-030 |
| SC-004 | PARTIAL | [Replay assertions](../../tests/contract/test_risk_assessment_reproducibility.py#L26) compare caller-provided inputs, not snapshot-only replay with all controlling facts. | AUD-012-018, AUD-012-028 |
| SC-005 | UNVERIFIED | [Template fallback](../../apps/agents/common/llm_mixin.py#L202) supports continuity in source, not measured <=10 seconds/zero drop over an outage. | AUD-012-012, AUD-012-017, AUD-012-029 |
| SC-006 | PARTIAL | [Finalization](../../apps/agents/risk_assessment/pipeline.py#L773) has no record reconciliation; audit stage completeness is not proved. | AUD-012-022, AUD-012-023 |
| SC-007 | UNVERIFIED | [Dispatch/retry](../../apps/agents/risk_assessment/pipeline.py#L573) lacks a production sender and assessment-completion-to-delivery measurement. | AUD-012-024, AUD-012-029 |
| SC-008 | UNVERIFIED | [Survey obligation](spec.md#L279) has no local responses, cohort, anchored rubric or >=90% result. | AUD-012-030, AUD-012-033 |

## Acceptance Scenarios

Identifiers below are audit labels for the original numbered scenarios; no scenario was executed.

| Scenario | Status | Evidence and remaining obligation | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Assessment test](../../tests/simulation/test_bushfire_risk_assessment.py#L105) supports helper fields, but uses synthetic input and no actual incident lookup/durable host. | AUD-012-001, AUD-012-002, AUD-012-004, AUD-012-007 |
| US1-AS2 | PARTIAL | [Counter test](../../tests/unit/test_risk_assessment_versioning.py#L17) increments a mock; no-store and contention paths collide. | AUD-012-006 |
| US1-AS3 | PARTIAL | [Stale flag test](../../tests/unit/test_risk_assessment_correlation.py#L69) does not assert confidence reduction or LLM annotation. | AUD-012-005, AUD-012-019 |
| US1-AS4 | PARTIAL | [Read failures](../../apps/agents/risk_assessment/pipeline.py#L199) log IDs, but confidence/audit missing-input contract incomplete. | AUD-012-004 |
| US2-AS1 | PARTIAL | [Communication contracts](../../tests/contract/test_risk_assessment_escalation.py#L31) prove builder payload/threshold, not complete citations and delivered workflow. | AUD-012-015, AUD-012-024 |
| US2-AS2 | PARTIAL | [Below-threshold builder](../../tests/contract/test_risk_assessment_escalation.py#L39) returns None; durable human-review storage not proved. | AUD-012-007 |
| US2-AS3 | PARTIAL | [Generic recommendation](../../apps/agents/risk_assessment/agent.py#L359) sets approval/agent/method; legacy context and persistence incomplete. | AUD-012-007, AUD-012-015, AUD-012-016 |
| US3-AS1 | PARTIAL | [Evacuation contracts](../../tests/contract/test_risk_assessment_escalation.py#L73) test high/low cases, not route-risk production and delivery. | AUD-012-016, AUD-012-024 |
| US3-AS2 | PARTIAL | [Coordination predicate](../../apps/agents/risk_assessment/agent.py#L380) infers tasks from category; resource tests supply type directly. | AUD-012-016 |
| US3-AS3 | PARTIAL | [No-escalation test](../../tests/unit/test_risk_assessment_pipeline.py#L118) counts no delivery without a sender; review persistence unproved. | AUD-012-007, AUD-012-016, AUD-012-028 |
| US4-AS1 | PARTIAL | [Detector](../../apps/agents/risk_assessment/correlation.py#L143) finds opposing directions, not matching geography/actual named sources. | AUD-012-011 |
| US4-AS2 | PARTIAL | [Audit branch](../../apps/agents/risk_assessment/pipeline.py#L288) omits pair-specific sources and real before/after confidence. | AUD-012-011, AUD-012-022 |
| US4-AS3 | PARTIAL | [Consistent-input test](../../tests/unit/test_risk_assessment_correlation.py#L106) supports no flag; real source mapping/quality analysis incomplete. | AUD-012-019 |
| US5-AS1 | CONFLICT | [Narrative replay](spec.md#L75) implies identical output/version; [research](research.md#L172) explicitly uses semantic equivalence, while snapshot-only replay is absent. | AUD-012-018, AUD-012-031 |
| US5-AS2 | PARTIAL | [Config test](../../tests/contract/test_risk_assessment_reproducibility.py#L99) checks a hash; all model/config/prompt facts are not captured. | AUD-012-018 |
| US5-AS3 | PARTIAL | [Simulation test](../../tests/unit/test_risk_assessment_pipeline.py#L118) checks a counter with no sender; reads/context override permit scope disagreement. | AUD-012-003, AUD-012-028 |
| US6-AS1 | PARTIAL | [Core records](../../apps/agents/risk_assessment/pipeline.py#L97) exist but missing structured context/steps invalidate completeness. | AUD-012-022 |
| US6-AS2 | PARTIAL | [Assessment audit](../../apps/agents/risk_assessment/pipeline.py#L428) links ID/version/config, not complete source snapshot/contradiction evidence. | AUD-012-018, AUD-012-022 |
| US6-AS3 | PARTIAL | [Delivery audits](../../apps/agents/risk_assessment/pipeline.py#L573) lack consistent structured outbound ID and durable dead-letter surface. | AUD-012-024, AUD-012-022 |
| US7-AS1 | PARTIAL | [Fallback adjustment](../../apps/agents/risk_assessment/agent.py#L143) exists; summary fields, default severity and degradation records disagree. | AUD-012-012, AUD-012-014, AUD-012-017 |
| US7-AS2 | PARTIAL | [Circuit-breaker success](../../apps/agents/common/llm_mixin.py#L173) allows resumed LLM calls but risk recovery event is absent. | AUD-012-012 |
| US7-AS3 | PARTIAL | [Partial reads](../../apps/agents/risk_assessment/pipeline.py#L199) do not apply proportional confidence reduction or persist missing ID list. | AUD-012-004 |

## Edge Cases

| Edge | Original behavior | Status | Evidence and follow-up |
| --- | --- | --- | --- |
| EC-01 | Nonexistent incident rejected/audited; no assessment. | MISSING | [Intake](../../apps/agents/risk_assessment/pipeline.py#L97); no lookup in S2/S3. AUD-012-002. |
| EC-02 | All-stale inputs -> low, explicit staleness, no downstream handoff. | MISSING | [Flag](../../apps/agents/risk_assessment/correlation.py#L103) is not enforced by generation/escalation. AUD-012-005. |
| EC-03 | Duplicate delivery discarded with audit. | PARTIAL | [Cache](../../apps/agents/risk_assessment/dedup.py#L35) plus [duplicate branch](../../apps/agents/risk_assessment/pipeline.py#L126); concurrency/retry/restart gap. AUD-012-010. |
| EC-04 | Unsafe LLM output replaced and safety failure audited. | PARTIAL | [Mixin replacement](../../apps/agents/common/llm_mixin.py#L151) works in source; risk audit/review metadata missing. AUD-012-012. |
| EC-05 | Simulation data isolated; no live handoffs. | PARTIAL | [Prefix guard](../../apps/agents/risk_assessment/pipeline.py#L527) is not complete tenant enforcement. AUD-012-003. |
| EC-06 | Unhealthy status, platform restart, unprocessed redelivery. | PARTIAL | [Health queue placeholder](../../apps/agents/risk_assessment/agent.py#L669); no connected consumer/probe evidence; deployed restart outcome UNVERIFIED. AUD-012-001, AUD-012-025, AUD-012-027. |
| EC-07 | Ineligible recommendation produces no downstream handoff. | PARTIAL | [Type builders](../../apps/agents/risk_assessment/agent.py#L462) exist; resource-task eligibility and stored review path incomplete. AUD-012-007, AUD-012-016. |

## Original Task Coverage

Exact checkbox state is copied from the original list. Separate rows include the three suffixed IDs;
no original task is inferred complete merely because its box is checked. Test rows judge assertions as source,
not execution or historical red-before-green ordering.

| Original ID | Original state | Status | Concrete evidence and remaining gap | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Package export](../../apps/agents/risk_assessment/__init__.py#L3) exposes RiskAssessmentAgent. | None for scoped export. |
| T002 | [X] | IMPLEMENTED | [Dependency declarations](../../apps/agents/pyproject.toml#L10) include Cosmos, Service Bus and tenacity; installation not claimed. | None for declarations. |
| T003 | [X] | IMPLEMENTED | [Config](../../apps/agents/risk_assessment/config.py#L15) declares all data-model parameter entries; additional validation/integration gaps tracked separately. | AUD-012-021 |
| T004 | [X] | IMPLEMENTED | [Enums and decision model](../../apps/agents/risk_assessment/models.py#L23) contain 12 decision types and canonical 22 fields plus buffer annotations. | AUD-012-022 for producer completeness. |
| T005 | [X] | PARTIAL | [Assessment/map models](../../packages/domain/src/domain/models/hazard_assessment.py#L7) add fields but do not derive confidence level or enforce complete map/validity invariants. | AUD-012-013, AUD-012-020, AUD-012-021 |
| T006 | [X] | IMPLEMENTED | [Recommendation fields/validator](../../packages/domain/src/domain/models/recommendation.py#L22) add all task-listed fields and score bounds; later lineage/related-ID obligations remain. | AUD-012-009, AUD-012-021 |
| T007 | [X] | PARTIAL | [Model tests](../../tests/unit/test_risk_assessment_models.py#L203) omit derived-level enforcement, full state lifecycle and valid GeoJSON assertions. | AUD-012-021, AUD-012-028 |
| T008 | [X] | PARTIAL | [Config tests](../../tests/unit/test_risk_assessment_config.py#L10) cover selected defaults/overrides, not all core configuration boundary/optional cases. | AUD-012-021, AUD-012-028 |
| T009 | [X] | PARTIAL | [Dedup tests](../../tests/unit/test_risk_assessment_dedup.py#L8) cover sequential TTL/eviction, not concurrent dedup safety. | AUD-012-010, AUD-012-028 |
| T010 | [X] | PARTIAL | [Correlation tests](../../tests/unit/test_risk_assessment_correlation.py#L34) do not assert exact weighted formula, missing proportion, or low score for all stale. | AUD-012-004, AUD-012-005, AUD-012-019, AUD-012-028 |
| T011 | [X] | PARTIAL | [Severity tests](../../tests/unit/test_risk_assessment_severity.py#L20) cover supplied disaster type, but not actual incident/geography derivation and exact fallback downgrades. | AUD-012-014, AUD-012-028 |
| T012 | [X] | PARTIAL | [Version tests](../../tests/unit/test_risk_assessment_versioning.py#L17) exercise mock conflicts; exhaustion checks only positive integer and has no concurrent allocation assertion. | AUD-012-006, AUD-012-028 |
| T013 | [X] | PARTIAL | [Pipeline tests](../../tests/unit/test_risk_assessment_pipeline.py#L55) omit malformed/unknown incident, real partial retrieval, safety and durable persistence assertions. | AUD-012-002, AUD-012-004, AUD-012-007, AUD-012-028 |
| T014 | [X] | PARTIAL | [TTL cache](../../apps/agents/risk_assessment/dedup.py#L16) exists but check/insert is not concurrency-safe and pre-success dedup suppresses recovery. | AUD-012-010 |
| T015 | [X] | PARTIAL | [Correlator](../../apps/agents/risk_assessment/correlation.py#L60) computes mean/stale/diversity flags; unverified kinds and consumption of results incomplete. | AUD-012-005, AUD-012-019 |
| T016 | [X] | CONFLICT | [Severity helper](../../apps/agents/risk_assessment/severity.py#L62) and [two fallback tables](data-model.md#L254) conflict with direct category wording in FR-031. | AUD-012-014, AUD-012-031 |
| T017 | [X] | CONFLICT | [Counter](../../apps/agents/risk_assessment/versioning.py#L39) has retry code, but fallback is neither reserved nor UUID-suffixed; integer contract conflicts with task fallback. | AUD-012-006, AUD-012-031 |
| T018 | [X] | IMPLEMENTED | [Assessment](../../apps/agents/risk_assessment/templates.py#L10) and [recommendation templates](../../apps/agents/risk_assessment/templates.py#L72) include IDs for all five types. | AUD-012-015, AUD-012-017 for final-context integration. |
| T019 | [X] | PARTIAL | [AuditWriter.write](../../apps/agents/risk_assessment/audit.py#L42) is relocated method name; create-only adapter exists, but no container-bound production construction found. | AUD-012-001, AUD-012-022, AUD-012-023 |
| T020 | [X] | PARTIAL | [Generate assessment](../../apps/agents/risk_assessment/agent.py#L76) plus [pipeline stage](../../apps/agents/risk_assessment/pipeline.py#L377) exist; real inputs, versions, complete snapshot and durability incomplete. | AUD-012-004, AUD-012-006, AUD-012-007, AUD-012-014, AUD-012-018 |
| T021 | [X] | PARTIAL | [Pipeline](../../apps/agents/risk_assessment/pipeline.py#L97) orchestrates stages but omits schema/incident checks and real batch retrieval. | AUD-012-001, AUD-012-002, AUD-012-003, AUD-012-004 |
| T022 | [X] | MISSING | S2/S3/S5: [entrypoint](../../apps/agents/risk_assessment/agent.py#L808) serves HTTP only; no risk ServiceBusReceiver/settlement lifecycle found after replacement checks. | AUD-012-001, AUD-012-029, AUD-012-031 |
| T023 | [X] | IMPLEMENTED | [Communication tests](../../tests/contract/test_risk_assessment_escalation.py#L31) assert above/below numeric threshold, required payload and numeric confidence. | AUD-012-028 for end-to-end strengthening. |
| T024 | [X] | IMPLEMENTED | [Handoff tests](../../tests/contract/test_risk_assessment_handoff.py#L31) assert source/target, payload and tenant propagation on constructed models. | AUD-012-003 for boundary enforcement. |
| T025 | [X] | PARTIAL | [Legacy public-alert API](../../apps/agents/risk_assessment/agent.py#L410) still sets empty assessment, invented 0.85/high, and default live scope. | AUD-012-015 |
| T026 | [X] | IMPLEMENTED | [Communication builder](../../apps/agents/risk_assessment/agent.py#L462) uses configurable numeric threshold and actual recommendation score. | None for local comparison fix. |
| T027 | [X] | PARTIAL | [Generic missing-ID loop](../../apps/agents/risk_assessment/agent.py#L352) exists; [legacy any-ID guard](../../apps/agents/risk_assessment/agent.py#L438) leaves incomplete citations. | AUD-012-015 |
| T028 | [X] | PARTIAL | [Stage generation/persistence](../../apps/agents/risk_assessment/pipeline.py#L461) exists but failed writes are swallowed and type/task mapping incomplete. | AUD-012-007, AUD-012-016 |
| T029 | [X] | PARTIAL | [Escalation](../../apps/agents/risk_assessment/pipeline.py#L512) calls shared retry only with injected sender; default host has none. | AUD-012-001, AUD-012-024 |
| T030a | [X] | IMPLEMENTED | [Evacuation assertions](../../tests/contract/test_risk_assessment_escalation.py#L73) cover high/confident, low severity, low confidence and required payload. | AUD-012-028 for actual route/threshold-boundary integration. |
| T030b | [X] | PARTIAL | [Resource tests](../../tests/contract/test_risk_assessment_escalation.py#L128) supply recommendation type, not present/absent coordination tasks or low-confidence cases. | AUD-012-016, AUD-012-028 |
| T030c | [X] | PARTIAL | [Pipeline tests](../../tests/unit/test_risk_assessment_pipeline.py#L118) have a weak no-escalation counter assertion; no required dead-letter retry/audit tests found in that home. | AUD-012-024, AUD-012-028 |
| T030 | [X] | IMPLEMENTED | [Type selection](../../apps/agents/risk_assessment/agent.py#L271) supports route-risk and severe spread evacuation; [generic construction](../../apps/agents/risk_assessment/agent.py#L309) carries parent severity/IDs. | AUD-012-016 for route-risk production context. |
| T031 | [X] | PARTIAL | [Resource type selection](../../apps/agents/risk_assessment/agent.py#L286) uses category/boolean heuristics instead of explicit task evidence. | AUD-012-016 |
| T032 | [X] | PARTIAL | [Generic five-type generator](../../apps/agents/risk_assessment/agent.py#L309) supports coordination text, but actual type selection never requests coordination. | AUD-012-016 |
| T033 | [X] | IMPLEMENTED | [Pipeline invocation](../../apps/agents/risk_assessment/pipeline.py#L540) reaches [numeric severity/confidence builder](../../apps/agents/risk_assessment/agent.py#L491). | AUD-012-013, AUD-012-024 for lifecycle/delivery. |
| T034 | [X] | PARTIAL | [Resource builder](../../apps/agents/risk_assessment/agent.py#L520) has no task predicate beyond type. | AUD-012-016 |
| T035 | [X] | PARTIAL | [Dead-letter audit](../../apps/agents/risk_assessment/pipeline.py#L607) exists, but default callback only fabricates an entry ID and no operator store is wired. | AUD-012-024 |
| T036 | [X] | PARTIAL | [Review log](../../apps/agents/risk_assessment/pipeline.py#L635) does not guarantee durable human-review records or correct task gating. | AUD-012-007, AUD-012-016 |
| T037 | [X] | PARTIAL | [Contradiction tests](../../tests/unit/test_risk_assessment_correlation.py#L106) omit geography, named source output, stale/fresh and comprehensive multi-way penalty assertions. | AUD-012-011, AUD-012-028 |
| T038 | [X] | PARTIAL | [Detector](../../apps/agents/risk_assessment/correlation.py#L143) groups by parameter only and substitutes source kinds for names. | AUD-012-011 |
| T039 | [X] | IMPLEMENTED | [Penalty helper](../../apps/agents/risk_assessment/correlation.py#L199) applies one configured 0.7 factor and bounds result. | AUD-012-017 for full stacking integration. |
| T040 | [X] | PARTIAL | [Stage](../../apps/agents/risk_assessment/pipeline.py#L288) and [assessment details](../../apps/agents/risk_assessment/agent.py#L250) preserve a flag, but no durable human-review workflow. | AUD-012-011, AUD-012-022 |
| T041 | [X] | PARTIAL | [Summary](../../apps/agents/risk_assessment/agent.py#L159) and [audit](../../apps/agents/risk_assessment/pipeline.py#L288) lack reliable names, pair evidence and actual confidence adjustment. | AUD-012-011, AUD-012-022 |
| T042 | [X] | PARTIAL | [Replay tests](../../tests/contract/test_risk_assessment_reproducibility.py#L26) cover simple same-input helper results/keys, not actual replay or simulation persistence/delivery. | AUD-012-003, AUD-012-018, AUD-012-028 |
| T043 | [X] | PARTIAL | [SHA-256 hash](../../apps/agents/risk_assessment/config.py#L123) is deterministic but not a complete record/hash of all active config and prompt/model inputs. | AUD-012-018 |
| T044 | [X] | PARTIAL | Snapshot responsibility relocated to [agent](../../apps/agents/risk_assessment/agent.py#L202); selected fields omit controlling facts and resolved policy. | AUD-012-018 |
| T045 | [X] | IMPLEMENTED | [Shared default](../../apps/agents/common/llm_mixin.py#L64) is zero and forwarded to [client](../../apps/agents/common/llm_client.py#L144); risk calls do not override it. | AUD-012-018 for broader determinism. |
| T046 | [X] | PARTIAL | [Scope construction](../../apps/agents/risk_assessment/pipeline.py#L41) and [prefix block](../../apps/agents/risk_assessment/pipeline.py#L527) do not secure reads or conflicting tenant overrides. | AUD-012-003 |
| T047 | [X] | PARTIAL | [Audit tests](../../tests/unit/test_risk_assessment_audit.py#L23) check calls/depth/file existence, not full chronology/annotations/reconciliation/restart loss. | AUD-012-022, AUD-012-023, AUD-012-028 |
| T048 | [X] | IMPLEMENTED | [Bounded deque and memory fallback](../../apps/agents/risk_assessment/audit.py#L29) wrap buffered_at per entry. | AUD-012-023 for durable lifecycle. |
| T049 | [X] | PARTIAL | [JSONL spill](../../apps/agents/risk_assessment/audit.py#L89) exists; rotation, storage provisioning and failed-write retention absent. | AUD-012-023 |
| T050 | [X] | PARTIAL | Recovery relocated to [flush](../../apps/agents/risk_assessment/audit.py#L113); no production caller and ordering/retry hazards remain. | AUD-012-023 |
| T051 | [X] | PARTIAL | [Core audit calls](../../apps/agents/risk_assessment/pipeline.py#L826) exist; safety/recovery/success-stage completeness missing. | AUD-012-012, AUD-012-022 |
| T052 | [X] | PARTIAL | [Rationale truncation](../../apps/agents/risk_assessment/audit.py#L42) moved to writer; [finalization](../../apps/agents/risk_assessment/pipeline.py#L773) does not reconcile records. | AUD-012-022 |
| T053 | [X] | PARTIAL | [All template types](../../apps/agents/risk_assessment/templates.py#L10) authored; pre-approval only asserted in docstring, not established by review evidence. | AUD-012-017, AUD-012-033 |
| T054 | [X] | PARTIAL | [Penalty](../../apps/agents/risk_assessment/agent.py#L143) relocated to agent and correctly follows contradiction; text/method/recommendation consistency incomplete. | AUD-012-017 |
| T055 | [X] | PARTIAL | [Partial retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) proceeds; proportion reduction and exact missing-ID audit absent. | AUD-012-004 |
| T056 | [X] | PARTIAL | [All-missing degradation](../../apps/agents/risk_assessment/pipeline.py#L688) exists; safety, Cosmos/partial-store and LLM recovery audit events missing. | AUD-012-012, AUD-012-022 |
| T057 | [X] | PARTIAL | [Health endpoint](../../apps/agents/risk_assessment/agent.py#L631) returns expected shape but queue/store checks and one-second bound are not real. | AUD-012-025 |
| T058 | [X] | PARTIAL | [Override endpoint](../../apps/agents/risk_assessment/agent.py#L714) lacks authenticated scope, correct partition, immutable versioning and conditional conflict handling. | AUD-012-008, AUD-012-009 |
| T059 | [X] | PARTIAL | [Root/stage spans](../../apps/agents/risk_assessment/pipeline.py#L671) exist; required nested version/LLM/safety/delivery and causal correlation incomplete. | AUD-012-026 |
| T060 | [X] | PARTIAL | [Registry](../../apps/agents/risk_assessment/telemetry.py#L85) declares metric names but eight required metrics lack risk emission and gauges are misrepresented. | AUD-012-026, AUD-012-031 |
| T061 | [X] | PARTIAL | [Event methods](../../apps/agents/risk_assessment/telemetry.py#L318) exist; VersionConflict and several degradation branches are not emitted. | AUD-012-026 |
| T062 | [X] | PARTIAL | [Cosmos tests](../../tests/integration/test_risk_assessment_cosmos.py#L65) test audit records/counters/model copies, not real assessment/recommendation read-back and lifecycle. | AUD-012-006, AUD-012-007, AUD-012-013, AUD-012-028 |
| T063 | [X] | PARTIAL | [Service Bus tests](../../tests/integration/test_risk_assessment_service_bus.py#L111) perform settlement/dead-letter logic in tests, not a production consumer. | AUD-012-001, AUD-012-024, AUD-012-028 |
| T064 | [X] | PARTIAL | [Bushfire scenario](../../tests/simulation/test_bushfire_risk_assessment.py#L105) uses synthetic inputs and synchronous delivery callback with async helper. | AUD-012-004, AUD-012-024, AUD-012-028 |
| T065 | [X] | PARTIAL | [Module](../../infra/modules/risk-assessment.bicep#L63) exists but is unreferenced in searched deployments and uses HTTP scaling/misaligned image port/settings. | AUD-012-027 |
| T066 | [ ] | UNVERIFIED | [Quickstart](quickstart.md#L64) is authored, inconsistent with actual launch/tests; no local execution evidence, and audit did not run it. | AUD-012-029, AUD-012-030, AUD-012-032 |

## Clarification and Amendment Coverage

### All Clarification Decisions

CL labels are audit labels for the original Q/A bullets in [the three sessions](spec.md#L281).
They do not replace original requirement identifiers.

| Decision | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| CL-01: version format/immutability | CONFLICT | Old incident_vN answer versus type-qualified FR-006 and UUID research; [counter](../../apps/agents/risk_assessment/versioning.py#L127) does not reserve fallback. | AUD-012-006, AUD-012-031 |
| CL-02: escalation thresholds | PARTIAL | [Numeric builders](../../apps/agents/risk_assessment/agent.py#L462) implement alert/evacuation values; actual resource tasks/delivery incomplete. | AUD-012-016, AUD-012-024 |
| CL-03: source weights | PARTIAL | [Config weights](../../apps/agents/risk_assessment/config.py#L106) present; source mapping/analysis incomplete. | AUD-012-019 |
| CL-04: contradiction reduction/review | PARTIAL | [Penalty](../../apps/agents/risk_assessment/correlation.py#L199) present; pair-specific named explanation/audit/review incomplete. | AUD-012-011 |
| CL-05: snapshot/temperature | PARTIAL | [Temperature default](../../apps/agents/common/llm_mixin.py#L64) supported; [snapshot](../../apps/agents/risk_assessment/agent.py#L202) incomplete. | AUD-012-018 |
| CL-06: template fallback/20% | PARTIAL | [Penalty](../../apps/agents/risk_assessment/agent.py#L143) present but final text and per-call metadata inconsistent. | AUD-012-017 |
| CL-07: audit fields/Cosmos/no TTL | PARTIAL | [Schema](../../apps/agents/risk_assessment/models.py#L89) and create-only writer exist; canonical field reconciliation/durable delivery incomplete. | AUD-012-022, AUD-012-023, AUD-012-031 |
| CL-08: five AU scenarios | PARTIAL | [Severity table](../../apps/agents/risk_assessment/severity.py#L34) is not scenario-specific geography/calibration. | AUD-012-014 |
| CL-09: 100 concurrent/ACA scaling | PARTIAL | [HTTP scaler](../../infra/modules/risk-assessment.bicep#L181) differs from queue requirement; capacity UNVERIFIED. | AUD-012-027, AUD-012-029 |
| CL-10: six observability families | PARTIAL | [Telemetry](../../apps/agents/risk_assessment/telemetry.py#L85) declares them, not all values/alerts are connected. | AUD-012-026 |
| CL-11: structured hazard map | PARTIAL | [Helper](../../apps/agents/risk_assessment/hazard_map.py#L29) exists but is unattached/incompatible with complete entity shape. | AUD-012-020 |
| CL-12: single incident/future related IDs | PARTIAL | [Assessment metadata](../../packages/domain/src/domain/models/hazard_assessment.py#L48) exists; recommendation metadata/input isolation incomplete. | AUD-012-003, AUD-012-021 |
| CL-13: expiry/supersession | PARTIAL | [Validity](../../apps/agents/risk_assessment/agent.py#L114) only; transition timing conflicts between spec/model. | AUD-012-013, AUD-012-031 |
| CL-14: commander overrides | PARTIAL | [Endpoint](../../apps/agents/risk_assessment/agent.py#L714) contradicts identity/lineage requirements. | AUD-012-008, AUD-012-009 |
| CL-15: content safety/templates | PARTIAL | [Mixin](../../apps/agents/common/llm_mixin.py#L151) validates LLM text; approval/review/audit evidence incomplete. | AUD-012-012, AUD-012-033 |
| CL-16: Service Bus/5s ack/10s SLA | CONFLICT | [Intake contract](contracts/assessment-pipeline.md#L17) versus acknowledge-on-completion task; actual consumer missing. | AUD-012-001, AUD-012-029, AUD-012-031 |
| CL-17: four-level AIDR severity | PARTIAL | [Four-level model](../../apps/agents/risk_assessment/models.py#L58) exists; MAF prompt uses five levels and calibration is not established. | AUD-012-014, AUD-012-031 |
| CL-18: fallback mapping/downgrade | CONFLICT | [Severity helper](../../apps/agents/risk_assessment/severity.py#L62) and original mapping tables disagree for direct categories/geohazard. | AUD-012-014, AUD-012-031 |

### Appended Amendments and Deferred Scope

| Original obligation | Status | Evidence, execution distinction, and follow-up |
| --- | --- | --- |
| ASM-033 | IMPLEMENTED | [AU baseline and deferred countries](spec.md#L314) are explicit authored scope. Real deployment/calibration approval is not implied; AUD-012-027, AUD-012-033. |
| ASM-034 | UNVERIFIED | [Named actor consultation](spec.md#L315) is a mandate, not a consultation transcript or revision-bound approval; AUD-012-033. No actors were delegated to in this audit. |
| ASM-035 | PARTIAL | [Schema authority](spec.md#L316) is referenced; HYP-010 filename/validation evidence gaps remain; AUD-012-033. |
| PER-028 | UNVERIFIED | [Validated AIIMS cross-reference](spec.md#L322) does not attach the practitioner identity/date/scenario evidence required by the [persona contract](../027-spec-hardening/contracts/persona-profile.md#L7); AUD-012-033. |
| PER-029 | UNVERIFIED | [Validated actor-catalogue reference](spec.md#L323) is not proof of practitioner validation or consultation on this feature; AUD-012-033. |
| PER-030 | IMPLEMENTED | [Non-AU placeholder](spec.md#L324) explicitly requires D-009 and SME validation. Placeholder authorship is supported, real validation is not claimed. |
| HYP-010 | PARTIAL | [Hypothesis](spec.md#L330) and [portfolio baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1) exist; S6 found neither named stub nor comparator. Per-012 improvement/consultation is UNVERIFIED; AUD-012-033. |
| SCP-031 | IMPLEMENTED | [Country promotion gates](spec.md#L336) explicitly defer PH/JP/BD pending reinterpretation, legal/data-sharing and calibration sign-off. Do not treat deferred calibration as missing v1 implementation. |
| SCP-032 | PARTIAL | [Non-negotiable preservation rule](spec.md#L337) is authored; plan constitutional references must be reconciled with current constitution and bounded carve-out, not autonomously changed; AUD-012-031. |
| SCP-033 | IMPLEMENTED | [Authority boundaries](spec.md#L338) defer recovery to 018 and warning authoring/delivery to 008; protective-action execution remains out of scope. Dispute approvals are not asserted. |
| CAP-012-PH: typhoon taxonomy row | IMPLEMENTED | [Taxonomy extension](spec.md#L341) adds a deferred PH analogue without replacing the AU hazard row. No country deployment/ratification is proved. |
| CAP-012-JP: earthquake/tsunami taxonomy row | IMPLEMENTED | [Taxonomy extension](spec.md#L341) declares JP subduction earthquake/tsunami deferred; no calibrated implementation is claimed. |
| CAP-012-BD: flood taxonomy row | IMPLEMENTED | [Taxonomy extension](spec.md#L341) declares BD monsoon/coastal flood deferred; existing AU class is retained. |
| HYP-039 | UNVERIFIED | [PH stub](evidence/HYP-039.md#L1) satisfies six headings/preconditions/quantified falsification and says Not tested. Target <=15%, falsification >25%; >=10 events, risk-manager ratification, D-009, Jun-Nov window remain prerequisites. |
| HYP-040 | UNVERIFIED | [JP stub](evidence/HYP-040.md#L1) is structurally present, Not tested. Target <=10%, falsification >20%; >=10 events, taxonomy ratification, D-009, quarterly review required. |
| HYP-041 | UNVERIFIED | [BD stub](evidence/HYP-041.md#L1) is structurally present, Not tested. Target <=20%, falsification >30%; >=10 events, taxonomy ratification, D-009, Apr-Sep window required. |

HYP-039/040/041 statuses describe empirical claims, not missing files. Their authored stub obligation is
IMPLEMENTED. Promotion requires a separately authorized feature per the [evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L81),
not implementation work or approval invented by this audit.

## Review and Checklist Evidence Assessment

### Plan's Five Historical Issues

| Plan issue | Status | Current source assessment | Follow-up |
| --- | --- | --- | --- |
| ISSUE-1: hardcoded handoff confidence | IMPLEMENTED | [Builder](../../apps/agents/risk_assessment/agent.py#L462) uses recommendation score, not 0.9. | Legacy invented recommendation confidence is separate: AUD-012-015. |
| ISSUE-2: categorical threshold | IMPLEMENTED | [Builder](../../apps/agents/risk_assessment/agent.py#L462) uses numeric/configured comparison. | None for the local fix. |
| ISSUE-3: incomplete recommendation fields | PARTIAL | [Generic generator](../../apps/agents/risk_assessment/agent.py#L359) fills fields; [legacy public API](../../apps/agents/risk_assessment/agent.py#L410) does not derive them from an assessment. | AUD-012-015 |
| ISSUE-4: single recommendation type | PARTIAL | [Type selection](../../apps/agents/risk_assessment/agent.py#L271) covers four reachable types; coordination remains unreachable. | AUD-012-016 |
| ISSUE-5: no retrieval/correlation | PARTIAL | [Pipeline retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) and correlator exist, but real producer/host/store integration is absent. | AUD-012-001, AUD-012-004 |

### All 21 Constitution Gate Obligations

These rows assess both the [pre-design PASS table](plan.md#L46) and the [post-design PASS declaration](plan.md#L72).
They do not establish who reviewed either gate, that tests ran, or that approval was granted. Current constitution
principle numbering/content also differs from the historical plan; AUD-012-031 covers reconciliation.

| Gate | Status | Evidence and limitation | Follow-up |
| --- | --- | --- | --- |
| GATE-01: life-safety latency/escalation | PARTIAL | [Generation/dispatch](../../apps/agents/risk_assessment/pipeline.py#L648) exists without real host or measurements. | AUD-012-001, AUD-012-029 |
| GATE-02: human override/emergency stop | PARTIAL | [Override](../../apps/agents/risk_assessment/agent.py#L714) lacks secure immutable semantics; local gate approval not evidenced. | AUD-012-008, AUD-012-009, AUD-012-033 |
| GATE-03: commander explanations | PARTIAL | [Any-ID guard](../../apps/agents/risk_assessment/agent.py#L156) and incomplete prompt context; no clarity survey. | AUD-012-015, AUD-012-030 |
| GATE-04: safe stale/degraded behavior | PARTIAL | [All-stale flag](../../apps/agents/risk_assessment/correlation.py#L103) is not enforced. | AUD-012-005, AUD-012-017 |
| GATE-05: explicit handoffs | PARTIAL | [Handoff schema](../../apps/agents/common/handoffs.py#L26) exists; real delivery and task gating incomplete. | AUD-012-016, AUD-012-024 |
| GATE-06: no silent state change | PARTIAL | [Swallowed writes](../../apps/agents/risk_assessment/pipeline.py#L415) and incomplete audit break the claim. | AUD-012-007, AUD-012-022 |
| GATE-07: AIIMS authority | PARTIAL | [Default approval](../../apps/agents/risk_assessment/agent.py#L359) is correct but not authenticated/configurable; override unsafe. | AUD-012-008, AUD-012-016 |
| GATE-08: provenance | PARTIAL | [Snapshot subset](../../apps/agents/risk_assessment/agent.py#L202) and synthetic fallback lose required facts. | AUD-012-004, AUD-012-018 |
| GATE-09: authority weighting | PARTIAL | [Weights](../../apps/agents/risk_assessment/config.py#L106) present; canonical mapping/unverified notice incomplete. | AUD-012-019 |
| GATE-10: freshness | PARTIAL | [Weighted mean](../../apps/agents/risk_assessment/correlation.py#L60) does not guarantee stale-score reduction/holds. | AUD-012-005, AUD-012-019 |
| GATE-11: contradictions | PARTIAL | [Detector](../../apps/agents/risk_assessment/correlation.py#L143) misses geographic/name/review requirements. | AUD-012-011 |
| GATE-12: reproducible versions | PARTIAL | [Version fallback](../../apps/agents/risk_assessment/versioning.py#L127) and [snapshot](../../apps/agents/risk_assessment/agent.py#L202) incomplete. | AUD-012-006, AUD-012-018 |
| GATE-13: data minimization | UNVERIFIED | [Raw provenance subset](../../apps/agents/risk_assessment/agent.py#L202) is persisted without a reviewed risk classification/retention mapping in local artifacts. | AUD-012-018, AUD-012-031, AUD-012-033 |
| GATE-14: Australian residency | UNVERIFIED | [Region design](research.md#L132) is an assertion; current constitution permits a bounded model exception, actual deployment unqueried. | AUD-012-027, AUD-012-031 |
| GATE-15: tenant isolation | PARTIAL | [Prefix gate](../../apps/agents/risk_assessment/pipeline.py#L527) does not validate reads or tenant overrides. | AUD-012-003 |
| GATE-16: prompt injection protection | PARTIAL | [Shared system prompt](../../apps/agents/common/llm_client.py#L177) exists; risk-specific context/adversarial gate incomplete. | AUD-012-012, AUD-012-015 |
| GATE-17: content safety | PARTIAL | [Validation/fallback](../../apps/agents/common/llm_mixin.py#L151) exists; risk audit/review/approval evidence absent. | AUD-012-012, AUD-012-033 |
| GATE-18: Azure/AU hosting | PARTIAL | [Azure module](../../infra/modules/risk-assessment.bicep#L1) is authored, not called or verified deployed with regional controls. | AUD-012-027 |
| GATE-19: outage resilience | PARTIAL | [Audit tiers](../../apps/agents/risk_assessment/audit.py#L42) and LLM fallback exist, but no-loss recovery is not established. | AUD-012-007, AUD-012-023 |
| GATE-20: immutable infinite audit | PARTIAL | [create-only writer](../../apps/agents/risk_assessment/audit.py#L70) and no-TTL declaration present, durable completeness unproved. | AUD-012-022, AUD-012-023, AUD-012-027 |
| GATE-21: WAF/operability | PARTIAL | [Health](../../apps/agents/risk_assessment/agent.py#L631), telemetry and scaling artifacts incomplete; no operational review proof. | AUD-012-025, AUD-012-026, AUD-012-027, AUD-012-033 |

### All 102 Checklist Obligations

Original state for every item is `[ ]`. Status here evaluates the specific question's design/source support,
not a historical review sign-off. IMPLEMENTED can mean an explicit authored answer; deployment/performance
claims still require independent evidence. Quoted fragments identify the exact obligation being assessed.

| Checklist ID | Original state | Status | Evidence assessment and follow-up |
| --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | "prediction accuracy": [SCs](spec.md#L272) cover timing/detection, not hazard accuracy methodology. AUD-012-030, AUD-012-031. |
| CHK002 | [ ] | PARTIAL | "confidence calculation": [research formula](research.md#L9) resolves averaging, not diversity/missing/stale integration. AUD-012-019. |
| CHK003 | [ ] | IMPLEMENTED | "exactly 0.4": [level helper](../../apps/agents/risk_assessment/models.py#L72) and [boundary tests](../../tests/unit/test_risk_assessment_models.py#L105) define inclusive lower bounds. |
| CHK004 | [ ] | PARTIAL | "all signal categories": [Monitoring categories](../../apps/agents/monitoring/agent.py#L34) include earthquake/tsunami outside explicit default mapping. AUD-012-014. |
| CHK005 | [ ] | PARTIAL | "unmapped category": [helper](../../apps/agents/risk_assessment/severity.py#L96) defaults impact_projection, but authoritative policy/severity semantics unresolved. AUD-012-014, AUD-012-031. |
| CHK006 | [ ] | PARTIAL | "scenario-specific parameters": [disaster table](../../apps/agents/risk_assessment/severity.py#L34) lacks incident/geographic models. AUD-012-014. |
| CHK007 | [ ] | PARTIAL | "population thresholds": [50,000 cutoff](../../apps/agents/risk_assessment/severity.py#L83) is code-defined without local calibration evidence. AUD-012-014, AUD-012-030. |
| CHK008 | [ ] | UNVERIFIED | "accuracy per disaster": [deferred stubs](evidence/HYP-039.md#L17) are not AU accuracy evidence. AUD-012-030. |
| CHK009 | [ ] | CONFLICT | "SLA boundary": [plan resolution](plan.md#L160) says persistence; [pipeline timing](../../apps/agents/risk_assessment/pipeline.py#L773) includes later work. AUD-012-029, AUD-012-031. |
| CHK010 | [ ] | IMPLEMENTED | "retrieval included": [latency budget](contracts/assessment-pipeline.md#L138) explicitly budgets retrieval in ten seconds; execution UNVERIFIED. AUD-012-029. |
| CHK011 | [ ] | CONFLICT | "bitwise or semantic": [US5](spec.md#L75) versus [research semantic definition](research.md#L172), with undefined tolerance. AUD-012-018, AUD-012-031. |
| CHK012 | [ ] | PARTIAL | "model upgrades": [snapshot requirement](spec.md#L190) requires attribution, but current snapshot lacks model revision. AUD-012-018. |
| CHK013 | [ ] | IMPLEMENTED | "temperature sufficient": [research](research.md#L172) explicitly acknowledges it is necessary, not sufficient. |
| CHK014 | [ ] | PARTIAL | "implicit inputs": [snapshot](../../apps/agents/risk_assessment/agent.py#L202) omits payload/clock semantics controlling decisions. AUD-012-018. |
| CHK015 | [ ] | PARTIAL | "template reproducibility": [replay contract tests](../../tests/contract/test_risk_assessment_reproducibility.py#L26) do not force generation modes and replay persisted inputs. AUD-012-018, AUD-012-028. |
| CHK016 | [ ] | PARTIAL | "verification harness": [tests](../../tests/contract/test_risk_assessment_reproducibility.py#L26) compare supplied helper inputs, not snapshot reconstruction. AUD-012-018. |
| CHK017 | [ ] | PARTIAL | "configuration strategy": [SHA-256](../../apps/agents/risk_assessment/config.py#L123) present; complete canonical active-input scope unresolved. AUD-012-018. |
| CHK018 | [ ] | IMPLEMENTED | "configurable weights": [environment-backed defaults](../../apps/agents/risk_assessment/config.py#L15) and [override tests](../../tests/unit/test_risk_assessment_config.py#L73) exist. |
| CHK019 | [ ] | IMPLEMENTED | "weighted averaging formula": [research](research.md#L9) and [correlator](../../apps/agents/risk_assessment/correlation.py#L60) agree on normalized mean. Freshness semantics remain separate AUD-012-019. |
| CHK020 | [ ] | PARTIAL | "unmapped source kinds": [social default](../../apps/agents/risk_assessment/config.py#L106) exists but unverified warning omits unknown kinds. AUD-012-019. |
| CHK021 | [ ] | MISSING | "geographic proximity": S2/S3 [detector grouping](../../apps/agents/risk_assessment/correlation.py#L143) has no area predicate; local design lacks granularity. AUD-012-011, AUD-012-031. |
| CHK022 | [ ] | PARTIAL | "across handoffs": [pipeline](../../apps/agents/risk_assessment/pipeline.py#L169) sees only current IDs; correlation time/window scope is not resolved. AUD-012-019, AUD-012-031. |
| CHK023 | [ ] | MISSING | "minimum corroborating sources": no rule in local [research formula](research.md#L9)/S2 correlator. AUD-012-019, AUD-012-031. |
| CHK024 | [ ] | PARTIAL | "diversity measure": [source-kind count](../../apps/agents/risk_assessment/correlation.py#L122) exists but has no defined confidence contribution or persistence. AUD-012-019. |
| CHK025 | [ ] | PARTIAL | "opposing trajectories": [research](research.md#L31) defines direction/parameter, but geographic criterion is not implemented. AUD-012-011. |
| CHK026 | [ ] | IMPLEMENTED | "multiplicative": [penalty helper](../../apps/agents/risk_assessment/correlation.py#L199) and [research](research.md#L31) specify x0.7. |
| CHK027 | [ ] | PARTIAL | "multi-way": one penalty/pair list present; [audit](../../apps/agents/risk_assessment/pipeline.py#L288) does not individually log pairs. AUD-012-011, AUD-012-022. |
| CHK028 | [ ] | UNVERIFIED | "labelled set size/composition": [SC-003](spec.md#L274) has a percentage, no inspected labelled benchmark/result. AUD-012-030. |
| CHK029 | [ ] | IMPLEMENTED | "different authority treatment": [research](research.md#L31) rejects authority-dependent penalties; detector applies uniform rule. Named-source integrity remains AUD-012-011. |
| CHK030 | [ ] | PARTIAL | "human review workflow": [summary notice](../../apps/agents/risk_assessment/agent.py#L159) is not a stored review queue/ownership/deadline. AUD-012-011, AUD-012-031. |
| CHK031 | [ ] | PARTIAL | "fresh versus stale conflict": [detector](../../apps/agents/risk_assessment/correlation.py#L143) permits it and [research](research.md#L69) orders penalties; full stale guard/tests incomplete. AUD-012-005, AUD-012-011. |
| CHK032 | [ ] | PARTIAL | "concurrent monotonic versions": [counter](../../apps/agents/risk_assessment/versioning.py#L39) falls back unsafely; no real contention assertion. AUD-012-006. |
| CHK033 | [ ] | PARTIAL | "assessment/recommendation versions": [per-process sequencing](../../apps/agents/risk_assessment/agent.py#L66) and no immutable modification lineage. AUD-012-007, AUD-012-009. |
| CHK034 | [ ] | CONFLICT | "status-only immutability": [FR-006](spec.md#L146) permits status changes; [data-model transition timing](data-model.md#L98) disagrees with expiry-time wording. AUD-012-013, AUD-012-031. |
| CHK035 | [ ] | MISSING | "version-history query": S2/S3 finds no risk history query; [model](../../packages/domain/src/domain/models/hazard_assessment.py#L18) alone is not a query interface. AUD-012-013. |
| CHK036 | [ ] | CONFLICT | "ID type uniqueness": [FR-006](spec.md#L146) includes type, old clarification does not; contention fallback still unsafe. AUD-012-006, AUD-012-031. |
| CHK037 | [ ] | PARTIAL | "version growth": no maximum/capacity projection in [version entity](data-model.md#L218); infinite retention must be planned, not silently capped. AUD-012-027, AUD-012-031. |
| CHK038 | [ ] | MISSING | "version comparison": no comparator in scoped risk/API source; [US5](spec.md#L75) describes side-by-side comparison only. AUD-012-018, AUD-012-031. |
| CHK039 | [ ] | PARTIAL | "penalty order": [research](research.md#L69) resolves core order; missing-input/extrapolation effects and rendered final values differ. AUD-012-017. |
| CHK040 | [ ] | IMPLEMENTED | "LLM unavailability detection": [mixin](../../apps/agents/common/llm_mixin.py#L64) has timeout/error/circuit-breaker fallback in source. Recovery audit is separate AUD-012-012. |
| CHK041 | [ ] | PARTIAL | "fallback content/quality": [five templates](../../apps/agents/risk_assessment/templates.py#L10) include IDs; final-value consistency and approval unverified. AUD-012-017, AUD-012-033. |
| CHK042 | [ ] | PARTIAL | "simultaneous degradation": [pipeline](../../apps/agents/risk_assessment/pipeline.py#L169) drops missing fraction before LLM penalty. AUD-012-004, AUD-012-017. |
| CHK043 | [ ] | PARTIAL | "proportional formula": [stage 2 contract](contracts/assessment-pipeline.md#L31) defines fraction; source does not apply it. AUD-012-004. |
| CHK044 | [ ] | PARTIAL | "recovery path": mixin resumes after success, but [risk generation](../../apps/agents/risk_assessment/agent.py#L76) has no recovery state/event. AUD-012-012. |
| CHK045 | [ ] | PARTIAL | "dead-letter notification": [default callback](../../apps/agents/risk_assessment/pipeline.py#L79) invents an ID; no durable operator surface found. AUD-012-024. |
| CHK046 | [ ] | PARTIAL | "health schema": [contract](contracts/health-endpoint.md#L13) is explicit; [implementation](../../apps/agents/risk_assessment/agent.py#L631) has placeholder checks. AUD-012-025. |
| CHK047 | [ ] | PARTIAL | "audit dependency outage": [three tiers](../../apps/agents/risk_assessment/audit.py#L42) exist without durable recovery/no-loss guarantee. AUD-012-023. |
| CHK048 | [ ] | CONFLICT | "canonical audit fields": [research 22 fields](research.md#L97) resolves some naming, but [FR-029](spec.md#L197) still requires categorical confidence/full context absent from model/records. AUD-012-022, AUD-012-031. |
| CHK049 | [ ] | PARTIAL | "retention obligations": [no TTL design](data-model.md#L151) explicit; privacy/classification justification and approval not established. AUD-012-031, AUD-012-033. |
| CHK050 | [ ] | MISSING | "audit querying": S2/S3 finds writer, not a scoped risk audit query/authorization/filter interface for [US6](spec.md#L91). AUD-012-022, AUD-012-024. |
| CHK051 | [ ] | PARTIAL | "safety failure detail": [mixin metadata](../../apps/agents/common/llm_mixin.py#L151) exists but is not recorded by risk audit; raw unsafe text retention should not be assumed. AUD-012-012, AUD-012-022. |
| CHK052 | [ ] | PARTIAL | "successful step audit": [finalization](../../apps/agents/risk_assessment/pipeline.py#L773) does not reconcile successful correlation/no-anomaly stages. AUD-012-022. |
| CHK053 | [ ] | PARTIAL | "causal ordering": [flush](../../apps/agents/risk_assessment/audit.py#L113) drains later file records after memory failure and lacks cross-tier sequence policy. AUD-012-023. |
| CHK054 | [ ] | PARTIAL | "referential links": [audit model](../../apps/agents/risk_assessment/models.py#L89) has assessment/recommendation IDs but missing outbound-event structure and swallowed persistence undermine links. AUD-012-007, AUD-012-022. |
| CHK055 | [ ] | PARTIAL | "sizing/partitioning": [scope key](data-model.md#L151) and [4000 RU declaration](../../infra/modules/risk-assessment.bicep#L101) exist, no load/growth evidence. AUD-012-027, AUD-012-029. |
| CHK056 | [ ] | PARTIAL | "AIDR publication mapping": [research](research.md#L142) cites the collection, not a precise source mapping for the four labels; current constitution has handbook years. AUD-012-014, AUD-012-033. |
| CHK057 | [ ] | PARTIAL | "severity formula": [code cutoff](../../apps/agents/risk_assessment/severity.py#L62) exists without reviewed scenario calibration/threshold contract. AUD-012-014. |
| CHK058 | [ ] | IMPLEMENTED | "asymmetric escalation": [threshold table](data-model.md#L278) explicitly makes severity required only for evacuation. |
| CHK059 | [ ] | CONFLICT | "fallback versus AIDR semantics": [two category tables](data-model.md#L254) and [FR-031](spec.md#L202) differ; code cannot settle policy. AUD-012-014, AUD-012-031. |
| CHK060 | [ ] | IMPLEMENTED | "low floor": [downgrade helper](../../apps/agents/risk_assessment/severity.py#L51) and [severity test](../../tests/unit/test_risk_assessment_severity.py#L20) retain low as floor. |
| CHK061 | [ ] | PARTIAL | "stable version severity": [fallback recomputation](../../apps/agents/risk_assessment/agent.py#L143) occurs after text creation; immutable persistence and input snapshot incomplete. AUD-012-007, AUD-012-017, AUD-012-018. |
| CHK062 | [ ] | PARTIAL | "severity justification": [assessment prompt](../../apps/agents/risk_assessment/agent.py#L127) names severity but omits the actual evidence/population rationale. AUD-012-014, AUD-012-015. |
| CHK063 | [ ] | UNVERIFIED | "AU sovereignty/regions": [research region assertion](research.md#L132) is not deployed evidence and must be reconciled with the bounded current carve-out. AUD-012-027, AUD-012-031. |
| CHK064 | [ ] | PARTIAL | "Service Bus/failover": [queue module](../../infra/modules/risk-assessment.bicep#L123) exists, but deployment call/failover intake path absent in S5. AUD-012-001, AUD-012-027. |
| CHK065 | [ ] | CONFLICT | "Cosmos geo-redundancy": [plan resources](plan.md#L180) mix serverless primary and multi-region-write DR; isolated module uses autoscale. No verified replication design. AUD-012-027, AUD-012-031. |
| CHK066 | [ ] | UNVERIFIED | "AU model availability": [research claim](research.md#L132) is dated design text, not current availability/approval evidence. AUD-012-027, AUD-012-033. |
| CHK067 | [ ] | UNVERIFIED | "regional capacity": [100 concurrent target](spec.md#L221) has no inspected capacity/load proof; no cloud queries allowed. AUD-012-029. |
| CHK068 | [ ] | PARTIAL | "network isolation": [internal ingress](../../infra/modules/risk-assessment.bicep#L149) present but complete risk service/network integration not shown. AUD-012-027. |
| CHK069 | [ ] | PARTIAL | "DR/RPO/RTO": [DR region declaration](research.md#L132) lacks scoped failover/recovery measurements and operational policy. AUD-012-027, AUD-012-029, AUD-012-031. |
| CHK070 | [ ] | UNVERIFIED | "data classification": local spec/plan do not attach an approved risk-data classification/retention assessment. [Current constitution](../../.specify/memory/constitution.md#L263) still applies. AUD-012-031, AUD-012-033. |
| CHK071 | [ ] | PARTIAL | "GeoJSON ownership/validation": [unattached helper](../../apps/agents/risk_assessment/hazard_map.py#L29) and permissive model do not satisfy embedded output. AUD-012-020. |
| CHK072 | [ ] | PARTIAL | "population source": [first-payload estimate](../../apps/agents/risk_assessment/agent.py#L258) has no source/provenance aggregation policy. AUD-012-014, AUD-012-020. |
| CHK073 | [ ] | PARTIAL | "time horizon": [map model](../../packages/domain/src/domain/models/hazard_assessment.py#L7) accepts arbitrary string; no connected computation. AUD-012-020, AUD-012-021. |
| CHK074 | [ ] | PARTIAL | "recommendation lifecycle": [Literal status](../../packages/domain/src/domain/models/recommendation.py#L7) lists values, while override writes invalid modified state and no full transition policy. AUD-012-009, AUD-012-021. |
| CHK075 | [ ] | PARTIAL | "concurrent override": [contract 409](contracts/health-endpoint.md#L90) exists, but [upsert](../../apps/agents/risk_assessment/agent.py#L762) has no conditional write. AUD-012-009. |
| CHK076 | [ ] | MISSING | "override authorization": S2/S3 standalone [endpoint](../../apps/agents/risk_assessment/agent.py#L714) trusts body role and has no auth dependency. AUD-012-008. |
| CHK077 | [ ] | PARTIAL | "scope key": [data model](data-model.md#L9) names routing scope; source/tenant/partition consistency is not enforced. AUD-012-003. |
| CHK078 | [ ] | CONFLICT | "audit write latency": [contract async budget](contracts/assessment-pipeline.md#L138) differs from serial [write calls](../../apps/agents/risk_assessment/pipeline.py#L826). AUD-012-023, AUD-012-029, AUD-012-031. |
| CHK079 | [ ] | PARTIAL | "human-readable summary": [template](../../apps/agents/risk_assessment/templates.py#L10) provides content, but no final factual/clarity rubric or complete evidence context. AUD-012-015, AUD-012-030. |
| CHK080 | [ ] | UNVERIFIED | "five-point rubric anchors": [SC-008](spec.md#L279) names dimensions only; no anchored survey/results locally. AUD-012-030. |
| CHK081 | [ ] | CONFLICT | "total response boundary": [10-second stage budget](contracts/assessment-pipeline.md#L138) includes delivery while SC-007 separately allows 15 seconds after assessment. AUD-012-029, AUD-012-031. |
| CHK082 | [ ] | UNVERIFIED | "commander sample size": [SC-008](spec.md#L279) has no defined minimum cohort or measured denominator. AUD-012-030. |
| CHK083 | [ ] | PARTIAL | "retry delay values": [helper](../../apps/agents/common/handoffs.py#L124) supplies backoff/caps, but retry-versus-attempt contract unresolved. AUD-012-024, AUD-012-031. |
| CHK084 | [ ] | CONFLICT | "acknowledgment meaning": [stage 1](contracts/assessment-pipeline.md#L17) and acknowledge-on-completion T022 disagree; no real receiver to measure. AUD-012-001, AUD-012-029, AUD-012-031. |
| CHK085 | [ ] | MISSING | "closed incident": S2/S3 [intake](../../apps/agents/risk_assessment/pipeline.py#L97) has no incident lifecycle policy. AUD-012-002, AUD-012-031. |
| CHK086 | [ ] | PARTIAL | "backpressure": [synchronous pipeline](../../apps/agents/risk_assessment/pipeline.py#L648) and HTTP scaler do not define queue overload behavior. AUD-012-027, AUD-012-029. |
| CHK087 | [ ] | PARTIAL | "misrouted simulation": [tenant override](../../apps/agents/risk_assessment/pipeline.py#L648) and prefix check can disagree with inbound context. AUD-012-003. |
| CHK088 | [ ] | PARTIAL | "multiple assessment types": [generation](../../apps/agents/risk_assessment/pipeline.py#L377) selects first signal category; mixed-category ordering policy unspecified. AUD-012-014, AUD-012-031. |
| CHK089 | [ ] | CONFLICT | "validator unavailable": [keyword fallback](../../apps/agents/common/content_safety.py#L104) can pass with review flag lost by caller; strict safety versus continuity policy unresolved. AUD-012-012, AUD-012-031. |
| CHK090 | [ ] | MISSING | "modify after handoff": S2/S3 [override](../../apps/agents/risk_assessment/agent.py#L714) has no recall/supersession linkage. AUD-012-009, AUD-012-031. |
| CHK091 | [ ] | MISSING | "expiry during downstream work": S2/S3 has no risk lifecycle/handoff notification path. [Stage 7](contracts/assessment-pipeline.md#L114) does not resolve it. AUD-012-013, AUD-012-031. |
| CHK092 | [ ] | PARTIAL | "governance trust mapping": [three string weights](../../apps/agents/risk_assessment/config.py#L106) are not a governed source-registry mapping. AUD-012-019. |
| CHK093 | [ ] | CONFLICT | "Monitoring payload sufficiency": [documented inbound shape](data-model.md#L30) and [producer](../../apps/agents/monitoring/agent.py#L111) omit IDs needed by FR-002. AUD-012-004, AUD-012-031. |
| CHK094 | [ ] | PARTIAL | "downstream scope/dead letters": [stage 7](contracts/assessment-pipeline.md#L114) owns delivery failure but actual operator surfacing is unwired. AUD-012-024. |
| CHK095 | [ ] | PARTIAL | "signal store interface": [repository get_signal](../../apps/api/app/repositories/signal_repository.py#L60) differs from [direct risk read](../../apps/agents/risk_assessment/pipeline.py#L199); no boundary adapter. AUD-012-003, AUD-012-004. |
| CHK096 | [ ] | IMPLEMENTED | "LLMCallMixin exists": [actual method/signature](../../apps/agents/common/llm_mixin.py#L64) inspected, including temperature and fallback; no import executed. |
| CHK097 | [ ] | PARTIAL | "broader security": [MI/RBAC declarations](../../infra/modules/risk-assessment.bicep#L205) present; auth, effective permissions and configured network protection incomplete/unverified. AUD-012-008, AUD-012-027. |
| CHK098 | [ ] | IMPLEMENTED | "sub-operation budgets": [stage latency table](contracts/assessment-pipeline.md#L138) explicitly defines them; measured compliance remains AUD-012-029. |
| CHK099 | [ ] | PARTIAL | "metric alerts": [eight alert definitions](contracts/telemetry.md#L57) exist, but S5 found no risk alert configuration/call chain. AUD-012-026. |
| CHK100 | [ ] | PARTIAL | "structured logs/correlation": [span helper](../../apps/agents/risk_assessment/telemetry.py#L443) sets handoff ID, while LLM calls omit it and runtime logs are mixed text. AUD-012-026. |
| CHK101 | [ ] | PARTIAL | "load/chaos/integration testing": [test plan](plan.md#L30) names suites, but actual assertions and load/outage evidence incomplete. AUD-012-028, AUD-012-029. |
| CHK102 | [ ] | MISSING | "100-concurrent load profile": [target](spec.md#L221) has no local burst/ramp/sustained profile or completed result. AUD-012-029. |

### Remaining Contract Ledgers

The pipeline's stage obligations are covered by FR rows and AUD tasks: intake (001/002/003/010), retrieval
(004), correlation (005/019), contradiction (011), assessment (006/007/013/014/015/018/020), recommendations
(007/009/016/017/021), dispatch (024), and audit finalization (022/023). These numbers refer to AUD-012 IDs,
not collapsed original tasks. All error-table branches are addressed by those tasks. The added extrapolation
stage is assessed under AUD-012-017/018/031, not accepted as a silent change to the eight-stage contract.

| Telemetry metric | Status | Inspected source result |
| --- | --- | --- |
| assessment_latency | PARTIAL | [Final measurement](../../apps/agents/risk_assessment/pipeline.py#L773) exists, but differs from receipt-to-persistence boundary and has no export proof. |
| assessment_count | PARTIAL | [Generation stage](../../apps/agents/risk_assessment/pipeline.py#L738) increments even when persistence failed. |
| handoff_intake_count | PARTIAL | [Intake](../../apps/agents/risk_assessment/pipeline.py#L673) increments only after validation, not all received messages. |
| handoff_rejected_count | PARTIAL | [Target rejection](../../apps/agents/risk_assessment/pipeline.py#L106) counted; malformed/incident cases absent. |
| duplicate_discard_count | IMPLEMENTED | [Duplicate branch](../../apps/agents/risk_assessment/pipeline.py#L126) emits a counter for locally detected duplicates. |
| sla_breach_count | IMPLEMENTED | [Final timer](../../apps/agents/risk_assessment/pipeline.py#L773) emits above ten seconds; timing-boundary defect is separate. |
| escalation_rate_by_type | PARTIAL | [Delivery branch](../../apps/agents/risk_assessment/pipeline.py#L582) increments after delivery, not handoff creation; no recommendation-type dimension. |
| handoff_success_rate | MISSING | [Declared registry member](../../apps/agents/risk_assessment/telemetry.py#L124); S2/S3 found no risk ratio emission. |
| dead_letter_count | IMPLEMENTED | [Failure branch](../../apps/agents/risk_assessment/pipeline.py#L607) emits the counter when an injected delivery exhausts. |
| contradiction_detection_rate | MISSING | [Registry](../../apps/agents/risk_assessment/telemetry.py#L134) only; no ratio emission in risk path. |
| confidence_distribution | IMPLEMENTED | [Generation stage](../../apps/agents/risk_assessment/pipeline.py#L738) records adjusted score. |
| severity_distribution | IMPLEMENTED | [Generation stage](../../apps/agents/risk_assessment/pipeline.py#L738) records severity dimension. |
| stale_signal_rate | MISSING | [Registry](../../apps/agents/risk_assessment/telemetry.py#L147) only; no rate calculation/emission. |
| fallback_mode_activations | PARTIAL | [Generation stage](../../apps/agents/risk_assessment/pipeline.py#L748) counts assessment template fallback, not all recommendation/dependency activations. |
| content_safety_failures | MISSING | [Helper](../../apps/agents/risk_assessment/telemetry.py#L290) exists without a risk caller. |
| audit_buffer_depth | MISSING | [Registry](../../apps/agents/risk_assessment/telemetry.py#L161) only; writer does not emit current depth. |
| audit_tier | MISSING | [Registry](../../apps/agents/risk_assessment/telemetry.py#L165) only; no current tier observation. |
| version_count_per_incident | MISSING | [Registry](../../apps/agents/risk_assessment/telemetry.py#L171) only; no scoped version observation. |
| version_conflict_retries | MISSING | [Helper](../../apps/agents/risk_assessment/telemetry.py#L293) has no counter caller. |

All metric gaps above map to AUD-012-026; declared gauges also need correct observation semantics.
The contract's eight alerts (5-minute SLA, 15-minute sustained SLA, delivery ratio <0.9, >10 fallbacks/5min,
audit tier 2/3 for 5min, buffer >8,000, contradiction ratio >0.5 for 15min, and zero assessments/10min during
an active incident) are **PARTIAL**: [threshold text](contracts/telemetry.md#L57) exists, but S5 found no connected
risk alert rules. Deployment and alert firing are **UNVERIFIED**, AUD-012-026/027/029.

| Custom event | Status | Evidence and gap |
| --- | --- | --- |
| HandoffReceived | IMPLEMENTED | [Validated intake](../../apps/agents/risk_assessment/pipeline.py#L677) calls the event with handoff/incident/tenant. |
| AssessmentGenerated | PARTIAL | [Generation](../../apps/agents/risk_assessment/pipeline.py#L742) emits, but also represents unpersisted work/extrapolation as generated. |
| ContradictionDetected | IMPLEMENTED | [Contradiction stage](../../apps/agents/risk_assessment/pipeline.py#L718) emits required property names; source-name correctness remains AUD-012-011. |
| EscalationTriggered | PARTIAL | [Delivery branch](../../apps/agents/risk_assessment/pipeline.py#L584) emits only on successful delivery. |
| DegradationEvent | PARTIAL | [All-missing](../../apps/agents/risk_assessment/pipeline.py#L688) and template cases emit; Cosmos/partial-store/recovery incomplete. |
| SLABreach | IMPLEMENTED | [Final timing](../../apps/agents/risk_assessment/pipeline.py#L773) emits duration when >10 seconds. |
| VersionConflict | MISSING | [Declared emitter](../../apps/agents/risk_assessment/telemetry.py#L421), no version-counter call found. |

Trace context and hierarchy are **PARTIAL**: [root/stage spans](../../apps/agents/risk_assessment/pipeline.py#L671)
and handoff attributes exist, but there are no dedicated `assign_version`, nested `llm_call`/`template_fallback`,
`content_safety_check`, or per-target `deliver_handoff` spans in the inspected path. No inbound transport parent
extraction is wired, and LLM correlation defaults independently. AUD-012-026 owns the complete hierarchy,
exporter, dimension, event and alert acceptance, not merely registry existence.

Health contract coverage is **PARTIAL** for every dependency check and unhealthy transition, with real one-second
performance **UNVERIFIED**. Override response-shape presence is **PARTIAL** because success can be fictional;
404/409 handling catches text patterns but does not establish correct partitioning or conditional concurrency.
AUD-012-008/009/025 cover the exact request/response/status-code obligations.

## Future Validation Commands and Acceptance Gates

**None of the following product commands was executed in this audit.** Run only after the relevant remediation
and explicit authorization. Use repository root as working directory. Prepare Python 3.12+, the agent and API
dependencies, pytest/pytest-asyncio, existing test import configuration, and the approved project environment.
Install dependency fakes before agent construction; disable live credentials/endpoints for hermetic runs.
Integration markers in [root configuration](../../pyproject.toml#L48) describe mock external services, not proof
of real Azure interaction. Do not simply set a staging flag and assume a skipped test became an acceptance gate.

| Family | Future-only command or procedure | Prerequisites and expected result |
| --- | --- | --- |
| V1: unit/contract | `uv run --project apps/agents pytest tests/unit/ tests/contract/ -k risk_assessment -q` | Prepared environment and FX-1 through FX-7; no network calls. New focused assertions prove exact fields, holds, thresholds, boundaries and errors. Narrow to the owning test file while repairing each task. |
| V2: adapters/scenario | `uv run --project apps/agents pytest tests/integration/test_risk_assessment_cosmos.py tests/integration/test_risk_assessment_service_bus.py tests/simulation/test_bushfire_risk_assessment.py -q` | Actual production adapters under strict stateful fakes, async delivery spies and fixed clocks. Assertions must inspect stored assessment/recommendation documents, message settlement and a complete causal audit ledger. |
| V3: replay/fan-out | `uv run --project apps/agents pytest tests/contract/test_risk_assessment_reproducibility.py tests/unit/test_risk_assessment_extrapolation.py tests/integration/test_risk_assessment_auto_fanout.py -q` | Snapshot-only replay fixtures and explicit mode/clock isolation. Local timing of a sleeping dummy runner is not a production latency result; unconditional skip must be replaced before claiming live gate coverage. |
| V4: service/IaC acceptance | Later authorized Bicep validation and isolated staging rehearsal using the supported host and deployment entrypoint. No deploy command is authorized by this report. | Resolve AUD-012-031; satisfy AVM/policy/identity/network/region prerequisites. Verify queue scaler, ports, partition keys, no audit TTL, writable durable spill, actual sender/receiver/SDK concurrency, health outage behavior, 100 concurrent assessments, 5/10/15-second boundaries and zero drops. Capture commands/results at execution time. |
| V5: domain/human evidence | Later labelled contradiction evaluation and commander exercise/survey using approved fixtures and rubric. | AU fixtures, source/area labels, sample size, threshold interpretation and reviewer consent. Record >=95% detection and >=90% qualifying ratings with denominators; no result is pre-filled here. |
| V6: document/governance | Reconcile decisions, links, original-ID coverage, approvals, hypothesis schema and revision-bound evidence in an authorized follow-up. | No retrospective claims. All 102 checklist answers and 21 gates must distinguish authored design from actual execution/approval. Deferred country promotion uses its separate feature process. |

The test-first instructions and original checkpoints are **UNVERIFIED historical process claims**. Current
test source cannot prove the tests failed before implementation, that checkpoints were exercised, that the
buffer pattern ran in production, that infrastructure passed a What-If review, or that a human approved
templates/public-facing outputs. Do not retroactively mark them complete from this static audit.

## Report-Only Validation and Limitations

The authorized validation for this deliverable is restricted to comparing original task/requirement/checklist
IDs and checkbox states with this report, verifying 22 scenario and seven edge rows, checking amendment/gate
coverage, resolving local evidence links and their line anchors, ensuring all AUD task definitions are unique
and unchecked and all follow-up references resolve, and requesting diagnostics for this Markdown file only.
Any document defect found by those checks must be repaired here, not in original artifacts.

All original task states are preserved in the coverage table. All proposed work is future-only. Measured
latency/capacity/detection/clarity, cloud configuration, SDK wire behavior, security approvals, persona validation,
country calibration, product test outcomes and real deployment remain outside this audit's execution evidence.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 012 only. Three parallel technical reviews examined intake/
provenance, persistence/safety, and runtime/evidence. The source-completable stale-data safety defect was fixed:
when every input signal is below the configured freshness threshold, correlation confidence is forced to zero and
the risk pipeline suppresses all downstream escalation handoffs.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| AUD-012-005 | Source fix complete for all-stale gating. | Added a regression assertion and ran `python -m pytest tests/unit/test_risk_assessment_pipeline.py tests/unit/test_risk_assessment_correlation.py tests/contract/test_risk_assessment_handoff.py -q`: `29 passed`. |
| AUD-012-001–004 / 006–014 | Partial/open safety and persistence work. | Production intake remains disconnected; incident/scope validation, signal provenance, version reservation, persistence failure handling, overrides, contradiction boundaries, and expiry/review workers remain open. |
| AUD-012-015–033 | Evidence/runtime gated. | Audit recovery, health/telemetry, infrastructure wiring, MAF convergence, integration/load/reproducibility, and human/country evidence remain unverified. |

No deployment, broker, Cosmos, model, human approval, performance, or calibration evidence was created. The pass is a
narrow fail-closed stale-data correction, not end-to-end risk-agent readiness.

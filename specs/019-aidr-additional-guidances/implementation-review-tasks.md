# Implementation Review: 019 AIDR Additional Guidance Integration

**Review date**: 2026-09-11  
**Source revision**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Scope**: Fresh, isolated, static review of specification 019. This continues the existing implementation audit; it does not create a feature.  
**Status**: Static review complete; implementation acceptance is not established. All 35 remediation tasks remain open.

## Scope, Inputs, and Evidence Boundaries

The full [Review Contract](../001-spec-implementation-audit/README.md#L13) governs this report. The current HEAD matches the requested revision. The only authored file is this report. No branch, commit, index, source, original task, original document, or evidence artifact is changed. No other implementation audit report is an input; no subagents are used.

Read in full: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [contracts/planning-api.yaml](contracts/planning-api.yaml), [contracts/me-framework-api.yaml](contracts/me-framework-api.yaml), [contracts/recovery-catalogue-api.yaml](contracts/recovery-catalogue-api.yaml), [contracts/ai-analysis-api.yaml](contracts/ai-analysis-api.yaml), [checklists/requirements.md](checklists/requirements.md), and [checklists/deep-review.md](checklists/deep-review.md). The files with `.yaml` extensions contain Markdown contract prose, not executable OpenAPI schemas.

The specification includes its two clarification sessions and later Personas, Hypotheses, and Out of Scope amendments. PH, JP, and BD variants are explicitly deferred; their absence is not an implementation defect under this feature. AU role, privacy, life-safety, and community-engagement obligations remain in scope.

Additional full-document inputs: the relocated [Emergency Planning Handbook](../../docs/corpus/aidr/emergency-planning/handbook.md#L1), [M&E Framework](../../docs/corpus/aidr/monitoring-evaluation-framework/handbook.md#L1), [Outcomes, Activities and Indicators](../../docs/corpus/aidr/outcomes-indicators/handbook.md#L1), [constitution](../../.specify/memory/constitution.md#L1), the directly inherited [specification 018](../018-aidr-guidance-integration/spec.md#L1), [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1), [hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1), and the linked [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1), [post-feature rubric](../028-capstone-alignment/evidence/rubric-postfeature.md#L1), and [decision record](../028-capstone-alignment/evidence/decision-record.md#L1). All six catalogue seed files and all test files expressly named by the original tasks were read. Supporting source was followed into current callers, including the documented MAF replacement and the deployed dispatcher.

Applicable guidance: [code-review.instructions.md](../../.github/instructions/code-review.instructions.md), its [detailed review reference](../../.github/instructions/references/code-review-checklists.md), [Bicep review rules](../../.github/instructions/bicep-code-best-practices.instructions.md), and [policy-compliance rules](../../.github/instructions/bicep-policy-compliance.instructions.md). The Python fact-grounded-coding and Cosmos DB best-practices skills were read; they inform source interpretation, not a substitute checklist of product obligations. Conclusions are limited to inspected source and explicit test assertions. No product tests, builds, imports, deployments, cloud queries, human approvals, or runtime measurements are performed. Future commands below are instructions only, not execution evidence. Report validation reads text and checks identifiers, original checkbox states, source links, line bounds, and open follow-ups.

The inspected source and original feature inputs had no tracked differences from HEAD in the scoped revision check. Local catalogue JSON was parsed only to inventory authored records: 61 outcomes, 155 activities, 152 indicators, and one five-domain evaluation-question document, or 369 flattened seed documents. These counts are not seed-loader execution or database observations.

Evidence statuses are used with the contract meanings:

| Status | Meaning |
| --- | --- |
| IMPLEMENTED | Full scoped source behavior or authored artifact supported by inspected source; runtime success is not implied. |
| PARTIAL | Some behavior exists, but a specific required obligation is absent or contradicted. |
| MISSING | Required behavior or artifact is absent after the stated scoped search. |
| CONFLICT | Requirements, task instructions, or current behavior disagree and need an explicit resolution. |
| UNVERIFIED | Source cannot establish execution, observed outcomes, approval, or deployed state. |
| SUPERSEDED | Explicit repository evidence documents replacement or retirement. |

## Priority-Ordered Findings and Open Remediation

### AUD-019-001: Critical - Plan authorization trusts caller-supplied roles

- [ ] AUD-019-001 Bind plan access and lifecycle authority to authenticated, scoped AIIMS assignments.

**Affected obligations**: FR-006, FR-007, FR-007a; US1 acceptance 1 and 4; US5 acceptance 2 and 4; T027, T034, T040, T041, T042, T063, T065; CHK013, CHK014, CHK033, CHK051. **Status**: PARTIAL.

**Expected versus actual and impact**: Only the assigned Planning Officer may author/edit plans, the appropriate hierarchy-level authority may endorse, and the Incident Controller may activate against a live incident; visibility follows the security rating. The standalone [planning entry point](../../apps/agents/planning/__main__.py#L12) directly serves the factory. The factory has no authentication dependency in [agent.py](../../apps/agents/planning/agent.py#L235), transition handling passes the request's role to the service at [agent.py](../../apps/agents/planning/agent.py#L301), and activation directly mutates the plan without checking an IC assignment at [agent.py](../../apps/agents/planning/agent.py#L336). The role table checks the supplied string, not an authenticated principal. Existing contract tests create a client without identity and assert success for supplied roles at [test_planning_api_contract.py](../../tests/contract/test_planning_api_contract.py#L13) and [test_planning_api_contract.py](../../tests/contract/test_planning_api_contract.py#L84). This is source evidence of an unenforced authorization boundary, not a claim that an exposed deployment was exploited.

**Owning surfaces and developer steps**: Secure the Planning Agent factory and the Platform API emergency-plan routes and service. Resolve identity and AIIMS assignment from trusted request context; scope endorsement authority by hierarchy level and activation authority by incident. Treat body fields such as `created_by`, `activated_by`, and `user_role` as non-authoritative. Enforce security-rating visibility on detail, list, hierarchy, and operational content reads, and apply identical rules to section/process edits, transitions, activation, and post-event review. Preserve documented lifecycle semantics and existing spec 018 role integration; do not invent non-AU permission mappings for the deferred variants.

**Tester steps**: Extend existing [test_planning_api_contract.py](../../tests/contract/test_planning_api_contract.py#L13) and [test_plan_lifecycle.py](../../tests/unit/test_plan_lifecycle.py). Positive: authenticated Planning Officer creates/edits, scoped authority endorses, assigned IC activates a live flood incident. Negative: anonymous requests, spoofed body roles, wrong hierarchy authority, out-of-incident assignments, and insufficient security clearance are rejected without mutation or protected-content disclosure. Edge: role revocation between requests, empty actor fields, and restricted plans appearing in list/hierarchy results. Use the existing flood/region fixture shape and add identity/assignment fixtures in those existing tests; those fixtures are future work, not inspected evidence.

**Future validation**: In an approved local test environment with repository dependencies and existing import-path configuration, run `pytest tests/contract/test_planning_api_contract.py tests/unit/test_plan_lifecycle.py`. Expected assertions: authorized operations succeed; unauthenticated/unauthorized cases return the agreed 401/403 responses; rejected operations leave state and audit actor unchanged; restricted plan content is not returned. This command is not run in this audit.

**Dependencies and acceptance**: Coordinate with the existing identity/AIIMS owner and resolve CHK014/CHK051 permission details without relaxing FR-007a. Complete only when both exposed paths enforce the same trusted identity policy and the positive, negative, and edge assertions above exist and pass in separately recorded validation.

**Additional exposed boundaries**: The registered API has authentication middleware, but [auth_middleware.py](../../apps/api/app/middleware/auth_middleware.py#L18) populates claims rather than enforcing these permissions. The production role middleware's [protected prefixes](../../apps/api/app/middleware/rbac_check.py#L33) do not include the 019 routes registered by [router.py](../../apps/api/app/api/router.py#L86). Apply the roles in the [M&E contract](contracts/me-framework-api.yaml#L6), [analysis contract](contracts/ai-analysis-api.yaml#L6), and [catalogue contract](contracts/recovery-catalogue-api.yaml#L6) as well: Recovery Coordinator manages/requests, IC views, and catalogue browsing requires authentication. Do not mistake geographic filter arguments for verified jurisdiction authority. Related original tasks: T044, T049, T051, T053, T056, T061. Validate both factories and the full API middleware stack, including protected-plan filtering across AU regions; external ingress configuration is UNVERIFIED.

### AUD-019-002: Critical - Safety is bypassed or asserted without validation

- [ ] AUD-019-002 Withhold unvalidated AI output and record the real content-safety decision.

**Affected**: FR-028; FR-014, FR-025, FR-026, FR-027; US4-AS4; T014, T032, T048, T059, T060, T062; CHK041, CHK064. **Status**: CONFLICT.

**Expected/actual/impact**: Every generated analysis, rationale, summary, and evaluation must pass the existing safety pipeline before presentation. The conditional LLM branch explicitly returns `ai_summary` with `not_validated` at [indicator_analysis.py](../../apps/agents/monitoring/indicator_analysis.py#L97), and [its test](../../tests/unit/test_indicator_analysis.py#L202) expects that behavior. Both [agent evaluation](../../apps/agents/monitoring/me_framework_service.py#L139) and [API evaluation](../../apps/api/app/services/me_framework_service.py#L223) assign `passed` solely from the requested mode. The unused [EvaluationService](../../apps/agents/monitoring/evaluation_service.py#L22) checks a constant string, not the output. Default analysis is rule-based, not observed live AI; the defect is the bypass and unsupported safety claim, not proof that a deployed model produced harmful text.

**Developer steps**: Own the monitoring analysis/evaluation services, API facades, factories, and EvaluationReport boundary. Inject the existing [ContentSafetyValidator](../../apps/agents/common/content_safety.py#L54), validate the exact assembled content, and propagate its method, review flag, failure reason, and validation identity. Absent validator, exception, timeout, or rejection must withhold AI fields and return explicitly non-AI structured fallback. Manual mode must not acquire a fabricated AI approval. Validate generated recommendations and summaries as well as correlations; preserve required human dissemination review.

**Tester positive**: In [test_indicator_analysis.py](../../tests/unit/test_indicator_analysis.py#L149) and [test_evaluation_report.py](../../tests/unit/test_evaluation_report.py#L1), use a deterministic generated-text fixture and assert that exactly the displayed text is validated before release.

**Tester negative**: Replace the unsafe expectation at the cited test; assert no AI text for missing validator, rejected content, exception, or missing safety result. A model field containing an arbitrary nonempty string is not proof of validation.

**Tester edge**: Empty output, long multi-domain output, keyword-fallback review flags, mixed safe/unsafe sections, and manual reports must retain honest provenance. Exercise the real factory dependency wiring, not only unrestricted MagicMock objects.

**Future check**: With local dependencies installed, run `pytest tests/unit/test_indicator_analysis.py tests/unit/test_evaluation_report.py tests/contract/test_me_framework_api_contract.py`. No cloud credentials are needed for injected test doubles. Expected: withheld unsafe fields and exact-text validation assertions on every branch.

**Dependencies/acceptance**: Depends on the existing safety contract, not new AI infrastructure. Accept when all presentation paths fail closed and no code or assertion manufactures a successful safety decision.

### AUD-019-003: Critical - Lifecycle, endorsement, and version guarantees diverge

- [ ] AUD-019-003 Reconcile the two state machines and implement incident-aware, version-preserving transitions.

**Affected**: FR-006, FR-007, FR-007a; US1-AS4, US5-AS2, US5-AS4; activation-during-revision edge; T009, T026, T027, T033, T040, T041, T063, T065; CHK029, CHK042, CHK045, CHK051, CHK052, CHK054, CHK060. **Status**: CONFLICT.

**Expected/actual/impact**: FR-006 requires the specified roles, live/concluded incident checks, new version creation after review, system-conditioned supersession, and a terminal superseded state. [Agent transitions](../../apps/agents/planning/plan_lifecycle.py#L11) differ from the [domain state machine](../../packages/domain/src/domain/models/plan_lifecycle.py#L22); the latter is what [T033 tests import](../../tests/unit/test_plan_lifecycle.py#L9). Those tests [reject the required review-to-draft transition](../../tests/unit/test_plan_lifecycle.py#L77). The live [agent transition](../../apps/agents/planning/agent.py#L143) and [API transition](../../apps/api/app/services/emergency_plan_service.py#L125) mutate raw state only, with no incident argument, endorsement fields, new version, or endorsed snapshot. The [fallback helper](../../apps/agents/common/plan_activation.py#L12) has no inspected runtime caller and no snapshot producer. Invalid or obsolete plans can therefore be represented as operationally endorsed/activated.

**Developer steps**: Establish one authoritative transition contract with the spec owner before retiring either module. Enforce every FR-006 transition and condition in the shared service; use verified principals from AUD-019-001 and persisted incident state. Store immutable endorsed versions, endorsement identity/time, rationale, amendments, activation/deactivation history, and explicit draft lineage. Review-to-draft creates a new version and supersedes its original as specified; newer endorsement performs only the permitted system supersession. Apply conditional writes to prevent concurrent endorsement/activation from losing history. Resolve the contract's post-event editable-state disagreement explicitly.

**Tester positive**: Extend [test_plan_lifecycle.py](../../tests/unit/test_plan_lifecycle.py#L20), [planning contract tests](../../tests/contract/test_planning_api_contract.py#L84), and [plan repository tests](../../tests/integration/test_emergency_plans_cosmos.py#L1) with the complete FR-006 matrix, linked live/concluded incidents, and endorsed-v1/draft-v2 fixtures.

**Tester negative**: Missing/closed incident activation, early post-event review, wrong authority, arbitrary supersession, reactivation of a terminal plan, and direct state bypass must leave documents unchanged.

**Tester edge**: Concurrent updates, repeated requests, rejected drafts, superseded parents, and activation during revision must retain the correct endorsement and return a draft-versus-active warning.

**Future check**: In an isolated local fixture environment, run `pytest tests/unit/test_plan_lifecycle.py tests/contract/test_planning_api_contract.py tests/integration/test_emergency_plans_cosmos.py`; an emulator-backed extension is required for conditional-write guarantees. Expected: identical matrices across entry points and preserved version/history assertions, not only state-string equality.

**Dependencies/acceptance**: Requires AUD-019-001 and durable state. Accept only after the conflicting matrix is resolved by an explicit decision and tests exercise the same state machine as both runtime callers.

### AUD-019-004: Critical - Small-cohort privacy is not guaranteed on the extended paths

- [ ] AUD-019-004 Enforce population-aware privacy before storage, analysis, and public presentation.

**Affected**: NFR-009; FR-024, FR-027, FR-030, FR-031; US3-AS6; T008, T045, T047, T050, T059, T060, T061; plan gate NN-3. **Status**: PARTIAL.

**Expected/actual/impact**: The inherited privacy requirement covers community aggregates identifiable to fewer than ten people. [RecoveryIndicator](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L75) rejects only sensitive social values when coverage is supplied. The reachable [update service](../../apps/api/app/services/recovery_service.py#L83) also accepts unknown coverage, and only health/employment are initially classified sensitive. The [new analysis inputs](../../apps/api/app/api/routes/ai_analysis.py#L22) are arbitrary dictionaries without cohort, classification, or population validation. The existing [community view](../../apps/api/app/services/recovery_service.py#L174) does filter sensitive indicators, but the new analysis/report routes do not call it. This leaves the new catalogue/cohort extension without the promised privacy boundary; no actual disclosure is claimed.

**Developer steps**: Own RecoveryIndicator, recovery and M&E ingress, analysis input assembly, and report/public projections. Keep the optional catalogue link backward compatible, but require sufficient population metadata for sensitive aggregates and decide how unknown coverage is withheld. Apply the policy to social issues and newly introduced social indicators, not just two names. Validate typed persisted inputs before deriving prompts, report evidence, summaries, or public output; preserve safe aggregates and clearly explain suppressed data without leaking values. Use authorised community-group definitions, not ad hoc person-identifying labels.

**Tester positive**: Extend [test_emergency_plan.py](../../tests/unit/test_emergency_plan.py#L1) and [test_recovery_contract.py](../../tests/contract/test_recovery_contract.py#L1) with ten-person aggregate fixtures and authorised non-sensitive indicators; accepted aggregates retain catalogue linkage.

**Tester negative**: Nine-person, missing-count, negative-count, and person-identifying inputs must not reach persistence, model requests, or community output. Test both direct analysis inputs and stored-tracker inputs.

**Tester edge**: Cohort size changes after collection, multiple intersecting subgroups, qualitative sensitive text, and a legacy indicator with no catalogue link must not bypass suppression or break existing safe reads.

**Future check**: With synthetic data and no cloud calls, run `pytest tests/contract/test_recovery_contract.py tests/unit/test_emergency_plan.py tests/unit/test_indicator_analysis.py`. Expected assertions cover response, persistence, and captured prompt content at the 9/10 boundary.

**Dependencies/acceptance**: Coordinate with the privacy and community representatives and AUD-019-001/AUD-019-002. Accept when all newly reachable outputs inherit the same reviewed policy; subgroup data collection is not permission to weaken k-anonymity.

### AUD-019-005: Important - Agent and API state are separate, with silent volatile fallback

- [ ] AUD-019-005 Connect the feature to durable, shared repositories and explicit degraded behavior.

**Affected**: FR-006, FR-008, FR-010, FR-014, FR-030, FR-031; NFR-005, NFR-006; graceful-degradation contracts; T004, T022, T023, T040, T043, T047, T049, T050, T052. **Status**: PARTIAL.

**Expected/actual/impact**: Plans, logic, and evaluations must remain available across agent/API requests and revisions. [PlanningAgent](../../apps/agents/planning/agent.py#L42) uses its own dictionary; [MEFrameworkService](../../apps/agents/monitoring/me_framework_service.py#L16) does the same. The registered API uses repositories, but [plan repository construction](../../apps/api/app/repositories/emergency_plan_repository.py#L36) and [M&E construction](../../apps/api/app/repositories/me_framework_repository.py#L36) silently fall back to memory on missing configuration or failed initialization. Point-read exceptions become `None`. The Cosmos-labelled [plan tests](../../tests/integration/test_emergency_plans_cosmos.py#L1) and [M&E tests](../../tests/integration/test_me_framework_cosmos.py#L1) expressly use in-memory repositories. Authored repository methods are real source support, not proof of shared persistence or recovery from outages.

**Developer steps**: Inject a shared persistence abstraction into both factories and API services; make volatile storage an explicit test/development choice. Distinguish not-found from unavailable storage, and implement the documented 503/degraded response plus timestamped last-known plan where available. Preserve partition scopes and document identity, use conditional updates for mutable plans/frameworks, and link program logic/report writes consistently. Health must reflect the configured dependency state instead of unconditional planning `healthy`.

**Tester positive**: Reuse the existing integration test files with a partition-aware fake and a separately authorised local emulator fixture: create through one process, read through another, and restart the producer without losing plans, process records, logic, or evaluations.

**Tester negative**: Wrong partition, unavailable storage, initialization failure in production mode, and failed secondary writes must not look like successful durable writes or 404s.

**Tester edge**: Concurrent update/retry, duplicate document IDs across partitions, interrupted multi-document operations, and cache expiry must preserve identity and disclose staleness.

**Future check**: Run `pytest tests/integration/test_emergency_plans_cosmos.py tests/integration/test_me_framework_cosmos.py` only after fixtures explicitly separate in-memory and local-emulator modes. Existing constructors can use `COSMOS_ENDPOINT`; ensure it is unset for doubles or points only to the approved emulator. Expected: restart/cross-instance persistence and failure classification assertions.

**Dependencies/acceptance**: Maintain the documented region/incident partition contracts and compatibility with spec 018. Accept when API and agent observe the same durable records and no production failure silently switches to volatile state.

### AUD-019-006: Important - Audit helpers do not establish a durable decision trail

- [ ] AUD-019-006 Persist authentic plan and M&E decision provenance through the shared audit path.

**Affected**: FR-006, FR-007a, FR-014, FR-028, FR-032, FR-033; Constitution IV and human-review gates; T037, T040, T041, T048, T050, T063, T065, T070, T071; CHK058. **Status**: PARTIAL.

**Expected/actual/impact**: Operators must trace decisions to people, inputs, rationale, and resulting versions. [audit.py](../../apps/agents/planning/audit.py#L11) authors suitable helper dictionaries, but [agent updates](../../apps/agents/planning/agent.py#L111) append only to a private list and use `system` for edits; transition user identity is the role string. Activation and post-event routes bypass even that list. The API transition service has no audit write, and no inspected caller uses the endorsement helper. M&E mutations and generated report labels do not establish a human review or dissemination approval.

**Developer steps**: Route section/process edits, endorsement/rejection, activation, post-event review, M&E configuration changes, evaluation generation, and dissemination decisions into the existing durable audit mechanism. Record verified actor, scope, source document version, before/after state, rationale, correlation, safety provenance, and human approval separately. Preserve failed-attempt events without storing suppressed personal data; use idempotent event identifiers and define audit-store outage behavior.

**Tester positive**: Add captured audit-sink assertions to [planning contract tests](../../tests/contract/test_planning_api_contract.py#L1) and [M&E contract tests](../../tests/contract/test_me_framework_api_contract.py#L1): one successful mutation produces one attributable event with the resulting version.

**Tester negative**: Spoofed actors, missing rationale, failed persistence, and rejected/unsafe evaluations must not yield a successful approval record.

**Tester edge**: Repeated handoffs, concurrent edits, audit-store outage, and partial report generation must retain traceability without duplicate successful decisions or PII leakage.

**Future check**: Run `pytest tests/contract/test_planning_api_contract.py tests/contract/test_me_framework_api_contract.py` with injected persistence/audit fakes, followed by separately approved durability checks. Expected: actor/version/correlation/payload assertions, not a count of helper dictionaries.

**Dependencies/acceptance**: Depends on AUD-019-001, AUD-019-002, and AUD-019-005. Accept when a reviewer can follow the actual persisted decision chain; authored audit helpers or report fields alone do not close this task.

### AUD-019-007: Important - Plan slots are not the required document-assembly workflow

- [ ] AUD-019-007 Deliver complete, versioned plan retrieval and document assembly.

**Affected**: FR-002; NFR-001; SC-001; US1-AS3; T009, T034, T035, T039, T040, T041, T042; CHK001, CHK012, CHK020, CHK039. **Status**: PARTIAL.

**Expected/actual/impact**: All 27 elements must be present in the generated document, with JSON interoperability and the assumed PDF distribution path. The [27 slugs](../../packages/domain/src/domain/models/emergency_plan.py#L26) and empty section initialization exist. However, [pipeline.py](../../apps/agents/planning/pipeline.py#L12) only computes/checks completeness; it has no assembly or export function. The [agent detail route](../../apps/agents/planning/agent.py#L283) returns `_to_summary`, discarding sections and process information. API detail can return a raw full dictionary when the region key is supplied, which is partial JSON support, not the contracted document workflow. No assembly/PDF replacement was found in the scoped planning/API/client search.

**Developer steps**: Own the planning pipeline, models, service, and routes. Return full plan/process information on detail reads and a section on section updates; preserve all 27 canonical elements, authority, version, amendments, distribution, PPRR arrangements, and exercise/review information in exports. Implement human-authored content assembly and a supported PDF path, with explicit incomplete-content behavior and the configured deadline. Preserve existing summary consumers through an agreed compatibility adapter rather than silently changing their fields.

**Tester positive**: Extend [planning contract tests](../../tests/contract/test_planning_api_contract.py#L1) with a complete 27-section flood plan containing distinguishable content and verify every section and version in full JSON and exported text.

**Tester negative**: Unknown slugs, absent required content, insufficient clearance, and an unendorsed version presented as endorsed must be rejected or clearly identified, never silently omitted.

**Tester edge**: Long sections, glossary/contents, empty optional narrative with approved justification, concurrent version changes, and export timeout; do not confuse the 15-second assembly target with 10-second activation retrieval.

**Future check**: After adding assembly assertions, run `pytest tests/contract/test_planning_api_contract.py tests/unit/test_emergency_plan.py`; PDF renderer and local export fixtures are prerequisites. Expected: exact 27-element coverage and faithful content, not only `len(slugs) == 27`.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-003, AUD-019-005 and agreed section-content criteria. Accept when full authored content is accessible and distributable; measured latency remains a separate validation gate.

### AUD-019-008: Important - Nine-step guidance and eight-principle validation stop at flags

- [ ] AUD-019-008 Connect structured planning records and principle evidence to the planning workflow.

**Affected**: FR-001, FR-004; SC-002; US1-AS1; T010, T029, T039, T040, T041; CHK002, CHK004, CHK068. **Status**: PARTIAL.

**Expected/actual/impact**: The platform must guide each AIDR step and use all eight principles as completeness criteria. [PlanningProcessRecord](../../packages/domain/src/domain/models/planning_process_record.py#L85) models teams, consultation, risk references, and endorsements, but [agent creation](../../apps/agents/planning/agent.py#L54) stores only a `process_steps` dictionary. Step updates accept independent flags; they do not advance or validate a structured process record. Principles start empty, have no update/evidence workflow, and the unused [endorsement helper](../../apps/agents/planning/pipeline.py#L44) accepts only 50% section completion while actual transitions do not call it.

**Developer steps**: Store/retrieve the typed process record with the plan; guide entry/exit outputs for project planning, team formation, consultation, risk, strategies, trial, endorsement, implementation/exercise, and review. Link team and engagement records, preserve iterative rework, and derive or record reviewable evidence for each principle. Do not invent an arbitrary universal gate where CHK002 needs an owner decision; define the agreed evidence criteria explicitly and enforce them consistently.

**Tester positive**: Extend [test_planning_process_record.py](../../tests/unit/test_planning_process_record.py#L1) and [planning simulation](../../tests/simulation/test_planning_me_scenarios.py#L30) with all nine steps, a team, consultation entries, risk reference, and eight independently distinguishable principle records.

**Tester negative**: Unsupported completion, invalid/mismatched step identifiers, missing completion actor, or falsely checked principles must not certify readiness.

**Tester edge**: Reopen earlier steps after consultation, update a team member, and reject then resubmit endorsement without erasing prior evidence.

**Future check**: Run `pytest tests/unit/test_planning_process_record.py tests/contract/test_planning_api_contract.py tests/simulation/test_planning_me_scenarios.py` with injected stores and actors. Expected: persisted step outputs and principle-specific readiness assertions.

**Dependencies/acceptance**: Depends on AUD-019-003, AUD-019-005, AUD-019-006 and the planner-approved criteria. Accept when a nine-step user journey produces more than nine booleans.

### AUD-019-009: Important - The renamed risk helper returns fixed risk levels

- [ ] AUD-019-009 Wire evidence-based four-environment risk assessment into plan development.

**Affected**: FR-003; US1-AS2; T038, T040; CHK002. **Status**: PARTIAL.

**Expected/actual/impact**: Hazard/consequence analysis must cover social, built, economic, and natural environments, including cascading, concurrent, and catastrophic cases. The historical `risk_assessment.py` has a current counterpart, [plan_risk_assessment.py](../../apps/agents/planning/plan_risk_assessment.py#L17). It returns `medium` for every environment and generic cascade text; the scoped call search found only its definition. Scenario labels and copied hazards do not establish contextual risk analysis.

**Developer steps**: Own the renamed helper, PlanningProcessRecord risk link, and controlling planning service. Consume authoritative hazard/consequence evidence or a documented human risk study; calculate/structure environment-specific impacts and uncertainty, and connect the result to step 4 and plan strategies. Concurrent and catastrophic scenarios need their own contextual assessment rather than only a label. Reuse existing risk-assessment capabilities while preserving their distinct AIIMS Intelligence role.

**Tester positive**: In [planning simulation tests](../../tests/simulation/test_planning_me_scenarios.py#L30), introduce flood/secondary-infrastructure-failure and multi-hazard fixtures with different impacts in all four environments; assert linked evidence and differentiated results.

**Tester negative**: Missing risk-study inputs must not produce an authoritative medium-risk conclusion; invalid scenario/domain values are rejected.

**Tester edge**: Concurrent hazards, exhausted capacity in a catastrophic scenario, contradictory evidence, and a region with no observations must expose uncertainty and human review needs.

**Future check**: After adding the cases, run `pytest tests/simulation/test_planning_me_scenarios.py tests/contract/test_planning_api_contract.py`. All external risk inputs must be deterministic fixtures. Expected: changes in input change the relevant findings and references.

**Dependencies/acceptance**: Requires AUD-019-008 and the existing risk service contract. Accept only with a real caller; renaming the helper or adding more canned text is insufficient.

### AUD-019-010: Important - Plan currency and exercises are not scheduled or measured

- [ ] AUD-019-010 Implement plan review reminders and exercise completion records.

**Affected**: FR-006; NFR-007; US1-AS4; T002, T036, T040, T065; CHK003, CHK019, CHK022, CHK035. **Status**: PARTIAL.

**Expected/actual/impact**: Plans need version/endorsement currency, next review date, exercise dates/completion, and reminders by interval or significant event. The [model](../../packages/domain/src/domain/models/emergency_plan.py#L100) and [configuration](../../apps/agents/planning/config.py#L14) contain fields/defaults, but creation and routes do not manage schedules or reminders. [Governance readiness](../../apps/api/app/services/governance_data_service.py#L366) derives endorsement from framework metadata and never computes an overdue date; [exercise breakdown](../../apps/api/app/services/dashboard_aggregation_service.py#L429) is derived from phase distribution, not exercise completion.

**Developer steps**: Store authoritative review/exercise schedules and completion history; implement clock-based reminders and incident/exercise-triggered review. Feed readiness from those records, with real due dates and explicit unavailable status. Define exercise types/frequency with the planning owner and use validated configurable intervals, not fabricated completion percentages.

**Tester positive**: Add frozen-clock fixtures to [planning integration tests](../../tests/integration/test_emergency_plans_cosmos.py#L1) and assert a due reminder and an exercise completion update change currency/readiness.

**Tester negative**: Future-due plans, cancelled exercises, and missing review evidence must not be marked overdue/completed incorrectly.

**Tester edge**: Exact due boundary, timezone offsets, leap dates, overdue endorsed plans, superseded versions, and repeated significant-event notifications.

**Future check**: Run `pytest tests/integration/test_emergency_plans_cosmos.py tests/simulation/test_planning_me_scenarios.py` after adding scheduler cases. Prerequisites: injected clock and event delivery, no cloud scheduler. Expected: date-sensitive reminders, retained completion records, and correct denominators.

**Dependencies/acceptance**: Requires AUD-019-003, AUD-019-005, AUD-019-008. Accept when the schedule is operational, not just a model field or environment variable.

### AUD-019-011: Important - Plan hierarchy is a regional list, not an interoperable hierarchy

- [ ] AUD-019-011 Build and validate AU plan relationships and meaningful conflict flags.

**Affected**: FR-005; US1-AS5; plan-hierarchy-conflicts edge; T022, T034, T040, T041, T042, T076; CHK025, CHK043, CHK053, CHK054. **Status**: PARTIAL.

**Expected/actual/impact**: A national/state/regional/local tree must expose relationships and conflicts in terminology, responsibilities, and arrangements. The [repository hierarchy query](../../apps/api/app/repositories/emergency_plan_repository.py#L128) and [agent hierarchy method](../../apps/agents/planning/agent.py#L182) only filter by exact region. Parents in broader regions are not traversed. The disconnected [conflict helper](../../apps/agents/common/edge_cases.py#L87) only notices a local plan without a parent, not inconsistent arrangements.

**Developer steps**: Resolve ancestor/child references across authorised AU scopes; validate hierarchy levels, referential integrity, and cycles. Return the contracted tree and actionable interoperability flags with source sections and AIDR references. Surface a superseded/missing parent without silently choosing new operational arrangements. Conflict resolution belongs to the designated human authority; PH/JP/BD capability is not implied.

**Tester positive**: Extend [hierarchy integration tests](../../tests/integration/test_emergency_plans_cosmos.py#L1) with national, NSW, Northern Rivers, and local plans under different region keys; assert all authorised ancestors and children.

**Tester negative**: Cycles, missing parents, invalid levels, and unauthorised parent content must be rejected or safely flagged.

**Tester edge**: Contradictory roles/terminology, incomplete hierarchies, and superseded parents must produce specific flags without automatic override.

**Future check**: Run `pytest tests/integration/test_emergency_plans_cosmos.py tests/contract/test_planning_api_contract.py` with cross-region parent fixtures. Expected: tree relationships and conflict detail, not only `len(hierarchy) == 2`.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-003, AUD-019-005 and documented human resolution policy. Accept when the hierarchy and flags reach the user-facing caller.

### AUD-019-012: Important - Incident lookup and operational plan activation are incomplete

- [ ] AUD-019-012 Connect incident matching and activation to complete phase-specific plan content.

**Affected**: FR-007, FR-029; SC-008; US5-AS1, US5-AS2, US5-AS3, US5-AS4; T026, T063, T065, T066. **Status**: PARTIAL.

**Expected/actual/impact**: Region/hazard-relevant plans must be recommended and activation must surface roles, resources, response arrangements, and communications, followed by recovery/M&E links and post-event review. [Incident lookup](../../apps/api/app/api/routes/emergency_plans.py#L103) always returns an empty list. [Activation](../../apps/agents/planning/agent.py#L336) returns only response arrangements and does not verify incident existence or call the fallback helper. Post-event review is a separate unauthenticated state flip, not incident-conclusion driven. These are specific stubbed paths, not missing filenames.

**Developer steps**: Own emergency-plan routes/service and the incident/PPRR integration. Match a real incident's authorised region, hazards, and relevant plan hierarchy; return explained recommendations. Activate through the shared transition service, resolve the endorsed version, and expose every contracted operational section plus activation record. Reference phase-specific recovery arrangements and linked M&E frameworks while retaining response/recovery overlap semantics. Trigger post-event review from confirmed closure, not arbitrary requests.

**Tester positive**: Extend [planning contract tests](../../tests/contract/test_planning_api_contract.py#L1) and [planning/M&E simulation](../../tests/simulation/test_planning_me_scenarios.py#L30) with a live flood incident, full endorsed plan, and distinct roles/resources/comms/recovery content.

**Tester negative**: Wrong region/hazard, missing incident, closed incident, unendorsed plan, and no relevant plan must not create activation history or leak unrelated content.

**Tester edge**: Endorsed-v1 plus draft-v2, multiple matching plans, concurrent incidents, duplicate activation, and partial recovery overlap.

**Future check**: Run `pytest tests/contract/test_planning_api_contract.py tests/simulation/test_planning_me_scenarios.py` against one shared test store. Expected: matching plan IDs, all four operational content groups, recovery linkage, and closure-driven review. Measure the 10-second target separately.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-003, AUD-019-005, AUD-019-011. Accept when the incident controller uses the real plan, not an acknowledged request or canned empty result.

### AUD-019-013: Important - Neither legacy transport nor its replacement runs the 019 handoffs

- [ ] AUD-019-013 Integrate planning activation and M&E handoffs through the supported orchestration path.

**Affected**: FR-007, FR-029, FR-030; US5-AS1, US5-AS3, US5-AS4; T025, T026, T064, T077; R-010; CHK013, CHK065, CHK066. **Status**: PARTIAL.

**Expected/actual/impact**: Incident requests and recovery transitions must actually activate plans/initialize M&E. [Legacy handoffs](../../apps/agents/common/handoffs.py#L1) explicitly document replacement by MAF; the authored [plan/M&E builders](../../apps/agents/common/handoffs.py#L192) remain, but the [planning handler](../../apps/agents/planning/agent.py#L213) only acknowledges that it would activate a plan. The scoped source search found no `planning-handoffs` consumer or runtime builder caller. The [replacement workflow](../../apps/agents/maf_runtime/workflow/builder.py#L80) runs five response executors, with no 019 plan/M&E path; the replacement-directory search also found no such behavior.

**Developer steps**: Resolve the transport decision with the orchestration owner. Implement the required behavior in the supported workflow, or a documented compatibility consumer if still required; do not resurrect a deprecated queue silently. Deliver authenticated, scope-preserving, idempotent activation and M&E initialization with retry/dead-letter semantics. Preserve PPRR overlap and emit durable correlations linking incident, plan version, framework, and resulting action.

**Tester positive**: Extend [test_planning_me_scenarios.py](../../tests/simulation/test_planning_me_scenarios.py#L1) with a real orchestrator/transport test double that drives both factories and verifies persisted state, not just event construction.

**Tester negative**: Invalid scope, unauthorised actor, malformed payload, unendorsed plan, and failed persistence must not be acknowledged as successful execution.

**Tester edge**: Redelivery, out-of-order phase events, consumer restart, and partial handoff failures must not duplicate frameworks or activation records.

**Future check**: Run `pytest tests/simulation/test_planning_me_scenarios.py` after registering the supported transport fixture. Expected: end-to-end state assertions, retry/dead-letter assertions, and preserved identity. No Service Bus or cloud operation is executed by this audit.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-003, AUD-019-005, AUD-019-012. The transport is documented as SUPERSEDED; the feature's required behavior is not documented as retired and remains open.

### AUD-019-014: Important - The catalogue is a rewritten subset, not a faithful AIDR reference

- [ ] AUD-019-014 Reconcile seeded outcomes, activities, indicators, and KEQs to the authoritative sources.

**Affected**: FR-009, FR-011, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021; US2-AS1, US2-AS3; US3-AS1, US3-AS2, US3-AS3, US3-AS4; T015, T016, T017, T018, T019, T020, T021, T031, T054, T057, T058; CHK006, CHK008, CHK009, CHK032, CHK044, CHK062, CHK070. **Status**: PARTIAL.

**Expected/actual/impact**: The feature requires the full AIDR catalogue, explicit undeveloped outcomes, and separately governed custom extensions. The checked-in inventory is 61 outcomes/155 activities/152 indicators, not approximately 61/200/300, and every outcome is marked developed. More importantly, the [source explicitly has undeveloped insurance and vulnerable-group outcomes](../../docs/corpus/aidr/outcomes-indicators/handbook.md#L115), while [overarching.json](../../packages/domain/src/domain/seed/recovery-catalogue/overarching.json#L5) substitutes broad resilience/governance categories. [Source community health](../../docs/corpus/aidr/outcomes-indicators/handbook.md#L168) has one activity and many named indicators; [social.json](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L5) substitutes three activities and three indicators. The [undeveloped built linkage](../../docs/corpus/aidr/outcomes-indicators/handbook.md#L1798) is not retained as such. Five generic questions per KEQ domain in [evaluation-questions.json](../../packages/domain/src/domain/seed/recovery-catalogue/evaluation-questions.json#L1) are not a complete mapping to [M&E section 5.2](../../docs/corpus/aidr/monitoring-evaluation-framework/handbook.md#L1950). Approximate counts alone are not the basis of this finding; the inspected semantic substitutions are.

**Developer steps**: Own seed data and its provenance manifest with an AIDR subject-matter reviewer. Map every source outcome, activity, indicator, methodology, and KEQ to a stable ID and source/page anchor. Restore undeveloped entries without inventing authoritative content; mark locally authored enrichments as custom and preserve their provenance separately. Validate domain/parent/child ID consistency and maintain an explicit migration map for any replaced seed IDs so existing frameworks do not silently change meaning.

**Tester positive**: Extend [catalogue unit tests](../../tests/unit/test_catalogue_service.py#L19) and [seed integration tests](../../tests/integration/test_recovery_catalogue_cosmos.py#L20) with an independently reviewed expected-ID/provenance manifest across all five domains, including natural heritage and economic vulnerability outcomes.

**Tester negative**: Omitted entries, duplicate IDs, altered AIDR meaning, unlabelled invented methodology, and custom records overwriting `aidr:` entries must fail validation.

**Tester edge**: No activities, no indicators, overlapping outcome themes, qualitative/both types, and a later catalogue edition must preserve explicit gaps and existing program links.

**Future check**: Run `pytest tests/unit/test_catalogue_service.py tests/unit/test_recovery_outcome.py tests/integration/test_recovery_catalogue_cosmos.py` against the reviewed manifest, not only positive-count assertions. Prerequisite: human-approved source mapping, which is not claimed here.

**Dependencies/acceptance**: Depends on source-provenance approval and compatibility decisions. Accept when completeness and attribution are demonstrable; do not pad counts to 561 or relabel custom guidance as AIDR.

### AUD-019-015: Important - Catalogue API wiring and Cosmos result handling are incomplete

- [ ] AUD-019-015 Connect catalogue browsing/suggestions and correct repository response semantics.

**Affected**: FR-009, FR-011, FR-015, FR-020, FR-021, FR-026; T024, T053, T054, T055, T056, T057, T058; catalogue contract; CHK008, CHK013. **Status**: PARTIAL.

**Expected/actual/impact**: Runtime catalogue browsing must use the seeded reference source and expose nested details, summaries, filters, suggestions, and KEQs. [API routes](../../apps/api/app/api/routes/recovery_catalogue.py#L14) construct `RecoveryCatalogueService()` without a repository, so its [default methods](../../apps/api/app/services/recovery_catalogue_service.py#L13) return empty data. Even with a repository, `suggest_activities` is a stub and there is no Platform API KEQ route. The agent uses [file-backed CatalogueService](../../apps/agents/monitoring/catalogue_service.py#L28), not the runtime Cosmos source described in R-004. The Cosmos [summary loop](../../apps/api/app/repositories/recovery_catalogue_repository.py#L144) compares singular `kind` values with plural keys, so counts remain zero; its in-memory branch differs. The declared composite index also does not match the catalogue query's two-field ordering, requiring real backend validation.

**Developer steps**: Inject the real catalogue repository, implement hydration/suggestions and KEQ reads, fix singular-to-plural aggregation, and align actual ordering/indexes. Honor outcome/objective/has-indicators filters and the contracted summary fields. Make backend failures distinguishable from an empty catalogue, use an explicitly bounded immutable-data cache, and keep the agent/API source consistent. Preserve the already implemented [loader/main integration](../../scripts/seed_loader.py#L263), which flattens and upserts source data.

**Tester positive**: Extend [catalogue contract tests](../../tests/contract/test_recovery_catalogue_contract.py#L14) to the registered Platform API and a partition-aware fake: seed an outcome, activity, indicator, and KEQ; assert detail hydration, every count, filtering, and suggestions.

**Tester negative**: Missing repository, unavailable catalogue, wrong partition, unknown outcome, and wrong `kind` must not masquerade as a valid empty result.

**Tester edge**: Undeveloped outcome, custom extension, cache expiry, all-five-domain browse, and repeated seeding. The Cosmos branch must be exercised separately from the in-memory branch.

**Future check**: Run `pytest tests/contract/test_recovery_catalogue_contract.py tests/unit/test_catalogue_service.py tests/integration/test_recovery_catalogue_cosmos.py` with explicit no-cloud doubles, then a separately approved local Cosmos test for query/index compatibility. Expected: known nonzero backend counts and exact contract shapes.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-005, AUD-019-014. Accept when a normally constructed API returns the same reference records as the agent without manual private-state injection.

### AUD-019-016: Important - M&E configuration accepts unvalidated, incomplete framework data

- [ ] AUD-019-016 Enforce catalogue-linked M&E configuration and the full evaluative lifecycle.

**Affected**: FR-008, FR-009, FR-011, FR-012, FR-022; US2-AS1, US2-AS2, US2-AS3; T011, T030, T044, T045, T047, T049, T050, T051; CHK005, CHK023, CHK040, CHK046, CHK049, CHK070. **Status**: CONFLICT.

**Expected/actual/impact**: Selection must validate real outcomes, enrich them with catalogue metadata and suggested interventions/indicators, allow community restatement/custom definitions, and support the complete evaluative lifecycle. [Agent selection](../../apps/agents/monitoring/me_framework_service.py#L60) and [API selection](../../apps/api/app/services/me_framework_service.py#L73) simply replace a list. [Contract tests](../../tests/contract/test_me_framework_api_contract.py#L91) expect success for nonexistent `out-1` and objective type `recovery`. Active KEQ domains are hard-coded to five despite the contract's configurable input. Setting even an empty schedule can activate an otherwise incomplete framework. Community needs analysis, process/outcome evaluation stages, and closure have no controlling workflow in these services.

**Developer steps**: Own both M&E services, request models, and MEFramework. Resolve selected IDs against the reference catalogue, derive domain/objective metadata, validate standards' outcome membership, and return suggested indicators/activities. Store restatements without changing the source outcome; implement separately governed custom extensions. Allow valid active KEQ subsets to shape reports only. Define and enforce lifecycle readiness criteria, needs-analysis records, evaluation progression, and closure while allowing opt-in use by an existing spec 018 program.

**Tester positive**: Extend [M&E contract tests](../../tests/contract/test_me_framework_api_contract.py#L23) with existing social/economic/built catalogue IDs, a community restatement, and a custom extension fixture; verify returned suggestions and persistence.

**Tester negative**: Unknown IDs, domain/objective mismatches, invalid KEQs, standards for unselected outcomes, and premature activation must not persist partial invalid updates.

**Tester edge**: Empty/catalogue-only/custom-only configurations, repeated selection, inactive outcomes, unavailable catalogue, and adoption by an existing incident tracker must have explicit behavior.

**Future check**: Run `pytest tests/unit/test_me_framework.py tests/contract/test_me_framework_api_contract.py tests/integration/test_me_framework_cosmos.py` with reference data and injected stores. Expected: invalid fixtures rejected, valid metadata derived, and every lifecycle boundary asserted.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-005, AUD-019-014, AUD-019-015 and documented readiness/custom-extension rules. Accept when both routes enforce the same validated configuration, not permissive dictionary copying.

### AUD-019-017: Important - Detailed outcomes do not feed the legacy tracker or cohort views

- [ ] AUD-019-017 Link catalogue observations to recovery trackers and separate objective/cohort progress.

**Affected**: FR-009, FR-015, FR-016, FR-017, FR-018, FR-019, FR-022, FR-023, FR-024, FR-030, FR-031; SC-003; US3-AS1, US3-AS2, US3-AS3, US3-AS4, US3-AS5, US3-AS6; T008, T047, T050, T054; CHK027, CHK028, CHK037, CHK046, CHK063. **Status**: PARTIAL.

**Expected/actual/impact**: The full catalogue must extend the existing 21 indicators, roll overarching data into relevant concrete domains, and track sustainability/resilience and vulnerable populations separately. The optional [catalogue link field](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L90) exists. However, [RecoveryService](../../apps/api/app/services/recovery_service.py#L27) creates only the original fixed set and its [update method](../../apps/api/app/services/recovery_service.py#L83) rejects names outside that set. [The API input](../../apps/api/app/api/routes/recovery.py#L18) has no catalogue/cohort link, and neither M&E selection path creates tracker indicators. Objective/cohort labels in reference data do not create separate live progress tracking. The dashboard's synthetic overarching average is not the required indicator roll-up.

**Developer steps**: Add a durable observation-to-catalogue-to-outcome mapping and define explicit roll-up rules to the four-value RecoveryEnvironmentTracker without changing its type. Create/update detailed indicators from selected outcomes, retaining null links for legacy indicators. Support objective and authorised subgroup projections with community-specific restatements, qualitative evidence, and privacy-aware denominators. Link frameworks to existing trackers by incident/program context and prevent double counting across overarching and concrete domains.

**Tester positive**: Extend [recovery contract tests](../../tests/contract/test_recovery_contract.py#L25) and [M&E integration tests](../../tests/integration/test_me_framework_cosmos.py#L1) with a cyclone program spanning at least three concrete domains, both objective types, and an authorised vulnerable cohort.

**Tester negative**: Wrong-domain links, unknown template IDs, duplicate roll-up contributions, and unauthorised/small cohorts must not distort or expose progress.

**Tester edge**: Existing 21-indicator tracker with no catalogue links, an overarching indicator affecting two concrete domains, inactive outcomes, and the same indicator under different objectives.

**Future check**: Run `pytest tests/contract/test_recovery_contract.py tests/integration/test_me_framework_cosmos.py tests/unit/test_emergency_plan.py` with synthetic observation history. Expected: linked detailed and summary values, separate objective/cohort results, and unchanged legacy behavior.

**Dependencies/acceptance**: Requires AUD-019-004, AUD-019-005, AUD-019-014, AUD-019-016. Accept only when new observations change the appropriate live tracker and disaggregated views through a real caller.

### AUD-019-018: Important - Collection schedules do not collect data or drive staleness

- [ ] AUD-019-018 Implement manual/bulk observation capture, overdue computation, and missing-data reasons.

**Affected**: FR-012, FR-013, FR-021, FR-024, FR-030; SC-005; US2-AS3, US2-AS4; unavailable/delayed-data edge; T030, T046, T047, T050, T073; CHK009, CHK012, CHK019, CHK022, CHK034, CHK048, CHK049. **Status**: PARTIAL.

**Expected/actual/impact**: Quantitative/qualitative observations, CSV bulk input, baseline/current values, collection dates, reasons for missing data, and last-known/stale values must support non-blocking reporting. [Schedule setters](../../apps/agents/monitoring/me_framework_service.py#L92) store caller dictionaries; overdue reporting trusts `is_overdue`. [The unit test](../../tests/unit/test_me_framework.py#L168) sets that flag itself instead of proving date-based detection. The disconnected [unavailability helper](../../apps/agents/common/edge_cases.py#L25) has no reason field and treats a missing timestamp as not stale. Existing tracker endpoints take numeric values only; no scoped CSV or qualitative collection workflow was found.

**Developer steps**: Own collection records, M&E/recovery inputs, and reporting. Persist value/history, methodology, baseline, collection/due timestamps, collector, and unavailability reason; separate missing from zero. Derive overdue/staleness with an injected clock and the configured threshold, advance recurring due dates, and retain last-known values. Add bounded CSV import and qualitative capture with row-level errors, idempotency, and the same privacy rules. Continue reports when some or all observations are unavailable.

**Tester positive**: Extend [test_me_framework.py](../../tests/unit/test_me_framework.py#L130) and [M&E integration tests](../../tests/integration/test_me_framework_cosmos.py#L1) with on-time/late/manual/CSV/qualitative records and a fixed clock; verify due dates and last-known values.

**Tester negative**: Malformed CSV, invalid dates/units, unapproved cohort data, and unsupported methodology must not bypass validation or silently turn missing values into zero.

**Tester edge**: Exact staleness boundary, missing timestamp, no data in an entire domain, delayed census with a reason, duplicated imports, leap dates, and timezone offsets.

**Future check**: Run `pytest tests/unit/test_me_framework.py tests/contract/test_me_framework_api_contract.py tests/integration/test_me_framework_cosmos.py`; future CSV fixtures should live alongside these existing suites or in an explicitly proposed fixture subdirectory. Expected: date-derived status and non-blocking report assertions.

**Dependencies/acceptance**: Requires AUD-019-004, AUD-019-005, AUD-019-016, AUD-019-017. Accept when collection events, not manually supplied flags, determine timeliness and staleness.

### AUD-019-019: Important - Success standards are stored but not evaluated per stakeholder

- [ ] AUD-019-019 Evaluate every configured standard with explicit primary selection and measurement direction.

**Affected**: FR-012, FR-013, FR-023, FR-026; US2-AS4; conflicting-standards edge; T011, T030, T047, T050, T075; CHK021, CHK024, CHK040, CHK047. **Status**: PARTIAL.

**Expected/actual/impact**: Reports must compare observed values with each stakeholder's `gte`, `lte`, `eq`, or bounded range and allow designation of the primary standard. [SuccessStandard](../../packages/domain/src/domain/models/me_framework.py#L43) defines operators/labels, but [the service](../../apps/api/app/services/me_framework_service.py#L114) only stores dictionaries. The [conflict helper](../../apps/agents/common/edge_cases.py#L64) groups labels/thresholds without evaluating progress or choosing a primary. Analysis instead uses an unrelated fixed 80% target rule. Low contamination and low employment cannot both be treated as failure in the same direction.

**Developer steps**: Implement one typed standard evaluator, binding each standard to its selected outcome and indicator with units, direction, stakeholder identity, and one explicit primary. Reject reversed/missing ranges and inconsistent bindings. Report all standards separately and use the designated primary only where the evaluation calls for it; preserve different program baselines. Apply the same evaluator to lagging detection, intervention recommendations, and sustainability checks.

**Tester positive**: Extend [test_me_framework.py](../../tests/unit/test_me_framework.py#L72) with national/state/community thresholds for the same indicator, plus employment `gte`, contamination `lte`, exact, and range cases; assert each result and the selected primary.

**Tester negative**: Unknown outcome, invalid operator, conflicting primary flags, incompatible units, and reversed bounds must fail before persistence.

**Tester edge**: Exact equality, zero target, absent value, qualitative standard, changed primary, and shared observations with different program baselines.

**Future check**: Run `pytest tests/unit/test_me_framework.py tests/integration/test_me_framework_cosmos.py tests/unit/test_indicator_analysis.py` with deterministic measured values. Expected: per-stakeholder results and consistent direction-aware lagging classifications.

**Dependencies/acceptance**: Requires AUD-019-016, AUD-019-017, AUD-019-018 and agreed qualitative-standard semantics. Accept when reports evaluate, not merely echo, the standards.

### AUD-019-020: Important - Monitoring reports return configuration instead of recovery progress

- [ ] AUD-019-020 Generate monitoring reports from scoped observations and program logic.

**Affected**: FR-013, FR-022, FR-023, FR-024, FR-031; US2-AS4, US3-AS5, US3-AS6; NFR-003; T047, T050; unavailable-data edge. **Status**: PARTIAL.

**Expected/actual/impact**: Reports need baseline/current progress, trends, standards, intervention alerts, and program-logic context. [Agent reporting](../../apps/agents/monitoring/me_framework_service.py#L102) and [API reporting](../../apps/api/app/services/me_framework_service.py#L144) put the standards list in `indicators_status`, copy overdue flags, and always return empty staleness warnings. Neither reads observations, catalogue detail, or logic. Contract tests check keys, not any measured outcome.

**Developer steps**: Own both report services and the consumer projection. Join selected outcomes, collection history, standards, and the stored logic for the requested reporting period. Produce counts and domain/objective/cohort summaries with evidence, baseline changes, positive/negative/stagnant trends, missing-data reasons, and intervention flags. Respect inactive outcomes and privacy suppression; unavailable data must be explicit rather than reported as success or zero progress.

**Tester positive**: Extend [M&E contract lifecycle tests](../../tests/contract/test_me_framework_api_contract.py#L286) with multiple collection periods containing improving, declining, and flat indicators. Assert exact values, summaries, standard results, and alert membership.

**Tester negative**: Cross-incident observations, unselected outcomes, future observations, and suppressed data must not appear in the report.

**Tester edge**: All data unavailable, mixed collection frequencies, changed baseline, and incomplete program logic must yield honest partial reports with reasons.

**Future check**: Run `pytest tests/contract/test_me_framework_api_contract.py tests/integration/test_me_framework_cosmos.py` against controlled history fixtures. Expected: report values change when the scoped observations change; key-existence checks are insufficient.

**Dependencies/acceptance**: Requires AUD-019-017, AUD-019-018, AUD-019-019. Accept when reported progress is traceable to actual input records and logic, with performance measured separately.

### AUD-019-021: Important - Evaluation reports have headings but no KEQ evidence or dissemination

- [ ] AUD-019-021 Produce evidence-based evaluations and controlled stakeholder dissemination.

**Affected**: FR-008, FR-011, FR-014, FR-027, FR-028; SC-009; US2-AS5; T014, T032, T048, T049, T050, T051, T052; CHK006, CHK007, CHK021. **Status**: PARTIAL.

**Expected/actual/impact**: Each active KEQ domain needs source questions, findings supported by observations/evidence, recommendations, and stakeholder-appropriate dissemination. [API evaluation](../../apps/api/app/services/me_framework_service.py#L187) fills five domains with empty lists; [agent evaluation](../../apps/agents/monitoring/me_framework_service.py#L116) returns an empty domain map and retains only its ID. [EvaluationService](../../apps/agents/monitoring/evaluation_service.py#L22) is not called by those routes. [The integration assertion](../../tests/integration/test_me_framework_cosmos.py#L324) checks five keys, not findings. Dissemination exists as a model shape, not a reviewed delivery workflow.

**Developer steps**: Connect manual and AI-assisted evaluation to the period-filtered data, program logic, agreed standards, and seeded KEQs. Validate dates and evidence ownership; support authored manual findings, limitations/alternative explanations, and recommendations with catalogue links. Persist the full report and expose retrieval/review/dissemination records for government, community, NGO, and research audiences. Gate public release on safety, privacy, and real human review; do not assume five empty sections satisfy SC-009.

**Tester positive**: Extend [evaluation model tests](../../tests/unit/test_evaluation_report.py#L1) and the cited integration test with five nonempty KEQ findings, identifiable synthetic evidence records, and a reviewed audience-specific output.

**Tester negative**: Empty findings represented as completed evaluation, fabricated evidence, invalid period, unvalidated AI, and unauthorised dissemination must be prevented.

**Tester edge**: A valid configured subset of KEQ domains, partial evidence, manual mode during LLM outage, report amendments, and a withdrawn dissemination approval.

**Future check**: Run `pytest tests/unit/test_evaluation_report.py tests/contract/test_me_framework_api_contract.py tests/integration/test_me_framework_cosmos.py` with fake delivery and safety adapters. Expected: question/evidence references, period filtering, retrieval persistence, and approval assertions.

**Dependencies/acceptance**: Requires AUD-019-002, AUD-019-004, AUD-019-006, AUD-019-014, AUD-019-020. Accept when a reviewer can substantiate each finding; human review/delivery outcomes require separate evidence.

### AUD-019-022: Important - Program logic accepts disconnected data and ex-post creation is an echo

- [ ] AUD-019-022 Implement the AIDR logic template, validated chains, and persisted ex-post reconstruction.

**Affected**: FR-010, FR-023; SC-004; US2-AS2, US6-AS1, US6-AS2, US6-AS3; T012, T047, T050, T051, T067, T068; CHK055, CHK069. **Status**: PARTIAL.

**Expected/actual/impact**: Both approaches must connect resources, activities, outputs, intermediate outcomes, and final outcomes with catalogue links and timeline projections. The [typed model](../../packages/domain/src/domain/models/program_logic_model.py#L46) checks referenced IDs, but [API creation](../../apps/api/app/services/me_framework_service.py#L87) accepts arbitrary dictionaries and never calls its [own validator](../../apps/api/app/services/me_framework_service.py#L163). That validator only checks endpoint existence and at least one recognised objective, not connectedness, catalogue meaning, or timeline. The [ex-post endpoint](../../apps/api/app/api/routes/me_frameworks.py#L131) returns a canned ID merged with the request without lookup, reconstruction, or persistence.

**Developer steps**: Own ProgramLogicModel, M&E service/routes, and the eventual builder. Present the national template; validate unique node IDs, valid directed relationships, connected chains, catalogue linkage, and timelines. Distinguish sustainability/resilience without forcing every small program to include both when the source framework allows a relevant subset. For ex-post work, derive links from actual deployed resources/activities and document human-confirmed inferred outcomes. Store and retrieve the result under the verified framework; never allow body fields to overwrite framework/model ownership.

**Tester positive**: Extend [test_me_framework.py](../../tests/unit/test_me_framework.py#L1) and [M&E integration tests](../../tests/integration/test_me_framework_cosmos.py#L1) with a five-stage ex-ante graph and an ex-post fixture with recorded activities/resources and inferred outcomes.

**Tester negative**: Orphans, duplicate nodes, cycles, unknown catalogue IDs, invalid timelines, nonexistent framework, and ownership override must fail without saving.

**Tester edge**: Single-objective programs, several final outcomes, cross-domain links, incomplete evidence requiring confirmation, and repeated edits must preserve versioned graph meaning.

**Future check**: Run `pytest tests/unit/test_me_framework.py tests/contract/test_me_framework_api_contract.py tests/integration/test_me_framework_cosmos.py` after adding graph assertions. Expected: persisted, connected, provenance-bearing graphs on both approaches.

**Dependencies/acceptance**: Requires AUD-019-005, AUD-019-014, AUD-019-016. Accept when ex-post creation is not an echo and all runtime writes use the authoritative validation.

### AUD-019-023: Important - Cross-domain dependency links do not produce downstream delay alerts

- [ ] AUD-019-023 Evaluate program-logic dependencies and warn about upstream recovery delays.

**Affected**: FR-010, FR-013, FR-025; cross-domain cascading-recovery edge; T012, T047, T059, T068; US4-AS1. **Status**: PARTIAL.

**Expected/actual/impact**: Infrastructure delays must be linked to dependent economic/social outcomes and alert coordinators. [OutcomeChainLink](../../packages/domain/src/domain/models/program_logic_model.py#L38) has a `depends_on` value, but neither [logic creation](../../apps/api/app/services/me_framework_service.py#L87) nor [monitoring reports](../../apps/api/app/services/me_framework_service.py#L144) evaluates dependencies or produces those alerts. Generic simultaneous-lag correlation is not a dependency evaluation.

**Developer steps**: Own program-logic evaluation and monitoring alert production. Track authorised cross-domain prerequisites, expected timing, completion evidence, and downstream impact. Evaluate upstream delays against the recorded graph and produce actionable, deduplicated alerts identifying affected outcomes and evidence; clear/update them when the upstream condition recovers. Keep this deterministic dependency signal distinct from speculative AI correlations.

**Tester positive**: Add a transport-restoration-to-business-reopening chain to [planning/M&E simulation tests](../../tests/simulation/test_planning_me_scenarios.py#L1); delaying the upstream work must flag only dependent outcomes.

**Tester negative**: Unlinked simultaneous lags, reverse-direction links, and another program's activities must not create dependency alerts.

**Tester edge**: Fan-out, transitive dependencies, circular invalid graphs, missing upstream data, recovery of an upstream activity, and duplicate monitoring cycles.

**Future check**: Run `pytest tests/unit/test_me_framework.py tests/simulation/test_planning_me_scenarios.py` with a fixed timeline and deterministic graph. Expected: exact alert targets, evidence, deduplication, and clearance assertions.

**Dependencies/acceptance**: Requires AUD-019-018, AUD-019-020, AUD-019-022. Accept when a real report/event caller evaluates the links; storing `depends_on` alone does not close the edge case.

### AUD-019-024: Important - Overlap detection does not share indicator observations

- [ ] AUD-019-024 Reuse authorised observations across overlapping programs without merging their evaluations.

**Affected**: FR-008, FR-010, FR-013, FR-030, FR-031; overlapping-programs edge; T072; CHK040, CHK047. **Status**: PARTIAL.

**Expected/actual/impact**: Programs for the same community/outcome must avoid duplicate collection while retaining distinct logic/reports. [handle_overlapping_programs](../../apps/agents/common/edge_cases.py#L12) only intersects standard indicator IDs and returns advice; the scoped runtime search found no caller or shared-observation link in the M&E services. Independent program documents alone do not fulfill observation reuse.

**Developer steps**: Introduce authorised shared observation references keyed to community, indicator, cohort, and collection event. Link programs explicitly while preserving each program's baseline, standards, logic, and evaluation identity. Propagate corrected data without duplicating collection or silently equating two different populations; ensure both programs are authorised to use the shared data.

**Tester positive**: In [M&E integration tests](../../tests/integration/test_me_framework_cosmos.py#L1), create two frameworks for one community/outcome and collect once; assert both read the same observation while reports/logic remain distinct.

**Tester negative**: Different communities/cohorts, unauthorised cross-scope sharing, or mismatched indicator meaning must not share observations.

**Tester edge**: Different baselines/primary standards, revised observations, one closed program, repeated linking, and unlinking after collection.

**Future check**: Run `pytest tests/integration/test_me_framework_cosmos.py tests/simulation/test_planning_me_scenarios.py` with two-program fixtures. Expected: one collection identity, two separate evaluation results, and no cross-scope leakage.

**Dependencies/acceptance**: Requires AUD-019-004, AUD-019-005, AUD-019-017, AUD-019-019. Accept when actual observations are reused, not merely overlapping identifiers counted.

### AUD-019-025: Important - Post-closure regression is an unused fixed-ratio calculation

- [ ] AUD-019-025 Monitor closed programs for real regression and advise on reactivation.

**Affected**: FR-008, FR-012, FR-013, FR-023; post-closure-regression edge; T074; CHK024. **Status**: PARTIAL.

**Expected/actual/impact**: Subsequent deterioration must be assessed against community sustainability and generate a recommendation to consider reactivation. [handle_outcome_regression](../../apps/agents/common/edge_cases.py#L47) compares a value/target ratio to a fixed 0.9 without program status, history, objective, or configured standard; no caller was found in the scoped reporting paths. It cannot distinguish a genuine regression after closure from a low baseline or a lower-is-better measure.

**Developer steps**: Own closed-framework monitoring, observation history, and advisory generation. Compare post-closure observations with prior achievement and the agreed sustainability standard/direction; retain baseline/context and missing-data uncertainty. Generate an attributable recommendation for coordinator review, never automatically reactivate or redeploy assistance.

**Tester positive**: Extend [M&E integration tests](../../tests/integration/test_me_framework_cosmos.py#L1) with a closed program that met its employment standard, then regresses; assert compromise evidence and a reactivation recommendation.

**Tester negative**: Stable recovery, an active program, missing observations, or improved lower-is-better indicators must not produce a false post-closure regression.

**Tester edge**: Zero targets, conflicting stakeholder standards, a repeated collection event, privacy-suppressed cohorts, and a new secondary disaster.

**Future check**: Run `pytest tests/integration/test_me_framework_cosmos.py tests/unit/test_me_framework.py` with fixed pre/post-closure history. Expected: correct advisory decisions and no automatic framework reactivation.

**Dependencies/acceptance**: Requires AUD-019-018, AUD-019-019, AUD-019-020 and an approved definition of compromised sustainability. Accept only with scheduled/event-driven runtime use and evidence-bearing advisories.

### AUD-019-026: Important - Correlation analysis equates simultaneous lag with a relationship

- [ ] AUD-019-026 Analyse scoped multi-period evidence and expose uncertainty with a validated correlation benchmark.

**Affected**: FR-025; NFR-004; SC-006; US4-AS1; T059, T060, T061, T062; CHK010, CHK011, CHK017, CHK036, CHK050. **Status**: PARTIAL.

**Expected/actual/impact**: The analysis contract requires at least two periods, lookback/domain selection, supporting evidence, and insufficient-data status; SC-006 requires at least 80% of planted known relationships identified. [Agent analysis](../../apps/agents/monitoring/indicator_analysis.py#L22) and [API fallback](../../apps/api/app/services/ai_analysis_service.py#L26) pair every lagging domain, using caller-provided trends or a fixed 80%-of-target rule. [The tests](../../tests/unit/test_indicator_analysis.py#L78) intentionally infer a correlation from two single snapshots, and [the three-domain test](../../tests/unit/test_indicator_analysis.py#L97) expects all three pairs. No independent relationship benchmark or period-based evidence is established by those assertions.

**Developer steps**: Own the analysis service and incident-scoped endpoint. Retrieve authorised observation histories and standards, honor lookback/domain options, distinguish co-occurrence from supported correlation and causal dependencies, and report sample counts, lag, strength, and limitations. Use the configured end-to-end deadline for up to 50 active indicators. Define the planted-case truth set and scoring rule independently with an M&E reviewer; do not tune the expected results to the implementation's all-pairs heuristic.

**Tester positive**: Extend [test_indicator_analysis.py](../../tests/unit/test_indicator_analysis.py#L55) with multi-period fixtures containing known positive/negative/lagged relationships and expected evidence references.

**Tester negative**: Unrelated simultaneous lags, one period, insufficient variation, wrong incident, and missing data must not produce a strong supported correlation.

**Tester edge**: Two-period minimum, zero/negative targets, mixed frequencies, missing observations, 50 indicators, timeout, and conflicting interpretations. Assert explicit insufficient-data/uncertainty instead of a silent empty success.

**Future check**: Run `pytest tests/unit/test_indicator_analysis.py tests/simulation/test_planning_me_scenarios.py` with a separately reviewed truth manifest. Expected: at least 80% recall on planted correlations plus documented false-positive/insufficient-data results; no such benchmark was run here.

**Dependencies/acceptance**: Requires AUD-019-002, AUD-019-004, AUD-019-018, AUD-019-019. Accept only with evidence-based behavior and recorded benchmark results, not assertions that repeat the heuristic.

### AUD-019-027: Important - AI recommendations and audience summaries are not wired to live services

- [ ] AUD-019-027 Connect safe catalogue recommendations and audience-specific recovery summaries.

**Affected**: FR-026, FR-027, FR-028; SC-007; US4-AS2, US4-AS3, US4-AS4; T054, T059, T060, T061, T062; CHK011, CHK018, CHK026, CHK041. **Status**: PARTIAL.

**Expected/actual/impact**: Lagging outcomes should receive catalogue-matched activities with safe rationale, and reports should serve community, government, and inter-agency audiences. The [monitoring factory](../../apps/agents/monitoring/agent.py#L530) supplies only a catalogue to the analysis service, not an LLM or safety validator. The [API service](../../apps/api/app/services/ai_analysis_service.py#L85) returns no recommendations without a client, and routes instantiate it without one. [Community summaries](../../apps/agents/monitoring/indicator_analysis.py#L110) are fixed counts of positive flags with no target-audience selection or actual progress narrative. The existing [LLMClient interface](../../apps/agents/common/llm_client.py#L144) is compatible with the helper call; this is a wiring/behavior gap, not an alleged SDK signature mismatch.

**Developer steps**: Inject the supported LLM/safety/catalogue adapters and use authorised program observations plus the standard evaluator to identify genuinely lagging outcomes. Generate grounded rationales referencing allowed activities and their limitations. Produce truthful audience-specific summaries covering all selected active domains. Label deterministic degradation explicitly; on LLM outage, retain matched catalogue activities and structured data without pretending AI ran. Keep existing model-gateway minimisation and human review boundaries.

**Tester positive**: Extend [analysis unit tests](../../tests/unit/test_indicator_analysis.py#L1) and [analysis route tests](../../tests/contract/test_recovery_catalogue_contract.py#L57) with known lagging outcomes and distinct community/government/inter-agency requests; capture actual prompts and safe outputs.

**Tester negative**: Non-lagging outcomes, untraceable activity IDs, unsupported claims, privacy-sensitive content, and a failed validator must not be presented as grounded recommendations.

**Tester edge**: LLM unavailable, no catalogue activity, one active domain, all observations unavailable, contradictory domain advice, and manual summaries. Verify real factory injection and honest fallback provenance.

**Future check**: Run `pytest tests/unit/test_indicator_analysis.py tests/contract/test_recovery_catalogue_contract.py` using deterministic LLM/safety doubles; separately conduct the approved non-specialist reader study for the 85% target. Expected: actual adapter calls and audience/content assertions.

**Dependencies/acceptance**: Requires AUD-019-002, AUD-019-004, AUD-019-014, AUD-019-015, AUD-019-019, AUD-019-026. Accept when default configured entry points deliver the required safe behavior; a dispatcher Q&A response is not this feature.

### AUD-019-028: Important - Stakeholder continuity is represented by a count, not linked participation

- [ ] AUD-019-028 Preserve planning consultation and community-led recovery evidence across the handover.

**Affected**: FR-019, FR-022, FR-024, FR-032; US1-AS1, US3-AS4, US3-AS6; T010, T026, T070; CHK004, CHK005, CHK023; Constitution VI-C/VII-A. **Status**: PARTIAL.

**Expected/actual/impact**: Planning engagement must inform recovery community definition, needs, and priorities. [PlanningProcessRecord](../../packages/domain/src/domain/models/planning_process_record.py#L85) has an engagement log, but the controllers do not capture it. [link_stakeholder_engagement](../../apps/agents/common/plan_activation.py#L59) returns only a count, community string, and `linked` label; it has no inspected caller and preserves no consultation provenance. The [natural-domain seed](../../packages/domain/src/domain/seed/recovery-catalogue/natural.json#L1) mentions Traditional Owner participation, which is authored guidance, not proof of consultation or cultural authority approval.

**Developer steps**: Own planning process capture, handover, and M&E community/outcome configuration. Persist scoped consultation records, community-stated priorities, relevant participants/representatives, and references into recovery configuration and evaluations. Retain vulnerable-group restatements and culturally appropriate heritage input, with consent and privacy handling; never turn a stakeholder count into an approval. This spec does not mandate a named cultural-authority registry or authorise a new automated cultural approval regime. Preserve its actual community-led and human-authority constraints instead.

**Tester positive**: Extend [planning-process tests](../../tests/unit/test_planning_process_record.py#L1) and [cross-agent simulation](../../tests/simulation/test_planning_me_scenarios.py#L1) with a consultation record, community priority, vulnerable cohort, and heritage representative; assert linked references survive the handover.

**Tester negative**: No engagement record, absent consent, wrong community, or unauthorised claimed approval must not become `linked`/approved recovery evidence.

**Tester edge**: Evolving priorities, changed representatives, withdrawal/correction, qualitative cultural information, and participation by displaced community members outside the impact region.

**Future check**: Run `pytest tests/unit/test_planning_process_record.py tests/simulation/test_planning_me_scenarios.py` with synthetic representative/consent fixtures. Human/cultural validation remains a separate, explicitly evidenced activity.

**Dependencies/acceptance**: Requires AUD-019-001, AUD-019-004, AUD-019-006, AUD-019-008, AUD-019-016. Accept when traceable participation informs recovery decisions rather than merely being counted.

### AUD-019-029: Important - Evaluation findings do not enter the lessons system

- [ ] AUD-019-029 Deliver attributable evaluation and post-event lessons through the supported lessons workflow.

**Affected**: FR-033; FR-029, FR-032; US5-AS4; T025, T065, T071, T077; inherited 018 lessons/contradictory-lesson constraints. **Status**: PARTIAL.

**Expected/actual/impact**: Evaluation findings and post-event lessons must close the continuous-improvement loop. [The evaluation handoff builder](../../apps/agents/common/handoffs.py#L214) exists, but neither evaluation generator calls it; its `lessons_management` target differs from other legacy builders' `lessons_service` target. [LessonsService.capture](../../apps/api/app/services/lessons_service.py#L19) is a real available surface, yet no inspected 019 controller delivers findings there. The simulation does not assert a lesson at all. Existing lessons capability is therefore credited, while the 019 integration remains open.

**Developer steps**: Connect reviewed evaluation recommendations and post-event observations to the supported lessons service/orchestrator. Preserve incident, framework/report, plan version, originating event, AIIMS function, PPRR phase, severity, owner, and resolution links. Resolve target naming with the orchestration owner. Deduplicate retries and preserve buffering/degradation semantics. Respect the inherited requirement to escalate contradictory lessons for human approval, not auto-apply them to plans or agent configuration.

**Tester positive**: Extend [planning/M&E simulation](../../tests/simulation/test_planning_me_scenarios.py#L1) to generate a supported evaluation finding and assert a persisted, attributable lesson in the actual lessons register.

**Tester negative**: Empty/fabricated/unsafe findings, wrong incident references, and contradictory configuration changes without approval must not become applied lessons.

**Tester edge**: Duplicate delivery, unavailable lessons store, later report correction, several recommendations from one evaluation, and retry after restart.

**Future check**: Run `pytest tests/simulation/test_planning_me_scenarios.py tests/integration/test_me_framework_cosmos.py` with injected transport and lessons storage. Expected: lesson identity/provenance, deduplication, buffering, and approval-boundary assertions.

**Dependencies/acceptance**: Requires AUD-019-003, AUD-019-006, AUD-019-013, AUD-019-021. Accept when the lessons register changes through a real runtime path, not when a builder returns a payload.

### AUD-019-030: Important - Required rates are local snapshots or unused event counters

- [ ] AUD-019-030 Emit the specified telemetry with correct units, denominators, and runtime callers.

**Affected**: NFR-007; SC-005; T036, T069; R-013; all four contracts' observability sections. **Status**: PARTIAL.

**Expected/actual/impact**: The five required metrics must be emitted: activation count, framework completion rate, on-time indicator collection rate, outcome achievement rate, and plan currency compliance ratio. [Planning telemetry](../../apps/agents/planning/telemetry.py#L10) is a dictionary plus logs; only activation/section updates have inspected callers. [Monitoring telemetry](../../apps/agents/monitoring/telemetry.py#L107) keeps rate snapshots and adds an event to differently named counters with the rate as a string attribute. The update helpers have no callers in the inspected M&E paths. This cannot establish the required operational ratios.

**Developer steps**: Own planning/monitoring telemetry and the decision/collection/report callers. Emit the exact required counter/gauge names and compute rates from auditable events with defined denominators/windows. Add the contract's analysis latency, recommendation/safety counts, and catalogue query/suggestion latency instruments. Preserve privacy-safe dimensions, distinguish zero from no observations, and avoid double counting retries or treating a count as a rate.

**Tester positive**: Add a captured meter/exporter fixture to [planning contract tests](../../tests/contract/test_planning_api_contract.py#L1) and [M&E integration tests](../../tests/integration/test_me_framework_cosmos.py#L1); drive real mutations/collections and assert metric name, type, value, unit, and dimensions.

**Tester negative**: Rejected activation, unsafe output, empty denominator, and duplicate delivery must not inflate success rates.

**Tester edge**: Rate-window rollover, late collections, reopened frameworks, process restart, and exporter outage must preserve or explicitly degrade the measurement.

**Future check**: Run `pytest tests/contract/test_planning_api_contract.py tests/integration/test_me_framework_cosmos.py tests/unit/test_indicator_analysis.py` after adding telemetry assertions. Use an in-process test exporter, not a cloud query. Expected: the specified instruments emitted by actual callers.

**Dependencies/acceptance**: Requires working lifecycle, collection, standard evaluation, and reporting. Accept when telemetry reflects events and can be reconciled to their source records.

### AUD-019-031: Important - Performance, capacity, and human outcomes lack qualifying evidence

- [ ] AUD-019-031 Define representative workloads and measure every performance/capacity/user-outcome target.

**Affected**: NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006; SC-002, SC-003, SC-005, SC-006, SC-007, SC-008; T039, T043, T046, T052, T062, T077, T078; CHK015, CHK016, CHK017, CHK018, CHK034, CHK035, CHK036, CHK037, CHK039, CHK059. **Status**: UNVERIFIED.

**Expected/actual/impact**: Required outcomes are 15-second full-plan assembly, under-30-minute M&E configuration, 10-second expanded dashboard, 30-second analysis for 50 indicators, at least 20 concurrent plans and 10 frameworks, five-working-day planning, 90% on-time collection, 80% planted-correlation recall, 85% reader clarity, and 10-second operational activation. [Config defaults](../../apps/agents/planning/config.py#L14), [M&E defaults](../../apps/agents/monitoring/config.py#L76), and [smoke assertions](../../tests/simulation/test_planning_me_scenarios.py#L30) do not measure these. No qualifying scoped run logs or reader-study evidence were present in the reviewed inputs.

**Developer steps**: Define standard program/region sizes, active-indicator mixes, concurrent workload, timing boundaries, and measurement windows with the owner. Make timeouts govern the entire operation and instrument it. Build deterministic workload fixtures plus representative dependency latency; distinguish service timing from user session time and external consultation/endorsement delays. The capacity figures are minimum support targets, not proof supplied by maximum-count configuration variables.

**Tester positive**: Extend [planning/M&E simulation](../../tests/simulation/test_planning_me_scenarios.py#L1) with named `spec019_capacity` and timing cases covering 20 plans, 10 frameworks, 50 indicators, 27-section documents, and full operational content.

**Tester negative**: Slow/unavailable dependencies, rejected operations, missing data, and reduced-content responses must not be counted as compliant successful runs.

**Tester edge**: Concurrent edits/activations, cold start, 50-indicator boundary, large narrative sections, and low-sample reader results. Separately recruit an approved non-specialist reader cohort and record the measurement instrument, sample size, ratings, and limitations.

**Future check**: After the named cases exist, run `pytest tests/simulation/test_planning_me_scenarios.py -k spec019_capacity` and the separately reviewed timing/accuracy suite. Require nonzero collected cases and recorded raw results. Browser/user-study prerequisites include working UI, synthetic/approved data, consent, and defined scenarios; no measurements are claimed here.

**Dependencies/acceptance**: Depends on functional remediation and agreed CHK definitions. Accept only with reproducible, revision-bound measurements and human-study evidence; authored benchmark plans or checked tasks are not observed outcomes.

### AUD-019-032: Important - The production packages do not deliver the real Planning Agent

- [ ] AUD-019-032 Package and register the actual emergency-planning service and its shared lifecycle dependency.

**Affected**: FR-001, FR-006, FR-007, FR-029; T001, T003, T004, T005, T006, T040, T042, T064; R-001, R-010, R-012; CHK013, CHK065. **Status**: PARTIAL.

**Expected/actual/impact**: The standalone planning factory must be an available runtime capability, not only a source directory. [Agent wheel packages](../../apps/agents/pyproject.toml#L60) omit `planning`; [the agent Dockerfile](../../apps/agents/Dockerfile#L4) omits its directory and runs the dispatcher. [Dispatcher planning](../../apps/agents/dispatcher/agent.py#L63) is a generic simulation prompt, not the plan lifecycle API. [The API image](../../apps/api/Dockerfile#L19) also does not copy planning, while [its transition method](../../apps/api/app/services/emergency_plan_service.py#L125) imports `planning.plan_lifecycle` on demand. Repository test path injection can hide this packaging gap. No packaged import or build was executed, so an observed deployment failure is not claimed.

**Developer steps**: Own package manifests, service entry points, API shared-domain imports, deployment registration, and health. Make the supported planning implementation available in built artifacts and reachable through the intended API/service boundary; remove reliance on source-tree-only import paths. Keep the simulation Q&A role separate. Wire dependency-aware readiness and the supported orchestration route. Retain the authored [three-container module](../../infra/modules/emergency-planning.bicep#L19) and [main module reference](../../infra/main.bicep#L810); validate their deployment later, not by assuming a source file proves it.

**Tester positive**: Add an installed-artifact fixture to [plan integration tests](../../tests/integration/test_emergency_plans_cosmos.py#L1) and assert the real planning factory/lifecycle and API transition resolve without the repository's [test path injection](../../tests/conftest.py#L10).

**Tester negative**: Missing planning artifact, missing dependency configuration, or unreachable service must not report healthy/available planning.

**Tester edge**: API-only and agents-only deployments, nondefault port, dependency outage, and restart must preserve the advertised route/health contract.

**Future check**: After adding `packaged` cases and preparing an approved local artifact, run `pytest tests/integration/test_emergency_plans_cosmos.py -k packaged`. Before any later deployment, require the existing infrastructure review and approved validation workflow. Expected: installed-package route availability, not source-tree-only import success.

**Dependencies/acceptance**: Requires AUD-019-003, AUD-019-005, AUD-019-013 and an explicit service registration decision. Accept when the built product contains and serves the actual 019 capability.

### AUD-019-033: Important - Existing dashboard screens do not provide the required live workflows

- [ ] AUD-019-033 Connect real plan/M&E data and deliver the missing guided user workflows.

**Affected**: FR-001, FR-005, FR-010, FR-013, FR-020, FR-021, FR-022, FR-023, FR-024, FR-031; NFR-002, NFR-003; SC-002, SC-003, SC-004; US1, US2, US3, US6; T040, T042, T051, T056, T067, T077; CHK020, CHK055, CHK057. **Status**: PARTIAL.

**Expected/actual/impact**: Planners/coordinators need guided plan development, M&E setup, catalogue selection/collection, and a visual logic builder. Existing [readiness](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L16) and [recovery](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L50) pages are real read-only views. Their [API client](../../apps/web/src/lib/api/governance.ts#L275) calls governance aggregation, whose [plan summaries](../../apps/api/app/services/governance_data_service.py#L366) use framework metadata and whose [recovery data](../../apps/api/app/services/governance_data_service.py#L491) hard-code zero progress. The [overarching average](../../apps/api/app/services/dashboard_aggregation_service.py#L496) is not catalogue-indicator roll-up. The source search found no client for the 019 plan/M&E/catalogue/program-logic endpoints, and no builder replacement. Thus screens exist, but the required user journeys are not established.

**Developer steps**: Reuse existing governance navigation/accessibility components, connecting scoped live plan and M&E services with honest loading, unavailable, partial, stale, and privacy-suppressed states. Provide guided planning/consultation, hierarchy/conflict views, M&E outcome/standard/schedule/observation controls, and a persisted ex-ante/ex-post graph view/editor. Distinguish guidance/reference data from measured recovery progress and human approvals; respect existing read-only consumers and role restrictions.

**Tester positive**: Extend [governance-dashboard E2E tests](../../tests/e2e/governance-dashboard.spec.ts#L89) with `AIDR 019` cases using real local test endpoints and a seeded flood plan/recovery program. Create/edit/reload, select outcomes, enter observations, and verify live values and graph links.

**Tester negative**: Wrong role/scope, unavailable endpoints, suppressed cohorts, and read-only users must not mutate records or see fabricated zero/completed states.

**Tester edge**: Keyboard operation, small viewport, back-navigation, concurrent edits, empty domains, and a last-endorsed plan during a draft revision. Do not make required controls optional in the assertions.

**Future check**: After adding the cases, run `pnpm --filter @ama/web test:e2e --project=chromium governance-dashboard.spec.ts --grep "AIDR 019"` and repeat with `--project=mobile`. Prerequisites: installed web/test dependencies and browsers, an approved isolated API, and awareness that [playwright.config.cts](../../apps/web/playwright.config.cts#L18) starts servers and writes test artifacts. Neither command is run here.

**Dependencies/acceptance**: Requires the remediated planning, catalogue, M&E, privacy, and graph services. Accept when a user completes the required flows and the views show their persisted data, not only static headings or baseline summaries.

### AUD-019-034: Important - Contract, integration, and simulation assertions miss the promised behavior

- [ ] AUD-019-034 Make the authored contracts executable and validate the actual exposed paths.

**Affected**: All four contracts, all 27 acceptance scenarios, all seven edges; T028, T030, T031, T033, T034, T035, T043, T044, T045, T052, T053, T057, T058, T062, T077, T078. **Status**: PARTIAL.

**Expected/actual/impact**: The original tasks require contract tests for complete payloads/side effects, actual persistence coverage, and an integrated planning-to-lessons simulation. [Planning tests](../../tests/contract/test_planning_api_contract.py#L27) accept summaries and omit activation assertions; [catalogue tests](../../tests/contract/test_recovery_catalogue_contract.py#L14) use the other agent instead of the registered API; [M&E tests](../../tests/contract/test_me_framework_api_contract.py#L91) accept invalid catalogue values. All three Cosmos suites state they use memory. [The simulation](../../tests/simulation/test_planning_me_scenarios.py#L30) completes one process step and one transition, then runs unrelated tests, not the required integrated chain. Prose `.yaml` contracts are not machine-validated schemas. These observations do not establish whether any test run passed.

**Developer steps**: Agree any compatibility aliases or approved contract changes; otherwise expose the specified paths, fields, pagination, errors, full-detail content, and side effects. Validate real router/factory construction, not manually repaired private state. Translate prose contracts into an enforceable test matrix or schema and map every assertion to a scenario/edge. Restore the complete nine-step/endorse/activate/PPRR/M&E/collect/analyse/evaluate/lessons journey. Keep unit doubles, emulator integration, installed-artifact, and human evidence separate.

**Tester positive**: Use the existing three contract suites, three Cosmos suites, foundational unit suites, and [simulation suite](../../tests/simulation/test_planning_me_scenarios.py#L1) as the test homes; assert values, identity, side effects, and persistence through the correct exposed paths.

**Tester negative**: Send the exact contract examples and malformed/wrong-role/wrong-scope variants; assert agreed 400/403/409/422/503 behavior, no mutation on failure, and honest fallback.

**Tester edge**: Cover every edge fixture listed in this report, real Cosmos query/partition branches, source-tree versus installed imports, and zero collected tests. Avoid weak assertions such as merely having five keys or a nonnegative element count.

**Future check**: Run `pytest tests/contract/test_planning_api_contract.py tests/contract/test_me_framework_api_contract.py tests/contract/test_recovery_catalogue_contract.py tests/simulation/test_planning_me_scenarios.py`, then the explicitly configured integration tier. Prerequisites: Python 3.12+ per current package metadata, installed dependencies, safe fixture configuration, and no unintended cloud endpoints. Record commands, revision, collected count, results, and limitations separately.

**Dependencies/acceptance**: Depends on the functional fixes; test assertions must challenge them, not redefine the requirements to fit stubs. T078 and test-first historical execution remain UNVERIFIED until qualifying evidence is supplied.

### AUD-019-035: Important - Checklist closure and amendment claims lack spec-specific evidence

- [ ] AUD-019-035 Resolve documentary conflicts and obtain bounded, attributable review/outcome evidence.

**Affected**: FR-034; NFR-008; SC-010; PER-049, PER-050, PER-051, HYP-017, SCP-055, SCP-056, SCP-057; all local quality/deep-review items and plan gates; T005, T006, T078. **Status**: PARTIAL.

**Expected/actual/impact**: Every checklist question must be assessed, with approval/measurement claims supported separately. [Deep review](checklists/deep-review.md#L16) has 70 unchecked questions; [requirements checklist](checklists/requirements.md#L9) claims all items pass, including no implementation details, despite explicit implementation choices in the spec. Its note says planning extends an agent, whereas the clarified spec requires a new one. [The constitution](../../.specify/memory/constitution.md#L300) has all three handbook entries, but no reviewed approval timestamp establishes SC-010's seven-day window. The named HYP-HYP-017 stub has no exact or renamed `HYP*017*.md` match under specs. The [portfolio rubric](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) is not a spec-019 result or proof that actors consulted on every change. Persona `validated` labels do not themselves supply the contract's named practitioner evidence. AU storage is declared in [main.bicep](../../infra/main.bicep#L580), not observed in deployment.

**Developer steps**: With the spec owner, resolve each open checklist decision using the tables below; obtain explicit acceptance criteria where absent and preserve approved deferrals instead of silently expanding scope. Reconcile stale paths, API shapes, state matrices, catalogue provenance, and the current Python/service architecture. Locate or author, only in a later authorised change, a contract-conforming HYP-017 evidence record (proposed location: `specs/019-aidr-additional-guidances/evidence/HYP-017.md`), retain a not-tested state until measured, and record spec-specific rubric/consultation provenance. Obtain actual constitution/SME approvals and infrastructure/region review evidence without backdating or checking historical tasks retroactively.

**Tester/reviewer positive**: Verify named reviewers, dates, decision scope, source revision, artifact integrity, per-spec hypothesis scores, and the documented constitutional handbook amendment/approval interval. Confirm declared storage/backup/telemetry residency stays AU and any model-hosting carve-out does not extend to persisted regulated data.

**Tester/reviewer negative**: A checked box, template, empty evidence stub, portfolio score, simulated invocation, or `passed` string must not be accepted as a run, approval, or observed outcome.

**Tester/reviewer edge**: Missing approval date, withdrawn endorsement, conflicting architecture decisions, superseded handbook paths, and deferred PH/JP/BD prerequisites must remain explicitly unresolved/deferred, not inferred approved.

**Future check**: Perform text-only contract/identifier/link checks on the later evidence record and compare its five criterion scores to the frozen baseline; require an independent reviewer to verify claims. A future `bicep build infra/modules/emergency-planning.bicep --stdout` requires the approved Bicep tooling and is only a compile check, not deployment/residency proof. Any what-if, deployment, or cloud validation requires separate authorisation. No original artifact, approval, or evidence is changed by this audit.

**Dependencies/acceptance**: Requires attributable owner decisions and the functional/measurement work identified above. Close only individual claims with matching evidence; do not treat a generic checklist or this report as product approval.

## Runtime Trace and Scoped Negative Searches

The findings follow these concrete paths, rather than treating matching files or checked boxes as implementation:

1. [API main](../../apps/api/app/main.py#L25) -> [registered routers](../../apps/api/app/api/router.py#L86) -> emergency-plan, M&E, catalogue, and analysis services. The actual prefixes are `/api/emergency-plans`, `/api/me-frameworks`, `/api/recovery-catalogue`, and `/api/analysis`; two differ from the documented planning/incident-scoped M&E contract, and analysis loses its incident path context. No inspected compatibility alias repairs those contracts.
2. [Standalone planning entry](../../apps/agents/planning/__main__.py#L12) -> [factory/controller](../../apps/agents/planning/agent.py#L235) -> agent-local dictionary and agent transition table. This is distinct from the API repository path and from the different domain transition table imported by the unit tests.
3. [Monitoring factory](../../apps/agents/monitoring/agent.py#L225) -> local M&E service, file-backed catalogue, and analysis service with no LLM/safety dependencies injected. The separately authored EvaluationService and several edge handlers are not on this route path.
4. [Existing tracker controller](../../apps/api/app/api/routes/recovery.py#L44) -> [RecoveryService](../../apps/api/app/services/recovery_service.py#L27) -> 21 fixed tracker indicators. The optional catalogue field exists, but the exposed update path does not accept it or create detailed observations/cohorts.
5. [Recovery page](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L61) -> [governance client](../../apps/web/src/lib/api/governance.ts#L419) -> [dashboard router](../../apps/api/app/api/routes/governance_dashboard.py#L794) -> [aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L462) -> [seed-derived data service](../../apps/api/app/services/governance_data_service.py#L491). Existing visible domain widgets are credited; they are not a substitute for live M&E records.
6. [Deployment services](../../azure.yaml#L29) -> [agents image](../../apps/agents/Dockerfile#L48) -> [dispatcher](../../apps/agents/dispatcher/agent.py#L189). Its planning role is simulation Q&A. Separately, the [documented MAF replacement](../../apps/agents/maf_runtime/workflow/builder.py#L80) runs the five response executors, not the 019 planning/M&E workflow.

| Search | Completed scope and terms | Result and limitation |
| --- | --- | --- |
| NEG-01 | Named handbook paths; filename search for handbooks; title search under documentation Markdown. | All three found under `docs/corpus/aidr/`; full relocated texts read. No missing-handbook finding. Historical paths need documentary correction only. |
| NEG-02 | Inventory of `apps/agents/planning/*.py`, then full renamed risk helper. | `plan_risk_assessment.py` is the current counterpart. It is a fixed-risk helper, not missing source. |
| NEG-03 | Python files immediately in planning, monitoring, common, API services, and API routes; activation/fallback, engagement, edge-case, endorsement, risk, M&E/lessons-builder and graph-validation symbols. | Completed PowerShell search found definitions but no runtime caller for the identified helpers in those controlling directories. Full services/controllers confirm the omissions. This is not a claim about every possible alias in the repository. |
| NEG-04 | Full legacy handoff module; full MAF workflow builder; recursive MAF Python search for planning, emergency-plan, activation, M&E, evaluation-lessons, and recovery-arrangement terms; full dispatcher. | Legacy transport has an explicit replacement notice. No equivalent 019 behavior found in the replacement; dispatcher planning is a different simulation capability. Do not mark the behavior retired. |
| NEG-05 | Recursive web-source TypeScript/TSX search for emergency plans, M&E, recovery catalogue, program logic, and their identifier variants; full readiness/recovery pages and their API/aggregation callers. | Read-only governance views found; no client for the 019 authoring/configuration routes or program-logic builder found in this scope. A catalogue navigation link does not prove a working catalogue workflow. |
| NEG-06 | All target feature documents/checklists/contracts; linked feature-028 evidence directory; filename search `specs/**/HYP*017*.md`. | No HYP-017 evidence file or renamed match. Portfolio baseline/post-feature documents are present and were read, but do not establish the individual hypothesis. No other implementation-review report was read. |
| NEG-07 | Full planning pipeline/agent/API service/routes/models plus catalogue/M&E/recovery services and exposed request shapes. | No connected full-plan/PDF assembly, qualitative/CSV observation capture, current-step/consultation workflow, or observation-sharing path found; nearby raw JSON/typed fields/helpers are credited as partial support. |
| NEG-08 | Feature-local review inputs and the directly linked supporting evidence records. | No qualifying 019 performance run, reader study, signed human approval, or deployed-residency result identified. Such external outcomes are UNVERIFIED, not asserted absent everywhere. |

Two broad workspace reference searches timed out and are not negative evidence. `rg` was unavailable; completed bounded PowerShell text searches were used instead. All searches were read-only. No source test, seed-loader function, application import, browser, deployment, or cloud query was executed.

## Original Task Coverage

Each row preserves the exact original checkbox state from [tasks.md](tasks.md). IMPLEMENTED here credits the full scoped source artifact/behavior stated in that row, not test execution or a successful deployment. Follow-ups on implemented artifacts identify integration/evidence work rather than retroactively changing their original state.

| Task | Original state | Review status | Concrete source/test evidence | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | Planning package/entry and [agent class](../../apps/agents/planning/agent.py#L42) exist; installed delivery is separate. | AUD-019-032 |
| T002 | [X] | IMPLEMENTED | [Frozen PlanningConfig](../../apps/agents/planning/config.py#L14) reads the named timeout, reminder, and version variables with validation. | AUD-019-010, AUD-019-031 |
| T003 | [X] | IMPLEMENTED | [Standalone entry](../../apps/agents/planning/__main__.py#L5) creates the app and defaults to port 8085. | AUD-019-032 |
| T004 | [X] | IMPLEMENTED | [Factory and health](../../apps/agents/planning/agent.py#L235) fulfill the skeleton task; unconditional healthy is not dependency readiness. | AUD-019-005, AUD-019-032 |
| T005 | [X] | IMPLEMENTED | [Bicep module](../../infra/modules/emergency-planning.bicep#L19) declares all three named containers, partitions, composites, and 1000 max autoscale settings. No compile/deployment claim. | AUD-019-015, AUD-019-035 |
| T006 | [X] | IMPLEMENTED | [Main reference](../../infra/main.bicep#L810) passes the account/database names. | AUD-019-035 |
| T007 | [X] | IMPLEMENTED | Populated seed home is demonstrated by [overarching seed](../../packages/domain/src/domain/seed/recovery-catalogue/overarching.json#L1) and the other five read seed files; an empty-directory placeholder is no longer needed. | - |
| T008 | [X] | IMPLEMENTED | [RecoveryIndicator](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L90) adds the optional field and regex; [extension tests](../../tests/unit/test_emergency_plan.py#L143) assert valid/null/invalid formats. | AUD-019-004, AUD-019-017 |
| T009 | [X] | IMPLEMENTED | [EmergencyPlan](../../packages/domain/src/domain/models/emergency_plan.py#L100) contains lifecycle/types, 27 slugs, eight keys, nested history, and endorsement validators. Runtime raw dictionaries bypass it. | AUD-019-003, AUD-019-007 |
| T010 | [X] | IMPLEMENTED | [PlanningProcessRecord](../../packages/domain/src/domain/models/planning_process_record.py#L85) and nested step/team/engagement/approval models are authored. | AUD-019-008, AUD-019-028 |
| T011 | [X] | PARTIAL | [MEFramework](../../packages/domain/src/domain/models/me_framework.py#L71) has the types/fields; it does not validate standard membership in selected outcomes. | AUD-019-016, AUD-019-019 |
| T012 | [X] | IMPLEMENTED | [ProgramLogicModel](../../packages/domain/src/domain/models/program_logic_model.py#L46) has both modes, nested elements/links, and unknown-link validation. Full connectedness is a later task. | AUD-019-022, AUD-019-023 |
| T013 | [X] | PARTIAL | [Catalogue models](../../packages/domain/src/domain/models/recovery_outcome.py#L22) validate individual ID syntax but not domain/parent-child consistency. | AUD-019-014, AUD-019-016 |
| T014 | [X] | IMPLEMENTED | [EvaluationReport](../../packages/domain/src/domain/models/evaluation_report.py#L60) contains nested findings/dissemination and period/domain/safety-result-presence checks. This is not proof safety ran. | AUD-019-002, AUD-019-021 |
| T015 | [X] | PARTIAL | [Overarching seed](../../packages/domain/src/domain/seed/recovery-catalogue/overarching.json#L5): seven authored outcomes, but source outcomes and undeveloped entries are substituted/omitted. | AUD-019-014 |
| T016 | [X] | PARTIAL | [Social seed](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L5): 24 outcomes, 57 activities, 53 indicators; substantive source mapping is incomplete. | AUD-019-014 |
| T017 | [X] | PARTIAL | [Economic seed](../../packages/domain/src/domain/seed/recovery-catalogue/economic.json#L5): 19 outcomes, 43 activities, 42 indicators; no complete source mapping or preserved gaps. | AUD-019-014 |
| T018 | [X] | PARTIAL | [Built seed](../../packages/domain/src/domain/seed/recovery-catalogue/built.json#L5): five outcomes, 19 activities, 18 indicators; undeveloped intergovernmental infrastructure outcome is not retained as such. | AUD-019-014 |
| T019 | [X] | PARTIAL | [Natural seed](../../packages/domain/src/domain/seed/recovery-catalogue/natural.json#L5): six outcomes, 16 activities, 17 indicators; authored summaries/methodologies are not a complete catalogue transcription. | AUD-019-014, AUD-019-028 |
| T020 | [X] | PARTIAL | [KEQ seed](../../packages/domain/src/domain/seed/recovery-catalogue/evaluation-questions.json#L1) has five questions per domain, not a complete source-section mapping. | AUD-019-014, AUD-019-021 |
| T021 | [X] | IMPLEMENTED | [Loader](../../scripts/seed_loader.py#L263) flattens by hierarchical ID/domain and [main](../../scripts/seed_loader.py#L643) calls catalogue seeding when configured. Actual seed inputs produce 369 documents; no loader was run. | AUD-019-014, AUD-019-015 |
| T022 | [X] | PARTIAL | [Plan repository](../../apps/api/app/repositories/emergency_plan_repository.py#L65) implements CRUD/region/state reads; requested hazard/hierarchy list filtering, tree behavior, and explicit failure semantics are incomplete. | AUD-019-005, AUD-019-011 |
| T023 | [X] | PARTIAL | [M&E repository](../../apps/api/app/repositories/me_framework_repository.py#L65) has framework/logic/report CRUD; volatile fallback and swallowed point-read failures weaken persistence guarantees. | AUD-019-005 |
| T024 | [X] | PARTIAL | [Catalogue repository](../../apps/api/app/repositories/recovery_catalogue_repository.py#L29) has read methods, but [Cosmos summary](../../apps/api/app/repositories/recovery_catalogue_repository.py#L144) compares singular kinds to plural keys. | AUD-019-015 |
| T025 | [X] | IMPLEMENTED | [Plan and M&E builders](../../apps/agents/common/handoffs.py#L192) follow the original envelope pattern. The module documents deprecation; delivery is not proved. | AUD-019-013, AUD-019-029 |
| T026 | [X] | PARTIAL | [Activation helpers](../../apps/agents/common/plan_activation.py#L12) author fallback/record/trigger shapes; no scoped runtime caller or endorsed snapshot producer was found. | AUD-019-003, AUD-019-012, AUD-019-013 |
| T027 | [X] | CONFLICT | [Agent transition table](../../apps/agents/planning/plan_lifecycle.py#L11) omits required conditional supersessions; [domain table](../../packages/domain/src/domain/models/plan_lifecycle.py#L22) disagrees further. | AUD-019-003 |
| T028 | [X] | PARTIAL | [Model tests](../../tests/unit/test_emergency_plan.py#L20) check constants and several states/validators; they do not exercise all lifecycle states or generated 27-section content. | AUD-019-003, AUD-019-007, AUD-019-034 |
| T029 | [X] | IMPLEMENTED | [Process-model tests](../../tests/unit/test_planning_process_record.py#L21) assert step bounds/completion timestamp, team/engagement nesting, and approval records. Execution unclaimed. | AUD-019-008, AUD-019-028 |
| T030 | [X] | PARTIAL | [Tests](../../tests/unit/test_me_framework.py#L168) set overdue flags manually and [accept standards without selection](../../tests/unit/test_me_framework.py#L222), omitting two requested assertions. | AUD-019-016, AUD-019-018, AUD-019-019, AUD-019-034 |
| T031 | [X] | PARTIAL | [Catalogue-model tests](../../tests/unit/test_recovery_outcome.py#L19) cover individual regex/types, not cross-entity domain/parent consistency or source completeness. | AUD-019-014, AUD-019-016, AUD-019-034 |
| T032 | [X] | IMPLEMENTED | [Evaluation-model tests](../../tests/unit/test_evaluation_report.py#L1) assert dates, valid domain keys, nested records, and safety-result presence. They are not generation/safety execution evidence. | AUD-019-002, AUD-019-021 |
| T033 | [X] | CONFLICT | [Tests import the other state machine](../../tests/unit/test_plan_lifecycle.py#L9), explicitly reject review-to-draft, and do not check live incident linkage. | AUD-019-003, AUD-019-034 |
| T034 | [X] | PARTIAL | [Planning contract tests](../../tests/contract/test_planning_api_contract.py#L27) omit activation and accept incomplete response shapes/no identity. | AUD-019-001, AUD-019-007, AUD-019-012, AUD-019-034 |
| T035 | [X] | CONFLICT | [Planning request/response models](../../apps/agents/planning/models.py#L34) use `user_role/new_state` and reduced activation fields instead of documented request/response names. | AUD-019-007, AUD-019-012, AUD-019-034 |
| T036 | [X] | PARTIAL | [Planning telemetry](../../apps/agents/planning/telemetry.py#L10) is local state/logs, not the required exported instruments and currency computation. | AUD-019-010, AUD-019-030 |
| T037 | [X] | PARTIAL | [Audit builders](../../apps/agents/planning/audit.py#L11) exist; actual agent uses private memory and role/system strings, with no durable endorsement path. | AUD-019-006 |
| T038 | [X] | PARTIAL | [Renamed risk helper](../../apps/agents/planning/plan_risk_assessment.py#L17) supports four labels and scenarios but fixed medium risk, generic cascades, and no caller. | AUD-019-009 |
| T039 | [X] | PARTIAL | [Pipeline](../../apps/agents/planning/pipeline.py#L12) scores completeness; assembly, PDF, and deadline enforcement are absent from that path. | AUD-019-007, AUD-019-008, AUD-019-031 |
| T040 | [X] | PARTIAL | [Planning factory](../../apps/agents/planning/agent.py#L235) has endpoints but not complete repository, risk, process, hierarchy, or authority integration. | AUD-019-001, AUD-019-005, AUD-019-007, AUD-019-008, AUD-019-009, AUD-019-011 |
| T041 | [X] | PARTIAL | [API plan service](../../apps/api/app/services/emergency_plan_service.py#L27) creates raw dictionaries and only flips lifecycle state; no full process record/tree/version behavior. | AUD-019-003, AUD-019-008, AUD-019-011 |
| T042 | [X] | PARTIAL | [Registered plan routes](../../apps/api/app/api/routes/emergency_plans.py#L13) expose different base/shapes, missing process/activation parity and scoped authorization. | AUD-019-001, AUD-019-007, AUD-019-012, AUD-019-034 |
| T043 | [X] | PARTIAL | [Cosmos-labelled suite](../../tests/integration/test_emergency_plans_cosmos.py#L1) explicitly uses memory and shallow hierarchy assertions, not a real Cosmos round trip. | AUD-019-005, AUD-019-011, AUD-019-034 |
| T044 | [X] | PARTIAL | [M&E contract suite](../../tests/contract/test_me_framework_api_contract.py#L91) uses standalone agent and invalid catalogue fixtures; report assertions are mainly keys/status. | AUD-019-016, AUD-019-020, AUD-019-021, AUD-019-034 |
| T045 | [X] | PARTIAL | [M&E request models](../../apps/agents/monitoring/models.py#L121) use untyped dictionaries and omit configurable KEQ input/contracted rich response semantics. | AUD-019-016, AUD-019-019, AUD-019-034 |
| T046 | [X] | IMPLEMENTED | [MonitoringConfig](../../apps/agents/monitoring/config.py#L76) reads all four added variables. Their operational use is not established. | AUD-019-018, AUD-019-026, AUD-019-031 |
| T047 | [X] | PARTIAL | [Agent M&E service](../../apps/agents/monitoring/me_framework_service.py#L23) lacks catalogue validation/suggestions, needs analysis, observed-data reporting, and date-derived overdue detection. | AUD-019-016, AUD-019-017, AUD-019-018, AUD-019-019, AUD-019-020 |
| T048 | [X] | PARTIAL | [EvaluationService](../../apps/agents/monitoring/evaluation_service.py#L22) creates empty sections and validates a constant; actual controllers do not use it. | AUD-019-002, AUD-019-021 |
| T049 | [X] | PARTIAL | [Monitoring endpoints](../../apps/agents/monitoring/agent.py#L403) route to local stores and incomplete services; no durable/shared framework or report path. | AUD-019-005, AUD-019-016, AUD-019-020, AUD-019-021, AUD-019-027 |
| T050 | [X] | PARTIAL | [Platform M&E service](../../apps/api/app/services/me_framework_service.py#L24) persists dictionaries but lacks required validation, observation evaluation, and graph integration. | AUD-019-016, AUD-019-020, AUD-019-021, AUD-019-022 |
| T051 | [X] | PARTIAL | [M&E routes](../../apps/api/app/api/routes/me_frameworks.py#L13) differ from incident-scoped contract and expose an ex-post echo. | AUD-019-001, AUD-019-016, AUD-019-022, AUD-019-034 |
| T052 | [X] | PARTIAL | [M&E persistence tests](../../tests/integration/test_me_framework_cosmos.py#L1) use memory; five keys are tested, not KEQ evidence or persisted cross-process behavior. | AUD-019-005, AUD-019-021, AUD-019-034 |
| T053 | [X] | PARTIAL | [Catalogue contract tests](../../tests/contract/test_recovery_catalogue_contract.py#L14) exercise agent paths, omit activity/indicator route coverage, and do not validate the Platform API. | AUD-019-015, AUD-019-034 |
| T054 | [X] | PARTIAL | [CatalogueService](../../apps/agents/monitoring/catalogue_service.py#L28) loads files and matches activities, but does not establish faithful full reference data, live tracking, rich endpoint detail, or Cosmos-backed runtime behavior. | AUD-019-014, AUD-019-015, AUD-019-017, AUD-019-027 |
| T055 | [X] | PARTIAL | [API catalogue facade](../../apps/api/app/services/recovery_catalogue_service.py#L13) has optional delegation but no wired repository or suggestion/seed-status implementation. | AUD-019-015 |
| T056 | [X] | PARTIAL | [Catalogue routes](../../apps/api/app/api/routes/recovery_catalogue.py#L14) construct the empty facade and omit the KEQ endpoint/contract response shapes. | AUD-019-015, AUD-019-034 |
| T057 | [X] | PARTIAL | [Catalogue tests](../../tests/unit/test_catalogue_service.py#L19) verify positive counts/filtering/matching but not authoritative completeness or backend behavior. | AUD-019-014, AUD-019-015, AUD-019-034 |
| T058 | [X] | PARTIAL | [Seed-query suite](../../tests/integration/test_recovery_catalogue_cosmos.py#L20) seeds memory directly, checks counts greater than zero, and never exercises the broken Cosmos summary branch. | AUD-019-005, AUD-019-014, AUD-019-015, AUD-019-034 |
| T059 | [X] | PARTIAL | [Indicator analysis](../../apps/agents/monitoring/indicator_analysis.py#L22) has optional LLM enrichment but no default wiring, history retrieval, supported correlation evidence, or fail-closed safety. | AUD-019-002, AUD-019-026, AUD-019-027 |
| T060 | [X] | PARTIAL | [API analysis facade](../../apps/api/app/services/ai_analysis_service.py#L16) is constructed without a client, returns no recommendations, and uses a counts-only summary. | AUD-019-002, AUD-019-026, AUD-019-027 |
| T061 | [X] | PARTIAL | [Analysis routes](../../apps/api/app/api/routes/ai_analysis.py#L13) accept arbitrary client dictionaries/IDs without contracted incident/audience/lookback semantics. | AUD-019-001, AUD-019-004, AUD-019-026, AUD-019-034 |
| T062 | [X] | CONFLICT | [Unsafe-path assertion](../../tests/unit/test_indicator_analysis.py#L202) expects unvalidated AI text; snapshot/all-pairs cases do not validate correlations against independent truth. | AUD-019-002, AUD-019-026, AUD-019-034 |
| T063 | [X] | PARTIAL | [Activation route](../../apps/agents/planning/agent.py#L336) checks endorsed state only, returns one content group, and omits role/live-incident/version fallback. | AUD-019-001, AUD-019-003, AUD-019-012 |
| T064 | [X] | PARTIAL | [Activation handoff handler](../../apps/agents/planning/agent.py#L213) is an acknowledgment stub; neither the legacy consumer nor MAF replacement performs the required workflow. | AUD-019-013, AUD-019-032 |
| T065 | [X] | PARTIAL | [Post-event route](../../apps/agents/planning/agent.py#L366) flips state without closure trigger, new version, supersession, or lessons delivery. | AUD-019-003, AUD-019-012, AUD-019-029 |
| T066 | [X] | MISSING | [Incident lookup behavior](../../apps/api/app/api/routes/emergency_plans.py#L103) is a fixed empty response; no region/hazard lookup replacement in the traced path. | AUD-019-012 |
| T067 | [X] | MISSING | [Ex-post endpoint](../../apps/api/app/api/routes/me_frameworks.py#L131) echoes input without reconstruction, validation, or storage; typed generic model is credited separately. | AUD-019-022 |
| T068 | [X] | PARTIAL | [Unused validator](../../apps/api/app/services/me_framework_service.py#L163) checks referenced IDs and one objective type only; no full connectivity, catalogue, timeline, or dependency-alert validation. | AUD-019-022, AUD-019-023 |
| T069 | [X] | PARTIAL | [M&E telemetry](../../apps/agents/monitoring/telemetry.py#L107) uses local rates/differently named counters and has no scoped service callers. | AUD-019-030 |
| T070 | [X] | PARTIAL | [Engagement helper](../../apps/agents/common/plan_activation.py#L59) counts stakeholders; it does not transfer participation evidence or have a caller. | AUD-019-028 |
| T071 | [X] | PARTIAL | [Evaluation lessons builder](../../apps/agents/common/handoffs.py#L214) exists but no controller sends it to the actual lessons service. | AUD-019-013, AUD-019-029 |
| T072 | [X] | PARTIAL | [Overlap helper](../../apps/agents/common/edge_cases.py#L12) intersects IDs, not observations; no shared-data runtime integration. | AUD-019-024 |
| T073 | [X] | PARTIAL | [Unavailability helper](../../apps/agents/common/edge_cases.py#L25) is disconnected, lacks reasons, and mishandles unknown freshness; reports always use empty warnings. | AUD-019-018, AUD-019-020 |
| T074 | [X] | PARTIAL | [Regression helper](../../apps/agents/common/edge_cases.py#L47) is disconnected and uses an unscoped ratio, not closed-program history/standards. | AUD-019-025 |
| T075 | [X] | PARTIAL | [Conflicting-standards helper](../../apps/agents/common/edge_cases.py#L64) groups labels but does not assess each standard or select a primary. | AUD-019-019 |
| T076 | [X] | PARTIAL | [Hierarchy helper](../../apps/agents/common/edge_cases.py#L87) only flags absent parents and is not called; terminology/arrangement comparison is absent. | AUD-019-011 |
| T077 | [X] | PARTIAL | [Simulation source](../../tests/simulation/test_planning_me_scenarios.py#L30) has four separate shallow checks, not the required nine-step-to-lessons flow. | AUD-019-013, AUD-019-029, AUD-019-034 |
| T078 | [X] | UNVERIFIED | [Quickstart](quickstart.md#L76) is authored guidance; no qualifying execution record in the reviewed inputs, and factory/state/transport patterns have drifted. | AUD-019-034, AUD-019-035 |

## Requirement Coverage

There are 35 functional requirements including FR-007a, nine NFRs, and ten success criteria: 54 individual rows. UNVERIFIED on a measured outcome does not excuse a functional defect identified elsewhere. Source-level support and observed execution are intentionally separate.

| Requirement | Status | Specific evidence and remaining obligation | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Nine step names](../../packages/domain/src/domain/models/planning_process_record.py#L14) and [raw step initialization](../../apps/agents/planning/agent.py#L54) exist; structured guidance/team/consultation flow is not connected. | AUD-019-008, AUD-019-033 |
| FR-002 | PARTIAL | [All 27 slugs](../../packages/domain/src/domain/models/emergency_plan.py#L26) exist, but [pipeline](../../apps/agents/planning/pipeline.py#L12) does not assemble/export the full plan. | AUD-019-007 |
| FR-003 | PARTIAL | [Renamed assessment](../../apps/agents/planning/plan_risk_assessment.py#L17) labels four environments/scenarios but uses fixed risk levels and is disconnected. | AUD-019-009 |
| FR-004 | PARTIAL | [Completeness calculation](../../apps/agents/planning/pipeline.py#L12) counts eight checkboxes; no evidence-driven principle workflow or endorsement enforcement. | AUD-019-008 |
| FR-005 | PARTIAL | [Region query](../../apps/api/app/repositories/emergency_plan_repository.py#L128) is flat and does not resolve cross-region ancestors or meaningful interoperability conflicts. | AUD-019-011 |
| FR-006 | CONFLICT | [Agent table](../../apps/agents/planning/plan_lifecycle.py#L11), [domain table](../../packages/domain/src/domain/models/plan_lifecycle.py#L22), and required transitions disagree; services omit endorsement/version/incident conditions. | AUD-019-003, AUD-019-010 |
| FR-007 | PARTIAL | [Activation](../../apps/agents/planning/agent.py#L336) creates a record but lacks real incident/AIIMS linkage and most operational content. | AUD-019-001, AUD-019-012, AUD-019-013 |
| FR-007a | PARTIAL | [Supplied role handling](../../apps/agents/planning/agent.py#L301) is not identity/assignment enforcement; [RBAC prefixes](../../apps/api/app/middleware/rbac_check.py#L33) omit these routes. | AUD-019-001 |
| FR-008 | PARTIAL | [Framework service](../../apps/agents/monitoring/me_framework_service.py#L23) covers basic configuration but not needs analysis, valid lifecycle progression, complete evaluation, or dissemination. | AUD-019-016, AUD-019-021 |
| FR-009 | PARTIAL | [Five-value domain type](../../packages/domain/src/domain/models/me_framework.py#L21) coexists with four-value tracker; source outcomes are rewritten and overarching roll-up is absent. | AUD-019-014, AUD-019-015, AUD-019-017 |
| FR-010 | PARTIAL | [Graph model](../../packages/domain/src/domain/models/program_logic_model.py#L46) and raw CRUD exist; ex-post reconstruction, validated timelines/chains, and visual builder do not. | AUD-019-022, AUD-019-023, AUD-019-033 |
| FR-011 | PARTIAL | [KEQ seed](../../packages/domain/src/domain/seed/recovery-catalogue/evaluation-questions.json#L1) and five report headings exist; complete questions and selectable reporting domains are not wired. | AUD-019-014, AUD-019-016, AUD-019-021 |
| FR-012 | PARTIAL | [Standard schema](../../packages/domain/src/domain/models/me_framework.py#L43) exists; service storage does not compare observations or enforce selection integrity. | AUD-019-016, AUD-019-019 |
| FR-013 | PARTIAL | [Monitoring report](../../apps/api/app/services/me_framework_service.py#L144) returns configuration and empty warnings rather than measured progress/trends/intervention evidence. | AUD-019-018, AUD-019-019, AUD-019-020 |
| FR-014 | PARTIAL | [Report/dissemination models](../../packages/domain/src/domain/models/evaluation_report.py#L50) exist, but generators return empty findings and have no reviewed dissemination path. | AUD-019-021 |
| FR-015 | PARTIAL | [Seed loader](../../scripts/seed_loader.py#L263) and optional tracker FK exist; 369 authored flattened records are a semantically incomplete substitute and the live API is not bound to the repository. | AUD-019-014, AUD-019-015, AUD-019-017 |
| FR-016 | PARTIAL | [Social seed](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L5) covers broad themes but not the full AIDR set or live outcome tracking. | AUD-019-014, AUD-019-017 |
| FR-017 | PARTIAL | [Economic seed](../../packages/domain/src/domain/seed/recovery-catalogue/economic.json#L5) covers broad business/workforce themes but substitutes activities/indicators and lacks live linkage. | AUD-019-014, AUD-019-017 |
| FR-018 | PARTIAL | [Built seed](../../packages/domain/src/domain/seed/recovery-catalogue/built.json#L5) covers essential/community/private infrastructure, but not faithful full outcomes or measured tracker integration. | AUD-019-014, AUD-019-017 |
| FR-019 | PARTIAL | [Natural seed](../../packages/domain/src/domain/seed/recovery-catalogue/natural.json#L5) includes health/ecosystems/heritage/risk themes; source fidelity, actual heritage input, and tracking remain open. | AUD-019-014, AUD-019-017, AUD-019-028 |
| FR-020 | PARTIAL | [Activity lookup](../../apps/agents/monitoring/catalogue_service.py#L80) exists; API default facade is empty and a usable intervention menu is not connected. | AUD-019-014, AUD-019-015, AUD-019-033 |
| FR-021 | PARTIAL | [Indicator metadata](../../packages/domain/src/domain/models/recovery_outcome.py#L64) exists; authoritative methodology, full presentation, and qualitative collection remain incomplete. | AUD-019-014, AUD-019-015, AUD-019-018 |
| FR-022 | IMPLEMENTED | [SelectedOutcome](../../packages/domain/src/domain/models/me_framework.py#L33) has a separate free-text restatement, [selection storage](../../apps/api/app/services/me_framework_service.py#L73) preserves it, and [unit tests](../../tests/unit/test_me_framework.py#L38) assert the value. Validated selection and guided UX remain separately open. | AUD-019-016, AUD-019-033 |
| FR-023 | PARTIAL | Objective types are modeled/filterable, but [live tracker service](../../apps/api/app/services/recovery_service.py#L27) has no objective-specific progress/reporting. | AUD-019-017, AUD-019-019, AUD-019-025 |
| FR-024 | PARTIAL | Vulnerable-group guidance is authored, but [tracker ingress](../../apps/api/app/api/routes/recovery.py#L18) lacks cohort support and privacy coverage is conditional. | AUD-019-004, AUD-019-017, AUD-019-028 |
| FR-025 | PARTIAL | [All-pairs lag analysis](../../apps/agents/monitoring/indicator_analysis.py#L22) is not multi-period, independently supported correlation evidence. | AUD-019-023, AUD-019-026 |
| FR-026 | PARTIAL | [Catalogue matching](../../apps/agents/monitoring/catalogue_service.py#L103) exists; [API recommendations](../../apps/api/app/services/ai_analysis_service.py#L85) return empty without an injected client and do not evaluate standards. | AUD-019-015, AUD-019-019, AUD-019-027 |
| FR-027 | PARTIAL | [Summary generation](../../apps/agents/monitoring/indicator_analysis.py#L110) is a counts-only template, not grounded audience-specific recovery reporting. | AUD-019-027, AUD-019-031 |
| FR-028 | CONFLICT | [Unvalidated AI output](../../apps/agents/monitoring/indicator_analysis.py#L97) and [hard-coded evaluation pass](../../apps/api/app/services/me_framework_service.py#L223) contradict mandatory safety. | AUD-019-002 |
| FR-029 | PARTIAL | [PPRR transition](../../apps/api/app/services/pprr_service.py#L30) maintains phases/timeline but does not surface plan sections or initialize linked M&E. | AUD-019-012, AUD-019-013 |
| FR-030 | PARTIAL | Optional catalogue FK preserves the base model, but [existing 21-indicator creation](../../apps/api/app/services/recovery_service.py#L27) is not extended by M&E selection. | AUD-019-016, AUD-019-017 |
| FR-031 | PARTIAL | [Tracker updates](../../apps/api/app/services/recovery_service.py#L83) accept fixed names only; [dashboard data](../../apps/api/app/services/governance_data_service.py#L491) is not a detailed-indicator roll-up. | AUD-019-017, AUD-019-020, AUD-019-033 |
| FR-032 | PARTIAL | [Engagement linkage helper](../../apps/agents/common/plan_activation.py#L59) returns a count and string without connected consultation/provenance transfer. | AUD-019-028 |
| FR-033 | PARTIAL | [Evaluation lessons envelope](../../apps/agents/common/handoffs.py#L214) exists; no inspected report/controller caller delivers it to the real lessons register. | AUD-019-029 |
| FR-034 | IMPLEMENTED | [Constitution handbook table](../../.specify/memory/constitution.md#L300) includes all three requested titles; approval and timing are not inferred. | AUD-019-035 |
| NFR-001 | UNVERIFIED | [15-second configuration](../../apps/agents/planning/config.py#L18) is not a full-document timing result; assembly itself is incomplete. | AUD-019-007, AUD-019-031 |
| NFR-002 | UNVERIFIED | No measured under-30-minute coordinator session; [M&E configuration](../../apps/agents/monitoring/me_framework_service.py#L23) and guided UI remain incomplete. | AUD-019-016, AUD-019-031, AUD-019-033 |
| NFR-003 | UNVERIFIED | [Recovery page](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L61) uses baseline aggregation; no 10-second expanded live-catalogue measurement. | AUD-019-020, AUD-019-031, AUD-019-033 |
| NFR-004 | UNVERIFIED | [30-second setting](../../apps/agents/monitoring/config.py#L81) has no qualifying 50-indicator end-to-end result or timeout assertion. | AUD-019-026, AUD-019-031 |
| NFR-005 | UNVERIFIED | [20-plan default](../../apps/agents/planning/config.py#L26) is not concurrent durable-plan validation across regions. | AUD-019-005, AUD-019-031 |
| NFR-006 | UNVERIFIED | [10-framework default](../../apps/agents/monitoring/config.py#L77) does not prove concurrent active recovery-framework support. | AUD-019-005, AUD-019-031 |
| NFR-007 | PARTIAL | [Planning metrics](../../apps/agents/planning/telemetry.py#L10) and [M&E counters](../../apps/agents/monitoring/telemetry.py#L107) lack the required rate/gauge semantics and callers. | AUD-019-030 |
| NFR-008 | UNVERIFIED | [AU-only primary parameter](../../infra/main.bicep#L78), [account location/backup](../../infra/main.bicep#L580), and [new containers](../../infra/modules/emergency-planning.bicep#L19) are authored support, not deployed-residency evidence. No non-AU data exception is granted here. | AUD-019-035 |
| NFR-009 | PARTIAL | [Sensitive-data check](../../apps/api/app/services/recovery_service.py#L83) permits unknown population and does not govern arbitrary new analysis/report inputs. | AUD-019-004 |
| SC-001 | PARTIAL | [27-element constant](../../packages/domain/src/domain/models/emergency_plan.py#L26) is tested by count; no generated full document proves 100% required content. | AUD-019-007, AUD-019-034 |
| SC-002 | UNVERIFIED | [Scenario test](../../tests/simulation/test_planning_me_scenarios.py#L30) performs one step/transition, not a five-working-day nine-step user process. | AUD-019-008, AUD-019-031, AUD-019-033 |
| SC-003 | PARTIAL | [Simulation M&E setup](../../tests/simulation/test_planning_me_scenarios.py#L80) selects one social outcome; no source assertion demonstrates three concrete domains with measured catalogue indicators. | AUD-019-017, AUD-019-031, AUD-019-034 |
| SC-004 | PARTIAL | [Graph model](../../packages/domain/src/domain/models/program_logic_model.py#L46) has the five stages, but exposed writes do not validate a connected, correctly linked AIDR model. | AUD-019-022, AUD-019-033 |
| SC-005 | UNVERIFIED | [Collection-rate helper](../../apps/agents/monitoring/telemetry.py#L140) is not called by collections, and no on-time event sample establishes 90%. | AUD-019-018, AUD-019-030, AUD-019-031 |
| SC-006 | UNVERIFIED | [All-pairs test](../../tests/unit/test_indicator_analysis.py#L97) repeats the heuristic, not an independently planted-correlation benchmark with 80% recall. | AUD-019-026, AUD-019-031 |
| SC-007 | UNVERIFIED | [Template summary tests](../../tests/unit/test_indicator_analysis.py#L246) do not establish 85% non-specialist reader approval. | AUD-019-027, AUD-019-031 |
| SC-008 | PARTIAL | [Activation response](../../apps/agents/planning/agent.py#L336) omits roles/resources/comms; no measured 10-second complete-content result exists in reviewed inputs. | AUD-019-012, AUD-019-031 |
| SC-009 | PARTIAL | [Five-domain assertion](../../tests/integration/test_me_framework_cosmos.py#L324) checks keys only; [generated findings](../../apps/api/app/services/me_framework_service.py#L187) are empty. | AUD-019-021, AUD-019-034 |
| SC-010 | UNVERIFIED | Three [handbook entries](../../.specify/memory/constitution.md#L300) exist, but the approval date and seven-day amendment interval are not evidenced by the reviewed records. | AUD-019-035 |

## Acceptance Scenario Coverage

`USn-ASm` is a report-local locator for the original user-story number and its numbered acceptance scenario, not a new requirement ID. All 27 original scenarios are individually assessed.

| Scenario | Status | Expected outcome compared with inspected evidence | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | Nine steps are named in [process constants](../../packages/domain/src/domain/models/planning_process_record.py#L14), but actual initiation exposes flags/summary, not full guided records. | AUD-019-008, AUD-019-033 |
| US1-AS2 | PARTIAL | [Risk helper](../../apps/agents/planning/plan_risk_assessment.py#L17) labels all four environments and scenario types without contextual assessment or a caller. | AUD-019-009 |
| US1-AS3 | PARTIAL | [Section slots](../../packages/domain/src/domain/models/emergency_plan.py#L26) cover the required elements; generation/detail/export omit the complete documented product. | AUD-019-007 |
| US1-AS4 | PARTIAL | Model review/exercise fields exist, but [service](../../apps/api/app/services/emergency_plan_service.py#L27) has no schedule/reminder/completion workflow. | AUD-019-003, AUD-019-010 |
| US1-AS5 | PARTIAL | [Hierarchy route](../../apps/agents/planning/agent.py#L275) returns regional summaries, not a parent-child tree with interoperability flags. | AUD-019-011 |
| US2-AS1 | PARTIAL | [Five-domain seed loader](../../apps/agents/monitoring/catalogue_service.py#L38) exists; full national source content and Platform API access are incomplete. | AUD-019-014, AUD-019-015 |
| US2-AS2 | PARTIAL | Restatement storage exists, but [logic creation](../../apps/api/app/services/me_framework_service.py#L87) accepts arbitrary disconnected structures. | AUD-019-016, AUD-019-022 |
| US2-AS3 | PARTIAL | [Outcome selection](../../apps/agents/monitoring/me_framework_service.py#L60) does not validate/enrich catalogue choices or provide custom/qualitative collection. | AUD-019-015, AUD-019-016, AUD-019-018 |
| US2-AS4 | PARTIAL | [Monitoring report](../../apps/agents/monitoring/me_framework_service.py#L102) echoes standards/flags, not baseline trends or actual comparisons. | AUD-019-018, AUD-019-019, AUD-019-020 |
| US2-AS5 | PARTIAL | [Evaluation generator](../../apps/api/app/services/me_framework_service.py#L187) produces empty findings rather than five evidence-based KEQ sections. | AUD-019-002, AUD-019-021 |
| US3-AS1 | PARTIAL | [Social reference file](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L5) provides broad themes but not full source outcomes/activities/indicators and tracking. | AUD-019-014, AUD-019-017 |
| US3-AS2 | PARTIAL | [Economic file](../../packages/domain/src/domain/seed/recovery-catalogue/economic.json#L5) is rewritten and not linked to live catalogue observations. | AUD-019-014, AUD-019-017 |
| US3-AS3 | PARTIAL | [Built file](../../packages/domain/src/domain/seed/recovery-catalogue/built.json#L5) includes essential/community/private/resilience themes; detailed measured outcomes are not connected. | AUD-019-014, AUD-019-017 |
| US3-AS4 | PARTIAL | [Natural file](../../packages/domain/src/domain/seed/recovery-catalogue/natural.json#L5) includes environment/heritage themes, not verified source fidelity or observed restoration/consultation. | AUD-019-014, AUD-019-017, AUD-019-028 |
| US3-AS5 | PARTIAL | Objective tags exist; [live tracker](../../apps/api/app/services/recovery_service.py#L27) does not separately report sustainability/resilience progress. | AUD-019-017, AUD-019-019 |
| US3-AS6 | PARTIAL | Restatement is possible, but [update input](../../apps/api/app/api/routes/recovery.py#L18) cannot capture separate authorised vulnerable-population observations. | AUD-019-004, AUD-019-017, AUD-019-028 |
| US4-AS1 | PARTIAL | [Correlation code](../../apps/agents/monitoring/indicator_analysis.py#L22) reports simultaneous lag, not supported multi-period or dependency evidence. | AUD-019-023, AUD-019-026 |
| US4-AS2 | PARTIAL | [Agent activity matching](../../apps/agents/monitoring/catalogue_service.py#L103) exists; no configured live API recommendation path or standards-based lag determination. | AUD-019-015, AUD-019-019, AUD-019-027 |
| US4-AS3 | PARTIAL | [Summary](../../apps/api/app/services/ai_analysis_service.py#L91) counts caller flags and ignores the contracted audience/period context. | AUD-019-027, AUD-019-031 |
| US4-AS4 | CONFLICT | [Unit assertion](../../tests/unit/test_indicator_analysis.py#L202) explicitly permits unvalidated AI output. | AUD-019-002 |
| US5-AS1 | MISSING | [Incident-plan lookup](../../apps/api/app/api/routes/emergency_plans.py#L103) returns no plans/recommendations regardless of incident. | AUD-019-012, AUD-019-013 |
| US5-AS2 | PARTIAL | [Activation](../../apps/agents/planning/agent.py#L336) returns arrangements only and lacks authorised complete operational content. | AUD-019-001, AUD-019-003, AUD-019-012 |
| US5-AS3 | MISSING | [PPRR transition caller](../../apps/api/app/services/pprr_service.py#L30) does not surface the plan or linked M&E; a disconnected trigger helper is not this workflow. | AUD-019-012, AUD-019-013 |
| US5-AS4 | PARTIAL | [Manual post-event route](../../apps/agents/planning/agent.py#L366) changes state, but incident conclusion, new version, pending revisions, and lessons are not linked. | AUD-019-003, AUD-019-012, AUD-019-029 |
| US6-AS1 | PARTIAL | [Graph types](../../packages/domain/src/domain/models/program_logic_model.py#L46) exist, but there is no connected national-template/visual-builder workflow. | AUD-019-022, AUD-019-033 |
| US6-AS2 | PARTIAL | [Raw graph write](../../apps/api/app/services/me_framework_service.py#L87) stores supplied data without validating national outcome links or timeline projections. | AUD-019-022 |
| US6-AS3 | MISSING | [Ex-post route](../../apps/api/app/api/routes/me_frameworks.py#L131) echoes the body; it does not reconstruct or persist the actual resources-to-outcomes chain. | AUD-019-022 |

## Edge Case Coverage

`EDGE-01` through `EDGE-07` are report-local locators in the original specification's order; they do not replace its descriptive edge-case names.

| Edge | Status | Specific obligation and evidence | Follow-up |
| --- | --- | --- | --- |
| EDGE-01 | PARTIAL | Overlapping programs: [helper](../../apps/agents/common/edge_cases.py#L12) detects common standard IDs only; shared collection data with separate logic/reports is not linked. | AUD-019-024 |
| EDGE-02 | PARTIAL | Unavailable/delayed data: [helper](../../apps/agents/common/edge_cases.py#L25) is disconnected; last-known values/reasons/unknown freshness do not reach reports. | AUD-019-018, AUD-019-020 |
| EDGE-03 | PARTIAL | Activation during revision: [fallback helper](../../apps/agents/common/plan_activation.py#L12) exists, but [activation](../../apps/agents/planning/agent.py#L336) rejects drafts and has no persisted endorsed snapshot/draft warning. | AUD-019-003, AUD-019-012 |
| EDGE-04 | PARTIAL | Regression after closure: [helper](../../apps/agents/common/edge_cases.py#L47) uses a fixed ratio without closure/history/standard or runtime notification. | AUD-019-025 |
| EDGE-05 | PARTIAL | Conflicting standards: [helper](../../apps/agents/common/edge_cases.py#L64) groups values without per-standard progress or coordinator primary selection. | AUD-019-019 |
| EDGE-06 | PARTIAL | Cascading domain recovery: [graph link type](../../packages/domain/src/domain/models/program_logic_model.py#L38) can say `depends_on`, but controllers/reporting do not track delays or alert downstream outcomes. | AUD-019-023 |
| EDGE-07 | PARTIAL | Plan hierarchy conflicts: [helper](../../apps/agents/common/edge_cases.py#L87) only notices missing local parents and is not connected; actual arrangement/terminology conflicts are not surfaced. | AUD-019-011 |

## Deep-Review Obligation Assessment

All 70 original items in [checklists/deep-review.md](checklists/deep-review.md) are unchecked. The rows below preserve that state and assess the question; IMPLEMENTED means that the scoped documentary question has a source-supported answer, not that a human completed the original checklist. Missing policy detail is not silently converted into new product scope. AUD-019-035 owns explicit owner decisions for such gaps.

| Item | Original state | Status | Specific assessment/evidence | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | FR-002 lists 27 titles; [handbook Chapter 3](../../docs/corpus/aidr/emergency-planning/handbook.md#L1438) supplies content guidance, but no per-section output criteria are enforced. | AUD-019-007, AUD-019-035 |
| CHK002 | [ ] | PARTIAL | [Process model](../../packages/domain/src/domain/models/planning_process_record.py#L85) names/tracks steps but does not define or enforce each step's entry/exit evidence. | AUD-019-008, AUD-019-035 |
| CHK003 | [ ] | PARTIAL | Exercise schedule is specified; exact required exercise types/frequency need an owner decision. [Config](../../apps/agents/planning/config.py#L23) only supplies a review interval. | AUD-019-010, AUD-019-035 |
| CHK004 | [ ] | PARTIAL | [EngagementEntry](../../packages/domain/src/domain/models/planning_process_record.py#L64) defines methods/records, but no active consultation capture/continuity workflow. | AUD-019-008, AUD-019-028 |
| CHK005 | [ ] | PARTIAL | FR-008 and [M&E source](../../docs/corpus/aidr/monitoring-evaluation-framework/handbook.md#L419) include needs analysis; framework service holds only a community string. | AUD-019-016, AUD-019-028 |
| CHK006 | [ ] | PARTIAL | [Seed KEQs](../../packages/domain/src/domain/seed/recovery-catalogue/evaluation-questions.json#L1) are generic subsets without complete source mapping. | AUD-019-014, AUD-019-021 |
| CHK007 | [ ] | PARTIAL | [Dissemination model](../../packages/domain/src/domain/models/evaluation_report.py#L50) names recipients/formats, not an implemented channel/review/frequency workflow. | AUD-019-021, AUD-019-035 |
| CHK008 | [ ] | CONFLICT | Spec assumptions acknowledge undeveloped outcomes; [source gaps](../../docs/corpus/aidr/outcomes-indicators/handbook.md#L115) are not retained in the all-developed seed. | AUD-019-014 |
| CHK009 | [ ] | PARTIAL | [CatalogueIndicator](../../packages/domain/src/domain/models/recovery_outcome.py#L64) supports qualitative/both, but source-methodology mapping and observation capture do not. | AUD-019-014, AUD-019-018 |
| CHK010 | [ ] | PARTIAL | R-006 chooses trend comparison and analysis contract requires periods; [code](../../apps/agents/monitoring/indicator_analysis.py#L22) uses one-snapshot all-pairs lag. | AUD-019-026, AUD-019-035 |
| CHK011 | [ ] | PARTIAL | Analysis contract describes strength/insufficient data; recommendation confidence/uncertainty criteria are not complete, and defaults have no AI adapter. | AUD-019-026, AUD-019-027, AUD-019-035 |
| CHK012 | [ ] | PARTIAL | CSV and JSON/PDF are explicit spec assumptions and R-007 intent, but [pipeline](../../apps/agents/planning/pipeline.py#L12) and collection routes do not deliver them. | AUD-019-007, AUD-019-018 |
| CHK013 | [ ] | PARTIAL | Four authored API contracts plus R-010 describe endpoints/auth/transport; [actual router](../../apps/api/app/api/router.py#L86) and factories diverge. | AUD-019-001, AUD-019-013, AUD-019-034 |
| CHK014 | [ ] | PARTIAL | [Security ratings](../../packages/domain/src/domain/models/emergency_plan.py#L24) are defined, but clearance/section-visibility policy and enforcement are not. | AUD-019-001, AUD-019-035 |
| CHK015 | [ ] | PARTIAL | No quantified standard recovery workload; the checklist's SC-002/NFR-006 citation is imprecise (session target is NFR-002). Owner-defined workload is needed. | AUD-019-031, AUD-019-035 |
| CHK016 | [ ] | PARTIAL | SC-002's standard regional plan lacks hazard/stakeholder/area bounds; [simulation](../../tests/simulation/test_planning_me_scenarios.py#L30) is not a complete proxy. | AUD-019-031, AUD-019-035 |
| CHK017 | [ ] | PARTIAL | SC-006 names known correlations, but [tests](../../tests/unit/test_indicator_analysis.py#L78) do not provide independent truth labels or count rules. | AUD-019-026, AUD-019-031 |
| CHK018 | [ ] | PARTIAL | SC-007 supplies 85% but not reader instrument/sample/window; template-summary assertions do not resolve it. | AUD-019-027, AUD-019-031, AUD-019-035 |
| CHK019 | [ ] | PARTIAL | [365-day default](../../apps/agents/planning/config.py#L23) and positivity checks exist; operating bounds and actual reminder scheduling do not. | AUD-019-010, AUD-019-035 |
| CHK020 | [ ] | PARTIAL | [Activation contract](contracts/planning-api.yaml#L133) names content groups, but UX/retrieval currently returns only one group. | AUD-019-007, AUD-019-012, AUD-019-033 |
| CHK021 | [ ] | PARTIAL | [Finding model](../../packages/domain/src/domain/models/evaluation_report.py#L24) carries evidence fields; generation supplies no substantive findings or sufficient-evidence criteria. | AUD-019-021, AUD-019-035 |
| CHK022 | [ ] | PARTIAL | Seven-day threshold is documented/configured; [helper](../../apps/agents/common/edge_cases.py#L25) is disconnected and unknown freshness is not handled honestly. | AUD-019-018 |
| CHK023 | [ ] | PARTIAL | Separate [restatement field](../../packages/domain/src/domain/models/me_framework.py#L33) exists; intent-preserving guidance and validation/consultation are not integrated. | AUD-019-016, AUD-019-028, AUD-019-035 |
| CHK024 | [ ] | PARTIAL | Community sustainability threshold lacks an agreed measurement rule; [fixed 0.9 helper](../../apps/agents/common/edge_cases.py#L47) is not that decision. | AUD-019-019, AUD-019-025, AUD-019-035 |
| CHK025 | [ ] | PARTIAL | Region/hazard/hierarchy are described in planning artifacts; [incident lookup](../../apps/api/app/api/routes/emergency_plans.py#L103) performs no matching. | AUD-019-011, AUD-019-012 |
| CHK026 | [ ] | PARTIAL | General-public/85% comprehension intent exists; no explicit readability instrument or audience-specific generation is wired. | AUD-019-027, AUD-019-031, AUD-019-035 |
| CHK027 | [ ] | IMPLEMENTED | Clarification 2 and [type aliases](../../packages/domain/src/domain/models/me_framework.py#L21) explicitly distinguish five catalogue domains from four tracker environments. Runtime roll-up remains open. | AUD-019-017 |
| CHK028 | [ ] | IMPLEMENTED | Spec terminology explains four concrete risk/recovery environments versus cross-cutting overarching; four-environment risk scope is not a missing fifth risk domain. | - |
| CHK029 | [ ] | CONFLICT | FR-006 and Key Entities agree, but [two current state machines](../../packages/domain/src/domain/models/plan_lifecycle.py#L22) and tests disagree with them. | AUD-019-003 |
| CHK030 | [ ] | IMPLEMENTED | [Spec 018](../018-aidr-guidance-integration/spec.md#L1) NFR-004 and this NFR-003 both specify a 10-second dashboard target; timing is unmeasured. | AUD-019-031 |
| CHK031 | [ ] | IMPLEMENTED | FR-011, US2-AS5, and SC-009 consistently name the five KEQ domains; [model](../../packages/domain/src/domain/models/me_framework.py#L14) encodes them. | AUD-019-021 |
| CHK032 | [ ] | CONFLICT | The spec repeats approximate 61/200/300 consistently, but full-source content and the 61/155/152 seed differ; exact provenance matters more than padding counts. | AUD-019-014 |
| CHK033 | [ ] | PARTIAL | Planning function is consistently stated in spec/plan; actual [role enforcement](../../apps/agents/planning/agent.py#L301) is request-string based. | AUD-019-001, AUD-019-032 |
| CHK034 | [ ] | PARTIAL | Schedule dates exist, but [collection test](../../tests/unit/test_me_framework.py#L168) manually sets overdue; no measured on-time event/window definition. | AUD-019-018, AUD-019-030, AUD-019-031 |
| CHK035 | [ ] | UNVERIFIED | No five-working-day rehearsal with consultation/endorsement dependencies in the reviewed evidence; [smoke simulation](../../tests/simulation/test_planning_me_scenarios.py#L30) is insufficient. | AUD-019-031, AUD-019-035 |
| CHK036 | [ ] | PARTIAL | No independent planted-correlation methodology; [all-pairs expectations](../../tests/unit/test_indicator_analysis.py#L97) repeat the algorithm. | AUD-019-026, AUD-019-031 |
| CHK037 | [ ] | PARTIAL | SC-003 clearly refers to three concrete domains; rationale for that threshold and a qualifying cross-domain tracked example are not evidenced. | AUD-019-017, AUD-019-031, AUD-019-035 |
| CHK038 | [ ] | IMPLEMENTED | SC-010 is a governance/timing claim distinct from software behavior; [table exists](../../.specify/memory/constitution.md#L300), approval interval remains UNVERIFIED. | AUD-019-035 |
| CHK039 | [ ] | IMPLEMENTED | R-007/contract distinguish 15-second document assembly from 10-second activation/content retrieval; neither is a demonstrated performance outcome. | AUD-019-007, AUD-019-012, AUD-019-031 |
| CHK040 | [ ] | PARTIAL | Multi-stakeholder standards/shared programs are described, but multi-community priorities and authority boundaries need explicit decisions. | AUD-019-019, AUD-019-024, AUD-019-035 |
| CHK041 | [ ] | PARTIAL | Content safety is required; conflict-resolution/uncertainty behavior for contradictory recommendations is not fully defined or connected. | AUD-019-002, AUD-019-027, AUD-019-035 |
| CHK042 | [ ] | PARTIAL | Activation history is modeled, but concurrent multiple-incident activation policy and atomicity are unspecified/unimplemented. | AUD-019-003, AUD-019-012, AUD-019-035 |
| CHK043 | [ ] | PARTIAL | Spec mandates conflict flagging, not a resolution algorithm; [helper](../../apps/agents/common/edge_cases.py#L87) falls short even of flagging substantive conflicts. | AUD-019-011, AUD-019-035 |
| CHK044 | [ ] | PARTIAL | Immutable catalogue is specified; edition migration/version/provenance policy needs an explicit owner decision before changing existing IDs. | AUD-019-014, AUD-019-035 |
| CHK045 | [ ] | PARTIAL | Last-endorsed revision fallback is specified; emergency live amendment policy is not. Do not infer permission to overwrite an activated version. | AUD-019-003, AUD-019-035 |
| CHK046 | [ ] | PARTIAL | Optional FK preserves spec 018 compatibility; the [M&E/tracker adoption link](../../apps/api/app/services/me_framework_service.py#L24) is not implemented. | AUD-019-016, AUD-019-017 |
| CHK047 | [ ] | PARTIAL | Shared outcomes are specified but per-program baseline reconciliation is not implemented; [overlap helper](../../apps/agents/common/edge_cases.py#L12) only intersects IDs. | AUD-019-019, AUD-019-024, AUD-019-035 |
| CHK048 | [ ] | PARTIAL | Non-blocking reports with available data are required; all-unavailable-domain output is not clearly defined or tested. | AUD-019-018, AUD-019-020, AUD-019-035 |
| CHK049 | [ ] | PARTIAL | Catalogue/custom extensions are allowed; zero/custom-only selection and collection behavior need explicit rules and valid service support. | AUD-019-016, AUD-019-018, AUD-019-035 |
| CHK050 | [ ] | CONFLICT | [Analysis contract](contracts/ai-analysis-api.yaml#L80) requires insufficient-data status and two periods; code/tests infer relationships from snapshots. | AUD-019-026 |
| CHK051 | [ ] | PARTIAL | FR-007a requires designated authority; unavailable/disputed/vacant authority policy is not supplied by role strings. No auto-approval default is justified. | AUD-019-001, AUD-019-003, AUD-019-035 |
| CHK052 | [ ] | PARTIAL | Review-to-new-draft is specified; fundamentally inadequate-plan handling needs an owner decision without bypassing endorsement. | AUD-019-003, AUD-019-035 |
| CHK053 | [ ] | PARTIAL | Four [hierarchy levels](../../packages/domain/src/domain/models/emergency_plan.py#L23) are defined; incomplete/invalid hierarchy behavior is not validated. No sub-local level is implied. | AUD-019-011, AUD-019-035 |
| CHK054 | [ ] | PARTIAL | Parent references exist but [flat hierarchy](../../apps/api/app/repositories/emergency_plan_repository.py#L128) does not handle a superseded parent. | AUD-019-003, AUD-019-011 |
| CHK055 | [ ] | PARTIAL | Existing [recovery widget](../../apps/web/src/components/governance/dashboard/RecoveryDomainTracker.tsx#L20) has labels/companion table; builder accessibility and measured target need definition and validation. | AUD-019-033, AUD-019-035 |
| CHK056 | [ ] | PARTIAL | Version/history retention is required, but exact archive/retention durations for these entities need an approved policy; none is inferred. | AUD-019-003, AUD-019-005, AUD-019-035 |
| CHK057 | [ ] | PARTIAL | [Planning contract](contracts/planning-api.yaml#L262) specifies cache/degraded behavior; available code has no connected endorsed-plan cache or offline workflow. | AUD-019-005, AUD-019-007, AUD-019-035 |
| CHK058 | [ ] | PARTIAL | Constitution IV and [audit helpers](../../apps/agents/planning/audit.py#L11) support intent; actual provenance is incomplete/private-memory-only. | AUD-019-006 |
| CHK059 | [ ] | PARTIAL | Initial seeding performance target is not specified; [loader](../../scripts/seed_loader.py#L325) is authored but not measured. Decide whether a seed SLO is needed instead of inventing one. | AUD-019-031, AUD-019-035 |
| CHK060 | [ ] | PARTIAL | [Repository updates](../../apps/api/app/repositories/emergency_plan_repository.py#L120) are unconditional upserts; concurrent edit/endorsement conflict behavior is not guaranteed. | AUD-019-003, AUD-019-005 |
| CHK061 | [ ] | UNVERIFIED | [Parent Cosmos account](../../infra/main.bicep#L580) declares continuous backup; no feature-specific restore/DR exercise or approved operational result was inspected. | AUD-019-005, AUD-019-035 |
| CHK062 | [ ] | PARTIAL | All three full handbooks were found in [relocated corpus](../../docs/corpus/aidr/emergency-planning/handbook.md#L1); stale assumption paths and provenance review remain. | AUD-019-014, AUD-019-035 |
| CHK063 | [ ] | PARTIAL | [Optional link/default](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L90) and null-link unit test support compatibility; actual opt-in/roll-up regression behavior remains untested. | AUD-019-017, AUD-019-034 |
| CHK064 | [ ] | CONFLICT | Existing safety validator exists but [bypass assertion](../../tests/unit/test_indicator_analysis.py#L202) contradicts mandatory validation for the new outputs. | AUD-019-002 |
| CHK065 | [ ] | PARTIAL | R-010 and [builders](../../apps/agents/common/handoffs.py#L192) document transport; neither legacy nor replacement runtime implements the required behavior. | AUD-019-013, AUD-019-032 |
| CHK066 | [ ] | PARTIAL | [PPRR service](../../apps/api/app/services/pprr_service.py#L30) exposes transitions/overlap, but plan/M&E callbacks are absent from the inspected caller. | AUD-019-012, AUD-019-013 |
| CHK067 | [ ] | PARTIAL | [Handbook table](../../.specify/memory/constitution.md#L300) is updated; approval identity/date and seven-day claim are not established. | AUD-019-035 |
| CHK068 | [ ] | IMPLEMENTED | R-007 explicitly retains human-authored plan content with AI assistance only; automated authoritative plan authorship is not required. | AUD-019-008 |
| CHK069 | [ ] | IMPLEMENTED | [ProgramLogicModel](../../packages/domain/src/domain/models/program_logic_model.py#L46) explicitly contains the outcome-chain relationships; it is not a separate ambiguous artifact. | AUD-019-022 |
| CHK070 | [ ] | PARTIAL | [Data model](data-model.md) separates immutable `aidr:` reference data and `custom:` extensions; no implemented governance/migration enforcement proves this separation. | AUD-019-014, AUD-019-016, AUD-019-035 |

## Quality Checklist and Plan Gates

The 16 unnumbered items in [checklists/requirements.md](checklists/requirements.md) are assigned report-local `QC-01` identifiers in original order. All originally use lowercase `[x]`. The plan's PASS assertions describe design coverage; they do not certify executed testing, infrastructure, or human review.

| Item | Original state | Status | Assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QC-01 | [x] | CONFLICT | "No implementation details": spec explicitly names agents, type aliases, Cosmos containers, ID schemes, and seed loading. Authored assertion is stale. | AUD-019-035 |
| QC-02 | [x] | IMPLEMENTED | User stories explain emergency-planning/recovery value and stakeholder needs. | - |
| QC-03 | [x] | PARTIAL | Narratives are stakeholder-oriented; several FRs/clarifications are implementation-specific and require a clearer audience separation. | AUD-019-035 |
| QC-04 | [x] | IMPLEMENTED | Mandatory stories, requirements, entities, assumptions, dependencies, and success criteria are populated. | - |
| QC-05 | [x] | IMPLEMENTED | No unresolved clarification marker in the source spec; this does not resolve the separately enumerated deep-review gaps. | - |
| QC-06 | [x] | PARTIAL | Named requirements exist, but standard workloads, evidence sufficiency, authority details, and qualitative/edge semantics remain ambiguous. | AUD-019-035 |
| QC-07 | [x] | PARTIAL | Numeric targets exist; collection windows, correlation truth set, and reader-study method are not defined sufficiently. | AUD-019-031, AUD-019-035 |
| QC-08 | [x] | IMPLEMENTED | SCs principally describe user/operational outcomes; no new technology-specific acceptance metric is needed. Governance timing is assessed separately. | - |
| QC-09 | [x] | IMPLEMENTED | All 27 numbered acceptance scenarios are authored. Their delivery and execution remain independently assessed above. | AUD-019-034 |
| QC-10 | [x] | IMPLEMENTED | All seven explicit edge cases are authored. Runtime helpers do not close them. | AUD-019-034 |
| QC-11 | [x] | IMPLEMENTED | Spec distinguishes AU feature scope, deferred PH/JP/BD variants, and external data-system exclusions. | - |
| QC-12 | [x] | PARTIAL | Assumptions/dependencies are listed, but handbook paths, architecture notes, and evidence prerequisites need reconciliation. | AUD-019-035 |
| QC-13 | [x] | PARTIAL | Requirements are traceable to scenarios, but not all have sufficiently concrete acceptance criteria or corresponding assertions. | AUD-019-034, AUD-019-035 |
| QC-14 | [x] | IMPLEMENTED | Six stories cover planning, M&E, domains, AI, incident use, and logic building; implementation gaps remain explicit. | AUD-019-034 |
| QC-15 | [x] | UNVERIFIED | "Feature meets measurable outcomes" is not supported by authored design documents or shallow tests without qualifying results. | AUD-019-031, AUD-019-035 |
| QC-16 | [x] | CONFLICT | The repeated no-implementation-leak assertion conflicts with current technical FRs/clarifications, as for QC-01. | AUD-019-035 |

| Plan gate | Authored claim | Status | Source-grounded assessment | Follow-up |
| --- | --- | --- | --- | --- |
| I | PASS | PARTIAL | Life-safety intent exists; unverified authority and incomplete activated content violate the intended operational boundary. | AUD-019-001, AUD-019-012 |
| II | PASS | PARTIAL | Named planning principles/PPRR intent exists, but process/risk/lessons integration is incomplete. | AUD-019-008, AUD-019-009, AUD-019-029 |
| II-A | PASS | PARTIAL | AIIMS Planning role is named but trusted assignment enforcement is absent on these paths. | AUD-019-001 |
| III | PASS | PARTIAL | Hazard/domain labels exist; fixed-risk analysis and flat hierarchy do not implement multi-hazard/multi-agency planning. | AUD-019-009, AUD-019-011 |
| IV | PASS | PARTIAL | Audit helper dictionaries are authored; durable decisions/provenance are not connected. | AUD-019-006 |
| V | PASS | PARTIAL | Warning/communication section slots exist; activation does not surface communication protocols and release review is not evidenced. | AUD-019-007, AUD-019-012, AUD-019-021 |
| VI | PASS | PARTIAL | Evacuation plan section exists; operational linkage/complete export is not established. | AUD-019-007, AUD-019-012 |
| VI-C | PASS | PARTIAL | Vulnerable populations are described, not separately tracked with enforced privacy in the extension. | AUD-019-004, AUD-019-017, AUD-019-028 |
| VII | PASS | PARTIAL | M&E/graph/report models exist; full recovery evaluation lifecycle is incomplete. | AUD-019-016, AUD-019-020, AUD-019-021, AUD-019-022 |
| VII-A | PASS | PARTIAL | Community-led principles are described; stakeholder evidence and needs priorities are not linked. | AUD-019-028 |
| VII-B | PASS | PARTIAL | Four concrete domains/fifth catalogue domain are modeled; full source catalogue and detailed live roll-up are not. | AUD-019-014, AUD-019-017 |
| VII-C | PASS | PARTIAL | Existing PPRR overlap is available, but plan-to-recovery/M&E handover is not connected. | AUD-019-012, AUD-019-013 |
| VIII | PASS | PARTIAL | Azure container declarations exist; packaged planning service is absent and deployment was not verified. | AUD-019-032, AUD-019-035 |
| NN-1 | PASS | PARTIAL | Human authorship/endorsement is the requirement; caller-supplied role strings are not human authorisation. | AUD-019-001, AUD-019-006 |
| NN-2 | PASS | UNVERIFIED | AU storage location is authored; actual residency/replication/logging was not queried or attested. | AUD-019-035 |
| NN-3 | PASS | PARTIAL | Conditional sensitive-data check does not guarantee the extended small-cohort privacy boundary. | AUD-019-004 |
| NN-4 | PASS | PARTIAL | JSON routes exist; prose contract shapes, CSV collection, full-plan/PDF export are incomplete. | AUD-019-007, AUD-019-018, AUD-019-034 |
| NN-5 | PASS | PARTIAL | Fallback helper/optional clients exist; actual persistence failures become volatile storage or empty results rather than the specified degradation. | AUD-019-005, AUD-019-015, AUD-019-027 |
| QG | PASS | UNVERIFIED | No qualifying test-first/PR tests/IaC what-if/human-output review evidence was inspected for 019. | AUD-019-034, AUD-019-035 |

The final aggregate "Gate Result: PASS" in [plan.md](plan.md) is consequently an authored design assertion, not a confirmed implementation gate. Each phase checkpoint in [tasks.md](tasks.md) is similarly not executable evidence: skeleton health/infra (T001-T007), model/seed foundation (T008-T033), planning (T034-T043), M&E (T044-T052), catalogue (T053-T058), AI (T059-T062), incident activation (T063-T066), graph (T067-T068), and integrated polish (T069-T078) all retain the individual findings above. The plan does not provide historical FAIL-before-implementation/PASS-after records or a signed reviewer result.

## Clarifications, Amendments, and Boundaries

`CL-01` through `CL-10` map, in order, to the two five-question clarification sessions in the full spec. These are amendments to the original obligations and are not ignored in favor of older quickstart examples.

| Obligation | Status | Assessment/evidence | Follow-up |
| --- | --- | --- | --- |
| CL-01 | CONFLICT | Formal seven-state lifecycle is defined; duplicate state machines and runtime mutations disagree. | AUD-019-003 |
| CL-02 | PARTIAL | New Planning Agent and monitoring extension exist as source; deployed package, persistence, and capability boundaries are incomplete. | AUD-019-005, AUD-019-032 |
| CL-03 | PARTIAL | Deployment-time loader exists; immutable complete reference data, separate custom extensions, and runtime Cosmos source are not fully implemented. | AUD-019-014, AUD-019-015, AUD-019-016 |
| CL-04 | PARTIAL | Planning Officer/IC/designated-authority intent exists, not trusted scoped authority enforcement. | AUD-019-001 |
| CL-05 | IMPLEMENTED | Canonical new domain terminology and the retained four-value legacy environment type are explicitly documented. | - |
| CL-06 | PARTIAL | 27 elements, including contents/glossary, are defined; full generated output is not delivered. | AUD-019-007 |
| CL-07 | PARTIAL | Five-value catalogue/four-value tracker types exist; overarching-to-concrete roll-up is missing from the runtime path. | AUD-019-017 |
| CL-08 | PARTIAL | Hierarchical IDs/container/optional FK exist, but complete faithful catalogue, relationship checks, and actual source binding do not. | AUD-019-014, AUD-019-015, AUD-019-016 |
| CL-09 | CONFLICT | Exact transitions/roles/incident conditions are not enforced; the unit-test state machine rejects the mandated review-to-draft flow. | AUD-019-003 |
| CL-10 | PARTIAL | KEQs are report dimensions rather than a separate collection subsystem, but configurable domains/full questions/evidence generation are incomplete. | AUD-019-014, AUD-019-016, AUD-019-021 |
| PER-049 | UNVERIFIED | Cross-reference to operational personas exists. [Referenced source](../001-disaster-response-hub/spec.md#L167) says concrete SME identities are recorded during review; role labels alone do not meet the [persona validation contract](../027-spec-hardening/contracts/persona-profile.md#L8). | AUD-019-035 |
| PER-050 | UNVERIFIED | Technical-actor cross-reference exists, but [the referenced spec](../004-actor-github-agents/spec.md#L165) repeats declarations, not dated practitioner validation for this feature. | AUD-019-035 |
| PER-051 | IMPLEMENTED | Non-AU operator personas are explicitly placeholders pending D-009 and SME review, not asserted delivered capabilities. No PH/JP/BD implementation is demanded by this audit. | - |
| HYP-017 | UNVERIFIED | Authored hypothesis exists; named stub has no scoped filename match. [Portfolio rubric results](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) do not establish spec-019 uplift or consultation on every change. | AUD-019-035 |
| SCP-055 | IMPLEMENTED | Non-AU variants remain deferred with decision, legal/data-sharing, and calibration-signoff prerequisites. [D-009 record](../028-capstone-alignment/evidence/decision-record.md#L9) explicitly preserves that deferral. | - |
| SCP-056 | PARTIAL | No unilateral constitutional exception is authorised by 019; required `[RISK]` documentation for any tension is not present in its Assumptions. Existing model-hosting carve-out does not exempt data stores. | AUD-019-035 |
| SCP-057 | IMPLEMENTED | Explicit defers-to 018/008 and product-owner arbitration boundaries are authored. This report does not retire their obligations or invent warning/country requirements for 019. | - |

The directly referenced [First Nations liaison profile](../001-disaster-response-hub/spec.md#L331) assigns cultural advisory responsibilities. Together with FR-019/FR-024/FR-032 and the source handbook's consultation guidance, this supports requiring attributable community/heritage input, not inventing a new unilateral cultural approval authority. A configured role, prompt, source paragraph, or cultural-heritage catalogue entry is not an observed consultation or sign-off. Warnings, multilingual delivery, evacuation execution, and country-specific governance remain with their named owners; only 019's real integration obligations are audited here.

| Assumption/dependency | Status | Evidence/assessment | Follow-up |
| --- | --- | --- | --- |
| A-01: three converted handbooks | IMPLEMENTED | All three found and fully read under the relocated corpus; stale original paths are not missing content. | AUD-019-035 |
| A-02: extend, not replace 018 | PARTIAL | Optional catalogue FK/type preservation exists; detailed tracker/PPRR/lessons integrations remain disconnected. | AUD-019-013, AUD-019-017, AUD-019-029 |
| A-03: immutable seed/custom/KEQs | PARTIAL | Loader/source files exist but substitute content, omit explicit undeveloped gaps, and lack a governed custom extension path. | AUD-019-014, AUD-019-015, AUD-019-016 |
| A-04: new planning, existing monitoring | PARTIAL | Source factories exist; package/dispatcher and raw-dictionary boundaries do not deliver the complete services. | AUD-019-005, AUD-019-032 |
| A-05: use existing AI capacity | PARTIAL | Existing LLMClient remains available; default 019 factories/facades do not inject it. No new AI provisioning is required by this report. | AUD-019-027 |
| A-06: manual/semi-auto, CSV, JSON/PDF | PARTIAL | Legacy numeric entry and raw JSON reads exist; catalogue-linked/qualitative/CSV collection and full document export remain incomplete. External ABS/health integrations remain deferred. | AUD-019-007, AUD-019-018 |
| A-07: external AIDR evaluation database | IMPLEMENTED | It is a human-consulted reference, explicitly not integrated. Missing direct integration is not a finding. | - |
| D-01: spec 018 tracker/PPRR/lessons | PARTIAL | Actual owning services were read; available shared capability does not prove a 019 caller. | AUD-019-013, AUD-019-017, AUD-019-029 |
| D-02: constitution amendment | PARTIAL | Three handbook titles exist; version/approval timing and deployment-residency evidence remain separate. | AUD-019-035 |
| D-03: incident/simulation/safety/evacuation | PARTIAL | Incident/PPRR and safety services exist; incomplete authority/activation/safety wiring blocks the specified integration. | AUD-019-001, AUD-019-002, AUD-019-012, AUD-019-034 |
| D-04: authoritative AIDR reference | PARTIAL | Full source is available after relocation, but seed provenance/completeness needs source-by-source reconciliation. | AUD-019-014 |
| TERM-01: domain versus environment | IMPLEMENTED | Five reference domains versus four concrete environments are documented and represented by distinct type aliases. | - |
| TERM-02: evaluation domain | PARTIAL | Five KEQ types exist and are report dimensions; selectable KEQs/report evidence remain incomplete, not a need for new collection subsystems. | AUD-019-016, AUD-019-021 |
| TERM-03: catalogue versus tracker indicator | PARTIAL | Template/live-data distinction and optional FK exist; runtime linkage and separately governed custom observations do not. | AUD-019-017, AUD-019-018 |

## Research and Data-Model Obligations

All research decisions and model definitions were read, including configurable parameters and container summaries. A design decision is not proof that its caller, measurement, or deployment exists.

| Decision/model | Status | Source-grounded result | Follow-up |
| --- | --- | --- | --- |
| R-001 | PARTIAL | Planning source factory/class exists; human-guided planning and supported runtime registration are incomplete. | AUD-019-008, AUD-019-032 |
| R-002 | CONFLICT | Transition-table pattern exists twice with contradictory semantics; role/incident/version conditions are incomplete. | AUD-019-003 |
| R-003 | IMPLEMENTED | All three declared containers/partitions/autoscale settings exist in Bicep. Backend query/index behavior and deployment remain separate. | AUD-019-015, AUD-019-035 |
| R-004 | PARTIAL | Loader uses domain JSON and upsert; agent instead loads files and API is unbound. Full source catalogue/custom separation is incomplete. | AUD-019-014, AUD-019-015 |
| R-005 | PARTIAL | Framework/optional FK models preserve tracker compatibility, but no live framework-to-observation-to-tracker enrichment. | AUD-019-017 |
| R-006 | PARTIAL | Optional LLM call exists, but no injected production path, history query, grounded correlation, or fail-closed result validation. | AUD-019-002, AUD-019-026, AUD-019-027 |
| R-007 | PARTIAL | Human-authored plan principle is explicit; source pipeline only scores and does not assemble JSON/PDF output within a measured budget. | AUD-019-007 |
| R-008 | PARTIAL | Parent/activation fields/helpers exist, but actual tree/version/incident conditions are not wired. | AUD-019-003, AUD-019-011, AUD-019-012 |
| R-009 | PARTIAL | API persists empty evaluation structures; agent omits findings and stores report ID only. | AUD-019-005, AUD-019-021 |
| R-010 | CONFLICT | Legacy queue design is documented as replaced by MAF, but required 019 behavior has not been delivered by either path. | AUD-019-013, AUD-019-029 |
| R-011 | PARTIAL | Optional regex-checked FK exists; automatic association from M&E selection and legacy regression coverage are incomplete. | AUD-019-017, AUD-019-034 |
| R-012 | PARTIAL | Port 8085 entry exists; planning health lacks the named dependency checks and deployment serves another factory. | AUD-019-005, AUD-019-032 |
| R-013 | PARTIAL | Required rates are local state or event counters, without complete runtime measurement/export. | AUD-019-030 |
| E-001 | IMPLEMENTED | Existing RecoveryIndicator fields/validators are preserved and optional catalogue FK added. Full privacy/live-link obligations are separately partial. | AUD-019-004, AUD-019-017 |
| N-001 | PARTIAL | EmergencyPlan schema is authored; runtime raw documents bypass endorsement/version/section/security behavior. | AUD-019-001, AUD-019-003, AUD-019-007 |
| N-002 | PARTIAL | Nested process/team/engagement/approval schemas exist; endpoints store only step dictionaries, not the full record. | AUD-019-008, AUD-019-028 |
| N-003 | PARTIAL | Framework fields exist; standards membership, validated catalogue selection, schedule semantics, and lifecycle controls are incomplete. | AUD-019-016, AUD-019-018, AUD-019-019 |
| N-004 | PARTIAL | Graph schema validates referenced IDs; runtime writes bypass it and omit connectedness/catalogue/timeline/ex-post validation. | AUD-019-022, AUD-019-023 |
| N-005 | PARTIAL | Catalogue schemas/IDs exist; parent/domain coherence, faithful reference data, immutable/custom separation, and hydrated runtime access are incomplete. | AUD-019-014, AUD-019-015, AUD-019-016 |
| N-006 | PARTIAL | Evaluation model contains the required fields; real report generation, safety proof, persistence parity, and dissemination are incomplete. | AUD-019-002, AUD-019-005, AUD-019-021 |
| PARAM-01 | PARTIAL | Plan timeout 15s is read but no assembly operation uses it. | AUD-019-007, AUD-019-031 |
| PARAM-02 | PARTIAL | Analysis timeout 30s is read but not enforced as an end-to-end configured operation deadline. | AUD-019-026, AUD-019-031 |
| PARAM-03 | PARTIAL | Review reminder default 365 days is read but no reminder caller exists. | AUD-019-010 |
| PARAM-04 | PARTIAL | Indicator staleness seven days is read; reports/collection do not apply it to actual observations. | AUD-019-018 |
| PARAM-05 | UNVERIFIED | Twenty-plan capacity value exists; concurrent durable support is unmeasured. | AUD-019-031 |
| PARAM-06 | UNVERIFIED | Ten-framework capacity value exists; concurrent active support is unmeasured. | AUD-019-031 |
| PARAM-07 | PARTIAL | One-hour catalogue TTL variable exists; file-loaded agent catalogue/no-repository API do not implement that cache contract. | AUD-019-015 |
| PARAM-08 | PARTIAL | Minimum-ten privacy intent exists; conditional hard-coded check is not an enforced configurable policy across the new paths. | AUD-019-004 |

The shared architecture's distinct five-domain reference type, separate immutable catalogue container, and seven-state planning lifecycle are justified in the plan's complexity section. The audit does not propose collapsing them into the legacy four-domain tracker, merging mutable/reference data, or a three-state lifecycle. It requires implementing the already chosen boundaries consistently.

## Contract Obligation Coverage

The four complete local contracts define 28 endpoints plus role, failure, latency, and observability behavior. These report-local endpoint IDs enumerate that contract surface. Merely accepting a differently shaped request in a test does not amend a contract. AUD-019-034 requires explicit compatibility/contract decisions before changing public behavior.

| Contract item | Status | Expected versus actual route/service evidence | Follow-up |
| --- | --- | --- | --- |
| PAPI-01: create plan | PARTIAL | Contract `/api/planning/plans` expects full initialization/process summary/security/authority fields; actual `/plans` returns a reduced summary and API uses `/emergency-plans`. | AUD-019-001, AUD-019-007, AUD-019-008, AUD-019-034 |
| PAPI-02: get full plan | PARTIAL | Agent returns summary only; API can return dictionary with sections but requires caller-supplied region key and lacks full process record/visibility enforcement. Two-second retrieval is unmeasured. | AUD-019-001, AUD-019-005, AUD-019-007, AUD-019-031 |
| PAPI-03: filtered paginated list | PARTIAL | Agent ignores all filters; API exposes region/state only, with no continuation pagination or hazard/hierarchy filtering. | AUD-019-011, AUD-019-034 |
| PAPI-04: update section | CONFLICT | Contract allows draft, consultation, and post-event review and returns a PlanSection; implementations allow only first two and return summary/full plan. `edited_by` is not trusted/persisted correctly. | AUD-019-001, AUD-019-003, AUD-019-006, AUD-019-007, AUD-019-034 |
| PAPI-05: transition | CONFLICT | Contract request uses `authorised_by/authorisation_role/rationale/incident_id`; code expects `user_role/reason`, omits incident verification, returns different fields, and maps invalid cases largely to 422 rather than specified 400/403/409. | AUD-019-001, AUD-019-003, AUD-019-034 |
| PAPI-06: activate | PARTIAL | Endorsed-state check/history exists, but live-incident/IC/version fallback and roles/resources/comms content are absent; 10-second timing unverified. | AUD-019-001, AUD-019-003, AUD-019-012, AUD-019-031 |
| PAPI-07: hierarchy | PARTIAL | Actual output is a regional list instead of nested national/state/regional/local children and actionable interoperability flags. | AUD-019-011 |
| PAPI-08: process step | PARTIAL | Agent updates a boolean/notes dictionary and returns a plan summary; API has no equivalent process endpoint or complete record update. | AUD-019-001, AUD-019-008, AUD-019-034 |
| PAPI-09: completeness | PARTIAL | Code counts section/principle flags, using different field names without the contracted principle map/readiness semantics; no evidence-based validation. | AUD-019-008, AUD-019-034 |
| PAPI-10: health | PARTIAL | Agent always returns healthy without LLM/Cosmos/pipeline checks; one-second healthy/degraded behavior is not established. | AUD-019-005, AUD-019-031, AUD-019-032 |
| MAPI-01: create framework | PARTIAL | Actual routes require body incident ID under a different base, ignore active KEQ selection, and do not link the existing tracker. | AUD-019-001, AUD-019-016, AUD-019-017, AUD-019-034 |
| MAPI-02: get framework | PARTIAL | Actual routes use framework ID (and API query incident ID), not the contracted incident lookup; durable shared behavior is absent on the agent path. | AUD-019-005, AUD-019-034 |
| MAPI-03: select outcomes | PARTIAL | Unvalidated supplied dictionaries replace selection; no derived domain/objective/suggested indicators/activities or governed custom input. | AUD-019-014, AUD-019-015, AUD-019-016 |
| MAPI-04: program logic | PARTIAL | Raw data is stored/returned without full graph/catalogue/timeline validation; extra ex-post endpoint is an echo. | AUD-019-022, AUD-019-034 |
| MAPI-05: standards | PARTIAL | Setter stores arbitrary standards and does not evaluate membership, operators, or primary stakeholder semantics. | AUD-019-019 |
| MAPI-06: collection schedule | PARTIAL | Setter stores arbitrary dictionaries/flags, lacks observation capture/date-based overdue handling, and activates incomplete framework. | AUD-019-016, AUD-019-018 |
| MAPI-07: monitoring report | PARTIAL | No report period, baseline history, domain outcome totals, per-standard assessment, or required evidence-driven alerts; configured standards are returned as indicator status. | AUD-019-018, AUD-019-019, AUD-019-020 |
| MAPI-08: evaluation | PARTIAL | Actual output lacks KEQ findings/evidence and may fabricate safety pass; agent stores ID only, API persists empty findings. | AUD-019-002, AUD-019-005, AUD-019-021 |
| CAPI-01: browse outcomes | PARTIAL | Registered API default is empty; lacks `has_indicators`, total/filtered counts, activity/indicator counts, and faithful full catalogue. | AUD-019-014, AUD-019-015, AUD-019-034 |
| CAPI-02: outcome detail | PARTIAL | API requires undocumented domain query and returns no data by default; agent detail supplies IDs rather than hydrated activity/indicator objects. | AUD-019-015, AUD-019-034 |
| CAPI-03: activities | PARTIAL | API endpoint exists but unbound service returns empty; agent has a lookup helper but not a matching nested route. | AUD-019-015 |
| CAPI-04: indicators | PARTIAL | API endpoint exists but unbound service returns empty; methodology/indicator data do not reach the contracted response. | AUD-019-014, AUD-019-015 |
| CAPI-05: domain summary | PARTIAL | Cosmos branch never assigns singular kinds to plural count keys; neither route returns full sustainability/resilience/undeveloped/category summary. | AUD-019-015 |
| CAPI-06: suggest activities | PARTIAL | Contract takes lagging-indicator objects and returns structured suggestions; actual route takes ID list, API suggestion is empty, agent matches only parent activities. | AUD-019-015, AUD-019-019, AUD-019-027, AUD-019-034 |
| CAPI-07: evaluation questions | MISSING | API route absent after inspecting full catalogue router/service/repository; agent counterpart exists, but returns its own shape and cannot substitute for the documented Platform API route. | AUD-019-015, AUD-019-034 |
| AAPI-01: cross-domain analysis | PARTIAL | Contract is incident-scoped with domain/lookback/recommendation options; actual input is a snapshot list and output lacks required strength/period/sample/insufficient-data semantics. | AUD-019-004, AUD-019-026, AUD-019-034 |
| AAPI-02: recommendations | PARTIAL | Contract computes gaps against standards and enriches catalogue recommendations; default API returns empty from caller IDs, with no real lagging selection or rationale path. | AUD-019-019, AUD-019-027 |
| AAPI-03: community summary | PARTIAL | Contract takes audience/domain selection and returns titled narrative plus per-domain details; actual output is counts from caller data with no privacy/safety review chain. | AUD-019-002, AUD-019-004, AUD-019-027 |

| Cross-cutting contract obligation | Status | Assessment | Follow-up |
| --- | --- | --- | --- |
| AUTH-P/M/C/A | PARTIAL | None of the four exposed surfaces enforces the specified identity/role/visibility policy end to end; claim-population middleware is not sufficient. | AUD-019-001 |
| DEG-P: planning outages/revisions | PARTIAL | No connected last-endorsed cache/revision activation fallback; persistence faults may become missing records or volatile stores. LLM-free manual drafting intent is retained. | AUD-019-003, AUD-019-005, AUD-019-007 |
| DEG-M: missing data/catalogue/LLM | PARTIAL | Empty warnings ignore missing-data detail; catalogue outage cannot be distinguished from unbound selection; AI evaluation fabricates pass rather than an honest 503/partial response. | AUD-019-002, AUD-019-015, AUD-019-018, AUD-019-021 |
| DEG-C: catalogue cache/suggestions | PARTIAL | Agent file-loading is not a configured one-hour Cosmos cache; API returns empty suggestions rather than usable catalogue fallback. | AUD-019-015, AUD-019-027 |
| DEG-A: AI unavailable/unsafe/insufficient | CONFLICT | Rule fallback exists, but missing-validator output is released and insufficient-data metadata is absent. | AUD-019-002, AUD-019-026, AUD-019-027 |
| PERF-P/M/C/A | UNVERIFIED | Full-plan read <=2s, catalogue browse <=3s, health <=1s, activation/dashboard <=10s, assembly <=15s, and 50-indicator analysis <=30s are not measured in the reviewed evidence. | AUD-019-031 |
| OBS-P | PARTIAL | Activation count/section completeness use local dict/logs; plan currency ratio has no computation/caller. | AUD-019-030 |
| OBS-M | PARTIAL | Framework completion/collection/achievement rates are not emitted as the required gauges from actual events. | AUD-019-030 |
| OBS-C | MISSING | Catalogue query-count and suggestion-latency instrumentation is absent from the fully read catalogue query/suggestion paths. | AUD-019-030 |
| OBS-A | MISSING | Analysis-latency, recommendation-count, and content-safety-failure metrics are absent from the fully read 019 analysis paths. Shared LLM metrics are not replacements. | AUD-019-030 |

## Evidence Ledger and Completion Gates

| Evidence category | What the inspected material establishes | What it does not establish | Status/follow-up |
| --- | --- | --- | --- |
| Feature specification/design | Six stories, 27 scenarios, seven edges, 54 requirement/SC IDs, ten clarifications, seven named PER/HYP/SCP amendments, and associated plans/contracts are authored. | Product delivery, agreement on every ambiguous definition, or approved amendment scope. | PARTIAL; AUD-019-035 |
| Original task checkboxes | All 78 task rows are originally `[X]`, preserved verbatim in this report. | That tests/builds/deployments or handoffs actually ran. | UNVERIFIED execution; AUD-019-034 |
| Local checklists | Sixteen structural items are checked; 70 deep-review questions are unchecked; plan has 19 PASS gate claims. | A signed implementation review, closure of unanswered questions, or runtime conformance. | PARTIAL; AUD-019-035 |
| Source models/helpers | Type aliases, fields, constants, validators, request handlers, reference loaders, and several helpers exist. | Call-path integration where the report identifies disconnected helpers or raw dictionaries. | PARTIAL; individual functional AUD tasks |
| Unit/contract tests | Inspected assertion text covers some constants, field validation, basic endpoint shape, lookup, and fallback branches. | Execution success, exact contract conformance, real identity/partition behavior, or independent scientific correctness. | PARTIAL authored coverage; AUD-019-034 |
| Cosmos-labelled integration tests | Authored in-memory CRUD/query scenarios. | Live/emulator Cosmos query/index/partition results, restart persistence, or deployment status. | UNVERIFIED backend outcomes; AUD-019-005, AUD-019-015, AUD-019-034 |
| Simulation | Four independent smoke checks in the named file. | The required complete plan-to-incident-to-recovery-to-evaluation-to-lessons flow. | PARTIAL; AUD-019-034 |
| Catalogue inventory | Read-only JSON parse found 61/155/152 records and five KEQ groups; all files were read against the full handbooks. | That 369 flattened documents were loaded, immutable in production, or approved as faithful source content. | PARTIAL provenance; AUD-019-014, AUD-019-015 |
| Infrastructure source | Three containers and AU primary account/backup settings are declared; seed hook/main are authored. | Successful compilation, what-if review, deployment, actual data residency, failover, or restore outcome. | UNVERIFIED operations; AUD-019-035 |
| Handbook/constitution artifacts | Relocated source handbooks and all three constitutional reference titles exist. | Project-lead approval identity/date or SC-010 timing. | IMPLEMENTED artifacts; UNVERIFIED approvals; AUD-019-035 |
| Persona/hypothesis records | Cross-references and portfolio structural scores exist, including explicit non-AU deferral. | Named/datetimed SME validation for PER-049/PER-050, HYP-017 results, or universal actor consultation. | UNVERIFIED; AUD-019-035 |
| Cultural/community involvement | Source guidance and catalogue text describe consultation, vulnerability, and heritage considerations. | Observed Traditional Owner consultation, representative consent, cultural approval, or community-led decision evidence. | UNVERIFIED outcomes; AUD-019-028, AUD-019-035 |
| Performance/capacity/readability | Configuration defaults and target statements exist. | NFR timings, concurrent capacity, 90% collection timeliness, 80% correlation recall, or 85% reader clarity. | UNVERIFIED; AUD-019-031 |
| This audit | Static source/document/test-assertion inspection and report-text validation only. | Any product test run, import, build, deployment, cloud operation, approval, or completed remediation. | Review-only; every AUD task remains open |

### Future Execution Prerequisites

All commands in remediation tasks are instructions for later authorised implementation/validation, not commands run in this review. Use Python 3.12+ and installed repository dependencies/import paths, synthetic fixtures, and explicitly injected adapters. Existing repository constructors inspect `COSMOS_ENDPOINT`; ensure tests cannot accidentally use production resources. The original "Cosmos" suites currently use memory; introduce explicit local-emulator cases before treating them as integration proof. Installed-artifact cases must not rely on the repository's conftest path additions.

Future Playwright validation requires installed browsers, the working local API/web stack, and approval for its configured server starts and artifact writes. The `AIDR 019` and `spec019_capacity` filters above describe proposed additions to existing test files, not existing tests. A zero-collected/zero-matched run fails the acceptance gate. Future human studies require an agreed sample, instrument, consent, review window, and attributable results; simulated names or generated text are not reviewer approval.

Implementation should proceed through trusted authority/safety/privacy and durable state first; then lifecycle/planning/catalogue; then validated observations, standards, reports, graphs, and orchestration; then UI, telemetry, packaging, and measured acceptance. Some work can be independent, but this audit authorises none of its execution. Do not mark original task checkboxes retrospectively or change original evidence to make the review appear complete.

## Review Summary and Text Validation

- Original tasks: 78 separate rows, all original `[X]` states preserved. Review statuses: 17 IMPLEMENTED, 54 PARTIAL, 4 CONFLICT, 2 MISSING, 1 UNVERIFIED. These statuses do not claim test execution.
- Requirements: 54 separate FR/NFR/SC rows, including FR-007a; all six user stories and their 27 numbered acceptance scenarios; all seven explicit edge cases.
- Documentary obligations: 70 deep-review rows with original `[ ]` states, 16 quality-checklist rows with original `[x]` states, 19 plan gates, ten clarification amendments, three personas, one hypothesis, three scope amendments, thirteen research decisions, seven model definitions, and eight parameter assessments.
- Contracts: 28 endpoint assessments plus role, degradation, performance, and observability obligations for all four contracts.
- Follow-ups: 35 stable, unchecked AUD-019 tasks. The leading risks are unenforced plan authority, unvalidated/falsely validated AI output, contradictory lifecycle/version handling, incomplete privacy protection, disconnected persistence/integration, and non-faithful catalogue/report content.
- Verification boundary: only report-text identifiers/states/coverage, local link existence, source-line bounds, open follow-up integrity, Markdown diagnostics, and scoped read-only revision/text inventory are checked. No tester command in this report is executed. Final validation results are reported separately in the audit completion response; this report does not certify implementation acceptance.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 019 only. Three parallel technical reviews examined planning
authority/lifecycle, M&E safety/privacy, and durable repository integration. The source-completable safety defect was
corrected: indicator-analysis LLM output is now withheld when content-safety validation is unavailable, with an explicit
`content_safety_unavailable` result. The existing lifecycle transition was already aligned with the specification and
required no edit.

Validation: `python -m pytest tests/unit/test_indicator_analysis.py -q` returned `21 passed`.

Remaining open work includes trusted plan authorization, incident-scoped lifecycle/versioning, durable shared state,
catalogue fidelity and repository wiring, small-cohort privacy, report/evidence truthfulness, activation integration,
human review, deployment, performance, and operational evidence.

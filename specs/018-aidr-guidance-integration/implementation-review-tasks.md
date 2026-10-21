# Implementation Review Tasks: AIDR Guidance Integration

**Review date**: 2026-09-11 (requested audit date)  
**Reviewed revision**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (checkout HEAD confirmed)  
**Disposition**: PARTIAL; not implementation-complete or operationally approved.  
**Coverage**: 85 original tasks, all originally `[X]`; 54 FRs, 15 NFRs, 10 SCs; 30 acceptance scenarios and 7 edge cases; 40 open remediation tasks.

## Scope and Evidence Rules

This is an isolated, static, review-only audit under the full [Review Contract](../001-spec-implementation-audit/README.md#L13). Only this report was authored. No branch, commit, index, source, original document, original checkbox, or existing evidence was changed. No other implementation-review report was read. No subagents, product imports, tests, builds, deployments, or cloud queries were run. External identity configuration, deployed state, timing, test execution, human approval, and operational outcomes remain unverified unless explicitly qualified as an authored claim.

The complete local input set was read: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [warning contract](contracts/warning-api.yaml#L1), [AIIMS contract](contracts/aiims-api.yaml#L1), [evacuation contract](contracts/evacuation-api.yaml#L1), [PPRR contract](contracts/pprr-api.yaml#L1), [recovery contract](contracts/recovery-api.yaml#L1), [lessons contract](contracts/lessons-api.yaml#L1), [detailed checklist](checklists/aidr-guidance.md#L1), and [summary checklist](checklists/requirements.md#L1). The six files named `.yaml` contain Markdown contract narratives and examples, not machine-readable OpenAPI schemas.

The two clarification sessions and all appended persona, hypothesis, scope, and authority sections were included. Relevant amendments in the six dependent specifications, the [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1), [hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1), and the complete linked [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1), [post-feature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L1), and [decision record](../028-capstone-alignment/evidence/decision-record.md#L1) were read. These records are authoring evidence, not a new rubric assessment or proof of Spec 018 outcomes.

Applied guidance: [code-review instructions](../../.github/instructions/code-review.instructions.md#L1), their [detailed review checklist](../../.github/instructions/references/code-review-checklists.md#L1), and the applicable [Bicep](../../.github/instructions/bicep-code-best-practices.instructions.md#L1) and [policy-compliance](../../.github/instructions/bicep-policy-compliance.instructions.md#L1) review rules. The `python-fact-grounded-coding`, `cosmosdb-best-practices`, and `ama-rubric-grader` skills were read; execution, cloud discovery, and grading were not performed. Python conclusions below are source-path findings, not runtime reproductions.

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Inspected source supports the full named behavior or authored artifact; no execution success implied. |
| PARTIAL | An inspected implementation exists, but a specified obligation is absent or contradicted. |
| MISSING | The required behavior or artifact was not found within the stated, bounded search and controlling path. |
| CONFLICT | Specification, task, contract, documentation, or implementation disagree and need an explicit decision. |
| UNVERIFIED | Source cannot establish execution, approval, measurement, deployment, or observed outcome. |
| SUPERSEDED | An explicit repository statement documents replacement; this does not certify replacement behavior. |

### Original Guidance and Replacement Checks

The historical handbook location is stale, not proof of missing guidance. The six original publications were located under `docs/corpus/aidr/`; relevant original passages were read before evaluating compliance.

| Evidence | What it establishes, and what it does not |
| --- | --- |
| [AWS Companion, nested model and icons](../../docs/corpus/aidr/warning-system-companion/handbook.md#L141) | Warning level, hazard/location, and action belong together. The complete companion was read; labels alone do not establish useful, approved warnings. |
| [Public Information and Warnings, principles](../../docs/corpus/aidr/public-info-warnings/handbook.md#L663) and [Total Warning System](../../docs/corpus/aidr/public-info-warnings/handbook.md#L805) | Authority, impact, accessibility, and connected interpretation/response are substantive obligations, not field-presence checks. |
| [Incident Management, command/control/coordination](../../docs/corpus/aidr/incident-management/handbook.md#L1340) | Organizational authority and shared situational awareness are distinct from assigning function labels. |
| [Evacuation Planning, inclusive planning](../../docs/corpus/aidr/evacuation-planning/handbook.md#L820) and [authority and five stages](../../docs/corpus/aidr/evacuation-planning/handbook.md#L973) | Group-specific support, lawful authority, and operational responsibilities must survive each stage. |
| [Community Recovery, principles](../../docs/corpus/aidr/community-recovery/handbook.md#L1558) | Community-led, adaptive, long-term recovery requires continuing assessment and participation. |
| [Emergency Management Arrangements, PPRR and shared responsibility](../../docs/corpus/aidr/emergency-management-arrangements/handbook.md#L559) | PPRR phases need not be sequential; continual improvement is an operational process. |
| [Current constitution](../../.specify/memory/constitution.md#L1) | Version 1.2.0 retains AU data-persistence obligations. Its bounded non-AU model-hosting carve-out is not permission to relocate warning, recovery, lessons, audit, or telemetry stores. |
| [Legacy handoff deprecation](../../apps/agents/common/handoffs.py#L1), [replacement graph](../../apps/agents/maf_runtime/workflow/builder.py#L89), [executor dispatch](../../apps/agents/maf_runtime/workflow/executors/_base.py#L177) | Legacy orchestration is explicitly SUPERSEDED in design, with fallback retained. The replacement was inspected; it does not implement recovery/lessons branches merely by replacing handoffs. |
| [Runtime prompt loading](../../apps/agents/maf_runtime/agents/_factory.py#L45), [Communication prompt](../../apps/agents/maf_runtime/agents/communication.yaml#L8), [output parsing](../../apps/agents/maf_runtime/agents/_factory.py#L281) | Prompts are consumed, but output validation uses the declared model. AWS instructions cannot supply fields absent from that model or substitute for deterministic guards. |
| [Typed AIIMS registry](../../apps/agents/common/aiims_registry.py#L1) and [registry tests](../../tests/unit/test_spec032_llm_and_aiims.py#L122) | A later registry replaces bare constants and supports jurisdiction overrides; its defaults still omit Control and do not create per-incident assignments. |
| [Later recovery analysis](../../apps/agents/monitoring/indicator_analysis.py#L16), [planning routes](../../apps/api/app/api/routes/emergency_plans.py#L47), [recovery catalogue](../../apps/api/app/services/recovery_catalogue_service.py#L13), [handover service](../../apps/api/app/services/recovery_handover_service.py#L169) | Related functionality exists. It does not replace the connected phase lifecycle, four-environment longitudinal tracker, or community participation required here. |
| [Later lessons draft](../../apps/api/app/services/simulation/lessons_capture.py#L320) and [full-AAR tests](../../tests/integration/test_lessons_capture_full_aar.py#L1) | A separate, explicitly synthetic exercise-draft path exists. It is not an automatic operational `Lesson` register connection or an observed exercise. |
| [Governance recovery data](../../apps/api/app/services/governance_data_service.py#L491), [warning-compliance data](../../apps/api/app/services/governance_data_service.py#L590), [later recovery web test](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L1) | New panels use catalogue baselines and source trust tiers; these are not the incident tracker values or per-warning compliance results. The later web test checks a seeded economic-outcome evaluator/audit path, not the 21-indicator tracker. |
| [Presentation recovery/NCM scope](../../docs/ama-presentation/AMA_Capstone_QnA.md#L176), [transition diagram narrative](../../docs/architecture/sequence/recovery-transition.md#L12) | These are authored architecture/roadmap statements. They are not runtime traces, formal retirement of Spec 018, or human sign-off. |

### Bounded Search Record

Negative findings refer to these scopes, not to an unrestricted claim about all possible deployments:

| Scope | Search and controlling-path result |
| --- | --- |
| Local feature | All 14 local input files, complete task/spec contents, contracts and checklists. No local implementation evidence/review log or amendment file beyond the appended spec sections was present. |
| Warning execution | Communication app, pipeline, models, approval workflow, builder, compliance helper, API alerts/chain routes, runtime YAML/factory/facade/executors/HITL. Builder callers were confined to helpers/tests; the registered compliance route calls validation, but the publish service does not. |
| API AIDR state | Registered router, AIIMS/PPRR/recovery/lessons services, evacuation routes, state store, authentication/RBAC/tenant middleware, health and dashboard consumers. Searches for the five store symbols found direct dictionary consumers, not durable repository adapters. |
| Agent integration | `apps/agents/**/*.py` for phase, mapping, recovery/lessons handoff, and warning helper symbols; inspected current monitoring/risk/resource/evacuation controllers and the replacement workflow. No phase-driven AIDR mode dispatcher or seven required metric emitters was found. |
| Lessons events and gates | API exercise report generation, simulation lifecycle and lessons modules, plus `.github/workflows/*`, `scripts/**`, and `tools/**` for lesson-reference verification. No operational closure/exercise-to-register subscriber or PR gate was found. |
| Tests and replacements | Named unit/contract/simulation/benchmark tests; integration directory searched for the five AIDR containers, partition and lesson/recovery alternatives. Existing catalogue, workflow, and exercise tests do not cover CRUD/partition/TTL for these five stores. EDXL endpoint assertions exist inside the warning contract test, despite the absent historical EDXL test filename. |
| UI and doctrine | Web source searched for incident AIIMS/PPRR/recovery endpoint consumers; existing governance panels and their data service were followed. Six original handbooks were located and consulted at their new paths. |
| Review and outcome records | Local checklists, linked feature-028 records, referenced persona material, and bounded `docs/**/*.md` / `weblogs/**/*.md` searches for Spec 018. No Spec-018-specific execution report or approval was located. Filename search also found no relocated HYP-016 stub. |

## Priority-Ordered Findings and Remediation

All steps below are future work, not authorization to implement or run them during this audit. `V-*` identifiers refer to the command/prerequisite catalogue later in this report. Acceptance requires developer changes plus independent tester evidence; authored tests alone do not close a task.

### P1: Security, Life Safety, and Connected Enforcement

- [ ] AUD-018-001 Enforce authenticated authority on every AIDR mutation
  - **Affected**: T019, T028, T039, T043, T051, T063, T065; FR-004, FR-017, FR-019, FR-023, FR-038, FR-041; IC-unavailable and contradictory-lesson edges; all six contracts' Auth obligations. **Status**: PARTIAL.
  - **Expected / actual / impact**: Authority must come from verified identity and incident permission. [Bearer middleware](../../apps/api/app/middleware/entra_auth.py#L37) and [RBAC middleware](../../apps/api/app/middleware/rbac_check.py#L32) protect other prefixes, while [AIIMS inputs](../../apps/api/app/api/routes/aiims.py#L19) and [lesson resolution](../../apps/api/app/api/routes/lessons.py#L40) trust supplied actor strings. External EasyAuth policy is UNVERIFIED; the application itself does not establish authorization for these mutations.
  - **Owner / developer**: Extend the existing middleware/dependency policy to the AIDR routes and Communication approval app. Derive author/approver IDs from verified claims; authorize IC, delegated Control, evacuation, recovery, and QA actions separately. Preserve a deliberately public, redacted recovery read surface without making mutations public.
  - **Tester positive**: Extend [AIIMS contract tests](../../tests/contract/test_aiims_contract.py#L1) and the other contract fixtures with a trusted IC and explicitly delegated principal; assert actor provenance comes from claims.
  - **Tester negative**: Anonymous, expired, wrong-role, and spoofed body-role requests must fail without state/timeline mutation.
  - **Tester edge**: Expired delegation, missing identity service, and community read-only access must fail closed for writes while preserving permitted reads.
  - **Future check / prerequisites**: V-AUTH and V-CONTRACT, with isolated identity/JWKS fixtures, never a real operator token.
  - **Dependencies / acceptance**: None; all write paths require verified, incident-scoped authority and authorization failures are auditable.

- [ ] AUD-018-002 Bind object lookup to incident, tenant, and authorized scope
  - **Affected**: T027, T028, T039, T042, T051, T063; FR-013, FR-014, FR-021, FR-022, FR-027, FR-036, FR-040; independent-incident edge and spec-007 dependency. **Status**: PARTIAL.
  - **Expected / actual / impact**: [AIIMS update](../../apps/api/app/api/routes/aiims.py#L62) checks incident and assignment existence separately. [Evacuation lookup](../../apps/api/app/api/routes/evacuation.py#L75) retrieves any stage ID, and transition writes its event to the URL incident. [Global stores](../../apps/api/app/services/state_store.py#L16) carry no tenant key. An existing incident can therefore be paired with another incident's object in the inspected path.
  - **Owner / developer**: Resolve objects using authenticated tenant plus incident ownership; reject mismatches before reading or mutating. Apply the same boundary to warning chains, recovery indicators, lesson/exercise references, and non-incident contexts. Do not rely on [tenant middleware's context annotation](../../apps/api/app/middleware/tenant_middleware.py#L20) as authorization.
  - **Tester positive**: Use two `_seed_incident` fixtures in [evacuation contract tests](../../tests/contract/test_evacuation_contract.py#L23); same-scope requests succeed.
  - **Tester negative**: Cross-incident assignment/stage IDs and cross-tenant lesson/alert references return the approved 403/404 policy and leave both incidents unchanged.
  - **Tester edge**: Identical local IDs in simulation and live tenants, removed membership, and replayed requests cannot alias stores or contaminate timelines.
  - **Future check / prerequisites**: V-AUTH and V-STORE, with two tenants and independently recorded before/after snapshots.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005; no successful cross-scope lookup or mutation, including audit destinations.

- [ ] AUD-018-003 Make publication depend on approval and final validated content
  - **Affected**: T019, T020, T022, T025; FR-001, FR-004, FR-005, FR-006, FR-007; SC-001, SC-006; US1 and NN-1. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Publish eligibility](../../apps/api/app/services/public_alert_service.py#L48) accepts `pending_approval`; [publish](../../apps/api/app/services/public_alert_service.py#L66) stamps a caller-supplied persona without inspecting an approval or AWS/content-safety result. Template mutation is separate. The later [HITL gate](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L165) does not guard this registered route.
  - **Owner / developer**: Centralize a non-bypassable publish/deliver precondition using a persisted approval for the exact content/version, authorized principal, and passing applicable safety/compliance checks. Editing approved content must invalidate approval. Keep simulation delivery suppression and never convert an escalation into approval.
  - **Tester positive**: Extend [warning contract fixtures](../../tests/contract/test_warning_contract.py#L37) to approve a valid version and publish it once with provenance.
  - **Tester negative**: Pending, rejected, expired, unsafe, noncompliant, or altered-after-approval alerts cannot publish or deliver.
  - **Tester edge**: Concurrent publish, replayed approval, all-clear, correction, and simulation requests retain exactly-once state and the correct approval association.
  - **Future check / prerequisites**: V-WARNING and V-AUTH; recording channel adapters only.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005, AUD-018-006, AUD-018-007; every release path proves approval of the final validated version.

- [ ] AUD-018-004 Fail closed on under-aggregated recovery data
  - **Affected**: T009, T050, T051, T052, T055; NFR-014; FR-032, FR-034, FR-037; R-012 and CHK070. **Status**: PARTIAL.
  - **Expected / actual / impact**: The [model validator](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L93) and [service update](../../apps/api/app/services/recovery_service.py#L109) check low population only when supplied. Classification defaults to public in direct model construction; only health/employment slots default sensitive. [Tests explicitly permit public health data covering three people](../../tests/unit/test_domain_models_aidr.py#L339). The store/update path uses unchecked copies and represents no LGA granularity constraint.
  - **Owner / developer**: Distinguish empty slots from populated observations; require valid coverage >=10 for protected community aggregates, derive minimum classification from indicator/source, and enforce geographic granularity. Revalidate all writes/imports/exports and redact sensitive content independently of a caller's classification label. Obtain privacy-owner decisions for classification and retention; do not claim legal compliance from a count alone.
  - **Tester positive**: Extend [recovery contract tests](../../tests/contract/test_recovery_contract.py#L1) and model fixtures with valid ten-person LGA aggregates.
  - **Tester negative**: Reject populated sensitive records with null, omitted, zero, nine, or forged classification/coverage; check batch and non-API writes.
  - **Tester edge**: Empty slots, exactly ten people, overlapping small cohorts, social-issues indicators, and exports must not expose identifiable data.
  - **Future check / prerequisites**: V-RECOVERY; synthetic aggregate fixtures and a documented privacy decision.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-002; every populated write and public projection applies the approved privacy policy.

- [ ] AUD-018-005 Connect durable state and explicit degraded-mode recovery
  - **Affected**: T002, T003, T022, T031, T040, T048, T056, T067, T069, T082; NFR-011, NFR-012, NFR-015; FR-036, FR-040; R-002, R-013. **Status**: MISSING for the five API stores' durable integration.
  - **Expected / actual / impact**: [Five Cosmos containers are authored](../../infra/modules/recovery-lessons.bicep#L18), but [AIDR services use process dictionaries](../../apps/api/app/services/state_store.py#L26). No adapter/flush consumer was found for those symbols. [Warning persistence logs and continues on failure](../../apps/agents/communication/pipeline.py#L542). Restart, multiple workers, and outages can lose or diverge safety and longitudinal records.
  - **Owner / developer**: Add repository injection to the existing services, preserving incident/context partition contracts and tenant authorization. Define a storage-safe exercise partition representation without fabricating a real incident. Add bounded local queues, append-before-ack audit, idempotent replay, concurrency tokens, and truthful degraded/last-known responses. Keep phase state unchanged until a queued transition is safely applied.
  - **Tester positive**: Use existing API fixtures and the proposed five-container integration suite in AUD-018-035; write through controllers, restart, and read through a separate instance.
  - **Tester negative**: Timeout/429/unavailable stores must not silently acknowledge durable completion, lose buffered writes, or block incident operations on lessons failure.
  - **Tester edge**: Crash during flush, duplicate replay, two writers, full buffer, and exercise-only lessons preserve provenance and deterministic recovery.
  - **Future check / prerequisites**: V-STORE; disposable local stores/emulator and recording audit sink, with cloud access separately authorized.
  - **Dependencies / acceptance**: AUD-018-001; define scoped repository interfaces here for AUD-018-002 to enforce. Demonstrate survival, isolation, replay, and each R-002 failure mode, not just dictionary retention.

- [ ] AUD-018-006 Connect AWS construction and validation to both runtime paths
  - **Affected**: T005, T017, T018, T019, T020, T060; FR-001, FR-002, FR-003, FR-048; SC-001; US1. **Status**: PARTIAL.
  - **Expected / actual / impact**: The [AWS builder](../../apps/agents/communication/warning_builder.py#L60) constructs the extended domain model, but the [processing pipeline](../../apps/agents/communication/pipeline.py#L455) builds [the separate Communication model](../../apps/agents/communication/models.py#L250) without AWS fields. The [MAF definition](../../apps/agents/maf_runtime/agents/communication.yaml#L39) selects the same model, and [legacy facade](../../apps/agents/maf_runtime/agents/communication_agent.py#L31) returns a minimal draft. Request DTOs alone do not connect these paths.
  - **Owner / developer**: Preserve both existing lifecycles through an explicit adapter or compatible model extension. Carry editorially selected tier, hazard, location, action, chain, languages, and accessibility through generation, persistence, approval, and delivery. Invoke deterministic validation on both legacy and MAF outputs; make all-clear requests representable without a required tier.
  - **Tester positive**: Extend [warning tests](../../tests/contract/test_warning_contract.py#L1) with real pipeline/facade calls and recording LLM/store boundaries for each tier.
  - **Tester negative**: Missing location/action/icon, unsupported output fields, and a prompt-only AWS claim must not produce a publishable result.
  - **Tester edge**: Legacy non-AWS data, template fallback, all-clear, and mode switching retain compatible fields and approval state.
  - **Future check / prerequisites**: V-WARNING; both runtime modes configured in isolated fixtures.
  - **Dependencies / acceptance**: AUD-018-007, AUD-018-009, AUD-018-017; every public warning construction path yields validated AWS data for the publication guard, not merely an authored prompt.

- [ ] AUD-018-007 Replace automatic principle passes with evidence-based checks
  - **Affected**: T014, T017, T020, T025, T026, T060; FR-006; SC-006; CHK006, CHK011, CHK012, CHK072. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Builder defaults all ten principles to true](../../apps/agents/communication/warning_builder.py#L56). [Structural validation](../../apps/agents/common/warning_compliance.py#L70) equates tier presence with life safety/risk scaling, approval-mode text with authority, and content count with broader context; supplied analysis can pass through. All-clear is structurally unable to pass `risk_scaled`. [Governance percentages](../../apps/api/app/services/governance_data_service.py#L590) measure source trust, not warnings.
  - **Owner / developer**: Operationalize each principle using [original guidance](../../docs/corpus/aidr/public-info-warnings/handbook.md#L663), distinguishing deterministic checks, content assessment, and required human review. Record evidence, checker version and outcome; define approved all-clear applicability. Set individual validity flags accurately and never accept an untrusted all-true map as proof.
  - **Tester positive**: Extend `compliant_alert` in [warning-compliance tests](../../tests/unit/test_warning_compliance.py#L17) with authority, impact, targeting, accessibility and context evidence.
  - **Tester negative**: Ten structurally complete but misleading/unsupported warnings must fail the relevant principles; fabricated analysis and missing icons must not leave misleading validity flags.
  - **Tester edge**: Valid all-clear, stale hazard evidence, unavailable content analysis, and partial translation require explicit outcomes rather than automatic passes.
  - **Future check / prerequisites**: V-WARNING; reviewer-approved per-principle positive/negative fixtures, no live public output.
  - **Dependencies / acceptance**: AUD-018-038; define and test the compliance contract before runtime integration. All ten decisions are explainable and the validator rejects noncompliance; publication integration is verified by AUD-018-003.

- [ ] AUD-018-008 Implement the tier-aware IC delegation deadline
  - **Affected**: T019, T029, T031; clarification sessions, IC-unavailable edge; warning-timeout authority amendment; US1-AS3. **Status**: PARTIAL.
  - **Expected / actual / impact**: Emergency warnings require five-minute delegation; lower warning tiers fifteen minutes; non-warning approvals keep their default. [ApprovalWorkflow](../../apps/agents/communication/approval.py#L91) uses one configuration timeout and [synthetic commander-level identifiers](../../apps/agents/communication/approval.py#L108). The [MAF gate explicitly leaves those mechanics unchanged](../../apps/agents/maf_runtime/workflow/hitl_request_port.py#L39). The legacy pipeline's [approval stage only emits audit/event metadata](../../apps/agents/communication/pipeline.py#L575).
  - **Owner / developer**: Start a persisted deadline at a defined submission event, select it by warning tier, and resolve IC -> deputy -> authorized Control successor from incident assignments. Connect request publication and timer startup; persist/audit actual delegation identities and exhaustion. Never auto-approve.
  - **Tester positive**: Extend [AIIMS escalation tests](../../tests/integration/test_aiims_escalation.py#L1) and warning tests with a warning-specific chain; keep the existing Ops-conflict timeout behavior distinct.
  - **Tester negative**: No early escalation, no unauthorized successor, and no automatic release after chain exhaustion.
  - **Tester edge**: Exact 5/15-minute boundaries, restart, concurrent approval at timeout, configuration override, and non-warning approvals retain correct deadlines.
  - **Future check / prerequisites**: V-WARNING and V-AUTH; controllable clock and fake queues, not sleeps or real messaging.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005, AUD-018-014; durable, audited delegation follows the actual authorized chain.

- [ ] AUD-018-009 Enforce hazard-specific warning chains, tier changes, and closure
  - **Affected**: T005, T017, T019, T023; FR-004, FR-005, FR-048; multi-hazard/tier-skip edges; R-004; US1-AS2, US1-AS3, US1-AS4. **Status**: PARTIAL.
  - **Expected / actual / impact**: [De-escalation/all-clear builders](../../apps/agents/communication/warning_builder.py#L117) accept unchecked predecessor IDs; [supersede](../../apps/api/app/services/public_alert_service.py#L74) only marks status. [Traversal](../../apps/agents/communication/warning_builder.py#L183) walks ancestors, not successors, and chain-position traversal has no cycle guard. Skip checks run only when justification is supplied and do not establish sudden-onset hazard identity.
  - **Owner / developer**: Validate published predecessor, same incident/tenant/hazard/geography, current-head uniqueness, acyclicity and monotonic issue order. Make supersession atomic; preserve independent overlapping hazards even when both icons are `other`. Require authorized tier-skip rationale/hazard, verify de-escalation direction, and permit terminal all-clear only for an authorized resolved threat. Return the complete ordered chain from any member.
  - **Tester positive**: Extend [chain fixtures](../../tests/contract/test_warning_contract.py#L68) through escalation, downgrade, and all-clear with exact status/timestamp assertions.
  - **Tester negative**: Reject missing/draft/cross-hazard predecessor, branches, self-links, cycles, invalid downgrade, and unjustified sudden-onset skip.
  - **Tester edge**: Simultaneous overlapping hazards, racing successors, chain reads from the oldest member, and correction/retraction policy are explicit.
  - **Future check / prerequisites**: V-WARNING; two hazards, controlled clock, persisted approvals.
  - **Dependencies / acceptance**: AUD-018-002, AUD-018-005, AUD-018-038; one unambiguous active head per hazard scope and auditable authorized closure, exposing validated chain operations for the publication guard.

- [ ] AUD-018-010 Integrate the complete vulnerable-population policy
  - **Affected**: T021, T036, T037, T038, T060, T085; FR-007, FR-021; SC-009; CHK007, CHK013, CHK037, CHK054, CHK096. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Canonical constants](../../apps/agents/common/vulnerable_populations.py#L10) list seven groups but omit explicit Aboriginal/TSI, homelessness, tourist/transient, and institutional-care categories. [Communication categories](../../apps/agents/communication/models.py#L149) use a different four-category set. The helper is not connected to the stage or warning controllers; a translation/accessibility label does not prove an accommodation was delivered.
  - **Owner / developer**: Reconcile all Constitution VI-C groups plus the three handbook extensions, with documented aliases for existing data. Apply group-specific warning formats, language QA, transport priority, shelter/welfare, medical continuity, assistance animals and return support. Reuse existing translation and segmentation functionality instead of replacing it with labels.
  - **Tester positive**: Extend [domain tests](../../tests/unit/test_domain_models_aidr.py#L1), warning fixtures, and [evacuation tests](../../tests/unit/test_evacuation_stages.py#L1) with each group and verifiable accommodations at all five stages.
  - **Tester negative**: Unknown aliases, untranslated CALD content, inaccessible shelter, missing medical support, or exclusion of assistance animals must surface unmet needs.
  - **Tester edge**: Intersecting groups, unavailable translations, no transport, and partial evacuation preserve priority and visible unresolved support.
  - **Future check / prerequisites**: V-WARNING, V-EVAC, V-UI; synthetic demographics and qualified language/accessibility reviewers.
  - **Dependencies / acceptance**: AUD-018-038; establish canonical groups and accommodation policy first, then integrate through the warning and stage adapters. All required groups are covered by connected actions and independent assertions.

- [ ] AUD-018-011 Gate evacuation transitions on stage-specific safety
  - **Affected**: T008, T034, T036, T039; FR-018, FR-019, FR-022, FR-023; SC-003. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Transition logic](../../apps/agents/evacuation/stages.py#L37) checks only allowed stage names then uses `model_copy`; it never requires safe-return certification or completion. [Update routes](../../apps/api/app/api/routes/evacuation.py#L161) accept unbounded counts/rates without stage validation. [Full lifecycle test](../../tests/unit/test_evacuation_stages.py#L215) reaches completed with no operational safety evidence.
  - **Owner / developer**: Require complete Decision metadata and validated stage outputs before advancement. Gate Return on authorized certification of current conditions and Completed on documented return outcomes. Enforce nonnegative counts, moved <= total, occupancy/capacity policy, rate bounds, correct current stage, and revalidation after mutation.
  - **Tester positive**: Extend `decision_stage` and contract fixtures with all stage evidence, phased return and current certification.
  - **Tester negative**: Unsafe/stale certification, missing authority/type/scope, negative counts, excess occupancy without an explicit exception, and out-of-stage updates cannot advance or mutate.
  - **Tester edge**: Partial return, renewed hazard, withdrawn certification, zero population and concurrent transition are handled explicitly.
  - **Future check / prerequisites**: V-EVAC; test certifiers and controlled hazard observations.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-002, AUD-018-005; the unsafe lifecycle currently permitted is rejected and every accepted stage has evidence.

- [ ] AUD-018-012 Connect the five stages to evacuation operations
  - **Affected**: T035, T036, T037, T038, T039; FR-018, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025; US3. **Status**: PARTIAL.
  - **Expected / actual / impact**: [API transitions](../../apps/api/app/api/routes/evacuation.py#L103) change a record and timeline only. They do not call Communication, allocate transport, track shelters individually, or schedule shelter-in-place monitoring. [Evacuation agent](../../apps/agents/evacuation/agent.py#L123) continues to use its separate zone-planning pipeline. Request DTOs exist in routes, not a complete stage-aware agent model/response contract.
  - **Owner / developer**: Add an orchestration adapter around existing zone plans, routes, transport and stage records. Warning must produce approved linked alerts with timeframe/routes/destinations; Withdrawal must update movement and priority allocation; Shelter must record per-location welfare/capacity; Return must track phased progress. Schedule shelter-in-place reassessment and distinguish immediate from pre-warned timing without bypassing authority.
  - **Tester positive**: Extend [cyclone simulation](../../tests/simulation/test_aidr_scenarios.py#L67) with recording Communication/transport/shelter clients and assert their actual invocation and outputs.
  - **Tester negative**: Missing/failed warning, unavailable route, full shelter, and unsafe return cannot be disguised by moving the stage label.
  - **Tester edge**: Directed/recommended/self-initiated and total/partial/phased cases, immediate hazards, and shelter-in-place reevaluation preserve existing zone functionality.
  - **Future check / prerequisites**: V-EVAC and V-SCENARIO; existing plan fixtures and fake external adapters, not mocked domain transitions.
  - **Dependencies / acceptance**: AUD-018-006, AUD-018-010, AUD-018-011; each of the five stages produces the required operational outputs.

- [ ] AUD-018-013 Make blocked-route re-entry perform a real replan
  - **Affected**: T034, T036, T037, T040; SC-003; evacuation-abandonment edge and preserved spec-009 <=15s replan target. **Status**: PARTIAL; shared spec-009 risk independently required by this spec.
  - **Expected / actual / impact**: [Replan controller](../../apps/agents/evacuation/agent.py#L127) recognizes triggers, but route/transport/version/persistence work is placeholder code and compares the current plan with itself. It does not reactivate Decision in the stage store. [Return-to-Decision is permitted but not counted as re-entry](../../packages/domain/src/domain/models/evacuation_stage.py#L29).
  - **Owner / developer**: Connect trigger evaluation to recalculation with the changed road graph, alternative shelter-in-place assessment, validated new plan/version, Decision re-entry, audit and persistence. Count every permitted active-stage re-entry, including Return. Preserve existing scope and priority rules; do not simply emit `material_change=True`.
  - **Tester positive**: Extend [evacuation-stage tests](../../tests/unit/test_evacuation_stages.py#L194) and the cyclone simulation with an impassable active route; assert changed routing or explicit shelter-in-place output plus a new audited Decision.
  - **Tester negative**: A trigger with unchanged plan content cannot be reported as a completed replan; stale/unauthorized updates cannot replace the plan.
  - **Tester edge**: No safe route, multiple closures, Return re-entry, rate limiting of life-safety changes, and partial evacuation remain visible.
  - **Future check / prerequisites**: V-EVAC and V-PERF; deterministic road graph/clock and the original <=15s target.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-011, AUD-018-012; inspectable before/after plans, correct re-entry count and timeline, no placeholder success.

- [ ] AUD-018-014 Bootstrap complete incident AIIMS assignments and enforce coverage
  - **Affected**: T007, T012, T027, T029, T030, T031, T033; FR-013, FR-014, FR-015, FR-016, FR-049; SC-002. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Defaults cover five functions](../../apps/agents/common/aiims_mapping.py#L16). [Level changes](../../apps/api/app/services/aiims_service.py#L99) mutate the level without calling [coverage validation](../../apps/api/app/services/aiims_service.py#L155). No incident-start consumer consults framework applicability and creates role assignments. Registry and coverage tests demonstrate helpers, not startup enforcement.
  - **Owner / developer**: Hook authoritative incident creation/start to framework applicability, role definitions, authorized Control representation, and idempotent per-agent assignments. Enforce the approved coverage policy before escalation and keep any fallback visible as stale. Resolve the SC-002 all-active-incidents versus N-001 Level-3-only policy conflict rather than silently weakening either.
  - **Tester positive**: Extend [AIIMS contract fixtures](../../tests/contract/test_aiims_contract.py#L23) to start an incident through its controller and obtain the complete six-function structure.
  - **Tester negative**: Missing Control, invalid framework, duplicate active assignment or incomplete Level 3 coverage prevents the relevant operation.
  - **Tester edge**: Five available agents plus human IC, degraded role service, duplicate start and simultaneous incidents preserve identity and exactly-one-function constraints.
  - **Future check / prerequisites**: V-AIIMS; framework/jurisdiction fixtures and an approved coverage decision.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005, AUD-018-038; source and tests demonstrate bootstrap and guarded escalation, not only manual assignment calls.

- [ ] AUD-018-015 Preserve assignment periods and validate reassignment
  - **Affected**: T007, T027, T028; FR-013, FR-049; CHK021. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Assignment update](../../apps/api/app/services/aiims_service.py#L73) mutates a function without validating the new string or retaining the prior function's assignment period; `is_active=True` has no reactivation implementation. Caller notes and reassignment authority/history are not recorded.
  - **Owner / developer**: Use typed validated updates, close the previous assignment period and create a traceable replacement, authorize/audit reassignment, and define reactivation behavior. Check duplicate active assignments and coverage atomically with changes; preserve delegation lineage.
  - **Tester positive**: Extend [AIIMS contract tests](../../tests/contract/test_aiims_contract.py#L1) with reassignment/deactivation and assert both historical and current periods.
  - **Tester negative**: Unknown functions, overlapping active periods and unauthorized reassignment fail without mutation.
  - **Tester edge**: Deactivate the last Control role, repeat a reassignment, reactivate, and change roles at the same timestamp; maintain the approved coverage policy.
  - **Future check / prerequisites**: V-AIIMS; persisted assignments and a controlled clock.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005, AUD-018-014; role history can reconstruct each function holder at any reviewed time.

- [ ] AUD-018-016 Enforce Command/Control/Coordination and resolve NCM readiness
  - **Affected**: T029, T030, T074; FR-016, FR-017; US2-AS2, US2-AS3, US2-AS4; CHK025, CHK026, CHK027. **Status**: PARTIAL for communication boundaries; CONFLICT for claimed NCM scope.
  - **Expected / actual / impact**: [Handoffs](../../apps/agents/common/handoffs.py#L26) and [the replacement graph](../../apps/agents/maf_runtime/workflow/builder.py#L89) pass agent payloads without organizational command/coordination policy. [COP assembly](../../apps/api/app/services/dashboard_service.py#L48) has no relationship structure. [Presentation B19](../../docs/ama-presentation/AMA_Capstone_QnA.md#L180) calls NCM mandatory but unbuilt, while US2-AS3 requires support.
  - **Owner / developer**: Model controlling entity, participating agency and authorized decision scope; enforce intra-entity commands versus cross-entity requests at the actual dispatch boundary. Expose these relationships in COP. Agree NCM exchange data, trigger, access and readiness criteria with the owner; implement the agreed adapter or obtain an explicit amendment, not a presentation-only deferral.
  - **Tester positive**: Extend [AIIMS tests](../../tests/contract/test_aiims_contract.py#L1) and scenario tests with two agencies and distinct command/coordination links.
  - **Tester negative**: A cross-agency command without authority must be rejected or converted into an explicit authorized request, never silently dispatched.
  - **Tester edge**: Common controller, agency withdrawal and NCM unavailability retain local operations and honest readiness state.
  - **Future check / prerequisites**: V-AIIMS and V-UI; approved agency/NCM contract, stub external exchange only.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-014, AUD-018-038; establish the relationship contract consumed by the COP task. All four FR-017 acceptance clauses and the approved Level 3 scope are demonstrable.

- [ ] AUD-018-017 Align runtime prompts with the independent severity scales
  - **Affected**: T004, T019, T058, T059, T071; FR-015, FR-044, FR-050, FR-051; second clarification session. **Status**: CONFLICT.
  - **Expected / actual / impact**: Spec 018 preserves triage severity, `low/moderate/high/critical` risk severity, public AWS tiers, and AIIMS levels 1/2/3 as independent concepts. [Risk runtime prompt](../../apps/agents/maf_runtime/agents/risk_assessment.yaml#L7) requests levels 0/1/2/3 and five different severity buckets. [Factory](../../apps/agents/maf_runtime/agents/_factory.py#L90) actually supplies this prompt to the agent.
  - **Owner / developer**: Reconcile all five operational definitions with canonical models and the clarified scales. Validate structured model output against the correct scale and retain IC editorial choice for warnings. Do not introduce an automatic risk-to-warning or incident-status-to-phase mapping as a shortcut.
  - **Tester positive**: Add schema/definition assertions beside [domain model tests](../../tests/unit/test_domain_models_aidr.py#L35), including independent values on one incident.
  - **Tester negative**: Level 0, severe/catastrophic substituted for the required risk scale, and automatic warning-tier coercion must be rejected or explicitly mapped under an approved different contract.
  - **Tester edge**: Legacy records, all added hazards and low-confidence/high-impact assessments preserve independence.
  - **Future check / prerequisites**: V-MODELS and V-WARNING; canned MAF responses, no model inference.
  - **Dependencies / acceptance**: AUD-018-038; consumed prompts, parsing, and accepted values agree with the normative scales before warning-path integration.

- [ ] AUD-018-018 Implement managed, recurring PPRR phases rather than a terminal enum
  - **Affected**: T013, T042, T046, T047, T048; FR-026, FR-030, FR-031, FR-053; SC-004; US4-AS3, US4-AS4. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Transition map](../../apps/agents/common/pprr_lifecycle.py#L10) makes Recovery terminal. [Service](../../apps/api/app/services/pprr_service.py#L30) overwrites one phase, defaults legacy null to Prevention and records overlap only in an event; [readback](../../apps/api/app/services/pprr_service.py#L83) omits active overlap state. This contradicts [non-sequential doctrine](../../docs/corpus/aidr/emergency-management-arrangements/handbook.md#L576) and does not activate overlapping work.
  - **Owner / developer**: Agree safe recurring-transition/exit criteria, persist active phases and overlap start/end/authorizer, and retire prior work only after a managed handover. Treat unknown legacy phase explicitly. Connect overlap to agent scheduling and preserve current phase on failure; do not implement unrestricted arbitrary switching.
  - **Tester positive**: Extend [PPRR tests](../../tests/unit/test_pprr_lifecycle.py#L1) and contracts with Response/Recovery overlap, readback and authorized completion.
  - **Tester negative**: Invalid/unauthorized transitions, expired or contradictory overlap metadata, and failed persistence cannot abruptly change operations.
  - **Tester edge**: Secondary disaster during recovery, two incidents in different phases, legacy null, repeat transition and overlap expiry retain clear state/history.
  - **Future check / prerequisites**: V-PPRR and V-SCENARIO; approved transition policy and controlled clock.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005, AUD-018-031, AUD-018-038; provide managed active-phase state for downstream dispatch. The platform represents overlapping phases and permitted recurrence; agent activation is verified by AUD-018-020.

### P2: Capability Completion, Contracts, and Evidence

- [ ] AUD-018-019 Complete the non-incident context-to-Response transition
  - **Affected**: T011, T042, T043; FR-050, FR-053; R-001; CHK045, CHK046, CHK095. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Context creation](../../apps/api/app/services/pprr_service.py#L99) accepts any reference ID. [Transition](../../apps/api/app/services/pprr_service.py#L124) deactivates the context but never sets the target incident to Response or records rationale/authority. The [contract](contracts/pprr-api.yaml#L95) promises those effects; task/runtime use PUT while that contract uses POST.
  - **Owner / developer**: Validate region/scenario ownership and existence, carry authorized rationale, and atomically link/deactivate context, enter incident Response and append the transition record. Resolve the verb mismatch in the contract decision under AUD-018-032; preserve non-incident contexts without phantom incidents.
  - **Tester positive**: Extend [PPRR contract tests](../../tests/contract/test_pprr_contract.py#L85) from a valid preparedness context to an incident and assert both records plus timeline.
  - **Tester negative**: Unknown/cross-scope reference, closed context and invalid target incident fail without partial linkage.
  - **Tester edge**: Retry after a partial failure and two concurrent transitions yield one link and consistent Response state.
  - **Future check / prerequisites**: V-PPRR and V-STORE; real local jurisdiction/scenario fixtures.
  - **Dependencies / acceptance**: AUD-018-002, AUD-018-005, AUD-018-018; no closed context can falsely imply a Response transition that never happened.

- [ ] AUD-018-020 Dispatch phase-appropriate capabilities and concurrent recovery agents
  - **Affected**: T044, T045, T046, T047, T054, T072; FR-028, FR-029, FR-030, FR-035, FR-045; US4. **Status**: PARTIAL.
  - **Expected / actual / impact**: Phase designation does not invoke phase-specific work. [Resource pipeline](../../apps/agents/resource_allocation/pipeline.py#L91) has no recovery-mode dispatch; related [planning routes](../../apps/api/app/api/routes/emergency_plans.py#L47), simulation and [indicator analysis](../../apps/agents/monitoring/indicator_analysis.py#L22) exist separately. Search of agent phase consumers found helpers, not operational mode selection.
  - **Owner / developer**: Connect Prevention risk/mitigation/risk-reduction outputs, Preparedness rehearsal/readiness/pre-positioning/warning tests, and Response-onset recovery planning to the approved phase state. Configure existing Resource, Communication and Monitoring agents for reconstruction, recovery updates and regressions in parallel with response. Preserve life-safety priority and spec-011 cross-incident tie-breaking.
  - **Tester positive**: Extend [flood lifecycle simulation](../../tests/simulation/test_aidr_scenarios.py#L107) with real dispatcher calls and recording external adapters for each phase.
  - **Tester negative**: A phase-label-only update must not satisfy capability completion; missing prerequisites or resource contention must surface unresolved work.
  - **Tester edge**: Response and recovery for different incidents, shared inventory, cancelled exercise and return to response do not disable safety-critical work.
  - **Future check / prerequisites**: V-PPRR and V-SCENARIO; seeded scenarios, inventory and preparedness context.
  - **Dependencies / acceptance**: AUD-018-018, AUD-018-019; implement phase-aware agent operations before adding graph routing. Required phase outputs and concurrent agent calls are asserted.

- [ ] AUD-018-021 Add longitudinal recovery observations, regression response, and staleness
  - **Affected**: T009, T050, T051, T054, T056; FR-032, FR-036; NFR-012; recovery-regression edge. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Initialization](../../apps/api/app/services/recovery_service.py#L27) creates all 21 slots with no baseline. [Update](../../apps/api/app/services/recovery_service.py#L83) replaces the latest indicator; APIs cannot set baseline/target/unit/source identity. Regression compares only against baseline, writes a generic cause, and triggers no reassessment. [Dashboard](../../apps/api/app/services/recovery_service.py#L58) has no staleness signal or history.
  - **Owner / developer**: Preserve timestamped observations, baselines, targets, direction-of-improvement, provenance, and actual causes. Define indicator-specific measurement and update frequency; expose historical and last-known views. Detect regression against approved criteria, request reassessment, and distinguish seven-day recovery staleness from the warning-linked 24-hour SLA.
  - **Tester positive**: Extend [recovery contract fixtures](../../tests/contract/test_recovery_contract.py#L35) with dated samples across all four environments and a genuine regression/reassessment.
  - **Tester negative**: Missing baseline must not imply healthy improvement; invalid/future timestamps, overwritten history and fabricated causes fail or remain explicitly unknown.
  - **Tester edge**: Higher-is-worse metrics, secondary disaster, out-of-order imports, months/years of observations and unavailable sources retain usable last-known values with staleness.
  - **Future check / prerequisites**: V-RECOVERY and V-STORE; approved measurement definitions and controllable time.
  - **Dependencies / acceptance**: AUD-018-004, AUD-018-005; longitudinal queries and regressions are reproducible from retained observations.

- [ ] AUD-018-022 Deliver principle-linked, community-led, safety-checked recovery
  - **Affected**: T050, T051, T054, T055; FR-033, FR-034, FR-037; NFR-013; US5-AS2, US5-AS3. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Recovery initialization route](../../apps/api/app/api/routes/recovery.py#L43) ignores the documented principles/community-input body. The model permits empty principles. Later [analysis enrichment](../../apps/agents/monitoring/indicator_analysis.py#L80) returns LLM text with `not_validated` when its validator is absent; [the test expects that bypass](../../tests/unit/test_indicator_analysis.py#L201). Default monitoring wiring is rule-based, not proof of a safe configured LLM path.
  - **Owner / developer**: Accept and validate community input/local priorities, map every recommendation to applicable principles and evidence, and provide an accountable response loop. Make safety validation mandatory for generated recovery/public content; unavailable or failed validation must withhold it or use an approved fallback. Require human review before community dissemination.
  - **Tester positive**: Extend [indicator-analysis tests](../../tests/unit/test_indicator_analysis.py#L1) and recovery contracts with reviewed community needs and principle-linked recommendations.
  - **Tester negative**: Missing principles, unauthorized input, absent/failing safety dependency and unsafe generated text cannot be presented as validated public content.
  - **Tester edge**: Conflicting community priorities, no data, unavailable LLM and multilingual updates preserve explanation, privacy and review status.
  - **Future check / prerequisites**: V-RECOVERY and V-UI; reviewer-approved content fixtures and recording safety client.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-004, AUD-018-020; participation and principle alignment are visible and no generated public path bypasses validation/review.

- [ ] AUD-018-023 Connect COP and community views to actual AIDR state
  - **Affected**: T028, T030, T043, T051, T056, T060; FR-014, FR-016, FR-027, FR-032, FR-037; SC-002, SC-005; multi-hazard overlap edge. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Incident dashboard](../../apps/api/app/services/dashboard_service.py#L48) omits level, AIIMS and phase. [Governance recovery](../../apps/api/app/services/governance_data_service.py#L491) reports catalogue baselines, and [warning percentages](../../apps/api/app/services/governance_data_service.py#L590) are based on source trust. Existing [recovery](../../apps/web/src/components/governance/dashboard/RecoveryDomainTracker.tsx#L20), [phase](../../apps/web/src/components/governance/dashboard/PPRRPhaseIndicator.tsx#L25), and [warning panels](../../apps/web/src/components/governance/dashboard/WarningCompliancePanel.tsx#L21) are not incident-specific endpoint integration.
  - **Owner / developer**: Join authorized incident state into COP with six-function status/relationships, level, active phases/overlaps and independent hazard chains. Present all 21 current/recent indicators and real compliance evidence, clearly separating catalogue metadata. Provide a redacted non-expert community view and working input mechanism; preserve existing dashboard consumers through versioned adapters.
  - **Tester positive**: Extend existing governance component/contract fixtures with two incident states and verify updates after actual AIDR mutations.
  - **Tester negative**: Changing source trust or catalogue counts alone must not change warning compliance or measured recovery progress; private indicators stay hidden.
  - **Tester edge**: Empty, stale, inaccessible, overlapping-hazard and partially available data remain clearly labeled and keyboard/screen-reader usable.
  - **Future check / prerequisites**: V-UI and V-CONTRACT; isolated web/API fixtures and accessibility reviewers, no public release.
  - **Dependencies / acceptance**: AUD-018-014, AUD-018-016, AUD-018-018, AUD-018-021, AUD-018-022; observed UI state matches authorized runtime records rather than placeholders.

- [ ] AUD-018-024 Preserve provenance across the Total Warning System
  - **Affected**: T058, T059, T060; FR-008, FR-009, FR-010, FR-011; US6-AS1, US6-AS2, US6-AS3. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Monitoring sends a summary](../../apps/agents/monitoring/agent.py#L89), so the first link is not absent. It omits original signal IDs/observations. [Risk retrieval](../../apps/agents/risk_assessment/pipeline.py#L169) then synthesizes an input with freshness 1.0 and empty provenance when IDs are absent. [Trend prediction exists](../../apps/agents/risk_assessment/pipeline.py#L326), but this lossy path and disconnected AWS output do not establish the full chain.
  - **Owner / developer**: Define and enforce a shared, versioned handoff carrying original IDs, times, provenance, hazard measurements, predictions, location and uncertainty through summary, assessment, interpretation, warning construction and delivery. Distinguish unavailable facts from synthetic fixtures and apply local staleness policy rather than restoring freshness.
  - **Tester positive**: Extend [AIDR scenarios](../../tests/simulation/test_aidr_scenarios.py#L30) using a recorded storm sequence through actual Monitoring, Risk and Communication boundaries; assert source-to-warning traceability.
  - **Tester negative**: Missing/stale/contradictory input cannot be relabeled fresh authoritative intelligence or silently become a complete warning.
  - **Tester edge**: Partial stores, multiple hazards, malformed predictions and fallback generation retain uncertainty and original references.
  - **Future check / prerequisites**: V-SCENARIO and V-WARNING; synthetic, timestamped source records and fake external I/O only.
  - **Dependencies / acceptance**: AUD-018-006, AUD-018-010, AUD-018-017; each element consumes the prior element's actual, attributable output.

- [ ] AUD-018-025 Close the warning-linked community-response deadline
  - **Affected**: T050, T053, T061; FR-012; SC-010; R-003, R-008; US6-AS4. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Indicator update](../../apps/api/app/services/recovery_service.py#L83) stores any `linked_alert_id` but does not resolve it, track warning issuance, enforce a minimum response set, or schedule overdue attention. No 24-hour consumer was found. A timestamp on an indicator is not the warning-to-feedback deadline.
  - **Owner / developer**: Validate same-scope warning links, define the minimum community-response set, and create deadlines at issuance even when no tracker/indicator exists. Support manual entry and batch imports; expose timely, missing and overdue feedback to operators and retain chain linkage across supersession.
  - **Tester positive**: Extend [recovery contract tests](../../tests/contract/test_recovery_contract.py#L80) with a published warning and linked evacuation/shelter response within 24 hours.
  - **Tester negative**: Unknown/cross-incident alert IDs, unrelated recovery updates and absence of any indicator must not satisfy the deadline.
  - **Tester edge**: Exactly 24 hours, late arrival, warning correction, daylight-saving changes and outage/replay generate one accurate overdue state without losing history.
  - **Future check / prerequisites**: V-RECOVERY and V-SCENARIO; fixed clock and published-warning fixtures, no waiting in real time.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-009, AUD-018-021, AUD-018-024; every issued warning has reviewable feedback or explicit overdue evidence.

- [ ] AUD-018-026 Automatically initiate lessons capture with exercise linkage
  - **Affected**: T032, T062, T064; FR-038, FR-052, FR-054; first-session significance clarification; US7-AS1. **Status**: PARTIAL.
  - **Expected / actual / impact**: The trigger [payload builder](../../apps/agents/common/pprr_lifecycle.py#L83) has no operational caller. [Exercise report generation](../../apps/api/app/services/exercise_report_service.py#L32) does not create a capture session/lesson; performance arrays are empty. Later [draft generation](../../apps/api/app/services/simulation/lessons_capture.py#L320) is a separate artifact, and [abort response](../../apps/api/app/api/routes/simulations_036.py#L580) asserts capture started without a generator call in that path.
  - **Owner / developer**: Subscribe to authoritative Level 2/3 closure and formally declared exercise completion; support explicit IC initiation and optional Level 1 capture. Idempotently create an audited capture session linked to the actual incident/run/report, and correlate available exercise metrics without fabricating outcomes. Reuse later draft builders where appropriate, but connect them to the operational register.
  - **Tester positive**: Extend [lessons contracts](../../tests/contract/test_lessons_contract.py#L1) and [full-AAR fixtures](../../tests/integration/test_lessons_capture_full_aar.py#L93) through real lifecycle controllers.
  - **Tester negative**: Non-significant Level 1 closure, undeclared practice session, failed closure and unknown report must not imply mandatory capture completion.
  - **Tester edge**: Duplicate closure/report events, exercise-only context, late metrics and lessons-store outage preserve one linked, resumable session.
  - **Future check / prerequisites**: V-LESSONS and V-SCENARIO; real local lifecycle fixtures and fake queues/stores.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-027; implement the idempotent lifecycle-to-register subscriber before exposing it through additional graph routes. Capture starts automatically for all mandatory triggers and acknowledgments reflect actual work.

- [ ] AUD-018-027 Enforce lesson categorization, assignment, and approved resolution
  - **Affected**: T010, T062, T063, T064, T065; FR-039, FR-041, FR-052; contradictory-lesson edge. **Status**: PARTIAL; category optionality conflicts with FR-039.
  - **Expected / actual / impact**: [Lesson model](../../packages/domain/src/domain/models/lesson.py#L19) permits missing categories, empty context strings and optional dates. [Service](../../apps/api/app/services/lessons_service.py#L74) uses unchecked copies for transitions; contradictory resolution trusts an approver string, and flagging an already resolved lesson does not reopen review. Origin references are not resolved to actual records.
  - **Owner / developer**: Require or explicitly govern deferred categorization, validate nonempty real origin references, assignment target/date and lifecycle transitions, and enforce IC/admin approval from authenticated evidence. Record contradiction/config links, decisions and resolution history. Revalidate updates and define the effect of a newly discovered contradiction on a resolved lesson.
  - **Tester positive**: Extend `_create_lesson` in [lessons tests](../../tests/contract/test_lessons_contract.py#L34) through categorized capture, assignment with target, reviewed resolution and original event lookup.
  - **Tester negative**: Blank/foreign origins, missing required categories/date, empty resolution and spoofed approver do not close a lesson.
  - **Tester edge**: Resolved-then-contradictory, reassignment, overdue target, repeat resolution and concurrent approval retain audit and state validity.
  - **Future check / prerequisites**: V-LESSONS and V-AUTH; authenticated QA/IC/admin fixtures and approved category policy.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-002, AUD-018-005, AUD-018-032; no unauthenticated or invalid closure and every lesson remains traceable.

- [ ] AUD-018-028 Calculate time-bounded trends and the actual 90-day closure metric
  - **Affected**: T062, T063, T068; FR-040, FR-041; SC-007; NFR-006, NFR-008; CHK058, CHK074. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Trend service](../../apps/api/app/services/lessons_service.py#L139) divides all resolved lessons by all lessons, irrespective of resolution age, treats rejected items as unresolved, and counts repeated tags rather than distinct events. Its route ignores documented time-window/minimum-event parameters and listing is unpaginated.
  - **Owner / developer**: Specify cohort maturity and rejected/reopened treatment; calculate capture-to-resolution <=90 days, overdue assignments, recurring themes across distinct events, and time-filtered function/phase distributions. Implement bounded pagination/full-register analysis and expose denominators and measurement window. Keep the operational 90% outcome UNVERIFIED until observed.
  - **Tester positive**: Extend [lessons tests](../../tests/contract/test_lessons_contract.py#L131) with dated lessons spanning multiple incidents and known expected cohorts.
  - **Tester negative**: Resolution at 91 days, duplicate tags on one event, future dates and excluded periods cannot inflate success.
  - **Tester edge**: Empty/immature cohort, reopened/rejected lessons, exact 90-day boundary, time zones and >=50 distinct lessons have explicit semantics.
  - **Future check / prerequisites**: V-LESSONS and V-PERF; frozen clock and approved denominator definition.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-027; independently computed expected cohort counts match responses, without claiming a measured 90-day business outcome.

- [ ] AUD-018-029 Add the lesson-linked PR gate and meaningful reference verification
  - **Affected**: T063, T066; FR-042; US7-AS4; R-007; CHK059. **Status**: MISSING for CI enforcement; PARTIAL for the helper.
  - **Expected / actual / impact**: [Verifier](../../apps/api/app/services/lessons_service.py#L177) recognizes a different `lesson...` token convention from contract examples, does not require open status or originating-event validity, and is not called by a located workflow/script. [Contract](contracts/lessons-api.yaml#L133) requests `lesson_ids`; the route instead takes `pr_description`.
  - **Owner / developer**: Set a canonical ID/reference format with legacy compatibility, verify existence/open state/origin, and integrate a least-privilege, fail-safe PR gate into the existing [CI workflow](../../.github/workflows/ci.yml#L1). Require change/test evidence addressing the lesson, with human review for substantive adequacy. Define non-lesson PR and register-outage behavior without exposing production data/secrets.
  - **Tester positive**: Extend [lessons contract tests](../../tests/contract/test_lessons_contract.py#L1) with an open lesson, valid event and matching PR/change evidence.
  - **Tester negative**: Unknown, closed, cross-scope or malformed references, unrelated change, and unavailable verifier cannot falsely pass a lesson-addressing PR.
  - **Tester edge**: Multiple IDs, canonical UUID and documented legacy format, duplicate refs and non-lesson PRs follow explicit policy.
  - **Future check / prerequisites**: V-LESSONS and V-GATE; synthetic PR bodies/register and a local workflow harness.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-027, AUD-018-032; an actual CI check consumes the verifier and demonstrates both block and pass cases.

- [ ] AUD-018-030 Route recovery and lessons through the active orchestration graph
  - **Affected**: T006, T015, T046, T054, T062; FR-054; R-005, R-006, R-007. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Legacy helper](../../apps/agents/common/handoffs.py#L70) targets `recovery_service`, uses category as scope and defaults tenant to live. It does not route to recovery-configured agents. The [replacement workflow](../../apps/agents/maf_runtime/workflow/builder.py#L89) contains only the five response steps plus HITL. Category declarations in [HandoffStep](../../packages/domain/src/domain/models/handoff_chain.py#L6) do not establish a consumer.
  - **Owner / developer**: Implement category/phase-aware dispatch in the active graph and documented fallback, map destinations to existing recovery modes or the lessons service, and preserve authenticated tenant/incident/correlation context. Prevent payload overrides of routing metadata; define retries, idempotency, failed-consumer and closure-trigger behavior.
  - **Tester positive**: Extend [handoff category tests](../../tests/unit/test_domain_models_aidr.py#L559) and scenarios to assert actual recipient invocation and resulting state.
  - **Tester negative**: Merely constructing a helper, unknown destination, wrong category and live/simulation cross-routing cannot count as successful handoff.
  - **Tester edge**: Runtime mode change, duplicate event, receiver outage and parallel Response/Recovery retain one correct destination and provenance.
  - **Future check / prerequisites**: V-SCENARIO and V-STORE; recording recipients and explicit runtime mode.
  - **Dependencies / acceptance**: AUD-018-002, AUD-018-005, AUD-018-020, AUD-018-026; both AIDR categories have demonstrated producers and consumers.

- [ ] AUD-018-031 Enforce versioned timeline payload contracts and durable provenance
  - **Affected**: T013, T016, T032, T034, T042; FR-019, FR-053; all audited transition edges. **Status**: PARTIAL.
  - **Expected / actual / impact**: [TimelineEvent](../../packages/domain/src/domain/models/timeline_event.py#L7) accepts an arbitrary payload dictionary. [Evacuation payload](../../apps/agents/evacuation/stages.py#L74) differs from the [documented four payload schemas](data-model.md#L392), omitting plan/re-entry-count fields and using different names. PPRR/level builders supply useful fields but no shared validation enforces completeness or provenance.
  - **Owner / developer**: Define validated, versioned payloads for the four named actions while preserving unrelated system events. Standardize source/target, incident/plan/run, rationale, authenticated authorizer, overlap and re-entry fields. Commit state and audit consistently and retain clear timestamps/order through replay.
  - **Tester positive**: Extend [PPRR payload tests](../../tests/unit/test_pprr_lifecycle.py#L94) and stage/lesson tests with exact field assertions for every action.
  - **Tester negative**: Missing actor/rationale/source, invalid enum, wrong incident and incompatible payload version cannot be recorded as a valid transition.
  - **Tester edge**: Re-entry count, overlap end, exercise-only event, old payload migration and concurrent events remain reconstructible.
  - **Future check / prerequisites**: V-MODELS, V-PPRR, V-EVAC and V-LESSONS; approved schema compatibility policy and durable audit fixture.
  - **Dependencies / acceptance**: AUD-018-001, AUD-018-005; all four event shapes are enforced at producers/consumers and trace real state changes.

- [ ] AUD-018-032 Reconcile all six API contracts and test exact conformance
  - **Affected**: T018, T023, T025, T028, T035, T039, T043, T051, T063, T078, T081; all six API contracts. **Status**: CONFLICT.
  - **Expected / actual / impact**: Creation status codes, verbs, names and response shapes differ; detailed deviations are enumerated below. [AIIMS contract test](../../tests/contract/test_aiims_contract.py#L67) accepts any dictionary, and [recovery tests](../../tests/contract/test_recovery_contract.py#L60) do not enforce the contract. Markdown in `.yaml` files cannot itself be schema validation.
  - **Owner / developer**: Obtain canonical contract decisions, preserving required semantics and compatibility. Produce a machine-readable representation or explicit test schema for the approved narratives; type request/response models and generate OpenAPI from them. Correct the missing warning-create operation, exact fields, errors, pagination and PPRR verb conflict. Do not resolve discrepancies simply by weakening tests.
  - **Tester positive**: Extend all six existing contract files using their local `_seed_incident`/creation fixtures; validate exact status, required fields, enums and documented examples against generated schemas.
  - **Tester negative**: Wrong verb, aliases not explicitly supported, invalid enums, unknown fields and missing required fields receive the documented error, not silently ignored data.
  - **Tester edge**: Legacy client compatibility, empty lists, all-clear, duplicate creation, unknown resources and response pagination are explicit.
  - **Future check / prerequisites**: V-CONTRACT; approved contract decisions, isolated app fixture and schema tooling.
  - **Dependencies / acceptance**: AUD-018-038; settle canonical contracts/test oracles before producers are integrated, then run conformance checks as each capability lands. All six contracts have strict positive/negative parity tests and no ambiguous pass assertions.

- [ ] AUD-018-033 Validate CAP, EDXL-DE and geographic interoperability
  - **Affected**: T024, T078, T080; R-009; NN-4; CHK009, CHK018, CHK093. **Status**: PARTIAL.
  - **Expected / actual / impact**: [CAP rendering](../../apps/api/app/api/routes/warning_chain.py#L104) interpolates unescaped alert text into XML, hard-codes category and uses rendering time as sent time. [EDXL](../../apps/agents/communication/edxl_serialiser.py#L16) can emit empty sent time and `Actual` for a draft, with custom AWS elements but no inspected standards-schema validation/delivery integration. Existing [XML tests](../../tests/contract/test_warning_contract.py#L89) cover simple parsing, not conformance. Geographic fields are not consistently validated as GeoJSON.
  - **Owner / developer**: Use structured XML serialization for CAP, proper warning/update/cancel references, issue time, status/simulation semantics and hazard mapping. Define a standards-compliant EDXL content envelope and connect the delivery option. Reuse/extend geographic models with validated GeoJSON and explicit non-graphical fallbacks. Pin authoritative schemas with provenance for future offline checks.
  - **Tester positive**: Extend existing warning contract XML assertions, including published AWS tiers, cancellation/update and approved geometry fixtures.
  - **Tester negative**: Ampersand/angle-bracket content must remain valid escaped XML; missing required timestamps, draft-as-Actual, invalid references and malformed geometry must not export as valid operational messages.
  - **Tester edge**: Non-English text, all-clear, `other` hazards, simulation, empty area and polygon boundaries preserve semantics.
  - **Future check / prerequisites**: V-INTEROP; pinned CAP/EDXL schemas and offline validators, not live emergency consumers.
  - **Dependencies / acceptance**: AUD-018-003, AUD-018-009, AUD-018-032; schema-valid output and verified delivery-envelope integration, not just well-formed XML.

- [ ] AUD-018-034 Emit the seven metrics and report real capability health
  - **Affected**: T026, T033, T041, T049, T057, T068, T075, T076; NFR-009, NFR-010; CHK067. **Status**: MISSING for required metrics; PARTIAL for health.
  - **Expected / actual / impact**: Searches of API and agent Python sources found none of the seven required metric emitters. [AIDR health](../../apps/api/app/api/routes/health.py#L23) measures `len(dict)` and calls it healthy, without dependency, queue, staleness or failure information. Fast dictionary access is not measured operational health.
  - **Owner / developer**: Define units, denominators, cardinality, recording points and alert thresholds for every named metric; emit at validated state boundaries with failure/denial treatment. Distinguish liveness from readiness, include warning validation and degraded queue/last-known state, and bound dependency health probes to the one-second budget.
  - **Tester positive**: Extend existing capability contract tests with a recording meter and deterministic health clients; assert each metric changes only after its corresponding operation.
  - **Tester negative**: Failed transition, rejected warning, duplicate replay and unavailable dependency cannot increment success or report healthy readiness.
  - **Tester edge**: Zero denominator, stale cache, slow probe, recovery/flush and concurrent updates yield stable, low-cardinality measurements.
  - **Future check / prerequisites**: V-METRICS and V-PERF; in-memory telemetry exporter and fake clocks/dependencies.
  - **Dependencies / acceptance**: AUD-018-005 and the corresponding capability tasks; all seven signals are consumed/tested and health reflects actual readiness without exceeding its budget.

- [ ] AUD-018-035 Add five-container CRUD, partition and retention integration evidence
  - **Affected**: T002, T003, T077, T082; NFR-015; R-013. **Status**: MISSING for the specified suite/coverage; deployed residency UNVERIFIED.
  - **Expected / actual / impact**: The named `tests/integration/test_aidr_cosmos.py` is absent, and scoped replacement search found catalogue/exercise/workflow tests, not integration of recovery, lessons, assignments, stages and contexts. [Container declarations](../../infra/modules/recovery-lessons.bicep#L18) define keys but no explicit TTL policy. Declarations do not prove provisioning, CRUD or lawful retention.
  - **Owner / developer**: After repository wiring, define retention/TTL and exercise partition behavior with the data owner. Add the originally proposed integration file or an explicitly documented extension to a suitable existing suite; use the real adapters against disposable stores. Retain AU-only persistence and review IaC policy/AVM exceptions through the approved process.
  - **Tester positive**: CRUD each entity via service/controller and a new client; assert actual partition keys, indexes/retention settings and preserved model fields.
  - **Tester negative**: Wrong partition/tenant, stale ETag, forbidden region configuration and retention violations fail without leakage or silent fallback.
  - **Tester edge**: Exercise-only lesson, context transfer, re-entry history, restart, and retention-boundary records retain the approved semantics.
  - **Future check / prerequisites**: V-STORE and V-INFRA. Proposed path: `tests/integration/test_aidr_cosmos.py`; not existing evidence. Live-resource verification requires separately authorized AU test resources and signed read-only inventory evidence.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-031; five real adapter paths covered, retention decisions documented, deployment claims backed separately.

- [ ] AUD-018-036 Replace label-only scenario success with end-to-end assertions
  - **Affected**: T069, T079, T081, T083; all seven user stories, seven edges and SC-001 through SC-010. **Status**: PARTIAL.
  - **Expected / actual / impact**: [Bushfire scenario](../../tests/simulation/test_aidr_scenarios.py#L30) creates no warning and ignores a phase-transition result; cyclone progresses without safety evidence; recovery only checks selected responses. Later AAR tests synthesize input directly. These sources do not establish connected enforcement or actual test execution.
  - **Owner / developer**: Extend the existing scenario file and relevant contract/unit fixtures rather than duplicating test scaffolding. Exercise real orchestration/controller paths, mocking external I/O only. Assert required outputs, denials, persistence, authority, provenance, UI readback and every edge; remove comments that permit silently failed setup.
  - **Tester positive**: Run bushfire escalation/closure, cyclone five stages, flood phases and long-term recovery, plus lessons and TWS, with the acceptance matrix as an explicit oracle.
  - **Tester negative**: Mutate/bypass a guard or disconnect a consumer; the corresponding scenario must fail, not pass on type or status alone.
  - **Tester edge**: Include all EC-01 through EC-07 fixtures and failure/retry boundaries named by remediation tasks.
  - **Future check / prerequisites**: V-SCENARIO, V-CONTRACT and V-UI; isolated channels/stores and approved scenario fixtures.
  - **Dependencies / acceptance**: Capability fixes in AUD-018-001 through AUD-018-034; every acceptance row has an independent behavior assertion and a later recorded run result.

- [ ] AUD-018-037 Measure all NFR budgets using valid outputs and real concurrency
  - **Affected**: T084; NFR-001 through NFR-009; SC-004. **Status**: PARTIAL for test authoring; execution/outcomes UNVERIFIED.
  - **Expected / actual / impact**: [Benchmark file](../../tests/benchmark/test_aidr_performance.py#L1) times in-process dictionary-backed calls. [Recovery concurrency](../../tests/benchmark/test_aidr_performance.py#L155) uses sequential loops. Fifty lessons are seeded for trend analysis, not verified as a concurrent register workload. The extra T084 generation <=2s and evacuation-stage <=3s checks are absent.
  - **Owner / developer**: Extend that file with representative, valid operation results, controller-to-adapter timing, concurrent workload coordination, warm/cold/failure profiles and explicit concurrency counts. Keep each NFR budget distinct; add the extra task budgets without substituting generation time for validation time. Record configuration, volume, latency distribution and actual assertions.
  - **Tester positive**: Validate <=5s warning validation/assignment/phase/capture, <=10s dashboard, <=30s trends, >=10 simultaneous recovery operations, >=50 distinct lessons and <=1s health under the agreed workload.
  - **Tester negative**: Inject slow dependency, invalid response, sequential scheduling or lost updates; the benchmark must fail rather than timing an error/empty result as success.
  - **Tester edge**: Mixed incidents/phases, simultaneous writers, degraded queues, cold starts and exact budget boundaries preserve correctness.
  - **Future check / prerequisites**: V-PERF; approved benchmark environment and isolated representative stores, with no production output.
  - **Dependencies / acceptance**: AUD-018-005, AUD-018-034, AUD-018-036; measured concurrency and correct results support every budget, with no retroactive success claim.

- [ ] AUD-018-038 Complete cross-spec alignment and resolve normative inconsistencies
  - **Affected**: T070, T071, T072, T073, T074; FR-043, FR-044, FR-045, FR-046, FR-047; SC-008; CHK020, CHK024, CHK063, CHK077 through CHK084, CHK097. **Status**: PARTIAL / CONFLICT.
  - **Expected / actual / impact**: The six dependent specs have persona and authority references, and [Risk severity is already AIDR-aligned](../012-risk-assessment-agent/spec.md#L160), but no dedicated per-agent AIIMS mapping/TWS addendum was found in their inspected specifications. [Hub recovery deferral](../001-disaster-response-hub/spec.md#L479) is not a Shared Responsibility Model/agent mapping. [Quickstart mapping](quickstart.md#L146) assigns Resource Allocation both Planning and Logistics, contradicting exactly one function; SC-002 and N-001 differ on required coverage by level.
  - **Owner / developer**: Append approved, reciprocal addenda covering role/function, TWS inputs/outputs, priority/recovery behavior, PPRR and Shared Responsibility. Preserve existing risk scales, zone routing and non-warning timeouts. Resolve all-active versus Level-3 coverage, dual-role examples, NCM scope, indicator measurement definitions and other detailed checklist ambiguities with named owners. Keep original checkbox history unchanged.
  - **Tester positive**: V-DOC review must find a specific, consistent mapping and relevant handbook citation for each of the six specs.
  - **Tester negative**: A generic persona cross-reference, conflicting dual role or unapproved scope reduction cannot satisfy alignment.
  - **Tester edge**: Five agent types plus human Control, existing severity/zone consumers, and out-of-scope country variants remain explicitly compatible.
  - **Future check / prerequisites**: V-DOC; specification owners and a recorded approval date for the 30-day SC-008 clock.
  - **Dependencies / acceptance**: None; resolve the normative decisions before dependent implementation, with named owners. All six addenda and critical checklist decisions are reviewable; elapsed approval-to-update time is separately evidenced.

- [ ] AUD-018-039 Supply honest review, onboarding, approval and outcome evidence
  - **Affected**: T001, T069, T075, T076, T077, T078, T079, T081, T082, T083, T084; plan gates, both checklists, quickstart checklist, SC-006, SC-007, SC-008. **Status**: UNVERIFIED for claimed execution/approval; CONFLICT for stale guidance.
  - **Expected / actual / impact**: [Summary checklist](checklists/requirements.md#L32) claims first-pass validation and 47 FRs; the current spec has 54, while all 98 detailed items remain unchecked. [Quickstart](quickstart.md#L10) says Python 3.10+ but [project metadata](../../pyproject.toml#L9) requires >=3.12. Named model-package exports are absent; [the alternate namespace](../../packages/domain/src/ama_domain/__init__.py#L1) explicitly serves other contracts. No Spec-018 run/sign-off record was located.
  - **Owner / developer**: Reconcile onboarding and export conventions without declaring namespace imports broken merely because an initializer is absent. Append an evidence ledger distinguishing source artifacts, run IDs/revision/configuration, human reviews, infrastructure review/residency evidence and business outcomes. Preserve historical checkboxes and frozen rubric evidence; do not recreate a branch to prove T001.
  - **Tester positive**: An independent future reviewer follows the corrected onboarding path and records actual results plus identified approvers for warnings, privacy, IaC and accessibility.
  - **Tester negative**: Fixtures, screenshots, prose, compiled caches and checked boxes alone cannot close execution, residency or human-review obligations.
  - **Tester edge**: Missing/failed/skipped runs, partial approvals, stale results and unavailable external validation remain explicitly open.
  - **Future check / prerequisites**: V-DOC, V-INFRA and approved V-* runs; no commands from this task were executed here.
  - **Dependencies / acceptance**: AUD-018-032, AUD-018-035, AUD-018-036, AUD-018-037, AUD-018-038; every gate has attributable evidence or an honest open status.

- [ ] AUD-018-040 Repair appended persona/hypothesis traceability without inventing validation
  - **Affected**: PER-046, PER-047, PER-048, HYP-016, SCP-052, SCP-053, SCP-054 and both authority amendments; linked persona/evidence contracts. **Status**: CONFLICT / UNVERIFIED; HYP-016 stub MISSING.
  - **Expected / actual / impact**: [Spec appendices](spec.md#L317) claim validated personas and link a nonexistent `HYP-HYP-016.md`. [Persona evidence](../001-disaster-response-hub/spec.md#L171) names generic former-role reviewers, not the contract's named/date records; [presentation B7](../../docs/ama-presentation/AMA_Capstone_QnA.md#L132) describes handbook-derived personas and future pilot validation. Portfolio structural uplift is not per-spec HYP-016 validation. The timeout authority cites FR-017, which in this spec describes communication semantics.
  - **Owner / developer**: Fix the hypothesis link/location under approved change control, create an honest contract-conforming Not tested stub if no historical evidence exists, and distinguish per-spec measurement from portfolio summaries. Resolve persona identity/date/authority records with the owners. Correct authority references while retaining 018 recovery/timeout ownership and all non-AU/constitution-change deferrals.
  - **Tester positive**: V-DOC verifies the six-heading stub, two prerequisites, bounded window, falsification rule, own-spec link and attributable persona review evidence.
  - **Tester negative**: An aggregate rubric score, actor-file existence or generic SME description cannot prove interviews, consultation on every change or hypothesis validation.
  - **Tester edge**: Missing approvals and unresolved D-009 preserve placeholders and deferrals; no new grading, agents or country rollout is implied.
  - **Future check / prerequisites**: V-DOC; separately authorized human review/evidence work only.
  - **Dependencies / acceptance**: AUD-018-038, AUD-018-039; links and authority references are consistent and every outcome claim is supported or explicitly Not tested/UNVERIFIED.

## Functional Requirement Coverage

Every row assesses the original requirement, not just a filename. Follow-ups are open; an IMPLEMENTED model/artifact row does not certify an operational outcome.

| Requirement | Status | Inspected evidence and remaining obligation | Open follow-ups |
| --- | --- | --- | --- |
| [FR-001](spec.md#L165) | PARTIAL | [Builder](../../apps/agents/communication/warning_builder.py#L60) has three tiers; runtime model/publish integration is absent. | AUD-018-003, AUD-018-006 |
| [FR-002](spec.md#L166) | PARTIAL | Builder supplies headline/areas/action but permits generic location and is not the pipeline output. | AUD-018-006, AUD-018-009 |
| [FR-003](spec.md#L167) | PARTIAL | [Icon lookup](../../apps/agents/communication/warning_builder.py#L38) exists; graphical delivery and fallback are not connected/proven. | AUD-018-006, AUD-018-033 |
| [FR-004](spec.md#L168) | PARTIAL | [Downgrade helper](../../apps/agents/communication/warning_builder.py#L117) does not validate prior tier or approval. | AUD-018-003, AUD-018-009 |
| [FR-005](spec.md#L169) | PARTIAL | [All-clear helper](../../apps/agents/communication/warning_builder.py#L137) does not validate resolution or terminal chain state. | AUD-018-003, AUD-018-009 |
| [FR-006](spec.md#L170) | PARTIAL | [Ten checks](../../apps/agents/common/warning_compliance.py#L70) are structural proxies; default pass and governance trust percentages are not compliance review. | AUD-018-007, AUD-018-039 |
| [FR-007](spec.md#L171) | PARTIAL | [Translation stages](../../apps/agents/communication/pipeline.py#L298) exist; all population groups/formats are not enforced. | AUD-018-006, AUD-018-010 |
| [FR-008](spec.md#L175) | PARTIAL | Monitoring/risk/communication components exist; provenance and response-loop connections are incomplete. | AUD-018-024, AUD-018-025 |
| [FR-009](spec.md#L176) | PARTIAL | [Summary handoff](../../apps/agents/monitoring/agent.py#L89) reaches risk retrieval but lacks source IDs/observations. | AUD-018-024 |
| [FR-010](spec.md#L177) | PARTIAL | [Trend extrapolation](../../apps/agents/risk_assessment/pipeline.py#L326) exists; lossy intake and prompt scale conflict weaken connected predictions. | AUD-018-017, AUD-018-024 |
| [FR-011](spec.md#L178) | PARTIAL | Multilingual drafting/safety are present in the old pipeline; AWS interpretation/delivery are not connected end to end. | AUD-018-006, AUD-018-010, AUD-018-024 |
| [FR-012](spec.md#L179) | PARTIAL | [Linked indicator field](../../apps/api/app/services/recovery_service.py#L83) is stored without validated warning linkage or response deadline. | AUD-018-025 |
| [FR-013](spec.md#L183) | PARTIAL | [Assign service](../../apps/api/app/services/aiims_service.py#L31) rejects existing active duplicates; no incident bootstrap or complete coverage. | AUD-018-002, AUD-018-014, AUD-018-015 |
| [FR-014](spec.md#L184) | PARTIAL | [Structure API](../../apps/api/app/services/aiims_service.py#L58) exists; current incident COP does not integrate it. | AUD-018-014, AUD-018-023 |
| [FR-015](spec.md#L185) | PARTIAL | [Level field](../../packages/domain/src/domain/models/incident.py#L30) and change endpoint exist; Level 3 guard unused and prompt includes zero. | AUD-018-014, AUD-018-017 |
| [FR-016](spec.md#L186) | PARTIAL | Level update does not establish governed cross-agency COP or relationships. | AUD-018-016, AUD-018-023 |
| [FR-017](spec.md#L187) | PARTIAL | [Handoff shape](../../apps/agents/common/handoffs.py#L26) does not enforce entity-specific semantics; COP lacks links. All four inline acceptance clauses assessed below. | AUD-018-016 |
| [FR-018](spec.md#L192) | PARTIAL | [Stage state machine](../../apps/agents/evacuation/stages.py#L37) exists, but stage labels do not execute operations. | AUD-018-011, AUD-018-012 |
| [FR-019](spec.md#L193) | PARTIAL | [Decision DTO](../../apps/api/app/api/routes/evacuation.py#L35) makes type/approach/scope optional and trusts authority text. | AUD-018-001, AUD-018-011 |
| [FR-020](spec.md#L194) | PARTIAL | Warning stage transition writes a timeline event, not an approved evacuation warning with route/destination/timeframe. | AUD-018-012 |
| [FR-021](spec.md#L195) | PARTIAL | [Withdrawal update](../../apps/api/app/api/routes/evacuation.py#L161) stores aggregate movement/status but does not allocate priority transport. | AUD-018-010, AUD-018-012 |
| [FR-022](spec.md#L196) | PARTIAL | [Shelter update](../../apps/api/app/api/routes/evacuation.py#L179) stores totals only; per-shelter welfare/accessibility/vulnerability missing. | AUD-018-011, AUD-018-012 |
| [FR-023](spec.md#L197) | PARTIAL | [Return update](../../apps/api/app/api/routes/evacuation.py#L197) accepts flags/rate but does not certify safety or manage phased reentry. | AUD-018-011, AUD-018-012 |
| [FR-024](spec.md#L198) | PARTIAL | [Shelter-in-place state](../../apps/agents/evacuation/stages.py#L37) captures rationale but schedules no monitoring/reassessment. | AUD-018-012, AUD-018-013 |
| [FR-025](spec.md#L199) | PARTIAL | [Type literals](../../packages/domain/src/domain/models/evacuation_stage.py#L24) exist; timing and sudden-onset warning integration do not. | AUD-018-009, AUD-018-012 |
| [FR-026](spec.md#L203) | PARTIAL | Four phase values exist, but current transition map is terminal/sequential and phase work is disconnected. | AUD-018-018, AUD-018-020 |
| [FR-027](spec.md#L204) | PARTIAL | Incident/context phase fields exist; [dashboard](../../apps/api/app/services/dashboard_service.py#L48) omits them. | AUD-018-019, AUD-018-023 |
| [FR-028](spec.md#L205) | PARTIAL | Existing risk/planning capabilities are available independently, not driven by Prevention context with risk-reduction outputs. | AUD-018-020 |
| [FR-029](spec.md#L206) | PARTIAL | Existing simulation/planning surfaces do not connect all four Preparedness obligations to a phase context. | AUD-018-019, AUD-018-020 |
| [FR-030](spec.md#L207) | PARTIAL | Response pipeline exists; [phase service](../../apps/api/app/services/pprr_service.py#L30) initiates no concurrent recovery planning. | AUD-018-018, AUD-018-020 |
| [FR-031](spec.md#L208) | PARTIAL | Overlap flag is recorded but no operational overlap/end-state or managed handover is maintained. | AUD-018-018 |
| [FR-032](spec.md#L212) | PARTIAL | [All 21 slots](../../apps/api/app/services/recovery_service.py#L27) and grouped view exist; meaningful ongoing tracking/UI incomplete. | AUD-018-021, AUD-018-023 |
| [FR-033](spec.md#L213) | PARTIAL | [Principle list validation](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L131) permits empty list; recommendations are not required to cite principles. | AUD-018-022 |
| [FR-034](spec.md#L214) | PARTIAL | Community-input model field exists but initialization ignores documented body; no connected prioritization/feedback mechanism. | AUD-018-022, AUD-018-023 |
| [FR-035](spec.md#L215) | MISSING | No inspected phase consumer activates existing recovery-configured agents alongside Response. | AUD-018-020, AUD-018-030 |
| [FR-036](spec.md#L216) | PARTIAL | [Update](../../apps/api/app/services/recovery_service.py#L83) overwrites latest values; no retained longitudinal observations. | AUD-018-005, AUD-018-021 |
| [FR-037](spec.md#L217) | PARTIAL | [Community projection](../../apps/api/app/services/recovery_service.py#L174) excludes sensitive labels but is not a complete safe/non-expert community workflow. | AUD-018-004, AUD-018-022, AUD-018-023 |
| [FR-038](spec.md#L221) | PARTIAL | Capture API, trigger helpers and later exercise drafts exist; required lifecycle auto-initiation does not. | AUD-018-026 |
| [FR-039](spec.md#L222) | CONFLICT | Normative required categorization conflicts with optional model/contract fields. | AUD-018-027, AUD-018-032 |
| [FR-040](spec.md#L223) | PARTIAL | [Register/trends](../../apps/api/app/services/lessons_service.py#L139) lack distinct-event/time-window semantics and durable pagination. | AUD-018-005, AUD-018-028 |
| [FR-041](spec.md#L224) | PARTIAL | [Assignment/resolution](../../apps/api/app/services/lessons_service.py#L74) exist, but dates optional and transitions/authority not enforced. | AUD-018-027, AUD-018-028 |
| [FR-042](spec.md#L225) | PARTIAL | A verifier helper exists, but actual CI enforcement, open status, valid origin and meaningful change review are absent. | AUD-018-029 |
| [FR-043](spec.md#L229) | PARTIAL | [Monitoring specification](../010-monitoring-agent/spec.md#L156) has freshness/threshold behavior; required explicit TWS/AIIMS addendum not found. | AUD-018-038 |
| [FR-044](spec.md#L230) | PARTIAL | [Risk specification](../012-risk-assessment-agent/spec.md#L160) retains AIDR four-level severity; explicit TWS mapping and prompt consistency incomplete. | AUD-018-017, AUD-018-038 |
| [FR-045](spec.md#L231) | PARTIAL | [Resource ownership amendment](../011-resource-allocation-agent/spec.md#L355) and AIIMS language exist, but recovery-mode behavior does not. | AUD-018-020, AUD-018-038 |
| [FR-046](spec.md#L232) | PARTIAL | [Hub persona/PPRR references](../001-disaster-response-hub/spec.md#L171) exist; full AIIMS structure/Shared Responsibility alignment not established by those references. | AUD-018-038 |
| [FR-047](spec.md#L233) | MISSING | Dedicated per-agent mapping sections not found in the six specified dependent specs; generic persona references are not those sections. | AUD-018-038 |
| [FR-048](spec.md#L237) | IMPLEMENTED | [Domain PublicAlert](../../packages/domain/src/domain/models/public_alert.py#L30) contains the five required additive fields and preserved lifecycle. Runtime adoption is separately incomplete. | AUD-018-006, AUD-018-009 |
| [FR-049](spec.md#L238) | PARTIAL | [Assignment model](../../packages/domain/src/domain/models/aiims_role_assignment.py#L34) exists; mutating function loses true historical assignment periods. | AUD-018-014, AUD-018-015 |
| [FR-050](spec.md#L239) | IMPLEMENTED | [Independent incident field](../../packages/domain/src/domain/models/incident.py#L43) and [non-incident context model](../../packages/domain/src/domain/models/pprr_phase_context.py#L15) exist. Transition/COP obligations remain separate. | AUD-018-018, AUD-018-019 |
| [FR-051](spec.md#L240) | IMPLEMENTED | [IncidentType](../../packages/domain/src/domain/models/incident.py#L6) contains all nine required hazard values, additively extended further. [Model tests](../../tests/unit/test_domain_models_aidr.py#L35) cover added values. | - |
| [FR-052](spec.md#L241) | PARTIAL | `scenario_run_id` exists, but no report resolution/metric correlation or lifecycle-to-register connection. | AUD-018-026, AUD-018-027 |
| [FR-053](spec.md#L242) | PARTIAL | [PPRR service](../../apps/api/app/services/pprr_service.py#L30) creates system TimelineEvents; overlap execution, durable authority and schema validation incomplete. | AUD-018-018, AUD-018-031 |
| [FR-054](spec.md#L243) | PARTIAL | [Categories](../../packages/domain/src/domain/models/handoff_chain.py#L6) and helpers exist; active graph lacks AIDR producers/consumers. | AUD-018-026, AUD-018-030 |

## Non-Functional and Success Coverage

| Requirement | Status | Evidence and remaining obligation | Open follow-ups |
| --- | --- | --- | --- |
| [NFR-001](spec.md#L249) | UNVERIFIED | [Five-second test](../../tests/benchmark/test_aidr_performance.py#L31) exists; no run or valid publication-path measurement. | AUD-018-006, AUD-018-037 |
| [NFR-002](spec.md#L250) | UNVERIFIED | Benchmark times a manual dictionary assignment, not complete incident bootstrap. | AUD-018-014, AUD-018-037 |
| [NFR-003](spec.md#L251) | UNVERIFIED | Benchmark times enum/event mutation, not managed overlap. | AUD-018-018, AUD-018-037 |
| [NFR-004](spec.md#L252) | UNVERIFIED | Benchmark times an API response, not populated four-environment user dashboard load. | AUD-018-021, AUD-018-023, AUD-018-037 |
| [NFR-005](spec.md#L253) | UNVERIFIED | Capture timing source exists, but template presentation/durable valid save not measured. | AUD-018-026, AUD-018-027, AUD-018-037 |
| [NFR-006](spec.md#L254) | UNVERIFIED | Fifty seeded lessons exercise an in-memory trend call; full-register corrected analysis not measured. | AUD-018-028, AUD-018-037 |
| [NFR-007](spec.md#L255) | UNVERIFIED | [Concurrency test](../../tests/benchmark/test_aidr_performance.py#L155) is sequential. | AUD-018-037 |
| [NFR-008](spec.md#L256) | UNVERIFIED | Fifty fixture lessons are not execution evidence of the specified simultaneous register workload. | AUD-018-028, AUD-018-037 |
| [NFR-009](spec.md#L260) | PARTIAL | [Health routes](../../apps/api/app/api/routes/health.py#L23) exist; dependency health and <=1s outcome unverified. | AUD-018-034, AUD-018-037 |
| [NFR-010](spec.md#L261) | MISSING | Required seven named emitters not found in API/agent sources; metric table below retains each obligation. | AUD-018-034 |
| [NFR-011](spec.md#L265) | MISSING | [Lesson store](../../apps/api/app/services/state_store.py#L29) has no local buffer/recovery synchronization consumer. | AUD-018-005 |
| [NFR-012](spec.md#L266) | MISSING | [Recovery dashboard](../../apps/api/app/services/recovery_service.py#L58) has no staleness/dependency-unavailable behavior. | AUD-018-005, AUD-018-021 |
| [NFR-013](spec.md#L270) | PARTIAL | Existing warning safety and optional recovery analysis safety do not enforce all recovery/public output; unvalidated branch inspected. | AUD-018-022 |
| [NFR-014](spec.md#L271) | PARTIAL | Model/service k-check allows absent coverage and classification bypass; no LGA control or observed privacy approval. | AUD-018-004, AUD-018-039 |
| [NFR-015](spec.md#L272) | UNVERIFIED | [AU-only main parameter](../../infra/main.bicep#L78), [account location](../../infra/main.bicep#L580), and module binding support authored residency. No deployed-state verification. | AUD-018-005, AUD-018-035, AUD-018-039 |
| [SC-001](spec.md#L305) | PARTIAL | Three-tier helpers do not make all runtime warnings compliant; no exhaustive connected assertion or execution. | AUD-018-003, AUD-018-006, AUD-018-036 |
| [SC-002](spec.md#L306) | CONFLICT | Six roles for every active incident conflicts with Level-3-only full-coverage rule; defaults omit Control and COP lacks integration. | AUD-018-014, AUD-018-023, AUD-018-038 |
| [SC-003](spec.md#L307) | PARTIAL | Sequential labels exist; operational outputs, safe return, replan and Return re-entry accounting incomplete. | AUD-018-011, AUD-018-012, AUD-018-013, AUD-018-036 |
| [SC-004](spec.md#L308) | PARTIAL | Incident fields are independent, but overlap/phase-driven resource behavior and non-degradation under concurrency not demonstrated. | AUD-018-018, AUD-018-020, AUD-018-037 |
| [SC-005](spec.md#L309) | IMPLEMENTED | [Indicator catalogue](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L26) and [initialization](../../apps/api/app/services/recovery_service.py#L27) provide exactly 7+5+5+4=21; [simulation assertion](../../tests/simulation/test_aidr_scenarios.py#L151) checks count. Longitudinal/UI/outcome claims are separate. | AUD-018-021, AUD-018-023 |
| [SC-006](spec.md#L310) | PARTIAL | Structural checks and source-trust percentages do not prove ten-principle compliance review of 100% of warnings. | AUD-018-007, AUD-018-039 |
| [SC-007](spec.md#L311) | PARTIAL | Current all-time ratio is not 90%-within-90-days; real closure outcome UNVERIFIED. | AUD-018-027, AUD-018-028, AUD-018-039 |
| [SC-008](spec.md#L312) | PARTIAL | Six specific addenda are incomplete and no approval date/30-day elapsed evidence was found. | AUD-018-038, AUD-018-039 |
| [SC-009](spec.md#L313) | PARTIAL | Seven-group helper and legacy segment labels do not cover every required population at every stage. | AUD-018-010, AUD-018-012, AUD-018-036 |
| [SC-010](spec.md#L314) | PARTIAL | Link field exists, but 24-hour warning-to-response tracking, alerting and observed feedback are absent. | AUD-018-025, AUD-018-039 |

| NFR-010 metric | Status | Required future observation point | Follow-up |
| --- | --- | --- | --- |
| `warning_compliance_rate` | MISSING | Validated warning outcomes with a warning denominator, not source trust. | AUD-018-034 |
| `tier_transition_latency` | MISSING | Actual approved/persisted transitions in a warning chain. | AUD-018-034 |
| `evacuation_stage_duration` | MISSING | Real stage entry/exit, including re-entry and incomplete stages. | AUD-018-034 |
| `recovery_indicator_update_frequency` | MISSING | Retained observation intervals and explicit stale/missing observations. | AUD-018-034 |
| `lesson_resolution_time` | MISSING | Valid capture-to-approved-resolution duration, with reopen semantics. | AUD-018-034 |
| `pprr_phase_transition_count` | MISSING | Successfully committed authorized transitions, replay-safe. | AUD-018-034 |
| `aiims_role_coverage_ratio` | MISSING | Active per-incident assignments against the approved coverage policy. | AUD-018-034 |

## Acceptance Scenarios and Edge Cases

`USn-ASn` and `EC-nn` are report labels for the original numbered scenarios and named edges, not new product requirements. All execution outcomes are UNVERIFIED; statuses below describe source coverage.

| Scenario | Status | Expected versus inspected evidence | Open follow-ups |
| --- | --- | --- | --- |
| [US1-AS1](spec.md#L38) | PARTIAL | Advice/fire/location/action helper exists; real agent output path does not use it. | AUD-018-006, AUD-018-036 |
| [US1-AS2](spec.md#L39) | PARTIAL | Upgrade helper accepts a predecessor but does not prove Risk-triggered approved supersession. | AUD-018-006, AUD-018-009, AUD-018-024 |
| [US1-AS3](spec.md#L40) | PARTIAL | Downgrade does not check prior tier or verified IC approval. | AUD-018-003, AUD-018-008, AUD-018-009 |
| [US1-AS4](spec.md#L41) | PARTIAL | All-clear helper not triggered by authorized stand-down or terminal-chain enforcement. | AUD-018-003, AUD-018-009 |
| [US2-AS1](spec.md#L55) | PARTIAL | Manual role API exists; no framework-aware automatic incident assignment/COP. | AUD-018-014, AUD-018-023 |
| [US2-AS2](spec.md#L56) | PARTIAL | Level changes but shared multi-agency operations are not established. | AUD-018-014, AUD-018-016 |
| [US2-AS3](spec.md#L57) | CONFLICT | Level 3 guard unused; NCM is described elsewhere as unbuilt/future, not formally removed here. | AUD-018-014, AUD-018-016, AUD-018-038 |
| [US2-AS4](spec.md#L58) | PARTIAL | Structure endpoint lacks level/full contract and incident COP does not consume it. | AUD-018-023, AUD-018-032 |
| [US3-AS1](spec.md#L72) | PARTIAL | Authority/rationale required as strings, other required Decision metadata optional and authority unverified. | AUD-018-001, AUD-018-011 |
| [US3-AS2](spec.md#L73) | PARTIAL | Warning transition records state but no Communication handoff/timeframe/routes/shelters. | AUD-018-012 |
| [US3-AS3](spec.md#L74) | PARTIAL | Aggregate progress update does not prioritize or allocate vulnerable transport. | AUD-018-010, AUD-018-012 |
| [US3-AS4](spec.md#L75) | PARTIAL | Shelter totals cannot represent all shelter welfare/vulnerability obligations. | AUD-018-011, AUD-018-012 |
| [US3-AS5](spec.md#L76) | PARTIAL | Safe return and completion can be asserted without certification or phased execution. | AUD-018-011, AUD-018-012 |
| [US3-AS6](spec.md#L77) | PARTIAL | Shelter-in-place rationale exists; ongoing monitoring/reassessment not connected. | AUD-018-012, AUD-018-013 |
| [US4-AS1](spec.md#L91) | PARTIAL | Non-incident context exists; Prevention risk/mitigation/risk-reduction integration does not. | AUD-018-019, AUD-018-020 |
| [US4-AS2](spec.md#L92) | PARTIAL | Simulation is retained; readiness, pre-positioning and warning tests are not phase-driven. | AUD-018-020 |
| [US4-AS3](spec.md#L93) | PARTIAL | Response agents exist; concurrent recovery planning not initiated. | AUD-018-018, AUD-018-020 |
| [US4-AS4](spec.md#L94) | PARTIAL | Overlap flag does not implement managed concurrent operations or phase exit. | AUD-018-018, AUD-018-020 |
| [US5-AS1](spec.md#L108) | PARTIAL | API groups 21 slots; actual coordinator UI is not connected to the incident tracker. | AUD-018-021, AUD-018-023 |
| [US5-AS2](spec.md#L109) | PARTIAL | No required recommendation-to-principle evidence; optional safety branch permits unchecked output. | AUD-018-022 |
| [US5-AS3](spec.md#L110) | PARTIAL | Input-summary field and raw community projection do not provide local prioritization/feedback. | AUD-018-022, AUD-018-023 |
| [US5-AS4](spec.md#L111) | PARTIAL | Latest-value replacement is not longitudinal tracking over months. | AUD-018-005, AUD-018-021 |
| [US6-AS1](spec.md#L125) | PARTIAL | Summary reaches Risk but IDs, measurements and freshness/provenance are lost. | AUD-018-024 |
| [US6-AS2](spec.md#L126) | PARTIAL | Drafting exists; impact/action semantics and all ten principles are not enforced in the path. | AUD-018-006, AUD-018-007, AUD-018-024 |
| [US6-AS3](spec.md#L127) | PARTIAL | Translation stages exist; required accessibility and AWS-channel integration remain incomplete. | AUD-018-010, AUD-018-024, AUD-018-033 |
| [US6-AS4](spec.md#L128) | PARTIAL | Unvalidated link storage does not establish warning feedback or overdue detection. | AUD-018-025 |
| [US7-AS1](spec.md#L142) | PARTIAL | Manual capture model exists; required initiation/template/categorization/origin enforcement incomplete. | AUD-018-026, AUD-018-027 |
| [US7-AS2](spec.md#L143) | PARTIAL | Raw tag/status counts lack bounded distinct-event trends and correct unresolved/overdue semantics. | AUD-018-028 |
| [US7-AS3](spec.md#L144) | PARTIAL | Resolution stores free text, not verified originating event and approved change closure. | AUD-018-027, AUD-018-029 |
| [US7-AS4](spec.md#L145) | MISSING | No CI gate invokes the lesson verifier or verifies the change addresses the linked event. | AUD-018-029 |
| [EC-01 Multi-hazard overlap](spec.md#L151) | PARTIAL | Helpers permit chains but do not enforce hazard isolation, branching prevention or overlap display. | AUD-018-002, AUD-018-009, AUD-018-023 |
| [EC-02 Sudden-onset tier skip](spec.md#L152) | PARTIAL | Optional justification check neither requires rationale nor verifies hazard; not wired to warnings. | AUD-018-006, AUD-018-009 |
| [EC-03 Evacuation abandonment](spec.md#L153) | PARTIAL | Replan trigger exists but recomputation/audit/state re-entry incomplete; <=15s outcome unverified. | AUD-018-012, AUD-018-013, AUD-018-037 |
| [EC-04 Concurrent incident phases](spec.md#L154) | PARTIAL | Independent fields exist; operational concurrency and shared-resource tie-breaking are not phase-integrated. | AUD-018-002, AUD-018-018, AUD-018-020, AUD-018-037 |
| [EC-05 Recovery regression](spec.md#L155) | PARTIAL | No baseline-setting API/history; generic cause and no plan reassessment. | AUD-018-021 |
| [EC-06 Contradictory lesson](spec.md#L156) | PARTIAL | Flag/string approval exist; no authenticated IC/admin approval or safe resolved-then-flagged handling. | AUD-018-001, AUD-018-027 |
| [EC-07 IC unavailable](spec.md#L157) | PARTIAL | Single timer and synthetic chain do not implement actual five/fifteen-minute delegation. | AUD-018-008 |

| FR-017 inline acceptance clause | Status | Evidence gap | Follow-up |
| --- | --- | --- | --- |
| (a) Intra-entity Command | PARTIAL | No controlling-entity policy in inspected dispatch path. | AUD-018-016 |
| (b) Cross-entity Coordination | PARTIAL | Agent-target selection is not authorization of organizational semantics. | AUD-018-016 |
| (c) COP relationship distinction | MISSING | Current incident dashboard omits command/coordination relationships. | AUD-018-016, AUD-018-023 |
| (d) Level 2+ multi-agency assertion | MISSING | AIIMS tests accept shape/level without asserting distinct intra/inter-agency links. | AUD-018-016, AUD-018-036 |

## Original Task Coverage

Each original task has exactly one row, including the out-of-order T079 and bold T080-T085 entries. Original checkbox state is copied exactly, not changed to match the review. Evidence describes inspected source/test assertions, never an inferred successful run.

| Original task | Original state | Status | Concrete implementation/test evidence and limit | Open follow-ups |
| --- | --- | --- | --- | --- |
| [T001](tasks.md#L28) | [X] | UNVERIFIED | Current revision confirmed; historical creation from main is not proved by a checkbox. No branch recreated. | AUD-018-039 |
| [T002](tasks.md#L29) | [X] | IMPLEMENTED | [Module](../../infra/modules/recovery-lessons.bicep#L18) authors five containers and required partition keys. Provisioning/TTL/runtime use separate. | AUD-018-005, AUD-018-035 |
| [T003](tasks.md#L30) | [X] | IMPLEMENTED | [Main module reference](../../infra/main.bicep#L801) binds to the [AU-restricted account](../../infra/main.bicep#L580). No deployment claimed. | AUD-018-035, AUD-018-039 |
| [T004](tasks.md#L42) | [X] | IMPLEMENTED | [Incident model](../../packages/domain/src/domain/models/incident.py#L6), [model assertions](../../tests/unit/test_domain_models_aidr.py#L35): additive hazards, phase and level defaults. | - |
| [T005](tasks.md#L43) | [X] | PARTIAL | [Alert fields/validators](../../packages/domain/src/domain/models/public_alert.py#L45) exist; published predecessor and full chain/all-clear invariants not enforced. | AUD-018-006, AUD-018-009 |
| [T006](tasks.md#L44) | [X] | IMPLEMENTED | [SignalCategory](../../packages/domain/src/domain/models/handoff_chain.py#L6) adds both categories; domain tests assert accepted values. Routing separate. | AUD-018-030 |
| [T007](tasks.md#L48) | [X] | IMPLEMENTED | [Role model](../../packages/domain/src/domain/models/aiims_role_assignment.py#L34) includes period/delegation fields and active-state validation. Service history/bootstrapping incomplete. | AUD-018-014, AUD-018-015 |
| [T008](tasks.md#L49) | [X] | IMPLEMENTED | [Stage model](../../packages/domain/src/domain/models/evacuation_stage.py#L48) authors stage, decision, tracking, shelter-in-place and audit fields. Operational guards separate. | AUD-018-011, AUD-018-012 |
| [T009](tasks.md#L50) | [X] | PARTIAL | [21 indicators/model](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L26) exist; nullable coverage/classification and longitudinal enforcement incomplete. | AUD-018-004, AUD-018-021 |
| [T010](tasks.md#L51) | [X] | IMPLEMENTED | [Lesson model](../../packages/domain/src/domain/models/lesson.py#L19) contains specified fields and context validator. Required categorization/update guards separate. | AUD-018-027 |
| [T011](tasks.md#L52) | [X] | PARTIAL | [Context model](../../packages/domain/src/domain/models/pprr_phase_context.py#L15) enforces phase/link timestamp; referenced region/scenario not validated. | AUD-018-019 |
| [T012](tasks.md#L56) | [X] | PARTIAL | [Mapping](../../apps/agents/common/aiims_mapping.py#L16) and later registry exist; no three-tier consultation/bootstrap or Control fallback. | AUD-018-014 |
| [T013](tasks.md#L57) | [X] | PARTIAL | [Transition helpers](../../apps/agents/common/pprr_lifecycle.py#L10) create payloads; overlap is not active managed state and Recovery is terminal. | AUD-018-018, AUD-018-031 |
| [T014](tasks.md#L58) | [X] | PARTIAL | [Validator](../../apps/agents/common/warning_compliance.py#L70) structurally approximates ten principles, not substantive compliance. | AUD-018-007 |
| [T015](tasks.md#L63) | [X] | PARTIAL | [Helpers](../../apps/agents/common/handoffs.py#L70) authored in deprecated module; no active graph recovery/lessons routing. | AUD-018-030 |
| [T016](tasks.md#L67) | [X] | PARTIAL | [Timeline model](../../packages/domain/src/domain/models/timeline_event.py#L7) remains arbitrary payload; docs/builders do not enforce four schemas. | AUD-018-031 |
| [T017](tasks.md#L83) | [X] | PARTIAL | [Builder](../../apps/agents/communication/warning_builder.py#L60) provides labels/icons/templates, but unchecked supersession and disconnected runtime. | AUD-018-006, AUD-018-007, AUD-018-009 |
| [T018](tasks.md#L84) | [X] | PARTIAL | [AWS DTOs](../../apps/agents/communication/models.py#L380) exist; separate runtime PublicAlert has no AWS fields and request requires tier even for all-clear. | AUD-018-006, AUD-018-032 |
| [T019](tasks.md#L85) | [X] | PARTIAL | [App](../../apps/agents/communication/agent.py#L186) calls old pipeline; builder/delegation/tier lifecycle not connected. MAF inspected too. | AUD-018-001, AUD-018-003, AUD-018-006, AUD-018-008, AUD-018-009 |
| [T020](tasks.md#L86) | [X] | MISSING | Runtime pre-publish compliance call absent; [standalone endpoint](../../apps/api/app/api/routes/warning_chain.py#L139) is not that gate. | AUD-018-003, AUD-018-006, AUD-018-007 |
| [T021](tasks.md#L87) | [X] | PARTIAL | [Multilingual pipeline](../../apps/agents/communication/pipeline.py#L298) exists; complete population/accommodation integration absent. | AUD-018-010 |
| [T022](tasks.md#L88) | [X] | PARTIAL | Template/safety fallback exists; [persistence failure](../../apps/agents/communication/pipeline.py#L542) logs without warning replay queue. | AUD-018-005, AUD-018-006 |
| [T023](tasks.md#L89) | [X] | PARTIAL | [Chain endpoint](../../apps/api/app/api/routes/warning_chain.py#L30) returns ancestors/list without documented status/time/envelope/full-chain behavior. | AUD-018-009, AUD-018-032 |
| [T024](tasks.md#L90) | [X] | PARTIAL | [CAP endpoint](../../apps/api/app/api/routes/warning_chain.py#L104) exists; unsafe XML interpolation and incomplete standards semantics. | AUD-018-033 |
| [T025](tasks.md#L91) | [X] | PARTIAL | [Compliance endpoint](../../apps/api/app/api/routes/warning_chain.py#L139) exists; flags, names, elapsed measurement and substantive checks incomplete. | AUD-018-007, AUD-018-032 |
| [T026](tasks.md#L92) | [X] | MISSING | No `warning_compliance_rate` or `tier_transition_latency` emitter in inspected API/agent sources. | AUD-018-034 |
| [T027](tasks.md#L108) | [X] | PARTIAL | [AIIMS service](../../apps/api/app/services/aiims_service.py#L31) has CRUD/coverage helpers; Level 3 guard unused, updates unvalidated/history-losing. | AUD-018-014, AUD-018-015 |
| [T028](tasks.md#L109) | [X] | PARTIAL | [Routes](../../apps/api/app/api/routes/aiims.py#L36) registered; actor/scope/status/structure contracts incomplete. | AUD-018-001, AUD-018-002, AUD-018-032 |
| [T029](tasks.md#L110) | [X] | MISSING | No incident-start framework consultation/role-assignment consumer found; defaults/registry are not startup. | AUD-018-014, AUD-018-016 |
| [T030](tasks.md#L111) | [X] | PARTIAL | [Level mutation](../../apps/api/app/services/aiims_service.py#L99) records an event, not shared COP or guarded six-function Level 3. | AUD-018-014, AUD-018-016, AUD-018-023 |
| [T031](tasks.md#L112) | [X] | PARTIAL | Static mapping/registry exists, but incident-assignment failure fallback and stale COP state are not connected. | AUD-018-005, AUD-018-014 |
| [T032](tasks.md#L113) | [X] | MISSING | Trigger payload builder exists, but no Level 2+ closure subscriber creates the required capture event/session. | AUD-018-026 |
| [T033](tasks.md#L114) | [X] | MISSING | No `aiims_role_coverage_ratio` emitter located. | AUD-018-034 |
| [T034](tasks.md#L130) | [X] | PARTIAL | [State logic](../../apps/agents/evacuation/stages.py#L20) works for named transitions; Return re-entry uncounted and event/operational guards incomplete. | AUD-018-011, AUD-018-013, AUD-018-031 |
| [T035](tasks.md#L131) | [X] | PARTIAL | [Route DTOs](../../apps/api/app/api/routes/evacuation.py#L35) provide partial moved request handling; no complete stage-aware agent request/response integration. | AUD-018-012, AUD-018-032 |
| [T036](tasks.md#L132) | [X] | PARTIAL | [Stage routes](../../apps/api/app/api/routes/evacuation.py#L84) store metadata; actual Communication/transport/welfare/phased-return operations absent. | AUD-018-010, AUD-018-011, AUD-018-012 |
| [T037](tasks.md#L133) | [X] | PARTIAL | [Shelter-in-place transition](../../apps/agents/evacuation/stages.py#L37) records rationale; no ongoing monitoring or automatic reevaluation. | AUD-018-012, AUD-018-013 |
| [T038](tasks.md#L134) | [X] | PARTIAL | Type literals/optional input exist; no immediate/pre-warned timing or warning-tier-skip integration. | AUD-018-009, AUD-018-012 |
| [T039](tasks.md#L135) | [X] | PARTIAL | [Six endpoints](../../apps/api/app/api/routes/evacuation.py#L84) exist but fields/errors/auth/ownership and operational effects differ. | AUD-018-001, AUD-018-002, AUD-018-011, AUD-018-032 |
| [T040](tasks.md#L136) | [X] | MISSING | No local stage transition buffer/circuit-breaker/audit-before-Cosmos path in inspected controllers. | AUD-018-005, AUD-018-013 |
| [T041](tasks.md#L137) | [X] | MISSING | No `evacuation_stage_duration` emitter located. | AUD-018-034 |
| [T042](tasks.md#L153) | [X] | PARTIAL | [PPRR service](../../apps/api/app/services/pprr_service.py#L30) mutates phase/events and contexts; real overlap/transfer incomplete. | AUD-018-018, AUD-018-019 |
| [T043](tasks.md#L154) | [X] | CONFLICT | [Runtime PUT](../../apps/api/app/api/routes/pprr.py#L89) follows task but contract says POST; context filters/response fields also differ. | AUD-018-019, AUD-018-032 |
| [T044](tasks.md#L155) | [X] | PARTIAL | Risk/planning functions exist independently; no Prevention orchestration with mitigation/risk-reduction outputs. | AUD-018-020 |
| [T045](tasks.md#L156) | [X] | PARTIAL | Simulation and plan functionality retained; no complete phase-driven rehearsal/readiness/pre-positioning/warning-test flow. | AUD-018-019, AUD-018-020 |
| [T046](tasks.md#L157) | [X] | MISSING | Transition events do not activate recovery agents/planning concurrently with Response. | AUD-018-018, AUD-018-020 |
| [T047](tasks.md#L158) | [X] | PARTIAL | [Overlap flag](../../apps/api/app/services/pprr_service.py#L30) exists; active overlap lifecycle and cross-incident behavior not implemented end to end. | AUD-018-018, AUD-018-020 |
| [T048](tasks.md#L159) | [X] | MISSING | No phase-transition queue/replay consumer located. | AUD-018-005 |
| [T049](tasks.md#L160) | [X] | MISSING | No `pprr_phase_transition_count` emitter located. | AUD-018-034 |
| [T050](tasks.md#L176) | [X] | PARTIAL | [Recovery service](../../apps/api/app/services/recovery_service.py#L27) supplies slots/updates; history, real regression/staleness/principle/SLA work incomplete. | AUD-018-021, AUD-018-022, AUD-018-025 |
| [T051](tasks.md#L177) | [X] | PARTIAL | [Recovery routes](../../apps/api/app/api/routes/recovery.py#L43) registered; body/response/UI/authorization obligations incomplete. | AUD-018-001, AUD-018-023, AUD-018-032 |
| [T052](tasks.md#L178) | [X] | PARTIAL | Supplied low coverage is rejected, but omitted coverage/direct classification bypasses the policy. | AUD-018-004 |
| [T053](tasks.md#L179) | [X] | PARTIAL | `linked_alert_id` stored; no validated origin or 24-hour deadline/alerting. | AUD-018-025 |
| [T054](tasks.md#L180) | [X] | PARTIAL | Later [analysis endpoints](../../apps/agents/monitoring/agent.py#L530) exist; requested three-agent recovery mode is not driven by incident phase. | AUD-018-020, AUD-018-021, AUD-018-022 |
| [T055](tasks.md#L181) | [X] | PARTIAL | [Recovery analysis](../../apps/agents/monitoring/indicator_analysis.py#L80) can return unvalidated LLM content; community summaries do not prove safety/review. | AUD-018-022 |
| [T056](tasks.md#L182) | [X] | MISSING | Dashboard returns raw latest data without unavailable-source/staleness behavior. | AUD-018-005, AUD-018-021 |
| [T057](tasks.md#L183) | [X] | MISSING | No `recovery_indicator_update_frequency` emitter located. | AUD-018-034 |
| [T058](tasks.md#L201) | [X] | PARTIAL | [Monitoring handoff](../../apps/agents/monitoring/agent.py#L89) carries summary but loses source IDs/provenance for prediction. | AUD-018-024 |
| [T059](tasks.md#L202) | [X] | PARTIAL | [Prediction code](../../apps/agents/risk_assessment/pipeline.py#L326) exists; synthetic intake/scale mismatch undermine connected AIDR prediction. | AUD-018-017, AUD-018-024 |
| [T060](tasks.md#L203) | [X] | PARTIAL | Legacy multilingual/safety stages exist; AWS principles/accessibility and complete TWS integration are not assured. | AUD-018-006, AUD-018-007, AUD-018-010, AUD-018-024 |
| [T061](tasks.md#L204) | [X] | PARTIAL | Link field is not a connected warning-response loop or SLA consumer. | AUD-018-025 |
| [T062](tasks.md#L220) | [X] | PARTIAL | [Lessons service](../../apps/api/app/services/lessons_service.py#L19) supports manual CRUD; auto-trigger, trend/closure and durable state incomplete. | AUD-018-026, AUD-018-027, AUD-018-028 |
| [T063](tasks.md#L221) | [X] | PARTIAL | [Lessons routes](../../apps/api/app/api/routes/lessons.py#L53) exist; auth, categories, pagination, verifier and response contracts incomplete. | AUD-018-001, AUD-018-027, AUD-018-029, AUD-018-032 |
| [T064](tasks.md#L222) | [X] | PARTIAL | Scenario field exists; no actual ExerciseReport/metric correlation and capture linkage. | AUD-018-026, AUD-018-027 |
| [T065](tasks.md#L223) | [X] | PARTIAL | Contradiction flag/approver string exist; no trusted approval or safe retrospective contradiction flow. | AUD-018-001, AUD-018-027 |
| [T066](tasks.md#L224) | [X] | MISSING | No located workflow/script invokes lesson verification or enforces PR change linkage. | AUD-018-029 |
| [T067](tasks.md#L225) | [X] | MISSING | Dictionary storage has no local buffer/sync or durable failure isolation. | AUD-018-005 |
| [T068](tasks.md#L226) | [X] | MISSING | No `lesson_resolution_time` emitter located. | AUD-018-034 |
| [T069](tasks.md#L238) | [X] | UNVERIFIED | No all-capability fault-injection execution record; several advertised degraded paths absent in source. | AUD-018-005, AUD-018-036, AUD-018-039 |
| [T070](tasks.md#L242) | [X] | PARTIAL | Existing Monitoring requirements cover thresholds; explicit AIDR role/TWS spec amendment incomplete. | AUD-018-038 |
| [T071](tasks.md#L243) | [X] | PARTIAL | Risk spec already defines four AIDR risk levels; explicit TWS mapping/runtime alignment incomplete. | AUD-018-017, AUD-018-038 |
| [T072](tasks.md#L244) | [X] | PARTIAL | [Resource YAML](../../apps/agents/maf_runtime/agents/resource_allocation.yaml#L7) uses AIIMS language; pipeline lacks phase-specific reconstruction allocation. | AUD-018-020, AUD-018-038 |
| [T073](tasks.md#L245) | [X] | PARTIAL | Hub has personas/PPRR deferral, not full required structural/Shared Responsibility alignment. | AUD-018-038 |
| [T074](tasks.md#L246) | [X] | MISSING | No dedicated role-mapping sections located in the six specified dependent specifications. | AUD-018-038 |
| [T075](tasks.md#L250) | [X] | PARTIAL | [Health endpoints](../../apps/api/app/api/routes/health.py#L46) exist but only inspect dictionaries; latency/outage meaning unverified. | AUD-018-034, AUD-018-037 |
| [T076](tasks.md#L251) | [X] | UNVERIFIED | No execution evidence for seven emitted metrics; source search found no required emitters. | AUD-018-034, AUD-018-039 |
| [T077](tasks.md#L255) | [X] | UNVERIFIED | AU-only authored account/module binding inspected; actual data-store residency and replication not queried. | AUD-018-035, AUD-018-039 |
| [T078](tasks.md#L256) | [X] | PARTIAL | FastAPI routes register, but response typing/contract and GeoJSON/CAP/EDXL conformance incomplete. | AUD-018-032, AUD-018-033 |
| [T079](tasks.md#L268) | [X] | UNVERIFIED | Quickstart read fully, not executed; Python/export/test-path/setup drift prevents claiming current success. | AUD-018-039 |
| [T080](tasks.md#L260) | [X] | PARTIAL | [EDXL serializer](../../apps/agents/communication/edxl_serialiser.py#L16), endpoint and relocated warning-test assertions exist; standards/delivery semantics incomplete. | AUD-018-033 |
| [T081](tasks.md#L261) | [X] | PARTIAL | All six contract test files exist, but weak/different response assertions do not validate the authored contracts. | AUD-018-032, AUD-018-036 |
| [T082](tasks.md#L262) | [X] | MISSING | Named suite absent; bounded integration search found no replacement covering CRUD, keys and TTL for all five AIDR containers. | AUD-018-035 |
| [T083](tasks.md#L263) | [X] | PARTIAL | [Four scenario classes](../../tests/simulation/test_aidr_scenarios.py#L30) exist but bushfire creates no warnings and other flows check labels/selected responses. | AUD-018-036 |
| [T084](tasks.md#L264) | [X] | PARTIAL | [Benchmarks](../../tests/benchmark/test_aidr_performance.py#L1) contain six timing targets, sequential recovery loop, no complete concurrent/extra task-budget proof. | AUD-018-037 |
| [T085](tasks.md#L59) | [X] | PARTIAL | [Seven-group helper](../../apps/agents/common/vulnerable_populations.py#L10) omits Constitution groups and is disconnected from operational handling. | AUD-018-010 |

## Clarifications, Appendices, and Dependencies

The ten clarification entries are each covered below; entity bullets, assumptions and later scope/authority additions are not silently excluded.

| Original amendment or clarification | Status | Assessment | Follow-up |
| --- | --- | --- | --- |
| Session 1 Q1: budgets, concurrency, health, metrics | PARTIAL | All 15 NFRs and seven metrics assessed above; measurements UNVERIFIED and metrics absent. | AUD-018-034, AUD-018-037 |
| Session 1 Q2: sudden-onset tier skipping | PARTIAL | Optional helper justification is not required, hazard-validated, connected or audited at issuance. | AUD-018-009 |
| Session 1 Q3: complete 21-indicator set | IMPLEMENTED | Exact 7/5/5/4 catalogue/initialization exists; methodology/history separate. | AUD-018-021 |
| Session 1 Q4: IC delegation, 5/15-minute deadline | PARTIAL | Actual chain and tier-aware timer not implemented by either inspected runtime path. | AUD-018-008 |
| Session 1 Q5: significant incident/exercise definition | PARTIAL | Definition authored, but mandatory auto-capture/explicit IC/optional Level 1 flows not wired. | AUD-018-026 |
| Session 2 Q1: additive domain model alignment | PARTIAL | New models and additive fields exist; runtime uses a separate warning model and no stable exported AIDR package surface is documented. | AUD-018-006, AUD-018-039 |
| Session 2 Q2: three independent severity scales | CONFLICT | Domain retains independence; active Risk prompt uses different risk/incident-level sets. | AUD-018-017 |
| Session 2 Q3: PPRR orthogonal to incident status | IMPLEMENTED | Separate optional field and non-incident context exist; transition behavior is separately incomplete. | AUD-018-018, AUD-018-019 |
| Session 2 Q4: warning timeout supersedes spec 008 | PARTIAL | Reciprocal authority pointer exists; code retains the single timeout. Non-warning default must be preserved. | AUD-018-008, AUD-018-038 |
| Session 2 Q5: extended vulnerable populations | PARTIAL | Extensions appear in constants but Constitution groups and connected accommodations are incomplete. | AUD-018-010 |
| [PER-046](spec.md#L321) | UNVERIFIED | Cross-reference exists; generic former-role descriptions do not establish named/date SME validation or all persona-contract fields. | AUD-018-040 |
| [PER-047](spec.md#L322) | UNVERIFIED | Actor-catalogue reference is authored; actor existence does not prove consultation or human validation. | AUD-018-040 |
| [PER-048](spec.md#L323) | IMPLEMENTED | Explicit non-AU placeholder and D-009/SME preconditions retained; validation not claimed here. | AUD-018-040 |
| [HYP-016](spec.md#L329) | UNVERIFIED | Per-spec outcome and every-change consultation not established; named stub not found, and portfolio structural score is not that evidence. | AUD-018-040 |
| [SCP-052](spec.md#L335) | IMPLEMENTED | PH/JP/BD variants explicitly deferred behind constitutional, data-sharing and calibration approvals. No implementation added to scope. | AUD-018-040 |
| [SCP-053](spec.md#L336) | IMPLEMENTED | This spec does not authorize constitutional changes; current bounded model carve-out does not relax data persistence. | AUD-018-039, AUD-018-040 |
| [SCP-054](spec.md#L337) | CONFLICT | Authored arbitration/deferral rule includes self-deferral to 018; clarify with the explicit authority statements without widening scope. | AUD-018-038, AUD-018-040 |
| [Recovery authority](spec.md#L342) | IMPLEMENTED | Reciprocal 001/011 deferrals and feature-028 decision document 018 ownership; runtime phase-exit criteria incomplete. | AUD-018-018, AUD-018-038 |
| [Warning-timeout authority](spec.md#L343) | CONFLICT | Ownership reciprocal in spec 008; local FR-017 reference names a different requirement, and code does not enforce timeout. | AUD-018-008, AUD-018-040 |

| Assumption/dependency | Status | Assessment and compatibility boundary | Follow-up |
| --- | --- | --- | --- |
| Constitution v1.1.0 baseline | CONFLICT | Historical baseline remains readable, but current constitution is 1.2.0; document bounded amendment applicability, not blanket non-AU permission. | AUD-018-039 |
| Six handbooks under historical location | PARTIAL | All six originals relocated; update links, not an assertion that guidance is absent. | AUD-018-038, AUD-018-039 |
| Addenda to 001/008/009/010/011/012 | PARTIAL | Later persona/authority edits exist; complete per-agent AIDR addenda do not. | AUD-018-038 |
| Existing agents in recovery mode, no mandatory new agent | PARTIAL | Related recovery services exist, but no phase-driven three-agent operation. Preserve this architectural boundary. | AUD-018-020, AUD-018-030 |
| Lessons are platform-wide, not a dedicated agent | PARTIAL | Manual service exists; event integration and CI gate absent. | AUD-018-026, AUD-018-029 |
| Manual community-response entry initially acceptable | PARTIAL | Update API exists; manual mode still requires validated linkage and 24-hour overdue handling. | AUD-018-025 |
| Spec-007 simulation/rehearsal reuse | PARTIAL | Simulation capabilities exist; PPRR integration and AIDR tenant separation are not inferred from them. | AUD-018-002, AUD-018-020 |
| Preserve spec-009 zones/routing/transport | PARTIAL | Existing agent/pipeline retained, but five stages not connected and current replan contains placeholders. | AUD-018-012, AUD-018-013 |
| Preserve spec-012 risk scale and IC editorial tier choice | CONFLICT | Source models preserve scales; new prompt diverges. | AUD-018-017 |

## Design and Contract Obligations

| Design input | Status | Evidence-based assessment | Follow-up |
| --- | --- | --- | --- |
| R-001 non-incident phase context | PARTIAL | Context exists; validation, target incident Response update and timeline incomplete. | AUD-018-019 |
| R-002 all-capability degradation | PARTIAL | Existing template/static helpers do not prove queues, replay, stale views or fault isolation. | AUD-018-005 |
| R-003 manual indicators and alerting | PARTIAL | Manual updates exist; no 24-hour warning deadline consumer. | AUD-018-025 |
| R-004 singly linked non-branching warnings | PARTIAL | Links exist, no atomic chain invariants/full-chain traversal. | AUD-018-009 |
| R-005 three-tier AIIMS consultation | PARTIAL | Models/registry exist, not incident startup consultation. | AUD-018-014 |
| R-006 existing-agent recovery mode | PARTIAL | Independent analysis/catalogue/handover functions do not activate recovery agents. | AUD-018-020, AUD-018-022 |
| R-007 lessons service, trigger and PR gate | PARTIAL | Manual service exists; trigger and gate not connected. | AUD-018-026, AUD-018-029 |
| R-008 feedback subset and warning links | PARTIAL | No minimum response set, validated alert relation or 24-hour completeness. | AUD-018-025 |
| R-009 OpenAPI/CAP/GeoJSON/EDXL | PARTIAL | Routes and XML artifacts exist, not complete typed/standard-compliant delivery. | AUD-018-032, AUD-018-033 |
| R-010 audited evacuation state machine | PARTIAL | Normal transitions/re-entry helper exist; Return re-entry count, safety and operations incomplete. | AUD-018-011, AUD-018-013, AUD-018-031 |
| R-011 independent incident level | PARTIAL | Field/default implemented; escalation behavior/coverage and prompt values diverge. | AUD-018-014, AUD-018-017 |
| R-012 model-level privacy/LGA granularity | PARTIAL | Supplied low coverage check only; missing coverage/classification/geography gaps. | AUD-018-004 |
| R-013 five containers/keys/exercise partition | PARTIAL | Containers and keys authored; adapters, exercise serialization and retention integration unproved. | AUD-018-005, AUD-018-035 |
| E-001 Incident / Incident Level / PPRR entity | IMPLEMENTED | Additive fields, defaults and hazard expansion in domain model; operational transitions separately incomplete. | AUD-018-018 |
| E-002 Warning/PublicAlert entity | PARTIAL | Additive model fields exist; chain-reference validators and runtime model adoption incomplete. | AUD-018-006, AUD-018-009 |
| E-003 HandoffChainDefinition | PARTIAL | Categories present, active AIDR routing absent. | AUD-018-030 |
| N-001 AIIMS Role Assignment entity | PARTIAL | Model fields/initial uniqueness present; periods, active coverage and delegation enforcement incomplete. | AUD-018-014, AUD-018-015 |
| N-002 Evacuation Stage entity | PARTIAL | All fields authored; operational guards/validated updates/re-entry history incomplete. | AUD-018-011, AUD-018-012, AUD-018-013 |
| N-003 Recovery Tracker entity | PARTIAL | 21 slots and principle-name validator exist; privacy, history, regression response and community workflow incomplete. | AUD-018-004, AUD-018-021, AUD-018-022 |
| N-004 Lesson entity | PARTIAL | Model authored; optional categories/dates and unchecked state changes conflict with requirements. | AUD-018-027 |
| N-005 PPRR Context entity | PARTIAL | Restricted phase/link timestamp validator exists, but references/transfer behavior incomplete. | AUD-018-019 |
| Timeline payload: PPRR transition | PARTIAL | Builder supplies required fields; no enforced schema/durable authorized overlap lifecycle. | AUD-018-018, AUD-018-031 |
| Timeline payload: incident level change | PARTIAL | Event is emitted, but level coverage and shared schema not enforced. | AUD-018-014, AUD-018-031 |
| Timeline payload: evacuation transition | PARTIAL | API event exists with different names and missing plan/re-entry count. | AUD-018-013, AUD-018-031 |
| Timeline payload: lessons-capture trigger | PARTIAL | Builder only; no mandatory operational producer/subscriber. | AUD-018-026, AUD-018-031 |
| Model registration/public exports | CONFLICT | Named initializer absent; alternate `ama_domain` is explicitly separate. Direct namespace-module imports are not declared broken; document/implement approved public surface. | AUD-018-039 |

### Six API Contract Deviations

| Contract | Status | Concrete deviations from authored narrative | Follow-up |
| --- | --- | --- | --- |
| Warning | PARTIAL | No create operation in registered alert/chain routers. Chain returns list/ancestors without status/published time/closed envelope. Compliance returns `is_compliant`/`errors`, not `aws_compliant`/`issues`/elapsed time. XML/auth/publication gaps assessed separately. | AUD-018-003, AUD-018-006, AUD-018-009, AUD-018-032, AUD-018-033 |
| AIIMS | PARTIAL | Create 200 not 201; structure uses assignments/missing-functions, omits incident level/keyed structure/all-functions flag. Notes/delegation/update period handling incomplete. Level change returns summary rather than updated Incident, with unused Level 3 guard. | AUD-018-014, AUD-018-015, AUD-018-032 |
| Evacuation | PARTIAL | `plan_id` versus `evacuation_plan_id`; `rationale` versus `transition_rationale`; 200 versus 201; 409 versus 422 invalid transitions. Withdrawal omits total, shelter omits IDs/welfare/status, return uses `certifier`/`rate` aliases. | AUD-018-011, AUD-018-012, AUD-018-032 |
| PPRR | CONFLICT | Task/runtime PUT versus contract POST transfer. `rationale` differs; response omits promised timestamps/overlap phases; context filters ignored; transfer does not enter Response. | AUD-018-018, AUD-018-019, AUD-018-032 |
| Recovery | PARTIAL | Initialization body ignored, status 200 not 201; dashboard environments are lists rather than count-bearing objects; update returns a summary and omits editable unit/baseline/target/source; batch uses `updates`, not `indicators`; community view lacks promised non-expert content/input link/staleness. | AUD-018-021, AUD-018-022, AUD-018-023, AUD-018-032 |
| Lessons | CONFLICT | Contract's optional categories contradict FR-039; 200 not 201; no pagination/time-window parameters/overdue metric; `resolved_by` not bound; verifier expects `pr_description`, not `lesson_ids`; no event consumer or CI gate. | AUD-018-026, AUD-018-027, AUD-018-028, AUD-018-029, AUD-018-032 |

## Checklist and Review Evidence Assessment

The following rows preserve original authoring states. A reviewed question can be resolved by an authored decision without establishing that its implementation, human review or measured outcome succeeded. Mandatory P1 detailed items remain open pending the named remediation/owner decisions.

### Detailed AIDR Checklist: 98 Original Open Items

All original CHK states are `[ ]` in [the detailed checklist](checklists/aidr-guidance.md#L13). Each item receives a separate assessment; narrative decisions are not retrospective checkbox completion.

| Item | Original state | Status | Assessment / evidence | Open follow-ups |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | IMPLEMENTED | Spec/Companion enumerate exactly three tiers and colors; runtime integration separate. | AUD-018-006 |
| CHK002 | [ ] | PARTIAL | Nested model stated; meaningful location/action criteria and enforced runtime outputs incomplete. | AUD-018-006, AUD-018-007 |
| CHK003 | [ ] | PARTIAL | Six icons/other fallback present; applicability and graphical output semantics incomplete. | AUD-018-006, AUD-018-033 |
| CHK004 | [ ] | PARTIAL | R-004 defines supersession but downgrade direction, prior-tier references and approval unguarded. | AUD-018-009 |
| CHK005 | [ ] | PARTIAL | R-004 terminal all-clear described; resolution authority and chain closure not enforced. | AUD-018-003, AUD-018-009 |
| CHK006 | [ ] | PARTIAL | Ten names/checks exist, not individual substantive compliance evidence. | AUD-018-007 |
| CHK007 | [ ] | PARTIAL | Group helper describes accommodations but omits groups and has no controller integration. | AUD-018-010 |
| CHK008 | [ ] | PARTIAL | R-002 covers LLM/store failure, not a complete stale/unavailable hazard warning policy. | AUD-018-007, AUD-018-024, AUD-018-038 |
| CHK009 | [ ] | PARTIAL | Icon fields exist; graphical availability and non-graphical fallback unspecified operationally. | AUD-018-033, AUD-018-038 |
| CHK010 | [ ] | PARTIAL | R-004 precisely defines non-branching chain, but actual chain invariant is not enforced. | AUD-018-009 |
| CHK011 | [ ] | PARTIAL | Tier presence is not measurable life-saving content per handbook. | AUD-018-007 |
| CHK012 | [ ] | PARTIAL | Two content blocks do not establish broader community-warning context. | AUD-018-007 |
| CHK013 | [ ] | PARTIAL | Existing six-language pipeline retained; per-group scope/quality/human approval incomplete. | AUD-018-010, AUD-018-039 |
| CHK014 | [ ] | PARTIAL | Tiered duration stated, actual timer start/persistence/authority chain not defined and enforced. | AUD-018-008 |
| CHK015 | [ ] | PARTIAL | Edge requires independent chains/COP overlap; implementation lacks both guarantees. | AUD-018-009, AUD-018-023 |
| CHK016 | [ ] | PARTIAL | Skip fields/justification helper exist; required sudden-onset evidence not enforced. | AUD-018-009 |
| CHK017 | [ ] | PARTIAL | Legacy correction/reference exists; approved retraction semantics across AWS chains unresolved. | AUD-018-009, AUD-018-033, AUD-018-038 |
| CHK018 | [ ] | PARTIAL | Area strings/audience labels do not define validated geographic warning boundary. | AUD-018-009, AUD-018-033 |
| CHK019 | [ ] | PARTIAL | IC editorial authority stated; disagreement workflow/version reapproval not connected. | AUD-018-003, AUD-018-008, AUD-018-038 |
| CHK020 | [ ] | CONFLICT | Exactly-one-function versus dual-role quickstart; five defaults versus six-role success target. | AUD-018-014, AUD-018-038 |
| CHK021 | [ ] | PARTIAL | Update endpoint exists; invalid mutation/history/reactivation behavior incomplete. | AUD-018-015 |
| CHK022 | [ ] | PARTIAL | Level behavior described, but actual COP lacks level-specific structure/sharing. | AUD-018-014, AUD-018-023 |
| CHK023 | [ ] | PARTIAL | Level descriptions exist; objective escalation/demotion criteria and enforcement not complete. | AUD-018-014, AUD-018-038 |
| CHK024 | [ ] | CONFLICT | N-001 Level-3-only policy conflicts with SC-002 all-active six functions. | AUD-018-014, AUD-018-038 |
| CHK025 | [ ] | PARTIAL | FR-017 and handbook distinguish semantics; dispatch does not. | AUD-018-016 |
| CHK026 | [ ] | PARTIAL | Four FR-017 criteria authored; enforcement and behavioral tests incomplete. | AUD-018-016, AUD-018-036 |
| CHK027 | [ ] | CONFLICT | NCM required in US2, described as unbuilt/future in presentation, no agreed exchange contract inspected. | AUD-018-016, AUD-018-038 |
| CHK028 | [ ] | PARTIAL | R-005 explains three tiers clearly; no runtime consultation/bootstrap. | AUD-018-014 |
| CHK029 | [ ] | PARTIAL | N-002 fields enumerate outputs; transition controllers do not require/produce them. | AUD-018-011, AUD-018-012 |
| CHK030 | [ ] | PARTIAL | Type/approach/scope enums present; API permits omission and no combinations/authority policy. | AUD-018-011, AUD-018-038 |
| CHK031 | [ ] | PARTIAL | Warning timeframe field exists; hazard-specific adequate lead-time policy and delivery not enforced. | AUD-018-012, AUD-018-037, AUD-018-038 |
| CHK032 | [ ] | PARTIAL | Moved/total model fields exist; API progress and live route/transport integration incomplete. | AUD-018-012 |
| CHK033 | [ ] | PARTIAL | Aggregate capacity/occupancy fields do not cover each shelter's welfare/accessibility. | AUD-018-011, AUD-018-012 |
| CHK034 | [ ] | PARTIAL | Safety boolean/certifier exist but no return gate or defined certification evidence. | AUD-018-011, AUD-018-038 |
| CHK035 | [ ] | PARTIAL | Monitoring interval field unused; no scheduled shelter-in-place exit/reassessment. | AUD-018-012, AUD-018-013 |
| CHK036 | [ ] | PARTIAL | R-010 defines re-entry; Return re-entry permitted but uncounted and replan disconnected. | AUD-018-013 |
| CHK037 | [ ] | PARTIAL | Animal group names/needs exist; actual transport/shelter/reunification support not connected. | AUD-018-010, AUD-018-012 |
| CHK038 | [ ] | PARTIAL | Partial scope literal is not partial-failure operational handling. | AUD-018-012, AUD-018-013, AUD-018-038 |
| CHK039 | [ ] | PARTIAL | Multiple stage records possible; hazard/area isolation and resource conflict behavior not demonstrated. | AUD-018-002, AUD-018-012, AUD-018-020 |
| CHK040 | [ ] | PARTIAL | Required Warning-to-Communication coordination is not a stage side effect. | AUD-018-006, AUD-018-012 |
| CHK041 | [ ] | PARTIAL | Prevention capabilities named; phase-specific input/output/owner integration absent. | AUD-018-020, AUD-018-038 |
| CHK042 | [ ] | PARTIAL | Preparedness functions bundled; individual connected outcomes not tested. | AUD-018-020, AUD-018-036 |
| CHK043 | [ ] | PARTIAL | R-006 identifies recovery modes; no Response-onset activation. | AUD-018-020 |
| CHK044 | [ ] | PARTIAL | Authorizer/overlap fields exist; real authorization, triggers and managed completion absent. | AUD-018-001, AUD-018-018 |
| CHK045 | [ ] | PARTIAL | Single phase plus overlap payload chosen; active overlap representation/readback incomplete. | AUD-018-018 |
| CHK046 | [ ] | PARTIAL | R-001 context decision implemented structurally; reference/transfer validation incomplete. | AUD-018-019 |
| CHK047 | [ ] | PARTIAL | All 21 names present; individual methods/sources/directions/cadences unresolved. | AUD-018-021, AUD-018-038 |
| CHK048 | [ ] | PARTIAL | Input field and public projection do not define a governed community-led workflow. | AUD-018-022, AUD-018-023 |
| CHK049 | [ ] | PARTIAL | Community API exists; safe, accessible non-expert entry point and input link not connected. | AUD-018-004, AUD-018-023 |
| CHK050 | [ ] | PARTIAL | Principle-name validator permits none; recommendation-level assessment/human review absent. | AUD-018-022 |
| CHK051 | [ ] | PARTIAL | Generic baseline comparison without configurable baselines/history/cause/reassessment. | AUD-018-021 |
| CHK052 | [ ] | PARTIAL | Parallel recovery promise consistent in prose but not in phase-driven execution. | AUD-018-018, AUD-018-020 |
| CHK053 | [ ] | PARTIAL | Six elements named; incomplete inter-element provenance and feedback. | AUD-018-024, AUD-018-025 |
| CHK054 | [ ] | PARTIAL | Translation and accessibility flags do not ensure interpretation/audio/visual/sign-language support. | AUD-018-010 |
| CHK055 | [ ] | PARTIAL | R-008 subset approach lacks a minimum validated response set per warning. | AUD-018-025, AUD-018-038 |
| CHK056 | [ ] | PARTIAL | R-003/R-008 explicitly permit manual entry; SLA remains unenforced. | AUD-018-025 |
| CHK057 | [ ] | CONFLICT | Model/contract template permits optional categories despite mandatory FR-039. | AUD-018-027, AUD-018-032 |
| CHK058 | [ ] | PARTIAL | Contract time window/minimum-event count ignored; tag repetitions are not distinct-event trends. | AUD-018-028 |
| CHK059 | [ ] | PARTIAL | Verifier helper/reference convention mismatch and no CI consumer/change adequacy check. | AUD-018-029 |
| CHK060 | [ ] | PARTIAL | Approver string does not specify/enforce authenticated IC/admin escalated review. | AUD-018-001, AUD-018-027 |
| CHK061 | [ ] | PARTIAL | Single optional run ID and origin fields exist; absent/multiple/foreign exercise handling unresolved. | AUD-018-026, AUD-018-027, AUD-018-038 |
| CHK062 | [ ] | PARTIAL | Domain extension preserves fields but active Communication model is separate; compatibility needs integration tests. | AUD-018-006 |
| CHK063 | [ ] | CONFLICT | Clarification preserves independent scales; runtime Risk prompt conflicts. | AUD-018-017 |
| CHK064 | [ ] | IMPLEMENTED | Incident hazards were additively extended; existing values remain. | - |
| CHK065 | [ ] | PARTIAL | PPRR payload fields present; schema/auth/durable overlap representation incomplete. | AUD-018-018, AUD-018-031 |
| CHK066 | [ ] | PARTIAL | New categories/helpers specified; deprecated and replacement graph routing not reconciled. | AUD-018-030 |
| CHK067 | [ ] | MISSING | Seven named metrics lack emitters and complete collection/threshold definitions. | AUD-018-034 |
| CHK068 | [ ] | PARTIAL | Validation budget stated; benchmark does not establish complete valid runtime check scope. | AUD-018-006, AUD-018-037 |
| CHK069 | [ ] | PARTIAL | R-002 closes prose gap; implemented queues/fallback/readiness still incomplete. | AUD-018-005 |
| CHK070 | [ ] | PARTIAL | R-012 names k=10/LGA; absent coverage/classification/geographic enforcement gaps remain. | AUD-018-004 |
| CHK071 | [ ] | PARTIAL | Existing warning safety retained; recovery enrichment permits missing validator. | AUD-018-022 |
| CHK072 | [ ] | PARTIAL | No authoritative all-warning compliance methodology/results; structural tests insufficient. | AUD-018-007, AUD-018-036, AUD-018-039 |
| CHK073 | [ ] | PARTIAL | Hazard-specific stage timeframes not quantified in a complete approved policy. | AUD-018-012, AUD-018-037, AUD-018-038 |
| CHK074 | [ ] | PARTIAL | Correct 90-day denominator/closure/overdue semantics absent; outcome unobserved. | AUD-018-028, AUD-018-039 |
| CHK075 | [ ] | PARTIAL | Required section content and approval-date/30-day evidence incomplete. | AUD-018-038, AUD-018-039 |
| CHK076 | [ ] | PARTIAL | Manual entry feasible by R-003 decision; no measured/alerted 24-hour loop. | AUD-018-025 |
| CHK077 | [ ] | PARTIAL | Monitoring amendment intent clear; exact role/TWS normative addendum incomplete. | AUD-018-038 |
| CHK078 | [ ] | PARTIAL | Risk retains four-level scale in spec; runtime prompt and TWS mapping diverge. | AUD-018-017, AUD-018-038 |
| CHK079 | [ ] | PARTIAL | AIIMS priority language exists; exact recovery allocation mode not connected. | AUD-018-020, AUD-018-038 |
| CHK080 | [ ] | PARTIAL | Hub persona/PPRR deferral not full structure/Shared Responsibility addendum. | AUD-018-038 |
| CHK081 | [ ] | MISSING | No located consistent dedicated role-mapping template/sections across the six specs. | AUD-018-038 |
| CHK082 | [ ] | PARTIAL | Warning-only timeout supersession authored and reciprocal; actual tier distinction absent. | AUD-018-008, AUD-018-038 |
| CHK083 | [ ] | PARTIAL | Zone model explicitly augmented, not replaced; integration/replan gaps violate full preserved behavior. | AUD-018-012, AUD-018-013 |
| CHK084 | [ ] | PARTIAL | Six specs enumerated, but complete reciprocal addenda and acceptance reconciliation incomplete. | AUD-018-038 |
| CHK085 | [ ] | PARTIAL | Existing-agent recovery-mode assumption clear; runtime activation missing. | AUD-018-020 |
| CHK086 | [ ] | PARTIAL | Simulation dependency named; exact phase-triggered rehearsal/readiness behavior incomplete. | AUD-018-020, AUD-018-038 |
| CHK087 | [ ] | PARTIAL | R-003 reconciles manual entry in design, not execution/SLA proof. | AUD-018-025, AUD-018-039 |
| CHK088 | [ ] | IMPLEMENTED | Six original handbooks located in corpus and relevant passages inspected; historical path stale. | AUD-018-038, AUD-018-039 |
| CHK089 | [ ] | PARTIAL | Plan maps P1 mandates; full bidirectional implementation/review evidence not established. | AUD-018-036, AUD-018-038, AUD-018-039 |
| CHK090 | [ ] | IMPLEMENTED | Plan explicitly maps AWS/AIIMS/evacuation/recovery/TWS constitutional sections to FRs; runtime status separate. | AUD-018-039 |
| CHK091 | [ ] | PARTIAL | Human authorization authored, but warning/stage/lesson paths trust strings or bypass approval. | AUD-018-001, AUD-018-003, AUD-018-027 |
| CHK092 | [ ] | PARTIAL | AU-only authored account/module exists; actual persistence/residency unverified and stores disconnected. | AUD-018-005, AUD-018-035, AUD-018-039 |
| CHK093 | [ ] | PARTIAL | R-009/serializers/routes exist; standards schemas/GeoJSON/delivery validation incomplete. | AUD-018-032, AUD-018-033 |
| CHK094 | [ ] | PARTIAL | Plan links principles and lessons FRs; connected improvement/measurement evidence incomplete. | AUD-018-026, AUD-018-029, AUD-018-039 |
| CHK095 | [ ] | PARTIAL | R-001 solves model-host conflict but context transfer does not set Response. | AUD-018-019 |
| CHK096 | [ ] | PARTIAL | Spec population lists agree; seven-group implementation omits Constitution categories and aliases diverge. | AUD-018-010 |
| CHK097 | [ ] | CONFLICT | Six names consistent in spec, but dual-role example/five defaults/coverage-level policy disagree. | AUD-018-014, AUD-018-038 |
| CHK098 | [ ] | CONFLICT | Summary says 47 FRs; current numbered requirement set has 54. | AUD-018-039 |

### Summary Checklist: 16 Original Checked Items

`QC-nn` numbers below label the original unnumbered items in order; original lowercase `[x]` state is preserved.

| Item | Original state | Status | Assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QC-01 No implementation details | [x] | CONFLICT | Later spec explicitly names domain fields/models, Azure regions and timeline payload contracts. Reassess intended spec audience. | AUD-018-039 |
| QC-02 User value/business focus | [x] | IMPLEMENTED | Seven stories explain life safety, coordination, recovery and improvement value. | - |
| QC-03 Non-technical stakeholder wording | [x] | PARTIAL | Story narratives are accessible; later model/technical additions exceed the original summary claim. | AUD-018-039 |
| QC-04 Mandatory sections complete | [x] | IMPLEMENTED | Scenarios, requirements and measurable-outcome sections are present. | - |
| QC-05 No clarification markers remain | [x] | IMPLEMENTED | No unresolved marker in original spec; this does not resolve checklist contradictions. | AUD-018-038 |
| QC-06 Testable/unambiguous requirements | [x] | PARTIAL | Coverage levels, category optionality, timing/measurement and contract decisions remain inconsistent. | AUD-018-032, AUD-018-038 |
| QC-07 Measurable success criteria | [x] | PARTIAL | Counts/budgets exist; hazard-specific timing and closure cohort definitions incomplete. | AUD-018-028, AUD-018-037, AUD-018-038 |
| QC-08 Technology-agnostic success criteria | [x] | IMPLEMENTED | SCs describe domain outcomes/counts rather than framework choices. | - |
| QC-09 Acceptance scenarios defined | [x] | IMPLEMENTED | All 30 original scenarios present and individually mapped above; execution separate. | AUD-018-036 |
| QC-10 Edge cases identified | [x] | IMPLEMENTED | Seven original edges present and individually mapped above. | AUD-018-036 |
| QC-11 Clearly bounded scope | [x] | PARTIAL | AU deferrals explicit; NCM/coverage/authority ambiguities need reconciliation. | AUD-018-016, AUD-018-038, AUD-018-040 |
| QC-12 Dependencies/assumptions identified | [x] | IMPLEMENTED | Seven assumptions and relevant spec/constitution dependencies authored; applicability and execution separate. | AUD-018-038, AUD-018-039 |
| QC-13 Every FR has clear acceptance | [x] | PARTIAL | Detailed checklist identifies unanswered P1 operational criteria; weak tests do not supply them. | AUD-018-036, AUD-018-038 |
| QC-14 Stories cover primary flows | [x] | IMPLEMENTED | Seven domains represented with independent-test narratives. | AUD-018-036 |
| QC-15 Feature meets measurable outcomes | [x] | UNVERIFIED | Source/test authoring cannot establish measured execution or operational success. | AUD-018-037, AUD-018-039 |
| QC-16 No implementation details leak | [x] | CONFLICT | Same later technical additions as QC-01; stale first-pass summary not revalidated. | AUD-018-039 |

### Quickstart Checklist: 10 Original Open Items

`QS-nn` labels original unnumbered checklist entries; every original state is `[ ]`.

| Item | Original state | Status | Assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QS-01 New domain model exports | [ ] | CONFLICT | Named initializer absent; alternate namespace is not an AIDR export replacement. Resolve documentation/public surface, not invented import failure. | AUD-018-039 |
| QS-02 Router registration | [ ] | IMPLEMENTED | [API router](../../apps/api/app/api/router.py#L77) registers warning/AIIMS/evacuation/lessons/PPRR/recovery/health routes. | AUD-018-032 |
| QS-03 Health <=1s | [ ] | UNVERIFIED | Endpoints authored; only dictionary checks and no execution evidence. | AUD-018-034, AUD-018-037 |
| QS-04 AU-only containers | [ ] | UNVERIFIED | Authored parent-region restriction exists, deployed residency unqueried. | AUD-018-035, AUD-018-039 |
| QS-05 Social k>=10 | [ ] | PARTIAL | Nullable coverage and classification bypass remain. | AUD-018-004 |
| QS-06 Warning validator <=5s | [ ] | UNVERIFIED | Benchmark source exists, no connected measured run. | AUD-018-037 |
| QS-07 Unit tests pass | [ ] | UNVERIFIED | Tests were read only. | AUD-018-039 |
| QS-08 Contract tests pass | [ ] | UNVERIFIED | Tests were read only; conformance assertions incomplete. | AUD-018-032, AUD-018-039 |
| QS-09 No secrets in source | [ ] | UNVERIFIED | No credential value was needed/reported; no complete secret-scanner execution performed. | AUD-018-039 |
| QS-10 Constitution alignment verified | [ ] | PARTIAL | Plan trace table authored; security/safety/degradation gaps prevent operational verification. | AUD-018-039 |

### Plan Constitution and Review Gates

Original `PASS`/`NOTE` values are design-stage assertions, not human approvals. All 21 gate rows are retained here.

| Original gate | Original assertion | Status | Assessment / follow-up |
| --- | --- | --- | --- |
| I Primacy of life | PASS | PARTIAL | Unsafe warning publication/evacuation advancement remain; AUD-018-003, AUD-018-011. |
| II Eleven EM principles | PASS | PARTIAL | PPRR/coordination/continual-improvement execution incomplete; AUD-018-016, AUD-018-020, AUD-018-026. |
| II-A AIIMS | PASS | PARTIAL | Incomplete bootstrap, coverage and communication boundaries; AUD-018-014, AUD-018-016. |
| III Multi-hazard/multi-agency | PASS | PARTIAL | Hazards additive, but chain/agency boundaries incomplete; AUD-018-009, AUD-018-016. |
| IV Auditability | PASS | PARTIAL | Arbitrary payloads/volatile storage/self-asserted actors; AUD-018-001, AUD-018-005, AUD-018-031. |
| V-A AWS tiers | PASS | PARTIAL | Builder not runtime enforcement; AUD-018-006, AUD-018-009. |
| V-B Ten warning principles | PASS | PARTIAL | Structural/default passes insufficient; AUD-018-007. |
| V-C Total Warning System | PASS | PARTIAL | Provenance and feedback loop gaps; AUD-018-024, AUD-018-025. |
| VI Five-stage evacuation | PASS | PARTIAL | Labels without all operations/safety; AUD-018-011, AUD-018-012, AUD-018-013. |
| VI-C Vulnerable populations | PASS | PARTIAL | Missing groups/connected accommodations; AUD-018-010. |
| VII Recovery support | PASS | PARTIAL | History/community/phase operations incomplete; AUD-018-020, AUD-018-021, AUD-018-022. |
| VII-A Six recovery principles | PASS | PARTIAL | Optional labels not recommendation-level alignment; AUD-018-022. |
| VII-B Four environments | PASS | PARTIAL | 21-slot artifact implemented, longitudinal/current UI incomplete; AUD-018-021, AUD-018-023. |
| VII-C Recovery transition | PASS | PARTIAL | No operational managed overlap; AUD-018-018, AUD-018-020. |
| VIII Azure platform | PASS | IMPLEMENTED | Relevant Azure container/account/module artifacts authored; deployed state remains UNVERIFIED under AUD-018-035. |
| NN-1 Human authorization | PASS | PARTIAL | AIDR actor strings/publish bypass; AUD-018-001, AUD-018-003. |
| NN-2 AU data sovereignty | PASS | UNVERIFIED | AU IaC restriction supports intent, not observed storage/replication; AUD-018-035, AUD-018-039. |
| NN-3 Privacy | PASS | PARTIAL | Coverage/classification/geography controls incomplete; AUD-018-004. |
| NN-4 Interoperability | NOTE | PARTIAL | R-009 decision and XML endpoints not full standards conformance; AUD-018-032, AUD-018-033. |
| NN-5 Graceful degradation | NOTE | PARTIAL | R-002 decision not complete queues/replay/fallback; AUD-018-005. |
| QG Tests/IaC/human review/lessons | PASS | UNVERIFIED | No attributable Spec-018 run/what-if/human sign-off; PR lesson gate missing. AUD-018-029, AUD-018-039. |

The plan's Phase-0/Phase-1 gate and its two notes were reviewed as authored records. Research says all clarification decisions are complete; this is not approval evidence. The tasks' phase checkpoints and final claim of full operational capability likewise remain PARTIAL/UNVERIFIED. No chronological proof establishes T001, T069, T076, T077 or T079 execution. Reviewer/security checks found authorization, input-validation and data-loss risks; dependency freshness, exhaustive secret scanning, real performance and human review remain UNVERIFIED rather than implicitly passed.

## Future Validation Catalogue

**Not executed in this audit.** Run only after separate implementation/test authorization. Common prerequisites: an isolated Python >=3.12 environment matching [project metadata](../../pyproject.toml#L9), API/agent/dev dependencies installed, repository root as working directory, and [test path setup](../../tests/conftest.py#L10). All external network, LLM, delivery, telemetry and production-store access must be disabled/replaced by recording test adapters. No real warnings, credentials or personal data belong in fixtures. A passed source-only check is never a measured deployment or human approval.

| Check | Future command or procedure | Additional prerequisites and expected assertions |
| --- | --- | --- |
| V-MODELS | `python -m pytest tests/unit/test_domain_models_aidr.py -q` | Extend fixtures first. Assert all additive models, rejected invalid updates, public export decision, independent severity scales and four validated event shapes. |
| V-WARNING | `python -m pytest tests/unit/test_warning_compliance.py tests/contract/test_warning_contract.py -q` | Add pipeline/MAF/approval/chain tests, controllable timers and recording channels. Assert complete AWS fields, ten evidence-based results, trusted approval, no bypass, correct supersession and fallback. |
| V-AUTH | Run V-CONTRACT with trusted claim fixtures plus anonymous/wrong-role/cross-tenant cases. | Do not use the production-auth test-principal shortcut as the only authentication proof. Validate trusted identity resolution separately; assert 401/403/404 policy and zero unauthorized state/audit-destination changes. |
| V-AIIMS | `python -m pytest tests/unit/test_aiims_role_assignment.py tests/unit/test_spec032_llm_and_aiims.py tests/contract/test_aiims_contract.py tests/integration/test_aiims_escalation.py -q` | Add incident-start, complete coverage, period history, actual delegation and agency relationship assertions. Keep conflict-escalation semantics distinct from public-warning deadlines. |
| V-EVAC | `python -m pytest tests/unit/test_evacuation_stages.py tests/contract/test_evacuation_contract.py -q` | Add plan/road/shelter/medical/animal fixtures. Assert stage side effects, safe return, bounded progress, all re-entry counts and no unsafe completion. |
| V-PPRR | `python -m pytest tests/unit/test_pprr_lifecycle.py tests/contract/test_pprr_contract.py -q` | Update expectations against approved recurring-transition policy. Assert active overlap, managed exit, context references/Response transfer, authority and persistence. |
| V-RECOVERY | `python -m pytest tests/contract/test_recovery_contract.py tests/unit/test_indicator_analysis.py tests/unit/test_domain_models_aidr.py -q` | Add dated 21-indicator history, directional regression, privacy-null/batch cases, principles, community input, fail-closed safety and warning-relative deadlines. |
| V-LESSONS | `python -m pytest tests/contract/test_lessons_contract.py tests/integration/test_lessons_capture_full_aar.py -q` | Extend from direct synthetic drafts to actual lifecycle triggers/register linkage. Assert real origin, categories, approved transitions, correct 90-day cohorts and verifier semantics. |
| V-STORE | After authoring: `python -m pytest tests/integration/test_aidr_cosmos.py -q` | This test path is proposed, not existing. Disposable emulator/local adapter fixtures and approved TTL/key decisions first. Assert five-container CRUD, key routing, ETag conflicts, restart, buffering/replay and exercise isolation. |
| V-CONTRACT | `python -m pytest tests/contract/test_warning_contract.py tests/contract/test_aiims_contract.py tests/contract/test_evacuation_contract.py tests/contract/test_pprr_contract.py tests/contract/test_recovery_contract.py tests/contract/test_lessons_contract.py -q` | Approved canonical schemas first. Compare exact requests/responses/status/errors against schemas, including bad enums, missing fields and preserved compatibility. |
| V-INTEROP | Run V-WARNING extended with offline CAP 1.2 / EDXL-DE schema validation and GeoJSON cases. | Pin authoritative schemas and validators beforehand. Assert escaped content, valid timestamps/references/status, simulation marking and a real envelope delivery option. Simple XML parsing is insufficient. |
| V-METRICS | Run V-CONTRACT with recording metric exporter and capability-health failure fixtures. | Assert all seven names, units/denominators, success/failure/replay behavior, bounded cardinality and truthful readiness/queue/staleness. |
| V-SCENARIO | `python -m pytest tests/simulation/test_aidr_scenarios.py -q` | Replace weak cases before running. Exercise real controllers and domain logic with fake external I/O; assert all 30 scenarios, seven edges, inter-agent calls and persisted effects. |
| V-PERF | `python -m pytest tests/benchmark/test_aidr_performance.py -q` | Representative configured stores/workload and corrected valid-output assertions first. Measure every NFR, actual simultaneous operations, >=50 distinct lessons, plus T084's <=2s generation/<=3s stage and edge <=15s replan budgets. |
| V-UI | `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium recovery-environments.spec.ts` and `pnpm --filter @ama/web test:a11y` after extending the AIDR cases. | The [package scripts](../../apps/web/package.json#L12) and [existing recovery test](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L1) provide the harness; provision its local web/API and persona fixtures first. Extend it beyond the current economic-evaluator proxy to actual incident/COP/community state. Assert record readback, privacy, overlap, keyboard/screen-reader usability, and no catalogue/trust proxy presented as measured results. |
| V-GATE | Exercise the implemented lesson PR verifier and CI job with synthetic PR bodies in a local workflow harness. | Gate is currently absent. Require positive and blocking cases plus safe outage policy; attach reviewer evidence that the change addresses the referenced lesson/event. |
| V-INFRA | Use the approved existing IaC validation/what-if review process, then inspect separately authorized AU test-resource inventory and retention evidence. | No deployment or cloud query is authorized by this report. Capture region/replication/retention/key configuration and named IaC/privacy approval; model-hosting carve-out does not cover data stores. |
| V-DOC | `git --no-optional-locks diff --check -- specs/018-aidr-guidance-integration` plus the report-text coverage/link gate and independent document review. | Text hygiene is not approval. Verify all original IDs/states remain intact, all 98 detailed obligations have dispositions, six addenda agree, hypotheses/persona records meet contracts, and each claimed run/approval has revision/date/owner evidence. |

### Exit Criteria

1. Every remediation checkbox above remains open until the specified behavior, independent assertions and attributable future results exist. No original checkbox is retrospectively rewritten by this audit.
2. Resolve P1 authority, privacy, persistence, warning and evacuation risks before relying on this feature for operational decision-making or public dissemination.
3. Close requirement/scenario/checklist follow-ups only with the corresponding evidence class: source for artifacts, recorded runs for execution/latency, identified reviewers for human approval, and authorized inventory for deployed residency.
4. Maintain explicit Not tested/UNVERIFIED status for HYP-016, persona validation and business outcomes until appropriate evidence exists; retain non-AU deferrals and constitutional boundaries.
5. Audit completion validation is limited to this report's text: exact original task IDs/states, all requirement and scenario rows, checklist coverage, existing link targets and line bounds, 40 distinct unchecked follow-ups with no unresolved references, and diagnostics for this Markdown file only. It is not execution of any V-* procedure.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 018 only. Three parallel technical reviews examined authority
and durable-state boundaries, warning/evacuation integration, and recovery/lessons evidence. No source edit was safe to
apply without first resolving the shared authentication, incident-scope, persistence, approval, privacy, and lifecycle
contracts. The report remains PARTIAL; all external, human, deployment, performance, and operational evidence remains
UNVERIFIED.

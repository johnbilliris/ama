# Spec 034 Implementation Review

## Review Metadata

- Review date: 2026-09-14.
- Requested and verified HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Scope: only `034-webapp-capstone-coverage`, in this fresh, user-approved static review context.
- Authority: [Review Contract](../001-spec-implementation-audit/README.md#L11) and
  [code-review instructions](../../.github/instructions/code-review.instructions.md#L1).
- Sole writable artifact: this report. No delegation and no other implementation review reports consulted.
- Existing unrelated untracked work was observed through git metadata only and left untouched.
- No application tests, repository verifiers, builds, imports, browsers, screenshots, servers,
  cloud operations, deployments, installations, runtime inspection, approvals, branches, or commits were performed.
- Source and assertions establish authored behavior only. Test execution, accessibility, performance,
  deployment, operational outcomes, and human sign-off remain UNVERIFIED without attributable evidence.

## Findings

**Static disposition: Not Ready.** Existing source does not support capstone completion. This is not a
fresh test result. The first falsifiable hypothesis was that supplied-metric evaluation could pass while
the operator workflow was broken; tracing SC-001 into `_evaluate_metric` supported it. The report was
started at that point and immediately validated using report-only text/link diagnostics.

Findings are impact ordered. Source defects and absent proof are distinguished; none implies that a
production exploit, deployment failure, or browser failure was reproduced.

| Finding | Evidence, expected versus actual, and impact | Follow-up |
| --- | --- | --- |
| F01 - HIGH: Publication does not require completed IC approval | [Publish validation](../../apps/api/app/services/public_alert_service.py#L48) admits `pending_approval`; [publication route](../../apps/api/app/api/routes/alerts.py#L37) accepts a body-supplied publisher without a principal dependency. [HITL negative test](../../tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts#L53) rejects missing metrics, not an unauthorized action. FR-009/FR-011 and SC-001 can be falsely satisfied while an unapproved alert becomes `published`. Channel adapters construct payloads; actual external delivery is not established. | AUD-034-008 |
| F02 - HIGH: Persona and incident scope are not established | [Workspace API](../../apps/api/app/api/routes/personas.py#L7) accepts arbitrary persona IDs; [service](../../apps/api/app/services/persona_workspace_service.py#L26) derives visible tasks from that ID, not the caller. [Auth middleware](../../apps/api/app/middleware/auth_middleware.py#L22) ignores the test persona header. [Evacuation transition](../../apps/api/app/api/routes/evacuation.py#L103) checks incident and stage existence separately without checking ownership. Button visibility is not FR-007 authorization. | AUD-034-005, AUD-034-011 |
| F03 - HIGH: Offline actions can be lost before acknowledgement | [Queue drain](../../apps/web/src/lib/offline/queue-store.ts#L215) deletes entries before [replay](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L89) knows whether the request succeeded. Failures are counted, not requeued. [Replay API](../../apps/api/app/api/routes/offline_replay.py#L101) writes audit rows but does not dispatch the saved action. [Offline test](../../tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts#L30) only retries an evaluator online. | AUD-034-013 |
| F04 - HIGH: Audit read-back is not the durable operational audit | [Evaluator ledger](../../apps/api/app/services/outcome_evaluator_service.py#L38) and [list](../../apps/api/app/services/outcome_evaluator_service.py#L292) are process-local; they never query the [existing repository](../../apps/api/app/repositories/audit_repository.py#L41). [Denial records](../../apps/api/app/api/routes/audit.py#L43) enter another ring buffer, not that list. Restarts/workers lose or disagree on evidence; denial, gap and rollback events are not joined into FR-010/Q22/Q24 read-back. | AUD-034-006 |
| F05 - HIGH: Arithmetic replaces contractual measurements | [SC-001](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L26) posts 800 lives at risk. [Evaluator formulas](../../apps/api/app/services/outcome_evaluator_service.py#L120) omit warning reach, AIIMS absolute ceilings, reference evacuation timestamps, and the 70%-baseline/12-click mutual-aid rule. [SC-005 assertion](../../tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts#L45) uses `<=` instead of `>=`; the exact-30% fixture conceals this. [Proxy validator](../../tests/e2e/web-coverage/_support/validators/outcome-proxy.ts#L36) checks labels only. | AUD-034-001 |
| F06 - HIGH: Depth profiles do not control workflows | [Generator](../../scripts/web-coverage/_lib/persona_spec_generator.py#L834) selects an evaluator and [passing constants](../../scripts/web-coverage/_lib/persona_spec_generator.py#L745), ignoring steps, workspace route, language, UI target, and read-only variants. [Workspace PO](../../tests/e2e/web-coverage/_support/pages/workspaces.po.ts#L20) opens the index. All 90 persona files contain evaluator/audit calls and no click/fill/offline control interactions. [Cross-jurisdiction template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) performs two evaluations, not a handoff. FR-029(b) is separate from the evaluator permitted by (c). | AUD-034-002 |
| F07 - HIGH: Readiness counts unrelated or non-passing rows | [Gate](../../scripts/web-coverage/_lib/schema_validators.py#L82) counts persona/outcome rows without requiring `passed`; uses AIIMS `operations` plus compound hazards for eight jurisdiction integrations; counts an ordinary Commonwealth row as a bridge; checks neither mandatory hazard pairs nor cross-cutting JUnit. [Missing register](../../scripts/web-coverage/_lib/schema_validators.py#L66) means zero open gaps; only `Open` blocks. Routes, tests, audits and canonical persona membership are not resolved. | AUD-034-003 |
| F08 - HIGH: Trace artifacts lose evidence identity | [Reporter](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L225) expects attachments absent from the fixtures, defaulting to `/`, empty correlation and null audit. It ignores gap annotations and has no `onStdErr` enforcement. [Merge](../../scripts/web-coverage/trace-merge.py#L49) dedupes by test IDs/FR as well as tuple; [Markdown](../../scripts/web-coverage/trace-merge.py#L84) prints counts, not Test IDs. [CI upload](../../.github/workflows/ci.yml#L317) omits nested JUnit, run JSON and cycle metadata. No portfolio invalidation exists in this emitter/merge/gate chain. | AUD-034-004 |
| F09 - HIGH: Evaluator contracts are incompletely validated | [Request](../../apps/api/app/api/routes/outcome_evaluator.py#L39) accepts arbitrary correlation strings and metric dictionaries; [service](../../apps/api/app/services/outcome_evaluator_service.py#L178) checks field presence then calls `float`, without non-negative/finite/integer-click checks, SC/scenario compatibility, or principal binding. Response model is not applied. [Cross-jurisdiction template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) constructs a non-UUID handover correlation. Malformed or spoofed evidence can be admitted. | AUD-034-007 |
| F10 - HIGH: COP latency measures an empty landmark | [Test](../../tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts#L27) times navigation; [page](../../apps/web/src/app/incidents/page.tsx#L53) hard-codes no incidents and a placeholder map. The real [root mapper](../../apps/web/src/app/page.tsx#L89) loads API data on filter changes, not through this test. Peer convergence, conflicting AWS reconciliation, partition defaults and AIIMS transitions are untested. | AUD-034-009 |
| F11 - HIGH: Span warning has no command-structure input | [Workspace](../../apps/web/src/components/workspaces/persona-workspace.tsx#L84) supplies empty reports and omits Logistics; [panel](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23) suppresses only Planning and delegates only for IC. No save/delegation binding is supplied. [Test](../../tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts#L25) has no reports or warning assertion. | AUD-034-010 |
| F12 - HIGH: Five-stage evacuation is not exercised | [Stages API](../../apps/api/app/api/routes/evacuation.py#L82) exists, but [suite](../../tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts#L29) posts fixed lead hours. No progression, illegal transition, type/approach, shelter-in-place or eight-cohort prioritization is asserted. [Data model](data-model.md#L309) substitutes warning states for evacuation stages. | AUD-034-011 |
| F13 - HIGH: Recovery checks do not establish handover | [Recovery service](../../apps/api/app/services/recovery_service.py#L25) tracks four environments; [suite](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L32) ignores them. [UI](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L29) retains a zero claims placeholder on failed fetch; [utility page](../../apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx#L11) always uses one. Editable environment state, managed handover, Sendai provenance and three named sources are unproved. | AUD-034-012 |
| F14 - HIGH: Accessibility and languages are narrowed | [Axe](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) disables contrast/region; [tests](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) scan three indexes, not every P1 route, and lack the axe project's `@a11y` tag. [Language probe](../../tests/e2e/web-coverage/_support/a11y/languagePackProbe.ts#L19) checks a list, not rendered warnings. The [active draft bridge](../../apps/api/app/api/routes/agents.py#L185) prepends a language label to English carrier text; this is not translated Simplified Chinese or endorsed ATSI content. | AUD-034-014 |
| F15 - HIGH: Sovereignty triple is not exercised | [Suite](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L29) compares ranks locally; registry-date test calls logistics evaluator. [Fixture](../../tests/e2e/web-coverage/_support/fixtures/carveoutRegistry.fixture.ts#L29) swallows missing/malformed registry and expects `carveouts`; [actual registry](../../infra/parameters/foundry-carveout.yaml#L14) uses `deployments`, last review 2026-05-08 and renewal dates 2027-04-08. The 90-day versus renewal-date policy remains unresolved. | AUD-034-015 |
| F17 - HIGH: Gap transitions lack closure proof | [Promote/close](../../scripts/web-coverage/gap-register.py#L154) overwrite any prior state and trust supplied PR/SHA; no rerun/pass/regression proof or iteration increment. [Regress](../../scripts/web-coverage/gap-register.py#L177) can escalate at three instead of resetting and overwrites origin cycle. JSON is source while gate reads Markdown; validation checks shape only. | AUD-034-017 |
| F18 - HIGH: Tribunal can bypass constitutional merit | [Resolver](../../scripts/web-coverage/review-log.py#L114) counts approvals among submitted votes instead of objection support from the 10/58/17 roster; historical objections can veto and 43 approvals can override. Resolutions are not saved into votes. [Closure](../../scripts/web-coverage/review-log.py#L282) assumes merit, excludes owner names containing `project-lead`, treats empty as 100%, and checks no PR/diff/pass proof. [Workflow](../../.github/workflows/web-coverage-iteration.yml#L69) collects no votes, invokes no closure and swallows resolver failures. | AUD-034-018 |
| F19 - HIGH: Rollback records a claim instead of restoring | [Update](../../scripts/web-coverage/known-good.py#L92) skips missing trace, accepts partial passes and omits hash/run proof. [Rollback](../../scripts/web-coverage/known-good.py#L148) stamps JSON only. [CD](../../.github/workflows/cd.yml#L331) downloads no canonical trace, skips dev updates and rolls back health failures only. [Determinism](../../scripts/web-coverage/verify-trace-determinism.ps1#L16) remerges files, not three runs, without checking native exit codes. | AUD-034-019 |
| F20 - HIGH: Retention and redaction are incomplete | [Policy](../../infra/bicep/main.bicep#L246) is 30 days, not 2,557; [active entry](../../azure.yaml#L8) selects another template without this container wiring. [Audit helper](../../scripts/web-coverage/_lib/audit_append.py#L19) has no Blob path. [Redactor](../../tests/e2e/web-coverage/_support/reporter/redact.ts#L10) omits names/GPS and does not process screenshots, video, JUnit or free-text attachments. No actual leak or deployed state is claimed. | AUD-034-020 |
| F16 - IMPORTANT: Simulation proof is a cache hit | [Playback test](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L32) compares cached evaluator responses; [lessons test](../../tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts#L28) only reads an evaluator audit. Real [playback](../../apps/api/app/services/playback_service.py#L42) enforces participants/events. [Report UI](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L30) uses report ID as tenant ID and has no export/control-mapping. [Service construction](../../apps/api/app/api/routes/simulations.py#L53) supplies no Blob client; [report persistence](../../apps/api/app/services/exercise_report_service.py#L96) then performs no write although a URI is recorded. No phase is emitted in trace. | AUD-034-016 |
| F21 - IMPORTANT: Collection and onboarding drift | [Config](../../apps/web/playwright.config.cts#L48) excludes the [persona contract](../../tests/e2e/web-coverage/_support/fixtures/__tests__/persona.contract.spec.ts#L15), whose URL and `personas` envelope disagree with the API. Config omits `forbidOnly`, explicit workers and failure media. [Lint](../../apps/web/eslint.config.mjs#L23) targets outside ordinary `eslint .`; no tag/permission rule is registered. Documented CLI names/flags differ from parsers. | AUD-034-021 |
| F22 - IMPORTANT: Checked work lacks attributable completion | All [tasks](tasks.md#L29) are checked; all [workflow checks](checklists/validation.md#L23) unchecked. [Trace](coverage-trace.md#L1), [manifest](known-good.json#L1), [review](review-log.md#L1) and [first run](_evidence/first-run.log#L3) incomplete. [Ignored JUnit](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L1) records 76 skips; [metadata](../../tests/e2e/web-coverage/_artifacts/cycle-metadata.json#L4) names another SHA. [Objection template](../../scripts/web-coverage/agent-objection-template.json#L1) is incompatible with its schema. Reviews, hypotheses and sign-off remain unverified. | AUD-034-022 |

## Remediation Tasks

- [ ] AUD-034-001 Connect capstone proofs to observable operator workflows
  - Obligations/impact: T028-T032, T040, T146-T150, T180/T186; FR-002/FR-016/FR-028, SC-001-SC-005, Q1/Q7/Q8/Q15. Expected measured operator outcomes; F05 substitutes supplied arithmetic and can overstate readiness.
  - Developer: derive inputs in the existing five capstone tests, proxy validator and evaluator from persisted actions and actual UI readings. Enforce both relative and absolute latency/click limits, reference-based evacuation lead and per-scenario managed economic handover. Correct SC-005 comparison; consolidate seed baselines with fixture types and retain separately labelled evaluator contract tests.
  - Tester: extend the five capstone files and [evaluator tests](../../tests/contract/test_outcome_evaluator.py#L107). Use 119/120/121-second reach; each AIIMS level at/above its absolute and 50% bounds; 23.9/24/24.1-hour uplift; 7/8 and 12/13 clicks plus 70% baselines; 29/30/31% loss reduction and zero/missing baseline. Exercise each mandatory hazard separately and break UI delivery while leaving evaluator healthy. Future V-API and V-P filtered to `capstone/`; expected broken workflow fails.
  - Boundaries/dependencies: AUD-034-005/008/009/011/012/014 supply real actor/workflow data. No budget relaxation, new infrastructure, annual lives-saved inference, or dashboard-chrome translation.
  - Done: attributable measurements and boundary assertions support every proxy; a passing constant cannot close an operator outcome.

- [ ] AUD-034-002 Execute declared persona workflows instead of evaluator templates
  - Obligations/impact: T014, T069-T145, T174-T177/T184, T187-T199/T205; FR-001/002/003/019/029/030, Q15/Q20/Q23/Q24/Q28. F06 collapses distinct must-do actions into a generic calculator and the default generator can restore bails.
  - Developer: make generator render consume validated ordered steps, primary route, persisted UI targets, read-only denial/export/acknowledgement variants, language and cross-jurisdiction tags. Support UI-only profiles and combined targets; open a structured gap on invalid/missing profile. Remove default stub generation or require an explicit migration-only mode. Reconcile two-step profiles with T175's three-step minimum and approved persona needs; use actual persona routes in the PO.
  - Tester: extend the existing 90 persona files, including [SAPOL](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L25) and [BoM relay](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts#L26). Assert all 68 roles, 13 FR-030 topics, eight jurisdiction bridges, shared incident IDs/AWS/geometry, DACC lifecycle, declarations, clinical/transport handoffs, ABC/SBS source and translated/recovery state. Wrong selector, missing profile, wrong actor, denied transition and read-only tamper must fail distinctly. Future V-P `operational/ sectors/`; proposed generator cases under existing `tests/unit` use temporary output only.
  - Boundaries/dependencies: reuse newer sector panels/APIs; AUD-034-022 resolves syntheses/schema conflicts and AUD-034-008 through AUD-034-016 close product gaps. No new persona or fixture-only authority.
  - Done: breaking a persona-specific action fails its scenario; profile changes alter executed steps and read-only cases genuinely exercise their allowed transition.

- [ ] AUD-034-003 Fail readiness closed on incomplete or unrelated evidence
  - Obligations/impact: T047/T151-T154/T177; FR-003/004/016/022/023/025, SC-006-SC-009, Q29. F07 counts skipped/arbitrary IDs and unrelated rows as coverage.
  - Developer: replace gate heuristics with exact canonical inventory, passing test identity, eight distinct jurisdictions, a real Commonwealth bridge, named outcome/hazard pairs, phase coverage and complete cross-cutting JUnit. Require expected shards with matching revision/seed/cycle; reject absent/malformed files, unresolved audits/routes, unexplained skips/flakes and missing validator libraries. Block unresolved In-Progress/Reopened/Escalated/veto states, not only Open; support HYP-002 re-scope only with an explicit approved cohort record.
  - Tester: proposed gate fixture tests beside [CLI unit tests](../../tests/unit/test_review_log_closure.py#L1) cover a complete matrix, 68 skipped rows, invented persona, duplicate jurisdiction, ordinary NEMA row, missing hazard/JUnit/shard/register, stale SHA and each unresolved status. Future V-CLI; every incomplete matrix must exit nonzero and emit no Ready event.
  - Boundaries/dependencies: AUD-034-004 supplies typed trace; AUD-034-017/018 define state/merit. Branch-protection application is later administrator work, not a JSON-file effect.
  - Done: only complete attributable passing coverage can emit Ready, with later evidence of the exact applied required checks.

- [ ] AUD-034-004 Preserve evidence identity through reporter merge and artifact transfer
  - Obligations/impact: T025/T026/T033-T035/T037/T048/T151/T152/T182/T183; FR-004/006/010/022, Q10/Q12/Q26. F08 loses route, correlation, audit, tuple cardinality and cycle provenance.
  - Developer: connect typed captured evidence from fixtures to reporter; reject missing evidence rather than defaulting success. Consume gap/coverage annotations and evaluator envelopes. Merge one row per persona/outcome/individual-hazard, join actual Test IDs/FR associations and retain adverse duplicate results. Carry one coordinator cycle ID across isolated shards; transfer metadata/JUnit/run JSON and sanitized media. Add deterministic tie ordering and explicit portfolio AU-v1 invalidation linkage.
  - Tester: existing capstone specs must emit and reread exact evidence IDs. Proposed reporter/merge cases under existing test roots cover absent attachments, two tests/one tuple, conflicting pass/fail, gap annotations, missing shards, shuffled input, same-SHA distinct cycles, absent seed and unknown revision. Future V-CLI/V-P/V-MERGE in a disposable checkout; assert real routes, valid UUIDs, joined IDs, shared cycle and byte-equal remerges.
  - Boundaries/dependencies: retain canonical/partial path contracts; AUD-034-003 consumes output and AUD-034-020 sanitizes/archives it. No portfolio or original evidence is changed now.
  - Done: each claim resolves to actual test, persisted audit, revision, seed and run; missing evidence cannot silently disappear.

- [ ] AUD-034-005 Bind fixture personas to authenticated incident-scoped access
  - Obligations/impact: T007-T010/T023/T025/T052-T054/T069-T145/T175; FR-007/019/021, ASM-011. F02's actor lookup/button hiding is not authorization, and the 68-count hides `afp` versus `afp-act` drift.
  - Developer: connect a dual-guarded seeded principal resolver to normal authorization and both browser/API contexts. Verify exact persona/function/permissions and enforce caller/organisation/incident scope on workspace and action APIs. Resolve ACT AFP through an explicit compatibility decision while preserving Commonwealth disambiguation. Production paths must ignore unsigned test headers and disallow unguarded test principals.
  - Tester: reuse [test-support](../../tests/contract/test_test_support_router.py#L50), [workspace](../../tests/contract/test_persona_workspace_contract.py#L1) and [RBAC](../../tests/e2e/web-coverage/cross-cutting/rbac-aiims.spec.ts#L16) tests. Control succeeds, Logistics is denied; foreign incident/organisation, removed/unknown persona, actor/header/body mismatch and unsigned production identity fail. Verify exact AFP IDs and all flag combinations with three real jurisdictions. Future V-API/V-P `rbac-aiims`.
  - Boundaries/dependencies: no IdP rewrite; preserve normal auth and test-only isolation. AUD-034-007/008/011 bind mutations to the resolved actor.
  - Done: the same seeded actor has identical permissions across fixture/UI/API/audit; denial is an audited authz decision, not a hidden button or 404.

- [ ] AUD-034-006 Use durable audit storage for evaluator and denial read-back
  - Obligations/impact: T008/T026/T046/T056/T066/T077/T179-T183; FR-010/026/028/029, Q22/Q24/Q26. F04's separate memory stores lose provenance across workers and restarts.
  - Developer: join evaluator, real denial, gap and rollback records through the existing append-only writer/repository and an authorized correlation projection. Preserve actor/rationale/source/confidence/original time; define an explicit per-run boundary rather than a fixed February timestamp, stable cursors and origin/detection cycles. Measure action-to-audit latency, bounding each polling request; isolate reset helpers to injected test stores.
  - Tester: extend [audit tests](../../tests/contract/test_outcome_evaluator.py#L245) and existing append-only/timeline specs. Seed pre-cycle/exact-boundary/current rows, append between pages, use two instances/restart, deny PUT/PATCH/DELETE and assert unchanged target plus a new denied event. Assert all fields and <=2-second action-to-audit timing; storage outage must not fabricate durable success. Future V-API/V-P `audit`.
  - Boundaries/dependencies: preserve `items`/cursor or explicitly version adapters; no new ledger. AUD-034-005 controls access and AUD-034-020 retention.
  - Done: returned evidence IDs survive restart, resolve across workers/cycles and cannot be replaced by synthetic UI denial claims.

- [ ] AUD-034-007 Enforce strict evaluator payload and identity contracts
  - Obligations/impact: T173/T174/T178/T180/T181/T184/T186; FR-028, Q21/Q27/Q29. F09 admits malformed metrics and unbound identity/correlation.
  - Developer: implement UUIDv4, strict per-SC non-negative finite metrics, integer clicks, readiness and SC/scenario compatibility in route/service. Apply response validation, preserve structured 400/404/422/503 errors, bind actor to principal and correct cross-jurisdiction UUID creation. Compile embedded payload schemas in the gate, enable format checking and fail if validators are unavailable.
  - Tester: extend [evaluator tests](../../tests/contract/test_outcome_evaluator.py#L107) with negative/bool/string/null/non-finite metrics, fractional clicks, extra fields, bad UUID versions, header/body mismatches, absent baseline, wrong SC/scenario, same-tuple replay versus fresh correlation and non-routable SCs. Future V-API; assert documented errors/no audit for rejected input and full response-schema validity rather than 500 or pass.
  - Boundaries/dependencies: retain Q29's five evaluators and named CI owners; AUD-034-005 supplies identity and AUD-034-008/022 resolve environment-dependent workspace adapters.
  - Done: accepted payloads and evidence conform to the actual contract; invalid metrics/actors cannot create a passing verdict.

- [ ] AUD-034-008 Require and exercise actual warning approval before publication
  - Obligations/impact: T015/T041/T054/T057/T064/T069/T073/T080/T119/T120/T146/T185; FR-007/009/011, SC-001, US1-1/2, US2-1/5. F01 and IC/PIO contract mismatch undermine the safety gate.
  - Developer: reject pending approval in the publish service, require an incident-scoped IC approval record and ignore body-supplied authority. Wire PIO request callback and real warning ID to IC decision/publish APIs; separate business approval from counterfactual evaluator paths. Validate nested model, icons, approved variants, de-escalation/all-clear and provenance before publication. Keep payload-only channel adapters explicitly non-delivery evidence.
  - Tester: reuse [warning contract](../../tests/contract/test_warning_contract.py#L1), HITL/AWS and IC/PIO specs. Drive draft -> request -> authorized approval -> publish -> audience read-back; cover missing/unauthorized/stale approval, malformed fields/icon, six hazard categories, threat reduction/all-clear and approval-service failure. Future targeted V-API and V-P `aws-warning|decision-support-hitl|public-information-officer|incident-commander`; every denial leaves publish state unchanged and emits actor-linked audit.
  - Boundaries/dependencies: use deterministic delivery-boundary doubles, never real public channels or mocked approval logic. AUD-034-005/006/014 provide actor/audit/language controls.
  - Done: active UI/API cannot publish without explicit scoped approval, and a publication bypass fails its tests.

- [ ] AUD-034-009 Measure real COP updates and cross-jurisdiction convergence
  - Obligations/impact: T016/T019/T055/T070/T137-T145; FR-008/015/016, SC-002/007, US3 and partition/level/conflict edges. F10 measures initial empty markup.
  - Developer: bind suite to the actual root mapper, incident and workflow clients, preserving `/disasters` -> `/`. Provide update subscription/polling, freshness indicators, peer incident views, AIIMS escalation and deterministic warning/closure reconciliation. Connect or explicitly retire dummy incident actions, not just their test IDs.
  - Tester: extend COP and all nine cross-jurisdiction files with two authenticated contexts and post-load incident/warning/closure changes. Assert <=5-second peer convergence, highest warning plus rationale, identical polygon/IDs, stale defaults/reconnect indicators and L1/L2/L3/NCM behavior. Future V-P `cop-refresh|cross-jurisdiction|dacc-state-controller`; missing/delayed update fails even if initial load is fast.
  - Boundaries/dependencies: reuse current map/services, distinguish historical read views from operational actions; AUD-034-005/008/004 provide identity/warning/evidence.
  - Done: source change-to-peer visibility, not navigation latency, proves shared COP and handoff.

- [ ] AUD-034-010 Connect span warnings to real supervisory assignments
  - Obligations/impact: T063/T069/T070/T072; FR-020/Q9, US2-2 and span edge. F11's empty props suppress required warnings and cannot coordinate save/delegation.
  - Developer: load incident direct reports and supervisory state into workspace panels, including Logistics; enforce IC/Tier-2/N/A rules and wire real delegation/pre-save warning. Resolve any stronger hard-save-block behavior explicitly rather than inferring it from prose inside the component.
  - Tester: extend existing span spec with 0/7/8 reports, IC, supervising/non-supervising Ops/Logistics, every other operational role and sectors outside command. Assert warning before save/within one COP refresh, working delegation, disappearance after reassignment and N/A suppression. Future V-P `span-of-control`.
  - Boundaries/dependencies: incident assignment API plus AUD-034-005/009; do not derive authority from any non-Planning role string.
  - Done: real report changes govern tested warning/delegation; active path never passes a hard-coded empty list.

- [ ] AUD-034-011 Exercise and secure five-stage evacuation
  - Obligations/impact: T058/T071/T078/T080/T148/T185/T188; FR-007/012, SC-003, US1-2 and vulnerable-population edges. F02/F12 leave stage ownership and transition behavior unproved.
  - Developer: connect UI to existing stage service/API; enforce stage-to-incident and actor scope on every operation. Reconcile warning-state fixture/model lists with Decision/Warning/Withdrawal/Shelter/Return. Preserve total/partial/phased, all approaches, shelter-in-place rationale, safe return and eight cohort controls.
  - Tester: reuse [evacuation contract](../../tests/contract/test_evacuation_contract.py#L1), [stage tests](../../tests/unit/test_evacuation_stages.py#L1) and existing five-stage/lead specs. Cover full progression, illegal/duplicate/reversed transitions, foreign incident stage, unauthorized actor, zero transport/shelter, every cohort, immediate/pre-warned hazards and 24-hour reference boundary. Future targeted V-API and V-P `evacuation-five-stage|predictive-risk-evac|watch-and-act-flood`.
  - Boundaries/dependencies: no engine rewrite or real evacuation; AUD-034-001/005/006 supply metrics, authority and audit.
  - Done: correct-incident UI progression and denied paths yield durable evidence and actual reference lead time.

- [ ] AUD-034-012 Validate managed recovery and sourced economic projections
  - Obligations/impact: T059/T065/T075/T076/T150/T185/T199; FR-013, plan source multiplicity, SC-005/Q7. F13 has tracking helpers but no proved managed handover or measured economic state.
  - Developer: connect recovery/utility views to editable four-environment state and existing handover service. Make unknown/error/loading explicit instead of retaining live-looking zeros. Persist overlap/handover, sourced baseline/projected loss and >=3 named sources where required; avoid fixed-percent projections.
  - Tester: reuse [recovery contract](../../tests/contract/test_recovery_contract.py#L1), [outcome tests](../../tests/unit/test_recovery_outcome.py#L1), recovery/outcome-5/utility specs. Update all four environments and reread after handover/reload; test 1/2/3 sources, absent/stale baseline, 29/30/31%, declined handover and unavailable claims endpoint. Future V-P `recovery|economic|outcome-5` and targeted V-API.
  - Boundaries/dependencies: preserve community-safe indicators; AUD-034-001/005/006 provide formulas/identity/audit; portfolio annualization remains outside this suite.
  - Done: actual sourced state and managed transition, not an unrelated evaluator, support recovery claims.

- [ ] AUD-034-013 Retain field actions until real replay is acknowledged
  - Obligations/impact: T061/T074/T185; FR-017, US2-3 and duplicate/partition edges. F03 can discard failed requests and report audit-only work as replayed.
  - Developer: lease/peek queued entries and delete only after successful acknowledgement; retain/retry network and non-success responses. Wire active offline capture/reconnect rather than the no-op worker. Use canonical batched envelopes, bound actor/tier/integrity and supported domain dispatch with durable dedupe. Preserve original time/actor/GPS within privacy rules; require approval for irreversible actions.
  - Tester: extend [queue tests](../../apps/web/tests/unit/spec_035/offline-queue-store.test.ts#L1), [replay contract](../../apps/api/tests/contract/spec_035/test_offline_replay.py#L1), existing field specs. Cover reload/reconnect, duplicate after ack, 500/403/timeout, restart between apply/ack, mixed actors, cap/displacement and stale life-safety input. Future V-U/V-API/V-P `offline`; assert one domain mutation/logical audit and failed entries retained with original authorship/time.
  - Boundaries/dependencies: web only, reuse IndexedDB/API; AUD-034-005/006/008 supply actor/audit/approval.
  - Done: neither reconnect nor retry loses a submitted action or falsely completes an audit-only record.

- [ ] AUD-034-014 Restore full P1 accessibility and rendered language coverage
  - Obligations/impact: T043/T044/T060/T073/T189/T192/T195/T197; FR-014, Q2/Q14/R-007/R-008, SC-001/008. F14 disables required rules and tests availability rather than rendered warnings.
  - Developer: restore WCAG 2.2 AA including contrast, select actual axe tests, enumerate every workspace/governance/warning/simulation/audit P1 surface and open appropriate gaps. Replace English carrier variants with approved language-pack content where actual translation is required; assert published payloads per hazard, not a language list. Resolve Indigenous placeholder/language authority explicitly; never invent endorsed translations.
  - Tester: existing accessibility/language/PIO/FR-030 specs need keyboard focus/activation, names, contrast failures, empty/error states, long text, EN/zh-Hans and approved ATSI representation/disclaimer across hazards. Assert exact payload/reviewer gates. Future V-A11Y/V-P `multilingual|warning`; separately record later assistive-technology/human review, since axe cannot certify it.
  - Boundaries/dependencies: English chrome stays out of scope; no screenshot campaign now. AUD-034-008/015/022 supply publication/classification/cultural authority.
  - Done: nonempty full-scope checks fail on regressions, and any human conformance claim has attributable evidence.

- [ ] AUD-034-015 Exercise the real sovereignty gateway and registry policy
  - Obligations/impact: T027/T042/T062/T185/T197; FR-018/Q3/NN-2/R-006. F15 never probes the model boundary or fails a missing registry.
  - Developer: validate actual `deployments` schema and fail closed; reconcile completed-review age versus renewal deadline with policy authority. Bind regulated-route/feature badges and carve-out navigation to configuration. Send synthetic PSPF/PII through the actual gateway, proving deny/mask before non-AU transport and safe classifier failure.
  - Tester: extend sovereignty and BoM relay specs with all regulated routes, missing/malformed registry, empty approvers, boundary/future/expired dates, clean/PSPF/PII/combined payloads and classifier failure. A capturing fake upstream must observe no sensitive transit and matching denied/masked audit. Future V-P `data-sovereignty|abc-sbs` plus targeted gateway contract tests after setup.
  - Boundaries/dependencies: no real PII/cloud calls or broadened carve-out; no automatic new Content Safety. AUD-034-005/006/020 establish authority/audit/residency.
  - Done: the connected three-part sovereignty contract and its explicit date-policy resolution are evidenced.

- [ ] AUD-034-016 Close simulation replay export and PPRR feedback
  - Obligations/impact: T020/T021/T067/T068/T077/T185; FR-006, US4-1/2/3, SC-010 and lessons quality gate. F16 confuses evaluator cache idempotency with simulation behavior.
  - Developer: extend POs through real isolated creation/run/playback, correct report-to-tenant mapping, persisted export and lessons-to-preparedness controls. Wire the report's Blob/repository dependency and fail persistence before publishing a retrievable URI; do not keep empty performance/coordination placeholders as computed results. Use participant-enforced playback and current actor identity. Add phase evidence for Prevention/Preparedness/Response/Recovery without rewriting the engine.
  - Tester: existing simulation/lessons specs need repeated multi-hazard seeds, participant/nonparticipant, distinct report ID, empty/partial streams, resume and duplicate lesson application. Compare normalized event sequence/properties across three runs; assert exported report persistence/audit and visible preparedness update. Future V-P `simulation-playback|lessons-management` and owning existing simulation contracts after authorized setup.
  - Boundaries/dependencies: no load/chaos, engine rewrite or live alerts; AUD-034-004/005/006 carry phase/tenant/audit provenance.
  - Done: real exercise and durable lessons/control changes prove US4, not a repeated calculator response.

- [ ] AUD-034-017 Enforce evidence-anchored gap transitions and cycle budgets
  - Obligations/impact: T038/T045-T047/T159/T161/T170/T183; FR-005/024/026/027, Q5/Q6/Q11/Q26. F17 permits arbitrary closure and has no iteration increment.
  - Developer: centralize allowed transitions, require PR/rerun/merge/pass/no-regression proof, increment once per cycle and halt a fourth unresolved attempt pending audited lead disposition. Reset regression budget while preserving origin/detection cycles; resolve Open/Reopened semantics explicitly. Atomically synchronize JSON/Markdown with full columns and durable operator/rationale/SHA/regression audit.
  - Tester: proposed state-machine tests beside [CLI unit tests](../../tests/unit/test_review_log_closure.py#L1) use temporary registers. Cover valid lifecycle, Open -> Closed, Closed -> promote, fake SHA/PR, missing rerun/pass, contradictory renders, counts 0/1/2/3/fourth, escalation freeze, regression at cap, absent metadata and concurrent writes. Future V-CLI; invalid transitions leave state/audit unchanged and exit nonzero.
  - Boundaries/dependencies: no GitHub edits or checkbox closure now; AUD-034-006/018/019 provide evidence and dispositions.
  - Done: every closure/reopening resolves to failing test, approved fix, passing revision and immutable event.

- [ ] AUD-034-018 Resolve tribunal votes and closure from verified roster evidence
  - Obligations/impact: T050/T157/T158/T162/T163/T168/T203; FR-024/025, ASM-006/Q13, SC-009/012. F18 admits duplicate/historical/small-panel votes and forbidden veto overrides.
  - Developer: implement missing ingestion flow, roster/standing checks and agent/gap/cycle dedupe. Compute objection support against 10/58/17 or explicitly defined relevant sub-panel; operational safety veto cannot be overridden. Persist dispositions and actual amendments, not TODOs. Count only proven meritorious closures with PR/diff/run evidence; distinguish absent review from a completed empty cycle. Exclude real escalations only; fix lowercase UUID meta-gap IDs against uppercase schema, include raw lists in audit and propagate creation failures.
  - Tester: extend [closure tests](../../tests/unit/test_review_log_closure.py#L53) for 6/10 versus 7/10 objections, missing/duplicate/forged voters, cross-cycle replay, QG-1-only veto, 43-vote override, unproven Closed, 4/5 closure, corrupt input, owner-name non-escalation and meta-gap failure. Workflow must fetch a named upstream run, increment cycles, collect votes/invoke closure and fail on errors. Future V-CLI using synthetic review fixtures only.
  - Boundaries/dependencies: AUD-034-017/022 establish state/schema; no actual agents or human approvals executed in this audit.
  - Done: unresolved safety veto or unproven merit blocks Ready, with replayable roster-bound cycle evidence.

- [ ] AUD-034-019 Detect regressions and restore verified known-good state
  - Obligations/impact: T049/T051/T155/T160/T161/T167/T171; FR-027, SC-010, US5-4, Q5/Q6. F19 stamps rollback claims and skips absent trace.
  - Developer: version/validate manifest with trace hash, run ID, seed, full SHA and environment deployment identifiers. Promote only after three independent same-seed passing signals, excluding volatile timestamps/UUIDs from equality. Download attributable trace in CD, reject partial/missing evidence, compare persona regressions and invoke authorized restoration before recording success. Preserve prior baseline on failure and account for the current App Service web deployment.
  - Tester: proposed manifest/regression cases under existing CLI unit roots cover unrelated-gap regression, changed seed, stale/missing/partial trace, skipped/failed reaffirmation, corrupt manifest, wrong environment, failed restoration and duplicate notification. Future V-CLI/V-MERGE; a separately approved sandbox rehearsal verifies actual restored revision and audit linkage, never a supplied string alone.
  - Boundaries/dependencies: no revert/deployment/branch now; coordinate existing CD and AUD-034-003/004/017/018.
  - Done: detection holds the gate closed and, when authorized, verified restoration precedes rollback-success evidence.

- [ ] AUD-034-020 Archive sanitized evidence through active immutable infrastructure
  - Obligations/impact: T011-T013/T036/T046/T151; FR-010/022, NN-2/3, RISK-07/10/12, R-013/016. F20 has unconnected 30-day retention and JSON-only sanitization.
  - Developer: compose into active IaC or explicitly map an approved existing archive, retaining container-scoped managed identity. Resolve seven-year period/versioning/locking with current governance; return resource ID and connect upload/audit writers with an explicit local-fallback flag. Sanitize names, precise GPS, free-text PII/PSPF, JSON/JUnit/attachments/images before transfer; discard regulated video or prove sanitization. Contributor is not a write-only role merely because prose calls it so.
  - Tester: proposed reporter/CLI redaction/upload fixtures and existing infra tests cover nested/free-text PII, spaced labels, GPS, media/sanitizer failure, Blob failure, wrong scope and short retention. Future V-CLI/V-INFRA after separate authorization; expect attributable reviewed minimal delta and correct AU archive, no unredacted upload on any failure.
  - Boundaries/dependencies: reuse policy-compliant approved resources/AVM; no infra refactor/new service by default. AUD-034-004/006 supply manifests and audit contract; no cloud check or screenshot capture now.
  - Done: sanitized artifacts reach the correct AU store with approved retention; local fallback cannot masquerade as archived proof.

- [ ] AUD-034-021 Align collection lint media and onboarding with the active toolchain
  - Obligations/impact: T001-T006/T010/T014-T022/T053/T151-T156/T164-T166/T200-T206; FR-001/021/022, SC-008/011. F21 leaves contract checks uncollected and commands inconsistent.
  - Developer: retain CTS config/working alias; deliberately collect the persona contract, fix `/api` and `items`, assert exact IDs/nonempty permissions. Set `forbidOnly`, workers/retries and failure-artifact/media policy. Lint actual repository-level suite files and enforce tag/permission/bail/wait rules. Align POs to active routes/actions/audit methods and fail on error markers; update CLI flags/generator mode without weakening obligations.
  - Tester: future V-COLLECT must show all intended tests and a nonempty axe project without duplicate legacy ownership. Positive fixture passes; `.only`, missing tag, permission literal, wait, unknown persona and wrong envelope fail. Rehearse one persona/all shards in disposable seeded checkout with exact versions, expected artifacts and total dev/CI budgets. Future V-P/V-A11Y/V-CLI.
  - Boundaries/dependencies: preserve existing framework, legacy projects and Playwright pin; no installs now. AUD-034-020 controls media before upload.
  - Done: documented commands select real checks, and missing collection/configuration cannot be mistaken for completed coverage.

- [ ] AUD-034-022 Reconcile authority conflicts and record attributable completion evidence
  - Obligations/impact: T013/T154/T164-T174/T181/T182/T201-T206, all formal review/CHK gates, ASM/HYP constraints, SC-006-SC-012. F22's checked work/CLEAN prose lacks run and review proof.
  - Developer: recover or formally replace missing syntheses; explicitly resolve AFP naming, depth keys/enum/steps, tuple/status contracts, evacuation states, manifest, date policy, production route extension and HYP-002 cohort/gate tension. Correct objection schema/template and bad task/checklist links in separately reviewed work. Preserve valid history; never backfill sign-off with checkboxes.
  - Tester/reviewer: later capture full revision, environment/flags/versions/seed, selected checks, four shard manifests, pass/skip/fail counts, three clean runs, elapsed budgets, accessibility, reviewed infra diff and real 10/58/17 panel/lead dispositions using existing checklists. Wrong-SHA/all-skipped/zero-row/missing-review bundles must be rejected. Future V-API/V-P/V-A11Y/V-MERGE/V-INFRA as applicable; human approval stays human work.
  - Boundaries/dependencies: all work above is future; no other report/index/source/evidence change or Asia expansion is authorized. No hypothesis is resolved without observation.
  - Done: each obligation has supported evidence or explicit approved replacement; unmeasured outcomes stay UNVERIFIED.

## Future Validation

Commands below are instructions, not audit actions. Use an authorized disposable checkout with isolated data,
Python >=3.12 and declared dependencies, Node 24, pnpm 10.6.3, Playwright 1.59.1 and browser assets.
V-P starts configured servers and is permitted only after the static-only restriction is lifted. Record
`AMA_TEST_SUPPORT=1`, `AMA_ENVIRONMENT=dev`, loopback API/upstream, known seed and production-auth mode.
Disable real delivery/cloud backends for deterministic tests. Proposed test paths above are future locations,
not linked evidence. No command in this section was executed.

| ID | Future command and expected outcome |
| --- | --- |
| V-API | `pytest tests/contract/test_test_support_router.py tests/contract/test_outcome_evaluator.py -q`, adding owning existing contract files named in each task. Expect strict positive/negative actor/scope/schema/audit assertions, not just arithmetic. |
| V-P | `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium`; append task-specific file filters or `--grep` expression. Expect actual UI workflows, no unexplained skips, valid trace/audit and contractual budgets. |
| V-A11Y | `pnpm --filter @ama/web exec playwright test --project=web-coverage-axe`; after selection repair, expect nonzero full-P1 scans/interactions with required rules. Human/assistive-technology review is separately recorded. |
| V-COLLECT | `pnpm --filter @ama/web exec playwright test --list`; expect deliberate collection including the persona contract and nonempty axe project. Listing is future work and does not prove execution. |
| V-CLI | `pytest tests/unit/test_review_log_closure.py -q`, then proposed gate/generator/reporter/manifest tests in existing test roots, with injected temporary registers/sinks/shards. Expect fail-closed cases and exact 2/3 and 80% boundaries; no GitHub writes or real agents. |
| V-U | `pnpm --filter @ama/web exec vitest run tests/unit/spec_035/offline-queue-store.test.ts`, extended to replay panel. Failed requests remain queued; real actions deduplicate and preserve actor/time. |
| V-MERGE | In a disposable copy: `python scripts/web-coverage/trace-merge.py --shards-dir tests/e2e/web-coverage/_artifacts --shard-glob 'coverage-trace.partial-*.json' --output-md specs/034-webapp-capstone-coverage/coverage-trace.md --output-json specs/034-webapp-capstone-coverage/coverage-trace.json`, then `pwsh scripts/web-coverage/verify-trace-determinism.ps1`. Expect four attributable shards, actual joined IDs and byte-equal remerges; this alone is not three suite executions. |
| V-INFRA | T013's documented Bicep build and group what-if remain unperformed. After AUD-034-020 resolves the active template, a separately authorized infrastructure reviewer supplies approved dev scope/parameters and runs its build/what-if plus existing IAM/retention checks. Expect minimal reviewed delta, seven-year retention and scoped identity with revision/environment evidence; no deployment is authorized here. |

## Reviewed Inputs And Authority

All 26 pre-existing files beneath this specification folder were read completely, including embedded amendments:

| Input | Scope of inspection |
| --- | --- |
| [Specification](spec.md#L1) | All 1,118 lines; Q1-Q29, five stories, 20 acceptance scenarios, 12 edge cases, FR-001 through FR-030, SC-001 through SC-012, 11 assumptions, three hypotheses, ten exclusions, constitution baseline and authority rules. |
| [Tasks](tasks.md#L1) | All 625 lines; cycle 0 and cycle 1, exact original check states, dependencies, notes, and review/integration obligations. |
| [Plan](plan.md#L1) | All 809 lines; both constitution checks, module and CI design, risks RISK-01 through RISK-16, retention, tribunal and rollback. |
| [Research](research.md#L1) | All 821 lines; R-001 through R-024, including rejected mock-only coverage, identity binding, metric provenance and artifact redaction. |
| [Data model](data-model.md#L1) | All 631 lines; all 13 entities and both sets of cross-entity invariants. |
| [Quickstart](quickstart.md#L1) | All 369 lines, original commands and appended implementation deltas and caveats. Commands were read, not run. |
| [Original analysis](analysis.md#L1) and [cycle-1 analysis](analysis-cycle1.md#L1) | Complete local design reviews, their claimed resolutions, retained inconsistencies and formal phase gates; not independent runtime evidence. |
| [Requirements checklist](checklists/requirements.md#L1) and [validation checklist](checklists/validation.md#L1) | All 16 unnumbered quality checks and CHK001 through CHK215, including cross-reference table and notes. |
| [Persona contract](contracts/persona-fixture.contract.md#L1) and [evaluator contract](contracts/outcome-evaluator.contract.md#L1) | Full text, embedded schemas, five checked persona acceptance items, request/response, activation, retention, and CI obligations. |
| [Trace schema](contracts/coverage-trace-row.schema.json#L1), [gap schema](contracts/gap-register-entry.schema.json#L1), [vote schema](contracts/review-vote.schema.json#L1), [objection schema](contracts/agent-objection.schema.json#L1), [cycle schema](contracts/cycle-metadata.schema.json#L1) | All five standalone local JSON contracts. The externally located [depth schema](../../tests/e2e/web-coverage/_lib/depth-profiles/_schema.json#L1) was also read completely. |
| [Trace](coverage-trace.md#L1), [gap Markdown](gap-register.md#L1), [gap JSON](gap-register.json#L1), [known-good](known-good.json#L1), [review log](review-log.md#L1) | Complete committed artifact state; assessment below. |
| [First-run record](_evidence/first-run.log#L1), [what-if record](bicep-whatif.txt#L1), [gap audit](_evidence/audit/web-coverage-gaps/2026-05-03/13.jsonl#L1), [trace audit](_evidence/audit/web-coverage-trace/2026-05-03/12.jsonl#L1) | Every line, including explicit skipped/deferred work and zero-row merge events. |

Explicit replacements applied: [Q25](spec.md#L582) replaces the Q19/Q21 activation-name drift with
`AMA_TEST_SUPPORT=1`; [Q26](spec.md#L624) moves the cycle timestamp from a per-gap cell to per-run
metadata; [Q29](spec.md#L748) replaces eleven routable evaluators with five and names CI owners for
SC-006 through SC-011. [Q23](spec.md#L518) assigns NEMA's DACC/JATWC scenario to its owning
Commonwealth folder. No other lower-level simplification is treated as an approved relaxation.

The five cited session-only persona/technical input files were not found by exact-filename workspace
search. Their original content and panel provenance cannot be reconstructed from claims in the plan.
This does not make the enumerated personas or existing source files missing; it limits ASM-001 verification.

## Saved Evidence Assessment

| Record | Assessment |
| --- | --- |
| [First-run record](_evidence/first-run.log#L3) | UNVERIFIED execution. Explicitly a lint-only starter; Playwright and trace determinism deferred to CI; no attributable full-suite run, SHA, machine shape or timings. |
| [What-if record](bicep-whatif.txt#L16) | UNVERIFIED what-if/deployment; explicitly skipped for lack of tenant context. Authored build-success prose lacks exact version/run attribution and describes 30-day, not seven-year, retention. |
| [Trace placeholder](coverage-trace.md#L7) | MISSING populated canonical coverage evidence. Header only, no passing persona/outcome/hazard rows. |
| [Trace audit](_evidence/audit/web-coverage-trace/2026-05-03/12.jsonl#L1) | Two authored merge events with `row_count: 0`, `shard_count: 3`; not proof of a four-shard passing run or three consecutive executions. |
| [Closed gap](gap-register.json#L16) and [gap audit](_evidence/audit/web-coverage-gaps/2026-05-03/13.jsonl#L1) | PARTIAL closure record: PR and short SHA present, but no failing/passing Test ID, run on merge SHA, operator/rationale provenance, regression comparison, or demanded assertion diff. Notes still say review pending. |
| [Known-good](known-good.json#L1) | MISSING usable restoration baseline: empty entries and null update revision/time; shape differs from the data-model manifest. No successful deployment inferred. |
| [Review log](review-log.md#L8) | UNVERIFIED tribunal and human sign-off: no votes, placeholder run/date and pending panel approvals; header uses 30/35/20 instead of 10/58/17. |
| [Validation checklist](checklists/validation.md#L23) | 215 unchecked obligations. Neither these boxes nor 206 checked tasks establish execution or outcomes. |
| [Ignored cycle metadata](../../tests/e2e/web-coverage/_artifacts/cycle-metadata.json#L1), [partial trace](../../tests/e2e/web-coverage/_artifacts/coverage-trace.partial-1.json#L1), [run JSON](../../tests/e2e/web-coverage/_artifacts/web-coverage.json#L1) and [JUnit](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L1) | Historical local evidence, not accepted current-run proof. Metadata identifies `f7fb35e6bf78b8249c4b7012dabd4223b3b905a2`; JSON/JUnit record 2026-05-06, Playwright 1.59.1, 76 skipped interface tests, zero expected passes, zero unexpected/flaky, approximately 399 ms and zero trace rows. No cryptographic manifest binds those files to each other; none proves spec-034 workflows or the audited SHA. |

## Coverage Accounting

Inventory: **206 original tasks**, all `[X]`, no suffixed IDs; **30 FRs**, **12 SCs**, **20 numbered
acceptance scenarios**, **12 edge cases**, **215 CHK items**, **16 unnumbered quality checks**, and
**five checked persona-contract acceptance items**. No separately numbered NFRs exist: nonfunctional
constraints are carried by FRs, SCs, assumptions, constitution baseline and plan/research obligations below.
The original `[X]` state is normalized to `[x]` in the task table; it is not the review status.

### Functional Requirements

| Requirement | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Generator registry](../../scripts/web-coverage/_lib/persona_spec_generator.py#L77) and all four suite folders exist; 90 persona files, but ACT uses `afp-act` and documented mappings/default generation drift. | AUD-034-002, AUD-034-005, AUD-034-021 |
| FR-002 | PARTIAL | [Generated body](../../scripts/web-coverage/_lib/persona_spec_generator.py#L528) and all 90 bodies resolve identity/evaluate/read audit but never execute persona-specific control interaction; no attributable 68/68 passing run. | AUD-034-001, AUD-034-002 |
| FR-003 | PARTIAL | [Nine bridge definitions](../../scripts/web-coverage/_lib/persona_spec_generator.py#L337) exist; [template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) compares evaluations, not shared incident/COP/COMDISPLAN state. | AUD-034-002, AUD-034-009 |
| FR-004 | PARTIAL | [Reporter](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L225), [merge](../../scripts/web-coverage/trace-merge.py#L49) and schemas exist; wrong dedupe key/column order, missing actual Test IDs/audit/correlation/metadata and portfolio invalidation; [canonical trace](coverage-trace.md#L7) empty. | AUD-034-004 |
| FR-005 | PARTIAL | [CLI](../../scripts/web-coverage/gap-register.py#L123) writes register and local audit; not every failure/gap is captured and transition evidence is unchecked. JSON is actual source, Markdown differs from specified columns. | AUD-034-017 |
| FR-006 | PARTIAL | [Simulation/lessons tests](../../tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts#L28) evaluate economics; [trace type](../../tests/e2e/web-coverage/_support/types/coverage.d.ts#L5) has no phase tag. Real preparedness/simulation surfaces exist but PPRR loop is not covered. | AUD-034-004, AUD-034-016 |
| FR-007 | PARTIAL | [RBAC tests](../../tests/e2e/web-coverage/cross-cutting/rbac-aiims.spec.ts#L28) check visibility; [workspace API](../../apps/api/app/api/routes/personas.py#L7) lacks caller scope, and fixture headers do not become API principals. | AUD-034-005, AUD-034-008, AUD-034-011 |
| FR-008 | PARTIAL | [COP test](../../tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts#L27) times static initial list, not <=5-second shared refresh. [Real map](../../apps/web/src/app/page.tsx#L89) is a different path. | AUD-034-009 |
| FR-009 | PARTIAL | [Publish service](../../apps/api/app/services/public_alert_service.py#L48) accepts pending approval; [HITL test](../../tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts#L53) mistakes missing metrics for no approval. | AUD-034-008 |
| FR-010 | PARTIAL | [Audit-list](../../apps/api/app/services/outcome_evaluator_service.py#L292) reads only process memory; [observer](../../tests/e2e/web-coverage/_support/fixtures/auditObserver.fixture.ts#L38) starts its timer after actions and permits a request to exceed deadline. Actual immutable/denial provenance and <=2-second end-to-end outcome unproved. | AUD-034-006, AUD-034-020 |
| FR-011 | PARTIAL | [Warning chain/CAP API](../../apps/api/app/api/routes/warning_chain.py#L27) exists; [coverage test](../../tests/e2e/web-coverage/cross-cutting/aws-warning-compliance.spec.ts#L25) evaluates the same bushfire seed under six names. No composed nested payload/icon/de-escalation/all-clear chain is asserted. | AUD-034-008, AUD-034-014 |
| FR-012 | PARTIAL | [Five-stage API](../../apps/api/app/api/routes/evacuation.py#L82) exists; [test](../../tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts#L29) does not transition/filter stages or cohorts; model/fixture warning states conflict. | AUD-034-011 |
| FR-013 | PARTIAL | [Tracking service](../../apps/api/app/services/recovery_service.py#L25) groups real indicators into four environments; [test](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L32) ignores state and managed handover. | AUD-034-012 |
| FR-014 | PARTIAL | [Test scope](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) is three indexes; [axe](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) disables contrast; language inventory is not rendered per-hazard warning evidence. | AUD-034-014 |
| FR-015 | PARTIAL | [NEMA scenario](../../tests/e2e/web-coverage/sectors/commonwealth/nema.activate-comdisplan.spec.ts#L1) and [bridge template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) contain no COMDISPLAN/DACC/NCM/NJCOP lifecycle or shared incident mutation. Newer sector pages are not exercised. | AUD-034-002, AUD-034-009 |
| FR-016 | PARTIAL | [Five fixtures](../../tests/e2e/web-coverage/_support/validators/outcome-proxy.ts#L8) name hazard pairs; neither assertions nor [gate](../../scripts/web-coverage/_lib/schema_validators.py#L82) prove each individual pair. Tsunami persona evaluates lives arithmetic, not AWS payload. | AUD-034-001, AUD-034-002, AUD-034-003 |
| FR-017 | PARTIAL | [Queue](../../apps/web/src/lib/offline/queue-store.ts#L215) drains before ack, [worker](../../apps/web/public/offline-sw.js#L8) no-ops, [test](../../tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts#L30) remains online. Original timestamp/authorship and actual dispatch are not validated. | AUD-034-013 |
| FR-018 | PARTIAL | [Sovereignty test](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L29) substitutes rank/evaluator checks; [registry](../../infra/parameters/foundry-carveout.yaml#L14) has different schema/date semantics. One badge is not every regulated route or gateway protection. | AUD-034-015, AUD-034-020 |
| FR-019 | PARTIAL | [Dynamic workspace](../../apps/web/src/app/workspaces/[personaId]/page.tsx#L17) and task/panel rendering exist; [PO](../../tests/e2e/web-coverage/_support/pages/workspaces.po.ts#L20) only opens index. Canonical AFP drift and generic/disconnected panel state prevent all-68 task-tailored proof. | AUD-034-002, AUD-034-005, AUD-034-010 |
| FR-020 | PARTIAL | [Panel](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23) has >7 logic but [parent](../../apps/web/src/components/workspaces/persona-workspace.tsx#L84) passes empty data/omits Logistics; test never assigns reports. | AUD-034-010 |
| FR-021 | PARTIAL | [Guard](../../apps/api/app/middleware/test_support_guard.py#L31), loopback config, seed reads and driver mappings exist; exact actor binding and deterministic rerun signal do not. `afp-act` replaces canonical `afp` without a spec-034 replacement record. | AUD-034-005, AUD-034-019, AUD-034-021 |
| FR-022 | PARTIAL | [Reporters](../../apps/web/playwright.config.cts#L42) emit JSON/JUnit; [CI glob](../../.github/workflows/ci.yml#L317) misses files and no failure media policy/redacted durable archive is wired. | AUD-034-004, AUD-034-020, AUD-034-021 |
| FR-023 | PARTIAL | [Three jobs](../../.github/workflows/ci.yml#L258) exist; gate heuristics, skipped rows, missing inputs and unresolved statuses break (a)-(e). [Branch rule](../../.github/branch-protection.json#L2) is explicitly descriptive only. | AUD-034-003 |
| FR-024 | PARTIAL | [Iteration workflow](../../.github/workflows/web-coverage-iteration.yml#L69) runs hard-coded cycle-1 summaries, no vote collection or closure; [CLI](../../scripts/web-coverage/gap-register.py#L154) never increments cycles. | AUD-034-017, AUD-034-018 |
| FR-025 | PARTIAL | [Gap tooling](../../scripts/web-coverage/gap-register.py#L123) exists but no automatic all-failure register or enforced closure of product gaps. Pending/closed candidate prose is not proof. | AUD-034-003, AUD-034-017, AUD-034-022 |
| FR-026 | PARTIAL | [Closed record](gap-register.json#L9) has PR/short SHA only; no failing/passing Test ID/run/diff, and [close](../../scripts/web-coverage/gap-register.py#L165) requires none. | AUD-034-017, AUD-034-022 |
| FR-027 | PARTIAL | [Rollback CLI](../../scripts/web-coverage/known-good.py#L148) records supplied claims; no cross-run detection or actual restore. [Manifest](known-good.json#L4) empty. | AUD-034-019 |
| FR-028 | PARTIAL | [Routed evaluator](../../apps/api/app/api/routes/outcome_evaluator.py#L81) and [audit list](../../apps/api/app/api/routes/audit_list.py#L35) exist with named SC owners/idempotency; schema/retention incomplete. [Router extension](../../apps/api/app/api/router.py#L149) deliberately adds production reach and ungated fallbacks, conflicting with original prohibition, not absence. | AUD-034-006, AUD-034-007, AUD-034-022 |
| FR-029 | PARTIAL | [68-profile gate](../../scripts/web-coverage/_lib/schema_validators.py#L213) validates file shapes; [generator](../../scripts/web-coverage/_lib/persona_spec_generator.py#L834) ignores required workflow steps and rejects permitted UI-only/read-only routes. No structured gap opener. | AUD-034-002, AUD-034-004 |
| FR-030 | PARTIAL | All 13 named files exist under owning jurisdiction, but [SAPOL](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L25) and peers only open index/evaluate/read audit. [BoM](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts#L26) asserts no ABC/SBS source or languages. Every scenario is accounted in T187-T199 below. | AUD-034-002, AUD-034-008, AUD-034-012, AUD-034-014, AUD-034-015 |

### Success Criteria

| Criterion | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| SC-001 | PARTIAL | [Outcome 1](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L26) does not publish approved Emergency Warnings, time <=2-minute reach or operate eight population filters/language variants. | AUD-034-001, AUD-034-008, AUD-034-014 |
| SC-002 | PARTIAL | [Formula](../../apps/api/app/services/outcome_evaluator_service.py#L141) asserts relative 50% only, not each persona's signal-to-approved-action and stricter 5/15/30-minute ceilings or <=5-second span update. | AUD-034-001, AUD-034-009, AUD-034-010 |
| SC-003 | PARTIAL | [Outcome 3](../../tests/e2e/web-coverage/capstone/outcome-3-tropical-cyclone-flood.spec.ts#L21) supplies 26 hours, with no predictive-to-five-stage transition/reference timestamp; pre-warned bushfire path also unproved. | AUD-034-001, AUD-034-011 |
| SC-004 | PARTIAL | [Outcome 4](../../tests/e2e/web-coverage/capstone/outcome-4-bushfire-cyclone-logistics.spec.ts#L21) supplies six clicks; no actual match/allocation or stricter 70% baseline and 7/12 ceilings. | AUD-034-001, AUD-034-002, AUD-034-009 |
| SC-005 | PARTIAL | [Outcome 5](../../tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts#L45) reverses inequality and never reads editable environments/handover; baseline/projected values are canned, not post-handover source. | AUD-034-001, AUD-034-012 |
| SC-006 | UNVERIFIED | [Trace](coverage-trace.md#L7) has no persona rows; 90 authored files and 68 drifted identities do not establish 68 passing persona workflows. [Saved JUnit](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L1) is all skipped. | AUD-034-002, AUD-034-003, AUD-034-022 |
| SC-007 | UNVERIFIED | [Bridge template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) does not execute integration; no passing 8/8 + Commonwealth evidence. | AUD-034-002, AUD-034-009, AUD-034-022 |
| SC-008 | UNVERIFIED | All 15 cross-cutting bodies inspected; weak substitutes and disabled contrast do not establish 100% compliance or a clean runtime run. [First run](_evidence/first-run.log#L22) deferred. | AUD-034-008 through AUD-034-016, AUD-034-022 |
| SC-009 | UNVERIFIED | [Review log](review-log.md#L8) has no votes or panel sign-offs; one Closed candidate does not prove all meritorious objections resolved. | AUD-034-017, AUD-034-018, AUD-034-022 |
| SC-010 | UNVERIFIED | [Determinism script](../../scripts/web-coverage/verify-trace-determinism.ps1#L16) compares saved merges; [two zero-row audit events](_evidence/audit/web-coverage-trace/2026-05-03/12.jsonl#L1) are not three clean executions. | AUD-034-019, AUD-034-022 |
| SC-011 | UNVERIFIED | [CI shard timeout](../../.github/workflows/ci.yml#L261) is 45 minutes but not total elapsed budget; no representative <=30-minute dev/full <=45-minute CI measurement. Skipped 0.4-second run is not proof. | AUD-034-021, AUD-034-022 |
| SC-012 | PARTIAL | [Ratio logic](../../scripts/web-coverage/review-log.py#L282) and [unit assertions](../../tests/unit/test_review_log_closure.py#L83) exist but assume merit, omit closure proof, exclude owners and accept empty input; no actual cycle closure evidence. | AUD-034-018, AUD-034-022 |

### Acceptance Scenarios

Review IDs below label the original numbered scenarios; none is a new requirement.

| Scenario | Status | Required result versus inspected evidence | Follow-up |
| --- | --- | --- | --- |
| US1-1 | PARTIAL | [IC scenario](../../tests/e2e/web-coverage/operational/incident-commander.approve-cross-agency-action.spec.ts#L1) evaluates only outcome 1, not cross-agency approval, full audit fields/2 seconds or both #1/#2 trace. | AUD-034-001, AUD-034-002, AUD-034-006, AUD-034-008 |
| US1-2 | PARTIAL | [SES-NSW](../../tests/e2e/web-coverage/sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts#L1) no Watch and Act composition/IC request/predictive evacuation transition. | AUD-034-002, AUD-034-008, AUD-034-011 |
| US1-3 | PARTIAL | [NEMA](../../tests/e2e/web-coverage/sectors/commonwealth/nema.activate-comdisplan.spec.ts#L1) supplies logistics metric; no COMDISPLAN/NJCOP/consequence metrics/match. | AUD-034-002, AUD-034-009 |
| US1-4 | CONFLICT | [Scenario prose](spec.md#L814) uses persona/outcome and older columns; [Q10](spec.md#L233) explicitly replaces cardinality with persona/outcome/hazard. Actual [merge](../../scripts/web-coverage/trace-merge.py#L49) implements neither required joined-ID key. | AUD-034-004, AUD-034-022 |
| US1-5 | PARTIAL | [PO](../../tests/e2e/web-coverage/_support/pages/workspaces.po.ts#L20) visits index, so a missing persona landing page is not detected as required `GAP-WORKSPACE-MISSING`. | AUD-034-002, AUD-034-004 |
| US2-1 | PARTIAL | [HITL test](../../tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts#L53) tests malformed metrics, not denied alerts/evacuation/reallocation followed by real IC approval and audit. | AUD-034-005, AUD-034-006, AUD-034-008 |
| US2-2 | PARTIAL | [Span test](../../tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts#L25) never creates eighth report or observes warning/delegation. | AUD-034-010 |
| US2-3 | PARTIAL | [Offline test](../../tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts#L30) sends online repeats; no offline GPS capture/reconnect/original author-time proof. | AUD-034-013 |
| US2-4 | PARTIAL | [Three-page scan](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) omits most routes, keyboard/focus journeys and disabled contrast. | AUD-034-014 |
| US2-5 | PARTIAL | [AWS test](../../tests/e2e/web-coverage/cross-cutting/aws-warning-compliance.spec.ts#L25) has no draft/nested/icon/variant/de-escalation/publish assertion. | AUD-034-008, AUD-034-014 |
| US3-1 | PARTIAL | [NSW/VIC scenario](../../tests/e2e/web-coverage/sectors/nsw/cross-jurisdiction-nsw-vic-bushfire.spec.ts#L1) checks evaluator audit visibility, not same incident COP/AWS/history. | AUD-034-002, AUD-034-009 |
| US3-2 | PARTIAL | [Commonwealth bridge](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-state-controller-bridge.spec.ts#L1) has no state request/COMDISPLAN/DACC A-B-C/arrival/mission-close IDs. | AUD-034-002, AUD-034-009 |
| US3-3 | MISSING | All nine bridge bodies/owning [generator](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) inspected: no two-police closure update/merged polygon/<=5-second assertion. This is missing scenario behavior, not a declaration that no map feature exists. | AUD-034-009 |
| US4-1 | PARTIAL | [Real create UI](../../apps/web/src/app/simulations/create/page.tsx#L39) exists; [suite](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L32) never creates/runs it. | AUD-034-016 |
| US4-2 | PARTIAL | [Playback UI](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L15) and participant service exist; suite compares evaluator cache, not normalized timeline bytes. | AUD-034-016, AUD-034-019 |
| US4-3 | PARTIAL | [Report UI](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L30) reads wrong ID domain and has no export/preparedness controls; [lessons spec](../../tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts#L28) substitutes economics. | AUD-034-016 |
| US5-1 | PARTIAL | [Panel resolver](../../scripts/web-coverage/review-log.py#L114) emits TODO amendment stubs; no objection -> reviewed spec change -> test update proof. | AUD-034-017, AUD-034-018 |
| US5-2 | PARTIAL | [Gate](../../scripts/web-coverage/_lib/schema_validators.py#L66) only checks Open Markdown rows; no meritorious/veto/state completeness or audited flip. | AUD-034-003, AUD-034-018 |
| US5-3 | PARTIAL | [Escalate](../../scripts/web-coverage/gap-register.py#L227) can check count >=3, but nothing increments count, freezes later promote/close, or requires lead disposition. | AUD-034-017, AUD-034-018 |
| US5-4 | PARTIAL | [Rollback](../../scripts/web-coverage/known-good.py#L148) only records strings; no unrelated-gap regression detection/revert or verified restored SHA. | AUD-034-017, AUD-034-019 |

### Edge Cases

| Edge | Status | Static assessment | Follow-up |
| --- | --- | --- | --- |
| EC01 - missing persona workspace | PARTIAL | [Workspace UI](../../apps/web/src/app/workspaces/[personaId]/page.tsx#L57) handles 404, but suite opens index and emits no required structured gap. | AUD-034-002, AUD-034-004 |
| EC02 - overlapping agency terminology/iconography | MISSING | All persona bodies/declared generator checked; no NSW/VIC-specific designation/icon assertion. [Generator](../../scripts/web-coverage/_lib/persona_spec_generator.py#L528) is controlling template. | AUD-034-002 |
| EC03 - conflicting cross-border AWS levels | MISSING | [Bridge template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) has no conflict/maximum-severity/reconciliation audit case. | AUD-034-008, AUD-034-009 |
| EC04 - de-escalation/all-clear | PARTIAL | [Warning-chain backend](../../apps/api/app/api/routes/warning_chain.py#L27) exists; AWS suite never transitions a warning. | AUD-034-008 |
| EC05 - replay already-synced action | PARTIAL | [Evaluator duplicate test](../../tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts#L30) does not test durable real-action dedupe after reconnect/restart. | AUD-034-013 |
| EC06 - AIIMS Level 1/2/3 transition | MISSING | No level transition in persona/bridge/COP suite bodies; [COP test](../../tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts#L27) only navigates. | AUD-034-001, AUD-034-009 |
| EC07 - eighth report before save | PARTIAL | [Panel](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23) threshold exists but disconnected; no test report assignment/save/delegate. | AUD-034-010 |
| EC08 - vulnerable evacuation filters/community warning | PARTIAL | [Stages API](../../apps/api/app/api/routes/evacuation.py#L47) accepts vulnerable status; suite does not assert cohorts/filters/languages or priority. | AUD-034-011, AUD-034-014 |
| EC09 - missing AU badge | PARTIAL | [Sovereignty](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L12) checks one dashboard badge, not all regulated routes or `GAP-DATA-SOV-BANNER`. | AUD-034-004, AUD-034-015 |
| EC10 - Foundry carve-out feature/list discoverability | PARTIAL | Registry exists; [coverage body](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L43) never navigates compliance list or feature badge. | AUD-034-015 |
| EC11 - cross-jurisdiction network partition | MISSING | No partition/stale-peer/reconnect control interaction in all nine [bridge bodies](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648). | AUD-034-009, AUD-034-013 |
| EC12 - audit PUT/PATCH tampering | PARTIAL | [Append-only spec](../../tests/e2e/web-coverage/cross-cutting/audit-append-only.spec.ts#L29) rereads evaluator row without mutation; separate denial buffer is not joined to list. | AUD-034-006 |

### Clarification And Scope Coverage

| Binding | Status | Assessment and follow-up |
| --- | --- | --- |
| Q1 | PARTIAL | Contractual thresholds not all measured, F05; AUD-034-001. |
| Q2 | PARTIAL | zh-Hans/ATSI per-hazard rendering not proved; approved placeholder disclaimer/language authority needed, F14; AUD-034-014. |
| Q3 | PARTIAL | Display/gateway/current-registry triple not exercised, F15; AUD-034-015. |
| Q4 | UNVERIFIED | No attributable full 30/45-minute measurements; AUD-034-021/022. |
| Q5 | PARTIAL | Three-cycle guard lacks increment/verified rollback; AUD-034-017/019. |
| Q6 | PARTIAL | US5-3/4 written but actual escalation/disposition/restore not wired; AUD-034-017/019. |
| Q7 | PARTIAL | Correct economic formula exists; no sourced post-handover per-scenario measurement, F05/F13; AUD-034-001/012. |
| Q8 | PARTIAL | Hazard labels exist; separate paired behaviors and earthquake/tsunami AWS not established; AUD-034-001/002. |
| Q9 | PARTIAL | Empty span props, Logistics omission and incomplete N/A negatives; AUD-034-010. |
| Q10 | PARTIAL | Explicit three-part key replaces earlier US1-4 key, but merge uses FR/test ID and displays counts; AUD-034-004. |
| Q11 | PARTIAL | No validated rerun/merge/pass transition or full audit; AUD-034-017. |
| Q12 | MISSING | No inspected emitter/merge/gate path invalidates portfolio AU-v1 on supporting failure; AUD-034-004. |
| Q13 | CONFLICT | Submitted approval fraction/historical override contradict fixed-panel merit and non-overridable safety veto; AUD-034-018. |
| Q14 | PARTIAL | Three index scans are not all workspace and P1 routes; AUD-034-014. |
| Q15 | PARTIAL | Executable `test.fail(true)` absent in 90 bodies, but real workflow-state transition still missing; AUD-034-002. |
| Q16 | PARTIAL | Evaluator/list routes added; payload/lifecycle/audit incomplete; AUD-034-006/007. |
| Q17 | PARTIAL | All six SA/WA/TAS files exist but use generic evaluator bodies; AUD-034-002. |
| Q18 | PARTIAL | All seven ACT/NT/Commonwealth/cross-sector files exist, without required specific behavior; AUD-034-002/012/014/015. |
| Q19 | SUPERSEDED | Name/diagnosis explicitly corrected by [Q25](spec.md#L582); not an unresolved demand to rename middleware. Current behavior assessed under Q25. |
| Q20 | PARTIAL | Schema/68 files exist, but schema/task keys/step count diverge and generator ignores steps; AUD-034-002/022. |
| Q21 | PARTIAL | Idempotency/range/error routes authored; strict schemas/actor binding incomplete. Activation/range expressly replaced by Q25/Q29; AUD-034-007. |
| Q22 | PARTIAL | Default/all and limit filtering implemented only on memory with fixed timestamp; retention/tamper/cross-cycle proof absent; AUD-034-006. |
| Q23 | IMPLEMENTED | NEMA and BoM scenarios are under Commonwealth, utility under cross-sector; location preserved. Reach/tag execution remains FR-003/FR-030 work, AUD-034-002. |
| Q24 | PARTIAL | Read-only enum/profile artifacts exist; generator still requires evaluator, no actual tamper/report/brief acknowledgement; AUD-034-002/006/016. |
| Q25 | IMPLEMENTED | [Guard](../../apps/api/app/middleware/test_support_guard.py#L27), [CI export](../../.github/workflows/ci.yml#L307) and [quickstart](quickstart.md#L36) use canonical `AMA_TEST_SUPPORT=1`. Other production registration is separately a contract conflict. |
| Q26 | PARTIAL | Reporter emits metadata but not full seed payload hash/cycle-start semantics or merged header; origin cycle overwritten on regression; AUD-034-004/006/017. |
| Q27 | PARTIAL | Accepted contract and embedded schemas authored, but gate does not validate captured requests/responses; AUD-034-007/022. |
| Q28 | PARTIAL | Draft-07 schema and task family present, not actual workflow translation or structured gap creation; AUD-034-002. |
| Q29 | IMPLEMENTED | Five routable SCs and named six CI owners appear in [service](../../apps/api/app/services/outcome_evaluator_service.py#L45) and [contract tests](../../tests/contract/test_outcome_evaluator.py#L158). Actual CI obligations still fail their independent SC coverage. |
| ASM-001 | UNVERIFIED | Five cited session syntheses absent from bounded exact-filename search; cannot establish source-to-persona must-do fidelity; AUD-034-022. |
| ASM-002 | PARTIAL | Seed file reads deterministic; live traces include volatile IDs/times and three clean runs absent; AUD-034-004/019. |
| ASM-003 | PARTIAL | Real dynamic routes remain; `/disasters` explicitly redirects to root, POs target indexes/old selectors; AUD-034-002/009/021. |
| ASM-004 | PARTIAL | Plan cannot relax contractual thresholds; implementation does, F05; AUD-034-001. |
| ASM-005 | IMPLEMENTED | Canonical inventory is Australian; no PH/JP/BD personas added. Asian-language codes alone in AU CALD fixtures do not prove non-AU cohort leakage. |
| ASM-006 | PARTIAL | Authored tribunal differs from 10/58/17 merit/veto and no completed panel record; AUD-034-018/022. |
| ASM-007 | UNVERIFIED | Plan justifies one container; no attributable technical approval/what-if and actual retention differs; AUD-034-020/022. |
| ASM-008 | PARTIAL | Constitutional baseline is not met by evaluator substitution across roles; AUD-034-005 through AUD-034-016. |
| ASM-009 | CONFLICT | Contrast suppression and missing rendered variants are treated as tolerable in helper prose despite mandatory uplift rule; AUD-034-014/022. |
| ASM-010 | PARTIAL | Operator budgets cannot be replaced by infra timeouts/calculator constants; AUD-034-001/009/019/021. |
| ASM-011 | PARTIAL | Seed identity lookup exists, but actor authorization and canonical IDs differ; AUD-034-005. |
| HYP-001 | UNVERIFIED | No three clean runs or attributable evaluator-panel acceptance of proxy validity; AUD-034-019/022. |
| HYP-002 | CONFLICT | No measured >30%-uplift tally or approved validated-cohort boundary; stated reduced-cohort gate conflicts with hard 68/68 gate unless explicitly rebaselined; AUD-034-003/022. |
| HYP-003 | UNVERIFIED | No grading/85-agent evidence accepting Asia deferral; AU-only scope is intentional, acceptance not inferred; AUD-034-022. |
| OOS-001 | IMPLEMENTED | No non-AU personas required/created by scoped suite; maintain explicit Asia deferral. |
| OOS-002 | IMPLEMENTED | Requested translation remains warning payloads, not dashboard chrome. |
| OOS-003 | PARTIAL | One justified container authored in inactive template, no approval/deployed proof; conditional Content Safety gap closure unproved; AUD-034-020/022. |
| OOS-004 | IMPLEMENTED | Existing simulation engine reused by product; future suite must exercise it, not rewrite it. |
| OOS-005 | IMPLEMENTED | No pixel-perfect regression assertion in inspected suite; failure media is distinct. |
| OOS-006 | IMPLEMENTED | No load/soak/chaos workload in spec-034 suite; controlled partition edge case is functional, not a chaos campaign. |
| OOS-007 | CONFLICT | Original fixture-only IdP boundary coexists with explicitly added production-auth registration; not silently SUPERSEDED; AUD-034-005/022. |
| OOS-008 | IMPLEMENTED | Scoped requested IaC addition is a child resource/assignment, not wholesale infra rewrite; active wiring still incomplete. |
| OOS-009 | IMPLEMENTED | Offline work is web IndexedDB/service-worker, not mobile-native. |
| OOS-010 | UNVERIFIED | Authored outputs intended internal; actual archive access/retention/publication state cannot be established here; AUD-034-020/022. |

### Nonfunctional And Unnumbered Constraints

These audit labels group original unnumbered obligations without inventing NFR IDs. Every sub-obligation
listed remains part of its group and is linked to the concrete findings/tasks above.

| Audit group | Status | Complete obligation set and assessed evidence | Follow-up |
| --- | --- | --- | --- |
| U01 - AEMA eleven principles | PARTIAL | Primacy of life; comprehensive; collaborative; coordinated; flexible; risk-based; shared responsibility; resilience; communication; integrated; continual improvement. [Constitution](../../.specify/memory/constitution.md#L18) and [baseline](spec.md#L30) require behavior, not generic `II` tags. F01/F06/F10/F12-F16/F18 leave action/phase/multiagency/learning proofs incomplete. | AUD-034-002, AUD-034-008 through AUD-034-018 |
| U02 - AIIMS functions and levels | PARTIAL | Control, Intelligence, Planning, Operations, Logistics, Public Information; distinguish command/control/coordination; levels 1/2/3 and scoped COP. [Seed map](../../packages/domain/src/domain/seed/aiims_function_map.json#L1) and spec's five-value test enum omit Intelligence, requiring explicit applicability resolution. No level transitions asserted. | AUD-034-005, AUD-034-009, AUD-034-010, AUD-034-022 |
| U03 - Ten warning principles | PARTIAL | Life-saving, empowering, trusted/verifiable, risk-scaled, timely/targeted/tailored, impact, action, clarity, accessible, bigger-picture. [Warning API](../../apps/api/app/api/routes/warning_chain.py#L143) exposes compliance but suite never reads it or published warnings. | AUD-034-008, AUD-034-014 |
| U04 - Total warning system | PARTIAL | Situational awareness, monitoring/prediction, construction, interpretation, communication, community response. [Constitution](../../.specify/memory/constitution.md#L119); rank/evaluator tests stop before delivery/response. | AUD-034-001, AUD-034-008, AUD-034-009 |
| U05 - Evacuation doctrine | PARTIAL | Five stages, pre-warned/immediate, three approaches, total/partial/phased, shelter-in-place; eight named vulnerable cohorts and safe return. [Actual stages](../../apps/api/app/api/routes/evacuation.py#L82) versus F12/model conflict; not fully covered. | AUD-034-011 |
| U06 - Recovery doctrine | PARTIAL | Understand context, recognize complexity, community-led, coordinate, communicate, build capacity; four environments, onset planning/parallel response, managed handover. [Recovery service](../../apps/api/app/services/recovery_service.py#L25) is more than stub, but F13/F16 leave workflow/community/learning proof open. | AUD-034-012, AUD-034-016 |
| U07 - National/shared responsibility | PARTIAL | Individuals/households, communities, businesses, local/state/territory/Commonwealth, NCM/NJCOP/ANZEMC and DRFA/DACC/COMDISPLAN. [Bridge template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) proves none of the distinct handoffs. | AUD-034-002, AUD-034-009 |
| U08 - Privacy/interoperability/degradation | PARTIAL | NN-1 through NN-5: explicit authorization, bounded AU/model carve-out, privacy, CAP/EDXL/GeoJSON/OpenAPI and graceful single-component failure. [CAP/EDXL routes](../../apps/api/app/api/routes/warning_chain.py#L105) exist; test substitutes and disconnected audit/offline/redaction remain. | AUD-034-006, AUD-034-008, AUD-034-013, AUD-034-015, AUD-034-020 |
| U09 - Formal quality/governance | UNVERIFIED | PR lint/unit/integration, infra what-if/plan review, human-reviewed public outputs, lessons management, reviewed spec changes and explicit lead-only constitution amendments. [Quality gates](../../.specify/memory/constitution.md#L300) are obligations, not proof; no actual sign-off in local review log. | AUD-034-018, AUD-034-021, AUD-034-022 |
| U10 - Suite execution discipline | PARTIAL | Fixed suite topology/naming, >=3 personas from >=3 jurisdictions per cross-cutting spec, legacy preservation, four workers/shards, retry/`.only`/wait policy, required tag axes, no fixture permissions literals, error classification and fail-closed gaps. [Config](../../apps/web/playwright.config.cts#L48)/[lint](../../apps/web/eslint.config.mjs#L23) miss collection/policy; most tests have one persona or Operational plus ACT, not three jurisdictions. | AUD-034-002, AUD-034-003, AUD-034-021 |
| U11 - Artifact/provenance discipline | PARTIAL | Exact tuple/cardinality/columns/IDs, cycle UUID/seed hash/revision, timestamp symmetry, blob-linked audits, closed-gap-to-pass linkage, vote-cycle consistency, known-good hash, >=3 identical run signals, redacted failure assets and seven-year archive. [Models/invariants](data-model.md#L577) not fully enforced; F04/F08/F17-F20. | AUD-034-004, AUD-034-006, AUD-034-017 through AUD-034-020 |
| U12 - Hypothesis and boundary discipline | UNVERIFIED | Measure flake/proxy validity, >30% uplift/cohort disposition, Asia grading acceptance; preserve 10 OOS limits and 68 persona scope. [Hypotheses](spec.md#L1029) and [review](review-log.md#L8) have no measurement/disposition chain. | AUD-034-022 |

### Original Task Coverage

The next table uses one row per exact original ID. IMPLEMENTED denotes supported authored behavior only,
never an executed test, applied branch policy, deployed resource or approved review.

| Original task | Original state | Status | Concrete inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | [Suite layout](../../tests/e2e/web-coverage/README.md#L9) and directory inventory confirm operational/sectors/cross-cutting/capstone/support/artifacts and script folders. | none |
| T002 | [x] | PARTIAL | [Dependencies](../../apps/web/package.json#L36) include axe, YAML, Ajv/formats and Playwright 1.59.1; installation/lockfile execution at the required revision is not demonstrated. | AUD-034-021, AUD-034-022 |
| T003 | [x] | IMPLEMENTED | [TS alias](../../apps/web/tsconfig.json#L32) targets suite root to match `_support` imports; relocated [CTS config](../../apps/web/playwright.config.cts#L9) explicitly selects this tsconfig. | none |
| T004 | [x] | PARTIAL | [Ignore rules](../../.gitignore#L50) protect artifact folder and preserve canonical files, but do not include the requested anywhere-under-suite `*.partial-*.json` pattern. | AUD-034-021 |
| T005 | [x] | PARTIAL | [Projects/reporters](../../apps/web/playwright.config.cts#L42) added without deleting legacy projects; `.only`/workers/media policy missing and artifact glob differs from CI. | AUD-034-004, AUD-034-021 |
| T006 | [x] | PARTIAL | [Custom rule](../../tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs#L27) detects method calls, but [flat config](../../apps/web/eslint.config.mjs#L23) is outside normal app lint traversal; no tag-axis enforcement. | AUD-034-021 |
| T007 | [x] | IMPLEMENTED | [Guard](../../apps/api/app/middleware/test_support_guard.py#L27) requires exact flag plus dev/test and logs activation/refusal. | none |
| T008 | [x] | PARTIAL | [Lookup router](../../apps/api/app/api/routes/test_support.py#L83) reads bootstrap identities/scenarios with intended shapes; audit uses best-effort fallback, not guaranteed shared durable writer. | AUD-034-006 |
| T009 | [x] | IMPLEMENTED | [Aggregator](../../apps/api/app/api/router.py#L136) mounts test-support only under guard; [main](../../apps/api/app/main.py#L73) includes aggregator. Later evaluator production routes assessed separately. | none |
| T010 | [x] | IMPLEMENTED | Relocated [contract tests](../../tests/contract/test_test_support_router.py#L50) assert unset/prod guard, 68-row shape, unknown identity and nonmutation. Authored tests only; not run. | none |
| T011 | [x] | PARTIAL | [Container/policy](../../infra/bicep/main.bicep#L231) exists with 30 days, not seven years/versioning; active entry selects another template. | AUD-034-020 |
| T012 | [x] | PARTIAL | [Role assignment](../../infra/bicep/main.bicep#L475) correctly scopes Blob Contributor to container/API identity; active deployment/zero-trust verification and ID output not established. | AUD-034-020, AUD-034-022 |
| T013 | [x] | UNVERIFIED | [What-if record](bicep-whatif.txt#L16) explicitly skipped; build-success prose lacks exact run/version attribution. | AUD-034-020, AUD-034-022 |
| T014 | [x] | PARTIAL | [Workspace PO](../../tests/e2e/web-coverage/_support/pages/workspaces.po.ts#L20) opens index and has no persona argument or auditApprove. | AUD-034-002, AUD-034-021 |
| T015 | [x] | PARTIAL | [Incident PO](../../tests/e2e/web-coverage/_support/pages/incidents.po.ts#L26) only navigates/list-checks; no detail warning composer or approval modal. | AUD-034-008, AUD-034-021 |
| T016 | [x] | PARTIAL | [Disasters PO](../../tests/e2e/web-coverage/_support/pages/disasters.po.ts#L26) swallows both readiness waits and assumes declaration UI; actual route redirects to root mapper. | AUD-034-009, AUD-034-021 |
| T017 | [x] | PARTIAL | [Governance PO](../../tests/e2e/web-coverage/_support/pages/governance.dashboard.po.ts#L19) targets only index, not five dashboard details. | AUD-034-021 |
| T018 | [x] | PARTIAL | [Data-source PO](../../tests/e2e/web-coverage/_support/pages/governance.dataSource.po.ts#L19) targets relocated listing, not source detail/assignments/compliance actions. | AUD-034-021 |
| T019 | [x] | PARTIAL | [Workflow PO](../../tests/e2e/web-coverage/_support/pages/operations.workflows.po.ts#L23) swallows failure; active workflow dashboard uses actual run/list/detail clients, not expected generic selectors. | AUD-034-009, AUD-034-021 |
| T020 | [x] | PARTIAL | [Preparedness PO](../../tests/e2e/web-coverage/_support/pages/preparedness.po.ts#L19) offers navigation only; no lesson/control action. | AUD-034-016, AUD-034-021 |
| T021 | [x] | PARTIAL | [Simulation PO](../../tests/e2e/web-coverage/_support/pages/simulations.po.ts#L23) opens index, not create/playback/report/export lifecycle. | AUD-034-016, AUD-034-021 |
| T022 | [x] | PARTIAL | [Eval PO](../../tests/e2e/web-coverage/_support/pages/eval.po.ts#L19) index only, no run detail/actions/audit. | AUD-034-021 |
| T023 | [x] | PARTIAL | [Resolver](../../tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts#L27) uses module cache/test-scoped fixture, not specified worker scope; doesn't set context principal or verify returned role/permissions. | AUD-034-005 |
| T024 | [x] | PARTIAL | [Scenario fixture](../../tests/e2e/web-coverage/_support/fixtures/hazardScenario.fixture.ts#L15) performs read-only API lookup; no matching fixture baseline/incident-chain contract exposed. | AUD-034-001, AUD-034-002 |
| T025 | [x] | PARTIAL | [Correlation fixture](../../tests/e2e/web-coverage/_support/fixtures/correlationId.fixture.ts#L15) generates UUID but attaches neither header nor reporter evidence. | AUD-034-004, AUD-034-005 |
| T026 | [x] | PARTIAL | [Audit observer](../../tests/e2e/web-coverage/_support/fixtures/auditObserver.fixture.ts#L38) loops after action, returns null, and lacks bounded requests/full fields/reporter attachment. | AUD-034-004, AUD-034-006 |
| T027 | [x] | PARTIAL | [Registry fixture](../../tests/e2e/web-coverage/_support/fixtures/carveoutRegistry.fixture.ts#L29) catches missing/invalid data, uses obsolete shape and checks neither schema/date nor approvers. | AUD-034-015 |
| T028 | [x] | PARTIAL | [Outcome-1 fixture](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json#L1) has labels but no baseline; numeric seed baseline exists [elsewhere](../../packages/domain/src/domain/seed/hazard_scenarios_australia.json#L52), not measured warning reach. | AUD-034-001 |
| T029 | [x] | PARTIAL | [Outcome-2 fixture](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-2-bushfire-severe-storm.fixture.json#L1) omits level budgets/baseline; seed has one scalar, no three-level measurement. | AUD-034-001 |
| T030 | [x] | PARTIAL | [Outcome-3 fixture](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json#L1) labels hazards; no baseline lead/reference timestamp or actual predictive transition. | AUD-034-001, AUD-034-011 |
| T031 | [x] | PARTIAL | [Outcome-4 fixture](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-4-bushfire-cyclone-logistics.fixture.json#L1) lacks numeric routine/mutual-aid/70% baseline contract. | AUD-034-001 |
| T032 | [x] | PARTIAL | [Outcome-5 fixture](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-5-flood-storm-economic.fixture.json#L1) lists environments; seed scalar exists but no Sendai source/managed-handover provenance. | AUD-034-001, AUD-034-012 |
| T033 | [x] | PARTIAL | [Reporter](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L225) parses tags/attachments, not structured coverage/gap annotations; no required dedupe or onStdErr enforcement. | AUD-034-004 |
| T034 | [x] | PARTIAL | [Annotation helper](../../tests/e2e/web-coverage/_support/reporter/annotations.ts#L47) builds/parses tag strings, not recordCoverage evidence. | AUD-034-004 |
| T035 | [x] | PARTIAL | [Trace factory/sort](../../tests/e2e/web-coverage/_support/reporter/trace-row.ts#L18) creates one row per FR with volatile time; no complete deterministic tie ordering/tuple merge. | AUD-034-004 |
| T036 | [x] | PARTIAL | [Redactor](../../tests/e2e/web-coverage/_support/reporter/redact.ts#L10) handles selected keys only, not names/GPS/free text/media/JUnit before upload. | AUD-034-020 |
| T037 | [x] | IMPLEMENTED | [Coverage type](../../tests/e2e/web-coverage/_support/types/coverage.d.ts#L5) declares current schema fields; enforcement gaps belong to reporter/gate tasks. | none |
| T038 | [x] | PARTIAL | [Gap type](../../tests/e2e/web-coverage/_support/types/gap.d.ts#L12) covers base fields but not additive cycle_id/regression flag or evidenced transition linkage. | AUD-034-017, AUD-034-022 |
| T039 | [x] | PARTIAL | [Review types](../../tests/e2e/web-coverage/_support/types/review.d.ts#L10) define votes/objections but omit required KnownGoodManifest type. | AUD-034-019, AUD-034-022 |
| T040 | [x] | PARTIAL | [Proxy validator](../../tests/e2e/web-coverage/_support/validators/outcome-proxy.ts#L36) checks metadata membership, not any numeric outcome proxy. | AUD-034-001 |
| T041 | [x] | PARTIAL | [CAP helper](../../tests/e2e/web-coverage/_support/validators/aws-cap-envelope.ts#L27) checks required keys/levels/language/time; no CAP XML/nested semantics/icon/de-escalation chain. | AUD-034-008 |
| T042 | [x] | PARTIAL | [PSPF helper](../../tests/e2e/web-coverage/_support/validators/pspf-classification.ts#L39) compares classification rank; no synthetic gateway probe generator/enforcement. | AUD-034-015 |
| T043 | [x] | PARTIAL | [Axe helper](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) configures tags but disables contrast/region contrary to full AA obligation. | AUD-034-014 |
| T044 | [x] | PARTIAL | [Language helper](../../tests/e2e/web-coverage/_support/a11y/languagePackProbe.ts#L19) queries advertised languages, never toggles/renders/verifies payload variants. | AUD-034-014 |
| T045 | [x] | PARTIAL | [Gap CLI](../../scripts/web-coverage/gap-register.py#L123) exists but command/state/evidence/audit source differ and validations can no-op. | AUD-034-017 |
| T046 | [x] | PARTIAL | [Append helper](../../scripts/web-coverage/_lib/audit_append.py#L19) is local-only JSONL with no managed-identity Blob path or explicit fallback control. | AUD-034-006, AUD-034-020 |
| T047 | [x] | PARTIAL | [Validator](../../scripts/web-coverage/_lib/schema_validators.py#L45) silently no-ops without dependency, does not check formats/cross-entity or embedded evaluator/manifest contracts. | AUD-034-003, AUD-034-007, AUD-034-022 |
| T048 | [x] | PARTIAL | [Merge](../../scripts/web-coverage/trace-merge.py#L49) keeps separate Test-ID tuples, no joined IDs, wrong Markdown columns, empty-input success, no cycle header. | AUD-034-004 |
| T049 | [x] | PARTIAL | [Manifest update](../../scripts/web-coverage/known-good.py#L92) no trace hash/schema/complete-run prerequisite; silently skips missing trace. | AUD-034-019 |
| T050 | [x] | PARTIAL | [Review parser](../../scripts/web-coverage/review-log.py#L431) offers vote/panel/list/closure, no run/agent-card/sidecar ingestion; scaffold not promised flow. | AUD-034-018 |
| T051 | [x] | PARTIAL | [Verifier source](../../scripts/web-coverage/verify-trace-determinism.ps1#L16) remerges hashes but does not assert native success and cannot prove three suite runs. | AUD-034-019 |
| T052 | [x] | PARTIAL | [Bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L42) and [seed driver](../../scripts/seed_loader.py#L74) include identities/scenarios/AIIMS; 68 identities use `afp-act`, no actual seeded incident chain used by evaluator. | AUD-034-001, AUD-034-005 |
| T053 | [x] | PARTIAL | [Contract spec](../../tests/e2e/web-coverage/_support/fixtures/__tests__/persona.contract.spec.ts#L15) uses wrong prefix/collection key, does not use resolver/nonempty permissions, and is excluded by config. | AUD-034-005, AUD-034-021 |
| T054 | [x] | PARTIAL | [RBAC](../../tests/e2e/web-coverage/cross-cutting/rbac-aiims.spec.ts#L28) asserts button presence/absence only, no backend denial/incident scope; labels misclassify Operational/ARC jurisdictions. | AUD-034-005, AUD-034-008 |
| T055 | [x] | PARTIAL | [COP](../../tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts#L27) times initial empty incident list; no shared data refresh. | AUD-034-009 |
| T056 | [x] | PARTIAL | [Audit append-only](../../tests/e2e/web-coverage/cross-cutting/audit-append-only.spec.ts#L29) rereads evaluator ID without PUT/PATCH/no-mutation/latency/full-field assertions. | AUD-034-006 |
| T057 | [x] | PARTIAL | [AWS](../../tests/e2e/web-coverage/cross-cutting/aws-warning-compliance.spec.ts#L25) repeats lives evaluator across six labels, never warning lifecycle. | AUD-034-008 |
| T058 | [x] | PARTIAL | [Evacuation](../../tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts#L29) repeats lead-hour evaluation, no stage/types/approaches/cohorts. | AUD-034-011 |
| T059 | [x] | PARTIAL | [Recovery](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L32) visits governance index/evaluates loss, no four-environment handover or sources. | AUD-034-012 |
| T060 | [x] | PARTIAL | [A11y/language](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) three indexes/advertised codes only, omitted full P1/contrast/per-hazard rendering. | AUD-034-014 |
| T061 | [x] | PARTIAL | [Offline](../../tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts#L30) never goes offline or replays real field action. | AUD-034-013 |
| T062 | [x] | PARTIAL | [Sovereignty](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L29) no real gateway payload/date/approver assertion. | AUD-034-015 |
| T063 | [x] | PARTIAL | [Span](../../tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts#L25) only calculator passes; no >7 warning/delegation and only one N/A persona. | AUD-034-010 |
| T064 | [x] | PARTIAL | [HITL](../../tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts#L53) malformed metrics are not absent approval; no irreversible action state/denial audit. | AUD-034-008 |
| T065 | [x] | PARTIAL | [Source multiplicity](../../tests/e2e/web-coverage/cross-cutting/data-source-multiplicity.spec.ts#L29) never counts/names three sources; evaluator's baseline JSON not three independent sources. | AUD-034-012 |
| T066 | [x] | PARTIAL | [Timeline](../../tests/e2e/web-coverage/cross-cutting/audit-trail.spec.ts#L29) visible/absent-edit checks; empty rows allowed, correlation values never asserted. | AUD-034-006 |
| T067 | [x] | PARTIAL | [Simulation](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L32) compares calculator cache, not actual create/run/replay timelines. | AUD-034-016 |
| T068 | [x] | PARTIAL | [Lessons](../../tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts#L28) no report export or preparedness mapping. | AUD-034-016 |
| T069 | [x] | PARTIAL | [IC](../../tests/e2e/web-coverage/operational/incident-commander.approve-cross-agency-action.spec.ts#L1) index/evaluator only; no cross-agency approval or second outcome. | AUD-034-002, AUD-034-008 |
| T070 | [x] | PARTIAL | [Operations](../../tests/e2e/web-coverage/operational/operations-officer.tactical-tasking.spec.ts#L1) no issued task or three-level action timing. | AUD-034-001, AUD-034-002 |
| T071 | [x] | PARTIAL | [Planning](../../tests/e2e/web-coverage/operational/planning-officer.predictive-risk-evac.spec.ts#L1) no predictive-risk/evacuation state; fixed metric. | AUD-034-002, AUD-034-011 |
| T072 | [x] | PARTIAL | [Logistics](../../tests/e2e/web-coverage/operational/logistics-officer.mutual-aid-lifecycle.spec.ts#L1) no request/approval/match lifecycle or observed 12-click budget. | AUD-034-001, AUD-034-002 |
| T073 | [x] | PARTIAL | [PIO](../../tests/e2e/web-coverage/operational/public-information-officer.aws-multilingual-warning.spec.ts#L1) no composed translated warning or approval/publication. | AUD-034-002, AUD-034-008, AUD-034-014 |
| T074 | [x] | PARTIAL | [Field](../../tests/e2e/web-coverage/operational/field-coordinator.offline-gps-hazard-report.spec.ts#L1) no offline GPS capture/reconnect. | AUD-034-002, AUD-034-013 |
| T075 | [x] | PARTIAL | [Resilience](../../tests/e2e/web-coverage/operational/resilience-planner.recovery-handover.spec.ts#L1) no response/recovery handover; supplied loss value. | AUD-034-002, AUD-034-012 |
| T076 | [x] | PARTIAL | [Executive](../../tests/e2e/web-coverage/operational/executive-leader.economic-environment-view.spec.ts#L1) no Economic view or read-only acknowledgement/export. | AUD-034-002, AUD-034-012 |
| T077 | [x] | PARTIAL | [Observer](../../tests/e2e/web-coverage/operational/observer-auditor.append-only-timeline.spec.ts#L1) no tamper rejection; logistics evaluator only. | AUD-034-002, AUD-034-006 |
| T078 | [x] | PARTIAL | [Risk manager](../../tests/e2e/web-coverage/operational/risk-manager.predictive-evac-lead.spec.ts#L1) fixed lead metric, no predictive/risk workflow. | AUD-034-001, AUD-034-002 |
| T079 | [x] | PARTIAL | [NSW RFS](../../tests/e2e/web-coverage/sectors/nsw/nsw-rfs.bushfire-incident-action-plan.spec.ts#L1) no incident action plan; generic evaluator body. | AUD-034-002 |
| T080 | [x] | PARTIAL | [SES NSW](../../tests/e2e/web-coverage/sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts#L1) no flood warning/IC approval/evacuation flow. | AUD-034-002, AUD-034-008, AUD-034-011 |
| T081 | [x] | PARTIAL | [NSW Ambulance](../../tests/e2e/web-coverage/sectors/nsw/nsw-ambulance.mass-casualty-triage.spec.ts#L1) no mass-casualty triage state. | AUD-034-002 |
| T082 | [x] | PARTIAL | [NSWPF](../../tests/e2e/web-coverage/sectors/nsw/nswpf.evacuation-cordon.spec.ts#L1) no cordon/closure action or peer geometry. | AUD-034-002, AUD-034-009 |
| T083 | [x] | PARTIAL | [FRNSW](../../tests/e2e/web-coverage/sectors/nsw/frnsw.urban-fire-response.spec.ts#L1) no urban-fire response action; lives arithmetic. | AUD-034-002 |
| T084 | [x] | PARTIAL | [MRNSW](../../tests/e2e/web-coverage/sectors/nsw/mrnsw.maritime-flood-rescue.spec.ts#L1) no maritime rescue/transport state. | AUD-034-002 |
| T085 | [x] | PARTIAL | [CFA VIC](../../tests/e2e/web-coverage/sectors/vic/cfa-vic.code-red-day.spec.ts#L1) no Code Red warning/operational action. | AUD-034-002, AUD-034-008 |
| T086 | [x] | PARTIAL | [SES VIC](../../tests/e2e/web-coverage/sectors/vic/ses-vic.flash-flood-rescue.spec.ts#L1) no flash-flood rescue transition. | AUD-034-002 |
| T087 | [x] | PARTIAL | [AV](../../tests/e2e/web-coverage/sectors/vic/av.heat-related-illness-surge.spec.ts#L1) no clinical surge triage/capacity action. | AUD-034-002 |
| T088 | [x] | PARTIAL | [VicPol](../../tests/e2e/web-coverage/sectors/vic/vicpol.cross-border-evac.spec.ts#L1) no cross-border evacuation/closure comparison. | AUD-034-002, AUD-034-009 |
| T089 | [x] | PARTIAL | [FRV](../../tests/e2e/web-coverage/sectors/vic/frv.warehouse-fire-haz-mat.spec.ts#L1) no hazardous-material response workflow. | AUD-034-002 |
| T090 | [x] | PARTIAL | [QFD](../../tests/e2e/web-coverage/sectors/qld/qfd.cyclone-pre-positioning.spec.ts#L1) no pre-position/match/allocation; fixed clicks. | AUD-034-001, AUD-034-002 |
| T091 | [x] | PARTIAL | [SES QLD](../../tests/e2e/web-coverage/sectors/qld/ses-qld.tropical-cyclone-flood.spec.ts#L1) no cyclone/flood evacuation action. | AUD-034-002, AUD-034-011 |
| T092 | [x] | PARTIAL | [QAS](../../tests/e2e/web-coverage/sectors/qld/qas.heat-stress-mass-casualty.spec.ts#L1) no heat-stress casualty workflow. | AUD-034-002 |
| T093 | [x] | PARTIAL | [QPS](../../tests/e2e/web-coverage/sectors/qld/qps.evac-traffic-management.spec.ts#L1) no evacuation traffic/closure state. | AUD-034-002, AUD-034-009 |
| T094 | [x] | PARTIAL | [SACFS](../../tests/e2e/web-coverage/sectors/sa/sacfs.code-red-bushfire.spec.ts#L1) no actual Code Red bushfire workflow. | AUD-034-002 |
| T095 | [x] | PARTIAL | [SES SA](../../tests/e2e/web-coverage/sectors/sa/ses-sa.river-murray-flood.spec.ts#L1) no river evacuation transition/reference lead. | AUD-034-002, AUD-034-011 |
| T096 | [x] | PARTIAL | [SAAS](../../tests/e2e/web-coverage/sectors/sa/saas.extreme-heat-mass-call.spec.ts#L1) no heat mass-call handling or signal-action timing. | AUD-034-001, AUD-034-002 |
| T097 | [x] | PARTIAL | [SAPOL](../../tests/e2e/web-coverage/sectors/sa/sapol.cross-border-evac.spec.ts#L1) no cross-border evacuation/COP closure. | AUD-034-002, AUD-034-009 |
| T098 | [x] | PARTIAL | [SAMFS](../../tests/e2e/web-coverage/sectors/sa/samfs.urban-fire-multi-storey.spec.ts#L1) no multistorey evacuation/response action. | AUD-034-002 |
| T099 | [x] | PARTIAL | [DFES WA](../../tests/e2e/web-coverage/sectors/wa/dfes-wa.cyclone-pilbara.spec.ts#L1) no Pilbara staging/resource workflow. | AUD-034-002 |
| T100 | [x] | PARTIAL | [SJA WA](../../tests/e2e/web-coverage/sectors/wa/sja-wa.remote-medical-evac.spec.ts#L1) no remote medical evacuation/handoff. | AUD-034-002 |
| T101 | [x] | PARTIAL | [WAPOL](../../tests/e2e/web-coverage/sectors/wa/wapol.remote-evac-cordon.spec.ts#L1) no cordon/state or degraded remote coordination. | AUD-034-002, AUD-034-009 |
| T102 | [x] | PARTIAL | [TFS](../../tests/e2e/web-coverage/sectors/tas/tfs.bushfire-island-evac.spec.ts#L1) no island transport/evacuation transition. | AUD-034-002 |
| T103 | [x] | PARTIAL | [SES TAS](../../tests/e2e/web-coverage/sectors/tas/ses-tas.severe-storm-rescue.spec.ts#L1) no storm rescue despite cyclone/flood metric label. | AUD-034-002 |
| T104 | [x] | PARTIAL | [AT](../../tests/e2e/web-coverage/sectors/tas/at.aeromedical-retrieval.spec.ts#L1) no aeromedical assignment or care handoff. | AUD-034-002 |
| T105 | [x] | PARTIAL | [TasPol](../../tests/e2e/web-coverage/sectors/tas/taspol.island-evac-coordination.spec.ts#L1) no island evacuation coordination. | AUD-034-002 |
| T106 | [x] | PARTIAL | [ACT ESA](../../tests/e2e/web-coverage/sectors/act/act-esa.multi-agency-coordination.spec.ts#L1) no multiagency incident state; fixed lead evaluator. | AUD-034-002, AUD-034-009 |
| T107 | [x] | PARTIAL | [ACT FR](../../tests/e2e/web-coverage/sectors/act/act-fr.urban-fire.spec.ts#L1) no urban-fire action. | AUD-034-002 |
| T108 | [x] | PARTIAL | [ACT ambulance](../../tests/e2e/web-coverage/sectors/act/act-ambulance.heat-surge.spec.ts#L1) no heat surge/care flow. | AUD-034-002 |
| T109 | [x] | PARTIAL | [ACT policing](../../tests/e2e/web-coverage/sectors/act/act-policing.evac-cordon.spec.ts#L1) no cordon updates. | AUD-034-002, AUD-034-009 |
| T110 | [x] | PARTIAL | [ACT RFS](../../tests/e2e/web-coverage/sectors/act/act-rfs.bushfire-pre-positioning.spec.ts#L1) no actual pre-position allocation. | AUD-034-002 |
| T111 | [x] | CONFLICT | [AFP ACT file](../../tests/e2e/web-coverage/sectors/act/afp.protective-services.spec.ts#L1) uses `afp-act`, not task's `afp`, and performs no protective-services action. | AUD-034-002, AUD-034-005, AUD-034-022 |
| T112 | [x] | PARTIAL | [SES ACT](../../tests/e2e/web-coverage/sectors/act/ses-act.severe-storm-rescue.spec.ts#L1) no severe-storm rescue state. | AUD-034-002 |
| T113 | [x] | PARTIAL | [Bushfires NT](../../tests/e2e/web-coverage/sectors/nt/bushfires-nt.savanna-burn.spec.ts#L1) no savanna-burn planning/approval. | AUD-034-002 |
| T114 | [x] | PARTIAL | [NTES](../../tests/e2e/web-coverage/sectors/nt/ntes.cyclone-shelter.spec.ts#L1) no cyclone shelter/capacity/evacuation state. | AUD-034-002, AUD-034-011 |
| T115 | [x] | PARTIAL | [NTFRS](../../tests/e2e/web-coverage/sectors/nt/ntfrs.remote-fire-response.spec.ts#L1) no remote fire dispatch. | AUD-034-002 |
| T116 | [x] | PARTIAL | [NTPF](../../tests/e2e/web-coverage/sectors/nt/ntpf.remote-evac.spec.ts#L1) no remote evacuation workflow. | AUD-034-002, AUD-034-011 |
| T117 | [x] | PARTIAL | [SJA NT](../../tests/e2e/web-coverage/sectors/nt/sja-nt.remote-medical-retrieval.spec.ts#L1) no retrieval/clinical handoff. | AUD-034-002 |
| T118 | [x] | PARTIAL | [NEMA](../../tests/e2e/web-coverage/sectors/commonwealth/nema.activate-comdisplan.spec.ts#L1) no COMDISPLAN/NJCOP/consequence metrics. | AUD-034-002, AUD-034-009 |
| T119 | [x] | PARTIAL | [BoM](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.cyclone-warning-relay.spec.ts#L1) no cyclone AWS relay/translated delivery. | AUD-034-002, AUD-034-008 |
| T120 | [x] | PARTIAL | [GA](../../tests/e2e/web-coverage/sectors/commonwealth/ga-national.tsunami-warning-relay.spec.ts#L1) adds earthquake/tsunami labels to outcome-1 calculator instead of AWS-specific relay. | AUD-034-002, AUD-034-008 |
| T121 | [x] | PARTIAL | [ADF](../../tests/e2e/web-coverage/sectors/commonwealth/adf.dacc-asset-arrival.spec.ts#L1) no A/B/C categorization or asset arrival. | AUD-034-002, AUD-034-009 |
| T122 | [x] | PARTIAL | [ABF](../../tests/e2e/web-coverage/sectors/commonwealth/abf.border-disaster-coordination.spec.ts#L1) no border coordination/action. | AUD-034-002 |
| T123 | [x] | PARTIAL | [ARC](../../tests/e2e/web-coverage/sectors/commonwealth/arc.recovery-financial-assistance.spec.ts#L1) no financial-assistance request/handover. | AUD-034-002, AUD-034-012 |
| T124 | [x] | PARTIAL | [ASA](../../tests/e2e/web-coverage/sectors/commonwealth/asa.shipping-evac.spec.ts#L1) no shipping evacuation workflow. | AUD-034-002 |
| T125 | [x] | PARTIAL | [RFDS](../../tests/e2e/web-coverage/sectors/commonwealth/rfds.remote-aeromedical.spec.ts#L1) no remote aeromedical dispatch/care. | AUD-034-002 |
| T126 | [x] | PARTIAL | [SJA National](../../tests/e2e/web-coverage/sectors/commonwealth/sja-national.community-first-aid.spec.ts#L1) no community first-aid task. | AUD-034-002 |
| T127 | [x] | PARTIAL | [Surf lifesaving](../../tests/e2e/web-coverage/sectors/commonwealth/surf-lifesaving.coastal-cyclone-evac.spec.ts#L1) no coastal cyclone evacuation state. | AUD-034-002, AUD-034-011 |
| T128 | [x] | PARTIAL | [AFP Commonwealth](../../tests/e2e/web-coverage/sectors/commonwealth/afp-commonwealth.national-evac-coordination.spec.ts#L1) correct distinct ID but no national evacuation coordination. | AUD-034-002, AUD-034-009 |
| T129 | [x] | PARTIAL | [Community NGOs](../../tests/e2e/web-coverage/sectors/cross-sector/community-ngos.recovery-coordination.spec.ts#L1) no community-led recovery action. | AUD-034-002, AUD-034-012 |
| T130 | [x] | PARTIAL | [Health](../../tests/e2e/web-coverage/sectors/cross-sector/health.surge-capacity.spec.ts#L1) no surge-capacity workflow. | AUD-034-002 |
| T131 | [x] | PARTIAL | [Local government](../../tests/e2e/web-coverage/sectors/cross-sector/local-government.recovery-funding.spec.ts#L1) no recovery funding/DRFA transaction. | AUD-034-002, AUD-034-012 |
| T132 | [x] | PARTIAL | [State government](../../tests/e2e/web-coverage/sectors/cross-sector/state-government.disaster-declaration.spec.ts#L1) no declaration persistence. | AUD-034-002 |
| T133 | [x] | PARTIAL | [Territory government](../../tests/e2e/web-coverage/sectors/cross-sector/territory-government.cross-jurisdiction-coord.spec.ts#L1) no cross-jurisdiction coordination. | AUD-034-002, AUD-034-009 |
| T134 | [x] | PARTIAL | [Transport](../../tests/e2e/web-coverage/sectors/cross-sector/transport.evac-routing.spec.ts#L1) no route/closure/allocation action. | AUD-034-002, AUD-034-009 |
| T135 | [x] | PARTIAL | [Utility](../../tests/e2e/web-coverage/sectors/cross-sector/utility.power-restoration.spec.ts#L1) no power-restoration or Built recovery update. | AUD-034-002, AUD-034-012 |
| T136 | [x] | PARTIAL | [Volunteer](../../tests/e2e/web-coverage/sectors/cross-sector/volunteer.surge-deployment.spec.ts#L1) no volunteer deployment/credential check. | AUD-034-002 |
| T137 | [x] | PARTIAL | [NSW/VIC bridge](../../tests/e2e/web-coverage/sectors/nsw/cross-jurisdiction-nsw-vic-bushfire.spec.ts#L1) two evaluators, no shared incident/AWS/history. | AUD-034-002, AUD-034-009 |
| T138 | [x] | PARTIAL | [VIC/TAS bridge](../../tests/e2e/web-coverage/sectors/vic/cross-jurisdiction-vic-tas-storm.spec.ts#L1) no storm handoff/peer COP. | AUD-034-002, AUD-034-009 |
| T139 | [x] | PARTIAL | [QLD/NSW bridge](../../tests/e2e/web-coverage/sectors/qld/cross-jurisdiction-qld-nsw-cyclone-flood.spec.ts#L1) no border-flood coordination/closure polygon. | AUD-034-002, AUD-034-009 |
| T140 | [x] | PARTIAL | [SA/VIC bridge](../../tests/e2e/web-coverage/sectors/sa/cross-jurisdiction-sa-vic-bushfire.spec.ts#L1) no bushfire peer incident mutation. | AUD-034-002, AUD-034-009 |
| T141 | [x] | PARTIAL | [WA/SA bridge](../../tests/e2e/web-coverage/sectors/wa/cross-jurisdiction-wa-sa-flood.spec.ts#L1) no actual flood handoff. | AUD-034-002, AUD-034-009 |
| T142 | [x] | PARTIAL | [TAS/mainland bridge](../../tests/e2e/web-coverage/sectors/tas/cross-jurisdiction-tas-mainland-cyclone.spec.ts#L1) no mainland-link evacuation/transport state. | AUD-034-002, AUD-034-009 |
| T143 | [x] | PARTIAL | [ACT/NSW bridge](../../tests/e2e/web-coverage/sectors/act/cross-jurisdiction-act-nsw-bushfire.spec.ts#L1) no shared bushfire/COP state. | AUD-034-002, AUD-034-009 |
| T144 | [x] | PARTIAL | [NT/WA bridge](../../tests/e2e/web-coverage/sectors/nt/cross-jurisdiction-nt-wa-bushfire-cyclone.spec.ts#L1) no compound-hazard coordination. | AUD-034-002, AUD-034-009 |
| T145 | [x] | PARTIAL | [NEMA/ADF bridge](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-state-controller-bridge.spec.ts#L1) no request/DACC/arrival/mission close. | AUD-034-002, AUD-034-009 |
| T146 | [x] | PARTIAL | [Outcome 1](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L26) lives subtraction replaces approval/reach/language/timing. | AUD-034-001, AUD-034-008 |
| T147 | [x] | PARTIAL | [Outcome 2](../../tests/e2e/web-coverage/capstone/outcome-2-bushfire-severe-storm.spec.ts#L21) fixed 4500ms, no three-level absolute/relative measured action timing. | AUD-034-001 |
| T148 | [x] | PARTIAL | [Outcome 3](../../tests/e2e/web-coverage/capstone/outcome-3-tropical-cyclone-flood.spec.ts#L21) fixed 26 hours without reference-based workflow. | AUD-034-001, AUD-034-011 |
| T149 | [x] | PARTIAL | [Outcome 4](../../tests/e2e/web-coverage/capstone/outcome-4-bushfire-cyclone-logistics.spec.ts#L21) fixed six clicks; no observed lifecycle or 70% reduction. | AUD-034-001 |
| T150 | [x] | PARTIAL | [Outcome 5](../../tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts#L45) wrong inequality and no managed handover/UI values. | AUD-034-001, AUD-034-012 |
| T151 | [x] | PARTIAL | [Four shard jobs](../../.github/workflows/ci.yml#L258) install/seed/run commands authored; transfer omits nested JUnit/run JSON/cycle metadata/media policy. | AUD-034-004, AUD-034-020, AUD-034-021 |
| T152 | [x] | PARTIAL | [Merge job](../../.github/workflows/ci.yml#L329) consumes partials but no cycle header/full manifests; failures skip downstream merge and no structured gap capture. | AUD-034-004 |
| T153 | [x] | PARTIAL | [Gate job](../../.github/workflows/ci.yml#L374) invokes incomplete heuristics; notice is not requested named status API and does not prove full matrix. | AUD-034-003 |
| T154 | [x] | UNVERIFIED | [Protection file](../../.github/branch-protection.json#L2) explicitly descriptive; actual required checks not inspected remotely or proven locally. | AUD-034-003, AUD-034-022 |
| T155 | [x] | PARTIAL | [CD step](../../.github/workflows/cd.yml#L331) follows revisions but skips dev, downloads no trace and swallows push failure; no actual baseline run proof. | AUD-034-019 |
| T156 | [x] | IMPLEMENTED | [Scripts](../../apps/web/package.json#L16) declare full/P1/axe/mobile/shard entry points; behavior/selection defects covered elsewhere. | none |
| T157 | [x] | PARTIAL | [Vote command](../../scripts/web-coverage/review-log.py#L93) appends JSON/Markdown but trusts supplied disposition/agent/panel and records incomplete audit. | AUD-034-018 |
| T158 | [x] | PARTIAL | [Resolver](../../scripts/web-coverage/review-log.py#L114) wrong panel cardinality/merit/veto/override, does not save resolved vote rows and emits TODO diffs. | AUD-034-018 |
| T159 | [x] | PARTIAL | [Escalation](../../scripts/web-coverage/gap-register.py#L227) threshold differs and no increment/freeze/project-lead disposition enforcement. | AUD-034-017 |
| T160 | [x] | PARTIAL | [Rollback command](../../scripts/web-coverage/known-good.py#L148) stamps evidence only; no restoration integration or verified target. | AUD-034-019 |
| T161 | [x] | PARTIAL | [Regress](../../scripts/web-coverage/gap-register.py#L177) records flags but accepts arbitrary prior state, escalates at cap rather than unconditional reset, omits full rollback event. | AUD-034-017, AUD-034-019 |
| T162 | [x] | PARTIAL | [Workflow](../../.github/workflows/web-coverage-iteration.yml#L32) triggers exist, but downloads wrong-run artifact, no actual agents/votes/closure/regression, cycle hard-coded and failures swallowed. | AUD-034-018 |
| T163 | [x] | CONFLICT | [Template](../../scripts/web-coverage/agent-objection-template.json#L1) has forbidden metadata/vote/evidence_uris fields and omits required evidence/proposed_remediation; [guide](../../.github/agents/_subagents/web-coverage-objection-format.md#L9) repeats different schema. | AUD-034-018, AUD-034-022 |
| T164 | [x] | PARTIAL | [Quickstart](quickstart.md#L292) updated limitations but wrong single-persona path/CLI flags/run command and unsupported closure claims remain. | AUD-034-021, AUD-034-022 |
| T165 | [x] | IMPLEMENTED | [Root README](../../README.md#L306) links quickstart and supplies a P1 snippet with canonical test-support flag. Runtime success not implied. | none |
| T166 | [x] | PARTIAL | [Suite README](../../tests/e2e/web-coverage/README.md#L32) contains taxonomy/index but recommends default stub generator, stale file map and unsupported three-run statement. | AUD-034-021, AUD-034-022 |
| T167 | [x] | CONFLICT | [Manifest skeleton](known-good.json#L1) uses schema_version/entries, not required version/commit/hash/revisions/run fields; no current SHA baseline. | AUD-034-019, AUD-034-022 |
| T168 | [x] | PARTIAL | [Review skeleton](review-log.md#L8) exists but uses wrong 30/35/20 panels; no votes/run/sign-off. | AUD-034-018, AUD-034-022 |
| T169 | [x] | IMPLEMENTED | [Trace placeholder](coverage-trace.md#L7) has exact original eight columns and no invented passing rows; later populated trace still missing. | none |
| T170 | [x] | PARTIAL | [Candidate row](gap-register.json#L16) exists but is Closed without required test/merit/approval proof; cannot validate requested evidence-anchored initialization/closure history. | AUD-034-017, AUD-034-022 |
| T171 | [x] | UNVERIFIED | [First-run log](_evidence/first-run.log#L19) explicitly defers both required runs; ignored artifacts show unrelated all-skipped history. | AUD-034-019, AUD-034-022 |
| T172 | [x] | PARTIAL | [CHK cross-reference](checklists/validation.md#L300) exists but maps ACT ESA to T080 and span to T065, repeats T146, and confuses merge equality with three runs. | AUD-034-022 |
| T173 | [x] | PARTIAL | [Accepted evaluator contract](contracts/outcome-evaluator.contract.md#L3) authored; formal acceptance is prose, captured-payload gate integration and strict error/schema evidence incomplete. | AUD-034-007, AUD-034-022 |
| T174 | [x] | PARTIAL | [Cycle schema](contracts/cycle-metadata.schema.json#L1) and [depth schema](../../tests/e2e/web-coverage/_lib/depth-profiles/_schema.json#L1) authored; enum/key/combined-target/min-step conflicts, no full formal review proof. | AUD-034-002, AUD-034-022 |
| T175 | [x] | PARTIAL | 68 profiles exist; [IC example](../../tests/e2e/web-coverage/_lib/depth-profiles/incident-commander.depth.yaml#L1) has two steps, not >=3; AFP mismatch, source syntheses absent, all workflow declarations ignored by generator. | AUD-034-002, AUD-034-005, AUD-034-022 |
| T176 | [x] | PARTIAL | [Generator](../../scripts/web-coverage/_lib/persona_spec_generator.py#L776) loads/schema-validates profiles but only emits canned evaluator body, rejects UI-only, prints missing-gap text instead of opening register entry. | AUD-034-002 |
| T177 | [x] | PARTIAL | [Depth gate](../../scripts/web-coverage/_lib/schema_validators.py#L213) checks 68 profile shapes against drifted seed inventory, no exact spec roster/workflow semantics or posted binary status check. | AUD-034-002, AUD-034-003 |
| T178 | [x] | PARTIAL | [Route](../../apps/api/app/api/routes/outcome_evaluator.py#L81) serves five outcomes/errors, but incomplete strict payload validation and explicitly extended production activation differ from task. | AUD-034-007, AUD-034-022 |
| T179 | [x] | PARTIAL | [Audit route](../../apps/api/app/api/routes/audit_list.py#L35) filters/pages process memory, no never-deleted durable cross-cycle/denial timeline. | AUD-034-006 |
| T180 | [x] | PARTIAL | [Service](../../apps/api/app/services/outcome_evaluator_service.py#L178) implements calculations/cache but not existing durable writer/full thresholds/strict metric validation. | AUD-034-001, AUD-034-006, AUD-034-007 |
| T181 | [x] | PARTIAL | Relocated combined [contract tests](../../tests/contract/test_outcome_evaluator.py#L107) cover ranges/idempotency/basic errors; no tamper rows/stable multi-page/backdated exclusion; rejects 501 instead of task's clamp; later fallback test asserts approved shape, not 404. | AUD-034-006, AUD-034-007, AUD-034-022 |
| T182 | [x] | PARTIAL | [onBegin](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L194) emits only shard-1 metadata using regex/fixed timestamp and file concat hash; no Ajv/full-payload hash/canonical merge header. | AUD-034-004, AUD-034-006 |
| T183 | [x] | PARTIAL | [Cycle filter](../../scripts/web-coverage/gap-register.py#L243) falls back to all on missing metadata; updates do not consistently stamp/preserve cycle and regression overwrites origin. | AUD-034-017 |
| T184 | [x] | PARTIAL | [Generated template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L528) removes active bails but not shallowness; 77 original generated files, not an independently verified 81 must-do workflows. | AUD-034-002 |
| T185 | [x] | PARTIAL | All 11 named refactors inspected: [HITL](../../tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts#L14) and peers replace bails with unrelated evaluations, not constitutional invariants. | AUD-034-006, AUD-034-008 through AUD-034-016 |
| T186 | [x] | PARTIAL | All five capstone files call evaluators/read audit, but constants are not fixture-derived measurements and SC-005 comparison is reversed. [Outcome 5](../../tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts#L45). | AUD-034-001 |
| T187 | [x] | PARTIAL | [SAPOL control centre](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L25) no delegation/role separation/persisted authority. | AUD-034-002, AUD-034-005 |
| T188 | [x] | PARTIAL | [SA multi-LGA](../../tests/e2e/web-coverage/sectors/sa/ses-sa.long-distance-multi-lga-evacuation.spec.ts#L1) no convoy, shelter routing or degraded communications. | AUD-034-002, AUD-034-009, AUD-034-011 |
| T189 | [x] | PARTIAL | [DFES cultural handoff](../../tests/e2e/web-coverage/sectors/wa/dfes-wa.atsi-handoff-culturally-safe.spec.ts#L1) no cultural approval/translated warning/remote community handoff. | AUD-034-002, AUD-034-014 |
| T190 | [x] | PARTIAL | [DFES iron ore](../../tests/e2e/web-coverage/sectors/wa/dfes-wa.iron-ore-critical-infrastructure.spec.ts#L1) no port/rail/power allocation under compound hazards. | AUD-034-002 |
| T191 | [x] | PARTIAL | [AT island isolation](../../tests/e2e/web-coverage/sectors/tas/at.island-isolation-aeromedical-disruption.spec.ts#L1) no ferry/air disruption or rescue-to-care handoff. | AUD-034-002 |
| T192 | [x] | PARTIAL | [TasPol multilingual](../../tests/e2e/web-coverage/sectors/tas/taspol.palawa-multilingual-warning.spec.ts#L1) no palawa variant payload/reviewer/approval assertion. | AUD-034-002, AUD-034-014 |
| T193 | [x] | PARTIAL | [AFP precinct](../../tests/e2e/web-coverage/sectors/act/afp.national-capital-security-mechanics.spec.ts#L1) uses `afp-act` and no precinct/Commonwealth tenancy escalation. | AUD-034-002, AUD-034-005 |
| T194 | [x] | PARTIAL | [SES ACT declaration](../../tests/e2e/web-coverage/sectors/act/ses-act.territory-emergency-declaration.spec.ts#L1) no declaration persisted/authenticated state. | AUD-034-002, AUD-034-005 |
| T195 | [x] | PARTIAL | [NTES language](../../tests/e2e/web-coverage/sectors/nt/ntes.atsi-multilingual-at-persona-level.spec.ts#L1) no actual NT language variant assertions; string in assertion message is not translation evidence. | AUD-034-002, AUD-034-014 |
| T196 | [x] | PARTIAL | [SJA NT logistics](../../tests/e2e/web-coverage/sectors/nt/sja-nt.tropical-disease-remote-logistics.spec.ts#L1) no clinical surge/supply chain or 12-click mutual-aid workflow. | AUD-034-001, AUD-034-002 |
| T197 | [x] | PARTIAL | [BoM ABC/SBS](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts#L26) no `Source=ABC/SBS`, rendered languages or gateway/date triple. | AUD-034-002, AUD-034-014, AUD-034-015 |
| T198 | [x] | PARTIAL | [NEMA DACC/JATWC](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-jatwc-cross-jurisdiction.spec.ts#L1) correct folder, no actual DACC/JATWC/state/territory handoff. | AUD-034-002, AUD-034-009 |
| T199 | [x] | PARTIAL | [Utility insurance](../../tests/e2e/web-coverage/sectors/cross-sector/utility.insurance-recovery-handoff.spec.ts#L1) no insurance handoff/Built/Economic update despite outcome-5 evaluator. | AUD-034-002, AUD-034-012 |
| T200 | [x] | IMPLEMENTED | [CI export](../../.github/workflows/ci.yml#L307) uses `AMA_TEST_SUPPORT: "1"`; no alternate flag in fully inspected workflow. | none |
| T201 | [x] | IMPLEMENTED | [Quickstart](quickstart.md#L36) and all activation examples read canonical flag; other onboarding errors are distinct. | none |
| T202 | [x] | PARTIAL | [README](../../README.md#L313) canonical name fixed; repository-wide documentation-sweep execution is not attributable from artifact claims alone. | AUD-034-021, AUD-034-022 |
| T203 | [x] | PARTIAL | [Closure](../../scripts/web-coverage/review-log.py#L282) counts arbitrary Closed rows/owner exclusions, not merit + PR/diff/pass proof; metadata transfer absent and meta-gap schema mismatch. | AUD-034-018 |
| T204 | [x] | PARTIAL | [Quickstart amendment](quickstart.md#L313) documents metadata/closure but wrongly attributes API cycle filtering to reporter and leaves unsupported readiness/determinism commands. | AUD-034-021, AUD-034-022 |
| T205 | [x] | PARTIAL | [Depth guide](../../tests/e2e/web-coverage/README.md#L185) publishes an enum different from schema, omits real workflow translation and still advertises legacy default generator. | AUD-034-002, AUD-034-021, AUD-034-022 |
| T206 | [x] | PARTIAL | [Cycle checklist](checklists/validation.md#L318) adds closing-task prose rather than requested column, some CHK/task references incorrect; boxes correctly remain unchecked. | AUD-034-022 |

## Review And Checklist Evidence

All original workflow checkboxes are `[ ]`. A status here evaluates the obligation, not the checkbox.
Persona checklist items require a passing must-do workflow, trace and closed review objections together;
authored generic evaluator tests therefore leave those completion/sign-off items UNVERIFIED.

| Checklist item | Original state | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | IMPLEMENTED | [Complete spec](spec.md#L1) contains populated mandatory sections and resolved-question text; no unresolved clarification marker. This is document completeness only. | none |
| CHK002 | [ ] | CONFLICT | [Clarifications/tasks embedded in spec](spec.md#L688) prescribe schemas, generator paths and task implementation, beyond declared WHAT-only boundary. | AUD-034-022 |
| CHK003 | [ ] | PARTIAL | [68-persona roster](spec.md#L16) exists; cited session inputs absent and current AFP identity differs. | AUD-034-005, AUD-034-022 |
| CHK004 | [ ] | IMPLEMENTED | [ASM-005/OOS-001](spec.md#L1021) explicitly justify AU-only scope. Grader acceptance is separate HYP-003. | none |
| CHK005 | [ ] | IMPLEMENTED | [Pass 1](spec.md#L53) codifies Q1-Q5 budgets/languages/sovereignty/cycles. | none |
| CHK006 | [ ] | PARTIAL | [Pass 2](spec.md#L123) answers Q6-Q14, but later key/enum/authority conflicts remain despite zero-ambiguity claims. | AUD-034-022 |
| CHK007 | [ ] | PARTIAL | [FR-027](spec.md#L959) exists; [iteration tooling](../../scripts/web-coverage/gap-register.py#L177) not a consistent enforced FR-024/027 pair. | AUD-034-017, AUD-034-019 |
| CHK008 | [ ] | IMPLEMENTED | [ASM-006/011](spec.md#L1022) codify merit/veto and seed-RBAC obligations. Implementation assessed separately. | none |
| CHK009 | [ ] | IMPLEMENTED | [Requirements](checklists/requirements.md#L1) and [workflow checklist](checklists/validation.md#L1) both exist and were fully read. | none |
| CHK010 | [ ] | IMPLEMENTED | [All 215 items](checklists/validation.md#L23) have explicit spec/contract/constitution/workflow references; correctness of some mappings is separate. | none |
| CHK011 | [ ] | UNVERIFIED | [Checklist header](checklists/validation.md#L5) cites a revision but no attributable lifecycle evidence establishes committed-before-plan ordering. | AUD-034-022 |
| CHK012 | [ ] | PARTIAL | [Plan budgets](plan.md#L676) mention targets but downstream calculator replaces stricter operator budgets. | AUD-034-001, AUD-034-022 |
| CHK013 | [ ] | PARTIAL | [Research R-008](research.md#L195) selects a placeholder and defers actual variants; no authoritative translation approval demonstrated. | AUD-034-014, AUD-034-022 |
| CHK014 | [ ] | PARTIAL | [Seed scenario](../../packages/domain/src/domain/seed/hazard_scenarios_australia.json#L52) carries scalar baseline, no cited Sendai input/capture proof. | AUD-034-001, AUD-034-012 |
| CHK015 | [ ] | PARTIAL | [Four-shard design](research.md#L61) is arithmetic estimate, not actual dev/CI budget measurement. | AUD-034-021, AUD-034-022 |
| CHK016 | [ ] | PARTIAL | [Impersonation design](research.md#L87) claims API/web integration; actual auth does not consume the fixture header. | AUD-034-005 |
| CHK017 | [ ] | PARTIAL | [Q12](spec.md#L275) specifies portfolio invalidation; plan/emitter/merge do not implement a matching automatic flip. | AUD-034-004, AUD-034-022 |
| CHK018 | [ ] | IMPLEMENTED | [Task persona section](tasks.md#L157) has 68 original persona work items; runtime quality not implied. | none |
| CHK019 | [ ] | IMPLEMENTED | [Cross-cutting tasks](tasks.md#L135) enumerate the required baseline files, with 15 actual files. | none |
| CHK020 | [ ] | IMPLEMENTED | [Capstone tasks](tasks.md#L294) enumerate five outcomes and named pairs. | none |
| CHK021 | [ ] | IMPLEMENTED | [Bridge tasks](tasks.md#L278) enumerate eight states/territories plus Commonwealth bridge. | none |
| CHK022 | [ ] | PARTIAL | [Original analysis](analysis.md#L24) reports 68 mappings, but inaccurate requirement/task mapping and AFP drift undermine the claimed closure. | AUD-034-022 |
| CHK023 | [ ] | PARTIAL | [Analysis matrix](analysis.md#L136) names planned tasks, not a complete tuple-to-real-Test-ID table. | AUD-034-004, AUD-034-022 |
| CHK024 | [ ] | PARTIAL | [Constitution matrix](analysis.md#L51) names cross-cutting tests; those tests substitute evaluations for safety behavior. | AUD-034-008, AUD-034-015, AUD-034-018 |
| CHK025 | [ ] | CONFLICT | [CLEAN analysis](analysis-cycle1.md#L16) coexists with incompatible depth enums/keys, review/manifest schemas and gate semantics. | AUD-034-022 |
| CHK026 | [ ] | PARTIAL | [OOS analysis](analysis.md#L83) authored, not independent approval of later production registration/retention changes. | AUD-034-020, AUD-034-022 |
| CHK027 | [ ] | UNVERIFIED | [First-run record](_evidence/first-run.log#L19) defers runs; no three clean seeded executions. | AUD-034-019, AUD-034-022 |
| CHK028 | [ ] | PARTIAL | [Merge](../../scripts/web-coverage/trace-merge.py#L49) wrong tuple/ID rendering; committed trace empty. | AUD-034-004 |
| CHK029 | [ ] | MISSING | Canonical JSON absent from complete local inventory; [Markdown](coverage-trace.md#L7) only header; ignored partial has zero rows, not companion proof. | AUD-034-004, AUD-034-022 |
| CHK030 | [ ] | PARTIAL | [Register](gap-register.md#L5) columns/statuses differ; transitions not mirrored with required complete durable audit. | AUD-034-017 |
| CHK031 | [ ] | PARTIAL | [Configured reports](../../apps/web/playwright.config.cts#L42) exist; saved run is skipped and no failure media settings/transfer. | AUD-034-004, AUD-034-020, AUD-034-021 |
| CHK032 | [ ] | PARTIAL | [Dynamic route](../../apps/web/src/app/workspaces/[personaId]/page.tsx#L17) exists; suite only visits index and no structured missing-workspace gap. | AUD-034-002 |
| CHK033 | [ ] | UNVERIFIED | [Operational sign-off](review-log.md#L12) pending, no actual ten-agent votes/merit closure. | AUD-034-018, AUD-034-022 |
| CHK034 | [ ] | UNVERIFIED | [Sector sign-off](review-log.md#L13) pending, no 58-agent review evidence. | AUD-034-018, AUD-034-022 |
| CHK035 | [ ] | UNVERIFIED | [Technical sign-off](review-log.md#L14) pending, no 17-agent evidence. | AUD-034-018, AUD-034-022 |
| CHK036 | [ ] | UNVERIFIED | [Resolver](../../scripts/web-coverage/review-log.py#L114) allows forbidden override; no performed domain-veto closure record. | AUD-034-018 |
| CHK037 | [ ] | UNVERIFIED | [Empty review table](review-log.md#L16) has no lead dispute dispositions. | AUD-034-022 |
| CHK038 | [ ] | UNVERIFIED | No actual non-meritorious votes; [resolver](../../scripts/web-coverage/review-log.py#L114) computes a different merit rule. | AUD-034-018 |
| CHK039 | [ ] | UNVERIFIED | [Empty trace](coverage-trace.md#L7) cannot establish 68/68 passing. | AUD-034-002, AUD-034-022 |
| CHK040 | [ ] | UNVERIFIED | [Saved JUnit](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L1) has 76 skips, not full cross-cutting pass. | AUD-034-022 |
| CHK041 | [ ] | UNVERIFIED | [Bridge template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L648) and empty trace prove no passing integration matrix. | AUD-034-002, AUD-034-009 |
| CHK042 | [ ] | UNVERIFIED | [Outcome suite](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L26) no attributable paired-hazard workflow evidence. | AUD-034-001, AUD-034-004 |
| CHK043 | [ ] | UNVERIFIED | [One Closed candidate](gap-register.json#L16) does not establish every failure/veto/escalation resolved. | AUD-034-003, AUD-034-017, AUD-034-018 |
| CHK044 | [ ] | UNVERIFIED | [CI notice](../../.github/workflows/ci.yml#L414) is authored output text; no audited performed gate-flip event. | AUD-034-003, AUD-034-022 |
| CHK045 | [ ] | UNVERIFIED | [IC scenario](../../tests/e2e/web-coverage/operational/incident-commander.approve-cross-agency-action.spec.ts#L1) lacks approval, #2 and real span; no pass/review closure. | AUD-034-002, AUD-034-010 |
| CHK046 | [ ] | UNVERIFIED | [Operations](../../tests/e2e/web-coverage/operational/operations-officer.tactical-tasking.spec.ts#L1) no tasking/supervisory span evidence. | AUD-034-002, AUD-034-010 |
| CHK047 | [ ] | UNVERIFIED | [Planning](../../tests/e2e/web-coverage/operational/planning-officer.predictive-risk-evac.spec.ts#L1) no predictive action/N/A warning assertion. | AUD-034-002, AUD-034-010 |
| CHK048 | [ ] | UNVERIFIED | [Logistics](../../tests/e2e/web-coverage/operational/logistics-officer.mutual-aid-lifecycle.spec.ts#L1) no outcome-4 lifecycle/Tier-2 span. | AUD-034-002, AUD-034-010 |
| CHK049 | [ ] | UNVERIFIED | [PIO](../../tests/e2e/web-coverage/operational/public-information-officer.aws-multilingual-warning.spec.ts#L1) no warning/zh-Hans/ATSI payload proof. | AUD-034-008, AUD-034-014 |
| CHK050 | [ ] | UNVERIFIED | [Field](../../tests/e2e/web-coverage/operational/field-coordinator.offline-gps-hazard-report.spec.ts#L1) no offline action. | AUD-034-013 |
| CHK051 | [ ] | UNVERIFIED | [Resilience](../../tests/e2e/web-coverage/operational/resilience-planner.recovery-handover.spec.ts#L1) no Preparedness phase trace or actual handover. | AUD-034-012, AUD-034-016 |
| CHK052 | [ ] | UNVERIFIED | [Executive](../../tests/e2e/web-coverage/operational/executive-leader.economic-environment-view.spec.ts#L1) no cross-jurisdiction COP. | AUD-034-002, AUD-034-009 |
| CHK053 | [ ] | UNVERIFIED | [Observer](../../tests/e2e/web-coverage/operational/observer-auditor.append-only-timeline.spec.ts#L1) no tamper/exported lessons evidence. | AUD-034-006, AUD-034-016 |
| CHK054 | [ ] | UNVERIFIED | [Risk manager](../../tests/e2e/web-coverage/operational/risk-manager.predictive-evac-lead.spec.ts#L1) no recovery-environment risk register. | AUD-034-002, AUD-034-012 |
| CHK055 | [ ] | UNVERIFIED | [NSW bridge](../../tests/e2e/web-coverage/sectors/nsw/cross-jurisdiction-nsw-vic-bushfire.spec.ts#L1) calculator/audit only. | AUD-034-009 |
| CHK056 | [ ] | UNVERIFIED | [FRNSW](../../tests/e2e/web-coverage/sectors/nsw/frnsw.urban-fire-response.spec.ts#L1) no must-do/pass/review evidence. | AUD-034-002 |
| CHK057 | [ ] | UNVERIFIED | [MRNSW](../../tests/e2e/web-coverage/sectors/nsw/mrnsw.maritime-flood-rescue.spec.ts#L1) no must-do/pass/review evidence. | AUD-034-002 |
| CHK058 | [ ] | UNVERIFIED | [NSW ambulance](../../tests/e2e/web-coverage/sectors/nsw/nsw-ambulance.mass-casualty-triage.spec.ts#L1) no must-do/pass/review evidence. | AUD-034-002 |
| CHK059 | [ ] | UNVERIFIED | [NSW RFS](../../tests/e2e/web-coverage/sectors/nsw/nsw-rfs.bushfire-incident-action-plan.spec.ts#L1) no IAP/pass/review evidence. | AUD-034-002 |
| CHK060 | [ ] | UNVERIFIED | [NSWPF](../../tests/e2e/web-coverage/sectors/nsw/nswpf.evacuation-cordon.spec.ts#L1) no cordon/pass/review evidence. | AUD-034-002 |
| CHK061 | [ ] | UNVERIFIED | [SES NSW](../../tests/e2e/web-coverage/sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts#L1) no composed Watch and Act warning. | AUD-034-008, AUD-034-011 |
| CHK062 | [ ] | UNVERIFIED | [VIC bridge](../../tests/e2e/web-coverage/sectors/vic/cross-jurisdiction-vic-tas-storm.spec.ts#L1) no shared incident/pass trace. | AUD-034-009 |
| CHK063 | [ ] | UNVERIFIED | [AV](../../tests/e2e/web-coverage/sectors/vic/av.heat-related-illness-surge.spec.ts#L1) no clinical must-do or passing proof. | AUD-034-002 |
| CHK064 | [ ] | UNVERIFIED | [CFA](../../tests/e2e/web-coverage/sectors/vic/cfa-vic.code-red-day.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK065 | [ ] | UNVERIFIED | [FRV](../../tests/e2e/web-coverage/sectors/vic/frv.warehouse-fire-haz-mat.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK066 | [ ] | UNVERIFIED | [SES VIC](../../tests/e2e/web-coverage/sectors/vic/ses-vic.flash-flood-rescue.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK067 | [ ] | UNVERIFIED | [VicPol](../../tests/e2e/web-coverage/sectors/vic/vicpol.cross-border-evac.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK068 | [ ] | UNVERIFIED | [QLD bridge](../../tests/e2e/web-coverage/sectors/qld/cross-jurisdiction-qld-nsw-cyclone-flood.spec.ts#L1) no actual border-flood workflow. | AUD-034-009 |
| CHK069 | [ ] | UNVERIFIED | [QAS](../../tests/e2e/web-coverage/sectors/qld/qas.heat-stress-mass-casualty.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK070 | [ ] | UNVERIFIED | [QFD](../../tests/e2e/web-coverage/sectors/qld/qfd.cyclone-pre-positioning.spec.ts#L1) no resource pre-position action. | AUD-034-002 |
| CHK071 | [ ] | UNVERIFIED | [QPS](../../tests/e2e/web-coverage/sectors/qld/qps.evac-traffic-management.spec.ts#L1) no traffic action. | AUD-034-002 |
| CHK072 | [ ] | UNVERIFIED | [SES QLD](../../tests/e2e/web-coverage/sectors/qld/ses-qld.tropical-cyclone-flood.spec.ts#L1) no evacuation flow. | AUD-034-002 |
| CHK073 | [ ] | UNVERIFIED | [SA bridge](../../tests/e2e/web-coverage/sectors/sa/cross-jurisdiction-sa-vic-bushfire.spec.ts#L1) no integrated peer state. | AUD-034-009 |
| CHK074 | [ ] | UNVERIFIED | [SAAS](../../tests/e2e/web-coverage/sectors/sa/saas.extreme-heat-mass-call.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK075 | [ ] | UNVERIFIED | [SACFS](../../tests/e2e/web-coverage/sectors/sa/sacfs.code-red-bushfire.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK076 | [ ] | UNVERIFIED | [SES SA](../../tests/e2e/web-coverage/sectors/sa/ses-sa.river-murray-flood.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK077 | [ ] | UNVERIFIED | [SAMFS](../../tests/e2e/web-coverage/sectors/sa/samfs.urban-fire-multi-storey.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK078 | [ ] | UNVERIFIED | [SAPOL](../../tests/e2e/web-coverage/sectors/sa/sapol.cross-border-evac.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK079 | [ ] | UNVERIFIED | [WA bridge](../../tests/e2e/web-coverage/sectors/wa/cross-jurisdiction-wa-sa-flood.spec.ts#L1) no actual WA/SA integration. | AUD-034-009 |
| CHK080 | [ ] | UNVERIFIED | [DFES](../../tests/e2e/web-coverage/sectors/wa/dfes-wa.cyclone-pilbara.spec.ts#L1) no Pilbara operational action. | AUD-034-002 |
| CHK081 | [ ] | UNVERIFIED | [SJA WA](../../tests/e2e/web-coverage/sectors/wa/sja-wa.remote-medical-evac.spec.ts#L1) no medical handoff. | AUD-034-002 |
| CHK082 | [ ] | UNVERIFIED | [WAPOL](../../tests/e2e/web-coverage/sectors/wa/wapol.remote-evac-cordon.spec.ts#L1) no cordon action. | AUD-034-002 |
| CHK083 | [ ] | UNVERIFIED | [TAS bridge](../../tests/e2e/web-coverage/sectors/tas/cross-jurisdiction-tas-mainland-cyclone.spec.ts#L1) no mainland-link evacuation. | AUD-034-009 |
| CHK084 | [ ] | UNVERIFIED | [AT](../../tests/e2e/web-coverage/sectors/tas/at.aeromedical-retrieval.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK085 | [ ] | UNVERIFIED | [SES TAS](../../tests/e2e/web-coverage/sectors/tas/ses-tas.severe-storm-rescue.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK086 | [ ] | UNVERIFIED | [TasPol](../../tests/e2e/web-coverage/sectors/tas/taspol.island-evac-coordination.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK087 | [ ] | UNVERIFIED | [TFS](../../tests/e2e/web-coverage/sectors/tas/tfs.bushfire-island-evac.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK088 | [ ] | UNVERIFIED | [ACT bridge](../../tests/e2e/web-coverage/sectors/act/cross-jurisdiction-act-nsw-bushfire.spec.ts#L1) no ACT/NSW incident integration. | AUD-034-009 |
| CHK089 | [ ] | UNVERIFIED | [ACT ambulance](../../tests/e2e/web-coverage/sectors/act/act-ambulance.heat-surge.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK090 | [ ] | UNVERIFIED | [ACT ESA](../../tests/e2e/web-coverage/sectors/act/act-esa.multi-agency-coordination.spec.ts#L1) no multiagency workflow; original cross-reference incorrectly says T080. | AUD-034-002, AUD-034-022 |
| CHK091 | [ ] | UNVERIFIED | [ACT FR](../../tests/e2e/web-coverage/sectors/act/act-fr.urban-fire.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK092 | [ ] | UNVERIFIED | [ACT policing](../../tests/e2e/web-coverage/sectors/act/act-policing.evac-cordon.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK093 | [ ] | UNVERIFIED | [ACT RFS](../../tests/e2e/web-coverage/sectors/act/act-rfs.bushfire-pre-positioning.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK094 | [ ] | UNVERIFIED | [AFP scenario](../../tests/e2e/web-coverage/sectors/act/afp.protective-services.spec.ts#L1) uses noncanonical `afp-act`; no protective-services action. | AUD-034-002, AUD-034-005 |
| CHK095 | [ ] | UNVERIFIED | [SES ACT](../../tests/e2e/web-coverage/sectors/act/ses-act.severe-storm-rescue.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK096 | [ ] | UNVERIFIED | [NT bridge](../../tests/e2e/web-coverage/sectors/nt/cross-jurisdiction-nt-wa-bushfire-cyclone.spec.ts#L1) no NT/WA shared incident. | AUD-034-009 |
| CHK097 | [ ] | UNVERIFIED | [Bushfires NT](../../tests/e2e/web-coverage/sectors/nt/bushfires-nt.savanna-burn.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK098 | [ ] | UNVERIFIED | [NTES](../../tests/e2e/web-coverage/sectors/nt/ntes.cyclone-shelter.spec.ts#L1) no shelter/preparedness workflow. | AUD-034-002, AUD-034-011 |
| CHK099 | [ ] | UNVERIFIED | [NTFRS](../../tests/e2e/web-coverage/sectors/nt/ntfrs.remote-fire-response.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK100 | [ ] | UNVERIFIED | [NTPF](../../tests/e2e/web-coverage/sectors/nt/ntpf.remote-evac.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK101 | [ ] | UNVERIFIED | [SJA NT](../../tests/e2e/web-coverage/sectors/nt/sja-nt.remote-medical-retrieval.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK102 | [ ] | UNVERIFIED | [NEMA activation](../../tests/e2e/web-coverage/sectors/commonwealth/nema.activate-comdisplan.spec.ts#L1) lacks COMDISPLAN/NJCOP/consequences/match. | AUD-034-002, AUD-034-009 |
| CHK103 | [ ] | UNVERIFIED | [ADF bridge](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-state-controller-bridge.spec.ts#L1) lacks complete DACC/A-B-C/arrival/mission-close chain. | AUD-034-009 |
| CHK104 | [ ] | UNVERIFIED | [ABF](../../tests/e2e/web-coverage/sectors/commonwealth/abf.border-disaster-coordination.spec.ts#L1) calculator only. | AUD-034-002 |
| CHK105 | [ ] | UNVERIFIED | [ADF](../../tests/e2e/web-coverage/sectors/commonwealth/adf.dacc-asset-arrival.spec.ts#L1) no asset arrival. | AUD-034-002 |
| CHK106 | [ ] | UNVERIFIED | [AFP Commonwealth](../../tests/e2e/web-coverage/sectors/commonwealth/afp-commonwealth.national-evac-coordination.spec.ts#L1) correct ID, no national coordination action. | AUD-034-002 |
| CHK107 | [ ] | UNVERIFIED | [ARC](../../tests/e2e/web-coverage/sectors/commonwealth/arc.recovery-financial-assistance.spec.ts#L1) no financial assistance. | AUD-034-002, AUD-034-012 |
| CHK108 | [ ] | UNVERIFIED | [ASA](../../tests/e2e/web-coverage/sectors/commonwealth/asa.shipping-evac.spec.ts#L1) no shipping evacuation. | AUD-034-002 |
| CHK109 | [ ] | UNVERIFIED | [BoM](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.cyclone-warning-relay.spec.ts#L1) no earthquake/tsunami AWS assertion. | AUD-034-002, AUD-034-008 |
| CHK110 | [ ] | UNVERIFIED | [GA](../../tests/e2e/web-coverage/sectors/commonwealth/ga-national.tsunami-warning-relay.spec.ts#L1) labels tsunami but measures lives arithmetic. | AUD-034-002, AUD-034-008 |
| CHK111 | [ ] | UNVERIFIED | [NEMA](../../tests/e2e/web-coverage/sectors/commonwealth/nema.activate-comdisplan.spec.ts#L1) no operational activation evidence. | AUD-034-009 |
| CHK112 | [ ] | UNVERIFIED | [RFDS](../../tests/e2e/web-coverage/sectors/commonwealth/rfds.remote-aeromedical.spec.ts#L1) no aeromedical action. | AUD-034-002 |
| CHK113 | [ ] | UNVERIFIED | [SJA National](../../tests/e2e/web-coverage/sectors/commonwealth/sja-national.community-first-aid.spec.ts#L1) no first-aid workflow. | AUD-034-002 |
| CHK114 | [ ] | UNVERIFIED | [Surf lifesaving](../../tests/e2e/web-coverage/sectors/commonwealth/surf-lifesaving.coastal-cyclone-evac.spec.ts#L1) no coastal evacuation workflow. | AUD-034-002 |
| CHK115 | [ ] | UNVERIFIED | [Community NGOs](../../tests/e2e/web-coverage/sectors/cross-sector/community-ngos.recovery-coordination.spec.ts#L1) no recovery action. | AUD-034-002 |
| CHK116 | [ ] | UNVERIFIED | [Health](../../tests/e2e/web-coverage/sectors/cross-sector/health.surge-capacity.spec.ts#L1) no surge-capacity action. | AUD-034-002 |
| CHK117 | [ ] | UNVERIFIED | [Local government](../../tests/e2e/web-coverage/sectors/cross-sector/local-government.recovery-funding.spec.ts#L1) no funding action. | AUD-034-002 |
| CHK118 | [ ] | UNVERIFIED | [State government](../../tests/e2e/web-coverage/sectors/cross-sector/state-government.disaster-declaration.spec.ts#L1) no declaration. | AUD-034-002 |
| CHK119 | [ ] | UNVERIFIED | [Territory government](../../tests/e2e/web-coverage/sectors/cross-sector/territory-government.cross-jurisdiction-coord.spec.ts#L1) no cross-jurisdiction state. | AUD-034-002 |
| CHK120 | [ ] | UNVERIFIED | [Transport](../../tests/e2e/web-coverage/sectors/cross-sector/transport.evac-routing.spec.ts#L1) no evacuation routing. | AUD-034-002 |
| CHK121 | [ ] | UNVERIFIED | [Utility](../../tests/e2e/web-coverage/sectors/cross-sector/utility.power-restoration.spec.ts#L1) no restoration state. | AUD-034-002 |
| CHK122 | [ ] | UNVERIFIED | [Volunteer](../../tests/e2e/web-coverage/sectors/cross-sector/volunteer.surge-deployment.spec.ts#L1) no deployment action. | AUD-034-002 |
| CHK123 | [ ] | UNVERIFIED | [Outcome 1](../../tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts#L26) no measured bushfire AND heat warning/lives-proxy trace. | AUD-034-001, AUD-034-004 |
| CHK124 | [ ] | UNVERIFIED | [Outcome 2](../../tests/e2e/web-coverage/capstone/outcome-2-bushfire-severe-storm.spec.ts#L21) no observed hazard/level timing. | AUD-034-001 |
| CHK125 | [ ] | UNVERIFIED | [Outcome 3](../../tests/e2e/web-coverage/capstone/outcome-3-tropical-cyclone-flood.spec.ts#L21) no relative lead-time evidence for both hazards. | AUD-034-001, AUD-034-011 |
| CHK126 | [ ] | UNVERIFIED | [Outcome 4](../../tests/e2e/web-coverage/capstone/outcome-4-bushfire-cyclone-logistics.spec.ts#L21) no logistics/DACC lifecycle. | AUD-034-001, AUD-034-009 |
| CHK127 | [ ] | UNVERIFIED | [Outcome 5](../../tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts#L45) wrong comparison and no handover/source evidence. | AUD-034-001, AUD-034-012 |
| CHK128 | [ ] | PARTIAL | [GA scenario](../../tests/e2e/web-coverage/sectors/commonwealth/ga-national.tsunami-warning-relay.spec.ts#L1) labels earthquake/tsunami but asserts no AWS envelope. | AUD-034-002, AUD-034-008 |
| CHK129 | [ ] | PARTIAL | [RBAC suite](../../tests/e2e/web-coverage/cross-cutting/rbac-aiims.spec.ts#L28) button visibility, not every-route incident authorization. | AUD-034-005 |
| CHK130 | [ ] | PARTIAL | [COP test](../../tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts#L27) initial markup timing, not update propagation. | AUD-034-009 |
| CHK131 | [ ] | PARTIAL | [Audit observer](../../tests/e2e/web-coverage/_support/fixtures/auditObserver.fixture.ts#L38) incomplete latency/full-provenance semantics; ledger local. | AUD-034-006 |
| CHK132 | [ ] | PARTIAL | [AWS suite](../../tests/e2e/web-coverage/cross-cutting/aws-warning-compliance.spec.ts#L25) no warning/de-escalation/all-clear transitions. | AUD-034-008 |
| CHK133 | [ ] | PARTIAL | [Evacuation suite](../../tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts#L29) no five-stage/types/approaches behavior. | AUD-034-011 |
| CHK134 | [ ] | MISSING | [Same suite](../../tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts#L29) has no eight-population filtering/priority assertion; all scenario bodies inspected. | AUD-034-011 |
| CHK135 | [ ] | PARTIAL | [Recovery suite](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L32) no four-environment/managed-handover assertion. | AUD-034-012 |
| CHK136 | [ ] | PARTIAL | [Span suite](../../tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts#L25) no report count/delegation/N/A suppression; static panel disconnected. | AUD-034-010 |
| CHK137 | [ ] | PARTIAL | [Axe configuration](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) disables required checks; three routes only, no GAP-A11Y-WORKSPACE emission. | AUD-034-014 |
| CHK138 | [ ] | PARTIAL | [Language probe](../../tests/e2e/web-coverage/_support/a11y/languagePackProbe.ts#L19) availability only, no per-hazard zh-Hans rendering. | AUD-034-014 |
| CHK139 | [ ] | PARTIAL | [Language test](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L44) no ATSI payload/disclaimer rendering. | AUD-034-014 |
| CHK140 | [ ] | PARTIAL | [Badge test](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L12) one route, no all-regulated routes/feature-specific carve-out navigation. | AUD-034-015 |
| CHK141 | [ ] | MISSING | [Rank comparison](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L29) never invokes gateway or observes upstream masking/denial. | AUD-034-015 |
| CHK142 | [ ] | PARTIAL | [Registry fixture](../../tests/e2e/web-coverage/_support/fixtures/carveoutRegistry.fixture.ts#L29) checks neither date nor approvers, and current schema/date policy differs. | AUD-034-015 |
| CHK143 | [ ] | PARTIAL | [HITL](../../tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts#L53) malformed-body negative not approval/authz denial; real publish admits pending approval. | AUD-034-008 |
| CHK144 | [ ] | PARTIAL | [Offline queue](../../apps/web/src/lib/offline/queue-store.ts#L215) removes before acknowledgement and test is online. | AUD-034-013 |
| CHK145 | [ ] | MISSING | [Append-only spec](../../tests/e2e/web-coverage/cross-cutting/audit-append-only.spec.ts#L29) no tamper attempt/unchanged row plus denial audit. | AUD-034-006 |
| CHK146 | [ ] | MISSING | [Trace type](../../tests/e2e/web-coverage/_support/types/coverage.d.ts#L5) and emitter have no PPRR phase; lessons suite no feedback transition. | AUD-034-004, AUD-034-016 |
| CHK147 | [ ] | PARTIAL | [Publish validation](../../apps/api/app/services/public_alert_service.py#L48) allows pending approval, contradicting no-publication-without-IC. | AUD-034-008 |
| CHK148 | [ ] | PARTIAL | [Escalation](../../scripts/web-coverage/gap-register.py#L227) has no increment/freeze of subsequent commands. | AUD-034-017 |
| CHK149 | [ ] | MISSING | [Gap commands](../../scripts/web-coverage/gap-register.py#L154) have no lead-disposition field/enforced prerequisite. | AUD-034-017, AUD-034-018 |
| CHK150 | [ ] | MISSING | [Rollback command](../../scripts/web-coverage/known-good.py#L148) records only; scoped CLI/CI chain contains no cross-run unrelated-gap detector/restore invocation. | AUD-034-019 |
| CHK151 | [ ] | PARTIAL | [Regress](../../scripts/web-coverage/gap-register.py#L177) flags but may escalate at cap rather than reset; gate ignores Reopened/Escalated. | AUD-034-003, AUD-034-017 |
| CHK152 | [ ] | PARTIAL | [Rollback fields](../../scripts/web-coverage/known-good.py#L148) supplied, no performed restoration evidence; gap audit omits full details. | AUD-034-006, AUD-034-019 |
| CHK153 | [ ] | PARTIAL | [Promote/close](../../scripts/web-coverage/gap-register.py#L154) trust PR/SHA strings and do not verify rerun/pass/no-regression. | AUD-034-017 |
| CHK154 | [ ] | PARTIAL | [Promote](../../scripts/web-coverage/gap-register.py#L154) can overwrite Closed without regression; no protected single state machine. | AUD-034-017 |
| CHK155 | [ ] | PARTIAL | [JUnit config](../../apps/web/playwright.config.cts#L44) writes nested file that upload glob misses; saved file all skipped. | AUD-034-004, AUD-034-021 |
| CHK156 | [ ] | PARTIAL | [Reporter](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L270) emits partial JSON; canonical companion absent and identity fields not attached. | AUD-034-004 |
| CHK157 | [ ] | MISSING | [Config](../../apps/web/playwright.config.cts#L39) has no screenshot/video-on-failure setting or proven sanitizer/transfer. | AUD-034-020, AUD-034-021 |
| CHK158 | [ ] | UNVERIFIED | [Quickstart estimate](quickstart.md#L77) is not measured representative <=30-minute evidence. | AUD-034-022 |
| CHK159 | [ ] | UNVERIFIED | [Shard timeout](../../.github/workflows/ci.yml#L261) not full <=45-minute CI elapsed proof. | AUD-034-021, AUD-034-022 |
| CHK160 | [ ] | UNVERIFIED | [Merge verifier](../../scripts/web-coverage/verify-trace-determinism.ps1#L16) not three clean test runs; source cross-reference misleading. | AUD-034-019, AUD-034-022 |
| CHK161 | [ ] | PARTIAL | [Persona resolver](../../tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts#L27) reads seed but API auth ignores header; exact `afp` missing. | AUD-034-005 |
| CHK162 | [ ] | IMPLEMENTED | [Scope](spec.md#L1039) and 68-ID inventory remain AU-only. AU CALD language codes do not imply Asian jurisdiction coverage. | none |
| CHK163 | [ ] | IMPLEMENTED | [FR-014/OOS-002](spec.md#L1040) constrain translation to warnings, not dashboard chrome. | none |
| CHK164 | [ ] | UNVERIFIED | [One-resource justification](plan.md#L606) is authored; actual technical approval/what-if missing. | AUD-034-020, AUD-034-022 |
| CHK165 | [ ] | IMPLEMENTED | [Playback service](../../apps/api/app/services/playback_service.py#L19) uses existing simulation/event repositories; no suite-specific engine rewrite. | none |
| CHK166 | [ ] | IMPLEMENTED | [Suite test bodies](../../scripts/web-coverage/_lib/persona_spec_generator.py#L528) contain no pixel snapshot behavior; OOS-005 preserved. | none |
| CHK167 | [ ] | IMPLEMENTED | [Cross-cutting tests](../../tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts#L27) are functional, not load/soak/chaos; budget assertions remain incomplete. | none |
| CHK168 | [ ] | CONFLICT | [Additive production registration](../../apps/api/app/api/router.py#L149) changes actual auth surface; no explicit spec-034 IdP boundary replacement. | AUD-034-005, AUD-034-022 |
| CHK169 | [ ] | IMPLEMENTED | [Scoped child/role](../../infra/bicep/main.bicep#L231) no wholesale infrastructure refactor; active wiring still an implementation gap. | none |
| CHK170 | [ ] | IMPLEMENTED | [IndexedDB queue](../../apps/web/src/lib/offline/queue-store.ts#L134) is web-based, not native mobile. | none |
| CHK171 | [ ] | UNVERIFIED | [Private-container declaration](../../infra/bicep/main.bicep#L231) and artifact intention do not establish actual release/access state. | AUD-034-020, AUD-034-022 |
| CHK172 | [ ] | UNVERIFIED | [Operational review](review-log.md#L12) pending; wrong header count and no ten-agent closure proof. | AUD-034-018, AUD-034-022 |
| CHK173 | [ ] | UNVERIFIED | [Sector review](review-log.md#L13) pending; no 58-persona panel completion. | AUD-034-018, AUD-034-022 |
| CHK174 | [ ] | UNVERIFIED | [Technical review](review-log.md#L14) pending; no 17-agent closure proof. | AUD-034-018, AUD-034-022 |
| CHK175 | [ ] | UNVERIFIED | [Review log](review-log.md#L8) no votes/roster, 30/35/20 differs from 10/58/17. | AUD-034-018, AUD-034-022 |
| CHK176 | [ ] | PARTIAL | [Resolver](../../scripts/web-coverage/review-log.py#L114) can override safety veto and misuses historical votes. | AUD-034-018 |
| CHK177 | [ ] | UNVERIFIED | No performed panel dispositions; [code](../../scripts/web-coverage/review-log.py#L114) applies operational veto onto other panels without required quorum/cycle. | AUD-034-018 |
| CHK178 | [ ] | UNVERIFIED | [Empty review table](review-log.md#L16) has no cross-panel lead decision. | AUD-034-022 |
| CHK179 | [ ] | UNVERIFIED | [HYP-002](spec.md#L1032) no measured uplift tally/validated-cohort decision or follow-on record. | AUD-034-003, AUD-034-022 |
| CHK180 | [ ] | UNVERIFIED | [HYP-003](spec.md#L1033) no attributable rubric decision accepting Asia deferral. | AUD-034-022 |
| CHK181 | [ ] | PARTIAL | [Depth template](../../scripts/web-coverage/_lib/persona_spec_generator.py#L528) no required persona-specific transition despite no executable bails. | AUD-034-002 |
| CHK182 | [ ] | PARTIAL | All 90 persona bodies have no executable bails, but [generator default](../../scripts/web-coverage/_lib/persona_spec_generator.py#L905) still emits them and gate cannot distinguish adequate workflow proof. | AUD-034-002, AUD-034-003 |
| CHK183 | [ ] | PARTIAL | [Evaluator/list registration](../../apps/api/app/api/router.py#L136) exists, but strict contract/audit durability/production boundaries not fulfilled. | AUD-034-006, AUD-034-007, AUD-034-022 |
| CHK184 | [ ] | CONFLICT | [Six-scenario requirement](checklists/validation.md#L322) mandates pairs #4/#5 while task examples prescribe other outcomes/hazards; existing files only calculator checks. | AUD-034-002, AUD-034-022 |
| CHK185 | [ ] | PARTIAL | [BoM file](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts#L26) and six peers assert no recovery/sovereignty/specialized handoff. | AUD-034-002, AUD-034-012, AUD-034-015 |
| CHK186 | [ ] | PARTIAL | [Depth schema](../../tests/e2e/web-coverage/_lib/depth-profiles/_schema.json#L8) and 68 files exist; exact AFP/source/three-step/task-key conflicts. | AUD-034-002, AUD-034-005 |
| CHK187 | [ ] | PARTIAL | [Generator validation](../../scripts/web-coverage/_lib/persona_spec_generator.py#L776) refuses invalid/missing profile but does not open structured gap. | AUD-034-002 |
| CHK188 | [ ] | PARTIAL | [Evaluator tests](../../tests/contract/test_outcome_evaluator.py#L133) assert same-tuple/unknown range/scenario; no strict fresh-run/provenance/gap-opener closure. | AUD-034-006, AUD-034-007 |
| CHK189 | [ ] | PARTIAL | [List service](../../apps/api/app/services/outcome_evaluator_service.py#L292) uses numeric-offset cursor and memory; no durable never-delete/tamper/boundary proof. | AUD-034-006 |
| CHK190 | [ ] | IMPLEMENTED | [NEMA](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-jatwc-cross-jurisdiction.spec.ts#L1), BoM and utility are placed by owning persona. Tag execution remains incomplete, not placement. | none |
| CHK191 | [ ] | PARTIAL | [Observer profile](../../tests/e2e/web-coverage/_lib/depth-profiles/observer-auditor.depth.yaml#L1) declares tamper; generator ignores it and performs calculator workflow. | AUD-034-002, AUD-034-006 |
| CHK192 | [ ] | IMPLEMENTED | [Canonical guard](../../apps/api/app/middleware/test_support_guard.py#L27) and Q25 explicit override agree; CI exports same flag. | none |
| CHK193 | [ ] | PARTIAL | [Reporter onBegin](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L194) writes metadata, but wrong hash semantic/no schema validator/no shared cycle transfer. | AUD-034-004 |
| CHK194 | [ ] | PARTIAL | [Accepted contract](contracts/outcome-evaluator.contract.md#L3) has embedded schemas; gate integration/formal acceptance chronology not proven. | AUD-034-007, AUD-034-022 |
| CHK195 | [ ] | PARTIAL | [T174-T177](tasks.md#L475) exist, but generator has no workflow translator/automatic gap opener. | AUD-034-002 |
| CHK196 | [ ] | IMPLEMENTED | [Named CI owners](../../apps/api/app/services/outcome_evaluator_service.py#L47) and [negative SC tests](../../tests/contract/test_outcome_evaluator.py#L158) cover 006-011 non-routability. Authored, not executed. | none |
| CHK197 | [ ] | PARTIAL | [Audit shape tests](../../tests/contract/test_outcome_evaluator.py#L245) assert fields but response schema/durable append-only are not fully enforced. | AUD-034-006, AUD-034-007 |
| CHK198 | [ ] | IMPLEMENTED | [Unknown persona test](../../tests/contract/test_outcome_evaluator.py#L208) and [service registry lookup](../../apps/api/app/services/outcome_evaluator_service.py#L226) reject unresolved IDs. Authenticated actor binding is a separate gap. | none |
| CHK199 | [ ] | PARTIAL | [Current/all test](../../tests/contract/test_outcome_evaluator.py#L288) only compares same current row; no cross-cycle gap/rollback event persistence/read-back. | AUD-034-006 |
| CHK200 | [ ] | CONFLICT | [Registration](../../apps/api/app/api/router.py#L149) explicitly mounts evaluator/list under production auth and workspace fallback when flags off; original 404-only rule not simply deleted. | AUD-034-005, AUD-034-022 |
| CHK201 | [ ] | CONFLICT | [Schema enum](../../tests/e2e/web-coverage/_lib/depth-profiles/_schema.json#L28) uses `approve`/`queue-and-sync`, checklist/spec use `approval`/`queue-sync`; task matches schema, no explicit precedence amendment. | AUD-034-002, AUD-034-022 |
| CHK202 | [ ] | PARTIAL | [Language pattern](../../tests/e2e/web-coverage/_lib/depth-profiles/_schema.json#L124) accepts code-shaped unknown tags, not canonical BCP-47 selection; no approved variant vocabulary check. | AUD-034-014, AUD-034-022 |
| CHK203 | [ ] | PARTIAL | [Render](../../scripts/web-coverage/_lib/persona_spec_generator.py#L834) never emits read-only tamper/report/acknowledgement steps. | AUD-034-002 |
| CHK204 | [ ] | PARTIAL | [Binary gate](../../scripts/web-coverage/_lib/schema_validators.py#L213) validates drifted 68 seed IDs/shapes, not exact roster or executed workflow. | AUD-034-002, AUD-034-003 |
| CHK205 | [ ] | PARTIAL | All six SA/WA/TAS files exist; [SAPOL body](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L25) and peers no specialized assertions/passing evidence. | AUD-034-002 |
| CHK206 | [ ] | PARTIAL | All four ACT/NT files exist; [NTES](../../tests/e2e/web-coverage/sectors/nt/ntes.atsi-multilingual-at-persona-level.spec.ts#L1) has no rendered language variant. | AUD-034-002, AUD-034-014 |
| CHK207 | [ ] | PARTIAL | [BoM](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts#L26) and [NEMA](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-jatwc-cross-jurisdiction.spec.ts#L1) correct folders, no relay source/sovereignty/DACC/JATWC workflow. | AUD-034-002, AUD-034-009, AUD-034-015 |
| CHK208 | [ ] | PARTIAL | [Utility scenario](../../tests/e2e/web-coverage/sectors/cross-sector/utility.insurance-recovery-handoff.spec.ts#L1) no actual Built/Economic state or insurance handoff. | AUD-034-012 |
| CHK209 | [ ] | PARTIAL | All 13 net-new bodies have only index/evaluator/audit checks; [SAPOL](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L25) representative controlling shape. | AUD-034-002, AUD-034-004 |
| CHK210 | [ ] | PARTIAL | [Closure math](../../scripts/web-coverage/review-log.py#L282) no PR/diff/passing-run/merit proof. | AUD-034-018 |
| CHK211 | [ ] | PARTIAL | [Escalation predicate](../../scripts/web-coverage/review-log.py#L262) also excludes any project-lead-owned gap; no real cycle-count progression. | AUD-034-017, AUD-034-018 |
| CHK212 | [ ] | PARTIAL | [Closure audit](../../scripts/web-coverage/review-log.py#L399) records counts, not required raw lists; assumes merit and empty-cycle success. | AUD-034-018 |
| CHK213 | [ ] | IMPLEMENTED | [CI flag](../../.github/workflows/ci.yml#L307) normalized; fully read workflow uses canonical name. | none |
| CHK214 | [ ] | IMPLEMENTED | [Quickstart examples](quickstart.md#L36) consistently export canonical flag; other command drift assessed separately. | none |
| CHK215 | [ ] | UNVERIFIED | [Q25 override](spec.md#L582) documents future change authority, but no future-proposal/review evidence can establish ongoing compliance. | AUD-034-022 |

### Other Original Checklists

`QC` and `PC` labels below are audit-only identifiers for original unnumbered items, in file order.

| Item | Original state | Status | Obligation and evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QC01 | [x] | CONFLICT | No implementation details: [spec](spec.md#L688) now prescribes schemas/paths/generator behavior beyond named Playwright surface. | AUD-034-022 |
| QC02 | [x] | IMPLEMENTED | User value/business needs explicit in [background](spec.md#L8) and five stories. | none |
| QC03 | [x] | PARTIAL | Nontechnical readership: story prose clear, but embedded schema/CLI/task amendments highly technical. [Q28](spec.md#L688). | AUD-034-022 |
| QC04 | [x] | IMPLEMENTED | Mandatory sections present in [full spec](spec.md#L1). | none |
| QC05 | [x] | IMPLEMENTED | No unresolved clarification marker; Q1-Q29 answered in [clarifications](spec.md#L53). This does not prove consistency. | none |
| QC06 | [x] | CONFLICT | Testable/unambiguous: metric, key, enum, cycle, auth and HYP-002 conflicts detailed in findings. [Depth definition](spec.md#L965). | AUD-034-022 |
| QC07 | [x] | IMPLEMENTED | [SC-001-SC-012](spec.md#L1002) have numerical/measurable obligations; actual performance unverified. | none |
| QC08 | [x] | PARTIAL | Technology-agnostic success criteria cite routes/Playwright/runner shape/PR-diff contract despite operator framing. [SCs](spec.md#L1002). | AUD-034-022 |
| QC09 | [x] | IMPLEMENTED | [Five stories](spec.md#L795) include all 20 explicit numbered acceptance scenarios. | none |
| QC10 | [x] | IMPLEMENTED | [Twelve edges](spec.md#L891) are enumerated. | none |
| QC11 | [x] | PARTIAL | [OOS boundaries](spec.md#L1035) explicit, but validated-cohort exception/auth additions need formal reconciliation. | AUD-034-022 |
| QC12 | [x] | IMPLEMENTED | [Assumptions/authority](spec.md#L1015) explicitly identify dependencies; absent session files remain verification blocker. | none |
| QC13 | [x] | PARTIAL | FR acceptance described, but [FR-029](spec.md#L965)/lower-level schema conflicts block unambiguous closure. | AUD-034-022 |
| QC14 | [x] | IMPLEMENTED | [Stories](spec.md#L795) cover persona, constitutional, national, simulation and iteration flows. Execution not implied. | none |
| QC15 | [x] | UNVERIFIED | Feature meets outcomes: [trace](coverage-trace.md#L7) empty and first run deferred, not empirical success. | AUD-034-022 |
| QC16 | [x] | CONFLICT | No leaked implementation details: same [Q27/Q28](spec.md#L663) schema/tool/task prescriptions as QC01. | AUD-034-022 |
| PC01 | [x] | PARTIAL | Every test persona seeded: normal resolver exists, but canonical AFP and special `contract` persona tags differ; [contract test](../../tests/e2e/web-coverage/_support/fixtures/__tests__/persona.contract.spec.ts#L15) is not resolver-based. | AUD-034-005, AUD-034-021 |
| PC02 | [x] | IMPLEMENTED | Test-support lookup router refuses production per [guard](../../apps/api/app/middleware/test_support_guard.py#L31) and [contract assertion](../../tests/contract/test_test_support_router.py#L65); evaluator production extension separately conflicted. | none |
| PC03 | [x] | MISSING | Required CI ban on literal permission arrays absent from [only registered suite rule](../../apps/web/eslint.config.mjs#L23) and full inspected CI workflow. | AUD-034-021 |
| PC04 | [x] | PARTIAL | [Resolver failure](../../tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts#L40) actionable on uncached miss, but cached identity bypasses later seed removal and no removal test runs/collects. | AUD-034-005, AUD-034-021 |
| PC05 | [x] | PARTIAL | Named cross-cutting guard spec absent from suite inventory; relocated [root contract](../../tests/contract/test_test_support_router.py#L50) covers guard. Not falsely missing behavior, but claimed dedicated file/run unsupported. | AUD-034-021, AUD-034-022 |

### Formal Review Records

| Record/obligation | Status | Evidence and disposition |
| --- | --- | --- |
| Cycle-0 F1/F2 persona roster repair | PARTIAL | [Original analysis](analysis.md#L37) records resolved planning names; current seed/generator AFP mismatch remains, and syntheses unavailable. |
| Cycle-0 F3 outcome mapping repair | PARTIAL | [Plan SC table](plan.md#L676) improved, but [analysis FR matrix](analysis.md#L136) still mislabels FR-003/006/015/019/025/026 and several tasks. |
| Cycle-0 F4 span-role repair | PARTIAL | [T063](tasks.md#L145) names Logistics correctly; live parent still omits it/uses empty reports. |
| Cycle-0 F5/F7 fixture naming/hazard repair | PARTIAL | Five filenames/tokens aligned; actual fixtures/generator still contain unsupported labels and do not prove paired hazards. [Fixture example](../../tests/e2e/web-coverage/_support/fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json#L6). |
| Cycle-0 F6 role type repair | IMPLEMENTED | [Persona type](../../tests/e2e/web-coverage/_support/types/persona.d.ts#L28) separates free-form role from AIIMS enum; authentication is a separate gap. |
| Cycle-1 C1/C2 canonical range/flag | IMPLEMENTED | [FR-028](spec.md#L963), Q25/Q29 and guard/range source agree on five evaluators and canonical flag. Production extension is a distinct unresolved boundary. |
| Cycle-1 H1 sovereignty inclusion | PARTIAL | [T185](tasks.md#L517) includes the file, but the actual sovereignty test still substitutes unrelated evaluations. |
| Cycle-1 H2 UUID versus ULID | PARTIAL | [Cycle schema](contracts/cycle-metadata.schema.json#L20) and reporter use UUID, but validators do not enforce v4 consistently and cross-jurisdiction correlation is malformed. |
| Cycle-1 M1 broader audit scope | PARTIAL | Explicitly left illustrative/not edited in [analysis](analysis-cycle1.md#L158); actual per-persona ledger read exists but full field/durable audit does not. |
| Cycle-1 L1 layout count | PARTIAL | Fifteen real cross-cutting files versus twelve in spec layout recognized; not a reason to omit any of the fifteen from this audit. [Analysis](analysis-cycle1.md#L158). |
| Accepted contracts / constitution PASS / chronological phase gates | UNVERIFIED | [Accepted stamp](contracts/outcome-evaluator.contract.md#L3) and [plan PASS prose](plan.md#L87) are authored records, not independently attributable panel/lead/infra approvals. Local dates also mix 2025-11, 2026-02, 2026-04/05; no trustworthy run/revision sequence supplied. |
| Operational/eastern/southwest/territories/technical cycle-1 review claims | UNVERIFIED | [Q15-Q19](spec.md#L339) cite session-only reviews and an eastern zero-objection endorsement; original panel records not local. Embedded amendments are binding, endorsement/85-agent completion is not inferred. |
| Public-output/cultural review and rubric acceptance | UNVERIFIED | [Review log](review-log.md#L8) has no approvals; language availability/placeholder prose is not cultural or accessibility sign-off. |

All incomplete formal-review items feed AUD-034-022, with AUD-034-018 owning actual merit/veto mechanics.

## Design And Risk Obligations

These tables account for the remaining full local plan/research/data-model content. A decision being
marked Resolved in research means authored intent, not demonstrated delivery or approval.

| Research decision | Status | Actual assessment and owning follow-up |
| --- | --- | --- |
| R-001 | PARTIAL | CTS relocation preserves main config/legacy projects, but helper contract excluded and axe empty selection; AUD-034-021. |
| R-002 | PARTIAL | Reporter exists, not structured annotation/required tuple/joined-ID evidence; AUD-034-004. |
| R-003 | PARTIAL | Four shards authored; no full runtime/budget proof or complete transfers; AUD-034-004/021/022. |
| R-004 | PARTIAL | Seed lookup exists, signed/guarded principal propagation does not; AUD-034-005. |
| R-005 | PARTIAL | Polling reads separate memory ledger, not Blob-projected action audit; AUD-034-006. |
| R-006 | PARTIAL | Registry fixture ignores errors/schema/date and suite never gateway-probes; AUD-034-015. |
| R-007 | CONFLICT | Required AA coverage disabled for contrast/region; severity treatment not an approved exemption; AUD-034-014/022. |
| R-008 | PARTIAL | Placeholder identifier/disclaimer design authored; actual Chinese carrier isn't translation and cultural approval unverified; AUD-034-014/022. |
| R-009 | PARTIAL | JSON, not Markdown, is CLI source; local-only incomplete audit and weak transition enforcement; AUD-034-017. |
| R-010 | PARTIAL | Tribunal logic uses wrong roster/merit/veto and no agent ingestion; AUD-034-018. |
| R-011 | PARTIAL | Five AU hazard seeds/fixture names exist; no separate measured pairs/nonmandatory tsunami AWS proof or source-attributed baselines; AUD-034-001/002. |
| R-012 | PARTIAL | Three jobs composed but no complete fail-closed gate/artifact/CD lifecycle; AUD-034-003/004/019. |
| R-013 | PARTIAL | One container authored but wrong retention/inactive deployment root and no archive writer; AUD-034-020. |
| R-014 | PARTIAL | Browser cache key uses app-local lockfile path while workspace has root lock; cache/performance execution unverified; AUD-034-021. |
| R-015 | PARTIAL | Wait rule authored, no reaffirm subcommand or three-run signal check; no verified retry/flake capture; AUD-034-019/021. |
| R-016 | PARTIAL | Names/GPS/free text/media/JUnit sanitization and video-discard/trace handling absent; AUD-034-020. |
| R-017 | PARTIAL | Title parser handles some axes only, no phase/all-tag lint/flake-gap enforcement or mobile-selection parity; AUD-034-003/004/021. |
| R-018 | PARTIAL | Source says read baseline/projected widget; actual tests supply constants and proxy helper only checks labels; AUD-034-001/012. |
| R-019 | PARTIAL | Schedule/manual/closed-PR triggers exist, but no upstream run ID/latest artifact binding/agent objections, fixed cycle and swallowed errors; AUD-034-018. |
| R-020 | PARTIAL | Draft-07 schema/68 files exist; oneOf rejects both non-null evaluator and UI selector despite prose allowing both; generator ignores steps; AUD-034-002/022. |
| R-021 | PARTIAL | Route/range/idempotency authored, not full numeric/UUID/actor/schema/audit integration; AUD-034-006/007. |
| R-022 | PARTIAL | Current/all reads process-local memory and fixed timestamp; offset-string cursor, not stable durable projection; AUD-034-006. |
| R-023 | PARTIAL | Metadata file exists, not shared across runners/transferred/merged or fully seed-contract sourced; AUD-034-004. |
| R-024 | IMPLEMENTED | Canonical test-support flag restored by Q25; historical contradictory text explicitly overridden. |

| Plan risk | Status | Mitigation evidence or residual exposure |
| --- | --- | --- |
| RISK-01 | UNVERIFIED | Four shards alone do not prove full 30/45-minute runtime; AUD-034-021/022. |
| RISK-02 | PARTIAL | Deterministic evaluator avoids model variability but also bypasses actual HITL JSON/workflow; AUD-034-001/008. |
| RISK-03 | PARTIAL | Actual registry schema/policy has drifted; suite neither schema-validates nor compares policy; AUD-034-015. |
| RISK-04 | CONFLICT | Test-support lookup guarded, evaluator intentionally mounted in production auth and ungated fallback; authority/negative tests must address all modes; AUD-034-005/022. |
| RISK-05 | UNVERIFIED | No <=2-second durable parallel-shard audit measurement; polling memory is not mitigation proof; AUD-034-006/022. |
| RISK-06 | PARTIAL | Rule exists but CI lint/flake handling and three-run signal evidence incomplete; AUD-034-019/021. |
| RISK-07 | PARTIAL | JSON key redaction does not sanitize whole failure artifact set; AUD-034-020. |
| RISK-08 | PARTIAL | No increment/real panel progression; bad veto/override/closure semantics; AUD-034-017/018. |
| RISK-09 | PARTIAL | Hazard tags share one calculator/seed, no independent pair or persona-specific evidence; AUD-034-001/002. |
| RISK-10 | PARTIAL | Container assignment source is correctly scoped, but active resource/RBAC application and zero-trust validation unverified; AUD-034-020. |
| RISK-11 | UNVERIFIED | Placeholder prose is not Indigenous-led language validation/sign-off; English labelled Chinese also unresolved; AUD-034-014/022. |
| RISK-12 | PARTIAL | GitHub retention config is not AU-resident archive assurance; no enforced sanitized transfer within claimed 90-day period; AUD-034-020. |
| RISK-13 | PARTIAL | Same-input sorting implemented, but duplicate/conflicting rows and missing-native-exit handling leave evidence gaps; AUD-034-004/019. |
| RISK-14 | UNVERIFIED | No performed active-template what-if/deploy/timing evidence; AUD-034-020/022. |
| RISK-15 | PARTIAL | Seed lookup helps, but canonical identity/cached-role drift and no real fixture principal binding remain; AUD-034-005. |
| RISK-16 | PARTIAL | Shape gate present, but doesn't ensure actual workflow/depth/actor semantics; default regeneration can reintroduce bails; AUD-034-002/003. |

| Data-model entity / invariant | Status | Inspected implementation and required correction |
| --- | --- | --- |
| 1 CoverageTraceRow | PARTIAL | Type exists; missing actual route/audit/correlation/phase binding, wrong aggregate cardinality/IDs; AUD-034-004. |
| 2 GapRegisterEntry | PARTIAL | JSON fields largely present, but TS lacks additive fields and no enforced closure proof/atomic audit; AUD-034-017. |
| 3 ReviewVote | PARTIAL | Fields authored but roster/standing/cycle/merit validation and saved dispositions incomplete; AUD-034-018. |
| 4 KnownGoodManifest | CONFLICT | Different schema_version/entries model, no required hash/run/full deployment shape; no explicit replacement record; AUD-034-019/022. |
| 5 PersonaFixture | PARTIAL | Lookup/type exists; no signed seeded principal/strict role/request consistency, AFP drift; AUD-034-005. |
| 6 HazardScenarioFixture | CONFLICT | Type/fixture use scenario_id/hazards versus required fixture_id/paired baseline/incident chain/languages; relocated numeric seed exists, not missing globally; AUD-034-001/022. |
| 7 EvacuationStageState | CONFLICT | Spec stages versus model warning-state enum/population subset differ; use existing real stages model and approved correction, AUD-034-011/022. |
| 8 RecoveryEnvironmentState | PARTIAL | Four-environment service exists; measured baseline/projection/window/source/handover is not established by suite; AUD-034-012. |
| 9 AgentObjection | CONFLICT | Schema/type exist but template/guide use incompatible vote/evidence_uris shape and no ingestion; AUD-034-018/022. |
| 10 CycleMetadata | PARTIAL | UUID/SHA/file hash emitted; fixed start, all-zero SHA fallback accepted, no canonical header/shared runner cycle; AUD-034-004/006. |
| 11 DepthProfile | CONFLICT | Task keys/enum/minimum differ from model/schema; oneOf and ignored steps defeat combined/read-only workflows; AUD-034-002/022. |
| 12 EvaluatorRequest | PARTIAL | Extra top-level fields rejected but UUID/strict metric/SC/actor contracts unenforced; AUD-034-007. |
| 13 EvaluatorResponse | PARTIAL | Shape returned, not schema-enforced; evidence points only at memory calculator ledger; AUD-034-006/007. |
| Base cross-entity invariants | PARTIAL | Audit ID -> durable Blob with matching correlation/latency, Closed gap -> actual passing test, vote cycle -> gap count, known-good -> trace hash, and scenario/persona -> exact seeded IDs are not all enforced; AUD-034-004/005/006/017/018/019. |
| Cycle-1 cross-entity invariants | PARTIAL | Fixed timestamp matches server literal but not real run boundary; cycle links not retained/merged, valid profile != executed workflow, request/response/audit actor not independently authenticated; AUD-034-002/004/005/006/007/017. |

## Connected Surfaces And Search Limits

| Inspected chain / negative boundary | Conclusion |
| --- | --- |
| [Workspace route](../../apps/web/src/app/workspaces/[personaId]/page.tsx#L17) -> [client](../../apps/web/src/lib/api/personas.ts#L32) -> [API](../../apps/api/app/api/routes/personas.py#L7) -> [service](../../apps/api/app/services/persona_workspace_service.py#L26) -> [registry](../../apps/api/app/repositories/persona_registry_repository.py#L52) / [tasks repository](../../apps/api/app/repositories/coordination_tasks_repository.py#L109) | Task loading and organization-filtered Cosmos/memory repository exist. Requested persona determines visibility rather than caller authorization; role panels receive empty/placeholder inputs. This is not a claim that workspace routes or database repositories are absent. |
| [Suite fixtures](../../tests/e2e/web-coverage/_support/webCoverageTest.ts#L10) -> [Next rewrite](../../apps/web/next.config.ts#L28) -> [guarded router](../../apps/api/app/api/router.py#L136) -> [bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L42) -> evaluator/list | Real seed lookups, five calculators and idempotency exist; no product workflow execution is introduced by invoking them. `X-Test-Persona-Id` search scoped to API implementation found no consumer; web implementation found incident-page visibility lookup only. |
| [PIO panel](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L56) -> [draft bridge](../../apps/api/app/api/routes/agents.py#L199); [IC card](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L50) -> mode-dependent evaluator/fallback; [publish](../../apps/api/app/api/routes/alerts.py#L37) -> [service](../../apps/api/app/services/public_alert_service.py#L66) -> in-memory ALERTS/payload adapters | Draft carrier/approval UI is not a complete approved translated publication chain. No external delivery success or human approval asserted. Existing warning-chain/CAP/EDXL API prevents an incorrect missing-warning-feature conclusion. |
| [Offline panel](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L89) -> IndexedDB drain -> route POST; [replay API](../../apps/api/app/api/routes/offline_replay.py#L101) -> [audit repository](../../apps/api/app/repositories/audit_repository.py#L92) | Queue/replay/audit helpers exist but erase before acknowledgement or record without domain dispatch. Search/read bounded to queue store, worker/registration helper, active field panel, replay route and audit repository. |
| [Real stages API](../../apps/api/app/api/routes/evacuation.py#L82) -> stage domain functions/state store; [recovery API](../../apps/api/app/api/routes/recovery.py#L46) -> [recovery service](../../apps/api/app/services/recovery_service.py#L25) -> RECOVERY_TRACKERS; [UI](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L60) | Nontrivial domain support exists. Audit is of spec-034's connected expression, auth scope, actual transition assertions and evidence, not a separate review of whole evacuation/recovery agents. |
| [Simulation creation](../../apps/web/src/app/simulations/create/page.tsx#L39) / [playback](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L15) -> [playback API](../../apps/api/app/api/routes/simulation_playback.py#L52) -> [participant service](../../apps/api/app/services/playback_service.py#L42) -> event/simulation repositories; [report service](../../apps/api/app/services/exercise_report_service.py#L31) | Actual participant checks and event replay exist. No report export/lessons linkage in inspected report page or spec-034 tests; report route omits storage dependency. No claim of proven tenant isolation/runtime determinism. |
| [Reporter](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L225) -> [merge](../../scripts/web-coverage/trace-merge.py#L49) -> [gate](../../scripts/web-coverage/_lib/schema_validators.py#L82) -> [iteration](../../.github/workflows/web-coverage-iteration.yml#L69) / [known-good](../../scripts/web-coverage/known-good.py#L92) | Entire named script family/CI jobs read. No missing-helper names were accepted on filename alone; no alternate automatic regression, portfolio invalidation, sidecar ingestion, or Blob writer was found in this controlling chain. Other specifications' automation is not assumed to satisfy it. |
| Historical path relocation | `apps/web/playwright.config.ts` found as [CTS config](../../apps/web/playwright.config.cts#L1); old API test paths found under [root contracts](../../tests/contract/test_outcome_evaluator.py#L1); `/disasters` explicitly [redirects](../../apps/web/src/app/disasters/page.tsx#L1) to [root mapper](../../apps/web/src/app/page.tsx#L3); governance data-source listing and thirteen sector route pages exist. Route changes do not automatically supersede feature obligations. |
| Missing cited inputs / schema / guard test / canonical trace | Exact-name inventory enumerated 11,628 repository files including hidden/ignored paths, excluding node_modules, git internals, .next and Python environments/caches. No operational/eastern/southwest/territories/technical input Markdown, known-good schema, or named web-coverage guard spec found; canonical trace JSON absent. No contents of another implementation-review report were read. External session directories were not searched; recover or formally replace inputs under AUD-034-022. |
| Test-source census | All 15 cross-cutting and five capstone bodies read; all 90 persona bodies scanned for actual endpoint/interaction/assertion behavior and all 13 FR-030 assertion lists inspected. Generator templates and registry read fully. All 68 depth profiles inventoried, each has two steps; shape/field examples and schema fully inspected. Metadata counts are not executable test collection or passing proof. |
| Evidence search | Complete local specification subtree plus ignored web-coverage artifacts/JUnit/run JSON examined; no current-revision full passing suite, three-run determinism, human/accessibility/performance/infra approval or usable restoration baseline found there. No remote Actions, branch settings, cloud state, browsers, or external approvals consulted. |

### Contract Conflicts Requiring Explicit Resolution

- Q10's three-part tuple versus schema/plan four-part key and merge's five-part key; joined Test IDs versus counts.
- Q20/model `approval`/`queue-sync` versus task/schema `approve`/`queue-and-sync`; T175's primary route/assertion
  array/audit_readback/three-step request versus actual schema's workspace_route/assertion object/two-step profiles.
- `oneOf` rejects both populated evaluator and UI selector although prose says both may be present; the
  generator rejects permitted UI-only profiles. Language regex checks shape, not canonical recognized tags.
- FR-005 Open reset versus Reopened/Escalated storage, different escalation counters, and code permitting
  arbitrary transitions; Q13 non-overridable safety veto versus plan/code override behavior and wrong roster.
- Data-model manifest versus actual entries map; no replacement schema or trace hash; seven-year retention
  versus 30-day policy in a different root; renewal deadline versus 90-day review-age semantics.
- Test-only evaluator 404 requirement versus explicit additive production and ungated workspace fallback
  registration. The fallback is selected by flag absence, not an environment allowlist, and returns a different
  `approved`/`rows` shape. Preserve compatibility only through a documented, authorized contract decision.
- HYP-002's validated-cohort gate versus FR-002/FR-023 non-relaxable 68/68; no actual measured re-scope record.

No entire original task or feature was labelled SUPERSEDED. Only Q19's explicitly replaced flag diagnosis is
so classified; Q10/Q23/Q25/Q26/Q29 explicit sub-binding replacements are cited. Lower-level comments claiming
to prove a stronger behavior with a calculator are not replacement authority.

## Audit Checks And Limits

Performed checks were read-only git metadata, complete local document reads, scoped source/test/config
inspection, JSON/text inventories, exact task/checklist comparison, local Markdown target/line-bound checks,
and report diagnostics. `rg` was unavailable; its failed empty output was discarded and replaced by the
successful bounded PowerShell filename inventory. Two report-check tooling issues (duplicate patch path and
greedy link parser) were corrected without product edits or validator files.

Original-state accounting is explicit: 206 task rows preserve `[X]` as `[x]`, no suffixes found; all 215
workflow boxes remain represented as unchecked; all 16 quality and five persona-contract boxes preserve
their checked original states. Twenty acceptance scenarios and twelve edge cases have separate rows.
Twenty-two AUD-034 follow-ups remain unchecked and include expected/actual impact, owning surfaces,
developer boundaries/dependencies, concrete positive/negative/edge assertions, future commands and done criteria.

Blocking evidence limits: missing authoritative session inputs, no attributable current-revision passing
matrix, no three independent clean runs, no complete human/panel/cultural/accessibility sign-offs, no measured
full runtime budgets, no verified applied branch protection or active immutable archive/what-if/restore.
These remain UNVERIFIED where execution/approval is required. No implementation, deployment, sign-off,
original checkbox update, index edit, branch or commit was performed. Only this report was written.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 034 only. Three parallel technical reviews examined capstone
measurement truth, persona/authenticated workflow coverage, and evidence/rollback/retention integrity. The reported
SC-005 comparator defect was checked and is already corrected in the current evaluator: economic-loss reduction must be
`>= 0.30`. The offline queue loss finding spans the replay panel and API acknowledgement contract, so no speculative
source edit was applied.

Remaining open work includes authenticated incident/persona scope, completed approval publication, durable audit read-back,
offline acknowledgement/requeue, real COP/evacuation/recovery workflows, trace identity, accessibility/language,
sovereignty, gap closure, rollback restoration, retention/redaction, and attributable browser/human evidence.

# Analysis findings

Analysis completed: 2026-10-18T18:08:33.6798888+11:00.

Result: HOLD pending human review and targeted remediation. Planned coverage includes all 16 functional requirements and seven success criteria; this is not implementation or operational acceptance.

| ID | Severity | Location | Finding | Required refinement |
|---|---|---|---|---|
| I1 | HIGH | tasks.md:25; contracts/rollout-and-preflight.md:60-65 | G4 requires validation evidence while blocking all Azure validation until that evidence exists. | Separate approval for scoped evidence collection from activation, canary, switching and promotion approval. Preserve required What-If. |
| U1 | HIGH | contracts/routing-configuration.md:24-29,71-79; data-model.md:53-59; tasks.md:48,61 | Legacy model metadata is not explicitly bound to the deployment actually selected by an explicit tier setting. | Require evidence that legacy identity describes the resolved destination. Test explicit deployment A with legacy coordinate pointing to B and absent new identity fields. |
| I2 | HIGH | research.md:143-149; contracts/inference-provenance.md:27-46,86-89; tasks.md:136 | Unknown request-submission evidence has no explicit inference-record admission rule. | Define true/false/unknown admission rules for each record surface. Preserve uncertainty in existing event envelopes without asserting invocation; add writer-level row-count cases. |
| U2 | MEDIUM | contracts/routing-configuration.md:77-88; tasks.md:61,68 | Simulation isolation is not explicitly tested against live tiers resolved through legacy mappings. | Compare effective resolved destinations within the account, including alias, exact-coordinate and base-model live-tier resolution. |
| U3 | MEDIUM | tasks.md:97,110; contracts/rollout-and-preflight.md:47-58; data-model.md:147-155 | Stale-evidence rejection lacks a defined freshness or invalidation policy. | Require an approved freshness/invalidation policy bound to target and configuration revision; specify missing-policy failure without inventing a universal duration. |
| I3 | MEDIUM | quickstart.md:143-148; tasks.md:160,173,185-186 | Local implementation completion, target release readiness and operational migration acceptance are conflated. | Name the three completion levels separately; synthetic migration rehearsal must not satisfy real operational acceptance. |

## Outstanding gates

- The 36 items in checklists/routing-rollout.md remain unchecked; reviewer acceptance has not been evidenced.
- Approved target baselines, current governance evidence and pinned AVM preservation compatibility remain execution gates.
- Deployment activation, optional migration and retirement require separate approvals.
- No direct constitution violation was identified in the design.
- Analysis did not run live validation or feature acceptance, change approved artifacts, or authorise implementation.

## Next step

Obtain approval for targeted plan/contract/task refinement, address the findings, and rerun analysis before proceeding to implementation. The analysis marker records that analysis ran, not that it passed.

## Targeted refinement disposition — 2026-10-18

User approved resolving all six findings before the orchestrator reruns Analyze.
The original findings/HOLD above remain the analysis history. Dispositions below
record artifact refinement only, **pending independent reanalysis**, not a
verified pass, implementation approval or operational acceptance.

| ID | Refinement disposition and artifact references |
| --- | --- |
| I1 | Addressed in design: `contracts/rollout-and-preflight.md` “Separate collection and activation authority” and `tasks.md` G0/G4 now allow explicitly scoped baseline/governance reads before evidence exists, and explicitly scoped metadata/mandatory What-If/carve-out validation to assemble G4 after prerequisite gates. Canary/activation/switch/promotion remain separately stage-approved. Aligned `plan.md` rollout ordering, `research.md` R8, `quickstart.md` §3 and T029/T051/T052. No Azure authority inferred or exercised. |
| U1 | Addressed in design: `contracts/routing-configuration.md` “Metadata association after destination resolution”, `data-model.md` §§4/6 and `research.md` R6 require a same resolved deployment/account association, not mere key uniqueness. Explicit A with absent new fields and legacy-to-B retains A with unavailable identity. T007/T009/T010/T012/T020 and `quickstart.md` §2 cover mismatched, matching, absent and wrong-account association; embedding/unambiguous legacy use retained. |
| I2 | Addressed in design: `contracts/inference-provenance.md` “Evidence boundary and per-surface admission”, `data-model.md` §7 and `research.md` R7 distinguish true submission/unknown completion from unknown submission. New inference rows require proved true submission; false/null submission admits zero, with uncertainty retained in existing agent/event/invocation envelopes. T032/T033/T036/T037/T043, the shared T037–T042 obligation and `quickstart.md` §2 specify all five single-call writer counts and two-round totals, preserving opt-out/ownership, reader-first strict schemas and historical uncertain records. |
| U2 | Addressed in design: `contracts/routing-configuration.md` resolution/isolation rules, `data-model.md` §3 and `research.md` R3 compare effective live destinations in the same account, including alias/exact/base paths without live explicit settings and mixed explicit/legacy cases. T009/T012/T020 and `quickstart.md` §2 add collisions, distinct controls and unresolved-comparison fail-closed cases. |
| U3 | Addressed in design: `contracts/rollout-and-preflight.md` “Approved freshness and invalidation policy”, `data-model.md` §§8/9 and `research.md` R8 require approved policy/version, target/config/image/compiled-proposal bindings, invalidation evaluation and authorised refresh/reapproval. Missing/unapproved policy or stale/unbound evidence fails closed; no universal TTL invented. Aligned task gate text, T023/T028/T029/T046/T051/T052, `plan.md` and `quickstart.md` §§2/3. Actual target policy remains an external gate, not fabricated here. |
| I3 | Addressed in design: `contracts/rollout-and-preflight.md` “Completion and acceptance levels”, `quickstart.md` completion table, `plan.md` validation gates and `research.md` R9 distinguish local implementation/procedure verification, target P1 release readiness and real P2 operational migration acceptance. T029/T046/T048/T051/T052 and FR-016/SC-006 mapping keep synthetic branch coverage distinct from actual readiness/traffic-switch/forward/rollback acceptance. Optional G5 execution and separate G6 retention/retirement decisions remain pending. |

**Inventory**: 52 tasks before/after; no task IDs, parallel groups or existing
task dependencies changed. No task/reviewer checkboxes ticked. `spec.md`,
checklists and the prior `.analyze-done` marker are unchanged.

**Remaining gates**: Independent Analyze rerun by the orchestrator; actual
reviewer/H1 acceptance; scoped G0 authority; approved target baselines and
freshness/invalidation policy; current inherited governance and pinned AVM
preservation compatibility; stage-specific G4 release approval and optional
G5/G6 operational approvals. This refinement supplies none of that external
evidence. No application/IaC code, models, resources or historical records were
changed, and no deployment, live validation, inference, commit or Analyze rerun
was performed.

## Independent analysis rerun - 2026-10-18T18:35:28.8437822+11:00

Result: HOLD. All six original findings (I1, U1, I2, U2, U3, I3) are
independently verified as resolved in the design/task artifacts. This is not
verification of implementation or operational controls.

One HIGH finding was newly detected; it is not established as introduced by
the refinement:

| ID | Severity | Location | Finding | Required refinement |
| --- | --- | --- | --- | --- |
| I4 | HIGH | tasks.md:27; contracts/rollout-and-preflight.md:198-214 | G5 requires verified replacement readiness before authorising provisioning, while the procedure can verify actual readiness only after provisioning. | Separate pre-provision approval based on approved proposal, quota, policy and baseline checks from post-provision parity/readiness verification and separately authorised traffic switching. Retain independent G6 retirement approval. |

Delta: six original findings fixed, one newly detected HIGH finding, one
remaining finding. Planned coverage remains 23/23 FR/SC items across 52 tasks.
All tasks and 36 reviewer-owned routing-rollout checklist items remain unchecked.
External and operational gates remain unsatisfied. Human approval is required
before further remediation or phase advancement.

## I4 targeted refinement

User approved fixing I4 and rerunning Analyze. The rollout contract now
distinguishes proposal-based G5a provisioning approval, G0-authorised actual
post-provision readiness/parity evidence, and separately scoped G5b traffic
approval. The tasks gate table and T046 reference the same ordering. G6
retirement remains independent. No task IDs or checkboxes changed.

This is a design refinement pending independent reanalysis, not permission
to provision, read Azure metadata, invoke models, switch traffic or retire
resources.

## Independent analysis rerun - 2026-10-18T18:47:20.5109281+11:00

Result: PASS for artifact consistency. I4 is independently verified resolved
in tasks.md G5a/G5b/G6 and T046, and the rollout contract's staged authority
and migration procedure. No remaining material artifact findings or
constitution conflicts were detected. All seven identified findings are
resolved in design; this does not verify implemented behaviour.

Planned coverage remains 23/23 FR/SC items across 52 unchecked tasks.
The 36 reviewer checklist items, approved target baselines/governance/AVM
evidence and operational approvals remain outstanding. No implementation,
live validation, provisioning, inference, traffic switch, deletion or commit
was performed by this analysis.

## E1/E2 implementation remediation — 2026-10-19

Authority: **“Approve — fix both provenance findings and re-verify”**.
These are local implementation corrections, **pending independent read-only
re-verification**, not independent acceptance or a release decision.

| Finding | Implemented correction | Regression evidence |
| --- | --- | --- |
| E1 — HIGH: post-completion processing erased proved evidence | `LLMCallMixin` captures response evidence immediately, before text/budget/safety processing, and reuses it on downstream failure. The local fallback/error remains distinct from the observed model outcome. Proved call ID, resolved identity and actual usage survive; pre-response errors retain their attached evidence or unknown, never invented success. | Installed SDK plus fake transport: safety-validator and budget-processing exceptions both failed first with lost usage; both now retain the original transport call ID, true/succeeded, independent identity and 7/2 usage. Deadline and ordinary blocked-completion safety fallback still pass. |
| E2 — MEDIUM: workflow positive provenance could never reach timeline guards | Workflow risk/communication execution captures adapter evidence separately from generated JSON. Common mixin and nested MAF audit scopes forward evidence to this collector without adding an audit owner. API builders retain typed evidence only in private internal model subclasses; the timeline admits one event per distinct proved call ID, including failed/unknown completion. Alias/model/version/usage come from the same request evidence, not generated flags or model labels. | Full `AmaWorkflow` → API builders → timeline tests cover MAF success, submitted failure, lost completion, no call, opaque submission, plus real common-adapter success. Event counts are 2/2/2/0/0/2; generated positive flags and misleading identities are deliberately present and ignored. |

The first test-only run reproduced **7 failures / 2 passes**. The separately
added common-adapter positive-path regression also failed before its collector
bridge was implemented. Final provenance files: **62 passed**. Expanded relevant
regression union: **1,313 passed / 4 unchanged pre-existing stale audit-test
failures**, 56 selectors. Ruff/format: **41 files pass**; configured mypy:
**39 files plus one separate fixture pass**; original anchors **50/50 unchanged**.
Exact commands and limitations:
[verification.md](verification.md#e1e2-provenance-remediation-2026-10-19).

No public/domain schema, target model/configuration, infrastructure, strict
reader, historical fixture, reviewer checklist or task marker changed. No
dependency installation, delegation, hook/workflow, Azure/live inference
operation, staging or commit occurred. T024–T027/T030 and external G0–G6
decisions remain blocked/pending as documented in the T052 handover.

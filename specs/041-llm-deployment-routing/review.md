# Pre-Implementation Review (Phase 7, fresh complete review)

**Feature**: 041 - Unambiguous LLM Deployment Configuration and Routing
**Branch**: `model-upgrade-chat-sumlation`
**Review model**: claude-sonnet-5.5
**Generating model**: GPT-6.1 Sol (Phases 1-6)
**Mode**: Read-only. No files, tasks or checklist items were changed by the
reviewer. No Azure reads or writes, commits or handoffs.

## Artifact coverage

The fresh reviewer read spec.md, plan.md, tasks.md, research.md, data-model.md,
quickstart.md, remediation.md, the earlier incomplete review, both checklists
and all three contracts in full. It read the constitution principles,
Non-Negotiables 1-5, Quality Gates and Governance sections, and rechecked
task dependencies and T012/T013/T027/T034/T036. The earlier limited review is
superseded; its findings are dispositioned below.

## Summary

| Dimension | Verdict | Note |
| --- | --- | --- |
| Spec-Plan Alignment | PASS | All 16 FRs, four stories and seven SCs are covered; authority, metadata, provenance, freshness and acceptance separations are consistent. |
| Plan-Tasks Completeness | PASS | Every component and contract has tasks; 23/23 planned FR/SC coverage. |
| Dependency Ordering | PASS | Phase and gate ordering is correct; T013 ordering is a low observation. |
| Parallelization Correctness | PASS | Nine groups, maximum three concurrent tasks, 23 parallel-marked tasks; shared files are sequenced. |
| Feasibility and Risk | WARN | Large coherent tasks and transport submission-evidence feasibility require execution evidence. |
| Standards Compliance | PASS | Actual constitution requirements are addressed; no numeric coverage threshold is imposed. |
| Implementation Readiness | WARN | Reader file inventory and per-target approval evidence must be established; H1 remains outstanding. |

**Overall: READY WITH WARNINGS for local implementation only, subject to
H0/H1. Operational readiness: NOT READY, by design.** No blocker was found
in the reviewed design. This review does not satisfy H1 owning-reviewer
acceptance or any target or operational gate.

## Constitution check

- Constitution v1.2.0 sets no numeric coverage threshold. Its testing quality
  gates require lint, unit and integration tests; the plan covers these.
- The auditable sovereignty carve-out retains model, region, justification,
  approver and review-date evidence; destination identity and fail-closed
  comparisons support that obligation.
- Graceful degradation keeps simulation unavailable instead of silently
  consuming live capacity.
- Proven-call versus unknown-call evidence, append-only records and no
  historical backfill align with auditability.
- Mandatory What-If, reviewed plans, Bicep/Azure-native delivery and PR
  review remain applicable. Target evidence is not fabricated by this report.

## Findings

There are **zero FAIL items, four warnings and three observations**.

### F1 - Large tasks (optional splitting)

T012 combines CSV validation, resolution, isolation and diagnostics; T014
rewires adapters; T036 changes audit writing. Splitting coherent steps is
optional if execution becomes unwieldy. Same-file steps remain sequential;
do not exceed three tasks in any parallel group. The reviewer's suggested
approximately 200-line split heuristic is not a repository quality gate.

### F2 - Submission-evidence hook feasibility

The provenance contract requires request-bound outbound evidence.
At T036-T039, record in verification.md whether a supported hook proves
submission or the designed unknown/no-inference-row fallback applies.
Do not claim proven-call FR/SC acceptance without supporting evidence.
This is a designed execution risk, not permission to invent invocation rows.

### F3 - Reader projection file inventory

T034's affected replay/export readers are discovered by T003. Require that
explicit reader file inventory as input to T034/T035 and update affected
write sets before either starts, preserving parallel safety.

### F4 - Per-target parameter approval

T027 spans dev, staging and production parameter files. Record each
environment's G1 approval reference independently in verification.md before
editing that target. Missing approval blocks that target, not a partial pass
for the entire task.

## Observations

**O1 - T013 ordering:** The graph at tasks.md:234 orders T012, T013, T014.
T009-T011 already introduce failing new tests before T012, so the header's
test-first rule is satisfied. Moving legacy expectation changes in T013
before T012 and recording their red state is optional, not a correctness
blocker.

**O2 - Shared-file sequencing:** Keep these write paths sequential:

- foundry_chat_client.py: T008/T014/T037.
- MAF chat client: T015/T039.
- controller_service.py: T017/T040.
- dispatcher agent: T016/T041.
- sub_agent_invoker.py and _base.py: T035/T042.
- verification.md: T003/T004/T021/T030/T044/T048/T051.

**O3 - Proportionate task inventory:** 52 tasks across setup (4), foundation
(4), US1 (13), US2 (9), US3 (14), US4 (4) and polish (4) fit the cross-cutting
scope. Local procedure coverage remains distinct from actual migration
acceptance.

## Earlier provisional warning dispositions

| Earlier warning | Complete-review disposition |
| --- | --- |
| W1 - T013 after T012 | Substantiated but downgraded to low observation O1; new red tests precede implementation. |
| W2 - Large/open-ended tasks | Retained as optional splitting F1 and execution-readiness warnings F3/F4, not blockers. |
| W3 - H1 ownership | Designed gate, not a defect: T001/T002 can collect/review evidence; stop before T003 until H1 acceptance. |
| W4 - 80% coverage | Dismissed; no numeric threshold exists in the actual constitution. |
| W5 - Shared-file sequencing | Informational O2; declared parallel groups are disjoint. |

## Outstanding gates

- H0/H1: human implementation approval and owning-reviewer acceptance of
  CHK001-CHK036. All 36 routing-rollout items remain unchecked.
- G0: scoped evidence-collection authority.
- G1-G3: approved baselines, current governance and pinned AVM preservation
  compatibility; IaC remains gated.
- G4: stage-specific P1 release approval based on required What-If,
  carve-out, metadata, compatible revision and rollback evidence.
- G5a/G5b: optional proposal-based provisioning followed by actual
  replacement readiness and independently scoped traffic approval.
- G6: independent retirement approval.

No approved target baselines, freshness policy or operational authority is
supplied by this review. No model change, live validation, provisioning,
inference, traffic switch or retirement is authorised.

## Recommended actions

Obtain the human gate and actual H1 review. During execution, record the
submission-hook outcome, enumerate reader projections before T034/T035,
keep shared evidence files single-writer, and record per-target G1 evidence
before T027. Split tasks or reorder T013 only when useful; do not create
new quality gates from reviewer heuristics. Retain all target/operational
approval boundaries.

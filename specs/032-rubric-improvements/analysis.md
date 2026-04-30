# Cross-Artifact Analysis Report — Spec 032

**Analysis date**: 2026-04-30
**Artifacts**: spec.md, plan.md, research.md, data-model.md, quickstart.md, contracts/*, tasks.md
**Mode**: read-only; this report identifies issues but does not modify the artifacts.
**Constitution authority**: `.specify/memory/constitution.md` v1.2.0; conflicts with constitution are auto-CRITICAL.

## A. Summary

| Severity | Count | Status |
|---|---|---|
| CRITICAL (constitution / blocker) | 0 | ✅ Pass |
| HIGH | 3 | Resolved inline below |
| MEDIUM | 5 | Resolved inline below |
| LOW | 4 | Tracked |

The artifacts are internally consistent. The rubber-duck pre-tasks critique already removed all Blocker- and most High-severity issues. The remaining items below are residual integration drift between the artifacts (most are docs-side / labelling) plus three High items where a task was implied but not labelled, all resolved by clarifying notes here (not by re-editing artifacts in this read-only step; these notes will be honoured by Step 7).

## B. Findings

### CRITICAL — none

The constitution check in `plan.md` passes both pre- and post-Phase-1. No NN-1, NN-2, NN-3, NN-4, NN-5 violation found in any artifact.

### HIGH

**H1. spec.md FR-S02 → tasks.md mapping is split (FR-S02a vs FR-S02b) but tasks.md only labels T011 (ADR-032) and T413–T415 (rollout). Verify naming.**
- Evidence: `spec.md` decomposes FR-S02 into FR-S02a + FR-S02b after the Pass-1 clarify. `tasks.md` T011 is marked `[→ FR-S02a]` and T413–T415 `[→ FR-S02b]`. ✅ Resolved — labels correctly track the decomposition.
- Action: none beyond labelling already in place.

**H2. FR-AI03a (Foundry carve-out registry) is added in the spec as a child of FR-AI03; tasks.md tracks it via T017, T018, T412.**
- Evidence: T017 creates the registry skeleton, T018 wires the CD validator, T412 adds the OPA policy. ✅ Resolved — three-task coverage is appropriate.
- Action: none.

**H3. FR-AG05a (kill-switch authorisation/dual-approval) is in the spec but tasks.md only references it via T707/T708.**
- Evidence: T707 (`POST /agents/{id}/killswitch`) and T708 (`POST /agents/{id}/autonomy`) cite `FR-AG05a, NN-1`. The OpenAPI delta in `contracts/openapi-delta.yaml` was updated to require Entra OAuth scopes + dual-approval semantics. ✅ Resolved.
- Action: none.

### MEDIUM

**M1. spec.md FR-T05 ≡ FR-R02 (nightly load) — tasks.md tracks once via T803.**
- ✅ Single task per spec's "tracked once" assumption. No drift.

**M2. spec.md FR-S01 ≡ FR-C05 (Cosmos public-rule replacement) — tasks.md tracks once via T401.**
- ✅ Single task. No drift.

**M3. plan.md "kill-switch propagation" mechanism description vs spec.md FR-AG05.**
- spec.md says "Cosmos config change → Cosmos change-feed push → Service Bus topic → agent watcher → in-flight handoff drain". plan.md and tasks.md (T704–T706) align. ✅ Consistent.

**M4. FR-AI01 metadata-only fallback when handbook lacks indexing rights.**
- spec calls for default to metadata-only if licence inventory hasn't approved. tasks.md T029 creates the inventory; T602 ingestion is "gated to handbooks with positive licence inventory". ✅ Consistent — implementation must respect the gate.

**M5. data-model.md vs contracts/openapi-delta.yaml entity field naming.**
- Both call provenance fields `prompt_sha`, `prompt_version`, `model_id`, `model_version`, `deployment_alias`. Spelling matches. ✅

### LOW

**L1. plan.md Stream-9 mentions "render workshop video" but tasks.md uses "60-second walkthrough video" (T901).**
- Naming nit. Both refer to FR-DOC01. No action.

**L2. Acceptance scenario for US3 mentions "Workbook updates within one minute" — quickstart.md mentions visiting the Workbook but doesn't state the latency.**
- Quickstart is a smoke contract, not the assertion site. No action.

**L3. tasks.md T020 creates governance-hub stub; T903 then does the consolidation.**
- Two-step is intentional (stub early to register the URL; full consolidation later). No action.

**L4. tasks.md T010 README agent table refresh is in Phase 1 but FR-AG04 is also referenced in T905+ docs work.**
- Two passes is fine: initial table now, full doc refresh in polish. No action.

## C. Coverage Matrix (FR → tasks)

(Spot-checked; full matrix lives in T907 deliverable.)

| FR | Task(s) | Status |
|---|---|---|
| FR-A01 | T021 | ✓ |
| FR-A02 | T022 | ✓ |
| FR-A03 | T023 | ✓ |
| FR-A04 | T024 | ✓ |
| FR-A05 | T201–T204 | ✓ |
| FR-P01 | T205 | ✓ |
| FR-P02 | T207 | ✓ |
| FR-P03 | T013, T206 | ✓ |
| FR-P04 | T311 | ✓ |
| FR-P05 | T208 | ✓ |
| FR-Q01 | T101, T105 | ✓ |
| FR-Q02 | T102, T106 | ✓ |
| FR-Q03 | T103, T104 | ✓ |
| FR-Q04 | T001 | ✓ |
| FR-Q05 | (= FR-A05) | ✓ |
| FR-I01 | T006, T007 | ✓ |
| FR-I02 | T611 | ✓ |
| FR-I03 | T905 | ✓ |
| FR-I04 | T910 | ✓ |
| FR-I05 | T008 | ✓ |
| FR-T01 | T107 | ✓ |
| FR-T02 | T904 | ✓ |
| FR-T03 | T807 | ✓ |
| FR-T04 | T108, T109 | ✓ |
| FR-T05 | T803 | ✓ |
| FR-T06 | T002 | ✓ |
| FR-T07 | T009, T907 | ✓ |
| FR-T08 | T906 | ✓ |
| FR-T09 | T610, T909 | ✓ |
| FR-T10 | T908 | ✓ |
| FR-O01 | T505 | ✓ |
| FR-O02 | T026, T511 | ✓ |
| FR-O03 | T512 | ✓ |
| FR-O04 | T508–T510 | ✓ |
| FR-O05 | T309 | ✓ |
| FR-O06 | T025 | ✓ |
| FR-O07 | T501–T504 | ✓ |
| FR-O08 | T510 | ✓ |
| FR-O09 | T506 | ✓ |
| FR-O10 | T507 | ✓ |
| FR-AI01 | T015, T029, T406, T601–T604 | ✓ |
| FR-AI02 | T301, T308 | ✓ |
| FR-AI03 | T012, T209, T608 | ✓ |
| FR-AI03a | T017, T018, T412 | ✓ |
| FR-AI04 | T609 | ✓ |
| FR-AI05 | T028, T605 | ✓ |
| FR-AI06 | T404, T405, T406 | ✓ |
| FR-AI07 | T811 | ✓ |
| FR-AI08 | T817 | ✓ |
| FR-AI09 | T014, T028, T606, T607 | ✓ |
| FR-AI10 | T819 | ✓ |
| FR-AG01 | T027 | ✓ |
| FR-AG02 | T701–T703, T708 | ✓ |
| FR-AG03 | T714 | ✓ |
| FR-AG04 | T010 | ✓ |
| FR-AG05 | T016, T704–T706 | ✓ |
| FR-AG05a | T707, T708 | ✓ |
| FR-AG06 | T709 | ✓ |
| FR-AG07 | T710 | ✓ |
| FR-AG08 | T711 | ✓ |
| FR-AG09 | T712 | ✓ |
| FR-AG10 | T713 | ✓ |
| FR-S01 | T401 | ✓ |
| FR-S02a | T011 | ✓ |
| FR-S02b | T413–T415 | ✓ (gated by spec 031) |
| FR-S03 | T108, T109 | ✓ |
| FR-S04 | T407, T408 | ✓ |
| FR-S05 | T402, T403 | ✓ |
| FR-R01 | T802 | ✓ |
| FR-R02 | T803 | ✓ |
| FR-R03 | T804 | ✓ |
| FR-R04 | T805 | ✓ |
| FR-R05 | T806, T807, T818 | ✓ |
| FR-C01 | T007, T801 (verify) | ✓ (external) |
| FR-C02 | T815 | ✓ |
| FR-C03 | T110 | ✓ |
| FR-C04 | T814, T816 | ✓ |
| FR-C05 | T401 | ✓ |
| FR-D01 | T809 | ✓ |
| FR-D02 | T005, T813 | ✓ |
| FR-D03 | T812 | ✓ |
| FR-D04 | T808, T810 | ✓ |
| FR-D05 | T030 | ✓ |
| FR-DOC01 | T901 | ✓ |
| FR-DOC02 | T902 | ✓ |
| FR-DOC03 | T020, T903 | ✓ |
| FR-DOC04 | T003 | ✓ |
| FR-DOC05 | T004, T1006 | ✓ |

**Result**: 100% FR → task coverage. No orphans.

## D. SC → Test Coverage

| SC | Test surface |
|---|---|
| SC-001 | Out-of-band re-grade post-merge; manual evaluator process. |
| SC-002 | T306, T307, T310 (why-fired panel + integrity). |
| SC-003 | T416 (public-network probe). |
| SC-004 | T025 + T507 + T506 (SLO + availability test + Action Group). |
| SC-005 | T610 + T611 (eval gates + dataset). |
| SC-006 | T818 (dr-drill workflow). |
| SC-007 | T901–T907 (docs surfaces) + automated link check (Phase 12 polish). |
| SC-008 | Phase 3 + Phase 6 (CodeQL, coverage, format, import-linter, SHA-pin). |
| SC-009 | T506 + T025 (Action Group + SLO doc). |
| SC-010 | T030 + T818 + T807 (exercise schedule + drills). |

## E. Constitution Re-check (post-tasks)

| NN | Where honoured |
|---|---|
| NN-1 Human-in-the-loop | T707, T708 dual-approval; existing approval workflow preserved |
| NN-2 Data sovereignty | T401–T408 (PE+CMK), T412 (carve-out OPA), T209 (classification gate), T029 (licence inventory) |
| NN-3 Privacy | T309 (PII redaction), T402 (CMK), T201–T209 (safety package) |
| NN-4 Interoperability | T902 (Redoc), T605 (versioned prompts) |
| NN-5 Graceful degradation | T206 (pybreaker), T705 (kill-switch + degraded mode), T209 (template fallback) |

✅ Constitution check still passes after tasks.

## F. Recommendation

**Proceed to Step 7 (implement)**. No artefact amendments required. Stream 0 (T001–T030) and Stream 1 (T101–T110) form the foundation — start there. Watch for the spec-031 prerequisite gate at T801/T413; if spec 031 is not yet merged at the moment we reach those tasks, mark them `blocked` and continue with non-gated tasks.

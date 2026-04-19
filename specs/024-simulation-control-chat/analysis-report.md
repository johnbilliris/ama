# Analysis Report: Simulation Control & Chat Orchestration

**Phase**: 6 (speckit.analyze) · **Date**: 2026-04-19

## Coverage matrix (FR → tasks)

| FR | Tasks |
|---|---|
| FR-001 | T040, T061 |
| FR-002 | T002, T040 |
| FR-003 | T040 |
| FR-004 | T042 |
| FR-005 | T030 |
| FR-006 | T031, T033 |
| FR-007 | T004, T033 |
| FR-008 | T030, T034 |
| FR-009 | T034, T063 |
| FR-010 | T030, T035 |
| FR-011 | T033, T062 |
| FR-012 | T032 |
| FR-013 | T004, T033 |
| FR-014 | T033 |
| FR-015..018 | T070–T073 |
| FR-019 | T010, T012 |
| FR-020 | T011 |
| FR-021 | T010, T013, T014 |
| FR-022 | T062, T066 |
| FR-023 | T090 |
| FR-024 | plan region-pin; T091 alerts |
| FR-025 | T051, T073 |
| FR-026 | T020, T033 |
| FR-027 | T084, T093 |
| FR-028 | T085 |
| FR-029 | T072 |
| FR-030 | **T088 (added after analysis)** |
| FR-031 | T003 |
| FR-032 | T021 |
| FR-033 | T062 |
| FR-034 | T033, **T087 (added after analysis)** |
| FR-035 | T040, T051 |
| FR-036 | T041 |
| FR-037 | T030, T033 |
| FR-038 | T020 |
| FR-039 | T084, **T093 (added after analysis)** |
| FR-040 | T042, T064 |

**Result**: 100 % FR coverage after gap-fill tasks T087, T088, T093.

## Consistency issues found & resolved

| # | Finding | Resolution |
|---|---|---|
| A1 | FR-030 printable chat had no implementing task | Added T088 transcript export |
| A2 | FR-034 OpenAI-down degradation lacked frontend work | Added T087 frontend degradation |
| A3 | FR-027 / FR-039 CI cadence not explicitly wired | Added T093 CI pipeline jobs |
| A4 | `draft` / `ended` statuses extend spec 007 enum — potential migration risk | Plan T002 covers validators; data-model.md documents the extension explicitly |
| A5 | Plan references `PlanningService` which may not exist by that name | T032 already notes "fallback to existing equivalents" — acceptable |

## Outstanding risks

- Jailbreak suite fidelity depends on curation quality. T084 includes curated categories (roleplay-to-real, prompt-exfiltration, tool-fabrication, PII-extraction, policy-rewriting).
- Cosmos DB cross-container queries may need composite indexes; T004 must profile.

**Verdict**: Analysis complete. Ready to proceed to `/speckit.implement`.

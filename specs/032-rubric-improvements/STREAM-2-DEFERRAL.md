# Stream 2 — `apps/agents/common/` Refactor (Deferred to Follow-Up PR)

**Tasks**: T201–T209 from `tasks.md`.
**Status**: Deferred to a follow-up PR series.

## Why deferred

Stream 2 moves 18 modules from a flat `apps/agents/common/` into three sub-packages (`resilience/`, `safety/`, `lifecycle/`) and introduces several behavioural changes:
- Strategy pattern extraction (FR-P01)
- pybreaker swap (FR-P03)
- Externalised budget tracker (FR-P02)
- Typed AIIMS registry (FR-P05)
- Classification-aware sensitive-content filter (FR-AI03)

Each of these touches the agent runtime hot-path and risks regressing the existing pytest suite (2,255 tests per stored memories). Bundling them with the foundation + planning + Stream 1 + Stream 4-Bicep PR would make review impractical and increase the chance of a blast-radius incident on review or merge.

## Recommended PR sequence (follow-up sessions)

| PR | Tasks | Tests to gate |
|---|---|---|
| `032/stream-2a — common refactor (move only)` | T201–T204 | Full unit + integration; assert no test moves required (via re-export shims) |
| `032/stream-2b — Strategy + pybreaker` | T205, T206 | + benchmark on monitoring/risk-assessment paths |
| `032/stream-2c — externalise budget tracker` | T207 | + Cosmos integration test for `llm_budgets` container |
| `032/stream-2d — typed AIIMS registry` | T208 | + unit tests for jurisdiction overrides |
| `032/stream-2e — classification-aware filter` | T209 | + unit tests for PII/PSPF/sensitive-ops detection; gates Stream 6 Phi shadow |

Each PR should be small enough (~5 files) for thorough review.

## Cross-stream impact

Stream 2 is a precondition for:
- Stream 3 (audit + integrity) — uses `safety.redaction` module after refactor
- Stream 4 (Foundry carve-out gate) — depends on `safety/classification.py` (T209)
- Stream 6 (Phi shadow) — depends on T209 + T207 + T205
- Stream 7 (kill-switch + autonomy) — uses `lifecycle/` sub-package

The streams above can lay groundwork (Bicep, ADRs, contracts) that does NOT depend on the refactor. Spec-032 has been organised so this delay does not block the foundation work shipped in this PR.

# Field connectivity loss during evacuation

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-008` |
| Category | Operational |
| Likelihood × Consequence | 3 × 4 = 12 (inherent) |
| Residual L × C | 2 × 3 = 6 |
| Treatment | spec-036 FR-RAG-LS-02 offline-cache manifest; conservative life-safety default; local audit log replays on reconnect (spec-027). |
| Owner | Field Coordinator |
| Next review | 2026-08-11 |

## Description

Field Coordinator without connectivity makes locally-cached decisions that may diverge from HQ.

## Back-citations

- `specs/036-foundry-rag-grounding/spec.md` (spec)
- `.github/agents/operational/field-coordinator.agent.md` (agent_md)

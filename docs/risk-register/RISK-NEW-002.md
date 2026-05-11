# Cosmos partition hotspot under cross-jurisdiction surge

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-002` |
| Category | Platform |
| Likelihood × Consequence | 2 × 4 = 8 (inherent) |
| Residual L × C | 1 × 3 = 3 |
| Treatment | Partitioning math documented in docs/architecture/cosmos-partitioning.md; autoscale 1000 RU/s; capacity model in docs/governance-hub/architecture/capacity-model.md. |
| Owner | Data Engineer |
| Next review | 2026-08-11 |

## Description

A multi-jurisdiction incident may concentrate writes on a single partition (audit-timeline /tenant_id).

## Back-citations

- `docs/governance-hub/architecture/cosmos-partitioning.md` (governance_hub)
- `.github/agents/technical/data-engineer.agent.md` (agent_md)

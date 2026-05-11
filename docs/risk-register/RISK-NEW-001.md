# Container Apps revision saturation

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-001` |
| Category | Platform |
| Likelihood × Consequence | 3 × 4 = 12 (inherent) |
| Residual L × C | 2 × 3 = 6 |
| Treatment | HPA tuned in infra/main.bicep; load tests in tests/load/; KEDA scale-to-zero rejected for hot-path. |
| Owner | Infrastructure/DevOps Lead |
| Next review | 2026-08-11 |

## Description

Concurrent disaster activations could exceed Container Apps autoscale ceiling.

## Back-citations

- `specs/032-rubric-improvements/spec.md` (spec)
- `.github/agents/technical/sre-engineer.agent.md` (agent_md)

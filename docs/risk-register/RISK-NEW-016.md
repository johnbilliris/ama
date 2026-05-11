# Container image dependency CVE

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-016` |
| Category | Supply-chain |
| Likelihood × Consequence | 3 × 4 = 12 (inherent) |
| Residual L × C | 2 × 3 = 6 |
| Treatment | Cosign keyless signing (spec-032 FR-AI09); CodeQL + security-scan workflows; Defender for Cloud alerts; SBOM generated at build. |
| Owner | Security Engineer |
| Next review | 2026-06-11 |

## Description

Critical CVE in a transitive dependency of the api/agents container images.

## Back-citations

- `specs/032-rubric-improvements/spec.md` (spec)
- `.github/agents/technical/security-engineer.agent.md` (agent_md)

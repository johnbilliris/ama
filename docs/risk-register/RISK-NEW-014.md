# PII leakage in audit log payloads

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-014` |
| Category | Data |
| Likelihood × Consequence | 2 × 5 = 10 (inherent) |
| Residual L × C | 1 × 4 = 4 |
| Treatment | Presidio anonymizer in spec-030 + spec-032 PII guards; integration test in tests/integration/spec_037/test_publish_pipeline.py asserts no email/phone patterns. |
| Owner | Compliance Auditor |
| Next review | 2026-06-11 |

## Description

Audit-writer could inadvertently persist PII (NN-2 violation).

## Back-citations

- `specs/032-rubric-improvements/spec.md` (spec)
- `.github/agents/technical/security-engineer.agent.md` (agent_md)

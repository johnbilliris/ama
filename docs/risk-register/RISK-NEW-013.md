# Signal envelope schema drift breaks ingest contract

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-013` |
| Category | Data |
| Likelihood × Consequence | 2 × 4 = 8 (inherent) |
| Residual L × C | 1 × 3 = 3 |
| Treatment | Contract test in tests/contract/spec_006/; signal-envelope.schema.v2.json with backwards-compat layer; spec-005 data-source governance. |
| Owner | Data Engineer |
| Next review | 2026-08-11 |

## Description

Unversioned changes to signal-envelope schema would break downstream consumers.

## Back-citations

- `specs/006-data-ingestion-storage/spec.md` (spec)
- `specs/005-data-source-governance/spec.md` (spec)

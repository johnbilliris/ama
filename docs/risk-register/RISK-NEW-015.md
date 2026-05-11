# Corpus snapshot drift in Foundry RAG retrievals

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-015` |
| Category | Data |
| Likelihood × Consequence | 2 × 3 = 6 (inherent) |
| Residual L × C | 1 × 2 = 2 |
| Treatment | spec-036 FR-RAG-G3 corpus-build-sha tagging; staleness_alert.schema.json; quarterly corpus refresh cadence. |
| Owner | Data Engineer |
| Next review | 2026-08-11 |

## Description

Mismatched corpus_build_sha between ingest snapshot and live index returns stale citations.

## Back-citations

- `specs/036-foundry-rag-grounding/spec.md` (spec)

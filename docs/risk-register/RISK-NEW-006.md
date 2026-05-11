# Confidence-threshold drift in Risk Assessment Agent

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-006` |
| Category | AI |
| Likelihood × Consequence | 2 × 4 = 8 (inherent) |
| Residual L × C | 1 × 3 = 3 |
| Treatment | Quarterly re-calibration via spec-030 LLM-eval framework; canary deployment with confidence histogram diff; spec-012 FR-024 explicit confidence band. |
| Owner | AI/ML Engineer |
| Next review | 2026-08-11 |

## Description

Model retraining changes the confidence-distribution; existing 0.7 threshold may be miscalibrated.

## Back-citations

- `specs/012-risk-assessment-agent/spec.md` (spec)
- `specs/030-llm-eval-framework/spec.md` (spec)

# LLM hallucination in Communication Agent public alerts

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-004` |
| Category | AI |
| Likelihood × Consequence | 3 × 5 = 15 (inherent) |
| Residual L × C | 1 × 4 = 4 |
| Treatment | spec-008 FR-072 NN-1 mandatory PIO approval; spec-030 grounding-faithfulness eval gate; misinformation watchlist. |
| Owner | Public Information Officer |
| Next review | 2026-06-11 |

## Description

A grounded but hallucinated alert text could be approved if the human-in-the-loop fails.

## Back-citations

- `specs/008-communication-agent/spec.md` (spec)
- `specs/030-llm-eval-framework/spec.md` (spec)

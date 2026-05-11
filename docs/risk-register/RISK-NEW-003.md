# Foundry RAG carve-out endpoint unavailability

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-003` |
| Category | Platform |
| Likelihood × Consequence | 2 × 3 = 6 (inherent) |
| Residual L × C | 1 × 3 = 3 |
| Treatment | Fallback to non-RAG path with explicit `rag_used:false` flag; spec-036 FR-RAG-LS-02 offline-cache bundles for Field Coordinator; chaos drill quarterly. |
| Owner | Solution Architect |
| Next review | 2026-08-11 |

## Description

Foundry inference endpoint outage breaks RAG-grounded sub-agent responses.

## Back-citations

- `specs/036-foundry-rag-grounding/spec.md` (spec)
- `infra/parameters/foundry-carveout.yaml` (governance_hub)
- `docs/aidr/decisions/adr-033-phi-shadow-boundary.md` (adr)

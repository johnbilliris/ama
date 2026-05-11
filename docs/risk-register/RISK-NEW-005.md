# Sim-agent idempotency replay under simulated disaster load

| Field | Value |
|-------|-------|
| Risk ID | `RISK-NEW-005` |
| Category | AI |
| Likelihood × Consequence | 2 × 3 = 6 (inherent) |
| Residual L × C | 1 × 2 = 2 |
| Treatment | spec-036 ADR-036-009 idempotency-cache design (24h TTL); production-grade idempotency on /inject-telemetry per spec-036-sim-agent-extend FR-066; integration test in tests/integration/spec_036/. |
| Owner | AI/ML Engineer |
| Next review | 2026-08-11 |

## Description

spec-036-sim-agent-extend telemetry-injection agent could double-fire under retries if idempotency cache fails.

## Back-citations

- `specs/036-sim-agent-extend/spec.md` (spec)
- `docs/aidr/decisions/ADR-036-009-idempotency-cache-design.md` (adr)

# ADR-036-004: APIM Token-Bucket + In-Process Circuit Breaker for Telemetry Injection

**Status**: Accepted
**Deciders**: SRE, Network Engineer, AI Engineer
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-014, FR-016, FR-017
**Plan trade-off**: #4

## Context

Telemetry-injection prompts pass through Azure OpenAI (Foundry) for
strict-JSON-schema parsing (FR-014) — a finite, expensive resource. Two
failure modes need bounding:

1. **Burst attempts** — a malformed coordinator prompt that retries
   tens of times per second drains TPM and risks `429 Too Many
   Requests` from Foundry.
2. **Sustained low-confidence parses** — an LLM that consistently
   returns garbled JSON should be circuit-broken so the deterministic
   regex fallback (FR-016) can take over before the budget is gone.

## Decision

Adopt the **two-layer rate-limit / circuit-breaker** pattern outlined
by the SRE + Network Engineer cohort canvass (`cohort-tech-qsoi.md
§2.3`):

### Layer 1 — APIM token-bucket policy (per-user)

`infra/bicep/modules/apim-policy-simulation-inject.bicep` defines an
APIM rate-limit policy:

- **60 attempts / minute** per user (sliding window).
- **10-attempt burst** allowance (token bucket).
- **60-second cooldown** when the bucket is empty.

The policy returns `429` with a `Retry-After` header. The route
surfaces this as `injection.circuit_open` audit envelope per
`audit-envelope.md §3.4`.

### Layer 2 — In-process circuit breaker (per-simulation)

`apps/api/app/services/simulation/parse_attempt_circuit_breaker.py`
implements a **success-only counted token-bucket** keyed on
`simulation_id`. The state machine:

```
CLOSED  -- 60 successive parse failures within 60 s -->  OPEN
OPEN    -- 60 s elapsed -->                              HALF_OPEN
HALF_OPEN -- next attempt succeeds -->                   CLOSED
HALF_OPEN -- next attempt fails -->                      OPEN
```

Successes are counted via `rate_limiter.record_success()`; failures
**do NOT** decrement the bucket — this is critical because a hostile
prompt that intentionally fails MUST NOT be allowed to hold the bucket
open. See `tests/integration/test_parse_attempt_circuit_breaker.py`.

When the breaker is OPEN, the route falls through to the deterministic
regex fallback (`fallback_extractor.py`) per FR-016, and tags the
resulting `SyntheticSignal` with `confidence='low'` + `provenance`
indicating the fallback path.

## Consequences

- The 60/min ceiling is intentionally low; ops can tune it via APIM
  policy fragment without re-deploying the application. The breaker's
  60-second cooldown is configurable but **must** stay ≤ the APIM
  policy window so user-perceived behaviour is consistent.
- The breaker is **per-simulation**, not per-user — a single hostile
  user cannot starve other simulations within the same tenant.
- The cohort canvass also evaluated Redis-backed sliding windows and a
  Polly-style state machine; both were rejected for added latency or
  insufficient observability.

## Alternatives considered

- **APIM-only** (no in-process breaker) — rejected: cannot bias toward
  the FR-016 regex fallback; APIM has no concept of LLM success rate.
- **Polly state machine** — rejected: not idiomatic in Python; would
  require a third-party port.
- **Counting failures rather than successes** — rejected per spec
  decision: hostile prompts MUST NOT keep the breaker closed.

## Linked artefacts

- `apps/api/app/services/simulation/parse_attempt_circuit_breaker.py`
- `apps/api/app/services/simulation/rate_limiter.py`
- `infra/bicep/modules/apim-policy-simulation-inject.bicep`
- `apps/agents/simulation_telemetry_injection/fallback_extractor.py`

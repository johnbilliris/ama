# ADR-034: Adopt `pybreaker` for Circuit-Breaker Resilience

## Status

Proposed (target: Accepted upon merge of spec-032 Stream-2 task T206).

## Context

The current circuit breaker implementation lives in `apps/agents/common/circuit_breaker.py` as a hand-rolled class. The AMA Rubric Evaluation flagged this as technical debt under "Use of Design Patterns" item 2.3:

> Replace the hand-rolled circuit breaker with a battle-tested library (e.g. pybreaker or tenacity + half-open) and document the choice in an ADR.

The hand-rolled implementation lacks:
- A formal **half-open** state with a configurable trial-call budget.
- State-change listeners (the new `circuitbreaker.state` customMetric — FR-O02 — needs these).
- Test coverage for race conditions under concurrent load.
- A canonical `excluded_exceptions` model.

## Decision

Adopt **`pybreaker`** (PyPI: `pybreaker`, repo: `danielfm/pybreaker`) and wrap it behind the existing `apps.agents.common.resilience.CircuitBreaker` Protocol so that all current call-sites continue to work unchanged.

The migration:
1. Add `pybreaker>=1.2.0` to the agents app dependency.
2. Implement `apps/agents/common/resilience/circuit_breaker.py` as a thin adapter exposing the existing methods (`call()`, `record_success()`, `record_failure()`, `state`).
3. Subscribe a state-change listener that emits `circuitbreaker.state` (gauge) + `circuitbreaker.transitions_total` (counter) customMetrics to App Insights.
4. Migrate one call-site at a time; remove the hand-rolled class once all sites are switched.

## Consequences

### Positive

- Battle-tested half-open state machine; no homegrown race conditions.
- Built-in state-change listener hook satisfies FR-O02 customMetric needs.
- Maintained library; security patches inherited.
- Smaller surface area to audit (~400 LoC of pybreaker vs the hand-rolled implementation + tests).

### Negative / accepted

- One new transitive dependency. Mitigated: `pybreaker` is pure Python with no native deps; vendored licence (MIT).
- Requires migration; tracked as a single Stream-2 task (T206).

### Alternatives considered

- **`tenacity`** — retry-only library, no half-open state; rejected.
- **`aiobreaker`** — async-only, niche, unmaintained; rejected.
- **Continue rolling our own** — explicitly called out as debt by the rubric; rejected.

## Compliance

- **NN-5 (Graceful degradation)**: improved — half-open state with budget gives bounded recovery probing rather than fail-open after timeout.
- All other Non-Negotiables unaffected.

## References

- pybreaker: <https://github.com/danielfm/pybreaker>
- AMA Rubric — Use of Design Patterns item 2.3.
- Spec 032 FR-P03.

---
*Author: API Architect + SRE Engineer personas via spec-032 Stream-0. Date: 2026-04-30.*

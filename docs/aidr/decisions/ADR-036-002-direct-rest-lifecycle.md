# ADR-036-002: Direct-REST Lifecycle Verbs (abort/pause/resume) Bypass the Agent Loop

**Status**: Accepted
**Deciders**: Solution Architect, Security Architect, SRE
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-059
**Constitution**: Primacy of Life (NN-1), HITL Unconditional (NN-3)

## Context

Pre-spec-036 the simulation realm exposed `pause`, `resume`, and `stop`
as **agent tools** — the LLM controller could invoke them via the
tool-loop. This created two operational risks:

1. **Cancellation latency** — the LLM tool-loop adds 5–30 s of
   thinking-and-emit delay before the cancellation propagates. For an
   abort that needs to honour Primacy of Life (NN-1), even seconds
   matter.
2. **Auditability** — agent-loop tool calls are interleaved with
   model reasoning; an abort that fires mid-cascade leaves a
   non-deterministic audit ordering.

## Decision

Implement **direct-REST endpoints** in
`apps/api/app/api/routes/simulations_036.py` for the three lifecycle
verbs:

```text
POST /api/simulations/{simId}/abort   → 200 AbortResponse
POST /api/simulations/{simId}/pause   → 200 LifecycleAck
POST /api/simulations/{simId}/resume  → 200 LifecycleAck
```

The endpoints **bypass the LLM tool-loop entirely**. Specifically:

- `abort` calls
  `apps.api.app.services.simulation.cancellation.cancel_all()` which
  walks the per-simulation in-flight task registry and cancels every
  registered `asyncio.Task` within ~1 s. Each cancelled invocation
  emits exactly one `sub_agent.cancel` audit envelope (per
  `audit-envelope.md §3.17`), and the lifecycle endpoint emits one
  `lifecycle.aborted` envelope summarising the count.
- `pause` does **NOT** cancel in-flight invocations — they run to
  completion and their replies are written under the paused state.
  Resume does **NOT** replay them.

The corresponding `pause_simulation` / `resume_simulation` agent tools
(in `controller_tools.py:TOOL_SCHEMAS`) are **kept** for ergonomic
agent-driven flows, but `abort_simulation` is **explicitly NOT a tool**
— per FR-059 the abort verb must always be operator-initiated.

## Consequences

- The cancellation scope (`apps/api/app/services/simulation/
  cancellation.py`) is process-local; production wiring expects a
  Redis-backed registry when scaled across container apps.
- The abort endpoint sets `lifecycle.aborted.cancelled_invocations`
  byte-equal to the count produced by `cancel_all`. The chaos test
  harness in `tests/integration/test_cancellation_scope.py` validates
  this invariant for fan-outs of up to 50 in-flight invocations.
- HITL Unconditional (NN-3) is preserved: the abort endpoint is
  served behind the existing AAD `Simulation.Coordinator` role, never
  open to the public.

## Alternatives considered

- **Tool + post-tool middleware that bypasses the loop** — rejected:
  the cancellation path needs to emit the `sub_agent.cancel` audit
  envelope **before** the tool-loop returns; middleware ordering is
  fragile.
- **Sentinel signal (`abort=true`) injected into the agent state** —
  rejected: requires the LLM to honour the signal, which violates
  Primacy of Life when the model is unhealthy.

## Linked artefacts

- `apps/api/app/api/routes/simulations_036.py`
- `apps/api/app/services/simulation/cancellation.py`
- `apps/api/app/services/simulation/controller_tools.py`
- `apps/api/tests/test_lifecycle_endpoints.py`

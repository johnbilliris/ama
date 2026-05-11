# ADR-036-001: Real Sub-Agent Invocation Replaces Stub Adapters

**Status**: Accepted
**Deciders**: Solution Architect, AI Architect, Backend Engineer
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-002, FR-003, FR-007, FR-060

## Context

Pre-spec-036 the simulation realm called every sub-agent (planning,
monitoring, risk-assessment, communication, evacuation,
resource-allocation) through stub adapters in
`apps/api/app/services/simulation/sub_agent_invoker.py:67-101` that
returned the literal string `"simulated reply (no data source wired in
this environment)."`. The stubs satisfied the routing surface but
prevented real telemetry-injection scenarios from exercising the
controller↔sub-agent loop.

## Decision

Replace the six stub adapters with **real production adapters** that:

1. Call each sub-agent's HTTP endpoint via `httpx.AsyncClient`
   (async, connection-pooled, deadline-aware). Per the
   backend-engineer + sre-engineer cohort canvass: `httpx` was selected
   over `aiohttp` for its first-class typing, deterministic timeouts,
   and HTTP/2 support — see `cohort-tech-qsoi.md §3.7`.
2. Compute a deterministic SHA-256 prompt hash via
   `apps/agents/common/llm_mixin.compute_prompt_hash()` so audit replay
   can verify byte-determinism (FR-060).
3. Soft-ack at T+5 s and hard-timeout at T+120 s (FR-003) — emitted as
   typed SSE events `sub_agent.started`, `ack.working`,
   `sub_agent.completed`, `sub_agent.degraded`.
4. Produce `SubAgentReply` records carrying `prompt_hash`,
   `model_deployment`, and `sub_agent_invocation_id` (FR-060).

The `select_invoker()` factory accepts either:
- `default_invoker` — keeps the stub literal in non-staging environments
  so the **FR-002 trip-wire** (`"simulated reply (no data source wired
  in this environment)."`) survives until the staging flag flips; or
- `production_invoker(http_client)` — the real adapter set, gated by
  `SIM_CONTROLLER_MODE=production`.

## Consequences

- The `simulation-stub-sweep` CI step (`tools/simulation_stub_sweep.py`)
  greps for the trip-wire string; once `SIM_CONTROLLER_MODE=production`
  lands, the sweep flips to **enforcement mode** and fails the build
  if the literal reappears.
- A citation-filter (`apps/api/app/services/simulation/sub_agents/
  citation_filter.py`) inspects every adapter reply and strips
  references to live-tenant resources (FR-007 / Constitution Audit-and-
  Provenance), emitting `tenant_isolation.violation` on breach.
- The previous tenant-pause/resume verbs in `simulations.py` remain
  untouched; the new direct-REST surface lives in
  `simulations_036.py` with the `sim_id` UUID slug.

## Alternatives considered

- **Keep stubs and add a parallel "live adapters" router** —
  rejected: doubles maintenance, splits audit lineage, hides the trip-
  wire and prevents byte-deterministic FR-060 hashing.
- **Use `aiohttp` instead of `httpx`** — rejected per cohort canvass
  (typing churn, no HTTP/2, less ergonomic mock-transport for tests).

## Linked artefacts

- `apps/api/app/services/simulation/sub_agent_invoker.py`
- `apps/api/app/services/simulation/sub_agents/`
- `tools/simulation_stub_sweep.py`
- `.github/workflows/simulation-stub-sweep.yml`

# ADR 06 — RAG Opt-Out: Resilience Planner / Simulation Scenario Execution

**FR**: FR-RAG-NS-06; FR-RAG-SIM-06
**Persona memo citation**: `personas-input/sectors-crosssector.md` §"Tabletop scenarios must be deterministic"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

## Context

The Simulation Controller serves two modes: a **decision-support** mode (operators driving real incidents through scenario walk-throughs) and a **scripted-scenario / offline** mode (tabletop exercises with pre-baked timelines).

In the scripted mode:

* the timeline is pre-baked (turn N+1 follows turn N by construction),
* operators rehearse against a **deterministic** state machine,
* the LLM only emits canned, intent-routed responses (e.g., "advance the clock", "show the next event card").

A grounded retrieval on a scripted turn:

1. defeats the determinism that makes tabletop exercises reproducible,
2. risks the LLM substituting corpus content for the scripted card (a content-injection bug pattern),
3. doubles latency on every clock-tick.

The same logic applies to the Resilience Planner agent's scenario-replay paths — they replay an existing decision rather than make a new one.

## Decision

The Simulation Controller's `_stream_offline` path and the Resilience Planner's scenario-replay paths emit LLM `AuditRecord`s with `rag_used=false` and `rag_optout_reason="scenario-execution"`. The **decision-support** path (real incidents through the same Controller) remains fully grounded.

## Audit-log shape

```json
{
  "agent_name": "SimulationController",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "scenario-execution",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/06-rag-optout-scenario-execution.md"
}
```

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-06]: Scripted-scenario / offline execution path — no LLM-driven decision; canned responses by intent.
```

Applied at the offline-streaming entry in `apps/api/app/services/simulation/controller_service.py::_stream_offline`.

## Consequences

* **Preserves**: tabletop determinism, latency floor on clock ticks, replay reproducibility for scripted exercises.
* **Precludes**: in-scenario doctrine grounding. (Operators wanting to consult doctrine *during* a scripted exercise switch to decision-support mode.)
* **Quality gate**: a decision-support call mis-routed into the scripted path would surface as `rag_used=false` on a turn that should have grounded — the parity-tests review (Phase C T098) catches this regression.

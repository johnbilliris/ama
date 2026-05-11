# ADR 02 — RAG Opt-Out: Monitoring Agent BoM Live-Feed Path

**FR**: FR-RAG-NS-02
**Persona memo citation**: `personas-input/sectors-eastern.md` §"BoM warning ingestion must reflect live state"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

## Context

The Monitoring agent ingests live data from the Bureau of Meteorology (BoM) — severe weather warnings, riverine flood gauges, fire-danger ratings — over the BoM's published feeds. These signals are:

* time-critical (warnings stale within minutes),
* **already authoritative** (BoM is the single national source of truth for the data they emit),
* **not** corpus content — the corpus indexes BoM's *doctrine* (warning thresholds, escalation playbooks), not the live signal stream.

Issuing a corpus retrieval call against the live signal would:

1. add latency (≥ 50 ms p50 over the corpus index) without information gain,
2. risk shadowing a fresh signal with a cached chunk from a stale corpus build,
3. emit a hallucinated citation if the LLM tries to "explain" the live signal using the doctrine corpus.

## Decision

When the Monitoring agent processes a **live BoM feed event**, RAG is **not** invoked. The signal is parsed, normalised, and routed to the indicator-analysis pipeline directly. Any LLM call on this path uses `_generate_with_fallback` with `rag_used=false` and an explicit `rag_optout_reason="bom-live-feed"`.

Doctrine grounding still applies to the **escalation decision** that follows ingestion (e.g., when the indicator-analysis pipeline asks "what protocol matches a class-4 BoM cyclone warning?") — that downstream LLM call carries `rag_used=true` and cites the relevant handbook.

## Audit-log shape

```json
{
  "agent_name": "MonitoringAgent",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "bom-live-feed",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/02-rag-optout-bom-live.md",
  "model_id": "gpt-4o-mini"
}
```

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-02]: BoM live-feed signal is the source of truth; doctrine grounding lives on the downstream escalation call.
```

Applied at the live-feed entry point in `apps/agents/monitoring/pipeline.py`.

## Consequences

* **Preserves**: signal freshness (no corpus-induced latency), zero hallucinated-citation risk on live events.
* **Precludes**: post-hoc grounded justification on the *ingestion* event itself. (Operators inspecting "why did Monitoring escalate?" see the cited doctrine on the escalation record — not on the ingestion record.)
* **Replay invariant**: BoM events are reproducible from the BoM feed archive (independent of corpus build), so SC-011 audit replay still holds.

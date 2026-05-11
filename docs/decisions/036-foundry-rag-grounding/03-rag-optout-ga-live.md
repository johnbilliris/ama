# ADR 03 — RAG Opt-Out: Risk Assessment Agent GA Seismic Live-Feed Path

**FR**: FR-RAG-NS-03
**Persona memo citation**: `personas-input/sectors-territories.md` §"GA seismic events drive northern earthquake response"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

## Context

The Risk Assessment agent ingests live seismic events from Geoscience Australia (GA). The reasoning is symmetric to ADR 02 (BoM):

* GA is the **single authoritative source** for AU seismic events,
* events are **time-critical** (initial assessment within minutes),
* the corpus indexes GA's *response doctrine* — not the event stream itself.

A corpus retrieval call on the live event:

1. adds latency without information gain,
2. risks citing stale corpus content as "evidence" for a magnitude figure that came from the live feed,
3. erodes the audit-log determinism (replay would need both corpus-build-sha **and** the GA feed snapshot).

## Decision

GA seismic-feed ingestion does **not** invoke RAG. The Risk Assessment agent's downstream **assessment** call (e.g., "what response doctrine applies to a magnitude-5.2 event near Darwin?") still carries `rag_used=true` and cites the relevant handbook — RAG is preserved on the decision, not the signal ingestion.

## Audit-log shape

```json
{
  "agent_name": "RiskAssessmentAgent",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "ga-live-feed",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/03-rag-optout-ga-live.md"
}
```

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-03]: GA seismic live feed is authoritative; doctrine grounding moves to the downstream assessment call.
```

Applied at the live-feed entry point in `apps/agents/risk_assessment/pipeline.py`.

## Consequences

* **Preserves**: event freshness, signal authority, replay determinism (GA feed snapshot is the only replay anchor).
* **Precludes**: grounded explanation on the ingestion record itself.
* **Maintenance**: the marker MUST be re-applied if the ingestion path is ever restructured into a single LLM-fronted pipeline.

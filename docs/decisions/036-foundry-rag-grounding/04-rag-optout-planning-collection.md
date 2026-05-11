# ADR 04 — RAG Opt-Out: Planning Officer Pure-Data-Collection Paths

**FR**: FR-RAG-NS-04
**Persona memo citation**: `personas-input/operational.md` §"Planning officers collect signals before they decide"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

**Code-marker optional**: true

## Context

The **collection** stage gathers facts from upstream services (incident records, resource inventories, dependency chains) and normalises them into the planning context. No decision is being made; no recommendation is being generated; the LLM is used purely to extract structured fields from semi-structured input.

The persona memo for Planning Officers explicitly separates these phases: "we want grounded reasoning *on the decision*; the collection step needs to be fast and deterministic so the same incident always produces the same planning context."

A grounded retrieval on the collection step:

1. adds 50–250 ms per stage with no decision-quality gain,
2. risks the LLM "explaining" a fact rather than extracting it (which is a planning-context corruption),
3. inflates the audit volume (collection runs hundreds of times per incident vs. dozens of decisions).

## Decision

LLM calls in the **collection** stage of `apps/agents/planning/pipeline.py` carry `rag_used=false` and an explicit `rag_optout_reason="planning-collection"`. The downstream **assessment** and **decision** stages remain grounded.

## Audit-log shape

```json
{
  "agent_name": "PlanningOfficerAgent",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "planning-collection",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/04-rag-optout-planning-collection.md"
}
```

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-04]: Planning collection is pure structured-extraction; doctrine grounding lives on the assessment + decision stages.
```

Applied at the LLM call site in the planning collection stage.

## Consequences

* **Preserves**: collection-stage determinism, planning-context reproducibility, latency budget (collection runs N>>1 per decision).
* **Precludes**: grounded explanations on the collection step. (If an operator asks "why did Planning gather this resource record?", the answer is in the upstream record — not in a corpus chunk.)
* **Replay**: collection records are deterministically replayable from the input alone — `corpus_build_sha` is **not** needed in the replay key for these records.

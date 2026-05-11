# ADR 05 — RAG Opt-Out: Logistics Transactional Resource-Movement Paths

**FR**: FR-RAG-NS-05
**Persona memo citation**: `personas-input/operational.md` §"Resource moves are transactions, not recommendations"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

## Context

The Logistics agent (per AIIMS span-of-control) executes **transactional** resource movements: dispatch a strike team, recall a unit, transfer a coordination function. These transactions are:

* **decisions made elsewhere** — Resource Allocation has already committed; Logistics merely realises the move,
* **idempotent** by construction (same source + destination + role = same transaction),
* **bounded** by service-bus message contracts — the LLM call exists only to format the dispatch directive, not to choose it.

A grounded retrieval here:

1. adds latency to a critical-path dispatch (operationally a hard cost),
2. risks the LLM second-guessing a Resource Allocation decision (which would create an inconsistency loop),
3. doubles audit volume on idempotent transactions.

## Decision

LLM calls in the transactional dispatch path of the Resource Allocation / Logistics pipeline carry `rag_used=false` and an explicit `rag_optout_reason="logistics-transactional"`. The **upstream** Resource Allocation **decision** call remains grounded (citation list pinned to the dispatched directive).

## Audit-log shape

```json
{
  "agent_name": "ResourceAllocationAgent",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "logistics-transactional",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/05-rag-optout-logistics-transactional.md"
}
```

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-05]: Transactional dispatch — decision was already grounded; this call only formats the directive.
```

Applied at the dispatch-formatting LLM call site in `apps/agents/resource_allocation/pipeline.py`.

## Consequences

* **Preserves**: dispatch latency, transactional idempotency, audit-volume bound.
* **Precludes**: re-justification of the dispatch on the transactional record. (Replay shows the upstream Resource Allocation decision record — that is where the citations live.)
* **Failure handling**: if dispatch formatting fails, the agent retries with the *same* upstream decision context — no re-grounding occurs (which would risk citation drift).

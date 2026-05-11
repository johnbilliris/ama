# ADR 09 — RAG Opt-Out: Observer-Auditor Non-Decision Paths

**FR**: FR-RAG-NS-09
**Persona memo citation**: `personas-input/technical-quality.md` §"observer-auditor is read-only"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

## Context

The Observer-Auditor surface (audit-replay UI, byte-replay automation, integrity-verification jobs) **reads** existing audit records and **does not make decisions**. Specifically:

* `apps/api/app/services/audit_export_service.py` exports records for compliance reviewers,
* the byte-replay automation (T144) re-renders an old completion from the original prompt + corpus snapshot to verify reproducibility,
* the playback service streams archived events for tabletop after-action reviews.

These paths use the LLM **only** to verify reproducibility — the LLM is asked "given this exact prompt + this exact corpus snapshot + this exact model, do you produce the same output?". A fresh retrieval call would defeat the test (it would compute a *new* citation set from the *current* corpus build, breaking the byte-replay invariant).

## Decision

LLM calls on Observer-Auditor non-decision paths carry `rag_used=false` and `rag_optout_reason="observer-auditor"`. The replayed prompt's original `retrieved_chunks[]` is read from the archived audit record and re-injected into the prompt as static context — the call is **not** re-grounded.

## Audit-log shape

```json
{
  "agent_name": "ObserverAuditor",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "observer-auditor",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/09-rag-optout-observer-auditor.md",
  "replay_of_call_id": "<original call_id>"
}
```

The `replay_of_call_id` field cross-references the original record so SC-011 byte-replay reports stay traceable.

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-09]: Observer-Auditor read-only / replay path; no fresh retrieval to preserve byte-replay determinism.
```

Applied at the LLM call site in the audit-export and byte-replay services.

## Consequences

* **Preserves**: byte-replay determinism (SC-011 ≥ 95% reproduction), audit-trail integrity, compliance-review reproducibility.
* **Precludes**: any grounded enhancement of the replayed answer. (Replay reproduces the *original* answer faithfully; if the original was wrong, the audit trail surfaces that — re-grounding would *hide* the original error.)
* **Quality-memo §No-RAG Opt-Out Audit Trail**: this carve-out is explicitly recorded as a pre-condition for SC-011 — replay verification only works if replay does not re-ground.

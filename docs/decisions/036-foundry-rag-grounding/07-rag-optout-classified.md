# ADR 07 — RAG Opt-Out: Classified Content (ADF DACC, AFP Classified Annex)

**FR**: FR-RAG-NS-07; Constitution §NN-2 (national-security carve-out)
**Persona memo citation**: `personas-input/sectors-commonwealth.md` §"ADF DACC and AFP classified channels never traverse the corpus"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect) + Security Review Board
**Date**: 2026-05-08
**Status**: Accepted

## Context

A subset of operational content carries **above-OFFICIAL** PSPF markings:

* ADF DACC ("Defence Aid to the Civil Community") tasking annexes can carry `OFFICIAL: SENSITIVE` or `PROTECTED`,
* AFP classified annexes (covert tactical, CHIS handles, breach-point geometry) start at `PROTECTED` and can rise to `SECRET`.

The AMA corpus is **OFFICIAL ceiling by design** (FR-RAG-IDX-02; data-model.md §RetrievalRequest.classification_max). Above-OFFICIAL content:

1. is **not in the corpus** (so retrieval would return zero results, then risk a fabricated citation),
2. **must not** flow to the data-minimisation gateway (the gateway would deny, but the *attempt* itself is a logged event we want to avoid),
3. requires a separate audit trail with PSPF retention rules.

## Decision

LLM calls carrying above-OFFICIAL content are routed through the model gateway's **classified path** (`apps/agents/common/model_gateway.py`). On this path, RAG is structurally bypassed: the gateway refuses any retrieval invocation, and the audit record carries `rag_used=false` with `rag_optout_reason="classified"`.

The retrieval client `RetrievalRequest.classification_max` is `Literal["OFFICIAL"]`; any duck-typed caller attempting `classification_max="PROTECTED"` raises `ClassificationCeilingError` (defence in depth at the entity boundary).

## Audit-log shape

```json
{
  "agent_name": "<routing agent>",
  "call_kind": "inference",
  "rag_used": false,
  "rag_optout_reason": "classified",
  "adr_pointer": "docs/decisions/036-foundry-rag-grounding/07-rag-optout-classified.md",
  "gateway_decision": "deny|allow",
  "classification_marking": "PROTECTED|SECRET"
}
```

The `classification_marking` field is captured in the **classified-channel audit trail** (separate retention container), not in the operational `audit_records` Cosmos container.

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-07]: Classified content (above OFFICIAL); RAG bypass enforced by retrieval-client classification ceiling.
```

Applied in `apps/agents/common/model_gateway.py` (the routing decision point) and at any classified-content entry-point per spec-029 carve-out.

## Consequences

* **Preserves**: PSPF compliance (corpus stays OFFICIAL ceiling), structural separation between operational and classified audit trails.
* **Precludes**: any grounded explanation against the classified content. (Classified channel uses its own knowledge-base; spec-029 carve-out anchors the alternative.)
* **Defence in depth**: the entity boundary (`Literal["OFFICIAL"]`) AND the runtime check (`ClassificationCeilingError`) both enforce the ceiling — bypassing one requires bypassing both.

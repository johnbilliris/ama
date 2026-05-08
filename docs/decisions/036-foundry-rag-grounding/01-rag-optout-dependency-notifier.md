# ADR 01 — RAG Opt-Out: Dependency Notifier

**FR**: FR-RAG-NS-01
**Persona memo citation**: `personas-input/operational.md` §"Dependency notifications must be deterministic"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect)
**Date**: 2026-05-08
**Status**: Accepted

**Code-marker optional**: true

## Context

The Dependency Notifier (`apps/agents/common/dependency_notifier.py`) is a structured-signal pipeline. It receives a `CoordinationTask` and emits a deterministic `dict` summarising the task id, dependency ids, and status. There is **no LLM call** on this path.

The persona memo for Operational personnel calls out that dependency notifications must be:

* deterministic (so two identical tasks produce identical notifications),
* low-latency (sub-millisecond — they fan out in tight scheduling loops),
* free of any natural-language synthesis (downstream automation parses the JSON).

A grounded LLM call would breach all three properties: the corpus retrieval round-trip alone (≥ 50 ms p50) is two orders of magnitude over the latency budget, and the LLM's variable phrasing breaks downstream JSON parsing.

## Decision

The Dependency Notifier path is **structurally non-LLM** — RAG is not invoked because there is no LLM call to ground. This ADR exists to document the carve-out so that future refactoring (e.g., introducing an explanatory text field) cannot silently introduce an ungrounded call.

## Audit-log shape

Dependency-notifier outputs are not LLM `AuditRecord`s; they flow through the workflow-run repository's task-status-change journal. No `rag_optout_reason` is recorded because no LLM record is emitted.

If a future change introduces an LLM call on this path, the developer MUST:

1. Add a `# RAG-OPTOUT [FR-RAG-NS-01]: <reason>` marker, **OR**
2. Land a follow-up ADR amending this decision and remove the `code_marker_optional: true` flag.

## Code-comment marker

```python
# RAG-OPTOUT [FR-RAG-NS-01]: Dependency-notifier output is structured-signal only; no LLM call to ground.
```

The marker is **optional today** because no LLM call exists on the path. The lint mechanism (FR-RAG-NS-08) treats this ADR as marker-optional via the `code_marker_optional: true` front-matter line.

## Consequences

* **Preserves**: determinism, sub-millisecond latency, machine-parseable output.
* **Precludes**: post-hoc grounded explanation of dependency decisions. (If operators ask "why was task X blocked?", the answer comes from the workflow-run repository's audit journal — not from the agent.)
* **Maintenance**: any PR that introduces an LLM call to `dependency_notifier.py` MUST also amend this ADR and add the marker. The CI lint catches the unintended introduction.

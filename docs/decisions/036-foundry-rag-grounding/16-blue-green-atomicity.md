# ADR 16 — Blue-Green Alias-Flip Atomicity & Rollback SLO

**FR**: FR-RAG-IDX-04a (in-flight query atomicity), FR-RAG-IDX-09 (5-minute rollback SLO)
**Cluster**: A7 — Blue-Green Audit Replay Consistency
**Persona memo citation**: `personas-input/r3-technical-architecture.md` §F-ARCH-02 "Blue-green alias flip is not transactional at query layer"; `personas-input/r3-technical-delivery.md` §"5-minute rollback SLA"
**Approver**: AMA Spec-036 Architecture Review + Release Manager
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A7 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A7-ADR16` (planned). This stub exists per Assumption **A11** so `[NEEDS ADR]` markers on FR-RAG-IDX-04a and FR-RAG-IDX-09 resolve to a real path at plan-review time.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — F-ARCH-02 finding: alias update (`infra/modules/ai-search-blue-green.bicep:94-106`) and index creation are separate ARM operations; in-flight queries to the old index complete on the old index but new queries hit the new index. Without session-level pinning, multi-turn conversations can see citations from two `corpus_build_sha`s, breaking SC-011 byte-identical replay. F-ARCH-03 finding: no documented rollback for embedding-dimension regressions.
- **Decision — In-flight atomicity (FR-RAG-IDX-04a)** — Retrieval client MUST resolve the alias to a *concrete index name* at query start and use that concrete name for the entire query lifecycle (no alias re-resolution mid-query). Audit log MUST record the concrete index name in `retrieval_index_name` (see ADR-14). For multi-turn sessions, the concrete index name is pinned for the duration of the SSE stream; new SSE sessions resolve the alias afresh.
- **Decision — Rollback SLO (FR-RAG-IDX-09 / Pass 1 Q-P1-04)** — The 5-minute rollback timer **starts at emission of the `index_rollback` Service Bus event** (i.e., at parity-gate failure detection, mirroring spec 029 FR-008 "within 5 minutes of detecting a fast-burn breach"). "Rollback complete" means: (a) alias resolves to the previous (old) index for **all new queries** issued after the SLO deadline, AND (b) a rollback record `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}` is appended to the audit store. In-flight queries continue against the index version they started with per FR-RAG-IDX-04a.
- **Decision — Manual-not-automatic rollback** — Rollback is `feature.alias_flip_rollback` Manual operator action class (per A12 Q-P2-08); the operator path *is* the rollback mechanism (alias re-flip). Release Manager approval required; on-call paged via existing alert pipeline; emits `index_rollback` event to Service Bus.
- **Decision — 7-day previous-index retention** — Previous index MUST be retained 7 days post-flip (already required per FR-RAG-IDX-04; enforced by Bicep TTL tag).
- **Consequences** — SC-019 measurable (concurrent retrieval queries spanning blue-green flip return consistent index name in audit log; rollback completes ≤5 min). Closes F-ARCH-02 + F-ARCH-03 findings.

## Cross-references

- Cluster A7 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-04 in `specs/036-foundry-rag-grounding/spec.md` Session 4.
- ADR-14 for `retrieval_index_name` audit field.
- Existing `infra/modules/ai-search-blue-green.bicep` parity gate at `apps/ingest-runner/src/ama_ingest/parity_gate.py`.
- Plan phase `F-A7` in `specs/036-foundry-rag-grounding/plan.md`.

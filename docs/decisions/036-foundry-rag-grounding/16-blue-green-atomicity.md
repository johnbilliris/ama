# ADR 16 — Blue-Green Alias-Flip Atomicity & Rollback SLO

**FR**: FR-RAG-IDX-04a (in-flight query atomicity), FR-RAG-IDX-09 (5-minute rollback SLO)
**Cluster**: A7 — Blue-Green Audit Replay Consistency
**Persona memo citation**: `personas-input/r3-technical-architecture.md` §F-ARCH-02 "Blue-green alias flip is not transactional at query layer"; `personas-input/r3-technical-delivery.md` §"5-minute rollback SLA"
**Approver**: AMA Spec-036 Architecture Review + Release Manager
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A7)

## Context

The Phase D blue-green ingest path issued an alias flip via two ARM operations: index create + alias update (`infra/modules/ai-search-blue-green.bicep:94-106`). Two architecture-review findings from R3 amend identified a soundness gap:

- **F-ARCH-02**: in-flight queries that land between the alias-update HTTP request and its propagation to the data plane can race — some chunks come from the old index, some from the new — violating Spec 014 SC-011 byte-identical replay across a single conversation.
- **F-ARCH-03**: no documented rollback for embedding-dimension regressions; the parity gate (`apps/ingest-runner/src/ama_ingest/parity_gate.py`) emits a Service Bus event but the human procedure was undocumented.

Pass 1 Q-P1-04 settled the "rollback timer starts when?" question (at parity-gate failure detection, mirroring spec 029 FR-008's fast-burn breach semantics). Pass 2 Q-P2-08 classed alias-flip rollback as **Manual** in the A12 flag taxonomy.

## Decision

1. **In-flight query atomicity (FR-RAG-IDX-04a)** — the retrieval client resolves the alias to a *concrete index name* at query start and uses that concrete name for the entire query lifecycle. No alias re-resolution mid-query. The concrete name is recorded in `retrieval_index_name` on the audit record (ADR 14).
2. **Multi-turn pinning** — for an SSE-streamed conversation, the concrete index name is pinned for the duration of the SSE session. The next SSE session resolves the alias afresh. This bounds the "two corpus shas in one conversation" risk to zero while still allowing fast cutover for new sessions.
3. **5-minute rollback SLO (FR-RAG-IDX-09)** — when the parity gate fails, the rollback timer starts at the *emission* of the `index_rollback` Service Bus event. Rollback complete means: (a) the alias resolves to the previous index for all queries started after the SLO deadline; (b) a rollback record `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}` is appended to the audit store. In-flight queries continue against the index version they started with, per FR-RAG-IDX-04a.
4. **Manual-not-automatic rollback** — `feature.alias_flip_rollback` is in the **Manual operator action** A12 class. The operator path *is* the rollback mechanism (alias re-flip). Release-Manager approval is required; on-call is paged via the existing alert pipeline. The orchestrator at `apps/api/app/services/blue_green_orchestrator.py` exposes `flip_alias()` and `rollback_alias()` as the two operator-callable verbs.
5. **7-day previous-index retention** — the previous index is retained for 7 days post-flip (already required by FR-RAG-IDX-04 and enforced by a Bicep TTL tag on the index resource).
6. **Audit consistency** — every flip and every rollback emits a typed audit record so downstream replay can deterministically pick the right index version.

## Rationale

- **Why pin at query start, not at conversation start?** Pinning at conversation start would force every new turn through the *original* index even after a flip, defeating the whole point of blue-green for new content. Pinning at query start (with multi-turn extending to the SSE session) gives both byte-identical replay and prompt new-content uptake.
- **Why a 5-minute rollback SLO?** This matches Spec 029 FR-008 ("fast-burn breach detected → mitigation initiated within 5 minutes"). Operators already trained on that SLO transfer the muscle memory.
- **Why Manual, not Automatic?** Parity-gate failures can be transient (ingest-job glitch, embedding-API throttling); auto-rollback would amplify rather than damp the incident. The 5-minute SLO is fast enough that the human in the loop is not a bottleneck, given the existing on-call pipeline.
- **Why a 7-day retention window?** Two days covers a long weekend; seven days covers a public-holiday week and gives enough cushion for a delayed compliance review without escalating Cosmos cost. Anything longer was rejected as cost without operational benefit.

## Consequences

**Positive**
- SC-019 (concurrent retrieval queries spanning a blue-green flip return a consistent `retrieval_index_name` in the audit log; rollback completes ≤ 5 min) becomes measurable. The E2E test `tests/e2e/test_blue_green_alias_flip.py` (T221) exercises the post-flip pinning, the 7-day previous-index accessibility, and the ≤ 5-min rollback path.
- F-ARCH-02 and F-ARCH-03 findings closed.
- Audit replay becomes unconditional: any audit row in any time window can be re-played byte-identically by reading `retrieval_index_name`.

**Negative / mitigations**
- Concrete-name resolution adds one additional alias→index lookup per query. Mitigated by an in-process LRU cache with a 30-second TTL — staleness is bounded but well under the multi-turn pinning window.
- Operators must learn that flip and rollback are the *same primitive*. Mitigated by a single runbook (`docs/runbooks/036-foundry-rag-blue-green-flip.md`) covering both directions.
- Storage cost of the 7-day retention is non-trivial for very large indexes (estimated +35 % index storage during a heavy-rebuild week). Acceptable: blue-green is, by design, a temporary doubling.

## Cross-references

- Cluster A7 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-04 in spec.md Session 4; Pass 2 Q-P2-08 in spec.md Session 5.
- ADR 14 for the `retrieval_index_name` audit field.
- Existing `infra/modules/ai-search-blue-green.bicep` and parity gate at `apps/ingest-runner/src/ama_ingest/parity_gate.py`.
- Tasks T166–T172; E2E coverage in T221 (F-A10).
- Plan phase F-A7 in `specs/036-foundry-rag-grounding/plan.md`.
- Runbook: `docs/runbooks/036-foundry-rag-blue-green-flip.md`.

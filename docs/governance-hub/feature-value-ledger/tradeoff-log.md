# Decision/Tradeoff Log (spec-037 artefact 5b)

> Companion to the [Feature-Value Ledger](../../../specs/shared/feature-value-ledger.md).
> One row per ADR under `docs/aidr/decisions/` plus the four spec-037 ADRs
> (FR-032 + FR-036).

- Source publication: `24e82da3-be63-5286-9b9f-e627874be014`

| ADR | Bounding feature(s) | Tension | Alternatives considered | Rationale |
|---|---|---|---|---|
| [`ADR-036-001`](../../aidr/decisions/ADR-036-001-real-sub-agent-invocation.md) | 036-foundry-rag-grounding | `automation-vs-command` | Direct API stubs; MAF agent registry; Real sub-agent invocation via MAF | Real invocation preserves spec-008..012 behaviour while migrating to Foundry SDK. |
| [`ADR-036-002`](../../aidr/decisions/ADR-036-002-direct-rest-lifecycle.md) | 036-foundry-rag-grounding | `none` | SDK-only; Hybrid SDK + REST; Direct REST lifecycle for migration anchors | Direct REST gives explicit control over the three migration anchor signatures. |
| [`ADR-036-003`](../../aidr/decisions/ADR-036-003-cosmos-session-consistency.md) | 036-foundry-rag-grounding | `none` | Strong; Eventual; Session | Session consistency balances RAG-citation freshness with cross-region throughput. |
| [`ADR-036-004`](../../aidr/decisions/ADR-036-004-apim-token-bucket-circuit-breaker.md) | 036-foundry-rag-grounding | `none` | Token-bucket only; Circuit breaker only; Combined | Combined gives both rate-limit smoothing and fast-fail under sustained outage. |
| [`ADR-036-005`](../../aidr/decisions/ADR-036-005-cascade-etag-optimistic-concurrency.md) | 036-foundry-rag-grounding | `none` | Pessimistic locks; Last-writer-wins; Cascade-ETag | Cascade-ETag honours append-only audit while avoiding distributed locks. |
| [`ADR-036-006`](../../aidr/decisions/ADR-036-006-lessons-capture-blob-worm.md) | 036-foundry-rag-grounding | `none` | Cosmos only; Blob WORM | Blob WORM matches the spec-030 audit-archive 7-year immutability precedent. |
| [`ADR-036-007`](../../aidr/decisions/ADR-036-007-distributed-sequence-allocator.md) | 036-foundry-rag-grounding | `none` | DB sequence; ULID; Distributed allocator | Allocator avoids hot-partition writes during simulation surges. |
| [`ADR-036-008`](../../aidr/decisions/ADR-036-008-sli-thresholds-rationale.md) | 036-foundry-rag-grounding | `none` | Per-spec SLOs; Single global SLO; Tiered SLI thresholds | Tiered thresholds map to capstone criteria via spec-015. |
| [`ADR-036-009`](../../aidr/decisions/ADR-036-009-idempotency-cache-design.md) | 036-foundry-rag-grounding, 036-sim-agent-extend | `none` | No idempotency; Server-side dedup; Cache TTL 24h | 24h TTL matches the longest sustained simulation activation pattern. |
| [`ADR-036-010`](../../aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md) | 036-foundry-rag-grounding | `none` | No amendment cycle; Annual; Per-deployment | Per-deployment review with explicit amendment cycle preserves QG-3 lessons capture. |
| [`ADR-036-011`](../../aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md) | 036-foundry-rag-grounding | `none` | Cycle 2 only; Cycle 3 expansion | Cycle 3 extends the amendment cycle with cross-spec coupling enforcement. |
| [`ADR-037-01-text-first-evidence-pack`](../../aidr/decisions/adr-037-01-text-first-evidence-pack.md) | 037-capstone-evidence-pack | `none` | OpenAPI-first contract; YAML-only artefacts; Bespoke per-artefact schemas; Markdown + JSON sidecar (chosen) | Text-first matches the 'evidence in git' principle and reuses existing JSON Schema tooling. |
| [`ADR-037-02-executive-shell-reuse`](../../aidr/decisions/adr-037-02-executive-shell-reuse.md) | 037-capstone-evidence-pack | `automation-vs-command` | Standalone micro-frontend; Embed in dashboard sub-route; New sibling route reusing PersonaWorkspace (chosen) | Honours Clarification 3 + SC-009 (zero net-new dashboards / chart libraries). |
| [`ADR-037-03-manual-evidence-cap`](../../aidr/decisions/adr-037-03-manual-evidence-cap.md) | 037-capstone-evidence-pack | `speed-vs-legality` | No cap; Fleet-wide cap; Hard cap with no override; Per-artefact ≤0.5 with named-auditor override (chosen) | Preserves NN-1 human-in-the-loop without disabling judgement-heavy RAI Register. |
| [`ADR-037-04-three-layer-append-only`](../../aidr/decisions/adr-037-04-three-layer-append-only.md) | 037-capstone-evidence-pack | `visibility-vs-privacy` | Git only; Cosmos only; Blob only; Three-layer (chosen); Four-layer with KV signing | Three-layer gives tamper-evidence auditors can verify independently without the cost of a fourth signing layer. |
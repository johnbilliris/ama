# Research: Monitoring Agent — Signal Triage, Misinformation Detection, and Escalation

**Feature**: 010-monitoring-agent  
**Date**: 2026-04-11  
**Status**: Complete

---

## Research Task 1 — Async LLM Misinformation Evaluation vs 5-Second Escalation SLA (CHK030)

**Context**: SC-001 requires high-risk signals to produce a handoff within 5 seconds. FR-004 requires escalated signals to undergo LLM misinformation evaluation before escalation. Typical Azure OpenAI latency for a short classification prompt is 1–3 seconds, but can spike to 5–10+ seconds under load.

**Decision**: Use async LLM evaluation with timeout-gated escalation. The misinformation check runs concurrently with a configurable timeout (default: 3 seconds). If the LLM responds within the timeout, its result determines whether escalation proceeds or is blocked. If the LLM does NOT respond within the timeout, escalation proceeds as **fail-safe-CLOSED** (held for human review) consistent with the life-safety-first mandate (CHK066). This holds the signal rather than auto-escalating potentially dangerous misinformation.

**Rationale**: The 5-second SLA is measured from signal receipt to handoff *creation*, not delivery. By using a 3-second timeout for LLM evaluation, the remaining 2 seconds provide sufficient margin for signal parsing, summarisation, and handoff assembly. For escalated signals that time out on LLM evaluation, they are held for human review rather than auto-escalated — this satisfies both the SLA (the *decision* is made within 5 seconds) and the constitution's life-safety-first mandate.

**Alternatives considered**:
- **Fire-and-forget LLM check**: Escalate immediately and retroactively block if LLM returns misinformation. Rejected because this could propagate misinformation to downstream agents, violating Constitution Principle III.
- **Synchronous LLM with no timeout**: Could block the entire pipeline for 10+ seconds during Azure OpenAI degradation. Rejected as it violates SC-001.
- **Skip LLM for non-social escalated signals**: Would reduce LLM load but contradicts FR-004 which applies to all escalated signals regardless of source kind.

---

## Research Task 2 — Freshness Score in Escalation Condition (CHK070)

**Context**: FR-009 escalation condition checks only `confidenceScore >= threshold`. FR-017 says the agent MUST consider `freshnessScore`. FR-023 says to reduce triage confidence when sources degrade. These requirements are misaligned — freshness is mandated but not incorporated into the escalation gate.

**Decision**: Introduce an `effectiveConfidence` score computed as `confidenceScore * freshnessScore`. The escalation threshold is applied to `effectiveConfidence` rather than raw `confidenceScore`. This means a signal with `confidenceScore=0.85` and `freshnessScore=0.7` has `effectiveConfidence=0.595`, which falls below the 0.8 threshold and would NOT escalate.

**Rationale**: This aligns FR-009 with FR-017 and FR-023 in a single, testable formula. The multiplicative approach naturally degrades confidence as freshness drops, which is the behaviour mandated by the constitution ("agents MUST consider freshness in decisions"). The raw `confidenceScore` and `freshnessScore` are both preserved in audit records alongside the computed `effectiveConfidence` for traceability.

**Alternatives considered**:
- **Additive penalty**: `confidenceScore - (1 - freshnessScore) * penalty_factor`. More configurable but introduces a new tuning parameter with no clear default.
- **Separate freshness gate**: Block escalation below a minimum freshness threshold (e.g., 0.3). Simpler but doesn't capture the interaction between confidence and freshness.
- **Weighted average**: `alpha * confidenceScore + (1 - alpha) * freshnessScore`. Rejected as it requires alpha tuning and dilutes high-confidence signals unnecessarily.

---

## Research Task 3 — Audit Store Unavailability Degradation Path (CHK040)

**Context**: FR-020–FR-022 mandate audit recording for every decision in Cosmos DB. No degradation path is specified if Cosmos DB becomes unavailable during a disaster event — which is precisely when audit is most critical.

**Decision**: Implement a three-tier degradation strategy:
1. **Primary**: Write audit records to Cosmos DB (normal path).
2. **Secondary**: If Cosmos DB write fails, buffer the audit record in an in-memory ring buffer (bounded at 10,000 records, ~50 MB) and schedule async flush with exponential backoff retries.
3. **Tertiary**: If the in-memory buffer reaches capacity, spill to a local append-only JSONL file (`/var/log/monitoring-agent/audit-buffer.jsonl`) and emit a critical alert to Application Insights.
4. **Recovery**: On Cosmos DB recovery, the agent drains the in-memory buffer first, then replays the local file (if any), in strict chronological order. Each record carries a `buffered_at` timestamp and `flush_source` annotation to distinguish buffered from direct-write records.

**Rationale**: The constitution mandates append-only audit trails for safety-critical decisions. Silently dropping audit records during a Cosmos DB outage would violate this mandate. The three-tier approach ensures audit continuity with graceful degradation — in-memory is fast, local file is durable, and both are reconciled on recovery. The ring buffer size (10,000 records) supports approximately 10 minutes of peak throughput (1,000 signals/min) which exceeds typical Azure Cosmos DB recovery time.

**Alternatives considered**:
- **Fail-stop on audit failure**: Halt signal processing if audit can't be written. Rejected because this would halt life-safety processing during a disaster, violating Constitution Principle I and the graceful degradation NFRs.
- **Azure Service Bus dead-letter for audit**: Route failed audit writes to a Service Bus queue. Rejected because adding another Azure dependency doesn't help when the issue is Azure infrastructure degradation.
- **In-memory only (no file spill)**: Simpler but risks audit loss if the container restarts while the buffer is full.

---

## Research Task 4 — Fail-Safe Policy for Misinformation Detection (CHK066)

**Context**: The spec defines fail-safe-open for misinformation detection (FR-007 edge case): unexpected LLM responses are treated as "credible", allowing signals through. CHK066 identifies a conflict with Constitution Principle I (Life Safety First) — allowing unverified signals through could propagate misinformation that endangers lives.

**Decision**: Change to **fail-safe-CLOSED** for misinformation classification. When the LLM returns an unexpected response (not "credible", "suspicious", or "misinformation"), the signal is HELD for human review rather than automatically allowed through. This is the same behaviour as LLM unavailability (FR-006). The unexpected response is logged with full context for operator investigation.

For "suspicious" classification: the signal proceeds to triage but with a `0.15` confidence penalty applied to `effectiveConfidence`. This provides differential treatment for "suspicious" vs "credible" as identified by CHK027.

**Rationale**: In a life-safety-critical disaster response system, the cost of propagating misinformation (panic, misallocated resources, delayed evacuations) far exceeds the cost of briefly holding a signal for human review. The constitution mandates "degrade safely: if confidence drops or data is stale, fall back to conservative guidance and/or request human approval." Fail-safe-closed is the conservative choice.

**Alternatives considered**:
- **Fail-safe-open (spec default)**: Allow through on unexpected response. Rejected per CHK066 — violates life-safety-first mandate.
- **Auto-block on unexpected response**: Treat unexpected as "misinformation" and block. Rejected because blocking without human review loses the signal entirely; holding preserves it for operator action.
- **Retry the LLM on unexpected response**: Could work but adds latency and doesn't solve the fundamental classification ambiguity.

---

## Research Task 5 — Azure OpenAI Availability in Australian Regions (CHK060)

**Context**: NFR-004 mandates Australian deployment. The spec requires Azure OpenAI for LLM operations. Must confirm Azure OpenAI is available in `australiaeast`.

**Decision**: Azure OpenAI is available in `australiaeast` with GPT-4o and GPT-4o-mini deployments. Use `australiaeast` for primary deployment. For DR in `australiasoutheast`, note that Azure OpenAI availability may be limited — design the agent so that LLM unavailability triggers graceful degradation (rule-based triage fallback per FR-024) rather than being a hard dependency.

**Rationale**: Azure OpenAI regional availability is confirmed for Australia East. The graceful degradation design (already required by FR-024) provides built-in resilience if the LLM service is unavailable in a DR region.

**Alternatives considered**:
- **Cross-region LLM routing**: Route LLM calls from `australiasoutheast` to `australiaeast`. Rejected because it could violate data residency constraints — signal content sent to LLM would cross regions.
- **Self-hosted model in DR**: Deploy a local model via Azure ML. Rejected as over-engineering for this iteration; rule-based fallback is sufficient.

---

## Research Task 6 — Cosmos DB Partition Strategy for Audit Trail (CHK007)

**Context**: FR-022 says partition key should be "aligned with incident scope" but doesn't specify the key path or hot-partition mitigation.

**Decision**: Use a composite partition key strategy:
- **Container**: `monitoring-decisions`
- **Partition key**: `/incident_scope_key` where `incident_scope_key` = `{tenant_id}:{incident_id}` (or `{tenant_id}:unassociated` for signals without an incident).
- **Hot-partition mitigation**: For high-traffic incidents, the `unassociated` partition uses a synthetic suffix (`{tenant_id}:unassociated:{signal_id_hash % 16}`) to distribute writes across 16 logical partitions.
- **Cross-partition queries**: Required only for post-incident review (non-latency-critical). Use cross-partition queries with continuation tokens for paginated retrieval.

**Rationale**: Partition by incident scope aligns with the primary query pattern (retrieve all decisions for an incident during post-mortem review). The synthetic suffix for unassociated signals prevents a hot partition during the early stage of an event when many signals arrive before an incident is declared.

**Alternatives considered**:
- **Partition by signal_id**: Even distribution but makes incident-scoped queries expensive (always cross-partition). Rejected.
- **Partition by timestamp**: Good for time-range queries but doesn't support efficient incident-scoped retrieval. Rejected.
- **Hierarchical partition key**: Cosmos DB supports hierarchical partitioning (e.g., `/tenant_id/incident_id`). Viable but adds complexity for a v1 implementation.

---

## Research Task 7 — Signal Input Validation at Agent Boundary (CHK001)

**Context**: The spec assumes all required fields are populated by the ingestion pipeline. CHK001 identifies that no validation or rejection behaviour is specified at the Monitoring Agent boundary.

**Decision**: Validate `SignalEnvelope` at the agent boundary using Pydantic v2 validation. Signals with missing or invalid required fields (`category`, `confidenceScore`, `freshnessScore`, `source`) are rejected with a `validation_failed` audit record. Signals with missing optional fields (`incidentId`, `jurisdictionId`) are accepted and processed with null-safe logic. The validation rejection count is emitted as a metric to Application Insights.

**Rationale**: Defence-in-depth — even though the ingestion pipeline should normalise signals, the agent should not crash or produce undefined behaviour on malformed input. Pydantic validation is already the pattern used across the codebase (all domain models are `BaseModel` subclasses).

**Alternatives considered**:
- **Trust the pipeline (no validation)**: Rejected because the constitution mandates safe degradation, and a malformed signal could cause unhandled exceptions.
- **Schema validation middleware**: Add a separate validation layer before the agent. Rejected as unnecessary complexity when Pydantic handles this naturally.

---

## Research Task 8 — Deduplication Mechanism for Multi-Instance Scaling (CHK024)

**Context**: FR-029 requires idempotency checking on `signal_id` within a configurable window. CHK024 asks whether this uses in-memory cache, distributed cache, or database lookup.

**Decision**: Use a time-bounded in-memory set (LRU cache with TTL) per instance for v1. Each instance maintains its own dedup cache. At the messaging infrastructure level (Azure Service Bus), use session-based message delivery to ensure signals for the same `signal_id` are routed to the same instance (session ID = `signal_id`). This provides per-instance dedup that is effective with session affinity.

**Rationale**: Distributed caching (e.g., Redis) adds infrastructure complexity and latency for a check that only needs to catch at-least-once delivery retries within a short window. Session-based routing in Azure Service Bus ensures the same `signal_id` goes to the same instance, making per-instance dedup effective. The 10-minute window is short enough that cache memory remains bounded.

**Alternatives considered**:
- **Azure Redis Cache**: Provides cross-instance dedup but adds latency, cost, and another infrastructure dependency. Over-engineering for v1.
- **Cosmos DB lookup**: Guaranteed cross-instance consistency but adds ~5ms per signal, which impacts the 5-second SLA at scale. Rejected for hot path.
- **Bloom filter**: Space-efficient but has false positives and no TTL support. Rejected.

---

## Research Task 9 — Configuration Change Propagation (CHK044)

**Context**: Multiple thresholds are configurable via environment variables. CHK044 asks whether changes are applied at startup only or hot-reloaded.

**Decision**: Startup-only for v1. All environment variable-based configuration is read at agent startup and cached in instance attributes. Changes require a container restart (rolling update via Azure Container Apps). Hot-reload is deferred to a future iteration when configuration moves to a centralised config service.

**Rationale**: Environment variable configuration is the simplest model and is consistent with 12-factor app principles. Azure Container Apps supports zero-downtime rolling updates, so configuration changes can be applied without service interruption. Hot-reload adds complexity (config watching, thread-safety, state consistency) that is not justified for v1.

**Alternatives considered**:
- **Azure App Configuration with polling**: Provides hot-reload but adds another Azure dependency and polling overhead. Deferred to v2.
- **Config file with inotify/watchdog**: Works on Linux but is fragile in containerised environments with ephemeral filesystems.

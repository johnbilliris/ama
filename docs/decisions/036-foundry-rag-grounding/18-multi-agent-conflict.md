# ADR 18 — Multi-Agent Conflict Detection & AIIMS Escalation Chain

**FR**: FR-RAG-COORD-01 (conflict detection), FR-RAG-COORD-02 (escalation)
**Cluster**: A9 — Multi-Agent Coordination
**Persona memo citation**: `personas-input/r3-operational.md` §"Conflicting recommendations from concurrent agents — Ops Officer ownership"; `personas-input/r3-technical-architecture.md` §"deterministic replay constraint"
**Approver**: AMA Spec-036 Architecture Review + Ops Officer persona owner
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A9 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A9-ADR18` (planned). This stub exists per Assumption **A11** so `[NEEDS ADR]` markers on FR-RAG-COORD-01 and FR-RAG-COORD-02 resolve to a real path at plan-review time.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — Two or more agents (Risk Assessment + Monitoring; Evacuation + Resource Allocation) routinely issue recommendations on overlapping resources, geographies, time windows, or hazard severities. Without detection, contradictions are silently surfaced; with naive auto-resolution, the platform breaches Constitution Principle I (no AI override of human authority).
- **Decision — Detection mechanics (Pass 2 Q-P2-06)** — **Reactive, post-return, deterministic, rule-based** detector. Runs in the recommendation-aggregation layer (NOT inside any individual agent and NOT in real-time streaming). Compares each pair of agent recommendations after both return. Pre-emptive divergence detection during inference is rejected because (a) it requires inter-agent message-passing (contradicting spec-033 MAF agent-isolation model); (b) it cannot satisfy Constitution Principle IV deterministic replay (every conflict event must be reproducible from `retrieved_chunks[] + prompt_sha`).
- **Decision — Four conflict classes** —
  - **(1) Resource conflict** — same `resource_id` claimed by two agents in overlapping `(start_time, end_time)` windows.
  - **(2) Spatial conflict** — incompatible recommendations covering overlapping `(geo_bbox, time_window)` (e.g., "evacuate" vs "shelter-in-place" for the same area).
  - **(3) Temporal conflict** — action verbs with mutually exclusive deadlines (e.g., "issue warning by T+5min" vs "withhold pending verification").
  - **(4) Severity conflict** — conflicting hazard severity buckets for the same hazard (Risk Assessment vs Monitoring) with delta ≥1 AIIMS incident level.
- **Decision — `conflict_group_id` audit emission** — On any match, the detector emits a `conflict_group_id` to the audit log linking both agent records; resolution is human-in-loop per FR-RAG-COORD-02. No AI auto-resolution at any stage (Constitution Principle I).
- **Decision — Escalation chain (Pass 1 Q-P1-03)** — Per AIIMS §II-A Control / Operations split:
  1. **Ops Officer** receives the `conflict_detected` event first (Operations function owns tactical resource arbitration).
  2. If the Ops Officer does not acknowledge within **5 minutes**, the platform escalates to the **IC** (Control function) and records `escalation_unack_timeout`.
  3. If both are unreachable AND the requesting agent is in degraded-connectivity mode, Field Coordinator MUST queue the conflict for IC review on reconnect per FR-RAG-LS-02 offline boundaries (Field Coordinator MUST NOT auto-resolve cross-agent conflicts).
- **Decision — Disable path** — `feature.multi_agent_conflict_detection.enabled` (Reversible class per A12); when disabled, agents revert to single-agent behaviour and `conflict_group_id` is not populated; flip emits `multi_agent_coordination_disabled` audit event; reversible mid-incident per spec 029 FR-008 5-minute SLO.
- **Consequences** — Ops Officer carries the resolution authority for tactical resource conflicts; IC for unack timeouts; Field Coordinator constrained to queue-on-reconnect; audit log has full provenance (`conflict_group_id` links every implicated record).

## Cross-references

- Cluster A9 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-03, Pass 2 Q-P2-06/Q-P2-08 in `specs/036-foundry-rag-grounding/spec.md` Sessions 4 + 5.
- Schema `specs/036-foundry-rag-grounding/contracts/conflict_detection.schema.json`.
- ADR-14 for offline-decision boundary audit fields.
- Plan phase `F-A9` in `specs/036-foundry-rag-grounding/plan.md`.

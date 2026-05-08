# ADR 18 — Multi-Agent Conflict Detection & AIIMS Escalation Chain

**FR**: FR-RAG-COORD-01 (conflict detection), FR-RAG-COORD-02 (escalation)
**Cluster**: A9 — Multi-Agent Coordination
**Persona memo citation**: `personas-input/r3-operational.md` §"Conflicting recommendations from concurrent agents — Ops Officer ownership"; `personas-input/r3-technical-architecture.md` §"deterministic replay constraint"
**Approver**: AMA Spec-036 Architecture Review + Ops Officer persona owner
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A9)

## Context

Spec 033's Microsoft Agent Framework (MAF) topology runs multiple specialised agents concurrently — Risk Assessment, Monitoring, Evacuation, Resource Allocation — each with its own retrieval/prompt path. Two failure modes surface in practice:

- **Silent contradiction.** Risk Assessment and Monitoring may classify the same hazard at different AIIMS levels (e.g. "Level 2" vs "Level 3"). Evacuation and Resource Allocation may both lay claim to the same vehicle in overlapping time windows. Without a coordination layer, both recommendations land on the operator unranked and unflagged.
- **Auto-resolution risk.** A naïve "pick the higher-confidence answer" auto-resolver crosses Constitution Principle I (no AI override of human authority) and Pass 2 Q-P2-06's settled deterministic-replay requirement: any auto-resolver introduces hidden state that cannot be reproduced from `retrieved_chunks[] + prompt_sha`.

The R3 operational memo and the Pass 1 Q-P1-03 negotiation produced an AIIMS-aligned escalation chain (Ops Officer → IC → Field Coordinator queue) that this ADR encodes.

## Decision

1. **Detection mechanics (Pass 2 Q-P2-06)** — **reactive, post-return, deterministic, rule-based.** The detector runs in the recommendation-aggregation layer at `apps/api/app/services/conflict_detection.py`, *not* inside any individual agent and *not* during streaming inference. It compares each pair of agent recommendations after both have returned. Pre-emptive divergence detection during inference is rejected because (a) it requires inter-agent message-passing — contradicting spec 033's MAF agent-isolation model — and (b) it cannot satisfy Principle IV deterministic replay.
2. **Four conflict classes** (`apps/api/app/services/conflict_detection.py::detect_conflicts`):
   - **Resource conflict** — same `resource_id` claimed by two agents in overlapping `(start_time, end_time)` windows.
   - **Spatial conflict** — antagonistic action verbs covering overlapping `(geo_bbox, time_window)`. The verb-antagonism table is `{evacuate ↔ shelter-in-place, deploy ↔ recall}`; symmetric and conservative — only verb pairs explicitly listed conflict.
   - **Temporal conflict** — antagonistic action verbs whose deadlines fall within 60 seconds of each other.
   - **Severity conflict** — same `hazard_type` with an AIIMS-level delta ≥ 1.
3. **`conflict_group_id` audit emission** — on any match, the detector emits a `conflictDetectionLog` Cosmos record (Australia East, partition key `/conflict_group_id`, container provisioned by `infra/bicep/modules/cosmos-conflict-detection.bicep`) and stamps both implicated audit rows with the same `conflict_group_id`. **No AI auto-resolution at any stage** (Constitution I).
4. **Escalation chain (Pass 1 Q-P1-03)** — `apps/api/app/services/aiims_escalation.py`:
   1. **Ops Officer** receives the `conflict_detected` event first (Operations function owns tactical resource arbitration in AIIMS § II-A).
   2. If the Ops Officer does not acknowledge within **5 minutes**, the platform escalates to the **IC** (Control function) and stamps `escalation_unack_timeout`.
   3. If both Ops Officer and IC are unreachable **and** the requesting agent is in degraded-connectivity mode, the conflict is queued for IC review on reconnect by the Field Coordinator. The Field Coordinator **MUST NOT** auto-resolve cross-agent conflicts — `acknowledge()` raises `PermissionError` when invoked by an actor whose id starts with `field-coordinator-` while the conflict is in the `field_coordinator_queued` state.
5. **Reversible flag** — `feature.multi_agent_conflict_detection.enabled` (Reversible per A12). When disabled, agents revert to single-agent behaviour and `conflict_group_id` is not populated; the flag flip itself emits a `multi_agent_coordination_disabled` audit event and is reversible mid-incident per Spec 029 FR-008 (5-minute SLO).

## Rationale

- **Why post-return, not streaming?** Determinism. Streaming-time detection necessarily reads partial responses, which would require either replaying partial token streams (huge audit cost) or accepting non-determinism (which violates Principle IV). Post-return detection runs against the final canonical response and the same `retrieved_chunks[] + prompt_sha` that the audit row already holds.
- **Why a rule-based detector, not an LLM judge?** An LLM-based judge would itself produce a non-deterministic verdict and would need its own audit chain. The rule set (4 classes) is small and inspectable; new classes can be added behind feature flags as operational experience grows.
- **Why a verb-antagonism allow-list, not free text?** The verb table is the *only* source of false positives for spatial/temporal conflicts. Constraining to a curated, reviewed list is conservative — under-detection is acceptable (operators still see both recommendations); over-detection would drown the Ops Officer.
- **Why a separate Cosmos container for the log?** `conflictDetectionLog` is partitioned by `conflict_group_id`, not by tenant or agent, so colocating it in an existing container would either misalign partitioning or force composite keys. A dedicated container with two composite indexes (`(class, detected_at)` and `(state, detected_at)`) keeps both Ops-Officer dashboard queries and after-action review queries cheap.
- **Why 5 minutes for Ops Officer unack?** Mirrors Spec 029 FR-008 fast-burn breach SLO. Operators trained on that timer transfer.
- **Why explicit Field-Coordinator opt-out?** The Field Coordinator's role under FR-RAG-LS-02 (ADR 14) is to make local resource decisions; cross-agent arbitration sits in IC's authority by AIIMS doctrine. The PermissionError makes the boundary uncircumventable.

## Consequences

**Positive**
- Operators see typed conflicts with shared `conflict_group_id` linkage; Ops Officer carries tactical resolution authority; IC carries unacked cases.
- Deterministic replay preserved — every conflict event is reproducible from the persisted audit + retrieval inputs.
- Field Coordinator offline boundary aligns with ADR 14 (audit shape) and FR-RAG-LS-02; no covert auto-resolution path.
- New conflict classes can be added by extending `detect_conflicts()` and the verb table without schema or container changes.

**Negative / mitigations**
- Detector latency adds ~ 50 ms p95 per pair of recommendations. Mitigated by short-circuiting on quick checks (resource id, hazard type) before expensive bbox math.
- The verb-antagonism table is curated and necessarily incomplete. Mitigated by Reversible flag (operators can disable detection if false positives spike during a novel incident type) and by the F-A11 dashboard surfacing detector firing rate.
- `conflictDetectionLog` storage grows linearly with operational tempo. Mitigated by `defaultTtl=-1` (TTL-on-document) and a quarterly archival job.

## Cross-references

- Cluster A9 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-03, Pass 2 Q-P2-06 / Q-P2-08 in spec.md Sessions 4 + 5.
- Schema `contracts/conflict_detection.schema.json`.
- ADR 14 for offline-decision boundary audit fields.
- Tasks T225–T231; Bicep at `infra/bicep/modules/cosmos-conflict-detection.bicep`.
- Plan phase F-A9 in `specs/036-foundry-rag-grounding/plan.md`.

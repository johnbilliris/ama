# Research: Communication Agent

**Phase 0 output** | **Date**: 2026-04-18 | **Spec**: [spec.md](spec.md)

## R-001: Multilingual Translation Strategy — Azure OpenAI with temperature=0

**Decision**: Use Azure OpenAI with `temperature=0` for deterministic LLM-based translation. Generate en-AU first as the reference, then translate to each target language sequentially using the en-AU content as context.

**Rationale**: Temperature=0 ensures reproducible translations for the same input, which is critical for audit trail consistency and commander review. Sequential generation with en-AU as reference ensures semantic consistency across all languages — the same factual content, urgency level, and action items appear in every translation. This matches the existing `LLMCallMixin._generate_with_fallback()` pattern used by all other agents.

**Alternatives considered**:
- **Parallel LLM calls (all 6 languages simultaneously)**: Faster but makes semantic consistency harder to enforce; rejected because each non-English translation must reference the en-AU output
- **Azure Translator API (neural machine translation)**: More cost-effective for bulk translation but lacks context-awareness for emergency alert domain terminology; may produce overly literal translations of Australian emergency terminology
- **Pre-translated templates only (no LLM)**: Most reliable but cannot adapt to dynamic situations; used as fallback only

## R-002: Back-Translation Quality Validation — Cosine Similarity of Embeddings

**Decision**: After generating each non-English translation, translate it back to English using the same LLM, then compute cosine similarity between the original en-AU embedding and the back-translated embedding. Threshold: 0.85 (configurable). If below threshold, flag for review but do NOT block. Apply 0.9× confidence penalty.

**Rationale**: Back-translation is an established technique for assessing translation quality without human reviewers. Cosine similarity of dense embeddings (from Azure OpenAI embedding model) captures semantic equivalence even when surface-level wording differs. The 0.85 threshold balances quality assurance against operational speed — during a disaster, a slightly imperfect translation is better than a delayed alert.

**Alternatives considered**:
- **BLEU/ROUGE scores**: Token-overlap metrics that miss semantic equivalence (e.g., synonyms score poorly); not suitable for cross-lingual quality checks
- **Human-in-the-loop review for every translation**: Too slow for 20s SLA during active disasters; reserved for offline template approval process
- **Skip quality validation entirely**: Unacceptable for safety-critical public-facing content; constitutional requirement for safe degradation

**Embedding outage handling (CHK051)**: When the embedding service is unavailable, skip the back-translation check entirely, use the LLM-generated translation as-is (or template if LLM unavailable), and log a `degradation_detected` audit record. This ensures alert flow is never blocked by an auxiliary quality check.

## R-003: Content Safety Validation Scope

**Decision**: All LLM-generated content MUST pass through `ContentSafetyValidator` (from `apps/agents/common/content_safety.py`). Pre-approved static template text is EXEMPT from runtime validation (pre-vetted through git PR approval process per CHK014/CHK068).

**Rationale**: LLM output is non-deterministic (even at temperature=0, model updates can change output), so runtime safety validation is essential. Template text is human-reviewed and version-controlled, making runtime checks redundant and wasteful of SLA budget. This distinction reduces the 20s drafting SLA pressure — only LLM-generated content incurs the validation overhead.

**Alternatives considered**:
- **Validate everything including templates**: Wastes ~1s per language on pre-vetted text; rejected to preserve SLA budget
- **Validate nothing and trust LLM**: Unacceptable for public-facing safety-critical content; constitutional violation (Principle V)
- **Separate content safety service**: Over-engineered for current scale; the existing `ContentSafetyValidator` module is sufficient

## R-004: AIIMS Approval Workflow — Escalation Chain Design

**Decision**: Max 3 escalation levels. If the primary commander doesn't respond within 15 minutes (configurable), escalate to the next-in-chain commander. After 3 levels with no response, hold the alert with a `CRITICAL` priority flag for the next available commander. NEVER auto-approve (CHK019).

**Rationale**: The AIIMS framework establishes a clear hierarchy of command. Auto-approval would violate the Constitution's mandate that "operational authority remains with designated incident management roles" and the system "MUST NOT exceed configured decision rights." A 3-level cap prevents infinite escalation chains while ensuring the alert remains visible with maximum urgency. The "hold with CRITICAL flag" pattern ensures eventual human review without autonomous publication.

**Alternatives considered**:
- **Unlimited escalation depth**: Could cascade indefinitely in a chaotic disaster; rejected for predictability
- **Auto-approve after timeout**: Violates Constitution Principle I (human override mandate) and AIIMS governance; explicitly prohibited
- **Single commander, no escalation**: Too brittle — if the one commander is incapacitated, alerts stall indefinitely

**Escalation chain configuration**: The AIIMS hierarchy is configured via the incident management system (external). The Communication Agent queries the incident record for the escalation chain. Chain order is determined by AIIMS role hierarchy: Operations Officer → Deputy Incident Controller → Incident Controller.

## R-005: Multi-Part SMS — Concatenated SMS for 612-Character Messages

**Decision**: Use multi-part (concatenated) SMS via Azure Communication Services. FR-028's 612-character maximum = 4-part message (153 usable chars per segment in multi-part mode due to UDH header). Log the segment count in each `DeliveryRecord` (CHK034).

**Rationale**: Standard SMS is 160 characters in GSM-7 encoding, but multi-part SMS uses a User Data Header (UDH) that reduces each segment to 153 usable characters. 612 chars ÷ 153 = 4 segments. Azure Communication Services handles segmentation transparently — the SDK accepts the full message and manages segment assembly/delivery. Logging segment count is important for cost tracking and delivery monitoring.

**Alternatives considered**:
- **Truncate to 160 characters**: Loses critical safety information; rejected because emergency alerts must be complete and actionable
- **Truncate with URL link**: Requires infrastructure for hosted alert pages and assumes recipients have internet access during a disaster — not reliable in remote/low-connectivity Australian environments
- **MMS with rich content**: Not supported by Azure Communication Services SDK in current version; also not universally supported on recipient devices

## R-006: Audience Segment Deduplication at Delivery Time

**Decision**: Recipients that appear in multiple audience segments (e.g., Zone 1 + vulnerable population) receive ONE alert per channel. The highest-priority segment wins (CHK041). Deduplication happens at delivery time, not at segmentation time, to preserve full segment metadata for commander review.

**Rationale**: A hospital in Zone 1 appears in both the "Zone 1 immediate danger" segment and the "vulnerable-population hospital" segment. Sending duplicate alerts causes confusion and degrades trust. Deduplicating at delivery time (rather than segmentation time) allows the commander to see the full audience analysis (all segments) while ensuring recipients aren't overwhelmed. Highest-priority wins ensures the most urgent variant is delivered.

**Alternatives considered**:
- **Deduplicate at segmentation time**: Commander loses visibility into overlapping populations; rejected for transparency
- **Allow duplicates**: Creates alert fatigue and confusion during disasters; rejected per Constitution Principle V
- **Merge segments**: Loses the distinct urgency levels and delivery priorities per segment; rejected for operational clarity

## R-007: Compound Confidence Penalty Stacking Order

**Decision**: Confidence penalties stack multiplicatively in deterministic order: freshness penalty → back-translation penalty (0.9×) → LLM fallback penalty (0.8×) (CHK031). Starting confidence is 1.0 for base LLM-generated content.

**Rationale**: Multiplicative stacking (rather than additive) ensures each penalty proportionally reduces confidence without risk of negative values. The deterministic order (freshness → back-translation → fallback) ensures reproducible confidence scores for the same conditions. Example: if all three penalties apply, confidence = 1.0 × freshness_factor × 0.9 × 0.8. This matches the resource allocation agent's confidence reduction pattern.

**Alternatives considered**:
- **Additive penalties**: Risk of negative confidence; harder to reason about cumulative effect
- **Minimum-of-all penalties**: Discards compounding information; a single low factor dominates regardless of other issues
- **No stacking — only worst penalty**: Loses information about multiple quality issues occurring simultaneously

## R-008: Alert Template Governance — Git-Based Version Control

**Decision**: Templates are version-controlled in git at `data/alert-templates/`. Any change requires a PR review. No runtime governance mechanism (CHK014/CHK068). Template files are static JSON, one per language.

**Rationale**: Git-based governance is simpler, more auditable, and more reliable than a runtime template management system. PRs provide a natural review process where operational stakeholders and translators can approve changes. Templates change infrequently (new hazard types, translation improvements), so the overhead of a PR-based process is acceptable. Runtime governance would add complexity for a feature that changes rarely.

**Alternatives considered**:
- **Database-stored templates with admin UI**: Over-engineered; introduces another data store dependency and runtime change risk during disasters
- **Template files with file-system watching**: Risky — file changes during a disaster could introduce untested content
- **Hardcoded templates in source code**: Less accessible to non-developer translators; makes template-only updates require code deployment

**Missing template fallback (CHK008)**: If a template file for a supported language is missing at startup, the agent falls back to en-AU templates for that language and appends "[Translation unavailable]" to the alert content. The missing template is logged as a startup warning.

## R-009: Commander Authentication on Approval Endpoints

**Decision**: Commander identity validated via JWT claims with `role=commander` (CHK059). The JWT is issued by the platform's identity provider (Azure Entra ID via managed identity). Full RBAC (role-based access control with granular permissions) deferred to v2.

**Rationale**: JWT-based authentication provides a secure, stateless mechanism for verifying commander identity on the `POST /alerts/{alert_id}/approve` and `POST /alerts/{alert_id}/reject` endpoints. Azure Entra ID integration is already established in the platform. Deferring full RBAC to v2 avoids premature abstraction — for v1, the binary `role=commander` check is sufficient since the AIIMS hierarchy is simple.

**Alternatives considered**:
- **API key authentication**: Not suitable for user-specific audit trails; cannot trace approval to individual commander
- **Full RBAC with permission matrix**: Over-engineered for v1 where only commanders approve alerts; deferred to v2 when multi-role support is needed
- **No authentication (trust dashboard)**: Unacceptable — approval endpoint is safety-critical; must verify commander identity

## R-010: Auto-Scaling Strategy — Queue Depth Triggers

**Decision**: Scale out when Service Bus queue depth > 10 messages. Scale in when queue depth < 3 for 5 consecutive minutes (CHK062). Azure Container Apps handles the scaling infrastructure.

**Rationale**: Each alert requires 6 LLM calls (one per language) plus back-translation checks, making the Communication Agent more computationally intensive per handoff than upstream agents. A queue depth of 10 is a conservative trigger — with 50 concurrent alert capacity per instance, scaling at 10 provides headroom before capacity is reached. The 5-minute cooldown for scale-in prevents flapping during bursty disaster events.

**Alternatives considered**:
- **CPU/memory-based scaling**: LLM calls are I/O-bound (waiting for Azure OpenAI), so CPU metrics don't accurately reflect load; queue depth is a more direct indicator
- **Scale at queue depth > 1**: Too aggressive; single alerts are handled well by one instance
- **No auto-scaling (fixed instances)**: Wasteful during quiet periods; insufficient during major disasters

## R-011: Superseded vs Expired — Independent State Semantics

**Decision**: `superseded` and `expired` are independent, non-overlapping terminal states (CHK024). `superseded` means replaced by a newer version of the same alert for the same incident. `expired` means the alert's TTL has passed (default 24 hours, configurable via `ALERT_EXPIRY_HOURS`). An alert can only be in one terminal state.

**Rationale**: These two concepts serve different purposes: `superseded` reflects the alert versioning lifecycle (a newer version exists), while `expired` reflects a time-based safety mechanism (old alerts should not remain active indefinitely). Keeping them independent ensures clear semantics — a superseded alert was explicitly replaced, while an expired alert simply aged out. Both are terminal states (no further transitions).

**Alternatives considered**:
- **Single `inactive` state for both**: Loses the reason for deactivation; complicates audit analysis
- **Expired as a sub-state of superseded**: Conflates two distinct triggers; makes it unclear whether a newer version exists
- **No expiry (alerts active indefinitely)**: Dangerous — stale evacuation orders could persist long after a disaster ends

## R-012: SLA Budget Allocation — 60-Second End-to-End

**Decision**: The 60s end-to-end SLA (SC-011) is allocated as: 20s alert drafting (6 LLM calls + back-translation + content safety) + 5s approval notification (Service Bus publish) + 10s delivery initiation (first channel begins) = 35s pipeline time + 25s buffer for queue processing overhead, serialisation, and Cosmos DB persistence (CHK035).

**Rationale**: The 25s buffer accounts for: Service Bus message delivery latency (~2-5s), Cosmos DB write latency (~3-5s), template loading and interpolation (~1-2s), audience segmentation computation (~2-3s), and operational variance during peak load. The 20s drafting SLA is the tightest constraint — it must accommodate 6 sequential LLM calls (~2-3s each), up to 5 back-translation checks (~1-2s each), and content safety validation (~0.5s each). If all languages use templates (fallback mode), drafting completes in < 5s.

**Alternatives considered**:
- **Parallel LLM calls to reduce drafting time**: Would break en-AU-first sequential generation required for semantic consistency
- **Tighter 30s end-to-end target**: Insufficient buffer for peak-load queue processing; risks SLA violations during major disasters
- **No explicit SLA breakdown**: Makes performance debugging impossible; SLA violations would be undiagnosable

## R-013: Delivery Record Segment Count for Multi-Part SMS

**Decision**: Each `DeliveryRecord` for SMS delivery includes a `segment_count` field (integer) recording the number of SMS segments used. Calculated as `ceil(len(message) / 153)` for multi-part messages or `1` for messages ≤ 160 chars in GSM-7 encoding.

**Rationale**: Multi-part SMS incurs per-segment costs from Azure Communication Services. Tracking segment count per delivery enables: cost monitoring (4× cost for 612-char messages), delivery time estimation (multi-part SMS may have slightly higher latency), and audit trail completeness. The formula uses 153 chars per segment (GSM-7 multi-part) rather than 160 chars (single-segment) because multi-part SMS requires a UDH header in each segment.

**Alternatives considered**:
- **Track only total character count**: Loses the actual cost multiplier; requires post-hoc calculation
- **Track only delivery success/failure**: Insufficient for cost analysis and capacity planning
- **Always assume single-segment**: Incorrect for 612-char messages; would undercount costs by 4×

## R-014: Concurrent Approval Conflict Resolution

**Decision**: If two commanders attempt to approve/reject the same alert simultaneously (CHK018), the first write wins (Cosmos DB optimistic concurrency via etag). The second commander receives a 409 Conflict response indicating the alert has already been actioned, with the current status and actioning commander ID returned in the response body.

**Rationale**: Concurrent approval is unlikely in practice (alerts are typically assigned to a specific commander in the AIIMS hierarchy), but must be handled gracefully. Optimistic concurrency via Cosmos DB etag is already the established pattern for alert versioning. Returning a 409 with context allows the second commander to see who already approved/rejected and take no further action.

**Alternatives considered**:
- **Last write wins**: Could silently override a rejection with an approval; dangerous for safety-critical alerts
- **Locking mechanism**: Over-engineered for a rare scenario; introduces deadlock risk and complexity
- **Queue all approval actions**: Adds latency to the approval workflow; the first action is almost always the intended one

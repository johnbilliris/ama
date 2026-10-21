# Feature Specification: Communication Agent — Multilingual Alert Generation, Content Safety, AIIMS Approval, and Multi-Channel Public Dissemination

**Feature Branch**: `008-communication-agent`  
**Created**: 2026-04-18  
**Status**: Draft  
**Input**: User description: "The Communication Agent is the 5th and final agent in the disaster-response multi-agent system. It receives risk assessments and generates multilingual public alerts. Supported languages: en-AU (primary), zh-Hans, ar, vi, el, it. Must integrate content safety validation before any public-facing output. AIIMS-aligned approval workflow — commander must approve before public dissemination. Delivery channels: SMS, push notifications, emergency broadcast. Template-based alert generation with LLM enhancement. Three-tier audit degradation pattern. Audience segmentation by geographic zone, vulnerability, language preference. Must handle alert versioning (updates, corrections, all-clear notifications). Port: 8084."

## Clarifications

### Session 2026-04-12

- Q: What translation approach should be used for multilingual alert generation? → A: Azure OpenAI with temperature=0 for deterministic translation. Pre-approved template translations stored as static JSON for fallback. LLM translates dynamically when available; template translations used when LLM unavailable. Quality validation via back-translation check (translate back to English, compare semantic similarity).
- Q: What scope should content safety validation cover — LLM-generated text only or also template text? → A: All LLM-generated AND all template-generated text must pass ContentSafetyValidator before approval queue. Check for: inappropriate content, culturally insensitive language, panic-inducing phrasing, inaccurate safety instructions. Use same content_safety module from `apps/agents/common/`.
- Q: What is the approval workflow for multilingual alerts — per-language or all-at-once? → A: Commander receives alert draft with all language variants. Can approve (all languages), reject (with reason), or request modifications. Approval applies to ALL language variants simultaneously — no per-language approval. Auto-escalation if no response within 15 minutes (configurable). Escalation goes to next-in-chain commander, NOT auto-approve.
- Q: What specific delivery channel SDKs/protocols should be used? → A: SMS via Azure Communication Services SDK. Push notifications via Azure Notification Hubs. Emergency broadcast is a webhook POST to the EAS endpoint (configurable URL). Each channel has independent retry logic (3 retries, exponential backoff). Delivery receipts tracked per channel per recipient segment.
- Q: How are audience segments defined and what is the default language? → A: Segments defined by: geographic zone (polygon from evacuation agent zones), vulnerability category (from risk assessment), preferred language. Each segment gets the alert in their preferred language. Default language is en-AU if preference unknown. Segment size estimation for delivery planning.
- Q: What are the alert lifecycle states and transitions? → A: States: `drafting` → `pending_review` → `approved` → `delivering` → `delivered` → `superseded`/`expired`. Also: `rejected` (from pending_review), `cancelled` (from any pre-delivered state). Updates create new version; previous version moves to `superseded`. All-clear is a special alert type that references the original alert.
- Q: What deduplication pattern should be used? → A: TTL-based LRU cache on handoff message IDs (same pattern as other agents). Prevent duplicate alerts for same incident+hazard combination within configurable window (default 30 minutes).
- Q: What are the SLA targets for alert processing? → A: Alert drafting: 20s from handoff receipt to draft completion. Approval notification: 5s to commander. Delivery initiation: 10s after approval. End-to-end (handoff to first delivery): 60s excluding approval wait time.
- Q: What port does the Communication Agent use? → A: 8084, following the sequence (monitoring=8080, risk=8081, evacuation=8082, resource=8083).
- Q: What health endpoint fields should be reported? → A: Same pattern as other agents. Report: llm_connectivity, cosmos_connectivity, sms_service_status, push_service_status, broadcast_endpoint_status, pending_approvals_count, active_deliveries_count.

### Session 2026-04-12 — Pass 2

- Q: What semantic similarity threshold should be used for back-translation quality checks, and what happens when it fails? → A: Semantic similarity ≥ 0.85 (cosine similarity of embeddings). If below threshold, flag translation for human review but do NOT block alert delivery. Log as audit decision with confidence penalty of 0.9× (multiplicative).
- Q: What is the structure for alert templates? → A: Static JSON files per language in `data/alert-templates/`. Structure: `{template_id, hazard_type, severity, language_code, title_template, body_template, action_items_template}`. Templates use `{placeholder}` syntax for dynamic values (location, time, severity). One file per language: `en-AU.json`, `zh-Hans.json`, `ar.json`, `vi.json`, `el.json`, `it.json`.
- Q: What is the delivery retry logic per channel? → A: Per-channel independent retry. Max 3 retries with exponential backoff (1s, 2s, 4s). If all retries fail for a channel, mark as `failed` in DeliveryRecord, continue with other channels. Never block other channels due to one channel failure. Alert-level delivery status = `partially_delivered` if any channel fails.
- Q: How is the commander notified for approval? → A: Commander notified via dedicated Service Bus queue (`commander-approval-queue`). Commander interacts via web dashboard (`apps/web/`). Approval/rejection received via POST endpoint on the communication agent. Include alert preview with all language variants in the approval request payload.
- Q: How do all-clear alerts work? → A: Special alert type `all_clear` referencing original alert ID. Delivered to same audience segments as original alert. Uses dedicated all-clear templates per hazard type. Automatically supersedes the referenced alert upon delivery.
- Q: How are alert corrections handled? → A: Create new alert version with `correction` flag. Previous version moves to `superseded`. Corrections require commander approval (same workflow). Correction alerts include "CORRECTION:" prefix in all languages and reference the original alert.
- Q: What observability metrics should be emitted? → A: alert_draft_latency, translation_latency, content_safety_check_latency, approval_wait_time, delivery_latency_per_channel, delivery_success_rate_per_channel, back_translation_quality_score, audience_segment_count, active_alerts_count, template_fallback_rate, escalation_count.
- Q: What is the LLM fallback behavior for translation? → A: When Azure OpenAI unavailable, use pre-approved static template translations. Reduce confidence by 20% (multiplicative, 0.8 factor). Log as `template_fallback` decision type. Static template text is pre-approved and does NOT need runtime content safety validation (reverting FR-014 for pre-vetted static templates).
- Q: How should concurrent alerts be handled? → A: Support 50 concurrent alerts (NFR-001). Each alert independent — no cross-alert coordination. Use asyncio for concurrent processing. Queue overflow beyond 50 returns 429 Too Many Requests.
- Q: What plan versioning format should be used? → A: Same pattern as other agents — `ca-{incident_id}-v{N}` with optimistic concurrency via Cosmos DB etag.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Receive Handoff and Draft Multilingual Public Alert (Priority: P1)

A severe cyclone is approaching a populated coastal region in Far North Queensland. The Risk Assessment Agent has produced a high-confidence hazard assessment and generated a `public_alert` recommendation with confidence ≥ 0.7. It escalates a handoff to the Communication Agent. The Communication Agent receives the handoff, retrieves the referenced recommendation and hazard assessment data, identifies the affected geographic zone and community demographics, and drafts a multilingual public alert. The alert is generated in all six supported languages (en-AU as primary, zh-Hans, ar, vi, el, it) using LLM-enhanced text with a template-based fallback. Each language version passes through content safety validation before being included in the alert. The alert is created in `pending_review` status and presented to the incident commander for review and approval. The commander can trace the alert back to the risk assessment and the signals that triggered it.

**Why this priority**: This is the Communication Agent's core function — the final step in the disaster response pipeline that translates risk assessments into actionable public guidance. Without this capability, the entire upstream pipeline (monitoring → risk assessment → communication) produces no public-facing output. The Constitution (Principle V) mandates multilingual, accessible, actionable alerts, and (Principle I) mandates content safety for all safety-critical outputs.

**Independent Test**: Can be fully tested by sending a synthetic `AgentHandoffEvent` with `source_agent=risk_assessment`, `target_agent=communication`, and a payload containing a recommendation ID, summary, and explanation, then verifying that the agent produces a `PublicAlert` record with content blocks in all six languages, `status=pending_review`, content safety validation results, and traceability references to the originating recommendation.

**Acceptance Scenarios**:

1. **Given** an `AgentHandoffEvent` arrives from the Risk Assessment Agent with a payload containing a `public_alert` recommendation ID, summary, and explanation for a cyclone scenario, **When** the Communication Agent processes the handoff, **Then** it produces a `PublicAlert` record containing: content blocks in all six supported languages (en-AU, zh-Hans, ar, vi, el, it), `status=pending_review`, audience segments derived from the affected area, delivery channels, accessibility attributes, and traceability references (recommendation ID, incident ID).
2. **Given** the LLM generates alert text for a specific language that fails content safety validation (blocked keyword, language mismatch, or length exceeded), **When** the Communication Agent drafts the alert, **Then** the failing language version is replaced with the pre-approved template text, the alert's `content_safety_result` reflects the fallback, and the content safety failure is recorded in the audit trail.
3. **Given** the LLM service is unavailable, **When** the Communication Agent drafts the alert, **Then** all language versions use template-based text with `generation_method=template_fallback`, the alert is still created with `status=pending_review`, and a degradation event is logged.
4. **Given** multiple handoffs arrive for the same incident within a short time window, **When** the Communication Agent processes each handoff, **Then** each successive alert receives a monotonically increasing version number for that incident and the previous alert version is marked as `superseded`.

---

### User Story 2 — AIIMS-Aligned Commander Approval Workflow (Priority: P2)

A bushfire alert has been drafted by the Communication Agent and is awaiting approval. The incident commander reviews the alert on their dashboard, seeing the content in all six languages, the audience segments that will receive it, the delivery channels that will be used, and the risk assessment that triggered the alert. The commander can approve the alert for immediate dissemination, reject it with a justification, or request modifications. Only after commander approval does the alert transition to `approved` status and become eligible for public delivery. The entire approval workflow — including who approved, when, and any modifications — is recorded in the audit trail.

**Why this priority**: The Constitution (Principle I) mandates human override for any autonomous action, and the AIIMS framework requires that public alerts be approved by the designated incident commander before dissemination. Without this approval workflow, the system would bypass incident management governance and potentially disseminate incorrect or premature warnings. The Constitution explicitly states the platform MUST NOT exceed configured decision rights.

**Independent Test**: Can be fully tested by creating a `PublicAlert` in `pending_review` status, submitting an approval action with a user ID and role, and verifying that the alert transitions to `approved` status with the approval metadata recorded in both the alert record and the audit trail.

**Acceptance Scenarios**:

1. **Given** a `PublicAlert` exists with `status=pending_review`, **When** an incident commander approves the alert with their user ID and role, **Then** the alert transitions to `approved` status, the approval is recorded with `approved_by_user_id`, `approved_by_role`, and `approved_at` timestamp, and an audit record captures the approval action.
2. **Given** a `PublicAlert` exists with `status=pending_review`, **When** an incident commander rejects the alert with a justification, **Then** the alert transitions to `rejected` status, the rejection reason is recorded, and no delivery is initiated.
3. **Given** a `PublicAlert` exists with `status=pending_review`, **When** an incident commander requests modifications (e.g., adjusting audience segments or rewording a content block), **Then** a new alert version is created incorporating the changes, the original alert remains intact for audit, and the new version enters `pending_review` status.
4. **Given** a `PublicAlert` exists with `status=approved`, **When** the agent receives new information that would change the alert content, **Then** the agent produces a new alert version but does NOT automatically supersede the approved alert — the new version is presented for commander review.

---

### User Story 3 — Multi-Channel Alert Delivery (Priority: P3)

An incident commander has approved a bushfire evacuation alert. The Communication Agent initiates delivery across the configured channels: SMS messages to affected residents, push notifications to users of the emergency app, and emergency broadcast integration for the affected geographic area. Each channel receives the alert content in the appropriate format and language based on recipient preferences. The delivery status for each channel is tracked, and the commander can see which channels have been successfully delivered, which are pending, and which have failed.

**Why this priority**: Alert generation without delivery is ineffective. The Constitution (Principle V) mandates support for multiple delivery channels including SMS, push notifications, and broadcast integrations. Multi-channel delivery ensures maximum reach, particularly in disaster-affected areas where some communication infrastructure may be degraded.

**Independent Test**: Can be fully tested by creating an `approved` alert, triggering the delivery process, and verifying that delivery records are created for each configured channel with the appropriate content format, delivery status tracking, and language-specific content.

**Acceptance Scenarios**:

1. **Given** a `PublicAlert` with `status=approved` and `channel_set=["sms", "push", "emergency_broadcast"]`, **When** delivery is initiated, **Then** a delivery record is created for each channel with `status=pending`, the content is formatted according to each channel's constraints (e.g., SMS character limits), and each delivery record references the alert ID and version.
2. **Given** an SMS delivery is initiated for a geographic zone where recipients have different language preferences, **When** the SMS is dispatched, **Then** each recipient receives the alert in their preferred language from the alert's content blocks.
3. **Given** a delivery attempt to a channel fails (e.g., SMS gateway timeout), **When** the failure is detected, **Then** the delivery record is updated with the failure reason, the agent retries delivery up to a configurable maximum (default: 3 retries), and a degradation event is logged. If all retries are exhausted, the failure is surfaced to the incident commander.
4. **Given** an emergency broadcast channel is included in the delivery, **When** the broadcast is initiated, **Then** only the en-AU content is used for broadcast (broadcast systems use the primary language only), and the delivery record notes the language used.

---

### User Story 4 — Audience Segmentation by Zone, Vulnerability, and Language (Priority: P4)

A major flood event is affecting a large metropolitan area with diverse communities. The Communication Agent must segment the affected audience to ensure the right people receive the right information through the right channels. Residents in the immediate flood zone (Zone 1) receive urgent evacuation orders. Residents in Zone 2 receive preparation warnings. Vulnerable populations (elderly care facilities, hospitals, schools) receive additional guidance specific to their needs. Language preferences from demographic data determine which language version each segment receives. The incident commander can review the audience segmentation before approving the alert to ensure appropriate targeting.

**Why this priority**: Untargeted mass alerts cause alert fatigue, panic in unaffected areas, and fail to provide specific guidance to those who need it most. The Constitution (Principle V) mandates audience segmentation, and (Principle I) mandates that life-safety considerations — including vulnerability — drive communication priorities.

**Independent Test**: Can be fully tested by providing an affected area with known geographic zones, vulnerability data (care facilities, schools), and language demographics, and verifying that the agent produces audience segments with appropriate zone-based priority, vulnerability flags, and language assignments.

**Acceptance Scenarios**:

1. **Given** a hazard assessment identifies three geographic zones (Zone 1: immediate danger, Zone 2: likely impact, Zone 3: possible impact), **When** the Communication Agent segments the audience, **Then** each zone is assigned a separate audience segment with appropriate urgency level (Zone 1: `immediate`, Zone 2: `watch`, Zone 3: `advisory`).
2. **Given** the affected area contains a registered aged care facility with 80 residents, **When** the Communication Agent segments the audience, **Then** the facility is included in a `vulnerable-population` segment with `priority=critical` and additional guidance about facility-specific evacuation procedures.
3. **Given** demographic data indicates 15% of residents in Zone 1 prefer zh-Hans, **When** the Communication Agent assigns languages to segments, **Then** the zh-Hans content block is designated as the primary content for that sub-segment and en-AU is included as a secondary fallback.
4. **Given** no demographic or vulnerability data is available for a zone, **When** the Communication Agent segments the audience, **Then** all residents in the zone receive the en-AU version by default, the missing data is logged, and the alert summary notes that segmentation is limited.

---

### User Story 5 — Alert Versioning: Updates, Corrections, and All-Clear (Priority: P5)

A bushfire situation is evolving over 48 hours. The initial alert warned residents of Zone 1 to evacuate. Six hours later, wind direction changes and the fire front shifts, requiring an updated alert with revised zones. Twelve hours later, an error is discovered in the original zone mapping, requiring a correction alert. Finally, when the fire is contained, an all-clear notification is issued. Each alert version is linked to its predecessor, clearly identifies whether it is an update, correction, or all-clear, and includes a change summary so recipients and commanders understand what changed and why. All versions remain in the audit trail, and no previous version is modified.

**Why this priority**: Disaster situations are dynamic. Alerts that cannot be updated, corrected, or concluded leave communities with stale information. The Constitution (Principle III) mandates versioned, traceable outputs. Alert versioning ensures that the public always has the most current guidance while maintaining a complete audit trail for post-incident review.

**Independent Test**: Can be fully tested by creating an initial alert, then issuing an update (changed zones), a correction (fixed error), and an all-clear, verifying that each version has a monotonically increasing version number, a clear change type indicator, a change summary, and that all previous versions remain queryable.

**Acceptance Scenarios**:

1. **Given** an active published alert exists for an incident, **When** the Communication Agent receives a new handoff with updated hazard data, **Then** it produces a new alert version with `change_type=update`, a change summary describing what differs from the previous version, and the previous version is marked as `superseded`.
2. **Given** an active published alert contains incorrect information (e.g., wrong zone boundary), **When** an incident commander requests a correction, **Then** the Communication Agent produces a new alert version with `change_type=correction`, the correction reason is recorded, and the corrected content clearly identifies itself as a correction to recipients.
3. **Given** the hazard has passed and an incident commander issues an all-clear, **When** the Communication Agent generates the all-clear notification, **Then** a new alert version is produced with `change_type=all_clear`, the content explicitly states that the threat has passed and any evacuation orders are lifted, and the previous alert is marked as `superseded`.
4. **Given** an alert has been through multiple versions (v1 through v4), **When** the incident commander reviews the alert history, **Then** all versions are queryable with their respective change types, change summaries, approval records, and timestamps.

---

### User Story 6 — Content Safety Validation Before Public Dissemination (Priority: P6)

During an active disaster, the LLM generates alert text that inadvertently includes a blocked keyword or produces content that fails language validation (e.g., text intended for zh-Hans is detected as English). The Communication Agent's content safety validation catches the issue before the alert reaches the commander for approval. The failing content is replaced with pre-approved template text, the failure is logged in the audit trail, and the commander is informed that one or more language versions used fallback content. The alert is still produced and enters the approval workflow — no alert is silently dropped due to content safety failures.

**Why this priority**: The Constitution (Principle I) mandates safe degradation for safety-critical outputs, and (Principle V) requires that alerts be accurate and appropriate. Content safety validation is the final safeguard before public-facing content reaches the approval stage. Without it, harmful, misleading, or incorrectly localised content could reach the commander for approval.

**Independent Test**: Can be fully tested by configuring a mock LLM to return text containing a blocked keyword for one language and valid text for others, then verifying that the blocked language version uses template fallback, the other languages use LLM text, and the content safety result is recorded per language.

**Acceptance Scenarios**:

1. **Given** the LLM generates alert text for en-AU that passes all content safety checks (no blocked keywords, correct language, within length), **When** the content safety validator runs, **Then** the en-AU content block uses the LLM-generated text and `content_safety_result=passed`.
2. **Given** the LLM generates alert text for ar that contains a blocked keyword, **When** the content safety validator runs, **Then** the ar content block is replaced with the pre-approved template text, the overall `content_safety_result` reflects the fallback, and the failure reason (`blocked_keyword`) is recorded in the audit trail.
3. **Given** the LLM generates text intended for zh-Hans but the output contains no Chinese characters, **When** the content safety validator runs, **Then** the zh-Hans content block is replaced with template text, the failure reason (`language_mismatch`) is recorded, and the alert is still produced.
4. **Given** all six language versions fail content safety validation, **When** the Communication Agent drafts the alert, **Then** all content blocks use template fallback text, `generation_method=safety_fallback`, and the alert is still created with `status=pending_review` rather than being dropped.

---

### User Story 7 — Audit Trail of All Communication Decisions (Priority: P7)

After a multi-day flood response, the post-incident review team requests a complete record of every alert drafted, every content safety evaluation, every approval decision, every delivery attempt, every audience segmentation decision, every version transition, and every degradation event. The review team retrieves a chronological log with timestamps, inputs, outputs, content safety results, approval metadata, delivery outcomes, and the reasoning behind each decision. Every alert can be traced back to the recommendation and signals that triggered it.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates an append-only audit trail for safety-critical recommendations and actions. Public alerts directly affect community safety. Complete traceability is essential for post-incident reviews, coronial inquiries, media accountability, regulatory compliance, and continuous improvement.

**Independent Test**: Can be fully tested by processing a sequence of handoffs resulting in alerts with various outcomes (approved, rejected, updated, corrected, all-clear), then querying the audit trail to verify that every processing step has a corresponding record with all required fields.

**Acceptance Scenarios**:

1. **Given** the Communication Agent processes any incoming handoff, **When** the processing completes, **Then** an audit record is created containing: handoff ID, recommendation ID, alert ID (if produced), decision type, content safety results per language, generation method, and timestamp.
2. **Given** an incident commander approves or rejects an alert, **When** the approval action is recorded, **Then** an audit record captures the commander's user ID, role, action (approve/reject/modify), justification (if reject), and timestamp.
3. **Given** alert delivery is attempted across channels, **When** each delivery completes or fails, **Then** an audit record captures the channel, delivery status, recipient segment, language used, retry count, and any failure reason.
4. **Given** the audit trail storage degrades (primary unavailable), **When** audit records are generated, **Then** they are written to the next available tier (in-memory buffer or local file) and the degradation transition is itself recorded as an audit event.

---

### User Story 8 — Graceful Degradation When Services Are Unavailable (Priority: P8)

During a major disaster, the LLM service used for generating alert content becomes temporarily unavailable. Simultaneously, one of the delivery channels (SMS gateway) experiences intermittent failures. The Communication Agent continues to draft alerts using template-based content for all languages, marks the alerts with reduced confidence and `generation_method=template_fallback`, and proceeds through the normal approval workflow. For delivery, the agent retries failed SMS deliveries and, after exhausting retries, reports the SMS channel as degraded while continuing delivery on other available channels. When services recover, the agent resumes normal LLM-enhanced generation and SMS delivery. Throughout the outage, all degradation events are logged.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates that the system continue operating with reduced functionality when services are unavailable. During a disaster — when communication is most critical — the Communication Agent must never halt entirely. Template-based alerts are preferable to no alerts.

**Independent Test**: Can be fully tested by disabling the LLM client and SMS gateway, sending handoffs to the agent, and verifying that alerts are still produced with template fallback, delivery proceeds on available channels, degradation events are logged, and recovery is handled when services are restored.

**Acceptance Scenarios**:

1. **Given** the LLM service is unavailable, **When** the Communication Agent drafts an alert, **Then** all language versions use template text with `generation_method=template_fallback`, confidence is reduced, and the degradation is logged.
2. **Given** the LLM service becomes available again, **When** the next alert is drafted, **Then** the agent resumes LLM-enhanced generation with `generation_method=llm` and logs the recovery event.
3. **Given** an SMS delivery channel fails after exhausting retries, **When** the failure is recorded, **Then** the agent marks the SMS channel as degraded, continues delivery on push notification and emergency broadcast channels, and surfaces the SMS failure to the incident commander.
4. **Given** the primary audit storage is unavailable, **When** audit records are generated, **Then** they are written to the in-memory buffer tier, and when primary storage recovers, buffered records are flushed to primary storage.

---

### Edge Cases

- What happens when a handoff arrives referencing a recommendation ID that does not exist in the data store? The agent logs the error, records a `handoff_rejected` audit entry with the reason, and does not produce an alert.
- What happens when the same handoff ID is received more than once (duplicate delivery)? The agent performs idempotency checking on handoff ID and discards duplicates, logging the discard in the audit trail.
- What happens when a handoff arrives from a simulation tenant? The agent processes the handoff in the simulation context, produces alerts isolated from live data, and does not trigger real delivery to public channels.
- What happens when the LLM generates content that exceeds the maximum output token budget? The content is truncated per the `LLMCallMixin` token budget enforcement, then passed through content safety validation. If truncation produces incoherent text, content safety catches the language mismatch and falls back to template text.
- What happens when an SMS message exceeds the channel's character limit (e.g., 160 characters for standard SMS)? The Communication Agent truncates the SMS content to fit within channel constraints, ensuring the message remains actionable (what is happening, what to do, where to get help). Multi-part SMS is used for longer messages where the channel supports it.
- What happens when all delivery channels fail simultaneously? The agent records all failures, marks the alert delivery as `failed`, surfaces the failure to the incident commander with maximum urgency, and logs a critical degradation event. The alert remains approved and can be retried when channels recover.
- What happens when a commander approves an alert but the alert's underlying recommendation has since been superseded by a newer assessment? The agent presents a warning to the commander noting the newer assessment exists but does not block the approval — the commander retains authority to publish the alert as approved.
- What happens when an all-clear notification is requested but there are still active alerts for sub-zones within the incident area? The agent validates that the all-clear scope matches the incident scope, warns the commander if active alerts exist for sub-zones, and requires explicit confirmation before generating the all-clear.
- What happens when the Communication Agent itself becomes unhealthy? The health endpoint reports unhealthy status, the hosting platform detects the failure and restarts the agent, and unprocessed handoffs are re-delivered from the messaging infrastructure.

## Requirements *(mandatory)*

### Functional Requirements

#### Handoff Intake and Validation

- **FR-001**: The Communication Agent MUST consume `AgentHandoffEvent` records where `target_agent=communication` from the Risk Assessment Agent via the messaging infrastructure. The agent MUST acknowledge receipt of each handoff within 5 seconds of delivery. The agent MUST validate the handoff structure and reject malformed handoffs with an audit record.
- **FR-002**: Upon receiving a valid handoff, the Communication Agent MUST retrieve the referenced recommendation and hazard assessment from the data store using the IDs provided in the handoff payload (`recommendationId`, `assessmentId`).
- **FR-003**: The Communication Agent MUST perform idempotency checking using a TTL-based LRU cache on handoff message IDs (same deduplication pattern as other agents). Duplicate handoffs within the deduplication window (default: 30 minutes, configurable via environment variable `HANDOFF_DEDUP_WINDOW_MINUTES`) MUST be discarded and the discard recorded in the audit trail. Additionally, the agent MUST prevent duplicate alerts for the same `incident_id` + `hazard_type` combination within the deduplication window.
- **FR-004**: The Communication Agent MUST validate that the `incident_id` referenced in the handoff exists in the incident store. If the incident does not exist, the handoff MUST be rejected with a `rejected_handoff` audit record.

#### Multilingual Alert Drafting

- **FR-005**: The Communication Agent MUST draft alert content in all six supported languages: en-AU (primary), zh-Hans, ar, vi, el, and it. The set of supported languages MUST be configurable via environment variable `SUPPORTED_LANGUAGES` (default: `en-AU,zh-Hans,ar,vi,el,it`).
- **FR-006**: For each language, the Communication Agent MUST generate alert text using the `_generate_with_fallback` method from `LLMCallMixin`, which attempts LLM-enhanced generation first and falls back to template text if the LLM is unavailable or content safety validation fails. Translation MUST use Azure OpenAI with `temperature=0` for deterministic, consistent output. Pre-approved template translations MUST be stored as static JSON files (one per alert type) and used as fallback when the LLM is unavailable. Quality validation MUST be performed via a back-translation check: translate the generated non-English text back to English and compare semantic similarity (cosine similarity of embeddings) against the original en-AU source. If similarity falls below a configurable threshold (default: 0.85, configurable via environment variable `BACK_TRANSLATION_THRESHOLD`), the language version MUST be flagged for human review but MUST NOT block alert delivery. The flagged translation MUST be logged as an audit decision of type `back_translation_below_threshold` and a confidence penalty of 0.9× (multiplicative) MUST be applied to that language version's confidence score. If the language version's quality is insufficient for operational needs, the pre-approved static JSON template translation MAY be substituted by the commander during approval review.
- **FR-006a**: Per Constitution (Principle III), the Communication Agent MUST consider data freshness when computing alert confidence. The effective confidence MUST be calculated using multiplicative compound penalty stacking applied in deterministic order: (1) freshness penalty (default factor: 0.9×, configurable via `FRESHNESS_PENALTY_FACTOR`) when the upstream hazard assessment data age exceeds a staleness threshold, (2) back-translation penalty (0.9×) when any language version's back-translation score falls below `BACK_TRANSLATION_THRESHOLD`, and (3) LLM fallback penalty (0.8×) when template fallback is used. The formula is: `effectiveConfidence = confidenceScore × freshnessScore × backTranslationPenalty × fallbackPenalty`, where each penalty defaults to 1.0 when not triggered.
- **FR-007**: Alert content MUST be concise, actionable, and structured following the Constitution (Principle V) format: what is happening, where, when, what to do, and where to get help. Each language version MUST convey the same semantic content.
- **FR-008**: The en-AU version MUST be generated first and serve as the reference for all other language versions. The LLM prompt for non-primary languages MUST include the en-AU content as context to ensure semantic consistency across translations.
- **FR-009**: The Communication Agent MUST support a configurable maximum output token budget per language (default: 180 tokens, configurable via environment variable `ALERT_MAX_TOKENS`). If the LLM output exceeds the budget, the `LLMCallMixin` token budget enforcement truncates the output before content safety validation.

#### Content Safety

- **FR-010**: All LLM-generated alert content MUST pass through the `ContentSafetyValidator` (from `apps/agents/common/content_safety.py`) before inclusion in any alert record or entry into the approval queue. Pre-approved static template text is exempt from runtime content safety validation (see FR-014). Validation of LLM-generated content MUST check for: inappropriate content, culturally insensitive language, panic-inducing phrasing, inaccurate safety instructions, blocked keyword filtering, expected language detection, and maximum length enforcement (default: 1,200 characters per language block).
- **FR-011**: If content safety validation fails for any language version, the failing language's content block MUST be replaced with the pre-approved template text. The alert MUST still be produced — content safety failures for individual languages MUST NOT block alert creation.
- **FR-012**: The overall `content_safety_result` on the alert record MUST reflect the worst-case outcome across all language versions: `passed` only if all languages passed, `failed_with_fallback` if any language required fallback, `not_checked` only if content safety could not be performed.
- **FR-013**: All LLM interactions MUST use system prompts that scope the model's role to emergency alert drafting and MUST NOT allow the model to be repurposed via prompt injection from recommendation or signal content.
- **FR-014**: Pre-approved static template text is pre-vetted and does NOT require runtime `ContentSafetyValidator` checks. Templates are maintained via an offline approval process and any template change requires re-approval before deployment. The default template text MUST be configurable per alert type (evacuation, shelter-in-place, all-clear, general warning). Templates are stored as static JSON files in `data/alert-templates/`, one file per language (`en-AU.json`, `zh-Hans.json`, `ar.json`, `vi.json`, `el.json`, `it.json`). Each template entry MUST conform to the structure: `{template_id, hazard_type, severity, language_code, title_template, body_template, action_items_template}`. Templates use `{placeholder}` syntax for dynamic values (e.g., `{location}`, `{time}`, `{severity}`). Only dynamically generated (LLM-produced) content requires runtime content safety validation.

#### Alert Versioning

- **FR-015**: Each `PublicAlert` MUST include a version number using the format `ca-{incident_id}-v{N}` where N starts at 1 and increases monotonically per incident (consistent with the agent prefix pattern used by other agents). Version assignment MUST use optimistic concurrency control via Cosmos DB etag to prevent conflicts during concurrent alert generation.
- **FR-016**: Alert versions MUST be immutable once persisted. New alerts create new versions; existing versions MUST NOT be overwritten. Status-only transitions (`pending_review` → `approved`/`rejected`/`superseded`/`cancelled`) are the sole permitted mutation on existing records.
- **FR-017**: Each alert version MUST include a `change_type` field indicating the nature of the version: `initial` (first alert for an incident), `update` (changed situation), `correction` (error fix), or `all_clear` (threat has passed). Correction alerts MUST include the prefix "CORRECTION:" in the alert title across all language versions and MUST reference the original alert ID being corrected. Corrections require commander approval via the same approval workflow as initial alerts. All-clear alerts MUST reference the original alert ID, MUST be delivered to the same audience segments as the original alert, MUST use dedicated all-clear templates per hazard type (from `data/alert-templates/`), and MUST automatically supersede the referenced alert upon delivery.
- **FR-018**: When a new alert version is created, the previous active version for the same incident MUST be marked as `superseded`. The new version MUST include a `change_summary` field describing what changed from the previous version and why.

#### AIIMS-Aligned Approval Workflow

- **FR-019**: All public alerts MUST be created with `status=pending_review`. The Communication Agent MUST NOT autonomously publish any alert without incident commander approval. This is consistent with the AIIMS framework where the designated incident controller authorises public information.
- **FR-020**: Incident commanders MUST be able to perform the following actions on a `PublicAlert`: (a) **approve** — transitions alert to `approved` and makes it eligible for delivery (approval applies to ALL language variants simultaneously; there is no per-language approval), (b) **reject** — transitions alert to `rejected` with a mandatory justification, (c) **modify** — creates a new alert version incorporating the commander's changes, which enters `pending_review` status. Each action MUST record `approved_by_user_id`, `approved_by_role`, `approval_action`, `approval_justification` (for reject), and `approved_at` timestamp. The commander receives the alert draft with all language variants for review. Commander notification MUST be delivered via a dedicated Azure Service Bus queue (`commander-approval-queue`). The approval request payload MUST include a full alert preview with all language variants, audience segments, and delivery channels. The commander interacts via the existing web dashboard (`apps/web/`). Approval and rejection responses MUST be received via a POST endpoint on the Communication Agent (e.g., `POST /alerts/{alert_id}/approve` and `POST /alerts/{alert_id}/reject`).
- **FR-021**: Only alerts with `status=approved` are eligible for delivery. The delivery process MUST NOT be triggered for alerts in any other status.
- **FR-042**: If an alert in `pending_review` status receives no commander response within 15 minutes (configurable via environment variable `APPROVAL_ESCALATION_TIMEOUT_MINUTES`), the agent MUST auto-escalate to the next-in-chain commander as defined by the AIIMS incident management hierarchy. Auto-escalation MUST NOT auto-approve the alert. The escalation event MUST be recorded in the audit trail with the original commander ID, escalation target commander ID, and elapsed time.

#### Audience Segmentation

- **FR-022**: The Communication Agent MUST segment the target audience for each alert based on three dimensions: (a) **geographic zone** — derived from the hazard assessment's affected area using zone polygons provided by the Evacuation Agent, with segments for each impact zone (immediate danger, likely impact, possible impact), (b) **vulnerability** — identifying known vulnerable populations (aged care facilities, hospitals, schools, disability services) from risk assessment data within the affected area, and (c) **language preference** — derived from demographic data for the affected area. Each segment receives the alert in its preferred language.
- **FR-023**: Each audience segment MUST include: segment ID, geographic zone (zone level and boundary polygon), population estimate, vulnerability flags (list of vulnerability categories), preferred language, urgency level (`immediate`, `watch`, or `advisory`), the delivery channels appropriate for the segment, and an estimated segment size for delivery planning purposes.
- **FR-024**: Vulnerable population segments MUST receive `priority=critical` and MUST be delivered before general population segments. This aligns with the Constitution's Life Safety First principle.
- **FR-025**: When demographic or vulnerability data is unavailable for a geographic zone, the Communication Agent MUST default to: en-AU (Australian English) as the language — the default when language preference is unknown — no vulnerability flags, and general population treatment. The missing data MUST be logged and noted in the alert summary.

#### Multi-Channel Delivery

- **FR-026**: The Communication Agent MUST support delivery across three channels: (a) **SMS** via Azure Communication Services SDK, (b) **push notifications** via Azure Notification Hubs, and (c) **emergency broadcast** via a webhook POST to the Emergency Alert System (EAS) endpoint (configurable URL via environment variable `EAS_ENDPOINT_URL`). The set of active channels MUST be configurable per environment via `DELIVERY_CHANNELS` (default: `sms,push,emergency_broadcast`). Each channel MUST have independent retry logic (default: 3 retries with exponential backoff). Delivery receipts MUST be tracked per channel per recipient segment.
- **FR-027**: For each approved alert, the Communication Agent MUST create a `DeliveryRecord` for each channel-segment combination, tracking: delivery ID, alert ID, alert version, channel, audience segment ID, language used, delivery status (`pending`, `in_progress`, `delivered`, `failed`, `retrying`), attempt count, and timestamps.
- **FR-028**: SMS delivery MUST respect channel-specific constraints: maximum message length (configurable, default: 612 characters for multi-part SMS), actionable content format (what is happening, what to do, emergency contact), and recipient language preference. Messages exceeding the limit MUST be truncated with an appended link to full alert details.
- **FR-029**: Emergency broadcast delivery MUST use the en-AU content block only (primary language). Broadcast content MUST be formatted according to the emergency broadcast channel's requirements.
- **FR-030**: Delivery attempts that fail MUST be retried up to a configurable maximum (default: 3 retries, configurable via `DELIVERY_MAX_RETRIES`) with exponential backoff using intervals of 1 second, 2 seconds, and 4 seconds. Retry logic MUST be per-channel independent — a failure in one channel (e.g., SMS) MUST NOT block or delay delivery attempts on other channels (e.g., push, emergency broadcast). If all retries are exhausted for a channel, the delivery record for that channel MUST be marked as `failed` and the failure MUST be surfaced to the incident commander. The alert-level delivery status MUST be set to `partially_delivered` if any channel fails while others succeed. Only when all channels succeed is the alert-level status set to `delivered`.
- **FR-031**: The Communication Agent MUST track aggregate delivery metrics per alert: total segments targeted, total deliveries attempted, successful deliveries, failed deliveries, and delivery completion percentage. These metrics MUST be available for commander review.

#### Audit Trail

- **FR-032**: The Communication Agent MUST produce an audit record for every processing step, including: handoff receipt, handoff rejection, duplicate discard, alert drafting, content safety evaluation (per language), alert versioning, approval actions, delivery initiation, delivery success, delivery failure, audience segmentation, degradation events, and health status changes.
- **FR-033**: Each audit record MUST be append-only (no updates or deletes) and MUST include: record ID, handoff ID (when applicable), alert ID (when applicable), decision type, content safety results, generation method, agent version, configuration version, processing duration, and timestamp.
- **FR-034**: The audit trail MUST use a three-tier storage degradation pattern: (1) **primary** — durable, queryable storage for production use; (2) **secondary** — in-memory buffer when primary storage is unavailable, flushed to primary upon recovery; (3) **tertiary** — local file fallback when both primary and memory buffer are exhausted. The current audit write tier MUST be reported via the `/health` endpoint's `audit_store` field. Degradation transitions MUST be logged as audit events themselves.
- **FR-035**: All outbound alerts MUST be logged with audience, content, time, channel, and approval mode (human-approved vs. autonomous) per Constitution (Principle V).

#### Graceful Degradation

- **FR-036**: When the LLM service (Azure OpenAI) is unavailable, the Communication Agent MUST fall back to pre-approved static template translations from `data/alert-templates/`. Confidence MUST be reduced by a multiplicative factor of 0.8 (20% reduction, consistent with other agents' degradation pattern). All fallback outputs MUST carry `generation_method=template_fallback`. The fallback MUST be logged as a `template_fallback` decision type in the audit trail. Pre-approved static template text does NOT require runtime content safety validation (templates are pre-vetted through an offline approval process).
- **FR-037**: When one or more delivery channels are unavailable, the Communication Agent MUST continue delivering through available channels. Failed channels MUST be reported to the incident commander with specific failure details.
- **FR-038**: The Communication Agent MUST expose a `/health` endpoint on port 8084 (following the agent port sequence: monitoring=8080, risk=8081, evacuation=8082, resource=8083, communication=8084) that reports agent readiness. The health response MUST include: `llm_connectivity` (LLM service reachability), `cosmos_connectivity` (data store reachability), `sms_service_status` (Azure Communication Services SMS health), `push_service_status` (Azure Notification Hubs health), `broadcast_endpoint_status` (EAS webhook endpoint reachability), `pending_approvals_count` (number of alerts in `pending_review` status), `active_deliveries_count` (number of deliveries currently in progress), `processing_queue_depth` (number of pending handoffs), and `audit_store` (current audit write tier: primary/secondary/tertiary). The endpoint MUST respond within 1 second under normal operation. This follows the same health endpoint pattern as other agents in the system.
- **FR-039**: The Communication Agent MUST NOT halt entirely when any single dependency (LLM, delivery channel, data store) is unavailable. It MUST continue processing with degraded capabilities and log all degradation events.

#### Simulation and Tenant Isolation

- **FR-040**: The Communication Agent MUST support processing handoffs in simulation tenant contexts per spec 007. Alerts produced in simulation MUST be isolated from live data and MUST NOT trigger delivery to real public channels.
- **FR-041**: Simulation alerts MUST be clearly labelled with the simulation tenant identifier in all records and MUST NOT appear in live incident queries.

### Non-Functional Requirements

#### Scalability

- **NFR-001**: The Communication Agent MUST handle at minimum 50 concurrent alert drafting operations during peak disaster events. Each alert MUST be processed independently with no cross-alert coordination required. The agent MUST use `asyncio` for concurrent processing of alert drafting, translation, and delivery workflows. If the processing queue exceeds 50 concurrent alerts, the agent MUST return HTTP 429 Too Many Requests for incoming handoffs until capacity is available. This is comparable to the Evacuation Agent's capacity because each alert requires LLM calls for six languages, making it more computationally intensive per unit than upstream agents. Horizontal scaling via auto-scaling MUST be used based on message queue depth.

#### Observability

- **NFR-002**: The Communication Agent MUST emit telemetry for operational monitoring. The following metrics MUST be tracked: `alert_draft_latency` (time from handoff receipt to alert draft completion, reported as p50, p95, p99), `translation_latency` (time per language translation including back-translation check), `content_safety_check_latency` (time for content safety validation per language), `approval_wait_time` (time from alert creation to commander approval or rejection), `delivery_latency_per_channel` (time from approval to delivery completion, broken down by channel), `delivery_success_rate_per_channel` (percentage of delivery attempts succeeding, broken down by channel), `back_translation_quality_score` (semantic similarity score distribution for back-translation checks), `audience_segment_count` (number of audience segments generated per alert), `active_alerts_count` (current number of active alerts gauge), `template_fallback_rate` (percentage of alerts using template fallback vs. LLM generation per time window), and `escalation_count` (number of approval escalations per time window). All metrics MUST support alerting thresholds.

#### Multi-Region Deployment

- **NFR-003**: Per the Constitution (Principle VI), the Communication Agent MUST be deployable to Azure regions within Australia. Each regional deployment MUST operate independently with no cross-region data leakage — alerts processed in one region MUST NOT be visible to or affect the other region's processing.

### Key Entities

- **PublicAlert**: A versioned, multilingual public alert drafted by the Communication Agent for incident commander approval and public dissemination. Key attributes: alert ID (format: `ca-{incident_id}-v{N}`, consistent with agent prefix pattern), incident ID, version number (monotonically increasing per incident, optimistic concurrency via Cosmos DB etag), status (lifecycle: `drafting` → `pending_review` → `approved` → `delivering` → `delivered` | `partially_delivered` → `superseded` | `expired`; also `rejected` from `pending_review`, `cancelled` from any pre-delivered state; `partially_delivered` indicates at least one delivery channel failed while others succeeded), change type (`initial`, `update`, `correction`, `all_clear`), change summary (what changed from previous version), referenced alert ID (for `correction` and `all_clear` types — the original alert being corrected or cleared), correction prefix ("CORRECTION:" prepended to title in all languages for `correction` type), approval mode (`human_approved`, `escalated`), audience segments (list of segment IDs), languages (list of supported language codes), accessibility attributes (e.g., `plain-language`), channel set (list of delivery channels), content blocks (language code → alert text mapping), generation method (`llm`, `template`, `template_fallback`, `safety_fallback`), model deployment ID, content safety result (`passed`, `failed_with_fallback`, `not_checked`), content safety details (per-language results), approval metadata (`approved_by_user_id`, `approved_by_role`, `approval_action`, `approval_justification`, `approved_at`), recommendation ID (traceability to triggering recommendation), assessment ID (traceability to hazard assessment), published at timestamp, and created/updated timestamps. Alerts are immutable once persisted; updates create new versions and the previous version moves to `superseded`. All-clear is a special alert type that references the original alert ID, is delivered to the same audience segments as the original, uses dedicated all-clear templates per hazard type, and automatically supersedes the referenced alert upon delivery. Status transitions are the only permitted mutation.

- **AudienceSegment**: A targeted group of recipients for a public alert, defined by geographic, vulnerability, and language dimensions. Key attributes: segment ID, alert ID, geographic zone (zone level: 1/2/3, zone boundary polygon from evacuation agent zones), population estimate, estimated segment size (for delivery planning), vulnerability categories (list: aged care, hospital, school, disability services — empty for general population), preferred language (ISO language code from the six supported languages; defaults to en-AU if preference unknown), urgency level (`immediate`, `watch`, `advisory`), priority (`critical` for vulnerable populations, `high`/`moderate` for general population by zone), and assigned delivery channels.

- **DeliveryRecord**: A tracking record for a single delivery attempt of an alert to a specific audience segment via a specific channel. Key attributes: delivery ID, alert ID, alert version, channel (`sms`, `push`, `emergency_broadcast`), audience segment ID, language used, delivery status (`pending`, `in_progress`, `delivered`, `failed`, `retrying`), attempt count, max retries (default: 3), retry backoff intervals (1s, 2s, 4s exponential), failure reason (if failed), content payload (channel-formatted version of alert text), initiated at timestamp, completed at timestamp, and delivery duration. Retry logic is per-channel independent — a failure in one channel does not affect other channels' delivery attempts.

- **CommunicationDecisionRecord**: An audit trail entry capturing a single processing step or decision made by the Communication Agent. Key attributes: record ID, handoff ID (when applicable), alert ID (when applicable), delivery ID (when applicable), decision type (handoff_received, handoff_rejected, duplicate_discarded, alert_drafted, content_safety_evaluated, alert_versioned, approval_action, delivery_initiated, delivery_succeeded, delivery_failed, audience_segmented, degradation_detected, content_safety_failure, health_status_changed), content safety results (per-language breakdown), generation method, processing duration, agent version, configuration version, and timestamp. Append-only; no updates or deletes permitted.

- **AgentHandoffEvent**: An explicit handoff record consumed by the Communication Agent from the Risk Assessment Agent. Key attributes: handoff ID, incident ID, source agent (`risk_assessment`), target agent (`communication`), scope key, confidence, payload (containing recommendation ID, summary, explanation, and assessment ID), tenant ID, status, retry count, and timestamps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Public alert drafting (template loading, multilingual LLM generation, back-translation validation, and content safety checks — pipeline stages 4–7) MUST complete within 20 seconds. The full pipeline from handoff receipt through alert persistence and approval notification MUST complete within 35 seconds (see contracts/communication-pipeline.md for per-stage latency budgets). If drafting exceeds 20 seconds, the alert MUST still complete but MUST log a processing delay event.
- **SC-002**: 100% of LLM-generated alert content passes through content safety validation before being included in any alert record — no LLM-generated public-facing content bypasses the safety check. Pre-approved static template text is exempt from runtime content safety validation (pre-vetted through offline approval process).
- **SC-003**: 100% of public alerts require incident commander approval before delivery — no alert is autonomously published without human authorisation.
- **SC-004**: Alert delivery reaches at least 95% of targeted audience segments within 5 minutes of commander approval, across all configured channels.
- **SC-005**: When the LLM service is unavailable, the Communication Agent continues producing alerts using template fallbacks within 20 seconds, with no processing interruption — measured as 0% handoff drop rate during LLM outage periods.
- **SC-006**: Every processing step has a corresponding audit record — audit completeness is 100% verifiable via reconciliation of handoff IDs processed vs. audit records created.
- **SC-007**: The health endpoint responds within 1 second under normal operation, enabling container orchestration to detect failures and restart the agent within the platform's configured health check interval.
- **SC-008**: At least 90% of incident commanders in scenario-based exercises rate the multilingual alert content as clear, actionable, and appropriately targeted, using a structured post-exercise survey.
- **SC-009**: Approval notification is delivered to the incident commander within 5 seconds of alert draft completion.
- **SC-010**: Delivery initiation begins within 10 seconds of commander approval.
- **SC-011**: End-to-end latency from handoff receipt to first delivery completion MUST be ≤ 60 seconds (excluding approval wait time).

## Assumptions

- The Risk Assessment Agent (spec 012) delivers handoffs in the `AgentHandoffEvent` format with payload containing `recommendationId`, `summary`, `explanation`, and `assessmentId`. The Communication Agent does not re-assess risk — it consumes the recommendation and assessment as provided.
- Recommendations arriving at the Communication Agent have already been filtered by the Risk Assessment Agent's escalation threshold (confidence ≥ 0.7 for public alerts per spec 012 FR-020). The Communication Agent does not re-evaluate escalation eligibility.
- The LLM client uses Azure OpenAI with `temperature=0` for deterministic translation output and content safety filters enabled. The `_generate_with_fallback` method from `LLMCallMixin` provides the primary generation pattern with automatic template fallback. Translation quality is validated via back-translation semantic similarity check. When Azure OpenAI is unavailable, pre-approved static JSON template translations apply with 20% confidence reduction (multiplicative factor 0.8).
- The six supported languages (en-AU, zh-Hans, ar, vi, el, it) represent the most commonly spoken community languages in disaster-affected Australian regions. The language set is configurable for future expansion.
- Audience segmentation relies on demographic and vulnerability data available from the data store (spec 006). For MVP, if demographic data is unavailable, the agent defaults to en-AU for all recipients and logs the data gap.
- SMS delivery via Azure Communication Services SDK, push notifications via Azure Notification Hubs, and emergency broadcast integration via webhook POST to the EAS endpoint are the three delivery channels for MVP. Each channel has independent retry logic (3 retries, exponential backoff at 1s, 2s, 4s intervals). A failure in one channel never blocks delivery on other channels. Delivery receipts are tracked per channel per recipient segment. Alert-level delivery status is `partially_delivered` if any channel fails while others succeed. Additional channels (e.g., social media, email, digital signage) may be added in future iterations.
- Template-based fallback text is pre-approved by operational stakeholders and does NOT undergo runtime content safety validation (pre-vetted through offline approval process). Templates are stored as static JSON files in `data/alert-templates/` (one file per language: `en-AU.json`, `zh-Hans.json`, `ar.json`, `vi.json`, `el.json`, `it.json`) and exist for each alert type (evacuation, shelter-in-place, all-clear, general warning) with translations for all six supported languages. Each template entry uses the structure `{template_id, hazard_type, severity, language_code, title_template, body_template, action_items_template}` with `{placeholder}` syntax for dynamic values. Any template change requires re-approval before deployment.
- The AIIMS approval workflow requires `incident_commander` as the default required approval level. The system supports but does not replace human authority over public alert dissemination.
- Tenant isolation (simulation vs. live) is enforced at the data layer per spec 007. The Communication Agent respects tenant boundaries for all alerts, deliveries, and audit records. Simulation alerts MUST NOT trigger real public delivery.
- Handoff delivery from the Risk Assessment Agent uses the same messaging infrastructure as other agent-to-agent communication, with at-least-once delivery semantics. The Communication Agent handles duplicate delivery via a TTL-based LRU cache on handoff message IDs (same deduplication pattern as other agents), with a default 30-minute deduplication window.
- The Communication Agent listens on port 8084 for health checks and any direct API interactions.

### Out of Scope

- Replacement of incident commander authority over public alert publication. The Communication Agent proposes alerts; human commanders approve them.
- Translation quality assurance — the agent generates translations via LLM but does not perform professional human translation review. Template fallback text is assumed to be professionally translated.
- Management of recipient contact databases — the agent segments audiences and initiates delivery but does not manage phone number registries, push notification tokens, or subscriber lists.
- Real-time delivery tracking with per-recipient acknowledgment — the agent tracks delivery status at the channel-segment level, not individual recipient level.
- Social media posting or monitoring — the agent delivers through SMS, push, and emergency broadcast only. Social media integration is deferred to a future iteration.
- Alert content for Aboriginal and Torres Strait Islander languages — recognised as important by the Constitution but deferred to a future iteration when appropriate language resources and community consultation can be completed.
- Direct integration with the Australian Emergency Alert system — emergency broadcast delivery is modelled as a channel interface; the specific integration with government emergency alert infrastructure is an operational concern outside the agent's scope.

### Dependencies

- **spec 001 (Disaster Response Hub)**: Defines the PublicAlert, Recommendation, AgentHandoffEvent, and TimelineEvent data models that the Communication Agent operates on.
- **spec 005 (Data Source Governance)**: Defines the data source registry that informs demographic and vulnerability data used for audience segmentation.
- **spec 006 (Data Ingestion & Storage)**: Defines the data store from which the Communication Agent retrieves recommendation, assessment, and demographic data.
- **spec 007 (Simulation & Tenant Isolation)**: Defines the tenant isolation model that the Communication Agent must respect for simulation vs. live processing and delivery.
- **spec 012 (Risk Assessment Agent)**: Defines the upstream agent that produces handoffs consumed by the Communication Agent. The handoff payload format (`recommendationId`, `summary`, `explanation`, `assessmentId`) and escalation criteria (confidence ≥ 0.7 for public alerts) are defined in spec 012.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-016**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-017**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-018** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-006**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/008-communication-agent/evidence/HYP-006.md`.

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-019** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (public-information-officer, accessibility-tester, ai-ml-engineer) sign off on country-specific calibration.
- **SCP-020**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-021**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.

## Capstone-Aligned Requirements (Feature 028 / FR-006)

- **FR-CAP-008-001** [DEFERRED]: Multilingual language-pack plugin support with at least one non-English language pack per capstone country: **Philippines** (Filipino + regional languages), **Japan** (Japanese), **Bangladesh** (Bangla). Each language pack has the following preconditions: (i) content-safety classifier in target language; (ii) human back-translation audit on >=1 % of public-facing alerts; (iii) accessibility QA per `specs/020-disaster-mapper-ui` and the accessibility-tester actor.
  - **BCP-47 identifier selection is deferred to research.md** per clarification Q2 / D-004; no concrete identifier (`fil-PH` / `ja-JP` / `bn-BD`) is hard-coded in this spec.
- **FR-CAP-008-002** [DEFERRED]: Multilingual misinformation-detection inherits the spec-010 fallback rule (when language-specific classifier confidence is below threshold, fall back to the conservative English-baseline classifier and flag for human review).
- **FR-CAP-008-003**: `defers-to:` 018 (warning-tier approval timeout escalation; spec 018 is authoritative for portfolio-wide escalation timeout per FR-017 / T045).
- **FR-CAP-008-004**: `supersedes:` `specs/006-data-ingestion-storage/spec.md` FR-024 (warning-tier multilingual authoring + delivery - formally relocated here per FR-016 / T044).

## Capstone-Country Hypotheses (Feature 028 / US2)

> Three deferred capstone-country hypotheses for multilingual public alerting + misinformation detection. Each cites an evidence stub at `specs/008-communication-agent/evidence/HYP-<id>.md` conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. `Status = Not tested` until D-009 capstone-reinterpretation clears and per-cohort preconditions are met.

- **HYP-027** [PH deferred]: We believe a Filipino + regional-language pack with content-safety classifier and human back-translation audit will produce true-positive misinformation detection >= 85% on known PH samples and alert delivery confirmation latency p95 <= 60s for the Philippines operator persona; we will know we are wrong if true-positive rate < 70% on the labelled fil-PH validation corpus during PH typhoon season Jun-Nov is observed in the measurement window (PH typhoon season Jun-Nov).
  - **Falsification**: true-positive rate < 70% on the labelled fil-PH validation corpus during PH typhoon season Jun-Nov.
  - **Evidence stub**: `specs/008-communication-agent/evidence/HYP-027.md` (created by feature 028 / US2 / T034..T038).
- **HYP-028** [JP deferred]: We believe a Japanese language pack with JMA-aligned warning-tier templates and content-safety classifier will produce true-positive misinformation detection >= 85% on known JP samples and earthquake-alert delivery latency p95 <= 5s for the Japan operator persona; we will know we are wrong if true-positive rate < 70% on the labelled ja-JP validation corpus or earthquake-alert latency p95 > 10s during quarterly review is observed in the measurement window (JP continuous; quarterly review).
  - **Falsification**: true-positive rate < 70% on the labelled ja-JP validation corpus or earthquake-alert latency p95 > 10s during quarterly review.
  - **Evidence stub**: `specs/008-communication-agent/evidence/HYP-028.md` (created by feature 028 / US2 / T034..T038).
- **HYP-029** [BD deferred]: We believe a Bangla language pack with BMD / FFWC-aligned templates and content-safety classifier will produce true-positive misinformation detection >= 80% on known BD samples and flood-alert delivery latency p95 <= 60s for the Bangladesh operator persona; we will know we are wrong if true-positive rate < 65% on the labelled bn-BD validation corpus during BD monsoon Apr-Sep is observed in the measurement window (BD monsoon Apr-Sep).
  - **Falsification**: true-positive rate < 65% on the labelled bn-BD validation corpus during BD monsoon Apr-Sep.
  - **Evidence stub**: `specs/008-communication-agent/evidence/HYP-029.md` (created by feature 028 / US2 / T034..T038).

## Implementation Contract Resolution (2026-09-17)

The decisions in [contracts/contract-resolution.v2.json](contracts/contract-resolution.v2.json) resolve implementation ambiguities without claiming external operational approval:

- A replacement is persisted first; its predecessor is superseded only after confirmed replacement delivery.
- Deduplication is tenant-scoped and distinguishes in-flight work, completed handoffs, and new authoritative assessment/change identities.
- All failed or unconfigured delivery operations produce `delivery_failed`; provider acceptance remains `delivering` until confirmation.
- SMS truncation preserves required actions and help links and uses GSM-7 or UCS-2 segment limits.
- Embedding outages produce an unmeasured back-translation result and no fabricated confidence penalty.
- Spec 018 owns timeout policy: Emergency Warning uses 5 minutes and lower tiers use 15 minutes; no escalation auto-approves.
- The standalone FastAPI service is the compatibility runtime. MAF integration must invoke its existing safety, persistence, approval, and delivery boundaries rather than replace them.
- Configuration and metric inventories are schema-derived and are not governed by stale fixed-count prose.

Human operational/template approval and Azure deployment evidence remain unverified.

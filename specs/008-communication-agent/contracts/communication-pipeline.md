# Contract: Communication Processing Pipeline — 11-Stage Orchestrator

**Date**: 2026-04-18 | **Spec**: [../spec.md](../spec.md) | **Data Model**: [../data-model.md](../data-model.md)

## Pipeline Overview

The `CommunicationProcessingPipeline` is an 11-stage orchestrator that processes an `AgentHandoffEvent` and produces a `PublicAlert` with multilingual content blocks, audience segments, and delivery records.

**Total latency budget**: 60 seconds end-to-end (excluding approval wait time)

```
Stage 1: Handoff Intake & Validation          [≤ 2s]
Stage 2: Data Retrieval                        [≤ 3s]
Stage 3: Audience Segmentation                 [≤ 3s]
Stage 4: Template Loading & Interpolation      [≤ 1s]
Stage 5: Multilingual Alert Drafting (LLM)     [≤ 15s] (6 languages sequential)
Stage 6: Back-Translation Quality Validation   [≤ 5s]  (5 non-English languages)
Stage 7: Content Safety Validation             [≤ 3s]
Stage 8: Alert Versioning & Persistence        [≤ 3s]
Stage 9: Approval Notification                 [≤ 5s]
                                               ────────
                                  Drafting subtotal: ≤ 24s (stages 4–7)
                                     Pipeline total: ≤ 40s
                                     Queue overhead: ≤ 20s buffer
                                     End-to-end:     ≤ 60s

    [APPROVAL WAIT — excluded from SLA]

Stage 10: Multi-Channel Delivery               [≤ 10s to initiate first channel]
Stage 11: Audit Finalisation                   [≤ 2s]
```

---

## Stage 1: Handoff Intake & Validation

**Input**: `AgentHandoffEvent` from Service Bus `communication-handoffs` queue
**Output**: Validated handoff payload or rejection audit record

**Steps**:
1. Deserialise and validate handoff against Pydantic schema
2. Check deduplication cache (`HandoffDeduplicator`)
   - Duplicate by handoff ID → discard with `duplicate_discarded` audit record
   - Duplicate by `incident_id + hazard_type` within dedup window → discard
3. Validate `incident_id` exists in incident store
4. Validate `target_agent == "communication"`
5. Acknowledge receipt to Service Bus (within 5s per FR-001)
6. Emit `handoff_received` audit record

**Error handling**:
- Malformed handoff → `handoff_rejected` audit record, message dead-lettered
- Incident not found → `handoff_rejected` audit record
- Dedup cache full/restart (CHK056) → accept handoff (fail-open for safety)

---

## Stage 2: Data Retrieval

**Input**: Validated handoff payload (`recommendationId`, `assessmentId`)
**Output**: Recommendation data, hazard assessment data, incident metadata

**Steps**:
1. Retrieve recommendation from Cosmos DB using `recommendationId`
2. Retrieve hazard assessment using `assessmentId`
3. Retrieve incident metadata (zones, demographics) from incident store
4. Snapshot input data for audit reproducibility

**Error handling**:
- Recommendation not found → `handoff_rejected` audit record
- Assessment superseded (CHK054/Edge Case §7) → proceed with warning; commander notified
- Cosmos DB unavailable → fail with `degradation_detected` audit; retry via Service Bus

---

## Stage 3: Audience Segmentation

**Input**: Hazard assessment (affected area, zones), incident demographics
**Output**: `list[AudienceSegment]`

**Steps**:
1. Extract geographic zones from hazard assessment (Zone 1/2/3 from evacuation agent polygons)
2. Create zone-based segments with urgency levels:
   - Zone 1 → `immediate`, priority `high`
   - Zone 2 → `watch`, priority `moderate`
   - Zone 3 → `advisory`, priority `moderate`
3. Identify vulnerable populations within each zone (aged care, hospitals, schools, disability services)
   - Create additional `priority=critical` segments for each vulnerability category
4. Assign language preferences from demographic data
   - Unknown preference → default `en-AU` (FR-025)
5. Assign delivery channels per segment
6. Compute segment size estimates
7. Log missing data flags if demographic/vulnerability data unavailable (CHK042)
8. Emit `audience_segmented` audit record

**Note**: Segments may overlap (CHK041) — deduplication happens at delivery time (Stage 10).

---

## Stage 4: Template Loading & Interpolation

**Input**: Hazard type, severity, alert type, dynamic values from assessment
**Output**: Template text per language (fallback content)

**Steps**:
1. Load template JSON files from `data/alert-templates/{language_code}.json`
2. Select template by `hazard_type + severity + alert_type`
3. Validate all `{placeholder}` values exist in the input data
   - Missing placeholder value → substitute `[unknown]`, log warning (CHK006)
   - Sanitise placeholder values to prevent injection (CHK005)
4. Interpolate placeholders into templates for all languages
5. If template file missing for a language (CHK008) → use en-AU template with `[Translation unavailable]` suffix

**Error handling**:
- Template file not found for language → en-AU fallback + `[Translation unavailable]`
- Template file malformed → startup error (fail-fast)
- All template files missing → startup error (agent cannot start)

---

## Stage 5: Multilingual Alert Drafting (LLM)

**Input**: en-AU template text, hazard context, dynamic values
**Output**: `dict[str, ContentBlock]` — LLM-generated content per language

**Steps**:
1. Generate en-AU content first using `_generate_with_fallback()`:
   - System prompt scopes LLM to emergency alert drafting (FR-013)
   - User prompt includes hazard context, location, severity, action items
   - `temperature=0` for deterministic output
   - `max_output_tokens` per config (default: 180)
2. For each non-English language (zh-Hans, ar, vi, el, it):
   - Generate translation using LLM with en-AU content as context (FR-008)
   - `_generate_with_fallback()` handles LLM failure → template fallback
3. Track `generation_method` per language:
   - `llm`: LLM succeeded and passed content safety
   - `safety_fallback`: LLM succeeded but content safety failed
   - `template_fallback`: LLM unavailable, template used
4. Apply `CORRECTION:` prefix to title if `change_type == correction` (FR-017)

**Latency budget**: ≤ 15s for 6 sequential LLM calls (~2.5s each)

**Error handling**:
- LLM unavailable for all languages → all use template fallback; `generation_method=template_fallback`; confidence × 0.8 (FR-036)
- LLM succeeds for some, fails for others → mixed generation methods; worst-case method recorded on alert

---

## Stage 6: Back-Translation Quality Validation

**Input**: Non-English content blocks, en-AU reference text
**Output**: Back-translation scores per language, flagged translations

**Steps**:
1. For each non-English language with `generation_method=llm`:
   - Translate content back to English using LLM
   - Compute cosine similarity between original en-AU embedding and back-translated embedding
   - If similarity < threshold (default: 0.85) → flag for review, apply 0.9× confidence penalty
   - Record `back_translation_score` on ContentBlock
2. Skip for languages using template text (pre-approved, no quality check needed)
3. Skip entirely if embedding service unavailable (CHK051) → log `degradation_detected`

**Confidence penalty stacking (CHK031)**:
- Applied multiplicatively in order: freshness → back-translation (0.9×) → fallback (0.8×)
- Example: freshness 0.95 × back-translation 0.9 × fallback 0.8 = 0.684

---

## Stage 7: Content Safety Validation

**Input**: LLM-generated content blocks
**Output**: Validated content blocks with safety results

**Steps**:
1. For each language with `generation_method=llm`:
   - Pass through `ContentSafetyValidator.validate()`
   - Check: blocked keywords, language detection, length (≤ 1,200 chars), culturally sensitive content
   - If fails → replace with template text, set `generation_method=safety_fallback`
2. Skip for template-based content (pre-approved, FR-014)
3. Compute overall `content_safety_result`:
   - `passed` if all LLM languages passed
   - `failed_with_fallback` if any language required fallback
   - `not_checked` if content safety could not run
4. Emit `content_safety_evaluated` audit record per language

---

## Stage 8: Alert Versioning & Persistence

**Input**: Complete alert content, segments, safety results
**Output**: Persisted `PublicAlert` with version number

**Steps**:
1. Assign version number via `VersionCounter.assign_version(incident_id)`:
   - Optimistic concurrency via Cosmos DB etag
   - Retry up to 3 times on 412 Precondition Failed (R-014)
2. Generate `alert_id` = `ca-{incident_id}-v{version}`
3. Set `status=pending_review`
4. If previous version exists for incident → mark as `superseded`
5. Persist `PublicAlert` to Cosmos DB `public-alerts` container
6. Persist `AudienceSegment` records
7. Emit `alert_versioned` audit record

---

## Stage 9: Approval Notification

**Input**: Persisted `PublicAlert` in `pending_review` status
**Output**: Commander notification via Service Bus

**Steps**:
1. Build approval request payload:
   - Alert preview with all language variants
   - Audience segment summary
   - Delivery channel configuration
   - Traceability references (recommendation ID, assessment ID)
   - Warning if assessment has been superseded (Edge Case §7)
2. Publish to Service Bus `commander-approval-queue`
3. Start escalation timer (configurable, default: 15 minutes)
4. Emit `approval_requested` audit record

**Escalation flow (asynchronous)**:
1. Timer fires after `APPROVAL_ESCALATION_TIMEOUT_MINUTES`
2. Check if alert is still `pending_review`
3. If `escalation_level < MAX_ESCALATION_LEVELS`:
   - Escalate to next commander in AIIMS chain
   - Emit `escalation_triggered` audit record
   - Restart timer
4. If `escalation_level >= MAX_ESCALATION_LEVELS` (CHK019):
   - Set CRITICAL priority flag on alert
   - Hold for next available commander
   - NEVER auto-approve
   - Emit `escalation_triggered` audit record with `held_for_next_available=True`

---

## Stage 10: Multi-Channel Delivery

**Trigger**: Alert transitions to `approved` status (via POST endpoint)
**Input**: `PublicAlert` with `status=approved`, `AudienceSegment` records
**Output**: `DeliveryRecord` per channel × segment combination

**Steps**:
1. Transition alert to `delivering` status
2. Deduplicate recipients across overlapping segments (CHK041):
   - Group segments by geographic overlap
   - For overlapping recipients, keep highest-priority segment
   - Mark lower-priority segment deliveries as `is_deduplicated=True`
3. Sort delivery order: `priority=critical` (vulnerable) first, then by zone level ascending
4. For each segment × channel combination:
   - Create `DeliveryRecord` with `status=pending`
   - Format content for channel constraints:
     - **SMS**: Truncate to `SMS_MAX_LENGTH` (612 chars); calculate `segment_count = ceil(len/153)`; use recipient's preferred language
     - **Push**: Format as push notification payload with title + body; use recipient's preferred language
     - **Emergency broadcast**: en-AU only (FR-029); format per EAS webhook spec
   - Dispatch delivery with per-channel independent retry:
     - SMS → Azure Communication Services SDK
     - Push → Azure Notification Hubs SDK
     - Broadcast → HTTP POST to `EAS_ENDPOINT_URL`
   - On success: `delivery_status=delivered`, emit `delivery_succeeded` audit
   - On failure: retry with exponential backoff (1s, 2s, 4s); if all retries exhausted, `delivery_status=failed`, emit `delivery_failed` audit
5. Compute alert-level delivery status:
   - All channels succeeded → `delivered`
   - Any channel failed → `partially_delivered`
   - All channels failed → mark alert delivery as `failed`, surface to commander
6. Emit aggregate delivery metrics

**Channel failures are independent** — one channel failing MUST NOT block others (FR-030).

---

## Stage 11: Audit Finalisation

**Input**: Complete processing results (alert, deliveries, decisions)
**Output**: Finalised audit trail

**Steps**:
1. Verify audit completeness — reconcile all expected records against actual records
2. Compute aggregate metrics (total processing time, per-stage latencies)
3. Flush any buffered audit records if primary storage recovered
4. Emit final telemetry events

---

## Approval API Endpoints

These endpoints are called by the web dashboard after the pipeline pauses at Stage 9.

### POST /alerts/{alert_id}/approve

**Authentication**: JWT with `role=commander` claim (CHK059)

**Request**: `{ "user_id": str, "role": str }`
**Response 200**: Alert transitions to `approved`, triggers Stage 10
**Response 409**: Alert already actioned (R-014 concurrent approval handling)
**Response 404**: Alert not found
**Response 403**: Invalid JWT or role

### POST /alerts/{alert_id}/reject

**Authentication**: JWT with `role=commander` claim

**Request**: `{ "user_id": str, "role": str, "justification": str }`
**Response 200**: Alert transitions to `rejected`
**Response 409**: Alert already actioned

### POST /alerts/{alert_id}/modify

**Authentication**: JWT with `role=commander` claim

**Request**: `{ "user_id": str, "role": str, "modifications": dict }`
**Response 200**: New alert version created in `pending_review` status; original remains for audit

---

## Pipeline Invariants

1. **No alert is published without commander approval** — Stage 10 only triggers after explicit approval via POST endpoint
2. **All LLM-generated content passes content safety** — Stage 7 validates before Stage 8 persists
3. **All processing steps produce audit records** — every stage emits at least one `CommunicationDecisionRecord`
4. **Channel failures are independent** — SMS, push, and broadcast retry independently
5. **Template fallback is always available** — even if all LLM calls fail, template content enables alert creation
6. **Deduplication happens at two levels** — handoff level (Stage 1) and delivery level (Stage 10)
7. **Confidence penalties stack deterministically** — freshness → back-translation → fallback (CHK031)
8. **Simulation alerts never trigger real delivery** — tenant isolation checked at Stage 1 and Stage 10

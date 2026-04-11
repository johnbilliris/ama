# Tasks: Communication Agent — Multilingual Alert Generation, Content Safety, AIIMS Approval, and Multi-Channel Public Dissemination

**Input**: Design documents from `/specs/008-communication-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, checklists/communication-agent.md ✅, quickstart.md ✅

**Tests**: Included — plan.md explicitly specifies unit, contract, integration, and simulation tests per phase.

**Organization**: Tasks are grouped by user story (P1–P8) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Agent source**: `apps/agents/communication/` (new modules within existing agent workspace)
- **Shared modules**: `apps/agents/common/` (existing — ContentSafetyValidator, LLMCallMixin, LLMClient, handoffs, dependency_notifier)
- **Test files**: `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/simulation/`
- **Alert templates**: `data/alert-templates/`
- **Agent workspace config**: `apps/agents/pyproject.toml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package initialization, dependency installation, and pre-approved alert template files for all 6 supported languages.

- [x] T001 Create package initialization file at `apps/agents/communication/__init__.py` with version string `__version__ = "0.1.0"` and public API imports (`CommunicationAgent`, `CommunicationConfig`)
- [x] T002 Add `azure-communication-sms`, `azure-notificationhubs`, and `numpy` dependencies to the `[project.dependencies]` section of `apps/agents/pyproject.toml`
- [x] T003 [P] Create primary en-AU alert template file at `data/alert-templates/en-AU.json` with pre-approved template entries for all hazard types (`cyclone`, `bushfire`, `flood`, `storm`, `earthquake`, `tsunami`, `general`) and alert types (`evacuation`, `shelter_in_place`, `all_clear`, `general_warning`), each with `template_id`, `hazard_type`, `severity`, `language_code`, `title_template`, `body_template`, `action_items_template` per data-model.md §Alert Template Schema, using `{placeholder}` syntax for dynamic values (`{location}`, `{time}`, `{severity}`, `{wind_speed}`, `{severity_detail}`, `{help_url}`)
- [x] T004 [P] Create 5 non-English alert template files at `data/alert-templates/zh-Hans.json`, `data/alert-templates/ar.json`, `data/alert-templates/vi.json`, `data/alert-templates/el.json`, `data/alert-templates/it.json` — same structure as en-AU.json with pre-approved translations for all hazard and alert type combinations, maintaining semantic equivalence across all languages per FR-007

**Checkpoint**: Project initialised — dependencies available, 6 pre-approved alert template files in place for local development.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, configuration, and enums that ALL user stories depend on. Every pipeline stage, every service module, and every test relies on these types.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `apps/agents/communication/config.py` with `CommunicationConfig` frozen dataclass reading all 26 environment variables from data-model.md §Configurable Parameters: `SUPPORTED_LANGUAGES` (default `en-AU,zh-Hans,ar,vi,el,it`, CSV), `BACK_TRANSLATION_THRESHOLD` (default 0.85, float), `ALERT_MAX_TOKENS` (default 180, int), `HANDOFF_DEDUP_WINDOW_MINUTES` (default 30, int), `APPROVAL_ESCALATION_TIMEOUT_MINUTES` (default 15, int), `MAX_ESCALATION_LEVELS` (default 3, int), `ALERT_EXPIRY_HOURS` (default 24, int), `DELIVERY_MAX_RETRIES` (default 3, int), `DELIVERY_CHANNELS` (default `sms,push,emergency_broadcast`, CSV), `EAS_ENDPOINT_URL` (required, str), `SMS_MAX_LENGTH` (default 612, int), `CONTENT_MAX_LENGTH` (default 1200, int), `AUDIT_BUFFER_CAPACITY` (default 10000, int), `AUDIT_BUFFER_FILE_PATH` (default `communication_audit.jsonl`), `VERSION_CONFLICT_MAX_RETRIES` (default 3, int), `AGENT_VERSION` (default `0.1.0`), `PORT` (default 8084, int), `CONFIDENCE_BASE` (default 1.0, float), `FRESHNESS_PENALTY_FACTOR` (default 0.9, float), `BACK_TRANSLATION_PENALTY_FACTOR` (default 0.9, float), `FALLBACK_REDUCTION_FACTOR` (default 0.8, float), `MAX_CONCURRENT_ALERTS` (default 50, int — per NFR-001, controls asyncio.Semaphore concurrency limit; incoming handoffs beyond this limit receive HTTP 429), `QUEUE_SCALE_OUT_THRESHOLD` (default 10, int), `QUEUE_SCALE_IN_THRESHOLD` (default 3, int), `SCALE_IN_COOLDOWN_MINUTES` (default 5, int), plus Azure service connection strings; include `compute_config_hash() -> str` for configuration version tracking
- [x] T006 [P] Create `apps/agents/communication/models.py` with all Pydantic v2 models and enums from data-model.md: 10 enums — `AlertStatus` (10 values: `drafting`, `pending_review`, `approved`, `rejected`, `delivering`, `delivered`, `partially_delivered`, `superseded`, `expired`, `cancelled`), `ChangeType` (4 values: `initial`, `update`, `correction`, `all_clear`), `ChannelType` (3 values: `sms`, `push`, `emergency_broadcast`), `DeliveryStatus` (5 values: `pending`, `in_progress`, `delivered`, `failed`, `retrying`), `GenerationMethod` (4 values: `llm`, `template`, `template_fallback`, `safety_fallback`), `ContentSafetyResult` (3 values: `passed`, `failed_with_fallback`, `not_checked`), `ApprovalMode` (2 values: `human_approved`, `escalated`), `UrgencyLevel` (3 values: `immediate`, `watch`, `advisory`), `SegmentPriority` (3 values: `critical`, `high`, `moderate`), `CommunicationDecisionType` (18 values per data-model.md); 7 entity/embedded models — `ContentBlock` (12 fields including `language_code`, `title`, `body`, `action_items`, `generation_method`, `content_safety_result`, `back_translation_score`, `back_translation_flagged`, `translation_unavailable`), `ContentSafetyDetail` (5 fields), `EscalationEvent` (6 fields including `level` 1–3, `from_commander_id`, `to_commander_id`, `held_for_next_available`), `AudienceSegment` (13 fields including `zone_level` 1–3, `vulnerability_categories`, `urgency_level`, `priority`, `missing_data_flags`), `DeliveryRecord` (18 fields including `segment_count` for SMS, `is_deduplicated`, `deduplicated_by_segment_id`, `retry_backoff_intervals` default `[1.0, 2.0, 4.0]`), `PublicAlert` (primary output with 35+ fields including state machine per data-model.md, alert_id regex `^ca-[a-zA-Z0-9_-]+-v\d+$`, version ≥ 1, `content_blocks` must contain `en-AU`, `change_summary` required for non-initial, `referenced_alert_id` required for correction/all_clear, confidence clamped [0.0, 1.0]), `CommunicationDecisionRecord` (18 fields per data-model.md audit entity), `AuditBufferEntry` (2 fields: `record`, `buffered_at`)
- [x] T007 [P] Write unit tests for all models, enums, and validation rules in `tests/unit/test_communication_models.py` covering: all 10 enum completeness checks, `PublicAlert` validation (alert_id regex, version ≥ 1, confidence range [0.0, 1.0], content_blocks must include `en-AU`, change_summary required for non-initial change_type, referenced_alert_id required for correction/all_clear, approval_justification required when approval_action is reject), `AlertStatus` state machine transitions per data-model.md, `ContentBlock` field constraints (title ≤ 200, body ≤ 1200, action_items ≤ 500), `AudienceSegment` validation (zone_level 1/2/3, vulnerability_categories items from allowed set, vulnerable segments must have priority=critical), `DeliveryRecord` validation (default retry_backoff_intervals, attempt_count range), `CommunicationDecisionRecord` required fields and optional field handling, `EscalationEvent` level range 1–3, serialization/deserialization for all models
- [x] T008 [P] Write unit tests for config loading in `tests/unit/test_communication_config.py` covering: default values for all 26 parameters, environment variable overrides, CSV parsing for `SUPPORTED_LANGUAGES` and `DELIVERY_CHANNELS`, type coercion (str→float, str→int), missing optional variables use defaults, `compute_config_hash()` returns consistent SHA-256 for same config, config hash changes when any parameter changes

**Checkpoint**: All foundational data types and configuration exist. Model validation tests pass. Every subsequent phase depends on these types.

---

## Phase 3: User Story 1 — Receive Handoff and Draft Multilingual Public Alert (Priority: P1) 🎯 MVP

**Goal**: End-to-end pipeline: receive `AgentHandoffEvent` from Risk Assessment Agent via Service Bus, validate handoff with deduplication, retrieve recommendation and assessment data, load templates, generate multilingual alert content in 6 languages (en-AU first, then 5 translations via LLM with template fallback), perform back-translation quality validation, run basic content safety checks, assign monotonic version number via optimistic concurrency, persist `PublicAlert` with `status=pending_review` to Cosmos DB, and write audit records.

**Independent Test**: Send a synthetic `AgentHandoffEvent` with `source_agent=risk_assessment`, `target_agent=communication`, and payload containing `recommendationId`, `summary`, `explanation`, and `assessmentId`. Verify the agent produces a `PublicAlert` with content blocks in all 6 languages, `status=pending_review`, back-translation quality scores, content safety results, traceability references, and version number `ca-{incident_id}-v1`.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Write unit tests for handoff deduplication in `tests/unit/test_communication_dedup.py` covering: first-seen handoff returns False, duplicate by handoff_id within 30-minute window returns True, handoff after TTL expiry returns False, duplicate by `incident_id + hazard_type` combination within window returns True, cache eviction behaviour, configurable dedup window duration, dedup cache restart/full → fail-open for safety per CHK056 (accept handoff rather than reject)
- [x] T010 [P] [US1] Write unit tests for multilingual translation in `tests/unit/test_communication_translator.py` covering: en-AU generated first as reference, non-English languages generated sequentially using en-AU as context per FR-008, LLM translation with `temperature=0` for determinism, back-translation quality check (cosine similarity ≥ 0.85 threshold → pass, below threshold → flag with 0.9× confidence penalty per R-002), LLM unavailable → template fallback with `generation_method=template_fallback` and 0.8× confidence penalty per FR-036, compound confidence penalty stacking in deterministic order (freshness → back-translation → fallback per CHK031), embedding service outage → skip back-translation check entirely per CHK051, `CORRECTION:` prefix applied to title when `change_type=correction` per FR-017, mixed generation methods tracked per language
- [x] T011 [P] [US1] Write unit tests for version counter in `tests/unit/test_communication_versioning.py` covering: first version = 1 for new incident, monotonic increment per incident, alert_id format `ca-{incident_id}-v{N}`, optimistic concurrency retry on 412 Precondition Failed (Cosmos DB etag conflict), max 3 retries with jitter per `VERSION_CONFLICT_MAX_RETRIES`, concurrent version assignment safety, separate version sequences per incident ID
- [x] T012 [P] [US1] Write unit tests for pipeline stages 1–8 in `tests/unit/test_communication_pipeline.py` covering: valid handoff acceptance and processing, malformed handoff rejection with `handoff_rejected` audit record, missing incident rejection, duplicate handoff discard with `duplicate_discarded` audit record, recommendation/assessment retrieval success and failure, template loading and placeholder interpolation (missing placeholder → `[unknown]` per CHK006), en-AU-first multilingual drafting, back-translation quality validation, basic content safety check (LLM output through ContentSafetyValidator, fail → template fallback), version assignment and persistence to Cosmos with `status=pending_review`, audit record creation at each stage

### Implementation for User Story 1

- [x] T013 [P] [US1] Create `apps/agents/communication/dedup.py` with `HandoffDeduplicator` class: TTL-based in-memory LRU cache with configurable dedup window from `CommunicationConfig.handoff_dedup_window_minutes` (default 30 min), dual dedup keys — `is_duplicate_by_id(handoff_id) -> bool` for handoff ID dedup and `is_duplicate_by_incident(incident_id, hazard_type) -> bool` for incident+hazard combination dedup per FR-003, automatic eviction of expired entries, fail-open on cache full/restart per CHK056 (accept handoff rather than reject)
- [x] T014 [P] [US1] Create `apps/agents/communication/templates.py` with `TemplateLoader` class: load JSON template files from `data/alert-templates/{language_code}.json` at startup, select template by `hazard_type + severity + alert_type`, `interpolate(template, values) -> str` method substituting `{placeholder}` values with sanitisation to prevent injection per CHK005, missing placeholder value → substitute `[unknown]` and log warning per CHK006, missing template file for a language → fall back to en-AU template with `[Translation unavailable]` suffix per CHK008, malformed template file → startup error (fail-fast), all template files missing → startup error (agent cannot start), `get_template_text(hazard_type, severity, alert_type, language_code, values) -> str` convenience method
- [x] T015 [P] [US1] Create `apps/agents/communication/translator.py` with `MultilingualTranslator` class: `translate_all(en_au_context, hazard_context, config) -> dict[str, ContentBlock]` generating en-AU first via `_generate_with_fallback()` from `LLMCallMixin` with system prompt scoping LLM to emergency alert drafting per FR-013, then translating sequentially to each non-English language with en-AU content as context per FR-008, `temperature=0` for deterministic output, `max_output_tokens` from config (default 180), `back_translate_and_score(content, original_en_au, language) -> float` performing back-translation to English via LLM then computing cosine similarity of embeddings (numpy dot product) per R-002, threshold from `BACK_TRANSLATION_THRESHOLD` (default 0.85), below threshold → flag with `back_translation_flagged=True` and apply 0.9× confidence penalty, `compute_compound_confidence(base, penalties) -> float` applying multiplicative stacking in order: freshness → back-translation (0.9×) → fallback (0.8×) per CHK031, embedding service unavailable → skip back-translation entirely, log `degradation_detected`, use translation as-is per CHK051
- [x] T016 [P] [US1] Create `apps/agents/communication/versioning.py` with `VersionCounter` class: Cosmos DB etag-based optimistic concurrency per R-014, counter document pattern `{incident_id}_alert_counter` in `public-alerts` container, `assign_version(incident_id) -> int` with read-increment-replace, conflict retry with exponential jitter (max retries from `VERSION_CONFLICT_MAX_RETRIES`), format `alert_id` as `ca-{incident_id}-v{N}`, `supersede_previous(incident_id, current_version) -> bool` marking previous active version as `superseded` per FR-018
- [x] T017 [P] [US1] Create `apps/agents/communication/audit.py` with `AuditWriter` class: primary Cosmos DB write path to `communication-decisions` container, `write_record(record: CommunicationDecisionRecord) -> None` method, partition key `/tenant_id`, append-only (`create_item`, not upsert), error handling for Cosmos unavailability (to be extended with three-tier degradation in US7), `get_status() -> str` returning `"healthy"` for Cosmos available
- [x] T018 [US1] Create `apps/agents/communication/pipeline.py` with `CommunicationProcessingPipeline` class orchestrating the 11-stage pipeline per contracts/communication-pipeline.md: Stage 1 (handoff intake — Pydantic v2 validation, `target_agent=communication` check, incident existence check, dual dedup via `HandoffDeduplicator`, acknowledge within 5s per FR-001, emit `handoff_received` audit record), Stage 2 (data retrieval — retrieve recommendation and assessment from Cosmos DB using `recommendationId`/`assessmentId`, snapshot input data for reproducibility, handle missing recommendation with `handoff_rejected`, handle superseded assessment with warning per CHK054), Stage 3 (audience segmentation — stub for MVP creating one default segment per zone from assessment data; full implementation in US4), Stage 4 (template loading — load templates via `TemplateLoader`, interpolate placeholders, handle missing templates per CHK008), Stage 5 (multilingual drafting — invoke `MultilingualTranslator.translate_all` for 6 sequential languages per ≤15s budget), Stage 6 (back-translation validation — cosine similarity check for LLM-generated non-English content, skip for template text), Stage 7 (content safety — validate LLM content through `ContentSafetyValidator` from `apps/agents/common/content_safety.py`, fail → template fallback per FR-011, compute overall `content_safety_result`), Stage 8 (versioning & persistence — assign version via `VersionCounter`, generate alert_id, set `status=pending_review`, supersede previous version, persist `PublicAlert` to Cosmos), Stage 9 (approval notification — stub for MVP; full implementation in US2), Stage 10 (delivery — stub for MVP; full implementation in US3), Stage 11 (audit finalisation — basic audit record write; full implementation in US7)
- [x] T019 [US1] Replace existing stub in `apps/agents/communication/agent.py` with full `CommunicationAgent` class: subclass `LLMCallMixin`, integrate `CommunicationConfig`, `CommunicationProcessingPipeline`, `TemplateLoader`, `MultilingualTranslator`, `HandoffDeduplicator`, `VersionCounter`, `AuditWriter`; implement `process_handoff(event: AgentHandoffEvent) -> PublicAlert` as main pipeline entry point; wire Service Bus consumer for `communication-handoffs` queue to deserialise messages to `AgentHandoffEvent`, invoke pipeline, acknowledge on completion, handle poison messages; implement `asyncio.Semaphore(MAX_CONCURRENT_ALERTS)` concurrency limiter — return HTTP 429 Too Many Requests when semaphore is full per NFR-001; create FastAPI app factory `create_app()` with health endpoint placeholder, configure port 8084; implement `__main__.py` entry point per quickstart.md (`uv run python -m communication`)
- [x] T020 [P] [US1] Write contract tests for handoff intake structure in `tests/contract/test_communication_handoff.py` covering: inbound `AgentHandoffEvent` schema validation (required fields: handoff_id, incident_id, source_agent=risk_assessment, target_agent=communication, payload with recommendationId/summary/explanation/assessmentId), validation rejection of malformed handoffs, duplicate discard with `duplicate_discarded` audit record, incident+hazard combination dedup, tenant_id propagation from handoff through alert
- [x] T021 [P] [US1] Write contract tests for alert output schema in `tests/contract/test_communication_alert_schema.py` covering: `PublicAlert` output contains all required fields per data-model.md (alert_id format `ca-{incident_id}-v{N}`, incident_id, version ≥ 1, status=pending_review, change_type=initial for first alert, content_blocks with all 6 languages, en-AU always present, generation_method, content_safety_result, confidence in [0.0, 1.0], recommendation_id, assessment_id, tenant_id), traceability references back to handoff/recommendation/assessment, ContentBlock per-language fields (title, body, action_items, generation_method, back_translation_score for non-English)

**Checkpoint**: US1 complete — end-to-end multilingual alert generation from handoff. The agent receives handoffs, validates, retrieves assessment data, loads templates, generates 6-language content with LLM + template fallback, performs back-translation quality checks, runs content safety validation, assigns monotonic versions, and persists alerts with `status=pending_review`. Fully testable with synthetic handoffs.

---

## Phase 4: User Story 2 — AIIMS-Aligned Commander Approval Workflow (Priority: P2)

**Goal**: Implement the AIIMS approval workflow where all alerts enter `pending_review` and the incident commander approves, rejects, or modifies via POST endpoints. Add escalation chain with configurable timeout (15 min default), max 3 levels, NEVER auto-approve (CHK019). Commander identity validated via JWT `role=commander` claim (CHK059). Approval notifications sent via Service Bus `commander-approval-queue`.

**Independent Test**: Create a `PublicAlert` in `pending_review` status, submit an approval action with a user ID and role, and verify the alert transitions to `approved` with approval metadata recorded in both the alert record and the audit trail.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T022 [P] [US2] Write unit tests for approval workflow in `tests/unit/test_communication_approval.py` covering: approve transitions alert from `pending_review` to `approved` with `approved_by_user_id`, `approved_by_role`, `approved_at`, reject transitions to `rejected` with mandatory justification per FR-020, modify creates new alert version in `pending_review` (original remains for audit), escalation after 15-minute timeout sends to next-in-chain commander, max 3 escalation levels (CHK019), after level 3 hold with CRITICAL priority flag for next available commander — NEVER auto-approve, concurrent approval conflict → 409 with first-write-wins via Cosmos etag per R-014, escalation history recorded as `EscalationEvent` list on alert, cancel transitions from `drafting`/`pending_review`/`approved` (pre-delivery) to `cancelled`, cancel from `delivering`/`delivered` → 409 conflict

### Implementation for User Story 2

- [x] T023 [US2] Create `apps/agents/communication/approval.py` with `ApprovalWorkflow` class: `request_approval(alert: PublicAlert, commander_chain: list[str]) -> None` publishing approval request to Service Bus `commander-approval-queue` with full alert preview (all language variants, audience segments, delivery channels, traceability per FR-020), `start_escalation_timer(alert_id, timeout_minutes) -> None` using `asyncio` timer per `APPROVAL_ESCALATION_TIMEOUT_MINUTES` (default 15), `escalate(alert_id, current_level) -> None` escalating to next commander if `escalation_level < MAX_ESCALATION_LEVELS` (default 3), emitting `escalation_triggered` audit record, holding with CRITICAL flag when max levels reached per CHK019, `process_approval(alert_id, user_id, role, action) -> PublicAlert` executing approve/reject with Cosmos etag-based optimistic concurrency for concurrent approval handling per R-014 (first write wins, second gets 409), `create_modified_version(alert_id, modifications, user_id, role) -> PublicAlert` creating new version with commander changes, `cancel_alert(alert_id, user_id, role, reason) -> PublicAlert` transitioning to cancelled from pre-delivery states only
- [x] T024 [US2] Implement pipeline stage 9 (approval notification) in `apps/agents/communication/pipeline.py`: build approval request payload with alert preview including all language variants, audience segment summary, delivery channel configuration, traceability references (recommendation_id, assessment_id), warning if assessment has been superseded per Edge Case §7; publish to Service Bus `commander-approval-queue`; start escalation timer; emit `approval_requested` audit record
- [x] T025 [US2] Implement `POST /alerts/{alert_id}/approve` and `POST /alerts/{alert_id}/reject` endpoints in `apps/agents/communication/agent.py`: JWT authentication with `role=commander` claim per CHK059, approve → transition to `approved`, record approval metadata, trigger Stage 10 delivery (when implemented), emit `approval_action` audit record; reject → transition to `rejected` with mandatory non-empty `justification` (422 if missing per FR-020), emit `approval_action` audit record; 409 Conflict on concurrent approval per R-014; 404 Not Found; 403 Forbidden for invalid JWT/role; response schemas per contracts/health-endpoint.md
- [x] T026 [US2] Implement `POST /alerts/{alert_id}/modify` and `POST /alerts/{alert_id}/cancel` endpoints in `apps/agents/communication/agent.py`: modify → create new alert version via `ApprovalWorkflow.create_modified_version` incorporating commander's changes (audience segment adjustments, content overrides), new version enters `pending_review`, original remains for audit, emit `approval_action` audit record; cancel → transition to `cancelled` from `drafting`/`pending_review`/`approved` only, 409 if already `delivering`/`delivered`/terminal state, emit `approval_action` audit record; response schemas per contracts/health-endpoint.md
- [x] T027 [P] [US2] Write unit tests for approval and management endpoints in `tests/unit/test_communication_endpoints.py` covering: approve returns 200 with correct response schema, reject returns 200 with justification recorded, reject without justification returns 422, modify returns 200 with new version created, cancel returns 200 from pre-delivery states, cancel returns 409 from delivering/delivered, concurrent approve returns 409 for second caller, invalid JWT returns 403, missing alert returns 404, all endpoints emit appropriate audit records

**Checkpoint**: US2 complete — full AIIMS approval workflow operational. Commanders can approve, reject, modify, or cancel alerts via POST endpoints. Escalation chain works up to 3 levels with CRITICAL hold. NEVER auto-approve. Concurrent approval resolved via first-write-wins.

---

## Phase 5: User Story 3 — Multi-Channel Alert Delivery (Priority: P3)

**Goal**: After commander approval, deliver alerts across SMS (Azure Communication Services, multi-part up to 612 chars/4 segments per CHK034), push notifications (Azure Notification Hubs), and emergency broadcast (EAS webhook, en-AU only). Per-channel independent retry (3×, exponential backoff 1s/2s/4s). Vulnerable populations delivered first with `priority=critical`. Overlapping segments deduplicated at delivery time (highest-priority wins per CHK041). Delivery receipts tracked per channel per segment.

**Independent Test**: Create an `approved` alert with audience segments, trigger delivery, and verify that `DeliveryRecord` records are created for each channel × segment combination with appropriate content formatting, delivery status tracking, and language-specific content.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T028 [P] [US3] Write unit tests for multi-channel delivery in `tests/unit/test_communication_delivery.py` covering: SMS formatting respects `SMS_MAX_LENGTH` (612 chars), SMS `segment_count` computed as `ceil(len/153)` for multi-part per CHK034/R-013, SMS uses recipient's preferred language, push notification formatted as title + body payload, emergency broadcast uses en-AU only per FR-029, per-channel independent retry with exponential backoff (1s, 2s, 4s), channel failure does NOT block other channels per FR-030, all retries exhausted → `delivery_status=failed` with failure reason, vulnerable/critical segments delivered first per FR-024, overlapping segment deduplication at delivery time (highest-priority segment wins per CHK041, lower-priority marked `is_deduplicated=True`), aggregate delivery status: all succeed → `delivered`, any fail → `partially_delivered`, all fail → `failed`, simulation tenant alerts MUST NOT trigger real public delivery per FR-040

### Implementation for User Story 3

- [x] T029 [US3] Create `apps/agents/communication/delivery.py` with `MultiChannelDeliveryService` class: `deliver_alert(alert: PublicAlert, segments: list[AudienceSegment]) -> list[DeliveryRecord]` orchestrating delivery across configured channels; `_deduplicate_segments(segments) -> list[AudienceSegment]` grouping overlapping segments by geographic overlap and keeping highest-priority per CHK041, marking lower-priority as `is_deduplicated=True`; `_sort_delivery_order(segments) -> list` ordering `priority=critical` first then by zone_level ascending per FR-024; `_deliver_sms(content, segment, language) -> DeliveryRecord` via Azure Communication Services SDK, formatting to `SMS_MAX_LENGTH` (612 chars), computing `segment_count = ceil(len/153)` per R-013, using recipient's preferred language; `_deliver_push(content, segment, language) -> DeliveryRecord` via Azure Notification Hubs SDK, formatting as push payload with title + body; `_deliver_broadcast(content, segment) -> DeliveryRecord` via HTTP POST to `EAS_ENDPOINT_URL`, en-AU only per FR-029; `_retry_with_backoff(deliver_fn, max_retries, backoff_intervals) -> DeliveryRecord` implementing per-channel independent retry with exponential backoff `[1.0, 2.0, 4.0]` using `tenacity`; tenant isolation check — simulation alerts skip real delivery per FR-040; emit `delivery_initiated`/`delivery_succeeded`/`delivery_failed`/`delivery_deduplicated` audit records
- [x] T030 [US3] Implement pipeline stage 10 (multi-channel delivery) in `apps/agents/communication/pipeline.py`: trigger on alert transition to `approved` status (via POST approve endpoint), transition alert to `delivering`, invoke `MultiChannelDeliveryService.deliver_alert`, persist `DeliveryRecord` records to Cosmos DB `delivery-records` container, compute alert-level delivery status (all → `delivered`, any fail → `partially_delivered`, all fail → `failed` surfaced to commander), emit aggregate delivery metrics, update alert `published_at` timestamp on first delivery
- [x] T031 [US3] Add `GET /alerts/{alert_id}/delivery-status` endpoint in `apps/agents/communication/agent.py`: response schema per contracts/health-endpoint.md with `overall_status`, `delivery_summary` (total_segments, total_deliveries, delivered, in_progress, failed, pending, completion_percentage), `by_channel` breakdown (sms, push, emergency_broadcast), and `records` array; JWT authentication required

**Checkpoint**: US3 complete — multi-channel delivery operational. SMS with multi-part support (612 chars/4 segments), push notifications, and emergency broadcast all working with independent retry. Vulnerable populations delivered first. Overlapping segments deduplicated. Delivery status tracked per channel per segment.

---

## Phase 6: User Story 4 — Audience Segmentation by Zone, Vulnerability, and Language (Priority: P4)

**Goal**: Three-dimensional audience segmentation: geographic zone (Zone 1/2/3 from evacuation agent polygons with urgency levels immediate/watch/advisory), vulnerability (aged care, hospitals, schools, disability services → `priority=critical`), and language preference (from demographic data, default en-AU). Segment size estimation for delivery planning. Missing data flags when demographic/vulnerability data unavailable (CHK042).

**Independent Test**: Provide a hazard assessment with three geographic zones, known vulnerable facilities, and language demographics. Verify the agent produces correctly prioritised audience segments with zone-based urgency, vulnerability flags, language assignments, and missing data annotations.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T032 [P] [US4] Write unit tests for audience segmentation in `tests/unit/test_communication_segmentation.py` covering: Zone 1 → `urgency=immediate`, `priority=high`; Zone 2 → `urgency=watch`, `priority=moderate`; Zone 3 → `urgency=advisory`, `priority=moderate`; vulnerable populations (aged care, hospital, school, disability services) → `priority=critical` with additional guidance; language preference assignment from demographic data; unknown language preference → default en-AU per FR-025; delivery channel assignment per segment; segment size estimation computation; missing demographic data → en-AU default, no vulnerability flags, missing_data_flags populated per FR-025/CHK042; overlapping segments preserved (dedup at delivery per CHK041, not at segmentation); each zone gets separate segment

### Implementation for User Story 4

- [x] T033 [US4] Create `apps/agents/communication/segmentation.py` with `AudienceSegmenter` class: `segment_audience(assessment_data, incident_demographics) -> list[AudienceSegment]` performing three-dimensional segmentation; `_create_zone_segments(zones) -> list[AudienceSegment]` extracting geographic zones from hazard assessment (Zone 1 = immediate/high, Zone 2 = watch/moderate, Zone 3 = advisory/moderate), zone boundaries as GeoJSON polygons from evacuation agent per FR-022; `_identify_vulnerable_populations(zones, vulnerability_data) -> list[AudienceSegment]` creating additional `priority=critical` segments for aged care, hospitals, schools, disability services within each zone per FR-024; `_assign_language_preferences(segments, demographics) -> list[AudienceSegment]` assigning preferred language from demographic data, default en-AU when unknown per FR-025; `_assign_delivery_channels(segments, config) -> list[AudienceSegment]` assigning channels per segment; `_estimate_segment_sizes(segments) -> list[AudienceSegment]` computing population estimates per FR-023; `_flag_missing_data(segments) -> list[AudienceSegment]` annotating `missing_data_flags` when demographic/vulnerability data unavailable per CHK042; emit `audience_segmented` audit record
- [x] T034 [US4] Wire full audience segmentation into pipeline stage 3 in `apps/agents/communication/pipeline.py`: replace MVP stub with `AudienceSegmenter.segment_audience`, pass zones and demographics from assessment data retrieved in stage 2, persist `AudienceSegment` records alongside alert, include segment summary in approval request payload (stage 9) for commander review

**Checkpoint**: US4 complete — three-dimensional audience segmentation operational. Zone-based urgency, vulnerability prioritisation, language preference assignment, and missing data flags all working. Commander can review full segment analysis before approving.

---

## Phase 7: User Story 5 — Alert Versioning: Updates, Corrections, and All-Clear (Priority: P5)

**Goal**: Support alert lifecycle beyond initial creation: `update` (changed situation → new version with change summary), `correction` (error fix → "CORRECTION:" prefix in all languages, references original), `all_clear` (threat passed → dedicated templates, references and supersedes original). Immutable versions — previous versions marked `superseded`. TTL-based expiry (`expired` status at 24h configurable per CHK024). `superseded` and `expired` as independent terminal states per R-011.

**Independent Test**: Create an initial alert, issue an update (changed zones), a correction (fixed error), and an all-clear. Verify each version has monotonically increasing version number, correct `change_type`, `change_summary`, "CORRECTION:" prefix for corrections, and that all previous versions remain queryable and marked `superseded`.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T035 [P] [US5] Write unit tests for versioning lifecycle in `tests/unit/test_communication_versioning.py` (extend existing) covering: `change_type=update` creates new version with change summary describing differences, previous version → `superseded`; `change_type=correction` adds "CORRECTION:" prefix to title in all 6 languages per FR-017, references original alert via `referenced_alert_id`, requires commander approval; `change_type=all_clear` uses dedicated all-clear templates per hazard type, references original alert, delivered to same audience segments as original, automatically supersedes referenced alert upon delivery per FR-017; `superseded` vs `expired` are independent terminal states per R-011/CHK024 (superseded = replaced by newer version, expired = 24h TTL); alert expiry at `ALERT_EXPIRY_HOURS` (default 24h); multiple versions (v1→v4) all queryable with change types and timestamps per US5 acceptance scenario 4

### Implementation for User Story 5

- [x] T036 [US5] Enhance `apps/agents/communication/versioning.py` with full lifecycle support: `create_update_version(incident_id, change_summary) -> PublicAlert` producing new version with `change_type=update` and change summary, superseding previous active version per FR-018; `create_correction_version(incident_id, original_alert_id, correction_reason) -> PublicAlert` producing new version with `change_type=correction`, "CORRECTION:" prefix on title in all languages per FR-017, `referenced_alert_id` set to original; `create_all_clear_version(incident_id, original_alert_id) -> PublicAlert` producing new version with `change_type=all_clear`, using dedicated all-clear templates, `referenced_alert_id` set to original, auto-supersedes referenced alert upon delivery per FR-017; `expire_alert(alert_id) -> bool` transitioning to `expired` after `ALERT_EXPIRY_HOURS` (independent of `superseded` per R-011/CHK024); `get_version_history(incident_id) -> list[PublicAlert]` retrieving all versions for an incident ordered by version number
- [x] T037 [US5] Wire versioning lifecycle into pipeline stage 8 in `apps/agents/communication/pipeline.py`: on new handoff for existing incident → create `update` version with change summary, supersede previous; on correction request → create `correction` version; on all-clear → create `all_clear` version with dedicated templates; implement periodic expiry check for alerts past TTL; emit `alert_versioned` audit record for each version transition with `change_type` and `change_summary`

**Checkpoint**: US5 complete — full alert versioning lifecycle. Updates, corrections (with "CORRECTION:" prefix), and all-clear notifications all work with proper version chaining, supersession, and independent expiry. Complete version history queryable.

---

## Phase 8: User Story 6 — Content Safety Validation Before Public Dissemination (Priority: P6)

**Goal**: Comprehensive per-language content safety validation using `ContentSafetyValidator` from `apps/agents/common/content_safety.py`. Check blocked keywords, language detection (e.g., zh-Hans content must contain Chinese characters), length enforcement (≤ 1,200 chars per FR-010). Failures → template fallback per language. Pre-approved template text exempt from runtime validation per FR-014. Track `ContentSafetyDetail` per language and overall `ContentSafetyResult`.

**Independent Test**: Configure a mock LLM to return text with a blocked keyword for one language and valid text for others. Verify the blocked language uses template fallback, others use LLM text, and `content_safety_result` reflects `failed_with_fallback`.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T038 [P] [US6] Write unit tests for content safety validation per-language in `tests/unit/test_communication_pipeline.py` (extend existing) covering: LLM content passes all checks → `content_safety_result=passed` per language; blocked keyword detected → template fallback with `generation_method=safety_fallback`, `failure_reason=blocked_keyword` in `ContentSafetyDetail`; language detection mismatch (zh-Hans output with no Chinese characters) → template fallback with `failure_reason=language_mismatch`; content exceeds 1,200 chars → `failure_reason=length_exceeded`; template-based content (pre-approved) skips runtime validation per FR-014; overall `content_safety_result`: `passed` if all languages pass, `failed_with_fallback` if any fallback, `not_checked` if validator unavailable; all 6 languages fail → all use template fallback, alert still created with `status=pending_review` (never dropped per US6 acceptance scenario 4); each language generates `content_safety_evaluated` audit record per FR-032

### Implementation for User Story 6

- [x] T039 [US6] Enhance pipeline stage 7 (content safety validation) in `apps/agents/communication/pipeline.py`: for each language with `generation_method=llm`, invoke `ContentSafetyValidator.validate()` checking blocked keywords, language detection, length enforcement (≤ `CONTENT_MAX_LENGTH` default 1,200 chars per FR-010); populate `ContentSafetyDetail` per language with `passed`, `failure_reason` (`blocked_keyword`/`language_mismatch`/`length_exceeded`), `original_text_length`, `fallback_used`; on failure → replace content with template text, set `generation_method=safety_fallback` per FR-011; skip validation for template-based content per FR-014; compute overall `content_safety_result` (worst-case across all languages per FR-012); emit `content_safety_evaluated` audit record per language and `content_safety_failure` audit record for each failure
- [x] T040 [US6] Implement per-language content safety fallback logic in `apps/agents/communication/translator.py`: when `ContentSafetyValidator` fails for a specific language, load template text via `TemplateLoader` for that language only, set `generation_method=safety_fallback` (distinct from `template_fallback` which is LLM-unavailable per CHK015), preserve LLM-generated content for languages that pass, track mixed `generation_method` across languages, set alert-level `generation_method` to worst-case across all languages

**Checkpoint**: US6 complete — comprehensive per-language content safety validation. Blocked keywords, language detection mismatches, and length violations all caught with template fallback per language. Pre-approved templates exempt from runtime checks. Detailed `ContentSafetyDetail` tracking per language.

---

## Phase 9: User Story 7 — Audit Trail of All Communication Decisions (Priority: P7)

**Goal**: Extend audit writer with three-tier degradation (Cosmos DB → in-memory buffer → JSONL file spill → recovery flush) per research.md §3. Ensure every processing step across all 11 pipeline stages produces a `CommunicationDecisionRecord` with all 18 decision types. 100% reconcilable via handoff-to-audit correlation per SC-006.

**Independent Test**: Process a sequence of handoffs resulting in alerts with various outcomes (approved, rejected, updated, corrected, all-clear). Query the audit trail to verify every processing step has a corresponding record with all required fields, and simulate Cosmos outage to verify tier 2/3 degradation.

### Tests for User Story 7

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T041 [P] [US7] Write unit tests for three-tier audit degradation in `tests/unit/test_communication_audit.py` covering: tier 1 Cosmos write success, tier 2 in-memory ring buffer activation on Cosmos failure (bounded deque at `AUDIT_BUFFER_CAPACITY` default 10K), tier 3 JSONL file spill when memory buffer full, recovery flush order (memory → file → Cosmos in chronological order), `buffered_at` and `flush_source` annotation on recovered records, `get_status()` returning `"healthy"`/`"buffering"`/`"degraded"` based on current tier, `buffer_depth` property reporting current buffer size, tier transitions logged as audit events themselves per FR-034, audit completeness verification (handoff_ids processed vs records created), all 18 `CommunicationDecisionType` values produce valid records

### Implementation for User Story 7

- [x] T042 [US7] Extend `AuditWriter` in `apps/agents/communication/audit.py` with tier 2 in-memory ring buffer: bounded `collections.deque` with `maxlen` from `CommunicationConfig.audit_buffer_capacity` (default 10K), auto-fallback when Cosmos DB write raises exception, annotate buffered records with `buffered_at` timestamp, `get_status()` returns `"buffering"` when tier 2 active, emit `degradation_detected` audit event on tier transition per FR-034
- [x] T043 [US7] Extend `AuditWriter` in `apps/agents/communication/audit.py` with tier 3 JSONL file spill: append-only write to `CommunicationConfig.audit_buffer_file_path` (default `communication_audit.jsonl`), triggered when memory buffer is full, `get_status()` returns `"degraded"` when tier 3 active, emit critical alert on tier 3 activation, include `buffer_depth` property combining memory + file record counts
- [x] T044 [US7] Implement recovery flush in `apps/agents/communication/audit.py`: `flush() -> int` method draining memory buffer then file buffer to Cosmos in chronological order, annotating each record with `flush_source` (`memory_buffer` or `file_buffer`), invoked on Cosmos recovery detection and periodically, handle partial flush failures gracefully (retry remaining), report flush progress via telemetry
- [x] T045 [US7] Implement audit finalisation (pipeline stage 11) in `apps/agents/communication/pipeline.py`: verify audit completeness by reconciling all expected records against actual records for the current handoff, compute aggregate metrics (total processing time, per-stage latencies), flush any buffered audit records if primary storage recovered, emit final telemetry events, log discrepancies if any records are missing
- [x] T046 [US7] Add comprehensive audit records for all 18 decision types across pipeline stages in `apps/agents/communication/pipeline.py`: ensure every stage emits appropriate `CommunicationDecisionRecord` entries — `handoff_received` (stage 1), `handoff_rejected` (stage 1 failure), `duplicate_discarded` (stage 1 dedup), `audience_segmented` (stage 3), `alert_drafted` (stage 5), `back_translation_below_threshold` (stage 6), `content_safety_evaluated` (stage 7), `content_safety_failure` (stage 7 failure), `alert_versioned` (stage 8), `approval_requested` (stage 9), `approval_action` (approve/reject/modify endpoints), `escalation_triggered` (escalation timer), `delivery_initiated` (stage 10), `delivery_succeeded` (stage 10), `delivery_failed` (stage 10), `degradation_detected` (any fallback), `health_status_changed` (health endpoint), `template_fallback` (LLM unavailable); each record includes `agent_version`, `config_version`, `processing_duration_ms`, and `timestamp`

**Checkpoint**: US7 complete — full audit trail with three-tier degradation. Every processing step produces an audit record. 100% reconcilable via handoff-to-audit correlation. Cosmos outage → memory buffer → file spill → recovery flush. All 18 decision types covered.

---

## Phase 10: User Story 8 — Graceful Degradation When Services Are Unavailable (Priority: P8)

**Goal**: The agent MUST NOT halt when any single dependency fails (FR-039). LLM unavailable → template fallback with 0.8× confidence (FR-036). Delivery channel down → continue on available channels (FR-037). Embedding outage → skip back-translation (CHK051). Audit degradation → three-tier (implemented in US7). Service recovery detected and logged.

**Independent Test**: Disable the LLM client and SMS gateway, send handoffs, and verify alerts are still produced with template fallback, delivery proceeds on available channels, degradation events are logged, and recovery is handled when services are restored.

### Tests for User Story 8

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T047 [P] [US8] Write unit tests for degradation scenarios in `tests/unit/test_communication_pipeline.py` (extend existing) covering: LLM unavailable → all languages use template text with `generation_method=template_fallback`, confidence × 0.8 per FR-036, `degradation_detected` audit record; LLM becomes available → resumes LLM-enhanced generation with `generation_method=llm`, logs recovery event; embedding service unavailable → skip back-translation check entirely per CHK051, use translation as-is, log `degradation_detected`; SMS channel fails → mark SMS as degraded, continue push + broadcast delivery, surface failure to commander per FR-037; all delivery channels fail → mark alert delivery as `failed`, surface to commander with maximum urgency per Edge Case §6; primary audit storage unavailable → tier 2 in-memory buffer, recovery flush on restore per FR-034; mixed degradation (LLM + SMS down simultaneously) → template alerts delivered via push + broadcast only

### Implementation for User Story 8

- [x] T048 [US8] Implement comprehensive LLM fallback with multiplicative confidence reduction in `apps/agents/communication/translator.py` and `apps/agents/communication/pipeline.py`: when LLM service unavailable, all language versions use template text from `TemplateLoader` with `generation_method=template_fallback`, apply 0.8× confidence penalty multiplicatively per FR-036/CHK031, log `template_fallback` audit record with degradation details, track LLM availability state for recovery detection
- [x] T049 [US8] Implement per-channel degradation handling in `apps/agents/communication/delivery.py`: when a specific delivery channel fails after exhausting retries, mark channel as degraded in health status, continue delivery on remaining available channels per FR-037, surface failed channel to incident commander, aggregate alert-level delivery status (`partially_delivered` when any channel fails per FR-030), log `degradation_detected` audit record per channel, track per-channel availability state
- [x] T050 [US8] Implement embedding service outage handling in `apps/agents/communication/translator.py`: when embedding service (Azure OpenAI embedding deployment) is unavailable during back-translation quality check, skip the cosine similarity comparison entirely per CHK051, use LLM-generated translation as-is (or template if LLM also unavailable), log `degradation_detected` audit record with `service=embedding`, `fallback_used=skip_back_translation`, do NOT apply back-translation confidence penalty (only apply it when check runs and fails)
- [x] T051 [US8] Implement service recovery detection and logging across `apps/agents/communication/pipeline.py`: track per-dependency health state (LLM, embedding, SMS, push, broadcast, Cosmos), detect recovery transitions (unhealthy → healthy), emit `DegradationRecovered` custom event with `service` and `downtime_ms` per contracts/telemetry.md, log recovery in audit trail, resume normal processing path on recovery, flush buffered audit records on Cosmos recovery

**Checkpoint**: US8 complete — the agent never halts for any single dependency failure. Template fallback for LLM outage, per-channel independent degradation for delivery, embedding outage handling for back-translation, and comprehensive recovery detection. All degradation/recovery events logged.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Health endpoint, observability instrumentation, integration tests, simulation tests, infrastructure, and end-to-end validation.

### Health Endpoint

- [x] T052 Implement `GET /health` endpoint in `apps/agents/communication/agent.py` with FastAPI per contracts/health-endpoint.md: response schema with `status` (`healthy`/`degraded`/`unhealthy`), `agent` (`communication`), `version`, `timestamp`, `checks` object (`llm_connectivity`, `cosmos_connectivity`, `sms_service_status`, `push_service_status`, `broadcast_endpoint_status` — each with `status` and `latency_ms`/`last_checked`), `operational` object (`pending_approvals_count`, `active_deliveries_count`, `processing_queue_depth`, `audit_store` current tier, `dedup_cache_size`), `config_hash` from `compute_config_hash()`; status determination: `healthy` if all checks healthy, `degraded` if any non-critical check degraded, `unhealthy` if Cosmos down OR all delivery channels down; 200 for healthy/degraded, 503 for unhealthy; ≤1s response SLA per SC-007

### Read Endpoint

- [x] T053 [P] Add `GET /alerts/{alert_id}` endpoint in `apps/agents/communication/agent.py`: return full `PublicAlert` object per contracts/health-endpoint.md with all language variants and metadata; 404 if not found; JWT authentication required

### Observability

- [x] T054 [P] Create `apps/agents/communication/telemetry.py` with OpenTelemetry instrumentation per contracts/telemetry.md: configure `azure-monitor-opentelemetry` exporter, set service name `communication-agent`, define meter and tracer instances, helper functions for span creation and metric recording, correlation ID propagation from incoming Service Bus messages as trace parent
- [x] T055 [P] Add distributed tracing and emit all metrics defined in contracts/telemetry.md across `apps/agents/communication/pipeline.py` and `apps/agents/communication/delivery.py`: trace hierarchy with root span `communication.pipeline.process` and child spans for each of the 11 stages (including per-language LLM spans `communication.llm.generate.{lang}` and per-language back-translation spans `communication.backtranslate.{lang}` and per-segment delivery spans `communication.delivery.{channel}.{segment_id}`); 23 metrics — processing (`alert_draft_latency`, `translation_latency`, `content_safety_check_latency`, `pipeline_total_latency`, `end_to_end_latency`), approval (`approval_wait_time`, `approval_notification_latency`, `escalation_count`), delivery (`delivery_latency_per_channel`, `delivery_success_rate_per_channel`, `sms_segment_count`), quality (`back_translation_quality_score`, `template_fallback_rate`, `content_safety_failure_rate`), operational (`active_alerts_count`, `audience_segment_count`, `pending_approvals`, `processing_queue_depth`), degradation (`llm_fallback_active`, `channel_degraded`, `audit_tier`, `embedding_service_available`)
- [x] T056 [P] Emit all 17 custom events per contracts/telemetry.md at appropriate decision points across pipeline, delivery, and approval modules: `HandoffReceived`, `HandoffRejected`, `DuplicateDiscarded`, `AlertDrafted`, `BackTranslationFlagged`, `ContentSafetyFailed`, `AlertVersionCreated`, `ApprovalRequested`, `EscalationTriggered`, `EscalationExhausted`, `DeliveryStarted`, `DeliveryCompleted`, `DeliveryFailed`, `DeliveryDeduplicated`, `DegradationDetected`, `DegradationRecovered`, `TemplateFileMissing` — each with key attributes specified in contracts/telemetry.md

### Contract & Reproducibility Tests

- [x] T057 [P] Write reproducibility contract tests in `tests/contract/test_communication_reproducibility.py` covering: identical inputs (handoff payload + templates + config) produce identical alert content and version assignments, `temperature=0` ensures deterministic LLM output, configuration version tracked in each alert via config_hash, input snapshot captures assessment data for reproducibility, simulation tenant alerts isolated from live queries (different partition key)

### Integration Tests

- [x] T058 [P] Write integration tests for Cosmos DB persistence in `tests/integration/test_communication_cosmos.py` covering: `PublicAlert` write/read with partition key `/tenant_id`, `CommunicationDecisionRecord` append-only write, `DeliveryRecord` write/read, version counter optimistic concurrency (concurrent increment, etag conflict, retry), alert status transitions (`pending_review` → `approved` → `delivering` → `delivered`/`partially_delivered`), supersession (previous version marked `superseded` on new version), simulation tenant isolation (separate partition scope)
- [x] T059 [P] Write integration tests for Service Bus handoff intake in `tests/integration/test_communication_service_bus.py` covering: message deserialization to `AgentHandoffEvent`, message acknowledgement on success, poison message handling (malformed handoff → dead-letter), approval notification publish to `commander-approval-queue`, queue consumer lifecycle (start, process, stop)

### Simulation Tests

- [x] T060 [P] Write cyclone alert scenario simulation test in `tests/simulation/test_cyclone_alert_scenario.py`: send cyclone-category handoff for Far North QLD, verify 6-language alert generation, audience segmentation (Zone 1 coastal + Zone 2 inland + vulnerable hospital), commander approval workflow, multi-channel delivery (SMS multi-part, push, emergency broadcast en-AU only), audit trail completeness from handoff to delivery
- [x] T061 [P] Write bushfire alert scenario simulation test in `tests/simulation/test_bushfire_alert_scenario.py`: send bushfire-category handoff for NSW/VIC border, verify alert versioning lifecycle (initial → update with changed wind direction → correction with fixed zone boundary → all-clear), approval at each version, "CORRECTION:" prefix on correction version, all-clear using dedicated templates and superseding previous
- [x] T062 [P] Write flood alert scenario simulation test in `tests/simulation/test_flood_alert_scenario.py`: send flood-category handoff for multilingual metro area, verify three-dimensional audience segmentation (zone + vulnerability + language preference from demographics), zh-Hans and vi language segments with correct content, LLM fallback scenario (disable LLM mid-scenario), delivery deduplication for overlapping segments

### Infrastructure

- [x] T063 [P] Add/update Bicep modules in `infra/` for: Cosmos DB containers (`public-alerts` with partition key `/tenant_id` no TTL, `communication-decisions` with partition key `/tenant_id` no TTL infinite retention, `delivery-records` with partition key `/tenant_id`), Service Bus queues (`communication-handoffs` intake queue, `commander-approval-queue`), Container Apps configuration (port 8084, auto-scaling rules based on queue depth: scale-out > 10 messages, scale-in < 3 for 5 min per CHK062), managed identity role assignments (Cosmos DB Data Contributor, Service Bus Data Receiver/Sender, Azure OpenAI Cognitive Services User, Azure Communication Services Contributor), all resources in `australiaeast` per Constitution §VI

### Quickstart Validation

- [x] T064 Run quickstart.md validation: execute all steps from `specs/008-communication-agent/quickstart.md` — setup (`uv sync`), environment configuration, unit tests (`uv run pytest tests/unit/test_communication_*.py -v`), local agent start (`uv run python -m communication`), health endpoint verification (`curl localhost:8084/health`), template loading confirmation (6 languages), and verify end-to-end operation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — core pipeline, MVP
- **US2 (Phase 4)**: Depends on US1 — needs pipeline and alert records to approve
- **US3 (Phase 5)**: Depends on US1 — needs pipeline and approved alerts to deliver; independent of US2 for code development (can use mock approved alerts)
- **US4 (Phase 6)**: Depends on US1 — inserts into pipeline stage 3; independent of US2/US3
- **US5 (Phase 7)**: Depends on US1 — extends versioning from basic to full lifecycle; independent of US2–US4
- **US6 (Phase 8)**: Depends on US1 — enhances pipeline stage 7 content safety; independent of US2–US5
- **US7 (Phase 9)**: Depends on US1 — extends basic audit writer to three-tier; independent of US2–US6
- **US8 (Phase 10)**: Depends on US1 — adds degradation handling across pipeline; independent of US2–US7
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2)**: Depends on US1 for pipeline infrastructure — adds approval workflow
- **US3 (P3)**: Depends on US1 for pipeline — adds delivery; can be developed in parallel with US2 using mock approved alerts
- **US4 (P4)**: Depends on US1 for pipeline — adds segmentation; independent of US2/US3
- **US5 (P5)**: Depends on US1 for versioning — adds lifecycle; independent of US2–US4
- **US6 (P6)**: Depends on US1 for pipeline — enhances content safety; independent of US2–US5
- **US7 (P7)**: Depends on US1 for audit writer — extends to three-tier; independent of US2–US6
- **US8 (P8)**: Depends on US1 for pipeline — adds degradation; independent of US2–US7

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models and data types before services
- Services before pipeline integration
- Pipeline integration before endpoints
- Core implementation before contract/integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004)
- All Foundational tasks marked [P] can run in parallel within Phase 2 (T006, T007, T008)
- Once Foundational completes, US2–US8 can all start in parallel (each depends only on US1, not on each other)
- All tests for a user story marked [P] can run in parallel
- Within US1: T013–T017 can all run in parallel (different files, no dependencies)
- Integration and simulation tests (T058–T062) can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (write first, ensure they fail):
Task: "Unit tests for handoff dedup in tests/unit/test_communication_dedup.py"
Task: "Unit tests for translator in tests/unit/test_communication_translator.py"
Task: "Unit tests for version counter in tests/unit/test_communication_versioning.py"

# Launch all US1 implementation modules together (different files):
Task: "Create dedup.py — HandoffDeduplicator"
Task: "Create templates.py — TemplateLoader"
Task: "Create translator.py — MultilingualTranslator"
Task: "Create versioning.py — VersionCounter"
Task: "Create audit.py — AuditWriter basic"

# Then sequentially (depends on modules above):
Task: "Create pipeline.py — CommunicationProcessingPipeline"
Task: "Replace agent.py — CommunicationAgent"

# Then contract tests (can run in parallel):
Task: "Contract tests for handoff intake"
Task: "Contract tests for alert output schema"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (templates + deps)
2. Complete Phase 2: Foundational (models + config) — CRITICAL, blocks everything
3. Complete Phase 3: User Story 1 (core pipeline)
4. **STOP and VALIDATE**: Send synthetic handoff → verify 6-language alert with `status=pending_review`
5. Deploy/demo if ready — alerts are generated but require manual database inspection (no approval UI yet)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy (MVP: alerts generated)
3. Add US2 → Test independently → Deploy (commanders can approve/reject)
4. Add US3 → Test independently → Deploy (approved alerts delivered via SMS/push/broadcast)
5. Add US4 → Test independently → Deploy (three-dimensional audience targeting)
6. Add US5 → Test independently → Deploy (alert updates, corrections, all-clear)
7. Add US6 → Test independently → Deploy (comprehensive content safety per language)
8. Add US7 → Test independently → Deploy (resilient three-tier audit trail)
9. Add US8 → Test independently → Deploy (graceful degradation across all services)
10. Polish → Full observability, infrastructure, simulation tests

### Parallel Team Strategy

With multiple developers after US1 is complete:

1. Team completes Setup + Foundational + US1 together (critical path)
2. Once US1 is done:
   - Developer A: US2 (approval workflow) + US5 (versioning lifecycle)
   - Developer B: US3 (delivery) + US4 (segmentation)
   - Developer C: US6 (content safety) + US7 (audit trail) + US8 (degradation)
3. Stories complete and integrate independently
4. Team reconvenes for Phase 11 (polish, observability, simulation tests)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 64 |
| **Setup** | 4 tasks |
| **Foundational** | 4 tasks |
| **US1 (P1) — Handoff & Draft** | 13 tasks (4 test + 9 implementation) |
| **US2 (P2) — Approval Workflow** | 6 tasks (2 test + 4 implementation) |
| **US3 (P3) — Multi-Channel Delivery** | 4 tasks (1 test + 3 implementation) |
| **US4 (P4) — Audience Segmentation** | 3 tasks (1 test + 2 implementation) |
| **US5 (P5) — Alert Versioning** | 3 tasks (1 test + 2 implementation) |
| **US6 (P6) — Content Safety** | 3 tasks (1 test + 2 implementation) |
| **US7 (P7) — Audit Trail** | 6 tasks (1 test + 5 implementation) |
| **US8 (P8) — Graceful Degradation** | 5 tasks (1 test + 4 implementation) |
| **Polish & Cross-Cutting** | 13 tasks |
| **Parallel opportunities** | 38 of 64 tasks (59%) marked [P] |
| **Suggested MVP scope** | Phases 1–3 (US1 only): 21 tasks |
| **Pipeline stages covered** | All 11 stages across US1–US8 |
| **Modules created** | 13 new files + 1 replaced stub |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD within each story)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Port: 8084 (following sequence: monitoring=8080, risk=8081, evacuation=8082, resource=8083)
- All Azure resources in australiaeast per Constitution §VI
- Template governance via git PR per CHK014/CHK068 — no runtime governance

# Data Model: Communication Agent

**Phase 1 output** | **Date**: 2026-04-18 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Entities

### 1. PublicAlert

Primary output entity — a versioned, multilingual public alert for incident commander approval and public dissemination.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `alert_id` | `str` | Format: `ca-{incident_id}-v{N}`, unique, PK | Alert identifier with version suffix |
| `incident_id` | `str` | Required, indexed | Incident this alert pertains to |
| `version` | `int` | ≥ 1, monotonically increasing per incident | Version number assigned via OCC |
| `status` | `AlertStatus` enum | Required | Lifecycle state (see state machine below) |
| `change_type` | `ChangeType` enum | Required | `initial`, `update`, `correction`, `all_clear` |
| `change_summary` | `str \| None` | Required for non-initial versions | What changed from the previous version |
| `referenced_alert_id` | `str \| None` | Required for `correction` and `all_clear` | Original alert being corrected/cleared |
| `content_blocks` | `dict[str, ContentBlock]` | 1–6 entries, keyed by language code | Language → content mapping |
| `audience_segments` | `list[str]` | ≥ 1 segment ID | Audience segment IDs targeted |
| `languages` | `list[str]` | Default: 6 supported languages | Language codes included in this alert |
| `accessibility_attributes` | `list[str]` | Default: `["plain-language"]` | Accessibility metadata |
| `channel_set` | `list[ChannelType]` | ≥ 1 channel | Delivery channels for this alert |
| `generation_method` | `GenerationMethod` enum | Required | Worst-case across all languages |
| `model_deployment_id` | `str \| None` | Set when LLM used | Azure OpenAI deployment ID |
| `content_safety_result` | `ContentSafetyResult` enum | Required | Worst-case across all languages |
| `content_safety_details` | `dict[str, ContentSafetyDetail]` | Per-language breakdown | Language → safety result mapping |
| `confidence` | `float` | 0.0–1.0 | Overall confidence with compound penalties applied |
| `approval_mode` | `ApprovalMode` enum | Set on approval | `human_approved` or `escalated` |
| `approved_by_user_id` | `str \| None` | Set on approval | Commander who approved |
| `approved_by_role` | `str \| None` | Set on approval | Commander's AIIMS role |
| `approval_action` | `str \| None` | Set on approval | `approve`, `reject`, `modify` |
| `approval_justification` | `str \| None` | Required for reject | Rejection reason |
| `approved_at` | `datetime \| None` | Set on approval | Approval timestamp (UTC) |
| `escalation_level` | `int` | 0–3 | Current escalation level (0 = no escalation) |
| `escalation_history` | `list[EscalationEvent]` | Append-only | Escalation events log |
| `recommendation_id` | `str` | Required, traceability | Triggering recommendation from Risk Assessment |
| `assessment_id` | `str` | Required, traceability | Hazard assessment from Risk Assessment |
| `tenant_id` | `str` | Required, partition key component | Tenant isolation (simulation/live) |
| `published_at` | `datetime \| None` | Set on first delivery | When first delivery initiated |
| `expires_at` | `datetime \| None` | Default: created_at + 24h | TTL-based expiry timestamp |
| `created_at` | `datetime` | Auto-set, UTC | Creation timestamp |
| `updated_at` | `datetime` | Auto-set, UTC | Last status transition timestamp |
| `_etag` | `str \| None` | Cosmos DB managed | Optimistic concurrency control |

**State machine (AlertStatus)**:

```
                    ┌──────────────┐
                    │   drafting   │
                    └──────┬───────┘
                           │ draft complete
                           ▼
                    ┌──────────────┐     reject
                    │pending_review├──────────────► rejected
                    └──────┬───────┘
                           │ approve
                           ▼
                    ┌──────────────┐
                    │   approved   │
                    └──────┬───────┘
                           │ delivery initiated
                           ▼
                    ┌──────────────┐
                    │  delivering  │
                    └──────┬───────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
             ┌───────────┐ ┌──────────────────┐
             │ delivered  │ │partially_delivered│
             └─────┬─────┘ └────────┬─────────┘
                   │                │
                   ▼                ▼
            ┌────────────┐   ┌────────────┐
            │ superseded │   │  expired   │
            └────────────┘   └────────────┘

  cancelled: reachable from drafting, pending_review, approved (pre-delivery)
```

**Validation rules**:
- `alert_id` MUST match pattern `^ca-[a-zA-Z0-9_-]+-v\d+$`
- `version` MUST be ≥ 1
- `content_blocks` MUST contain at least the `en-AU` key
- `change_summary` MUST be non-empty for `change_type != initial`
- `referenced_alert_id` MUST be non-null for `correction` and `all_clear` types
- `approval_justification` MUST be non-empty when `approval_action == reject`
- `confidence` MUST be 0.0–1.0 inclusive

**Cosmos DB container**: `public-alerts`
**Partition key**: `/tenant_id`

---

### 2. ContentBlock

Embedded model — alert content for a single language.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `language_code` | `str` | One of supported languages | ISO language code |
| `title` | `str` | ≤ 200 chars | Alert title (includes "CORRECTION:" prefix for corrections) |
| `body` | `str` | ≤ 1,200 chars (FR-010) | Alert body — what/where/when |
| `action_items` | `str` | ≤ 500 chars | What to do, where to get help |
| `generation_method` | `GenerationMethod` enum | Required | How this content was generated |
| `content_safety_result` | `str` | `passed`, `failed_with_fallback` | Per-language safety result |
| `content_safety_failure_reason` | `str \| None` | Set on failure | `blocked_keyword`, `language_mismatch`, `length_exceeded` |
| `back_translation_score` | `float \| None` | 0.0–1.0, null for en-AU | Cosine similarity score |
| `back_translation_flagged` | `bool` | Default: `False` | True if score < threshold |
| `translation_unavailable` | `bool` | Default: `False` | True if template was missing (CHK008 fallback) |

---

### 3. AudienceSegment

Audience targeting entity — defines a group of recipients by zone, vulnerability, and language.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `segment_id` | `str` | UUID, PK | Unique segment identifier |
| `alert_id` | `str` | FK to PublicAlert | Alert this segment belongs to |
| `zone_level` | `int` | 1, 2, or 3 | Geographic zone level (1=immediate, 2=likely, 3=possible) |
| `zone_boundary` | `dict` | GeoJSON polygon | Zone boundary from evacuation agent |
| `population_estimate` | `int` | ≥ 0 | Estimated population in segment |
| `estimated_segment_size` | `int` | ≥ 0 | Estimated delivery target count |
| `vulnerability_categories` | `list[str]` | Values: `aged_care`, `hospital`, `school`, `disability_services` | Empty for general population |
| `preferred_language` | `str` | Default: `en-AU` | Language code for this segment |
| `urgency_level` | `UrgencyLevel` enum | Required | `immediate`, `watch`, `advisory` |
| `priority` | `SegmentPriority` enum | Required | `critical` (vulnerable), `high` (Zone 1), `moderate` (Zone 2/3) |
| `delivery_channels` | `list[ChannelType]` | ≥ 1 | Channels assigned to this segment |
| `missing_data_flags` | `list[str]` | Optional | Notes about missing demographic/vulnerability data |

**Validation rules**:
- `zone_level` MUST be 1, 2, or 3
- `vulnerability_categories` items MUST be from the allowed set
- `preferred_language` MUST be one of the 6 supported languages
- Segments with non-empty `vulnerability_categories` MUST have `priority=critical`

---

### 4. DeliveryRecord

Delivery tracking entity — one record per alert × segment × channel combination.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `delivery_id` | `str` | UUID, PK | Unique delivery identifier |
| `alert_id` | `str` | FK to PublicAlert | Alert being delivered |
| `alert_version` | `int` | ≥ 1 | Alert version at time of delivery |
| `channel` | `ChannelType` enum | Required | `sms`, `push`, `emergency_broadcast` |
| `audience_segment_id` | `str` | FK to AudienceSegment | Target segment |
| `language_used` | `str` | One of supported languages | Language delivered |
| `delivery_status` | `DeliveryStatus` enum | Required | `pending`, `in_progress`, `accepted`, `delivered`, `failed`, `retrying`, `skipped`, `unconfigured` |
| `attempt_count` | `int` | 0–max_retries+1, default: 0 | Number of attempts made |
| `max_retries` | `int` | Default: 3 | Maximum retry count |
| `retry_backoff_intervals` | `list[float]` | Default: `[1.0, 2.0, 4.0]` | Exponential backoff intervals (seconds) |
| `failure_reason` | `str \| None` | Set on failure | Specific failure description |
| `content_payload` | `str` | Channel-formatted content | Formatted message for this channel |
| `segment_count` | `int \| None` | SMS only, ≥ 1 | Number of SMS segments (R-013) |
| `is_deduplicated` | `bool` | Default: `False` | True if recipient appeared in higher-priority segment |
| `deduplicated_by_segment_id` | `str \| None` | Set when deduplicated | Higher-priority segment that took precedence |
| `initiated_at` | `datetime \| None` | Set when first attempt starts | First delivery attempt timestamp |
| `completed_at` | `datetime \| None` | Set on final outcome | Completion timestamp (success or final failure) |
| `delivery_duration_ms` | `int \| None` | Computed | Time from initiation to completion |
| `tenant_id` | `str` | Required, partition key component | Tenant isolation |

**Cosmos DB container**: `delivery-records`
**Partition key**: `/tenant_id`

---

### 5. CommunicationDecisionRecord

Audit trail entity — append-only record of every processing step.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `record_id` | `str` | UUID, PK | Unique audit record identifier |
| `handoff_id` | `str \| None` | When applicable | Originating handoff |
| `alert_id` | `str \| None` | When applicable | Associated alert |
| `delivery_id` | `str \| None` | When applicable | Associated delivery record |
| `decision_type` | `CommunicationDecisionType` enum | Required | Type of decision (see enum below) |
| `content_safety_results` | `dict[str, str] \| None` | Per-language breakdown | Language → safety result |
| `generation_method` | `str \| None` | When applicable | `llm`, `template`, `template_fallback`, `safety_fallback` |
| `confidence` | `float \| None` | 0.0–1.0 | Confidence at time of decision |
| `confidence_penalties_applied` | `list[str] \| None` | Optional | List of penalties applied (traceability) |
| `processing_duration_ms` | `int \| None` | ≥ 0 | Processing time for this step |
| `agent_version` | `str` | Required | Agent version string |
| `config_version` | `str` | Required | Config hash from `compute_config_hash()` |
| `input_snapshot` | `dict \| None` | For key decisions | Snapshot of inputs for reproducibility |
| `output_summary` | `str \| None` | For key decisions | Summary of outputs produced |
| `escalation_details` | `dict \| None` | For escalation events | Source/target commander, elapsed time |
| `degradation_details` | `dict \| None` | For degradation events | Service affected, fallback used |
| `flush_source` | `str \| None` | Set on flush | `direct`, `memory_buffer`, `file_spill` |
| `timestamp` | `datetime` | Auto-set, UTC | Decision timestamp |

**CommunicationDecisionType enum** (18 values):

```python
class CommunicationDecisionType(str, Enum):
    handoff_received = "handoff_received"
    handoff_rejected = "handoff_rejected"
    duplicate_discarded = "duplicate_discarded"
    alert_drafted = "alert_drafted"
    content_safety_evaluated = "content_safety_evaluated"
    back_translation_below_threshold = "back_translation_below_threshold"
    alert_versioned = "alert_versioned"
    approval_requested = "approval_requested"
    approval_action = "approval_action"
    escalation_triggered = "escalation_triggered"
    delivery_initiated = "delivery_initiated"
    delivery_succeeded = "delivery_succeeded"
    delivery_failed = "delivery_failed"
    audience_segmented = "audience_segmented"
    degradation_detected = "degradation_detected"
    content_safety_failure = "content_safety_failure"
    health_status_changed = "health_status_changed"
    template_fallback = "template_fallback"
```

**Cosmos DB container**: `communication-decisions`
**Partition key**: `/tenant_id`

---

### 6. EscalationEvent

Embedded model — records a single escalation in the approval workflow.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `level` | `int` | 1–3 | Escalation level |
| `from_commander_id` | `str` | Required | Commander who didn't respond |
| `to_commander_id` | `str \| None` | None if held for next available | Target commander |
| `elapsed_minutes` | `float` | ≥ 0 | Time waited before escalation |
| `escalated_at` | `datetime` | UTC | When escalation occurred |
| `held_for_next_available` | `bool` | Default: `False` | True at level 3 when no commander available |

---

### 7. ContentSafetyDetail

Embedded model — per-language content safety result.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `language_code` | `str` | Required | Language checked |
| `passed` | `bool` | Required | Whether validation passed |
| `failure_reason` | `str \| None` | Set on failure | `blocked_keyword`, `language_mismatch`, `length_exceeded` |
| `original_text_length` | `int` | ≥ 0 | LLM-generated text length |
| `fallback_used` | `bool` | Default: `False` | Whether template fallback was used |

---

## Enums

```python
class AlertStatus(str, Enum):
    drafting = "drafting"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    delivering = "delivering"
    delivered = "delivered"
    partially_delivered = "partially_delivered"
    superseded = "superseded"
    expired = "expired"
    cancelled = "cancelled"

class ChangeType(str, Enum):
    initial = "initial"
    update = "update"
    correction = "correction"
    all_clear = "all_clear"

class ChannelType(str, Enum):
    sms = "sms"
    push = "push"
    emergency_broadcast = "emergency_broadcast"

class DeliveryStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    delivered = "delivered"
    failed = "failed"
    retrying = "retrying"

class GenerationMethod(str, Enum):
    llm = "llm"
    template = "template"
    template_fallback = "template_fallback"
    safety_fallback = "safety_fallback"

class ContentSafetyResult(str, Enum):
    passed = "passed"
    failed_with_fallback = "failed_with_fallback"
    not_checked = "not_checked"

class ApprovalMode(str, Enum):
    human_approved = "human_approved"
    escalated = "escalated"

class UrgencyLevel(str, Enum):
    immediate = "immediate"
    watch = "watch"
    advisory = "advisory"

class SegmentPriority(str, Enum):
    critical = "critical"
    high = "high"
    moderate = "moderate"
```

---

## Embedded Support Types

### AuditBufferEntry

Used by the three-tier audit degradation writer.

| Field | Type | Description |
|-------|------|-------------|
| `record` | `CommunicationDecisionRecord` | The audit record |
| `buffered_at` | `datetime` | When buffered (UTC) |

---

## Alert Template Schema

Static JSON files in `data/alert-templates/{language_code}.json`:

```json
[
  {
    "template_id": "evacuation-cyclone-severe",
    "hazard_type": "cyclone",
    "severity": "severe",
    "language_code": "en-AU",
    "title_template": "SEVERE CYCLONE WARNING — {location}",
    "body_template": "A severe cyclone is approaching {location}. Conditions are expected to deteriorate from {time}. Wind gusts may exceed {wind_speed}. {severity_detail}.",
    "action_items_template": "EVACUATE immediately if directed by emergency services. Move to higher ground. Listen to ABC Radio for updates. Call 000 for life-threatening emergencies. Visit {help_url} for evacuation centres."
  }
]
```

**Hazard types**: `cyclone`, `bushfire`, `flood`, `storm`, `earthquake`, `tsunami`, `general`
**Alert types**: `evacuation`, `shelter_in_place`, `all_clear`, `general_warning`
**Placeholder syntax**: `{placeholder_name}` — validated before interpolation; missing values replaced with `[unknown]` and logged

---

## Configurable Parameters

All parameters read from environment variables at startup, frozen for process lifetime.

| Parameter | Env Var | Default | Type | Description |
|-----------|---------|---------|------|-------------|
| Supported languages | `SUPPORTED_LANGUAGES` | `en-AU,zh-Hans,ar,vi,el,it` | `str` (CSV) | Languages for alert generation |
| Back-translation threshold | `BACK_TRANSLATION_THRESHOLD` | `0.85` | `float` | Cosine similarity minimum |
| Alert max tokens | `ALERT_MAX_TOKENS` | `180` | `int` | Max output tokens per language |
| Handoff dedup window | `HANDOFF_DEDUP_WINDOW_MINUTES` | `30` | `int` | Deduplication window (minutes) |
| Approval escalation timeout | `APPROVAL_ESCALATION_TIMEOUT_MINUTES` | `15` | `int` | Time before auto-escalation |
| Max escalation levels | `MAX_ESCALATION_LEVELS` | `3` | `int` | Maximum escalation depth |
| Alert expiry hours | `ALERT_EXPIRY_HOURS` | `24` | `int` | TTL for alert expiry |
| Delivery max retries | `DELIVERY_MAX_RETRIES` | `3` | `int` | Max retries per channel |
| Delivery channels | `DELIVERY_CHANNELS` | `sms,push,emergency_broadcast` | `str` (CSV) | Active delivery channels |
| EAS endpoint URL | `EAS_ENDPOINT_URL` | *(required)* | `str` | Emergency broadcast webhook |
| SMS max length | `SMS_MAX_LENGTH` | `612` | `int` | Max SMS characters (multi-part) |
| Content max length | `CONTENT_MAX_LENGTH` | `1200` | `int` | Max chars per language block |
| Audit buffer capacity | `AUDIT_BUFFER_CAPACITY` | `10000` | `int` | In-memory audit buffer size |
| Audit buffer file path | `AUDIT_BUFFER_FILE_PATH` | `communication_audit.jsonl` | `str` | JSONL spill file path |
| Version conflict max retries | `VERSION_CONFLICT_MAX_RETRIES` | `3` | `int` | OCC retry limit |
| Agent version | `AGENT_VERSION` | `0.1.0` | `str` | Agent version string |
| Port | `PORT` | `8084` | `int` | Health endpoint port |
| Confidence base | `CONFIDENCE_BASE` | `1.0` | `float` | Starting confidence for alerts |
| Freshness penalty factor | `FRESHNESS_PENALTY_FACTOR` | `0.9` | `float` | Data freshness confidence penalty |
| Back-translation penalty factor | `BACK_TRANSLATION_PENALTY_FACTOR` | `0.9` | `float` | Back-translation quality penalty |
| Fallback reduction factor | `FALLBACK_REDUCTION_FACTOR` | `0.8` | `float` | LLM fallback confidence penalty |
| Queue scale-out threshold | `QUEUE_SCALE_OUT_THRESHOLD` | `10` | `int` | Queue depth to trigger scale-out |
| Queue scale-in threshold | `QUEUE_SCALE_IN_THRESHOLD` | `3` | `int` | Queue depth to trigger scale-in |
| Scale-in cooldown minutes | `SCALE_IN_COOLDOWN_MINUTES` | `5` | `int` | Cooldown before scale-in |

---

## Cosmos DB Containers

| Container | Partition Key | TTL | Purpose |
|-----------|--------------|-----|---------|
| `public-alerts` | `/tenant_id` | None (manual expiry via status) | Alert records with versions |
| `communication-decisions` | `/tenant_id` | None (infinite retention) | Append-only audit trail |
| `delivery-records` | `/tenant_id` | None | Delivery tracking per channel per segment |

---

## Relationships

```
AgentHandoffEvent (upstream)
  │
  │ 1:1 triggers
  ▼
PublicAlert
  │
  ├── 1:N ──► AudienceSegment
  │              │
  │              └── 1:N ──► DeliveryRecord (per channel per segment)
  │
  ├── 1:N ──► ContentBlock (per language, embedded)
  │
  ├── 1:N ──► ContentSafetyDetail (per language, embedded)
  │
  ├── 0:N ──► EscalationEvent (embedded list)
  │
  └── 1:N ──► CommunicationDecisionRecord (audit trail)

PublicAlert ──► PublicAlert (via referenced_alert_id for corrections/all-clear)
PublicAlert ──► PublicAlert (via superseded status for versioning)
```

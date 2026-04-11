# Data Model: Risk Assessment Agent

**Feature**: 012-risk-assessment-agent  
**Date**: 2026-04-15  
**Status**: Complete

---

## Entity: AgentHandoffEvent (consumed from monitoring, produced for downstream)

**Source**: `apps/agents/common/handoffs.py` (existing shared model)  
**Direction**: Inbound from Monitoring Agent; outbound to Communication, Evacuation, Resource Allocation agents

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Unique handoff identifier |
| `incident_id` | `str` | Yes | Associated incident ID |
| `source_agent` | `str` | Yes | Originating agent (inbound: `monitoring`, outbound: `risk_assessment`) |
| `target_agent` | `str` | Yes | Target agent (inbound: `risk_assessment`, outbound: `communication`/`evacuation`/`resource_allocation`) |
| `scope_key` | `str` | Yes | Incident scope key for routing |
| `confidence` | `float` | Yes | Source agent's confidence in the escalation |
| `payload` | `dict` | Yes | Handoff-specific data (signal summary, recommendation, etc.) |
| `tenant_id` | `str` | Yes | `live` or simulation tenant ID |
| `status` | `str` | Yes | `pending` → `delivered` / `retrying` / `dead_lettered` |
| `retry_count` | `int` | Yes | Current retry attempt |
| `max_retries` | `int` | Yes | Maximum retry attempts (default: 3) |
| `created_at` | `datetime` | Yes | When the handoff was created |
| `delivered_at` | `datetime \| None` | No | When successfully delivered |
| `failed_at` | `datetime \| None` | No | When permanently failed |

**Inbound payload schema** (from Monitoring Agent):
```json
{
  "category": "fire",
  "sourceKind": "authoritative",
  "signalSummary": {
    "category": "fire",
    "sourceKind": "authoritative",
    "incidentId": "inc-001"
  }
}
```

**Outbound payload schema** (to downstream agents):
```json
{
  "recommendationId": "rec-inc001-pa-001",
  "summary": "...",
  "explanation": "...",
  "assessmentId": "ha-inc001-spread-v3"
}
```

---

## Entity: HazardAssessment (owned — to be extended)

**Storage**: Azure Cosmos DB — container `risk-assessments`  
**Partition key**: `/incident_scope_key` (format: `{tenant_id}:{incident_id}`)  
**TTL**: None (immutable, versioned)  
**Source**: `packages/domain/src/domain/models/hazard_assessment.py` (existing, to be extended)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hazard_assessment_id` | `str` | Yes | Unique identifier (format: `ha-{incident_id}-{type}-v{N}`) |
| `incident_id` | `str` | Yes | Associated incident |
| `assessment_type` | `AssessmentType` | Yes | `spread_prediction` \| `impact_projection` \| `route_risk` \| `infrastructure_risk` \| `community_impact` |
| `input_signal_ids` | `list[str]` | Yes | All contributing signal IDs |
| `version` | `int` | Yes | Monotonically increasing per incident+type |
| `confidence_score` | `float` | Yes | Raw weighted confidence (0.0–1.0) |
| `confidence_adjusted` | `float` | Yes | Final confidence after all adjustments |
| `confidence_level` | `ConfidenceLevel` | Yes | `low` (<0.4) \| `medium` (0.4–0.69) \| `high` (≥0.7) |
| `severity_level` | `SeverityLevel` | Yes | `low` \| `moderate` \| `high` \| `critical` (AIDR-aligned) |
| `summary` | `str` | Yes | Human-readable hazard impact summary |
| `hazard_map` | `HazardMap \| None` | No | Structured JSON (GeoJSON polygon, severity, time horizon, population) |
| `generation_method` | `str` | Yes | `llm` \| `template_fallback` \| `safety_fallback` |
| `generation_timestamp` | `datetime` | Yes | When assessment was produced |
| `valid_until` | `datetime` | Yes | Expiry (configurable per hazard type, default 4h) |
| `status` | `str` | Yes | `active` \| `superseded` \| `expired` |
| `model_deployment_id` | `str \| None` | No | Azure OpenAI deployment used |
| `prompt_template_version` | `str` | Yes | Version of prompt template |
| `configuration_version` | `str` | Yes | Hash of active config values |
| `input_snapshot` | `dict` | Yes | Complete input data for reproducibility |
| `contradiction_detected` | `bool` | No | Whether contradictions were found |
| `contradiction_details` | `list[dict] \| None` | No | Contradicting signal pairs and sources |
| `stale_signal_ids` | `list[str]` | No | Signals below freshness threshold |
| `related_incident_ids` | `list[str]` | No | Reserved for v2 cross-incident correlation |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |

**Validation rules**:
- `confidence_score` and `confidence_adjusted` must be in [0.0, 1.0]
- `version` must be ≥ 1
- `valid_until` must be after `generation_timestamp`
- `confidence_level` must be derived from `confidence_adjusted` using thresholds: `low` (<0.4), `medium` (0.4–0.69), `high` (≥0.7)
- Immutable once persisted — updates create new versions

**State transitions**:
- `active` → `superseded`: When a new version is created for the same incident+type
- `active` → `expired`: When `valid_until` elapses with no newer version
- `superseded`/`expired` → (terminal): No further transitions; records remain queryable

---

## Entity: Recommendation (owned — to be extended)

**Storage**: Azure Cosmos DB — container `risk-recommendations`  
**Partition key**: `/incident_scope_key`  
**Source**: `packages/domain/src/domain/models/recommendation.py` (existing, to be extended)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recommendation_id` | `str` | Yes | Unique identifier (format: `rec-{incident_id}-{type_abbrev}-{seq}`) |
| `incident_id` | `str` | Yes | Associated incident |
| `assessment_id` | `str` | Yes | Originating hazard assessment |
| `type` | `RecommendationType` | Yes | `evacuation` \| `resource_allocation` \| `coordination` \| `public_alert` \| `infrastructure_action` |
| `summary` | `str` | Yes | Brief action summary |
| `explanation` | `str` | Yes | Detailed explanation with signal ID references |
| `supporting_signal_ids` | `list[str]` | Yes | All contributing signals |
| `required_approval_level` | `str` | Yes | Default: `incident_commander` |
| `confidence_level` | `ConfidenceLevel` | Yes | Derived from assessment confidence |
| `confidence_score` | `float` | Yes | Numeric confidence (0.0–1.0) |
| `severity_level` | `SeverityLevel` | Yes | From parent assessment |
| `status` | `str` | Yes | `proposed` → `under_review` → `approved`/`rejected`/`escalated` → `executed`/`expired` |
| `proposed_by_agent` | `str` | Yes | Always `risk_assessment` |
| `generation_method` | `str` | Yes | `llm` \| `template_fallback` \| `safety_fallback` |
| `model_deployment_id` | `str \| None` | No | Azure OpenAI deployment used |
| `token_usage` | `dict \| None` | No | LLM token counts |
| `override_by_user_id` | `str \| None` | No | User who overrode (if applicable) |
| `override_by_role` | `str \| None` | No | Role of overriding user |
| `override_justification` | `str \| None` | No | Reason for override |
| `override_timestamp` | `datetime \| None` | No | When override occurred |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |

**Status lifecycle**:
```
proposed → under_review → approved → executed
                        → rejected
                        → escalated → executed / expired
proposed → expired (if assessment expires without review)
```

**Override rules**:
- Override creates a new recommendation version linked to original via `original_recommendation_id`
- Original recommendation is immutable; its status updates to `under_review` or `rejected`
- Override audit record includes `override_by_user_id`, `override_by_role`, `override_justification`, `override_timestamp`

---

## Entity: RiskAssessmentDecisionRecord (owned — audit trail)

**Storage**: Azure Cosmos DB — container `risk-assessment-decisions`  
**Partition key**: `/incident_scope_key`  
**TTL**: None (infinite retention, append-only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` (UUID) | Yes | Unique record identifier |
| `handoff_id` | `str` | Yes | Originating handoff ID |
| `input_signal_ids` | `list[str]` | Yes | Signal IDs involved in this step |
| `assessment_id` | `str \| None` | No | Resulting assessment ID |
| `recommendation_id` | `str \| None` | No | Resulting recommendation ID |
| `hazard_type` | `str \| None` | No | Hazard type being assessed |
| `severity_level` | `str \| None` | No | Assessed severity level |
| `confidence_raw` | `float` | Yes | Raw weighted confidence |
| `confidence_adjusted` | `float` | Yes | Final adjusted confidence |
| `version` | `int \| None` | No | Assessment version number |
| `decision_type` | `DecisionType` | Yes | Processing step type (enum) |
| `model_id` | `str \| None` | No | LLM deployment ID |
| `prompt_template_version` | `str` | Yes | Prompt template version |
| `processing_duration_ms` | `float` | Yes | Processing time for this step |
| `decision_rationale` | `str` | Yes | Human-readable decision explanation |
| `generation_method` | `str` | Yes | `llm` \| `template_fallback` \| `safety_fallback` |
| `escalation_targets` | `list[str]` | No | Downstream agents targeted |
| `agent_version` | `str` | Yes | Semantic version of agent code |
| `configuration_version` | `str` | Yes | Hash of active config |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `timestamp` | `datetime` (UTC) | Yes | When recorded |
| `buffered_at` | `datetime \| None` | No | When buffered (degradation) |
| `flush_source` | `str \| None` | No | `direct` \| `memory_buffer` \| `file_buffer` |

**DecisionType enum values** (12 types):

| Value | Description |
|-------|-------------|
| `handoff_received` | Handoff acknowledged and validated |
| `handoff_rejected` | Handoff rejected (invalid structure, missing incident) |
| `duplicate_discarded` | Duplicate handoff discarded by idempotency check |
| `signals_retrieved` | Signals successfully retrieved from store |
| `assessment_generated` | Hazard assessment produced |
| `recommendation_generated` | Recommendation produced |
| `handoff_created` | Downstream agent handoff created |
| `handoff_delivered` | Downstream handoff successfully delivered |
| `handoff_dead_lettered` | Downstream handoff permanently failed |
| `contradiction_detected` | Contradictory signals identified |
| `degradation_detected` | Service degradation event (LLM, Cosmos, signal store) |
| `content_safety_failure` | LLM output failed content safety validation |

---

## Entity: HazardMap (embedded in HazardAssessment)

**Storage**: Embedded JSON within `HazardAssessment.hazard_map`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `affected_area` | `dict` (GeoJSON Polygon) | Yes | Geographic polygon of affected area |
| `severity_level` | `SeverityLevel` | Yes | Assessment severity |
| `hazard_type` | `str` | Yes | Type of hazard (bushfire, cyclone, etc.) |
| `confidence_score` | `float` | Yes | Assessment confidence |
| `time_horizon` | `str` | Yes | Prediction time window (e.g., `4h`, `12h`, `24h`) |
| `population_estimate` | `int \| None` | No | Estimated affected population |

---

## Entity: VersionCounter (internal — concurrency control)

**Storage**: Azure Cosmos DB — container `risk-assessments`  
**Partition key**: `/incident_scope_key`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | `{incident_id}_{assessment_type}_counter` |
| `current_version` | `int` | Yes | Current version number |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `_etag` | `str` | Auto | Cosmos DB-managed ETag for OCC |

**Concurrency pattern**:
1. Read counter + `_etag`
2. Increment `current_version`
3. `replace_item` with `If-Match: {_etag}`
4. On 412 Precondition Failed: re-read, re-increment, retry (max 3)

---

## Relationships

```
AgentHandoffEvent (from Monitoring)
    └── triggers → HazardAssessment (1:1 per assessment type)
        ├── produces → Recommendation (1:N)
        │   └── triggers → AgentHandoffEvent (to downstream, 0..1 per recommendation)
        └── has → HazardMap (0..1, embedded)

VersionCounter ──guards──→ HazardAssessment.version (per incident+type)

All processing steps → RiskAssessmentDecisionRecord (audit trail)
```

---

## Signal Category → Assessment Type Mapping

| Signal Category | Assessment Type | Default Severity (Fallback) |
|----------------|----------------|----------------------------|
| `fire` | `spread_prediction` | `high` |
| `weather` | `impact_projection` | `moderate` |
| `hydrology` | `impact_projection` | `moderate` |
| `geohazard` | `impact_projection` | `critical` |
| `infrastructure` | `infrastructure_risk` | `moderate` |
| `community_report` | `community_impact` | `moderate` |
| `social_report` | `community_impact` | `moderate` |

**Disaster type → severity mapping** (for LLM fallback mode):
| Signal Category | Default Severity |
|----------------|-----------------|
| `fire` | `high` |
| `cyclone` | `critical` |
| `flood` | `high` |
| `earthquake` | `critical` |
| `tsunami` | `critical` |
| (all others) | `moderate` |

---

## Escalation Thresholds

| Target Agent | Recommendation Type | Confidence Threshold | Severity Threshold |
|-------------|--------------------|--------------------|-------------------|
| Communication | `public_alert` | ≥ 0.7 | — |
| Evacuation | `evacuation` | ≥ 0.6 | ≥ `high` |
| Resource Allocation | `resource_allocation` | — (task-based) | — |

---

## Configurable Parameters

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| Source weight — authoritative | `SOURCE_WEIGHT_AUTHORITATIVE` | `2.0` | BoM, Geoscience Australia |
| Source weight — IoT | `SOURCE_WEIGHT_IOT` | `1.0` | Sensor networks |
| Source weight — social | `SOURCE_WEIGHT_SOCIAL` | `0.5` | Social media, crowd-sourced |
| Stale signal threshold | `STALE_SIGNAL_THRESHOLD` | `0.5` | Freshness score below this = stale |
| Handoff dedup window | `HANDOFF_DEDUP_WINDOW_MINUTES` | `10` | Minutes for duplicate detection |
| Assessment validity — default | `ASSESSMENT_VALIDITY_HOURS_DEFAULT` | `4` | Hours until assessment expires |
| Assessment validity — fire | `ASSESSMENT_VALIDITY_HOURS_FIRE` | `2` | Shorter validity for fast-moving fires |
| Assessment validity — cyclone | `ASSESSMENT_VALIDITY_HOURS_CYCLONE` | `6` | Longer validity for slow cyclone tracking |
| Contradiction reduction factor | `CONTRADICTION_REDUCTION_FACTOR` | `0.7` | Multiplicative reduction on contradiction |
| Fallback reduction factor | `FALLBACK_REDUCTION_FACTOR` | `0.8` | Multiplicative reduction when LLM unavailable |
| Communication escalation threshold | `ESCALATION_THRESHOLD_COMMUNICATION` | `0.7` | Confidence threshold for public alert handoff |
| Evacuation escalation threshold | `ESCALATION_THRESHOLD_EVACUATION` | `0.6` | Confidence threshold for evacuation handoff |
| Audit buffer capacity | `AUDIT_BUFFER_CAPACITY` | `10000` | In-memory ring buffer size |
| Audit buffer file path | `AUDIT_BUFFER_FILE_PATH` | `/var/log/risk-agent/audit-buffer.jsonl` | Tier 3 spill location |
| Max reasoning summary length | `MAX_REASONING_SUMMARY_LENGTH` | `500` | Truncation limit for audit rationale |
| Agent version | `AGENT_VERSION` | `0.1.0` | Semantic version |

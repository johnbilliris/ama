# Contract: Assessment Processing Pipeline

**Feature**: 012-risk-assessment-agent  
**Date**: 2026-04-15  
**Type**: Processing pipeline contract

---

## Overview

The Risk Assessment Agent processes inbound `AgentHandoffEvent` messages from the Monitoring Agent through an 8-stage pipeline, producing versioned `HazardAssessment` and `Recommendation` records, with optional downstream `AgentHandoffEvent` escalation to Communication, Evacuation, and Resource Allocation agents.

---

## Pipeline Stages

### Stage 1: Handoff Intake and Validation

**Input**: Raw `AgentHandoffEvent` from Azure Service Bus  
**Output**: Validated handoff or rejection audit record  
**SLA**: Acknowledge within 5 seconds of delivery

| Check | Action on Failure |
|-------|-------------------|
| Pydantic schema validation | Reject with `handoff_rejected` audit record |
| `target_agent == "risk_assessment"` | Reject with `handoff_rejected` audit record |
| `incident_id` exists in incident store | Reject with `handoff_rejected` audit record |
| Idempotency check (handoff_id dedup) | Discard with `duplicate_discarded` audit record |
| Tenant validation (simulation vs live) | Route to appropriate processing context |

### Stage 2: Signal Retrieval

**Input**: Validated handoff with signal references  
**Output**: Retrieved `Signal` objects with provenance  
**Degradation**: If signal store is partially unavailable, proceed with available signals; reduce confidence proportionally.

| Outcome | Action |
|---------|--------|
| All signals retrieved | Continue with full signal set |
| Some signals missing | Log missing IDs, reduce confidence by `missing_count / total_count`, proceed |
| All signals missing | Log error, produce low-confidence assessment with degradation flag |

### Stage 3: Multi-Source Correlation

**Input**: Retrieved signals  
**Output**: Weighted confidence score, source analysis

**Formula**:
```
weighted_confidence = Σ(signal_i.confidence * weight_i * signal_i.freshness)
                    / Σ(weight_i * signal_i.freshness)
```

Where `weight_i` = `SOURCE_WEIGHT_AUTHORITATIVE` (2.0) | `SOURCE_WEIGHT_IOT` (1.0) | `SOURCE_WEIGHT_SOCIAL` (0.5)

| Check | Result |
|-------|--------|
| Any signal freshness < `STALE_SIGNAL_THRESHOLD` | Flag as stale in assessment |
| All signals stale | Set confidence_level to `low`, block escalation |
| Signals from > 1 source type | Record diversity in assessment |
| Assessment relies primarily on unverified sources | Note in assessment summary |

### Stage 4: Contradiction Detection

**Input**: Correlated signals  
**Output**: Contradiction flag, adjusted confidence

| Condition | Action |
|-----------|--------|
| Opposing risk trajectories detected | Reduce confidence by 30% (`× 0.7`), flag for human review, record in audit |
| No contradictions | No adjustment |
| Multiple contradiction pairs | Single 30% reduction, each pair individually logged |

**Contradiction criteria**: Two signals for the same incident and geographic area indicate opposing risk trends (one increasing, one decreasing) for the same hazard parameter.

### Stage 5: Assessment Generation

**Input**: Correlated signals, adjusted confidence, contradiction analysis  
**Output**: Versioned `HazardAssessment`

| Step | Detail |
|------|--------|
| Derive assessment type | Signal category → assessment type mapping |
| Assign version | Optimistic concurrency via version counter (Cosmos DB etag) |
| Compute severity | From signal category, confidence, and population estimate (AIDR-aligned) |
| Generate summary | LLM with template fallback; content safety validation |
| Set valid_until | `generation_timestamp + validity_duration` per hazard type |
| Store input snapshot | All signals, model version, config hash for reproducibility |

**LLM fallback mode** (Azure OpenAI unavailable):
- `generation_method = "template_fallback"`
- Confidence reduced by 20% (`× 0.8`)
- Severity from default category-to-severity mapping
- Severity downgraded one level if adjusted confidence < 0.4 (`low` is floor)

### Stage 6: Recommendation Generation

**Input**: Completed `HazardAssessment`  
**Output**: One or more `Recommendation` records

| Assessment Type | Recommendation Types Generated |
|----------------|-------------------------------|
| `spread_prediction` | `public_alert`, `evacuation` (if severity ≥ high) |
| `impact_projection` | `public_alert`, `resource_allocation` (if coordination tasks) |
| `route_risk` | `evacuation` |
| `infrastructure_risk` | `infrastructure_action`, `resource_allocation` |
| `community_impact` | `public_alert`, `resource_allocation` (if coordination tasks) |

All recommendations include:
- Signal ID references in explanation (enforced: missing IDs appended)
- `required_approval_level = "incident_commander"` (configurable)
- `proposed_by_agent = "risk_assessment"`

### Stage 7: Downstream Escalation

**Input**: Generated `Recommendation` records  
**Output**: `AgentHandoffEvent` records for qualifying recommendations

| Target Agent | Trigger | Payload |
|-------------|---------|---------|
| `communication` | `public_alert` with confidence ≥ 0.7 | recommendation_id, summary, explanation |
| `evacuation` | `evacuation` with severity ≥ `high` AND confidence ≥ 0.6 | recommendation_id, summary, assessment_id |
| `resource_allocation` | Any recommendation with coordination tasks | recommendation_id, summary, assessment_id |

**Delivery**: Exponential backoff, max 3 retries. Dead-lettered handoffs surfaced to incident commanders.

**No escalation**: Recommendations below threshold stored for human review only.

### Stage 8: Audit Finalisation

**Input**: All processing artifacts  
**Output**: Comprehensive audit record for each processing step

Every stage produces one or more `RiskAssessmentDecisionRecord` entries. The finalisation stage verifies completeness: handoff_id processed vs audit records created.

---

## Latency Budget (10-second SLA)

| Stage | Target | Notes |
|-------|--------|-------|
| 1. Handoff intake | ≤ 500ms | Pydantic validation + dedup lookup |
| 2. Signal retrieval | ≤ 1,500ms | Cosmos DB reads (batch) |
| 3. Multi-source correlation | ≤ 200ms | In-memory computation |
| 4. Contradiction detection | ≤ 200ms | In-memory analysis |
| 5. Assessment generation | ≤ 5,000ms | LLM call (primary bottleneck); template fallback ≤ 100ms |
| 6. Recommendation generation | ≤ 500ms | In-memory derivation + content safety |
| 7. Downstream escalation | ≤ 1,000ms | Service Bus publish (async, non-blocking) |
| 8. Audit finalisation | ≤ 500ms | Cosmos DB write (async batch) |
| **Total** | **≤ 10,000ms** | SLA breach logged if exceeded; processing still completes |

---

## Error Handling

| Error | Behaviour |
|-------|-----------|
| Malformed handoff | Reject, audit, do not process |
| Missing incident | Reject, audit, do not process |
| Signal store timeout | Proceed with available signals, reduce confidence |
| LLM timeout/error | Template fallback, 20% confidence reduction |
| Content safety failure | Replace with template text, audit |
| Cosmos DB write failure | Three-tier degradation (memory → file) |
| Downstream delivery failure | Retry 3× with exponential backoff, then dead-letter |
| Version counter conflict | Retry 3× with jitter, fallback to UUID-suffixed version |

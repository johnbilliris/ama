# Contract: Signal Processing Pipeline

**Feature**: 010-monitoring-agent  
**Date**: 2026-04-11  
**Type**: Internal processing pipeline

---

## Overview

The Monitoring Agent exposes a signal processing pipeline that consumes `SignalEnvelope` messages from Azure Service Bus and produces `AgentHandoffEvent` records and `MonitoringDecisionRecord` audit entries. This contract defines the processing stages, their ordering, and the inputs/outputs at each stage.

---

## Pipeline Stages

### Stage 1: Input Validation

**Input**: Raw `SignalEnvelope` from Azure Service Bus  
**Output**: Validated `SignalEnvelope` or rejection

```
IF SignalEnvelope fails Pydantic validation:
    → Emit audit record (decision=validation_failed)
    → Emit metric: signal_validation_failures_total
    → STOP processing
ELSE:
    → Proceed to Stage 2
```

### Stage 2: Deduplication Check

**Input**: Validated `SignalEnvelope`  
**Output**: Unique signal or discard

```
IF signal_id exists in dedup cache (TTL = SIGNAL_DEDUP_WINDOW_MINUTES):
    → Emit audit record (decision=discarded, reasoning="duplicate_signal_id")
    → STOP processing
ELSE:
    → Add signal_id to dedup cache
    → Proceed to Stage 3
```

### Stage 3: Freshness Assessment

**Input**: Validated, unique `SignalEnvelope`  
**Output**: Updated `DataFreshnessIndicator` for the source

```
Update DataFreshnessIndicator for source:
    → Update last_signal_received_at
    → Recompute status (healthy/degraded/offline)
    → IF status changed: emit audit record (decision=degradation_detected)
    → Emit metric: data_source_freshness{source_id, status}
```

### Stage 4: Misinformation Evaluation (conditional)

**Input**: Signal with `validationStatus=escalated`  
**Output**: Classification result (credible | suspicious | misinformation | held_for_review)

```
IF validationStatus != "escalated":
    → Skip to Stage 5

Run LLM classification with timeout (LLM_EVAL_TIMEOUT_SECONDS):
    IF LLM returns "misinformation":
        → Emit audit record (decision=blocked, llm_classification=misinformation)
        → STOP processing (no handoff)
    IF LLM returns "suspicious":
        → Apply SUSPICIOUS_CONFIDENCE_PENALTY to effectiveConfidence
        → Emit audit record (decision=summarised, llm_classification=suspicious)
        → Proceed to Stage 5
    IF LLM returns "credible":
        → Emit audit record (decision=summarised, llm_classification=credible)
        → Proceed to Stage 5
    IF LLM times out OR returns unexpected response:
        → Emit audit record (decision=held_for_review, llm_classification=llm_timeout)
        → STOP processing (fail-safe-CLOSED per life-safety-first)
    IF LLM is unavailable:
        → Emit audit record (decision=held_for_review, llm_classification=llm_unavailable)
        → STOP processing
```

### Stage 5: Signal Summarisation

**Input**: Signal (passed misinformation check if applicable)  
**Output**: Structured summary

```
IF LLM is available:
    → Generate LLM summary via _generate_with_fallback()
    → Validate output through ContentSafetyValidator
    → IF content safety fails: use structured fallback summary
ELSE (LLM degraded):
    → Use rule-based summary: {category, sourceKind, incidentId}
    → Set reduced confidence annotation

Emit audit record (decision=summarised)
```

### Stage 6: Confidence-Based Triage

**Input**: Summarised signal  
**Output**: Escalation decision

```
Compute effectiveConfidence = confidenceScore × freshnessScore
IF "suspicious" penalty applied: effectiveConfidence -= SUSPICIOUS_CONFIDENCE_PENALTY

IF ALL conditions met:
    (a) category IN {fire, weather, hydrology, earthquake, tsunami}
    (b) effectiveConfidence >= ESCALATION_CONFIDENCE_THRESHOLD
    (c) incidentId IS NOT NULL
THEN:
    → Create AgentHandoffEvent via build_handoff()
    → Deliver via deliver_handoff_with_retry()
    → Emit audit record (decision=escalated, then decision=handed_off on delivery)
    → Emit metrics: escalation_rate, handoff_success_rate
ELSE:
    → Signal stored for potential retrospective association
    → No handoff created
```

---

## Latency Budget (5-second SLA for high-risk escalation)

| Stage | Max Latency | Notes |
|-------|------------|-------|
| 1. Input Validation | 5 ms | Pydantic v2 validation |
| 2. Deduplication | 1 ms | In-memory set lookup |
| 3. Freshness Assessment | 1 ms | In-memory indicator update |
| 4. Misinformation Eval | 3,000 ms | LLM timeout; skipped for non-escalated |
| 5. Summarisation | 500 ms | Rule-based if LLM unavailable |
| 6. Triage + Handoff | 500 ms | Computation + handoff creation |
| **Total (escalated)** | **≤ 4,007 ms** | Within 5-second SLA |
| **Total (non-escalated)** | **≤ 1,007 ms** | No LLM misinformation check |

---

## Error Handling Contract

| Error Condition | Behaviour | Audit Decision |
|-----------------|-----------|----------------|
| Invalid SignalEnvelope | Reject, do not process | `validation_failed` |
| Duplicate signal_id | Discard silently | `discarded` |
| LLM unavailable | Hold escalated for review; rule-based for others | `held_for_review` |
| LLM timeout (> 3s) | Hold escalated for review (fail-safe-closed) | `held_for_review` |
| LLM unexpected response | Hold for review (fail-safe-closed) | `held_for_review` |
| Content safety failure | Replace with structured fallback | `summarised` (with safety annotation) |
| Handoff delivery failure | Retry 3× with exponential backoff, then dead-letter | `handed_off` → update status |
| Cosmos DB unavailable | Buffer in-memory → file spill → flush on recovery | Record carries `buffered_at` |
| Retrospective association DB error | Return 0 associations, log error | No audit record (operation failed) |

# ADR-F07: Keyword Fallback with Review Flag

## Status

Accepted

## Context

Compliance audit finding F07 identified that the content safety validator used
a simple keyword blocklist without integration to Azure AI Content Safety. The
keyword approach has two deficiencies:

1. **False negatives**: Harmful content that doesn't contain exact blocklist
   words passes validation.
2. **False positives**: Disaster-context words (e.g., "kill", "bomb cyclone")
   were previously blocked, causing legitimate alerts to fail.

Azure AI Content Safety provides ML-based classification across four categories
(hate, self-harm, sexual, violence) with severity scoring, but it introduces an
external dependency that may fail (network issues, throttling, outages).

## Decision

We implement a 3-layer content safety pipeline:

1. **Layer 1 — Azure AI Content Safety** (primary): ML-based classification via
   the `azure-ai-contentsafety` SDK with a dedicated `ContentSafetyCircuitBreaker`
   (trip=3, cooldown=60s). When the circuit is open, Layer 1 is bypassed.

2. **Layer 2 — Factual consistency**: Validates that alert text references the
   correct hazard type, severity level, and location from the originating signal.

3. **Layer 3 — Tone alignment**: Validates that alert language matches the
   assigned Australian Warning System tier (Advice / Watch and Act /
   Emergency Warning). Prevents calm-tier alerts from containing emergency
   escalation language.

When the Azure AI circuit breaker is open, **keyword fallback** is used with
`review_flag=True` on all results. This signals downstream consumers that a
human should review the alert before final publication.

## Consequences

### Positive

- Azure AI Content Safety provides ML-based detection of harmful content
  (finding F07 resolved).
- Circuit breaker prevents cascade failures when Azure AI is unavailable.
- `review_flag=True` on fallback results ensures no unvalidated content
  reaches the public without human review.
- Factual consistency prevents hallucinated alert content.
- Tone alignment enforces Australian Warning System compliance.

### Negative

- Azure AI Content Safety adds ~200ms latency per validation call.
- When circuit is open, keyword-only validation has lower detection accuracy.
- `review_flag` adds operational overhead — operators must review flagged
  alerts.

### Metrics

- `content_safety_circuit_opened`: Circuit breaker trip count.
- `content_safety_fallback_summary`: Count of messages validated via
  keyword fallback during each open circuit window.
- `content_safety_probe_attempted`: Half-open probe events.

## Alternatives Considered

1. **Azure AI only, no fallback**: Rejected — service outage would block all
   alert publication.
2. **Keyword only (status quo)**: Rejected — does not meet compliance finding.
3. **Local ML model**: Rejected — adds deployment complexity and model
   maintenance burden without clear benefit over Azure AI.

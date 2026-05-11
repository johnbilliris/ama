# Contract: Audit Envelope Schema (Typed Audit Entries)

**Feature**: 036 — Real Sub-Agent Invocation & Telemetry-Injection Agent
**Spec FRs**: FR-005, FR-038, FR-048, FR-049, FR-060
**Constitution**: IV (Transparency and Auditability)
**Container**: `simulation_audit_entries` (Cosmos, append-only, gap-free per-sim sequence number)

This contract enumerates **every typed audit entry** produced by feature 036 (including those inherited from spec 024 that are extended here) and pins the schema for each. The `simulation_audit_entries` container is **append-only**: a custom Cosmos role denies `replace` and `delete` for the API Managed Identity. Change-feed → Blob immutable archive (existing spec-024 pattern).

---

## 1. Common Audit Envelope

Every audit entry is a Cosmos document conforming to:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://platform/schemas/audit-envelope.schema.json",
  "type": "object",
  "required": ["id", "_partitionKey", "simulation_id", "sequence_number", "entry_type", "timestamp", "source", "details"],
  "additionalProperties": false,
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "_partitionKey": { "type": "string", "description": "= simulation_id" },
    "simulation_id": { "type": "string", "format": "uuid" },
    "sequence_number": { "type": "integer", "minimum": 1, "description": "Monotonic per simulation_id; gap-free per FR-048" },
    "entry_type": {
      "type": "string",
      "description": "Discriminator. See §3 for the complete enumeration.",
      "enum": [
        "injection.attempted",
        "injection.success",
        "injection.refused",
        "injection.circuit_open",
        "routing.viewport_hint_mismatch",
        "routing.jurisdiction_ambiguous",
        "routing.ambiguous",
        "cascade.degraded_to_annotation",
        "cascade.depth2_refused",
        "thread.cap_exceeded",
        "lifecycle.paused",
        "lifecycle.aborted",
        "lifecycle.resumed",
        "lifecycle.refused_while_paused",
        "audit.watermark.locale_missing",
        "audit.watermark.applied",
        "audit.sequence.uncertainty",
        "audit.idempotency.replay_cross_user",
        "audit.rbac.unauthorized_attempt",
        "synthetic-delivery",
        "sub_agent.timeout",
        "sub_agent.cancel",
        "sub_agent.degraded",
        "tenant_isolation.violation",
        "signal_pipeline.dispatch_failed"
      ]
    },
    "timestamp": { "type": "string", "format": "date-time" },
    "source": {
      "type": "object",
      "required": ["component"],
      "properties": {
        "component": { "type": "string", "description": "e.g. 'controller_service', 'simulation_telemetry_injection', 'cascade_orchestrator'" },
        "user_id": { "type": "string", "description": "Entra OID — populated when caller is a coordinator action" },
        "trace_id": { "type": "string", "description": "OpenTelemetry trace_id" }
      }
    },
    "correlation_id": { "type": "string", "format": "uuid", "description": "Links this entry to a sub-agent invocation, signal, or chat turn" },
    "turn_id": { "type": "string", "format": "uuid", "description": "FR-008 single audit envelope: groups inject + dispatch + replies under one turn" },
    "details": { "type": "object", "description": "Per-type payload. See §3." }
  }
}
```

**Gap-free guarantee** (FR-048): for any `simulation_id`, the `sequence_number` series is dense from 1..N. Detection: a periodic Azure Function reads `MAX(sequence_number)` and `COUNT(*)` per simulation; mismatch fires SEV-2 alert. Reconstruction: change-feed → Blob WORM archive ensures no entry can be lost in transit.

---

## 2. Sequence Number Generation

```python
async def write_audit_entry(sim_id: UUID, entry: AuditEntry) -> None:
    for attempt in range(5):
        max_doc, etag = await audit_repo.read_max_seq_with_etag(sim_id)
        proposed = (max_doc.last_sequence + 1)
        try:
            entry.sequence_number = proposed
            await audit_repo.create(entry)
            await audit_repo.replace_max_seq(sim_id, last_sequence=proposed, etag=etag)
            return
        except CosmosAccessConditionFailedError:
            await asyncio.sleep(0.05 * (2 ** attempt))
    raise AuditWriteContention(sim_id)
```

A `simulation_audit_max_seq/{sim_id}` document holds the latest sequence number under ETag concurrency.

---

## 3. Typed Audit Entries

For each `entry_type`, the `details` block conforms to the schema below.

### 3.1 `injection.attempted`

Written on **every** parse attempt (success or refused). Drives FR-009 circuit-breaker accounting; does NOT count toward the 30/min success budget.

```json
{
  "type": "object",
  "required": ["chat_turn_id", "user_id", "original_text_hash", "parse_started_at", "prompt_hash", "prompt_hash_source"],
  "properties": {
    "chat_turn_id": { "type": "string", "format": "uuid" },
    "user_id": { "type": "string" },
    "original_text_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "parse_started_at": { "type": "string", "format": "date-time" },
    "viewport_centroid_lat": { "type": ["number", "null"] },
    "viewport_centroid_lng": { "type": ["number", "null"] },
    "prompt_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$", "description": "FR-065 / Step 8 Amendment R — present on every attempt (accepted, refused, OR fallback)" },
    "prompt_hash_source": { "type": "string", "enum": ["raw_user_input", "canonical_llm_prompt", "system_only"], "description": "FR-065 / pass 1 Q5 — disambiguates the byte-source of prompt_hash" }
  }
}
```

### 3.2 `injection.success`

Written when one or more typed signals were written to `simulation_synthetic_signals`. Counts toward FR-009 30/min budget once per chat-turn (regardless of how many signals were derived).

```json
{
  "type": "object",
  "required": ["chat_turn_id", "injection_correlation_id", "signal_ids", "categories", "confidences", "prompt_hash", "prompt_hash_source", "triggered_sub_agents"],
  "properties": {
    "chat_turn_id": { "type": "string", "format": "uuid" },
    "injection_correlation_id": { "type": "string", "format": "uuid" },
    "signal_ids": { "type": "array", "items": { "type": "string", "format": "uuid" } },
    "categories": { "type": "array", "items": { "type": "string" } },
    "confidences": { "type": "array", "items": { "type": "string", "enum": ["high", "medium", "low"] } },
    "model_deployment": { "type": "string", "description": "e.g. 'gpt-4o-mini-australiaeast'" },
    "prompt_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$", "description": "FR-060 + FR-065 — telemetry-injection LLM prompt hash" },
    "prompt_hash_source": { "type": "string", "enum": ["raw_user_input", "canonical_llm_prompt", "system_only"], "description": "FR-065 / pass 1 Q5 — typically 'canonical_llm_prompt' on success" },
    "triggered_sub_agents": {
      "type": "array",
      "description": "FR-009 + FR-015 (Step 8 Amendment C) + pass 1 Q1 + FR-069 (Cycle 2 Amendment A2-04) — populated by signal_pipeline_orchestrator with subscriber + controller_intent invocations sharing this injection_correlation_id. Per Cycle 2 pass-1 Q1 the array MUST be byte-equal (after RFC 8785 JCS canonicalisation) to the HTTP 202 response body's array; ordered lexicographically ascending by `sub_agent` PascalCase enum value (Cycle 2 pass-1 Q4).",
      "items": {
        "type": "object",
        "required": ["sub_agent", "trigger_source", "correlation_id", "dispatch_status"],
        "properties": {
          "sub_agent": { "type": "string", "enum": ["Comms", "Evac", "Health", "Intel", "Logistics", "Operations", "Planning", "Resource", "Risk"], "description": "Cycle 2 Amendment A2-07 / FR-070 — canonical 9-member PascalCase SubAgent Literal from packages/domain/src/domain/models/aiims_mapping.py:51-61. Supersedes the prior 7-name kebab-case enum." },
          "trigger_source": { "type": "string", "enum": ["subscriber", "controller_intent", "cascade", "lifecycle"], "description": "Per Cycle 1 pass 1 Q1 dedup — see data-model § 8.7. This is the `injection.success` 4-value enum (Cycle 1 invariant retained). The Cycle 2 narrower pair `{primary, cascade}` is **exclusive to** the new §3.25 `signal_pipeline.dispatch_failed` envelope (see line 637) per data-model.md §11.5; `primary` does NOT appear in `injection.success`." },
          "correlation_id": { "type": "string", "format": "uuid", "description": "Per Cycle 2 pass-1 Q4 — per-subscriber dispatch UUID generated by the orchestrator at fan-out time, ONE per subscriber edge, DIFFERENT from the parent injection_correlation_id. Reused as the correlation_id on any subsequent sub_agent.timeout / sub_agent.cancel / sub_agent.degraded envelope raised against the same fan-out edge." },
          "dispatch_status": { "type": "string", "enum": ["acknowledged", "failed", "timed_out"], "description": "Cycle 2 Amendment A2-04 / FR-069 + pass-2 Q1 — three-value transport-layer outcome. acknowledged: subscriber acked within DISPATCH_ACK_TIMEOUT_SECONDS = 5.0 s; failed: orchestrator raised before/at publish (rate-limit and circuit-open subsumed here, with exception_class on the signal_pipeline.dispatch_failed envelope carrying granularity); timed_out: no ack within 5 s." }
        }
      }
    },
    "idempotency_key": { "type": ["string", "null"], "description": "FR-066 / pass 2 Q7 — present when the request carried Idempotency-Key" },
    "request_correlation_id": { "type": "string", "format": "uuid", "description": "FR-066 / pass 2 Q7 cross-replay traceability" }
  }
}
```

### 3.3 `injection.refused`

```json
{
  "type": "object",
  "required": ["chat_turn_id", "reason", "prompt_hash", "prompt_hash_source"],
  "properties": {
    "chat_turn_id": { "type": "string", "format": "uuid" },
    "reason": {
      "type": "string",
      "enum": [
        "missing_provenance",
        "life_safety_low_confidence",
        "unknown_category",
        "malformed_input",
        "pii_detected",
        "real_world_action_request"
      ]
    },
    "original_text_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "parsed_category": { "type": "string" },
    "inferred_confidence": { "type": "string", "enum": ["high", "medium", "low"] },
    "clarification_question": { "type": "string", "description": "Surfaced to coordinator UI" },
    "prompt_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$", "description": "FR-065 — REQUIRED on refusal paths per Amendment R" },
    "prompt_hash_source": { "type": "string", "enum": ["raw_user_input", "canonical_llm_prompt", "system_only"], "description": "FR-065 / pass 1 Q5 — typically 'raw_user_input' on pre-LLM refusals (RBAC, malformed, missing-provenance, idempotency conflict) and 'canonical_llm_prompt' on post-LLM refusals (life_safety_low_confidence, unknown_category, pii_detected)" }
  }
}
```

### 3.4 `injection.circuit_open`

```json
{
  "type": "object",
  "required": ["user_id", "attempts_in_window", "threshold", "window_seconds"],
  "properties": {
    "user_id": { "type": "string" },
    "attempts_in_window": { "type": "integer" },
    "threshold": { "type": "integer", "default": 60 },
    "window_seconds": { "type": "integer", "default": 60 },
    "enforcement_layer": { "type": "string", "enum": ["apim", "in_process"] },
    "cooldown_seconds": { "type": "integer", "default": 60 }
  }
}
```

### 3.5 `routing.viewport_hint_mismatch`

```json
{
  "type": "object",
  "required": ["chat_turn_id", "client_hint", "server_computed", "viewport_centroid_lat", "viewport_centroid_lng"],
  "properties": {
    "chat_turn_id": { "type": "string", "format": "uuid" },
    "client_hint": { "type": "string", "description": "Client-supplied jurisdiction hint" },
    "server_computed": { "type": "string", "description": "Server-revalidated jurisdiction (wins per FR-021 step 3)" },
    "viewport_centroid_lat": { "type": "number" },
    "viewport_centroid_lng": { "type": "number" },
    "jurisdiction_dataset_version": { "type": "string", "description": "e.g. 'platform-registry-v3' or 'abs-sa4-2026-fallback'" }
  }
}
```

### 3.6 `routing.jurisdiction_ambiguous`

```json
{
  "type": "object",
  "required": ["chat_turn_id", "inference_step_attempted", "candidates"],
  "properties": {
    "chat_turn_id": { "type": "string", "format": "uuid" },
    "inference_step_attempted": { "type": "integer", "minimum": 1, "maximum": 5 },
    "candidates": { "type": "array", "items": { "type": "string" } },
    "clarification_question": { "type": "string" }
  }
}
```

### 3.7 `routing.ambiguous`

```json
{
  "type": "object",
  "required": ["chat_turn_id", "candidate_agents"],
  "properties": {
    "chat_turn_id": { "type": "string", "format": "uuid" },
    "candidate_agents": { "type": "array", "items": { "type": "string" } },
    "confidences": { "type": "array", "items": { "type": "number", "minimum": 0, "maximum": 1 } },
    "clarification_question": { "type": "string" }
  }
}
```

### 3.8 `cascade.degraded_to_annotation`

FR-057 cascade absorbed into existing thread.

```json
{
  "type": "object",
  "required": ["origin_cascade_id", "triggering_thread_id", "target_thread_id", "affinity_step", "suppressed_proposal"],
  "properties": {
    "origin_cascade_id": { "type": "string", "format": "uuid" },
    "triggering_thread_id": { "type": "string", "format": "uuid" },
    "target_thread_id": { "type": "string", "format": "uuid" },
    "affinity_step": { "type": "integer", "minimum": 1, "maximum": 5 },
    "suppressed_proposal": { "type": "object", "description": "The would-be-new-thread that was absorbed" }
  }
}
```

### 3.9 `cascade.depth2_refused`

FR-057 cascade-depth ceiling: a depth-1 cascade child produced a synthetic signal that would have triggered a depth-2 cascade. The depth-2 fan-out is **refused** and a brand-new top-level injection-correlation-id is issued in lieu so that `origin_cascade_id` does **not** propagate transitively beyond depth 1. The would-be depth-2 trigger is recorded here for audit reconstruction.

```json
{
  "type": "object",
  "required": [
    "audit_id",
    "simulation_id",
    "sequence_number",
    "tenant_id",
    "timestamp_utc",
    "actor",
    "entry_type",
    "attempted_signal_id",
    "originating_cascade_id",
    "refusal_reason",
    "chat_reply_text",
    "new_top_level_correlation_id"
  ],
  "additionalProperties": false,
  "properties": {
    "audit_id": { "type": "string", "format": "uuid" },
    "simulation_id": { "type": "string", "format": "uuid" },
    "sequence_number": { "type": "integer", "minimum": 1 },
    "tenant_id": { "type": "string" },
    "timestamp_utc": { "type": "string", "format": "date-time" },
    "actor": { "type": "string", "description": "Component or coordinator identity that produced the depth-2 trigger" },
    "entry_type": { "type": "string", "const": "cascade.depth2_refused" },
    "attempted_signal_id": { "type": "string", "format": "uuid", "description": "The synthetic signal that would have triggered depth-2" },
    "originating_cascade_id": { "type": "string", "format": "uuid", "description": "The depth-1 cascade that produced the trigger" },
    "refusal_reason": { "type": "string", "const": "depth2_cascade_disallowed" },
    "chat_reply_text": { "type": "string", "maxLength": 500, "description": "Coordinator-visible message explaining the refusal" },
    "new_top_level_correlation_id": { "type": "string", "format": "uuid", "description": "Fresh top-level injection correlation ID issued in lieu of cascading; origin_cascade_id is NOT propagated" }
  }
}
```

### 3.10 `thread.cap_exceeded`

```json
{
  "type": "object",
  "required": ["proposed_thread", "current_thread_count", "rejection_source"],
  "properties": {
    "proposed_thread": { "type": "object", "description": "Hazard thread proposal that was refused" },
    "current_thread_count": { "type": "integer", "const": 5 },
    "rejection_source": { "type": "string", "enum": ["coordinator_injection", "scenario_setup"] }
  }
}
```

### 3.11 `lifecycle.paused`

The lifecycle audit entry that records the simulation transition into the `paused` state. (NB: refusals of attempted-actions while in the paused state are recorded under the NEW typed entry `lifecycle.refused_while_paused` — see § 3.13a below — per Step 8 amendment pass 2 Q7.)

```json
{
  "type": "object",
  "required": ["coordinator_user_id", "idempotency_key", "request_correlation_id"],
  "properties": {
    "coordinator_user_id": { "type": "string" },
    "idempotency_key": { "type": ["string", "null"], "description": "Per FR-066 / pass 2 Q7 — present when the request carried Idempotency-Key; null when absent" },
    "request_correlation_id": { "type": "string", "format": "uuid", "description": "Per FR-066 / pass 2 Q7 cross-replay traceability" }
  }
}
```

### 3.12 `lifecycle.aborted`

Abort REST endpoint invoked.

```json
{
  "type": "object",
  "required": ["coordinator_user_id", "cancelled_invocations", "abort_timestamp", "idempotency_key", "request_correlation_id"],
  "properties": {
    "coordinator_user_id": { "type": "string" },
    "cancelled_invocations": { "type": "integer", "minimum": 0 },
    "abort_timestamp": { "type": "string", "format": "date-time" },
    "reason": { "type": "string", "maxLength": 500 },
    "idempotency_key": { "type": ["string", "null"], "description": "Per FR-066 / pass 2 Q7" },
    "request_correlation_id": { "type": "string", "format": "uuid", "description": "Per FR-066 / pass 2 Q7" }
  }
}
```

### 3.13 `lifecycle.resumed`

```json
{
  "type": "object",
  "required": ["coordinator_user_id", "previous_paused_duration_seconds", "idempotency_key", "request_correlation_id"],
  "properties": {
    "coordinator_user_id": { "type": "string" },
    "previous_paused_duration_seconds": { "type": "integer" },
    "idempotency_key": { "type": ["string", "null"], "description": "Per FR-066 / pass 2 Q7" },
    "request_correlation_id": { "type": "string", "format": "uuid", "description": "Per FR-066 / pass 2 Q7" }
  }
}
```

### 3.13a `lifecycle.refused_while_paused` *(NEW — Step 8 Amendment F / pass 2 Q7)*

Recorded when a write request (chat turn, telemetry injection, sub-agent invocation) arrives while the simulation is in `paused` state and is refused with HTTP 409. Per pass 2 Q7, the 409 refusal itself is **NOT cached** in the FR-066 idempotency cache so that a fresh request body is serviced cleanly on resume rather than serving a cached refusal.

```json
{
  "type": "object",
  "required": ["attempted_action", "coordinator_user_id", "idempotency_key", "request_correlation_id"],
  "properties": {
    "attempted_action": { "type": "string", "enum": ["chat_turn", "sub_agent_invocation", "telemetry_injection"] },
    "coordinator_user_id": { "type": "string" },
    "idempotency_key": { "type": ["string", "null"], "description": "Per FR-066 / pass 2 Q7 — present on the refused request even though the refusal is not itself cached" },
    "request_correlation_id": { "type": "string", "format": "uuid" },
    "refusal_response_status": { "type": "integer", "const": 409 }
  }
}
```

### 3.14 `audit.watermark.locale_missing`

Translation table miss (text variant) OR audio-prefix table miss (audio variant). The same `entry_type` covers both with the `pathway` discriminator.

```json
{
  "type": "object",
  "required": ["artefact_id", "locale", "pathway"],
  "properties": {
    "artefact_id": { "type": "string", "description": "Warning ID, PDF ID, audio MP3 ID" },
    "locale": { "type": "string", "description": "BCP-47 locale tag (e.g. 'vi-VN', 'zh-Hans-CN')" },
    "pathway": { "type": "string", "enum": ["text", "audio"] },
    "fallback_applied": { "type": "string", "enum": ["english_only_text", "english_only_spoken_prefix"] }
  }
}
```

### 3.14a `audit.watermark.applied` *(NEW — Step 8 Amendment Q / pass 2 Q6)*

Recorded when the FR-039 / FR-058 / FR-064 watermark is applied to a deliverable artefact. Captures the `delivery_channel` discriminator that links FR-058 audio-prefix renderings to FR-064 accessible live-log emissions; both pathways consume the SAME `packages/domain/src/domain/sim_locale_table.json` (per pass 2 Q6 shared-source-of-truth).

```json
{
  "type": "object",
  "required": ["artefact_id", "delivery_channel", "resolved_locale", "watermark_text_hash"],
  "properties": {
    "artefact_id": { "type": "string", "description": "Warning ID, MP3 ID, or live-log SSE event id" },
    "delivery_channel": {
      "type": "string",
      "enum": ["audio", "text-live-log", "both"],
      "description": "Per pass 2 Q6 — distinguishes FR-058 audio prefix from FR-064 accessible live-log; 'both' indicates a public-warning artefact with text + audio renderings"
    },
    "resolved_locale": { "type": "string", "description": "BCP-47 tag returned by the 3-step fallback `request_locale → jurisdiction_priority_locale → en_AU`" },
    "watermark_text_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$", "description": "sha256 over the rendered bilingual watermark string (text) or the concatenated MP3 file (audio); used by SC-006 byte-match regression tests" },
    "audio_prefix_table_version": { "type": ["string", "null"], "description": "Present when delivery_channel ∈ {audio, both}" },
    "live_log_sse_event_id": { "type": ["string", "null"], "description": "Present when delivery_channel ∈ {text-live-log, both}" }
  }
}
```

### 3.14b `audit.sequence.uncertainty` *(NEW — Step 8 Amendment D / pass 1 Q2)*

Best-effort entry written to the **fail-safe dead-letter queue** (Cosmos `simulation_audit_dlq` container; see data-model § 8.5) when the FR-048 distributed sequence allocator (ADR-036-007) cannot allocate a gap-free `sequence_number` within its 5-attempt retry budget. Carries `sequence_number = -1` as a sentinel so downstream readers can detect evidence-integrity warnings.

```json
{
  "type": "object",
  "required": ["original_correlation_id", "uncertainty_reason", "sequence_number", "fallback_audit_envelope", "queued_at"],
  "properties": {
    "original_correlation_id": { "type": "string", "format": "uuid", "description": "Correlation id of the originating request that failed sequence allocation" },
    "uncertainty_reason": { "type": "string", "enum": ["etag_exhausted", "counter_unreachable", "replica_partition"] },
    "sequence_number": { "type": "integer", "const": -1 },
    "fallback_audit_envelope": { "type": "object", "description": "Best-effort copy of the audit entry that would have been written; preserves the request payload for post-hoc reconstruction" },
    "queued_at": { "type": "string", "format": "date-time" },
    "idempotency_key": { "type": ["string", "null"], "description": "FR-066 / pass 1 Q2 — recorded for cross-replay traceability" }
  }
}
```

### 3.14c `audit.idempotency.replay_cross_user` *(NEW — ADR-036-009 § 6)*

SEV-2 audit-only event written when an FR-066 cache hit replay arrives with a different `rbac_subject_id` than the originally-cached entry. The replay PROCEEDS (the original side effect already committed) but the cross-user attempt is recorded for forensic review.

```json
{
  "type": "object",
  "required": ["cache_doc_id", "cached_rbac_subject_id", "replay_rbac_subject_id"],
  "properties": {
    "cache_doc_id": { "type": "string", "description": "= `{sim_id}/{verb}/{route}/{idempotency_key}`" },
    "cached_rbac_subject_id": { "type": "string", "description": "Entra OID of the original requester" },
    "replay_rbac_subject_id": { "type": "string", "description": "Entra OID of the replay requester" },
    "verb": { "type": "string" },
    "route": { "type": "string" }
  }
}
```

### 3.14d `audit.rbac.unauthorized_attempt` *(NEW — analyse pass 1 D-03 / FR-051)*

Emitted when an authenticated user attempts an action their role does not authorise. Per FR-051 (Amendment E STRENGTHEN), every coordinator-only route MUST validate JWT/app-role + tenant membership BEFORE any audit attempt, and anonymous fallbacks are PROHIBITED in production. This typed entry captures the deny decision so refusals are forensically reconstructable. Per spec.md § 1369, the cached idempotency response MUST NOT be served when this entry is written — the deny decision is authoritative even on replay.

**Fields summary** (per analyse pass 1 D-03 prescribed schema):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subject.user_id | string | yes | OID claim of authenticated principal |
| subject.tenant_id | string | yes | Tenant of the authenticated principal |
| route | string | yes | Path of the denied request, e.g. `/api/simulations/{sim_id}/inject_telemetry` |
| requested_role | string | yes | Role required to perform the action (`coordinator`, `observer`, `admin`) |
| actual_roles | string[] | yes | Roles the principal actually held |
| reason | string | yes | One of `missing_role`, `tenant_mismatch`, `expired_token`, `invalid_signature` |
| sim_id | string | no | Simulation ID if route was simulation-scoped |
| request_correlation_id | string | yes | Correlation ID propagated from request header |
| prompt_hash | string | no | Pre-LLM refusal path; populated when request body contained user prompt |
| prompt_hash_source | enum | no | One of `raw_user_input \| canonical_llm_prompt \| system_only`; required if `prompt_hash` present |

```json
{
  "type": "object",
  "required": ["subject", "route", "requested_role", "actual_roles", "reason", "request_correlation_id"],
  "properties": {
    "subject": {
      "type": "object",
      "required": ["user_id", "tenant_id"],
      "properties": {
        "user_id": { "type": "string", "description": "OID claim of authenticated principal" },
        "tenant_id": { "type": "string", "description": "Tenant of the authenticated principal" }
      }
    },
    "route": { "type": "string", "description": "Path of the denied request, e.g. `/api/simulations/{sim_id}/inject_telemetry`" },
    "requested_role": { "type": "string", "enum": ["coordinator", "observer", "admin"], "description": "Role required to perform the action" },
    "actual_roles": { "type": "array", "items": { "type": "string" }, "description": "Roles the principal actually held" },
    "reason": { "type": "string", "enum": ["missing_role", "tenant_mismatch", "expired_token", "invalid_signature"] },
    "sim_id": { "type": ["string", "null"], "format": "uuid", "description": "Simulation ID if route was simulation-scoped" },
    "request_correlation_id": { "type": "string", "format": "uuid", "description": "Correlation ID propagated from request header" },
    "prompt_hash": { "type": ["string", "null"], "pattern": "^[a-f0-9]{64}$", "description": "Pre-LLM refusal path; populated when request body contained user prompt" },
    "prompt_hash_source": { "type": ["string", "null"], "enum": ["raw_user_input", "canonical_llm_prompt", "system_only", null], "description": "Required if `prompt_hash` present" }
  }
}
```

### 3.15 `synthetic-delivery`

Every blocked outbound communication (FR-038).

```json
{
  "type": "object",
  "required": ["channel", "audience", "message_id", "sim_timestamp", "block_reason", "payload_hash", "watermark_applied"],
  "properties": {
    "channel": { "type": "string" },
    "audience": { "type": "string" },
    "message_id": { "type": "string", "pattern": "^sim-msg-[a-f0-9]{4,}$" },
    "sim_timestamp": { "type": "string", "format": "date-time" },
    "block_reason": { "type": "string", "enum": ["simulation_tenant_egress_blocked", "publication_service_refusal", "http_wrapper_refusal"] },
    "payload_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "watermark_applied": { "const": true },
    "aws_tier": { "type": "string", "enum": ["advice", "watch_and_act", "emergency_warning"] },
    "rendered_chat_text": { "type": "string", "description": "Always begins '[SIMULATION] '" }
  }
}
```

### 3.16 `sub_agent.timeout`

Hard timeout per FR-006 (default 120 s).

```json
{
  "type": "object",
  "required": ["correlation_id", "sub_agent", "timeout_seconds"],
  "properties": {
    "correlation_id": { "type": "string", "format": "uuid" },
    "sub_agent": { "type": "string" },
    "timeout_seconds": { "type": "number" },
    "model_deployment": { "type": "string" },
    "soft_ack_emitted": { "type": "boolean", "description": "Whether the 'working on it' SSE delta was sent" }
  }
}
```

### 3.17 `sub_agent.cancel`

In-flight invocation cancelled (`abort` REST endpoint or `pause` clean-shutdown).

```json
{
  "type": "object",
  "required": ["correlation_id", "sub_agent", "cancellation_reason"],
  "properties": {
    "correlation_id": { "type": "string", "format": "uuid" },
    "sub_agent": { "type": "string" },
    "cancellation_reason": { "type": "string", "enum": ["aborted", "paused_clean_shutdown"] },
    "elapsed_ms": { "type": "number" }
  }
}
```

### 3.18 `sub_agent.degraded`

Fall-back path triggered (e.g. Azure OpenAI 429 exhausted retries → `degraded` reply tag).

```json
{
  "type": "object",
  "required": ["correlation_id", "sub_agent", "degradation_reason"],
  "properties": {
    "correlation_id": { "type": "string", "format": "uuid" },
    "sub_agent": { "type": "string" },
    "degradation_reason": { "type": "string", "enum": ["rate_limit_exhausted", "llm_unavailable", "cached_state_used", "network_partition"] },
    "fallback_path": { "type": "string" }
  }
}
```

### 3.19 `tenant_isolation.violation`

FR-007 / FR-016 / FR-050 — citation or signal write resolved to a non-sim-tenant resource.

```json
{
  "type": "object",
  "required": ["violation_kind", "offending_resource_id"],
  "properties": {
    "violation_kind": { "type": "string", "enum": ["citation_to_live_tenant", "signal_write_outside_partition", "subscription_to_live_signal"] },
    "offending_resource_id": { "type": "string" },
    "sub_agent": { "type": "string" },
    "rejection_path": { "type": "string", "enum": ["opa_policy", "application_layer", "rbac"] }
  }
}
```

### 3.25 `signal_pipeline.dispatch_failed` *(NEW — Cycle 2 Amendment A2-01 / A2-08 / FR-067)*

Written whenever `SignalPipelineOrchestrator.dispatch()` raises mid-fan-out (per `apps/api/app/api/routes/simulations_036.py:316-345` site flagged by Cycle 2 A2-01). The HTTP 202 response is still returned (signal write was durable) but with `degraded_dispatch=true` on the response body (per Cycle 2 pass-2 Q2 always-present invariant), the partial-successful subset populated in `triggered_sub_agents`, and this typed audit entry recording the orchestrator failure for forensic reconstruction. Per Cycle 2 pass-1 Q1, the audit envelope's `triggered_sub_agents` array MUST be byte-equal (after RFC 8785 JCS canonicalisation) to the HTTP 202 response body's array — `partial_successful_subset[]` and `failed_subscriber_list[]` are retained as derivable views for forensic-export ergonomics.

```json
{
  "type": "object",
  "required": [
    "injection_correlation_id",
    "exception_class",
    "triggered_sub_agents",
    "partial_successful_subset",
    "failed_subscriber_list",
    "prompt_hash",
    "prompt_hash_source",
    "degraded_dispatch_flag"
  ],
  "additionalProperties": false,
  "properties": {
    "injection_correlation_id": { "type": "string", "format": "uuid", "description": "Parent correlation id for the inject-telemetry request; equals the top-level envelope.correlation_id (Cycle 2 pass-2 Q3)." },
    "exception_class": { "type": "string", "description": "Fully-qualified Python exception class raised by the orchestrator (e.g. `azure.eventhub.exceptions.EventHubError`, `RateLimitError`, `CircuitOpenError`). Per Cycle 2 pass-2 Q1 carries the granularity that the 3-value dispatch_status enum subsumes." },
    "exception_message": { "type": "string", "maxLength": 1000, "description": "Sanitised exception message; PII-scrubbed before write." },
    "triggered_sub_agents": {
      "type": "array",
      "description": "Cycle 2 pass-1 Q1 — byte-equal (after RFC 8785 JCS canonicalisation) to the HTTP 202 response body's `triggered_sub_agents` array. Ordered lexicographically by `sub_agent` PascalCase enum value (Cycle 2 pass-1 Q4). Contains ONE entry per attempted subscriber.",
      "items": {
        "type": "object",
        "required": ["sub_agent", "trigger_source", "correlation_id", "dispatch_status"],
        "properties": {
          "sub_agent": { "type": "string", "enum": ["Comms", "Evac", "Health", "Intel", "Logistics", "Operations", "Planning", "Resource", "Risk"] },
          "trigger_source": { "type": "string", "enum": ["primary", "cascade"], "description": "Cycle 2 pass-1 Q4 — narrowed pair for Cycle 2 dispatch entries." },
          "correlation_id": { "type": "string", "format": "uuid", "description": "Per-subscriber dispatch UUID (Cycle 2 pass-1 Q4); DIFFERENT from injection_correlation_id." },
          "dispatch_status": { "type": "string", "enum": ["acknowledged", "failed", "timed_out"], "description": "Cycle 2 pass-2 Q1 — 5 s per-subscriber transport timeout (`DISPATCH_ACK_TIMEOUT_SECONDS`)." }
        }
      }
    },
    "partial_successful_subset": {
      "type": "array",
      "description": "Derivable view: subset of `triggered_sub_agents` with `dispatch_status == 'acknowledged'`. Retained for forensic-export ergonomics.",
      "items": { "type": "string", "enum": ["Comms", "Evac", "Health", "Intel", "Logistics", "Operations", "Planning", "Resource", "Risk"] }
    },
    "failed_subscriber_list": {
      "type": "array",
      "description": "Derivable view: subset of `triggered_sub_agents` with `dispatch_status` ∈ {'failed', 'timed_out'}. Retained for forensic-export ergonomics.",
      "items": { "type": "string", "enum": ["Comms", "Evac", "Health", "Intel", "Logistics", "Operations", "Planning", "Resource", "Risk"] }
    },
    "prompt_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$", "description": "FR-065 — present on every dispatch_failed entry; same source bytes as the paired injection.attempted/success entry." },
    "prompt_hash_source": { "type": "string", "enum": ["raw_user_input", "canonical_llm_prompt", "system_only"], "description": "FR-065 / pass 1 Q5 — typically 'canonical_llm_prompt' for orchestrator-failure paths reached after LLM classification." },
    "degraded_dispatch_flag": { "type": "boolean", "const": true, "description": "Cycle 2 pass-2 Q2 invariant: the HTTP 202 response body's `degraded_dispatch` field MUST equal `true` whenever this audit entry is written; the field is the single source-of-truth for whether the paired `signal_pipeline.dispatch_failed` envelope was written for this request." },
    "dispatch_ack_timeout_seconds": { "type": "number", "const": 5.0, "description": "Cycle 2 pass-2 Q1 — `DISPATCH_ACK_TIMEOUT_SECONDS: Final[float] = 5.0` defined in `signal_pipeline_orchestrator.py`. Captured for forensic-replay determinism." },
    "idempotency_key": { "type": ["string", "null"], "description": "FR-066 / pass 2 Q7 — present when the request carried Idempotency-Key; replay of the same key returns the cached degraded-dispatch response unchanged without re-attempting the dispatch." },
    "request_correlation_id": { "type": "string", "format": "uuid", "description": "FR-066 / pass 2 Q7 cross-replay traceability." }
  }
}
```

**Acceptance criteria** (per Cycle 2 A2-01):

- Integration test injects a `weather` signal while one subscribed sub-agent's stub raises; endpoint returns HTTP 202 with `degraded_dispatch=true` and `triggered_sub_agents` populated with the surviving subset.
- Audit subtree contains exactly one `signal_pipeline.dispatch_failed` entry with `partial_successful_subset[]`, `failed_subscriber_list[]`, `exception_class`, `prompt_hash`, and `prompt_hash_source`.
- On a fully-failed dispatch (zero acknowledged subscribers), the `injection.success` envelope is NOT emitted; only `signal_pipeline.dispatch_failed` is written, and the response body still carries `degraded_dispatch=true` with `triggered_sub_agents` populated with **one entry per attempted subscriber** (all `dispatch_status` ∈ `{"failed", "timed_out"}`), per the §3.25 schema and Cycle 2 Pass-1 Q1 byte-equality with the audit envelope's array.
- Replay of the same `Idempotency-Key` (per FR-066) returns the cached degraded-dispatch response unchanged without re-attempting the dispatch.

---

### 3.26 `staging_promotion.refused` *(NEW — Cycle 3 Amendment A3-01 / FR-071)*

Written by `tests/staging_gates.py::assert_sli_thresholds()` immediately
before each `StagingPromotionRefused` raise (per Cycle 3 Pass-1 Q3 — `spec.md:1016-1097`),
recording the gate-job refusal for forensic reconstruction. The eight `details`
fields are pinned by Pass-1 Q3 (`spec.md:1031-1039`); the `correlation_id`
parity invariant from Pass-1 Q4 / Pass-2 Q1 mandates the top-level
`correlation_id` field equal `details.staging_promotion_correlation_id`
(single-stream JOIN-by-`correlation_id`).

The §3.20–§3.24 envelope-section gap is **preserved** (Pass-2 Q1 explicit
decision — `spec.md:1328-1330`); back-filling would obscure temporal
ordering. Allocator (Cycle 1 ADR-036-007) remains the sole `sequence_number`
source — this schema MUST NOT carry a placeholder `sequence_number` literal
(Cycle 2 Amendment A2-06 precedent, see §6.2).

Two concurrent refused invocations produce two distinct envelopes with two
distinct `staging_promotion_correlation_id` values (Pass-1 Q3 — no coalescing).

```json
{
  "type": "object",
  "required": [
    "staging_promotion_correlation_id",
    "build_label",
    "triggering_workflow_run_id",
    "triggering_actor",
    "breached_slis",
    "sample_floor_underages",
    "refused_at",
    "gate_helper_version"
  ],
  "additionalProperties": false,
  "properties": {
    "entry_type": { "type": "string", "const": "staging_promotion.refused", "description": "Discriminator — equals the envelope's top-level `entry_type` field." },
    "staging_promotion_correlation_id": { "type": "string", "format": "uuid", "description": "Fresh UUID4 minted on every gate run that raises; equals the top-level `envelope.correlation_id` per Pass-1 Q4 single-stream JOIN invariant." },
    "build_label": { "type": "string", "description": "Build label of the candidate being gated (e.g. `v0.36.0-rc.1`); supplied by the workflow as a `BUILD_LABEL` env var or as a kwarg to `assert_sli_thresholds()`." },
    "triggering_workflow_run_id": { "type": "integer", "minimum": 1, "description": "GitHub Actions `${{ github.run_id }}` for the staging-promotion workflow run; sourced from `GITHUB_RUN_ID` env var." },
    "triggering_actor": { "type": "string", "description": "GitHub Actions `${{ github.actor }}` for the dispatcher; sourced from `GITHUB_ACTOR` env var." },
    "breached_slis": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Lex-sorted list of SLI ids whose threshold was breached (e.g. `[\"SLI-Z6\", \"SLI-Z7\"]`). Empty list when the refusal stems solely from sample-floor under-meets."
    },
    "sample_floor_underages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["sli_id", "observed_samples", "required_samples"],
        "additionalProperties": false,
        "properties": {
          "sli_id": { "type": "string" },
          "observed_samples": { "type": "integer", "minimum": 0 },
          "required_samples": { "type": "integer", "minimum": 1 }
        }
      },
      "description": "Per-SLI sample-floor under-meets where `observed_samples < required_samples` (per Cycle 2 Pass-2 Q4 / `MIN_SAMPLES_PER_SLI_24H`). Empty list when the refusal stems solely from threshold breaches."
    },
    "refused_at": { "type": "string", "format": "date-time", "description": "ISO-8601 timestamp at the moment of refusal (UTC, `datetime.now(timezone.utc).isoformat()`)." },
    "gate_helper_version": { "type": "string", "pattern": "^[a-f0-9]{64}$", "description": "SHA-256 of `tests/staging_gates.py` at run time — `hashlib.sha256(Path(__file__).read_bytes()).hexdigest()` — captured for forensic-replay determinism." }
  }
}
```

**Acceptance criteria** (per Cycle 3 Amendment A3-01 / FR-071):

- `assert_sli_thresholds()` writes exactly one `staging_promotion.refused` envelope before each `StagingPromotionRefused` raise (Pass-1 Q3 / `spec.md:1075-1081`).
- The envelope's top-level `correlation_id` field equals `details.staging_promotion_correlation_id` (Pass-1 Q4 single-stream JOIN invariant).
- Two concurrent refused invocations produce two distinct envelopes with two distinct UUID4 `staging_promotion_correlation_id` values — no coalescing.
- The envelope's `sequence_number` is allocator-assigned (ADR-036-007); `details` MUST NOT carry a placeholder `sequence_number` literal (A2-06 precedent).
- The `gate_helper_version` SHA-256 is recomputed per run from the live `tests/staging_gates.py` file — drift-detection is the explicit goal.

---

## 4. Contract Tests

Every `entry_type` has a contract test in `tests/contract/test_audit_schemas.py` asserting:

1. Required fields are present.
2. Field types match the schema.
3. Sequence number is monotonic and gap-free for the simulation under test.
4. Append-only RBAC denies `replace`/`delete` (negative test attempting both expects 403).

Per the QA cohort (concern 2): no `entry_type` is silently dropped — every typed audit write produces a Cosmos document and every refusal pathway asserts the corresponding entry was written.

---

## 5. Machine-export pathway (FR-049)

Audit entries are exported via the existing spec-024 audit-export endpoint, extended to:

- Filter by `simulation_id`, `entry_type` (any of the **26** typed entries above, including `cascade.depth2_refused`, `lifecycle.refused_while_paused`, `audit.watermark.applied`, `audit.sequence.uncertainty`, `audit.idempotency.replay_cross_user`, `audit.rbac.unauthorized_attempt`, `signal_pipeline.dispatch_failed`, and `staging_promotion.refused`), `time_range`.
- Return as NDJSON (one document per line), gzipped.
- Include the SHA-256 digest of the export bundle in a sibling `<bundle>.sha256` file.
- Access-controlled: `Simulation.Coordinator` or `Auditor` Entra app role only (Security cohort §3, Compliance cohort §4).
- DLQ entries (`sequence_number = -1`, `audit.sequence.uncertainty`) are reconciled into the main `simulation_audit_entries` container only after operator review per ADR-036-007 § 7; until reconciliation, exports flag them with `evidence_integrity_warning: true` so consumers cannot silently treat them as gap-free.

Foundry-carve-out audit hygiene: when `model_deployment` indicates a non-AU endpoint (e.g. `gpt-4o-eastus2-carve-out`), the audit-export filter MUST also flag the entry for review by the Compliance Auditor as part of the regular carve-out review cycle (Constitution v1.2.0 §Non-Negotiable #2 review-date enforcement).

---

## 6. Amendment-cycle additions (Step 8 + Cycle 2 audit-field changes)

The following audit-envelope changes are introduced by the Step 8 amendment cycle (Cycle 1) and the post-Step-8i amendment cycle (Cycle 2). They are **additive** — every existing field on entries §3.1 through §3.19 is preserved.

### 6.1 New typed entries (5 added in Cycle 1, 1 added in Cycle 2, 1 added in Cycle 3 — total 19 → 26)

| Entry | Source amendment | Cosmos container |
|-------|------------------|------------------|
| `lifecycle.refused_while_paused` | Cycle 1 Amendment F / pass 2 Q7 | `simulation_audit_entries` |
| `audit.watermark.applied` | Cycle 1 Amendment Q / pass 2 Q6 | `simulation_audit_entries` |
| `audit.sequence.uncertainty` | Cycle 1 Amendment D / pass 1 Q2 | `simulation_audit_dlq` (DLQ) |
| `audit.idempotency.replay_cross_user` | ADR-036-009 § 6 | `simulation_audit_entries` |
| `audit.rbac.unauthorized_attempt` | analyse pass 1 D-03 / FR-051 (Amendment E STRENGTHEN) | `simulation_audit_entries` |
| `signal_pipeline.dispatch_failed` *(NEW Cycle 2)* | Cycle 2 Amendment A2-01 / A2-08 / FR-067 | `simulation_audit_entries` |
| `staging_promotion.refused` *(NEW Cycle 3)* | Cycle 3 Amendment A3-01 / FR-071 | `simulation_audit_entries` |

### 6.2 Field additions to existing entries

| Entry(s) | New field | Type | Source |
|----------|-----------|------|--------|
| `injection.attempted`, `injection.success`, `injection.refused` | `prompt_hash_source` | enum `raw_user_input | canonical_llm_prompt | system_only` | Amendment R / pass 1 Q5 |
| `injection.attempted`, `injection.refused` | `prompt_hash` (now REQUIRED on all paths) | sha256 hex | Amendment R / pass 1 Q5 |
| `injection.success` | `triggered_sub_agents[].trigger_source` | enum `subscriber | controller_intent | cascade | lifecycle` | Cycle 1 Amendment C / pass 1 Q1 (Cycle 2 pass-1 Q4 narrows the `{primary, cascade}` pair to §3.25 `signal_pipeline.dispatch_failed` only — see line 637 — so `primary` does NOT appear in `injection.success`) |
| `injection.success` | `triggered_sub_agents[].dispatch_status` | enum `acknowledged | failed | timed_out` | **Cycle 2 Amendment A2-04 / FR-069 + pass-2 Q1** |
| `injection.success` | `triggered_sub_agents[].sub_agent` enum bumped 7 kebab-case → 9 PascalCase | enum `Comms | Evac | Health | Intel | Logistics | Operations | Planning | Resource | Risk` | **Cycle 2 Amendment A2-07 / FR-070** |
| `lifecycle.paused`, `lifecycle.aborted`, `lifecycle.resumed`, `lifecycle.refused_while_paused`, `injection.success` | `idempotency_key`, `request_correlation_id` | string | uuid | FR-066 / pass 2 Q7 |
| `audit.watermark.applied` (NEW) and `synthetic-delivery` callers | `delivery_channel` | enum `audio | text-live-log | both` | Amendment Q / pass 2 Q6 |
| `audit.sequence.uncertainty` (NEW) | `sequence_number = -1` sentinel | integer const | Amendment D / pass 1 Q2 |
| `cascade.depth2_refused` | placeholder `sequence_number = 1` literal **REMOVED** (writer's gap-free allocator is sole source of truth) | n/a | **Cycle 2 Amendment A2-06 / FR-048 STRENGTHEN** |

### 6.3 Cross-references

- **prompt_hash_source semantics** — see data-model § 8.6 for the `SyntheticSignal.prompt_hash_source` field definition; the audit envelope mirrors that enum exactly.
- **Idempotency-key handling on lifecycle** — see `contracts/idempotency-cache.md` § 4 (state-machine consumption) for the full rule: lifecycle `paused / aborted / resumed` SUCCESSES are cached for 24 h replay; `lifecycle.refused_while_paused` 409 refusals are NOT cached (per pass 2 Q7).
- **Sequence-uncertainty DLQ flow** — see ADR-036-007 § 4 + § 7 for the 5-attempt retry budget + operator-reconciliation workflow. Until reconciliation, the main audit stream remains gap-free for sequence numbers `1..N`; DLQ entries with `sequence_number = -1` carry a `fallback_audit_envelope` for forensic reconstruction.
- **AIIMS function tagging on sub-agent-side audit entries** — `sub_agent.timeout / cancel / degraded` entries are NOT amended in this cycle; AIIMS-function tagging is recorded on the `SubAgentInvocationRecord` (see data-model § 8.7) and is joined into audit-export NDJSON post-hoc rather than embedded in each audit envelope.
- **RBAC denial entry** — `audit.rbac.unauthorized_attempt` (§ 3.14d) added per analyse pass 1 D-03; FR-051 canonical name confirmed as `audit.rbac.unauthorized_attempt` (per spec.md § 1356 & § 1369). Per FR-051 (Amendment E STRENGTHEN), this entry MUST be written BEFORE any cached idempotency replay is served — the deny decision is authoritative on every request even when an `Idempotency-Key` matches a prior success.
- **(Cycle 2) `signal_pipeline.dispatch_failed` byte-equality invariant** — per Cycle 2 pass-1 Q1, the `triggered_sub_agents` array on this typed entry MUST be byte-equal (after RFC 8785 JCS canonicalisation) to the HTTP 202 response body's `triggered_sub_agents` array. Tested by `tests/integration/test_dispatch_failed_body_audit_byte_equality.py` (`json.dumps(body, sort_keys=True) == json.dumps(audit['details']['triggered_sub_agents'], sort_keys=True)`).
- **(Cycle 2) per-subscriber dispatch correlation_id semantics** — per Cycle 2 pass-1 Q4, each `triggered_sub_agents[].correlation_id` is a fresh UUID generated by the orchestrator at fan-out time, ONE per subscriber edge, and DIFFERENT from the parent `injection_correlation_id`. The per-subscriber id MUST be reused as the `correlation_id` on any subsequent `sub_agent.timeout` (§ 3.16), `sub_agent.cancel` (§ 3.17), or `sub_agent.degraded` (§ 3.18) envelope raised against the same fan-out edge. Single-stream JOIN by `correlation_id` reconstructs the per-subscriber timeline (no parent→child JOIN required).
- **(Cycle 2) hybrid OTel + customDimensions correlation propagation** — per Cycle 2 pass-2 Q3, the orchestrator opens a parent OTel span at `dispatch()` entry and sets `injection_correlation_id` as both a span attribute (`customDimensions["injection_correlation_id"]`) AND propagates it as the W3C TraceContext `trace_id`; each per-subscriber dispatch opens a CHILD span whose `span_id` is derived from the per-subscriber `correlation_id` AND sets `customDimensions["correlation_id"]` to the full UUID string. The `signal_pipeline.dispatch_failed` envelope's top-level `correlation_id` field equals the parent `injection_correlation_id`; each per-subscriber entry's `correlation_id` equals the corresponding child span's `customDimensions["correlation_id"]`.

---

*Audit envelope contract complete 2026-05-08 (revised); amendment-cycle revision 2026-05-09 (Cycle 1) + 2026-05-09 (Cycle 2 — A2-01/04/06/07/08); analyse pass 1 D-03 revision 2026-05-08. **25 typed entry types** defined; all enumerated and schema-pinned. (Added `cascade.depth2_refused` per FR-057 — was 18 prior to first revision; then `lifecycle.refused_while_paused`, `audit.watermark.applied`, `audit.sequence.uncertainty`, `audit.idempotency.replay_cross_user` per Step 8 amendment cycle — 19 → 23; then `audit.rbac.unauthorized_attempt` per analyse pass 1 D-03 / FR-051 — 23 → 24; then `signal_pipeline.dispatch_failed` per Cycle 2 Amendment A2-01 / A2-08 / FR-067 — 24 → 25.)*

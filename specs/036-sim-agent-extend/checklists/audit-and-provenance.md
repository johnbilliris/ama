# Audit & Provenance Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Verify the spec satisfies Constitution **IV — Transparency and Auditability**: every
sub-agent invocation logged with full provenance; every telemetry-injection records canonical
input + parsed signal + confidence + source persona; cascade audit ownership is single-walk; every
audit entry type referenced in the spec is enumerable; the entire simulation lifecycle is forensically
reconstructible from audit alone.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion**: [requirements.md](./requirements.md) (spec-quality, all 16 items pass)

## Append-only, gap-free, typed audit foundation

- [x] CHK001 Append-only, gap-free, typed audit entries mandated for every injection, refusal, sub-agent invocation, sub-agent timeout, sub-agent fallback, sub-agent cancel, watermark application, refusal of a real-world action, and synthetic-delivery event → FR-048
- [x] CHK002 Audit entries machine-exportable for lessons capture (reuses spec-024 audit infrastructure) → FR-049
- [x] CHK003 Refused injections still produce typed audit (never silently dropped) → SC-007
- [x] CHK004 Audit-schema changes (e.g., the category → life-safety boolean mapping) governed by spec 024 audit-schema-governance process → FR-010 (final bullet)

## Sub-agent invocation provenance

- [x] CHK005 Every sub-agent invocation has a unique correlation ID linking the chat turn → invocation → response → any downstream signal/state change → FR-005, scenario US1 #4
- [x] CHK006 Sub-Agent Invocation Record entity captures `correlation_id`, `triggering_chat_turn_id` (or `triggering_signal_id`), `sub_agent`, `tenant_id` (always sim), `request_payload`, `response_payload`, `citations[]`, `degraded`, `error`, `timeout`, `started_at`, `completed_at` → Key Entities (Sub-Agent Invocation Record)
- [x] CHK007 Hard timeout (default 120 s) writes a typed `sub_agent.timeout` audit entry with correlation IDs → FR-006, scenario US1 #3
- [x] CHK008 Tenant-isolation violation (sub-agent citation resolving to live-tenant data) writes an audit entry and marks the reply `degraded` → FR-007
- [x] CHK009 Routing-Decision entity captures `chat_turn_id`, `inferred_intent`, `selected_sub_agents[]`, `jurisdiction`, `location`, `hazard_class`, `confidence`, `ambiguous`, `clarification_required` → Key Entities (Routing Decision)
- [x] CHK010 **Prompt hash** (LLM input fingerprint) recorded per LLM-bearing sub-agent invocation so an exercise can be forensically replayed bit-for-bit (resolved — `apps/agents/common/llm_mixin.py:254 compute_prompt_hash()` produces a SHA-256 fingerprint over `(system_prompt, user_payload, tool_schemas)`; recorded on every sub-agent invocation envelope (`sub_agent_invoker.prompt_hash` field); validated by `apps/api/tests/test_compute_prompt_hash.py`)

## Telemetry-injection provenance — canonical input + parsed signal + confidence + source persona

- [x] CHK011 Every synthetic signal carries `source: "sim-injected"`, `simulation_id`, `injecting_user_id`, `timestamp`, `confidence` (`high|medium|low`), and `gps` (where location-bound) **or be refused at ingest** → FR-009
- [x] CHK012 `injection.refused` audit entry contains the original chat text, the parsed category, the inferred confidence, and the typed reason (`life_safety_low_confidence` per FR-010) → FR-010 (life-safety bullet)
- [x] CHK013 `injection_correlation_id` links every synthetic signal back to its triggering chat turn → FR-011
- [x] CHK014 Multi-signal turns share the same `injection_correlation_id` so all derived signals are jointly traceable → FR-012
- [x] CHK015 Synthetic Signal entity lifecycle is captured (injected → published-to-pipeline → consumed → eventually flagged-stale) so per-stage forensic anchoring is possible → Key Entities (Synthetic Signal)
- [x] CHK016 Contradicting signals tagged `contradicts: <prior_signal_id>` (the prior is preserved, not overwritten) → FR-013
- [x] CHK017 Stale signals flagged `stale: true` so downstream audit/render shows the staleness state at consumption time → FR-014
- [x] CHK018 PII detector redacts; **transcript and signal payload** are redacted in audit; coordinator notified → Edge Cases ("Injection includes PII")
- [x] CHK019 Anti-abuse parse-attempt circuit-breaker trip writes a typed audit entry and notifies the coordinator → FR-009 (final paragraph), Edge Cases ("Buggy or malicious client floods the Telemetry-Injection parser")
- [x] CHK020 `injection.refused` reason set is enumerable: `life_safety_low_confidence`, unknown-category, missing-provenance, `thread.cap_exceeded`, malformed input → FR-009 (refused-doesn't-consume-budget paragraph)

## Single audit envelope per Controller turn

- [x] CHK021 When a chat turn produces both a synthetic signal and a substantive sub-agent invocation, the signal is **fully written and visible to subscribers** before the substantive sub-agents are invoked, so all activity is observable within a single audit envelope → FR-008, FR-015, scenario US1 #5
- [x] CHK022 The audit envelope for the turn lists `simulation-telemetry-injection` as the first invocation and substantive sub-agents after it → scenario US1 #5
- [x] CHK023 The Telemetry-Injection Agent is NOT invoked from outside the Controller's allow-listed invocation surface (single owner of the audit envelope) → FR-008

## Routing-decision audit

- [x] CHK024 `routing.ambiguous` audit entry written when inferred routing is ambiguous → FR-020
- [x] CHK025 `routing.jurisdiction_ambiguous` audit entry written when FR-021 ladder reaches step 5 (clarify) → FR-021 step 5, scenario US4 #8
- [x] CHK026 `jurisdiction_inference_step: 1..5` recorded in the routing-decision audit entry so the matched ladder step is forensically visible → FR-021, scenario US4 #7
- [x] CHK027 `routing.viewport_hint_mismatch` audit entry captures the client hint, the server-computed jurisdiction, the viewport centroid, and the chat-turn ID → FR-021 step 3, scenario US4 #9
- [x] CHK028 The routing decision MUST proceed using the server-computed value when the hint and the lookup disagree (no client-trusted routing) → FR-021 step 3

## Cascade audit ownership — single-walk lessons capture

- [x] CHK029 Cascade audit entries (signal-write, sub-agent invocation, map-overlay update) MUST be written into the **target thread's** audit subtree → FR-057 ("Audit ownership" block)
- [x] CHK030 Each cascade entry tagged `origin_cascade_id: <id>` identifying the originating cascade trigger → FR-057
- [x] CHK031 Exactly **one** `cascade.degraded_to_annotation` back-pointer per cascade, recording the originating cascade trigger (signal ID, triggering thread ID), the suppressed would-be-new-thread proposal, the chosen target thread, and the affinity-ladder step (`affinity_step: 1..5`) → FR-057
- [x] CHK032 FR-054 timeline reconstruction is **single-walk per thread** (per FR-057's audit-ownership model — no cross-thread JOIN required) → FR-054
- [x] CHK033 Affinity-ladder selection is **byte-identical across replays of the same scenario seed** so audit replay is deterministic → FR-057, scenario US6 #7
- [x] CHK034 The audit entry records the candidate set considered alongside the chosen `affinity_step`, so the selection is forensically reproducible → scenario US6 #7

## Cap-exceedance audit

- [x] CHK035 `thread.cap_exceeded` audit entry contains the rejecting sim ID, the rejected thread proposal, the current thread-count → FR-052
- [x] CHK036 No silent drop, no throttling, no queueing of a 6th thread (every refusal is forensically visible) → FR-052
- [x] CHK037 Coordinator-injected and cascade-spawned 6th-thread cases produce **distinct** audit entry types (`thread.cap_exceeded` vs `cascade.degraded_to_annotation`) so the operational cause is unambiguous → FR-052, FR-057, Edge Cases ("6th hazard thread attempted at the FR-052 / A10 cap")

## Synthetic-delivery audit

- [x] CHK038 `synthetic-delivery` audit entry has `payload_hash`, `channel`, `audience`, `sim_timestamp`, `block_reason`, `watermark_applied: true` → FR-038, Key Entities (Synthetic-Delivery Receipt)
- [x] CHK039 Both refusal layers (PublicationService AND HTTP wrapper) write audit entries (defence-in-depth observability) → FR-037, scenario US5 IT
- [x] CHK040 Refused real-world dispatch requests (ADF DACC, BOM warning, NEMA COMDISPLAN) write a typed audit entry → FR-042, Edge Cases ("Free-text injects a real-world action")

## Watermark audit

- [x] CHK041 `audit.watermark.locale_missing` audit entry distinguishes **text variant** vs **audio variant** so the failed-translation pathway is unambiguous → FR-039, FR-058
- [x] CHK042 Each `audit.watermark.locale_missing` entry names the locale and the artefact (or audio-artefact) ID → FR-039, FR-058
- [x] CHK043 Translation-table version pinning per artefact, so a post-exercise lessons-capture replay reproduces the **same** locale string that was emitted at exercise time (resolved — `apps/api/app/config/watermark_text.yaml` is committed under git; every audit envelope captures the loader-resolved bytes via `watermark_text_loader.compute_table_hash()` and embeds `translation_table_version` in `audit_writer` output; replay is byte-for-byte deterministic by virtue of git-pinned config)
- [x] CHK044 Translation-table update is itself an audit-bearing event (e.g., `audit.watermark.table_updated`) so post-update artefact churn is traceable (resolved — `audit.watermark.table_updated` registered in `test_audit_schemas_19_types.py`; emitted by `watermark_text_loader` on hash change; counterpart `audit.watermark.locale_missing` covered for fallback path)

## Lessons-capture and audit retention

- [x] CHK045 Lessons-capture record is idempotent (re-generation byte-identical) and a failed generation is retriable from audit without data loss → FR-055
- [x] CHK046 Exercise Outcome Record sections enumerated: timeline, agent responses, IC decisions, identified gaps, lessons-identified → FR-054, Key Entities (Exercise Outcome Record)
- [x] CHK047 Audit retention policy spans the full simulation lifecycle through lessons capture and beyond (resolved — `apps/api/app/services/simulation/lessons_capture_blob_worm.py` writes lessons to a Blob container with `immutability_policy=ImmutabilityPolicy(immutability_period_since_creation_in_days=2557)` (7 years per spec-024 ADR-036-006); WORM index in Cosmos `exercise_outcome_index`; covered by `apps/api/tests/test_lessons_capture_and_export.py` + `tests/integration/test_blob_worm_persistence_staging.py`)

## Step 8 amendment additions (2026-05-08) — FR-048 5-step fail-closed + FR-065 prompt_hash + Q5/Q6/Q7/Q8

These items extend the original 47-item checklist for the Step 8 amendment cycle
(see [amendment-pass.md](./amendment-pass.md) for the master traceability matrix).

### FR-048 distributed gap-free audit — Amendment D + pass-1 Q2 (5-step fail-closed)

- [ ] CHK048 Audit `sequence_number` allocation is safe across multiple API replicas via
  one of: (a) Cosmos transactional ETag conditional replace on a per-simulation sequence
  document; (b) Cosmos stored procedure; (c) **documented** single-writer constraint with
  replica-affinity routing; the prior process-local `_sequence_counters: dict[str, int]`
  approach is PROHIBITED in production → FR-048, Amendment D
- [ ] CHK049 The fail-closed protocol enumerates **five steps**: (1) HTTP 503 +
  `Retry-After: 5` on the originating endpoint; (2) best-effort
  `audit.sequence.uncertainty` DLQ entry to `simulation_audit_dlq` partitioned by
  `simulation_id` with `sequence_number = -1` and `uncertainty_reason ∈ {etag_exhausted,
  counter_unreachable, replica_partition}`; (3) charged to FR-009 chat-turn budget but
  NOT to FR-026 fan-out budget; (4) idempotent replay returns cached 503 unchanged + DLQ
  written exactly once per original; (5) Constitution-I fail-closed-over-silent-gap with
  `sequence_number = -1` surfaced to FR-049 / FR-054 readers as evidence-integrity
  warnings → FR-048, pass-1 Q2
- [ ] CHK050 `contracts/audit-envelope.md` registers the `audit.sequence.uncertainty`
  audit-entry type with the three-value `uncertainty_reason` enum and the
  `sequence_number = -1` sentinel → FR-048, pass-1 Q2
- [ ] CHK051 FR-049 FOI-export and FR-054 lessons-capture readers detect
  `sequence_number = -1` entries and surface them as evidence-integrity warnings (not
  silent omissions) → FR-048, pass-1 Q2

### FR-065 prompt_hash on every path — Amendment R + pass-1 Q5

- [ ] CHK052 Every Telemetry-Injection audit entry — `injection.accepted`,
  `injection.refused` (any reason), and `injection.fallback` — persists a `prompt_hash`
  field; recording `prompt_hash` only on accepted injections with `null` on
  refused/fallback paths is non-compliant → FR-065
- [ ] CHK053 Every audit entry that carries `prompt_hash` ALSO carries a sibling
  **`prompt_hash_source`** enum field (REQUIRED whenever `prompt_hash` is present) with
  values **`"raw_user_input"`** | **`"canonical_llm_prompt"`** | **`"system_only"`** →
  FR-065, pass-1 Q5
- [ ] CHK054 The byte-source rule is documented and enforced: `raw_user_input` for
  pre-LLM refusal paths (RBAC failure, malformed input, `thread.cap_exceeded`,
  missing-provenance, idempotency conflict) — `prompt_hash = sha256(raw_chat_text_utf8_bytes)`;
  `canonical_llm_prompt` for post-LLM paths (parse success, parse failure with LLM
  invocation, fallback extractor) — `prompt_hash = sha256(canonical_assembled_prompt_text)`;
  `system_only` for paths with no user prompt (scheduled cascade injection, system-
  initiated lifecycle telemetry) — `prompt_hash = sha256(system_prompt_canonical_bytes)`
  → FR-065, pass-1 Q5
- [ ] CHK055 `contracts/audit-envelope.md` adds `prompt_hash_source` to **all 24 typed
  audit entries** that may carry `prompt_hash` (not just the LLM-bearing sub-agent
  invocation entry) → FR-065, pass-1 Q5

### FR-064 + FR-058 delivery_channel — pass-2 Q6

- [ ] CHK056 The `audit.watermark.applied` audit entry records both `delivery_channel`
  ∈ `{audio | text-live-log | both}` AND `resolved_locale`; when the same chat turn
  produces both a screen-reader live-log entry AND a TTS audio artefact, a single
  `audit.watermark.applied` correlation MUST record `delivery_channel: "both"` (NOT two
  separate entries) → FR-064, FR-058, pass-2 Q6
- [ ] CHK057 `contracts/audit-envelope.md` registers the `audit.watermark.applied`
  schema with the three-value `delivery_channel` enum and the `resolved_locale` field →
  FR-064, FR-058, pass-2 Q6

### FR-059 lifecycle audit lineage — pass-2 Q7

- [ ] CHK058 Every lifecycle audit entry (`audit.lifecycle.pause_requested`, `paused`,
  `resume_requested`, `resumed`, `refused_while_paused`, `aborted`) carries BOTH
  `idempotency_key` AND `request_correlation_id` for cross-replay traceability →
  FR-059, FR-066, pass-2 Q7
- [ ] CHK059 An `audit.lifecycle.refused_while_paused` entry is written for every
  request refused while `paused` (new chat turns, new injection attempts, new sub-agent
  invocations); the HTTP 409 refusal itself is NOT written to the FR-066 idempotency
  cache so a fresh request body is serviced cleanly on resume → FR-059, FR-066,
  pass-2 Q7
- [ ] CHK060 The RFC 9457 problem-detail type `"lifecycle-state-conflict"` is registered
  in the contracts and emitted on replay-after-state-transition (e.g. replay
  `POST /pause` after the sim has been resumed) → FR-059, FR-066, pass-2 Q7

### FR-052 thread_kind audit — pass-2 Q8

- [ ] CHK061 The `simulation_state.active_hazard_threads` document records each entry
  with a `thread_kind` field ∈ `{"hazard" | "annotation"}`; only entries with
  `thread_kind = "hazard"` are summed against the FR-052 cap of 5 → FR-052, pass-2 Q8
- [ ] CHK062 The `cascade.degraded_to_annotation` audit entry records the
  `affinity_step: 1..5` AND the candidate set considered, AND records the resulting
  annotation's `thread_kind = "annotation"` so the cap-enforcement edge cases (5 hazard
  + N annotations permitted) are forensically reproducible → FR-052, FR-057, pass-2 Q8

### FR-066 idempotency audit ordering — Amendment S + pass-1 Q3

- [ ] CHK063 The audit writer enforces the order **RBAC check → idempotency-cache
  lookup → action**; an unauthorised principal cannot retrieve a cached coordinator
  response by replaying a known `Idempotency-Key` (FR-051 strengthened by pass-1 Q3) →
  FR-051, FR-066, pass-1 Q3
- [ ] CHK064 The RFC 9457 problem-detail type `"idempotency-key-conflict"` is registered
  and emitted on same-key + same-verb + same-`sim_id` + DIFFERENT-canonical-body
  requests; the audit entry persists alongside the wire response → FR-066, pass-1 Q3
- [ ] CHK065 The 24-h replay window includes 503 responses from FR-048 sequence-
  uncertainty fail-closed; replay returns the cached 503 unchanged WITHOUT re-attempting
  the underlying Cosmos operation; the companion `audit.sequence.uncertainty` DLQ entry
  is written **exactly once** per original request (no duplicate DLQ write on replay) →
  FR-066, FR-048, pass-1 Q2

## Notes

**What this checklist covers**: the Constitution-IV (Transparency & Auditability) surface area of
spec 036 — specifically, that every operation in the simulation produces a typed, append-only,
forensically replayable audit entry; that telemetry-injection provenance carries the canonical
input + parsed output + confidence + source; that the cascade-degradation pathway preserves
single-walk timeline reconstruction; and that every audit entry type referenced in the spec is
enumerable for downstream test-matrix design. The Step 8 amendment additions extend this to the
distributed gap-free 5-step fail-closed protocol (Amendment D + pass-1 Q2), the prompt-hash
+ prompt_hash_source fields on every injection path (Amendment R + pass-1 Q5), the
delivery_channel enum on watermark-applied entries (pass-2 Q6), the lifecycle audit lineage
(pass-2 Q7), the thread_kind cap-counter source (pass-2 Q8), and the RBAC-before-idempotency
ordering (Amendment S + pass-1 Q3).

**What this checklist does NOT cover**:
- Constitution-I (Primacy of Life) safety guarantees — covered by `safety-and-life-primacy.md`.
- CALD watermark rendering completeness — covered by `accessibility-and-cald.md`.
- Test enumerability and acceptance-scenario coverage — covered by `integration-and-test-coverage.md`.
- Failure-mode behaviour and recovery — covered by `graceful-degradation.md`.
- General requirement-quality — covered by `requirements.md`.

**Relation to `requirements.md`**: that checklist verifies the spec is *well-written*. This
checklist verifies the spec is *forensically replayable* — that every event, decision, refusal,
and degradation has a typed audit anchor sufficient for after-action lessons capture and
single-walk timeline reconstruction.

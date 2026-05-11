# Graceful Degradation Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Verify the spec satisfies Constitution **V — Graceful Degradation**: every cap,
limit, fallback, timeout, partition, and missing-resource event produces a **predictable,
typed, coordinator-visible failure** rather than a silent drop, throttle, queue, or LLM-fabricated
recovery. Specifically: predictable failure on cap-exceedance (FR-052 + FR-057);
parse-attempt circuit-breaker hand-off (FR-009); translation-locale-missing fallback
(FR-039 + FR-058); routing-clarify fallback (FR-021 step 5); sub-agent timeout fallback
(FR-006); tenant-isolation-breach fallback (FR-007).
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion**: [requirements.md](./requirements.md) (spec-quality, all 16 items pass)

## Predictable failure on cap-exceedance — FR-052 + FR-057

- [x] CHK001 6th hazard thread coordinator-injected: **hard-refused** with typed `thread.cap_exceeded` audit entry → FR-052, scenario US6 #5
- [x] CHK002 Cap-refusal chat reply explains the cap and recommends splitting into parallel sims (spec 007 FR-010 permits 3 concurrent sims per tenant) → FR-052, A10
- [x] CHK003 6th hazard thread cascade-spawned: **degrades to annotation** on the most-related existing thread with `cascade.degraded_to_annotation` audit entry → FR-057, scenario US6 #6
- [x] CHK004 No silent drop, no throttling, no queueing of a 6th thread (Constitution V — graceful degradation requires **predictable failure**) → FR-052
- [x] CHK005 Cap is enforced **at thread creation** (not by collapsing existing threads) so SC-011 "no combat-agency thread collapse" is preserved by construction → FR-057
- [x] CHK006 The chat timeline surfaces a brief annotation indicating the cascade was attached rather than spawned (visible degradation, not hidden) → FR-057
- [x] CHK007 The cascade-degradation pathway is byte-deterministic across replays of the same scenario seed (so post-exercise lessons capture is reproducible even after cap-exceedance) → FR-057, scenario US6 #7

## Parse-attempt circuit-breaker hand-off — FR-009

- [x] CHK008 Anti-abuse parse-attempt circuit-breaker is enumerated as a **separate** mechanism from the FR-009 success-counted injection budget so it cannot be conflated → FR-009 (final paragraph)
- [x] CHK009 Once tripped, the parser short-circuits with a typed audit entry and notifies the coordinator to investigate the client → Edge Cases ("Buggy or malicious client floods the Telemetry-Injection parser")
- [x] CHK010 Legitimate successful injections remain **unaffected** when the parse-attempt circuit-breaker trips so the exercise can continue under partial-failure conditions → Edge Cases
- [x] CHK011 Refused injections (`life_safety_low_confidence`, unknown-category, missing-provenance, `thread.cap_exceeded`, malformed input) do **NOT** consume the FR-009 success-counted budget so refuse-and-clarify loops never penalise the coordinator under exercise pressure → FR-009
- [x] CHK012 Parse-attempt circuit-breaker exact threshold value (resolved — `apps/api/app/services/simulation/parse_attempt_circuit_breaker.py:32-36` sets `WINDOW_SECONDS=60`, `WINDOW_THRESHOLD=60`, `COOLDOWN_SECONDS=60.0`; covered by `apps/api/tests/test_parse_attempt_circuit_breaker.py`) → FR-009

## Translation-locale-missing fallback — FR-039 + FR-058

- [x] CHK013 Text locale missing from translation table → fall back to **English-only** + `audit.watermark.locale_missing` (text variant) audit entry → FR-039, scenario US5 #7
- [x] CHK014 Audio locale missing from audio-prefix table → fall back to **English-only spoken prefix** + `audit.watermark.locale_missing` (audio variant) audit entry → FR-058, scenario US5 #9
- [x] CHK015 Neither fallback pathway invokes a translation or TTS model — both are deterministic English-only emissions (no LLM-fabricated recovery on either pathway) → FR-039, FR-058, A11
- [x] CHK016 Audit-entry distinction between text variant and audio variant is **explicit** so post-exercise reporting can quantify each pathway's coverage gaps → FR-039, FR-058
- [x] CHK017 Both fallbacks preserve the SC-006 byte-match guarantee on the canonical English string so the egress sweep cannot be bypassed by missing-locale → FR-039, SC-006

## Routing-clarify fallback — FR-021 step 5 + FR-020

- [x] CHK018 FR-021 ladder reaches step 5 (clarify) when steps 1–4 do not resolve a jurisdiction; the Controller MUST NOT route speculatively or fan out to all candidate jurisdictions → FR-021 step 5, scenario US4 #8
- [x] CHK019 FR-021 step 5 writes `routing.jurisdiction_ambiguous` audit entry → FR-021 step 5
- [x] CHK020 FR-020 routing ambiguity (multiple plausible targets at similar confidence) reaches a clarifying chat question with `routing.ambiguous` audit entry → FR-020
- [x] CHK021 FR-021 step 3 viewport-hint mismatch falls back to **server-computed jurisdiction** (client hint discarded) and writes `routing.viewport_hint_mismatch` audit entry → FR-021 step 3, scenario US4 #9
- [x] CHK022 Ambiguous peri-urban / inter-state border zones reach the clarify step rather than being silently misrouted → Edge Cases ("Multi-jurisdiction sim with no explicit jurisdiction in chat")

## Sub-agent timeout fallback — FR-006

- [x] CHK023 Per-sub-agent timeout default 30 s with a `working on it` ack on slow paths → FR-006
- [x] CHK024 Hard timeout default 120 s writes a typed `sub_agent.timeout` audit entry with correlation IDs → FR-006, scenario US1 #3
- [x] CHK025 Coordinator can see the timeout reflected in the audit/timeline view (visible degradation, not hidden) → scenario US1 #3
- [x] CHK026 Streaming partial output is preserved on slow paths so partial decision-support is available even before timeout → FR-003, FR-006

## Tenant-isolation breach fallback — FR-007

- [x] CHK027 Sub-agent citation resolving to a live-tenant resource is treated as a tenant-isolation violation: citation rejected, sub-agent reply marked `degraded`, audit entry written → FR-007
- [x] CHK028 No synthetic signal can escape the simulation tenant in either direction → FR-016, FR-050

## Deliberate degraded-mode injectables — FR-053

- [x] CHK029 `comms-blackout` injectable degrades the Communication agent's channel list for the configured window and **auto-recovers** at the configured time → FR-053, scenario US8 #1
- [x] CHK030 `sub-agent-unavailable` injectable returns `degraded` with cached state for the window and auto-recovers → FR-053, scenario US8 #2
- [x] CHK031 `network-partition` injectable returns `degraded` and the Controller reports the partition status in chat → FR-053, scenario US8 #3
- [x] CHK032 Recovery is **automatic** at the configured time and recorded in audit → FR-053, US8 IT
- [x] CHK033 Affected sub-agent honours the configured behaviour for **100 %** of the configured window across a ≥ 50-injection sample → SC-012
- [x] CHK034 Recovery telemetry: configured-window expiry triggers an **explicit recovery audit entry** type (resolved — `audit.signal.recovery_window_expired` / `audit.signal.recovered` types registered; map_overlay_publisher emits on freshness expiry per `signal_freshness.py`) → FR-053
- [x] CHK035 Configured-window default values for each injectable type (resolved — `apps/api/app/config/signal_freshness.py:26-36` sets weather/fire/geohazard=300 s, hydrology/evacuation/comms=600 s, utility/transport=900 s, resource=1800 s; default 600 s) → FR-053

## Cascade-derived degradation visibility

- [x] CHK036 Telco-outage cascade reduces the Communication agent's available-channel list with unavailable channels **visibly annotated** → FR-041, scenario US5 #4
- [x] CHK037 Triple Zero coverage loss (when telco outage cascades) is **prominently flagged** → FR-041, scenario US5 #4
- [x] CHK038 Stale signals are visually flagged (reduced opacity + stale badge), **not silently hidden** → FR-014, FR-030
- [x] CHK039 Map-overlay capacity overflow clusters / down-samples for render but **preserves the underlying signal payload in audit**; clustering is visually indicated → FR-034, Edge Cases ("Map overlay capacity exceeded")

## Tenant rate-limit graceful-degradation — FR-009 (inherited spec-024 budget)

- [x] CHK040 30-injections/min/user budget counts only **successful** injections (signal landed on the pipeline) → FR-009
- [x] CHK041 Refused injections do not consume budget so the FR-010 refuse-and-clarify loop and FR-052 / FR-057 cap-refusal pathways do not penalise the coordinator under exercise pressure → FR-009

## Contradiction handling and concurrent-coordinator graceful-degradation

- [x] CHK042 Contradicting signals: **both** accepted with `contradicts: <prior_signal_id>` flag (no silent overwrite of the prior signal) → FR-013, Edge Cases ("Injection contradicts an existing signal")
- [x] CHK043 Concurrent multi-coordinator contradicting injections: both accepted with shared `injection_correlation_id` and `contradicts` flags; downstream agents re-run on each; coordinators are notified of the contradiction → Edge Cases ("Concurrent multi-coordinator injection of contradicting signals")
- [x] CHK044 PII detector redacts with coordinator notification (no silent loss; degradation visible to coordinator) → Edge Cases ("Injection includes PII")

## Hard-refusal as graceful-degradation

- [x] CHK045 Hard refusal of real-world action requests (ADF DACC, BOM warnings, NEMA COMDISPLAN, Commonwealth pathways) returns a typed audit + chat explanation rather than crashing → FR-042, Edge Cases ("Free-text injects a real-world action")
- [x] CHK046 `SimulationObserver` injection attempt: refused with UI hiding the action and audit written if API called directly (defence-in-depth refusal) → FR-051, Edge Cases ("`SimulationObserver` user attempts to inject")
- [x] CHK047 Combat-vs-control role-tagging breaches refused (no firefighting / SAR / law-enforcement routed to control entities); audit entry written → FR-022, Edge Cases ("Attempt to invoke a sub-agent for a hazard outside its declared role")
- [x] CHK048 Chat model hallucinates a non-existent agent or signal type: server-side allow-list **refuses execution regardless of model output**; refusal recorded in audit → Edge Cases ("Chat model hallucinates")

## Real Level-3 NEMA throttle as graceful-degradation

- [x] CHK049 If a real Level-3 NEMA event activates while a sim is running, the sim **auto-throttles immediately** (banner + restricted tool list per spec 024 FR-004 / FR-005) → FR-056
- [x] CHK050 Real notifications **MUST NOT be suppressed** under any circumstances (degrade the sim, not the real-world response) → FR-056

## Lessons-capture graceful-degradation

- [x] CHK051 Lessons-capture record is idempotent on regeneration (byte-identical) → FR-055, scenario US9 #2
- [x] CHK052 A failed generation is retriable from audit **without data loss** → FR-055, scenario US9 #3
- [x] CHK053 Lessons-capture timeline reconstruction is single-walk per thread (so cap-degraded cascades are surfaced even when reconstruction encounters a degraded path) → FR-054

## Coordinator-visibility of every degradation event

- [x] CHK054 Every degradation event surfaces in the coordinator-visible audit / chat timeline (no hidden state) — supported by FR-048's append-only typed audit and the chat-timeline annotation contract → FR-048, FR-057, FR-006, FR-009
- [x] CHK055 Browser tab close mid-conversation: server-authoritative simulation state survives; re-opening resumes from the last server snapshot (degraded-client recovery is graceful) → Edge Cases ("Browser tab closed mid-conversation")

## Cascade chain-depth graceful-degradation

- [x] CHK056 Cascade chain-depth limit (resolved — `apps/api/app/services/simulation/cascade_orchestrator.py` enforces depth ≤ 2; depth-2 attempts emit `cascade.depth2_refused` audit + fresh top-level `correlation_id`; covered by `apps/api/tests/test_cascade_orchestrator.py::test_depth2_refused_emits_new_corr`) → FR-043..FR-047, FR-057

## Step 8 amendment additions (2026-05-08) — FR-052 annotation-exclusion + FR-057 affinity ladder + FR-048 fail-closed + Q2 HTTP 503/DLQ

These items extend the original 56-item checklist for the Step 8 amendment cycle
(see [amendment-pass.md](./amendment-pass.md) for the master traceability matrix).

### FR-052 annotation-exclusion from cap — Amendment J + pass-2 Q8

- [ ] CHK057 Annotation threads spawned by `cascade.degraded_to_annotation` do NOT count
  toward the FR-052 thread cap of 5; the cap counts **hazard threads only** with
  `thread_kind = "hazard"` → FR-052, FR-057, pass-2 Q8
- [ ] CHK058 The cap-enforcement edge cases are enumerated and verifiable: 5 hazard +
  N annotations permitted (N unbounded); 4 hazard + cascade-creating-5th-hazard
  succeeds; 5 hazard + cascade trigger degrades to annotation on the affinity-selected
  thread; 6th cascade trigger while at 5 hazard stacks chronologically as another
  annotation on the affinity-selected thread → FR-052, FR-057, pass-2 Q8
- [ ] CHK059 The cap-counter document `simulation_state.active_hazard_threads` uses
  ETag-based transactional update (the FR-048 distributed gap-free mechanism) at the
  thread-cap layer for concurrency safety → FR-052, FR-048, pass-2 Q8
- [ ] CHK060 `cascade_orchestrator.fan_out` calls `ThreadCapService.check_or_acquire()`
  BEFORE every target dispatch; cap-exceedance emits the typed
  `cascade.degraded_to_annotation` audit entry; running the cascade fan-out without
  consulting `ThreadCapService` is PROHIBITED → FR-057, Amendment J

### FR-057 affinity ladder — Amendment J + pass-2 Q8

- [ ] CHK061 The 5-step affinity ladder runs deterministically (no LLM, no heuristics)
  when annotation degradation is selected, choosing the annotation host thread; the
  selection is byte-identical across replays of the same scenario seed → FR-057,
  SC-011
- [ ] CHK062 The `cascade.degraded_to_annotation` audit entry records the chosen
  `affinity_step: 1..5` AND the candidate set considered, so the selection is
  forensically reproducible → FR-057
- [ ] CHK063 When the FR-052 5-thread cap is reached and a cascade trigger fires, the
  affinity ladder selects WHICH of the existing hazard threads receives the annotation
  (not whether the annotation is created — the annotation is always created when cap
  is reached) → FR-052, FR-057, pass-2 Q8
- [ ] CHK064 The thread-cap counter source filter (`thread_kind = "hazard"`) is
  applied AT the `ThreadCapService.check_or_acquire()` read so annotation threads are
  excluded from the count by construction (not by post-hoc subtraction) → FR-052,
  pass-2 Q8

### FR-048 fail-closed semantics — Amendment D + pass-1 Q2

- [ ] CHK065 Sequence-allocator retry exhaustion (max 5 ETag retries, counter
  unreachable, replica partition) returns **HTTP 503 Service Unavailable** with
  `Retry-After: 5` on the originating endpoint; silent gap or speculative
  sequence-number assignment is PROHIBITED → FR-048, pass-1 Q2
- [ ] CHK066 A best-effort `audit.sequence.uncertainty` entry is written to a separate
  fail-safe **dead-letter queue** (`simulation_audit_dlq` Cosmos container partitioned
  by `simulation_id`) with `sequence_number = -1` and `uncertainty_reason` ∈
  `{etag_exhausted, counter_unreachable, replica_partition}` → FR-048, pass-1 Q2
- [ ] CHK067 Sequence-uncertainty handling MAY be charged against the FR-009 chat-turn
  latency budget but MUST NOT be charged against the FR-026 fan-out budget (subscriber
  retries are separately bounded) → FR-048, pass-1 Q2
- [ ] CHK068 Per FR-066, replay of the same `Idempotency-Key` returns the cached 503
  response unchanged WITHOUT re-attempting the underlying Cosmos operation; the DLQ
  entry is written **exactly once** per original request → FR-048, FR-066, pass-1 Q2
- [ ] CHK069 Per Constitution Principle I (Primacy of Life), the system prefers
  fail-closed over a silent gap; downstream readers (FR-054 lessons-capture, FR-049 FOI
  export) detect `sequence_number = -1` entries and surface them as
  evidence-integrity warnings → FR-048, pass-1 Q2

### FR-059 lifecycle round-trip + idempotency refusal — pass-2 Q7

- [ ] CHK070 While `paused`, any non-`resume` and non-`abort` write request (new chat
  turns, new injection attempts, new sub-agent invocations) is refused with HTTP 409 +
  typed `audit.lifecycle.refused_while_paused`; the 409 refusal itself is NOT written to
  the FR-066 idempotency cache so a fresh request body is serviced cleanly on resume →
  FR-059, FR-066, pass-2 Q7
- [ ] CHK071 Replay of `POST /pause` with key `K1` AFTER the simulation has been
  resumed is refused with HTTP 409 + RFC 9457 `type: "lifecycle-state-conflict"`
  problem detail; the cache entry is preserved for the full 24 h replay window as an
  immutable receipt but the state machine refuses re-execution → FR-059, FR-066,
  pass-2 Q7

## Notes

**What this checklist covers**: the Constitution-V (Graceful Degradation) surface area of spec
036 — specifically, that every cap, limit, fallback, timeout, partition, missing-locale,
ambiguous-routing, contradicting-signal, observer-injection, hallucinated-agent, and
tenant-isolation event produces a **predictable, typed, coordinator-visible** failure rather
than a silent drop, throttle, queue, or LLM-fabricated recovery. The Step 8 amendment additions
extend this to the FR-052 annotation-exclusion from the cap (pass-2 Q8), the FR-057 deterministic
5-step affinity ladder for the annotation host (Amendment J), the FR-048 5-step fail-closed
HTTP 503 + DLQ + Retry-After protocol (Amendment D + pass-1 Q2), and the FR-059 + FR-066
lifecycle round-trip refusal semantics (pass-2 Q7).

**What this checklist does NOT cover**:
- Constitution-I (Primacy of Life) safety guarantees beyond the visible-failure contract — covered
  by `safety-and-life-primacy.md`.
- Audit-record completeness and provenance for forensic replay — covered by
  `audit-and-provenance.md`.
- CALD-locale rendering correctness end-to-end — covered by `accessibility-and-cald.md`.
- Test-matrix enumerability and acceptance-scenario coverage — covered by
  `integration-and-test-coverage.md`.
- General requirement-quality — covered by `requirements.md`.

**Relation to `requirements.md`**: that checklist verifies the spec is *well-written*. This
checklist verifies the spec **fails predictably** — that no failure mode (rate-limit, cap,
timeout, partition, missing-locale, ambiguous routing, hostile client) can degrade silently or
recover via an LLM-fabricated path; every degradation is typed, audited, and surfaced to the
coordinator so exercise integrity survives the failure.

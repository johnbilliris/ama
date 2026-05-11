# Integration & Test Coverage Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Verify the spec gives the planning and test phases enough enumerable structure to
write a complete test matrix — that every acceptance scenario has measurable assertions; that the
FR-002 stub-string trip-wire literal is still quoted byte-for-byte; that every audit entry type,
signal category, map overlay layer, sub-agent, combat agency, and outbound channel is enumerable;
that the FR-021 jurisdiction inference ladder and the FR-057 affinity tie-break are
byte-deterministic across replays.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion**: [requirements.md](./requirements.md) (spec-quality, all 16 items pass)

## Trip-wire literals and migration-test anchors

- [x] CHK001 The spec-024 stub-string trip-wire literal `"simulated reply (no data source wired in this environment)"` is quoted byte-for-byte in the spec so the migration test can assert on its absence → FR-002, scenario US1 IT
- [x] CHK002 FR-002 explicitly named "the explicit migration test" so its purpose cannot be lost in downstream refactoring → FR-002
- [x] CHK003 `[SIMULATION] ` literal prefix (with trailing space) is quoted byte-for-byte so chat-receipt assertions are byte-stable → FR-035
- [x] CHK004 Watermark literal `SIMULATION — DO NOT DISTRIBUTE` is quoted byte-for-byte and is verifiable by the SC-006 egress-test sweep → FR-039, SC-006

## Closed-set enumerations for test-matrix design

- [x] CHK005 Telemetry signal-category enum is closed-set (9 categories explicitly listed: `weather`, `fire-behaviour`, `hydrology`, `geohazard`, `utility`, `transport`, `evacuation`, `resource`, `comms-channel-state`) → FR-008
- [x] CHK006 Life-safety vs non-life-safety category mapping is explicitly enumerated (life-safety: `weather`, `fire-behaviour`, `hydrology`, `geohazard`, `evacuation`; non-life-safety: `utility`, `transport`, `comms-channel-state`, `resource`) → FR-010
- [x] CHK007 `confidence` enum closed: `high|medium|low` → FR-009
- [x] CHK008 Sub-agent set closed: Monitoring, Planning, Resource Allocation, Communication, Evacuation, Risk Assessment, plus the new `simulation-telemetry-injection` → FR-001, FR-008
- [x] CHK009 All 16 `sim-telemetry-overlay` map layer types enumerated (wind-arrow, hazard-perimeter, evacuation-route, resource-pin, evac-centre-pin, utility-outage-zone, TC-track-and-cone, road-closure-and-alt-route, vessel-or-aircraft-position, airspace-restriction, maritime-exclusion, hospital-surge, remote-community-access, volunteer-staging, geohazard-zone, flood-polygon) → FR-027
- [x] CHK010 Combat-agency mapping per jurisdiction is closed-set: NSW (FRNSW / NSW RFS), VIC (FRV / CFA), QLD (QFD combined), TAS (TFS combined), WA (DFES sole), SA (SACFS / SAMFS), NT (NTFRS / Bushfires NT), ACT (ESA umbrella) → FR-021
- [x] CHK011 Medical service brand per jurisdiction is closed-set: SAAS, SJA-WA, SJA-NT, AT, ACT-Ambulance, NSW Ambulance, Vic Ambulance, QAS — never a generic ambulance agent → FR-024
- [x] CHK012 SES is the lead flood/storm combat agency in NSW + VIC + QLD; QFD invocable as secondary coordination input in SES-led QLD flood scenarios → cohort table NSW+VIC+QLD
- [x] CHK013 Outbound-channel set closed-set in SC-006 (BOM, GA, NEMA COMDISPLAN, ADF DACC, ABF, ASA, RFDS, ARC, SLSA, SJA, all state/territory alert systems including Emergency Alert, Emergency WA, SA Emergency, TAS Alert, NT Emergency Alert, ACT Emergency Alerts, telco SMS gateways, social media connectors, broadcast integrations) → SC-006
- [x] CHK014 ACT policing routing distinguishes AFP (federal/CT) vs ACT Policing (territory EM) and routes ACT policing to AFP per cohort → FR-023

## Audit-entry type enumerability

- [x] CHK015 Every audit entry type referenced in the spec is enumerable for the test matrix: `injection.refused` (with sub-reasons `life_safety_low_confidence`, unknown-category, missing-provenance, `thread.cap_exceeded`, malformed input), `sub_agent.timeout`, `synthetic-delivery`, `cascade.degraded_to_annotation`, `thread.cap_exceeded`, `routing.ambiguous`, `routing.jurisdiction_ambiguous`, `routing.viewport_hint_mismatch`, `audit.watermark.locale_missing` (text + audio variants) → FR-005, FR-006, FR-009, FR-010, FR-020, FR-021, FR-038, FR-039, FR-048, FR-052, FR-057, FR-058
- [x] CHK016 Sub-agent timeout default values are explicit (30 s soft / 120 s hard) so test cases can be sized → FR-006

## Determinism contracts (test reproducibility anchors)

- [x] CHK017 FR-021 jurisdiction inference 5-step ladder is byte-deterministic with stop-at-first-match and `jurisdiction_inference_step: 1..5` recorded in audit → FR-021
- [x] CHK018 FR-021 step-3 server-side jurisdiction lookup uses an authoritative dataset (platform jurisdiction registry with explicit ABS-SA fallback) and the server-computed value wins → FR-021 step 3
- [x] CHK019 FR-057 affinity 5-step ladder is **pure deterministic** (no LLM, no heuristics) and byte-identical across replays of the same scenario seed → FR-057, scenario US6 #7, SC-011
- [x] CHK020 FR-057 step-4 (most-recent-mutation timestamp newest-wins) and step-5 (thread-creation-id ascending oldest-wins) guarantee a single deterministic answer even when timestamps collide → FR-057
- [x] CHK021 Lessons-capture record is byte-identical on regeneration → FR-055, scenario US9 #2

## Map-delta enumerability and latency targets

- [x] CHK022 Each map-delta latency target is enumerable per category: weather + geohazard ≤ 10 s; hazard + evacuation + resource ≤ 15 s; utility cascade visible within 30 s of original injection → FR-028, FR-029, FR-043
- [x] CHK023 Cascade triggers are enumerable (`utility` per FR-043; `transport` per FR-044; `comms-channel-state` per FR-045; `resource` per FR-046; `evacuation` centre event per FR-047) → FR-043..FR-047
- [x] CHK024 SC-010 measures map-overlay update for **100 % of major signal categories** within FR-028 / FR-029 latency target on a 100-sample observation → SC-010

## Acceptance-scenario coverage

- [x] CHK025 Each FR has at least one acceptance scenario or success criterion (per `requirements.md` iteration evidence) → FR-001..FR-058
- [x] CHK026 FR-008 / FR-015 sequential placement mirrored by scenario US1 #5 → US1 #5
- [x] CHK027 FR-010 hybrid life-safety threshold mirrored by scenarios US2 #6 and US2 #7 → US2
- [x] CHK028 FR-021 ladder mirrored by scenarios US4 #7 (step 3 viewport), US4 #8 (step 5 clarify), US4 #9 (server re-validation winning over client hint) → US4
- [x] CHK029 FR-039 bilingual text + locale-missing fallback mirrored by scenarios US5 #6 and US5 #7 → US5
- [x] CHK030 FR-058 audio bilingual + locale-missing fallback mirrored by scenarios US5 #8 and US5 #9 → US5
- [x] CHK031 FR-052 cap-refusal mirrored by scenario US6 #5 → US6 #5
- [x] CHK032 FR-057 cascade-degradation + tie-break mirrored by scenarios US6 #6 and US6 #7 → US6 #6, #7
- [x] CHK033 FR-002 stub-string trip-wire verified by Independent Test of US1 → US1 IT
- [x] CHK034 Each user story carries an explicit Independent Test paragraph naming the assertion targets → US1..US9 IT paragraphs
- [x] CHK035 US5 Independent Test specifies a network-trace mock to verify zero outbound calls reach any real channel → US5 IT
- [x] CHK036 US3 Independent Test specifies wall-clock latency observation (15 s arrow appearance) → US3 IT

## Success-criteria measurability

- [x] CHK037 SC-001..SC-012 each carry quantitative thresholds and sample sizes → SC-001..SC-012
- [x] CHK038 Baseline definition explicit: same scenario re-run with auto-fan-out and Telemetry-Injection Agent disabled (spec-024-only behaviour) → A8
- [x] CHK039 Baseline runs matched on scenario seed, jurisdiction, hazard class, and starting telemetry → A8
- [x] CHK040 Economic-loss baseline defined: AIDR-aligned synthetic economic profile maintained in the scenario library (no real economic data consumed) → A9
- [x] CHK041 SC-006 (zero false-positive deliveries) measured **continuously** across all participating egress channels; any single false positive is SEV-0 → SC-006
- [x] CHK042 SC-008 verified by automated egress-test sweep on every PR → SC-008
- [x] CHK043 SC-011 measured across 30 multi-hazard exercises with **zero** combat-agency thread collapse → SC-011

## Planning hand-offs (parameters explicitly deferred to plan phase)

- [x] CHK044 Parse-attempt circuit-breaker exact threshold value (resolved — `apps/api/app/services/simulation/parse_attempt_circuit_breaker.py:32-36` sets `WINDOW_SECONDS=60`, `WINDOW_THRESHOLD=60`, `COOLDOWN_SECONDS=60.0`; covered by `apps/api/tests/test_parse_attempt_circuit_breaker.py`) → FR-009, Edge Cases (parser-flood)
- [x] CHK045 Authoritative jurisdiction-boundary dataset wiring (resolved — `apps/api/app/services/simulation/jurisdiction_boundary_service.py` loads boundary polygons via STRtree spatial index with explicit ABS-SA4 fallback step; small WKT/GeoJSON test fixture under `tests/fixtures/jurisdiction_boundaries/`; full AU Geoscience dataset deployed at runtime via Bicep storage container; jurisdiction ladder enumerates `abs_sa4_fallback`; covered by `apps/api/tests/test_jurisdiction_routing.py`) → FR-021 step 3
- [x] CHK046 Per-category freshness window values (resolved — `apps/api/app/config/signal_freshness.py:26-36` enumerates weather/fire/geohazard=300 s, hydrology/evacuation/comms=600 s, utility/transport=900 s, resource=1800 s; default 600 s; covered by `apps/api/tests/test_map_overlay_publisher.py`) → FR-013, FR-014, FR-030
- [x] CHK047 FR-020 routing "similar confidence" ambiguity threshold (resolved — `apps/api/app/services/simulation/agent_routing_table.py` enumerates routing agencies; routing similarity ambiguity is plan-decision #6 fixed at Δ ≤ 0.10 (10 percentage points) per `plan.md` decision register; ambiguous routing emits `routing.clarification_required` audit per `apps/api/app/services/simulation/routing_audit_writers.py`)
- [x] CHK048 CALD locale-set membership for translation tables (resolved — MVP delivered set is en-AU, zh-Hans, zh-Hant, ar, vi, hi, el, it, tl, tr, id (11 locales) per `apps/api/app/config/watermark_text.yaml:9-15`; remaining ~19 CALD locales tracked in `docs/runbooks/cald-locale-backlog.md` with locale_missing fallback to en-AU + audit) → A11
- [x] CHK049 Sub-agent unavailable / network-partition / comms-blackout configured-window default values (resolved — sub-agent unavailable window matches the per-category `signal_freshness.py` map; network-partition / comms-blackout share the 600 s default; recovery audit emitted via `audit.signal.recovery_window_expired`) → FR-053
- [x] CHK050 Cascade chain depth limit (resolved — `apps/api/app/services/simulation/cascade_orchestrator.py:200-243` enforces depth ≤ 2; depth-2 attempts emit `cascade.depth2_refused` audit + fresh `correlation_id`; covered by `apps/api/tests/test_cascade_orchestrator.py::test_depth2_refused_emits_new_corr`) → FR-043..FR-047, FR-057

## Test-design hand-offs (test fixtures and harness implementation)

- [x] CHK051 Test seed catalogue for SC-011 byte-deterministic reproducibility runs (resolved — `tests/simulation/test_sc011_thread_collapse.py` exercises 30 multi-hazard scenarios with deterministic seeding; `tests/contract/test_telemetry_injection_llm.py` provides 5 byte-deterministic prompt fixtures with cassette payloads pinned in git; affinity-ladder seed determinism covered by `apps/api/tests/test_cascade_affinity_ladder.py::test_ladder_byte_deterministic`) → SC-011, scenario US6 #7
- [x] CHK052 Test fixtures covering each of the 9 signal categories at each of `high|medium|low` confidence (resolved — `tests/contract/test_telemetry_injection_llm.py` parameterises over 5 hazard categories × 3 confidence levels; `apps/api/tests/test_audit_schemas_19_types.py` covers all 19 audit envelope variants; remaining 4 categories covered by integration tests under `tests/integration/test_sc009_auto_routing_coverage.py`) → FR-008, FR-010
- [x] CHK053 Network-trace mock implementation for SC-006 SEV-0 monitoring (resolved — `tests/devops/test_sev0_egress_alert.py` exercises the SEV-0 SimEgressBlocked alert via the bicep diagnostics tap; outbound HTTP wrapper `SimAwareHttpClient` blocks live egress and the synthetic-delivery service records every block) → SC-006
- [x] CHK054 Egress-test sweep automation triggering on every PR (resolved — `.github/workflows/simulation-stub-sweep.yml` runs `tools/simulation_stub_sweep.py --enforce` as a blocking PR gate; covered by `tests/devops/test_observability_alerts_bicep.py` and `tools/simulation_stub_sweep.py` self-tests) → SC-008
- [x] CHK055 Forensic replay harness for FR-057 byte-determinism verification (resolved — `tests/simulation/paired_exercise_harness.py` + `tests/simulation/test_paired_exercise_harness.py` provide the replay fixture; the LLM-determinism contract in `tests/contract/test_telemetry_injection_llm.py` enforces `response_format` strict-mode + cassette-based byte equality across runs; affinity-ladder + prompt-hash determinism complete the chain) → FR-057, US6 #7
- [x] CHK056 Per-jurisdiction combat-agency routing test matrix (resolved — `apps/api/app/services/simulation/agent_routing_table.py` + `apps/api/app/config/agent_routing_table.yaml` enumerate combat/control/police/medical agencies for every jurisdiction; covered cross-product by `apps/api/tests/test_jurisdiction_routing.py` and `tests/integration/test_sc009_auto_routing_coverage.py`) → FR-021
- [x] CHK057 Concurrent multi-coordinator contradicting-signal test fixtures (resolved — `apps/api/tests/test_map_overlay_publisher.py` covers the contradiction-tagging path; `apps/api/tests/test_audit_schemas_19_types.py` covers `signal.contradiction_tagged` audit; multi-coordinator concurrency covered by `apps/api/tests/test_thread_cap_service.py::test_cap_atomic_contention`) → Edge Cases
- [x] CHK058 Multi-hazard 5-thread concurrent-injection performance test fixtures (resolved — `tests/load/simulation_injection_load.py` Locust harness drives 200 concurrent injections at p95 < 5 s with the 5-thread cap enforced; `tests/load/test_workflow_capacity.py` validates the 5-thread cap under load; staging-gated via `simulation-load-test.yml`) → A10, FR-052, scenario US6 IT

## Notes

**What this checklist covers**: the test-matrix enumerability surface area of spec 036 — that
every literal trip-wire (stub-string, watermark, `[SIMULATION] ` prefix) is byte-quoted in the
spec; that every closed-set enum (signal category, sub-agent, combat agency, audit entry type,
map overlay layer, outbound channel, jurisdiction → agency mapping) is enumerable for test
generation; that every acceptance scenario maps to a measurable assertion; and that determinism
contracts (FR-021 jurisdiction ladder, FR-057 affinity ladder, FR-055 idempotent lessons-capture)
are explicit so they can be tested by replay.

**What this checklist does NOT cover**:
- Constitution-I (Primacy of Life) safety guarantees — covered by `safety-and-life-primacy.md`.
- Audit-record completeness for forensic replay — covered by `audit-and-provenance.md`.
- CALD-locale rendering completeness — covered by `accessibility-and-cald.md`.
- Failure-mode behaviour and recovery — covered by `graceful-degradation.md`.
- General requirement-quality — covered by `requirements.md`.

**Relation to `requirements.md`**: that checklist verifies the spec is *well-written*. This
checklist verifies the spec is *test-implementable* — that the planning and test phases have
enough closed-set structure, byte-quoted literals, and explicit hand-offs to build a complete
test matrix without re-opening the spec for clarification on enumerable values.

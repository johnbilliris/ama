# Safety & Life-Primacy Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Verify the spec satisfies Constitution **Principle I — Primacy of Life**: no real
public-warning leakage under any code path; HITL on every life-safety telemetry write; deterministic
fail-safes on every safety-critical decision; no LLM in critical-path safety logic; provenance
unbroken end-to-end on every life-safety pathway.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion**: [requirements.md](./requirements.md) (spec-quality, all 16 items pass)

## Coordinator override / pause / abort surface

- [x] CHK001 Coordinator-injected attempt to exceed concurrent-thread cap is **hard-refused** (no silent drop, no throttle, no queue) so the coordinator retains predictable control under exercise pressure → FR-052, scenario US6 #5
- [x] CHK002 Cap-refusal chat reply explains the cap and recommends splitting into parallel sims → FR-052
- [x] CHK003 Refusal of real-world action requests (ADF DACC, BOM warning, NEMA COMDISPLAN, ADF/Commonwealth pathways) returns a typed audit + chat explanation rather than crashing → FR-042, scenario US5 #5, Edge Cases ("Free-text injects a real-world action")
- [x] CHK004 `SimulationObserver` users are blocked from injecting at both UI and API surfaces → FR-051, Edge Cases ("`SimulationObserver` user attempts to inject telemetry")
- [x] CHK005 Coordinator-invoked **pause / abort** of an active simulation is enumerated as a first-class control surface (resolved in plan/impl — `apps/api/app/api/routes/simulations_036.py` exposes POST `/api/simulations/{simId}/pause`, `/resume`, `/abort` endpoints with audit-on-transition; FR-059 was added to spec; covered by `apps/api/tests/test_lifecycle_endpoints.py`)

## Telemetry parsing fail-safes — hybrid life-safety threshold

- [x] CHK006 The five life-safety signal categories are explicitly enumerated and decisive: `weather`, `fire-behaviour`, `hydrology`, `geohazard`, `evacuation` → FR-010
- [x] CHK007 Life-safety low-confidence parses are **refused-and-clarified** (no synthetic signal written; clarifying chat question returned; `injection.refused` audit entry written with reason `life_safety_low_confidence`) → FR-010, scenario US2 #6
- [x] CHK008 Hybrid-gate rationale explicitly invokes Constitution Principle I (primacy of life) so the design intent survives downstream refactoring → FR-010 ("Rationale: … Constitution Principle I (primacy of life) requires a refuse-and-clarify gate")
- [x] CHK009 Non-life-safety low-confidence parses are accepted with `confidence: low` recorded so degraded data is visible-not-hidden → FR-010, scenario US2 #7
- [x] CHK010 The **category → life-safety boolean** mapping is a single source of truth used by both the parser gate and the audit entry → FR-010 (last bullet of hybrid rule)
- [x] CHK011 Refused life-safety injections do **NOT** consume the per-user injection budget so the safety gate is never under rate-limit pressure → FR-009
- [x] CHK012 Post-injection re-uses of `confidence: low` (sub-agent self-degraded re-evaluations, cascade-induced staleness, network-partition fallback) are **explicitly preserved** so the gate cannot be widened by accident at later boundaries → FR-010 (third bullet)

## No real comms can leak under any code path

- [x] CHK013 `[SIMULATION] ` literal prefix mandated **byte-for-byte** on every Communication-agent receipt (visually unmistakable in any rendering) → FR-035
- [x] CHK014 Real-world publication hard-blocked at **PublicationService AND outbound HTTP client wrapper** (defence in depth, two independent refusals) → FR-037
- [x] CHK015 Each blocked outbound recorded as `synthetic-delivery` audit entry with payload hash, channel, audience, sim-timestamp, block reason → FR-038
- [x] CHK016 `[SIMULATION] ` prefix and watermark cover **every outbound channel for every agency in every jurisdiction** (Emergency Alert, Emergency WA, SA Emergency, TAS Alert, NT Emergency Alert, ACT Emergency Alerts, BOM, GA, NEMA, ADF DACC, ABF, ASA, RFDS, ARC, SLSA, SJA, telco SMS, social, broadcast) → FR-040, SC-006
- [x] CHK017 Watermark `SIMULATION — DO NOT DISTRIBUTE` applied to every render and every translated language → FR-039
- [x] CHK018 Watermark applied **before** any IC approval step **and before** any would-have-published event so it cannot be retro-suppressed → FR-039
- [x] CHK019 Watermark NEVER produced via LLM translation path (text artefacts) → FR-039
- [x] CHK020 Watermark NEVER produced via LLM-generated TTS of an LLM-translated string (audio artefacts) → FR-058
- [x] CHK021 Locale-missing fallback writes `audit.watermark.locale_missing` (text variant) and falls back to canonical English only — no LLM fallback → FR-039
- [x] CHK022 Locale-missing fallback writes `audit.watermark.locale_missing` (audio variant) and falls back to canonical English spoken prefix only — no LLM-TTS fallback → FR-058
- [x] CHK023 SC-006 measures **zero** real-world deliveries continuously across all enumerated egress channels and treats any single false positive as SEV-0 → SC-006

## HITL on all life-safety telemetry

- [x] CHK024 Risk Assessment auto-fan-out triggers on **every** hazard-telemetry change without requiring a separate chat message (so the coordinator never has to remember to invoke it) → FR-026, scenario US4 #6
- [x] CHK025 Sub-agent timeout produces a `working on it` ack and writes a typed `sub_agent.timeout` audit entry (no silent stall on a life-safety pathway) → FR-006
- [x] CHK026 Routing ambiguity reaches a coordinator-facing **clarifying question** rather than speculative routing on a combat-agency assignment → FR-020, FR-021 step 5
- [x] CHK027 NSW persona handoffs do NOT auto-escalate to IC without explicit user direction (per cohort guidance — prevents accidental IC declaration) → FR-025
- [x] CHK028 Combat-vs-control role tagging is enforced — firefighting / SAR / law-enforcement intents cannot be routed to control/coord/support entities (Local/State/Territory govt, ARC, NGOs, Health, Volunteers) → FR-022, Edge Cases ("Attempt to invoke a sub-agent for a hazard outside its declared role")
- [x] CHK029 Tenant-isolation breach (sub-agent citation that resolves to a live-tenant resource) marks the reply `degraded` and writes an audit entry → FR-007
- [x] CHK030 No synthetic signal can escape the simulation tenant in either direction → FR-016, FR-050

## Risk-Assessment fan-out provenance unbroken

- [x] CHK031 Single audit envelope per Controller turn: telemetry-injection invoked **sequentially first**, signal **fully written** to pipeline, **then** substantive sub-agents invoked — no race-condition on read-your-own-write → FR-008, FR-015, scenario US1 #5
- [x] CHK032 `injection_correlation_id` links every synthetic signal back to its triggering chat turn → FR-011
- [x] CHK033 Multiple signals from a single turn share the same `injection_correlation_id` so cascade analysis is single-walk → FR-012
- [x] CHK034 Cascade audit entries (signal-write + sub-agent invocation + map-overlay update) tagged `origin_cascade_id` and written into the **target thread's** audit subtree so provenance is preserved when cap-degradation occurs → FR-057
- [x] CHK035 Exactly one `cascade.degraded_to_annotation` back-pointer per degraded cascade so the originating trigger is never lost → FR-057
- [x] CHK036 Single-walk lessons-capture timeline reconstruction over the target thread surfaces every cascade that touched it (no cross-thread JOIN required) → FR-054
- [x] CHK037 Refused injections still produce typed audit (never silently dropped) so safety-related refusals are forensically visible → SC-007

## No LLM in deterministic critical paths

- [x] CHK038 FR-057 affinity ladder is **pure deterministic** — 5 explicit ranking steps, **no LLM, no heuristics**, byte-deterministic for SC-011 reproducibility across exercise replays → FR-057, scenario US6 #7
- [x] CHK039 FR-021 jurisdiction inference ladder is **deterministic** — 5 explicit steps with a single stop-at-first-match rule, recorded as `jurisdiction_inference_step: 1..5` → FR-021
- [x] CHK040 FR-021 step-3 viewport hint treated as **advisory only**: server **re-validates** centroid → jurisdiction lookup against an authoritative server-side dataset; the **server-computed jurisdiction wins** → FR-021 step 3, scenario US4 #9
- [x] CHK041 Watermark text translation pulls from a **version-controlled table** under spec 024 watermark-governance — no LLM in the translation path → FR-039, A11
- [x] CHK042 Watermark audio prefix pulls from a **version-controlled audio-prefix table** under spec 024 watermark-governance — no LLM-TTS in the prefix path → FR-058, A11
- [x] CHK043 Server-side allow-list refuses any sub-agent or signal type the chat model hallucinates → Edge Cases ("Chat model hallucinates a non-existent agent or signal type")
- [x] CHK044 Real Level-3 NEMA event auto-throttles the sim **immediately** and **MUST NOT suppress real notifications** under any circumstances → FR-056

## Notes

**What this checklist covers**: the Constitution-Principle-I (Primacy of Life) surface area of spec 036
— specifically, the deterministic guarantees that no real public warning can leak from a simulation,
that life-safety telemetry never enters the pipeline without HITL on low-confidence parses, that the
coordinator can always override / refuse / abort, and that LLMs are never on the critical path of a
safety decision (jurisdiction routing, cascade affinity, watermark translation, audio prefix).

**What this checklist does NOT cover**:
- General requirement-quality (clarity / completeness / consistency of FR wording) — covered by
  `requirements.md` (the `/speckit.specify` checklist re-validated through pass-1 and pass-2).
- Audit-record completeness for non-safety pathways — covered by `audit-and-provenance.md`.
- CALD-locale rendering correctness end-to-end — covered by `accessibility-and-cald.md`.
- Test enumerability and matrix coverage — covered by `integration-and-test-coverage.md`.
- Degraded-mode / fallback behaviour for non-safety failures — covered by `graceful-degradation.md`.

**Relation to `requirements.md`**: that checklist verifies the spec is *well-written*. This
checklist verifies the spec is *constitutionally safe* — that the safety-critical FR set is
complete and unambiguous enough that downstream code cannot accidentally degrade Principle I.

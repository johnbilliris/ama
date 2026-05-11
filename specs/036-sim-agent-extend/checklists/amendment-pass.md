# Amendment-Pass Checklist: Step 8 Cross-Cohort Re-Loop (2026-05-08)

**Purpose**: Master traceability checklist for the Step 8 amendment cycle on spec-036. Covers
**every** item that must hold true for the 19 amendments (A–S) and the 8 new clarification
Q→A entries (pass 1 Q1–Q5 + pass 2 Q6–Q8) before the next `speckit.plan` / `speckit.tasks`
cycle is rerun. Each item is testable, FR-cross-referenced, categorised
(**Spec | Contract | Implementation | Test | Operations**), and severity-ranked
(**P0 = BLOCKER**, **P1 = HIGH**, **P2 = MEDIUM**).
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md) (Step 8 Amendment Log at top)
**Companions**:
[requirements.md](./requirements.md) (spec-quality master),
[accessibility-and-cald.md](./accessibility-and-cald.md),
[audit-and-provenance.md](./audit-and-provenance.md),
[graceful-degradation.md](./graceful-degradation.md),
[multi-jurisdiction.md](./multi-jurisdiction.md),
[safety-and-life-primacy.md](./safety-and-life-primacy.md),
[integration-and-test-coverage.md](./integration-and-test-coverage.md).

**Severity legend**:

- **P0 (BLOCKER)** — Constitution-bound (Primacy of Life, AU residency, Transparency &
  Auditability, AAD-only auth) or directly tied to one of the 18 CRITICAL Step-8 findings.
  Failure of any P0 item blocks production promotion.
- **P1 (HIGH)** — Operational correctness items (idempotency, gap-free audit, RBAC,
  cascade fan-out integrity) tied to HIGH cohort findings. Failure blocks staging promotion.
- **P2 (MEDIUM)** — Polish, locale/persona coverage, lessons-capture content depth.
  Failure surfaces as a release-readiness reservation, not a hard block.

**Category legend**:

- **Spec** — spec.md MUST contain the cited language (FR text, table, enum, MUST/SHALL).
- **Contract** — `contracts/*.md` or `contracts/*.yaml` MUST carry the schema/enum/problem-detail.
- **Implementation** — production code MUST behave per the FR at runtime.
- **Test** — automated test (unit / integration / E2E / contract / a11y / regression) MUST
  exist and pass.
- **Operations** — CI/CD gate, runbook, deployment promotion evidence, registry, or
  runtime ops surface.

---

## Amendment A — FR-061 AIIMS function-to-sub-agent mapping (NEW) + pass-1 Q4

- [ ] CHK001 spec.md FR-061 enumerates the **canonical AIIMS-function-to-sub-agent table**
  covering all six AIIMS functions (Control, Operations, Logistics, Intelligence, Planning,
  Public Information) and the nine simulation sub-agents → FR-061 [Spec, **P0**]
- [ ] CHK002 spec.md FR-061 mandates that `aiims_function` on every Sub-Agent Invocation
  Record is **single-valued** (exactly one canonical AIIMS function per invocation) and
  routing logic + FR-054 lessons-capture deterministic ordering consume **only** the
  primary value → FR-061, pass-1 Q4 [Spec, **P0**]
- [ ] CHK003 spec.md FR-061 defines the `secondary_aiims_tags` array (max 2 entries,
  may be empty) with the canonical primary/secondary mapping for the nine sub-agents
  (Communication: primary `Public Information`, secondary `["Operations"]`; Evacuation:
  primary `Operations`, secondary `["Public Information"]`; Resource Allocation: primary
  `Logistics`, secondary `["Operations"]`; Risk Assessment: primary `Intelligence`,
  secondary `["Planning"]`; …) → FR-061, pass-1 Q4 [Spec, **P0**]
- [ ] CHK004 `contracts/sub-agent-adapter.md` and the Sub-Agent Invocation Record entity in
  `data-model.md` MUST add the `aiims_function` (single-valued) and `secondary_aiims_tags`
  (string array, max 2) fields to the typed schema → FR-061 [Contract, **P0**]
- [ ] CHK005 The lessons-capture writer (FR-054 §4 IC decisions) MUST surface the resolved
  primary `aiims_function` alongside the sub-agent name and MUST NOT introduce ordering
  by `secondary_aiims_tags` → FR-061, FR-054 [Implementation, **P1**]

---

## Amendment B — FR-027 visible rendering (STRENGTHENED)

- [ ] CHK006 spec.md FR-027 states that **all 16 layer types MUST be visually rendered when
  geometrically applicable**; the Map a11y digest is REQUIRED but **NOT SUFFICIENT** as a
  substitute for visual rendering → FR-027 [Spec, **P0**]
- [ ] CHK007 The web map component MUST render LineString and Polygon geometries (evacuation
  routes, hazard perimeters, flood polygons, road closures, TC cones, maritime exclusions,
  utility zones) in addition to Point overlays — i.e. no `.filter((f) => f.geometry.type === "Point")`
  bottleneck remains in the rendering path → FR-027 [Implementation, **P0**]
- [ ] CHK008 An automated test asserts that all 16 canonical layer types render as a visible
  SVG/Canvas/WebGL primitive (not just as a digest entry) on the simulation page → FR-027
  [Test, **P0**]

---

## Amendment C — FR-009 / FR-015 transactional invariant (STRENGTHENED) + pass-1 Q1

- [ ] CHK009 spec.md FR-009/FR-015 mandate the **publish-before-ack invariant**: accepted
  telemetry MUST be (a) persisted to `simulation_synthetic_signals`, (b) published to the
  tenant-scoped event pipeline, (c) consumed by all subscribed sub-agents within the turn
  barrier — **all before** the inject-telemetry endpoint returns 202/200 → FR-009, FR-015
  [Spec, **P0**]
- [ ] CHK010 spec.md mandates that the inject-telemetry response `triggered_sub_agents[]`
  array is populated with one entry per subscribed sub-agent (sub-agent name, correlation
  ID, aggregated reply where applicable); returning an empty `triggered_sub_agents: []`
  while sub-agents subscribe to the signal type is PROHIBITED → FR-009, FR-015 [Spec, **P0**]
- [ ] CHK011 spec.md (pass-1 Q1) adds the `trigger_source` enum field with values
  `"subscriber" | "controller_intent"` on every entry of `triggered_sub_agents[]`; the
  inject-telemetry response body MUST list only `subscriber` entries; the Controller turn
  audit envelope MUST additionally list `controller_intent` entries within the same envelope
  → FR-009, FR-015, FR-026, pass-1 Q1 [Spec, **P0**]
- [ ] CHK012 spec.md (pass-1 Q1) mandates that a sub-agent that is **both** a subscriber
  AND chat-intent-inferred MUST be invoked **exactly once** by the inject-telemetry
  endpoint and its result MUST be propagated into the Controller's substantive-aggregation
  reply via a **shared `injection_correlation_id`** (one correlation ID per chat turn);
  double-invocation is PROHIBITED → FR-009, FR-026, pass-1 Q1 [Spec, **P0**]
- [ ] CHK013 `contracts/openapi-simulation.yaml` AND `contracts/audit-envelope.md` add
  `trigger_source` enum to the typed schemas; contract test asserts the enum is
  `["subscriber", "controller_intent"]` (no other values) → FR-009, pass-1 Q1
  [Contract, **P0**]
- [ ] CHK014 An orchestration service implements the **full transaction**
  `parse → durable signal write → tenant-scoped event publish → subscriber fan-out →
  aggregated chat response → map updates` atomically before HTTP response, with idempotent
  rollback on any sub-step failure → FR-009, FR-015 [Implementation, **P0**]
- [ ] CHK015 An E2E test asserts the publish-before-ack invariant: subscribers OBSERVE the
  signal in the pipeline (or persisted store) BEFORE the HTTP 202/200 response is received
  by the test client → FR-009, FR-015 [Test, **P0**]

---

## Amendment D — FR-048 distributed gap-free audit (STRENGTHENED) + pass-1 Q2

- [ ] CHK016 spec.md FR-048 mandates that `sequence_number` allocation is safe across
  multiple API replicas via one of: (a) Cosmos transactional ETag conditional replace on a
  per-simulation sequence document; (b) Cosmos stored procedure; (c) **documented**
  single-writer constraint with replica-affinity routing → FR-048 [Spec, **P0**]
- [ ] CHK017 spec.md (pass-1 Q2) FR-048 fail-closed protocol enumerates the **five steps**:
  (1) HTTP 503 + `Retry-After: 5`; (2) best-effort `audit.sequence.uncertainty` DLQ entry
  with `sequence_number = -1` + `uncertainty_reason ∈ {etag_exhausted, counter_unreachable,
  replica_partition}`; (3) charged to FR-009 chat-turn budget but NOT to FR-026 fan-out
  budget; (4) replay returns cached 503 unchanged + DLQ written exactly once per original;
  (5) Constitution-I fail-closed-over-silent-gap with `sequence_number = -1` surfaced as
  evidence-integrity warning → FR-048, pass-1 Q2 [Spec, **P0**]
- [ ] CHK018 `contracts/audit-envelope.md` registers the `audit.sequence.uncertainty`
  audit-entry type with the three-value `uncertainty_reason` enum and the `sequence_number = -1`
  sentinel → FR-048, pass-1 Q2 [Contract, **P0**]
- [ ] CHK019 The audit writer integrates the chosen distributed sequence-allocation
  mechanism (NOT the process-local `_sequence_counters: dict[str, int] = {}`) and FAILS
  CLOSED with HTTP 503 on retry exhaustion (max 5 ETag retries) → FR-048
  [Implementation, **P0**]
- [ ] CHK020 A `simulation_audit_dlq` Cosmos container exists, partitioned by
  `simulation_id`, and the audit writer writes the DLQ entry **best-effort** (does not block
  the 503 response) on sequence uncertainty → FR-048, pass-1 Q2 [Implementation, **P0**]
- [ ] CHK021 An E2E test injects N concurrent telemetry calls across ≥ 2 API replicas and
  asserts **0 sequence-number gaps** in any simulation's audit subtree → FR-048,
  FR-063 SLI #2 [Test, **P0**]
- [ ] CHK022 FR-049 FOI-export and FR-054 lessons-capture readers detect
  `sequence_number = -1` entries and surface them as evidence-integrity warnings (not
  silent omissions) → FR-048, pass-1 Q2 [Implementation, **P0**]

---

## Amendment E — FR-051 RBAC enforcement (STRENGTHENED)

- [ ] CHK023 spec.md FR-051 mandates that every coordinator-only route (inject-telemetry,
  pause, resume, abort) MUST validate JWT/app-role membership in `Simulation.Coordinator`
  AND tenant membership BEFORE any audit attempt; anonymous fallbacks are PROHIBITED
  in production → FR-051 [Spec, **P0**]
- [ ] CHK024 spec.md (pass-1 Q3 strengthening of FR-051) mandates that the RBAC check
  executes BEFORE the FR-066 idempotency-cache lookup so an unauthorised principal cannot
  retrieve a cached coordinator response by replaying a known `Idempotency-Key` →
  FR-051, FR-066, pass-1 Q3 [Spec, **P0**]
- [ ] CHK025 A FastAPI dependency (or equivalent middleware) enforces JWT/app-role +
  tenant validation on all four coordinator-only routes; no `getattr(..., "anonymous-coord")`
  fallback remains in the production code path → FR-051 [Implementation, **P0**]
- [ ] CHK026 Unauthorised coordinator-only requests return HTTP 403 AND emit a typed
  `audit.lifecycle.unauthorized_attempt` (or equivalent) audit entry; the request never
  reaches the idempotency-cache layer → FR-051, FR-066 [Implementation, **P0**]
- [ ] CHK027 An integration test sweeps each of the four coordinator-only routes with
  `Simulation.Observer`, `Simulation.Coordinator`, anonymous, and cross-tenant principals
  and asserts the RBAC outcome matrix → FR-051 [Test, **P0**]

---

## Amendment F — FR-059 lifecycle state enforcement (STRENGTHENED) + pass-2 Q7

- [ ] CHK028 spec.md FR-059 mandates that `pause` PERSISTS simulation state to a durable
  store; future chat turns, telemetry injections, and sub-agent invocations MUST be refused
  with HTTP 409 + typed `audit.lifecycle.refused_while_paused` audit entry while paused →
  FR-059 [Spec, **P0**]
- [ ] CHK029 spec.md FR-059 mandates that `abort` **queues** the FR-054 lessons-capture
  job (claim of `lessons_capture_started=True` without queuing is PROHIBITED) → FR-059,
  FR-054 [Spec, **P0**]
- [ ] CHK030 spec.md (pass-2 Q7) defines the lifecycle round-trip semantics with FR-066:
  (a) replay-during-same-phase returns cached response unchanged; (b) replay-after-state-
  transition is refused with HTTP 409 + RFC 9457 `type: "lifecycle-state-conflict"` problem
  detail; (c) HTTP 409 refusals are NOT written to the idempotency cache; (d) per-verb
  namespace preserved across pause/resume/abort → FR-059, FR-066, pass-2 Q7 [Spec, **P0**]
- [ ] CHK031 spec.md (pass-2 Q7) mandates that every lifecycle audit entry
  (`audit.lifecycle.pause_requested`, `paused`, `resume_requested`, `resumed`,
  `refused_while_paused`, `aborted`) carries BOTH `idempotency_key` AND
  `request_correlation_id` for cross-replay traceability → FR-059, FR-066, pass-2 Q7
  [Spec, **P0**]
- [ ] CHK032 `contracts/audit-envelope.md` adds `idempotency_key` and
  `request_correlation_id` fields to all six lifecycle audit-entry schemas and the
  `lifecycle-state-conflict` RFC 9457 problem-detail type → FR-059, pass-2 Q7
  [Contract, **P0**]
- [ ] CHK033 The pause/resume/abort handlers persist a durable lifecycle state document
  (Cosmos or equivalent) and gate every chat-turn / injection / sub-agent invocation on
  the read of that state; in-flight cascade work completes its current step but no new
  invocations or signal writes are issued while paused → FR-059 [Implementation, **P0**]
- [ ] CHK034 An integration test exercises the full round-trip
  `pause → replay-pause → resume → replay-pause → pause-with-new-key` and asserts each
  outcome (cached replay vs. 409 lifecycle-state-conflict vs. 200 with new cache entry)
  → FR-059, FR-066, pass-2 Q7 [Test, **P0**]

---

## Amendment G — FR-013 contradiction detector inputs (STRENGTHENED)

- [ ] CHK035 spec.md FR-013 mandates that the contradiction detector receives **recent
  signals within freshness windows** when invoked from any path; the injection route MUST
  load recent signals (Cosmos query within freshness window) and pass them to the handler;
  hardcoded `recent_signals=()` is PROHIBITED → FR-013 [Spec, **P0**]
- [ ] CHK036 The injection route loads recent signals from
  `simulation_synthetic_signals` filtered by `simulation_id` + `signal_category` + freshness
  window before invoking the contradiction handler; no `recent_signals=()` literal remains
  in the production call site → FR-013 [Implementation, **P1**]
- [ ] CHK037 A unit test asserts that the contradiction handler is invoked with a non-empty
  `recent_signals` argument when at least one in-window prior signal exists → FR-013
  [Test, **P1**]

---

## Amendment H — FR-027 layer taxonomy alignment (STRENGTHENED)

- [ ] CHK038 spec.md FR-027 mandates that the 16-layer taxonomy is a **single canonical
  enumeration** owned by `packages/domain` and shared between backend
  `map_overlay_publisher.py` LAYER_TYPES and the web SSE map-overlay event contract →
  FR-027, Amendment H [Spec, **P0**]
- [ ] CHK039 `packages/domain` exports the 16-layer enum as the single source of truth;
  backend `map_overlay_publisher.py` and `apps/web/src/lib/sse/map-overlay-events.ts` BOTH
  import from `packages/domain` (no local divergent string literals) → FR-027
  [Implementation, **P0**]
- [ ] CHK040 A contract test asserts byte-for-byte equality between the backend LAYER_TYPES
  emitted enum and the web layer enum; the test fails if either side adds, removes, or
  renames a layer type → FR-027 [Test, **P0**]

---

## Amendment I — FR-054 lessons capture content (STRENGTHENED)

- [ ] CHK041 spec.md FR-054 mandates that ExerciseOutcomeRecord includes all **six** named
  sections: (1) participant summary, (2) timeline, (3) sub-agent responses, (4) IC decisions,
  (5) identified gaps, (6) lessons-identified narrative → FR-054 [Spec, **P1**]
- [ ] CHK042 spec.md FR-054 mandates **deterministic ordering**: timestamp ascending, then
  `sequence_number` ascending → FR-054 [Spec, **P1**]
- [ ] CHK043 The lessons-capture writer populates section §2 (timeline) with signal
  injections + sub-agent invocations + lifecycle events; §3 (sub-agent responses) with
  attribution + correlation IDs; §4 (IC decisions) from lifecycle audit; §5 (identified
  gaps) from cascade refusals + degraded-mode entries; §6 (lessons-identified narrative)
  → FR-054 [Implementation, **P1**]
- [ ] CHK044 An integration test asserts that an aborted simulation produces an
  ExerciseOutcomeRecord with all six sections populated AND deterministically ordered
  across two replays of the same scenario seed (byte-identical output) → FR-054, FR-055
  [Test, **P1**]
- [ ] CHK045 The lessons-capture writer surfaces the resolved primary `aiims_function`
  (FR-061) alongside each sub-agent name in §4 IC decisions and §3 sub-agent responses
  → FR-054, FR-061 [Implementation, **P1**]

---

## Amendment J — FR-057 cascade thread-cap + affinity ladder (STRENGTHENED) + pass-2 Q8

- [ ] CHK046 spec.md FR-057 mandates that `cascade_orchestrator.fan_out` integrates
  `ThreadCapService.check_or_acquire()` BEFORE target dispatch and emits
  `cascade.degraded_to_annotation` when cap exceeded → FR-057, Amendment J [Spec, **P0**]
- [ ] CHK047 spec.md FR-057 mandates that the **5-step affinity ladder** runs when
  annotation degradation is selected, choosing which thread receives the annotation;
  selection is byte-identical across replays of the same scenario seed → FR-057
  [Spec, **P0**]
- [ ] CHK048 spec.md (pass-2 Q8) FR-052 mandates that the 5-thread cap counts **hazard
  threads only**: `simulation_state.active_hazard_threads` entries with
  `thread_kind = "hazard"` are summed against the cap of 5; `thread_kind = "annotation"`
  entries are unbounded and do NOT count → FR-052, FR-057, pass-2 Q8 [Spec, **P0**]
- [ ] CHK049 spec.md (pass-2 Q8) defines the cap-enforcement edge cases: 4 hazard + cascade
  → 5th hazard succeeds; 5 hazard + cascade → degrades to annotation on the affinity-
  selected thread; 6th cascade trigger while at 5 hazard → stacks chronologically as
  another annotation on the affinity-selected thread → FR-052, pass-2 Q8 [Spec, **P0**]
- [ ] CHK050 The cascade orchestrator calls `ThreadCapService.check_or_acquire()` before
  every target dispatch; on cap-exceedance it invokes the 5-step affinity ladder and emits
  the typed `cascade.degraded_to_annotation` audit entry with `affinity_step: 1..5` and
  the candidate set → FR-057 [Implementation, **P0**]
- [ ] CHK051 The thread-cap counter document uses the FR-048 distributed gap-free
  mechanism (ETag conditional replace) for cap-accounting concurrency safety → FR-052,
  FR-048, pass-2 Q8 [Implementation, **P0**]
- [ ] CHK052 An integration test reproduces the byte-identical affinity-ladder selection
  across two replays of the same scenario seed under cap-exceedance → FR-057, SC-011
  [Test, **P1**]

---

## Amendment K — FR-027 AWS-tier colours (STRENGTHENED)

- [ ] CHK053 spec.md FR-027 mandates AWS-tier visual rendering colours: **Advice = yellow**
  (AWS-standard hex), **Watch and Act = orange**, **Emergency Warning = red**, **Not
  Applicable = neutral grey** → FR-027, Amendment K (synthesis labelled "FR-040" in error,
  corrected to FR-027) [Spec, **P0**]
- [ ] CHK054 The web map component sets `"advice": "<AWS-yellow hex>"` (NOT `#22c55e`
  green) and the corresponding orange / red / grey hex values for the other three tiers →
  FR-027 [Implementation, **P0**]
- [ ] CHK055 A regression test asserts the rendered AWS-tier colour for all four tiers
  (Advice / Watch and Act / Emergency Warning / Not Applicable) on the wind-arrow,
  hazard-perimeter, evacuation-route, flood-polygon, and TC-track-and-cone overlay layers
  → FR-027 [Test, **P0**]

---

## Amendment L — FR-039 watermark locale coverage (STRENGTHENED)

- [ ] CHK056 spec.md FR-039 mandates the watermark text-translation table AND audio-prefix
  table cover **at minimum ~30 locales** including English + Mandarin + Arabic + Vietnamese
  + Cantonese + Italian + Greek + Tagalog + Hindi + Spanish + Punjabi + Korean + Persian +
  Tamil + Urdu (>0.5 % AU population speakers) → FR-039 [Spec, **P1**]
- [ ] CHK057 spec.md FR-039 mandates inclusion of NT/remote Aboriginal languages
  (**Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte**), **Kriol**, and **Torres Strait
  Creole** in both the text and audio translation tables → FR-039 [Spec, **P0**]
- [ ] CHK058 spec.md FR-039 mandates **jurisdiction language profiles** linking each
  jurisdiction (NSW, VIC, QLD, SA, WA, TAS, NT, ACT) to its priority locales → FR-039
  [Spec, **P1**]
- [ ] CHK059 `apps/api/app/config/watermark_text.yaml` (and the audio-prefix table) cover
  the ~30-locale spec target; backlog entries are tracked with explicit
  `staging_promotion_blocker: true|false` flags so non-blocker NT/Aboriginal locales do
  not accidentally block release → FR-039 [Operations, **P1**]

---

## Amendment M — FR-021 jurisdiction routing (STRENGTHENED)

- [ ] CHK060 spec.md FR-021 mandates jurisdiction routing via **jurisdiction × hazard ×
  agency tuples**, not category-only lookup → FR-021, Amendment M (synthesis labelled
  "FR-007" in error, corrected to FR-021) [Spec, **P0**]
- [ ] CHK061 spec.md FR-021 enumerates concrete blocking fixtures: **WA DFES** single-route
  for fire+SES; **QFD** (Queensland Fire Department, formerly QFES) naming; **CFA/FRV**
  split for VIC; **SA SACFS/SAMFS** split; **NT dual-fire** (NTFRS structural + Bushfires
  NT rural); **ACT ESA-first** with AFP/ACT-policing fallback → FR-021 [Spec, **P0**]
- [ ] CHK062 The jurisdiction-resolution module loads the tuple table from
  `packages/domain` (single source of truth) and applies it byte-deterministically; no
  agency name appears as a category-only string literal in the routing code → FR-021
  [Implementation, **P0**]
- [ ] CHK063 A test sweep covers each jurisdiction × hazard × agency tuple with a
  positive case (correct route) and a negative case (mis-jurisdiction or mis-hazard
  rejected with `routing.jurisdiction_ambiguous` audit) → FR-021 [Test, **P0**]

---

## Amendment N — Cascade matrix expansion

- [ ] CHK064 spec.md (Amendment N) AND `data-model.md` mandate cascade rules covering:
  **utility → {Health, Comms, Transport, Resource}**;
  **hydrology → {Risk, Evac, Comms, Resource}**;
  **transport → {Evac, Comms, Resource}**;
  **evacuation-centre → {Planning, Evac, Resource}**;
  **geohazard → {Risk, Evac, Resource}** → FR-043, FR-044, FR-047 [Spec, **P0**]
- [ ] CHK065 The cascade orchestrator's rule table contains all five expanded cascade
  rule sets with deterministic target ordering → FR-043, FR-044, FR-047
  [Implementation, **P0**]
- [ ] CHK066 An acceptance test proves routing for each of the five cascade rule sets
  (one positive case per cascade type) → FR-043, FR-044, FR-047 [Test, **P0**]
- [ ] CHK067 The cascade rule table is a closed-set enumeration in `packages/domain`
  consumed by both the orchestrator and the lessons-capture identified-gaps section →
  FR-054, Amendment N [Implementation, **P1**]

---

## Amendment O — FR-062 Foundry carve-out registry (NEW)

- [ ] CHK068 spec.md FR-062 mandates the registry schema fields **`tenant_id`** (or `*`
  with documented justification), **`model_deployment`**, **`carveout_reason`**,
  **`evidence_uri`**, **`expires_at`**, **`approver`** → FR-062 [Spec, **P0**]
- [ ] CHK069 `foundry_carveout_registry.json` (or equivalent path) exists with at least
  one valid entry corresponding to the Foundry deployment(s) referenced in code →
  FR-062 [Operations, **P0**]
- [ ] CHK070 A CI evaluation step runs on every PR that references a carved-out model
  deployment AND fails closed when: (a) the registry is empty (`[]`); (b) any entry has
  `expires_at` in the past; (c) a referenced deployment has no matching entry; (d) any
  required field is missing → FR-062 [Operations, **P0**]
- [ ] CHK071 The CI evaluation also fails when `foundry_carveout_registry.json` exists but
  is empty while a sub-agent references a Foundry deployment in code → FR-062
  [Operations, **P0**]
- [ ] CHK072 Constitution v1.2.0 Non-Negotiable #2 traceability is preserved: every
  registry entry's `carveout_reason` references the specific Constitution Principle
  (typically II / III) and its operational driver → FR-062 [Spec, **P0**]

---

## Amendment P — FR-063 SLI E2E staging promotion gate (NEW)

- [ ] CHK073 spec.md FR-063 enumerates the **five plan-canonical SLIs**: (1) P95
  inject→fan-out latency; (2) P99 audit gap-free invariant (0 sequence-number gaps); (3)
  throughput at 200 concurrent injections; (4) error budget on map-overlay drift across
  the 16-layer taxonomy; (5) P95 sub-agent reply latency → FR-063 [Spec, **P0**]
- [ ] CHK074 spec.md FR-063 mandates that **promotion to production is refused** (CI gate
  or runbook gate) if any SLI lacks fresh staging evidence or fails its threshold →
  FR-063 [Spec, **P0**]
- [ ] CHK075 An E2E test exists for **each** of the five SLIs and runs in the staging
  environment as part of every release-promotion sequence → FR-063 [Test, **P0**]
- [ ] CHK076 The CI/CD pipeline gates production promotion on the green E2E result for all
  five SLIs from the immediately preceding staging run → FR-063 [Operations, **P0**]
- [ ] CHK077 SLI threshold values are set in `plan.md` (deferred from spec phase per
  FR-063 hand-off) and consumed by the E2E tests via a single config source →
  FR-063 [Operations, **P1**]
- [ ] CHK078 Staging-promotion evidence is auditable: a runbook entry or CI artefact
  records the run timestamp, commit SHA, SLI name, observed value, threshold, and
  pass/fail outcome for each of the five SLIs → FR-063 [Operations, **P1**]

---

## Amendment Q — FR-064 accessible live-log (NEW) + pass-2 Q6

- [ ] CHK079 spec.md FR-064 mandates a dedicated accessible live region for SSE/streaming
  chat updates with **`role="log"`**, **`aria-live="polite"`**, and an explicit
  `aria-label` (e.g. `aria-label="Simulation chat log"`) → FR-064 [Spec, **P0**]
- [ ] CHK080 spec.md FR-064 mandates that the live region is **separate from** (and not
  substituted by) the Disaster Map a11y digest; both surfaces MUST be present
  simultaneously → FR-064 [Spec, **P0**]
- [ ] CHK081 spec.md (pass-2 Q6) FR-064 mandates that the live-log consumes the
  **shared** `packages/domain/src/domain/sim_locale_table.json` source of truth used by
  FR-058, with the **3-step locale-resolution fallback**
  `request_locale → jurisdiction_priority_locale → en_AU` → FR-064, FR-058, pass-2 Q6
  [Spec, **P0**]
- [ ] CHK082 spec.md (pass-2 Q6) mandates that every chat-receipt event in the live region
  emits (or contributes to) an `audit.watermark.applied` audit entry recording
  **`delivery_channel`** ∈ `{audio | text-live-log | both}` AND **`resolved_locale`**;
  when the same chat turn produces both screen-reader live-log AND TTS audio, a single
  audit-watermark-applied correlation MUST record `delivery_channel: "both"` → FR-064,
  FR-058, pass-2 Q6 [Spec, **P0**]
- [ ] CHK083 `contracts/audit-envelope.md` registers the `audit.watermark.applied` schema
  with the `delivery_channel` enum and the `resolved_locale` field → FR-064,
  pass-2 Q6 [Contract, **P0**]
- [ ] CHK084 An axe-core (or equivalent) accessibility regression test asserts the live
  region exists with the correct ARIA roles and labels on every render of the simulation
  page; the test fails if the live region is missing, mis-labelled, or replaced by the
  map digest as the sole accessible surface → FR-064 [Test, **P0**]
- [ ] CHK085 A vitest suite asserts that the live-log text rendering at SSE-event-receipt
  time contains the `[SIMULATION]` prefix and the locale-resolution fallback follows
  the 3-step rule (test fails if the fallback is inverted) → FR-064 [Test, **P0**]

---

## Amendment R — FR-065 prompt_hash on every path (NEW) + pass-1 Q5

- [ ] CHK086 spec.md FR-065 mandates that every Telemetry-Injection audit entry —
  `injection.accepted`, `injection.refused` (any reason), and `injection.fallback` —
  persists a `prompt_hash` field; recording `prompt_hash` only on accepted injections
  with `null` on refused/fallback paths is non-compliant → FR-065 [Spec, **P0**]
- [ ] CHK087 spec.md (pass-1 Q5) FR-065 adds the sibling **`prompt_hash_source`** enum
  field (REQUIRED whenever `prompt_hash` is present) with values
  **`"raw_user_input"`** | **`"canonical_llm_prompt"`** | **`"system_only"`** and
  documents the byte-source rule for each value → FR-065, pass-1 Q5 [Spec, **P0**]
- [ ] CHK088 spec.md (pass-1 Q5) mandates that `contracts/audit-envelope.md` adds
  `prompt_hash_source` to **all 24 typed audit entries** that may carry `prompt_hash`
  → FR-065, pass-1 Q5 [Contract, **P0**]
- [ ] CHK089 The audit writer populates `prompt_hash` AND `prompt_hash_source` on every
  injection path (accepted, refused on each enumerated reason, fallback, system-driven
  cascade) per the byte-source rules: `raw_user_input` for pre-LLM refusals;
  `canonical_llm_prompt` for post-LLM paths; `system_only` for paths with no user prompt
  → FR-065, pass-1 Q5 [Implementation, **P0**]
- [ ] CHK090 A unit test sweeps each refusal reason (`life_safety_low_confidence`,
  unknown-category, missing-provenance, `thread.cap_exceeded`, malformed input,
  idempotency conflict, RBAC failure) and asserts the audit entry carries the correct
  `prompt_hash_source` enum value → FR-065, pass-1 Q5 [Test, **P0**]
- [ ] CHK091 The FR-049 audit-export and FR-054 lessons-capture writers expose
  `prompt_hash` + `prompt_hash_source` to §3 sub-agent responses and §5 identified gaps
  for forensic replay verification → FR-065, FR-054 [Implementation, **P1**]

---

## Amendment S — FR-066 direct REST idempotency (NEW) + pass-1 Q2 + pass-1 Q3

- [ ] CHK092 spec.md FR-066 mandates that all four direct REST lifecycle endpoints
  (`inject-telemetry`, `pause`, `resume`, `abort`) honour the `Idempotency-Key` header
  with a **24-hour replay window**; replays return the original cached response without
  re-executing side effects → FR-066 [Spec, **P0**]
- [ ] CHK093 spec.md (pass-1 Q3) FR-066 mandates that the idempotency uniqueness scope
  is the **`(simulation_id, HTTP verb, route)` tuple** (NOT
  `(simulation_id, idempotency_key)` alone); the same key on `POST /pause` and
  `POST /abort` for the same `sim_id` occupy **different namespaces** and both succeed
  independently → FR-066, pass-1 Q3 [Spec, **P0**]
- [ ] CHK094 spec.md (pass-1 Q3) FR-066 mandates **conflict detection**: same key + same
  verb + same `sim_id` within 24 h with a DIFFERENT canonical-body sha256 returns
  **HTTP 422 Unprocessable Entity** with an **RFC 9457 problem detail** of
  `type: "idempotency-key-conflict"` → FR-066, pass-1 Q3 [Spec, **P0**]
- [ ] CHK095 spec.md (pass-1 Q2) FR-066 mandates **503 caching**: the 24-h replay window
  INCLUDES entries whose cached response is a 503 from sequence-uncertainty fail-closed;
  replay returns the cached 503 unchanged WITHOUT re-attempting the underlying Cosmos
  operation; the companion `audit.sequence.uncertainty` DLQ entry MUST be written
  **exactly once** per original request (no duplicate DLQ write on replay) → FR-066,
  FR-048, pass-1 Q2 [Spec, **P0**]
- [ ] CHK096 spec.md FR-066 mandates **tenant scoping**: the Idempotency-Key persistence
  store is tenant-scoped — a key from one simulation tenant MUST NOT match a request from
  another → FR-066 [Spec, **P0**]
- [ ] CHK097 The Cosmos `simulation_idempotency_cache` container exists, partitioned by
  `simulation_id`, with TTL of 24 h anchored on the original request timestamp (not on
  sim end), storing
  `{key, verb, route, body_hash, response_status, response_body, created_at}` → FR-066
  [Implementation, **P0**]
- [ ] CHK098 An integration test asserts that the same `Idempotency-Key` value used on
  `POST /pause` and `POST /abort` for the same `sim_id` produces two separate cache
  entries and two distinct successful responses (verifies per-verb namespace) →
  FR-066, pass-1 Q3 [Test, **P0**]
- [ ] CHK099 An integration test asserts that a same-key + same-verb + DIFFERENT-body
  request returns HTTP 422 with the RFC 9457 `idempotency-key-conflict` problem detail
  → FR-066, pass-1 Q3 [Test, **P0**]

---

## Q→A traceability matrix (cross-reference)

- [ ] CHK100 Each of the eight new clarification answers (pass-1 Q1–Q5 + pass-2 Q6–Q8)
  has at least **one** P0 checklist item in this file that asserts the answer is
  preserved in spec / contract / implementation / test surface, traced as:
  Q1 → CHK009..CHK015; Q2 → CHK017..CHK022, CHK095; Q3 → CHK024, CHK092..CHK099;
  Q4 → CHK002..CHK005; Q5 → CHK087..CHK091; Q6 → CHK081..CHK085;
  Q7 → CHK030..CHK034; Q8 → CHK048..CHK052 → all eight Q→A entries
  [Spec, **P1**]

---

## Notes

**What this checklist covers**: every item that must hold true for the 19 amendments
(A–S) introduced by the Step 8 cross-cohort re-loop and the 8 new Q→A entries (pass 1
Q1–Q5 + pass 2 Q6–Q8). Items are categorised so that `speckit.plan` (Spec / Contract
items), `speckit.tasks` (Implementation / Test / Operations items), and the
release-promotion runbook (Operations items) can each consume the relevant slice.

**What this checklist does NOT cover**:

- Pre-amendment baseline FR coverage — covered by `requirements.md` and the four
  domain-specific checklists (`safety-and-life-primacy.md`, `audit-and-provenance.md`,
  `accessibility-and-cald.md`, `graceful-degradation.md`,
  `integration-and-test-coverage.md`).
- Implementation-only items I1–I7 from the synthesis (refactor refusals, freshness
  windows, guard wrappers, etc.) — those become tasks in `tasks.md`, not checklist items.
- Plan-phase trade-off resolution (e.g., choice between Cosmos ETag conditional replace
  vs. stored procedure for FR-048; exact `Idempotency-Key` storage for FR-066) — those
  are owned by `speckit.plan` and recorded as ADRs.

**Severity totals**: **P0 = 83** · **P1 = 17** · **P2 = 0** · **Total = 100**.

**Category totals**: **Spec = 47** · **Contract = 6** · **Implementation = 22** ·
**Test = 18** · **Operations = 7** · **Total = 100**. (Each item carries exactly one
primary category in its `[…]` tag.)

**Suggested next step**: Run `/speckit.plan` to update `plan.md`, `research.md`,
`data-model.md`, and ADRs for the amendment scope (FR-061 → FR-066 + 12 strengthened
FRs + 8 new Q→A entries). After plan update, run `/speckit.tasks` to regenerate
`tasks.md` for the amendment scope plus implementation-only items I1–I7. After tasks
update, run `/speckit.analyze` until 🟢 GREEN. Only then proceed to `/speckit.implement`.

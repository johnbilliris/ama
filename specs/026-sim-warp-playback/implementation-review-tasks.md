# Spec 026 Implementation Audit: Simulation Time Warp & Playback

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 026 only. Three parallel technical reviews examined scheduler
delivery, playback authorization/cursors, and event-clock persistence. The source-completable degraded-recording gap
was corrected: a durable playback snapshot write failure now marks the tenant's recorder unhealthy instead of being
logged while leaving health green. This preserves simulation continuity but exposes incomplete scrub fidelity.

Validation: `python -m pytest tests/unit/test_event_recorder.py -q` returned `8 passed`.

Remaining open work includes live scheduler/seed wiring, pause/resume and speed-boundary delivery, participant-scoped
playback, cursor/scrub semantics, annotation ownership, deletion retention, durable ordering/deduplication, performance,
and human playback-value evidence.

## Review Metadata and Limits

- Review date: 2026-09-14.
- Expected and verified Git HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- HEAD was reverified at closure. Read-only, no-optional-locks Git metadata reported zero tracked
  differences from HEAD under apps, packages, infra, scripts, tests, .github, spec 026, azure.yaml and
  pyproject.toml. This is not a claim that unrelated audit artifacts elsewhere were unchanged.
- Scope: spec 026 only, fresh stand-alone review authorized by the user; no delegation.
- Sole writable artifact: this report. No source, original task, checklist, evidence, index, branch, or commit changes.
- Static source and test-assertion inspection only. No tests, builds, imports, runtime/debug execution,
  browsers, servers, cloud queries, deployments, installation, or external approval requests.
- Validation is limited to report text integrity and editor diagnostics. `IMPLEMENTED` means supported
  by inspected source, not demonstrated execution. Performance, deployed state, and human outcomes
  remain `UNVERIFIED` without qualifying evidence.
- Binding contract: [audit contract](../001-spec-implementation-audit/README.md#L11), limited to lines 1-59;
  [code-review instructions](../../.github/instructions/code-review.instructions.md#L1).
- No existing spec-026 report was present. No other implementation-review-tasks report was read.
- Review conclusion: **not implementation-complete**. Clock arithmetic, speed validation and basic
  author/controller denial are supported, but live scheduled delivery, durable recording, faithful
  state replay and lifecycle boundaries have material gaps. Original task checkboxes are not evidence
  either for or against implementation.
- Coverage: **57 original tasks, 19 functional requirements plus 6 success criteria, 22 acceptance
  scenarios, 16 original checklist items, and 24 unique unchecked follow-ups**.
- Original-task dispositions: **10 IMPLEMENTED, 33 PARTIAL, 5 MISSING, 4 CONFLICT, 5 UNVERIFIED**;
  none are SUPERSEDED. Follow-up IDs are stable; their display order follows priority, not numeric order.

## Inputs Inspected

- [spec.md](spec.md#L1), including clarifications, user scenarios, requirements, success criteria,
  assumptions, personas, hypotheses, and scope amendments.
- [tasks.md](tasks.md#L1), including suffix task T001a, checkpoints, validation requests, and dependencies.
- [plan.md](plan.md#L1), [research.md](research.md#L1), [data-model.md](data-model.md#L1),
  [API contracts](contracts/api-contracts.md#L1), [quickstart.md](quickstart.md#L1), and the complete
  [requirements checklist](checklists/requirements.md#L1).
- [scheduler implementation](../../apps/api/app/services/warp_scheduler.py#L1).
- [scheduler unit tests](../../tests/unit/test_warp_scheduler.py#L1).
- [simulation routes](../../apps/api/app/api/routes/simulations.py#L1),
  [lifecycle service](../../apps/api/app/services/simulation_service.py#L1),
  [scenario seeder](../../apps/api/app/services/scenario_seeding_service.py#L1),
  [event repository](../../apps/api/app/repositories/simulation_event_repository.py#L1),
  [event recorder](../../apps/api/app/services/simulation_event_recorder.py#L1),
  [recorder tests](../../tests/unit/test_event_recorder.py#L1),
  [clock service](../../apps/api/app/services/simulation_clock_service.py#L1), and
  [clock tests](../../tests/unit/test_simulation_clock.py#L1).
- Domain/alternate-path inputs: [warp constants](../../packages/domain/src/domain/models/warp_constants.py#L1),
  [speed history model](../../packages/domain/src/domain/models/warp_speed_change.py#L1),
  [event/snapshot/cursor models](../../packages/domain/src/domain/models/simulation_event.py#L1),
  [tenant model](../../packages/domain/src/domain/models/simulation_tenant.py#L1),
  [tenant repository](../../apps/api/app/repositories/simulation_repository.py#L1),
  [signal repository](../../apps/api/app/repositories/signal_repository.py#L1),
  [signal read route](../../apps/api/app/api/routes/signals.py#L28),
  [simulation validators](../../apps/api/app/validators/simulation_validators.py#L1),
  [template model](../../packages/domain/src/domain/models/scenario_template.py#L1),
  [Run model](../../packages/domain/src/domain/models/simulation_run.py#L1),
  [Scenario model](../../packages/domain/src/domain/models/simulation_scenario.py#L1),
  [older ingestion runner](../../apps/ingestion/simulation/simulation_runner.py#L1), and
  [legacy backfill](../../scripts/backfill_simulation_elapsed.py#L1).
- Playback/auth inputs: [playback service](../../apps/api/app/services/playback_service.py#L1),
  [annotation service](../../apps/api/app/services/annotation_service.py#L1),
  [playback routes](../../apps/api/app/api/routes/simulation_playback.py#L1),
  [chat route wiring](../../apps/api/app/api/routes/simulation_chat.py#L1),
  [controller persistence](../../apps/api/app/services/simulation/controller_service.py#L223),
  [controller tool/ingestion path](../../apps/api/app/services/simulation/controller_service.py#L927),
  [RBAC dependency](../../apps/api/app/api/dependencies/rbac.py#L1),
  [tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L1),
  [RBAC middleware](../../apps/api/app/middleware/rbac_check.py#L1),
  [router registration](../../apps/api/app/api/router.py#L68), and
  [middleware registration](../../apps/api/app/main.py#L47).
  The neighboring [UUID injection handler](../../apps/api/app/api/routes/simulations_036.py#L171)
  and [UUID pause/resume handlers](../../apps/api/app/api/routes/simulations_036.py#L588) were inspected
  only to rule out a relocated owner for this tenant-based lifecycle, not to audit spec 036.
- UI inputs: [creation page](../../apps/web/src/app/simulations/create/page.tsx#L1),
  [list page](../../apps/web/src/app/simulations/page.tsx#L1),
  [dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L1),
  [player page](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L1),
  [live clock](../../apps/web/src/components/simulation-server-clock.tsx#L1),
  [warp control](../../apps/web/src/components/simulation-warp-controls.tsx#L1),
  [timeline](../../apps/web/src/components/playback-timeline.tsx#L1),
  [playback controls](../../apps/web/src/components/playback-controls.tsx#L1),
  [annotation panel](../../apps/web/src/components/playback-annotation-panel.tsx#L1),
  [simulation client](../../apps/web/src/lib/api/simulations.ts#L1), and
  [playback client](../../apps/web/src/lib/api/simulation-playback.ts#L1).
- Test/discovery inputs: the three complete unit modules above, complete
  [warp API tests](../../tests/contract/test_warp_speed_api.py#L1),
  [combined playback/annotation tests](../../tests/contract/test_playback_api.py#L1),
  [controller wiring test](../../apps/api/tests/test_simulation_chat_controller_wiring.py#L1),
  [similarly named evaluator test](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L1),
  [pytest path fixture](../../tests/conftest.py#L1), [pytest metadata](../../pyproject.toml#L43),
  [web package](../../apps/web/package.json#L1), [Vitest config](../../apps/web/vitest.config.ts#L1),
  [Playwright config](../../apps/web/playwright.config.cts#L1),
  [CI selection](../../.github/workflows/ci.yml#L131), and
  [coverage helper](../../scripts/coverage-ratchet.ps1#L1).
- Infrastructure/evidence inputs: [azd configuration](../../azure.yaml#L1),
  [active container/module declarations](../../infra/main.bicep#L577),
  [alternate container definition](../../infra/bicep/main.bicep#L158),
  [Bicep standards](../../.github/instructions/bicep-code-best-practices.instructions.md#L1),
  [policy-compliance instructions](../../.github/instructions/bicep-policy-compliance.instructions.md#L1),
  complete [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1),
  [evidence-stub contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1), and
  [persona-profile contract](../027-spec-hardening/contracts/persona-profile.md#L1).
  The complete [meta-spec contract](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L1)
  was also read for SCP-081.
- Loaded installed Python fact-grounded-coding and Cosmos DB best-practices skills. Used only their
  static-evidence guidance; did not inspect interpreter state, run SDKs or query services.

The eight local input documents were read completely. Source inspection followed the listed owning
paths; referenced external evidence was inspected only for this specification's obligations. Searches
for the claimed HYP stub and domain aggregate export found no artifact; those nonexistent paths are
described as proposed/missing below and are not linked as evidence.

## Findings and Remediation

### P1: Live Seeding Bypasses the Warp Scheduler

- [ ] AUD-026-001 Connect scheduled delivery to the live seed and resume paths

  **Obligations:** FR-004/005/007, US1/US2/US4 timing scenarios, T012-T019, SC-001/002.
  **Expected / observed / impact:** The seed operation must schedule future signals against canonical
  simulated time. Instead, [seed_from_template](../../apps/api/app/services/scenario_seeding_service.py#L30)
  calls `create_signal` for every entry before initializing the cursor. `replay_realtime` still sleeps
  each absolute offset sequentially. The routes construct a scheduler but never start its delivery
  loop; pause/resume only update the tenant clock. Future scenario data is written immediately, and
  the intended paced delivery is not connected to the user workflow.
  [Tenant signal reads](../../apps/api/app/repositories/signal_repository.py#L75) have no due-time
  filter. The general [signals route](../../apps/api/app/api/routes/signals.py#L28) reads a separate
  SIGNALS store, not this repository or scheduler. Immediate writes are therefore not evidence of a
  correctly timed participant-visible feed; the write-to-read integration also needs explicit assertions.
  The alternate [chat seed path](../../apps/api/app/services/simulation/controller_service.py#L990)
  starts `_ingest_synthetic_signals`, which only increments a counter every two wall-clock seconds
  (even while Paused), without delivering or recording a signal.
  **Search / owner:** Inspected the complete seeder, simulation routes, lifecycle service, and scheduler;
  searched API Python sources plus agents, ingestion/evaluation runners, scripts, and tools for
  `WarpScheduler`, `run_delivery_loop`, and `load_timeline`. Only API construction and scheduler
  definitions were found, not a production loop caller.
  **Developer:** Stage envelopes separately from visible signals; start delivery through an owned worker;
  connect pause/resume, speed updates, and archive cancellation. Pass the template store dependency to
  the seeder: the current route factory does not supply its `cosmos_client`, so `_load_template` returns
  `None` through that construction path. Connect due delivery to the actual participant read surface,
  preserving tenant scoping, canonical envelope/partition fields and the 1x default; do not substitute counters.
  **Compatibility / dependencies:** Depends on AUD-026-002 for recovery and idempotence; do not publish
  staged envelopes early or re-seed delivered entries when resuming.
  **Tester:** Extend [scheduler tests](../../tests/unit/test_warp_scheduler.py#L1) and
  [warp API tests](../../tests/contract/test_warp_speed_api.py#L1); proposed new test home:
  `tests/integration/test_warp_simulation_lifecycle.py`. Use template offsets [0,300,600,3600] at 10x;
  assert visible IDs exactly at wall offsets [0,30,60,360], none early, stable order, pause freezes
  cursor/time, resume delivers each ID once, and 1x is the identity schedule. Cover missing template,
  equal offsets, empty timeline, and archive with pending entries.
  **Future validation:** With dependencies installed and isolated test repositories, run
  `python -m pytest tests/unit/test_warp_scheduler.py tests/contract/test_warp_speed_api.py -q`, then
  the proposed lifecycle test after authoring it. Expected: real seed/lifecycle wiring is exercised,
  every timing/cursor assertion passes, and no mocks bypass delivery ownership.
  **Complete when:** The reachable user workflow meets the assertions above and its worker lifecycle
  is documented; performance results remain a separate evidence obligation.

### P1: Cursor Storage Alone Does Not Provide Restart or Multi-Worker Safety

- [ ] AUD-026-002 Persist scheduler recovery state and enforce idempotent single-owner delivery

  **Obligations:** Research R1/R6, T012(9)/T014, FR-004/005/007, US2-AS3 and SC-002.
  **Expected / observed / impact:** [WarpScheduler](../../apps/api/app/services/warp_scheduler.py#L45)
  keeps timelines only in `_timelines`, overwrites initial ownership unconditionally, never checks
  the recorded owner or the declared 30-second stale lease, and writes a signal before saving its
  cursor. A replacement instance has no timeline; concurrent workers or a failure between delivery
  and cursor persistence can repeat work. The existing persistence test reads the same objects and
  does not establish recovery.
  **Search / owner:** Same bounded scheduler-call search as AUD-026-001, plus the complete event
  repository's scheduler-state methods; no alternate ownership/recovery implementation found there.
  **Developer:** Persist ordered timeline references, claim/renew a conditional tenant lease, fence stale
  workers, and use stable delivery identities with retry-safe acknowledgement. Define and serialize
  the due-signal/speed-change boundary so a signal already due uses the old speed. Reload cursor and
  timeline after worker replacement; do not reset either on resume. Renew heartbeat while waiting for
  future offsets, not only after due deliveries: the current positive-delay branch continues before renewal.
  **Compatibility / dependencies:** Integrate with AUD-026-001. Resolve the data model's `simulation`
  container versus current `sim-events` cursor storage explicitly before changing persisted documents.
  **Tester:** Extend [scheduler tests](../../tests/unit/test_warp_scheduler.py#L1) using two scheduler
  instances sharing a persistent fake, injected clock, and crash points before/after signal write.
  Assert one owner, failover after stale lease, no repeat visible IDs, cursor resumes at the next
  undelivered signal, stable equal-offset ordering, deterministic delivery at a speed-change boundary,
  and continued ownership/heartbeat during a sparse interval longer than 30 seconds.
  **Future validation:** After installing repository test dependencies, run
  `python -m pytest tests/unit/test_warp_scheduler.py -q`; add isolated durable-store integration tests
  before claiming restart safety. Expected: repeated/restarted/concurrent drains yield identical IDs
  and order, with no gaps or duplicates.
  **Complete when:** Recovery and concurrency paths have executable assertions, not merely cursor reads
  from one in-memory object. No runtime result is claimed by this audit.

### P1: Persistence Failures Are Hidden from Recording Health

- [ ] AUD-026-003 Propagate durable recording failures and persist partial playback health

  **Obligations:** FR-010a, SC-003, T005/T008/T010 and the graceful-degradation gate.
  **Expected / observed / impact:** The [event repository](../../apps/api/app/repositories/simulation_event_repository.py#L107)
  catches failed writes, caches in memory, and returns the event. The recorder treats that return as
  healthy; its failure counter cannot observe the caught storage failure. The inspected lifecycle
  creates tenants with `playback_status="full"` and does not persist recorder health. A storage outage
  can therefore leave an apparently complete recording that is lost on restart or absent from reads.
  **Search / owner:** Full repository, recorder, simulation service and route construction inspected.
  The [failure test](../../tests/unit/test_event_recorder.py#L84) replaces `append_event` itself with
  a raising function, skipping the real catch-and-success behavior.
  **Developer:** Separate explicit test-memory mode from durable-write failure; propagate a typed
  persistence outcome to the recorder, latch partial status after known loss, record bounded gap
  metadata, and expose a controller warning. Preserve training continuity and do not restore `full`
  merely because a subsequent event succeeds. Isolate recording failures from signal delivery.
  **Compatibility / dependencies:** Preserve `full/partial/none` API values and legacy empty playback.
  Gap metadata must be consumed by the playback UI; snapshot failure is not successful state capture.
  **Tester:** Extend [recorder tests](../../tests/unit/test_event_recorder.py#L1) with a fake Cosmos
  container that fails `upsert_item`, then recovers. Assert the simulation continues, durable status
  becomes/stays partial, other tenants are unaffected, available records survive a bad row, and the
  controller/reviewer sees the gap. Do not replace the repository method under examination.
  **Future validation:** With isolated repositories and dependencies present, run
  `python -m pytest tests/unit/test_event_recorder.py tests/contract/test_playback_api.py -q`.
  Expected: actual storage-boundary failures exercise health propagation without stopping training.
  **Complete when:** Durable health and visible gaps agree with failure/recovery assertions; a log
  message or process-local health dictionary alone is insufficient.

### P1: Recorded Chat Times and Event Scope Do Not Match the Canonical Timeline

- [ ] AUD-026-004 Record decision events at their real simulated offsets and exclude UI navigation

  **Obligations:** FR-010, clarifications on event scope/chat independence, SC-003, T008/T034/T043.
  **Expected / observed / impact:** Chat turns must be captured once on completion with canonical
  offsets, independent of warp pacing. The [controller](../../apps/api/app/services/simulation/controller_service.py#L223)
  defaults `_persist_turn(sim_seconds=0.0)` and its user/assistant/tool-turn callers omit the value.
  Tool-role turns are mapped to assistant events by the recorder. The
  [dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L113) persists a page-load log, and
  [log-entry handling](../../apps/api/app/api/routes/simulation_playback.py#L100) assigns zero when
  the client omits an offset. The timeline therefore misplaces real decisions and includes explicitly
  excluded UI navigation. Signal recording is in the disconnected scheduler, not the signal write boundary.
  **Search / owner:** Inspected controller persistence and both backends, simulation chat route wiring,
  recorder helpers, seeder, SignalRepository, and dashboard log entry path; searched API Python sources
  for recorder construction, event writes, and convenience-helper calls.
  **Developer:** Stamp each completed turn at the server clock lookup, preserve user/assistant/tool
  identities, capture actual tool outcome/latency and linkage, and record required signal/alert/state
  decisions at their owning writes. Do not use UI logs as a substitute. Exclude page-load interactions;
  retain any explicitly supported decision-log extension with versioned payloads. Preserve normal chat pace.
  **Compatibility / dependencies:** Coordinate with AUD-026-001/003 and the state reducer in AUD-026-005;
  keep source references or sufficient payloads for reconstructing the decisions, not just labels.
  **Tester:** Extend [recorder tests](../../tests/unit/test_event_recorder.py#L1) and
  [playback contract tests](../../tests/contract/test_playback_api.py#L1); proposed new integration home:
  `tests/integration/test_playback_events.py`. With a controlled clock at nonzero time, emit a complete
  user/assistant exchange, tool success/error/timeout, signal, alert and lifecycle changes. Assert exact
  event types/counts, nonzero offsets, stable equal-time order, one completed turn not per SSE token,
  correct tool linkage, and no page-view event. Assert chat latency is not multiplied by warp speed.
  **Future validation:** After dependencies and isolated/offline service doubles are available, run
  `python -m pytest tests/unit/test_event_recorder.py tests/contract/test_playback_api.py -q`, then
  the proposed recording round-trip suite. Expected: event records match the actual write-boundary sequence.
  **Complete when:** Every required decision category has reachable capture and end-to-end assertions,
  with no fabricated zero timestamp when a canonical clock is available.

### P1: Scrubbing Does Not Reconstruct Simulation State

- [ ] AUD-026-005 Build complete snapshots and replay state from the nearest snapshot

  **Obligations:** FR-011/013, US3-AS3/5, SC-004, data-model snapshot state, R4, T008/T034/T039/T041.
  **Expected / observed / impact:** A scrub must show active signals, alert statuses, speed, and metrics
  at the selected offset. [Snapshot creation](../../apps/api/app/services/simulation_event_recorder.py#L211)
  stores only the last event type/payload. The [playback page](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L82)
  filters events by time, never calls the snapshot API, and renders only event metadata, not reconstructed
  state or decision contents. A reviewer cannot inspect the required historical state.
  **Search / owner:** Complete recorder, snapshot repository/service/routes, playback API client, page,
  timeline, controls and annotation panel inspected; the client's snapshot helper is not imported by
  the player. This is not a missing-filename claim about the planned `PlaybackPlayer` abstraction.
  **Developer:** Define a versioned deterministic event reducer, materialize complete snapshots at the
  required count/time thresholds, fetch the nearest snapshot, then apply subsequent events through the
  target offset. Render state and relevant payloads; retain stable ordering at equal offsets and handle
  missing/corrupt records with the gaps from AUD-026-003. Preserve independent per-reviewer positions.
  **Compatibility / dependencies:** Requires accurate events from AUD-026-004 and reliable cursors from
  AUD-026-006. Retain compatibility with historical snapshot/event schema versions and no-snapshot runs.
  **Tester:** Extend [playback contracts](../../tests/contract/test_playback_api.py#L1); proposed new
  unit home: `tests/unit/test_playback_service.py`. Use a known event stream and snapshots bracketing
  targets. Assert the nearest snapshot is at/before target; exact active signal IDs, alert status,
  warp speed and accumulated metrics match a full replay; future events are absent. Cover backward
  scrub, equal-time events, empty/partial history and malformed rows.
  **Future validation:** With dependencies installed and the proposed service tests authored, run
  `python -m pytest tests/unit/test_playback_service.py tests/contract/test_playback_api.py -q`.
  Add player assertions under proposed `apps/web/tests/unit/spec_026/playback.test.tsx` and run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026`. Measure SC-004 separately with a
  representative low-thousands-event fixture;
  expected exact state equality plus reconstruction under three seconds, not just a visible slider.
  **Complete when:** Snapshot-assisted and full replay yield the same state for every tested position,
  and a separately recorded performance result supports the latency claim.

### P1: Pagination Stops Early When Event Sequences Have Gaps

- [ ] AUD-026-006 Paginate events independently of row count

  **Obligations:** FR-009/017, SC-003/006, T005/T032/T035/T038/T048 and cursor-based playback retrieval.
  **Expected / observed / impact:** The [playback service](../../apps/api/app/services/playback_service.py#L58)
  sets `has_more` by comparing the last sequence with total row count. For sequences [1,3,4] and limit
  2, it ends at 3 and omits 4. Annotation deletion is a supported operation, so contiguous sequences
  cannot be assumed even after allocation is fixed. Valid remaining events/notes can disappear from playback.
  **Search / owner:** Full sequence, event query/delete, annotation CRUD, playback pagination and
  `getAllPlaybackEvents` paths inspected. Existing cursor tests only request `after_seq` once and
  do not assert continuation across gaps, deletion or concurrent writes.
  **Developer:** Fetch one extra matching record or use a validated continuation
  token to determine `has_more`. Apply the same annotation filter to continuation semantics; validate
  nonnegative cursors and page size 1..1000. Keep annotations anchored by simulated time, not append order.
  **Compatibility / dependencies:** Preserve public cursor compatibility or explicitly version it;
  support pre-existing gapped/duplicate histories without silently dropping records. Integrates with
  AUD-026-023 for monotonic allocation, but gaps from deletion must remain supported independently.
  **Tester:** Extend [playback contracts](../../tests/contract/test_playback_api.py#L1) with sequences
  [1,3,4], small pages, deleted middle/tail annotations and filtered annotation pages.
  Assert concatenated pages equal all expected IDs exactly once; continuation is present until the
  last matching row. Invalid
  limits/cursors must fail validation, not become arbitrary slices or false empty pages.
  **Future validation:** With deterministic repository fixtures, run
  `python -m pytest tests/contract/test_playback_api.py tests/unit/test_event_recorder.py -q`.
  Expected: no loss, duplication or premature termination across deletion/filter cases.
  **Complete when:** All matching events are returned without assuming contiguous event numbers.

### P1: Sequence Allocation Reuses IDs and Is Not Safe Across Writers

- [ ] AUD-026-023 Allocate durable monotonic event sequences independently of current event count

  **Obligations:** R3/R7, SimulationEvent monotonic sequence, SC-003/006, T005/T008/T045.
  **Expected / observed / impact:** [next_sequence](../../apps/api/app/repositories/simulation_event_repository.py#L81)
  returns len(events)+1 in memory and queries MAX+1 in Cosmos. With sequences [1,2,3], deleting 2 makes
  the next allocation 3 again. Separate Cosmos writers can observe the same maximum and allocate the
  same next value; deleting the latest event can also reuse its number. Cursor readers then cannot
  unambiguously include every new event/annotation.
  **Search / owner:** Complete repository allocation/append/delete and recorder/annotation producers
  inspected; no persisted atomic counter or unique sequence claim appears on these paths. Existing
  recorder tests only allocate consecutive events without deletion or parallel producers.
  **Developer:** Allocate a never-reused sequence through a durable tenant-scoped counter/conditional
  claim or transactional write. Treat allocation/storage failure honestly, preserve stable order for
  equal simulated offsets, and define handling for legacy duplicate sequence rows. Do not solve it by
  reordering/renumbering recorded events or assuming a single process in a multi-replica deployment.
  **Compatibility / dependencies:** Coordinate with AUD-026-002/003 and preserve cursor semantics from
  AUD-026-006. Sequence gaps are allowed; duplicate/reused sequence values are not.
  **Tester:** Extend [recorder tests](../../tests/unit/test_event_recorder.py#L21) and
  [annotation contract tests](../../tests/contract/test_playback_api.py#L293) using shared persistent
  fakes and two producers. Assert allocations after middle/tail deletion exceed the previous high-water
  mark, concurrent writers receive distinct increasing values, retry does not create duplicate events,
  and a fresh worker retains the high-water mark. Inject counter-write conflict and outage failures.
  **Future validation:** With isolated persistent-store doubles and test dependencies, run
  `python -m pytest tests/unit/test_event_recorder.py tests/contract/test_playback_api.py -q`.
  Expected: exact uniqueness/monotonicity assertions pass across deletion, concurrency and restart.
  **Complete when:** Every accepted event receives a stable never-reused per-tenant sequence, including annotations.

### P1: Playback Eligibility Is Not Frozen at Completion or Enforced by Lifecycle

- [ ] AUD-026-007 Enforce terminal playback eligibility and preserve the original review audience

  **Obligations:** FR-009/015/018, US3-AS1/2, edge cases on unauthorized annotation, read-only assumption,
  T032-T036/T042/T045/T046, and the participant/controller clarification.
  **Expected / observed / impact:** [PlaybackService](../../apps/api/app/services/playback_service.py#L33)
  checks current membership but no lifecycle status; annotation creation has the same omission and
  edit/delete check only the author. The participants endpoint allows additions after archive. A
  newly enrolled user can therefore gain review access without having participated in the exercise.
  [Chat routes](../../apps/api/app/api/routes/simulation_chat.py#L58) do not check tenant membership
  or terminal status, so the alternate history/mutation path does not preserve the review boundary.
  The tenant model does not accept `Completed`, although the specification and UI name that state.
  **Search / owner:** Complete playback/annotation services, simulation management and chat routes,
  domain state machine, tenant middleware and RBAC middleware inspected. Tenant middleware only logs
  a nonmember; the newer RBAC middleware's protected prefixes do not include these simulation routes.
  The neighboring UUID lifecycle handlers use a different simulation_state repository and no tenant
  warp clock; [registration order](../../apps/api/app/api/router.py#L68) places these tenant routes
  first. They do not supply an implicit replacement or missing guard for the inspected path.
  **Developer:** Define a terminal-state policy, support or explicitly map historical Completed records,
  freeze the review audience at completion, and prevent post-completion enrollment from expanding it.
  Gate all review reads and annotation writes consistently; reject terminal chat/tool mutations and
  unauthorized history access. Preserve the live dashboard feed through an explicitly live read API
  or policy, since it currently consumes `/playback/events`; do not accidentally break live monitoring.
  **Compatibility / dependencies:** Maintain creator access and eligible participants who joined during
  the exercise. Preserve live chat's independent pace. Coordinate terminal deletion with AUD-026-008;
  obtain an explicit lifecycle-contract resolution rather than declaring Completed superseded.
  **Tester:** Extend [playback contracts](../../tests/contract/test_playback_api.py#L120) and the
  existing [controller wiring test home](../../apps/api/tests/test_simulation_chat_controller_wiring.py#L22).
  Use controller, original participant, stranger, post-archive invitee and author fixtures across
  Active/Paused/Archived/Completed/Deleted. Assert eligible terminal review succeeds, ordinary strangers
  and late invitees receive 403, deleted review is unavailable, and terminal chat/tool calls produce
  no new history, events or signals. Preserve valid live-feed reads and author-only 403 tests.
  **Future validation:** With offline dependencies and controlled auth claims, run
  `python -m pytest tests/contract/test_playback_api.py apps/api/tests/test_simulation_chat_controller_wiring.py -q`.
  Expected: the expanded state/audience matrix passes without weakening the live workflow.
  **Complete when:** The review audience and terminal behavior are enforceable on every reachable path,
  not just by hiding a link in the UI.

### P1: Deletion Retains Playback Events, Snapshots and Annotations

- [ ] AUD-026-008 Delete playback artifacts with the simulation lifecycle

  **Obligations:** Playback-retention assumption, FR-009/016/017, R7, and lifecycle/deletion boundaries.
  **Expected / observed / impact:** [Delete handling](../../apps/api/app/api/routes/simulations.py#L385)
  only transitions the retained tenant to Deleted. The complete event repository has no tenant purge,
  and playback authorization still accepts its participants. Review data remains stored and readable
  after the specified deletion boundary.
  **Search / owner:** Inspected delete/archive handlers, SimulationRepository and SimulationEventRepository
  through their complete CRUD paths; searched their event/snapshot/scheduler document operations.
  No purge or retention hook appears on the controlling deletion path.
  **Developer:** Implement an idempotent tenant-scoped purge of events, annotations, snapshots and
  scheduler artifacts; include chat data if it remains a source for playback reconstruction. Deny
  playback immediately on deletion and make purge failure observable/retryable. Preserve separately
  governed audit records and other tenants; a tombstone may remain without retaining playback payloads.
  **Compatibility / dependencies:** Coordinate with AUD-026-007 and the chosen scheduler container.
  Archive must continue retaining review data; deletion, not wall-clock TTL alone, removes it.
  **Tester:** Extend [playback contracts](../../tests/contract/test_playback_api.py#L1) with two tenants,
  events, snapshots, annotations and cursor state. Assert archive retains them, deletion makes every
  playback endpoint unavailable and removes only the target partition's artifacts; retries after a
  partial purge finish cleanup without affecting the second tenant.
  **Future validation:** With fake repositories and injected purge failures, run
  `python -m pytest tests/contract/test_playback_api.py -q`.
  Expected: no deleted-tenant payloads remain accessible, cleanup is idempotent, and archive retention holds.
  **Complete when:** Both access revocation and durable cleanup are covered, with a documented retry policy.

### P1: Legacy Clock Data Can Be Reset or Have Its Running Anchor Removed

- [ ] AUD-026-012 Migrate legacy elapsed time and retire the destructive clock backfill

  **Obligations:** FR-002/006/007, default/backward-compatibility clarification, R2/R5, data-model deprecation,
  T004/T016/T018/T049/T050/T053.
  **Expected / observed / impact:** [Legacy-compatible model defaults](../../packages/domain/src/domain/models/simulation_tenant.py#L70)
  retain `elapsed_seconds` but default accumulated time to zero and clock_paused to true without
  migration. A legacy Active tenant therefore appears paused to the clock and cannot be paused by
  the service; a legacy paused/archived tenant can lose its displayed elapsed value. The
  [backfill script](../../scripts/backfill_simulation_elapsed.py#L20) still labels `last_resumed_at`
  obsolete and deletes it. Running that script after this feature would remove the canonical anchor.
  **Search / owner:** Full tenant model, clock/service/repository serialization and backfill inspected;
  searched scripts for accumulated time, running anchors and playback fields. No replacement clock
  migration was found in that scope. This audit did not run the backfill.
  **Developer:** Add an idempotent migration/compatibility adapter that preserves known legacy elapsed
  values and establishes an explicit paused/running anchor without inventing unobserved time. Guard
  or replace the old backfill. Keep default 1x and wall-clock expires_at unchanged. Resolve whether
  legacy elapsed_seconds means live current time or accumulated time; the API contract and task/data
  model text currently differ. Include the legacy field on the documented compatibility responses.
  **Compatibility / dependencies:** Must precede applying clock mutations to pre-feature tenants;
  coordinate wire-shape decisions with AUD-026-015, without requiring playback events to exist.
  **Tester:** Extend [clock tests](../../tests/unit/test_simulation_clock.py#L41) and
  [warp contracts](../../tests/contract/test_warp_speed_api.py#L107). Load old Active/Paused/Archived
  documents with elapsed_seconds=123 and no new fields; assert preserved elapsed time, valid pause/resume,
  unchanged TTL, no advance while paused, and migration replay makes no further changes. Assert a
  guarded backfill cannot remove an active clock anchor. Include negative/zero time and clock rollback cases.
  **Future validation:** After extracting any migration into a testable offline transform, run
  `python -m pytest tests/unit/test_simulation_clock.py tests/contract/test_warp_speed_api.py -q`.
  Expected: legacy documents and new 1x tenants satisfy the same compatibility assertions; no cloud script runs.
  **Complete when:** Known elapsed time survives upgrade, all lifecycle transitions remain usable, and
  operational guidance cannot erase the new canonical clock state.

### P1: Annotation Writes Can Report Success Without Durable Mutation

- [ ] AUD-026-013 Fail annotation mutations when persistence does not succeed

  **Obligations:** FR-016/018, SC-006, US5-AS1/2, T044-T048 and author-only CRUD correctness.
  **Expected / observed / impact:** [Repository update/delete](../../apps/api/app/repositories/simulation_event_repository.py#L175)
  catches durable-write failures; update returns the event and delete returns false. The
  [annotation service](../../apps/api/app/services/annotation_service.py#L59) ignores delete's result,
  so the route returns 204 even when nothing was deleted; updates can similarly return 200 after a
  failed upsert. Creation shares the hidden-write-success path in AUD-026-003. The UI then removes or
  replaces its local row, contradicting what later reviewers will retrieve.
  **Search / owner:** Complete repository, annotation service/routes, API client and panel CRUD callbacks
  inspected. Existing tests assert 201/200/204 and author denial, not reread durability under storage failure.
  **Developer:** Return a truthful persistence result or raise a typed storage exception for CRUD;
  map it to a retriable API failure and retain the user's draft/current row on failure. Do not apply
  payload mutations before durable success. Refetch authoritative events after a successful mutation,
  including other reviewers' intervening notes. Keep author-only authorization independent from storage errors.
  **Compatibility / dependencies:** Preserve successful 201/200/204 semantics; coordinate failure
  propagation with AUD-026-003 and payload compatibility with AUD-026-015. Avoid duplicate retry creates.
  **Tester:** Extend [annotation tests in the consolidated suite](../../tests/contract/test_playback_api.py#L239)
  using a fake Cosmos container that fails create/update/delete independently. Assert failed requests
  are not 2xx, a fresh repository still reads the previous text, failed delete retains the row, successful
  delete removes it, and another user's update/delete remains 403. Verify UI drafts survive a 503.
  After a successful mutation, assert the refreshed list includes another reviewer's concurrently saved note.
  **Future validation:** With isolated storage doubles, run
  `python -m pytest tests/contract/test_playback_api.py -q`; add UI failure cases under proposed
  `apps/web/tests/unit/spec_026/playback.test.tsx` and run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026` after authoring that suite.
  **Complete when:** Acknowledged mutations survive a fresh read and failed ones remain visibly unsaved.

### P1: The Configured Infrastructure Entry Point Omits the Event Container

- [ ] AUD-026-014 Include sim-events in the configured infrastructure deployment

  **Obligations:** T001a, T005, plan storage/AU-platform/quality gates and durable recording prerequisites.
  **Expected / observed / impact:** [azure.yaml](../../azure.yaml#L8) selects `infra/main.bicep`.
  Its [container declarations](../../infra/main.bicep#L603) include simulation and sim-chat but no
  sim-events. The required definition and indexes exist in the alternate
  [infra/bicep/main.bicep](../../infra/bicep/main.bicep#L158), which is not referenced by that entry point.
  Thus an authored container is present, but the configured deployment path does not provide it.
  Actual deployed container existence and approvals are UNVERIFIED, not asserted absent.
  **Search / owner:** Searched all Bicep/JSON/Terraform files under infra for `sim-events`, `event_seq`
  and `sim_time_offset`; matches were only the alternate template and its generated JSON. Inspected
  azd configuration, active container declarations and module references.
  **Developer:** Add/reuse the tenant-partitioned event container through the active module graph,
  retaining ordered-sequence/sim-time indexes and AU residency. Resolve scheduler cursor placement
  explicitly: the design says simulation with /tenant_id, current simulation uses /scenario_id,
  while the implementation stores the cursor in sim-events. Follow repository AVM/policy requirements
  and do not change existing partition keys destructively.
  **Compatibility / dependencies:** This is a prerequisite for durable AUD-026-001/002/003/013 behavior.
  Do not replace the deployment entry point wholesale or modify unrelated infrastructure.
  **Tester:** Add a focused static assertion under proposed `infra/tests/test_sim_events_wiring.py`:
  traverse the configured entry point, assert exactly one `sim-events` container with /tenant_id and
  both required indexes, and assert the scheduler's selected store matches the documented schema.
  **Future validation:** With Bicep tooling and restored modules available, run
  `bicep build infra/main.bicep --stdout`; after authoring the proposed test, run
  `python -m pytest infra/tests/test_sim_events_wiring.py -q`. Expected: the compiled active graph
  contains the required container/indexes. What-If, policy review and deployment require separate
  authorization and evidence; none were performed here.
  **Complete when:** Active-template validation passes and separately authorized deployment evidence
  establishes the intended container without changing unrelated resources.

### P2: Reviewer Identity and Controller Controls Use the Wrong Client Boundary

- [ ] AUD-026-009 Use the authenticated reviewer identity for author and controller controls

  **Obligations:** FR-018, US5 editing/deletion clarification, T020/T030/T047/T048; controller-only US2 controls.
  **Expected / observed / impact:** The [playback page](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L41)
  sets currentUserOid to `sim.created_by`, not the signed-in reviewer. The panel compares that value
  with each annotation's author, so participants cannot edit their own notes and see controls for the
  creator's notes instead. The [dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L320)
  shows speed controls to all participants. Backend author/controller checks correctly reject forbidden
  writes; this is a broken client workflow, not evidence of bypassing those checks.
  **Search / owner:** Complete player, annotation panel, dashboard, warp control and clients inspected;
  successful/forbidden backend cases are present in the contract tests.
  **Developer:** Supply the authenticated session OID, keep it separate from tenant ownership, and hide
  author/controller-only controls until identity is resolved. Reuse a controlled speed picker for both
  creation and live control rather than coupling the reusable picker itself to a tenant API call.
  Show notes at/near the selected position, with an explicit all-notes view if needed, rather than an
  unqualified list that loses the local review context.
  **Compatibility / dependencies:** Preserve server authorization, all six allowed speeds and default 1x.
  Resolve paused speed-change policy against the amended contract through AUD-026-015.
  **Tester:** Proposed home `apps/web/tests/unit/spec_026/playback.test.tsx`, following the existing
  [Vitest discovery pattern](../../apps/web/vitest.config.ts#L17). Mock authenticated creator and
  participant identities plus their respective notes. Assert each sees only their own edit/delete,
  participants can edit their own note, only creator sees live speed controls, and unresolved identity
  exposes neither privileged control. Assert near-position filtering and an explicit way to inspect
  all notes. Retain backend 403 tests against crafted requests.
  **Future validation:** After authoring fixtures/tests, run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026` and
  `python -m pytest tests/contract/test_playback_api.py tests/contract/test_warp_speed_api.py -q`.
  Expected: positive owner actions work, unauthorized controls are absent, server denial remains enforced.
  **Complete when:** Identity comes from the authenticated caller and creator/participant journeys both pass.

### P2: End Feedback and Empty-Timeline Handling Are Incomplete

- [ ] AUD-026-010 Complete playback end feedback and empty-timeline states

  **Obligations:** FR-009/014, US3-AS7, empty/corrupt-history edge cases, T040/T041.
  **Expected / observed / impact:** The [player](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L66)
  stops advancing at duration but has no ended notification. Its empty-history branch returns before the
  timeline and partial warning, saying playback is unavailable rather than showing the required empty
  timeline. Duration includes annotations, allowing a future-offset note to extend the recorded end.
  **Search / owner:** Complete page, controls, timeline and annotation panel inspected; no alternate
  player terminal-state implementation was found in the inspected client path.
  **Developer:** Implement explicit ended state and restart semantics, an empty timeline with explanatory
  text, and a partial-empty state that
  does not conceal recording loss. Derive recorded duration independently of annotations; validate or
  visibly handle out-of-range notes. Do not auto-pause on annotation markers.
  **Compatibility / dependencies:** Preserve 1/2/5/10x playback and independent local positions;
  integrate reconstruction from AUD-026-005 and gap information from AUD-026-003.
  **Tester:** Proposed `apps/web/tests/unit/spec_026/playback.test.tsx`: use controlled RAF/timers,
  known total duration, annotation markers and empty/partial histories. Assert
  end stops scheduling and announces completion,
  annotation markers do not pause, and out-of-range notes cannot silently change recorded duration.
  **Future validation:** With dependencies and authored unit tests, run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026`. A later browser gesture check needs
  separate runtime authorization; no existing evaluator-idempotency test substitutes for this player test.
  **Complete when:** Empty/partial states, stable recorded duration and completion feedback have exact assertions.

### P2: The Timeline Does Not Implement Its Required Drag Interaction

- [ ] AUD-026-024 Implement draggable scrubbing with informative timeline markers

  **Obligations:** T039, FR-011, US3-AS5 interaction detail; timeline labels and event-summary tooltip design.
  **Expected / observed / impact:** [Timeline input](../../apps/web/src/components/playback-timeline.tsx#L44)
  has click and left/right key handlers but no pointer-down/move/up capture. Its playhead is a static
  span, labels show only endpoints, and tooltips contain type/offset rather than event summaries.
  The documented click/drag review interaction is therefore only partly usable.
  **Search / owner:** Complete timeline, player onScrub and controls inspected; no delegated drag handler
  is wired through their props. No matching timeline test exists in the scoped frontend test search.
  **Developer:** Implement pointer capture with clamped continuous position updates, safe cancellation,
  accessible keyboard equivalents, interval labels and concise payload summaries. Use canonical
  simulated offsets and stable dimensions; do not make pointer movement change playback speed or author notes.
  **Compatibility / dependencies:** Preserve existing click/arrow behavior and annotation markers;
  connect to state reconstruction in AUD-026-005 without coupling independent reviewer positions.
  **Tester:** Proposed `apps/web/tests/unit/spec_026/playback-timeline.test.tsx`: use a fixed bounding
  rectangle and events at 0,300,600. Assert pointer drag maps to exact clamped offsets, outside-pointer
  release/cancel stops updates, click and keyboard still work, zero duration is safe, and marker
  summaries/time labels reflect the fixture. Check equal-offset marker behavior explicitly.
  **Future validation:** With web test dependencies and the proposed suite authored, run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026/playback-timeline.test.tsx`.
  Expected: positive drag, negative cancelled drag and edge-clamping assertions all pass.
  **Complete when:** The required drag/label/summary behavior is implemented and tested without regressing click/key input.

### P2: Throttling and Lag Warnings Are Not Deployment-Tunable End to End

- [ ] AUD-026-011 Honor deployment throttle settings and report actual pending-delivery lag

  **Obligations:** FR-008, clarifications 10/11, edge case 1, R6, T012/T014/T023/T051 and plan limits.
  **Expected / observed / impact:** The scheduler factory never configures max_burst_rate; the scheduler's
  environment-based warning helper is unused. [Clock route output](../../apps/api/app/api/routes/simulations.py#L166)
  uses a fixed constant and [the display](../../apps/web/src/components/simulation-server-clock.tsx#L71)
  independently tests `lag >= 10`. Lag is only updated after successful delivery, so pending/failing
  work is not represented reliably. A due signal write failure loops without a failure sleep/backoff.
  No lag>0 throttle indicator exists; the unrelated tenant throttle_mode display is not that indicator.
  **Search / owner:** Complete scheduler loop/config helper, route factory/clock response, warp constants,
  dashboard and clock component inspected; searched runtime sources for throttle/lag configuration consumers.
  **Developer:** Validate positive deployment settings, default burst to 100/s and warning to greater
  than 10 wall seconds, and expose one authoritative warning threshold/boolean to the UI. Measure lag
  from the oldest pending due delivery, handle pauses/speed changes correctly, add failure backoff and
  a nonzero-backlog indicator. Resolve T023's older five-second instruction explicitly against FR-008/R6.
  **Compatibility / dependencies:** Preserve strict signal order and never drop/coalesce signals;
  requires connected scheduling from AUD-026-001 and lease safety from AUD-026-002.
  **Tester:** Extend [scheduler tests](../../tests/unit/test_warp_scheduler.py#L1), clock API tests and
  proposed web spec-026 clock tests with 101 same-time signals, a configured cap of 2/s, and a failing
  signal store. Assert each rolling window obeys the cap, no loss/reordering, pending lag rises,
  failures yield/back off, and 9.9/10/10.1 plus custom-threshold values produce consistent warning states.
  **Future validation:** Run `python -m pytest tests/unit/test_warp_scheduler.py tests/contract/test_warp_speed_api.py -q`
  and `pnpm --filter @ama/web exec vitest run tests/unit/spec_026` after authoring the fixtures.
  Expected: defaults, overrides, invalid settings, backlog and failure behavior all satisfy exact assertions.
  **Complete when:** Deployment configuration controls both enforcement and displayed warnings, including backlog.

### P2: Wire Contracts, Client Types and Quickstart Examples Disagree

- [ ] AUD-026-015 Resolve contract conflicts and align request and response shapes

  **Obligations:** API contract's five modified/seven new endpoints, T011/T018/T019/T024/T026/T028/T029/T031,
  T038/T044-T046/T050/T054, R5/R7 and data-model compatibility.
  **Expected / observed / impact:** The [amended warp contract](contracts/api-contracts.md#L93)
  allows Paused, while original T026/T028/T029 reject every non-Active state; current service/tests allow
  Paused. Annotation contracts require `ann-*` identity, author_id/name and flat replies, but services
  return `evt-*` SimulationEvent documents with payload.author_oid and no author_name. The
  [client types](../../apps/web/src/lib/api/simulations.ts#L85) require clock fields not returned and
  name previous_warp_speed instead of previous_speed. Metadata response field names also differ.
  [Quickstart creation](quickstart.md#L56) sends lowercase bushfire and object participants instead
  of the accepted Bushfire/string-list shape, with no authenticated-role setup. These are concrete
  compatibility/documentation conflicts, not proof the smoke commands ran successfully.
  **Search / owner:** Complete contract, quickstart, request models, response builders, clients,
  services and contract assertions inspected. Paused handling is documented, but there is no explicit
  replacement of the contradictory original tasks; they are CONFLICT, not SUPERSEDED.
  **Developer:** Record explicit owner-approved resolutions for paused speed changes, Completed lifecycle,
  elapsed_seconds meaning, scheduler container placement, annotation identity/payload and creation clock
  state. Align serializers, validators, TypeScript types and examples to that resolved contract. Preserve
  old annotation IDs/payloads through an adapter/version if needed; do not silently break existing records.
  Populate the corresponding Run initial compression ratio from selected warp, or explicitly document
  its replacement in the declared ownership contract. Enforce text limits for direct service callers too.
  **Compatibility / dependencies:** Coordinates AUD-026-007/012/013/014; does not authorize changing original
  artifacts during this audit. Reuse consolidated annotation tests rather than creating a duplicate suite.
  **Tester:** Extend [warp](../../tests/contract/test_warp_speed_api.py#L86) and
  [annotation contracts](../../tests/contract/test_playback_api.py#L233) with exact response key/value
  assertions, legacy/new annotation fixtures, paused/terminal speed behavior, omitted/invalid warp values,
  and schema-valid quickstart request bodies. Assert author attribution, sim offset and edit timestamp,
  not only status or field presence. Typecheck the actual client response types.
  **Future validation:** With dependencies and offline auth fixtures, run
  `python -m pytest tests/contract/test_warp_speed_api.py tests/contract/test_playback_api.py -q` and
  `pnpm --filter @ama/web exec tsc --noEmit`. Corrected curl smoke steps require a later authorized
  local server and identity; expected create/change/clock/read/create-note results are 201/200/200/200/201.
  **Complete when:** Each published request/response matches exact assertions, and all conflicts have
  cited resolutions rather than retrospective completion or assumed supersession.

### P2: The Live Clock Does Not Interpolate Between Server Polls

- [ ] AUD-026-017 Interpolate simulated time between canonical server clock samples

  **Obligations:** FR-006, T021/T023; smooth server-owned clock display.
  **Expected / observed / impact:** [The clock component](../../apps/web/src/components/simulation-server-clock.tsx#L28)
  displays each one-second poll directly with no interpolation; at 60x it jumps by about 60 simulated
  seconds. It polls regardless of lifecycle. This fails the explicit smooth-display task even though
  the displayed samples themselves are simulated rather than wall-clock time.
  **Search / owner:** Complete dashboard/list, clock/control components and client/route timer responses
  inspected; searched those pages for elapsed, playback-status and lag rendering.
  **Developer:** Interpolate from the latest current_sim_seconds sample while running and freeze the
  display when paused; do not add time to a stale accumulated-only value. Handle late/stale poll replies.
  Dispose timers and restrict running interpolation to a current unpaused sample.
  **Compatibility / dependencies:** Requires aligned clock types from AUD-026-015. Preserve server
  ownership: never post client elapsed time back as authority, and retain lag display from AUD-026-011.
  **Tester:** Proposed `apps/web/tests/unit/spec_026/clock.test.tsx` under the existing Vitest pattern.
  Use fake timers, delayed/out-of-order polls, 1x/60x, pause/resume and Archived responses. Assert
  intermediate display ticks use simulated time, pause freezes, stale data cannot undo newer state,
  disposed components stop polling, and no elapsed-time write is sent to the API.
  **Future validation:** After authoring the suite, run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026`.
  Expected: exact time/status/UI assertions pass without client-clock writes or persistent polling after disposal.
  **Complete when:** Smooth displayed time follows canonical samples without advancing through pauses or stale replies.

### P2: Stopping an Exercise Leaves the Dashboard in Archiving

- [ ] AUD-026-021 Apply the archive response and reveal playback after completion

  **Obligations:** T023/T042, FR-009, US3-AS1 and the archive response/lifecycle contract.
  **Expected / observed / impact:** [handleStop](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L263)
  ignores result.status and accumulated_sim_seconds and sets Archiving. The
  [service](../../apps/api/app/services/simulation_service.py#L212) has already persisted Archived
  before returning. No status refetch follows, so the Review Playback link remains hidden until reload.
  **Search / owner:** Complete dashboard stop handler, clock callback, archive client/route/service and
  playback-link condition inspected; existing clock polling does not refresh lifecycle status.
  **Developer:** Apply authoritative response status and final accumulated time. If the resolved API
  contract allows asynchronous Archiving, explicitly refetch until terminal completion or a visible
  error; do not replace the returned status with a constant. Enable the eligible playback link as soon
  as terminal completion is known, preserving final clock state and closed controls.
  **Compatibility / dependencies:** Coordinate the archive contract resolution in AUD-026-015 and
  eligibility policy in AUD-026-007. Support both immediate Archived and a genuinely pending Archiving response.
  **Tester:** Proposed `apps/web/tests/unit/spec_026/dashboard.test.tsx` under existing Vitest discovery.
  Return Archived with a known accumulated value from archiveSimulation and assert the status/time and
  Review Playback link immediately update without reload. Cover pending-then-Archived, failure, stale poll,
  and ineligible viewer cases; assert stop sends no client elapsed time and failure does not fake completion.
  **Future validation:** With dependencies and the proposed test file authored, run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026/dashboard.test.tsx`.
  Expected: the archive-to-review journey works with exact server status/time and no false terminal state.
  **Complete when:** A successful stop leads to the correct terminal UI and eligible playback access without reload.

### P2: Recording Completeness Is Not Displayed in Detail or List Views

- [ ] AUD-026-022 Display durable recording completeness in both simulation views

  **Obligations:** T052, FR-010a's controller visibility and the SimulationTenant full/partial/none contract.
  **Expected / observed / impact:** [List columns](../../apps/web/src/app/simulations/page.tsx#L65) and
  [dashboard header](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L297) have no Full Recording,
  Partial Recording or No Recording badge. onClockTick tries to consume playback_status, but the clock
  route does not return it. Users cannot see recording completeness before opening the player.
  **Search / owner:** Complete list/detail, clock output/type and playback_status references inspected;
  the player's generic partial warning is not the required list/detail indicator.
  **Developer:** Render all three status badges with accessible labels and a partial-recording explanation.
  Obtain current durable health via a documented polling/detail response, retaining the previous value
  on fetch errors instead of assuming full. Handle legacy none consistently and make loss visible to controllers.
  **Compatibility / dependencies:** Depends on truthful health in AUD-026-003 and response alignment in
  AUD-026-015; UI badges cannot remedy the missing persisted health latch by themselves.
  **Tester:** Proposed `apps/web/tests/unit/spec_026/dashboard.test.tsx` with full/partial/none tenants
  and a healthy-to-partial update. Assert exact labels appear in both views, partial has an explanation,
  none is not portrayed as complete, and a failed refresh preserves known partial status. Keep lifecycle
  status and recording completeness separate in the fixtures and assertions.
  **Future validation:** After authoring the web tests, run
  `pnpm --filter @ama/web exec vitest run tests/unit/spec_026/dashboard.test.tsx`.
  Expected: all completeness states and refresh/error transitions display accurately in list and detail.
  **Complete when:** Both views expose durable completeness without implying an unverified full recording.

### P2: Authored Tests Do Not Establish the Missing Acceptance or Performance Outcomes

- [ ] AUD-026-018 Add missing boundary assertions and retain revision-specific validation evidence

  **Obligations:** T009-T013/T026/T027/T032-T034/T044/T049/T050/T054-T056, SC-001/002/003/004/006,
  test-first/checkpoint instructions and plan quality gates.
  **Expected / observed / impact:** The five feature-specific modules contain 43 test functions:
  23 unit and 20 contract tests. They cover useful arithmetic/CRUD cases, but no actual seeded lifecycle
  round-trip, storage failure boundary, nearest-state replay, 24-hour timing or browser player behavior.
  `test_scheduler_state_persists` never restarts a worker; the empty-history test permits up to five
  events; snapshot tests assert count/offset, not state. The similarly named web test exercises an
  outcome evaluator, not playback. [CI](../../.github/workflows/ci.yml#L131) selects contract/integration
  tests; its [coverage helper](../../scripts/coverage-ratchet.ps1#L45) reads XML and does not run the
  feature's unit tests. No execution/coverage/performance record for this reviewed revision was supplied.
  The scheduler unit fixture also leaves tenant.status as Provisioning and calls the permissive tick
  directly; the real delivery loop would exit for that status. It cannot prove the real loop works.
  **Search / owner:** Searched tests/unit, contract, integration, simulation, benchmark/load/performance,
  apps/api test modules and both apps/web tests and `__tests__` for warp/playback/clock/event services and assertions.
  Read matching tests, fixtures, discovery configs, CI and its helper. Planned integration files were
  not found; annotation tests were relocated into test_playback_api.py and are credited there.
  **Developer:** Add boundary tests within each owning fix above, and proposed integration homes
  `tests/integration/test_warp_simulation_lifecycle.py` and `tests/integration/test_playback_events.py`.
  Add focused playback/snapshot unit cases and make CI select the new unit/UI suites. Record artifact
  revision, fixture hash, environment, commands, pass/fail counts and coverage, not a checklist assertion.
  **Compatibility / dependencies:** Functional fixes precede measurement. Preserve existing unrelated
  suites; no tests or benchmarks are authorized to run in this audit. Clear real COSMOS_ENDPOINT for
  isolated tests or inject fakes, since the fixtures otherwise construct environment-sensitive clients.
  **Tester:** Use deterministic small clocks for assertions plus a separately authorized wall-time run:
  all scheduled IDs delivered once in order; 86,400 simulated seconds at 60x finishes under 1,500 wall
  seconds; speed changes affect delivery within five seconds; scrub state is exact in under three seconds;
  healthy recordings contain every required event and degraded histories expose exact gaps.
  **Future validation:** With Python 3.12+, API/agent dependencies, pytest/asyncio/cov and isolated stores,
  run `python -m pytest tests/unit/ tests/integration/ tests/contract/ -q --tb=line`, then
  `python -m pytest tests/ -q --tb=short --cov=apps --cov=packages --cov-report=term`.
  Run `pnpm --filter @ama/web exec vitest run tests/unit/spec_026` after authoring it. Proposed benchmark
  home `tests/simulation/test_warp_scenario.py`: run `python -m pytest tests/simulation/test_warp_scenario.py -v`
  only after an approved representative measurement environment exists. Expected: no regressions,
  exact acceptance assertions, relevant coverage and retained timing evidence satisfying the thresholds.
  **Complete when:** The missing assertions are discoverable and actual revision-bound execution artifacts
  support the claimed results. An authored test or CI file alone cannot close an execution task.

### P2: Reviewer Utility and Required Human Reviews Have No Supplied Proof

- [ ] AUD-026-019 Measure reviewer utility and retain the requested human review outcomes

  **Obligations:** SC-005, phase-3/4 incident-commander reviews, phase-5 observer/incident-commander/planning-officer
  reviews, phase-6 observer/security reviews, and plan architecture/operational/quality sign-offs.
  **Expected / observed / impact:** [SC-005](spec.md#L170) requires at least 80% useful/very-useful survey
  responses. [Task checkpoints](tasks.md#L150) request actual review sessions. Local documents contain
  assignments, PASS claims and checkboxes, but no named session record, survey denominator/responses,
  signed result or scoped review evidence. Source cannot establish that training value or approval occurred.
  **Search / owner:** All eight local documents and the cited rubric baseline/evidence contracts were
  read; no spec-026 reviewer survey or review execution record is among those inputs. This is an
  UNVERIFIED evidence outcome, not a claim about every possible external meeting or system.
  A further bounded search in docs/testing, test-data, observability, operator-runbooks, runbooks and
  attestations for this spec/HYP/playback-survey/warp timing references found no matching evidence document.
  **Developer:** After functional fixes, arrange a separately authorized after-action review with actual
  eligible participants. Preserve explicit criteria, reviewer role/date/revision, findings and disposition;
  do not substitute agent-name assignment for human evidence. Capture a bounded, nonempty survey cohort
  and anonymized raw ratings so the percentage is reproducible. Review template/scenario fidelity and
  the ordinary/restricted reviewer flows as well as happy-path UI.
  **Compatibility / dependencies:** Depends on AUD-026-001/003/005/007/009/010/013/017. Country placeholders
  remain deferred; do not invent SME approvals or request external approvals during this audit.
  **Tester:** Proposed evidence homes `specs/026-sim-warp-playback/evidence/reviewer-survey.json` and
  `specs/026-sim-warp-playback/evidence/review-register.md`. Assert cohort size > 0, each counted response
  is eligible/in-window, useful-or-very-useful count divided by all responses is at least 0.80, and
  all requested review roles have attributable outcomes; preserve negative feedback and open actions.
  **Future validation:** After genuine evidence exists, inspect ratings with
  `Get-Content specs/026-sim-warp-playback/evidence/reviewer-survey.json -Raw | ConvertFrom-Json | Group-Object rating`
  and read the review register. Expected: reproducible numerator/denominator and traceable review outcomes;
  arithmetic or source inspection cannot manufacture a human sign-off.
  **Complete when:** The measured survey meets SC-005 and every requested review has evidence or an
  explicit unresolved disposition. Until then the corresponding outcome remains UNVERIFIED.

### P2: HYP-024 Links to a Missing and Noncanonical Evidence Stub

- [ ] AUD-026-020 Repair hypothesis evidence and establish scoped persona-validation provenance

  **Obligations:** HYP-024, PER-070/071 validation claims, PER-072 preconditions, SCP-078/079/080/081.
  **Expected / observed / impact:** [HYP-024](spec.md#L197) claims a created stub at
  `specs/028-capstone-alignment/evidence/HYP-HYP-024.md`; that file is missing. Filename search for
  `*HYP*024*` found no replacement; the bounded feature-028 evidence search found only the
  [portfolio-wide baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1), not a spec-026
  post-feature delta or consultation history. The [stub contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L7)
  instead requires an owning-spec HYP-024.md file, six sections and initial status Not tested.
  PER-070/071 say validated but the local amendments provide no named SME/practitioner/date evidence.
  **Search / owner:** Complete inline amendments, baseline, stub/persona contracts and the bounded
  HYP filename/content searches. No other implementation-review report was consulted.
  **Developer:** Resolve the owning location through the declared governance process; proposed canonical
  home is `specs/026-sim-warp-playback/evidence/HYP-024.md`. Repair references/register links in an
  authorized follow-up, add all six required sections and retain Not tested until a qualifying
  feature validates it. Preserve the frozen portfolio baseline; add a genuinely spec-scoped comparator
  and consultation record for the five criteria. Link real validation evidence for claimed personas,
  or explicitly qualify those claims. Do not promote PH/JP/BD placeholders or claim other specs' authority.
  **Compatibility / dependencies:** Changes to evidence status require the contract's change-control
  process. This audit's no-delegation authorization is not proof of historical agent consultation.
  **Tester:** Validate six H2 headings in order, at least two preconditions, quantified falsification,
  a bounded measurement window, Not tested status and owning-spec link. For future validation, assert
  each required criterion does not regress and the specified mean improvement is met using attributable
  pre/post scores; do not substitute the portfolio mean for this spec's scores. Persona validation must
  cite at least one SME/practitioner, not only a proxy or role label.
  **Future validation:** After authoring the proposed stub, run
  `Select-String -Path specs/026-sim-warp-playback/evidence/HYP-024.md -Pattern '^## '` and validate against
  the cited contract. Expected: the six named headings and a resolvable owning-spec link; subsequent
  score/consultation/SME evidence must be reviewed independently, not inferred from this structural check.
  **Complete when:** References resolve, the stub conforms, and claimed outcomes/validation have scoped
  evidence or remain explicitly unverified. No country or constitutional scope is silently expanded.

### P3: Required Domain Aggregate Exports Were Not Added

- [ ] AUD-026-016 Export the new domain models and warp constants through the declared package surface

  **Obligations:** T006; shared-model registration from phase 1.
  **Expected / observed / impact:** [T006](tasks.md#L60) requires aggregate exports. The proposed target
  `packages/domain/src/domain/models/__init__.py` does not exist; a scoped search of domain package
  initializers found none exporting the new symbols. Direct module imports work as authored but do
  not establish the promised aggregate import surface.
  **Search / owner:** Inspected [model declarations](../../packages/domain/src/domain/models/simulation_event.py#L29)
  and warp modules; searched packages/domain initializers for every requested model/constant export.
  **Developer:** Add the declared initializer or explicitly document an approved namespace-package
  alternative. Export SimulationEvent, PlaybackSnapshot, SignalSchedulerState, WarpSpeedChange and
  the named speed constants/helpers without importing API services or changing existing direct imports.
  **Compatibility / dependencies:** Preserve domain-only dependency direction and namespace/package
  discovery; do not introduce import cycles just to satisfy a filename.
  **Tester:** Extend [clock unit tests](../../tests/unit/test_simulation_clock.py#L8) with an aggregate
  import assertion for every promised symbol and identity equality with its defining module. Assert
  no API/service dependency is required; existing direct imports remain valid.
  **Future validation:** With the domain package and pytest available, run
  `python -m pytest tests/unit/test_simulation_clock.py -q`. Expected: both aggregate and direct imports
  resolve identical objects. No import was executed during this audit.
  **Complete when:** The declared package contract is exported and covered, or its replacement is explicitly approved.

## Requirement Coverage

All 19 functional IDs, including FR-010a, and all six success criteria are listed separately.
IMPLEMENTED credits the precise authored behavior, not its execution, performance, deployed state or
neighboring obligations. The evidence-status meanings are those in the binding audit contract.

| Requirement | Status | Concrete evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | IMPLEMENTED | [Constants/validator](../../packages/domain/src/domain/models/warp_constants.py#L11) and [creation choices](../../apps/web/src/app/simulations/create/page.tsx#L153) enumerate all six fixed speeds; arbitrary 7 is rejected in [contract assertions](../../tests/contract/test_warp_speed_api.py#L102). Delivery wiring is separately FR-004. | - |
| FR-002 | IMPLEMENTED | [Create service](../../apps/api/app/services/simulation_service.py#L40) validates/persists chosen warp and starts the clock; [default test](../../tests/contract/test_warp_speed_api.py#L96) asserts omitted speed is 1.0. | - |
| FR-003 | IMPLEMENTED | [Controller-only service mutation](../../apps/api/app/services/simulation_service.py#L169) and [route](../../apps/api/app/api/routes/simulations.py#L356) accept a running speed change, persist it and record history; [API test](../../tests/contract/test_warp_speed_api.py#L151) asserts previous/current values and participant denial. | AUD-026-009, AUD-026-015 |
| FR-004 | PARTIAL | [Delay arithmetic](../../apps/api/app/services/warp_scheduler.py#L109) is warp-aware, but [live seeding](../../apps/api/app/services/scenario_seeding_service.py#L30) publishes all entries before scheduling and no production loop caller was found. | AUD-026-001, AUD-026-002 |
| FR-005 | PARTIAL | [Clock speed transition](../../apps/api/app/services/simulation_clock_service.py#L71) preserves elapsed old-speed time; scheduler recomputes from its cursor, but live scheduling/restart/atomic boundary are incomplete. | AUD-026-001, AUD-026-002 |
| FR-006 | IMPLEMENTED | [Clock read](../../apps/api/app/services/simulation_clock_service.py#L111) computes simulated time and [display](../../apps/web/src/components/simulation-server-clock.tsx#L85) renders that value. Smooth interpolation and legacy upgrade are narrower outstanding obligations. | AUD-026-012, AUD-026-017 |
| FR-007 | PARTIAL | [Pause/resume arithmetic assertion](../../tests/unit/test_simulation_clock.py#L81) preserves 50 then advances to 150; delivery is not resumed by [service lifecycle](../../apps/api/app/services/simulation_service.py#L150), and chat synthetic counters advance while Paused. | AUD-026-001, AUD-026-002, AUD-026-012 |
| FR-008 | PARTIAL | [Burst loop](../../apps/api/app/services/warp_scheduler.py#L208) exists, but deployment configuration is not wired, pending failure lag is not maintained and [UI threshold](../../apps/web/src/components/simulation-server-clock.tsx#L71) is hard-coded. | AUD-026-001, AUD-026-011 |
| FR-009 | PARTIAL | [Participant/controller check](../../apps/api/app/services/playback_service.py#L43) exists, but lifecycle/original-audience enforcement is absent; [Completed is absent from tenant states](../../packages/domain/src/domain/models/simulation_tenant.py#L55), and [empty UI](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L116) omits the timeline. | AUD-026-007, AUD-026-008, AUD-026-010, AUD-026-021 |
| FR-010 | PARTIAL | [Recorder helpers](../../apps/api/app/services/simulation_event_recorder.py#L96) capture some categories; [turn persistence](../../apps/api/app/services/simulation/controller_service.py#L223) defaults chat to zero, signal capture is disconnected, alerts lack a canonical event path, and page-load UI logs are persisted. | AUD-026-001, AUD-026-004 |
| FR-010a | PARTIAL | [Recorder failure catch](../../apps/api/app/services/simulation_event_recorder.py#L70) preserves continuity, but [repository catch](../../apps/api/app/repositories/simulation_event_repository.py#L107) hides durable failures. No tenant partial latch/controller warning/gap reconstruction is connected. | AUD-026-003, AUD-026-022 |
| FR-011 | IMPLEMENTED | [Controls](../../apps/web/src/components/playback-controls.tsx#L34) support play/pause and [page onScrub](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L90) updates position from click/keyboard input. Required drag detail and actual state replay remain separate gaps. | AUD-026-005, AUD-026-024 |
| FR-012 | IMPLEMENTED | [Playback speed set](../../apps/web/src/components/playback-controls.tsx#L3) is 1/2/5/10 and [RAF advancement](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L60) multiplies wall delta by selected playbackSpeed. | - |
| FR-013 | MISSING | [Player scrub](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L90) only sets time; [snapshot contents](../../apps/api/app/services/simulation_event_recorder.py#L225) only retain the last event. The inspected page/client/components/services contain no state reducer or snapshot consumer. | AUD-026-005 |
| FR-014 | PARTIAL | [RAF end branch](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L66) stops at duration, but the page/controls do not announce that the simulation ended. | AUD-026-010 |
| FR-015 | IMPLEMENTED | [Panel submit](../../apps/web/src/components/playback-annotation-panel.tsx#L37) sends currentSimTime; [create route](../../apps/api/app/api/routes/simulation_playback.py#L145) validates nonnegative offset and 1..2000 text length. Persistence/audience flaws are assessed separately. | AUD-026-007, AUD-026-013 |
| FR-016 | PARTIAL | [Annotation create](../../apps/api/app/services/annotation_service.py#L35) stores offset/OID and text as an event, but [durable write failure](../../apps/api/app/repositories/simulation_event_repository.py#L107) still reports success; contract attribution shape differs. | AUD-026-003, AUD-026-013, AUD-026-015 |
| FR-017 | PARTIAL | [Page load](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L30) reloads annotations and timeline positions, but pagination can omit later notes after deletion and failed writes are not durable. | AUD-026-006, AUD-026-013, AUD-026-023 |
| FR-018 | PARTIAL | [Server author comparison](../../apps/api/app/services/annotation_service.py#L69) plus [403 tests](../../tests/contract/test_playback_api.py#L262) are present; the page uses creator identity for every reviewer and persistence can falsely acknowledge edits/deletes. | AUD-026-009, AUD-026-013 |
| SC-001 | UNVERIFIED | [24-hour/<25-minute criterion](spec.md#L166); no matching measured 60x scenario test/result found in searched simulation/benchmark scopes. Disconnected seeding is a concrete blocker, not a measurement. | AUD-026-001, AUD-026-002, AUD-026-018 |
| SC-002 | UNVERIFIED | [Five-second/no-loss criterion](spec.md#L167); clock/API tests do not measure actual delivery response, and scheduler ownership/wiring is incomplete. | AUD-026-001, AUD-026-002, AUD-026-018 |
| SC-003 | UNVERIFIED | [Complete healthy/gapped degraded outcome](spec.md#L168); incomplete categories, zero chat offsets and hidden persistence failures are source counterevidence. No completed-run capture comparison was found. | AUD-026-003, AUD-026-004, AUD-026-006, AUD-026-018, AUD-026-023 |
| SC-004 | UNVERIFIED | [Three-second exact-state criterion](spec.md#L169); no reconstruction implementation or measured scrub assertion exists in the inspected player/tests. | AUD-026-005, AUD-026-018 |
| SC-005 | UNVERIFIED | [Survey target](spec.md#L170) is at least 80% useful/very useful; no scoped survey/cohort/result accompanies the local evidence. | AUD-026-019 |
| SC-006 | UNVERIFIED | [No-loss reviewer visibility](spec.md#L171); basic in-memory CRUD assertions do not establish durable cross-reviewer results, especially on failure/restart/deletion gaps. | AUD-026-006, AUD-026-013, AUD-026-018, AUD-026-023 |

## Acceptance Scenario Coverage

USn-ASn identifiers are audit-local labels for the original numbered scenarios, not new requirements.
All 22 scenarios are separate. Assertions are read, never executed by this audit.

| Scenario | Status | Original obligation, controlling evidence and assertion coverage | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | IMPLEMENTED | [Creation at 5x](spec.md#L37): [service persistence](../../apps/api/app/services/simulation_service.py#L40) writes current_warp_speed; [create contract](../../tests/contract/test_warp_speed_api.py#L86) asserts 10x and default 1x in a sibling test. Tenant ownership follows R5; initial Run field linkage is separately assessed. | AUD-026-015 |
| US1-AS2 | PARTIAL | [600 simulated seconds at 60 wall seconds](spec.md#L38): [unit tick](../../tests/unit/test_warp_scheduler.py#L100) proves a smaller 60/6 case by fake clock, not the real seeded path, which writes early. | AUD-026-001, AUD-026-018 |
| US1-AS3 | IMPLEMENTED | [Displayed simulated clock](spec.md#L39): [60x arithmetic test](../../tests/unit/test_simulation_clock.py#L74) asserts 1800 after 30 wall seconds; [UI](../../apps/web/src/components/simulation-server-clock.tsx#L85) displays server current_sim_seconds. | AUD-026-017 |
| US1-AS4 | PARTIAL | [Pause at 2x preserves time/halts signals](spec.md#L40): [clock test](../../tests/unit/test_simulation_clock.py#L48) covers 5x pause; [tick pause test](../../tests/unit/test_warp_scheduler.py#L125) covers a direct call, not the loop or chat-counter path. | AUD-026-001, AUD-026-018 |
| US1-AS5 | PARTIAL | [Resume without gaps/duplicates](spec.md#L41): [clock resume test](../../tests/unit/test_simulation_clock.py#L81) covers arithmetic; [resume service](../../apps/api/app/services/simulation_service.py#L150) does not restart delivery. | AUD-026-001, AUD-026-002 |
| US2-AS1 | PARTIAL | [5x to 1x from current time](spec.md#L55): [change_speed](../../apps/api/app/services/simulation_clock_service.py#L71) accumulates old speed correctly; no connected future-delivery assertion across that transition. | AUD-026-001, AUD-026-002, AUD-026-018 |
| US2-AS2 | PARTIAL | [1800 to 1860 at 24x in 2.5 seconds](spec.md#L56): [delay formula](../../apps/api/app/services/warp_scheduler.py#L109) expresses this, but no actual seed-to-delivery test or measured result covers it. | AUD-026-001, AUD-026-018 |
| US2-AS3 | PARTIAL | [No loss/duplicates/order changes](spec.md#L57): [cursor write after signal](../../apps/api/app/services/warp_scheduler.py#L151) has no lease fencing/idempotent commit; same-object tests miss restarts/races. | AUD-026-002, AUD-026-006 |
| US3-AS1 | PARTIAL | [Eligible Completed/Archived link](spec.md#L71): [link condition](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L449) exists, but Completed is not a tenant state and stop leaves local Archiving. | AUD-026-007, AUD-026-021 |
| US3-AS2 | PARTIAL | [Deny nonparticipant/controller](spec.md#L72): [stranger 403 test](../../tests/contract/test_playback_api.py#L155) is real source evidence; post-archive enrollment changes the audience and alternate history routes lack the same guard. | AUD-026-007 |
| US3-AS3 | PARTIAL | [Chronological replay](spec.md#L73): [player advancement/filter](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L60) exists, but zero chat offsets, appended annotations sorted by sequence and reverse/last-100 metadata display do not faithfully reconstruct chronology/state. | AUD-026-004, AUD-026-005, AUD-026-006 |
| US3-AS4 | IMPLEMENTED | [Pause and display position](spec.md#L74): [controls callback](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L164) clears isPlaying; effect cleanup cancels RAF, and controls format current time. No UI execution result is implied. | AUD-026-018 |
| US3-AS5 | MISSING | [State at arbitrary scrub point](spec.md#L75): [onScrub](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L90) only assigns a scalar; no reducer consumes the available snapshot client. | AUD-026-005 |
| US3-AS6 | IMPLEMENTED | [1/2/5/10 playback speed](spec.md#L76): [speed radios](../../apps/web/src/components/playback-controls.tsx#L49) feed the RAF multiplier. | AUD-026-018 |
| US3-AS7 | PARTIAL | [Stop and inform at end](spec.md#L77): [end clamp](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L68) stops; no ended message or restart state. | AUD-026-010 |
| US4-AS1 | PARTIAL | [0,300,600,3600 to 0,30,60,360](spec.md#L91): [scheduler formula](../../apps/api/app/services/warp_scheduler.py#L109) is correct locally; actual seeding bypasses it. No exact four-offset assertion exists. | AUD-026-001, AUD-026-018 |
| US4-AS2 | PARTIAL | [Multisource relative order](spec.md#L92): [ordering test](../../tests/unit/test_warp_scheduler.py#L144) asserts [0,15,30] from three IDs but uses no distinct source IDs, equal-time cases or live worker. | AUD-026-001, AUD-026-002, AUD-026-018 |
| US4-AS3 | PARTIAL | [1x identity schedule](spec.md#L93): [identity test](../../tests/unit/test_warp_scheduler.py#L135) asserts only one calculated delay; production seed writes every offset immediately. | AUD-026-001, AUD-026-018 |
| US4-AS4 | PARTIAL | [Recalculate only future signals](spec.md#L94): [update hook](../../apps/api/app/services/warp_scheduler.py#L243) leaves cursor untouched, but no active delivery loop or restart/boundary assurance exists. | AUD-026-001, AUD-026-002 |
| US5-AS1 | PARTIAL | [Save at current offset with reviewer](spec.md#L108): [panel submit](../../apps/web/src/components/playback-annotation-panel.tsx#L37) and author OID creation exist; successful response does not guarantee durable storage. | AUD-026-013, AUD-026-015 |
| US5-AS2 | PARTIAL | [Other reviewer sees notes in position](spec.md#L109): [mount fetch](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L30) and markers exist; pagination/storage gaps prevent all-notes assurance. | AUD-026-006, AUD-026-013 |
| US5-AS3 | IMPLEMENTED | [Annotation indicator without auto-pause](spec.md#L110): [yellow annotation marker](../../apps/web/src/components/playback-timeline.tsx#L13) is positioned by offset; no annotation handler pauses the player. | AUD-026-018 |

## Clarifications and Edge Cases

CL-01..12 and EC-01..06 follow the original document order and are audit-local labels.

| Item | Status | Evidence and disposition | Follow-up |
| --- | --- | --- | --- |
| CL-01 | PARTIAL | [Independent chat pace](spec.md#L12): [controller turn path](../../apps/api/app/services/simulation/controller_service.py#L324) does not scale response speed, but recordings default to zero offset. | AUD-026-004 |
| CL-02 | PARTIAL | [Original participants/controller](spec.md#L13): current membership checks work; original audience is not frozen. | AUD-026-007 |
| CL-03 | PARTIAL | [Author-only edit/delete](spec.md#L14): server compares OID; current reviewer UI identity is wrong. | AUD-026-009, AUD-026-013 |
| CL-04 | PARTIAL | [Decision-only categories](spec.md#L15): missing signal/alert coverage and recorded navigation contradict the scope. | AUD-026-004 |
| CL-05 | IMPLEMENTED | [Default 1x](spec.md#L16) is asserted by [default contract test](../../tests/contract/test_warp_speed_api.py#L96); old-document compatibility is separate. | AUD-026-012 |
| CL-06 | PARTIAL | [Continue on recording failure/partial](spec.md#L17): catches preserve continuity but no durable partial/gap state follows. | AUD-026-003 |
| CL-07 | IMPLEMENTED | [Wall-clock TTL](spec.md#L18): [expires_at computation](../../packages/domain/src/domain/models/simulation_tenant.py#L96) uses created_at plus ttl_hours, not warp; [expiry query](../../apps/api/app/repositories/simulation_repository.py#L155) compares wall time. Auto-archive execution is not verified. | AUD-026-018 |
| CL-08 | PARTIAL | [Old empty playback](spec.md#L19): none default exists, but empty UI omits a timeline and Completed data has no model mapping. | AUD-026-007, AUD-026-010 |
| CL-09 | PARTIAL | [Refresh/re-entry sharing, no push](spec.md#L20): fresh page fetch reloads annotations; durability/pagination gaps prevent complete sharing. No real-time push is required. | AUD-026-006, AUD-026-013 |
| CL-10 | PARTIAL | [100/s deployment default](spec.md#L21): scheduler constructor defaults to 100 but route factory does not accept deployment configuration. | AUD-026-011 |
| CL-11 | CONFLICT | [10-second configurable lag](spec.md#L22) and R6 conflict with [T023 five-second banner](tasks.md#L139); current client hard-codes >=10 while server uses >10. | AUD-026-011, AUD-026-015 |
| CL-12 | IMPLEMENTED | [Survey replaces 40% time reduction](spec.md#L23) explicitly defines the new measure; actual >=80% outcome remains UNVERIFIED in SC-005. | AUD-026-019 |
| EC-01 | PARTIAL | [Dense signals](spec.md#L116): burst loop exists; pending queue visibility/configuration/failure backoff and actual loop wiring are incomplete. | AUD-026-001, AUD-026-011 |
| EC-02 | PARTIAL | [Delivery at speed-change instant](spec.md#L117): due calculation and speed update read/write independently; old-speed boundary is not serialized or asserted. | AUD-026-002 |
| EC-03 | PARTIAL | [Corrupt/missing data gaps](spec.md#L118): [list_events](../../apps/api/app/repositories/simulation_event_repository.py#L150) validates the whole result inside one catch and returns [] on a malformed item, discarding good rows too. No precise gap display exists. | AUD-026-003, AUD-026-005 |
| EC-04 | PARTIAL | [Ineligible annotation denied](spec.md#L119): [create stranger test](../../tests/contract/test_playback_api.py#L320) asserts 403, but post-completion membership and update/delete lifecycle are not guarded consistently. | AUD-026-007 |
| EC-05 | PARTIAL | [Independent concurrent playback](spec.md#L120): player position/speed live in local React state; shared annotations reload on mount, but sequence/concurrent durability guarantees are incomplete. | AUD-026-006, AUD-026-013, AUD-026-023 |
| EC-06 | PARTIAL | [Zero recorded events](spec.md#L121): explanatory text exists, but [early return](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L116) removes the required empty timeline and any partial warning. | AUD-026-010 |

## Assumptions and Amendments

ASM-01..08 label the eight unnumbered assumptions; META-01 labels the canonical scope bullet.
No deferred country capability is treated as a missing implementation, and no scope promotion is authorized.

| Item | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| ASM-01 | IMPLEMENTED | [Offset-based templates](spec.md#L175) are represented by [nonnegative timeline entries](../../packages/domain/src/domain/models/scenario_template.py#L12) with sorted-order validation. Actual scheduling remains FR-004. | - |
| ASM-02 | PARTIAL | [Run/scenario compression foundation](spec.md#L176): [Run field](../../packages/domain/src/domain/models/simulation_run.py#L23) and [Scenario field](../../packages/domain/src/domain/models/simulation_scenario.py#L23) remain, but create_tenant only allocates IDs and persists tenant warp; it does not set a corresponding Run initial ratio. | AUD-026-015 |
| ASM-03 | PARTIAL | [Read-only review](spec.md#L177): player has no chat/tool controls, but terminal simulation mutation remains reachable through chat/log routes. | AUD-026-007 |
| ASM-04 | PARTIAL | [Retention until deletion](spec.md#L178): archive retains data, but deletion neither purges it nor makes playback unavailable. | AUD-026-008 |
| ASM-05 | IMPLEMENTED | [Fixed speeds only](spec.md#L179): shared validator normalizes only the enumerated values; no arbitrary warp selector exists. | - |
| ASM-06 | PARTIAL | [Configurable 100/s](spec.md#L180): default exists; deployment capacity tuning and validated configuration do not reach the factory. | AUD-026-011 |
| ASM-07 | PARTIAL | [Natural chat pace plus simulated timestamps](spec.md#L181): pace remains independent, but turn timestamps use the zero default. | AUD-026-004 |
| ASM-08 | IMPLEMENTED | [Wall-clock ttl_hours/expires_at](spec.md#L182): model expiry and expiry query do not use warp. Runtime auto-archive and controller understanding are unverified. | AUD-026-018, AUD-026-019 |
| PER-070 | UNVERIFIED | [AIIMS persona references](spec.md#L189) are authored and labeled validated, but no spec-026 SME/practitioner/date record is supplied; [persona contract](../027-spec-hardening/contracts/persona-profile.md#L15) requires named validation evidence. | AUD-026-020 |
| PER-071 | UNVERIFIED | [Technical actor catalogue reference](spec.md#L190) is authored, not evidence of performed actor consultation or persona validation for this change. | AUD-026-020 |
| PER-072 | IMPLEMENTED | [PH/JP/BD placeholder](spec.md#L191) explicitly defers activation pending D-009 and SME validation. Placeholder authorship is supported; approval/validation outcomes are not claimed. | AUD-026-020 |
| HYP-024 | PARTIAL | [Hypothesis/falsification text](spec.md#L197) exists, but its stub is missing and the [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1) is portfolio-wide. Actual consultation and improvement remain UNVERIFIED. | AUD-026-020 |
| SCP-078 | IMPLEMENTED | [Country calibration deferred](spec.md#L205) names decision, regulatory/data-sharing and responsible-reviewer preconditions. Their clearance is not evidenced or assumed. | - |
| SCP-079 | IMPLEMENTED | [Constitutional scope boundary](spec.md#L206) is authored; this audit makes no constitutional changes and does not treat that sentence as a performed constitutional review. | - |
| SCP-080 | IMPLEMENTED | [Arbitration/defers-to scope](spec.md#L207) names product-owner governance and specs 018/008 authority. No cross-spec capability is reassigned here. | - |
| SCP-081 | IMPLEMENTED | [Meta designation](spec.md#L208) and the canonical bullet satisfy the [meta flag contract](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L13). | - |
| META-01 | IMPLEMENTED | [Single canonical bullet](spec.md#L201) names enabling ownership for specs 001,020,021,023, not capstone outcome ownership by spec 026. | - |
| HIST-SC005 | SUPERSEDED | Only the historical 40% time-reduction target is explicitly replaced by [clarification 12](spec.md#L23). No original task ID is marked SUPERSEDED merely because code or contracts differ. | - |

## Original Task Matrix

Every original checkbox is `[ ]`: 56 numeric IDs plus T001a, for 57 rows. Status is determined from
the inspected behavior, not the checkbox. Related gaps can remain even when a narrowly scoped artifact
task is IMPLEMENTED. No original task is treated as implicitly SUPERSEDED.

| Original task | Original state | Status | Concrete existing evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [ ] | IMPLEMENTED | [Constants and validation](../../packages/domain/src/domain/models/warp_constants.py#L11) provide all six allowed speeds, four playback speeds, default 1.0 and ValueError for invalid values; immutable tuples preserve the requested values. | - |
| T001a | [ ] | PARTIAL | [Relocated container/index definition](../../infra/bicep/main.bicep#L158) supplies /tenant_id and both indexes, but [configured entry point](../../azure.yaml#L8) points elsewhere. Provisioning and What-If evidence remain UNVERIFIED. | AUD-026-014 |
| T002 | [ ] | IMPLEMENTED | [WarpSpeedChange](../../packages/domain/src/domain/models/warp_speed_change.py#L10) declares required fields and ConfigDict(frozen=True). | - |
| T003 | [ ] | IMPLEMENTED | [Co-located domain models](../../packages/domain/src/domain/models/simulation_event.py#L29) implement events, snapshots and cursor fields/defaults; extra ui_log scope is assessed under FR-010, not mistaken for missing models. | AUD-026-004 |
| T004 | [ ] | PARTIAL | [Tenant extension](../../packages/domain/src/domain/models/simulation_tenant.py#L70) supplies fields, computed property, history and validator, but no legacy clock migration; elapsed compatibility semantics conflict across input documents. | AUD-026-012, AUD-026-015 |
| T005 | [ ] | PARTIAL | [Event repository](../../apps/api/app/repositories/simulation_event_repository.py#L43) implements requested operations/fallback, but sequences, cursor paging and hidden storage errors defeat durability. Annotation lookup uses event id rather than the specified payload annotation_id. | AUD-026-003, AUD-026-006, AUD-026-013, AUD-026-015, AUD-026-023 |
| T006 | [ ] | MISSING | [Required export task](tasks.md#L60) names an initializer that does not exist; scoped domain initializer search found no relocated exports. [Defining modules](../../packages/domain/src/domain/models/simulation_event.py#L29) are imported directly instead. | AUD-026-016 |
| T007 | [ ] | IMPLEMENTED | [Clock service](../../apps/api/app/services/simulation_clock_service.py#L32) returns copies, validates speed and pause/start preconditions, accumulates intervals and records speed history; clock ownership persists through the service. | - |
| T008 | [ ] | PARTIAL | [Recorder](../../apps/api/app/services/simulation_event_recorder.py#L48) has helpers and snapshot triggers, but local health is not persisted, repository failures are hidden and snapshots contain only last-event metadata. | AUD-026-003, AUD-026-004, AUD-026-005, AUD-026-023 |
| T009 | [ ] | PARTIAL | [Nine clock tests](../../tests/unit/test_simulation_clock.py#L40) assert arithmetic/history/resume/errors; explicit pause cases cover 5x only, not the requested 1x and 60x variants. No execution is claimed. | AUD-026-012, AUD-026-018 |
| T010 | [ ] | PARTIAL | [Seven recorder tests](../../tests/unit/test_event_recorder.py#L21) assert sequence/payload/threshold/count/time triggers, but failure injection bypasses the real repository, logs and complete assistant payload are not asserted, and snapshots are not checked for state. | AUD-026-003, AUD-026-004, AUD-026-005, AUD-026-018 |
| T011 | [ ] | PARTIAL | [Warp contract tests](../../tests/contract/test_warp_speed_api.py#L86) cover create/default/invalid/read/pause/resume/clock; most timer checks only assert key presence, not server-owned values or all-response legacy compatibility. | AUD-026-012, AUD-026-015, AUD-026-018 |
| T012 | [ ] | PARTIAL | [Scheduler tests](../../tests/unit/test_warp_scheduler.py#L75) cover delay/tick/pause/order and same-instance cursor reads; no loop throttle, restart, resume, distinct-source/equal-offset or failure-boundary assertions. | AUD-026-001, AUD-026-002, AUD-026-011, AUD-026-018 |
| T013 | [ ] | MISSING | [Original lifecycle test obligation](tasks.md#L105) has no file or matching relocated lifecycle assertions in searched unit/integration/simulation/API test scopes; [direct scheduler tests](../../tests/unit/test_warp_scheduler.py#L100) do not create/seed/run/archive through the API. | AUD-026-001, AUD-026-018 |
| T014 | [ ] | PARTIAL | [WarpScheduler](../../apps/api/app/services/warp_scheduler.py#L45) has local timing/cursor/loop helpers, but no production loop caller, durable timeline recovery, conditional lease ownership or retry-safe signal/cursor acknowledgement. | AUD-026-001, AUD-026-002, AUD-026-011 |
| T015 | [ ] | IMPLEMENTED | [Create service](../../apps/api/app/services/simulation_service.py#L40) accepts/validates warp, writes the tenant, transitions Active, starts clock, persists and records state change. Full recording health is separately defective under FR-010a. | AUD-026-003 |
| T016 | [ ] | IMPLEMENTED | [Lifecycle methods](../../apps/api/app/services/simulation_service.py#L131) remove client elapsed parameters, compute server time on pause/archive, resume the clock, persist and record state transitions. Delivery-loop wiring and old-document behavior are separate gaps. | AUD-026-001, AUD-026-012 |
| T017 | [ ] | PARTIAL | [Seeder](../../apps/api/app/services/scenario_seeding_service.py#L30) accepts initial warp and initializes scheduler, but writes signals immediately; replay_realtime retains sequential absolute-offset sleeps and injected recorder is unused. | AUD-026-001, AUD-026-004 |
| T018 | [ ] | PARTIAL | [Simulation routes](../../apps/api/app/api/routes/simulations.py#L83) add warp and server clock fields, accept empty timer bodies and ignore client elapsed. Create/list omit the promised legacy elapsed field; archive and response-type contracts disagree. | AUD-026-012, AUD-026-015, AUD-026-017 |
| T019 | [ ] | PARTIAL | [Tenant CRUD](../../apps/api/app/repositories/simulation_repository.py#L52) serializes new fields. Cursor methods were relocated to [event repository](../../apps/api/app/repositories/simulation_event_repository.py#L285), so not MISSING, but the container/partition contract differs and recovery is incomplete. | AUD-026-002, AUD-026-014, AUD-026-015 |
| T020 | [ ] | PARTIAL | [Warp component](../../apps/web/src/components/simulation-warp-controls.tsx#L10) renders six highlighted/disabled choices but owns tenant API calls instead of the prescribed controlled props and is not reused by creation. | AUD-026-009 |
| T021 | [ ] | PARTIAL | [Server clock](../../apps/web/src/components/simulation-server-clock.tsx#L16) polls each second and renders time/warp/paused state; no interpolation or clockPaused-driven lifecycle polling. | AUD-026-017 |
| T022 | [ ] | PARTIAL | [Creation form](../../apps/web/src/app/simulations/create/page.tsx#L29) defaults to 1 and sends warp_speed, but uses duplicate inline controls rather than the required shared component. Functional creation is credited under FR-002. | AUD-026-009 |
| T023 | [ ] | CONFLICT | [Dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L238) consumes pause/resume accumulated time and uses server clock, but stop ignores returned Archived/accumulated state. Original >5-second banner contradicts FR-008/R6's configurable >10 seconds. | AUD-026-011, AUD-026-015, AUD-026-017, AUD-026-021 |
| T024 | [ ] | PARTIAL | [API client](../../apps/web/src/lib/api/simulations.ts#L53) adds warp, timer/clock calls and empty bodies, but clock response requires absent fields and omits the authoritative threshold contract. | AUD-026-015 |
| T025 | [ ] | IMPLEMENTED | [List page](../../apps/web/src/app/simulations/page.tsx#L88) displays warp and pause/resume/archive calls use tenant ID only; defaults to 1 for old summaries. | - |
| T026 | [ ] | CONFLICT | [Endpoint tests](../../tests/contract/test_warp_speed_api.py#L151) cover 400/403 and prior/new speeds; [Paused success test](../../tests/contract/test_warp_speed_api.py#L186) directly contradicts original non-Active 409 while matching the amended contract. Terminal 409 assertion is absent. | AUD-026-015, AUD-026-018 |
| T027 | [ ] | PARTIAL | [Clock rapid-transition assertion](../../tests/unit/test_simulation_clock.py#L116) checks exact accumulated time/history, but no test changes scheduler speed after prior delivery and proves only remaining entries are rescheduled. | AUD-026-002, AUD-026-018 |
| T028 | [ ] | CONFLICT | [Service](../../apps/api/app/services/simulation_service.py#L169) enforces creator, persists speed/history/event; [route](../../apps/api/app/api/routes/simulations.py#L376) supplies the relocated scheduler hook. It permits Paused contrary to original Active-only wording. | AUD-026-015 |
| T029 | [ ] | CONFLICT | [Warp route](../../apps/api/app/api/routes/simulations.py#L356) validates speed and maps errors; service permits Paused, so original every-non-Active 409 is not its contract. No explicit task replacement is cited. | AUD-026-015 |
| T030 | [ ] | PARTIAL | [Dashboard warp control](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L320) calls change and updates state but is shown to all participants and remains enabled while Paused; controller-only visibility is absent. | AUD-026-009, AUD-026-015 |
| T031 | [ ] | PARTIAL | [changeWarpSpeed](../../apps/web/src/lib/api/simulations.ts#L168) issues the expected request, but [return type](../../apps/web/src/lib/api/simulations.ts#L103) declares previous_warp_speed and extra clock fields instead of actual previous_speed response. | AUD-026-015 |
| T032 | [ ] | PARTIAL | [Playback contract suite](../../tests/contract/test_playback_api.py#L120) checks ordering, after_seq, annotation filter and stranger denial. It does not assert multi-page has_more, nearest-before snapshot, exact empty []/none or partial recording. | AUD-026-003, AUD-026-005, AUD-026-006, AUD-026-007, AUD-026-018 |
| T033 | [ ] | PARTIAL | Planned unit filename is absent, but [relocated service-through-route tests](../../tests/contract/test_playback_api.py#L120) cover some ordering/access and a snapshot-list case. Nearest-state, exact empty and partial-status assertions remain missing. | AUD-026-003, AUD-026-005, AUD-026-006, AUD-026-018 |
| T034 | [ ] | MISSING | [Recording-to-playback integration obligation](tasks.md#L208) has no matching test in searched integration/simulation/API scopes; [manually seeded events](../../tests/contract/test_playback_api.py#L101) bypass live writes, chat and completion. | AUD-026-004, AUD-026-005, AUD-026-018 |
| T035 | [ ] | PARTIAL | [Playback service](../../apps/api/app/services/playback_service.py#L43) returns requested collections/metadata and participant checks; pagination assumes dense sequence numbers and lifecycle/original audience is not enforced. | AUD-026-006, AUD-026-007 |
| T036 | [ ] | IMPLEMENTED | [Playback router](../../apps/api/app/api/routes/simulation_playback.py#L22) wires GET events/snapshots with the named params/services and [registration](../../apps/api/app/api/router.py#L70). Service/query correctness is tracked independently. | AUD-026-005, AUD-026-006, AUD-026-007 |
| T037 | [ ] | IMPLEMENTED | [Router registration](../../apps/api/app/api/router.py#L37) imports simulation_playback_router and includes it at line 70; this is actual registration, not an unused file. | - |
| T038 | [ ] | PARTIAL | [Playback client](../../apps/web/src/lib/api/simulation-playback.ts#L29) has no-store fetch and all five operations. Annotations use generic PlaybackEvent rather than the specified PlaybackAnnotation shape; snapshot helper is unused by the page. | AUD-026-005, AUD-026-015 |
| T039 | [ ] | PARTIAL | [Timeline](../../apps/web/src/components/playback-timeline.tsx#L20) renders colored markers, position and click/arrow scrub; no drag handle behavior, interval labels or payload summary tooltips. | AUD-026-024 |
| T040 | [ ] | IMPLEMENTED | [Playback controls](../../apps/web/src/components/playback-controls.tsx#L13) implement play/pause, four speed choices, HH:MM:SS current/total and percentage. Runtime UI behavior remains unexecuted. | AUD-026-018 |
| T041 | [ ] | PARTIAL | [Client player page](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L15) loads paginated events and manages local controls; it is not the planned server/client split, never loads snapshots/reconstructs state and returns before an empty timeline. | AUD-026-005, AUD-026-010 |
| T042 | [ ] | PARTIAL | [Review Playback link](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L449) is gated by status after participant-checked detail fetch; Completed is not supported by the model and stop leaves the UI Archiving until reload. | AUD-026-007, AUD-026-021 |
| T043 | [ ] | PARTIAL | [Shared recorder wiring](../../apps/api/app/api/routes/simulation_chat.py#L45) and [completed-turn interception](../../apps/api/app/services/simulation/controller_service.py#L223) exist, but actual callers omit sim_seconds; tool-role turns are mislabeled as assistant and tool latency is default zero. | AUD-026-004 |
| T044 | [ ] | PARTIAL | [Annotation tests relocated into playback contracts](../../tests/contract/test_playback_api.py#L233) cover all seven basic CRUD/access cases; they assert the divergent nested author_oid shape and not durable rereads, exact offsets or contract author/name/identity fields. | AUD-026-013, AUD-026-015, AUD-026-018 |
| T045 | [ ] | PARTIAL | [Annotation service](../../apps/api/app/services/annotation_service.py#L35) enforces create membership and author-only writes, but lacks prescribed ann-id/name/payload fields, service-level length validation and checked durable delete result. | AUD-026-007, AUD-026-013, AUD-026-015, AUD-026-023 |
| T046 | [ ] | PARTIAL | [Annotation endpoints](../../apps/api/app/api/routes/simulation_playback.py#L145) implement methods/statuses and route text validation; response shape differs from contract and writes can acknowledge failed persistence. | AUD-026-013, AUD-026-015 |
| T047 | [ ] | PARTIAL | [Annotation panel](../../apps/web/src/components/playback-annotation-panel.tsx#L96) supplies limit, timestamp, author OID, edit/save/cancel/delete; it lists all notes rather than near-current notes, lacks author_name, and receives the wrong reviewer identity. | AUD-026-009, AUD-026-015 |
| T048 | [ ] | PARTIAL | [Page callbacks](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L193) wire CRUD and update local events/markers; they do not refetch all events after mutations, cannot expose other reviewers' intervening notes and trust false-success writes. | AUD-026-006, AUD-026-009, AUD-026-013 |
| T049 | [ ] | UNVERIFIED | [Requested regression execution](tasks.md#L289) has no supplied revision-specific results; [CI declaration](../../.github/workflows/ci.yml#L131) is authored configuration, not proof of a run, and omits new unit test selection. | AUD-026-012, AUD-026-018 |
| T050 | [ ] | UNVERIFIED | [Default test](../../tests/contract/test_warp_speed_api.py#L96) supports one assertion, but no performed compatibility review is evidenced; legacy records and all-response elapsed fields have concrete blockers. | AUD-026-012, AUD-026-015, AUD-026-018 |
| T051 | [ ] | MISSING | [Clock rendering](../../apps/web/src/components/simulation-server-clock.tsx#L71) only warns at >=10; complete dashboard/list/clock search found no indicator triggered by delivery_lag_seconds>0. Tenant throttle_mode is a different value. | AUD-026-011 |
| T052 | [ ] | MISSING | [List](../../apps/web/src/app/simulations/page.tsx#L65) and [detail header](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L297) render lifecycle/warp but no Full/Partial/No Recording badge; source search confirmed playback_status is not displayed there. | AUD-026-003, AUD-026-022 |
| T053 | [ ] | PARTIAL | [New clock/recorder docstrings](../../apps/api/app/services/simulation_clock_service.py#L1) are authored and clients stopped posting elapsed, but [legacy backfill](../../scripts/backfill_simulation_elapsed.py#L20) still deletes the new running anchor and multiple comments/types disagree with behavior. | AUD-026-012, AUD-026-015, AUD-026-017 |
| T054 | [ ] | UNVERIFIED | [Quickstart](quickstart.md#L56) is authored but no curl execution evidence exists; participant/case/auth/test-path discrepancies mean it is not a reliable verified walkthrough. | AUD-026-015, AUD-026-018 |
| T055 | [ ] | UNVERIFIED | [Full-suite/coverage request](tasks.md#L307) has no supplied run/coverage artifact tied to reviewed HEAD. No tests were executed by this audit. | AUD-026-018 |
| T056 | [ ] | UNVERIFIED | [Performance request](tasks.md#L310) has no matching 24-hour/speed-change/scrub measurement in the searched test/evidence scopes. Fake clock arithmetic and authored criteria are not performance results. | AUD-026-005, AUD-026-018 |

## Plan and Design Coverage

NFR, DM, ST and PAY labels below are audit-local labels for unnumbered plan/data-model obligations.
R1-R7 retain the original research IDs. File relocation alone is not classified as missing behavior.

| Item | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| NFR-01 | UNVERIFIED | [Timing goals](plan.md#L18): <25 wall minutes at 60x, <5-second pacing change and <3-second scrub are explicit but not measured. SC-001/002/004 account for all three. | AUD-026-018 |
| NFR-02 | PARTIAL | [Burst/lag limits](plan.md#L18) are partly represented in the loop, but deployment configuration and consistent lag semantics are not connected. | AUD-026-011 |
| NFR-03 | PARTIAL | [Hundreds to low-thousands of events](plan.md#L20) motivates snapshots/cursors; list_snapshots fetches all snapshots and the player loads all pages without a state reducer. No representative-scale assertion is present. | AUD-026-005, AUD-026-006, AUD-026-018 |
| NFR-04 | PARTIAL | [Concurrent playback sessions](plan.md#L20): local player state is independent; shared annotations need the sequence/durability fixes, not a new real-time push mechanism. | AUD-026-006, AUD-026-013 |
| NFR-05 | UNVERIFIED | [AU sovereignty/Azure storage](plan.md#L14) is an authored constraint; [active Cosmos location](../../infra/main.bicep#L580) references deployment location. No deployed residency, policy or approval evidence was queried or supplied. | AUD-026-014, AUD-026-019 |
| NFR-06 | IMPLEMENTED | [Hazard-agnostic design](plan.md#L30): scheduler uses generic envelopes and offsets; [template model](../../packages/domain/src/domain/models/scenario_template.py#L31) admits the supported hazard classes. Multi-hazard execution is not implied. | AUD-026-018 |
| NFR-07 | PARTIAL | [Three-runtime plan](plan.md#L8): API/web work is authored; controller hooks are relocated into the API service, not a separate agent helper. Searches of agents/ingestion/runners found no alternate spec-026 recorder or durable delivery worker. | AUD-026-001, AUD-026-004 |
| NFR-08 | UNVERIFIED | [Test and What-If quality gates](plan.md#L39), test-first ordering and reviews are plans; absent end-to-end assertions and performed-run evidence prevent a pass claim. | AUD-026-018, AUD-026-019 |
| R1 | PARTIAL | [Durable dedicated worker decision](research.md#L6): [scheduler](../../apps/api/app/services/warp_scheduler.py#L72) has a cursor but process-local timeline and no production runner/lease fencing. | AUD-026-001, AUD-026-002 |
| R2 | PARTIAL | [Canonical server clock](research.md#L17): new tenant arithmetic is supported; legacy documents/backfill and client lifecycle display still contradict reliable time ownership. | AUD-026-012, AUD-026-017 |
| R3 | PARTIAL | [Append-first coarse boundary recording](research.md#L27): helpers exist, but signal writes bypass capture, chat offsets are zero, ui_log includes navigation and sequences are not concurrent-monotonic. | AUD-026-003, AUD-026-004, AUD-026-023 |
| R4 | PARTIAL | [Client replay plus snapshots](research.md#L38): paginated loading exists; snapshots do not hold state and the player does not use them. | AUD-026-005, AUD-026-006 |
| R5 | PARTIAL | [Tenant canonical / Run initial default](research.md#L48): tenant is authoritative as intended, but corresponding Run initial ratio is not populated by create_tenant. | AUD-026-015 |
| R6 | PARTIAL | [Ordered backlog with configurable 10-second warning](research.md#L58): local loop has ordering/throttle logic, but ownership, reachable delivery and accurate configurable warnings are incomplete. | AUD-026-001, AUD-026-002, AUD-026-011 |
| R7 | PARTIAL | [Co-located annotation decision](research.md#L69): annotations use sim-events as intended; author payload differs, monotonic allocation fails after deletion/concurrency and writes can falsely succeed. | AUD-026-013, AUD-026-015, AUD-026-023 |
| DM-01 | PARTIAL | [SimulationTenant fields/defaults/property](data-model.md#L8) exist in [tenant model](../../packages/domain/src/domain/models/simulation_tenant.py#L75); playback full/partial semantics and backward migration are incomplete. | AUD-026-003, AUD-026-012 |
| DM-02 | PARTIAL | [SimulationRun initial ratio](data-model.md#L27) is retained as a field, but not linked to new tenant-selected speed; SimulationScenario's field also remains unchanged. | AUD-026-015 |
| DM-03 | IMPLEMENTED | [Embedded WarpSpeedChange](data-model.md#L31) is implemented with all fields and immutability in [model](../../packages/domain/src/domain/models/warp_speed_change.py#L10). | - |
| DM-04 | PARTIAL | [SimulationEvent](data-model.md#L42) fields, version and document discriminator exist; promised monotonic sequences, accurate offsets and reachable indexed storage are incomplete. Extra ui_log is not a replacement for required decision categories. | AUD-026-004, AUD-026-014, AUD-026-023 |
| DM-05 | CONFLICT | [Annotation payload](data-model.md#L60) requires annotation_id, author_id/name, text, created_at and updated_at=None; current service writes text/author_oid/created_at only under a generic evt id. | AUD-026-013, AUD-026-015 |
| DM-06 | PARTIAL | [Snapshot cadence and state](data-model.md#L73): recorder triggers at 100 events or >=300 seconds since anchor, with tests for each; state contains only last event rather than signals/alerts/speed/metrics. | AUD-026-005 |
| DM-07 | CONFLICT | [Scheduler cursor store/lease](data-model.md#L86) specifies simulation partitioned by tenant_id; implementation uses sim-events, active simulation partition is scenario_id, and recorded owner/heartbeat is not a lease. | AUD-026-002, AUD-026-014, AUD-026-015 |
| ST-01 | IMPLEMENTED | [Start/resume transition](data-model.md#L128): [clock](../../apps/api/app/services/simulation_clock_service.py#L32) sets last_resumed_at and unpauses; service persists both. | - |
| ST-02 | IMPLEMENTED | [Pause transition](data-model.md#L129): [pause_clock](../../apps/api/app/services/simulation_clock_service.py#L48) accumulates elapsed*warp, clears anchor and pauses. Legacy-state upgrade remains separate. | AUD-026-012 |
| ST-03 | IMPLEMENTED | [Speed transition](data-model.md#L130): [change_speed](../../apps/api/app/services/simulation_clock_service.py#L71) snapshots old speed and resets running anchor; paused-speed addition is documented by the later API contract. | AUD-026-015 |
| ST-04 | PARTIAL | [Archive transition](data-model.md#L131): service pauses/persists then archives, but recorder skips the Active/Paused-to-Archiving decision and UI hard-codes the intermediate status. | AUD-026-004, AUD-026-021 |
| PAY-01 | PARTIAL | [signal_delivered payload](data-model.md#L137) helper supplies all four fields; the actual seed path does not call it. | AUD-026-001, AUD-026-004 |
| PAY-02 | PARTIAL | [chat_turn_user payload](data-model.md#L142) uses sequence and 200-char preview as specified; actual simulated offset is zero because callers omit it. | AUD-026-004 |
| PAY-03 | PARTIAL | [chat_turn_assistant payload](data-model.md#L147) helper supports tool_calls; actual assistant calls omit that list and tool-role turns map to assistant type. | AUD-026-004 |
| PAY-04 | CONFLICT | [tool_invocation payload](data-model.md#L152) requires success/error/timeout and measured latency; actual call sites use ok/error and default latency_ms=0. | AUD-026-004, AUD-026-015 |
| PAY-05 | PARTIAL | [state_change payload](data-model.md#L157) shape is implemented; complete archive transition recording is absent. | AUD-026-004 |
| PAY-06 | IMPLEMENTED | [warp_speed_change payload](data-model.md#L162) old/new fields are emitted by [service](../../apps/api/app/services/simulation_service.py#L181) and tested at helper level. | - |
| PAY-07 | CONFLICT | [annotation payload](data-model.md#L167) differs from current nested author_oid/generic event identity and lacks explicit updated_at=None/name. | AUD-026-015 |

## API Contract Accounting

Five modified plus seven new original contract endpoints are accounted for. Additional log-entry and
metadata routes are inspected where they affect this feature; their existence does not supersede the contract.

| Contract item | Status | Expected versus actual source | Follow-up |
| --- | --- | --- | --- |
| API-M01 | CONFLICT | [POST create](contracts/api-contracts.md#L8) documents clock_paused=true, while [create service](../../apps/api/app/services/simulation_service.py#L89) starts it false in Active. Warp/default validation exists; T018's all-response elapsed field is also absent. | AUD-026-012, AUD-026-015 |
| API-M02 | IMPLEMENTED | [GET detail](contracts/api-contracts.md#L26) mirrors live current_sim_seconds into elapsed_seconds and includes canonical clock/playback fields through [_tenant_public_view](../../apps/api/app/api/routes/simulations.py#L56). Task/data-model accumulated-time wording conflicts separately. | AUD-026-012, AUD-026-015 |
| API-M03 | IMPLEMENTED | [POST pause](contracts/api-contracts.md#L42): [handler](../../apps/api/app/api/routes/simulations.py#L284) accepts no/empty body and returns Paused plus server accumulated/legacy time. Existing contract checks only field presence. | AUD-026-018 |
| API-M04 | IMPLEMENTED | [POST resume](contracts/api-contracts.md#L58): [handler](../../apps/api/app/api/routes/simulations.py#L305) returns Active, accumulated time, current speed and elapsed without client authority. | AUD-026-018 |
| API-M05 | CONFLICT | [POST archive](contracts/api-contracts.md#L75) says Archiving; [service](../../apps/api/app/services/simulation_service.py#L191) completes Archived before returning and the [client handler](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L263) assumes Archiving. | AUD-026-015, AUD-026-021 |
| API-N01 | IMPLEMENTED | [POST warp-speed amended purpose](contracts/api-contracts.md#L93) allows Active/Paused, creator only; [service/route](../../apps/api/app/api/routes/simulations.py#L356) implements 400/403/409 and old/new values. Original Active-only task wording is still CONFLICT, not silently retired. | AUD-026-015 |
| API-N02 | PARTIAL | [GET playback/events](contracts/api-contracts.md#L126) has filter/cursor/limit/metadata but [has_more](../../apps/api/app/services/playback_service.py#L64) is wrong for gapped sequences and original-terminal audience is not enforced. | AUD-026-006, AUD-026-007 |
| API-N03 | PARTIAL | [GET snapshots](contracts/api-contracts.md#L170) returns nearest at/before via [repository filter](../../apps/api/app/repositories/simulation_event_repository.py#L277), but reads all snapshots, hides query/corruption failure and returns incomplete state. | AUD-026-003, AUD-026-005 |
| API-N04 | CONFLICT | [POST annotation](contracts/api-contracts.md#L194) expects flat ann-id/author/name/time/text; [route](../../apps/api/app/api/routes/simulation_playback.py#L145) returns generic event with nested payload. | AUD-026-013, AUD-026-015 |
| API-N05 | CONFLICT | [PUT annotation](contracts/api-contracts.md#L219) expects flat annotation_id/text/updated_at; current route returns a generic event and may acknowledge failed persistence. | AUD-026-013, AUD-026-015 |
| API-N06 | PARTIAL | [DELETE annotation](contracts/api-contracts.md#L242) returns author-only 204, but [service](../../apps/api/app/services/annotation_service.py#L76) ignores a failed delete result. | AUD-026-013 |
| API-N07 | PARTIAL | [GET clock](contracts/api-contracts.md#L255) returns the documented timing/lag fields; configuration is not authoritative end to end and [client type](../../apps/web/src/lib/api/simulations.ts#L85) requires additional fields absent from the response. | AUD-026-011, AUD-026-015, AUD-026-017 |

Quickstart's unit command references missing test_playback_service.py; its two integration paths are
not present; annotation contract tests are consolidated rather than present at test_annotation_api.py.
The corrected future commands in remediation entries use existing homes, and proposed paths are
explicitly labeled. Its five curl scenarios are authored instructions, not executed evidence; the
create body and auth setup require AUD-026-015, terminal review setup requires AUD-026-007, and smoke
execution/results remain T054 UNVERIFIED. No quickstart command was run in this audit.

## Checklist Accounting

The original [quality checklist](checklists/requirements.md#L1) has 16 checked items. CHK-01..16 follow
their exact original order; original text/state are retained here. Status assesses the assertion, not
whether a named reviewer actually performed the review. That performance has no supplied evidence.

| Checklist item | Original state | Original assertion | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- | --- |
| CHK-01 | [x] | No implementation details (languages, frameworks, APIs) | CONFLICT | [Key entities](spec.md#L157) prescribe clock fields and annotation co-storage as SimulationEvent, so this is not wholly implementation-independent. | AUD-026-015 |
| CHK-02 | [x] | Focused on user value and business needs | IMPLEMENTED | [Training/after-action user stories](spec.md#L27) state controller/reviewer value. This is authored focus, not measured value. | - |
| CHK-03 | [x] | Written for non-technical stakeholders | PARTIAL | [Stories](spec.md#L27) are accessible, but [entity/field assumptions](spec.md#L155) and amendment schema references add technical detail. No readability review is evidenced. | AUD-026-019 |
| CHK-04 | [x] | All mandatory sections completed | IMPLEMENTED | [Scenarios](spec.md#L25), [requirements](spec.md#L123) and [success criteria](spec.md#L162) are all authored. | - |
| CHK-05 | [x] | No [NEEDS CLARIFICATION] markers remain | IMPLEMENTED | Complete [spec](spec.md#L1) has no unresolved marker; absence of markers does not resolve the separate contract contradictions. | - |
| CHK-06 | [x] | Requirements are testable and unambiguous | CONFLICT | [Paused contract](contracts/api-contracts.md#L93) versus [Active-only task](tasks.md#L164), [lag task](tasks.md#L139) and elapsed semantics leave incompatible expectations. | AUD-026-011, AUD-026-015 |
| CHK-07 | [x] | Success criteria are measurable | IMPLEMENTED | [Six criteria](spec.md#L166) include explicit timing, completeness, survey percentage and durability goals; execution/results are unverified. | AUD-026-018, AUD-026-019 |
| CHK-08 | [x] | Success criteria are technology-agnostic (no implementation details) | IMPLEMENTED | [SC-001..006](spec.md#L166) describe user/system outcomes rather than framework-specific implementations. | - |
| CHK-09 | [x] | All acceptance scenarios are defined | IMPLEMENTED | [Five story sections](spec.md#L27) contain 22 separately mapped scenarios. This does not assert their passing execution. | - |
| CHK-10 | [x] | Edge cases are identified | IMPLEMENTED | [Six edge cases](spec.md#L114) cover dense bursts, transition timing, gaps, unauthorized notes, concurrent reviewers and empty history. | - |
| CHK-11 | [x] | Scope is clearly bounded | IMPLEMENTED | [Scope section](spec.md#L199) identifies enabling ownership, country deferrals, constitutional boundary and external authority. | - |
| CHK-12 | [x] | Dependencies and assumptions identified | IMPLEMENTED | [Assumptions](spec.md#L173) and [task dependencies](tasks.md#L315) are authored. Correctness of every assumption is separately assessed. | - |
| CHK-13 | [x] | All functional requirements have clear acceptance criteria | PARTIAL | [US5 scenarios](spec.md#L108) do not explicitly enumerate edit/delete denial, while degradation and deployment-threshold behavior are distributed across edges/FRs/tasks with remaining conflicts. | AUD-026-015, AUD-026-018 |
| CHK-14 | [x] | User scenarios cover primary flows | IMPLEMENTED | [US1..US5](spec.md#L27) cover create, dynamic speed, playback, ingestion and annotation journeys. | - |
| CHK-15 | [x] | Feature meets measurable outcomes defined in Success Criteria | UNVERIFIED | [Checked claim](checklists/requirements.md#L29) has no associated execution, performance or survey evidence and is contradicted by the source blockers above. | AUD-026-018, AUD-026-019 |
| CHK-16 | [x] | No implementation details leak into specification | CONFLICT | [Entity storage choices](spec.md#L157) and field-level assumptions are implementation detail; repeats CHK-01 rather than proving a second independent review. | AUD-026-015 |

The [first-iteration PASS note](checklists/requirements.md#L34) is an authored assertion, not a dated
review transcript or named sign-off. Notes about fixed speeds and the existing time_compression_ratio
are supported as artifact descriptions; assumptions about their actual integration are covered above.
The checklist's 16 ticks were not changed and none are used as proof of task completion.

## Plan Gate Accounting

All 12 plan gates are authored as PASS, followed by an authored post-phase-1 re-check. These records
are not independently verified reviews, deployments or human approvals. Assessment stays within the
feature's named obligations rather than reopening other specifications or generic platform reviews.

| Gate | Authored result | Evidence status | Scoped evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| PG-01 Primacy of Life | PASS | UNVERIFIED | [Plan claim](plan.md#L28) describes training value; no performed safety/value review accompanies it. | AUD-026-019 |
| PG-02 AIIMS Alignment | PASS | UNVERIFIED | [Plan claim](plan.md#L29) says structure is unchanged; no attributable role/SME review for this feature is supplied. | AUD-026-019, AUD-026-020 |
| PG-03 Multi-Hazard | PASS | UNVERIFIED | [Plan claim](plan.md#L30) has hazard-generic source support, but no executed cross-hazard warp acceptance result. | AUD-026-018 |
| PG-04 Transparency/Auditability | PASS | UNVERIFIED | [Claimed monotonic provenance](plan.md#L31) is undermined by sequence allocation, zero chat times and missing event categories; no review execution record. | AUD-026-004, AUD-026-006 |
| PG-05 Warnings | PASS | UNVERIFIED | [Warning replay claim](plan.md#L32) lacks canonical alert-state replay and a completed review session. | AUD-026-004, AUD-026-005 |
| PG-06 Azure Platform | PASS | UNVERIFIED | [Platform claim](plan.md#L33) is architectural intent; active IaC omits sim-events, and deployed storage was not queried. | AUD-026-014 |
| PG-07 Human in the Loop | PASS | UNVERIFIED | [Controller/read-only claim](plan.md#L34) has creator-only speed checks, but terminal mutation/original audience is not enforced throughout. | AUD-026-007, AUD-026-009 |
| PG-08 Data Sovereignty | PASS | UNVERIFIED | [AU-region claim](plan.md#L35) has no supplied deployed-state/policy approval evidence; no cloud query was allowed. | AUD-026-014, AUD-026-019 |
| PG-09 Privacy | PASS | UNVERIFIED | [OID/no-new-PII claim](plan.md#L36) is not an approval; annotation payload/retention differ and deleted data remains accessible. | AUD-026-007, AUD-026-008, AUD-026-015 |
| PG-10 Interoperability | PASS | UNVERIFIED | [No external API change claim](plan.md#L37) does not resolve response/type and legacy-clock incompatibilities. | AUD-026-012, AUD-026-015 |
| PG-11 Graceful Degradation | PASS | UNVERIFIED | [FR-010a/throttle claim](plan.md#L38) is not established by hidden storage failures, process-local health and incomplete pending-lag behavior. | AUD-026-003, AUD-026-011 |
| PG-12 Quality Gates | PASS | UNVERIFIED | [Test/What-If claim](plan.md#L39) has incomplete tests and no revision-bound execution/What-If review evidence. | AUD-026-014, AUD-026-018, AUD-026-019 |
| PG-POST Post-Phase-1 Re-check | PASS | UNVERIFIED | [Re-check paragraph](plan.md#L41) repeats PASS assertions; it is not an independent signed/dated outcome record and cannot close the identified blockers. | AUD-026-018, AUD-026-019 |

## Original Review and Checkpoint Accounting

RV labels are local accounting labels, not new original task IDs. Primary/consulting role labels and
checkpoints were read completely. They establish an authored plan only; no agent consultation,
human approval or runtime exercise was performed as part of this static audit.

| Review item | Authored instruction or claim | Evidence status | Assessment and follow-up |
| --- | --- | --- | --- |
| RV-01 | [Agent involvement matrix and all Primary/Consult labels](tasks.md#L16) | UNVERIFIED | Assignments exist for software/data/API/QA/UX/security/SRE/solution/observer/IC/principal roles, with infra/compliance participation elsewhere. No invocation/review transcripts for spec 026 are supplied. AUD-026-019/020. |
| RV-02 | [Foundation-ready checkpoint](tasks.md#L85) | UNVERIFIED | Clock helpers exist, but recording health/snapshots are incomplete; authored readiness is not an executed gate. AUD-026-003/005/018. |
| RV-03 | [US1+US4 MVP checkpoint](tasks.md#L148) | UNVERIFIED | Real seeded delivery is not connected; cannot credit a demonstrated MVP from the checkpoint text. AUD-026-001/002/018. |
| RV-04 | [Incident commander: controller UX](tasks.md#L150) | UNVERIFIED | No scoped session/feedback record; visibility, clock and archive-to-playback problems remain. AUD-026-009/017/019. |
| RV-05 | [Observer auditor: signal/state recording](tasks.md#L150) | UNVERIFIED | No observed event-completeness comparison; recorder hooks alone are not review evidence. AUD-026-004/018/019. |
| RV-06 | [Full time-warp checkpoint](tasks.md#L186) | UNVERIFIED | Helper speed changes are authored, but seamless delivery has no connected/asserted worker path. AUD-026-001/002/018. |
| RV-07 | [Incident commander: live speed transitions](tasks.md#L188) | UNVERIFIED | No live exercise timing/usability record is supplied. AUD-026-018/019. |
| RV-08 | [QA: integration no-loss/no-duplication](tasks.md#L188) | UNVERIFIED | No matching lifecycle integration assertions/run were found after relocation search. AUD-026-001/002/018. |
| RV-09 | [Full playback checkpoint](tasks.md#L242) | UNVERIFIED | State reconstruction is absent and event capture incomplete; authored checkpoint does not demonstrate replay fidelity. AUD-026-004/005/018. |
| RV-10 | [Observer auditor: full playback session](tasks.md#L244) | UNVERIFIED | No performed session or feedback; metadata lists do not establish review usefulness. AUD-026-005/019. |
| RV-11 | [Incident commander: after-action flow](tasks.md#L244) | UNVERIFIED | No attributable controller review outcome is supplied. AUD-026-019. |
| RV-12 | [Planning officer: after-action flow](tasks.md#L244) | UNVERIFIED | No attributable planning-officer review outcome is supplied. AUD-026-019. |
| RV-13 | [All stories/full annotation checkpoint](tasks.md#L277) | UNVERIFIED | Basic CRUD exists; false-success storage, wrong reviewer UI identity and sequence gaps prevent claiming completion. AUD-026-006/009/013/018. |
| RV-14 | [Observer auditor: annotation review workflow](tasks.md#L279) | UNVERIFIED | No actual reviewer session or survey is supplied. AUD-026-019. |
| RV-15 | [Security engineer: author-only enforcement](tasks.md#L279) | UNVERIFIED | Contract assertions cover basic nonauthor denial, not a performed security review or full lifecycle/audience matrix. AUD-026-007/009/013/019. |
| RV-16 | [Principal engineer: code/backward-compatibility review](tasks.md#L287) | UNVERIFIED | No review record; legacy clock/backfill and wire-shape conflicts remain. AUD-026-012/015/019. |
| RV-17 | [SRE: operational readiness](tasks.md#L287) | UNVERIFIED | No operational review; durable worker, degradation and deployment prerequisites remain open. AUD-026-002/003/011/014/019. |
| RV-18 | [Compliance auditor: audit compliance](tasks.md#L287) | UNVERIFIED | No scoped compliance sign-off; recording completeness and retention failures are identified without asserting a wider compliance conclusion. AUD-026-004/008/019. |
| RV-19 | [Test-first and dependency ordering](tasks.md#L346) | UNVERIFIED | Current source cannot prove tests failed before implementation, sequence of consultations or historical checkpoint execution. Phase dependencies/MVP strategy are authored instructions, not evidence of their performance. AUD-026-018/019. |

The `Review Playback` UI label is not evidence of a performed review. Likewise, authoring the checklist,
plan, baseline or a test file is not proof of test execution, performance, approval or deployment.
Scope amendments requiring country/SME decisions remain deferred and are not treated as completed.

## Validation Prerequisites and Limits

All commands in remediation entries are **future instructions only**. None were run in this audit.
Python 3.12+ and API/agent/test dependencies must already be installed; use isolated fakes or an explicitly
approved emulator, with environment-sensitive Cosmos clients disabled/injected for offline tests.
Web tests require the declared Node/pnpm workspace dependencies. Proposed test/evidence paths do not
exist yet and must be authored before their commands are meaningful.

The current Playwright configuration starts backend/frontend servers. It was only read; it must not be
executed under this audit authorization. Likewise, Bicep compilation/module restore, cloud What-If,
deployment, external approvals and reviewer surveys require a separate authorized execution context.
The 43 inspected feature-specific test functions, adjacent wiring test and evaluator-idempotency test
are source evidence only. No collected-test count, pass rate, runtime latency or coverage percentage
has been inferred from filenames, comments, fixtures, checked boxes or CI definitions.

## Report Validation and Remaining Blockers

- Text-only checks matched all 57 task IDs and original unchecked states, including T001a; every task
  row has an allowed status and an existing evidence link. Task counts are 10/33/5/4/5 as summarized above.
- Coverage checks matched all 33 original FR/SC/PER/HYP/SCP IDs, the 22 individual acceptance scenarios,
  12 clarifications, six edge cases, eight assumptions and the canonical meta bullet. The historical
  SC-005 target has its own explicitly cited replacement, not an invented original-task supersession.
- Checklist checks preserved all 16 original assertion texts and checked states. Additional accounting
  covers eight unnumbered NFR groups, seven research decisions, seven entities, four clock transitions,
  seven payloads, 12 API endpoints, 12 plan gates plus re-check, and 19 review/checkpoint items.
- All 24 follow-ups are unique, unchecked and include obligations, expected/observed/impact, owner/search
  scope, developer instructions, compatibility/dependencies, tester cases, future commands and completion
  criteria. References are reconciled to task/requirement/amendment coverage; proposed paths are not evidence links.
- Local Markdown evidence targets and 1-based line bounds were text-validated; editor diagnostics were
  checked on this report only. No product tests/builds/imports, servers, browsers, cloud operations,
  package installations, approvals or deployments were performed.
- Execution blockers remain: disconnected/durable scheduler work, incomplete recording and replay state,
  lifecycle/audience/retention gaps, active-template storage omission, conflicting API/legacy-clock
  contracts, missing boundary tests and absent performance/reviewer/HYP evidence. Their resolution
  requires the explicit future work above, not retrospective task/checklist completion in this audit.

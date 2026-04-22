# Tasks: Simulation Time Warp & Playback

**Input**: Design documents from `/specs/026-sim-warp-playback/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md, quickstart.md

**Tests**: Included — the spec mandates unit, integration, and contract tests for all new services.

**Organization**: Tasks grouped by user story (P1→P2→P3) for independent implementation. US1 and US4 are merged into a single phase since US4 (time-scaled ingestion) is the engine that powers US1 (time-warped simulation).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Agent Involvement Matrix

Each task identifies the **primary agent** responsible and any **consulting agents** whose input/output is valuable.

| Agent | Role | Involvement |
| ----- | ---- | ----------- |
| `@software-developer` | Primary implementer | All coding tasks — Python backend (FastAPI/Pydantic) and TypeScript frontend (Next.js) |
| `@data-engineer` | Data layer architect | Cosmos DB container design, event recording pipeline, signal scheduling cursor, partition strategy |
| `@api-architect` | API contract owner | Endpoint design, service boundaries, request/response validation, event-driven patterns |
| `@qa-test-engineer` | Test strategy lead | Test design, acceptance scenario mapping, contract/integration/unit test authoring |
| `@ux-designer` | UI/UX design | Playback timeline, warp speed controls, annotation panel, clock display, empty states |
| `@security-engineer` | Access control | Playback access restriction, annotation author enforcement, controller-only speed change |
| `@sre-engineer` | Reliability/operations | Graceful degradation (FR-010a), delivery lag monitoring, throttle behaviour, scheduler durability |
| `@solution-architect` | Design validation | Cross-cutting architecture review, state machine correctness, data flow validation |
| `@observer-auditor` | Domain validation | Playback as after-action review tool — validates that event recording captures what auditors need |
| `@incident-commander` | User validation | Primary persona for warp controls — validates controller UX for speed selection and mid-run changes |
| `@principal-engineer` | Code review | Design pattern review, backward compatibility validation, migration strategy |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New Cosmos container, shared constants, and domain model foundations.

**Consulting agents**: `@data-engineer` for Cosmos container config; `@principal-engineer` for backward compat strategy.

- [ ] T001 Define allowed warp speeds constant `ALLOWED_WARP_SPEEDS = [1, 2, 5, 10, 24, 60]` and shared validation helper in `packages/domain/src/domain/models/warp_constants.py`. Export a `validate_warp_speed(speed: float) -> float` function that raises `ValueError` for invalid values. Also define `PLAYBACK_SPEEDS = [1, 2, 5, 10]` and `DEFAULT_WARP_SPEED = 1.0`.
  - **Primary**: `@software-developer`

- [ ] T001a [P] Provision Cosmos DB container `sim-events` with partition key `/tenant_id`. Add composite index on `(tenant_id, event_seq)` for ordered retrieval and secondary range index on `(tenant_id, sim_time_offset)` for scrub queries. Add container definition to the existing Bicep/IaC templates in `infra/`. For local dev/test, the in-memory fallback in `SimulationEventRepository` covers this.
  - **Primary**: `@infrastructure-devops` | **Consult**: `@data-engineer` for index strategy

- [ ] T002[P] Create `WarpSpeedChange` Pydantic model in `packages/domain/src/domain/models/warp_speed_change.py`. Fields per data-model.md: `sim_time_offset: float`, `old_speed: float`, `new_speed: float`, `changed_at: datetime`. Use `model_config = ConfigDict(frozen=True)` since it's an immutable value object.
  - **Primary**: `@software-developer` | **Consult**: `@data-engineer`

- [ ] T003 [P] Create `SimulationEvent` Pydantic model in `packages/domain/src/domain/models/simulation_event.py`. Fields per data-model.md: `id: str` (default factory `evt-{uuid4}`), `tenant_id: str`, `event_seq: int`, `event_type: Literal["signal_delivered", "chat_turn_user", "chat_turn_assistant", "tool_invocation", "state_change", "warp_speed_change", "annotation"]`, `sim_time_offset: float`, `wall_clock_time: datetime`, `payload: dict[str, Any]`, `schema_version: int = 1`, `document_type: str = "simulation_event"`. Add `PlaybackSnapshot` model in same file: `id: str` (default `snap-{uuid4}`), `tenant_id: str`, `event_seq: int`, `sim_time_offset: float`, `state: dict[str, Any]`, `document_type: str = "playback_snapshot"`. Add `SignalSchedulerState` model: `id: str`, `tenant_id: str`, `next_signal_index: int = 0`, `last_delivered_signal_id: str | None`, `last_delivery_sim_time: float = 0.0`, `scheduler_owner: str | None`, `heartbeat_at: datetime | None`, `delivery_lag_seconds: float = 0.0`, `document_type: str = "signal_scheduler_state"`.
  - **Primary**: `@software-developer` | **Consult**: `@data-engineer` for partition key and index strategy

- [ ] T004 [P] Extend `SimulationTenant` model in `packages/domain/src/domain/models/simulation_tenant.py`. Add new fields per data-model.md: `current_warp_speed: float = Field(default=1.0)`, `accumulated_sim_seconds: float = 0.0`, `last_resumed_at: datetime | None = None`, `clock_paused: bool = True`, `playback_status: Literal["full", "partial", "none"] = "none"`, `warp_speed_history: list[WarpSpeedChange] = Field(default_factory=list)`. Add import for `WarpSpeedChange` from T002. Add a `@property` computed `current_sim_seconds` that returns `accumulated_sim_seconds + (now - last_resumed_at).total_seconds() * current_warp_speed` when running, else `accumulated_sim_seconds`. Add field validator for `current_warp_speed` using `validate_warp_speed` from T001. Deprecate `elapsed_seconds` field with a comment but retain for backward compatibility — the API will map `accumulated_sim_seconds` → `elapsed_seconds` in responses.
  - **Primary**: `@software-developer` | **Consult**: `@principal-engineer` for backward compat; `@data-engineer` for Cosmos document size

- [ ] T005 Create `SimulationEventRepository` in `apps/api/app/repositories/simulation_event_repository.py`. Follow the existing repository pattern from `simulation_repository.py` (Cosmos with in-memory fallback). Target Cosmos container `sim-events` partitioned by `/tenant_id`. Methods: `append_event(event: SimulationEvent) -> SimulationEvent` (upsert), `next_sequence(tenant_id: str) -> int` (query MAX event_seq + 1, similar to `sim_chat_history_repository.py:next_sequence`), `list_events(tenant_id: str, after_seq: int = 0, limit: int = 200, include_annotations: bool = True) -> list[SimulationEvent]` (query ordered by event_seq, optionally filter out annotation type), `count_events(tenant_id: str) -> int`, `save_snapshot(snapshot: PlaybackSnapshot)`, `get_nearest_snapshot(tenant_id: str, before_sim_time: float) -> PlaybackSnapshot | None` (query for nearest snapshot ≤ sim_time), `get_annotation(tenant_id: str, annotation_id: str) -> SimulationEvent | None`, `update_event(event: SimulationEvent)`, `delete_event(tenant_id: str, event_id: str)`. In-memory fallback: use `dict[str, list]` keyed by tenant_id. Include `_build_cosmos_client()` with `DefaultAzureCredential` try/except pattern per existing repos.
  - **Primary**: `@data-engineer` | **Consult**: `@software-developer` for Pydantic integration

- [ ] T006 Register new domain models in `packages/domain/src/domain/models/__init__.py` — add exports for `SimulationEvent`, `PlaybackSnapshot`, `SignalSchedulerState`, `WarpSpeedChange`, and warp constants.
  - **Primary**: `@software-developer`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Server-owned clock service and event recording infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**Consulting agents**: `@solution-architect` for clock state machine validation; `@sre-engineer` for graceful degradation design.

- [ ] T007 Create `SimulationClockService` in `apps/api/app/services/simulation_clock_service.py`. This is the canonical server-owned clock (research decision R2). Methods: `start_clock(tenant: SimulationTenant, warp_speed: float = 1.0) -> SimulationTenant` (sets `last_resumed_at=now`, `clock_paused=False`, `current_warp_speed=warp_speed`; returns mutated tenant), `pause_clock(tenant: SimulationTenant) -> SimulationTenant` (computes `accumulated_sim_seconds += (now - last_resumed_at).total_seconds() * current_warp_speed`, sets `last_resumed_at=None`, `clock_paused=True`), `change_speed(tenant: SimulationTenant, new_speed: float) -> SimulationTenant` (validates speed via `validate_warp_speed`, snapshots accumulated time at old speed, sets `last_resumed_at=now`, `current_warp_speed=new_speed`, appends `WarpSpeedChange` to `warp_speed_history`), `get_current_sim_seconds(tenant: SimulationTenant) -> float` (computes live simulated time), `resume_clock(tenant: SimulationTenant) -> SimulationTenant` (sets `last_resumed_at=now`, `clock_paused=False`). Each method validates preconditions (e.g., cannot pause already-paused clock). All mutations return a new tenant instance (immutable pattern).
  - **Primary**: `@software-developer` | **Consult**: `@solution-architect` for state machine correctness

- [ ] T008 Create `SimulationEventRecorder` in `apps/api/app/services/simulation_event_recorder.py`. This is the write-boundary interceptor (research decision R3). Constructor takes `SimulationEventRepository` and optional `SimulationClockService`. Methods: `record_event(tenant_id: str, event_type: str, sim_time_offset: float, payload: dict) -> SimulationEvent | None` (gets next sequence number, creates `SimulationEvent`, appends via repository; on failure logs warning and returns `None` — graceful degradation per FR-010a), `record_signal_delivered(tenant_id: str, sim_time: float, signal_id: str, data_source_id: str, category: str, offset_seconds: float)`, `record_chat_turn(tenant_id: str, sim_time: float, turn_sequence: int, role: str, message_preview: str, tool_calls: list[str] | None = None)`, `record_tool_invocation(tenant_id: str, sim_time: float, tool_name: str, outcome: str, latency_ms: int)`, `record_state_change(tenant_id: str, sim_time: float, from_status: str, to_status: str, trigger: str)`, `record_warp_speed_change(tenant_id: str, sim_time: float, old_speed: float, new_speed: float)`. Track recording health: `_consecutive_failures: int`, `_recording_healthy: bool`. After 3 consecutive failures, set tenant `playback_status = "partial"` and log critical warning. Include snapshot logic: call `_maybe_create_snapshot()` after every event write — create snapshot if event_seq is divisible by 100 or sim_time_offset crossed a 300-second boundary since last snapshot.
  - **Primary**: `@software-developer` | **Consult**: `@sre-engineer` for degradation thresholds; `@observer-auditor` for event completeness validation

- [ ] T009 Write unit tests for `SimulationClockService` in `tests/unit/test_simulation_clock.py`. Test cases from spec acceptance scenarios: (1) start_clock sets correct fields, (2) pause_clock computes accumulated_sim_seconds correctly at 1×/5×/60× warp, (3) change_speed snapshots accumulated time then resets last_resumed_at, (4) change_speed appends to warp_speed_history, (5) get_current_sim_seconds returns live computed value, (6) resume_clock after pause continues from correct offset, (7) precondition violations raise appropriate errors (pause already-paused, start already-running), (8) validate_warp_speed rejects invalid speeds. Use `freezegun` or manual datetime injection for deterministic time testing.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@software-developer`

- [ ] T010 [P] Write unit tests for `SimulationEventRecorder` in `tests/unit/test_event_recorder.py`. Test cases: (1) record_event creates event with correct seq/type/payload, (2) graceful degradation — repo failure returns None and logs warning, (3) after 3 consecutive failures, marks recording as unhealthy, (4) each convenience method (record_signal_delivered, record_chat_turn, etc.) produces correct payload shape, (5) snapshot creation triggers at event_seq divisible by 100, (6) snapshot creation triggers at 300-second sim_time boundary.
  - **Primary**: `@qa-test-engineer`

**Checkpoint**: Server clock and event recording infrastructure ready — user story implementation can now begin.

---

## Phase 3: User Story 1 + 4 — Time-Warped Simulation & Ingestion Engine (Priority: P1) 🎯 MVP

**Goal**: Controllers can create a simulation with a warp speed, and signals are delivered at the correct compressed intervals. The simulation clock displays simulated time, and pause/resume preserves the correct offset.

**Independent Test**: Create a simulation at 10×, seed a scenario, verify signals arrive at compressed times. Pause, verify time preserved. Resume, verify no gaps.

**Consulting agents**: `@data-engineer` for scheduler durability; `@incident-commander` for controller UX validation; `@api-architect` for endpoint design.

### Tests for US1+US4

- [ ] T011 [P] [US1] Write contract tests for modified simulation endpoints in `tests/contract/test_warp_speed_api.py`. Test: (1) POST /simulations with `warp_speed=10` returns `warp_speed`, `accumulated_sim_seconds`, `clock_paused` in response, (2) POST /simulations without `warp_speed` defaults to 1.0, (3) POST /simulations with invalid `warp_speed=7` returns 400, (4) GET /simulations/{id} returns `current_warp_speed`, `current_sim_seconds`, `playback_status`, (5) POST /pause returns server-computed `accumulated_sim_seconds` (no request body needed), (6) POST /resume returns updated clock state, (7) GET /clock returns live clock with `delivery_lag_seconds`, (8) backward compat: all responses include `elapsed_seconds` field.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@api-architect` for contract shape

- [ ] T012 [P] [US1] Write unit tests for `WarpScheduler` in `tests/unit/test_warp_scheduler.py`. Test: (1) schedule_signals calculates correct real-time delivery offsets at 1×/10×/60×, (2) next_delivery_delay returns correct delay for next signal given current clock state, (3) deliver_next_signal advances cursor and records event, (4) pause halts delivery loop, (5) resume continues from correct cursor position, (6) signals at 1× match original template offsets (identity transform), (7) ordering preserved across multiple data sources, (8) throttle: when burst rate exceeded, signals queue with lag > 0, (9) scheduler state persists across simulated restart (loads from repo).
  - **Primary**: `@qa-test-engineer` | **Consult**: `@data-engineer`

- [ ] T013 [P] [US1] Write integration test for full warp lifecycle in `tests/integration/test_warp_simulation_lifecycle.py`. Test: (1) create simulation at 10×, (2) seed scenario with known offsets, (3) start scheduler, (4) wait appropriate wall-clock time, (5) verify signals delivered at correct compressed intervals, (6) pause — verify clock preserved, (7) resume — verify delivery continues without gaps, (8) complete — verify all signals delivered.
  - **Primary**: `@qa-test-engineer`

### Backend Implementation for US1+US4

- [ ] T014 [US1] Create `WarpScheduler` service in `apps/api/app/services/warp_scheduler.py`. This is the durable cursor-based signal delivery engine (research decisions R1, R6). Constructor takes `SimulationEventRepository`, `SimulationClockService`, signal repository (from existing `scenario_seeding_service`), and `SimulationEventRecorder`. Key methods: `initialize(tenant_id: str, signal_timeline: list[dict], warp_speed: float)` — creates `SignalSchedulerState` in repo with `next_signal_index=0`; `next_delivery_delay(tenant: SimulationTenant, scheduler_state: SignalSchedulerState, signal_timeline: list) -> float | None` — computes `(signal.offset_seconds - current_sim_time) / tenant.current_warp_speed`, returns None if no more signals; `deliver_next_signal(tenant_id: str) -> bool` — loads state, computes if next signal is due, delivers it via signal repository, records `signal_delivered` event, advances cursor, persists state, returns True if delivered; `run_delivery_loop(tenant_id: str)` — async loop that calls `deliver_next_signal` with appropriate sleep between, respects `clock_paused`, implements configurable max burst rate (default 100 signals/sec), tracks `delivery_lag_seconds`; `pause(tenant_id: str)`, `resume(tenant_id: str)`, `update_speed(tenant_id: str, new_speed: float)` — mutate state. Lease/ownership: set `scheduler_owner` to instance UUID, heartbeat every 10s, stale after 30s.
  - **Primary**: `@software-developer` | **Consult**: `@data-engineer` for cursor durability; `@sre-engineer` for heartbeat/lease pattern

- [ ] T015 [US1] Modify `SimulationService.create_tenant()` in `apps/api/app/services/simulation_service.py`. Changes: (1) accept new `warp_speed: float = 1.0` parameter, (2) validate warp speed via `validate_warp_speed`, (3) set `current_warp_speed` on new `SimulationTenant`, (4) after transition to Active, call `clock_service.start_clock(tenant, warp_speed)`, (5) record `state_change` event via `event_recorder.record_state_change(...)`. Update constructor to accept `SimulationClockService` and `SimulationEventRecorder` as dependencies.
  - **Primary**: `@software-developer` | **Consult**: `@principal-engineer` for backward compat

- [ ] T016 [US1] Modify `SimulationService` pause/resume/archive methods in `apps/api/app/services/simulation_service.py`. Changes: (1) `pause_tenant()` — remove `elapsed_seconds` parameter, instead call `clock_service.pause_clock(tenant)` to compute server-side accumulated time, record `state_change` event, return updated tenant; (2) `resume_tenant()` — remove `elapsed_seconds` parameter, call `clock_service.resume_clock(tenant)`, record `state_change` event; (3) `archive_tenant()` — call `clock_service.pause_clock(tenant)` first (to finalize accumulated time), then proceed with existing archive flow, record `state_change` event. Each method persists updated tenant via repo.
  - **Primary**: `@software-developer`

- [ ] T017 [US1] Modify `ScenarioSeedingService` in `apps/api/app/services/scenario_seeding_service.py`. Changes: (1) `seed_from_template()` — after writing signals, initialize `WarpScheduler` with the signal timeline and tenant's `current_warp_speed`; (2) `replay_realtime()` — replace sequential `asyncio.sleep` loop with `WarpScheduler.run_delivery_loop()` call; the scheduler handles warp-aware timing via the durable cursor; (3) both methods now accept `event_recorder` and record events for each signal delivery. Accept `warp_speed` parameter to configure initial scheduling.
  - **Primary**: `@software-developer` | **Consult**: `@data-engineer`

- [ ] T018 [US1] Modify simulation API routes in `apps/api/app/api/routes/simulations.py`. Changes per contracts/api-contracts.md: (1) `CreateSimulationRequest` — add `warp_speed: float = 1.0` field with validator; (2) `create_simulation` handler — pass `warp_speed` to service; include `warp_speed`, `accumulated_sim_seconds`, `clock_paused` in response; (3) `get_simulation` handler — add `current_sim_seconds` (computed), `current_warp_speed`, `playback_status` to response; (4) `PauseResumeRequest` — make `elapsed_seconds` optional/deprecated, server computes time; (5) `pause_simulation` / `resume_simulation` / `archive_simulation` — remove client `elapsed_seconds` dependency, return server-computed values; (6) all responses include `elapsed_seconds` field (mapped from `accumulated_sim_seconds`) for backward compat. (7) Add new `GET /simulations/{tenant_id}/clock` endpoint — lightweight polling, returns `current_sim_seconds`, `accumulated_sim_seconds`, `current_warp_speed`, `clock_paused`, `delivery_lag_seconds`.
  - **Primary**: `@software-developer` | **Consult**: `@api-architect` for contract compliance

- [ ] T019 [US1] Modify `SimulationRepository` in `apps/api/app/repositories/simulation_repository.py` — ensure CRUD operations handle the new fields on `SimulationTenant` (no schema migration needed for Cosmos — new fields auto-included in `model_dump()`). Add `get_scheduler_state(tenant_id: str) -> SignalSchedulerState | None` and `save_scheduler_state(state: SignalSchedulerState)` methods for the warp scheduler cursor. In-memory fallback: store scheduler states in separate dict.
  - **Primary**: `@software-developer` | **Consult**: `@data-engineer`

### Frontend Implementation for US1+US4

- [ ] T020 [P] [US1] Create `SimulationWarpControls` component in `apps/web/src/components/simulation-warp-controls.tsx`. Renders a dropdown/segmented-control for warp speed selection showing allowed speeds (1×, 2×, 5×, 10×, 24×, 60×). Props: `currentSpeed: number`, `onChange: (speed: number) => void`, `disabled: boolean`. Show active speed highlighted. Used in both creation form and simulation dashboard.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer` for control layout; `@incident-commander` for usability in high-pressure scenarios

- [ ] T021 [P] [US1] Create `SimulationServerClock` component in `apps/web/src/components/simulation-server-clock.tsx`. Replaces the existing client-side `useElapsed` hook for warp simulations. Polls `GET /simulations/{tenant_id}/clock` every 1 second when running, displays `HH:MM:SS` of simulated time. Props: `tenantId: string`, `clockPaused: boolean`. Between polls, interpolates locally using `accumulated_sim_seconds + elapsed_since_poll × warp_speed` for smooth display. Shows warp speed badge (e.g., "10×") next to the clock.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer`

- [ ] T022 [US1] Update simulation creation page in `apps/web/src/app/simulations/create/page.tsx`. Add `SimulationWarpControls` component to the creation form. Default selection: 1× (real time). Pass selected `warp_speed` in the `createSimulation()` API call payload.
  - **Primary**: `@software-developer`

- [ ] T023 [US1] Update simulation dashboard page in `apps/web/src/app/simulations/[tenantId]/page.tsx`. Changes: (1) Replace `useElapsed` hook with `SimulationServerClock` component for time display when simulation is Active; (2) Remove `elapsed_seconds` from pause/resume/archive request bodies — server handles it; (3) Update pause/resume/archive response handlers to read `accumulated_sim_seconds` from server response; (4) Show current warp speed in simulation details panel; (5) Display `delivery_lag_seconds` warning banner if lag > 5 seconds (from clock endpoint).
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer` for lag warning design

- [ ] T024 [US1] Update simulation API client in `apps/web/src/lib/api/simulations.ts`. Changes: (1) Add `warp_speed?: number` to `CreateSimulationPayload`; (2) Add `ClockResponse` type: `{ current_sim_seconds, accumulated_sim_seconds, current_warp_speed, clock_paused, delivery_lag_seconds }`; (3) Add `getSimulationClock(tenantId: string): Promise<ClockResponse>` function; (4) Update `SimulationDetail` type to include `current_warp_speed`, `current_sim_seconds`, `playback_status`; (5) Make `elapsed_seconds` parameter optional/removed in `pauseSimulation` and `resumeSimulation` — send empty body.
  - **Primary**: `@software-developer`

- [ ] T025 [US1] Update simulation list page in `apps/web/src/app/simulations/page.tsx`. If this page calls pause/resume/archive, update those calls to no longer pass `elapsed_seconds` in request body (server owns the clock now). Show warp speed badge on simulation cards that have `current_warp_speed > 1`.
  - **Primary**: `@software-developer`

**Checkpoint**: At this point, simulations can be created with warp speed, signals deliver at compressed intervals, the clock displays simulated time, and pause/resume works correctly. This is the **MVP** — independently testable and demonstrable.

**Validation**: `@incident-commander` should review controller UX flow. `@observer-auditor` should verify event recording captures signal deliveries and state changes.

---

## Phase 4: User Story 2 — Change Warp Speed During Running Simulation (Priority: P2)

**Goal**: Controllers can adjust warp speed mid-simulation. Signal delivery seamlessly transitions to the new rate without losing or duplicating events.

**Independent Test**: Start at 5×, change to 1×, verify signals slow down. Change to 24×, verify signals speed up. No duplicates or gaps.

**Consulting agents**: `@api-architect` for endpoint design; `@incident-commander` for mid-exercise UX.

### Tests for US2

- [ ] T026 [P] [US2] Write contract tests for warp-speed change endpoint in `tests/contract/test_warp_speed_api.py` (append to existing file from T011). Test: (1) POST /simulations/{id}/warp-speed with `{"warp_speed": 24}` returns 200 with `previous_speed`, `current_warp_speed`, `accumulated_sim_seconds`, (2) invalid speed returns 400, (3) non-Active simulation returns 409, (4) non-controller user returns 403.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@security-engineer` for auth checks

- [ ] T027 [P] [US2] Write unit tests for speed change in clock service and scheduler in `tests/unit/test_simulation_clock.py` (append to existing from T009). Test: (1) change_speed mid-run correctly snapshots accumulated time, (2) change_speed appends WarpSpeedChange to history, (3) multiple rapid speed changes preserve correct accumulated time, (4) scheduler recalculates next delivery delay after speed change without affecting already-delivered signals.
  - **Primary**: `@qa-test-engineer`

### Backend Implementation for US2

- [ ] T028 [US2] Add `change_warp_speed()` method to `SimulationService` in `apps/api/app/services/simulation_service.py`. Logic: (1) load tenant, verify status is Active, verify requester is `created_by` (controller only per spec), (2) call `clock_service.change_speed(tenant, new_speed)`, (3) call `warp_scheduler.update_speed(tenant_id, new_speed)` to recalculate next signal delay, (4) record `warp_speed_change` event via `event_recorder`, (5) persist updated tenant, (6) return updated tenant with previous and new speed.
  - **Primary**: `@software-developer` | **Consult**: `@security-engineer` for controller-only authorization

- [ ] T029 [US2] Add `POST /simulations/{tenant_id}/warp-speed` route in `apps/api/app/api/routes/simulations.py`. Request model: `ChangeWarpSpeedRequest` with `warp_speed: float` validated against allowed set. Route handler: extracts user from auth context, calls `simulation_service.change_warp_speed()`, returns `{ tenant_id, previous_speed, current_warp_speed, accumulated_sim_seconds }`. Error responses: 400 for invalid speed, 403 for non-controller, 409 for non-Active status.
  - **Primary**: `@software-developer` | **Consult**: `@api-architect`

### Frontend Implementation for US2

- [ ] T030 [US2] Add speed change controls to simulation dashboard in `apps/web/src/app/simulations/[tenantId]/page.tsx`. Show `SimulationWarpControls` component (from T020) in the controller's sidebar when simulation is Active. On speed change selection, call `changeWarpSpeed()` API. Update local state with new speed. Disable during non-Active states. Only show to controller (check `created_by === currentUser`).
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer` for placement; `@incident-commander` for validation

- [ ] T031 [US2] Add `changeWarpSpeed(tenantId: string, warpSpeed: number)` function to `apps/web/src/lib/api/simulations.ts`. Returns `{ tenant_id, previous_speed, current_warp_speed, accumulated_sim_seconds }`. Add `WarpSpeedChangeResponse` type.
  - **Primary**: `@software-developer`

**Checkpoint**: Controllers can change warp speed mid-simulation. Signal delivery adjusts seamlessly. US1 + US2 together enable full time-warp capability.

**Validation**: `@incident-commander` should test speed changes during a live exercise scenario. `@qa-test-engineer` should run integration test verifying no signal loss/duplication across speed transitions.

---

## Phase 5: User Story 3 — Replay a Completed Simulation (Priority: P2)

**Goal**: Completed/archived simulations can be opened in read-only playback mode with play/pause/scrub/speed controls and a visual timeline.

**Independent Test**: Complete a simulation (from US1), open playback, play events, pause, scrub to a point, verify state matches expected.

**Consulting agents**: `@ux-designer` for timeline design; `@observer-auditor` for after-action review completeness; `@security-engineer` for access control.

### Tests for US3

- [ ] T032 [P] [US3] Write contract tests for playback API in `tests/contract/test_playback_api.py`. Test: (1) GET /playback/events returns paginated events sorted by event_seq, (2) `after_seq` cursor pagination works, (3) `include_annotations=false` filters annotations, (4) non-participant gets 403, (5) GET /playback/snapshots returns nearest snapshot, (6) empty simulation (no events) returns empty list with `playback_status: "none"`.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@security-engineer`

- [ ] T033 [P] [US3] Write unit tests for `PlaybackService` in `tests/unit/test_playback_service.py`. Test: (1) get_events returns ordered events with pagination, (2) get_nearest_snapshot returns correct snapshot for given sim_time, (3) access control — rejects non-participant, (4) handles simulation with zero events gracefully, (5) handles partial playback_status correctly.
  - **Primary**: `@qa-test-engineer`

- [ ] T034 [P] [US3] Write integration test for playback flow in `tests/integration/test_playback_events.py`. Test: (1) create simulation, (2) seed and run to completion (deliver signals, chat turns, state changes), (3) verify all events are recorded with correct types and seq order, (4) retrieve events via playback API, (5) verify event count matches expected, (6) verify scrub snapshot contains correct state.
  - **Primary**: `@qa-test-engineer`

### Backend Implementation for US3

- [ ] T035 [US3] Create `PlaybackService` in `apps/api/app/services/playback_service.py`. Constructor takes `SimulationEventRepository` and `SimulationRepository`. Methods: `get_events(tenant_id: str, requesting_user_oid: str, after_seq: int = 0, limit: int = 200, include_annotations: bool = True) -> dict` — (1) load tenant, (2) verify user is participant or controller via `repo.is_participant()` or `tenant.created_by == user_oid`, (3) query events from event repo, (4) return `{ events, has_more, next_cursor, total_events, playback_status }`; `get_snapshots(tenant_id: str, requesting_user_oid: str, before_sim_time: float | None = None) -> dict` — (1) access check, (2) query snapshots from event repo, (3) return list; `check_access(tenant_id: str, user_oid: str) -> bool` — centralised access check used by all playback endpoints.
  - **Primary**: `@software-developer` | **Consult**: `@security-engineer` for access control logic

- [ ] T036 [US3] Create playback API routes in `apps/api/app/api/routes/simulation_playback.py`. New router: `APIRouter(prefix="/simulations/{tenant_id}/playback", tags=["simulation-playback"])`. Endpoints per contracts/api-contracts.md: (1) `GET /events` — query params: `after_seq`, `limit`, `include_annotations`; calls `playback_service.get_events()`; (2) `GET /snapshots` — query param: `before_sim_time`; calls `playback_service.get_snapshots()`. Register router in `apps/api/app/api/router.py`.
  - **Primary**: `@software-developer` | **Consult**: `@api-architect`

- [ ] T037 [US3] Register playback router in `apps/api/app/api/router.py` — add `include_router(simulation_playback_router)` import and registration.
  - **Primary**: `@software-developer`

### Frontend Implementation for US3

- [ ] T038 [P] [US3] Create playback API client in `apps/web/src/lib/api/simulation-playback.ts`. Types: `PlaybackEvent`, `PlaybackEventsResponse`, `PlaybackSnapshot`, `PlaybackAnnotation`. Functions: `getPlaybackEvents(tenantId, afterSeq?, limit?, includeAnnotations?)`, `getPlaybackSnapshots(tenantId, beforeSimTime?)`, `createAnnotation(tenantId, simTimeOffset, text)`, `updateAnnotation(tenantId, annotationId, text)`, `deleteAnnotation(tenantId, annotationId)`. Use native fetch with cache: "no-store" per existing patterns.
  - **Primary**: `@software-developer`

- [ ] T039 [US3] Create `PlaybackTimeline` component in `apps/web/src/components/playback-timeline.tsx`. A horizontal timeline scrubber showing the full simulated duration. Props: `events: PlaybackEvent[]`, `annotations: PlaybackAnnotation[]`, `currentPosition: number` (sim seconds), `totalDuration: number`, `onScrub: (simTime: number) => void`. Renders: (1) horizontal bar representing total sim duration, (2) markers for events (color-coded by type: signal=blue, chat=green, state_change=orange, tool=purple), (3) annotation markers (yellow pins), (4) draggable scrub handle at current position, (5) time labels at intervals. Click/drag to scrub. Shows tooltip with event summary on hover.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer` for visual design, marker layout, responsiveness

- [ ] T040 [US3] Create `PlaybackControls` component in `apps/web/src/components/playback-controls.tsx`. Props: `isPlaying: boolean`, `playbackSpeed: number`, `currentSimTime: number`, `totalDuration: number`, `onPlay: () => void`, `onPause: () => void`, `onSpeedChange: (speed: number) => void`. Renders: play/pause button, speed selector (1×, 2×, 5×, 10×), current time / total time display (e.g., "01:23:45 / 24:00:00"), progress percentage.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer`

- [ ] T041 [US3] Create playback page in `apps/web/src/app/simulations/[tenantId]/playback/page.tsx`. Server component that fetches simulation detail and initial event batch. Client component `PlaybackPlayer` manages: (1) state: events array, current position (sim seconds), isPlaying, playbackSpeed, loaded snapshots, (2) on mount: load all events via paginated API calls (cursor-based, load in chunks of 200), (3) play logic: advance position at `playbackSpeed` per second, emit events as position crosses their `sim_time_offset`, (4) pause: stop advancing, (5) scrub: load nearest snapshot if available, then apply events from snapshot to target position, update current position, (6) event display: render event list panel showing events at/before current position, (7) access denied: if 403 returned, show "Playback access restricted" message, (8) empty state: if no events, show "No events were recorded for this simulation" with explanation. Layout: timeline at top, event list on left, simulation state visualization on right, controls at bottom.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer` for layout; `@observer-auditor` for what reviewers need to see

- [ ] T042 [US3] Add "Playback" button to simulation detail page. In `apps/web/src/app/simulations/[tenantId]/page.tsx`, add a "Review Playback" button visible when simulation status is "Completed" or "Archived". Button links to `/simulations/{tenantId}/playback`. Only show to participants and controller (check membership from tenant detail response).
  - **Primary**: `@software-developer`

- [ ] T043 [US3] Integrate event recording into chat pane in `apps/web/src/components/simulation-chat-pane.tsx` (backend side). Modify `SimulationControllerService` in `apps/api/app/services/simulation/controller_service.py` — after a complete user turn is appended to chat history, call `event_recorder.record_chat_turn(tenant_id, sim_time, seq, "user", preview)`. After assistant turn completes (not each SSE delta), call `event_recorder.record_chat_turn(tenant_id, sim_time, seq, "assistant", preview, tool_calls)`. After tool invocation completes, call `event_recorder.record_tool_invocation(...)`.
  - **Primary**: `@software-developer` | **Consult**: `@observer-auditor` for completeness

**Checkpoint**: Completed simulations can be replayed in full with play/pause/scrub/speed controls. Events recorded during live simulations are faithfully reproduced in playback.

**Validation**: `@observer-auditor` should review a complete playback session. `@incident-commander` and `@planning-officer` should validate the after-action review flow.

---

## Phase 6: User Story 5 — Annotate During Playback (Priority: P3)

**Goal**: Reviewers can add, edit, and delete text annotations at specific timeline positions during playback. Annotations are visible to all eligible reviewers.

**Independent Test**: Open playback, add annotation at a timeline position, save, reopen playback, verify annotation appears at correct position. Edit and delete — verify author-only enforcement.

**Consulting agents**: `@security-engineer` for author-only enforcement; `@ux-designer` for annotation UX.

### Tests for US5

- [ ] T044 [P] [US5] Write contract tests for annotation API in `tests/contract/test_annotation_api.py`. Test: (1) POST /playback/annotations creates annotation with correct fields and 201 status, (2) annotations appear in GET /playback/events response, (3) PUT updates text and sets `updated_at`, (4) PUT by non-author returns 403, (5) DELETE by author returns 204, (6) DELETE by non-author returns 403, (7) non-participant gets 403 on create.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@security-engineer`

### Backend Implementation for US5

- [ ] T045 [US5] Create `AnnotationService` in `apps/api/app/services/annotation_service.py`. Constructor takes `SimulationEventRepository`, `SimulationRepository`. Methods: `create_annotation(tenant_id: str, user_oid: str, user_name: str, sim_time_offset: float, text: str) -> SimulationEvent` — (1) verify access (participant/controller), (2) validate text length ≤ 2000 chars, (3) get next event_seq, (4) create `SimulationEvent` with `event_type="annotation"` and payload containing `annotation_id=ann-{uuid4}`, `author_id`, `author_name`, `text`, `created_at`, `updated_at=None`, (5) append to repo, (6) return event; `update_annotation(tenant_id: str, annotation_id: str, user_oid: str, text: str) -> SimulationEvent` — (1) load annotation event by querying for `annotation_id` in payload, (2) verify `author_id == user_oid` (403 if not), (3) update `text` and `updated_at` in payload, (4) update in repo; `delete_annotation(tenant_id: str, annotation_id: str, user_oid: str)` — (1) load annotation, (2) verify `author_id == user_oid` (403 if not), (3) delete from repo.
  - **Primary**: `@software-developer` | **Consult**: `@security-engineer`

- [ ] T046 [US5] Add annotation endpoints to playback router in `apps/api/app/api/routes/simulation_playback.py`. Per contracts/api-contracts.md: (1) `POST /annotations` — request: `{ sim_time_offset, text }`, extract user from auth context, call annotation_service.create_annotation(), return 201; (2) `PUT /annotations/{annotation_id}` — request: `{ text }`, call annotation_service.update_annotation(), return 200; (3) `DELETE /annotations/{annotation_id}` — call annotation_service.delete_annotation(), return 204.
  - **Primary**: `@software-developer` | **Consult**: `@api-architect`

### Frontend Implementation for US5

- [ ] T047 [US5] Create `PlaybackAnnotationPanel` component in `apps/web/src/components/playback-annotation-panel.tsx`. Props: `annotations: PlaybackAnnotation[]`, `currentSimTime: number`, `currentUserId: string`, `onAdd: (simTime: number, text: string) => void`, `onEdit: (annotationId: string, text: string) => void`, `onDelete: (annotationId: string) => void`. Renders: (1) "Add Note" button that creates annotation at current playback position, (2) text input with 2000-char limit, (3) list of annotations at or near current position, (4) each annotation shows author, time, text, (5) edit/delete buttons visible only for current user's annotations, (6) inline edit mode with save/cancel.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer` for panel layout

- [ ] T048 [US5] Integrate annotation panel into playback page in `apps/web/src/app/simulations/[tenantId]/playback/page.tsx`. Add `PlaybackAnnotationPanel` to the layout. Wire up annotation CRUD callbacks to the playback API client functions (from T038). On annotation create/edit/delete, refresh the events list to include updated annotations. Show annotation markers on the `PlaybackTimeline` component (yellow pins).
  - **Primary**: `@software-developer`

**Checkpoint**: Full annotation capability — create, view, edit, delete — with author-only enforcement. All user stories now complete.

**Validation**: `@observer-auditor` should test the complete after-action review workflow with annotations. `@security-engineer` should verify author-only enforcement.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, backward compatibility verification, documentation, and quality hardening.

**Consulting agents**: `@principal-engineer` for code review; `@sre-engineer` for operational readiness; `@compliance-auditor` for audit compliance.

- [ ] T049 [P] Run existing test suite (`python -m pytest tests/unit/ tests/integration/ tests/contract/ -q --tb=line`) to verify no regressions from SimulationTenant model changes and API route modifications. Fix any failures caused by the `elapsed_seconds` deprecation or new required fields.
  - **Primary**: `@qa-test-engineer`

- [ ] T050 [P] Backward compatibility verification — create a simulation WITHOUT specifying `warp_speed`, verify it defaults to 1× and behaves identically to pre-feature behavior. Verify all API responses include `elapsed_seconds` field for existing clients. Verify simulation list page works unchanged for non-warped simulations.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@principal-engineer`

- [ ] T051 [P] Add throttle status indicator to simulation dashboard. In `apps/web/src/app/simulations/[tenantId]/page.tsx`, show a visual throttle status indicator (e.g., icon or badge) when `delivery_lag_seconds > 0` from the clock endpoint. The delivery lag warning banner is already covered by T023.
  - **Primary**: `@software-developer` | **Consult**: `@sre-engineer`; `@incident-commander` for indicator design

- [ ] T052[P] Add `playback_status` indicator to simulation detail and list views. Show badge: "Full Recording" (green), "Partial Recording" (yellow with tooltip), "No Recording" (grey) on simulation cards and detail header.
  - **Primary**: `@software-developer` | **Consult**: `@ux-designer`

- [ ] T053 Code cleanup — remove any deprecated `elapsed_seconds` usage paths that are no longer needed. Update JSDoc/docstrings on modified services. Ensure all new files have appropriate module-level docstrings.
  - **Primary**: `@software-developer` | **Consult**: `@principal-engineer`

- [ ] T054 Run quickstart.md validation — execute all curl examples from `specs/026-sim-warp-playback/quickstart.md` against a running local instance. Verify: (1) create with warp_speed, (2) change warp speed, (3) check clock, (4) retrieve playback events, (5) create annotation. Fix any discrepancies.
  - **Primary**: `@qa-test-engineer`

- [ ] T055 Run full test suite including all new tests — `python -m pytest tests/ -q --tb=short`. Verify 100% pass rate. Generate coverage report for new files.
  - **Primary**: `@qa-test-engineer`

- [ ] T056 [P] Performance validation against success criteria. Test: (1) SC-001 — run a 24-hour scenario at 60× warp, verify completion in under 25 wall-clock minutes with all signals delivered at correct compressed intervals; (2) SC-002 — change warp speed mid-simulation, verify new pacing takes effect within 5 seconds with no signal loss; (3) SC-004 — scrub to arbitrary points in a completed simulation playback, verify state reconstruction completes within 3 seconds. Document results.
  - **Primary**: `@qa-test-engineer` | **Consult**: `@sre-engineer` for performance measurement methodology

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **US1+US4 (Phase 3)**: Depends on Foundational — **MVP milestone**
- **US2 (Phase 4)**: Depends on Phase 3 (extends clock service and scheduler from US1)
- **US3 (Phase 5)**: Depends on Foundational Phase 2 (uses event recorder) — can run **in parallel** with US2
- **US5 (Phase 6)**: Depends on Phase 5 (requires playback infrastructure)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ──── BLOCKS ALL ────┐
    │                                        │
    ▼                                        ▼
Phase 3 (US1+US4)                   Phase 5 (US3)
    │                                   │
    ▼                                   ▼
Phase 4 (US2)                     Phase 6 (US5)
    │                                   │
    └──────────┐    ┌──────────────────┘
               ▼    ▼
          Phase 7 (Polish)
```

### Within Each User Story

1. Contract/integration tests written FIRST (fail before implementation)
2. Domain models before services
3. Services before API routes
4. Backend before frontend
5. Core logic before UI polish

### Parallel Opportunities

- **Phase 1**: T001–T006 all run in parallel (different files)
- **Phase 2**: T007–T008 sequential (T008 depends on T007), T009–T010 parallel tests
- **Phase 3**: T011–T013 tests parallel; T020–T021 frontend components parallel with T014–T019 backend
- **Phase 4 & 5 can run in parallel** (different service/route files, no dependencies between them)
- **Phase 7**: T049–T055 mostly parallel

---

## Parallel Example: Phase 3 (US1+US4)

```text
# Parallel batch 1 — Tests (write first, verify they fail):
T011: Contract test for warp speed API         (tests/contract/test_warp_speed_api.py)
T012: Unit test for WarpScheduler              (tests/unit/test_warp_scheduler.py)
T013: Integration test for warp lifecycle      (tests/integration/test_warp_simulation_lifecycle.py)

# Parallel batch 2 — Backend core:
T014: WarpScheduler service                    (apps/api/app/services/warp_scheduler.py)
T015: SimulationService.create_tenant changes  (apps/api/app/services/simulation_service.py)
  ↓ (T015 depends on T014)
T016: SimulationService pause/resume changes   (same file, sequential with T015)
T017: ScenarioSeedingService changes           (apps/api/app/services/scenario_seeding_service.py) [P with T015]

# Parallel batch 3 — Backend routes + Frontend:
T018: API route modifications                  (apps/api/app/api/routes/simulations.py)
T019: Repository updates                       (apps/api/app/repositories/simulation_repository.py) [P with T018]
T020: WarpControls component                   (apps/web/src/components/...) [P with T018]
T021: ServerClock component                    (apps/web/src/components/...) [P with T018]

# Sequential batch 4 — Frontend integration:
T022: Creation page update                     (apps/web/src/app/simulations/create/page.tsx)
T023: Dashboard page update                    (apps/web/src/app/simulations/[tenantId]/page.tsx)
T024: API client update                        (apps/web/src/lib/api/simulations.ts)
T025: List page update                         (apps/web/src/app/simulations/page.tsx)
```

---

## Implementation Strategy

### MVP First (US1 + US4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1+US4 — Time-Warped Simulation
4. **STOP and VALIDATE**: Create 10× simulation, verify signals arrive at correct compressed times
5. Deploy/demo if ready — this alone delivers significant value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1+US4 → Test independently → Deploy/Demo (**MVP! Faster training cycles**)
3. Add US2 → Test independently → Deploy/Demo (mid-exercise speed control)
4. Add US3 → Test independently → Deploy/Demo (after-action playback review)
5. Add US5 → Test independently → Deploy/Demo (collaborative annotation)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational phase:

- **Developer A**: US1+US4 backend (T014–T019)
- **Developer B**: US1+US4 frontend (T020–T025)
- **Developer C**: US3 backend (T035–T037) — can start in parallel once Phase 2 done
- After US1+US4 complete: Developer A → US2, Developer B → US3 frontend, Developer C → US5

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after Phase 2
- `@observer-auditor` should validate playback completeness at Phase 5 checkpoint
- `@incident-commander` should validate controller UX at Phase 3 and Phase 4 checkpoints
- `@security-engineer` should review access control at Phase 5 and Phase 6 checkpoints
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

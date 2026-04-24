# Feature Specification: Simulation Time Warp & Playback

**Feature Branch**: `026-sim-warp-playback`  
**Created**: 2026-04-22  
**Status**: Draft  
**Input**: User description: "Accelerated / time-warped simulations at 1x, 2x, 5x, 10x, 24x, 60x speed with matching ingestion data; simulation playback for completed simulations to observe and improve disaster coordination."

## Clarifications

### Session 2026-04-22

- Q: When a simulation runs at warp speed, how should the AI chat controller behave? → A: Chat is independent of warp speed — the controller responds at its normal pace regardless of warp factor. Chat history is still recorded for playback.
- Q: Who can access playback for a completed simulation? → A: Only original simulation participants and the exercise controller.
- Q: Can playback annotations be edited or deleted after creation? → A: Editable and deletable by the original author only.
- Q: What scope of events should be recorded for playback? → A: Decision-significant events only — signals, alerts, chat messages, tool invocations, and state changes (including warp speed changes).
- Q: What should the default warp speed be when creating a simulation? → A: Default to 1× (real time), preserving backward compatibility.
- Q: If event recording fails during a live simulation, what should happen? → A: Continue the simulation and mark playback as partial/degraded. Training continuity takes priority over recording completeness.
- Q: How should simulation TTL (auto-archive) interact with warp speed? → A: TTL remains wall-clock based (unchanged). Controllers set TTL knowing the warp speed.
- Q: Should playback be available for simulations completed before event recording is deployed? → A: Yes — offer playback for all completed/archived simulations. Pre-existing simulations with no recorded events will show an empty timeline with an appropriate message.
- Q: How are annotations from concurrent playback sessions shared between reviewers? → A: Annotations are visible on page refresh or when re-entering playback. No real-time push mechanism is needed — concurrent reviewers see each other's annotations after refreshing.
- Q: What should the default maximum burst rate for signal throttling be? → A: 100 signals per second. Configurable per deployment to allow tuning based on system capacity.
- Q: At what delivery lag should the controller be warned about signal backpressure? → A: 10 seconds of wall-clock delivery lag. Configurable per deployment.
- Q: How should SC-005 (playback value) be measured? → A: Post-review survey — ≥80% of reviewers rate playback "useful" or "very useful". Replaces unmeasurable 40% time-reduction target.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Run a Time-Warped Simulation (Priority: P1)

An exercise controller wants to run a disaster simulation at an accelerated speed so that a scenario that would normally take 24 hours of wall-clock time can be completed in a shorter training session. The controller selects a scenario, chooses a time-warp speed (e.g. 10×), and starts the simulation. All ingested signals, alerts, and timeline events arrive at the accelerated rate — a signal scheduled 60 minutes into the scenario appears after just 6 real-time minutes. Participants experience the full pressure of the scenario in compressed time, and the simulation clock displayed in the interface reflects the accelerated simulated time, not wall-clock time.

**Why this priority**: Time-warp is the foundational capability that unlocks faster training cycles. Without it, every simulation runs strictly in real time, limiting the number of exercises an organisation can conduct.

**Independent Test**: Can be fully tested by creating a simulation with a known scenario, setting speed to 10×, and verifying that signals scheduled at specific offsets arrive at the expected compressed wall-clock times. Delivers immediate value by enabling faster training sessions.

**Acceptance Scenarios**:

1. **Given** a simulation is being created, **When** the controller selects a time-warp speed of 5×, **Then** the simulation is configured with a time compression ratio of 5 and this choice is persisted with the simulation.
2. **Given** a simulation is running at 10× speed with a signal scheduled at offset 600 seconds (10 simulated minutes), **When** 60 real-time seconds have elapsed since simulation start, **Then** the signal is ingested and visible to participants.
3. **Given** a simulation is running at any warp speed, **When** a participant views the simulation clock, **Then** the displayed time reflects simulated elapsed time (wall-clock elapsed × warp factor), not wall-clock time.
4. **Given** a simulation is running at 2× speed, **When** the controller pauses the simulation, **Then** the simulated elapsed time is preserved and signal ingestion halts until resumed.
5. **Given** a paused time-warped simulation, **When** the controller resumes it, **Then** signal ingestion continues from the correct simulated time offset without gaps or duplicates.

---

### User Story 2 — Change Warp Speed During a Running Simulation (Priority: P2)

A controller is running a simulation at 5× speed and realises that an upcoming phase needs closer observation. The controller adjusts the speed down to 1× (real time) while the simulation is running. Later, they accelerate to 24× to skip through a quiet period. The transition is seamless — signals continue arriving at the new rate without losing or duplicating events.

**Why this priority**: Mid-simulation speed changes give controllers fine-grained control over pacing, allowing them to slow down for critical decision-making moments and speed through routine phases. This significantly improves training quality.

**Independent Test**: Can be tested by starting a simulation at 5×, changing to 1× mid-run, verifying signal timing adjusts, then changing to 24× and confirming signals accelerate accordingly with no gaps or duplicates.

**Acceptance Scenarios**:

1. **Given** a simulation running at 5× speed, **When** the controller changes the speed to 1×, **Then** subsequent signals arrive at real-time intervals and the simulation clock adjusts to tick at 1× from the current simulated time.
2. **Given** a simulation running at 1× speed with simulated elapsed time of 30 minutes, **When** the controller changes to 24×, **Then** the next signal scheduled at simulated offset 31 minutes arrives within approximately 2.5 real-time seconds.
3. **Given** a speed change occurs, **When** signals are being ingested, **Then** no signals are skipped, duplicated, or delivered out of order.

---

### User Story 3 — Replay a Completed Simulation (Priority: P2)

After a major bushfire exercise, the emergency management team wants to review how decisions unfolded. A reviewer opens a completed simulation and enters playback mode. They see the full timeline of events — signals, alerts, chat messages, decisions, and tool invocations — replayed in chronological order. They can play, pause, fast-forward, and scrub to any point in the timeline. This enables after-action review, identification of coordination bottlenecks, and training material development.

**Why this priority**: Playback transforms simulations from one-time events into reusable learning assets. The ability to review and analyse past exercises is critical for continuous improvement in disaster coordination.

**Independent Test**: Can be tested by completing a simulation, opening it in playback mode, playing through the timeline, pausing, scrubbing to a specific point, and verifying that events at that point match the original simulation record.

**Acceptance Scenarios**:

1. **Given** a simulation with status "Completed" or "Archived", **When** a user who was a participant or controller opens the simulation, **Then** a playback option is available.
2. **Given** a completed simulation, **When** a user who was not a participant or controller attempts to open playback, **Then** the playback option is not available and access is denied.
3. **Given** playback mode is active, **When** the user presses play, **Then** events are replayed in chronological order at the selected playback speed.
4. **Given** playback is running, **When** the user pauses, **Then** the timeline stops and the current position is displayed.
5. **Given** playback is paused, **When** the user scrubs (jumps) to a specific point on the timeline, **Then** the display updates to show the state of the simulation at that moment, including all events that had occurred up to that point.
6. **Given** playback mode, **When** the user selects a playback speed (1×, 2×, 5×, 10×), **Then** events replay at the chosen speed relative to the original simulated time.
7. **Given** a completed simulation, **When** playback reaches the end of the recorded timeline, **Then** playback stops and the user is informed the simulation has ended.

---

### User Story 4 — Generate Time-Scaled Ingestion Data (Priority: P1)

When a simulation is configured with a time-warp speed, the system must generate or transform ingestion data (signals, events) so that their timing matches the warp factor. If a scenario template defines a signal at offset 3600 seconds (1 hour), and the simulation runs at 60×, that signal must be scheduled for delivery at 60 real-time seconds. The data generation must handle all signal types consistently and preserve the logical ordering of events.

**Why this priority**: This is the engine behind time-warp — without correctly scaled ingestion data, accelerated simulations would either deliver signals at wrong times or not at all. It is a prerequisite for User Story 1.

**Independent Test**: Can be tested by seeding a scenario with known offsets at various warp speeds and verifying the resulting delivery schedule matches expected compressed times.

**Acceptance Scenarios**:

1. **Given** a scenario template with signals at offsets [0s, 300s, 600s, 3600s], **When** seeded at 10× warp, **Then** the ingestion schedule targets delivery at real-time offsets [0s, 30s, 60s, 360s].
2. **Given** signals from multiple sources within the same scenario, **When** seeded at any warp speed, **Then** relative ordering between signals is preserved exactly.
3. **Given** a warp speed of 1× (real time), **When** a scenario is seeded, **Then** signal delivery times match the original template offsets with no transformation applied.
4. **Given** a warp speed change mid-simulation, **When** remaining undelivered signals are rescheduled, **Then** only future signals are recalculated — already-delivered signals are unaffected.

---

### User Story 5 — Annotate During Playback (Priority: P3)

During a playback session, a reviewer wants to add notes at specific points in the timeline to highlight coordination issues, commend good decisions, or flag areas for improvement. These annotations are saved with the simulation record and visible to other reviewers in future playback sessions.

**Why this priority**: Annotations turn passive review into active documentation. While playback alone has value, annotations make the insights persistent and shareable across the organisation.

**Independent Test**: Can be tested by opening a completed simulation in playback, adding annotations at specific timeline positions, saving, and then reopening playback to confirm annotations appear at the correct positions.

**Acceptance Scenarios**:

1. **Given** playback is active or paused, **When** the reviewer adds an annotation at the current timeline position, **Then** the annotation is saved with the simulation record, tagged with the simulated time offset, and attributed to the reviewer.
2. **Given** a simulation with existing annotations, **When** a different user opens playback, **Then** all annotations are visible at their correct timeline positions.
3. **Given** playback is running, **When** the timeline reaches a position with annotations, **Then** a visual indicator appears but playback does not auto-pause.

---

### Edge Cases

- What happens when the controller selects a warp speed that would cause signals to arrive faster than the system can process them (e.g. 60× on a scenario with very dense signal clusters)? The system should throttle ingestion to a maximum burst rate and queue excess signals, warning the controller if delivery falls behind simulated time.
- What happens when a speed change occurs at the exact moment a signal is scheduled for delivery? The signal should be delivered at the old speed; the new speed applies to subsequent signals.
- What happens if a completed simulation's recorded data is partially corrupted or missing? Playback should proceed with available data and indicate gaps in the timeline where data is missing.
- What happens when a user attempts to annotate a simulation they did not participate in? Since playback access is restricted to participants and the controller, this scenario does not arise — only eligible users can reach the annotation feature.
- What happens if playback is opened by multiple users simultaneously? Each user should have an independent playback position and controls; annotations created by any user are visible to others after they refresh or re-enter playback (no real-time push).
- What happens when a simulation has zero recorded events? Playback should display an empty timeline with a message indicating no events were recorded.

## Requirements *(mandatory)*

### Functional Requirements

**Time Warp**

- **FR-001**: System MUST support simulation time-warp speeds of 1×, 2×, 5×, 10×, 24×, and 60×.
- **FR-002**: System MUST allow the time-warp speed to be set when creating a simulation, defaulting to 1× (real time) if not specified.
- **FR-003**: System MUST allow the time-warp speed to be changed while a simulation is running.
- **FR-004**: System MUST transform signal delivery schedules to match the active time-warp speed, preserving relative event ordering.
- **FR-005**: System MUST recalculate delivery schedules for undelivered signals when the warp speed changes mid-simulation, without affecting already-delivered signals.
- **FR-006**: System MUST display simulated elapsed time (wall-clock elapsed × warp factor) rather than wall-clock time during a time-warped simulation.
- **FR-007**: System MUST preserve the simulated elapsed time when a time-warped simulation is paused and resume signal delivery from the correct offset.
- **FR-008**: System MUST throttle signal ingestion to a configurable maximum burst rate (default: 100 signals per second) when warp speed causes signal density to exceed processing capacity, and warn the controller if delivery lag exceeds 10 seconds of wall-clock time (configurable per deployment).

**Playback**

- **FR-009**: System MUST allow completed and archived simulations to be opened in a read-only playback mode, restricted to users who were participants or the controller of that simulation. Playback MUST be available for all completed/archived simulations regardless of when they were run; simulations without recorded events display an empty timeline with an explanatory message.
- **FR-010**: System MUST record decision-significant simulation events — signals, alerts, chat messages, tool invocations, and state changes (including warp speed changes) — with their simulated time offsets during a live simulation to enable playback. UI-level interactions (page views, map pans) are excluded.
- **FR-010a**: If the event recording pipeline fails during a live simulation, the simulation MUST continue uninterrupted. The system MUST warn the controller that recording is degraded and mark the simulation's playback status as partial. Playback of partially-recorded simulations MUST indicate gaps where data is missing.
- **FR-011**: System MUST support playback controls: play, pause, and scrub-to-position on the event timeline.
- **FR-012**: System MUST support playback speed selection of 1×, 2×, 5×, and 10× relative to original simulated time.
- **FR-013**: When scrubbing to a position, the system MUST reconstruct the simulation state at that point by replaying all events up to the selected offset.
- **FR-014**: System MUST indicate when playback reaches the end of the recorded timeline.

**Annotations**

- **FR-015**: System MUST allow reviewers to add text annotations at specific simulated time offsets during playback.
- **FR-016**: System MUST persist annotations with the simulation record, attributed to the reviewer and tagged with the simulated time offset.
- **FR-017**: System MUST display saved annotations at their correct timeline positions during subsequent playback sessions.
- **FR-018**: System MUST allow the original author of an annotation to edit or delete it. Other users MUST NOT be able to modify or remove another reviewer's annotations.

### Key Entities

- **SimulationTenant** (extended): Existing entity representing a simulation tenant. Extended with server-owned clock state (accumulated simulated seconds, warp speed, pause/resume timestamps), warp speed change history, and a playback status indicating recording completeness (full, partial, or none).
- **SimulationEvent**: A recorded occurrence during a simulation — signal arrival, alert trigger, chat message, tool invocation, or state change. Each event has a simulated time offset, event type, and payload. Used as the source of truth for playback.
- **WarpSpeedChange**: A record of a speed change during a simulation, capturing the simulated time offset, old speed, and new speed. Enables accurate reconstruction of timing during playback.
- **PlaybackAnnotation** (stored as SimulationEvent): A reviewer's note anchored to a specific simulated time offset in a completed simulation. Stored as a `SimulationEvent` with `event_type="annotation"`, containing the annotation text, author, and creation timestamp within the event payload. This co-location with other events simplifies timeline queries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A 24-hour scenario completes in under 25 minutes of wall-clock time when run at 60× warp speed, with all signals delivered at correct compressed intervals.
- **SC-002**: Controllers can change simulation speed mid-exercise and observe the new pacing take effect within 5 seconds, with no signal loss or duplication.
- **SC-003**: 100% of simulation events (signals, chat messages, decisions, tool invocations) are available for playback after a simulation completes when recording is healthy. When recording degrades (FR-010a), partial playback is available with gaps clearly indicated to the reviewer.
- **SC-004**: Reviewers can scrub to any point in a completed simulation's timeline and see the correct simulation state within 3 seconds.
- **SC-005**: In post-review surveys, ≥80% of reviewers rate playback with annotations as "useful" or "very useful" for producing after-action reports.
- **SC-006**: Annotations added during playback are visible to all subsequent reviewers without data loss.

## Assumptions

- The existing scenario template format (with `offset_seconds` in signal timelines) is sufficient to express all timing relationships needed for time-warp transformations.
- The existing `time_compression_ratio` field on `SimulationRun` and `SimulationScenario` will serve as the foundation for the warp speed feature, extended to support dynamic changes.
- Playback is read-only — no participant actions, chat interactions, or tool invocations can occur during playback. It is a review tool, not a re-run.
- Playback data retention follows the same lifecycle as the simulation itself (available while simulation is in Completed or Archived state, removed upon Deletion).
- The allowed warp speeds (1×, 2×, 5×, 10×, 24×, 60×) are a fixed set; arbitrary custom speeds are not supported in this iteration.
- Signal burst rate throttling defaults to 100 signals per second, configurable per deployment based on system capacity testing.
- The AI chat controller operates independently of the time-warp speed — it responds at its natural pace. Chat messages are timestamped with simulated time offsets for playback but are not accelerated or throttled by the warp factor.
- Simulation TTL (`ttl_hours` / `expires_at`) operates on wall-clock time regardless of warp speed. Controllers are expected to set TTL with the chosen warp speed in mind. The existing TTL mechanism is unchanged.

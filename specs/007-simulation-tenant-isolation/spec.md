# Feature Specification: Simulation-as-Tenant — Tenant-Partitioned Simulation Mode

**Feature Branch**: `007-simulation-tenant-isolation`
**Created**: 2026-04-09
**Status**: Draft
**Input**: User description: "Enable the disaster response hub to operate in simulation mode (tenant-partitioned isolation) while simultaneously ingesting and processing real data, so that preparedness exercises, training scenarios, and rehearsal replays can run without contaminating live operational state."

## Overview

The Disaster Response Coordination Hub must support concurrent operation of live disaster response and simulation exercises. Simulation mode enables preparedness drills, cross-agency tabletop exercises, scenario-based training, and post-incident replay analysis — all running alongside real-time ingestion from BOM, IoT sensors, and community sources. The simulation must be realistic enough to train operators and validate coordination procedures, while maintaining absolute isolation from the live operational environment.

This specification adopts the **Simulation-as-Tenant** approach: each simulation run is modelled as an independent logical tenant, sharing compute infrastructure but maintaining structural data isolation through partitioned storage, namespaced caching, prefixed audit artefacts, and tenant-scoped API routing. This design ensures that simulated signals, recommendations, alerts, and audit events cannot leak into the live operational view, and conversely that live data does not contaminate simulation analysis.

### Assumptions

- The multi-tenant storage layer (Cosmos DB partition keys, Redis namespaces, Blob Storage prefixes) will be established as part of this feature for both the live tenant and simulation tenants. The current in-memory state stores will be progressively replaced.
- Simulation tenants share Azure compute resources (Container Apps, OpenAI deployments) with the live tenant. Resource contention is mitigated by configurable concurrency limits and priority queuing, not by provisioning dedicated infrastructure per simulation.
- The existing agent chain (Monitoring → Risk Assessment → Communication → Evacuation → Resource Allocation) processes simulation signals identically to live signals. Simulation fidelity depends on processing parity, not separate agent implementations.
- Simulation tenants do not require separate Entra ID registrations. Simulation access is governed by role-based permissions within the existing identity model.
- The live tenant is always exactly one tenant with the well-known identifier `live`. All other tenants are simulation tenants with identifiers derived from their scenario run ID.
- BOM ingestion, IoT polling, and community report ingestion continue operating on the live tenant uninterrupted during any simulation exercise.

## Clarifications

### Session 2026-04-09

- Q: How should the system authenticate and determine tenant context on each request? → A: Server-derived from Entra ID token claims. The API middleware extracts tenant context from the authenticated user's Entra ID token (e.g., a custom claim or role assignment indicating the simulation tenant). The client never supplies tenant context directly; it is always resolved server-side from the identity token.
- Q: What observability signals should simulation tenants emit for operational monitoring? → A: Shared Application Insights with a `tenant_id` custom dimension on all telemetry (metrics, logs, traces). This enables per-tenant filtering and alerting without deploying separate monitoring infrastructure per simulation.
- Q: How should the system handle Entra ID role/claim assignment for simulation tenant membership? → A: Internal participant list in Cosmos DB. Entra ID is used only for authentication and base authorisation (e.g., `SimulationUser` app role). Per-simulation tenant membership is managed via a `participants` list on the SimulationTenant document — no dynamic Entra ID groups or per-simulation app roles are created.
- Q: When a real disaster activates during a simulation, should active simulations be automatically paused or only throttled? → A: Auto-throttle to a reduced resource quota (e.g., 20% of shared throughput). Administrators can manually pause simulations if needed. No automatic pause — throttling preserves simulation state and participant context while protecting live operations.
- Q: Are "exercise coordinator" and "resilience planner" distinct roles or synonyms? → A: Synonyms. Normalised to "exercise coordinator" as the canonical term throughout the spec.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create and run a simulation exercise alongside live operations (Priority: P1)

An exercise coordinator creates a new simulation scenario (for example, a Category 4 cyclone approaching Far North Queensland) to conduct a multi-agency tabletop exercise. The simulation must not interfere with real data being ingested from BOM and other live sources. Participants log into the simulation tenant, see only simulated data, and work through the exercise. Meanwhile, operators on live duty see only real data and are unaware the simulation is running.

**Why this priority**: This is the core capability. Without tenant-partitioned simulation, the system cannot safely support preparedness exercises alongside live operations. The constitutional requirement for scenario-based testing and the spec 001 requirement for rehearsal replays both depend on this.

**Independent Test**: Can be fully tested by creating a simulation tenant, injecting synthetic signals, verifying they appear only in the simulation view, and confirming the live dashboard remains unaffected. Delivers the foundational simulation capability upon which all other stories build.

**Acceptance Scenarios**:

1. **Given** the hub is ingesting real BOM weather warnings on the live tenant, **When** an exercise coordinator creates a new simulation tenant for a cyclone drill, **Then** the simulation tenant is provisioned with its own storage partition, cache namespace, and audit prefix within 30 seconds, and the live tenant continues processing without interruption.
2. **Given** a simulation tenant exists, **When** synthetic cyclone signals are injected via the signal ingestion endpoint with the simulation tenant context, **Then** those signals are stored only in the simulation partition and do not appear in live queries, live dashboard views, or the live audit trail.
3. **Given** both live and simulation tenants are actively processing signals, **When** an operator queries the live dashboard, **Then** zero simulation signals, recommendations, or alerts are visible, and the dashboard shows no simulation-related UI elements.
4. **Given** a simulation tenant is active, **When** the agent chain processes a simulated signal and generates a recommendation, **Then** the recommendation is stored in the simulation partition and the approval workflow operates within the simulation tenant boundary.
5. **Given** a simulated public alert is approved within a simulation tenant, **When** the alert reaches the publication service, **Then** the system blocks delivery to real channels (SMS, broadcast, social media) and records the alert as "published (simulation)" in the simulation audit trail.

---

### User Story 2 — Seed a simulation with realistic scenario data (Priority: P2)

An exercise coordinator selects a scenario template (bushfire, flood, cyclone, or cross-jurisdiction) and seeds the simulation tenant with appropriate organisations, jurisdictions, framework assignments, personas, and a timeline of synthetic signals. Historical incident data or curated scenario packs can be loaded as seed data so the exercise starts with a realistic operational picture.

**Why this priority**: A simulation without realistic seed data is a toy. This story makes simulations operationally useful for training, gap analysis, and cross-agency coordination practice. It builds on the tenant infrastructure from US1.

**Independent Test**: Can be fully tested by loading a bushfire scenario pack into a simulation tenant and verifying that all seeded organisations, frameworks, and signals appear in the simulation dashboard with correct provenance, timestamps, and jurisdictional assignments.

**Acceptance Scenarios**:

1. **Given** a simulation tenant has been created, **When** the coordinator selects the "QLD Cyclone — Multi-Agency" scenario template, **Then** the system seeds the simulation partition with at least 5 participating organisations (QPS, QFES, QAS, SES QLD, BOM National), their jurisdiction assignments, relevant AIIMS framework configuration, and a set of 20+ time-sequenced synthetic signals.
2. **Given** historical incident data exists in the live audit trail, **When** the coordinator requests a replay of a past incident as a simulation, **Then** the system copies the incident timeline, signals, and recommendations into a new simulation tenant (with fresh IDs and no references to the original live IDs) and allows the exercise to proceed from any point in the replayed timeline.
3. **Given** a scenario template includes signals with time offsets, **When** the simulation is started in real-time replay mode, **Then** signals are injected into the simulation tenant at the specified time offsets from the exercise start time, producing a realistic unfolding scenario.
4. **Given** seed data has been loaded, **When** an exercise participant opens the simulation dashboard, **Then** the participant sees the seeded operating picture including organisations, frameworks, signal timeline, and initial hazard assessment — indistinguishable in quality from a live operating picture except for the simulation identification banner.

---

### User Story 3 — Operate a persona-specific workspace within a simulation (Priority: P2)

Exercise participants are assigned persona roles (incident commander, operations officer, logistics officer, etc.) within the simulation tenant. Each participant sees only the simulation data scoped to their persona's role and jurisdiction, just as they would during a live incident. Participants can approve simulated recommendations, coordinate simulated tasks, and draft simulated public alerts within the simulation boundary.

**Why this priority**: Realistic persona-scoped participation is what makes a simulation exercise useful for training. Without it, the simulation is a passive data display rather than an interactive exercise. This story is equal priority with US2 because both are needed for a usable exercise.

**Independent Test**: Can be fully tested by assigning an incident commander persona to a simulation tenant, verifying that the persona workspace shows only simulation-scoped tasks and recommendations, and confirming that approval actions within the simulation do not generate live approvals.

**Acceptance Scenarios**:

1. **Given** a simulation tenant is running a flood exercise, **When** a participant logs in and selects their assigned persona (e.g., NSW SES Operations Officer), **Then** the workspace shows only simulation tasks, signals, and recommendations relevant to that persona's role, jurisdiction, and organisation — filtered identically to how the live workspace filters live data.
2. **Given** a participant is operating as an incident commander within a simulation, **When** they approve a simulated recommendation for evacuation, **Then** the approval is recorded in the simulation audit trail, the recommendation status updates to "approved" within the simulation, and no live operational state is affected.
3. **Given** a communication officer drafts a simulated public alert, **When** the alert is approved and "published" within the simulation, **Then** the system records the publication event in the simulation audit trail but does not send the alert to any real delivery channel.
4. **Given** multiple participants are operating simultaneously in a simulation, **When** one participant updates a coordination task, **Then** other participants in the same simulation see the update in near real-time (within 5 seconds) and participants on the live tenant see no changes.

---

### User Story 4 — Review simulation outcomes and produce exercise reports (Priority: P3)

After a simulation exercise concludes, the exercise coordinator and observer-auditors review the simulation's audit trail, decision timeline, coordination gaps, and outcome metrics. The system produces a structured exercise report comparing simulation performance against defined benchmarks (e.g., response time, coordination coverage, approval latency).

**Why this priority**: Post-exercise analysis is the primary value extraction mechanism for simulation exercises. Without it, exercises produce experience but not measurable improvement. This story depends on US1–US3 being complete.

**Independent Test**: Can be fully tested by completing a short simulation exercise, triggering the exercise report generation, and verifying that the report includes the decision timeline, coordination gap analysis, and performance metrics.

**Acceptance Scenarios**:

1. **Given** a simulation exercise has completed, **When** the coordinator requests an exercise report, **Then** the system generates a structured report containing: exercise timeline, participating organisations and personas, signals processed, recommendations generated and their approval outcomes, alerts drafted and published (simulation), coordination gaps identified, and performance metrics.
2. **Given** baseline performance benchmarks are defined for the scenario type, **When** the exercise report is generated, **Then** the report includes a side-by-side comparison of simulation performance against benchmark targets (e.g., time to first recommendation, time to alert publication, cross-agency coordination coverage).
3. **Given** the observer-auditor reviews a simulation audit trail, **When** they inspect the timeline, **Then** every signal, recommendation, approval, alert, and task state change within the simulation is recorded with full provenance, timestamps, and actor attribution — with no live tenant events interleaved.
4. **Given** an exercise report has been generated, **When** the coordinator archives the simulation tenant, **Then** the report and audit trail are persisted to immutable storage and the simulation's operational state (Cosmos DB partition, Redis namespace) is cleaned up to reclaim resources.

---

### User Story 5 — Manage simulation tenant lifecycle and resource governance (Priority: P3)

An administrator manages the lifecycle of simulation tenants: creating, monitoring, pausing, resuming, archiving, and deleting them. The system enforces governance constraints including maximum concurrent simulations, per-simulation resource budgets, and automatic cleanup of stale simulation tenants.

**Why this priority**: Without lifecycle governance, simulation tenants accumulate as storage debt and can degrade system performance. This story ensures operational hygiene and prevents resource exhaustion. It depends on the tenant infrastructure from US1.

**Independent Test**: Can be fully tested by creating multiple simulation tenants, verifying concurrency limits are enforced, triggering automatic cleanup of an expired simulation, and confirming that archived simulations retain their audit trails but release operational resources.

**Acceptance Scenarios**:

1. **Given** the system has a configured maximum of 3 concurrent simulation tenants, **When** a coordinator attempts to create a 4th simulation, **Then** the system rejects the creation with a clear message indicating the concurrency limit and listing active simulations.
2. **Given** a simulation tenant has been idle for longer than its configured TTL (default 72 hours), **When** the lifecycle manager runs its scheduled check, **Then** the simulation is automatically archived: its audit trail and exercise report are preserved in immutable storage, and its Cosmos DB partition, Redis namespace, and in-memory state are cleaned up.
3. **Given** a simulation tenant is active, **When** the administrator views the simulation management dashboard, **Then** the dashboard shows: tenant identifier, scenario type, creation time, participant count, signal count, resource consumption (storage size, cache keys), and tenant status (active, paused, archiving, archived).
4. **Given** an administrator archives a simulation tenant, **When** the archive completes, **Then** the exercise report, audit trail, and seed data are written to immutable blob storage under a dedicated simulation archive prefix, and the operational partition is deleted.

---

### Edge Cases

- **Concurrent live disaster and simulation**: A simulation exercise is running when a real disaster activates. The system automatically throttles all active simulations to 20% of shared throughput and notifies simulation participants. Administrators can manually pause simulations via the management dashboard. Live tenant receives absolute processing priority. Simulation state is preserved throughout throttling for later resumption at full capacity.
- **Simulation signal with live-matching identifiers**: A synthetic signal happens to reference a data source ID or jurisdiction ID that also exists in the live tenant. The tenant partition boundary must prevent any cross-contamination regardless of matching identifiers within the signal payload.
- **Network partition during simulation**: If the connection to Cosmos DB or Redis is temporarily interrupted during a simulation, the system must not fall back to writing simulation data into the live tenant's partitions. Simulation operations should fail safely rather than cross tenant boundaries.
- **Simulation tenant outlives its exercise**: An exercise coordinator forgets to archive a simulation. The TTL-based automatic cleanup must handle this gracefully, including notifying the coordinator before deletion and preserving the audit trail.
- **Exercise coordinator loses connectivity mid-exercise**: Participants already logged into the simulation must be able to continue working. The simulation should not terminate because the coordinator disconnects.
- **Replay of a live incident that is still active**: The system must allow replaying a past segment of a live incident as a simulation, but the replay must use a snapshot of data — it must not create a view into the still-active live incident's evolving state.
- **Simulation approaches resource quota limits**: If a large simulation (e.g., 50,000 synthetic signals) begins consuming a significant fraction of shared database throughput, the system should throttle simulation writes before they impact live operations, rather than throttling both equally.

## Requirements *(mandatory)*

### Functional Requirements

#### Tenant Infrastructure

- **FR-001**: The system MUST support exactly one well-known live tenant (identifier: `live`) and zero or more concurrent simulation tenants (identifier: `sim-{scenarioRunId}`).
- **FR-002**: The system MUST propagate tenant context through every layer of the request lifecycle: API routing, service layer, agent runtime, storage access, cache operations, and audit trail writes. Tenant context MUST be server-derived from the authenticated user's Entra ID token claims — never from client-supplied headers or query parameters.
- **FR-003**: The system MUST enforce tenant isolation at the storage layer such that a query scoped to tenant A cannot return data belonging to tenant B, regardless of query parameters, filter omissions, or application-layer bugs.
- **FR-004**: The system MUST route all incoming real-world data (BOM warnings, IoT sensor readings, community reports) exclusively to the live tenant. External data sources must never be routable to a simulation tenant.
- **FR-005**: The system MUST default to the live tenant when the authenticated user's Entra ID token does not contain a simulation tenant claim, preventing accidental writes to or reads from simulation tenants.

#### Simulation Lifecycle

- **FR-006**: The system MUST allow authorised users (exercise coordinators with the Entra ID `SimulationUser` app role) to create a new simulation tenant by specifying a scenario type, participating jurisdictions, an optional scenario template, and an initial participant list. Simulation tenant membership is managed internally via a `participants` list on the SimulationTenant document in Cosmos DB — no per-simulation Entra ID groups or app roles are created.
- **FR-007**: The system MUST provision a simulation tenant's storage partition, cache namespace, and audit prefix within the time limit defined by NFR-001.
- **FR-008**: The system MUST support pausing a simulation tenant, which suspends signal injection and agent processing while preserving all state for later resumption.
- **FR-009**: The system MUST support archiving a simulation tenant, which persists the exercise report and audit trail to immutable storage and releases operational resources (database partition contents, cache namespace).
- **FR-010**: The system MUST enforce a configurable maximum number of concurrent active simulation tenants (default: 3).
- **FR-011**: The system MUST automatically archive simulation tenants that have been idle beyond a configurable TTL (default: 72 hours), with a notification to the creating coordinator at least 24 hours before automatic archival.

#### Scenario Seeding

- **FR-012**: The system MUST support seeding a simulation tenant with curated scenario packs containing organisations, jurisdictions, framework assignments, and time-sequenced synthetic signals for at least three scenario types: bushfire, flood, and cyclone.
- **FR-013**: The system MUST support replaying historical live incidents as simulations by copying a snapshot of the incident data into a new simulation tenant with regenerated identifiers.
- **FR-014**: The system MUST support real-time signal replay whereby synthetic signals are injected at their original time offsets from the exercise start time.
- **FR-015**: The system MUST generate synthetic signals with full provenance metadata (source, confidence, freshness, location, timestamp) that matches the schema and quality of real signals.

#### Agent Processing and Workflow

- **FR-016**: The system MUST process simulation signals through the same agent chain (Monitoring → Risk Assessment → Communication → Evacuation → Resource Allocation) as live signals, with identical business logic and handoff patterns.
- **FR-017**: The system MUST scope all agent-generated artefacts (recommendations, hazard assessments, alerts, coordination tasks) to the simulation tenant in which the triggering signal was processed.
- **FR-018**: The system MUST support the full approval workflow within a simulation tenant, including recommendation review, approval, rejection, escalation, and alert publication — with all actions recorded in the simulation audit trail.
- **FR-019**: The system MUST block simulated public alerts from being delivered to any real communication channel (SMS, broadcast, social media, email). Simulated alerts MUST be recorded as "published (simulation)" in the simulation audit trail.

#### Dashboard and User Interface

- **FR-020**: The system MUST provide a simulation dashboard that is functionally identical to the live dashboard but displays only data from the selected simulation tenant.
- **FR-021**: The system MUST display a persistent, prominent "SIMULATION" identification banner on all simulation dashboard views that cannot be dismissed, minimised, or obscured by other UI elements.
- **FR-022**: The system MUST never display simulation data on the default (live) dashboard view. The live dashboard MUST NOT include a tenant picker, simulation toggle, or any simulation-related UI element.
- **FR-023**: The system MUST provide a separate simulation management area (accessible only to authorised roles) where exercise coordinators can create, monitor, pause, resume, archive, and delete simulation tenants.
- **FR-024**: The system MUST support persona-scoped workspaces within simulation tenants, filtering tasks, signals, and recommendations by persona role and jurisdiction identically to the live workspace filtering logic.

#### Audit and Reporting

- **FR-025**: The system MUST maintain a separate audit trail for each simulation tenant, stored under a tenant-specific prefix in immutable storage. Simulation audit events MUST NOT appear in the live audit trail.
- **FR-026**: The system MUST generate a structured exercise report for completed simulations containing: exercise timeline, participating organisations and personas, signals processed, recommendations and their outcomes, alerts drafted and published (simulation), coordination gaps, and performance metrics.
- **FR-027**: The system MUST support side-by-side comparison of simulation performance against defined benchmarks and, where applicable, against previous exercises of the same scenario type.

#### Resource Governance

- **FR-028**: The system MUST prioritise live tenant operations over simulation tenant operations when shared resources (compute, database throughput, LLM token quotas) are under contention. When a live incident is declared, the system MUST automatically throttle all active simulation tenants to a reduced resource quota (default: 20% of shared throughput) and notify simulation participants. Administrators MAY manually pause simulations via the management dashboard; no automatic pause occurs.
- **FR-029**: The system MUST support configurable per-simulation resource limits including maximum signal count, maximum recommendation count, and maximum exercise duration.
- **FR-030**: The system MUST throttle simulation writes before they impact live operations when shared database throughput exceeds a configurable threshold (default: 70% of provisioned capacity).
- **FR-031**: The system MUST expose an administrative endpoint (`POST /api/incidents/declare` and `POST /api/incidents/resolve`) that transitions the system between normal and live-incident mode. This endpoint is the trigger mechanism referenced by FR-028 and FR-030. Only users with an administrative role may invoke it.

### Non-Functional Requirements

- **NFR-001**: Creating a simulation tenant MUST complete within 30 seconds.
- **NFR-002**: Live signal ingestion latency MUST NOT increase by more than 10% when the maximum number of concurrent simulations are active.
- **NFR-003**: Simulation operations MUST fail safely (error, not redirect to live) if the simulation tenant's storage partition is unavailable.
- **NFR-004**: The system MUST support at least 10,000 synthetic signals per simulation exercise.
- **NFR-005**: Simulation tenant archival (audit trail persistence + operational resource cleanup) MUST complete within 5 minutes for exercises with up to 10,000 signals.
- **NFR-006**: All application telemetry (metrics, logs, distributed traces) MUST include a `tenant_id` custom dimension, emitted to the shared Application Insights instance, enabling per-tenant filtering, dashboards, and alerting without separate monitoring infrastructure.

### Key Entities

- **SimulationTenant**: A logical tenant representing a single simulation exercise. Key attributes: tenant identifier (`sim-{scenarioRunId}`), scenario type, status (provisioning, active, paused, archiving, archived, deleted), created by persona, creation timestamp, TTL, participant list (Entra ID object IDs of users granted access to this simulation), resource limits. Participant membership is managed internally in Cosmos DB; the API middleware resolves tenant access by checking the authenticated user's object ID against this list. Relates to exactly one ScenarioRun.
- **ScenarioTemplate**: A reusable definition for a simulation exercise. Key attributes: template identifier, scenario type (bushfire, flood, cyclone, cross-jurisdiction), seed organisations, seed jurisdictions, seed framework assignments, signal timeline definitions, benchmark targets. Used to initialise SimulationTenant seed data.
- **ScenarioRun** (extended): The existing ScenarioRun entity is extended with tenant association and lifecycle state. Key new attributes: tenant identifier, exercise report URI, archive status, resource consumption metrics. Relates to one SimulationTenant and many SimulationSignals.
- **SimulationSignal**: A synthetic signal injected into a simulation tenant. Structurally identical to a live Signal but scoped to a simulation tenant partition. Carries full provenance metadata including `source_context: "simulation"` in its provenance field.
- **ExerciseReport**: A structured report generated after a simulation concludes. Key attributes: report identifier, scenario run reference, exercise timeline summary, participating organisations and personas, signal and recommendation counts, coordination gaps, performance metrics vs benchmarks, archive URI.
- **TenantContext**: A request-scoped value object that identifies the active tenant for the current operation. Derived by API middleware from the authenticated user's Entra ID token claims (never from client-supplied headers). Propagated through service layer, repository layer, and agent runtime. Defaults to `live` when no simulation tenant claim is present in the token.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A simulation exercise with 5,000 synthetic signals can be provisioned, seeded, executed, and archived without any simulation data appearing in the live dashboard, live audit trail, or live agent processing pipeline — verified by automated cross-tenant leakage tests.
- **SC-002**: Live signal ingestion throughput remains within 10% of baseline (50,000 signals/hour) while 3 concurrent simulations are actively processing synthetic signals.
- **SC-003**: Exercise participants can complete a full simulation workflow (join exercise → view dashboard → approve recommendation → draft alert → publish simulation alert) in under 10 minutes for a pre-seeded scenario.
- **SC-004**: An exercise report produced after a completed simulation includes all required sections (timeline, organisations, signals, recommendations, alerts, coordination gaps, metrics) and can be generated within 60 seconds.
- **SC-005**: Simulation tenant archival reclaims at least 95% of the operational resources (database documents, cache keys) within 5 minutes while preserving the complete audit trail and exercise report in immutable storage.
- **SC-006**: 100% of automated cross-tenant isolation tests pass on every deployment, covering: signal write isolation, recommendation scope, alert publication blocking, audit trail separation, cache namespace isolation, and dashboard view segregation.
- **SC-007**: Operators on the live dashboard during an active simulation report zero confusion or cognitive interference from simulation activity, validated by a usability assessment with at least 3 operational personas.

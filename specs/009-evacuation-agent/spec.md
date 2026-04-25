# Feature Specification: Evacuation Agent — Route Optimisation, Transport Coordination, and Evacuation Planning

**Feature Branch**: `009-evacuation-agent`  
**Created**: 2026-04-16  
**Status**: Draft  
**Input**: User description: "The Evacuation Agent receives escalated assessments from Risk Assessment and must: (1) compute optimal evacuation routes considering road closures, capacity, and accessibility, (2) coordinate transport plans for vulnerable populations, (3) estimate evacuation timelines, (4) support dynamic route updates as conditions change, (5) consider accessibility constraints (mobility-impaired, elderly, children), (6) produce human-reviewable evacuation plans for incident commanders, (7) support rehearsal/simulation mode, and (8) maintain full audit trail."

## Clarifications

### Session 2026-04-11

- Q: What algorithm should the Evacuation Agent use for route computation? → A: Graph-based algorithm (Dijkstra's variant) on a simplified road network from external GIS service or pre-loaded dataset. LLM generates human-readable route descriptions and reasoning only — not used for path computation.
- Q: How should evacuation zones be modeled? → A: Concentric zones from hazard center. Zone 1 = immediate danger (evacuate first), Zone 2 = likely impact (evacuate within hours), Zone 3 = possible impact (prepare to evacuate). Zone boundaries derived from hazard assessment's affected_area GeoJSON.
- Q: What specific conditions trigger dynamic replanning of an active evacuation plan? → A: (a) new road closure reported, (b) hazard area expands >10%, (c) evacuation progress report shows >30% delay, (d) new higher-severity assessment received, (e) manual trigger by incident commander.
- Q: When no viable evacuation route exists, what determines shelter-in-place vs. emergency escalation? → A: No viable route AND hazard timeline allows → shelter-in-place with specific building requirements. No viable route AND immediate threat → escalate to emergency services with maximum urgency.
- Q: How are evacuation timelines estimated and how are vulnerable populations factored in? → A: Population density × road capacity × distance. 1.5x buffer multiplier for vulnerable population transport. Phased evacuation required to prevent road congestion.

### Session 2026-04-11 — Pass 2

- Q: What is the road network data source and structure for MVP? → A: Simplified graph loaded from a static road network JSON file with nodes (intersections) and edges (road segments with capacity, distance, accessibility features). Future versions integrate with live GIS services.
- Q: How are road segments classified into hazard zones from GeoJSON? → A: Use Shapely/geospatial library. Segments fully within Zone 1 are closed. Segments in Zone 2 get 50% capacity reduction. Segments in Zone 3 get 25% capacity reduction.
- Q: How should multi-hazard evacuation be handled when multiple hazards affect the same area? → A: Merge affected zones (union of GeoJSON polygons) and use the highest severity for overlapping areas. Routes must avoid all hazard zones.
- Q: What is the specific phased evacuation algorithm and phase transition criteria? → A: Phase 1: Zone 1 vulnerable. Phase 2: Zone 1 general. Phase 3: Zone 2 vulnerable. Phase 4: Zone 2 general. Phase 5: Zone 3 (advisory only). Each phase starts when previous phase reaches 50% completion or time threshold is met.
- Q: What plan versioning ID format should be used? → A: `ep-{incident_id}-v{N}` with optimistic concurrency. Each replan creates a new version. Previous versions remain immutable for audit.
- Q: What specific checks should the health endpoint report? → A: road_network_loaded, llm_connectivity, cosmos_connectivity, active_plan_count, processing_queue_depth.
- Q: What specific observability metrics should be emitted? → A: plan_generation_latency, replan_count, shelter_in_place_count, transport_requests_generated, zone_population_covered, route_computation_time, active_plans_gauge.
- Q: What specific human override capabilities should incident commanders have? → A: (a) Override route selections, (b) change zone boundaries, (c) reprioritize evacuation phases, (d) cancel/pause evacuation plans. All overrides logged with justification.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Receive Handoff and Generate Evacuation Plan (Priority: P1)

A cyclone is approaching a populated coastal region in Far North Queensland. The Risk Assessment Agent has produced a high-severity hazard assessment and escalated an evacuation recommendation to the Evacuation Agent via a handoff event. The Evacuation Agent receives the handoff, retrieves the associated hazard assessment and recommendation data, identifies the affected geographic area and population, and generates an evacuation plan. The plan includes recommended evacuation routes (considering known road closures, road capacity, and estimated congestion), designated assembly areas, estimated evacuation timelines, and a human-readable summary of the rationale. The incident commander reviews the plan on their dashboard, traces the recommendations back to the hazard assessment that triggered it, and decides whether to approve, modify, or reject the plan before public release.

**Why this priority**: This is the Evacuation Agent's core function — receiving escalated handoffs and producing actionable evacuation plans. Without this capability, the multi-agent coordination chain is broken: the Risk Assessment Agent escalates but nothing actionable is produced for incident commanders. The Constitution (Principle I) mandates that evacuation guidance is safety-critical output and must include explanations suitable for incident commanders.

**Independent Test**: Can be fully tested by sending a synthetic `AgentHandoffEvent` with `source_agent=risk_assessment`, `target_agent=evacuation`, and a payload containing a recommendation ID, summary, and assessment ID, then verifying that the agent produces an `EvacuationPlan` record with routes, assembly areas, timeline estimates, and a human-readable rationale linked to the originating assessment.

**Acceptance Scenarios**:

1. **Given** an `AgentHandoffEvent` arrives from the Risk Assessment Agent with a payload containing a recommendation ID, summary, and assessment ID for a flood scenario in Queensland, **When** the Evacuation Agent processes the handoff, **Then** it produces an `EvacuationPlan` record containing: the affected area, at least one evacuation route, designated assembly areas, estimated evacuation time, a confidence level, and a human-readable summary explaining the route selection rationale.
2. **Given** the hazard assessment referenced in the handoff identifies road closures in the affected area, **When** the Evacuation Agent generates routes, **Then** the plan excludes closed roads and routes through the closed segments, and the summary explicitly notes which roads are unavailable and why alternative routes were selected.
3. **Given** multiple handoffs arrive for the same incident within a short time window, **When** the Evacuation Agent processes each handoff, **Then** each successive evacuation plan receives a monotonically increasing version number for that incident and the previous plan version is marked as superseded.
4. **Given** a handoff arrives but the referenced hazard assessment cannot be retrieved from the data store, **When** the Evacuation Agent attempts to process the handoff, **Then** it logs the missing assessment, records a `handoff_rejected` audit entry with the reason, and does not produce an evacuation plan from incomplete data.

---

### User Story 2 — Compute Routes with Road Closure and Capacity Constraints (Priority: P2)

A major bushfire is spreading across multiple towns in regional NSW. Several roads have been closed by emergency services due to fire proximity, and remaining evacuation corridors have limited capacity. The Evacuation Agent receives updated road network status information and must compute evacuation routes that avoid closed roads, distribute evacuees across available corridors to prevent bottlenecks, and estimate travel times under load. The incident commander can see which routes are recommended, the expected capacity utilisation of each corridor, and why specific roads were excluded.

**Why this priority**: Route computation with real-world constraints is the core algorithmic capability that differentiates the Evacuation Agent from a simple alert system. The Constitution (Principle II) specifies that the Evacuation Agent MUST propose optimal routes with constraints (road closures, capacity, accessibility). Without constraint-aware routing, evacuation plans may direct people into danger or create fatal bottlenecks.

**Independent Test**: Can be fully tested by providing a road network graph with specific closures and capacity limits, an affected population estimate, and verifying that the generated routes avoid closed segments, distribute load across available corridors, and include capacity utilisation estimates.

**Acceptance Scenarios**:

1. **Given** the road network data indicates three potential evacuation corridors from an affected area, two of which are open and one of which is closed, **When** the Evacuation Agent computes routes, **Then** the plan includes only the two open corridors and explains that the third is excluded due to closure.
2. **Given** an affected population estimate exceeds the capacity of a single evacuation corridor, **When** the Evacuation Agent computes routes, **Then** it distributes the population across multiple corridors with estimated load percentages and flags any corridor that would exceed 80% capacity utilisation.
3. **Given** road conditions change during an active evacuation (a previously open road is now closed), **When** the Evacuation Agent receives updated road network data, **Then** it generates a new plan version that reroutes affected populations away from the newly closed road and includes a change summary highlighting what differs from the previous version.

---

### User Story 3 — Transport Coordination for Vulnerable Populations (Priority: P3)

A flood event is developing in a regional area with a significant elderly population, a disability care facility, and a primary school. Many residents do not have private transport, and some require wheelchair-accessible vehicles or medical transport. The Evacuation Agent identifies vulnerable population groups in the affected area, estimates transport requirements (vehicle types, number of vehicles, staging locations), and produces a transport coordination plan that is included as part of the overall evacuation plan. The incident commander can review the transport needs, approve the plan, and coordinate with transport providers.

**Why this priority**: Vulnerable populations are disproportionately affected by disasters and require explicit transport planning. The Constitution (Principle I, Life Safety First) mandates prioritisation of life preservation, and the feature description explicitly requires accessibility constraints (mobility-impaired, elderly, children). Without transport coordination, these groups may be left behind during self-evacuation scenarios.

**Independent Test**: Can be fully tested by providing an affected area with known vulnerable population data (care facilities, schools, mobility-impaired residents), and verifying that the plan includes specific transport requirements: vehicle types, estimated quantities, pickup locations, and priority ordering.

**Acceptance Scenarios**:

1. **Given** the affected area contains a registered disability care facility with 40 residents requiring wheelchair-accessible transport, **When** the Evacuation Agent generates the transport coordination plan, **Then** the plan includes a transport requirement for wheelchair-accessible vehicles, an estimated number of vehicles needed, a designated pickup location at the facility, and a priority level of "immediate."
2. **Given** the affected area contains a primary school with 200 enrolled students, **When** the Evacuation Agent generates the transport coordination plan, **Then** the plan includes a transport requirement for buses, estimated number of buses, the school address as the pickup location, and notes that child supervision must be maintained throughout evacuation.
3. **Given** the affected area has residents registered as requiring medical transport (e.g., dialysis patients, oxygen-dependent), **When** the Evacuation Agent generates the transport plan, **Then** medical transport needs are listed separately with priority "critical" and specific vehicle type requirements (e.g., ambulance, medical transport vehicle).

---

### User Story 4 — Evacuation Timeline Estimation (Priority: P4)

A Category 4 cyclone is forecast to make landfall in 18 hours. The incident commander needs to know whether there is sufficient time to evacuate the at-risk population before conditions become too dangerous for travel. The Evacuation Agent calculates estimated evacuation timelines for each zone: the time to mobilise, the time to travel each route under expected load, and the total clearance time. The commander can compare the clearance time against the hazard arrival window and make an informed decision about whether to order evacuation, shelter-in-place, or a phased approach.

**Why this priority**: The Constitution's success targets include enabling earlier evacuation decisions (24 hours earlier for at-risk populations). Timeline estimation is essential for incident commanders to decide whether evacuation is feasible within the available time window. Without it, commanders must rely on rough estimates that may either delay evacuation until too late or trigger unnecessary evacuations.

**Independent Test**: Can be fully tested by providing an affected area with a known population, route distances, and capacity constraints, and verifying that the plan includes zone-by-zone clearance time estimates that account for mobilisation time, travel time, and congestion.

**Acceptance Scenarios**:

1. **Given** an affected area has 5,000 residents across three evacuation zones, **When** the Evacuation Agent calculates timelines, **Then** each zone has an estimated clearance time that includes mobilisation time (time for people to prepare and depart) and travel time along the recommended route under expected load.
2. **Given** the estimated total clearance time exceeds the hazard arrival window, **When** the Evacuation Agent generates the plan, **Then** the plan flags the time deficit, identifies which zones cannot be cleared in time, and recommends shelter-in-place for those zones as an alternative.
3. **Given** a phased evacuation is recommended (outer zones first, inner zones after), **When** the Evacuation Agent generates the plan, **Then** the plan specifies the phase order, estimated start and completion times for each phase, and explains the phasing rationale.

---

### User Story 5 — Dynamic Route Updates as Conditions Change (Priority: P5)

During an active bushfire evacuation, conditions are changing rapidly. A road that was open two hours ago is now threatened by fire and has been closed. A new assembly area has been opened by the SES at a different location. The Evacuation Agent receives updated situational data (either via a new handoff from Risk Assessment with updated hazard information, or via road network status updates), detects that the current evacuation plan is affected, generates an updated plan version, and highlights the changes from the previous version. The incident commander can quickly see what changed, why, and decide whether to approve the updated plan.

**Why this priority**: Disasters are dynamic events where conditions change continuously. The Constitution (Non-Functional Requirements) mandates low-latency updates for time-critical decisions. Static plans become dangerous when conditions change; the agent must support iterative replanning to keep evacuation guidance current.

**Independent Test**: Can be fully tested by generating an initial plan, then providing an updated road network status (closing a previously open road), and verifying that a new plan version is generated with a change summary, revised routes, and a superseded status on the previous version.

**Acceptance Scenarios**:

1. **Given** an active evacuation plan exists for an incident, **When** a new handoff arrives from the Risk Assessment Agent with updated hazard data indicating expanded affected area, **Then** the Evacuation Agent generates a new plan version that covers the expanded area, marks the previous version as superseded, and includes a change summary listing the differences.
2. **Given** road network status changes during an active evacuation, **When** the Evacuation Agent receives the update, **Then** it evaluates whether the change affects any active evacuation route and, if so, generates a revised plan version within the low-latency update window.
3. **Given** conditions have not materially changed since the last plan version, **When** the Evacuation Agent receives a new handoff, **Then** it does not generate a redundant plan version and instead logs that the existing plan remains valid.

---

### User Story 6 — Human-Reviewable Evacuation Plans for Incident Commanders (Priority: P6)

After a major flood assessment triggers evacuation planning, the incident commander opens the evacuation plan on their dashboard. The plan is presented in a structured, human-readable format that includes: the affected area and population, recommended routes with rationale, assembly areas, transport coordination requirements, timeline estimates, confidence level, the data sources and assumptions that drove the plan, and a clear indication of what the commander needs to approve or modify before public release. The commander can trace every recommendation back to the hazard assessment and the signals that triggered it.

**Why this priority**: The Constitution (Principle I) mandates that the system produce explanations suitable for incident commanders and support human override for any autonomous action. The system MUST NOT bypass human authority — incident commanders must review and approve evacuation plans before they become operational. Traceability builds trust and enables informed decision-making.

**Independent Test**: Can be fully tested by generating an evacuation plan and verifying that the plan record contains all required sections (area, routes, assembly areas, transport, timelines, confidence, assumptions, traceability references) and that every route recommendation includes a rationale.

**Acceptance Scenarios**:

1. **Given** the Evacuation Agent has generated a complete evacuation plan, **When** the plan is retrieved for review, **Then** it includes: a summary of the triggering hazard, the affected geographic area, population estimate, all recommended routes with selection rationale, assembly area locations, transport requirements, phase-by-phase timeline, overall confidence level, and a list of assumptions.
2. **Given** an evacuation plan includes transport coordination for vulnerable populations, **When** the incident commander reviews the plan, **Then** the transport section clearly separates general evacuation transport from accessibility-specific transport with priority ordering.
3. **Given** an incident commander reviews a plan and decides to modify a route recommendation, **When** the override is submitted with justification, **Then** the modified plan is stored as a new version linked to the original, the override is recorded in the audit trail with user ID, role, justification, and timestamp, and the original plan remains intact and queryable.

---

### User Story 7 — Rehearsal and Simulation Mode (Priority: P7)

A resilience planner is conducting a tabletop exercise simulating a major bushfire across western Sydney. The exercise uses a simulation tenant to isolate test data from live operations. The Evacuation Agent processes handoffs arriving in the simulation context, generates evacuation plans using the simulated hazard data, and produces plans that are fully isolated from live incident data. The planner can review the plans, compare them with previous exercise results, and evaluate how the system performed without any risk of contaminating live operations.

**Why this priority**: The Constitution (Quality Gates) mandates scenario-based testing for bushfire, cyclone, and flood, and supports drills/tabletop exercises with stored scenarios. Simulation mode is essential for training, system validation, and continuous improvement without risk to live operations. Tenant isolation (spec 007) provides the underlying infrastructure.

**Independent Test**: Can be fully tested by sending handoffs in a simulation tenant context and verifying that the generated evacuation plans are isolated from live data, do not trigger real downstream actions, and carry the simulation tenant identifier.

**Acceptance Scenarios**:

1. **Given** a handoff arrives with a simulation tenant identifier, **When** the Evacuation Agent processes the handoff, **Then** the resulting evacuation plan is stored within the simulation tenant boundary and does not appear in live incident queries.
2. **Given** a simulation scenario is replayed with identical inputs, **When** the Evacuation Agent processes the handoffs, **Then** the resulting plans are comparable to previous runs (same route selections, same timeline estimates) when no configuration changes have occurred, enabling reproducibility verification.
3. **Given** a simulation evacuation plan is generated, **When** the plan is reviewed, **Then** it is clearly labelled as a simulation output and carries the simulation tenant identifier in all records.

---

### User Story 8 — Audit Trail of All Evacuation Decisions (Priority: P8)

After a week-long flood event across multiple NSW jurisdictions, the post-incident review team requests a complete record of every evacuation plan produced, every route recommendation made, every transport coordination decision, every dynamic update, every human override, and every degradation event that occurred during the event. The review team retrieves a chronological log with timestamps, input references, confidence levels, and the reasoning behind each decision.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates an append-only audit trail for safety-critical recommendations and actions. Evacuation guidance is explicitly identified as safety-critical output. Complete traceability is essential for post-incident reviews, coronial inquiries, continuous improvement, and maintaining public trust.

**Independent Test**: Can be fully tested by processing a sequence of handoffs resulting in evacuation plans, route updates, and overrides, then querying the audit trail to verify that every processing step has a corresponding record with all required fields.

**Acceptance Scenarios**:

1. **Given** the Evacuation Agent processes any incoming handoff, **When** the processing completes, **Then** an audit record is created containing: handoff ID, assessment ID, recommendation ID, plan ID (if produced), decision type, confidence level, and timestamp.
2. **Given** an incident commander overrides a route recommendation, **When** the override is recorded, **Then** an audit record captures the original route, the modified route, the commander's user ID, role, justification, and the override timestamp.
3. **Given** the Evacuation Agent experiences a degradation event (e.g., road network data unavailable), **When** the agent continues processing in degraded mode, **Then** an audit record documents the degradation, the fallback behaviour used, and the impact on plan confidence.

---

### Edge Cases

- What happens when a handoff arrives referencing an assessment ID that does not exist in the data store? The agent logs the error, records a `handoff_rejected` audit entry with the reason, and does not produce an evacuation plan.
- What happens when the road network data source is completely unavailable? The agent produces a degraded plan using last-known-good road network data (if available within a configurable staleness window, default 6 hours), flags the plan as degraded with reduced confidence, and logs the data source unavailability. If no road data is available within the staleness window, the agent produces a plan with generic evacuation guidance (evacuate away from hazard, seek high ground for floods) and flags it for immediate human review.
- What happens when the affected area has no registered vulnerable population data? The agent produces the plan without transport coordination for specific groups, notes the absence of vulnerable population data in the assumptions section, and recommends that the incident commander verify vulnerable population needs through local contacts.
- What happens when all available routes from an affected area are closed? The agent applies the shelter-in-place decision criteria: if the hazard timeline allows, it recommends shelter-in-place with specific building requirements (structural integrity, supplies, communication capability) and flags for human review. If the hazard poses an immediate threat with no viable route, the agent escalates to emergency services with maximum urgency, flags for immediate human intervention, and logs the situation in the audit trail.
- What happens when the same handoff ID is received more than once (duplicate delivery)? The agent performs idempotency checking on handoff ID and discards duplicates, logging the discard in the audit trail.
- What happens when a handoff arrives from a simulation tenant? The agent processes the handoff in the simulation context, produces plans isolated from live data, and does not trigger real downstream actions.
- What happens when the estimated clearance time far exceeds the hazard arrival window? The agent recommends phased evacuation with shelter-in-place for zones that cannot be cleared in time, flags the time deficit prominently, and assigns the plan a reduced confidence level.
- What happens when the Evacuation Agent itself becomes unhealthy? The health endpoint reports unhealthy status, the hosting platform detects the failure and restarts the agent, and unprocessed handoffs are re-delivered from the messaging infrastructure.
- What happens when population data for the affected area is outdated or unavailable? The agent uses the best available estimate, documents the data age in assumptions, and flags reduced confidence in the timeline estimates.

## Requirements *(mandatory)*

### Functional Requirements

#### Handoff Intake and Validation

- **FR-001**: The Evacuation Agent MUST consume `AgentHandoffEvent` records where `target_agent=evacuation` from the Risk Assessment Agent via the messaging infrastructure. The agent MUST acknowledge receipt of each handoff within 5 seconds of delivery.
- **FR-002**: Upon receiving a valid handoff, the Evacuation Agent MUST validate the handoff structure and verify that the referenced assessment ID and recommendation ID exist in the data store. If validation fails, the handoff MUST be rejected with a `handoff_rejected` audit record including the specific reason for rejection.
- **FR-003**: The Evacuation Agent MUST perform idempotency checking on `handoff_id` to avoid processing the same handoff twice within a configurable deduplication window (default: 10 minutes). Duplicate handoffs MUST be discarded and the discard recorded in the audit trail.
- **FR-004**: The Evacuation Agent MUST extract the affected geographic area, hazard type, severity level, and confidence score from the referenced hazard assessment to inform evacuation planning.

#### Route Computation

- **FR-005**: The Evacuation Agent MUST compute evacuation routes using a graph-based pathfinding algorithm (Dijkstra's variant) on a simplified road network graph. For MVP, the road network MUST be loaded from a static JSON configuration file containing nodes (intersections, each with geographic coordinates and zone membership) and edges (road segments, each with capacity in vehicles per hour, distance in kilometres, accessibility features such as wheelchair-accessible footpaths, and surface type). Future versions MAY integrate with live GIS services for dynamic road network updates. Route computation MUST consider: road closure status, road capacity (vehicles per hour), current estimated traffic load, road surface suitability (sealed vs. unsealed for different vehicle types), and distance to designated assembly areas. The LLM is used exclusively for generating human-readable route descriptions and reasoning — not for path computation. The agent does NOT require real-time traffic data; it uses road closure data from signals and capacity estimates.
- **FR-006**: The Evacuation Agent MUST exclude roads that are marked as closed in the current road network status data. The plan summary MUST explicitly list excluded roads and the reason for exclusion (closure type: emergency services closure, flood cut, fire proximity, structural damage).
- **FR-007**: When the affected population estimate exceeds the capacity of a single evacuation corridor, the Evacuation Agent MUST distribute the population across multiple corridors with estimated load percentages. Any corridor that would exceed 80% capacity utilisation MUST be flagged as congestion-risk.
- **FR-008**: The Evacuation Agent MUST support at minimum the following Australian disaster scenario types for route planning: bushfire (prioritise routes away from fire front and wind direction), cyclone (prioritise routes to inland shelters), flood (prioritise routes to higher ground, exclude flood-prone roads), earthquake (prioritise routes away from damaged infrastructure), and tsunami (prioritise routes to elevated ground inland).
- **FR-009**: Each computed route MUST include: the route path (ordered sequence of road segments), total distance, estimated travel time under current conditions, estimated travel time under evacuation load, capacity utilisation percentage, and a suitability assessment for different vehicle types (standard, heavy, accessible).

#### Evacuation Zone Model

- **FR-009a**: The Evacuation Agent MUST model evacuation zones as concentric zones from the hazard center, derived from the hazard assessment's `affected_area` GeoJSON. Zone 1 = immediate danger (evacuate first, highest priority), Zone 2 = likely impact (evacuate within hours), Zone 3 = possible impact (prepare to evacuate). Zone boundaries MUST be computed from the hazard assessment's geographic data and hazard type characteristics.
- **FR-009b**: Evacuation priority, timeline phasing, and resource allocation MUST respect zone ordering: Zone 1 populations are evacuated before Zone 2, and Zone 2 before Zone 3, unless route capacity constraints dictate otherwise.
- **FR-009c**: The Evacuation Agent MUST use a geospatial library (Shapely or equivalent) to determine which road segments fall within each hazard zone by intersecting road segment geometries with zone boundary polygons. Road segments whose geometry falls fully within Zone 1 MUST be marked as closed (capacity = 0). Road segments within Zone 2 MUST have their capacity reduced by 50%. Road segments within Zone 3 MUST have their capacity reduced by 25%. Road segments outside all zones retain full capacity.
- **FR-009d**: When multiple hazards affect the same geographic area (multi-hazard scenario), the Evacuation Agent MUST merge the affected zones by computing the geometric union of all hazard GeoJSON polygons. For overlapping areas where zone classifications conflict, the highest severity (lowest zone number) MUST apply. Routes MUST avoid all hazard zones from all active hazards. The merged zone boundaries MUST be reflected in the evacuation plan's affected area and used for all route computation, timeline estimation, and phased evacuation planning.

#### Transport Coordination for Vulnerable Populations

- **FR-010**: The Evacuation Agent MUST identify vulnerable population groups in the affected area using available population and facility data, classified into four vulnerability categories: (a) **mobility-impaired** — wheelchair users, walking aid users (transport: wheelchair-accessible vehicles, accessible buses), (b) **medical-dependent** — dialysis patients, oxygen-dependent individuals (transport: ambulance, medical transport vehicle), (c) **elderly/aged care** — residents of aged care facilities (transport: accessible buses, medical transport as needed), (d) **children/schools/childcare** — school-age children at registered schools and childcare centres (transport: buses with child supervision). Each category has specific transport type requirements as indicated.
- **FR-011**: For each identified vulnerable group, the Evacuation Agent MUST produce a transport REQUEST specifying: the vulnerability category (mobility-impaired, medical-dependent, elderly/aged care, children/schools/childcare), estimated number of individuals, required vehicle type (bus, wheelchair-accessible vehicle, ambulance, medical transport), estimated number of vehicles needed, designated pickup location, and a priority level (`critical` for medical-dependent, `immediate` for mobility-impaired and aged care, `high` for schools and childcare). The agent generates transport requests but does NOT directly dispatch vehicles — the Resource Allocation Agent (spec 011) handles actual dispatch based on availability.
- **FR-012**: Transport coordination requirements MUST be included as a distinct section within the evacuation plan, separate from general self-evacuation route guidance, so that incident commanders can address them independently.

#### Evacuation Timeline Estimation

- **FR-013**: The Evacuation Agent MUST compute estimated evacuation timelines for each evacuation zone (Zone 1, Zone 2, Zone 3) within the affected area. The baseline timeline is calculated as: `clearance_time = (population / road_capacity) × distance_km × 60` (result in minutes), where `population` is the zone population estimate (absolute count), `road_capacity` is aggregate vehicles-per-hour for the zone's corridors, and `distance_km` is the weighted average route distance. A 1.5x buffer multiplier MUST be applied to transport time estimates for zones containing vulnerable populations. Each timeline MUST include: mobilisation time (estimated time for the population to prepare and begin moving), travel time along the recommended route under expected load, and total clearance time (mobilisation + travel). Phased evacuation MUST be used to prevent road congestion when multiple zones share evacuation corridors.
- **FR-014**: When the total estimated clearance time exceeds the available time before hazard arrival (derived from the hazard assessment's time horizon), the Evacuation Agent MUST flag the time deficit, identify which zones cannot be cleared in time, and apply the following decision criteria: (a) if no viable evacuation route exists AND the hazard timeline allows sufficient time, recommend shelter-in-place with specific building requirements (structural integrity, supplies, communication capability); (b) if no viable evacuation route exists AND the hazard poses an immediate threat, escalate to emergency services with maximum urgency and flag for immediate human intervention. For zones that can be partially cleared, recommend phased evacuation with shelter-in-place for remaining populations. (c) When conditions change (e.g., road network update opens a new route), the agent MUST re-evaluate shelter-in-place zones for viable evacuation routes. If a viable route is found, a new plan version MUST be generated transitioning affected zones from shelter-in-place to evacuation, logged with `replanning_triggers=["shelter_to_evacuation_recovery"]`.
- **FR-015**: The Evacuation Agent MUST support phased evacuation planning using the following five-phase sequence: Phase 1 — Zone 1 vulnerable populations (mobility-impaired, medical-dependent, aged care, children); Phase 2 — Zone 1 general population; Phase 3 — Zone 2 vulnerable populations; Phase 4 — Zone 2 general population; Phase 5 — Zone 3 (advisory evacuation only, no mandatory transport coordination). Each phase MUST start when the previous phase reaches 50% completion (measured by estimated population departed from pickup/origin points) OR a configurable time threshold is met (default: phase duration estimate × 1.2), whichever occurs first. The plan MUST specify the phase order, estimated start and completion times for each phase, phase transition criteria, and the rationale for the phasing.

#### Dynamic Route Updates

- **FR-016**: The Evacuation Agent MUST trigger dynamic replanning of an active evacuation plan when any of the following conditions occur: (a) a new road closure is reported affecting an active route, (b) the hazard area expands by more than 10%, (c) an evacuation progress report shows greater than 30% delay against the current timeline, (d) a new higher-severity hazard assessment is received for the same incident, or (e) an incident commander issues a manual replanning trigger. If none of these conditions are met, the agent MUST log that the existing plan remains valid and not produce a redundant version.
- **FR-017**: Each new plan version MUST be identified using the format `ep-{incident_id}-v{N}` where `N` is a monotonically increasing integer for that incident, starting at 1. Plan creation MUST use optimistic concurrency control to prevent version conflicts during concurrent replanning. Each replan triggered by condition changes MUST create a new version. Previous plan versions MUST be marked as `superseded` when a new version is created and MUST remain immutable and queryable for audit purposes.
- **FR-018**: The change summary in an updated plan MUST include: which routes changed and why, which assembly areas changed, any changes to transport coordination, changes to timeline estimates, and the triggering event (new hazard data, road closure update, commander override).

#### Evacuation Plan Structure

- **FR-019**: Each `EvacuationPlan` MUST include the following sections: affected area (geographic boundary), population estimate, hazard summary (type, severity, time horizon), evacuation routes (with rationale for each), assembly areas, transport coordination requirements (if vulnerable populations present), phase-by-phase timeline, overall confidence level, data sources and assumptions, and traceability references (handoff ID, assessment ID, recommendation ID, input signal IDs).
- **FR-020**: The evacuation plan summary MUST be written in plain language suitable for incident commanders, consistent with AIIMS terminology and conventions. Technical details MUST be available in supporting sections but the summary MUST be immediately actionable.
- **FR-021**: Each evacuation plan MUST include a confidence level (0.0–1.0 numeric score and a categorical level: `low`, `medium`, `high`) reflecting the quality and completeness of the input data used to generate the plan.

#### Human Override

- **FR-022**: Incident commanders MUST be able to perform the following override actions on any evacuation plan: (a) **override route selections** — replace agent-recommended routes with commander-specified alternatives, (b) **change zone boundaries** — adjust the geographic extent of evacuation zones, (c) **reprioritize evacuation phases** — reorder or merge phases based on field conditions, (d) **cancel or pause evacuation plans** — halt an active plan's execution (status transitions to `cancelled` or `paused`). Each override action MUST update the plan's `status` field and record the `override_by_user_id`, `override_by_role`, `override_justification`, override action type, and `override_timestamp` in both the plan record and the audit trail. All overrides MUST be logged with mandatory justification text.
- **FR-023**: When an incident commander modifies a plan (e.g., changes a route, adds an assembly area, adjusts priorities), the modified plan MUST be stored as a new version linked to the original, preserving the original plan intact. The override audit record MUST be append-only and immutable.
- **FR-024**: The Evacuation Agent MUST NOT autonomously publish or execute evacuation orders. All plans MUST remain in `proposed` status until explicitly approved by an incident commander via the override endpoint (approve, reject, cancel, pause, resume actions — see contracts/health-endpoint.md §POST /override). The system supports but does not replace human authority over evacuation decisions.

#### Simulation and Reproducibility

- **FR-025**: The Evacuation Agent MUST support processing handoffs in simulation tenant contexts per spec 007. Plans produced in simulation MUST be isolated from live data and MUST NOT appear in live incident queries.
- **FR-026**: Given identical input data (same hazard assessment, same road network status, same population data) and identical configuration version, the Evacuation Agent MUST produce identical route selections, timeline estimates, and transport coordination recommendations, enabling reproducibility verification for scenario-based testing.
- **FR-027**: Each evacuation plan MUST record the configuration version and data snapshot used at generation time, enabling post-incident auditing and reproducibility verification.

#### Audit Trail

- **FR-028**: The Evacuation Agent MUST produce an audit record for every processing step, including: handoff receipt, handoff rejection, duplicate discard, plan generation, route computation, transport coordination, timeline estimation, plan versioning, dynamic updates, human overrides, degradation events, and health status changes. Audit storage MUST follow a three-tier degradation pattern: primary tier (Cosmos DB), fallback tier (in-memory buffer), emergency tier (local file). Each audit record MUST include: plan_version, routes, zones, populations, transport_requests, constraints_applied, replanning_triggers, and processing_duration.
- **FR-029**: Each audit record MUST be append-only (no updates or deletes) and MUST include the following base schema fields: record ID, handoff ID, plan ID (when applicable), decision type, confidence level, processing duration, decision rationale, agent version, configuration version, and timestamp. These base fields complement the domain-specific fields specified in FR-028 (plan_version, routes, zones, populations, transport_requests, constraints_applied, replanning_triggers); both sets apply to every `EvacuationDecisionRecord`. See data-model.md §EvacuationDecisionRecord for the canonical 22-field schema.
- **FR-030**: Audit records MUST be queryable by incident ID, plan ID, decision type, and time range to support post-incident reviews and coronial inquiries.

#### Graceful Degradation

- **FR-031**: When road network data is unavailable, the Evacuation Agent MUST attempt to use last-known-good road network data if available within a configurable staleness window (default: 6 hours). If no data is available within the window, the agent MUST produce a degraded plan with generic evacuation guidance appropriate to the hazard type (e.g., "evacuate away from fire front," "move to higher ground for floods") and flag the plan for immediate human review.
- **FR-032**: When population or facility data is unavailable, the Evacuation Agent MUST produce the plan without transport coordination details, note the data gap in the assumptions section, and flag the plan as incomplete regarding vulnerable population needs.
- **FR-033**: When the AI service used for plan summary generation is unavailable, the Evacuation Agent MUST fall back to template-based plan summaries using structured route and timeline data without AI enrichment. Confidence MUST be reduced by a multiplicative factor of 0.8 (i.e., `confidence_score = confidence_score × 0.8`). All fallback outputs MUST carry `generation_method=template_fallback`.
- **FR-034**: The Evacuation Agent MUST expose a `/health` endpoint that reports agent readiness. The health response MUST include the following specific checks: `road_network_loaded` (whether the static road network graph is loaded and valid), `llm_connectivity` (AI service reachability), `cosmos_connectivity` (data store reachability), `active_plan_count` (number of currently active evacuation plans), `processing_queue_depth` (number of pending handoffs awaiting processing), and `audit_store` (current audit write tier: `healthy` for Cosmos DB, `buffering` for in-memory buffer, `degraded` for file spill). The endpoint MUST respond within 1 second under normal operation.
- **FR-035**: The Evacuation Agent MUST NOT halt entirely when any single dependency is unavailable. It MUST continue processing with degraded capabilities and log all degradation events.

#### Content Safety

- **FR-036**: All AI-generated outputs (plan summaries, route rationale text) MUST pass through content safety validation before inclusion in any persisted record. If validation fails, the output MUST be replaced with a structured template fallback, the plan MUST carry `generation_method=safety_fallback`, and the failure recorded in the audit trail with `decision_type=content_safety_failure`. Template-based fallback text is pre-approved and does not require runtime content safety checks.

### Non-Functional Requirements

#### Scalability

- **NFR-001**: The Evacuation Agent MUST handle at minimum 50 concurrent evacuation plans (across different incidents/zones) during peak disaster events (lower than Risk Assessment's 100 concurrent assessments because not all assessments trigger evacuation). Horizontal scaling via Azure Container Apps auto-scaling MUST be used to scale processing capacity based on message queue depth.

#### Observability

- **NFR-002**: The Evacuation Agent MUST emit telemetry for operational monitoring. The following metrics MUST be tracked: `plan_generation_latency` (p50, p95, p99 — time from handoff receipt to plan persisted), `route_computation_time` (duration of graph-based pathfinding per plan), `replan_count` (number of replans per incident), `shelter_in_place_count` (number of shelter-in-place recommendations issued), `transport_requests_generated` (count of TransportRequirement records created), `zone_population_covered` (population estimate per zone included in plans), `active_plans_gauge` (current number of active non-superseded plans), `dynamic_update_rate` (plan versions per incident), `override_rate` (percentage of plans modified by commanders), `degradation_events` (count per time window), and `handoff_success_rate`. All metrics MUST support alerting thresholds.

### Key Entities

- **EvacuationPlan**: A versioned, human-reviewable plan for evacuating an affected area produced by analysing escalated hazard assessments and computing constrained routes. Key attributes: plan ID (format: `ep-{incident_id}-v{N}` where N is the version number), incident ID, version number (monotonically increasing per incident, managed via optimistic concurrency control), affected area (geographic boundary — may be a merged union of multiple hazard GeoJSON polygons in multi-hazard scenarios), population estimate, hazard summary (type, severity, time horizon — from the triggering assessment), evacuation routes (list of `EvacuationRoute` records), assembly areas (list of locations with capacity), transport coordination (list of `TransportRequirement` records for vulnerable populations), five-phase timeline (Zone 1 vulnerable → Zone 1 general → Zone 2 vulnerable → Zone 2 general → Zone 3 advisory), overall confidence level (0.0–1.0 numeric and categorical low/medium/high), status (`proposed`, `approved`, `rejected`, `superseded`, `expired`, `cancelled`, `paused`), change summary (for version > 1), generation method (`ai_assisted`, `template_fallback`, or `safety_fallback`), configuration version, data snapshot references, traceability references (handoff ID, assessment ID, recommendation ID), assumptions, override metadata (user ID, role, justification, action type, timestamp — when applicable), and timestamps (created, updated, valid_until). Plans are immutable once persisted; new plans create new versions. Status transitions (`proposed` → `approved`/`rejected`/`superseded`/`cancelled`/`paused`) are the only permitted mutation on existing records.

- **EvacuationRoute**: A single evacuation corridor within a plan. Key attributes: route ID, ordered sequence of road segments (path), origin zone, destination assembly area, total distance, estimated travel time under normal conditions, estimated travel time under evacuation load, capacity (vehicles per hour), estimated capacity utilisation percentage, congestion risk flag (true if utilisation > 80%), suitability by vehicle type (standard, heavy, accessible), excluded roads with reasons, and selection rationale.

- **TransportRequirement**: A transport need for a specific vulnerable population group. Key attributes: requirement ID, group type (aged care, disability care, hospital, school/childcare, mobility-impaired, medical-dependent), estimated number of individuals, required vehicle type (bus, wheelchair-accessible, ambulance, medical transport), estimated number of vehicles, designated pickup location, destination assembly area, priority level (`critical`, `immediate`, `high`), and special considerations (e.g., medical equipment, child supervision).

- **EvacuationDecisionRecord**: An audit trail entry capturing a single processing step or decision made by the Evacuation Agent. Key attributes: record ID, handoff ID, plan ID (when applicable), decision type (handoff_received, handoff_rejected, duplicate_discarded, assessment_retrieved, road_network_loaded, zones_computed, routes_computed, transport_coordinated, timeline_estimated, plan_generated, plan_updated, override_applied, shelter_in_place_recommended, degradation_detected, content_safety_failure), confidence level, processing duration, decision rationale, agent version, configuration version, and timestamp. Append-only; no updates or deletes permitted.

### Assumptions

- The Risk Assessment Agent (spec 012) delivers handoffs in the `AgentHandoffEvent` format with payload containing `recommendationId`, `summary`, and `assessmentId`. The Evacuation Agent does not re-assess hazard severity — it consumes the assessment as provided.
- Handoff delivery uses the same messaging infrastructure as other agent-to-agent communication, with at-least-once delivery semantics. The Evacuation Agent handles duplicate delivery via idempotency checking.
- Road network data (road segments, closures, capacity) is available from the data ingestion layer (spec 006). The format and update frequency of road network data are defined by the data source governance (spec 005). The Evacuation Agent consumes this data but does not manage the data source.
- Population and facility data (aged care facilities, hospitals, schools, disability care facilities, registered mobility-impaired residents) is available from authoritative sources through the data ingestion layer. The granularity and completeness of this data varies by jurisdiction.
- Assembly area locations and capacities are pre-configured per jurisdiction and maintained as reference data. The Evacuation Agent selects from available assembly areas but does not create new ones.
- The Evacuation Agent produces plans and recommendations but does not directly communicate with the public. Public communication of evacuation orders is the Communication Agent's responsibility (spec 008).
- Tenant isolation (simulation vs. live) is enforced at the data layer per spec 007. The Evacuation Agent respects tenant boundaries for all plans, audit records, and data queries.
- Mobilisation time defaults are configurable per hazard type and jurisdiction (e.g., 30 minutes for a sudden-onset event like a tsunami, 2 hours for a slower-onset event like a flood with advance warning). These defaults are based on Australian emergency management best practices.
- The AI service used for plan summary generation follows the same `_generate_with_fallback` pattern as other agents, with automatic template fallback when unavailable.

### Out of Scope

- Replacement of incident commander authority over evacuation orders. The Evacuation Agent proposes plans; human commanders approve and execute them.
- Direct public communication of evacuation orders — the Communication Agent (spec 008) is responsible for alert composition and delivery.
- Real-time GPS tracking of individual evacuees or vehicles during evacuation.
- Real-time traffic management or signal control during evacuation.
- Management of road network data sources — the agent consumes road data from the data ingestion layer (spec 006).
- Creation or management of assembly areas — the agent selects from pre-configured assembly areas.
- Resource procurement or dispatch — resource coordination is the Resource Allocation Agent's responsibility (spec 011).
- Cross-incident evacuation coordination (e.g., two simultaneous disasters sharing evacuation corridors) — deferred to v2. Each plan is scoped to a single incident in v1.
- Graphical map rendering of evacuation routes — the agent produces structured route data; visual rendering is the web UI's responsibility.

### Dependencies

- **spec 001 (Disaster Response Hub)**: Defines the AgentHandoffEvent, Recommendation, and HazardAssessment data models that the Evacuation Agent consumes.
- **spec 005 (Data Source Governance)**: Defines the data source registry and trust tiers that inform road network and population data reliability.
- **spec 006 (Data Ingestion & Storage)**: Defines the data store from which the Evacuation Agent retrieves road network data, population data, facility data, and assembly area reference data.
- **spec 007 (Simulation & Tenant Isolation)**: Defines the tenant isolation model that the Evacuation Agent must respect for simulation vs. live processing.
- **spec 012 (Risk Assessment Agent)**: Defines the upstream agent that produces handoffs consumed by the Evacuation Agent. The handoff payload format (`recommendationId`, `summary`, `assessmentId`), escalation criteria (severity ≥ high AND confidence ≥ 0.6), and data model are defined in spec 012.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Initial evacuation plans are produced within 30 seconds of receiving a valid handoff from the Risk Assessment Agent, ensuring timely guidance during active incidents. Dynamic replanning (triggered by condition changes on an active plan) MUST complete within 15 seconds. The replanning SLA is shorter because the agent can incrementally update the existing plan graph rather than computing from scratch. Route computation is more complex than monitoring/risk assessment, justifying longer SLAs than those agents. If processing exceeds the applicable SLA, the plan MUST still complete but MUST log an SLA breach event with the actual processing duration.
- **SC-002**: 100% of evacuation plans include traceable references — every plan links back to the handoff, assessment, and recommendation that triggered it, verifiable through the audit trail.
- **SC-003**: Route computation correctly excludes closed roads in 100% of test cases — no plan recommends a route through a road segment marked as closed in the current road network data.
- **SC-004**: Evacuation plans for areas with known vulnerable populations include transport coordination in 100% of cases — no vulnerable group is left without a transport plan when population data is available.
- **SC-005**: When the estimated clearance time exceeds the hazard arrival window, the time deficit is flagged in 100% of cases and shelter-in-place is recommended for zones that cannot be cleared.
- **SC-006**: Given identical inputs and configuration, the Evacuation Agent produces identical route selections and timeline estimates in 100% of reproducibility test runs.
- **SC-007**: Every processing step has a corresponding audit record — audit completeness is 100% verifiable via reconciliation of handoff IDs processed vs. audit records created.
- **SC-008**: When road network data is unavailable, the agent continues producing degraded plans with no processing interruption — measured as 0% handoff drop rate during data source outage periods.
- **SC-009**: At least 90% of incident commanders in scenario-based exercises rate the evacuation plans as clear, actionable, and traceable, using a structured post-exercise survey.
- **SC-010**: Dynamic route updates are generated within 15 seconds of receiving updated situational data (see replanning triggers: new road closure, hazard area expansion >10%, progress delay >30%, higher-severity assessment, or manual trigger), supporting the Constitution's target of enabling evacuation decisions 24 hours earlier for at-risk populations.

## Assumptions

Scoped to this spec's domain (evacuation routing + lead-time recommendations). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-022**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-023** [DECISION]: This spec's deliverables (evacuation routing + lead-time recommendations) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`); responsible technical agents - planning-officer, operations-officer, resilience-planner - are consulted via the `agent` tool during authoring and review.
- **ASM-024**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.
- **ASM-025** [RISK]: AU-only data residency (constitution NON-NEGOTIABLE #2; Azure `australiaeast` / `australiasoutheast` only) is in tension with the capstone Asia framing (PH / JP / BD sovereign-data handling). Resolution requires a constitution-level amendment owned outside this feature (see `specs/028-capstone-alignment/research.md` D-009). `linked_gaps:` constitution NON-NEGOTIABLE #2. `status:` Open.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-019**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-020**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-021** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-007**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-007.md` (created in feature 028 polish).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-022** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (planning-officer, operations-officer, resilience-planner) sign off on country-specific calibration.
- **SCP-023**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-024**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.


## Capstone-Country Hypotheses (Feature 028 / US2)

> Three deferred capstone-country hypotheses for evacuation routing + lead-time recommendations. Each cites an evidence stub at `specs/009-evacuation-agent/evidence/HYP-<id>.md` conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. `Status = Not tested` until D-009 capstone-reinterpretation clears and per-cohort preconditions are met.

- **HYP-030** [PH deferred]: We believe pre-warned typhoon evacuation routing across archipelagic terrain will produce recommended evacuation start >= 24h earlier than the unaided NDRRMC reference timeline for the Philippines operator persona; we will know we are wrong if mean lead-time uplift < 12h across exercise scenarios during PH typhoon season Jun-Nov is observed in the measurement window (PH typhoon season Jun-Nov).
  - **Falsification**: mean lead-time uplift < 12h across exercise scenarios during PH typhoon season Jun-Nov.
  - **Evidence stub**: `specs/009-evacuation-agent/evidence/HYP-030.md` (created by feature 028 / US2 / T034..T038).
- **HYP-031** [JP deferred]: We believe immediate-onset earthquake / tsunami evacuation routing in dense urban topology will produce first safe-route recommendation issued within 60s of JMA seismic warning, prioritising vertical evacuation where applicable for the Japan operator persona; we will know we are wrong if first-recommendation latency p95 > 120s during quarterly tabletop exercises is observed in the measurement window (JP continuous; quarterly review).
  - **Falsification**: first-recommendation latency p95 > 120s during quarterly tabletop exercises.
  - **Evidence stub**: `specs/009-evacuation-agent/evidence/HYP-031.md` (created by feature 028 / US2 / T034..T038).
- **HYP-032** [BD deferred]: We believe pre-warned monsoon flood evacuation routing across deltaic / cyclone-shelter network (CPP) will produce recommended evacuation start >= 24h earlier than the unaided BD reference timeline using CPP shelter capacity awareness for the Bangladesh operator persona; we will know we are wrong if mean lead-time uplift < 12h across exercise scenarios during BD monsoon Apr-Sep is observed in the measurement window (BD monsoon Apr-Sep).
  - **Falsification**: mean lead-time uplift < 12h across exercise scenarios during BD monsoon Apr-Sep.
  - **Evidence stub**: `specs/009-evacuation-agent/evidence/HYP-032.md` (created by feature 028 / US2 / T034..T038).


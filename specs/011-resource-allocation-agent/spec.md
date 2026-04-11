# Feature Specification: Resource Allocation Agent — Demand Prioritisation, Resource Matching, Deployment Planning, and Multi-Incident Coordination

**Feature Branch**: `011-resource-allocation-agent`  
**Created**: 2026-04-17  
**Status**: Draft  
**Input**: User description: "The Resource Allocation Agent receives coordination tasks from Risk Assessment and transport requests from Evacuation. It must: (1) prioritize resource allocation using objective criteria (life safety > property > environment), (2) match available resources to needs considering location, capability, and availability, (3) generate deployment recommendations for incident commanders, (4) track resource status and utilization, (5) handle competing demands across multiple incidents, (6) support human override of allocation decisions, (7) coordinate with evacuation agent for transport dispatch, and (8) maintain full audit trail."

## Clarifications

### Session 2026-04-11

- Q: What specific resource categories and sub-types does the system manage? → A: Four categories: (a) vehicles (ambulances, fire trucks, buses, helicopters), (b) personnel (paramedics, firefighters, SES volunteers, police), (c) supplies (water, food, medical kits, generators, fuel), (d) facilities (evacuation centers, hospitals, staging areas). Each has capacity, capability, and location attributes.
- Q: What matching algorithm does the MVP use for resource-to-demand assignment? → A: Greedy assignment using scoring function: score = capability_match × (1/distance) × availability_factor × priority_weight. Assign highest-scoring resource to highest-priority demand first. Linear programming optimisation deferred to v2.
- Q: How are competing demands across incidents resolved when priority tiers and severity are equal? → A: Four-level tiebreaking hierarchy: (a) life safety incidents first, (b) higher severity assessment, (c) closer proximity, (d) earlier request timestamp. Cross-incident recommendations include trade-off analysis showing what each incident loses.
- Q: What are the specific performance SLAs for allocation operations? → A: Allocation plan generation within 15 seconds. Resource status updates processed within 5 seconds. Cross-incident analysis within 30 seconds.
- Q: What storage degradation pattern does the audit trail use? → A: Three-tier degradation: Cosmos DB → in-memory buffer → local file fallback. Audit records include: plan_version, demands, assignments, scoring_rationale, resources_considered, resources_excluded_reason, processing_duration.

### Session 2026-04-11 (Pass 2)

- Q: What is the formal resource state machine? → A: States: `available` → `assigned` (plan generated) → `en_route` (dispatch confirmed) → `deployed` (on-site) → `returning` → `available`. Also: `unavailable` (broken/destroyed), `reserved` (held for specific incident). All transitions logged in audit trail.
- Q: How does capability matching work in detail? → A: Each resource has a capabilities list (e.g., ambulance: [medical_transport, patient_stabilization]). Each demand has required_capabilities. A resource matches if it has ALL required capabilities. capability_match = 1.0 if full match, 0.0 if not (binary for MVP).
- Q: What distance calculation algorithm is used? → A: Haversine formula for straight-line distance between resource location and demand location. Road distance optimisation deferred to v2.
- Q: What plan versioning pattern is used? → A: Same pattern as other agents — `rdp-{incident_id}-v{N}` with optimistic concurrency. Each re-allocation creates new version.
- Q: What does the health endpoint report? → A: inventory_loaded, llm_connectivity, cosmos_connectivity, active_plan_count, pending_demands, processing_queue_depth.
- Q: What core observability metrics are tracked? → A: allocation_latency, resource_utilization_rate, unmet_demand_count, cross_incident_conflicts, override_count, plan_versions_per_incident, status_update_latency.
- Q: How is the LLM used in allocation? → A: LLM used ONLY for generating human-readable allocation rationale text. All matching/scoring is algorithmic. When LLM unavailable, use template-based rationale. Reduce confidence by 20% (multiplicative) in fallback.
- Q: How is partial allocation handled? → A: Generate a partial plan clearly marking unfulfilled demands with reasoning. Flag for commander attention. Never silently drop demands.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Receive Handoff and Generate Resource Deployment Plan (Priority: P1)

A major flood event is developing across multiple communities in south-east Queensland. The Risk Assessment Agent has produced a hazard assessment with coordination tasks requiring emergency supplies, personnel, and equipment. It escalates a `resource_allocation` recommendation to the Resource Allocation Agent via a handoff event. The Resource Allocation Agent receives the handoff, retrieves the associated recommendation and hazard assessment data, identifies the resource demands implied by the coordination tasks, queries the available resource inventory, and generates a resource deployment plan. The plan includes recommended resource assignments (matching available resources to identified needs by type, capability, and proximity), estimated deployment timelines, and a human-readable summary explaining the allocation rationale and any trade-offs. The incident commander reviews the plan on their dashboard, traces the recommendations back to the hazard assessment that triggered them, and decides whether to approve, modify, or reject the plan before dispatch.

**Why this priority**: This is the Resource Allocation Agent's core function — receiving escalated handoffs from Risk Assessment and producing actionable deployment plans. Without this capability, the multi-agent coordination chain is broken: risk assessments identify needs, but no concrete resource assignments are produced for incident commanders. The Constitution (Principle II) mandates that the Resource Allocation Agent prioritise supplies and personnel allocation using objective criteria and declared policies.

**Independent Test**: Can be fully tested by sending a synthetic `AgentHandoffEvent` with `source_agent=risk_assessment`, `target_agent=resource_allocation`, and a payload containing a recommendation ID, summary, and assessment ID, then verifying that the agent produces a `ResourceDeploymentPlan` record with resource assignments, deployment timelines, allocation rationale, and traceability references back to the originating assessment.

**Acceptance Scenarios**:

1. **Given** an `AgentHandoffEvent` arrives from the Risk Assessment Agent with a payload containing a recommendation ID, summary, and assessment ID for a flood scenario, **When** the Resource Allocation Agent processes the handoff, **Then** it produces a `ResourceDeploymentPlan` record containing: the incident ID, identified resource demands, at least one resource assignment matching a demand to an available resource, estimated deployment timelines, a confidence level, and a human-readable summary explaining the allocation rationale.
2. **Given** the hazard assessment referenced in the handoff generates multiple coordination tasks with different priority levels, **When** the Resource Allocation Agent processes the handoff, **Then** critical-priority demands are assigned resources before high-priority demands, and high before moderate, consistent with the life safety prioritisation hierarchy.
3. **Given** multiple handoffs arrive for the same incident within a short time window, **When** the Resource Allocation Agent processes each handoff, **Then** each successive deployment plan receives a monotonically increasing version number for that incident and the previous plan version is marked as superseded.
4. **Given** a handoff arrives but the referenced recommendation or assessment cannot be retrieved from the data store, **When** the Resource Allocation Agent attempts to process the handoff, **Then** it logs the missing data, records a `handoff_rejected` audit entry with the reason, and does not produce a deployment plan from incomplete data.

---

### User Story 2 — Match Available Resources to Demands (Priority: P2)

A bushfire is threatening several towns in regional NSW. The Resource Allocation Agent has identified demands for water tankers, firefighting crews, emergency medical teams, and temporary shelters. The agent queries the resource inventory to find available resources, evaluates each candidate resource against the demand requirements (type match, capability, current location, and availability status), and produces a ranked list of assignments that minimise deployment time while maximising coverage. Where a demand cannot be fully met from available resources, the agent flags the shortfall and recommends the best partial allocation. The incident commander can see which resources are recommended for each need, why they were selected, and where gaps exist.

**Why this priority**: Resource-demand matching is the core algorithmic capability that differentiates this agent from a simple task queue. The Constitution (Principle II) requires the Resource Allocation Agent to prioritise using objective criteria. Without intelligent matching that considers location, capability, and availability, resource deployment would be inefficient and potentially endanger lives by sending unsuitable or distant resources.

**Independent Test**: Can be fully tested by providing a set of resource demands (typed, prioritised, geolocated) and a resource inventory with known locations and capabilities, then verifying that the agent produces assignments that respect type compatibility, prefer closer resources, and flag unmet demands.

**Acceptance Scenarios**:

1. **Given** a demand for 3 water tankers at a specific location and the inventory contains 5 water tankers at various distances, **When** the Resource Allocation Agent performs matching, **Then** it assigns the 3 closest available water tankers and the assignment records include estimated travel time from each resource's current location.
2. **Given** a demand for a specialised hazmat team and no hazmat-capable teams are available in the inventory, **When** the Resource Allocation Agent performs matching, **Then** it flags the demand as `unmet`, includes the shortfall in the plan summary, and does not assign an incompatible resource type as a substitute.
3. **Given** a demand for emergency medical personnel and two candidate teams are equidistant, **When** the Resource Allocation Agent performs matching, **Then** it prefers the team with higher capability match (e.g., paramedic team over general first-aid volunteers) and documents the selection rationale.
4. **Given** a resource is currently assigned to another active incident, **When** the Resource Allocation Agent evaluates that resource for a new demand, **Then** it marks the resource as `unavailable` and does not reassign it unless the new demand has higher priority and reallocation is explicitly triggered.

---

### User Story 3 — Process Transport Dispatch Requests from Evacuation Agent (Priority: P3)

A cyclone is approaching a coastal community with a large elderly population and a disability care facility. The Evacuation Agent has generated an evacuation plan that includes transport requirements for vulnerable populations — wheelchair-accessible vehicles for the care facility, buses for a primary school, and ambulances for medical-dependent residents. The Evacuation Agent sends transport dispatch requests to the Resource Allocation Agent. The Resource Allocation Agent receives these requests, matches them against the available transport resource inventory, generates dispatch assignments for each transport need, and produces a transport dispatch plan with vehicle assignments, estimated arrival times at pickup locations, and routing coordination. The incident commander reviews the combined transport dispatch alongside the evacuation plan.

**Why this priority**: Transport coordination for vulnerable populations is explicitly required by the Constitution (Principle I, Life Safety First) and the Evacuation Agent (spec 009) generates transport requirements that it cannot fulfil on its own — it depends on the Resource Allocation Agent to match transport needs to available vehicles. Without this capability, vulnerable populations identified by the Evacuation Agent have no concrete transport assignments.

**Independent Test**: Can be fully tested by sending transport requirement records (specifying vehicle types, quantities, pickup locations, and priority levels) and a transport resource inventory, then verifying that the agent produces dispatch assignments matching vehicles to requirements by type and proximity, with critical-priority medical transport assigned first.

**Acceptance Scenarios**:

1. **Given** a transport request for 4 wheelchair-accessible vehicles at a disability care facility and the inventory contains 6 such vehicles at various locations, **When** the Resource Allocation Agent processes the request, **Then** it assigns the 4 closest available wheelchair-accessible vehicles, records estimated arrival times at the facility, and marks the assigned vehicles as `assigned` in the resource inventory.
2. **Given** a transport request for ambulances (priority: `critical`) and a transport request for buses (priority: `high`) arrive simultaneously, **When** the Resource Allocation Agent processes both, **Then** ambulance assignments are completed before bus assignments, consistent with the priority hierarchy.
3. **Given** a transport request for 10 buses but only 6 buses are available in the inventory, **When** the Resource Allocation Agent processes the request, **Then** it assigns the 6 available buses, flags a shortfall of 4 buses, and includes the deficit in the deployment plan summary for incident commander awareness.
4. **Given** a transport dispatch request references an evacuation plan ID, **When** the Resource Allocation Agent produces dispatch assignments, **Then** each assignment includes the originating evacuation plan ID and transport requirement ID for end-to-end traceability.

---

### User Story 4 — Handle Competing Demands Across Multiple Incidents (Priority: P4)

Two simultaneous disasters are occurring: a bushfire in regional NSW and a flash flood in suburban Brisbane. Both incidents have generated resource demands for emergency personnel, vehicles, and supplies. The shared resource pool cannot satisfy all demands from both incidents simultaneously. The Resource Allocation Agent evaluates the competing demands using the prioritisation hierarchy (life safety > property protection > environmental protection), considers the severity and urgency of each incident, and produces a cross-incident allocation plan that distributes the constrained resource pool to maximise life-safety outcomes. Where resources are reallocated from a lower-priority incident to a higher-priority one, the plan explicitly documents the trade-off and flags the resulting gap for the affected incident commander.

**Why this priority**: Multi-incident resource contention is a realistic operational scenario during the Australian disaster season. The Constitution's target of 30% improvement in resource deployment efficiency depends on intelligent cross-incident allocation. Without this capability, resources may be allocated on a first-come-first-served basis rather than by objective need, violating the Constitution's requirement for objective criteria and declared policies.

**Independent Test**: Can be fully tested by creating two incidents with overlapping resource demands that exceed total inventory, assigning different severity levels, and verifying that the higher-severity incident receives preferential allocation with documented trade-offs.

**Acceptance Scenarios**:

1. **Given** two active incidents both requiring emergency medical teams, the bushfire is `critical` severity and the flood is `high` severity, and only enough medical teams exist to fully serve one incident, **When** the Resource Allocation Agent allocates across incidents, **Then** the critical-severity bushfire receives medical teams first, the flood incident receives remaining teams, and the shortfall is documented with the reason.
2. **Given** a new critical-severity incident arises while resources are already assigned to a moderate-severity incident, **When** the Resource Allocation Agent evaluates the new demand, **Then** it recommends reallocation of resources from the lower-severity incident (with the lower-severity plan updated to reflect the reduction), and the reallocation is flagged for incident commander approval before execution.
3. **Given** two incidents of equal severity are competing for the same resource pool, **When** the Resource Allocation Agent performs allocation, **Then** it distributes resources proportionally based on assessed population at risk and proximity, and documents the distribution rationale.

---

### User Story 5 — Human Override of Allocation Decisions (Priority: P5)

An incident commander reviewing a resource deployment plan disagrees with the agent's recommendation to allocate a heavy rescue team to a property-protection task when a life-safety evacuation is underway in an adjacent area. The commander overrides the allocation, reassigning the rescue team to support the evacuation. The Resource Allocation Agent records the override (who, what role, justification, timestamp), generates a new plan version reflecting the commander's changes, and adjusts downstream assignments as needed. The original plan and the override rationale remain in the audit trail.

**Why this priority**: The Constitution (Principle I) mandates human override for any autonomous action, including resource dispatch recommendations. The system MUST NOT autonomously deploy resources without commander approval. Overrides are essential for incorporating field-level situational awareness that the agent may not have.

**Independent Test**: Can be fully tested by generating a resource deployment plan, submitting an override request with a user ID, role, justification, and modified assignments, then verifying that a new plan version is created, the override is recorded immutably, and the original plan remains intact.

**Acceptance Scenarios**:

1. **Given** a resource deployment plan in `proposed` status assigns a rescue team to task A, **When** an incident commander overrides the assignment to reassign the team to task B with justification, **Then** a new plan version is created with the updated assignment, the override is recorded with user ID, role, justification, and timestamp, and the original plan remains queryable.
2. **Given** an incident commander approves a deployment plan, **When** the approval is submitted, **Then** the plan status transitions from `proposed` to `approved` and an audit record captures the approval action with commander details.
3. **Given** an incident commander cancels a deployment plan, **When** the cancellation is submitted with justification, **Then** the plan status transitions to `cancelled`, all pending resource assignments are released back to the available pool, and the cancellation is recorded in the audit trail.
4. **Given** a resource deployment plan is in `approved` status, **When** the agent receives new information that would change assignments, **Then** the agent produces a new plan version but does NOT automatically supersede the approved plan — the new version is presented for commander review.

---

### User Story 6 — Track Resource Status and Utilisation (Priority: P6)

During a multi-day flood response, the incident commander needs to understand the current state of all deployed resources: which teams are active, which vehicles are in transit, which supplies have been consumed, and what remains available. The Resource Allocation Agent maintains an up-to-date view of resource status by processing status update signals (category: `resource_status`), tracking assignments against the resource inventory, and computing utilisation metrics. The commander can query current resource status by type, location, and assignment, and the agent highlights resources approaching exhaustion or requiring rotation.

**Why this priority**: Resource tracking is essential for sustained multi-day operations. Without visibility into current resource status, incident commanders cannot make informed allocation decisions and the agent cannot produce accurate deployment plans. This capability supports the Constitution's target of 30% improvement in resource deployment efficiency.

**Independent Test**: Can be fully tested by creating an initial resource inventory, processing a sequence of status update signals (deployed, in-transit, consumed, returned), and verifying that the agent's resource status view accurately reflects each update, with utilisation metrics computed correctly.

**Acceptance Scenarios**:

1. **Given** a resource is assigned and deployed to an incident, **When** a `resource_status` signal reports the resource has arrived on-site, **Then** the agent updates the resource status to `deployed` and records the status change timestamp in the audit trail.
2. **Given** a consumable supply (e.g., water, medical kits) has been partially consumed, **When** a status update reports the remaining quantity, **Then** the agent updates the remaining quantity and flags the supply for replenishment when it falls below 20% of initial stock.
3. **Given** a personnel team has been deployed for more than 12 hours continuously, **When** the agent evaluates resource status, **Then** it flags the team for rotation and recommends a replacement in the next allocation cycle.
4. **Given** multiple resources are tracked across multiple incidents, **When** the incident commander queries resource utilisation, **Then** the agent provides a summary showing: total resources by type, assigned vs. available counts, utilisation percentage per type, and resources flagged for rotation or replenishment.

---

### User Story 7 — Rehearsal and Simulation Mode (Priority: P7)

A state emergency management agency is conducting a tabletop exercise simulating concurrent bushfire and flood events. The exercise uses a simulation tenant to isolate test data from live operations. The Resource Allocation Agent processes handoffs arriving in the simulation context, generates deployment plans using simulated resource inventories and demands, and produces plans that are fully isolated from live incident data. Planners can evaluate the agent's allocation decisions, test cross-incident prioritisation logic, and compare results with previous exercises.

**Why this priority**: The Constitution (Quality Gates) mandates scenario-based testing for bushfire, cyclone, and flood, and supports drills and tabletop exercises. Simulation mode is essential for training, system validation, and continuous improvement without risk to live operations. Tenant isolation (spec 007) provides the underlying infrastructure.

**Independent Test**: Can be fully tested by sending handoffs in a simulation tenant context with a simulated resource inventory and verifying that the generated plans are isolated from live data, do not trigger real dispatch actions, and carry the simulation tenant identifier.

**Acceptance Scenarios**:

1. **Given** a handoff arrives with a simulation tenant identifier, **When** the Resource Allocation Agent processes the handoff, **Then** the resulting deployment plan is stored within the simulation tenant boundary and does not appear in live incident queries.
2. **Given** a simulation scenario is replayed with identical inputs and resource inventories, **When** the Resource Allocation Agent processes the handoffs, **Then** the resulting plans produce identical resource assignments and priority rankings when no configuration changes have occurred.
3. **Given** a simulation deployment plan is generated, **When** the plan is reviewed, **Then** it is clearly labelled as a simulation output and carries the simulation tenant identifier in all records.

---

### User Story 8 — Audit Trail of All Allocation Decisions (Priority: P8)

After a prolonged disaster response involving multiple incidents across several states, the post-incident review team requests a complete record of every resource deployment plan produced, every resource assignment made, every priority decision, every cross-incident reallocation, every human override, and every degradation event. The review team retrieves a chronological log with timestamps, input references, confidence levels, prioritisation rationale, and the reasoning behind each allocation decision.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates an append-only audit trail for safety-critical recommendations. Resource deployment directly affects life-safety outcomes, making complete traceability essential for post-incident reviews, coronial inquiries, continuous improvement, and public accountability.

**Independent Test**: Can be fully tested by processing a sequence of handoffs resulting in deployment plans, overrides, and cross-incident reallocations, then querying the audit trail to verify that every processing step has a corresponding record with all required fields.

**Acceptance Scenarios**:

1. **Given** the Resource Allocation Agent processes any incoming handoff, **When** the processing completes, **Then** an audit record is created containing: handoff ID, recommendation ID, assessment ID, plan ID (if produced), decision type, confidence level, and timestamp.
2. **Given** an incident commander overrides a resource assignment, **When** the override is recorded, **Then** an audit record captures the original assignment, the modified assignment, the commander's user ID, role, justification, and the override timestamp.
3. **Given** the Resource Allocation Agent reallocates resources across incidents due to priority differences, **When** the reallocation is recorded, **Then** an audit record documents: the source incident, the destination incident, the resources reallocated, the priority comparison that justified the reallocation, and the resulting gap in the source incident's plan.

---

### Edge Cases

- What happens when a handoff arrives referencing a recommendation ID that does not exist in the data store? The agent logs the error, records a `handoff_rejected` audit entry with the reason, and does not produce a deployment plan.
- What happens when the resource inventory is completely empty (no resources registered)? The agent produces a plan documenting all demands as `unmet`, flags the plan for immediate human attention, and logs the empty inventory condition.
- What happens when all available resources of a required type are already assigned to higher-priority incidents? The agent documents the shortfall, does not downgrade existing assignments, and flags the unmet demand for the incident commander with recommendations for mutual aid or external resource requests.
- What happens when the same handoff ID is received more than once (duplicate delivery)? The agent performs idempotency checking on handoff ID and discards duplicates, logging the discard in the audit trail.
- What happens when a handoff arrives from a simulation tenant? The agent processes the handoff in the simulation context, produces plans isolated from live data, and does not trigger real dispatch actions.
- What happens when a transport dispatch request arrives but the referenced evacuation plan has been superseded? The agent retrieves the latest active evacuation plan version for the incident and processes against the current plan, logging that the original reference was superseded.
- What happens when the Resource Allocation Agent itself becomes unhealthy? The health endpoint reports unhealthy status, the hosting platform detects the failure and restarts the agent, and unprocessed handoffs are re-delivered from the messaging infrastructure.
- What happens when a resource's status update indicates it has been destroyed or is non-operational? The agent transitions the resource to `unavailable` status, removes it from the available pool, flags any active assignments that depended on it, logs the state transition in the audit trail, and triggers re-planning for affected demands.
- What happens when two incidents have identical severity and identical population-at-risk, creating a true tie in priority? The agent allocates proportionally (equal split where possible), documents the tie-breaking rationale, and flags both allocations for incident commander review.

## Requirements *(mandatory)*

### Functional Requirements

#### Handoff Intake and Validation

- **FR-001**: The Resource Allocation Agent MUST consume `AgentHandoffEvent` records where `target_agent=resource_allocation` from the Risk Assessment Agent via the messaging infrastructure. The agent MUST acknowledge receipt of each handoff within 5 seconds of delivery. The agent MUST validate the handoff structure and reject malformed handoffs with an audit record.
- **FR-002**: Upon receiving a valid handoff, the Resource Allocation Agent MUST retrieve the referenced recommendation and hazard assessment from the data store using the IDs provided in the handoff payload (`recommendationId`, `assessmentId`).
- **FR-003**: The Resource Allocation Agent MUST perform idempotency checking on `handoff_id` to avoid processing the same handoff twice within a configurable deduplication window (default: 10 minutes, configurable via environment variable `HANDOFF_DEDUP_WINDOW_MINUTES`). Duplicate handoffs MUST be discarded and the discard recorded in the audit trail.
- **FR-004**: The Resource Allocation Agent MUST validate that the `incident_id` referenced in the handoff exists in the incident store. If the incident does not exist, the handoff MUST be rejected with a `rejected_handoff` audit record.
- **FR-005**: The Resource Allocation Agent MUST consume transport dispatch requests from the Evacuation Agent. Transport requests arrive as `AgentHandoffEvent` records with `source_agent=evacuation`, `target_agent=resource_allocation`, and a payload containing transport requirement records (vehicle type, quantity, pickup location, priority level, and the originating evacuation plan ID).

#### Demand Identification and Prioritisation

- **FR-006**: The Resource Allocation Agent MUST extract resource demands from incoming handoffs by analysing the coordination tasks and recommendation data. Each demand MUST be classified by: resource type, required capability, quantity, location (derived from the hazard assessment's affected area), and urgency (derived from the coordination task priority and hazard severity). The system manages four resource categories, each with capacity, capability, and location attributes: (a) **vehicles** — ambulances, fire trucks, buses, helicopters; (b) **personnel** — paramedics, firefighters, SES volunteers, police; (c) **supplies** — water, food, medical kits, generators, fuel; (d) **facilities** — evacuation centres, hospitals, staging areas. Demands MUST specify the sub-type within the category (e.g., `vehicle:ambulance`, `personnel:paramedic`) to enable precise matching.
- **FR-007**: The Resource Allocation Agent MUST prioritise demands using a three-tier hierarchy aligned with the Constitution's Life Safety First principle: Tier 1 — life safety (evacuation support, medical response, search and rescue); Tier 2 — property protection (structural defence, asset safeguarding); Tier 3 — environmental protection (containment, pollution control). Within each tier, demands MUST be further ordered by coordination task priority (`critical` > `high` > `moderate` > `low`) and then by hazard assessment severity (`critical` > `high` > `moderate` > `low`).
- **FR-008**: Transport dispatch requests from the Evacuation Agent MUST be classified as Tier 1 (life safety) demands and MUST be prioritised using the transport requirement's priority level (`critical` > `immediate` > `high`).
- **FR-009**: The Resource Allocation Agent MUST maintain a consolidated demand queue across all active incidents, ordered by the prioritisation hierarchy. When new demands arrive, they MUST be inserted into the queue at the appropriate position based on their priority, not appended to the end.

#### Resource Inventory and Matching

- **FR-010**: The Resource Allocation Agent MUST maintain awareness of available resources by querying the resource inventory from the data store. Each resource record MUST include: resource ID, resource type (one of: vehicle, personnel, supply, facility), resource sub-type (e.g., ambulance, paramedic, medical kit, staging area), capabilities (list of capability tags — e.g., ambulance: `[medical_transport, patient_stabilization]`; fire truck: `[firefighting, water_pumping, rescue]`), current location (coordinates or locality name), availability status (one of: `available`, `reserved`, `assigned`, `en_route`, `deployed`, `returning`, `unavailable`), assigned incident ID (if any), capacity or quantity (for consumables), and last status update timestamp. The resource availability status MUST follow a formal state machine with these transitions: `available` → `reserved` (held for specific incident) or `assigned` (plan generated) → `en_route` (dispatch confirmed by commander) → `deployed` (arrived on-site) → `returning` → `available`. Resources may transition to `unavailable` (broken, destroyed, or non-operational) from any active state. The `reserved` state holds a resource for a specific incident without an active assignment; it may transition to `assigned` when a plan is generated or back to `available` when released. All state transitions MUST be logged in the audit trail with the previous state, new state, trigger event, and timestamp.
- **FR-011**: The Resource Allocation Agent MUST match demands to available resources using a greedy scoring algorithm. For each eligible resource–demand pair, the agent MUST compute: `score = capability_match × (1/distance) × availability_factor × priority_weight`, where: `capability_match` is binary for MVP — 1.0 if the resource possesses ALL capabilities listed in the demand's `required_capabilities` (0.0 otherwise, which excludes the resource); `distance` is calculated using the **Haversine formula** for straight-line distance (in kilometres) between the resource's current location coordinates and the demand location coordinates (road-distance optimisation deferred to v2); `availability_factor` reflects current status (1.0 for `available`, reduced for `returning` based on estimated return time); and `priority_weight` reflects the demand's priority tier and urgency. The agent MUST assign the highest-scoring resource to the highest-priority demand first (greedy assignment), then proceed to the next demand. Eligibility prerequisites remain: (1) type compatibility — the resource type and sub-type MUST match the demand; (2) capability match — the resource MUST possess all required capabilities; (3) availability — only resources with status `available` or `returning` (estimated return within the demand's time window) are eligible. The agent MUST NOT assign a resource that does not meet type and capability requirements. Linear programming global optimisation is deferred to v2.
- **FR-012**: When a demand cannot be fully met from available resources, the Resource Allocation Agent MUST generate a partial allocation plan: (a) assign whatever partial resources are available that meet type and capability requirements, (b) clearly mark each unfulfilled demand with the shortfall (unmet quantity and type) and reasoning for why it could not be met, (c) flag the shortfall in the deployment plan summary for incident commander attention, and (d) recommend the shortfall for commander action (e.g., request mutual aid, activate reserve resources). The agent MUST never silently drop demands — every demand in the input MUST appear in the output plan as either `fully_met`, `partially_met`, or `unmet` with explicit reasoning.
- **FR-013**: The Resource Allocation Agent MUST NOT reassign a resource currently assigned to an active, approved deployment plan for a higher-priority demand without explicit incident commander approval, except in the following case: when a `critical`-priority life-safety demand cannot be met from unassigned resources and a resource is assigned to a Tier 2 or Tier 3 demand, the agent MUST recommend the reallocation but flag it for mandatory commander approval before execution.

#### Deployment Plan Generation

- **FR-014**: The Resource Allocation Agent MUST generate a `ResourceDeploymentPlan` for each valid handoff or set of related demands. The plan MUST include: plan ID (format: `rdp-{incident_id}-v{N}` where N is the version number), incident ID, version number (monotonically increasing per incident), identified demands (with priorities), resource assignments (with selection rationale), unmet demands (with shortfall details), estimated deployment timelines, overall confidence level, generation method, traceability references (handoff ID, recommendation ID, assessment ID), and a human-readable summary.
- **FR-015**: The deployment plan version number MUST increase monotonically per incident. Version assignment MUST use optimistic concurrency control to prevent conflicts during concurrent planning. Previous plan versions MUST be marked as `superseded` when a new version is created and MUST remain immutable and queryable for audit purposes. Status-only transitions (`proposed` → `approved`/`rejected`/`superseded`/`cancelled`) are the sole permitted mutation on existing records.
- **FR-016**: The deployment plan summary MUST be generated using an LLM when available, with a template-based fallback when the LLM is unavailable. The LLM is used ONLY for generating human-readable allocation rationale text; all resource matching, scoring, and assignment logic is purely algorithmic and does not depend on the LLM. The summary MUST be written in plain language suitable for incident commanders, consistent with AIIMS terminology, and MUST include: what resources are being deployed, where, why (linked to the triggering hazard assessment), and what gaps remain. All LLM outputs MUST pass through content safety validation before inclusion.
- **FR-017**: Each deployment plan MUST include an estimated deployment timeline for each assignment, calculated as the estimated travel time from the resource's current location to the demand location. The timeline MUST account for mobilisation overhead (configurable default: 15 minutes for personnel, 10 minutes for vehicles, 5 minutes for helicopters) plus travel time.

#### Resource Status Tracking

- **FR-018**: The Resource Allocation Agent MUST process `resource_status` category signals to update the status of tracked resources. Status updates MUST include: resource ID, new status (must be a valid state per the resource state machine defined in FR-010), location (if changed), remaining capacity (for consumables), and timestamp. The agent MUST validate that the requested state transition is permitted by the state machine before applying it, and MUST log every transition in the audit trail with previous state, new state, and trigger event.
- **FR-019**: The Resource Allocation Agent MUST flag resources approaching operational limits: (a) personnel teams deployed continuously for more than 12 hours MUST be flagged for rotation; (b) consumable supplies below 20% of initial stock MUST be flagged for replenishment; (c) vehicles that have reported mechanical issues MUST be flagged as degraded. Flagged resources MUST be highlighted in the next deployment plan and in resource utilisation queries.
- **FR-020**: The Resource Allocation Agent MUST compute and expose resource utilisation metrics on demand: total resources by type, assigned vs. available counts, utilisation percentage per resource type, resources flagged for rotation or replenishment, and resources by incident.

#### Cross-Incident Allocation

- **FR-021**: When resource demands from multiple active incidents compete for the same resource pool, the Resource Allocation Agent MUST allocate resources using the following four-level tiebreaking hierarchy, evaluated in order: (1) **life safety priority** — Tier 1 (life safety) demands before Tier 2 (property) before Tier 3 (environment); (2) **severity assessment** — higher severity incidents first (`critical` > `high` > `moderate` > `low`); (3) **proximity** — closer resources to demand location preferred; (4) **request timestamp** — earlier request receives priority when all other factors are equal. Cross-incident allocation recommendations MUST include a trade-off analysis showing what each affected incident loses if the reallocation proceeds. Resources MUST NOT be silently taken from one incident to serve another — all cross-incident reallocations MUST be explicitly documented in the deployment plan and flagged for commander approval.
- **FR-022**: When two incidents have identical priority tier, identical severity, and identical population-at-risk estimates, the Resource Allocation Agent MUST distribute contested resources proportionally based on the ratio of unmet demands and document the tie-breaking rationale.
- **FR-023**: The Resource Allocation Agent MUST support cross-incident resource reallocation recommendations: when a higher-priority incident's life-safety demands cannot be met from unassigned resources, the agent MUST identify resources assigned to lower-priority demands in other incidents and recommend reallocation with a documented trade-off analysis. The recommendation MUST require incident commander approval before execution.

#### Human Override

- **FR-024**: Incident commanders MUST be able to perform the following override actions on any resource deployment plan: (a) **reassign resources** — redirect a specific resource from one demand to another, (b) **add resources** — manually assign resources not selected by the agent, (c) **remove resources** — remove a resource assignment from the plan, (d) **change priority** — adjust the priority of a specific demand, (e) **approve, reject, or cancel** the plan. Each override action MUST update the plan and record the `override_by_user_id`, `override_by_role`, `override_justification`, override action type, and `override_timestamp` in both the plan record and the audit trail. All overrides MUST be logged with mandatory justification text.
- **FR-025**: When an incident commander modifies a deployment plan, the modified plan MUST be stored as a new version linked to the original, preserving the original plan intact. The override audit record MUST be append-only and immutable.
- **FR-026**: The Resource Allocation Agent MUST NOT autonomously dispatch resources. All deployment plans MUST remain in `proposed` status until explicitly approved by an incident commander. The system supports but does not replace human authority over resource deployment decisions.

#### Simulation and Reproducibility

- **FR-027**: The Resource Allocation Agent MUST support processing handoffs in simulation tenant contexts per spec 007. Plans produced in simulation MUST be isolated from live data and MUST NOT appear in live incident queries or affect live resource inventories.
- **FR-028**: Given identical input data (same demands, same resource inventory, same configuration version), the Resource Allocation Agent MUST produce identical resource assignments and priority rankings, enabling reproducibility verification for scenario-based testing.
- **FR-029**: Each deployment plan MUST record the configuration version and input data snapshot used at generation time, enabling post-incident auditing and reproducibility verification.

#### Audit Trail

- **FR-030**: The Resource Allocation Agent MUST produce an audit record for every processing step, including: handoff receipt, handoff rejection, duplicate discard, demand identification, resource matching, plan generation, plan versioning, transport dispatch processing, cross-incident reallocation, human overrides, resource status updates, degradation events, and health status changes.
- **FR-031**: Each audit record MUST be append-only (no updates or deletes) and MUST include: record ID, handoff ID, plan ID (when applicable), plan_version, decision type, confidence level, demands, assignments, scoring_rationale, resources_considered, resources_excluded_reason, processing_duration, decision rationale (including prioritisation logic applied), agent version, configuration version, and timestamp.
- **FR-031a**: The audit trail MUST use a three-tier storage degradation pattern consistent with other agents: (1) **primary** — Cosmos DB for durable, queryable storage; (2) **secondary** — in-memory buffer when Cosmos DB is unavailable, flushed to primary upon recovery; (3) **tertiary** — local file fallback when both Cosmos DB and memory buffer are exhausted. The current audit write tier MUST be reported via the `/health` endpoint's `audit_store` field. Degradation transitions MUST be logged as audit events themselves.
- **FR-032**: Audit records MUST be queryable by incident ID, plan ID, decision type, resource ID, and time range to support post-incident reviews and cross-incident analysis.

#### Graceful Degradation

- **FR-033**: When the AI service used for plan summary generation is unavailable, the Resource Allocation Agent MUST fall back to template-based plan summaries using structured assignment and priority data without AI enrichment. Confidence MUST be reduced by a multiplicative factor of 0.8. All fallback outputs MUST carry `generation_method=template_fallback`.
- **FR-034**: When the resource inventory data store is partially unavailable, the Resource Allocation Agent MUST produce plans using the last-known-good inventory snapshot (if available within a configurable staleness window, default: 30 minutes). The plan MUST flag that inventory data may be stale and reduce confidence accordingly.
- **FR-035**: The Resource Allocation Agent MUST expose a `/health` endpoint that reports agent readiness. The health response MUST include: `inventory_loaded` (whether resource inventory data is accessible), `llm_connectivity` (AI service reachability), `cosmos_connectivity` (data store reachability), `active_plan_count` (number of currently active deployment plans), `pending_demands` (number of unprocessed demands awaiting allocation), `processing_queue_depth` (number of pending handoffs awaiting processing), and `audit_store` (current audit write tier). The endpoint MUST respond within 1 second under normal operation.
- **FR-036**: The Resource Allocation Agent MUST NOT halt entirely when any single dependency is unavailable. It MUST continue processing with degraded capabilities and log all degradation events.

#### Content Safety

- **FR-037**: All AI-generated outputs (plan summaries, allocation rationale text) MUST pass through content safety validation before inclusion in any persisted record. If validation fails, the output MUST be replaced with a structured template fallback, the plan MUST carry `generation_method=safety_fallback`, and the failure recorded in the audit trail. Template-based fallback text is pre-approved and does not require runtime content safety checks.

### Non-Functional Requirements

#### Scalability

- **NFR-001**: The Resource Allocation Agent MUST handle at minimum 30 concurrent deployment plans (across different incidents) during peak disaster events. This is lower than the Evacuation Agent's 50 concurrent plans because not all evacuations generate resource allocation demands, and resource matching is computationally simpler than route computation. Horizontal scaling via auto-scaling MUST be used to scale processing capacity based on message queue depth.

#### Observability

- **NFR-002**: The Resource Allocation Agent MUST emit telemetry for operational monitoring. The following core metrics MUST be tracked: `allocation_latency` (time from handoff receipt to plan persisted, reported as p50, p95, p99), `resource_utilization_rate` (percentage of each resource type currently assigned), `unmet_demand_count` (number of demands not fully met per time window), `cross_incident_conflicts` (count of cross-incident resource contention events per time window), `override_count` (number of commander overrides per time window), `plan_versions_per_incident` (average and max plan versions generated per incident), `status_update_latency` (time from resource status signal receipt to inventory update). Additional detailed metrics: `resource_matching_time` (duration of demand-to-resource matching per plan), `demand_fulfilment_rate` (percentage of demands fully met per plan), `shortfall_count` (number of unmet demands per time window), `cross_incident_reallocation_count` (reallocations recommended per time window), `override_rate` (percentage of plans modified by commanders), `transport_dispatch_latency` (time from evacuation transport request to dispatch plan produced), `active_plans_gauge` (current number of active non-superseded plans), `degradation_events` (count per time window), and `handoff_success_rate`. All metrics MUST support alerting thresholds.

### Key Entities

- **ResourceDeploymentPlan**: A versioned, human-reviewable plan for deploying resources to meet identified demands during a disaster incident. Key attributes: plan ID (format: `rdp-{incident_id}-v{N}` where N is the version number), incident ID, version number (monotonically increasing per incident, managed via optimistic concurrency control), identified demands (list of `ResourceDemand` records), resource assignments (list of `ResourceAssignment` records), unmet demands (list of demands that could not be fulfilled with shortfall details), estimated deployment timeline per assignment, overall confidence level (0.0–1.0 numeric and categorical low/medium/high), status (`proposed`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`), generation method (`ai_assisted`, `template_fallback`, `safety_fallback`, `commander_override`), configuration version, input data snapshot references, traceability references (handoff ID, recommendation ID, assessment ID, evacuation plan ID if transport-related), human-readable summary, override metadata (user ID, role, justification, action type, timestamp — when applicable), and timestamps (created, updated). Plans are immutable once persisted; new plans create new versions. Status transitions are the only permitted mutation on existing records.

- **ResourceDemand**: A specific resource need identified from a coordination task, recommendation, or transport dispatch request. Key attributes: demand ID, incident ID, source (coordination task ID or transport requirement ID), resource type (personnel, vehicle, supply, facility), required capabilities (list of capability tags), quantity, location (coordinates or locality name), priority tier (Tier 1/2/3), urgency (critical/high/moderate/low), fulfilment status (`pending`, `partially_met`, `fully_met`, `unmet`, `closed`), and originating handoff ID.

- **ResourceAssignment**: A match between a specific resource and a specific demand within a deployment plan. Key attributes: assignment ID, demand ID, resource ID, assignment status (`proposed`, `approved`, `dispatched`, `en_route`, `deployed`, `completed`, `cancelled`), estimated travel time, estimated arrival time, selection rationale (why this resource was chosen), and timestamps.

- **ResourceInventoryItem**: An available resource tracked by the agent for allocation purposes. Key attributes: resource ID, resource type (one of four categories: vehicle, personnel, supply, facility), resource sub-type (vehicles: ambulance, fire truck, bus, helicopter; personnel: paramedic, firefighter, SES volunteer, police; supplies: water, food, medical kit, generator, fuel; facilities: evacuation centre, hospital, staging area), capabilities (list of capability tags — e.g., ambulance: `[medical_transport, patient_stabilization]`; fire truck: `[firefighting, water_pumping, rescue]`), current location, availability status (formal state machine: `available` → `reserved` or `assigned` → `en_route` → `deployed` → `returning` → `available`; also `unavailable` for broken/destroyed/non-operational), assigned incident ID (if any), capacity or quantity (for consumables), last status update timestamp, operational flags (rotation needed, replenishment needed, degraded condition), and managing organisation ID.

- **AllocationDecisionRecord**: An audit trail entry capturing a single processing step or decision made by the Resource Allocation Agent. Key attributes: record ID, handoff ID, plan ID (when applicable), demand ID (when applicable), resource ID (when applicable), decision type (handoff_received, handoff_rejected, duplicate_discarded, demand_identified, resource_matched, resource_excluded, partial_allocation, plan_generated, plan_superseded, plan_expired, override_applied, reallocation_recommended, transport_dispatched, resource_status_updated, degradation_detected, content_safety_failure), confidence level, prioritisation rationale, processing duration, agent version, configuration version, and timestamp. Append-only; no updates or deletes permitted.

- **AgentHandoffEvent**: An explicit handoff record consumed by the Resource Allocation Agent from upstream agents (Risk Assessment, Evacuation). Key attributes: handoff ID, incident ID, source agent (`risk_assessment` or `evacuation`), target agent (`resource_allocation`), scope key, confidence, payload (containing recommendation ID, summary, assessment ID, or transport requirement data), tenant ID, status, retry count, and timestamps.

### Assumptions

- The Risk Assessment Agent (spec 012) delivers handoffs in the `AgentHandoffEvent` format with payload containing `recommendationId`, `summary`, `explanation`, and `assessmentId`. The Resource Allocation Agent does not re-assess hazard severity — it consumes the assessment and recommendation as provided.
- The Evacuation Agent (spec 009) delivers transport dispatch requests as `AgentHandoffEvent` records with payload containing transport requirement records (vehicle type, quantity, pickup location, priority level, evacuation plan ID). The format aligns with the `TransportRequirement` entity defined in spec 009.
- Resource inventory data (resource types, capabilities, locations, availability) is available from the data store (spec 006). For MVP, resource inventory is pre-loaded from a static configuration file with support for dynamic updates via `resource_status` signals. Future versions may integrate with live asset management systems.
- The resource matching algorithm uses a greedy scoring function (`score = capability_match × (1/distance) × availability_factor × priority_weight`) to rank and assign resources to demands in priority order. Advanced optimisation (e.g., linear programming for global optimum) is deferred to v2.
- Handoff delivery uses the same messaging infrastructure as other agent-to-agent communication, with at-least-once delivery semantics. The Resource Allocation Agent handles duplicate delivery via idempotency checking.
- The agent does not directly interface with physical dispatch systems (radio, vehicle tracking, logistics platforms). It produces deployment plans and dispatch recommendations for human commanders to execute through their operational channels.
- Tenant isolation (simulation vs. live) is enforced at the data layer per spec 007. The Resource Allocation Agent respects tenant boundaries for all plans, audit records, and resource queries.
- The AI service used for plan summary generation follows the same `_generate_with_fallback` pattern as other agents, with automatic template fallback when unavailable.
- The `required_approval_level` for all deployment plans defaults to `incident_commander`. The system supports but does not replace human authority over resource deployment decisions.
- Each deployment plan is scoped to a single incident for v1. Cross-incident allocation is supported through recommendations and documented trade-offs, but a single plan does not span multiple incidents. The data model supports optional `related_incident_ids` for future cross-incident planning capabilities.
- Mobilisation time defaults (15 minutes for personnel, 10 minutes for vehicles) are based on Australian emergency management best practices and are configurable per resource type.

### Out of Scope

- Replacement of incident commander authority over resource deployment. The Resource Allocation Agent proposes plans; human commanders approve and execute them.
- Physical dispatch of resources — the agent produces deployment plans but does not interface with radio dispatch, vehicle tracking, or logistics platforms.
- Resource procurement or purchasing — the agent allocates from available inventory but does not order or procure new resources.
- Management of resource inventory data sources — the agent consumes resource data but does not manage the data source registration (that is spec 005's responsibility).
- Cross-incident deployment plans spanning multiple incidents in a single plan — deferred to v2. Cross-incident allocation is supported through recommendations and trade-off documentation but each plan is scoped to one incident.
- Real-time GPS tracking of deployed resources — the agent processes status update signals but does not provide real-time tracking visualisation.
- Financial cost optimisation of resource deployment — the agent optimises for life-safety outcomes, not cost.
- Volunteer management or credentialing — the agent allocates pre-registered resources but does not manage volunteer registration or capability verification.

### Dependencies

- **spec 001 (Disaster Response Hub)**: Defines the CoordinationTask, Recommendation, AgentHandoffEvent, and Signal data models that the Resource Allocation Agent operates on.
- **spec 005 (Data Source Governance)**: Defines the data source registry and trust tiers that inform resource inventory data reliability.
- **spec 006 (Data Ingestion & Storage)**: Defines the data store from which the Resource Allocation Agent retrieves resource inventory, recommendation, and assessment data.
- **spec 007 (Simulation & Tenant Isolation)**: Defines the tenant isolation model that the Resource Allocation Agent must respect for simulation vs. live processing.
- **spec 009 (Evacuation Agent)**: Defines the upstream agent that produces transport dispatch requests consumed by the Resource Allocation Agent. The transport requirement format (vehicle type, quantity, pickup location, priority level, evacuation plan ID) is defined in spec 009.
- **spec 012 (Risk Assessment Agent)**: Defines the upstream agent that produces handoffs consumed by the Resource Allocation Agent. The handoff payload format (`recommendationId`, `summary`, `explanation`, `assessmentId`) and escalation criteria (coordination tasks present) are defined in spec 012.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Resource deployment plans (allocation plans) MUST be generated within **15 seconds** of receiving a valid handoff. Resource status updates MUST be processed within **5 seconds** of signal receipt. Cross-incident analysis (multi-incident allocation recommendations with trade-off analysis) MUST complete within **30 seconds**. If processing exceeds the applicable threshold, the plan MUST still complete but MUST log a processing delay event with the actual duration.
- **SC-002**: 100% of deployment plans include traceable references — every plan links back to the handoff, recommendation, and assessment that triggered it, verifiable through the audit trail.
- **SC-003**: Resource assignments correctly match demand type and capability requirements in 100% of cases — no assignment pairs an incompatible resource with a demand.
- **SC-004**: When competing demands exist across multiple incidents, the higher-severity life-safety incident receives preferential resource allocation in 100% of test cases, consistent with the Tier 1 > Tier 2 > Tier 3 prioritisation hierarchy.
- **SC-005**: Transport dispatch requests from the Evacuation Agent are processed and matched to available transport resources with critical-priority requests dispatched first, achieving 100% priority-ordering compliance in test scenarios.
- **SC-006**: Resource deployment plans achieve a 30% improvement in resource deployment efficiency compared to manual allocation baselines, measured as: reduced average time from demand identification to resource arrival on-site, and improved demand fulfilment rate (percentage of demands fully met from available resources).
- **SC-007**: Given identical inputs and configuration, the Resource Allocation Agent produces identical resource assignments and priority rankings in 100% of reproducibility test runs.
- **SC-008**: Every processing step has a corresponding audit record — audit completeness is 100% verifiable via reconciliation of handoff IDs processed vs. audit records created.
- **SC-009**: When the AI service or resource inventory is unavailable, the agent continues producing degraded plans with no processing interruption — measured as 0% handoff drop rate during dependency outage periods.
- **SC-010**: At least 90% of incident commanders in scenario-based exercises rate the deployment plans as clear, actionable, and appropriately prioritised, using a structured post-exercise survey with a 5-point rubric across clarity, priority justification, and decision confidence.

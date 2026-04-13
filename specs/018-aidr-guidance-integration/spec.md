# Feature Specification: AIDR Guidance Integration

**Feature Branch**: `018-aidr-guidance-integration`  
**Created**: 2025-07-17  
**Status**: Draft  
**Input**: User description: "Incorporate AIDR (Australian Institute for Disaster Resilience) guidance and knowledge into the Autonomous Disaster Response Agent Coordination Hub — covering Australian Warning System three-tier alerts, AIIMS-aligned incident management, five-stage evacuation, community recovery, PPRR lifecycle, Total Warning System, and lessons management."

## Clarifications

### Session 2026-04-13

- Q: What non-functional requirements (latency, concurrency, observability) apply to new AIDR capabilities? → A: Align with existing spec baselines. Warning compliance validation ≤5s. AIIMS role assignment ≤5s. PPRR phase transition ≤5s. Recovery dashboard load ≤10s. Lessons capture ≤5s, trend analysis ≤30s. Concurrency: ≥10 concurrent recovery operations, ≥50 concurrent lessons. Health endpoints ≤1s (consistent with all agents). Observability metrics: warning_compliance_rate, tier_transition_latency, evacuation_stage_duration, recovery_indicator_update_frequency, lesson_resolution_time, pprr_phase_transition_count, aiims_role_coverage_ratio.
- Q: Can warning tiers be skipped for sudden-onset events (e.g., straight to Emergency Warning for earthquakes)? → A: Yes. Tiers may be skipped for sudden-onset hazards (earthquake, tsunami, structural collapse). Life safety (Constitution Principle I) demands immediate issuance of the appropriate tier. The warning MUST log the tier-skip justification and hazard type. The AWS three tiers represent severity levels, not mandatory sequential steps.
- Q: What specific measurable indicators should be tracked for each recovery environment? → A: Per AIDR Community Recovery Handbook — Social: wealth, employment, amenity, health, social issues, social belonging, recreation/leisure (7). Built: essential services, community infrastructure, transport networks, property/housing, planning/building compliance (5). Economic: personal income, business premises, tourism, workforce availability, productive land (5). Natural: air quality, water quality, land/soil health, biodiversity (4). Total 21 indicators, satisfying SC-005's ≥3 per environment.
- Q: What happens when the Incident Controller is unavailable to approve a warning escalation? → A: AIIMS delegation chain applies. Authority passes to deputy IC, then next-in-command within Control function. Configurable timeout triggers auto-escalation to next authority (default 5 min for Emergency Warning, 15 min for lower tiers — matching spec 008 pattern). No warning is auto-approved without human authorisation (Constitution §1). All delegation events fully audited.
- Q: What defines a "significant incident" that triggers the mandatory lessons-capture process (FR-038)? → A: Any AIIMS Level 2 or Level 3 incident, any formally declared exercise, or any incident where the IC explicitly triggers lessons capture. Level 1 incidents may optionally trigger lessons capture at IC discretion. Aligned with AIDR Incident Management Handbook after-action review guidance.

### Session 2026-04-13 (Pass 2 — Cross-Spec Consistency)

- Q: How do the six Key Entities map to existing domain models in `packages/domain/`? → A: Warning extends `PublicAlert` with new AWS-tier fields (`warning_tier`, `colour_code`, `hazard_icon`, `action_statement`, `superseded_warning_id`). AIIMS Role Assignment is a new model linking an agent to an AIIMS function for a specific incident, complementing the existing `OperatingFramework` (which defines AIIMS as a `framework_type`) and `FrameworkAssignment` (which maps frameworks to jurisdictions/orgs). Evacuation Stage, PPRR Phase, Recovery Environment Tracker, and Lesson are new domain models with no existing equivalents. No existing models are replaced or removed.
- Q: How do the three distinct severity scales in the domain relate to each other? → A: `Incident.severity` (`advisory|watch|warning|emergency`) represents overall incident urgency for triage. `HazardAssessment.severity_level` (`low|moderate|high|critical`) represents assessed hazard risk. AWS warning tiers (`Advice|Watch and Act|Emergency Warning`) represent public-facing alert levels. These are independent scales serving different purposes — incident triage, risk assessment, and public communication respectively. No automatic mapping exists between them; the Communication Agent applies editorial judgment (with IC approval) when selecting the AWS tier, informed by the hazard assessment severity.
- Q: How do PPRR phases map to the existing `Incident.status` enum (`monitoring|active|stabilising|recovery|closed|rehearsal`)? → A: PPRR phase is an orthogonal attribute, not a replacement for `Incident.status`. An incident in `active` status may be in Response phase; one in `recovery` status aligns with Recovery phase. Prevention and Preparedness phases apply to regions/scenarios and do not require an active incident. The PPRR phase designation is stored as a separate field, not overloaded onto the existing status enum.
- Q: How does the tiered escalation timeout (5 min Emergency Warning, 15 min lower tiers) reconcile with spec 008's flat 15-min timeout? → A: This spec's tiered timeout supersedes spec 008's flat 15-minute escalation timeout for warning-related approvals. Spec 008 will be amended to reference this spec's tiered timeout. The 5-minute timeout for Emergency Warnings is life-safety-driven (Constitution Principle I). Non-warning approvals in spec 008 retain their existing 15-minute default.
- Q: Does the vulnerable populations list in FR-007 and FR-021 cover all groups from the AIDR Evacuation Planning Handbook? → A: Extended. In addition to Constitution §VI-C groups (Aboriginal/TSI, CALD, disability, children, older persons, homelessness, tourists/transient, institutional care), the AIDR Evacuation Planning Handbook (2023) identifies: pregnant and breastfeeding women, people with ongoing health needs, and people with pets or assistance animals. FR-007 and FR-021 updated to reference both sources.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Three-Tier Australian Warning System Alerts (Priority: P1)

An Incident Controller needs the Communication Agent to issue public warnings that conform to the Australian Warning System (AWS). When a bushfire threat escalates, the agent drafts an **Advice** alert, then upgrades to **Watch and Act**, and finally to **Emergency Warning** as severity increases. Each warning includes the correct tier colour, hazard icon, location, and a clear call-to-action. When the threat reduces, the agent issues a de-escalation notice and eventually an all-clear notification.

**Why this priority**: Public warnings are life-safety critical. Non-compliant warnings risk confusion, undermine public trust, and may conflict with official agency messaging. The Constitution (§V-A) makes AWS compliance non-negotiable.

**Independent Test**: Can be fully tested by simulating a hazard escalation sequence and verifying each generated warning contains the correct tier label, colour code, hazard icon, action statement, and nested-model structure defined by the AWS Companion (2022).

**Acceptance Scenarios**:

1. **Given** a new bushfire incident at Level 1, **When** the Communication Agent generates the first public alert, **Then** it MUST be formatted as an "Advice" (yellow) tier warning with the fire hazard icon, incident location, and an informational action statement.
2. **Given** an existing Advice-level warning and an escalation trigger from the Risk Assessment Agent, **When** the Communication Agent upgrades the alert, **Then** it MUST issue a "Watch and Act" (orange) warning that supersedes the prior Advice and includes a protective-action statement.
3. **Given** an Emergency Warning (red) is active and the hazard de-escalates, **When** the Incident Controller approves the downgrade, **Then** the Communication Agent MUST issue a de-escalation notice clearly stating the reduced threat level and updated action guidance.
4. **Given** an incident is resolved, **When** the Incident Controller triggers stand-down, **Then** the Communication Agent MUST issue an all-clear notification referencing the original warning chain.

---

### User Story 2 — AIIMS-Aligned Incident Management Structure (Priority: P1)

A platform administrator configures the coordination hub so that every active incident assigns agents to the six AIIMS functional roles: Control, Intelligence, Planning, Operations, Logistics, and Public Information. Each agent understands its functional role, communicates within role boundaries, and supports incident-level escalation (Level 1 → 2 → 3) with proportional expansion of coordination effort.

**Why this priority**: AIIMS alignment is the structural backbone of Australian emergency management. Without it, the platform cannot credibly participate in multi-agency coordination. The Constitution (§II-A) mandates this alignment.

**Independent Test**: Can be fully tested by creating a simulated incident and verifying that each agent is mapped to its AIIMS function, that role boundaries are respected in agent-to-agent communication, and that escalating the incident level activates the correct coordination behaviours.

**Acceptance Scenarios**:

1. **Given** a new incident is created, **When** agents are assigned, **Then** each agent MUST be mapped to exactly one AIIMS functional role, and the mapping MUST be visible in the Common Operating Picture.
2. **Given** a Level 1 incident, **When** the situation escalates beyond single-agency capacity, **Then** the platform MUST support promotion to Level 2 with cross-agency coordination activated and a shared COP established.
3. **Given** a Level 3 incident, **When** the platform is operating at full multi-tier coordination, **Then** all six AIIMS functions MUST have active agents with clearly delineated responsibilities, and the platform MUST support integration with the National Coordination Mechanism.
4. **Given** an active incident with AIIMS roles assigned, **When** a user queries the Common Operating Picture, **Then** the COP MUST display the current AIIMS functional structure, the incident level, and the status of each function.

---

### User Story 3 — Five-Stage Evacuation Process (Priority: P1)

An Evacuation Agent operates through the five mandatory stages — Decision, Warning, Withdrawal, Shelter, and Return — for a cyclone evacuation. The agent supports pre-warned and immediate evacuation types, directed/recommended/self-initiated approaches, and total/partial/phased scoping. Vulnerable populations receive prioritised attention at every stage.

**Why this priority**: Evacuation is a life-safety operation where incomplete or disordered processes directly endanger lives. The Constitution (§VI) mandates the five-stage model. The existing evacuation spec (009) partially covers these stages but does not use AIDR terminology or enforce the full framework.

**Independent Test**: Can be fully tested by simulating a cyclone scenario and stepping the Evacuation Agent through all five stages, verifying that each stage produces the required outputs, decision records, and vulnerable-population considerations.

**Acceptance Scenarios**:

1. **Given** a cyclone threat is assessed as requiring evacuation, **When** the Decision stage begins, **Then** the system MUST record the decision authority, decision rationale, evacuation type (pre-warned), approach (directed/recommended), and scope (total/partial/phased).
2. **Given** a Decision to evacuate has been made, **When** the Warning stage activates, **Then** the Evacuation Agent MUST coordinate with the Communication Agent to issue evacuation warnings that include timeframes, routes, and shelter destinations.
3. **Given** the Withdrawal stage is active, **When** the agent manages population movement, **Then** vulnerable populations (as defined in Constitution §VI-C) MUST receive priority transport allocation and progress tracking.
4. **Given** evacuees have arrived at shelters, **When** the Shelter stage is active, **Then** the system MUST track shelter capacity, welfare needs, and vulnerable-population status across all active shelter locations.
5. **Given** the hazard has passed and conditions are safe, **When** the Return stage begins, **Then** the system MUST manage phased re-entry, validate safety conditions, and track return completion rates.
6. **Given** evacuation is assessed as more dangerous than sheltering, **When** the Decision stage evaluates options, **Then** the system MUST support a shelter-in-place decision with rationale capture and ongoing monitoring.

---

### User Story 4 — PPRR Lifecycle Integration (Priority: P2)

An emergency manager uses the platform across all four PPRR phases — Prevention, Preparedness, Response, and Recovery — for a flood-prone region. During Prevention, the platform supports hazard mitigation planning. During Preparedness, it enables scenario rehearsal and resource pre-positioning. During Response, it coordinates real-time multi-agent operations. During Recovery, it tracks community restoration across all four recovery environments.

**Why this priority**: PPRR is the foundational lifecycle for Australian emergency management. The platform currently focuses heavily on the Response phase. Extending to all four phases aligns the platform with AEMA (2023) and enables end-to-end emergency management support.

**Independent Test**: Can be fully tested by configuring a flood scenario and verifying that the platform provides distinct capabilities and agent behaviours appropriate to each of the four PPRR phases, and that transitions between phases are managed rather than abrupt.

**Acceptance Scenarios**:

1. **Given** a flood-prone region is identified, **When** the platform is in Prevention phase, **Then** it MUST support hazard risk assessments, mitigation option analysis, and risk-reduction tracking.
2. **Given** flood season is approaching, **When** the platform transitions to Preparedness, **Then** it MUST support scenario rehearsal (simulation), community readiness assessment, resource pre-positioning plans, and warning system testing.
3. **Given** a flood event is occurring, **When** the platform is in Response phase, **Then** all agents MUST operate with their established real-time coordination capabilities, and the platform MUST already be planning for Recovery.
4. **Given** the flood event has peaked and is receding, **When** the platform transitions to Recovery, **Then** the transition MUST be managed (not abrupt) and Recovery agents MUST activate in parallel with ongoing Response operations.

---

### User Story 5 — Community Recovery Support (Priority: P2)

A Recovery Coordinator uses the platform to manage the post-disaster recovery process for a flood-affected community. The platform tracks progress across all four recovery environments (Social, Built, Economic, Natural), applies the six National Recovery Principles, and supports community-led recovery approaches with long-term tracking.

**Why this priority**: Recovery is a distinct, long-term phase that is currently absent from the platform's agent capabilities. The Constitution (§VII) mandates recovery support as a core function, and the Community Recovery Handbook (2018) provides the authoritative framework.

**Independent Test**: Can be fully tested by simulating a post-flood recovery scenario and verifying that the platform tracks recovery indicators across all four environments, enforces community-led approaches, and supports recovery coordination activities.

**Acceptance Scenarios**:

1. **Given** a disaster event transitions to recovery, **When** a Recovery Coordinator accesses the platform, **Then** the system MUST present a recovery dashboard covering all four environments: Social, Built, Economic, and Natural.
2. **Given** recovery is underway, **When** the system generates recovery plans and recommendations, **Then** each recommendation MUST align with at least one of the six National Recovery Principles and MUST reference which principle(s) apply.
3. **Given** a community-led recovery process, **When** the platform facilitates recovery activities, **Then** it MUST provide mechanisms for community input, local needs prioritisation, and recovery progress that is visible to the affected community.
4. **Given** recovery operations span months, **When** the platform tracks recovery progress, **Then** it MUST support longitudinal tracking with measurable indicators for each of the four recovery environments.

---

### User Story 6 — Total Warning System Implementation (Priority: P2)

A warning officer uses the platform to manage the full lifecycle of a warning — from situational awareness through monitoring, message construction, interpretation support, multi-channel communication, to community response enablement — for a severe storm event.

**Why this priority**: Warnings are not isolated messages; the AIDR Public Information and Warnings Handbook (2021) establishes that effective warnings require all six elements of the Total Warning System working together. The Constitution (§V-C) mandates this holistic approach.

**Independent Test**: Can be fully tested by tracing a single warning lifecycle through all six elements and verifying that each element produces outputs that feed into the next.

**Acceptance Scenarios**:

1. **Given** environmental monitoring detects a developing severe storm, **When** the Monitoring Agent analyses the situation, **Then** it MUST produce a situational awareness summary that feeds into monitoring and prediction outputs.
2. **Given** a monitoring and prediction output indicates a credible threat, **When** the Communication Agent constructs a warning, **Then** the message MUST follow the ten warning principles (Constitution §V-B) and include an impact statement and call-to-action.
3. **Given** a warning has been constructed, **When** the system prepares it for dissemination, **Then** it MUST include interpretation aids (plain language, translations for CALD communities, accessibility formats) and deliver via all appropriate channels.
4. **Given** a warning has been issued, **When** the platform monitors community response, **Then** it MUST capture response indicators (e.g., evacuation compliance rates, shelter arrivals) to close the Total Warning System feedback loop.

---

### User Story 7 — Lessons Management Framework (Priority: P3)

After a significant incident or simulation exercise, a quality assurance officer uses the platform to capture lessons identified, analyse patterns across multiple events, and track whether lessons have been integrated into updated procedures, agent configurations, or training materials.

**Why this priority**: Continual improvement is one of the eleven National EM Principles (Constitution §II, Principle 11). Without structured lessons management, the platform cannot demonstrate compliance with AIDR continuous-improvement expectations. This also supports Quality Gates (Constitution §Quality Gates).

**Independent Test**: Can be fully tested by completing a simulation exercise and using the lessons management features to capture, categorise, assign, and track lessons through to resolution.

**Acceptance Scenarios**:

1. **Given** a significant incident or exercise has concluded, **When** a user initiates a lessons-capture process, **Then** the system MUST provide a structured template for recording observations, categorised by AIIMS function, PPRR phase, and severity.
2. **Given** lessons have been captured from multiple events, **When** a user analyses the lessons register, **Then** the system MUST surface recurring themes, unresolved items, and trend indicators.
3. **Given** a lesson has been identified and assigned for action, **When** the responsible party updates agent procedures or configurations, **Then** the system MUST track the lesson through to closure and link the resolution back to the originating event.
4. **Given** a Pull Request is submitted that addresses a lessons-identified action item, **When** the PR undergoes review, **Then** the quality gate MUST verify that the linked lesson is referenced and the change addresses the identified gap.

---

### Edge Cases

- **Simultaneous multi-hazard warnings**: When multiple hazard types occur simultaneously (e.g., bushfire and flood) requiring different warning tiers for overlapping geographic areas, the system MUST issue independent warning chains per hazard type. Each warning references its specific hazard and tier. The COP MUST display all active warnings with geographic overlap clearly indicated.
- **Warning tier skipping**: For sudden-onset hazards (earthquake, tsunami, structural collapse), the system MUST support issuing an Emergency Warning directly without requiring prior Advice or Watch and Act tiers. The warning MUST log the tier-skip justification and the sudden-onset hazard type. Life safety (Constitution Principle I) takes precedence over sequential tier progression.
- **Evacuation abandonment mid-process**: If an evacuation route becomes impassable during Withdrawal, the Evacuation Agent MUST trigger immediate replanning (spec 009 replanning ≤15s target) and evaluate shelter-in-place as an alternative. The Decision stage re-activates with updated risk data. All stage transitions and rationale are audited.
- **Conflicting PPRR phases across overlapping incidents**: Each incident maintains its own independent PPRR phase designation. The platform MUST support concurrent phases (e.g., Response for one incident, Recovery for another in the same region) without mutual interference. Resource allocation conflicts across incidents are resolved per spec 011 cross-incident tie-breaking rules (severity, proximity, timestamp).
- **Recovery indicator regression**: When a recovery environment indicator regresses (e.g., economic recovery reverses due to a secondary disaster), the system MUST flag the regression, capture the cause, and trigger reassessment of the recovery plan for the affected environment. Recovery progress is tracked longitudinally and regression is a valid data point, not an error.
- **Contradictory lesson**: When a lesson contradicts an existing agent configuration or policy, the lesson MUST be flagged for escalated review. Resolution requires explicit approval from the Incident Controller or platform administrator. The system MUST NOT auto-apply contradictory lessons. The conflicting configuration and lesson are linked for audit traceability.
- **IC unavailable for warning approval**: AIIMS delegation chain applies. Authority passes to deputy IC, then next-in-command within the Control function. A configurable timeout (default 5 min for Emergency Warning, 15 min for lower tiers) triggers auto-escalation to the next authority in the chain. No warning is ever auto-approved without human authorisation (Constitution non-negotiable §1). All delegation events are fully audited with provenance.

## Requirements *(mandatory)*

### Functional Requirements

#### Australian Warning System (AWS) — Communication Agent Updates

- **FR-001**: The Communication Agent MUST generate warnings using the three-tier Australian Warning System: Advice (yellow), Watch and Act (orange), and Emergency Warning (red).
- **FR-002**: Each warning MUST follow the AWS nested model: Warning Level + Hazard/Location + Action Statement.
- **FR-003**: Warnings MUST include the appropriate hazard icon (cyclone, fire, flood, heat, storm, other) where graphical output is supported.
- **FR-004**: The Communication Agent MUST support de-escalation notices when threat levels reduce, clearly referencing the prior warning tier.
- **FR-005**: The Communication Agent MUST issue all-clear notifications when an incident is resolved, closing the warning chain.
- **FR-006**: Every warning MUST adhere to the ten warning principles: life-saving, empowering, trusted/authoritative/verifiable, risk-scaled, timely/targeted/tailored, impact-conveying, action-calling, clearly communicated, readily accessible, and part of a bigger picture.
- **FR-007**: Warnings MUST be accessible to vulnerable populations including CALD communities (translated content), people with disability (accessible formats), and all groups identified in Constitution §VI-C and the AIDR Evacuation Planning Handbook (2023) — including pregnant and breastfeeding women, people with ongoing health needs, and people with pets or assistance animals requiring evacuation support.

#### Total Warning System — Cross-Agent Integration

- **FR-008**: The platform MUST implement all six elements of the Total Warning System: situational awareness, monitoring and prediction, message construction, interpretation, communication, and community response.
- **FR-009**: The Monitoring Agent MUST produce situational-awareness outputs that feed the monitoring-and-prediction element.
- **FR-010**: The Risk Assessment Agent MUST produce hazard predictions that satisfy the monitoring-and-prediction element.
- **FR-011**: The Communication Agent MUST implement the message-construction and communication elements, including interpretation aids for diverse audiences.
- **FR-012**: The platform MUST capture community-response indicators (e.g., evacuation compliance, shelter utilisation) to close the warning-system feedback loop.

#### AIIMS Functional Alignment — All Agents

- **FR-013**: Every agent operating within the platform MUST be mapped to exactly one AIIMS functional role: Control, Intelligence, Planning, Operations, Logistics, or Public Information.
- **FR-014**: The platform MUST maintain and display the current AIIMS functional structure for each active incident within the Common Operating Picture.
- **FR-015**: Agents MUST support three incident levels (Level 1: local/single-agency, Level 2: significant/multi-agency, Level 3: major/regional/state-wide) with escalation and de-escalation between levels.
- **FR-016**: At Level 2 and above, the platform MUST establish a shared Common Operating Picture accessible to all participating entities.
- **FR-017**: Agents MUST respect the distinction between Command (vertical, within an entity), Control (horizontal, across entities), and Coordination (bringing together resources and efforts) in their communication and decision-making.
  Acceptance criteria: (a) Agent-to-agent communications within a single controlling entity use Command semantics (direct instruction). (b) Cross-entity communications use Coordination semantics (request/collaborate). (c) The COP displays the distinction between Command and Coordination relationships. (d) Test validates that a Level 2+ incident with multiple agencies shows Coordination links between agencies and Command links within each agency.

#### Five-Stage Evacuation Framework — Evacuation Agent Updates

- **FR-018**: The Evacuation Agent MUST implement all five evacuation stages: Decision, Warning, Withdrawal, Shelter, and Return.
- **FR-019**: The Decision stage MUST capture and record the decision authority, decision rationale, evacuation type (pre-warned or immediate), approach (directed, recommended, or self-initiated), and scope (total, partial, or phased).
- **FR-020**: The Warning stage MUST coordinate with the Communication Agent to issue evacuation-specific warnings with timeframes, routes, and shelter destinations.
- **FR-021**: The Withdrawal stage MUST provide real-time progress tracking and prioritise vulnerable populations (as defined in Constitution §VI-C and the AIDR Evacuation Planning Handbook 2023, including pregnant and breastfeeding women, people with ongoing health needs, and people with pets or assistance animals) for transport allocation.
- **FR-022**: The Shelter stage MUST track shelter capacity, welfare needs, and vulnerable-population status across all active shelter locations.
- **FR-023**: The Return stage MUST manage phased re-entry with safety-condition validation and return-completion tracking.
- **FR-024**: The system MUST support shelter-in-place as an alternative strategy, including rationale capture and ongoing monitoring of conditions.
- **FR-025**: The Evacuation Agent MUST support both pre-warned evacuations (with lead time) and immediate evacuations (sudden-onset events).

#### PPRR Lifecycle — Platform-Wide

- **FR-026**: The platform MUST support all four PPRR lifecycle phases: Prevention, Preparedness, Response, and Recovery.
- **FR-027**: Each incident or scenario MUST have a current PPRR phase designation that is visible in the Common Operating Picture.
- **FR-028**: Prevention phase MUST support hazard risk assessments and mitigation-option analysis.
- **FR-029**: Preparedness phase MUST support scenario rehearsal (simulation), community readiness assessment, resource pre-positioning, and warning system testing.
- **FR-030**: Response phase MUST encompass all existing real-time coordination capabilities and MUST initiate recovery planning concurrently.
- **FR-031**: Transitions between PPRR phases MUST be managed transitions, not abrupt switches, with overlap periods where multiple phases are active simultaneously.

#### Community Recovery — New Capability

- **FR-032**: The platform MUST provide recovery tracking across all four recovery environments: Social, Built, Economic, and Natural.
- **FR-033**: Recovery recommendations and plans MUST align with the six National Recovery Principles: understand the context, recognise complexity, use community-led approaches, coordinate all activities, communicate effectively, and acknowledge and build capacity.
- **FR-034**: The system MUST support community-led recovery approaches, including mechanisms for community input and local needs prioritisation.
- **FR-035**: Recovery agents MUST activate in parallel with response agents, not sequentially after response concludes.
- **FR-036**: The system MUST support longitudinal recovery tracking with measurable indicators for each recovery environment over weeks, months, and years.
- **FR-037**: Recovery progress MUST be visible to affected communities, not only to government agencies and platform operators.

#### Lessons Management — Quality Gates Enhancement

- **FR-038**: The platform MUST provide a structured lessons-capture process that is automatically initiated after any AIIMS Level 2 or Level 3 incident and any formally declared exercise. Level 1 incidents may optionally trigger lessons capture at the Incident Controller's discretion.
- **FR-039**: Each lesson MUST be categorised by AIIMS function, PPRR phase, and severity.
- **FR-040**: The system MUST maintain a lessons register that supports trend analysis, recurring-theme identification, and unresolved-item tracking.
- **FR-041**: Each lesson MUST be assignable to a responsible party with a target resolution date and tracked through to closure.
- **FR-042**: Quality gates for Pull Requests MUST support verification that changes addressing lessons-identified items reference the originating lesson and event.

#### Existing Spec Alignment — Gap Closure

- **FR-043**: The Monitoring Agent specification (010) MUST be updated to include AIDR-aligned warning classifications and escalation thresholds, and to explicitly feed the situational-awareness element of the Total Warning System.
- **FR-044**: The Risk Assessment Agent specification (012) MUST be updated to align hazard-severity scales with AIDR guidance and to explicitly feed the monitoring-and-prediction element of the Total Warning System.
- **FR-045**: The Resource Allocation Agent specification (011) MUST be updated to use AIDR/AIIMS-aligned prioritisation language and to support recovery-phase resource allocation.
- **FR-046**: The disaster response hub specification (001) MUST be updated to reference AIIMS functional structure, PPRR lifecycle, and the Shared Responsibility Model.
- **FR-047**: All agent specifications MUST include an AIIMS role mapping section that identifies which AIIMS function the agent fulfils.

#### Domain Model Alignment

- **FR-048**: The `PublicAlert` domain model MUST be extended with AWS-specific fields: `warning_tier` (Advice | Watch and Act | Emergency Warning), `colour_code` (yellow | orange | red), `hazard_icon` (cyclone | fire | flood | heat | storm | other), `action_statement`, and `superseded_warning_id`. Existing `PublicAlert` fields and lifecycle are preserved unchanged.
- **FR-049**: A new `AiimsRoleAssignment` domain model MUST be created linking an agent identifier to an AIIMS functional role for a specific incident, with assignment period tracking. This model complements the existing `OperatingFramework` (framework definition) and `FrameworkAssignment` (framework-to-jurisdiction mapping) but operates at the agent-per-incident level.
- **FR-050**: The `Incident` domain model MUST be extended with a `pprr_phase` field (Prevention | Preparedness | Response | Recovery) that is independent of the existing `status` enum. Multiple incidents MAY hold different PPRR phases concurrently. Prevention and Preparedness phases MAY apply to scenario/region contexts without an active incident.
- **FR-051**: The `Incident.incident_type` enum MUST be extended to include all hazard types specified in Constitution §III: `bushfire`, `flood`, `cyclone`, `storm`, `earthquake`, `tsunami`, `extreme_heat`, `pandemic`, and `other`.
- **FR-052**: Lessons captured from exercises (FR-038) MUST be linked to the corresponding `ExerciseReport` via `scenario_run_id`, enabling correlation between lesson observations and exercise performance metrics (`coordination_gaps`, `benchmark_comparison`).
- **FR-053**: PPRR phase transitions (FR-031) MUST be recorded as `TimelineEvent` entries with `event_type = "system"`, capturing the source phase, target phase, transition rationale, and authorising user. Overlap periods where multiple phases are active MUST be explicitly represented.
- **FR-054**: Handoff chains (`HandoffChainDefinition`) MUST be extended to support AIDR capability routing — specifically, recovery-phase handoffs from Risk Assessment to recovery-configured agents, and lessons-capture handoffs triggered by incident closure at Level 2+.

### Non-Functional Requirements

#### Performance and Concurrency

- **NFR-001**: Warning compliance validation (AWS three-tier model checks) MUST complete within 5 seconds per warning.
- **NFR-002**: AIIMS role assignment for a new incident MUST complete within 5 seconds.
- **NFR-003**: PPRR phase transitions MUST complete within 5 seconds.
- **NFR-004**: Recovery dashboard MUST load within 10 seconds, presenting all four recovery environments with current indicator values.
- **NFR-005**: Lessons capture (template presentation and initial save) MUST complete within 5 seconds.
- **NFR-006**: Lessons trend analysis across the full register MUST complete within 30 seconds.
- **NFR-007**: The platform MUST support at least 10 concurrent recovery operations.
- **NFR-008**: The platform MUST support at least 50 concurrent lessons in the register.

#### Observability

- **NFR-009**: Each AIDR capability MUST expose a health endpoint responding within 1 second, consistent with all existing agents.
- **NFR-010**: The following telemetry metrics MUST be emitted: `warning_compliance_rate`, `tier_transition_latency`, `evacuation_stage_duration`, `recovery_indicator_update_frequency`, `lesson_resolution_time`, `pprr_phase_transition_count`, `aiims_role_coverage_ratio`.

#### Graceful Degradation

- **NFR-011**: If the lessons register is unavailable, lessons MUST be buffered locally and synchronised when the register recovers. Incident operations MUST NOT be blocked by lessons subsystem failures.
- **NFR-012**: If recovery indicator data sources are unavailable, the recovery dashboard MUST display the last-known values with a staleness indicator rather than failing.

#### Content Safety and Data Protection

- **NFR-013**: All LLM-generated recovery recommendations and community-facing recovery content MUST pass content safety validation before presentation, consistent with the content safety pipeline established in spec 008 (`content_safety_result` field on `PublicAlert`).
- **NFR-014**: Recovery environment indicator data — particularly Social environment data (health, employment, social issues) — MUST comply with the Australian Privacy Act 1988 and applicable state/territory privacy legislation (Constitution non-negotiable §3). Community-level aggregations MUST not be identifiable to fewer than 10 individuals.
- **NFR-015**: All AIDR capability data (warnings, recovery indicators, lessons, evacuation records) MUST reside exclusively within Azure Australia East and Australia Southeast regions (Constitution non-negotiable §2). No cross-region replication outside Australia is permitted.

### Key Entities

- **Warning**: A public-facing alert conforming to the AWS three-tier model. Attributes include tier (Advice/Watch and Act/Emergency Warning), colour code, hazard type, hazard icon, location, action statement, issue time, issuing authority, and superseded-warning reference. *Domain model*: Extends existing `PublicAlert` (retains all current fields and lifecycle states) with new AWS-specific attributes per FR-048.
- **AIIMS Role Assignment**: The mapping of an agent to an AIIMS functional role for a given incident. Attributes include agent identifier, AIIMS function, incident reference, and assignment period. *Domain model*: New `AiimsRoleAssignment` model per FR-049. Complements — does not replace — `OperatingFramework` (AIIMS framework definition, `framework_type = "aiims"`) and `FrameworkAssignment` (framework-to-jurisdiction/org mapping).
- **Incident Level**: The current severity classification (Level 1, 2, or 3) for an active incident. Determines the scope of coordination, COP sharing, and escalation behaviours. *Domain model*: New field on existing `Incident` model. Independent of `Incident.severity` (triage urgency) and `HazardAssessment.severity_level` (risk assessment scale).
- **Evacuation Stage**: The current stage of an evacuation operation (Decision, Warning, Withdrawal, Shelter, Return, or Shelter-in-Place). Attributes include stage, start time, decision authority, scope, and stage-specific outputs. *Domain model*: New model. Augments spec 009's zone-based `EvacuationPlan` with AIDR five-stage lifecycle tracking.
- **PPRR Phase**: The current lifecycle phase designation for an incident or scenario (Prevention, Preparedness, Response, Recovery). Multiple phases may be active simultaneously. *Domain model*: New `pprr_phase` field on `Incident` per FR-050. Orthogonal to `Incident.status` — an `active` incident is typically in Response phase; a `recovery` status incident is in Recovery phase; Prevention/Preparedness phases may exist without an active incident.
- **Recovery Environment Tracker**: A longitudinal record tracking recovery progress across Social, Built, Economic, and Natural environments with AIDR-defined indicators. Social indicators: wealth, employment, amenity, health, social issues, social belonging, recreation/leisure (7). Built indicators: essential services, community infrastructure, transport networks, property/housing, planning/building compliance (5). Economic indicators: personal income, business premises, tourism, workforce availability, productive land (5). Natural indicators: air quality, water quality, land/soil health, biodiversity (4). Each indicator tracked over weeks, months, and years with regression detection. *Domain model*: New model with no existing equivalent. Community-level social data subject to NFR-014 privacy constraints.
- **Lesson**: An observation captured from an incident or exercise. Attributes include description, AIIMS function, PPRR phase, severity, assigned party, status (identified/in-progress/resolved), resolution reference, and originating event. *Domain model*: New model. For exercise-originated lessons, linked to `ExerciseReport` via `scenario_run_id` per FR-052.

## Assumptions

- The Constitution v1.1.0 (`.specify/memory/constitution.md`) is the authoritative source for AIDR requirements. This specification operationalises the Constitution's mandates into implementable capabilities.
- The six AIDR handbooks converted to Markdown in `docs/aidr/` are the reference materials. No additional AIDR publications are required for this scope.
- Existing agent specifications (001, 008, 009, 010, 011, 012) will be updated via amendments or addenda rather than full rewrites. The existing functional requirements remain valid; this specification adds AIDR-alignment requirements.
- Recovery capabilities are initially delivered through the existing agent framework; agents configured for recovery-phase operations are referred to as "recovery agents" in this specification (e.g., FR-035). A dedicated, standalone Recovery Agent may be introduced later but is not mandated. When this specification states "recovery agents MUST activate," it refers to existing agents (e.g., Resource Allocation, Communication) entering recovery-phase operation mode, not a separate agent type.
- Lessons management is a platform-wide capability, not assigned to a single agent. It operates as a cross-cutting concern integrated into quality gates and the COP.
- Community-response indicators (FR-012) may initially be manually entered by operators; automated collection is a future enhancement.
- The platform already supports simulation/rehearsal mode (spec 007); PPRR Preparedness phase leverages this existing capability.

## Dependencies

- **Constitution v1.1.0**: This specification directly implements the AIDR mandates established in the Constitution. Changes to the Constitution's AIDR sections would require corresponding updates here.
- **Existing Specs (001, 008, 009, 010, 011, 012)**: This specification requires amendments to all listed specs. Implementation should coordinate with any in-flight changes to those specs. Specific reconciliations: (a) Spec 008's flat 15-minute escalation timeout is superseded by this spec's tiered timeout (5 min Emergency Warning, 15 min lower tiers) for warning-related approvals — non-warning approvals retain 15 min; (b) Spec 009's zone-based evacuation model is augmented — not replaced — by the five-stage AIDR evacuation framework; existing zone routing and transport coordination capabilities are preserved; (c) Spec 012's `low/moderate/high/critical` severity scale is retained for risk assessment and is independent of AWS warning tiers — no automatic mapping between them.
- **AIDR Handbook Reference Materials** (`docs/aidr/`): The converted handbooks serve as the authoritative source for framework details, terminology, and process definitions.
- **Simulation & Tenant Isolation (007)**: PPRR Preparedness phase scenario rehearsal depends on the simulation capability defined in spec 007.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of public warnings generated by the Communication Agent conform to the AWS three-tier model, including correct tier label, colour code, hazard icon, and nested-model structure.
- **SC-002**: Every active incident displays a complete AIIMS functional-role mapping in the Common Operating Picture, with all six roles assigned.
- **SC-003**: Evacuation operations implement all five stages (Decision, Warning, Withdrawal, Shelter, Return) with each stage producing documented outputs and decision records, within the timeframes appropriate to the hazard type. Stages progress sequentially under normal conditions but MAY re-enter earlier stages when conditions change (e.g., Decision re-activation when routes become impassable during Withdrawal), with all stage transitions and re-entries audited.
- **SC-004**: The platform supports at least two concurrent PPRR phases for overlapping incidents (e.g., Response for one event, Recovery for another) without degradation of either.
- **SC-005**: Recovery tracking covers all four environments with the full AIDR indicator set: Social (7 indicators), Built (5 indicators), Economic (5 indicators), and Natural (4 indicators) — totalling 21 indicators as defined in the Recovery Environment Tracker entity.
- **SC-006**: 100% of warnings adhere to all ten warning principles as validated by a compliance checklist review.
- **SC-007**: Lessons captured after incidents or exercises are tracked through to resolution, with 90% of identified lessons reaching closure within 90 days of capture.
- **SC-008**: All six existing agent specifications include an AIIMS role-mapping section and reference the relevant AIDR guidance within 30 days of this specification's approval.
- **SC-009**: Vulnerable populations receive prioritised attention at every evacuation stage, with specific accommodations documented for each population group defined in Constitution §VI-C and the AIDR Evacuation Planning Handbook (2023), including pregnant and breastfeeding women, people with ongoing health needs, and people with pets or assistance animals.
- **SC-010**: The Total Warning System feedback loop is closed — community-response indicators are captured and available for review within 24 hours of a warning being issued.

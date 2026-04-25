# Feature Specification: AIDR Additional Guidance Integration

**Feature Branch**: `019-aidr-additional-guidances`  
**Created**: 2025-07-18  
**Status**: Draft  
**Input**: User description: "Integrate three additional AIDR guidance documents — Emergency Planning Handbook (2020), Monitoring and Evaluation Framework for Disaster Recovery Programs (v2), and Outcomes, Activities and Indicators for Recovery Programs — into the disaster response platform, extending the work started in spec 018."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Emergency Planning Guidance for Preparedness (Priority: P1)

An emergency planner uses the platform to develop, document, and maintain emergency plans for a flood-prone region. The platform guides the planner through the AIDR emergency planning process: establishing a project plan and team, conducting risk assessment and consequence analysis across the four environments (social, built, economic, natural), developing prevention/preparedness/response/recovery strategies, documenting the plan with all required elements, and scheduling exercises and reviews. The platform applies the eight AIDR emergency planning principles — risk-informed, reducing unknowns, collaborative and inclusive, strategic, solutions-oriented, iterative, enabling adaptive capacity, and shared responsibility — throughout the process.

**Why this priority**: Emergency planning is a foundational preparedness activity that directly strengthens the platform's Prevention and Preparedness phases (PPRR). Without structured planning guidance, the platform cannot support the "front end" of emergency management. The Constitution (§II, Principle 6: Risk-based; Principle 2: Comprehensive) mandates this capability.

**Independent Test**: Can be fully tested by initiating a new emergency plan for a simulated flood-prone region, stepping through each phase of the planning process, and verifying that each step produces AIDR-compliant outputs with appropriate risk analysis, stakeholder engagement records, and plan documentation elements.

**Acceptance Scenarios**:

1. **Given** a user initiates a new emergency plan for a region, **When** the planning process begins, **Then** the system MUST present the AIDR emergency planning process steps (establish project plan, establish project team, communicate and consult, understand risks and consequences, develop strategies, document and trial, endorse, implement and exercise, monitor and review) and guide the user through each step.
2. **Given** the risk assessment step is active, **When** the planner analyses hazards, **Then** the system MUST structure the assessment across all four environments (social, built, economic, natural) and support consideration of cascading, concurrent, and catastrophic scenarios as defined in the Emergency Planning Handbook.
3. **Given** plan documentation is being prepared, **When** the planner generates the plan document, **Then** it MUST include all required AIDR plan elements: authority, security rating, review schedule, amendment register, distribution list, aim and objectives, legislative context, scope, leadership structures, roles and responsibilities, resource requirements, PPRR-phase-specific arrangements, exercise schedule, and recovery arrangements.
4. **Given** a completed plan, **When** the planner schedules review and exercise cycles, **Then** the system MUST track plan currency, upcoming exercise dates, and trigger review reminders based on configurable intervals or after significant events.
5. **Given** the platform has multiple emergency plans, **When** a planner views the plan hierarchy, **Then** the system MUST display plan relationships (national, state, regional, local) and identify interoperability considerations between plans.

---

### User Story 2 — Monitoring and Evaluation for Recovery Programs (Priority: P1)

A Recovery Coordinator sets up a monitoring and evaluation (M&E) framework for a bushfire community recovery program. The platform guides them through defining the affected community, selecting appropriate recovery outcomes from the nationally agreed outcome tables, developing a program logic model that maps resources → activities → outputs → intermediate outcomes → final outcomes, establishing indicators and data collection plans, and producing monitoring reports. The M&E framework covers all five key evaluation question domains: governance, community engagement, effectiveness, efficiency, and implementation.

**Why this priority**: Without structured M&E, recovery programs cannot demonstrate effectiveness, and lessons cannot feed back into improved future programs. The M&E Framework (v2) is the national standard for recovery evaluation, directly supporting the Constitution's continual improvement principle (§II, Principle 11) and the six National Recovery Principles (§VII-A). This addresses a gap in spec 018, which established recovery tracking indicators but not the overarching evaluation framework.

**Independent Test**: Can be fully tested by creating a simulated bushfire recovery program, configuring its M&E framework with selected outcomes and program logic, collecting sample indicator data over simulated time periods, and verifying that the system produces meaningful monitoring and evaluation reports with appropriate standards of success.

**Acceptance Scenarios**:

1. **Given** a new recovery program is initiated, **When** the coordinator sets up M&E, **Then** the system MUST present the nationally agreed recovery outcomes organised by domain (Overarching/Resilience & Sustainability, Social, Economic, Built Environment, Natural Environment) for selection.
2. **Given** outcomes have been selected, **When** the coordinator builds a program logic, **Then** the system MUST support defining an outcomes chain with resources, activities, outputs, intermediate outcomes, and final outcomes, and allow restating generic outcomes into community-specific terms.
3. **Given** a program logic is defined, **When** the coordinator establishes indicators, **Then** the system MUST suggest indicators from the AIDR Outcomes, Activities and Indicators catalogue that match the selected outcomes, and support custom indicator definition.
4. **Given** indicator data is being collected, **When** the coordinator reviews monitoring data, **Then** the system MUST present progress against baseline values, highlight trends (positive, negative, stagnant), and flag indicators that fall below defined standards of success.
5. **Given** an evaluation period has elapsed, **When** the coordinator generates an evaluation report, **Then** the report MUST address the five key evaluation question domains (governance, community engagement, effectiveness, efficiency, implementation) and present findings with supporting evidence.

---

### User Story 3 — Outcomes-Based Recovery Tracking Across Four Domains (Priority: P1)

A Recovery Coordinator uses the platform to track measurable recovery outcomes across all four recovery domains — social, economic, built environment, and natural environment — for a cyclone-affected community. For each domain, the system presents the AIDR-defined outcomes with their associated activities and measurable indicators. The coordinator tracks both sustainability outcomes (community can continue recovery independently) and resilience outcomes (community is better prepared for future disasters). Progress is measured through quantitative and qualitative indicators mapped from the AIDR Outcomes, Activities and Indicators catalogue.

**Why this priority**: Spec 018 established 21 high-level indicators across the four recovery environments. This story extends that with the full AIDR outcomes-activities-indicators framework — dozens of specific, measurable indicators per domain with associated activities. This transforms recovery from a dashboard of summary metrics into a comprehensive outcomes-based tracking system aligned with national standards. The Constitution (§VII-B) mandates all four recovery environments be addressed.

**Independent Test**: Can be fully tested by configuring a cyclone recovery scenario with outcomes selected from each of the four domains, entering sample indicator data, and verifying that the system tracks progress toward both sustainability and resilience objectives with appropriate activities linked to each outcome.

**Acceptance Scenarios**:

1. **Given** recovery tracking is configured for a community, **When** the coordinator selects social domain outcomes, **Then** the system MUST present the full AIDR social outcomes catalogue (e.g., community health levels, access to housing, social networks, education continuity, psychosocial support, safety and security, community capacity and resilience) with their associated activities and measurable indicators.
2. **Given** economic domain tracking is active, **When** the coordinator reviews economic indicators, **Then** the system MUST track outcomes including business continuity, employment rates, economic diversity, access to goods and services, financial security, supply chain stability, and business confidence — each with their AIDR-defined indicators.
3. **Given** built environment recovery is underway, **When** the coordinator monitors infrastructure restoration, **Then** the system MUST track essential services infrastructure, community infrastructure, private infrastructure (residential, commercial, rural), and resilience outcomes (infrastructure rebuilt to reduce future disaster impact).
4. **Given** natural environment recovery is in progress, **When** the coordinator assesses environmental restoration, **Then** the system MUST track outcomes including environmental health risks, biodiversity and ecosystems, cultural heritage restoration, and community awareness of future environmental disaster risks.
5. **Given** recovery data is being collected over time, **When** the coordinator distinguishes sustainability from resilience outcomes, **Then** the system MUST separately track and report on sustainability objectives (community managing own recovery) and resilience objectives (community better prepared for future disasters) for each domain.
6. **Given** vulnerable groups are identified in the recovery, **When** recovery outcomes are assessed, **Then** the system MUST support restating outcomes in terms specific to vulnerable populations and tracking their recovery separately, consistent with the AIDR M&E Framework guidance.

---

### User Story 4 — AI-Assisted Indicator Analysis and Recommendations (Priority: P2)

A Recovery Coordinator reviews recovery progress and receives intelligent analysis from the platform. The system identifies patterns across indicator data, highlights correlations between domains (e.g., economic recovery lagging because built environment restoration is incomplete), suggests activities from the AIDR catalogue that could address lagging indicators, and generates natural-language summaries of recovery status for community communication and government reporting.

**Why this priority**: The volume of AIDR indicators across four domains (potentially hundreds of data points) exceeds what coordinators can manually analyse. Intelligent analysis turns raw data into actionable insights, accelerating recovery decision-making. This leverages Azure AI capabilities to enhance M&E beyond manual reporting.

**Independent Test**: Can be fully tested by populating a recovery scenario with mixed indicator data (some progressing, some regressing, some stagnant), requesting AI analysis, and verifying that the system identifies cross-domain correlations, recommends relevant AIDR activities, and produces coherent natural-language summaries.

**Acceptance Scenarios**:

1. **Given** recovery indicator data is available across multiple domains, **When** the coordinator requests an analysis, **Then** the system MUST identify cross-domain correlations (e.g., housing delays impacting social connectedness) and present them with supporting evidence.
2. **Given** specific indicators are lagging behind targets, **When** the system generates recommendations, **Then** it MUST suggest relevant activities from the AIDR Outcomes, Activities and Indicators catalogue that are associated with the lagging outcomes.
3. **Given** a reporting period has ended, **When** the coordinator generates a community-facing summary, **Then** the system MUST produce a plain-language recovery status report suitable for public communication, covering progress in each active domain.
4. **Given** generated analysis and recommendations, **When** content is presented to the coordinator, **Then** all AI-generated content MUST pass content safety validation before display, consistent with the existing content safety pipeline.

---

### User Story 5 — Emergency Plan Integration with Incident Response (Priority: P2)

An Incident Controller activates a pre-existing emergency plan when a flood event occurs. The platform retrieves the relevant emergency plan, presents the documented response arrangements, roles and responsibilities, resource requirements, and communication protocols. As the event progresses through PPRR phases, the platform references the plan's phase-specific arrangements and tracks plan activation, implementation actions, and post-event review requirements.

**Why this priority**: Emergency plans are only valuable if they are accessible and actionable during incidents. Linking plans to live incident management closes the gap between preparedness and response, making pre-event planning directly useful during operations. The Emergency Planning Handbook emphasises that plans must be accessible and implementable.

**Independent Test**: Can be fully tested by creating an emergency plan during preparedness, simulating a flood event, activating the plan, and verifying that plan content is surfaced during response with appropriate role assignments and resource triggers.

**Acceptance Scenarios**:

1. **Given** an emergency plan exists for a region, **When** an incident occurs in that region, **Then** the system MUST identify and present the relevant emergency plan(s) with activation recommendations.
2. **Given** an emergency plan is activated, **When** the Incident Controller reviews the plan, **Then** the system MUST display the plan's response arrangements, roles and responsibilities, resource requirements, and communication protocols in an operationally useful format.
3. **Given** an incident transitions between PPRR phases, **When** recovery arrangements are needed, **Then** the system MUST surface the plan's recovery arrangements section and any linked recovery program M&E frameworks.
4. **Given** an incident has concluded, **When** the post-event review process begins, **Then** the system MUST flag that the emergency plan requires review and update based on lessons identified, per the AIDR monitoring and review guidance.

---

### User Story 6 — Program Logic Model Builder (Priority: P3)

A program designer uses the platform to build and visualise a program logic model for a new disaster recovery program. Starting from the AIDR national program logic template, they map their specific resources, activities, outputs, and outcomes into a structured diagram. The platform supports both ex ante (planning-stage) and ex post (evaluation-stage) program logic development as defined in the M&E Framework.

**Why this priority**: Program logic models are the central planning tool in the AIDR M&E Framework, connecting activities to outcomes. A structured builder reduces the effort of creating these models and ensures consistency with national standards. This is a supporting capability that enhances the M&E workflow but is not essential for initial M&E operation.

**Independent Test**: Can be fully tested by using the builder to create a program logic for a sample recovery program, defining resource → activity → output → outcome chains, and verifying the resulting model aligns with the AIDR national program logic structure.

**Acceptance Scenarios**:

1. **Given** a recovery program is being designed, **When** the designer starts a new program logic, **Then** the system MUST present the AIDR national program logic template with the standard elements: resources/inputs, activities, outputs, intermediate outcomes, and final outcomes (sustainability and resilience).
2. **Given** the designer is building an ex ante program logic, **When** they define outcomes, **Then** the system MUST support linking to nationally agreed outcomes from the AIDR catalogue and constructing an outcomes chain with a timeline.
3. **Given** the designer is building an ex post program logic, **When** they reverse-engineer the logic from an existing program, **Then** the system MUST support identifying final outcomes, tracing back through intermediate outcomes, and mapping to actual activities and resources deployed.

---

### Edge Cases

- **Overlapping recovery programs for same community**: When multiple recovery programs target the same community with shared outcomes, the system MUST support linking programs to shared indicator data while maintaining separate program logic models and evaluation reports. Indicator data collected for one program MUST be available to other programs targeting the same outcomes, avoiding duplicate data collection.
- **Indicator data unavailable or delayed**: When scheduled indicator data is not available (e.g., census data delayed, survey not completed), the system MUST display the last-known value with a staleness indicator, flag the gap in monitoring reports, and allow the coordinator to record the reason for data unavailability. M&E reporting MUST proceed with available data rather than blocking.
- **Emergency plan activation during plan revision**: When an emergency plan is being updated and an incident occurs requiring plan activation, the system MUST activate the last endorsed version of the plan (not the in-progress draft) and flag to the planner that the active plan differs from the draft. Post-event review MUST incorporate both the live experience and the pending revisions.
- **Recovery outcome regression after program closure**: When a recovery program has concluded but subsequent monitoring shows indicator regression (e.g., economic indicators decline after government assistance withdrawal), the system MUST flag the regression, assess whether the community sustainability threshold has been compromised, and recommend whether program reactivation should be considered.
- **Conflicting standards of success across stakeholders**: When different stakeholders (e.g., federal government, state government, local community) define different standards for the same indicator, the system MUST support multiple standards and present indicator progress against each standard separately in reports. The coordinator MUST be able to designate which standard is primary for evaluation purposes.
- **Cross-domain cascading recovery impacts**: When an activity in one domain (e.g., built environment infrastructure repair) is a prerequisite for outcomes in another domain (e.g., economic recovery requires restored transport), the system MUST track these cross-domain dependencies in the program logic and alert coordinators when upstream domain delays will impact downstream domain outcomes.
- **Plan hierarchy conflicts**: When a local emergency plan's arrangements conflict with a state-level plan, the system MUST flag the inconsistency during plan documentation and reference the AIDR guidance that plans within a hierarchy should ensure consistent terminology, responsibilities, and arrangements.

## Requirements *(mandatory)*

### Functional Requirements

#### Emergency Planning — Planning Agent Enhancement

- **FR-001**: The Planning Agent MUST support the AIDR emergency planning process with all nine steps: establish project plan, establish project team, communicate and consult, understand risks and consequences, develop strategies and arrangements, document and trial, endorse the plan, implement and exercise, and monitor and review.
- **FR-002**: Emergency plans MUST be structured with all required AIDR plan elements (27 total per Emergency Planning Handbook Chapter 3): contents/abbreviations/glossary, authority, security rating, review schedule, amendment register, distribution list, aim and objectives, legislative and policy context, plan context, plan scope, leadership and network structures, roles and responsibilities, financial management, communication systems, information management, resource capability and capacity, prevention and mitigation arrangements, preparedness arrangements, public education and community engagement, plan scheduling and activation, response arrangements, emergency control and coordination facilities, public information and warnings, evacuation management, relief arrangements, recovery arrangements, and exercise schedule.
- **FR-003**: The risk assessment component MUST analyse hazards across all four environments (social, built, economic, natural) and support assessment of cascading, concurrent, and catastrophic disaster scenarios.
- **FR-004**: The system MUST apply the eight AIDR emergency planning principles (risk-informed, reducing unknowns, collaborative and inclusive, strategic, solutions-oriented, iterative, enabling adaptive capacity, shared responsibility) as validation criteria for plan completeness.
- **FR-005**: Emergency plans MUST support the hierarchical framework (national, state, regional, local) with explicit relationships between plans and interoperability tracking.
- **FR-006**: The system MUST track plan currency including version history, endorsement status, next review date, and exercise completion records. Emergency Plans follow a formal lifecycle: `Draft` → `InConsultation` → `UnderReview` → `Endorsed` → `Activated` → `PostEventReview` → `Superseded`. Valid state transitions with authorization:
  - `Draft` → `InConsultation` (Planning Officer)
  - `InConsultation` → `UnderReview` (Planning Officer)
  - `InConsultation` → `Draft` (Planning Officer — major rework required)
  - `UnderReview` → `Endorsed` (Designated Authority per plan hierarchy level)
  - `UnderReview` → `Draft` (Designated Authority rejects — returns for revision)
  - `Endorsed` → `Activated` (Incident Controller — only when linked to a live incident)
  - `Activated` → `PostEventReview` (Incident Controller or Planning Officer — after incident concludes)
  - `PostEventReview` → `Draft` (Planning Officer — creates new version; original transitions to Superseded)
  - Any non-terminal state → `Superseded` (system-triggered when a newer version reaches Endorsed)
  - `Superseded` is a terminal state. No other transitions are permitted.
- **FR-007**: The system MUST support plan activation during incidents, linking the plan's documented arrangements to the live incident management operations and AIIMS functional structure.
- **FR-007a**: Emergency plan access MUST be governed by AIIMS role-based authorization: Planning Officer (AIIMS Planning function) creates and edits plans; Incident Controller activates plans during incidents; plan endorsement requires the designated authority appropriate to the plan's hierarchy level. Plan visibility follows the plan's security rating.

#### Monitoring and Evaluation Framework — Recovery Enhancement

- **FR-008**: The platform MUST implement the AIDR M&E Framework for disaster recovery programs, supporting the full evaluative activity lifecycle: identifying program outcomes, developing program logic, community needs analysis, preparing M&E plans, process evaluation, monitoring and reporting, outcome evaluation, and disseminating findings.
- **FR-009**: The system MUST present the nationally agreed recovery outcome tables organised by domain: Overarching (Resilience & Sustainability), Social, Economic, Built Environment, and Natural Environment — as defined in the M&E Framework Tables 2–6. The type alias `RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]` represents all five domains in catalogue entities. The existing `RecoveryEnvironment` type (4 values, without "overarching") is retained for backward compatibility with spec 018's `RecoveryEnvironmentTracker`. Overarching outcomes are cross-cutting; their indicators roll up into the relevant concrete domain tracker(s).
- **FR-010**: The system MUST support program logic model creation for both ex ante (planning-stage) and ex post (evaluation-stage) approaches, including resources/inputs, activities, outputs, intermediate outcomes, and final outcomes with timeline projections.
- **FR-011**: The system MUST support the five key evaluation question domains from the M&E Framework: governance of the recovery process, community engagement, effectiveness, efficiency, and implementation. These domains are evaluation structuring dimensions that shape report sections and analysis — they do NOT alter indicator data collection or monitoring workflows. The M&E Framework entity stores active evaluation domains as `active_evaluation_domains: list[EvaluationDomain]` where `EvaluationDomain = Literal["governance", "community_engagement", "effectiveness", "efficiency", "implementation"]`. Standard evaluation questions per domain are seeded as reference data from AIDR M&E Framework §5.2.
- **FR-012**: The system MUST support defining standards of successful recovery for each selected outcome, enabling comparison of actual indicator values against defined thresholds.
- **FR-013**: The system MUST generate monitoring reports that track program progress against the program logic, highlight indicator trends, and flag areas requiring intervention.
- **FR-014**: Evaluation findings MUST be structured for dissemination to stakeholders including government at all levels, affected communities, NGOs, and the research community.

#### Outcomes, Activities and Indicators — Recovery Tracking Enhancement

- **FR-015**: The system MUST incorporate the full AIDR Outcomes, Activities and Indicators catalogue spanning all five recovery domains (overarching, social, economic, built, natural), with each outcome linked to its defined activities and measurable indicators. Catalogue scale: ~61 outcomes, ~200 activities, ~300 indicators. Catalogue entities use hierarchical IDs: `aidr:{domain}:{outcome-slug}` for outcomes, `aidr:{domain}:{outcome-slug}:act:{index}` for activities, `aidr:{domain}:{outcome-slug}:ind:{index}` for indicators. All catalogue data resides in a single Cosmos DB container `recovery-catalogue` partitioned by `domain`. The existing `RecoveryIndicator` model (spec 018) gains an optional `catalogue_indicator_id: str | None` field to link high-level tracker indicators to their detailed AIDR catalogue counterparts.
- **FR-016**: Social domain tracking MUST cover all AIDR-defined social outcomes including but not limited to: community health levels, access to housing, social networks, education continuity, safety and security, psychosocial support, access to social services, creative expression, and community capacity for future disasters.
- **FR-017**: Economic domain tracking MUST cover all AIDR-defined economic outcomes including but not limited to: business continuity, access to financial services, employment and workforce skills, economic diversity, supply chain stability, business confidence, insurance accessibility, and business continuity planning.
- **FR-018**: Built environment tracking MUST cover all AIDR-defined built outcomes including: essential services infrastructure (water, sewerage, electricity, gas, transport, telecommunications), community infrastructure (education, health, welfare), private infrastructure (residential, commercial, rural), and resilience-focused rebuilding.
- **FR-019**: Natural environment tracking MUST cover all AIDR-defined environmental outcomes including: environmental health risks, biodiversity and ecosystem health, cultural heritage restoration, and community awareness of future environmental disaster risks.
- **FR-020**: For each outcome, the system MUST present the associated AIDR-defined activities as a menu of evidence-based interventions that recovery programs can adopt.
- **FR-021**: For each outcome, the system MUST present the associated AIDR-defined measurable indicators with guidance on data collection methodology where available.
- **FR-022**: The system MUST support restating generic AIDR outcomes into community-specific terms, as prescribed by the M&E Framework Step 3, to focus evaluation on the particular context of the affected community.
- **FR-023**: The system MUST separately track sustainability outcomes (community can continue recovery without government disaster-related assistance) and resilience outcomes (community is better prepared for future disasters) for each domain.
- **FR-024**: The system MUST track indicators for vulnerable populations separately where outcomes can be disaggregated, consistent with the M&E Framework guidance and Constitution §VI-C.

#### AI-Assisted Analysis

- **FR-025**: The system MUST provide AI-assisted cross-domain correlation analysis that identifies relationships between indicators across different recovery domains (e.g., built environment delays impacting economic recovery).
- **FR-026**: The system MUST generate activity recommendations from the AIDR catalogue when indicators are lagging behind standards of success.
- **FR-027**: The system MUST produce natural-language recovery status summaries suitable for community communication, government reporting, and inter-agency coordination.
- **FR-028**: All AI-generated content (analysis, recommendations, summaries) MUST pass content safety validation before presentation, consistent with the existing content safety pipeline (spec 008).

#### Integration with Existing Capabilities

- **FR-029**: Emergency planning capabilities MUST integrate with the PPRR lifecycle (spec 018 FR-026–FR-031), with emergency planning being the primary activity within the Preparedness phase and plan content feeding directly into Response and Recovery phase operations.
- **FR-030**: M&E framework capabilities MUST integrate with the existing recovery tracking (spec 018 FR-032–FR-037) by extending the 21 high-level recovery indicators with the full AIDR outcomes-activities-indicators structure.
- **FR-031**: The outcomes-based tracking MUST be compatible with the existing Recovery Environment Tracker entity (spec 018) by providing the detailed indicator data that rolls up into the tracker's summary view.
- **FR-032**: Emergency planning stakeholder engagement records MUST link to the community-led recovery approach requirements (spec 018 FR-034) to maintain continuity of community engagement from planning through recovery.
- **FR-033**: Lessons identified from M&E evaluations MUST feed into the lessons management system (spec 018 FR-038–FR-042) to close the continuous improvement loop between evaluation findings and platform enhancement.
- **FR-034**: The AIDR Handbook Reference table in the Constitution MUST be updated to include the three new handbooks: Emergency Planning (2020), Monitoring and Evaluation Framework (v2, 2018), and Outcomes, Activities and Indicators for Recovery Programs.

#### Non-Functional Requirements

- **NFR-001**: Emergency plan generation (full document assembly) MUST complete within 15 seconds.
- **NFR-002**: M&E framework configuration (outcome selection, program logic setup) MUST be completable within a single session of under 30 minutes for a standard recovery program.
- **NFR-003**: Recovery indicator dashboard (expanded AIDR catalogue view) MUST load within 10 seconds, consistent with the spec 018 NFR-004 recovery dashboard target.
- **NFR-004**: AI-assisted cross-domain analysis MUST complete within 30 seconds for a recovery program with up to 50 active indicators.
- **NFR-005**: The system MUST support at least 20 concurrent active emergency plans across different regions.
- **NFR-006**: The system MUST support at least 10 concurrent M&E frameworks for active recovery programs, consistent with spec 018 NFR-007 (10 concurrent recovery operations).
- **NFR-007**: The following additional telemetry metrics MUST be emitted: `emergency_plan_activation_count`, `me_framework_completion_rate`, `recovery_indicator_collection_rate`, `outcome_achievement_rate`, `plan_currency_compliance_ratio`.
- **NFR-008**: All M&E indicator data, emergency plan content, and recovery outcome data MUST reside exclusively within Azure Australia East and Australia Southeast regions, consistent with spec 018 NFR-015 and Constitution non-negotiable §2.
- **NFR-009**: Social recovery indicator data MUST comply with the privacy constraints established in spec 018 NFR-014 — community-level aggregations MUST not be identifiable to fewer than 10 individuals.

### Key Entities

- **Emergency Plan**: A structured document conforming to the AIDR Emergency Planning Handbook format. Attributes include plan identifier, region/entity scope, hazard type(s) covered, PPRR phase coverage, authority, current version, next review date, plan hierarchy level (national/state/regional/local), parent plan reference, and security rating. **Lifecycle states**: `Draft` (initial creation, steps 1–6 in progress) → `InConsultation` (stakeholder consultation active, step 3) → `UnderReview` (formal review before endorsement) → `Endorsed` (approved by designated authority, step 7) → `Activated` (linked to a live incident, step 8 operational) → `PostEventReview` (post-incident review triggered, step 9) → `Superseded` (replaced by a newer version). **Valid transitions**: Draft→InConsultation, InConsultation→UnderReview, InConsultation→Draft (rework), UnderReview→Endorsed, UnderReview→Draft (rejected), Endorsed→Activated (live incident only), Activated→PostEventReview (post-incident), PostEventReview→Draft (new version; original→Superseded), Any non-terminal→Superseded (system). Superseded is terminal. Contains sub-elements for each of the 27 required AIDR plan sections. Linked to incidents via plan activation records. **Authorization**: Planning Officer (AIIMS role) creates/edits plans; Incident Controller activates plans; endorsement requires the designated authority per plan hierarchy level.
- **Planning Process Record**: Tracks progress through the nine-step AIDR emergency planning process for a specific plan. Attributes include current step, step completion status, project team membership, stakeholder engagement log, risk assessment reference, and endorsement approvals.
- **M&E Framework**: The monitoring and evaluation configuration for a specific recovery program. Attributes include program identifier, affected community definition, selected outcomes (with community-specific restatements), program logic model, indicator selection, data collection schedule, active evaluation question domains (`active_evaluation_domains: list[EvaluationDomain]` where `EvaluationDomain = Literal["governance", "community_engagement", "effectiveness", "efficiency", "implementation"]`), and standards of success per selected outcome. Linked to one or more recovery programs and their Recovery Environment Trackers.
- **Program Logic Model**: A structured representation of how a recovery program's resources and activities connect to intended outcomes. Attributes include model type (ex ante or ex post), resources/inputs, activities, outputs, intermediate outcomes, final outcomes (sustainability and resilience), outcome chain relationships, and timeline projections.
- **Recovery Outcome**: A nationally agreed outcome from the AIDR catalogue, belonging to a `RecoveryDomain` (Overarching, Social, Economic, Built, Natural) and objective type (sustainability or resilience). Catalogue ID scheme: `aidr:{domain}:{outcome-slug}` (e.g., `aidr:social:community-health-levels`). Each outcome has associated activities (`CatalogueActivity`, ID: `aidr:{domain}:{outcome-slug}:act:{index}`) and indicators (`CatalogueIndicator`, ID: `aidr:{domain}:{outcome-slug}:ind:{index}`). All catalogue entries are immutable reference data in Cosmos DB container `recovery-catalogue`, partitioned by `domain`. Community-specific restatements are stored as separate mutable attributes linked to the generic outcome. Catalogue scale: ~61 outcomes (~7 overarching, ~24 social, ~19 economic, ~6 natural, ~5 built), ~200 activities, ~300 indicators.
- **Recovery Indicator**: A measurable data point associated with one or more recovery outcomes. Attributes include indicator name, domain, associated outcome(s), data collection methodology, baseline value, current value, target/standard value, collection frequency, last collected date, trend direction, and staleness flag. Extends the spec 018 Recovery Environment Tracker indicators with granular AIDR catalogue data via an optional `catalogue_indicator_id: str | None` field linking to the corresponding `CatalogueIndicator` entry. Indicators may be quantitative, qualitative, or both — qualitative indicators complement quantitative measures per AIDR M&E Framework guidance.
- **Evaluation Report**: A structured evaluation document addressing the five M&E key evaluation question domains. Attributes include evaluation period, program reference, findings by evaluation domain, evidence references, recommendations, and dissemination records.

## Assumptions

- The three new AIDR handbooks have been converted to Markdown and are available in `docs/aidr/` — Emergency Planning in `docs/aidr/emergency-planning/handbook.md`, M&E Framework in `docs/aidr/monitoring-evaluation-framework/handbook.md`, and Outcomes/Indicators in `docs/aidr/outcomes-indicators/handbook.md`.
- This specification extends — not replaces — spec 018. All spec 018 requirements, entities, and capabilities remain valid. The new capabilities build on top of the existing recovery tracking, PPRR lifecycle, and lessons management infrastructure.
- The AIDR Outcomes, Activities and Indicators catalogue is treated as immutable reference data seeded at deployment from parsed handbook content into Cosmos DB (container: `recovery-catalogue`, partition key: `domain`). Catalogue scale: ~61 outcomes (~7 overarching, ~24 social, ~19 economic, ~6 natural, ~5 built), ~200 activities, ~300 indicators. Not all outcomes will have developed activities and indicators (the source document notes several outcomes where "no activities or indicators were developed"). The system presents what exists and supports user-defined extensions stored separately from the reference catalogue. Standard evaluation questions per KEQ domain (from AIDR M&E Framework §5.2) are seeded alongside the outcomes catalogue as additional reference data.
- Emergency planning capabilities are delivered through a **new `planning` agent** (mapping to the AIIMS Planning function) created under `apps/agents/planning/` using the existing `create_app()` factory pattern and FastAPI conventions. M&E and indicator tracking capabilities extend the existing `monitoring` agent (`apps/agents/monitoring/`). Outcomes-based recovery tracking is a domain model concern exposed through these agents, not a separate agent.
- AI-assisted analysis capabilities leverage the existing Azure AI / Azure OpenAI infrastructure established in other specs. No new AI service provisioning is assumed beyond existing capacity.
- Recovery indicator data entry is initially manual or semi-automated. Full integration with external data sources (ABS census, health department reporting systems, etc.) is a future enhancement beyond this scope. Indicator data supports CSV import for bulk entry; emergency plans export as structured JSON (API interop) and PDF (human distribution).
- The M&E Framework database referenced in the AIDR handbook (the National Disaster Recovery Monitoring and Evaluation Database at knowledge.aidr.org.au) is used as a reference for past evaluations but is not directly integrated with the platform. Users may consult it independently.

## Dependencies

- **Spec 018 (AIDR Guidance Integration)**: This specification directly extends spec 018's recovery tracking (FR-032–FR-037), PPRR lifecycle (FR-026–FR-031), and lessons management (FR-038–FR-042). The Recovery Environment Tracker entity from spec 018 is the parent structure for the expanded indicator data.
- **Constitution v1.1.0**: The Constitution MUST be amended to add the three new handbooks to the AIDR Handbook Collection Reference table (FR-034). New sections may be needed for Emergency Planning principles and M&E requirements.
- **Existing Specs (001, 007, 008, 009)**: Emergency plan activation (FR-007) integrates with incident management (001). Scenario rehearsal for plan exercises leverages simulation capabilities (007). Content safety for AI outputs references the pipeline from spec 008. Evacuation plan sections reference spec 009.
- **AIDR Handbook Reference Materials** (`docs/aidr/`): The three converted handbooks serve as the authoritative source for framework details, outcome catalogues, planning processes, and indicator definitions.

## Terminology

- **Recovery domain** is the canonical term in this specification for the four recovery groupings (Social, Economic, Built, Natural) plus the Overarching domain. This aligns with the AIDR M&E Framework Tables 2–6 headings. The type alias `RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]` is used for catalogue entities (RecoveryOutcome, CatalogueActivity, CatalogueIndicator). The existing code type alias `RecoveryEnvironment = Literal["social", "built", "economic", "natural"]` (from spec 018) is retained unchanged for backward compatibility with `RecoveryEnvironmentTracker` and `RecoveryIndicator`. New code and user-facing text MUST use "domain". The Constitution's references to "four recovery environments" are understood as synonymous with the four concrete domains (excluding overarching).
- **Evaluation domain** refers to one of the five M&E key evaluation question (KEQ) domains: governance, community engagement, effectiveness, efficiency, implementation. The type alias `EvaluationDomain = Literal["governance", "community_engagement", "effectiveness", "efficiency", "implementation"]` is used in M&E Framework configuration. These domains structure evaluation analysis and reporting only; they do not alter indicator data collection.
- **Catalogue indicator** vs **tracker indicator**: A "catalogue indicator" (`CatalogueIndicator`) is an immutable AIDR-defined indicator template from the seeded reference data. A "tracker indicator" (`RecoveryIndicator`) is a live data point in a `RecoveryEnvironmentTracker` with actual baseline/current/target values. Tracker indicators link to catalogue indicators via the optional `catalogue_indicator_id` field.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Emergency plans generated by the platform include 100% of the 27 required AIDR plan elements documented in the Emergency Planning Handbook Chapter 3 (including the structural contents/abbreviations/glossary element).
- **SC-002**: Users can complete the full emergency planning process (nine AIDR steps) for a standard regional plan within 5 working days using platform guidance.
- **SC-003**: Recovery programs configured with M&E frameworks track outcomes from at least 3 of the 4 recovery domains, each with measurable indicators from the AIDR catalogue.
- **SC-004**: Program logic models created in the platform correctly represent the AIDR structure: resources → activities → outputs → intermediate outcomes → final outcomes, with sustainability and resilience outcomes distinguished.
- **SC-005**: 90% of scheduled indicator data collection events are completed on time across active recovery programs.
- **SC-006**: AI-assisted cross-domain analysis correctly identifies at least 80% of known indicator correlations in test scenarios with planted cross-domain dependencies.
- **SC-007**: Community-facing recovery status reports are rated as "clear and understandable" by 85% of test readers from non-specialist backgrounds.
- **SC-008**: Emergency plans activated during incidents surface all relevant plan content (roles, resources, arrangements) within 10 seconds of activation.
- **SC-009**: Evaluation reports generated from M&E data address all five key evaluation question domains with evidence-based findings.
- **SC-010**: The Constitution's AIDR Handbook Collection Reference table includes all three new handbooks within 7 days of this specification's approval.

## Clarifications

### Session 2026-04-13

- Q: What are the formal lifecycle states for an Emergency Plan? → A: Draft → InConsultation → UnderReview → Endorsed → Activated → PostEventReview → Superseded, matching the AIDR 9-step planning process.
- Q: Should emergency planning be a new agent or extend an existing one, and where does M&E live? → A: Create a new `planning` agent (AIIMS Planning function); extend the existing `monitoring` agent with M&E and indicator tracking capabilities.
- Q: How is the AIDR outcomes/activities/indicators catalogue loaded into the system? → A: Seeded as immutable reference data at deployment from parsed handbook content into Cosmos DB; user-defined extensions stored separately.
- Q: What authorization model governs emergency plan access and activation? → A: AIIMS role-based — Planning Officer creates/edits plans, Incident Controller activates, endorsement requires designated authority per plan hierarchy level.
- Q: What is the canonical term for the four recovery groupings: "domain" or "environment"? → A: "Recovery domain" is the canonical spec term (aligning with AIDR M&E Framework Tables 2–6); existing code type alias `RecoveryEnvironment` retained for backward compatibility.

### Session 2026-04-13 (Pass 2 — Cross-Spec Consistency & Data Model)

- Q: SC-001 says "26 required AIDR plan elements" but the Emergency Planning Handbook Chapter 3 lists 27 elements including "Contents, abbreviations and glossary" — which count is correct? → A: The handbook lists 27 elements. FR-002 and SC-001 updated to 27 to include the structural element "Contents, abbreviations and glossary" for full AIDR compliance.
- Q: How does the "Overarching (Resilience & Sustainability)" fifth domain map to the existing four-value `RecoveryEnvironment` type system? → A: New `RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]` type for catalogue entities (RecoveryOutcome, CatalogueActivity, CatalogueIndicator). Existing `RecoveryEnvironment` (4 values) retained for spec 018 backward compatibility. Overarching outcome indicators roll up into the relevant concrete domain tracker(s).
- Q: What is the AIDR catalogue data model — ID scheme, Cosmos DB container, relationship to existing RecoveryIndicator, and catalogue scale? → A: Hierarchical IDs: `aidr:{domain}:{outcome-slug}` for outcomes, `:act:{index}` suffix for activities, `:ind:{index}` for indicators. Single Cosmos DB container `recovery-catalogue` partitioned by `domain`. Existing `RecoveryIndicator` gains optional `catalogue_indicator_id` FK. Catalogue scale: ~61 outcomes, ~200 activities, ~300 indicators across 5 domains.
- Q: What are the valid Emergency Plan lifecycle state transitions and which AIIMS role authorizes each? → A: Draft→InConsultation (Planning Officer), InConsultation→UnderReview (Planning Officer), InConsultation→Draft (Planning Officer, major rework), UnderReview→Endorsed (Designated Authority), UnderReview→Draft (Designated Authority rejects), Endorsed→Activated (Incident Controller, live incident only), Activated→PostEventReview (IC or Planning Officer, post-incident), PostEventReview→Draft (Planning Officer, new version; original→Superseded), Any non-terminal→Superseded (system-triggered on new version endorsed). No other transitions permitted; Superseded is terminal.
- Q: Do the five M&E evaluation question domains (KEQ) drive separate data collection subsystems or only structure evaluation reporting? → A: KEQ domains are evaluation structuring dimensions only — they shape report sections and analysis, not indicator data collection. M&EFramework stores `active_evaluation_domains: list[EvaluationDomain]` where `EvaluationDomain = Literal["governance", "community_engagement", "effectiveness", "efficiency", "implementation"]`. Standard evaluation questions per domain are seeded as reference data from AIDR M&E Framework §5.2.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-049**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-050**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-051** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-017**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-017.md` (created in feature 028 polish).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-055** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (resilience-planner, product-owner-ba) sign off on country-specific calibration.
- **SCP-056**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-057**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.

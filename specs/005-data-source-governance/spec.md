# Feature Specification: Data Source Identification, Constitutional Review, and Governance Assignment

**Feature Branch**: `005-data-source-governance`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Identify all potential sources of data for the solution; whether they are from a government organisation or from social media. For each of these sources, they need to be reviewed against the Constitution, and the responsibility of governance and co-ordination defined (e.g., which agent is responsible, and how the handoffs are defined.)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catalogue all data sources that feed the hub (Priority: P1)

A preparedness planner or system administrator opens the data source registry and sees every data source the hub depends on, organised by category (government authoritative, sensor/IoT, social media, community, field report, derived). Each entry shows the source name, owning organisation, data type, expected update frequency, geographic coverage, and trust tier. The planner can add, update, or deactivate sources and verify the catalogue is complete before an incident season.

**Why this priority**: Without a comprehensive and reviewable catalogue of data sources, the system cannot demonstrate that it has identified all inputs, which is the foundational requirement of this feature.

**Independent Test**: Can be fully tested by loading the catalogue, verifying that all known Australian disaster-relevant data sources are listed with complete metadata, and confirming a planner can add a new source and see it reflected immediately.

**Acceptance Scenarios**:

1. **Given** the data source registry exists, **When** a planner opens it, **Then** every registered data source is displayed with its name, category, owning organisation, data type, update frequency, geographic coverage, and trust tier.
2. **Given** a planner identifies a new data source not yet in the registry, **When** they add it with the required metadata, **Then** the system persists the entry and it appears in the catalogue immediately.
3. **Given** a data source becomes permanently unavailable, **When** a planner deactivates it, **Then** the system marks it as deactivated, retains its history, and excludes it from active ingestion.
4. **Given** the catalogue is loaded, **When** a planner filters by category (e.g., "government authoritative" or "social media"), **Then** only matching sources are shown.

---

### User Story 2 - Review each data source against the Constitution (Priority: P2)

A governance lead or safety lead opens the constitutional compliance view for any data source and sees a structured assessment of how that source aligns with each relevant constitutional principle (Life Safety First, Multi-Agent Coordination, Data Trust and Provenance, Privacy and Security, Multilingual Communication, and Cloud Platform). Each assessment shows the principle, the compliance status (compliant, partially compliant, non-compliant, not applicable), an explanation, and any conditions or mitigations required. The lead can approve, flag for remediation, or reject a data source based on its compliance profile.

**Why this priority**: The Constitution is the supreme governance document for this project. Reviewing each data source against it ensures that no source enters the system without meeting life-safety, provenance, privacy, and operational standards.

**Independent Test**: Can be tested by selecting any registered data source, viewing its constitutional compliance assessment, verifying that every relevant principle is addressed, and confirming that a governance lead can record an approval or flag a remediation.

**Acceptance Scenarios**:

1. **Given** a data source is registered, **When** a governance lead opens its compliance view, **Then** the system displays an assessment against each relevant constitutional principle with status, explanation, and conditions.
2. **Given** a data source is assessed as partially compliant on Data Trust and Provenance, **When** the governance lead reviews the assessment, **Then** the system shows the specific gaps (e.g., missing freshness metadata, no contradiction detection) and required mitigations.
3. **Given** a governance lead approves a data source with conditions, **When** the approval is saved, **Then** the system records the approval, the conditions, the approving user, and the date, and the source is marked as conditionally approved.
4. **Given** a data source is marked non-compliant on Privacy and Security, **When** the governance lead rejects it, **Then** the system prevents the source from being used in active ingestion until remediation is completed and re-reviewed.

---

### User Story 3 - Assign agent governance and define handoffs for each data source (Priority: P3)

A system architect or preparedness planner opens the governance assignment view for a data source and assigns the responsible agent (Monitoring, Risk Assessment, Evacuation, Resource Allocation, or Communication), defines the handoff chain for data flowing from that source, and specifies coordination rules (e.g., which downstream agents receive signals from this source, under what conditions, and with what confidence thresholds). The assignment is validated against the existing agent architecture and handoff contracts.

**Why this priority**: Defining which agent is responsible for each data source and how handoffs flow is essential for operational clarity, auditability, and avoiding gaps or duplicated processing.

**Independent Test**: Can be tested by assigning an agent to a data source, defining the handoff chain, and verifying that the system validates the assignment against known agent contracts and displays the complete governance chain for that source.

**Acceptance Scenarios**:

1. **Given** a registered and constitutionally approved data source, **When** an architect assigns the Monitoring Agent as the responsible ingestion agent, **Then** the system records the assignment and displays the agent's responsibilities for that source.
2. **Given** a data source is assigned to the Monitoring Agent, **When** the architect defines the handoff chain (e.g., Monitoring → Risk Assessment → Evacuation), **Then** the system validates that each handoff target is a recognised agent and that the handoff payload contract is compatible.
3. **Given** a handoff includes a confidence threshold (e.g., signals with confidence ≥ 0.8 are forwarded to Risk Assessment), **When** the threshold is configured, **Then** the system records the threshold and uses it to filter handoffs during operation.
4. **Given** an agent governance assignment is complete, **When** a planner views the full governance map, **Then** the system shows all data sources, their responsible agents, handoff chains, confidence thresholds, and any gaps where sources lack assignments.

---

### User Story 4 - View a consolidated data source governance dashboard (Priority: P4)

An incident commander, executive, or auditor opens the data source governance dashboard and sees a single-page summary of all data sources, their constitutional compliance status, assigned agents, handoff chains, and any outstanding issues (unreviewed sources, non-compliant sources, sources without agent assignments). The dashboard supports filtering by compliance status, agent, category, and geographic coverage.

**Why this priority**: A consolidated view provides operational assurance that all data sources are governed, compliant, and assigned before and during incidents.

**Independent Test**: Can be tested by loading the dashboard with a mix of compliant, non-compliant, assigned, and unassigned data sources and verifying that totals, filters, and drill-downs work correctly.

**Acceptance Scenarios**:

1. **Given** the registry contains data sources in various states, **When** an executive opens the governance dashboard, **Then** summary counts are displayed for total sources, compliant, partially compliant, non-compliant, assigned, and unassigned.
2. **Given** the dashboard is open, **When** the user filters by "non-compliant", **Then** only data sources with at least one non-compliant constitutional assessment are shown.
3. **Given** a data source has no agent assignment, **When** the dashboard highlights governance gaps, **Then** the source is flagged with a clear indicator and appears in the "unassigned" filter.

---

### Edge Cases

- A data source provides data relevant to multiple agents (e.g., Bureau of Meteorology warnings are used by Monitoring and Risk Assessment); the governance model must support shared responsibility without ambiguity.
- A data source changes its data format, availability, or terms of use after initial constitutional review; the system must support re-review workflows.
- A social media source is identified as carrying both valuable community intelligence and significant misinformation risk; the constitutional review must capture both aspects and define mitigations.
- A government data source is available nationally but has different access terms or data formats by state or territory; governance must account for jurisdictional variations.
- An IoT sensor network is operated by a private organisation with no formal agreement with participating agencies; the constitutional review must flag privacy and data-sharing concerns.
- Two data sources provide contradictory information for the same hazard type and location; the system resolves precedence using functional-domain authority per jurisdiction (e.g., BoM for weather, state fire services for fire), falling back to trust tier when domain authority is equal.

## Clarifications

### Session 2026-03-24

- Q: Should this feature's scope include agent modifications so agents read handoff routing rules from the governance registry at runtime, given the monitoring agent currently has hardcoded categories, thresholds, and targets? → A: Partially (Option B, refined). The governance registry will expose handoff chain definitions in a structured, queryable format. Agent-side refactoring to consume those definitions is a downstream dependency, not a deliverable of this spec.
- Q: Should the data source categorisation model use a two-level structure (kind + sub-category) or a single expanded enum? → A: Two-level (Option A). Retain the existing `kind` field for coarse category and add a `sub_category` field for granular classification (e.g., kind=`authoritative`, sub_category=`weather_climate`).
- Q: When two data sources of the same trust tier provide contradictory signals, how should precedence be determined? → A: Functional-domain precedence per jurisdiction (Option B). The governance registry records which source is authoritative for each hazard type within each jurisdiction (e.g., BoM is primary for weather nationally, RFS is primary for fire in NSW).
- Q: Should this feature produce an enumerated seed catalogue of specific named Australian data sources as a deliverable? → A: Yes (Option A). The spec will include a seed catalogue of named Australian data sources covering government, sensor, social, and community sources for bushfire, flood, cyclone, and severe storm scenarios. This catalogue provides the denominator for SC-001.
- Q: Should the seed catalogue be delivered as a structured, machine-loadable data file or as documentation-only content? → A: Structured data file (Option A). The seed catalogue will be delivered as a machine-loadable file (JSON or YAML) in `packages/domain` seed data, enabling programmatic import, deterministic testing, and automated SC-001 measurement.
- Q: When a previously approved and assigned data source fails re-review (FR-012), should it be immediately blocked from ingestion or allowed to continue with a warning? → A: Grace period with warning (Option B). The source continues operating with a visible "compliance lapsed" warning on the governance dashboard; a configurable grace period applies before automatic blocking. This prevents abrupt removal of critical data feeds during active incidents.
- Q: Should the spec require structured observability signals for governance-registry operations? → A: Yes. The governance registry must emit structured logging and metrics (query latency, cache hit/miss rate, governance-gap counts) that integrate with the existing hub monitoring infrastructure.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a data source registry that catalogues every external and internal data source used by the hub, including government authoritative feeds, sensor and IoT networks, social media channels, community reporting platforms, field report inputs, and derived or computed sources.
- **FR-001a**: The feature MUST deliver an enumerated seed catalogue of named Australian data sources applicable to bushfire, flood, cyclone, and severe storm scenarios. The seed catalogue MUST be delivered as a structured, machine-loadable data file (JSON or YAML) within `packages/domain` seed data, consistent with the existing seed data pattern. The file MUST be programmatically importable into the data source registry to enable automated bootstrapping, deterministic integration testing, and programmatic SC-001 measurement. The spec prose below summarises the minimum content; the structured file is the source of truth. The seed catalogue MUST include at minimum the following named sources organised by category:
  - **Government Authoritative — Weather & Climate**: Bureau of Meteorology (BoM) warnings, forecasts, radar, and observations
  - **Government Authoritative — Geohazard**: Geoscience Australia earthquake alerts, tsunami warnings, and sentinel hotspot data
  - **Government Authoritative — Fire**: NSW Rural Fire Service (RFS) Fires Near Me, CFA (VIC), QFES (QLD), CFS (SA), DFES (WA), TFS (TAS), ACTESA, NTPFES
  - **Government Authoritative — Flood**: Bureau of Meteorology flood warnings, state SES flood intelligence (NSW SES, VIC SES, QLD SES)
  - **Government Authoritative — Emergency Management**: Emergency Management Australia (EMA), state/territory emergency management agencies, Australian Institute for Disaster Resilience (AIDR)
  - **Government Authoritative — Health**: State/territory health departments for public health advisories during disasters
  - **Government Authoritative — Transport & Infrastructure**: State road authorities (Transport for NSW, VicRoads, TMR QLD), infrastructure status feeds
  - **Government Authoritative — Utilities**: Energy network operators, water authorities (jurisdictional)
  - **Sensor & IoT**: Weather station networks (BoM AWS), river gauge networks (BoM/state), bushfire smoke/air quality sensors (state EPAs), satellite imagery (Sentinel, Himawari-8/9)
  - **Social Media**: X/Twitter (disaster hashtags and emergency accounts), Facebook (community groups and official pages), Reddit (Australian subreddits during events)
  - **Community & Volunteer**: Volunteer rescue organisations (e.g., Surf Life Saving, volunteer bushfire brigades), community reporting platforms (e.g., Snap Send Solve, local council apps)
  - **Field Reports**: Agency field officer reports, incident management system feeds (e.g., ICON, WebEOC)
  - **Derived/Computed**: Internal agent-generated assessments, aggregated risk scores, historical incident databases
- **FR-002**: Each data source entry MUST include: unique identifier, name, primary category (`kind`: authoritative, sensor, IoT, field_report, social, community, derived), sub-category for granular classification (e.g., `weather_climate`, `geohazard`, `emergency_services`, `health`, `transport_infrastructure`, `utilities`, `gov_commonwealth`, `gov_state`, `gov_territory`, `gov_local`), owning or providing organisation, data type, expected update frequency, geographic coverage, trust tier, and operational status.
- **FR-002a**: Trust tier MUST be a discrete classification assigned to each data source, with the following defined values and semantics:
  - **Tier 1 — Authoritative Government**: Official government sources mandated by legislation or regulation as the authoritative source for a domain (e.g., Bureau of Meteorology for weather warnings, Geoscience Australia for earthquake alerts). Maps to `authority_rank` 1.
  - **Tier 2 — Verified Institutional**: Government or institutional sources that are reliable and officially published but not the sole legislated authority (e.g., state health department advisories, transport authority road status). Maps to `authority_rank` 2.
  - **Tier 3 — Operational Sensor/IoT**: Sensor networks and IoT feeds with known operators and calibration standards (e.g., BoM automatic weather stations, river gauges, EPA air quality sensors). Maps to `authority_rank` 3.
  - **Tier 4 — Field Reports**: Reports from trained field personnel using established reporting protocols (e.g., agency field officer reports, WebEOC/ICON feeds). Maps to `authority_rank` 4.
  - **Tier 5 — Community/Volunteer**: Reports from community organisations, volunteer groups, and community platforms with some organisational accountability (e.g., Surf Life Saving, volunteer bushfire brigades). Maps to `authority_rank` 5.
  - **Tier 6 — Social Media/Unverified**: Crowd-sourced and social media inputs with no formal accountability or verification (e.g., Twitter/X disaster hashtags, Reddit threads). Maps to `authority_rank` 6.
  - **Tier 7 — Derived/Computed**: Internally generated assessments and aggregated outputs whose trust depends on the trust of their input sources. Maps to `authority_rank` 7; effective trust tier is bounded by the lowest-tier input source.
  Trust tier is recorded as the `trust_tier` field on the DataSourceRegistryEntry and is mapped to the existing `authority_rank` integer field on the DataSource model for backward compatibility.
- **FR-003**: The system MUST support a two-level categorisation: the primary `kind` field uses the existing values (authoritative, sensor, IoT, field_report, social, community, derived) and a `sub_category` field provides granular classification within each kind (e.g., weather_climate, geohazard, emergency_services, health, transport_infrastructure, utilities, gov_commonwealth, gov_state, gov_territory, gov_local). Filtering MUST be supported at both levels.
- **FR-004**: The system MUST provide a constitutional compliance assessment for each data source, evaluating it against each relevant principle in the project Constitution: Life Safety First, Multi-Agent Coordination, Data Trust Provenance and Freshness, Privacy Security and Regional Policy Compliance, Multilingual Accessible and Actionable Communication, and Cloud Platform.
- **FR-004a**: The system MUST present assessors with principle-specific assessment criteria to ensure consistent evaluations across assessors and data sources. At minimum, criteria MUST address:
  - **Life Safety First**: Does the source provide data used in safety-critical decisions (evacuation, alerts)? Is the source reliable enough for life-safety use? Are there failure modes that could endanger life if the source provides incorrect data?
  - **Multi-Agent Coordination**: Which agents consume this source? Are handoff boundaries clear? Could ambiguous ownership cause gaps or duplicated processing?
  - **Data Trust, Provenance & Freshness**: Does the source provide provenance metadata (origin, collection method, timestamp)? Is the source authoritative or unverified? What is the expected freshness and how is staleness detected? Can contradictory signals from this source be identified?
  - **Privacy, Security & Regional Policy Compliance**: Does the source contain or transmit PII or sensitive location data? Does the source require data-sharing agreements? Does it comply with Australian Privacy Principles? Are there jurisdictional data residency requirements?
  - **Multilingual, Accessible & Actionable Communication**: Does the source provide content that will be used in public alerts? If so, does the content support multilingual requirements or require translation?
  - **Cloud Platform**: Does the source require connectivity to systems outside Australian Azure regions? Are there data residency constraints that affect ingestion architecture?
- **FR-005**: Each constitutional assessment MUST record the principle, compliance status (compliant, partially compliant, non-compliant, not applicable), explanation, required conditions or mitigations, assessor identity, and assessment date.
- **FR-006**: The system MUST prevent a data source marked as non-compliant on any constitutional principle from being used in active ingestion until remediation is completed and a new assessment records compliance or conditional compliance.
- **FR-007**: The system MUST allow authorised users to assign a primary responsible agent to each data source from the set of recognised agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication).
- **FR-008**: The system MUST allow authorised users to define the handoff chain for each data source, specifying the sequence of agents that process signals from that source, the handoff payload expectations, and any confidence or category thresholds that gate forwarding.
- **FR-009**: The system MUST validate agent governance assignments against the known agent architecture, ensuring that assigned agents exist, handoff targets are valid, and payload contracts are compatible.
- **FR-009a**: The governance registry MUST expose handoff chain definitions (target agents, confidence thresholds, category filters) in a structured format that agents can query at runtime, so that routing decisions are driven by governance data rather than hardcoded logic.
- **FR-009b**: Agent refactoring to consume governance-defined routing rules (replacing hardcoded category sets, confidence thresholds, and target agent references in agents such as the Monitoring Agent) is a downstream dependency of this feature. This spec defines the governance data and query contract; the agent runtime changes are tracked separately and are not a deliverable of this spec.
- **FR-009c**: The set of recognised agent names used in governance assignments (FR-007) and handoff chain definitions (FR-008) MUST be validated against the agent catalogue maintained by spec 004 (Actor-Specific GitHub Agents). If the agent catalogue adds, removes, or renames an agent, the governance registry MUST detect and flag any assignments or handoff chains that reference an unrecognised agent name. The system MUST NOT allow governance assignments to agents that do not exist in the current agent catalogue.
- **FR-010**: The system MUST support data sources that serve multiple agents, recording shared responsibilities and defining precedence or coordination rules to avoid ambiguity.
- **FR-010a**: The governance registry MUST record functional-domain precedence for data sources using a hierarchical inheritance model: a national-level default specifies which source is authoritative for each hazard type nationally (e.g., Bureau of Meteorology for weather, Geoscience Australia for geohazards). State/territory-level overrides MAY be recorded where a different source has jurisdictional authority for a specific hazard type (e.g., NSW RFS for fire ground truth in NSW). When resolving precedence, the system MUST check for a jurisdiction-specific override first, then fall back to the national default. This inheritance model avoids the need to enumerate every source × hazard × jurisdiction combination. When two sources of equal trust tier provide contradictory signals and no functional-domain precedence record exists, the system MUST flag the conflict for human resolution rather than silently choosing one source.
- **FR-011**: The system MUST provide a consolidated governance dashboard showing all data sources with their compliance status, agent assignments, handoff chains, and outstanding governance gaps.
- **FR-012**: The system MUST support re-review workflows when a data source's characteristics change (format, availability, terms of use, provider organisation), triggering a new constitutional assessment cycle.
- **FR-012a**: The system MUST support re-review workflows triggered by changes to the Constitution itself. When the Constitution is amended (e.g., a new principle is added, an existing principle is modified, or assessment criteria change), all existing constitutional assessments MUST be flagged as requiring re-evaluation against the amended principles. The governance dashboard (FR-011) MUST surface the count of assessments requiring re-evaluation due to constitutional amendments.
- **FR-012b**: When a previously approved and operationally assigned data source fails re-review (triggered by FR-012 or FR-012a), the system MUST NOT immediately block the source from ingestion. Instead, the system MUST mark the source as "compliance lapsed", display a visible warning on the governance dashboard, and start a configurable grace period (default: 72 hours). During the grace period, the source continues operating normally but governance leads receive notifications to remediate or explicitly revoke the source. If the grace period expires without remediation or explicit extension by an authorised governance lead, the system MUST automatically block the source from active ingestion per FR-006. An authorised governance lead MAY override the grace period to immediately block or extend it based on operational circumstances (e.g., active incident).
- **FR-013**: The system MUST record an audit trail of all governance actions: source registration, constitutional assessments, approvals, rejections, agent assignments, handoff definitions, and re-reviews.
- **FR-014**: The system MUST identify and flag governance gaps where a data source is registered but lacks a constitutional assessment, or has been assessed but lacks an agent assignment.

### Non-Functional Requirements

- **NFR-001**: The governance registry MUST support read queries with latency suitable for agent handoff decisions (target: ≤ 50 ms at the 95th percentile for a single handoff-chain lookup) so that governance-driven routing does not degrade signal processing throughput.
- **NFR-002**: Agents MUST be able to cache governance-registry data locally (handoff chains, confidence thresholds, category filters) with a configurable cache TTL (default: 5 minutes). Agents MUST continue operating with cached data if the governance registry is temporarily unreachable.
- **NFR-003**: If the governance registry is unreachable and no cached data is available, agents MUST fall back to safe default routing behaviour (as defined per agent) and log a warning. The system MUST NOT halt signal processing due to governance-registry unavailability.
- **NFR-004**: The governance registry MUST support the same availability and resilience guarantees as other hub components, consistent with the Constitution's requirement for resilience to partial outages during disasters.
- **NFR-005**: The governance registry MUST emit structured observability signals that integrate with the existing hub monitoring infrastructure. At minimum, signals MUST include: registry query latency (per-query timing for handoff-chain lookups), cache hit/miss rate (for agent-side governance-data caches per NFR-002), governance-gap counts (number of sources missing assessments or assignments, updated on each registry mutation), grace-period expiry warnings (for sources in "compliance lapsed" state per FR-012b approaching automatic block), and audit-trail write failures (any failure to persist a GovernanceAuditEntry per FR-013).

### Security & Access Control

- **FR-015**: Access to the governance registry MUST be role-based. Only authorised governance leads, safety leads, and system architects MAY create, modify, or approve constitutional assessments and agent assignments. Read access to the governance dashboard MAY be granted to broader operational roles (incident commanders, executives, auditors) as defined by the organisation's access policy.
- **FR-016**: The governance registry itself MUST be treated as a sensitive asset. The registry contains data source vulnerability assessments, compliance gaps, and routing configuration that could be exploited if exposed. Access controls, audit logging (FR-013), and data classification consistent with the Constitution's privacy and security requirements (Principle IV) MUST apply to all governance data.

### Key Entities

- **DataSourceRegistryEntry**: A catalogued data source with its metadata (name, primary `kind`, `sub_category` for granular classification, provider, data type, frequency, coverage, trust tier, status), constitutional compliance profile, and agent governance assignments. Extends the existing DataSource model with governance-specific attributes; the existing `kind` field is retained as the coarse category and a new `sub_category` field is added. **Source of truth note**: The current DataSource implementation (`packages/domain/src/domain/models/data_source.py`) has 5 fields (`data_source_id`, `name`, `kind`, `authority_rank`, `status`). The spec 001 data model describes additional fields (`provider`, `collectionMethod`) not yet implemented. This spec adds further governance fields (`sub_category`, `trust_tier`, `update_frequency`, `geographic_coverage`, compliance profile, agent assignments). During planning, the implementation task list MUST reconcile these three definitions into a single authoritative model, using the spec 001 data model as the baseline and this spec's extensions as additive.
- **ConstitutionalAssessment**: A structured review of a single data source against one constitutional principle, recording the principle reference, compliance status, explanation, conditions, assessor, and date. Multiple assessments form the compliance profile for a source.
- **AgentGovernanceAssignment**: The assignment of a responsible agent to a data source, including the agent name, role (primary or secondary), scope of responsibility, and any operational conditions.
- **HandoffChainDefinition**: The defined sequence of agent-to-agent handoffs for signals originating from a data source, including each step's source agent, target agent, confidence threshold, category filter, and payload contract reference.
- **GovernanceAuditEntry**: An immutable record of a governance action (registration, assessment, approval, rejection, assignment, re-review) with actor, timestamp, and details.

### Assumptions

- The set of constitutional principles to assess against is defined in the existing Constitution document (v1.0.1). If the Constitution is amended, FR-012a requires all existing assessments to be flagged for re-evaluation against the amended principles.
- The initial catalogue of data sources will be populated from the seed catalogue defined in FR-001a, covering named Australian disaster-response data providers across government, sensor, social, community, field, and derived categories. The seed catalogue is extensible as new sources are identified.
- The agent architecture (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) is stable for the purpose of governance assignment. New agents would require governance model extension.
- Existing agents (particularly the Monitoring Agent) have hardcoded handoff routing (static category sets, confidence thresholds, target agent references) that should be replaced with governance-registry lookups. This spec delivers the governance data and query contract; agent-side refactoring to consume that data is a separate downstream work item.
- Constitutional assessments are performed by authorised governance or safety leads, not automated. The system facilitates the assessment but does not make compliance judgements autonomously.
- Trust tiers are defined in FR-002a as a 7-level classification (Authoritative Government through Derived/Computed) that maps to the existing `authority_rank` integer field on the DataSource model. Trust tier assignment is part of the governance workflow and may be adjusted during constitutional assessment.

### Out of Scope

- Automated constitutional compliance scoring (assessments are human-led and recorded in the system).
- Negotiation of data-sharing agreements with external organisations.
- New real-time ingestion connectors to external data providers (connector implementation remains in spec 001; this feature governs which sources are approved and how their signals are routed).
- Modification of the Constitution itself (governed by the separate constitutional amendment process).
- Changes to agent business logic beyond handoff routing (e.g., risk scoring algorithms, alert drafting templates); only the routing and threshold lookup mechanism is in scope.
- Agent runtime refactoring to consume governance-registry data (e.g., modifying the Monitoring Agent to replace hardcoded routing with registry lookups). This spec defines the governance data and query contract; agent code changes are a downstream dependency tracked separately.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The data source registry contains entries for at least 90% of the sources listed in the seed catalogue (FR-001a), as validated by a subject-matter review panel. The seed catalogue serves as the denominator for this measurement.
- **SC-002**: Every registered data source has a completed constitutional compliance assessment covering all applicable principles, with zero sources left in an unassessed state before the system enters operational readiness.
- **SC-003**: Every constitutionally approved data source has a defined agent governance assignment and at least one handoff chain, with zero governance gaps flagged on the consolidated dashboard at operational readiness.
- **SC-004**: Authorised users can complete the full governance workflow for a new data source (registration, constitutional assessment, agent assignment, handoff definition) in under 30 minutes.
- **SC-005**: The governance dashboard accurately reflects the current state of all data sources, and 90% of tested users can identify governance gaps within 2 minutes of opening the dashboard.
- **SC-006**: All governance actions are captured in the audit trail with no gaps, verified by replaying the audit log against the current registry state.

## Assumptions

Scoped to this spec's domain (per-country PII / data-source classification). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-007**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-008** [DECISION]: This spec's deliverables (per-country PII / data-source classification) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`). The compliance-auditor, security-engineer, and product-owner-ba roles identify the required review scope. Agent/tool invocations do not count as human consultation or approval; a revision-bound review record is required before claiming either. `status:` unverified.
- **ASM-009**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.
- **ASM-010** [RISK]: AU-only data residency (constitution NON-NEGOTIABLE #2; Azure `australiaeast` / `australiasoutheast` only) is in tension with the capstone Asia framing (PH / JP / BD sovereign-data handling). Resolution requires a constitution-level amendment owned outside this feature (see `specs/028-capstone-alignment/research.md` D-009). `linked_gaps:` constitution NON-NEGOTIABLE #2. `status:` Open.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 persona validation is unverified for this feature; PH / JP / BD entries remain explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-007**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` unverified. `preconditions:` feature-scoped practitioner validation with a dated revision-bound record.
- **PER-008**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` unverified. `preconditions:` feature-scoped workflow/usability review with a dated revision-bound record.
- **PER-009** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-043**: If this spec records per-change governance consultation and rehearsal evidence with named reviewers and dated revision links, then the next per-spec readiness review will report zero unsupported approval claims for this feature revision window. **Falsification**: at least two unsupported approval claims within one review cycle. **Evidence stub**: `specs/005-data-source-governance/evidence/HYP-043.md`. **Status**: Not tested. This owner-scoped hypothesis replaces the historical, malformed HYP-003 cross-reference; portfolio rubric snapshots do not establish its outcome.

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-009** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (compliance-auditor, security-engineer, product-owner-ba) sign off on country-specific calibration.
- **SCP-010**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-011**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.


## Capstone-Aligned Requirements (Feature 028 / FR-007)

The capabilities below are deferred-scope; AU-v1 today only. Promotion requires per-regime data-protection authority approval and constitution amendment per D-009.

- **FR-CAP-005-001** [DEFERRED]: Per-country PII classification covering: AU **Privacy Act 1988 (Cth) + Australian Privacy Principles (APPs)** (status: in-scope, AU-v1); JP **Act on the Protection of Personal Information (APPI) 2017 / 2020 amendments** (status: deferred); PH **RA 10173 Data Privacy Act 2012 + NPC Circulars** (status: deferred); BD **ICT Act 2006 + draft Data Protection Act 2023** (status: deferred). Each non-AU regime is gated by an MoU + DPIA + data-residency lawful basis precondition. `defers-to:` future capstone-reinterpretation feature.
- **FR-CAP-005-002** [DEFERRED]: Cross-border data-transfer rules (where lawful) follow the strictest regime applicable to the data subject's locus and the data-storage region; default is to **forbid** transfer until the per-country regime is gated active. `defers-to:` 028.

# AIDR Guidance Integration — Requirements Quality Checklist

**Purpose**: Validate the completeness, clarity, consistency, and measurability of all AIDR guidance integration requirements across 8 domains (54 FRs, 15 NFRs, 10 SCs). Elevated scrutiny (P1) for life-safety domains: Australian Warning System, AIIMS alignment, and evacuation. Includes cross-spec consistency checks for specs 001, 008, 009, 010, 011, 012.  
**Created**: 2025-07-20  
**Feature**: [spec.md](../spec.md)  
**Constitution**: [constitution.md](../../../.specify/memory/constitution.md) v1.1.0  
**Depth**: Elevated (P1 life-safety) · Standard (P2/P3)  
**Audience**: Reviewer (PR / spec review gate)

---

## P1 Life-Safety: Australian Warning System (AWS) — Requirement Completeness

- [ ] CHK001 — Are all three AWS tiers explicitly defined with distinct visual identifiers (label, colour code) and is the mapping exhaustive with no unlisted tiers? [Completeness, Spec §FR-001]
- [ ] CHK002 — Is the AWS nested model (Warning Level + Hazard/Location + Action Statement) fully specified for every tier, including what constitutes a valid "Action Statement" for each severity? [Completeness, Spec §FR-002]
- [ ] CHK003 — Are all six hazard icon types (cyclone, fire, flood, heat, storm, other) enumerated, and is the criteria for selecting "other" defined? [Completeness, Spec §FR-003]
- [ ] CHK004 — Are de-escalation notice requirements specified with the same structural rigour as escalation — including which prior warning fields must be referenced and what "clearly referencing" entails? [Completeness, Spec §FR-004]
- [ ] CHK005 — Are all-clear notification requirements defined, including what conditions constitute incident "resolution" and what it means to "close the warning chain"? [Completeness, Spec §FR-005]
- [ ] CHK006 — Are requirements specified for every one of the ten warning principles, or are they listed only as a collective reference without individual operationalisation? [Completeness, Spec §FR-006]
- [ ] CHK007 — Are vulnerable-population accessibility requirements (FR-007) enumerated for each group — CALD translation, disability-accessible formats, pregnant women, health needs, pets/assistance animals — or do they remain a collective list without per-group specifics? [Completeness, Spec §FR-007]
- [ ] CHK008 — Are requirements defined for what happens when a warning is issued but the underlying hazard data is stale or unavailable? [Gap, Graceful Degradation]

## P1 Life-Safety: Australian Warning System (AWS) — Requirement Clarity

- [ ] CHK009 — Is "graphical output is supported" (FR-003) defined with specific criteria for determining when graphical output is or is not available, and what the fallback is? [Clarity, Spec §FR-003]
- [ ] CHK010 — Is the "warning chain" concept (FR-005) precisely defined — how individual warnings are linked, how supersession is tracked via `superseded_warning_id`, and whether a chain can branch? [Clarity, Spec §FR-005]
- [ ] CHK011 — Is "life-saving" (warning principle 1) operationalised beyond a restatement of the principle — i.e., what measurable property makes a warning life-saving? [Clarity, Spec §FR-006]
- [ ] CHK012 — Is "part of a bigger picture" (warning principle 10) quantified — what contextual information must be included to satisfy this principle? [Clarity, Spec §FR-006]
- [ ] CHK013 — Is "translated content" for CALD communities (FR-007) specified with scope — which languages, what translation quality standard, human vs. machine translation? [Clarity, Spec §FR-007]
- [ ] CHK014 — Is the 5-minute Emergency Warning escalation timeout (clarification §IC unavailability) specified with unambiguous trigger conditions — does the timer start at submission, at first failed contact attempt, or at another event? [Clarity, Edge Case §IC unavailable]

## P1 Life-Safety: Australian Warning System (AWS) — Scenario & Edge Case Coverage

- [ ] CHK015 — Are requirements for simultaneous multi-hazard warnings in overlapping geographic areas complete — including COP display, independent warning chains, and potential user confusion mitigation? [Coverage, Edge Cases]
- [ ] CHK016 — Are tier-skipping requirements for sudden-onset hazards (earthquake, tsunami, structural collapse) specified with the required audit fields (tier-skip justification, hazard type)? [Coverage, Edge Cases]
- [ ] CHK017 — Are requirements defined for a warning that needs to be retracted or corrected after issuance (e.g., false alarm)? [Gap, Exception Flow]
- [ ] CHK018 — Are requirements defined for geographic boundary determination — how the system identifies the warning area for location-based targeting? [Gap, Spec §FR-002]
- [ ] CHK019 — Does the spec define behaviour when the Communication Agent and Incident Controller disagree on the appropriate warning tier? [Gap, Exception Flow]

## P1 Life-Safety: AIIMS Functional Alignment — Requirement Completeness

- [ ] CHK020 — Is the constraint "exactly one AIIMS functional role" (FR-013) fully specified — does it prohibit dual-role assignments, and is behaviour defined when fewer than six agents are available? [Completeness, Spec §FR-013]
- [ ] CHK021 — Are AIIMS role reassignment requirements defined for mid-incident personnel or agent changes? [Gap]
- [ ] CHK022 — Are the distinct COP content requirements specified for each incident level (Level 1 vs. 2 vs. 3), or is the COP treated identically across levels? [Completeness, Spec §FR-014, §FR-016]
- [ ] CHK023 — Are incident-level escalation and de-escalation trigger criteria specified — what objective conditions warrant promotion from Level 1→2→3 or demotion? [Clarity, Spec §FR-015]
- [ ] CHK024 — Are requirements defined for the minimum functional capability at each incident level — e.g., which AIIMS functions must be staffed at Level 1 vs. required full coverage at Level 3? [Gap, Spec §FR-015]

## P1 Life-Safety: AIIMS Functional Alignment — Requirement Clarity

- [ ] CHK025 — Are the boundaries between Command (vertical), Control (horizontal), and Coordination (resource-bringing) precisely delineated in terms of agent communication patterns and decision authority? [Clarity, Spec §FR-017]
- [ ] CHK026 — Is "agents MUST respect" (FR-017) operationalised — what specific behaviours constitute respecting vs. violating these boundaries? [Clarity, Spec §FR-017]
- [ ] CHK027 — Is "integration with the National Coordination Mechanism" (User Story 2, scenario 3) specified with sufficient detail — what data is exchanged, what protocol, what triggers NCM integration? [Clarity, Spec §US-2]
- [ ] CHK028 — Is the `AiimsRoleAssignment` model's relationship to `OperatingFramework` and `FrameworkAssignment` clearly delineated — specifically when each model is consulted and by which agents? [Clarity, Spec §FR-049]

## P1 Life-Safety: Five-Stage Evacuation — Requirement Completeness

- [ ] CHK029 — Are stage-specific outputs defined for every evacuation stage (Decision, Warning, Withdrawal, Shelter, Return), or is the requirement limited to "documented outputs" without enumeration? [Completeness, Spec §FR-018, §SC-003]
- [ ] CHK030 — Are the Decision stage attributes (authority, rationale, type, approach, scope) each defined with valid value sets and are all combinations valid? [Completeness, Spec §FR-019]
- [ ] CHK031 — Are timeframe requirements specified for the Warning stage — what constitutes adequate lead time for pre-warned vs. immediate evacuations? [Gap, Spec §FR-020]
- [ ] CHK032 — Are "real-time progress tracking" metrics for the Withdrawal stage enumerated — what specific data points are tracked (headcount, percentage moved, route status)? [Clarity, Spec §FR-021]
- [ ] CHK033 — Are shelter capacity tracking requirements specified with data model attributes — maximum capacity, current occupancy, welfare categories, accessibility features? [Completeness, Spec §FR-022]
- [ ] CHK034 — Are Return stage "safety-condition validation" criteria defined — who certifies safety, what conditions are checked, and what happens if conditions are not met? [Gap, Spec §FR-023]
- [ ] CHK035 — Are shelter-in-place "ongoing monitoring" requirements specified — what conditions trigger exit from shelter-in-place back to evacuation? [Clarity, Spec §FR-024]

## P1 Life-Safety: Five-Stage Evacuation — Scenario & Edge Case Coverage

- [ ] CHK036 — Are requirements defined for stage re-entry (e.g., Decision re-activation during Withdrawal when routes become impassable) including all valid re-entry transitions? [Coverage, Edge Cases, §SC-003]
- [ ] CHK037 — Are requirements for evacuating populations with pets or assistance animals specific enough — transport allocation, shelter accommodation, reunification? [Coverage, Spec §FR-021]
- [ ] CHK038 — Are requirements defined for partial evacuation failure — what happens when some areas cannot be evacuated and others can? [Gap, Exception Flow]
- [ ] CHK039 — Are requirements specified for concurrent evacuations for different hazard types in overlapping areas? [Gap, Edge Case]
- [ ] CHK040 — Does the spec define coordination requirements between the Evacuation Agent's Warning stage and the Communication Agent's AWS warning generation (FR-020 ↔ FR-001)? [Consistency, Spec §FR-020]

## P2: PPRR Lifecycle — Requirement Completeness & Clarity

- [ ] CHK041 — Are Prevention phase capabilities (FR-028) specific enough — are "hazard risk assessments" and "mitigation-option analysis" defined with inputs, outputs, and agent responsibilities? [Clarity, Spec §FR-028]
- [ ] CHK042 — Are Preparedness phase capabilities (FR-029) — simulation, readiness assessment, pre-positioning, warning testing — each specified with success criteria, or bundled as a list? [Completeness, Spec §FR-029]
- [ ] CHK043 — Is "recovery planning concurrently" during Response (FR-030) specified with what recovery planning activities are expected and which agents perform them? [Clarity, Spec §FR-030]
- [ ] CHK044 — Are "managed transitions" between PPRR phases (FR-031) specified with who authorises the transition, what triggers it, and what "overlap periods" entail operationally? [Clarity, Spec §FR-031]
- [ ] CHK045 — Is the `pprr_phase` field (FR-050) specified as single-valued or multi-valued per incident — given that "overlap periods where multiple phases are active" are required? [Ambiguity, Spec §FR-050, §FR-031]
- [ ] CHK046 — Are Prevention and Preparedness phases specified for region/scenario contexts without active incidents — how is a PPRR phase tracked when no `Incident` record exists? [Gap, Spec §FR-050]

## P2: Community Recovery — Requirement Completeness & Clarity

- [ ] CHK047 — Are all 21 recovery indicators (Social: 7, Built: 5, Economic: 5, Natural: 4) individually defined with measurement methodology, data sources, and update frequency? [Completeness, Spec §FR-032, Key Entities §Recovery Environment Tracker]
- [ ] CHK048 — Is "community-led recovery" (FR-034) operationalised beyond "mechanisms for community input" — are specific interaction patterns, access controls, or governance structures defined? [Clarity, Spec §FR-034]
- [ ] CHK049 — Is "visible to affected communities" (FR-037) specified with access mechanisms, authentication requirements, and presentation format for non-expert users? [Clarity, Spec §FR-037]
- [ ] CHK050 — Are recovery recommendation requirements (FR-033) specified with how alignment to National Recovery Principles is validated — manual annotation, automated check, or both? [Clarity, Spec §FR-033]
- [ ] CHK051 — Are recovery indicator regression detection requirements (edge case) specified with threshold criteria, alerting mechanism, and required response actions? [Completeness, Edge Cases]
- [ ] CHK052 — Is the "managed transition" from Response to Recovery (FR-035, Constitution §VII-C) consistent with PPRR phase transition requirements in FR-031? [Consistency, Spec §FR-035 ↔ §FR-031]

## P2: Total Warning System — Requirement Completeness

- [ ] CHK053 — Are all six Total Warning System elements (situational awareness, monitoring/prediction, message construction, interpretation, communication, community response) specified with distinct requirements, or are some elements conflated? [Completeness, Spec §FR-008]
- [ ] CHK054 — Is the "interpretation" element (FR-011 mentions "interpretation aids") specified beyond translation — does it include plain language, visual aids, audio formats, and sign language? [Completeness, Spec §FR-011]
- [ ] CHK055 — Are "community-response indicators" (FR-012) enumerated beyond the examples (evacuation compliance, shelter utilisation) — what is the minimum set of indicators required? [Clarity, Spec §FR-012]
- [ ] CHK056 — Is the requirement that community-response indicators "may initially be manually entered" (Assumptions) reflected in the functional requirements or only in assumptions? [Consistency, Assumptions vs. §FR-012]

## P3: Lessons Management — Requirement Completeness & Clarity

- [ ] CHK057 — Is "structured template" for lessons capture (FR-038) specified with required fields, or left to implementation? [Clarity, Spec §FR-038]
- [ ] CHK058 — Is "trend analysis" (FR-040) defined with what constitutes a trend — minimum event count, time window, statistical significance threshold? [Clarity, Spec §FR-040]
- [ ] CHK059 — Are quality gate integration requirements (FR-042) specific enough — how does a PR "reference" an originating lesson, and how is the verification automated? [Clarity, Spec §FR-042]
- [ ] CHK060 — Are requirements for the contradictory-lesson edge case (lesson contradicts existing config) specific enough about what "escalated review" means procedurally? [Clarity, Edge Cases]
- [ ] CHK061 — Is the exercise-to-lesson linkage via `scenario_run_id` (FR-052) specified with behaviour when a lesson spans multiple exercises or when `scenario_run_id` is unavailable? [Gap, Spec §FR-052]

## Domain Model Alignment — Requirement Completeness

- [ ] CHK062 — Is the `PublicAlert` extension (FR-048) fully backward-compatible — are existing fields, lifecycle states, and consumers documented as "preserved unchanged"? [Completeness, Spec §FR-048]
- [ ] CHK063 — Are the three independent severity scales (incident severity, hazard assessment severity, AWS tier) explicitly documented as having no automatic mapping — and is the editorial judgment process for tier selection specified? [Clarity, Clarifications §Pass 2]
- [ ] CHK064 — Is the `Incident.incident_type` extension (FR-051) specified with whether the new hazard types are additive or replace existing enum values? [Clarity, Spec §FR-051]
- [ ] CHK065 — Are PPRR phase transition `TimelineEvent` requirements (FR-053) specified with all required fields (source phase, target phase, rationale, authorising user) and how overlap periods are represented? [Completeness, Spec §FR-053]
- [ ] CHK066 — Are `HandoffChainDefinition` extension requirements (FR-054) specific enough to determine which existing handoff patterns are modified vs. which are new? [Clarity, Spec §FR-054]

## Non-Functional Requirements — Completeness & Measurability

- [ ] CHK067 — Are all seven observability metrics (NFR-010) individually defined with units, collection frequency, and alerting thresholds, or listed only as names? [Completeness, Spec §NFR-010]
- [ ] CHK068 — Is the 5-second warning compliance validation target (NFR-001) specified with what operations are included — parsing, validation, tier/principle checking, or end-to-end? [Clarity, Spec §NFR-001]
- [ ] CHK069 — Are graceful degradation requirements (NFR-011, NFR-012) specified for all new capabilities, or only for lessons register and recovery dashboard? What about AWS warning generation and AIIMS role assignment degradation? [Gap, Spec §NFR-011, §NFR-012]
- [ ] CHK070 — Is the privacy threshold "not identifiable to fewer than 10 individuals" (NFR-014) specified with the aggregation methodology and geographic granularity? [Clarity, Spec §NFR-014]
- [ ] CHK071 — Are content safety validation requirements for recovery content (NFR-013) consistent with spec 008's content safety pipeline — same pipeline, same thresholds, same fallback behaviour? [Consistency, Spec §NFR-013 ↔ Spec 008]

## Acceptance Criteria & Success Criteria — Measurability

- [ ] CHK072 — Is SC-001 ("100% of public warnings conform") measurable — is the compliance check automated, manual, or both, and what is the validation methodology? [Measurability, Spec §SC-001]
- [ ] CHK073 — Is SC-003 (five-stage evacuation with "timeframes appropriate to the hazard type") sufficiently quantified — are hazard-specific timeframes defined or left to operational judgment? [Measurability, Spec §SC-003]
- [ ] CHK074 — Is SC-007 (90% lesson closure within 90 days) specified with how "closure" is defined and what happens to the 10% that don't close in time? [Clarity, Spec §SC-007]
- [ ] CHK075 — Is SC-008 (all six specs updated within 30 days) realistic and measurable — is "include an AIIMS role-mapping section" defined with minimum content requirements? [Measurability, Spec §SC-008]
- [ ] CHK076 — Is SC-010 (community-response indicators within 24 hours) consistent with the assumption that indicators "may initially be manually entered"? [Consistency, Spec §SC-010 ↔ Assumptions]

## Cross-Spec Consistency — Specs 001, 008, 009, 010, 011, 012

- [ ] CHK077 — Does FR-043 (Monitoring Agent spec 010 update) specify the exact sections to be added/modified, or only the intent — "include AIDR-aligned warning classifications and escalation thresholds"? [Clarity, Spec §FR-043]
- [ ] CHK078 — Does FR-044 (Risk Assessment spec 012 update) clarify the relationship between existing `severity_level` (low/moderate/high/critical) and AIDR guidance, given the explicit "no automatic mapping" clarification? [Consistency, Spec §FR-044, Clarifications §Pass 2]
- [ ] CHK079 — Does FR-045 (Resource Allocation spec 011 update) define what "AIDR/AIIMS-aligned prioritisation language" means concretely — specific terminology changes or structural additions? [Clarity, Spec §FR-045]
- [ ] CHK080 — Does FR-046 (Hub spec 001 update) scope the additions precisely — which sections of spec 001 gain AIIMS, PPRR, and Shared Responsibility Model references? [Clarity, Spec §FR-046]
- [ ] CHK081 — Does FR-047 (all agent specs AIIMS role mapping) define a standard template or format for the AIIMS role-mapping section to ensure consistency across all six specs? [Gap, Spec §FR-047]
- [ ] CHK082 — Is the tiered timeout supersession of spec 008's flat 15-minute timeout (Dependency §Spec 008) precisely scoped — which approval types in spec 008 are affected vs. retained? [Consistency, Dependencies ↔ Spec 008]
- [ ] CHK083 — Is spec 009's zone-based evacuation model documented as "augmented not replaced" with clear boundary delineation — which evacuation capabilities come from spec 009 vs. this spec's five-stage framework? [Consistency, Dependencies ↔ Spec 009]
- [ ] CHK084 — Are all six specs (001, 008, 009, 010, 011, 012) enumerated in the Dependencies section with specific reconciliation details, or are some listed without amendment specifics? [Completeness, Dependencies]

## Assumptions & Dependencies — Validation

- [ ] CHK085 — Is the assumption that "recovery agents" are existing agents in recovery-phase mode (not a new agent type) clearly reflected in all FRs that reference "recovery agents" (FR-035, FR-033)? [Consistency, Assumptions ↔ FRs]
- [ ] CHK086 — Is the dependency on spec 007 (simulation/rehearsal mode) for PPRR Preparedness phase specified with what specific simulation capabilities are required? [Completeness, Dependencies ↔ Spec 007]
- [ ] CHK087 — Is the assumption that "community-response indicators may initially be manually entered" reconciled with NFR time constraints (SC-010: 24-hour feedback loop)? [Consistency, Assumptions ↔ §SC-010]
- [ ] CHK088 — Is the assumption that six AIDR handbooks in `docs/aidr/` are sufficient validated — are all handbook references in the spec traceable to one of the six listed handbooks? [Traceability, Assumptions]

## Constitution Alignment — Traceability

- [ ] CHK089 — Does every P1 user story trace to at least one Constitution non-negotiable requirement, and is the traceability bidirectional — does each Constitution AIDR mandate have at least one implementing FR? [Traceability, Constitution ↔ Spec]
- [ ] CHK090 — Are Constitution §V-A (AWS), §II-A (AIIMS), §VI (Evacuation), §VII (Recovery), §V-B/V-C (Warning Principles/Total Warning System) each covered by at least one FR with explicit section reference? [Traceability, Constitution ↔ Spec]
- [ ] CHK091 — Is Constitution non-negotiable §1 (human-in-the-loop) explicitly referenced in warning approval, evacuation decision, and lesson application requirements — or is it only implied? [Traceability, Constitution §Non-Negotiable 1]
- [ ] CHK092 — Is Constitution non-negotiable §2 (data sovereignty — Azure Australia regions) enforced for all new data stores (recovery indicators, lessons register, evacuation records) via NFR-015, or are there gaps? [Traceability, Constitution §Non-Negotiable 2 ↔ §NFR-015]
- [ ] CHK093 — Is Constitution non-negotiable §4 (interoperability — CAP, EDXL, GeoJSON, OpenAPI) addressed for new capabilities (warnings, recovery, lessons) or only for existing capabilities? [Gap, Constitution §Non-Negotiable 4]
- [ ] CHK094 — Are the eleven National EM Principles (Constitution §II) traceable to specific FRs — particularly Principle 11 (continual improvement) to the lessons management FRs? [Traceability, Constitution §II ↔ Spec]

## Requirement Consistency — Internal Coherence

- [ ] CHK095 — Is FR-050's statement that "Prevention and Preparedness phases MAY apply to scenario/region contexts without an active incident" consistent with the `Incident` model being the host of `pprr_phase`? [Conflict, Spec §FR-050]
- [ ] CHK096 — Is the vulnerable populations list consistent across FR-007 (warnings), FR-021 (evacuation), and SC-009 (success criteria) — same groups in all three, or do they diverge? [Consistency, Spec §FR-007 ↔ §FR-021 ↔ §SC-009]
- [ ] CHK097 — Is the "6 AIIMS functions" count consistent throughout the spec — FR-013, FR-014, User Story 2, SC-002, and Constitution §II-A all reference six functions with the same list? [Consistency, Spec-wide]
- [ ] CHK098 — Is the FR count in the spec notes (requirements.md says "47 functional requirements") consistent with the actual count (FRs 001–054 = 54 FRs)? [Conflict, checklists/requirements.md ↔ Spec]

## Notes

- Check items off as completed: `[x]`
- P1 items (CHK001–CHK040) require mandatory resolution before spec approval — life-safety domains per Constitution Principle I
- P2 items (CHK041–CHK056) and P3 items (CHK057–CHK061) follow standard review depth
- Cross-spec items (CHK077–CHK088) validate integration touchpoints with specs 001, 008, 009, 010, 011, 012
- Constitution alignment items (CHK089–CHK094) ensure bidirectional traceability to constitution.md v1.1.0
- Items are numbered globally (CHK001–CHK098) for unambiguous reference

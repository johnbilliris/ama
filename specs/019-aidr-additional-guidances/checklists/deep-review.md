# Deep Requirements Quality Checklist: AIDR Additional Guidance Integration

**Purpose**: Validate that the spec's requirements for emergency planning, M&E framework, recovery indicator catalogue, AI-assisted analysis, and cross-spec integration are complete, clear, consistent, measurable, and free of gaps — before proceeding to planning/implementation.  
**Created**: 2025-07-19  
**Feature**: [spec.md](../spec.md)  
**Depth**: Standard  
**Audience**: Reviewer (PR)  
**Focus Areas**: Requirement Completeness, Clarity & Ambiguity, Consistency, Acceptance Criteria Quality, Scenario Coverage, Edge Case Coverage, Non-Functional Requirements, Dependencies & Assumptions

---

## Requirement Completeness

- [ ] CHK001 — Are the 27 AIDR plan elements listed in FR-002 individually specified with expected content/structure, or only enumerated by title? [Completeness, Spec §FR-002]
- [ ] CHK002 — Are the nine AIDR planning process steps in FR-001 individually defined with entry criteria, exit criteria, and expected outputs for each step? [Completeness, Spec §FR-001]
- [ ] CHK003 — Are requirements for plan exercise types (desktop, functional, field) and their minimum frequency specified beyond "schedule exercises"? [Gap, Spec §FR-006, User Story 1 §AS-4]
- [ ] CHK004 — Are requirements for the "communicate and consult" planning step (step 3) defined beyond listing it as a process step — e.g., stakeholder identification, consultation methods, documentation? [Gap, Spec §FR-001]
- [ ] CHK005 — Are requirements for the "community needs analysis" step of the M&E evaluative lifecycle specified, or only mentioned as a lifecycle stage in FR-008? [Completeness, Spec §FR-008]
- [ ] CHK006 — Are the standard evaluation questions per KEQ domain (referenced as "seeded from AIDR M&E Framework §5.2") enumerated or described with enough detail to validate completeness? [Gap, Spec §FR-011]
- [ ] CHK007 — Are requirements for "disseminating findings" (FR-014) specified with formats, target audiences, channels, and frequency, or only listed as a stakeholder enumeration? [Gap, Spec §FR-014]
- [ ] CHK008 — Are requirements specified for handling AIDR outcomes where "no activities or indicators were developed" (acknowledged in Assumptions), including how these gaps are presented to users? [Completeness, Spec §Assumptions]
- [ ] CHK009 — Are data collection methodology requirements for qualitative indicators specified alongside quantitative, given that FR-021 mentions "data collection methodology where available"? [Gap, Spec §FR-021]
- [ ] CHK010 — Are requirements defined for what constitutes a "cross-domain correlation" in FR-025 — correlation threshold, minimum data points, statistical method, or heuristic approach? [Completeness, Spec §FR-025]
- [ ] CHK011 — Are confidence levels, uncertainty bounds, or reliability indicators defined for AI-generated recommendations in FR-026? [Gap, Spec §FR-026]
- [ ] CHK012 — Are requirements for CSV import (indicator bulk entry) and PDF/JSON export (emergency plans) specified as functional requirements, or only mentioned in Assumptions? [Gap, Spec §Assumptions]
- [ ] CHK013 — Are requirements for the new Planning Agent's API surface, authentication, and inter-agent communication patterns specified? [Gap, Spec §Assumptions]
- [ ] CHK014 — Are requirements for plan security rating enforcement specified beyond "plan visibility follows the plan's security rating" in FR-007a? [Completeness, Spec §FR-007a]

## Requirement Clarity & Ambiguity

- [ ] CHK015 — Is "standard recovery program" in SC-002 and NFR-006 defined with measurable criteria (e.g., number of domains, indicators, outcomes)? [Ambiguity, Spec §SC-002, §NFR-006]
- [ ] CHK016 — Is "standard regional plan" in SC-002 quantified — e.g., number of hazards covered, geographic scope, stakeholder count? [Ambiguity, Spec §SC-002]
- [ ] CHK017 — Is "known indicator correlations" in SC-006 defined with objective criteria for how correlations are established and counted in test scenarios? [Ambiguity, Spec §SC-006]
- [ ] CHK018 — Is "clear and understandable" in SC-007 operationalised with a specific measurement instrument, sample size, or readability metric? [Ambiguity, Spec §SC-007]
- [ ] CHK019 — Are "configurable intervals" for plan review reminders (User Story 1 §AS-4) bounded with default values, minimum/maximum ranges, or guidance? [Clarity, User Story 1 §AS-4]
- [ ] CHK020 — Is "operationally useful format" for activated plan display (User Story 5 §AS-2) defined with specific UX or information architecture requirements? [Ambiguity, User Story 5 §AS-2]
- [ ] CHK021 — Is "evidence-based findings" in SC-009 clarified — what constitutes sufficient evidence for an evaluation finding? [Clarity, Spec §SC-009]
- [ ] CHK022 — Is the "staleness indicator" for delayed indicator data (Edge Case §Indicator-data-unavailable) defined with specific staleness thresholds or aging categories? [Clarity, Spec §Edge Cases]
- [ ] CHK023 — Are "community-specific terms" for restating AIDR outcomes (FR-022) constrained or guided — can users freely rewrite outcomes or must restatements preserve the original intent? [Clarity, Spec §FR-022]
- [ ] CHK024 — Is "community sustainability threshold" in the regression edge case defined with measurable criteria for determining when it has been "compromised"? [Ambiguity, Spec §Edge Cases]
- [ ] CHK025 — Is "relevant emergency plan(s)" in User Story 5 §AS-1 clarified — what matching criteria link plans to incidents (region, hazard type, hierarchy level)? [Clarity, User Story 5 §AS-1]
- [ ] CHK026 — Is "plain-language" in FR-027 defined with a specific readability standard or target audience literacy level? [Clarity, Spec §FR-027]

## Requirement Consistency

- [ ] CHK027 — Does the introduction of RecoveryDomain (5 values including "overarching") alongside RecoveryEnvironment (4 values) create ambiguity in requirements that reference "all domains" vs "all environments" vs "four recovery domains"? [Consistency, Spec §FR-009, §Terminology]
- [ ] CHK028 — Are the "four environments" references in User Story 1 §AS-2 and User Story 3 title consistent with the "five domains" introduced in FR-009/FR-015, or should overarching be explicitly included/excluded? [Consistency, User Stories 1 & 3 vs §FR-009]
- [ ] CHK029 — Do the plan lifecycle states and transitions in FR-006 match exactly with those in the Key Entities §Emergency Plan section (both lists appear independently)? [Consistency, Spec §FR-006 vs §Key Entities]
- [ ] CHK030 — Are NFR performance targets consistent between this spec and the spec 018 targets they reference (e.g., NFR-003 "10 seconds" vs spec 018 NFR-004)? [Consistency, Spec §NFR-003]
- [ ] CHK031 — Do the five evaluation domains listed in FR-011 exactly match the five domains referenced in User Story 2 §AS-5 and SC-009? [Consistency, Spec §FR-011, User Story 2, §SC-009]
- [ ] CHK032 — Is the catalogue scale (~61 outcomes, ~200 activities, ~300 indicators) consistently stated across FR-015, Key Entities §Recovery Outcome, and Assumptions? [Consistency, Spec §FR-015, §Key Entities, §Assumptions]
- [ ] CHK033 — Does the Planning Agent creation (Assumptions) align with FR-007a's AIIMS role-based authorization model — is the agent's AIIMS function mapping documented consistently with Constitution §II-A? [Consistency, Spec §FR-007a, §Assumptions, Constitution §II-A]

## Acceptance Criteria Quality

- [ ] CHK034 — Is SC-005 ("90% of scheduled indicator data collection events completed on time") measurable without explicitly defining what "on time" means relative to each indicator's collection frequency? [Measurability, Spec §SC-005]
- [ ] CHK035 — Is SC-002 ("full emergency planning process within 5 working days") achievable and validated — does this account for the external dependencies inherent in steps like stakeholder consultation and authority endorsement? [Measurability, Spec §SC-002]
- [ ] CHK036 — Does SC-006 ("80% of known indicator correlations") define the methodology for planting and counting "known correlations" in test scenarios? [Measurability, Spec §SC-006]
- [ ] CHK037 — Is SC-003's threshold of "at least 3 of the 4 recovery domains" justified, and does it account for the fifth overarching domain? [Measurability, Spec §SC-003]
- [ ] CHK038 — Is SC-010 ("Constitution updated within 7 days of specification approval") a process/governance requirement rather than a testable software acceptance criterion? [Measurability, Spec §SC-010]
- [ ] CHK039 — Is SC-008 ("all relevant plan content within 10 seconds") consistent with NFR-001 ("plan generation within 15 seconds"), and is plan retrieval during activation the same operation as generation? [Measurability, Spec §SC-008 vs §NFR-001]

## Scenario Coverage

- [ ] CHK040 — Are requirements defined for what happens when a recovery program spans multiple communities with different outcome priorities and conflicting standards of success? [Coverage, Gap]
- [ ] CHK041 — Are requirements specified for when AI analysis produces conflicting or contradictory recommendations across domains? [Coverage, Gap]
- [ ] CHK042 — Are requirements defined for concurrent plan activation across multiple incidents in the same region using overlapping plans? [Coverage, Gap]
- [ ] CHK043 — Are requirements specified for plan hierarchy conflict resolution beyond flagging inconsistencies — who resolves the conflict and what is the default? [Coverage, Spec §Edge Case - Plan hierarchy conflicts]
- [ ] CHK044 — Are requirements for handling future AIDR catalogue updates (new handbook editions) specified — versioning, migration, impact on existing program logic models? [Coverage, Gap]
- [ ] CHK045 — Are requirements defined for when an Activated plan needs emergency amendment during a live incident (not just "activate last endorsed version")? [Coverage, Gap]
- [ ] CHK046 — Are requirements specified for the transition path when an existing spec 018 recovery program adopts the new M&E framework — is this a migration or opt-in? [Coverage, Gap]
- [ ] CHK047 — Are requirements defined for the scenario where the same indicator is tracked by multiple overlapping recovery programs with different baseline values? [Coverage, Spec §Edge Case - Overlapping recovery programs]

## Edge Case Coverage

- [ ] CHK048 — Is the behavior defined when all indicators in a domain show "data unavailable" — can M&E reports still be generated for that domain? [Edge Case, Gap]
- [ ] CHK049 — Are requirements specified for an M&E framework configured with zero custom indicators (catalogue-only), and conversely, for one with only custom indicators (no catalogue links)? [Edge Case, Gap]
- [ ] CHK050 — Is the behavior defined when AI cross-domain analysis has insufficient data points for statistically meaningful correlation? [Edge Case, Gap]
- [ ] CHK051 — Are requirements defined for when the "designated authority" for plan endorsement (FR-007a) is unavailable, disputed, or the authority role is vacant? [Edge Case, Gap]
- [ ] CHK052 — Is the behavior specified when a PostEventReview determines the entire plan was fundamentally inadequate — does this differ from normal PostEventReview→Draft flow? [Edge Case, Gap]
- [ ] CHK053 — Are requirements specified for the maximum depth of plan hierarchy relationships (national → state → regional → local → sub-local?) and behaviour when hierarchy is incomplete? [Edge Case, Gap]
- [ ] CHK054 — Is the behavior defined when an emergency plan references a parent plan that has been Superseded? [Edge Case, Gap]

## Non-Functional Requirements Coverage

- [ ] CHK055 — Are accessibility requirements specified for the program logic model visualisation and recovery indicator dashboards? [NFR, Gap]
- [ ] CHK056 — Are data retention and archival requirements specified for Superseded emergency plans and concluded M&E frameworks? [NFR, Gap]
- [ ] CHK057 — Are offline access or degraded-connectivity requirements specified for emergency plans during incidents (when network may be disrupted)? [NFR, Gap]
- [ ] CHK058 — Are audit trail requirements specified for emergency plan state transitions and M&E framework modifications, beyond the Constitution's general auditability principle (§IV)? [NFR, Gap]
- [ ] CHK059 — Is the performance target for initial catalogue data loading (~300 indicators, ~200 activities, ~61 outcomes into Cosmos DB) specified independently from dashboard rendering targets? [NFR, Gap]
- [ ] CHK060 — Are concurrency/locking requirements specified for simultaneous editing of the same emergency plan by multiple Planning Officers? [NFR, Gap]
- [ ] CHK061 — Are backup and disaster recovery requirements specified for the immutable AIDR catalogue data in Cosmos DB? [NFR, Gap]

## Dependencies & Assumptions

- [ ] CHK062 — Is the assumption that "AIDR handbooks have been converted to Markdown in docs/aidr/" validated as a prerequisite with a clear owner and timeline? [Assumption, Spec §Assumptions]
- [ ] CHK063 — Are backward compatibility requirements for the spec 018 RecoveryIndicator model explicitly defined beyond adding an "optional catalogue_indicator_id field"? [Dependency, Spec §FR-015]
- [ ] CHK064 — Is the dependency on the existing content safety pipeline (spec 008) validated as sufficient for the new AI analysis output types (correlations, recommendations, summaries)? [Dependency, Spec §FR-028, §Dependencies]
- [ ] CHK065 — Are requirements for the new Planning Agent's integration with existing agents (incident controller, monitoring) specified — message contracts, event bus topics, shared state? [Dependency, Gap]
- [ ] CHK066 — Is the dependency on spec 018's PPRR lifecycle (FR-026–FR-031) validated — does spec 018 expose the integration points this spec requires for emergency planning? [Dependency, Spec §FR-029]
- [ ] CHK067 — Are requirements for Constitution amendment (FR-034, SC-010) specified with enough detail — which sections change, who approves, is it versioned? [Dependency, Spec §FR-034]

## Ambiguities & Potential Conflicts

- [ ] CHK068 — Does the spec clarify whether the "planning agent" in Assumptions creates plans autonomously or assists human Planning Officers — given FR-007a assigns authorship to Planning Officers? [Ambiguity, Spec §Assumptions vs §FR-007a]
- [ ] CHK069 — Is the relationship between "program logic model" (FR-010, User Story 6) and "outcomes chain" (User Story 2 §AS-2) clarified — are these the same artefact or distinct? [Ambiguity, Spec §FR-010, User Story 2]
- [ ] CHK070 — Does the spec resolve the tension between "immutable reference data" for the AIDR catalogue and the need for "user-defined extensions stored separately" — are extension governance rules specified? [Conflict, Spec §FR-015, §Assumptions]

## Notes

- Check items off as completed: `[x]`
- Add inline findings or comments after each item as needed
- Items are numbered CHK001–CHK070 for cross-reference in review discussions
- This checklist tests the **quality of requirements** — not whether the implementation works
- Traceability: 90% of items include spec section references, gap markers, or ambiguity flags
- The existing `requirements.md` checklist covers basic structural readiness; this checklist provides deep requirements-quality analysis

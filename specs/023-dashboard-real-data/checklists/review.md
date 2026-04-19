# Review Checklist: Governance Dashboard Real Data Integration

**Purpose**: Validate specification completeness, clarity, consistency, and coverage for the governance dashboard real-data integration feature — testing whether requirements are well-written, not whether the implementation works.
**Created**: 2025-07-19
**Feature**: [spec.md](../spec.md)
**Depth**: Standard
**Audience**: Reviewer (PR / spec review gate)
**Focus Areas**: Health score inputs, Operational readiness, Recovery progress, Risk & warning, Audit trail, Compliance matrix, Cross-cutting concerns, Constitution compliance

## Health Score Input Requirements

- [ ] CHK001 - Are all four health score component weights (40/25/20/15) documented and confirmed to sum to 100%? [Completeness, Spec §FR-001–004]
- [ ] CHK002 - Is the computation method for constitutional compliance (40%) specified — e.g., pass/fail ratio across 10 gates, or weighted scoring? [Clarity, Spec §FR-001]
- [ ] CHK003 - Is the computation method for operational readiness (25%) specified — how are plan states, AIIMS coverage, capabilities, and framework assignments combined into a single score? [Clarity, Spec §FR-002]
- [ ] CHK004 - Is the computation method for data source governance (20%) specified — is it a simple available/total ratio, or does degraded status carry partial weight? [Clarity, Spec §FR-003]
- [ ] CHK005 - Is the computation method for recovery progress (15%) specified — how are outcomes, activities, and indicators across 5 domains aggregated into one number? [Clarity, Spec §FR-004]
- [ ] CHK006 - Is the expected health score range documented (0–100? 0.0–1.0? letter grade?)? [Gap]
- [ ] CHK007 - Is the fallback behavior defined independently for each of the four components when its specific data source is empty? [Completeness, Spec §FR-005]
- [ ] CHK008 - Is the "seed fallback" metadata format specified — what fields, values, and structure does the response include to indicate fallback is in use? [Clarity, Spec §FR-005]
- [ ] CHK009 - Is the behavior defined when some components use real data and others use seed fallback simultaneously? [Edge Case, Spec §FR-005]
- [ ] CHK010 - Are rounding or precision rules for component scores and the composite score specified? [Gap]

## Operational Readiness Requirements

- [ ] CHK011 - Are the PPRR phase distribution computation inputs explicitly tied to framework assignment records and their associated phase definitions? [Completeness, Spec §FR-006]
- [ ] CHK012 - Are all six AIIMS functions (Control, Planning, Intelligence, Public Information, Operations, Logistics) enumerated consistently between FR-007, the Key Entities section, and User Story 2? [Consistency, Spec §FR-007]
- [ ] CHK013 - Is "AIIMS role coverage" defined quantitatively — percentage of organisations with assignments? minimum per function? ratio across functions? [Clarity, Spec §FR-007]
- [ ] CHK014 - Are the 7 emergency plan lifecycle states enumerated or referenced to a definitive source? [Gap, Spec §FR-008, Assumptions]
- [ ] CHK015 - Is the seed/framework-derived fallback for emergency plan expectations specified when no plan records exist? [Clarity, Spec §FR-008]
- [ ] CHK016 - Is "capability gap" defined with measurable criteria — what constitutes a gap between organisation capabilities and framework requirements? [Clarity, Spec §FR-009]
- [ ] CHK017 - Is the volunteer readiness computation defined — how are count, jurisdiction distribution, and capability coverage combined into metrics? [Clarity, Spec §FR-010]
- [ ] CHK018 - Is the classification rule ("volunteer" or "mixed" workforce_type) consistently applied and documented as the sole criterion for volunteer readiness inclusion? [Consistency, Spec §FR-010, Assumptions]
- [ ] CHK019 - Is the behavior defined when an organisation has no AIIMS functions assigned — excluded from coverage but counted elsewhere? [Edge Case, Edge Cases section]
- [ ] CHK020 - Are jurisdiction-level aggregation and breakdown requirements specified for all readiness sub-metrics (PPRR, AIIMS, plans, gaps, volunteers)? [Gap]

## Recovery Progress Requirements

- [ ] CHK021 - Are all 5 recovery domain names (overarching, social, economic, built environment, natural environment) explicitly listed and consistent between FR-011, User Story 3, and Key Entities? [Consistency, Spec §FR-011]
- [ ] CHK022 - Is "domain progress" defined with measurable criteria — indicator completion rate? activity count ratio? weighted composite? [Clarity, Spec §FR-011]
- [ ] CHK023 - Are indicator target values and their relationship to progress computation documented — how does a target translate to a percentage? [Completeness, Spec §FR-012]
- [ ] CHK024 - Is the merge logic between recovery catalogue baseline structure and active tracker progress specified — which takes precedence, how are conflicts resolved? [Clarity, Spec §FR-013]
- [ ] CHK025 - Is the zero-progress baseline state clearly defined for domains where no active tracker exists — show catalogue structure with 0% or omit progress fields? [Completeness, Spec §FR-013, Acceptance Scenario 3.4]
- [ ] CHK026 - Is the behavior defined when a recovery catalogue domain file is malformed or missing — are the remaining 4 domains unaffected? [Edge Case, Edge Cases section]
- [ ] CHK027 - Are the specific counts cited in User Story 3 (e.g., "social domain has 24 outcomes, 57 activities, 53 indicators") documented as examples or hard requirements? [Ambiguity, Spec §US-3 Scenario 2]

## Risk & Warning Requirements

- [ ] CHK028 - Is the severity level taxonomy exhaustively defined — are "critical, high, medium, low" the only levels, or can others exist? [Clarity, Spec §FR-014]
- [ ] CHK029 - Is the ranking algorithm for top risks specified beyond "severity and confidence" — tie-breaking rules? maximum list length? recency factor? [Clarity, Spec §FR-015]
- [ ] CHK030 - Is the AWS principle compliance computation defined with a specific input-to-score mapping — how do trust tiers and data source statuses translate to compliance scores? [Clarity, Spec §FR-016]
- [ ] CHK031 - Is the trust tier to warning system tier alignment mapping documented or referenced? [Gap, Spec §FR-016]
- [ ] CHK032 - Are confidence score ranges and their interpretation specified for hazard assessments? [Gap, Spec §FR-015, Key Entities]
- [ ] CHK033 - Is the zero-count behavior (FR-017) consistent with the seed fallback approach (FR-005) — does zero-count apply only to risk, or should risk also have a seed fallback? [Consistency, Spec §FR-017 vs FR-005]
- [ ] CHK034 - Is the behavior specified when hazard assessments exist but all have the same severity level? [Edge Case]

## Audit Trail Requirements

- [ ] CHK035 - Are all auditable action types exhaustively enumerated — FR-019 lists four (assessments, status changes, framework updates, plan approvals); are these the only types or is the list illustrative? [Completeness, Spec §FR-019]
- [ ] CHK036 - Is the audit entry schema (field names, types, optionality) specified beyond the high-level list in FR-018? [Clarity, Spec §FR-018]
- [ ] CHK037 - Is the decision chain structure (linked audit events in FR-021) defined — parent-child? sequential? graph? [Clarity, Spec §FR-021]
- [ ] CHK038 - Are search and filter operations (FR-020) specified for each dimension — action type, actor, time range, related entity — with expected behavior for multi-criteria filters? [Completeness, Spec §FR-020]
- [ ] CHK039 - Is the immutability requirement for audit entries explicitly stated as a functional requirement, or only implied by the Key Entities description? [Gap, Key Entities]
- [ ] CHK040 - Is the clarification that seed data loading must NOT generate audit entries reflected in a formal requirement, or only in the Clarifications section? [Traceability, Clarifications session 2025-07-18]
- [ ] CHK041 - Is the "correct initial state" of an empty audit trail (no actions performed) documented as expected behavior in a requirement? [Completeness, Clarifications]
- [ ] CHK042 - Is tenant scoping for audit entries specified — are audit queries automatically filtered by tenant? [Consistency, Spec §FR-027, Key Entities]

## Compliance Matrix Requirements

- [ ] CHK043 - Is the "visual distinction" between real assessment results and seed-derived baselines (FR-024) specified with measurable criteria — indicator type? label? color? icon? [Clarity, Spec §FR-024]
- [ ] CHK044 - Is the seed-derived baseline computation defined — what compliance status does each gate receive for each data source when no assessment exists? [Gap, Spec §FR-023]
- [ ] CHK045 - Is the partial-assessment scenario (some data sources assessed, others not) handled explicitly as a requirement — not just in acceptance scenarios? [Completeness, Spec §FR-022/023, Acceptance Scenario 6.3]
- [ ] CHK046 - Are all 10 constitutional gates cross-referenced consistently between FR-001 (health score), FR-022/023 (compliance matrix), and Key Entities (constitutional assessment)? [Consistency]
- [ ] CHK047 - Is the compliance status taxonomy defined — are "pass/fail/partial" the only values, or can "not assessed" or "seed baseline" also appear? [Clarity, Key Entities]
- [ ] CHK048 - Is the "seed baseline" indicator (Acceptance Scenario 6.2) specified as a data field in the response or a presentation concern? [Clarity, Spec §US-6 Scenario 2]

## Cross-Cutting Requirements

- [ ] CHK049 - Are all 13 existing dashboard endpoints enumerated anywhere in the spec, or is "13" an unverifiable claim? [Gap, Spec §FR-025]
- [ ] CHK050 - Is "backward compatible" defined with specific constraints — are field names, data shapes, endpoint paths, HTTP methods, and status codes all covered? [Clarity, Spec §FR-025]
- [ ] CHK051 - Is the "additive metadata" approach (new fields like "data_source: seed_fallback") specified with a schema or examples showing the exact field structure? [Clarity, Assumptions]
- [ ] CHK052 - Is tenant isolation enforcement (FR-027) specified for all data query paths — seed data, Cosmos DB queries, audit queries, recovery catalogue? [Completeness, Spec §FR-027]
- [ ] CHK053 - Is the 500ms p95 performance target (SC-007) scoped to all 13 endpoints, or only specific "typical query patterns"? [Ambiguity, Spec §SC-007]
- [ ] CHK054 - Is the superseded assessment exclusion rule (FR-028, `is_current` flag) consistently applied across health score computation AND compliance matrix AND audit trail? [Consistency, Spec §FR-028, Assumptions]
- [ ] CHK055 - Is the seed-to-real-data transition behavior defined — automatic per-query detection, startup-time check, or explicit trigger? [Clarity, Spec §FR-026]
- [ ] CHK056 - Is degradation behavior specified when both seed data AND data store are unavailable simultaneously? [Edge Case, Edge Cases section]
- [ ] CHK057 - Are dataset scaling requirements beyond the baseline counts (46 sources, 49 orgs, etc.) addressed — any upper bounds or performance degradation expectations? [Gap, Assumptions]
- [ ] CHK058 - Is the partial seed data loading scenario (e.g., organisations loaded but frameworks missing) handled in a formal requirement, not just edge cases? [Traceability, Edge Cases section]
- [ ] CHK059 - Does the spec define what "graceful error response" means concretely — HTTP status, error body format, user-facing message? [Clarity, Edge Cases section]

## Constitution Compliance (10 Gates)

- [ ] CHK060 - Are all 10 constitutional gate names listed in FR-001 consistent with the names used in the existing codebase (`ConstitutionalGateStatus` interface) as documented in Clarifications? [Consistency, Spec §FR-001, Clarifications]
- [ ] CHK061 - Is each gate's assessment criteria specified or referenced — how does the system determine pass/fail/partial for each gate? [Gap, Spec §FR-001]
- [ ] CHK062 - Is the supersession chain for constitutional assessments defined with clear rules — what makes an assessment "current" vs "superseded"? [Clarity, Key Entities, Spec §FR-028]
- [ ] CHK063 - Is the relationship between the constitution's NON-NEGOTIABLE requirements and the 10 gate names documented as a formal mapping? [Traceability, Clarifications session 2025-07-18]
- [ ] CHK064 - Is it specified how a gate with no assessment data (neither stored nor seed-derived) should appear in the health score and compliance matrix? [Edge Case, Gap]
- [ ] CHK065 - Is the constitutional compliance component's aggregation across 10 gates defined — equal weight per gate, or are some gates weighted differently? [Gap, Spec §FR-001]

## Scenario Coverage & Acceptance Quality

- [ ] CHK066 - Are exception flows defined for transient failures (database timeout, partial query failure) across all dashboard views? [Coverage, Gap]
- [ ] CHK067 - Are concurrent access scenarios addressed — do simultaneous dashboard queries with different tenant contexts maintain isolation? [Coverage, Gap]
- [ ] CHK068 - Are the approximate counts in acceptance scenarios (e.g., "~24 response", "~22 preparedness") documented as illustrative examples rather than hard acceptance thresholds? [Ambiguity, Spec §US-2 Scenario 1]
- [ ] CHK069 - Is the exercise completion rate clarification (seed-derived for MVP, 0% when no data exists) captured in a formal requirement or only in Clarifications? [Traceability, Clarifications session 2025-07-18]
- [ ] CHK070 - Are data freshness/staleness requirements specified — how recent must data be to be considered valid for dashboard display? [Gap]
- [ ] CHK071 - Is the framework assignment referencing a non-existent jurisdiction/framework handled in a formal requirement? [Traceability, Edge Cases section]
- [ ] CHK072 - Is the "all data sources same status" edge case (e.g., all "available" = 100% score) captured in data source governance requirements? [Edge Case, Edge Cases section]

## Notes

- Check items off as completed: `[x]`
- Add comments or findings inline beneath each item
- Items marked `[Gap]` indicate requirements that may need to be added to the spec
- Items marked `[Ambiguity]` indicate requirements needing clarification
- Items marked `[Consistency]` indicate potential misalignment across spec sections
- Items marked `[Traceability]` indicate decisions in Clarifications not yet reflected in formal requirements
- This checklist tests the **quality of requirements**, not the correctness of implementation

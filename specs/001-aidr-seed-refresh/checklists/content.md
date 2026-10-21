# Content Requirements Checklist: Refresh AIDR Seed Incident Content

**Purpose**: Assess completeness, clarity, consistency, and release-readiness of the approved AIDR seed-content requirements.
**Created**: 2026-10-12
**Feature**: [spec.md](../spec.md) and [plan.md](../plan.md)

## Requirement Completeness

- [ ] CHK001 Are the boundaries of the complete seeded AIDR catalogue explicit, including execution-time membership discovery and reconciliation so no current seeded incident is omitted? [Completeness, Spec §FR-001, Spec §SC-001, Plan §Scale/Scope]
- [ ] CHK002 Are requirements explicit that every current seeded AIDR record is refreshed, including records with short, sparse, or less prominent source accounts—not only representative incidents? [Coverage, Spec §FR-001, Spec §FR-007, Spec §SC-001]
- [ ] CHK003 Are unavailable, incomplete, or non-explanatory source cases distinguished clearly, with requirements to retain verified information and avoid unsupported additions? [Completeness, Spec §FR-007, Spec §Edge Cases]
- [ ] CHK004 Are AIDR's non-commercial-use condition, required attribution, and item-level exclusion of identified third-party material without owner permission explicit? [Source Use, Spec §SRC-001–SRC-003, Plan §Content-use and publication controls]

## Requirement Clarity

- [ ] CHK005 Is “complete AIDR incident content” clear enough to mean the full available explanatory account rather than a selected excerpt or shortened summary? [Clarity, Spec §FR-002–FR-004]
- [ ] CHK006 Is it unambiguous that the captured content is stored and displayed directly as the same `introduction` value, with no separate source-text/display-text distinction or shortened parallel account? [Clarity, Consistency, Spec §FR-003–FR-005, Plan §Summary]
- [ ] CHK007 Are the heatwave details concrete enough to make completeness assessable, including the early-2013 record temperatures, geographic extent, 7 January national record, Perth impacts, Alice Springs and Oodnadatta records, Sydney's 17 January record and impacts, ambulance/hospital effects, commuter disruption, increased admissions, and the Bureau's exceptional-event characterization? [Clarity, Spec §FR-006, Spec §SC-004]
- [ ] CHK008 Are terms such as “when available,” “incomplete,” and “verified information” sufficiently defined to guide consistent decisions about retaining or refreshing an incident account? [Ambiguity, Spec §FR-002, Spec §FR-007, Spec §Assumptions]

## Requirement Consistency

- [ ] CHK009 Do the catalogue-wide refresh requirements and the detailed heatwave example remain consistent, so the example illustrates expected detail without narrowing the requirement to that single incident? [Consistency, Spec §FR-001, Spec §FR-005–FR-006]
- [ ] CHK010 Do requirements consistently treat `introduction` as both the captured incident content and the page-facing content, without implying a second narrative or intermediate shortened account? [Consistency, Spec §FR-003–FR-004, Spec §SC-002–SC-003, Plan §Design Decisions]
- [ ] CHK011 Are the instruction to use complete available source text and the fallback to retain verified content for unavailable or incomplete sources reconciled without encouraging invention or unsupported completion? [Consistency, Spec §FR-004, Spec §FR-007, Spec §Edge Cases]

## Acceptance Criteria Quality

- [ ] CHK012 Can catalogue-wide completeness be objectively demonstrated by automated reconciliation and coverage evidence derived from the current catalogue, without treating the observed 523-record count as permanent? [Measurability, Spec §SC-001–SC-002, Plan §Technical Context, Plan §Design Decisions]
- [ ] CHK013 Are the success criteria for full captured-text display measurable in a way that distinguishes full content from truncation or an intermediate summary? [Acceptance Criteria, Measurability, Spec §SC-002–SC-003]
- [ ] CHK014 Is human operator review defined as a release check before public dissemination, while explicitly not blocking local refresh, code changes, or automated validation? [Acceptance Criteria, Spec §FR-009, Plan §Constitution Check]

## Scenario and Edge Case Coverage

- [ ] CHK015 Are requirements complete for ordinary seeded incidents with available explanatory content, sparse accounts, unavailable sources, and incomplete source accounts? [Coverage, Spec §User Story 1, Spec §Acceptance Scenarios, Spec §Edge Cases]
- [ ] CHK016 Are all specified heatwave context categories represented in the requirements, with enough detail to distinguish national records, locality-specific impacts, and health/transport effects? [Coverage, Spec §FR-005, Spec §SC-004]
- [ ] CHK017 Are requirements for catalogue reconciliation and preservation of verified information explicit enough to cover incidents whose source content cannot be refreshed? [Coverage, Edge Case, Spec §FR-001–FR-002, Spec §FR-008, Plan §Design Decisions]

## Dependencies and Assumptions

- [ ] CHK018 Are the approved AIDR terms and attribution form documented as source-use constraints, without introducing an obsolete unresolved-rights gate? [Dependency, Assumption, Spec §SRC-001–SRC-003, Plan §Content-use and publication controls]
- [ ] CHK019 Is item-level handling explicit so content identified as third-party-owned or used with third-party permission is excluded unless the owner permits reproduction? [Dependency, Coverage, Spec §SRC-003, Plan §Content-use and publication controls]
- [ ] CHK020 Are catalogue-wide completeness and exact stored-to-rendered `introduction` equality evidenced automatically, with no manual per-record evidence ledger? [Auditability, Spec §SC-001–SC-002, Plan §Constitution Check, Plan §Architecture]
- [ ] CHK021 Are the assumptions clear that the current seeded AIDR cohort is re-inventoried at refresh time and that the heatwave is an illustrative completeness example, not the scope boundary? [Assumption, Clarity, Spec §FR-001, Spec §FR-006–FR-007, Plan §Scale/Scope]

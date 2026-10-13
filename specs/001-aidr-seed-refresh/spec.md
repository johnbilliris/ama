# Feature Specification: Refresh AIDR Seed Incident Content

**Feature Branch**: `001-aidr-seed-refresh`  
**Created**: 2026-10-12  
**Status**: Draft  
**Input**: User description:

> An earlier specification ingested historical incident data from the `knowledge.aidr.org.au` website. It appears that only a portion of the explanatory text was extracted and then saved for the initial seeding of this solution.
>
> For example, for incident URL `incidents/aidr-2349-health-national-heatwave-2012`, the solution currently states in “About this incident”: “From late December 2012 to early January 2013, Australia experienced a nationwide heatwave. Temperatures peaked throughout Australia, forcing the Bureau of Meteorology to add new colours (deep purple and pink) to its weather forecasting chart to record temperatures above 50°C.”
>
> The source website gives a much longer account, including: Australia’s first six days of 2013 being among the hottest 20 days on record for average maximums; the heatwave’s geographic extent; the 7 January national average maximum record; impacts in Perth and ambulance/hospital presentations; records in Alice Springs and Oodnadatta; Sydney’s 17 January record, ambulance treatments and commuter disruption; increased hospital admissions for kidney disease, acute renal failure, and heart attacks; and the Bureau’s characterization of this as an exceptional event.
>
> The requested change is a simple refresh of all AIDR seed data and ensuring that the complete explanatory information is shown on the incident page in this solution. Capture the AIDR incident content and use that same content directly as the incident page's displayed information. Apply the refresh across all seeded AIDR incidents, not only this example.

## Clarifications

### Session 2026-10-12

- Q: Should source explanatory text be distinct from the incident-page content? → A: No; use the captured AIDR incident content directly as the displayed incident information.
- Q: What is the intended use of AIDR incident text? → A: Non-commercial use.
- Q: What source-use conditions apply to reproduced AIDR materials? → A: Include the required AIDR attribution; exclude third-party-owned content unless its owner permits reproduction.
- Q: How should catalogue-wide completeness be validated? → A: Automatically verify every seeded record is refreshed and its captured `introduction` is passed through and rendered unchanged; no per-record manual evidence ledger.
- Q: When is human operator review required? → A: Before public dissemination or release; it does not block local refresh, code changes, or automated validation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand an AIDR incident (Priority: P1)

As a person reviewing a historical incident, I want its incident page to present a sufficiently complete account of what happened and its effects, so I can understand the event without relying on a short summary that omits important context.

**Why this priority**: The primary value of the refresh is making useful explanatory information available to people viewing seeded AIDR incidents.

**Independent Test**: Open an incident page for a seeded AIDR incident and confirm its displayed account reflects the meaningful context in the refreshed incident information. For the 2012 national heatwave example, confirm the full explanatory account is represented, including the early-2013 records, geographic extent, temperature records, Perth and Sydney impacts, ambulance and hospital effects, and the Bureau's characterization.

**Acceptance Scenarios**:

1. **Given** the 2012 national heatwave incident is available, **When** a user opens its incident page, **Then** the displayed incident information is the captured AIDR incident content, including the complete explanatory account: Australia's first six days of 2013 among the 20 hottest days on record for average maximums; the heatwave's geographic extent; the 7 January national average maximum record; Perth impacts and ambulance/hospital presentations; Alice Springs and Oodnadatta records; Sydney's 17 January record, ambulance treatments, and commuter disruption; increased admissions for kidney disease, acute renal failure, and heart attacks; and the Bureau's characterization of an exceptional event.
2. **Given** a user opens any other seeded AIDR incident with source explanatory text, **When** they read its incident information, **Then** the captured content includes the complete source explanatory text and is used directly as the displayed information rather than retaining an outdated partial account.
3. **Given** the source information for an incident is unavailable or incomplete, **When** the incident information is refreshed, **Then** verified information is retained and no unsupported facts are added.

### User Story 2 - Review refreshed AIDR incident information (Priority: P2)

As a person responsible for reviewing incident information, I want the refreshed AIDR incident content to be used directly on the incident page, so the displayed information reflects the complete captured account.

**Why this priority**: The incident page should present the captured AIDR incident information itself, without maintaining a separate content distinction that could leave the displayed account incomplete.

**Independent Test**: Run automated catalogue-wide validation confirming every seeded AIDR record is refreshed and, for each record with a captured `introduction`, that the exact captured value is passed through and rendered unchanged. This does not require a separate per-record manual evidence ledger. Human operator review remains a required check before public dissemination or release.

**Acceptance Scenarios**:

1. **Given** a seeded incident has refreshed AIDR incident content, **When** a reviewer opens its incident page, **Then** that same content is used as the displayed incident information and no separate source-versus-display account is required.
2. **Given** the source contains explanatory details relevant to understanding an incident, **When** the incident page is displayed, **Then** the complete captured explanatory text and its details are displayed directly.
3. **Given** a local refresh, code change, or automated validation is being performed, **When** no public dissemination or release is occurring, **Then** human operator review is not a prerequisite for that work.
4. **Given** refreshed incident content is to be publicly disseminated or released, **When** it is prepared for dissemination or release, **Then** a human operator reviews the public-facing output beforehand.

### Edge Cases

- A source incident may provide little explanatory material; the refreshed page must not invent missing facts.
- Some historical source accounts may include many dates, locations, records, and impacts; capture and display the complete AIDR incident content, including its full explanatory text.
- A source account may be unavailable or incomplete during refresh; existing verified incident information must not be replaced with fabricated content.
- The refresh must cover every seeded AIDR incident, including records with shorter or less prominent source accounts, rather than only the heatwave example.
- Content identified by AIDR as used with permission of a third-party copyright owner is excluded unless that owner permits reproduction.
- Human operator review of public-facing output is required before dissemination or release, but is not a gate on local refresh, code changes, or automated validation.

### Assumptions

- “All seeded AIDR incidents” means every historical incident from AIDR already included in the solution’s initial seeded incident set.
- Captured AIDR incident content is the content used directly as the incident page's displayed information; no separate source-content and page-content distinction is required.
- When available, the complete explanatory text is part of the captured incident content and is displayed in full.
- Existing verified information remains usable when a source account cannot be refreshed or contains no additional explanatory detail.
- The intended use of reproduced AIDR incident text is non-commercial.
- AIDR materials may be reproduced for personal or non-commercial use without formal permission, subject to the attribution and third-party-content requirements below.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The solution MUST refresh the seed information for every AIDR incident included in the initial seeded incident set.
- **FR-002**: For each seeded AIDR incident, the solution MUST capture the incident content, including the `introduction` value, from the corresponding AIDR incident information when available.
- **FR-003**: The captured AIDR incident content MUST be used directly as the incident page's displayed information; the solution MUST NOT require a separate distinction between source explanatory text and displayed content.
- **FR-004**: For every seeded AIDR incident with a captured `introduction`, automated validation MUST verify that the value is passed through and rendered unchanged.
- **FR-005**: When explanatory text is available, the captured incident content and incident page MUST include and display the complete text, rather than only a fragment.
- **FR-006**: The 2012 national heatwave incident page MUST preserve the source account's material details, including the first six days of 2013 ranking among the 20 hottest days on record for average maximums, geographic extent, the 7 January national average maximum record, Perth and Alice Springs/Oodnadatta records and impacts, Sydney's 17 January record and impacts, ambulance and hospital effects, increased admissions for kidney disease, acute renal failure, and heart attacks, and the Bureau's characterization of an exceptional event.
- **FR-007**: The complete-content capture and direct display MUST apply consistently to all seeded AIDR incidents and MUST NOT be limited to the example incident.
- **FR-008**: When source information is unavailable, incomplete, or lacks explanatory detail, the solution MUST retain verified information and MUST NOT invent incident facts.
- **FR-009**: Before public dissemination or release of public-facing output, a human operator MUST review that output. This review MUST NOT block local data refresh, code changes, or automated validation.

### Source Use Constraints

- **SRC-001**: Under AIDR's Terms and Conditions, materials may be reproduced for personal or non-commercial use without formal permission; the intended use for this feature is non-commercial.
- **SRC-002**: Reproduced AIDR materials MUST include this attribution: “Obtained from the Australian Institute for Disaster Resilience, © Commonwealth of Australia [year of use].”
- **SRC-003**: Content identified as used with permission of a third-party copyright owner MUST NOT be reproduced unless that owner permits reproduction.

### Key Entities

- **AIDR incident content**: The incident information captured from the corresponding AIDR source, including its complete explanatory text when available; this same content is used as the incident page's displayed information.
- **Seeded AIDR incident**: A historical incident included in the solution’s initial seeded incident set and identified by its source incident reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Automated validation confirms that 100% of seeded AIDR incident records are refreshed.
- **SC-002**: For 100% of refreshed records with a captured `introduction`, automated validation confirms that the exact captured value is passed through and rendered unchanged; no separate per-record manual evidence ledger is required.
- **SC-003**: All available explanatory text is retained and displayed in full, with no unsupported facts added when source information is unavailable or incomplete.
- **SC-004**: The heatwave incident-page account includes all supplied material context: the early-2013 record temperatures and geographic extent; national, Perth, Alice Springs, Oodnadatta, and Sydney records; Perth and Sydney impacts; ambulance, hospital, and commuter effects; increased admissions for kidney disease, acute renal failure, and heart attacks; and the Bureau’s characterization of an exceptional event.

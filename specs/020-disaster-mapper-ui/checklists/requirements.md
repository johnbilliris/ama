# Requirements Quality Checklist: Disaster Mapper UI

**Purpose**: Validate completeness, clarity, consistency, measurability, and coverage of all requirements in the Disaster Mapper UI specification — functional (FR-001–FR-038), non-functional (NFR-001–NFR-003), success criteria (SC-001–SC-009), edge cases, accessibility, and integration points.  
**Created**: 2025-07-17  
**Feature**: [spec.md](../spec.md)  
**Constitution**: [constitution.md](../../../.specify/memory/constitution.md)  
**Depth**: Comprehensive (formal review gate)  
**Audience**: Spec author and PR reviewers

---

## Requirement Completeness — Map Display (FR-001–FR-005)

- [ ] CHK001 — Is the initial map zoom level or bounding box specified so that "centred on Australia" can be objectively reproduced? [Clarity, Spec §FR-001]
- [ ] CHK002 — Are minimum and maximum zoom levels defined for the interactive map? [Gap]
- [ ] CHK003 — Is the marker size or scale defined for individual incident markers? [Gap, Spec §FR-002]
- [ ] CHK004 — Are the hex colour values for severity tiers consistent across FR-003, the Clarifications section, and the Assumptions section? [Consistency, Spec §FR-003]
- [ ] CHK005 — Are the marker shape dimensions (circle radius, triangle size, diamond size) specified or deferred to a design token system? [Clarity, Spec §FR-003a]
- [ ] CHK006 — Are touch-gesture interactions (pinch-to-zoom, two-finger pan) explicitly listed alongside mouse interactions in FR-004? [Completeness, Spec §FR-004]
- [ ] CHK007 — Is the visual style of cluster count badges (font, background colour, size) specified or delegated to a design system? [Gap, Spec §FR-005]
- [ ] CHK008 — Is the behaviour defined when a cluster is clicked but cannot expand further (e.g., fully overlapping coordinates at max zoom)? [Edge Case, Spec §FR-005]
- [ ] CHK009 — Is the 60px clustering radius justified or configurable, and are requirements defined for different screen densities (Retina/HiDPI)? [Clarity, Spec §FR-005]

## Requirement Completeness — Filter Panel (FR-006–FR-015)

- [ ] CHK010 — Is the filter panel's default state (open or collapsed) on initial page load specified for both desktop and mobile? [Gap, Spec §FR-006]
- [ ] CHK011 — Is the visual ordering or grouping of the five filter categories within the panel specified? [Gap, Spec §FR-006]
- [ ] CHK012 — Are the default selected values for each filter on initial page load defined (all selected, none selected, or specific defaults)? [Gap, Spec §FR-006]
- [ ] CHK013 — Is the behaviour defined when the user selects a start year greater than the end year in the date range filter? [Edge Case, Spec §FR-007]
- [ ] CHK014 — Is it specified whether the year selectors are dropdowns, sliders, or free-text inputs? [Clarity, Spec §FR-007]
- [ ] CHK015 — Is the dynamic year range source (earliest incident to current year) documented as a requirement or only as an assumption? [Traceability, Assumptions §6]
- [ ] CHK016 — Are the default toggle states for incident type filters defined (all on or all off)? [Gap, Spec §FR-008]
- [ ] CHK017 — Is the "Reset" control's target state defined — does it reset to "all selected" or "none selected"? [Ambiguity, Spec §FR-012]
- [ ] CHK018 — Is debouncing or throttling behaviour specified for rapid consecutive filter changes to prevent excessive API calls? [Gap, Spec §FR-014]
- [ ] CHK019 — Is the location and visual format of the visible incident count display specified? [Clarity, Spec §FR-015]
- [ ] CHK020 — Does the incident count in FR-015 include or exclude incidents that could not be mapped (FR-030)? [Ambiguity]

## Requirement Completeness — Detail Sidebar (FR-016–FR-020)

- [ ] CHK021 — Is the sidebar width (fixed or percentage) specified for desktop viewports? [Gap, Spec §FR-016]
- [ ] CHK022 — Is the sidebar entry/exit animation or transition behaviour specified or deferred to a design system? [Gap, Spec §FR-016]
- [ ] CHK023 — Are date and time formatting requirements defined for the "start date" field in the sidebar? [Gap, Spec §FR-017]
- [ ] CHK024 — Is the display format for "affected jurisdictions" specified when an incident has multiple jurisdictions? [Gap, Spec §FR-017]
- [ ] CHK025 — Is the display format for "incident level" specified (numeric "Level 1" vs descriptive "Local, single-agency")? [Clarity, Spec §FR-017]
- [ ] CHK026 — Is the link text and visual treatment for the incident workspace link specified? [Gap, Spec §FR-018]
- [ ] CHK027 — Is it specified whether the sidebar can be closed by clicking outside the sidebar area, or only via the close button? [Clarity, Spec §FR-019]
- [ ] CHK028 — Is transition behaviour defined when switching between incidents in the sidebar (instant swap, cross-fade, slide)? [Gap, Spec §FR-020]

## Requirement Completeness — Search (FR-021–FR-024)

- [ ] CHK029 — Is a debounce delay or minimum character count defined before search triggers map updates? [Gap, Spec §FR-021]
- [ ] CHK030 — Is the decision to match only incident titles (excluding descriptions, jurisdictions, type labels) explicitly justified as intentional scope limitation? [Scope, Spec §FR-022]
- [ ] CHK031 — Is the "no results" message content and location specified for search-with-no-matches? [Clarity, User Story 4, Acceptance Scenario 4]
- [ ] CHK032 — Is it specified whether the search input is preserved or cleared when navigating away from and back to the Disasters page? [Gap]

## Requirement Completeness — Responsiveness & Layout (FR-025–FR-028)

- [ ] CHK033 — Is the 768px breakpoint the only breakpoint, or are additional breakpoints needed for tablet (1024px) and large desktop? [Completeness, Spec §FR-027]
- [ ] CHK034 — Is the mobile bottom sheet maximum height specified to ensure the map remains partially visible? [Gap, Spec §FR-027]
- [ ] CHK035 — Are landscape orientation requirements for mobile devices explicitly defined beyond "adapts smoothly"? [Clarity, User Story 5, Acceptance Scenario 4]
- [ ] CHK036 — Is the minimum supported viewport width specified (SC-007 says 360px — is this also in the FR section)? [Consistency, Spec §FR-027 vs SC-007]

## Requirement Completeness — Data & Error Handling (FR-029–FR-035)

- [ ] CHK037 — Is the full list of query parameters for `GET /api/v1/incidents/map` enumerated with their types, formats, and validation rules? [Completeness, Spec §FR-029]
- [ ] CHK038 — Is the GeoJSON FeatureCollection response schema defined or referenced, including required and optional properties per Feature? [Clarity, Spec §FR-029]
- [ ] CHK039 — Is the sort order for "most recent 500 incidents" defined (by start date, by creation timestamp, or other)? [Ambiguity, Spec §FR-035]
- [ ] CHK040 — Is the maximum total incident count for progressive loading bounded, or does it load the entire dataset regardless of size? [Gap, Spec §FR-035]
- [ ] CHK041 — Is the visual location and dismissibility of the "incidents could not be mapped" notice specified? [Clarity, Spec §FR-030]
- [ ] CHK042 — Is the list-view fallback table's default sort column and sort order defined? [Gap, Spec §FR-031]
- [ ] CHK043 — Is the "retry" mechanism in FR-031 defined as a manual button click, automatic retry with backoff, or both? [Clarity, Spec §FR-031]
- [ ] CHK044 — Is the loading indicator type and placement specified (spinner, skeleton, progress bar)? [Gap, Spec §FR-032]
- [ ] CHK045 — Is the "Last updated" timestamp format (absolute, relative, locale-specific) defined? [Gap, Spec §FR-034]
- [ ] CHK046 — Is the "Last updated" timestamp's position on the page specified? [Gap, Spec §FR-034]
- [ ] CHK047 — Is the behaviour defined when progressive background loading (FR-035) encounters an error mid-stream? [Edge Case, Spec §FR-035]
- [ ] CHK048 — Are HTTP error response codes and their user-facing messages specified for the `/api/v1/incidents/map` endpoint? [Gap, Spec §FR-029]

## Requirement Completeness — Accessibility (FR-036–FR-038)

- [ ] CHK049 — Is the keyboard tab order through map markers defined (geographic order, severity order, or DOM order)? [Gap, Spec §FR-036]
- [ ] CHK050 — Is the visual focus indicator style for keyboard-navigated markers specified? [Gap, Spec §FR-036]
- [ ] CHK051 — Is keyboard navigation defined for sidebar controls, filter panel controls, and the search bar in addition to map markers? [Completeness, Spec §FR-036]
- [ ] CHK052 — Is the exact ARIA live region announcement text template specified (e.g., "Showing {n} incidents" vs "42 incidents match your filters")? [Clarity, Spec §FR-037]
- [ ] CHK053 — Is the ARIA live region politeness level specified (`polite` vs `assertive`)? [Gap, Spec §FR-037]
- [ ] CHK054 — Are `alt` text or `aria-label` requirements specified for map markers, cluster badges, and severity icons? [Gap]
- [ ] CHK055 — Is the 3:1 contrast ratio in FR-038 validated against specific Azure Maps tile styles (e.g., road, satellite, dark mode)? [Clarity, Spec §FR-038]
- [ ] CHK056 — Are ARIA roles and landmarks specified for the map region, filter panel, sidebar, and search bar? [Gap]

## Requirement Clarity — Vague Terms & Measurability

- [ ] CHK057 — Is "smoothly" in User Story 1 Acceptance Scenario 4 ("map responds smoothly") quantified with frame-rate or latency thresholds? [Measurability, User Story 1 §AS-4]
- [ ] CHK058 — Is "without visible performance degradation" in SC-004 quantified (minimum FPS, maximum input latency)? [Measurability, Spec §SC-004]
- [ ] CHK059 — Is "longer than expected" in the slow-network edge case quantified with a specific timeout threshold? [Ambiguity, Edge Cases §5]
- [ ] CHK060 — Is "prominent link" in User Story 3 defined with specific visual treatment (button vs hyperlink, sizing, placement)? [Clarity, User Story 3]
- [ ] CHK061 — Can "usable on mobile viewports" in SC-007 be objectively measured beyond "no horizontal scrolling or truncated controls"? [Measurability, Spec §SC-007]
- [ ] CHK062 — Is the "first-time users" testing methodology for SC-005 specified (participant count, task definition, testing environment)? [Measurability, Spec §SC-005]
- [ ] CHK063 — Is "within 3 seconds" in SC-001 measured under specified network conditions (3G, 4G, broadband) and device types? [Clarity, Spec §SC-001]

## Requirement Consistency — Cross-Reference Checks

- [ ] CHK064 — Are the five status values in FR-010 (Monitoring, Active, Stabilising, Recovery, Closed) consistent with the omission of "rehearsal" documented in FR-029 and Assumptions §9? [Consistency]
- [ ] CHK065 — Is the severity domain value mapping consistent across FR-003, FR-009, Clarifications, and Assumptions (four locations)? [Consistency]
- [ ] CHK066 — Does the 768px breakpoint in FR-027 align with the 360px minimum in SC-007, and are intermediate widths (360px–768px) addressed? [Consistency, Spec §FR-027 vs §SC-007]
- [ ] CHK067 — Is the "no matching incidents" message consistent between Edge Case §1 ("No incidents match your criteria") and User Story 4 Acceptance Scenario 4 ("informational message indicates no results")? [Consistency]
- [ ] CHK068 — Is the 5-second fallback timeout consistent between NFR-003 and SC-008? [Consistency]
- [ ] CHK069 — Does the pagination default (200 per page in FR-029) align with the initial load of 500 in FR-035 (i.e., 3 pages to reach 500)? [Consistency, Spec §FR-029 vs §FR-035]
- [ ] CHK070 — Is the GeoJSON requirement consistent between FR-029 (API response format), Key Entities (location field), and Assumptions §1? [Consistency]
- [ ] CHK071 — Are the five observability metrics consistent between NFR-002 and SC-009 (same metric names listed in both)? [Consistency]

## Acceptance Criteria Quality — Success Criteria (SC-001–SC-009)

- [ ] CHK072 — Does SC-001 define whether the 3-second threshold applies to the initial 500 incidents or the full dataset? [Clarity, Spec §SC-001]
- [ ] CHK073 — Does SC-002 define whether the 1-second threshold includes API round-trip time or only client-side rendering? [Clarity, Spec §SC-002]
- [ ] CHK074 — Does SC-003 define what constitutes a "click" in the 2-click path (does opening the filter panel count as a click)? [Clarity, Spec §SC-003]
- [ ] CHK075 — Does SC-004 define the measurement method for "500 or more simultaneous markers" (all visible on screen vs all loaded in memory)? [Measurability, Spec §SC-004]
- [ ] CHK076 — Does SC-005 define the minimum sample size and statistical significance for the 90% usability threshold? [Measurability, Spec §SC-005]
- [ ] CHK077 — Does SC-009 define the measurement method for "queryable in Log Analytics within 60 seconds" (end-to-end from event to query result)? [Clarity, Spec §SC-009]

## Scenario Coverage — Primary Flows

- [ ] CHK078 — Are requirements defined for the first-visit experience when no incidents exist in the system (zero-state)? [Coverage, Gap]
- [ ] CHK079 — Are requirements defined for the behaviour when all incidents are filtered out (all filters active but no matches)? [Coverage, Edge Cases §1]
- [ ] CHK080 — Are requirements defined for URL query parameter handling when parameters contain invalid values (e.g., `?severity=invalid`)? [Coverage, Edge Cases §7]
- [ ] CHK081 — Are requirements defined for deep-linking with URL filter state when the user is not authenticated? [Coverage, Assumptions §7]
- [ ] CHK082 — Are requirements defined for the behaviour when the user navigates directly to `/disasters` with partial query parameters? [Coverage, Edge Cases §7]

## Scenario Coverage — Alternate & Exception Flows

- [ ] CHK083 — Are requirements defined for what happens when the backend API returns a 401/403 (authentication/authorisation failure)? [Gap, Exception Flow]
- [ ] CHK084 — Are requirements defined for partial API failures (e.g., incident data loads but Azure Maps tiles fail, or vice versa)? [Gap, Exception Flow]
- [ ] CHK085 — Are requirements defined for the behaviour when the API returns incidents with unknown/new severity values not in the domain mapping? [Edge Case, Spec §FR-003]
- [ ] CHK086 — Are requirements defined for the behaviour when the API returns incidents with unknown/new status or PPRR phase values? [Edge Case, Spec §FR-010, §FR-011]
- [ ] CHK087 — Are requirements defined for concurrent filter + search interactions (user types in search while filter API call is in flight)? [Coverage, Gap]
- [ ] CHK088 — Are requirements defined for browser back/forward navigation interaction with URL filter state? [Gap]
- [ ] CHK089 — Are requirements defined for the behaviour when a linked incident workspace (`/incidents/[incidentId]`) does not exist or returns 404? [Edge Case, Spec §FR-018]

## Edge Case Coverage — Boundary Conditions

- [ ] CHK090 — Is the behaviour defined when an incident's GeoJSON coordinates are outside Australia (e.g., maritime incidents, data errors)? [Edge Case, Spec §FR-002]
- [ ] CHK091 — Is the behaviour defined when incidents have identical coordinates (same location, different incidents)? [Edge Case, Spec §FR-005]
- [ ] CHK092 — Is the behaviour defined for incidents with extreme date values (very old incidents, future-dated incidents)? [Edge Case, Spec §FR-007]
- [ ] CHK093 — Is the maximum length or character set for the search input defined? [Edge Case, Spec §FR-021]
- [ ] CHK094 — Is the behaviour defined when the search input contains special characters, HTML, or script injection attempts? [Edge Case, Security]
- [ ] CHK095 — Is the behaviour defined when the dataset exceeds the "1,000+ incidents" edge case (e.g., 10,000+ incidents)? [Edge Case, Edge Cases §6]
- [ ] CHK096 — Is the behaviour defined when a user rapidly clicks multiple different markers in quick succession? [Edge Case, Spec §FR-020]

## Non-Functional Requirements — Data Sovereignty (NFR-001)

- [ ] CHK097 — Is it specified how to validate that Azure Maps tile requests are served exclusively from Australia-region endpoints? [Measurability, Spec §NFR-001]
- [ ] CHK098 — Is the requirement that "no third-party map tile CDNs outside Australia" are used verifiable through configuration or runtime checks? [Measurability, Spec §NFR-001]
- [ ] CHK099 — Does NFR-001 address whether client-side browser caching of map tiles has data sovereignty implications? [Gap, Spec §NFR-001]

## Non-Functional Requirements — Observability (NFR-002)

- [ ] CHK100 — Are alerting thresholds or SLO targets defined for each of the five named metrics? [Gap, Spec §NFR-002]
- [ ] CHK101 — Is the metric emission mechanism specified (Application Insights SDK, OpenTelemetry, custom events)? [Gap, Spec §NFR-002]
- [ ] CHK102 — Is the `disaster_mapper.api_error_rate` metric's calculation window specified (per-minute, per-hour, rolling)? [Clarity, Spec §NFR-002]
- [ ] CHK103 — Are custom dimensions or properties defined for each metric (e.g., filter type for `filter_apply_ms`, error code for `api_error_rate`)? [Gap, Spec §NFR-002]

## Non-Functional Requirements — Reliability (NFR-003)

- [ ] CHK104 — Is the detection mechanism for "Azure Maps tile service is unavailable" specified (timeout, HTTP status, tile load failure count)? [Clarity, Spec §NFR-003]
- [ ] CHK105 — Is the retry strategy for the API endpoint defined (manual only, automatic with backoff, maximum retries)? [Gap, Spec §NFR-003]
- [ ] CHK106 — Is the transition from map view to list-view fallback specified (automatic, user-initiated, or both)? [Clarity, Spec §NFR-003]

## Constitution Alignment — Integration & Compliance

- [ ] CHK107 — Does the spec address interoperability standards beyond GeoJSON (CAP, EDXL, OpenAPI) as mandated by Constitution §IV? [Gap, Constitution §IV]
- [ ] CHK108 — Does the spec address Privacy Act 1988 compliance for incident data displayed on the map (e.g., PII in incident titles or descriptions)? [Gap, Constitution §III]
- [ ] CHK109 — Does the spec explicitly confirm that the read-only nature (FR-033) satisfies the human-in-the-loop requirement (Constitution §1) by not taking irreversible actions? [Traceability, Constitution §1]
- [ ] CHK110 — Does the spec address auditability requirements (Constitution §IV) for user interactions with the Disasters page (filter changes, marker clicks, searches)? [Gap, Constitution §IV]
- [ ] CHK111 — Are the Australian Warning System tier colours and names consistent with the Constitution §V-A warning level definitions? [Consistency, Constitution §V-A]
- [ ] CHK112 — Does the spec address graceful degradation requirements if a single Azure region becomes unavailable, per Constitution §V? [Gap, Constitution §V]

## Dependencies & Assumptions

- [ ] CHK113 — Is the assumption that "the majority of incidents have location data" quantified with a minimum percentage? [Clarity, Assumptions §1]
- [ ] CHK114 — Is the assumption about existing authentication/authorisation (Assumptions §7) validated as sufficient, or could the Disasters page need additional access controls for sensitive incidents? [Assumption]
- [ ] CHK115 — Is the dependency on the Azure Maps account provisioning explicitly linked to a task or prerequisite in the spec? [Traceability, Assumptions §10]
- [ ] CHK116 — Is the dependency on the FastAPI backend for the new endpoint explicitly linked to the spec as a prerequisite? [Traceability, Assumptions §11]
- [ ] CHK117 — Is it specified whether the Azure Maps SDK version or API version is pinned for reproducibility? [Gap]
- [ ] CHK118 — Is the relationship between the existing incident data model and the new `location` GeoJSON field (migration strategy, backfill plan) addressed? [Gap, Key Entities]

## Ambiguities & Conflicts

- [ ] CHK119 — The spec lists nine incident types in FR-008 but the Edge Cases and User Stories reference only a subset — are all nine types confirmed as exhaustive, or is "Other" a catch-all? [Ambiguity, Spec §FR-008]
- [ ] CHK120 — FR-029 specifies server-side filtering, but FR-014 says "map MUST update without full page reload" — is it specified whether filtering is client-side, server-side, or hybrid? [Ambiguity, Spec §FR-014 vs §FR-029]
- [ ] CHK121 — The spec mentions "sortable table" in FR-031 but does not list which columns are sortable — are all six columns sortable or only a subset? [Ambiguity, Spec §FR-031]
- [ ] CHK122 — Is there a conflict between loading the "most recent 500" (FR-035) and applying date range filters that may not include recent incidents? [Conflict, Spec §FR-035 vs §FR-007]
- [ ] CHK123 — Is a requirement ID scheme established for acceptance scenarios (currently unnumbered "Acceptance Scenarios: 1, 2, 3…") to enable traceability? [Traceability]

## Requirement Coverage — Missing Requirement Classes

- [ ] CHK124 — Are performance budgets specified for the frontend bundle size (JavaScript, CSS) to support the 3-second load target? [Gap, Performance]
- [ ] CHK125 — Are caching requirements specified for API responses and/or map tiles to reduce load times on repeated visits? [Gap, Performance]
- [ ] CHK126 — Are internationalisation (i18n) or localisation requirements specified, particularly for Indigenous language support per Constitution §VI-C? [Gap]
- [ ] CHK127 — Are print or export requirements specified for the map view (screenshot, PDF, data export)? [Gap]
- [ ] CHK128 — Are browser compatibility requirements specified (minimum browser versions, supported browsers)? [Gap]
- [ ] CHK129 — Are session timeout or idle behaviour requirements specified for the Disasters page? [Gap]
- [ ] CHK130 — Are Content Security Policy (CSP) requirements specified for loading Azure Maps scripts and tiles? [Gap, Security]

---

## Notes

- Check items off as completed: `[x]`
- Add inline comments for findings or decisions
- Items marked `[Gap]` indicate requirements that may need to be added to the spec
- Items marked `[Ambiguity]` indicate requirements needing clarification
- Items marked `[Conflict]` indicate potential contradictions between requirements
- Items marked `[Consistency]` indicate cross-reference checks between spec sections
- Refer to `spec.md` section references (e.g., `Spec §FR-001`) for traceability
- Constitution references point to `.specify/memory/constitution.md`

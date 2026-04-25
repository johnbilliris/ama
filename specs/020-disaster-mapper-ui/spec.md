# Feature Specification: Disaster Mapper UI

**Feature Branch**: `020-disaster-mapper-ui`  
**Created**: 2025-07-14  
**Status**: Draft  
**Input**: User description: "Build a sleek, interactive Disaster Mapper user interface inspired by the AIDR Knowledge Hub Disasters page. Interactive map of Australia showing disaster incident markers with search, filter, and detail panels."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — View Incidents on a Map (Priority: P1)

An emergency coordinator navigates to the Disasters page and sees a full-page interactive map of Australia. All current and historical incidents stored in the system are displayed as coloured markers on the map. Each marker's colour and shape reflects the incident's severity using the Australian Warning System tiers: yellow circle for Advice, orange triangle for Watch and Act, and red diamond for Emergency Warning. The coordinator can pan, zoom, and interact with the map to understand the geographic distribution of incidents at a glance.

**Why this priority**: The interactive map is the foundational component of the entire feature. Without it, no other functionality (filtering, detail panels, search) has a surface to operate on. A map displaying severity-coded incident markers delivers immediate situational-awareness value even without filters.

**Independent Test**: Can be fully tested by navigating to `/disasters` and verifying that the map renders with incident markers colour-coded by severity. Delivers geographic situational awareness as a standalone capability.

**Acceptance Scenarios**:

1. **Given** the user navigates to the Disasters page, **When** the page finishes loading, **Then** an interactive map of Australia is displayed with the map centred on the Australian continent.
2. **Given** incidents exist in the system with location data, **When** the map loads, **Then** each incident appears as a marker at its geographic location.
3. **Given** incidents have different severity levels, **When** markers are rendered, **Then** Advice incidents display yellow circle markers (#FFC107), Watch and Act display orange triangle markers (#FF8C00), and Emergency Warning display red diamond markers (#D32F2F). Domain values "warning" and "emergency" both render as Emergency Warning (red diamond).
4. **Given** the user interacts with the map, **When** they pan or zoom, **Then** the map responds smoothly and markers reposition correctly.
5. **Given** the page is accessed within the application, **When** it renders, **Then** it is wrapped in the standard application shell layout with consistent navigation.

---

### User Story 2 — Filter Incidents by Criteria (Priority: P2)

An emergency coordinator needs to narrow down the incidents visible on the map. They open a filter panel alongside the map and apply one or more filters: date range (year-based start and end selectors), incident type (bushfire, flood, cyclone, storm, earthquake, tsunami, extreme heat, pandemic, other), severity tier (Advice, Watch and Act, Emergency Warning), status (monitoring, active, stabilising, recovery, closed), and PPRR phase (prevention, preparedness, response, recovery). The map updates in real time to show only incidents matching the selected criteria. The panel provides "Select All" and "Reset" controls for multi-value filters.

**Why this priority**: Filtering transforms the map from a static display into an analytical tool. Coordinators managing specific hazard types, regions, or time periods depend on filters to extract actionable intelligence. This is the most-requested capability after the base map.

**Independent Test**: Can be tested by applying each filter type individually and in combination, then verifying the map markers update to show only matching incidents. Delivers targeted situational analysis as a standalone capability.

**Acceptance Scenarios**:

1. **Given** the filter panel is visible, **When** the user selects a date range (e.g., 2020–2024), **Then** only incidents with start dates within that range appear on the map.
2. **Given** the filter panel is visible, **When** the user selects one or more incident types (e.g., Bushfire and Flood), **Then** only incidents of those types appear on the map.
3. **Given** the filter panel is visible, **When** the user selects a severity level (e.g., Emergency Warning), **Then** only incidents with that severity appear on the map.
4. **Given** the filter panel is visible, **When** the user selects a status (e.g., Active), **Then** only incidents with that status appear on the map.
5. **Given** the filter panel is visible, **When** the user selects a PPRR phase (e.g., Response), **Then** only incidents in that phase appear on the map.
6. **Given** multiple filters are active, **When** the user applies them together, **Then** only incidents matching ALL selected criteria appear (filters are combined with AND logic).
7. **Given** filters are active, **When** the user clicks "Reset", **Then** all filters are cleared and all incidents reappear on the map.
8. **Given** a multi-value filter (e.g., incident type), **When** the user clicks "Select All", **Then** all values in that filter category are selected.
9. **Given** filters are applied, **When** the map updates, **Then** a count of visible incidents is displayed to the user.

---

### User Story 3 — View Incident Details from Map (Priority: P3)

An emergency coordinator spots a marker of interest on the map and clicks it. A detail sidebar slides in from the right, displaying the incident's full information: title, incident type, severity, status, affected jurisdictions, start date, PPRR phase, and incident level. The sidebar also provides a prominent link to navigate to the incident's dedicated workspace page for deeper analysis and coordination. The coordinator can close the sidebar to return to the full map view.

**Why this priority**: Clicking through to incident details closes the loop between spatial awareness and operational action. Without this, users would need to leave the map to look up specific incidents, breaking their workflow.

**Independent Test**: Can be tested by clicking any map marker and verifying the detail sidebar appears with correct incident information and a working link to the incident workspace. Delivers incident drill-down as a standalone capability.

**Acceptance Scenarios**:

1. **Given** incident markers are displayed on the map, **When** the user clicks a marker, **Then** a detail sidebar appears showing the incident's title, type, severity, status, affected jurisdictions, start date, PPRR phase, and incident level.
2. **Given** the detail sidebar is open, **When** the user clicks the link to the incident workspace, **Then** they are navigated to the incident's dedicated page at `/incidents/[incidentId]`.
3. **Given** the detail sidebar is open, **When** the user clicks the close button, **Then** the sidebar closes and the full map view is restored.
4. **Given** the detail sidebar is open, **When** the user clicks a different marker on the map, **Then** the sidebar updates to show the newly selected incident's details.
5. **Given** the incident has a severity of Emergency Warning, **When** the detail sidebar renders, **Then** the severity is displayed with the corresponding red Australian Warning System colour.

---

### User Story 4 — Search Incidents by Keyword (Priority: P4)

An emergency coordinator is looking for a specific incident by name or description. They type a keyword into the search bar at the top of the Disasters page. The map updates to show only incidents whose titles match the search term. The search works in conjunction with any active filters (results must match both the search term and the applied filters).

**Why this priority**: Keyword search is a convenience feature for users who already know what they are looking for. It complements but does not replace the filter panel.

**Independent Test**: Can be tested by entering a known incident title into the search bar and verifying only matching incidents appear on the map. Delivers quick-access search as a standalone capability.

**Acceptance Scenarios**:

1. **Given** the search bar is visible, **When** the user types a keyword, **Then** the map updates to show only incidents whose title contains that keyword (case-insensitive).
2. **Given** the user has typed a search term, **When** filters are also active, **Then** only incidents matching BOTH the search term AND the active filters are displayed.
3. **Given** the user has typed a search term, **When** they clear the search bar, **Then** the map reverts to showing all incidents matching the current filters.
4. **Given** the user types a search term with no matching incidents, **When** the map updates, **Then** no markers are displayed and an informational message indicates no results were found.

---

### User Story 5 — Use Disaster Mapper on Mobile (Priority: P5)

A field officer accesses the Disasters page on a mobile device (phone or tablet). The interface adapts to the smaller viewport: the map occupies the full screen, the filter panel is accessible via a collapsible drawer or bottom sheet, and the incident detail sidebar adapts to a card or overlay format. All functionality available on desktop remains accessible on mobile.

**Why this priority**: Field officers frequently operate from mobile devices during disaster response. While desktop is the primary use case, mobile access ensures the tool is useful in the field where it matters most.

**Independent Test**: Can be tested by accessing the Disasters page on various mobile viewport sizes and verifying all features (map, filters, search, detail view) remain accessible and usable. Delivers mobile field access as a standalone capability.

**Acceptance Scenarios**:

1. **Given** the user accesses the Disasters page on a mobile device, **When** the page loads, **Then** the map fills the available viewport and is fully interactive (pan, zoom, tap).
2. **Given** a mobile viewport, **When** the user taps a control to open the filter panel, **Then** the filter panel appears as a collapsible drawer or bottom sheet that does not permanently obscure the map.
3. **Given** a mobile viewport, **When** the user taps a map marker, **Then** the incident detail view appears in an overlay or card format appropriate for the screen size.
4. **Given** a mobile viewport, **When** the user rotates the device, **Then** the layout adapts smoothly to the new orientation.

---

### Edge Cases

- **No matching incidents**: When filters or search return zero results, the map displays no markers and a message communicates "No incidents match your criteria" with an option to reset filters.
- **Incidents without location data**: Incidents that lack geographic coordinates are excluded from the map but are counted and disclosed via a notice (e.g., "3 incidents could not be mapped due to missing location data").
- **Marker clustering at high density**: When many incidents overlap geographically (e.g., 50+ incidents in the same region at low zoom), markers are grouped into clusters showing the count. Clicking a cluster zooms in or expands the cluster.
- **Map service unavailable**: If the mapping service fails to load, a fallback message is displayed with an option to retry, and the filter panel and search remain usable in a list-view fallback mode.
- **Slow or intermittent network**: If incident data takes longer than expected to load, a loading indicator is shown on the map. Partial data renders progressively as it becomes available.
- **Very large datasets (1,000+ incidents)**: The map handles large numbers of markers without freezing or significant frame-rate drops through clustering and progressive rendering. The API endpoint supports server-side pagination (default 200 per page); the initial view loads the most recent 500 incidents, with additional pages fetched progressively in the background.
- **Filter panel state persistence**: Filter state is persisted via URL query parameters (e.g., `/disasters?type=bushfire&severity=warning&year_start=2020`) so that filter configurations are shareable and bookmarkable. Navigating to a URL with query parameters restores the corresponding filter state.

## Requirements *(mandatory)*

### Functional Requirements

#### Map Display

- **FR-001**: System MUST display an interactive map centred on Australia using Azure Maps when the user navigates to the Disasters page. The Azure Maps account MUST be provisioned in the Australia East region via Bicep in `infra/`.
- **FR-002**: System MUST render each incident with location data as a marker on the map at its geographic coordinates.
- **FR-003**: Each marker MUST be colour-coded by the incident's severity using the Australian Warning System colours: yellow (#FFC107) for Advice, orange (#FF8C00) for Watch and Act, and red (#D32F2F) for Emergency Warning. Domain severity values map as follows: "advisory" → Advice (yellow), "watch" → Watch and Act (orange), "warning" and "emergency" → Emergency Warning (red). Both "warning" and "emergency" map to the red tier per the AWS nested model.
- **FR-003a**: Each severity tier MUST use a distinct marker shape in addition to colour for WCAG accessibility: circle for Advice, triangle for Watch and Act, and diamond for Emergency Warning.
- **FR-004**: System MUST support standard map interactions: pan, zoom, and click/tap on markers.
- **FR-005**: System MUST group overlapping markers into clusters using Azure Maps' built-in clustering with a pixel radius of 60px, showing count badges when markers would overlap at the current zoom level. Clicking a cluster MUST zoom to expand and reveal individual markers.

#### Filter Panel

- **FR-006**: System MUST provide a filter panel alongside the map with the following filter categories: date range, incident type, severity level, status, and PPRR phase.
- **FR-007**: The date range filter MUST allow users to select a start year and end year to bound which incidents are displayed.
- **FR-008**: The incident type filter MUST present toggles for all system incident types: Bushfire, Flood, Cyclone, Storm, Earthquake, Tsunami, Extreme Heat, Pandemic, and Other.
- **FR-009**: The severity filter MUST present options for the three Australian Warning System tiers: Advice (matching domain value "advisory"), Watch and Act (matching domain value "watch"), and Emergency Warning (matching domain values "warning" and "emergency").
- **FR-010**: The status filter MUST present options for: Monitoring, Active, Stabilising, Recovery, and Closed.
- **FR-011**: The PPRR phase filter MUST present options for: Prevention, Preparedness, Response, and Recovery.
- **FR-012**: Each multi-value filter MUST provide "Select All" and "Reset" controls.
- **FR-013**: Filters MUST combine using AND logic across filter categories — an incident must match all active filter criteria to be displayed. Within a multi-value filter category (e.g., incident type), values MUST combine with OR logic — an incident matching any selected value within that category satisfies that category's filter. Example: selecting Bushfire and Flood for type AND Active for status shows incidents that are (Bushfire OR Flood) AND Active.
- **FR-014**: The map MUST update to reflect the applied filters without requiring a full page reload.
- **FR-015**: System MUST display a count of currently visible incidents that updates as filters change.

#### Incident Detail Sidebar

- **FR-016**: System MUST display a detail sidebar when a user clicks/taps an incident marker.
- **FR-017**: The detail sidebar MUST display: incident title, incident type, severity (with Australian Warning System colour), status, affected jurisdictions, start date, PPRR phase, and incident level.
- **FR-018**: The detail sidebar MUST include a link that navigates the user to the incident's workspace page (`/incidents/[incidentId]`).
- **FR-019**: The detail sidebar MUST include a close control that dismisses the sidebar and restores the full map view.
- **FR-020**: When a user clicks a different marker while the sidebar is open, the sidebar MUST update to display the newly selected incident's details.

#### Search

- **FR-021**: System MUST provide a search bar at the top of the Disasters page for keyword search.
- **FR-022**: The search MUST filter incidents by matching the search term against incident titles (case-insensitive).
- **FR-023**: Search MUST combine with active filters — only incidents matching both the search term and all active filters are displayed.
- **FR-024**: Clearing the search bar MUST restore the map to showing all incidents matching the current filters.

#### Responsiveness & Layout

- **FR-025**: The Disasters page MUST be accessible at the `/disasters` route within the application.
- **FR-026**: The page MUST render within the application's standard shell layout with consistent navigation.
- **FR-027**: The layout MUST be responsive with a breakpoint at 768px. Above 768px (desktop): side panel layout with the filter panel alongside the map. Below 768px (mobile): full-screen map with a bottom sheet for filters and an overlay card for incident details.
- **FR-028**: The incident detail sidebar MUST adapt to mobile viewports, displaying as an overlay or card rather than a fixed sidebar.

#### Data & Error Handling

- **FR-029**: System MUST retrieve incident data via a new `GET /api/v1/incidents/map` endpoint on the FastAPI backend. This endpoint MUST support query parameters for all filter criteria (date range, type, severity, status, PPRR phase, keyword) and return incident data as a **GeoJSON FeatureCollection** (per constitution Section IV — interoperability standard). Each incident MUST be represented as a GeoJSON Feature with Point geometry and incident attributes in the `properties` object. The endpoint MUST support server-side pagination via `page` and `page_size` query parameters (default page size: 200). Incidents with status "rehearsal" MUST be excluded server-side by this endpoint.
- **FR-030**: Incidents without geographic coordinates MUST be excluded from the map and disclosed via a notice indicating how many incidents could not be mapped.
- **FR-031**: If the map service fails to load, system MUST display a fallback message with a retry option and provide incident data in a sortable table with columns: Title, Type, Severity, Status, Date, and Location. The table MUST include the same filter controls available on the map view.
- **FR-032**: While incident data is loading, system MUST display a loading indicator on the map area.
- **FR-033**: The Disasters page is a read-only situational awareness view. It MUST NOT create, modify, or delete incidents. All operational actions are performed on the incident workspace page (`/incidents/[incidentId]`), linked from the detail sidebar. No agent handoff events are emitted from this page.
- **FR-034**: The Disasters page MUST display a "Last updated" timestamp indicating when the displayed incident data was last fetched from the server. Users refresh the page or re-apply filters to see updated data; no real-time (WebSocket) push updates are required for this initial version.
- **FR-035**: The initial map view MUST load the most recent 500 incidents. The frontend MUST progressively request additional pages (200 per page) in the background to populate the full dataset without blocking the initial render.

#### Accessibility (WCAG 2.1 AA)

- **FR-036**: The Disasters page MUST support keyboard navigation through map markers. Users MUST be able to Tab between markers and activate the detail sidebar via Enter or Space.
- **FR-037**: Filter changes MUST trigger screen reader announcements via ARIA live regions indicating the updated incident count (e.g., "Showing 42 incidents").
- **FR-038**: All marker colours MUST meet WCAG 2.1 AA contrast ratio requirements (minimum 3:1 against the map background). The distinct marker shapes (circle, triangle, diamond) per FR-003a provide a non-colour-dependent differentiator.

### Non-Functional Requirements

#### Data Sovereignty

- **NFR-001**: All incident data MUST be stored and served from Azure Australia East region. The Azure Maps account MUST be provisioned in Australia East. Map tile requests MUST be served via Azure Maps' Australia-region endpoints only. No third-party map tile CDNs outside Australia are permitted. This aligns with constitution Section IV (data sovereignty — all data within Australian borders).

#### Observability

- **NFR-002**: The `/disasters` page and `GET /api/v1/incidents/map` endpoint MUST emit structured telemetry to Azure Monitor / Application Insights. The following named metrics MUST be emitted:
  - `disaster_mapper.page_load_ms` — time from navigation to interactive map render
  - `disaster_mapper.filter_apply_ms` — latency from filter selection to map update completion
  - `disaster_mapper.map_render_ms` — time to render/re-render map markers after data load
  - `disaster_mapper.api_error_rate` — error rate for map service and API failures (5xx, timeouts, tile load failures)
  - `disaster_mapper.incidents_displayed` — gauge of currently visible incident count

#### Reliability

- **NFR-003**: The map MUST degrade gracefully per constitution Section V (graceful degradation). If Azure Maps tile service is unavailable, the list-view fallback (FR-031) MUST activate within 5 seconds. If the `/api/v1/incidents/map` endpoint is unavailable, a user-facing error message MUST be displayed with a retry option.

### Key Entities

- **Incident**: The primary entity displayed on the map. Represents a disaster event with attributes: unique identifier, title, incident type (one of nine hazard categories), status (monitoring through closed), severity (advisory through emergency), affected jurisdiction identifiers, participating organisation identifiers, start date/time, PPRR phase, and incident level (1–3). The Incident model is extended with an optional `location` field stored as a **GeoJSON Point geometry** (`{ "type": "Point", "coordinates": [longitude, latitude] }`) for geographic map placement, per constitution Section IV (interoperability — GeoJSON standard). Not all existing incidents will have the `location` field populated.
- **Jurisdiction**: A geographic or administrative region affected by an incident. Incidents reference one or more jurisdictions, which correspond to Australian states, territories, or local government areas.

## Assumptions

- Incidents in the data store include geographic location data as GeoJSON Point geometry for the majority of records. Incidents lacking location data are a known minority.
- All incident data and Azure Maps tiles are served exclusively from Azure Australia East region. No third-party map tile CDNs outside Australia are used, per constitution Section IV (data sovereignty).
- The Disasters page does not require real-time (WebSocket) push updates for this initial version. Users refresh or re-apply filters to see new incidents. A "Last updated" timestamp is displayed.
- The Disasters page is a read-only situational awareness view. It does not create, modify, or delete incidents. It links to the incident workspace (`/incidents/[incidentId]`) for operational actions. No agent handoff events are emitted.
- The year range for the date filter spans from the earliest incident in the system to the current year. The range dynamically adapts as new incidents are added.
- The system's existing authentication and authorisation controls apply to the Disasters page — no additional access-control logic is required for this feature.
- The existing domain model's `severity` field values map to the Australian Warning System tiers: "advisory" → Advice (yellow #FFC107), "watch" → Watch and Act (orange #FF8C00), "warning" → Emergency Warning (red #D32F2F), "emergency" → Emergency Warning (red #D32F2F). Both "warning" and "emergency" map to the red tier per the AWS nested model, as both represent immediate danger.
- The `rehearsal` status (used for simulation scenarios) is excluded from the Disasters page to avoid confusion with real incidents. Rehearsal incidents are filtered out server-side by the `GET /api/v1/incidents/map` endpoint. Only operational statuses are shown.
- The mapping service account and credentials will be provisioned as part of the infrastructure setup for this feature. Azure Maps is the mapping service (per constitution Section VIII, Azure-native services preferred). The Azure Maps account will be provisioned in Australia East region via Bicep in `infra/`.
- A new `GET /api/v1/incidents/map` endpoint will be created on the FastAPI backend to support the query parameters needed for filtering (date range, type, severity, status, PPRR phase, keyword search) and return incident data as a GeoJSON FeatureCollection with Point geometry per incident. The endpoint supports server-side pagination (default page size: 200). Existing endpoints are not modified.

## Clarifications

### Session 2026-04-13

- Q: Which mapping service should the Disaster Mapper UI use? → A: Azure Maps (constitution Section VIII mandates Azure-native services). Provisioned in Australia East via Bicep in `infra/`.
- Q: How do the 4 domain severity values map to the 3 AWS tiers? → A: "advisory" → Advice (Yellow #FFC107), "watch" → Watch and Act (Orange #FF8C00), "warning" and "emergency" → Emergency Warning (Red #D32F2F). Both map to red per the AWS nested model.
- Q: What specific marker shapes differentiate severity tiers beyond colour for accessibility? → A: Circle for Advice, triangle for Watch and Act, diamond for Emergency Warning (WCAG compliance).
- Q: Should the existing incident API be extended or a new endpoint created for map data? → A: New `GET /api/v1/incidents/map` endpoint on FastAPI backend with query parameters for all filter criteria. Existing endpoints unchanged.
- Q: Should filter state be persisted via URL query parameters or session storage? → A: URL query parameters for shareability and bookmarkability (e.g., `/disasters?type=bushfire&severity=warning&year_start=2020`).

### Session 2026-04-13 (Pass 2)

- Q: Should the incident location field use flat lat/lon or GeoJSON per constitution interoperability standards? → A: GeoJSON Point geometry (`{ "type": "Point", "coordinates": [lon, lat] }`). API responses use GeoJSON FeatureCollection. Constitution Section IV mandates GeoJSON.
- Q: Must Azure Maps tiles and incident data be served from within Australia (data sovereignty)? → A: Yes. Azure Maps account in Australia East only. All incident data from Australia East. No third-party map tile CDNs outside Australia.
- Q: What observability telemetry must the Disasters page and API emit? → A: Named metrics to Azure Monitor / Application Insights: `disaster_mapper.page_load_ms`, `disaster_mapper.filter_apply_ms`, `disaster_mapper.map_render_ms`, `disaster_mapper.api_error_rate`, `disaster_mapper.incidents_displayed`.
- Q: What WCAG 2.1 AA accessibility requirements apply beyond marker shapes? → A: Keyboard navigation through markers (Tab + Enter/Space), screen reader announcements for filter changes (ARIA live regions), minimum 3:1 contrast ratio for marker colours against map background.
- Q: Is the Disasters page read-only or can it modify incidents? → A: Read-only situational awareness view. Links to `/incidents/[incidentId]` for operational actions. No agent handoff events emitted.
- Q: Does the map require real-time WebSocket updates? → A: No. Users refresh or re-apply filters. A "Last updated" timestamp is displayed. WebSocket may be added in a future iteration.
- Q: What is the maximum dataset scope and pagination strategy? → A: Server-side pagination with default page size of 200. Initial view loads most recent 500 incidents. Frontend progressively requests additional pages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see all mapped incidents rendered on the Disasters page within 3 seconds of navigation.
- **SC-002**: Users can apply any combination of filters and see updated map markers within 1 second.
- **SC-003**: Users can access full details of any incident from its map marker in 2 clicks or taps or fewer.
- **SC-004**: The map displays 500 or more simultaneous incident markers without visible performance degradation (no dropped frames or frozen interactions).
- **SC-005**: 90% of first-time users can locate a specific incident using filters or search within 30 seconds during usability testing.
- **SC-006**: All three Australian Warning System severity tiers are visually distinguishable from each other on the map using distinct marker shapes in addition to colour: circle for Advice, triangle for Watch and Act, and diamond for Emergency Warning (WCAG accessibility compliance).
- **SC-007**: All features (map, filters, search, detail view) are usable on mobile viewports (360px width and above) without horizontal scrolling or truncated controls.
- **SC-008**: When the map service is unavailable, users can still view incident data via the list-view fallback within 5 seconds.
- **SC-009**: All five observability metrics (`disaster_mapper.page_load_ms`, `disaster_mapper.filter_apply_ms`, `disaster_mapper.map_render_ms`, `disaster_mapper.api_error_rate`, `disaster_mapper.incidents_displayed`) are emitted to Azure Monitor / Application Insights and queryable in Log Analytics within 60 seconds of the triggering event.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-052**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-053**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-054** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-018**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-018.md` (created in feature 028 polish).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-058** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (ux-designer, accessibility-tester, operations-officer) sign off on country-specific calibration.
- **SCP-059**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-060**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.

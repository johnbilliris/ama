# Feature Specification: Multi-Jurisdiction Filter for Preparedness Page

**Feature Branch**: `022-multi-jurisdiction-filter`  
**Created**: 2025-07-15  
**Status**: Draft  
**Input**: User description: "Enhance the preparedness page to allow end users to select one or more jurisdictions from a dropdown list, dynamically filtering Organisation Catalog, Framework Catalog, and rehearsal replay data based on the selected jurisdictions instead of hardcoded NSW."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Select Jurisdictions to View Organisations and Frameworks (Priority: P1)

As a Resilience Planner preparing for cross-boundary events, I need to select one or more Australian jurisdictions on the preparedness page so that the Organisation Catalog and Framework Catalog display only the agencies and frameworks relevant to my selected jurisdictions.

**Why this priority**: This is the core capability that unblocks all other preparedness planning. Without multi-jurisdiction selection, the page is limited to a single hardcoded jurisdiction and cannot support cross-boundary coordination — a fundamental requirement of the national PPRR framework and multi-agency design principles.

**Independent Test**: Can be fully tested by loading the preparedness page, selecting one or more jurisdictions from the dropdown, and verifying that the Organisation Catalog and Framework Catalog update to show data matching those jurisdictions.

**Acceptance Scenarios**:

1. **Given** the preparedness page is loaded, **When** the user selects "VIC" from the jurisdiction selector, **Then** the Organisation Catalog displays only organisations associated with Victoria and the Framework Catalog displays only frameworks applicable to Victoria.
2. **Given** the preparedness page is loaded, **When** the user selects both "NSW" and "QLD", **Then** both catalogs display combined data from New South Wales and Queensland without duplicates.
3. **Given** "Commonwealth" is selected alongside one or more state/territory jurisdictions, **When** the catalogs load, **Then** Commonwealth-level organisations (e.g., nationally operating agencies) appear alongside the state/territory organisations.
4. **Given** no jurisdictions are selected, **When** the user views the catalogs, **Then** the page displays an empty state message prompting the user to select at least one jurisdiction.

---

### User Story 2 — Run Rehearsal Replay Across Selected Jurisdictions (Priority: P2)

As a Resilience Planner conducting scenario rehearsals, I need the rehearsal replay to use the jurisdictions I have selected so that the generated findings and coordination gap analysis reflect the cross-jurisdictional operating environment I am planning for.

**Why this priority**: Rehearsal replay is valuable but depends on the jurisdiction selection from P1. Once jurisdictions are selectable, passing them to the replay gives planners realistic multi-jurisdiction scenario outputs critical for identifying cross-boundary coordination gaps.

**Independent Test**: Can be fully tested by selecting multiple jurisdictions, choosing a scenario type, clicking "Run rehearsal replay", and verifying the findings and coordination gaps reflect all selected jurisdictions.

**Acceptance Scenarios**:

1. **Given** the user has selected "NSW" and "VIC" as jurisdictions, **When** they click "Run rehearsal replay" with scenario type "bushfire", **Then** the replay request includes both "nsw" and "vic" as jurisdiction identifiers, and the findings and coordination gaps reflect cross-jurisdictional analysis.
2. **Given** the user has selected a single jurisdiction "SA", **When** they run a rehearsal replay, **Then** the replay uses only "sa" and returns South Australia-specific findings.
3. **Given** no jurisdictions are selected, **When** the user attempts to run a rehearsal replay, **Then** the replay button is disabled with a message indicating that at least one jurisdiction must be selected.

---

### User Story 3 — View All Nine Jurisdictions in the Selector (Priority: P3)

As an Incident Commander coordinating a Level 2–3 multi-state disaster response, I need the jurisdiction selector to present all nine Australian jurisdictions (eight states/territories plus Commonwealth) so that I can plan across any combination of jurisdictions relevant to the incident.

**Why this priority**: Completeness of the jurisdiction list is necessary for full national coverage but is less urgent than the core selection and filtering mechanics. An incomplete list still delivers partial value; the complete list ensures national interoperability.

**Independent Test**: Can be fully tested by opening the jurisdiction selector and verifying all nine jurisdictions are listed with their full display names and identifiers.

**Acceptance Scenarios**:

1. **Given** the preparedness page is loaded, **When** the user opens the jurisdiction selector, **Then** the following nine jurisdictions are available for selection: Commonwealth of Australia, New South Wales, Victoria, Queensland, South Australia, Western Australia, Tasmania, Australian Capital Territory, and Northern Territory.
2. **Given** the jurisdiction selector is open, **When** the user reviews the list, **Then** each jurisdiction displays its full name (e.g., "New South Wales") and can be individually selected or deselected.

---

### User Story 4 — Support Multi-Jurisdiction Filtering in the Data Layer (Priority: P4)

As a system, the data retrieval layer must accept multiple jurisdiction identifiers for organisations and frameworks so that the preparedness page can request data filtered by any combination of jurisdictions in a single request.

**Why this priority**: This is the enabling backend capability. The current data layer accepts a single jurisdiction identifier. Supporting multiple identifiers is necessary for P1 to function but is lower priority as a user story because it is not directly user-facing.

**Independent Test**: Can be tested by sending a data request with multiple jurisdiction identifiers (e.g., "nsw,vic") and verifying the response includes records matching any of the specified jurisdictions.

**Acceptance Scenarios**:

1. **Given** a request for organisations filtered by jurisdictions "nsw" and "qld", **When** the data layer processes the request, **Then** it returns all organisations whose jurisdiction associations include "nsw" or "qld".
2. **Given** a request for frameworks filtered by jurisdictions "tas" and "act", **When** the data layer processes the request, **Then** it returns all frameworks applicable to Tasmania or the Australian Capital Territory.
3. **Given** a request with no jurisdiction identifiers, **When** the data layer processes the request, **Then** it returns an empty result set (not a default fallback to any specific jurisdiction).

---

### Edge Cases

- What happens when the user selects all nine jurisdictions? The system must handle the full dataset without performance degradation or display issues.
- What happens when a jurisdiction has no organisations or frameworks? The catalogs should display an appropriate empty state for that jurisdiction without errors.
- What happens when the user rapidly toggles jurisdictions on and off? The system MUST debounce API calls with a 300ms delay, ensuring only the final selection state triggers a data refresh. Stale in-flight responses MUST be discarded if a newer request has been issued.
- What happens when the data request fails for one or more jurisdictions? The affected catalog section MUST display an inline error message with a retry action. Stale or partial results MUST NOT be shown. The jurisdiction selector remains operational so users can adjust their selection.
- What happens when a new jurisdiction is added to the seed data in the future? The jurisdiction list should be dynamically sourced from the data layer, not hardcoded in the interface.
- What happens when the user changes jurisdiction selection after a rehearsal replay has completed? The previous replay results MUST be cleared and a notice displayed indicating the replay was run for different jurisdictions. The user must re-run the replay for updated results. Stale cross-jurisdictional findings MUST NOT be displayed alongside catalogs filtered for a different set of jurisdictions.
- What happens when URL query parameters contain invalid or unrecognised jurisdiction identifiers? The system MUST silently ignore invalid identifiers, retaining only valid ones for the selection. If all identifiers are invalid, the page MUST fall through to the empty state (no jurisdictions selected). This aligns with the Constitution's graceful degradation principle.

## Clarifications

### Session 2026-04-18

- Q: What accessibility standard must the multi-select jurisdiction control meet? → A: WCAG 2.1 AA — keyboard navigable and screen-reader compatible.
- Q: Must jurisdiction data queries be scoped by tenant_id per the platform's tenant isolation model? → A: Yes — tenant_id derived from Entra ID claims is required in all data layer queries (per specs 007, 021).
- Q: What debounce interval should be applied to jurisdiction selection changes before triggering API calls? → A: 300ms debounce to avoid excessive API calls during rapid toggling.
- Q: What should the UI display while catalog data is loading after a jurisdiction selection change? → A: Show inline loading indicator per catalog; do not display stale previous results.
- Q: What specific behavior should occur when a data request fails? → A: Show inline error with retry action per catalog; do not show stale data; jurisdiction selector remains functional (Constitution principle 5: graceful degradation).

### Session 2026-04-18 (Pass 2)

- Q: How are frameworks linked to jurisdictions for filtering, given OperatingFramework has no jurisdiction field? → A: Filter via FrameworkAssignment junction entity — a framework is "applicable to" a jurisdiction when a FrameworkAssignment record links that OperatingFramework to the jurisdiction (per spec 018 data model).
- Q: Should jurisdiction selection persist across page loads, consistent with the URL-driven filter state pattern from spec 020? → A: Yes — persist selection in URL query parameters (e.g., /preparedness?jurisdictions=nsw,vic) enabling shareable and bookmarkable views, per Constitution principles 3 (Collaborative) and 9 (Communication).
- Q: Should the jurisdiction selector include "Select All" and "Clear All" controls, consistent with spec 020 FR-012's multi-value filter pattern? → A: Yes — include both controls. Essential for Level 3 national response coordination where all nine jurisdictions must be quickly selectable.
- Q: What happens to rehearsal replay results when jurisdiction selection changes after a replay has completed? → A: Clear replay results and display a notice that the previous replay used different jurisdictions; prompt user to re-run. Consistent with the no-stale-data principle in FR-012/FR-013.
- Q: How should the system handle invalid or unrecognised jurisdiction identifiers in URL query parameters? → A: Silently ignore invalid IDs, retaining only valid ones. If all IDs are invalid, fall through to empty state. Per Constitution principle 5 (graceful degradation).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The preparedness page MUST display a multi-select jurisdiction control that allows users to select one or more jurisdictions from the complete list of nine Australian jurisdictions. The control MUST include "Select All" and "Clear All" actions, consistent with spec 020's multi-value filter pattern. The control MUST be keyboard navigable and screen-reader compatible, conforming to WCAG 2.1 AA.
- **FR-002**: The Organisation Catalog MUST dynamically filter and display organisations based on the currently selected jurisdictions, showing only organisations associated with at least one of the selected jurisdictions.
- **FR-003**: The Framework Catalog MUST dynamically filter and display frameworks based on the currently selected jurisdictions, showing only frameworks linked to at least one of the selected jurisdictions via FrameworkAssignment records (per spec 018 data model — OperatingFramework has no direct jurisdiction field).
- **FR-004**: The rehearsal replay function MUST pass the currently selected jurisdictions to the scenario replay request instead of using a hardcoded jurisdiction list.
- **FR-005**: The data layer MUST support accepting multiple jurisdiction identifiers in a single request for both organisations and frameworks, returning the union of matching records. All data layer queries MUST include the tenant_id derived from the authenticated user's Entra ID claims, consistent with the platform's tenant isolation model (specs 007, 021).
- **FR-006**: When no jurisdictions are selected, the preparedness page MUST display an empty state prompting the user to select at least one jurisdiction, and the rehearsal replay button MUST be disabled.
- **FR-007**: The jurisdiction selector MUST source its list of available jurisdictions from the data layer rather than hardcoding the options, ensuring new jurisdictions added to seed data are automatically reflected.
- **FR-008**: The jurisdiction selector MUST display the full human-readable name for each jurisdiction (e.g., "New South Wales" not "nsw"), while using the jurisdiction identifier internally for data requests.
- **FR-009**: Combined results across multiple jurisdictions MUST NOT contain duplicate entries — if an organisation or framework belongs to multiple selected jurisdictions, it MUST appear only once.
- **FR-010**: Changing the jurisdiction selection MUST update the Organisation Catalog and Framework Catalog without requiring a full page reload.
- **FR-011**: The rehearsal replay button MUST be disabled and display a user-friendly message when no jurisdictions are selected.
- **FR-012**: When a data request fails, the system MUST display an inline error message with a retry action within the affected catalog section, without showing stale or partial data. The jurisdiction selector MUST remain functional so users can adjust their selection or retry. This aligns with the Constitution's graceful degradation principle.
- **FR-013**: While catalog data is loading after a jurisdiction selection change, the UI MUST display an inline loading indicator within each affected catalog section. Previous results MUST be cleared immediately to avoid displaying stale data.
- **FR-014**: The jurisdiction selection MUST be persisted in URL query parameters so that preparedness views are shareable and bookmarkable, consistent with the URL-driven filter state pattern from spec 020. Navigating to a URL with jurisdiction query parameters MUST restore the corresponding selection. Invalid or unrecognised jurisdiction identifiers in the URL MUST be silently ignored; only valid identifiers are applied. If all identifiers are invalid, the page MUST default to the empty state. When no query parameters are present, the page MUST also default to the empty state (no jurisdictions selected).
- **FR-015**: When the jurisdiction selection changes after a rehearsal replay has completed, the displayed replay results MUST be cleared and a notice MUST inform the user that the previous replay was run for different jurisdictions. The user MUST re-run the replay for updated results. This prevents misleading cross-jurisdictional analysis.

### Key Entities

- **Jurisdiction**: Represents an Australian government level (Commonwealth, state, or territory). Key attributes: unique identifier, full display name, administrative level (commonwealth/state/territory), parent jurisdiction, and active/inactive status.
- **Organisation**: Represents an emergency management agency or body. Belongs to one or more jurisdictions via a list of jurisdiction identifiers. Key attributes: name, category, operating role, authority level, and status.
- **Operating Framework**: Represents a preparedness or operating framework applicable to organisations within specific jurisdictions. Key attributes: name, framework type, span of control guidance, and jurisdiction applicability. Note: OperatingFramework has no direct jurisdiction field — jurisdiction applicability is determined via **FrameworkAssignment** records that link a framework to one or more jurisdictions (per spec 018).
- **Framework Assignment**: Junction entity linking an OperatingFramework to a Jurisdiction. Used to determine which frameworks are applicable to a given set of selected jurisdictions. Key attributes: framework reference, jurisdiction identifier, and assignment context.

### Non-Functional Requirements

- **NFR-001**: The multi-select jurisdiction control MUST conform to WCAG 2.1 AA, including full keyboard navigation (Tab/Shift-Tab to focus, Space/Enter to toggle, Arrow keys to navigate options) and appropriate ARIA roles/labels for screen readers.
- **NFR-002**: Jurisdiction selection changes MUST debounce API calls with a 300ms delay to prevent excessive requests during rapid toggling. Only the final selection state after the debounce window MUST trigger a data refresh.

## Assumptions

- The existing nine jurisdictions (Commonwealth, NSW, VIC, QLD, SA, WA, TAS, ACT, NT) from the seed data represent the complete initial set. The system must accommodate future additions without code changes.
- Organisations may belong to multiple jurisdictions (the domain model already supports this with a list of jurisdiction identifiers). Filtering should return organisations that match **any** of the selected jurisdictions (OR logic, not AND).
- There is no user-specific jurisdiction preference or saved state required for this feature. However, the current jurisdiction selection MUST be persisted in URL query parameters (e.g., `/preparedness?jurisdictions=nsw,vic`) so that views are shareable and bookmarkable, consistent with the URL-driven filter state pattern established in spec 020. If no query parameters are present, the page defaults to no jurisdictions selected (empty state).
- The default initial state is no jurisdictions selected, showing an empty state prompt, rather than pre-selecting a default jurisdiction. This avoids bias toward any single jurisdiction and encourages deliberate selection.
- Performance is acceptable for the current data volume (approximately 40–60 organisations and a similar number of frameworks across all nine jurisdictions). Pagination or lazy loading is not required at this stage.
- Commonwealth organisations operate nationally and should appear whenever "Commonwealth" is selected. They do not automatically appear when only state/territory jurisdictions are selected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select any combination of the nine jurisdictions and see updated catalog results within 2 seconds of changing their selection.
- **SC-002**: 100% of the nine Australian jurisdictions are available for selection in the jurisdiction control.
- **SC-003**: Rehearsal replay results accurately reflect the selected jurisdictions, with findings and coordination gaps spanning all selected jurisdictions rather than a single hardcoded one.
- **SC-004**: No duplicate organisations or frameworks appear when multiple jurisdictions are selected that share common agencies.
- **SC-005**: Users who need to plan across multiple jurisdictions can complete their preparedness review without manually switching between single-jurisdiction views, reducing the number of interactions required by at least 50% compared to the current single-jurisdiction workflow.
- **SC-006**: The empty state when no jurisdictions are selected clearly communicates the required action, with 90% of first-time users successfully selecting jurisdictions without external guidance.

# Feature Specification: Governance Dashboard

**Feature Branch**: `021-governance-dashboard`  
**Created**: 2025-07-15  
**Status**: Draft  
**Input**: User description: "Build a comprehensive Governance Dashboard into the AMA web application that provides a unified, role-aware view of governance health, compliance status, audit trails, operational readiness, and recovery progress across the entire disaster response hub."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executive Governance Health Overview (Priority: P1)

An Executive Leader or Incident Commander opens the Governance Dashboard and immediately sees a high-level governance health score, constitutional compliance status across all 10 mandatory gates, count of active incidents, overall resource utilisation, and a strategic risk summary. They can identify governance gaps at a glance and drill down into any area that shows non-compliance or elevated risk. This is the "single pane of glass" that demonstrates the platform's governance posture to senior leadership and inter-government liaisons.

**Why this priority**: The executive summary view is the foundation of the entire dashboard — it aggregates governance signals from every downstream data source and provides the unified entry point. Without it, no other view has meaningful context. It directly satisfies Constitution Gate 4 (transparency and auditability) and Gate 10 (governance and quality gates).

**Independent Test**: Can be fully tested by navigating to the governance dashboard URL and verifying that the health score, compliance indicators, incident count, resource utilisation gauge, and risk summary render with live data. Delivers immediate strategic oversight value to executive users.

**Acceptance Scenarios**:

1. **Given** the user has an Executive Leader or Incident Commander role, **When** they navigate to the Governance Dashboard, **Then** they see a governance health score (0–100), constitutional compliance status for all 10 gates (compliant/non-compliant/partially compliant), active incident count, resource utilisation percentage, and a strategic risk summary (counts by severity level).
2. **Given** any constitutional gate shows non-compliant status, **When** the user views the executive summary, **Then** the non-compliant gate is visually highlighted with a severity indicator and a link to the detailed compliance view.
3. **Given** the dashboard data is loading, **When** the user first arrives, **Then** they see skeleton placeholders for each widget that resolve within 3 seconds, and any widget that fails to load displays a graceful error state with a retry option.
4. **Given** a backend data source is unavailable, **When** the user views the dashboard, **Then** the affected widgets show a "data unavailable" indicator with the last-known timestamp, while unaffected widgets continue to display current data.

---

### User Story 2 - Compliance Matrix and Assessment Tracking (Priority: P1)

An Observer/Auditor or Executive Leader navigates to the Compliance View to inspect the full data source compliance matrix. They see every registered data source with its current constitutional assessment status, compliance level, any active grace periods, and governance gaps. They can filter by compliance status, sort by assessment date, and drill into individual data source details to review assessment history and remediation actions.

**Why this priority**: Compliance is the core governance function. This view directly enables Constitution Gate 4 (auditability) and Gate 10 (quality gates) by making compliance status transparent and verifiable. Auditors cannot perform their role without this capability.

**Independent Test**: Can be fully tested by viewing the compliance matrix, verifying data source rows match the governance registry, filtering by non-compliant status, and drilling into a specific data source to confirm assessment history is displayed.

**Acceptance Scenarios**:

1. **Given** the user has an Observer/Auditor role, **When** they open the Compliance View, **Then** they see a matrix of all registered data sources with columns for: source name, compliance status (compliant/non-compliant/pending/grace period), last assessment date, next assessment due date, and governance gap count.
2. **Given** a data source has an active grace period, **When** it appears in the compliance matrix, **Then** it displays the grace period expiry date, reason for the grace period, and a countdown indicator.
3. **Given** the user filters the compliance matrix by "non-compliant" status, **When** results are displayed, **Then** only data sources with non-compliant assessments appear, sorted by most overdue assessment first.
4. **Given** the user selects a specific data source row, **When** the detail panel opens, **Then** it shows the full assessment history (date, assessor, result, notes), current remediation actions, and links to related audit trail entries.

---

### User Story 3 - Searchable Audit Trail (Priority: P1)

An Observer/Auditor needs to investigate a specific governance decision. They open the Audit Trail View and search for events by date range, actor, action type, or affected entity. They can trace the full decision chain from initial trigger through approvals to final action, verify evidence integrity, and export audit records for external compliance reporting.

**Why this priority**: The audit trail is a constitutional non-negotiable (Gate 4 — every action, recommendation, and decision must be logged with provenance and rationale). Without a searchable, filterable audit interface, the platform cannot demonstrate compliance to regulators or satisfy observer/auditor needs.

**Independent Test**: Can be fully tested by searching the audit trail for a known governance event, verifying the decision chain is complete, and confirming export functionality produces a valid report.

**Acceptance Scenarios**:

1. **Given** the user has an Observer/Auditor role, **When** they open the Audit Trail View, **Then** they see a chronological list of governance events with columns for: timestamp, actor, action type, affected entity, outcome, and provenance reference.
2. **Given** the user enters a search query (e.g., actor name, date range, action type), **When** they execute the search, **Then** results are filtered to match the query within 2 seconds and display the total result count.
3. **Given** the user selects an audit event, **When** the detail panel opens, **Then** it shows the full decision chain: triggering event, intermediate approvals (with approver and timestamp), final action, rationale text, and evidence integrity indicator (verified/unverified).
4. **Given** the user selects one or more audit records, **When** they choose the export action, **Then** the system generates a downloadable report containing the selected records with all provenance metadata preserved.

---

### User Story 4 - Operational Readiness Assessment (Priority: P2)

A Resilience Planner or Planning Officer opens the Operational Readiness View to assess the organisation's preparedness posture. They see the current PPRR (Prevention, Preparedness, Response, Recovery) phase status, emergency plan endorsement and review status, simulation exercise completion rates, capability gap tracking, and AIIMS role coverage percentages. They can identify readiness gaps and prioritise preparedness activities.

**Why this priority**: Operational readiness is the proactive governance function — it prevents governance failures rather than just detecting them. This view supports Constitution Gate 9 (PPRR and shared responsibility) and is essential for resilience planners to maintain preparedness between incidents.

**Independent Test**: Can be fully tested by viewing PPRR phase indicators, verifying emergency plan statuses match their lifecycle records, and confirming exercise completion rates calculate correctly from simulation data.

**Acceptance Scenarios**:

1. **Given** the user has a Resilience Planner role, **When** they open the Operational Readiness View, **Then** they see: PPRR phase indicators with current phase highlighted, emergency plan count by lifecycle status (Draft, InConsultation, UnderReview, Endorsed, Activated, PostEventReview, Superseded) with overdue-review flags, exercise completion rate as a percentage, capability gap count, and AIIMS role coverage percentage.
2. **Given** an emergency plan has an expired review date, **When** it appears in the readiness view, **Then** it is visually flagged as overdue with the number of days past due.
3. **Given** AIIMS role coverage is below 100%, **When** the user views the role coverage widget, **Then** they see which specific roles are unassigned or under-staffed.
4. **Given** simulation exercise data is available, **When** the user views exercise completion rates, **Then** they see rates broken down by exercise type, with the most recent exercise date and overall readiness score.

---

### User Story 5 - Recovery Progress Tracking (Priority: P2)

An Executive Leader or Resilience Planner navigates to the Recovery Dashboard View to monitor recovery progress across the five recovery domains: overarching (resilience & sustainability), social, economic, built, and natural. They see outcome indicators, activity completion rates, community recovery indicators, and M&E (Monitoring and Evaluation) framework results. They can track whether recovery programmes are meeting their targets and identify domains that are falling behind.

**Why this priority**: Recovery tracking is a constitutional requirement (Gate 7 — recovery support with 6 principles and 5 domains including overarching). This view closes the governance loop by tracking outcomes after incident response, which is essential for demonstrating long-term effectiveness.

**Independent Test**: Can be fully tested by viewing recovery domain progress bars, verifying indicator values match recovery catalogue data, and confirming M&E outcome displays aggregate correctly.

**Acceptance Scenarios**:

1. **Given** recovery data exists for an active or recent incident, **When** the user opens the Recovery Dashboard View, **Then** they see progress indicators for each of the five recovery domains (overarching, social, economic, built, natural) expressed as percentage complete with trend direction. The overarching domain appears as a cross-cutting summary row.
2. **Given** the user selects a specific recovery domain, **When** the detail panel opens, **Then** it shows: outcome targets, activity completion rates, community indicators (quantitative and qualitative), and M&E framework evaluation results.
3. **Given** a recovery domain is below its target trajectory, **When** the user views the summary, **Then** it is flagged with a warning indicator and shows the variance from target.
4. **Given** no recovery data exists (no active recovery programmes), **When** the user opens the Recovery Dashboard View, **Then** they see an empty state message indicating no active recovery programmes with a link to the recovery catalogue.

---

### User Story 6 - Risk Register and Warning Compliance (Priority: P2)

A Risk Manager or Incident Commander opens the Risk & Warning View to review the active risk register, treatment status, alert compliance metrics, and warning system effectiveness. They see risk counts by severity, treatment closure rates, alert approval latency, AWS (Australian Warning System) tier usage, and broadcast reach metrics.

**Why this priority**: Risk and warning management are constitutional requirements (Gates 1, 5, and 10). This view enables real-time monitoring of whether the warning system meets compliance standards and whether identified risks are being actively managed.

**Independent Test**: Can be fully tested by viewing the risk register, verifying risk counts match assessment data, and confirming alert compliance metrics calculate correctly from warning system records.

**Acceptance Scenarios**:

1. **Given** the user has a Risk Manager role, **When** they open the Risk & Warning View, **Then** they see: total risk count by severity (extreme/high/medium/low), treatment closure rate as a percentage, average alert approval latency, AWS 3-tier usage breakdown (Advice/Watch and Act/Emergency Warning), broadcast reach percentage, and per-principle compliance rates for the 10 AWS warning principles with an overall principle compliance score.
2. **Given** extreme or high-severity risks exist with open treatments, **When** the user views the risk register, **Then** these risks are prominently displayed at the top with treatment due dates and responsible parties.
3. **Given** alert approval latency exceeds an acceptable threshold, **When** the user views the warning compliance section, **Then** they see a warning indicator with the specific alerts that exceeded the threshold and their actual approval times.
4. **Given** the user selects a specific risk entry, **When** the detail panel opens, **Then** it shows: risk description, likelihood, consequence, current treatments, treatment history, and links to related audit entries.

---

### User Story 7 - Role-Based Dashboard Personalisation (Priority: P3)

Any authenticated user with an AIIMS role assignment accesses the Governance Dashboard and sees a personalised workspace filtered to show the widgets, metrics, and views most relevant to their role. An Operations Officer sees deployment status and field safety prominently. A Public Information Officer sees alert approval times and broadcast reach. A Logistics Officer sees inventory and supply chain metrics. Users can access all views they are authorised for but their default landing experience is tailored.

**Why this priority**: Role-based personalisation improves usability across 10 distinct actor personas without requiring manual configuration. While all data is accessible through the standard views (P1/P2 stories), role-aware defaults reduce cognitive load and surface the most relevant information first.

**Independent Test**: Can be fully tested by logging in with different AIIMS role assignments and verifying that the default dashboard layout changes to highlight role-relevant widgets, while all authorised views remain accessible via navigation.

**Acceptance Scenarios**:

1. **Given** the user has an Operations Officer AIIMS role, **When** they open the Governance Dashboard, **Then** their default view highlights: deployment status, task completion metrics, staging utilisation, and field safety indicators, while other views remain accessible via navigation.
2. **Given** the user has a Public Information Officer role, **When** they open the dashboard, **Then** their default view highlights: alert approval latency, broadcast reach, multilingual coverage percentage, and accessibility compliance status.
3. **Given** the user has multiple AIIMS roles assigned, **When** they open the dashboard, **Then** they see a combined workspace showing widgets from all assigned roles, with the highest-authority role's widgets displayed first.
4. **Given** the user's AIIMS role assignment changes during an active session, **When** they refresh the dashboard, **Then** their default view updates to reflect the new role assignment.

---

### User Story 8 - Dashboard Interaction Audit Logging (Priority: P3)

Every user interaction with the Governance Dashboard — viewing a section, applying a filter, exporting data, drilling into details — is recorded in the audit trail. An Observer/Auditor can later review who accessed which governance information and when, supporting the platform's transparency and auditability requirements.

**Why this priority**: Constitution Gate 4 requires every action to be logged with provenance. Dashboard interactions are governance actions (accessing compliance data, viewing risk registers) and must be auditable. This is foundational to trust in the governance system itself.

**Independent Test**: Can be fully tested by performing dashboard actions (view, filter, export, drill-down) and then verifying corresponding audit entries appear in the audit trail with correct actor, timestamp, and action details.

**Acceptance Scenarios**:

1. **Given** a user navigates to any dashboard view, **When** the view loads, **Then** an audit entry is created recording: user identity, role, view accessed, timestamp, and session context.
2. **Given** a user applies a filter or performs a search in any dashboard view, **When** results are returned, **Then** an audit entry is created recording the filter/search parameters and result count.
3. **Given** a user exports audit records or compliance data, **When** the export completes, **Then** an audit entry is created recording the export action, data scope, format, and record count.
4. **Given** an Observer/Auditor searches the audit trail for dashboard interaction events, **When** results are returned, **Then** they can see all recorded dashboard interactions filtered by user, date range, or action type.

---

### Edge Cases

- What happens when all backend governance data sources are simultaneously unavailable? The dashboard must display a system-wide degraded-mode banner indicating limited data availability, show last-known-good data with staleness timestamps for each widget, and remain navigable.
- How does the dashboard handle a user with no AIIMS role assignment? The user sees a restricted view with only publicly available governance information (if any) and a message directing them to request role assignment from their administrator.
- What happens when the governance health score calculation encounters incomplete data (e.g., some constitutional gates have no assessment data)? The health score is calculated from available data, the score denominator adjusts to reflect only assessed gates, and unassessed gates are listed separately with "assessment pending" status.
- How does the system handle concurrent users viewing and exporting the same audit trail data during a high-activity incident? Export operations are queued and processed sequentially per user to prevent resource contention, with progress indicators for long-running exports.
- What happens when a user's AIIMS role is revoked while they are actively using the dashboard? On the next data refresh cycle, the dashboard detects the role change, adjusts the view to match remaining authorisations, and logs the access transition in the audit trail.
- How does the dashboard behave when recovery data spans multiple incidents? Recovery progress is segmented by incident, with a selector to switch between active recovery programmes, and aggregate views show cross-incident totals.
- How does the dashboard handle a user switching between simulation and live contexts? Tenant context is server-derived from Entra ID claims per spec 007. If a user's session context changes (e.g., they join a simulation), the dashboard reflects the new tenant context on the next data refresh. A persistent visual indicator distinguishes simulation from live data. No tenant switcher is exposed to the client.

## Requirements *(mandatory)*

### Functional Requirements

**Executive Summary & Health Score**

- **FR-001**: System MUST calculate and display a governance health score (0–100) using weighted inputs: constitutional compliance (40%), operational readiness (25%), data source governance (20%), and recovery progress (15%). The score MUST be mapped to a traffic-light indicator: Green (≥80), Amber (50–79), Red (<50).
- **FR-002**: System MUST display the compliance status of each of the 10 constitutional gates as one of: compliant, non-compliant, partially compliant, or assessment pending.
- **FR-003**: System MUST display a count of active incidents, overall resource utilisation percentage, and a strategic risk summary showing risk counts by severity level (extreme, high, medium, low).
- **FR-004**: System MUST allow users to drill down from any summary indicator to the detailed view for that governance domain.

**Compliance View**

- **FR-005**: System MUST display a compliance matrix showing all registered data sources with their compliance status, last assessment date, next assessment due date, and governance gap count.
- **FR-006**: System MUST display grace period information for data sources under grace periods, including expiry date, reason, and countdown indicator.
- **FR-007**: System MUST support filtering the compliance matrix by compliance status, assessment date range, and data source category.
- **FR-008**: System MUST provide a detail panel for each data source showing full assessment history, current remediation actions, and links to related audit trail entries.

**Audit Trail View**

- **FR-009**: System MUST provide a searchable, filterable audit log displaying governance events with timestamp, actor, action type, affected entity, outcome, and provenance reference.
- **FR-010**: System MUST support searching audit events by date range, actor, action type, affected entity, and free-text keyword.
- **FR-011**: System MUST display full decision chains for selected audit events, showing the sequence from triggering event through intermediate approvals to final action, including rationale and evidence integrity indicators.
- **FR-012**: System MUST support exporting selected audit records as downloadable reports in three formats: PDF (for executive/regulatory reporting), CSV (for data analysis), and JSON (for API interoperability), preserving all provenance metadata.

**Operational Readiness View**

- **FR-013**: System MUST display PPRR (Prevention, Preparedness, Response, Recovery) phase indicators with the current active phase highlighted.
- **FR-014**: System MUST display emergency plan counts by lifecycle status using all 7 states from the spec 019 state machine: Draft, InConsultation, UnderReview, Endorsed, Activated, PostEventReview, and Superseded. Plans with overdue review dates MUST be visually flagged regardless of lifecycle state. "Expired" is a display-level condition (next review date has passed) applied as an overlay indicator, not a lifecycle state.
- **FR-015**: System MUST display simulation exercise completion rates broken down by exercise type, with most recent exercise date and overall readiness score.
- **FR-016**: System MUST display AIIMS role coverage as a percentage with detail on which specific roles are unassigned or under-staffed.

**Recovery Dashboard View**

- **FR-017**: System MUST display recovery progress for each of the five recovery domains defined by AIDR: Overarching (Resilience & Sustainability), Social, Economic, Built, and Natural — as percentage complete with trend direction indicators. The overarching domain is displayed as a cross-cutting summary row that aggregates resilience and sustainability outcomes spanning the four concrete domains. Uses `RecoveryDomain` (5-value type from spec 019) for display; maps to `RecoveryEnvironmentTracker` (4-value type from spec 018) for underlying data.
- **FR-018**: System MUST provide detail panels for each recovery domain showing outcome targets, activity completion rates, community indicators, and M&E framework evaluation results. For the overarching domain, the detail panel shows cross-cutting resilience and sustainability outcomes with their roll-up indicators from the four concrete domains.
- **FR-019**: System MUST flag recovery domains that are below their target trajectory with a warning indicator and variance from target.

**Risk & Warning View**

- **FR-020**: System MUST display the active risk register with risk counts by severity level (extreme, high, medium, low) and treatment closure rate.
- **FR-021**: System MUST display alert compliance metrics including average alert approval latency, AWS 3-tier usage breakdown (Advice/Watch and Act/Emergency Warning), and broadcast reach percentage.
- **FR-021A**: System MUST display AWS warning principle compliance as a per-principle compliance rate showing the percentage of warnings that meet each of the 10 principles: life_saving, empowering, trusted, risk_scaled, timely_targeted, impact_conveying, action_calling, clearly_communicated, accessible, and bigger_picture. Non-compliant warnings MUST be drillable to show which specific principles they failed. Overall principle compliance score is also shown as a single percentage.
- **FR-022**: System MUST flag alerts that exceed acceptable approval latency thresholds and display the specific alerts with their actual approval times.
- **FR-023**: System MUST provide a detail panel for selected risks showing description, likelihood, consequence, current treatments, treatment history, and related audit entries.

**Role-Based Access & Personalisation**

- **FR-024**: System MUST filter dashboard views and widgets based on the authenticated user's AIIMS role assignment(s), showing role-relevant metrics prominently while maintaining access to all authorised views.
- **FR-025**: System MUST support users with multiple AIIMS roles by combining relevant widgets with the highest-authority role's widgets displayed first.
- **FR-026**: System MUST restrict dashboard access to authenticated users with valid AIIMS role assignments. Users without role assignments see a restricted view with a message directing them to request access.
- **FR-026A**: System MUST respect simulation vs live tenant isolation per spec 007. Tenant context (`live` or `sim-{scenarioRunId}`) is server-derived from the user's Entra ID claims — never client-selectable. The dashboard defaults to the `live` tenant. When accessed within a simulation session, the dashboard displays simulation-scoped governance data with a persistent visual tenant indicator (e.g., "SIMULATION — {scenario name}" banner). All dashboard queries MUST include `tenant_id` in their API calls to prevent cross-tenant data leakage.

**Auditability & Transparency**

- **FR-027**: System MUST log all dashboard interactions (view access, filter application, search execution, data export, drill-down navigation) as audit trail entries with user identity, role, action details, and timestamp. Note: user identity is required in audit records for provenance (Constitution Gate 4) and is distinct from observability telemetry, which MUST NOT contain PII (see FR-035).
- **FR-028**: System MUST require human confirmation for any governance state changes initiated from the dashboard (e.g., acknowledging a compliance gap, triggering a reassessment).

**Data Freshness & Resilience**

- **FR-029**: System MUST refresh dashboard data via REST polling at configurable intervals: default 30 seconds during active incidents and 5 minutes for steady-state dashboard views. Governance data MUST be cached with a 5-minute TTL. Users MAY trigger a manual refresh at any time.
- **FR-030**: System MUST display data staleness indicators showing the age of displayed data for each widget.
- **FR-031**: System MUST gracefully degrade when backend data sources are unavailable, displaying last-known-good data with staleness timestamps and a degraded-mode indicator per affected widget.

**Accessibility & Responsiveness**

- **FR-032**: System MUST meet WCAG 2.1 AA accessibility standards across all dashboard views, including keyboard navigation, screen reader compatibility, and sufficient colour contrast. Every chart and data visualisation widget (gauges, progress bars, trend charts, pie/donut charts) MUST provide a companion data table as the programmatic alternative for screen readers. Data tables are visually hidden by default with a toggle to show/hide them. Charts MUST also include ARIA labels summarising the key data point (e.g., "Governance health score: 78 out of 100, Amber status").
- **FR-033**: System MUST render usably on mobile devices (minimum 375px viewport width) with responsive layouts that reorganise widgets for smaller screens. Primary use is desktop in Emergency Operations Centres (EOCs); mobile is responsive but not mobile-first.
- **FR-033A**: System MUST use the platform's AWS severity colour tokens for all warning-level indicators: `--ama-aws-advice` (yellow) for Advice tier, `--ama-aws-watch` (orange) for Watch and Act tier, and `--ama-aws-emergency` (red) for Emergency Warning tier. These tokens MUST be used consistently across all views that display warning severity.

**Observability & Operational Health**

- **FR-034**: System MUST emit structured telemetry to Azure Monitor and Application Insights for dashboard performance metrics (page load time, API call latency, error rates, widget render times) and operational health.
- **FR-035**: System MUST NOT include personally identifiable information (PII) in observability telemetry (Application Insights traces, Azure Monitor logs). User actions in telemetry MUST use anonymised correlation IDs only.

### Key Entities

- **Governance Health Score**: A calculated composite score (0–100) representing the overall governance posture of the platform. Derived from four weighted dimensions: constitutional compliance (40%), operational readiness (25%), data source governance (20%), and recovery progress (15%). Mapped to traffic-light status: Green (≥80), Amber (50–79), Red (<50). Associated with: a calculation timestamp, contributing factor scores, and the set of inputs used.
- **Constitutional Gate Assessment**: An evaluation record for one of the 10 mandatory constitution gates, capturing compliance status, assessment date, assessor, evidence references, and remediation actions. Related to data source compliance records and audit trail entries.
- **Dashboard Widget Configuration**: A role-to-widget mapping that defines which metrics and views are shown by default for each AIIMS role. Contains: role identifier, widget list (ordered by priority), and view access permissions.
- **Audit Event (Dashboard)**: An immutable record of a dashboard interaction, capturing: timestamp, actor identity, actor role, action type (view/filter/search/export/drill-down), action parameters, affected entity, and session context. Appended to the existing platform-wide audit trail.
- **Compliance Matrix Entry**: A row in the compliance matrix representing a single data source's governance status, containing: source identifier, compliance status, last assessment date, next due date, grace period details (if applicable), and gap count.
- **Recovery Domain Progress**: A tracking record for one of the five recovery domains (overarching, social, economic, built, natural), containing: percentage complete, trend direction, outcome targets, activity completion rates, community indicators, and M&E evaluation results. For the four concrete domains, linked to a specific incident's `RecoveryEnvironmentTracker` (spec 018). For the overarching domain, aggregates cross-cutting resilience and sustainability indicators that roll up from the concrete domains. Linked to a specific incident's recovery programme.
- **Risk Register Entry (Dashboard View)**: A read-only view of a risk record showing: risk identifier, description, severity, likelihood, consequence, treatment status, treatment closure date, responsible party, and related audit references. Sourced from the platform's risk assessment system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 10 AIIMS actor personas can access role-appropriate governance information from a single dashboard entry point within 2 navigation steps.
- **SC-002**: The dashboard fully loads and displays data within 3 seconds on a standard broadband connection for the executive summary view.
- **SC-003**: Users can search and retrieve specific audit trail entries within 2 seconds using any combination of date range, actor, and action type filters (5-second degraded-mode fallback when backend services are partially unavailable).
- **SC-004**: The compliance matrix accurately reflects the current compliance status of 100% of registered data sources, with no data older than the configured refresh interval.
- **SC-005**: Governance health score updates reflect changes in underlying compliance, readiness, or risk data within one refresh cycle (default 30 seconds).
- **SC-006**: 90% of users in usability testing can identify the compliance status of a specific data source within 30 seconds of opening the dashboard.
- **SC-007**: Dashboard remains navigable and displays last-known-good data when up to 50% of backend data sources are unavailable.
- **SC-008**: 100% of dashboard user interactions (view, filter, search, export, drill-down) are captured in the audit trail with complete provenance metadata.
- **SC-009**: Recovery progress tracking covers all five recovery domains (overarching, social, economic, built, natural) with outcome indicators that match the AIDR M&E Framework definitions and catalogue structure from spec 019.
- **SC-010**: Role-based dashboard personalisation correctly adjusts the default view for each of the 10 AIIMS roles without requiring manual user configuration.
- **SC-011**: The dashboard meets WCAG 2.1 AA compliance as verified by automated accessibility testing tools and manual screen reader testing.
- **SC-012**: All governance state changes initiated from the dashboard require explicit human confirmation before execution.

## Assumptions

- The existing governance data sources (data source registry, AIIMS role assignments, PPRR contexts, emergency plans, M&E frameworks, recovery catalogue, audit trails, risk assessments, alert/warning records, evacuation stages, signal pipeline health, and simulation exercises) expose read-accessible endpoints or data feeds that the dashboard can consume. No new data collection mechanisms are assumed.
- AIIMS role assignments are managed by the platform's existing identity and access management system (spec 018). The dashboard reads role assignments but does not manage them.
- The governance health score algorithm uses the following default weights: constitutional compliance (40%), operational readiness (25%), data source governance (20%), recovery progress (15%). Traffic-light thresholds are: Green (≥80), Amber (50–79), Red (<50). Weights and thresholds are configurable by administrators.
- Audit trail infrastructure (immutable, append-only logging) already exists across the platform. The dashboard adds a new category of audit events (dashboard interactions) to the existing trail.
- "Acceptable approval latency threshold" for alert compliance (FR-022) is configurable by administrators and defaults to the value defined in the alert/warning specification (spec 008).
- Data sovereignty requirements (Australian regions only) are enforced at the infrastructure level and do not require dashboard-specific controls.
- The dashboard is a read-only reporting interface for governance data. Any governance state changes (e.g., triggering reassessment) are submitted as requests that go through existing human-in-the-loop approval workflows.
- Export formats for audit trail and compliance reports are: PDF (executive and regulatory reporting, supporting AIDR M&E annual reporting requirements), CSV (data analysis and downstream processing), and JSON (API consumers and system interoperability per OpenAPI standards).
- The dashboard uses REST polling (consistent with the platform's existing API pattern) rather than WebSocket. Default intervals are 30 seconds during active incidents and 5 minutes for steady-state dashboards. Governance data is cached with a 5-minute TTL (aligned with spec 005). Intervals are configurable to accommodate different operational tempos.

## Clarifications

### Session 2026-04-17

- Q: What are the governance health score algorithm weights and traffic-light thresholds? → A: Constitutional compliance 40%, Operational readiness 25%, Data source governance 20%, Recovery progress 15%. Traffic-light: Green (≥80), Amber (50–79), Red (<50).
- Q: Which export formats must the dashboard support for audit and compliance reports? → A: PDF for executive/regulatory reports, CSV for data analysis, JSON for API interoperability.
- Q: What data refresh mechanism should the dashboard use? → A: REST polling with configurable intervals (30s active incidents, 5min steady-state). Cache with 5-min TTL.
- Q: How should the dashboard itself be monitored for operational health? → A: Azure Monitor + App Insights with structured logging. No PII in telemetry.
- Q: How is the PII boundary defined between audit trail records and observability telemetry? → A: Audit entries include user identity (provenance required). Observability telemetry uses anonymised correlation IDs only — no PII.

### Session 2026-04-17 (Pass 2)

- Q: Should FR-014 display all 7 emergency plan lifecycle states from spec 019, or only the 4 originally listed? → A: All 7 states (Draft, InConsultation, UnderReview, Endorsed, Activated, PostEventReview, Superseded). "Expired" is a display-level overlay condition for overdue review dates, not a lifecycle state.
- Q: Should the Recovery Dashboard View display 5 recovery domains (including overarching) or only 4 concrete environments? → A: All 5 domains (overarching, social, economic, built, natural). Overarching is a cross-cutting summary row per AIDR M&E Framework. Uses RecoveryDomain 5-value type from spec 019; maps to RecoveryEnvironmentTracker 4-value type for underlying data.
- Q: How should the dashboard handle simulation vs live tenant context from spec 007? → A: Default to live tenant; tenant context server-derived from Entra ID claims per spec 007. Simulation context shows simulation-scoped data with persistent visual indicator. All API queries include tenant_id. No client-side tenant switcher.
- Q: Should the Risk & Warning View validate warnings against all 10 AWS warning principles, or only show tier usage? → A: Per-principle compliance rate (% of warnings meeting each of the 10 principles) with drill-down to non-compliant warnings. Overall principle compliance score also displayed.
- Q: What accessibility pattern should chart/visualization widgets use for screen readers? → A: Every chart MUST have a companion data table (visually hidden, togglable) as the screen reader alternative. ARIA labels summarising key data points also required. AWS severity colour tokens (--ama-aws-advice yellow, --ama-aws-watch orange, --ama-aws-emergency red) for all warning indicators.

# Feature Specification: Governance Dashboard Real Data Integration

**Feature Branch**: `023-dashboard-real-data`
**Created**: 2025-07-18
**Status**: Draft
**Input**: User description: "Replace all hardcoded stubs in the governance dashboard with real data sourced from existing seed catalogues, repositories, and computation services."

## Problem Statement

The governance dashboard presents six views — health score, operational readiness, recovery progress, risk overview, compliance matrix, and audit trail — but approximately 75% of the data displayed is fabricated from hardcoded stubs. Fifteen or more internal helper methods return static values instead of querying actual system state. This means emergency managers, sector coordinators, and operational agents cannot trust the dashboard for decision-making. The dashboard is decorative rather than actionable.

Real data already exists across seed catalogues (46 data sources, 49 organisations, 27 frameworks, 123 framework assignments, 9 jurisdictions, 5 recovery domains), domain models (constitutional assessments, governance audit entries, emergency plans, hazard assessments, recovery trackers), and existing services (health score computation, recovery catalogue, seed loading, governance queries). The gap is not data availability — it is wiring.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Accurate Health Score from Real Inputs (Priority: P1)

An emergency management coordinator opens the governance dashboard and sees a composite health score that reflects the actual state of the system. The score's four components — constitutional compliance (40% weight), operational readiness (25%), data source governance (20%), and recovery progress (15%) — each derive from real assessments, real organisation data, real data source registrations, and real recovery catalogue entries. The coordinator drills into any component and sees the underlying data that produced the score, enabling them to identify which areas need attention.

**Why this priority**: The health score is the first thing every user sees. If this single number is fabricated, the entire dashboard loses credibility. Replacing its inputs with real data transforms the dashboard from decorative to trustworthy.

**Independent Test**: Can be fully tested by loading the dashboard summary endpoint and verifying that each health score component returns values derived from actual seed or stored data, not static constants. Delivers a trustworthy headline metric.

**Acceptance Scenarios**:

1. **Given** the system has seed data loaded (46 data sources, 49 organisations, 27 frameworks, 5 recovery domains), **When** the coordinator requests the dashboard summary, **Then** the health score is computed from real inputs and the component breakdown reflects actual counts and ratios from those data sets.
2. **Given** constitutional assessment records exist in the data store, **When** the health score is computed, **Then** the constitutional compliance component (40% weight) reflects the pass/fail status of all 10 constitutional gates derived from those assessments.
3. **Given** no constitutional assessments exist in the data store but seed data is available, **When** the health score is computed, **Then** the system falls back to seed-derived defaults for constitutional compliance and indicates the data source as "seed fallback" in metadata.
4. **Given** the data source registry contains sources with mixed statuses, **When** the data source governance component (20% weight) is calculated, **Then** the score reflects the actual ratio of available vs degraded vs offline sources.
5. **Given** the recovery catalogue contains 5 domains with outcomes, activities, and indicators, **When** the recovery progress component (15% weight) is calculated, **Then** the score reflects actual indicator completion rates across domains.

---

### User Story 2 — Real Operational Readiness View (Priority: P2)

A state-level emergency planning officer opens the operational readiness view to assess preparedness across jurisdictions. They see actual PPRR (Prevention, Preparedness, Response, Recovery) phase distribution computed from the 123 framework assignments, real AIIMS role coverage computed from organisation function assignments across all six AIIMS functions (Control, Planning, Intelligence, Public Information, Operations, Logistics), actual emergency plan statuses, capability gap analysis derived from organisation capabilities versus framework requirements, and volunteer readiness metrics computed from organisations with volunteer or mixed workforce types.

**Why this priority**: Operational readiness is the most decision-critical view for pre-incident planning. Hardcoded values here could lead to false confidence about jurisdictional preparedness, putting lives at risk.

**Independent Test**: Can be fully tested by requesting the operational readiness endpoint and verifying each section returns data traceable to seed records or stored plans. Delivers an actionable preparedness picture for all 9 jurisdictions.

**Acceptance Scenarios**:

1. **Given** 123 framework assignments exist across 9 jurisdictions, **When** the readiness view is loaded, **Then** the PPRR phase distribution shows counts computed from actual assignment records (e.g., response: ~24, preparedness: ~22, recovery: ~15, prevention: ~12 based on framework phases).
2. **Given** 49 organisations with AIIMS function assignments exist, **When** the AIIMS role coverage section is displayed, **Then** coverage percentages are computed from actual organisation-to-function mappings across all six AIIMS functions.
3. **Given** organisations have defined `primary_capabilities` and frameworks have defined requirements, **When** the capability gaps section is displayed, **Then** gaps represent real mismatches between what organisations can do and what frameworks require.
4. **Given** 16 volunteer organisations and 8 mixed-workforce organisations exist in seed data, **When** the volunteer readiness section is displayed, **Then** metrics reflect actual volunteer organisation counts, jurisdiction distribution, and capability coverage.
5. **Given** emergency plans exist in the data store with various lifecycle states, **When** the emergency plans section is displayed, **Then** plan counts per state reflect actual records (not hardcoded numbers).

---

### User Story 3 — Real Recovery Progress View (Priority: P3)

A recovery coordinator opens the recovery progress view to track post-disaster recovery across five domains: overarching, social, economic, built environment, and natural environment. They see actual progress derived from the recovery catalogue's outcomes, activities, and indicators, including domain-level completion percentages and target tracking based on indicator data.

**Why this priority**: Recovery tracking drives resource allocation across domains. Fabricated progress data could cause under-resourcing of lagging domains or premature withdrawal from active recovery efforts.

**Independent Test**: Can be fully tested by requesting the recovery progress endpoint and verifying domain breakdowns match recovery catalogue seed data structure (5 domains, their outcomes, activities, indicators). Delivers real domain-level progress visibility.

**Acceptance Scenarios**:

1. **Given** the recovery catalogue contains 5 domain files with outcomes, activities, and indicators, **When** the recovery progress view is loaded, **Then** all 5 domains are represented with progress metrics derived from actual catalogue entries.
2. **Given** the social domain has 24 outcomes, 57 activities, and 53 indicators, **When** the social domain detail is requested, **Then** the response reflects these actual counts and any completion status tracked against them.
3. **Given** recovery environment trackers exist with progress data, **When** the recovery view is loaded, **Then** domain progress percentages incorporate tracked indicator values rather than static percentages.
4. **Given** no active recovery trackers exist but the recovery catalogue is loaded, **When** the recovery view is loaded, **Then** the system displays catalogue structure (domains, outcomes, activities, indicators) with baseline/zero progress rather than fabricated progress values.

---

### User Story 4 — Real Risk & Warning View (Priority: P4)

A risk analyst opens the risk overview to assess current threat levels. They see severity counts derived from actual hazard assessments, a top risks list sourced from real risk records, and warning system principle compliance derived from data source configurations and their alignment with Australian Warning System (AWS) tiers.

**Why this priority**: Risk overview drives immediate protective actions. Hardcoded severity counts could mask emerging threats or create false alarms that erode trust.

**Independent Test**: Can be fully tested by requesting the risk endpoint and verifying severity counts come from actual hazard assessment records or computed signals, not static arrays. Delivers a real risk posture summary.

**Acceptance Scenarios**:

1. **Given** hazard assessment records exist with varying severity levels, **When** the risk overview is loaded, **Then** severity counts (critical, high, medium, low) reflect actual assessment data.
2. **Given** no hazard assessments exist in the data store, **When** the risk overview is loaded, **Then** the system returns zero-count severity breakdown (not fabricated numbers) and indicates that no assessments are on record.
3. **Given** data sources have trust tier and status information, **When** the AWS principle compliance section is computed, **Then** compliance scores reflect actual data source configuration alignment with warning system tiers.
4. **Given** hazard assessments include risk summaries and confidence levels, **When** the top risks list is displayed, **Then** risks are ranked by actual severity and confidence, not by hardcoded position.

---

### User Story 5 — Real Audit Trail (Priority: P5)

A governance officer searches the audit trail for recent system changes. They see actual audit entries capturing constitutional assessments performed, data source status changes, framework updates, and plan approvals — each with actor identity, timestamp, and related entity context. The audit trail is no longer empty.

**Why this priority**: Auditability is one of the 10 constitutional gates. An always-empty audit trail means the system fails its own governance requirements. This story establishes the accountability chain.

**Independent Test**: Can be fully tested by performing auditable actions (e.g., a constitutional assessment, a data source status change) and then querying the audit endpoint to confirm entries appear with correct details. Delivers a functioning governance audit log.

**Acceptance Scenarios**:

1. **Given** governance audit entries exist in the data store, **When** the audit trail endpoint is queried, **Then** actual audit entries are returned with action, actor, timestamp, and related entity details.
2. **Given** a constitutional assessment is recorded, **When** the audit trail is queried, **Then** an audit entry for that assessment appears with the correct assessment reference.
3. **Given** the audit trail is queried with search/filter parameters, **When** the results are returned, **Then** filtering operates on actual stored records (not returning empty regardless of filter).
4. **Given** the audit event chain endpoint is called for a specific event, **When** related events exist, **Then** the decision chain shows the actual provenance of linked events.

---

### User Story 6 — Reliable Compliance Matrix with Seed Fallback (Priority: P6)

A compliance officer views the compliance matrix to assess data source adherence to constitutional principles. The matrix displays real compliance entries from stored assessments and, when the data store is empty, reliably falls back to seed-derived compliance baselines rather than returning an empty grid.

**Why this priority**: The compliance matrix already has partial real-data wiring but silently falls back to empty. Fixing the fallback ensures the view is never blank while maintaining the path to real-time compliance data.

**Independent Test**: Can be fully tested by loading the compliance endpoint with and without stored assessments to verify real data is used when available and seed-derived defaults are used otherwise. Delivers a compliance matrix that always shows meaningful data.

**Acceptance Scenarios**:

1. **Given** constitutional assessment records exist for data sources, **When** the compliance matrix is loaded, **Then** entries reflect actual assessment outcomes per principle per data source.
2. **Given** no constitutional assessments exist in the data store, **When** the compliance matrix is loaded, **Then** the system displays a seed-derived baseline matrix showing all 10 constitutional gates across registered data sources with a "seed baseline" indicator.
3. **Given** assessments exist for some but not all data sources, **When** the compliance matrix is loaded, **Then** assessed sources show real results and unassessed sources show seed-derived defaults, with clear visual distinction.

---

### Edge Cases

- What happens when the data store is completely empty and seed data fails to load? The dashboard must return graceful error responses indicating data unavailability rather than crashing or showing misleading fabricated data.
- What happens when seed data is partially loaded (e.g., organisations loaded but frameworks missing)? Each dashboard component must independently handle partial data, computing what it can and clearly indicating which sections have incomplete data.
- What happens when a recovery catalogue domain file is malformed or missing? The remaining 4 domains must still display correctly; the missing domain should be reported as unavailable.
- What happens when an organisation has no AIIMS functions assigned? It should be excluded from AIIMS coverage calculations but still counted in general organisation metrics.
- What happens when a framework assignment references a jurisdiction or framework that no longer exists? The assignment should be included in aggregate counts but flagged in detail views as referencing an unknown entity.
- What happens when constitutional assessments exist but are marked as superseded? Only current (non-superseded) assessments should factor into health score and compliance matrix computations.
- What happens when all data sources have the same status (e.g., all "available")? The data source governance score should correctly compute 100% availability, not assume a distribution.

## Requirements *(mandatory)*

### Functional Requirements

#### Health Score Inputs

- **FR-001**: System MUST compute the constitutional compliance component (40% weight) from actual constitutional gate assessment records, evaluating all 10 gates by their canonical names: (1) Primacy of Life, (2) National EM Principles, (3) Multi-Hazard Design, (4) Transparency & Auditability, (5) Warning & Public Information, (6) Evacuation Framework, (7) Recovery Support, (8) Cloud Platform & Infrastructure, (9) PPRR Lifecycle, (10) Governance & Quality Gates. These gate names are the established contract in the existing codebase; the constitution's NON-NEGOTIABLE requirements map into these 10 sections.
- **FR-002**: System MUST compute the operational readiness component (25% weight) from actual emergency plan states, AIIMS role assignment coverage, organisation capability data, and framework assignment records.
- **FR-003**: System MUST compute the data source governance component (20% weight) from the actual data source registry, counting sources by status (available, degraded, offline) and computing coverage ratios.
- **FR-004**: System MUST compute the recovery progress component (15% weight) from actual recovery catalogue domain data (outcomes, activities, indicators) and any active recovery tracker progress.
- **FR-005**: System MUST fall back to seed-derived input values when the data store contains no records for a given health score component, and MUST indicate that seed fallback is in use in the response metadata.

#### Operational Readiness

- **FR-006**: System MUST compute PPRR phase distribution from the actual set of framework assignments and their associated framework phase definitions.
- **FR-007**: System MUST compute AIIMS role coverage from actual organisation AIIMS function assignments, reporting coverage across all six functions: Control, Planning, Intelligence, Public Information, Operations, Logistics.
- **FR-008**: System MUST derive emergency plan counts and status distribution from actual plan records with their lifecycle states, or from seed/framework-derived plan expectations when no plan records exist.
- **FR-009**: System MUST compute capability gap analysis by comparing organisation primary capabilities against framework requirements for each jurisdiction.
- **FR-010**: System MUST compute volunteer readiness metrics from organisations whose workforce type includes volunteer or mixed classifications, including count, jurisdiction distribution, and capability coverage.

#### Recovery Progress

- **FR-011**: System MUST derive recovery domain progress from the 5 recovery catalogue domains (overarching, social, economic, built, natural), reflecting actual outcome counts, activity counts, and indicator counts per domain.
- **FR-012**: System MUST compute recovery targets from indicator target values in the recovery catalogue data.
- **FR-013**: System MUST incorporate active recovery tracker data when available, merging tracker progress with catalogue baseline structure.

#### Risk & Warning

- **FR-014**: System MUST derive risk severity counts from actual hazard assessment records, categorised by severity level.
- **FR-015**: System MUST populate the top risks list from actual hazard assessment records or risk register entries, ranked by severity and confidence.
- **FR-016**: System MUST compute AWS principle compliance from data source trust tier configurations and their alignment with warning system requirements.
- **FR-017**: System MUST return zero-count severity breakdowns (not fabricated counts) when no hazard assessments exist.

#### Audit Trail

- **FR-018**: System MUST populate the audit trail from actual governance audit entry records, returning entries with action type, actor identity, timestamp, related entity reference, and contextual details.
- **FR-019**: System MUST record audit entries for constitutional assessments, data source status changes, framework updates, and plan approvals.
- **FR-020**: System MUST support search and filtering of audit entries by action type, actor, time range, and related entity.
- **FR-021**: System MUST return the actual decision chain (linked audit events) when the chain endpoint is queried for a specific event.

#### Compliance Matrix

- **FR-022**: System MUST display compliance matrix entries from actual constitutional assessment records when available.
- **FR-023**: System MUST fall back to a seed-derived baseline compliance matrix when no assessment records exist, covering all 10 constitutional gates across all registered data sources.
- **FR-024**: System MUST visually distinguish between real assessment results and seed-derived baseline entries.

#### Cross-Cutting

- **FR-025**: System MUST maintain backward-compatible response structures for all 13 existing dashboard endpoints — no breaking changes to field names, data shapes, or endpoint paths.
- **FR-026**: System MUST use seed data as the default/fallback data source when data store containers are empty, with graceful transition to real data as it becomes available.
- **FR-027**: System MUST enforce tenant isolation on all data store queries — no cross-tenant data leakage in multi-tenant deployments.
- **FR-028**: System MUST only include current (non-superseded) constitutional assessments in health score and compliance matrix computations.

### Key Entities

- **Constitutional Assessment**: A record of compliance evaluation against one of the 10 constitutional gates. Key attributes: gate/principle identifier, compliance status (pass/fail/partial), assessed data source, assessor identity, assessment date, supersession chain.
- **Governance Audit Entry**: An immutable log record of a governance-relevant action. Key attributes: action type, actor identity, timestamp, related entity reference, contextual details, tenant scope.
- **Emergency Plan**: A jurisdictional emergency management plan with lifecycle tracking. Key attributes: plan identity, jurisdiction/region, hazard types covered, lifecycle state (7 possible states), version, endorsement status, review/exercise dates.
- **Hazard Assessment**: A risk evaluation record generated from input signals. Key attributes: hazard identity, severity level, confidence score, summary, assessment type, associated incident, generation metadata.
- **AIIMS Role Assignment**: An assignment of an agent to one of the six AIIMS functional roles during incident management. Key attributes: agent identity, AIIMS function, assignment period, delegation source.
- **Data Source**: A registered data feed in the governance registry. Key attributes: source identity, name, provider, data type, trust tier, operational status (available/degraded/offline), geographic coverage, update frequency.
- **Organisation**: An entity participating in emergency management. Key attributes: organisation identity, category, jurisdictions, AIIMS function assignments, primary capabilities, workforce type (paid/volunteer/mixed), operational status.
- **Framework**: A governing framework for emergency management activities. Key attributes: framework identity, type, applicable jurisdictions, PPRR phases covered, approval and escalation rules.
- **Framework Assignment**: A link between a framework and a jurisdiction. Key attributes: assignment identity, framework reference, jurisdiction reference, effective period.
- **Recovery Catalogue Domain**: One of five recovery knowledge domains. Key attributes: domain name, outcomes (each with activities and indicators), indicator targets.

## Clarifications

### Session 2025-07-18

- Q: The spec's FR-001 listed constitutional gates using constitution NON-NEGOTIABLE requirement names (human-in-the-loop, data sovereignty, etc.) but the codebase uses AIDR-section-derived names (Primacy of Life, National EM Principles, etc.). Which naming scheme is canonical? → A: The code's AIDR-section names are canonical (Option A). They are the established contract in the frontend `ConstitutionalGateStatus` interface, unit tests, and Pydantic model. The constitution's NON-NEGOTIABLE requirements map *into* these 10 sections. FR-001 updated to list canonical names.
- Q: The spec claims "46 data sources" but should the count be treated as a fixed contract or a dynamic baseline? → A: Dynamic baseline. The data source registry is the seed file `data_sources_australia.json` which currently has 46 entries. The system must handle any number of sources; 46 is the current seed count, not a ceiling.
- Q: How should the recovery catalogue be loaded given it's not in the current `bootstrap_seed_data()` function? → A: Extend `bootstrap_seed_data()` to include recovery catalogue data. Add a `recovery_catalogue` key to the returned dict, loading all 5 domain files and the evaluation questions file from the `recovery-catalogue/` subdirectory.
- Q: Should the exercise completion rate be computed from actual exercise records or remain a seed-derived metric? → A: Seed-derived for MVP. No exercise records exist yet. The system should compute from seed framework data (frameworks with review/exercise metadata) and show 0% when no exercise data exists, transitioning to real data when exercise tracking is implemented.
- Q: Should audit trail entries be auto-generated when seed data is loaded, or only created by actual user/system actions? → A: Only actual actions. Seed data loading should NOT generate audit trail entries. The audit trail reflects real governance actions (assessments, status changes, approvals). An empty audit trail when no actions have occurred is the correct initial state.

## Assumptions

- The existing health score algorithm (40/25/20/15 weighting) is correct and should not be modified — only its inputs change.
- The 13 existing dashboard endpoints retain their current paths and response structures. New metadata fields (e.g., "data_source: seed_fallback") are additive, not breaking.
- Seed data statistics (46 data sources, 49 organisations, 27 frameworks, 123 assignments, 9 jurisdictions, 5 recovery domains) represent the baseline dataset. The system should handle larger datasets without degradation.
- All 10 constitutional gates are evaluable from the combination of stored assessments and seed data — no gate requires an external API to assess.
- Emergency plan lifecycle has 7 states as defined in the existing model. No new states are needed.
- AIIMS functions are the standard six (Control, Planning, Intelligence, Public Information, Operations, Logistics). No additional functions are required.
- Superseded constitutional assessments are identified by the `is_current` flag on the assessment record.
- Volunteer readiness is determined by the `workforce_type` field on organisation records (values: "paid", "volunteer", "mixed").
- All data must reside in the Australia East region per project constraints.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero hardcoded stub values remain in the dashboard data pipeline — every value displayed on the dashboard is traceable to a seed record, a stored assessment, or a computed derivation from real inputs.
- **SC-002**: The health score summary endpoint returns component breakdowns where each component value changes when the underlying data changes (e.g., adding a new data source with "degraded" status changes the data source governance score).
- **SC-003**: The operational readiness view correctly reflects all 49 organisations' AIIMS function coverage, all 123 framework assignments' PPRR phase distribution, and volunteer metrics from all 24 volunteer/mixed-workforce organisations.
- **SC-004**: The recovery progress view displays all 5 recovery domains with accurate outcome, activity, and indicator counts matching the recovery catalogue data.
- **SC-005**: The risk overview returns severity counts that are zero when no hazard assessments exist, and accurately reflect stored assessment severity distribution when assessments are present.
- **SC-006**: The audit trail returns actual stored entries (not empty results) when auditable events have occurred, with correct action, actor, timestamp, and entity reference.
- **SC-007**: Dashboard responses are delivered within 500 milliseconds at the 95th percentile for typical query patterns.
- **SC-008**: When the data store is completely empty, all 13 dashboard endpoints return meaningful seed-derived responses rather than errors or fabricated data.
- **SC-009**: All existing dashboard consumers (agents, frontend views) continue to function without modification after this change — zero breaking changes to response contracts.
- **SC-010**: The compliance matrix correctly displays 10 constitutional gates across all registered data sources, using real assessments where available and clearly-marked seed baselines elsewhere.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-061**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-062**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-063** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-021**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-021.md` (created in feature 028 polish).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-067** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (data-engineer, ux-designer) sign off on country-specific calibration.
- **SCP-068**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-069**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.

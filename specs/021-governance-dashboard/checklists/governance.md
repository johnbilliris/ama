# Governance Dashboard — Specification Quality Checklist

**Purpose**: Formal governance gate — exhaustive validation of specification completeness, clarity, consistency, and coverage for the Governance Dashboard feature. Items are "unit tests for English" that evaluate the *requirements themselves*, not the implementation.
**Created**: 2025-07-18
**Feature**: [spec.md](../spec.md)
**Depth**: Deep (formal governance gate)
**Focus**: Weighted toward safety/compliance — Constitutional gates, audit integrity, AWS warning compliance, and tenant isolation receive 2–3× item density.
**Audience**: Reviewer (PR / design review gate)

---

## Requirement Completeness

- [ ] CHK001 — Are the specific input data sources for each of the four governance health score dimensions (constitutional compliance 40%, operational readiness 25%, data source governance 20%, recovery progress 15%) individually identified, or is the mapping left to implementation inference? [Completeness, Spec §FR-001]
- [ ] CHK002 — Are the conditions under which each of the 10 constitutional gates transitions between compliant, non-compliant, partially compliant, and assessment pending defined or cross-referenced to a governing spec? [Completeness, Spec §FR-002]
- [ ] CHK003 — Is the "drill down" navigation model (FR-004) specified with destination views for every summary indicator on the executive summary, or is mapping left ambiguous? [Completeness, Spec §FR-004]
- [ ] CHK004 — Is "governance gap count" in the compliance matrix (FR-005) defined — what constitutes a gap, how gaps are detected, and how the count is calculated? [Completeness, Spec §FR-005]
- [ ] CHK005 — Are requirements for the audit export report layout, content ordering, and metadata inclusion specified for each of the three formats (PDF, CSV, JSON), or only the format names? [Completeness, Spec §FR-012]
- [ ] CHK006 — Are the emergency plan "overdue review" calculation rules specified — which date field is compared, what threshold triggers the flag, and is timezone handling addressed? [Completeness, Spec §FR-014]
- [ ] CHK007 — Are the AIIMS role coverage calculation rules specified — what defines "unassigned" vs "under-staffed" for each role, and what is the denominator for percentage calculations? [Completeness, Spec §FR-016]
- [ ] CHK008 — Are the recovery domain "target trajectory" baselines specified or referenced, so that below-target variance (FR-019) can be calculated against a known standard? [Completeness, Spec §FR-019]
- [ ] CHK009 — Are the mapping rules between RecoveryDomain (5-value type from spec 019) and RecoveryEnvironmentTracker (4-value type from spec 018) explicitly defined, including how the overarching domain aggregates the four concrete domains? [Completeness, Spec §FR-017]
- [ ] CHK010 — Are the role-to-widget mappings exhaustively specified for all 10 AIIMS roles, or only the three examples given (Operations Officer, PIO, Logistics Officer)? [Completeness, Spec §FR-024, US7]
- [ ] CHK011 — Are "highest-authority role" ranking rules defined for multi-role users (FR-025), including the authority hierarchy for all 10 AIIMS roles? [Completeness, Spec §FR-025]
- [ ] CHK012 — Is the set of "governance state changes" that require human confirmation (FR-028) enumerated, or is the boundary between read-only viewing and state-changing actions left implicit? [Completeness, Spec §FR-028]
- [ ] CHK013 — Are requirements for the configurable refresh intervals specified — who can configure them, what are the valid ranges, and where is the configuration stored? [Completeness, Spec §FR-029]
- [ ] CHK014 — Are the cache invalidation rules specified beyond the 5-minute TTL — does a manual refresh bypass the cache, and what happens on data source recovery after an outage? [Completeness, Spec §FR-029]

---

## Constitutional Gate Compliance *(Safety/Compliance — Weighted)*

- [ ] CHK015 — Are requirements for each of the 10 constitutional gates individually traceable to specific functional requirements, or is compliance status treated as an opaque aggregate? [Traceability, Spec §FR-002]
- [ ] CHK016 — Is Gate 4 (transparency and auditability) coverage comprehensive — are all audit-relevant FRs (FR-009 through FR-012, FR-027, FR-028) explicitly cross-referenced as Gate 4 evidence? [Consistency, Gap]
- [ ] CHK017 — Is Gate 9 (PPRR and shared responsibility) coverage traceable to specific FRs for each PPRR phase (Prevention, Preparedness, Response, Recovery), or are some phases unaddressed? [Traceability, Gap]
- [ ] CHK018 — Is Gate 10 (governance and quality gates) coverage traceable to the compliance matrix and health score FRs with explicit mapping? [Traceability, Gap]
- [ ] CHK019 — Are Gates 1, 5, and 10 (referenced in US6 for risk/warning management) individually mapped to specific functional requirements, or only mentioned in the user story rationale? [Traceability, Gap]
- [ ] CHK020 — Is the handling of gates with "assessment pending" status defined in the health score calculation — is it treated as zero, excluded from the denominator, or handled differently? [Completeness, Spec §FR-001, FR-002, Edge Cases]
- [ ] CHK021 — Are requirements defined for what happens when a constitutional gate transitions from compliant to non-compliant — are notification, escalation, or alerting paths specified? [Gap, Exception Flow]
- [ ] CHK022 — Is the constitutional gate assessment frequency or triggering criteria defined — are assessments periodic, event-driven, or both? [Gap]
- [ ] CHK023 — Are the "severity indicator" and "link to detailed compliance view" for non-compliant gates (US1-AS2) specified with sufficient detail for all 10 gates? [Clarity, Spec §US1-AS2]
- [ ] CHK024 — Does the spec define what evidence artefacts constitute proof of compliance for each constitutional gate, or is this deferred to another spec? [Gap, Dependency]

---

## Audit Integrity *(Safety/Compliance — Weighted)*

- [ ] CHK025 — Is the audit trail's immutability requirement explicitly stated in the functional requirements, or only assumed in the Assumptions section? [Completeness, Spec §Assumptions]
- [ ] CHK026 — Are audit entry retention and archival policies specified — how long are records kept, and are there regulatory requirements driving retention periods? [Gap]
- [ ] CHK027 — Are audit export integrity requirements defined — are exported reports tamper-evident, digitally signed, or otherwise verifiable for regulatory submission? [Gap, Spec §FR-012]
- [ ] CHK028 — Is the "provenance reference" field in audit events (FR-009) defined — what does it contain, what format does it use, and how is provenance verified? [Clarity, Spec §FR-009]
- [ ] CHK029 — Are the audit trail search performance requirements consistent between SC-003 (5 seconds for search/retrieval) and US3-AS2 (2 seconds for filtered results)? [Conflict, Spec §SC-003, US3-AS2]
- [ ] CHK030 — Is the scope of "all dashboard interactions" (FR-027) exhaustively enumerated — does it include failed actions, timeout events, session start/end, and error states? [Clarity, Spec §FR-027]
- [ ] CHK031 — Are requirements for audit entry ordering guaranteed — is strict chronological ordering maintained under concurrent writes from multiple users? [Gap]
- [ ] CHK032 — Is the "decision chain" completeness requirement (FR-011) defined for chains that span multiple systems or are partially unavailable? [Edge Case, Spec §FR-011]
- [ ] CHK033 — Are requirements specified for preventing audit trail manipulation by privileged users (e.g., system administrators)? [Gap, Security]
- [ ] CHK034 — Is the PII boundary between audit records (user identity required per Gate 4) and observability telemetry (no PII per FR-035) clearly delineated for every FR that produces log data? [Consistency, Spec §FR-027, FR-035]
- [ ] CHK035 — Are audit records for export actions (FR-027, US8-AS3) specified to include sufficient detail to reconstruct exactly what data left the system, including scope, filters applied, and record count? [Completeness, Spec §FR-027]
- [ ] CHK036 — Are requirements specified for the audit trail's own availability — what happens if the audit logging subsystem is down when a dashboard interaction occurs? [Gap, Exception Flow]

---

## AWS Warning Compliance *(Safety/Compliance — Weighted)*

- [ ] CHK037 — Are the 10 AWS warning principles individually defined with measurable criteria for how compliance with each principle is assessed, or only listed by name? [Completeness, Spec §FR-021A]
- [ ] CHK038 — Is the "per-principle compliance rate" calculation defined — percentage of which population (all warnings, active warnings, warnings within a time range)? [Clarity, Spec §FR-021A]
- [ ] CHK039 — Are requirements for the "drill-down to non-compliant warnings" view specified — what columns, filters, sorting, and detail are shown for each non-compliant warning? [Completeness, Spec §FR-021A]
- [ ] CHK040 — Is the "acceptable approval latency threshold" (FR-022) defined with a concrete default value and configuration mechanism, or only referenced to spec 008 without specification? [Clarity, Spec §FR-022, Assumptions]
- [ ] CHK041 — Are the AWS severity colour tokens (FR-033A) required across an exhaustive list of affected views, or are some warning-severity displays potentially missed? [Coverage, Spec §FR-033A]
- [ ] CHK042 — Are requirements defined for how warnings are classified into AWS 3-tier categories (Advice / Watch and Act / Emergency Warning) — is the classification criteria specified or referenced? [Gap]
- [ ] CHK043 — Is "broadcast reach percentage" (FR-021) defined — reach of which audience, measured by what method, over what time window? [Clarity, Spec §FR-021]
- [ ] CHK044 — Are requirements specified for AWS warning principle compliance trending over time, or is only point-in-time compliance displayed? [Gap, Spec §FR-021A]
- [ ] CHK045 — Are requirements defined for the "overall principle compliance score" aggregation method — is it an average across principles, a weighted score, or a pass/fail count? [Clarity, Spec §FR-021A]

---

## Tenant Isolation *(Safety/Compliance — Weighted)*

- [ ] CHK046 — Is the server-derived tenant context mechanism (Entra ID claims) specified with sufficient detail — which specific claim, what format, and how is the claim validated? [Clarity, Spec §FR-026A]
- [ ] CHK047 — Are requirements for preventing cross-tenant data leakage defined as a mandatory constraint on every data endpoint, or only stated once as a general principle? [Coverage, Spec §FR-026A]
- [ ] CHK048 — Is the "persistent visual tenant indicator" for simulation mode specified with placement, styling, size, and dismissibility rules (or explicit non-dismissibility)? [Clarity, Spec §FR-026A]
- [ ] CHK049 — Are requirements defined for what happens when tenant context cannot be derived from Entra ID claims — e.g., missing, malformed, or expired claims? [Edge Case, Gap]
- [ ] CHK050 — Are audit trail entries explicitly scoped to tenant context — can simulation audit events contaminate live audit records, or vice versa? [Gap, Spec §FR-027, FR-026A]
- [ ] CHK051 — Is the dashboard's default-to-live-tenant behaviour specified for edge cases — users with both live and simulation access, users with simulation-only access? [Completeness, Spec §FR-026A]
- [ ] CHK052 — Are requirements defined for the governance health score calculation in simulation context — is it calculated independently per tenant, or does simulation share the live score? [Gap, Spec §FR-001, FR-026A]
- [ ] CHK053 — Is the edge case of a user's session context changing mid-session (joining a simulation) fully specified — including refresh timing, state preservation, and data continuity? [Completeness, Spec §Edge Cases]
- [ ] CHK054 — Are requirements specified for the compliance matrix, risk register, and recovery dashboard behaving correctly under tenant isolation — are all views confirmed tenant-scoped? [Coverage, Spec §FR-026A]

---

## Requirement Clarity & Measurability

- [ ] CHK055 — Is "standard broadband connection" (SC-002) quantified with specific bandwidth and latency parameters that make the 3-second load target objectively testable? [Ambiguity, Spec §SC-002]
- [ ] CHK056 — Is "navigable" in the degraded mode requirement (SC-007) defined — which specific navigation paths, views, and interactions must remain functional? [Ambiguity, Spec §SC-007]
- [ ] CHK057 — Can "role-appropriate governance information" (SC-001) be objectively determined for each of the 10 AIIMS roles, or does it require subjective interpretation? [Measurability, Spec §SC-001]
- [ ] CHK058 — Is "within 2 navigation steps" (SC-001) defined — does a drill-down count as a step, does scrolling, tab switching, or filtering count? [Ambiguity, Spec §SC-001]
- [ ] CHK059 — Is "render usably on mobile devices" (FR-033) defined with specific criteria beyond minimum viewport width — e.g., touch target sizes, readable font sizes, scrollable regions? [Ambiguity, Spec §FR-033]
- [ ] CHK060 — Is "structured telemetry" (FR-034) specified with a schema definition, required fields, or at minimum the categories of metrics that must be emitted? [Clarity, Spec §FR-034]
- [ ] CHK061 — Are "widget render times" (FR-034) defined with acceptable threshold values, or are they measured without pass/fail criteria? [Gap, Spec §FR-034]
- [ ] CHK062 — Can "90% of users in usability testing" (SC-006) be objectively replicated — are user profiles, task instructions, and testing methodology specified? [Measurability, Spec §SC-006]

---

## Requirement Consistency

- [ ] CHK063 — Is the refresh interval behaviour consistent between FR-029 (30s active / 5min steady-state) and SC-005 ("default 30 seconds") — does SC-005 implicitly apply only during active incidents, or is there a conflict? [Conflict, Spec §FR-029, SC-005]
- [ ] CHK064 — Are the emergency plan lifecycle states in FR-014 confirmed consistent with the 7 states from spec 019's state machine — is the cross-spec dependency verified and is the "Expired" overlay condition non-conflicting? [Consistency, Spec §FR-014]
- [ ] CHK065 — Is "last-known-good data" behaviour (FR-031) consistent with "data staleness indicators" (FR-030) — do both use the same timestamp source and display format? [Consistency, Spec §FR-030, FR-031]
- [ ] CHK066 — Are the recovery domain definitions consistent between FR-017, the Key Entities section, SC-009, and the referenced specs 018 and 019? [Consistency, Spec §FR-017, Key Entities, SC-009]
- [ ] CHK067 — Is the role-based access model (FR-024 through FR-026A) consistent with the "restricted view" for no-role users (FR-026) and the corresponding edge case definition? [Consistency, Spec §FR-026, Edge Cases]
- [ ] CHK068 — Does the "read-only reporting interface" assumption (Assumptions section) conflict with FR-028's reference to "governance state changes initiated from the dashboard"? [Conflict, Spec §Assumptions, FR-028]

---

## Scenario Coverage & Edge Cases

- [ ] CHK069 — Are requirements defined for maximum audit export size — what happens when a user selects thousands of records for PDF export, and are pagination or size limits specified? [Edge Case, Gap]
- [ ] CHK070 — Are requirements specified for the compliance matrix when zero data sources are registered — is empty-state messaging and guidance defined? [Edge Case, Gap]
- [ ] CHK071 — Are requirements defined for the risk register when no risks exist — empty-state behaviour, visual treatment, and messaging? [Edge Case, Gap]
- [ ] CHK072 — Are the concurrent export queuing requirements (Edge Cases section) specified with queue depth limits, timeout behaviour, progress indicators, and failure notification? [Completeness, Spec §Edge Cases]
- [ ] CHK073 — Are requirements defined for dashboard behaviour during role assignment propagation delay — what is shown between role revocation and detection on the next refresh cycle? [Edge Case, Spec §Edge Cases]
- [ ] CHK074 — Are requirements specified for the governance health score when all four input dimensions have stale or entirely missing data? [Edge Case, Spec §FR-001, Edge Cases]
- [ ] CHK075 — Are requirements defined for PPRR phase indicators when no active incident context exists — is there a "peacetime" state? [Edge Case, Gap]
- [ ] CHK076 — Are requirements specified for dashboard behaviour when a data source is deregistered or goes offline while a user is actively viewing its detail panel? [Edge Case, Gap]
- [ ] CHK077 — Are recovery dashboard requirements defined for the case when recovery data spans multiple incidents — is the incident selector's behaviour, default selection, and aggregate view fully specified? [Completeness, Spec §Edge Cases]

---

## Non-Functional Requirements Coverage

- [ ] CHK078 — Are performance requirements specified for views beyond the executive summary — compliance matrix, audit trail, risk register, recovery dashboard, and operational readiness load times? [Gap, Spec §SC-002]
- [ ] CHK079 — Are concurrent user capacity requirements defined — how many simultaneous dashboard users must be supported without degradation? [Gap]
- [ ] CHK080 — Are data volume requirements specified — maximum number of audit entries, risk records, data sources, and recovery records the views must handle? [Gap]
- [ ] CHK081 — Are WCAG 2.1 AA requirements for the companion data tables (FR-032) specified with proper table semantics, captions, row/column scope attributes, and keyboard operability? [Completeness, Spec §FR-032]
- [ ] CHK082 — Are keyboard navigation requirements defined beyond WCAG minimums — including tab order across widgets, focus management for drill-down panels, and modal/side-panel keyboard trapping? [Gap, Spec §FR-032]
- [ ] CHK083 — Are security requirements for the export functionality specified — are exports scoped to the user's authorised data only, and is unauthorised data excluded even if the user crafts filter parameters? [Gap, Security]
- [ ] CHK084 — Are error rate and availability requirements (SLO/SLA) specified for the dashboard as a whole, or only individual widget behaviours? [Gap]

---

## Dependencies & Assumptions

- [ ] CHK085 — Is the assumption that "existing governance data sources expose read-accessible endpoints" validated — are the specific endpoints, data contracts, or API schemas identified? [Assumption, Spec §Assumptions]
- [ ] CHK086 — Are the dependencies on spec 007 (tenant isolation), spec 008 (alert/warning), spec 018 (AIIMS roles), and spec 019 (emergency plans, recovery domains) documented with specific interface requirements and version constraints? [Dependency, Gap]
- [ ] CHK087 — Is the assumption that "audit trail infrastructure already exists" validated with specific requirements for how the dashboard's new event category integrates with existing infrastructure? [Assumption, Spec §Assumptions]
- [ ] CHK088 — Are requirements defined for graceful behaviour when a referenced spec's data model changes — are API versioning, contract dependencies, or backward compatibility strategies specified? [Gap, Dependency]
- [ ] CHK089 — Is the data sovereignty assumption ("Australian regions only, enforced at infrastructure level") documented as an explicit non-requirement for the dashboard, or does the dashboard need to verify region compliance? [Assumption, Spec §Assumptions]
- [ ] CHK090 — Is a requirement and acceptance criteria ID scheme established that enables end-to-end traceability from FR → acceptance scenario → success criteria → implementation → test? [Traceability]

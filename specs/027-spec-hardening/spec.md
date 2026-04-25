# Feature Specification: Capstone Specification Hardening

**Feature Branch**: `027-spec-hardening`
**Created**: 2026-04-24
**Status**: Draft
**Input**: User description: "Harden the disaster-response-hub specification to address the critical review findings: add explicit assumptions, non-functional requirements, persona profiles, falsifiable hypotheses, and scope boundaries. Explicitly document Australia as the v1 primary deployment jurisdiction and the rationale for that decision relative to the Asia-focused capstone brief."

## Summary

A critical review of the existing solution artefacts (`capstone.md`, `specs/001-disaster-response-hub/spec.md`, `plan.md`, `research.md`, architecture and regional-adaptation docs, `README.md`) found the solution to be a well-structured *Australian* disaster-response hub, while the capstone brief is explicitly *Asia-focused* (Philippines typhoons, Japan earthquakes, Bangladesh floods). The resulting ambiguity cascaded into weak assumptions, missing hypotheses, incomplete personas, and a thin scope fence.

This feature hardens the specification set so that:

1. **Australia is explicitly declared the v1 primary deployment jurisdiction**, with the Asia-Pacific brief re-framed as the *vN extension target* rather than a v1 commitment. The rationale, trade-offs, and deferred-scope plan are documented normatively in the spec — not in an annex.
2. Every gap raised by the critical review (A-GAP, REQ-GAP, PER-GAP, HYP-GAP, SCP-GAP series) is resolved by producing normative content in `specs/001-disaster-response-hub/spec.md` and, where needed, supporting persona/hypothesis artefacts.
3. The specification becomes self-sufficient for planning, testing, legal review, and UX evaluation without reliance on scattered plan/architecture notes.

This feature is scoped to `specs/001-disaster-response-hub/spec.md` only. Cross-spec propagation of the same gap taxonomy across the remaining specs (notably 005, 007, 008–012, 018–026) is owned by feature `028-capstone-alignment` and is explicitly deferred from this feature.

> **Scope note (added by feature 028 / T009)**: portfolio-wide cross-spec hardening (assumption / persona / hypothesis / scope-boundary uplift across all 27 specs) is owned by `specs/028-capstone-alignment/spec.md`. This spec (`027-spec-hardening`) remains scoped to `001-disaster-response-hub` only; spec 028 reuses the taxonomies and contracts defined here (FR-005 reuse rule).

## Clarifications

### Session 2026-04-24

- Q: What is the relationship between feature 027 (this hardening spec) and feature 028-capstone-alignment? → A: 027 is scoped to spec 001; 028 handles cross-spec propagation for all other specs.
- Q: Who is authorised to move an Assumption, Hypothesis, or Persona between status values? → A: Role matrix with countersign — domain SME owns Assumption transitions, test lead owns Hypothesis transitions, UX lead owns Persona transitions; every transition requires a countersign by one other named role (planner, privacy reviewer, or the spec's maintainer).
- Q: What constitutes "validation" of a persona for a jurisdiction (FR-016)? → A: SME review by a practitioner currently or formerly in the role, or a documented named proxy (e.g. an AIDR-accredited trainer); the reviewer's name, role, and review date are recorded against the persona.
- Q: What is "the evidence pack" referenced in FR-020 and how is it located? → A: A per-feature `evidence/` folder within the owning spec directory (`specs/<feature>/evidence/<HYP-ID>.md`) containing rehearsal scenario, observed metric, date, observer, and links to supporting artefacts; cited from the hypothesis status by relative path.
- Q: What is the default "target resolution point" for Open Deltas (FR-032)? → A: Bounded to the next `/speckit.plan` — Open Deltas may remain at merge of 027, but each MUST be settled before `/speckit.plan` runs on the affected follow-on feature; owner and target feature ID are recorded per delta.
- Q: Who is the "spec's maintainer" named in FR-034's countersign list? → A: The GitHub CODEOWNERS entry for `specs/001-disaster-response-hub/`; PR review by that code owner constitutes the countersign.
- Q: Who authorises the initial numeric targets on Non-Functional Requirements (FR-004 through FR-010)? → A: Planner drafts with a cited basis (standard, benchmark, or prior rehearsal observation) and the relevant domain SME countersigns; privacy/legal NFRs additionally require the privacy reviewer's sign-off.
- Q: What is the uniqueness & monotonicity rule for Gap IDs across features? → A: Monorepo-wide monotonic register at `specs/shared/gap-id-register.md`; allocations are appended with owning feature; IDs are never reused and never renumbered.
- Q: Must an Evidence Pack file exist at hypothesis creation (status = *Not tested*), or only once the hypothesis transitions? → A: Stub at creation — a stub file MUST exist from the moment the hypothesis is recorded, carrying the hypothesis text, falsification indicator, measurement window, and a "No observations yet" marker; the same file is updated in place at each subsequent status transition.
- Q: Where does the Traceability Table (FR-031) physically live? → A: Canonical table lives in `specs/027-spec-hardening/spec.md` (the change record); `specs/001-disaster-response-hub/spec.md` carries a pointer row in its changelog that links to the 027 table by anchor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capstone alignment is unambiguous to a new reviewer (Priority: P1)

A reviewer (program sponsor, external assessor, or new engineer) who has read only `capstone.md` opens `specs/001-disaster-response-hub/spec.md` and can, within one reading, understand (a) that the v1 implementation targets Australia, (b) why Australia was chosen as the reference jurisdiction for an Asia-framed brief, (c) what Asia-region claims the v1 implementation does *not* validate, and (d) what would have to be true to extend the hub to the Philippines, Japan, or Bangladesh in a later version.

**Why this priority**: The Australia-vs-Asia ambiguity is the single largest scoping defect identified in the review and the root cause of most other gaps. Closing it is a precondition for credible assumption, persona, hypothesis, and scope work.

**Independent Test**: Give the hardened spec to a reviewer who has not seen the Asia-Pacific annex; verify in a structured read-through that they can correctly answer the four questions above without consulting any other document.

**Acceptance Scenarios**:

1. **Given** the hardened spec, **When** a reviewer reads §Scope and §Assumptions, **Then** they find an explicit "v1 Primary Jurisdiction" declaration naming Australia, a dated rationale, and a deferred-scope register for Philippines/Japan/Bangladesh with preconditions for promotion.
2. **Given** the capstone brief states Asia-regional success metrics, **When** the reviewer reads §Success Criteria, **Then** each success criterion is scoped to the v1 Australian evaluation cohort and is not represented as evidence of Asia-wide performance.
3. **Given** the regional-adaptation annex claims "no code changes needed" for Asia, **When** the reviewer reads the hardened spec, **Then** that claim is re-characterised as an *unvalidated extensibility hypothesis* (HYP-006) with a named falsification test, not an architectural guarantee.

---

### User Story 2 - Planner, tester, and legal reviewer can proceed without further clarification (Priority: P1)

A delivery planner, a test lead, a privacy/legal reviewer, and a UX evaluator each pick up the hardened spec and can derive their own artefacts (plan, test matrix, DPIA, evaluation protocol) without raising blocking clarification requests on assumptions, non-functional requirements, personas, or scope.

**Why this priority**: The spec is the single source of truth for downstream work. Gaps in NFRs, personas, and scope currently force every downstream role to make private assumptions, which undermines traceability and rubric scoring.

**Independent Test**: Have each of the four roles review the hardened spec against a structured checklist; verify that no role records a blocking clarification in the areas covered by REQ-GAP, PER-GAP, or SCP-GAP.

**Acceptance Scenarios**:

1. **Given** the hardened spec, **When** the test lead reads §Non-Functional Requirements, **Then** every NFR has a stated target, measurement method, and evaluation surface (operator UI, public alert, API behaviour, audit artefact).
2. **Given** the hardened spec, **When** the privacy reviewer reads §Non-Functional Requirements and §Scope, **Then** PII classification, retention, residency, and cross-border transfer behaviour are stated normatively.
3. **Given** the hardened spec, **When** the UX evaluator reads §Personas, **Then** each persona carries goals, pains, device profile, language(s), authority level, and top-3 tasks, sufficient to design a usability study.
4. **Given** the hardened spec, **When** the planner reads §Scope, **Then** the in-scope hazard list, autonomy boundary table, in-scope data sources, citizen-facing surface, recovery-phase position, and in-scope integrations are each explicit.

---

### User Story 3 - Claims about the solution are falsifiable (Priority: P2)

A program assessor or retrospective facilitator can identify, for each major design claim in the solution, the hypothesis it rests on, the leading indicator that would falsify it, and the measurement window. The assessor can determine, post-exercise, whether any hypothesis has been invalidated and therefore which design decisions need to be revisited.

**Why this priority**: Without falsifiable hypotheses, success criteria are assertions of hope. This prevents learning and weakens rubric scoring on experimentation and evidence.

**Independent Test**: List the six required hypothesis categories from the review (safety-autonomy, signal trust, orchestration, mobile delivery, cross-jurisdictional portability, misinformation resilience); verify each is present in the hardened spec with a falsification condition and measurement window.

**Acceptance Scenarios**:

1. **Given** the hardened spec contains a Hypotheses section, **When** an assessor reviews it, **Then** each hypothesis follows the form *"We believe {capability} will produce {outcome} for {persona}; we will know we are wrong if {leading indicator} is observed in {measurement window}"*.
2. **Given** a rehearsal exercise has been run, **When** the assessor checks the hypotheses register, **Then** every hypothesis has a recorded status (Not tested / Supported / Invalidated / Inconclusive) with a citation to the evidence pack.

### Edge Cases

- A downstream artefact (plan, data model, contract, task list) conflicts with the hardened spec after the update. The hardened spec is authoritative; conflicting artefacts MUST be reconciled in the same feature branch or recorded as open deltas.
- A stakeholder disputes the Australia-as-v1 decision. The decision MUST be revisited only via an explicit change to §Scope with a dated rationale; the Asia-Pacific annex alone does not override it.
- A hypothesis is invalidated mid-feature. The related design decision MUST be re-opened; the hypothesis is not silently removed.
- A persona profile added here conflicts with a role named in spec 001 User Story 2 or 3. Persona profiles are authoritative; role lists in user stories MUST be reconciled.
- Asia-region data (seed files, language packs) already exists in the repository. Its presence does NOT change the v1 scope; it is retained as extensibility evidence only.

## Requirements *(mandatory)*

### Functional Requirements

Each requirement below amends `specs/001-disaster-response-hub/spec.md` (and where noted, `plan.md` or supporting artefacts). "The Spec" below refers to spec 001 unless stated otherwise.

#### Assumptions hardening (resolves A-GAP-001 through A-GAP-008)

- **FR-001**: The Spec MUST contain a dated Assumptions section in which each assumption states: (a) the assumption itself, (b) why it is reasonable, (c) a validation method, (d) an owner role, and (e) a status (Unvalidated / Validated / Invalidated).
- **FR-002**: The Spec MUST include explicit assumptions covering, at minimum: v1 jurisdiction selection and rationale; Asia-region data availability and quality; minimum connectivity floor for field operation; AI/agent quality floor (hallucination rate, false-positive tolerance, multilingual quality); data residency and sovereignty obligations per target country; baseline-exercise availability for success-criteria measurement; legal and statutory standing of AI-generated recommendations; target user device profiles.
- **FR-003**: The Spec MUST record, as an assumption, that Australia has been selected as the v1 primary deployment jurisdiction and that Asia-region claims are deferred to a later version; the assumption MUST cite the capstone-vs-solution divergence as the reason for the explicit statement.

#### Non-functional requirements hardening (resolves REQ-GAP-001 through REQ-GAP-010)

- **FR-004**: The Spec MUST contain a Non-Functional Requirements section. NFRs scattered across `plan.md` or architecture docs MUST be promoted into the Spec and MUST state target, measurement method, and evaluation surface.
- **FR-005**: The Spec MUST include a normative accessibility NFR naming a specific conformance level (WCAG 2.2 AA; EN 301 549 v3.2.1 is the only accepted equivalent) and the surfaces to which it applies (operator dashboard, public web dashboard, public alerts).
- **FR-006**: The Spec MUST include normative privacy NFRs covering PII classification, retention period (including for location data), right-to-erasure behaviour, in-region storage per the jurisdiction of collection, and cross-border transfer rules.
- **FR-007**: The Spec MUST include normative security NFRs covering authentication strength (including multi-factor expectations), session management, key management, and a named threat-model coverage set that includes at least: adversarial signal injection, coordinated misinformation, insider misuse, and credential compromise.
- **FR-008**: The Spec MUST include normative latency and freshness NFRs (for example, authoritative-hazard freshness, dashboard initial load, read-API p95) currently stated in `plan.md` only.
- **FR-009**: The Spec MUST include an interoperability NFR naming at least: a public-alert message standard (e.g. OASIS CAP 1.2), an inter-agency exchange standard (e.g. EDXL-DE) where a counterpart agency exists, and a monitoring-and-evaluation indicator standard (e.g. Sendai Framework indicators) where measurement claims are made.
- **FR-010**: The Spec MUST include a training and change-management NFR stating the onboarding target that Success Criterion SC-003 (unassisted task completion) depends on.
- **FR-011**: The Spec MUST add, or explicitly re-scope, functional requirements for: medical triage recommendations, shelter allocation recommendations, utility isolation (power/gas/water) recommendations, and search-and-rescue tasking; or MUST declare these explicitly out-of-scope for v1 with a rationale.
- **FR-012**: The Spec MUST add a functional requirement for misinformation detection and down-ranking with operator-visible evidence, or MUST declare misinformation handling explicitly out-of-scope for v1 with a rationale.
- **FR-013**: The Spec MUST contain an audit-retention requirement stating retention duration, format, and recoverability SLO for the auditable timeline referenced by the existing FR-012 of spec 001.

#### Persona hardening (resolves PER-GAP-001 through PER-GAP-007)

- **FR-014**: The Spec MUST reference a Personas section (either inline or as a linked artefact within the same feature directory) containing profiles that each include: goals, pains, primary context of use, technical proficiency, time-on-task tolerance, device profile, language(s), authority level, and top-3 tasks the hub must optimise for the persona.
- **FR-015**: The Personas section MUST include profiles for: (a) operational roles — incident commander, operations officer, logistics lead, public information officer, field coordinator, resilience planner, auditor/post-incident reviewer; (b) executive roles — Minister/Premier-equivalent and Mayor/local-government-equivalent; (c) affected-community archetypes — native-language speaker, limited-literacy resident, accessibility-impaired resident (low-vision, hard-of-hearing), tourist/non-resident; (d) adversarial archetypes — misinformation actor, insider threat; (e) accessibility-specific operator archetypes — low-vision operator, hard-of-hearing field worker.
- **FR-016**: Each persona MUST be tagged with the jurisdictions for which it is currently validated. For v1, operational and executive personas MUST be validated for Australia. *Validated* means that a subject-matter expert (SME) who currently holds, formerly held, or is a documented named proxy for the role (e.g. an AIDR-accredited trainer, a published AIIMS course facilitator) has reviewed and signed off the persona profile; the reviewer's name, role/affiliation, and review date MUST be recorded against the persona. Desk-only review against published role descriptions is NOT sufficient. Asia-region equivalents (e.g. NDRRMC Regional Director, JMA Forecaster, Bangladesh Union Parishad Chairman) MUST be listed as *placeholder* profiles in the deferred-scope register, not as validated v1 personas.
- **FR-017**: Success Criterion SC-003 of spec 001 MUST be updated to reference the validated v1 persona set by name so the criterion becomes testable.

#### Hypotheses introduction (resolves HYP-GAP-001 through HYP-GAP-006)

- **FR-018**: The Spec MUST contain a Hypotheses section. Each hypothesis MUST follow the form: *"We believe {capability} will produce {outcome} for {persona}; we will know we are wrong if {leading indicator} is observed in {measurement window}."*
- **FR-019**: The Hypotheses section MUST include at least one hypothesis for each of the following themes: safety-autonomy balance (human-in-the-loop vs autonomous action); signal trust model (authoritative-first with provenance scoring vs naive fusion); orchestration approach (deterministic vs LLM-routed); mobile delivery mode (responsive PWA vs native) under degraded connectivity; cross-jurisdictional framework portability (AIIMS → NDRRMC / Japan / Bangladesh via seed configuration); misinformation resilience.
- **FR-020**: Each hypothesis MUST carry a status field (Not tested / Supported / Invalidated / Inconclusive) and a citation slot referencing its Evidence Pack. The Evidence Pack for a hypothesis HYP-ID MUST live at `specs/<owning-feature>/evidence/<HYP-ID>.md` and MUST exist as a stub from the moment the hypothesis is first recorded (status *Not tested*). The stub MUST contain at minimum: the hypothesis text, the falsification indicator, the measurement window, and a visible "No observations yet" marker. On each subsequent status transition the same file MUST be updated in place to add: the rehearsal or exercise scenario, the observed metric or qualitative finding, the observation date, the observer's name and role, and relative-path links to any supporting artefacts (logs, transcripts, screenshots, data exports). The hypothesis citation in the Spec MUST use the relative path to that file.
- **FR-021**: Existing Success Criteria that embed causal claims (SC-004, SC-005, SC-006 of spec 001) MUST be cross-referenced from at least one hypothesis so that an invalidated hypothesis forces reconsideration of the related success claim.

#### Scope hardening (resolves SCP-GAP-001 through SCP-GAP-009)

- **FR-022**: The Spec MUST contain a "v1 Primary Jurisdiction" subsection that names Australia, states the rationale for choosing Australia despite the Asia-framed capstone brief, and lists the preconditions under which a second jurisdiction may be promoted into scope.
- **FR-023**: The Spec MUST contain a deferred-scope register with entries covering **deferred jurisdictions AND deferred hazards AND any deferred capability** (see FR-024 for the hazard enumeration). At minimum it MUST list Philippines, Japan, and Bangladesh (as named in the capstone). For each row: the reason deferred, the extensibility evidence that already exists in the repository (e.g., seed files, language packs, regional-adaptation annex), and the validation steps required before promotion. Each row MUST carry a `kind` classifier ∈ {`Jurisdiction`, `Hazard`, `Capability`, `Surface`, `Integration`}.
- **FR-024**: The Spec MUST contain an in-scope hazard list for v1 and an explicit out-of-scope hazard list with rationale. The out-of-scope list MUST, at minimum, enumerate **every hazard named in Constitution Principle III that is not promoted into v1 scope** — specifically earthquake, tsunami, extreme heat, pandemic/biosecurity, CBRN, space weather, and cyber-physical infrastructure attack. Silent exclusion is forbidden: any Principle III hazard absent from the in-scope list MUST appear in the Deferred-Scope Register (FR-023) with a reason, extensibility-evidence citation, and promotion preconditions.
- **FR-025**: The Spec MUST contain an autonomy-boundary table classifying each category of agent action as one of {advisory-only, human-approved (HITL), auto-executable with operator override window}. Categories MUST include at minimum: public alert publication, evacuation routing, resource pre-positioning, SMS/voice alert drafting, recommendation re-prioritisation on new signals, field-task assignment, de-escalation/closure.
- **FR-026**: The Spec MUST enumerate in-scope community-signal and social-media data sources for v1 (platform, licensing basis, moderation obligation) and MUST exclude all others.
- **FR-027**: The Spec MUST state whether the Recovery phase of the Prevention–Preparedness–Response–Recovery (PPRR) model is in scope for v1. If out of scope, the Spec MUST describe the hand-off contract expected from the hub to a downstream recovery system.
- **FR-028**: The Spec MUST state whether each of the following citizen-facing surfaces is in scope for v1: public web dashboard, push-notification mobile app, two-way SMS, voice IVR. Surfaces not in scope MUST be listed explicitly.
- **FR-029**: The Spec MUST list in-scope upstream/downstream integrations for v1 (e.g. CAD, EOC, GIS/mapping, utilities SCADA, telco cell-broadcast, meteorology authority feed) and MUST exclude all others with rationale.
- **FR-030**: The Spec MUST state whether rehearsal/simulation scenario content is shipped with v1, imported from an external authoring tool, or user-authored, and MUST fix the boundary.

#### Traceability and maintenance

- **FR-031**: The canonical Traceability Table — mapping each new FR / NFR / Assumption / Hypothesis / Scope-boundary item in this hardening feature to the originating gap identifier (A-GAP-###, REQ-GAP-###, PER-GAP-###, HYP-GAP-###, SCP-GAP-###) from the critical review — MUST live in `specs/027-spec-hardening/spec.md`. `specs/001-disaster-response-hub/spec.md` MUST NOT duplicate the table; instead, its changelog (FR-033) MUST carry a pointer row referencing the canonical table by markdown anchor (e.g. `specs/027-spec-hardening/spec.md#traceability-table`). If the canonical table moves, the pointer is the only place in spec 001 that needs to be updated.
- **FR-032**: Downstream artefacts in the `specs/001-disaster-response-hub/` directory (plan.md, data-model.md, contracts/, quickstart.md, tasks.md) MUST be inspected for contradictions with the hardened spec. Each contradiction MUST be either resolved in this feature branch or logged in an Open Deltas subsection of the Spec. Each Open Delta MUST record: (a) the contradiction statement, (b) the owner role, (c) the follow-on feature ID under which it will be settled, and (d) the firm resolution deadline — which MUST be *"before `/speckit.plan` runs on the owning follow-on feature"*. Open Deltas that miss this deadline MUST block `/speckit.plan` on that feature until they are resolved or explicitly re-assigned with a new feature ID.
- **FR-033**: The hardened Spec MUST carry a "Last reviewed" date and a summary changelog entry referencing this feature (027) as the source of the hardening changes.
- **FR-034**: The hardened Spec MUST contain a "Status-transition authority" subsection that names, for each state-bearing artefact, the role authorised to propose a transition and the role required to countersign it. The authority matrix MUST be at minimum: Assumption status transitions are proposed by the domain subject-matter expert (SME) named as assumption owner and countersigned by the planner or privacy reviewer; Hypothesis status transitions are proposed by the test lead and countersigned by the planner; Persona validation transitions (per-jurisdiction) are proposed by the UX lead and countersigned by the domain SME for that jurisdiction. Where the countersign role list references "the spec maintainer", the maintainer is the GitHub code owner listed for `specs/001-disaster-response-hub/` in `.github/CODEOWNERS`; PR approval by that code owner constitutes the countersign. A transition is not considered effective until both signatures are recorded in the audit changelog referenced by FR-033.
- **FR-035**: Every NFR introduced by FR-004 through FR-010 MUST carry (a) a numeric or categorical target, (b) a *basis citation* naming the authoritative source of the target (e.g. a published standard, an industry benchmark, a prior rehearsal observation, or a statutory instrument), (c) the planner's name as drafter, and (d) the countersigning domain SME's name. Privacy, legal, security, and data-residency NFRs (including those introduced by FR-006 and FR-007) additionally require the privacy reviewer's name as a second countersigner; for all other NFR categories the `privacy_reviewer` field MUST be recorded literally as `N/A`. An NFR that lacks basis, drafter, or countersigner — or that records `N/A` where a privacy reviewer is required — is treated as *provisional* and MUST be listed in the Open Deltas subsection under the Open Delta governance defined in FR-032.
- **FR-036**: Gap identifiers (A-GAP-###, REQ-GAP-###, PER-GAP-###, HYP-GAP-###, SCP-GAP-###) MUST be allocated from a monorepo-wide monotonic register maintained at `specs/shared/gap-id-register.md`. Every allocation MUST append a row recording: prefix, number, owning feature ID, allocation date, and one-line summary. IDs MUST NOT be reused and MUST NOT be renumbered once committed; a withdrawn gap remains in the register with status *Withdrawn* and a reason. Feature 027 owns the seeding of this register with the gap IDs already cited in the critical review.

### Key Entities

- **Gap**: A shortfall identified by the critical review, identified by code (A-GAP-###, REQ-GAP-###, PER-GAP-###, HYP-GAP-###, SCP-GAP-###) and severity.
- **Assumption**: A stated belief the solution relies on, with validation method, owner, and status.
- **Non-Functional Requirement**: A normative quality attribute with target, measurement method, and evaluation surface.
- **Persona**: A user archetype profile with goals, pains, context, device, language(s), authority level, top-3 tasks, and validated-jurisdiction tags.
- **Hypothesis**: A falsifiable belief with leading indicator, measurement window, status, and Evidence Pack citation.
- **Evidence Pack**: A per-hypothesis markdown file at `specs/<owning-feature>/evidence/<HYP-ID>.md` recording the rehearsal scenario, observed metric or finding, observation date, observer identity, and links to supporting artefacts; the authoritative citation target for a hypothesis status transition.
- **Scope Boundary**: An explicit statement of in-scope or out-of-scope behaviour for v1, with rationale.
- **Deferred-Scope Entry**: A named future-version candidate (e.g. Philippines, Japan, Bangladesh) with preconditions for promotion.
- **Traceability Link**: A mapping from a Gap to one or more FR/NFR/Assumption/Hypothesis/Scope items that resolve it.

### Assumptions

- The critical review findings cited in the Input are accepted as authoritative for this feature; they are not re-litigated here. If they are disputed, disputes are raised in a separate feature, not by silently weakening the hardened content.
- The existing Asia-Pacific regional adaptation annex (`docs/disaster-response-hub/regional-adaptation-asia-pacific.md`) remains in the repository as extensibility evidence but loses any implicit authority to re-scope the solution.
- Australia is selected as the v1 reference jurisdiction because (a) the build team's domain evidence (AIIMS, AIDR handbooks, Bureau of Meteorology feeds, state SES workflows) is strongest there, (b) Australian emergency-management governance provides a coherent legal and statutory frame for safety-critical AI, and (c) a single validated jurisdiction produces more credible evidence than partial coverage of several.
- The hardening feature is documentation-led; no runtime behaviour changes are required by this feature itself. Code changes that become necessary because a hypothesis is invalidated are handled in follow-on features.

### Out of Scope

- Implementing the Asia-region extensions (Philippines, Japan, Bangladesh) themselves. This feature only *documents* their deferral.
- Propagating the hardening taxonomy (A-GAP / REQ-GAP / PER-GAP / HYP-GAP / SCP-GAP) across specs other than `specs/001-disaster-response-hub/spec.md`. That cross-spec propagation is owned by feature `028-capstone-alignment` and MUST NOT be duplicated here.
- Renegotiating capstone success metrics. The hardened spec may re-scope the *evaluation cohort* of existing success criteria (e.g. to the Australian cohort) but does not change the numeric targets in the capstone.
- Rewriting architecture, data model, contracts, or task plan. These are only amended where they directly contradict the hardened spec; deeper rework is handled in follow-on features.
- Producing the rehearsal evidence that would *settle* the new hypotheses. Hypotheses are introduced with status "Not tested"; actual settlement is a separate rehearsal activity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a structured read-through, 100% of reviewers can correctly answer four questions from User Story 1 (v1 jurisdiction, rationale, un-validated Asia claims, extension preconditions) using only the hardened spec.
- **SC-002**: Each of the identified gaps (8 A-GAP, 10 REQ-GAP, 7 PER-GAP, 6 HYP-GAP, 9 SCP-GAP, per the critical review) is traceable to at least one FR / NFR / Assumption / Hypothesis / Scope-boundary item in the hardened spec via the §Traceability table.
- **SC-003**: 100% of non-functional requirements carry a named target, measurement method, and evaluation surface.
- **SC-004**: 100% of persona profiles in the validated-for-v1 set carry goals, pains, device profile, language(s), authority level, and top-3 tasks.
- **SC-005**: 100% of hypotheses in the Hypotheses section conform to the required form (capability → outcome → persona → falsification indicator → measurement window) and carry a status field.
- **SC-006**: At least one hypothesis exists for each of the six required themes (safety-autonomy, signal trust, orchestration, mobile delivery, cross-jurisdictional portability, misinformation resilience).
- **SC-007**: The autonomy-boundary table classifies 100% of agent-action categories named in FR-025 into one of the three autonomy classes.
- **SC-008**: Downstream artefact inspection (plan.md, data-model.md, contracts/, quickstart.md, tasks.md of spec 001) records zero unreconciled contradictions; any unresolved items are listed in §Open Deltas with owner and target resolution point.
- **SC-009**: A sampled privacy reviewer and a sampled test lead each derive their initial artefact (DPIA outline; test matrix) from the hardened spec without raising a blocking clarification request in the areas covered by REQ-GAP, PER-GAP, or SCP-GAP.
- **SC-010**: The hardened spec's §Scope unambiguously states Australia as the v1 primary deployment jurisdiction in language that contradicts any prior implication of Asia-region v1 coverage; a keyword search for "Australia" in §Scope returns a declaration within the first 200 words of the section.

### Evaluation Method

- A documentation-quality review is conducted against the checklist generated for this feature (at `specs/027-spec-hardening/checklists/requirements.md`).
- Gap traceability is verified by a one-to-many mapping check from each Gap ID in the critical review to the §Traceability table in the hardened spec 001.
- Stakeholder readiness is verified by walk-throughs with a planner, a test lead, a privacy reviewer, and a UX evaluator.

---

## Traceability Table

> Canonical per FR-031. Every Gap ID raised by the 027 critical review resolves to one or more normative items authored in `specs/001-disaster-response-hub/spec.md`. `specs/001-disaster-response-hub/spec.md` § Changelog carries a pointer row only — no duplicate table.

| gap_id | short_title | category | resolved_by | evidence_pack | status |
| --- | --- | --- | --- | --- | --- |
| A-GAP-001 | v1 jurisdiction selection rationale unstated | Assumption | spec 001 § Scope — v1 Primary Jurisdiction; ASM-001, ASM-008 | N/A | Resolved |
| A-GAP-002 | Asia-region data availability and quality unasserted | Assumption | spec 001 ASM-002; § Scope — Deferred-Scope Register (DEF-001..003) | N/A | Resolved |
| A-GAP-003 | Capstone-vs-solution jurisdiction divergence uncallouted | Assumption | spec 001 ASM-001; § Open Deltas OD-001; § Hypotheses HYP-006 | evidence/HYP-006.md | Resolved |
| A-GAP-004 | Minimum connectivity floor for field operation unstated | Assumption | spec 001 ASM-003; NFR-005; § Hypotheses HYP-004 | evidence/HYP-004.md | Resolved |
| A-GAP-005 | AI/agent quality floor unstated | Assumption | spec 001 ASM-004; NFR-004 (reliability rollback trigger) | N/A | Resolved |
| A-GAP-006 | Data residency and sovereignty obligations per target country unstated | Assumption | spec 001 ASM-005; NFR-002; NFR-009 | N/A | Resolved |
| A-GAP-007 | Baseline-exercise availability for SC-004..SC-006 unstated | Assumption | spec 001 ASM-006; § Success Criteria SC-004..SC-006 (cohort-scoped) | N/A | Resolved |
| A-GAP-008 | Legal / statutory standing of AI-generated recommendations unstated | Assumption | spec 001 ASM-007; § Scope — Autonomy Boundary Table | N/A | Resolved |
| REQ-GAP-001 | NFRs scattered across plan.md and not promoted into spec | Requirement | spec 001 § Non-Functional Requirements (NFR-001..013) | N/A | Resolved |
| REQ-GAP-002 | Accessibility NFR conformance level absent | Requirement | spec 001 NFR-001; NFR-013 | N/A | Resolved |
| REQ-GAP-003 | Privacy NFRs absent | Requirement | spec 001 NFR-002; NFR-007; NFR-009 (APP-8 + residency) | N/A | Resolved |
| REQ-GAP-004 | Security NFRs absent | Requirement | spec 001 NFR-003; NFR-012 | N/A | Resolved |
| REQ-GAP-005 | Performance / freshness NFRs not promoted | Requirement | spec 001 NFR-005 | N/A | Resolved |
| REQ-GAP-006 | Interoperability NFR (CAP / EDXL-DE / Sendai) absent | Requirement | spec 001 NFR-006; § Scope — Upstream/Downstream Integrations | N/A | Resolved |
| REQ-GAP-007 | Training & change-management NFR absent | Requirement | spec 001 NFR-011 | N/A | Resolved |
| REQ-GAP-008 | Medical triage / shelter / utility isolation / SAR FR gap | Requirement | spec 001 § Scope — Deferred-Scope Register (DEF-011..014) | N/A | Resolved |
| REQ-GAP-009 | Misinformation detection FR absent | Requirement | spec 001 § Scope — Autonomy Boundary Table; § Hypotheses HYP-005; NFR-007 | evidence/HYP-005.md | Resolved |
| REQ-GAP-010 | Audit-retention NFR absent | Requirement | spec 001 NFR-008; NFR-012 | N/A | Resolved |
| PER-GAP-001 | Persona schema absent | Persona | spec 001 § Personas (18 profiles with goals/pains/authority/top-3 tasks) | N/A | Resolved |
| PER-GAP-002 | AIIMS operational personas unvalidated | Persona | spec 001 § Personas — Operational cohort (P-OPS-IC, P-OPS-OPS, P-OPS-LOG, P-OPS-PIO, P-OPS-FIELD, P-OPS-PLAN, P-OPS-AUDIT) | N/A | Resolved |
| PER-GAP-003 | Executive personas absent | Persona | spec 001 § Personas — Executive cohort (P-EXEC-MIN, P-EXEC-MAYOR) | N/A | Resolved |
| PER-GAP-004 | CALD / community archetype personas absent | Persona | spec 001 § Personas — Community cohort (P-COM-CALD-HH, P-COM-REMOTE, P-COM-FIRSTNATIONS, P-COM-DISAB, P-COM-TOURIST) | N/A | Resolved |
| PER-GAP-005 | Adversarial personas absent | Persona | spec 001 § Personas — Adversarial cohort (P-ADV-MISINFO, P-ADV-INSIDER) | N/A | Resolved |
| PER-GAP-006 | Accessibility-specific operator personas absent | Persona | spec 001 § Personas — Accessibility-operator cohort (P-ACC-SCREEN, P-ACC-VOICE) | N/A | Resolved |
| PER-GAP-007 | Persona SME-validation provenance absent | Persona | spec 001 § Personas — YAML front-matter `validated_by` on every persona | N/A | Resolved |
| HYP-GAP-001 | Safety-autonomy balance unfalsifiable | Hypothesis | spec 001 HYP-001 | evidence/HYP-001.md | Resolved |
| HYP-GAP-002 | Signal trust model unfalsifiable | Hypothesis | spec 001 HYP-002 | evidence/HYP-002.md | Resolved |
| HYP-GAP-003 | Orchestration approach unfalsifiable | Hypothesis | spec 001 HYP-003 | evidence/HYP-003.md | Resolved |
| HYP-GAP-004 | Mobile delivery under degraded connectivity unfalsifiable | Hypothesis | spec 001 HYP-004 | evidence/HYP-004.md | Resolved |
| HYP-GAP-005 | Misinformation resilience unfalsifiable | Hypothesis | spec 001 HYP-005 | evidence/HYP-005.md | Resolved |
| HYP-GAP-006 | Cross-jurisdictional framework portability unfalsifiable | Hypothesis | spec 001 HYP-006; § Open Deltas OD-001 | evidence/HYP-006.md | Resolved |
| SCP-GAP-001 | v1 Primary Jurisdiction not declared | Scope | spec 001 § Scope — v1 Primary Jurisdiction | N/A | Resolved |
| SCP-GAP-002 | Deferred-Scope Register absent | Scope | spec 001 § Scope — Deferred-Scope Register (DEF-001..016) | N/A | Resolved |
| SCP-GAP-003 | In-scope vs out-of-scope hazard list absent | Scope | spec 001 § Scope — Hazard List (H-001..011) | N/A | Resolved |
| SCP-GAP-004 | Autonomy-boundary table absent | Scope | spec 001 § Scope — Autonomy Boundary Table | N/A | Resolved |
| SCP-GAP-005 | Community-signal source enumeration absent | Scope | spec 001 § Scope — Community Signal Sources; NFR-007 | N/A | Resolved |
| SCP-GAP-006 | Recovery (PPRR) stance unfixed | Scope | spec 001 § Scope — Recovery (PPRR) Stance; DEF-015 | N/A | Resolved |
| SCP-GAP-007 | Citizen-facing surface list absent | Scope | spec 001 § Scope — Citizen-Surface List | N/A | Resolved |
| SCP-GAP-008 | Upstream / downstream integration list absent | Scope | spec 001 § Scope — Upstream/Downstream Integrations | N/A | Resolved |
| SCP-GAP-009 | Rehearsal content boundary unfixed | Scope | spec 001 § Scope — Rehearsal Content Boundary | N/A | Resolved |

---

## Last Reviewed

**2026-04-24** — hardened release authored by feature 027-spec-hardening (see spec 001 § Changelog).


## Assumptions

> Cross-reference: spec 027 is the *meta-contract* defining the assumption taxonomy itself (FR-001..FR-005 of this spec). Feature `028-capstone-alignment` reuses these definitions across the remaining 26 specs.

- **ASM-082**: The taxonomy and YAML contracts in `specs/027-spec-hardening/contracts/*.md` are authoritative for the AMA portfolio; feature 028 and any subsequent hardening features defer to them rather than redefining shapes.
- **ASM-083**: Spec 027's scope is intentionally limited to `specs/001-disaster-response-hub/spec.md`; cross-spec propagation is owned by feature 028.

## Personas

> Cross-reference: persona-profile YAML schema at `specs/027-spec-hardening/contracts/persona-profile.md` is authoritative for the portfolio; this spec defines the contract rather than enumerating personas.

- **PER-073**: cross-ref to `specs/001-disaster-response-hub/spec.md` § Personas (the validated v1 persona set covered by spec 001's PER-001..PER-NNN).

## Hypotheses

- **HYP-025**: If feature 027's hardening taxonomy is faithfully reused by feature 028 (FR-005 reuse rule), then the AMA rubric criterion mean across the 26 propagated specs rises by at least +1 band relative to `specs/028-capstone-alignment/evidence/rubric-baseline.md` baseline. **Falsification**: post-feature rubric snapshot shows regression. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-025.md` (created in feature 028 polish).

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs all capstone-critical-path specs (001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023).

- **SCP-082** [META]: This spec is delivery-hygiene / enabling infrastructure. It defines portfolio-wide hardening taxonomies but is itself **not** on the capstone outcome critical path. (Verbatim canonical meta-flag bullet added by feature 028 / US4 / T056.)
- **SCP-083**: Cross-spec propagation across specs other than 001 — owned by feature 028.


# Feature Specification: Autonomous Disaster Response Coordination Hub

**Feature Branch**: `001-disaster-response-hub`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "I am building a modern and cloud-native solution that is an autonomous disaster response co-ordination hub for natural disasters across the many jurisdictions of Australia. The solution must identify and analyse all organisations involved, the frameworks they use, how they operate individually and collectively, support personas from each organisation, ingest signals from weather sensors, IoT sources, social media, and provide sleek, standout dashboards and pages."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Coordinate a live multi-agency incident (Priority: P1)

An incident commander or state coordination lead opens the hub during a live bushfire or flood and gets a shared operating picture that combines authoritative warnings, field signals, community reports, and cross-agency responsibilities. The user can understand which organisations are involved, which framework rules apply in that jurisdiction, what each organisation is doing, what coordinated actions are recommended next, and whether a public alert is ready for human approval and publication.

**Why this priority**: Coordinated decision-making during an active incident has the highest life-safety impact and is the main reason the hub exists.

**Independent Test**: Can be fully tested by simulating a multi-jurisdiction incident, loading live and historical signals, and verifying that an incident commander can see the participating organisations, applicable frameworks, current status, cross-agency recommended actions, and complete an approved public-alert workflow without needing any other feature slice.

**Acceptance Scenarios**:

1. **Given** an active disaster affecting more than one Australian jurisdiction, **When** the incident commander opens the incident workspace, **Then** the system shows the participating organisations, current incident status, jurisdiction boundaries, applicable command frameworks, and prioritised cross-agency actions in one view.
2. **Given** a new high-confidence hazard update or field report, **When** it materially changes risk or coordination priorities, **Then** the system updates the shared operating picture, records the source and freshness of the update, and highlights the impacted organisations and actions.
3. **Given** a recommended action affects multiple agencies, **When** the incident commander reviews it, **Then** the system explains the rationale, shows dependencies and trade-offs, and records approval, rejection, or escalation.
4. **Given** an approved recommendation requires public communication, **When** the incident commander prepares a public alert, **Then** the system presents the audience, language, channel, and approval details required to review and publish the alert safely.

---

### User Story 2 - Work through a role-specific operational view (Priority: P2)

An operator from a participating organisation such as emergency services, fire, police, health, local government, utilities, transport, meteorology, or community support accesses a persona-specific workspace tailored to their role. They can see only the tasks, obligations, requests, and information needed for their organisation while still understanding how their work connects to the wider response effort.

**Why this priority**: The hub must serve many organisations and personas; without role-specific views, shared coordination becomes noisy and operational adoption drops.

**Independent Test**: Can be tested by assigning multiple personas to the same incident and verifying that each sees relevant tasks, responsibilities, inbound requests, escalation paths, and inter-agency dependencies appropriate to their role.

**Acceptance Scenarios**:

1. **Given** an authenticated user mapped to a specific organisation and persona, **When** they open the hub, **Then** the system presents a role-specific view of the incident, showing relevant tasks, incoming requests, approvals, and dependencies with other organisations.
2. **Given** the user is responsible for an action that depends on another organisation, **When** they inspect the action, **Then** the system shows the dependency chain, current owner, expected timing, and any blockers.
3. **Given** a user changes status on a task or request, **When** the update is saved, **Then** the shared operating picture reflects the change and the relevant counterpart organisations are notified.

---

### User Story 3 - Prepare and analyse agency operating models before an event (Priority: P3)

A resilience planner, policy lead, or program administrator uses the hub outside an active disaster to catalogue organisations, frameworks, responsibilities, decision rights, communication pathways, and personas across Australian jurisdictions. They can analyse how agencies operate individually and collectively, identify gaps or overlaps, and rehearse disaster scenarios before a real event.

**Why this priority**: Preparedness data is required for credible live coordination, but it can be delivered after the core incident workflow and still provide standalone value.

**Independent Test**: Can be tested by onboarding a jurisdiction, defining organisations and personas, mapping frameworks and responsibilities, and verifying that users can review agency relationships, escalation paths, and scenario outcomes without running a live incident.

**Acceptance Scenarios**:

1. **Given** a planner is configuring a jurisdiction, **When** they add participating organisations and frameworks, **Then** the system captures roles, responsibilities, decision rights, contact paths, and coordination relationships.
2. **Given** a framework or agency responsibility differs by jurisdiction, **When** the planner reviews the model, **Then** the system clearly shows the differences and the resulting operational implications.
3. **Given** a rehearsal scenario is run using the configured operating model, **When** the simulation completes, **Then** the system produces a review of coordination gaps, duplicated responsibilities, and delayed decisions.

### Edge Cases

- Conflicting signals arrive from authoritative sources, sensors, and social media for the same location and time window.
- A single disaster spans multiple jurisdictions with different command structures, approval rules, and communication obligations.
- A participating organisation is missing required persona mappings or has incomplete responsibilities defined before an incident begins.
- Connectivity is degraded for field operators, causing delayed updates or partial data visibility.
- A misinformation burst or anomalous sensor feed creates a sudden spike in low-trust alerts.
- Communities affected by the incident require different languages, accessibility needs, or communication channels than the default alert profile.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a catalogue of Australian disaster-response organisations across Commonwealth, state, territory, local government, utility, health, transport, community, and volunteer sectors, including each organisation's role, jurisdiction, and participation conditions.
- **FR-002**: The system MUST maintain a catalogue of operating frameworks, command structures, approval rules, and escalation models used by each jurisdiction and organisation, including how those frameworks interact during shared incidents.
- **FR-003**: The system MUST allow authorised users to define and manage personas for each participating organisation, including responsibilities, decision rights, information needs, and communication pathways.
- **FR-004**: The system MUST ingest and normalise incident-relevant signals from authoritative weather and hazard feeds, IoT and sensor networks, field reports, public submissions, and social or community channels.
- **FR-005**: The system MUST attach provenance, freshness, confidence, and jurisdiction metadata to every ingested signal and display that metadata wherever the signal influences a recommendation or alert.
- **FR-006**: The system MUST present a live, shared operating picture that combines incident status, impacted locations, organisation participation, framework context, risks, tasks, and recommended actions.
- **FR-007**: The system MUST provide role-specific workspaces so each persona can view relevant tasks, requests, approvals, obligations, and cross-agency dependencies without losing visibility of how their work affects collective outcomes.
- **FR-008**: The system MUST explain how organisations operate individually and collectively for a given incident or jurisdiction, including ownership boundaries, dependencies, handoffs, and coordination bottlenecks.
- **FR-009**: The system MUST generate recommendations for evacuation, communication, and resource prioritisation that can be reviewed, approved, rejected, or escalated by authorised human operators.
- **FR-010**: The system MUST support multilingual, accessible public communication workflows that tailor message content, urgency, and delivery channels to affected communities and jurisdictional obligations.
- **FR-011**: The system MUST provide a distinctive, high-clarity dashboard and supporting pages that are visually suitable for high-pressure operations, executive briefings, and public-sector stakeholder demonstrations.
- **FR-012**: The system MUST record an auditable timeline of key signals, recommendations, approvals, alerts, and inter-agency actions for live response, rehearsal, and post-incident review.
- **FR-013**: The system MUST support preparedness analysis by allowing authorised users to model jurisdictions, run scenario rehearsals, and identify coordination gaps, duplicated responsibilities, and delayed decision points.
- **FR-014**: The system MUST continue providing clearly marked reduced-function operation when one or more data sources become unavailable, stale, or untrusted.
- **FR-014a**: In reduced-function operation, the system MUST visibly identify degraded inputs, suppress or down-rank affected recommendations, and show operators which decisions now require manual review.

### Key Entities *(include if feature involves data)*

- **Organisation**: A participating agency, authority, service, utility, council, community body, or volunteer group involved in disaster preparedness or response; includes jurisdiction, operating role, responsibilities, and contact pathways.
- **Persona**: A role performed by a user within an organisation, such as incident commander, operations officer, logistics lead, public information officer, field coordinator, or planner; includes permissions, decision rights, and information needs.
- **Jurisdiction**: A geographic and governance boundary such as Commonwealth, state, territory, regional, or local area; includes applicable frameworks, authorities, and policy constraints.
- **Operating Framework**: The command, control, approval, and escalation model that governs how organisations collaborate within a jurisdiction or incident.
- **Incident**: A disaster event or rehearsal scenario with a type, severity, impacted areas, participating organisations, active tasks, and evolving status.
- **Signal**: A single ingested data point or aggregated observation from weather feeds, sensors, field reports, social channels, or public sources; includes provenance, freshness, confidence, and location.
- **Recommendation**: A proposed evacuation, resource, communication, or coordination action generated from current incident context and supporting signals.
- **Coordination Task**: A tracked action, request, or approval assigned to an organisation or persona with dependencies, timing, and status.
- **Public Alert**: A community-facing message with audience, language, accessibility attributes, urgency, channel plan, and approval state.

### Assumptions

> Normative table per FR-001 + FR-002 + FR-034 of `specs/027-spec-hardening/spec.md`. Narrative bullets previously in this section have been promoted into `ASM-001` through `ASM-008` below. `drafter` and `countersigner` cells name the accountable AMA role; concrete individuals are populated during PR review per the dual-control rule in § Status-transition authority.

| assumption_id | statement | basis | test | owner | drafter | countersigner | status | last_reviewed | linked_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASM-001 | Australia is the v1 primary deployment jurisdiction; Asia-region claims from the capstone brief are deferred and must not be treated as architectural guarantees. | `capstone.md` §Domain Scenario; SCP-GAP-001 critical-review finding; AIDR *Australian Disaster Resilience Handbook Collection*; NEMA *Australian Government Crisis Management Framework* (2022). | Two independent reviewers reading only `capstone.md` and spec 001 answer "which jurisdiction is v1?" with "Australia" without consulting any other document. | Product Owner (AMA) | `product-owner-ba` | `solution-architect` | Proposed | 2026-04-24 | A-GAP-003, SCP-GAP-001 |
| ASM-002 | Asia-region (Philippines / Japan / Bangladesh) operational data feeds, taxonomies, and message-standard conformance are of **unknown** quality and availability for v1 and MUST NOT be assumed equivalent to Australian feeds. | `docs/disaster-response-hub/regional-adaptation-asia-pacific.md`; NDRRMC / JMA / Bangladesh-MoDMR publication inventories. | Cross-jurisdictional rehearsal against a non-Australian feed surfaces ≥ 1 parity gap per theme (provenance, freshness, taxonomy, language). | Resilience Planner (AMA) | `product-owner-ba` | `data-engineer` | Proposed | 2026-04-24 | A-GAP-002 |
| ASM-003 | Field operators are expected to work under an *intermittent connectivity floor* of ≥ 64 kbps for authoritative alert retrieval and ≥ 2 G-equivalent for situation-picture refresh over ≤ 30-minute outage windows. | AIDR *Communicating with People in Disasters* (2020); NBN Co regional coverage maps; BoM field-telemetry practice. | Degraded-connectivity rehearsal at the stated floor completes the P1 acceptance scenario without operator workaround. | Field Coordinator Lead (AMA) | `product-owner-ba` | `field-coordinator` | Proposed | 2026-04-24 | A-GAP-004 |
| ASM-004 | AI / agent components operate above a published quality floor: ≤ 2 % hallucination rate on domain-grounded retrieval, ≤ 5 % false-positive rate on alert triage, and full BCP-47 coverage for Australian English, and ≥ 1 CALD language (Simplified Chinese) at v1. | Internal evaluation harness (proposed); Microsoft Responsible AI practices; OAIC AI Principle 4 (Reliability and Safety). | Weekly offline eval harness report below any floor triggers automatic roll-back per NFR-004. | AI Platform Lead (AMA) | `product-owner-ba` | `ai-ml-engineer` | Proposed | 2026-04-24 | A-GAP-005 |
| ASM-005 | All operational and audit data remains in **Australian Azure regions** (Australia East primary, Australia Southeast DR); no cross-border transfer of operational PII without an explicit APP-8 disclosure register entry. | *Privacy Act 1988* (Cth) + OAIC APP-8; AMA Constitution §Non-Negotiable-2; Australian Government Information Security Manual (ISM). | Azure Policy `allowed-locations` compliance report is 100 % for every subscription in scope. | Privacy Counsel (AMA) | `product-owner-ba` | `compliance-auditor` | Proposed | 2026-04-24 | A-GAP-006 |
| ASM-006 | Baseline exercise packs suitable for computing SC-004 / SC-005 / SC-006 relative improvements (same scenario, same jurisdiction, same roles) are available from at least one Australian tier-1 emergency-management agency by the first v1 evaluation cycle. | AIDR / AFAC exercise library; NSW RFS and VIC CFA public after-action reviews. | Pre-v1 evaluation readiness review confirms ≥ 1 baseline pack per measured SC; otherwise the SC is marked *provisional* with an Open Delta. | Resilience Planner (AMA) | `product-owner-ba` | `resilience-planner` | Proposed | 2026-04-24 | A-GAP-007 |
| ASM-007 | AI-generated coordination recommendations have **advisory** legal standing only; statutory authority for safety-critical decisions (evacuation, public alerts, resource requisition) remains with the human incident controller under the relevant state Emergency Management Act. | State EM Acts (NSW, VIC, QLD, WA, SA, TAS, ACT, NT); AIIMS-5 §2 Command; Constitution §Non-Negotiable-1. | Legal review of every hub-generated recommendation category confirms advisory-only framing; no statutory authority claims appear in UI copy. | Legal Counsel (AMA) | `product-owner-ba` | `compliance-auditor` | Proposed | 2026-04-24 | A-GAP-008 |
| ASM-008 | Target device profiles at v1 are: (a) operator workstation — modern Chromium / Firefox on Windows / macOS at ≥ 1366×768; (b) field / executive mobile — iOS 16+ or Android 12+ on 4G or better, touch-first; (c) degraded field — the same device at ASM-003's connectivity floor. | Internal device-support policy; NSW SES operator survey 2025; AIDR mobile-accessibility guidance. | End-to-end scenario rehearsal passes on each named profile. | UX Lead (AMA) | `product-owner-ba` | `ux-designer` | Proposed | 2026-04-24 | A-GAP-001 |

### Out of Scope (summary — detailed list under § Scope)

- Replacement of statutory command authority, emergency legislation, or formal incident governance.
- Direct control of field hardware, emergency vehicles, or physical infrastructure.
- Detailed payroll, rostering, or enterprise human resources processes for participating organisations.
- Public-facing self-service citizen reporting workflows beyond the ingestion and use of externally supplied reports.
- v1 deferrals (Asia jurisdictions, earthquake / tsunami / extreme heat / pandemic / CBRN / space-weather / cyber-physical hazards, recovery phase, some citizen surfaces) are enumerated in § Scope subsections below and in the Deferred-Scope Register.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an operational exercise scoped to the **v1 Australian evaluation cohort** (participants drawn from ≥ 3 tier-1 Australian emergency-management agencies), authorised users identify the relevant organisations, personas, and governing frameworks for an affected jurisdiction in under 5 minutes.
- **SC-002**: In a multi-agency disaster simulation against the **v1 Australian** jurisdiction set, incident leaders establish a shared operating picture and issue the first coordinated action plan in under 10 minutes from incident activation.
- **SC-003**: At least 90 % of tested **v1 Australian** personas — the validated operational set enumerated in § Personas below (Incident Controller, Operations Officer, Logistics Officer, Public Information Officer, Field Coordinator, Resilience Planner, Observer / Auditor) — complete their highest-priority incident tasks on the first attempt without facilitator assistance.
- **SC-004**: Coordinated response time in scenario-based exercises run against the **v1 Australian evaluation cohort** improves by at least 50 % compared with the current documented baseline process, where the baseline is the pre-hub tabletop or exercise workflow recorded in the project evaluation pack for the same scenario and jurisdiction. *(Revisit if HYP-001 is invalidated.)*
- **SC-005**: Scenario-based risk assessment enables at-risk population evacuation decisions at least 24 hours earlier than the current documented baseline in applicable **v1 Australian** events, using the same scenario definition, authority threshold, and documented baseline exercise pack. *(Revisit if HYP-002 is invalidated.)*
- **SC-006**: Resource deployment efficiency improves by at least 30 % in rehearsal or pilot measurements within the **v1 Australian evaluation cohort** against the current documented baseline, with efficiency measured using time-to-assignment, resource-utilization ratio, and unfilled-priority-request count captured in the evaluation pack. *(Revisit if HYP-003 is invalidated.)*
- **SC-007**: At least 85 % of evaluated users in the **v1 Australian evaluation cohort** rate the dashboard and key pages as clear, distinctive, and appropriate for high-pressure decision-making, using a structured post-exercise survey with a 5-point rubric across clarity, scanability, visual distinctiveness, and decision confidence, with participants representing at least 3 Australian organisation types and 5 validated v1 personas.

### Evaluation Baseline

- The baseline for SC-004 through SC-006 is the documented pre-hub exercise or tabletop workflow captured per scenario, jurisdiction, and participating organisations.
- Baseline and hub-enabled runs must use the same scenario inputs, participating roles, and exercise controller rules.

### UX Evaluation Method

- UX evaluation will be run after scenario exercises using a standard rubric and post-task survey.
- The evaluation cohort must include incident leadership, operational users, and planning users from multiple organisations.

---

## Non-Functional Requirements

> Normative table per FR-004..FR-013 of `specs/027-spec-hardening/spec.md`. Every NFR carries a measurable target, a verifiable measurement method, a cited external standard, and a three-way signature (drafter / SME-countersigner / privacy-reviewer) per FR-034. Privacy-category rows **require** a privacy-reviewer cell populated; non-privacy rows may use `N/A`.

| nfr_id | category | statement | target | basis | drafter | sme_countersigner | privacy_reviewer | standard_reference | measurement_method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFR-001 | Accessibility | All operator and public surfaces MUST conform to WCAG 2.2 Level AA; screen-reader, keyboard-only, and high-contrast paths MUST complete every P1 user journey. | 0 Level-A or Level-AA violations on automated + manual audit of every P1 flow; keyboard-only task completion ≥ 95 %. | WCAG 2.2 AA; EN 301 549 v3.2.1; Disability Discrimination Act 1992 (Cth). | `product-owner-ba` | `ux-designer` | N/A | WCAG 2.2 AA / EN 301 549 v3.2.1 | axe-core + Accessibility Insights + manual screen-reader walkthrough per release; pass/fail tracked per flow. |
| NFR-002 | Privacy | Personal or community-reported information MUST be classified, retention-bounded, erasure-enabled, held in Australian regions, and never transferred cross-border without an APP-8 disclosure register entry. | 100 % of PII-carrying entities classified; retention ≤ {operational: 30 d, incident evidence: 7 y, system audit: 7 y}; erasure SLA ≤ 30 d from verified request. | *Privacy Act 1988* (Cth); Australian Privacy Principles (APP 1, 3, 5, 6, 8, 11, 12, 13); OAIC Guide to Data Analytics. | `product-owner-ba` | `compliance-auditor` | OAIC-certified Privacy Officer (AMA) | Privacy Act 1988 (Cth) + APPs | Quarterly privacy impact review; Microsoft Purview classification report; erasure-request SLA dashboard. |
| NFR-003 | Security | Authentication MUST be phishing-resistant MFA; sessions MUST be short-lived and bound; secrets MUST live in a managed HSM-backed store; the system MUST have an accepted threat-model. | MFA 100 % on admin + coordination roles; access-token ≤ 1 h, refresh ≤ 24 h; 0 secrets in code/config; STRIDE threat-model signed per quarter. | ACSC *Essential Eight* maturity level 2; Australian Government ISM (latest); NIST SP 800-63-3; OWASP ASVS 4.0 L2. | `product-owner-ba` | `security-architect` | OAIC-certified Privacy Officer (AMA) | Essential Eight ML2 + ACSC ISM | Essential Eight assessment; Defender for Cloud Secure Score; pen-test per major release. |
| NFR-004 | Reliability | Core coordination surfaces (dashboard, alert ingress, agent orchestration) MUST provide regional HA with an automated rollback trigger tied to the AI quality floor in ASM-004. | Monthly availability ≥ 99.9 %; RTO ≤ 1 h; RPO ≤ 15 min; AI quality-breach rollback ≤ 10 min. | Microsoft Azure Well-Architected Framework (Reliability pillar); AS/NZS 5050 business continuity. | `product-owner-ba` | `sre-site-reliability` | N/A | Azure WAF Reliability pillar | Azure Monitor SLO dashboards; monthly DR game-day; rollback-drill report. |
| NFR-005 | Performance | Situation-picture refresh, authoritative-alert retrieval, and operator action round-trip MUST meet operator-usable latencies including at the ASM-003 connectivity floor. | p95 situation refresh ≤ 3 s online / ≤ 10 s at 64 kbps; alert ingest → operator visibility p95 ≤ 60 s; action round-trip p95 ≤ 2 s. | Nielsen response-time heuristic; AIDR connectivity guidance; BoM CAP freshness SLA. | `product-owner-ba` | `performance-engineer` | N/A | Nielsen / ISO 9241-11 | Application Insights percentile reports per cohort and per network profile. |
| NFR-006 | Interoperability | External alert, resource, and situation-sharing payloads MUST conform to recognised emergency-management standards. | 100 % of outbound alerts validate against CAP 1.2 schema; 100 % of resource exchanges validate against EDXL-DE 2.0; Sendai-Framework indicator mapping present. | OASIS CAP 1.2; OASIS EDXL-DE 2.0; UNDRR *Sendai Framework for Disaster Risk Reduction 2015-2030*. | `product-owner-ba` | `integration-engineer` | N/A | OASIS CAP 1.2 / EDXL-DE 2.0 | CI schema-validation gate; sample-pack conformance report per release. |
| NFR-007 | Privacy | Community-reported data MUST distinguish provenance tiers and MUST NOT be surfaced as authoritative guidance. | 100 % of ingested community items carry provenance ∈ {authoritative, verified-community, unverified}; UI distinguishes tiers on every surface. | OAIC APP-10 (Quality of Personal Information); AIIMS-5 §8 Information Management. | `product-owner-ba` | `ai-ml-engineer` | OAIC-certified Privacy Officer (AMA) | OAIC APP-10 | Rehearsal verification: provenance-mismatch count = 0; quarterly UX-conformance audit. |
| NFR-008 | Observability | Every operator decision, AI-generated recommendation, and escalation MUST leave an immutable, time-boxed audit record. | 100 % of decisions logged within 1 s of event; audit store append-only; sampled replay within 5 min per request. | AGRKMS (Australian Government Recordkeeping Metadata Standard); VERS v3 retention; NIST SP 800-92. | `product-owner-ba` | `sre-site-reliability` | N/A | AGRKMS / VERS v3 | Daily audit-integrity hash check; monthly sampled replay drill. |
| NFR-009 | Data-Residency | All primary, replica, and backup copies of operational and audit data MUST reside in Australian Azure regions unless approved APP-8 disclosure applies. | 100 % Azure Policy `allowed-locations` compliance; 0 out-of-region backup copies. | Australian Government Hosting Certification Framework; *Privacy Act 1988* (Cth) APP-8. | `product-owner-ba` | `cloud-architect` | OAIC-certified Privacy Officer (AMA) | Hosting Certification Framework | Azure Policy compliance report; monthly residency attestation. |
| NFR-010 | Cost | Unit cost per rehearsal-scenario-run and per monitored 24 h MUST remain within approved capstone budget envelopes. | Unit cost variance ≤ 20 % of approved envelope month-on-month. | Microsoft Azure Well-Architected Framework (Cost Optimisation pillar). | `product-owner-ba` | `finops-engineer` | N/A | Azure WAF Cost pillar | Azure Cost Management workbook + unit-cost telemetry on every rehearsal run. |
| NFR-011 | Reliability | Training and operational change-management artefacts MUST be refreshed with every release that alters a P1 flow (dependency of SC-003). | 100 % of P1-flow-altering releases accompanied by updated training pack and operator release note ≤ 5 business days post-release. | ITIL 4 Change Enablement; AIIMS-5 Training & Competency guidance. | `product-owner-ba` | `training-lead` | N/A | ITIL 4 Change Enablement | Release checklist gate: updated training-pack artefact attached to release evidence. |
| NFR-012 | Security | The system MUST retain an immutable tamper-evident audit trail of safety-critical events for at least 7 years and MUST prove recoverability annually. | Audit retention ≥ 7 y; recoverability drill successful within RTO ≤ 1 h annually. | VERS v3 retention; AGRKMS; *Archives Act 1983* (Cth) where applicable. | `product-owner-ba` | `compliance-auditor` | OAIC-certified Privacy Officer (AMA) | VERS v3 / AGRKMS | Annual restore drill + audit-hash continuity report. |
| NFR-013 | Accessibility | All operator surfaces MUST support Australian English + ≥ 1 CALD language (Simplified Chinese at v1), with locale-correct formats and right-to-left readiness documented. | v1 surfaces localised in 2 languages at release; locale conformance audit passes 100 %. | AIDR CALD Communication Guidance; W3C Internationalisation BCP-47. | `product-owner-ba` | `ux-designer` | N/A | W3C BCP-47 / AIDR CALD | Release localisation checklist + native-speaker review per release. |

---

## Personas

> Normative persona set per FR-014..FR-016 of `specs/027-spec-hardening/spec.md`. Each persona carries the YAML front-matter specified in `specs/027-spec-hardening/contracts/persona-profile.md`. `validated_by` records the SME role that signs the persona; concrete SME identities are recorded during review. Top-3 tasks are the persona's highest-priority P1-flow tasks. Personas are grouped by cohort.

### Operational cohort (AIIMS-5)

```yaml
persona_id: P-OPS-IC
display_name: Australian Incident Controller
aiims_function: Control
role_basis: AIIMS-5 §2 Command; AFAC Doctrine
jurisdiction_scope: Australian state or territory
authority_scope: Statutory incident control under the relevant state EM Act
validated_by: Former AIIMS-5 Incident Controller (AMA SME panel)
representative_scenarios: [bushfire-level3, flood-escalation, cyclone-landfall]
accessibility_needs: [high-contrast mode, large-text, noisy-environment audio]
```

**Goals**: Issue timely coordinated action plans; maintain shared operating picture; uphold statutory command. **Pains**: Information overload; conflicting feeds; ambiguous authority. **Top-3 tasks**: (1) Establish IAP within 10 min of activation (SC-002). (2) Approve public-alert dispatch. (3) Trigger escalation to state controller.

```yaml
persona_id: P-OPS-OPS
display_name: Operations Officer
aiims_function: Operations
role_basis: AIIMS-5 §4 Operations
jurisdiction_scope: Incident area of operations
authority_scope: Tactical direction of assigned resources
validated_by: Former Operations Officer (AMA SME panel)
representative_scenarios: [multi-sector-bushfire, urban-flood]
accessibility_needs: [one-hand mobile operation]
```

**Goals**: Assign and track tactical resources; brief sector commanders. **Pains**: Stale position data; missing ETAs. **Top-3 tasks**: (1) Create / split sectors. (2) Assign crews to tasks. (3) Confirm tactical ETA with logistics.

```yaml
persona_id: P-OPS-LOG
display_name: Logistics Officer
aiims_function: Logistics
role_basis: AIIMS-5 §5 Logistics
jurisdiction_scope: Incident area + supply chain reach-back
authority_scope: Resource requisition and tracking
validated_by: Former Logistics Officer (AMA SME panel)
representative_scenarios: [multi-day-deployment, resource-shortfall]
accessibility_needs: []
```

**Goals**: Match requests to supply; prevent shortfall cascades. **Pains**: Duplicate requests; opaque ETAs. **Top-3 tasks**: (1) Fulfil priority requisition. (2) Reconcile stock. (3) Coordinate reach-back with state ops centre.

```yaml
persona_id: P-OPS-PIO
display_name: Public Information Officer
aiims_function: Public Information
role_basis: AIIMS-5 §3 Planning/Information; AIDR Public Information Handbook
jurisdiction_scope: Affected community and media
authority_scope: Release of public information on delegated authority
validated_by: Former PIO (AMA SME panel)
representative_scenarios: [multilingual-alerting, misinformation-spike]
accessibility_needs: [CALD-language tooling]
```

**Goals**: Timely, accurate, accessible public messaging. **Pains**: Misinformation drift; language/access gaps. **Top-3 tasks**: (1) Draft and dispatch CAP-compliant alert. (2) Counter misinformation. (3) Coordinate translations.

```yaml
persona_id: P-OPS-FIELD
display_name: Field Coordinator
aiims_function: Operations (field)
role_basis: AIIMS-5 §4; AIDR Field Operations Handbook
jurisdiction_scope: Incident sector
authority_scope: On-ground tactical coordination
validated_by: Former sector commander (AMA SME panel)
representative_scenarios: [degraded-connectivity-field, remote-community-evac]
accessibility_needs: [glare readability, voice-dictation entry]
```

**Goals**: Shared picture under degraded connectivity. **Pains**: Intermittent network; bulky UI. **Top-3 tasks**: (1) Submit sitrep under ASM-003 connectivity floor. (2) Receive tasking. (3) Call for reinforcement.

```yaml
persona_id: P-OPS-PLAN
display_name: Resilience Planner
aiims_function: Planning
role_basis: AIIMS-5 §3 Planning; AIDR Resilience Handbooks
jurisdiction_scope: Pre-event & inter-event (PPRR: Prevention + Preparedness)
authority_scope: Scenario design, rehearsal programme
validated_by: Former state-level planner (AMA SME panel)
representative_scenarios: [annual-exercise, community-profile-review]
accessibility_needs: []
```

**Goals**: Run rehearsals that improve readiness measurably. **Pains**: Baseline data missing; feedback loop slow. **Top-3 tasks**: (1) Compose rehearsal scenario. (2) Inject exercise events. (3) Capture after-action outcomes.

```yaml
persona_id: P-OPS-AUDIT
display_name: Observer / Auditor
aiims_function: Governance (cross-cut)
role_basis: AIIMS-5 §8 Information Management; AGRKMS
jurisdiction_scope: Cross-jurisdictional
authority_scope: Read-only / audit
validated_by: Internal audit (AMA SME panel)
representative_scenarios: [audit-replay, compliance-review]
accessibility_needs: [assistive-tech support per NFR-001]
```

**Goals**: Reconstruct decisions faithfully. **Pains**: Silent mutations; missing provenance. **Top-3 tasks**: (1) Replay decision trail (NFR-008). (2) Export audit pack. (3) File compliance finding.

### Executive cohort

```yaml
persona_id: P-EXEC-MIN
display_name: Minister / Premier delegate
aiims_function: Strategic oversight
role_basis: State EM Acts; Ministerial delegations
jurisdiction_scope: State / territory
authority_scope: Statutory emergency declaration and resource direction
validated_by: Former ministerial-office EM advisor (AMA SME panel)
representative_scenarios: [state-of-emergency-declaration, cabinet-brief]
accessibility_needs: []
```

**Goals**: Single trusted brief; defensible authority. **Pains**: Conflicting briefings; political exposure. **Top-3 tasks**: (1) Consume executive-brief surface. (2) Approve declaration. (3) Authorise cross-border request.

```yaml
persona_id: P-EXEC-MAYOR
display_name: Mayor / Local Government Lead
aiims_function: Local strategic liaison
role_basis: Local Government Acts; LEMC arrangements
jurisdiction_scope: Local Government Area
authority_scope: Community liaison and local resource coordination
validated_by: Former LGA recovery lead (AMA SME panel)
representative_scenarios: [community-impact-brief, recovery-handover]
accessibility_needs: []
```

**Goals**: Protect community; coordinate locally. **Pains**: Slow state-to-local information flow. **Top-3 tasks**: (1) Request local resource. (2) Coordinate community liaison. (3) Trigger recovery handover referral.

### Community / affected cohort (CALD-inclusive)

```yaml
persona_id: P-COM-CALD-HH
display_name: CALD Household Member
aiims_function: Recipient of public information
role_basis: AIDR CALD Communication Guidance
jurisdiction_scope: Affected LGA
authority_scope: None (public)
validated_by: Settlement Services International SME (AMA panel)
representative_scenarios: [multilingual-evac-alert, recovery-assistance]
accessibility_needs: [CALD language, low-literacy copy]
```

**Goals**: Understand action to take. **Pains**: Language barrier; jargon. **Top-3 tasks**: (1) Read CALD alert. (2) Follow evac instruction. (3) Locate assistance centre.

```yaml
persona_id: P-COM-REMOTE
display_name: Remote / Regional Resident
aiims_function: Recipient of public information
role_basis: AIDR Remote-Community Guidance
jurisdiction_scope: Remote LGA
authority_scope: None (public)
validated_by: Regional EM advisor (AMA panel)
representative_scenarios: [cyclone-isolation, degraded-connectivity]
accessibility_needs: [SMS fallback, radio fallback]
```

**Goals**: Receive alerts under poor connectivity. **Pains**: Patchy coverage. **Top-3 tasks**: (1) Receive SMS/CAP alert. (2) Confirm evac route. (3) Request welfare check.

```yaml
persona_id: P-COM-FIRSTNATIONS
display_name: First Nations Community Liaison
aiims_function: Cultural liaison
role_basis: AIDR First Nations Guidance; relevant Land Council protocols
jurisdiction_scope: First Nations community
authority_scope: Cultural advisory
validated_by: First Nations EM advisor (AMA panel)
representative_scenarios: [cultural-sensitive-evac, land-access-brief]
accessibility_needs: [plain-language English + local language]
```

**Goals**: Culturally safe protection of community. **Pains**: Lack of cultural awareness in defaults. **Top-3 tasks**: (1) Review culturally sensitive brief. (2) Advise on land access. (3) Coordinate with elders.

```yaml
persona_id: P-COM-DISAB
display_name: Person with Disability / Carer
aiims_function: Recipient of public information
role_basis: Disability Discrimination Act 1992 (Cth); AIDR Inclusive EM Guidance
jurisdiction_scope: Affected LGA
authority_scope: None (public)
validated_by: Accessibility advocacy SME (AMA panel)
representative_scenarios: [accessible-evac, assistance-animal]
accessibility_needs: [screen-reader, captions, plain-language]
```

**Goals**: Equivalent-quality access to safety information. **Pains**: Inaccessible alerts. **Top-3 tasks**: (1) Receive accessible alert. (2) Request assistance. (3) Evacuate with support.

```yaml
persona_id: P-COM-TOURIST
display_name: Visitor / Tourist
aiims_function: Recipient of public information
role_basis: Tourism-Research-Australia visitor profile; AIDR Visitor Guidance
jurisdiction_scope: Affected LGA (transient)
authority_scope: None (public)
validated_by: Visitor-services EM advisor (AMA panel)
representative_scenarios: [no-local-knowledge-evac]
accessibility_needs: [multilingual, map-centric UI]
```

**Goals**: Act on alerts despite no local knowledge. **Pains**: Place-name unfamiliarity. **Top-3 tasks**: (1) Understand alert. (2) Follow map-based route. (3) Locate accommodation alternative.

### Adversarial cohort

```yaml
persona_id: P-ADV-MISINFO
display_name: Misinformation Actor (Archetype)
aiims_function: Threat model
role_basis: ACSC Threat Actor Typology; AIDR Misinformation Guidance
jurisdiction_scope: Cross-jurisdictional / online
authority_scope: None
validated_by: Security-architect review (AMA)
representative_scenarios: [viral-false-alert, spoofed-authority]
accessibility_needs: N/A
```

**Goals (adversary's goals)**: Degrade public trust; amplify false alerts. **Pains (for us)**: Speed of rebuttal. **Top-3 tasks (system must defeat)**: (1) Detect false-amplification clusters. (2) Block spoofed-authority content. (3) Surface counter-message path.

```yaml
persona_id: P-ADV-INSIDER
display_name: Insider Threat (Archetype)
aiims_function: Threat model
role_basis: ACSC Insider Threat Guidance
jurisdiction_scope: Internal
authority_scope: Legitimate operator access with elevated risk
validated_by: Security-architect review (AMA)
representative_scenarios: [unauthorised-export, scope-creep-query]
accessibility_needs: N/A
```

**Goals (adversary's goals)**: Exfiltration; unauthorised action. **Pains (for us)**: Blast-radius containment. **Top-3 tasks (system must defeat)**: (1) Detect anomalous access pattern. (2) Enforce least-privilege. (3) Preserve immutable audit.

### Accessibility-operator cohort

```yaml
persona_id: P-ACC-SCREEN
display_name: Screen-Reader Operator
aiims_function: Operational (any function)
role_basis: WCAG 2.2 AA; AIDR Inclusive EM
jurisdiction_scope: Any
authority_scope: Any operational role
validated_by: Assistive-technology SME (AMA panel)
representative_scenarios: [dashboard-navigation, alert-draft]
accessibility_needs: [NVDA/JAWS screen-reader, keyboard only]
```

**Goals**: Complete every P1 task non-visually. **Pains**: Missing labels; focus traps. **Top-3 tasks**: (1) Navigate dashboard via landmarks. (2) Compose alert via keyboard. (3) Acknowledge critical notification.

```yaml
persona_id: P-ACC-VOICE
display_name: Voice-Control / Switch-Device Operator
aiims_function: Operational (any function)
role_basis: WCAG 2.2 AA; EN 301 549 v3.2.1
jurisdiction_scope: Any
authority_scope: Any operational role
validated_by: Assistive-technology SME (AMA panel)
representative_scenarios: [voice-task-assignment]
accessibility_needs: [voice control, switch-access compatibility]
```

**Goals**: Perform operational tasks via voice / switch-access. **Pains**: Unpredictable hit-targets. **Top-3 tasks**: (1) Dictate sitrep. (2) Activate action via voice command. (3) Confirm acknowledgement.

---

## Hypotheses

> Normative hypotheses table per FR-017..FR-021 of `specs/027-spec-hardening/spec.md`. Every hypothesis has a falsification criterion, a bounded method, a linked architectural or product decision, and an `evidence_pack` pointer. Invalidation forces the linked decision to be re-opened.

| hypothesis_id | statement | falsification_criterion | method | linked_decision | owner | status | evidence_pack |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HYP-001 | Introducing autonomous agents for signal triage, resource matching, and public-information drafting will reduce coordinated response time ≥ 50 % (SC-004) without breaching the Constitution §Non-Negotiable-1 human-authority boundary. | Two consecutive rehearsal cycles show < 25 % response-time improvement OR any safety-critical decision taken without documented human approval. | rehearsal | Architectural decision: "Adopt autonomous-agent pattern in coordination surface". | AI Platform Lead (AMA) | Proposed | evidence/HYP-001.md |
| HYP-002 | A mixed authoritative + provenance-tiered community signal model lets incident leaders trigger at-risk evacuation decisions ≥ 24 h earlier (SC-005) without increasing false-positive evacuation rate. | Two consecutive rehearsal cycles show < 8 h earlier decisions OR false-positive evacuation rate rises above the accepted baseline. | rehearsal | Architectural decision: "Signal trust model = tiered provenance with human-in-the-loop gating". | Resilience Planner (AMA) | Proposed | evidence/HYP-002.md |
| HYP-003 | Deterministic orchestration of agents (typed contracts, human-approval gates) outperforms LLM-routed orchestration for P1 coordination flows on reliability and auditability, and meets SC-006 resource-deployment efficiency. | A comparative telemetry study shows LLM-routed orchestration yields ≥ 10 % better resource-deployment efficiency *and* matches the auditability bar (NFR-008) over two rehearsal cycles. | telemetry | Architectural decision: "Orchestration fabric = deterministic / typed". | Platform Architect (AMA) | Proposed | evidence/HYP-003.md |
| HYP-004 | Mobile-first surfaces can deliver P1 coordination tasks within operator-usable latencies at the ASM-003 connectivity floor (≥ 64 kbps). | A degraded-connectivity rehearsal shows P1 task completion rate < 90 % or p95 situation-refresh latency > 10 s at the floor. | rehearsal | Product decision: "v1 field delivery surface = responsive web + PWA". | UX Lead (AMA) | Proposed | evidence/HYP-004.md |
| HYP-005 | The tiered provenance model + misinformation countermeasures reduce misinformation-driven operator or citizen actions to below an agreed tolerance during rehearsal. | A simulated misinformation-injection rehearsal shows operator or citizen action on false-alert content above the agreed tolerance. | A/B | Product decision: "Ship misinformation-resilience v1 bundle". | Security Architect (AMA) | Proposed | evidence/HYP-005.md |
| HYP-006 | The AMA coordination framework is structurally portable to non-Australian jurisdictions (Asia-Pacific in capstone) *with* jurisdictional adaptation work that is bounded and discoverable, and MUST NOT be assumed to require "no code changes". | Any attempt to extend the hub to a non-Australian jurisdiction where required changes exceed the documented adaptation envelope (data integration, taxonomy binding, legal alignment) without a spec-amendment path. | expert-review | Product decision: "Defer Asia-region claims to a post-v1 spec-amendment lane; treat capstone Asia content as aspirational". | Product Owner (AMA) | Proposed | evidence/HYP-006.md |

---

## Scope

> Normative scope subsections per FR-022..FR-030 of `specs/027-spec-hardening/spec.md`. Deferred items are enumerated in `### Deferred-Scope Register` with a `kind` classifier per FR-023.

### v1 Primary Jurisdiction

- **Primary jurisdiction (v1)**: Commonwealth of Australia.
- **In-scope Australian tiers**: Commonwealth (NEMA), state / territory EM bodies (NSW SES, NSW RFS, VIC SES, VIC CFA, QLD QFES, QLD SES, WA DFES, SA SES, SA CFS, TAS SES, TAS FS, ACT ESA, NT PFES), and Local Government (LGA Local Emergency Management Committees).
- **Preconditions**: ASM-001 (jurisdiction chosen + justified), ASM-005 (Australian-region data residency), ASM-006 (baseline exercise availability), ASM-007 (advisory-only AI standing), NFR-009 (data residency).
- **Portability**: Framework portability to non-Australian jurisdictions is *hypothesis HYP-006*. It is **NOT** a v1 architectural guarantee. Any extension to Asia or other jurisdictions requires a new spec-amendment lane and a bounded adaptation envelope; the capstone's "no code changes" framing for Asia is **aspirational** and is treated as an open delta on HYP-006.

### Deferred-Scope Register

| defer_id | kind | item | reason | re-visit trigger | owner |
| --- | --- | --- | --- | --- | --- |
| DEF-001 | jurisdiction | Philippines (NDRRMC ecosystem) | ASM-002 data-quality unknowns; Asia-region deferred to post-v1 amendment lane; HYP-006 open. | Baseline exercise + data-sharing MoU + PIA (APP-8) completed. | Product Owner |
| DEF-002 | jurisdiction | Japan (JMA + national alert ecosystem) | ASM-002 data-quality unknowns; Japanese standards binding (J-Alert / ETWS) not yet mapped to CAP baseline. | Japanese standards mapping completed and baseline exercise pack secured. | Product Owner |
| DEF-003 | jurisdiction | Bangladesh (MoDMR / CPP ecosystem) | ASM-002; extreme capacity / connectivity constraints; limited English-primary artefacts. | Operating-model and accessibility envelope assessed. | Product Owner |
| DEF-004 | hazard | Earthquake | v1 Principle-III hazard allocation (see Constitution); Geoscience-Australia feed integration not in v1 scope. | GA integration + rehearsal pack available. | Resilience Planner |
| DEF-005 | hazard | Tsunami | v1 Principle-III hazard allocation; JATWC integration deferred. | JATWC integration + coastal LGA rehearsal. | Resilience Planner |
| DEF-006 | hazard | Extreme heat | v1 Principle-III hazard allocation; vulnerable-population overlay not in v1. | BoM heat-index overlay + vulnerable-population data access. | Resilience Planner |
| DEF-007 | hazard | Pandemic / biosecurity | v1 Principle-III hazard allocation; human-biosecurity command model differs. | Human-biosecurity cross-command model drafted. | Resilience Planner |
| DEF-008 | hazard | CBRN (chemical / biological / radiological / nuclear) | Specialist command and data feeds; outside v1. | CBRN advisory + NEMA coordination model drafted. | Resilience Planner |
| DEF-009 | hazard | Space weather | Specialist (Bureau of Meteorology Space-Weather Services); outside v1. | Space-weather data-feed integration. | Resilience Planner |
| DEF-010 | hazard | Cyber-physical | ACSC lead; cross-jurisdictional command outside v1. | Cyber-physical coordination model drafted. | Resilience Planner |
| DEF-011 | capability | Medical triage decision-support | Not in v1 — clinical decision-support requires TGA / ADHA pathway (REQ-GAP-008). | Clinical-safety evidence pack + regulatory pathway. | Clinical Advisor |
| DEF-012 | capability | Shelter / evacuation-centre allocation | Not in v1 — couples to LGA shelter databases not yet integrated. | LGA shelter data integration. | Resilience Planner |
| DEF-013 | capability | Utility-network isolation coordination | Not in v1 — safety-critical; requires utility-specific agreements. | Utility SCADA / advisory coupling design. | Platform Architect |
| DEF-014 | capability | Search-and-Rescue tasking | Not in v1 — AMSA / state-police operational scope. | AMSA / police SAR integration design. | Resilience Planner |
| DEF-015 | capability | Recovery (PPRR) phase surfaces | v1 scope is Response + rehearsal (Preparedness); Recovery deferred. | Recovery surface scoping + LGA handover model. | Resilience Planner |
| DEF-016 | capability | Public self-service citizen reporting | v1 scope is ingest only; two-way citizen surface deferred. | Two-way citizen surface design + misinformation-resilience pack v2. | Product Owner |

### Hazard List

> v1 primary set derived from Constitution Principle III; deferred items cross-linked to the Deferred-Scope Register above.

| hazard_id | name | v1 status | primary authoritative feed | notes |
| --- | --- | --- | --- | --- |
| H-001 | Bushfire | In scope (v1) | State RFS / CFA + BoM Fire-Weather | AFAC fire-behaviour doctrine. |
| H-002 | Flood | In scope (v1) | BoM Flood Warning + state SES | AIDR Flood Handbook. |
| H-003 | Tropical cyclone | In scope (v1) | BoM Tropical-Cyclone Advisory | AIDR Cyclone Handbook. |
| H-004 | Severe storm (incl. hail / wind) | In scope (v1) | BoM Severe-Weather Warnings | AIDR Severe-Weather Handbook. |
| H-005 | Earthquake | Deferred (see DEF-004) | Geoscience Australia | Rapid-impact assessment pathway out of v1. |
| H-006 | Tsunami | Deferred (see DEF-005) | JATWC (BoM + GA) | Coastal LGA coupling out of v1. |
| H-007 | Extreme heat | Deferred (see DEF-006) | BoM Heatwave Service | Vulnerable-population overlay out of v1. |
| H-008 | Pandemic / biosecurity | Deferred (see DEF-007) | Commonwealth Health + AHPPC | Human-biosecurity command differs. |
| H-009 | CBRN | Deferred (see DEF-008) | Specialist | Out of v1. |
| H-010 | Space weather | Deferred (see DEF-009) | BoM Space-Weather Services | Out of v1. |
| H-011 | Cyber-physical | Deferred (see DEF-010) | ACSC | Out of v1. |

### Autonomy Boundary Table

> Derived from Constitution §Non-Negotiable-1 and AIIMS-5 §2 Command. "Decide" = system may execute without human approval. "Recommend + human-approve" = system drafts, human controls. "Human only" = system MUST NOT act.

| decision_class | autonomy mode | who approves | audit requirement |
| --- | --- | --- | --- |
| Public evacuation order | Human only | Statutory incident controller | NFR-008 + NFR-012 retention ≥ 7 y |
| Public alert dispatch (CAP) | Recommend + human-approve | PIO under delegated authority | NFR-008 full decision trail |
| Cross-border resource request | Recommend + human-approve | Incident controller / state ops | NFR-008 |
| Internal resource assignment (non-safety-critical) | Decide (with human over-ride) | System (automated) with operator veto | NFR-008 |
| Misinformation rebuttal drafting | Recommend + human-approve | PIO | NFR-008 |
| Recommendation ranking & surfacing | Decide | N/A (advisory) | NFR-008 |
| Agent self-modification / code-execution | Human only | Platform owner + change board | NFR-003 + NFR-008 |

### Community Signal Sources

| source_tier | examples | provenance label | v1 status |
| --- | --- | --- | --- |
| Authoritative | BoM, GA, state RFS / SES / fire, NEMA, Police, AFP | authoritative | In scope |
| Verified community | Registered VRA, AIDR-trained volunteer networks, ARC shelter partners | verified-community | In scope (ingest only) |
| Unverified community | Open social-media streams (X / Facebook / Reddit / TikTok) via read-only APIs, SMS tip lines | unverified | In scope (ingest only, provenance-flagged per NFR-007) |
| Third-party risk / analytics | Commercial geospatial, satellite, insurance-sector feeds | authoritative (contract-bound) | In scope where licensing permits |

### Recovery (PPRR) Stance

- **In scope (v1)**: Preparedness (rehearsal, scenario-design) and Response (coordination, alerting, resource flow, audit).
- **Out of scope (v1)**: Recovery phase surfaces (impact assessment, grants, reconstruction) — deferred via DEF-015. Limited Recovery *handover referral* is supported (Mayor persona Top-3 task 3) as a one-way pointer to LGA recovery processes; no recovery workflow lives in the hub at v1.
- **Prevention**: Constitution & strategic planning artefacts sit upstream of the hub; no hub workflow at v1.

### Citizen-Surface List

| surface | direction | v1 status | notes |
| --- | --- | --- | --- |
| Public authoritative alert broadcast (outbound CAP) | Outbound | In scope | NFR-006 conformance. |
| Accessible alert (screen-reader + CALD + plain-language) | Outbound | In scope | NFR-001 + NFR-013. |
| Ingest of community-reported incidents | Inbound (one-way) | In scope (ingest only) | NFR-007 provenance-tiered. |
| Public self-service reporting portal (two-way dialog) | Bi-directional | Out of scope (DEF-016) | Deferred to post-v1. |
| Public dashboard / sitrep for citizens | Outbound | Out of scope (v1) | Deferred to Recovery surfaces pack. |

### Upstream / Downstream Integrations

| role | system / party | direction | integration contract | v1 status |
| --- | --- | --- | --- | --- |
| Upstream authoritative | BoM alert feeds | Inbound | CAP 1.2 | In scope |
| Upstream authoritative | Geoscience Australia | Inbound | Web-feature / CAP | In scope (read-only) |
| Upstream authoritative | State EM agencies (RFS / SES / CFA etc.) | Inbound | CAP / per-agency | In scope |
| Upstream authoritative | NEMA | Bi-directional | EDXL-DE 2.0 / CAP | In scope |
| Upstream authoritative | Australian Red Cross (shelter / welfare) | Bi-directional | Per-MoU | In scope |
| Upstream community | Social-media platforms (read-only) | Inbound | Platform APIs | In scope (unverified tier) |
| Downstream citizen | Public CAP distribution | Outbound | CAP 1.2 | In scope |
| Downstream inter-jurisdictional | NEMA national coordination | Bi-directional | EDXL-DE 2.0 | In scope |
| Downstream audit / records | VERS / agency archives | Outbound | AGRKMS | In scope |
| Downstream deferred | Asia-region systems (NDRRMC / JMA / MoDMR) | N/A | TBD | Deferred (DEF-001..DEF-003) |

### Rehearsal Content Boundary

- Rehearsal scenarios MUST be clearly labelled and visually differentiated from live operations.
- Rehearsal data MUST NOT dispatch to public alert channels; CAP dispatch paths MUST be stub-routed during rehearsal.
- Rehearsal artefacts share the NFR-008 / NFR-012 audit store but carry an immutable `mode=rehearsal` label.
- Bi-modal operation (concurrent live + rehearsal per user) is **out of scope (v1)**; operators switch mode explicitly.
- Rehearsal-only personas and content are authored under the Resilience Planner role and governed by the same SME-validation rule as live personas (FR-015).

---

## Status-transition authority

> Normative per FR-031..FR-033 of `specs/027-spec-hardening/spec.md`.

- **Drafting authority**: Any maintainer listed in `.github/CODEOWNERS` for the affected `specs/<feature>/` path may author `Proposed` rows for Assumptions, NFRs, Personas, and Hypotheses.
- **Countersignature rule**: No row may transition from `Proposed` to `Validated` (or equivalent) without a **dual-control** approval: the drafter plus an independent SME countersigner named in the row. Privacy-category NFRs additionally require a **privacy-reviewer** signature (an OAIC-certified Privacy Officer in the AMA panel or equivalent).
- **Invalidation / Withdrawn**: Transitioning any row to `Invalidated` or `Withdrawn` REQUIRES updating the linked decision, success criterion, or spec section that depended on it, and opening an Open Delta if the breach crosses a phase boundary.
- **Hypothesis invalidation**: If a Hypothesis is `Invalidated`, the linked decision and every Success Criterion cross-referenced (e.g., SC-004..SC-006) MUST be re-opened for review in the same PR.
- **Gap-register rule**: Every status change in a spec row MUST correspond to a status change in `specs/shared/gap-id-register.md` (per FR-036).
- **Dispute resolution**: Deadlock between drafter and countersigner escalates to the feature-owning maintainer group listed in `.github/CODEOWNERS`; a consensus decision is recorded in the Changelog and referenced from the row.

---

## Open Deltas

> Normative per FR-007 + FR-032 + FR-035. Deltas blocking the `plan` phase are enforced by `scripts/verify-spec-hardening.ps1` invariant (e).

| delta_id | description | source_section | target_feature | blocking_phase | status | resolution_link |
| --- | --- | --- | --- | --- | --- | --- |
| OD-001 | Capstone "no code changes" framing for Asia jurisdictions is aspirational; system portability to non-Australian jurisdictions is HYP-006, not an architectural guarantee. Any future Asia work needs a spec-amendment lane. | § Scope — v1 Primary Jurisdiction + § Hypotheses HYP-006 | unassigned | plan | Open | evidence/HYP-006.md |
| OD-002 | `.github/CODEOWNERS` references team `@johnbilliris/ama-spec-maintainers`. If the team does not yet exist in GitHub, individual interim maintainers apply until the team is provisioned, per CODEOWNERS comment. | governance / CODEOWNERS | 027-spec-hardening | none (governance) | Open | .github/CODEOWNERS |
| OD-003 | Drafter and countersigner cells currently name the accountable AMA role (e.g., `product-owner-ba`). Named individuals will be populated during PR review per the dual-control rule. | § Status-transition authority | 001-disaster-response-hub | none (authoring workflow) | Open | — |

---

## Changelog

| date | change summary | feature / PR |
| --- | --- | --- |
| 2026-04-24 | Initial hardened release: Assumptions promoted to table (ASM-001..008); added Non-Functional Requirements (NFR-001..013), Personas (18), Hypotheses (HYP-001..006), § Scope with 9 normative subsections, § Status-transition authority, § Open Deltas, § Changelog; Success Criteria scoped to v1 Australian evaluation cohort. | 027-spec-hardening (this PR) |

> **Traceability**: the canonical Traceability Table covering every Gap ID resolved by this hardening lives in `specs/027-spec-hardening/spec.md` § Traceability Table. See also the cross-spec monotonic register at `specs/shared/gap-id-register.md`.

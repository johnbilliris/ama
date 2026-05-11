# Feature Acceptance & Delivery Checklist: In-Product Help Documentation & Grounded Chat Assistant

**Purpose**: End-to-end build + sign-off checklist for spec-038. Used by the implementation team during build and the review team at release sign-off. Complements the spec-quality checklist (`requirements.md`); this one validates **delivered behaviour** against every FR, SC, persona, content domain, governance gate, and cross-spec dependency.
**Created**: 2026-05-11
**Feature**: [`specs/038-help-docs-chat/spec.md`](../spec.md)
**Companion checklist**: [`requirements.md`](./requirements.md) (spec-quality, kept separate)

> **How to use**: Each row is a discrete acceptance gate. Tick `[x]` only when evidence (test id, telemetry query, audit log sample, screenshot, attestation doc, or signed reviewer note) is linked. Items marked **[Gate]** are release blockers.

---

## 1. Persona Coverage — Operational Roles (10) × content surfaces

For each operational role, confirm: (a) persona landing page exists, (b) "first 15 minutes" tour, (c) screen-by-screen guides for the role's surfaces, (d) annotated screenshots present, (e) chat persona-context wiring (FR-015/FR-027) returns persona-tailored retrieval. **[Spec §Personas Operational, FR-002, FR-004, FR-027, FR-028]**

- [ ] CHK001 **[Gate]** Incident Commander — landing page, 15-min tour, AIIMS Controller workflow, public-alert-approval guide, cross-jurisdiction escalation guide, span-of-control warnings, audit traceability, screenshots, persona-context wiring verified
- [ ] CHK002 **[Gate]** Operations Officer — landing page, 15-min tour, tactical task assignment/reassignment, multi-sector coordination, staging strategy, agent-recommendations review, escalation-up guide, screenshots, persona-context wiring verified
- [ ] CHK003 **[Gate]** Planning Officer — landing page, 15-min tour, situation reporting, intelligence aggregation, resource forecasting, action-plan templates, map overlays, confidence/provenance reading, screenshots, persona-context wiring verified
- [ ] CHK004 **[Gate]** Logistics Officer — landing page, 15-min tour, supply-chain dashboards, transport coordination, forward-staging requests, consumption tracking, supplier directory, screenshots, persona-context wiring verified
- [ ] CHK005 **[Gate]** Public Information Officer — landing page, 15-min tour, multilingual alert composer, accessibility checker, channel selection, IC-approval submission, social monitoring, Principle V coverage, screenshots, persona-context wiring verified
- [ ] CHK006 **[Gate]** Field Coordinator — landing page, 15-min tour, mobile/field workflows, degraded-connectivity behaviour, local situation reporting, forward-staging accountability, life-safety defaults, screenshots, persona-context wiring verified
- [ ] CHK007 **[Gate]** Resilience Planner — landing page, 15-min tour, scenario design, simulation config & warp playback, gap-analysis exports, lessons-learned ingestion, screenshots, persona-context wiring verified
- [ ] CHK008 **[Gate]** Executive Leader — landing page, 15-min tour, strategic dashboards, cross-jurisdiction status, escalations, policy decision logs, briefing exports, screenshots, persona-context wiring verified
- [ ] CHK009 **[Gate]** Observer-Auditor — landing page, 15-min tour, read-only audit timeline navigation, framework-deviation review, append-only integrity verification, lessons-learned export, screenshots, **chat MUST NOT instruct state-changing actions** (FR-025) verified
- [ ] CHK010 **[Gate]** Risk Manager — landing page, 15-min tour, hazard assessment, risk levels, consequence analysis, decision support, Risk Assessment Agent integration, screenshots, persona-context wiring verified

## 2. Persona Coverage — Sector Clusters (6)

For each sector cluster, confirm: landing page, cluster-specific workflow guide, jurisdictional theming visible in screenshots, chat persona-context biases retrieval to cluster scope. **[Spec §Personas Sector clusters, FR-002]**

- [ ] CHK011 **[Gate]** `frontline-fire` (NSW RFS, FRNSW, CFA-VIC, FRV, SAMFS, SACFS, QFD, DFES-WA, TFS, NTFRS, ACT-FR, ACT-RFS, surf-lifesaving, bushfires-NT, ASA) — incident intake, jurisdictional theming, resource availability, tasking ack, mutual-aid handoffs; NSW-jurisdiction screenshot variant present (Acceptance Scenario US1 #3)
- [ ] CHK012 **[Gate]** `frontline-medical` (AV, NSW Ambulance, QAS, SAAS, SJA family, AT, ACT Ambulance, RFDS) — patient-load reporting, hospital availability, medical supply requests, retrieval coordination
- [ ] CHK013 **[Gate]** `frontline-police` (VicPol, NSWPF, QPS, SAPOL, WAPOL, TasPol, NTPF, ACT Policing, AFP, ABF) — perimeter coordination, traffic management, evacuation enforcement, multi-agency liaison
- [ ] CHK014 **[Gate]** `frontline-ses & marine` (SES VIC/NSW/QLD/SA/TAS/ACT, NTES, MRNSW) — storm/flood/marine workflows, volunteer activation, rescue tasking, water-domain SA
- [ ] CHK015 **[Gate]** `commonwealth` (NEMA, ADF, BoM-national, Geoscience Australia, Australian Red Cross) — national coordination dashboards, RFA flows, weather/geo data interpretation, recovery hand-off
- [ ] CHK016 **[Gate]** `cross-sector` (community NGOs, health, local/state/territory government, transport, utility, volunteer) — partner intake, jurisdictional context, recovery coordination, volunteer activation, infrastructure status

## 3. Help Content Domains (FR-003, Spec §Help Content Domains 1–9)

- [ ] CHK017 **[Gate]** Domain 1 — Getting started (Hub overview, sign-in, persona switcher, jurisdiction filter, theme/accessibility settings) published with screenshots
- [ ] CHK018 **[Gate]** Domain 2 — Persona-specific workflows (one curated journey per role and per cluster) published — cross-references CHK001–CHK016
- [ ] CHK019 **[Gate]** Domain 3 — Screen-by-screen guides published for **all** primary surfaces enumerated in spec: Disaster Mapper, Governance Dashboard, Multi-Jurisdiction Filter, Simulation Control, Alert Composer, Communication agent, Evacuation agent, Monitoring agent, Risk Assessment agent, Resource Allocation agent, Audit/Observer view, Persona switcher, Settings, Login
- [ ] CHK020 **[Gate]** Domain 4 — Simulation playbook (scenario config, warp/playback, multi-jurisdiction scenarios, observation export) — Acceptance Scenario US4 #1 verified end-to-end
- [ ] CHK021 **[Gate]** Domain 5 — Agent playbooks: Communication ✅, Evacuation ✅, Monitoring ✅, Risk Assessment ✅, Resource Allocation ✅ — each with provenance, confidence, human-approval steps; Acceptance Scenario US4 #2 (Evacuation) verified
- [ ] CHK022 **[Gate]** Domain 6 — Audit & observer mode guide (append-only timeline, framework-deviation review, lessons-learned export); Acceptance Scenario US4 #3 verified
- [ ] CHK023 **[Gate]** Domain 7 — Accessibility how-tos (keyboard nav, screen-reader use, contrast/theme, multilingual authoring for PIO) (FR-024)
- [ ] CHK024 **[Gate]** Domain 8 — Troubleshooting/FAQ covers all enumerated topics: login, persona switching, jurisdiction filter, degraded mode, alert approval failures, simulation reset, chat refusals (FR-021)
- [ ] CHK025 **[Gate]** Domain 9 — Glossary published covering AIIMS, AIDR, jurisdictional, Hub-specific terms; glossary returns first on matching search (FR-021, US5 #1)
- [ ] CHK026 Help Centre is reachable via persistent control from every primary screen (FR-001)
- [ ] CHK027 Articles support contextual open ("Help on this screen") and stable deep-links (FR-005)

## 4. Visual & Accessibility Delivery (FR-006 – FR-009a, Spec §Visual Requirements, §Accessibility)

- [ ] CHK028 **[Gate]** Every primary screen has ≥1 annotated screenshot with numbered callouts mapped to numbered prose steps (FR-006)
- [ ] CHK029 **[Gate]** Both light **and** dark variants present and auto-switch with active theme (FR-007); evidence: theme-toggle test report (US1 #5)
- [ ] CHK030 **[Gate]** Every screenshot has descriptive alt text **and** an adjacent keyboard-only steps block (FR-008, US3 #3)
- [ ] CHK031 **[Gate]** WCAG 2.2 AA conformance audit passed with **zero unresolved Level A/AA issues** for all Help surfaces and chat panel (FR-009, SC-006) — attestation report attached
- [ ] CHK032 **[Gate]** Visible focus indicators in all embedded interactive examples (Spec §Visual Requirements)
- [ ] CHK033 Keyboard-only navigation through full Help Centre + chat verified end-to-end (FR-009)
- [ ] CHK034 Screen-reader run-through (NVDA + JAWS or equivalent) of one article per persona completed
- [ ] CHK035 **[Gate]** FR-009a `lang` attribute hygiene: automated linter validates every embedded non-English fragment (Aboriginal & Torres Strait Islander terms, community-language items, AIIMS-adjacent non-English terms, non-English place names) carries correct `lang`; ≥1 screen-reader pronunciation spot-check evidence per language present in corpus
- [ ] CHK036 Chat panel announces status changes (sending, refused, redacted, complete) to assistive tech (FR-009)

## 5. Snapshot Governance (FR-011 – FR-011d)

- [ ] CHK037 **[Gate]** Chat retrieval **never** resolves live `HEAD` of `specs/**`; resolves only the active Help-approved snapshot (FR-011, FR-011a) — verified by inspecting retrieval pipeline + integration test
- [ ] CHK038 **[Gate]** Only specs in `Active`/`Implemented` status that passed Help-approval review are admitted to the snapshot; draft/experimental/archived/unreviewed are excluded — snapshot manifest review evidence
- [ ] CHK039 **[Gate]** Snapshot record persists: `snapshot_id`, included `spec_id+version` list, approver identities (both), approval timestamp (FR-011a)
- [ ] CHK040 **[Gate]** Snapshots are **immutable**; no in-place edit path exists (FR-011c) — verified by attempting an edit and observing rejection
- [ ] CHK041 **[Gate]** Dual sign-off enforced: Help-content owner **AND** safety/governance lead required to publish (FR-011b, mirrors spec-005 FR-015)
- [ ] CHK042 **[Gate]** Approver identities + timestamps surfaced in chat audit log (FR-011b)
- [ ] CHK043 **[Gate]** Rollback completes within **5 minutes** by re-publishing prior immutable snapshot id via configuration flip (no code redeploy) (FR-011c, mirrors spec-029 FR-008) — timed rehearsal evidence
- [ ] CHK044 **[Gate]** Rollback emits `audit.snapshot_rollback` event with `previous_snapshot_id`, `restored_snapshot_id`, `actor_id`, `change_reason`
- [ ] CHK045 **[Gate]** Deep links into superseded content render deprecation notice with old snapshot id, replacement date, new snapshot id, **and** citation to current equivalent — never silently substituted (FR-011d, Principle IV)
- [ ] CHK046 Snapshot refresh cadence is at minimum once per release; out-of-cycle refresh path uses the same approval gate

## 6. Stale-Screenshot Detection (FR-010, FR-010a, FR-010b)

- [ ] CHK047 **[Gate]** UI build pipeline computes deterministic `screen_id_hash = hash(route_id + ordered DOM fingerprints of numbered callout anchors)` for every documented surface
- [ ] CHK048 **[Gate]** Help asset registry stores `screen_id_hash` recorded at screenshot capture; release pipeline compares live vs stored and raises `Staleness Flag` on mismatch
- [ ] CHK049 **[Gate]** First "may be out of date" banner shows immediately on flag-raise; refresh task auto-created for authors (FR-010, FR-010b)
- [ ] CHK050 **[Gate]** If not refreshed by next release, **second** "screenshots not yet refreshed for this release" banner is added (grace-period escalation)
- [ ] CHK051 **[Gate]** Stale-flagged article is **never** auto-removed (Principle I — no silencing) — verified by attempting forced removal and observing prevention
- [ ] CHK052 SC-012 telemetry in place: 90% of stale-flagged screenshots refreshed within one release cycle — dashboard query attached

## 7. Chat Grounding & Safety (FR-011 – FR-016, FR-025)

- [ ] CHK053 **[Gate]** Chat answers ground exclusively in: in-product Help articles + `docs/corpus/**` + `docs/aidr/**` + active Help-approved spec snapshot (FR-011) — corpus-source allowlist test
- [ ] CHK054 **[Gate]** Refusal on out-of-scope: standard non-judgemental message + pointer to right surface/contact; refusal logged for review (FR-013, Edge Case) — evaluation set includes weather, legal, medical, cross-tenant prompts; **100% refusal rate** (SC-002) — attached test report
- [ ] CHK055 **[Gate]** Every factual claim has ≥1 inline citation deep-linking to source article + heading (FR-012, US2 #7)
- [ ] CHK056 **[Gate]** Persona-aware retrieval: only the **active** persona biases retrieval; never the union of entitled personas; never another persona's content (FR-015, FR-028)
- [ ] CHK057 **[Gate]** Australian data-residency: all chat processing, embeddings/indexes, retrieval, storage, logs remain in AU (FR-018, SC-011) — infra attestation per release attached
- [ ] CHK058 **[Gate]** PII redaction gateway path verified: redaction occurs **before** grounding/answering pipeline; user notified when redaction occurs (FR-017, US2 #4) — consistent with spec-036 data-minimisation gateway pattern; trace evidence for sample inputs
- [ ] CHK059 **[Gate]** No fabrication: SC-003 sampling audit shows **0** verified cases of claims not traceable to a citation; on insufficient corpus, chat states inability + offers nearest articles + support handoff (FR-014)
- [ ] CHK060 Conflict surfacing: when corpus sources disagree, chat cites both and recommends human verification (FR-016, Edge Case)
- [ ] CHK061 **[Gate]** Read-only persona protection: when active persona is Observer-Auditor, chat NEVER instructs state-changing operations (FR-025, Edge Case) — evaluation set evidence

## 8. Tenant Isolation (FR-019, SC-004)

- [ ] CHK062 **[Gate]** Chat retrieval scoped strictly to active tenant; cross-tenant retrieval impossible by design (FR-019)
- [ ] CHK063 **[Gate]** Transcript storage tenant-partitioned (Cosmos `/tenant_id` partition key per FR-029)
- [ ] CHK064 **[Gate]** Support-handoff destination configuration is per-tenant (FR-023a)
- [ ] CHK065 **[Gate]** Negative-feedback content-review backlog is tenant-scoped (FR-022a)
- [ ] CHK066 **[Gate]** Audit log entries tenant-scoped and retrievable only within tenant scope (FR-020, FR-029a)
- [ ] CHK067 **[Gate]** Red-team test: **0 cross-tenant retrievals** in any environment (SC-004) — test report attached

## 9. Persistence & Retention (FR-029, FR-029a)

- [ ] CHK068 **[Gate]** Chat conversations persisted per-tenant in Cosmos DB within AU residency boundaries (FR-029)
- [ ] CHK069 **[Gate]** Transcript retention = **30 days** (operational data class — strict spec-001 NFR-002 ≤30 d cap); auto-purge job verified by integration test producing aged transcript and confirming removal
- [ ] CHK070 **[Gate]** Audit log retention = **7 years** (per spec-001 NFR-012, spec-036 FR-RAG-COMP-01 / APP 11); auto-purge / lifecycle policy verified
- [ ] CHK071 **[Gate]** Both retention windows enforced by automatic purge — purge job alarms wired
- [ ] CHK072 Observer-Auditor can retrieve any chat audit-log entry within tenant scope at any time during 7-year window (FR-029a)
- [ ] CHK073 Transcripts older than 30 days no longer surfaced in user history but reconstructable from audit log

## 10. Feedback Loop (FR-022, FR-022a)

- [ ] CHK074 **[Gate]** Each article and each chat response exposes helpful/not-helpful + free-text feedback control (FR-022)
- [ ] CHK075 **[Gate]** Negative feedback enqueued in tenant-scoped content-review backlog visible to Help authors (FR-022a)
- [ ] CHK076 **[Gate]** Auto-promotion to "needs review" when ≥3 negative ratings within rolling 30-day window for the same article or chat-answer pattern — verified by simulation
- [ ] CHK077 **[Gate]** Negative feedback **never** auto-disables, hides, or alters the article/answer (Principle I — humans-only withdrawal via FR-011b snapshot gate) — attempted-suppression test rejected

## 11. Support Handoff (FR-023, FR-023a, FR-023b)

- [ ] CHK078 **[Gate]** Chat panel exposes one-click handoff to human support whenever assistant cannot answer or user requests it (FR-023)
- [ ] CHK079 **[Gate]** Per-tenant handoff record schema enforced with required fields: `channel_type` (email | shared mailbox | on-call rotation | chat link), `address/identifier`, `business_hours_window` (or `24x7`), `incident_mode_override_channel` (FR-023a)
- [ ] CHK080 **[Gate]** Platform-default support address falls back when no tenant record configured (no silent failure) (FR-023a)
- [ ] CHK081 **[Gate]** SLA timer: **5 minutes** during NEMA-Level-3 (or state-equivalent) incidents; **4 business hours** otherwise (FR-023b, mirrors spec-036 Q-P1-03)
- [ ] CHK082 **[Gate]** SLA breach emits `audit.support_handoff_unack_timeout` event with sufficient detail for Observer-Auditor review

## 12. Persona-Context Resolution (FR-027, FR-028)

- [ ] CHK083 **[Gate]** Default persona derived from IdP role claim; for multi-role users, the **highest-authority operational role** is selected (mirrors spec-021 FR-025)
- [ ] CHK084 **[Gate]** Persona switcher allows override to any entitled persona
- [ ] CHK085 **[Gate]** Active persona at each chat turn AND each article load recorded in audit log alongside its source (IdP claim vs user override) (FR-027)
- [ ] CHK086 **[Gate]** Multi-role landing page shows union of entitled persona tiles ordered by authority rank (highest-authority first) (FR-028)
- [ ] CHK087 **[Gate]** Chat uses **only** the active persona — never the union — to prevent leaking guidance scoped to an unentered role

## 13. Degraded Connectivity (FR-026, FR-026a, FR-026b)

- [ ] CHK088 **[Gate]** Available offline: previously-viewed Help articles, full glossary, curated troubleshooting/FAQ topics (FR-026a)
- [ ] CHK089 **[Gate]** Unavailable offline: chat assistant (visibly disabled with explanatory message), free-text search across uncached corpus, retrieval against `docs/aidr/**` / `docs/corpus/**` / spec snapshot — each surfaces standard "unavailable in degraded mode" message
- [ ] CHK090 **[Gate]** Cache TTL = **14 days**; per-device footprint stays within ≤500 MB envelope **shared with** Field Coordinator offline cache (spec-036 FR-RAG-LS-02), not additive — measured + asserted in test
- [ ] CHK091 **[Gate]** On reconnect, audit-logged refresh occurs (mirrors FR-RAG-LS-02)
- [ ] CHK092 **[Gate]** Articles past TTL display "may be stale — last cached `<YYYY-MM-DD>`" banner until refreshed
- [ ] CHK093 Chat-disabled state in degraded mode points user to cached troubleshooting content (FR-026, Edge Case)

## 14. Cross-Spec Dependency Verification (Spec §Dependencies)

- [ ] CHK094 **spec-001** — Persona / Organisation / Incident / AuditEntry data model reused; no redefinition; tenant + jurisdiction model reused
- [ ] CHK095 **spec-005** — Knowledge corpus sources classified per data-source governance; corpus-source allowlist tied to spec-005 tenant scoping; FR-011b dual-sign-off mirrors spec-005 FR-015
- [ ] CHK096 **spec-008** — Communication Agent playbook accurate against agent's current contract
- [ ] CHK097 **spec-009** — Evacuation Agent playbook accurate against agent's current contract (US4 #2)
- [ ] CHK098 **spec-010** — Monitoring Agent playbook accurate against agent's current contract
- [ ] CHK099 **spec-011** — Resource Allocation Agent playbook accurate against agent's current contract
- [ ] CHK100 **spec-012** — Risk Assessment Agent playbook accurate against agent's current contract
- [ ] CHK101 **spec-018 / spec-019** — `docs/aidr/**` AIDR guidance integration verified as a grounded corpus source
- [ ] CHK102 **spec-020** — Disaster Mapper screen-by-screen guide matches current UI; screenshots captured against the spec-020 surface
- [ ] CHK103 **spec-021** — Governance Dashboard guide matches current UI; FR-028 multi-role authority order mirrors spec-021 FR-025
- [ ] CHK104 **spec-022** — Multi-jurisdiction filter context propagation reused in persona/jurisdiction-aware retrieval (FR-015)
- [ ] CHK105 **spec-024** — Simulation control + chat-turn persistence patterns reused for Cosmos `/tenant_id` partition (FR-029); NEMA-Level-3 banner pattern reused for FR-023b
- [ ] CHK106 **spec-026** — Sim warp/playback playbook content matches spec-026 contract (US4 #1)
- [ ] CHK107 **spec-029** — 5-minute reversibility SLO via flag flip reused for snapshot rollback (FR-011c)
- [ ] CHK108 **spec-036** — Foundry RAG grounding + data-minimisation gateway pattern reused for FR-017 PII redaction; FR-RAG-LS-02 cache envelope shared (FR-026b); FR-RAG-COMP-01 7-year audit retention reused (FR-029); FR-RAG-COORD-02 5-minute escalation timer mirrored (FR-023b)

## 15. Constitution Principle Acceptance

- [ ] CHK109 **[Gate] Principle I — Primacy of Life**: stale-flagged articles never auto-removed (FR-010b); negative feedback never silences content (FR-022a); life-safety guidance remains readable offline (FR-026a) — three "no silencing" controls confirmed live
- [ ] CHK110 **[Gate] Principle III — Resilience**: append-only audit log of every chat interaction (prompt, redacted input, citations, response, refusal reason) operational and tamper-evident (FR-020)
- [ ] CHK111 **[Gate] Principle IV — Transparency / Auditability**: snapshot publication, rollback, deep-link supersession, persona-context-per-turn, support-handoff SLA breaches — every governance event has a corresponding audit entry; deprecation notice never silently substitutes content (FR-011a–d, FR-027, FR-023b)
- [ ] CHK112 **[Gate] Principle V — Accessibility / Multilingual**: WCAG 2.2 AA conformance attested (FR-009, SC-006); `lang` attribute hygiene for embedded non-English fragments verified (FR-009a, SC 3.1.2); PIO multilingual authoring guide published (FR-024)

## 16. Success Criteria Verification (SC-001 – SC-012)

- [ ] CHK113 **SC-001** — Task-based usability test with ≥1 participant per persona; **95%** locate correct article within 60 s — test report attached (manual review)
- [ ] CHK114 **SC-002** — Maintained in-scope + out-of-scope evaluation sets; ≥**90% citation rate** on in-scope, **100% refusal** on out-of-scope (test, run per release)
- [ ] CHK115 **SC-003** — Continuous sampled audit of chat sessions; **0** verified fabrication cases per release (audit + telemetry)
- [ ] CHK116 **SC-004** — Audit-log review + red-team test confirm **0** cross-tenant retrievals/answers in any environment (audit + test)
- [ ] CHK117 **SC-005** — Coverage report: 100% of primary screens have ≥1 light + ≥1 dark annotated screenshot with alt text + keyboard-equivalent path (telemetry / build-time report)
- [ ] CHK118 **SC-006** — WCAG 2.2 AA conformance attestation report, zero unresolved Level A/AA issues at release (manual review + automated axe scan)
- [ ] CHK119 **SC-007** — Median time-to-first-useful-answer **<5 s** for in-scope questions on representative connectivity profile (telemetry, p50)
- [ ] CHK120 **SC-008** — Cross-cluster cohort study: ≥**80%** of participants complete persona "first 15 minutes" tour in <15 minutes (manual review)
- [ ] CHK121 **SC-009** — 3-month post-release: human "how do I…" support volume down ≥**40%** vs pre-release baseline (telemetry / support system metrics)
- [ ] CHK122 **SC-010** — 100% of chat interactions in append-only audit log with redacted input + citations + response, retrievable by Observer-Auditor in tenant scope (audit query sample evidence)
- [ ] CHK123 **SC-011** — Per-release infra attestation: 100% of chat data processing within AU residency boundaries (audit + attestation)
- [ ] CHK124 **SC-012** — 90% of screenshots flagged stale by a UI change refreshed within one release cycle (telemetry dashboard query)

## 17. Edge Cases & Out-of-Scope Boundaries

- [ ] CHK125 Out-of-scope chat questions: standard refusal + pointer + refusal logged (Edge Case) — covered in CHK054
- [ ] CHK126 Cross-tenant question refused on isolation grounds; no retrieval performed (Edge Case) — covered in CHK062 / CHK067
- [ ] CHK127 PII in user input: redacted at gateway; user informed (Edge Case) — covered in CHK058
- [ ] CHK128 Corpus disagreement: surface conflict, cite both, recommend human verification — covered in CHK060
- [ ] CHK129 No matching corpus answer: state inability + nearest articles + support handoff — covered in CHK059
- [ ] CHK130 Stale screenshots: in-product flag visible — covered in CHK049–CHK051
- [ ] CHK131 Multilingual: PIO authoring guide present (FR-024) — covered in CHK023; Help UI itself stays English (Pass 1 decision; out-of-scope confirmed)
- [ ] CHK132 Out-of-Scope confirmed *not* delivered: Help-UI localisation, voice chat I/O, public unauthenticated portal, AIIMS-doctrine training replacement, chat-initiated state changes (Spec §Out of Scope)

## 18. Operational Readiness

- [ ] CHK133 Runbook for snapshot publish + rollback documented and rehearsed
- [ ] CHK134 On-call playbook for SLA-breach `audit.support_handoff_unack_timeout` events
- [ ] CHK135 Dashboards live for SC-002 / SC-003 / SC-007 / SC-009 / SC-012 telemetry
- [ ] CHK136 Tenant onboarding form includes support-handoff record fields (FR-023a)

---

## Notes

- Items marked **[Gate]** are release-blocking; tick only with linked evidence (test id, query, audit sample, attestation, signed reviewer note).
- Each `/speckit.checklist` invocation creates a NEW file; this file complements `requirements.md` (spec-quality) — do not overwrite.
- Cross-references use `Spec §`, `FR-`, `SC-`, `US#`, or `Edge Case` markers from `../spec.md`.

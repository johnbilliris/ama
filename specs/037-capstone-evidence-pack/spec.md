# Feature Specification: Capstone Evidence Pack — Residual Rubric Gap Closure

**Feature Branch**: `037-capstone-evidence-pack`  
**Created**: 2026-05-11  
**Status**: Draft  
**Input**: User description: "Close the residual capstone-rubric gaps identified in a Step 0 review of the AMA solution against the rubric. Demo (spec 016) and FinOps cost dashboard are explicitly excluded. Five durable, evidence-bearing, version-controlled artefacts: (1) Systematic Risk Register, (2) Adoption Roadmap, (3) Executive KPI Surface, (4) Responsible AI Register, (5) Feature-to-Value Ledger + Decision/Tradeoff Log."

> **Capstone-criticality flag**: This spec is **non-capstone-critical-path / delivery-hygiene** in the sense of `028-capstone-alignment` FR-020. It produces evidence artefacts that *prove* the value already delivered by specs 001–036 against the assessment rubric; it does NOT directly deliver a capstone success-criterion metric. It MUST be tagged accordingly in `specs/shared/capstone-metric-trace.md` and in any roll-up scorecards.

## Clarifications

### Session 2026-05-11

- Q: Provenance of evidence not yet automated (FR-037) — stub manual rows, block publication, or ship degraded? → A: Stub manual-entry rows tagged `provenance: manual` with named owner + review cadence (`quarterly|monthly|post-incident`) and an `automation_target` reference; expose a `manual_row_count` counter on each artefact's metadata block.
- Q: Is the simulation telemetry-injection agent (`036-sim-agent-extend`) a production AI component for RAI scope (FR-024)? → A: Yes — full production AI component requiring a complete row across 4 frameworks × 8 principles. Simulation watermark / `[SIMULATION]` chat-receipt prefix do not reduce RAI obligations.
- Q: Hosting model for the read-only Executive KPI page (FR-021)? → A: New top-level route `apps/web/src/app/governance/executive/`, sibling to existing `/governance/dashboard/{audit,compliance,readiness,recovery,risk}` routes from spec 035; reuses `PersonaWorkspace` + audit-row read primitives — no net-new UI primitives.
- Q: Manual-evidence cap that blocks publication (FR-037 follow-up) — fleet-wide cap, per-artefact cap, or no cap? → A: Per-artefact cap at ≤ 50 % manual rows for v1; > 50 % requires named-auditor sign-off recorded in the artefact metadata (matches `Validated`/`Deferred`/`Unresolved` precedent in `specs/shared/capstone-metric-trace.md`; preserves NN-1 human-in-the-loop while not disabling the inherently judgement-heavy RAI Register).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Risk Manager assembles a portfolio-wide Systematic Risk Register (Priority: P1)

The Risk Manager persona currently has only `docs/risk-register/RISK-AOAI-001.md` (3 AI-only risks). They need a single, schema-bound register that consolidates Platform, AI, Operational, Jurisdictional, Data, and Supply-chain risks across the whole portfolio, each row carrying likelihood × consequence, treatment, ownership, residual risk, and review cadence — so that an Observer-Auditor or Executive Leader can answer "what are our top 10 portfolio risks today and who owns each?" in under five minutes without reading 36 specs.

**Why this priority**: Risk visibility is a hard rubric requirement ("Mandatory: risks & tradeoffs") and is the single biggest gap surfaced in the Step 0 review. Without it, every other artefact in this pack lacks the risk context auditors expect. It is also the operational persona explicitly named in the synthesised Step 1 input.

**Independent Test**: A reviewer can open `docs/risk-register/index.md` and `docs/risk-register/<RISK-ID>.md` files, confirm each row matches the published schema, sort by residual-risk score, and trace each risk back to its originating spec(s). Delivered value standalone: passes the "risks & tradeoffs" mandatory rubric criterion.

**Acceptance Scenarios**:

1. **Given** the existing single-file risk register, **When** the new Systematic Risk Register is published, **Then** at least one risk row exists per category (Platform, AI, Operational, Jurisdictional, Data, Supply-chain) and each row conforms to the published schema validated by an automated schema check.
2. **Given** any risk row, **When** an auditor opens it, **Then** they see likelihood (1–5), consequence (1–5), inherent score, treatment summary, owner (named role), residual likelihood/consequence/score, next review date, and back-citations to the spec(s) and ADR(s) that introduced or mitigated the risk.
3. **Given** a risk whose review date has passed, **When** the register's roll-up is rendered, **Then** that risk is flagged "review overdue" and counted in an overdue-risks summary.

---

### User Story 2 — Resilience Planner publishes a phased Adoption Roadmap (Priority: P1)

The Resilience Planner needs the first concrete, jurisdiction-onboarding sequence for the platform: which AIIMS-aligned cohort adopts in which order (state lead agencies → local government → utilities → transport → volunteer/NGO → Commonwealth), what readiness gates each pilot must clear, what training/exercise cadence is required, what change-management artefacts accompany each adoption wave, and what decommission/rollback criteria allow a pilot to be retired without harming life-safety.

**Why this priority**: Adoption is a rubric **differentiator** and is currently absent. Without a phased roadmap, the platform's value-realisation story has no timeline. Field Coordinator, Incident Commander, and Executive Leader personas all depend on this artefact.

**Independent Test**: A reviewer can open `docs/governance-hub/adoption-roadmap/roadmap.md`, identify wave 1 → wave N cohorts, read the readiness gates and rollback criteria for any wave, and confirm the wave order matches the synthesised sector-cohort input. Delivered value standalone: passes the "adoption roadmap" differentiator rubric criterion.

**Acceptance Scenarios**:

1. **Given** the eight Australian jurisdictions plus Commonwealth, **When** the roadmap is published, **Then** every jurisdiction appears in at least one wave with an explicit lead agency and at least one readiness gate.
2. **Given** any wave, **When** an exercise/training cadence is specified, **Then** the cadence references existing simulation, scenario-pack, or exercise capabilities (specs 007, 024, 026) rather than introducing new tooling.
3. **Given** any pilot, **When** rollback criteria are listed, **Then** the criteria explicitly preserve life-safety defaults defined in the constitution and degrade to manual operations without data loss.

---

### User Story 3 — Executive Leader reads a single Executive KPI Surface (Priority: P1)

The Executive Leader needs one surface that maps the five capstone success criteria (1,000+ lives saved/yr, 50% response-time reduction, 24-hour earlier evacuation, 30% logistics efficiency, 30% economic-loss reduction) to a leading + lagging KPI ladder. Each KPI specifies its owner, refresh cadence, target/threshold, source-of-truth, AND the existing scattered surfaces it consolidates — so an executive answers "are we on track against the capstone?" without opening five different dashboards.

**Why this priority**: KPI instrumentation is a rubric **differentiator**. Today, KPIs are scattered across `docs/governance-dashboard.md`, `docs/governance-hub/observability/slo.md`, `docs/governance-hub/observability/metrics-catalogue.md`, spec 015 SC-CAP-015-001..005, spec 021, and spec 030. Consolidation turns "many sources" into "one executive truth".

**Independent Test**: A reviewer can open `docs/governance-hub/executive-kpi/surface.md` plus `docs/governance-hub/executive-kpi/surface.json`, confirm each of the five capstone criteria has at least one leading and one lagging KPI, and confirm every KPI cites its source-of-truth. Delivered value standalone: passes the "KPI instrumentation" differentiator rubric criterion.

**Acceptance Scenarios**:

1. **Given** the five capstone success criteria, **When** the KPI surface is published, **Then** each criterion has ≥1 leading and ≥1 lagging KPI with named owner, refresh cadence, target value, threshold/alert band, and source-of-truth link.
2. **Given** any KPI, **When** it is rendered in the read-only Executive KPI page in `apps/web/src/app/governance/`, **Then** the page reuses the existing governance shell (no new chart libraries, no new infra) and displays values sourced from existing telemetry sinks (App Insights, Cosmos audit, governance-hub Markdown).
3. **Given** a KPI that consolidates pre-existing scattered surfaces, **When** the row is rendered, **Then** every superseded scattered surface is named and linked, and a deprecation note is added to each superseded surface pointing here.

---

### User Story 4 — Responsible AI Officer publishes a consolidated Responsible AI Register (Priority: P1)

The Responsible AI Officer (today implicit; formalised by this spec) needs one register that documents, for every AI/agentic component, its posture against Australia's 8 AI Ethics Principles, ISO/IEC 42001 management-system controls, ISO/IEC 23894 risk-management controls, and the NIST AI RMF Govern/Map/Measure/Manage profiles. Per-component rows must cover human oversight, fairness, accountability, transparency, privacy, safety, contestability, and reliability.

**Why this priority**: Responsible AI is a rubric **differentiator** and a regulator-facing artefact. Today, RAI evidence is implicit in spec 030's clarification line. Consolidation makes RAI auditable per agent.

**Independent Test**: A reviewer can open `docs/governance-hub/rai-register/responsible-ai-register.md`, locate any AI/agentic component (the 5 specialist sub-agents from specs 008–012, the simulation telemetry-injection agent from spec 036-sim-agent-extend, the LLM-eval framework from spec 030, the Foundry RAG client from spec 036-foundry-rag-grounding), and read its compliance posture across all four frameworks. Delivered value standalone: passes the "Responsible AI" differentiator rubric criterion.

**Acceptance Scenarios**:

1. **Given** the in-scope AI components, **When** the register is published, **Then** every component has a row with all four framework columns populated and all eight principle columns populated; missing entries appear as explicit "not-applicable + justification" rather than blanks.
2. **Given** any component row, **When** an auditor reviews it, **Then** the row cites back into spec 030's evaluation outputs (no re-evaluation is performed) and into the relevant agent spec (008–013, 030, 036).
3. **Given** a regulator-facing review, **When** the register is exported, **Then** it produces a stable Markdown + JSON pair suitable for archiving alongside `docs/aidr/`.

---

### User Story 5 — Capstone Reviewer reads Feature-to-Value Ledger and Decision/Tradeoff Log (Priority: P2)

A Capstone Reviewer needs an inverse, **feature-centric** ledger that complements the existing **metric-centric** `specs/shared/capstone-metric-trace.md`: for every spec 001–036, the ledger names the spec, the capstone metric(s) it contributes to, the magnitude/direction of contribution, and the residual gap to target. Bundled with this is a consolidated decision/tradeoff log that links every existing ADR under `docs/aidr/decisions/` to the feature it bounds, the alternatives considered, and the rationale.

**Why this priority**: This artefact directly addresses the rubric "business value mapping" mandatory criterion and the "risks & tradeoffs" mandatory criterion from the feature-side perspective. P2 because the metric-centric trace already partially satisfies the mandatory bar; this ledger lifts the score from "covered" to "differentiator-grade".

**Independent Test**: A reviewer can open `specs/shared/feature-value-ledger.md` and `docs/decisions/tradeoff-log.md`, locate any spec 001–036 by number, and read its mapped capstone metric(s) and the ADR(s) bounding its key tradeoffs. Delivered value standalone: passes "business value mapping" + adds depth to "risks & tradeoffs".

**Acceptance Scenarios**:

1. **Given** the set of merged specs 001–036, **When** the feature-value ledger is published, **Then** every spec appears as a row with at least one mapped capstone metric (or an explicit "delivery-hygiene" tag if it does not contribute to a capstone metric).
2. **Given** any ADR under `docs/aidr/decisions/`, **When** the tradeoff log is rendered, **Then** the ADR appears with its bounding feature(s), the alternatives considered, and the rationale for the chosen path.
3. **Given** a metric whose residual gap-to-target is non-zero, **When** the ledger is reviewed, **Then** at least one open follow-up (spec, issue, or roadmap wave) is named for closing the gap.

---

### Edge Cases

- **Stale citations**: A cited spec is later renamed or deleted — the artefact MUST fail an automated link-check rather than silently pointing to a 404.
- **Schema drift**: A risk row is added that omits required fields — schema validation MUST fail in CI before publication.
- **Conflicting jurisdiction sequencing**: Two jurisdictions claim "wave 1" but readiness gates are unmet for one — the roadmap MUST gate by readiness, not by political sequencing, and document the deviation.
- **Superseded scattered surface still being updated**: After deprecation, a superseded dashboard or markdown is edited — the deprecation banner MUST direct the editor to the consolidated surface.
- **AI component added later** (e.g., a future spec 038 introduces a new agent): The RAI register MUST require a new row before that agent is allowed to ship; this is enforced via the governance-discovery instructions.
- **Manual-evidence cap exceeded**: An artefact's `manual_row_ratio` exceeds 0.5 without a complete `auditor_signoff` block — the artefact-publication CI check MUST fail and the artefact MUST NOT publish until either ratio ≤ 0.5 or a named-auditor sign-off (with framework basis) is recorded in the metadata.
- **Append-only audit conflict**: An attempt to retroactively edit a published risk or KPI row MUST be rejected; corrections happen via a new dated revision row preserving the prior value.
- **Degraded telemetry**: When an upstream telemetry sink (App Insights, Cosmos audit) is unavailable, the KPI surface MUST display "stale as of <timestamp>" rather than blank or stale-but-fresh-looking values.

## Requirements *(mandatory)*

### Functional Requirements

#### Cross-cutting

- **FR-001**: The pack MUST publish exactly five durable artefacts: (a) Systematic Risk Register, (b) Adoption Roadmap, (c) Executive KPI Surface, (d) Responsible AI Register, (e) Feature-to-Value Ledger + Decision/Tradeoff Log.
- **FR-002**: All five artefacts MUST be version-controlled under `docs/` or `specs/shared/` (no ephemeral storage) and MUST be referenced from `docs/governance-hub/index.md`.
- **FR-003**: Every artefact MUST cite back into existing specs by spec number and section heading; no artefact may duplicate spec content beyond what is needed for context.
- **FR-004**: No artefact may modify the constitution (`.specify/memory/constitution.md`).
- **FR-005**: Every artefact MUST honour AU residency, append-only audit, human-in-the-loop, and graceful-degradation constraints from constitution v1.2.0; published rows are immutable and corrections are made via dated revision rows.
- **FR-006**: Where any artefact introduces or modifies a governance-constraint file, it MUST comply with `.github/instructions/governance-discovery.instructions.md`.
- **FR-007**: This spec MUST self-flag as "non-capstone-critical-path / delivery-hygiene" in `specs/shared/capstone-metric-trace.md` per the contract in `028-capstone-alignment` FR-020.
- **FR-008**: An automated link-check MUST run in CI over all five artefacts; broken back-citations MUST fail the pipeline.
- **FR-009**: An automated schema-check MUST validate the Risk Register, KPI Surface, RAI Register, and Feature-Value Ledger against published schemas (one schema per artefact). The schema-check MUST also enforce the manual-evidence cap defined in FR-038: any artefact with `manual_row_ratio > 0.5` and missing/incomplete `auditor_signoff` metadata MUST fail the publication pipeline.

#### Systematic Risk Register (artefact 1)

- **FR-010**: The register MUST cover six risk categories: Platform, AI, Operational, Jurisdictional, Data, Supply-chain — each with at least one row.
- **FR-011**: Each risk row MUST carry: ID, title, category, description, likelihood (1–5), consequence (1–5), inherent score, treatment, owner (named role), residual likelihood/consequence/score, next review date, back-citations to spec(s)/ADR(s).
- **FR-012**: The register MUST extend (not replace) the existing `docs/risk-register/RISK-AOAI-001.md`; that file MUST remain valid under the new schema.
- **FR-013**: The register MUST emit a roll-up index (`docs/risk-register/index.md`) sorted by residual score that flags "review overdue" rows.
- **FR-014**: The register MUST honour the request from `operational/risk-manager.agent.md:40-152` for a dynamic, schema-bound, archiveable register with likelihood/consequence matrix.

#### Adoption Roadmap (artefact 2)

- **FR-015**: The roadmap MUST sequence adoption in waves starting with state lead agencies, then local government, utilities, transport, volunteer/NGO, Commonwealth — informed by the synthesised 58-persona sector input.
- **FR-016**: Each wave MUST publish: cohort, lead agency, readiness gates, training/exercise cadence (citing existing capabilities in specs 007, 024, 026), change-management artefacts, decommission/rollback criteria.
- **FR-017**: Decommission/rollback criteria MUST preserve life-safety defaults and degrade gracefully to manual operations without data loss.
- **FR-018**: The roadmap MUST cover all eight Australian jurisdictions plus Commonwealth lanes; each MUST appear in at least one wave with an explicit lead agency.

#### Executive KPI Surface (artefact 3)

- **FR-019**: The surface MUST map each of the five capstone success criteria (`capstone.md` lines 31-36) to ≥1 leading and ≥1 lagging KPI.
- **FR-020**: Each KPI MUST specify owner, refresh cadence, target, threshold/alert band, source-of-truth link, and the scattered surfaces it consolidates from `docs/governance-dashboard.md`, `docs/governance-hub/observability/slo.md`, `docs/governance-hub/observability/metrics-catalogue.md`, `specs/015-performance-benchmarks/spec.md`, `specs/021-governance-dashboard/spec.md`, `specs/030-llm-eval-framework/spec.md`.
- **FR-021**: The surface MUST be published as a Markdown artefact (`docs/governance-hub/executive-kpi/surface.md`) AND a JSON export (`docs/governance-hub/executive-kpi/surface.json`) AND a thin read-only page at the new top-level route `apps/web/src/app/governance/executive/` (sibling to the existing `/governance/dashboard/{audit,compliance,readiness,recovery,risk}` routes established by spec 035). The page MUST reuse the existing governance shell, `PersonaWorkspace`, and audit-row read primitives from spec 035 — no new chart libraries, no net-new UI primitives, no new infrastructure. The page MUST surface the per-artefact `manual_row_ratio` (FR-037 / FR-038) for each of the five artefacts at the top of the Executive KPI Surface so reviewers see the auditability split immediately.
- **FR-022**: Each superseded scattered surface MUST gain a deprecation banner linking to the consolidated KPI surface. Deprecation MAY be section-scoped (banner on the executive-roll-up subsection only) where the file retains an operational role for non-executive content (e.g., `metrics-catalogue.md` continues as the operational metric inventory).
- **FR-023**: When upstream telemetry is unavailable, the rendered surface MUST show "stale as of <timestamp>" rather than rendering as fresh.

#### Responsible AI Register (artefact 4)

- **FR-024**: The register MUST include rows for: the 5 specialist sub-agents from specs 008–012, the simulation telemetry-injection agent from `036-sim-agent-extend` (treated as a production AI component — full row across 4 frameworks × 8 principles; the simulation watermark and `[SIMULATION]` chat-receipt prefix do NOT reduce RAI obligations because the agent is deployed to the same Container Apps revisions as production sub-agents and `036-sim-agent-extend` FR-066 mandates production-grade idempotency + append-only audit on `/inject-telemetry`), the LLM-eval framework from spec 030, the Foundry RAG client from `036-foundry-rag-grounding`.
- **FR-025**: Each row MUST be evaluated against four framework columns: Australia's 8 AI Ethics Principles, ISO/IEC 42001 controls, ISO/IEC 23894 controls, NIST AI RMF (Govern/Map/Measure/Manage profiles).
- **FR-026**: Each row MUST cover eight principle dimensions: human oversight, fairness, accountability, transparency, privacy, safety, contestability, reliability.
- **FR-027**: Empty cells MUST be replaced by an explicit "not-applicable + justification"; blanks are forbidden.
- **FR-028**: The register MUST cite spec 030's evaluation outputs and MUST NOT trigger or re-run any evaluation.
- **FR-029**: The register MUST publish a Markdown + JSON pair suitable for archiving alongside `docs/aidr/`.

#### Feature-to-Value Ledger + Decision/Tradeoff Log (artefact 5)

- **FR-030**: The Feature-Value Ledger MUST include one row per merged spec 001–036; rows that do not contribute to any capstone metric MUST be tagged "delivery-hygiene".
- **FR-031**: Each contributing row MUST name the capstone metric, the magnitude and direction of contribution, and the residual gap-to-target.
- **FR-032**: The Decision/Tradeoff Log MUST include one row per ADR currently under `docs/aidr/decisions/`, naming the bounding feature(s), alternatives considered, and the rationale.
- **FR-033**: For every metric with residual gap-to-target > 0, the ledger MUST name at least one open follow-up (existing spec, issue, or roadmap wave).
- **FR-034**: The ledger MUST be the inverse, feature-centric counterpart to `specs/shared/capstone-metric-trace.md` and MUST cross-link to it.

#### Governance and lifecycle

- **FR-035**: All published artefacts MUST be regenerable from source data (specs, ADRs, governance-hub) without manual transcription, where source data exists.
- **FR-036**: The pack MUST tradeoff-log the synthesised cross-sector tensions: speed vs. legality, automation vs. command authority, local autonomy vs. cross-jurisdiction standardisation, operational visibility vs. privacy/credentialing.
- **FR-037**: Where any artefact requires data not currently produced by existing telemetry sinks, the artefact MUST stub manual-entry rows tagged `provenance: manual` carrying `owner: <named role>`, `review_cadence: <quarterly|monthly|post-incident>`, and `automation_target: <spec/task ref or "none">`. Each artefact's metadata block MUST expose machine-readable `manual_row_count`, `total_row_count`, and `manual_row_ratio` (= `manual_row_count / total_row_count`, range 0..1) so reviewers can see the manual-vs-automated split at a glance. Manual rows MUST follow the same auditable / dated-revision convention as `specs/shared/capstone-metric-trace.md` (`Validated` / `Deferred` / `Unresolved`).
- **FR-038**: Per-artefact manual-evidence cap — for v1, each artefact MUST satisfy `manual_row_ratio ≤ 0.5`. If `manual_row_ratio > 0.5`, the artefact metadata block MUST include an `auditor_signoff` object with fields `{ name, role, signoff_date_utc, basis }` where `basis` cites the AIDR / ISO / NIST framework that authorises the override. Artefacts published with `manual_row_ratio > 0.5` AND missing or incomplete `auditor_signoff` MUST fail the artefact-publication CI check defined in FR-009.

### Key Entities

- **Risk Row** — A single risk with category, scoring (likelihood × consequence inherent and residual), treatment, owner, review cadence, back-citations.
- **Adoption Wave** — A grouped cohort of jurisdictions/sectors adopting together, with readiness gates, exercise cadence, change-management bundle, rollback criteria.
- **KPI Row** — A leading or lagging measure tied to one capstone success criterion, with owner/cadence/target/threshold/source-of-truth and the surfaces it supersedes.
- **RAI Row** — One AI/agentic component evaluated across four frameworks × eight principle dimensions, citing spec 030 evidence.
- **Feature-Value Row** — One spec mapped to capstone metric(s), contribution magnitude/direction, residual gap, and follow-ups.
- **Tradeoff Row** — One ADR mapped to feature(s), alternatives, and rationale.
- **Provenance** — Each row, on every artefact, carries a citation set (spec/ADR/governance-hub/telemetry sink) and a `provenance: automated|manual` tag for auditability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can answer "what are the platform's top 10 portfolio risks today and who owns each?" in under 5 minutes using only the published Systematic Risk Register.
- **SC-002**: 100% of risk rows pass schema validation in CI; 100% of back-citations resolve via the link-checker; zero broken links in the published pack.
- **SC-003**: All eight Australian jurisdictions plus Commonwealth appear in at least one adoption wave with named lead agency and explicit readiness gates.
- **SC-004**: Each of the five capstone success criteria has ≥1 leading and ≥1 lagging KPI on the Executive KPI Surface, with named owner, target, refresh cadence, and source-of-truth.
- **SC-005**: 100% of currently-shipping AI/agentic components (the 5 sub-agents, sim-agent-extend, LLM-eval framework, Foundry RAG client) have a row in the Responsible AI Register with all 4 framework columns × 8 principle dimensions populated (no blanks).
- **SC-006**: 100% of merged specs 001–036 appear in the Feature-Value Ledger; 100% of ADRs under `docs/aidr/decisions/` appear in the Tradeoff Log.
- **SC-007**: The rubric "Mandatory: risks & tradeoffs" and "Differentiators: adoption roadmap, KPI instrumentation, Responsible AI" criteria each move from "partial / scattered" to "covered with single-source evidence" in a Step 0 re-review.
- **SC-008**: An Executive Leader can determine on-track / at-risk status against all five capstone metrics from a single page in under 2 minutes.
- **SC-009**: Zero net-new dashboards, chart libraries, or infrastructure components are introduced; the read-only Executive KPI page reuses the existing `apps/web/src/app/governance/` shell.
- **SC-010**: Spec is correctly self-flagged as "non-capstone-critical-path / delivery-hygiene" in `specs/shared/capstone-metric-trace.md` and is excluded from capstone-metric attribution roll-ups.
- **SC-011**: 100% of published artefacts satisfy `manual_row_ratio ≤ 0.5` OR carry a complete `auditor_signoff` metadata block; CI rejects any artefact violating both conditions.

## Assumptions

- The existing telemetry sinks (App Insights, Cosmos append-only audit, governance-hub Markdown) remain authoritative sources of KPI data; this spec consumes them and does not replace them.
- Spec 016 (Demo) and any FinOps cost dashboard work are explicitly out of scope per user direction.
- Spec 030's existing LLM evaluation outputs are the source of truth for RAI evidence; this spec cites but does not re-run them.
- The "scattered surfaces" enumerated in FR-020 are the complete set to be consolidated; if additional scattered surfaces are discovered during implementation, they will be added to the deprecation list under the same rules.
- The 8 AI Ethics Principles (Australia), ISO/IEC 42001, ISO/IEC 23894, and NIST AI RMF reference texts are stable enough at publication time that posture rows do not need real-time refresh.
- The synthesised operational + sector cohort inputs (`step1-ops-synthesis.md`, `step1-sectors-synthesis.md`) are the canonical persona-evidence base for shaping personas, requirements, and acceptance scenarios in this spec.

## Dependencies

- `specs/shared/capstone-metric-trace.md` (existing) — the metric-centric counterpart; this spec adds the inverse feature-centric ledger.
- `docs/risk-register/RISK-AOAI-001.md` (existing) — extended, not replaced.
- `docs/governance-dashboard.md`, `docs/governance-hub/observability/{slo.md,metrics-catalogue.md}` (existing) — superseded for executive roll-up; deprecation banners added.
- `apps/web/src/app/governance/` (existing) — host shell for the read-only Executive KPI page.
- `docs/aidr/decisions/` (existing) — source of ADRs for the Tradeoff Log.
- `.specify/memory/constitution.md` v1.2.0 — constraints honoured unchanged.
- `.github/instructions/governance-discovery.instructions.md` — honoured for any governance-constraint file produced.
- `028-capstone-alignment` FR-020 — defines the "non-capstone-critical-path / delivery-hygiene" self-flag contract.

## Out of Scope

- Building any net-new operational dashboard UI (only a thin read-only page reusing the existing governance shell is permitted; no new charts).
- Building or redesigning the demo (covered by spec 016).
- Building a FinOps cost dashboard (explicitly excluded by user).
- Re-running or extending spec 030's LLM evaluation framework.
- Introducing any new infrastructure component (Bicep modules, App Service plans, storage accounts, monitoring workspaces).
- Modifying `.specify/memory/constitution.md`.

## Open Clarifications

All three queued `[NEEDS CLARIFICATION]` markers from `/speckit.specify` were resolved in round 1 of the 2026-05-11 clarification session (FR-021, FR-024, FR-037). The round-1 residual question (manual-evidence publication cap) was resolved in round 2 of the same session (FR-037 + new FR-038 + SC-011). Round 3 (post-`/speckit.analyze` orchestrator pre-resolutions, 2026-05-11) canonicalised four artefact filenames (analyser findings I1–I4), narrowed the FR-022 deprecation scope (analyser finding I5), and clarified SC-009's "net-new infrastructure" interpretation (analyser finding C1):

- **I1**: Executive KPI Surface canonical path is `docs/governance-hub/executive-kpi/surface.{md,json}` (FR-021 updated; matches `plan.md` Project Structure + RES-02 IA decision).
- **I2**: Adoption Roadmap canonical path is `docs/governance-hub/adoption-roadmap/roadmap.{md,json}` (US2 Independent Test updated).
- **I3**: Responsible AI Register canonical path is `docs/governance-hub/rai-register/responsible-ai-register.{md,json}` (US4 Independent Test updated; preserves PD-037-05 wording).
- **I4**: Risk Register artefact JSON sidecar is `docs/risk-register/risk-register.json`; the human-readable roll-up file mandated by FR-013 is `docs/risk-register/index.md` — they are different files.
- **I5 / FR-022**: Deprecation banners MAY be section-scoped where the underlying file retains a non-executive operational role.
- **C1 / SC-009**: "Zero net-new infrastructure components" is interpreted as **zero net-new top-level Azure resources**. Child resources of accounts already in `rg-ama` (the 1 Cosmos container `evidence_pack_artefact_cache` and the 1 Blob container `evidence-pack-archive`) and App Insights custom metrics emitted via the existing OpenTelemetry pipeline are explicitly permitted per PD-037-06 + Complexity Tracking.

No open clarifications remain at this time; the spec is ready for `/speckit.implement` after `/speckit.analyze` sign-off.

## Step 8 Cohort Review Amendment Log (2026-05-11)

This log records the amendments applied to spec.md following the **Step 8 cross-cohort
review** (synthetic canvas of 85 personas: 10 operational + 58 sectors + 17 technical)
which returned **ENDORSE-WITH-RESERVATIONS** with **0 CRITICAL / 2 HIGH / 4 MEDIUM / 3 LOW**
findings. Aggregate verdict by cohort: 65 ENDORSE/NIT, 17 ENDORSE-WITH-RESERVATIONS,
2 OBJECT (technical: api-architect, sre-engineer). The full validated triage is preserved at
`<session>/files/step8-review-triage.md`.

### Triage outcome

| Finding | Severity | Cohort | Disposition |
|---|---|---|---|
| **R1**: API routes raise plain `HTTPException` instead of RFC 7807 Problem Details | HIGH | api-architect (technical) | **APPLIED** — `evidence_pack.py` 404 path now returns `application/problem+json` per RFC 7807; convention bound by api-architect.agent.md and the spec-037 OpenAPI contract. |
| **R2**: CI gate App Insights metric emission is a placeholder `echo` step | HIGH | sre-engineer (technical) | **DEFERRED** — partial-merit: the gate logic itself executes (`python -m evidence_pack_gate` on line 399 of `ci.yml`); only the App Insights telemetry export is placeholder pending `AMA_GATE_AI_CONNECTION_STRING` secret wiring. This deferral was pre-authorised by the orchestrator at implementation time and is bound to **Step 9 (`azd up` redeploy)** when the secret lands in branch-protected scope. CI comment tightened to make the deferral explicit. |
| **R3**: Adoption Roadmap LGA waves under-cover MEMP / evac-centre / vulnerable-persons workflows | MEDIUM | local-government / volunteer / community-ngos (sectors) | **DEFERRED** — minor content polish; queued for v1.1 of the Adoption Roadmap artefact. Does not block v1 publication (artefact still validates against schema). |
| **R4**: Wave-03 omits explicit "federal responder coordination" appendix | MEDIUM | nema (commonwealth) | **DEFERRED** — same as R3. |
| **R5**: One Executive KPI lagging row's source-of-truth is self-referential to the surface | LOW | incident-commander / executive-leader / observer-auditor (operational) | **DEFERRED** — wording polish for v1.1. |
| **R6**: Playwright e2e missing for `/governance/executive` route | MEDIUM | qa-test-engineer (technical) | **REJECTED** — `apps/web/tests/e2e/spec-037/governance-executive.spec.ts` exists; reviewer false-positive (searched in `_components/__tests__/` only). |
| **R7**: axe-core page scan + 400% zoom + high-contrast missing | MEDIUM | accessibility-tester (technical) | **REJECTED** — `apps/web/tests/e2e/spec-037/axe.setup.ts` exists alongside the e2e spec. Same false-positive as R6. |
| **R8**: Executive page severity grouping not explicit | LOW | ux-designer (technical) | **DEFERRED** — v1.1 polish. |
| **R9**: CI gate has no explicit kill-switch / hotfix bypass | LOW | chaos-engineer (technical) | **DEFERRED** — v1.1 polish; current gate is fail-fast which is intentional for v1. |

**No new functional requirements (FR-039+) or success criteria (SC-012+) introduced.**
The single APPLIED finding (R1) is an implementation-quality fix to honour an
**already-existing convention** stated in `api-architect.agent.md` and the spec-037
OpenAPI contract — it does NOT change spec requirements, so the orchestrator skipped
the full clarify→checklist→plan→tasks loop and applied the fix directly per the
"amendment is implementation polish" pragmatic rule. R2 documentation tightening is
likewise non-requirements-altering. Cohort review CYCLE-1 is **complete**; no further
loops triggered.

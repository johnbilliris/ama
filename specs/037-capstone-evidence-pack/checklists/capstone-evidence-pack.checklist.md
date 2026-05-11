# Capstone Evidence Pack — Reviewer Verification Checklist

**Feature**: `037-capstone-evidence-pack`
**Spec**: `specs/037-capstone-evidence-pack/spec.md`
**Audience**: Reviewer evaluating the AMA capstone submission against the Azure Master Architect Program rubric (`AMA_Rubric_Asia.md`)
**Time budget**: ≤ 10 minutes per artefact (≤ 60 minutes total)
**Created**: 2026-05-11
**Authority sources**:

- Constitution v1.2.0 — `.specify/memory/constitution.md` (NN-1 Human-in-the-loop, NN-2 AU residency + Foundry carve-out, NN-3 Privacy by design, NN-4 Interoperability, NN-5 Graceful degradation, Quality Gates incl. Lessons Management)
- AIDR corpus — `docs/corpus/aidr/` (Incident Management 2023, PI&W 2021, AWS Companion 2022, Evacuation Planning 2023, Community Recovery 2018, EM Arrangements 2023, M&E Framework, Outcomes Indicators 2020)
- Capstone brief — `capstone.md` (5 success criteria, lines 31–36)
- Prior closure specs — 003, 015, 021, 028, 030, 032, 035, 036-foundry-rag-grounding, 036-sim-agent-extend
- Resolved clarifications — FR-021, FR-024, FR-037, FR-038
- Spec success criteria — SC-001 … SC-011

**Conventions**: `[ ]` = unchecked. Each item cites the FR-### / SC-### / authority it verifies. Items are testable (yes/no) — no subjective judgement required.

---

## Section 1 — Systematic Risk Register (artefact 1)

Rubric gap closed: **Mandatory — Risks & Tradeoffs**.

- [ ] CHK001 — `docs/risk-register/index.md` exists, is version-controlled, and is reachable from `docs/governance-hub/index.md`. *(FR-002, FR-013)*
- [ ] CHK002 — At least one risk row exists for each of the six categories: Platform, AI, Operational, Jurisdictional, Data, Supply-chain. *(FR-010, US1 Acceptance #1)*
- [ ] CHK003 — Every risk row passes schema validation in CI (no schema-validation failures in the latest pipeline run). *(FR-009, SC-002)*
- [ ] CHK004 — Every risk row carries: ID, title, category, description, likelihood (1–5), consequence (1–5), inherent score, treatment, named-role owner, residual likelihood/consequence/score, next review date, back-citations. *(FR-011, US1 Acceptance #2)*
- [ ] CHK005 — `docs/risk-register/RISK-AOAI-001.md` (the original 3 AI-only risks) is preserved, validates under the new schema, and is not deleted or rewritten in place. *(FR-012)*
- [ ] CHK006 — The roll-up `index.md` is sorted by residual score (highest first) and any row whose `next review date` is in the past is flagged "review overdue" with a counter. *(FR-013, US1 Acceptance #3)*
- [ ] CHK007 — At least one row references the Foundry carve-out (NN-2) — i.e., a risk row covers AU-residency exception handling for Azure AI Foundry RAG components. *(NN-2; cross-cuts FR-024 RAI scope)*
- [ ] CHK008 — At least one row covers each AIDR-aligned operational domain present in scope: Incident Management (AIDR 2023), Public Information & Warnings (AIDR 2021), Evacuation Planning (AIDR 2023), Community Recovery (AIDR 2018), EM Arrangements (AIDR 2023). *(`docs/corpus/aidr/`)*
- [ ] CHK009 — Every row's back-citation set resolves under the CI link-checker (zero broken links). *(FR-008, SC-002)*
- [ ] CHK010 — Top 10 portfolio risks (by residual score) are answerable in ≤ 5 minutes from `index.md` alone, without opening any spec. *(SC-001)*
- [ ] CHK011 — No row has been retroactively edited; corrections appear as new dated revision rows preserving the prior value. *(FR-005, NN-1 append-only audit)*
- [ ] CHK012 — Register metadata block exposes machine-readable `manual_row_count`, `total_row_count`, `manual_row_ratio`. *(FR-037)*
- [ ] CHK013 — Either `manual_row_ratio ≤ 0.5` OR a complete `auditor_signoff` block (`name, role, signoff_date_utc, basis`) is present and the `basis` cites an AIDR/ISO/NIST framework. *(FR-038, SC-011)*
- [ ] CHK014 — Register satisfies the dynamic, schema-bound, archiveable register requested by `operational/risk-manager.agent.md` (likelihood × consequence matrix renderable). *(FR-014)*
- [ ] CHK015 — Register cites back into existing specs (003, 015, 021, 028, 030, 032, 035, 036×2) by spec number and section heading; no risk row duplicates spec content beyond context. *(FR-003)*

---

## Section 2 — Adoption Roadmap (artefact 2)

Rubric gap closed: **Differentiator — Adoption Roadmap**.

- [ ] CHK016 — `docs/governance-hub/adoption-roadmap/roadmap.md` exists, is version-controlled, and is reachable from `docs/governance-hub/index.md`. *(FR-002, analyser I2)*
- [ ] CHK017 — Wave sequencing is: state lead agencies → local government → utilities → transport → volunteer/NGO → Commonwealth (informed by the 58-persona sector synthesis). *(FR-015)*
- [ ] CHK018 — All eight Australian jurisdictions plus Commonwealth appear in at least one wave, each with a named lead agency and ≥ 1 readiness gate. *(FR-018, SC-003, US2 Acceptance #1)*
- [ ] CHK019 — Every wave specifies: cohort, lead agency, readiness gates, training/exercise cadence, change-management artefacts, decommission/rollback criteria. *(FR-016)*
- [ ] CHK020 — Training/exercise cadence cites existing capabilities in specs 007, 024, 026 and introduces no new tooling. *(FR-016, US2 Acceptance #2)*
- [ ] CHK021 — Decommission/rollback criteria explicitly preserve life-safety defaults from the constitution and degrade to manual operations without data loss. *(FR-017, NN-5 graceful degradation, US2 Acceptance #3)*
- [ ] CHK022 — Where two jurisdictions claim the same wave but readiness gates are unmet for one, gating is by readiness (not political sequencing) and the deviation is documented. *(Edge case "Conflicting jurisdiction sequencing")*
- [ ] CHK023 — Each wave references at least one AIDR-aligned exercise/M&E loop (AIDR M&E Framework or AIDR Outcomes Indicators 2020). *(`docs/corpus/aidr/`)*
- [ ] CHK024 — Lessons-management workflow (Constitution Quality Gates) feeds explicitly back into roadmap revisions — i.e., a named loop from post-exercise lessons to the next wave's readiness gates. *(Constitution v1.2.0 Quality Gates — Lessons Management)*
- [ ] CHK025 — Roadmap link-check passes in CI (zero broken back-citations). *(FR-008, SC-002)*
- [ ] CHK026 — Roadmap rows are append-only; revisions to a wave appear as dated new rows preserving the prior version. *(FR-005, NN-1)*
- [ ] CHK027 — Roadmap metadata block exposes `manual_row_count`, `total_row_count`, `manual_row_ratio`. *(FR-037)*
- [ ] CHK028 — Either `manual_row_ratio ≤ 0.5` OR a complete `auditor_signoff` block with AIDR/ISO/NIST `basis` is present. *(FR-038, SC-011)*
- [ ] CHK029 — Roadmap cites back into existing specs (no duplication beyond context). *(FR-003)*

---

## Section 3 — Executive KPI Surface (artefact 3)

Rubric gap closed: **Differentiator — KPI Instrumentation**.

- [ ] CHK030 — `docs/governance-hub/executive-kpi/surface.md` AND `docs/governance-hub/executive-kpi/surface.json` AND a read-only page at `apps/web/src/app/governance/executive/` all exist. *(FR-021, analyser I1)*
- [ ] CHK031 — Each of the five capstone success criteria (`capstone.md` lines 31–36) maps to ≥ 1 leading and ≥ 1 lagging KPI. *(FR-019, SC-004, US3 Acceptance #1)*
- [ ] CHK032 — Every KPI row specifies: owner, refresh cadence, target, threshold/alert band, source-of-truth link, and the scattered surfaces it consolidates. *(FR-020, SC-004)*
- [ ] CHK033 — The scattered-surface consolidation list covers all six sources named in FR-020 (`governance-dashboard.md`, `slo.md`, `metrics-catalogue.md`, specs 015, 021, 030). *(FR-020)*
- [ ] CHK034 — Every superseded scattered surface carries a deprecation banner pointing to the consolidated KPI surface. *(FR-022, US3 Acceptance #3)*
- [ ] CHK035 — The `/governance/executive/` page reuses the existing governance shell, `PersonaWorkspace`, and audit-row read primitives from spec 035; no new chart libraries, no new UI primitives, no new infra components are added. *(FR-021, SC-009, US3 Acceptance #2)*
- [ ] CHK036 — The page surfaces the per-artefact `manual_row_ratio` for all five artefacts at the top of the surface. *(FR-021, FR-037)*
- [ ] CHK037 — When upstream telemetry (App Insights / Cosmos audit) is unavailable, the page renders "stale as of <timestamp>" rather than blanking or rendering as fresh. *(FR-023, NN-5 graceful degradation, Edge case "Degraded telemetry")*
- [ ] CHK038 — All KPI persistence resides in AU regions; no source-of-truth link points to a non-AU sink. *(NN-2 AU residency)*
- [ ] CHK039 — KPI rows pass schema validation and link-check in CI. *(FR-008, FR-009, SC-002)*
- [ ] CHK040 — An Executive Leader can determine on-track / at-risk status against all five capstone metrics from this single page in ≤ 2 minutes. *(SC-008)*
- [ ] CHK041 — KPI surface metadata exposes `manual_row_count`, `total_row_count`, `manual_row_ratio`; either ratio ≤ 0.5 or a complete `auditor_signoff` block is present. *(FR-037, FR-038, SC-011)*
- [ ] CHK042 — Surface cites back into existing specs (015, 021, 030, 035) by section heading; no duplication beyond context. *(FR-003)*

---

## Section 4 — Responsible AI Register (artefact 4)

Rubric gap closed: **Differentiator — Responsible AI**.

- [ ] CHK043 — `docs/governance-hub/rai-register/responsible-ai-register.md` AND `docs/governance-hub/rai-register/responsible-ai-register.json` exist, version-controlled and reachable from `docs/governance-hub/index.md`. *(FR-002, FR-029, analyser I3)*
- [ ] CHK044 — Register includes one row for **each** of: the 5 specialist sub-agents (specs 008–012), the simulation telemetry-injection agent (`036-sim-agent-extend`), the LLM-eval framework (spec 030), the Foundry RAG client (`036-foundry-rag-grounding`). *(FR-024, SC-005)*
- [ ] CHK045 — The simulation telemetry-injection agent row is **complete** across all 4 framework columns × 8 principle dimensions (the simulation watermark / `[SIMULATION]` chat-receipt prefix do NOT reduce RAI obligations). *(FR-024 clarification, `036-sim-agent-extend` FR-066)*
- [ ] CHK046 — Every row populates four framework columns: Australia's 8 AI Ethics Principles, ISO/IEC 42001, ISO/IEC 23894, NIST AI RMF (Govern/Map/Measure/Manage). *(FR-025, US4 Acceptance #1)*
- [ ] CHK047 — Every row populates eight principle dimensions: human oversight, fairness, accountability, transparency, privacy, safety, contestability, reliability. *(FR-026)*
- [ ] CHK048 — Zero blank cells; any non-applicable cell carries an explicit "not-applicable + justification". *(FR-027, SC-005)*
- [ ] CHK049 — Every row cites back into spec 030's existing evaluation outputs and the relevant agent spec (008–013, 030, 036×2); no row triggers or re-runs an evaluation. *(FR-028, US4 Acceptance #2)*
- [ ] CHK050 — Foundry RAG client row references the NN-2 Foundry carve-out for AU residency and the carve-out is current (not superseded). *(NN-2, FR-024)*
- [ ] CHK051 — Human-oversight cells reference NN-1 (Human-in-the-loop) and name the human approval/escalation point per agent. *(NN-1)*
- [ ] CHK052 — Privacy cells reference NN-3 (Privacy by design) and name the data-minimisation/PI&W (AIDR 2021) controls applied. *(NN-3, AIDR PI&W 2021)*
- [ ] CHK053 — Markdown + JSON pair are byte-stable across regenerations and suitable for archiving alongside `docs/aidr/`. *(FR-029, US4 Acceptance #3)*
- [ ] CHK054 — Register schema validation and link-check pass in CI. *(FR-008, FR-009, SC-002)*
- [ ] CHK055 — Register metadata block exposes `manual_row_count`, `total_row_count`, `manual_row_ratio`; either ratio ≤ 0.5 OR a complete `auditor_signoff` block (with AIDR/ISO/NIST `basis`) is present — RAI is the artefact most likely to exercise the auditor-signoff override path. *(FR-037, FR-038, SC-011)*
- [ ] CHK056 — Governance-discovery instructions (`.github/instructions/governance-discovery.instructions.md`) require a new RAI row before any future agent (e.g., a hypothetical spec 038 agent) is allowed to ship. *(FR-006, Edge case "AI component added later")*
- [ ] CHK057 — Register cites existing specs by section heading; no duplication beyond context. *(FR-003)*

---

## Section 5 — Feature-to-Value Ledger + Decision/Tradeoff Log (artefact 5)

Rubric gap closed: **Mandatory — Business Value Mapping**, plus depth on **Mandatory — Risks & Tradeoffs**.

- [ ] CHK058 — `specs/shared/feature-value-ledger.md` AND `docs/decisions/tradeoff-log.md` exist, version-controlled and reachable from `docs/governance-hub/index.md`. *(FR-002)*
- [ ] CHK059 — Every merged spec 001–036 appears as a row in the Feature-Value Ledger; specs not contributing to a capstone metric are tagged "delivery-hygiene". *(FR-030, SC-006, US5 Acceptance #1)*
- [ ] CHK060 — Every contributing row names: capstone metric, magnitude of contribution, direction of contribution, residual gap-to-target. *(FR-031)*
- [ ] CHK061 — Every metric with residual gap > 0 names at least one open follow-up (existing spec, issue, or roadmap wave). *(FR-033, US5 Acceptance #3)*
- [ ] CHK062 — The Ledger is the inverse, feature-centric counterpart to `specs/shared/capstone-metric-trace.md` and cross-links to it bidirectionally. *(FR-034)*
- [ ] CHK063 — Spec 037 itself is tagged "non-capstone-critical-path / delivery-hygiene" in `specs/shared/capstone-metric-trace.md` per `028-capstone-alignment` FR-020. *(FR-007, SC-010)*
- [ ] CHK064 — Every ADR currently under `docs/aidr/decisions/` appears as a row in the Tradeoff Log. *(FR-032, SC-006, US5 Acceptance #2)*
- [ ] CHK065 — Every Tradeoff Log row names: bounding feature(s), alternatives considered, rationale for the chosen path. *(FR-032)*
- [ ] CHK066 — The Tradeoff Log explicitly logs the four cross-sector tensions: speed vs. legality, automation vs. command authority, local autonomy vs. cross-jurisdiction standardisation, operational visibility vs. privacy/credentialing. *(FR-036)*
- [ ] CHK067 — Ledger and Log link-check and schema-check pass in CI. *(FR-008, FR-009, SC-002)*
- [ ] CHK068 — Ledger and Log rows are append-only; corrections appear as new dated revision rows. *(FR-005, NN-1)*
- [ ] CHK069 — Ledger metadata block exposes `manual_row_count`, `total_row_count`, `manual_row_ratio`; either ratio ≤ 0.5 OR a complete `auditor_signoff` block is present. *(FR-037, FR-038, SC-011)*
- [ ] CHK070 — Ledger and Log are regenerable from source (specs + ADRs) without manual transcription where source data exists. *(FR-035)*

---

## Section 6 — Cross-cutting (publication CI gates, AU residency, audit, Foundry carve-out, lessons loop)

- [ ] CHK071 — All five artefacts pass the artefact-publication CI check in the latest pipeline run (schema, link, manual-cap, auditor-signoff). *(FR-008, FR-009, FR-038)*
- [ ] CHK072 — All five artefacts are version-controlled under `docs/` or `specs/shared/` (no ephemeral storage) and are referenced from `docs/governance-hub/index.md`. *(FR-001, FR-002)*
- [ ] CHK073 — Spec 037 introduced **zero** modifications to `.specify/memory/constitution.md`. *(FR-004)*
- [ ] CHK074 — All persisted artefact data resides in AU regions; no JSON sink, telemetry source, or storage account referenced by any artefact is hosted outside AU. *(NN-2 AU residency)*
- [ ] CHK075 — The Foundry carve-out (NN-2) is documented and current in **both** the Risk Register (Section 1) and the Responsible AI Register (Section 4). *(NN-2, FR-024)*
- [ ] CHK076 — Append-only audit trail covers artefact creation and every subsequent revision (no in-place edits to published rows on any of the five artefacts). *(NN-1 Human-in-the-loop, FR-005, Edge case "Append-only audit conflict")*
- [ ] CHK077 — Lessons-management workflow (Constitution Quality Gates) is wired so post-exercise / post-incident lessons are captured and loop back into the Adoption Roadmap's next-wave readiness gates. *(Constitution v1.2.0 Quality Gates — Lessons Management; FR-016)*
- [ ] CHK078 — All four resolved clarifications (FR-021 hosting, FR-024 RAI scope, FR-037 manual provenance, FR-038 manual cap) are reflected in the published artefacts. *(Clarifications session 2026-05-11)*
- [ ] CHK079 — Each artefact carries a `provenance: automated|manual` tag on every row per FR-037; manual rows additionally carry `owner` (named role), `review_cadence` (`quarterly|monthly|post-incident`), and `automation_target`. *(FR-037)*
- [ ] CHK080 — All eleven success criteria SC-001 … SC-011 are independently verifiable from the published artefacts (no SC requires reading source code or specs to evaluate). *(SC-001 … SC-011)*
- [ ] CHK081 — Zero net-new dashboards, chart libraries, App Service plans, storage accounts, or monitoring workspaces were introduced by spec 037. *(SC-009, Out of Scope)*
- [ ] CHK082 — Governance-discovery instructions (`.github/instructions/governance-discovery.instructions.md`) are honoured for every governance-constraint file produced or modified. *(FR-006)*
- [ ] CHK083 — Spec 016 (Demo) and any FinOps cost dashboard are not referenced as in-scope deliverables anywhere in the artefacts. *(Out of Scope, Assumptions)*
- [ ] CHK084 — A reviewer can complete this checklist in ≤ 60 minutes (≤ 10 minutes per artefact + 10 minutes cross-cutting) without opening any spec other than `037-capstone-evidence-pack/spec.md`. *(SC-001, SC-008; capstone-brief reviewer-time intent)*

---

## Traceability Table

| Item | Spec FR / SC | Rubric criterion closed | Authority source |
|------|--------------|--------------------------|-------------------|
| CHK001 | FR-002, FR-013 | Mandatory: Risks & Tradeoffs | Spec §FR-002 |
| CHK002 | FR-010, US1 #1 | Mandatory: Risks & Tradeoffs | Spec §FR-010 |
| CHK003 | FR-009, SC-002 | Mandatory: Risks & Tradeoffs | Spec §FR-009 |
| CHK004 | FR-011, US1 #2 | Mandatory: Risks & Tradeoffs | Spec §FR-011 |
| CHK005 | FR-012 | Mandatory: Risks & Tradeoffs | `docs/risk-register/RISK-AOAI-001.md` |
| CHK006 | FR-013, US1 #3 | Mandatory: Risks & Tradeoffs | Spec §FR-013 |
| CHK007 | FR-024 (cross), NN-2 | Mandatory: Risks & Tradeoffs | Constitution v1.2.0 NN-2 |
| CHK008 | FR-010 | Mandatory: Risks & Tradeoffs | AIDR corpus (`docs/corpus/aidr/`) |
| CHK009 | FR-008, SC-002 | Mandatory: Risks & Tradeoffs | Spec §FR-008 |
| CHK010 | SC-001 | Mandatory: Risks & Tradeoffs | Spec §SC-001 |
| CHK011 | FR-005 | Mandatory: Risks & Tradeoffs | Constitution v1.2.0 NN-1 |
| CHK012 | FR-037 | Mandatory: Risks & Tradeoffs | Spec §FR-037 |
| CHK013 | FR-038, SC-011 | Mandatory: Risks & Tradeoffs | Spec §FR-038 |
| CHK014 | FR-014 | Mandatory: Risks & Tradeoffs | `operational/risk-manager.agent.md` |
| CHK015 | FR-003 | Mandatory: Risks & Tradeoffs | Spec §FR-003 |
| CHK016 | FR-002 | Differentiator: Adoption Roadmap | Spec §FR-002 |
| CHK017 | FR-015 | Differentiator: Adoption Roadmap | Spec §FR-015 |
| CHK018 | FR-018, SC-003, US2 #1 | Differentiator: Adoption Roadmap | Spec §FR-018 |
| CHK019 | FR-016 | Differentiator: Adoption Roadmap | Spec §FR-016 |
| CHK020 | FR-016, US2 #2 | Differentiator: Adoption Roadmap | Specs 007, 024, 026 |
| CHK021 | FR-017, US2 #3 | Differentiator: Adoption Roadmap | Constitution v1.2.0 NN-5 |
| CHK022 | Edge case | Differentiator: Adoption Roadmap | Spec §Edge Cases |
| CHK023 | FR-016 | Differentiator: Adoption Roadmap | AIDR M&E Framework, AIDR Outcomes Indicators 2020 |
| CHK024 | FR-016 | Differentiator: Adoption Roadmap | Constitution v1.2.0 Quality Gates — Lessons Management |
| CHK025 | FR-008, SC-002 | Differentiator: Adoption Roadmap | Spec §FR-008 |
| CHK026 | FR-005 | Differentiator: Adoption Roadmap | Constitution v1.2.0 NN-1 |
| CHK027 | FR-037 | Differentiator: Adoption Roadmap | Spec §FR-037 |
| CHK028 | FR-038, SC-011 | Differentiator: Adoption Roadmap | Spec §FR-038 |
| CHK029 | FR-003 | Differentiator: Adoption Roadmap | Spec §FR-003 |
| CHK030 | FR-021 | Differentiator: KPI Instrumentation | Spec §FR-021 |
| CHK031 | FR-019, SC-004, US3 #1 | Differentiator: KPI Instrumentation | `capstone.md` lines 31–36 |
| CHK032 | FR-020, SC-004 | Differentiator: KPI Instrumentation | Spec §FR-020 |
| CHK033 | FR-020 | Differentiator: KPI Instrumentation | Specs 015, 021, 030 + governance-hub |
| CHK034 | FR-022, US3 #3 | Differentiator: KPI Instrumentation | Spec §FR-022 |
| CHK035 | FR-021, SC-009, US3 #2 | Differentiator: KPI Instrumentation | Spec 035 (`PersonaWorkspace`) |
| CHK036 | FR-021, FR-037 | Differentiator: KPI Instrumentation | Spec §FR-021 |
| CHK037 | FR-023, Edge case | Differentiator: KPI Instrumentation | Constitution v1.2.0 NN-5 |
| CHK038 | NN-2 | Differentiator: KPI Instrumentation | Constitution v1.2.0 NN-2 |
| CHK039 | FR-008, FR-009, SC-002 | Differentiator: KPI Instrumentation | Spec §FR-008/FR-009 |
| CHK040 | SC-008 | Differentiator: KPI Instrumentation | Spec §SC-008 |
| CHK041 | FR-037, FR-038, SC-011 | Differentiator: KPI Instrumentation | Spec §FR-037/FR-038 |
| CHK042 | FR-003 | Differentiator: KPI Instrumentation | Spec §FR-003 |
| CHK043 | FR-002, FR-029 | Differentiator: Responsible AI | Spec §FR-002/FR-029 |
| CHK044 | FR-024, SC-005 | Differentiator: Responsible AI | Specs 008–012, 030, 036×2 |
| CHK045 | FR-024 clarification | Differentiator: Responsible AI | `036-sim-agent-extend` FR-066 |
| CHK046 | FR-025, US4 #1 | Differentiator: Responsible AI | AU AI Ethics, ISO/IEC 42001, ISO/IEC 23894, NIST AI RMF |
| CHK047 | FR-026 | Differentiator: Responsible AI | Spec §FR-026 |
| CHK048 | FR-027, SC-005 | Differentiator: Responsible AI | Spec §FR-027 |
| CHK049 | FR-028, US4 #2 | Differentiator: Responsible AI | Spec 030 |
| CHK050 | FR-024, NN-2 | Differentiator: Responsible AI | Constitution v1.2.0 NN-2 (Foundry carve-out) |
| CHK051 | NN-1 | Differentiator: Responsible AI | Constitution v1.2.0 NN-1 |
| CHK052 | NN-3 | Differentiator: Responsible AI | Constitution v1.2.0 NN-3; AIDR PI&W 2021 |
| CHK053 | FR-029, US4 #3 | Differentiator: Responsible AI | `docs/aidr/` |
| CHK054 | FR-008, FR-009, SC-002 | Differentiator: Responsible AI | Spec §FR-008/FR-009 |
| CHK055 | FR-037, FR-038, SC-011 | Differentiator: Responsible AI | Spec §FR-037/FR-038 |
| CHK056 | FR-006, Edge case | Differentiator: Responsible AI | `.github/instructions/governance-discovery.instructions.md` |
| CHK057 | FR-003 | Differentiator: Responsible AI | Spec §FR-003 |
| CHK058 | FR-002 | Mandatory: Business Value Mapping | Spec §FR-002 |
| CHK059 | FR-030, SC-006, US5 #1 | Mandatory: Business Value Mapping | Spec §FR-030 |
| CHK060 | FR-031 | Mandatory: Business Value Mapping | Spec §FR-031 |
| CHK061 | FR-033, US5 #3 | Mandatory: Business Value Mapping | Spec §FR-033 |
| CHK062 | FR-034 | Mandatory: Business Value Mapping | `specs/shared/capstone-metric-trace.md` |
| CHK063 | FR-007, SC-010 | Mandatory: Business Value Mapping | `028-capstone-alignment` FR-020 |
| CHK064 | FR-032, SC-006, US5 #2 | Mandatory: Risks & Tradeoffs (depth) | `docs/aidr/decisions/` |
| CHK065 | FR-032 | Mandatory: Risks & Tradeoffs (depth) | Spec §FR-032 |
| CHK066 | FR-036 | Mandatory: Risks & Tradeoffs (depth) | Spec §FR-036 |
| CHK067 | FR-008, FR-009, SC-002 | Mandatory: Business Value Mapping | Spec §FR-008/FR-009 |
| CHK068 | FR-005 | Mandatory: Business Value Mapping | Constitution v1.2.0 NN-1 |
| CHK069 | FR-037, FR-038, SC-011 | Mandatory: Business Value Mapping | Spec §FR-037/FR-038 |
| CHK070 | FR-035 | Mandatory: Business Value Mapping | Spec §FR-035 |
| CHK071 | FR-008, FR-009, FR-038 | Cross-cutting (all rubric) | Spec §FR-008/FR-009/FR-038 |
| CHK072 | FR-001, FR-002 | Cross-cutting (all rubric) | Spec §FR-001/FR-002 |
| CHK073 | FR-004 | Cross-cutting (all rubric) | Constitution v1.2.0 |
| CHK074 | NN-2 | Cross-cutting (all rubric) | Constitution v1.2.0 NN-2 |
| CHK075 | NN-2, FR-024 | Cross-cutting (Risks + RAI) | Constitution v1.2.0 NN-2 (Foundry carve-out) |
| CHK076 | NN-1, FR-005, Edge case | Cross-cutting (all rubric) | Constitution v1.2.0 NN-1 |
| CHK077 | Quality Gates, FR-016 | Cross-cutting (Adoption Roadmap) | Constitution v1.2.0 Quality Gates — Lessons Management |
| CHK078 | FR-021, FR-024, FR-037, FR-038 | Cross-cutting (all rubric) | Spec §Clarifications 2026-05-11 |
| CHK079 | FR-037 | Cross-cutting (all rubric) | Spec §FR-037 |
| CHK080 | SC-001 … SC-011 | Cross-cutting (all rubric) | Spec §Success Criteria |
| CHK081 | SC-009 | Cross-cutting (KPI / Adoption) | Spec §SC-009, §Out of Scope |
| CHK082 | FR-006 | Cross-cutting (all rubric) | `.github/instructions/governance-discovery.instructions.md` |
| CHK083 | Out of Scope | Cross-cutting (all rubric) | Spec §Out of Scope, §Assumptions |
| CHK084 | SC-001, SC-008 | Cross-cutting (reviewer time) | `capstone.md` |

---

**End of checklist.** Each `/speckit.checklist` invocation appends to or creates a new file under `specs/037-capstone-evidence-pack/checklists/`; this file is the v1 reviewer verification checklist for the Capstone Evidence Pack.

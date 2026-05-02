# Validation Checklist: Web Application Capstone Coverage Validation

**Purpose**: Workflow execution gate covering the 9-step speckit lifecycle (specify → clarify → checklist → plan → tasks → analyze → implement → review → deploy) plus the 85-agent review for `034-webapp-capstone-coverage`. This checklist is the parent agent's tick-list as it drives the spec from clarified-spec to `Capstone Ready`.
**Created**: 2026-05-02
**Branch**: `034-webapp-capstone-coverage` @ `350e1db`
**Feature**: [spec.md](../spec.md)
**Companion**: [requirements.md](./requirements.md) (spec-quality gate — already passing)

## How to use

- Tick `- [x]` as each gate is satisfied during workflow execution.
- IDs are stable; the User Story 5 iteration-loop runner (FR-024) and the gap-register state machine (FR-005) reference them.
- Items cite: spec sections (`[Spec §FR-XXX]` / `[SC-XXX]` / `[ASM-XXX]` / `[OOS-XXX]`), pass-1 / pass-2 clarifications (`[Clarif Q#]`), constitution clauses (`[Const §X]`), and downstream specs (`[spec-001]`, `[spec-017]`, `[spec-028]`, `[spec-029]`).
- A `[Gap]` marker means the item asks whether a future-state artefact exists yet (e.g. `coverage-trace.md` is emitted by the suite at implement-time, not at spec-time).
- A `[Veto]` marker calls out an operational-panel veto domain per ASM-006 / Clarif Q13.

---

## Section A — 9-Step Workflow Phase Gates

### A1. Phase 1 — `/speckit.specify` exit gate

- [ ] CHK001 Spec carries zero `[NEEDS CLARIFICATION]` markers and all mandatory sections are populated [requirements.md, Spec §Requirements]
- [ ] CHK002 Spec scopes WHAT (Playwright as the executable-spec surface) without leaking HOW (config / runner / page-object choices stay deferred to plan) [Spec Notes, requirements.md]
- [ ] CHK003 The 68-persona inventory (10 operational + 58 sector/jurisdiction) is enumerated and matches the cited input files [Spec §Cited inputs, FR-002]
- [ ] CHK004 AU-only scope is justified by ASM-005 (Asia deferral) and OOS-001 (PH/JP/BD personas/hazards/language packs deferred) [ASM-005, OOS-001]

### A2. Phase 2 — `/speckit.clarify` exit gate

- [ ] CHK005 Pass-1 clarifications Q1–Q5 are codified in spec body (contractual SC budgets, language baseline, Foundry triple-assertion, CI wall-clock cap, max-3-cycles + rollback) [Spec §Clarifications pass 1]
- [ ] CHK006 Pass-2 clarifications Q6–Q14 close all five pass-1 follow-ups and surface no new open ambiguities [Spec §Clarifications pass 2]
- [ ] CHK007 FR-027 (regression rollback) was added during clarifications and is referenced wherever FR-024 is referenced [Spec §FR-027, Clarif Q5]
- [ ] CHK008 ASM-006 (85-agent panel mechanics, ≥2/3 majority, operational veto on safety-critical clauses) and ASM-011 (fixture RBAC inheritance) are codified [ASM-006, ASM-011, Clarif Q13]

### A3. Phase 3 — `/speckit.checklist` exit gate (this artefact)

- [ ] CHK009 Both `requirements.md` (spec-quality gate) and `validation.md` (workflow gate) live under `specs/034-webapp-capstone-coverage/checklists/` [this file]
- [ ] CHK010 Every CHK item carries at least one traceability reference (spec section, FR, SC, ASM, OOS, constitution clause, or `[Gap]` marker) [self-test]
- [ ] CHK011 Validation checklist is committed on branch `034-webapp-capstone-coverage` before `/speckit.plan` is invoked [Workflow contract]

### A4. Phase 4 — `/speckit.plan` entry gate

- [ ] CHK012 Plan phase translates contractual SC budgets (≤ 2 min warning reach; ≤ 5/15/30 min L1/L2/L3 signal-to-action; ≥ 24 h evac lead; ≤ 7/12 click logistics; ≥ 0.30 economic-loss reduction; ≤ 30 min dev / ≤ 45 min CI wall-clock) into engineering targets without relaxing them [SC-001..SC-005, SC-011, ASM-004, ASM-010]
- [ ] CHK013 Plan records canonical BCP-47 identifier selection for additional CALD / ATSI variants in `research.md` (deferred from spec per Clarif Q2) [FR-014, Clarif Q2]
- [ ] CHK014 Plan records SC-005's `baseline_loss` / `projected_loss` capture mechanism in `bootstrap_seed_data()` per Sendai Indicator C and spec-015 SC-CAP-015-005 [SC-005, Clarif Q7, spec-015]
- [ ] CHK015 Plan picks Playwright config, runner shape, and CI shard strategy that meets the ≤ 30 min dev / ≤ 45 min `ubuntu-latest` budget; if breached, suite is sharded (never relaxed) [SC-011, Clarif Q4]
- [ ] CHK016 Plan documents the test-fixture impersonation mechanism (no fixture-only identities; RBAC strictly inherited from `bootstrap_seed_data()`) [ASM-011, FR-021, OOS-007]
- [ ] CHK017 Plan records `coverage-trace.md` linkage rule to `specs/shared/capstone-metric-trace.md` AU-v1 cells and the `Validated → Unresolved` flip behaviour on Open/Failing rows [FR-004, Clarif Q12, spec-028]

### A5. Phase 5 — `/speckit.tasks` entry gate

- [ ] CHK018 Tasks include one work item per persona (× 68) producing ≥ 1 Playwright spec each under `tests/e2e/web-coverage/{operational|sectors/<jurisdiction>}` [FR-001, FR-002, Spec §Suite Layout]
- [ ] CHK019 Tasks include one work item per cross-cutting spec (rbac-aiims, cop-refresh-latency, audit-append-only, aws-warning-compliance, evacuation-five-stage, recovery-environments, accessibility-and-multilingual, field-offline-mode, data-sovereignty, span-of-control, simulation-playback, lessons-management) [Spec §Suite Layout, FR-007..FR-018, FR-020]
- [ ] CHK020 Tasks include one work item per capstone outcome under `capstone/outcome-{1..5}-*.spec.ts` covering both mandatory hazards from FR-016 [FR-016, Clarif Q8, Spec §Suite Layout]
- [ ] CHK021 Tasks include one work item per state/territory cross-jurisdiction scenario plus the Commonwealth-bridge (NEMA / COMDISPLAN / DACC / NJCOP) scenario [FR-003, FR-015]

### A6. Phase 6 — `/speckit.analyze` exit gate

- [ ] CHK022 Cross-artefact analysis confirms every persona ID in the 68-inventory has at least one task and one planned spec file [FR-001, FR-002]
- [ ] CHK023 Analyze step verifies every (persona × outcome × hazard) tuple required for FR-016's mandatory hazard pairs has at least one planned Test ID [FR-004, FR-016, Clarif Q8, Clarif Q10]
- [ ] CHK024 Analyze step verifies every constitutional safety-critical clause covered by the operational-panel veto (`Const §I`, `§IV`, NN#1, NN#2, "Public outputs human-reviewed") maps to at least one cross-cutting spec [ASM-006, Clarif Q13] [Veto]
- [ ] CHK025 Analyze step confirms there are no [NEEDS CLARIFICATION] / unresolved ambiguity rows left in spec, plan, or tasks [Spec §Clarifications]
- [ ] CHK026 Analyze step confirms OOS-001..OOS-010 boundaries are not violated by any task or planned uplift [OOS-001..OOS-010]

### A7. Phase 7 — `/speckit.implement` exit gate

- [ ] CHK027 Suite runs against `http://127.0.0.1:3000/` using `bootstrap_seed_data()` with deterministic outputs across 3 consecutive clean runs (no flakes) [FR-021, SC-010]
- [ ] CHK028 `coverage-trace.md` is emitted with one row per (persona × outcome × hazard) and joined `;`-delimited Test IDs where multiple scenarios assert the same tuple [FR-004, Clarif Q10, Clarif Q12]
- [ ] CHK029 `coverage-trace.json` machine-readable companion is emitted alongside the Markdown trace [FR-004]
- [ ] CHK030 `gap-register.md` is emitted with status enum `Open|In-Progress|Closed` and every status change is mirrored to the audit timeline (FR-010) [FR-005, Clarif Q11, Const §IV]
- [ ] CHK031 JUnit XML + JSON trace + screenshot/video on failure are written to `tests/e2e/web-coverage/_artifacts/` [FR-022]
- [ ] CHK032 Persona workspace `/workspaces/[personaId]` resolves for every persona ID; missing routes emit `GAP-WORKSPACE-MISSING` and surface in gap-register [FR-019, FR-005]

### A8. Phase 8 — Review exit gate (85-agent panel)

- [ ] CHK033 Operational panel (10 agents) has reviewed; each meritorious objection (≥ 2/3 of operational panel) is `Closed` in gap-register [ASM-006, Clarif Q13]
- [ ] CHK034 Sector panel (58 agents) has reviewed; each meritorious objection (≥ 2/3 of relevant sector sub-panel) is `Closed` in gap-register [ASM-006, Clarif Q13]
- [ ] CHK035 Technical panel (17 agents) has reviewed; each meritorious objection (≥ 2/3 of technical panel) is `Closed` in gap-register [ASM-006, Clarif Q13]
- [ ] CHK036 Operational-panel domain-veto guarantee was honoured: every ≥ 2/3 objection against `Const §I`, `§IV`, NN#1, NN#2, or "Public outputs human-reviewed" was addressed before any gate flip [ASM-006, Clarif Q13] [Veto]
- [ ] CHK037 Cross-panel disputes (if any) carry recorded project-lead disposition in audit timeline before sign-off [Const §Governance, ASM-006]
- [ ] CHK038 Non-meritorious objections (< 2/3 panel support) are recorded but did not block the gate [ASM-006]

### A9. Phase 9 — Deploy / `Capstone Ready` flip gate

- [ ] CHK039 Every persona (68/68) has ≥ 1 passing scenario [FR-023(a), SC-006]
- [ ] CHK040 Every cross-cutting spec passes on a clean run [FR-023(b), SC-008]
- [ ] CHK041 Every state/territory (8/8) has ≥ 1 passing cross-jurisdiction scenario plus a passing Commonwealth-bridge scenario [FR-023(c), SC-007, FR-003]
- [ ] CHK042 Every capstone outcome (#1..#5) has ≥ 1 traceable passing assertion in `coverage-trace.md` for both mandatory FR-016 hazards [FR-023(d), FR-016]
- [ ] CHK043 Gap register has zero `Open` entries (no `escalated:project-lead`, no `regression_detected` in flight) [FR-023(e), FR-024, FR-027]
- [ ] CHK044 Suite-level signal flipped from `Not Ready` to `Capstone Ready` in the audit timeline; flip event records operator identity, rationale, and source commit SHA [FR-010, Const §IV]

---

## Section B — Persona Coverage Tracking

> Each persona below is ticked when (a) ≥ 1 Playwright scenario passes for that persona, (b) the corresponding `coverage-trace.md` row(s) show `Status = Passing`, and (c) any agent-review objections raised against that persona's scenario are `Closed`. References: [FR-001, FR-002, FR-004, FR-005, FR-019, ASM-006].

### B1. Operational personas (10 — `tests/e2e/web-coverage/operational/`)

- [ ] CHK045 `incident-commander` — workspace + must-do scenario passing; outcome #1 + #2 trace rows present; span-of-control Tier-1 evaluated (positive test) [FR-002, FR-020 Tier-1, Clarif Q9]
- [ ] CHK046 `operations-officer` — workspace + must-do scenario passing; span-of-control Tier-2 evaluated when supervising field supervisors [FR-002, FR-020 Tier-2, Clarif Q9]
- [ ] CHK047 `planning-officer` — workspace + must-do scenario passing; span-of-control suppressed (negative test) [FR-002, FR-020 N/A, Clarif Q9]
- [ ] CHK048 `logistics-officer` — workspace + must-do scenario passing; outcome #4 trace row present; span-of-control Tier-2 evaluated when supervising branch supervisors [FR-002, FR-020 Tier-2, SC-004, Clarif Q9]
- [ ] CHK049 `public-information-officer` — workspace + must-do scenario passing; AWS warning composition with Simplified Chinese + ATSI placeholder asserted [FR-002, FR-011, FR-014, Clarif Q2]
- [ ] CHK050 `field-coordinator` — workspace + must-do scenario passing; offline / queue-and-sync flow exercised [FR-002, FR-017, Const NN#5]
- [ ] CHK051 `resilience-planner` — workspace + must-do scenario passing; PPRR Preparedness phase tagged in trace [FR-002, FR-006]
- [ ] CHK052 `executive-leader` — workspace + must-do scenario passing; cross-jurisdiction COP visibility verified [FR-002, FR-008]
- [ ] CHK053 `observer-auditor` — workspace + must-do scenario passing; audit timeline + lessons report exported [FR-002, FR-010, US4]
- [ ] CHK054 `risk-manager` — workspace + must-do scenario passing; recovery-environment risk register exercised [FR-002, FR-013]

### B2. NSW (6 — `tests/e2e/web-coverage/sectors/nsw/`)

- [ ] CHK055 NSW cross-jurisdiction scenario passing (e.g. NSW RFS → CFA bushfire crossing, or SES-NSW ↔ SES-QLD cyclone-flood) [FR-003, US3 §Acceptance #1]
- [ ] CHK056 `frnsw` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK057 `mrnsw` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK058 `nsw-ambulance` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK059 `nsw-rfs` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK060 `nswpf` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK061 `ses-nsw` — workspace + must-do scenario passing (Watch-and-Act flood per US1 §Acceptance #2) [FR-002, US1 §Acceptance #2]

### B3. VIC (5 — `tests/e2e/web-coverage/sectors/vic/`)

- [ ] CHK062 VIC cross-jurisdiction scenario passing [FR-003]
- [ ] CHK063 `av` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK064 `cfa-vic` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK065 `frv` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK066 `ses-vic` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK067 `vicpol` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]

### B4. QLD (4 — `tests/e2e/web-coverage/sectors/qld/`)

- [ ] CHK068 QLD cross-jurisdiction scenario passing (e.g. tropical-cyclone flooding at QLD/NSW border) [FR-003]
- [ ] CHK069 `qas` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK070 `qfd` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK071 `qps` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]
- [ ] CHK072 `ses-qld` — workspace + must-do scenario passing [FR-002, sector-eastern-input.md]

### B5. SA (5 — `tests/e2e/web-coverage/sectors/sa/`)

- [ ] CHK073 SA cross-jurisdiction scenario passing [FR-003]
- [ ] CHK074 `saas` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK075 `sacfs` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK076 `ses-sa` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK077 `samfs` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK078 `sapol` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]

### B6. WA (3 — `tests/e2e/web-coverage/sectors/wa/`)

- [ ] CHK079 WA cross-jurisdiction scenario passing [FR-003]
- [ ] CHK080 `dfes-wa` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK081 `sja-wa` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK082 `wapol` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]

### B7. TAS (4 — `tests/e2e/web-coverage/sectors/tas/`)

- [ ] CHK083 TAS cross-jurisdiction scenario passing [FR-003]
- [ ] CHK084 `at` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK085 `ses-tas` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK086 `taspol` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]
- [ ] CHK087 `tfs` — workspace + must-do scenario passing [FR-002, sector-southwest-input.md]

### B8. ACT (7 — `tests/e2e/web-coverage/sectors/act/`)

- [ ] CHK088 ACT cross-jurisdiction scenario passing (ACT/NSW border) [FR-003]
- [ ] CHK089 `act-ambulance` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK090 `act-esa` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK091 `act-fr` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK092 `act-policing` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK093 `act-rfs` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK094 `afp` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK095 `ses-act` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]

### B9. NT (5 — `tests/e2e/web-coverage/sectors/nt/`)

- [ ] CHK096 NT cross-jurisdiction scenario passing (e.g. tropical cyclone preparedness) [FR-003]
- [ ] CHK097 `bushfires-nt` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK098 `ntes` — workspace + must-do scenario passing (cyclone preparedness) [FR-002, sector-tc-input.md]
- [ ] CHK099 `ntfrs` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK100 `ntpf` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK101 `sja-nt` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]

### B10. Commonwealth (11 — `tests/e2e/web-coverage/sectors/commonwealth/`)

- [ ] CHK102 Commonwealth-bridge scenario passing: `nema` activates COMDISPLAN, opens NJCOP, requests consequence metrics, asserts logistics-match efficiency proxy linked to outcome #4 [FR-003, FR-015, US1 §Acceptance #3, SC-004]
- [ ] CHK103 ADF DACC request lifecycle scenario passing (state controller → NEMA → DACC A/B/C categorisation → asset arrival → mission close, all in audit timeline) [FR-015, US3 §Acceptance #2]
- [ ] CHK104 `abf` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK105 `adf` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK106 `afp-commonwealth` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK107 `arc` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK108 `asa` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK109 `bom-national` — workspace + must-do scenario passing; earthquake/tsunami AWS warning composition exercised [FR-002, FR-011, FR-016 (eq/tsunami SHOULD)]
- [ ] CHK110 `ga-national` — workspace + must-do scenario passing; tsunami-warning relay exercised [FR-002, FR-011, FR-016 (eq/tsunami SHOULD)]
- [ ] CHK111 `nema` — workspace + must-do scenario passing (covered by CHK102) [FR-002, FR-015]
- [ ] CHK112 `rfds` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK113 `sja-national` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK114 `surf-lifesaving` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]

### B11. Cross-Sector (8 — `tests/e2e/web-coverage/sectors/cross-sector/`)

- [ ] CHK115 `community-ngos` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK116 `health` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK117 `local-government` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK118 `state-government` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK119 `territory-government` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK120 `transport` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK121 `utility` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]
- [ ] CHK122 `volunteer` — workspace + must-do scenario passing [FR-002, sector-tc-input.md]

---

## Section C — Capstone outcomes × FR-016 mandatory hazard pairs

- [ ] CHK123 Outcome #1 (1,000+ lives) — `bushfire` AND `extreme heat` rows passing in `coverage-trace.md`; `capstone/outcome-1-lives-saved.spec.ts` covers both [FR-016, Clarif Q8, SC-001]
- [ ] CHK124 Outcome #2 (50% faster response) — `bushfire` AND `severe storm` rows passing; rapid-onset signal-to-action latency asserted at AIIMS L1/L2 [FR-016, Clarif Q8, SC-002]
- [ ] CHK125 Outcome #3 (24-h earlier evacuation) — `tropical cyclone` AND `riverine flood` rows passing; ≥ 24 h evac-lead-time proxy asserted [FR-016, Clarif Q8, SC-003]
- [ ] CHK126 Outcome #4 (30% logistics efficiency) — `bushfire` AND `tropical cyclone` rows passing; mutual-aid / DACC / COMDISPLAN lifecycle exercised [FR-016, Clarif Q8, SC-004]
- [ ] CHK127 Outcome #5 (30% economic-loss reduction) — `riverine flood` AND `severe storm` rows passing; per-scenario `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30` asserted at response → recovery handover [FR-016, Clarif Q7, Clarif Q8, SC-005]
- [ ] CHK128 `earthquake/tsunami` exercised by ≥ 1 persona suite for AWS warning composition (e.g. `bom-national` / `ga-national`) but NOT mandated as a 2nd hazard for any specific outcome [FR-016, Clarif Q8]

---

## Section D — Constitution gates (cross-cutting specs)

- [ ] CHK129 AIIMS-aligned RBAC enforced on every interactive route; negative tests confirm unauthorised personas are denied [FR-007, Const §II-A] [Veto]
- [ ] CHK130 COP refresh latency ≤ 5 s asserted in `cross-cutting/cop-refresh-latency.spec.ts` [FR-008, Const §II-A, ASM-010]
- [ ] CHK131 Append-only audit timeline writes within 2 s with rationale, confidence, source references, operator identity [FR-010, Const §IV, ASM-010] [Veto]
- [ ] CHK132 AWS three-tier warnings (Advice / Watch and Act / Emergency Warning) parameterised across hazards including de-escalation and All Clear [FR-011, Const §V-A/V-B/V-C]
- [ ] CHK133 5-stage evacuation flow (Decision → Warning → Withdrawal → Shelter → Return) with types (total/partial/phased/shelter-in-place) and approaches (directed/recommended/self-initiated) asserted [FR-012, Const §VI-A/VI-B]
- [ ] CHK134 Vulnerable-population evacuation prioritisation (ATSI, CALD, disability, children, older persons, homeless, tourists, institutional care) filterable [FR-012, Const §VI-C]
- [ ] CHK135 Four recovery environments (Social, Built, Economic, Natural) tracked with managed handover from response [FR-013, Const §VII-A/B/C, SC-005]
- [ ] CHK136 Span-of-control warning fires for command-side personas at > 7 direct reports (Tier-1 IC; Tier-2 Ops/Logistics when supervising); suppressed for N/A personas (negative test) [FR-020, Clarif Q9]
- [ ] CHK137 WCAG 2.2 AA conformance asserted on every P1 operator surface: `/workspaces/[personaId]`, `/governance/dashboard/*`, warning composition, `/simulations/*`, audit timeline; failure emits `GAP-A11Y-WORKSPACE` [FR-014, Clarif Q14, spec-001 NFR-001]
- [ ] CHK138 Multilingual baseline asserted: Simplified Chinese variant on at least one warning per hazard category [FR-014, Clarif Q2, spec-001 NFR-013]
- [ ] CHK139 Aboriginal & Torres Strait Islander language placeholder rendered on at least one warning per hazard category [FR-014, Clarif Q2, Const §VI-C]
- [ ] CHK140 Data-sovereignty (a) **Display** — AU-region badge/banner on every regulated-data route; Foundry carve-out list reachable from `/governance/dashboard/compliance` [FR-018(a), Clarif Q3, Const NN#2] [Veto]
- [ ] CHK141 Data-sovereignty (b) **Gateway enforcement** — synthetic PSPF-marked / PII payload denied or masked at platform model gateway before any non-AU model-hosting endpoint (per ADR-033 Layer 2) [FR-018(b), Clarif Q3, Const NN#2] [Veto]
- [ ] CHK142 Data-sovereignty (c) **Registry currency** — `infra/parameters/foundry-carveout.yaml` (or successor) `review_date` within 90 days; `approver_identities[]` non-empty [FR-018(c), Clarif Q3, ADR-032, spec-029 FR-018]
- [ ] CHK143 Human-in-the-loop required for every safety-critical action (evacuation orders, public alerts, above-threshold reallocation); positive + negative tests both pass [FR-009, Const §I, Const NN#1] [Veto]
- [ ] CHK144 Field offline / degraded-mode queue-and-sync with idempotent dedupe by client correlation ID and conservative life-safety defaults [FR-017, Const NN#5]
- [ ] CHK145 Audit-timeline tampering attempt (PUT/PATCH against an audit ID) is rejected; no row is mutated [Edge Cases, FR-010, Const §IV] [Veto]
- [ ] CHK146 PPRR phases (Prevention, Preparedness, Response, Recovery) all exercised across the suite; every persona scenario tagged to ≥ 1 phase in trace [FR-006, Const §PPRR Lifecycle]
- [ ] CHK147 Quality Gate "Public outputs human-reviewed" honoured: no AWS warning publishes without IC approval [FR-009, FR-011, Const Quality Gates] [Veto]

---

## Section E — Iteration loop discipline (FR-024 / FR-027)

- [ ] CHK148 Iteration counter is enforced per gap: 4th cycle triggers `escalated:project-lead` flag, halts further automated cycles, blocks gate flip [FR-024, Clarif Q5, Clarif Q6, US5 §Acceptance #3]
- [ ] CHK149 Project-lead disposition (override / re-baseline / abandon) is recorded in audit timeline before any gate flip past an escalated gap [Const §Governance, FR-024]
- [ ] CHK150 Regression detection (FR-027): a previously-passing persona scenario failing after a fix for an unrelated gap triggers automatic rollback to prior known-good revision [FR-027, Clarif Q5, Clarif Q6, spec-017 FR-004, spec-029 FR-008]
- [ ] CHK151 On regression: gate stays `Not Ready`; regressed gap row tagged `regression_detected`; status returned to `Open`; iteration counter reset [FR-027, FR-005, Clarif Q11]
- [ ] CHK152 Rollback evidence captured for grading: failing Test ID + reverted commit SHA + restored revision SHA written to audit timeline [FR-027, US5 §Acceptance #4]
- [ ] CHK153 Gap-register state machine respects evidence-anchored transitions (Open → In-Progress requires real Closing Spec/PR + ≥ 1 re-run; In-Progress → Closed requires merge + re-run + passing test + no regression) [FR-005, Clarif Q11]
- [ ] CHK154 `Closed → Open` transitions only via FR-027; never by manual edit [FR-005, FR-027, Clarif Q11]

---

## Section F — CI gate (artefacts + budget + determinism)

- [ ] CHK155 Suite emits JUnit XML at stable path under `tests/e2e/web-coverage/_artifacts/` consumable by the CI gate without manual interpretation [FR-022, FR-023]
- [ ] CHK156 Suite emits JSON trace (machine-readable companion of `coverage-trace.md`) at stable path [FR-022, FR-004]
- [ ] CHK157 Screenshot/video captured on failure for post-incident review [FR-022]
- [ ] CHK158 Wall-clock budget ≤ 30 minutes on a developer machine asserted on a representative dev-shape host [SC-011, Clarif Q4, ASM-010]
- [ ] CHK159 Wall-clock budget ≤ 45 minutes on `ubuntu-latest` CI runner asserted on the CI gate run [SC-011, Clarif Q4, spec-017, spec-029]
- [ ] CHK160 Determinism asserted: 3 consecutive clean re-runs on the same `bootstrap_seed_data()` seed produce identical pass/fail signals (no flakes) [SC-010, FR-021, HYP-001]
- [ ] CHK161 Test fixtures impersonating personas use only identities present in `bootstrap_seed_data()`'s identity registry; no fixture-only RBAC drift [ASM-011, FR-021, OOS-007]

---

## Section G — Out-of-scope discipline (no scope creep through implementation)

- [ ] CHK162 Asia (PH/JP/BD) personas, hazards, and language packs remain absent from the 68-inventory, the suite, and the success criteria [OOS-001, ASM-005, spec-028]
- [ ] CHK163 UI translation / localisation of dashboard chrome remains out of scope; only AWS warning payloads and ≥ 1 community-language variant per warning category are translated [OOS-002, FR-014]
- [ ] CHK164 Net-new Azure infrastructure is included only when essential and approved by technical agents during plan phase [OOS-003, ASM-007]
- [ ] CHK165 Existing simulation engine is reused; no engine rewrite is in scope [OOS-004]
- [ ] CHK166 Visual-regression / pixel-perfect snapshot tests are not included [OOS-005]
- [ ] CHK167 Load / soak / chaos tests are not included; SC-002, FR-008, FR-010 budgets are operator-visible, not infra-scale [OOS-006, ASM-010]
- [ ] CHK168 IdP-integration changes are not made; suite uses test fixtures under existing RBAC model [OOS-007, ASM-011]
- [ ] CHK169 Bicep / Terraform refactors stay in their owning infra spec(s); not in this feature [OOS-008]
- [ ] CHK170 Mobile-native field application is not built; offline mode is web-context only [OOS-009, FR-017]
- [ ] CHK171 Suite outputs are CI-internal; no public release of artefacts [OOS-010]

---

## Section H — 85-agent review feedback ledger (per ASM-006 / Clarif Q13)

- [ ] CHK172 Operational sub-panel (10 agents) — every meritorious objection (≥ 2/3 panel) is `Closed` in gap-register before sign-off [ASM-006, Clarif Q13]
- [ ] CHK173 Sector sub-panel (58 agents — NSW 6 + VIC 5 + QLD 4 + SA 5 + WA 3 + TAS 4 + ACT 7 + NT 5 + Commonwealth 11 + Cross-Sector 8) — every meritorious objection (≥ 2/3 of relevant sector sub-panel) is `Closed` [ASM-006, Spec §Cited inputs]
- [ ] CHK174 Technical sub-panel (17 agents) — every meritorious objection (≥ 2/3 panel) is `Closed` [ASM-006, Clarif Q13]
- [ ] CHK175 Total 85 agents (10 + 58 + 17) accounted for in the review log [ASM-006]

---

## Section I — Tasks ↔ checklist cross-reference (T172)

The iteration loop runners use this table to mark coverage gates without
re-tracing every CHK-ID. Each row links a checklist item to the spec-034
task(s) that satisfy it; once those tasks are marked `[X]` in
`tasks.md`, the corresponding CHK can be ticked.

| CHK-ID  | Satisfied by tasks            | Notes                                                                                       |
| ------- | ----------------------------- | ------------------------------------------------------------------------------------------- |
| CHK034  | T053, T157, T158, T162        | Sector panel review wired via `review-log.py panel` resolver and nightly iteration workflow. |
| CHK045  | T069 (incident-commander), T146, T146 (Outcome 1 closure), T065 (span-of-control) | Workspace + scenario + outcome 1+2 trace + Tier-1 evaluation. |
| CHK090  | T080 (act-esa)                | ACT ESA workspace + must-do scenario.                                                        |
| CHK130  | T055                          | COP refresh latency assertion in `cross-cutting/cop-refresh-latency.spec.ts`.                |
| CHK160  | T051, T152, T153              | Determinism: 3-run script, trace-merge sort_keys, CI gate determinism step.                  |
- [ ] CHK176 Operational-panel domain-veto exercised correctly: any ≥ 2/3 operational objection on `Const §I` (Primacy of Life), `§IV` (Auditability), NN#1 (Human-in-the-loop), NN#2 (Data sovereignty), or "Public outputs human-reviewed" was addressed before any gate flip [ASM-006, Clarif Q13] [Veto]
- [ ] CHK177 Sector and technical panels did NOT exercise an analogous unilateral veto; their objections fell under default 2/3 weighting + project-lead adjudication [ASM-006, Clarif Q13]
- [ ] CHK178 Cross-panel disputes carry recorded project-lead disposition per `Const §Governance` ("project lead has final authority on architectural decisions") [Const §Governance, ASM-006]
- [ ] CHK179 HYP-002 falsification trigger evaluated: if > 30 % of the 68 personas required new routes/features, AU-validated cohort still ships and un-validated routes/features spawn a follow-on uplift feature (not a hard suite-fail) [HYP-002, spec-027 FR-018]
- [ ] CHK180 HYP-003 evaluated: rubric grading did not flag Asia coverage as a non-deferable critical-path criterion; if it did, OOS-001 / ASM-005 are revisited [HYP-003, spec-028]

---

## Cycle-1 Amendment Items (CHK181+)

> Added in cycle-1 to cover the pass-3 / pass-4 / pass-5 amendments (Q15..Q29, FR-028, FR-029, FR-030, SC-012) introduced after the original 180-item checklist (CHK001..CHK180) was produced at `350e1db`. Existing items are NOT renumbered. Each item below uses a `WHEN ... THEN ... ASSERT ...` plain-English assertion with the originating clarification Q-id and FR/SC anchor cited inline.

### J1. Pass 3 (Q15..Q19) coverage

- [ ] CHK181 [Q15, FR-002, FR-009] WHEN a persona scenario is committed under `tests/e2e/web-coverage/{operational,sectors/<jurisdiction>}/` THEN ASSERT it carries at least one workflow-state assertion proving the persona's safety-critical capstone capability (state-changing transition: approval / publish / allocate / decline / queue-sync / escalate / handover / declare / reopen, or a Pass 4 Q24 read-only equivalent) — route reachability + audit emission alone are NOT sufficient. **Closes via**: T184.
- [ ] CHK182 [Q15, FR-002, FR-028] WHEN any persona scenario contains `test.fail(true, "<API not wired>")` THEN ASSERT it does NOT count toward the 68/68 FR-002 numerator AND the missing capability MUST be closed via the FR-028 endpoints before the gate may flip to `Capstone Ready` (no `test.fail` workaround at gate time). **Closes via**: T184, T185, T186.
- [ ] CHK183 [Q16, FR-028] WHEN the plan/tasks decompose FR-028 THEN ASSERT both endpoint families — `/api/outcomes/sc-{NNN}/evaluate` (the capstone evaluator) AND `/api/audit/list` (correlation-keyed read-back) — are wired as route-only additions against the existing Next.js + FastAPI baseline; OOS-003 (no net-new Azure resource) does NOT apply. **Closes via**: T173, T178, T179.
- [ ] CHK184 [Q17, FR-030, FR-016] WHEN the 6 SA/WA/TAS net-new scenarios (`sapol.state-control-centre-rbac`, `ses-sa.long-distance-multi-lga-evacuation`, `dfes-wa.atsi-handoff-culturally-safe`, `dfes-wa.iron-ore-critical-infrastructure`, `at.island-isolation-aeromedical-disruption`, `taspol.palawa-multilingual-warning`) are authored THEN ASSERT they sit under existing FR-002 personas (no new persona IDs introduced) AND emit `coverage-trace.md` rows mapped to FR-016 hazard pair #4 (bushfire+TC) or pair #5 (riverine flood+severe storm). **Closes via**: T188, T190, T199.
- [ ] CHK185 [Q18, FR-030, FR-013] WHEN the 7 ACT/NT/Commonwealth/cross-sector net-new scenarios (`afp.national-capital-security-mechanics`, `ses-act.territory-emergency-declaration`, `ntes.atsi-multilingual-at-persona-level`, `sja-nt.tropical-disease-remote-logistics`, `bom-national.abc-sbs-warning-relay`, `nema.dacc-jatwc-cross-jurisdiction`, `utility.insurance-recovery-handoff`) are authored THEN ASSERT they target FR-013 recovery environments (Built + Economic) and FR-018 sovereignty triple where applicable; ABC/SBS coverage is carried by `bom-national.abc-sbs-warning-relay` (no new ABC/SBS personas added to the canonical 11-Commonwealth roster). **Closes via**: T193..T198.

### J2. Pass 4 (Q20..Q24) coverage

- [ ] CHK186 [Q20, FR-029] WHEN the depth-profile contract is materialised THEN ASSERT `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml` exists for every persona in the FR-002 inventory of 68, validated against `_schema.json` (JSON-Schema draft-07), with required keys `persona_id`, `workspace_route`, `safety_critical_workflow`, `workflow_steps`, `assertion_targets`, `capstone_outcome`, `hazard`. **Closes via**: T174, T175.
- [ ] CHK187 [Q20, FR-029, FR-005, FR-023] WHEN any depth-profile YAML is missing or fails schema validation THEN ASSERT the persona spec generator refuses to emit a spec AND `GAP-DEPTH-PROFILE-MISSING-{persona-id}` is opened in the gap register AND the binary CI gate (FR-029 final sentence) blocks `Capstone Ready` — opt-out is forbidden. **Closes via**: T177.
- [ ] CHK188 [Q21, FR-028] WHEN `POST /api/outcomes/sc-{001..005}/evaluate` is invoked THEN ASSERT (a) idempotency keyed by `(sc_id, scenario_id, persona_id, correlation_id)` (repeat call → same `audit_id` + verdict; new `correlation_id` → fresh evaluation), (b) unknown `scenario_id` returns HTTP 404 + `GAP-EVALUATOR-SCENARIO-MISSING` per FR-005, (c) out-of-range `sc_id` returns HTTP 400 (silent pass forbidden). **Closes via**: T178, T180.
- [ ] CHK189 [Q22, FR-028, FR-010] WHEN `GET /api/audit/list?cycle={current|all}` is invoked THEN ASSERT cursor-based pagination (`limit` default 100, max 500), `cycle=current` filters by `bootstrap_seed_data().current_cycle_start`, rows are append-only and never deleted (constitution §IV), AND tamper attempts themselves emit audit entries (per Pass 4 Q24). **Closes via**: T179, T181.
- [ ] CHK190 [Q23, FR-001, FR-030] WHEN an FR-030 cross-jurisdiction scenario is placed in the suite layout THEN ASSERT folder placement pivots on the **owning persona** (`nema.dacc-jatwc-cross-jurisdiction.spec.ts` → `sectors/commonwealth/`; `bom-national.abc-sbs-warning-relay.spec.ts` → `sectors/commonwealth/`; `utility.insurance-recovery-handoff.spec.ts` → `sectors/cross-sector/`), NOT on the union of cross-jurisdiction tags; multi-jurisdiction reach is recorded via `coverage_tags` in the depth-profile YAML, never via folder placement. **Closes via**: T187..T199.
- [ ] CHK191 [Q24, FR-029, FR-020] WHEN a persona's canonical safety-critical workflow is read-only (Observer/Auditor, Executive Leader, sector personas with no state-changing must-do, FR-020 "Warning is N/A" cohort) THEN ASSERT FR-029(b) is satisfied by ANY of (a) tamper-attempt + read-back returning `403`/`409` + denied audit entry, (b) audit-derivative report-generate + export with persisted report ID, or (c) briefing-acknowledgement state change written to the audit timeline; the depth-profile enum admits `observe-tamper-resist`, `report-generate`, `export-evidence`. **Closes via**: T175, T177.

### J3. Pass 5 (Q25..Q29) coverage

- [ ] CHK192 [Q25, FR-021, ASM-011] WHEN test-support routes are activated in CI / dev / test THEN ASSERT the canonical env-var name is `AMA_TEST_SUPPORT=1` (matching `contracts/persona-fixture.contract.md` L21/L37 and `apps/api/app/middleware/test_support_guard.py:27`); spec text in Pass 3 Q19 / Pass 4 Q21 / Pass 4 Q22 referencing `AMA_TEST_SUPPORT_ENABLED` is read as `AMA_TEST_SUPPORT` per the Q25 canonical override (no Q19..Q22 re-edits required). **Closes via**: T007 (middleware), T200..T202.
- [ ] CHK193 [Q26, FR-022, FR-005] WHEN the suite starts a run THEN ASSERT a custom Playwright Reporter `onBegin` hook emits `tests/e2e/web-coverage/_artifacts/cycle-metadata.json` (gitignored) with required keys `cycle_start_ts` (ISO-8601 UTC, sourced from `bootstrap_seed_data().current_cycle_start`), `cycle_id` (UUID v4), `commit_sha`, `seed_hash` (SHA-256 of seed JSON) — validated against `contracts/cycle-metadata.schema.json`; `GapRegisterEntry` MAY carry an optional `cycle_id` reference (additive, not mandatory). **Closes via**: T182.
- [ ] CHK194 [Q27, FR-028] WHEN `/speckit.plan` re-runs THEN ASSERT `contracts/outcome-evaluator.contract.md` is promoted to a Phase-1 contract peer of `coverage-trace-row.schema.json`, embeds a JSON-Schema block for the request body (`ajv`-validatable per T047 pattern), is authored by NEW task **T173**, and is a dependency of T146..T150 — plan re-run cannot exit Phase-1 without it committed. **Closes via**: T173.
- [ ] CHK195 [Q28, FR-029] WHEN `/speckit.tasks` re-runs THEN ASSERT a NEW task family **T174..T177** is added: T174 authors `_schema.json` (Phase-1 contract); T175 authors 68 `*.depth.yaml` files across 4 shards (sourced from cited input persona-must-do lists); T176 extends `scripts/web-coverage/_lib/persona_spec_generator.py` to load + validate + emit + open `GAP-DEPTH-PROFILE-MISSING` on missing/invalid profile; T177 extends `web-coverage-gate` (T153) to fail when any persona lacks a valid profile. **Closes via**: T174..T177.
- [ ] CHK196 [Q29, FR-028] WHEN `/api/outcomes/sc-{NNN}/evaluate` is invoked for `sc-006..sc-011` (or any sc-NNN outside `sc-001..sc-005`) THEN ASSERT HTTP 400 is returned with body `{ error: "evaluator_not_routable", sc_id: "...", suggested_action: "see SC-XXX ownership in spec.md FR-028 / Pass 5 Q29 — derived from CI artefacts (web-coverage-gate, gap-register, verify-trace-determinism), not from a workflow-state evaluator endpoint" }` — `metric_inputs` are SC-001..SC-005 only. **Closes via**: T180.

### J4. FR-028 outcome-evaluator endpoint conformance

- [ ] CHK197 [FR-028, Q21, FR-010] WHEN the evaluator endpoint returns 200 THEN ASSERT the response body matches the FR-028 shape `{ status: "pass"|"fail"|"gap", evidence_refs: string[], metric_value: number|null, threshold: number|null, audit_id: string }` AND the returned `audit_id` resolves via `/api/audit/list?correlation_id={id}` to an append-only audit row containing rationale + confidence + source references + operator identity. **Closes via**: T180.
- [ ] CHK198 [FR-028, Q21, ASM-011] WHEN an evaluator request includes `persona_id` THEN ASSERT the persona resolves in `bootstrap_seed_data().identities` (no fixture-only identities); unresolved persona IDs emit a contract-validation failure consistent with `persona-fixture.contract.md` and are NEVER silently accepted. **Closes via**: T180.
- [ ] CHK199 [FR-028, Q22, FR-027] WHEN `cycle=all` is requested on `/api/audit/list` THEN ASSERT it is opt-in only and reserved for FR-005 cross-cycle status-transition reads + FR-027 regression evidence (failing Test ID + reverted commit SHA + restored revision); default behaviour stays `cycle=current` to keep gate runs bounded by SC-011's CI runtime budget. **Closes via**: T181.
- [ ] CHK200 [FR-028, Q21, FR-021, OOS-007] WHEN the evaluator or audit-list endpoint is reached in production THEN ASSERT the dual-guard rejects activation (`AMA_TEST_SUPPORT != "1"` OR `ENVIRONMENT not in {dev,test}` → 404 / 403) AND no IdP changes are introduced — OOS-007 still holds; production registration of test-support routes is forbidden. **Closes via**: T180, T181.

### J5. FR-029 depth-profile contract conformance

- [ ] CHK201 [FR-029, Q20, Q24, T174] WHEN `_schema.json` is authored (task T174) THEN ASSERT it is JSON-Schema draft-07 AND `safety_critical_workflow` is a closed enum with all 12 values: `approval | publish | allocate | decline | queue-sync | escalate | handover | declare | reopen | observe-tamper-resist | report-generate | export-evidence` — no other values are admissible. **Closes via**: T174.
- [ ] CHK202 [FR-029, Q20, FR-014] WHEN a depth-profile YAML carries `multilingual_variant` THEN ASSERT the value is a canonical BCP-47 tag (selection deferred to plan-phase `research.md` per FR-014 / Clarif Q2); the key is OPTIONAL (missing variants are NOT a gate failure) but unrecognised tags MUST fail schema validation. **Closes via**: T177.
- [ ] CHK203 [FR-029, Q24, FR-002] WHEN a read-only persona's depth-profile YAML uses `observe-tamper-resist` / `report-generate` / `export-evidence` THEN ASSERT the generated spec actually drives a tamper-attempt + read-back, an audit-derivative report-export flow, or a briefing-acknowledgement (per Pass 4 Q24 (a)/(b)/(c)) — the generator MUST NOT silently downgrade to a route-only stub. **Closes via**: T175.
- [ ] CHK204 [FR-029, T177, FR-023] WHEN `web-coverage-gate` runs THEN ASSERT it fails (binary, non-relaxable) when any persona in the FR-002 inventory of 68 lacks a valid `*.depth.yaml`; this realises the FR-029 final-sentence gate and feeds FR-023(a) (every persona has ≥ 1 passing scenario). **Closes via**: T177.

### J6. FR-030 13 net-new scenarios coverage

- [ ] CHK205 [FR-030, Q17, FR-016] WHEN SA + WA + TAS net-new scenarios are committed THEN ASSERT all 6 spec files exist + pass: `sapol.state-control-centre-rbac.spec.ts`, `ses-sa.long-distance-multi-lga-evacuation.spec.ts`, `dfes-wa.atsi-handoff-culturally-safe.spec.ts`, `dfes-wa.iron-ore-critical-infrastructure.spec.ts`, `at.island-isolation-aeromedical-disruption.spec.ts`, `taspol.palawa-multilingual-warning.spec.ts`. **Closes via**: T187..T192.
- [ ] CHK206 [FR-030, Q18, FR-014] WHEN ACT + NT net-new scenarios are committed THEN ASSERT all 4 spec files exist + pass: `afp.national-capital-security-mechanics.spec.ts`, `ses-act.territory-emergency-declaration.spec.ts`, `ntes.atsi-multilingual-at-persona-level.spec.ts`, `sja-nt.tropical-disease-remote-logistics.spec.ts`; ATSI multilingual is exercised at persona scope (NT-specific palawa / Yolŋu / Kriol variants), not just cross-cutting. **Closes via**: T193..T196.
- [ ] CHK207 [FR-030, Q18, Q23, FR-015, FR-018] WHEN Commonwealth net-new scenarios are committed THEN ASSERT both spec files exist + pass under `sectors/commonwealth/`: `bom-national.abc-sbs-warning-relay.spec.ts` (records `Source = ABC/SBS` in audit + multilingual variants per FR-014 + sovereignty triple per FR-018 at relay handoff) AND `nema.dacc-jatwc-cross-jurisdiction.spec.ts` (DACC + JATWC handoff via `state-government` and `territory-government` cross-jurisdiction tags, moved here from cross-sector per Pass 4 Q23). **Closes via**: T197, T198.
- [ ] CHK208 [FR-030, Q18, FR-013, SC-005] WHEN the cross-sector net-new scenario is committed THEN ASSERT `utility.insurance-recovery-handoff.spec.ts` exists + passes under `sectors/cross-sector/` AND its `coverage-trace.md` row(s) map to capstone outcome #5 (30% economic-loss reduction) AND assert Built + Economic Recovery Environment state per FR-013. **Closes via**: T199.
- [ ] CHK209 [FR-030, FR-029, FR-004] WHEN any of the 13 FR-030 net-new scenarios is committed THEN ASSERT it conforms to FR-029's depth contract (workspace + state-changing transition + audit read-back + post-transition assertion via FR-028 evaluator or persisted-state UI selector) AND emits at least one row in `coverage-trace.md` against the persona's primary capstone outcome — NO scenario added by FR-030 is admitted as a stub. **Closes via**: T187..T199.

### J7. SC-012 cycle closure measurement

- [ ] CHK210 [SC-012, FR-024, FR-005] WHEN an iteration cycle closes THEN ASSERT ≥ 80 % of merit-validated objections are flipped to `Closed` per FR-005 in the next implement phase, with closure evidenced by (a) gap register row = `Closed`, (b) the originally-failing or generator-driven scenario passing on the post-amendment commit, AND (c) the closing PR's diff containing the FR-029 depth-contract assertion the panel demanded. **Closes via**: T203.
- [ ] CHK211 [SC-012, FR-024] WHEN any objection survives 3 iteration cycles THEN ASSERT it is escalated to project lead per FR-024 AND excluded from BOTH the SC-012 numerator and denominator — escalated objections do NOT count as "open below 80 %" and are NEVER counted as closed. **Closes via**: T203.
- [ ] CHK212 [SC-012, ASM-006, FR-010] WHEN cycle-N closure is computed THEN ASSERT the metric is calculated per cycle (not aggregated across cycles), uses only **merit-validated** objections (≥ 2/3 panel support per ASM-006 / Clarif Q13), AND the calculation evidence (numerator, denominator, escalated set, raw objection list) is captured in the audit timeline (FR-010) before the gate may flip toward `Capstone Ready`. **Closes via**: T203.

### J8. Env-var canonicalisation (CI + quickstart)

- [ ] CHK213 [Q25, FR-021] WHEN `.github/workflows/ci.yml` is normalised under cycle-2 budget THEN ASSERT line 147's `AMA_TEST_SUPPORT_ENABLED: "true"` is replaced with `AMA_TEST_SUPPORT: "1"` AND no other test-support env-var name is introduced anywhere in the workflow — the contract + middleware + tasks T007/T010 stand unchanged. **Closes via**: T200.
- [ ] CHK214 [Q25, FR-021] WHEN `quickstart.md` is normalised under the same plan/implement task THEN ASSERT line 281's `AMA_TEST_SUPPORT_ENABLED=true` is replaced with `AMA_TEST_SUPPORT=1` AND every body command line that exports the test-support guard reads `AMA_TEST_SUPPORT=1` (consistent with contract + middleware); the dual-guard semantic (`os.environ.get("AMA_TEST_SUPPORT") == "1"` AND `settings.environment in {"dev","test"}`) is unchanged. **Closes via**: T201.
- [ ] CHK215 [Q25, ASM-011, OOS-007] WHEN any future agent or PR proposes a name change away from `AMA_TEST_SUPPORT` THEN ASSERT the persona-fixture contract (`contracts/persona-fixture.contract.md`) is updated FIRST (it is the named source of truth per ASM-011 and Pass 5 Q25); spec text and CI workflow MUST follow the contract, not lead it — and OOS-007 still applies (no IdP changes). **Closes via**: T202.

---

## Notes

- This checklist is the **workflow gate** counterpart to `requirements.md` (the **spec-quality gate** which is already passing per `350e1db`).
- The parent agent ticks Section A items as it advances through `/speckit.plan` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement` → 85-agent review → deploy.
- Sections B–H are the empirical evidence the gate looks for at the `/speckit.implement` and review phases.
- `[Veto]`-marked items map to ASM-006 / Clarif Q13's operational-panel domain-veto; these MUST be `[x]` before any gate flip to `Capstone Ready` regardless of sector / technical panel weighting.
- `[Gap]` markers indicate forward-looking artefacts (e.g. `coverage-trace.md`, `gap-register.md`) that don't exist at spec-time but are required at implement-time.
- Re-runs of `/speckit.checklist` should APPEND new files to this folder rather than overwrite this one. Persona inventory drift is recorded by adding a CHKxxx item under the affected jurisdiction subsection.

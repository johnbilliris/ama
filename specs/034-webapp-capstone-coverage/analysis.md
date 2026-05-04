# Spec 034 — Cross-Artifact Consistency Analysis

> **Scope**: spec.md, plan.md, tasks.md, data-model.md, research.md, contracts/*, checklists/validation.md against constitution v1.2.0, capstone.md, ADRs (031–036), and prior specs (028, 027, 029, 017, 015, 001).
> **Branch**: `034-webapp-capstone-coverage`
> **Pre-fix commit**: `1da3beb`
> **Mode**: `/speckit.analyze` with auto-resolution mandate (resolutions applied inline; only truly ambiguous items escalated).
> **Date**: 2026-04-26

---

## Summary

| Bucket | Count |
| --- | --- |
| Total findings raised | 7 |
| CRITICAL | 2 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 1 |
| Auto-resolved (this pass) | 7 |
| Escalated for parent decision | 0 |
| Final state | **CLEAN** — parent agent may proceed to `/speckit.implement` |

**Coverage check** (sampled — full matrix below):

| Surface | Items | Mapped to ≥1 task | % |
| --- | --- | --- | --- |
| Functional Requirements (FR-001..FR-027) | 27 | 27 | 100% |
| Success Criteria (SC-001..SC-011) | 11 | 11 | 100% |
| Capstone outcomes (1–5) | 5 | 5 | 100% (T146..T150) |
| In-scope personas (10 operational + 58 sector) | 68 | 68 | 100% (T069..T136 + T137..T145) |
| Hazard pairs (FR-016 outcomes 1–5) | 5 | 5 | 100% (fixtures T028..T032 + tagged tests) |
| Constitution clauses (I, II, II-A, III, IV, V/V-A/V-B/V-C, VI, VII, VIII, NN-1..NN-5, QG-1..QG-3) | 22 | 22 | 100% (cross-cutting T054..T068) |
| Out-of-Scope items (OOS-001..OOS-010) | 10 | 0 violations | n/a (boundary check) |

---

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| --- | --- | --- | --- | --- | --- |
| F1 | Drift / inconsistency | **CRITICAL** | `plan.md` §Module Breakdown lines 158–167 | Operational persona file list cites `06-recovery-coordinator`, `07-volunteer-coordinator`, `08-resource-deployer`, `09-evacuation-marshal`, `10-warning-officer` — none of which exist in spec §Cited inputs (line 16) or §Suite Layout (lines 566–577). Tasks T069–T078 + validation CHK045–054 use the spec-canonical IDs. | **Resolved**: rewrote plan §Module Breakdown lines 156–167 to use canonical IDs `incident-commander`, `operations-officer`, `planning-officer`, `logistics-officer`, `public-information-officer`, `field-coordinator`, `resilience-planner`, `executive-leader`, `observer-auditor`, `risk-manager`. Authority: spec.md lines 16, 566–577 (the spec is the authoritative persona inventory; plan is a downstream view). |
| F2 | Drift / inconsistency | **HIGH** | `plan.md` §Module Breakdown lines 168–178 | Sector persona shorthand uses non-existent IDs (`qfes`, `sesqld`, `qhealth`, `vicses`, `sa-cfs`, `sa-ses`, `wa-dfes`, `tas-fire`, `nt-pfes`, `geoscience`, `defence-dacc`, `abc-emergency`, `esta-triple-zero`, `ica`, `electricity-tx`, `water-utils`, `telco`, `supply-chain`, `disability`, `health-utility`, `multi-faith`). Tasks T079–T136 use spec-canonical IDs (`qfd`, `ses-qld`, `ses-vic`, `sacfs`, `ses-sa`, `dfes-wa`, `tfs`, `ses-tas`, `bushfires-nt`, `ntfrs`, `ga-national`, `adf`, `nema`, `bom-national`, `surf-lifesaving`, `community-ngos`, `health`, `local-government`, `state-government`, `territory-government`, `transport`, `utility`, `volunteer`). | **Resolved**: rewrote plan §Module Breakdown lines 168–178 to enumerate the 58 sector personas exactly as defined in spec lines 17–19. Authority: spec.md §Cited inputs is the authoritative inventory. |
| F3 | Drift / inconsistency | **CRITICAL** | `plan.md` §NFR Verification lines 607–619 | Plan rows for SC-001..SC-009 are mislabelled. Spec defines SC-001 = lives saved (Outcome #1), SC-002 = 50% faster response, SC-003 = 24-h-earlier evac, SC-004 = 30% logistics efficiency, SC-005 = 30% economic-loss reduction, SC-006 = 100% persona coverage, SC-007 = cross-jurisdiction coverage, SC-008 = cross-cutting compliance, SC-009 = iteration loop closure. Plan reverses much of this (e.g., labels persona×outcome×hazard coverage as `SC-001` rather than `SC-006`). | **Resolved**: rewrote NFR Verification table to correctly map each SC to its plan element + test surface, matching spec lines 515–525. SC-010 + SC-011 already correct; left intact. |
| F4 | Drift / typo | **HIGH** | `tasks.md` T063 line 144 | Task says "parameterised over IC + Operations Officer + Planning Officer". Spec Q9 + FR-020 (lines 309–334, 460) defines Tier-1 = `incident-commander`; Tier-2 (when supervising direct reports) = `operations-officer` + `logistics-officer`; `planning-officer` is in the Tier-N/A list (negative test only). | **Resolved**: edited tasks.md T063 to read "parameterised over IC + Operations Officer + Logistics Officer". Authority: spec.md FR-020 (line 460) + Clarifications Q9 (lines 309–334). |
| F5 | Inconsistency | **MEDIUM** | `research.md` R-011 lines 295–304 vs `plan.md` lines 195–197, 600–602, `tasks.md` T030–T032, T148–T150 | Research uses verbose canonical fixture filenames (`outcome-3-tropical-cyclone-riverine-flood.fixture.json`, `outcome-4-bushfire-tropical-cyclone.fixture.json`, `outcome-5-riverine-flood-severe-storm.fixture.json`); plan + tasks use abbreviated forms (`outcome-3-tropical-cyclone-flood.fixture.json`, `outcome-4-bushfire-cyclone-logistics.fixture.json`, `outcome-5-flood-storm-economic.fixture.json`). Implement-time, the test files are what gets created; research is a design-decision artefact and should match. | **Resolved**: aligned research.md R-011 fixture filenames to the abbreviated plan/tasks naming (less churn — tasks are already authored against those names). The canonical hazard tag `riverine-flood` (per tasks line 21 tag taxonomy) is preserved in tags; only filenames are abbreviated for human readability. |
| F6 | Schema gap | **MEDIUM** | `data-model.md` §5 lines 251–256 + `contracts/persona-fixture.contract.md` lines 99–104 | The `role` field is a closed enum of the 5 AIIMS function names (`incident-controller`, `operations-officer`, `planning-officer`, `logistics-officer`, `public-information-officer`), which (a) duplicates the existing `aiims_function` field and (b) cannot represent the 63 personas outside AIIMS-5 (Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager + all 58 sector combat-agency roles such as BoM forecaster, NEMA officer, NSW RFS captain). T053's `persona.fixture.ts` MUST resolve all 68 personas; the current closed enum would fail validation for ≥63 of them. | **Resolved**: redefined `PersonaFixture.role` as a free-form `string` (the persona's organisational role title, e.g., `"Incident Commander"`, `"BoM Forecaster"`, `"NSW RFS Captain"`). Kept `aiims_function` as the closed AIIMS-5 enum (this is what RBAC checks against). Updated both `data-model.md` §5 and `contracts/persona-fixture.contract.md` Type block. Authority: constitution §II-A defines AIIMS-5 as the function map (preserved on `aiims_function`); spec §Cited inputs defines 68 personas across non-AIIMS-5 roles (preserved on `role`). |
| F7 | Inconsistency | **LOW** | `plan.md` §Hazard-Pair Coverage line 600–602 | Trace-tags column uses `@hazard:flood` but the canonical hazard tag taxonomy in `tasks.md` line 21 + spec FR-016 is `@hazard:riverine-flood`. Tasks (T080, T091, T148, etc.) use `@hazard:tropical-cyclone+riverine-flood`; plan's table uses the wrong slug. | **Resolved**: edited plan §Hazard-Pair Coverage table to use canonical `@hazard:riverine-flood` everywhere. Authority: tasks.md line 21 tag taxonomy is normative for the lint rule; spec FR-016 + R-017 lock that taxonomy. |

> **No CRITICAL / HIGH findings remain after resolution. CLEAN state achieved.**

---

## Constitution Alignment

All five Non-Negotiables and three Quality Gates are exercised by ≥1 cross-cutting test:

| Constitution clause | Spec/Task anchor | Test surface |
| --- | --- | --- |
| §I Primacy of Life | FR-009, FR-011, ASM-008 | T056 `decision-support-hitl.spec.ts`, T058 `public-warnings.spec.ts`, ASM-006 operational-panel veto |
| §II AEMA principles (#4 Coordinated → span-of-control; #11 Continual improvement → lessons) | FR-020, FR-005, T063, T067 | `span-of-control.spec.ts`, `lessons-management.spec.ts`, gap register |
| §II-A AIIMS function map | FR-007, ASM-008, T057 | `rbac-aiims.spec.ts` + persona fixture's `aiims_function` field |
| §III Multi-Hazard, Multi-Agency | FR-016 hazard pairs | 5 capstone fixtures + 68 persona × hazard tags |
| §IV Transparency and Auditability | FR-010, FR-022, T066 | `audit-trail.spec.ts` + `auditObserver` fixture (≤2 s) |
| §V/V-A/V-B/V-C (AWS / 10 warning principles / CALD) | FR-011, FR-014, T058, T060 | `public-warnings.spec.ts`, `accessibility-and-multilingual.spec.ts` |
| §VI Evacuation (5-stage) | FR-012, T059 | `evacuation.spec.ts` |
| §VII Recovery (4 environments) | FR-013, SC-005, T075, T076 | `recovery.spec.ts` + outcome-5 capstone test |
| §VIII Azure-only / IaC / OIDC | FR-018(c), Bicep delta, RISK-12 | `data-sovereignty.spec.ts` + new `web-coverage-evidence` Bicep child + cd.yml `update-known-good` step |
| **NN-1 Human-in-the-loop** | FR-009, NN-#1, T056 | `decision-support-hitl.spec.ts` (positive + negative) |
| **NN-2 Data sovereignty + Foundry carve-out** | FR-018(a/b/c), constitution amendment 1.2.0, spec 029 FR-018, T062 | `data-sovereignty.spec.ts` triple assertion: AU badge + gateway PSPF/PII deny + `infra/parameters/foundry-carveout.yaml` review-date ≤90 days + non-empty approvers |
| NN-3 Privacy by design | FR-018(b), RISK-07 | `pspf-classification.ts` + `redact.ts` reporter |
| NN-4 Interoperability (CAP, EDXL, GeoJSON, OpenAPI) | FR-011 (CAP envelope), FR-018(a) | `aws-cap-envelope.ts` validator |
| **NN-5 Graceful degradation** | FR-017, T061 | `field-offline-mode.spec.ts` (queue-and-sync, conservative life-safety defaults) |
| QG-1 Lint + unit + integration on PR | T151–T156 | `web-coverage-shard / merge / gate` jobs in ci.yml |
| QG-2 What-If / Plan review on infra changes | new Bicep child, T013–T015 | What-If gate already part of cd.yml |
| QG-3 Public outputs human-reviewed | OOS-010, FR-009, ASM-006 operational-panel veto on QG | suite outputs are CI-internal; warning-publish flow has IC HITL gate |

**No constitution conflicts detected post-resolution.**

---

## Out-of-Scope Compliance

| OOS | Spec line | Cross-checked surfaces | Status |
| --- | --- | --- | --- |
| OOS-001 — Asia (PH/JP/BD) personas, hazards, language packs | spec §551 | tasks.md (zero PH/JP/BD task), plan.md, fixtures (zero non-AU events), `specs/shared/capstone-metric-trace.md` defers PH/JP/BD per cohort | ✓ Compliant |
| OOS-002 — UI translation/localisation of dashboard chrome | spec §552 | T060 only asserts community-language warning variants on warning routes, not chrome | ✓ Compliant |
| OOS-003 — Net-new Azure infrastructure | spec §553 | Plan §Net-New Azure adds **only** the `web-coverage-evidence` Blob child to the existing storage account (per ASM-007); justified for FR-022 + RISK-12 evidence retention | ✓ Compliant — minimal addition justified |
| OOS-004 — Replacing the simulation engine | spec §554 | Tasks reference existing engine + `bootstrap_seed_data()` | ✓ Compliant |
| OOS-005 — Visual regression | spec §555 | No tasks introduce snapshot/pixel comparisons | ✓ Compliant |
| OOS-006 — Load/soak/chaos | spec §556 | Performance tests are operator-visible-behaviour budgets only (SC-002, FR-008, FR-010) | ✓ Compliant |
| OOS-007 — Identity-provider integration changes | spec §557 | T008 `test_support.py` reads identities from `bootstrap_seed_data().identities` (ASM-011); no IdP work | ✓ Compliant |
| OOS-008 — Bicep/Terraform refactors | spec §558 | Plan adds one Bicep child only (allowed under OOS-003 carve-out); zero refactor | ✓ Compliant |
| OOS-009 — Mobile-native field app | spec §559 | T061 `field-offline-mode.spec.ts` exercises web-context offline only | ✓ Compliant |
| OOS-010 — Public release of suite outputs | spec §560 | All artefacts are CI-internal; new Blob container is private, RBAC-scoped to container per RISK-10 | ✓ Compliant |

---

## Capstone-Metric Trace Cross-Check (vs `specs/shared/capstone-metric-trace.md`)

| Capstone metric | AU-v1 cohort owner | Spec 034 task(s) | Status |
| --- | --- | --- | --- |
| `LIVES_SAVED` | spec 001 SC-002+SC-004 + spec 015 SC-CAP-015-001 | T058 + T146 (outcome 1, lives proxy via warning-coverage funnel + AWS compliance) | ✓ |
| `RESPONSE_SPEED` | spec 001 SC-004 + spec 015 SC-CAP-015-002 | T147 (outcome 2, signal→IC-action ≤ persona's L1/L2/L3 budget) | ✓ |
| `EVAC_LEAD_TIME` | spec 001 SC-005 + spec 015 SC-CAP-015-003 | T071, T078, T148 (outcome 3, `evac_lead_hours ≥ 24`) | ✓ |
| `LOGISTICS_EFFICIENCY` | spec 001 SC-006 + spec 015 SC-CAP-015-004 | T149 (outcome 4, `logistics_clicks ≤ 7`/`≤ 12`) | ✓ |
| `ECONOMIC_LOSS_REDUCTION` | spec 015 SC-CAP-015-005 (Sendai-aligned) | T075, T076, T150 (outcome 5, `(baseline−projected)/baseline ≥ 0.30`) | ✓ |

PH/JP/BD cohorts remain `Deferred` per `specs/shared/capstone-metric-trace.md` and OOS-001 — no spec-034 task contradicts deferral.

---

## Hypotheses Falsification

| HYP | Falsification trigger | Spec 034 evidence path |
| --- | --- | --- |
| HYP-001 — persona-driven suite produces credible signal | 3 consecutive runs disagree on pass/fail (any flake) | SC-010 + T155 nightly determinism check |
| HYP-002 — AIIMS / COP / audit / AWS / evac / recovery mostly already present (>30% personas requiring new routes/features falsifies) | per FR-018 spec-027 hypothesis format: re-scopes (AU-v1 still ships, un-validated routes spawn uplift feature); not a hard fail | gap-register `Open` count + uplift-feature trigger in CHK179 |
| HYP-003 — Asia deferral acceptable to graders | rubric flags Asia coverage as non-deferable critical-path | CHK180 (post-merge rubric inspection) |

All three HYPs have explicit falsification mechanisms and post-merge measurement paths.

---

## Coverage Matrix (FR → Tasks)

| FR | Description (abbrev) | Tasks |
| --- | --- | --- |
| FR-001 | Persona-driven Playwright suite naming | T001, T024–T026, T053, T069–T136 |
| FR-002 | One spec per persona | T069–T145 |
| FR-003 | Capstone-outcome proxy assertions | T146–T150 |
| FR-004 | Coverage-trace row schema (10 fields incl. clauses[]) | T038, T039, T044 |
| FR-005 | Gap register state machine | T044, T045, T157, T160 |
| FR-006 | RBAC AIIMS function check | T057 |
| FR-007 | RBAC denial / approval | T057, T079–T136 |
| FR-008 | COP refresh ≤ 5 s | T055 |
| FR-009 | HITL deterministic JSON | T056 |
| FR-010 | Audit append ≤ 2 s | T066, T029 |
| FR-011 | AWS warning compliance + 10 principles | T058 |
| FR-012 | 5-stage evacuation | T059 |
| FR-013 | 4 recovery environments | T075, T076, T150 |
| FR-014 | WCAG 2.2 AA + multilingual | T060 |
| FR-015 | Span-of-control surface | T063 |
| FR-016 | Outcome × hazard-pair fixtures | T028–T032 + tagged personas |
| FR-017 | Field offline mode | T061 |
| FR-018 | Data-sovereignty triple (badge / gateway / carveout) | T062 |
| FR-019 | Cross-jurisdiction scenarios | T137–T145 |
| FR-020 | Span-of-control parameterised over IC + Ops + Logistics | T063 (post-fix) |
| FR-021 | Bootstrap seed determinism | T011, T012, T155 |
| FR-022 | JUnit + JSON artefacts | T038, T040, T154 |
| FR-023 | CI gate fails on Open gaps + missing personas | T152, T153 |
| FR-024 | Max-3-cycle iteration loop with escalation | T046, T157, T161 |
| FR-025 | 85-agent review log + sub-panel weighting | T046, T157, T158 |
| FR-026 | Operational-panel domain-veto on safety clauses | T046, T157 (review-vote.schema.json `allOf` veto-clause guard) |
| FR-027 | Known-good manifest + ≤10 min rollback | T047, T048, T156, T162 |

**100% FR coverage. 0 unmapped tasks.**

---

## Metrics

- **Total Findings**: 7 (2 CRITICAL, 2 HIGH, 2 MEDIUM, 1 LOW)
- **Auto-resolved**: 7 / 7 (100%)
- **Escalated**: 0
- **Coverage % (FRs)**: 100 (27/27)
- **Coverage % (SCs)**: 100 (11/11)
- **Coverage % (personas)**: 100 (68/68)
- **Coverage % (constitution clauses)**: 100 (22/22)
- **Ambiguity count** (unresolved placeholders, vague NFRs): 0 (all NFRs have measurable budgets per Q1/Q4)
- **Duplication count** (near-duplicate FRs/SCs): 0
- **Critical issues remaining**: **0**

---

## Resolutions Applied (this pass)

1. **plan.md** §Module Breakdown — operational + sector persona file lists rewritten to match spec.md §Cited inputs and §Suite Layout.
2. **plan.md** §NFR Verification — table re-keyed so every SC label matches spec.md lines 515–525.
3. **plan.md** §Hazard-Pair Coverage — trace-tags column corrected to use canonical `riverine-flood` slug.
4. **tasks.md** T063 — "Planning Officer" replaced with "Logistics Officer" per spec FR-020 + Clarifications Q9.
5. **research.md** R-011 — fixture filenames aligned to abbreviated forms used in plan + tasks (less downstream churn; canonical hazard tags preserved separately).
6. **data-model.md** §5 `PersonaFixture.role` — redefined as free-form `string` with worked example; `aiims_function` retained as AIIMS-5 closed enum (the field RBAC checks against).
7. **contracts/persona-fixture.contract.md** Type block — same change as data-model.md §5.

---

## Next Actions

- **Parent agent may proceed to `/speckit.implement`** — no blockers remain.
- The 7 resolutions are committed on the same branch in a single commit (`spec(034): analyze — cross-artifact consistency analysis and resolutions`), with the Copilot co-author trailer per `Const §Governance`.
- No constitution amendments required.
- No spec re-clarification required.
- The 85-agent iteration tribunal (FR-024..FR-026) will catch any further drift at implement time; the gap register state machine + max-3-cycle bound enforce closure discipline.

---

*Generated by `/speckit.analyze` per spec-034 workflow gate (validation.md Section A.A4).*

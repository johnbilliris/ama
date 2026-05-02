# Tasks: Web Application Capstone Coverage Validation

**Branch**: `034-webapp-capstone-coverage` · **Spec**: `specs/034-webapp-capstone-coverage/spec.md`
**Plan**: `specs/034-webapp-capstone-coverage/plan.md` · **Data model**: `specs/034-webapp-capstone-coverage/data-model.md`
**Contracts**: `specs/034-webapp-capstone-coverage/contracts/{coverage-trace-row,gap-register-entry,review-vote,agent-objection}.schema.json` + `persona-fixture.contract.md`
**Research**: `specs/034-webapp-capstone-coverage/research.md` (R-001..R-019) · **Quickstart**: `specs/034-webapp-capstone-coverage/quickstart.md`
**Validation checklist**: `specs/034-webapp-capstone-coverage/checklists/validation.md` (180 items, CHK001..CHK180)
**Date**: 2026-05-02 · **Author**: tasks agent (grounded in plan §Module Breakdown + persona-need syntheses)
**Status**: Ready for `/speckit.analyze`

## Format: `[ID] [P?] [Story?] Description`

- **[P]** = parallel-safe (different file, no in-flight dependency on an incomplete task)
- **[Story]** = which user story the task serves (`US1` capstone traceability, `US2` cross-cutting guarantees, `US3` cross-jurisdiction integration, `US4` simulation/lessons, `US5` quality gate + iteration loop). Foundation tasks carry no story label.
- File paths are absolute-from-repo-root; an implementer with the path can execute without re-asking.
- Dependency order honoured: **foundation → cross-cutting → persona → capstone → CI → iteration loop → polish**. Within each phase `[P]` tasks may run concurrently.

## Tag taxonomy (R-017)

Every Playwright test MUST carry one tag from each axis (enforced by ESLint rule, T006):
`@persona:<persona-id>` · `@outcome:<1..5>` · `@hazard:<bushfire|extreme-heat|riverine-flood|tropical-cyclone|severe-storm|earthquake|tsunami>` · `@fr:FR-NNN` · `@clause:<I|II|II-A|...|NN-1|...>` · `@p1|@p2|@p3` (priority for shard / smoke selection).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding for `tests/e2e/web-coverage/**` and `scripts/web-coverage/**` without disturbing the existing Playwright suite at `tests/e2e/*.spec.ts`.

- [ ] T001 Create directory tree `tests/e2e/web-coverage/{operational,sectors/{nsw,vic,qld,sa,wa,tas,act,nt,commonwealth,cross-sector},cross-cutting,capstone,_support/{pages,fixtures,fixtures/data,reporter,validators,a11y,types,eslint-rules},_artifacts/{junit,screenshots}}` and `scripts/web-coverage/_lib/`
- [ ] T002 Add devDependencies `@axe-core/playwright@^4.10.0`, `js-yaml@^4`, `ajv@^8`, `ajv-formats@^3` to `apps/web/package.json`; pin Playwright at `1.59.1`; run `pnpm install --filter @ama/web` and commit lockfile delta
- [ ] T003 [P] Add path alias `@web-coverage/*` → `tests/e2e/web-coverage/_support/*` in `apps/web/tsconfig.json` and matching alias in `apps/web/playwright.config.ts`
- [ ] T004 [P] Append `tests/e2e/web-coverage/_artifacts/` and `tests/e2e/web-coverage/**/*.partial-*.json` to `.gitignore`; explicitly NOT-ignore `specs/034-webapp-capstone-coverage/coverage-trace.{md,json}` and `gap-register.md`
- [ ] T005 Extend `apps/web/playwright.config.ts` with three new `projects` entries — `web-coverage-chromium` (default), `web-coverage-mobile` (Pixel 7 emulation), `web-coverage-axe` (WCAG run); preserve existing legacy project list; wire `reporter` to `[['junit', { outputFile: 'tests/e2e/web-coverage/_artifacts/junit/results.xml' }], ['json', { outputFile: 'tests/e2e/web-coverage/_artifacts/playwright.json' }], ['./tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts']]`; set `forbidOnly: !!process.env.CI`, `retries: 0` on PR, `workers: process.env.CI ? 4 : 4`, base URL `http://127.0.0.1:3000`
- [ ] T006 [P] Author ESLint rule `tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs` (forbids `page.waitForTimeout`, R-015); register in `apps/web/.eslintrc.cjs` `rules` block scoped to `tests/e2e/web-coverage/**`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Test-support endpoint, Bicep child resource, page objects, fixtures, custom reporter, validators, gap-register CLI, trace-merge CLI, schema validators, seed-data extension. **No persona, cross-cutting, or capstone task may begin until this phase is complete.**

### Test-support endpoint (per `contracts/persona-fixture.contract.md`)

- [ ] T007 Implement `apps/api/app/middleware/test_support_guard.py` — dual-guard middleware (refuses requests when `settings.environment == "production"` OR `os.environ.get("AMA_TEST_SUPPORT") != "1"`); emits structured `test-support disabled: environment=… AMA_TEST_SUPPORT=…` log on startup
- [ ] T008 Implement `apps/api/app/api/routes/test_support.py` — FastAPI router exposing `GET /api/test-support/personas`, `GET /api/test-support/personas/{persona_id}`, `POST /api/test-support/seed/scenario`; reads identities only from `bootstrap_seed_data().identities` (ASM-011); returns shape per `contracts/persona-fixture.contract.md` lines 50–80
- [ ] T009 Wire test-support router into `apps/api/app/main.py` — conditional `include_router` gated by `test_support_guard.is_enabled()`; ensure no router registration when disabled (404 path); update `apps/api/app/api/router.py` aggregator
- [ ] T010 [P] Author contract test `apps/api/tests/test_test_support_router.py` asserting (a) 404 when `AMA_TEST_SUPPORT` unset, (b) 404 when `settings.environment == "production"` regardless of env var, (c) 200 + correct shape when both guards green, (d) refuses to mutate seed data on any verb

### Net-new Azure infrastructure (Bicep + RBAC)

- [ ] T011 [P] Add Bicep child resource `web-coverage-evidence` blob container + 7-year `immutabilityPolicy` (`allowProtectedAppendWrites: true`) to `infra/bicep/main.bicep` (insert under existing `storageBlob` parent); follow plan §Net-New Azure Resources HCL example verbatim; output container resourceId for downstream RBAC binding
- [ ] T012 [P] Extend the API Container App's managed-identity role assignment in `infra/bicep/modules/identity.bicep` (or equivalent existing assignments file) — grant `Storage Blob Data Contributor` (`ba92f5b4-2d11-453d-a403-e96b0029c9fe`) scoped **only** to the `web-coverage-evidence` container resourceId from T011; verify with `verify-iam-zero-trust.ps1` (RISK-10)
- [ ] T013 [P] Run `bicep build infra/bicep/main.bicep` and `az deployment group what-if` against the dev subscription; capture the diff in `specs/034-webapp-capstone-coverage/bicep-whatif.txt` for grading evidence

### Page objects (one per route in plan §Module Breakdown)

- [ ] T014 [P] Page object `tests/e2e/web-coverage/_support/pages/workspaces.po.ts` (`/workspaces/[personaId]`) — `getByRole`/`getByLabel`/`getByTestId` only; emits `auditApprove()` returning `audit_id`
- [ ] T015 [P] Page object `tests/e2e/web-coverage/_support/pages/incidents.po.ts` (`/incidents/[incidentId]`) — drives warning composer + IC approval modal
- [ ] T016 [P] Page object `tests/e2e/web-coverage/_support/pages/disasters.po.ts` (`/disasters/`) — disaster index + drill-down
- [ ] T017 [P] Page object `tests/e2e/web-coverage/_support/pages/governance.dashboard.po.ts` (`/governance/dashboard/{audit,compliance,readiness,recovery,risk}`)
- [ ] T018 [P] Page object `tests/e2e/web-coverage/_support/pages/governance.dataSource.po.ts` (`/governance/[dataSourceId]`)
- [ ] T019 [P] Page object `tests/e2e/web-coverage/_support/pages/operations.workflows.po.ts` (`/operations/workflows`)
- [ ] T020 [P] Page object `tests/e2e/web-coverage/_support/pages/preparedness.po.ts` (`/preparedness/`)
- [ ] T021 [P] Page object `tests/e2e/web-coverage/_support/pages/simulations.po.ts` (`/simulations/{create,[tenantId]/playback,reports/[reportId]}`)
- [ ] T022 [P] Page object `tests/e2e/web-coverage/_support/pages/eval.po.ts` (`/eval/[runId]`)

### Fixtures

- [ ] T023 [P] Persona fixture `tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts` — calls `GET /api/test-support/personas/{id}`, sets `X-Test-Persona-Id` header on context, exposes typed `PersonaFixture` per `data-model.md` §5; worker-scoped; fails fast if persona absent from seed (ASM-011)
- [ ] T024 [P] Hazard scenario fixture `tests/e2e/web-coverage/_support/fixtures/hazardScenario.fixture.ts` — loads `outcome-{N}-*.fixture.json`, calls `POST /api/test-support/seed/scenario`, exposes typed `HazardScenarioFixture` per `data-model.md` §6
- [ ] T025 [P] Correlation-id fixture `tests/e2e/web-coverage/_support/fixtures/correlationId.fixture.ts` — emits `crypto.randomUUID()` and attaches `X-Correlation-Id` to every request via `context.setExtraHTTPHeaders`
- [ ] T026 [P] Audit observer fixture `tests/e2e/web-coverage/_support/fixtures/auditObserver.fixture.ts` — wraps `expect.poll(GET /api/audits?cid=…)` with 2-second deadline (FR-010, SC-004); returns observed `audit_evidence_id`
- [ ] T027 [P] Carve-out registry fixture `tests/e2e/web-coverage/_support/fixtures/carveoutRegistry.fixture.ts` — loads `infra/parameters/foundry-carveout.yaml` once per worker, validates with `infra/parameters/foundry-carveout.schema.json` via `ajv`, asserts `review_date` ≤ 90 days old + `approver_identities[]` non-empty (FR-018(c))

### Hazard-pair fixture data (FR-016)

- [ ] T028 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json` — bushfire+extreme-heat seed scenario with baseline `lives_at_risk` numeric per data-model §6
- [ ] T029 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-2-bushfire-severe-storm.fixture.json` — baseline `signal_to_action_ms` per AIIMS Levels 1/2/3 budgets (SC-002 contractual: ≤ 5/15/30 min)
- [ ] T030 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json` — baseline `evac_lead_hours` ≥ 24 (SC-003)
- [ ] T031 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-4-bushfire-cyclone-logistics.fixture.json` — baseline `logistics_clicks` ≤ 7 routine / ≤ 12 mutual-aid (SC-004)
- [ ] T032 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-5-flood-storm-economic.fixture.json` — baseline `economic_loss_aud` per Sendai Indicator C (SC-005 formula `(baseline-projected)/baseline ≥ 0.30`)

### Custom reporter + types (FR-004)

- [ ] T033 Implement `tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts` — Playwright `Reporter` interface; `onTestEnd` extracts `coverage` annotations + dedupes by `(persona, outcome, hazard, fr_id)` tuple; `onEnd` writes `tests/e2e/web-coverage/_artifacts/coverage-trace.partial-${PW_SHARD ?? 1}.json` matching `contracts/coverage-trace-row.schema.json`; `onStdErr` converts `waitForTimeout` matches into test failures (R-002, R-015)
- [ ] T034 [P] Annotation helpers `tests/e2e/web-coverage/_support/reporter/annotations.ts` — typed `recordCoverage({persona, outcome, hazard, fr, clauses, route, audit_evidence_id, status})` wrapper around `test.info().annotations.push(...)`
- [ ] T035 [P] Trace-row helper `tests/e2e/web-coverage/_support/reporter/trace-row.ts` — `CoverageTraceRow` factory + sort key `(persona_id, outcome, hazard, fr_id)` for deterministic merge
- [ ] T036 [P] Redaction helper `tests/e2e/web-coverage/_support/reporter/redact.ts` — strips PII (names, emails, GPS coords < 1km precision) from screenshots/JSON before artefact upload (RISK-07, R-016)
- [ ] T037 [P] Type declaration `tests/e2e/web-coverage/_support/types/coverage.d.ts` — exports `CoverageTraceRow` matching `data-model.md` §1
- [ ] T038 [P] Type declaration `tests/e2e/web-coverage/_support/types/gap.d.ts` — exports `GapRegisterEntry` matching `data-model.md` §2
- [ ] T039 [P] Type declaration `tests/e2e/web-coverage/_support/types/review.d.ts` — exports `ReviewVote`, `AgentObjection`, `KnownGoodManifest` matching `data-model.md` §§3–4, §9

### Validators (outcome-proxy + AWS + PSPF)

- [ ] T040 [P] Outcome-proxy validator `tests/e2e/web-coverage/_support/validators/outcome-proxy.ts` — implements all five proxies (lives, latency, evac lead, logistics clicks, SC-005 economic-loss formula `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30`)
- [ ] T041 [P] AWS CAP envelope validator `tests/e2e/web-coverage/_support/validators/aws-cap-envelope.ts` — asserts CAP v1.2 nested model (level + hazard/location + action statement), de-escalation chain, all-clear, hazard iconography (FR-011)
- [ ] T042 [P] PSPF classification validator `tests/e2e/web-coverage/_support/validators/pspf-classification.ts` — synthetic OFFICIAL:Sensitive / PROTECTED markers; gateway probe payload generator (FR-018(b))

### Accessibility wrappers

- [ ] T043 [P] Axe builder `tests/e2e/web-coverage/_support/a11y/axeBuilder.ts` — wraps `@axe-core/playwright` with WCAG 2.2 AA rule pack + critical-violation gate (R-007, FR-014, Q14)
- [ ] T044 [P] Language pack probe `tests/e2e/web-coverage/_support/a11y/languagePackProbe.ts` — toggles `en`, `zh-Hans`, `aus-x-atsi-placeholder` (R-008) and asserts payload variants

### Gap-register state machine + audit append (FR-005, R-009)

- [ ] T045 Implement `scripts/web-coverage/gap-register.py` — state-machine CLI with subcommands `open|progress|close|regress|validate|escalate`; enforces transitions per `data-model.md` §2 invariants table; writes markdown to `specs/034-webapp-capstone-coverage/gap-register.md` and appends JSONL to `audit/web-coverage-gaps/{date}/{hour}.jsonl`; validates entries against `contracts/gap-register-entry.schema.json` via `ajv` (Python `jsonschema` package)
- [ ] T046 [P] Shared audit-append helper `scripts/web-coverage/_lib/__init__.py` and `scripts/web-coverage/_lib/audit_append.py` — append-only JSONL writer (local fallback + Blob `web-coverage-evidence` container via managed identity); honours `AMA_AUDIT_FALLBACK=1` for offline dev
- [ ] T047 [P] Schema validator helper `scripts/web-coverage/_lib/schema_validators.py` — single entry point for validating `coverage-trace.json`, `gap-register.md`, review-log JSONL, and known-good.json against contracts via `jsonschema`

### Trace merge + known-good + review-log scaffolding

- [ ] T048 Implement `scripts/web-coverage/trace-merge.py` — reads N partial JSONs, dedupes by `(persona, outcome, hazard, fr_id)` joining `test_ids` with `;`, sorts deterministically, emits `specs/034-webapp-capstone-coverage/coverage-trace.json` + Markdown render `coverage-trace.md` (FR-004 column order); validates against `contracts/coverage-trace-row.schema.json`; idempotent — re-running on the same input MUST produce byte-equal output (SC-010, RISK-13)
- [ ] T049 [P] Implement `scripts/web-coverage/known-good.py` — manifest manager with `update` subcommand (called from cd.yml after `record-revisions`); writes `specs/034-webapp-capstone-coverage/known-good.json` matching `KnownGoodManifest` schema (data-model §4); computes `trace_hash = sha256(coverage-trace.json)`
- [ ] T050 [P] Implement `scripts/web-coverage/review-log.py` skeleton — `run` subcommand loads `.github/agents/{operational,sectors,technical}/**/*.agent.md`, ingests AgentObjection JSON sidecars, emits `specs/034-webapp-capstone-coverage/review-log.md`; panel-resolution stub (full logic in T140)
- [ ] T051 [P] Implement `scripts/web-coverage/verify-trace-determinism.ps1` — runs `trace-merge.py` twice on the same partials and asserts byte-equal output; surfaces `GAP-DET-TRACE-MERGE` on failure (RISK-13, SC-010)

### Seed-data extension

- [ ] T052 Extend `bootstrap_seed_data()` (`packages/domain/src/domain/seed/bootstrap.py` + driver `scripts/seed_loader.py`) to materialise: (a) the 68 persona identities (10 operational + 58 sector with persona-id matching agent file basenames; Commonwealth AFP keyed as `afp-commonwealth` to disambiguate from ACT `afp`); (b) 5 hazard-pair scenario seeds (one per outcome) with disaster + primary incident chain referenced by T028–T032 fixtures; (c) the AIIMS function map per `data-model.md` §5; idempotent re-execution required (FR-021, SC-010)

### Persona-fixture contract test (closure)

- [ ] T053 [P] Implement contract test `tests/e2e/web-coverage/_support/fixtures/__tests__/persona.contract.spec.ts` — drives all 68 persona ids through the fixture, asserts each resolves to a seeded identity with non-empty `permissions[]`, fails fast if any id is fixture-only (ASM-011 closure)

**Checkpoint**: Phase 2 complete. Foundation ready. Cross-cutting, persona, capstone, and CI work may now proceed in parallel.

---

## Phase 3: Cross-Cutting Suites (US2 + US4) 🎯 Cross-cutting MVP

**Goal**: Prove the constitutional baseline holds regardless of persona. Each spec is parameterised over ≥ 3 personas drawn from ≥ 3 jurisdictions per spec §User Story 2.

**Independent Test**: Run only `tests/e2e/web-coverage/cross-cutting/`; every file passes. Failure of any single file blocks the gate.

- [ ] T054 [P] [US2] `tests/e2e/web-coverage/cross-cutting/rbac-aiims.spec.ts` — AIIMS function map; positive (Control may approve) + negative (Logistics may NOT approve evacuation) tests parameterised over ≥ 3 personas × ≥ 3 jurisdictions (FR-007, II-A)
- [ ] T055 [P] [US2] `tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts` — asserts `≤ 5 s` COP refresh across incidents/jurisdictions/AIIMS functions; uses `expect.poll` with 5000ms ceiling (FR-008)
- [ ] T056 [P] [US2] `tests/e2e/web-coverage/cross-cutting/audit-append-only.spec.ts` — every state-changing action produces an audit entry within 2 s with rationale/confidence/source/operator identity; asserts PUT/PATCH against an audit_id is rejected and no row mutates (FR-010, edge-case "Audit timeline tampering attempt")
- [ ] T057 [P] [US2] `tests/e2e/web-coverage/cross-cutting/aws-warning-compliance.spec.ts` — three states (Advice / Watch and Act / Emergency Warning), nested model, hazard iconography, de-escalation, all-clear; parameterised across all 6 hazards including `earthquake/tsunami` (FR-011, V-A/V-B/V-C)
- [ ] T058 [P] [US2] `tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts` — Decision → Warning → Withdrawal → Shelter → Return; total/partial/phased + shelter-in-place + directed/recommended/self-initiated; vulnerable-population fields (ATSI, CALD, disability, children, older persons, homeless, tourists, institutional care) populated and filterable (FR-012, VI-A/B/C)
- [ ] T059 [P] [US2] `tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts` — four environments (Social, Built, Economic, Natural) tracked + managed handover from response → recovery; ≥ 3 data sources per environment (FR-013, FR-018(a), VII)
- [ ] T060 [P] [US2] `tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts` — WCAG 2.2 AA conformance via `axeBuilder` on every P1 surface enumerated in FR-014 (workspaces, governance dashboards, warning-composition, simulations, audit-timeline); `en`+`zh-Hans`+`aus-x-atsi-placeholder` rendered on ≥ 1 warning per hazard category; emits `GAP-A11Y-WORKSPACE` on failure (FR-014, Q14, Q2)
- [ ] T061 [P] [US2] `tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts` — queue-and-sync, idempotent dedupe by client correlation ID, conservative life-safety defaults, offline banner; replay test asserts queued action syncs into immutable audit with original timestamp + authorship (FR-017, NN-#5, edge-case "Offline field coordinator submits a duplicate")
- [ ] T062 [P] [US2] `tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts` — three contractual assertions: (a) AU-region badge/banner on every regulated route + Foundry carve-out list reachable from `/governance/dashboard/compliance`; (b) PSPF/PII payload denied at gateway (FR-018(b) probe via `pspf-classification.ts`); (c) carve-out YAML `review_date` ≤ 90 days + non-empty approvers (FR-018, NN-#2)
- [ ] T063 [P] [US2] `tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts` — command-side persona with > 7 direct reports surfaces a warning before save; asserts warning text + delegation prompt; parameterised over IC (Tier-1) + Operations Officer + Logistics Officer (Tier-2 when supervising direct reports). Planning Officer + remaining personas covered as N/A negative test (FR-020, Clarifications Q9)
- [ ] T064 [P] [US2] `tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts` — every safety-critical action gated by IC approval; positive (approval succeeds, identity logged) + negative (no approval = no execution); deterministic structured-JSON HITL output (FR-009, NN-#1, RISK-02)
- [ ] T065 [P] [US2] `tests/e2e/web-coverage/cross-cutting/data-source-multiplicity.spec.ts` — each persona scenario asserts ≥ 3 named data sources surfaced in COP/governance views (FR-018(a))
- [ ] T066 [P] [US2] `tests/e2e/web-coverage/cross-cutting/audit-trail.spec.ts` — append-only timeline view + correlation_id propagation visible at `/governance/dashboard/audit` (Constitution §IV)
- [ ] T067 [P] [US4] `tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts` — `/simulations/create` → `/simulations/[tenantId]/playback`; deterministic replay with byte-identical asserted properties on second run (FR-006 Response/Recovery, US4 Acceptance #1–#2)
- [ ] T068 [P] [US4] `tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts` — `/simulations/reports/[reportId]` export includes lessons identified, mapped to preparedness controls in `/preparedness` (FR-006 PPRR loop closure, US4 Acceptance #3)

**Checkpoint**: Phase 3 complete. US2 + US4 are independently testable.

---

## Phase 4: Persona Scenarios (US1 + US3)

**Goal**: ≥ 1 passing persona scenario per FR-002 inventory (10 operational + 58 sector = 68) + ≥ 1 cross-jurisdiction integration per state/territory + ≥ 1 Commonwealth-bridge per FR-003. Each scenario asserts at least one outcome-proxy metric and writes a trace row tagged `@outcome:N @hazard:X+Y @fr:FR-NNN`.

**Independent Test**: For any persona ID drawn from the 68, locate the file, run it, confirm it (a) loads `/workspaces/[personaId]`, (b) performs the persona's must-do actions per the cited input file, (c) asserts an outcome-proxy metric within SC-001..SC-005 budgets, (d) writes the audit entry within 2 s.

### 4.1 Operational personas (10) — `tests/e2e/web-coverage/operational/`

- [ ] T069 [P] [US1] `operational/incident-commander.approve-cross-agency-action.spec.ts` — IC approves cross-agency action; outcome-1 (lives) + outcome-2 (latency); `@persona:incident-commander @outcome:1 @hazard:bushfire+extreme-heat @fr:FR-009 @clause:I @clause:NN-1` (Spec §US1 Acceptance #1)
- [ ] T070 [P] [US1] `operational/operations-officer.tactical-tasking.spec.ts` — Operations Officer issues tasking, signal-to-action ≤ 5/15/30 min for Levels 1/2/3; `@outcome:2 @hazard:bushfire+severe-storm @fr:FR-008`
- [ ] T071 [P] [US1] `operational/planning-officer.predictive-risk-evac.spec.ts` — Planning Officer drives predictive risk → 24-h-earlier evacuation lead-time proxy; `@outcome:3 @hazard:tropical-cyclone+riverine-flood @fr:FR-016`
- [ ] T072 [P] [US1] `operational/logistics-officer.mutual-aid-lifecycle.spec.ts` — Logistics Officer drives mutual-aid request through approval; clicks ≤ 12 (SC-004); `@outcome:4 @hazard:bushfire+tropical-cyclone @fr:FR-015`
- [ ] T073 [P] [US1] `operational/public-information-officer.aws-multilingual-warning.spec.ts` — PIO drafts AWS warning with `en` + `zh-Hans` + `aus-x-atsi-placeholder`; IC approval required; `@outcome:1 @hazard:bushfire+extreme-heat @fr:FR-011 @fr:FR-014`
- [ ] T074 [P] [US1] `operational/field-coordinator.offline-gps-hazard-report.spec.ts` — Field Coordinator captures GPS-tagged hazard report offline, syncs on reconnect; `@outcome:2 @hazard:bushfire+severe-storm @fr:FR-017`
- [ ] T075 [P] [US1] `operational/resilience-planner.recovery-handover.spec.ts` — Resilience Planner drives response→recovery handover; SC-005 economic-loss proxy ≥ 30 %; `@outcome:5 @hazard:riverine-flood+severe-storm @fr:FR-013`
- [ ] T076 [P] [US1] `operational/executive-leader.economic-environment-view.spec.ts` — Executive views post-handover Economic-environment view, asserts SC-005 formula; `@outcome:5 @hazard:riverine-flood+severe-storm @fr:FR-013`
- [ ] T077 [P] [US1] `operational/observer-auditor.append-only-timeline.spec.ts` — Observer/Auditor inspects audit timeline, asserts immutability (PUT/PATCH rejected); `@outcome:4 @hazard:bushfire+tropical-cyclone @fr:FR-010 @clause:IV`
- [ ] T078 [P] [US1] `operational/risk-manager.predictive-evac-lead.spec.ts` — Risk Manager validates 24-h-earlier evacuation proxy on cyclone+flood scenario; `@outcome:3 @hazard:tropical-cyclone+riverine-flood @fr:FR-016`

### 4.2 NSW (6) — `tests/e2e/web-coverage/sectors/nsw/`

- [ ] T079 [P] [US1] `sectors/nsw/nsw-rfs.bushfire-incident-action-plan.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T080 [P] [US1] `sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts` — Watch and Act flood warning + 24-h-earlier evac lead-time proxy (Spec §US1 Acceptance #2); `@outcome:3 @hazard:tropical-cyclone+riverine-flood @fr:FR-011 @fr:FR-016`
- [ ] T081 [P] [US1] `sectors/nsw/nsw-ambulance.mass-casualty-triage.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T082 [P] [US1] `sectors/nsw/nswpf.evacuation-cordon.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T083 [P] [US1] `sectors/nsw/frnsw.urban-fire-response.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T084 [P] [US1] `sectors/nsw/mrnsw.maritime-flood-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`

### 4.3 VIC (5) — `tests/e2e/web-coverage/sectors/vic/`

- [ ] T085 [P] [US1] `sectors/vic/cfa-vic.code-red-day.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T086 [P] [US1] `sectors/vic/ses-vic.flash-flood-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T087 [P] [US1] `sectors/vic/av.heat-related-illness-surge.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T088 [P] [US1] `sectors/vic/vicpol.cross-border-evac.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T089 [P] [US1] `sectors/vic/frv.warehouse-fire-haz-mat.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.4 QLD (4) — `tests/e2e/web-coverage/sectors/qld/`

- [ ] T090 [P] [US1] `sectors/qld/qfd.cyclone-pre-positioning.spec.ts` — `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [ ] T091 [P] [US1] `sectors/qld/ses-qld.tropical-cyclone-flood.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T092 [P] [US1] `sectors/qld/qas.heat-stress-mass-casualty.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T093 [P] [US1] `sectors/qld/qps.evac-traffic-management.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`

### 4.5 SA (5) — `tests/e2e/web-coverage/sectors/sa/`

- [ ] T094 [P] [US1] `sectors/sa/sacfs.code-red-bushfire.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T095 [P] [US1] `sectors/sa/ses-sa.river-murray-flood.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T096 [P] [US1] `sectors/sa/saas.extreme-heat-mass-call.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T097 [P] [US1] `sectors/sa/sapol.cross-border-evac.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T098 [P] [US1] `sectors/sa/samfs.urban-fire-multi-storey.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.6 WA (3) — `tests/e2e/web-coverage/sectors/wa/`

- [ ] T099 [P] [US1] `sectors/wa/dfes-wa.cyclone-pilbara.spec.ts` — `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [ ] T100 [P] [US1] `sectors/wa/sja-wa.remote-medical-evac.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T101 [P] [US1] `sectors/wa/wapol.remote-evac-cordon.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`

### 4.7 TAS (4) — `tests/e2e/web-coverage/sectors/tas/`

- [ ] T102 [P] [US1] `sectors/tas/tfs.bushfire-island-evac.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T103 [P] [US1] `sectors/tas/ses-tas.severe-storm-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T104 [P] [US1] `sectors/tas/at.aeromedical-retrieval.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T105 [P] [US1] `sectors/tas/taspol.island-evac-coordination.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`

### 4.8 ACT (7) — `tests/e2e/web-coverage/sectors/act/`

- [ ] T106 [P] [US1] `sectors/act/act-esa.multi-agency-coordination.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T107 [P] [US1] `sectors/act/act-fr.urban-fire.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T108 [P] [US1] `sectors/act/act-ambulance.heat-surge.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T109 [P] [US1] `sectors/act/act-policing.evac-cordon.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T110 [P] [US1] `sectors/act/act-rfs.bushfire-pre-positioning.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T111 [P] [US1] `sectors/act/afp.protective-services.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T112 [P] [US1] `sectors/act/ses-act.severe-storm-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`

### 4.9 NT (5) — `tests/e2e/web-coverage/sectors/nt/`

- [ ] T113 [P] [US1] `sectors/nt/bushfires-nt.savanna-burn.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T114 [P] [US1] `sectors/nt/ntes.cyclone-shelter.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T115 [P] [US1] `sectors/nt/ntfrs.remote-fire-response.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T116 [P] [US1] `sectors/nt/ntpf.remote-evac.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [ ] T117 [P] [US1] `sectors/nt/sja-nt.remote-medical-retrieval.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.10 Commonwealth (11) — `tests/e2e/web-coverage/sectors/commonwealth/`

- [ ] T118 [P] [US1] `sectors/commonwealth/nema.activate-comdisplan.spec.ts` — Activates COMDISPLAN, opens NJCOP, requests consequence metrics, asserts logistics-match efficiency proxy (Spec §US1 Acceptance #3); `@outcome:4 @hazard:bushfire+tropical-cyclone @fr:FR-015`
- [ ] T119 [P] [US1] `sectors/commonwealth/bom-national.cyclone-warning-relay.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T120 [P] [US1] `sectors/commonwealth/ga-national.tsunami-warning-relay.spec.ts` — Earthquake/tsunami AWS path (FR-011 only, not paired with capstone outcome); `@hazard:earthquake @hazard:tsunami @aws @fr:FR-011`
- [ ] T121 [P] [US1] `sectors/commonwealth/adf.dacc-asset-arrival.spec.ts` — DACC categorisation (A/B/C), asset arrival tracking; `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [ ] T122 [P] [US1] `sectors/commonwealth/abf.border-disaster-coordination.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T123 [P] [US1] `sectors/commonwealth/arc.recovery-financial-assistance.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T124 [P] [US1] `sectors/commonwealth/asa.shipping-evac.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T125 [P] [US1] `sectors/commonwealth/rfds.remote-aeromedical.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T126 [P] [US1] `sectors/commonwealth/sja-national.community-first-aid.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T127 [P] [US1] `sectors/commonwealth/surf-lifesaving.coastal-cyclone-evac.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [ ] T128 [P] [US1] `sectors/commonwealth/afp-commonwealth.national-evac-coordination.spec.ts` — Persona-id `afp-commonwealth` to disambiguate from ACT `afp` (T111); seeded by T052; `@outcome:2 @hazard:bushfire+severe-storm`

### 4.11 Cross-sector (8) — `tests/e2e/web-coverage/sectors/cross-sector/`

- [ ] T129 [P] [US1] `sectors/cross-sector/community-ngos.recovery-coordination.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T130 [P] [US1] `sectors/cross-sector/health.surge-capacity.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [ ] T131 [P] [US1] `sectors/cross-sector/local-government.recovery-funding.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T132 [P] [US1] `sectors/cross-sector/state-government.disaster-declaration.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T133 [P] [US1] `sectors/cross-sector/territory-government.cross-jurisdiction-coord.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T134 [P] [US1] `sectors/cross-sector/transport.evac-routing.spec.ts` — `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [ ] T135 [P] [US1] `sectors/cross-sector/utility.power-restoration.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [ ] T136 [P] [US1] `sectors/cross-sector/volunteer.surge-deployment.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.12 Cross-jurisdiction integration (FR-003 — 8 state/territory + 1 Commonwealth bridge)

- [ ] T137 [P] [US3] `sectors/nsw/cross-jurisdiction-nsw-vic-bushfire.spec.ts` — bushfire crosses NSW→VIC border; both NSW RFS + CFA see same incident COP, AWS warning state, audit history (Spec §US3 Acceptance #1); `@fr:FR-015`
- [ ] T138 [P] [US3] `sectors/vic/cross-jurisdiction-vic-tas-storm.spec.ts` — severe-storm bridge VIC↔TAS; `@fr:FR-015`
- [ ] T139 [P] [US3] `sectors/qld/cross-jurisdiction-qld-nsw-cyclone-flood.spec.ts` — SES-QLD ↔ SES-NSW for tropical-cyclone flooding at border; `@fr:FR-015`
- [ ] T140 [P] [US3] `sectors/sa/cross-jurisdiction-sa-vic-bushfire.spec.ts` — SA ↔ VIC bushfire bridge; `@fr:FR-015`
- [ ] T141 [P] [US3] `sectors/wa/cross-jurisdiction-wa-sa-flood.spec.ts` — WA ↔ SA flood bridge; `@fr:FR-015`
- [ ] T142 [P] [US3] `sectors/tas/cross-jurisdiction-tas-mainland-cyclone.spec.ts` — Tasmania mainland-link evac; `@fr:FR-015`
- [ ] T143 [P] [US3] `sectors/act/cross-jurisdiction-act-nsw-bushfire.spec.ts` — ACT ↔ NSW bushfire bridge; `@fr:FR-015`
- [ ] T144 [P] [US3] `sectors/nt/cross-jurisdiction-nt-wa-bushfire-cyclone.spec.ts` — NT ↔ WA bushfire/cyclone bridge; `@fr:FR-015`
- [ ] T145 [P] [US3] `sectors/commonwealth/nema.dacc-state-controller-bridge.spec.ts` — Commonwealth bridge: state controller → NEMA → ADF DACC lifecycle (COMDISPLAN activation, DACC categorisation A/B/C, mission-close report) (Spec §US3 Acceptance #2); `@fr:FR-015`

**Checkpoint**: Phase 4 complete. US1 + US3 are independently testable. The 68-persona inventory + 9 cross-jurisdiction scenarios fulfil FR-002 + FR-003.

---

## Phase 5: Capstone Outcome Suites (US1 closure)

**Goal**: Each capstone outcome (#1..#5) has ≥ 1 traceable passing assertion that closes the trace at the **outcome level** (FR-023(d)), aggregating signals from the persona scenarios via the trace emitter.

**Independent Test**: Run only `tests/e2e/web-coverage/capstone/`; every file passes. Each spec asserts the SC-001..SC-005 outcome-proxy threshold against the corresponding hazard-pair fixture and closes the trace.

- [ ] T146 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts` — Lives saved (zero preventable deaths); proxy = warning latency + IC-approval timeliness + multilingual reach within 2 min (SC-001); validates with `outcome-proxy.ts.lives` against `outcome-1-*.fixture.json`
- [ ] T147 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-2-bushfire-severe-storm.spec.ts` — 50 % faster signal-to-action; proxy = AIIMS Level 1/2/3 latencies ≤ 5/15/30 min (SC-002)
- [ ] T148 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-3-tropical-cyclone-flood.spec.ts` — 24-h-earlier evacuation; proxy = `evac_lead_hours ≥ 24` vs seed reference (SC-003)
- [ ] T149 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-4-bushfire-cyclone-logistics.spec.ts` — 30 % logistics-friction reduction; proxy = `logistics_clicks ≤ 7` routine / `≤ 12` mutual-aid (SC-004)
- [ ] T150 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts` — 30 % economic-loss reduction; proxy = `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30` evaluated at response→recovery handover on the post-handover Economic-environment view (SC-005, Q7)

**Checkpoint**: Phase 5 complete. Trace closes at the capstone-outcome level. US1 is fully provable end-to-end.

---

## Phase 6: CI Gate Wiring (US5)

**Goal**: Suite functions as a binary CI quality gate (FR-023). Three new jobs added to `.github/workflows/ci.yml`; one step appended to `.github/workflows/cd.yml`. ≤ 45 min wall-clock CI budget; 4 shards on `ubuntu-latest`.

- [ ] T151 [US5] Extend `.github/workflows/ci.yml` with `web-coverage-shard` job — `needs: [quality]`, `runs-on: ubuntu-latest`, `timeout-minutes: 45`, `strategy.matrix.shard: [1,2,3,4]`, `fail-fast: false`; steps per plan §CI Integration: `actions/checkout@v4`, `actions/setup-node@v4` (node 24 + pnpm cache), `actions/setup-python@v5` (3.12 + pip cache), `actions/cache@v4` keyed on `${{ runner.os }}-pw-${{ hashFiles('apps/web/pnpm-lock.yaml') }}`, `pnpm install --frozen-lockfile`, `python -m pip install -e apps/api`, `pnpm exec playwright install --with-deps chromium`, `pwsh scripts/seed-database.ps1`, `corepack pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --shard=${{ matrix.shard }}/4`; uploads partial JSON + JUnit + redacted screenshots via `actions/upload-artifact@v4`
- [ ] T152 [US5] Extend `.github/workflows/ci.yml` with `web-coverage-merge` job — `needs: [web-coverage-shard]`; downloads all 4 shard artefacts; runs `python scripts/web-coverage/trace-merge.py --inputs tests/e2e/web-coverage/_artifacts/coverage-trace.partial-*.json --out-md specs/034-webapp-capstone-coverage/coverage-trace.md --out-json specs/034-webapp-capstone-coverage/coverage-trace.json`; runs `python scripts/web-coverage/gap-register.py validate`; runs `pwsh scripts/web-coverage/verify-trace-determinism.ps1`; uploads canonical artefacts
- [ ] T153 [US5] Extend `.github/workflows/ci.yml` with `web-coverage-gate` job — `needs: [web-coverage-merge]`; validates `coverage-trace.json` against `contracts/coverage-trace-row.schema.json` via `python scripts/web-coverage/_lib/schema_validators.py`; fails if any row `status == "failing"`; fails if persona inventory < 68 OR state/territory cross-jurisdiction count < 8 OR Commonwealth-bridge < 1 OR capstone outcomes < 5; fails if gap-register has any `Open` entry (FR-023(e)); posts GitHub status check `web-coverage / capstone-ready`
- [ ] T154 [US5] Mark all three jobs as **required** for merge to `main` via `.github/branch-protection.json` (or repo settings reference); document in `specs/034-webapp-capstone-coverage/known-good.json` README header
- [ ] T155 [US5] Append step `Update FR-027 known-good manifest` to `.github/workflows/cd.yml` immediately after the existing `record-revisions` step (lines 238–264) — runs `python scripts/web-coverage/known-good.py update --commit "${{ github.sha }}" --revisions-json "${{ steps.record-revisions.outputs.json }}" --trace specs/034-webapp-capstone-coverage/coverage-trace.json` and commits via `ama-bot` with `[skip ci]` trailer
- [ ] T156 [P] [US5] Add `apps/web/package.json` scripts: `"test:web-coverage"`, `"test:web-coverage:p1"` (--grep "@p1"), `"test:web-coverage:axe"` (--project=web-coverage-axe), `"test:web-coverage:shard"` (parametric)

**Checkpoint**: Phase 6 complete. CI gate is active; PRs cannot merge to `main` while any `Failing` row or `Open` gap exists.

---

## Phase 7: Iteration Loop Tooling (US5)

**Goal**: 85-agent tribunal converts objections → spec amendments → re-runs; max 3 cycles before escalation (FR-024); regressions auto-rolled back to known-good revision (FR-027).

- [ ] T157 [US5] Implement vote-recording subcommand `python scripts/web-coverage/review-log.py vote --gap-id … --agent-id … --vote {approve|object|abstain} --rationale "…"` — appends a `ReviewVote` row to `specs/034-webapp-capstone-coverage/review-log.md` and JSONL audit shadow; validates against `contracts/review-vote.schema.json` (data-model §3, ASM-006, Q13)
- [ ] T158 [US5] Implement panel-resolver inside `scripts/web-coverage/review-log.py` — computes `meritorious` (≥ 2/3 of relevant panel), operational-panel veto on safety-critical clauses {I, IV, NN-1, NN-2, QG-1}, override-supermajority (≥ 50 % of all 85 agents); writes resolution to vote rows + emits PR-ready spec amendments under `specs/034-webapp-capstone-coverage/diffs/` (Q13)
- [ ] T159 [US5] Implement FR-024 max-3-cycles guard inside `scripts/web-coverage/gap-register.py escalate` subcommand — when `iteration_count >= 4`, transitions gap to `Escalated`, freezes counter, appends `gap.escalated` audit, halts further automated cycles for that gap (Spec §US5 Acceptance #3, Q5, Q6)
- [ ] T160 [US5] Implement FR-027 known-good rollback CLI `python scripts/web-coverage/known-good.py rollback --gap-id … --failing-test-id … --reverted-sha … --restored-sha …` — composes with `cd.yml` 5-min auto-rollback; updates `KnownGoodManifest.last_regression`; appends rollback evidence (failing Test ID, reverted commit SHA, restored revision SHA) to audit timeline (Spec §US5 Acceptance #4, FR-027)
- [ ] T161 [US5] Wire FR-027 rollback evidence capture into `gap-register.py regress` subcommand — populates `regression_evidence` block on `Closed → Reopened` transition, resets `iteration_count` to 0, tags row `regression_detected` (data-model §2 invariants table)
- [ ] T162 [P] [US5] Author `.github/workflows/web-coverage-iteration.yml` (single new workflow file per plan §CI Integration §`web-coverage-iteration.yml`) — `schedule: cron: "0 16 * * *"` (02:00 AEST), `workflow_dispatch.inputs.gap_id`, `pull_request: types: [closed], paths: ["specs/034-**"]`; runs `review-log.py run --trace … --gaps … --agents .github/agents/`; opens follow-up PRs as `ama-bot`
- [ ] T163 [P] [US5] Generate agent-objection sidecar template `scripts/web-coverage/agent-objection-template.json` matching `contracts/agent-objection.schema.json`; document the format in `.github/agents/_subagents/web-coverage-objection-format.md`

**Checkpoint**: Phase 7 complete. US5 closes: gate is active, iteration loop runs nightly, max-3-cycles + regression rollback are enforced.

---

## Phase 8: Documentation & Polish

**Purpose**: Finalise human-facing artefacts; populate skeletons; capture grading evidence.

- [ ] T164 [P] Update `specs/034-webapp-capstone-coverage/quickstart.md` with any deltas surfaced during implementation (paths, env vars, troubleshooting); add a "Known limitations" section if gaps remain on first pass
- [ ] T165 [P] Add a "Web coverage suite" section to repo `README.md` linking to `specs/034-webapp-capstone-coverage/quickstart.md` with a 5-line snippet for running the `@p1` smoke locally
- [ ] T166 [P] Author `tests/e2e/web-coverage/README.md` documenting: tag taxonomy (R-017), persona-id-to-spec mapping (10 + 58 = 68), hazard-pair fixture index, ESLint determinism rules
- [ ] T167 [P] Generate initial `specs/034-webapp-capstone-coverage/known-good.json` skeleton matching `KnownGoodManifest` schema with `version: 1`, current commit SHA, empty `last_regression: null`; cd.yml will refresh on first deploy (T155)
- [ ] T168 [P] Author `specs/034-webapp-capstone-coverage/review-log.md` skeleton with cycle 0 header (date, suite-run id placeholder, panel sign-off rows for operational/sector/technical)
- [ ] T169 [P] Author `specs/034-webapp-capstone-coverage/coverage-trace.md` placeholder with column header row only (`Persona | Outcome | Hazard | FR | Test ID | Route | Audit Evidence ID | Status`); first real run will replace via T152
- [ ] T170 [P] Initialise `specs/034-webapp-capstone-coverage/gap-register.md` with empty Markdown table + `GAP-AI-CONTENT-SAFETY-CANDIDATE` row in `Open` state per plan §Conditionally proposed
- [ ] T171 Run `pwsh scripts/web-coverage/verify-trace-determinism.ps1` locally + `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --grep "@p1"` and capture run output to `specs/034-webapp-capstone-coverage/_evidence/first-run.log` (RISK-12 redaction applied)
- [ ] T172 [P] Cross-link this tasks.md from `specs/034-webapp-capstone-coverage/checklists/validation.md` CHK-IDs (CHK034, CHK045, CHK090, CHK130, CHK160) so iteration-loop runners can mark gates without re-tracing

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)              ──▶ Phase 2 (Foundational)
Phase 2 (Foundational)       ──▶ Phase 3 (Cross-cutting)
                                ▷ Phase 4 (Persona)
                                ▷ Phase 5 (Capstone)
Phase 3 + Phase 4 + Phase 5  ──▶ Phase 6 (CI gate wiring)
Phase 6                       ──▶ Phase 7 (Iteration loop)
Any/all                       ──▶ Phase 8 (Polish)
```

### Hard intra-phase dependencies (within Phase 2)

- **T007 → T008 → T009 → T010** (test-support guard before router before main wiring before contract test)
- **T011 → T012 → T013** (Bicep child resource before RBAC scope before what-if validation)
- **T014..T022** (page objects) MAY run in parallel; ALL block all `*.spec.ts` consumers
- **T023..T027** (fixtures) depend on T008 (test-support endpoint) and T052 (seed data); MAY run in parallel with each other once T008 + T052 land
- **T033 → T034..T039** (custom reporter ships first; helpers and types in parallel after)
- **T045 → T046 → T047** (gap-register CLI before audit-append helper before schema validators)
- **T048 → T049 → T050** (trace-merge CLI before known-good before review-log skeleton — share `_lib/audit_append.py`)
- **T052** (seed-data extension) is the long-pole prerequisite for ALL Phase 3/4/5 specs; schedule it first inside Phase 2

### Hard intra-phase dependencies (within Phase 6)

- **T151 → T152 → T153** (shard → merge → gate)
- **T155** depends on T049 + T155 sequencing on `cd.yml` `record-revisions` line 238–264

### Hard intra-phase dependencies (within Phase 7)

- **T157 → T158** (vote recorder before panel resolver, both share `review-log.py`)
- **T159 → T161** (escalate guard ships before regress integration both edit `gap-register.py`)
- **T160 → T161** (rollback CLI ships before evidence-capture wiring)

### User Story Dependencies

- **US1 (Persona traceability)** — depends on Phase 2 foundational + Phase 4 personas + Phase 5 capstone
- **US2 (Cross-cutting guarantees)** — depends on Phase 2 foundational + Phase 3 cross-cutting; independently testable from US1
- **US3 (Cross-jurisdiction integration)** — depends on Phase 2 foundational + T137..T145 (subset of Phase 4); independently testable
- **US4 (Simulation/lessons)** — depends on Phase 2 foundational + T067 + T068 (subset of Phase 3); independently testable
- **US5 (Quality gate + iteration loop)** — depends on Phases 1–5 (consumes their outputs) + Phase 6 + Phase 7

### Parallel Opportunities

- All 9 page objects (T014..T022) — independent files
- All 5 fixtures (T023..T027) — independent files (after T008 + T052)
- All 5 hazard-pair fixture data files (T028..T032) — independent JSON files
- All 13 cross-cutting specs (T054..T068) — independent files
- All 77 persona-scenario specs (T069..T145) — independent files
- All 5 capstone-outcome specs (T146..T150) — independent files
- All Phase 8 doc tasks (T164..T172 except T171) — independent files

### Parallel example — Phase 2 fixtures + page objects

```bash
# After T008 (test-support router) and T052 (seed-data extension) complete:
Task: "Page object workspaces.po.ts"        # T014
Task: "Page object incidents.po.ts"         # T015
Task: "Page object disasters.po.ts"         # T016
Task: "Page object governance.dashboard.po" # T017
Task: "Persona fixture"                     # T023
Task: "Hazard-scenario fixture"             # T024
Task: "Correlation-id fixture"              # T025
Task: "Audit-observer fixture"              # T026
Task: "Carve-out registry fixture"          # T027
```

### Parallel example — Phase 4 entire NSW jurisdiction

```bash
# After Phase 2 + Phase 3 land:
Task: "T079 nsw-rfs.bushfire-incident-action-plan.spec.ts"
Task: "T080 ses-nsw.watch-and-act-flood.spec.ts"
Task: "T081 nsw-ambulance.mass-casualty-triage.spec.ts"
Task: "T082 nswpf.evacuation-cordon.spec.ts"
Task: "T083 frnsw.urban-fire-response.spec.ts"
Task: "T084 mrnsw.maritime-flood-rescue.spec.ts"
```

---

## Implementation Strategy

### MVP first (User Story 1 + Phase 2 + Phase 3 cross-cutting baseline)

1. Complete Phase 1: Setup (T001–T006) — single dev session
2. Complete Phase 2: Foundational (T007–T053) — long-pole; schedule T052 (seed extension) first
3. Complete Phase 3 cross-cutting (T054–T066) — provides the constitutional baseline
4. Land 10 operational personas (T069–T078) and 5 capstone outcomes (T146–T150)
5. **STOP and VALIDATE**: re-run trace merge, confirm trace closes for outcomes #1..#5 against operational personas; commit gap-register with any open issues; demo to project lead

### Incremental delivery (priority order P1 → P5)

1. MVP (above) → 10 + 5 + cross-cutting passing → demo to project lead
2. Add NSW + VIC personas (T079–T089) → trace closes for the two highest-population states → demo
3. Add QLD + SA + WA + TAS personas (T090–T105) → trace closes for southern/eastern AU → demo
4. Add ACT + NT personas (T106–T117) → trace closes for territories → demo
5. Add Commonwealth + Cross-sector (T118–T136) → trace closes for the entire 68 → demo
6. Add cross-jurisdiction scenarios (T137–T145) → US3 closes → demo
7. Add CI gate (Phase 6) → suite becomes a hard gate → first `Capstone Ready` PR
8. Add iteration loop (Phase 7) → 85-agent tribunal active → demo
9. Polish (Phase 8) → submit for `/speckit.analyze`

### Parallel team strategy

With multiple developers:
1. Dev A: Phase 2 foundational (T007–T053), long-pole
2. Dev B: Phase 1 setup + Phase 8 skeletons (T001–T006, T167–T170) — unblocks early
3. Dev C..F: 4 jurisdictions in parallel once Phase 2 lands (e.g., NSW+VIC vs QLD+SA vs WA+TAS+ACT vs NT+Commonwealth+CrossSector)
4. Dev A: Phase 6 + Phase 7 once trace closes locally for ≥ 1 outcome
5. Dev B: Polish + grading evidence (T171–T172)

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks in the same response
- `[Story]` label maps each task to one of the 5 user stories from `spec.md`
- Foundation, CI, iteration loop, and polish phases carry no story label per template convention
- Every persona scenario MUST emit ≥ 1 `coverageRow` annotation tagged with `@persona`, `@outcome`, `@hazard`, `@fr`, and at least one `@clause`
- Tests MUST NOT use `page.waitForTimeout` — enforced by ESLint rule T006
- Re-running `python scripts/web-coverage/trace-merge.py` on the same partial JSON inputs MUST produce byte-equal output (SC-010, RISK-13)
- Persona scenarios use only seeded identities from `bootstrap_seed_data()` — no fixture-only identities (ASM-011)
- The test-support endpoint is **never** registered in production (T007 dual-guard middleware verifies)
- All artefact uploads pass through `redact.ts` (T036) before `actions/upload-artifact` (RISK-07, R-016)
- Gap-register transitions are **append-only** in the JSONL audit shadow (T046); the markdown render is the human-readable mirror
- All five capstone outcome proxies use the seed-fixture baselines (T028–T032) — `(baseline − projected) / baseline ≥ 0.30` for SC-005 economic-loss

---

**End of tasks.md** — Total: 172 tasks. Ready for `/speckit.analyze`.

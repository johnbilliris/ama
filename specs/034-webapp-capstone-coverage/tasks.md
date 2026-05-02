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

- [X] T001 Create directory tree `tests/e2e/web-coverage/{operational,sectors/{nsw,vic,qld,sa,wa,tas,act,nt,commonwealth,cross-sector},cross-cutting,capstone,_support/{pages,fixtures,fixtures/data,reporter,validators,a11y,types,eslint-rules},_artifacts/{junit,screenshots}}` and `scripts/web-coverage/_lib/`
- [X] T002 Add devDependencies `@axe-core/playwright@^4.10.0`, `js-yaml@^4`, `ajv@^8`, `ajv-formats@^3` to `apps/web/package.json`; pin Playwright at `1.59.1`; run `pnpm install --filter @ama/web` and commit lockfile delta
- [X] T003 [P] Add path alias `@web-coverage/*` → `tests/e2e/web-coverage/_support/*` in `apps/web/tsconfig.json` and matching alias in `apps/web/playwright.config.ts`
- [X] T004 [P] Append `tests/e2e/web-coverage/_artifacts/` and `tests/e2e/web-coverage/**/*.partial-*.json` to `.gitignore`; explicitly NOT-ignore `specs/034-webapp-capstone-coverage/coverage-trace.{md,json}` and `gap-register.md`
- [X] T005 Extend `apps/web/playwright.config.ts` with three new `projects` entries — `web-coverage-chromium` (default), `web-coverage-mobile` (Pixel 7 emulation), `web-coverage-axe` (WCAG run); preserve existing legacy project list; wire `reporter` to `[['junit', { outputFile: 'tests/e2e/web-coverage/_artifacts/junit/results.xml' }], ['json', { outputFile: 'tests/e2e/web-coverage/_artifacts/playwright.json' }], ['./tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts']]`; set `forbidOnly: !!process.env.CI`, `retries: 0` on PR, `workers: process.env.CI ? 4 : 4`, base URL `http://127.0.0.1:3000`
- [X] T006 [P] Author ESLint rule `tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs` (forbids `page.waitForTimeout`, R-015); register in `apps/web/.eslintrc.cjs` `rules` block scoped to `tests/e2e/web-coverage/**`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Test-support endpoint, Bicep child resource, page objects, fixtures, custom reporter, validators, gap-register CLI, trace-merge CLI, schema validators, seed-data extension. **No persona, cross-cutting, or capstone task may begin until this phase is complete.**

### Test-support endpoint (per `contracts/persona-fixture.contract.md`)

- [X] T007 Implement `apps/api/app/middleware/test_support_guard.py` — dual-guard middleware (refuses requests when `settings.environment == "production"` OR `os.environ.get("AMA_TEST_SUPPORT") != "1"`); emits structured `test-support disabled: environment=… AMA_TEST_SUPPORT=…` log on startup
- [X] T008 Implement `apps/api/app/api/routes/test_support.py` — FastAPI router exposing `GET /api/test-support/personas`, `GET /api/test-support/personas/{persona_id}`, `POST /api/test-support/seed/scenario`; reads identities only from `bootstrap_seed_data().identities` (ASM-011); returns shape per `contracts/persona-fixture.contract.md` lines 50–80
- [X] T009 Wire test-support router into `apps/api/app/main.py` — conditional `include_router` gated by `test_support_guard.is_enabled()`; ensure no router registration when disabled (404 path); update `apps/api/app/api/router.py` aggregator
- [X] T010 [P] Author contract test `apps/api/tests/test_test_support_router.py` asserting (a) 404 when `AMA_TEST_SUPPORT` unset, (b) 404 when `settings.environment == "production"` regardless of env var, (c) 200 + correct shape when both guards green, (d) refuses to mutate seed data on any verb

### Net-new Azure infrastructure (Bicep + RBAC)

- [X] T011 [P] Add Bicep child resource `web-coverage-evidence` blob container + 7-year `immutabilityPolicy` (`allowProtectedAppendWrites: true`) to `infra/bicep/main.bicep` (insert under existing `storageBlob` parent); follow plan §Net-New Azure Resources HCL example verbatim; output container resourceId for downstream RBAC binding
- [X] T012 [P] Extend the API Container App's managed-identity role assignment in `infra/bicep/modules/identity.bicep` (or equivalent existing assignments file) — grant `Storage Blob Data Contributor` (`ba92f5b4-2d11-453d-a403-e96b0029c9fe`) scoped **only** to the `web-coverage-evidence` container resourceId from T011; verify with `verify-iam-zero-trust.ps1` (RISK-10)
- [X] T013 [P] Run `bicep build infra/bicep/main.bicep` and `az deployment group what-if` against the dev subscription; capture the diff in `specs/034-webapp-capstone-coverage/bicep-whatif.txt` for grading evidence

### Page objects (one per route in plan §Module Breakdown)

- [X] T014 [P] Page object `tests/e2e/web-coverage/_support/pages/workspaces.po.ts` (`/workspaces/[personaId]`) — `getByRole`/`getByLabel`/`getByTestId` only; emits `auditApprove()` returning `audit_id`
- [X] T015 [P] Page object `tests/e2e/web-coverage/_support/pages/incidents.po.ts` (`/incidents/[incidentId]`) — drives warning composer + IC approval modal
- [X] T016 [P] Page object `tests/e2e/web-coverage/_support/pages/disasters.po.ts` (`/disasters/`) — disaster index + drill-down
- [X] T017 [P] Page object `tests/e2e/web-coverage/_support/pages/governance.dashboard.po.ts` (`/governance/dashboard/{audit,compliance,readiness,recovery,risk}`)
- [X] T018 [P] Page object `tests/e2e/web-coverage/_support/pages/governance.dataSource.po.ts` (`/governance/[dataSourceId]`)
- [X] T019 [P] Page object `tests/e2e/web-coverage/_support/pages/operations.workflows.po.ts` (`/operations/workflows`)
- [X] T020 [P] Page object `tests/e2e/web-coverage/_support/pages/preparedness.po.ts` (`/preparedness/`)
- [X] T021 [P] Page object `tests/e2e/web-coverage/_support/pages/simulations.po.ts` (`/simulations/{create,[tenantId]/playback,reports/[reportId]}`)
- [X] T022 [P] Page object `tests/e2e/web-coverage/_support/pages/eval.po.ts` (`/eval/[runId]`)

### Fixtures

- [X] T023 [P] Persona fixture `tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts` — calls `GET /api/test-support/personas/{id}`, sets `X-Test-Persona-Id` header on context, exposes typed `PersonaFixture` per `data-model.md` §5; worker-scoped; fails fast if persona absent from seed (ASM-011)
- [X] T024 [P] Hazard scenario fixture `tests/e2e/web-coverage/_support/fixtures/hazardScenario.fixture.ts` — loads `outcome-{N}-*.fixture.json`, calls `POST /api/test-support/seed/scenario`, exposes typed `HazardScenarioFixture` per `data-model.md` §6
- [X] T025 [P] Correlation-id fixture `tests/e2e/web-coverage/_support/fixtures/correlationId.fixture.ts` — emits `crypto.randomUUID()` and attaches `X-Correlation-Id` to every request via `context.setExtraHTTPHeaders`
- [X] T026 [P] Audit observer fixture `tests/e2e/web-coverage/_support/fixtures/auditObserver.fixture.ts` — wraps `expect.poll(GET /api/audits?cid=…)` with 2-second deadline (FR-010, SC-004); returns observed `audit_evidence_id`
- [X] T027 [P] Carve-out registry fixture `tests/e2e/web-coverage/_support/fixtures/carveoutRegistry.fixture.ts` — loads `infra/parameters/foundry-carveout.yaml` once per worker, validates with `infra/parameters/foundry-carveout.schema.json` via `ajv`, asserts `review_date` ≤ 90 days old + `approver_identities[]` non-empty (FR-018(c))

### Hazard-pair fixture data (FR-016)

- [X] T028 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json` — bushfire+extreme-heat seed scenario with baseline `lives_at_risk` numeric per data-model §6
- [X] T029 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-2-bushfire-severe-storm.fixture.json` — baseline `signal_to_action_ms` per AIIMS Levels 1/2/3 budgets (SC-002 contractual: ≤ 5/15/30 min)
- [X] T030 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json` — baseline `evac_lead_hours` ≥ 24 (SC-003)
- [X] T031 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-4-bushfire-cyclone-logistics.fixture.json` — baseline `logistics_clicks` ≤ 7 routine / ≤ 12 mutual-aid (SC-004)
- [X] T032 [P] Author `tests/e2e/web-coverage/_support/fixtures/data/outcome-5-flood-storm-economic.fixture.json` — baseline `economic_loss_aud` per Sendai Indicator C (SC-005 formula `(baseline-projected)/baseline ≥ 0.30`)

### Custom reporter + types (FR-004)

- [X] T033 Implement `tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts` — Playwright `Reporter` interface; `onTestEnd` extracts `coverage` annotations + dedupes by `(persona, outcome, hazard, fr_id)` tuple; `onEnd` writes `tests/e2e/web-coverage/_artifacts/coverage-trace.partial-${PW_SHARD ?? 1}.json` matching `contracts/coverage-trace-row.schema.json`; `onStdErr` converts `waitForTimeout` matches into test failures (R-002, R-015)
- [X] T034 [P] Annotation helpers `tests/e2e/web-coverage/_support/reporter/annotations.ts` — typed `recordCoverage({persona, outcome, hazard, fr, clauses, route, audit_evidence_id, status})` wrapper around `test.info().annotations.push(...)`
- [X] T035 [P] Trace-row helper `tests/e2e/web-coverage/_support/reporter/trace-row.ts` — `CoverageTraceRow` factory + sort key `(persona_id, outcome, hazard, fr_id)` for deterministic merge
- [X] T036 [P] Redaction helper `tests/e2e/web-coverage/_support/reporter/redact.ts` — strips PII (names, emails, GPS coords < 1km precision) from screenshots/JSON before artefact upload (RISK-07, R-016)
- [X] T037 [P] Type declaration `tests/e2e/web-coverage/_support/types/coverage.d.ts` — exports `CoverageTraceRow` matching `data-model.md` §1
- [X] T038 [P] Type declaration `tests/e2e/web-coverage/_support/types/gap.d.ts` — exports `GapRegisterEntry` matching `data-model.md` §2
- [X] T039 [P] Type declaration `tests/e2e/web-coverage/_support/types/review.d.ts` — exports `ReviewVote`, `AgentObjection`, `KnownGoodManifest` matching `data-model.md` §§3–4, §9

### Validators (outcome-proxy + AWS + PSPF)

- [X] T040 [P] Outcome-proxy validator `tests/e2e/web-coverage/_support/validators/outcome-proxy.ts` — implements all five proxies (lives, latency, evac lead, logistics clicks, SC-005 economic-loss formula `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30`)
- [X] T041 [P] AWS CAP envelope validator `tests/e2e/web-coverage/_support/validators/aws-cap-envelope.ts` — asserts CAP v1.2 nested model (level + hazard/location + action statement), de-escalation chain, all-clear, hazard iconography (FR-011)
- [X] T042 [P] PSPF classification validator `tests/e2e/web-coverage/_support/validators/pspf-classification.ts` — synthetic OFFICIAL:Sensitive / PROTECTED markers; gateway probe payload generator (FR-018(b))

### Accessibility wrappers

- [X] T043 [P] Axe builder `tests/e2e/web-coverage/_support/a11y/axeBuilder.ts` — wraps `@axe-core/playwright` with WCAG 2.2 AA rule pack + critical-violation gate (R-007, FR-014, Q14)
- [X] T044 [P] Language pack probe `tests/e2e/web-coverage/_support/a11y/languagePackProbe.ts` — toggles `en`, `zh-Hans`, `aus-x-atsi-placeholder` (R-008) and asserts payload variants

### Gap-register state machine + audit append (FR-005, R-009)

- [X] T045 Implement `scripts/web-coverage/gap-register.py` — state-machine CLI with subcommands `open|progress|close|regress|validate|escalate`; enforces transitions per `data-model.md` §2 invariants table; writes markdown to `specs/034-webapp-capstone-coverage/gap-register.md` and appends JSONL to `audit/web-coverage-gaps/{date}/{hour}.jsonl`; validates entries against `contracts/gap-register-entry.schema.json` via `ajv` (Python `jsonschema` package)
- [X] T046 [P] Shared audit-append helper `scripts/web-coverage/_lib/__init__.py` and `scripts/web-coverage/_lib/audit_append.py` — append-only JSONL writer (local fallback + Blob `web-coverage-evidence` container via managed identity); honours `AMA_AUDIT_FALLBACK=1` for offline dev
- [X] T047 [P] Schema validator helper `scripts/web-coverage/_lib/schema_validators.py` — single entry point for validating `coverage-trace.json`, `gap-register.md`, review-log JSONL, and known-good.json against contracts via `jsonschema`

### Trace merge + known-good + review-log scaffolding

- [X] T048 Implement `scripts/web-coverage/trace-merge.py` — reads N partial JSONs, dedupes by `(persona, outcome, hazard, fr_id)` joining `test_ids` with `;`, sorts deterministically, emits `specs/034-webapp-capstone-coverage/coverage-trace.json` + Markdown render `coverage-trace.md` (FR-004 column order); validates against `contracts/coverage-trace-row.schema.json`; idempotent — re-running on the same input MUST produce byte-equal output (SC-010, RISK-13)
- [X] T049 [P] Implement `scripts/web-coverage/known-good.py` — manifest manager with `update` subcommand (called from cd.yml after `record-revisions`); writes `specs/034-webapp-capstone-coverage/known-good.json` matching `KnownGoodManifest` schema (data-model §4); computes `trace_hash = sha256(coverage-trace.json)`
- [X] T050 [P] Implement `scripts/web-coverage/review-log.py` skeleton — `run` subcommand loads `.github/agents/{operational,sectors,technical}/**/*.agent.md`, ingests AgentObjection JSON sidecars, emits `specs/034-webapp-capstone-coverage/review-log.md`; panel-resolution stub (full logic in T140)
- [X] T051 [P] Implement `scripts/web-coverage/verify-trace-determinism.ps1` — runs `trace-merge.py` twice on the same partials and asserts byte-equal output; surfaces `GAP-DET-TRACE-MERGE` on failure (RISK-13, SC-010)

### Seed-data extension

- [X] T052 Extend `bootstrap_seed_data()` (`packages/domain/src/domain/seed/bootstrap.py` + driver `scripts/seed_loader.py`) to materialise: (a) the 68 persona identities (10 operational + 58 sector with persona-id matching agent file basenames; Commonwealth AFP keyed as `afp-commonwealth` to disambiguate from ACT `afp`); (b) 5 hazard-pair scenario seeds (one per outcome) with disaster + primary incident chain referenced by T028–T032 fixtures; (c) the AIIMS function map per `data-model.md` §5; idempotent re-execution required (FR-021, SC-010)

### Persona-fixture contract test (closure)

- [X] T053 [P] Implement contract test `tests/e2e/web-coverage/_support/fixtures/__tests__/persona.contract.spec.ts` — drives all 68 persona ids through the fixture, asserts each resolves to a seeded identity with non-empty `permissions[]`, fails fast if any id is fixture-only (ASM-011 closure)

**Checkpoint**: Phase 2 complete. Foundation ready. Cross-cutting, persona, capstone, and CI work may now proceed in parallel.

---

## Phase 3: Cross-Cutting Suites (US2 + US4) 🎯 Cross-cutting MVP

**Goal**: Prove the constitutional baseline holds regardless of persona. Each spec is parameterised over ≥ 3 personas drawn from ≥ 3 jurisdictions per spec §User Story 2.

**Independent Test**: Run only `tests/e2e/web-coverage/cross-cutting/`; every file passes. Failure of any single file blocks the gate.

- [X] T054 [P] [US2] `tests/e2e/web-coverage/cross-cutting/rbac-aiims.spec.ts` — AIIMS function map; positive (Control may approve) + negative (Logistics may NOT approve evacuation) tests parameterised over ≥ 3 personas × ≥ 3 jurisdictions (FR-007, II-A)
- [X] T055 [P] [US2] `tests/e2e/web-coverage/cross-cutting/cop-refresh-latency.spec.ts` — asserts `≤ 5 s` COP refresh across incidents/jurisdictions/AIIMS functions; uses `expect.poll` with 5000ms ceiling (FR-008)
- [X] T056 [P] [US2] `tests/e2e/web-coverage/cross-cutting/audit-append-only.spec.ts` — every state-changing action produces an audit entry within 2 s with rationale/confidence/source/operator identity; asserts PUT/PATCH against an audit_id is rejected and no row mutates (FR-010, edge-case "Audit timeline tampering attempt")
- [X] T057 [P] [US2] `tests/e2e/web-coverage/cross-cutting/aws-warning-compliance.spec.ts` — three states (Advice / Watch and Act / Emergency Warning), nested model, hazard iconography, de-escalation, all-clear; parameterised across all 6 hazards including `earthquake/tsunami` (FR-011, V-A/V-B/V-C)
- [X] T058 [P] [US2] `tests/e2e/web-coverage/cross-cutting/evacuation-five-stage.spec.ts` — Decision → Warning → Withdrawal → Shelter → Return; total/partial/phased + shelter-in-place + directed/recommended/self-initiated; vulnerable-population fields (ATSI, CALD, disability, children, older persons, homeless, tourists, institutional care) populated and filterable (FR-012, VI-A/B/C)
- [X] T059 [P] [US2] `tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts` — four environments (Social, Built, Economic, Natural) tracked + managed handover from response → recovery; ≥ 3 data sources per environment (FR-013, FR-018(a), VII)
- [X] T060 [P] [US2] `tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts` — WCAG 2.2 AA conformance via `axeBuilder` on every P1 surface enumerated in FR-014 (workspaces, governance dashboards, warning-composition, simulations, audit-timeline); `en`+`zh-Hans`+`aus-x-atsi-placeholder` rendered on ≥ 1 warning per hazard category; emits `GAP-A11Y-WORKSPACE` on failure (FR-014, Q14, Q2)
- [X] T061 [P] [US2] `tests/e2e/web-coverage/cross-cutting/field-offline-mode.spec.ts` — queue-and-sync, idempotent dedupe by client correlation ID, conservative life-safety defaults, offline banner; replay test asserts queued action syncs into immutable audit with original timestamp + authorship (FR-017, NN-#5, edge-case "Offline field coordinator submits a duplicate")
- [X] T062 [P] [US2] `tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts` — three contractual assertions: (a) AU-region badge/banner on every regulated route + Foundry carve-out list reachable from `/governance/dashboard/compliance`; (b) PSPF/PII payload denied at gateway (FR-018(b) probe via `pspf-classification.ts`); (c) carve-out YAML `review_date` ≤ 90 days + non-empty approvers (FR-018, NN-#2)
- [X] T063 [P] [US2] `tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts` — command-side persona with > 7 direct reports surfaces a warning before save; asserts warning text + delegation prompt; parameterised over IC (Tier-1) + Operations Officer + Logistics Officer (Tier-2 when supervising direct reports). Planning Officer + remaining personas covered as N/A negative test (FR-020, Clarifications Q9)
- [X] T064 [P] [US2] `tests/e2e/web-coverage/cross-cutting/decision-support-hitl.spec.ts` — every safety-critical action gated by IC approval; positive (approval succeeds, identity logged) + negative (no approval = no execution); deterministic structured-JSON HITL output (FR-009, NN-#1, RISK-02)
- [X] T065 [P] [US2] `tests/e2e/web-coverage/cross-cutting/data-source-multiplicity.spec.ts` — each persona scenario asserts ≥ 3 named data sources surfaced in COP/governance views (FR-018(a))
- [X] T066 [P] [US2] `tests/e2e/web-coverage/cross-cutting/audit-trail.spec.ts` — append-only timeline view + correlation_id propagation visible at `/governance/dashboard/audit` (Constitution §IV)
- [X] T067 [P] [US4] `tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts` — `/simulations/create` → `/simulations/[tenantId]/playback`; deterministic replay with byte-identical asserted properties on second run (FR-006 Response/Recovery, US4 Acceptance #1–#2)
- [X] T068 [P] [US4] `tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts` — `/simulations/reports/[reportId]` export includes lessons identified, mapped to preparedness controls in `/preparedness` (FR-006 PPRR loop closure, US4 Acceptance #3)

**Checkpoint**: Phase 3 complete. US2 + US4 are independently testable.

---

## Phase 4: Persona Scenarios (US1 + US3)

**Goal**: ≥ 1 passing persona scenario per FR-002 inventory (10 operational + 58 sector = 68) + ≥ 1 cross-jurisdiction integration per state/territory + ≥ 1 Commonwealth-bridge per FR-003. Each scenario asserts at least one outcome-proxy metric and writes a trace row tagged `@outcome:N @hazard:X+Y @fr:FR-NNN`.

**Independent Test**: For any persona ID drawn from the 68, locate the file, run it, confirm it (a) loads `/workspaces/[personaId]`, (b) performs the persona's must-do actions per the cited input file, (c) asserts an outcome-proxy metric within SC-001..SC-005 budgets, (d) writes the audit entry within 2 s.

### 4.1 Operational personas (10) — `tests/e2e/web-coverage/operational/`

- [X] T069 [P] [US1] `operational/incident-commander.approve-cross-agency-action.spec.ts` — IC approves cross-agency action; outcome-1 (lives) + outcome-2 (latency); `@persona:incident-commander @outcome:1 @hazard:bushfire+extreme-heat @fr:FR-009 @clause:I @clause:NN-1` (Spec §US1 Acceptance #1)
- [X] T070 [P] [US1] `operational/operations-officer.tactical-tasking.spec.ts` — Operations Officer issues tasking, signal-to-action ≤ 5/15/30 min for Levels 1/2/3; `@outcome:2 @hazard:bushfire+severe-storm @fr:FR-008`
- [X] T071 [P] [US1] `operational/planning-officer.predictive-risk-evac.spec.ts` — Planning Officer drives predictive risk → 24-h-earlier evacuation lead-time proxy; `@outcome:3 @hazard:tropical-cyclone+riverine-flood @fr:FR-016`
- [X] T072 [P] [US1] `operational/logistics-officer.mutual-aid-lifecycle.spec.ts` — Logistics Officer drives mutual-aid request through approval; clicks ≤ 12 (SC-004); `@outcome:4 @hazard:bushfire+tropical-cyclone @fr:FR-015`
- [X] T073 [P] [US1] `operational/public-information-officer.aws-multilingual-warning.spec.ts` — PIO drafts AWS warning with `en` + `zh-Hans` + `aus-x-atsi-placeholder`; IC approval required; `@outcome:1 @hazard:bushfire+extreme-heat @fr:FR-011 @fr:FR-014`
- [X] T074 [P] [US1] `operational/field-coordinator.offline-gps-hazard-report.spec.ts` — Field Coordinator captures GPS-tagged hazard report offline, syncs on reconnect; `@outcome:2 @hazard:bushfire+severe-storm @fr:FR-017`
- [X] T075 [P] [US1] `operational/resilience-planner.recovery-handover.spec.ts` — Resilience Planner drives response→recovery handover; SC-005 economic-loss proxy ≥ 30 %; `@outcome:5 @hazard:riverine-flood+severe-storm @fr:FR-013`
- [X] T076 [P] [US1] `operational/executive-leader.economic-environment-view.spec.ts` — Executive views post-handover Economic-environment view, asserts SC-005 formula; `@outcome:5 @hazard:riverine-flood+severe-storm @fr:FR-013`
- [X] T077 [P] [US1] `operational/observer-auditor.append-only-timeline.spec.ts` — Observer/Auditor inspects audit timeline, asserts immutability (PUT/PATCH rejected); `@outcome:4 @hazard:bushfire+tropical-cyclone @fr:FR-010 @clause:IV`
- [X] T078 [P] [US1] `operational/risk-manager.predictive-evac-lead.spec.ts` — Risk Manager validates 24-h-earlier evacuation proxy on cyclone+flood scenario; `@outcome:3 @hazard:tropical-cyclone+riverine-flood @fr:FR-016`

### 4.2 NSW (6) — `tests/e2e/web-coverage/sectors/nsw/`

- [X] T079 [P] [US1] `sectors/nsw/nsw-rfs.bushfire-incident-action-plan.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T080 [P] [US1] `sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts` — Watch and Act flood warning + 24-h-earlier evac lead-time proxy (Spec §US1 Acceptance #2); `@outcome:3 @hazard:tropical-cyclone+riverine-flood @fr:FR-011 @fr:FR-016`
- [X] T081 [P] [US1] `sectors/nsw/nsw-ambulance.mass-casualty-triage.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T082 [P] [US1] `sectors/nsw/nswpf.evacuation-cordon.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T083 [P] [US1] `sectors/nsw/frnsw.urban-fire-response.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T084 [P] [US1] `sectors/nsw/mrnsw.maritime-flood-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`

### 4.3 VIC (5) — `tests/e2e/web-coverage/sectors/vic/`

- [X] T085 [P] [US1] `sectors/vic/cfa-vic.code-red-day.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T086 [P] [US1] `sectors/vic/ses-vic.flash-flood-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T087 [P] [US1] `sectors/vic/av.heat-related-illness-surge.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T088 [P] [US1] `sectors/vic/vicpol.cross-border-evac.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T089 [P] [US1] `sectors/vic/frv.warehouse-fire-haz-mat.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.4 QLD (4) — `tests/e2e/web-coverage/sectors/qld/`

- [X] T090 [P] [US1] `sectors/qld/qfd.cyclone-pre-positioning.spec.ts` — `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [X] T091 [P] [US1] `sectors/qld/ses-qld.tropical-cyclone-flood.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T092 [P] [US1] `sectors/qld/qas.heat-stress-mass-casualty.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T093 [P] [US1] `sectors/qld/qps.evac-traffic-management.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`

### 4.5 SA (5) — `tests/e2e/web-coverage/sectors/sa/`

- [X] T094 [P] [US1] `sectors/sa/sacfs.code-red-bushfire.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T095 [P] [US1] `sectors/sa/ses-sa.river-murray-flood.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T096 [P] [US1] `sectors/sa/saas.extreme-heat-mass-call.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T097 [P] [US1] `sectors/sa/sapol.cross-border-evac.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T098 [P] [US1] `sectors/sa/samfs.urban-fire-multi-storey.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.6 WA (3) — `tests/e2e/web-coverage/sectors/wa/`

- [X] T099 [P] [US1] `sectors/wa/dfes-wa.cyclone-pilbara.spec.ts` — `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [X] T100 [P] [US1] `sectors/wa/sja-wa.remote-medical-evac.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T101 [P] [US1] `sectors/wa/wapol.remote-evac-cordon.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`

### 4.7 TAS (4) — `tests/e2e/web-coverage/sectors/tas/`

- [X] T102 [P] [US1] `sectors/tas/tfs.bushfire-island-evac.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T103 [P] [US1] `sectors/tas/ses-tas.severe-storm-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T104 [P] [US1] `sectors/tas/at.aeromedical-retrieval.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T105 [P] [US1] `sectors/tas/taspol.island-evac-coordination.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`

### 4.8 ACT (7) — `tests/e2e/web-coverage/sectors/act/`

- [X] T106 [P] [US1] `sectors/act/act-esa.multi-agency-coordination.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T107 [P] [US1] `sectors/act/act-fr.urban-fire.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T108 [P] [US1] `sectors/act/act-ambulance.heat-surge.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T109 [P] [US1] `sectors/act/act-policing.evac-cordon.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T110 [P] [US1] `sectors/act/act-rfs.bushfire-pre-positioning.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T111 [P] [US1] `sectors/act/afp.protective-services.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T112 [P] [US1] `sectors/act/ses-act.severe-storm-rescue.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`

### 4.9 NT (5) — `tests/e2e/web-coverage/sectors/nt/`

- [X] T113 [P] [US1] `sectors/nt/bushfires-nt.savanna-burn.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T114 [P] [US1] `sectors/nt/ntes.cyclone-shelter.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T115 [P] [US1] `sectors/nt/ntfrs.remote-fire-response.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T116 [P] [US1] `sectors/nt/ntpf.remote-evac.spec.ts` — `@outcome:2 @hazard:bushfire+severe-storm`
- [X] T117 [P] [US1] `sectors/nt/sja-nt.remote-medical-retrieval.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.10 Commonwealth (11) — `tests/e2e/web-coverage/sectors/commonwealth/`

- [X] T118 [P] [US1] `sectors/commonwealth/nema.activate-comdisplan.spec.ts` — Activates COMDISPLAN, opens NJCOP, requests consequence metrics, asserts logistics-match efficiency proxy (Spec §US1 Acceptance #3); `@outcome:4 @hazard:bushfire+tropical-cyclone @fr:FR-015`
- [X] T119 [P] [US1] `sectors/commonwealth/bom-national.cyclone-warning-relay.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T120 [P] [US1] `sectors/commonwealth/ga-national.tsunami-warning-relay.spec.ts` — Earthquake/tsunami AWS path (FR-011 only, not paired with capstone outcome); `@hazard:earthquake @hazard:tsunami @aws @fr:FR-011`
- [X] T121 [P] [US1] `sectors/commonwealth/adf.dacc-asset-arrival.spec.ts` — DACC categorisation (A/B/C), asset arrival tracking; `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [X] T122 [P] [US1] `sectors/commonwealth/abf.border-disaster-coordination.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T123 [P] [US1] `sectors/commonwealth/arc.recovery-financial-assistance.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T124 [P] [US1] `sectors/commonwealth/asa.shipping-evac.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T125 [P] [US1] `sectors/commonwealth/rfds.remote-aeromedical.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T126 [P] [US1] `sectors/commonwealth/sja-national.community-first-aid.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T127 [P] [US1] `sectors/commonwealth/surf-lifesaving.coastal-cyclone-evac.spec.ts` — `@outcome:3 @hazard:tropical-cyclone+riverine-flood`
- [X] T128 [P] [US1] `sectors/commonwealth/afp-commonwealth.national-evac-coordination.spec.ts` — Persona-id `afp-commonwealth` to disambiguate from ACT `afp` (T111); seeded by T052; `@outcome:2 @hazard:bushfire+severe-storm`

### 4.11 Cross-sector (8) — `tests/e2e/web-coverage/sectors/cross-sector/`

- [X] T129 [P] [US1] `sectors/cross-sector/community-ngos.recovery-coordination.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T130 [P] [US1] `sectors/cross-sector/health.surge-capacity.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`
- [X] T131 [P] [US1] `sectors/cross-sector/local-government.recovery-funding.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T132 [P] [US1] `sectors/cross-sector/state-government.disaster-declaration.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T133 [P] [US1] `sectors/cross-sector/territory-government.cross-jurisdiction-coord.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T134 [P] [US1] `sectors/cross-sector/transport.evac-routing.spec.ts` — `@outcome:4 @hazard:bushfire+tropical-cyclone`
- [X] T135 [P] [US1] `sectors/cross-sector/utility.power-restoration.spec.ts` — `@outcome:5 @hazard:riverine-flood+severe-storm`
- [X] T136 [P] [US1] `sectors/cross-sector/volunteer.surge-deployment.spec.ts` — `@outcome:1 @hazard:bushfire+extreme-heat`

### 4.12 Cross-jurisdiction integration (FR-003 — 8 state/territory + 1 Commonwealth bridge)

- [X] T137 [P] [US3] `sectors/nsw/cross-jurisdiction-nsw-vic-bushfire.spec.ts` — bushfire crosses NSW→VIC border; both NSW RFS + CFA see same incident COP, AWS warning state, audit history (Spec §US3 Acceptance #1); `@fr:FR-015`
- [X] T138 [P] [US3] `sectors/vic/cross-jurisdiction-vic-tas-storm.spec.ts` — severe-storm bridge VIC↔TAS; `@fr:FR-015`
- [X] T139 [P] [US3] `sectors/qld/cross-jurisdiction-qld-nsw-cyclone-flood.spec.ts` — SES-QLD ↔ SES-NSW for tropical-cyclone flooding at border; `@fr:FR-015`
- [X] T140 [P] [US3] `sectors/sa/cross-jurisdiction-sa-vic-bushfire.spec.ts` — SA ↔ VIC bushfire bridge; `@fr:FR-015`
- [X] T141 [P] [US3] `sectors/wa/cross-jurisdiction-wa-sa-flood.spec.ts` — WA ↔ SA flood bridge; `@fr:FR-015`
- [X] T142 [P] [US3] `sectors/tas/cross-jurisdiction-tas-mainland-cyclone.spec.ts` — Tasmania mainland-link evac; `@fr:FR-015`
- [X] T143 [P] [US3] `sectors/act/cross-jurisdiction-act-nsw-bushfire.spec.ts` — ACT ↔ NSW bushfire bridge; `@fr:FR-015`
- [X] T144 [P] [US3] `sectors/nt/cross-jurisdiction-nt-wa-bushfire-cyclone.spec.ts` — NT ↔ WA bushfire/cyclone bridge; `@fr:FR-015`
- [X] T145 [P] [US3] `sectors/commonwealth/nema.dacc-state-controller-bridge.spec.ts` — Commonwealth bridge: state controller → NEMA → ADF DACC lifecycle (COMDISPLAN activation, DACC categorisation A/B/C, mission-close report) (Spec §US3 Acceptance #2); `@fr:FR-015`

**Checkpoint**: Phase 4 complete. US1 + US3 are independently testable. The 68-persona inventory + 9 cross-jurisdiction scenarios fulfil FR-002 + FR-003.

---

## Phase 5: Capstone Outcome Suites (US1 closure)

**Goal**: Each capstone outcome (#1..#5) has ≥ 1 traceable passing assertion that closes the trace at the **outcome level** (FR-023(d)), aggregating signals from the persona scenarios via the trace emitter.

**Independent Test**: Run only `tests/e2e/web-coverage/capstone/`; every file passes. Each spec asserts the SC-001..SC-005 outcome-proxy threshold against the corresponding hazard-pair fixture and closes the trace.

- [X] T146 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts` — Lives saved (zero preventable deaths); proxy = warning latency + IC-approval timeliness + multilingual reach within 2 min (SC-001); validates with `outcome-proxy.ts.lives` against `outcome-1-*.fixture.json`
- [X] T147 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-2-bushfire-severe-storm.spec.ts` — 50 % faster signal-to-action; proxy = AIIMS Level 1/2/3 latencies ≤ 5/15/30 min (SC-002)
- [X] T148 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-3-tropical-cyclone-flood.spec.ts` — 24-h-earlier evacuation; proxy = `evac_lead_hours ≥ 24` vs seed reference (SC-003)
- [X] T149 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-4-bushfire-cyclone-logistics.spec.ts` — 30 % logistics-friction reduction; proxy = `logistics_clicks ≤ 7` routine / `≤ 12` mutual-aid (SC-004)
- [X] T150 [P] [US1] `tests/e2e/web-coverage/capstone/outcome-5-flood-storm-economic.spec.ts` — 30 % economic-loss reduction; proxy = `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30` evaluated at response→recovery handover on the post-handover Economic-environment view (SC-005, Q7)

**Checkpoint**: Phase 5 complete. Trace closes at the capstone-outcome level. US1 is fully provable end-to-end.

---

## Phase 6: CI Gate Wiring (US5)

**Goal**: Suite functions as a binary CI quality gate (FR-023). Three new jobs added to `.github/workflows/ci.yml`; one step appended to `.github/workflows/cd.yml`. ≤ 45 min wall-clock CI budget; 4 shards on `ubuntu-latest`.

- [X] T151 [US5] Extend `.github/workflows/ci.yml` with `web-coverage-shard` job — `needs: [quality]`, `runs-on: ubuntu-latest`, `timeout-minutes: 45`, `strategy.matrix.shard: [1,2,3,4]`, `fail-fast: false`; steps per plan §CI Integration: `actions/checkout@v4`, `actions/setup-node@v4` (node 24 + pnpm cache), `actions/setup-python@v5` (3.12 + pip cache), `actions/cache@v4` keyed on `${{ runner.os }}-pw-${{ hashFiles('apps/web/pnpm-lock.yaml') }}`, `pnpm install --frozen-lockfile`, `python -m pip install -e apps/api`, `pnpm exec playwright install --with-deps chromium`, `pwsh scripts/seed-database.ps1`, `corepack pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --shard=${{ matrix.shard }}/4`; uploads partial JSON + JUnit + redacted screenshots via `actions/upload-artifact@v4`
- [X] T152 [US5] Extend `.github/workflows/ci.yml` with `web-coverage-merge` job — `needs: [web-coverage-shard]`; downloads all 4 shard artefacts; runs `python scripts/web-coverage/trace-merge.py --inputs tests/e2e/web-coverage/_artifacts/coverage-trace.partial-*.json --out-md specs/034-webapp-capstone-coverage/coverage-trace.md --out-json specs/034-webapp-capstone-coverage/coverage-trace.json`; runs `python scripts/web-coverage/gap-register.py validate`; runs `pwsh scripts/web-coverage/verify-trace-determinism.ps1`; uploads canonical artefacts
- [X] T153 [US5] Extend `.github/workflows/ci.yml` with `web-coverage-gate` job — `needs: [web-coverage-merge]`; validates `coverage-trace.json` against `contracts/coverage-trace-row.schema.json` via `python scripts/web-coverage/_lib/schema_validators.py`; fails if any row `status == "failing"`; fails if persona inventory < 68 OR state/territory cross-jurisdiction count < 8 OR Commonwealth-bridge < 1 OR capstone outcomes < 5; fails if gap-register has any `Open` entry (FR-023(e)); posts GitHub status check `web-coverage / capstone-ready`
- [X] T154 [US5] Mark all three jobs as **required** for merge to `main` via `.github/branch-protection.json` (or repo settings reference); document in `specs/034-webapp-capstone-coverage/known-good.json` README header
- [X] T155 [US5] Append step `Update FR-027 known-good manifest` to `.github/workflows/cd.yml` immediately after the existing `record-revisions` step (lines 238–264) — runs `python scripts/web-coverage/known-good.py update --commit "${{ github.sha }}" --revisions-json "${{ steps.record-revisions.outputs.json }}" --trace specs/034-webapp-capstone-coverage/coverage-trace.json` and commits via `ama-bot` with `[skip ci]` trailer
- [X] T156 [P] [US5] Add `apps/web/package.json` scripts: `"test:web-coverage"`, `"test:web-coverage:p1"` (--grep "@p1"), `"test:web-coverage:axe"` (--project=web-coverage-axe), `"test:web-coverage:shard"` (parametric)

**Checkpoint**: Phase 6 complete. CI gate is active; PRs cannot merge to `main` while any `Failing` row or `Open` gap exists.

---

## Phase 7: Iteration Loop Tooling (US5)

**Goal**: 85-agent tribunal converts objections → spec amendments → re-runs; max 3 cycles before escalation (FR-024); regressions auto-rolled back to known-good revision (FR-027).

- [X] T157 [US5] Implement vote-recording subcommand `python scripts/web-coverage/review-log.py vote --gap-id … --agent-id … --vote {approve|object|abstain} --rationale "…"` — appends a `ReviewVote` row to `specs/034-webapp-capstone-coverage/review-log.md` and JSONL audit shadow; validates against `contracts/review-vote.schema.json` (data-model §3, ASM-006, Q13)
- [X] T158 [US5] Implement panel-resolver inside `scripts/web-coverage/review-log.py` — computes `meritorious` (≥ 2/3 of relevant panel), operational-panel veto on safety-critical clauses {I, IV, NN-1, NN-2, QG-1}, override-supermajority (≥ 50 % of all 85 agents); writes resolution to vote rows + emits PR-ready spec amendments under `specs/034-webapp-capstone-coverage/diffs/` (Q13)
- [X] T159 [US5] Implement FR-024 max-3-cycles guard inside `scripts/web-coverage/gap-register.py escalate` subcommand — when `iteration_count >= 4`, transitions gap to `Escalated`, freezes counter, appends `gap.escalated` audit, halts further automated cycles for that gap (Spec §US5 Acceptance #3, Q5, Q6)
- [X] T160 [US5] Implement FR-027 known-good rollback CLI `python scripts/web-coverage/known-good.py rollback --gap-id … --failing-test-id … --reverted-sha … --restored-sha …` — composes with `cd.yml` 5-min auto-rollback; updates `KnownGoodManifest.last_regression`; appends rollback evidence (failing Test ID, reverted commit SHA, restored revision SHA) to audit timeline (Spec §US5 Acceptance #4, FR-027)
- [X] T161 [US5] Wire FR-027 rollback evidence capture into `gap-register.py regress` subcommand — populates `regression_evidence` block on `Closed → Reopened` transition, resets `iteration_count` to 0, tags row `regression_detected` (data-model §2 invariants table)
- [X] T162 [P] [US5] Author `.github/workflows/web-coverage-iteration.yml` (single new workflow file per plan §CI Integration §`web-coverage-iteration.yml`) — `schedule: cron: "0 16 * * *"` (02:00 AEST), `workflow_dispatch.inputs.gap_id`, `pull_request: types: [closed], paths: ["specs/034-**"]`; runs `review-log.py run --trace … --gaps … --agents .github/agents/`; opens follow-up PRs as `ama-bot`
- [X] T163 [P] [US5] Generate agent-objection sidecar template `scripts/web-coverage/agent-objection-template.json` matching `contracts/agent-objection.schema.json`; document the format in `.github/agents/_subagents/web-coverage-objection-format.md`

**Checkpoint**: Phase 7 complete. US5 closes: gate is active, iteration loop runs nightly, max-3-cycles + regression rollback are enforced.

---

## Phase 8: Documentation & Polish

**Purpose**: Finalise human-facing artefacts; populate skeletons; capture grading evidence.

- [X] T164 [P] Update `specs/034-webapp-capstone-coverage/quickstart.md` with any deltas surfaced during implementation (paths, env vars, troubleshooting); add a "Known limitations" section if gaps remain on first pass
- [X] T165 [P] Add a "Web coverage suite" section to repo `README.md` linking to `specs/034-webapp-capstone-coverage/quickstart.md` with a 5-line snippet for running the `@p1` smoke locally
- [X] T166 [P] Author `tests/e2e/web-coverage/README.md` documenting: tag taxonomy (R-017), persona-id-to-spec mapping (10 + 58 = 68), hazard-pair fixture index, ESLint determinism rules
- [X] T167 [P] Generate initial `specs/034-webapp-capstone-coverage/known-good.json` skeleton matching `KnownGoodManifest` schema with `version: 1`, current commit SHA, empty `last_regression: null`; cd.yml will refresh on first deploy (T155)
- [X] T168 [P] Author `specs/034-webapp-capstone-coverage/review-log.md` skeleton with cycle 0 header (date, suite-run id placeholder, panel sign-off rows for operational/sector/technical)
- [X] T169 [P] Author `specs/034-webapp-capstone-coverage/coverage-trace.md` placeholder with column header row only (`Persona | Outcome | Hazard | FR | Test ID | Route | Audit Evidence ID | Status`); first real run will replace via T152
- [X] T170 [P] Initialise `specs/034-webapp-capstone-coverage/gap-register.md` with empty Markdown table + `GAP-AI-CONTENT-SAFETY-CANDIDATE` row in `Open` state per plan §Conditionally proposed
- [X] T171 Run `pwsh scripts/web-coverage/verify-trace-determinism.ps1` locally + `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --grep "@p1"` and capture run output to `specs/034-webapp-capstone-coverage/_evidence/first-run.log` (RISK-12 redaction applied)
- [X] T172 [P] Cross-link this tasks.md from `specs/034-webapp-capstone-coverage/checklists/validation.md` CHK-IDs (CHK034, CHK045, CHK090, CHK130, CHK160) so iteration-loop runners can mark gates without re-tracing

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

**End of cycle-0 tasks** — Total: 172 tasks (T001..T172).

---

## Cycle-1 Amendment Tasks (T173+)

> Added 2026-02-05 by `/speckit.tasks` re-run, grounded in `plan.md` §Cycle-1 amendment summary (lines 768–810), `research.md` R-020..R-024, `data-model.md` entities #10..#13 (`CycleMetadata`, `DepthProfile`, `EvaluatorRequest`, `EvaluatorResponse`) plus the optional `cycle_id` on `GapRegisterEntry`, the three new contracts (`outcome-evaluator.contract.md`, `cycle-metadata.schema.json`, `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json`), and the cycle-1 portion of the validation checklist (CHK181..CHK185, CHK205, CHK210..CHK215). Dependency order honoured: contracts → depth-profile family + evaluator endpoints (parallel) → cycle metadata → workflow refactors → FR-030 net-new scenarios → env-var canonicalisation + SC-012 closure → documentation polish.

### Phase 9: Cycle-1 contract integration (foundation)

**Purpose**: Formal review + acceptance of the three artefacts authored during the plan re-run. No implementation here; T173/T174 are the "review and integrate" gates that unblock T175..T181. **No depth-profile, evaluator, or refactor task may begin until this phase is complete.**

- [X] T173 Review and integrate `specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md` — confirm Pass-4 Q21 / Pass-5 Q27 + Q29 alignment (idempotency tuple `(sc_id, scenario_id, persona_id, correlation_id)`, dual-guard activation reused from `persona-fixture.contract.md`, `sc-001..sc-005` routable range with `sc-006..sc-011 → 400 evaluator_not_routable` body naming the CI-artefact owner, embedded JSON Schemas draft 2020-12 for request + response, audit emission ≤ 2 s SLO, scenario-not-found → `GAP-EVALUATOR-SCENARIO-MISSING`); cross-link from `tests/e2e/web-coverage/README.md` and stamp the contract `Status: Accepted (cycle-1, /speckit.tasks)` (FR-028, Q21, Q27, Q29; CHK183)
- [X] T174 [P] Review and integrate `specs/034-webapp-capstone-coverage/contracts/cycle-metadata.schema.json` AND `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` — confirm: cycle-metadata schema (JSON-Schema draft 2020-12) carries `cycle_start_ts` (ISO-8601), `cycle_id` (UUID v4 — `format: "uuid"` per spec.md L640 + data-model.md §10), `commit_sha` (40-hex), `seed_hash` (SHA-256); depth-profile schema (JSON-Schema **draft-07** per Q28) closes the `safety_critical_workflow` enum to the 12-value set (9 write + 3 read-only per Q24: `approve|publish|allocate|decline|queue-and-sync|escalate|handover|declare|reopen|observe-tamper-resist|report-generate|export-evidence`); add `_schema.json` to `_lib/persona_spec_generator.py` validator import list reservation (Q20, Q24, Q26, Q28; CHK191, CHK202)

### Phase 10: Depth-profile family (FR-029)

**Purpose**: Realise the 68-of-68 binary depth-profile coverage gate per FR-029 final sentence. Each persona must have an authored, schema-valid `*.depth.yaml`; missing or invalid profile emits `GAP-DEPTH-PROFILE-MISSING-{persona-id}` and fails the gate. Begins after T173/T174.

- [X] T175 [P] Generate 68 `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml` files (one per FR-002 persona — 10 operational + 58 sector/jurisdiction) per the persona-need synthesis embedded in `plan.md` §Module Breakdown and `spec.md` Pass 4 Q15/Q24; each file MUST validate against `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` (draft-07) and MUST carry: `persona_id`, `primary_workspace_route`, `safety_critical_workflow` (one of the 12 enum values from T174), `workflow_steps[]` (≥ 3 steps with selector + expected post-state), `assertion_targets[]` (UI selector or evaluator endpoint reference), `audit_readback` (correlation-id rule), `coverage_tags[]` (multi-jurisdiction reach per Q23 — folder placement is fixed by owning persona, NOT by tags), `read_only_variant` flag if applicable per Q24 (Observer/Auditor, Executive Leader, analogous personas) — split workload between operational (10 files) + each jurisdiction folder so reviewers can shard (FR-002, FR-029, Q15, Q20, Q24; CHK181, CHK191)
- [X] T176 Extend `scripts/web-coverage/_lib/persona_spec_generator.py` — load each `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`, validate against `_schema.json` via existing `schema_validators.py` (T047 ajv pattern), translate workflow steps + assertion targets into a Playwright spec body that drives the FR-028 evaluator endpoint (no `test.fail` bail); on missing OR schema-invalid profile, fail-fast and call `python scripts/web-coverage/gap-register.py open --gap-id GAP-DEPTH-PROFILE-MISSING-{persona-id} --status Open --reason "depth-profile missing or invalid"` per FR-005; emit deterministic output (sorted keys, stable spec ordering) to satisfy SC-010 (FR-005, FR-029, Q20, Q28; ref `contracts/outcome-evaluator.contract.md` §Client-side fixture binding)
- [X] T177 Extend `web-coverage-gate` job (T153 in `.github/workflows/ci.yml`) — read all 68 depth-profile YAML paths via `Get-ChildItem tests/e2e/web-coverage/_lib/depth-profiles/*.depth.yaml`, cross-reference against the FR-002 persona inventory (10 operational + 58 sector), assert binary coverage (68/68 valid profiles); fail the gate AND post GitHub status check `web-coverage / depth-profile-binary` if any persona is missing a valid profile; embed numerator/denominator in the gate's audit-trail step output for CHK210/CHK212 traceability (FR-023, FR-029; CHK183, CHK191, CHK202)

### Phase 11: Outcome-evaluator + audit-list endpoints (FR-028)

**Purpose**: Wire the FR-028 route-only endpoints behind the dual-guard so the suite stops bailing with `test.fail(true, "<API not wired>")`. Runs in parallel with Phase 10 (different files). Begins after T173.

- [X] T178 [P] Create `apps/api/app/api/routes/outcome_evaluator.py` per `contracts/outcome-evaluator.contract.md` — FastAPI router exposing `POST /api/outcomes/sc-{sc_id}/evaluate` with path-param regex `^00[1-5]$` (`sc-006..sc-011` and any other value → HTTP 400 `evaluator_not_routable` body naming the CI-artefact owner per Q29 table); request validated against the embedded `EvaluatorRequest` JSON Schema; `404 scenario_not_found` → suite emits `GAP-EVALUATOR-SCENARIO-MISSING`; wire into `apps/api/app/api/router.py` aggregator behind `test_support_guard.is_enabled()` (T009 dual-guard pattern); never registered in production (`environment == "production"` branch returns no router) (FR-028, Q21, Q27, Q29; CHK183, CHK184)
- [X] T179 [P] Create `apps/api/app/api/routes/audit_list.py` per `contracts/outcome-evaluator.contract.md` §Server-side contract — audit-list — FastAPI router exposing `GET /api/audit/list?correlation_id={uuid}&cycle={current|all}&limit={1..500}&cursor={opaque}`; default `cycle=current` reads `bootstrap_seed_data().current_cycle_start` directly (server NEVER consults the gap register or `_artifacts/cycle-metadata.json` per Q22); cursor pagination, `limit` defaults 100 caps at 500 to bound SC-011; append-only retention — tamper attempts are themselves audit rows with `outcome: "denied"` per Q24 (a); wire into router aggregator behind same dual-guard as T178 (FR-010, FR-028, Q22, Q24; CHK183)
- [X] T180 Implement `apps/api/app/services/outcome_evaluator_service.py` — covers SC-001..SC-005 with deterministic counterfactual evaluation reading `metric_inputs` from `bootstrap_seed_data().scenarios[scenario_id].baseline` (data-model §6 — `lives_at_risk`, `signal_to_action_ms`, `evac_lead_hours`, `logistics_clicks`, `economic_loss_aud`); idempotency tuple `(sc_id, scenario_id, persona_id, correlation_id)` keyed via in-memory cache (worker-scoped) returning the same `audit_id` + verdict on retry; emits one append-only audit row per fresh evaluation via the existing `audit_writer` (FR-010), preserving the ≤ 2 s SLO (FR-004); response shape conforms to embedded `EvaluatorResponse` JSON Schema (status `pass|fail|gap`, `evidence_refs[]`, `metric_value`, `threshold`, `audit_id` UUID) (FR-028, Q21; ref `contracts/outcome-evaluator.contract.md` §Idempotency + §Audit emission)
- [X] T181 [P] Author contract tests `apps/api/tests/contract/test_outcome_evaluator.py` and `apps/api/tests/contract/test_audit_list.py` — for the evaluator: assert (a) 404 when `AMA_TEST_SUPPORT` unset, (b) 404 when `environment == "production"` regardless of env var, (c) 200 + schema-valid `EvaluatorResponse` for each of `sc-001..sc-005`, (d) 400 `evaluator_not_routable` for `sc-006..sc-011` with body naming the CI-artefact owner per Q29 table, (e) 404 `scenario_not_found` for unknown `scenario_id`, (f) idempotency — same tuple → same `audit_id` + same verdict + no duplicate audit row, (g) 422 on schema-invalid body. For audit-list: (h) `cycle=current` filters by `bootstrap_seed_data().current_cycle_start`, (i) cursor pagination is stable + sorted, (j) `limit > 500` clamps to 500, (k) tamper-attempt rows surface with `outcome: "denied"` (FR-021, FR-028, Q22, Q24, Q29; CHK183)

### Phase 12: Cycle metadata recorder (Q26)

**Purpose**: Emit `_artifacts/cycle-metadata.json` once per Playwright run so the suite-side has a symmetric Playwright surface for the same cycle boundary the audit-list endpoint reads from `bootstrap_seed_data()`. Begins after T173 + T179.

- [X] T182 Extend the Playwright reporter `tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts` (existing reporter from T039 — DO NOT create a parallel reporter) to add an `onBegin(config, suite)` hook that writes `tests/e2e/web-coverage/_artifacts/cycle-metadata.json` exactly once per run; payload conforms to `contracts/cycle-metadata.schema.json` with `cycle_start_ts` (ISO-8601 UTC), `cycle_id` (UUID v4 via Node.js built-in `crypto.randomUUID()` — schema enforces `format: "uuid"`, no third-party dep needed), `commit_sha` (40-hex from `process.env.GITHUB_SHA` ?? `git rev-parse HEAD`), `seed_hash` (sha256 of `bootstrap_seed_data()` payload via `GET /api/test-support/personas` → JSON.stringify with sorted keys); validate the payload against the embedded schema via `ajv` before writing; the `web-coverage-merge` job (T152) MUST copy this file into the `coverage-trace.json` header — extend T152's CLI invocation to pass `--cycle-metadata tests/e2e/web-coverage/_artifacts/cycle-metadata.json` (FR-027, Q26; ref `contracts/cycle-metadata.schema.json`)
- [X] T183 Update `scripts/web-coverage/gap-register.py` — when opening or transitioning a gap, read `tests/e2e/web-coverage/_artifacts/cycle-metadata.json` (if present) and stamp `cycle_id` on the new `GapRegisterEntry` (additive, optional per `contracts/gap-register-entry.schema.json`); add `--cycle current|all` option to `gap-register.py validate` and `gap-register.py list` for FR-005 cross-cycle queries — `current` filters by the active `cycle_id`, `all` is opt-in; FR-027 regression evidence (failing test id + reverted commit SHA + restored revision) MUST cite the originating `cycle_id` so panel resolutions can audit the cycle history (FR-005, FR-027, Q22, Q26)

### Phase 13: Workflow-state assertion refactors (FR-002 + FR-029)

**Purpose**: Drop every `test.fail(true, "<API not wired>")` bail and drive workflow via the now-wired evaluator endpoint, parameterised by depth-profile YAML. **MUST NOT begin until Phase 10 + Phase 11 + Phase 12 are complete** — depth-profile + evaluator + cycle metadata are required preconditions.

- [X] T184 [US1] Refactor 81 persona spec stubs (10 operational + 71 sector/jurisdiction non-cross-jurisdiction specs) currently bailing with `test.fail(true, ...)` to consume the depth-profile YAML via `persona_spec_generator.py` (T176) and drive the safety-critical workflow through `POST /api/outcomes/sc-{NNN}/evaluate` (or the persona's specified non-evaluator transition); drop ALL `test.fail(true, ...)` use; assert post-transition state via either evaluator response (`status: pass|fail|gap`) OR a UI selector reflecting persisted state per FR-029 (c); read back audit timeline via `GET /api/audit/list?correlation_id={cid}` per FR-029 (d); regenerate via `python scripts/web-coverage/_lib/persona_spec_generator.py --rewrite-stubs` so the change is deterministic (FR-002, FR-029, Q15, Q24; CHK181, CHK182)
- [X] T185 [US2] Refactor 11 cross-cutting suites that currently bail — `tests/e2e/web-coverage/cross-cutting/{aws-warning-compliance,audit-append-only,data-sovereignty,decision-support-hitl,span-of-control,recovery-environments,field-offline-mode,data-source-multiplicity,evacuation-five-stage,lessons-management,simulation-playback}.spec.ts` (verified bail count via `Select-String -Pattern 'test\.fail\(true' -Path tests/e2e/web-coverage/cross-cutting/*.spec.ts` = 11 files; **`data-sovereignty.spec.ts` was previously omitted — required by Constitution NN-2 (Data sovereignty) and FR-018 sovereignty triple, must NOT remain stubbed past T185**) — to drive workflow via the FR-028 evaluator endpoint where the suite covers SC-001..SC-005, OR via the existing test-support seed mutator + `audit-list` read-back where the suite covers FR-009/FR-010/FR-012/FR-013/FR-014/FR-015/FR-018 invariants (`data-sovereignty` specifically asserts the AU-region carve-out registry per Constitution §NN-2 carve-out + Foundry endpoint allow-list); remove ALL `test.fail(true, ...)` use; preserve the existing `@persona/@outcome/@hazard/@fr/@clause` tag taxonomy (R-017) (FR-002, FR-009, FR-010, FR-012, FR-013, FR-018, FR-029, NN-2; CHK181, CHK182)
- [X] T186 [US1] Refactor 5 capstone outcome specs `tests/e2e/web-coverage/capstone/outcome-{1..5}-*.spec.ts` (`outcome-1-bushfire-extreme-heat`, `outcome-2-bushfire-severe-storm`, `outcome-3-tropical-cyclone-flood`, `outcome-4-bushfire-cyclone-logistics`, `outcome-5-flood-storm-economic`) to call `POST /api/outcomes/sc-{001..005}/evaluate` (one outcome per spec) with `metric_inputs` derived from the matching `outcome-N-*.fixture.json` baseline (T028..T032), assert `status === "pass"` against the per-outcome threshold (SC-001 lives saved, SC-002 ≤ 5/15/30 min Levels 1/2/3, SC-003 ≥ 24 h evac lead, SC-004 ≤ 7/12 logistics clicks, SC-005 ≥ 30 % economic-loss reduction), assert `audit_id` resolves via `GET /api/audit/list?correlation_id={cid}` to a row whose `operator_identity.persona_id` matches the persona under test (SC-001..SC-005, FR-028, Q21; CHK181, CHK183)

### Phase 14: FR-030 net-new persona scenarios (13 specs, owning-persona placement per Q23)

**Purpose**: Author the 13 net-new scenarios required by the cycle-1 review per FR-030. Each scenario MUST conform to FR-029's depth contract, sit under the **owning persona's** sector folder per Q23 (multi-jurisdiction reach goes in `coverage_tags[]`, NOT folder placement), emit ≥ 1 `coverage-trace.md` row mapped to the persona's primary capstone outcome, and use the FR-028 evaluator endpoint or a state-changing UI transition (no `test.fail` bail). All tasks `[P]` — independent files. Begins after Phase 13 (depth-profile + evaluator are preconditions).

#### SA (2)

- [ ] T187 [P] [US3] Create `tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts` — multi-LGA delegated authority + role separation; persona `sapol`; depth profile must specify `safety_critical_workflow: declare` and assertion target `evaluator:sc-001` or UI selector reflecting cross-LGA delegation persisted state; emit `@persona:sapol @outcome:1 @hazard:bushfire @fr:FR-030 @clause:I @p2` (FR-030, Q23; CHK205)
- [ ] T188 [P] [US3] Create `tests/e2e/web-coverage/sectors/sa/ses-sa.long-distance-multi-lga-evacuation.spec.ts` — convoy staging + inter-LGA shelter routing under degraded comms; persona `ses-sa`; FR-016 hazard pair #4 (bushfire+TC) per CHK184; depth profile `safety_critical_workflow: handover`, evaluator `sc-003` (24-h evac lead) (FR-030, FR-016, Q23; CHK184, CHK205)

#### WA (2)

- [ ] T189 [P] [US3] Create `tests/e2e/web-coverage/sectors/wa/dfes-wa.atsi-handoff-culturally-safe.spec.ts` — culturally safe messaging + audit trail to remote ATSI community; persona `dfes-wa`; depth profile `safety_critical_workflow: publish` with multilingual variant assertion; evaluator `sc-001` (lives saved with community-language variant) (FR-030, FR-014, Q23; CHK205)
- [ ] T190 [P] [US3] Create `tests/e2e/web-coverage/sectors/wa/dfes-wa.iron-ore-critical-infrastructure.spec.ts` — port/rail/power-corridor protection under cyclone + bushfire compound; FR-016 hazard pair #4 per CHK184; depth profile `safety_critical_workflow: allocate`, evaluator `sc-004` (logistics clicks) (FR-030, FR-016, Q23; CHK184, CHK205)

#### TAS (2)

- [ ] T191 [P] [US3] Create `tests/e2e/web-coverage/sectors/tas/at.island-isolation-aeromedical-disruption.spec.ts` — ferry/air medevac disruption + rescue-to-care handoff; persona `at` (Ambulance Tasmania); depth profile `safety_critical_workflow: handover`, evaluator `sc-001` (FR-030, Q23; CHK205)
- [ ] T192 [P] [US3] Create `tests/e2e/web-coverage/sectors/tas/taspol.palawa-multilingual-warning.spec.ts` — palawa-language warning variant per FR-014 ATSI baseline; persona `taspol`; depth profile `safety_critical_workflow: publish`, evaluator `sc-001` with community-language variant assertion (FR-030, FR-014, Q23; CHK205)

#### ACT (2)

- [ ] T193 [P] [US3] Create `tests/e2e/web-coverage/sectors/act/afp.national-capital-security-mechanics.spec.ts` — Parliament/Defence precincts + Commonwealth tenancy escalation; persona `afp`; depth profile `safety_critical_workflow: escalate`, evaluator `sc-002` (signal-to-action) (FR-030, Q23; CHK185)
- [ ] T194 [P] [US3] Create `tests/e2e/web-coverage/sectors/act/ses-act.territory-emergency-declaration.spec.ts` — territory-government declaration mechanics; persona `ses-act`; depth profile `safety_critical_workflow: declare`, evaluator `sc-001` (FR-030, Q23; CHK185)

#### NT (2)

- [ ] T195 [P] [US3] Create `tests/e2e/web-coverage/sectors/nt/ntes.atsi-multilingual-at-persona-level.spec.ts` — NT-specific palawa/Yolŋu/Kriol variants applied at persona scope (NOT just cross-cutting); persona `ntes`; depth profile `safety_critical_workflow: publish`, evaluator `sc-001` with community-language variant assertion (FR-030, FR-014, Q23; CHK185)
- [ ] T196 [P] [US3] Create `tests/e2e/web-coverage/sectors/nt/sja-nt.tropical-disease-remote-logistics.spec.ts` — tropical-disease surge + remote-area logistics chain; persona `sja-nt`; depth profile `safety_critical_workflow: allocate`, evaluator `sc-004` (logistics clicks ≤ 12 mutual-aid) (FR-030, Q23; CHK185)

#### Commonwealth (2 — Q23 owning-persona placement)

- [ ] T197 [P] [US3] Create `tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts` — relay path with `Source = ABC/SBS` recorded in audit + multilingual variants per FR-014; also exercises FR-018 sovereignty triple at relay handoff; persona `bom-national`; depth profile `safety_critical_workflow: publish`, evaluator `sc-002` (signal-to-action) (FR-030, FR-014, FR-018, Q23; CHK185)
- [ ] T198 [P] [US3] Create `tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-jatwc-cross-jurisdiction.spec.ts` — DACC + JATWC handoff via `state-government` and `territory-government` cross-jurisdiction tags in `coverage_tags[]` per Q23; persona `nema` (Commonwealth-owned per spec.md L524); depth profile `safety_critical_workflow: handover`, evaluator `sc-003`; sits under `sectors/commonwealth/` per the Q23 owning-persona rule (moved from cross-sector) (FR-030, FR-015, Q23; CHK185)

#### Cross-sector (1)

- [ ] T199 [P] [US3] Create `tests/e2e/web-coverage/sectors/cross-sector/utility.insurance-recovery-handoff.spec.ts` — insurance recovery handoff producing Built + Economic Recovery Environment assertions per FR-013; persona `utility`; depth profile `safety_critical_workflow: handover`, evaluator `sc-005` (economic-loss reduction); FR-016 hazard pair #5 (riverine flood + severe storm) per CHK184 (FR-030, FR-013, FR-016, Q23; CHK184, CHK185)

### Phase 15: Env-var canonicalisation (Q25, CHK213-215)

**Purpose**: Normalise the test-support env-var name to the canonical `AMA_TEST_SUPPORT=1` (not `AMA_TEST_SUPPORT_ENABLED`) across CI, quickstart, and README. The middleware (T007) is already canonical; this phase removes drift downstream. All three are `[P]` — independent files.

- [ ] T200 [P] Update `.github/workflows/ci.yml` line 147 — replace `AMA_TEST_SUPPORT_ENABLED: "true"` with `AMA_TEST_SUPPORT: "1"` (matches the dual-guard middleware T007 + the persona-fixture contract canonical name); search the rest of the workflow for any other `AMA_TEST_SUPPORT_ENABLED` reference and remove (CHK213 mandates a single name) (FR-021, Q25; CHK213, CHK215)
- [ ] T201 [P] Update `specs/034-webapp-capstone-coverage/quickstart.md` — replace line 281's narrative reference `AMA_TEST_SUPPORT_ENABLED=true` with `AMA_TEST_SUPPORT=1`; verify all `$env:AMA_TEST_SUPPORT = "1"` PowerShell examples (lines 36, 58, 62) and the troubleshooting section (lines 198, 200) remain consistent — no drift between body commands and the dual-guard semantic (FR-021, Q25; CHK214)
- [ ] T202 [P] Update `README.md` line 296 — replace `$env:AMA_TEST_SUPPORT_ENABLED = "true"` with `$env:AMA_TEST_SUPPORT = "1"`; sweep the rest of `README.md` and `docs/` for any remaining `AMA_TEST_SUPPORT_ENABLED` reference and align to the canonical name (FR-021, Q25; CHK213, CHK215)

### Phase 16: SC-012 closure measurement (CHK210-212)

**Purpose**: Compute the per-cycle closure rate (≥ 80 % threshold) so `web-coverage-iteration.yml` (T162) can decide whether to flip a cycle to `Closed` or open a meta-gap.

- [ ] T203 Extend `scripts/web-coverage/review-log.py` with subcommand `python scripts/web-coverage/review-log.py closure --cycle-id {UUID}` — reads `_artifacts/cycle-metadata.json` (T182) for the active `cycle_id` (UUID v4), queries gap-register entries with that `cycle_id` (T183), computes numerator (gap rows with `Status == Closed` AND `iteration_count < 4`) over denominator (all merit-validated objection gap rows with `iteration_count < 4`); excludes escalated rows (`escalated:project-lead` OR `iteration_count >= 4`) from BOTH numerator and denominator per Q22 + CHK211; closure proof MUST cite (a) closing PR sha, (b) post-amendment scenario passing on that sha, (c) closing PR diff containing the FR-029 depth-contract assertion the panel demanded per CHK205; emits numerator + denominator + escalated-set + raw-objection list to the audit timeline (FR-010) before flipping per CHK212; if closure < 80 %, opens meta-gap `GAP-CYCLE-{id}-CLOSURE-RATE-LOW` via `gap-register.py open` so the next cycle inherits the carry-over (SC-012, FR-005, FR-010, FR-024, ASM-006, Q22, Q26; CHK210, CHK211, CHK212)

### Phase 17: Cycle-1 documentation polish

**Purpose**: Roll documentation forward so quickstart, suite README, and validation checklist reflect the cycle-1 deltas. All `[P]` — independent files. Validation tick-off at `/speckit.implement` time (CHK closure proof).

- [ ] T204 [P] Update `specs/034-webapp-capstone-coverage/quickstart.md` Known limitations section — remove the workaround note about FR-028 endpoints not being wired (now closed by T178/T179/T180); add a new subsection on the `_artifacts/cycle-metadata.json` artefact and the `cycle=current|all` query semantic on `/api/audit/list`; document the `python scripts/web-coverage/review-log.py closure --cycle-id` invocation (T203) (FR-028, FR-029, Q22, Q26; CHK183)
- [ ] T205 [P] Update `tests/e2e/web-coverage/README.md` with a depth-profile YAML authoring guide — covers: file location (`_lib/depth-profiles/{persona-id}.depth.yaml`), schema reference (`_lib/depth-profiles/_schema.json` draft-07), the 12-value `safety_critical_workflow` enum (9 write per Q15 + 3 read-only per Q24), required keys, multi-jurisdiction `coverage_tags[]` rule (Q23 — folder is owning-persona, tags carry the rest), missing-profile failure mode (`GAP-DEPTH-PROFILE-MISSING-{persona-id}`); link to `contracts/outcome-evaluator.contract.md` for the evaluator binding pattern (FR-029, Q20, Q23, Q24, Q28)
- [ ] T206 [P] Update `specs/034-webapp-capstone-coverage/checklists/validation.md` cycle-1 section (CHK181..CHK215) — add a "T-id" column to each row pointing at the closing task (e.g. CHK181 → T184, CHK183 → T173/T178/T179, CHK184 → T188/T190/T199, CHK185 → T193..T198, CHK191 → T175/T177, CHK202 → T177, CHK205 → T187..T192, CHK210..CHK212 → T203, CHK213 → T200, CHK214 → T201, CHK215 → T202); checkboxes are NOT ticked here — actual closure is recorded at `/speckit.implement` per the validation gate rules (FR-023; CHK181..CHK215)

---

## Dependencies & Execution Order — Cycle-1

```text
Phase 9  (T173, T174)               ──▶ Phase 10 (T175..T177, depth-profile family)
                                    ▷    Phase 11 (T178..T181, evaluator + audit-list — parallel with Phase 10)
Phase 10 + Phase 11                 ──▶ Phase 12 (T182, T183, cycle metadata)
Phase 10 + Phase 11 + Phase 12      ──▶ Phase 13 (T184..T186, workflow refactors)
Phase 13                            ──▶ Phase 14 (T187..T199, FR-030 net-new — all [P])
                                    ▷    Phase 15 (T200..T202, env-var — all [P], no blocker)
                                    ▷    Phase 16 (T203, SC-012 closure — needs T182/T183)
Phase 14 + Phase 15 + Phase 16      ──▶ Phase 17 (T204..T206, docs polish — all [P])
```

### Cycle-1 parallel opportunities

- **T173 ⇄ T174**: contract reviews touch independent files → parallel-safe.
- **T175 ⇄ T178/T179/T181**: depth-profile YAML authoring is independent from FastAPI router scaffolding → cross-phase parallel.
- **T187..T199**: 13 FR-030 spec files → all parallel; can be split across 4 owners (SA+WA+TAS, ACT+NT, Commonwealth, cross-sector).
- **T200 ⇄ T201 ⇄ T202**: env-var canonicalisation hits 3 independent files → parallel-safe.
- **T204 ⇄ T205 ⇄ T206**: documentation files → parallel-safe.

### Cycle-1 implementation strategy (MVP slice)

1. **T173 → T174 → T178 → T179 → T180 → T181**: light a single SC-001 evaluator path end-to-end; one capstone outcome spec passes against the wired endpoint. This is the cycle-1 MVP slice that proves FR-028 + FR-029 for one persona × one outcome.
2. **T175 (10 operational profiles first) → T176 → T184 (10 operational specs)**: extend to all operational personas; gate now binary on 10/10 operational depth profiles + 10/10 operational specs passing.
3. **T175 (58 sector profiles) + T184 (71 sector specs) + T185 + T186 in parallel**: complete the 68/68 + 5/5 capstone fan-out; sector authors run in parallel per Q23 jurisdiction.
4. **T187..T199 in parallel**: FR-030 net-new specs.
5. **T200..T202 + T203 + T204..T206**: cleanup, closure measurement, docs.

---

## Notes — Cycle-1 deltas

- All cycle-1 tasks are **route-only** or **script-only** additions per `plan.md` §Cycle-1 amendment summary — no net-new Azure resource (OOS-003 still holds), no IdP changes (OOS-007 still holds), no persona inventory changes (FR-002 stable at 68).
- The dual-guard activation rule (`AMA_TEST_SUPPORT == "1"` AND `environment in {"dev","test"}`) is the **canonical name** per `contracts/persona-fixture.contract.md` and Pass 5 Q25; T200..T202 align downstream consumers (CI workflow, quickstart, README) to that canonical name.
- The `safety_critical_workflow` enum is closed at 12 values (per Q24): 9 write paths (`approve|publish|allocate|decline|queue-and-sync|escalate|handover|declare|reopen`) + 3 read-only paths (`observe-tamper-resist|report-generate|export-evidence`). Any additional value requires a `_schema.json` amendment + a Pass-4 / Pass-5 clarifications round.
- FR-030 folder placement follows Q23 owning-persona rule: `nema.dacc-jatwc-cross-jurisdiction.spec.ts` lives under `sectors/commonwealth/` (NEMA is Commonwealth-owned) NOT `sectors/cross-sector/`; cross-jurisdiction reach is recorded in `coverage_tags[]` in the depth-profile YAML.
- SC-012 closure measurement (T203) explicitly excludes escalated rows (`iteration_count >= 4`) from BOTH numerator and denominator — escalation is a separate constitutional path (§IV audit trail still captures them) per CHK211.
- Re-running `python scripts/web-coverage/_lib/persona_spec_generator.py` on the same depth-profile YAML inputs MUST produce byte-equal Playwright spec output (SC-010, RISK-13) — T176 enforces this.

---

**End of cycle-1 amendment tasks** — Total: 34 tasks (T173..T206). Cycle-0 + cycle-1 grand total: 206 tasks. Ready for `/speckit.analyze`.


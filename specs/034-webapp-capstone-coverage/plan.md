# Implementation Plan: Web Application Capstone Coverage Validation

**Branch**: `034-webapp-capstone-coverage` · **Spec**: `specs/034-webapp-capstone-coverage/spec.md`
**Date**: 2025-11-20 · **Author**: planning agent (grounded in 17-agent technical input)
**Status**: Phase 0 + Phase 1 complete · Ready for `/speckit.tasks`

## Summary

Spec 034 demands a re-runnable, persona-driven Playwright suite that **proves**
the AMA web app meets the capstone (5 outcomes × 68 personas = 10 operational +
58 sector / jurisdiction). This plan composes onto the existing tech stack
(Next.js 16.2.4 + React 19.1.0 + FastAPI + Cosmos DB + Playwright 1.59.1 + pnpm
10.6.3 + Python 3.12) without forking the build, treats existing Bicep infra
under `infra/bicep/` as sacrosanct, and proposes only **one** net-new Azure
resource (an immutable Blob container for evidence retention) plus a
conditional Content Safety candidate gated behind a registered gap.

The deliverable is fundamentally a **validation suite** — not a product
feature. Its outputs are: (a) `coverage-trace.{md,json}` mapping every
(persona × outcome × hazard) tuple to passing test IDs and audit evidence;
(b) `gap-register.md` driving FR-005 closure cycles; (c) `review-log.md`
recording the 85-agent iteration tribunal; (d) a binary CI gate (FR-023)
that blocks merge to `main` while any `Failing` trace row exists; and
(e) an FR-027 rollback manifest co-located with each deployment.

Hard limits: ≤ 30 min single-runner dev loop; ≤ 45 min CI; deterministic
on `bootstrap_seed_data()`; FR-024 max-3-cycles before escalation;
FR-027 sub-10-min auto-rollback honouring spec-029.

## Technical Context

**Language**: TypeScript 5.6 (Playwright tests, page objects, fixtures, custom
reporter) + Python 3.12 (gap-register CLI, review-log CLI, trace-merge CLI).
**Runtimes**: Node.js 24 LTS (per repo `package.json`), Python 3.12
(per `pyproject.toml`).
**Primary tools**: `@playwright/test@1.59.1` (existing), `@axe-core/playwright@^4.10.0`
(NEW devDep), `js-yaml@^4` (transitive, used directly), `ajv@^8` (existing).
**Test framework**: Playwright with custom `Reporter` implementation; existing
`apps/web/playwright.config.ts` extended (NOT replaced) with three new
projects.
**Storage**: existing Azure Storage (`${envPrefix}storage`) — adds one container
`web-coverage-evidence` (7-yr immutable). Existing `audit/` containers reused
for gap-register JSONL append.
**Observability**: existing `drh-app-insights` + `drh-log-analytics` (no new
workspace). The trace emitter publishes custom events
`web_coverage.scenario.{started,passed,failed}` via the already-pinned
`@azure/monitor-opentelemetry` package.
**Identity / RBAC**: managed identity of the existing `${envPrefix}-api`
Container App acquires write-only `Storage Blob Data Contributor` on the new
container. No new service principal, no new Key Vault. Persona impersonation
goes through a new test-support endpoint (env-gated; never enabled in
production).
**CI/CD**: extends `.github/workflows/ci.yml` with 3 new jobs (no new workflow
files); composes with existing `cd.yml` known-good revision recording (line
238–264) for FR-027 rollback evidence.
**Deployment platform**: same as the rest of the repo — Azure Container Apps
in `australiaeast` only (constitution VIII, Non-Negotiable #2).
**Performance constraints**: ≤ 30 min dev loop, ≤ 45 min CI, audit append
≤ 2 s, signal-to-action measurable per persona scenario.
**Determinism constraints**: no `page.waitForTimeout`, three-run reaffirmation
for known-good promotion, zero retries on PRs.
**Security constraints**: no PII in artefacts (redaction reporter); carve-out
registry remains source of truth for FR-018(c); test-support endpoints refuse
to start in production.

## Constitution Check

> Per `.specify/memory/constitution.md` v1.2.0 with v1.1 carve-out clauses,
> verified against the spec's NFRs.

| Clause                                                       | How this plan honours it                                                                                                       |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| I. Primacy of Life & Safety                                  | FR-009 HITL tests (deterministic structured-JSON model output, never autonomous action); FR-027 rollback within 10 min.        |
| II. AEMA #1–#11 alignment                                    | Cross-cutting suite asserts each principle has at least one passing persona × clause × evidence row.                           |
| II-A. AIIMS function map                                     | Persona fixture loads the 5 AIIMS roles from seed; RBAC tests assert function-only authorisation, no platform-elevated.        |
| III. Multi-Hazard universality                               | FR-016 hazard-pair fixtures cover bushfire, cyclone, flood, storm, heat, earthquake/tsunami AWS path.                          |
| IV. Auditability & Transparency                              | Audit append ≤ 2 s assertion in every state-changing test; immutable Blob container retains evidence for 7 years.              |
| V. Warning System Cohesion                                   | FR-011 AWS test asserts CAP envelope, BoM/Geoscience NTWC integration, fallback to operator approval on degradation.           |
| V-A / V-B / V-C. SoP, Standardisation, Continual Improvement | AWS workflow test exercises mandated SoP; warnings rendered in EN/zh-Hans/`aus-x-atsi-placeholder`; gap register drives CI.    |
| VI. Evacuation Doctrine                                      | FR-012 5-stage evacuation path tested with vulnerable-population fields populated.                                             |
| VII. Recovery Doctrine                                       | FR-013 4-environment recovery test (Built / Economic / Natural / Social).                                                      |
| VIII. Cloud Platform Sovereignty                             | All new infra `australiaeast`; AVM-first acceptable for child Blob container.                                                  |
| Non-Negotiable #1 HITL                                       | FR-009 enforced; review-log records human dispositions.                                                                        |
| Non-Negotiable #2 Data Sovereignty                           | FR-018 triple verified per scenario: code path + gateway probe + carve-out YAML.                                               |
| Non-Negotiable #5 Graceful Degradation                       | FR-017 offline / partition test asserts user-visible status banner + safe-mode UX.                                             |
| QG-1 Public Outputs                                          | Audit / outputs surfaced in tests carry the `data-classification` landmark; redaction reporter prevents PII bleed.             |

**Result**: PASS. No deviations require Complexity Tracking entries.

## Architecture Overview

```
┌──────────────────────────── Developer / CI Runner ────────────────────────────┐
│                                                                                │
│   pnpm --filter @ama/web exec playwright test --project=web-coverage-…         │
│              │                                                                 │
│              ▼                                                                 │
│   ┌─────────────────────┐    ┌──────────────────────────┐                      │
│   │ Playwright Workers  │───▶│ Page Objects + Fixtures  │                      │
│   │ (4 shards × 4 wkrs) │    │ (_support/{pages,fixtures})                     │
│   └──────────┬──────────┘    └────────────┬─────────────┘                      │
│              │ test.info().annotations: {type:"coverage", ...}                  │
│              ▼                            ▼                                    │
│   ┌─────────────────────┐    ┌──────────────────────────┐                      │
│   │ Custom Reporter     │    │ Browser session ▶︎ Web App│                      │
│   │ (_support/reporter) │    │   http://127.0.0.1:3000  │ (next dev)           │
│   └──────────┬──────────┘    └────────────┬─────────────┘                      │
│              │                            │                                    │
│              │                            ▼                                    │
│              │                ┌──────────────────────────┐                      │
│              │                │ FastAPI ─ /api/* +       │                      │
│              │                │ /api/test-support/* (gated)                     │
│              │                └────────────┬─────────────┘                      │
│              │                             │                                   │
│              │     ┌───────────────────────┼───────────────────────┐           │
│              │     ▼                       ▼                       ▼           │
│              │  Cosmos DB             Blob Storage              App Insights / │
│              │  (seeded by            (audit/, web-coverage-    Log Analytics  │
│              │  bootstrap_seed_data)   evidence/)               (existing)     │
│              ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐     │
│   │ specs/034-webapp-capstone-coverage/                                  │     │
│   │   coverage-trace.md / coverage-trace.json   (FR-004)                 │     │
│   │   gap-register.md                            (FR-005)                │     │
│   │   review-log.md                              (FR-008 + ASM-006)      │     │
│   │   known-good.json                            (FR-027 manifest)       │     │
│   └─────────────────────────────────────────────────────────────────────┘     │
│              │                                                                 │
│              ▼                                                                 │
│   GitHub Actions: ci.yml `web-coverage-shard` → `web-coverage-merge` →         │
│                   `web-coverage-gate` ─▶ blocks merge to main                  │
│                                                                                │
│   Nightly: web-coverage-iteration.yml runs 85-agent review tribunal,           │
│            updates gap-register and (if quorum) amends spec / closes gaps.     │
└────────────────────────────────────────────────────────────────────────────────┘
```

Key arrows the suite must verify in addition to the obvious browser→web-app
path:
- **Web app ↔ FastAPI** — every state-changing call asserted with
  `expect.poll` on the audit GET endpoint.
- **FastAPI ↔ Cosmos DB** — verified indirectly via the audit response and
  via re-reads of the resource through subsequent persona views.
- **FastAPI ↔ Blob Storage (audit)** — directly asserted via the
  audit_id ↔ blob path mapping.
- **FastAPI ↔ Foundry/AOAI gateway** — exercised via FR-018(b) probe;
  classification denial path asserted explicitly.
- **Web app ↔ Front Door / CDN** — out of scope; the suite hits the
  Container App directly via dev URL (FR-021).
- **App Insights / Log Analytics** — receives custom events from the
  reporter for portfolio dashboards (spec-028).

## Module Breakdown

```
tests/e2e/web-coverage/
├── operational/                              # 10 operational personas
│   ├── 01-incident-controller.spec.ts        # IC, AIIMS Control function
│   ├── 02-operations-officer.spec.ts
│   ├── 03-planning-officer.spec.ts
│   ├── 04-logistics-officer.spec.ts
│   ├── 05-public-information.spec.ts
│   ├── 06-recovery-coordinator.spec.ts
│   ├── 07-volunteer-coordinator.spec.ts
│   ├── 08-resource-deployer.spec.ts
│   ├── 09-evacuation-marshal.spec.ts
│   └── 10-warning-officer.spec.ts
├── sectors/                                  # 58 sector personas
│   ├── nsw/{rfs,ses,nswpol,health,...}.spec.ts
│   ├── vic/{cfa,vicses,vicpol,health,...}.spec.ts
│   ├── qld/{qfes,sesqld,qps,qhealth,...}.spec.ts
│   ├── sa/{sa-cfs,sa-ses,sapol,sa-health}.spec.ts
│   ├── wa/{wa-dfes,wapol,wa-health,...}.spec.ts
│   ├── tas/{tas-fire,tas-ses,tas-pol,tas-health}.spec.ts
│   ├── act/{act-esa,act-pol,act-health}.spec.ts
│   ├── nt/{nt-pfes,nt-pol,nt-health}.spec.ts
│   ├── commonwealth/{nema,bom,geoscience,defence-dacc,abs,abc-emergency,esta-triple-zero}.spec.ts
│   └── cross-sector/{ica,red-cross,salvation-army,electricity-tx,water-utils,telco,supply-chain,disability,health-utility,multi-faith}.spec.ts
├── cross-cutting/
│   ├── span-of-control.spec.ts               # AEMA #4
│   ├── audit-trail.spec.ts                   # constitution IV
│   ├── data-sovereignty.spec.ts              # FR-018 triple
│   ├── rbac.spec.ts                          # AIIMS function map
│   ├── accessibility-and-multilingual.spec.ts# FR-014 + axe + ATSI placeholder
│   ├── public-warnings.spec.ts               # FR-011 AWS / V-A / V-B / V-C
│   ├── evacuation.spec.ts                    # FR-012 + VI
│   ├── recovery.spec.ts                      # FR-013 + VII
│   ├── offline-degradation.spec.ts           # FR-017 + NN-#5
│   ├── decision-support-hitl.spec.ts         # FR-009 + NN-#1
│   ├── common-operating-picture.spec.ts      # FR-010
│   └── data-source-multiplicity.spec.ts      # FR-018(a) ≥3 sources
├── capstone/
│   ├── outcome-1-bushfire-extreme-heat.spec.ts
│   ├── outcome-2-bushfire-severe-storm.spec.ts
│   ├── outcome-3-tropical-cyclone-flood.spec.ts
│   ├── outcome-4-bushfire-cyclone-logistics.spec.ts
│   └── outcome-5-flood-storm-economic.spec.ts
└── _support/
    ├── pages/                                 # Page-object models per route
    │   ├── workspaces.po.ts                   # /workspaces/[personaId]
    │   ├── incidents.po.ts                    # /incidents/[incidentId]
    │   ├── disasters.po.ts                    # /disasters/
    │   ├── governance.dashboard.po.ts         # /governance/dashboard/*
    │   ├── governance.dataSource.po.ts        # /governance/[dataSourceId]
    │   ├── operations.workflows.po.ts         # /operations/workflows
    │   ├── preparedness.po.ts                 # /preparedness/
    │   ├── simulations.po.ts                  # /simulations/*
    │   └── eval.po.ts                         # /eval/[runId]
    ├── fixtures/
    │   ├── persona.fixture.ts                 # ASM-011 persona resolver
    │   ├── hazardScenario.fixture.ts          # FR-016 hazard pairs
    │   ├── correlationId.fixture.ts           # X-Correlation-Id propagation
    │   ├── auditObserver.fixture.ts           # ≤2 s audit assertion
    │   └── carveoutRegistry.fixture.ts        # FR-018(c) YAML loader
    ├── reporter/
    │   ├── coverage-reporter.ts               # custom Playwright Reporter
    │   ├── annotations.ts                     # typed annotation helpers
    │   ├── trace-row.ts                       # row dedupe + TestID join
    │   └── redact.ts                          # PII redaction
    ├── validators/
    │   ├── outcome-proxy.ts                   # SC-005 economic loss proxy
    │   ├── aws-cap-envelope.ts                # CAP v1.2 validator
    │   └── pspf-classification.ts             # FR-018 PSPF marker validator
    ├── a11y/
    │   ├── axeBuilder.ts                      # WCAG 2.2 AA wrapper
    │   └── languagePackProbe.ts               # EN, zh-Hans, aus-x-atsi-placeholder
    ├── eslint-rules/
    │   └── no-waitfortimeout.cjs              # determinism guard
    └── types/
        ├── coverage.d.ts                      # CoverageTraceRow type
        ├── gap.d.ts                           # GapRegisterEntry type
        └── review.d.ts                        # ReviewVote type

tests/e2e/web-coverage/_artifacts/             # gitignored
├── coverage-trace.partial-{shard}.json
├── junit/
├── screenshots/
└── gap-register-audit.jsonl                   # local dev fallback

scripts/web-coverage/
├── gap-register.py                            # FR-005 state machine CLI
├── review-log.py                              # 85-agent vote recorder + panel resolver
├── trace-merge.py                             # multi-shard trace merger
└── known-good.py                              # FR-027 manifest manager

specs/034-webapp-capstone-coverage/
├── plan.md                                    # this file
├── research.md                                # phase 0
├── data-model.md                              # phase 1
├── quickstart.md                              # phase 1
├── coverage-trace.md                          # generated, deterministic
├── coverage-trace.json                        # generated, deterministic
├── gap-register.md                            # FR-005 source-of-truth markdown
├── review-log.md                              # 85-agent tribunal log
├── known-good.json                            # FR-027 manifest (committed)
└── contracts/
    ├── coverage-trace-row.schema.json
    ├── gap-register-entry.schema.json
    ├── review-vote.schema.json
    ├── persona-fixture.contract.md
    └── agent-objection.schema.json
```

### Page-object responsibilities

Each PO file exposes a typed surface for one route. Page objects MUST:
- Locate elements via `getByRole`, `getByLabel`, `getByTestId` — never CSS.
- Forbid `page.waitForTimeout`; use `expect.poll` or implicit Playwright
  awaits.
- Carry no state; receive `Page`, `personaContext`, and
  `correlationId` from fixtures.
- Expose `audit{ActionName}()` helpers that return the audit_id observed
  for the most recent action.

### Fixtures

- `personaFixture` — calls `GET /api/test-support/personas/{id}`, sets
  the `X-Test-Persona-Id` header, exposes `{id, role, jurisdiction,
  permissions}`. Worker-scoped to keep cost amortised.
- `hazardScenarioFixture` — loads the matching
  `outcome-N-{pair}.fixture.json`, calls
  `POST /api/test-support/seed/scenario` (gated) to materialise the
  hazard pair into Cosmos for the test's lifetime, returns the
  `incident_id` and `disaster_id` chain.
- `correlationIdFixture` — `crypto.randomUUID()`, attaches
  `X-Correlation-Id` to every request via
  `context.setExtraHTTPHeaders`.
- `auditObserverFixture` — wraps `expect.poll(GET /api/audits?cid=...)`
  with the 2-second deadline.
- `carveoutRegistryFixture` — reads
  `infra/parameters/foundry-carveout.yaml` once per worker, validates
  with `ajv`, exposes typed accessor.

### Custom reporter

Implements:
- `onTestEnd(test, result)` — extracts annotations, dedupes by tuple,
  buffers in-memory.
- `onEnd(result)` — flushes a partial JSON named
  `coverage-trace.partial-${process.env.PW_SHARD ?? "1"}.json` with the
  shard's rows; never overwrites canonical files.
- `onStdErr` — captures lint of `waitForTimeout` matches and converts
  them to test failures.

`scripts/web-coverage/trace-merge.py` runs in the merge job, sorts by
`(persona, outcome, hazard, fr_id)`, joins duplicate test IDs with `;`,
emits the canonical `coverage-trace.md` (Markdown table) and
`coverage-trace.json` (JSON array).

## Data Flow — Trace Emitter

```
┌── Test ──────────────────────────────────────┐
│ test.info().annotations.push({               │
│   type: "coverage",                           │
│   description: JSON.stringify({               │
│     persona: "ic-nsw-rfs",                    │
│     outcome: 1,                               │
│     hazard: "bushfire+extreme-heat",          │
│     fr: "FR-009",                             │
│     test_id: test.info().titlePath.join("/"), │
│     route: "/incidents/inc-001",              │
│     audit_evidence_id: auditId,               │
│     status: "passed",                         │
│     duration_ms: 2410,                        │
│     correlation_id: cid                       │
│   })                                          │
│ });                                           │
└──────────────┬──────────────────────────────┘
               │ Playwright events
               ▼
┌── Reporter (per-shard) ─────────────────────┐
│ onTestEnd: collect all annotations           │
│ onEnd: write coverage-trace.partial-N.json   │
└──────────────┬──────────────────────────────┘
               │ artefact upload
               ▼
┌── Merge job (single CI runner) ─────────────┐
│ trace-merge.py partial-1..N.json             │
│  ▶ dedupe by (persona, outcome, hazard, fr)  │
│  ▶ join test_ids with ";"                    │
│  ▶ emit specs/034-…/coverage-trace.json      │
│  ▶ emit specs/034-…/coverage-trace.md        │
│  ▶ assert determinism: re-run merge with     │
│    same input → byte-equal output (SC-010)   │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌── Gate job ──────────────────────────────────┐
│ Validate JSON against contracts/coverage-    │
│ trace-row.schema.json                        │
│ Fail gate if any row.status === "failing"    │
│ Fail gate if FR-002 personas[] not all       │
│ covered (10 op + 58 sector + 5 outcome)      │
└─────────────────────────────────────────────┘
```

## Gap-Register State Machine

State diagram (per FR-005 + Q11):

```
                ┌─────────────┐
   open ──────▶ │   Open      │
                └──────┬──────┘
                       │ progress (closing PR id)
                       ▼
                ┌─────────────┐
                │ In-Progress │
                └──────┬──────┘
                       │ close (merge SHA + passing test ID)
                       ▼
                ┌─────────────┐
                │   Closed    │
                └──────┬──────┘
                       │ regress (FR-027 trigger:
                       │  same test FAILS again
                       │  on a later commit)
                       ▼
                ┌─────────────┐
                │  Reopened   │ ──▶ progress (new PR)
                └──────┬──────┘
                       │ escalate (iteration_count >= 4)
                       ▼
                ┌─────────────┐
                │  Escalated  │  (frozen counter, project-lead disposition)
                └─────────────┘
```

Invariants enforced by `gap-register.py`:
- Transition `Open → In-Progress` requires `closing_pr_url` non-empty.
- Transition `In-Progress → Closed` requires `merge_sha` non-empty AND a
  successful suite run on `merge_sha` AND the previously failing test
  ID now `passing`.
- Transition `Closed → Reopened` (regression) records
  `failing_test_id`, `reverted_commit_sha`, `restored_revision_sha` —
  feeds FR-027 manifest.
- `iteration_count` increments on each `Reopened → In-Progress` cycle.
- On `iteration_count >= 4`, force `Escalated`; freeze counter; emit
  `gap.escalated` audit.

Persistence: every transition appends a JSONL row to
`audit/web-coverage-gaps/{date}/{hour}.jsonl` via `AuditWriter`.
The markdown table at `specs/034-webapp-capstone-coverage/gap-register.md`
is the **source of truth** for human review; the JSONL stream is the
**append-only audit shadow**.

## CI Integration

### `.github/workflows/ci.yml` (extended; not replaced)

Existing jobs (unchanged): `quality`.

New jobs (added in dependency order):

1. **`web-coverage-shard`** — `needs: [quality]`
   - `runs-on: ubuntu-latest`
   - `strategy: fail-fast: false, matrix: { shard: [1, 2, 3, 4] }`
   - `timeout-minutes: 45`
   - Steps:
     - `actions/checkout@v4`
     - `actions/setup-node@v4` (node 24, pnpm cache)
     - `actions/setup-python@v5` (3.12, pip cache)
     - `actions/cache@v4` for `~/.cache/ms-playwright`
     - `pnpm install --frozen-lockfile`
     - `python -m pip install -e apps/api`
     - `pnpm exec playwright install --with-deps chromium`
     - `python scripts/seed-database.ps1` *(via pwsh on ubuntu)*
     - `corepack pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --shard=${{ matrix.shard }}/4 --reporter=junit,json,./tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts`
     - `actions/upload-artifact@v4`: shard partial JSON, JUnit XML,
       redacted screenshots.

2. **`web-coverage-merge`** — `needs: [web-coverage-shard]`
   - Downloads all 4 shard artefacts.
   - `python scripts/web-coverage/trace-merge.py
       --inputs tests/e2e/web-coverage/_artifacts/coverage-trace.partial-*.json
       --out-md specs/034-webapp-capstone-coverage/coverage-trace.md
       --out-json specs/034-webapp-capstone-coverage/coverage-trace.json`
   - `python scripts/web-coverage/gap-register.py validate`
   - Uploads canonical artefacts.

3. **`web-coverage-gate`** — `needs: [web-coverage-merge]`
   - Validates `coverage-trace.json` against
     `contracts/coverage-trace-row.schema.json` via `ajv`.
   - Fails if any row has `status == "failing"`.
   - Fails if persona coverage incomplete (must hit 10 + 58 + 5).
   - Posts GitHub status check `web-coverage / capstone-ready`.

Required for PR merge to `main`: all three jobs succeed.

### `.github/workflows/cd.yml` (composed, not modified)

The existing CD pipeline already records known-good revisions
(lines 238–264). The plan adds **one** new step **after** the
`record-revisions` step:

```yaml
      - name: Update FR-027 known-good manifest
        run: |
          python scripts/web-coverage/known-good.py update \
            --commit "${{ github.sha }}" \
            --revisions-json "${{ steps.record-revisions.outputs.json }}" \
            --trace specs/034-webapp-capstone-coverage/coverage-trace.json
          git add specs/034-webapp-capstone-coverage/known-good.json
          git -c user.name="ama-bot" -c user.email="… " commit -m "chore: update known-good manifest [skip ci]"
          git push
```

The CD rollback step (FR-015a) consumes
`specs/034-webapp-capstone-coverage/known-good.json` to identify the
previous restored revision when the auto-rollback fires.

### `.github/workflows/web-coverage-iteration.yml` (NEW)

New workflow file (only one created); triggers documented in R-019:
- `schedule: cron: "0 16 * * *"` (02:00 AEST)
- `workflow_dispatch: inputs.gap_id`
- `pull_request: types: [closed], paths: ["specs/034-**"]`

Runs `scripts/web-coverage/review-log.py run`, opens follow-up PRs as
the bot identity.

## Iteration Loop (85-Agent Tribunal)

Per spec ASM-006 + Q13:

```
Day N        Suite runs in CI
             ▼
             coverage-trace.json + gap-register.md updated
             ▼
Night N+1   web-coverage-iteration.yml fires
             ▼
             For each unresolved gap (Status ∈ {Open, In-Progress, Reopened}):
               ▶ Load relevant agents from .github/agents/{op,sector,tech}/
               ▶ Each agent emits a JSON objection (or +1) per
                 contracts/agent-objection.schema.json
               ▶ review-log.py records vote, computes panel outcomes:
                   - meritorious if ≥2/3 of relevant panel
                   - operational-panel veto on safety-critical clauses
               ▶ If meritorious AND iteration_count < 4:
                   ▶ amend gap row (next_action, owner)
                   ▶ if spec change required, open PR amending spec
                   ▶ increment iteration_count
               ▶ If iteration_count == 3:
                   ▶ next failure → mark Escalated
               ▶ Bot commits with Co-authored-by: Copilot trailer
             ▼
PR opened → human reviewer → merge → suite re-runs → cycle continues
```

Veto resolution (per Q13):
- Operational-panel meritorious objection on
  `clause ∈ {I, IV, NN-1, NN-2}` blocks closure regardless of other
  panels.
- Standard meritorious objection blocks closure unless overridden by
  ≥ 50% of *all* 85 agents (`override_supermajority`).
- All overrides written to `review-log.md` with rationale.

## Net-New Azure Resources

### Adopted (1)

| Resource | Type | SKU / Config | Why |
|----------|------|---------|-----|
| `web-coverage-evidence` | `Microsoft.Storage/.../containers@2023-05-01` (child of existing `${envPrefix}storage`) | Immutable container, 7-yr `period`, `allowProtectedAppendWrites: true` | GitHub Actions retention is 90 days; spec-029 requires 7-yr audit retention; this single child resource closes the gap without creating a new top-level account. |

Bicep delta (added to `infra/bicep/main.bicep`):

```bicep
resource webCoverageEvidence 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: storageBlob
  name: 'web-coverage-evidence'
  properties: {
    publicAccess: 'None'
    immutableStorageWithVersioning: { enabled: true }
  }
}

resource webCoverageEvidenceImmutability 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  parent: webCoverageEvidence
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: 2557 // 7 years
    allowProtectedAppendWrites: true
  }
}
```

RBAC: extend the API Container App's managed identity assignment with
`Storage Blob Data Contributor` scoped to this container only (no
account-level grant).

### Rejected (with reasons)

| Resource | Why rejected |
|----------|--------------|
| New Application Insights | `drh-app-insights` already deployed; reuse via OTel. |
| New Log Analytics workspace | `drh-log-analytics` already deployed; second workspace fragments queries. |
| New Key Vault | Suite needs no new secrets; persona registry comes from seed JSON. |
| Azure API Management | FR-018(b) gateway lives in `apps/agents/common/safety/classification.py` (ADR-033 Layer 2); no APIM benefit. |
| Azure Container Registry | CI runs Playwright on `ubuntu-latest`; no container image required. |
| Azure Front Door dev profile | FR-021 pins `http://127.0.0.1:3000` for dev runs; CDN not on the test path. |
| Service Bus / Event Grid for trace events | OTel → App Insights is sufficient and existing. |

### Conditionally proposed (deferred)

| Resource | Trigger condition | Decision |
|----------|------------------|----------|
| Azure AI Content Safety | If FR-018 gateway tests show rule-based classifier missing PSPF markers in real failure cases. | Tracked as `GAP-AI-CONTENT-SAFETY-CANDIDATE` with status `Open`; resolved at `/speckit.tasks` or first iteration cycle. |

## Risk Register

Drawn from technical-input.md (lines 300–311) plus this plan's analysis:

| ID  | Risk | Likelihood | Impact | Mitigation | Owner |
|-----|------|-----------|--------|-----------|-------|
| RISK-01 | 68 personas × 5 outcomes pushes runtime past 45 min budget | Medium | High | 4-shard matrix; per-shard caching; `@p1` smoke subset for PRs; nightly full sweep | qa-test-engineer |
| RISK-02 | LLM-driven HITL UI emits non-deterministic JSON, breaking SC-010 | Medium | High | FR-009 schema-locked structured outputs; tests assert against fixtures, not free text | ai-ml-engineer |
| RISK-03 | Carve-out registry drift between YAML and OPA policy | Low | High | Shared schema validation; FR-018(c) test reads YAML directly; OPA gate runs in same CI | security-engineer |
| RISK-04 | Persona impersonation endpoint leaks into production | Low | Critical | Two-sided env guard (API + middleware); refusal returns 404 + audit; CD pipeline checks for `AMA_TEST_SUPPORT` env var = unset on staging/production | sre-engineer |
| RISK-05 | Audit append > 2 s under shard-parallel load | Medium | Medium | Existing audit_writer is async + batch-resilient; tests poll with `expect.poll`; CI uses dedicated test storage account if shared one shows contention | data-engineer |
| RISK-06 | Flake bleeds into FR-027 rollback metric | Medium | High | Lint forbids `waitForTimeout`; zero retries on PRs; flake-detected events surface in gap register | qa-test-engineer |
| RISK-07 | PII leakage into screenshots / videos / JSON | Medium | Critical | `_support/reporter/redact.ts` redacts before artefact upload; failure tracing disabled by default | security-engineer / compliance-auditor |
| RISK-08 | 85-agent loop produces unbounded debate (no convergence) | Medium | Medium | FR-024 max-3-cycles → forced escalation; review-log records iteration_count; project-lead breaks ties | principal-engineer |
| RISK-09 | Hazard-pair fixtures over-fit to specific events, missing coverage breadth | Low | Medium | Use AU-canonical events as exemplars; review-loop catches gaps in hazard-pair fidelity | doctrine-architect |
| RISK-10 | New Blob container's RBAC assignment too broad | Low | High | Scope `Storage Blob Data Contributor` to *container*, not account; verified by `verify-iam-zero-trust.ps1` | iam-architect |
| RISK-11 | ATSI placeholder language strategy mis-perceived as substituting for real Indigenous-led translation | Low | High | Visible disclaimer in UI; explicit BCP-47 private-use subtag; deferred canonical selection per spec-028 | accessibility-tester / cultural-advisor |
| RISK-12 | CI artefact retention exceeds AU residency boundary | Low | High | Artefacts stored in GitHub-hosted runners (US/EU), copied within ≤ 90 days to `web-coverage-evidence` (`australiaeast`); raw artefacts redacted of PII before upload | compliance-auditor |
| RISK-13 | Trace merge non-determinism (sort order) | Low | Medium | `trace-merge.py` sorts by tuple keys; CI re-runs merge twice on same inputs and asserts byte-equal output | qa-test-engineer |
| RISK-14 | Adding evidence container subtly delays CD on first deploy | Low | Low | Idempotent Bicep; deployed once per env; no runtime hot-path | platform-engineer |
| RISK-15 | Sector personas reference seeded orgs that break when seed schema evolves | Medium | Medium | `bootstrap_seed_data()` is the single SoT; persona fixture asserts org_id presence and fails fast with actionable message | data-engineer |

## Hazard-Pair Coverage (FR-016)

| Outcome | Hazard pair (mandatory) | Fixture | Trace tags |
|---------|------------------------|---------|-----------|
| 1: Lives saved (zero preventable deaths) | Bushfire AND Extreme heat | `outcome-1-bushfire-extreme-heat.fixture.json` | `@outcome:1 @hazard:bushfire @hazard:extreme-heat` |
| 2: 50% faster signal-to-action | Bushfire AND Severe storm | `outcome-2-bushfire-severe-storm.fixture.json` | `@outcome:2 @hazard:bushfire @hazard:severe-storm` |
| 3: 24-hour evac uplift | Tropical cyclone AND Riverine flood | `outcome-3-tropical-cyclone-flood.fixture.json` | `@outcome:3 @hazard:tropical-cyclone @hazard:flood` |
| 4: 30% logistics-friction reduction | Bushfire AND Tropical cyclone | `outcome-4-bushfire-cyclone-logistics.fixture.json` | `@outcome:4 @hazard:bushfire @hazard:tropical-cyclone` |
| 5: 30% economic-loss reduction | Riverine flood AND Severe storm | `outcome-5-flood-storm-economic.fixture.json` | `@outcome:5 @hazard:flood @hazard:severe-storm` |
| n/a (FR-011 only) | Earthquake / Tsunami | seeded but not paired (AWS-only) | `@hazard:earthquake @hazard:tsunami @aws` |

## NFR Verification

| NFR / SC | Plan element verifying it | Test surface |
|----------|---------------------------|--------------|
| SC-001 — every persona × outcome × hazard has ≥1 passing scenario | trace-merge gate | `web-coverage-merge` job |
| SC-002 — ≥1 cross-cutting clause assertion per persona | reporter dedupe + persona coverage check | `web-coverage-gate` job |
| SC-003 — ≥3 dependency-hazard cross-jurisdictional traces | hazard-pair fixtures + tag selectors | `capstone/*` |
| SC-004 — Audit append ≤ 2 s | `auditObserverFixture` + `expect.poll` | every state-changing test |
| SC-005 — Outcome-proxy assertion per outcome | `validators/outcome-proxy.ts` | `capstone/*` |
| SC-006 — FR-018 triple per scenario | `cross-cutting/data-sovereignty.spec.ts` | every cross-cutting + capstone test |
| SC-007 — Gap closure cycle ≤ 3 cycles | FR-024 enforced by `gap-register.py` | review-log + escalation path |
| SC-008 — FR-027 rollback ≤ 10 min | known-good manifest + cd.yml step | CD pipeline post-deploy |
| SC-009 — FR-014 a11y on P1 surfaces | `web-coverage-axe` project | nightly + PR `@p1` |
| SC-010 — 3 consecutive identical runs | `known-good.py reaffirm` | nightly main-branch run |
| SC-011 — Dev loop ≤ 30 min | 4-worker default; spec gates Single-runner perf in `quickstart.md` | local profiling |

## Project Structure Decisions

- **Test root**: `tests/e2e/web-coverage/` (sibling to existing
  `tests/e2e/*.spec.ts`); allows the new suite to evolve without
  touching legacy specs.
- **Tooling root**: `scripts/web-coverage/` (consistent with
  existing `scripts/` Python conventions; not under
  `tools/` because the latter holds repo-management scripts).
- **Generated artefacts**: under `specs/034-webapp-capstone-coverage/`
  for the canonical files (committed); under
  `tests/e2e/web-coverage/_artifacts/` for shard-partials (gitignored).
- **Page objects vs fixtures**: page objects own DOM contracts; fixtures
  own cross-cutting state (persona, scenario, correlation, audit).
- **Tag taxonomy** finalised in R-017; tasks output in `/speckit.tasks`
  will register the lint rules to enforce one-of-each.

## Phase 0 Output (`research.md`)

All `NEEDS CLARIFICATION` resolved. See `research.md` for R-001 through
R-019 decisions, rationales, and rejected alternatives.

## Phase 1 Outputs

- `data-model.md` — entities and contracts.
- `contracts/coverage-trace-row.schema.json`
- `contracts/gap-register-entry.schema.json`
- `contracts/review-vote.schema.json`
- `contracts/persona-fixture.contract.md`
- `contracts/agent-objection.schema.json`
- `quickstart.md` — developer onboarding for spec 034.
- Agent context updated via
  `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`.

## Phase 2 Plan (preview)

`/speckit.tasks` will:
1. Decompose this plan into ~120 tasks across `tests/e2e/web-coverage/**`,
   `scripts/web-coverage/**`, `apps/web/playwright.config.ts`,
   `apps/api/app/routers/test_support.py`, `infra/bicep/main.bicep`
   delta, and `.github/workflows/{ci.yml,cd.yml,web-coverage-iteration.yml}`.
2. Order by dependency (fixtures → page objects → operational specs →
   sector specs → cross-cutting → capstone → gate jobs → infra).
3. Resolve the deferred ATSI BCP-47 final selection question.

## Complexity Tracking

No constitution gate violations require justification. Two
architectural choices are noted for transparency, with their
constitutional/spec citations:

| Decision | Why simpler alternatives were inadequate |
|----------|-----------------------------------------|
| Custom Playwright Reporter (vs. parsing JUnit) | JUnit cannot carry the per-row `Audit Evidence ID` cell required by FR-004 without `<system-out>` parsing, which is non-deterministic. |
| New test-support endpoint (vs. JWT injection) | Spec ASM-011 forbids fixture-only identities; persona impersonation must use seeded RBAC. Building a real Entra ID test tenant adds infrastructure (rejected per "minimal Azure additions"). The env-gated endpoint is the lowest-risk realisation. |

No further deviations.

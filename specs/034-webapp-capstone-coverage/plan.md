# Implementation Plan: Web Application Capstone Coverage Validation

**Branch**: `034-webapp-capstone-coverage` · **Spec**: `specs/034-webapp-capstone-coverage/spec.md`
**Date**: 2025-11-20 (cycle-0) · 2026-02-05 (cycle-1 amendments) · **Author**: planning agent (grounded in 17-agent technical input)
**Status**: Phase 0 + Phase 1 complete (cycle-0) · cycle-1 amendments landed (FR-028..FR-030, SC-012, depth-profile, evaluator) · Ready for `/speckit.tasks` re-run

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

**Result (cycle-0)**: PASS. No deviations require Complexity Tracking entries.

### Cycle-1 amendment Constitution re-check

> Re-evaluated 2026-02-05 after spec passes 4 + 5 (Q20..Q29; FR-028, FR-029, FR-030, SC-012). Same constitution v1.2.0; no clause additions; carve-outs unchanged.

| Cycle-1 delta | Clause(s) consulted | How this amendment honours them |
| ------------- | ------------------- | ------------------------------- |
| **FR-028 — Outcome evaluator (`POST /api/outcomes/sc-{001..005}/evaluate`) + audit-list (`GET /api/audit/list`)** | §IV (Auditability) · §V-A (AWS) · NN-2 (Sovereignty) · §VIII (Cloud Sovereignty) | Route-only addition under `apps/api/app/api/routes/`; no net-new Azure resource (OOS-003 holds, §VIII compliant). Dual-guard activation (`AMA_TEST_SUPPORT == "1"` AND `environment ∈ {dev,test}`) reuses persona-fixture middleware (Q25) so the router is *physically un-importable* in production — NN-2 preserved. Idempotency tuple `(sc_id, scenario_id, persona_id, correlation_id)` plus append-only audit-list (default `cycle=current`, max `limit=500`, cursor pagination, tamper attempts themselves audited per Q24) discharge §IV's "every action observable" requirement. SC-001..SC-005 routable; SC-006..SC-011 → 400 per Q29 because their oracles (web-coverage-gate, gap-register, verify-trace-determinism) are CI-artefact-derived and a route would corrupt the audit narrative. |
| **FR-029 — Per-persona scenario depth contract (`_lib/depth-profiles/{persona-id}.depth.yaml × 68` validated by `_schema.json` draft-07)** | §I (Primacy of Life) · §IV (Auditability) · NN-1 (HITL) | Closed enum (12 values per Q24, including the read-only triplet `observe-tamper-resist | report-generate | export-evidence`) prevents the silent-stub failure mode where a persona spec passes the suite while testing nothing safety-critical — the depth contract turns "did we test this?" into a binary, machine-checked question. T177 gate is non-bypassable. Where the panel finds the depth shallow it is FR-024-empowered to escalate without the planner being able to lower the bar. Every depth profile names the workflow + RBAC clauses + audit assertions + iteration-loop hooks — preserving §IV's traceability to constitutional clause. NN-1 unaffected: no autonomous action, only test depth specification. |
| **FR-030 — Net-new persona-level scenarios (13 specs across SA / WA / TAS / ACT / NT / Commonwealth / cross-sector)** | §III (Multi-Hazard) · §VII-A/B/C (Recovery Doctrine) · AEMA #11 (Continual Improvement) | All scenarios bind to existing FR-002 personas (no new persona ids → no IdP changes, OOS-007 holds; folder placement pivots on owning persona per Q23, *not* tags). Each scenario must conform to FR-029's depth contract (no exemption). Scenario topics chosen to fill coverage gaps in §III (storm, heat, earthquake variants) and §VII recovery environments (Built+Economic e.g. utility-insurance handoff, Social e.g. ATSI-led recovery committees). All evidence audited via the same FR-028 audit-list — single accountability surface. |
| **SC-012 — ≥ 80 % merit-validated objections closed per cycle** | AEMA #11 (Continual Improvement) · §IV (Auditability) | Per-cycle measurement via `review-log.py`; closure proven by three artefacts (gap register state + scenario PR pass + depth-contract assertion present) per the FR-024 escalation policy. Numerator/denominator/escalated set audited before each gate flip per CHK212 — meets §IV. Threshold codifies the constitutional principle that the system must *demonstrably learn* from each tribunal cycle; below-threshold closure auto-opens an iteration-loop gap per FR-005. |
| **`_artifacts/cycle-metadata.json` + `cycle_id` on `GapRegisterEntry`** | §IV (Auditability) | Per-run cycle metadata is centralised (Q26) — no per-gap-row drift; `cycle_id` is OPTIONAL on `GapRegisterEntry` (additive, non-breaking) so cycle-0 historical rows remain valid while cycle-1 rows can be filtered. Fully discharges §IV's "evidence trail tied to cycle" implicit requirement that pass 4 surfaced. |
| **Env-var canonicalisation: `AMA_TEST_SUPPORT=1`** | NN-2 (Sovereignty) · §VIII (Cloud Sovereignty) | Q25 confirmed the middleware + persona-fixture contract is canonical (CI line 147 + quickstart line 281 are drift to be fixed in T173 prep). Single env var name → impossible to "accidentally" enable test-support routes in prod via the wrong toggle — NN-2 holds. |

**Cycle-1 verdict**: **PASS**. No new deviations. No new Azure resources (§VIII compliant). No IdP changes (OOS-007 holds). No persona inventory changes (FR-002 stable). All cycle-1 additions are either route-only (under existing FastAPI app), test-only (under `tests/e2e/`), or contract-only (under `specs/034-webapp-capstone-coverage/contracts/`). Complexity Tracking entries: **none required** — every addition is constitutionally pre-authorised by §IV (Auditability) or §I (Primacy of Life).

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
├── operational/                              # 10 operational personas (spec §Cited inputs + §Suite Layout)
│   ├── incident-commander.<scenario>.spec.ts        # AIIMS Control
│   ├── operations-officer.<scenario>.spec.ts        # AIIMS Operations
│   ├── planning-officer.<scenario>.spec.ts          # AIIMS Planning
│   ├── logistics-officer.<scenario>.spec.ts         # AIIMS Logistics
│   ├── public-information-officer.<scenario>.spec.ts# AIIMS Public Information
│   ├── field-coordinator.<scenario>.spec.ts
│   ├── resilience-planner.<scenario>.spec.ts
│   ├── executive-leader.<scenario>.spec.ts
│   ├── observer-auditor.<scenario>.spec.ts
│   └── risk-manager.<scenario>.spec.ts
├── sectors/                                  # 58 sector personas (IDs match spec lines 17–19)
│   ├── nsw/{frnsw,mrnsw,nsw-ambulance,nsw-rfs,nswpf,ses-nsw}.spec.ts            # 6
│   ├── vic/{av,cfa-vic,frv,ses-vic,vicpol}.spec.ts                              # 5
│   ├── qld/{qas,qfd,qps,ses-qld}.spec.ts                                        # 4
│   ├── sa/{saas,sacfs,ses-sa,samfs,sapol}.spec.ts                               # 5
│   ├── wa/{dfes-wa,sja-wa,wapol}.spec.ts                                        # 3
│   ├── tas/{at,ses-tas,taspol,tfs}.spec.ts                                      # 4
│   ├── act/{act-ambulance,act-esa,act-fr,act-policing,act-rfs,afp,ses-act}.spec.ts # 7
│   ├── nt/{bushfires-nt,ntes,ntfrs,ntpf,sja-nt}.spec.ts                         # 5
│   ├── commonwealth/{abf,adf,afp-commonwealth,arc,asa,bom-national,ga-national,nema,rfds,sja-national,surf-lifesaving}.spec.ts # 11
│   └── cross-sector/{community-ngos,health,local-government,state-government,territory-government,transport,utility,volunteer}.spec.ts # 8
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
    ├── types/
    │   ├── coverage.d.ts                      # CoverageTraceRow type
    │   ├── gap.d.ts                           # GapRegisterEntry type
    │   └── review.d.ts                        # ReviewVote type
    └── reporter/
        └── cycle-metadata.ts                  # NEW (cycle-1, Q26): onBegin emit of _artifacts/cycle-metadata.json

tests/e2e/web-coverage/_lib/                   # NEW (cycle-1, Q20 + Q28)
└── depth-profiles/
    ├── _schema.json                           # JSON-Schema draft-07 for DepthProfile (Phase-1 contract peer)
    └── {persona-id}.depth.yaml                # 68 files — one per FR-002 persona; consumed by persona_spec_generator.py

tests/e2e/web-coverage/_artifacts/             # gitignored
├── coverage-trace.partial-{shard}.json
├── junit/
├── screenshots/
├── gap-register-audit.jsonl                   # local dev fallback
└── cycle-metadata.json                        # NEW (cycle-1, Q26): per-run cycle_start_ts / cycle_id / commit_sha / seed_hash

scripts/web-coverage/
├── gap-register.py                            # FR-005 state machine CLI
├── review-log.py                              # 85-agent vote recorder + panel resolver
├── trace-merge.py                             # multi-shard trace merger
├── known-good.py                              # FR-027 manifest manager
└── _lib/
    ├── persona_spec_generator.py              # EXTENDED (cycle-1, Q28 / T176): loads + validates depth-profile YAML; opens GAP-DEPTH-PROFILE-MISSING on miss
    └── schema_validators.py                   # T047: shared ajv-style validator (now also serves _schema.json + cycle-metadata.schema.json)

apps/api/app/api/routes/                       # NEW (cycle-1, Q21 + Q22): route-only additions, OOS-003 does NOT apply
├── outcome_evaluator.py                       # POST /api/outcomes/sc-{001..005}/evaluate; sc-006..sc-011 → 400 per Q29
└── audit_list.py                              # GET /api/audit/list?correlation_id=&cycle=&limit=&cursor=

specs/034-webapp-capstone-coverage/
├── plan.md                                    # this file
├── research.md                                # phase 0 + R-020..R-024 (cycle-1)
├── data-model.md                              # phase 1 + cycle-1 entities (DepthProfile, EvaluatorRequest, EvaluatorResponse, CycleMetadata)
├── quickstart.md                              # phase 1
├── coverage-trace.md                          # generated, deterministic
├── coverage-trace.json                        # generated, deterministic
├── gap-register.md                            # FR-005 source-of-truth markdown
├── review-log.md                              # 85-agent tribunal log
├── known-good.json                            # FR-027 manifest (committed)
└── contracts/
    ├── coverage-trace-row.schema.json
    ├── gap-register-entry.schema.json         # cycle-1: additive cycle_id field (Q26)
    ├── review-vote.schema.json
    ├── persona-fixture.contract.md
    ├── agent-objection.schema.json
    ├── outcome-evaluator.contract.md          # NEW (cycle-1, Q21 + Q27 + Q29): FR-028 evaluator + audit-list contract with embedded JSON Schemas
    └── cycle-metadata.schema.json             # NEW (cycle-1, Q26): per-run metadata schema
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
- `onBegin(config, suite)` — *(NEW, cycle-1, Q26)* writes
  `tests/e2e/web-coverage/_artifacts/cycle-metadata.json` with
  `{cycle_start_ts, cycle_id, commit_sha, seed_hash}` validated against
  `contracts/cycle-metadata.schema.json`. `cycle_start_ts` is read from
  `bootstrap_seed_data().current_cycle_start` so it byte-equals the
  server-side value the audit-list endpoint filters on (R-022 / R-023).
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
`coverage-trace.json` (JSON array). At cycle-1 it ALSO copies
`_artifacts/cycle-metadata.json` into the canonical
`coverage-trace.json` header (Q26) so any `GapRegisterEntry.cycle_id`
reference resolves without consulting the gitignored artefact.

### Cycle-1 net-new modules

> Added per spec.md passes 4 + 5 (Q20, Q21, Q22, Q26, Q27, Q28).
> Each is a route-only or script-only addition — no net-new Azure
> resource (OOS-003 still holds), no net-new top-level files outside
> the `_lib/`, `_artifacts/`, `apps/api/app/api/routes/`, and
> `contracts/` paths called out in §Project Structure above.

| Module | Path | Purpose | Source clarification |
| ------ | ---- | ------- | -------------------- |
| **Cycle metadata recorder** | `tests/e2e/web-coverage/_support/reporter/cycle-metadata.ts` | Writes `_artifacts/cycle-metadata.json` at `onBegin`. Schema-validates against `contracts/cycle-metadata.schema.json`. The merge job copies the file into the `coverage-trace.json` header. | Q26 (R-023) |
| **Outcome evaluator router** | `apps/api/app/api/routes/outcome_evaluator.py` | FastAPI router exposing `POST /api/outcomes/sc-{001..005}/evaluate`. Idempotency keyed by `(sc_id, scenario_id, persona_id, correlation_id)`. Unknown `scenario_id` → 404 + `GAP-EVALUATOR-SCENARIO-MISSING`. `sc_id ∉ {001..005}` (i.e. `sc-006..sc-011` or any other value) → 400 per Q29 with body naming the CI-artefact owner. Dual-guard activation reuses the persona-fixture middleware (`AMA_TEST_SUPPORT == "1"` AND `environment in {dev,test}`) — router is not registered in production. | Q21 + Q27 + Q29 (R-021) |
| **Audit-list endpoint** | `apps/api/app/api/routes/audit_list.py` | FastAPI router exposing `GET /api/audit/list?correlation_id={uuid}&cycle={current\|all}&limit={1..500}&cursor={opaque}`. Default `cycle=current` filters by `bootstrap_seed_data().current_cycle_start` (server-side; never reads the gap register or `_artifacts/cycle-metadata.json`). Cursor-based pagination, `limit` capped at 500. Append-only retention; tamper attempts are themselves audit rows per Q24 (a). | Q22 (R-022) |
| **Depth-profile validator + generator extension** | `scripts/web-coverage/_lib/persona_spec_generator.py` (extended; T176) | Loads `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`, validates against `_schema.json` via `schema_validators.py` (T047), emits a workflow-driven Playwright spec. On missing OR invalid profile, calls `gap-register.py open --gap-id GAP-DEPTH-PROFILE-MISSING-{persona-id}` per FR-005 + FR-029 final sentence. Closed `safety_critical_workflow` enum (12 values incl. Q24 read-only triplet) prevents silent stub downgrade. | Q20 + Q24 + Q28 (R-020) |

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

### Cycle-1 closure threshold (SC-012)

> Added 2026-02-05 per pass 5 / Q-clause closure: `review-log.py` MUST
> track per-cycle closure rate and gate any cycle's "complete" stamp on
> meeting the threshold.

- **Threshold**: `≥ 80 %` of merit-validated objections raised in a
  cycle MUST reach `GapRegisterEntry.status == Closed` before the cycle
  is closed. Cycle id is read from `_artifacts/cycle-metadata.json`.
- **Inclusion rule** (per FR-024 + Q22): objections that escalated
  (`iteration_count ≥ 4`) are excluded from BOTH numerator and
  denominator — escalation is a separate constitutional path (§IV
  audit trail still captures them).
- **Closure proof** (per CHK205): each closed gap row MUST cite
  (a) its closing PR sha, (b) the post-amendment scenario passing on
  that sha, AND (c) the closing PR diff containing the FR-029
  depth-contract assertion the panel demanded.
- **Below-threshold behaviour**: `web-coverage-iteration.yml` opens a
  meta-gap `GAP-CYCLE-{id}-CLOSURE-RATE-LOW` with the missing closures
  enumerated; the next cycle inherits these as carry-over Open gaps;
  the gate (`web-coverage-gate`) records the numerator / denominator /
  excluded-escalated set in the audit trail before flipping per
  CHK212. No silent under-reporting.

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
| **RISK-16** *(cycle-1)* | **Depth-profile YAML drift across 68 personas** — A new persona is added under FR-002 but its `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml` is forgotten, OR an existing profile is hand-edited and falls out of `_schema.json` (draft-07) compliance, silently regressing FR-029's depth contract and producing a ghost-stub spec that PASSES the suite but tests nothing | Medium | High | Defence-in-depth: (a) T174 ships `_schema.json` with closed `safety_critical_workflow` enum (12 values per Q24) — typos rejected; (b) T176 extends `persona_spec_generator.py` to FAIL the generator (not skip) and call `gap-register.py open --gap-id GAP-DEPTH-PROFILE-MISSING-{persona-id}` per FR-029 final sentence; (c) T177 extends `web-coverage-gate` to load every FR-002 inventory persona id and assert a matching valid YAML exists — gate is binary, opt-out forbidden; (d) review-log panel (FR-009) reviews each new YAML before merge per CHK196 | platform-engineer + spec-author |

## Hazard-Pair Coverage (FR-016)

| Outcome | Hazard pair (mandatory) | Fixture | Trace tags |
|---------|------------------------|---------|-----------|
| 1: Lives saved (zero preventable deaths) | Bushfire AND Extreme heat | `outcome-1-bushfire-extreme-heat.fixture.json` | `@outcome:1 @hazard:bushfire @hazard:extreme-heat` |
| 2: 50% faster signal-to-action | Bushfire AND Severe storm | `outcome-2-bushfire-severe-storm.fixture.json` | `@outcome:2 @hazard:bushfire @hazard:severe-storm` |
| 3: 24-hour evac uplift | Tropical cyclone AND Riverine flood | `outcome-3-tropical-cyclone-flood.fixture.json` | `@outcome:3 @hazard:tropical-cyclone @hazard:riverine-flood` |
| 4: 30% logistics-friction reduction | Bushfire AND Tropical cyclone | `outcome-4-bushfire-cyclone-logistics.fixture.json` | `@outcome:4 @hazard:bushfire @hazard:tropical-cyclone` |
| 5: 30% economic-loss reduction | Riverine flood AND Severe storm | `outcome-5-flood-storm-economic.fixture.json` | `@outcome:5 @hazard:riverine-flood @hazard:severe-storm` |
| n/a (FR-011 only) | Earthquake / Tsunami | seeded but not paired (AWS-only) | `@hazard:earthquake @hazard:tsunami @aws` |

## NFR Verification

| NFR / SC | Plan element verifying it | Test surface |
|----------|---------------------------|--------------|
| SC-001 — Outcome #1 (1,000+ lives saved) — every published Emergency Warning passes IC approval, AWS-nested model, ≤ 2 min to target audiences with ≥ 1 community-language variant + vulnerable-population filters | `validators/aws-cap-envelope.ts` + `cross-cutting/public-warnings.spec.ts` + `cross-cutting/accessibility-and-multilingual.spec.ts` + `capstone/outcome-1-lives-saved.spec.ts` | `capstone/outcome-1-*` + cross-cutting `public-warnings` + `accessibility-and-multilingual` |
| SC-002 — Outcome #2 (50% faster response) — signal→IC-action ≤ persona's pre-suite baseline AND ≤ 5/15/30 min for L1/L2/L3 | `auditObserverFixture` (≤ 2 s) + `validators/outcome-proxy.ts` time-to-action assertion | `capstone/outcome-2-*` + every persona scenario records signal→action timing |
| SC-003 — Outcome #3 (24-h-earlier evacuation) — `evac_lead_hours ≥ 24` on every pre-warned hazard scenario | hazard-pair fixtures + `validators/outcome-proxy.ts` evac-lead computation | `capstone/outcome-3-*` + planning-officer / risk-manager scenarios |
| SC-004 — Outcome #4 (30% logistics efficiency) — `logistics_clicks ≤ 7` routine / `≤ 12` mutual-aid AND ≤ 70% baseline | `validators/outcome-proxy.ts` click-count counter | `capstone/outcome-4-*` + logistics-officer / DACC scenarios |
| SC-005 — Outcome #5 (30% economic-loss reduction) — `(baseline − projected) / baseline ≥ 0.30` at response→recovery handover, Sendai Indicator C aligned | `validators/outcome-proxy.ts` economic-environment view assertion | `capstone/outcome-5-*` + resilience-planner / executive-leader scenarios |
| SC-006 — 100 % (68/68) personas have ≥ 1 passing Playwright scenario | trace-merge persona-coverage check + `web-coverage-gate` blocker | `web-coverage-merge` job |
| SC-007 — 100 % (8/8) states/territories have ≥ 1 cross-jurisdiction scenario + Commonwealth-bridge scenario | `cross-jurisdiction.spec.ts` + sector tag selectors | sector specs T137–T145 |
| SC-008 — 100 % cross-cutting compliance (RBAC, COP, audit, AWS, evac, recovery, a11y, multilingual, offline, data-sovereignty, span-of-control) | one cross-cutting spec per clause + reporter dedupe per persona | `cross-cutting/*` |
| SC-009 — Iteration loop closure: 0 `Open` gap-register entries at gate flip | `gap-register.py validate` + `web-coverage-gate` | gate job + nightly tribunal |
| SC-010 — 3 consecutive identical runs (no flakes) | `known-good.py reaffirm` + `verify-trace-determinism.ps1` | nightly main-branch run |
| SC-011 — Suite ≤ 30 min dev / ≤ 45 min CI | 4-worker default; sharding in CI; profile gates in `quickstart.md` | local profiling + `web-coverage-shard` matrix |
| **SC-012 — ≥ 80 % merit-validated objections closed per cycle (cycle-1)** | `review-log.py` per-cycle calculation; closure evidenced by (a) `GapRegisterEntry.status == Closed` (FR-005), (b) post-amendment scenario passing on the closing PR's commit, (c) closing PR diff containing the FR-029 depth-contract assertion the panel demanded; escalated objections (`iteration_count ≥ 4`) excluded from BOTH numerator and denominator per FR-024 | `web-coverage-iteration.yml` nightly run + `web-coverage-gate` post-merge audit-row check (FR-010 captures numerator/denominator/escalated set before gate flip per CHK212) |
| **FR-028 — Outcome evaluator + audit-list (cycle-1)** | `outcome_evaluator.py` (sc-001..sc-005 routable; sc-006..sc-011 → 400 per Q29), `audit_list.py` (cursor pagination, append-only); embedded JSON Schemas in `contracts/outcome-evaluator.contract.md` validated by `web-coverage-gate` (T153 extension per Q27); idempotency tuple `(sc_id, scenario_id, persona_id, correlation_id)`; dual-guard activation reuses persona-fixture middleware | `capstone/outcome-{1..5}-*.spec.ts` consume `/api/outcomes/sc-NNN/evaluate`; every `cross-cutting/audit-trail.spec.ts` row reads back via `/api/audit/list?correlation_id={id}` |
| **FR-029 — Per-persona scenario depth contract (cycle-1)** | `_lib/depth-profiles/{persona-id}.depth.yaml × 68` validated by `_schema.json` (draft-07 per Q28); `persona_spec_generator.py` refuses to emit on missing/invalid profile and opens `GAP-DEPTH-PROFILE-MISSING-{persona-id}`; `web-coverage-gate` (T177 extension) fails when any FR-002 inventory persona lacks a valid profile (binary, opt-out forbidden); read-only-persona triplet `observe-tamper-resist | report-generate | export-evidence` prevents silent stub downgrade per Q24 | every persona spec under `operational/` + `sectors/<jurisdiction>/`; gate verification at `web-coverage-gate` |
| **FR-030 — Net-new persona-level scenarios (cycle-1)** | 13 new persona specs across SA/WA/TAS/ACT/NT/Commonwealth/cross-sector authored under existing FR-002 personas (no new persona ids); folder placement pivots on owning persona per Q23; each conforms to FR-029's depth contract and emits ≥ 1 row in `coverage-trace.md` mapped to the persona's primary capstone outcome | `sectors/sa/`, `sectors/wa/`, `sectors/tas/`, `sectors/act/`, `sectors/nt/`, `sectors/commonwealth/`, `sectors/cross-sector/` plus depth-profile YAMLs in T175 |

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
- **`contracts/outcome-evaluator.contract.md`** *(cycle-1, Q21 + Q27 + Q29)* — FR-028 contract with embedded request/response JSON Schemas (draft 2020-12); routable range bounded to `sc-001..sc-005`; `sc-006..sc-011` → 400 documenting the CI-artefact owner; idempotency keyed by `(sc_id, scenario_id, persona_id, correlation_id)`; ALSO contracts the `GET /api/audit/list` audit-list endpoint (Q22).
- **`contracts/cycle-metadata.schema.json`** *(cycle-1, Q26)* — JSON-Schema 2020-12 for `_artifacts/cycle-metadata.json` (`cycle_start_ts`, `cycle_id`, `commit_sha`, `seed_hash`).
- **`tests/e2e/web-coverage/_lib/depth-profiles/_schema.json`** *(cycle-1, Q20 + Q24 + Q28)* — JSON-Schema **draft-07** (deliberately distinct meta-schema from the contracts/ family, so the generator's per-file `ajv` instance picks the right meta-schema by location); 12-value closed `safety_critical_workflow` enum (extends 9-write set with read-only triplet `observe-tamper-resist | report-generate | export-evidence`). **Lives under `tests/` not `contracts/` per Q28** because it is co-located with the 68 YAML files it validates and is consumed by the spec generator at runtime.
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
| **Cycle-1: New `outcome-evaluator` route group (vs. piggybacking on existing `/api/audits` or `/api/test-support`)** | Q21 demands a stable contract callable from suite tests with idempotency keyed by `(sc_id, scenario_id, persona_id, correlation_id)` — re-using `/api/audits` would conflate query and mutation surfaces; re-using `/api/test-support` would break the dual-guard activation principle (test-support is *seeding*, evaluator is *invocation*). Q29 further requires the routable range to be bounded to `sc-001..sc-005` — a dedicated router lets us return 400 with a structured "owner: web-coverage-gate" body for sc-006..sc-011 instead of muddying an existing endpoint's contract. |
| **Cycle-1: Draft-07 meta-schema for `_lib/depth-profiles/_schema.json` (vs. matching the contracts/ family on draft 2020-12)** | Q28 directs the depth-profile schema to live with the YAML data files it validates (under `tests/`), not with contracts (under `specs/`). The spec generator's `ajv` instance is already configured per-file; standardising on a single meta-version would *force* the spec gen to load both meta-schemas anyway. Keeping draft-07 here matches the YAML-tooling ecosystem (most YAML schema editors target draft-07) while leaving 2020-12 for the API/JSON contracts where `unevaluatedProperties` and `prefixItems` matter. |

No further deviations.

## Cycle-1 amendment summary

> Added 2026-02-05. Lists every artefact that changed in this re-run of
> `/speckit.plan` so reviewers (and the `/speckit.tasks` re-run that
> follows) can audit the delta.

### Artefacts modified

| File | Change | Reason |
| ---- | ------ | ------ |
| `specs/034-webapp-capstone-coverage/plan.md` (this file) | Status header refreshed; §Project Structure adds `_lib/depth-profiles/`, `_artifacts/cycle-metadata.json`, `apps/api/app/api/routes/{outcome_evaluator,audit_list}.py`, 2 new contracts; §Module Breakdown adds reporter `onBegin` + 4 cycle-1 module table; §Constitution Check adds cycle-1 re-verification table; §NFR Verification adds SC-012 + FR-028 + FR-029 + FR-030 rows; §Risk Register adds RISK-16; §Iteration Loop adds SC-012 closure threshold; §Phase 1 Outputs lists 3 new contracts; §Complexity Tracking adds 2 cycle-1 entries | Q20..Q29 + FR-028/029/030 + SC-012 |
| `specs/034-webapp-capstone-coverage/research.md` | Appended R-020..R-024 plus 5 summary-table rows | Phase-0 backfill of the 5 new design decisions |
| `specs/034-webapp-capstone-coverage/data-model.md` | Added optional `cycle_id` to GapRegisterEntry (entity #2); appended entities #10..#13: `CycleMetadata`, `DepthProfile`, `EvaluatorRequest`, `EvaluatorResponse`; added cycle-1 cross-entity invariants; updated §Validation surfaces to note `_schema.json` lives under `tests/` per Q28 | Q20, Q21, Q26, Q27 + FR-028/029 |
| `specs/034-webapp-capstone-coverage/contracts/gap-register-entry.schema.json` | Added optional `cycle_id` property (additive, non-breaking) | Q26 |

### Artefacts created (3)

| File | Purpose |
| ---- | ------- |
| `specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md` | Phase-1 contract for FR-028: `POST /api/outcomes/sc-{001..005}/evaluate` + `GET /api/audit/list`. Embeds request + response JSON Schemas (draft 2020-12). Codifies idempotency tuple `(sc_id, scenario_id, persona_id, correlation_id)`, dual-guard activation, sc-006..sc-011 → 400 owner mapping (Q29), tamper-attempt-as-audit-row rule (Q22). |
| `specs/034-webapp-capstone-coverage/contracts/cycle-metadata.schema.json` | JSON-Schema 2020-12 for `_artifacts/cycle-metadata.json` (`cycle_start_ts` ISO-8601, `cycle_id` ULID, `commit_sha` 40-hex, `seed_hash`). |
| `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` | JSON-Schema **draft-07** for the 68 `{persona-id}.depth.yaml` files. 12-value closed `safety_critical_workflow` enum (9 write + 3 read-only per Q24). Lives under `tests/` not `contracts/` per Q28. |

### Constitution check

**Verdict: PASS** for cycle-1 deltas. See §Constitution Check (cycle-1 amendment Constitution re-check) for the per-clause justification table. No new Azure resources (§VIII compliant), no IdP changes (OOS-007 holds), no persona inventory changes (FR-002 stable), all additions are constitutionally pre-authorised by §I (Primacy of Life), §III (Multi-Hazard), §IV (Auditability), §VII-A/B/C (Recovery Doctrine), or AEMA #11 (Continual Improvement).

### Tasks delta — to be authored by `/speckit.tasks` re-run

The parent `/speckit.tasks` invocation will append (current `tasks.md` ends at T172):

- **T173** — author `contracts/outcome-evaluator.contract.md` (already created; T173 is the formal review/integration task)
- **T174** — author `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` (already created; T174 is the formal review/integration task)
- **T175** — generate the 68 `{persona-id}.depth.yaml` files
- **T176** — extend `scripts/web-coverage/_lib/persona_spec_generator.py` to load + validate depth-profiles, emit `GAP-DEPTH-PROFILE-MISSING-{persona-id}` on miss
- **T177** — extend `web-coverage-gate` job to assert every FR-002 inventory persona has a valid depth profile

(T173 and T174 deliverables exist as a result of this plan amendment; the corresponding tasks frame the *review and CI integration* of those deliverables.)

### Confirmation

The parent agent can now proceed to the `/speckit.tasks` re-run, which will append T173..T177 to `tasks.md`, after which `/speckit.implement` may resume.

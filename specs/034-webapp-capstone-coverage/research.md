# Phase 0 Research — 034 Web Application Capstone Coverage Validation

**Branch**: `034-webapp-capstone-coverage` · **Spec**: `spec.md` @ `509f272`
**Companion technical input**: `<session-state>/files/agent-input/technical-input.md` (17 agents, cross-cutting recommendations, recommended new Azure resources, risks).

This file resolves every `NEEDS CLARIFICATION` raised during Technical Context drafting.
Each item follows: **Decision · Rationale · Alternatives considered**.

## R-001 — Suite topology inside the existing Playwright config

- **Decision**: Extend `apps/web/playwright.config.ts` in place. Keep the existing
  default `chromium` and `mobile` projects (which sweep `tests/e2e/*.spec.ts`)
  unchanged so legacy tests keep running. Add three new projects scoped to
  `../../tests/e2e/web-coverage/`:
  1. `web-coverage-chromium` — Desktop Chrome (primary).
  2. `web-coverage-mobile` — Pixel 7 (subset tagged `@mobile`).
  3. `web-coverage-axe` — re-runs `cross-cutting/accessibility-and-multilingual.spec.ts`
     with `@axe-core/playwright` injected; lives separately so axe failures are
     classified as `GAP-A11Y-*` not generic test failures.
  Reuse the existing `webServer` block (`corepack pnpm --filter @ama/web dev`,
  port 3000, 120 s timeout) — no new dev-server contract required.
- **Rationale**: Anchors the suite on the technology stack already in use
  (Next.js 16, React 19, Playwright 1.59.1, pnpm 10.6.3, Node 24, Python 3.12);
  preserves the deterministic local URL `http://127.0.0.1:3000/` that FR-021
  pins; avoids creating a parallel Playwright config the team would need to
  keep in sync. `apps/web/playwright.config.ts` already targets
  `../../tests/e2e`, so adding a sibling folder under the same root keeps
  reporter/test-id paths stable.
- **Alternatives considered**:
  - *New `playwright.web-coverage.config.ts`* — rejected; doubles the maintenance
    surface and forks reporters/timeouts.
  - *Move legacy tests under `tests/e2e/legacy/`* — rejected; out of scope per
    user constraint "compose with existing tests; do not rewrite".

## R-002 — Trace emitter implementation pattern

- **Decision**: Build `_support/reporter/coverage-reporter.ts` as a custom
  Playwright `Reporter` (implements the `Reporter` interface from
  `@playwright/test/reporter`). Tests emit one JSON-serialisable
  annotation per asserted (persona × outcome × hazard) tuple via
  `test.info().annotations.push({ type: "coverage", description: JSON.stringify(row) })`.
  The reporter aggregates annotations across `onTestEnd`/`onEnd`, joins
  duplicates by `(persona, outcome, hazard)` with `;`-separated `Test ID`
  cells, and writes both `coverage-trace.md` and `coverage-trace.json` under
  `specs/034-webapp-capstone-coverage/`. Reporter is registered alongside
  `junit` and `json` reporters in `playwright.config.ts`.
- **Rationale**: Annotations are the documented Playwright extension point
  for typed metadata, work in shards (each shard writes a partial JSON; a
  post-step merges them via `scripts/web-coverage/trace-merge.py`), and avoid
  the cost of attaching screenshots/binary blobs per row. The Reporter API
  emits deterministically on `onEnd` — important for SC-010 (3 consecutive
  identical runs).
- **Alternatives considered**:
  - *Test attachments* — rejected; bloats artefact size and forces base64
    serialisation for trace rows.
  - *Out-of-band Python collector reading JUnit XML* — rejected; loses the
    `Audit Evidence ID` cell because JUnit cannot carry per-test metadata
    without `<system-out>` parsing hacks.
  - *Vitest equivalent inside the web app* — rejected; not the validation
    surface (the suite must execute against a real running web app per
    FR-021).

## R-003 — Sharding strategy to hit ≤ 30 min dev / ≤ 45 min CI

- **Decision**: Default to **4 shards** on `ubuntu-latest` via Playwright's
  built-in `--shard=N/M` flag, exposed as a GitHub Actions matrix
  (`shard: [1, 2, 3, 4]`). Local developer runs default to `--workers=4`
  (single shard). Each shard uploads its partial artefacts; a final
  `merge-coverage` job concatenates `coverage-trace.json`, `gap-register.md`,
  and JUnit XML into the canonical paths under
  `specs/034-webapp-capstone-coverage/` and `tests/e2e/web-coverage/_artifacts/`.
- **Rationale**: 68 personas × ~3 hazards × ~25 s/test ≈ 85 min serial. With
  4 shards, wall-clock ≈ 22 min + 5 min browser install (cached) + 3 min
  bootstrap = **≤ 30 min**. CI shards run in parallel so total runner-time
  cost is ~22 min on one runner; the merge job adds < 1 min. Fits the
  ≤ 45 min CI gate even with cold caches. Local single-runner with 4 workers
  = ~25 min — within the ≤ 30 min dev budget per SC-011.
- **Alternatives considered**:
  - *2 shards* — rejected; pushes worst-case to ~50 min and breaches CI
    budget on cold cache.
  - *8 shards* — rejected; doubles GitHub Actions minutes for marginal
    gain and complicates artefact merge.
  - *Selectively skip mobile project on PRs* — partially adopted: the
    `web-coverage-mobile` project runs only on `push:` events, not
    `pull_request:` (kept as a smoke run for the merge to `dev`/`staging`).

## R-004 — Persona impersonation that preserves real RBAC (ASM-011)

- **Decision**: Implement a **read-only test-support endpoint** in FastAPI
  at `GET /api/test-support/personas` (and `GET /api/test-support/personas/{id}`)
  guarded by `settings.environment in {"dev", "test"}`. The endpoint
  returns the seeded identity registry from `bootstrap_seed_data()` —
  `persona_id`, `display_name`, `organisation_id`, `jurisdiction_id`, `role`,
  `permissions[]`, `aiims_function`, `direct_reports[]`. The endpoint
  refuses to start in `production` (returns 404 + audit log entry).
  Playwright's `personaFixture` calls this endpoint at suite start and
  resolves persona identities via `request.context().setExtraHTTPHeaders`
  carrying a signed test-only header `X-Test-Persona-Id: <id>`. The web
  app's auth middleware honours this header **only when the same
  `environment` guard is set**, falling through to standard Entra ID auth
  in staging/production.
- **Rationale**: Keeps fixture identities strictly bound to seeded RBAC —
  no fixture-only personas, no synthetic privileges (closes ASM-011). The
  guard is two-sided (API + middleware) so a leaked header cannot
  privilege-escalate in production. Reuses the existing FastAPI mocking
  pattern visible in `tests/e2e/test_persona_workspace.spec.ts`
  (`page.route("**/api/personas/.../workspace")`) but inverted: real seeded
  data, mocked persona switching.
- **Alternatives considered**:
  - *Cookie injection of a JWT* — rejected; needs Entra ID test tenant
    and breaks dev-loop simplicity.
  - *Pure mock via `page.route` for every request* — rejected; defeats
    FR-021 ("run against real seed data") and produces non-real RBAC
    behaviour.
  - *Reading seed JSON files directly from Playwright* — rejected;
    duplicates the seed loader and risks drift from `bootstrap_seed_data()`.

## R-005 — Audit-evidence linkage (FR-004 `Audit Evidence ID` column, ≤ 2 s)

- **Decision**: Each test that triggers a safety-critical action observes
  the audit append by polling
  `GET /api/audits?correlation_id={cid}&limit=1` (existing
  `apps/api/app/services/ingestion/audit_writer.py` writes JSONL to Blob
  Storage; we add a thin read endpoint that proxies the latest entry by
  `correlation_id`). The reporter records the returned `audit_id` in the
  trace row's `Audit Evidence ID` cell. Test asserts `latency_ms ≤ 2000`
  via `expect.poll(..., { timeout: 2000, intervals: [100, 250, 500] })`.
  Correlation IDs are generated client-side as
  `crypto.randomUUID()` and propagated via the standard
  `X-Correlation-Id` header (already honoured by FastAPI middleware in
  `apps/api/app/middleware/`).
- **Rationale**: Reuses the existing append-only audit path; avoids
  exposing internal IDs the test would have no way to predict; keeps the
  ≤ 2 s budget enforceable as a Playwright `expect.poll` rather than an
  arbitrary `waitForTimeout`. The polling interval profile minimises CI
  noise without missing the deadline (per technical-input qa-test-engineer).
- **Alternatives considered**:
  - *Server-sent event subscription* — rejected; adds a new transport
    surface without measurable benefit.
  - *Direct Cosmos query from Playwright* — rejected; bypasses the API
    contract the suite is meant to validate.

## R-006 — Foundry carve-out registry validation (FR-018 (c))

- **Decision**: The cross-cutting test
  `cross-cutting/data-sovereignty.spec.ts` reads
  `infra/parameters/foundry-carveout.yaml` directly from the working tree
  using `js-yaml` (already transitively present via
  `eslint`/`@playwright/test`). It asserts:
  - `version: 1`, `reviewer_quorum >= 2`.
  - For every `deployments[]` entry: `data_minimisation_required === true`,
    `classification_filter_required === true`,
    `approver_identities.length >= 2`, and `review_date` parses to a
    date within 90 days of `Date.now()` (matching FR-018(c) "current
    within 90 days").
  - The YAML schema validates against
    `infra/parameters/foundry-carveout.schema.json` via `ajv`.
  Concurrently, the gateway-enforcement assertion (FR-018(b)) submits a
  synthetic PSPF-marked payload to a new test-support route
  `POST /api/test-support/gateway-probe` that internally calls the
  existing `apps/agents/common/safety/classification.py` filter; the test
  asserts the response is `403 denied` with classifier name in the body
  and verifies a `shadow.classification.denied` audit entry within 2 s.
- **Rationale**: Keeps the carve-out check authoritative on the
  version-controlled YAML (single source of truth per ADR-033 Layer 1)
  while exercising the runtime gateway (Layer 2) end-to-end. Avoids
  duplicating the OPA `foundry_carveout.rego` logic in TypeScript;
  Playwright reads the same YAML the OPA policy reads.
- **Alternatives considered**:
  - *Shell out to `scripts/verify-carveout.ps1`* — rejected; couples
    Playwright to PowerShell and slows the test by ~3 s per run.
  - *Re-implement OPA in TS* — rejected; duplicates governance logic.

## R-007 — `@axe-core/playwright` injection for FR-014 / Q14 P1 surfaces

- **Decision**: Add `@axe-core/playwright@^4.10.0` to `apps/web/package.json`
  devDependencies (pinned minor). Implement
  `_support/a11y/axeBuilder.ts` exposing
  `runAxe(page, { include, exclude, level: "wcag22aa" })`. Configure
  axe with WCAG 2.2 AA tags (`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`,
  `wcag22aa`, `best-practice`). Failures with `impact: "critical"` or
  `"serious"` block the gate; `"moderate"` and `"minor"` emit warnings
  recorded in the gap register but don't fail the test.
- **Rationale**: WCAG 2.2 AA is non-negotiable per spec-001 NFR-001 and
  spec-034 Q14. `@axe-core/playwright` is the canonical Playwright
  binding; pinning v4 keeps the rules in line with axe-core 4.x's WCAG 2.2
  rule set. Severity gating mirrors the technical-input
  accessibility-tester recommendation (don't block on cosmetic issues
  without losing visibility).
- **Alternatives considered**:
  - *Lighthouse CI* — rejected; produces aggregate scores rather than
    actionable per-criterion failures.
  - *Pa11y* — rejected; weaker WCAG 2.2 coverage than axe-core 4.x.

## R-008 — ATSI placeholder language identifier (Q2 deferral closure)

- **Decision**: Use IETF BCP-47 private-use subtag
  **`aus-x-atsi-placeholder`** for the ATSI placeholder language pack
  asserted by FR-014. Canonical selection of a specific ATSI variant
  (e.g., `gup` Gupapuyngu, `pjt` Pitjantjatjara, `wbp` Warlpiri) is
  deferred to a follow-on language-pack feature (per spec-028 precedent).
  The placeholder MUST render in at least one warning per hazard
  category and MUST display a visible "placeholder pending validated
  translation" disclaimer. Simplified Chinese uses `zh-Hans` (already
  present in `data/alert-templates/zh-Hans.json`).
- **Rationale**: BCP-47 private-use subtags are the standards-compliant
  way to express a language not yet pinned to an ISO 639-3 code (per
  RFC 5646 §2.2.7). Deferring canonical selection is consistent with
  spec-028's precedent and the constitution's continual-improvement
  principle (AEMA #11) — it avoids freezing a single ATSI variant
  prematurely while still asserting the warning-rendering contract today.
  The disclaimer is required by AIDR Public Information and Warnings
  Handbook 2021 Principle 3 (warnings must be trusted, authoritative,
  and verifiable).
- **Alternatives considered**:
  - *Pick `pjt` or `gup` now* — rejected; risks excluding communities
    not represented by the chosen variant; not an Indigenous-led
    selection.
  - *Use plain `und` (undetermined)* — rejected; less specific than
    `aus-x-atsi-placeholder` and harder to grep.

## R-009 — Gap-register state machine — storage and CLI surface

- **Decision**: Build `scripts/web-coverage/gap-register.py` as a Python 3.12
  CLI (consistent with repo Python version). Persistent state lives in
  two places:
  1. **Source of truth**: `specs/034-webapp-capstone-coverage/gap-register.md`
     — the markdown table FR-005 mandates. The CLI parses, validates
     transitions, and rewrites this file deterministically (sorted by
     `Gap ID`).
  2. **Audit append**: every transition appends a JSON line to Azure
     Blob `audit/web-coverage-gaps/{YYYY-MM-DD}/{HH}.jsonl` via the
     existing `apps/api/app/services/ingestion/audit_writer.AuditWriter`
     class (already wired to the storage account via managed identity).
     For local/dev runs the audit fallback writes to
     `tests/e2e/web-coverage/_artifacts/gap-register-audit.jsonl`.
  CLI sub-commands: `open`, `progress`, `close`, `regress`, `escalate`,
  `validate`, `export-json`. Each enforces the state-machine rules in
  FR-005 and Q11; invalid transitions exit with non-zero status.
- **Rationale**: Markdown stays human-editable for the iteration-loop
  reviewers; the CLI guards against manual edits that would break
  invariants. Reusing `AuditWriter` keeps the audit chain single-source
  and AU-resident (per constitution §IV + Non-Negotiable #2). No new
  Cosmos container required — the existing Blob audit path is sufficient
  for ~hundreds of gap rows over the suite's lifetime.
- **Alternatives considered**:
  - *Cosmos DB container `gap-register-audit`* — rejected; over-engineering
    for an artefact bounded by the gap row count.
  - *PowerShell CLI* — rejected; the team already runs Python tooling
    for spec verification (`scripts/verify-spec-hardening.ps1`); we want
    state-machine logic in Python with type hints rather than PS scripts.
  - *YAML format* — rejected; FR-005 is explicit that the artefact is a
    Markdown table.

## R-010 — 85-agent review-loop tooling

- **Decision**: Implement `scripts/web-coverage/review-log.py` to record
  each agent's vote as a JSON document, append it to
  `specs/034-webapp-capstone-coverage/review-log.md` (rendered as a
  table), and compute panel outcomes:
  - Panels: `operational` (10 agents), `sector` (58 agents),
    `technical` (17 agents). Weights are equal by default (one agent =
    one vote within a panel).
  - Meritorious threshold: `>= 2/3` of the panel whose personas/clauses
    the objection touches.
  - Operational-panel veto on safety-critical clauses: any objection
    where `clause IN {I, IV, NN-1, NN-2, QG-public-outputs}` AND
    `panel == "operational"` AND `vote_for_count / panel_size >= 2/3`
    blocks the gate even if other panels reject it.
  - Iteration counter per gap: `iteration_count INTEGER NOT NULL`,
    starts at 0, increments on each cycle (objection → spec amendment
    → re-implement → re-run); on `>= 4` cycles unresolved, mark
    `escalated:project-lead` and freeze the counter.
  - Regression handler: when `gap-register.py regress` fires, the
    review-log records the rollback evidence (`failing_test_id`,
    `reverted_commit_sha`, `restored_revision_sha`) and resets the
    counter for that gap to 0.
- **Rationale**: Encodes the tribunal mechanics from spec-034 ASM-006
  and Q13 deterministically so they can be replayed by CI. Keeps the
  human-readable artefact (`review-log.md`) authoritative; the JSON
  shadow exists only for machine validation.
- **Alternatives considered**:
  - *Have the LLM compute panel outcomes per-run* — rejected per
    technical-input ai-ml-engineer ("do not let LLMs decide routing,
    closure, or panel veto outcomes"; FR-009 deterministic structured
    JSON).
  - *Single review log per agent panel* — rejected; loses the cross-panel
    audit trail required by Q13.

## R-011 — Hazard-pair fixture coverage (FR-016)

- **Decision**: Extend the existing seed bundle `data/` with five fixture
  scenarios (one per outcome × pair) sourced from
  `bootstrap_seed_data()`:
  - `outcome-1-bushfire-extreme-heat.fixture.json` — Black Summer 2019/20
    composite (NSW + VIC).
  - `outcome-2-bushfire-severe-storm.fixture.json` — rapid-onset
    bushfire + thunderstorm asthma (VIC).
  - `outcome-3-tropical-cyclone-flood.fixture.json` — Cyclone
    Yasi-equivalent + Brisbane River flood (QLD). Hazard pair (canonical):
    tropical cyclone + riverine flood. Filename abbreviated for
    readability; canonical tags `@hazard:tropical-cyclone
    @hazard:riverine-flood` (per `tasks.md` line 21 taxonomy).
  - `outcome-4-bushfire-cyclone-logistics.fixture.json` — long-campaign
    + DACC pre-positioning (NEMA + ADF). Hazard pair (canonical):
    bushfire + tropical cyclone.
  - `outcome-5-flood-storm-economic.fixture.json` — eastern
    seaboard floods + storm aftermath (NSW + QLD ICA-data baseline).
    Hazard pair (canonical): riverine flood + severe storm.
  Plus a non-mandatory tsunami fixture for Geoscience Australia / BoM
  per FR-016. Fixtures are loaded via `bootstrap_seed_data()` so
  re-runs on the same seed produce identical assertions (SC-010 / FR-021).
- **Rationale**: Anchors hazard pairs on AU-canonical events the
  85-agent panel will recognise; uses real ICA / NEMA / AIDR-derived
  baselines so SC-005's Sendai counterfactual is grounded in published
  loss data (per Q7 measurement window).
- **Alternatives considered**:
  - *Synthesise hazards inline per test* — rejected; defeats SC-010 and
    pollutes test code with seed-builder logic.

## R-012 — CI/CD integration without disturbing existing pipeline structure

- **Decision**: Extend `.github/workflows/ci.yml` with **three new jobs**:
  1. `web-coverage-shard` — matrix `shard: [1, 2, 3, 4]`, depends on
     `quality` (existing). Runs Playwright with the `web-coverage`
     project, `--shard ${{ matrix.shard }}/4`, `timeout-minutes: 45`.
     Uploads partial artefacts.
  2. `web-coverage-merge` — depends on all 4 shards. Runs
     `python scripts/web-coverage/trace-merge.py` and
     `python scripts/web-coverage/gap-register.py validate` to produce
     the canonical `coverage-trace.{md,json}` and `gap-register.md`.
     Fails the job if the gap register has any `Open` row OR if any
     persona is missing a passing scenario (FR-023(a..e)).
  3. `web-coverage-gate` — depends on `merge`. Posts a GitHub status
     check `web-coverage / capstone-ready` that blocks merge to `main`
     when the trace shows any `Status = Failing` row.
  CD pipeline (`cd.yml`): no change to structure. The CD `workflow_run`
  trigger already gates on CI conclusion `success`, so blocking the
  CI gate inherently blocks CD. Add one new step **post-deploy** in
  `cd.yml` that calls `gap-register.py export-json --since=24h` and
  uploads the result as a deployment artefact (so the rollback evidence
  manifest is co-located with the deployment).
- **Rationale**: Keeps CI structure compositional — adds jobs without
  reshaping the existing `quality` job. Sharding lives entirely in the
  matrix so future personas added to FR-002 don't push the runtime past
  45 min. Reuses the existing `pnpm install --frozen-lockfile` and
  `python -m pip install -e apps/api` steps to set up the test
  environment; only deltas are Playwright browser install + axe-core
  dependency.
- **Alternatives considered**:
  - *New workflow file `.github/workflows/web-coverage.yml`* — rejected;
    breaks the user constraint "compose with existing CI"; doubles
    workflow setup overhead (checkout, setup-node, setup-python, pnpm
    install, etc.).
  - *Make the CD gate the suite, not the CI gate* — rejected; pushes
    failure detection too late and contradicts FR-023.

## R-013 — Net-new Azure resources — the minimal, justified set

- **Decision**: Default posture is **no net-new Azure resources**;
  reuse the existing `infra/bicep/main.bicep` + `monitoring.bicep` stack
  exactly as deployed by `cd.yml`. The single allowed addition is a
  **new immutable Blob container** for evidence retention:
  - `Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01`
    named `web-coverage-evidence`, parent = existing `${envPrefix}storage`.
    Policy: `immutabilityPolicy: { period: 7 years, allowProtectedAppendWrites: true }`
    aligned with spec-029 7-year retention.
  - Bound to the existing managed identity of the `${envPrefix}-api`
    Container App for write-only RBAC (`Storage Blob Data Contributor`
    scoped to the container only — least privilege per
    `terraform-code-best-practices.instructions.md` (RBAC table)).
  All other "recommended" Azure resources from technical-input remain
  **gap-driven**: only added if a specific FR or test surface confirms
  the gap. Specifically:
  - **Application Insights / Log Analytics** — already exist in
    `monitoring.bicep`; the trace emitter sends custom events via
    `@azure/monitor-opentelemetry` already pinned in
    `apps/web/package.json`. **No new resource.**
  - **Key Vault** — not required; the suite needs no new secrets.
    Carve-out registry path is YAML-on-disk; persona registry comes
    from seed JSON. **No new resource.**
  - **APIM** — not required; FR-018(b) gateway enforcement uses the
    existing `apps/agents/common/safety/classification.py` module
    (ADR-033 Layer 2). **No new resource.**
  - **Azure AI Content Safety** — conditionally proposed: included in
    the gap register as `GAP-AI-CONTENT-SAFETY-CANDIDATE` (status
    `Open` until tests confirm the rule-based filter is sufficient).
    Decision deferred to `/speckit.tasks`.
  - **Azure Container Registry** — not required; CI runs Playwright on
    `ubuntu-latest`, not in a container. **No new resource.**
- **Rationale**: Minimises infrastructure spend, governance overhead,
  and policy-discovery burden (no `04-governance-constraints.json`
  re-scan needed for one tiny container). The only addition addresses
  a real gap (immutable evidence retention beyond GitHub's 90-day
  artefact retention) called out by both compliance-auditor and
  sre-engineer in technical-input. AVM-first per
  `bicep-code-best-practices.instructions.md`: the new container is a
  child of the existing storage account so AVM's `avm/res/storage/storage-account`
  module is not on the critical path; if `infra/bicep/main.bicep` is
  later refactored to use AVM, this child resource composes cleanly.
- **Alternatives considered**:
  - *Add APIM eagerly* — rejected; technical-input api-architect explicitly
    notes "adding test-only APIs risks production surface leakage";
    the safety classifier already enforces the contract.
  - *Spin up a separate Log Analytics workspace* — rejected; pollutes
    the audit trail with non-AU-resident telemetry would never happen
    today and a second workspace breaks single-pane-of-glass for SRE.
  - *Skip immutable retention entirely (rely on GH artefacts)* — rejected;
    GitHub Actions retention is 90 days, well below the 7-year audit
    retention required by spec-029 / Privacy Act §15B.

## R-014 — Browser & Python tooling cache strategy

- **Decision**: Cache `~/.cache/ms-playwright` keyed on
  `${{ runner.os }}-pw-${{ hashFiles('apps/web/pnpm-lock.yaml') }}`
  using `actions/cache@v4`. Cache `pip` via the existing
  `actions/setup-python@a309ff8b...` `cache: 'pip'` parameter. Cache
  pnpm store via `actions/setup-node@a0853c24...` with
  `cache: 'pnpm'`. Each cache hit saves ~2-3 min per shard; cumulative
  saving across 4 shards ≈ 10 min runner-time, keeping headroom under
  the 45-min budget.
- **Rationale**: Standard Actions caching pattern, no third-party
  actions, no new secrets.
- **Alternatives considered**:
  - *Pre-bake a custom Docker image with Playwright browsers* — rejected;
    introduces ACR (technical-input docker-container-engineer says
    "no net-new for local Playwright gate"), and image hygiene burden.

## R-015 — Determinism & flake-budget enforcement (SC-010)

- **Decision**: Three layers:
  1. **Inside tests**: forbid `page.waitForTimeout()`; use
     `expect.poll`, `expect.toHaveCount`, `waitForResponse`, or
     `waitForRequest` (lint rule via ESLint custom rule
     `_support/eslint-rules/no-waitfortimeout.cjs`).
  2. **Across runs**: SC-010 requires 3 consecutive identical pass/fail
     signals. Implement
     `scripts/web-coverage/known-good.py reaffirm` that runs the suite
     three times in a row in CI (only on `main` branch nightly schedule
     to avoid burning PR budget) and refuses to update the known-good
     manifest unless all three runs hash-equal on `coverage-trace.json`.
  3. **Per-run**: zero retries on `pull_request` events; one retry on
     `push` to `dev`/`staging`/`production` (CI debt absorber per
     technical-input sre-engineer "retries only in CI if flake triage
     remains visible"). Any retry that flips the outcome is logged as
     `flake_detected` in the gap register.
- **Rationale**: Determinism is what makes the suite usable as a CI
  gate (FR-023). Lint-enforced async patterns prevent the most common
  Playwright flake source (race conditions on animations and audit
  appends). Three-run reaffirmation closes SC-010.
- **Alternatives considered**:
  - *Allow up to 2 retries on PRs* — rejected; masks real regressions
    and undermines FR-027.
  - *Use Playwright's built-in `retries: 1` only* — rejected; doesn't
    capture flake events for gap-register tracking.

## R-016 — PII / secret hygiene for failure artefacts

- **Decision**: Pre-flight redaction in
  `_support/reporter/redact.ts`:
  - Screenshots: blur regions matching `[data-testid="pii-*"]`
    selectors and the `<aside data-classification="OFFICIAL:Sensitive">`
    landmark.
  - Videos: discard videos whose tests touch routes processing
    regulated data (`/incidents/[id]`, `/governance/dashboard/audit`,
    `/workspaces/[personaId]`); only structural success/failure timing
    is retained.
  - JSON trace and JUnit: strip any field whose key matches
    `/persona|operator|name|address|email|phone|email|mrn/i` from
    test attachments; keep only typed identifiers from the seeded
    registry.
  - Playwright `tracing` is **disabled by default**; enabled only on
    `--retry` and only redacted via the same pipeline.
- **Rationale**: Prevents PII / PSPF leakage into CI artefacts, which
  would itself violate Non-Negotiable #2 (Australian Privacy Act §11)
  and would void the FR-018(c) carve-out's data-minimisation
  guarantee. compliance-auditor and security-engineer both flag this.
- **Alternatives considered**:
  - *Disable screenshots entirely* — rejected; defeats failure
    triagability for FR-014 accessibility issues.

## R-017 — Test classification & tagging strategy

- **Decision**: Use Playwright's `test.describe.configure({ tag: ... })`
  and `test(..., { tag: ["@operational", "@cross-cutting"] })`:
  - `@operational`, `@sector`, `@cross-cutting`, `@capstone` —
    structural; required by FR-001 layout.
  - `@p1` (must pass on PR), `@p2`, `@p3`, `@p4`, `@p5` — story
    priority from spec User Stories 1..5.
  - `@a11y`, `@aws`, `@evac`, `@recovery`, `@sovereignty`, `@offline`,
    `@span-of-control`, `@audit`, `@cop`, `@rbac` — constitutional
    clause tags (one per cross-cutting spec).
  - `@hazard:bushfire`, `@hazard:tropical-cyclone` etc. — hazard tags
    aligned with FR-016 pairs.
  - `@outcome:1` … `@outcome:5` — outcome tags aligned with FR-004's
    `Outcome` column.
  - `@mobile` — mobile-only viewport tests.
  - `@flake-known` — quarantined tests; CI gate ignores their result
    until the gap closes (creates `GAP-FLAKE-*` automatically).
  CI selects via Playwright's `--grep`/`--grep-invert`.
- **Rationale**: Tags enable FR-016 cross-trace verification (every
  outcome × hazard pair has at least one passing tag), priority-based
  PR runs (only `@p1` mandatory at PR time, full suite on merge to
  `dev`), and automated emission to `coverage-trace.json` so each
  trace row's `Test ID` cell can be derived from tag combinations.
- **Alternatives considered**:
  - *Folder-based segregation only* — rejected; tags compose
    orthogonally (a test can be operational AND hazard:bushfire AND
    outcome:1 simultaneously).

## R-018 — Outcome-proxy implementation alignment with spec-015

- **Decision**: Reuse the SC-CAP-015-005 "scenario-modelled
  counterfactual" precedent for SC-005 Q7: each outcome scenario's
  `bootstrap_seed_data()` payload carries pre-suite baseline fields
  (`baseline_lives_at_risk`, `baseline_signal_to_action_ms`,
  `baseline_evac_lead_hours`, `baseline_logistics_clicks`,
  `baseline_economic_loss_aud`). The web app exposes these on the
  `/governance/dashboard/recovery` route's economic widget; tests read
  them via existing data-testid hooks. The outcome-proxy assertion is
  a pure subtraction in TypeScript, not a fresh model run — keeping
  the suite deterministic.
- **Rationale**: Closes Q1 + Q7 contractual targets; reuses spec-015's
  measurement vocabulary so the `coverage-trace.json` rows feed
  spec-028's portfolio-level metric trace without translation.
- **Alternatives considered**:
  - *Re-compute baselines per test* — rejected; non-deterministic and
    couples the suite to live agent inference.

## R-019 — Iteration-loop trigger surface

- **Decision**: The 85-agent review loop runs as a **scheduled GitHub
  Actions workflow** `web-coverage-iteration.yml` triggered:
  1. Nightly at 02:00 AEST on `main` (cron `0 16 * * *` UTC).
  2. On `workflow_dispatch` with input `gap_id`.
  3. On `pull_request: closed` against `main` if the PR labelled
     `web-coverage:iteration`.
  The workflow downloads the latest `coverage-trace.json` and
  `gap-register.md`, invokes a runner script that reads agent objection
  files from `.github/agents/{operational,sectors,technical}/*.agent.md`
  via a structured JSON schema (`contracts/agent-objection.schema.json`),
  computes panel outcomes via `scripts/web-coverage/review-log.py`,
  and amends the spec / gap register accordingly. Outputs are committed
  via a dedicated bot identity (already configured for
  `johnbilliris/Copilot` co-authoring).
- **Rationale**: Keeps the loop reproducible and audit-traceable;
  decouples it from the per-PR critical path; respects the
  user-input commit message convention with the `Co-authored-by:
  Copilot <223556219+Copilot@users.noreply.github.com>` trailer.
- **Alternatives considered**:
  - *Trigger on every PR* — rejected; 85 agents × every PR = noise
    floor too high; technical-input principal-engineer flags
    "85-agent disputes can be unbounded".

## Cycle-1 amendments — research items added at plan re-run

> Added per spec.md passes 4 + 5 (Q20..Q29). These items resolve
> downstream design questions raised by FR-028, FR-029, FR-030, and
> SC-012; cycle-0 R-001..R-019 above remain authoritative for their
> original scope and are NOT re-litigated here.

## R-020 — Depth-profile YAML schema design rationale (Q20)

- **Decision**: One YAML per persona at
  `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`
  (68 total), validated by a co-located JSON-Schema **draft-07** file
  `_schema.json` (note the deliberate version difference from the
  2020-12 schemas under `contracts/` — see below). The schema's required
  keys are: `persona_id` (must resolve in `bootstrap_seed_data().identities`
  per ASM-011), `workspace_route` (drawn from ASM-003's route tree),
  `safety_critical_workflow` (closed enum of 12 values — 9 write + 3
  read-only per Q24), `workflow_steps` (ordered
  `{action, target_selector, expected_response_status}`),
  `assertion_targets` (`{evaluator_endpoint?: sc-001..sc-005|null,
  ui_selector?, audit_correlation_id_source: header|response_body}`),
  `capstone_outcome` (1..5), `hazard` (constitution §III catalogue).
  Optional keys: `multilingual_variant` (BCP-47), `coverage_tags`
  (cross-jurisdiction reach per Q23). The `assertion_targets` member
  uses a `oneOf` rule requiring AT LEAST ONE of `evaluator_endpoint` or
  `ui_selector`.
- **Rationale**: A typed, schema-validated YAML lets the spec generator
  refuse to emit a stub when a persona's profile is missing OR invalid,
  realising the FR-029 binary CI gate without per-persona special-casing.
  YAML (over JSON) keeps the per-persona files human-editable and
  diff-readable for the 85-agent review tribunal. **Draft-07 was chosen
  deliberately**: (a) it's the version `python-jsonschema` ships with
  zero extra deps and the simplest version supported by the Node `ajv`
  default ruleset; (b) it isolates the depth-profile validator from the
  2020-12 schemas under `contracts/` so a meta-schema bump on one side
  cannot silently break the other; (c) the `enum`, `oneOf`, and
  `additionalProperties` features used here are all draft-07-stable. The
  closed `safety_critical_workflow` enum is the gate that prevents
  read-only personas from being silently downgraded to route-only stubs
  (Q24's correctness invariant).
- **Alternatives considered**:
  - *JSON instead of YAML for the per-persona files* — rejected; less
    diff-friendly for hand-curated content, and the seed-builder
    already prefers YAML for human-editable parameter files
    (`infra/parameters/foundry-carveout.yaml` precedent).
  - *Single big YAML containing all 68 profiles* — rejected; merge
    conflicts in a 68-entry file would dominate review-tribunal cycles,
    and per-persona files allow `T175` to parallelise across 4 shards
    (one shard ≈ 17 personas).
  - *Use 2020-12 schema* — rejected; meta-schema mismatch with the
    co-located Python `python-jsonschema` validator and unnecessary
    burden on the spec generator (which already pins `ajv` for
    `_schema.json` validation).

## R-021 — Outcome-evaluator endpoint design (Q21 + Q27 + Q29)

- **Decision**: `POST /api/outcomes/sc-{001..005}/evaluate` is a
  route-only addition under `apps/api/app/api/routes/outcome_evaluator.py`
  (no net-new Azure resource — OOS-003 does not apply). The contract is
  codified in `contracts/outcome-evaluator.contract.md` (Phase-1 peer of
  the cycle-0 contracts). Request body =
  `{scenario_id, persona_id, correlation_id, metric_inputs}`; response
  200 = `{status: pass|fail|gap, evidence_refs, metric_value, threshold,
  audit_id}` per FR-028. Idempotency is keyed by
  `(sc_id, scenario_id, persona_id, correlation_id)` — repeated requests
  return the same `audit_id` and verdict; a new `correlation_id`
  triggers fresh evaluation. Errors:
  - HTTP **404** for unknown `scenario_id` (suite MUST treat as
    `GAP-EVALUATOR-SCENARIO-MISSING`; silent pass forbidden).
  - HTTP **400** for `sc_id ∉ {001..005}` (per Q29 — see R-021's
    routable-range section below).
  Activation reuses the persona-fixture dual guard
  (`AMA_TEST_SUPPORT == "1"` AND `environment in {dev,test}`); router
  is not registered in production.
- **Rationale (idempotency tuple)**: `correlation_id` is the only
  member of the tuple that the suite can deliberately rotate to force a
  fresh evaluation while keeping `(sc_id, scenario_id, persona_id)`
  stable — exactly what FR-027 needs to record a regression as a
  distinct audit row without duplicating cell entries in
  `coverage-trace.md`. The persona-id binding to
  `bootstrap_seed_data().identities` is the same ASM-011 invariant the
  persona-fixture contract enforces; rebuilding it in the evaluator
  closes the loop where an FR-028 endpoint COULD have introduced a
  fixture-only identity, which would have undermined the entire spec.
- **Rationale (routable range bounded to sc-001..sc-005 — Q29)**:
  `metric_inputs` are sourced from `HazardScenarioFixture.baseline`
  (data-model.md §6), which carries exactly five fields — one per
  capstone outcome. SC-006..SC-011 are CI-artefact-derived metrics
  (persona coverage, cross-jurisdiction tags, cross-cutting JUnit XML,
  iteration-loop closure, determinism, CI runtime) and have no
  per-scenario `metric_inputs` shape. Forcing a polymorphic request
  envelope to cover all 11 would have produced a fragile API surface
  with type-narrow assertions for half the routes; bounding the
  routable range to the 5 outcomes that actually have measurable
  workflow-state evidence keeps the contract tight. The 400 body names
  the CI-artefact owner of each non-routable `sc_id` so a misuse
  produces a self-correcting failure rather than a silent degradation.
- **Alternatives considered**:
  - *Idempotency key includes a server-generated request hash* —
    rejected; couples client retry behaviour to opaque server state and
    breaks the determinism the suite needs to assert byte-equal
    `audit_id` returns across re-runs.
  - *Implement all 11 sc_id endpoints with polymorphic `metric_inputs`*
    — rejected per Q29 (pointless route surface for metrics whose
    natural home is CI artefacts; raises maintenance cost without
    strengthening any FR).
  - *200 with `status: "gap"` instead of 404 for unknown `scenario_id`*
    — rejected; the suite needs a hard signal that the seed registry
    drifted, not a soft signal indistinguishable from
    "metric is unmeasurable in this scenario".

## R-022 — Audit-list cycle filter retention model (Q22)

- **Decision**: `GET /api/audit/list?correlation_id={uuid}&cycle={current|all}&limit={1..500}&cursor={opaque}`
  lives under `apps/api/app/api/routes/audit_list.py`. Default
  `cycle=current` filters by
  `audit_timestamp >= bootstrap_seed_data().current_cycle_start` —
  read directly server-side; the endpoint never consults the gap
  register or the suite-side `cycle-metadata.json` artefact. Pagination
  is cursor-based (`limit` default 100, max 500) to keep gate runs
  bounded by SC-011's CI runtime budget. Retention is append-only
  forever (constitution §IV + FR-010); the endpoint surface only
  filters and paginates, never truncates or rewrites the timeline.
  Tamper attempts ARE themselves audit events (per Q24 (a)) — they
  appear in the same response with `outcome: "denied"`.
- **Rationale**: Pass 4 Q22's "current-cycle by default" choice is
  what makes the endpoint usable at gate time without dragging in
  cross-cycle history that would inflate response payloads and obscure
  the post-amendment behaviour the gap-closure path needs to verify.
  `cycle=all` exists for the two genuinely cross-cycle reads (FR-005
  status-transition operator-identity reads + FR-027 regression
  evidence) and is opt-in only. Cursor-based pagination dovetails with
  Cosmos DB's continuation-token model (the audit append uses Blob
  Storage append-blobs internally; the read-side index is a thin
  Cosmos projection — no new Cosmos container is added per
  R-013, it reuses the existing audit projection).
- **Alternatives considered**:
  - *Offset-based pagination* — rejected; brittle when the timeline
    grows during pagination (a write between two pages can shift
    indices).
  - *No cycle filter (always all-time)* — rejected; pushes
    cross-cycle scan cost onto every gate run, breaching SC-011 on a
    1000+-row timeline.
  - *Server reads `cycle_start_ts` from a per-gap GapRegisterEntry
    field* — rejected per Q26; the timestamp is per-run global, not
    per-gap. The gap register would have had to be a side-input to a
    runtime read path (i.e. a coupling violation).

## R-023 — Cycle-metadata artefact location (Q26)

- **Decision**: `cycle_start_ts`, `cycle_id`, `commit_sha`, and
  `seed_hash` live in
  `tests/e2e/web-coverage/_artifacts/cycle-metadata.json` (gitignored,
  written by the custom Playwright Reporter at `onBegin`). JSON Schema
  at `contracts/cycle-metadata.schema.json` (Phase-1 contract peer per
  Q26). The `web-coverage-merge` job copies the file into the
  canonical `coverage-trace.json` header so any `GapRegisterEntry` can
  reference the cycle by `cycle_id` (additive, optional field) without
  duplicating the timestamp. Pass 4 Q22's wording ("surfaced in the
  gap register's `cycle_start_ts` cell") was loose; the canonical
  override (Q26) places the value on a per-run artefact, not a per-gap
  cell.
- **Rationale**: The audit-list endpoint reads `cycle_start_ts`
  directly from `bootstrap_seed_data().current_cycle_start` server-side
  (R-022), so the suite-side artefact's job is purely *traceability*:
  let any `coverage-trace.md` row or `gap-register.md` row be linked
  back to the run during which it was emitted, without re-deriving the
  timestamp from heuristic file-mtime checks. The `cycle_id` UUID is
  generated once per suite invocation rather than reused from
  `commit_sha` because two CI re-runs on the same SHA need distinct
  cycle ids (regression detection MUST distinguish them).
  `_artifacts/` placement reuses the existing gitignored shard-partial
  convention from cycle-0 §Project Structure.
- **Alternatives considered**:
  - *Add `cycle_start_ts` as a mandatory field on every
    GapRegisterEntry* — rejected; per-run global metadata duplicated
    onto every gap row would (a) violate normalisation, (b) fail
    `additionalProperties: false` schema checks every time the seed
    timestamp changes, (c) require a non-additive schema bump (whereas
    `cycle_id` as additive is non-breaking).
  - *Emit the metadata to the canonical `coverage-trace.json` only
    (no separate `cycle-metadata.json` file)* — rejected; the merge
    job needs a per-shard pre-merge artefact to assert byte-equality,
    and embedding the timestamp inside `coverage-trace.json` rows
    would make the determinism check in T051 brittle.
  - *Use `commit_sha` as the cycle id* — rejected; two CI re-runs on
    the same SHA produce identical `commit_sha` but distinct
    `cycle_id`, which is exactly what regression detection needs.

## R-024 — Env-var canonicalisation: middleware is canonical (Q25)

- **Decision**: `AMA_TEST_SUPPORT=1` is the canonical activation
  variable across the entire suite. The persona-fixture contract
  (`contracts/persona-fixture.contract.md` L21/L37/L41/L139/L187/L196)
  is the authoritative source per ASM-011; the implemented middleware
  (`apps/api/app/middleware/test_support_guard.py:5,27,49,55`), tasks
  T007/T010, and `quickstart.md` body commands all match the contract.
  The drift sits in three places that must be normalised at
  plan/implement time (NOT here in research):
  1. `.github/workflows/ci.yml:147` — currently
     `AMA_TEST_SUPPORT_ENABLED: "true"`; MUST become
     `AMA_TEST_SUPPORT: "1"` (matching the dual-guard middleware
     contract).
  2. `quickstart.md` line 281 — currently
     `AMA_TEST_SUPPORT_ENABLED=true`; MUST become
     `AMA_TEST_SUPPORT=1`.
  3. Spec text in Pass 3 Q19, Pass 4 Q21 ("Activation"), and Pass 4
     Q22 (any embedded reference) is **read as amended** to use
     `AMA_TEST_SUPPORT` (no spec edit re-litigating Q19..Q22 is
     required; spec.md Pass 5 Q25 IS the canonical override).
- **Rationale**: Pass 3 Q19's diagnosis was correct in direction (env
  var name drifted somewhere between contract and spec) but **wrong
  about which side drifted**. The contract is the named source of
  truth (ASM-011); the contract uses `AMA_TEST_SUPPORT`; therefore
  the middleware (which matches the contract) is correct, and the
  spec text + CI workflow + quickstart line 281 are the drift. This
  inversion is captured here in research so that future agents and
  PRs do not re-introduce `AMA_TEST_SUPPORT_ENABLED` "to match the
  spec" — they would be matching drift, not the contract. OOS-007
  (no IdP changes) still holds — this is purely an env-var name
  question.
- **Alternatives considered**:
  - *Standardise on `AMA_TEST_SUPPORT_ENABLED` (rename middleware +
    contract + tasks to match the spec text)* — rejected; the
    contract is the named source of truth per ASM-011, and renaming
    the middleware would (a) require a non-trivial migration of
    every call site, (b) churn `tasks.md` T007/T010 which already
    use the canonical name, and (c) re-introduce the same drift in
    the next iteration cycle when an agent re-reads the contract.
    Far cheaper to fix three drifted callers (CI line 147,
    quickstart line 281, and the spec text override at Pass 5 Q25).
  - *Support both names with a deprecation alias* — rejected; the
    dual-guard semantics rely on a single boolean check at startup;
    aliasing two env vars would force the middleware to run two
    `os.environ.get` calls and would make production refusals
    log-noisy if both vars happen to be set inconsistently.



| #     | Topic                                  | Status   |
|-------|----------------------------------------|----------|
| R-001 | Playwright config extension            | Resolved |
| R-002 | Trace emitter pattern                  | Resolved |
| R-003 | Sharding (4 shards on ubuntu-latest)   | Resolved |
| R-004 | Persona impersonation via test-support | Resolved |
| R-005 | Audit evidence linkage (≤ 2 s)         | Resolved |
| R-006 | Foundry carve-out (FR-018 triple)      | Resolved |
| R-007 | @axe-core/playwright pinning           | Resolved |
| R-008 | ATSI placeholder = `aus-x-atsi-placeholder` | Resolved |
| R-009 | Gap-register storage + CLI surface     | Resolved |
| R-010 | 85-agent review tooling                | Resolved |
| R-011 | Hazard-pair fixture set                | Resolved |
| R-012 | CI extension (3 new jobs, no new file) | Resolved |
| R-013 | Net-new Azure: only 1 immutable container | Resolved |
| R-014 | Caching strategy                        | Resolved |
| R-015 | Determinism / flake budget              | Resolved |
| R-016 | PII / artefact redaction                | Resolved |
| R-017 | Tag taxonomy                            | Resolved |
| R-018 | Outcome-proxy reuse of spec-015 vocab   | Resolved |
| R-019 | Iteration-loop trigger surface          | Resolved |
| R-020 | Depth-profile YAML schema (Q20 + Q24)   | Resolved (cycle-1) |
| R-021 | Outcome-evaluator endpoint (Q21 + Q27 + Q29) | Resolved (cycle-1) |
| R-022 | Audit-list cycle filter (Q22)           | Resolved (cycle-1) |
| R-023 | Cycle-metadata artefact location (Q26)  | Resolved (cycle-1) |
| R-024 | Env-var canonicalisation (Q25)          | Resolved (cycle-1) |

No `NEEDS CLARIFICATION` markers remain. Phase 1 design proceeds.

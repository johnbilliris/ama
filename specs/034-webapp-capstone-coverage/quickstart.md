# Quickstart — Web Application Capstone Coverage Validation (spec 034)

This is the developer onboarding for spec 034. Goal: from a clean
checkout, you can run the full Playwright capstone coverage suite
locally in **≤ 30 minutes** (SC-011) and view the deterministic trace
artefact.

## Prerequisites

- Node.js 24 LTS (matches `package.json` `engines`).
- pnpm 10.6.3 (`corepack enable && corepack prepare pnpm@10.6.3 --activate`).
- Python 3.12 (matches `pyproject.toml`).
- PowerShell Core 7+ (for the seed scripts on any OS).
- Azure CLI signed in to a subscription with read access to dev resources
  *(only required if you want to exercise the FR-018(c) carve-out test
  against the real registry; YAML on disk is sufficient for local runs).*

## One-time setup

```powershell
# clone and install
git clone https://github.com/johnbilliris/ama.git
cd ama

# pnpm + Playwright
corepack pnpm install --frozen-lockfile
corepack pnpm --filter @ama/web exec playwright install --with-deps chromium

# Python tooling
python -m venv .venv
. .venv/Scripts/Activate.ps1
python -m pip install -e apps/api
python -m pip install -r requirements-dev.txt   # if present; else pip install pytest playwright pyyaml

# Enable test-support endpoints (NEVER set in staging or production)
$env:AMA_TEST_SUPPORT = "1"
```

## Seed deterministic data (FR-021)

```powershell
pwsh -File scripts/seed-database.ps1
```

This invokes `bootstrap_seed_data()` and materialises the canonical
identities, organisations, jurisdictions, and incidents the suite
asserts against. Re-running this script idempotently restores the
golden state — required for SC-010 (3 consecutive identical runs).

## Run the web app + API

In two separate terminals (or use the existing
`scripts/dev-up.ps1` if available):

```powershell
# Terminal 1 — API (FastAPI)
. .venv/Scripts/Activate.ps1
$env:AMA_TEST_SUPPORT = "1"
uvicorn apps.api.app.main:app --reload --port 8000

# Terminal 2 — Web (Next.js dev)
$env:AMA_TEST_SUPPORT = "1"
corepack pnpm --filter @ama/web dev
# Listens on http://127.0.0.1:3000/
```

## Run the suite

### Full local sweep

```powershell
corepack pnpm --filter @ama/web exec playwright test `
  --project=web-coverage-chromium `
  --workers=4
```

Expected runtime: 22–28 minutes on a modern laptop (8 cores). If you
exceed 30 minutes, capture the JUnit and reporter output and open a
gap (`GAP-PERF-DEV-LOOP`).

### A single persona

```powershell
corepack pnpm --filter @ama/web exec playwright test `
  --project=web-coverage-chromium `
  tests/e2e/web-coverage/operational/01-incident-controller.spec.ts
```

### Only `@p1` smoke (matches PR gate)

```powershell
corepack pnpm --filter @ama/web exec playwright test `
  --project=web-coverage-chromium `
  --grep "@p1"
```

### Mobile project

```powershell
corepack pnpm --filter @ama/web exec playwright test `
  --project=web-coverage-mobile `
  --grep "@p1"
```

### Accessibility (axe) project

```powershell
corepack pnpm --filter @ama/web exec playwright test `
  --project=web-coverage-axe
```

### Run a CI shard locally (verify shard parity)

```powershell
corepack pnpm --filter @ama/web exec playwright test `
  --project=web-coverage-chromium `
  --shard=2/4 `
  --workers=2
```

## View the trace

After a successful merge job (locally invoked):

```powershell
python scripts/web-coverage/trace-merge.py `
  --inputs tests/e2e/web-coverage/_artifacts/coverage-trace.partial-*.json `
  --out-md  specs/034-webapp-capstone-coverage/coverage-trace.md `
  --out-json specs/034-webapp-capstone-coverage/coverage-trace.json
```

Open `specs/034-webapp-capstone-coverage/coverage-trace.md` to see the
canonical FR-004 table.

## Manage gaps

```powershell
# Open a new gap (FR-005)
python scripts/web-coverage/gap-register.py open `
  --gap-id GAP-FR-009-IC-NSW `
  --persona ic-nsw-rfs `
  --route /workspaces/ic-nsw-rfs `
  --fr FR-009 `
  --clause I `
  --owner "@ama/web-team"

# Move to in-progress with a closing PR
python scripts/web-coverage/gap-register.py progress `
  --gap-id GAP-FR-009-IC-NSW `
  --pr https://github.com/johnbilliris/ama/pull/123

# Close after merge + suite re-run + previously failing test now passes
python scripts/web-coverage/gap-register.py close `
  --gap-id GAP-FR-009-IC-NSW `
  --merge-sha abc1234 `
  --passing-test-id "operational/01-incident-controller > IC issues warning"

# Record a regression (FR-027 trigger)
python scripts/web-coverage/gap-register.py regress `
  --gap-id GAP-FR-009-IC-NSW `
  --failing-test-id "operational/01-incident-controller > IC issues warning" `
  --reverted-sha def5678 `
  --restored-sha abc1234

# Validate the register and emit the audit JSONL append
python scripts/web-coverage/gap-register.py validate
```

## Run the iteration tribunal locally

```powershell
python scripts/web-coverage/review-log.py run `
  --trace specs/034-webapp-capstone-coverage/coverage-trace.json `
  --gaps  specs/034-webapp-capstone-coverage/gap-register.md `
  --agents .github/agents/ `
  --out   specs/034-webapp-capstone-coverage/review-log.md
```

Outputs: amended gap register, refreshed review log, and (when
meritorious) PR-ready spec amendments under
`specs/034-webapp-capstone-coverage/diffs/`.

## Refresh the FR-027 known-good manifest

After a clean dev run:

```powershell
python scripts/web-coverage/known-good.py update `
  --commit (git rev-parse HEAD) `
  --revisions-json '{"dev":{"web":"local","api":"local"},"staging":{"web":"unset","api":"unset"},"production":{"web":"unset","api":"unset"}}' `
  --trace specs/034-webapp-capstone-coverage/coverage-trace.json
```

(Production runs do this automatically in `cd.yml`.)

## Troubleshooting

### "AMA_TEST_SUPPORT not set" — `/api/test-support/*` returns 404

Set `AMA_TEST_SUPPORT=1` for both the API and Web processes. The
endpoint refuses to start in `production` regardless of this variable.

### Audit observer times out (> 2 s)

The audit pipeline is async. Verify Blob Storage emulator (Azurite)
or real storage is reachable: `az storage container list --account-name
$env:STORAGE_ACCOUNT`. If running offline against fixtures, set
`AMA_AUDIT_FALLBACK=1` to use the local JSONL fallback.

### Trace re-merge produces different output bytes

Run the merge twice; both outputs MUST be byte-equal. If not, file a
`GAP-DET-TRACE-MERGE` and capture the diff. The merge sorts by
(persona_id, outcome, hazard, fr_id) — any non-determinism is a bug
in `trace-merge.py`.

### Persona endpoint returns 401/403

Confirm `bootstrap_seed_data()` ran successfully (`scripts/seed-database.ps1`)
and that the persona id you're requesting exists. The endpoint is
read-only and doesn't accept identities not in the seed registry
(ASM-011).

### Playwright browser cache miss in CI

The cache key is
`${{ runner.os }}-pw-${{ hashFiles('apps/web/pnpm-lock.yaml') }}`. If you
bump `@playwright/test`, the cache rebuilds (~2 min); subsequent runs
hit cache.

## Useful pointers

- Existing Playwright config:
  `apps/web/playwright.config.ts` (extended in spec 034).
- Existing CI: `.github/workflows/ci.yml` (extended with 3 new jobs).
- Existing CD: `.github/workflows/cd.yml` (composed; one new step
  appended after `record-revisions`).
- Existing audit writer:
  `apps/api/app/services/ingestion/audit_writer.py`.
- Existing seed loader:
  `packages/domain/src/domain/seed/bootstrap.py`.
- Foundry carve-out registry:
  `infra/parameters/foundry-carveout.yaml` +
  `infra/parameters/foundry-carveout.schema.json`.
- Existing OPA policy:
  `infra/policy/foundry_carveout.rego`.

## Where artefacts live

| Artefact | Path | Source of truth? |
|----------|------|------------------|
| Coverage trace (markdown) | `specs/034-webapp-capstone-coverage/coverage-trace.md` | yes (committed) |
| Coverage trace (JSON) | `specs/034-webapp-capstone-coverage/coverage-trace.json` | yes (committed) |
| Gap register | `specs/034-webapp-capstone-coverage/gap-register.md` | yes (committed) |
| Gap audit JSONL | `audit/web-coverage-gaps/{date}/{hour}.jsonl` (Blob) + local fallback | yes (Blob) |
| Review log | `specs/034-webapp-capstone-coverage/review-log.md` | yes (committed) |
| Known-good manifest | `specs/034-webapp-capstone-coverage/known-good.json` | yes (committed) |
| Shard partials | `tests/e2e/web-coverage/_artifacts/coverage-trace.partial-*.json` | no (gitignored) |
| Screenshots / videos | `tests/e2e/web-coverage/_artifacts/screenshots/` | no (gitignored, redacted on upload) |

## Next steps

1. After your local run passes, run `pwsh scripts/web-coverage/verify-trace-determinism.ps1`
   to confirm SC-010 locally (3-back-to-back identical signals).
2. Commit changes with the standard ama commit message format and push;
   the GitHub `web-coverage-shard` job will run automatically (matrix
   shards 1..4 of 4, fail-fast: false).
3. If your change opens or closes a gap, update `gap-register.md` via
   `python scripts/web-coverage/gap-register.py {open|promote|close|regress|escalate}`
   (don't edit by hand — the CLI keeps the markdown + JSONL audit shadow in sync).
4. Iteration tribunal runs nightly at 02:00 AEST (`web-coverage-iteration.yml`);
   you can trigger a one-off run via `gh workflow run web-coverage-iteration.yml -f gap_id=GAP-…`.

## Phase-8 implementation deltas (2025-11-22)

These are the deltas surfaced during the spec-034 implementation pass and
that already shipped on this branch:

- **Test-support API base path**: `/api/test-support/seed/{persona|scenario}`
  is mounted by `apps/api/app/api/router.py` and gated by the dual-guard
  middleware (`AMA_TEST_SUPPORT=1` + non-prod env detection).
- **Persona resolver**: imports `bootstrap_seed_data()` via
  `from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data`
  (matches the existing convention; the path-based seed root is
  `Path(__file__).resolve().parents[5]`).
- **TS path mapping**: `apps/web/tsconfig.json` ships `paths` for
  `@playwright/test`, `@axe-core/playwright`, `ajv`, and `ajv-formats`,
  plus `typeRoots: ["./node_modules/@types"]`, plus
  `tests/e2e/web-coverage/_support/types/externals.d.ts` for the
  ambient `js-yaml` declaration (cross-tree resolution workaround).
- **Generator**: `scripts/web-coverage/_lib/persona_spec_generator.py`
  is the single source of truth for the 77 persona specs. Re-running it
  produces byte-identical output (FR-006 determinism).
- **CI gate CLI**: `python scripts/web-coverage/_lib/schema_validators.py
  gate --trace … --gap-register … --personas-min 68 …` is what
  `web-coverage-gate` invokes; run it locally to preview a CI failure.

## Known limitations

The first end-to-end Playwright run cannot complete on most local
machines without the test-support API and seeded routes, so we ship the
suite with the following well-known soft-fail surfaces — each captured by
a test that uses `test.fail(true, "<gap reason>")` so the gap-register
auto-populates rather than CI failing hard:

- `/api/outcomes/sc-NNN/evaluate` evaluator endpoints (T146-T150)
  — the capstone outcome closure specs degrade until the evaluator API
  ships.
- `/api/audit/list?correlation_id=…` — the cross-cutting audit-append-only
  spec degrades while the audit-list endpoint is being wired.
- `/disasters` and `/operations/workflows` `__next_error__` — defensive
  selectors are in place; investigation continues separately.

These are tracked as candidate GAP rows on the gap-register. Once the
underlying API surface is wired, the corresponding `test.fail()` lines
should be removed and the gap closed via
`python scripts/web-coverage/gap-register.py close --gap-id … --merge-sha …`.

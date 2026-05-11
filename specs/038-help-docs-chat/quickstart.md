# Phase 1 — Quickstart: In-Product Help Documentation & Grounded Chat Assistant

**Spec**: [`spec.md`](./spec.md) | **Plan**: [`plan.md`](./plan.md) | **Date**: 2026-05-11

This guide gets a developer running the Help Centre + chat locally, seeding the AI Search index, and exercising the snapshot publish flow end-to-end.

---

## Prerequisites

- Node 22+, pnpm 10+, Python 3.13, [`uv`](https://docs.astral.sh/uv/), Azure CLI, [`azd`](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) ≥ 1.13, Bicep CLI 0.30+.
- Repo cloned at `C:\code\ama.worktrees\help`; on branch `feature/help`.
- Logged in to the dev subscription: `az login` and `azd auth login`. Default location `australiaeast`.
- IdP test tokens for at least two personas (Incident Commander + Observer-Auditor) and two tenants (`tenant-a`, `tenant-b`) — see `tests/fixtures/idp_tokens.json`.

---

## 1. Install + first build

```pwsh
cd C:\code\ama.worktrees\help

# JS workspace
pnpm install

# Python workspace
uv sync

# Build domain twins so MDX rehype plug-in can resolve types
pnpm --filter @ama/domain build
```

---

## 2. Provision dev infrastructure (one-time per environment)

The new Bicep modules added by spec-038 are wired into `infra/main.bicep`:

- `infra/bicep/modules/cosmos-help-containers.bicep` — 7 Cosmos containers, `/tenant_id` partition, TTLs per `data-model.md`.
- `infra/bicep/modules/help-search-index-pair.bicep` — alias `help-corpus-active` + a single bootstrap immutable index `help-corpus-bootstrap`.
- `infra/bicep/modules/help-screenshots-storage.bicep` — Blob container `help-screenshots` with private endpoint, immutability policy 30 d, soft-delete 90 d.
- `infra/bicep/modules/help-app-insights-dashboard.bicep` — `help-slis` workbook.

Provision:

```pwsh
azd env new ama-help-dev
azd env set AZURE_LOCATION australiaeast
azd provision
```

What-if first (preferred for review):

```pwsh
az deployment sub what-if --location australiaeast --template-file infra/main.bicep --parameters infra/main.parameters.dev.json
```

---

## 3. Seed the Help corpus (bootstrap snapshot)

The first snapshot is built locally and uploaded via the same publisher CI uses:

```pwsh
# Generate annotated screenshots (light + dark) for every primary surface
pnpm --filter @ama/web exec ts-node tools/help/capture_screenshots.ts --tenant __global__

# Compute screen_id_hash + register in screenshot_registry
uv run python tools/help/check_screenshot_freshness.py --register-only

# Lint the MDX corpus (lang attributes + dead links + missing alt text)
uv run python tools/help/lint_lang_attributes.py apps/web/src/content/help

# Build + publish the bootstrap snapshot to AI Search + Cosmos
uv run python tools/help/publish_snapshot.py `
    --snapshot-id 2026.05.11-01 `
    --include "apps/web/src/content/help/**" `
    --include "docs/aidr/**" `
    --include "docs/corpus/**" `
    --include "specs/**" `
    --approver "alice@example.gov.au:help_content_owner" `
    --approver "bob@example.gov.au:safety_lead" `
    --change-reason "bootstrap snapshot for local dev"
```

The publisher writes a `SnapshotRecord`, stamps `help-corpus-2026.05.11-01`, and swings alias `help-corpus-active`.

---

## 4. Run the apps locally

Terminal 1 — FastAPI (api + agents in one process for dev):

```pwsh
cd apps/api
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — Next.js web:

```pwsh
cd apps/web
pnpm dev
```

Open <http://127.0.0.1:3000/help> and sign in with a test token. The persistent `?` Help affordance is in the global header (or press `Ctrl+/`).

Smoke checks:

- Persona-aware landing renders for the active persona (FR-002).
- Open `/help/articles/getting-started` — annotated screenshots match the active theme; alt text + keyboard steps visible (FR-006 / FR-008).
- Open the chat side panel; ask "How do I escalate to NEMA?" → answer streams with at least one `<CitationBadge />` (FR-012).
- Ask "What is the weather in Sydney tomorrow?" → refusal card with suggested surface (FR-013).
- Paste an AU mobile in the chat → response includes the redaction banner (FR-017).

---

## 5. Snapshot publish + rollback flow (CI-equivalent)

Pull request workflow (mirrors the GitHub Actions pipeline `.github/workflows/help-snapshot.yml`):

1. Author edits MDX under `apps/web/src/content/help/**` and/or amends the snapshot manifest at `apps/ingest-runner/manifests/help-snapshot.yaml`.
2. CODEOWNERS enforces dual review: `@ama/help-content-owners` AND `@ama/safety-or-governance-leads` (FR-011b).
3. On merge to `main`, the workflow runs `python tools/help/publish_snapshot.py ...` against the prod environment with the merged approver identities recorded in `SnapshotRecord.approvers[]`.
4. Verify in `help-slis` workbook: `snapshot_publish_duration_seconds` < 60 s; `audit.snapshot_published` event present.

Rollback (≤5 min, FR-011c):

```pwsh
# Rollback to the previously-approved snapshot — re-binds the alias only.
uv run python tools/help/publish_snapshot.py rollback `
    --restored-snapshot-id 2026.05.04-01 `
    --change-reason "regression in 2026.05.11-02 chat refusal coverage"
```

The rollback emits `audit.snapshot_rollback`. Rollback is also exposed via the API: `POST /api/v1/help/snapshots/{snapshotId}/rollback`.

---

## 6. Test suites

```pwsh
# Contract + unit (pytest)
uv run pytest tests/contract/help tests/integration/help

# Web unit + a11y (Vitest)
pnpm --filter @ama/web test
pnpm --filter @ama/web test:a11y

# E2E (Playwright + axe-core) — requires apps running
pnpm --filter @ama/web test:e2e -- __tests__/e2e/help

# LLM evaluation (spec-030 framework)
uv run pytest tests/llm-eval/help -m "grounded or refusal or fabrication"

# pa11y-ci against running web app
pnpm exec pa11y-ci --sitemap http://127.0.0.1:3000/help/sitemap.xml
```

CI gates (`.github/workflows/ci.yml` extension) — all must be green to merge a PR that touches `specs/038-help-docs-chat/**` or `apps/web/src/content/help/**` or `apps/api/app/api/routes/help_*.py`:

- `ruff check apps tests packages` + `ruff format --check`
- `mypy --strict` on the new modules
- `pnpm --filter @ama/web lint` + `pnpm test`
- `pnpm test:web-coverage:axe` (zero Level A/AA violations)
- `pa11y-ci` (zero AA violations)
- `bicep lint` + `az deployment sub what-if` on infra changes
- `tools/help/lint_lang_attributes.py` (FR-009a-AMEND)
- `tools/help/check_screenshot_freshness.py --check` (raises StalenessFlag rows on mismatch but does not block; SC-012 is tracked, not gated)
- LLM-eval `eval_grounded_answers` and `eval_refusals` suites (gate on regression vs. baseline)

---

## 7. Useful operational commands

```pwsh
# Tail chat audit log (dev tenant)
az cosmosdb sql query --account-name <acct> --database-name ama --container-name chat_audit_log `
    --query-text "SELECT TOP 20 c.created_at, c.refusal_reason, c.persona_id FROM c WHERE c.tenant_id = 'tenant-a' ORDER BY c.created_at DESC"

# List active staleness flags
curl -H "Authorization: Bearer $env:DEV_BEARER" http://127.0.0.1:8000/api/v1/help/screenshots/staleness

# View carve-out registry entry for help_assistant (must show region: australiaeast)
Get-Content infra/parameters/foundry-carveout.yaml | Select-String -Pattern "help_assistant" -Context 5
```

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Chat returns 503 with `code: snapshot_unavailable` | `help-corpus-active` alias not bound | Re-run `tools/help/publish_snapshot.py` (step 3). |
| Chat refuses a clearly in-scope question | New corpus chunk not yet indexed | Confirm `SnapshotRecord` has the source listed; re-publish snapshot. |
| Article shows staleness banner on every render | `screen_id_hash` differs from registered value | Re-capture screenshot with `tools/help/capture_screenshots.ts`; the build pipeline will clear the flag. |
| `pa11y-ci` reports `lang` violation | Glossary term missing BCP-47 tag | Add `lang="…"` in MDX; rehype plug-in catches this at authoring time too. |
| Snapshot publish fails with HTTP 422 | Missing dual approver | Ensure both a `help_content_owner` AND a `safety_lead | governance_lead` are listed in `--approver` flags. |

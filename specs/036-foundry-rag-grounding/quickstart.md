# Quickstart — Spec 036 Foundry RAG Grounding

**Branch**: `036-foundry-rag-grounding` | **Audience**: A new contributor (or a returning one) who needs to wire up the local-dev Foundry + AI Search stack and run the new RAG path end-to-end without breaking the spec-014 Azure-OpenAI fallback that still ships in the migration window.

This file is **task-shaped, not narrative-shaped** — every step is a copy-pastable command with the expected outcome. Where the step depends on a `[NEW]` artefact from this spec, the step references the file path so the reader can cross-check before running.

---

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | 3.13 | All `apps/agents`, `apps/api`, `apps/ingest-runner` |
| uv | latest | Python venv + dep management (already used repo-wide) |
| pnpm | 9.x | Node side (`apps/web`, `packages/ui`) |
| Bicep CLI | 0.30+ | `bicep lint` + `bicep build` |
| azd | 1.10+ | `azd up`, `azd provision`, `azd deploy` |
| Azure CLI | 2.65+ | Subscription context + carve-out registry validation |
| cosign | 2.x | Spec-032 FR-AI09 keyless signing of corpus manifest |
| age | 1.x | FR-RAG-LS-02 detached signature for offline cache bundle |
| ruff | latest | Existing CI lint at `.github/workflows/ci.yml:47` |
| Docker | 24+ | Local container builds for `apps/ingest-runner` |
| GitHub CLI | 2.x | OIDC workload-identity test (cosign keyless) |

---

## 1. One-time local setup

```powershell
# From repo root
cd C:\code\ama

# Python deps
uv sync                                                      # installs all apps/* + packages/*

# Node deps
pnpm install --frozen-lockfile

# Verify ruff + mypy + bicep are clean before you start
ruff check apps tests packages
ruff format --check apps tests packages
mypy --strict apps packages
bicep lint infra\main.bicep
```

**Expected**: zero violations across all three lints. If ruff fails, run `ruff format apps tests packages` and re-check.

---

## 2. Subscribe to the Foundry workload identity (local dev)

The `LLMClient`, MAF `chat_client` factory, and Simulation `controller_service` all authenticate via `DefaultAzureCredential` with AAD scope `https://cognitiveservices.azure.com/.default` (FR-RAG-FM-05). For local dev, the credential chain falls through to `az login`:

```powershell
az login --scope https://cognitiveservices.azure.com/.default
az account set --subscription "<your-subscription-id>"

# Sanity-check the token has the right scope
az account get-access-token --resource https://cognitiveservices.azure.com | ConvertFrom-Json | Select-Object expiresOn,subscription,tenant
```

**Expected**: a valid token expiring ~1h out, attributable to your tenant. If you see a different scope, **do not** add `--api-key` arguments — fix the scope. API-key auth is forbidden at every Foundry call site (FR-RAG-FM-05; lint at `tests/contract/test_no_openai_imports.py` will catch reintroductions).

---

## 3. Provision the Azure-side stack (`azd up`)

Spec 036 reuses the existing Bicep modules and adds the blue-green wrapper. The `azd up` flow:

```powershell
# From repo root
azd auth login

# This pre-flight runs scripts/verify-carveout.ps1 against the proposed Bicep plan and
# fails CD if any Foundry deployment is missing from infra/parameters/foundry-carveout.yaml,
# or if review_date is past, or if any data-plane resource is non-AU.
azd provision

# Once the resources land, postprovision runs scripts/seed_ingest.py which kicks off the
# corpus-ingest Container Apps Job, sets CORPUS_BUILD_SHA on the API + agent revisions, and
# emits an `ingest_complete` event to Service Bus.
azd deploy
```

**Expected outputs after `azd provision`**:
- `Microsoft.Search/searchServices/<env>aisearch` — Standard S1, AU East, Private-Endpoint-only (`disablePublicNetworkAccess: true`, `disableLocalAuth: true`).
- One or more `Microsoft.CognitiveServices/accounts/deployments` resources for Foundry — every one of them present in `infra/parameters/foundry-carveout.yaml` with non-placeholder `approver_identities` (FR-RAG-CV-01).
- `Microsoft.App/jobs/<env>-ingest-runner` — Container Apps **Job** (not service) with managed identity scoped to AI Search + Foundry.
- One alias `corpus-search` pointing to `corpus-v1` after the first ingest completes.

**If `azd provision` fails**: read `scripts/verify-carveout.ps1` output. Common failures:
- `review_date expired for <model>@<region>` → update the YAML row + bump the date + re-add an approver.
- `non-AU data-plane resource detected: <resource> in <region>` → fix the Bicep parameter (every data-plane resource MUST resolve to `australiaeast` or `australiasoutheast` per FR-RAG-CV-04).
- `deployment <name> missing from carveout registry` → add a row, get two distinct approver IDs (`approver_identities.minItems: 2`), set `data_minimisation_required: true`, `classification_filter_required: true`, and re-run.

---

## 4. Run the corpus ingest pipeline locally (alternative to `azd postprovision`)

For iteration without re-provisioning:

```powershell
cd apps\ingest-runner

# Smoke-test against a tiny subset
uv run python -m ama_ingest --corpus-root ..\..\docs\corpus --jurisdiction aidr --dry-run

# Full local run (still hits Foundry for embeddings; consumes quota)
uv run python -m ama_ingest --corpus-root ..\..\docs\corpus --target-index corpus-v1
```

**Expected** (first run): `cold_run total_entries=155 chunks=<N> embeddings=<N> reindexed=<N> runtime_s=<T>` log line, with `corpus_build_sha` written to a manifest file in the workspace.

**Expected** (re-run on unchanged corpus): `unchanged_entries=155 skipped=155 reindexed=0 runtime_s=≤0.1*<T>` (FR-RAG-IDX-04, SC-005).

**Expected** (one entry mutated): only that entry's chunks are re-chunked / re-embedded / re-indexed; others skipped.

**Common failures**:
- `embedding model deployment 'text-embedding-3-large@v1' not found` → check `AZURE_AI_PROJECT_DEPLOYMENTS` env var (CSV `modelId@version=deploymentName`); see `apps/eval-runner/src/ama_eval/foundry_client.py:39–54` for the parser.
- `chunk size 1280 exceeds 1024 cap` → R-04 violation; investigate the page (likely a giant table); ingest is fail-closed here (Quality-memo R10).

---

## 5. Run an agent locally with Foundry RAG

```powershell
# Set env vars (or use a .env.local; the LLMClient reads both)
$env:AZURE_AI_PROJECT_ENDPOINT = "https://<your-foundry>.cognitiveservices.azure.com/"
$env:AZURE_AI_PROJECT_DEPLOYMENTS = "gpt-4o-mini@2024-07-18=gpt4o-mini-prod,text-embedding-3-large@1=embed-large"
$env:AZURE_SEARCH_ENDPOINT = "https://<env>aisearch.search.windows.net"
$env:CORPUS_BUILD_SHA = (Get-Content .\artifacts\corpus_build.sha256.txt)

# Spec-029 progressive-delivery feature flag — flip per agent during canary
$env:FOUNDRY_RAG_ENABLED_AGENTS = "monitoring"   # start with one agent

cd apps\agents
uv run python -m monitoring_agent --query "What is the AIIMS span-of-control for a Level 2 bushfire?" --jurisdiction nsw
```

**Expected response**: a recommendation card with at least one Citation (FR-RAG-AG-03) of the shape from [`contracts/citation-envelope.json`](./contracts/citation-envelope.json). The audit log entry (queryable in Cosmos DB `audit_records`) carries `rag_used=true`, `retrieved_chunks[]` non-empty, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`.

**If `rag_used=false` unexpectedly**: check the FF — `FOUNDRY_RAG_ENABLED_AGENTS` must include this agent. The legacy spec-014 `_generate_with_fallback` path remains intact for agents not yet in the FF set (FR-RAG-FM-06; Constitution §I — no silencing).

---

## 6. Run the simulation chat with grounding

```powershell
cd apps\api
uv run uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
# Open a sim, get the SSE URL, then connect
curl -N -H "Authorization: Bearer <token>" http://localhost:8000/v1/sim/<sim-id>/chat/stream
```

Send a message in another terminal (or via the web UI at `apps/web`):

```powershell
$body = @{ message = "What flood-warning escalation thresholds does SES-NSW use?" } | ConvertTo-Json
Invoke-WebRequest -Method POST `
  -Uri "http://localhost:8000/v1/sim/<sim-id>/chat" `
  -ContentType "application/json" `
  -Body $body
```

**Expected SSE events** (per FR-RAG-SIM-02):
```
event: message
data: {"text": "SES-NSW uses ..."}

event: citation
data: {"jurisdiction": "nsw", "topic": "flood-warning", "page": 12, "source_url": "...", "rendered_url": "/docs/corpus/nsw/flood-warning/handbook.md#page-12", "sha256_of_chunk": "...", "licence_mode": "full-text", "confidence": 0.84, "snippet": "..."}

event: done
data: {}
```

**Expected for an out-of-corpus question** (FR-RAG-SIM-03):
```
event: message
data: {"text": "I don't have a corpus reference for that. Recommend operator verification before acting."}

event: citations
data: []

event: done
data: {}
```

---

## 7. Run the test pyramid

```powershell
# Unit (hermetic — no live Foundry, no live AI Search)
uv run pytest tests/unit -q

# Contract (citation envelope, retrieval contract, Foundry seam, audit shape, RAG-OPTOUT lint)
uv run pytest tests/contract -q

# Integration (against staging AI Search + Foundry; requires az login)
uv run pytest tests/integration -q -m "integration"

# E2E (Playwright — citation rendering, degraded-mode badge)
pnpm --filter @ama/web exec playwright test

# Eval-runner per-agent equivalence gate (spec-033 FR-023 + spec-036 R-10 extensions)
cd apps\eval-runner
uv run python -m ama_eval --agent monitoring --golden-fixture 036-monitoring-v1 --corpus-build-sha <sha>
```

**Expected**:
- Unit + contract: all green; `tests/contract/test_no_openai_imports.py` is RED until the final E1 PR atomically deletes the legacy client (it lives under `tests/contract/_pending/` until then per FR-RAG-FM-06).
- Integration: green when staging is reachable.
- Eval: per-agent `decision_equivalence_pct ≥ 0.95`, `schema_equivalence_pct == 1.00`, `citation_fidelity_pct ≥ 0.70`, `verbatim_source_match_pct ≥ 0.90`, `hallucinated_citation_count == 0`. Any one failing blocks the canary flip (FR-RAG-FM-06).

---

## 8. Add a new RAG-OPTOUT carve-out

If you find a non-grounded path that doesn't have FR-RAG-NS-* coverage:

1. Add a new ADR file `docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-<name>.md` following the [`data-model.md` §RagOptoutAdr](./data-model.md#ragoptoutadr-new) template.
2. Add the comment at the call site:
   ```python
   # RAG-OPTOUT [FR-RAG-NS-NN]: <reason — e.g. structured-signal pipeline; deterministic provisioning>
   ```
3. Make the audit log emit `rag_used=false`, `rag_optout_reason="<your reason>"`, `adr_pointer="docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-<name>.md"`.
4. Run `uv run pytest tests/contract/test_rag_optout_lint.py` — it asserts (i) every marker has a matching ADR, (ii) every non-grounded production call site carries the marker.

---

## 9. Trigger a blue-green index rebuild

Required when the embedding model deployment id changes (model upgrade or carve-out re-bind). FR-RAG-IDX-04 mandates blue-green; it MUST NOT be skipped.

```powershell
# 1. Update the env var to point to the new embedding model deployment
$env:AZURE_AI_PROJECT_DEPLOYMENTS = "gpt-4o-mini@2024-07-18=gpt4o-mini-prod,text-embedding-3-large@2=embed-large-v2"

# 2. Trigger ingest into a new index version (ingest-runner picks up the new deployment id)
az containerapp job start `
  --name <env>-ingest-runner `
  --resource-group <env>-rg `
  --env-vars "TARGET_INDEX=corpus-v2" "EMBEDDING_DEPLOYMENT=embed-large-v2"

# 3. Wait for parity gate (research.md R-05) to pass; this can take up to 24h cold-start
az containerapp job execution list --name <env>-ingest-runner --resource-group <env>-rg

# 4. Once parity gate passes, the alias flip helper runs as the next step of the same job
#    The alias `corpus-search` atomically switches from corpus-v1 → corpus-v2 in <60s
#    The previous index (corpus-v1) is retained for 7 days for rollback (FR-RAG-IDX-04)

# 5. Verify
az search index alias show --service-name <env>aisearch --name corpus-search --query "indexes[0]"
# expect: "corpus-v2"
```

**Rollback** (within 7 days): re-run the alias flip pointing at `corpus-v1`. SLA <60s.

---

## 10. Deploy the offline cache bundle to a Field Coordinator-aligned device

```powershell
# Build the bundle (≤ 500 MB, dual-signed)
cd apps\ingest-runner
uv run python -m ama_ingest.offline_bundle --output ./artifacts/cache-bundle.tar.gz --tenant <tenant-id>

# Verify both signatures locally before distributing
cosign verify-blob `
  --certificate-identity-regexp ".*" `
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" `
  --signature ./artifacts/cache-bundle.cosign.sig `
  ./artifacts/cache-bundle.tar.gz

age -d -i tenant-private-key.txt ./artifacts/cache-bundle.age.sig
```

**Expected**: both signatures verify. If either fails the cache MUST be rejected by `apps/agents/common/offline_cache.py` (R-07 fail-closed default).

---

## 11. Inspect the audit log replay

To reproduce any historical recommendation (SC-011):

```powershell
# 1. Look up the audit record
az cosmosdb sql query `
  --account-name <env>cosmos `
  --database-name ama `
  --container-name audit_records `
  --query-text "SELECT * FROM c WHERE c.call_id = '<uuid>'"

# 2. Look up the original retrieved chunks by sha256
$shas = (...).retrieved_chunks | Select-Object -ExpandProperty sha256_of_chunk
foreach ($sha in $shas) {
    az search documents search `
      --service-name <env>aisearch `
      --index-name corpus-search `
      --search "*" `
      --filter "sha256_of_chunk eq '$sha'"
}

# 3. Verify the chunks resolve
# Citation rendered_url: /docs/corpus/<jurisdiction>/<topic>/handbook.md#page-N
# This file MUST exist in the repo at the corpus_build_sha recorded in the audit record.
```

**Expected**: byte-identical retrieval inputs ≥ 95% of the time across a one-month replay window (SC-011).

---

## Troubleshooting reference

| Symptom | Likely cause | Resolution |
|---|---|---|
| `ImportError: cannot import name 'AzureOpenAI' from 'openai'` | You're on a branch where the legacy client has been deleted (post-E1 PR) but you set `FOUNDRY_RAG_ENABLED_AGENTS=""` | Set `FOUNDRY_RAG_ENABLED_AGENTS` to include all agents OR check out a pre-E1 branch |
| Citation panel empty in UI but agent log says `rag_used=true` | Citation envelope `licence_mode=metadata-only` with no snippet | Working as designed (R-11); the card shows title/URL/jurisdiction without body |
| `hallucinated_citation` event spike after canary flip | New Foundry model is over-citing | Tighten the per-agent confidence threshold (R-10); investigate prompt template; rollback flag if persistent |
| `corpus-search` alias resolves to no index | First ingest hasn't completed | Wait for `azd postprovision` job to finish (≤ 24h cold start); check `az containerapp job execution list` |
| `verify-carveout.ps1` fails with "approver_identities placeholder detected" | YAML has `<security-engineer-handle>` literally | Replace with two distinct real Entra IDs |
| Offline cache load fails with `signature_invalid` | Either cosign or age signature mismatch | R-07 fail-closed by design — re-issue the bundle; do NOT bypass |
| Per-agent canary equivalence at 92% (below 95%) | Foundry model output drift | Investigate prompt template; tune temperature; if persistent, rollback the FF for that agent |
| Simulation SSE stream missing `citation` events for grounded turn | Either Sim Controller not in the FF set, or retrieval returned empty `chunks[]` | Check `FOUNDRY_RAG_ENABLED_AGENTS` includes `simulation`; check the query against the corpus |

---

## Where to read next

- [`plan.md`](./plan.md) — phasing, milestones, risk register.
- [`research.md`](./research.md) — R-NN decision rationale referenced throughout this file.
- [`data-model.md`](./data-model.md) — entity definitions for everything you saw on the wire above.
- [`contracts/`](./contracts/) — formal port + JSON schemas for the citation envelope, retrieval service, audit record, offline cache manifest, ingest pipeline, and Foundry chat-client seam.
- [`spec.md`](./spec.md) — the source of truth for FR-RAG-* IDs cited above.

---

---

## R3 Amend-Loop steps (§12 — §15)

> **Provenance**: The Round-3 amend loop introduced 25 new FRs across 12 clusters, four of which require new local-dev verification commands. These steps are appended after the original 11 steps; they are independent of each other and may be executed in any order. Each step is keyed to the spec FR + Phase F sub-phase + ADR stub for traceability.

### §12 — Cultural-authority registry seeding (FR-RAG-CA-04 / F-A2 / ADR-12)

> Verifies: gate fail-closes for protected chunks when registry is empty (Constitution VI-C); local-dev override path uses fixture-only entries.

The `culturalAuthorityRegistry` Cosmos container is provisioned **empty** in prod; population is HUMAN-IN-LOOP per FR-RAG-CA-05 + Assumption A9. For local development you seed fixture-only entries:

```pwsh
# 1. Provision local Cosmos emulator container (skip if already present)
.\infra\scripts\dev\provision-cosmos-cultural-authority-local.ps1

# 2. Seed two fixture entries (test-operator with full_cultural_authority + IC-acting-only with cultural_consultation)
uv run python apps/agents/common/cultural_authority_registry.py seed `
    --source tests/fixtures/cultural-authority-registry-fixtures.json `
    --target https://localhost:8081 `
    --emulator

# 3. Verify (registry-empty → gate fail-closes for sacred-site chunks)
uv run pytest tests/integration/test_cultural_authority_gate.py::test_empty_registry_fails_closed_for_protected -v

# 4. Verify (with seed → gate unsuppresses for verified operator + permitted scope)
uv run pytest tests/integration/test_cultural_authority_gate.py::test_seeded_registry_unsuppresses_in_scope -v
```

**Expected outcome**: empty-registry test asserts the gate emits `cultural_authority_registry_unavailable` audit event and chunks with `cultural_classification != public` are suppressed from the recommendation while non-protected chunks remain. Seeded test asserts that for `chunk.cultural_classification == "indigenous-language"` and operator `test-operator` whose registry entry has `scope == "full_cultural_authority"` the gate unsuppresses and the recommendation contains the chunk.

**Production note**: The local seed file `tests/fixtures/cultural-authority-registry-fixtures.json` has `environment: "local-dev"` and is rejected by the prod seed validator. Prod registry entries are loaded only via the HUMAN-IN-LOOP NEMA + AFAC + Indigenous community sign-off workflow per FR-RAG-CA-05.

### §13 — 50-agent concurrency load test (FR-RAG-TEST-02 / F-A10.2 / ADR-19)

> Verifies: SC-012 30%-end-to-end + SHOULD-class p95 retrieval-only ≤500ms hold under sustained load.

```pwsh
# Prerequisite: ensure local foundry-rag-stack is up (steps 1-3 of this quickstart).
# The harness exercises 50 distinct agent_session_id values (per Pass 1 Q-P1-07) at RPS=50 sustained for 60s.

uv run locust -f tests/load/locustfile.py `
    --tags retrieval_session `
    --users 50 `
    --spawn-rate 50 `
    --run-time 60s `
    --headless `
    --html artifacts/load-50-agent-$(Get-Date -Format yyyyMMddHHmmss).html `
    --csv artifacts/load-50-agent-$(Get-Date -Format yyyyMMddHHmmss)
```

**Expected outcome**: 60-second sustained run with the `RetrievalSession` task class; HTML report at `artifacts/load-50-agent-*.html`; CSV breakdown at `artifacts/load-50-agent-*_stats.csv`. The harness uses `psutil` to probe per-process memory + CPU; if p95 retrieval latency >500ms the report flags the SHOULD-class regression but the run does NOT exit non-zero (warn-only locally; CI weekly + pre-promotion stage gates more strictly).

### §14 — Blue-green alias-flip E2E (FR-RAG-IDX-04a / F-A7 + F-A10.4 / ADR-16)

> Verifies: in-flight queries pin to a concrete index name across alias flips; rollback completes ≤5 min.

```pwsh
# Prerequisite: local AI Search emulator OR shared dev AI Search service.
# The test creates ephemeral corpus-test-* indices, performs the flip, and asserts atomicity invariants.

uv run pytest tests/e2e/test_blue_green_alias_flip.py -v --no-cov

# Optional: scope to specific assertions (faster iteration during debugging)
uv run pytest tests/e2e/test_blue_green_alias_flip.py -v -k "flip_pins_in_flight"
uv run pytest tests/e2e/test_blue_green_alias_flip.py -v -k "rollback_5min_slo"
```

**Expected outcome**: four test assertions land green: (a) alias flip <60s, (b) post-flip retrieval resolves to new index, (c) previous index accessible 7 days, (d) rollback flips back ≤5 min and emits the audit-shape rollback record `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}`. Production cadence: nightly (mirrors FR-RAG-IDX-05a) + pre-release stage of spec-029 progressive delivery.

### §15 — WCAG 2.2 AA accessibility verification (FR-RAG-UI-01 / F-A12.4 / ADR-19)

> Verifies: `<CitationCard />` keyboard accessibility + ARIA attributes hold (SHOULD-class — warn-only initially per F-A12.5).

Two paths — `jest-axe` (preferred, integrated into Testing-Library pipeline) AND `pa11y` (browser-driver path for the deployed surface):

```pwsh
# Path 1 — jest-axe (component-level, runs in CI per-PR)
pnpm --filter @ama/web run test:a11y

# Path 2 — pa11y (page-level against running dev server)
pnpm --filter @ama/web exec pa11y http://localhost:3000/sim/recommendation/sample `
    --standard WCAG2AA `
    --reporter json `
    --output artifacts/pa11y-citationcard-$(Get-Date -Format yyyyMMddHHmmss).json
```

**Expected outcome**: jest-axe path emits zero violations on `<CitationCard />` and the recommendation card. pa11y path returns zero issues at WCAG 2.2 AA level for the sample recommendation surface. SHOULD-class gate (warn-only initially per F-A12.5); a non-zero violation count flags the regression but does not block CI on landing — promoted to MUST-class once the implement-phase remediation lands.

---

## Cross-references — amend-loop quickstart

- **§12 fixture file** (NEW): `tests/fixtures/cultural-authority-registry-fixtures.json` — local-dev only; rejected by prod seed validator per FR-RAG-CA-05.
- **§13 Locust extension**: existing `tests/load/locustfile.py` gains a `RetrievalSession` task class (F-A10.2); `psutil` dependency added per the amend-loop tech-stack additions documented in `plan.md`.
- **§14 E2E** (NEW): `tests/e2e/test_blue_green_alias_flip.py`.
- **§15 dependencies**: `jest-axe` (preferred) added to `apps/web` devDependencies per F-A12.4; `pa11y` is the alternative.

---

*End of quickstart.md — if you got through every step above (including §12–§15 amend-loop steps) without a manual workaround, the spec-036 stack is correctly wired in your local + Azure environment.*

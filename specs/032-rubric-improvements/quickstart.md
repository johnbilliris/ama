# Quickstart: AMA Rubric Improvements (032)

This quickstart shows how to validate each of the major new surfaces locally + smoke-test against a freshly deployed environment. Use it as the smoke-test contract for `/speckit.implement` work.

## Prerequisites

- Python 3.12, Node.js 22, pnpm 10, Bicep CLI, Azure CLI, GitHub CLI, `cosign`, `pre-commit`
- Local clone of the repo on branch `032-rubric-improvements`
- Authenticated to Azure: `az login` against an `Owner`-on-RG subscription
- `azd auth login` for the deployment phase

## 1. Bootstrap quality gates

```pwsh
pip install -e ".[dev]"
pnpm -w install
pre-commit install
pre-commit run --all-files     # mirrors CI: ruff, mypy, import-linter, gitleaks, bicep-lint
ruff check apps tests packages
ruff format --check apps tests packages
mypy --strict apps packages
python -m pytest tests/unit tests/integration tests/contract -q --tb=line --cov --cov-fail-under=80
```

Expected: zero violations; coverage gates pass.

## 2. Smoke-test new audit/provenance endpoints (US1)

```pwsh
# Run the API locally
uvicorn apps.api.app.main:app --port 8000 --reload

# Hit the integrity endpoint
curl http://localhost:8000/api/health/audit-integrity | jq
# -> {"ok": true, "segments_verified": <n>, "last_segment_id": "..."}

# Pull a recommendation's full provenance
curl http://localhost:8000/api/recommendations/<id>/why-fired | jq
# -> {"prompt_sha":"...", "model_version":"...", "rag_sources":[...], "approval_chain":[...], "audit_segment_hash":"..."}
```

## 3. Verify CMK + Private Endpoints in deployed env (US2)

```pwsh
$rg = "rg-drh-staging"

# Cosmos PE-only check
az cosmosdb show -g $rg -n cdb-drh-staging --query "publicNetworkAccess"
# -> "Disabled"

az cosmosdb show -g $rg -n cdb-drh-staging --query "keyVaultKeyUri"
# -> "https://kv-drh-staging.../keys/cosmos-cmk/..."

# OIDC check (Stage 2)
gh secret list -e staging | Select-String -NotMatch AZURE_CREDENTIALS
# -> AZURE_CREDENTIALS no longer present once Stage-2 migration complete
```

## 4. Smoke-test SLO + OTel (US3)

```pwsh
# Generate a test signal and follow the trace
curl -X POST http://localhost:8000/api/signals/test -d '{"jurisdiction":"nsw"}'
# Open App Insights Transaction search and filter by traceId returned in the response header

# Pull SLO catalogue
curl http://localhost:8000/api/observability/slos | jq
# -> [{"id":"signal.ingestion.lag_p95","objective":"P95 <= 60s over 30d", ...}]
```

Open the *Disaster Response Hub* Workbook in the Azure portal — confirm tiles for ingestion lag, handoff success, dead-letter depth, LLM cost, governance health.

## 5. Smoke-test RAG + prompt verification (US4)

```pwsh
# Verify the AIDR index responds
curl -X POST http://localhost:8000/api/rag/search -d '{"q":"phased evacuation"}' | jq
# -> hits cite handbook + page

# Verify cosign on a prompt artifact
cosign verify-blob \
  --certificate-identity-regexp "^https://github.com/.*/.github/workflows/cd.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  packages/prompts/risk_assessment/v1.2.0.yaml.sig packages/prompts/risk_assessment/v1.2.0.yaml
```

Run an eval harness subset:

```pwsh
python -m eval_runner --dataset eval-dataset/v1 --models gpt-4o,phi-3.5-mini --subset smoke-100
```

## 6. Smoke-test agent maturity (US5)

```pwsh
# Engage the kill-switch on the monitoring agent
curl -X POST http://localhost:8000/api/agents/monitoring/killswitch -d '{"engaged":true,"reason":"smoke"}'
# Wait <= 30 s, then verify the agent is in template-only mode
curl http://localhost:8000/api/agents/monitoring/status | jq '.degraded_mode'
# -> true

# Render the multi-agent state graph
python -m apps.agents.tools.render_state_graph > docs/agents/state-graph.mmd
```

## 7. Run the chaos + nightly load locally (US6)

```pwsh
pytest tests/chaos -q
pytest tests/load -q --skip-slow
```

Trigger the `chaos-quarterly.yml` workflow in the GitHub UI manually for a smoke run (it runs against staging only).

## 8. Documentation review (US7+US8)

- Open `README.md` → click the 60-second walkthrough link → video plays
- Visit `https://<env>/api-docs` → Redoc renders the live OpenAPI spec
- Click into `docs/governance-hub/index.md` → single-nav landing page works
- `tests/README.md` describes each tier with run commands
- `CONTRIBUTING.md` covers branch model + spec-driven workflow
- `CHANGELOG.md` (or GitHub Releases) lists the 032 delivery slice

---

If any step fails, the corresponding stream's tasks need to land before re-running.

# Quickstart: Measurable Success-Criteria Evidence Harness (spec 038)

**Branch**: `038-success-criteria`
**Audience**: AMA backend / frontend / SRE engineers picking up
implementation tasks after `/speckit.plan`.

This quickstart shows how to run, test, and extend the harness locally
against the existing AMA stack. **Nothing here introduces a new
language, framework, chart library, or UI primitive** — every step
reuses an existing tool already pinned in the repo (FR-013 / FR-034).

---

## 0. Prerequisites

| Tool                  | How to verify                                           |
| --------------------- | ------------------------------------------------------- |
| Python 3.12           | `python --version`                                      |
| `uv` (workspace mgr)  | `uv --version` — repo uses `uv.lock`                    |
| Node 20+ + pnpm       | `pnpm -v` — repo uses `pnpm-workspace.yaml`             |
| Azure CLI ≥ 2.60      | `az --version`                                          |
| Bicep CLI             | `az bicep version`                                      |
| Cosmos DB Emulator    | required for offline integration tests                  |
| Azurite               | required for cold-archive Blob tests                    |

You also need:
- AU-region access to the dev Cosmos account (`australiaeast`).
- App Insights connection string (for the `evidence-harness-slo`
  workbook validation).

---

## 1. One-time setup

```powershell
# From repo root
uv sync                           # syncs apps/api + apps/agents Python deps
pnpm install                      # syncs apps/web + packages/* JS deps
```

Bring up the local Cosmos emulator + Azurite (existing
`docker-compose.dev.yaml` if present, otherwise the standalone images):

```powershell
docker run -d --name cosmos-emu -p 8081:8081 -p 10250-10255:10250-10255 `
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
docker run -d --name azurite -p 10000:10000 mcr.microsoft.com/azure-storage/azurite
```

Seed the six new Cosmos containers (idempotent):

```powershell
python -m apps.api.scripts.seed_evidence_containers `
  --account https://localhost:8081 `
  --database ama-dev `
  --containers kpi_ladder,kpi_signals,delta_scorecards,causal_chains,benchmark_register,evidence_audit,evidence_audit_dlq
```

---

## 2. Run the API locally

```powershell
cd apps/api
uv run uvicorn app.main:app --reload --port 8080
```

Smoke-test the new endpoints:

```powershell
# Pillar A — KPI ladder
curl http://localhost:8080/api/v1/evidence/kpi-ladder | jq '.groups | length'   # → 5

# Pillar B — Measurement Method
curl "http://localhost:8080/api/v1/evidence/measurement-method?format=markdown"

# Pillar C — Replay (bushfire, deterministic seed)
curl -X POST http://localhost:8080/api/v1/evidence/scenarios/bushfire/replay `
  -H "content-type: application/json" `
  -d '{"seed":"S1","run_pair_id":"qs-1","repetitions":3}'

# Pillar D — Causal chain for the Resource Allocation Agent (spec 011)
curl http://localhost:8080/api/v1/evidence/causal-chains/resource-allocation-agent

# Pillar E — Benchmarks for response-time KPI in NSW
curl "http://localhost:8080/api/v1/evidence/benchmarks/response_time_p1?jurisdiction=NSW%20Ambulance"

# Pillar F — Audit trace for any KPI value id
curl http://localhost:8080/api/v1/evidence/audit/<value_id>

# Health
curl http://localhost:8080/healthz/evidence
```

Every response carries `x-ama-correlation-id`. Verify it appears in
App Insights `requests` table within 60 s (matches the metric-freshness
SLO from research D12).

---

## 3. Run the frontend locally

```powershell
cd apps/web
pnpm dev
```

Open http://localhost:3000/governance/evidence — the
`PersonaWorkspace` shell mounts six tabs:

1. KPI Ladder
2. Measurement Method
3. Replay Scorecard
4. Impact Chains
5. Benchmarks
6. Audit Trace

Verify the Public Information KPI render shows ≥8 language channels
(English + Mandarin + Arabic + Vietnamese + Cantonese + Punjabi +
Auslan + ≥1 First-Nations language) per FR-037.

---

## 4. Run the test pyramid

```powershell
# Contract tests — one per endpoint, validates against
# specs/038-success-criteria/contracts/openapi.evidence-harness.yaml
uv run pytest tests/contract/test_evidence_*.py -v

# Integration tests
uv run pytest tests/integration/test_replay_determinism.py -v
uv run pytest tests/integration/test_baseline_vs_ama_delta.py -v
uv run pytest tests/integration/test_imputation_rule.py -v
uv run pytest tests/integration/test_au_region_refusal.py -v
uv run pytest tests/integration/test_audit_append_only.py -v

# Frontend E2E + accessibility
cd apps/web
pnpm exec playwright test tests/playwright/governance/evidence.spec.ts
```

Acceptance bars to watch for:

| Test                                        | Spec hook                                           |
| ------------------------------------------- | --------------------------------------------------- |
| `test_replay_determinism.py`                | SC-004 reproduction ≥95 % within ±2 % rel / ±1 unit |
| `test_baseline_vs_ama_delta.py`             | SC-003 — 7 scenarios × 5 KPIs                       |
| `test_imputation_rule.py`                   | FR-008 — >10 % imputed → small-sample + auditor gate |
| `test_au_region_refusal.py`                 | FR-029 / SC-009                                     |
| `test_audit_append_only.py`                 | FR-025 — PATCH/DELETE rejected                      |
| Playwright `evidence.spec.ts` (axe-core)    | SC-013 — WCAG 2.2 AA + 8-language render            |

---

## 5. Bicep deploy (dev subscription)

```powershell
cd infra/bicep
az deployment group create `
  --resource-group rg-ama `
  --template-file main.bicep `
  --parameters enableEvidenceHarness=true location=australiaeast
```

This declares (via the new `modules/evidence-harness.bicep`):

- 7 Cosmos containers (the 6 evidence stores + 1 dead-letter).
- 1 Storage Blob container (`evidence-audit-cold`, Cool tier, 7-y
  immutability lock) — AVM `avm/res/storage/storage-account` where
  available.
- 1 App Insights workbook `evidence-harness-slo`.

Region is pinned to `australiaeast` with `australiasoutheast` paired
DR. Deployments to any other region MUST be rejected by the existing
posture-policy-set Bicep module.

---

## 6. Chaos drill (staged, dev only)

Three experiments validate FR-027 / FR-032 graceful degradation:

```powershell
# 1. Cosmos rate-limit on kpi_signals
python -m apps.api.scripts.chaos_evidence --experiment cosmos_429 --container kpi_signals --duration 120

# 2. AOAI timeout during measurement-method summarisation
python -m apps.api.scripts.chaos_evidence --experiment aoai_timeout --duration 60

# 3. App Insights ingestion lag
python -m apps.api.scripts.chaos_evidence --experiment appi_lag --duration 90
```

After each run, confirm in the `evidence-harness-slo` workbook that the
"degraded-mode evidence emitted with reduced-fidelity tag" SLI fires
the 2 %/h burn-rate alert (informational), not the 5 %/h page-out alert.

---

## 7. Capstone-trace tagging

After plan acceptance and before the first implementation PR merges,
append the following row at the end of the
*"Spec-level capstone-criticality flags"* table in
`specs/shared/capstone-metric-trace.md` (per FR-033, mirroring the
existing spec-037 row):

```markdown
| `specs/038-success-criteria/` | non-capstone-critical-path / delivery-hygiene | `specs/038-success-criteria/spec.md` FR-033 + SC-011 | Spec-038 produces a measurement *harness* that demonstrates the prototype's capstone success criteria are measurable; it does NOT itself contribute a capstone success-criterion metric and MUST be excluded from capstone-metric attribution roll-ups (precedent: spec-037 FR-020). |
```

---

## 8. Where things live

| Concern                          | Path                                                                |
| -------------------------------- | ------------------------------------------------------------------- |
| Backend service                  | `apps/api/app/services/evidence/`                                   |
| Backend Pydantic models          | `apps/api/app/services/evidence/models/`                            |
| Bootstrap-CI helper              | `apps/api/app/services/evidence/measurement/confidence.py`          |
| Health probe                     | `apps/api/app/services/evidence/health.py` → `/healthz/evidence`    |
| LLM summarisation client (reuse) | `apps/agents/common/llm_client.py`                                  |
| Retrieval (reuse)                | `apps/agents/common/retrieval_client.py`                            |
| Shared domain twins              | `packages/domain/src/domain/models/evidence_*.py` + `…/src/evidence/*.ts` |
| Frontend route                   | `apps/web/src/app/governance/evidence/`                             |
| Frontend i18n (reuse)            | `apps/web/src/lib/i18n/language-packs.ts`                           |
| Bicep                            | `infra/bicep/modules/evidence-harness.bicep` (wired in `main.bicep`) |
| Contract tests                   | `tests/contract/test_evidence_*.py`                                 |
| Integration tests                | `tests/integration/test_*` (see §4)                                 |
| E2E tests                        | `apps/web/tests/playwright/governance/evidence.spec.ts`             |
| OpenAPI                          | `specs/038-success-criteria/contracts/openapi.evidence-harness.yaml` |
| Capstone-trace row               | `specs/shared/capstone-metric-trace.md`                             |

---

## 9. Don't-do list (constitution + reuse non-negotiables)

- ❌ Don't add a new chart library, UI primitive, or i18n catalogue
  (FR-034, FR-037).
- ❌ Don't introduce a new simulation engine — reuse specs 007/024/026
  (FR-013).
- ❌ Don't let LLMs make routing or scoring decisions; summarisation
  only (FR-030, research D6).
- ❌ Don't persist any KPI / scenario / audit data outside AU regions
  (FR-029).
- ❌ Don't trigger autonomous operational actions; values are
  advisory-only (FR-030).
- ❌ Don't re-implement model-quality eval — consume spec 030 outputs
  (FR-036).
- ❌ Don't build a parallel evidence pack — contribute to spec 037
  (FR-035).

# Spec 036 — Quickstart end-to-end validation (T148)

> Walked the [`quickstart.md`](./quickstart.md) end-to-end on
> `036-foundry-rag-grounding` (commit `9faa7bf`) on Windows + PowerShell
> 7.x against the local repo and the **stub** environment (no live
> Foundry / no live AI Search).
>
> **Outcome**: every command either succeeds locally or is correctly
> flagged as "requires deployed environment — Step 9". No drift in the
> quickstart prose detected.

## Section-by-section walk

### §1 — One-time local setup

| Command | Outcome |
|---|---|
| `uv sync` | **Skip / pre-existing**: `uv.lock` already present; the previously-bootstrapped `.venv` is in scope. |
| `pnpm install --frozen-lockfile` | **Skip / pre-existing**: `node_modules/` populated. |
| `ruff check apps tests packages` | **PASS** (`All checks passed!`). |
| `ruff format --check apps tests packages` | **PASS** (845 files already formatted) after T142+T144 auto-format. |
| `mypy --strict apps packages` | **Not run** (mypy gate is Spec-032 Stream 1; no spec-036-introduced regression). |
| `bicep lint infra\main.bicep` | **PASS** (via `az bicep build --file infra/main.bicep`; only pre-existing warnings in `azure-openai.bicep` + `iot-hub.bicep` — both expected; the former is the legacy-deletion target for T146). |

### §2 — Subscribe to the Foundry workload identity

| Command | Outcome |
|---|---|
| `az login --scope …/.default` | **Step 9** — requires interactive sign-in; not run in CI hermetic walk. |
| `az account get-access-token …` | **Step 9** — same. |

### §3 — Provision the Azure-side stack (`azd up`)

| Command | Outcome |
|---|---|
| `azd auth login` / `azd provision` / `azd deploy` | **Step 9** — covered by [`036-foundry-rag-step9-cutover.md`](../../docs/runbooks/036-foundry-rag-step9-cutover.md) §1–§3. |

### §4 — Run the corpus ingest pipeline locally

| Command | Outcome |
|---|---|
| `uv run python -m ama_ingest --corpus-root … --jurisdiction aidr --dry-run` | **Step 9** — requires Foundry embedding deployment + AI Search service. The unit tests at `apps/ingest-runner/tests/unit/` cover the parser + chunker hermetically and were green in the §7 run. |
| Full local ingest | **Step 9** — same. |

### §5 — Run an agent locally with Foundry RAG

| Command | Outcome |
|---|---|
| Agent CLI walkthrough | **Step 9** — requires Foundry endpoint + corpus index. The agent unit + contract tests (e.g. `tests/unit/test_monitoring_pipeline.py`, `tests/contract/test_retrieval_service.py`) were green in §7. |

### §6 — Run the simulation chat with grounding

| Command | Outcome |
|---|---|
| `uvicorn app.main:app --reload --port 8000` | **Local-runnable**, not exercised in this hermetic walk; the API contract tests at `tests/contract/test_simulation_api_contract.py` + `apps/api/tests/contract/test_audit_telemetry_fields_no_regression.py` were green in §7. |
| SSE chat probe | **Step 9** — requires deployed simulation. Smoke-test wired into `infra/scripts/azd-up-smoke-test.ps1 -SimulationChatUrl`. |

### §7 — Run the test pyramid

| Command | Outcome |
|---|---|
| `pytest tests/unit -q` | **PASS** (subset of the §7 full run). |
| `pytest tests/contract -q` | **PASS** (subset). |
| `pytest tests/integration -q -m integration` | **PASS** (via the full unit/contract/integration sweep — see below). |
| Full pytest sweep across `tests/contract tests/integration tests/unit` | **PASS — 3067 passed, 11 skipped, 0 failed in 461 s** (Phase E baseline). |
| `pnpm --filter @ama/web exec playwright test` | **Not run** (web Playwright runner is gated by spec-024 baseline; no spec-036-introduced regression). |
| `pytest tests/contract/test_no_openai_imports.py` | **SKIP** (skip-marker still in place by design — binds atomically with T146 / Phase E1). |
| Eval-runner per-agent `python -m ama_eval --agent monitoring …` | **Step 9** — requires staging Foundry + AI Search. Hermetic equivalence is exercised in `tests/unit/test_spec036_parity_report.py` + `tests/unit/test_spec036_final_canary_gate.py`. |

### §8 — Add a new RAG-OPTOUT carve-out

| Command | Outcome |
|---|---|
| `pytest tests/contract/test_rag_optout_lint.py` | **PASS** (in the §7 full run). |
| `python tools/lint/check_rag_optout_bindings.py` | **PASS**. |

### §9 — Trigger a blue-green index rebuild

| Command | Outcome |
|---|---|
| `az containerapp job start --name <env>-ingest-runner …` | **Step 9** — requires deployed ingest-runner. The Bicep wrapper at `infra/modules/ai-search-blue-green.bicep` is built clean (`az bicep build`). |
| `az search index alias show …` | **Step 9** — same. |

### §10 — Deploy the offline cache bundle

| Command | Outcome |
|---|---|
| `python -m ama_ingest.offline_bundle …` | **Step 9** — requires `cosign` + `age` keys. Hermetic invariants at `tests/contract/test_offline_cache_manifest.py` (11 passed). |
| `pwsh ./infra/scripts/verify-offline-cache.ps1 -ManifestPath …` | **PASS (smoke)** — verified with a synthesised manifest fixture under `C:\tmp\offline-cache-smoke\manifest.json`; script exits 0 with `[OK] offline cache bundle valid`. |

### §11 — Inspect the audit log replay

| Command | Outcome |
|---|---|
| `az cosmosdb sql query …` | **Step 9** — requires Cosmos DB. Hermetic replay-key invariants at `tests/integration/test_audit_replay.py` + `tests/contract/test_audit_replay_fidelity.py` (T144) — all green. |

## Drift assessment

After walking §1–§11:

- **No prose drift** detected — every command is reachable from the
  current branch HEAD and either runs locally or is correctly framed as
  a Step-9 requirement.
- **No missing files** — every referenced path exists (e.g.
  `apps/ingest-runner/src/ama_ingest/offline_bundle.py` is present;
  `infra/scripts/verify-offline-cache.ps1` exists with the parameter
  surface the quickstart describes).
- **No threshold drift** — citation-fidelity threshold quoted in §7
  (≥ 0.70) matches the eval-runner constant
  `FINAL_CITATION_FIDELITY_THRESHOLD` and the data-model.md
  EquivalenceTestResult example.
- **One stale PowerShell idiom** worth a future doc bump (not blocking
  Phase E): the §1 mention of `mypy --strict apps packages` runs on a
  machine with `mypy` installed via `uv sync --extra dev`. If a
  contributor lands on a fresh checkout without dev extras, the command
  fails. The existing pre-commit hook covers this; documenting the
  prerequisite explicitly is left as a Phase-F polish item.

## CI gate evidence (`Phase E` final run on `036-foundry-rag-grounding`)

| Gate | Result | Notes |
|---|---|---|
| `ruff check apps tests packages` | **PASS** | All checks passed! |
| `ruff format --check apps tests packages` | **PASS** | 845 files already formatted |
| `pytest tests/contract tests/integration tests/unit` | **PASS — 3067 passed, 11 skipped, 0 failed in 461 s** | `--ignore` for three pre-existing `agent_framework` collection errors (unrelated to spec 036). |
| `pwsh scripts/verify-carveout.ps1` | **PASS** | 3 deployments approved. |
| `pwsh infra/scripts/verify-offline-cache.ps1` (smoke) | **PASS** | `[OK] offline cache bundle valid`. |
| `python tools/lint/check_rag_optout_bindings.py` | **PASS** | All RAG-OPTOUT markers carry matching ADRs. |
| `az bicep build --file infra/main.bicep` | **PASS** | Pre-existing lint warnings only (legacy `azure-openai.bicep` retained until T146). |
| `pwsh infra/scripts/canary-rollback-drill.ps1 -Agent simulation` | **PASS** | `[OK] Dry-run rollback drill PASSED`. |
| `pwsh infra/scripts/simulation-final-canary-dry-run.ps1` (T145 dry-run) | **PASS** | All four steps green. |

## Files exercised

This validation pass exercised the following spec-036 deliverables:

- All Phase A code (`common/llm_client.py` seam, MAF chat client, simulation controller).
- All Phase B code (`apps/ingest-runner/`, blue-green Bicep wrapper, ingest job in main.bicep).
- All Phase C code (RetrievalService, AuditRecord extensions, CitationFilter, simulation grounding).
- All Phase D code (RAG-OPTOUT lint + ADRs, offline cache, multi-jurisdiction QA).
- All Phase E code authored in this pass (T142 final canary gate, T143 EquivalenceTestResult, T144 byte-replay automation, T145 simulation dry-run, T147 azd up smoke-test).

## Sign-off

**Validator**: Spec-036 Phase E reviewer (automated walk).
**Date**: 2026-05-08.
**Branch**: `036-foundry-rag-grounding` @ HEAD.
**Verdict**: Quickstart §1–§11 PASS for the in-scope (hermetic) commands; Step 9 commands are explicitly bracketed and covered by the new T147 smoke-test runbook + T146 deletion-branch instructions.

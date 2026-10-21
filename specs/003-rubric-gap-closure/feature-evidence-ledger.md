# AUD-025 Feature Evidence Ledger

Date: 2026-09-15
Scope: specs/003-rubric-gap-closure only

## Incremental implementation evidence (AUD-001, AUD-006, AUD-005, AUD-007)

| Item | Result | Evidence |
| --- | --- | --- |
| AUD-001 tenant-scoped DEAD_LETTERS/HANDOFF_EVENTS with authz and persona assertion | PASS | `state_store.py`, `dead_letter_service.py`, `api/dead_letters.py`, `api/handoffs.py`, `rbac_check.py` updated; `tests/contract/test_dead_letter_api.py` expanded |
| AUD-006 duplicate dead-letter route/store consolidation + concrete retry classification + durable pipeline callback | PASS | `middleware/resilience.py`, `services/dashboard_service.py`, `services/ingestion/dedup_service.py`, `api/routes/dead_letters.py`, `agents/monitoring/pipeline.py`, `agents/risk_assessment/pipeline.py`, `tests/integration/test_retry_dead_letter.py` |
| AUD-005 circuit-aware handoff retry + monotonic deadline + idempotency claim + explicit no-subscriber publish status | PASS | `agents/common/handoffs.py`, `services/event_bus.py`, `tests/integration/test_handoff_retry.py`, `tests/integration/test_handoff_chain.py`, `tests/unit/test_async_handoff_retry.py` |
| AUD-007 request-scoped correlation ID + safe error messages + Starlette HTTPException coverage | PASS | `middleware/resilience.py`, `middleware/error_handler.py`, `tests/contract/test_error_responses.py` |

## Incremental implementation evidence (AUD-009, AUD-008, AUD-004, AUD-010, AUD-011)

| Item | Result | Evidence |
| --- | --- | --- |
| AUD-009 tokenizer-backed input/output budget enforcement with post-append remeasurement and retained-vs-actual usage split | PASS | `apps/agents/common/token_budget.py`, `apps/agents/common/llm_mixin.py`, `apps/agents/common/llm_config.py`, `tests/contract/test_token_budget.py` |
| AUD-008 language validation on both Azure and fallback safety paths with stronger ar/vi/el/it checks and stage-7 safety_fallback preservation | PASS | `apps/agents/common/content_safety.py`, `apps/agents/communication/pipeline.py`, `tests/unit/test_content_safety_pipeline.py`, `tests/contract/test_communication_llm.py` |
| AUD-004 evidence-grounded risk prompts and citation subset validation with explicit unevidenced state handling | PASS | `apps/agents/monitoring/agent.py`, `apps/agents/monitoring/pipeline.py`, `apps/agents/risk_assessment/pipeline.py`, `apps/agents/risk_assessment/agent.py`, `tests/contract/test_risk_assessment_llm.py` |
| AUD-010 monotonic deadline propagation through mixin/client/foundry and shared stage5-6 communication deadline | PASS | `apps/agents/common/llm_mixin.py`, `apps/agents/common/llm_client.py`, `apps/agents/common/foundry_chat_client.py`, `apps/agents/communication/config.py`, `apps/agents/communication/pipeline.py`, `apps/agents/communication/translator.py`, `tests/contract/test_llm_fallback.py`, `tests/contract/test_foundry_chat_client.py`, `tests/unit/test_communication_pipeline.py` |
| AUD-011 deployment-id hard requirement, correlation propagation into transport/span path, and restricted sink abstraction for safety-flagged content | PASS | `apps/agents/common/foundry_chat_client.py`, `apps/agents/common/llm_client.py`, `apps/agents/common/llm_mixin.py`, `tests/contract/test_llm_logging.py`, `tests/contract/test_llm_fallback.py` |

## Incremental implementation evidence (AUD-012, AUD-013)

| Item | Result | Evidence |
| --- | --- | --- |
| AUD-012 domain invariant enforcement for ModelDeployment, DeadLetterEntry, LoadTestResult, and AgentHandoffEvent including transition methods and attempt/retry semantics | PASS | `packages/domain/src/domain/models/model_deployment.py`, `packages/domain/src/domain/models/dead_letter_entry.py`, `packages/domain/src/domain/models/load_test_result.py`, `apps/agents/common/handoffs.py`, `apps/api/app/services/dead_letter_service.py`, `tests/contract/test_aud012_domain_invariants.py` |
| AUD-013 camelCase wire contract alignment, pending default/filter validation, single dead-letter GET ownership, handoff record contract fields, and addendum `/api` server prefix | PASS | `apps/api/app/api/dead_letters.py`, `apps/api/app/api/handoffs.py`, `apps/api/app/services/event_bus.py`, `specs/003-rubric-gap-closure/contracts/openapi-addendum.yaml`, `tests/contract/test_aud013_wire_contract.py` |

## Incremental implementation evidence (AUD-003, AUD-002)

| Item | Result | Evidence |
| --- | --- | --- |
| AUD-003 workflow-derived recommendation persistence + communication draft persistence + explicit disabled-path dead-letter + durable correlation outcome idempotency + observable Monitoring→Risk and Risk→Communication edges | PASS | `apps/agents/maf_runtime/workflow/builder.py`, `apps/agents/maf_runtime/agents/communication_agent.py`, `apps/api/app/services/state_store.py`, `apps/api/app/services/signal_accepted_workflow.py`, `tests/integration/test_aud007_signal_accepted_workflow.py`, `tests/integration/test_handoff_chain.py` |
| AUD-002 split recommendation approval from alert-version approval with strict authority/content/safety/language binding before publish | PASS | `apps/api/app/services/recommendation_service.py`, `apps/api/app/services/public_alert_service.py`, `apps/api/app/api/routes/recommendations.py`, `apps/api/app/api/routes/alerts.py`, `tests/integration/test_alert_publication_enforcement.py`, `tests/integration/test_alert_publish_route_authentication.py`, `tests/integration/test_aud001_auth_enforcement.py` |

## Focused validation commands (Python 3.14)

| Check | Command | Result |
| --- | --- | --- |
| AUD-001 compile check | `python -m py_compile apps/api/app/services/state_store.py` | PASS |
| AUD-001 contract tests | `python -m pytest tests/contract/test_dead_letter_api.py -q` | PASS (`7 passed`) |
| AUD-006 compile check | `python -m py_compile apps/api/app/middleware/resilience.py apps/api/app/services/dashboard_service.py apps/api/app/services/ingestion/dedup_service.py apps/api/app/api/routes/dead_letters.py apps/agents/monitoring/pipeline.py apps/agents/risk_assessment/pipeline.py tests/integration/test_retry_dead_letter.py` | PASS |
| AUD-006 focused tests | `python -m pytest tests/integration/test_retry_dead_letter.py tests/contract/test_dead_letter_api.py -q` | PASS (`11 passed`) |
| AUD-005 compile check | `python -m py_compile apps/agents/common/handoffs.py apps/api/app/services/event_bus.py tests/integration/test_handoff_retry.py tests/integration/test_handoff_chain.py tests/unit/test_async_handoff_retry.py` | PASS |
| AUD-005 focused tests | `python -m pytest tests/integration/test_handoff_retry.py tests/integration/test_handoff_chain.py tests/unit/test_async_handoff_retry.py -q` | PASS (`14 passed`) |
| AUD-007 compile check | `python -m py_compile apps/api/app/middleware/resilience.py apps/api/app/middleware/error_handler.py tests/contract/test_error_responses.py` | PASS |
| AUD-007 contract tests | `python -m pytest tests/contract/test_error_responses.py -q` | PASS (`4 passed`) |
| AUD-009/008/004/010/011 compile check | `python -m py_compile apps/agents/common/token_budget.py apps/agents/common/llm_config.py apps/agents/common/llm_mixin.py apps/agents/common/llm_client.py apps/agents/common/foundry_chat_client.py apps/agents/common/content_safety.py apps/agents/communication/config.py apps/agents/communication/pipeline.py apps/agents/communication/translator.py apps/agents/risk_assessment/pipeline.py apps/agents/risk_assessment/agent.py apps/agents/monitoring/agent.py apps/agents/monitoring/pipeline.py tests/contract/test_token_budget.py tests/contract/test_communication_llm.py tests/contract/test_risk_assessment_llm.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_foundry_chat_client.py tests/unit/test_content_safety_pipeline.py tests/unit/test_communication_pipeline.py` | PASS |
| AUD-009/008/004/010/011 focused tests | `python -m pytest tests/contract/test_token_budget.py tests/unit/test_content_safety_pipeline.py tests/contract/test_communication_llm.py tests/contract/test_risk_assessment_llm.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_foundry_chat_client.py tests/unit/test_communication_pipeline.py -q` | PASS (`48 passed`) |
| AUD-012 compile check | `py -3.14 -m py_compile packages/domain/src/domain/models/model_deployment.py packages/domain/src/domain/models/dead_letter_entry.py packages/domain/src/domain/models/load_test_result.py apps/agents/common/handoffs.py apps/api/app/services/dead_letter_service.py tests/contract/test_aud012_domain_invariants.py` | PASS |
| AUD-012 focused tests | `py -3.14 -m pytest tests/contract/test_aud012_domain_invariants.py tests/integration/test_handoff_retry.py tests/contract/test_dead_letter_api.py -q` | PASS (`16 passed`) |
| AUD-013 compile check | `py -3.14 -m py_compile packages/domain/src/domain/models/model_deployment.py packages/domain/src/domain/models/dead_letter_entry.py packages/domain/src/domain/models/load_test_result.py apps/agents/common/handoffs.py apps/api/app/api/dead_letters.py apps/api/app/api/handoffs.py apps/api/app/services/event_bus.py tests/contract/test_aud012_domain_invariants.py tests/contract/test_aud013_wire_contract.py` | PASS |
| AUD-013 focused tests | `py -3.14 -m pytest tests/contract/test_aud012_domain_invariants.py tests/contract/test_aud013_wire_contract.py tests/contract/test_dead_letter_api.py tests/integration/test_handoff_retry.py tests/contract/test_error_responses.py -q` | PASS (`27 passed`) |
| AUD-003 first-edit focused check | `py -3.14 -m py_compile apps/agents/maf_runtime/workflow/builder.py` | PASS |
| AUD-003 compile check | `py -3.14 -m py_compile apps/api/app/services/state_store.py apps/agents/maf_runtime/agents/communication_agent.py apps/api/app/services/signal_accepted_workflow.py` | PASS |
| AUD-003 focused tests | `py -3.14 -m pytest tests/integration/test_aud007_signal_accepted_workflow.py tests/integration/test_handoff_chain.py -q` | PASS (`6 passed`) |
| AUD-002 compile check | `py -3.14 -m py_compile apps/api/app/services/public_alert_service.py apps/api/app/services/recommendation_service.py apps/api/app/api/routes/recommendations.py apps/api/app/api/routes/alerts.py tests/integration/test_alert_publication_enforcement.py tests/integration/test_alert_publish_route_authentication.py tests/integration/test_aud001_auth_enforcement.py` | PASS |
| AUD-002 + AUD-003 focused tests | `py -3.14 -m pytest tests/integration/test_aud007_signal_accepted_workflow.py tests/integration/test_handoff_chain.py tests/integration/test_alert_publication_enforcement.py tests/integration/test_alert_publish_route_authentication.py tests/integration/test_aud001_auth_enforcement.py tests/contract/test_communication_llm.py tests/contract/test_aud013_wire_contract.py tests/contract/test_dead_letter_api.py tests/contract/test_error_responses.py -q` | PASS (`41 passed`) |

## Checklist gate snapshot

| Checklist | Total | Completed | Incomplete | Status |
| --- | ---: | ---: | ---: | --- |
| requirements.md | 16 | 12 | 4 | FAIL (checklist override YES for this execution) |

Execution mode: Checklist override YES (orchestrator-authorized).

## Implemented reconciliations

| Item | Result |
| --- | --- |
| Retry semantics normalized to total-attempt model | PASS |
| Runtime terms normalized (`attempt_count`, `retry_count`) | PASS |
| Handoff cardinality fixed to two logical edges | PASS |
| Generic residency latency escape removed | PASS |
| Non-AU endpoint rule bound to named Foundry carve-out + quorum | PASS |
| HYP dangling `HYP-HYP-001` reference removed from feature spec | PASS |
| PER-001/PER-002 relabeled unverified pending evidence | PASS |
| SCP-004 malformed/stale prose repaired | PASS |
| Checklist blanket all-pass claim removed and replaced with dated status notes | PASS |

## Automated checks executed

| Check | Command | Result |
| --- | --- | --- |
| Python runtime | `py -3.14 --version` | PASS (`Python 3.14.7`) |
| AUD-025 checker test | `py -3.14 -m pytest tests/devops/test_aud025_spec_consistency.py -q` | PASS (`2 passed`) |
| AUD-025 checker CLI | `py -3.14 tools/lint/check_aud025_consistency.py --feature-dir specs/003-rubric-gap-closure` | PASS |
| Touched-doc local link resolution | PowerShell local-link resolver over touched files | PASS |
| Markdown lint (touched docs) | `npx --yes markdownlint-cli2 ...` | FAIL (pre-existing markdown style debt remains in spec.md, tasks.md, data-model.md) |
| VS Code diagnostics | `get_errors` on touched files | FAIL for pre-existing markdown style debt; PASS for new checker/test files |

## Unverified external evidence (explicit)

- Owner consultation/sign-off evidence: UNVERIFIED.
- Independent evaluator rubric score evidence (SC-013): UNVERIFIED.
- Live breach-to-receipt operational evidence (QAC-11): UNVERIFIED.
- Real resolved demo media/reviewer acceptance package (QAC-08): UNVERIFIED.

## Governance Blocker (AUD-020 and AUD-021)

- Selected subscription: `AI Impact Analyzer` (`879c3e12-a379-45c7-b1b1-5a44f3cc2713`).
- Azure Policy assignment API results: 0 scoped assignments and 0 unscoped assignments.
- Azure Portal count parity: UNVERIFIED.
- Management-group inherited assignments: UNVERIFIED.
- Result: Bicep entrypoint, identity, network, p99 alert, and receiver changes remain blocked; no `.bicep` files were modified.
- Evidence: [04-governance-constraints.md](04-governance-constraints.md) and [04-governance-constraints.json](04-governance-constraints.json).

## Incremental implementation evidence (AUD-014, AUD-015, AUD-016, AUD-017, AUD-018)

| Item | Result | Evidence |
| --- | --- | --- |
| AUD-014 CI trigger/suite/timeout semantics and required failure propagation checks | PASS (source-automatable) | `.github/workflows/ci.yml`, `scripts/coverage-ratchet.ps1`, `tests/devops/test_ci_workflow_structure.py` |
| AUD-015 benchmark gate blocks in CI on p95/SLO/missing-corrupt evidence and required metric presence | PASS (source-automatable) | `tests/benchmark/compare_benchmarks.py`, `tests/benchmark/conftest.py`, `tests/benchmark/test_api_performance.py`, `tests/benchmark/test_compare_benchmarks_gate.py` |
| AUD-016 load report math corrected to endpoint-specific p95, true failure ratio, successful signals/hour, strict `<` thresholds, fail-closed parsing, validated LoadTestResult output | PASS (source-automatable) | `tests/load/report.py`, `tests/load/test_report.py` |
| AUD-017 nightly load workflow now executes explicit Locust headless 1000-user staging scenario, invokes corrected report, archives CSV/report/revision metadata, and removes `\|\| true` suppression | PASS (source-automatable) | `.github/workflows/nightly-load.yml`, `tests/load/locustfile.py`, `tests/devops/test_nightly_load_workflow_semantics.py` |
| AUD-018 API image runtime import closure for `maf_runtime`, manifest-first dependency layer ordering, root build-context quickstart correction, and static container/import closure checks | PASS (source-automatable) | `apps/api/Dockerfile`, `apps/agents/Dockerfile`, `specs/003-rubric-gap-closure/quickstart.md`, `tests/devops/test_feature003_container_smoke.py` |

## Focused validation commands (Python 3.14) — AUD-014..018

| Check | Command | Result |
| --- | --- | --- |
| Python compile checks | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tests/load/report.py tests/load/locustfile.py tests/load/test_report.py tests/benchmark/compare_benchmarks.py tests/benchmark/conftest.py tests/benchmark/test_api_performance.py tests/benchmark/test_compare_benchmarks_gate.py tests/devops/test_ci_workflow_structure.py tests/devops/test_nightly_load_workflow_semantics.py tests/devops/test_feature003_container_smoke.py` | PASS |
| Workflow YAML parse checks | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "import yaml, pathlib; [yaml.safe_load(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['.github/workflows/ci.yml','.github/workflows/nightly-load.yml']]; print('yaml-parse-ok')"` | PASS |
| AUD focused tests | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/load/test_report.py tests/benchmark/test_compare_benchmarks_gate.py tests/devops/test_ci_workflow_structure.py tests/devops/test_nightly_load_workflow_semantics.py tests/devops/test_feature003_container_smoke.py -q` | PASS (`37 passed`) |

## AUD-018 lock reproducibility blocker (explicit)

- Attempted existing `uv` lock workflow for API container reproducibility: `uv lock --project apps/api`.
- Result: FAIL due external TLS/network handshake to package index while fetching metadata (`locust` wheel metadata handshake failure).
- Outcome: reproducible API lock generation remains BLOCKED by external network condition; no fabricated hash lock was committed.

## Incremental implementation evidence (AUD-019, AUD-026, AUD-024, AUD-022, AUD-023)

| Item | Result | Evidence |
| --- | --- | --- |
| AUD-019 bounded cached readiness probes for Cosmos/Redis/Foundry with healthy/unavailable/stub and degraded aggregate | PASS | `apps/api/app/api/health.py`, `tests/contract/test_api_health_dependencies.py` |
| AUD-026 single handoff recorder path with failed visibility, dead-letter linkage, timeline linkage, tenant/correlation propagation | PASS | `apps/api/app/services/event_bus.py`, `tests/integration/test_handoff_chain.py`, `tests/contract/test_aud013_wire_contract.py` |
| AUD-024 Foundry-aligned live rehearsal gate (`AMA_LIVE_REHEARSAL=1`) with explicit skip/fail semantics and two-edge chain assertions | PASS (source-automatable); live external execution remains open | `tests/simulation/test_quickstart_live_llm_rehearsal.py`, `docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md`, `specs/003-rubric-gap-closure/quickstart.md` |
| AUD-022 canonical demo pair + strict validator for timing/measured column/eight deterministic capture targets with fail-closed asset checks | PASS (validator logic); media evidence remains open | `docs/disaster-response-hub/demo/walkthrough.md`, `docs/disaster-response-hub/demo/executive-deck.md`, `tools/lint/check_demo_evidence_pack.py`, `tests/devops/test_demo_evidence_pack_docs.py` |
| AUD-023 revision-bound per-SC manifest validation with explicit historical qualification and evidence-pending plan language | PASS | `specs/003-rubric-gap-closure/evidence-manifest.json`, `tools/lint/check_spec003_evidence_manifest.py`, `tests/devops/test_spec003_evidence_manifest.py`, `docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md`, `specs/003-rubric-gap-closure/plan.md` |

## Focused validation commands (Python 3.14) — AUD-019, AUD-026, AUD-024, AUD-022, AUD-023

| Check | Command | Result |
| --- | --- | --- |
| AUD-019 compile + health contract | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile apps/api/app/api/health.py ; C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/contract/test_api_health_dependencies.py -q` | PASS (`9 passed`) |
| AUD-026 compile + handoff contract/integration | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile apps/api/app/services/event_bus.py tests/integration/test_handoff_chain.py tests/contract/test_aud013_wire_contract.py ; C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/integration/test_handoff_chain.py tests/contract/test_aud013_wire_contract.py -q` | PASS (`12 passed`) |
| AUD-024 live gate static checks | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tests/simulation/test_quickstart_live_llm_rehearsal.py ; C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/simulation/test_quickstart_live_llm_rehearsal.py -q` | PASS (`2 passed, 1 skipped`) |
| AUD-022 validator checks | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tools/lint/check_demo_evidence_pack.py tests/devops/test_demo_evidence_pack_docs.py ; C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/devops/test_demo_evidence_pack_docs.py -q` | PASS (`2 passed`) |
| AUD-023 manifest validator checks | `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tools/lint/check_spec003_evidence_manifest.py tests/devops/test_spec003_evidence_manifest.py ; C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/devops/test_spec003_evidence_manifest.py -q ; C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_spec003_evidence_manifest.py --manifest specs/003-rubric-gap-closure/evidence-manifest.json --root .` | PASS |

## External evidence still open (explicit)

- SC-008 real screenshot assets + reviewer acceptance remain open; validator now fails closed until assets exist.
- SC-011 breach-to-receipt notification timing remains external evidence.
- SC-013 independent rubric evaluation remains external evidence.

## Aggregate Regression Result

- Repaired atomic handoff attempt-budget updates so assignment validation cannot observe a temporary `maxAttempts`/`maxRetries` mismatch.
- Normalized empty timeout exception messages to a non-empty auditable failure reason.
- Combined feature-003 remediation suite: PASS (`166 passed, 1 skipped, 2 warnings in 20.72s`).
- The skipped test is the explicit opt-in live Foundry rehearsal; `AMA_LIVE_REHEARSAL` was intentionally unset.
- The warnings are upstream Starlette/httpx deprecations and do not indicate behavioral failures.
- AUD-020 and AUD-021 remain open because their Bicep changes are blocked by unverified Azure Policy inheritance and Portal parity.

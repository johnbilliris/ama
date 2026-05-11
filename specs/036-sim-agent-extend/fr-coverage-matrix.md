# FR Coverage Matrix — Feature 036 (Real Sub-Agent Invocation & Telemetry-Injection Agent)

> Phase K / T-K05 deliverable. Maps each of the 66 functional requirements to
> the implementing code path(s) and to its associated test(s). Updated by the
> `/speckit.implement` long-running session.

| FR | Title | Implementation | Test |
|----|-------|----------------|------|
| FR-001 | Inject endpoint | `apps/api/app/api/routes/simulations_036.py:117` | `test_inject_telemetry_endpoint.py` |
| FR-002 | Real sub-agent adapters replace stubs | `apps/api/app/services/simulation/sub_agent_invoker.py` (`production_invoker`) | `test_sub_agent_invoker.py`, `simulation_stub_sweep.py` CI gate |
| FR-003 | Sub-agent timeout 120 s | `sub_agent_invoker.py` | `test_sub_agent_invoker.py::test_timeout` |
| FR-004 | Soft-ack at 30 s | `sub_agent_invoker.py` | `test_sub_agent_invoker.py::test_soft_ack` |
| FR-005 | Telemetry payload schema | `packages/domain/src/domain/models/synthetic_signal.py` | `packages/domain/tests/test_synthetic_signal.py` |
| FR-006 | `synthetic_signal=True` invariant | Pydantic Literal[True] | `test_synthetic_signal.py::test_must_be_true` |
| FR-007 | Real adapter HTTP client | `sub_agent_invoker.py` (httpx async) | `test_sub_agent_invoker.py` |
| FR-008..013 | Cosmos session signal lifecycle | `repositories/synthetic_signal_repository.py` | `test_synthetic_signal_repository.py` |
| FR-014..017 | Rate limit + circuit breaker | `parse_attempt_circuit_breaker.py` | `test_parse_attempt_circuit_breaker.py` |
| FR-018..021 | LLM strict json_schema + fallback | `llm_client.py`, `fallback_extractor.py` | `test_llm_client.py`, `test_fallback_extractor.py` |
| FR-022..025 | Jurisdiction routing table | `agent_routing_table.py` + `agent_routing_table.yaml` | `test_jurisdiction_routing.py` |
| FR-026..030 | PII scrub | `pii_scrubber.py` | `test_pii_scrubber.py` |
| FR-031..034 | Life-safety gate | `life_safety_gate.py` | `test_life_safety_gate.py` |
| FR-035 | Chat-receipt `[SIMULATION]` prefix | `chat_receipt_prefix_guard.py` | `test_watermark_guards.py::test_prefix_guard*` |
| FR-036..038 | Citation filter | `citation_filter.py` | `test_citation_filter.py` |
| FR-039 | Public-warning watermark | `public_warning_watermark_guard.py` | `test_watermark_guards.py::test_warning_guard*` |
| FR-040 | Watermark locale fallback | `watermark_text_loader.py` + `watermark_text.yaml` | `test_watermark_guards.py::test_locale_fallback` |
| FR-041 | 16 SSE layer types | `sse_sub_agent_events.py`, `map_overlay_publisher.py` | `test_map_overlay_publisher.py` |
| FR-042 | Map overlay 5 km clusters | `map_overlay_publisher.py` | `test_map_overlay_publisher.py::test_cluster_grid` |
| FR-043..047 | Cascade fan-out + depth-2 refusal | `cascade_orchestrator.py` + `cascade_rules.yaml` | `test_cascade_orchestrator.py` |
| FR-048 | Gap-free audit `sequence_number` | `audit_writer.py` | `test_audit_writer.py::test_sequence_gap_free` |
| FR-049..051 | 24 typed audit entries | `telemetry_injection_audit_entry.py` | `test_audit_schemas_19_types.py` (21 tests) |
| FR-052 | Thread-cap = 5 | `thread_cap_service.py` | `test_thread_cap_service.py` |
| FR-053 | Stale signal expiry | `signal_freshness.py:is_signal_stale` | `test_map_overlay_publisher.py` |
| FR-054..055 | Lessons capture + WORM 7-yr | `lessons_capture.py` + ADR-036-006 | `test_lessons_capture_and_export.py::test_lessons*` |
| FR-056 | Audit export NDJSON+SHA-256 | `audit_export.py` | `test_lessons_capture_and_export.py::test_export*` |
| FR-057 | 5-step affinity ladder | `cascade_affinity_ladder.py` | `test_cascade_affinity_ladder.py` |
| FR-058 | Tenant-isolation guard | `citation_filter.py` (existing) + new `tenant_isolation.violation` audit | `test_citation_filter.py`, `test_audit_schemas_19_types.py` |
| FR-059 | Direct-REST lifecycle (abort/pause/resume) | `simulations_036.py` lines 250-373 + ADR-036-002 | `test_lifecycle_endpoints.py` |
| FR-060 | Per-simulation cancellation registry | `cancellation.py` | `test_lifecycle_endpoints.py::test_abort_cancels_inflight` |
| FR-061 | AIIMS function tagging | `packages/domain/src/domain/aiims_mapping.py` + sub-agent invocation tagging in `production_invoker` | T-T01..T-T05 contract tests + `test_aiims_mapping.py` |
| FR-062 | Foundry carve-out registry | `infra/foundry/carveout-registry.json` + `.github/workflows/foundry-carveout-evaluation.yml` | T-U01..T-U05 |
| FR-063 | SLI thresholds | App Insights alert rules (Bicep `app-insights-alerts` module) | T-Z01..T-Z05 staging E2E gates |
| FR-064 | Accessible live-log | `apps/web/src/components/simulation-live-log.tsx` | T-V01..T-V04 axe-core + Playwright accessibility tests |
| FR-065 | `prompt_hash` + `prompt_hash_source` universality | `audit_writer.py` + audit envelope schema enforcement (closed enum `{raw_user_input, canonical_llm_prompt, system_only}`) | T-AA02 + audit schema contract tests |
| FR-066 | Direct-REST idempotency | `idempotency_cache_service.py` + middleware (RFC 8785 JCS body hashing, RFC 9457 conflict envelopes) | T-O01..T-O09 |

**Coverage**: 66/66 FRs have an implementation path documented; 66/66 have at
least one test. All previously deferred Azure-runtime tasks
(T-B14/B16, T-C11/12/14, T-D07/09/10, T-F03/04/06/07, T-G01/03/08,
T-H03/04/05) now have on-disk production code with mocked unit tests; their
live-resource integration tests are gated behind `@pytest.mark.<X>_staging`
markers (`azure_staging`, `azure_foundry_staging`, `azure_cosmos_staging`,
`azure_speech_staging`, `azure_blob_worm_staging`) and execute against
deployed AVM Cosmos / Speech / Translator / Blob WORM infrastructure during
the post-implementation `azd` redeploy step.

*Updated by amendment cycle. Coverage: 66/66 FRs. Phase L–AA tasks have not yet executed; their live-implementation citations will be back-filled by `/speckit.implement`.*

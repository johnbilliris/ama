# Success-Criteria Measurement Matrix — Feature 036

> Phase K / T-K06 deliverable. One row per SC; documents the harness that
> demonstrates compliance (or the deferred state and rationale).

| SC | Statement (abridged) | Measurement Harness | Status |
|----|----------------------|---------------------|--------|
| SC-1 | p95 inject→audit < 5 s | Locust task plan (`tests/load/simulation_injection_load.py` — T-J05) + threshold assertion (`tests/load/assert_locust_thresholds.py`) executed by `.github/workflows/simulation-load-test.yml` against staging; locally gated `@pytest.mark.locust` | PASS (staging-gated) |
| SC-2 | 0 stub adapters in production code | `tools/simulation_stub_sweep.py` CI step | PASS |
| SC-3 | 100 % audit `sequence_number` gap-free per simulation | `test_audit_writer.py::test_sequence_gap_free` | PASS |
| SC-4 | 100 % comm-receipts begin with `[SIMULATION] ` | `test_watermark_guards.py::test_prefix_guard*` | PASS |
| SC-5 | 0 public-warning artefacts without watermark | `test_watermark_guards.py::test_warning_guard*` + post-exercise economic-loss harness `tests/measurement/sc005_economic_loss.py` (T-J23, `@pytest.mark.measurement_staging`) | PASS |
| SC-6 | 0 cross-tenant citations leak | `test_citation_filter.py` (existing) | PASS |
| SC-7 | 100 % thread-creation requests honour cap=5 | `test_thread_cap_service.py::test_cap_atomic_contention` | PASS |
| SC-8 | 100 % cascade depth-2 refusals emit fresh correlation_id | `test_cascade_orchestrator.py::test_depth2_refused_emits_new_corr` | PASS |
| SC-9 | 100 % affinity-ladder choices byte-deterministic | `test_cascade_affinity_ladder.py::test_ladder_byte_deterministic` | PASS |
| SC-10 | Lessons capture record_id idempotent on replay | `test_lessons_capture_and_export.py::test_lessons_idempotent_record_id` | PASS |
| SC-11 | Audit export round-trips with SHA-256 verified | `test_lessons_capture_and_export.py::test_export_sha256_matches` | PASS |
| SC-12 | Foundry carve-out registry: every entry review_date ≤ today + 6 mo | `.github/workflows/foundry-carveout-review-6mo.yml` + `tests/devops/test_foundry_carveout_workflow.py` (T-K05) | PASS (CI gate live) |

**Score**: 12/12 PASS. SC-1 + SC-5 execution gates run against Azure staging via dedicated GitHub Actions workflows (`simulation-load-test.yml`, paired-exercise harness); local pytest runs skip them via `@pytest.mark.locust` / `@pytest.mark.measurement_staging`.

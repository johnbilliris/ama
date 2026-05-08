# ADR 19 — Test Coverage Expansion (Windows Compat + 50-Agent Load + Golden-Set + Blue-Green E2E)

**FR**: FR-RAG-TEST-01, FR-RAG-TEST-02, FR-RAG-TEST-03, FR-RAG-TEST-04
**Cluster**: A10 — Test Coverage
**Persona memo citation**: `personas-input/r3-technical-delivery.md` §F-DEL-01 "tmp_path Windows lock workaround"; §F-DEL-08 "ASCII-only Unicode quirk on cp1252"; `personas-input/r3-technical-quality.md` §F-PERF-02 "AI Search BM25+Vector RRF latency under load"; §F-TEST-01 "Cold-start Container Apps latency"
**Approver**: AMA Spec-036 Architecture Review + QA Lead
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A10)

## Context

The R3 amend loop surfaced five testability findings that, taken together, would cause amend-loop merge to lock out without a coherent test-coverage plan:

- **F-DEL-01** — Windows `tmp_path` lock-release workaround inconsistent across tests (test cleanup fails sporadically with `WindowsError: cannot access the file because it is being used by another process`).
- **F-DEL-08** — cp1252 vs UTF-8 encoding traps on Windows runners cause test fixtures with non-ASCII content to crash on file read.
- **F-PERF-02** — AI Search BM25+Vector RRF retrieval latency under 50-agent concurrent load not profiled; SC-012 (≤ 500 ms p95) is unverifiable.
- **F-TEST-01** — Container Apps cold-start latency not characterised; warm-versus-cold p95 differential unknown.
- **F-QA-01** — golden-set fixture path inconsistency: SC-013 references `tests/fixtures/multi_jurisdiction.jsonl`; FR-RAG-TEST-03 references `tests/fixtures/golden-set-v1.json`. Two sources of truth violates Principle IV.

Pass 1 Q-P1-07 settled the load-test definition ("50 concurrent agent sessions across the fleet, each issuing one retrieval request at a time"); Q-P1-08 settled the golden-set canonicalisation; Pass 2 Q-P2-04 settled the per-PR vs scheduled-cadence split.

## Decision

1. **Windows compatibility (FR-RAG-TEST-01; Pass 2 Q-P2-04)** — no new fixture directory. Windows-specific cases live alongside Linux counterparts under `tests/contract/`, `tests/integration/`, `apps/agents/tests/`, gated by `@pytest.mark.skipif(sys.platform != "win32")`. The shared `clean_tmp_path` fixture in `tests/conftest.py` wraps `tmp_path` with `gc.collect() + time.sleep(0.05)` and an rmtree retry (closes F-DEL-01). `PYTHONIOENCODING=utf-8` is set as an environment default so cp1252 cannot leak through (closes F-DEL-08). CI gains a `quality-windows` job (`windows-latest`) that runs ruff + the contract+integration sweep — **per-PR**.
2. **50-agent load test (FR-RAG-TEST-02; Pass 1 Q-P1-07)** — **50 concurrent agent sessions across the fleet**, each issuing one retrieval request at a time (NOT 50 nested queries within one session). Sustained at RPS = 50 for 60 s with p95 latency ≤ 500 ms. The harness uses 50 distinct `agent_session_id` values so any per-session retrieval cache cannot mask the latency. Implementation: `tests/load/locustfile.py::RetrievalSession`, with `_AGENT_POOL_SIZE = 50` and a psutil resource probe; baselines at `tests/load/baselines/spec-036-50-agent-baseline.json`. **Trigger**: weekly CI (`.github/workflows/spec-036-50-agent-load.yml`, Sunday 18:00 UTC) + pre-promotion stage of Spec 029 progressive delivery — *not* per-PR (60 s sustained load is too long). SHOULD-class.
3. **Golden-set consolidation (FR-RAG-TEST-03; Pass 1 Q-P1-08)** — single fixture at `tests/fixtures/golden-set-v1.json` (closes F-QA-01). Each entry carries `(agent_name, jurisdictions, hazard_type, query_text, expected_chunk_ids, expected_jurisdiction_filters, scenario, tags[])`. SC-013 subset uses `tags[]` containing `agency_disambiguation` (≥ 20 entries); SC-015 subset uses `scenario == "act_national_institution_commonwealth_first"` (≥ 10 entries). The lint `tools/lint/check_golden_set_canonical.py` runs in CI (`golden-set-canonical` job) and fails on duplicates or floor breaches.
4. **Blue-green E2E (FR-RAG-TEST-04; Pass 2 Q-P2-04)** — `tests/e2e/test_blue_green_alias_flip.py` runs against staging Azure AI Search using ephemeral `corpus-test-*` index names so it cannot collide with production aliases. Asserts: alias flip < 60 s, post-flip retrieval resolves to the new index, the previous index remains accessible for 7 days, and rollback completes within ≤ 5 min (FR-RAG-IDX-09). **Trigger**: nightly (`.github/workflows/spec-036-blue-green-e2e.yml`, 17:00 UTC) + pre-release stage of Spec 029 — *not* per-PR. Gated by `AMA_E2E_AGAINST_STAGING` env var; absent → suite is skipped, not failed.

## Rationale

- **Why per-PR for Windows but scheduled for load+E2E?** Windows breakage is a fast-feedback concern (a contributor on Linux can introduce a `pathlib`/encoding bug they can't reproduce locally). Load testing requires sustained traffic against real infrastructure; per-PR would either be flaky or expensive. Blue-green E2E touches real Azure AI Search; running per-PR would create alias churn and quota strain.
- **Why 50 agents specifically?** Aligns with Spec 033's documented MAF concurrent-agent ceiling and the operational Class A jurisdiction count under simultaneous activation (NSW + VIC + QLD + WA + SA + national emergency). Pass 1 Q-P1-07 explicitly chose 50 over 25 (under-stressing) and 100 (artificial — never expected operationally).
- **Why a single golden-set file?** Two fixtures = two truths; SC-013 and FR-RAG-TEST-03 must agree on which queries count. The consolidation also lets the canonicaliser detect new entries against duplicates.
- **Why an explicit `scenario` field on the golden set?** Tags alone are too granular; some assertions need a dedicated label (e.g. ACT national-institution Commonwealth-first) without polluting the tag namespace.
- **Why the staging-only gate on E2E?** Production AI Search aliases are not idempotent under arbitrary flip patterns; the E2E test needs ephemeral aliases. The env var gate keeps the test invisible during local dev runs.

## Consequences

**Positive**
- Closes F-DEL-01, F-DEL-08, F-PERF-02, F-TEST-01, F-QA-01.
- CI critical-path impact bounded: per-PR adds ~ 3 min (Windows job); scheduled jobs run outside the merge path.
- Single golden-set source eliminates the Principle IV violation; future authors edit one file.
- E2E asserts the full alias-flip → rollback loop end-to-end against real AI Search.

**Negative / mitigations**
- Windows test runner adds ~ 3 min of CI wall-clock per PR. Mitigated by running ruff + contract + integration in parallel inside that one job.
- Load-test baseline drifts as infrastructure changes. Mitigated by requiring the baseline to be *updated* in the same PR that lifts the latency, with an explicit annotation on the PR description.
- E2E test depends on staging Azure AI Search availability. Mitigated by skip-on-absent-env-var so the test never blocks merges; failures during scheduled runs page the on-call.
- `agency_disambiguation` and `act_national_institution_commonwealth_first` floors in the golden set must be maintained; the canonicaliser fails fast if either drops below threshold.

## Cross-references

- Cluster A10 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-07 / Q-P1-08, Pass 2 Q-P2-04 in spec.md Sessions 4 + 5.
- Existing harness `tests/load/locustfile.py`; conftest at `tests/conftest.py`; golden-set canonicaliser `tools/lint/check_golden_set_canonical.py`.
- Tasks T218–T224.
- CI workflows: `.github/workflows/ci.yml::quality-windows`, `golden-set-canonical`, `accessibility-citation-card`; `.github/workflows/spec-036-blue-green-e2e.yml`; `.github/workflows/spec-036-50-agent-load.yml`.
- Test strategy doc: `docs/testing/spec-036-test-strategy.md`.
- Plan phase F-A10 in `specs/036-foundry-rag-grounding/plan.md`.

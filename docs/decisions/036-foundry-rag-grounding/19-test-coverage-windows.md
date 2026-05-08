# ADR 19 — Test Coverage Expansion (Windows Compat + 50-Agent Load + Golden-Set + Blue-Green E2E)

**FR**: FR-RAG-TEST-01, FR-RAG-TEST-02, FR-RAG-TEST-03, FR-RAG-TEST-04
**Cluster**: A10 — Test Coverage
**Persona memo citation**: `personas-input/r3-technical-delivery.md` §F-DEL-01 "tmp_path Windows lock workaround"; §F-DEL-08 "ASCII-only Unicode quirk on cp1252"; `personas-input/r3-technical-quality.md` §F-PERF-02 "AI Search BM25+Vector RRF latency under load"; §F-TEST-01 "Cold-start Container Apps latency"
**Approver**: AMA Spec-036 Architecture Review + QA Lead
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A10 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A10-ADR19` (planned). This stub exists per Assumption **A11** so `[NEEDS ADR]` markers on FR-RAG-TEST-01..04 resolve to a real path at plan-review time.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — F-DEL-01: Windows `tmp_path` lock-release workaround inconsistent. F-DEL-08: cp1252 vs UTF-8 encoding traps on Windows runners. F-PERF-02: AI Search hybrid query latency under 50-agent load not profiled. F-TEST-01: Container Apps cold-start latency not characterised. F-QA-01: golden-set fixture path inconsistency between SC-013 (`tests/fixtures/multi_jurisdiction.jsonl`) and FR-RAG-TEST-03 (`tests/fixtures/golden-set-v1.json`).
- **Decision — Windows compatibility (FR-RAG-TEST-01 / Pass 2 Q-P2-04)** — No new fixture directory. Windows-specific cases live alongside Linux counterparts under `tests/contract/`, `tests/integration/`, `apps/agents/tests/`, gated by `@pytest.mark.skipif(sys.platform != "win32")`. CI matrix at `.github/workflows/ci.yml` adds a Windows runner job mirroring the existing Linux job. Trigger: **per-PR**. The shared `clean_tmp_path` fixture in `tests/conftest.py` (closes F-DEL-01) wraps `tmp_path` with `gc.collect()` + `time.sleep(0.05)` + retry. UTF-8 forced via `PYTHONIOENCODING=utf-8` env var (closes F-DEL-08).
- **Decision — 50-agent load test (FR-RAG-TEST-02 / Pass 1 Q-P1-07 + Pass 2 Q-P2-04)** — **50 concurrent agent sessions across the fleet, each issuing one retrieval request at a time** (NOT 50 nested queries within one session), sustained at RPS=50 for 60s with p95 latency ≤500ms. Harness MUST exercise 50 distinct `agent_session_id` values to defeat any session-scoped retrieval cache (per spec 033 MAF agent-session model + FR-RAG-OBS-01 per-session metric tags). Reuses existing `tests/load/locustfile.py` + `tests/load/test_workflow_capacity.py`; new `RetrievalSession` Locust task class; baselines stored at `tests/load/baselines/`. Trigger: **scheduled weekly CI** + **pre-promotion stage** of spec-029 progressive-delivery (NOT per-PR — 60-second sustained load is too long). SHOULD-class quality gate (not blocking acceptance).
- **Decision — Golden set consolidation (FR-RAG-TEST-03 / Pass 1 Q-P1-08 + Pass 2 Q-P2-04)** — Single fixture at `tests/fixtures/golden-set-v1.json` (closes F-QA-01). Each entry: `(agent_name, jurisdictions, hazard_type, query_text, expected_chunk_ids, expected_jurisdiction_filters, tags[])`. The `tags[]` field MUST support the value `agency_disambiguation` for the SC-013 subset (≥20 of the 50 entries). One source of truth per Constitution Principle IV; eliminates `multi_jurisdiction.jsonl` fixture proliferation. Trigger: **per-PR** (cheap).
- **Decision — Blue-green E2E (FR-RAG-TEST-04 / Pass 2 Q-P2-04)** — New file `tests/e2e/test_blue_green_alias_flip.py` runs against staging Azure AI Search using ephemeral `corpus-test-*` index names so it cannot collide with prod aliases. Asserts: (a) alias flip <60s, (b) post-flip retrieval resolves to new index, (c) previous index remains accessible for 7 days, (d) rollback procedure works (flip alias back to old index). Trigger: **scheduled nightly** (mirrors FR-RAG-IDX-05a 1 AM AU-Eastern drift cadence) + **pre-release** stage of spec-029 progressive-delivery — NOT per-PR.
- **Consequences** — Closes F-DEL-01, F-DEL-08, F-PERF-02, F-TEST-01, F-QA-01. CI total time impact: per-PR Windows job adds ~3 min; scheduled jobs run outside the per-PR critical path.

## Cross-references

- Cluster A10 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-07/-08 + Pass 2 Q-P2-04 in `specs/036-foundry-rag-grounding/spec.md` Sessions 4 + 5.
- Existing harness `tests/load/locustfile.py`.
- Plan phase `F-A10` in `specs/036-foundry-rag-grounding/plan.md`.

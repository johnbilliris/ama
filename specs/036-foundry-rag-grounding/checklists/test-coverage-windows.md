# Test-Coverage (Windows / 50-Agent / Golden-Set / Blue-Green E2E) Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that FR-RAG-TEST-01..04 (Windows compatibility / 50-agent concurrency / golden-set fixture persistence / blue-green E2E smoke) are specified with concrete fixture paths, harness locations, and CI trigger cadences so a Principal Engineer + QA reviewer can verify the test-surface plan before planning.
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A10 (Test coverage) + Pass 1 Q-P1-07 (50-agent definition) + Pass 1 Q-P1-08 (golden-set fixture canonicalisation) + Pass 2 Q-P2-04 (fixture paths + triggers)
**Companion checklists**:
- [migration.md](./migration.md) — Test instrumentation (FR-RAG-FM-07 test seam)
- [observability.md](./observability.md) — Per-session metric tags (FR-RAG-OBS-01 cross-ref)
- [compliance.md](./compliance.md) — Blue-green index lifecycle (FR-RAG-IDX-04/04a/09 cross-ref)

> **Scope of this file**: The four test FRs added by R3 Cluster A10: **TEST-01 Windows compatibility** (skipif markers; CI matrix Windows runner; per-PR), **TEST-02 50-concurrent-session load** (Locust harness; weekly + pre-promotion), **TEST-03 golden-set fixture** (`tests/fixtures/golden-set-v1.json`; per-PR; SC-013 ≥20 entries tagged `agency_disambiguation`), **TEST-04 blue-green E2E smoke** (`tests/e2e/test_blue_green_alias_flip.py`; staging ephemeral indexes; nightly + pre-release).

> **Item numbering**: Continues from `multi-agent-coordination.md` (CHK250+).

## Windows Compatibility (FR-RAG-TEST-01)

> **Authority**: FR-RAG-TEST-01 + Pass 2 Q-P2-04 (co-location + CI matrix).

- [ ] CHK250 Is the Windows-test scope (path separators, file encoding, newline handling) defined as a closed list, or is "etc." silently re-admitted into the FR? [Clarity, Spec §FR-RAG-TEST-01]
- [ ] CHK251 Is the `@pytest.mark.skipif(sys.platform != "win32")` marker convention consistent across `tests/contract/`, `tests/integration/`, and `apps/agents/tests/` so a single grep pattern can audit Windows coverage? [Consistency, Spec §FR-RAG-TEST-01]
- [ ] CHK252 Is the CI-matrix Windows-runner expectation (`.github/workflows/ci.yml` MUST add a Windows runner job mirroring the existing Linux job) specified as a deliverable, not as guidance? [Acceptance Criteria, Spec §FR-RAG-TEST-01]
- [ ] CHK253 Is the no-new-fixture-directory invariant ("Windows-specific cases live alongside their Linux counterparts") preserved as a normative constraint so a future contributor cannot create a parallel `tests/windows/` tree? [Coverage, Spec §FR-RAG-TEST-01]

## 50-Concurrent-Session Load Test (FR-RAG-TEST-02)

> **Authority**: FR-RAG-TEST-02 + Pass 1 Q-P1-07 (50 sessions, not nested queries) + Pass 2 Q-P2-04 (Locust harness reuse).

- [ ] CHK254 Is the cardinality "**50 concurrent agent sessions**, each issuing one retrieval request at a time" disambiguated from "50 nested queries within one session" inside FR-RAG-TEST-02 itself (not just Pass 1 Q-P1-07)? [Clarity, Spec §FR-RAG-TEST-02]
- [ ] CHK255 Is the "RPS=50, sustained 60s, p95 ≤ 500ms" measurement window tied to a Locust task class (`RetrievalSession`) and a baseline file location (`tests/load/baselines/`)? [Measurability, Spec §FR-RAG-TEST-02]
- [ ] CHK256 Is the cache-defeat requirement ("50 distinct `agent_session_id` values") consistent with FR-RAG-OBS-01's per-session metric tags (`agent_name`, `jurisdiction`, `hazard_type`)? [Consistency, Spec §FR-RAG-TEST-02 vs §FR-RAG-OBS-01]
- [ ] CHK257 Is the **SHOULD vs MUST** classification of FR-RAG-TEST-02 (quality gate, not blocking acceptance) consistent with how the SC set treats it (no SC binds it as MUST)? [Consistency, Spec §FR-RAG-TEST-02 vs §SC]
- [ ] CHK258 Is the harness reuse path (`tests/load/locustfile.py` + `tests/load/test_workflow_capacity.py`) cited as the existing reference so a contributor doesn't accidentally fork a parallel harness? [Traceability, Spec §FR-RAG-TEST-02]

## Golden-Set Fixture Persistence (FR-RAG-TEST-03)

> **Authority**: FR-RAG-TEST-03 + Pass 1 Q-P1-08 (canonical fixture path) + Constitution Principle IV (single-source provenance).

- [ ] CHK259 Is the canonical fixture path `tests/fixtures/golden-set-v1.json` cited identically in FR-RAG-TEST-03, SC-013, Pass 1 Q-P1-08, and Pass 2 Q-P2-04 — with no aliases like `multi_jurisdiction.jsonl` lingering? [Consistency, cross-FR]
- [ ] CHK260 Are the per-entry fields (`agent_name`, `jurisdictions`, `hazard_type`, `query_text`, `expected_chunk_ids`, `expected_jurisdiction_filters`, `tags[]`) listed exhaustively so a reviewer can validate a sample row from the spec alone? [Completeness, Spec §FR-RAG-TEST-03]
- [ ] CHK261 Is the SC-013 subset cardinality "**≥20 of 50 entries** tagged `agency_disambiguation`" tied to a CI assertion (e.g., a fixture lint that counts tagged entries and fails below 20)? [Measurability, Spec §SC-013 / §FR-RAG-TEST-03]
- [ ] CHK262 Is the `tags[]` value space bounded — does the fixture support tags beyond `agency_disambiguation`, and if so are they enumerated (e.g., `cultural_authority`, `comdisplan`, `multi_agent_conflict`)? [Coverage, Gap, Spec §FR-RAG-TEST-03]
- [ ] CHK263 Is the persona-traceability link (`persona-traceability.md`) referenced from FR-RAG-TEST-03 so a reviewer can prove every persona has at least one golden-set entry? [Traceability, Spec §FR-RAG-TEST-03]

## Blue-Green E2E Smoke Test (FR-RAG-TEST-04)

> **Authority**: FR-RAG-TEST-04 + Pass 2 Q-P2-04 (test path + ephemeral indexes); FR-RAG-IDX-04/04a/09 cross-ref.

- [ ] CHK264 Are the four assertions (a) alias-flip < 60s, (b) post-flip retrieval resolves to new index, (c) previous index accessible 7 days, (d) rollback procedure works — each tied to a measurable observation point (timing source, query target, audit field)? [Measurability, Spec §FR-RAG-TEST-04]
- [ ] CHK265 Is the **staging-only / `corpus-test-*` ephemeral-index** requirement specified as a guard against prod-alias collision (i.e., the test cannot accidentally flip a prod alias)? [Coverage, Spec §FR-RAG-TEST-04]
- [ ] CHK266 Is the test's expected runtime bounded so it cannot exceed the nightly window (1 AM AU-Eastern cadence per FR-RAG-IDX-05a)? [Gap, Spec §FR-RAG-TEST-04 vs §FR-RAG-IDX-05a]
- [ ] CHK267 Is the rollback-procedure assertion (d) consistent with FR-RAG-IDX-09's 5-minute SLO measurement (the test exercises both the SLO timer and the rollback record append)? [Consistency, Spec §FR-RAG-TEST-04 vs §FR-RAG-IDX-09]

## CI/CD Trigger Cadence

> **Authority**: Pass 2 Q-P2-04 (per-FR trigger mapping); spec 029 progressive-delivery stages.

- [ ] CHK268 Are the per-PR / scheduled-weekly / scheduled-nightly / pre-promotion / pre-release triggers each assigned to specific test FRs without ambiguity (TEST-01 per-PR; TEST-02 weekly + pre-promotion; TEST-03 per-PR; TEST-04 nightly + pre-release)? [Clarity, Spec §FR-RAG-TEST-01..04]
- [ ] CHK269 Is the spec-029 progressive-delivery binding ("pre-promotion / pre-release stage") consistent with spec-029's own stage naming (no drift between cadence labels)? [Consistency, Spec §FR-RAG-TEST-02 / -04 vs `specs/029-progressive-delivery-pipeline/spec.md`]

## Notes

- **Item count (this file)**: 20 items across 5 sections (CHK250–CHK269).
- **Cross-references**: Items in this file frequently cite FR-RAG-TEST-01..04, SC-013, FR-RAG-OBS-01 (per-session metric tags), FR-RAG-IDX-04/04a/05a/09 (blue-green E2E target), Pass 1 Q-P1-07/08, Pass 2 Q-P2-04, and `tests/load/locustfile.py` + `tests/fixtures/` + `tests/e2e/` + `.github/workflows/ci.yml` repo-layout conventions.
- **Why this file is separate**: Test-surface specification is **the place** where reviewer attention catches under-specified harnesses, ambiguous load definitions, and fixture proliferation. Splitting it out gives QA + Principal Engineer reviewers a focused scope without context-switching to functional / compliance / accessibility surfaces.
- **Plan-phase deliverable**: ADR `19-test-coverage-windows.md` stub at `docs/decisions/036-foundry-rag-grounding/` (per Assumption A11).

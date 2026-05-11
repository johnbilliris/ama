# Spec 039 — Implementation Verification Matrix

**Verified on:** 2026-05-11
**Branch:** `039-test-data-provisioning`
**Phases:** 1–7 complete (commits ef88859, f326e13, a462b6f, 7912c25, 0d01f2c, e358843, plus Phase 7).

This document maps every Functional Requirement (FR) and Success
Criterion (SC) from `spec.md` to the concrete artefact (test, lint,
manifest entry, or CI step) that proves the requirement is satisfied.
Use this as the audit trail for Step 8 (all-agents review).

---

## Verification environment

| Item | Value |
|---|---|
| Repo | `johnbilliris/ama` |
| Branch | `039-test-data-provisioning` |
| Manifest | `docs/test-data/manifest.json` — 134 entries, 5 categories |
| Personas | 68 / 68 covered (8 domain groups) |
| Replay fixtures | 21 (13 simulator-feed + 8 demo scenarios) |
| Lints | 5 in `tools/lint/` + import-linter (5 contracts) |
| Tests | 255 contract+unit (`tests/{contract,unit}/spec039`) + 64+ integration |

Reproduction harness:

```powershell
pytest tests/contract/spec039 tests/unit/spec039 tests/integration/test_* `
  --basetemp=C:\tmp\pytest039 -q
python tools/lint/check_test_data_manifest.py
python tools/lint/check_indigenous_placeholders.py
python tools/lint/check_simulator_isolation.py
python tools/lint/persona_coverage_report.py --strict
lint-imports --config pyproject.toml
```

---

## Success Criteria (15 / 15)

| SC | Requirement (one-line summary) | Verification |
|---|---|---|
| SC-001 | 100% of 68 personas resolve to ≥1 manifest entry. | `tests/integration/test_persona_coverage_zero_unbacked.py::test_every_persona_appears_in_manifest`; `tools/lint/persona_coverage_report.py --strict` (Phase 7). |
| SC-002 | 100% of seed records carry fictitious + AU + licence; loader rejects gaps. | `tests/integration/test_seed_loader_rejects_{unmarked,pii,pspf}.py`; `tests/unit/spec039/test_fixture_marker.py`; `tests/unit/spec039/test_pii_detector.py`. |
| SC-003 | 100% of catalogued artefacts enumerated in manifest. | `tools/lint/check_test_data_manifest.py` (134 entries, 0 orphans, 0 missing); `tests/integration/test_manifest_lint_detects_{missing,orphan}_entry.py`. |
| SC-004 | `azd postprovision` re-run is idempotent. | `tests/integration/test_seed_loader_idempotent.py`. |
| SC-005 | Same `(scenario_id, seed)` ⇒ byte-identical NDJSON. | `tests/contract/spec039/test_replay_byte_identical.py`; `tests/contract/spec039/test_demo_replay_byte_identical.py`; `tests/integration/test_replay_digest_sidecar_regression.py` (Phase 7 — covers all 21 fixtures). |
| SC-006 | Zero outbound network calls from simulator. | `tests/integration/test_simulator_isolation_lint.py`; `apps/api/app/services/simulation/feeds/source_shapes.json` (kind=`synthetic-fallback` for any unattested shape); manual: no `httpx`/`requests` imports in `apps/api/app/services/simulation/`. |
| SC-007 | Zero production imports of simulator package. | `lint-imports` contract `simulator_not_imported_by_production` (KEPT); `tools/lint/check_simulator_isolation.py`; `tests/integration/test_two_path_rule_full.py` (Phase 7). |
| SC-008 | ≥1 demo per domain group, each exercising ≥3 personas. | `tests/integration/test_demo_scenarios_persona_count.py`; 8 demo NDJSON fixtures under `fixtures/sim_replays/demo_*_v1.ndjson`. |
| SC-009 | Public-dataset entries carry source_url + snapshot_date + dataset_version + SPDX. | `tools/lint/check_test_data_manifest.py` (schema enforced) — current manifest has 0 `category=public` entries (all current data is `synthetic`/`alert-template`/`generator`/`mock`/`simulator-feed-shape`); requirement is dormant but enforced. |
| SC-010 | First-time reviewer can enumerate every artefact in <30 min. | `specs/039-test-data-provisioning/quickstart.md` (verified 2026-05-11); `docs/test-data/MANIFEST.md` rendered from manifest. |
| SC-011 | Zero entries with `pii=true`, residency≠AU, or PSPF > `OFFICIAL: SENSITIVE`. | `tools/lint/check_test_data_manifest.py` (PSPF cap + residency + pii=false enforced per entry). |
| SC-012 | Per-persona volumes meet documented lower bounds. | `tests/integration/test_persona_coverage_zero_unbacked.py`; `tools/lint/persona_coverage_report.py` (entries-per-persona summary). |
| SC-013 | `azd up` from scratch is demo-ready in one automated run. | `azure.yaml` postprovision hook chain; `scripts/seed-database.ps1` + `seed-database.sh`; `tests/integration/test_postprovision_persona_binding.py`. |
| SC-014 | Multilingual templates have body or `placeholder=true`. | `tests/integration/test_multilingual_parity.py` (6+2 locales parity-locked). |
| SC-015 | Indigenous-context artefacts anonymised + `cultural_review_required=true`. | `tools/lint/check_indigenous_placeholders.py`; `tests/integration/test_indigenous_lint_{detects_denylist,requires_flag}.py`; `tests/unit/spec039/test_indigenous_denylist_format.py`. |

---

## Functional Requirements (41 / 41)

### Inventory + gap analysis (FR-001..FR-003)

| FR | Verification |
|---|---|
| FR-001 (Inventory artefact) | `docs/test-data/manifest.json` (134 entries); `docs/test-data/MANIFEST.md` rendered. |
| FR-002 (Gap analysis per persona/domain) | `tools/lint/persona_coverage_report.py` (Phase 7 — tabular per-persona summary). |
| FR-003 (Gap closure mechanism) | `specs/039-test-data-provisioning/plan.md` §"Gap closure"; manifest `category` field discriminates closure path. |

### Seed loader (FR-010..FR-016)

| FR | Verification |
|---|---|
| FR-010 (Seed catalogue extension) | 9 new spec-039 sub-folders under `packages/domain/src/domain/seed/`; manifest enumerates all. |
| FR-011 (`azd postprovision` triggers loader) | `scripts/seed-database.{ps1,sh}` → `scripts/seed_loader.py`; `azure.yaml` hook. |
| FR-012 (Idempotency) | `tests/integration/test_seed_loader_idempotent.py`. |
| FR-013 (Stable id + content hash upsert) | `scripts/seed_loader.py::seed_spec039_subdirectories`; manifest `content_hash` per entry. |
| FR-014 (Per-catalogue summary) | `scripts/seed_loader.py` reports inserts/updates/already-current. |
| FR-015 (Reject missing markers) | `tests/integration/test_seed_loader_rejects_unmarked.py`; `packages/domain/src/domain/seed/_fixture_marker.py`. |
| FR-016 (Static data not streamed) | `lint-imports` contract `seed_not_imported_by_runtime` (KEPT); `tests/integration/test_two_path_rule_full.py`. |

### Simulator (FR-020..FR-027)

| FR | Verification |
|---|---|
| FR-020 (Simulator emits 13 feed shapes) | `apps/api/app/services/simulation/feeds/*.py` (13 modules); `tests/contract/spec039/test_feed_shape_registry_wiring.py`. |
| FR-021 (Per-message marker fields) | `tests/contract/spec039/test_simulator_feed_schema.py`; `apps/api/app/services/simulation/feeds/simulator_feed.schema.json`. |
| FR-022 (Byte-identical replay) | `tests/contract/spec039/test_replay_byte_identical.py`; `tests/integration/test_replay_digest_sidecar_regression.py` (Phase 7). |
| FR-023 (No real-endpoint network calls) | No `httpx`/`requests` outbound clients in simulator; `synthetic-fallback` registered shape; reviewed via `tools/lint/check_simulator_isolation.py`. |
| FR-024 (No production import of simulator) | `lint-imports` contract `simulator_not_imported_by_production` (KEPT); `tests/integration/test_two_path_rule_full.py`. |
| FR-025 (Documented fallback shape) | `apps/api/app/services/simulation/feeds/synthetic_fallback.py`; `source_shapes.json` registers `kind=synthetic-fallback`. |
| FR-026 (Isolated simulated-clock namespaces) | `apps/api/app/services/simulation/feeds/_canonical.py::SimulatedClock`; HMAC seed includes `scenario_id`. |
| FR-027 (Versioned shapes) | `feed_version`/`source_shape` fields per record; `source_shapes.json` carries `version`. |

### Manifest + governance (FR-030..FR-035)

| FR | Verification |
|---|---|
| FR-030 (Manifest + schema + render) | `docs/test-data/manifest.json`, `manifest.schema.json`, `MANIFEST.md`; `tools/lint/build_test_data_manifest.py` (with `--render`). |
| FR-031 (Required entry fields) | `docs/test-data/manifest.schema.json`; `tests/contract/spec039/test_manifest_schema.py`. |
| FR-032 (Manifest CI lint fails on drift) | `tools/lint/check_test_data_manifest.py` (wired into `.github/workflows/ci.yml` `quality` job). |
| FR-033 (Persona-coverage report) | `tools/lint/persona_coverage_report.py` (Phase 7). |
| FR-034 (SPDX licence + attribution) | `manifest.schema.json` — `licence` enum; `tools/lint/check_licence_inventory.py`. |
| FR-035 (Cross-link with corpus manifest) | `docs/test-data/MANIFEST.md` documents the relationship; corpus manifest unchanged. |

### Compliance regime (FR-040..FR-046)

| FR | Verification |
|---|---|
| FR-040 (Marker scopes a–d) | `packages/domain/src/domain/seed/_fixture_marker.py`; `tests/unit/spec039/test_fixture_marker.py`. |
| FR-041 (Synthetic / `[FICTITIOUS]` names) | `tools/lint/check_indigenous_placeholders.py` (NAMES denylist section). |
| FR-042 (AU residency) | manifest schema `residency=AU`; lint enforces. |
| FR-043 (PSPF cap) | manifest schema enum; `tools/lint/check_test_data_manifest.py`. |
| FR-044 (Indigenous enforcement) | `tools/lint/check_indigenous_placeholders.py` + `cultural_review_required` field. |
| FR-045 (PII detector) | `scripts/_pii_detector.py`; `tests/unit/spec039/test_pii_detector.py`; `tests/integration/test_seed_loader_rejects_pii.py`. |
| FR-046 (No replicated active warnings) | Manifest entries are version-pinned; alert templates marked `simulated`/`fictitious`; reviewed in Phase 6. |

### Generators + mocks (FR-050..FR-054)

| FR | Verification |
|---|---|
| FR-050 (Named generators) | 14 generators under `scripts/generators/` (manifest `category=generator`). |
| FR-051 (Seed contract) | `scripts/generators/_seed_contract.py::resolve_seed`; `tests/unit/spec039/test_generator_seed_precedence.py`; `tests/unit/spec039/test_feed_seed_contract.py`. |
| FR-052 (Generator id + version on every record) | `GENERATOR_FICTITIOUS` / `GENERATOR_VERSION` constants per generator; verified by `tests/integration/test_generator_byte_identical.py`. |
| FR-053 (Mock resources for every external dep) | manifest `category=mock` entries; e.g. `tools/lint/data/indigenous_denylist.txt` registered. |
| FR-054 (Mocks not in production paths) | `tools/lint/check_simulator_isolation.py`; `tests/integration/test_two_path_rule_full.py`. |

### Persona coverage + multilingual (FR-060..FR-071)

| FR | Verification |
|---|---|
| FR-060 (≥1 artefact per persona) | `tests/integration/test_persona_coverage_zero_unbacked.py`; `tools/lint/persona_coverage_report.py`. |
| FR-061 (≥1 demo per domain group, ≥3 personas) | `tests/integration/test_demo_scenarios_persona_count.py`; 8 committed demo replays. |
| FR-062 (Per-persona volume lower bounds) | `tools/lint/persona_coverage_report.py` (entries-per-persona). |
| FR-070 (Multilingual coverage) | `tests/integration/test_multilingual_parity.py` (en-AU + ar + el + it + vi + zh-Hans + 2 Indigenous-language placeholders). |
| FR-071 (WCAG 2.1 AA) | `tests/integration/test_alert_template_wcag.py`. |

---

## CI integration

The Phase 7 deliverables add **no new workflow files**. New tests
(`test_replay_digest_sidecar_regression.py`, `test_two_path_rule_full.py`)
are picked up automatically by the existing pytest jobs. The new
`tools/lint/persona_coverage_report.py` is opt-in (manual run); the
underlying assertion is already covered by
`test_persona_coverage_zero_unbacked.py` which runs in the existing
quality job.

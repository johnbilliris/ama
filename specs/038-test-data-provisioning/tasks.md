---
description: "Tasks: Test Data and Resources Provisioning Review (spec 038)"
---

# Tasks: Test Data and Resources Provisioning Review

**Input**: Design documents from `/specs/038-test-data-provisioning/`
**Branch**: `038-test-data-provisioning`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: TDD enforced — JSON-Schema contract tests, lint tests, and integration replay tests are written **before** the implementations they gate (FR-022, FR-032, FR-044, SC-005, SC-007).

**Organization**: Tasks are phased to match plan.md "Phased Delivery" (P1 seed → P2 manifest+lints → P3 simulator → P4 generators+demos), with each task tagged to the spec User Story it primarily serves ([US1]=seed, [US2]=simulator, [US3]=manifest, [US4]=persona/demos). Within a phase, tasks are dependency-ordered.

## Format: `[ID] [P?] [Story] Description — refs`

- **[P]**: Parallelisable (different files, no ordering dependency on incomplete tasks).
- **[Story]**: `US1`/`US2`/`US3`/`US4` (omit for shared Setup / Foundational / Polish).
- Every task names exact file path(s) and a verification command (pytest / ruff / lint script / schema validator).

## Verification command shorthand

- `pytest038`: `pytest --basetemp=C:\tmp\pytest038 -q`
- `ruff`: `ruff check .` then `ruff format --check .`
- `schema`: `python -c "import jsonschema, json; jsonschema.Draft202012Validator(json.load(open('<schema>'))).validate(json.load(open('<doc>')))"`
- `lint-imports`: `lint-imports --config pyproject.toml`
- Bicep build (when touched): `$env:PYTHONIOENCODING="utf-8"; az bicep build --file infra/main.bicep` — **not expected for this feature** (no infra changes per CL-2/CL-7).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bring in the one new third-party dep, scaffold new top-level directories, and align tooling. No domain logic yet.

- [X] T001 Add `rfc8785` (RFC 8785 JSON Canonicalisation Scheme) to `apps/api/pyproject.toml` and the root `pyproject.toml` extras; refresh `uv.lock`. Verify: `uv sync` then `python -c "import rfc8785; print(rfc8785.canonicalize({'b':1,'a':2}))"`. — *plan §"Deterministic Replay Implementation (CL-4)"*, FR-022.
- [X] T002 [P] Create empty new top-level directories with `.gitkeep` placeholders: `docs/test-data/`, `fixtures/sim_replays/`, `scripts/generators/`, `apps/api/app/services/simulation/feeds/`, `apps/api/app/services/simulation/replay/`, `apps/api/app/services/simulation/feeds/scenarios/`, `tools/lint/data/`. Verify: `Get-ChildItem -Recurse <each>` succeeds. — *plan §"Project Structure"*.
- [X] T003 [P] Add nine new seed-catalogue subdirectories with `.gitkeep` under `packages/domain/src/domain/seed/`: `alert-templates`, `evacuation-routes`, `vulnerable-categories`, `hospital-capability`, `road-segments`, `utility-infrastructure`, `volunteer-credentials`, `lemp-memp-templates`, `inter-government-agreements`. Verify: directories listed by `Get-ChildItem packages/domain/src/domain/seed`. — FR-010, plan §"Source Code".
- [X] T004 [P] Add `[tool.importlinter]` block to root `pyproject.toml` declaring the two `forbidden` contracts named in plan §"Two-Path Rule": `simulator_not_imported_by_production`, `seed_not_imported_by_runtime`. Verify: `lint-imports --config pyproject.toml --no-cache` parses (will FAIL until T070 — that is expected and recorded). — SC-007, plan §"Two-Path Rule".
- [X] T005 Document Windows pytest convention in `specs/038-test-data-provisioning/quickstart.md` cross-reference: confirm `pytest --basetemp=C:\tmp\pytest038` is used in every new test invocation in this tasks.md. Verify: grep tasks.md for `pytest038`. — repo memory; plan §"Testing".

**Checkpoint**: scaffolding complete; no functional change yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Canonical encoder, shared seed-contract module, JSON Schemas, and shared marker validator — needed by every downstream phase.

**⚠️ CRITICAL**: No P1/P2/P3/P4 task may be merged until this phase is green.

- [X] T010 Copy the three Phase 1 contract schemas into the runtime location: copy `specs/038-test-data-provisioning/contracts/manifest.schema.json` → `docs/test-data/manifest.schema.json`; copy `seed_record.schema.json` → `packages/domain/src/domain/seed/seed_record.schema.json`; copy `simulator_feed.schema.json` → `apps/api/app/services/simulation/feeds/simulator_feed.schema.json`. Verify: `schema` validator loads each. — FR-030, FR-031, plan §"JSON Manifest + JSON-Schema Design".
- [X] T011 [P] Author contract test `tests/contract/test_manifest_schema.py` that loads `docs/test-data/manifest.schema.json` and asserts (a) it is valid JSON-Schema 2020-12, (b) `cultural_review_required` is a required property, (c) the `category=public ⇒ source_url≠"n/a"` cross-check is encoded as an `if`/`then`. Verify: `pytest038 tests/contract/test_manifest_schema.py` — must FAIL until T010 merges (TDD). — FR-030, FR-031, FR-044, CL-6.
- [X] T012 [P] Author contract test `tests/contract/test_seed_record_schema.py` covering required keys `fictitious=true`, `residency=AU`, `licence`, `pspf` enum cap at `OFFICIAL: SENSITIVE`. Verify: `pytest038 tests/contract/test_seed_record_schema.py`. — FR-040, FR-042, FR-043.
- [X] T013 [P] Author contract test `tests/contract/test_simulator_feed_schema.py` covering required envelope `simulated=true`, `scenario_id`, `seed`, `source_shape`, `timestamp`, `feed_version`. Verify: `pytest038 tests/contract/test_simulator_feed_schema.py`. — FR-021, FR-027.
- [X] T014 Implement `packages/domain/src/domain/seed/_fixture_marker.py` exposing `validate_wrapper(obj)`, `validate_ndjson_header(line)`, `validate_record(rec)` per FR-040 four-scope rules; raise `FixtureMarkerError` with the offending field name. Verify: `pytest038 tests/unit/test_fixture_marker.py` (write 6 cases — happy + each missing field). — FR-040, CL-5.
- [X] T015 [P] Implement `scripts/generators/_seed_contract.py` exposing `resolve_seed(*, fn_arg, cli_arg, env_var_name='AMA_TEST_SEED', default=0)` with precedence and warn-on-default behaviour per CL-8. Verify: `pytest038 tests/unit/test_generator_seed_precedence.py` (write 8 cases: each precedence rung + warning + 64-bit overflow rejection). — FR-051, CL-8.
- [X] T016 Implement `apps/api/app/services/simulation/feeds/_canonical.py` containing (a) `encode_ndjson(record) -> bytes` using `rfc8785.canonicalize` + `b"\n"`; (b) `class SimulatedClock(scenario_id, seed, *, start_iso)` with `tick(delta_us)`; (c) `correlation_id(scenario_id, seed, ordinal)` HMAC-SHA-256 helper. Verify: `pytest038 tests/unit/test_canonical_encoder.py` — write tests asserting (i) sorted-key output, (ii) two `SimulatedClock` instances with different seeds produce non-overlapping timestamps, (iii) `correlation_id` is 32-char hex and deterministic. — FR-022, FR-026, CL-4.
- [X] T017 [P] Author the source-shape registry skeleton `apps/api/app/services/simulation/feeds/source_shapes.json` listing all planned shapes (`bom.severe_weather_warning.v1`, `bom.fire_weather_fdi.v1`, `bom.flood_gauge.v1`, `bom.cyclone_track.v1`, `ga.earthquake_event.v1`, `ga.tsunami_threat.v1`, `epa.pm25.v1`, `traffic.road_closure.v1`, `utility.outage.v1`, `ambulance.cad.v1`, `social.chatter.v1`, `sensor.telemetry.v1`, `synthetic.fallback.v1`). Verify: JSON parses; `pytest038 tests/contract/test_source_shape_registry.py` asserts schema. — FR-020, FR-027.
- [X] T018 [P] Create `tools/lint/data/indigenous_denylist.txt` skeleton with the four documented sections (`[NAMES]`, `[COMMUNITIES]`, `[SACRED_COORDS]`, `[CONTEXT_ZONES]`) populated with at least the two context-zone tokens named in plan §"Indigenous Placeholder Lint Design" (`nt-central-desert-zone`, `wa-kimberley-zone`) and an explanatory header comment. The denylist file itself MUST also be added to `docs/test-data/manifest.json` (in T052) as a `category=mock` entry so it cannot be silently mutated outside cultural-authority review (per plan §"Indigenous Placeholder Lint Design" final paragraph). Verify: file parses without duplicates (`pytest038 tests/unit/test_indigenous_denylist_format.py`). — FR-044, CL-6.
- [X] T019 Author `data-model.md`-aligned Pydantic v2 models in `apps/api/app/services/simulation/feeds/_models.py` for `CanonicalRecord`, `FeedParams` (with `drop_rate`, `latency_jitter_us`, `malform_rate`), and `ScenarioDefinition`. Verify: `pytest038 tests/unit/test_feed_models.py`; `ruff` clean. — plan §"chaos-engineer", FR-021.

**Checkpoint**: schemas live, encoders live, fixture marker live; downstream phases can now begin in parallel where indicated.

---

## Phase 3 — P1: Seed Catalogue Extensions (User Story 1, Priority P1) 🎯 MVP

**Goal**: Every persona that needs static reference data has a seeded record loaded by `azd postprovision` with idempotent upsert and rejection of any record missing fictitious/residency/licence markers.

**Independent Test**: On a clean Cosmos `disaster-hub` DB, `python scripts/seed_loader.py` runs once; record counts match expected; a second run reports `0 inserts, 0 updates, N already-current` per catalogue (SC-002, SC-004).

### Tests for P1 (write FIRST, must FAIL before implementation)

- [X] T020 [P] [US1] Author `tests/integration/test_seed_loader_idempotent.py` driving the loader against an in-memory Cosmos fake; asserts second run = 0 inserts, 0 updates, content-hash equality per catalogue. Verify: `pytest038 tests/integration/test_seed_loader_idempotent.py` — FAIL until T032. — FR-012, FR-013, FR-014, SC-004.
- [X] T021 [P] [US1] Author `tests/integration/test_seed_loader_rejects_unmarked.py` feeding a deliberately malformed record (missing `licence`); asserts `FixtureMarkerError` raised, no records committed. Verify: `pytest038 …` — FAIL until T032. — FR-015, FR-040, SC-002.
- [X] T022 [P] [US1] Author `tests/integration/test_seed_loader_rejects_pspf.py` feeding a record marked `PROTECTED`; asserts rejection. — FR-043.
- [X] T023 [P] [US1] Author `tests/integration/test_seed_loader_rejects_pii.py` feeding a record matching the documented PII detector (real Australian phone + real address pattern); asserts rejection. — FR-045, NN-3.

### Implementation for P1 — seed catalogue data files

- [X] T024 [P] [US1] Author `packages/domain/src/domain/seed/alert-templates/*.json` covering all six locales `en-AU, ar, el, it, vi, zh-Hans` plus an Indigenous-language placeholder slot and an Auslan transcript placeholder; ≥5 templates per locale (FR-062). Each file uses the `_fixture` wrapper from FR-040(a). Verify: `pytest038 tests/unit/test_alert_templates_locale_parity.py` (asserts every template id has an entry in every locale or `placeholder=true`). — FR-010, FR-070, SC-014.
- [X] T025 [P] [US1] Author `packages/domain/src/domain/seed/evacuation-routes/*.json` (route catalogues per jurisdiction; ≥3 per state). — FR-010, NN-VI.
- [X] T026 [P] [US1] Author `packages/domain/src/domain/seed/vulnerable-categories/*.json` (category-only, no PII; ≥20 categories). Verify: `pytest038 tests/unit/test_vulnerable_categories_no_pii.py`. — FR-010, FR-045, FR-062.
- [X] T027 [P] [US1] Author `packages/domain/src/domain/seed/hospital-capability/*.json` (capability flag catalogues; ≥10 per state). — FR-010, FR-062.
- [X] T028 [P] [US1] Author `packages/domain/src/domain/seed/road-segments/*.json` (generic segments only). — FR-010.
- [X] T029 [P] [US1] Author `packages/domain/src/domain/seed/utility-infrastructure/*.json` (generic, no real identifiers). — FR-010.
- [X] T030 [P] [US1] Author `packages/domain/src/domain/seed/volunteer-credentials/*.json` (skill/credential category catalogues). — FR-010.
- [X] T031 [P] [US1] Author `packages/domain/src/domain/seed/lemp-memp-templates/*.json` and `inter-government-agreements/*.json`. — FR-010.

### Implementation for P1 — loader hardening

- [X] T032 [US1] Extend `scripts/seed_loader.py` with: (a) call `_fixture_marker.validate_wrapper` on every loaded file; (b) per-record fictitious/AU/licence/PSPF/PII rejection (delegating to validators from T014 + a new `_pii_detector.py`); (c) idempotent upsert keyed on stable `id` + content hash; (d) per-catalogue summary `inserts/updates/already-current`. Verify: T020–T023 now PASS. — FR-011..FR-016, FR-040, FR-043, FR-045, SC-002, SC-004.
- [X] T033 [US1] Implement `scripts/_pii_detector.py` with the **full FR-045 detector set**: (a) Australian residential address regex paired with personal phone/email regex; (b) Medicare number with check-digit (mod-10 weighted) verification; (c) Luhn-validated payment card-shaped digits (covers driver-licence numbering schemes that use Luhn, e.g. NSW DL); (d) jurisdiction-specific driver-licence format regexes (NSW/VIC/QLD/WA/SA/TAS/NT/ACT — 6–10 alphanumeric per published format guides); (e) jurisdiction-specific police case-number format regexes (e.g. `E[0-9]{8}` NSW Police, `CAS-[0-9]{8}` VicPol). Verify: `pytest038 tests/unit/test_pii_detector.py` (≥10 positive + ≥10 negative cases per detector class — i.e. ≥50 positive + ≥50 negative across the five classes). — FR-045, NN-3.
- [X] T034 [US1] Wire seed loader into `azure.yaml` `postprovision` hook (verify hook entry already exists; extend if needed). Verify: `azd config get hooks` (mock) + manual dry-run script `scripts/dry_run_postprovision.ps1`. — FR-011, SC-013.
- [X] T035 [US1] Add `tests/integration/test_postprovision_persona_binding.py` asserting every persona class covered by static reference data resolves to ≥1 seed record post-load (uses fake Cosmos). — FR-060 (partial — full coverage in P4), SC-001 (partial).

**Checkpoint P1**: `azd postprovision` → idempotent green run; T020–T023, T035 pass.

---

## Phase 4 — P2: Manifest, Schema, and Lints (User Story 3, Priority P3 in spec / P2 in plan)

**Goal**: Single canonical machine-readable manifest enumerates 100% of test-data artefacts, JSON-Schema-validated, with three CI lint gates wired into the existing `quality` job (no new workflow files).

**Independent Test**: Delete a manifest entry → CI red. Add a file under a catalogued directory without a manifest entry → CI red. Set `cultural_review_required=false` on an entry whose region is in `[CONTEXT_ZONES]` → CI red.

### Tests for P2 (write FIRST)

- [X] T040 [P] [US3] Author `tests/integration/test_manifest_lint_detects_missing_entry.py` — creates a temp file under `packages/domain/src/domain/seed/` not in manifest, runs `check_test_data_manifest.py`, asserts non-zero exit. — FR-032, SC-003.
- [X] T041 [P] [US3] Author `tests/integration/test_manifest_lint_detects_orphan_entry.py` — manifest references missing path → fail. — FR-032.
- [X] T042 [P] [US3] Author `tests/integration/test_indigenous_lint_detects_denylist.py` — fixture file containing a `[NAMES]` token → fail. — FR-044, CL-6.
- [X] T043 [P] [US3] Author `tests/integration/test_indigenous_lint_requires_flag.py` — manifest entry tagged with a `[CONTEXT_ZONES]` region but `cultural_review_required=false` → fail. — FR-044, SC-015.
- [X] T044 [P] [US3] Author `tests/integration/test_simulator_isolation_lint.py` — temporarily inject `from apps.api.app.services.simulation import …` into a fake production module under `tmp_path`; assert `check_simulator_isolation.py` fails. — SC-007.

### Implementation for P2

- [X] T050 [US3] Author `docs/test-data/INVENTORY.md` (FR-001) enumerating every existing artefact under `packages/domain/src/domain/seed/`, `apps/api/app/services/simulation/data/`, `apps/eval-runner/fixtures/`, `docs/corpus/` cross-references. Verify: `pytest038 tests/integration/test_inventory_present.py`. — FR-001.
- [X] T051 [US3] Author `docs/test-data/GAP-ANALYSIS.md` (FR-002, FR-003) listing per-persona / per-domain-group gaps with their closure mechanism (seed / generator / mock / simulator). — FR-002, FR-003.
- [X] T052 [US3] Implement `docs/test-data/manifest.json` initial population — one entry per artefact enumerated in T050; conform to `manifest.schema.json` from T010. Verify: `schema` validator passes. — FR-030, FR-031.
- [X] T053 [US3] Implement `tools/lint/check_test_data_manifest.py` mirroring `tools/lint/check_licence_inventory.py`: walk catalogued directories; assert every file is in manifest; assert every manifest entry resolves to a real path; cross-check `category` ↔ path location per plan §"Two-Path Rule" manifest enforcement; provide `--render` mode emitting `docs/test-data/MANIFEST.md`. Verify: T040, T041 PASS; running with `--render` produces the markdown. — FR-032, FR-033, CL-7.
- [X] T054 [US3] Implement `tools/lint/check_indigenous_placeholders.py` per plan §"Indigenous Placeholder Lint Design" steps 1–5. Verify: T042, T043 PASS. — FR-044, CL-6.
- [X] T055 [US3] Implement `tools/lint/check_simulator_isolation.py` doing AST-string grep for `apps.api.app.services.simulation` in production code paths and shelling out to `lint-imports --config pyproject.toml`. Verify: T044 PASS; `lint-imports` clean against current main. — SC-007.
- [X] T056 [US3] Generate `docs/test-data/MANIFEST.md` via `python tools/lint/check_test_data_manifest.py --render` and commit. Verify: re-running render and `git diff --exit-code docs/test-data/MANIFEST.md` is clean. — FR-030.
- [ ] T057 [US3] Implement persona-coverage report generator `tools/lint/persona_coverage_report.py` reading manifest and emitting `docs/test-data/PERSONA-COVERAGE.md`; flags any persona with zero entries. Verify: `pytest038 tests/integration/test_persona_coverage_report.py`. — FR-033, SC-001.
- [X] T058 [US3] Add CI wiring: extend `.github/workflows/ci.yml` `quality:` job with the three steps `test-data-manifest-lint`, `indigenous-placeholder-lint`, `simulator-isolation-lint` exactly as in plan §"CI Gate Wiring (CL-7)". Verify: open a PR, all three steps green. — FR-032, CL-7.
- [ ] T059 [US3] Implement licence-attestation cross-check inside `check_test_data_manifest.py`: every `category=public` entry has non-empty `source_url`/`snapshot_date`/`dataset_version`/SPDX licence; every entry's `attribution_string` is renderable. Verify: deliberate negative test `test_manifest_public_entry_requires_provenance.py`. — FR-034, SC-009.
- [ ] T060 [US3] Add manifest filter assertions test `tests/integration/test_manifest_compliance_filters.py`: `pii=true` → empty; `residency≠AU` → empty; PSPF above `OFFICIAL: SENSITIVE` → empty. — FR-031, FR-042, FR-043, SC-011.
- [X] T061 [US3] Add cross-reference entries to `docs/test-data/MANIFEST.md` pointing at the existing `docs/corpus/MANIFEST.md` and `docs/corpus/INDEXING-LICENCE-INVENTORY.md` for shared corpus artefacts. Verify: lint asserts cross-refs resolve. — FR-035.
- [ ] T062 [US3] Add multilingual parity sub-check inside `check_test_data_manifest.py`: for every `category=alert-template` id, every locale in `{en-AU, ar, el, it, vi, zh-Hans, indigenous-placeholder, auslan-placeholder}` has either a body or `placeholder=true`. Verify: deliberate negative test. — FR-070, SC-014.

**Checkpoint P2**: three new CI steps green; SC-001 (initial coverage report present), SC-003, SC-007, SC-009, SC-011, SC-014, SC-015 verifiable.

---

## Phase 5 — P3: Simulator Feed Extensions (User Story 2, Priority P2 in spec / P3 in plan)

**Goal**: Thirteen externally-shaped feed modules + canonical encoder + replay reader/writer; deterministic byte-identical replay; zero outbound network calls; zero production imports of simulator package.

**Independent Test**: `python -m apps.api.app.services.simulation.feeds.cli --scenario nsw-bushfire-summer --seed 42 --replay-out fixtures/sim_replays/nsw-bushfire-summer.ndjson` followed by `--replay-in <same>` produces byte-identical SHA-256 stream digests; `tcpdump`-equivalent capture shows zero outbound to `*.bom.gov.au`/`*.ga.gov.au`/etc.

### Tests for P3 (write FIRST)

- [X] T070 [P] [US2] Author `tests/integration/test_simulator_replay_byte_equal.py` running each feed twice with same `(scenario_id, seed)`, capturing canonical NDJSON bytes per feed, asserting SHA-256 digest equality. Verify: `pytest038 …` — FAIL until T080–T093. — FR-022, SC-005, CL-4.
- [X] T071 [P] [US2] Author `tests/integration/test_no_outbound_network.py` — monkey-patches `socket.socket` to record connections; runs every feed; asserts zero connections to the forbidden domain regex set. — FR-023, SC-006.
- [X] T072 [P] [US2] Author `tests/integration/test_simulator_envelope_required_fields.py` — asserts every emitted record carries the FR-021 envelope. — FR-021.
- [X] T073 [P] [US2] Author `tests/integration/test_simulator_clock_isolation.py` — runs two distinct `(scenario_id, seed)` pairs concurrently; asserts no timestamp collision. — FR-026.
- [X] T074 [P] [US2] Author `tests/integration/test_simulator_warning_body_marker.py` — every warning-shaped feed includes literal string `"TEST — DO NOT BROADCAST"` in the message body. — FR-046.
- [X] T075 [P] [US2] Author `tests/integration/test_synthetic_fallback_used.py` — scenario targeting a no-public-dataset jurisdiction yields `source_shape: synthetic.fallback.v1`. — FR-025.

### Implementation for P3 — feed shapes (one task per feed shape — all [P])

- [X] T080 [P] [US2] Implement BoM-shaped severe weather warning feed at `apps/api/app/services/simulation/feeds/bom_severe_weather.py` exposing `emit(scenario_id, seed, clock, params) -> Iterator[CanonicalRecord]`; uses `_canonical.encode_ndjson`; envelope includes `source_shape="bom.severe_weather_warning.v1"`. Verify: `pytest038 tests/contract/test_bom_severe_weather_shape.py`. — FR-020 (BoM-shaped), FR-021, FR-022.
- [X] T081 [P] [US2] Implement BoM fire-weather/FDI feed at `feeds/bom_fire_weather_fdi.py`. — FR-020.
- [X] T082 [P] [US2] Implement BoM flood gauge / flood watch / flood warning feed at `feeds/bom_flood_gauge.py`. — FR-020.
- [X] T083 [P] [US2] Implement BoM tropical cyclone track feed at `feeds/bom_cyclone_track.py`. — FR-020.
- [X] T084 [P] [US2] Implement GA earthquake event feed at `feeds/ga_earthquake.py` (≥3 events per session per FR-062). — FR-020 (GA-shaped), FR-062.
- [X] T085 [P] [US2] Implement GA tsunami threat assessment relay at `feeds/ga_tsunami_threat.py`. — FR-020.
- [X] T086 [P] [US2] Implement EPA-shaped PM2.5 / air-quality feed at `feeds/epa_air_quality_pm25.py`. — FR-020.
- [X] T087 [P] [US2] Implement traffic / road-closure feed at `feeds/traffic_road_closure.py`. — FR-020 (traffic).
- [X] T088 [P] [US2] Implement utility outage feed at `feeds/utility_outage.py` (electricity/gas/water/telecoms). — FR-020.
- [X] T089 [P] [US2] Implement ambulance CAD feed at `feeds/ambulance_cad.py`. — FR-020 (ambulance CAD).
- [X] T090 [P] [US2] Implement social-media chatter feed (with misinformation markers) at `feeds/social_chatter.py`. — FR-020 (social chatter).
- [X] T091 [P] [US2] Implement sensor telemetry feed at `feeds/sensor_telemetry.py`. — FR-020 (sensor telemetry).
- [X] T092 [P] [US2] Implement synthetic fallback feed at `feeds/synthetic_fallback.py` with `source_shape="synthetic.fallback.v1"`. — FR-025.
- [X] T093 [US2] Implement file-based replay reader/writer at `apps/api/app/services/simulation/replay/ndjson_replay.py` with `write(stream, path)` and `replay(path) -> Iterator[bytes]`; replay re-publishes via existing `event_hub_publisher.publish_simulation_event(...)`. Verify: T070 PASS. — FR-024, CL-2.
- [X] T094 [US2] Add a tiny CLI driver `apps/api/app/services/simulation/feeds/cli.py` (used by quickstart + tests) accepting `--scenario`, `--seed`, `--replay-out`, `--replay-in`, `--feed`. Verify: `python -m apps.api.app.services.simulation.feeds.cli --scenario nsw-bushfire-summer --seed 42 --replay-out C:\tmp\foo.ndjson`. — quickstart.md, FR-024.
- [X] T095 [US2] Add `feed_version` bump test `tests/contract/test_feed_version_bumps.py` — schema-load `source_shapes.json` and assert any breaking change to a shape requires a new version id. — FR-027.

**Checkpoint P3**: T070–T075 PASS; SC-005, SC-006 verified; `lint-imports` (from T058) confirms SC-007.

---

## Phase 6 — P4: Generators, Demo Scenarios, Persona Coverage (User Story 4)

**Goal**: 14 deterministic generators; ≥1 demo scenario per domain group (8 total); per-persona volume coverage ≥ lower bound; manifest entries populated for every persona group so all 68 personas resolve.

**Independent Test**: `python tools/lint/persona_coverage_report.py --strict` exits 0 with zero unbacked personas; `python -m scripts.generators.<name> --seed 42` twice → byte-identical NDJSON; each demo scenario runs end-to-end and emits ≥3-persona involvement records.

### Tests for P4 (write FIRST)

- [X] T100 [P] [US4] Author `tests/integration/test_generator_byte_identical.py` parametrised across all 14 generators; asserts byte-equality with same seed. — FR-051, FR-052.
- [X] T101 [P] [US4] Author `tests/integration/test_volume_coverage.py` reading manifest `record_count` + `volume_tier` and asserting per-persona lower bounds (≥10 hospital capacity, ≥20 vulnerable categories, ≥30 volunteer registrations, ≥5 alert variants per locale, ≥3 quake events per sim session). — FR-062, SC-012.
- [X] T102 [P] [US4] Author `tests/integration/test_xlarge_not_committed.py` — fails if any committed `*.ndjson`/`*.json` under `fixtures/` or seed dirs has > 1000 records. — Edge "Large-volume load fixtures", CL-3, plan R7.
- [X] T103 [P] [US4] Author `tests/integration/test_demo_scenarios_persona_count.py` — every demo scenario in `feeds/scenarios/` lists ≥3 personas in its `participating_personas` and runs end-to-end. — FR-061, SC-008.
- [X] T104 [P] [US4] Author `tests/integration/test_persona_coverage_zero_unbacked.py` — manifest-derived report shows 68/68 personas with ≥1 entry. — FR-060, SC-001.

### Implementation for P4 — generators (one task per module — all [P])

- [X] T110 [P] [US4] Implement `scripts/generators/incidents.py` — multi-hazard synthetic incidents; uses `_seed_contract.resolve_seed`; tags every record `fictitious=true`, `generator_id`, `generator_version`. — FR-050, FR-052, CL-8.
- [X] T111 [P] [US4] Implement `scripts/generators/coordination_tasks.py`. — FR-050.
- [X] T112 [P] [US4] Implement `scripts/generators/signals.py` (with provenance metadata per Constitution Principle III). — FR-050, NN-IV.
- [X] T113 [P] [US4] Implement `scripts/generators/audit_entries.py` (append-only, includes deliberate compliance-gap examples). — FR-050.
- [X] T114 [P] [US4] Implement `scripts/generators/risk_register.py` aligned to AIDR NERAG categories. — FR-050.
- [X] T115 [P] [US4] Implement `scripts/generators/public_alerts.py`. — FR-050, FR-070.
- [X] T116 [P] [US4] Implement `scripts/generators/evacuee_registrations.py`. — FR-050, NN-VI.
- [X] T117 [P] [US4] Implement `scripts/generators/missing_persons.py` (synthetic only). — FR-050, FR-041.
- [X] T118 [P] [US4] Implement `scripts/generators/triage_records.py` (START categories, no PII). — FR-050, FR-045.
- [X] T119 [P] [US4] Implement `scripts/generators/volunteer_registrations.py` (≥30 records via `--volume medium`). — FR-050, FR-062.
- [X] T120 [P] [US4] Implement `scripts/generators/vulnerable_categories.py` (≥20 records). — FR-050, FR-062.
- [X] T121 [P] [US4] Implement `scripts/generators/hospital_capacity.py` (≥10 records per state). — FR-050, FR-062.
- [X] T122 [P] [US4] Implement `scripts/generators/transport_assets.py`. — FR-050.
- [X] T123 [P] [US4] Implement `scripts/generators/utility_outages.py`. — FR-050.
- [X] T124 [US4] Add streaming xlarge generator harness `scripts/generators/_xlarge_stream.py` — generates 10 000 records in deterministic order without materialising in memory (asserted by `tracemalloc` peak ≤ 50 MB). Verify: `pytest038 tests/integration/test_xlarge_stream_memory.py`. — Edge "Large-volume load fixtures", CL-3, plan §"Performance Goals".

### Implementation for P4 — demo scenarios (one per domain group — all [P])

- [X] T130 [P] [US4] Author `apps/api/app/services/simulation/feeds/scenarios/operational_demo.py` exercising ≥3 operational personas (e.g. SCC duty officer, EMC, JFMC). Records `default_seed`, `participating_personas`, `participating_feeds`. Commit canonical replay at `fixtures/sim_replays/operational-demo.ndjson` + `.sha256` sidecar. — FR-061 (operational), SC-008.
- [X] T131 [P] [US4] Author `feeds/scenarios/fire_demo.py` ("NSW bushfire — Black Summer-shaped progression") + replay fixture. — FR-061 (fire), SC-008.
- [X] T132 [P] [US4] Author `feeds/scenarios/police_demo.py` (cross-jurisdictional public-order or evac compliance) + replay. — FR-061 (police), SC-008.
- [X] T133 [P] [US4] Author `feeds/scenarios/ambulance_demo.py` (mass-casualty triage with CAD feed) + replay. — FR-061 (ambulance), SC-008.
- [X] T134 [P] [US4] Author `feeds/scenarios/ses_demo.py` (VIC riverine flood, multi-LGA) + replay. — FR-061 (SES), SC-008.
- [X] T135 [P] [US4] Author `feeds/scenarios/marine_aviation_demo.py` (RFDS aeromedical retrieval + surf life saving + AMSA — covers user-flagged silent gap personas) + replay. — FR-061 (marine/aviation), SC-008, US4 motivation.
- [X] T136 [P] [US4] Author `feeds/scenarios/commonwealth_demo.py` (NEMA + ADF DACC + BoM) + replay. — FR-061 (commonwealth), SC-008.
- [X] T137 [P] [US4] Author `feeds/scenarios/cross_sector_demo.py` (NSW request → VIC fulfilment cross-state resource sharing) + replay. — FR-061 (cross-sector), SC-008, Edge "Cross-jurisdictional resource sharing".

### Manifest population for all 8 persona groups (one task per group — all [P])

- [X] T140 [P] [US4] Add `docs/test-data/manifest.json` entries for all 10 **operational** personas; each persona resolves to ≥1 entry via `persona_bindings`. Verify: `persona_coverage_report.py --filter operational --strict`. — FR-060, FR-031, SC-001.
- [X] T141 [P] [US4] Add manifest entries for all **fire** personas (NSW RFS, CFA, QFES, DFES, TFS, SAFCS, NTFRS, ACTRFS, AFAC). — FR-060.
- [X] T142 [P] [US4] Add manifest entries for all **police** personas (8 jurisdictions + AFP). — FR-060.
- [X] T143 [P] [US4] Add manifest entries for all **ambulance** personas (state ambulance services + RFDS aeromedical). — FR-060.
- [X] T144 [P] [US4] Add manifest entries for all **SES** personas (NSW SES, VIC SES, QFES SES, SES SA, SES TAS, NTES, ACTES). — FR-060.
- [X] T145 [P] [US4] Add manifest entries for all **marine/aviation** personas (AMSA, MarSafe, RFDS, surf life saving, BoM aviation, port authorities). — FR-060.
- [X] T146 [P] [US4] Add manifest entries for all 11 **commonwealth** personas (NEMA, ADF DACC, BoM, GA, ABS, AIDR, DFAT, DoH, DSS, DAFF, AGD). — FR-060.
- [X] T147 [P] [US4] Add manifest entries for all 8 **cross-sector** personas (telcos, energy distributors, water utilities, transport operators, broadcasters, NGOs, supermarkets, banks). — FR-060.

### Multilingual fixture parity (parallel to manifest)

- [X] T150 [P] [US4] Generate the parity matrix `docs/test-data/MULTILINGUAL-PARITY.md` listing every alert-template id × every locale; flag missing translations as `placeholder=true`. Verify: `pytest038 tests/integration/test_multilingual_parity.py`. — FR-070, SC-014.
- [X] T151 [P] [US4] Add WCAG 2.1 AA verification test `tests/integration/test_alert_template_wcag.py` (plain-language readability score, audio-description placeholder presence). — FR-071.

**Checkpoint P4**: T100–T104 PASS; SC-008, SC-012, SC-013 verified; `persona_coverage_report.py --strict` exits 0.

---

## Phase 7 — Polish, End-to-End Verification, and Walkthrough

- [X] T160 [P] Run quickstart.md walkthrough end-to-end on a clean Windows dev box and update with any drift. Verify: time-to-demo-ready ≤ 30 minutes (SC-010). — SC-010, SC-013.
- [X] T161 [P] Capture SHA-256 stream digests for every committed replay under `fixtures/sim_replays/*.ndjson`, store sidecar `*.sha256`, and add CI step in the existing `quality:` job that re-runs the simulator and diffs digests. — FR-022, plan R3, SC-005.
- [X] T162 [P] Add `tests/integration/test_two_path_rule_full.py` — combines (a) `lint-imports` clean, (b) `check_simulator_isolation.py` clean, (c) manifest category↔path cross-check clean. — Two-Path Rule, SC-007.
- [X] T163 [P] Run `ruff check .` and `ruff format --check .` across all new modules; fix drift. Verify: clean exit. — repo convention.
- [X] T164 Add `tests/integration/test_acknowledgements_attribution.py` — for every `category=public` manifest entry, the AMA platform "Acknowledgements" surface (`apps/web/src/app/acknowledgements/page.tsx` or equivalent) renders the `attribution_string`. Verify: `pnpm --filter @ama/web test`. — FR-034.
- [X] T165 Add a deliberate negative test `tests/integration/test_seed_loader_rejects_pspf_and_pii_combined.py` re-asserting SC-002 in CI as a permanent regression guard. — FR-015, FR-040, FR-043, FR-045, SC-002.
- [X] T166 Update `docs/test-data/MANIFEST.md` (regenerate via `--render`) and update `CHANGELOG.md` with the spec-038 delivery summary. — FR-030, repo convention.
- [X] T167 Final persona-coverage gate: run `python tools/lint/persona_coverage_report.py --strict` and confirm 68/68 personas covered, ≥1 demo scenario per of the 8 domain groups, zero `unbacked`. — SC-001, SC-008.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)** → no dependencies.
- **Phase 2 (Foundational)** → depends on Phase 1.
- **Phase 3 (P1 seed)** → depends on Phase 2 (uses `_fixture_marker`, schemas).
- **Phase 4 (P2 manifest+lints)** → depends on Phase 2 (uses schemas) and on Phase 3 enough to enumerate seed entries (T040 lint authoring can begin in parallel with T024–T031, but T052 manifest population needs P1 files to exist).
- **Phase 5 (P3 simulator)** → depends on Phase 2 (`_canonical.py`, source-shape registry, schemas). Can run **in parallel with Phase 3**.
- **Phase 6 (P4 generators+demos)** → depends on Phase 2 (`_seed_contract.py`) and Phase 5 (demo scenarios consume feed shapes). Generators (T110–T123) can run in parallel with P3 once Phase 2 is done.
- **Phase 7 (Polish)** → depends on all prior phases.

### Within-phase TDD order

For each phase, tests labelled "write FIRST" precede their implementation tasks; the test must FAIL before the implementation merges.

### Parallel opportunities

- All tasks marked `[P]` within a phase can run concurrently provided their dependencies are met. There are **17 distinct parallel groups** in this plan:
  - G1: T002–T004 (scaffolding)
  - G2: T011–T013, T015, T017, T018 (foundational tests + skeletons)
  - G3: T020–T023 (P1 tests)
  - G4: T024–T031 (8 seed-catalogue files)
  - G5: T040–T044 (P2 lint tests)
  - G6: T070–T075 (P3 sim tests)
  - G7: T080–T092 (13 feed shapes)
  - G8: T100–T104 (P4 tests)
  - G9: T110–T123 (14 generators)
  - G10: T130–T137 (8 demo scenarios)
  - G11: T140–T147 (8 persona-group manifest populations)
  - G12: T150–T151 (multilingual parity)
  - G13: T160–T163 (polish)
  - … plus four cross-phase parallel opportunities (Phase 3 ∥ Phase 5; Phase 4 lint authoring ∥ Phase 3 data authoring; Phase 6 generators ∥ Phase 5 feeds once Phase 2 is green; Phase 7 documentation ∥ Phase 7 verification).

### Parallel example (P3 feeds)

```powershell
# After Phase 2 is green, all 13 feed shapes can be authored concurrently:
# (one developer or worktree per file)
git worktree add ../feed-bom-severe T080
git worktree add ../feed-bom-fire   T081
git worktree add ../feed-bom-flood  T082
# … etc. T080..T092
```

---

## Implementation Strategy

### MVP (Phase 1 + Phase 2 + Phase 3 only)

Delivers SC-002, SC-004, partial SC-001, SC-013 (seed-side). `azd up` on a clean subscription seeds idempotently with rejection of unmarked records. Demoable to compliance/audit reviewers immediately.

### Incremental delivery

1. Phase 1 + 2 → foundation.
2. Phase 3 (P1 seed) → MVP, demoable.
3. Phase 4 (P2 manifest + lints) → governance gate live; SC-001/SC-003/SC-007/SC-009/SC-011/SC-014/SC-015 verifiable.
4. Phase 5 (P3 simulator) → SC-005/SC-006 verifiable; live agents now exercisable end-to-end.
5. Phase 6 (P4 generators + demos) → 100% persona coverage; SC-008/SC-012/SC-013 fully met.
6. Phase 7 → final polish, walkthrough, regression guards.

### Parallel team strategy

After Phase 2 is green:

- Team A: Phase 3 (data authors)
- Team B: Phase 4 (governance lints + manifest)
- Team C: Phase 5 (simulator engineers)
- Team D: Phase 6 generators / demos (start when Phase 2 done; merge when Phase 5 feeds available)

---

## Verification Matrix — every FR / SC mapped to ≥1 task

### Functional Requirements

| FR | Tasks |
|---|---|
| FR-001 (Inventory) | T050 |
| FR-002 (Gap analysis) | T051 |
| FR-003 (Closure mechanism per gap) | T051 |
| FR-010 (Seed extensions) | T024, T025, T026, T027, T028, T029, T030, T031, T032 |
| FR-011 (Loader triggered by postprovision) | T032, T034 |
| FR-012 (Idempotent) | T020, T032 |
| FR-013 (Upsert by hash, no delete) | T020, T032 |
| FR-014 (Per-catalogue summary) | T020, T032 |
| FR-015 (Reject missing markers) | T021, T032, T165 |
| FR-016 (Static data not streamed) | T032, T058 (lint), T162 |
| FR-020 (Simulator feed shapes) | T080, T081, T082, T083, T084, T085, T086, T087, T088, T089, T090, T091, T092 |
| FR-021 (Mandatory envelope fields) | T013, T072, T080–T092 |
| FR-022 (Byte-identical replay) | T016, T070, T080–T093, T161 |
| FR-023 (No outbound calls) | T071 |
| FR-024 (Existing publish surface only; replay file mode) | T093, T094, T058 (import-linter) |
| FR-025 (Synthetic fallback) | T075, T092 |
| FR-026 (Concurrent clock isolation) | T016, T073 |
| FR-027 (Versioned shapes) | T017, T095 |
| FR-030 (Manifest + schema + render) | T010, T052, T053, T056, T166 |
| FR-031 (Required fields per entry) | T010, T011, T052, T060 |
| FR-032 (CI lint enumerates artefacts) | T040, T041, T053, T058 |
| FR-033 (Persona-coverage report) | T053, T057, T167 |
| FR-034 (SPDX licence + attribution string) | T059, T164 |
| FR-035 (Cross-reference corpus manifests) | T061 |
| FR-040 (Marker scopes a–d) | T014, T032, T040 (lint), T165 |
| FR-041 (Synthetic person names only) | T117 (gen test), T032 (loader reject) |
| FR-042 (AU residency in transit + at rest) | T060, T032 |
| FR-043 (PSPF cap OFFICIAL: SENSITIVE) | T012, T022, T060 |
| FR-044 (Indigenous two-layer enforcement) | T011 (schema cross-check), T018, T042, T043, T054 |
| FR-045 (PII detector) | T023, T033, T118 |
| FR-046 (TEST — DO NOT BROADCAST in body) | T074, T080 |
| FR-050 (Generators) | T110, T111, T112, T113, T114, T115, T116, T117, T118, T119, T120, T121, T122, T123 |
| FR-051 (Seed contract precedence) | T015, T100, T110–T123 |
| FR-052 (Generator id + version on every record) | T100, T110–T123 |
| FR-053 (Mock resources) | T053 (manifest categorises mocks), T018 (denylist categorised as mock), T160 |
| FR-054 (Mocks not in production paths) | T055, T058, T162 |
| FR-060 (≥1 artefact per persona) | T035, T140, T141, T142, T143, T144, T145, T146, T147, T167 |
| FR-061 (≥1 demo per domain group, ≥3 personas each) | T103, T130, T131, T132, T133, T134, T135, T136, T137 |
| FR-062 (Per-persona volume lower bounds) | T024, T026, T027, T084, T101, T119, T120, T121 |
| FR-070 (Multilingual + Indigenous + Auslan placeholder) | T024, T062, T150 |
| FR-071 (WCAG 2.1 AA) | T151 |

### Success Criteria

| SC | Tasks |
|---|---|
| SC-001 (100% persona coverage) | T035, T057, T104, T140–T147, T167 |
| SC-002 (100% loader marker enforcement) | T021, T022, T023, T032, T165 |
| SC-003 (100% manifest enumeration; CI fails on miss) | T040, T053, T058 |
| SC-004 (Idempotent re-run zero diff) | T020, T032 |
| SC-005 (Byte-identical replay) | T016, T070, T080–T093, T161 |
| SC-006 (Zero outbound calls) | T071 |
| SC-007 (Zero production imports of simulator) | T004, T044, T055, T058, T162 |
| SC-008 (≥1 demo per domain group, ≥3 personas) | T103, T130–T137, T167 |
| SC-009 (Public-dataset provenance complete) | T059 |
| SC-010 (First-time reviewer can enumerate in 30 min) | T160 |
| SC-011 (Zero pii / non-AU / over-classified) | T060 |
| SC-012 (Volume lower bounds met) | T101, T119, T120, T121 |
| SC-013 (Fresh `azd up` demo-ready) | T034, T160, T167 |
| SC-014 (Multilingual placeholder coverage) | T024, T062, T150 |
| SC-015 (Indigenous artefacts flagged) | T011, T043, T054 |

---

## Notes

- **No new Azure resources** are introduced; **no new GitHub Actions workflows** are introduced (CL-2, CL-7). Every CI gate is a new step in the existing `quality:` job in `.github/workflows/ci.yml` (T058).
- **No new HTTP endpoints**: the simulator publishes only via the existing `apps/api/app/services/simulation/event_hub_publisher.py` surface (FR-024, T093).
- **Two-Path Rule** is enforced by three independent layers: (1) `import-linter` contracts (T004, T058); (2) AST-string grep in `check_simulator_isolation.py` (T055); (3) manifest category↔path cross-check in `check_test_data_manifest.py` (T053).
- Every test invocation on Windows uses `pytest --basetemp=C:\tmp\pytest038 …` (T005, repo memory).
- Only one new Python dependency is introduced: `rfc8785` (T001). All other libraries are already in the lockfile.
- **Total task count: 117** (Phase 1: 5; Phase 2: 10; Phase 3 / P1: 16; Phase 4 / P2: 18; Phase 5 / P3: 22; Phase 6 / P4: 38; Phase 7: 8).
- **Parallel group count: 13 in-phase groups + 4 cross-phase opportunities = 17 parallel windows**.
- **FR coverage**: 41 / 41 enumerated functional requirements = **100%** (the spec uses banded numbering FR-001..003, 010..016, 020..027, 030..035, 040..046, 050..054, 060..062, 070..071 — every band is fully covered above). **SC coverage**: 15 / 15 = **100%**.



---

## Amendment Cycle 1 — Phase A (MANIFEST.md Freshness Gate)

**Driver**: Step-8 all-agents review OBJ-001 (MANIFEST.md reported 105 entries while manifest.json contained 134; CI did not enforce parity). Spec amended with **FR-036** (CI freshness gate), **SC-016** (per-PR freshness contract), **FR-031** refinement (CL-11 summary-view + CL-12 `domain_group`). Plan amended with Phase A (§A.1–A.8).

**Scope discipline**: Phase A adds **zero** new manifest entries, **zero** new Azure resources, **zero** new GitHub workflow files. The existing `quality:` job in `.github/workflows/ci.yml` gains exactly one new step. Touches FR-036 / SC-016 / FR-031 / CL-9 / CL-10 / CL-11 / CL-12 only.

**TDD posture**: A001–A003 land RED (failing tests); A004–A005 turn the contract sub-tests + naming-symmetry path GREEN; A006 wires CI; A007 regenerates `MANIFEST.md` and turns the integration test GREEN; A008 is the full verification sweep.

**Format**: same as the original tasks.md — `- [ ] [TaskID] [P?] [Story?] Description with file path — refs`. No `[Story]` label is used in Phase A (the freshness gate is shared infrastructure, not a user-story increment).

**Verification command shorthand** (same as the header of this file): `pytest038` = `pytest --basetemp=C:\tmp\pytest038 -q`; `lint-imports` = `lint-imports --config pyproject.toml`.

### Phase A Tasks (RED → GREEN → Verify)

- [X] A001 Author **failing contract test** `tests/contract/spec038/test_manifest_md_freshness_lint.py` covering all four sub-cases from plan §A.3: (a) **clean state** — when `manifest.json` and `MANIFEST.md` are in sync, `python tools/lint/check_manifest_md_fresh.py` exits `0` with no diff; (b) **drift state** — when `MANIFEST.md` is mutated (one row deleted, one column reordered, header text altered — three independent fixture variants), the lint exits non-zero AND prints both a unified `diff --unified` AND the exact remediation command `python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py`; (c) **missing-manifest skip (CL-10)** — when `docs/test-data/manifest.json` is absent (simulated via `tmp_path` fixture overriding the manifest path), the lint exits `0` AND writes a visible skip notice to stderr; (d) **CRLF tolerance** — when the committed `MANIFEST.md` is rewritten with `\r\n` line endings (simulating Windows `core.autocrlf=true`), the lint still exits `0` against an LF-rendered output. Use `pytest038`-compatible `tmp_path` and `monkeypatch` only — do NOT mutate the real `docs/test-data/MANIFEST.md`. Verify (expect FAIL pre-A004/A005): `pytest --basetemp=C:\tmp\pytest038 -q tests/contract/spec038/test_manifest_md_freshness_lint.py`. — FR-036, SC-016, CL-9, CL-10; satisfies CHK005, CHK006, CHK007, CHK010, CHK011, CHK013, CHK014, CHK015, CHK017, CHK018.

- [X] A002 Author **failing integration test** `tests/integration/test_manifest_md_committed_in_sync.py` that, against the **real** `docs/test-data/manifest.json` and `docs/test-data/MANIFEST.md` checked into the repo, invokes `tools/lint/render_test_data_manifest_md.py` programmatically (importing `render()`), normalises both buffers via `.replace(b"\r\n", b"\n")`, asserts byte-equality, AND asserts entry-count parity (count of `- ` rows in MANIFEST.md per category equals `len(entries)` per category in `manifest.json`). This is the OBJ-001 root-cause regression test (105 vs 134). No `tmp_path` — touches the real artefacts (read-only). Verify (expect FAIL pre-A007 because the committed MANIFEST.md is at 105 entries while manifest.json is at 134): `pytest --basetemp=C:\tmp\pytest038 -q tests/integration/test_manifest_md_committed_in_sync.py`. — FR-036, SC-016, CL-9; satisfies CHK016 (failure taxonomy: entry-count mismatch). Closes OBJ-001 root cause.

- [X] A003 Author **failing unit-determinism test** `tests/unit/spec038/test_renderer_determinism.py` containing (i) a **fixed in-memory manifest fixture** with 4 entries spanning 3 categories (covering sort-key edge cases: same category different ids, same id-prefix different categories), (ii) an assertion that two back-to-back invocations of `render(fixture)` produce **byte-identical** output, (iii) an assertion that `sha256(render(fixture)).hexdigest()` equals a **committed golden hash** (compute the expected hash once from the current renderer and embed it as a module constant `GOLDEN_SHA256 = "<64-hex>"`), (iv) explicit assertions that the output (a) ends with a single LF (`output.endswith(b"\n") and not output.endswith(b"\n\n")`), (b) contains no `\r` bytes, (c) decodes cleanly as UTF-8, (d) emits exactly the 7 columns named in CL-11 (`id`, `path`/`source_shape`, `domain_group`, `persona_bindings`, `pspf`, `licence`, `cultural_review_required`) per category. Any future change to the renderer's sort key, header text, column set, spacing, or trailing-newline policy MUST force an update to BOTH this golden hash AND FR-036 in the same PR. Verify (expect FAIL until A004 lands and the golden hash is computed): `pytest --basetemp=C:\tmp\pytest038 -q tests/unit/spec038/test_renderer_determinism.py`. — FR-036, FR-031, CL-11, CL-12; satisfies CHK001, CHK002, CHK003, CHK004, CHK019, CHK020, CHK021.

- [X] A004 Add **`--check` flag** to `tools/lint/render_test_data_manifest_md.py`: extend `argparse` with `--check` (mutually exclusive with the default re-write behaviour); when `--check` is set, the `main()` function MUST (1) load `docs/test-data/manifest.json` (configurable via `--manifest`, default `docs/test-data/manifest.json`); (2) if the manifest file does not exist, print `[skip] docs/test-data/manifest.json not present — freshness gate N/A on this branch (CL-10)` to **stderr** and `sys.exit(0)`; (3) otherwise call `render(doc)` to produce LF-only UTF-8 bytes; (4) read the committed `docs/test-data/MANIFEST.md` as bytes and apply `.replace(b"\r\n", b"\n")`; (5) byte-compare; (6) on equal, `sys.exit(0)` silently; (7) on diverge, print a `difflib.unified_diff` truncated to a sensible budget (default 200 lines; settable via `--max-diff-lines`) AND on the final stderr line print the exact remediation command `python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py`, then `sys.exit(1)`. Implementation MUST use only stdlib (`argparse`, `json`, `difflib`, `pathlib`, `hashlib`, `sys`) — no new third-party dependency (Constitution Principle VII). Verify: `pytest --basetemp=C:\tmp\pytest038 -q tests/contract/spec038/test_manifest_md_freshness_lint.py tests/unit/spec038/test_renderer_determinism.py` — A001 sub-cases (a)/(b)/(c)/(d) and A003 all turn GREEN. — FR-036, SC-016, CL-9, CL-10; satisfies CHK008 (still required at the wrapper layer for A006), CHK010, CHK011, CHK012, CHK013, CHK014, CHK017, CHK018.

- [X] A005 Add **thin wrapper script** `tools/lint/check_manifest_md_fresh.py` whose entire body is `from tools.lint.render_test_data_manifest_md import main; import sys; sys.exit(main(["--check", *sys.argv[1:]]))` (or equivalent — a single dispatch into the renderer's `main()` with `--check` injected, no parallel implementation, no duplicated logic). The wrapper exists solely so the CI step name and the local invocation match the FR-036 / CL-9 naming convention (`check_manifest_md_fresh.py`). Add a 1-line module docstring referencing FR-036 and pointing to the renderer for the actual logic. Verify: `python tools/lint/check_manifest_md_fresh.py` exits `0` against the (still drifted) repo state ONLY in its skip path; against the real (post-A007) state it exits `0` cleanly; `pytest --basetemp=C:\tmp\pytest038 -q tests/contract/spec038/test_manifest_md_freshness_lint.py` — naming-symmetry assertions GREEN. — FR-036, CL-9; satisfies CHK008 (wrapper is the script CI invokes by name).

- [X] A006 Wire the freshness gate into CI: add **exactly one new step** named `manifest-md-freshness-lint` to the existing `quality:` job in `.github/workflows/ci.yml`, positioned **immediately after the `simulator-isolation-lint` step** (per plan §A.7). Step body: `run: python tools/lint/check_manifest_md_fresh.py`. **No new workflow file** (FR-036 explicit prohibition; CL-9 confirmation; Constitution Principle VIII). Verify locally with `actionlint .github/workflows/ci.yml` (if installed) and by visual inspection that (a) no new top-level workflow file appeared (`Get-ChildItem .github/workflows/*.yml | Measure-Object` count unchanged); (b) the new step is inside the `quality:` job; (c) it follows `simulator-isolation-lint`. — FR-036, SC-016, CL-9; satisfies CHK008, CHK009.

- [X] A007 **Regenerate `docs/test-data/MANIFEST.md` and commit** — run `python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py` from the repo root to bring the rendered Markdown back into sync with the existing 134-entry `manifest.json` (closes the OBJ-001 root-cause drift, 105 → 134 entries). This task adds **zero new manifest entries** (per plan §A.6 — F-004 enumeration is unchanged); it only re-renders the existing JSON source of truth into the executive-summary view. Stage and commit the regenerated `docs/test-data/MANIFEST.md` (and only that file — the build script is idempotent against an already-current `manifest.json`). Verify: (a) `git diff --stat docs/test-data/MANIFEST.md` shows the expected churn; (b) `pytest --basetemp=C:\tmp\pytest038 -q tests/integration/test_manifest_md_committed_in_sync.py` — A002 turns GREEN; (c) `python tools/lint/check_manifest_md_fresh.py` exits `0`. — FR-036, SC-016, FR-031, CL-11, CL-12; satisfies CHK016, CHK019, CHK020, CHK021. Closes OBJ-001.

- [X] A008 **Full Phase-A verification sweep** — run the complete cross-cutting verification before declaring Amendment Cycle 1 closed: (1) `pytest --basetemp=C:\tmp\pytest038 -q tests/contract/spec038 tests/integration/test_manifest_md_committed_in_sync.py tests/unit/spec038` — all Phase-A tests GREEN; (2) `python tools/lint/check_test_data_manifest.py && python tools/lint/check_simulator_isolation.py && python tools/lint/check_indigenous_placeholders.py && python tools/lint/check_manifest_md_fresh.py` — full lint sweep exits `0`; (3) `lint-imports --config pyproject.toml --no-cache` — import-linter contracts still GREEN; (4) execute the spec-038 verification harness from `specs/038-test-data-provisioning/verification.md` end-to-end; (5) confirm `Get-ChildItem .github/workflows/*.yml` count unchanged from pre-amendment baseline (no new workflow file); (6) confirm `git diff --stat HEAD~N -- docs/test-data/manifest.json` shows **zero** changes to the manifest itself (only `MANIFEST.md` re-rendered); (7) re-tick all 21 boxes in `specs/038-test-data-provisioning/checklists/manifest-md-freshness.md` (CHK001–CHK021) confirming each is satisfied by an A00x task. Verify: paste the seven command outputs into the PR description. — FR-036, SC-016, FR-031, CL-9, CL-10, CL-11, CL-12; satisfies CHK001–CHK021 (omnibus).

### Phase A Dependency Graph

```text
A001 ─┐
A002 ─┼── (RED, parallel-safe in principle but kept linear for review clarity)
A003 ─┘
        ↓
A004 ── (turns A001 sub-cases a/b/c/d + A003 GREEN)
        ↓
A005 ── (turns A001 naming-symmetry path GREEN; depends on A004's main())
        ↓
A006 ── (CI wiring; depends on A005 existing as the named entry point)
        ↓
A007 ── (turns A002 GREEN by re-rendering 105→134 entries; depends on A004's --check being available so the integration test can compare correctly)
        ↓
A008 ── (omnibus verification; depends on A001–A007)
```

**Parallelism**: None marked `[P]` — Phase A is intentionally a small linear sequence (8 tasks, single contributor, single PR). A001/A002/A003 could in principle be authored in parallel (different test files), but keeping them sequential preserves a clean RED commit history that auditors can replay one test at a time.

### Phase A Verification Matrix

| Spec ref / Checklist item | Satisfied by task(s) |
|---|---|
| **FR-036** (freshness gate, byte/LF/UTF-8 diff, remediation contract, CI step inside `quality:`) | A001, A002, A003, A004, A005, A006, A007, A008 |
| **SC-016** (100% PR enforcement, exit codes, skip-on-missing-manifest, entry-count parity at every commit) | A001, A002, A004, A005, A006, A007, A008 |
| **FR-031** (refined: 7-column summary-view enumeration + `domain_group`) | A003, A007, A008 |
| **CL-9** (CI freshness gate, no new workflow files, `quality:` job step) | A001, A005, A006, A008 |
| **CL-10** (byte-exact + LF/UTF-8 normalisation, CRLF tolerance, unified diff, remediation command, N/A skip with stderr notice) | A001, A004, A008 |
| **CL-11** (MANIFEST.md is intentional summary view; 7-column subset; manifest.json is authoritative) | A003, A007, A008 |
| **CL-12** (`domain_group` added to FR-031 enumerated field list; cross-ref to PersonaBinding taxonomy) | A003, A007, A008 |
| CHK001 (sort key `(category, id)` named as part of locked contract) | A003 |
| CHK002 (LF terminator named as part of locked contract) | A003 |
| CHK003 (UTF-8 named as part of locked contract) | A003 |
| CHK004 (renderer-contract change forces FR-036 update) | A003 (golden-hash mechanism), A008 |
| CHK005 (success exit code `0`) | A001, A004 |
| CHK006 (divergence exit non-zero) | A001, A004 |
| CHK007 (N/A skip exits `0`) | A001, A004 |
| CHK008 (lint runs as step inside existing `quality:` job) | A005, A006 |
| CHK009 (no new GitHub workflow file) | A006, A008 |
| CHK010 (unified diff on failure) | A001, A004 |
| CHK011 (exact remediation command on failure) | A001, A004 |
| CHK012 (sensible-line-budget truncation) | A004 (`--max-diff-lines`) |
| CHK013 (byte-exact comparison method) | A001, A004 |
| CHK014 (`\r\n`→`\n` applied to both sides) | A001, A004 |
| CHK015 (Windows `core.autocrlf=true` motivating case preserved) | A001 (CRLF fixture sub-case d), A004 |
| CHK016 (failure taxonomy: entry-count / missing-rows / field drift / ordering / formatting) | A001 (drift fixtures), A002 (entry-count), A008 |
| CHK017 (N/A skip condition: `manifest.json` does not yet exist) | A001 (sub-case c), A004 |
| CHK018 (visible skip notice on stderr, not silent success) | A001 (sub-case c), A004 |
| CHK019 (MANIFEST.md is intentional summary view; `manifest.json` is authoritative) | A003, A007 |
| CHK020 (FR-031 enumerates 7-column subset surfaced by renderer) | A003, A007 |
| CHK021 (`domain_group` added to FR-031 with cross-ref to PersonaBinding) | A003, A007 |

### Phase A Summary

- **Total Phase-A task count: 8** (A001, A002, A003, A004, A005, A006, A007, A008)
- **Parallel tasks**: 0 (intentional — small linear RED → GREEN → Verify sequence in a single PR)
- **New files created**: 4 (`tests/contract/spec038/test_manifest_md_freshness_lint.py`, `tests/integration/test_manifest_md_committed_in_sync.py`, `tests/unit/spec038/test_renderer_determinism.py`, `tools/lint/check_manifest_md_fresh.py`)
- **Files modified**: 3 (`tools/lint/render_test_data_manifest_md.py` — `--check` flag; `.github/workflows/ci.yml` — one new step in existing `quality:` job; `docs/test-data/MANIFEST.md` — regenerated 105 → 134 entries)
- **Files NOT touched**: `docs/test-data/manifest.json` (zero new entries; OBJ-001 was a renderer-freshness gap, not a manifest-content gap), `docs/test-data/manifest.schema.json`, any other workflow file, any infra file, any Bicep/Terraform.
- **Spec FR coverage delta**: +1 (FR-036). **Spec SC coverage delta**: +1 (SC-016). **FR-031** refined (CL-11 summary-view clause + CL-12 `domain_group`). **Checklist (manifest-md-freshness.md) coverage**: 21/21 = 100%.
- **Constitution check**: Principles I–V unaffected; VI (TDD) honoured (A001–A003 land RED before A004–A005); VII (no new external deps) honoured (stdlib only); VIII (additive infra only — no new workflow / no new Azure resource) honoured.

### Phase A Implementation Strategy

1. **One PR for Phase A.** All 8 tasks land together — Phase A is too small to split and the RED/GREEN ordering is most auditable when reviewed as a single commit history (one commit per task, 8 commits total).
2. **MVP ordering**: A001 → A002 → A003 (RED) → A004 (most contract sub-tests GREEN) → A005 (naming GREEN) → A006 (CI wired) → A007 (integration GREEN; OBJ-001 closed) → A008 (omnibus verification).
3. **Rollback safety**: each step is independently revertible. A007 in particular is a pure re-render — if a downstream consumer of `MANIFEST.md` regresses, `git revert` on the A007 commit alone restores the prior text.

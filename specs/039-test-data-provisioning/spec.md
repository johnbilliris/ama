# Feature Specification: Test Data and Resources Provisioning Review

**Feature Branch**: `039-test-data-provisioning`
**Created**: 2026-05-11
**Status**: Draft
**Input**: User description: "Test Data and Resources Provisioning Review — comprehensive review of the AMA solution to ensure that test data and/or resources have been provided wherever feasible (synthetic datasets, public datasets, data generators, mock resources), and to fill any gaps via a single coherent feature. Honour the Two-Path Rule: static reference data goes through the seed loader (`scripts/seed_loader.py` + `packages/domain/src/domain/seed/`) and is loaded by `azd postprovision`; live-stream / external-feed data lives ONLY under the Simulation functionality (`apps/api/app/services/simulation/`) and never touches live-production code paths or real external services."

---

## Background and Scope Summary

The Autonomous Disaster Response Coordination Hub (AMA) must be reliably testable, demonstrable, and reproducible end-to-end without ever touching real Bureau of Meteorology (BoM), Geoscience Australia (GA), Australian Bureau of Statistics (ABS), Australasian Fire and Emergency Service Authorities Council (AFAC), or jurisdictional production endpoints, and without exposing real personal information (PII), Protective Security Policy Framework (PSPF) marked content, or culturally sensitive Indigenous community references.

This feature delivers an **inventory, gap closure plan, and governance regime** for all test data and resources required by the platform, covering:

- **Synthetic datasets** (locally generated, deterministic seeds, no real PII).
- **Public datasets** (Australian government open data: BoM open data, GA Earthquake Catalogue, ABS, AURIN, OpenStreetMap, AIDR — used under their stated open-data licences).
- **Data generators** (code-based factories that produce on-demand sample inputs, Faker-style).
- **Mock resources** (in-memory fakes, recorded HTTP cassettes, Azurite/Cosmos emulator fixtures, MSAL mock tenants, WireMock-style HTTP doubles).

It is scoped to the needs of all 68 actor personas (10 operational + 33 state/territory sector + 11 commonwealth + 8 cross-sector + 6 NSW already enumerated) and enforces a single non-negotiable design rule (the **Two-Path Rule**) and a uniform compliance regime (PII-free, PSPF OFFICIAL by default, Australia-resident, fictitious-labelled, licence-attested).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inventoried, Gap-Closed Seed Catalogue Loaded Idempotently by `azd postprovision` (Priority: P1)

A platform engineer runs `azd up` (or `azd provision` followed by the existing `postprovision` hook) against a fresh subscription. The seed loader executes once, loads every static reference dataset that the 68 personas require — jurisdictions, organisations, operating frameworks, hazard taxonomies, AIIMS function map, coordination tasks, recovery catalogues, identity/RBAC seeds, multilingual alert templates, evacuation route catalogues, vulnerable-person category catalogues, hospital-capability flags, utility/transport/road-segment catalogues, scenario templates — into the persistence layer. Re-running `azd postprovision` produces the identical state without duplicates, divergence, or errors.

**Why this priority**: Without a complete and idempotent seed catalogue, no agent, dashboard, evaluation run, or demo can execute. This story is the minimum viable foundation: it makes the platform demonstrable for every persona on a fresh environment.

**Independent Test**: Provision a clean environment, run `azd up`, and assert that (a) every persona has at least one named seed record bound to it, (b) re-running the postprovision hook leaves record counts and content hashes unchanged, and (c) every seeded record carries a fictitious-data marker, an Australian-residency attestation, and a licence reference.

**Acceptance Scenarios**:

1. **Given** a freshly provisioned environment with no prior data, **When** `azd postprovision` runs, **Then** the seed loader populates all reference catalogues (jurisdictions, organisations, frameworks, hazard taxonomies, recovery catalogues, identities, alert templates, scenario templates, route catalogues, persona binding records) and each loaded record is tagged `fictitious=true`, `residency=AU`, and references a licence record.
2. **Given** an environment that has already been seeded once, **When** `azd postprovision` is re-run, **Then** no duplicate records are created, content hashes for each catalogue match the prior run, and the loader exits with a success status that explicitly reports "0 inserts, 0 updates, N already-current" for each catalogue.
3. **Given** the seeded environment, **When** an auditor queries the persona-to-data binding view, **Then** every one of the 68 personas resolves to ≥1 seed record (organisation, operating framework, resource catalogue entry, or persona-bound scenario) and zero personas appear in an "unbacked" report.
4. **Given** a deliberately corrupted seed file (missing licence field), **When** the seed loader runs, **Then** the loader rejects the file with a clear error citing the missing compliance field and does not partially load the catalogue.

---

### User Story 2 - Deterministic Simulator Feeds for Every Live-Stream Need, Isolated From Production Code Paths (Priority: P2)

A demonstrator or evaluator selects a named scenario (e.g. "NSW bushfire — Black Summer-shaped progression", "QLD Category 4 cyclone — Far North coastal", "VIC riverine flood — multi-LGA"), supplies a numeric seed, and starts the Simulation functionality. The simulator emits, for the duration of the scenario, **BoM-shaped severe weather warnings, GA-shaped earthquake events, BoM-shaped flood gauge rises and cyclone tracks, fire weather/FDI updates, EPA-shaped PM2.5 air-quality signals, traffic/road-closure events, utility outage events, ambulance computer-aided-dispatch (CAD) events, social-media chatter with misinformation markers, and sensor telemetry**, each labelled `SIMULATED`, each fully reproducible given the same scenario+seed pair, and each routed exclusively through the existing simulator code under `apps/api/app/services/simulation/`. No production code path may import from the simulator package, and no simulator code path may call a real BoM/GA/ABS/EPA endpoint.

**Why this priority**: The platform's value proposition is real-time multi-source coordination. Without deterministic, isolated, externally-shaped feeds, the agents cannot be exercised end-to-end and demos cannot be reproduced. This story unlocks the live behaviour but depends on the seed catalogue (US1) for entity identifiers.

**Independent Test**: Run the same named scenario twice with the same seed, capture every emitted feed message, and assert byte-identical sequences (modulo wall-clock timestamps which must be replaced by simulated-clock timestamps) and no outbound network calls to any real-world domain.

**Acceptance Scenarios**:

1. **Given** a named scenario and a numeric seed, **When** the simulator runs to completion, **Then** the emitted message sequence on every feed (BoM weather, GA earthquake, fire weather, road status, utility outage, ambulance CAD, social media, sensor telemetry, PM2.5 air quality) is byte-identical to a prior run with the same scenario+seed, after normalising simulated-clock timestamps.
2. **Given** an active simulation, **When** any emitted message is inspected, **Then** it carries a top-level `simulated: true` marker, a `scenario_id` field, a `seed` field, and a `source_shape` field naming the public dataset whose schema it imitates (e.g. `bom.severe_weather_warning.v1`).
3. **Given** the running simulator, **When** outbound network traffic is observed, **Then** zero requests are made to `*.bom.gov.au`, `*.ga.gov.au`, `*.abs.gov.au`, `*.aurin.org.au`, or any other real external dataset host.
4. **Given** a static analysis of the production code paths (every module outside `apps/api/app/services/simulation/` and its declared sub-packages), **When** import dependencies are inspected, **Then** zero production modules import from the simulator package, and the simulator package exposes no symbols to dependency-injection registries used by production agents.
5. **Given** a jurisdiction with no real public dataset (e.g. a remote NT regional zone), **When** a scenario targets that jurisdiction, **Then** the simulator still emits a deterministic, plausibly-shaped feed using the documented fallback shape and labels it `source_shape: synthetic.fallback.v1`.

---

### User Story 3 - Versioned Test-Data Manifest with Provenance, Licence, PII, PSPF, and Residency Attestation for Every Artefact (Priority: P3)

A compliance reviewer, an evaluator, or an external auditor opens the **Test-Data Manifest** (a single, versioned, machine-readable + human-readable document at `docs/test-data/MANIFEST.md` plus a structured companion file) and finds, for every test-data artefact in the repository (synthetic dataset, public-dataset snapshot, generator, mock resource, simulator feed shape, alert template, persona binding):

- a stable identifier and human-readable name;
- the artefact's category (synthetic / public / generator / mock / simulator-feed-shape);
- the source URL (for public datasets), snapshot date, dataset version, and SPDX-compatible licence identifier;
- a fictitious-data attestation, a "no real PII" attestation, a PSPF marking (`OFFICIAL` by default, `OFFICIAL: SENSITIVE` only where called out), and an Australian-residency attestation;
- the persona(s) and user story (or simulator scenario) the artefact serves;
- the refresh policy (e.g. `static`, `refresh-on-public-dataset-update`, `regenerate-each-run`);
- a content hash for change detection.

**Why this priority**: Without a single source of truth, gap analysis is unverifiable, audit reviews require manual code archaeology, and licence attribution risks lapse. The manifest is what makes US1 and US2 governable and what makes ongoing additions traceable.

**Independent Test**: A reviewer who has never seen the codebase can, using only the manifest, list every test artefact, its provenance, its licence, and which persona it serves; and a CI check can verify that every file under the seed catalogue, the simulator data directories, the generator modules, and the public-data corpus is enumerated in the manifest with non-empty values for every required field.

**Acceptance Scenarios**:

1. **Given** the repository at any commit on `main` after this feature ships, **When** the manifest validation check runs, **Then** every test-data artefact in the catalogued directories is present in the manifest, every required field is non-empty, and the check passes; and every artefact in the manifest resolves to a real file or simulator feed shape.
2. **Given** the manifest, **When** a reviewer filters by `category=public`, **Then** every entry has a non-empty `source_url`, `snapshot_date`, `dataset_version`, and SPDX licence identifier.
3. **Given** the manifest, **When** a reviewer filters by `pii=true`, **Then** the result set is empty.
4. **Given** the manifest, **When** a reviewer filters by `residency≠AU`, **Then** the result set is empty.
5. **Given** the manifest, **When** the persona-coverage report is generated, **Then** each of the 68 personas appears with ≥1 manifest entry naming it.

---

### User Story 4 - Per-Persona, Per-Domain Gap-Filled Datasets and Generators (Priority: P3)

For every operational, fire, police, ambulance, SES/SES-equivalent, marine/aviation, commonwealth, and cross-sector persona, the platform exposes either (a) a named seed-catalogue entry, (b) a named generator producing on-demand records, (c) a named mock resource, or (d) a named simulator feed shape — covering the persona's "Key test data" needs as captured in the consolidated persona input report. No persona is left without representation, and the per-persona data volumes meet or exceed the lower bound of the persona's recommended volume guide.

**Why this priority**: The audit-grade promise of the platform is that every actor is exercisable. Without per-persona coverage, an entire sector (e.g. NT remote response, surf life saving, RFDS aeromedical retrieval) could remain silently untested.

**Independent Test**: Run the persona-coverage report and assert (a) ≥1 artefact per persona, (b) artefact volumes meet lower bounds, and (c) for each domain group (ops, fire, police, ambulance, SES, marine/aviation, commonwealth, cross-sector) at least one end-to-end demo scenario exists that exercises ≥3 personas in that group.

**Acceptance Scenarios**:

1. **Given** the persona-coverage report, **When** filtered by domain group, **Then** every group reports ≥1 demo scenario that exercises ≥3 of its personas.
2. **Given** a generator module, **When** invoked with a fixed seed, **Then** it produces the same record set on every invocation, and every produced record carries `fictitious=true`.
3. **Given** the seed catalogue extensions, **When** loaded, **Then** record counts per persona category meet or exceed the persona-specific lower bounds (e.g. ≥10 mock hospital capacity records, ≥20 synthetic vulnerable-persons category entries with no PII, ≥30 synthetic volunteer registration records, ≥5 multilingual alert variants per supported language).

---

### Edge Cases

- **Re-seeding without duplicates**: Re-running the seed loader against an environment with partial existing data must converge to the canonical state (idempotent upsert keyed by stable artefact IDs); records that no longer exist in the catalogue must NOT be deleted automatically (loader is upsert-only, deletions are out of scope).
- **Simulator feed for a jurisdiction with no real public dataset**: The simulator must fall back to a documented synthetic shape labelled `source_shape: synthetic.fallback.v1`, NOT silently skip the jurisdiction and NOT fabricate a fake BoM/GA shape.
- **Multilingual content for low-resource locales**: Where canned multilingual content is not available for a target locale (e.g. Pitjantjatjara, Auslan transcripts), the alert template entry must explicitly carry a `placeholder=true` flag and the manifest must record a "needs cultural-authority review" note; the loader must accept and label these placeholders, not reject them.
- **Indigenous cultural data placeholder handling**: No real Traditional Owner names, real sacred-site coordinates, or real community names may appear in any artefact. Where Indigenous-community context is required, artefacts use anonymised regional zones (e.g. "NT Central Desert regional zone — placeholder") and carry a `cultural-review-required=true` flag.
- **Large-volume load fixtures**: The seed loader and generators MUST support four named volume tiers — `small=10`, `medium=100`, `large=1,000`, `xlarge=10,000` records per catalogue/feed — aligned with `specs/015-performance-benchmarks`. Tiers `small`/`medium`/`large` MAY be committed to the repository as static fixtures; `xlarge` (and any volume above it) MUST NOT be committed and MUST instead be produced on demand by a deterministic generator script that streams records (no in-memory materialisation of the full set) in a deterministic order given a seed. [Resolved by CL-3]
- **Public-dataset snapshot drift**: When a public dataset is refreshed (BoM, GA, ABS), the manifest's `snapshot_date` must be updatable without code changes, and the system must not break if a snapshot is older than the recorded `snapshot_date` (warn, do not fail).
- **PII leakage attempt**: If any seed record or generator output contains a value matching documented real-PII detectors (real Australian phone number patterns linked to real exchanges, real residential addresses, real personal email addresses), the loader/generator must reject the record at load/generation time with an explicit error.
- **PSPF over-classification attempt**: Any seed record carrying a marking above `OFFICIAL: SENSITIVE` (e.g. `PROTECTED`, `SECRET`) must be rejected by the loader.
- **Simulator clock collision**: When two scenarios run concurrently in the same environment, each must use a distinct simulated-clock namespace so emitted timestamps cannot collide; deterministic reproducibility is preserved per scenario+seed pair.
- **Cross-jurisdictional resource sharing**: A scenario that triggers a cross-state resource request must produce coherent records on both sides (e.g. NSW request + VIC fulfilment) without requiring two separate seed loads.
- **Manifest renderer skipped or forgotten**: A contributor updates `docs/test-data/manifest.json` (or runs the build script that updates it) but forgets — or the renderer fails — to regenerate `docs/test-data/MANIFEST.md`. The Markdown then drifts from the JSON source of truth and external auditors relying on the rendered document form an incorrect picture of the test corpus. SC-016 / FR-036 ensures CI catches this divergence on every PR before merge by re-running the renderer and byte-diffing (LF-normalised, UTF-8) against the committed Markdown; the lint prints the exact remediation command (`python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py`) on failure so the contributor can fix it without consulting the spec.

---

## Requirements *(mandatory)*

### Functional Requirements

#### A. Inventory and Gap Analysis

- **FR-001**: System MUST publish, as an artefact under `docs/test-data/`, an **inventory** of every existing test-data asset in the repository at the time this feature ships, classified into one of {synthetic dataset, public dataset, generator, mock resource, simulator feed shape, alert template, persona binding} and bound to one or more of the 68 personas.
- **FR-002**: System MUST publish, alongside the inventory, a **gap analysis** that lists, per persona and per domain group (operational, fire, police, ambulance, SES, marine/aviation, commonwealth, cross-sector), the test-data artefacts still required to satisfy the persona's documented needs.
- **FR-003**: The gap analysis MUST identify, for each gap, the closure mechanism (seed-catalogue extension, new generator, new mock resource, or new simulator feed shape) and the artefact's persona binding(s).

#### B. Seed Catalogue Extensions (Static Reference Data — Path 1)

- **FR-010**: System MUST extend the existing seed catalogue under `packages/domain/src/domain/seed/` to cover, at minimum, every static reference dataset enumerated in the persona input report's "Summary Classification Table — Seed" column, including but not limited to: organisation records for all 68 entities, jurisdiction definitions for all 9 jurisdictions plus commonwealth, OperatingFramework definitions per organisation, hazard taxonomies, AIIMS function map extensions, coordination task templates, recovery catalogues (overarching, social, economic, built, natural, evaluation questions), identity/RBAC seed entries, multilingual alert templates, evacuation route catalogues, scenario templates, vulnerable-person category catalogues (category-only, no PII), hospital capability flag catalogues, road-segment catalogues, utility infrastructure catalogues (generic, no real identifiers), volunteer skill/credential category catalogues, LEMP/MEMP record templates, and inter-government agreement templates.
- **FR-011**: All seed-catalogue records MUST be loaded by the existing `scripts/seed_loader.py` and MUST be triggered by the existing `azd postprovision` hook with no manual intervention.
- **FR-012**: The seed loader MUST be **idempotent**: re-running it converges to the same state without duplicate records, regardless of how many times it is invoked.
- **FR-013**: The seed loader MUST detect record changes via stable artefact identifiers and content hashes and MUST upsert (insert-or-update); it MUST NOT delete records absent from the catalogue (deletion is out of scope).
- **FR-014**: The seed loader MUST emit, on completion, a per-catalogue summary of inserts, updates, and already-current records.
- **FR-015**: The seed loader MUST reject any record missing a fictitious-data marker, a residency attestation, or a licence reference; rejection MUST be explicit and MUST NOT silently skip the record.
- **FR-016**: Static reference data MUST NOT be emitted as a runtime stream; if a dataset must be streamed during a scenario it belongs under the simulator (FR-020+), not under the seed loader.

#### C. Simulator Feed Extensions (Live-Stream / External-Feed Data — Path 2)

- **FR-020**: System MUST extend the existing simulator under `apps/api/app/services/simulation/` to emit deterministic, externally-shaped feeds for: BoM-shaped severe weather warnings; BoM-shaped fire weather / Fire Danger Index updates; BoM-shaped flood gauge / flood watch / flood warning updates; BoM-shaped tropical cyclone track updates; GA-shaped earthquake event notifications; GA-shaped tsunami threat assessment relays; EPA-shaped PM2.5 / air-quality readings; traffic and road-closure status updates; utility outage event streams (electricity, gas, water, telecoms); ambulance computer-aided-dispatch (CAD) events; social-media chatter signals with misinformation markers; sensor telemetry (water level, wind, temperature).
- **FR-021**: Every simulator-emitted message MUST carry, at minimum: `simulated: true`, a `scenario_id`, the originating numeric `seed`, a `source_shape` identifier naming the public dataset whose schema it imitates (e.g. `bom.severe_weather_warning.v1`), a simulated-clock `timestamp`, and a `feed_version`.
- **FR-022**: Given identical `scenario_id` + `seed` inputs, the simulator MUST produce a byte-identical message sequence per feed. "Byte-identical" is defined as: (a) records emitted in the same total order; (b) each record serialised as **canonical JSON** (UTF-8, RFC 8259, lexicographically sorted object keys, no insignificant whitespace, numeric values rendered in shortest round-trip form, `\n` line terminator); (c) one record per line in NDJSON form; (d) `timestamp` fields populated from the deterministic simulated clock (ISO-8601 UTC, microsecond precision, derived from `scenario_id`+`seed`+ordinal — not wall-clock); (e) any non-deterministic correlation IDs derived from a seeded HMAC of `(scenario_id, seed, ordinal)`. Verification is a SHA-256 digest of the concatenated canonical NDJSON stream per feed; equal digests across runs constitute "byte-identical replay". [Resolved by CL-4]
- **FR-023**: The simulator MUST NOT make outbound network calls to any real BoM, GA, ABS, AURIN, EPA, OpenStreetMap, or jurisdictional production endpoint; all shape data is derived from cached, licence-attested public-dataset snapshots stored locally and recorded in the manifest, OR is fully synthetic.
- **FR-024**: Simulator code MUST NOT be importable from any production code path. Production agents MUST receive simulator-emitted messages only through the **existing in-process Event Hub / Service Bus publish surface already used by `apps/api/app/services/simulation/event_hub_publisher.py`** (the same channel production agents subscribe to for real-source ingestion); selecting simulator-on vs simulator-off is a runtime configuration concern, not a code-path concern. NO new public HTTP endpoints and NO new Azure resources are introduced by this feature solely for simulator delivery. A deterministic file-based replay mode (newline-delimited JSON under `fixtures/sim_replays/<scenario>.ndjson`) MUST additionally be supported for offline/CI tests that cannot run the in-process publisher. [Resolved by CL-2]
- **FR-025**: For any jurisdiction or hazard type with no available public-dataset shape, the simulator MUST emit a documented fallback shape labelled `source_shape: synthetic.fallback.v1` rather than fabricating a shape attributed to a real public dataset.
- **FR-026**: Concurrent scenario runs MUST use isolated simulated-clock namespaces so emitted timestamps cannot collide between scenarios.
- **FR-027**: Simulator feed shapes MUST be versioned; a breaking change to a shape requires a new `source_shape` version identifier and a manifest entry for the new version.

#### D. Test-Data Manifest, Provenance, and Licence Records

- **FR-030**: System MUST publish a **versioned test-data manifest** at `docs/test-data/MANIFEST.md` (human-readable, auto-rendered) accompanied by a single canonical machine-readable companion at `docs/test-data/manifest.json` (JSON; one entry per test-data artefact) that enumerates 100% of test-data artefacts in the repository. The structured companion MUST be validated against a JSON Schema at `docs/test-data/manifest.schema.json` by a CI check, mirroring the established pattern used for `docs/corpus/INDEXING-LICENCE-INVENTORY.md` (which is generated from per-source `source.json` sidecars). [Resolved by CL-1]
- **FR-031**: Every manifest entry MUST carry: stable `id`, human-readable `name`, `category` ∈ {synthetic, public, generator, mock, simulator-feed-shape, alert-template, persona-binding}, `domain_group` (mirrors the PersonaBinding `domain_group` taxonomy; required by `docs/test-data/manifest.schema.json` and surfaced in the rendered MANIFEST.md table), `path` (or `source_shape` for simulator feeds), `persona_bindings` (≥1), `fictitious=true`, `pii=false`, `pspf` marking (default `OFFICIAL`), `residency=AU`, `licence` (SPDX identifier or `proprietary-fictitious-internal`), `source_url` (for public datasets, otherwise `n/a`), `snapshot_date` (for public datasets), `dataset_version` (for public datasets), `refresh_policy` ∈ {static, refresh-on-public-dataset-update, regenerate-each-run}, `content_hash`, and `created_or_updated` date. The companion JSON entry is the authoritative carrier of every field; the rendered `MANIFEST.md` is an executive summary view that surfaces a deterministic subset (`id`, `path`/`source_shape`, `domain_group`, `persona_bindings`, `pspf`, `licence`, `cultural_review_required`) per the renderer contract locked in by FR-036 — auditors needing the full field set MUST consult `manifest.json`. [Refined by CL-11, CL-12]
- **FR-032**: System MUST provide a continuous-integration check that fails if any test-data artefact in the catalogued directories is missing from the manifest, if any required field is empty, or if any manifest entry references a non-existent artefact. The check is implemented as `tools/lint/check_test_data_manifest.py` (mirroring `tools/lint/check_licence_inventory.py`) and MUST be wired as a step into the **existing `quality` job in `.github/workflows/ci.yml`** (no new workflow file is introduced). The same step MUST also invoke the JSON Schema validator against `docs/test-data/manifest.json` and the Indigenous-placeholder lint (FR-044). [Resolved by CL-7]
- **FR-033**: System MUST provide a persona-coverage report derived from the manifest that lists, per persona, the manifest entries serving it; the report MUST flag any persona with zero entries.
- **FR-034**: System MUST record, per public-dataset snapshot, an SPDX-compatible licence note and an attribution string suitable for inclusion in the AMA platform's "Acknowledgements" surface.
- **FR-035**: The existing `docs/corpus/MANIFEST.md` and `docs/corpus/INDEXING-LICENCE-INVENTORY.md` MUST remain authoritative for the handbooks corpus; the new `docs/test-data/MANIFEST.md` MUST cross-reference (not duplicate) those entries that are also test-data inputs.
- **FR-036**: The CI `quality:` job MUST validate that `docs/test-data/MANIFEST.md` is in sync with `docs/test-data/manifest.json` (the CI-validated source of truth). The check MUST re-run the markdown renderer (`tools/lint/render_test_data_manifest_md.py`) against `manifest.json` and compare the rendered output against the committed `MANIFEST.md` using **byte-exact equality after both sides are normalised to LF line endings and UTF-8 encoding** (the renderer already emits LF-only bytes at write time; the lint MUST apply the same `\r\n`→`\n` normalisation to the committed file before comparison so that Windows `core.autocrlf=true` checkouts do not produce false positives). Any divergence (entry count mismatch, missing/added rows, field drift, ordering drift, or formatting drift) MUST cause a non-zero exit. The renderer's deterministic contract (entries sorted by `(category, id)`, LF terminators, UTF-8) MUST be preserved; any change to that contract requires updating both the renderer and this requirement. On failure, the lint MUST print (a) a unified `diff --unified` of the two normalised buffers truncated to a sensible line budget and (b) the exact remediation command: `python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py`. The lint script (e.g. `tools/lint/check_manifest_md_fresh.py`) MUST integrate as a step inside the existing `quality:` job in `.github/workflows/ci.yml` — NO new GitHub workflow files are introduced. This requirement closes the freshness gap identified in the Step-8 all-agents review (OBJ-001), where `MANIFEST.md` reported 105 entries while `manifest.json` contained 134 and CI did not enforce parity. [Resolved by CL-9, refined by CL-10]

#### E. Labelling, Compliance, and Sensitivity Controls

- **FR-040**: All test-data artefacts MUST carry the fictitious-data marker at **both** scopes, with these concrete locations: **(a) JSON files** — a top-level wrapper object `{"_fixture": {"fictitious": true, "residency": "AU", "licence": "<spdx>", "schema_version": "<n>"}, "records": [...]}`. **(b) NDJSON files** (`fixtures/sim_replays/*.ndjson` and similar) — a mandatory first-line header record `{"_fixture_header": true, "fictitious": true, "residency": "AU", "licence": "<spdx>", "scenario_id": "<id>", "seed": <int>}` followed by data records. **(c) Code-generated artefacts** — a documented module-level constant or file-prologue comment naming the generator id and version. **(d) Record level (authoritative post-load)** — every persisted record (whether stored in Cosmos, returned from a generator, or emitted on the simulator bus) MUST carry the field `fictitious: true` at the document root. Loaders MUST reject any file whose wrapper/header marker is missing AND every persistence path MUST verify the record-level marker on each record before commit. [Resolved by CL-5]
- **FR-041**: All persons named in any seed record, generator output, or simulator-emitted message MUST be synthetic (`John Doe`-style) or `[FICTITIOUS]`-prefixed; no real names of operational personnel, real patient identifiers, or real political/ministerial actors are permitted.
- **FR-042**: All seed and simulator data MUST remain Australia-resident in transit and at rest (Azure Australia East / Australia Southeast); the manifest MUST attest residency per artefact.
- **FR-043**: All test-data artefacts MUST default to PSPF marking `OFFICIAL`; artefacts that deliberately exercise sensitive-handling code paths MAY be marked `OFFICIAL: SENSITIVE` if explicitly enumerated in the manifest with a documented justification; markings of `PROTECTED` or above MUST be rejected.
- **FR-044**: Cultural-authority and Indigenous-community references MUST be paraphrased or labelled placeholder; no real Traditional Owner names, real sacred-site coordinates, or real community names may appear; remote NT and remote WA community references MUST be anonymised to the regional-zone level and MUST carry a `cultural-review-required=true` flag in the manifest. Enforcement is **two-layer**: (1) a curated **denylist + allow-list lint** at `tools/lint/check_indigenous_placeholders.py` (mirroring the existing `tools/lint/check_licence_inventory.py` pattern) MUST run in the manifest CI job and fail the build if any seed file, NDJSON replay, generator output sample, or manifest entry contains tokens from the denylist (real Traditional Owner names, real community names, real sacred-site coordinate ranges) or omits the `cultural_review_required` flag for any artefact whose `persona_bindings`, `regions`, or scenario context references an Indigenous-cultural zone; (2) the manifest **JSON Schema** (`docs/test-data/manifest.schema.json`) MUST declare `cultural_review_required: boolean` as a required field, defaulting `false`, and the schema validator (FR-030/FR-032) MUST cross-check that any entry whose region tag matches an Indigenous-context zone has the flag set to `true`. The denylist file is committed at `tools/lint/data/indigenous_denylist.txt` and is itself reviewed by the cultural-authority custodians named in the manifest. [Resolved by CL-6]
- **FR-045**: Loaders and generators MUST reject records that match documented real-PII detectors (real Australian residential address patterns combined with real personal phone/email patterns, real Medicare numbers, real police case numbers, real driver-licence patterns).
- **FR-046**: System MUST NOT replicate any currently-active real emergency warning. Where simulator output structurally imitates a real warning format, the `simulated: true` marker and a "TEST — DO NOT BROADCAST" string MUST appear in the message body, not only in metadata.

#### F. Generators and Mock Resources

- **FR-050**: System MUST provide named, deterministic generators (Faker-style) for the high-cardinality data classes called out in the persona input: synthetic incidents (across hazard types), coordination tasks, signals (with provenance metadata per Constitution Principle III), audit entries (append-only, with deliberate compliance-gap examples for detection testing), risk-register records aligned to AIDR NERAG categories, public-alert drafts, evacuee registration records, missing-persons records, triage records (START categories, no PII), volunteer registration records, vulnerable-person category records, hospital capacity records, transport-asset records, utility outage records.
- **FR-051**: Every generator MUST accept a numeric seed and produce a byte-identical record set on every invocation with that seed. The seed contract is concrete: each generator MUST expose **three input surfaces** with the following precedence (highest first): (1) **function argument** `seed: int` on the generator's primary callable (used by unit tests and in-process callers); (2) **CLI flag** `--seed <int>` on the generator's invocation script under `scripts/generators/<name>.py` (used by the fixtures pipeline and `azd postprovision`); (3) **environment variable** `AMA_TEST_SEED` (fallback for sandboxed CI/dev environments where flags are inconvenient). If none are supplied, the generator MUST use the deterministic default `0` and MUST log a warning. Seeds are 64-bit unsigned integers. "Byte-identical record set" uses the canonical-JSON / NDJSON encoding defined in FR-022. [Resolved by CL-8]
- **FR-052**: Every generator MUST tag every produced record with `fictitious=true`, a generator identifier, and the generator's version.
- **FR-053**: System MUST provide named mock resources for any external dependency a test or local-development run would otherwise contact: in-memory fakes, recorded-cassette HTTP doubles for any third-party REST shapes used illustratively, and locally-runnable storage emulators (e.g. Azurite, the Cosmos emulator) — with the choice of emulator(s) deferred to the planning phase.
- **FR-054**: Mock resources MUST NOT be wired into production code paths; they are reachable only from test, evaluation, and local-dev configurations.

#### G. Persona Coverage and Domain Demos

- **FR-060**: For each of the 68 personas, the manifest MUST resolve ≥1 test-data artefact (seed entry, generator, mock, or simulator feed shape) explicitly bound to that persona.
- **FR-061**: For each domain group (operational, fire, police, ambulance, SES, marine/aviation, commonwealth, cross-sector), at least one named end-to-end demo scenario MUST exist that exercises ≥3 personas in that group, end-to-end through the simulator + seeded reference data.
- **FR-062**: Per-persona artefact volumes MUST meet or exceed the lower bound of each persona's "Volume guide" as captured in the persona input report (e.g. ≥10 mock hospital capacity records per state, ≥20 synthetic vulnerable-person category entries, ≥30 synthetic volunteer registration records, ≥5 multilingual alert variants per supported language, ≥3–5 earthquake events per simulation session).

#### H. Multilingual and Accessibility Content

- **FR-070**: Multilingual alert templates MUST cover, at minimum, the existing locales (`en-AU`, `ar`, `el`, `it`, `vi`, `zh-Hans`) plus a documented placeholder slot for ≥1 Indigenous-language example and an Auslan-transcript placeholder; placeholders MUST carry `placeholder=true` and a "needs cultural-authority review" manifest note.
- **FR-071**: Alert template content MUST comply with WCAG 2.1 AA for any rendered surface (plain language, audio descriptions where applicable).

### Key Entities

- **TestDataAsset**: A single named test-data artefact. Attributes: `id`, `name`, `category`, `path` or `source_shape`, `version`, `content_hash`, `created_or_updated`. Relationships: serves ≥1 Persona; produces ≥0 emitted records; references exactly 1 LicenceRecord; references exactly 1 Provenance.
- **SeedCatalogueEntry**: A static reference record loaded by `seed_loader.py`. Attributes: `id`, `catalogue` (e.g. `organisations_australia`), `record_payload`, `fictitious=true`, `residency=AU`, `pspf` marking. Relationships: belongs to exactly 1 TestDataAsset.
- **SimulatorFeed**: A named, versioned simulator feed shape (e.g. `bom.severe_weather_warning.v1`). Attributes: `source_shape`, `version`, `feed_kind` (BoM/GA/EPA/synthetic-fallback/etc.), `deterministic=true`. Relationships: emitted only by code under `apps/api/app/services/simulation/`; bound to ≥1 named scenario.
- **TestDataManifestEntry**: A row in the test-data manifest. Attributes mirror FR-031.
- **Provenance**: Where the artefact came from. Attributes: `origin` (synthetic | public | generator-output | mock | simulator-feed-shape), `source_url` (if public), `snapshot_date` (if public), `dataset_version` (if public), `attribution_string`.
- **LicenceRecord**: SPDX-compatible licence record. Attributes: `spdx_identifier`, `licence_text_path`, `attribution_required` (bool), `attribution_string`.
- **PersonaBinding**: The link between a TestDataAsset and one or more personas it serves. Attributes: `persona_id`, `domain_group`, `binding_kind` (organisation-record, scenario-record, generator-output, simulator-feed, alert-template, etc.).
- **DemoScenario**: A named, deterministic end-to-end scenario combining seed entries + simulator feeds + persona bindings. Attributes: `scenario_id`, `name`, `default_seed`, `participating_personas`, `participating_feeds`, `expected_duration`.
- **CompliancePolicy**: The set of rules every artefact must satisfy. Attributes: `pii_forbidden=true`, `pspf_max=OFFICIAL: SENSITIVE`, `residency=AU`, `fictitious_required=true`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 68 personas resolve to ≥1 named test-data artefact in the manifest, verified by an automated persona-coverage report; the report shows zero "unbacked" personas.
- **SC-002**: 100% of seed records loaded by `azd postprovision` carry a fictitious-data marker, an Australian-residency attestation, and a licence reference; the loader rejects any record missing any of these fields, verified by a deliberate negative test.
- **SC-003**: 100% of test-data artefacts in the catalogued directories are enumerated in `docs/test-data/MANIFEST.md`, with all required fields non-empty; a continuous-integration check fails the build if this is not the case.
- **SC-004**: Re-running `azd postprovision` against a previously seeded environment produces zero inserts, zero updates, and zero divergence on every catalogue (idempotent convergence), verified by hash comparison.
- **SC-005**: Running the same simulator scenario twice with the same numeric seed produces byte-identical emitted message sequences on every feed, where "byte-identical" is defined per FR-022 (canonical-JSON NDJSON, deterministic simulated-clock timestamps, SHA-256 stream digest equality); verified by a recorded-tape diff and digest comparison.
- **SC-006**: Zero outbound network calls are made by the simulator to any real BoM, GA, ABS, AURIN, EPA, OpenStreetMap, or jurisdictional production endpoint during any scenario run, verified by network-egress capture.
- **SC-007**: Zero production code paths import from the simulator package, verified by a static dependency-graph check.
- **SC-008**: Each of the 8 domain groups (operational, fire, police, ambulance, SES, marine/aviation, commonwealth, cross-sector) has ≥1 named end-to-end demo scenario that exercises ≥3 of its personas; verified by the persona-coverage report.
- **SC-009**: 100% of public-dataset entries in the manifest carry a non-empty `source_url`, `snapshot_date`, `dataset_version`, and SPDX licence identifier; verified by the manifest CI check.
- **SC-010**: A first-time reviewer can, using only the manifest and the inventory document, enumerate every test-data artefact and identify the persona(s) it serves in under 30 minutes; verified by a documented walkthrough check. The <30-minute target is contingent on the freshness gate enforced by SC-016 / FR-036 — i.e. `docs/test-data/MANIFEST.md` accurately reflects every entry in `docs/test-data/manifest.json` at every commit on the default branch.
- **SC-011**: Zero artefacts in the manifest carry `pii=true`, zero carry `residency≠AU`, and zero carry a PSPF marking above `OFFICIAL: SENSITIVE`; verified by manifest filters.
- **SC-012**: Per-persona artefact volumes meet or exceed the lower bound of each persona's documented volume guide; verified by an automated volume-coverage check.
- **SC-013**: A fresh provisioned environment (clean subscription, `azd up` from scratch) becomes demo-ready (seed loaded, simulator runnable for ≥1 named scenario per domain group) in a single automated run with no manual data-entry steps.
- **SC-014**: Every multilingual alert template entry resolves to either a translated body or an explicitly-flagged `placeholder=true` entry with a "needs cultural-authority review" note; verified by manifest filter.
- **SC-015**: Every Indigenous-community-context artefact is anonymised to the regional-zone level and carries `cultural-review-required=true`; verified by manifest filter.
- **SC-016**: 100% of PRs that touch `docs/test-data/manifest.json` (directly or indirectly via `scripts/build_test_data_manifest.py`) MUST also commit a regenerated `docs/test-data/MANIFEST.md`; CI rejects any PR where the renderer's output diverges from the committed Markdown under byte-exact, LF-normalised, UTF-8 comparison (per FR-036). Verifiable locally by running `tools/lint/check_manifest_md_fresh.py` and observing exit code `0` on a fresh render and non-zero on any divergence; on non-zero, the lint MUST also print the remediation command from FR-036. Entry-count parity between `MANIFEST.md` and `manifest.json` MUST be exact at every commit on the default branch. SC-016 is N/A on any branch where `docs/test-data/manifest.json` does not yet exist (i.e. on branches predating spec-039 Phase 1); the lint MUST exit `0` with a skip notice in that case.

---

## Assumptions

The following informed defaults have been adopted in lieu of explicit clarifications, prioritising scope/security/UX over technical detail:

- **A-1 (existing system anchors):** The existing seed loader (`scripts/seed_loader.py`), seed catalogue (`packages/domain/src/domain/seed/`), simulator (`apps/api/app/services/simulation/`), and corpus manifests (`docs/corpus/`) are authoritative and are extended in place; this feature does NOT redesign or replace them.
- **A-2 (next branch):** Numbering follows the existing `0NN-` convention; this feature is `039-test-data-provisioning`.
- **A-3 (scope bounds):** This feature's spec is technology-agnostic; concrete choices (whether to add Azurite, Cosmos emulator, WireMock, MSAL mock tenants, etc., as bundled local-dev resources) are deferred to the planning phase per the user's explicit out-of-scope guidance.
- **A-4 (persona universe):** The 68 personas enumerated in the consolidated persona input report are the authoritative coverage set for this feature; if a persona is later added or renamed, the manifest's CI check will surface the gap.
- **A-5 (volume guides):** The lower bounds in each persona's "Volume guide" are treated as binding minima; upper bounds are advisory.
- **A-6 (public datasets):** BoM open data, GA earthquake catalogue, ABS, AURIN, OpenStreetMap, AIDR are used under their respective open-data licences (CC BY, public domain, ODbL, CC BY); attribution is recorded in the manifest. No real BoM/GA/ABS endpoints are called from production code paths; only cached snapshots are used by the simulator.
- **A-7 (PSPF default):** All test data defaults to `OFFICIAL`; `OFFICIAL: SENSITIVE` is permitted only where deliberate exercise of sensitive-handling code paths is required and is enumerated with justification in the manifest.
- **A-8 (residency):** All test data resides in Azure Australia East / Australia Southeast; cross-region data movement is out of scope.
- **A-9 (fictitious naming):** All persons are `John Doe`-style or `[FICTITIOUS]`-prefixed; this includes evacuees, missing persons, volunteers, ministerial actors, operational personnel.
- **A-10 (Indigenous data):** No real Traditional Owner names, sacred-site coordinates, or community names are used; placeholders carry `cultural-review-required=true`. No community-approved licence is assumed.
- **A-11 (out-of-scope):** Net-new Azure infrastructure, replacement of the simulation engine, real PII handling, and real BoM/GA/ABS production integrations are explicitly out of scope; the planning phase may select local-dev emulators as needed.
- **A-12 (deletion semantics):** The seed loader is upsert-only; deletion of records absent from the catalogue is out of scope and will not be performed automatically.
- **A-13 (manifest format):** The manifest is published in two forms — a human-readable Markdown file (`docs/test-data/MANIFEST.md`, auto-rendered) and a machine-readable JSON companion (`docs/test-data/manifest.json`) validated against `docs/test-data/manifest.schema.json` in CI. JSON is selected to match the existing `docs/corpus/` convention (per-source `source.json` sidecars rendered into `INDEXING-LICENCE-INVENTORY.md`). [Resolved CL-1]
- **A-14 (simulator delivery surface):** Simulator output is published onto the existing in-process Event Hub / Service Bus surface already used by `apps/api/app/services/simulation/event_hub_publisher.py`; no new HTTP endpoints, no new Azure resources. A deterministic file-based replay mode (`fixtures/sim_replays/<scenario>.ndjson`) is additionally supported for offline/CI scenarios. [Resolved CL-2]
- **A-15 (load-fixture volume tiers):** Four named tiers — `small=10`, `medium=100`, `large=1,000`, `xlarge=10,000` records — aligned with `specs/015-performance-benchmarks`. `small`/`medium`/`large` may be committed; `xlarge` and above are generated on demand by a deterministic streaming generator and never committed. [Resolved CL-3]
- **A-16 (canonical replay encoding):** "Byte-identical" means SHA-256 equality over canonical-JSON NDJSON (UTF-8, sorted keys, no insignificant whitespace, LF line terminator, deterministic simulated-clock timestamps and HMAC-derived correlation IDs). [Resolved CL-4]
- **A-17 (fictitious marker locations):** JSON files use a top-level `_fixture` wrapper; NDJSON files use a mandatory first-line `_fixture_header` record; code-generated artefacts use a module-level constant; and **every** persisted record carries `fictitious=true` at the document root regardless of source-file shape. [Resolved CL-5]
- **A-18 (Indigenous enforcement):** Two-layer — a `tools/lint/check_indigenous_placeholders.py` denylist lint (denylist file at `tools/lint/data/indigenous_denylist.txt`) plus a manifest schema field `cultural_review_required: boolean` cross-validated by the schema validator. [Resolved CL-6]
- **A-19 (manifest CI integration point):** Manifest validation is a step in the existing `quality` job in `.github/workflows/ci.yml`; no new workflow file is added. Implementing tool: `tools/lint/check_test_data_manifest.py`. [Resolved CL-7]
- **A-20 (generator seed contract):** Three input surfaces with precedence function-arg `seed:int` > CLI `--seed` > env `AMA_TEST_SEED` > default `0`; 64-bit unsigned integers. [Resolved CL-8]

---

## Resolved Clarifications

> **Amendment cycle 1: 2026-05-11** — driven by Step-8 all-agents review (1 HAS_MERIT objection, OBJ-001 from observer-auditor + product-owner-ba + compliance-auditor). Resolution recorded in Pass 4 below; spec touch-points: new FR-036, new SC-016, updated SC-010, new edge case "Manifest renderer skipped or forgotten". Pass 5 (clarification round 1 on the amendment) further refined FR-036 / SC-016 / Edge Case with byte+LF comparison rule, renderer-determinism lock-in, failure-message contract, and N/A-on-missing-manifest skip behaviour (CL-10). **Pass 6 (confirmation sweep, 2026-05-11)** — no contradictions found between FR-036/SC-016 and FR-030..FR-035 or FR-040..FR-046; two minor inventory gaps self-resolved (CL-11: MANIFEST.md is intentionally a summary view, not a 1:1 surface of every FR-031 field — JSON is authoritative; CL-12: `domain_group` added to FR-031's enumerated field list to align spec with the schema and renderer). Amendment cycle 1 is now closed.

### Session 2026-05-11

- **Q (CL-1):** Structured manifest format — JSON, YAML, or TOML?  
  **A:** **JSON.** Single canonical companion at `docs/test-data/manifest.json` validated against `docs/test-data/manifest.schema.json` in CI. Markdown render at `docs/test-data/MANIFEST.md` is auto-generated for human review.  
  **Source justification:** Established AMA convention — `docs/corpus/` uses per-source `source.json` sidecars and renders an aggregated `INDEXING-LICENCE-INVENTORY.md` via `scripts/disaster_corpus/manifest.py`. JSON Schema validation is standards-compliant per Constitution Principle VIII (open standards). Overrides the user's recommended YAML in favour of in-repo prior art.  
  **Spec touch-points:** FR-030 (rewritten), A-13 (rewritten).

- **Q (CL-2):** Simulator delivery surface — shared in-process bus or separate dev-only channel?  
  **A:** **Re-use the existing in-process Event Hub / Service Bus publish surface** in `apps/api/app/services/simulation/event_hub_publisher.py`; no new HTTP endpoints, no new Azure resources. Add a deterministic file-based replay mode at `fixtures/sim_replays/<scenario>.ndjson` for offline/CI tests.  
  **Source justification:** `apps/api/app/services/simulation/event_hub_publisher.py` is verified to exist; `specs/036-sim-agent-extend/spec.md` (FR-006/FR-064/FR-073 and the publish-budget discussion at lines 584–597) already establishes Event Hub publish + subscriber-ack as the canonical simulator-to-agent surface. Constitution Principle VIII (Azure-only, no superfluous resources) and the Two-Path Rule both forbid net-new infra here.  
  **Spec touch-points:** FR-024 (rewritten), A-14 (added).

- **Q (CL-3):** Upper bound for load-fixture volume?  
  **A:** **Four tiers — `small=10`, `medium=100`, `large=1,000`, `xlarge=10,000` records per catalogue/feed.** `small`/`medium`/`large` may be committed; `xlarge` (and any larger volume) is generated on demand by a deterministic streaming generator and is NOT committed.  
  **Source justification:** Aligns with `specs/015-performance-benchmarks` (which explicitly de-scopes the legacy 50-concurrent-worker load pattern and treats high-volume work as benchmark-suite output, not committed fixtures). Streaming requirement honours the existing edge-case constraint that the loader must not materialise the full set in memory.  
  **Spec touch-points:** Edge Case "Large-volume load fixtures" (rewritten), A-15 (added).

### Session 2026-05-11 (Pass 2)

- **Q (CL-4):** What does "byte-identical replay" mean precisely — same JSONL bytes, or same record set irrespective of order/encoding?  
  **A:** **Same canonical NDJSON bytes, in the same order, verified by SHA-256 stream digest equality.** Canonical encoding is UTF-8 / RFC 8259 with lexicographically sorted keys, no insignificant whitespace, shortest round-trip numeric form, LF line terminator, ISO-8601 microsecond UTC timestamps drawn from a deterministic simulated clock seeded by `(scenario_id, seed, ordinal)`, and HMAC-derived correlation IDs. Wall-clock timestamps are forbidden in replay-comparable fields.  
  **Source justification:** `specs/036-sim-agent-extend/spec.md` already mandates ordered deterministic publish (FR-006 / FR-064); Constitution Principle VIII (open standards) supports JCS-style canonical JSON; existing `tools/lint/check_licence_inventory.py` and `scripts/disaster_corpus/manifest.py` already use sorted-keys JSON for stable hashing.  
  **Spec touch-points:** FR-022 (rewritten), SC-005 (rewritten), A-16 (added).

- **Q (CL-5):** Where exactly does the fictitious-data marker live for NDJSON files and for records persisted into Cosmos (where file headers don't survive)?  
  **A:** **Both file-scope and record-scope, with concrete shapes per file format.** JSON files: top-level `_fixture` wrapper object. NDJSON files: mandatory first-line `_fixture_header` record. Code-generated artefacts: module-level constant or file-prologue comment. Authoritative post-load: every persisted document (Cosmos or otherwise) carries `fictitious: true` at the document root, verified by every persistence path before commit.  
  **Source justification:** FR-040 already mandated both scopes but left format-specific shape ambiguous; resolved against repo prior art in `apps/eval-runner/fixtures/spec036/` (record-level markers) and the corpus per-source `source.json` sidecar pattern (file-level wrapper). Cosmos pre-commit verification mirrors the existing seed-loader rejection pattern in FR-015.  
  **Spec touch-points:** FR-040 (rewritten), A-17 (added).

- **Q (CL-6):** What is the explicit enforcement mechanism for "no real Traditional Owner names"?  
  **A:** **Two-layer enforcement: (1) denylist lint at `tools/lint/check_indigenous_placeholders.py` (denylist data at `tools/lint/data/indigenous_denylist.txt`) wired into the manifest CI job, AND (2) a required manifest JSON Schema field `cultural_review_required: boolean` cross-validated against artefact region tags by the schema validator.**  
  **Source justification:** Mirrors the existing `tools/lint/check_licence_inventory.py` pattern verified to exist in the repo; constitution forbids unattested cultural references; CL-1's resolution already established `docs/test-data/manifest.schema.json` as the schema validation surface. Two-layer (data lint + schema cross-check) prevents bypass via either path.  
  **Spec touch-points:** FR-044 (rewritten), A-18 (added).

- **Q (CL-7):** Does the manifest CI lint run in the existing `.github/workflows/ci.yml`, and which job?  
  **A:** **Yes — as a step in the existing `quality` job in `.github/workflows/ci.yml`. No new workflow file is introduced.** Implementing tool: `tools/lint/check_test_data_manifest.py`. The same step also invokes the JSON Schema validator and the Indigenous-placeholder lint (FR-044).  
  **Source justification:** `.github/workflows/ci.yml` line 15 confirms the `quality:` job exists and is the canonical place for repo-wide lint gates; the corpus equivalent (`tools/lint/check_licence_inventory.py`) is already invoked from `corpus-ingest.yml` line 102, but for test-data the gate must run on every PR (not on cron), so the `quality` job in `ci.yml` is the correct surface. Adding a new workflow file would violate Constitution Principle VIII (no superfluous CI plumbing).  
  **Spec touch-points:** FR-032 (rewritten), A-19 (added).

- **Q (CL-8):** Is the generator's deterministic seed parameter a CLI flag, environment variable, or function argument?  
  **A:** **All three, with explicit precedence: function argument `seed: int` > CLI flag `--seed <int>` > env var `AMA_TEST_SEED` > deterministic default `0` (with a warning).** Seeds are 64-bit unsigned integers. The generator's primary callable accepts the function argument; an invocation script under `scripts/generators/<name>.py` exposes the CLI flag; `AMA_TEST_SEED` is read only when neither is supplied.  
  **Source justification:** `scripts/seed_loader.py` (verified to exist) follows the CLI + env pattern; Faker fixtures under `tests/fixtures/` use the function-argument pattern. Combining all three with a clear precedence honours all existing call sites without breaking either pattern, and the explicit default-with-warning ensures sandboxed CI never produces silent non-determinism.  
  **Spec touch-points:** FR-051 (rewritten), A-20 (added).

### Session 2026-05-11 (Pass 3 — implementation closure)

- **Note:** Implementation verified — see
  [`verification.md`](./verification.md). All 15 success criteria and
  all 41 banded functional requirements (FR-001..FR-071) map to a
  concrete test, lint, manifest entry, or CI step. No further
  clarifications added in Pass 3; this entry records closure only.
  Companion artefact: [`lessons.md`](./lessons.md).

### Session 2026-05-11 (Pass 4 — amendment cycle 1, post Step-8 all-agents review)

- **Trigger:** All-agents review returned 1 HAS_MERIT objection — **OBJ-001** (observer-auditor + product-owner-ba + compliance-auditor): `docs/test-data/MANIFEST.md` reported **105 entries** while `docs/test-data/manifest.json` (the CI-validated source of truth) contained **134 entries**. The CI `quality:` job enforced `check_test_data_manifest.py` against `manifest.json` but did NOT enforce `MANIFEST.md` freshness. SC-010's <30-minute reviewer enumeration target depends on the rendered Markdown being accurate; external auditors relying on the stale `MANIFEST.md` would form an incorrect picture of the test corpus. Three further objections (OBJ-002, OBJ-003, OBJ-004) were PARTIAL_MERIT and are tracked in [`lessons.md`](./lessons.md) follow-ups; no spec change for those.

- **Q (CL-9):** How does the spec guarantee that `docs/test-data/MANIFEST.md` (human-readable rendered view) cannot drift from `docs/test-data/manifest.json` (the CI-validated source of truth)?  
  **A:** **Add an explicit CI freshness gate.** A new lint `tools/lint/check_manifest_md_fresh.py` runs as a step inside the existing `quality:` job in `.github/workflows/ci.yml`; it re-invokes the renderer `tools/lint/render_test_data_manifest_md.py` against `manifest.json`, diffs the result against the committed `MANIFEST.md`, and exits non-zero on any divergence (entry count, row contents, field drift, or formatting drift). No new workflow files. Codified as **FR-036**, **SC-016**, the new edge case "Manifest renderer skipped or forgotten", and a clarifying addendum to **SC-010**.  
  **Source justification:** OBJ-001 evidence (105 vs 134 entry mismatch) confirmed empirically against `docs/test-data/MANIFEST.md` and `docs/test-data/manifest.json`. Pattern mirrors the existing CI-rendered-and-diffed approach used by `docs/corpus/INDEXING-LICENCE-INVENTORY.md` (rendered from per-source `source.json` sidecars). Honours Constitution Principle VIII (no superfluous CI plumbing — re-uses the existing `quality:` job per A-19 / CL-7).  
  **Spec touch-points:** FR-036 (added), SC-016 (added), SC-010 (clarifying addendum), Edge Case "Manifest renderer skipped or forgotten" (added), A-21 (added below in spirit; tracked here in the clarifications log to avoid renumbering existing assumption IDs).  
  **Implementation note:** Implementation occurs in this amendment's Step 7 (not in this spec edit). Required artefacts: `tools/lint/render_test_data_manifest_md.py`, `tools/lint/check_manifest_md_fresh.py`, and a single-step addition to the `quality:` job in `.github/workflows/ci.yml`.

### Session 2026-05-11 (Pass 5 — amendment cycle 1, clarification round 1 on FR-036/SC-016)

- **Q (CL-10):** FR-036 and SC-016 specify a "diff" between the re-rendered output and the committed `MANIFEST.md` but leave three micro-decisions implicit: (a) the comparison method (byte vs structural), (b) line-ending and encoding normalisation across Windows / macOS / Linux checkouts, and (c) the operator-actionable contract on lint failure. What are the canonical answers?
  **A:** **(a) Byte-exact equality**, applied to **(b) both buffers normalised to LF line endings and UTF-8 encoding** before comparison (the renderer at `tools/lint/render_test_data_manifest_md.py` already calls `.replace("\r\n", "\n")` before writing bytes, so the lint MUST apply the same `\r\n`→`\n` normalisation to the committed-file bytes — this neutralises Windows `core.autocrlf=true` checkouts without weakening byte-equality on the wire). The renderer's existing deterministic contract — entries sorted by `(category, id)`, LF terminators, UTF-8, fixed header — is locked in by FR-036 and any change requires updating both the renderer and FR-036. **(c) On failure, the lint MUST print** (i) a unified diff of the two normalised buffers (truncated to a sensible line budget so CI logs stay readable) and (ii) the exact remediation command `python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py`. SC-016 additionally clarifies that the gate is **N/A on branches predating spec-039 Phase 1** (no `manifest.json` yet) — the lint exits `0` with a skip notice in that case.
  **Source justification:** Renderer determinism verified at `tools/lint/render_test_data_manifest_md.py` lines 39 (sort key), 65 (LF join + trailing LF) and 80 (`\r\n`→`\n` on write). LF-everywhere normalisation matches the canonical-JSON / LF-terminator policy already adopted in CL-4 (`A-16 (canonical replay encoding)`) and the corpus rendering precedent at `docs/corpus/INDEXING-LICENCE-INVENTORY.md`. Printing the remediation command honours Constitution Principle VIII (no superfluous infra — the operator should not need to consult the spec to fix a freshness failure). N/A-on-missing-manifest mirrors the standard skip pattern used by other repo lints when the target artefact is not yet present on a branch.
  **Spec touch-points:** FR-036 (refined: byte/LF/UTF-8 comparison rule, renderer-determinism lock-in, failure-message contract), SC-016 (refined: same comparison rule, failure-message reference, N/A clause for pre-Phase-1 branches), Edge Case "Manifest renderer skipped or forgotten" (refined: explicit remediation command in failure path).

### Session 2026-05-11 (Pass 6 — amendment cycle 1, confirmation sweep / closure)

- **Q (CL-11):** FR-031 enumerates ~17 fields every manifest entry must carry, but the renderer at `tools/lint/render_test_data_manifest_md.py` (whose deterministic contract is now locked in by FR-036) only surfaces a 7-column subset (`id`, `path`/`source_shape`, `domain_group`, `persona_bindings`, `pspf`, `licence`, `cultural_review_required`). Is this a contradiction, or is `MANIFEST.md` intentionally a summary view?  
  **A:** **Intentionally a summary view — no contradiction.** `docs/test-data/manifest.json` is the authoritative carrier of every FR-031 field (and is the artefact validated against `manifest.schema.json` per FR-030/FR-032); `docs/test-data/MANIFEST.md` is the human-readable executive summary auditors use for the <30-min walkthrough check (SC-010). FR-036 freezes the renderer's column set as part of the deterministic contract; auditors needing the full field set per entry MUST consult `manifest.json`. FR-031 is updated to state this explicitly and to clarify which columns are surfaced.  
  **Source justification:** Renderer `render()` body emits exactly the 7 columns above; FR-030 already designates `manifest.json` as "the canonical machine-readable companion"; FR-036 already locks the renderer's deterministic contract.  
  **Spec touch-points:** FR-031 (added explicit summary-view clause and column enumeration).

- **Q (CL-12):** The schema at `docs/test-data/manifest.schema.json` lists `domain_group` as a required per-entry field and the renderer surfaces it as a table column, but FR-031's enumerated field list omits it. Should FR-031 be amended to include `domain_group`?  
  **A:** **Yes.** `domain_group` is a required field by both the schema (line 44) and the renderer's locked contract (FR-036), and is already defined in the Data Model under PersonaBinding. FR-031 is amended to include `domain_group` and to cross-reference the PersonaBinding taxonomy. This closes a latent drift between the spec text, the schema, and the renderer with no behavioural change to any of the three.  
  **Source justification:** `docs/test-data/manifest.schema.json:44` lists `domain_group` in the entry `required` array; renderer `render()` emits a `domain_group` column; spec.md:198 already defines `domain_group` on PersonaBinding.  
  **Spec touch-points:** FR-031 (added `domain_group` to the enumerated field list with cross-reference to PersonaBinding taxonomy).

- **Sweep result:** No contradictions found between FR-036/SC-016 (manifest freshness gate) and FR-030..FR-035 (manifest contract) or FR-040..FR-046 (compliance markers / Indigenous-placeholder / PII / no-active-warning). The Edge Case "Manifest renderer skipped or forgotten" remains aligned with FR-036/SC-016 (byte-exact, LF-normalised, UTF-8; same remediation command). No new edge cases unbound to an FR were introduced by the amendment. **Amendment cycle 1 is closed.**
  **Implementation note:** No new artefacts beyond those already listed under CL-9. The `tools/lint/check_manifest_md_fresh.py` to be implemented in Step 7 MUST encode the (a)/(b)/(c) rules above and the N/A-on-missing-manifest skip behaviour.

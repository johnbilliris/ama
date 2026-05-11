# Seed Catalogue Checklist: Idempotent Loading, Extension Procedure, Persona Coverage

**Purpose**: Operational acceptance gate for the Path-1 (static reference data) seed catalogue — covering idempotent loading via `azd postprovision`, the documented extension procedure, and full persona-group coverage.
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)
**Scope**: FR-010..FR-016, FR-060..FR-062, SC-001, SC-002, SC-004, SC-008, SC-012, SC-013, A-1, A-4, A-5, A-12.

## Catalogue Completeness (FR-010 Coverage)

- [ ] CHK001 Seed catalogue under `packages/domain/src/domain/seed/` contains organisation records for all 68 persona-bound entities (FR-010, FR-060).
- [ ] CHK002 Jurisdiction definitions exist for all 9 jurisdictions plus commonwealth (FR-010).
- [ ] CHK003 An `OperatingFramework` record exists for every organisation record (FR-010).
- [ ] CHK004 Hazard taxonomies, AIIMS function-map extensions, and coordination task templates are seeded (FR-010).
- [ ] CHK005 Recovery catalogues are seeded for: overarching, social, economic, built, natural, and evaluation-questions categories (FR-010).
- [ ] CHK006 Identity and RBAC seed entries are populated for every persona role (FR-010, FR-060).
- [ ] CHK007 Multilingual alert templates are seeded for `en-AU`, `ar`, `el`, `it`, `vi`, `zh-Hans`, ≥1 Indigenous-language placeholder, and ≥1 Auslan-transcript placeholder (FR-010, FR-070).
- [ ] CHK008 Evacuation route catalogues, scenario templates, and inter-government agreement templates are seeded (FR-010).
- [ ] CHK009 Vulnerable-person *category* catalogues are seeded with no PII (FR-010, FR-045).
- [ ] CHK010 Hospital capability flag catalogues, road-segment catalogues, and generic utility infrastructure catalogues (no real identifiers) are seeded (FR-010).
- [ ] CHK011 Volunteer skill/credential category catalogues, LEMP and MEMP record templates are seeded (FR-010).

## Idempotent Loading

- [ ] CHK012 The existing `scripts/seed_loader.py` is the sole loader entry point; no parallel loader path exists (FR-011, A-1).
- [ ] CHK013 The existing `azd postprovision` hook invokes `scripts/seed_loader.py` with no manual intervention required (FR-011, SC-013).
- [ ] CHK014 Re-running `azd postprovision` against a previously seeded environment produces zero inserts and zero updates on every catalogue (FR-012, SC-004).
- [ ] CHK015 Content hashes per catalogue match byte-for-byte across consecutive postprovision runs (FR-012, SC-004).
- [ ] CHK016 The loader uses stable artefact identifiers and content hashes to upsert (insert-or-update) records (FR-013).
- [ ] CHK017 The loader does NOT delete records that are absent from the catalogue source (deletion is out of scope) (FR-013, A-12).
- [ ] CHK018 The loader emits a per-catalogue summary on completion in the form "N inserts, N updates, N already-current" (FR-014).
- [ ] CHK019 The loader exits with a success status code on a successful re-seed even when all rows are already-current (FR-014, SC-004).
- [ ] CHK020 An automated re-seed test runs in CI and asserts hash equality across two consecutive invocations (SC-004).

## Loader Rejection Behaviour

- [ ] CHK021 The loader rejects any record missing the fictitious-data marker with an explicit error and zero partial load (FR-015, FR-040).
- [ ] CHK022 The loader rejects any record missing the residency attestation with an explicit error (FR-015, FR-042).
- [ ] CHK023 The loader rejects any record missing a licence reference with an explicit error (FR-015, FR-034).
- [ ] CHK024 A deliberate negative test exists that feeds a corrupted seed file (e.g. missing licence field) and asserts loader rejection citing the missing compliance field (FR-015, US1 acceptance scenario 4, SC-002).
- [ ] CHK025 The loader does NOT silently skip rejected records (FR-015).
- [ ] CHK026 No streamed/runtime data is loaded by the seed loader; any such dataset is routed through the simulator (FR-016).

## Seed Catalogue Extension Procedure

- [ ] CHK027 A documented extension procedure exists describing how to add a new seed-catalogue entry (which directory under `packages/domain/src/domain/seed/`, which fields are required, how the loader picks it up).
- [ ] CHK028 The extension procedure mandates that every new entry has a stable `id`, `fictitious=true`, `residency=AU`, `pspf` marking, and licence reference (FR-015, FR-031).
- [ ] CHK029 The extension procedure requires a corresponding manifest entry to be added in the same change (FR-030, FR-032).
- [ ] CHK030 The extension procedure requires the persona-binding(s) to be declared on the new entry (FR-060, FR-031).
- [ ] CHK031 The extension procedure requires the appropriate volume tier (`small`/`medium`/`large`) to be picked, and forbids committing `xlarge` fixtures (A-15, FR-062).
- [ ] CHK032 The extension procedure forbids editing `scripts/seed_loader.py` for new catalogue types unless a new catalogue kind is genuinely needed (A-1, "extended in place").
- [ ] CHK033 A code-review checklist or PR template enforces the above gates on any seed-catalogue change.

## Persona-Group Coverage (FR-060..FR-062)

- [ ] CHK034 Every one of the 68 personas resolves to ≥1 seed-catalogue entry, generator, mock, or simulator-feed-shape in the manifest (FR-060, SC-001, A-4).
- [ ] CHK035 The 10 operational personas each have ≥1 seed entry naming them in `persona_bindings` (FR-060, SC-001).
- [ ] CHK036 The 33 state/territory sector personas each have ≥1 seed entry naming them in `persona_bindings` (FR-060, SC-001).
- [ ] CHK037 The 11 commonwealth personas each have ≥1 seed entry naming them in `persona_bindings` (FR-060, SC-001).
- [ ] CHK038 The 8 cross-sector personas each have ≥1 seed entry naming them in `persona_bindings` (FR-060, SC-001).
- [ ] CHK039 The 6 NSW personas each have ≥1 seed entry naming them in `persona_bindings` (FR-060, SC-001).
- [ ] CHK040 Each of the 8 domain groups (operational, fire, police, ambulance, SES, marine/aviation, commonwealth, cross-sector) has ≥1 named end-to-end demo scenario seeded that exercises ≥3 personas in that group (FR-061, SC-008).
- [ ] CHK041 Per-persona seed volumes meet the lower bound of each persona's volume guide (FR-062, SC-012, A-5).
- [ ] CHK042 ≥10 mock hospital capacity records per state are seeded (FR-062, US4 acceptance scenario 3).
- [ ] CHK043 ≥20 synthetic vulnerable-person category entries (no PII) are seeded (FR-062, US4 acceptance scenario 3).
- [ ] CHK044 ≥30 synthetic volunteer registration records are seeded (FR-062, US4 acceptance scenario 3).
- [ ] CHK045 ≥5 multilingual alert variants per supported language are seeded (FR-062, FR-070).
- [ ] CHK046 The persona-coverage report (FR-033) shows zero "unbacked" personas (SC-001).
- [ ] CHK047 An automated volume-coverage check fails CI if any persona's volume bound is unmet (SC-012).

## Auditor Verification

- [ ] CHK048 An auditor can query a persona-to-data binding view and resolve every persona to ≥1 seed record (US1 acceptance scenario 3, SC-001).
- [ ] CHK049 Every seeded record in the loaded environment carries `fictitious=true`, `residency=AU`, and a licence reference (US1 acceptance scenario 1, SC-002).

## How to Use

This checklist is an **operational gate**:
- **At end of `/speckit.plan`**: confirm CHK012–CHK013, CHK020, CHK027–CHK033 are reflected in the plan (loader integration, CI re-seed test, extension procedure).
- **At end of `/speckit.implement`**: confirm all 49 items pass against the built environment before merging the feature.
- **Before each demo or evaluation run**: re-run CHK014–CHK019 (idempotency) and CHK046–CHK049 (coverage). Any unchecked item blocks the demo.
- **For every PR that touches `packages/domain/src/domain/seed/` or `scripts/seed_loader.py`**: re-run CHK027–CHK033.

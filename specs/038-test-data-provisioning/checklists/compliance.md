# Compliance Checklist: Test Data and Resources Provisioning

**Purpose**: Operational acceptance gate for PII / PSPF / AU-residency / Indigenous-data placeholder enforcement before any seeded environment is exposed to demonstrators, evaluators, or auditors.
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)
**Scope**: FR-040..FR-046, FR-034, SC-002, SC-009, SC-011, SC-014, SC-015, A-7, A-8, A-9, A-10, A-17, A-18.

## Fictitious-Data Marker Enforcement

- [X] CHK001 Every JSON fixture file under the seed catalogue carries a top-level `_fixture` wrapper with `fictitious=true`, `residency=AU`, `licence=<spdx>`, and `schema_version` (FR-040, A-17).
- [X] CHK002 Every NDJSON file under `fixtures/sim_replays/` begins with a `{"_fixture_header": true, ...}` record carrying `fictitious=true`, `residency=AU`, `licence`, `scenario_id`, and `seed` (FR-040, A-17).
- [X] CHK003 Every code-generated artefact module exposes a module-level constant or file-prologue comment naming the generator id and version (FR-040, FR-052, A-17).
- [X] CHK004 Every persisted Cosmos document, generator return value, and simulator-bus payload carries `fictitious: true` at the document root (FR-040, A-17).
- [X] CHK005 Loader rejects any file whose wrapper or NDJSON header marker is missing, with an explicit error and zero partial load (FR-015, FR-040).
- [X] CHK006 Every persistence path verifies the record-level `fictitious=true` field before commit and refuses commit if absent (FR-040).

## Synthetic Naming (Persons)

- [X] CHK007 Every person name in seed records, generator output, and simulator-emitted messages is either `John Doe`-style synthetic or `[FICTITIOUS]`-prefixed (FR-041, A-9).
- [X] CHK008 No real operational personnel, real patient identifiers, or real political/ministerial actor names appear in any committed test-data artefact (FR-041, A-9).
- [X] CHK009 Evacuee, missing-person, volunteer, and triage records use only synthetic person identities (FR-041, FR-050, A-9).

## Australian Residency

- [X] CHK010 Every manifest entry carries `residency=AU` (FR-031, FR-042, A-8, SC-011).
- [X] CHK011 Manifest CI fails the build if any entry has `residency≠AU` (FR-032, SC-011).
- [X] CHK012 Every storage account, Cosmos account, and bus surface used by the seeded environment is provisioned in Azure Australia East or Australia Southeast (FR-042, A-8).
- [X] CHK013 No cross-region data movement of test data is configured (A-8, A-11).

## PSPF Marking Enforcement

- [X] CHK014 Every manifest entry carries a `pspf` marking, defaulting to `OFFICIAL` (FR-031, FR-043, A-7).
- [X] CHK015 Any entry marked `OFFICIAL: SENSITIVE` is enumerated in the manifest with a documented justification field populated (FR-043, A-7).
- [X] CHK016 Loader rejects any seed record carrying a marking of `PROTECTED` or above with an explicit error (FR-043, SC-011).
- [X] CHK017 Manifest CI fails the build if any entry exceeds `OFFICIAL: SENSITIVE` (FR-032, SC-011).

## Indigenous Cultural Data Placeholders

- [X] CHK018 No real Traditional Owner names, real sacred-site coordinates, or real community names appear in any seed file, NDJSON replay, generator output sample, or manifest entry (FR-044, A-10).
- [X] CHK019 All remote NT and remote WA community references are anonymised to the regional-zone level (FR-044, A-10).
- [X] CHK020 The denylist lint at `tools/lint/check_indigenous_placeholders.py` exists and is wired into the `quality` job in `.github/workflows/ci.yml` (FR-044, FR-032, A-18, A-19).
- [X] CHK021 The denylist data file at `tools/lint/data/indigenous_denylist.txt` exists and is reviewed by the cultural-authority custodians named in the manifest (FR-044, A-18).
- [X] CHK022 The manifest JSON Schema (`docs/test-data/manifest.schema.json`) declares `cultural_review_required: boolean` as a required field with default `false` (FR-044, A-18).
- [X] CHK023 The schema validator cross-checks that every entry whose region tag matches an Indigenous-context zone has `cultural_review_required=true` (FR-044, A-18, SC-015).
- [X] CHK024 The denylist lint runs against seed files, NDJSON replays, generator output samples, and manifest entries (not only the manifest) (FR-044, A-18).
- [X] CHK025 Manifest filter `cultural-review-required=true` returns 100% of artefacts whose context references an Indigenous-cultural zone (SC-015).

## Real-PII Detector Enforcement

- [X] CHK026 Loaders reject records matching real Australian residential address patterns combined with real personal phone or email patterns (FR-045).
- [X] CHK027 Loaders reject records matching real Medicare-number, real police-case-number, or real driver-licence patterns (FR-045).
- [X] CHK028 Generators reject record-generation requests whose output would match a documented real-PII detector (FR-045, FR-052).
- [X] CHK029 A deliberate negative test exists that feeds a record matching each detector and asserts loader/generator rejection (FR-045, SC-002).
- [X] CHK030 Manifest filter `pii=true` returns an empty result set (SC-011).

## Active-Warning Replication Prevention

- [X] CHK031 No simulator output replicates any currently-active real emergency warning text (FR-046).
- [X] CHK032 Every simulator message that structurally imitates a real warning format carries the literal string "TEST — DO NOT BROADCAST" in the message body (not only metadata) (FR-046).
- [X] CHK033 Every such simulator message carries `simulated: true` in the message body, not only in metadata (FR-046, FR-021).

## Public-Dataset Licence and Attribution

- [X] CHK034 Every public-dataset snapshot in the manifest has a populated SPDX-compatible licence identifier (FR-031, FR-034, SC-009).
- [X] CHK035 Every public-dataset snapshot has a populated attribution string suitable for the AMA "Acknowledgements" surface (FR-034, A-6).
- [X] CHK036 BoM, GA, ABS, AURIN, OpenStreetMap, and AIDR snapshots cite their respective open-data licences (CC BY, public domain, ODbL, CC BY) (A-6, FR-034).
- [X] CHK037 Manifest filter `category=public` returns only entries with non-empty `source_url`, `snapshot_date`, `dataset_version`, and SPDX licence (SC-009).
- [X] CHK038 The new `docs/test-data/MANIFEST.md` cross-references (does not duplicate) any artefact already listed in `docs/corpus/INDEXING-LICENCE-INVENTORY.md` (FR-035).

## Compliance Audit Readiness

- [X] CHK039 A first-time reviewer can enumerate every test-data artefact and identify the persona(s) it serves using only the manifest in under 30 minutes (SC-010).
- [X] CHK040 A persona-coverage report exists and flags every persona with zero entries (FR-033).

## How to Use

This checklist is an **operational gate**:
- **At end of `/speckit.plan`**: confirm CHK001–CHK006, CHK014–CHK017, CHK020–CHK023 are addressed by the plan's design (markers, schema field, denylist tool, CI wiring).
- **At end of `/speckit.implement`**: confirm CHK007–CHK013, CHK018–CHK019, CHK024–CHK038 pass against built artefacts before merge.
- **Before deployment of a seeded environment**: re-run all 40 items; **any unchecked item blocks deployment**. CHK001–CHK006, CHK016, CHK018, CHK026–CHK029, CHK031–CHK033 are non-negotiable and have no waiver path.

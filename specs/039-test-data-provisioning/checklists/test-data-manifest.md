# Test-Data Manifest Checklist: JSON + Schema, CI Lint, Provenance, Persona Binding

**Purpose**: Operational acceptance gate for the versioned test-data manifest — covering JSON manifest + JSON-Schema validation (CL-1), the CI lint hook in the existing `quality` job (CL-7 / FR-032), per-entry provenance/licence/snapshot/refresh fields, and persona-binding completeness.
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)
**Scope**: FR-030..FR-035, FR-060, SC-001, SC-003, SC-009, SC-010, SC-011, SC-014, SC-015, A-13, A-19.

## Manifest Existence and Format (CL-1)

- [X] CHK001 A human-readable manifest exists at `docs/test-data/MANIFEST.md` (FR-030, A-13).
- [X] CHK002 A canonical machine-readable companion exists at `docs/test-data/manifest.json` with one entry per test-data artefact (FR-030, A-13).
- [X] CHK003 A JSON Schema exists at `docs/test-data/manifest.schema.json` (FR-030, A-13).
- [X] CHK004 The Markdown manifest is auto-generated from the JSON companion (not hand-edited) (FR-030, A-13).
- [X] CHK005 The manifest enumerates 100% of test-data artefacts in the catalogued directories (FR-030, SC-003).

## JSON Schema Validation

- [X] CHK006 The schema declares `id`, `name`, `category`, `path`-or-`source_shape`, `persona_bindings`, `fictitious`, `pii`, `pspf`, `residency`, `licence`, `source_url`, `snapshot_date`, `dataset_version`, `refresh_policy`, `content_hash`, `created_or_updated`, and `cultural_review_required` as required fields (FR-031, FR-044, A-18).
- [X] CHK007 The schema constrains `category` to {synthetic, public, generator, mock, simulator-feed-shape, alert-template, persona-binding} (FR-031).
- [X] CHK008 The schema constrains `refresh_policy` to {static, refresh-on-public-dataset-update, regenerate-each-run} (FR-031).
- [X] CHK009 The schema constrains `pspf` to {`OFFICIAL`, `OFFICIAL: SENSITIVE`} and rejects higher markings (FR-043).
- [X] CHK010 The schema requires `fictitious=true` and rejects `fictitious=false` (FR-040).
- [X] CHK011 The schema requires `pii=false` and rejects `pii=true` (FR-045, SC-011).
- [X] CHK012 The schema requires `residency=AU` and rejects other values (FR-042, SC-011).
- [X] CHK013 The schema requires `persona_bindings` to be a non-empty array (FR-031, FR-060).
- [X] CHK014 The schema requires `licence` to be a valid SPDX identifier or the literal `proprietary-fictitious-internal` (FR-031, FR-034).
- [X] CHK015 For entries with `category=public`, the schema requires non-empty `source_url`, `snapshot_date`, and `dataset_version` (FR-031, SC-009).
- [X] CHK016 The schema cross-validates that any entry whose region tag matches an Indigenous-context zone has `cultural_review_required=true` (FR-044, A-18).
- [X] CHK017 The schema validator rejects malformed entries with explicit field-level error messages (FR-032).

## CI Lint Hook (CL-7 / A-19)

- [X] CHK018 The lint tool exists at `tools/lint/check_test_data_manifest.py` (FR-032, A-19).
- [X] CHK019 The lint tool is wired as a step into the existing `quality` job in `.github/workflows/ci.yml` (FR-032, A-19).
- [X] CHK020 No new workflow file is introduced for manifest validation (A-19, A-11).
- [X] CHK021 The same `quality` step also invokes the JSON Schema validator against `docs/test-data/manifest.json` (FR-032, A-19).
- [X] CHK022 The same `quality` step also invokes the Indigenous-placeholder lint at `tools/lint/check_indigenous_placeholders.py` (FR-032, FR-044, A-18, A-19).
- [X] CHK023 The CI check fails the build if any test-data artefact in the catalogued directories is missing from the manifest (FR-032, SC-003).
- [X] CHK024 The CI check fails the build if any required field on any manifest entry is empty (FR-032, SC-003).
- [X] CHK025 The CI check fails the build if any manifest entry references a non-existent artefact (FR-032).
- [X] CHK026 The CI check runs on every pull request (not only on cron) (A-19).
- [X] CHK027 The lint tool mirrors the established pattern of `tools/lint/check_licence_inventory.py` (FR-032, A-19).

## Provenance, Licence, Snapshot, Refresh Policy (Per Entry)

- [X] CHK028 Every manifest entry has a stable `id` and human-readable `name` (FR-031).
- [X] CHK029 Every manifest entry declares its `category` (FR-031).
- [X] CHK030 Every entry carries either `path` (file artefacts) or `source_shape` (simulator feeds) (FR-031).
- [X] CHK031 Every entry carries a `content_hash` for change detection (FR-031).
- [X] CHK032 Every entry carries a `created_or_updated` date (FR-031).
- [X] CHK033 Every entry carries a `refresh_policy` value (FR-031).
- [X] CHK034 Every public-dataset entry carries a populated `source_url` (FR-031, SC-009).
- [X] CHK035 Every public-dataset entry carries a populated `snapshot_date` (FR-031, SC-009).
- [X] CHK036 Every public-dataset entry carries a populated `dataset_version` (FR-031, SC-009).
- [X] CHK037 Every public-dataset entry carries a populated SPDX `licence` identifier (FR-031, FR-034, SC-009).
- [X] CHK038 Every public-dataset entry carries an attribution string suitable for the AMA "Acknowledgements" surface (FR-034).
- [X] CHK039 The system tolerates a snapshot file older than its recorded `snapshot_date` with a warning (not a failure) (Edge Case "Public-dataset snapshot drift").
- [X] CHK040 `snapshot_date` can be updated by editing the manifest alone (no code change required) (Edge Case "Public-dataset snapshot drift").

## Persona-Binding Completeness

- [X] CHK041 Every manifest entry carries ≥1 entry in `persona_bindings` (FR-031, FR-060).
- [X] CHK042 Each `persona_binding` carries `persona_id`, `domain_group`, and `binding_kind` (Key Entities — PersonaBinding).
- [X] CHK043 Every one of the 68 personas appears in `persona_bindings` of ≥1 manifest entry (FR-060, SC-001, A-4).
- [X] CHK044 A persona-coverage report is generated from the manifest and lists, per persona, the manifest entries serving it (FR-033, US3 acceptance scenario 5).
- [X] CHK045 The persona-coverage report flags every persona with zero entries (FR-033, SC-001).
- [X] CHK046 The persona-coverage CI check fails the build if any persona is unbacked (FR-033, SC-001).

## Manifest Filter Outcomes (Compliance)

- [X] CHK047 Manifest filter `pii=true` returns an empty result set (US3 acceptance scenario 3, SC-011).
- [X] CHK048 Manifest filter `residency≠AU` returns an empty result set (US3 acceptance scenario 4, SC-011).
- [X] CHK049 Manifest filter `pspf > OFFICIAL: SENSITIVE` returns an empty result set (FR-043, SC-011).
- [X] CHK050 Manifest filter `category=public AND any(source_url, snapshot_date, dataset_version, licence) is empty` returns an empty result set (US3 acceptance scenario 2, SC-009).
- [X] CHK051 Manifest filter for placeholder multilingual entries returns each as either translated body or `placeholder=true` with a "needs cultural-authority review" note (SC-014, FR-070).
- [X] CHK052 Manifest filter `cultural-review-required=true` covers 100% of artefacts whose region tag matches an Indigenous-context zone (SC-015, FR-044).

## Cross-Reference With Corpus Manifest

- [X] CHK053 The new `docs/test-data/MANIFEST.md` cross-references (does not duplicate) entries that also appear in `docs/corpus/INDEXING-LICENCE-INVENTORY.md` (FR-035).
- [X] CHK054 Modifying a corpus entry that is also a test-data input updates the cross-reference (or fails CI if stale) (FR-035, FR-032).

## Reviewer Walkthrough

- [X] CHK055 A first-time reviewer can, using only the manifest and the inventory document, enumerate every test-data artefact and identify the persona(s) it serves in under 30 minutes (SC-010).
- [X] CHK056 A documented walkthrough exists that exercises CHK055 and is rerun on every major change (SC-010).

## How to Use

This checklist is an **operational gate**:
- **At end of `/speckit.plan`**: confirm CHK001–CHK022 (manifest format, schema design, CI wiring) are part of the plan.
- **At end of `/speckit.implement`**: confirm CHK023–CHK054 (CI behaviour, per-entry fields, filter outcomes, cross-references) all pass before merge.
- **Per PR that adds or modifies a test-data artefact**: confirm a corresponding manifest entry was added/updated and CHK023–CHK025 pass.
- **Quarterly compliance review**: re-run CHK043–CHK046 (persona coverage), CHK047–CHK052 (compliance filters), CHK055–CHK056 (reviewer walkthrough).
- CHK018–CHK022 are non-negotiable CI integration gates; CHK006–CHK017 are non-negotiable schema gates.

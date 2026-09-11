# Test-Data Manifest (Spec 039)

> **Auto-generated** from `docs/test-data/manifest.json` by
> `tools/lint/render_test_data_manifest_md.py`.
> Do not edit by hand — re-run the renderer instead.

This document is the human-readable view of the canonical machine-readable
manifest enumerating every test-data artefact in the AMA repository.
Validation lives in `tools/lint/check_test_data_manifest.py` and is wired
into the `quality` job of `.github/workflows/ci.yml` (CL-7).

Cross-references:

- Corpus inventory: [`docs/corpus/MANIFEST.md`](../corpus/MANIFEST.md)
- Indexing licence inventory: [`docs/corpus/INDEXING-LICENCE-INVENTORY.md`](../corpus/INDEXING-LICENCE-INVENTORY.md)
- Schema: [`manifest.schema.json`](./manifest.schema.json)
- Indigenous placeholder denylist:
  [`tools/lint/data/indigenous_denylist.txt`](../../tools/lint/data/indigenous_denylist.txt)


## Summary

- Schema version: `1.0.0`
- Total entries: **2**
- `mock`: 1
- `synthetic`: 1

## Category: `mock`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `x-001` | `fixtures/x1.json` | `cross-sector` | incident-commander | `OFFICIAL-DRIFT` | `proprietary-fictitious-internal` | no |

## Category: `synthetic`

| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |
|---|---|---|---|---|---|---|
| `y-001` | `fixtures/y1.json` | `ambulance` | operations-officer | `OFFICIAL` | `CC-BY-4.0` | no |

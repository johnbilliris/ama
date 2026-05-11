"""T113 — Contract test for OfflineCacheManifest schema (Spec 036 / FR-RAG-LS-02).

Round-trip JSON Schema 2020-12 validation against
``packages/schemas/spec_036/offline-cache-manifest.json``. Exercises:

* The happy-path manifest from the schema's own ``examples[0]`` (must validate).
* The 500 MB hard cap (``size_bytes_total > 524_288_000`` → invalid).
* The dual-signature requirement (missing ``cosign_keyless`` or ``age_detached``
  → invalid; both missing ⇒ R-07 fail-closed default).
* The 14-day TTL / 11-day stale-warning constants (any other value → invalid).
* Jurisdiction enum closed-set (rejects unknown jurisdictions).
* Embedding-model homogeneity is enforced at the entry-collection layer
  (T114) — here we only validate the manifest-level schema shape.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "packages" / "schemas" / "spec_036" / "offline-cache-manifest.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(payload: dict, schema: dict) -> list[str]:
    """Return the list of validation errors (empty on success)."""
    import jsonschema  # type: ignore[import-untyped]

    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
    return [e.message for e in validator.iter_errors(payload)]


def _example() -> dict:
    schema = _load_schema()
    examples = schema.get("examples") or []
    assert examples, "offline-cache-manifest.json must carry at least one example"
    return copy.deepcopy(examples[0])


def test_happy_path_example_validates() -> None:
    schema = _load_schema()
    payload = _example()
    errors = _validate(payload, schema)
    assert errors == [], f"happy-path example failed validation: {errors}"


def test_size_cap_500mb_enforced() -> None:
    schema = _load_schema()
    payload = _example()
    payload["size_bytes_total"] = 524_288_001  # one byte over 500 MB
    errors = _validate(payload, schema)
    assert errors, "manifest > 500 MB MUST fail validation (FR-RAG-LS-02)"


def test_size_cap_below_minimum_rejected() -> None:
    schema = _load_schema()
    payload = _example()
    payload["size_bytes_total"] = 0
    errors = _validate(payload, schema)
    assert errors


def test_ttl_must_be_14_days() -> None:
    schema = _load_schema()
    payload = _example()
    payload["ttl_days"] = 7  # any other value
    errors = _validate(payload, schema)
    assert errors, "ttl_days != 14 MUST fail (R-07 hard expiry)"


def test_stale_warning_must_be_11_days() -> None:
    schema = _load_schema()
    payload = _example()
    payload["stale_warning_days"] = 10
    errors = _validate(payload, schema)
    assert errors, "stale_warning_days != 11 MUST fail (R-07)"


def test_signatures_require_cosign_keyless() -> None:
    schema = _load_schema()
    payload = _example()
    del payload["signatures"]["cosign_keyless"]
    errors = _validate(payload, schema)
    assert errors, "missing cosign_keyless MUST fail (R-07 dual-sign fail-closed)"


def test_signatures_require_age_detached() -> None:
    schema = _load_schema()
    payload = _example()
    del payload["signatures"]["age_detached"]
    errors = _validate(payload, schema)
    assert errors, "missing age_detached MUST fail (R-07 dual-sign fail-closed)"


def test_unknown_jurisdiction_rejected() -> None:
    schema = _load_schema()
    payload = _example()
    payload["entries"][0]["jurisdiction"] = "xx"  # not in the closed set
    errors = _validate(payload, schema)
    assert errors


def test_corpus_build_sha_must_be_64_hex() -> None:
    schema = _load_schema()
    payload = _example()
    payload["corpus_build_sha"] = "deadbeef"  # too short
    errors = _validate(payload, schema)
    assert errors


def test_extra_top_level_fields_rejected() -> None:
    schema = _load_schema()
    payload = _example()
    payload["secret"] = "leak"  # additionalProperties: false
    errors = _validate(payload, schema)
    assert errors, "extra top-level fields MUST fail (additionalProperties: false)"


def test_zero_entries_rejected() -> None:
    schema = _load_schema()
    payload = _example()
    payload["entries"] = []
    errors = _validate(payload, schema)
    assert errors, "empty entries[] MUST fail (minItems=1)"

"""Spec-039 T014: tests for fictitious-data marker validator (FR-040)."""

from __future__ import annotations

import pytest

from packages.domain.src.domain.seed._fixture_marker import (
    FixtureMarkerError,
    validate_ndjson_header,
    validate_record,
    validate_wrapper,
)

GOOD_PAYLOAD = {
    "fictitious": True,
    "residency": "AU",
    "licence": "CC-BY-4.0",
    "schema_version": "1",
}


def test_valid_wrapper_passes():
    validate_wrapper({"_fixture": GOOD_PAYLOAD, "records": []})


def test_wrapper_missing_key_raises():
    with pytest.raises(FixtureMarkerError) as exc:
        validate_wrapper({"records": []})
    assert exc.value.field == "_fixture"


def test_wrapper_missing_fictitious_raises():
    bad = dict(GOOD_PAYLOAD)
    del bad["fictitious"]
    with pytest.raises(FixtureMarkerError) as exc:
        validate_wrapper({"_fixture": bad})
    assert exc.value.field == "fictitious"


def test_wrapper_wrong_residency_raises():
    bad = dict(GOOD_PAYLOAD, residency="US")
    with pytest.raises(FixtureMarkerError) as exc:
        validate_wrapper({"_fixture": bad})
    assert exc.value.field == "residency"


def test_wrapper_missing_licence_raises():
    bad = dict(GOOD_PAYLOAD)
    del bad["licence"]
    with pytest.raises(FixtureMarkerError) as exc:
        validate_wrapper({"_fixture": bad})
    assert exc.value.field == "licence"


def test_wrapper_missing_schema_version_raises():
    bad = dict(GOOD_PAYLOAD)
    del bad["schema_version"]
    with pytest.raises(FixtureMarkerError) as exc:
        validate_wrapper({"_fixture": bad})
    assert exc.value.field == "schema_version"


def test_valid_ndjson_header_passes():
    validate_ndjson_header({"_fixture_header": True, **GOOD_PAYLOAD})


def test_ndjson_header_missing_flag_raises():
    with pytest.raises(FixtureMarkerError) as exc:
        validate_ndjson_header(dict(GOOD_PAYLOAD))
    assert exc.value.field == "_fixture_header"


def test_valid_record_passes():
    validate_record({"id": "x", "fictitious": True, "residency": "AU"})


def test_record_missing_fictitious_raises():
    with pytest.raises(FixtureMarkerError) as exc:
        validate_record({"id": "x", "residency": "AU"})
    assert exc.value.field == "fictitious"


def test_record_missing_residency_raises():
    with pytest.raises(FixtureMarkerError) as exc:
        validate_record({"id": "x", "fictitious": True})
    assert exc.value.field == "residency"

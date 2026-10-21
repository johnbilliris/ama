from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tests.load.spec006_load_payload import build_canonical_ingest_payload, load_catalogue_source_ids


def _schema_validator() -> Draft202012Validator:
    schema = json.loads(Path("packages/schemas/signal-envelope.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema=schema, format_checker=FormatChecker())


def test_local_harness_payload_passes_schema_and_catalogue_eligibility() -> None:
    source_ids = load_catalogue_source_ids()
    assert "bom-warnings" in source_ids

    payload = build_canonical_ingest_payload(source_id="bom-warnings", incident_id="inc-1")
    _schema_validator().validate(payload)
    assert payload["source"]["dataSourceId"] in source_ids


def test_local_harness_payload_rejects_unknown_source_in_fake_eligibility_path() -> None:
    source_ids = load_catalogue_source_ids()
    payload = build_canonical_ingest_payload(source_id="unknown-source", incident_id="inc-1")
    _schema_validator().validate(payload)
    assert payload["source"]["dataSourceId"] not in source_ids

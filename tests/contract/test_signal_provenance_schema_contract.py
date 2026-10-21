import json
from pathlib import Path

from app.services.dashboard_service import DashboardService
from jsonschema import Draft202012Validator, FormatChecker

from packages.domain.src.domain.models.signal import Signal

_SCHEMA_PATH = Path("packages/schemas/signal-envelope.schema.json")


def _validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema=schema, format_checker=FormatChecker())


def _sample_envelope(source_kind: str, data_source_id: str) -> dict:
    return {
        "source": {
            "dataSourceId": data_source_id,
            "name": f"Source {data_source_id}",
            "kind": source_kind,
        },
        "category": "weather",
        "occurredAt": "2026-03-25T10:00:00Z",
        "receivedAt": "2026-03-25T10:00:20Z",
        "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        "payload": {},
        "confidenceScore": 0.8,
        "freshnessScore": 0.95,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": "https://example.test/source",
            "sourceTimestamp": "2026-03-25T10:00:00Z",
            "sourceName": f"Source {data_source_id}",
            "sourceKind": source_kind,
            "trustTier": "tier_1_authoritative_government",
            "evaluatedConfidenceScore": 0.8,
            "sourceStatus": "available",
            "sourceReason": "available",
            "expectedUpdateSeconds": 300,
            "rawPayloadUri": "raw-payloads/test/2026-03-25/sig-1.json",
            "owningAgencyId": "agency-1",
        },
    }


def test_provenance_keys_read_by_code_are_schema_permitted() -> None:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    provenance_properties = set(schema["properties"]["provenance"]["properties"].keys())

    keys_read_in_code = {
        "collectionMethod",
        "sourceUri",
        "collector",
        "validationNotes",
        "sourceTimestamp",
        "simulationRunId",
        "sourceName",
        "sourceKind",
        "trustTier",
        "evaluatedConfidenceScore",
        "sourceStatus",
        "sourceReason",
        "expectedUpdateSeconds",
        "rawPayloadUri",
        "owningAgencyId",
    }

    missing = keys_read_in_code - provenance_properties
    assert not missing


def test_source_classes_roundtrip_schema_signal_dashboard_flags() -> None:
    validator = _validator()
    source_kinds = ["authoritative", "sensor", "field_report", "community", "social"]

    for index, kind in enumerate(source_kinds, start=1):
        envelope = _sample_envelope(kind, f"source-{index}")
        validator.validate(envelope)

        signal = Signal(
            signal_id=f"sig-{index}",
            incident_id="inc-1",
            data_source_id=envelope["source"]["dataSourceId"],
            category=envelope["category"],
            occurred_at=envelope["occurredAt"],
            received_at=envelope["receivedAt"],
            jurisdiction_id="nsw",
            location=envelope["location"],
            payload=envelope["payload"],
            owning_agency_id="agency-1",
            source_name=envelope["source"]["name"],
            source_kind=kind,
            trust_tier=envelope["provenance"]["trustTier"],
            source_timestamp=envelope["provenance"]["sourceTimestamp"],
            raw_payload_uri=envelope["provenance"]["rawPayloadUri"],
            classification="official",
            pii_fields=[],
            retention_until="2026-03-26T10:00:00Z",
            confidence_score=envelope["confidenceScore"],
            freshness_score=envelope["freshnessScore"],
            validation_status=envelope["validationStatus"],
            provenance=envelope["provenance"],
        )

        if kind in {"community", "social"}:
            assert DashboardService._is_community_signal(signal)
        else:
            assert DashboardService._is_authoritative_signal(signal)

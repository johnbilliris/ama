from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

_CATALOGUE_PATH = Path("packages/domain/src/domain/seed/data_sources_australia.json")


def load_catalogue_source_ids() -> set[str]:
    rows = json.loads(_CATALOGUE_PATH.read_text(encoding="utf-8"))
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("data_source_id", "")).strip()
        if source_id:
            ids.add(source_id)
    return ids


def build_canonical_ingest_payload(*, source_id: str, incident_id: str) -> dict[str, object]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "source": {"dataSourceId": source_id, "name": source_id, "kind": "authoritative"},
        "incidentId": incident_id,
        "category": "weather",
        "occurredAt": now,
        "receivedAt": now,
        "jurisdictionId": "nsw",
        "location": {
            "type": "Point",
            "coordinates": [151.21, -33.86],
            "precisionMeters": 100,
        },
        "payload": {"headline": "load-harness", "severity": "watch"},
        "confidenceScore": 0.95,
        "freshnessScore": 1.0,
        "validationStatus": "pending",
        "provenance": {
            "collectionMethod": "api_push",
            "sourceUri": "load://spec006/locust",
        },
    }

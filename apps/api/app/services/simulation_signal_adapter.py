from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.validators.signal_envelope import SignalEnvelope

from packages.domain.src.domain.models.signal import Signal


def template_entry_to_signal(
    signal_envelope: dict[str, Any],
    *,
    tenant_id: str,
    offset_seconds: int | float,
    exercise_start: datetime,
) -> Signal:
    raw = deepcopy(signal_envelope)
    source_payload = raw.get("source") if isinstance(raw.get("source"), dict) else {}
    provenance_payload = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
    data_source_id = str(
        source_payload.get("dataSourceId")
        or raw.get("data_source_id")
        or provenance_payload.get("source")
        or "simulation-source"
    )
    source_kind = str(source_payload.get("kind") or _source_kind(data_source_id, raw.get("category")))
    occurred_at = _timestamp(raw.get("occurredAt") or raw.get("occurred_at")) or (
        exercise_start + timedelta(seconds=float(offset_seconds))
    )
    received_at = _timestamp(raw.get("receivedAt") or raw.get("received_at")) or occurred_at
    location = deepcopy(raw.get("location") or {"type": "Point", "coordinates": [0.0, 0.0]})
    location.setdefault("precisionMeters", 1000.0)
    jurisdiction_id = str(raw.get("jurisdictionId") or raw.get("jurisdiction_id") or "national").lower()
    confidence = float(raw.get("confidenceScore", raw.get("confidence_score", 0.5)))
    freshness = float(raw.get("freshnessScore", raw.get("freshness_score", 1.0)))
    validation_status = str(raw.get("validationStatus", raw.get("validation_status", "pending")))
    signal_id = str(raw.get("signalId") or raw.get("signal_id") or raw.get("id") or f"sig-{uuid4().hex[:12]}")
    category = _category(str(raw.get("category", "community_report")))

    envelope = SignalEnvelope.model_validate(
        {
            "source": {
                "dataSourceId": data_source_id,
                "name": str(source_payload.get("name") or data_source_id),
                "kind": source_kind,
            },
            "incidentId": raw.get("incidentId") or raw.get("incident_id"),
            "category": category,
            "occurredAt": occurred_at,
            "receivedAt": received_at,
            "jurisdictionId": jurisdiction_id,
            "location": location,
            "payload": deepcopy(raw.get("payload") or {}),
            "confidenceScore": confidence,
            "freshnessScore": freshness,
            "validationStatus": validation_status,
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": str(
                    provenance_payload.get("sourceUri")
                    or provenance_payload.get("source")
                    or f"simulation://{tenant_id}/{data_source_id}"
                ),
                "simulationRunId": tenant_id.removeprefix("sim-"),
                "sourceName": str(source_payload.get("name") or data_source_id),
                "sourceKind": source_kind,
            },
        }
    )

    return Signal(
        signal_id=signal_id,
        incident_id=envelope.incidentId,
        data_source_id=envelope.source.dataSourceId,
        category=envelope.category,
        occurred_at=envelope.occurredAt,
        received_at=envelope.receivedAt,
        jurisdiction_id=envelope.jurisdictionId,
        location=envelope.location.model_dump(),
        payload=envelope.payload,
        source_name=envelope.source.name,
        source_kind=envelope.source.kind,
        trust_tier=_trust_tier(source_kind),
        source_timestamp=envelope.occurredAt,
        classification="public" if source_kind in {"social", "community"} else "official",
        retention_until=envelope.receivedAt + timedelta(days=90),
        confidence_score=envelope.confidenceScore,
        freshness_score=envelope.freshnessScore,
        validation_status=envelope.validationStatus,
        provenance=envelope.provenance.model_dump(mode="json"),
    )


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if value is None or not str(value).strip():
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)


def _source_kind(data_source_id: str, category: Any) -> str:
    source = data_source_id.lower()
    category_text = str(category or "").lower()
    if "twitter" in source or "facebook" in source or "reddit" in source or category_text == "social_report":
        return "social"
    if "community" in source or "snap" in source or category_text == "community_report":
        return "community"
    if any(token in source for token in ("sensor", "gauge", "observation", "aws")):
        return "sensor"
    if any(token in source for token in ("field", "webeoc", "icon")):
        return "field_report"
    return "authoritative"


def _category(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return {
        "bushfire": "fire",
        "flood": "hydrology",
        "cyclone": "weather",
        "storm": "weather",
        "severe_storm": "weather",
        "heat": "weather",
        "heatwave": "weather",
        "earthquake": "geohazard",
        "tsunami": "geohazard",
    }.get(normalized, normalized)


def _trust_tier(source_kind: str) -> str:
    return {
        "authoritative": "tier_1_authoritative_government",
        "sensor": "tier_3_operational_sensor",
        "iot": "tier_3_operational_sensor",
        "field_report": "tier_2_verified_institutional",
        "social": "tier_5_unverified_public",
        "community": "tier_5_unverified_public",
        "derived": "tier_7_derived_computed",
    }[source_kind]

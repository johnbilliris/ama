from __future__ import annotations

from typing import Any

from packages.domain.src.domain.models.signal import Signal


def to_signal_document(signal: Signal, scope: str, *, document_id: str | None = None) -> dict[str, Any]:
    jurisdiction_id = signal.jurisdiction_id or "national"
    doc = signal.model_dump(mode="json")
    doc["id"] = document_id or signal.signal_id
    doc["scope"] = scope
    doc["jurisdictionId"] = jurisdiction_id
    doc["dataSourceId"] = signal.data_source_id
    doc["owningAgencyId"] = signal.owning_agency_id
    doc["partitionKey"] = f"{scope}/{jurisdiction_id}/{signal.data_source_id}"
    return doc


def partition_key_of(document: dict[str, Any]) -> list[str]:
    return [
        str(document["scope"]),
        str(document["jurisdictionId"]),
        str(document["dataSourceId"]),
    ]

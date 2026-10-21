from __future__ import annotations

from typing import Any

AU_REGIONS = frozenset({"australiaeast", "australiasoutheast"})


class NonAuRegionError(ValueError):
    def __init__(self, region: str | None) -> None:
        display = region or "<missing>"
        super().__init__(f"Region {display!r} is not an approved AU region.")
        self.region = region


def assert_au_region(
    payload: dict[str, Any] | Any,
    *,
    actor: str | None = None,
    correlation_id: str | None = None,
) -> None:
    region = payload.get("region") if isinstance(payload, dict) else getattr(payload, "region", None)
    if region in AU_REGIONS:
        return

    from .instrumentation.audit_manager import record

    value_id = str(payload.get("id", "unknown") if isinstance(payload, dict) else getattr(payload, "id", "unknown"))
    payload_actor = payload.get("actor") if isinstance(payload, dict) else getattr(payload, "actor", None)
    record(
        kind="non_au_signal_refused",
        value_id=value_id,
        actor=actor or str(payload_actor or "system"),
        payload={"rejected_region": region or "<missing>"},
        correlation_id=correlation_id
        or (
            str(payload.get("correlation_id", ""))
            if isinstance(payload, dict)
            else str(getattr(payload, "correlation_id", ""))
        ),
    )
    raise NonAuRegionError(region)


def coerce_advisory_only_for_low_band(signal_dict: dict[str, Any]) -> dict[str, Any]:
    confidence = signal_dict.get("confidence", {})
    value = (
        float(confidence.get("value", 1.0))
        if isinstance(confidence, dict)
        else float(getattr(confidence, "value", 1.0))
    )
    if value < 0.50:
        signal_dict["advisory_only"] = True
        signal_dict["reduced_fidelity"] = True
    return signal_dict

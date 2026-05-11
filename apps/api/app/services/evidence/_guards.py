"""Cross-pillar guards (Phase 2 foundational).

Implements:
    - T-S11 AU-region write guard (FR-029, SC-009)
    - T-S15 advisory-only banner enforcement (FR-024 / FR-030)

Audit emissions go through `instrumentation.audit_manager` to keep
the append-only invariant centralised.
"""

from __future__ import annotations

from typing import Any

AU_REGIONS = frozenset({"australiaeast", "australiasoutheast"})


class NonAuRegionError(ValueError):
    """Raised when a write attempts to land outside the AU region set."""

    def __init__(self, region: str) -> None:
        super().__init__(f"Region {region!r} is not AU-sovereign — only {sorted(AU_REGIONS)} accepted (FR-029)")
        self.region = region


def assert_au_region(payload: dict[str, Any] | Any) -> None:
    """Reject any write with a non-AU `region` field.

    Side-effect: emits an `evidence_audit` entry with `kind=non_au_signal_refused`
    via the audit manager, so refusals are themselves auditable (SC-009).
    """
    region = payload.get("region") if isinstance(payload, dict) else getattr(payload, "region", None)
    if region is None:
        # Some entities (e.g. KPI ladder rows) carry no region; nothing to check.
        return
    if region not in AU_REGIONS:
        # Best-effort audit log; never block on logging errors.
        try:
            from .instrumentation.audit_manager import record  # noqa: WPS433

            record(
                kind="non_au_signal_refused",
                value_id=str(payload.get("id") if isinstance(payload, dict) else getattr(payload, "id", "unknown")),
                actor="system",
                payload={"region": region},
                references={},
                region="australiaeast",  # the audit row itself lives in AU
            )
        except Exception:  # pragma: no cover — defence-in-depth only
            pass
        raise NonAuRegionError(region)


def coerce_advisory_only_for_low_band(signal_dict: dict[str, Any]) -> dict[str, Any]:
    """T-S15 — when confidence band is `low`, force advisory_only + reduced_fidelity.

    Mutates and returns the same dict for caller convenience.
    """
    conf = signal_dict.get("confidence", {})
    value = float(conf.get("value", 1.0)) if isinstance(conf, dict) else float(getattr(conf, "value", 1.0))
    if value < 0.50:
        signal_dict["advisory_only"] = True
        signal_dict["reduced_fidelity"] = True
    return signal_dict

# KPI ladder publication gates and materialised views.

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime

from ..instrumentation import audit_manager
from ..models.kpi import CapstoneScId, IndicatorDefinition, KpiLadderGroup, KpiLadderView
from .rank import life_safety_first
from .repository import list_published, publish

CAPSTONE_IDS: tuple[CapstoneScId, ...] = (
    "SC-CAP-015-001",
    "SC-CAP-015-002",
    "SC-CAP-015-003",
    "SC-CAP-015-004",
    "SC-CAP-015-005",
)


class ManualShareBlocked(PermissionError):
    pass


class CapstoneCoverageError(ValueError):
    pass


class EdgeCase5Error(ValueError):
    pass


def _has_auditor_signoff(
    value_id: str,
    *,
    artifact_version: str,
    artifact_hash: str,
) -> bool:
    from .._clients import get_registry

    rows = get_registry().get("evidence_audit").all()
    return any(
        row.get("kind") == "auditor_signoff_recorded"
        and row.get("value_id") == value_id
        and row.get("actor") not in {"system", "seed", "anonymous"}
        and row.get("payload", {}).get("authenticated") is True
        and row.get("payload", {}).get("artifact_version") == artifact_version
        and row.get("payload", {}).get("artifact_hash") == artifact_hash
        and row.get("payload", {}).get("auditor_id") == row.get("actor")
        and row.get("payload", {}).get("approval_id")
        for row in rows
    )


def manual_share(indicators: Iterable[IndicatorDefinition]) -> float:
    # Replacement versions count once by stable KPI identity.
    by_kpi = {indicator.kpi_id: indicator for indicator in indicators}
    if not by_kpi:
        return 0.0
    return sum(_is_manual(indicator) for indicator in by_kpi.values()) / len(by_kpi)


def _is_manual(indicator: IndicatorDefinition) -> bool:
    risk = indicator.risk_adjustment
    return (
        indicator.provenance == "manual" or risk is None or risk.provenance == "manual" or risk.auditor_signoff_required
    )


def candidate_snapshot_metadata(
    indicators: Iterable[IndicatorDefinition],
) -> tuple[str, str]:
    by_kpi = {indicator.kpi_id: indicator for indicator in indicators}
    payload = [
        indicator.model_dump(
            mode="json",
            exclude={"created_at", "created_by"},
        )
        for indicator in sorted(by_kpi.values(), key=lambda item: item.kpi_id)
    ]
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    artifact_hash = hashlib.sha256(canonical).hexdigest()
    artifact_version = f"{max((item.version for item in by_kpi.values()), default=0)}:{len(by_kpi)}"
    return artifact_version, artifact_hash


def record_auditor_signoff(
    *,
    artefact_id: str,
    indicators: Iterable[IndicatorDefinition],
    auditor_id: str,
    approval_id: str,
    basis: str,
    correlation_id: str = "",
) -> None:
    if auditor_id in {"", "system", "seed", "anonymous"}:
        raise PermissionError("authenticated named auditor identity is required")
    if not approval_id.strip() or len(basis.strip()) < 8:
        raise ValueError("approval_id and a substantive basis are required")
    artifact_version, artifact_hash = candidate_snapshot_metadata(indicators)
    audit_manager.record(
        kind="auditor_signoff_recorded",
        value_id=artefact_id,
        actor=auditor_id,
        payload={
            "authenticated": True,
            "auditor_id": auditor_id,
            "approval_id": approval_id,
            "artifact_version": artifact_version,
            "artifact_hash": artifact_hash,
            "basis": basis,
        },
        correlation_id=correlation_id,
    )


def publish_indicator(
    indicator: IndicatorDefinition,
    *,
    artefact_id: str = "kpi_ladder",
    actor: str = "system",
    correlation_id: str = "",
) -> IndicatorDefinition:
    current = {published.kpi_id: published for published in list_published()}
    current[indicator.kpi_id] = indicator
    candidate = list(current.values())
    share = manual_share(candidate)
    artifact_version, artifact_hash = candidate_snapshot_metadata(candidate)
    if share > 0.5 and not _has_auditor_signoff(
        artefact_id,
        artifact_version=artifact_version,
        artifact_hash=artifact_hash,
    ):
        audit_manager.record(
            kind="manual_share_blocked",
            value_id=artefact_id,
            actor=actor,
            payload={
                "manual_share_pct": share * 100.0,
                "artifact_version": artifact_version,
                "artifact_hash": artifact_hash,
            },
            correlation_id=correlation_id,
        )
        raise ManualShareBlocked(f"manual share {share:.2%} exceeds 50% — named auditor sign-off required")
    published = publish(indicator)
    audit_manager.record(
        kind="ladder_version_published",
        value_id=published.id,
        actor=actor,
        payload={
            "kpi_id": published.kpi_id,
            "version": published.version,
            "artifact_version": artifact_version,
            "artifact_hash": artifact_hash,
        },
        correlation_id=correlation_id,
    )
    return published


def assemble_ladder_view(
    *,
    capstone_sc_id: CapstoneScId | None = None,
    include_risk_adjusted: bool = True,
) -> KpiLadderView:
    indicators = list_published()
    requested = (capstone_sc_id,) if capstone_sc_id is not None else CAPSTONE_IDS
    groups: list[KpiLadderGroup] = []
    for sc_id in requested:
        leading = life_safety_first(
            indicator for indicator in indicators if indicator.capstone_sc_id == sc_id and indicator.kind == "leading"
        )
        lagging = life_safety_first(
            indicator for indicator in indicators if indicator.capstone_sc_id == sc_id and indicator.kind == "lagging"
        )
        if not leading or not lagging:
            raise CapstoneCoverageError(
                f"{sc_id} requires at least one leading and one lagging indicator; have {len(leading)}/{len(lagging)}"
            )
        if include_risk_adjusted:
            missing = [indicator.kpi_id for indicator in (*leading, *lagging) if indicator.risk_adjustment is None]
            if missing:
                raise EdgeCase5Error(f"risk-adjusted variant unavailable for {sorted(missing)}")
        groups.append(KpiLadderGroup(capstone_sc_id=sc_id, leading=leading, lagging=lagging))
    return KpiLadderView(
        version=str(max((indicator.version for indicator in indicators), default=1)),
        generated_at=datetime.now(UTC),
        groups=groups,
    )

"""Pillar A — KPI ladder Manager (T-A06, FR-001/004/028, SC-001/010).

Publish flow:
    - Validates ≥1 leading + ≥1 lagging per `capstone_sc_id` (SC-001).
    - Manual-share gate: refuses when manual provenance > 50 % per artefact
      unless an `auditor_signoff_recorded` audit row exists (FR-028 / SC-010).
    - Risk-adjusted twin: value × (L×C)/25 for indicators with a matrix.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from ..instrumentation import audit_manager
from ..models.kpi import (
    CapstoneScId,
    IndicatorDefinition,
    KpiLadderGroup,
    KpiLadderView,
)
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
    """Raised when manual-share > 50% and no auditor sign-off is on file."""


class CapstoneCoverageError(ValueError):
    """Raised when the ladder cannot satisfy ≥1 leading + ≥1 lagging per SC."""


def _has_auditor_signoff(value_id: str) -> bool:
    """Look for an `auditor_signoff_recorded` audit entry for this artefact."""
    from .._clients import get_registry  # late import to keep cycles clean

    rows = get_registry().get("evidence_audit").all()
    return any(r.get("kind") == "auditor_signoff_recorded" and r.get("value_id") == value_id for r in rows)


def manual_share(indicators: Iterable[IndicatorDefinition]) -> float:
    items = list(indicators)
    if not items:
        return 0.0
    return sum(1 for i in items if i.provenance == "manual") / len(items)


def publish_indicator(
    indicator: IndicatorDefinition,
    *,
    artefact_id: str = "kpi_ladder",
    actor: str = "system",
    correlation_id: str = "",
) -> IndicatorDefinition:
    """Publish a single indicator with manual-share gate (FR-028)."""
    candidate_set = list_published() + [indicator]
    share = manual_share(candidate_set)
    if share > 0.5 and not _has_auditor_signoff(artefact_id):
        audit_manager.record(
            kind="manual_share_blocked",
            value_id=artefact_id,
            actor=actor,
            payload={"manual_share_pct": share * 100.0},
            correlation_id=correlation_id,
        )
        raise ManualShareBlocked(f"manual share {share:.2%} exceeds 50% — auditor sign-off required (FR-028 / SC-010)")
    out = publish(indicator)
    audit_manager.record(
        kind="ladder_version_published",
        value_id=out.id,
        actor=actor,
        payload={"kpi_id": out.kpi_id, "version": out.version},
        correlation_id=correlation_id,
    )
    return out


def assemble_ladder_view(
    *,
    capstone_sc_id: CapstoneScId | None = None,
    include_risk_adjusted: bool = True,
) -> KpiLadderView:
    """Materialise the ladder view; raises if missing risk-adjusted matrix."""
    indicators = list_published()
    groups: list[KpiLadderGroup] = []
    for sc in CAPSTONE_IDS:
        leading = life_safety_first(i for i in indicators if i.capstone_sc_id == sc and i.kind == "leading")
        lagging = life_safety_first(i for i in indicators if i.capstone_sc_id == sc and i.kind == "lagging")
        if not leading or not lagging:
            raise CapstoneCoverageError(
                f"{sc} requires ≥1 leading and ≥1 lagging (SC-001); have {len(leading)}/{len(lagging)}"
            )
        if include_risk_adjusted:
            for i in (*leading, *lagging):
                if i.risk_adjustment is None:
                    raise EdgeCase5Error(
                        f"indicator {i.kpi_id} has no risk-adjustment matrix; "
                        f"use include_risk_adjusted=false to retrieve unadjusted variant (FR-004 / Edge Case #5)"
                    )
        groups.append(KpiLadderGroup(capstone_sc_id=sc, leading=leading, lagging=lagging))
    return KpiLadderView(
        version=str(max((i.version for i in indicators), default=1)),
        generated_at=datetime.now(UTC),
        groups=groups,
    )


class EdgeCase5Error(ValueError):
    """FR-004 / Edge Case #5 — returned as HTTP 409."""

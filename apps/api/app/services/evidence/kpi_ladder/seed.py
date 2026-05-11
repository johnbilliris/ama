"""Pillar A — KPI ladder seed data (used by unit/contract tests + dev quickstart).

Provides ≥1 leading + ≥1 lagging indicator per capstone SC, plus the
Public Information indicators consumed by US7.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from ..models.kpi import (
    AiimsFunction,
    CapstoneScId,
    ConfidenceBandRule,
    IncidentLevel,
    IndicatorDefinition,
    IndicatorKind,
    LifeSafetyTier,
    Provenance,
    RiskAdjustment,
)


def _id() -> str:
    return secrets.token_hex(13)


def _make(
    *,
    kpi_id: str,
    name: str,
    kind: IndicatorKind,
    sc: CapstoneScId,
    aiims: AiimsFunction = "Operations",
    level: IncidentLevel = 2,
    tier: LifeSafetyTier = "life_safety",
    formula: str = "value",
    unit: str = "count",
    target: float = 100.0,
    threshold: float = 80.0,
    cadence: str = "PT15M",
    baseline: str = "spec-015 prototype baseline",
    provenance: Provenance = "auto",
    risk: tuple[int, int] | None = None,
    owner: str = "RiskManager",
) -> IndicatorDefinition:
    return IndicatorDefinition(
        id=_id(),
        kpi_id=kpi_id,
        version=1,
        capstone_sc_id=sc,
        name=name,
        kind=kind,
        aiims_function=aiims,
        incident_level=level,
        life_safety_tier=tier,
        formula=formula,
        unit=unit,
        owner_role=owner,
        refresh_cadence=cadence,
        target_value=Decimal(str(target)),
        alert_threshold=Decimal(str(threshold)),
        baseline_source=baseline,
        provenance=provenance,
        confidence_band_rule=ConfidenceBandRule(),
        risk_adjustment=(
            RiskAdjustment(
                likelihood=risk[0],
                consequence=risk[1],
                provenance="auto" if risk else "manual",
                auditor_signoff_required=False,
            )
            if risk
            else RiskAdjustment(
                likelihood=3, consequence=3, provenance="manual", auditor_signoff_required=True
            )
        ),
        created_at=datetime.now(UTC),
        created_by="seed",
    )


def seed_default_ladder() -> list[IndicatorDefinition]:
    """≥1 leading + ≥1 lagging per SC + 3 Public Information rows for US7."""
    rows = [
        # SC-CAP-015-001 — lives saved
        _make(
            kpi_id="lives_saved_leading",
            name="Triage compliance rate",
            kind="leading",
            sc="SC-CAP-015-001",
            unit="pct",
            target=95.0,
            aiims="Operations",
            tier="life_safety",
        ),
        _make(
            kpi_id="lives_saved_lagging",
            name="Lives saved (estimated)",
            kind="lagging",
            sc="SC-CAP-015-001",
            unit="lives",
            target=1000.0,
            aiims="Operations",
            tier="life_safety",
        ),
        # SC-CAP-015-002 — response time
        _make(
            kpi_id="response_time_p1_leading",
            name="Triage-to-dispatch median",
            kind="leading",
            sc="SC-CAP-015-002",
            unit="seconds",
            target=60.0,
            aiims="Operations",
        ),
        _make(
            kpi_id="response_time_p1",
            name="Pri-1 response time (median)",
            kind="lagging",
            sc="SC-CAP-015-002",
            unit="seconds",
            target=480.0,
            aiims="Operations",
        ),
        # SC-CAP-015-003 — evac lead time
        _make(
            kpi_id="evac_warning_leading",
            name="Warning issuance lead time",
            kind="leading",
            sc="SC-CAP-015-003",
            unit="hours",
            target=24.0,
            aiims="Planning",
        ),
        _make(
            kpi_id="evac_lead_lagging",
            name="Population evacuation lead time",
            kind="lagging",
            sc="SC-CAP-015-003",
            unit="hours",
            target=24.0,
            aiims="Planning",
        ),
        # SC-CAP-015-004 — logistics efficiency
        _make(
            kpi_id="logistics_route_leading",
            name="Route optimisation acceptance rate",
            kind="leading",
            sc="SC-CAP-015-004",
            unit="pct",
            target=85.0,
            aiims="Logistics",
            tier="efficiency",
        ),
        _make(
            kpi_id="logistics_efficiency",
            name="Asset utilisation uplift",
            kind="lagging",
            sc="SC-CAP-015-004",
            unit="pct",
            target=30.0,
            aiims="Logistics",
            tier="efficiency",
        ),
        # SC-CAP-015-005 — economic loss reduction
        _make(
            kpi_id="econ_loss_leading",
            name="Risk-adjusted exposure reduction",
            kind="leading",
            sc="SC-CAP-015-005",
            unit="pct",
            target=20.0,
            aiims="Planning",
            tier="efficiency",
        ),
        _make(
            kpi_id="econ_loss_lagging",
            name="Economic loss avoided",
            kind="lagging",
            sc="SC-CAP-015-005",
            unit="AUDm",
            target=30.0,
            aiims="Planning",
            tier="efficiency",
        ),
    ]
    return rows


def seed_public_information_ladder() -> list[IndicatorDefinition]:
    """T-A12 — Public Information indicators for US7 (FR-002, FR-037)."""
    return [
        _make(
            kpi_id="public_info_alert_reach",
            name="Alert reach (population %)",
            kind="leading",
            sc="SC-CAP-015-001",
            unit="pct",
            target=95.0,
            aiims="PublicInformation",
            tier="life_safety",
        ),
        _make(
            kpi_id="public_info_behavioural_impact",
            name="Behavioural-impact proxy",
            kind="lagging",
            sc="SC-CAP-015-001",
            unit="pct",
            target=70.0,
            aiims="PublicInformation",
            tier="life_safety",
        ),
        _make(
            kpi_id="public_info_multilingual_coverage",
            name="Multilingual channel coverage",
            kind="leading",
            sc="SC-CAP-015-001",
            unit="languages",
            target=8.0,
            aiims="PublicInformation",
            tier="life_safety",
        ),
    ]

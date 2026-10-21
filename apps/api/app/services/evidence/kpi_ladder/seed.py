# Canonical KPI ladder seed definitions for local and test registries.

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from ..measurement.definitions import CAPSTONE_METRIC_BY_ID, FORMULA_VERSION
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
    formula: str = "count(source_events)",
    formula_version: str = FORMULA_VERSION,
    unit: str = "count",
    target: float = 100.0,
    threshold: float = 80.0,
    cadence: str = "PT15M",
    baseline: str = "spec-015 prototype baseline paired by scenario version, content hash, and seed",
    calibration: str = "AIDR M&E Framework v2 paired prototype-baseline calibration",
    provenance: Provenance = "auto",
    risk: tuple[int, int] | None | Literal["default"] = "default",
    owner: str = "RiskManager",
) -> IndicatorDefinition:
    if risk == "default":
        risk_adjustment = RiskAdjustment(
            likelihood=3,
            consequence=3,
            provenance="manual",
            auditor_signoff_required=True,
        )
    elif risk is None:
        risk_adjustment = None
    elif isinstance(risk, tuple):
        likelihood, consequence = risk
        risk_adjustment = RiskAdjustment(
            likelihood=likelihood,
            consequence=consequence,
            provenance="auto",
            auditor_signoff_required=False,
        )
    else:
        raise TypeError("risk must be a likelihood/consequence pair, None, or 'default'")
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
        formula_version=formula_version,
        unit=unit,
        owner_role=owner,
        refresh_cadence=cadence,
        target_value=Decimal(str(target)),
        alert_threshold=Decimal(str(threshold)),
        baseline_source=baseline,
        calibration_reference=calibration,
        provenance=provenance,
        confidence_band_rule=ConfidenceBandRule(),
        risk_adjustment=risk_adjustment,
        created_at=datetime.now(UTC),
        created_by="seed",
    )


def _lagging(
    *,
    kpi_id: str,
    name: str,
    sc: CapstoneScId,
    aiims: AiimsFunction,
    level: IncidentLevel,
    tier: LifeSafetyTier,
    target: float,
    threshold: float,
) -> IndicatorDefinition:
    definition = CAPSTONE_METRIC_BY_ID[kpi_id]
    return _make(
        kpi_id=kpi_id,
        name=name,
        kind="lagging",
        sc=sc,
        aiims=aiims,
        level=level,
        tier=tier,
        formula=definition.formula,
        formula_version=definition.formula_version,
        unit=definition.unit,
        target=target,
        threshold=threshold,
        calibration=definition.calibration_reference,
    )


def seed_default_ladder() -> list[IndicatorDefinition]:
    return [
        _make(
            kpi_id="lives_saved_leading",
            name="Approved triage compliance rate",
            kind="leading",
            sc="SC-CAP-015-001",
            aiims="Operations",
            level=1,
            formula="100 * approved_triage_decisions / valid_triage_decisions",
            unit="percent",
            target=95.0,
            threshold=90.0,
        ),
        _lagging(
            kpi_id="lives_saved_lagging",
            name="Modelled lives saved per annual operational tempo",
            sc="SC-CAP-015-001",
            aiims="Control",
            level=3,
            tier="life_safety",
            target=1000.0,
            threshold=900.0,
        ),
        _make(
            kpi_id="response_time_p1_leading",
            name="Call-to-dispatch median",
            kind="leading",
            sc="SC-CAP-015-002",
            aiims="Intelligence",
            level=1,
            formula="median(dispatched_at - call_received_at)",
            unit="seconds",
            target=60.0,
            threshold=90.0,
        ),
        _lagging(
            kpi_id="response_time_p1",
            name="Priority-1 call-to-control median",
            sc="SC-CAP-015-002",
            aiims="Operations",
            level=2,
            tier="life_safety",
            target=50.0,
            threshold=40.0,
        ),
        _make(
            kpi_id="evac_warning_leading",
            name="Actionable warning issuance lead time",
            kind="leading",
            sc="SC-CAP-015-003",
            aiims="PublicInformation",
            level=2,
            formula="hours(hazard_impact_at - actionable_warning_issued_at)",
            unit="hours",
            target=48.0,
            threshold=24.0,
        ),
        _lagging(
            kpi_id="evac_lead_lagging",
            name="Population evacuation lead time",
            sc="SC-CAP-015-003",
            aiims="Planning",
            level=3,
            tier="life_safety",
            target=24.0,
            threshold=12.0,
        ),
        _make(
            kpi_id="logistics_route_leading",
            name="Approved route optimisation acceptance rate",
            kind="leading",
            sc="SC-CAP-015-004",
            aiims="Logistics",
            level=2,
            tier="efficiency",
            formula="100 * accepted_route_recommendations / eligible_route_recommendations",
            unit="percent",
            target=85.0,
            threshold=70.0,
        ),
        _lagging(
            kpi_id="logistics_efficiency",
            name="Resources placed on task efficiency",
            sc="SC-CAP-015-004",
            aiims="Logistics",
            level=3,
            tier="efficiency",
            target=30.0,
            threshold=20.0,
        ),
        _make(
            kpi_id="econ_loss_leading",
            name="Risk-adjusted exposure action rate",
            kind="leading",
            sc="SC-CAP-015-005",
            aiims="Intelligence",
            level=2,
            tier="efficiency",
            formula="100 * mitigated_exposure_aud / assessed_exposure_aud",
            unit="percent",
            target=20.0,
            threshold=10.0,
        ),
        _lagging(
            kpi_id="econ_loss_lagging",
            name="Modelled economic loss reduction",
            sc="SC-CAP-015-005",
            aiims="Planning",
            level=3,
            tier="efficiency",
            target=30.0,
            threshold=20.0,
        ),
    ]


def seed_public_information_ladder() -> list[IndicatorDefinition]:
    return [
        _make(
            kpi_id="public_info_alert_reach",
            name="Alert reach by eligible population",
            kind="leading",
            sc="SC-CAP-015-001",
            unit="percent",
            formula="100 * unique_recipients_reached / eligible_population",
            target=95.0,
            threshold=90.0,
            aiims="PublicInformation",
            level=2,
            tier="life_safety",
        ),
        _make(
            kpi_id="public_info_behavioural_impact",
            name="Observed protective-action rate",
            kind="lagging",
            sc="SC-CAP-015-001",
            unit="percent",
            formula="100 * verified_protective_actions / reached_recipients",
            target=70.0,
            threshold=60.0,
            aiims="PublicInformation",
            level=2,
            tier="life_safety",
        ),
        _make(
            kpi_id="public_info_multilingual_coverage",
            name="Multilingual channel coverage",
            kind="leading",
            sc="SC-CAP-015-001",
            unit="languages",
            formula="count(distinct validated_language_channels)",
            target=8.0,
            threshold=8.0,
            aiims="PublicInformation",
            level=2,
            tier="life_safety",
        ),
    ]

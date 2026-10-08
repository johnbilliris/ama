# Canonical capstone KPI definitions shared by rendering and calculation.

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

MetricDirection = Literal["baseline_minus_assisted", "assisted_minus_baseline"]
TargetMeasure = Literal["absolute_delta", "percent_delta"]

FORMULA_VERSION = "040.1"
PROTOTYPE_DISCLAIMER = (
    "Spec 015 SC-CAP-015-001 Sendai-aligned prototype scenario-counterfactual estimate only; not an observed fatality, "
    "service-performance, evacuation, logistics, or economic outcome."
)
MISSING_TIMESTAMP_RULE = (
    "Forward-impute from the next available adjacent canonical event; tag missing-timestamp "
    "and reduced-fidelity; exclude the imputed row from the confidence interval."
)
CALIBRATION_REFERENCE = (
    "AIDR Monitoring and Evaluation Framework for Disaster Recovery v2; "
    "prototype baseline paired by scenario version, content hash, and seed"
)


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    kpi_id: str
    capstone_sc_id: str
    name: str
    plain_language_definition: str
    formula: str
    unit: str
    delta_unit: str
    direction: MetricDirection
    target_measure: TargetMeasure
    target_value: Decimal
    start_signal: str
    end_signal: str
    calibration_reference: str = CALIBRATION_REFERENCE
    formula_version: str = FORMULA_VERSION
    missing_timestamp_rule: str = MISSING_TIMESTAMP_RULE
    prototype_disclaimer: str = PROTOTYPE_DISCLAIMER


CAPSTONE_METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        kpi_id="lives_saved_lagging",
        capstone_sc_id="SC-CAP-015-001",
        name="Modelled lives saved",
        plain_language_definition=(
            "Baseline modelled fatalities minus AMA-assisted modelled fatalities, summed for the "
            "same canonical scenario and multiplied by the explicit annual operational-tempo scale."
        ),
        formula=(
            "annual_operational_tempo_scale * "
            "(sum(baseline.modelled_fatalities) - sum(ama_assisted.modelled_fatalities))"
        ),
        unit="modelled_lives_per_year",
        delta_unit="modelled_lives_per_year",
        direction="baseline_minus_assisted",
        target_measure="absolute_delta",
        target_value=Decimal("1000"),
        start_signal="modelled_fatalities outcome in baseline mode",
        end_signal="modelled_fatalities outcome in AMA-assisted mode",
    ),
    MetricDefinition(
        kpi_id="response_time_p1",
        capstone_sc_id="SC-CAP-015-002",
        name="Priority-1 response time",
        plain_language_definition=(
            "Median elapsed seconds from call_received_at to controlled_at for eligible incidents."
        ),
        formula=(
            "median(controlled_at - call_received_at); improvement_pct = "
            "100 * (baseline_seconds - ama_assisted_seconds) / baseline_seconds"
        ),
        unit="seconds",
        delta_unit="seconds_reduced",
        direction="baseline_minus_assisted",
        target_measure="percent_delta",
        target_value=Decimal("50"),
        start_signal="call_received_at",
        end_signal="controlled_at",
    ),
    MetricDefinition(
        kpi_id="evac_lead_lagging",
        capstone_sc_id="SC-CAP-015-003",
        name="Evacuation lead time",
        plain_language_definition=(
            "Median hours between confirmed evacuation completion and forecast hazard impact; more hours is better."
        ),
        formula=(
            "median(hazard_impact_at - evacuation_completed_at); improvement_hours = "
            "ama_assisted_hours - baseline_hours"
        ),
        unit="hours",
        delta_unit="hours_gained",
        direction="assisted_minus_baseline",
        target_measure="absolute_delta",
        target_value=Decimal("24"),
        start_signal="evacuation_completed_at",
        end_signal="hazard_impact_at",
    ),
    MetricDefinition(
        kpi_id="logistics_efficiency",
        capstone_sc_id="SC-CAP-015-004",
        name="Logistics efficiency",
        plain_language_definition=(
            "Resources placed on task divided by valid resource requests. Uplift uses the baseline "
            "efficiency as its percentage denominator."
        ),
        formula=(
            "efficiency_pct = 100 * sum(resources_on_task) / sum(resources_requested); "
            "uplift_pct = 100 * (ama_assisted_efficiency_pct - baseline_efficiency_pct) / "
            "baseline_efficiency_pct"
        ),
        unit="percent_resources_on_task",
        delta_unit="percentage_points",
        direction="assisted_minus_baseline",
        target_measure="percent_delta",
        target_value=Decimal("30"),
        start_signal="resource_request_recorded",
        end_signal="resource_on_task_recorded",
    ),
    MetricDefinition(
        kpi_id="econ_loss_lagging",
        capstone_sc_id="SC-CAP-015-005",
        name="Modelled economic loss reduction",
        plain_language_definition=(
            "Baseline modelled economic loss minus AMA-assisted modelled economic loss. The reduction "
            "percentage uses baseline modelled economic loss as its denominator."
        ),
        formula=(
            "loss_reduction_aud = sum(baseline.modelled_economic_loss_aud) - "
            "sum(ama_assisted.modelled_economic_loss_aud); reduction_pct = "
            "100 * loss_reduction_aud / sum(baseline.modelled_economic_loss_aud)"
        ),
        unit="AUD",
        delta_unit="AUD_avoided",
        direction="baseline_minus_assisted",
        target_measure="percent_delta",
        target_value=Decimal("30"),
        start_signal="risk_exposure_snapshot_at",
        end_signal="economic_loss_assessed_at",
    ),
)

CAPSTONE_METRIC_BY_ID = {definition.kpi_id: definition for definition in CAPSTONE_METRICS}
CAPSTONE_METRIC_BY_SC_ID = {definition.capstone_sc_id: definition for definition in CAPSTONE_METRICS}
CAPSTONE_KPI_IDS = tuple(definition.kpi_id for definition in CAPSTONE_METRICS)

# Measurement Method renderer backed by the canonical metric definitions.

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .._summariser import summarise_blocks
from ..kpi_ladder.repository import list_published
from ..models.kpi import ConfidenceBandRule
from .definitions import CAPSTONE_METRIC_BY_SC_ID, CAPSTONE_METRICS, FORMULA_VERSION

CAPSTONE_DEFINITIONS = CAPSTONE_METRIC_BY_SC_ID


class MeasurementMethodDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capstone_sc_id: str
    kpi_id: str
    name: str
    definition_version: str
    formula_version: str
    formula: str
    unit: str
    delta_unit: str
    target_measure: Literal["absolute_delta", "percent_delta"]
    target_value: str
    plain_language_definition: str
    start_signal: str
    end_signal: str
    missing_timestamp_rule: str
    calibration_method: str
    calibration_reference: str
    prototype_disclaimer: str
    confidence_band_rule: ConfidenceBandRule


class MeasurementMethod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    generated_at: AwareDatetime
    definitions: list[MeasurementMethodDefinition] = Field(min_length=5, max_length=5)
    ama_advisory_only: bool = True


def build_definitions() -> list[MeasurementMethodDefinition]:
    indicators = list_published()
    definitions: list[MeasurementMethodDefinition] = []
    for metric in CAPSTONE_METRICS:
        sample_indicator = next(
            (indicator for indicator in indicators if indicator.capstone_sc_id == metric.capstone_sc_id),
            None,
        )
        rule = sample_indicator.confidence_band_rule if sample_indicator else None
        definitions.append(
            MeasurementMethodDefinition(
                capstone_sc_id=metric.capstone_sc_id,
                kpi_id=metric.kpi_id,
                name=metric.name,
                definition_version=FORMULA_VERSION,
                formula_version=metric.formula_version,
                formula=metric.formula,
                unit=metric.unit,
                delta_unit=metric.delta_unit,
                target_measure=metric.target_measure,
                target_value=str(metric.target_value),
                plain_language_definition=metric.plain_language_definition,
                start_signal=metric.start_signal,
                end_signal=metric.end_signal,
                missing_timestamp_rule=metric.missing_timestamp_rule,
                calibration_method=metric.calibration_reference,
                calibration_reference=metric.calibration_reference,
                prototype_disclaimer=metric.prototype_disclaimer,
                confidence_band_rule=rule or ConfidenceBandRule(),
            )
        )
    return definitions


def render(format: Literal["json", "markdown"] = "json") -> MeasurementMethod | str:
    definitions = build_definitions()
    payload = MeasurementMethod(
        version=FORMULA_VERSION,
        generated_at=datetime.now(UTC),
        definitions=definitions,
    )
    if format == "json":
        return payload

    newline = chr(10)
    blocks = [f"# Measurement Method (formula version {FORMULA_VERSION}){newline}"]
    for definition in definitions:
        capstone_sc_id = definition.capstone_sc_id
        name = definition.name
        plain = definition.plain_language_definition
        formula = definition.formula
        unit = definition.unit
        formula_version = definition.formula_version
        start_signal = definition.start_signal
        end_signal = definition.end_signal
        missing_rule = definition.missing_timestamp_rule
        calibration = definition.calibration_reference
        target_value = definition.target_value
        target_measure = definition.target_measure
        disclaimer = definition.prototype_disclaimer
        blocks.append(
            f"## {capstone_sc_id} — {name}{newline}{newline}"
            f"{plain}{newline}{newline}"
            f"- **Formula**: `{formula}`{newline}"
            f"- **Unit**: {unit}{newline}"
            f"- **Formula version**: {formula_version}{newline}"
            f"- **Start signal**: {start_signal}{newline}"
            f"- **End signal**: {end_signal}{newline}"
            f"- **Missing-timestamp rule**: {missing_rule}{newline}"
            f"- **Calibration reference**: {calibration}{newline}"
            f"- **Target**: {target_value} ({target_measure}){newline}"
            f"- **Prototype disclaimer**: {disclaimer}{newline}"
        )
    blocks.append(
        "> Advisory only — confidence intervals use at least 1,000 deterministic bootstrap resamples when "
        f"two or more non-imputed observations are available; otherwise they are labelled ±1 SD.{newline}"
    )
    return summarise_blocks(blocks, max_chars=12000)

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SEED_CATALOGUE_PATH = Path("packages/domain/src/domain/seed/data_sources_australia.json")
EXCLUSIONS_PATH = Path("specs/006-data-ingestion-storage/evidence/scenario-source-exclusions.json")

SCENARIO_TYPES = ("bushfire", "flood", "cyclone", "severe_storm")


def _load_seed_catalogue() -> list[dict[str, Any]]:
    payload = json.loads(SEED_CATALOGUE_PATH.read_text(encoding="utf-8"))
    return [entry for entry in payload if isinstance(entry, dict)]


def _load_exclusions() -> dict[str, dict[str, str]]:
    if not EXCLUSIONS_PATH.exists():
        return {}
    payload = json.loads(EXCLUSIONS_PATH.read_text(encoding="utf-8"))
    rows = payload.get("excluded", []) if isinstance(payload, dict) else []
    exclusions: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("dataSourceId", "")).strip()
        if not source_id:
            continue
        scenario = str(row.get("scenarioType", "")).strip()
        reason = str(row.get("reason", "")).strip() or "excluded"
        exclusions.setdefault(scenario, {})[source_id] = reason
    return exclusions


def _cadence_seconds(update_frequency: str) -> float:
    value = update_frequency.strip().lower()
    if value == "real_time":
        return 60.0
    if value == "event_driven":
        return 60.0
    if value == "hourly":
        return 3600.0
    if value == "daily":
        return 86400.0
    if value.endswith("_minutes"):
        prefix = value.replace("_minutes", "")
        try:
            return float(prefix) * 60.0
        except ValueError:
            return 60.0
    return 60.0


def _is_relevant(source: dict[str, Any], scenario_type: str) -> bool:
    source_id = str(source.get("data_source_id", "")).strip().lower()
    sub_category = str(source.get("sub_category", "")).strip().lower()
    data_type = str(source.get("data_type", "")).strip().lower()
    kind = str(source.get("kind", "")).strip().lower()

    if scenario_type == "bushfire":
        return any(
            token in source_id
            for token in ("fire", "hotspot", "air-quality", "weather", "warning", "twitter", "facebook", "reddit")
        ) or sub_category in {"weather_climate", "emergency_services", "transport_infrastructure", "health"}
    if scenario_type == "flood":
        return any(
            token in source_id
            for token in ("flood", "river", "ses", "radar", "weather", "warning", "twitter", "facebook", "reddit")
        ) or sub_category in {"weather_climate", "emergency_services", "transport_infrastructure", "health"}
    if scenario_type == "cyclone":
        return any(
            token in source_id
            for token in (
                "cyclone",
                "storm",
                "himawari",
                "radar",
                "weather",
                "warning",
                "river",
                "twitter",
                "facebook",
                "reddit",
            )
        ) or sub_category in {"weather_climate", "emergency_services", "transport_infrastructure"}
    if scenario_type == "severe_storm":
        return any(
            token in source_id
            for token in (
                "storm",
                "radar",
                "weather",
                "warning",
                "observations",
                "river",
                "twitter",
                "facebook",
                "reddit",
            )
        ) or sub_category in {"weather_climate", "emergency_services", "transport_infrastructure"}
    return kind == "authoritative" and data_type in {"cap_alert", "geojson", "json_observations"}


def build_scenario_source_matrix() -> dict[str, dict[str, dict[str, Any]]]:
    catalogue = _load_seed_catalogue()
    exclusions = _load_exclusions()
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for scenario_type in SCENARIO_TYPES:
        scenario_rows: dict[str, dict[str, Any]] = {}
        excluded_ids = exclusions.get(scenario_type, {})
        for source in catalogue:
            source_id = str(source.get("data_source_id", "")).strip()
            if not source_id:
                continue
            if source_id in excluded_ids:
                continue
            if not _is_relevant(source, scenario_type):
                continue
            scenario_rows[source_id] = {
                "dataSourceId": source_id,
                "type": str(source.get("data_type", "unknown")),
                "kind": str(source.get("kind", "unknown")),
                "geographicCoverage": str(source.get("geographic_coverage", "national")),
                "cadenceSeconds": _cadence_seconds(str(source.get("update_frequency", "event_driven"))),
            }
        result[scenario_type] = scenario_rows
    return result


def activated_sources_for_scenario(scenario_type: str) -> list[str]:
    matrix = build_scenario_source_matrix()
    return sorted(matrix.get(scenario_type, {}).keys())


def source_matrix_for_scenario(scenario_type: str) -> dict[str, dict[str, Any]]:
    matrix = build_scenario_source_matrix()
    return matrix.get(scenario_type, {})


def validate_template_sources(scenario_type: str, source_ids: list[str]) -> None:
    matrix = source_matrix_for_scenario(scenario_type)
    unknown = [source_id for source_id in source_ids if source_id not in matrix]
    if unknown:
        raise ValueError(f"scenario {scenario_type} contains unregistered sources: {sorted(unknown)}")


def validate_source_region(source_id: str, scenario_type: str, jurisdictions: list[str]) -> None:
    matrix = source_matrix_for_scenario(scenario_type)
    config = matrix.get(source_id)
    if config is None:
        raise ValueError(f"source '{source_id}' is not registered for scenario {scenario_type}")
    coverage = str(config.get("geographicCoverage", "national")).strip().lower()
    if coverage == "national":
        return
    requested = {value.strip().lower() for value in jurisdictions if str(value).strip()}
    if not requested:
        return
    if coverage not in requested:
        raise ValueError(
            f"source '{source_id}' has coverage '{coverage}' and is not valid for jurisdictions {sorted(requested)}"
        )

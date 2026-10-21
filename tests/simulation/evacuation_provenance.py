"""Persisted provenance fixtures for evacuation scenario tests."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any


class ScenarioProvenanceStore:
    def __init__(self, documents: dict[str, dict[str, Any]]) -> None:
        self._documents = documents

    def read_item(self, item: str, partition_key: str) -> dict[str, Any]:
        document = self._documents[item]
        assert partition_key == document["incident_scope_key"]
        return deepcopy(document)


def build_scenario_provenance_stores(
    handoff: Any,
) -> tuple[ScenarioProvenanceStore, ScenarioProvenanceStore]:
    payload = handoff.payload
    generated_at = datetime.now(UTC)
    recommendation_id = str(payload["recommendationId"])
    assessment_id = str(payload["assessmentId"])
    incident_scope_key = handoff.scope_key

    recommendation = {
        "recommendation_id": recommendation_id,
        "incident_id": handoff.incident_id,
        "type": "evacuation",
        "summary": "Evacuate affected communities",
        "explanation": "The persisted route-risk assessment exceeds the evacuation threshold",
        "required_approval_level": "incident_commander",
        "assessment_id": assessment_id,
        "confidence_score": handoff.confidence,
        "severity_level": payload["severity_level"],
        "incident_scope_key": incident_scope_key,
        "tenant_id": handoff.tenant_id,
    }
    assessment = {
        "hazard_assessment_id": assessment_id,
        "incident_id": handoff.incident_id,
        "assessment_type": "route_risk",
        "input_signal_ids": [f"signal-{handoff.incident_id}"],
        "summary": "Hazard threatens evacuation corridors",
        "confidence_level": "high",
        "generated_at": generated_at.isoformat(),
        "valid_until": (generated_at + timedelta(hours=48)).isoformat(),
        "status": "active",
        "incident_scope_key": incident_scope_key,
        "tenant_id": handoff.tenant_id,
        "hazard_map": {
            "affected_area": payload["affected_area"],
            "severity_level": payload["severity_level"],
            "hazard_type": payload["hazard_type"],
            "confidence_score": handoff.confidence,
            "time_horizon": payload["time_horizon"],
            "population_estimate": payload["population_estimate"],
        },
    }
    return (
        ScenarioProvenanceStore({recommendation_id: recommendation}),
        ScenarioProvenanceStore({assessment_id: assessment}),
    )

"""Live adapter equivalence tests for deterministic evacuation planning."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from common.handoffs import AgentHandoffEvent
from evacuation.models import (
    DataSnapshot,
    EvacuationPhase,
    EvacuationPlan,
    EvacuationRoute,
    EvacuationZone,
    HazardSourceSnapshot,
    HazardSummary,
    Traceability,
    ZoneDisposition,
    ZoneDispositionType,
)

pytest.importorskip("agent_framework")

from maf_runtime.agents.evacuation_agent import EvacuationMafAgent


def _handoff() -> AgentHandoffEvent:
    return AgentHandoffEvent(
        handoff_id="hf-equivalence",
        incident_id="inc-equivalence",
        source_agent="risk_assessment",
        target_agent="evacuation",
        scope_key="simulation:inc-equivalence",
        tenant_id="simulation",
        confidence=0.8,
        payload={
            "assessmentId": "assessment-equivalence",
            "recommendationId": "recommendation-equivalence",
        },
    )


def _plan() -> EvacuationPlan:
    area = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
    }
    source = HazardSourceSnapshot(
        assessment_id="assessment-equivalence",
        hazard_type="bushfire",
        severity_level="high",
        affected_area=area,
        generated_at=datetime.now(UTC),
        buffer_radius_metres=2_000,
        geometry_sha256="a" * 64,
    )
    return EvacuationPlan(
        plan_id="ep-inc-equivalence-v1",
        incident_id="inc-equivalence",
        incident_scope_key="simulation:inc-equivalence",
        tenant_id="simulation",
        simulation=True,
        affected_area=area,
        hazard_summary=HazardSummary(
            hazard_type="bushfire",
            hazard_types=["bushfire"],
            severity_level="high",
            time_horizon="4h",
            source_assessment_id="assessment-equivalence",
            affected_area=area,
            sources=[source],
        ),
        zones=[
            EvacuationZone(
                zone_id="zone-1",
                zone_number=1,
                population_estimate=100,
            )
        ],
        routes=[
            EvacuationRoute(
                route_id="route-1",
                zone_id="1",
                assembly_area_id="aa-1",
                route_name="Deterministic route",
                waypoints=["edge-1"],
            )
        ],
        phases=[
            EvacuationPhase(
                phase_number=1,
                zone_ids=["1"],
                duration_minutes=10,
                population_moved=100,
            )
        ],
        zone_dispositions=[
            ZoneDisposition(
                zone_id="zone-1",
                zone_number=1,
                disposition=ZoneDispositionType.evacuation,
                urgency="immediate",
                affected_population=100,
                evacuating_population=100,
                remaining_population=0,
                rationale="Route available",
            )
        ],
        traceability=Traceability(
            source_handoff_id="hf-equivalence",
            risk_assessment_id="assessment-equivalence",
            risk_assessment_ids=["assessment-equivalence"],
            recommendation_id="recommendation-equivalence",
            input_data_versions={"config": "config"},
            generation_method="template_fallback",
        ),
        data_snapshot=DataSnapshot(
            road_network_version="road",
            population_data_version="population",
            facility_data_version="facility",
            assembly_area_data_version="assembly",
            hazard_assessment_ids=["assessment-equivalence"],
            hazard_geometry_algorithm="per-hazard-aeqd-level-union-v1",
        ),
        summary="Complete simulation plan",
        generation_method="template_fallback",
        configuration_version="config",
        assumptions=[],
        population_estimate=100,
        total_population=100,
    )


class _Planner:
    def __init__(self, plan: EvacuationPlan | None):
        self.plan = plan
        self.handoffs = []

    def process_handoff(self, handoff):
        self.handoffs.append(handoff)
        return self.plan


@pytest.mark.asyncio
async def test_supported_modes_delegate_to_same_deterministic_planner() -> None:
    planner = _Planner(_plan())
    adapter = EvacuationMafAgent(evacuation_agent=planner)

    legacy = await adapter.run_legacy(_handoff())
    maf = await adapter.run_maf({"evacuation_handoff": _handoff().model_dump(mode="json")})

    assert legacy.model_dump(mode="json") == maf.model_dump(mode="json")
    assert legacy.routes and legacy.zones and legacy.phases
    assert len(planner.handoffs) == 2
    assert all(handoff.tenant_id == "simulation" for handoff in planner.handoffs)


@pytest.mark.asyncio
async def test_rejected_handoff_never_becomes_an_empty_plan() -> None:
    adapter = EvacuationMafAgent(evacuation_agent=_Planner(None))
    with pytest.raises(ValueError, match="was rejected"):
        await adapter.run_legacy(_handoff())

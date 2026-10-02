# Contract coverage for source-derived evidence replay.

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.main import create_app
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.services.evidence._clients import reset_registry
from app.services.evidence.simulation.orchestrator import SimulationEventEvidenceAdapter
from app.services.evidence.simulation.router import configure_event_source
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.simulation_event import SimulationEvent

KPIS = (
    "lives_saved_lagging",
    "response_time_p1",
    "evac_lead_lagging",
    "logistics_efficiency",
    "econ_loss_lagging",
)


def _metrics(mode: str) -> dict[str, dict]:
    if mode == "baseline":
        return {
            "lives_saved_lagging": {"modelled_fatalities": 10, "annual_operational_tempo_scale": 100},
            "response_time_p1": {
                "call_received_at": "2026-05-11T10:00:00Z",
                "dispatched_at": "2026-05-11T10:01:00Z",
                "arrived_at": "2026-05-11T10:05:00Z",
                "controlled_at": "2026-05-11T10:10:00Z",
                "cleared_at": "2026-05-11T10:20:00Z",
            },
            "evac_lead_lagging": {"evacuation_lead_time_hours": 12},
            "logistics_efficiency": {"resources_on_task": 50, "resources_requested": 100},
            "econ_loss_lagging": {"modelled_economic_loss_aud": 1000},
        }
    return {
        "lives_saved_lagging": {"modelled_fatalities": 5, "annual_operational_tempo_scale": 100},
        "response_time_p1": {
            "call_received_at": "2026-05-11T10:00:00Z",
            "dispatched_at": "2026-05-11T10:00:30Z",
            "arrived_at": "2026-05-11T10:03:00Z",
            "controlled_at": "2026-05-11T10:05:30Z",
            "cleared_at": "2026-05-11T10:20:00Z",
        },
        "evac_lead_lagging": {"evacuation_lead_time_hours": 25.2},
        "logistics_efficiency": {"resources_on_task": 70, "resources_requested": 100},
        "econ_loss_lagging": {"modelled_economic_loss_aud": 700},
    }


def _seed_pair(repository: SimulationEventRepository, run_pair_id: str, *, seed: str = "S1") -> None:
    sequence = 0
    for mode in ("baseline", "ama_assisted"):
        for observation_index in range(2):
            for kpi_id, metrics in _metrics(mode).items():
                sequence += 1
                suffix = f"{mode}-{observation_index}-{kpi_id}"
                payload = {
                    "synthetic_test_fixture": True,
                    "scenario_id": "bushfire",
                    "scenario_version": "scenario-v7",
                    "scenario_content_hash": "a" * 64,
                    "seed": seed,
                    "mode": mode,
                    "run_pair_id": run_pair_id,
                    "kpi_id": kpi_id,
                    "observation_id": f"incident-{observation_index}",
                    "event_timestamp": "2026-05-11T10:00:00Z",
                    "confidence": 0.91,
                    "component_version": "sim-fixture-v1",
                    "signal_id": f"signal-{suffix}",
                    "model_output_id": f"model-{suffix}",
                    "recommendation_id": f"recommendation-{suffix}",
                    "human_decision_id": f"decision-{suffix}",
                    "decision_approved": True,
                    "outcome_id": f"outcome-{suffix}",
                    "metrics": metrics,
                }
                repository.append_event(
                    SimulationEvent(
                        tenant_id=run_pair_id,
                        event_seq=sequence,
                        event_type="state_change",
                        sim_time_offset=float(sequence),
                        wall_clock_time=datetime.now(UTC),
                        payload=payload,
                    )
                )


@pytest.fixture()
def client():
    reset_registry()
    repository = SimulationEventRepository()
    _seed_pair(repository, "qs-1")
    configure_event_source(SimulationEventEvidenceAdapter(repository))
    from app.services.evidence.kpi_ladder import router as kpi_router

    kpi_router._SEEDED = False
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    configure_event_source(None)


def test_replay_returns_and_persists_five_source_derived_deltas(client):
    response = client.post(
        "/api/v1/evidence/scenarios/bushfire/replay",
        json={"seed": "S1", "run_pair_id": "qs-1", "repetitions": 3, "allow_degraded_mode": False},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["kpi_deltas"]) == 5
    assert {row["kpi_id"] for row in body["kpi_deltas"]} == set(KPIS)
    assert body["scenario_version"] == "scenario-v7"
    assert body["scenario_content_hash"] == "a" * 64
    assert body["determinism"]["diverged"] is False
    assert body["advisory_only"] is True
    assert all(row["measurement_status"] == "measured" for row in body["kpi_deltas"])
    assert all(row["formula_version"] and row["unit"] and row["calibration_reference"] for row in body["kpi_deltas"])
    assert body["run_provenance"][0]["signal_ids"]

    readback = client.get(f"/api/v1/evidence/scorecards/{body['id']}")
    assert readback.status_code == 200
    assert readback.json()["id"] == body["id"]
    latest = client.get("/api/v1/evidence/scorecards/latest?scenario_id=bushfire")
    assert latest.status_code == 200
    assert latest.json()["id"] == body["id"]
    trace = client.get(f"/api/v1/evidence/audit/{body['id']}")
    assert trace.status_code == 200
    assert trace.json()["chain_complete"] is True
    assert trace.json()["missing_references"] == []

    retried = client.post(
        "/api/v1/evidence/scenarios/bushfire/replay",
        json={"seed": "S1", "run_pair_id": "qs-1", "repetitions": 1},
    )
    assert retried.status_code == 200
    assert retried.json()["id"] == body["id"]


def test_missing_sources_refuse_or_return_explicit_no_signal(client):
    refused = client.post(
        "/api/v1/evidence/scenarios/flood/replay",
        json={"seed": "S1", "run_pair_id": "missing", "allow_degraded_mode": False},
    )
    assert refused.status_code == 422
    assert refused.json()["title"] == "required-evidence-source-unavailable"

    degraded = client.post(
        "/api/v1/evidence/scenarios/flood/replay",
        json={"seed": "S1", "run_pair_id": "missing", "allow_degraded_mode": True},
    )
    assert degraded.status_code == 200
    rows = degraded.json()["kpi_deltas"]
    assert len(rows) == 5
    assert all(row["measurement_status"] == "no_signal" for row in rows)
    assert all(row["absolute_delta"] is None and row["reduced_fidelity"] for row in rows)


def test_replay_unknown_scenario_404(client):
    response = client.post(
        "/api/v1/evidence/scenarios/unknown/replay",
        json={"seed": "X", "run_pair_id": "x"},
    )
    assert response.status_code in (404, 422)

# Integration coverage for all canonical event-derived run pairs.

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.services.evidence.simulation.orchestrator import SimulationEventEvidenceAdapter
from app.services.evidence.simulation.scenarios import SCENARIOS
from app.services.evidence.simulation.scorecard_builder import build_scorecard

from packages.domain.src.domain.models.simulation_event import SimulationEvent


def _mode_metrics(mode: str) -> dict[str, dict]:
    if mode == "baseline":
        return {
            "lives_saved_lagging": {"modelled_fatalities": 100, "annual_operational_tempo_scale": 20},
            "response_time_p1": {
                "call_received_at": "2026-05-11T10:00:00Z",
                "dispatched_at": "2026-05-11T10:01:00Z",
                "arrived_at": "2026-05-11T10:05:00Z",
                "controlled_at": "2026-05-11T10:10:00Z",
                "cleared_at": "2026-05-11T10:15:00Z",
            },
            "evac_lead_lagging": {"evacuation_lead_time_hours": 12},
            "logistics_efficiency": {"resources_on_task": 50, "resources_requested": 100},
            "econ_loss_lagging": {"modelled_economic_loss_aud": 2000000},
        }
    return {
        "lives_saved_lagging": {"modelled_fatalities": 50, "annual_operational_tempo_scale": 20},
        "response_time_p1": {
            "call_received_at": "2026-05-11T10:00:00Z",
            "dispatched_at": "2026-05-11T10:00:30Z",
            "arrived_at": "2026-05-11T10:03:00Z",
            "controlled_at": "2026-05-11T10:05:30Z",
            "cleared_at": "2026-05-11T10:15:00Z",
        },
        "evac_lead_lagging": {"evacuation_lead_time_hours": 25.2},
        "logistics_efficiency": {"resources_on_task": 70, "resources_requested": 100},
        "econ_loss_lagging": {"modelled_economic_loss_aud": 1400000},
    }


def _source(scenario: str, run_pair_id: str) -> SimulationEventEvidenceAdapter:
    repository = SimulationEventRepository()
    sequence = 0
    for mode in ("baseline", "ama_assisted"):
        for kpi_id, metrics in _mode_metrics(mode).items():
            sequence += 1
            payload = {
                "synthetic_test_fixture": True,
                "scenario_id": scenario,
                "scenario_version": "canonical-v1",
                "scenario_content_hash": "b" * 64,
                "seed": "same-seed",
                "mode": mode,
                "run_pair_id": run_pair_id,
                "kpi_id": kpi_id,
                "observation_id": "incident-1",
                "event_timestamp": "2026-05-11T10:00:00Z",
                "confidence": 0.95,
                "component_version": "fixture-v1",
                "signal_id": f"signal-{sequence}",
                "model_output_id": f"model-{sequence}",
                "outcome_id": f"outcome-{sequence}",
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
    return SimulationEventEvidenceAdapter(repository)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_replay_covers_five_capstone_kpis_with_exact_source_arithmetic(scenario):
    run_pair_id = f"pair-{scenario}"
    scorecard = build_scorecard(
        scenario_id=scenario,
        seed="same-seed",
        run_pair_id=run_pair_id,
        repetitions=2,
        allow_degraded_mode=False,
        event_source=_source(scenario, run_pair_id),
    )
    deltas = {delta.kpi_id: delta for delta in scorecard.kpi_deltas}
    assert deltas["lives_saved_lagging"].absolute_delta == Decimal("1000.0000")
    assert deltas["lives_saved_lagging"].meets_target is True
    assert deltas["response_time_p1"].baseline_value == Decimal("600.0000")
    assert deltas["response_time_p1"].ama_assisted_value == Decimal("330.0000")
    assert deltas["response_time_p1"].percent_delta == Decimal("45.0000")
    assert deltas["response_time_p1"].meets_target is False
    assert deltas["evac_lead_lagging"].absolute_delta == Decimal("13.2000")
    assert deltas["evac_lead_lagging"].meets_target is False
    assert deltas["logistics_efficiency"].percent_delta == Decimal("40.0000")
    assert deltas["econ_loss_lagging"].percent_delta == Decimal("30.0000")
    assert scorecard.determinism is not None and scorecard.determinism.diverged is False
    assert scorecard.scenario_version == "canonical-v1"
    assert scorecard.run_provenance[0].source_event_ids

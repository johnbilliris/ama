# Same-seed determinism is evaluated on per-KPI deltas.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.repositories.simulation_event_repository import SimulationEventRepository
from app.services.evidence.simulation.orchestrator import SimulationEventEvidenceAdapter
from app.services.evidence.simulation.scorecard_builder import build_scorecard

from packages.domain.src.domain.models.simulation_event import SimulationEvent


def _metrics(mode: str, *, baseline_response_seconds: int = 600) -> dict[str, dict]:
    response_seconds = baseline_response_seconds if mode == "baseline" else 330
    controlled = datetime(2026, 5, 11, 10, 0, tzinfo=UTC) + timedelta(seconds=response_seconds)
    return {
        "lives_saved_lagging": {
            "modelled_fatalities": 100 if mode == "baseline" else 50,
            "annual_operational_tempo_scale": 20,
        },
        "response_time_p1": {
            "call_received_at": "2026-05-11T10:00:00Z",
            "dispatched_at": "2026-05-11T10:00:30Z",
            "arrived_at": "2026-05-11T10:03:00Z",
            "controlled_at": controlled.isoformat(),
            "cleared_at": "2026-05-11T10:20:00Z",
        },
        "evac_lead_lagging": {"evacuation_lead_time_hours": 12 if mode == "baseline" else 36},
        "logistics_efficiency": {
            "resources_on_task": 50 if mode == "baseline" else 70,
            "resources_requested": 100,
        },
        "econ_loss_lagging": {"modelled_economic_loss_aud": 1000 if mode == "baseline" else 700},
    }


def _source(*, changed_second_baseline: bool) -> SimulationEventEvidenceAdapter:
    repository = SimulationEventRepository()
    sequence = 0
    for repetition in (0, 1):
        for mode in ("baseline", "ama_assisted"):
            baseline_seconds = 700 if changed_second_baseline and repetition == 1 else 600
            for kpi_id, metrics in _metrics(mode, baseline_response_seconds=baseline_seconds).items():
                sequence += 1
                payload = {
                    "synthetic_test_fixture": True,
                    "scenario_id": "bushfire",
                    "scenario_version": "v1",
                    "scenario_content_hash": "d" * 64,
                    "seed": "same-seed",
                    "mode": mode,
                    "run_pair_id": "determinism-pair",
                    "repetition_index": repetition,
                    "kpi_id": kpi_id,
                    "observation_id": "incident-1",
                    "event_timestamp": "2026-05-11T10:00:00Z",
                    "confidence": 0.9,
                    "metrics": metrics,
                }
                repository.append_event(
                    SimulationEvent(
                        tenant_id="determinism-pair",
                        event_seq=sequence,
                        event_type="state_change",
                        sim_time_offset=float(sequence),
                        wall_clock_time=datetime.now(UTC),
                        payload=payload,
                    )
                )
    return SimulationEventEvidenceAdapter(repository)


def _scorecard(source):
    return build_scorecard(
        scenario_id="bushfire",
        seed="same-seed",
        run_pair_id="determinism-pair",
        event_source=source,
        repetitions=2,
        allow_degraded_mode=False,
    )


def test_identical_seed_reproduces_per_kpi_deltas():
    scorecard = _scorecard(_source(changed_second_baseline=False))
    assert scorecard.determinism is not None
    assert scorecard.determinism.repetition_count == 5
    assert scorecard.determinism.within_tolerance_count == 5
    assert scorecard.determinism.reproduction_rate == 1.0
    assert scorecard.determinism.diverged is False


def test_baseline_change_is_detected_when_assisted_value_is_constant():
    scorecard = _scorecard(_source(changed_second_baseline=True))
    response = next(delta for delta in scorecard.kpi_deltas if delta.kpi_id == "response_time_p1")
    assert float(response.ama_assisted_value) == 330.0
    assert scorecard.determinism is not None
    assert scorecard.determinism.within_tolerance_count == 4
    assert scorecard.determinism.diverged is True

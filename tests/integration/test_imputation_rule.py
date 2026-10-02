# Forward-imputation, confidence exclusion, and publication gate tests.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.services.evidence.measurement.confidence import bootstrap_ci
from app.services.evidence.measurement.imputation import forward_impute, small_sample_gate, small_sample_share
from app.services.evidence.models.signal import CanonicalEventChain
from app.services.evidence.simulation.orchestrator import SimulationEventEvidenceAdapter
from app.services.evidence.simulation.scorecard_builder import (
    ImputationSignoffRequiredError,
    NamedAuditorSignoff,
    build_scorecard,
)
from app.services.evidence.simulation.signoff import (
    AuditImputationSignoffResolver,
    record_imputation_signoff,
)

from packages.domain.src.domain.models.simulation_event import SimulationEvent


def _ts(offset: int) -> datetime:
    return datetime(2026, 5, 11, 10, 0, tzinfo=UTC) + timedelta(minutes=offset)


def test_forward_impute_fills_missing_call_received():
    chain = CanonicalEventChain(
        call_received_at=None,
        dispatched_at=_ts(0),
        arrived_at=_ts(5),
        controlled_at=_ts(20),
        cleared_at=_ts(40),
    )
    output = forward_impute(chain)
    assert output.call_received_at == _ts(0)
    assert output.imputed_fields == ["call_received_at"]


def test_forward_impute_does_not_backfill_missing_trailing_timestamp():
    chain = CanonicalEventChain(
        call_received_at=_ts(0),
        dispatched_at=_ts(1),
        arrived_at=_ts(2),
        controlled_at=_ts(3),
        cleared_at=None,
    )
    output = forward_impute(chain)
    assert output.cleared_at is None
    assert output.imputed_fields == []


def test_small_sample_gate_is_strictly_greater_than_ten_percent():
    complete = CanonicalEventChain(
        call_received_at=_ts(0),
        dispatched_at=_ts(1),
        arrived_at=_ts(2),
        controlled_at=_ts(3),
        cleared_at=_ts(4),
    )
    imputed = forward_impute(
        CanonicalEventChain(
            call_received_at=None,
            dispatched_at=_ts(1),
            arrived_at=_ts(2),
            controlled_at=_ts(3),
            cleared_at=_ts(4),
        )
    )
    assert small_sample_share([imputed, *([complete] * 9)]) == 0.1
    assert small_sample_gate([imputed, *([complete] * 9)]) is False
    assert small_sample_gate([imputed, *([complete] * 8)]) is True


def _response_source(run_pair_id: str, *, baseline_rows: int, assisted_rows: int, imputed_rows: int):
    repository = SimulationEventRepository()
    sequence = 0
    remaining_imputed = imputed_rows
    for mode, count in (("baseline", baseline_rows), ("ama_assisted", assisted_rows)):
        for index in range(count):
            sequence += 1
            metrics = {
                "call_received_at": "2026-05-11T10:00:00Z",
                "dispatched_at": "2026-05-11T10:01:00Z",
                "arrived_at": "2026-05-11T10:02:00Z",
                "controlled_at": "2026-05-11T10:10:00Z" if mode == "baseline" else "2026-05-11T10:05:00Z",
                "cleared_at": "2026-05-11T10:20:00Z",
            }
            if remaining_imputed:
                metrics["call_received_at"] = None
                remaining_imputed -= 1
            payload = {
                "synthetic_test_fixture": True,
                "scenario_id": "bushfire",
                "scenario_version": "v1",
                "scenario_content_hash": "c" * 64,
                "seed": "seed",
                "mode": mode,
                "run_pair_id": run_pair_id,
                "kpi_id": "response_time_p1",
                "observation_id": f"incident-{index}",
                "event_timestamp": "2026-05-11T10:00:00Z",
                "confidence": 0.9,
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


class _ApprovedSignoff:
    def resolve(self, **kwargs):
        assert kwargs["imputation_share"] > 0.10
        return NamedAuditorSignoff(approval_id="approval-1", auditor_id="auditor-1")


def test_real_scorecard_path_excludes_imputed_rows_from_ci_at_exact_ten_percent():
    scorecard = build_scorecard(
        scenario_id="bushfire",
        seed="seed",
        run_pair_id="ten-percent",
        event_source=_response_source("ten-percent", baseline_rows=5, assisted_rows=5, imputed_rows=1),
        allow_degraded_mode=True,
    )
    response = next(delta for delta in scorecard.kpi_deltas if delta.kpi_id == "response_time_p1")
    assert str(scorecard.imputation_share) == "0.1000"
    assert response.imputed_observation_count == 1
    assert response.confidence_observation_count == 4
    assert response.confidence_method == "bootstrap_p2_5_p97_5"
    assert response.bootstrap_resamples == 1000


def test_real_scorecard_path_requires_named_signoff_above_ten_percent():
    source = _response_source("over-ten", baseline_rows=5, assisted_rows=4, imputed_rows=1)
    with pytest.raises(ImputationSignoffRequiredError):
        build_scorecard(
            scenario_id="bushfire",
            seed="seed",
            run_pair_id="over-ten",
            event_source=source,
            allow_degraded_mode=True,
        )

    approved = build_scorecard(
        scenario_id="bushfire",
        seed="seed",
        run_pair_id="over-ten",
        event_source=source,
        allow_degraded_mode=True,
        signoff_resolver=_ApprovedSignoff(),
    )
    assert approved.auditor_signoff_id == "approval-1"
    assert approved.auditor_id == "auditor-1"
    assert all(delta.small_sample for delta in approved.kpi_deltas)


def test_bootstrap_uses_resample_count_not_raw_observation_count():
    bootstrapped = bootstrap_ci([1.0, 2.0], seed=7, n_resamples=1000)
    assert bootstrapped.method == "bootstrap_p2_5_p97_5"
    assert bootstrapped.n_resamples == 1000
    fallback = bootstrap_ci(list(range(2000)), seed=7, n_resamples=999)
    assert fallback.method == "stddev_pm1"
    assert fallback.label == "small-sample"


def test_audit_signoff_is_bound_to_exact_run_hash_and_share():
    from app.services.evidence._clients import reset_registry

    reset_registry()
    record_imputation_signoff(
        scenario_id="bushfire",
        run_pair_id="pair-1",
        scenario_content_hash="a" * 64,
        imputation_share=Decimal("0.2"),
        auditor_id="auditor-oid-1",
        approval_id="approval-1",
        basis="Reviewed the exact imputed event set and accepted the limitation.",
        correlation_id="signoff-test",
    )
    resolver = AuditImputationSignoffResolver()

    assert (
        resolver.resolve(
            scenario_id="bushfire",
            run_pair_id="pair-1",
            scenario_content_hash="a" * 64,
            imputation_share=Decimal("0.20"),
        )
        is not None
    )
    assert (
        resolver.resolve(
            scenario_id="flood",
            run_pair_id="pair-1",
            scenario_content_hash="a" * 64,
            imputation_share=Decimal("0.20"),
        )
        is None
    )
    assert (
        resolver.resolve(
            scenario_id="bushfire",
            run_pair_id="pair-1",
            scenario_content_hash="b" * 64,
            imputation_share=Decimal("0.20"),
        )
        is None
    )

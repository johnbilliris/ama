from __future__ import annotations

from typing import Any

from .._clients import get_registry
from .._guards import assert_au_region
from ..measurement.imputation import forward_impute
from ..models.signal import Signal, SignalIngressRequest
from . import audit_manager


def ingest_signal(
    payload: SignalIngressRequest | dict[str, Any],
    *,
    actor: str | None = None,
    trusted_region: str | None = None,
) -> Signal:
    request = payload if isinstance(payload, SignalIngressRequest) else SignalIngressRequest.model_validate(payload)
    raw = request.model_dump(mode="python")
    raw["region"] = trusted_region or request.region
    raw["actor"] = actor or request.actor or "system"
    assert_au_region(
        raw,
        actor=raw["actor"],
        correlation_id=request.correlation_id,
    )

    chain = forward_impute(request.chain)
    raw["chain"] = chain
    if chain.imputed_fields:
        raw["reduced_fidelity"] = True
        raw["advisory_only"] = True
    signal = Signal.model_validate(raw)

    audit_manager.record(
        kind="signal_ingested",
        value_id=signal.id,
        actor=signal.actor,
        references={"signal_id": signal.id},
        payload={
            "kpi_id": signal.kpi_id,
            "scenario_id": signal.scenario_id,
        },
        correlation_id=signal.correlation_id,
    )
    container = get_registry().get("kpi_signals")
    try:
        container.create_item(signal.model_dump(mode="json"))
    except Exception as exc:
        try:
            existing = container.read_item(
                signal.id,
                partition_key=signal.scenario_id,
            )
        except Exception:
            raise
        if existing != signal.model_dump(mode="json"):
            raise RuntimeError("signal id collision with different payload") from exc
    return signal


def enter_degraded_mode(
    *,
    value_id: str,
    reason: str,
    correlation_id: str = "",
) -> None:
    audit_manager.record(
        kind="degraded_mode_entered",
        value_id=value_id,
        actor="system",
        payload={"reason": reason},
        correlation_id=correlation_id,
    )

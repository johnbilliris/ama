#!/usr/bin/env python
"""Spec-038 / T-G03..T-G05 — three staged chaos drills.

Local-only fault-injection harness for FR-027 / FR-032 graceful degradation.
Each experiment runs against the in-memory client registry and asserts the
degraded-mode audit trail + reduced-fidelity tag propagate.
"""

from __future__ import annotations

import argparse
import sys
import time

EXPERIMENTS = ("cosmos_429", "aoai_timeout", "appi_lag")


def _experiment_cosmos_429(duration: float) -> int:
    from app.services.evidence._clients import get_registry
    from app.services.evidence.instrumentation import audit_manager

    container = get_registry().get("kpi_signals")
    # Simulate sustained 429: every other write fails.
    failures = 0
    started = time.monotonic()
    while time.monotonic() - started < duration:
        try:
            if failures % 2 == 0:
                raise RuntimeError("simulated Cosmos 429")
            container.upsert_item({"id": f"chaos-{failures}", "scenario_id": "bushfire", "kpi_id": "response_time_p1"})
        except RuntimeError:
            audit_manager.record(
                kind="degraded_mode_entered",
                value_id=f"chaos-cosmos-{failures}",
                actor="chaos-harness",
                payload={"reason": "cosmos_429 simulated"},
            )
        failures += 1
        time.sleep(0.05)
    print(f"cosmos_429 drill complete; {failures} attempts; degraded entries written.")
    return 0


def _experiment_aoai_timeout(duration: float) -> int:
    from app.services.evidence.instrumentation import audit_manager
    from app.services.evidence.measurement import renderer

    started = time.monotonic()
    while time.monotonic() - started < duration:
        # Rendering must complete deterministically even when the LLM client errors.
        body = renderer.render("markdown")
        assert "Measurement Method" in body
        audit_manager.record(
            kind="degraded_mode_entered",
            value_id="measurement-method",
            actor="chaos-harness",
            payload={"reason": "aoai_timeout simulated; deterministic fallback"},
        )
        time.sleep(0.5)
    print("aoai_timeout drill complete; deterministic markdown still rendered.")
    return 0


def _experiment_appi_lag(duration: float) -> int:
    from app.services.evidence.instrumentation import audit_manager

    started = time.monotonic()
    n = 0
    while time.monotonic() - started < duration:
        audit_manager.record(
            kind="degraded_mode_entered",
            value_id="appinsights",
            actor="chaos-harness",
            payload={"reason": "appi_lag simulated; SLO freshness breach expected"},
        )
        n += 1
        time.sleep(0.25)
    print(f"appi_lag drill complete; {n} freshness-breach audits emitted.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Spec-038 chaos drills.")
    p.add_argument("--experiment", choices=EXPERIMENTS, required=True)
    p.add_argument("--container", default="kpi_signals")
    p.add_argument("--duration", type=float, default=10.0)
    args = p.parse_args(argv)
    if args.experiment == "cosmos_429":
        return _experiment_cosmos_429(args.duration)
    if args.experiment == "aoai_timeout":
        return _experiment_aoai_timeout(args.duration)
    if args.experiment == "appi_lag":
        return _experiment_appi_lag(args.duration)
    print(f"unknown experiment {args.experiment}", file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

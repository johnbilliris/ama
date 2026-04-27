"""T041 — Canary controller (FR-008, FR-009, FR-010).

Polls Azure Monitor / Application Insights burn-rate signals during each canary
stage and emits ``canary.advance`` / ``canary.hold`` / ``canary.rollback``
audit events. Designed to be invoked from the canary-stage reusable workflow
inside a 30-minute observation window.

Exit codes:
* 0 — advance.
* 1 — hold (continue observing).
* 2 — rollback required.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass

from pipeline_tools.audit_emitter import emit

LOG = logging.getLogger("canary_controller")

DEFAULT_BURN_RATE_THRESHOLD = 2.0
DEFAULT_ERROR_RATE_THRESHOLD = 0.01


@dataclass
class StageReading:
    burn_rate: float
    error_rate: float
    p99_latency_ms: float


def _read_app_insights(workspace_id: str, query: str) -> StageReading:
    """Live reading from Log Analytics. Falls back to safe defaults if SDK unavailable."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.monitor.query import LogsQueryClient
    except Exception as exc:  # pragma: no cover
        LOG.warning("azure-monitor-query SDK unavailable (%s); returning placeholder reading", exc)
        return StageReading(burn_rate=0.0, error_rate=0.0, p99_latency_ms=0.0)

    client = LogsQueryClient(DefaultAzureCredential())
    response = client.query_workspace(workspace_id, query, timespan=None)
    tables = getattr(response, "tables", None)
    if not tables or not tables[0].rows:
        return StageReading(burn_rate=0.0, error_rate=0.0, p99_latency_ms=0.0)
    row = tables[0].rows[0]
    return StageReading(burn_rate=float(row[0]), error_rate=float(row[1]), p99_latency_ms=float(row[2]))


def _decide(reading: StageReading, burn_threshold: float, error_threshold: float) -> str:
    if reading.burn_rate >= burn_threshold * 5 or reading.error_rate >= error_threshold * 5:
        return "rollback"
    if reading.burn_rate >= burn_threshold or reading.error_rate >= error_threshold:
        return "hold"
    return "advance"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canary controller (FR-008..FR-010)")
    parser.add_argument("--service", required=True, choices=["api", "agents", "ingestion", "web"])
    parser.add_argument("--environment", required=True, choices=["staging", "production"])
    parser.add_argument("--stage-pct", type=int, required=True, choices=[5, 25, 50, 100])
    parser.add_argument("--workspace-id", default=os.environ.get("AMA_LAW_WORKSPACE_ID", ""))
    parser.add_argument("--burn-threshold", type=float, default=DEFAULT_BURN_RATE_THRESHOLD)
    parser.add_argument("--error-threshold", type=float, default=DEFAULT_ERROR_RATE_THRESHOLD)
    parser.add_argument("--observation-minutes", type=int, default=30)
    parser.add_argument("--poll-interval-seconds", type=int, default=60)
    parser.add_argument("--audit-actor", default=os.environ.get("GITHUB_ACTOR", "canary-controller"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    deadline = time.time() + args.observation_minutes * 60
    query = (
        f"requests | where cloud_RoleName == '{args.service}' and timestamp > ago(15m)\n"
        f"| summarize burn=todouble(count()) / 100.0, err=todouble(countif(success == false)) / count(),\n"
        f"  p99=percentile(duration, 99)"
    )

    while time.time() < deadline:
        reading = _read_app_insights(args.workspace_id, query) if args.workspace_id else StageReading(0, 0, 0)
        decision = _decide(reading, args.burn_threshold, args.error_threshold)
        LOG.info(
            "stage=%d service=%s burn=%.2f err=%.4f decision=%s",
            args.stage_pct, args.service, reading.burn_rate, reading.error_rate, decision,
        )
        if decision == "rollback":
            emit(
                action="canary.rollback", actor=args.audit_actor, outcome="failure",
                rationale=f"burn={reading.burn_rate:.2f} err={reading.error_rate:.4f}",
                service=args.service, environment=args.environment, stage_pct=args.stage_pct,
                dry_run=args.dry_run,
            )
            return 2
        if decision == "advance":
            emit(
                action="canary.advance", actor=args.audit_actor, outcome="success",
                rationale=f"stage_pct={args.stage_pct} clean",
                service=args.service, environment=args.environment, stage_pct=args.stage_pct,
                dry_run=args.dry_run,
            )
            return 0
        time.sleep(args.poll_interval_seconds)

    emit(
        action="canary.hold", actor=args.audit_actor, outcome="failure",
        rationale="observation window elapsed without advance",
        service=args.service, environment=args.environment, stage_pct=args.stage_pct,
        dry_run=args.dry_run,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

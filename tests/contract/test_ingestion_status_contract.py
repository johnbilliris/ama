from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.services.ingestion.pipeline_base import PipelineMetrics
from app.services.ingestion.pipeline_status_store import PipelineStatusStore

from apps.ingestion.worker import PipelineWorker


def _status_row(
    *,
    pipeline_id: str,
    replica_id: str,
    heartbeat_at: datetime,
    last_successful_poll: datetime | None,
    signals_last_hour: int,
    dedup_hits: int,
    dedup_total: int,
    dedup_rate_percent: float,
    breaker_state: str = "closed",
    health_state: str = "healthy",
    freshness_state: str = "fresh",
) -> dict:
    return {
        "pipelineId": pipeline_id,
        "sourceClass": "authoritative",
        "dataSourceIds": ["bom-warnings"],
        "circuitBreakerState": breaker_state,
        "lastSuccessfulPoll": last_successful_poll.isoformat() if last_successful_poll else None,
        "signalsLastHour": signals_last_hour,
        "dedupHitRatePercent": dedup_rate_percent,
        "normalisationLatencyP95Ms": 120.0,
        "deadLetterDepth": 0,
        "health": {
            "state": health_state,
            "taskState": "running",
            "reason": None,
            "windowDedupHits": dedup_hits,
            "windowDedupTotal": dedup_total,
        },
        "breaker": {"state": breaker_state, "consecutiveFailures": 0, "totalTrips": 0},
        "freshness": {"state": freshness_state, "ageSeconds": 10, "expectedUpdateSeconds": 60},
        "heartbeatAt": heartbeat_at.isoformat(),
        "replicaId": replica_id,
    }


def test_pipeline_metrics_are_bounded_and_use_rolling_windows() -> None:
    metrics = PipelineMetrics("pipeline-a")

    for i in range(metrics.latencies.maxlen + 20):
        metrics.record_ingestion(float(i))
    assert len(metrics.latencies) == metrics.latencies.maxlen

    now = datetime.now(UTC)
    metrics._dedup_events.appendleft((now - timedelta(seconds=PipelineMetrics.ROLLING_DEDUP_SECONDS + 1), True))
    metrics._signal_events.appendleft(now - timedelta(seconds=PipelineMetrics.ROLLING_SIGNALS_SECONDS + 1))
    dedup_counts = metrics.dedup_window_counts(now=now)
    assert dedup_counts["total"] == len(metrics._dedup_events)
    assert all((now - ts).total_seconds() <= PipelineMetrics.ROLLING_DEDUP_SECONDS for ts, _ in metrics._dedup_events)
    assert all((now - ts).total_seconds() <= PipelineMetrics.ROLLING_SIGNALS_SECONDS for ts in metrics._signal_events)


def test_status_store_aggregates_two_replicas_with_exact_contract_fields() -> None:
    store = PipelineStatusStore(stale_after_seconds=90)
    now = datetime.now(UTC)

    store.record(
        _status_row(
            pipeline_id="bom-warnings",
            replica_id="replica-a",
            heartbeat_at=now,
            last_successful_poll=now - timedelta(seconds=5),
            signals_last_hour=30,
            dedup_hits=3,
            dedup_total=10,
            dedup_rate_percent=30.0,
        )
    )
    store.record(
        _status_row(
            pipeline_id="bom-warnings",
            replica_id="replica-b",
            heartbeat_at=now,
            last_successful_poll=now - timedelta(seconds=3),
            signals_last_hour=20,
            dedup_hits=5,
            dedup_total=10,
            dedup_rate_percent=50.0,
        )
    )

    summary = store.summary()
    assert summary["totalSignalsLastHour"] == 50
    assert summary["degradedSources"] == 0
    row = summary["pipelines"][0]
    assert set(row.keys()) == {
        "pipelineId",
        "sourceClass",
        "dataSourceIds",
        "circuitBreakerState",
        "lastSuccessfulPoll",
        "signalsLastHour",
        "dedupHitRatePercent",
        "normalisationLatencyP95Ms",
        "deadLetterDepth",
        "health",
        "breaker",
        "freshness",
    }
    assert row["signalsLastHour"] == 50
    assert row["dedupHitRatePercent"] == 40.0


def test_status_store_marks_stale_worker_from_heartbeat_timeout() -> None:
    store = PipelineStatusStore(stale_after_seconds=30)
    old = datetime.now(UTC) - timedelta(seconds=120)
    store.record(
        _status_row(
            pipeline_id="bom-observations",
            replica_id="replica-old",
            heartbeat_at=old,
            last_successful_poll=old,
            signals_last_hour=0,
            dedup_hits=0,
            dedup_total=0,
            dedup_rate_percent=0.0,
            health_state="healthy",
            freshness_state="unknown",
        )
    )

    row = store.summary()["pipelines"][0]
    assert row["health"]["state"] in {"stale", "degraded"}


class _SnapshotPipeline:
    def __init__(self) -> None:
        self.source_class = "authoritative"
        self.data_source_ids = ["bom-warnings"]

    def _pipeline_status_snapshot(self, *, reason=None) -> dict:
        return {
            "pipelineId": "status-pipeline",
            "sourceClass": "authoritative",
            "dataSourceIds": ["bom-warnings"],
            "circuitBreakerState": "closed",
            "lastSuccessfulPoll": datetime.now(UTC).isoformat(),
            "signalsLastHour": 1,
            "dedupHitRatePercent": 0.0,
            "normalisationLatencyP95Ms": 1.0,
            "deadLetterDepth": 0,
            "health": {"state": "healthy", "taskState": "running", "reason": reason},
            "breaker": {"state": "closed", "consecutiveFailures": 0, "totalTrips": 0},
            "freshness": {"state": "fresh", "ageSeconds": 1, "expectedUpdateSeconds": 60},
        }


@pytest.mark.asyncio
async def test_worker_status_reports_failed_task_state_truthfully() -> None:
    async def _boom() -> None:
        raise RuntimeError("task-failed")

    worker = PipelineWorker()
    worker._running = True
    worker._pipelines = {"status-pipeline": _SnapshotPipeline()}
    task = asyncio.create_task(_boom())
    await asyncio.sleep(0)
    worker._tasks = {"status-pipeline": task}

    status = worker.get_status()
    assert status["pipelines"][0]["health"]["taskState"] == "failed"
    assert status["pipelines"][0]["health"]["state"] == "failed"


@pytest.mark.asyncio
async def test_worker_status_reports_stopped_task_state_truthfully() -> None:
    async def _ok() -> None:
        return None

    worker = PipelineWorker()
    worker._running = True
    worker._pipelines = {"status-pipeline": _SnapshotPipeline()}
    task = asyncio.create_task(_ok())
    await asyncio.sleep(0)
    worker._tasks = {"status-pipeline": task}

    status = worker.get_status()
    assert status["pipelines"][0]["health"]["taskState"] == "stopped"
    assert status["pipelines"][0]["health"]["state"] == "stopped"

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


class PipelineStatusStore:
    def __init__(self, *, stale_after_seconds: int = 90) -> None:
        self._stale_after_seconds = max(5, int(stale_after_seconds))
        self._memory_rows: dict[str, dict[str, Any]] = {}
        self._redis_key = "ingestion:pipeline_status:v1"
        self._redis = self._build_redis_client()

    @staticmethod
    def _build_redis_client() -> Any | None:
        host = os.environ.get("REDIS_HOST", "").strip()
        if not host:
            return None
        try:
            import redis

            port = int(os.environ.get("REDIS_PORT", "6380"))
            use_ssl = str(os.environ.get("REDIS_SSL", "1")).strip() != "0"
            return redis.Redis(
                host=host,
                port=port,
                ssl=use_ssl,
                decode_responses=True,
                socket_timeout=5,
            )
        except Exception:
            return None

    def record(self, status: dict[str, Any]) -> None:
        pipeline_id = str(status.get("pipelineId", "")).strip()
        if not pipeline_id:
            return

        row = dict(status)
        row.setdefault("heartbeatAt", datetime.now(UTC).isoformat())
        replica_id = str(row.get("replicaId") or os.environ.get("HOSTNAME") or "local").strip()
        row["replicaId"] = replica_id
        field = f"{pipeline_id}:{replica_id}"
        self._memory_rows[field] = row

        if self._redis is not None:
            try:
                self._redis.hset(self._redis_key, field, json.dumps(row, separators=(",", ":")))
                self._redis.expire(self._redis_key, max(300, self._stale_after_seconds * 4))
            except Exception:
                pass

    def clear(self) -> None:
        self._memory_rows.clear()
        if self._redis is not None:
            try:
                self._redis.delete(self._redis_key)
            except Exception:
                pass

    def list_pipeline_statuses(self) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        now = datetime.now(UTC)
        for row in self._merged_rows().values():
            pipeline_id = str(row.get("pipelineId", "")).strip()
            if not pipeline_id:
                continue
            grouped[pipeline_id].append(dict(row))

        snapshots: list[dict[str, Any]] = []
        for pipeline_id, rows in grouped.items():
            snapshots.append(self._aggregate_pipeline(pipeline_id, rows, now=now))
        snapshots.sort(key=lambda row: str(row.get("pipelineId", "")))
        return snapshots

    def _merged_rows(self) -> dict[str, dict[str, Any]]:
        merged = dict(self._memory_rows)
        if self._redis is None:
            return merged
        try:
            for field, payload in self._redis.hgetall(self._redis_key).items():
                if field in merged:
                    continue
                row = json.loads(payload)
                if isinstance(row, dict):
                    merged[str(field)] = row
        except Exception:
            return merged
        return merged

    def summary(self) -> dict[str, Any]:
        pipelines = self.list_pipeline_statuses()
        degraded = [row for row in pipelines if str(row.get("health", {}).get("state", "")).lower() != "healthy"]
        return {
            "pipelines": pipelines,
            "totalSignalsLastHour": sum(int(row.get("signalsLastHour", 0)) for row in pipelines),
            "degradedSources": len(degraded),
        }

    def _aggregate_pipeline(
        self,
        pipeline_id: str,
        rows: list[dict[str, Any]],
        *,
        now: datetime,
    ) -> dict[str, Any]:
        def _breaker_rank(value: str) -> int:
            return {"open": 3, "half_open": 2, "closed": 1}.get(value, 0)

        freshest = max(
            rows, key=lambda row: _parse_timestamp(row.get("heartbeatAt")) or datetime.min.replace(tzinfo=UTC)
        )
        fresh_rows = []
        stale_count = 0
        for row in rows:
            heartbeat = _parse_timestamp(row.get("heartbeatAt"))
            if heartbeat is None:
                stale_count += 1
                continue
            if (now - heartbeat).total_seconds() > self._stale_after_seconds:
                stale_count += 1
                continue
            fresh_rows.append(row)

        active_rows = fresh_rows if fresh_rows else [freshest]
        last_success = max(
            (_parse_timestamp(row.get("lastSuccessfulPoll")) for row in active_rows),
            default=None,
        )
        data_source_ids: set[str] = set()
        for row in active_rows:
            for source_id in row.get("dataSourceIds", []):
                text = str(source_id).strip()
                if text:
                    data_source_ids.add(text)

        dedup_hits = 0
        dedup_total = 0
        dedup_fallback: list[float] = []
        for row in active_rows:
            health = row.get("health", {}) if isinstance(row.get("health"), dict) else {}
            hits = health.get("windowDedupHits")
            total = health.get("windowDedupTotal")
            if isinstance(hits, int) and isinstance(total, int):
                dedup_hits += max(0, hits)
                dedup_total += max(0, total)
            else:
                dedup_fallback.append(float(row.get("dedupHitRatePercent", 0.0)))
        if dedup_total > 0:
            dedup_hit_rate_percent = round((dedup_hits / dedup_total) * 100.0, 1)
        else:
            dedup_hit_rate_percent = (
                round(
                    sum(dedup_fallback) / len(dedup_fallback),
                    1,
                )
                if dedup_fallback
                else 0.0
            )

        breaker_state = "closed"
        for row in active_rows:
            candidate = str(row.get("circuitBreakerState", "")).strip()
            if _breaker_rank(candidate) > _breaker_rank(breaker_state):
                breaker_state = candidate

        health_states = [
            str((row.get("health", {}) if isinstance(row.get("health"), dict) else {}).get("state", "healthy"))
            for row in active_rows
        ]
        health_state = "healthy"
        if any(state == "failed" for state in health_states):
            health_state = "failed"
        elif all(state == "stopped" for state in health_states):
            health_state = "stopped"
        elif stale_count > 0 and not fresh_rows:
            health_state = "stale"
        elif any(state in {"degraded", "stale"} for state in health_states) or breaker_state == "open":
            health_state = "degraded"

        freshness_state = "unknown"
        freshness_ages = []
        freshness_expected = []
        for row in active_rows:
            freshness = row.get("freshness", {}) if isinstance(row.get("freshness"), dict) else {}
            state = str(freshness.get("state", "unknown"))
            if state == "stale":
                freshness_state = "stale"
            elif freshness_state != "stale" and state == "fresh":
                freshness_state = "fresh"
            age = freshness.get("ageSeconds")
            expected = freshness.get("expectedUpdateSeconds")
            if isinstance(age, int):
                freshness_ages.append(age)
            if isinstance(expected, int):
                freshness_expected.append(expected)

        if freshness_state == "unknown" and stale_count and not fresh_rows:
            freshness_state = "stale"

        return {
            "pipelineId": pipeline_id,
            "sourceClass": str(freshest.get("sourceClass", "unknown")),
            "dataSourceIds": sorted(data_source_ids),
            "circuitBreakerState": breaker_state,
            "lastSuccessfulPoll": last_success.isoformat() if last_success else None,
            "signalsLastHour": sum(int(row.get("signalsLastHour", 0)) for row in active_rows),
            "dedupHitRatePercent": dedup_hit_rate_percent,
            "normalisationLatencyP95Ms": max(float(row.get("normalisationLatencyP95Ms", 0.0)) for row in active_rows),
            "deadLetterDepth": sum(int(row.get("deadLetterDepth", 0)) for row in active_rows),
            "health": {
                "state": health_state,
                "taskState": "failed"
                if health_state == "failed"
                else ("stopped" if health_state == "stopped" else "running"),
                "reason": None if health_state == "healthy" else json.dumps({"staleReplicas": stale_count}),
            },
            "breaker": {
                "state": breaker_state,
                "replicas": len(rows),
                "staleReplicas": stale_count,
            },
            "freshness": {
                "state": freshness_state,
                "ageSeconds": max(freshness_ages) if freshness_ages else None,
                "expectedUpdateSeconds": max(freshness_expected) if freshness_expected else None,
            },
        }


STATUS_STORE = PipelineStatusStore(stale_after_seconds=int(os.environ.get("INGESTION_STATUS_STALE_SECONDS", "90")))


def get_pipeline_status_store() -> PipelineStatusStore:
    return STATUS_STORE

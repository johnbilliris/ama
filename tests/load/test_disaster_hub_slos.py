"""Staging-only real HTTP SLO harness for spec-001 acceptance metrics.

This harness is intentionally skipped unless explicit staging env vars are set.
It does not claim NFR pass by itself; it only records and enforces thresholds
when the operator provides a staging endpoint and scenario identifiers.
"""

from __future__ import annotations

import json
import os
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from tests.staging_gates import measurement_staging_enabled

SITUATION_REFRESH_P95_ONLINE_S = 3.0
SITUATION_REFRESH_P95_64KBPS_S = 10.0
INGEST_TO_VISIBILITY_P95_S = 60.0
ACTION_ROUND_TRIP_P95_S = 2.0
MIN_SAMPLE_COUNT = 30


@dataclass(frozen=True)
class ProbeResult:
    metric: str
    samples: int
    p95_seconds: float


def _api_base() -> str:
    base = os.getenv("AMA_STAGING_API_BASE_URL", "").strip().rstrip("/")
    if not base:
        raise RuntimeError("AMA_STAGING_API_BASE_URL is required for staging SLO harness")
    return base


def _percentile(values: list[float], p: float) -> float:
    if not values:
        raise AssertionError("cannot compute percentile for empty samples")
    ordered = sorted(values)
    index = int(round((p / 100.0) * (len(ordered) - 1)))
    index = max(0, min(index, len(ordered) - 1))
    return ordered[index]


def _require_samples(values: list[float], *, minimum: int = MIN_SAMPLE_COUNT) -> None:
    if len(values) < minimum:
        raise AssertionError(f"insufficient sample count: {len(values)} < {minimum}")


def _request_json(method: str, path: str, *, body: dict | None = None, network_profile: str = "online") -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{_api_base()}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "x-ama-network-profile": network_profile,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - staging URL is operator-provided
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        raise AssertionError(f"request failed {method} {path} -> HTTP {exc.code}") from exc


def _latency_probe(
    *,
    metric: str,
    samples: int,
    request_factory: Callable[[str], None],
    profile: str,
) -> ProbeResult:
    durations: list[float] = []
    for _ in range(samples):
        start = time.perf_counter()
        request_factory(profile)
        durations.append(time.perf_counter() - start)

    _require_samples(durations)
    return ProbeResult(metric=metric, samples=len(durations), p95_seconds=_percentile(durations, 95.0))


def _staging_samples() -> int:
    return int(os.getenv("AMA_SLO_SAMPLE_COUNT", str(MIN_SAMPLE_COUNT)))


def _incident_id() -> str:
    value = os.getenv("AMA_SLO_INCIDENT_ID", "").strip()
    if not value:
        raise RuntimeError("AMA_SLO_INCIDENT_ID is required for staging SLO harness")
    return value


def _situation_refresh_request(profile: str) -> None:
    _request_json("GET", f"/api/incidents/{_incident_id()}/dashboard", network_profile=profile)


def _action_round_trip_request(profile: str) -> None:
    path = os.getenv("AMA_SLO_ACTION_PATH", "/api/health")
    method = os.getenv("AMA_SLO_ACTION_METHOD", "GET").upper()
    body = None
    if method == "POST":
        body = {"probe": "action-round-trip", "timestamp": time.time()}
    _request_json(method, path, body=body, network_profile=profile)


def _ingest_to_visibility_request(profile: str) -> None:
    incident_id = _incident_id()
    signal = {
        "source": {
            "dataSourceId": "failover-drill-slo",
            "name": "failover-drill-slo",
            "kind": "authoritative",
        },
        "incidentId": incident_id,
        "category": "weather",
        "occurredAt": "2026-09-15T00:00:00Z",
        "receivedAt": "2026-09-15T00:00:01Z",
        "location": {
            "type": "Point",
            "coordinates": [151.2093, -33.8688],
            "precisionMeters": 100,
        },
        "payload": {"probe": "slo-ingest"},
        "confidenceScore": 1.0,
        "freshnessScore": 1.0,
        "validationStatus": "pending",
        "provenance": {
            "collectionMethod": "failover-drill",
            "sourceUri": "failover-drill://slo",
        },
    }
    posted = _request_json("POST", "/api/signals", body=signal, network_profile=profile)
    signal_id = posted.get("signalId")
    if not signal_id:
        raise AssertionError("signal ingest response is missing signalId")

    deadline = time.time() + 60
    while time.time() < deadline:
        listed = _request_json("GET", f"/api/signals?incidentId={incident_id}", network_profile=profile)
        records = listed if isinstance(listed, list) else listed.get("items", [])
        if any(str(item.get("signalId", "")) == str(signal_id) for item in records if isinstance(item, dict)):
            return
        time.sleep(1.0)
    raise AssertionError("ingested signal did not become visible within 60 seconds")


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled() or not os.getenv("AMA_STAGING_API_BASE_URL"),
    reason="staging-only harness requires AMA_STAGING_MEASUREMENT=1 and AMA_STAGING_API_BASE_URL",
)
def test_situation_refresh_p95_online_and_64kbps() -> None:
    samples = _staging_samples()

    online = _latency_probe(
        metric="situation-refresh-online",
        samples=samples,
        request_factory=_situation_refresh_request,
        profile="online",
    )
    assert online.p95_seconds <= SITUATION_REFRESH_P95_ONLINE_S

    throttled = _latency_probe(
        metric="situation-refresh-64kbps",
        samples=samples,
        request_factory=_situation_refresh_request,
        profile="throttle-64kbps",
    )
    assert throttled.p95_seconds <= SITUATION_REFRESH_P95_64KBPS_S


def test_slo_helper_percentile_is_stable() -> None:
    values = [0.1, 0.2, 0.3, 0.4, 0.5]
    assert _percentile(values, 95.0) == 0.5
    assert statistics.mean(values) > 0


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled() or not os.getenv("AMA_STAGING_API_BASE_URL"),
    reason="staging-only harness requires AMA_STAGING_MEASUREMENT=1 and AMA_STAGING_API_BASE_URL",
)
def test_ingest_to_visibility_p95_and_disconnect_profile() -> None:
    samples = _staging_samples()

    online = _latency_probe(
        metric="ingest-to-visibility",
        samples=samples,
        request_factory=_ingest_to_visibility_request,
        profile="online",
    )
    assert online.p95_seconds <= INGEST_TO_VISIBILITY_P95_S

    # The disconnect profile is a seam hook consumed by staging adapters.
    _ingest_to_visibility_request("disconnect-30m")


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled() or not os.getenv("AMA_STAGING_API_BASE_URL"),
    reason="staging-only harness requires AMA_STAGING_MEASUREMENT=1 and AMA_STAGING_API_BASE_URL",
)
def test_action_round_trip_p95() -> None:
    samples = _staging_samples()
    result = _latency_probe(
        metric="action-round-trip",
        samples=samples,
        request_factory=_action_round_trip_request,
        profile="online",
    )
    assert result.p95_seconds <= ACTION_ROUND_TRIP_P95_S

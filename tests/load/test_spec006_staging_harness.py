"""Spec 006 staging harness for SC-001 and SC-002.

Skipped by default unless AMA_SPEC006_STAGING_MEASUREMENT=1 and
AMA_STAGING_API_BASE_URL are set.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.load.spec006_evidence_validator import _raw_sha256
from tests.load.spec006_load_payload import build_canonical_ingest_payload

MIN_SAMPLES = 30


def _enabled() -> bool:
    return os.getenv("AMA_SPEC006_STAGING_MEASUREMENT", "0") == "1"


def _base_url() -> str:
    return os.getenv("AMA_STAGING_API_BASE_URL", "").strip().rstrip("/")


def _sample_count() -> int:
    return max(MIN_SAMPLES, int(os.getenv("AMA_SPEC006_SAMPLE_COUNT", str(MIN_SAMPLES))))


def _write_raw_output(name: str, payload: dict[str, object]) -> None:
    out_dir = Path(os.getenv("AMA_SPEC006_RAW_OUTPUT_DIR", "artifacts/spec006-load"))
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (out_dir / f"{timestamp}-{name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _request_json(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{_base_url()}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - operator-provided staging URL
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    index = int(round(0.95 * (len(ordered) - 1)))
    return float(ordered[index])


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not _enabled() or not _base_url(),
    reason="set AMA_SPEC006_STAGING_MEASUREMENT=1 and AMA_STAGING_API_BASE_URL to run staging harness",
)
def test_sc001_source_publication_to_persist_latency_p95() -> None:
    source_id = os.getenv("AMA_LOAD_SOURCE_ID", "bom-warnings").strip() or "bom-warnings"
    incident_id = os.getenv("AMA_LOAD_INCIDENT_ID", "inc-1")
    samples: list[float] = []

    for _ in range(_sample_count()):
        payload = build_canonical_ingest_payload(source_id=source_id, incident_id=incident_id)
        start = time.perf_counter()
        created = _request_json("POST", "/api/signals", body=payload)
        signal_id = str(created.get("signalId", ""))
        deadline = time.time() + 90.0
        while True:
            listed = _request_json("GET", f"/api/signals?incidentId={incident_id}&limit=200")
            rows = listed if isinstance(listed, list) else listed.get("items", [])
            if any(str(row.get("signalId", "")) == signal_id for row in rows if isinstance(row, dict)):
                break
            if time.time() >= deadline:
                raise AssertionError("SC-001 visibility deadline exceeded")
            time.sleep(0.25)
        samples.append(time.perf_counter() - start)

    assert len(samples) >= MIN_SAMPLES
    measured = _p95(samples)
    raw = {
        "metric": "sc001_latency_p95_seconds",
        "samples": samples,
        "sampleCount": len(samples),
        "p95": measured,
        "threshold": 90.0,
        "outcome": "PASS" if measured <= 90.0 else "FAIL",
        "rawSha256": _raw_sha256(samples),
    }
    _write_raw_output("sc001", raw)
    assert measured <= 90.0


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not _enabled() or not _base_url(),
    reason="set AMA_SPEC006_STAGING_MEASUREMENT=1 and AMA_STAGING_API_BASE_URL to run staging harness",
)
def test_sc002_sustained_throughput_canonical_ingestion() -> None:
    source_id = os.getenv("AMA_LOAD_SOURCE_ID", "bom-warnings").strip() or "bom-warnings"
    incident_id = os.getenv("AMA_LOAD_INCIDENT_ID", "inc-1")
    target_samples = _sample_count()

    successes = 0
    raw_times: list[float] = []
    start = time.perf_counter()
    for _ in range(target_samples):
        payload = build_canonical_ingest_payload(source_id=source_id, incident_id=incident_id)
        request_start = time.perf_counter()
        _request_json("POST", "/api/signals", body=payload)
        raw_times.append(time.perf_counter() - request_start)
        successes += 1
    duration = time.perf_counter() - start

    assert successes >= MIN_SAMPLES
    throughput_per_hour = (successes / duration) * 3600.0
    raw = {
        "metric": "sc002_throughput_per_hour",
        "samples": raw_times,
        "sampleCount": successes,
        "durationSeconds": duration,
        "throughputPerHour": throughput_per_hour,
        "threshold": 50000.0,
        "outcome": "PASS" if throughput_per_hour >= 50000.0 else "FAIL",
        "rawSha256": _raw_sha256(raw_times),
    }
    _write_raw_output("sc002", raw)
    assert throughput_per_hour >= 50000.0

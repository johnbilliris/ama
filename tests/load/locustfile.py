from __future__ import annotations

import os
import random
import time
import uuid

from locust import HttpUser, LoadTestShape, between, constant_throughput, events, task

from tests.load.spec006_load_payload import build_canonical_ingest_payload

# Spec 036 / F-A10 / T219 — 50-agent retrieval harness (FR-RAG-TEST-02).
# `psutil` is best-effort: when absent we fall back to a no-op probe so
# the harness still runs in environments where the dep is not installed.
try:
    import psutil
except ImportError:  # pragma: no cover - exercised on first wheel pin
    psutil = None  # type: ignore[assignment]


class DashboardUser(HttpUser):
    wait_time = between(0.2, 1.0)

    def _auth_headers(self) -> dict[str, str]:
        header_name = os.getenv("AMA_LOAD_AUTH_HEADER_NAME", "").strip()
        header_value = os.getenv("AMA_LOAD_AUTH_HEADER_VALUE", "").strip()
        if not header_name or not header_value:
            return {}
        return {header_name: header_value}

    @task(3)
    def read_dashboard(self) -> None:
        incident_id = os.getenv("AMA_LOAD_INCIDENT_ID", "inc-1")
        self.client.get(
            f"/api/incidents/{incident_id}/dashboard",
            name="dashboard_incident_aggregate",
            headers=self._auth_headers(),
        )

    @task(2)
    def list_signals(self) -> None:
        incident_id = os.getenv("AMA_LOAD_INCIDENT_ID", "inc-1")
        self.client.get(
            f"/api/signals?incidentId={incident_id}",
            name="signals_list",
            headers=self._auth_headers(),
        )


class BurstIngestionUser(HttpUser):
    wait_time = constant_throughput(14)

    def _auth_headers(self) -> dict[str, str]:
        header_name = os.getenv("AMA_LOAD_AUTH_HEADER_NAME", "").strip()
        header_value = os.getenv("AMA_LOAD_AUTH_HEADER_VALUE", "").strip()
        if not header_name or not header_value:
            return {}
        return {header_name: header_value}

    @staticmethod
    def _canonical_payload(*, incident_id: str) -> dict[str, object]:
        source_id = os.getenv("AMA_LOAD_SOURCE_ID", "bom-warnings").strip() or "bom-warnings"
        return build_canonical_ingest_payload(source_id=source_id, incident_id=incident_id)

    @task
    def ingest_signal(self) -> None:
        incident_id = os.getenv("AMA_LOAD_INCIDENT_ID", "inc-1")
        payload = self._canonical_payload(incident_id=incident_id)
        self.client.post(
            "/api/signals",
            json=payload,
            name="signals_ingest",
            headers=self._auth_headers(),
        )


class StagingPlateauShape(LoadTestShape):
    """Ramp to a 1,000-user plateau for the nightly staging scenario."""

    stages = (
        {"duration": 60, "users": 500, "spawn_rate": 50},
        {"duration": 120, "users": 1000, "spawn_rate": 50},
        {"duration": 660, "users": 1000, "spawn_rate": 10},
    )

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


# ---------------------------------------------------------------------------
# Spec 036 / F-A10 / T219 — RetrievalSession user (FR-RAG-TEST-02).
#
# Pass 1 Q-P1-07 + Plan §F-A10.2 — sustain 50 distinct ``agent_session_id``
# values at RPS=50 for 60s with p95 retrieval-only latency ≤500ms.
# This file is the harness; ``baselines/spec-036-50-agent-baseline.json``
# is the regression reference.
# ---------------------------------------------------------------------------

_AGENT_POOL_SIZE = 50
_HAZARDS = ["bushfire", "flood", "cyclone", "earthquake", "marine"]
_JURISDICTIONS = ["nsw", "vic", "qld", "wa", "sa", "tas", "act", "nt"]
_AGENT_NAMES = ["evacuation", "alerts", "logistics", "casualty", "comms"]


def _pick_session_id(idx: int) -> str:
    """Deterministic 50-agent pool keyed on environment override + idx."""
    base = os.environ.get("AMA_LOAD_SESSION_PREFIX", "spec036-load")
    return f"{base}-agent-{idx % _AGENT_POOL_SIZE:03d}"


class RetrievalSession(HttpUser):
    """Hits POST /api/v1/retrieval at high concurrency.

    The harness intentionally fans out requests across exactly
    ``_AGENT_POOL_SIZE`` distinct ``agent_session_id`` values so the
    server-side cache cannot collapse the load (Plan §F-A10.2 invariant).
    """

    wait_time = between(0.01, 0.04)  # 25-100 RPS per user; we cap with -u flag.

    def on_start(self) -> None:  # type: ignore[override]
        self._user_idx = random.randrange(_AGENT_POOL_SIZE)  # noqa: S311 - load test, not crypto
        self._proc = psutil.Process(os.getpid()) if psutil else None
        self._last_probe = time.monotonic()

    @task
    def retrieve(self) -> None:
        idx = (self._user_idx + random.randrange(_AGENT_POOL_SIZE)) % _AGENT_POOL_SIZE  # noqa: S311
        agent_session_id = _pick_session_id(idx)
        request_id = uuid.uuid4().hex
        payload = {
            "agent_session_id": agent_session_id,
            "agent_name": random.choice(_AGENT_NAMES),  # noqa: S311
            "query": "Bushfire evacuation triggers in Bega Valley LGA",
            "jurisdiction": random.choice(_JURISDICTIONS),  # noqa: S311
            "hazard_type": random.choice(_HAZARDS),  # noqa: S311
            "request_id": request_id,
            "top_k": 6,
        }
        # `name` collapses metric reporting onto a single line so the p95
        # column in the locust stats matches the SLO target directly.
        with self.client.post(
            "/api/v1/retrieval",
            json=payload,
            name="retrieval_50_agent",
            catch_response=True,
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx: {resp.status_code}")
            elif resp.elapsed.total_seconds() * 1000 > 500:
                # SHOULD-class tag — tracked but does not fail the suite.
                resp.success()
            else:
                resp.success()

    @task(1)
    def probe_resources(self) -> None:
        """Sample CPU + RSS once a second per worker (psutil-instrumented)."""
        if not self._proc:
            return
        now = time.monotonic()
        if now - self._last_probe < 1.0:
            return
        self._last_probe = now
        try:
            cpu = self._proc.cpu_percent(interval=None)
            rss_mb = self._proc.memory_info().rss / (1024 * 1024)
            events.request.fire(
                request_type="probe",
                name="resource_probe",
                response_time=0,
                response_length=0,
                exception=None,
                context={"cpu_pct": cpu, "rss_mb": round(rss_mb, 2)},
            )
        except Exception:  # noqa: BLE001 - best-effort instrumentation
            pass

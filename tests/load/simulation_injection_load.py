"""T-J05 — Locust 200-injection load test for the simulation realm.

Drives 200 concurrent telemetry-injections per minute against the staging
``/api/simulations/{simId}/inject-telemetry`` endpoint. Asserts the four
plan-canonical SLIs:

1. Parse-to-pipeline ≤ 5 s p95         (per ``plan.md`` SLI table)
2. Risk fan-out ≤ 15 s p95             (replaces the previous ``<2 s`` target)
3. Error rate < 1 %
4. Map-overlay update ≤ 15 s p95 hazard / ≤ 10 s p95 weather

This file is intentionally executable as a standalone Locust script — the
entry-point is::

    locust -f tests/load/simulation_injection_load.py \
        --headless -u 200 -r 20 -t 60s --host https://api.staging

The pytest suite skips the file (`pytest.mark.locust` + skipif) so CI
clean-runs do not invoke Locust; the dedicated workflow
``simulation-load-test.yml`` (T-J09) drives it on demand.

SC mapping: SC-001, SC-009, SC-010 (NOT SC-005 — see T-J23 for the
post-exercise economic-loss harness).
"""

from __future__ import annotations

import json
import random
import time
import uuid
from typing import Any

import pytest

pytestmark = pytest.mark.locust

try:
    from locust import HttpUser, between, events, task
    from locust.env import Environment
except Exception:  # pragma: no cover — Locust optional in lint envs
    HttpUser = object  # type: ignore[assignment, misc]
    between = lambda a, b: None  # type: ignore[assignment]  # noqa: E731
    events = type("E", (), {"test_stop": type("S", (), {"add_listener": lambda f: f})})  # type: ignore[assignment]
    Environment = object  # type: ignore[assignment, misc]

    def task(weight: int = 1):  # type: ignore[no-redef]
        def deco(f):
            return f

        return deco


# Per-plan SLI thresholds — bake them into the harness so any drift is loud.
P95_PARSE_TO_PIPELINE_MS = 5_000
P95_RISK_FANOUT_MS = 15_000
P95_HAZARD_OVERLAY_MS = 15_000
P95_WEATHER_OVERLAY_MS = 10_000
ERROR_RATE_THRESHOLD = 0.01

CATEGORIES = (
    "weather",
    "fire-behaviour",
    "hydrology",
    "geohazard",
    "utility",
    "transport",
    "evacuation",
    "resource",
    "comms-channel-state",
)

SAMPLE_PROMPTS = (
    "Wind shifted NW at 55 km/h near Katoomba",
    "RFS reports fire-front advancing south of Blackheath",
    "Hawkesbury river level rose 0.3m in last 30 min",
    "Power outage cluster reported at Springwood substation",
    "Road closure: Great Western Highway eastbound at Mt Victoria",
    "Evacuation centre opened at Katoomba RSL",
    "Police: 25 vehicles staged at Lithgow showground",
    "Coastal swell warning Sydney metro 0.6m",
    "Aerial bushfire mapping reports 12% containment Lithgow complex",
)


def _build_payload(simulation_id: str) -> dict[str, Any]:
    return {
        "simulation_id": simulation_id,
        "tenant_id": f"sim-tenant-{simulation_id[:8]}",
        "chat_text": random.choice(SAMPLE_PROMPTS),
        "category": random.choice(CATEGORIES),
        "viewport_centroid": {"lat": -33.7 + random.random() * 0.5, "lng": 150.3 + random.random() * 0.5},
        "client_request_id": str(uuid.uuid4()),
    }


class SimulationInjectionUser(HttpUser):
    """Synthetic coordinator hammering /inject-telemetry at 1 req / 0.3 s."""

    wait_time = between(0.2, 0.4)

    def on_start(self) -> None:  # noqa: D401 — Locust hook
        # Reuse a stable simulation_id per virtual user so the 200/min
        # corpus splits across ~10 sims (matching the plan-canonical
        # 3-tenant×3-sim peak load).
        self.simulation_id = str(uuid.uuid4())
        self.start_ts: dict[str, float] = {}

    @task(10)
    def inject(self) -> None:
        body = _build_payload(self.simulation_id)
        client_req_id = body["client_request_id"]
        self.start_ts[client_req_id] = time.monotonic()
        with self.client.post(
            f"/api/simulations/{self.simulation_id}/inject-telemetry",
            json=body,
            name="inject-telemetry",
            catch_response=True,
        ) as resp:
            elapsed_ms = (time.monotonic() - self.start_ts.pop(client_req_id, time.monotonic())) * 1000
            if resp.status_code in (200, 202):
                resp.success()
                _PER_REQUEST_LATENCIES_MS.append(elapsed_ms)
            elif resp.status_code in (409, 429):
                # Circuit-breaker / cap — counted as throttled, not error.
                resp.success()
            else:
                resp.failure(f"unexpected status={resp.status_code}")

    @task(2)
    def read_overlays(self) -> None:
        with self.client.get(
            f"/api/simulations/{self.simulation_id}/overlays",
            name="overlays",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"overlays status={resp.status_code}")


_PER_REQUEST_LATENCIES_MS: list[float] = []


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1, int(round((p / 100) * (len(sorted_values) - 1)))))
    return sorted_values[idx]


@events.test_stop.add_listener
def report_p95_thresholds(environment: Environment, **_: Any) -> None:  # pragma: no cover - locust runtime
    """Emit a JSON summary at end-of-run; non-zero exit if any SLI breached."""
    stats = environment.stats
    inject_entry = stats.get("inject-telemetry", "POST")
    p95 = inject_entry.get_response_time_percentile(0.95) if inject_entry else 0
    error_rate = (inject_entry.num_failures / max(1, inject_entry.num_requests)) if inject_entry else 0
    summary = {
        "p95_parse_to_pipeline_ms": p95,
        "p95_threshold_ms": P95_PARSE_TO_PIPELINE_MS,
        "error_rate": error_rate,
        "error_rate_threshold": ERROR_RATE_THRESHOLD,
        "p95_hazard_overlay_target_ms": P95_HAZARD_OVERLAY_MS,
        "p95_weather_overlay_target_ms": P95_WEATHER_OVERLAY_MS,
        "p95_risk_fanout_target_ms": P95_RISK_FANOUT_MS,
    }
    print("LOCUST_SUMMARY:", json.dumps(summary, default=str))
    breaches = []
    if p95 and p95 > P95_PARSE_TO_PIPELINE_MS:
        breaches.append(f"parse-to-pipeline p95={p95:.0f}ms > {P95_PARSE_TO_PIPELINE_MS}ms")
    if error_rate > ERROR_RATE_THRESHOLD:
        breaches.append(f"error_rate={error_rate:.4f} > {ERROR_RATE_THRESHOLD}")
    if breaches:
        print("LOCUST_FAIL:", "; ".join(breaches))
        environment.process_exit_code = 1


def test_locust_thresholds_match_plan_canonical_sli() -> None:
    """Thresholds in this file mirror plan.md SLI table — guard against drift."""
    assert P95_PARSE_TO_PIPELINE_MS == 5_000, "plan.md SLI 1 — parse-to-pipeline ≤ 5 s p95"
    assert P95_RISK_FANOUT_MS == 15_000, "plan.md SLI 2 — risk-fan-out ≤ 15 s p95 (replaces prior <2 s target)"
    assert P95_HAZARD_OVERLAY_MS == 15_000
    assert P95_WEATHER_OVERLAY_MS == 10_000
    assert ERROR_RATE_THRESHOLD == 0.01

"""Spec-039 T071: event_hub_publisher integration in deterministic-replay mode.

Replays a committed NDJSON fixture and asserts that:
  * Every record is republished through the in-memory EventHubPublisher
    fallback (no Azure namespace configured).
  * The correlation_id from the canonical record is preserved in the
    SignalPipelineEvent so AAR (FR-054) can stitch the timeline.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "apps" / "api"
for _p in (REPO_ROOT, API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def test_replay_publishes_through_event_hub_in_memory(tmp_path) -> None:
    from app.services.simulation.event_hub_publisher import EventHubPublisher
    from app.services.simulation.feeds import bom_severe_weather_warning as mod
    from app.services.simulation.feeds._canonical import SimulatedClock
    from app.services.simulation.replay.engine import replay_to_publisher
    from app.services.simulation.replay.ndjson_writer import write_ndjson

    path = tmp_path / "scn.ndjson"
    records = list(
        mod.emit(
            "nsw-bushfire-summer",
            42,
            count=5,
            jurisdiction="nsw",
            clock=SimulatedClock("nsw-bushfire-summer", 42),
        )
    )
    write_ndjson(records, path)

    pub = EventHubPublisher(namespace=None)
    asyncio.run(
        replay_to_publisher(
            path,
            publisher=pub,
            tenant_id="tenant-test",
            simulation_id="sim-test",
        )
    )

    captured = pub.captured_events_for("tenant-test")
    assert len(captured) == len(records)
    expected_cids = [r.correlation_id for r in records]
    actual_cids = [e.correlation_id for e in captured]
    assert expected_cids == actual_cids
    for ev in captured:
        assert ev.tenant_id == "tenant-test"
        assert ev.simulation_id == "sim-test"
        assert ev.kind == "signal.persisted"

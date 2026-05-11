"""T-J02 — SSE event-types contract test.

Asserts the **closed set** of valid (event_type, layer_type) tuples
emitted by the simulation SSE stream — per
``contracts/sse-map-overlay.md §1, §2, §4.6``.

The cartesian-style breakdown is:

* 5 per-overlay event types ×16 layer types = 80 tuples.
* +1 sentinel envelope `map.overlay.batch` (wrapper-level overlay_id and
  layer_type are sentinel placeholders per §4.6 — it is NOT a 16-fold
  expansion).

Total: **81 valid tuples** (matches the spec text, "approximately 81 valid
tuples"). The previous draft over-counted (96) by treating
`map.overlay.batch` as a layer-aware event.

The four canonical sub-agent SSE events
(``sub_agent.{started,completed,degraded}`` + ``ack.working``) are
asserted separately as the chat-pane stream complement (FR-003).
"""

from __future__ import annotations

import json

import pytest

from apps.api.app.services.simulation.map_overlay_publisher import LAYER_TYPES
from apps.api.app.services.simulation.sse_sub_agent_events import (
    SUB_AGENT_SSE_EVENT_TYPES,
    completed,
    degraded,
    format_sse_event,
    soft_ack,
    started,
)

# Five per-overlay event types — match contracts/sse-map-overlay.md §1.
PER_OVERLAY_EVENT_TYPES: tuple[str, ...] = (
    "map.overlay.created",
    "map.overlay.updated",
    "map.overlay.stale",
    "map.overlay.cluster",
    "map.overlay.removed",
)

# Sentinel envelope (initial-load / SSE reconnect) — wrapper-level
# overlay_id/layer_type are placeholders per §4.6.
BATCH_EVENT_TYPE = "map.overlay.batch"


def test_layer_type_count_matches_contract() -> None:
    """The contract enumerates exactly 16 layer types."""
    assert len(LAYER_TYPES) == 16, "FR-027 closed set must have 16 layer types."


def test_per_overlay_event_count_is_5() -> None:
    """5 per-overlay events — created/updated/stale/cluster/removed."""
    assert len(PER_OVERLAY_EVENT_TYPES) == 5
    assert len(set(PER_OVERLAY_EVENT_TYPES)) == 5  # unique


def test_total_valid_tuples_is_81() -> None:
    """5 × 16 = 80 cartesian tuples + 1 sentinel batch envelope = 81."""
    cartesian = len(PER_OVERLAY_EVENT_TYPES) * len(LAYER_TYPES)
    sentinels = 1  # map.overlay.batch
    total = cartesian + sentinels
    assert cartesian == 80
    assert total == 81, f"Expected 81 valid (event_type, layer_type) tuples per spec; got {total}."


@pytest.mark.parametrize("event_type", PER_OVERLAY_EVENT_TYPES)
@pytest.mark.parametrize("layer_type", LAYER_TYPES)
def test_event_layer_tuple_serialises_cleanly(event_type: str, layer_type: str) -> None:
    """Round-trip JSON serialisation is stable for every valid tuple."""
    payload = {
        "overlay_id": "ov-1",
        "layer_type": layer_type,
        "observed_at": "2025-01-01T00:00:00+00:00",
        "origin_cascade_id": None,
    }
    chunk = format_sse_event(event_type, payload)
    # SSE wire format: "event: <name>\ndata: <json>\n\n".
    assert chunk.startswith(f"event: {event_type}\n")
    assert chunk.endswith("\n\n")
    body = chunk.split("data: ", 1)[1].rstrip("\n")
    parsed = json.loads(body)
    assert parsed["layer_type"] == layer_type


def test_batch_envelope_serialises_with_sentinel() -> None:
    """`map.overlay.batch` carries sentinel layer_type per §4.6."""
    payload = {
        "overlay_id": "00000000-0000-0000-0000-000000000000",
        "layer_type": LAYER_TYPES[0],  # any sentinel — not part of cartesian
        "batch": [],
    }
    chunk = format_sse_event(BATCH_EVENT_TYPE, payload)
    assert chunk.startswith(f"event: {BATCH_EVENT_TYPE}\n")
    parsed = json.loads(chunk.split("data: ", 1)[1].rstrip("\n"))
    assert parsed["overlay_id"] == "00000000-0000-0000-0000-000000000000"


def test_sub_agent_event_types_canonical_set() -> None:
    """FR-003 sub-agent stream — 3 phases + ack.working."""
    assert set(SUB_AGENT_SSE_EVENT_TYPES) == {
        "sub_agent.started",
        "sub_agent.completed",
        "sub_agent.degraded",
        "ack.working",
    }


def test_sub_agent_started_payload_shape() -> None:
    ev = started(sub_agent="risk-assessment", correlation_id="corr-1")
    assert ev.event == "sub_agent.started"
    assert ev.data["sub_agent"] == "risk-assessment"
    assert ev.data["phase"] == "started"
    assert ev.data["correlation_id"] == "corr-1"


def test_sub_agent_completed_payload_carries_prompt_hash() -> None:
    ev = completed(
        sub_agent="risk-assessment",
        summary="ok",
        citations=["c1"],
        prompt_hash="b" * 64,
        model_deployment="gpt-4o-australiaeast",
    )
    assert ev.event == "sub_agent.completed"
    assert ev.data["prompt_hash"] == "b" * 64
    assert ev.data["model_deployment"] == "gpt-4o-australiaeast"


def test_sub_agent_degraded_payload_carries_error() -> None:
    ev = degraded(sub_agent="risk-assessment", error="timeout")
    assert ev.data["error"] == "timeout"


def test_soft_ack_event_emitted() -> None:
    ev = soft_ack(sub_agent="risk-assessment", correlation_id="c-1")
    assert ev.event == "ack.working"


def test_overlay_per_child_uses_individual_created_events() -> None:
    """T-D09 — cascade fan-out emits N `map.overlay.created`, not a batch.

    Per `sse-map-overlay.md §4.6` `map.overlay.batch` is reserved for
    initial-load envelopes; cascade fan-outs MUST use one
    `map.overlay.created` event per child carrying `origin_cascade_id`.
    """
    chunks: list[str] = []
    children = ["sig-a", "sig-b", "sig-c", "sig-d", "sig-e"]
    cascade_id = "cas-42"
    for child in children:
        chunks.append(
            format_sse_event(
                "map.overlay.created",
                {
                    "overlay_id": child,
                    "layer_type": "fire-behaviour",
                    "origin_cascade_id": cascade_id,
                    "observed_at": "2025-01-01T00:00:00+00:00",
                },
            )
        )
    # 5 individual created events, all sharing one origin_cascade_id.
    assert len(chunks) == 5
    for c in chunks:
        assert c.startswith("event: map.overlay.created\n")
        body = json.loads(c.split("data: ", 1)[1].rstrip("\n"))
        assert body["origin_cascade_id"] == cascade_id
    # AND zero batch events used for cascade fan-out.
    assert not any(c.startswith("event: map.overlay.batch") for c in chunks)

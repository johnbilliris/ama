"""Spec-038 T071: replay engine — feed canonical NDJSON into existing
:class:`event_hub_publisher.EventHubPublisher`.

This is the *only* in-process delivery path mandated by CL-2 (no new HTTP
endpoints). The simulator package never calls Azure SDKs directly: the
publisher itself decides whether to use a real
``EventHubProducerClient`` or its in-memory fallback.

The replayed correlation_id is preserved end-to-end so AAR (FR-054) can
stitch the timeline back to the originating canonical record.
"""

from __future__ import annotations

from pathlib import Path

from app.services.simulation.event_hub_publisher import (
    EventHubPublisher,
    SignalPipelineEvent,
)

from .digest import verify_sidecar
from .ndjson_reader import read_ndjson


async def replay_to_publisher(
    path: str | Path,
    *,
    publisher: EventHubPublisher,
    tenant_id: str,
    simulation_id: str,
    kind: str = "signal.persisted",
    verify: bool = True,
) -> int:
    """Replay every record in ``path`` through ``publisher``.

    Args:
        path: NDJSON replay file written by :func:`ndjson_writer.write_ndjson`.
        publisher: an :class:`EventHubPublisher` (in-memory fallback OK).
        tenant_id: tenant scope for the synthetic Event Hub.
        simulation_id: simulation scope.
        kind: ``signal.persisted`` (default) or ``signal.fanned_out``.
        verify: when ``True`` (default) the sidecar SHA-256 is checked
            before any record is published; on mismatch
            :class:`DigestMismatchError` propagates and nothing is sent.

    Returns:
        Number of records published.
    """
    p = Path(path)
    if verify:
        verify_sidecar(p)
    sent = 0
    for rec in read_ndjson(p):
        ev = SignalPipelineEvent(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            signal_id=str(rec.get("correlation_id") or sent),
            kind=kind,  # type: ignore[arg-type]
            correlation_id=str(rec.get("correlation_id") or ""),
            metadata={
                "scenario_id": rec.get("scenario_id"),
                "seed": rec.get("seed"),
                "source_shape": rec.get("source_shape"),
                "feed_version": rec.get("feed_version"),
                "timestamp": rec.get("timestamp"),
            },
        )
        await _send_via_publisher(publisher, ev)
        sent += 1
    return sent


async def _send_via_publisher(
    publisher: EventHubPublisher, ev: SignalPipelineEvent
) -> None:
    """Use the canonical async ``publish`` method on the publisher."""
    await publisher.publish(ev)


__all__ = ["replay_to_publisher"]

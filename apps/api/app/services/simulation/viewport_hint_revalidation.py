"""T-G08 — viewport-hint server revalidation (FR-021).

Encapsulates the **advisory** policy that web clients tag chat turns with
a ``viewport_hint`` (the centroid of their displayed map), and the
server revalidates this hint against the STRtree-backed boundary
service. On mismatch, an ``audit.routing.viewport_hint_mismatch`` entry
is written carrying every field of the contract payload.

Importantly: the hint is treated **only** as advisory. The server's
STRtree result (or a downstream ladder fall-through) is the
authoritative jurisdiction for the chat turn.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.services.simulation.jurisdiction_boundary_service import (
    JurisdictionBoundaryService,
)
from app.services.simulation.routing_audit_writers import (
    write_viewport_hint_mismatch,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ViewportHint:
    chat_turn_id: str
    client_hint: str
    centroid_lat: float
    centroid_lng: float


@dataclass(frozen=True)
class RevalidationResult:
    server_computed: str | None
    mismatch: bool
    audit_emitted: bool


async def revalidate_viewport_hint(
    *,
    hint: ViewportHint,
    boundary_service: JurisdictionBoundaryService,
    audit_writer: Any | None,
    simulation_id: str,
    actor: str = "controller_service",
) -> RevalidationResult:
    """Revalidate *hint* against the STRtree; emit audit on mismatch."""
    server_computed = boundary_service.infer(hint.centroid_lat, hint.centroid_lng)
    mismatch = server_computed is not None and server_computed != hint.client_hint
    audit_emitted = False
    if mismatch and audit_writer is not None:
        await write_viewport_hint_mismatch(
            audit_writer=audit_writer,
            simulation_id=simulation_id,
            actor=actor,
            chat_turn_id=hint.chat_turn_id,
            client_hint=hint.client_hint,
            server_computed=server_computed,
            viewport_centroid_lat=hint.centroid_lat,
            viewport_centroid_lng=hint.centroid_lng,
            jurisdiction_dataset_version=(boundary_service.metrics.dataset_version),
        )
        audit_emitted = True
        logger.info(
            "viewport_hint.mismatch chat_turn=%s client=%s server=%s",
            hint.chat_turn_id,
            hint.client_hint,
            server_computed,
        )
    return RevalidationResult(
        server_computed=server_computed,
        mismatch=mismatch,
        audit_emitted=audit_emitted,
    )


__all__ = [
    "RevalidationResult",
    "ViewportHint",
    "revalidate_viewport_hint",
]

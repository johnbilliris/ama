"""T-G03 — routing audit writers (FR-020, FR-021).

Provides the three FR-020 / FR-021 routing audit writers that emit
typed entries into the audit envelope:

* ``routing.viewport_hint_mismatch`` — operator's viewport hint
  contradicted server-side STRtree resolution.
* ``routing.jurisdiction_ambiguous`` — the 5-step ladder could not
  resolve a unique jurisdiction.
* ``routing.ambiguous`` — multiple candidate agents with similar
  confidence; coordinator clarification required.

Each writer composes the appropriate ``*Details`` payload (already
registered in ``packages/domain/src/domain/models/telemetry_injection_audit_entry.py``)
and writes via the supplied audit writer.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    RoutingAmbiguousDetails,
    RoutingJurisdictionAmbiguousDetails,
    RoutingViewportHintMismatchDetails,
)

logger = logging.getLogger(__name__)


class _AuditWriterProtocol(Protocol):  # pragma: no cover - typing only
    async def write(
        self,
        entry_type: str,
        *,
        simulation_id: str,
        actor: str,
        details: dict[str, Any],
    ) -> None: ...


async def write_viewport_hint_mismatch(
    *,
    audit_writer: _AuditWriterProtocol,
    simulation_id: str,
    actor: str,
    chat_turn_id: str,
    client_hint: str,
    server_computed: str,
    viewport_centroid_lat: float,
    viewport_centroid_lng: float,
    jurisdiction_dataset_version: str | None = None,
) -> RoutingViewportHintMismatchDetails:
    details = RoutingViewportHintMismatchDetails(
        chat_turn_id=chat_turn_id,
        client_hint=client_hint,
        server_computed=server_computed,
        viewport_centroid_lat=viewport_centroid_lat,
        viewport_centroid_lng=viewport_centroid_lng,
        jurisdiction_dataset_version=jurisdiction_dataset_version,
    )
    await audit_writer.write(
        "routing.viewport_hint_mismatch",
        simulation_id=simulation_id,
        actor=actor,
        details=details.model_dump(mode="json"),
    )
    logger.info(
        "audit.routing.viewport_hint_mismatch sim=%s client=%s server=%s",
        simulation_id,
        client_hint,
        server_computed,
    )
    return details


async def write_jurisdiction_ambiguous(
    *,
    audit_writer: _AuditWriterProtocol,
    simulation_id: str,
    actor: str,
    chat_turn_id: str,
    inference_step_attempted: int,
    candidates: list[str],
    clarification_question: str | None = None,
) -> RoutingJurisdictionAmbiguousDetails:
    details = RoutingJurisdictionAmbiguousDetails(
        chat_turn_id=chat_turn_id,
        inference_step_attempted=inference_step_attempted,
        candidates=candidates,
        clarification_question=clarification_question,
    )
    await audit_writer.write(
        "routing.jurisdiction_ambiguous",
        simulation_id=simulation_id,
        actor=actor,
        details=details.model_dump(mode="json"),
    )
    logger.info(
        "audit.routing.jurisdiction_ambiguous sim=%s step=%d candidates=%s",
        simulation_id,
        inference_step_attempted,
        candidates,
    )
    return details


async def write_ambiguous(
    *,
    audit_writer: _AuditWriterProtocol,
    simulation_id: str,
    actor: str,
    chat_turn_id: str,
    candidate_agents: list[str],
    confidences: list[float] | None = None,
    clarification_question: str | None = None,
) -> RoutingAmbiguousDetails:
    details = RoutingAmbiguousDetails(
        chat_turn_id=chat_turn_id,
        candidate_agents=candidate_agents,
        confidences=confidences or [],
        clarification_question=clarification_question,
    )
    await audit_writer.write(
        "routing.ambiguous",
        simulation_id=simulation_id,
        actor=actor,
        details=details.model_dump(mode="json"),
    )
    logger.info(
        "audit.routing.ambiguous sim=%s agents=%s",
        simulation_id,
        candidate_agents,
    )
    return details


__all__ = [
    "write_ambiguous",
    "write_jurisdiction_ambiguous",
    "write_viewport_hint_mismatch",
]

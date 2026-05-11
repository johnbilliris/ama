"""T-G03 — routing audit writers contract test."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from apps.api.app.services.simulation.routing_audit_writers import (
    write_ambiguous,
    write_jurisdiction_ambiguous,
    write_viewport_hint_mismatch,
)
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    RoutingAmbiguousDetails,
    RoutingJurisdictionAmbiguousDetails,
    RoutingViewportHintMismatchDetails,
)


@pytest.fixture
def audit_writer() -> AsyncMock:
    aw = AsyncMock()
    aw.write = AsyncMock()
    return aw


@pytest.mark.asyncio
async def test_routing_viewport_hint_mismatch_emits_full_payload(
    audit_writer: AsyncMock,
) -> None:
    details = await write_viewport_hint_mismatch(
        audit_writer=audit_writer,
        simulation_id="sim-g03",
        actor="controller_service",
        chat_turn_id="turn-1",
        client_hint="VIC",
        server_computed="ACT",
        viewport_centroid_lat=-35.30,
        viewport_centroid_lng=149.13,
        jurisdiction_dataset_version="platform-registry-v3",
    )
    assert isinstance(details, RoutingViewportHintMismatchDetails)
    audit_writer.write.assert_awaited_once()
    args, kwargs = audit_writer.write.call_args
    assert args[0] == "routing.viewport_hint_mismatch"
    assert kwargs["simulation_id"] == "sim-g03"
    payload = kwargs["details"]
    # Every required field present.
    for f in (
        "chat_turn_id",
        "client_hint",
        "server_computed",
        "viewport_centroid_lat",
        "viewport_centroid_lng",
        "jurisdiction_dataset_version",
    ):
        assert f in payload
    assert payload["client_hint"] == "VIC"
    assert payload["server_computed"] == "ACT"
    assert payload["jurisdiction_dataset_version"] == "platform-registry-v3"


@pytest.mark.asyncio
async def test_routing_jurisdiction_ambiguous_validates_inference_step(
    audit_writer: AsyncMock,
) -> None:
    details = await write_jurisdiction_ambiguous(
        audit_writer=audit_writer,
        simulation_id="sim-g03",
        actor="jurisdiction_ladder",
        chat_turn_id="turn-2",
        inference_step_attempted=4,
        candidates=["NSW", "VIC"],
        clarification_question="Which jurisdiction is this incident in?",
    )
    assert isinstance(details, RoutingJurisdictionAmbiguousDetails)
    assert details.inference_step_attempted == 4
    payload = audit_writer.write.call_args.kwargs["details"]
    assert payload["candidates"] == ["NSW", "VIC"]
    # Out-of-range inference step rejected at schema time.
    with pytest.raises(ValidationError):
        RoutingJurisdictionAmbiguousDetails(
            chat_turn_id="turn-z",
            inference_step_attempted=99,
            candidates=["X"],
        )


@pytest.mark.asyncio
async def test_routing_ambiguous_emits_candidate_agents(
    audit_writer: AsyncMock,
) -> None:
    details = await write_ambiguous(
        audit_writer=audit_writer,
        simulation_id="sim-g03",
        actor="agent_router",
        chat_turn_id="turn-3",
        candidate_agents=["risk-assessment", "intelligence"],
        confidences=[0.62, 0.61],
        clarification_question="Risk or intelligence?",
    )
    assert isinstance(details, RoutingAmbiguousDetails)
    assert details.candidate_agents == ["risk-assessment", "intelligence"]
    payload = audit_writer.write.call_args.kwargs["details"]
    assert payload["confidences"] == [0.62, 0.61]

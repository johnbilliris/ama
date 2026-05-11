"""T-G08 — viewport-hint advisory + server revalidation integration test."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from apps.api.app.services.simulation.jurisdiction_boundary_service import (
    JurisdictionBoundaryService,
)
from apps.api.app.services.simulation.viewport_hint_revalidation import (
    ViewportHint,
    revalidate_viewport_hint,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "jurisdiction_boundaries"


def _service() -> JurisdictionBoundaryService:
    svc = JurisdictionBoundaryService()
    svc.load_from_directory(FIXTURE_ROOT, dataset_version="platform-registry-v3")
    return svc


@pytest.mark.asyncio
async def test_falsified_hint_detected_and_audit_emitted_with_full_payload() -> None:
    """Web client claims VIC, server STRtree resolves ACT → MUST audit."""
    audit = AsyncMock()
    audit.write = AsyncMock()

    hint = ViewportHint(
        chat_turn_id="turn-g08-mismatch",
        client_hint="VIC",
        centroid_lat=-35.30,  # Canberra
        centroid_lng=149.13,
    )
    result = await revalidate_viewport_hint(
        hint=hint,
        boundary_service=_service(),
        audit_writer=audit,
        simulation_id="sim-g08",
    )

    assert result.mismatch is True
    assert result.server_computed == "ACT"
    assert result.audit_emitted is True

    # Audit payload MUST carry every required field.
    audit.write.assert_awaited_once()
    args, kwargs = audit.write.call_args
    assert args[0] == "routing.viewport_hint_mismatch"
    payload = kwargs["details"]

    assert payload["chat_turn_id"] == "turn-g08-mismatch"
    assert payload["chat_turn_id"]  # non-empty
    assert payload["client_hint"] == "VIC"
    assert payload["server_computed"] == "ACT"
    assert payload["client_hint"] != payload["server_computed"]
    assert payload["viewport_centroid_lat"] == pytest.approx(-35.30)
    assert payload["viewport_centroid_lng"] == pytest.approx(149.13)
    assert payload["jurisdiction_dataset_version"] == "platform-registry-v3"


@pytest.mark.asyncio
async def test_matching_hint_does_not_emit_audit() -> None:
    audit = AsyncMock()
    audit.write = AsyncMock()

    hint = ViewportHint(
        chat_turn_id="turn-g08-match",
        client_hint="ACT",
        centroid_lat=-35.30,
        centroid_lng=149.13,
    )
    result = await revalidate_viewport_hint(
        hint=hint,
        boundary_service=_service(),
        audit_writer=audit,
        simulation_id="sim-g08",
    )
    assert result.mismatch is False
    assert result.audit_emitted is False
    audit.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_unresolvable_point_returns_none_no_audit() -> None:
    """Offshore point (no polygon) — mismatch is FALSE because there's no
    server computation to disagree with."""
    audit = AsyncMock()
    audit.write = AsyncMock()

    hint = ViewportHint(
        chat_turn_id="turn-g08-offshore",
        client_hint="QLD",
        centroid_lat=-30.0,
        centroid_lng=170.0,
    )
    result = await revalidate_viewport_hint(
        hint=hint,
        boundary_service=_service(),
        audit_writer=audit,
        simulation_id="sim-g08",
    )
    assert result.server_computed is None
    assert result.mismatch is False
    audit.write.assert_not_awaited()

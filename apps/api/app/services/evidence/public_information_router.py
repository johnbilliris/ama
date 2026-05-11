"""Public Information router (T-AMD-14, FR-039)."""
from __future__ import annotations

from fastapi import APIRouter, Path

from .public_information import render_public_information

router = APIRouter(tags=["evidence-public-information"])


@router.get(
    "/public-information/{scenario_id}",
    operation_id="getPublicInformationForScenario",
)
def get_public_information(scenario_id: str = Path(...)) -> dict:
    """Get public information channels for a scenario (T-AMD-14, FR-039)."""
    return render_public_information(scenario_id)

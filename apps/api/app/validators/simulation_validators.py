from app.core.settings import get_settings
from app.repositories.simulation_repository import SimulationRepository
from fastapi import HTTPException


class SimulationValidators:
    def __init__(self, simulation_repository: SimulationRepository):
        self._repo = simulation_repository
        self._settings = get_settings()

    # Concurrency is enforced by SimulationRepository.reserve_capacity, which takes a
    # conditional reservation across replicas. The former count-then-create check was
    # removed because a separate read could not make creation atomic (AUD-024).

    def validate_resource_limits(
        self,
        max_signals: int | None,
        max_recommendations: int | None,
        max_duration_hours: int | None,
    ) -> None:
        if max_signals is not None and max_signals <= 0:
            raise HTTPException(status_code=400, detail="max_signals must be positive")
        if max_recommendations is not None and max_recommendations <= 0:
            raise HTTPException(status_code=400, detail="max_recommendations must be positive")
        if max_duration_hours is not None and max_duration_hours <= 0:
            raise HTTPException(status_code=400, detail="max_duration_hours must be positive")

    def validate_participants(self, participants: list[str], creator_oid: str) -> None:
        if not participants:
            raise HTTPException(status_code=400, detail="participants list must not be empty")
        if creator_oid not in participants:
            raise HTTPException(
                status_code=400,
                detail="Creator must be included in the participants list",
            )

    def validate_scenario_type(self, scenario_type: str) -> None:
        valid = {
            "Bushfire",
            "Flood",
            "Cyclone",
            "Severe Storm",
            "Heatwave",
            "Earthquake",
            "Tsunami",
            "Pandemic",
            "Other",
            "Cross-jurisdiction",
        }
        if scenario_type not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scenario_type '{scenario_type}'. Must be one of: {sorted(valid)}",
            )

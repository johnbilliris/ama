from app.core.settings import get_settings
from app.repositories.simulation_repository import SimulationRepository
from fastapi import HTTPException


class SimulationValidators:
    def __init__(self, simulation_repository: SimulationRepository):
        self._repo = simulation_repository
        self._settings = get_settings()

    async def validate_concurrency_limit(self) -> None:
        active = await self._repo.count_active()
        if active >= self._settings.max_concurrent_simulations:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Maximum concurrent simulations ({self._settings.max_concurrent_simulations}) reached. "
                    "Archive or delete an existing simulation before creating a new one."
                ),
            )

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
            "Bushfire", "Flood", "Cyclone", "Severe Storm", "Heatwave",
            "Earthquake", "Tsunami", "Pandemic", "Other", "Cross-jurisdiction",
        }
        if scenario_type not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scenario_type '{scenario_type}'. Must be one of: {sorted(valid)}",
            )

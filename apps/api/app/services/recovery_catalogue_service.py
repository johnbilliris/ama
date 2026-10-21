"""Platform API recovery catalogue business logic.

Catalogue browsing, domain filtering, outcome detail, activity suggestion.

FRs: FR-015–024
"""

import logging

from app.repositories.recovery_catalogue_repository import RecoveryCatalogueDocument, RecoveryCatalogueRepository

logger = logging.getLogger(__name__)


class RecoveryCatalogueService:
    def __init__(self, repository: RecoveryCatalogueRepository | None = None) -> None:
        self._repo = repository

    async def list_outcomes(
        self, domain: str | None = None, objective_type: str | None = None
    ) -> list[RecoveryCatalogueDocument]:
        if self._repo:
            return await self._repo.list_outcomes(domain=domain, objective_type=objective_type)
        return []

    async def get_outcome(self, outcome_id: str, domain: str) -> RecoveryCatalogueDocument | None:
        if self._repo:
            return await self._repo.get_outcome(outcome_id, domain)
        return None

    async def get_activities_for_outcome(self, outcome_id: str, domain: str) -> list[RecoveryCatalogueDocument]:
        if self._repo:
            return await self._repo.get_activities_for_outcome(outcome_id, domain)
        return []

    async def get_indicators_for_outcome(self, outcome_id: str, domain: str) -> list[RecoveryCatalogueDocument]:
        if self._repo:
            return await self._repo.get_indicators_for_outcome(outcome_id, domain)
        return []

    async def get_domain_summary(self, domain: str) -> dict[str, str | int]:
        if self._repo:
            return await self._repo.get_domain_summary(domain)
        return {"domain": domain, "outcome_count": 0, "activity_count": 0, "indicator_count": 0}

    async def suggest_activities(self, lagging_indicator_ids: list[str]) -> list[RecoveryCatalogueDocument]:
        # This would normally cross-reference with repository data
        return []

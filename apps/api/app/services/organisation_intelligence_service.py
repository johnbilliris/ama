from pathlib import Path

from app.services.seed_service import SeedService

from packages.domain.src.domain.models.organisation import Organisation


class OrganisationIntelligenceService:
    def __init__(self, seed_root: Path | None = None) -> None:
        if seed_root is None:
            from packages.domain.src.domain.seed import bootstrap as _seed_mod

            seed_root = Path(_seed_mod.__file__).resolve().parent
        self.seed_root = seed_root

    def list_organisations(self, jurisdiction_ids: list[str] | None = None) -> list[Organisation]:
        seeds = SeedService().load(self.seed_root)
        organisations = [Organisation(**item) for item in seeds["organisations"]]
        if not jurisdiction_ids:
            return []
        seen_ids: set[str] = set()
        result: list[Organisation] = []
        for organisation in organisations:
            if organisation.organisation_id in seen_ids:
                continue
            if any(jid in organisation.jurisdiction_ids for jid in jurisdiction_ids):
                seen_ids.add(organisation.organisation_id)
                result.append(organisation)
        return result

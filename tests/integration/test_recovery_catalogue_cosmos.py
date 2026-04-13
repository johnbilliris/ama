"""Integration tests for catalogue seeding verification and queries using in-memory repository.

Validates that the seed data can be loaded into the RecoveryCatalogueRepository
(in-memory mode) and queried correctly, simulating Cosmos DB interactions.
"""
import json
import pytest
import pytest_asyncio
from pathlib import Path

from app.repositories.recovery_catalogue_repository import RecoveryCatalogueRepository

SEED_ROOT = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "domain"
    / "src"
    / "domain"
    / "seed"
    / "recovery-catalogue"
)

DOMAIN_FILES = ["overarching", "social", "economic", "built", "natural"]


@pytest_asyncio.fixture
async def seeded_repository():
    """Create an in-memory repository and seed it with catalogue data."""
    repo = RecoveryCatalogueRepository()

    for domain_name in DOMAIN_FILES:
        path = SEED_ROOT / f"{domain_name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        domain = data["domain"]

        for outcome in data.get("outcomes", []):
            outcome_doc = {
                "id": outcome["outcome_id"],
                "outcome_id": outcome["outcome_id"],
                "kind": "outcome",
                "domain": domain,
                "objective_type": outcome["objective_type"],
                "title": outcome["title"],
                "description": outcome.get("description", ""),
                "has_developed_activities": outcome.get("has_developed_activities", True),
            }
            await repo.upsert_catalogue_item(outcome_doc)

            for act in outcome.get("activities", []):
                act_doc = {
                    "id": act["activity_id"],
                    "activity_id": act["activity_id"],
                    "kind": "activity",
                    "domain": domain,
                    "outcome_id": outcome["outcome_id"],
                    "title": act["title"],
                    "description": act.get("description", ""),
                }
                await repo.upsert_catalogue_item(act_doc)

            for ind in outcome.get("indicators", []):
                ind_doc = {
                    "id": ind["indicator_id"],
                    "indicator_id": ind["indicator_id"],
                    "kind": "indicator",
                    "domain": domain,
                    "outcome_id": outcome["outcome_id"],
                    "title": ind["title"],
                    "description": ind.get("description", ""),
                    "indicator_type": ind.get("indicator_type", "quantitative"),
                }
                await repo.upsert_catalogue_item(ind_doc)

    return repo


class TestCatalogueSeeding:
    """Verify seed data is correctly ingested into the repository."""

    @pytest.mark.asyncio
    async def test_outcomes_seeded(self, seeded_repository):
        outcomes = await seeded_repository.list_outcomes()
        assert len(outcomes) > 0, "No outcomes were seeded"

    @pytest.mark.asyncio
    async def test_social_outcomes_present(self, seeded_repository):
        outcomes = await seeded_repository.list_outcomes(domain="social")
        assert len(outcomes) > 0
        assert all(o["domain"] == "social" for o in outcomes)

    @pytest.mark.asyncio
    async def test_economic_outcomes_present(self, seeded_repository):
        outcomes = await seeded_repository.list_outcomes(domain="economic")
        assert len(outcomes) > 0

    @pytest.mark.asyncio
    async def test_built_outcomes_present(self, seeded_repository):
        outcomes = await seeded_repository.list_outcomes(domain="built")
        assert len(outcomes) > 0

    @pytest.mark.asyncio
    async def test_natural_outcomes_present(self, seeded_repository):
        outcomes = await seeded_repository.list_outcomes(domain="natural")
        assert len(outcomes) > 0


class TestCatalogueQueries:
    """Test query operations against the seeded in-memory repository."""

    @pytest.mark.asyncio
    async def test_get_single_outcome(self, seeded_repository):
        outcome = await seeded_repository.get_outcome("aidr:social:community-health-levels", "social")
        assert outcome is not None
        assert outcome["outcome_id"] == "aidr:social:community-health-levels"
        assert outcome["domain"] == "social"

    @pytest.mark.asyncio
    async def test_get_nonexistent_outcome(self, seeded_repository):
        outcome = await seeded_repository.get_outcome("nonexistent", "social")
        assert outcome is None

    @pytest.mark.asyncio
    async def test_list_outcomes_with_objective_type_filter(self, seeded_repository):
        outcomes = await seeded_repository.list_outcomes(objective_type="sustainability")
        assert len(outcomes) > 0
        assert all(o["objective_type"] == "sustainability" for o in outcomes)

    @pytest.mark.asyncio
    async def test_get_activities_for_outcome(self, seeded_repository):
        activities = await seeded_repository.get_activities_for_outcome("aidr:social:community-health-levels", "social")
        assert isinstance(activities, list)
        assert len(activities) > 0
        for act in activities:
            assert act["kind"] == "activity"
            assert act["outcome_id"] == "aidr:social:community-health-levels"

    @pytest.mark.asyncio
    async def test_get_indicators_for_outcome(self, seeded_repository):
        indicators = await seeded_repository.get_indicators_for_outcome("aidr:social:community-health-levels", "social")
        assert isinstance(indicators, list)
        assert len(indicators) > 0
        for ind in indicators:
            assert ind["kind"] == "indicator"
            assert ind["outcome_id"] == "aidr:social:community-health-levels"


class TestDomainSummary:
    """Test domain summary aggregation from seeded data."""

    @pytest.mark.asyncio
    async def test_social_domain_summary(self, seeded_repository):
        summary = await seeded_repository.get_domain_summary("social")
        assert summary["domain"] == "social"
        assert summary["outcomes"] > 0
        assert summary["activities"] > 0
        assert summary["indicators"] > 0

    @pytest.mark.asyncio
    async def test_nonexistent_domain_summary(self, seeded_repository):
        summary = await seeded_repository.get_domain_summary("nonexistent")
        assert summary["domain"] == "nonexistent"
        assert summary["outcomes"] == 0
        assert summary["activities"] == 0
        assert summary["indicators"] == 0


class TestUpsertIdempotency:
    """Verify that upsert operations are idempotent."""

    @pytest.mark.asyncio
    async def test_upsert_same_item_twice(self, seeded_repository):
        item = {
            "id": "test-idempotency",
            "kind": "outcome",
            "domain": "social",
            "outcome_id": "test-idempotency",
            "title": "Test Outcome",
            "objective_type": "sustainability",
        }
        await seeded_repository.upsert_catalogue_item(item)
        await seeded_repository.upsert_catalogue_item(item)

        # Should still have the same item, not duplicated
        outcomes = await seeded_repository.list_outcomes(domain="social")
        matching = [o for o in outcomes if o["id"] == "test-idempotency"]
        assert len(matching) == 1

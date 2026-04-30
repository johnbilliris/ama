"""Integration tests for emergency plans Cosmos DB operations.

Uses in-memory repository — does not require actual Cosmos DB connection.
"""

import pytest
from app.repositories.emergency_plan_repository import EmergencyPlanRepository
from app.services.emergency_plan_service import EmergencyPlanService

# ---------------------------------------------------------------------------
# Mock Cosmos container
# ---------------------------------------------------------------------------


class MockCosmosContainer:
    """In-memory mock of Azure Cosmos DB container."""

    def __init__(self):
        self._store: dict[str, dict] = {}

    def create_item(self, body):
        doc_id = body.get("id", body.get("plan_id", "unknown"))
        self._store[doc_id] = dict(body)
        return body

    def upsert_item(self, body):
        doc_id = body.get("id", body.get("plan_id", "unknown"))
        self._store[doc_id] = dict(body)
        return body

    def read_item(self, item, partition_key):
        if item in self._store:
            return dict(self._store[item])
        raise Exception("404 NotFound")

    def query_items(self, query, parameters=None, partition_key=None, enable_cross_partition_query=False):
        return list(self._store.values())


# ---------------------------------------------------------------------------
# Repository-level tests
# ---------------------------------------------------------------------------


class TestEmergencyPlanRepository:
    @pytest.fixture
    def repo(self):
        return EmergencyPlanRepository()  # In-memory mode (no cosmos client)

    @pytest.mark.asyncio
    async def test_create_and_read_plan(self, repo):
        plan_doc = {
            "plan_id": "ep-001",
            "title": "Flood Plan",
            "region_id": "r-nsw",
            "lifecycle_state": "draft",
            "hierarchy_level": "local",
            "version": 1,
            "hazard_types": ["flood"],
            "created_at": "2024-01-01T00:00:00Z",
        }
        result = await repo.create_plan(plan_doc)
        assert result["plan_id"] == "ep-001"

        retrieved = await repo.get_plan("ep-001", "r-nsw")
        assert retrieved is not None
        assert retrieved["title"] == "Flood Plan"

    @pytest.mark.asyncio
    async def test_list_plans_empty(self, repo):
        plans = await repo.list_plans()
        assert plans == []

    @pytest.mark.asyncio
    async def test_list_plans_with_filter(self, repo):
        for i in range(3):
            await repo.create_plan(
                {
                    "plan_id": f"ep-{i}",
                    "region_id": "r-nsw" if i < 2 else "r-vic",
                    "lifecycle_state": "draft",
                }
            )
        nsw_plans = await repo.list_plans(region_id="r-nsw")
        assert len(nsw_plans) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan_returns_none(self, repo):
        result = await repo.get_plan("nonexistent", "r-any")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_plan(self, repo):
        await repo.create_plan({"plan_id": "ep-upd", "region_id": "r-1", "lifecycle_state": "draft"})
        plan = await repo.get_plan("ep-upd", "r-1")
        plan["lifecycle_state"] = "in_consultation"
        await repo.update_plan(plan)
        updated = await repo.get_plan("ep-upd", "r-1")
        assert updated["lifecycle_state"] == "in_consultation"

    @pytest.mark.asyncio
    async def test_get_hierarchy(self, repo):
        await repo.create_plan({"plan_id": "ep-h1", "region_id": "r-1", "hierarchy_level": "state"})
        await repo.create_plan({"plan_id": "ep-h2", "region_id": "r-1", "hierarchy_level": "local"})
        await repo.create_plan({"plan_id": "ep-h3", "region_id": "r-2", "hierarchy_level": "local"})
        hierarchy = await repo.get_hierarchy("r-1")
        assert len(hierarchy) == 2

    @pytest.mark.asyncio
    async def test_get_by_lifecycle_state(self, repo):
        await repo.create_plan({"plan_id": "ep-s1", "region_id": "r-1", "lifecycle_state": "draft"})
        await repo.create_plan({"plan_id": "ep-s2", "region_id": "r-2", "lifecycle_state": "endorsed"})
        drafts = await repo.get_by_lifecycle_state("draft")
        assert len(drafts) == 1
        assert drafts[0]["plan_id"] == "ep-s1"


# ---------------------------------------------------------------------------
# Service-level tests (in-memory)
# ---------------------------------------------------------------------------


class TestEmergencyPlanService:
    @pytest.fixture
    def svc(self):
        repo = EmergencyPlanRepository()
        return EmergencyPlanService(repository=repo)

    @pytest.mark.asyncio
    async def test_create_plan(self, svc):
        plan = await svc.create_plan(
            title="Flood Plan",
            region_id="r-nsw",
            hazard_types=["flood"],
        )
        assert plan["plan_id"]
        assert plan["lifecycle_state"] == "draft"
        assert "plan_sections" in plan

    @pytest.mark.asyncio
    async def test_create_and_list(self, svc):
        await svc.create_plan(title="P1", region_id="r-1", hazard_types=["flood"])
        await svc.create_plan(title="P2", region_id="r-1", hazard_types=["bushfire"])
        plans = await svc.list_plans()
        assert len(plans) == 2

    @pytest.mark.asyncio
    async def test_get_completeness(self, svc):
        plan = await svc.create_plan(title="Test", region_id="r-1", hazard_types=["flood"])
        result = await svc.get_completeness(plan["plan_id"], "r-1")
        assert result["plan_id"] == plan["plan_id"]
        assert result["section_completeness"] == 0.0
        assert result["completed_sections"] == 0
        assert len(result["missing_sections"]) == result["total_sections"]

    @pytest.mark.asyncio
    async def test_update_section(self, svc):
        plan = await svc.create_plan(title="Test", region_id="r-1", hazard_types=["flood"])
        updated = await svc.update_section(
            plan["plan_id"],
            "r-1",
            "authority",
            title="Authority",
            content="Issued by NSW SES",
        )
        section = updated["plan_sections"]["authority"]
        assert section["content"] == "Issued by NSW SES"
        assert section["is_complete"] is True

    @pytest.mark.asyncio
    async def test_transition_plan(self, svc):
        plan = await svc.create_plan(title="Test", region_id="r-1", hazard_types=["flood"])
        result = await svc.transition_plan(
            plan["plan_id"],
            "r-1",
            target_state="in_consultation",
            user_role="planning_officer",
        )
        assert result["previous_state"] == "draft"
        assert result["new_state"] == "in_consultation"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self, svc):
        plan = await svc.create_plan(title="Test", region_id="r-1", hazard_types=["flood"])
        with pytest.raises(ValueError, match="Invalid plan transition"):
            await svc.transition_plan(
                plan["plan_id"],
                "r-1",
                target_state="endorsed",
                user_role="planning_officer",
            )

    @pytest.mark.asyncio
    async def test_get_hierarchy(self, svc):
        await svc.create_plan(title="State", region_id="r-1", hazard_types=["flood"], hierarchy_level="state")
        await svc.create_plan(title="Local", region_id="r-1", hazard_types=["flood"], hierarchy_level="local")
        hierarchy = await svc.get_hierarchy("r-1")
        assert len(hierarchy) == 2

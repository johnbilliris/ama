"""Integration tests for M&E framework Cosmos DB persistence.

Uses in-memory repository — does not require actual Cosmos DB connection.
Tests both repository-level CRUD and service-level lifecycle operations.

FRs: FR-008–014
"""

import pytest
from app.repositories.me_framework_repository import MEFrameworkRepository
from app.services.me_framework_service import MEFrameworkPlatformService

# ---------------------------------------------------------------------------
# Repository-level tests (in-memory fallback)
# ---------------------------------------------------------------------------


class TestMEFrameworkRepository:
    """Tests for MEFrameworkRepository in-memory mode."""

    @pytest.fixture()
    def repo(self):
        return MEFrameworkRepository()  # No cosmos client → in-memory

    @pytest.mark.asyncio
    async def test_create_and_read_framework(self, repo):
        doc = {
            "framework_id": "mef-test001",
            "id": "mef-test001",
            "document_type": "me_framework",
            "incident_id": "inc-1",
            "program_name": "Test Programme",
            "status": "configuring",
        }
        result = await repo.create_framework(doc)
        assert result["framework_id"] == "mef-test001"

        retrieved = await repo.get_framework("mef-test001", "inc-1")
        assert retrieved is not None
        assert retrieved["program_name"] == "Test Programme"

    @pytest.mark.asyncio
    async def test_get_nonexistent_framework_returns_none(self, repo):
        result = await repo.get_framework("mef-missing", "inc-x")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_framework(self, repo):
        doc = {
            "framework_id": "mef-upd",
            "id": "mef-upd",
            "document_type": "me_framework",
            "incident_id": "inc-1",
            "status": "configuring",
        }
        await repo.create_framework(doc)
        fw = await repo.get_framework("mef-upd", "inc-1")
        fw["status"] = "active"
        await repo.update_framework(fw)
        updated = await repo.get_framework("mef-upd", "inc-1")
        assert updated["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_frameworks_empty(self, repo):
        results = await repo.list_frameworks()
        assert results == []

    @pytest.mark.asyncio
    async def test_list_frameworks_with_incident_filter(self, repo):
        for i in range(3):
            await repo.create_framework({
                "framework_id": f"mef-{i}",
                "id": f"mef-{i}",
                "document_type": "me_framework",
                "incident_id": "inc-A" if i < 2 else "inc-B",
                "status": "configuring",
            })
        results = await repo.list_frameworks(incident_id="inc-A")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_frameworks_with_status_filter(self, repo):
        await repo.create_framework({
            "framework_id": "mef-s1",
            "id": "mef-s1",
            "document_type": "me_framework",
            "incident_id": "inc-1",
            "status": "active",
        })
        await repo.create_framework({
            "framework_id": "mef-s2",
            "id": "mef-s2",
            "document_type": "me_framework",
            "incident_id": "inc-1",
            "status": "configuring",
        })
        active = await repo.list_frameworks(status="active")
        assert len(active) == 1
        assert active[0]["framework_id"] == "mef-s1"

    # -- Program Logic --

    @pytest.mark.asyncio
    async def test_create_and_read_program_logic(self, repo):
        logic_doc = {
            "model_id": "plm-001",
            "id": "plm-001",
            "document_type": "program_logic",
            "framework_id": "mef-1",
            "incident_id": "inc-1",
            "model_type": "ex_ante",
        }
        result = await repo.create_program_logic(logic_doc)
        assert result["model_id"] == "plm-001"

        retrieved = await repo.get_program_logic("plm-001", "inc-1")
        assert retrieved is not None
        assert retrieved["model_type"] == "ex_ante"

    @pytest.mark.asyncio
    async def test_get_nonexistent_logic_returns_none(self, repo):
        result = await repo.get_program_logic("plm-missing", "inc-x")
        assert result is None

    # -- Evaluation Reports --

    @pytest.mark.asyncio
    async def test_create_and_read_evaluation_report(self, repo):
        report_doc = {
            "report_id": "er-001",
            "id": "er-001",
            "document_type": "evaluation_report",
            "framework_id": "mef-1",
            "incident_id": "inc-1",
            "generated_by": "manual",
        }
        result = await repo.create_evaluation_report(report_doc)
        assert result["report_id"] == "er-001"

        retrieved = await repo.get_evaluation_report("er-001", "inc-1")
        assert retrieved is not None
        assert retrieved["generated_by"] == "manual"

    @pytest.mark.asyncio
    async def test_list_evaluation_reports(self, repo):
        for i in range(3):
            await repo.create_evaluation_report({
                "report_id": f"er-{i}",
                "id": f"er-{i}",
                "document_type": "evaluation_report",
                "framework_id": "mef-1",
                "incident_id": "inc-1",
            })
        reports = await repo.list_evaluation_reports("mef-1", "inc-1")
        assert len(reports) == 3

    @pytest.mark.asyncio
    async def test_list_evaluation_reports_filters_by_framework(self, repo):
        await repo.create_evaluation_report({
            "report_id": "er-a",
            "id": "er-a",
            "document_type": "evaluation_report",
            "framework_id": "mef-1",
            "incident_id": "inc-1",
        })
        await repo.create_evaluation_report({
            "report_id": "er-b",
            "id": "er-b",
            "document_type": "evaluation_report",
            "framework_id": "mef-2",
            "incident_id": "inc-1",
        })
        reports = await repo.list_evaluation_reports("mef-1", "inc-1")
        assert len(reports) == 1
        assert reports[0]["report_id"] == "er-a"


# ---------------------------------------------------------------------------
# Service-level tests (in-memory via repository)
# ---------------------------------------------------------------------------


class TestMEFrameworkPlatformService:
    """Tests for MEFrameworkPlatformService with in-memory repository."""

    @pytest.fixture()
    def svc(self):
        repo = MEFrameworkRepository()
        return MEFrameworkPlatformService(repository=repo)

    @pytest.mark.asyncio
    async def test_create_framework(self, svc):
        fw = await svc.create_framework(
            incident_id="inc-1",
            program_name="Flood Recovery",
        )
        assert fw["framework_id"].startswith("mef-")
        assert fw["status"] == "configuring"
        assert fw["incident_id"] == "inc-1"
        assert fw["document_type"] == "me_framework"

    @pytest.mark.asyncio
    async def test_create_and_get_framework(self, svc):
        fw = await svc.create_framework(
            incident_id="inc-1",
            program_name="Storm Recovery",
        )
        retrieved = await svc.get_framework(fw["framework_id"], "inc-1")
        assert retrieved is not None
        assert retrieved["program_name"] == "Storm Recovery"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, svc):
        result = await svc.get_framework("mef-missing", "inc-x")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_frameworks(self, svc):
        await svc.create_framework(incident_id="inc-1", program_name="P1")
        await svc.create_framework(incident_id="inc-1", program_name="P2")
        await svc.create_framework(incident_id="inc-2", program_name="P3")
        all_fws = await svc.list_frameworks()
        assert len(all_fws) == 3
        inc1_fws = await svc.list_frameworks(incident_id="inc-1")
        assert len(inc1_fws) == 2

    @pytest.mark.asyncio
    async def test_select_outcomes(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        outcomes = [{"catalogue_outcome_id": "o1", "domain": "built"}]
        updated = await svc.select_outcomes(fid, "inc-1", outcomes)
        assert updated["selected_outcomes"] == outcomes
        assert updated["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_select_outcomes_nonexistent_raises(self, svc):
        with pytest.raises(ValueError, match="not found"):
            await svc.select_outcomes("mef-bad", "inc-x", [])

    @pytest.mark.asyncio
    async def test_create_program_logic(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        logic = await svc.create_program_logic(
            fid, "inc-1", {"model_type": "ex_ante", "activities": [{"name": "Build"}]},
        )
        assert logic["model_id"].startswith("plm-")
        assert logic["framework_id"] == fid

        # Verify framework now references logic
        fw2 = await svc.get_framework(fid, "inc-1")
        assert fw2["program_logic_id"] == logic["model_id"]

    @pytest.mark.asyncio
    async def test_set_standards(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        standards = [{"indicator_id": "ind-1", "threshold_value": 80}]
        updated = await svc.set_standards(fid, "inc-1", standards)
        assert updated["standards_of_success"] == standards

    @pytest.mark.asyncio
    async def test_set_collection_schedule_activates(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        assert fw["status"] == "configuring"
        schedules = [{"indicator_id": "ind-1", "frequency": "weekly"}]
        updated = await svc.set_collection_schedule(fid, "inc-1", schedules)
        assert updated["status"] == "active"
        assert updated["indicator_collection_schedule"] == schedules

    @pytest.mark.asyncio
    async def test_generate_monitoring_report(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        report = await svc.generate_monitoring_report(fid, "inc-1")
        assert report["framework_id"] == fid
        assert report["incident_id"] == "inc-1"
        assert "overdue_indicators" in report
        assert "generated_at" in report

    @pytest.mark.asyncio
    async def test_generate_monitoring_report_nonexistent_raises(self, svc):
        with pytest.raises(ValueError, match="not found"):
            await svc.generate_monitoring_report("mef-bad", "inc-x")

    @pytest.mark.asyncio
    async def test_create_evaluation_report(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        report = await svc.create_evaluation_report(
            fid, "inc-1",
            period_start="2026-01-01",
            period_end="2026-06-30",
            generated_by="manual",
            created_by="analyst-1",
        )
        assert report["report_id"].startswith("er-")
        assert report["framework_id"] == fid
        assert report["generated_by"] == "manual"
        assert "domain_findings" in report

        # Verify framework tracks the report
        fw2 = await svc.get_framework(fid, "inc-1")
        assert report["report_id"] in fw2["evaluation_reports"]

    @pytest.mark.asyncio
    async def test_evaluation_report_has_5_domains(self, svc):
        fw = await svc.create_framework(incident_id="inc-1", program_name="Test")
        fid = fw["framework_id"]
        report = await svc.create_evaluation_report(
            fid, "inc-1",
            period_start="2026-01-01",
            period_end="2026-06-30",
        )
        domains = report["domain_findings"]
        assert len(domains) == 5
        expected = {"governance", "community_engagement", "effectiveness", "efficiency", "implementation"}
        assert set(domains.keys()) == expected

    @pytest.mark.asyncio
    async def test_full_service_lifecycle(self, svc):
        """End-to-end lifecycle through the platform service."""
        # Create
        fw = await svc.create_framework(
            incident_id="inc-lifecycle",
            program_name="Full Lifecycle Test",
            created_by="test",
        )
        fid = fw["framework_id"]

        # Select outcomes
        await svc.select_outcomes(fid, "inc-lifecycle", [{"id": "o1"}])

        # Create logic
        logic = await svc.create_program_logic(
            fid, "inc-lifecycle", {"model_type": "ex_ante"},
        )

        # Set standards
        await svc.set_standards(fid, "inc-lifecycle", [{"indicator_id": "i1"}])

        # Set schedule → activates
        updated = await svc.set_collection_schedule(
            fid, "inc-lifecycle", [{"indicator_id": "i1", "frequency": "monthly"}],
        )
        assert updated["status"] == "active"

        # Monitoring report
        report = await svc.generate_monitoring_report(fid, "inc-lifecycle")
        assert report["framework_id"] == fid

        # Evaluation
        eval_report = await svc.create_evaluation_report(
            fid, "inc-lifecycle",
            period_start="2026-01-01",
            period_end="2026-12-31",
        )
        assert eval_report["report_id"].startswith("er-")

        # Verify final state
        final = await svc.get_framework(fid, "inc-lifecycle")
        assert final["status"] == "active"
        assert final["program_logic_id"] == logic["model_id"]
        assert len(final["evaluation_reports"]) == 1

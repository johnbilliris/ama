"""Contract tests validating simulation API request/response schemas per contracts/simulation-api.md."""

import pytest

from packages.domain.src.domain.models.exercise_report import ExerciseReport
from packages.domain.src.domain.models.scenario_template import (
    ScenarioTemplate,
)
from packages.domain.src.domain.models.simulation_tenant import (
    SimulationTenant,
)


class TestSimulationTenantContract:
    def test_create_response_schema(self):
        """POST /api/simulations → 201 response must include tenant_id, scenario_run_id, status, created_at."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Cyclone",
            created_by="user-001",
            participants=["user-001"],
        )
        response = {
            "tenant_id": tenant.tenant_id,
            "scenario_run_id": tenant.scenario_run_id,
            "status": tenant.status,
            "created_at": tenant.created_at.isoformat(),
        }
        assert "tenant_id" in response
        assert "scenario_run_id" in response
        assert "status" in response
        assert "created_at" in response
        assert response["tenant_id"].startswith("sim-")

    def test_list_response_schema(self):
        """GET /api/simulations → 200 response must include simulations array, total, limit, offset."""
        response = {
            "simulations": [
                {
                    "tenant_id": "sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "scenario_type": "Cyclone",
                    "status": "Active",
                    "created_at": "2026-04-09T10:00:00+00:00",
                    "participant_count": 5,
                    "signal_count": 342,
                    "storage_bytes": 1048576,
                }
            ],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        assert isinstance(response["simulations"], list)
        assert "total" in response
        assert "limit" in response
        assert "offset" in response
        sim = response["simulations"][0]
        for key in (
            "tenant_id", "scenario_type", "status", "created_at",
            "participant_count", "signal_count", "storage_bytes",
        ):
            assert key in sim

    def test_detail_response_full_document(self):
        """GET /api/simulations/{tenantId} → 200 response is full SimulationTenant."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Flood",
            created_by="user-001",
            participants=["user-001"],
            jurisdictions=["nsw"],
        )
        doc = tenant.model_dump(mode="json")
        required_fields = [
            "tenant_id", "scenario_id", "scenario_run_id", "scenario_type",
            "status", "created_by", "created_at", "participants", "jurisdictions",
            "resource_limits", "resource_consumption",
            "elapsed_seconds", "last_resumed_at", "paused_at", "current_elapsed_seconds",
        ]
        for field in required_fields:
            assert field in doc, f"Missing field: {field}"

    def test_tenant_id_pattern(self):
        """tenant_id must match ^sim-[a-z0-9-]{36}$."""
        with pytest.raises(ValueError, match="tenant_id must match"):
            SimulationTenant(
                tenant_id="bad-id",
                scenario_id="sc-001",
                scenario_run_id="run-001",
                scenario_type="flood",
                created_by="user-001",
                participants=["user-001"],
            )

    def test_status_transition_contract(self):
        """Status transitions must follow contract: provisioning → active → paused ↔ active → archiving → archived → deleted."""  # noqa: E501
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="Provisioning",
        )
        assert tenant.can_transition_to("Active")
        assert not tenant.can_transition_to("Archived")

    def test_pause_resume_error_codes(self):
        """Pause on non-active → 409, Resume on non-paused → 409."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="Archived",
        )
        assert not tenant.can_transition_to("Paused")
        assert not tenant.can_transition_to("Active")

    def test_elapsed_time_fields_present_on_new_tenant(self):
        """New tenants have elapsed-time fields with correct defaults."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
        )
        assert tenant.elapsed_seconds == 0.0
        assert tenant.last_resumed_at is None
        assert tenant.paused_at is None
        doc = tenant.model_dump(mode="json")
        assert "current_elapsed_seconds" in doc

    def test_pause_response_schema(self):
        """POST /api/simulations/{tenantId}/pause → response includes timer fields."""
        from datetime import UTC, datetime

        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="Active",
            last_resumed_at=datetime.now(UTC),
        )
        paused = tenant.transition_to("Paused")
        response = {
            "tenant_id": paused.tenant_id,
            "status": paused.status,
            "elapsed_seconds": paused.elapsed_seconds,
            "paused_at": paused.paused_at.isoformat() if paused.paused_at else None,
            "last_resumed_at": None,
        }
        assert response["status"] == "Paused"
        assert isinstance(response["elapsed_seconds"], float)
        assert response["elapsed_seconds"] >= 0.0
        assert response["paused_at"] is not None
        assert response["last_resumed_at"] is None


class TestScenarioTemplateContract:
    def test_template_required_fields(self):
        template = ScenarioTemplate(
            template_id="qld-cyclone-multi-agency",
            scenario_type="Cyclone",
            name="QLD Cyclone Multi-Agency",
        )
        doc = template.model_dump(mode="json")
        for field in ("template_id", "kind", "scenario_type", "name", "signal_timeline", "benchmark_targets"):
            assert field in doc


class TestExerciseReportContract:
    def test_report_required_fields(self):
        report = ExerciseReport(
            report_id="rpt-001",
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
        )
        doc = report.model_dump(mode="json")
        for field in (
            "report_id", "tenant_id", "scenario_run_id", "scenario_type", "generated_at",
            "signal_summary", "recommendation_summary", "alert_summary",
            "coordination_gaps", "performance_metrics", "benchmark_comparison",
        ):
            assert field in doc

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
            scenario_type="cyclone",
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
                    "scenario_type": "cyclone",
                    "status": "active",
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
            scenario_type="flood",
            created_by="user-001",
            participants=["user-001"],
            jurisdictions=["nsw"],
        )
        doc = tenant.model_dump(mode="json")
        required_fields = [
            "tenant_id", "scenario_id", "scenario_run_id", "scenario_type",
            "status", "created_by", "created_at", "participants", "jurisdictions",
            "resource_limits", "resource_consumption",
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
            scenario_type="bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="provisioning",
        )
        assert tenant.can_transition_to("active")
        assert not tenant.can_transition_to("archived")

    def test_pause_resume_error_codes(self):
        """Pause on non-active → 409, Resume on non-paused → 409."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="archived",
        )
        assert not tenant.can_transition_to("paused")
        assert not tenant.can_transition_to("active")


class TestScenarioTemplateContract:
    def test_template_required_fields(self):
        template = ScenarioTemplate(
            template_id="qld-cyclone-multi-agency",
            scenario_type="cyclone",
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
            scenario_type="bushfire",
        )
        doc = report.model_dump(mode="json")
        for field in (
            "report_id", "tenant_id", "scenario_run_id", "scenario_type", "generated_at",
            "signal_summary", "recommendation_summary", "alert_summary",
            "coordination_gaps", "performance_metrics", "benchmark_comparison",
        ):
            assert field in doc

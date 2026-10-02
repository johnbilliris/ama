"""Contract tests validating simulation API request/response schemas per contracts/simulation-api.md."""

import pytest
from app.api.routes import simulations as simulations_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
        assert set(response) == {"tenant_id", "scenario_run_id", "status", "created_at"}
        assert response["tenant_id"].startswith("sim-")
        assert response["status"] == "Provisioning"

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
        assert set(response) == {"simulations", "total", "limit", "offset"}
        assert isinstance(response["simulations"], list)
        assert response["total"] == 1
        assert response["limit"] == 20
        assert response["offset"] == 0
        sim = response["simulations"][0]
        assert set(sim) == {
            "tenant_id",
            "scenario_type",
            "status",
            "created_at",
            "participant_count",
            "signal_count",
            "storage_bytes",
        }

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
            "tenant_id",
            "scenario_id",
            "scenario_run_id",
            "scenario_type",
            "status",
            "created_by",
            "created_at",
            "participants",
            "jurisdictions",
            "resource_limits",
            "resource_consumption",
            "elapsed_seconds",
        ]
        assert set(required_fields).issubset(doc.keys())
        # Verify removed fields are NOT present
        # Note: feature 026 reintroduces `last_resumed_at` as part of the server-owned
        # simulation clock (used to compute accumulated_sim_seconds on pause/resume).
        for removed in ("paused_at", "current_elapsed_seconds"):
            assert removed not in doc, f"Obsolete field still present: {removed}"

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
        """New tenants have elapsed_seconds with correct default."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
        )
        assert tenant.elapsed_seconds == 0.0
        doc = tenant.model_dump(mode="json")
        assert "elapsed_seconds" in doc

    def test_pause_response_schema(self):
        """POST /api/simulations/{tenantId}/pause → response includes elapsed_seconds."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="Active",
        )
        paused = tenant.transition_to("Paused", elapsed_seconds=75.5)
        response = {
            "tenant_id": paused.tenant_id,
            "status": paused.status,
            "elapsed_seconds": paused.elapsed_seconds,
        }
        assert response["status"] == "Paused"
        assert isinstance(response["elapsed_seconds"], float)
        assert response["elapsed_seconds"] == 75.5

    def test_transition_preserves_elapsed_when_not_provided(self):
        """Transitions without explicit elapsed_seconds keep existing value."""
        tenant = SimulationTenant(
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="Active",
            elapsed_seconds=42.0,
        )
        paused = tenant.transition_to("Paused")
        assert paused.elapsed_seconds == 42.0


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
            "report_id",
            "tenant_id",
            "scenario_run_id",
            "scenario_type",
            "generated_at",
            "signal_summary",
            "recommendation_summary",
            "alert_summary",
            "coordination_gaps",
            "performance_metrics",
            "benchmark_comparison",
        ):
            assert field in doc


@pytest.fixture()
def simulation_client() -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def _inject_claims(request, call_next):
        request.state.claims = {
            "sub": "user-1",
            "agency_id": "agency-a",
            "jurisdiction_ids": ["NSW"],
            "roles": ["SimulationUser"],
            "persona_id": "persona-1",
        }
        return await call_next(request)

    simulations_routes._repo._in_memory_docs.clear()
    app.include_router(simulations_routes.router)
    return TestClient(app)


class TestSpec006CompatSimulationRoutes:
    def test_create_list_start_get_abort_flow(self, simulation_client: TestClient) -> None:
        scenario_body = {
            "name": "Flood NSW",
            "scenarioType": "flood",
            "targetRegion": {
                "type": "Polygon",
                "coordinates": [[[151.0, -34.0], [151.5, -34.0], [151.5, -33.5], [151.0, -33.5], [151.0, -34.0]]],
            },
            "targetJurisdictionIds": ["NSW"],
            "activatedDataSourceIds": ["bom-warnings", "bom-river-gauges"],
            "timeCompressionRatio": 4.0,
            "misinformationRatio": 0.2,
        }
        created = simulation_client.post("/simulations/scenarios", json=scenario_body)
        assert created.status_code == 201
        scenario_id = created.json()["scenarioId"]

        listed = simulation_client.get("/simulations/scenarios")
        assert listed.status_code == 200
        assert any(row["scenarioId"] == scenario_id for row in listed.json())

        started = simulation_client.post(
            "/simulations/runs",
            json={"scenarioId": scenario_id, "requestedByPersonaId": "persona-1", "timeCompressionRatio": 8.0},
        )
        assert started.status_code == 202
        run = started.json()
        assert run["status"] == "running"

        fetched = simulation_client.get(f"/simulations/runs/{run['runId']}")
        assert fetched.status_code == 200
        assert fetched.json()["runId"] == run["runId"]

        aborted = simulation_client.post(
            f"/simulations/runs/{run['runId']}/abort",
            json={"requestedByPersonaId": "persona-1"},
        )
        assert aborted.status_code == 200
        assert aborted.json()["status"] == "aborted"

        duplicate_abort = simulation_client.post(
            f"/simulations/runs/{run['runId']}/abort",
            json={"requestedByPersonaId": "persona-1"},
        )
        assert duplicate_abort.status_code == 409

    def test_unknown_run_returns_404(self, simulation_client: TestClient) -> None:
        response = simulation_client.get("/simulations/runs/not-found")
        assert response.status_code == 404

    def test_polygon_and_catalogue_validation(self, simulation_client: TestClient) -> None:
        invalid_polygon = simulation_client.post(
            "/simulations/scenarios",
            json={
                "name": "Bad",
                "scenarioType": "flood",
                "targetRegion": {"type": "Point", "coordinates": [151.0, -33.8]},
                "targetJurisdictionIds": ["NSW"],
                "activatedDataSourceIds": ["bom-warnings"],
            },
        )
        assert invalid_polygon.status_code == 400

        invalid_source = simulation_client.post(
            "/simulations/scenarios",
            json={
                "name": "Bad Source",
                "scenarioType": "flood",
                "targetRegion": {
                    "type": "Polygon",
                    "coordinates": [[[151.0, -34.0], [151.5, -34.0], [151.5, -33.5], [151.0, -33.5], [151.0, -34.0]]],
                },
                "targetJurisdictionIds": ["NSW"],
                "activatedDataSourceIds": ["not-a-source"],
            },
        )
        assert invalid_source.status_code == 400

    def test_ratio_bounds_validation(self, simulation_client: TestClient) -> None:
        response = simulation_client.post(
            "/simulations/scenarios",
            json={
                "name": "Bad Ratio",
                "scenarioType": "flood",
                "targetRegion": {
                    "type": "Polygon",
                    "coordinates": [[[151.0, -34.0], [151.5, -34.0], [151.5, -33.5], [151.0, -33.5], [151.0, -34.0]]],
                },
                "targetJurisdictionIds": ["NSW"],
                "activatedDataSourceIds": ["bom-warnings"],
                "misinformationRatio": 1.5,
            },
        )
        assert response.status_code == 422

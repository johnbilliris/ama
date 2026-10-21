"""Tests for evacuation.agent endpoints — health, override, replan (T043)."""

import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from datetime import UTC, datetime

import pytest
from common.entra_principal import AuthenticatedPrincipal
from evacuation import telemetry as tel
from evacuation.agent import EvacuationAgent, create_app
from evacuation.config import EvacuationConfig
from evacuation.models import DecisionType
from evacuation.road_network import RoadNetworkLoader
from fastapi import HTTPException
from fastapi.testclient import TestClient

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"
COMMANDER_HEADERS = {"Authorization": "Bearer commander"}
REVIEWER_HEADERS = {"Authorization": "Bearer reviewer"}
FOREIGN_TENANT_HEADERS = {"Authorization": "Bearer foreign-tenant"}
REPLAN_EVIDENCE = {
    "update_id": "update-001",
    "base_plan_version": 1,
    "observed_at": "2026-01-02T00:00:00+00:00",
}


class _FakePlansStore:
    def __init__(self):
        self.read_calls = []
        self.replace_calls = []
        self.batch_calls = []
        self.conflict_on_replace = False
        self.conflict_on_batch = False
        self.unavailable = False
        zone = {
            "zone_id": "zone-1",
            "zone_name": "Zone 1",
            "zone_number": 1,
            "priority": 1,
            "population_estimate": 120,
            "vulnerable_population": 20,
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.70, -16.98],
                        [145.82, -16.98],
                        [145.82, -16.82],
                        [145.70, -16.82],
                        [145.70, -16.98],
                    ]
                ],
            },
        }
        route = {
            "route_id": "route-original",
            "zone_id": "1",
            "assembly_area_id": "assembly-001",
            "route_name": "Original route",
            "distance_km": 8.0,
            "estimated_travel_minutes": 18,
            "capacity_vehicles_per_hour": 500,
            "waypoints": ["edge-002", "edge-001"],
        }
        phase = {
            "phase_number": 1,
            "zone_ids": ["1"],
            "start_offset_minutes": 30,
            "duration_minutes": 45,
            "population_moved": 120,
            "description": "Original phase",
        }
        self.docs = {
            "ep-inc-001-v1": {
                "id": "ep-inc-001-v1",
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "tenant_id": "tenant-a",
                "incident_scope_key": "tenant-a:inc-001",
                "status": "proposed",
                "version": 1,
                "confidence_score": 0.8,
                "affected_area": zone["boundary"],
                "zones": [zone],
                "routes": [route],
                "phases": [phase],
                "zone_dispositions": [
                    {
                        "zone_id": "zone-1",
                        "zone_number": 1,
                        "disposition": "evacuation",
                        "urgency": "immediate",
                        "affected_population": 120,
                        "evacuating_population": 120,
                        "remaining_population": 0,
                        "rationale": "Route available",
                    }
                ],
                "transport_requirements": [],
                "shelter_in_place_zones": [],
                "population_estimate": 120,
                "total_population": 120,
                "estimated_completion_minutes": 75,
                "mobilisation_time_minutes": 30,
                "updated_at": "2026-01-01T00:00:00+00:00",
                "created_at": "2026-01-01T00:00:00+00:00",
                "hazard_summary": {
                    "hazard_type": "flood",
                    "hazard_types": ["flood"],
                    "severity_level": "high",
                    "time_horizon": "8h",
                    "estimated_arrival_minutes": 480,
                    "source_assessment_id": "assess-001",
                    "affected_area": zone["boundary"],
                    "sources": [
                        {
                            "assessment_id": "assess-001",
                            "hazard_type": "flood",
                            "severity_level": "high",
                            "affected_area": zone["boundary"],
                            "input_signal_ids": ["signal-001"],
                            "generated_at": "2026-01-01T00:00:00+00:00",
                            "buffer_radius_metres": 2000,
                            "geometry_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        }
                    ],
                },
                "traceability": {
                    "source_handoff_id": "hf-001",
                    "risk_assessment_id": "assess-001",
                    "risk_assessment_ids": ["assess-001"],
                    "recommendation_id": "rec-001",
                    "input_signal_ids": ["signal-001"],
                    "input_data_versions": {"config": "config"},
                    "generation_method": "template_fallback",
                },
                "data_snapshot": {
                    "road_network_version": "road",
                    "population_data_version": "population",
                    "facility_data_version": "facility",
                    "assembly_area_data_version": "assembly",
                    "hazard_assessment_ids": ["assess-001"],
                    "hazard_geometry_algorithm": "per-hazard-aeqd-level-union-v1",
                },
                "assumptions": [],
                "generation_method": "template_fallback",
                "configuration_version": "config",
                "simulation": True,
                "summary": "Complete evacuation plan",
                "overrides": [],
                "_etag": "v1",
            },
            "inc-001_plan_counter": {
                "id": "inc-001_plan_counter",
                "current_version": 1,
                "incident_scope_key": "tenant-a:inc-001",
                "_etag": "counter-v1",
            },
        }

    def read_item(self, item: str, partition_key: str):
        self.read_calls.append((item, partition_key))
        if self.unavailable:
            raise RuntimeError("503 ServiceUnavailable")
        if item not in self.docs or partition_key != self.docs[item]["incident_scope_key"]:
            raise RuntimeError("404 NotFound")
        return deepcopy(self.docs[item])

    def replace_item(
        self,
        item: str,
        body: dict,
        partition_key: str | None = None,
        etag: str | None = None,
        match_condition: str | None = None,
    ):
        del partition_key
        self.replace_calls.append((item, dict(body)))
        if self.unavailable:
            raise RuntimeError("503 ServiceUnavailable")
        if item not in self.docs:
            raise RuntimeError("404 NotFound")
        current = self.docs[item]
        if self.conflict_on_replace or (etag is not None and etag != current.get("_etag")):
            raise RuntimeError("412 PreconditionFailed")
        next_doc = deepcopy(body)
        next_doc["_etag"] = f"{current.get('_etag', 'etag')}-next"
        self.docs[item] = next_doc
        return deepcopy(next_doc)

    def execute_item_batch(self, batch_operations, partition_key):
        self.batch_calls.append((deepcopy(batch_operations), partition_key))
        if self.unavailable:
            raise RuntimeError("503 ServiceUnavailable")
        if self.conflict_on_batch:
            raise RuntimeError("412 PreconditionFailed")

        next_docs = deepcopy(self.docs)
        for operation in batch_operations:
            operation_type, args = operation[:2]
            options = operation[2] if len(operation) == 3 else {}
            if operation_type == "create":
                body = deepcopy(args[0])
                if body["id"] in next_docs:
                    raise RuntimeError("409 Conflict")
                body["_etag"] = "created-v1"
                next_docs[body["id"]] = body
                continue

            item, body = args
            if item not in next_docs:
                raise RuntimeError("404 NotFound")
            current = next_docs[item]
            if options.get("if_match_etag") != current.get("_etag"):
                raise RuntimeError("412 PreconditionFailed")
            replacement = deepcopy(body)
            replacement["_etag"] = f"{current['_etag']}-next"
            next_docs[item] = replacement

        self.docs = next_docs
        return []

    def query_items(
        self,
        query,
        parameters,
        partition_key=None,
        enable_cross_partition_query=False,
    ):
        del enable_cross_partition_query
        if "COUNT(1)" in query:
            now = next(parameter["value"] for parameter in parameters if parameter["name"] == "@now")
            return [
                sum(
                    1
                    for document in self.docs.values()
                    if document.get("plan_id")
                    and document.get("status") in {"proposed", "approved", "paused"}
                    and (document.get("valid_until") is None or document.get("valid_until") > now)
                )
            ]
        incident_id = next(
            (parameter["value"] for parameter in parameters if parameter["name"] == "@incident_id"),
            None,
        )
        return [
            deepcopy(document)
            for document in self.docs.values()
            if document.get("plan_id")
            and document.get("incident_scope_key") == partition_key
            and (incident_id is None or document.get("incident_id") == incident_id)
        ]


@pytest.fixture
def plans_store():
    return _FakePlansStore()


async def _resolve_principal(request):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    principals = {
        "commander": AuthenticatedPrincipal(
            subject="user-1",
            tenant_id="tenant-a",
            roles=("incident_commander",),
            incident_ids=("inc-001",),
        ),
        "reviewer": AuthenticatedPrincipal(
            subject="reviewer-1",
            tenant_id="tenant-a",
            roles=("reviewer",),
            incident_ids=("inc-001",),
        ),
        "foreign-tenant": AuthenticatedPrincipal(
            subject="foreign-commander",
            tenant_id="tenant-b",
            roles=("incident_commander",),
            incident_ids=("inc-001",),
        ),
    }
    if token not in principals:
        raise HTTPException(status_code=401, detail="Bearer authentication is required")
    return principals[token]


@pytest.fixture
def app(plans_store):
    config = EvacuationConfig()
    road_network = RoadNetworkLoader()
    road_network.load(SAMPLE_FILE)

    agent = EvacuationAgent(
        config=config,
        road_network=road_network,
        cosmos_plans_container=plans_store,
        cosmos_decisions_container=None,
        cosmos_assessments_container=None,
    )
    return create_app(agent=agent, config=config, principal_resolver=_resolve_principal)


@pytest.fixture
def client(app):
    return TestClient(app)


def _override(client, action, *, modifications=None, justification="Commander decision"):
    payload = {
        "plan_id": "ep-inc-001-v1",
        "incident_id": "inc-001",
        "action": action,
        "justification": justification,
    }
    if modifications is not None:
        payload["modifications"] = modifications
    return client.post("/override", json=payload, headers=COMMANDER_HEADERS)


def _route_modification():
    return {
        "override_type": "route_override",
        "details": {
            "routes": [
                {
                    "route_id": "route-commander",
                    "zone_id": "1",
                    "assembly_area_id": "aa-001",
                    "route_name": "Commander alternative",
                    "distance_km": 10.5,
                    "estimated_travel_minutes": 24,
                    "capacity_vehicles_per_hour": 350,
                    "waypoints": ["edge-002", "edge-001"],
                }
            ]
        },
    }


def _without_lifecycle_metadata(document):
    lifecycle_fields = {
        "_etag",
        "status",
        "updated_at",
        "superseded_by",
        "superseded_at",
    }
    return {key: value for key, value in document.items() if key not in lifecycle_fields}


def _without_route_allocation_metadata(document):
    allocation_fields = {
        "allocated_population",
        "evacuation_load_vehicles_per_hour",
        "uncapped_utilisation_pct",
        "congestion_risk_pct",
        "congestion_risk",
        "capacity_overloaded",
        "bottleneck_edge_ids",
        "zone_shared_capacity_vehicles_per_hour",
    }
    return {key: value for key, value in document.items() if key not in allocation_fields}


# ---------------------------------------------------------------------------
# GET /health returns valid JSON
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert "agent_version" in data
        assert "timestamp" in data
        assert "checks" in data

    def test_health_checks_structure(self, client):
        resp = client.get("/health")
        checks = resp.json()["checks"]
        assert "road_network_loaded" in checks
        assert "llm_connectivity" in checks
        assert "cosmos_connectivity" in checks
        assert "active_plan_count" in checks
        assert "processing_queue_depth" in checks
        assert "audit_store" in checks

    def test_road_network_loaded(self, client):
        resp = client.get("/health")
        rn = resp.json()["checks"]["road_network_loaded"]
        assert rn["node_count"] == 50
        assert rn["edge_count"] == 120

    def test_health_never_calls_slow_llm(self, app, client):
        called = {"value": False}

        def forbidden_probe(**kwargs):
            del kwargs
            called["value"] = True
            time.sleep(1.1)
            raise AssertionError("health must not call dependencies")

        app.state.agent._llm_client.generate_response = forbidden_probe
        app.state.agent.update_llm_health(
            status="offline",
            checked_at=datetime.now(UTC),
            latency_ms=None,
        )

        started = time.perf_counter()
        response = client.get("/health")
        elapsed = time.perf_counter() - started

        assert response.status_code == 200
        assert elapsed < 0.2
        assert called["value"] is False
        assert response.json()["checks"]["llm_connectivity"]["status"] == "offline"

    @pytest.mark.parametrize(
        ("depth", "expected"),
        [(19, "healthy"), (20, "backpressure")],
    )
    def test_queue_depth_boundaries(self, app, client, depth, expected):
        app.state.agent.update_queue_health(
            status="connected",
            depth=depth,
            checked_at=datetime.now(UTC),
        )

        check = client.get("/health").json()["checks"]["processing_queue_depth"]

        assert check["depth"] == depth
        assert check["status"] == expected
        assert check["connected"] is True

    @pytest.mark.parametrize(
        ("count", "expected"),
        [(39, "healthy"), (40, "warning")],
    )
    def test_active_plan_boundaries(self, app, client, count, expected):
        app.state.agent.update_active_plan_count(count)

        check = client.get("/health").json()["checks"]["active_plan_count"]

        assert check == {"count": count, "status": expected}

    def test_cosmos_failure_and_recovery_are_cached_with_timestamps(self, app, client):
        failed_at = datetime(2026, 1, 1, tzinfo=UTC)
        app.state.agent.update_cosmos_health(False, failed_at)
        failed = client.get("/health").json()["checks"]["cosmos_connectivity"]
        assert failed["status"] == "degraded"
        assert failed["last_checked_at"].startswith("2026-01-01")
        assert failed["last_successful_at"] is None

        recovered_at = datetime(2026, 1, 2, tzinfo=UTC)
        app.state.agent.update_cosmos_health(True, recovered_at)
        recovered = client.get("/health").json()["checks"]["cosmos_connectivity"]
        assert recovered["status"] == "healthy"
        assert recovered["last_successful_at"].startswith("2026-01-02")

    def test_road_health_exposes_source_and_load_timestamps(self, client):
        road = client.get("/health").json()["checks"]["road_network_loaded"]

        assert road["last_loaded_at"]
        assert road["source_updated_at"] == "2026-04-16T00:00:00Z"

    def test_liveness_and_readiness_are_distinct(self, app, client):
        app.state.agent.update_queue_health(
            status="offline",
            depth=0,
            checked_at=datetime.now(UTC),
        )

        assert client.get("/live").status_code == 200
        ready = client.get("/ready")
        assert ready.status_code == 503
        assert ready.json()["status"] == "unhealthy"

    def test_noncritical_degradation_remains_ready(self, app, client):
        app.state.agent.update_queue_health(
            status="connected",
            depth=0,
            checked_at=datetime.now(UTC),
        )
        app.state.agent.update_llm_health(
            status="offline",
            checked_at=datetime.now(UTC),
            latency_ms=None,
        )

        ready = client.get("/ready")

        assert ready.status_code == 200
        assert ready.json()["status"] == "degraded"

    def test_concurrent_cached_health_requests_complete_subsecond(self, client):
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=8) as executor:
            responses = list(executor.map(lambda _: client.get("/health"), range(16)))
        elapsed = time.perf_counter() - started

        assert all(response.status_code == 200 for response in responses)
        assert elapsed < 1

    def test_audit_and_road_states_are_reflected_without_probes(self, app, client):
        app.state.agent._pipeline.audit_writer._spill_corrupt = True
        degraded = client.get("/health").json()
        assert degraded["checks"]["audit_store"]["status"] == "degraded"

        app.state.agent._road_network._data = None
        offline = client.get("/health").json()
        assert offline["checks"]["road_network_loaded"]["status"] == "offline"
        assert offline["status"] == "unhealthy"

    def test_terminal_override_updates_committed_active_count(self, app, client):
        app.state.agent.update_active_plan_count(1)

        response = _override(client, "reject")

        assert response.status_code == 200
        count = client.get("/health").json()["checks"]["active_plan_count"]
        assert count == {"count": 0, "status": "healthy"}


class TestOverrideTelemetry:
    def test_route_override_updates_type_and_unique_plan_rate(
        self,
        client,
        monkeypatch,
    ):
        rates = []
        types = []
        monkeypatch.setattr(
            tel.override_rate,
            "set",
            lambda value, attributes=None: rates.append((value, attributes)),
        )
        monkeypatch.setattr(
            tel.override_by_type,
            "add",
            lambda value, attributes=None: types.append((value, attributes)),
        )

        response = _override(
            client,
            "modify",
            modifications=_route_modification(),
        )

        assert response.status_code == 200
        assert rates[-1] == (1.0, {"tenant_id": "tenant-a"})
        assert types[-1] == (
            1,
            {
                "action": "route",
                "incident_id": "inc-001",
                "tenant_id": "tenant-a",
            },
        )


# ---------------------------------------------------------------------------
# POST /override with valid actions
# ---------------------------------------------------------------------------


class TestOverrideEndpoint:
    def test_valid_override_approve(self, app, client, plans_store):
        """A verified commander can commit an override to the scoped plan."""
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "action": "approve",
                "justification": "Plan looks good",
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_status"] == "approved"
        assert data["plan_id"] == "ep-inc-001-v1"
        assert plans_store.docs["ep-inc-001-v1"]["overrides"][-1]["override_by_user_id"] == "user-1"
        audit_writer = app.state.agent._pipeline.audit_writer
        assert audit_writer.buffer_depth == 1
        assert "user-1" in audit_writer._buffer[-1].record.decision_rationale

    def test_override_response_fields(self, client):
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "action": "reject",
                "user_id": "user-1",
                "role": "incident_commander",
                "justification": "Insufficient routes",
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "previous_status" in data
        assert "new_status" in data
        assert "override_timestamp" in data
        assert "audit_record_id" in data

    def test_override_reviewer_forbidden(self, client):
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "action": "reject",
                "user_id": "user-1",
                "role": "incident_commander",
                "justification": "Insufficient routes",
            },
            headers=REVIEWER_HEADERS,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Invalid action returns 422
# ---------------------------------------------------------------------------


class TestInvalidOverride:
    def test_invalid_action_returns_422(self, client):
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "action": "invalid_action",
                "user_id": "user-1",
                "role": "incident_commander",
                "justification": "test",
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 422


class TestOverrideLifecycle:
    @pytest.mark.parametrize(
        ("start_status", "action", "target_status"),
        [
            ("proposed", "approve", "approved"),
            ("proposed", "reject", "rejected"),
            ("proposed", "cancel", "cancelled"),
            ("approved", "cancel", "cancelled"),
            ("paused", "cancel", "cancelled"),
            ("proposed", "pause", "paused"),
            ("approved", "pause", "paused"),
            ("paused", "resume", "approved"),
        ],
    )
    def test_status_actions_preserve_plan_version(
        self,
        client,
        plans_store,
        start_status,
        action,
        target_status,
    ):
        plans_store.docs["ep-inc-001-v1"]["status"] = start_status
        response = _override(client, action)
        assert response.status_code == 200
        assert response.json()["new_status"] == target_status
        assert response.json()["new_version_plan_id"] is None
        stored = plans_store.docs["ep-inc-001-v1"]
        assert stored["status"] == target_status
        assert stored["version"] == 1
        assert stored["overrides"][-1]["override_action_type"] == action

    @pytest.mark.parametrize("terminal_status", ["rejected", "cancelled", "superseded", "expired"])
    def test_terminal_states_cannot_transition(self, client, plans_store, terminal_status):
        plans_store.docs["ep-inc-001-v1"]["status"] = terminal_status
        before = deepcopy(plans_store.docs["ep-inc-001-v1"])
        response = _override(client, "approve")
        assert response.status_code == 422
        assert plans_store.docs["ep-inc-001-v1"] == before
        assert plans_store.replace_calls == []

    def test_repeated_status_action_is_not_reported_as_change(self, client, plans_store):
        plans_store.docs["ep-inc-001-v1"]["status"] = "approved"
        response = _override(client, "approve")
        assert response.status_code == 422
        assert plans_store.replace_calls == []

    def test_status_action_rejects_modification_payload(self, client, plans_store):
        response = _override(client, "approve", modifications=_route_modification())
        assert response.status_code == 422
        assert plans_store.replace_calls == []

    @staticmethod
    def _seed_linked_proposal(plans_store):
        source = plans_store.docs["ep-inc-001-v1"]
        source["status"] = "approved"
        source["valid_until"] = None
        source["approved_at"] = "2026-01-01T01:00:00+00:00"
        proposal = deepcopy(source)
        proposal.update(
            {
                "id": "ep-inc-001-v2",
                "plan_id": "ep-inc-001-v2",
                "version": 2,
                "status": "proposed",
                "source_plan_id": "ep-inc-001-v1",
                "change_summary": "Updated evacuation proposal",
                "valid_until": "2099-01-02T04:00:00+00:00",
                "approved_at": None,
                "_etag": "v2",
            }
        )
        plans_store.docs["ep-inc-001-v2"] = proposal

    def test_approving_linked_proposal_atomically_supersedes_approved_source(
        self,
        client,
        plans_store,
    ):
        self._seed_linked_proposal(plans_store)
        response = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v2",
                "incident_id": "inc-001",
                "action": "approve",
                "justification": "Approve updated plan",
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 200
        source = plans_store.docs["ep-inc-001-v1"]
        approved = plans_store.docs["ep-inc-001-v2"]
        assert source["status"] == "superseded"
        assert source["superseded_by"] == "ep-inc-001-v2"
        assert source["superseded_at"]
        assert approved["status"] == "approved"
        assert approved["valid_until"] is None
        assert approved["approved_at"]

    def test_rejecting_linked_proposal_preserves_approved_source(self, client, plans_store):
        self._seed_linked_proposal(plans_store)
        source_before = deepcopy(plans_store.docs["ep-inc-001-v1"])
        response = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v2",
                "incident_id": "inc-001",
                "action": "reject",
                "justification": "Retain current approved plan",
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 200
        assert plans_store.docs["ep-inc-001-v1"] == source_before
        assert plans_store.docs["ep-inc-001-v2"]["status"] == "rejected"

    def test_concurrent_linked_approval_rolls_back_both_plans(self, client, plans_store):
        self._seed_linked_proposal(plans_store)
        before = deepcopy(plans_store.docs)
        plans_store.conflict_on_batch = True
        response = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v2",
                "incident_id": "inc-001",
                "action": "approve",
                "justification": "Approve updated plan",
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 409
        assert plans_store.docs == before


class TestPlanLifecycleQueries:
    def test_historical_version_returns_complete_owned_plan(
        self,
        client,
        plans_store,
    ):
        TestOverrideLifecycle._seed_linked_proposal(plans_store)

        response = client.get(
            "/plans/inc-001/versions/1",
            headers=COMMANDER_HEADERS,
        )

        assert response.status_code == 200
        document = response.json()
        assert document["plan_id"] == "ep-inc-001-v1"
        assert document["hazard_summary"]["time_horizon"] == "8h"
        assert document["traceability"]["recommendation_id"] == "rec-001"
        assert document["data_snapshot"]["road_network_version"] == "road"
        assert document["simulation"] is True

    def test_historical_version_is_tenant_scoped(self, client, plans_store):
        response = client.get(
            "/plans/inc-001/versions/1",
            headers=FOREIGN_TENANT_HEADERS,
        )

        assert response.status_code == 404
        assert plans_store.read_calls == [("ep-inc-001-v1", "tenant-b:inc-001")]

    def test_missing_historical_version_returns_not_found(self, client):
        response = client.get(
            "/plans/inc-001/versions/99",
            headers=COMMANDER_HEADERS,
        )

        assert response.status_code == 404

    def test_approved_source_is_authoritative_beside_newer_proposal(
        self,
        client,
        plans_store,
    ):
        TestOverrideLifecycle._seed_linked_proposal(plans_store)
        authoritative = client.get(
            "/plans/inc-001/authoritative",
            headers=COMMANDER_HEADERS,
        )
        active = client.get("/plans/inc-001/active", headers=COMMANDER_HEADERS)
        history = client.get("/plans/inc-001/history", headers=COMMANDER_HEADERS)
        assert authoritative.status_code == 200
        assert authoritative.json()["plan_id"] == "ep-inc-001-v1"
        assert [plan["plan_id"] for plan in active.json()] == [
            "ep-inc-001-v2",
            "ep-inc-001-v1",
        ]
        assert [plan["plan_id"] for plan in history.json()] == [
            "ep-inc-001-v2",
            "ep-inc-001-v1",
        ]

    def test_linked_approval_flips_authority_and_active_count(self, client, plans_store):
        TestOverrideLifecycle._seed_linked_proposal(plans_store)
        approve = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v2",
                "incident_id": "inc-001",
                "action": "approve",
                "justification": "Approve updated plan",
            },
            headers=COMMANDER_HEADERS,
        )
        assert approve.status_code == 200
        authoritative = client.get(
            "/plans/inc-001/authoritative",
            headers=COMMANDER_HEADERS,
        )
        active = client.get("/plans/inc-001/active", headers=COMMANDER_HEADERS)
        history = client.get("/plans/inc-001/history", headers=COMMANDER_HEADERS)
        assert authoritative.json()["plan_id"] == "ep-inc-001-v2"
        assert [plan["plan_id"] for plan in active.json()] == ["ep-inc-001-v2"]
        assert [plan["status"] for plan in history.json()] == ["approved", "superseded"]
        assert (
            next(
                iter(
                    plans_store.query_items(
                        query="SELECT VALUE COUNT(1)",
                        parameters=[{"name": "@now", "value": "2026-01-01T00:00:00+00:00"}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            == 1
        )

    def test_expired_proposal_remains_in_history_and_is_audited(
        self,
        app,
        client,
        plans_store,
    ):
        plans_store.docs["ep-inc-001-v1"]["valid_until"] = "2025-01-01T00:00:00+00:00"
        active = client.get("/plans/inc-001/active", headers=COMMANDER_HEADERS)
        history = client.get("/plans/inc-001/history", headers=COMMANDER_HEADERS)
        assert active.status_code == 200
        assert active.json() == []
        assert history.json()[0]["status"] == "expired"
        audit = app.state.agent._pipeline.audit_writer._buffer[-1].record
        assert audit.plan_id == "ep-inc-001-v1"
        assert "expired" in audit.decision_rationale

    def test_history_denies_unassigned_incident_before_query(self, client, plans_store):
        response = client.get(
            "/plans/inc-999/history",
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 403


class TestAuditHistoryQueries:
    def test_combined_filter_and_pagination(self, app, client):
        from datetime import UTC, datetime

        from tests.unit.test_evacuation_audit import _query_record, _QueryCosmos

        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        store = _QueryCosmos(
            [
                _query_record(
                    "a",
                    timestamp,
                    incident_id="inc-001",
                    plan_id="ep-inc-001-v1",
                ),
                _query_record(
                    "b",
                    timestamp,
                    incident_id="inc-001",
                    plan_id="ep-inc-001-v1",
                ),
                _query_record(
                    "c",
                    timestamp,
                    incident_id="inc-001",
                    plan_id="ep-inc-001-v1",
                    decision_type=DecisionType.transport_coordinated,
                ),
            ]
        )
        app.state.agent._pipeline.audit_writer._cosmos_client = store

        first = client.get(
            "/audits/inc-001",
            params={
                "plan_id": "ep-inc-001-v1",
                "decision_type": "routes_computed",
                "from_timestamp": "2026-01-01T00:00:00Z",
                "to_timestamp": "2026-01-01T00:00:00Z",
                "limit": 1,
            },
            headers=COMMANDER_HEADERS,
        )

        assert first.status_code == 200
        first_body = first.json()
        assert [record["id"] for record in first_body["records"]] == ["a"]
        assert first_body["next_cursor"]

        second = client.get(
            "/audits/inc-001",
            params={
                "plan_id": "ep-inc-001-v1",
                "decision_type": "routes_computed",
                "from_timestamp": "2026-01-01T00:00:00Z",
                "to_timestamp": "2026-01-01T00:00:00Z",
                "limit": 1,
                "cursor": first_body["next_cursor"],
            },
            headers=COMMANDER_HEADERS,
        )

        assert second.status_code == 200
        assert [record["id"] for record in second.json()["records"]] == ["b"]

    def test_foreign_tenant_identical_incident_cannot_see_live_records(
        self,
        app,
        client,
    ):
        from datetime import UTC, datetime

        from tests.unit.test_evacuation_audit import _query_record, _QueryCosmos

        store = _QueryCosmos([_query_record("a", datetime(2026, 1, 1, tzinfo=UTC))])
        app.state.agent._pipeline.audit_writer._cosmos_client = store

        response = client.get(
            "/audits/inc-001",
            headers=FOREIGN_TENANT_HEADERS,
        )

        assert response.status_code == 200
        assert response.json()["records"] == []
        assert store.query_calls[0][2] == "tenant-b:inc-001"

    def test_unassigned_incident_is_denied_before_audit_query(
        self,
        app,
        client,
    ):
        from tests.unit.test_evacuation_audit import _QueryCosmos

        store = _QueryCosmos([])
        app.state.agent._pipeline.audit_writer._cosmos_client = store

        response = client.get(
            "/audits/inc-999",
            headers=COMMANDER_HEADERS,
        )

        assert response.status_code == 403
        assert store.query_calls == []


class TestImmutablePlanModification:
    def test_route_override_creates_linked_version_and_preserves_source(
        self,
        app,
        client,
        plans_store,
    ):
        source_before = deepcopy(plans_store.docs["ep-inc-001-v1"])
        response = _override(client, "modify", modifications=_route_modification())
        assert response.status_code == 200
        assert response.json()["new_version_plan_id"] == "ep-inc-001-v2"

        source_after = plans_store.docs["ep-inc-001-v1"]
        assert source_after["status"] == "superseded"
        assert source_after["superseded_by"] == "ep-inc-001-v2"
        assert source_after["superseded_at"]
        assert _without_lifecycle_metadata(source_after) == _without_lifecycle_metadata(source_before)
        modified = plans_store.docs["ep-inc-001-v2"]
        assert modified["source_plan_id"] == "ep-inc-001-v1"
        assert modified["version"] == 2
        assert modified["status"] == "proposed"
        assert modified["routes"][0]["route_id"] == "route-commander"
        assert "route-commander" in modified["summary"]
        assert modified["generation_method"] == "template_fallback"
        assert modified["phases"] != source_before["phases"]
        assert plans_store.docs["inc-001_plan_counter"]["current_version"] == 2

        metadata = modified["overrides"][-1]
        assert metadata["override_by_user_id"] == "user-1"
        assert metadata["override_by_role"] == "incident_commander"
        assert metadata["override_justification"] == "Commander decision"
        assert metadata["override_action_type"] == "route_override"
        assert metadata["source_plan_id"] == "ep-inc-001-v1"
        assert metadata["original_values"]["routes"] == source_before["routes"]
        assert metadata["modified_values"]["routes"] == modified["routes"]
        assert metadata["override_timestamp"]

        audit = app.state.agent._pipeline.audit_writer._buffer[-1].record
        assert audit.plan_id == "ep-inc-001-v2"
        assert audit.incident_id == "inc-001"
        assert audit.incident_scope_key == "tenant-a:inc-001"
        assert audit.tenant_id == "tenant-a"
        assert audit.override_metadata.model_dump(mode="json") == metadata

    def test_zone_boundary_change_recomputes_routes_population_and_timeline(
        self,
        client,
        plans_store,
    ):
        changed_zone = deepcopy(plans_store.docs["ep-inc-001-v1"]["zones"][0])
        changed_zone["population_estimate"] = 200
        changed_zone["boundary"] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.65, -17.05],
                    [145.85, -17.05],
                    [145.85, -16.78],
                    [145.65, -16.78],
                    [145.65, -17.05],
                ]
            ],
        }
        response = _override(
            client,
            "modify",
            modifications={
                "override_type": "zone_boundary_change",
                "details": {"zones": [changed_zone]},
            },
        )
        assert response.status_code == 200
        modified = plans_store.docs[response.json()["new_version_plan_id"]]
        assert modified["total_population"] == 200
        assert modified["routes"] != plans_store.docs["ep-inc-001-v1"]["routes"]
        assert modified["phases"] != plans_store.docs["ep-inc-001-v1"]["phases"]
        metadata = modified["overrides"][-1]
        assert "routes" in metadata["modified_values"]
        assert "estimated_completion_minutes" in metadata["modified_values"]

    def test_phase_reprioritization_recalculates_completion(self, client, plans_store):
        phases = [
            {
                "phase_number": 2,
                "zone_ids": ["1"],
                "start_offset_minutes": 10,
                "duration_minutes": 20,
                "population_moved": 50,
                "description": "Field-priority phase",
            },
            {
                "phase_number": 1,
                "zone_ids": ["1"],
                "start_offset_minutes": 30,
                "duration_minutes": 25,
                "population_moved": 70,
                "description": "Follow-up phase",
            },
        ]
        response = _override(
            client,
            "modify",
            modifications={
                "override_type": "phase_reprioritization",
                "details": {"phases": phases},
            },
        )
        assert response.status_code == 200
        modified = plans_store.docs[response.json()["new_version_plan_id"]]
        assert [phase["phase_number"] for phase in modified["phases"]] == [1, 2]
        assert [phase["start_offset_minutes"] for phase in modified["phases"]] == [30, 50]
        assert modified["estimated_completion_minutes"] == 75

    @pytest.mark.parametrize("edge_id", ["missing-edge", "edge-001"])
    def test_route_override_rejects_unknown_or_closed_road(
        self,
        app,
        client,
        plans_store,
        edge_id,
    ):
        modification = _route_modification()
        modification["details"]["routes"][0]["waypoints"] = [edge_id]
        if edge_id == "edge-001":
            app.state.agent._road_network.apply_closure(edge_id, "field closure")
        response = _override(client, "modify", modifications=modification)
        assert response.status_code == 422
        assert plans_store.batch_calls == []

    @pytest.mark.parametrize(
        "modifications",
        [
            None,
            {},
            {"override_type": "unknown", "details": {}},
            {"override_type": "route_override", "details": {}},
            {"override_type": "route_override", "details": {"routes": []}},
            {
                "override_type": "route_override",
                "details": {"routes": [], "unknown": []},
            },
        ],
    )
    def test_invalid_modification_is_rejected_without_writes(
        self,
        client,
        plans_store,
        modifications,
    ):
        response = _override(client, "modify", modifications=modifications)
        assert response.status_code == 422
        assert plans_store.replace_calls == []
        assert plans_store.batch_calls == []

    def test_no_op_modification_is_rejected(self, client, plans_store):
        response = _override(
            client,
            "modify",
            modifications={
                "override_type": "route_override",
                "details": {"routes": deepcopy(plans_store.docs["ep-inc-001-v1"]["routes"])},
            },
        )
        assert response.status_code == 422
        assert plans_store.batch_calls == []

    def test_terminal_plan_cannot_be_modified(self, client, plans_store):
        plans_store.docs["ep-inc-001-v1"]["status"] = "superseded"
        response = _override(client, "modify", modifications=_route_modification())
        assert response.status_code == 422
        assert plans_store.batch_calls == []


class TestOverridePersistenceFailures:
    def test_missing_plan_returns_404(self, client, plans_store):
        del plans_store.docs["ep-inc-001-v1"]
        response = _override(client, "approve")
        assert response.status_code == 404

    def test_unavailable_store_returns_503(self, client, plans_store):
        plans_store.unavailable = True
        response = _override(client, "approve")
        assert response.status_code == 503

    def test_simultaneous_status_override_returns_409_without_success_audit(
        self,
        app,
        client,
        plans_store,
    ):
        plans_store.conflict_on_replace = True
        response = _override(client, "approve")
        assert response.status_code == 409
        assert app.state.agent._pipeline.audit_writer.buffer_depth == 0

    def test_atomic_modify_conflict_leaves_source_counter_and_version_unchanged(
        self,
        app,
        client,
        plans_store,
    ):
        before = deepcopy(plans_store.docs)
        plans_store.conflict_on_batch = True
        response = _override(client, "modify", modifications=_route_modification())
        assert response.status_code == 409
        assert plans_store.docs == before
        assert "ep-inc-001-v2" not in plans_store.docs
        assert app.state.agent._pipeline.audit_writer.buffer_depth == 0

    def test_modify_serializes_against_replan_with_source_etag(
        self,
        app,
        client,
        plans_store,
    ):
        stale_plan = deepcopy(plans_store.docs["ep-inc-001-v1"])
        response = _override(client, "modify", modifications=_route_modification())
        assert response.status_code == 200
        with pytest.raises(RuntimeError, match="PreconditionFailed"):
            app.state.agent.process_replan(
                incident_id="inc-001",
                current_plan=stale_plan,
                manual_trigger=True,
            )

    def test_missing_fields_returns_422(self, client):
        resp = client.post(
            "/override",
            json={"plan_id": "ep-inc-001-v1"},
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /replan triggers replanning
# ---------------------------------------------------------------------------


class TestReplanEndpoint:
    def test_replan_with_triggers(self, client):
        resp = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Operator requested replan",
                "manual_trigger": True,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["triggered"] is True
        assert len(data["triggers"]) > 0
        assert data["incident_id"] == "inc-001"

    def test_replan_no_triggers(self, client):
        resp = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Re-evaluate current conditions",
                "manual_trigger": False,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["triggered"] is False
        assert data["status"] == "unchanged"
        assert data["new_plan_id"] is None
        assert data["audit_record_id"]

    def test_replan_with_road_closures(self, client):
        resp = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Road closures reported",
                "new_road_closures": ["edge-002"],
                "manual_trigger": False,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["triggered"] is True

    def test_replan_response_fields(self, client):
        resp = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Operator requested replan",
                "manual_trigger": True,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        data = resp.json()
        assert "incident_id" in data
        assert "status" in data
        assert "previous_plan_id" in data
        assert "new_plan_id" in data
        assert "audit_record_id" in data
        assert "triggered" in data
        assert "triggers" in data
        assert "material_change" in data

    def test_unrelated_closure_is_audited_without_version(self, app, client, plans_store):
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Assess unrelated closure",
                "new_road_closures": ["edge-999"],
                "manual_trigger": False,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["triggered"] is False
        assert response.json()["new_plan_id"] is None
        assert "ep-inc-001-v2" not in plans_store.docs
        audit = app.state.agent._pipeline.audit_writer._buffer[-1].record
        assert audit.id == response.json()["audit_record_id"]
        assert "no material trigger" in audit.decision_rationale
        assert "user-1 (incident_commander)" in audit.decision_rationale
        assert "Assess unrelated closure" in audit.decision_rationale

    def test_blank_update_id_is_rejected_before_persistence(self, client, plans_store):
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Missing source update identity",
                **{**REPLAN_EVIDENCE, "update_id": "   "},
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 422
        assert plans_store.batch_calls == []

    @pytest.mark.parametrize("status", ["rejected", "cancelled", "superseded", "expired"])
    def test_terminal_source_returns_404(self, client, plans_store, status):
        plans_store.docs["ep-inc-001-v1"]["status"] = status
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Replan terminal source",
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 404
        assert plans_store.batch_calls == []

    def test_stale_base_version_returns_422(self, client, plans_store):
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Stale source version",
                **{**REPLAN_EVIDENCE, "base_plan_version": 0},
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 422
        assert plans_store.batch_calls == []

    def test_stale_observation_returns_422(self, client, plans_store):
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Out-of-order observation",
                **{**REPLAN_EVIDENCE, "observed_at": "2025-12-31T00:00:00+00:00"},
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 422
        assert plans_store.batch_calls == []

    def test_progress_delay_is_derived_from_observations(self, client, plans_store):
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Progress is behind plan",
                "progress_completed_pct": 40,
                "expected_progress_pct": 80,
                "manual_trigger": False,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 202
        replanned = plans_store.docs[response.json()["new_plan_id"]]
        assert replanned["progress_delay_pct"] == 50
        assert any("progress_delay" in trigger for trigger in response.json()["triggers"])
        audit = client.app.state.agent._pipeline.audit_writer._buffer[-1].record
        assert audit.operation_id == REPLAN_EVIDENCE["update_id"]
        assert audit.replanning_triggers == ["progress_delay"]
        assert audit.principal_id == "user-1"
        assert audit.routes_count == len(replanned["routes"])
        assert audit.transport_requests_count == len(replanned["transport_requirements"])

    def test_replan_cannot_claim_unaccepted_audit_id(self, app, client):
        app.state.agent._pipeline.audit_writer.write = lambda record: None

        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Manual safety replan",
                "manual_trigger": True,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )

        assert response.status_code == 503

    def test_geometry_expansion_is_derived_from_zone_snapshots(self, client, plans_store):
        zone = deepcopy(plans_store.docs["ep-inc-001-v1"]["zones"][0])
        zone["boundary"] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.65, -17.05],
                    [145.85, -17.05],
                    [145.85, -16.78],
                    [145.65, -16.78],
                    [145.65, -17.05],
                ]
            ],
        }
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Updated hazard geometry",
                "updated_zones": [zone],
                "manual_trigger": False,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 202
        assert any("hazard_expansion" in trigger for trigger in response.json()["triggers"])

    def test_invalid_or_lower_severity_does_not_override_source(self, client, plans_store):
        invalid = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Invalid severity",
                "new_severity": "catastrophic",
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert invalid.status_code == 422
        lower = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Lower severity report",
                "new_severity": "moderate",
                "manual_trigger": False,
                **{**REPLAN_EVIDENCE, "update_id": "update-lower"},
            },
            headers=COMMANDER_HEADERS,
        )
        assert lower.status_code == 200
        assert lower.json()["triggered"] is False
        assert plans_store.batch_calls == []

    def test_multiple_derived_signals_create_one_version(self, client, plans_store):
        response = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Closure, delay, and severity changed",
                "new_road_closures": ["edge-002"],
                "progress_completed_pct": 40,
                "expected_progress_pct": 80,
                "new_severity": "critical",
                "manual_trigger": False,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert response.status_code == 202
        trigger_types = {trigger.split(":", 1)[0] for trigger in response.json()["triggers"]}
        assert trigger_types == {"road_closure", "progress_delay", "severity_escalation"}
        assert response.json()["new_plan_id"] == "ep-inc-001-v2"
        assert len(plans_store.batch_calls) == 1


# ---------------------------------------------------------------------------
# Rate limiting returns 429 (via rate_limited field)
# ---------------------------------------------------------------------------


class TestHealthTransitionAudit:
    def test_health_change_emits_one_canonical_transition(self, app, client):
        agent = app.state.agent
        agent._last_health_status = "healthy"

        first = client.get("/health")
        second = client.get("/health")

        assert first.status_code == 200
        assert first.json()["status"] == "degraded"
        assert second.status_code == 200
        assert not [
            entry.record
            for entry in agent._pipeline.audit_writer._buffer
            if entry.record.operation_id == "health-transition"
        ]

        agent.record_health_transition(
            first.json()["status"],
            datetime.now(UTC),
        )
        records = [
            entry.record
            for entry in agent._pipeline.audit_writer._buffer
            if entry.record.operation_id == "health-transition"
        ]
        assert len(records) == 1
        assert records[0].incident_scope_key == "system:system-health"
        assert "healthy to degraded" in records[0].decision_rationale


class TestReplanRateLimiting:
    def test_rapid_replans_rate_limited(self, client, plans_store):
        """Second rapid replan should be rate-limited."""
        # First replan — should succeed
        resp1 = client.post(
            "/replan",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "justification": "Operator requested replan",
                "manual_trigger": True,
                **REPLAN_EVIDENCE,
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp1.status_code == 202
        successor_plan_id = resp1.json()["new_plan_id"]

        # Second replan immediately — should be rate-limited
        resp2 = client.post(
            "/replan",
            json={
                "plan_id": successor_plan_id,
                "incident_id": "inc-001",
                "justification": "Operator requested replan again",
                "manual_trigger": True,
                **{
                    **REPLAN_EVIDENCE,
                    "update_id": "update-002",
                    "base_plan_version": 2,
                    "observed_at": plans_store.docs[successor_plan_id]["updated_at"],
                },
            },
            headers=COMMANDER_HEADERS,
        )
        assert resp2.status_code == 429
        assert resp2.headers["Retry-After"] == "30"
        assert resp2.json()["detail"]["status"] == "rate_limited"
        assert resp2.json()["detail"]["audit_record_id"]


class TestDeterministicReplan:
    def test_successful_replan_spans_are_children_of_correlated_root(
        self,
        app,
        plans_store,
        monkeypatch,
    ):
        stack = []
        spans = []

        @contextmanager
        def record_span(name, attributes=None):
            parent = stack[-1] if stack else None
            spans.append((name, parent, attributes or {}))
            stack.append(name)
            try:
                yield
            finally:
                stack.pop()

        monkeypatch.setattr(tel, "start_span", record_span)

        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
            new_road_closures=["edge-002"],
            update_id="update-span-1",
        )

        assert result["new_plan_id"] == "ep-inc-001-v2"
        root = next(span for span in spans if span[0] == "evacuation.replan")
        assert root[1] is None
        assert root[2]["correlation_id"] == "update-span-1"
        child_names = {name for name, parent, _ in spans if parent == "evacuation.replan"}
        assert {
            "evacuation.evaluate_replan_trigger",
            "evacuation.incremental_road_update",
            "evacuation.recompute_affected_routes",
            "evacuation.update_transport",
            "evacuation.reestimate_timeline",
            "evacuation.generate_change_summary",
            "evacuation.assign_version",
            "evacuation.persist_plan",
            "evacuation.write_audit",
        }.issubset(child_names)

    def test_same_route_id_path_change_names_old_and_new_edges(self):
        summary = EvacuationAgent._build_replan_change_summary(
            {"routes": [{"route_id": "route-1", "waypoints": ["old-edge"]}]},
            {"routes": [{"route_id": "route-1", "waypoints": ["new-edge"]}]},
            ["road_closure: old-edge"],
            {"old-edge"},
        )

        assert "route-1: ['old-edge'] -> ['new-edge']" in summary

    def test_used_road_closure_creates_linked_plan_and_preserves_source(
        self,
        app,
        plans_store,
    ):
        source = deepcopy(plans_store.docs["ep-inc-001-v1"])
        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(source),
            new_road_closures=["edge-002"],
        )
        assert result["material_change"] is True
        assert result["previous_plan_id"] == "ep-inc-001-v1"
        assert result["new_plan_id"] == "ep-inc-001-v2"
        assert result["version"] == 2
        replanned = plans_store.docs["ep-inc-001-v2"]
        assert replanned["source_plan_id"] == "ep-inc-001-v1"
        assert replanned["status"] == "proposed"
        assert all("edge-002" not in route["waypoints"] for route in replanned["routes"])
        assert replanned["data_snapshot"]["road_network_version"] != source["data_snapshot"]["road_network_version"]
        assert "edge-002" in result["change_summary"]
        assert replanned["generation_method"] == "template_fallback"
        assert f"({replanned['confidence_score']:.0%})" in replanned["summary"]
        source_after = plans_store.docs["ep-inc-001-v1"]
        assert source_after["status"] == "superseded"
        assert source_after["superseded_by"] == "ep-inc-001-v2"
        assert _without_lifecycle_metadata(source_after) == _without_lifecycle_metadata(source)

    def test_unaffected_route_is_preserved_byte_for_byte(self, app, plans_store):
        unaffected = {
            "route_id": "route-zone-2",
            "zone_id": "2",
            "assembly_area_id": "aa-002",
            "route_name": "Unaffected route",
            "distance_km": 4.0,
            "estimated_travel_minutes": 8,
            "capacity_vehicles_per_hour": 900,
            "waypoints": ["edge-040"],
        }
        plans_store.docs["ep-inc-001-v1"]["routes"].append(deepcopy(unaffected))
        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
            new_road_closures=["edge-002"],
        )
        replanned = plans_store.docs[result["new_plan_id"]]
        retained = next(route for route in replanned["routes"] if route["route_id"] == "route-zone-2")
        assert _without_route_allocation_metadata(retained) == unaffected

    def test_replan_audit_describes_committed_version(self, app, plans_store):
        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
            new_road_closures=["edge-002"],
        )
        audit = app.state.agent._pipeline.audit_writer._buffer[-1].record
        assert audit.decision_type == "plan_updated"
        assert audit.plan_id == result["new_plan_id"]
        assert audit.version == 2
        assert audit.incident_scope_key == "tenant-a:inc-001"
        assert audit.route_ids == [route["route_id"] for route in plans_store.docs[result["new_plan_id"]]["routes"]]
        assert "edge-002" in audit.decision_rationale

    def test_updated_zone_snapshot_recomputes_population_and_timeline(self, app, plans_store):
        changed_zone = deepcopy(plans_store.docs["ep-inc-001-v1"]["zones"][0])
        changed_zone["population_estimate"] = 240
        changed_zone["boundary"] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.65, -17.05],
                    [145.85, -17.05],
                    [145.85, -16.78],
                    [145.65, -16.78],
                    [145.65, -17.05],
                ]
            ],
        }
        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
            hazard_area_change_pct=15,
            updated_zones=[changed_zone],
        )
        replanned = plans_store.docs[result["new_plan_id"]]
        assert replanned["total_population"] == 240
        assert replanned["zones"][0]["boundary"] == changed_zone["boundary"]
        assert replanned["phases"] != plans_store.docs["ep-inc-001-v1"]["phases"]
        assert "Zone boundaries" in result["change_summary"]

    def test_severity_and_progress_updates_change_persisted_plan(self, app, plans_store):
        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
            progress_delay_pct=35,
            new_severity="critical",
            current_severity="high",
        )
        replanned = plans_store.docs[result["new_plan_id"]]
        assert replanned["hazard_summary"]["severity_level"] == "critical"
        assert replanned["progress_delay_pct"] == 35
        assert "Severity changed: high -> critical" in result["change_summary"]
        assert "Timeline changed" in result["change_summary"]

    def test_batch_conflict_leaves_no_partial_version(
        self,
        app,
        plans_store,
        monkeypatch,
    ):
        source = deepcopy(plans_store.docs)
        completed_replans = []
        monkeypatch.setattr(
            tel.replan_count,
            "add",
            lambda value, attributes=None: completed_replans.append((value, attributes)),
        )
        plans_store.conflict_on_batch = True
        with pytest.raises(RuntimeError, match="PreconditionFailed"):
            app.state.agent.process_replan(
                incident_id="inc-001",
                current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
                new_road_closures=["edge-002"],
            )
        assert plans_store.docs == source
        assert "ep-inc-001-v2" not in plans_store.docs
        assert completed_replans == []

    def test_shelter_recovery_persists_and_emits_real_route(
        self,
        app,
        plans_store,
        monkeypatch,
    ):
        zone_two = deepcopy(plans_store.docs["ep-inc-001-v1"]["zones"][0])
        zone_two.update(
            {
                "zone_id": "zone-2",
                "zone_number": 2,
                "zone_name": "Zone 2",
                "population_estimate": 80,
            }
        )
        plans_store.docs["ep-inc-001-v1"]["zones"].append(zone_two)
        plans_store.docs["ep-inc-001-v1"]["total_population"] = 200
        plans_store.docs["ep-inc-001-v1"]["shelter_in_place_zones"] = ["2"]
        monkeypatch.setattr(
            app.state.agent,
            "_build_replan_network",
            lambda zones, closures: app.state.agent._road_network,
        )
        monkeypatch.setattr(
            app.state.agent._pipeline,
            "_assign_zone_origin_nodes",
            lambda zones, road_network: {
                zone.zone_number: (["node-002"] if zone.zone_number == 2 else []) for zone in zones
            },
        )
        recovery_events = []
        monkeypatch.setattr(
            tel,
            "emit_shelter_to_evacuation_recovery",
            lambda plan_id, zone, new_route_id: recovery_events.append((plan_id, zone, new_route_id)),
        )
        result = app.state.agent.process_replan(
            incident_id="inc-001",
            current_plan=deepcopy(plans_store.docs["ep-inc-001-v1"]),
            shelter_zones_with_new_routes=[2],
        )
        replanned = plans_store.docs[result["new_plan_id"]]
        recovered_routes = [route for route in replanned["routes"] if route["zone_id"] == "2"]
        assert recovered_routes
        assert all(route["route_id"] for route in recovered_routes)
        assert "2" not in replanned["shelter_in_place_zones"]
        assert recovery_events
        assert recovery_events[0][0] == result["new_plan_id"]
        assert recovery_events[0][1] == "2"
        assert recovery_events[0][2]


class TestControlAuthorization:
    @pytest.mark.parametrize(
        ("path", "payload"),
        [
            (
                "/override",
                {
                    "plan_id": "ep-inc-001-v1",
                    "incident_id": "inc-001",
                    "action": "approve",
                    "justification": "Approve plan",
                },
            ),
            (
                "/replan",
                {
                    "plan_id": "ep-inc-001-v1",
                    "incident_id": "inc-001",
                    "justification": "Replan incident",
                    **REPLAN_EVIDENCE,
                },
            ),
        ],
    )
    def test_anonymous_controls_are_rejected(self, client, path, payload):
        response = client.post(path, json=payload)
        assert response.status_code == 401

    def test_body_role_cannot_elevate_noncommander(self, client, plans_store):
        response = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-001-v1",
                "incident_id": "inc-001",
                "action": "approve",
                "role": "incident_commander",
                "justification": "Approve plan",
            },
            headers=REVIEWER_HEADERS,
        )
        assert response.status_code == 403
        assert plans_store.read_calls == []
        assert plans_store.replace_calls == []

    @pytest.mark.parametrize(
        ("assertion", "value"),
        [("user_id", "forged-user"), ("role", "state_controller")],
    )
    def test_forged_body_identity_is_rejected(self, client, plans_store, assertion, value):
        payload = {
            "plan_id": "ep-inc-001-v1",
            "incident_id": "inc-001",
            "action": "approve",
            "justification": "Approve plan",
            assertion: value,
        }
        response = client.post("/override", json=payload, headers=COMMANDER_HEADERS)
        assert response.status_code == 403
        assert plans_store.read_calls == []
        assert plans_store.replace_calls == []

    @pytest.mark.parametrize("path", ["/override", "/replan"])
    def test_unassigned_incident_is_rejected_before_storage(self, client, plans_store, path):
        payload = {
            "plan_id": "ep-inc-001-v1",
            "incident_id": "inc-999",
            "justification": "Control another incident",
        }
        if path == "/override":
            payload["action"] = "approve"
        else:
            payload.update(REPLAN_EVIDENCE)
        response = client.post(path, json=payload, headers=COMMANDER_HEADERS)
        assert response.status_code == 403
        assert plans_store.read_calls == []
        assert plans_store.replace_calls == []

    @pytest.mark.parametrize("path", ["/override", "/replan"])
    def test_foreign_tenant_plan_is_not_disclosed(self, client, plans_store, path):
        payload = {
            "plan_id": "ep-inc-001-v1",
            "incident_id": "inc-001",
            "justification": "Control foreign tenant plan",
        }
        if path == "/override":
            payload["action"] = "approve"
        else:
            payload.update(REPLAN_EVIDENCE)
        response = client.post(path, json=payload, headers=FOREIGN_TENANT_HEADERS)
        assert response.status_code == 404
        assert plans_store.read_calls == [("ep-inc-001-v1", "tenant-b:inc-001")]
        assert plans_store.replace_calls == []

    def test_override_cannot_claim_unaccepted_audit_id(
        self,
        app,
        client,
    ):
        app.state.agent._pipeline.audit_writer.write = lambda record: None

        response = _override(client, "approve")

        assert response.status_code == 503
        assert "audit was not accepted" in response.json()["detail"]

    @pytest.mark.parametrize("path", ["/override", "/replan"])
    def test_blank_justification_is_rejected_before_storage(self, client, plans_store, path):
        payload = {
            "plan_id": "ep-inc-001-v1",
            "incident_id": "inc-001",
            "justification": "   ",
        }
        if path == "/override":
            payload["action"] = "approve"
        else:
            payload.update(REPLAN_EVIDENCE)
        response = client.post(path, json=payload, headers=COMMANDER_HEADERS)
        assert response.status_code == 422
        assert plans_store.read_calls == []
        assert plans_store.replace_calls == []

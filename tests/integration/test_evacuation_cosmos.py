"""Integration tests for evacuation Cosmos DB operations (T054).

Uses mocks — does not require actual Cosmos DB connection.
"""

from datetime import UTC, datetime

import pytest
from evacuation.models import (
    DataSnapshot,
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPhase,
    EvacuationPlan,
    EvacuationZone,
    HazardSourceSnapshot,
    HazardSummary,
    Traceability,
    ZoneDisposition,
    ZoneDispositionType,
)

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

    def query_items(self, query, parameters=None, partition_key=None):
        return list(self._store.values())


# ---------------------------------------------------------------------------
# Plan write/read round trip
# ---------------------------------------------------------------------------


class TestPlanWriteReadRoundTrip:
    def test_write_and_read_plan(self):
        container = MockCosmosContainer()
        area = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        }
        source = HazardSourceSnapshot(
            assessment_id="assess-001",
            hazard_type="bushfire",
            severity_level="high",
            affected_area=area,
            generated_at=datetime.now(UTC),
            buffer_radius_metres=2_000,
            geometry_sha256="a" * 64,
        )
        plan = EvacuationPlan(
            plan_id="ep-inc-001-v1",
            incident_id="inc-001",
            confidence_score=0.85,
            affected_area=area,
            hazard_summary=HazardSummary(
                hazard_type="bushfire",
                hazard_types=["bushfire"],
                severity_level="high",
                time_horizon="4h",
                source_assessment_id="assess-001",
                affected_area=area,
                sources=[source],
            ),
            zones=[EvacuationZone(zone_id="1", zone_number=1, boundary=area)],
            phases=[EvacuationPhase(phase_number=1, zone_ids=["1"])],
            zone_dispositions=[
                ZoneDisposition(
                    zone_id="1",
                    zone_number=1,
                    disposition=ZoneDispositionType.shelter_in_place,
                    urgency="immediate",
                    affected_population=0,
                    evacuating_population=0,
                    remaining_population=0,
                    rationale="No movement required",
                )
            ],
            traceability=Traceability(
                source_handoff_id="hf-001",
                risk_assessment_id="assess-001",
                risk_assessment_ids=["assess-001"],
                recommendation_id="rec-001",
                input_data_versions={"config": "config"},
                generation_method="template_fallback",
            ),
            data_snapshot=DataSnapshot(
                road_network_version="road",
                population_data_version="population",
                facility_data_version="facility",
                assembly_area_data_version="assembly",
                hazard_assessment_ids=["assess-001"],
                hazard_geometry_algorithm="per-hazard-aeqd-level-union-v1",
            ),
            generation_method="template_fallback",
            configuration_version="config",
            summary="Test plan",
            incident_scope_key="live:inc-001",
            simulation=False,
            assumptions=[],
            population_estimate=0,
            total_population=0,
        )
        doc = plan.model_dump(mode="json")
        doc["id"] = plan.plan_id

        container.create_item(body=doc)
        retrieved = container.read_item(item=plan.plan_id, partition_key="live:inc-001")

        assert retrieved["plan_id"] == "ep-inc-001-v1"
        assert retrieved["incident_id"] == "inc-001"
        assert retrieved["confidence_score"] == 0.85

    def test_upsert_updates_existing(self):
        container = MockCosmosContainer()
        doc = {
            "id": "ep-inc-v1",
            "plan_id": "ep-inc-v1",
            "status": "proposed",
        }
        container.create_item(body=doc)

        # Update status
        doc["status"] = "approved"
        container.upsert_item(body=doc)

        retrieved = container.read_item(item="ep-inc-v1", partition_key="live:inc")
        assert retrieved["status"] == "approved"

    def test_read_nonexistent_raises(self):
        container = MockCosmosContainer()
        with pytest.raises(Exception, match="404"):
            container.read_item(item="nonexistent", partition_key="key")


# ---------------------------------------------------------------------------
# Decision record write/read round trip
# ---------------------------------------------------------------------------


def _audit_record(handoff_id, decision_type=DecisionType.handoff_received):
    plan_event = decision_type in {
        DecisionType.plan_generated,
        DecisionType.plan_updated,
    }
    return EvacuationDecisionRecord(
        handoff_id=handoff_id,
        operation_id=handoff_id,
        incident_id="inc-001",
        plan_id="ep-inc-001-v1" if plan_event else None,
        version=1 if plan_event else None,
        decision_type=decision_type,
        decision_rationale="Test canonical audit decision",
        agent_version="0.1.0",
        configuration_version="config",
        incident_scope_key="live:inc-001",
        tenant_id="live",
        routes_count=0 if plan_event else None,
        transport_requests_count=0 if plan_event else None,
    )


class TestDecisionRecordRoundTrip:
    def test_write_and_read_decision_record(self):
        container = MockCosmosContainer()
        record = _audit_record("hf-001")
        doc = record.model_dump(mode="json")
        doc["id"] = str(doc["id"])

        container.create_item(body=doc)
        retrieved = container.read_item(item=doc["id"], partition_key="live:inc-001")

        assert retrieved["handoff_id"] == "hf-001"
        assert retrieved["decision_type"] == "handoff_received"

    def test_multiple_records_stored(self):
        container = MockCosmosContainer()
        for i in range(5):
            record = _audit_record(f"hf-{i}")
            doc = record.model_dump(mode="json")
            doc["id"] = f"record-{i}"
            container.create_item(body=doc)

        items = container.query_items(query="SELECT * FROM c")
        assert len(items) == 5


# ---------------------------------------------------------------------------
# Audit writer with mock Cosmos
# ---------------------------------------------------------------------------


class TestAuditWriterWithMockCosmos:
    def test_audit_writes_to_cosmos_mock(self):
        from evacuation.audit import AuditWriter

        container = MockCosmosContainer()
        writer = AuditWriter(cosmos_client=container)

        record = _audit_record("hf-audit", DecisionType.plan_generated)
        writer.write(record)

        assert len(container._store) == 1
        assert writer.get_status() == "healthy"

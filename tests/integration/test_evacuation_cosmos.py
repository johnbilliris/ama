"""Integration tests for evacuation Cosmos DB operations (T054).

Uses mocks — does not require actual Cosmos DB connection.
"""

import pytest
from evacuation.models import (
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPlan,
    HazardSummary,
    Traceability,
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
        plan = EvacuationPlan(
            plan_id="ep-inc-001-v1",
            incident_id="inc-001",
            confidence_score=0.85,
            hazard_summary=HazardSummary(hazard_type="bushfire"),
            traceability=Traceability(source_handoff_id="hf-001"),
            summary="Test plan",
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


class TestDecisionRecordRoundTrip:
    def test_write_and_read_decision_record(self):
        container = MockCosmosContainer()
        record = EvacuationDecisionRecord(
            handoff_id="hf-001",
            decision_type=DecisionType.handoff_received,
            incident_id="inc-001",
            decision_rationale="Test rationale",
        )
        doc = record.model_dump(mode="json")
        doc["id"] = str(doc["id"])

        container.create_item(body=doc)
        retrieved = container.read_item(item=doc["id"], partition_key="live:inc-001")

        assert retrieved["handoff_id"] == "hf-001"
        assert retrieved["decision_type"] == "handoff_received"

    def test_multiple_records_stored(self):
        container = MockCosmosContainer()
        for i in range(5):
            record = EvacuationDecisionRecord(
                handoff_id=f"hf-{i}",
                decision_type=DecisionType.handoff_received,
            )
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

        record = EvacuationDecisionRecord(
            handoff_id="hf-audit",
            decision_type=DecisionType.plan_generated,
        )
        writer.write(record)

        assert len(container._store) == 1
        assert writer.get_status() == "healthy"

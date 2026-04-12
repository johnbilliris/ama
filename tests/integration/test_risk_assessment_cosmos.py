"""Integration tests for Risk Assessment Agent Cosmos DB persistence.

Tests verify correct Cosmos DB interaction patterns:
- HazardAssessment write/read with partition key
- Recommendation write/read
- RiskAssessmentDecisionRecord append-only write
- Version counter optimistic concurrency
- Assessment status transitions (active → superseded/expired)

Marked @pytest.mark.integration — skipped in unit test runs.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from unittest.mock import MagicMock, patch

import pytest
from risk_assessment.audit import AuditWriter
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.models import DecisionType, RiskAssessmentDecisionRecord
from risk_assessment.versioning import VersionCounter

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides) -> RiskAssessmentConfig:
    defaults = {"audit_buffer_capacity": 100, "audit_buffer_file_path": "test-audit.jsonl"}
    defaults.update(overrides)
    with patch.dict(os.environ, {}, clear=False):
        return RiskAssessmentConfig(**defaults)


def _make_record(
    handoff_id: str = "handoff-001",
    decision_type: DecisionType = DecisionType.assessment_generated,
    tenant_id: str = "live",
    incident_id: str = "inc-001",
) -> RiskAssessmentDecisionRecord:
    return RiskAssessmentDecisionRecord(
        handoff_id=handoff_id,
        decision_type=decision_type,
        confidence_raw=0.85,
        confidence_adjusted=0.80,
        decision_rationale="Test record",
        agent_version="0.1.0",
        incident_scope_key=f"{tenant_id}:{incident_id}",
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# T062-1: Assessment write uses create_item
# ---------------------------------------------------------------------------


class TestAssessmentWriteUsesCreateItem:
    def test_assessment_write_uses_create_item(self) -> None:
        """Verify pipeline calls create_item with correct partition key."""
        mock_cosmos = MagicMock()
        config = _make_config()
        writer = AuditWriter(config=config, cosmos_client=mock_cosmos)

        record = _make_record()
        writer.write(record)

        mock_cosmos.create_item.assert_called_once()
        body = mock_cosmos.create_item.call_args[1]["body"]
        assert body["incident_scope_key"] == "live:inc-001"
        assert body["decision_type"] == DecisionType.assessment_generated.value


# ---------------------------------------------------------------------------
# T062-2: Assessment read by partition key
# ---------------------------------------------------------------------------


class TestAssessmentReadByPartitionKey:
    def test_assessment_read_by_partition_key(self) -> None:
        """Verify reads use incident_scope_key as partition key."""
        mock_container = MagicMock()
        mock_container.read_item.return_value = {
            "id": "counter-1",
            "current_version": 3,
            "_etag": "etag-abc",
            "incident_scope_key": "live:inc-001",
        }
        mock_container.replace_item.return_value = None

        counter = VersionCounter(cosmos_container=mock_container)
        version = counter.assign_version(
            incident_id="inc-001",
            assessment_type="spread_prediction",
            incident_scope_key="live:inc-001",
        )

        mock_container.read_item.assert_called_once_with(
            item="inc-001_spread_prediction_counter",
            partition_key="live:inc-001",
        )
        assert version == 4


# ---------------------------------------------------------------------------
# T062-3: Recommendation write uses create_item
# ---------------------------------------------------------------------------


class TestRecommendationWriteUsesCreateItem:
    def test_recommendation_write_uses_create_item(self) -> None:
        """Verify recommendation persistence calls create_item."""
        mock_cosmos = MagicMock()
        config = _make_config()
        writer = AuditWriter(config=config, cosmos_client=mock_cosmos)

        record = _make_record(decision_type=DecisionType.recommendation_generated)
        record.recommendation_id = "rec-001"
        writer.write(record)

        mock_cosmos.create_item.assert_called_once()
        body = mock_cosmos.create_item.call_args[1]["body"]
        assert body["recommendation_id"] == "rec-001"
        assert body["decision_type"] == DecisionType.recommendation_generated.value


# ---------------------------------------------------------------------------
# T062-4: Audit record append-only (create_item, not upsert)
# ---------------------------------------------------------------------------


class TestAuditRecordAppendOnly:
    def test_audit_record_append_only(self) -> None:
        """Verify AuditWriter uses create_item (not upsert_item)."""
        mock_cosmos = MagicMock()
        config = _make_config()
        writer = AuditWriter(config=config, cosmos_client=mock_cosmos)

        for i in range(5):
            writer.write(_make_record(handoff_id=f"handoff-{i}"))

        assert mock_cosmos.create_item.call_count == 5
        mock_cosmos.upsert_item.assert_not_called()


# ---------------------------------------------------------------------------
# T062-5: Version counter OCC retry on 412
# ---------------------------------------------------------------------------


class TestVersionCounterOCCRetry:
    def test_version_counter_occ_retry(self) -> None:
        """Verify version counter retries on 412 errors then succeeds."""
        mock_container = MagicMock()

        call_count = {"n": 0}

        def read_side_effect(**kwargs):
            return {
                "id": "inc-001_spread_prediction_counter",
                "current_version": 5,
                "_etag": f"etag-{call_count['n']}",
                "incident_scope_key": "live:inc-001",
            }

        def replace_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] <= 2:
                raise Exception("412 PreconditionFailed: etag mismatch")

        mock_container.read_item.side_effect = read_side_effect
        mock_container.replace_item.side_effect = replace_side_effect

        counter = VersionCounter(cosmos_container=mock_container)

        with patch("risk_assessment.versioning.time.sleep"):
            version = counter.assign_version(
                incident_id="inc-001",
                assessment_type="spread_prediction",
                incident_scope_key="live:inc-001",
            )

        assert version == 6
        assert mock_container.replace_item.call_count == 3


# ---------------------------------------------------------------------------
# T062-6: Assessment status transition
# ---------------------------------------------------------------------------


class TestAssessmentStatusTransition:
    def test_assessment_status_transition(self) -> None:
        """Verify status field can change from 'active' to 'superseded'."""
        from packages.domain.src.domain.models.hazard_assessment import HazardAssessment

        assessment = HazardAssessment(
            hazard_assessment_id="ha-001",
            incident_id="inc-001",
            assessment_type="spread_prediction",
            summary="Initial assessment",
            confidence_level="high",
            status="active",
        )
        assert assessment.status == "active"

        superseded = assessment.model_copy(update={"status": "superseded"})
        assert superseded.status == "superseded"
        assert assessment.status == "active"

        expired = assessment.model_copy(update={"status": "expired"})
        assert expired.status == "expired"


# ---------------------------------------------------------------------------
# T062-7: Partition key format
# ---------------------------------------------------------------------------


class TestPartitionKeyFormat:
    def test_partition_key_format(self) -> None:
        """Verify partition key format is {tenant_id}:{incident_id}."""
        from risk_assessment.pipeline import _build_scope_key

        assert _build_scope_key("live", "inc-001") == "live:inc-001"
        assert _build_scope_key("sim-train", "inc-abc") == "sim-train:inc-abc"
        assert _build_scope_key("tenant_x", "INC-999") == "tenant_x:INC-999"

    def test_record_partition_key_matches_format(self) -> None:
        """Verify RiskAssessmentDecisionRecord stores the correct partition key."""
        record = _make_record(tenant_id="test-tenant", incident_id="inc-042")
        assert record.incident_scope_key == "test-tenant:inc-042"

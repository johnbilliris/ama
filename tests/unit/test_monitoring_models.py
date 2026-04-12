"""Unit tests for monitoring agent models, enums, and config (Phase 1: T002–T008)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


class TestDecisionType:
    """T002: DecisionType enum has all 9 values."""

    def test_all_nine_values_exist(self) -> None:
        from monitoring.models import DecisionType

        expected = {
            "summarised", "escalated", "blocked", "handed_off",
            "held_for_review", "associated", "degradation_detected",
            "discarded", "validation_failed",
        }
        actual = {dt.value for dt in DecisionType}
        assert actual == expected

    def test_string_enum_values(self) -> None:
        from monitoring.models import DecisionType

        assert DecisionType.summarised == "summarised"
        assert DecisionType.blocked.value == "blocked"


class TestFreshnessAndSourceEnums:
    """T003: FreshnessStatus and SourceType enums."""

    def test_freshness_status_values(self) -> None:
        from monitoring.models import FreshnessStatus

        assert {fs.value for fs in FreshnessStatus} == {"healthy", "degraded", "offline"}

    def test_source_type_values(self) -> None:
        from monitoring.models import SourceType

        assert {st.value for st in SourceType} == {"authoritative", "iot", "social"}


class TestMonitoringDecisionRecord:
    """T004: MonitoringDecisionRecord Pydantic model."""

    def test_create_with_required_fields(self) -> None:
        from monitoring.models import DecisionType, MonitoringDecisionRecord

        record = MonitoringDecisionRecord(
            signal_id="sig-001",
            decision=DecisionType.summarised,
            confidence=0.85,
            reasoning_summary="Test summary",
        )
        assert record.signal_id == "sig-001"
        assert record.decision == DecisionType.summarised
        assert record.confidence == 0.85
        assert record.id  # auto-generated UUID
        assert record.timestamp  # auto-generated
        assert record.tenant_id == "live"
        assert record.agent_version == "0.1.0"

    def test_optional_fields_default_to_none(self) -> None:
        from monitoring.models import DecisionType, MonitoringDecisionRecord

        record = MonitoringDecisionRecord(
            signal_id="sig-002",
            decision=DecisionType.escalated,
            confidence=0.9,
        )
        assert record.effective_confidence is None
        assert record.freshness_score is None
        assert record.llm_classification is None
        assert record.content_safety_result is None
        assert record.buffered_at is None
        assert record.flush_source is None

    def test_all_fields_populated(self) -> None:
        from monitoring.models import DecisionType, MonitoringDecisionRecord

        now = datetime.now(UTC)
        record = MonitoringDecisionRecord(
            signal_id="sig-003",
            decision=DecisionType.blocked,
            confidence=0.7,
            effective_confidence=0.63,
            freshness_score=0.9,
            inputs={"category": "fire"},
            output={"blocked": True},
            agent_version="0.2.0",
            reasoning_summary="Misinformation detected",
            llm_classification="misinformation",
            content_safety_result="not_checked",
            incident_scope_key="live:INC-042",
            tenant_id="live",
            timestamp=now,
            buffered_at=now,
            flush_source="memory_buffer",
        )
        assert record.effective_confidence == 0.63
        assert record.flush_source == "memory_buffer"


class TestDataFreshnessIndicator:
    """T005: DataFreshnessIndicator Pydantic model."""

    def test_create_with_defaults(self) -> None:
        from monitoring.models import DataFreshnessIndicator, SourceType

        indicator = DataFreshnessIndicator(
            data_source_id="bom-weather-nsw",
            source_type=SourceType.authoritative,
        )
        assert indicator.data_source_id == "bom-weather-nsw"
        assert indicator.source_type == SourceType.authoritative
        assert indicator.current_freshness_score == 1.0
        assert indicator.staleness_threshold_minutes == 15
        assert indicator.status.value == "healthy"

    def test_create_iot_source(self) -> None:
        from monitoring.models import DataFreshnessIndicator, FreshnessStatus, SourceType

        indicator = DataFreshnessIndicator(
            data_source_id="sensor-001",
            source_type=SourceType.iot,
            staleness_threshold_minutes=5,
            current_freshness_score=0.95,
            status=FreshnessStatus.healthy,
        )
        assert indicator.staleness_threshold_minutes == 5


class TestAuditBufferEntry:
    """T006: AuditBufferEntry Pydantic model."""

    def test_create_buffer_entry(self) -> None:
        from monitoring.models import AuditBufferEntry, DecisionType, MonitoringDecisionRecord

        record = MonitoringDecisionRecord(
            signal_id="sig-buf",
            decision=DecisionType.summarised,
            confidence=0.8,
        )
        entry = AuditBufferEntry(record=record)
        assert entry.record.signal_id == "sig-buf"
        assert entry.retry_count == 0
        assert entry.last_retry_at is None
        assert entry.buffered_at  # auto-generated

    def test_increment_retry(self) -> None:
        from monitoring.models import AuditBufferEntry, DecisionType, MonitoringDecisionRecord

        record = MonitoringDecisionRecord(
            signal_id="sig-retry",
            decision=DecisionType.escalated,
            confidence=0.9,
        )
        entry = AuditBufferEntry(record=record, retry_count=3)
        assert entry.retry_count == 3


class TestMonitoringConfig:
    """T001: MonitoringConfig reads environment variables with defaults."""

    def test_defaults(self) -> None:
        from monitoring.config import MonitoringConfig

        config = MonitoringConfig()
        assert config.escalation_confidence_threshold == 0.8
        assert config.signal_dedup_window_minutes == 10
        assert config.retrospective_lookback_hours == 24
        assert config.staleness_threshold_authoritative_minutes == 15
        assert config.staleness_threshold_iot_minutes == 5
        assert config.staleness_threshold_social_minutes == 30
        assert config.llm_eval_timeout_seconds == 3.0
        assert config.suspicious_confidence_penalty == 0.15
        assert config.audit_buffer_capacity == 10000
        assert config.max_reasoning_summary_length == 500
        assert config.agent_version == "0.1.0"

    def test_env_override(self, monkeypatch) -> None:
        from monitoring.config import MonitoringConfig

        monkeypatch.setenv("ESCALATION_CONFIDENCE_THRESHOLD", "0.75")
        monkeypatch.setenv("SIGNAL_DEDUP_WINDOW_MINUTES", "5")
        monkeypatch.setenv("AGENT_VERSION", "1.0.0")

        config = MonitoringConfig()
        assert config.escalation_confidence_threshold == 0.75
        assert config.signal_dedup_window_minutes == 5
        assert config.agent_version == "1.0.0"

    def test_staleness_threshold_for(self) -> None:
        from monitoring.config import MonitoringConfig

        config = MonitoringConfig()
        assert config.staleness_threshold_for("authoritative") == 15
        assert config.staleness_threshold_for("iot") == 5
        assert config.staleness_threshold_for("social") == 30
        assert config.staleness_threshold_for("unknown") == 30  # default to social


class TestSignalEnvelopeValidation:
    """T007: SignalEnvelope field validators."""

    def _make_valid_signal(self) -> dict:
        return {
            "source": {"dataSourceId": "bom-nsw", "name": "BoM NSW", "kind": "authoritative"},
            "category": "fire",
            "occurredAt": "2026-01-01T00:00:00Z",
            "receivedAt": "2026-01-01T00:00:01Z",
            "location": {"type": "Point", "coordinates": [151.2, -33.8]},
            "confidenceScore": 0.85,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
        }

    def test_valid_signal_passes(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        envelope = SignalEnvelope.model_validate(data)
        assert envelope.category == "fire"
        assert envelope.confidenceScore == 0.85

    def test_empty_category_rejected(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        data["category"] = ""
        with pytest.raises(ValidationError, match="category must be non-empty"):
            SignalEnvelope.model_validate(data)

    def test_confidence_below_zero_rejected(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        data["confidenceScore"] = -0.1
        with pytest.raises(ValidationError, match="confidenceScore must be in range"):
            SignalEnvelope.model_validate(data)

    def test_confidence_above_one_rejected(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        data["confidenceScore"] = 1.1
        with pytest.raises(ValidationError, match="confidenceScore must be in range"):
            SignalEnvelope.model_validate(data)

    def test_freshness_out_of_range_rejected(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        data["freshnessScore"] = 2.0
        with pytest.raises(ValidationError, match="freshnessScore must be in range"):
            SignalEnvelope.model_validate(data)

    def test_empty_data_source_id_rejected(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        data["source"]["dataSourceId"] = "  "
        with pytest.raises(ValidationError, match="dataSourceId must be non-empty"):
            SignalEnvelope.model_validate(data)

    def test_empty_kind_rejected(self) -> None:
        from app.validators.signal_envelope import SignalEnvelope

        data = self._make_valid_signal()
        data["source"]["kind"] = ""
        with pytest.raises(ValidationError, match="kind must be non-empty"):
            SignalEnvelope.model_validate(data)

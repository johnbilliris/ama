"""Reproducibility tests — deterministic outputs for identical inputs."""

import pytest
from communication.config import CommunicationConfig
from communication.models import CommunicationDecisionRecord, CommunicationDecisionType
from communication.versioning import VersionCounter


class TestReproducibility:
    """Verify same inputs produce deterministic outputs (T057)."""

    @pytest.mark.asyncio
    async def test_same_inputs_produce_same_alert_id(self):
        """Two calls with the same incident_id produce sequential but predictable IDs."""
        counter = VersionCounter()
        v1 = await counter.assign_version("INC-001", "live")
        id1 = counter.format_alert_id("INC-001", v1)

        counter2 = VersionCounter()
        v2 = await counter2.assign_version("INC-001", "live")
        id2 = counter2.format_alert_id("INC-001", v2)

        assert id1 == "ca-INC-001-v1"
        assert id2 == "ca-INC-001-v1"

    def test_format_alert_id_is_deterministic(self):
        counter = VersionCounter()
        assert counter.format_alert_id("INC-X", 3) == "ca-INC-X-v3"
        assert counter.format_alert_id("INC-X", 3) == "ca-INC-X-v3"

    def test_decision_record_captures_config_version(self):
        config = CommunicationConfig()
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.alert_drafted,
            correlation_id="alert-1",
            tenant_id="live",
            config_version=config.compute_config_hash(),
        )
        assert record.config_version != ""
        assert len(record.config_version) == 64  # SHA-256 hex

    def test_config_hash_deterministic_for_same_config(self):
        cfg1 = CommunicationConfig()
        cfg2 = CommunicationConfig()
        assert cfg1.compute_config_hash() == cfg2.compute_config_hash()

    def test_config_hash_changes_with_different_config(self):
        """Config hash differs when a parameter changes."""
        cfg_default = CommunicationConfig()

        # Override via object construction (frozen dataclass requires new instance)
        import os

        original = os.environ.get("SMS_MAX_LENGTH")
        os.environ["SMS_MAX_LENGTH"] = "999"
        try:
            cfg_modified = CommunicationConfig()
            assert cfg_default.compute_config_hash() != cfg_modified.compute_config_hash()
        finally:
            if original is None:
                os.environ.pop("SMS_MAX_LENGTH", None)
            else:
                os.environ["SMS_MAX_LENGTH"] = original

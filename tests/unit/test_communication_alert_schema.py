"""Contract tests — PublicAlert output schema validation."""

import re

import pytest
from communication.models import (
    AlertStatus,
    ContentBlock,
    GenerationMethod,
    PublicAlert,
)
from pydantic import ValidationError


class TestPublicAlertSchema:
    """Verify PublicAlert JSON schema matches the published contract."""

    def _make_alert(self, **overrides) -> PublicAlert:
        defaults = {
            "alert_id": "ca-INC-2025-001-v1",
            "incident_id": "INC-2025-001",
            "version": 1,
            "tenant_id": "live",
            "status": AlertStatus.drafting,
            "content_blocks": {
                "en-AU": ContentBlock(
                    language_code="en-AU",
                    title="Cyclone Warning",
                    body="A severe cyclone is approaching the coast.",
                    action_items="Evacuate immediately.",
                    generation_method=GenerationMethod.llm,
                ),
            },
            "confidence": 0.92,
        }
        defaults.update(overrides)
        return PublicAlert(**defaults)

    def test_alert_id_format_regex(self):
        """alert_id must match ^ca-[a-zA-Z0-9_-]+-v\\d+$."""
        alert = self._make_alert()
        assert re.match(r"^ca-[a-zA-Z0-9_-]+-v\d+$", alert.alert_id)

    def test_invalid_alert_id_rejected(self):
        with pytest.raises(ValidationError):
            self._make_alert(alert_id="bad-format")

    def test_required_fields_in_serialized_output(self):
        alert = self._make_alert()
        data = alert.model_dump(mode="json")
        required = [
            "alert_id",
            "incident_id",
            "version",
            "status",
            "content_blocks",
            "confidence",
        ]
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_content_blocks_must_have_en_au(self):
        """content_blocks must contain 'en-AU' key per model validator."""
        with pytest.raises(ValidationError, match="en-AU"):
            self._make_alert(
                content_blocks={
                    "zh-Hans": ContentBlock(
                        language_code="zh-Hans",
                        title="警告",
                        body="台风来了",
                        action_items="撤离",
                    ),
                }
            )

    def test_version_at_least_one(self):
        with pytest.raises(ValidationError):
            self._make_alert(version=0)

    def test_confidence_between_zero_and_one(self):
        alert_low = self._make_alert(confidence=0.0)
        assert alert_low.confidence == 0.0

        alert_high = self._make_alert(confidence=1.0)
        assert alert_high.confidence == 1.0

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            self._make_alert(confidence=1.5)

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            self._make_alert(confidence=-0.5)

    def test_serialized_output_json_roundtrip(self):
        alert = self._make_alert()
        data = alert.model_dump(mode="json")
        restored = PublicAlert(**data)
        assert restored.alert_id == alert.alert_id
        assert restored.version == alert.version

"""Tests for content safety 3-layer validation pipeline (T046-T050).

Covers:
- Azure AI integration with circuit breaker
- Keyword fallback when circuit is open
- Factual consistency validation
- Tone-level alignment (Australian Warning System)
- Circuit breaker state transitions
- review_flag on fallback results
"""

from __future__ import annotations

import pytest
from common.content_safety import ContentSafetyValidator
from common.content_safety_circuit_breaker import ContentSafetyCircuitBreaker


class TestContentSafetyCircuitBreaker:
    """Tests for ContentSafetyCircuitBreaker state machine."""

    def test_starts_closed(self):
        cb = ContentSafetyCircuitBreaker()
        assert cb.state == "closed"
        assert not cb.is_open

    def test_trips_after_threshold_failures(self):
        cb = ContentSafetyCircuitBreaker(trip_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.is_open

    def test_half_open_after_cooldown(self):
        counter = [0.0]

        def mock_clock():
            return counter[0]

        cb = ContentSafetyCircuitBreaker(
            trip_threshold=1, cooldown_seconds=10.0, clock=mock_clock,
        )
        cb.record_failure()
        assert cb.state == "open"

        # Advance past cooldown
        counter[0] = 15.0
        assert not cb.is_open  # Should transition to half_open
        assert cb.state == "half_open"

    def test_success_in_half_open_closes_circuit(self):
        counter = [0.0]

        def mock_clock():
            return counter[0]

        cb = ContentSafetyCircuitBreaker(
            trip_threshold=1, cooldown_seconds=5.0, clock=mock_clock,
        )
        cb.record_failure()
        counter[0] = 10.0
        _ = cb.is_open  # Transition to half_open
        cb.record_success()
        assert cb.state == "closed"

    def test_fallback_usage_tracking(self):
        cb = ContentSafetyCircuitBreaker()
        cb.record_fallback_usage()
        cb.record_fallback_usage()
        assert cb.fallback_message_count == 2


class TestContentSafetyValidator:
    """Tests for the 3-layer validation pipeline."""

    @pytest.fixture
    def validator(self):
        return ContentSafetyValidator(azure_client=None)

    def test_empty_text_fails(self, validator):
        result = validator.validate(text="")
        assert not result.passed
        assert result.reason == "empty_output"

    def test_length_exceeded_fails(self, validator):
        result = validator.validate(text="x" * 1300, max_length=1200)
        assert not result.passed
        assert result.reason == "length_exceeded"

    def test_blocked_keyword_fails(self, validator):
        result = validator.validate(text="This contains terror word")
        assert not result.passed
        assert result.reason == "blocked_keyword"
        assert result.review_flag is True

    def test_clean_text_passes_with_fallback(self, validator):
        """Without Azure client, falls back to keyword check."""
        result = validator.validate(text="Normal alert about bushfire conditions")
        assert result.passed
        assert result.validation_method == "keyword_fallback"
        assert result.review_flag is True

    def test_language_mismatch_fails(self, validator):
        result = validator.validate(
            text="这是中文", expected_language="en-AU",
        )
        assert not result.passed
        assert result.reason == "language_mismatch"


class TestFactualConsistency:
    """Tests for factual consistency validation (FR-007b)."""

    @pytest.fixture
    def validator(self):
        return ContentSafetyValidator(azure_client=None)

    def test_matching_content_passes(self, validator):
        result = validator.validate_factual(
            alert_message="Bushfire warning for Sydney area, severity level 4",
            originating_signal={
                "hazard_type": "bushfire",
                "severity_level": "4",
                "location_name": "Sydney",
            },
        )
        assert result.passed
        assert result.validation_method == "factual"

    def test_missing_hazard_type_fails(self, validator):
        result = validator.validate_factual(
            alert_message="Warning for Sydney area",
            originating_signal={
                "hazard_type": "bushfire",
                "severity_level": "3",
                "location_name": "Sydney",
            },
        )
        assert not result.passed
        assert "hazard_type" in result.reason

    def test_missing_location_fails(self, validator):
        result = validator.validate_factual(
            alert_message="Bushfire warning, severity 3",
            originating_signal={
                "hazard_type": "bushfire",
                "severity_level": "3",
                "location_name": "Melbourne",
            },
        )
        assert not result.passed
        assert "location_name" in result.reason


class TestToneValidation:
    """Tests for tone-level alignment (FR-007c)."""

    @pytest.fixture
    def validator(self):
        return ContentSafetyValidator(azure_client=None)

    def test_advice_tier_with_calm_language_passes(self, validator):
        result = validator.validate_tone(
            alert_message="Please monitor conditions and stay informed.",
            warning_tier="Advice",
        )
        assert result.passed

    def test_advice_tier_with_emergency_language_fails(self, validator):
        result = validator.validate_tone(
            alert_message="Evacuate now! Immediate danger!",
            warning_tier="Advice",
        )
        assert not result.passed
        assert "emergency language" in result.reason.lower()

    def test_emergency_warning_tier_allows_all_language(self, validator):
        result = validator.validate_tone(
            alert_message="Evacuate immediately! Life-threatening conditions!",
            warning_tier="Emergency Warning",
        )
        assert result.passed

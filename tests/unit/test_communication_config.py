"""Tests for communication.config — CommunicationConfig dataclass and config hashing."""

import pytest
from communication.config import CommunicationConfig

# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestCommunicationConfigDefaults:
    def test_supported_languages_default(self, monkeypatch):
        monkeypatch.delenv("SUPPORTED_LANGUAGES", raising=False)
        cfg = CommunicationConfig()
        assert cfg.supported_languages == ["en-AU", "zh-Hans", "ar", "vi", "el", "it"]

    def test_back_translation_threshold_default(self, monkeypatch):
        monkeypatch.delenv("BACK_TRANSLATION_THRESHOLD", raising=False)
        cfg = CommunicationConfig()
        assert cfg.back_translation_threshold == 0.85

    def test_alert_max_tokens_default(self, monkeypatch):
        monkeypatch.delenv("ALERT_MAX_TOKENS", raising=False)
        cfg = CommunicationConfig()
        assert cfg.alert_max_tokens == 180

    def test_handoff_dedup_window_minutes_default(self, monkeypatch):
        monkeypatch.delenv("HANDOFF_DEDUP_WINDOW_MINUTES", raising=False)
        cfg = CommunicationConfig()
        assert cfg.handoff_dedup_window_minutes == 30

    def test_approval_escalation_timeout_default(self, monkeypatch):
        monkeypatch.delenv("APPROVAL_ESCALATION_TIMEOUT_MINUTES", raising=False)
        cfg = CommunicationConfig()
        assert cfg.approval_escalation_timeout_minutes == 15

    def test_max_escalation_levels_default(self, monkeypatch):
        monkeypatch.delenv("MAX_ESCALATION_LEVELS", raising=False)
        cfg = CommunicationConfig()
        assert cfg.max_escalation_levels == 3

    def test_alert_expiry_hours_default(self, monkeypatch):
        monkeypatch.delenv("ALERT_EXPIRY_HOURS", raising=False)
        cfg = CommunicationConfig()
        assert cfg.alert_expiry_hours == 24

    def test_delivery_max_retries_default(self, monkeypatch):
        monkeypatch.delenv("DELIVERY_MAX_RETRIES", raising=False)
        cfg = CommunicationConfig()
        assert cfg.delivery_max_retries == 3

    def test_delivery_channels_default(self, monkeypatch):
        monkeypatch.delenv("DELIVERY_CHANNELS", raising=False)
        cfg = CommunicationConfig()
        assert cfg.delivery_channels == ["sms", "push", "emergency_broadcast"]

    def test_sms_max_length_default(self, monkeypatch):
        monkeypatch.delenv("SMS_MAX_LENGTH", raising=False)
        cfg = CommunicationConfig()
        assert cfg.sms_max_length == 612

    def test_audit_buffer_capacity_default(self, monkeypatch):
        monkeypatch.delenv("AUDIT_BUFFER_CAPACITY", raising=False)
        cfg = CommunicationConfig()
        assert cfg.audit_buffer_capacity == 10000

    def test_agent_version_default(self, monkeypatch):
        monkeypatch.delenv("AGENT_VERSION", raising=False)
        cfg = CommunicationConfig()
        assert cfg.agent_version == "0.1.0"

    def test_port_default(self, monkeypatch):
        monkeypatch.delenv("PORT", raising=False)
        cfg = CommunicationConfig()
        assert cfg.port == 8084

    def test_confidence_base_default(self, monkeypatch):
        monkeypatch.delenv("CONFIDENCE_BASE", raising=False)
        cfg = CommunicationConfig()
        assert cfg.confidence_base == 1.0

    def test_freshness_penalty_factor_default(self, monkeypatch):
        monkeypatch.delenv("FRESHNESS_PENALTY_FACTOR", raising=False)
        cfg = CommunicationConfig()
        assert cfg.freshness_penalty_factor == 0.9

    def test_back_translation_penalty_factor_default(self, monkeypatch):
        monkeypatch.delenv("BACK_TRANSLATION_PENALTY_FACTOR", raising=False)
        cfg = CommunicationConfig()
        assert cfg.back_translation_penalty_factor == 0.9

    def test_fallback_reduction_factor_default(self, monkeypatch):
        monkeypatch.delenv("FALLBACK_REDUCTION_FACTOR", raising=False)
        cfg = CommunicationConfig()
        assert cfg.fallback_reduction_factor == 0.8


# ---------------------------------------------------------------------------
# Environment variable overrides
# ---------------------------------------------------------------------------


class TestCommunicationConfigEnvOverrides:
    def test_supported_languages_override(self, monkeypatch):
        monkeypatch.setenv("SUPPORTED_LANGUAGES", "en-AU,zh-Hans")
        cfg = CommunicationConfig()
        assert cfg.supported_languages == ["en-AU", "zh-Hans"]

    def test_delivery_channels_override(self, monkeypatch):
        monkeypatch.setenv("DELIVERY_CHANNELS", "sms,push")
        cfg = CommunicationConfig()
        assert cfg.delivery_channels == ["sms", "push"]

    def test_back_translation_threshold_override(self, monkeypatch):
        monkeypatch.setenv("BACK_TRANSLATION_THRESHOLD", "0.90")
        cfg = CommunicationConfig()
        assert cfg.back_translation_threshold == 0.90

    def test_alert_max_tokens_override(self, monkeypatch):
        monkeypatch.setenv("ALERT_MAX_TOKENS", "256")
        cfg = CommunicationConfig()
        assert cfg.alert_max_tokens == 256

    def test_port_override(self, monkeypatch):
        monkeypatch.setenv("PORT", "9000")
        cfg = CommunicationConfig()
        assert cfg.port == 9000

    def test_agent_version_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_VERSION", "1.0.0")
        cfg = CommunicationConfig()
        assert cfg.agent_version == "1.0.0"


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------


class TestCSVParsing:
    def test_csv_with_spaces_stripped(self, monkeypatch):
        monkeypatch.setenv("SUPPORTED_LANGUAGES", " en-AU , zh-Hans , ar ")
        cfg = CommunicationConfig()
        assert cfg.supported_languages == ["en-AU", "zh-Hans", "ar"]

    def test_csv_empty_entries_removed(self, monkeypatch):
        monkeypatch.setenv("DELIVERY_CHANNELS", "sms,,push,")
        cfg = CommunicationConfig()
        assert cfg.delivery_channels == ["sms", "push"]

    def test_csv_single_value(self, monkeypatch):
        monkeypatch.setenv("SUPPORTED_LANGUAGES", "en-AU")
        cfg = CommunicationConfig()
        assert cfg.supported_languages == ["en-AU"]


# ---------------------------------------------------------------------------
# Type coercion
# ---------------------------------------------------------------------------


class TestTypeCoercion:
    def test_str_to_float_coercion(self, monkeypatch):
        monkeypatch.setenv("CONFIDENCE_BASE", "0.95")
        cfg = CommunicationConfig()
        assert isinstance(cfg.confidence_base, float)
        assert cfg.confidence_base == 0.95

    def test_str_to_int_coercion(self, monkeypatch):
        monkeypatch.setenv("AUDIT_BUFFER_CAPACITY", "5000")
        cfg = CommunicationConfig()
        assert isinstance(cfg.audit_buffer_capacity, int)
        assert cfg.audit_buffer_capacity == 5000


# ---------------------------------------------------------------------------
# compute_config_hash()
# ---------------------------------------------------------------------------


class TestConfigHash:
    def test_same_config_same_hash(self, monkeypatch):
        monkeypatch.delenv("SUPPORTED_LANGUAGES", raising=False)
        monkeypatch.delenv("BACK_TRANSLATION_THRESHOLD", raising=False)
        cfg1 = CommunicationConfig()
        cfg2 = CommunicationConfig()
        assert cfg1.compute_config_hash() == cfg2.compute_config_hash()

    def test_different_config_different_hash(self, monkeypatch):
        monkeypatch.setenv("ALERT_MAX_TOKENS", "180")
        cfg1 = CommunicationConfig()
        monkeypatch.setenv("ALERT_MAX_TOKENS", "256")
        cfg2 = CommunicationConfig()
        assert cfg1.compute_config_hash() != cfg2.compute_config_hash()

    def test_hash_is_hex_string(self, monkeypatch):
        monkeypatch.delenv("SUPPORTED_LANGUAGES", raising=False)
        cfg = CommunicationConfig()
        h = cfg.compute_config_hash()
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest
        int(h, 16)  # Should not raise

    def test_frozen_config_is_immutable(self, monkeypatch):
        monkeypatch.delenv("SUPPORTED_LANGUAGES", raising=False)
        cfg = CommunicationConfig()
        with pytest.raises(Exception):
            cfg.port = 9999

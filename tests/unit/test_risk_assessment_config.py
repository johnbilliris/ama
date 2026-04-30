"""Tests for risk_assessment.config – defaults, env overrides, helpers."""

from risk_assessment.config import RiskAssessmentConfig

# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestConfigDefaults:
    def test_source_weight_authoritative(self):
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_authoritative == 2.0

    def test_source_weight_iot(self):
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_iot == 1.0

    def test_source_weight_social(self):
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_social == 0.5

    def test_stale_signal_threshold(self):
        cfg = RiskAssessmentConfig()
        assert cfg.stale_signal_threshold == 0.5

    def test_handoff_dedup_window_minutes(self):
        cfg = RiskAssessmentConfig()
        assert cfg.handoff_dedup_window_minutes == 10

    def test_assessment_validity_hours_default(self):
        cfg = RiskAssessmentConfig()
        assert cfg.assessment_validity_hours_default == 4

    def test_assessment_validity_hours_fire(self):
        cfg = RiskAssessmentConfig()
        assert cfg.assessment_validity_hours_fire == 2

    def test_assessment_validity_hours_cyclone(self):
        cfg = RiskAssessmentConfig()
        assert cfg.assessment_validity_hours_cyclone == 6

    def test_contradiction_reduction_factor(self):
        cfg = RiskAssessmentConfig()
        assert cfg.contradiction_reduction_factor == 0.7

    def test_escalation_threshold_communication(self):
        cfg = RiskAssessmentConfig()
        assert cfg.escalation_threshold_communication == 0.7

    def test_escalation_threshold_evacuation(self):
        cfg = RiskAssessmentConfig()
        assert cfg.escalation_threshold_evacuation == 0.6

    def test_audit_buffer_capacity(self):
        cfg = RiskAssessmentConfig()
        assert cfg.audit_buffer_capacity == 10_000

    def test_max_reasoning_summary_length(self):
        cfg = RiskAssessmentConfig()
        assert cfg.max_reasoning_summary_length == 500

    def test_agent_version(self):
        cfg = RiskAssessmentConfig()
        assert cfg.agent_version == "0.1.0"


# ---------------------------------------------------------------------------
# Environment variable overrides
# ---------------------------------------------------------------------------


class TestConfigEnvOverrides:
    def test_source_weight_authoritative_override(self, monkeypatch):
        monkeypatch.setenv("SOURCE_WEIGHT_AUTHORITATIVE", "3.0")
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_authoritative == 3.0

    def test_source_weight_iot_override(self, monkeypatch):
        monkeypatch.setenv("SOURCE_WEIGHT_IOT", "1.5")
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_iot == 1.5

    def test_source_weight_social_override(self, monkeypatch):
        monkeypatch.setenv("SOURCE_WEIGHT_SOCIAL", "0.8")
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_social == 0.8

    def test_handoff_dedup_window_override(self, monkeypatch):
        monkeypatch.setenv("HANDOFF_DEDUP_WINDOW_MINUTES", "20")
        cfg = RiskAssessmentConfig()
        assert cfg.handoff_dedup_window_minutes == 20

    def test_type_coercion_float(self, monkeypatch):
        monkeypatch.setenv("SOURCE_WEIGHT_AUTHORITATIVE", "2.5")
        cfg = RiskAssessmentConfig()
        assert isinstance(cfg.source_weight_authoritative, float)

    def test_type_coercion_int(self, monkeypatch):
        monkeypatch.setenv("HANDOFF_DEDUP_WINDOW_MINUTES", "15")
        cfg = RiskAssessmentConfig()
        assert isinstance(cfg.handoff_dedup_window_minutes, int)


# ---------------------------------------------------------------------------
# source_weight_for()
# ---------------------------------------------------------------------------


class TestSourceWeightFor:
    def test_authoritative(self):
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_for("authoritative") == 2.0

    def test_iot(self):
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_for("iot") == 1.0

    def test_social(self):
        cfg = RiskAssessmentConfig()
        assert cfg.source_weight_for("social") == 0.5

    def test_unknown_kind_returns_social_weight(self):
        cfg = RiskAssessmentConfig()
        result = cfg.source_weight_for("unknown_sensor")
        assert result == cfg.source_weight_social


# ---------------------------------------------------------------------------
# validity_hours_for()
# ---------------------------------------------------------------------------


class TestValidityHoursFor:
    def test_fire(self):
        cfg = RiskAssessmentConfig()
        assert cfg.validity_hours_for("fire") == 2

    def test_cyclone(self):
        cfg = RiskAssessmentConfig()
        assert cfg.validity_hours_for("cyclone") == 6

    def test_default_category(self):
        cfg = RiskAssessmentConfig()
        assert cfg.validity_hours_for("flood") == 4

    def test_unknown_category(self):
        cfg = RiskAssessmentConfig()
        assert cfg.validity_hours_for("meteor") == 4


# ---------------------------------------------------------------------------
# compute_config_hash()
# ---------------------------------------------------------------------------


class TestComputeConfigHash:
    def test_deterministic(self):
        cfg = RiskAssessmentConfig()
        h1 = cfg.compute_config_hash()
        h2 = cfg.compute_config_hash()
        assert h1 == h2

    def test_hash_is_hex_string(self):
        cfg = RiskAssessmentConfig()
        h = cfg.compute_config_hash()
        assert isinstance(h, str)
        int(h, 16)  # should not raise

    def test_different_config_different_hash(self):
        cfg1 = RiskAssessmentConfig()
        cfg2 = RiskAssessmentConfig(source_weight_authoritative=5.0)
        assert cfg1.compute_config_hash() != cfg2.compute_config_hash()

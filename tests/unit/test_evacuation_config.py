"""Tests for evacuation.config — defaults, hash, mobilisation, env overrides (T013)."""

from evacuation.config import EvacuationConfig

# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestConfigDefaults:
    def test_road_network_file_path(self):
        cfg = EvacuationConfig()
        assert cfg.road_network_file_path == "data/road-network.json"

    def test_road_data_staleness_hours(self):
        cfg = EvacuationConfig()
        assert cfg.road_data_staleness_hours == 6

    def test_handoff_dedup_window_minutes(self):
        cfg = EvacuationConfig()
        assert cfg.handoff_dedup_window_minutes == 10

    def test_congestion_risk_threshold_pct(self):
        cfg = EvacuationConfig()
        assert cfg.congestion_risk_threshold_pct == 80

    def test_vulnerable_population_buffer(self):
        cfg = EvacuationConfig()
        assert cfg.vulnerable_population_buffer == 1.5

    def test_phase_transition_time_factor(self):
        cfg = EvacuationConfig()
        assert cfg.phase_transition_time_factor == 1.2

    def test_phase_transition_population_pct(self):
        cfg = EvacuationConfig()
        assert cfg.phase_transition_population_pct == 50

    def test_hazard_expansion_replan_pct(self):
        cfg = EvacuationConfig()
        assert cfg.hazard_expansion_replan_pct == 10

    def test_progress_delay_replan_pct(self):
        cfg = EvacuationConfig()
        assert cfg.progress_delay_replan_pct == 30

    def test_fallback_confidence_reduction(self):
        cfg = EvacuationConfig()
        assert cfg.fallback_confidence_reduction == 0.8

    def test_mobilisation_time_tsunami(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_tsunami_min == 30

    def test_mobilisation_time_flood(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_flood_min == 120

    def test_mobilisation_time_bushfire(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_bushfire_min == 60

    def test_mobilisation_time_cyclone(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_cyclone_min == 120

    def test_mobilisation_time_earthquake(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_earthquake_min == 30

    def test_audit_buffer_capacity(self):
        cfg = EvacuationConfig()
        assert cfg.audit_buffer_capacity == 10_000

    def test_max_summary_length(self):
        cfg = EvacuationConfig()
        assert cfg.max_summary_length == 1000

    def test_replan_rate_limit_seconds(self):
        cfg = EvacuationConfig()
        assert cfg.replan_rate_limit_seconds == 30

    def test_agent_version(self):
        cfg = EvacuationConfig()
        assert cfg.agent_version == "0.1.0"


# ---------------------------------------------------------------------------
# Config hash generation
# ---------------------------------------------------------------------------


class TestConfigHash:
    def test_hash_is_sha256_hex(self):
        cfg = EvacuationConfig()
        h = cfg.compute_config_hash()
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex length

    def test_same_config_same_hash(self):
        cfg1 = EvacuationConfig()
        cfg2 = EvacuationConfig()
        assert cfg1.compute_config_hash() == cfg2.compute_config_hash()

    def test_hash_deterministic(self):
        cfg = EvacuationConfig()
        h1 = cfg.compute_config_hash()
        h2 = cfg.compute_config_hash()
        assert h1 == h2


# ---------------------------------------------------------------------------
# mobilisation_time_for()
# ---------------------------------------------------------------------------


class TestMobilisationTimeFor:
    def test_tsunami(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_for("tsunami") == 30

    def test_flood(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_for("flood") == 120

    def test_bushfire(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_for("bushfire") == 60

    def test_cyclone(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_for("cyclone") == 120

    def test_earthquake(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_for("earthquake") == 30

    def test_unknown_falls_back_to_bushfire(self):
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_for("unknown_hazard") == 60  # bushfire default


# ---------------------------------------------------------------------------
# Custom env var overrides
# ---------------------------------------------------------------------------


class TestEnvOverrides:
    def test_road_data_staleness_override(self, monkeypatch):
        monkeypatch.setenv("ROAD_DATA_STALENESS_HOURS", "12")
        cfg = EvacuationConfig()
        assert cfg.road_data_staleness_hours == 12

    def test_handoff_dedup_window_override(self, monkeypatch):
        monkeypatch.setenv("HANDOFF_DEDUP_WINDOW_MINUTES", "5")
        cfg = EvacuationConfig()
        assert cfg.handoff_dedup_window_minutes == 5

    def test_congestion_risk_threshold_override(self, monkeypatch):
        monkeypatch.setenv("CONGESTION_RISK_THRESHOLD_PCT", "90")
        cfg = EvacuationConfig()
        assert cfg.congestion_risk_threshold_pct == 90

    def test_vulnerable_population_buffer_override(self, monkeypatch):
        monkeypatch.setenv("VULNERABLE_POPULATION_BUFFER", "2.0")
        cfg = EvacuationConfig()
        assert cfg.vulnerable_population_buffer == 2.0

    def test_replan_rate_limit_override(self, monkeypatch):
        monkeypatch.setenv("REPLAN_RATE_LIMIT_SECONDS", "60")
        cfg = EvacuationConfig()
        assert cfg.replan_rate_limit_seconds == 60

    def test_agent_version_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_VERSION", "1.2.3")
        cfg = EvacuationConfig()
        assert cfg.agent_version == "1.2.3"

    def test_road_network_file_path_override(self, monkeypatch):
        monkeypatch.setenv("ROAD_NETWORK_FILE_PATH", "/custom/path.json")
        cfg = EvacuationConfig()
        assert cfg.road_network_file_path == "/custom/path.json"

    def test_mobilisation_time_override(self, monkeypatch):
        monkeypatch.setenv("MOBILISATION_TIME_CYCLONE_MIN", "180")
        cfg = EvacuationConfig()
        assert cfg.mobilisation_time_cyclone_min == 180
        assert cfg.mobilisation_time_for("cyclone") == 180

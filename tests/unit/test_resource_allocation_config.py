"""Unit tests for Resource Allocation Agent configuration.

Covers:
- Default values for all parameters
- Environment variable overrides
- Type coercion (str→float, str→int)
- Config hash computation
- Helper methods
"""

from __future__ import annotations

import os
import pytest

from resource_allocation.config import ResourceAllocationConfig


class TestConfigDefaults:
    """Verify default values match data-model.md §Configurable Parameters."""

    def test_priority_weight_defaults(self):
        config = ResourceAllocationConfig()
        assert config.priority_weight_critical == 4.0
        assert config.priority_weight_high == 3.0
        assert config.priority_weight_moderate == 2.0
        assert config.priority_weight_low == 1.0

    def test_availability_factor_defaults(self):
        config = ResourceAllocationConfig()
        assert config.availability_available == 1.0
        assert config.availability_returning == 0.5

    def test_distance_floor_default(self):
        config = ResourceAllocationConfig()
        assert config.distance_floor_km == 0.1

    def test_travel_speed_defaults(self):
        config = ResourceAllocationConfig()
        assert config.travel_speed_personnel_kmh == 40.0
        assert config.travel_speed_vehicle_kmh == 60.0
        assert config.travel_speed_helicopter_kmh == 200.0

    def test_mobilisation_defaults(self):
        config = ResourceAllocationConfig()
        assert config.mobilisation_personnel_minutes == 15.0
        assert config.mobilisation_vehicle_minutes == 10.0
        assert config.mobilisation_helicopter_minutes == 5.0

    def test_plan_expiry_default(self):
        config = ResourceAllocationConfig()
        assert config.plan_expiry_hours == 4

    def test_confidence_defaults(self):
        config = ResourceAllocationConfig()
        assert config.confidence_base == 0.9
        assert config.fallback_reduction_factor == 0.8
        assert config.stale_data_reduction_factor == 0.8
        assert config.partial_data_reduction_factor == 0.7

    def test_operational_defaults(self):
        config = ResourceAllocationConfig()
        assert config.inventory_staleness_window_minutes == 30
        assert config.handoff_dedup_window_minutes == 10
        assert config.rotation_threshold_hours == 12.0
        assert config.replenishment_threshold_percent == 0.2

    def test_audit_defaults(self):
        config = ResourceAllocationConfig()
        assert config.audit_buffer_capacity == 10000
        assert config.audit_buffer_file_path == "resource_allocation_audit.jsonl"

    def test_versioning_default(self):
        config = ResourceAllocationConfig()
        assert config.version_conflict_max_retries == 3

    def test_agent_version_default(self):
        config = ResourceAllocationConfig()
        assert config.agent_version == "0.1.0"

    def test_port_default(self):
        config = ResourceAllocationConfig()
        assert config.port == 8083


class TestConfigEnvironmentOverrides:
    """Verify environment variable overrides."""

    def test_priority_weight_override(self, monkeypatch):
        monkeypatch.setenv("PRIORITY_WEIGHT_CRITICAL", "5.0")
        config = ResourceAllocationConfig()
        assert config.priority_weight_critical == 5.0

    def test_distance_floor_override(self, monkeypatch):
        monkeypatch.setenv("DISTANCE_FLOOR_KM", "0.5")
        config = ResourceAllocationConfig()
        assert config.distance_floor_km == 0.5

    def test_plan_expiry_override(self, monkeypatch):
        monkeypatch.setenv("PLAN_EXPIRY_HOURS", "8")
        config = ResourceAllocationConfig()
        assert config.plan_expiry_hours == 8

    def test_agent_version_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_VERSION", "1.2.3")
        config = ResourceAllocationConfig()
        assert config.agent_version == "1.2.3"


class TestConfigHelpers:
    """Verify helper methods."""

    def test_priority_weight_for(self):
        config = ResourceAllocationConfig()
        assert config.priority_weight_for("critical") == 4.0
        assert config.priority_weight_for("high") == 3.0
        assert config.priority_weight_for("moderate") == 2.0
        assert config.priority_weight_for("low") == 1.0
        assert config.priority_weight_for("unknown") == 1.0

    def test_availability_factor_for(self):
        config = ResourceAllocationConfig()
        assert config.availability_factor_for("available") == 1.0
        assert config.availability_factor_for("returning") == 0.5
        assert config.availability_factor_for("assigned") == 0.0
        assert config.availability_factor_for("deployed") == 0.0

    def test_travel_speed_for(self):
        config = ResourceAllocationConfig()
        assert config.travel_speed_for("vehicle") == 60.0
        assert config.travel_speed_for("personnel") == 40.0
        assert config.travel_speed_for("vehicle", "helicopter") == 200.0

    def test_mobilisation_minutes_for(self):
        config = ResourceAllocationConfig()
        assert config.mobilisation_minutes_for("vehicle") == 10.0
        assert config.mobilisation_minutes_for("personnel") == 15.0
        assert config.mobilisation_minutes_for("vehicle", "helicopter") == 5.0

    def test_config_hash_deterministic(self):
        config = ResourceAllocationConfig()
        hash1 = config.compute_config_hash()
        hash2 = config.compute_config_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_config_hash_changes_with_values(self, monkeypatch):
        config1 = ResourceAllocationConfig()
        hash1 = config1.compute_config_hash()

        monkeypatch.setenv("PRIORITY_WEIGHT_CRITICAL", "5.0")
        config2 = ResourceAllocationConfig()
        hash2 = config2.compute_config_hash()

        assert hash1 != hash2

"""Evacuation Agent configuration — reads all environment variables at startup.

All configurable parameters are consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvacuationConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # Road network
    road_network_file_path: str = field(
        default_factory=lambda: os.getenv("ROAD_NETWORK_FILE_PATH", "data/road-network.json")
    )
    road_data_staleness_hours: int = field(
        default_factory=lambda: int(os.getenv("ROAD_DATA_STALENESS_HOURS", "6"))
    )

    # Handoff deduplication
    handoff_dedup_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("HANDOFF_DEDUP_WINDOW_MINUTES", "10"))
    )

    # Congestion
    congestion_risk_threshold_pct: int = field(
        default_factory=lambda: int(os.getenv("CONGESTION_RISK_THRESHOLD_PCT", "80"))
    )

    # Vulnerable population
    vulnerable_population_buffer: float = field(
        default_factory=lambda: float(os.getenv("VULNERABLE_POPULATION_BUFFER", "1.5"))
    )

    # Phase transitions
    phase_transition_time_factor: float = field(
        default_factory=lambda: float(os.getenv("PHASE_TRANSITION_TIME_FACTOR", "1.2"))
    )
    phase_transition_population_pct: int = field(
        default_factory=lambda: int(os.getenv("PHASE_TRANSITION_POPULATION_PCT", "50"))
    )

    # Replanning thresholds
    hazard_expansion_replan_pct: int = field(
        default_factory=lambda: int(os.getenv("HAZARD_EXPANSION_REPLAN_PCT", "10"))
    )
    progress_delay_replan_pct: int = field(
        default_factory=lambda: int(os.getenv("PROGRESS_DELAY_REPLAN_PCT", "30"))
    )

    # Confidence
    fallback_confidence_reduction: float = field(
        default_factory=lambda: float(os.getenv("FALLBACK_CONFIDENCE_REDUCTION", "0.8"))
    )

    # Mobilisation times (minutes) per hazard type
    mobilisation_time_tsunami_min: int = field(
        default_factory=lambda: int(os.getenv("MOBILISATION_TIME_TSUNAMI_MIN", "30"))
    )
    mobilisation_time_flood_min: int = field(
        default_factory=lambda: int(os.getenv("MOBILISATION_TIME_FLOOD_MIN", "120"))
    )
    mobilisation_time_bushfire_min: int = field(
        default_factory=lambda: int(os.getenv("MOBILISATION_TIME_BUSHFIRE_MIN", "60"))
    )
    mobilisation_time_cyclone_min: int = field(
        default_factory=lambda: int(os.getenv("MOBILISATION_TIME_CYCLONE_MIN", "120"))
    )
    mobilisation_time_earthquake_min: int = field(
        default_factory=lambda: int(os.getenv("MOBILISATION_TIME_EARTHQUAKE_MIN", "30"))
    )

    # Audit
    audit_buffer_capacity: int = field(
        default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000"))
    )
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv(
            "AUDIT_BUFFER_FILE_PATH", "/var/log/evacuation-agent/audit-buffer.jsonl"
        )
    )

    # Summary
    max_summary_length: int = field(
        default_factory=lambda: int(os.getenv("MAX_SUMMARY_LENGTH", "1000"))
    )

    # Replanning rate limit
    replan_rate_limit_seconds: int = field(
        default_factory=lambda: int(os.getenv("REPLAN_RATE_LIMIT_SECONDS", "30"))
    )

    # Version
    agent_version: str = field(
        default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0")
    )

    # Azure service connection strings (optional — injected at runtime)
    azure_cosmos_endpoint: str = field(
        default_factory=lambda: os.getenv("AZURE_COSMOS_ENDPOINT", "")
    )
    azure_cosmos_key: str = field(
        default_factory=lambda: os.getenv("AZURE_COSMOS_KEY", "")
    )
    azure_servicebus_connection: str = field(
        default_factory=lambda: os.getenv("AZURE_SERVICEBUS_CONNECTION", "")
    )

    def mobilisation_time_for(self, hazard_type: str) -> int:
        """Return mobilisation time in minutes for a given hazard type."""
        mapping = {
            "tsunami": self.mobilisation_time_tsunami_min,
            "flood": self.mobilisation_time_flood_min,
            "bushfire": self.mobilisation_time_bushfire_min,
            "cyclone": self.mobilisation_time_cyclone_min,
            "earthquake": self.mobilisation_time_earthquake_min,
        }
        return mapping.get(hazard_type, self.mobilisation_time_bushfire_min)

    def compute_config_hash(self) -> str:
        """Produce a deterministic SHA-256 hash of all active configuration values."""
        config_str = (
            f"road_network_file_path={self.road_network_file_path};"
            f"road_data_staleness_hours={self.road_data_staleness_hours};"
            f"handoff_dedup_window_minutes={self.handoff_dedup_window_minutes};"
            f"congestion_risk_threshold_pct={self.congestion_risk_threshold_pct};"
            f"vulnerable_population_buffer={self.vulnerable_population_buffer};"
            f"phase_transition_time_factor={self.phase_transition_time_factor};"
            f"phase_transition_population_pct={self.phase_transition_population_pct};"
            f"hazard_expansion_replan_pct={self.hazard_expansion_replan_pct};"
            f"progress_delay_replan_pct={self.progress_delay_replan_pct};"
            f"fallback_confidence_reduction={self.fallback_confidence_reduction};"
            f"mobilisation_time_tsunami_min={self.mobilisation_time_tsunami_min};"
            f"mobilisation_time_flood_min={self.mobilisation_time_flood_min};"
            f"mobilisation_time_bushfire_min={self.mobilisation_time_bushfire_min};"
            f"mobilisation_time_cyclone_min={self.mobilisation_time_cyclone_min};"
            f"mobilisation_time_earthquake_min={self.mobilisation_time_earthquake_min};"
            f"audit_buffer_capacity={self.audit_buffer_capacity};"
            f"max_summary_length={self.max_summary_length};"
            f"replan_rate_limit_seconds={self.replan_rate_limit_seconds};"
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

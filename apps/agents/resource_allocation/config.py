"""Resource Allocation Agent configuration — reads all environment variables at startup.

All configurable parameters are consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResourceAllocationConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # -----------------------------------------------------------------------
    # Scoring: priority weights
    # -----------------------------------------------------------------------
    priority_weight_critical: float = field(default_factory=lambda: float(os.getenv("PRIORITY_WEIGHT_CRITICAL", "4.0")))
    priority_weight_high: float = field(default_factory=lambda: float(os.getenv("PRIORITY_WEIGHT_HIGH", "3.0")))
    priority_weight_moderate: float = field(default_factory=lambda: float(os.getenv("PRIORITY_WEIGHT_MODERATE", "2.0")))
    priority_weight_low: float = field(default_factory=lambda: float(os.getenv("PRIORITY_WEIGHT_LOW", "1.0")))

    # -----------------------------------------------------------------------
    # Scoring: availability factors
    # -----------------------------------------------------------------------
    availability_available: float = 1.0  # Fixed — not configurable
    availability_returning: float = field(default_factory=lambda: float(os.getenv("AVAILABILITY_RETURNING", "0.5")))

    # -----------------------------------------------------------------------
    # Scoring: distance
    # -----------------------------------------------------------------------
    distance_floor_km: float = field(default_factory=lambda: float(os.getenv("DISTANCE_FLOOR_KM", "0.1")))

    # -----------------------------------------------------------------------
    # Travel speeds (km/h) and mobilisation overheads (minutes)
    # -----------------------------------------------------------------------
    travel_speed_personnel_kmh: float = field(
        default_factory=lambda: float(os.getenv("TRAVEL_SPEED_PERSONNEL_KMH", "40"))
    )
    travel_speed_vehicle_kmh: float = field(default_factory=lambda: float(os.getenv("TRAVEL_SPEED_VEHICLE_KMH", "60")))
    travel_speed_helicopter_kmh: float = field(
        default_factory=lambda: float(os.getenv("TRAVEL_SPEED_HELICOPTER_KMH", "200"))
    )
    mobilisation_personnel_minutes: float = field(
        default_factory=lambda: float(os.getenv("MOBILISATION_PERSONNEL_MINUTES", "15"))
    )
    mobilisation_vehicle_minutes: float = field(
        default_factory=lambda: float(os.getenv("MOBILISATION_VEHICLE_MINUTES", "10"))
    )
    mobilisation_helicopter_minutes: float = field(
        default_factory=lambda: float(os.getenv("MOBILISATION_HELICOPTER_MINUTES", "5"))
    )

    # -----------------------------------------------------------------------
    # Plan lifecycle
    # -----------------------------------------------------------------------
    plan_expiry_hours: int = field(default_factory=lambda: int(os.getenv("PLAN_EXPIRY_HOURS", "4")))

    # -----------------------------------------------------------------------
    # Confidence
    # -----------------------------------------------------------------------
    confidence_base: float = field(default_factory=lambda: float(os.getenv("CONFIDENCE_BASE", "0.9")))
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("FALLBACK_REDUCTION_FACTOR", "0.8"))
    )
    stale_data_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("STALE_DATA_REDUCTION_FACTOR", "0.8"))
    )
    partial_data_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("PARTIAL_DATA_REDUCTION_FACTOR", "0.7"))
    )

    # -----------------------------------------------------------------------
    # Operational parameters
    # -----------------------------------------------------------------------
    inventory_staleness_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("INVENTORY_STALENESS_WINDOW_MINUTES", "30"))
    )
    handoff_dedup_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("HANDOFF_DEDUP_WINDOW_MINUTES", "10"))
    )
    rotation_threshold_hours: float = field(default_factory=lambda: float(os.getenv("ROTATION_THRESHOLD_HOURS", "12")))
    replenishment_threshold_percent: float = field(
        default_factory=lambda: float(os.getenv("REPLENISHMENT_THRESHOLD_PERCENT", "0.2"))
    )

    # -----------------------------------------------------------------------
    # Audit
    # -----------------------------------------------------------------------
    audit_buffer_capacity: int = field(default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000")))
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv("AUDIT_BUFFER_FILE_PATH", "resource_allocation_audit.jsonl")
    )

    # -----------------------------------------------------------------------
    # Versioning / OCC
    # -----------------------------------------------------------------------
    version_conflict_max_retries: int = field(
        default_factory=lambda: int(os.getenv("VERSION_CONFLICT_MAX_RETRIES", "3"))
    )

    # -----------------------------------------------------------------------
    # Agent metadata
    # -----------------------------------------------------------------------
    agent_version: str = field(default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8083")))

    # -----------------------------------------------------------------------
    # LLM Configuration
    # -----------------------------------------------------------------------
    llm_model_tier: str = field(default_factory=lambda: os.getenv("LLM_MODEL_TIER", "drafting"))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    llm_max_output_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000")))
    llm_confidence_threshold: float = field(default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7")))
    llm_fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5"))
    )
    llm_monthly_budget_usd: float = field(default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "50.0")))

    def __post_init__(self) -> None:
        """Validate LLM configuration values immediately after construction."""
        if self.llm_model_tier not in ("reasoning", "drafting"):
            raise ValueError(f"Invalid LLM_MODEL_TIER: {self.llm_model_tier}")
        if not (0.0 <= self.llm_temperature <= 2.0):
            raise ValueError(f"LLM_TEMPERATURE must be 0.0–2.0, got {self.llm_temperature}")
        if self.llm_max_output_tokens <= 0 or self.llm_max_output_tokens > 16384:
            raise ValueError(f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.llm_max_output_tokens}")
        if not (0.0 <= self.llm_confidence_threshold <= 1.0):
            raise ValueError(f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.llm_confidence_threshold}")
        if not (0.0 <= self.llm_fallback_reduction_factor <= 1.0):
            raise ValueError(f"LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, got {self.llm_fallback_reduction_factor}")

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def priority_weight_for(self, urgency: str) -> float:
        """Return the scoring weight for a given urgency level."""
        weights = {
            "critical": self.priority_weight_critical,
            "high": self.priority_weight_high,
            "moderate": self.priority_weight_moderate,
            "low": self.priority_weight_low,
        }
        return weights.get(urgency, self.priority_weight_low)

    def availability_factor_for(self, status: str) -> float:
        """Return the availability factor for a given resource status."""
        factors = {
            "available": self.availability_available,
            "returning": self.availability_returning,
        }
        return factors.get(status, 0.0)

    def travel_speed_for(self, resource_type: str, resource_sub_type: str = "") -> float:
        """Return travel speed in km/h for a resource type."""
        if resource_sub_type == "helicopter":
            return self.travel_speed_helicopter_kmh
        if resource_type == "personnel":
            return self.travel_speed_personnel_kmh
        return self.travel_speed_vehicle_kmh

    def mobilisation_minutes_for(self, resource_type: str, resource_sub_type: str = "") -> float:
        """Return mobilisation overhead in minutes for a resource type."""
        if resource_sub_type == "helicopter":
            return self.mobilisation_helicopter_minutes
        if resource_type == "personnel":
            return self.mobilisation_personnel_minutes
        return self.mobilisation_vehicle_minutes

    def compute_config_hash(self) -> str:
        """Produce a deterministic SHA-256 hash of all active configuration values."""
        config_str = (
            f"priority_weight_critical={self.priority_weight_critical};"
            f"priority_weight_high={self.priority_weight_high};"
            f"priority_weight_moderate={self.priority_weight_moderate};"
            f"priority_weight_low={self.priority_weight_low};"
            f"availability_returning={self.availability_returning};"
            f"distance_floor_km={self.distance_floor_km};"
            f"confidence_base={self.confidence_base};"
            f"fallback_reduction_factor={self.fallback_reduction_factor};"
            f"stale_data_reduction_factor={self.stale_data_reduction_factor};"
            f"partial_data_reduction_factor={self.partial_data_reduction_factor};"
            f"plan_expiry_hours={self.plan_expiry_hours};"
            f"rotation_threshold_hours={self.rotation_threshold_hours};"
            f"replenishment_threshold_percent={self.replenishment_threshold_percent};"
            f"handoff_dedup_window_minutes={self.handoff_dedup_window_minutes};"
            f"inventory_staleness_window_minutes={self.inventory_staleness_window_minutes};"
            f"version_conflict_max_retries={self.version_conflict_max_retries};"
            f"llm_model_tier={self.llm_model_tier};"
            f"llm_temperature={self.llm_temperature};"
            f"llm_max_output_tokens={self.llm_max_output_tokens};"
            f"llm_confidence_threshold={self.llm_confidence_threshold};"
            f"llm_fallback_reduction_factor={self.llm_fallback_reduction_factor};"
            f"llm_monthly_budget_usd={self.llm_monthly_budget_usd};"
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

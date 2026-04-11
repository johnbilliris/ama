"""Risk Assessment Agent configuration — reads all environment variables at startup.

All configurable parameters are consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskAssessmentConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # Source weights for weighted confidence averaging
    source_weight_authoritative: float = field(
        default_factory=lambda: float(os.getenv("SOURCE_WEIGHT_AUTHORITATIVE", "2.0"))
    )
    source_weight_iot: float = field(
        default_factory=lambda: float(os.getenv("SOURCE_WEIGHT_IOT", "1.0"))
    )
    source_weight_social: float = field(
        default_factory=lambda: float(os.getenv("SOURCE_WEIGHT_SOCIAL", "0.5"))
    )

    # Stale signal threshold
    stale_signal_threshold: float = field(
        default_factory=lambda: float(os.getenv("STALE_SIGNAL_THRESHOLD", "0.5"))
    )

    # Handoff deduplication
    handoff_dedup_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("HANDOFF_DEDUP_WINDOW_MINUTES", "10"))
    )

    # Assessment validity (hours)
    assessment_validity_hours_default: int = field(
        default_factory=lambda: int(os.getenv("ASSESSMENT_VALIDITY_HOURS_DEFAULT", "4"))
    )
    assessment_validity_hours_fire: int = field(
        default_factory=lambda: int(os.getenv("ASSESSMENT_VALIDITY_HOURS_FIRE", "2"))
    )
    assessment_validity_hours_cyclone: int = field(
        default_factory=lambda: int(os.getenv("ASSESSMENT_VALIDITY_HOURS_CYCLONE", "6"))
    )

    # Confidence adjustments
    contradiction_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("CONTRADICTION_REDUCTION_FACTOR", "0.7"))
    )
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("FALLBACK_REDUCTION_FACTOR", "0.8"))
    )

    # Escalation thresholds
    escalation_threshold_communication: float = field(
        default_factory=lambda: float(os.getenv("ESCALATION_THRESHOLD_COMMUNICATION", "0.7"))
    )
    escalation_threshold_evacuation: float = field(
        default_factory=lambda: float(os.getenv("ESCALATION_THRESHOLD_EVACUATION", "0.6"))
    )

    # Audit buffer
    audit_buffer_capacity: int = field(
        default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000"))
    )
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv(
            "AUDIT_BUFFER_FILE_PATH", "/var/log/risk-agent/audit-buffer.jsonl"
        )
    )

    # Reasoning summary
    max_reasoning_summary_length: int = field(
        default_factory=lambda: int(os.getenv("MAX_REASONING_SUMMARY_LENGTH", "500"))
    )

    # Version
    agent_version: str = field(
        default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0")
    )

    def source_weight_for(self, source_kind: str) -> float:
        """Return the weight for a given source kind."""
        weights = {
            "authoritative": self.source_weight_authoritative,
            "iot": self.source_weight_iot,
            "social": self.source_weight_social,
        }
        return weights.get(source_kind, self.source_weight_social)

    def validity_hours_for(self, signal_category: str) -> int:
        """Return assessment validity hours for a given signal category."""
        mapping = {
            "fire": self.assessment_validity_hours_fire,
            "cyclone": self.assessment_validity_hours_cyclone,
        }
        return mapping.get(signal_category, self.assessment_validity_hours_default)

    def compute_config_hash(self) -> str:
        """Produce a deterministic SHA-256 hash of all active configuration values."""
        config_str = (
            f"source_weight_authoritative={self.source_weight_authoritative};"
            f"source_weight_iot={self.source_weight_iot};"
            f"source_weight_social={self.source_weight_social};"
            f"stale_signal_threshold={self.stale_signal_threshold};"
            f"handoff_dedup_window_minutes={self.handoff_dedup_window_minutes};"
            f"assessment_validity_hours_default={self.assessment_validity_hours_default};"
            f"assessment_validity_hours_fire={self.assessment_validity_hours_fire};"
            f"assessment_validity_hours_cyclone={self.assessment_validity_hours_cyclone};"
            f"contradiction_reduction_factor={self.contradiction_reduction_factor};"
            f"fallback_reduction_factor={self.fallback_reduction_factor};"
            f"escalation_threshold_communication={self.escalation_threshold_communication};"
            f"escalation_threshold_evacuation={self.escalation_threshold_evacuation};"
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

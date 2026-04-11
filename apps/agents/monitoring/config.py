"""Monitoring Agent configuration — reads all environment variables at startup (CHK044).

All configurable parameters are consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MonitoringConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # Escalation
    escalation_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("ESCALATION_CONFIDENCE_THRESHOLD", "0.8"))
    )

    # Deduplication
    signal_dedup_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("SIGNAL_DEDUP_WINDOW_MINUTES", "10"))
    )

    # Retrospective association
    retrospective_lookback_hours: int = field(
        default_factory=lambda: int(os.getenv("RETROSPECTIVE_LOOKBACK_HOURS", "24"))
    )

    # Freshness thresholds (per source type)
    staleness_threshold_authoritative_minutes: int = field(
        default_factory=lambda: int(os.getenv("STALENESS_THRESHOLD_AUTHORITATIVE_MINUTES", "15"))
    )
    staleness_threshold_iot_minutes: int = field(
        default_factory=lambda: int(os.getenv("STALENESS_THRESHOLD_IOT_MINUTES", "5"))
    )
    staleness_threshold_social_minutes: int = field(
        default_factory=lambda: int(os.getenv("STALENESS_THRESHOLD_SOCIAL_MINUTES", "30"))
    )

    # LLM evaluation
    llm_eval_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("LLM_EVAL_TIMEOUT_SECONDS", "3"))
    )

    # Misinformation
    suspicious_confidence_penalty: float = field(
        default_factory=lambda: float(os.getenv("SUSPICIOUS_CONFIDENCE_PENALTY", "0.15"))
    )

    # Audit buffer
    audit_buffer_capacity: int = field(
        default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000"))
    )
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv(
            "AUDIT_BUFFER_FILE_PATH", "/var/log/monitoring-agent/audit-buffer.jsonl"
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

    def staleness_threshold_for(self, source_type: str) -> int:
        """Return the staleness threshold in minutes for a given source type."""
        thresholds = {
            "authoritative": self.staleness_threshold_authoritative_minutes,
            "iot": self.staleness_threshold_iot_minutes,
            "social": self.staleness_threshold_social_minutes,
        }
        return thresholds.get(source_type, self.staleness_threshold_social_minutes)

    def compute_config_hash(self) -> str:
        """Produce a deterministic SHA-256 hash of all active configuration values."""
        config_str = (
            f"escalation_confidence_threshold={self.escalation_confidence_threshold};"
            f"signal_dedup_window_minutes={self.signal_dedup_window_minutes};"
            f"retrospective_lookback_hours={self.retrospective_lookback_hours};"
            f"staleness_threshold_authoritative_minutes={self.staleness_threshold_authoritative_minutes};"
            f"staleness_threshold_iot_minutes={self.staleness_threshold_iot_minutes};"
            f"staleness_threshold_social_minutes={self.staleness_threshold_social_minutes};"
            f"llm_eval_timeout_seconds={self.llm_eval_timeout_seconds};"
            f"suspicious_confidence_penalty={self.suspicious_confidence_penalty};"
            f"audit_buffer_capacity={self.audit_buffer_capacity};"
            f"max_reasoning_summary_length={self.max_reasoning_summary_length};"
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

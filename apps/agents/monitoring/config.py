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
    llm_eval_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("LLM_EVAL_TIMEOUT_SECONDS", "3")))

    # Misinformation
    suspicious_confidence_penalty: float = field(
        default_factory=lambda: float(os.getenv("SUSPICIOUS_CONFIDENCE_PENALTY", "0.15"))
    )

    # Audit buffer
    audit_buffer_capacity: int = field(default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000")))
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv("AUDIT_BUFFER_FILE_PATH", "/var/log/monitoring-agent/audit-buffer.jsonl")
    )

    # Reasoning summary
    max_reasoning_summary_length: int = field(
        default_factory=lambda: int(os.getenv("MAX_REASONING_SUMMARY_LENGTH", "500"))
    )

    # Version
    agent_version: str = field(default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0"))

    # --- LLM Configuration ---
    llm_model_tier: str = field(default_factory=lambda: os.getenv("LLM_MODEL_TIER", "drafting"))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    llm_max_output_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000")))
    llm_confidence_threshold: float = field(default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7")))
    llm_fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5"))
    )
    llm_monthly_budget_usd: float = field(default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "50.0")))

    # M&E Configuration
    max_concurrent_me_frameworks: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_ME_FRAMEWORKS", "10"))
    )
    indicator_staleness_days: int = field(default_factory=lambda: int(os.getenv("INDICATOR_STALENESS_DAYS", "7")))
    ai_analysis_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("AI_ANALYSIS_TIMEOUT_SECONDS", "30"))
    )
    catalogue_cache_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CATALOGUE_CACHE_TTL_SECONDS", "3600"))
    )

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
            f"llm_model_tier={self.llm_model_tier};"
            f"llm_temperature={self.llm_temperature};"
            f"llm_max_output_tokens={self.llm_max_output_tokens};"
            f"llm_confidence_threshold={self.llm_confidence_threshold};"
            f"llm_fallback_reduction_factor={self.llm_fallback_reduction_factor};"
            f"llm_monthly_budget_usd={self.llm_monthly_budget_usd};"
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

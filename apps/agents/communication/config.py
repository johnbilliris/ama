"""Communication Agent configuration — reads all environment variables at startup.

All configurable parameters are consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field


def _csv_list(env_var: str, default: str) -> list[str]:
    """Parse a comma-separated environment variable into a list of strings."""
    return [s.strip() for s in os.getenv(env_var, default).split(",") if s.strip()]


@dataclass(frozen=True)
class CommunicationConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # Languages
    supported_languages: list[str] = field(
        default_factory=lambda: _csv_list("SUPPORTED_LANGUAGES", "en-AU,zh-Hans,ar,vi,el,it")
    )

    # Translation quality
    back_translation_threshold: float = field(
        default_factory=lambda: float(os.getenv("BACK_TRANSLATION_THRESHOLD", "0.85"))
    )
    alert_max_tokens: int = field(
        default_factory=lambda: int(os.getenv("ALERT_MAX_TOKENS", "180"))
    )

    # Deduplication
    handoff_dedup_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("HANDOFF_DEDUP_WINDOW_MINUTES", "30"))
    )

    # Approval workflow
    approval_escalation_timeout_minutes: int = field(
        default_factory=lambda: int(os.getenv("APPROVAL_ESCALATION_TIMEOUT_MINUTES", "15"))
    )
    max_escalation_levels: int = field(
        default_factory=lambda: int(os.getenv("MAX_ESCALATION_LEVELS", "3"))
    )

    # Alert lifecycle
    alert_expiry_hours: int = field(
        default_factory=lambda: int(os.getenv("ALERT_EXPIRY_HOURS", "24"))
    )

    # Delivery
    delivery_max_retries: int = field(
        default_factory=lambda: int(os.getenv("DELIVERY_MAX_RETRIES", "3"))
    )
    delivery_channels: list[str] = field(
        default_factory=lambda: _csv_list("DELIVERY_CHANNELS", "sms,push,emergency_broadcast")
    )
    eas_endpoint_url: str = field(
        default_factory=lambda: os.getenv("EAS_ENDPOINT_URL", "")
    )
    sms_max_length: int = field(
        default_factory=lambda: int(os.getenv("SMS_MAX_LENGTH", "612"))
    )
    content_max_length: int = field(
        default_factory=lambda: int(os.getenv("CONTENT_MAX_LENGTH", "1200"))
    )

    # Audit
    audit_buffer_capacity: int = field(
        default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000"))
    )
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv("AUDIT_BUFFER_FILE_PATH", "communication_audit.jsonl")
    )

    # Versioning
    version_conflict_max_retries: int = field(
        default_factory=lambda: int(os.getenv("VERSION_CONFLICT_MAX_RETRIES", "3"))
    )

    # Agent metadata
    agent_version: str = field(
        default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("PORT", "8084"))
    )

    # Confidence penalties
    confidence_base: float = field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_BASE", "1.0"))
    )
    freshness_penalty_factor: float = field(
        default_factory=lambda: float(os.getenv("FRESHNESS_PENALTY_FACTOR", "0.9"))
    )
    back_translation_penalty_factor: float = field(
        default_factory=lambda: float(os.getenv("BACK_TRANSLATION_PENALTY_FACTOR", "0.9"))
    )
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("FALLBACK_REDUCTION_FACTOR", "0.8"))
    )

    # Concurrency and scaling
    max_concurrent_alerts: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_ALERTS", "50"))
    )
    queue_scale_out_threshold: int = field(
        default_factory=lambda: int(os.getenv("QUEUE_SCALE_OUT_THRESHOLD", "10"))
    )
    queue_scale_in_threshold: int = field(
        default_factory=lambda: int(os.getenv("QUEUE_SCALE_IN_THRESHOLD", "3"))
    )
    scale_in_cooldown_minutes: int = field(
        default_factory=lambda: int(os.getenv("SCALE_IN_COOLDOWN_MINUTES", "5"))
    )

    # --- LLM Configuration ---
    llm_model_tier: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL_TIER", "drafting")
    )
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3"))
    )
    llm_max_output_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000"))
    )
    llm_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7"))
    )
    llm_fallback_reduction_factor: float = field(
        default_factory=lambda: float(
            os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5")
        )
    )
    llm_monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "50.0"))
    )

    def __post_init__(self) -> None:
        """Validate LLM configuration values immediately after construction."""
        if self.llm_model_tier not in ("reasoning", "drafting"):
            raise ValueError(
                f"Invalid LLM_MODEL_TIER: {self.llm_model_tier}"
            )
        if not (0.0 <= self.llm_temperature <= 2.0):
            raise ValueError(
                f"LLM_TEMPERATURE must be 0.0–2.0, got {self.llm_temperature}"
            )
        if self.llm_max_output_tokens <= 0 or self.llm_max_output_tokens > 16384:
            raise ValueError(
                f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.llm_max_output_tokens}"
            )
        if not (0.0 <= self.llm_confidence_threshold <= 1.0):
            raise ValueError(
                f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.llm_confidence_threshold}"
            )
        if not (0.0 <= self.llm_fallback_reduction_factor <= 1.0):
            raise ValueError(
                "LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, "
                f"got {self.llm_fallback_reduction_factor}"
            )

    def compute_config_hash(self) -> str:
        """Produce a deterministic SHA-256 hash of all active configuration values."""
        config_str = (
            f"supported_languages={','.join(self.supported_languages)};"
            f"back_translation_threshold={self.back_translation_threshold};"
            f"alert_max_tokens={self.alert_max_tokens};"
            f"handoff_dedup_window_minutes={self.handoff_dedup_window_minutes};"
            f"approval_escalation_timeout_minutes={self.approval_escalation_timeout_minutes};"
            f"max_escalation_levels={self.max_escalation_levels};"
            f"alert_expiry_hours={self.alert_expiry_hours};"
            f"delivery_max_retries={self.delivery_max_retries};"
            f"delivery_channels={','.join(self.delivery_channels)};"
            f"eas_endpoint_url={self.eas_endpoint_url};"
            f"sms_max_length={self.sms_max_length};"
            f"content_max_length={self.content_max_length};"
            f"audit_buffer_capacity={self.audit_buffer_capacity};"
            f"audit_buffer_file_path={self.audit_buffer_file_path};"
            f"version_conflict_max_retries={self.version_conflict_max_retries};"
            f"agent_version={self.agent_version};"
            f"port={self.port};"
            f"confidence_base={self.confidence_base};"
            f"freshness_penalty_factor={self.freshness_penalty_factor};"
            f"back_translation_penalty_factor={self.back_translation_penalty_factor};"
            f"fallback_reduction_factor={self.fallback_reduction_factor};"
            f"max_concurrent_alerts={self.max_concurrent_alerts};"
            f"queue_scale_out_threshold={self.queue_scale_out_threshold};"
            f"queue_scale_in_threshold={self.queue_scale_in_threshold};"
            f"scale_in_cooldown_minutes={self.scale_in_cooldown_minutes};"
            f"llm_model_tier={self.llm_model_tier};"
            f"llm_temperature={self.llm_temperature};"
            f"llm_max_output_tokens={self.llm_max_output_tokens};"
            f"llm_confidence_threshold={self.llm_confidence_threshold};"
            f"llm_fallback_reduction_factor={self.llm_fallback_reduction_factor};"
            f"llm_monthly_budget_usd={self.llm_monthly_budget_usd};"
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

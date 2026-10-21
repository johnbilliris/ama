"""Communication Agent configuration — reads all environment variables at startup.

All configurable parameters are consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field


def _csv_tuple(env_var: str, default: str) -> tuple[str, ...]:
    """Parse a comma-separated environment variable into an immutable tuple."""
    return tuple(s.strip() for s in os.getenv(env_var, default).split(",") if s.strip())


@dataclass(frozen=True)
class CommunicationConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # Languages
    supported_languages: tuple[str, ...] = field(
        default_factory=lambda: _csv_tuple("SUPPORTED_LANGUAGES", "en-AU,zh-Hans,ar,vi,el,it")
    )

    # Translation quality
    back_translation_threshold: float = field(
        default_factory=lambda: float(os.getenv("BACK_TRANSLATION_THRESHOLD", "0.85"))
    )
    alert_max_tokens: int = field(default_factory=lambda: int(os.getenv("ALERT_MAX_TOKENS", "180")))
    draft_deadline_seconds: float = field(default_factory=lambda: float(os.getenv("DRAFT_DEADLINE_SECONDS", "30.0")))

    # Deduplication
    handoff_dedup_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("HANDOFF_DEDUP_WINDOW_MINUTES", "30"))
    )

    # Approval workflow
    approval_escalation_timeout_minutes: int = field(
        default_factory=lambda: int(os.getenv("APPROVAL_ESCALATION_TIMEOUT_MINUTES", "15"))
    )
    emergency_warning_timeout_minutes: int = field(
        default_factory=lambda: int(os.getenv("EMERGENCY_WARNING_TIMEOUT_MINUTES", "5"))
    )
    max_escalation_levels: int = field(default_factory=lambda: int(os.getenv("MAX_ESCALATION_LEVELS", "3")))

    # Alert lifecycle
    alert_expiry_hours: int = field(default_factory=lambda: int(os.getenv("ALERT_EXPIRY_HOURS", "24")))
    lifecycle_sweep_seconds: float = field(
        default_factory=lambda: float(os.getenv("COMMUNICATION_LIFECYCLE_SWEEP_SECONDS", "30"))
    )

    # Persistence
    environment: str = field(default_factory=lambda: os.getenv("AMA_ENVIRONMENT", "development").lower())
    cosmos_endpoint: str = field(default_factory=lambda: os.getenv("COSMOS_ENDPOINT", ""))
    cosmos_database_name: str = field(default_factory=lambda: os.getenv("COSMOS_DATABASE_NAME", "disaster-response"))
    public_alerts_container_name: str = field(
        default_factory=lambda: os.getenv("PUBLIC_ALERTS_CONTAINER_NAME", "public-alerts")
    )
    communication_decisions_container_name: str = field(
        default_factory=lambda: os.getenv("COMMUNICATION_DECISIONS_CONTAINER_NAME", "communication-decisions")
    )
    incidents_container_name: str = field(default_factory=lambda: os.getenv("INCIDENTS_CONTAINER_NAME", "incidents"))
    recommendations_container_name: str = field(
        default_factory=lambda: os.getenv("RECOMMENDATIONS_CONTAINER_NAME", "risk-recommendations")
    )
    assessments_container_name: str = field(
        default_factory=lambda: os.getenv("ASSESSMENTS_CONTAINER_NAME", "hazard-assessments")
    )
    service_bus_namespace: str = field(
        default_factory=lambda: os.getenv("AZURE_SERVICEBUS_NAMESPACE", os.getenv("SERVICE_BUS_NAMESPACE", ""))
    )
    commander_approval_queue: str = field(
        default_factory=lambda: os.getenv("COMMANDER_APPROVAL_QUEUE", "commander-approval-queue")
    )

    # Delivery
    delivery_max_retries: int = field(default_factory=lambda: int(os.getenv("DELIVERY_MAX_RETRIES", "3")))
    delivery_max_concurrency: int = field(default_factory=lambda: int(os.getenv("DELIVERY_MAX_CONCURRENCY", "16")))
    delivery_channels: tuple[str, ...] = field(
        default_factory=lambda: _csv_tuple("DELIVERY_CHANNELS", "sms,push,emergency_broadcast")
    )
    sms_sender_identity: str = field(default_factory=lambda: os.getenv("SMS_SENDER_IDENTITY", ""))
    sms_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_COMMUNICATION_SERVICES_ENDPOINT", ""))
    notification_hub_url: str = field(default_factory=lambda: os.getenv("NOTIFICATION_HUB_URL", ""))
    notification_hub_sas_token: str = field(default_factory=lambda: os.getenv("NOTIFICATION_HUB_SAS_TOKEN", ""))
    eas_endpoint_url: str = field(default_factory=lambda: os.getenv("EAS_ENDPOINT_URL", ""))
    eas_auth_token: str = field(default_factory=lambda: os.getenv("EAS_AUTH_TOKEN", ""))
    eas_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("EAS_TIMEOUT_SECONDS", "10.0")))
    sms_max_length: int = field(default_factory=lambda: int(os.getenv("SMS_MAX_LENGTH", "612")))
    content_max_length: int = field(default_factory=lambda: int(os.getenv("CONTENT_MAX_LENGTH", "1200")))

    # Audit
    audit_buffer_capacity: int = field(default_factory=lambda: int(os.getenv("AUDIT_BUFFER_CAPACITY", "10000")))
    audit_buffer_file_path: str = field(
        default_factory=lambda: os.getenv("AUDIT_BUFFER_FILE_PATH", "communication_audit.jsonl")
    )
    audit_flush_interval_seconds: float = field(
        default_factory=lambda: float(os.getenv("AUDIT_FLUSH_INTERVAL_SECONDS", "30"))
    )

    # Versioning
    version_conflict_max_retries: int = field(
        default_factory=lambda: int(os.getenv("VERSION_CONFLICT_MAX_RETRIES", "3"))
    )

    # Agent metadata
    agent_version: str = field(default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8084")))

    # Confidence penalties
    confidence_base: float = field(default_factory=lambda: float(os.getenv("CONFIDENCE_BASE", "1.0")))
    freshness_penalty_factor: float = field(default_factory=lambda: float(os.getenv("FRESHNESS_PENALTY_FACTOR", "0.9")))
    assessment_staleness_threshold_minutes: int = field(
        default_factory=lambda: int(os.getenv("ASSESSMENT_STALENESS_THRESHOLD_MINUTES", "15"))
    )
    back_translation_penalty_factor: float = field(
        default_factory=lambda: float(os.getenv("BACK_TRANSLATION_PENALTY_FACTOR", "0.9"))
    )
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("FALLBACK_REDUCTION_FACTOR", "0.8"))
    )

    # Concurrency and scaling
    max_concurrent_alerts: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_ALERTS", "50")))
    queue_scale_out_threshold: int = field(default_factory=lambda: int(os.getenv("QUEUE_SCALE_OUT_THRESHOLD", "10")))
    queue_scale_in_threshold: int = field(default_factory=lambda: int(os.getenv("QUEUE_SCALE_IN_THRESHOLD", "3")))
    scale_in_cooldown_minutes: int = field(default_factory=lambda: int(os.getenv("SCALE_IN_COOLDOWN_MINUTES", "5")))

    # --- LLM Configuration ---
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
        languages = tuple(dict.fromkeys(self.supported_languages))
        if not languages or "en-AU" not in languages:
            raise ValueError("SUPPORTED_LANGUAGES must include en-AU")
        supported = {"en-AU", "zh-Hans", "ar", "vi", "el", "it"}
        unknown_languages = set(languages) - supported
        if unknown_languages:
            raise ValueError(f"Unsupported languages: {', '.join(sorted(unknown_languages))}")
        object.__setattr__(self, "supported_languages", ("en-AU", *[lang for lang in languages if lang != "en-AU"]))

        channel_aliases = {"broadcast": "emergency_broadcast"}
        channels = tuple(dict.fromkeys(channel_aliases.get(channel, channel) for channel in self.delivery_channels))
        unknown_channels = set(channels) - {"sms", "push", "emergency_broadcast"}
        if not channels or unknown_channels:
            raise ValueError(f"Unsupported delivery channels: {', '.join(sorted(unknown_channels)) or '<empty>'}")
        object.__setattr__(self, "delivery_channels", channels)

        bounded_factors = {
            "BACK_TRANSLATION_THRESHOLD": self.back_translation_threshold,
            "CONFIDENCE_BASE": self.confidence_base,
            "FRESHNESS_PENALTY_FACTOR": self.freshness_penalty_factor,
            "BACK_TRANSLATION_PENALTY_FACTOR": self.back_translation_penalty_factor,
            "FALLBACK_REDUCTION_FACTOR": self.fallback_reduction_factor,
        }
        for name, value in bounded_factors.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be 0.0–1.0, got {value}")
        positive_values = {
            "ALERT_MAX_TOKENS": self.alert_max_tokens,
            "HANDOFF_DEDUP_WINDOW_MINUTES": self.handoff_dedup_window_minutes,
            "APPROVAL_ESCALATION_TIMEOUT_MINUTES": self.approval_escalation_timeout_minutes,
            "EMERGENCY_WARNING_TIMEOUT_MINUTES": self.emergency_warning_timeout_minutes,
            "ALERT_EXPIRY_HOURS": self.alert_expiry_hours,
            "DELIVERY_MAX_CONCURRENCY": self.delivery_max_concurrency,
            "SMS_MAX_LENGTH": self.sms_max_length,
            "CONTENT_MAX_LENGTH": self.content_max_length,
            "AUDIT_BUFFER_CAPACITY": self.audit_buffer_capacity,
            "VERSION_CONFLICT_MAX_RETRIES": self.version_conflict_max_retries,
            "PORT": self.port,
            "MAX_CONCURRENT_ALERTS": self.max_concurrent_alerts,
            "LIFECYCLE_SWEEP_SECONDS": self.lifecycle_sweep_seconds,
        }
        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")
        if not 1 <= self.max_escalation_levels <= 3:
            raise ValueError("MAX_ESCALATION_LEVELS must be between 1 and 3")
        if not 0 <= self.delivery_max_retries <= 10:
            raise ValueError("DELIVERY_MAX_RETRIES must be between 0 and 10")
        if self.queue_scale_in_threshold < 0 or self.queue_scale_out_threshold <= self.queue_scale_in_threshold:
            raise ValueError("Queue scale-out threshold must exceed the non-negative scale-in threshold")
        if self.llm_model_tier not in ("reasoning", "drafting"):
            raise ValueError(f"Invalid LLM_MODEL_TIER: {self.llm_model_tier}")
        if not (0.0 <= self.llm_temperature <= 2.0):
            raise ValueError(f"LLM_TEMPERATURE must be 0.0–2.0, got {self.llm_temperature}")
        if self.llm_max_output_tokens <= 0 or self.llm_max_output_tokens > 16384:
            raise ValueError(f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.llm_max_output_tokens}")
        if self.draft_deadline_seconds <= 0:
            raise ValueError(f"DRAFT_DEADLINE_SECONDS must be > 0, got {self.draft_deadline_seconds}")
        if self.eas_timeout_seconds <= 0:
            raise ValueError(f"EAS_TIMEOUT_SECONDS must be > 0, got {self.eas_timeout_seconds}")
        if not (0.0 <= self.llm_confidence_threshold <= 1.0):
            raise ValueError(f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.llm_confidence_threshold}")
        if not (0.0 <= self.llm_fallback_reduction_factor <= 1.0):
            raise ValueError(f"LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, got {self.llm_fallback_reduction_factor}")

    def compute_config_hash(self) -> str:
        """Produce a deterministic SHA-256 hash of all active configuration values."""
        config_str = (
            f"supported_languages={','.join(self.supported_languages)};"
            f"back_translation_threshold={self.back_translation_threshold};"
            f"alert_max_tokens={self.alert_max_tokens};"
            f"handoff_dedup_window_minutes={self.handoff_dedup_window_minutes};"
            f"approval_escalation_timeout_minutes={self.approval_escalation_timeout_minutes};"
            f"emergency_warning_timeout_minutes={self.emergency_warning_timeout_minutes};"
            f"max_escalation_levels={self.max_escalation_levels};"
            f"alert_expiry_hours={self.alert_expiry_hours};"
            f"lifecycle_sweep_seconds={self.lifecycle_sweep_seconds};"
            f"environment={self.environment};"
            f"cosmos_endpoint={self.cosmos_endpoint};"
            f"cosmos_database_name={self.cosmos_database_name};"
            f"public_alerts_container_name={self.public_alerts_container_name};"
            f"communication_decisions_container_name={self.communication_decisions_container_name};"
            f"incidents_container_name={self.incidents_container_name};"
            f"recommendations_container_name={self.recommendations_container_name};"
            f"assessments_container_name={self.assessments_container_name};"
            f"service_bus_namespace={self.service_bus_namespace};"
            f"commander_approval_queue={self.commander_approval_queue};"
            f"delivery_max_retries={self.delivery_max_retries};"
            f"delivery_max_concurrency={self.delivery_max_concurrency};"
            f"delivery_channels={','.join(self.delivery_channels)};"
            f"sms_sender_identity={self.sms_sender_identity};"
            f"sms_endpoint={self.sms_endpoint};"
            f"notification_hub_url={self.notification_hub_url};"
            f"eas_endpoint_url={self.eas_endpoint_url};"
            f"eas_timeout_seconds={self.eas_timeout_seconds};"
            f"sms_max_length={self.sms_max_length};"
            f"content_max_length={self.content_max_length};"
            f"audit_buffer_capacity={self.audit_buffer_capacity};"
            f"audit_buffer_file_path={self.audit_buffer_file_path};"
            f"audit_flush_interval_seconds={self.audit_flush_interval_seconds};"
            f"version_conflict_max_retries={self.version_conflict_max_retries};"
            f"agent_version={self.agent_version};"
            f"port={self.port};"
            f"confidence_base={self.confidence_base};"
            f"freshness_penalty_factor={self.freshness_penalty_factor};"
            f"assessment_staleness_threshold_minutes={self.assessment_staleness_threshold_minutes};"
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

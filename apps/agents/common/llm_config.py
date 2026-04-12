"""Shared Azure OpenAI LLM configuration — read from environment variables at startup.

All configurable parameters are consolidated per data-model.md §LLMClientConfig.
Values are read once at construction and frozen for the lifetime of the process.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMClientConfig:
    """Immutable LLM configuration read from environment variables with sensible defaults."""

    # Connection
    endpoint: str = field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", "")
    )
    reasoning_deployment: str = field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_REASONING_DEPLOYMENT", "")
    )
    drafting_deployment: str = field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_DRAFTING_DEPLOYMENT", "")
    )
    api_version: str = field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    )

    # Model parameters
    model_tier: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL_TIER", "drafting")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3"))
    )
    max_output_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000"))
    )

    # Retry & circuit breaker
    retry_attempts: int = field(
        default_factory=lambda: int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))
    )
    retry_min_wait: float = field(default=1.0)
    retry_max_wait: float = field(default=4.0)
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))
    )
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: int(os.getenv("LLM_CB_FAILURE_THRESHOLD", "3"))
    )
    circuit_breaker_recovery_timeout: float = field(
        default_factory=lambda: float(os.getenv("LLM_CB_RECOVERY_TIMEOUT", "30.0"))
    )

    # Confidence
    confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7"))
    )
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5"))
    )

    # Cost tracking
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "50.0"))
    )

    def __post_init__(self) -> None:
        """Validate configuration values immediately after construction."""
        if self.endpoint:
            hostname = self.endpoint.lower()
            # Azure OpenAI endpoints use format: https://<resource>.openai.azure.com/
            # The resource name doesn't contain the region, so we validate the
            # endpoint is a valid Azure OpenAI URL rather than checking for region
            # in the hostname. Region compliance is enforced by Bicep IaC (FR-009).
            if not (
                hostname.startswith("https://")
                and ("openai.azure.com" in hostname or "cognitiveservices.azure.com" in hostname)
            ):
                raise ValueError(
                    f"AZURE_OPENAI_ENDPOINT must be a valid Azure OpenAI URL "
                    f"(https://<resource>.openai.azure.com), got: {self.endpoint}"
                )
        if self.model_tier not in ("reasoning", "drafting"):
            raise ValueError(f"Invalid LLM_MODEL_TIER: {self.model_tier}")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"LLM_TEMPERATURE must be 0.0–2.0, got {self.temperature}")
        if self.max_output_tokens <= 0 or self.max_output_tokens > 16384:
            raise ValueError(f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.max_output_tokens}")
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError(f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.confidence_threshold}")
        if not (0.0 <= self.fallback_reduction_factor <= 1.0):
            raise ValueError(
                f"LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, got {self.fallback_reduction_factor}"
            )
        if self.monthly_budget_usd <= 0:
            raise ValueError(f"LLM_MONTHLY_BUDGET_USD must be > 0, got {self.monthly_budget_usd}")

    def deployment_for(self, purpose: str) -> str:
        """Return the deployment name for the given purpose."""
        if purpose == "reasoning":
            return self.reasoning_deployment
        if purpose == "drafting":
            return self.drafting_deployment
        raise ValueError(f"Unknown LLM purpose: {purpose!r}. Must be 'reasoning' or 'drafting'.")

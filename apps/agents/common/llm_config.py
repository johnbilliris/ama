"""Shared LLM configuration — Microsoft Foundry only (post-cutover).

ADR-20 §Q-P6-03 cleanup: the per-agent canary cutover (FR-RAG-FM-06) is
complete; the legacy ``LEGACY_AZURE_OPENAI=1`` rollback flag has been
removed and the configuration now reads exclusively from the
``AZURE_AI_PROJECT_*`` env vars. The legacy ``AZURE_OPENAI_*`` env vars
remain readable as a hermetic-test seam (unit tests inject ad-hoc
endpoints without provisioning Foundry) but are NEVER set in production
Bicep — the API and Agents container apps only see ``AZURE_AI_PROJECT_*``.

All configurable parameters are consolidated per data-model.md §LLMClientConfig.
Values are read once at construction and frozen for the lifetime of the process.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMClientConfig:
    """Immutable LLM configuration read from environment variables with sensible defaults.

    Spec 036 / ADR-20 hard cutover: the chat plane is Microsoft Foundry only,
    surfaced via ``AZURE_AI_PROJECT_ENDPOINT`` + ``AZURE_AI_PROJECT_DEPLOYMENTS``
    (CSV of ``modelId@version=deploymentName``) per
    ``apps/eval-runner/src/ama_eval/foundry_client.py``.

    The ``AZURE_OPENAI_*`` env vars are RETAINED here purely as a hermetic
    test seam — unit tests can inject a synthetic endpoint without
    provisioning Foundry. Production Bicep (``infra/main.bicep``) does
    NOT set these variables on the API or Agents container apps.
    """

    # ───────── Test-only fallback (production sets AZURE_AI_PROJECT_* only) ─────────
    endpoint: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    reasoning_deployment: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_REASONING_DEPLOYMENT", ""))
    drafting_deployment: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_DRAFTING_DEPLOYMENT", ""))
    api_version: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"))

    # ───────── Spec 036 — Foundry connection (FR-RAG-FM-01, R-01) ─────────
    foundry_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""))
    foundry_deployments: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_DEPLOYMENTS", ""))
    foundry_region: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_REGION", "australiaeast"))

    # Model parameters
    model_tier: str = field(default_factory=lambda: os.getenv("LLM_MODEL_TIER", "drafting"))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    max_input_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_INPUT_TOKENS", "4000")))
    max_output_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000")))

    # Retry & circuit breaker
    retry_attempts: int = field(default_factory=lambda: int(os.getenv("LLM_RETRY_ATTEMPTS", "3")))
    retry_min_wait: float = field(default=1.0)
    retry_max_wait: float = field(default=4.0)
    timeout_seconds: float = field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0")))
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: int(os.getenv("LLM_CB_FAILURE_THRESHOLD", "3"))
    )
    circuit_breaker_recovery_timeout: float = field(
        default_factory=lambda: float(os.getenv("LLM_CB_RECOVERY_TIMEOUT", "30.0"))
    )

    # Confidence
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7")))
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5"))
    )

    # Cost tracking
    monthly_budget_usd: float = field(default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "50.0")))

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
                    f"(https://<resource>.openai.azure.com or .cognitiveservices.azure.com), got: {self.endpoint}"
                )
        if self.model_tier not in ("reasoning", "drafting"):
            raise ValueError(f"Invalid LLM_MODEL_TIER: {self.model_tier}")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"LLM_TEMPERATURE must be 0.0–2.0, got {self.temperature}")
        if self.max_input_tokens <= 0 or self.max_input_tokens > 200000:
            raise ValueError(f"LLM_MAX_INPUT_TOKENS must be 1–200000, got {self.max_input_tokens}")
        if self.max_output_tokens <= 0 or self.max_output_tokens > 16384:
            raise ValueError(f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.max_output_tokens}")
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError(f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.confidence_threshold}")
        if not (0.0 <= self.fallback_reduction_factor <= 1.0):
            raise ValueError(f"LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, got {self.fallback_reduction_factor}")
        if self.monthly_budget_usd <= 0:
            raise ValueError(f"LLM_MONTHLY_BUDGET_USD must be > 0, got {self.monthly_budget_usd}")

    def deployment_for(self, purpose: str) -> str:
        """Return the deployment name for the given purpose."""
        if purpose == "reasoning":
            return self.reasoning_deployment
        if purpose == "drafting":
            return self.drafting_deployment
        raise ValueError(f"Unknown LLM purpose: {purpose!r}. Must be 'reasoning' or 'drafting'.")

    # Spec 036 (T021) — return the Foundry deployment **map** for the
    # constructor-injectable seam (FR-RAG-FM-07). The CSV format mirrors
    # apps/eval-runner/src/ama_eval/foundry_client._parse_deployment_map.
    def foundry_deployment_map(self) -> dict[str, str]:
        """Parse ``AZURE_AI_PROJECT_DEPLOYMENTS`` into ``{modelKey: deploymentName}``.

        First-write-wins: see
        ``apps/agents/common/foundry_chat_client._parse_deployment_map`` for
        the rationale. Per-tier env vars (``AZURE_AI_<TIER>_DEPLOYMENT``)
        should be preferred when callers need a specific tier rather than
        an arbitrary first match.
        """
        out: dict[str, str] = {}
        if not self.foundry_deployments:
            return out
        for entry in (e.strip() for e in self.foundry_deployments.split(",") if e.strip()):
            if "=" not in entry:
                continue
            key, name = entry.split("=", 1)
            out.setdefault(key.strip(), name.strip())
        return out

    def foundry_model_key_for(self, purpose: str) -> str:
        """Resolve the Foundry ``modelId@version`` key for an LLM purpose.

        Lookup order:
          1. ``AZURE_AI_<PURPOSE>_DEPLOYMENT`` set → return ``purpose``
             itself (a tier alias). ``LiveFoundryChatClient._resolve``
             recognises tier aliases and looks up the explicit deployment
             env var. This lets callers target a specific tier even when
             the CSV map collapses tiers onto a shared model key.
          2. ``AZURE_AI_<PURPOSE>_MODEL_KEY`` (e.g. ``AZURE_AI_REASONING_MODEL_KEY``).
          3. Reuse the legacy ``AZURE_OPENAI_<PURPOSE>_DEPLOYMENT`` value as the model key
             (single-deployment-per-tier convention from spec 014/032).
          4. Default to ``gpt-4o`` (reasoning) / ``gpt-4o-mini`` (drafting) per
             plan.md Performance Goals.
        """
        tier_env = f"AZURE_AI_{purpose.upper()}_DEPLOYMENT"
        if os.getenv(tier_env):
            return purpose
        env_key = f"AZURE_AI_{purpose.upper()}_MODEL_KEY"
        explicit = os.getenv(env_key)
        if explicit:
            return explicit
        legacy = self.deployment_for(purpose)
        if legacy:
            return legacy
        return "gpt-4o" if purpose == "reasoning" else "gpt-4o-mini"

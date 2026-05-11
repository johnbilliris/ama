"""Shared chat-client factory for MAF Agents (T012, ADR-033-01).

Spec 036 + ADR-20 hard cutover: the factory builds an
``OpenAIChatClient`` against the Microsoft Foundry project endpoint
(``AZURE_AI_PROJECT_ENDPOINT``) using AAD-only auth on the
``cognitiveservices`` token scope. The legacy
``AZURE_OPENAI_ENDPOINT`` path is gone — the env var is no longer set
by production Bicep — so unconfigured callers fail closed rather than
silently fall back to a synthetic / mock client. API-key kwargs remain
forbidden (FR-025, FR-RAG-FM-04).

The factory **signature is preserved verbatim** — call sites in the
five named MAF Agents do not change.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from agent_framework_openai import OpenAIChatClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from common.llm_config import LLMClientConfig

logger = logging.getLogger(__name__)

_AOAI_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


@lru_cache(maxsize=1)
def _shared_credential() -> DefaultAzureCredential:
    """Single ``DefaultAzureCredential`` instance shared across the process.

    ``DefaultAzureCredential`` caches tokens internally, so re-creating it per
    request leaks token-refresh load and breaks managed-identity probe caches.
    """
    return DefaultAzureCredential()


@lru_cache(maxsize=1)
def _shared_token_provider() -> Any:
    """Bearer-token callable for the cognitive-services scope (Foundry endpoint)."""
    return get_bearer_token_provider(_shared_credential(), _AOAI_TOKEN_SCOPE)


def _resolve_endpoint_and_deployment(
    cfg: LLMClientConfig,
    model_tier: str,
) -> tuple[str, str]:
    """Return ``(endpoint, deployment)`` for the Foundry chat plane.

    Lookup order (post-cutover):
      1. ``AZURE_AI_PROJECT_ENDPOINT`` is the canonical endpoint.
      2. ``cfg.endpoint`` (``AZURE_OPENAI_ENDPOINT``) is an opt-in
         test-only fallback — production Bicep no longer sets this var.
      3. Deployment is resolved via ``AZURE_AI_PROJECT_DEPLOYMENTS``
         indexed by ``cfg.foundry_model_key_for(model_tier)``; if absent,
         the legacy per-tier deployment env var is honoured for tests
         that exercise this seam directly.
    """
    foundry_endpoint = cfg.foundry_endpoint or cfg.endpoint
    if not foundry_endpoint:
        raise ValueError(
            "AZURE_AI_PROJECT_ENDPOINT is not configured; refusing to build an "
            "OpenAIChatClient (spec 036 / ADR-20 hard cutover — Foundry only)."
        )

    model_key = cfg.foundry_model_key_for(model_tier)
    deployment_map = cfg.foundry_deployment_map()
    deployment = deployment_map.get(model_key) or cfg.deployment_for(model_tier)
    if not deployment:
        raise ValueError(
            f"No Foundry deployment is mapped for tier {model_tier!r} (model key {model_key!r}). "
            f"Set AZURE_AI_PROJECT_DEPLOYMENTS='{model_key}=<deployment-name>'."
        )
    return foundry_endpoint, deployment


def build_azure_openai_chat_client(
    *,
    model_tier: str,
    config: LLMClientConfig | None = None,
    middleware: Any = None,
) -> OpenAIChatClient:
    """Build an ``OpenAIChatClient`` configured for Foundry + Entra ID.

    Args:
        model_tier: ``"reasoning"`` or ``"drafting"``; selects the deployment via
            ``LLMClientConfig.foundry_model_key_for(...)``.
        config: optional ``LLMClientConfig`` override (used by tests).
        middleware: optional MAF chat middleware (e.g., the audit middleware
            from T020). Per-Agent middleware is preferred — pass middleware on
            the ``Agent`` constructor instead — but the chat-client level is
            available where token-counting / pre-LLM hooks are needed.

    Raises:
        ValueError: if the Foundry project endpoint is not configured (the
            runtime fails closed rather than fall back to a synthetic / mock
            client), or if the deployment cannot be resolved for the
            requested tier.
    """
    cfg = config or LLMClientConfig()
    endpoint, deployment = _resolve_endpoint_and_deployment(cfg, model_tier)

    logger.info(
        "Building OpenAIChatClient",
        extra={
            "endpoint": endpoint,
            "deployment": deployment,
            "api_version": cfg.api_version,
            "model_tier": model_tier,
        },
    )
    return OpenAIChatClient(
        model=deployment,
        azure_endpoint=endpoint,
        api_version=cfg.api_version,
        credential=_shared_token_provider(),
        middleware=middleware,
    )


__all__ = ["build_azure_openai_chat_client"]

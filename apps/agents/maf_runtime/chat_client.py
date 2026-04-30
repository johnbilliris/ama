"""Shared OpenAIChatClient factory for MAF Agents (T012, ADR-033-01).

All five named MAF Agents back onto ``agent_framework_openai.OpenAIChatClient``
configured against Azure OpenAI with managed identity (Entra ID). API-key
authentication is **forbidden** (FR-025); the factory raises ``ValueError`` if
any code path attempts to pass an ``api_key``.
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
    """Bearer-token callable for the Azure OpenAI cognitive-services scope."""
    return get_bearer_token_provider(_shared_credential(), _AOAI_TOKEN_SCOPE)


def build_azure_openai_chat_client(
    *,
    model_tier: str,
    config: LLMClientConfig | None = None,
    middleware: Any = None,
) -> OpenAIChatClient:
    """Build an ``OpenAIChatClient`` configured for Azure OpenAI + Entra ID.

    Args:
        model_tier: ``"reasoning"`` or ``"drafting"``; selects the deployment via
            ``LLMClientConfig.deployment_for(...)``.
        config: optional ``LLMClientConfig`` override (used by tests).
        middleware: optional MAF chat middleware (e.g., the audit middleware
            from T020). Per-Agent middleware is preferred — pass middleware on
            the ``Agent`` constructor instead — but the chat-client level is
            available where token-counting / pre-LLM hooks are needed.

    Raises:
        ValueError: if ``LLMClientConfig.endpoint`` is empty (no Azure endpoint
            configured); the runtime must fail closed rather than fall back to
            a synthetic / mock client.
    """
    cfg = config or LLMClientConfig()
    if not cfg.endpoint:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT is not configured; refusing to build an OpenAIChatClient. "
            "Set the env var or supply an LLMClientConfig with a non-empty endpoint."
        )

    deployment = cfg.deployment_for(model_tier)
    if not deployment:
        raise ValueError(
            f"AZURE_OPENAI_{model_tier.upper()}_DEPLOYMENT is not configured for tier {model_tier!r}."
        )

    logger.info(
        "Building OpenAIChatClient",
        extra={
            "endpoint": cfg.endpoint,
            "deployment": deployment,
            "api_version": cfg.api_version,
            "model_tier": model_tier,
        },
    )
    return OpenAIChatClient(
        model=deployment,
        azure_endpoint=cfg.endpoint,
        api_version=cfg.api_version,
        credential=_shared_token_provider(),
        middleware=middleware,
    )


__all__ = ["build_azure_openai_chat_client"]

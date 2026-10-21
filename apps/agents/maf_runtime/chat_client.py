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
import uuid
from functools import lru_cache
from typing import Any

from agent_framework import ChatMiddleware, ChatResponse
from agent_framework_openai import OpenAIChatClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from common.inference_observation import (
    RequestObservation,
    observation_correlation_id,
    observe_openai_transport,
    observed_calls,
)
from common.llm_config import FoundryConfigurationError, LLMClientConfig, ResolvedDeployment

logger = logging.getLogger(__name__)

_AOAI_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


class _RequestEvidenceMiddleware(ChatMiddleware):
    """Observe a chat request independently of its enclosing agent/tool outcome."""

    def __init__(self, resolved: ResolvedDeployment) -> None:
        self._resolved = resolved

    async def process(self, context: Any, call_next: Any) -> None:
        calls = observed_calls.get()
        observation = RequestObservation(
            correlation_id=observation_correlation_id.get()
            or (context.metadata or {}).get("audit_correlation_id")
            or uuid.uuid4().hex,
            resolved=self._resolved,
            stamp_header=True,
        )
        observation.observable = observe_openai_transport(getattr(context.client, "client", None))
        from maf_runtime.middleware.audit_middleware import fingerprint

        observation.prompt_sha = fingerprint({"messages": context.messages, "options": context.options})
        recorded = False

        def capture(value: Any, *, terminal: bool = False) -> Any:
            observation.usage(getattr(value, "usage_details", None))
            raw = getattr(value, "raw_representation", None)
            observation.usage(getattr(getattr(raw, "response", raw), "usage", None))
            text = getattr(value, "text", "")
            if isinstance(text, str):
                observation.text += text
            finish = getattr(value, "finish_reason", None)
            status = getattr(getattr(raw, "response", raw), "status", None)
            if str(finish) in ("error", "failed") or status == "failed":
                observation.failed = True
            observed_terminal = (terminal and status not in ("queued", "in_progress")) or bool(finish)
            observation.terminal = observation.terminal or observed_terminal
            return value

        def record() -> None:
            nonlocal recorded
            if recorded:
                return
            recorded = True
            evidence = observation.evidence()
            if calls is not None:
                calls.append(evidence)
            from common.otel_telemetry import record_inference_evidence

            record_inference_evidence(evidence)

        observation.ready = True
        try:
            with observation.bind():
                await call_next()
            if context.stream:
                context.result.with_pull_context_manager(observation.bind)
                context.result.with_transform_hook(capture)
                context.result.with_cleanup_hook(record)
            else:
                capture(context.result, terminal=isinstance(context.result, ChatResponse))
                record()
        except BaseException as exc:
            observation.attach_failure(exc)
            record()
            raise


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


def _resolve_deployment(
    cfg: LLMClientConfig,
    model_tier: str,
) -> ResolvedDeployment:
    """Resolve the captured Foundry target, retaining the public ValueError boundary."""
    try:
        resolved = cfg.deployment_resolver(allow_test_endpoint=True).resolve(model_tier)
    except FoundryConfigurationError as exc:
        raise ValueError(f"Invalid Foundry configuration for tier {model_tier!r}: {exc}") from exc
    return resolved


def build_azure_openai_chat_client(
    *,
    model_tier: str,
    config: LLMClientConfig | None = None,
    middleware: Any = None,
) -> OpenAIChatClient:
    """Build an ``OpenAIChatClient`` configured for Foundry + Entra ID.

    Args:
        model_tier: ``"reasoning"`` or ``"drafting"``; selects the captured tier destination.
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
    resolved = _resolve_deployment(cfg, model_tier)
    endpoint, deployment = resolved.endpoint, resolved.deployment_name
    evidence_middleware = _RequestEvidenceMiddleware(resolved)
    chat_middleware = [evidence_middleware, *(middleware or [])]

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
        middleware=chat_middleware,
    )


__all__ = ["build_azure_openai_chat_client"]

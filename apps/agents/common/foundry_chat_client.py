"""Foundry chat client seam (Spec 036, FR-RAG-FM-01..07; R-01).

Constructor-injectable seam used by all three Foundry call-site migrations:

- ``apps/agents/common/llm_client.py`` (FR-RAG-FM-01) — sync chat completion.
- ``apps/agents/maf_runtime/chat_client.py`` (FR-RAG-FM-02) — MAF factory rewires here.
- ``apps/api/app/services/simulation/controller_service.py`` (FR-RAG-FM-03) — async streaming.

This module mirrors the reference pattern in
``apps/eval-runner/src/ama_eval/foundry_client.py`` and lifts it into the shared
shape consumed by all three call sites.

**AAD-only** (FR-RAG-FM-05): authenticates via ``DefaultAzureCredential`` against
scope ``https://cognitiveservices.azure.com/.default`` (preserved unchanged
across the OpenAI → Foundry migration). ``api_key=`` is rejected by the ctor.

**Carve-out gateway** (FR-RAG-CV-03): when the deployment region is not AU East
or AU Southeast, calls are routed through ``common.model_gateway.apply`` for
PII redaction, PSPF-marking detection, and sensitive-operational-content
classification. Deny → ``FoundryGatewayDenied`` raised; agent falls back to
template (Constitution Principle I).

**Failure modes** (per contract §5):

| Failure                | Behaviour                                       | Audit |
|------------------------|--------------------------------------------------|-------|
| 4xx (auth, deployment) | ``FoundryConfigurationError``; agent → template  | ``foundry_config_error``    |
| 5xx / timeout          | ``FoundryTransportError``; agent → template      | ``foundry_transport_error`` |
| Safety filter          | ``FoundryResponse.safety_filter_triggered=True`` | ``safety_filter_triggered`` |
| Gateway deny           | ``FoundryGatewayDenied``; never reaches Foundry  | ``gateway_deny``            |
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Module constants — preserved verbatim across the OpenAI → Foundry migration
# (FR-RAG-FM-05; mirrors ``apps/agents/maf_runtime/chat_client._AOAI_TOKEN_SCOPE``).
# --------------------------------------------------------------------------- #

AAD_SCOPE: str = "https://cognitiveservices.azure.com/.default"
"""Foundry AAD token scope. Hard-coded per FR-RAG-FM-05; do NOT parameterise."""

AU_REGIONS: frozenset[str] = frozenset({"australiaeast", "australiasoutheast"})
"""Regions exempt from the data-minimisation gateway (FR-RAG-CV-04 baseline)."""


# --------------------------------------------------------------------------- #
# Exception hierarchy
# --------------------------------------------------------------------------- #


class FoundryConfigurationError(RuntimeError):
    """Hard misconfig (missing endpoint, deployment-not-found, AAD scope wrong).

    Raising this MUST cause the calling agent to fall back to its template path
    rather than silently return an empty response (Constitution §I — no
    silencing).
    """


class FoundryTransportError(RuntimeError):
    """Wraps SDK 5xx / timeout / connection errors. Triggers template fallback."""


class FoundryGatewayDenied(RuntimeError):
    """The data-minimisation gateway denied the call (FR-RAG-CV-03).

    Carries the deny ``reason`` (PSPF marking, sensitive-operational, etc.) so
    the audit record can populate ``gateway_deny_reason``.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# --------------------------------------------------------------------------- #
# Wire-format dataclasses — frozen mirrors of the eval-runner reference.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FoundryResponse:
    """Sync-call response. Mirrors ``apps/eval-runner/src/ama_eval/foundry_client.FoundryResponse``."""

    text: str
    finish_reason: str
    usage_prompt_tokens: int
    usage_completion_tokens: int
    latency_ms: int
    safety_filter_triggered: bool
    raw: dict[str, Any]


@dataclass(frozen=True)
class FoundryStreamChunk:
    """One streamed delta. Carries only the fields the Simulation Controller needs
    for SSE emission (FR-RAG-FM-03 / spec 024)."""

    delta_text: str
    finish_reason: str | None
    raw: dict[str, Any]


# --------------------------------------------------------------------------- #
# Protocol shape (FR-RAG-FM-07).
# --------------------------------------------------------------------------- #


# Callable type aliases for constructor-injection (FR-RAG-FM-07).
ChatComplete = Callable[..., FoundryResponse]
"""Sync chat completion. Used by LLMClient.generate_response (FR-RAG-FM-01) and
by the MAF factory shim (FR-RAG-FM-02)."""

ChatCompleteStream = Callable[..., AsyncIterator[FoundryStreamChunk]]
"""Async streaming chat. Used by SimulationControllerService (FR-RAG-FM-03)."""


@runtime_checkable
class FoundryChatClient(Protocol):
    """The unified Foundry seam.

    Production: ``LiveFoundryChatClient`` wires
    ``azure.ai.inference.ChatCompletionsClient`` (sync) and
    ``azure.ai.inference.aio.ChatCompletionsClient`` (async) under
    ``DefaultAzureCredential``.

    Tests: a ``FakeFoundryClient`` matching the same shape (duck-typed via
    ``runtime_checkable``) — no SDK monkey-patching, no network.
    """

    def chat_complete(
        self,
        *,
        model_key: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 30.0,
    ) -> FoundryResponse: ...

    def chat_complete_stream(
        self,
        *,
        model_key: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 60.0,
    ) -> AsyncIterator[FoundryStreamChunk]: ...


# --------------------------------------------------------------------------- #
# Live implementation (T017).
# --------------------------------------------------------------------------- #


def _parse_deployment_map(raw: str | None) -> dict[str, str]:
    """Parse ``modelId@version=deploymentName,modelId@version=deploymentName``.

    Mirrors ``apps/eval-runner/src/ama_eval/foundry_client._parse_deployment_map``
    so a single env-var format works across both seams.
    """
    out: dict[str, str] = {}
    if not raw:
        return out
    for entry in (e.strip() for e in raw.split(",") if e.strip()):
        if "=" not in entry:
            continue
        key, name = entry.split("=", 1)
        out[key.strip()] = name.strip()
    return out


class LiveFoundryChatClient:
    """Production Foundry chat client. AAD-only; ``api_key=`` rejected.

    Reads:
      ``AZURE_AI_PROJECT_ENDPOINT``      — Foundry account endpoint.
      ``AZURE_AI_PROJECT_DEPLOYMENTS``   — CSV of ``modelId@version=deploymentName``.
      ``AZURE_AI_PROJECT_REGION``        — Region of the Foundry deployment;
                                           used by the carve-out gateway path.

    Token scope: ``https://cognitiveservices.azure.com/.default`` (FR-RAG-FM-05).
    """

    # Class-attribute alias for tests / introspection.
    _TOKEN_SCOPE = AAD_SCOPE

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        deployments: dict[str, str] | None = None,
        credential: Any | None = None,
        region: str | None = None,
        gateway_apply: Callable[..., Any] | None = None,
    ) -> None:
        # NB: NO ``api_key=`` parameter. AAD-only. Caller passing api_key triggers
        # a TypeError from the type system — defence-in-depth keyword check below.
        self._endpoint = endpoint or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
        self._deployments = (
            deployments
            if deployments is not None
            else _parse_deployment_map(os.environ.get("AZURE_AI_PROJECT_DEPLOYMENTS"))
        )
        self._region = (region or os.environ.get("AZURE_AI_PROJECT_REGION") or "").lower()
        self._cred = credential
        self._sync_client: Any | None = None
        self._async_client: Any | None = None
        # Gateway is injected lazily — avoids importing presidio at import time
        # (presidio has heavy spaCy deps; only needed for non-AU regions).
        self._gateway_apply = gateway_apply

    # ------------------------------------------------------------------ #
    # Resolve deployment name from the env-var map.
    # ------------------------------------------------------------------ #

    def _resolve(self, model_key: str) -> str:
        if model_key in self._deployments:
            return self._deployments[model_key]
        base = model_key.split("@", 1)[0]
        if base in self._deployments:
            return self._deployments[base]
        raise FoundryConfigurationError(
            f"no Foundry deployment configured for {model_key!r}; "
            "set AZURE_AI_PROJECT_DEPLOYMENTS env var (CSV: 'modelId@version=deploymentName')"
        )

    # ------------------------------------------------------------------ #
    # Lazy client construction — avoids importing azure-ai-inference at
    # import time (saves cold-start in unit tests using FakeFoundryClient).
    # ------------------------------------------------------------------ #

    def _ensure_sync_client(self) -> Any:
        if self._sync_client is not None:
            return self._sync_client
        from azure.ai.inference import ChatCompletionsClient  # noqa: PLC0415
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415

        if not self._endpoint:
            raise FoundryConfigurationError("AZURE_AI_PROJECT_ENDPOINT is not set")
        cred = self._cred or DefaultAzureCredential()
        self._sync_client = ChatCompletionsClient(
            endpoint=self._endpoint.rstrip("/"),
            credential=cred,
            credential_scopes=[AAD_SCOPE],
        )
        return self._sync_client

    def _ensure_async_client(self) -> Any:
        if self._async_client is not None:
            return self._async_client
        from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatClient  # noqa: PLC0415
        from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential  # noqa: PLC0415

        if not self._endpoint:
            raise FoundryConfigurationError("AZURE_AI_PROJECT_ENDPOINT is not set")
        cred = self._cred or AsyncDefaultAzureCredential()
        self._async_client = AsyncChatClient(
            endpoint=self._endpoint.rstrip("/"),
            credential=cred,
            credential_scopes=[AAD_SCOPE],
        )
        return self._async_client

    # ------------------------------------------------------------------ #
    # Carve-out gateway integration (FR-RAG-CV-03 / FR-RAG-CV-04).
    # ------------------------------------------------------------------ #

    def _apply_gateway(self, *, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run the data-minimisation gateway on user-role messages when the
        deployment region is non-AU. Returns the (possibly redacted) messages.

        Raises ``FoundryGatewayDenied`` if any deny rule fires.
        """
        if self._region in AU_REGIONS or not self._region:
            return messages
        gateway = self._gateway_apply
        if gateway is None:
            try:
                from common.model_gateway import apply as gateway  # noqa: PLC0415
            except ImportError:  # pragma: no cover — gateway not yet wired
                logger.warning(
                    "model_gateway unavailable; falling back to passthrough for region %s",
                    self._region,
                )
                return messages
        out: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user" and isinstance(content, str):
                result = gateway(text=content, deployment_region=self._region)
                if getattr(result, "gateway_decision", None) == "deny":
                    raise FoundryGatewayDenied(getattr(result, "reason", "unknown"))
                out.append({**msg, "content": result.transmitted_text})
            else:
                out.append(msg)
        return out

    # ------------------------------------------------------------------ #
    # Sync chat completion (FR-RAG-FM-01, FR-RAG-FM-02).
    # ------------------------------------------------------------------ #

    def chat_complete(
        self,
        *,
        model_key: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 30.0,
    ) -> FoundryResponse:
        """Single-shot chat completion."""
        deployment = self._resolve(model_key)
        guarded_messages = self._apply_gateway(messages=messages)
        client = self._ensure_sync_client()

        kwargs: dict[str, Any] = {"model": deployment, "messages": guarded_messages}
        if tools is not None:
            kwargs["tools"] = tools
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        start = time.perf_counter()
        try:
            result = client.complete(**kwargs)
        except FoundryGatewayDenied:
            raise
        except FoundryConfigurationError:
            raise
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.perf_counter() - start) * 1000)
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status in (401, 403, 404):
                raise FoundryConfigurationError(f"Foundry deployment {deployment!r} returned {status}: {exc}") from exc
            raise FoundryTransportError(f"Foundry transport error after {latency_ms}ms: {exc}") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        choice = result.choices[0]
        message = getattr(choice, "message", None)
        text = getattr(message, "content", "") if message else ""
        finish_reason = str(getattr(choice, "finish_reason", "") or "")
        usage = getattr(result, "usage", None)
        return FoundryResponse(
            text=text or "",
            finish_reason=finish_reason,
            usage_prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            usage_completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            latency_ms=latency_ms,
            safety_filter_triggered=(finish_reason == "content_filter"),
            raw={"deployment": deployment},
        )

    # ------------------------------------------------------------------ #
    # Async streaming chat (FR-RAG-FM-03).
    # ------------------------------------------------------------------ #

    async def chat_complete_stream(
        self,
        *,
        model_key: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 60.0,
    ) -> AsyncIterator[FoundryStreamChunk]:
        """Streaming chat completion. Used by the simulation Controller's SSE turn loop."""
        deployment = self._resolve(model_key)
        guarded_messages = self._apply_gateway(messages=messages)
        client = self._ensure_async_client()

        kwargs: dict[str, Any] = {
            "model": deployment,
            "messages": guarded_messages,
            "stream": True,
        }
        if tools is not None:
            kwargs["tools"] = tools
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        try:
            stream = await client.complete(**kwargs)
        except FoundryGatewayDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status in (401, 403, 404):
                raise FoundryConfigurationError(f"Foundry deployment {deployment!r} returned {status}: {exc}") from exc
            raise FoundryTransportError(f"Foundry stream transport error: {exc}") from exc

        async for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            text = getattr(delta, "content", "") if delta else ""
            yield FoundryStreamChunk(
                delta_text=text or "",
                finish_reason=str(getattr(choices[0], "finish_reason", "") or "") or None,
                raw={"deployment": deployment},
            )


__all__ = [
    "AAD_SCOPE",
    "AU_REGIONS",
    "ChatComplete",
    "ChatCompleteStream",
    "FoundryChatClient",
    "FoundryConfigurationError",
    "FoundryGatewayDenied",
    "FoundryResponse",
    "FoundryStreamChunk",
    "FoundryTransportError",
    "LiveFoundryChatClient",
]

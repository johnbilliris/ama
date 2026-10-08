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

import asyncio
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


def _uuid_hex() -> str:
    """Spec 036 / F-A11 / T235 — fallback correlation id when caller omits one."""
    return uuid.uuid4().hex


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
    deployment_id: str
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
        correlation_id: str | None = None,
    ) -> AsyncIterator[FoundryStreamChunk]: ...


# --------------------------------------------------------------------------- #
# Live implementation (T017).
# --------------------------------------------------------------------------- #


def _parse_deployment_map(raw: str | None) -> dict[str, str]:
    """Parse ``modelId@version=deploymentName,modelId@version=deploymentName``.

    Mirrors ``apps/eval-runner/src/ama_eval/foundry_client._parse_deployment_map``
    so a single env-var format works across both seams.

    First-write-wins: when multiple entries share the same key (e.g. when
    Bicep collapses reasoning/drafting/simulation tiers onto the same
    ``modelName@version``) the FIRST entry in the CSV is preserved. This
    keeps lookups deterministic and matches the simulation Controller's
    own ``_resolve_simulation_deployment`` semantics. Callers that need a
    specific tier should resolve it via the per-tier
    ``AZURE_AI_<TIER>_DEPLOYMENT`` env var instead.
    """
    out: dict[str, str] = {}
    if not raw:
        return out
    for entry in (e.strip() for e in raw.split(",") if e.strip()):
        if "=" not in entry:
            continue
        key, name = entry.split("=", 1)
        out.setdefault(key.strip(), name.strip())
    return out


class LiveFoundryChatClient:
    """Production Foundry chat client. AAD-only; ``api_key=`` rejected.

    Reads:
      ``AZURE_AI_PROJECT_ENDPOINT``      — Foundry account endpoint.
      ``AZURE_AI_PROJECT_DEPLOYMENTS``   — CSV of ``modelId@version=deploymentName``.
      ``AZURE_AI_PROJECT_REGION``        — Region of the Foundry deployment;
                                           used by the carve-out gateway path.

    Token scope: ``https://cognitiveservices.azure.com/.default`` (FR-RAG-FM-05).

    Endpoint shapes
    ---------------
    Two endpoint shapes are supported transparently:

    * **Native Foundry project** (``*.services.ai.azure.com``,
      ``*.inference.ml.azure.com``) — a single ``ChatCompletionsClient``
      bound to the project endpoint handles every deployment; ``model=``
      selects which one. Typed ``max_tokens`` is honoured.
    * **Azure-OpenAI cognitive-services** (``*.cognitiveservices.azure.com``,
      ``*.openai.azure.com``) — the inference SDK requires
      ``/openai/deployments/<name>`` in the URL. A per-deployment client
      is constructed (and cached) automatically. The ``max_completion_tokens``
      parameter required by GPT-5+ family models is forwarded via the SDK's
      ``model_extras`` passthrough.
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
        # Spec 036 / FR-RAG-FM-01 — clients are cached *per resolved
        # endpoint URL*. For Azure-OpenAI-kind cognitive-services accounts
        # the inference SDK requires the URL to include
        # ``/openai/deployments/<name>`` (without it the client POSTs to
        # ``{endpoint}/chat/completions`` which 404s on AOAI). Per-deployment
        # caches keep each ChatCompletionsClient pointed at the right route
        # while still avoiding per-call client construction.
        self._sync_clients: dict[str, Any] = {}
        self._async_clients: dict[str, Any] = {}
        # Gateway is injected lazily — avoids importing presidio at import time
        # (presidio has heavy spaCy deps; only needed for non-AU regions).
        self._gateway_apply = gateway_apply

    # ------------------------------------------------------------------ #
    # Resolve deployment name from the env-var map.
    # ------------------------------------------------------------------ #

    # Recognised tier aliases — when ``model_key`` matches one of these the
    # resolver checks ``AZURE_AI_<TIER>_DEPLOYMENT`` env vars first. This
    # lets callers express "give me the simulation-tier deployment" without
    # having to know whether the CSV map distinguishes that tier (it
    # currently can't — multiple tiers collapse onto the same
    # ``<modelName>@<version>`` key when they share a model).
    _TIER_ALIASES: frozenset[str] = frozenset({"reasoning", "drafting", "simulation", "embedding"})

    def _resolve(self, model_key: str) -> str:
        if model_key in self._deployments:
            return self._deployments[model_key]
        if model_key in self._TIER_ALIASES:
            env_name = f"AZURE_AI_{model_key.upper()}_DEPLOYMENT"
            override = os.environ.get(env_name)
            if override:
                return override
        base = model_key.split("@", 1)[0]
        if base in self._deployments:
            return self._deployments[base]
        raise FoundryConfigurationError(
            f"no Foundry deployment configured for {model_key!r}; "
            "set AZURE_AI_PROJECT_DEPLOYMENTS env var (CSV: 'modelId@version=deploymentName') "
            "or AZURE_AI_<TIER>_DEPLOYMENT for tier names ('reasoning', 'simulation', ...)"
        )

    # ------------------------------------------------------------------ #
    # Endpoint URL shaping — distinguishes Azure-OpenAI cognitive-services
    # accounts (which require ``/openai/deployments/<name>`` in the URL)
    # from native Foundry project endpoints (which accept the bare host).
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_aoai_endpoint(endpoint: str) -> bool:
        """Detect Azure-OpenAI / cognitive-services style endpoints.

        Returns ``True`` for hosts ending in ``cognitiveservices.azure.com``
        or ``openai.azure.com``. Native Foundry project endpoints (e.g.
        ``*.services.ai.azure.com`` or ``*.inference.ml.azure.com``) return
        ``False`` and use the existing inference-SDK URL pattern.
        """
        host = endpoint.lower()
        return ".cognitiveservices.azure.com" in host or ".openai.azure.com" in host

    def _endpoint_for(self, deployment: str) -> str:
        """Compose the inference-SDK endpoint URL for a given deployment."""
        if not self._endpoint:
            raise FoundryConfigurationError("AZURE_AI_PROJECT_ENDPOINT is not set")
        base = self._endpoint.rstrip("/")
        if self._is_aoai_endpoint(base) and "/openai/deployments/" not in base:
            return f"{base}/openai/deployments/{deployment}"
        return base

    # ------------------------------------------------------------------ #
    # Lazy client construction — avoids importing azure-ai-inference at
    # import time (saves cold-start in unit tests using FakeFoundryClient).
    # ------------------------------------------------------------------ #

    def _ensure_sync_client(self, deployment: str) -> Any:
        url = self._endpoint_for(deployment)
        cached = self._sync_clients.get(url)
        if cached is not None:
            return cached
        from azure.ai.inference import ChatCompletionsClient  # noqa: PLC0415
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415

        cred = self._cred or DefaultAzureCredential()
        client = ChatCompletionsClient(
            endpoint=url,
            credential=cred,
            credential_scopes=[AAD_SCOPE],
        )
        self._sync_clients[url] = client
        return client

    def _ensure_async_client(self, deployment: str) -> Any:
        url = self._endpoint_for(deployment)
        cached = self._async_clients.get(url)
        if cached is not None:
            return cached
        from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatClient  # noqa: PLC0415
        from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential  # noqa: PLC0415

        cred = self._cred or AsyncDefaultAzureCredential()
        client = AsyncChatClient(
            endpoint=url,
            credential=cred,
            credential_scopes=[AAD_SCOPE],
        )
        self._async_clients[url] = client
        return client

    # ------------------------------------------------------------------ #
    # Carve-out gateway integration (FR-RAG-CV-03 / FR-RAG-CV-04).
    # ------------------------------------------------------------------ #

    def _apply_gateway(self, *, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run the data-minimisation gateway on supported text-bearing content.

        For AU regions the gateway is explicitly bypassed.
        For non-AU regions, every supported text payload is inspected and
        redacted/denied before dispatch.

        Raises ``FoundryGatewayDenied`` if any deny rule fires.
        """
        if self._region in AU_REGIONS:
            return messages

        if not self._region:
            raise FoundryConfigurationError("AZURE_AI_PROJECT_REGION is required for non-AU gateway enforcement")

        gateway = self._load_gateway()
        out: list[dict[str, Any]] = []
        for msg in messages:
            out.append(self._apply_gateway_to_message(msg=msg, gateway=gateway))
        return out

    def _load_gateway(self) -> Callable[..., Any]:
        gateway = self._gateway_apply
        if gateway is not None:
            return gateway
        try:
            from common.model_gateway import apply as resolved_gateway  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover — dependency edge
            raise FoundryConfigurationError("model_gateway is required for non-AU requests") from exc
        self._gateway_apply = resolved_gateway
        return resolved_gateway

    def _apply_gateway_to_message(self, *, msg: dict[str, Any], gateway: Callable[..., Any]) -> dict[str, Any]:
        transformed = dict(msg)
        if "content" in transformed:
            transformed["content"] = self._apply_gateway_to_content(
                content=transformed["content"],
                gateway=gateway,
            )
        return transformed

    def _apply_gateway_to_content(self, *, content: Any, gateway: Callable[..., Any]) -> Any:
        if isinstance(content, str):
            return self._apply_gateway_to_text(content=content, gateway=gateway)

        if isinstance(content, list):
            rewritten: list[Any] = []
            for item in content:
                if isinstance(item, dict):
                    updated = dict(item)
                    text_value = updated.get("text")
                    if isinstance(text_value, str):
                        updated["text"] = self._apply_gateway_to_text(content=text_value, gateway=gateway)
                    rewritten.append(updated)
                elif isinstance(item, str):
                    rewritten.append(self._apply_gateway_to_text(content=item, gateway=gateway))
                else:
                    rewritten.append(item)
            return rewritten

        return content

    def _apply_gateway_to_text(self, *, content: str, gateway: Callable[..., Any]) -> str:
        result = gateway(text=content, deployment_region=self._region)
        if getattr(result, "gateway_decision", None) == "deny":
            raise FoundryGatewayDenied(getattr(result, "reason", "unknown"))
        return str(getattr(result, "transmitted_text", content))

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
        correlation_id: str | None = None,
    ) -> FoundryResponse:
        """Single-shot chat completion."""
        deployment = self._resolve(model_key)
        guarded_messages = self._apply_gateway(messages=messages)
        client = self._ensure_sync_client(deployment)

        kwargs: dict[str, Any] = {"model": deployment, "messages": guarded_messages}
        kwargs["timeout"] = timeout_s
        if tools is not None:
            kwargs["tools"] = tools
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            # GPT-5+ family deployments reject ``max_tokens`` and require
            # ``max_completion_tokens``. The inference SDK only types
            # ``max_tokens`` natively; surface the new parameter via the
            # SDK's ``model_extras`` passthrough for AOAI deployments where
            # the newer parameter is mandatory. Native Foundry endpoints
            # keep the typed ``max_tokens`` for backwards compat.
            if self._endpoint and self._is_aoai_endpoint(self._endpoint):
                kwargs["model_extras"] = {"max_completion_tokens": max_tokens}
            else:
                kwargs["max_tokens"] = max_tokens

        # Spec 036 / F-A11 / T235 — emit foundry.inference OTel span. The
        # correlation_id stitches this span back to the surrounding
        # retrieval.retrieve span so end-to-end SLO + retrieval-only SLO
        # are independently observable (Pass 1 Q-P1-06 + SC-012).
        from common.otel_telemetry import foundry_inference_span  # noqa: PLC0415

        cid = correlation_id or _uuid_hex()
        with foundry_inference_span(correlation_id=cid, model_id=deployment):
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
                if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
                    raise FoundryTransportError(
                        f"Foundry timeout after {latency_ms}ms (limit={timeout_s}s): {exc}"
                    ) from exc
                if status in (401, 403, 404):
                    raise FoundryConfigurationError(
                        f"Foundry deployment {deployment!r} returned {status}: {exc}"
                    ) from exc
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
            deployment_id=deployment,
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
        correlation_id: str | None = None,
    ) -> AsyncIterator[FoundryStreamChunk]:
        """Streaming chat completion. Used by the simulation Controller's SSE turn loop."""
        _ = correlation_id
        deployment = self._resolve(model_key)
        guarded_messages = self._apply_gateway(messages=messages)
        client = self._ensure_async_client(deployment)

        kwargs: dict[str, Any] = {
            "model": deployment,
            "messages": guarded_messages,
            "stream": True,
        }
        kwargs["timeout"] = timeout_s
        if tools is not None:
            kwargs["tools"] = tools
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            # See chat_complete for the AOAI ``max_completion_tokens``
            # parameter rename. Mirrored here to keep streaming behaviour
            # consistent with single-shot calls.
            if self._endpoint and self._is_aoai_endpoint(self._endpoint):
                kwargs["model_extras"] = {"max_completion_tokens": max_tokens}
            else:
                kwargs["max_tokens"] = max_tokens

        deadline = time.monotonic() + timeout_s
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FoundryTransportError("Foundry stream deadline exceeded before dispatch")
            stream = await asyncio.wait_for(client.complete(**kwargs), timeout=remaining)
        except FoundryGatewayDenied:
            raise
        except TimeoutError as exc:
            raise FoundryTransportError(f"Foundry stream timeout after {timeout_s}s") from exc
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status in (401, 403, 404):
                raise FoundryConfigurationError(f"Foundry deployment {deployment!r} returned {status}: {exc}") from exc
            raise FoundryTransportError(f"Foundry stream transport error: {exc}") from exc

        iterator = stream.__aiter__()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FoundryTransportError(f"Foundry stream timeout after {timeout_s}s")
            try:
                chunk = await asyncio.wait_for(iterator.__anext__(), timeout=remaining)
            except StopAsyncIteration:
                break
            except TimeoutError as exc:
                raise FoundryTransportError(f"Foundry stream timeout after {timeout_s}s") from exc

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

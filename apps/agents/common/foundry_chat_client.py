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
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable
from urllib.parse import urlsplit

from common.llm_config import DeploymentResolver, ResolvedDeployment, normalize_foundry_endpoint, parse_deployment_map
from common.llm_config import FoundryConfigurationError as FoundryConfigurationError

if TYPE_CHECKING:
    from common.inference_observation import RequestObservation


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
class InferenceAttemptEvidence:
    """Request-local evidence container; adapters must prove transport submission.

    Configuration, SDK entry and agent correlation alone leave the default
    unknown state intact. This scaffolding does not emit audit/usage records.
    """

    call_id: str
    correlation_id: str
    resolved_identity: ResolvedDeployment | None = None
    inference_attempted: bool | None = None
    inference_outcome: Literal["succeeded", "failed", "not_attempted", "unknown"] | None = "unknown"
    error_code: str | None = None
    usage_prompt_tokens: int | None = None
    usage_completion_tokens: int | None = None
    latency_ms: int | None = None
    output_text_hash: str | None = None
    prompt_sha: str | None = None

    def __post_init__(self) -> None:
        if not self.call_id.strip() or not self.correlation_id.strip():
            raise ValueError("call_id and correlation_id must be non-empty strings")
        if self.inference_attempted is not None and type(self.inference_attempted) is not bool:
            raise ValueError("inference_attempted must be boolean or null")
        if self.inference_outcome not in ("succeeded", "failed", "not_attempted", "unknown", None):
            raise ValueError("Invalid inference_outcome")
        if self.inference_outcome in ("succeeded", "failed") and self.inference_attempted is not True:
            raise ValueError("Terminal inference outcome requires submission evidence")
        if self.inference_outcome == "not_attempted" and self.inference_attempted is not False:
            raise ValueError("not_attempted requires known non-submission")
        if self.inference_attempted is False and self.inference_outcome not in ("not_attempted", "unknown", None):
            raise ValueError("Non-submitted request cannot claim an inference outcome")


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
    attempt_evidence: InferenceAttemptEvidence | None = None


@dataclass(frozen=True)
class FoundryStreamChunk:
    """One streamed delta. Carries only the fields the Simulation Controller needs
    for SSE emission (FR-RAG-FM-03 / spec 024)."""

    delta_text: str
    finish_reason: str | None
    raw: dict[str, Any]
    attempt_evidence: InferenceAttemptEvidence | None = None


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
    """Validate the shared compatibility grammar before creating a lookup."""
    return parse_deployment_map(raw)


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
        resolver: DeploymentResolver | None = None,
    ) -> None:
        # NB: NO ``api_key=`` parameter. AAD-only. Caller passing api_key triggers
        # a TypeError from the type system — defence-in-depth keyword check below.
        if resolver is None:
            settings = dict(os.environ)
            if endpoint is not None:
                settings["AZURE_AI_PROJECT_ENDPOINT"] = endpoint
            if region is not None:
                settings["AZURE_AI_PROJECT_REGION"] = region
            resolver = DeploymentResolver.from_environment(
                settings, configuration_revision="foundry-client-snapshot", deployments=deployments
            )
        elif deployments is not None or endpoint is not None or region is not None:
            raise FoundryConfigurationError("Supply a resolver snapshot or connection overrides, not both")
        self._resolver = resolver
        self._endpoint = (
            resolver.configuration.endpoint.strip() if resolver.configuration.endpoint is not None else None
        )
        self._region = (resolver.configuration.region or "").lower()
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

    def _resolve(self, model_key: str) -> str:
        return self._resolver.resolve_legacy(model_key).deployment_name

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
        host = urlsplit(endpoint).hostname or ""
        return host.endswith((".cognitiveservices.azure.com", ".openai.azure.com"))

    def _endpoint_for(self, deployment: str) -> str:
        """Compose the inference-SDK endpoint URL for a given deployment."""
        if not self._endpoint:
            raise FoundryConfigurationError("AZURE_AI_PROJECT_ENDPOINT is not set")
        base = normalize_foundry_endpoint(self._endpoint).rstrip("/")
        if self._is_aoai_endpoint(base):
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
        """Complete one request, retaining evidence even across exception translation."""
        from common.inference_observation import RequestObservation

        observation = RequestObservation(correlation_id=correlation_id or _uuid_hex())
        try:
            with observation.bind():
                return self._chat_complete(
                    observation=observation,
                    model_key=model_key,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout_s=timeout_s,
                    correlation_id=correlation_id,
                )
        except BaseException as exc:
            observation.attach_failure(exc)
            raise

    def _chat_complete(
        self,
        *,
        model_key: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 30.0,
        correlation_id: str | None = None,
        observation: RequestObservation,
    ) -> FoundryResponse:
        """Single-shot chat completion."""
        resolved = self._resolver.resolve_legacy(model_key)
        observation.resolved = resolved
        deployment = resolved.deployment_name
        guarded_messages = self._apply_gateway(messages=messages)
        client = self._ensure_sync_client(deployment)
        from common.inference_observation import observe_azure_transport

        observation.observable = observe_azure_transport(client)

        kwargs: dict[str, Any] = {"model": deployment, "messages": guarded_messages}
        kwargs["timeout"] = timeout_s
        kwargs["headers"] = {"x-ms-client-request-id": observation.call_id}
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

        cid = observation.correlation_id
        with foundry_inference_span(
            correlation_id=cid,
            model_id=resolved.model_id,
            model_version=resolved.model_version,
            deployment_alias=deployment,
        ) as span:
            start = time.perf_counter()
            try:
                observation.ready = True
                result = client.complete(**kwargs)
                observation.usage(getattr(result, "usage", None))
                observation.terminal = True
            except FoundryGatewayDenied:
                raise
            except FoundryConfigurationError:
                raise
            except Exception as exc:  # noqa: BLE001
                observation.attach_failure(exc)
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
            finally:
                evidence = observation.evidence()
                span.attributes.update(
                    call_id=evidence.call_id,
                    inference_attempted=evidence.inference_attempted,
                    inference_outcome=evidence.inference_outcome,
                    usage_prompt_tokens=evidence.usage_prompt_tokens,
                    usage_completion_tokens=evidence.usage_completion_tokens,
                )

            latency_ms = int((time.perf_counter() - start) * 1000)
        choice = result.choices[0]
        message = getattr(choice, "message", None)
        text = getattr(message, "content", "") if message else ""
        finish = getattr(choice, "finish_reason", "") or ""
        finish_reason = str(getattr(finish, "value", finish))
        usage = getattr(result, "usage", None)
        observation.usage(usage)
        observation.text = text or ""
        observation.terminal = True
        return FoundryResponse(
            text=text or "",
            finish_reason=finish_reason,
            usage_prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            usage_completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            latency_ms=latency_ms,
            safety_filter_triggered=(finish_reason == "content_filter"),
            deployment_id=deployment,
            raw={"deployment": deployment},
            attempt_evidence=observation.evidence(),
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
        """Stream one request; preserve partial observations on failure/cancellation."""
        from common.inference_observation import RequestObservation

        observation = RequestObservation(correlation_id=correlation_id or _uuid_hex())
        chunks = self._chat_complete_stream(
            observation=observation,
            model_key=model_key,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            correlation_id=correlation_id,
        )
        try:
            async for chunk in chunks:
                yield chunk
        except BaseException as exc:
            observation.attach_failure(exc)
            raise
        finally:
            await chunks.aclose()
            from common.otel_telemetry import record_inference_evidence

            record_inference_evidence(observation.evidence())

    async def _chat_complete_stream(
        self,
        *,
        model_key: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 60.0,
        correlation_id: str | None = None,
        observation: RequestObservation,
    ) -> AsyncGenerator[FoundryStreamChunk, None]:
        """Streaming chat completion. Used by the simulation Controller's SSE turn loop."""
        resolved = self._resolver.resolve_legacy(model_key)
        observation.resolved = resolved
        deployment = resolved.deployment_name
        guarded_messages = self._apply_gateway(messages=messages)
        client = self._ensure_async_client(deployment)
        from common.inference_observation import observe_azure_transport

        observation.observable = observe_azure_transport(client, asynchronous=True)

        kwargs: dict[str, Any] = {
            "model": deployment,
            "messages": guarded_messages,
            "stream": True,
        }
        kwargs["timeout"] = timeout_s
        kwargs["headers"] = {"x-ms-client-request-id": observation.call_id}
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
            observation.ready = True
            with observation.bind():
                stream = await asyncio.wait_for(client.complete(**kwargs), timeout=remaining)
        except FoundryGatewayDenied:
            raise
        except TimeoutError as exc:
            observation.attach_failure(exc)
            raise FoundryTransportError(f"Foundry stream timeout after {timeout_s}s") from exc
        except Exception as exc:  # noqa: BLE001
            observation.attach_failure(exc)
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
                with observation.bind():
                    chunk = await asyncio.wait_for(iterator.__anext__(), timeout=remaining)
            except StopAsyncIteration:
                break
            except TimeoutError as exc:
                raise FoundryTransportError(f"Foundry stream timeout after {timeout_s}s") from exc

            observation.usage(getattr(chunk, "usage", None))
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                if getattr(chunk, "usage", None) is not None:
                    yield FoundryStreamChunk(
                        delta_text="",
                        finish_reason=None,
                        raw={"deployment": deployment},
                        attempt_evidence=observation.evidence(),
                    )
                continue
            delta = getattr(choices[0], "delta", None)
            text = getattr(delta, "content", "") if delta else ""
            observation.text += text or ""
            finish = getattr(choices[0], "finish_reason", None)
            finish_reason = str(getattr(finish, "value", finish)) if finish else None
            observation.terminal = observation.terminal or bool(finish_reason)
            yield FoundryStreamChunk(
                delta_text=text or "",
                finish_reason=finish_reason,
                raw={"deployment": deployment},
                attempt_evidence=observation.evidence(),
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

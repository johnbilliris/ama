"""Foundry client wrapper for the eval-runner.

Wraps Azure AI Projects SDK for inference + evaluation. Designed so unit tests
can substitute a fake by injecting a different `chat_complete` callable.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class FoundryConfigurationError(RuntimeError):
    """Raised when the Foundry endpoint or deployment registry is misconfigured.

    This is a hard failure — the run cannot proceed because every model call
    would otherwise silently return an empty response, masking the misconfig
    behind a degenerate scorecard.
    """


@dataclass(frozen=True)
class FoundryResponse:
    text: str
    finish_reason: str
    usage_prompt_tokens: int
    usage_completion_tokens: int
    latency_ms: int
    safety_filter_triggered: bool
    raw: dict[str, Any]


def _parse_deployment_map(raw: str | None) -> dict[str, str]:
    """Parse ``modelKey=deploymentName,modelKey=deploymentName`` into a dict.

    Accepted modelKey shapes (matched in this order):
    - ``modelId@version`` (preferred — matches ``ModelUnderTest`` registry)
    - ``modelId`` (version-agnostic fallback)
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


class FoundryClient:
    """Minimal Foundry chat client.

    In production reads ``AZURE_AI_PROJECT_ENDPOINT`` (Foundry account endpoint)
    and ``AZURE_AI_PROJECT_DEPLOYMENTS`` (CSV of ``modelId@version=deploymentName``)
    and uses ``DefaultAzureCredential`` for AAD auth. For tests, pass
    ``chat_complete=`` callable that returns a ``FoundryResponse``.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_key: str | None = None,
        chat_complete: Callable[..., FoundryResponse] | None = None,
        deployments: dict[str, str] | None = None,
    ) -> None:
        self._endpoint = endpoint or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
        self._api_key = api_key
        self._fake = chat_complete
        self._client: Any | None = None
        self._deployments = (
            deployments
            if deployments is not None
            else _parse_deployment_map(
                os.environ.get("AZURE_AI_PROJECT_DEPLOYMENTS"),
            )
        )

    def deployment_for(self, model_id: str, version: str | None = None) -> str | None:
        """Return the configured deployment name for ``modelId@version`` or ``modelId``."""
        if version:
            key = f"{model_id}@{version}"
            if key in self._deployments:
                return self._deployments[key]
        return self._deployments.get(model_id)

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        if self._fake is not None:
            return None
        from azure.ai.inference import ChatCompletionsClient  # noqa: PLC0415
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415

        if not self._endpoint:
            raise FoundryConfigurationError(
                "AZURE_AI_PROJECT_ENDPOINT is not set; the eval runner cannot reach a Foundry endpoint",
            )
        if not self._deployments:
            raise FoundryConfigurationError(
                "AZURE_AI_PROJECT_DEPLOYMENTS is not set; the eval runner has no deployment to invoke",
            )
        cred = DefaultAzureCredential()
        # Foundry / AOAI endpoints expose Inference at /openai/deployments under the same hostname.
        endpoint = self._endpoint.rstrip("/")
        self._client = ChatCompletionsClient(endpoint=f"{endpoint}/openai", credential=cred)
        return self._client

    def complete(
        self,
        *,
        model_id: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout_seconds: float = 120.0,
        deployment: str | None = None,
        version: str | None = None,
    ) -> FoundryResponse:
        if self._fake is not None:
            return self._fake(
                model_id=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
                deployment=deployment,
            )

        client = self._ensure_client()
        deployment_name = deployment or self.deployment_for(model_id, version)
        if not deployment_name:
            raise FoundryConfigurationError(
                f"no Foundry deployment configured for model {model_id!r} (version={version!r}); "
                "set AZURE_AI_PROJECT_DEPLOYMENTS or pass deployment= explicitly",
            )

        start = time.perf_counter()
        try:
            result = client.complete(
                model=deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            choice = result.choices[0]
            content = choice.message.content if hasattr(choice, "message") else ""
            usage = getattr(result, "usage", None)
            safety_triggered = str(getattr(choice, "finish_reason", "")) == "content_filter"
            return FoundryResponse(
                text=content or "",
                finish_reason=str(getattr(choice, "finish_reason", "")),
                usage_prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                usage_completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                latency_ms=latency_ms,
                safety_filter_triggered=safety_triggered,
                raw={},
            )
        except FoundryConfigurationError:
            raise
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.warning("Foundry chat completion failed for deployment %s: %s", deployment_name, exc)
            return FoundryResponse(
                text="",
                finish_reason="error",
                usage_prompt_tokens=0,
                usage_completion_tokens=0,
                latency_ms=latency_ms,
                safety_filter_triggered=False,
                raw={"error": str(exc), "deployment": deployment_name},
            )


__all__ = ["FoundryClient", "FoundryConfigurationError", "FoundryResponse"]

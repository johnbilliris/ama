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
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

MAX_INFERENCE_REQUESTS_PER_MINUTE = 8
MAX_RATE_LIMIT_RETRIES = 2
REQUEST_INTERVAL_SECONDS = 60 / MAX_INFERENCE_REQUESTS_PER_MINUTE


class FoundryConfigurationError(RuntimeError):
    """Raised when the Foundry inference endpoint or deployment registry is misconfigured.

    This is a hard failure — the run cannot proceed because every model call
    would otherwise silently return an empty response, masking the misconfig
    behind a degenerate scorecard.
    """


class FoundryInferenceError(RuntimeError):
    """Raised when a configured Foundry model deployment cannot complete a request."""


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

    In production reads ``AZURE_AI_INFERENCE_ENDPOINT`` (Azure AI Model Inference endpoint)
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
        self._endpoint = endpoint or os.environ.get("AZURE_AI_INFERENCE_ENDPOINT")
        self._api_key = api_key
        self._fake = chat_complete
        self._client: Any | None = None
        self._request_rate_lock = Lock()
        self._next_request_at = 0.0
        self._deployments = (
            deployments
            if deployments is not None
            else _parse_deployment_map(
                os.environ.get("AZURE_AI_PROJECT_DEPLOYMENTS"),
            )
        )

    @staticmethod
    def _is_content_filter_error(exc: Exception) -> bool:
        message = str(exc).casefold()
        return "content_filter" in message or "responsibleaipolicyviolation" in message

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
                "AZURE_AI_INFERENCE_ENDPOINT is not set; the eval runner cannot reach a Foundry inference endpoint",
            )
        if not self._deployments:
            raise FoundryConfigurationError(
                "AZURE_AI_PROJECT_DEPLOYMENTS is not set; the eval runner has no deployment to invoke",
            )
        cred = DefaultAzureCredential()
        self._client = ChatCompletionsClient(
            endpoint=self._endpoint.rstrip("/"),
            credential=cred,
            credential_scopes=["https://cognitiveservices.azure.com/.default"],
        )
        return self._client

    def _wait_for_request_slot(self) -> None:
        with self._request_rate_lock:
            now = time.monotonic()
            delay = max(0.0, self._next_request_at - now)
            self._next_request_at = max(now, self._next_request_at) + REQUEST_INTERVAL_SECONDS
        if delay:
            time.sleep(delay)

    @staticmethod
    def _retry_after_seconds(exc: Exception, attempt: int) -> float:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", {})
        retry_after_ms = headers.get("retry-after-ms") if hasattr(headers, "get") else None
        retry_after = headers.get("Retry-After") if hasattr(headers, "get") else None
        try:
            if retry_after_ms is not None:
                return min(60.0, max(REQUEST_INTERVAL_SECONDS, float(retry_after_ms) / 1000))
            if retry_after is not None:
                return min(60.0, max(REQUEST_INTERVAL_SECONDS, float(retry_after)))
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid Foundry Retry-After header: %r", retry_after_ms or retry_after)
        return min(60.0, REQUEST_INTERVAL_SECONDS * (attempt + 1))

    def complete(
        self,
        *,
        model_id: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
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
            result: Any | None = None
            for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
                self._wait_for_request_slot()
                try:
                    if model_id.casefold().startswith("gpt-5"):
                        result = client.complete(
                            model=deployment_name,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=None,
                            model_extras={"max_completion_tokens": max_tokens},
                        )
                    else:
                        result = client.complete(
                            model=deployment_name,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                    break
                except Exception as exc:
                    if self._is_content_filter_error(exc):
                        logger.warning(
                            "Foundry content filter blocked a response for deployment %s",
                            deployment_name,
                        )
                        return FoundryResponse(
                            text="",
                            finish_reason="content_filter",
                            usage_prompt_tokens=0,
                            usage_completion_tokens=0,
                            latency_ms=int((time.perf_counter() - start) * 1000),
                            safety_filter_triggered=True,
                            raw={"errorCode": "content_filter"},
                        )
                    if getattr(exc, "status_code", None) != 429 or attempt >= MAX_RATE_LIMIT_RETRIES:
                        raise
                    retry_delay = self._retry_after_seconds(exc, attempt)
                    logger.warning(
                        "Foundry rate limited deployment %s; retrying attempt %s/%s after %.1fs",
                        deployment_name,
                        attempt + 1,
                        MAX_RATE_LIMIT_RETRIES,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
            if result is None:
                raise RuntimeError("Foundry request retry loop produced no response")
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
            logger.exception("Foundry chat completion failed for deployment %s", deployment_name)
            raise FoundryInferenceError(
                f"Foundry chat completion failed for deployment {deployment_name}",
            ) from exc


__all__ = ["FoundryClient", "FoundryConfigurationError", "FoundryInferenceError", "FoundryResponse"]

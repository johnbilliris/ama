"""Request-local evidence at the installed SDKs' outbound transport boundary."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import unquote, urlsplit

from common.foundry_chat_client import InferenceAttemptEvidence
from common.llm_config import ResolvedDeployment

_active_request: ContextVar[RequestObservation | None] = ContextVar("inference_request", default=None)
observed_calls: ContextVar[list[InferenceAttemptEvidence] | None] = ContextVar("inference_calls", default=None)
observation_correlation_id: ContextVar[str | None] = ContextVar("inference_correlation", default=None)


@contextmanager
def collect_inference_calls() -> Iterator[list[InferenceAttemptEvidence]]:
    """Capture request evidence without changing inference writer ownership."""
    calls: list[InferenceAttemptEvidence] = []
    token = observed_calls.set(calls)
    try:
        yield calls
    finally:
        observed_calls.reset(token)


@dataclass
class RequestObservation:
    """Collect only observed transport, usage and completion signals for one call."""

    correlation_id: str
    resolved: ResolvedDeployment | None = None
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    observable: bool = False
    transport_seen: bool = False
    submitted: bool = False
    ready: bool = False
    stamp_header: bool = False
    terminal: bool = False
    failed: bool = False
    local_failure: bool = False
    error_code: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    text: str = ""
    prompt_sha: str | None = None
    started: float = field(default_factory=time.perf_counter)

    def handoff(self, request: Any) -> None:
        """Match serialized call ID, destination and model before marking submission."""
        self.transport_seen = True
        if self.resolved is None:
            return
        headers = request.headers
        if self.stamp_header:
            headers["x-ms-client-request-id"] = self.call_id
        request_id = headers.get("x-ms-client-request-id")
        if request_id != self.call_id:
            return
        url = urlsplit(str(request.url))
        endpoint = urlsplit(self.resolved.endpoint)
        if (url.scheme, url.netloc) != (endpoint.scheme, endpoint.netloc):
            return
        if "/openai/deployments/" in url.path:
            destination = url.path.split("/openai/deployments/", 1)[1].split("/", 1)[0]
            if unquote(destination) != self.resolved.deployment_name:
                return
        body = getattr(request, "body", None)
        if body is None:
            body = getattr(request, "content", None)
        if not isinstance(body, (str, bytes, bytearray)):
            return
        try:
            payload = json.loads(body)
        except (TypeError, ValueError):
            return
        if not isinstance(payload, dict) or payload.get("model") != self.resolved.deployment_name:
            return
        self.submitted = True

    def usage(self, usage: Any) -> None:
        if usage is None:
            return
        for target, names in (
            ("prompt_tokens", ("prompt_tokens", "input_tokens", "input_token_count")),
            ("completion_tokens", ("completion_tokens", "output_tokens", "output_token_count")),
        ):
            for name in names:
                value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
                if isinstance(value, int) and not isinstance(value, bool):
                    setattr(self, target, value)
                    break

    def evidence(self) -> InferenceAttemptEvidence:
        outcome: Literal["succeeded", "failed", "not_attempted", "unknown"]
        if self.submitted:
            attempted = True
            outcome = "failed" if self.failed else "succeeded" if self.terminal else "unknown"
        elif not self.ready or (self.observable and self.local_failure and not self.transport_seen):
            attempted, outcome = False, "not_attempted"
        else:
            attempted, outcome = None, "unknown"
        return InferenceAttemptEvidence(
            call_id=self.call_id,
            correlation_id=self.correlation_id,
            resolved_identity=self.resolved,
            inference_attempted=attempted,
            inference_outcome=outcome,
            error_code=self.error_code,
            usage_prompt_tokens=self.prompt_tokens,
            usage_completion_tokens=self.completion_tokens,
            latency_ms=int((time.perf_counter() - self.started) * 1000),
            output_text_hash=hashlib.sha256(self.text.encode()).hexdigest(),
            prompt_sha=self.prompt_sha,
        )

    def attach_failure(self, exc: BaseException) -> None:
        from azure.core.exceptions import ClientAuthenticationError

        self.failed = True
        self.local_failure = self.local_failure or isinstance(exc, (TypeError, ValueError, ClientAuthenticationError))
        self.error_code = type(exc).__name__
        setattr(exc, "attempt_evidence", self.evidence())

    @contextmanager
    def bind(self) -> Iterator[None]:
        token = _active_request.set(self)
        try:
            yield
        except (StopIteration, StopAsyncIteration):
            raise
        except BaseException as exc:
            self.attach_failure(exc)
            raise
        finally:
            _active_request.reset(token)


def _observe_handoff(request: Any) -> None:
    observation = _active_request.get()
    if observation is not None:
        observation.handoff(request)


def observe_azure_transport(sdk: Any, *, asynchronous: bool = False) -> bool:
    """Observe the actual transport, not a policy that may precede auth rejection.

    The pinned azure-core pipeline exposes its transport via the generated client.
    Unsupported/injected opaque clients intentionally return unavailable observation.
    ContextVar binding keeps cached/shared transport instances request-local.
    """
    pipeline = getattr(getattr(sdk, "_client", None), "_pipeline", None)
    transport = getattr(pipeline, "_transport", None)
    if transport is None or not callable(getattr(transport, "send", None)):
        return False
    if getattr(transport, "_ama_submission_observer", False):
        return True
    send = transport.send
    if asynchronous:

        async def async_send(request: Any, **kwargs: Any) -> Any:
            _observe_handoff(request)
            return await send(request, **kwargs)

        transport.send = async_send
    else:

        def sync_send(request: Any, **kwargs: Any) -> Any:
            _observe_handoff(request)
            return send(request, **kwargs)

        transport.send = sync_send
    transport._ama_submission_observer = True
    return True


def observe_openai_transport(sdk: Any) -> bool:
    """Observe httpx's selected async transport, including proxy mounts."""
    client = getattr(sdk, "_client", None)
    primary = getattr(client, "_transport", None)
    if primary is None:
        return False
    transports = [primary, *(getattr(client, "_mounts", {}) or {}).values()]
    supported = True
    for transport in transports:
        if transport is None:
            continue
        if not callable(getattr(transport, "handle_async_request", None)):
            supported = False
            continue
        if getattr(transport, "_ama_submission_observer", False):
            continue

        def wrap(send: Any) -> Any:
            async def handoff(request: Any) -> Any:
                _observe_handoff(request)
                return await send(request)

            return handoff

        transport.handle_async_request = wrap(transport.handle_async_request)
        transport._ama_submission_observer = True
    return supported

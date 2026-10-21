"""Exercise installed azure-ai-inference serialization/auth/transport, never the network."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatCompletionsClient
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError, ServiceResponseError
from azure.core.pipeline.policies import SansIOHTTPPolicy
from azure.core.pipeline.transport import AsyncHttpResponse, AsyncHttpTransport, HttpResponse, HttpTransport
from common.foundry_chat_client import (
    FoundryConfigurationError,
    FoundryGatewayDenied,
    FoundryTransportError,
    LiveFoundryChatClient,
)

from tests.contract.test_llm_deployment_routing import ENDPOINT, MESSAGES, configure_tiers
from tests.fixtures.llm_deployment_routing import (
    MODEL_ID,
    MODEL_VERSION,
    TIER_DEPLOYMENTS,
    RequestSubmissionSpy,
    routing_environment,
)


@dataclass
class TransportObservations:
    scenario: str = "success"
    spy: RequestSubmissionSpy = field(default_factory=RequestSubmissionSpy)
    requests: list[Any] = field(default_factory=list)
    pipeline_entries: int = 0

    def handoff(self, request: Any) -> None:
        self.requests.append(request)
        body = json.loads(request.body)
        self.spy.submit(
            call_id=request.headers["x-ms-client-request-id"],
            deployment_name=body["model"],
        )
        if self.scenario == "timeout":
            raise ServiceResponseError("synthetic submitted request timed out")

    def completion(self) -> dict[str, Any]:
        return {
            "id": "synthetic-provider-response",
            "model": "provider-response-label-not-configured-identity",
            "created": 0,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "" if self.scenario in ("empty", "safety") else "ok"},
                    "finish_reason": "content_filter" if self.scenario == "safety" else "stop",
                }
            ],
            "usage": {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9},
        }


class PipelineEntry(SansIOHTTPPolicy[Any, Any]):
    def __init__(self, observations: TransportObservations) -> None:
        self.observations = observations

    def on_request(self, request: Any) -> None:
        self.observations.pipeline_entries += 1


class SyntheticCredential:
    def __init__(self, observations: TransportObservations) -> None:
        self.observations = observations

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        if self.observations.scenario == "credential":
            raise ClientAuthenticationError("synthetic local credential failure")
        return AccessToken("synthetic-offline-token", int(time.time()) + 3600)


class Response(HttpResponse):
    def __init__(self, request: Any, observations: TransportObservations) -> None:
        super().__init__(request, None)
        self.status_code = int(observations.scenario) if observations.scenario in ("403", "500") else 200
        self.reason = "synthetic response"
        self.headers = {"content-type": "application/json"}
        self.content_type = "application/json"
        self.payload = (
            observations.completion()
            if self.status_code == 200
            else {"error": {"code": "synthetic_failure", "message": "synthetic submitted failure"}}
        )

    def body(self) -> bytes:
        return json.dumps(self.payload).encode()

    def json(self) -> dict[str, Any]:
        return self.payload


class Transport(HttpTransport[Any, HttpResponse]):
    def __init__(self, observations: TransportObservations) -> None:
        self.observations = observations

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def __enter__(self) -> Transport:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def send(self, request: Any, **kwargs: Any) -> HttpResponse:
        self.observations.handoff(request)
        return Response(request, self.observations)


class StreamResponse(AsyncHttpResponse):
    def __init__(self, request: Any, observations: TransportObservations) -> None:
        super().__init__(request, None)
        self.observations = observations
        self.status_code = 200
        self.reason = "synthetic stream"
        self.headers = {"content-type": "text/event-stream"}
        self.content_type = "text/event-stream"

    def body(self) -> bytes:
        return b""

    async def load_body(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def stream_download(self, pipeline: Any, **kwargs: Any) -> AsyncIterator[bytes]:
        return self.chunks()

    def iter_bytes(self, **kwargs: Any) -> AsyncIterator[bytes]:
        return self.chunks()

    async def chunks(self) -> AsyncIterator[bytes]:
        payload = self.observations.completion()
        payload["choices"] = [{"index": 0, "delta": {"content": "partial"}, "finish_reason": None}]
        yield f"data: {json.dumps(payload)}\n\n".encode()
        if self.observations.scenario == "partial":
            raise ServiceResponseError("synthetic partial stream failure")
        if self.observations.scenario == "cancel":
            raise asyncio.CancelledError("synthetic cancellation after handoff")
        # End of transport is not a provider terminal finish_reason.
        yield b"data: [DONE]\n\n"


class AsyncTransport(AsyncHttpTransport[Any, AsyncHttpResponse]):
    def __init__(self, observations: TransportObservations) -> None:
        self.observations = observations

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def send(self, request: Any, **kwargs: Any) -> AsyncHttpResponse:
        self.observations.handoff(request)
        return StreamResponse(request, self.observations)


@pytest_asyncio.fixture
async def real_sdk_boundary() -> AsyncIterator[tuple[pytest.MonkeyPatch, TransportObservations]]:
    # Install the socket guard after pytest-asyncio has created its Windows loop.
    with routing_environment() as patch:
        configure_tiers(patch)
        patch.setenv("AZURE_AI_PROJECT_ENDPOINT", ENDPOINT)
        patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
        observations = TransportObservations()
        sync_clients: list[Any] = []
        async_clients: list[Any] = []

        def sync_factory(**settings: Any) -> ChatCompletionsClient:
            if observations.scenario == "client":
                raise ValueError("synthetic client construction failure")
            settings["credential"] = SyntheticCredential(observations)
            sdk = ChatCompletionsClient(
                **settings,
                transport=Transport(observations),
                retry_total=0,
                per_call_policies=[PipelineEntry(observations)],
            )
            sync_clients.append(sdk)
            return sdk

        def async_factory(**settings: Any) -> AsyncChatCompletionsClient:
            settings["credential"] = SyntheticCredential(observations)
            sdk = AsyncChatCompletionsClient(
                **settings,
                transport=AsyncTransport(observations),
                retry_total=0,
                per_call_policies=[PipelineEntry(observations)],
            )
            async_clients.append(sdk)
            return sdk

        patch.setattr("azure.ai.inference.ChatCompletionsClient", sync_factory)
        patch.setattr("azure.ai.inference.aio.ChatCompletionsClient", async_factory)
        patch.setattr("azure.identity.DefaultAzureCredential", lambda **kwargs: SyntheticCredential(observations))
        try:
            yield patch, observations
        finally:
            for sdk in sync_clients:
                sdk.close()
            for sdk in async_clients:
                await sdk.close()


def assert_attempt(value: Any, attempted: bool | None, outcome: str) -> Any:
    evidence = getattr(value, "attempt_evidence", None)
    assert evidence is not None, "T037 must retain request-local evidence on this response/failure"
    assert evidence.inference_attempted is attempted, "SDK/pipeline entry alone is not submission proof"
    assert evidence.inference_outcome == outcome
    return evidence


def assert_handoff_binding(evidence: Any, observations: TransportObservations) -> None:
    assert len(observations.requests) == 1
    request = observations.requests[0]
    assert observations.spy.submissions == [(evidence.call_id, "synthetic-exercise-s")]
    assert "/openai/deployments/synthetic-exercise-s/chat/completions" in request.url
    assert evidence.correlation_id == "synthetic-turn-041"
    assert evidence.resolved_identity.deployment_name == "synthetic-exercise-s"
    assert (evidence.resolved_identity.model_id, evidence.resolved_identity.model_version) == (MODEL_ID, MODEL_VERSION)


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["success", "empty", "safety", "timeout", "403", "500"])
async def test_submission_requires_real_sdk_transport_handoff(real_sdk_boundary: Any, scenario: str) -> None:
    _, observations = real_sdk_boundary
    observations.scenario = scenario
    client = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    if scenario in ("timeout", "403", "500"):
        with pytest.raises((FoundryTransportError, FoundryConfigurationError)) as caught:
            client.chat_complete(model_key="simulation", messages=MESSAGES, correlation_id="synthetic-turn-041")
        assert len(observations.requests) == 1
        evidence = assert_attempt(caught.value, True, "failed")
        assert evidence.usage_prompt_tokens is None
        assert evidence.usage_completion_tokens is None
    else:
        response = client.chat_complete(model_key="simulation", messages=MESSAGES, correlation_id="synthetic-turn-041")
        assert (response.usage_prompt_tokens, response.usage_completion_tokens) == (7, 2)
        assert response.safety_filter_triggered is (scenario == "safety")
        assert response.text == ("" if scenario in ("empty", "safety") else "ok")
        evidence = assert_attempt(response, True, "succeeded")
        assert (evidence.usage_prompt_tokens, evidence.usage_completion_tokens) == (7, 2)
    assert_handoff_binding(evidence, observations)


@pytest.mark.asyncio
@pytest.mark.parametrize("host", ["synthetic.cognitiveservices.azure.com", "synthetic.openai.azure.com"])
@pytest.mark.parametrize("kind", ["sync", "stream"])
async def test_qualified_endpoint_routes_each_tier_at_real_transport(
    real_sdk_boundary: Any, host: str, kind: str
) -> None:
    patch, observations = real_sdk_boundary
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", f"https://{host}/openai/deployments/synthetic-live-r/")
    client = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://mutated.invalid")
    for tier, destination in (*TIER_DEPLOYMENTS, *TIER_DEPLOYMENTS):
        if kind == "sync":
            result = client.chat_complete(model_key=tier, messages=MESSAGES)
        else:
            chunks = [chunk async for chunk in client.chat_complete_stream(model_key=tier, messages=MESSAGES)]
            result = chunks[-1]
        request = observations.requests[-1]
        assert request.url.startswith(f"https://{host}/openai/deployments/{destination}/chat/completions?")
        assert json.loads(request.body)["model"] == destination
        evidence = assert_attempt(result, True, "succeeded" if kind == "sync" else "unknown")
        assert evidence.resolved_identity.deployment_name == destination
        assert evidence.call_id == request.headers["x-ms-client-request-id"]
    assert len(observations.requests) == 6
    assert len(client._sync_clients if kind == "sync" else client._async_clients) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["config", "credential", "client", "sdk-validation", "gateway"])
async def test_known_local_failures_do_not_become_inference_at_sdk_or_policy_entry(
    real_sdk_boundary: Any, scenario: str
) -> None:
    patch, observations = real_sdk_boundary
    observations.scenario = scenario
    if scenario == "config":
        patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "")
    if scenario == "gateway":
        patch.setenv("AZURE_AI_PROJECT_REGION", "westus")
    client = LiveFoundryChatClient(
        credential=SyntheticCredential(observations),
        gateway_apply=lambda **kwargs: SimpleNamespace(gateway_decision="deny", reason="synthetic-denial"),
    )
    messages = [{"role": "user", "content": object()}] if scenario == "sdk-validation" else MESSAGES
    with pytest.raises((FoundryConfigurationError, FoundryTransportError, FoundryGatewayDenied, ValueError)) as caught:
        client.chat_complete(model_key="simulation", messages=messages, correlation_id="synthetic-turn-041")
    assert observations.requests == []
    assert observations.spy.submissions == []
    if scenario == "credential":
        assert observations.pipeline_entries == 1, "Credential rejection must occur inside the real SDK pipeline"
    evidence = assert_attempt(caught.value, False, "not_attempted")
    assert evidence.usage_completion_tokens is None


@pytest.mark.asyncio
async def test_unobserved_injected_sdk_entry_remains_unknown_not_a_proved_attempt(real_sdk_boundary: Any) -> None:
    _, observations = real_sdk_boundary
    client = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    endpoint = client._endpoint_for("synthetic-exercise-s")

    def opaque_complete(**kwargs: Any) -> Any:
        observations.spy.enter_method("opaque-sdk-entry")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="opaque"), finish_reason="stop")],
            usage=None,
        )

    # The supported legacy injection seam cannot observe a transport; it must not invent proof.
    client._sync_clients[endpoint] = SimpleNamespace(complete=opaque_complete)
    response = client.chat_complete(model_key="simulation", messages=MESSAGES)
    assert observations.spy.method_entries == ["opaque-sdk-entry"]
    assert observations.spy.submissions == []
    assert_attempt(response, None, "unknown")


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["partial", "cancel", "completion-unknown"])
async def test_stream_terminal_evidence_retains_observed_partial_usage(real_sdk_boundary: Any, scenario: str) -> None:
    _, observations = real_sdk_boundary
    observations.scenario = scenario
    client = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    chunks = []
    failure: BaseException | None = None
    try:
        async for chunk in client.chat_complete_stream(
            model_key="simulation", messages=MESSAGES, correlation_id="synthetic-turn-041"
        ):
            chunks.append(chunk)
    except (ServiceResponseError, FoundryTransportError, asyncio.CancelledError) as exc:
        failure = exc
    assert len(observations.requests) == 1
    assert chunks and chunks[0].delta_text == "partial", repr(failure)
    if scenario == "completion-unknown":
        assert failure is None
        evidence = assert_attempt(chunks[-1], True, "unknown")
    else:
        assert failure is not None
        evidence = assert_attempt(failure, True, "failed")
    assert_handoff_binding(evidence, observations)
    assert (evidence.usage_prompt_tokens, evidence.usage_completion_tokens) == (7, 2)

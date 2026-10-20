"""Producer/consumer regressions at existing request, event and owning-writer seams."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import pytest_asyncio
from agent_framework import Message
from agent_framework_openai import OpenAIChatClient
from app.services.simulation import controller_service as controller
from app.services.simulation.sub_agent_invoker import production_invoker
from common import audit, otel_telemetry
from common.audit import InMemoryAuditWriter
from common.content_safety import ContentSafetyValidator
from common.foundry_chat_client import LiveFoundryChatClient
from common.llm_client import LLMClient
from common.llm_config import LLMClientConfig
from common.llm_mixin import LLMCallMixin
from common.token_budget import UnicodeHeuristicTokenizer
from dispatcher import agent as dispatcher
from maf_runtime import chat_client as maf
from maf_runtime.middleware.audit_middleware import AuditMiddleware
from openai import AsyncAzureOpenAI

from tests.contract.test_audit_record_shape import _grounded_inference_example
from tests.contract.test_llm_deployment_provenance_schema import provenance_examples
from tests.contract.test_llm_deployment_routing import ENDPOINT, configure_tiers
from tests.fixtures.llm_deployment_routing import MODEL_ID, MODEL_VERSION, routing_environment
from tests.unit.test_llm_adapter_snapshots import build_controller, controller_events
from tests.unit.test_llm_inference_attempt_evidence import (
    SyntheticCredential,
)
from tests.unit.test_llm_inference_attempt_evidence import (
    real_sdk_boundary as real_sdk_boundary,
)


@pytest_asyncio.fixture
async def provenance_environment() -> AsyncIterator[pytest.MonkeyPatch]:
    with routing_environment() as patch:
        configure_tiers(patch)
        patch.setenv("AZURE_AI_PROJECT_ENDPOINT", ENDPOINT)
        patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
        patch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", "")
        patch.setenv("AZURE_SEARCH_ENDPOINT", "")
        patch.setenv("AZURE_COSMOS_ENDPOINT", "")
        patch.setattr("azure.identity.DefaultAzureCredential", lambda **kwargs: object())
        patch.setattr("azure.identity.get_bearer_token_provider", lambda *args: lambda: "synthetic-offline-token")
        patch.setattr("common.llm_mixin.create_tokenizer", lambda *args: UnicodeHeuristicTokenizer())
        yield patch


def attempt_projection(value: Any) -> tuple[Any, Any]:
    if isinstance(value, dict):
        evidence = value.get("attempt_evidence", value)
    else:
        evidence = getattr(value, "attempt_evidence", value)
    if isinstance(evidence, dict):
        assert "inference_attempted" in evidence, "Observed provenance was dropped by the producer/consumer"
        assert "inference_outcome" in evidence
        return evidence["inference_attempted"], evidence["inference_outcome"]
    assert hasattr(evidence, "inference_attempted"), "Request evidence is absent, not evidence of success"
    return evidence.inference_attempted, evidence.inference_outcome


@pytest.mark.asyncio
async def test_common_usage_preserves_request_identity_and_evidence(real_sdk_boundary: Any) -> None:
    _, observations = real_sdk_boundary
    seam = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    client = LLMClient(config=LLMClientConfig(), chat_complete=seam.chat_complete)
    result = client.generate_response(purpose="simulation", prompt="synthetic exercise", correlation_id="common-041")
    assert len(observations.requests) == 1
    assert result["deployment_id"] == "synthetic-exercise-s"
    assert result["token_usage"] == {"input_tokens": 7, "output_tokens": 2}
    assert attempt_projection(result) == (True, "succeeded")
    assert (result["model_id"], result["model_version"]) == (MODEL_ID, MODEL_VERSION)


@pytest.mark.asyncio
async def test_common_telemetry_uses_configured_model_not_alias_or_response_identity(real_sdk_boundary: Any) -> None:
    patch, observations = real_sdk_boundary
    misleading_alias = "gpt-4o-looking-alias-not-model-041"
    patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", misleading_alias)
    recorder = otel_telemetry.OtelRecorder()
    patch.setattr(otel_telemetry, "_active_recorder", recorder)
    LiveFoundryChatClient(credential=SyntheticCredential(observations)).chat_complete(
        model_key="simulation", messages=[{"role": "user", "content": "synthetic exercise"}], correlation_id="otel-041"
    )
    assert len(observations.requests) == 1
    spans = recorder.find("foundry.inference")
    assert len(spans) == 1
    assert spans[0].attributes["model_id"] == MODEL_ID
    assert spans[0].attributes["deployment_alias"] == misleading_alias
    assert spans[0].attributes["model_version"] == MODEL_VERSION


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["deadline", "post-call-safety", "safety-exception", "budget-exception"])
async def test_mixin_generation_method_does_not_erase_actual_inference(real_sdk_boundary: Any, case: str) -> None:
    patch, observations = real_sdk_boundary
    patch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", "")
    patch.setattr("common.llm_mixin.create_tokenizer", lambda *args: UnicodeHeuristicTokenizer())
    mixin = LLMCallMixin()
    mixin._llm_client = LLMClient(
        config=LLMClientConfig(),
        chat_complete=LiveFoundryChatClient(credential=SyntheticCredential(observations)).chat_complete,
    )
    if case == "post-call-safety":
        observations.completion = lambda: {
            "id": "synthetic-blocked-response",
            "model": "response-label",
            "created": 0,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "terror threat imminent"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9},
        }
        mixin._content_safety = ContentSafetyValidator()
    if case in ("safety-exception", "budget-exception"):

        def fail_processing(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("synthetic local processing failure")

        if case == "safety-exception":
            patch.setattr(mixin._content_safety, "validate", fail_processing)
        else:
            patch.setattr(mixin, "_track_budget", fail_processing)
    result = mixin._generate_with_fallback(
        purpose="simulation",
        prompt="synthetic exercise",
        template_text="safe exercise template",
        deadline_monotonic=time.monotonic() - 1 if case == "deadline" else None,
    )
    assert len(observations.requests) == (0 if case == "deadline" else 1)
    assert result["generation_method"] == ("safety_fallback" if case == "post-call-safety" else "template_fallback")
    if case != "deadline":
        assert result["actual_token_usage"] == {"input_tokens": 7, "output_tokens": 2}
        evidence = result["attempt_evidence"]
        assert evidence is not None
        assert evidence.call_id == observations.requests[0].headers["x-ms-client-request-id"]
        assert (result["model_id"], result["model_version"], result["model_deployment_id"]) == (
            MODEL_ID,
            MODEL_VERSION,
            "synthetic-exercise-s",
        )
    if case in ("safety-exception", "budget-exception"):
        assert result["error_reason"] == "synthetic local processing failure"
        assert result["requires_human_review"] is True
    assert attempt_projection(result) == ((False, "not_attempted") if case == "deadline" else (True, "succeeded"))


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["success", "empty", "config", "timeout"])
async def test_dispatcher_wire_reports_actual_attempt_not_http_invocation(
    real_sdk_boundary: Any, scenario: str
) -> None:
    patch, observations = real_sdk_boundary
    observations.scenario = scenario
    if scenario == "config":
        patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "")
    app = dispatcher.create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://dispatcher.test") as client:
        response = await client.post(
            "/monitoring/invoke", json={"tenant_id": "synthetic-tenant", "question": "exercise"}
        )
    assert response.status_code == 200
    wire = response.json()
    assert wire["invocation_id"]
    assert len(observations.requests) == (0 if scenario == "config" else 1)
    expected = (
        (False, "not_attempted") if scenario == "config" else (True, "failed" if scenario == "timeout" else "succeeded")
    )
    assert attempt_projection(wire) == expected
    assert wire["model_deployment"] == (None if scenario == "config" else "synthetic-exercise-s")
    assert wire["model_id"] == (None if scenario == "config" else MODEL_ID)
    assert wire["model_version"] == (None if scenario == "config" else MODEL_VERSION)
    assert wire.get("degraded", False) is (scenario != "success")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "example",
    [
        "old_dispatcher",
        "new_dispatcher",
        "new_not_attempted",
        "new_unknown",
        "proved-submission-completion-lost",
        "missing-deployment",
        "lost-response",
    ],
)
async def test_api_retains_remote_uncertainty_without_fallback_identity_or_duplicate_row(
    provenance_environment: pytest.MonkeyPatch, example: str
) -> None:
    patch = provenance_environment
    writer = InMemoryAuditWriter()
    patch.setattr(audit, "_writer", writer)
    requests = []
    wire = dict(provenance_examples().get(example, provenance_examples()["old_dispatcher"]))
    if example == "proved-submission-completion-lost":
        wire = {**provenance_examples()["new_dispatcher"], "inference_outcome": "unknown"}
    if example == "missing-deployment":
        wire.pop("model_deployment")

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if example == "lost-response":
            raise httpx.ReadTimeout("synthetic lost dispatcher response", request=request)
        return httpx.Response(200, json=wire)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        reply = await production_invoker(http).invoke("monitoring", "exercise", tenant_id="synthetic-tenant")
    assert len(requests) == 1
    assert writer.records == [], "Outer HTTP correlation must not create a second model-call row"
    assert reply.model_deployment == wire.get("model_deployment")
    if example == "lost-response":
        assert reply.degraded and reply.error == "timeout"
        expected = (None, "unknown")
    elif example in ("old_dispatcher", "missing-deployment"):
        assert reply.sub_agent_invocation_id == wire["invocation_id"]
        expected = (None, "unknown")
    else:
        assert reply.sub_agent_invocation_id == wire["invocation_id"]
        expected = (wire["inference_attempted"], wire["inference_outcome"])
    assert attempt_projection(reply) == expected
    assert getattr(reply, "model_id", None) == wire.get("model_id")
    assert getattr(reply, "model_version", None) == wire.get("model_version")
    if example == "new_not_attempted":
        assert reply.degraded and reply.error == wire["error"]


def inference_rows(writer: InMemoryAuditWriter) -> list[dict[str, Any]]:
    return [row for row in writer.records if row.get("call_kind") == "inference"]


def assert_owned_rows(writer: InMemoryAuditWriter, count: int) -> list[dict[str, Any]]:
    rows = inference_rows(writer)
    assert len(rows) == count, f"T036/T040 owning writer expected {count} proved calls, observed {len(rows)}"
    assert len({row["call_id"] for row in rows}) == count
    for row in rows:
        assert (row["model_id"], row["model_version"], row["deployment_alias"]) == (
            MODEL_ID,
            MODEL_VERSION,
            "synthetic-exercise-s",
        )
        assert row["inference_attempted"] is True
        assert row["tenant_id"] == "synthetic-tenant"
    return rows


@pytest_asyncio.fixture
async def controller_http(provenance_environment: pytest.MonkeyPatch) -> AsyncIterator[Any]:
    patch = provenance_environment
    state: dict[str, Any] = {"case": "success", "requests": [], "entries": 0}
    clients = []
    patch.setattr(controller, "get_rate_limiter", controller.RateLimiter)

    def frame(*, tool: bool, terminal: bool) -> bytes:
        delta: dict[str, Any] = {"content": "model-only-round"}
        if tool:
            delta = {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "tool-041",
                        "type": "function",
                        "function": {"name": "summarise_state", "arguments": "{}"},
                    }
                ]
            }
        payload = {
            "id": "synthetic-stream-response",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": "provider-reported-label",
            "choices": [
                {"index": 0, "delta": delta, "finish_reason": ("tool_calls" if tool else "stop") if terminal else None}
            ],
            "usage": {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9},
        }
        return f"data: {json.dumps(payload)}\n\ndata: [DONE]\n\n".encode()

    def handle(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        body = json.loads(request.content)
        assert body["model"] == "synthetic-exercise-s"
        assert body["stream"] and body["tools"] == controller.TOOL_SCHEMAS
        tool = state["case"].startswith("rounds-") and len(state["requests"]) == 1
        if state["case"] == "failed" or (state["case"] == "rounds-failed" and len(state["requests"]) == 2):
            return httpx.Response(500, json={"error": {"message": "synthetic submitted failure"}})
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=frame(tool=tool, terminal=state["case"] != "completion-unknown"),
        )

    async def unobserved_chunks() -> AsyncIterator[Any]:
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="opaque", tool_calls=None))])

    def factory(**settings: Any) -> Any:
        sdk = AsyncAzureOpenAI(
            **settings, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)), max_retries=0
        )
        clients.append(sdk)
        real_create = sdk.chat.completions.create

        async def create(**kwargs: Any) -> Any:
            state["entries"] += 1
            if state["case"] == "submission-unknown" or (state["case"] == "rounds-unknown" and state["entries"] == 2):
                # Opaque supported SDK injection has no observable handoff; ordinary output proves nothing.
                return unobserved_chunks()
            return await real_create(**kwargs)

        patch.setattr(sdk.chat.completions, "create", create)
        return sdk

    patch.setattr("openai.AsyncAzureOpenAI", factory)
    try:
        yield patch, state
    finally:
        for client in clients:
            await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case,attempted,outcome,count",
    [
        ("success", True, "succeeded", 1),
        ("failed", True, "failed", 1),
        ("completion-unknown", True, "unknown", 1),
        ("not-attempted", False, "not_attempted", 0),
        ("submission-unknown", None, "unknown", 0),
    ],
)
async def test_controller_no_rag_admission_matrix_at_owning_writer(
    controller_http: Any, case: str, attempted: bool | None, outcome: str, count: int
) -> None:
    patch, state = controller_http
    state["case"] = case
    if case == "not-attempted":
        patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "")
    writer = InMemoryAuditWriter()
    service = build_controller(patch)
    service._audit_writer = writer
    assert service._retrieval is None
    events = await controller_events(service)
    assert len(state["requests"]) == count
    rows = assert_owned_rows(writer, count)
    if rows:
        assert rows[0]["inference_outcome"] == outcome
        assert rows[0]["rag_used"] is False
        if outcome == "succeeded":
            assert rows[0]["output_tokens"] == 2, "Whitespace-counted aggregate output is not actual usage"
    else:
        envelopes = [event.data for event in events] + [
            call.kwargs for call in service._persist_turn_async.call_args_list
        ]
        assert any(
            item.get("inference_outcome") == outcome
            and "inference_attempted" in item
            and item["inference_attempted"] is attempted
            for item in envelopes
        ), "False/unknown evidence must survive in an existing event/turn envelope without inventing a call"


@pytest.mark.asyncio
@pytest.mark.parametrize("case,count", [("rounds-success", 2), ("rounds-failed", 2), ("rounds-unknown", 1)])
async def test_controller_each_tool_round_keeps_earlier_attempts(controller_http: Any, case: str, count: int) -> None:
    patch, state = controller_http
    state["case"] = case
    writer = InMemoryAuditWriter()
    service = build_controller(patch)
    service._audit_writer = writer
    events = await controller_events(service)
    assert state["entries"] == 2
    assert len(state["requests"]) == count
    assert any(event.event == "tool.result" for event in events)
    rows = assert_owned_rows(writer, count)
    assert len({row["correlation_id"] for row in rows}) == 1
    assert rows[0]["inference_outcome"] == "succeeded"
    assert rows[0]["output_tokens"] == 2
    if case == "rounds-failed":
        assert rows[1]["inference_outcome"] == "failed"


@pytest.mark.asyncio
@pytest.mark.parametrize("make_model_call", [False, True], ids=["tool-failure-before-model", "real-adapter-request"])
async def test_maf_middleware_entry_is_not_inference_and_adapter_evidence_is_retained(
    provenance_environment: pytest.MonkeyPatch, make_model_call: bool
) -> None:
    patch = provenance_environment
    agent_writer = InMemoryAuditWriter()
    model_writer = InMemoryAuditWriter()
    patch.setattr(audit, "_writer", model_writer)
    requests = []
    clients = []
    patch.setattr(maf, "_shared_token_provider", lambda: lambda: "synthetic-offline-token")

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "id": "response-041",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "provider-label-not-routing-authority",
                "output": [
                    {
                        "id": "msg-041",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": "ok", "annotations": []}],
                    }
                ],
                "usage": {"input_tokens": 7, "output_tokens": 2, "total_tokens": 9},
            },
        )

    def factory(**settings: Any) -> OpenAIChatClient:
        sdk = AsyncAzureOpenAI(
            azure_endpoint=settings["azure_endpoint"],
            api_version=settings["api_version"],
            azure_ad_token_provider=settings["credential"],
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
            max_retries=0,
        )
        clients.append(sdk)
        return OpenAIChatClient(**settings, async_client=sdk)

    patch.setattr(maf, "OpenAIChatClient", factory)
    grounding = _grounded_inference_example()
    context = SimpleNamespace(
        metadata={
            "incident_id": "incident-041",
            "tenant_id": "synthetic-tenant",
            "rag_audit_context": {
                key: grounding[key]
                for key in (
                    "rag_used",
                    "retrieved_chunks",
                    "citations",
                    "embedding_model_id",
                    "corpus_build_sha",
                    "retrieval_index_name",
                )
            },
        },
        messages=[],
        result=None,
    )

    async def call_next() -> None:
        if not make_model_call:
            raise ValueError("synthetic tool validation failure before model")
        chat = maf.build_azure_openai_chat_client(config=LLMClientConfig(), model_tier="reasoning")
        context.result = await chat.get_response(
            [
                Message("user", ["Synthetic grounding [nsw/evacuation-planning#p47]: exercise excerpt."]),
            ]
        )

    try:
        middleware = AuditMiddleware(agent_name="monitoring", model_tier="reasoning", writer=agent_writer)
        if make_model_call:
            await middleware.process(context, call_next)
        else:
            with pytest.raises(ValueError, match="before model"):
                await middleware.process(context, call_next)
        assert len(requests) == int(make_model_call)
        assert len(agent_writer.records) == 1
        rows = inference_rows(model_writer) + inference_rows(agent_writer)
        assert len(rows) == int(make_model_call), "T039 must connect adapter evidence without duplicate model rows"
        envelope = agent_writer.records[0]
        assert attempt_projection(envelope) == ((True, "succeeded") if make_model_call else (False, "not_attempted"))
    finally:
        for client in clients:
            await client.close()

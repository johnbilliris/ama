"""Hermetic reader/SDK/dispatcher/API/owning-writer acceptance for feature 041."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from agent_framework import Message
from agent_framework_openai import OpenAIChatClient
from ama_domain.audit_record import AuditRecord
from app.services.simulation.sub_agent_invoker import production_invoker
from common import audit, otel_telemetry
from common.audit import InMemoryAuditWriter
from common.foundry_chat_client import LiveFoundryChatClient
from common.inference_observation import RequestObservation
from dispatcher import agent as dispatcher
from jsonschema import Draft202012Validator
from maf_runtime import chat_client as maf
from maf_runtime.middleware.audit_middleware import AuditMiddleware
from openai import AsyncAzureOpenAI

from tests.contract.test_llm_deployment_provenance import (
    controller_http as controller_http,
)
from tests.contract.test_llm_deployment_provenance import (
    provenance_environment as provenance_environment,
)
from tests.contract.test_llm_deployment_provenance_schema import historical_fingerprints
from tests.fixtures.llm_deployment_routing import MODEL_ID, MODEL_VERSION, TIER_DEPLOYMENTS
from tests.unit.test_llm_adapter_snapshots import build_controller, controller_events
from tests.unit.test_llm_inference_attempt_evidence import (
    SyntheticCredential,
)
from tests.unit.test_llm_inference_attempt_evidence import (
    real_sdk_boundary as real_sdk_boundary,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
@pytest.mark.parametrize("role", sorted(dispatcher._ROLES))
async def test_all_roles_cross_real_sdk_dispatcher_and_api_without_duplicate_rows(
    real_sdk_boundary: Any, role: str
) -> None:
    patch, observations = real_sdk_boundary
    writer = InMemoryAuditWriter()
    patch.setattr(audit, "_writer", writer)
    recorder = otel_telemetry.OtelRecorder()
    patch.setattr(otel_telemetry, "_active_recorder", recorder)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=dispatcher.create_app())) as http:
        reply = await production_invoker(http).invoke(role, "synthetic exercise", tenant_id="synthetic-tenant")
    assert len(observations.requests) == 1
    assert reply.sub_agent_invocation_id
    assert (reply.inference_attempted, reply.inference_outcome) == (True, "succeeded")
    assert (reply.model_id, reply.model_version, reply.model_deployment) == (
        MODEL_ID,
        MODEL_VERSION,
        "synthetic-exercise-s",
    )
    spans = recorder.find("foundry.inference")
    assert len(spans) == 1
    assert writer.records == [], "API HTTP correlation is not an owning inference writer"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario,attempted,outcome,sends",
    [
        ("empty", True, "succeeded", 1),
        ("safety", True, "succeeded", 1),
        ("timeout", True, "failed", 1),
        ("gateway", False, "not_attempted", 0),
        ("config", False, "not_attempted", 0),
    ],
)
async def test_dispatcher_degradation_keeps_actual_attempt_through_api(
    real_sdk_boundary: Any, scenario: str, attempted: bool, outcome: str, sends: int
) -> None:
    patch, observations = real_sdk_boundary
    recorder = otel_telemetry.OtelRecorder()
    patch.setattr(otel_telemetry, "_active_recorder", recorder)
    observations.scenario = scenario
    if scenario == "config":
        patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "")
    if scenario == "gateway":
        patch.setenv("AZURE_AI_PROJECT_REGION", "westus")
        patch.setattr(
            "common.model_gateway.apply",
            lambda **kwargs: SimpleNamespace(gateway_decision="deny", reason="synthetic-gateway-denial"),
        )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=dispatcher.create_app())) as http:
        reply = await production_invoker(http).invoke("monitoring", "exercise", tenant_id="synthetic-tenant")
    assert len(observations.requests) == sends
    assert reply.degraded and reply.error
    assert (reply.inference_attempted, reply.inference_outcome) == (attempted, outcome)
    assert reply.model_deployment == ("synthetic-exercise-s" if attempted else None)
    assert reply.model_id == (MODEL_ID if attempted else None)
    spans = recorder.find("foundry.inference")
    assert len(spans) == sends
    if spans:
        assert spans[0].attributes["inference_outcome"] == outcome
        if scenario == "timeout":
            assert spans[0].attributes["usage_completion_tokens"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("case,count", [("rounds-success", 2), ("rounds-failed", 2), ("rounds-unknown", 1)])
async def test_each_controller_row_matches_its_own_transport_id_and_prompt(
    controller_http: Any, case: str, count: int
) -> None:
    patch, state = controller_http
    state["case"] = case
    writer = InMemoryAuditWriter()
    service = build_controller(patch)
    service._audit_writer = writer
    await controller_events(service)
    rows = writer.records
    assert len(rows) == count
    assert len({row["call_id"] for row in rows}) == count
    assert len({row["prompt_sha"] for row in rows}) == count
    for row, request in zip(rows, state["requests"], strict=True):
        AuditRecord.model_validate(row)
        assert row["call_id"] == request.headers["x-ms-client-request-id"]
        assert row["deployment_alias"] == json.loads(request.content)["model"]
        assert row["model_id"] == MODEL_ID and row["model_version"] == MODEL_VERSION
        assert row["rag_optout_reason"] == "scenario-execution"
    if case == "rounds-failed":
        assert rows[1]["inference_outcome"] == "failed"
        assert rows[1]["output_text_hash"] == hashlib.sha256(b"").hexdigest()


@pytest.mark.asyncio
async def test_controller_qualified_endpoint_uses_simulation_url_and_proved_writer_row(controller_http: Any) -> None:
    patch, state = controller_http
    endpoint = "https://synthetic.cognitiveservices.azure.com"
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", f"{endpoint}/openai/deployments/synthetic-live-r/")
    writer = InMemoryAuditWriter()
    service = build_controller(patch)
    service._audit_writer = writer
    await controller_events(service)
    assert len(state["requests"]) == len(writer.records) == 1
    request = state["requests"][0]
    assert str(request.url).startswith(f"{endpoint}/openai/deployments/synthetic-exercise-s/chat/completions?")
    assert json.loads(request.content)["model"] == "synthetic-exercise-s"
    row = writer.records[0]
    assert row["deployment_alias"] == "synthetic-exercise-s"
    assert (row["inference_attempted"], row["inference_outcome"]) == (True, "succeeded")
    assert row["call_id"] == request.headers["x-ms-client-request-id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("role", sorted(dispatcher._ROLES))
async def test_dispatcher_qualified_endpoint_never_consumes_live_route(real_sdk_boundary: Any, role: str) -> None:
    patch, observations = real_sdk_boundary
    endpoint = "https://synthetic.cognitiveservices.azure.com"
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", f"{endpoint}/openai/deployments/{TIER_DEPLOYMENTS[0][1]}")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=dispatcher.create_app())) as http:
        reply = await production_invoker(http).invoke(role, "synthetic exercise", tenant_id="synthetic-tenant")
    assert len(observations.requests) == 1
    assert observations.requests[0].url.startswith(
        f"{endpoint}/openai/deployments/synthetic-exercise-s/chat/completions?"
    )
    assert reply.model_deployment == "synthetic-exercise-s"
    assert (reply.inference_attempted, reply.inference_outcome) == (True, "succeeded")


class PartialBytes(httpx.AsyncByteStream):
    def __init__(self, *, cancel: bool) -> None:
        self.cancel = cancel

    async def __aiter__(self) -> AsyncIterator[bytes]:
        payload = {
            "id": "partial-041",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": "provider-label",
            "choices": [{"index": 0, "delta": {"content": "actual partial"}, "finish_reason": None}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9},
        }
        yield f"data: {json.dumps(payload)}\n\n".encode()
        if self.cancel:
            raise asyncio.CancelledError("synthetic cancellation after handoff")
        raise httpx.ReadError("synthetic lost stream after handoff")


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True], ids=["partial-failure", "cancel"])
async def test_controller_persists_actual_partial_evidence_on_stream_failure(
    provenance_environment: pytest.MonkeyPatch, cancel: bool
) -> None:
    patch = provenance_environment
    requests = []
    clients = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=PartialBytes(cancel=cancel))

    def factory(**settings: Any) -> AsyncAzureOpenAI:
        sdk = AsyncAzureOpenAI(
            **settings,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
            max_retries=0,
        )
        clients.append(sdk)
        return sdk

    patch.setattr("openai.AsyncAzureOpenAI", factory)
    writer = InMemoryAuditWriter()
    service = build_controller(patch)
    service._audit_writer = writer
    try:
        if cancel:
            with pytest.raises(asyncio.CancelledError):
                await controller_events(service)
        else:
            events = await controller_events(service)
            assert any(e.event == "error" and e.data["inference_outcome"] == "failed" for e in events)
        assert len(requests) == len(writer.records) == 1
        row = writer.records[0]
        AuditRecord.model_validate(row)
        assert row["call_id"] == requests[0].headers["x-ms-client-request-id"]
        assert row["output_tokens"] == 2
        assert row["output_text_hash"] == hashlib.sha256(b"actual partial").hexdigest()
        assert row["inference_outcome"] == "failed"
    finally:
        for client in clients:
            await client.close()


@pytest.mark.asyncio
async def test_cached_common_transport_keeps_concurrent_call_ids_and_correlations_separate(
    real_sdk_boundary: Any,
) -> None:
    _, observations = real_sdk_boundary
    client = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    client._ensure_sync_client("synthetic-exercise-s")
    responses = await asyncio.gather(
        *[
            asyncio.to_thread(
                client.chat_complete,
                model_key="simulation",
                messages=[{"role": "user", "content": "exercise"}],
                correlation_id=f"concurrent-{index}",
            )
            for index in range(2)
        ]
    )
    evidence = [response.attempt_evidence for response in responses]
    assert all(item is not None and item.inference_attempted is True for item in evidence)
    assert {item.correlation_id for item in evidence if item} == {"concurrent-0", "concurrent-1"}
    assert {item.call_id for item in evidence if item} == {
        request.headers["x-ms-client-request-id"] for request in observations.requests
    }
    assert len(observations.requests) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal", [True, False], ids=["terminal", "completion-lost"])
async def test_real_maf_stream_retains_transport_usage_in_agent_envelope_without_inventing_optout(
    provenance_environment: pytest.MonkeyPatch, terminal: bool
) -> None:
    patch = provenance_environment
    patch.setattr(maf, "_shared_token_provider", lambda: lambda: "synthetic-offline-token")
    agent_writer, model_writer = InMemoryAuditWriter(), InMemoryAuditWriter()
    patch.setattr(audit, "_writer", model_writer)
    clients = []
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        events = [
            {
                "type": "response.output_text.delta",
                "delta": "actual text",
                "item_id": "msg-041",
                "output_index": 0,
                "content_index": 0,
                "sequence_number": 0,
            },
        ]
        if terminal:
            events.append(
                {
                    "type": "response.completed",
                    "sequence_number": 1,
                    "response": {
                        "id": "resp-041",
                        "object": "response",
                        "created_at": 0,
                        "status": "completed",
                        "model": "provider-label",
                        "output": [],
                        "usage": {"input_tokens": 7, "output_tokens": 2, "total_tokens": 9},
                    },
                }
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join(f"data: {json.dumps(event)}\n\n" for event in events).encode(),
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
    context = SimpleNamespace(
        metadata={"incident_id": "incident-041", "run_id": "c9d6b90c-7954-44b2-8f4e-6bcc5403df7d"},
        messages=[],
        result=None,
    )

    async def call_next() -> None:
        chat = maf.build_azure_openai_chat_client(model_tier="reasoning")
        stream = chat.get_response([Message("user", ["synthetic exercise"])], stream=True)
        async for _ in stream:
            pass
        context.result = await stream.get_final_response()

    try:
        await AuditMiddleware(agent_name="monitoring", model_tier="reasoning", writer=agent_writer).process(
            context,
            call_next,
        )
        assert len(requests) == len(agent_writer.records) == 1
        envelope = agent_writer.records[0]
        Draft202012Validator(
            json.loads((ROOT / "specs/033-maf-adoption/contracts/audit-entry.schema.json").read_bytes())
        ).validate(envelope)
        assert (envelope["inference_attempted"], envelope["inference_outcome"]) == (
            True,
            "succeeded" if terminal else "unknown",
        )
        assert model_writer.records == [], "Missing RAG/opt-out proof must not fabricate a carve-out"
        calls = envelope["model_calls"]
        assert len(calls) == 1 and calls[0]["call_id"] == requests[0].headers["x-ms-client-request-id"]
        assert calls[0]["model_id"] == MODEL_ID
        if terminal:
            assert calls[0]["usage_completion_tokens"] == 2
    finally:
        for client in clients:
            await client.close()


def test_maf_strict_reader_accepts_additive_fields_and_rejects_extra_keys() -> None:
    schema = json.loads((ROOT / "specs/033-maf-adoption/contracts/audit-entry.schema.json").read_bytes())
    validator = Draft202012Validator(schema)
    payload = {
        "id": "c9d6b90c-7954-44b2-8f4e-6bcc5403df7d",
        "incident_id": "incident",
        "run_id": "c9d6b90c-7954-44b2-8f4e-6bcc5403df7d",
        "agent_name": "monitoring",
        "step_name": "monitoring",
        "model_tier": "reasoning",
        "input_fingerprint": "0" * 64,
        "output_fingerprint": "1" * 64,
        "correlation_id": "2" * 32,
        "started_at": "2026-10-19T00:00:00Z",
        "ended_at": "2026-10-19T00:00:01Z",
        "outcome": "success",
    }
    validator.validate(payload)
    enriched = {**payload, "inference_attempted": None, "inference_outcome": "unknown", "model_calls": []}
    validator.validate(enriched)
    assert list(validator.iter_errors({**enriched, "unexpected": True}))
    assert list(validator.iter_errors({**enriched, "inference_outcome": "completed"}))


def test_historical_fingerprints_still_match_original_anchors() -> None:
    anchors = historical_fingerprints()
    assert len(anchors) == 50
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in anchors.items())


@pytest.mark.asyncio
async def test_controller_tool_reply_retains_remote_unknown_completion_and_http_correlation(
    provenance_environment: pytest.MonkeyPatch,
) -> None:
    from tests.contract.test_llm_deployment_provenance_schema import provenance_examples

    wire = {**provenance_examples()["new_dispatcher"], "inference_outcome": "unknown", "degraded": True}
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=wire))) as http:
        service = build_controller(provenance_environment)
        service._sub_agents = production_invoker(http)
        result = await type(service)._execute_tool(
            service,
            name="query_sub_agent",
            args={"sub_agent": "monitoring", "question": "exercise"},
            tenant_id="synthetic-tenant",
            simulation_id="synthetic-simulation",
            user_message="exercise",
        )
    assert result["sub_agent_invocation_id"] == wire["invocation_id"]
    assert (result["inference_attempted"], result["inference_outcome"]) == (True, "unknown")
    assert result["model_deployment"] == wire["model_deployment"]
    assert result["outcome"] == "error" and result["degraded"] is True


@pytest.mark.asyncio
async def test_generation_method_alone_cannot_manufacture_model_call_timeline(
    provenance_environment: pytest.MonkeyPatch,
) -> None:
    from app.services import signal_accepted_workflow as workflow

    bucket: dict[str, Any] = {}
    provenance_environment.setattr(
        workflow.state_store,
        "TIMELINE_EVENTS",
        SimpleNamespace(bucket_for=lambda tenant: bucket),
    )
    event = SimpleNamespace(tenant_id="tenant", incident_id="incident", scope="scope", correlation_id="correlation")
    legacy_output = SimpleNamespace(generation_method="llm", model_deployment_id="configured-target")
    workflow._emit_llm_call_timeline_events(event, legacy_output, legacy_output)
    assert bucket == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case,outcome,count",
    [
        ("success", "succeeded", 2),
        ("common-success", "succeeded", 2),
        ("submitted-failure", "failed", 2),
        ("completion-lost", "unknown", 2),
        ("no-call", "not_attempted", 0),
        ("submission-unknown", "unknown", 0),
    ],
)
async def test_workflow_request_evidence_reaches_timeline_without_trusting_generated_flags(
    provenance_environment: pytest.MonkeyPatch, real_sdk_boundary: Any, case: str, outcome: str, count: int
) -> None:
    from app.services import signal_accepted_workflow as workflow
    from maf_runtime.workflow.builder import AmaWorkflow
    from pydantic import BaseModel

    from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent

    patch = provenance_environment
    _, common_observations = real_sdk_boundary
    patch.setattr(maf, "_shared_token_provider", lambda: lambda: "synthetic-offline-token")
    if case == "submission-unknown":
        patch.setattr(maf, "observe_openai_transport", lambda sdk: False)
    requests, clients = [], []
    agent_writer, model_writer = InMemoryAuditWriter(), InMemoryAuditWriter()
    patch.setattr(audit, "_writer", model_writer)
    bucket: dict[str, Any] = {}
    patch.setattr(workflow.state_store, "TIMELINE_EVENTS", SimpleNamespace(bucket_for=lambda tenant: bucket))

    class GeneratedOutput(BaseModel):
        generation_method: str = "llm"
        inference_attempted: bool = True
        model_id: str = "unproved-generated-model"
        model_deployment_id: str = "unproved-generated-alias"

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if case == "submitted-failure":
            return httpx.Response(500, json={"error": {"message": "synthetic submitted failure"}})
        events = []
        if case != "completion-lost":
            events.append(
                {
                    "type": "response.completed",
                    "sequence_number": 0,
                    "response": {
                        "id": "resp-workflow-041",
                        "object": "response",
                        "created_at": 0,
                        "status": "completed",
                        "model": "provider-label",
                        "output": [],
                        "usage": {"input_tokens": 7, "output_tokens": 2, "total_tokens": 9},
                    },
                }
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join(f"data: {json.dumps(event)}\n\n" for event in events).encode() + b"data: [DONE]\n\n",
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

    class Step:
        def __init__(self, name: str, *, infer: bool = False) -> None:
            self.name, self.infer = name, infer

        async def execute_step(self, payload: Any, **kwargs: Any) -> BaseModel:
            if not self.infer:
                return GeneratedOutput()
            context = SimpleNamespace(metadata={}, messages=[], result=None)

            async def call_next() -> None:
                if case == "no-call":
                    raise ValueError("synthetic local tool validation failure")
                if case == "common-success":
                    from common.llm_client import LLMClient
                    from common.llm_config import LLMClientConfig
                    from common.llm_mixin import LLMCallMixin

                    mixin = LLMCallMixin()
                    mixin._llm_client = LLMClient(
                        config=LLMClientConfig(),
                        chat_complete=LiveFoundryChatClient(
                            credential=SyntheticCredential(common_observations)
                        ).chat_complete,
                    )
                    context.result = mixin._generate_with_fallback(
                        purpose="simulation", prompt="exercise", template_text="template"
                    )
                    return
                chat = maf.build_azure_openai_chat_client(model_tier="reasoning")
                stream = chat.get_response([Message("user", ["exercise"])], stream=True)
                async for _ in stream:
                    pass
                context.result = await stream.get_final_response()

            try:
                await AuditMiddleware(agent_name=self.name, model_tier="reasoning", writer=agent_writer).process(
                    context, call_next
                )
            except Exception:
                if case not in ("submitted-failure", "no-call"):
                    raise
            return GeneratedOutput()

    async def hitl(**kwargs: Any) -> dict[str, Any]:
        return {}

    event = SignalAcceptedEvent(
        tenant_id="live",
        scope="live",
        signal_id="signal-041",
        data_source_id="source-041",
        correlation_id="workflow-041",
        incident_id="incident-041",
        derived_source_kind="authoritative",
        derived_trust_tier="tier_1_authoritative_government",
        validation_status="validated",
        evaluated_confidence_score=0.9,
    )
    runner = AmaWorkflow(
        monitoring_executor=Step("monitoring"),
        risk_executor=Step("risk_assessment", infer=True),
        evacuation_executor=Step("evacuation"),
        resource_executor=Step("resource"),
        communication_executor=Step("communication", infer=True),
        hitl_gate=SimpleNamespace(run=hitl),
    )
    try:
        doc = await runner.run_incident(incident={"incident_id": event.incident_id}, tenant_id=event.tenant_id)
        recommendation = workflow._build_recommendation(event, doc)
        alert = workflow._build_draft_alert(event, doc, recommendation)
        workflow._emit_llm_call_timeline_events(event, recommendation, alert)
        rows = bucket.get(event.incident_id, [])
        actual_requests = common_observations.requests if case == "common-success" else requests
        assert len(actual_requests) == (0 if case == "no-call" else 2)
        assert len(rows) == count
        assert model_writer.records == [], "Timeline projection must not invent an opt-out or another audit owner"
        expected_alias = ("synthetic-exercise-s" if case == "common-success" else "synthetic-live-r") if count else None
        assert recommendation.model_deployment_id == alert.model_deployment_id == expected_alias
        if rows:
            assert {row.payload["call_id"] for row in rows} == {
                request.headers["x-ms-client-request-id"] for request in actual_requests
            }
            assert {row.payload["source_agent"] for row in rows} == {"risk_assessment", "communication"}
            for row in rows:
                assert row.payload["inference_attempted"] is True
                assert row.payload["inference_outcome"] == outcome
                assert (row.payload["model_id"], row.payload["model_version"]) == (MODEL_ID, MODEL_VERSION)
                assert row.payload["actual_token_usage"] == (
                    {"input_tokens": 7, "output_tokens": 2} if case in ("success", "common-success") else None
                )
        assert "_inference_calls" not in recommendation.model_dump()
        assert "_inference_calls" not in alert.model_dump()
    finally:
        for client in clients:
            await client.close()


@pytest.mark.asyncio
async def test_common_stream_final_usage_only_frame_is_not_lost(real_sdk_boundary: Any) -> None:
    from tests.unit.test_llm_inference_attempt_evidence import StreamResponse

    patch, observations = real_sdk_boundary

    async def chunks(self: StreamResponse) -> AsyncIterator[bytes]:
        payload = observations.completion()
        payload["choices"] = [{"index": 0, "delta": {"content": "actual"}, "finish_reason": "stop"}]
        payload["usage"] = None
        yield f"data: {json.dumps(payload)}\n\n".encode()
        payload["choices"] = []
        payload["usage"] = {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9}
        yield f"data: {json.dumps(payload)}\n\ndata: [DONE]\n\n".encode()

    patch.setattr(StreamResponse, "chunks", chunks)
    response = [
        chunk
        async for chunk in LiveFoundryChatClient(credential=SyntheticCredential(observations)).chat_complete_stream(
            model_key="simulation",
            messages=[{"role": "user", "content": "exercise"}],
        )
    ]
    assert len(observations.requests) == 1 and len(response) == 2
    evidence = response[-1].attempt_evidence
    assert evidence and (evidence.inference_attempted, evidence.inference_outcome) == (True, "succeeded")
    assert (evidence.usage_prompt_tokens, evidence.usage_completion_tokens) == (7, 2)
    assert response[-1].delta_text == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("mismatch", ["none", "call-id", "model", "account", "url-deployment"])
async def test_handoff_proof_is_bound_to_id_account_model_and_destination(
    real_sdk_boundary: Any, mismatch: str
) -> None:
    _, observations = real_sdk_boundary
    client = LiveFoundryChatClient(credential=SyntheticCredential(observations))
    resolved = client._resolver.resolve("simulation")
    observation = RequestObservation(correlation_id="binding-041", resolved=resolved, ready=True, observable=True)
    destination = "wrong-destination" if mismatch == "url-deployment" else resolved.deployment_name
    # Use the actual configured account, not an independent synthetic assumption.
    url = f"{resolved.endpoint.rstrip('/')}/openai/deployments/{destination}/chat/completions"
    if mismatch == "account":
        url = f"https://wrong-account.invalid/openai/deployments/{destination}/chat/completions"
    request = httpx.Request(
        "POST",
        url,
        headers={"x-ms-client-request-id": "wrong-id" if mismatch == "call-id" else observation.call_id},
        json={"model": "wrong-model" if mismatch == "model" else resolved.deployment_name},
    )
    observation.handoff(request)
    assert observation.submitted is (mismatch == "none")
    assert observation.evidence().inference_attempted is (True if mismatch == "none" else None)
    observation.attach_failure(TypeError("synthetic response decoding failure"))
    assert observation.evidence().inference_attempted is (True if mismatch == "none" else None)
    assert observation.evidence().inference_outcome == ("failed" if mismatch == "none" else "unknown")
    assert observations.requests == [], "Validation of evidence must not send a request"

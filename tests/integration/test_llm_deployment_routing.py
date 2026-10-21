"""Closed T003 caller inventory exercised through hermetic SDK request boundaries."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from agent_framework import Message
from agent_framework_openai import OpenAIChatClient
from app.services.simulation import controller_service as controller
from common.content_safety import ContentSafetyValidator
from common.foundry_chat_client import FoundryConfigurationError, LiveFoundryChatClient
from common.handoffs import AgentHandoffEvent
from common.llm_client import LLMClient
from common.llm_config import LLMClientConfig
from common.token_budget import UnicodeHeuristicTokenizer
from communication.models import ContentBlock
from communication.translator import AlertDraftingContext, MultilingualTranslator
from dispatcher import agent as dispatcher
from evacuation.agent import EvacuationAgent
from evacuation.runtime import ThreadedDependencyHealthMonitor
from maf_runtime import chat_client as maf
from maf_runtime.agents.communication_agent import CommunicationMafAgent
from maf_runtime.agents.monitoring_agent import MonitoringMafAgent
from maf_runtime.agents.resource_allocation_agent import ResourceAllocationMafAgent
from maf_runtime.agents.risk_assessment_agent import RiskAssessmentMafAgent
from monitoring.agent import MonitoringAgent
from monitoring.indicator_analysis import IndicatorAnalysisService
from openai import AsyncAzureOpenAI
from resource_allocation.agent import ResourceAllocationAgent
from risk_assessment import agent as risk
from risk_assessment.correlation import ContradictionResult, CorrelationResult

from tests.contract.test_llm_deployment_routing import (
    ENDPOINT,
    MESSAGES,
    configure_tiers,
)
from tests.contract.test_llm_deployment_routing import (
    hermetic_routing_environment as hermetic_routing_environment,
)
from tests.contract.test_llm_deployment_routing import (
    sdk_boundary as sdk_boundary,
)
from tests.fixtures.llm_deployment_routing import (
    ALIAS_CSV_ORDERINGS,
    CONFLICTING_CSV_ORDERINGS,
    MODEL_KEY,
    TIER_DEPLOYMENTS,
)
from tests.unit.test_llm_adapter_snapshots import build_controller, controller_events

ORDER_IDS = ("RDS", "RSD", "DRS", "DSR", "SRD", "SDR")
PATH_TIERS = {
    **dict.fromkeys(("C01", "C02", "C03", "C04", "C06", "C10", "C11", "C12"), "reasoning"),
    **dict.fromkeys(("C05", "C07", "C08", "C09"), "drafting"),
    **dict.fromkeys(("C13", "C14", "C15", "C16"), "reasoning"),
    **dict.fromkeys(("C17", "C18", "C19", "C20", "C21", "C22", "C23", "A01", "A04"), "simulation"),
    "A02": "reasoning",
    "A03": "drafting",
    "A05": "drafting",
}
DISPATCHER_PATHS = {
    "C18": "monitoring",
    "C19": "planning",
    "C20": "risk-assessment",
    "C21": "communication",
    "C22": "evacuation",
    "C23": "resource-allocation",
}
MAF_PATHS = {
    "C13": (MonitoringMafAgent, {"signal_id": "sig-041", "decision": "escalated", "confidence": 0.8}),
    "C14": (RiskAssessmentMafAgent, {"handoff_id": "hf-041", "decision_type": "assessment_generated"}),
    "C15": (
        CommunicationMafAgent,
        {
            "alert_id": "ca-inc-041-v1",
            "incident_id": "inc-041",
            "version": 1,
            "tenant_id": "exercise-041",
            "mode": "rehearsal",
        },
    ),
    "C16": (ResourceAllocationMafAgent, {"plan_id": "rdp-inc-041-v1", "incident_id": "inc-041"}),
}


@pytest.fixture
def caller_boundaries(sdk_boundary):
    patch, _, _, _ = sdk_boundary
    configure_tiers(patch)
    patch.setattr("azure.identity.DefaultAzureCredential", lambda **kwargs: object())
    patch.setattr("azure.identity.get_bearer_token_provider", lambda *args: lambda: "synthetic-offline-token")
    patch.setattr("common.llm_mixin.create_tokenizer", lambda *args: UnicodeHeuristicTokenizer())
    patch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", "")
    patch.setenv("AZURE_SEARCH_ENDPOINT", "")
    patch.setenv("AZURE_COSMOS_ENDPOINT", "")
    return sdk_boundary


@pytest.fixture
def maf_http(caller_boundaries):
    patch, _, _, _ = caller_boundaries
    state = {"text": "ok"}
    requests = []
    clients = []
    patch.setattr(maf, "_shared_token_provider", lambda: lambda: "synthetic-offline-token")
    patch.setattr(
        "maf_runtime.middleware.audit_middleware._get_writer",
        lambda: SimpleNamespace(write=AsyncMock()),
    )

    def handle(request):
        requests.append((str(request.url), json.loads(request.content)))
        return httpx.Response(
            200,
            json={
                "id": "response-041",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "provider-response-is-not-routing-authority",
                "output": [
                    {
                        "id": "message-041",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": state["text"], "annotations": []}],
                    }
                ],
                "usage": {"input_tokens": 7, "output_tokens": 2, "total_tokens": 9},
            },
        )

    def sdk_factory(**settings):
        transport = AsyncAzureOpenAI(
            azure_endpoint=settings["azure_endpoint"],
            api_version=settings["api_version"],
            azure_ad_token_provider=settings["credential"],
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
            max_retries=0,
        )
        clients.append(transport)
        return OpenAIChatClient(**settings, async_client=transport)

    patch.setattr(maf, "OpenAIChatClient", sdk_factory)
    return state, requests, clients


@pytest.fixture
def controller_boundary(caller_boundaries):
    patch, _, _, _ = caller_boundaries
    requests = []
    constructors = []
    patch.setattr(controller, "get_rate_limiter", controller.RateLimiter)

    async def chunks(first_round):
        if first_round:
            for args, name, call_id in (("{", "summarise_state", "call-041"), ("}", None, None)):
                tool = SimpleNamespace(index=0, id=call_id, function=SimpleNamespace(name=name, arguments=args))
                yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[tool]))])
        else:
            yield SimpleNamespace(
                choices=[SimpleNamespace(delta=SimpleNamespace(content="exercise summary", tool_calls=None))]
            )

    def sdk_factory(**settings):
        constructors.append(settings)

        async def create(**request):
            requests.append(copy.deepcopy(request))
            patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "changed-during-tool-loop")
            return chunks(len(requests) == 1)

        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    patch.setattr("openai.AsyncAzureOpenAI", sdk_factory)
    return requests, constructors


def handoff():
    return AgentHandoffEvent(
        handoff_id="hf-041",
        incident_id="inc-041",
        source_agent="risk_assessment",
        target_agent="evacuation",
        scope_key="exercise-041:inc-041",
        confidence=0.8,
        payload={},
        tenant_id="exercise-041",
    )


def assessment():
    return risk.HazardAssessment(
        hazard_assessment_id="ha-inc-041-spread_prediction-v1",
        incident_id="inc-041",
        assessment_type="spread_prediction",
        input_signal_ids=["sig-041"],
        summary="Synthetic evidence sig-041",
        confidence_level="high",
        generated_at=datetime.now(UTC),
        version=1,
        confidence_score=0.8,
        confidence_adjusted=0.8,
        severity_level="high",
    )


async def call_common_path(path, valid=True):
    if path in ("C01", "C02", "C03", "C04"):
        agent = risk.RiskAssessmentAgent()
        if path == "C01":
            agent.generate_assessment(
                "inc-041",
                [{"signal_id": "sig-041", "category": "fire", "payload": {}}],
                CorrelationResult(weighted_confidence=0.8),
                ContradictionResult(),
                "spread_prediction",
                1,
                "synthetic-config",
            )
        elif path == "C02":
            agent._generate_recommendation(assessment(), [], "coordination")
        elif path == "C03":
            agent.recommend_public_alert("inc-041", ["sig-041"])
        else:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=risk.create_app(agent=agent)), base_url="http://offline"
            ) as http:
                response = await http.get("/health")
                assert response.status_code == 200
                expected = "healthy" if valid else "offline"
                assert response.json()["checks"]["llm_connectivity"]["status"] == expected
    elif path in ("C05", "C06"):
        envelope = SimpleNamespace(
            category="fire",
            source=SimpleNamespace(kind="authoritative"),
            incidentId="inc-041",
            payload={"summary": "synthetic exercise"},
        )
        agent = MonitoringAgent(llm_client=LLMClient(LLMClientConfig()))
        if path == "C05":
            agent.summarize_signal(envelope)
        else:
            await agent.evaluate_escalated_signal(envelope)
    elif path == "C07":
        IndicatorAnalysisService(
            llm_client=LLMClient(LLMClientConfig()), content_safety=ContentSafetyValidator()
        ).analyse_cross_domain_correlations(
            [
                {"domain": "social", "indicator_name": "health", "trend": "negative"},
                {"domain": "economic", "indicator_name": "employment", "trend": "negative"},
            ]
        )
    elif path in ("C08", "C09"):
        translator = MultilingualTranslator(embedding_client=lambda text: [1.0, 0.0])
        if path == "C08":
            translator._generate_content(
                language_code="en-AU",
                hazard_type="fire",
                severity="high",
                alert_type="warning",
                template_values={"location": "synthetic location"},
                en_au_reference=None,
                change_type="initial",
                deadline_monotonic=None,
                source_context=AlertDraftingContext(
                    hazard_type="fire",
                    severity="high",
                    alert_type="warning",
                    location="synthetic location",
                    effective_time="",
                    severity_detail="",
                    wind_speed="",
                    help_url="",
                    recommendation_summary="",
                    recommendation_explanation="",
                ),
            )
        else:
            content = ContentBlock(language_code="it", title="Avviso", body="Prova", action_items="Attendere")
            original = ContentBlock(language_code="en-AU", title="Alert", body="Exercise", action_items="Wait")
            assert translator.back_translate_and_score(content, original) == pytest.approx(1.0)
    elif path in ("C10", "C11"):
        agent = EvacuationAgent()
        if path == "C10":
            agent._pipeline._stage_8_plan_summary(
                handoff(),
                [],
                [],
                [],
                [],
                [],
                {},
                "exercise-041:inc-041",
                "exercise-041",
                [],
            )
        else:
            ThreadedDependencyHealthMonitor(agent, probe_timeout_seconds=2).probe_once()
            assert agent._llm_health.status == ("healthy" if valid else "offline")
    elif path == "C12":
        ResourceAllocationAgent()._pipeline._generate_summary(handoff(), [], [], [], None, 0.8)
    elif path == "A01":
        LiveFoundryChatClient(credential=object()).chat_complete(model_key="simulation", messages=MESSAGES)
    else:
        chunks = [
            chunk
            async for chunk in LiveFoundryChatClient(credential=object()).chat_complete_stream(
                model_key=PATH_TIERS[path], messages=MESSAGES
            )
        ]
        identity = chunks[-1].attempt_evidence.resolved_identity
        assert identity.deployment_name == dict(TIER_DEPLOYMENTS)[PATH_TIERS[path]]


async def invoke_role(app, role):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://offline") as http:
        response = await http.post(
            f"/{role}/invoke",
            json={"tenant_id": "exercise-041", "question": "summarise the exercise"},
            headers={"X-Tenant-Id": "exercise-041"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["citations"] == []
        assert len(body["prompt_hash"]) == 64
        assert body["invocation_id"]
        return body


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", ALIAS_CSV_ORDERINGS, ids=ORDER_IDS)
@pytest.mark.parametrize("path", sorted(PATH_TIERS))
async def test_inventory_request_routing(path, raw, caller_boundaries, maf_http, controller_boundary):
    patch, spy, common_requests, _ = caller_boundaries
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    destination = dict(TIER_DEPLOYMENTS)[PATH_TIERS[path]]
    if path in MAF_PATHS or path == "A05":
        state, requests, clients = maf_http
        try:
            if path == "A05":
                client = maf.build_azure_openai_chat_client(model_tier="drafting")
                await client.get_response([Message(role="user", contents=["synthetic probe"])])
            else:
                facade_class, payload = MAF_PATHS[path]
                state["text"] = json.dumps(payload)
                facade = facade_class(retrieval_service=object())
                result = await facade.run_maf({"incident_id": "inc-041"})
                assert isinstance(result, facade.output_schema)
            assert len(requests) == 1
            assert requests[0][0].startswith(f"{ENDPOINT}/openai/responses?")
            assert requests[0][1]["model"] == destination
        finally:
            for client in clients:
                await client.close()
    elif path == "C17":
        requests, constructors = controller_boundary
        service = build_controller(patch)
        events = await controller_events(service)
        assert len(requests) == 2
        assert all(request["model"] == destination for request in requests)
        assert all(request["stream"] and request["tools"] == controller.TOOL_SCHEMAS for request in requests)
        assert all(request["tool_choice"] == "auto" for request in requests)
        assert constructors[0]["azure_endpoint"] == ENDPOINT
        assert requests[1]["messages"][-1]["role"] == "tool"
        assert requests[1]["messages"][-1]["tool_call_id"] == "call-041"
        service._execute_tool.assert_awaited_once()
        assert [event.event for event in events] == [
            "turn.start",
            "tool.call",
            "tool.result",
            "turn.delta",
            "turn.end",
        ]
    else:
        if path in DISPATCHER_PATHS:
            role = DISPATCHER_PATHS[path]
            reply = await invoke_role(dispatcher.create_app(), role)
            assert reply["model_deployment"] is None
            assert (reply["inference_attempted"], reply["inference_outcome"]) == (None, "unknown")
            assert reply["summary"] == "ok"
            assert common_requests[0][1]["messages"][0]["content"] == dispatcher._ROLE_SYSTEM[role]
        else:
            await call_common_path(path)
        assert spy.submissions == [("sdk-request", destination)]
        assert common_requests[0][1]["model"] == destination
        assert common_requests[0][0] == f"{ENDPOINT}/openai/deployments/{destination}"


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [None, "", " "], ids=["absent", "empty", "whitespace"])
async def test_simulation_required_on_every_public_role_and_controller(value, caller_boundaries, controller_boundary):
    patch, spy, _, _ = caller_boundaries
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", ALIAS_CSV_ORDERINGS[0])
    if value is None:
        patch.delenv("AZURE_AI_SIMULATION_DEPLOYMENT")
    else:
        patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", value)
    app = dispatcher.create_app()
    for role in DISPATCHER_PATHS.values():
        reply = await invoke_role(app, role)
        assert "[configuration-error]" in reply["summary"]
        assert "AZURE_AI_SIMULATION_DEPLOYMENT" in reply["summary"]
        assert reply["model_deployment"] is None
    events = await controller_events(build_controller(patch))
    assert [event.event for event in events] == ["turn.start", "error"]
    assert events[-1].data["code"] == "openai_unavailable"
    assert "AZURE_AI_SIMULATION_DEPLOYMENT" in events[-1].data["message"]
    assert spy.submissions == []
    assert controller_boundary == ([], [])
    LiveFoundryChatClient(credential=object()).chat_complete(model_key="reasoning", messages=MESSAGES)
    assert spy.submissions == [("sdk-request", dict(TIER_DEPLOYMENTS)["reasoning"])]


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", CONFLICTING_CSV_ORDERINGS, ids=ORDER_IDS)
async def test_conflicts_reach_no_adapter_request(raw, caller_boundaries, maf_http, controller_boundary):
    patch, spy, _, _ = caller_boundaries
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    for role in DISPATCHER_PATHS.values():
        reply = await invoke_role(dispatcher.create_app(), role)
        assert "[configuration-error]" in reply["summary"]
        assert MODEL_KEY in reply["summary"]
        assert reply["model_deployment"] is None
    events = await controller_events(build_controller(patch))
    assert events[-1].event == "error"
    assert MODEL_KEY in events[-1].data["message"]
    for tier in ("reasoning", "drafting", "simulation"):
        with pytest.raises(FoundryConfigurationError, match="conflicting"):
            LiveFoundryChatClient(credential=object()).chat_complete(model_key=tier, messages=MESSAGES)
        with pytest.raises(FoundryConfigurationError, match="conflicting"):
            _ = [
                chunk
                async for chunk in LiveFoundryChatClient(credential=object()).chat_complete_stream(
                    model_key=tier, messages=MESSAGES
                )
            ]
    for path in sorted(key for key in PATH_TIERS if key.startswith("C") and int(key[1:]) <= 12):
        try:
            await call_common_path(path, valid=False)
        except FoundryConfigurationError as exc:
            assert "conflicting" in str(exc)
    for facade_class, _ in MAF_PATHS.values():
        with pytest.raises(ValueError, match="conflicting"):
            await facade_class(retrieval_service=object()).run_maf("synthetic exercise")
    with pytest.raises(ValueError, match="conflicting"):
        maf.build_azure_openai_chat_client(model_tier="drafting")
    assert spy.submissions == []
    assert maf_http[1] == []
    assert controller_boundary == ([], [])


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["alias", "exact", "base"])
@pytest.mark.parametrize("mixed", [False, True], ids=["both-legacy", "mixed-explicit-legacy"])
@pytest.mark.parametrize("collision", [False, True], ids=["distinct", "collision"])
async def test_effective_legacy_isolation_at_public_requests(
    mode,
    mixed,
    collision,
    caller_boundaries,
    controller_boundary,
):
    patch, spy, _, _ = caller_boundaries
    entries = []
    simulation = dict(TIER_DEPLOYMENTS)["simulation"]
    for tier in ("reasoning", "drafting"):
        for suffix in ("DEPLOYMENT", "MODEL_ID", "MODEL_VERSION", "MODEL_KEY"):
            patch.delenv(f"AZURE_AI_{tier.upper()}_{suffix}")
        destination = simulation if collision and tier == "drafting" else f"legacy-{tier}"
        if mixed and tier == "reasoning":
            patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", destination)
        elif mode == "alias":
            entries.append(f"{tier}={destination}")
        else:
            key = f"synthetic-{tier}" + ("@opaque" if mode == "exact" else "")
            patch.setenv(f"AZURE_AI_{tier.upper()}_MODEL_KEY", key)
            entries.append(f"{key}={destination}")
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", ",".join(entries))
    app = dispatcher.create_app()
    for role in DISPATCHER_PATHS.values():
        reply = await invoke_role(app, role)
        if collision:
            assert "distinct" in reply["summary"]
            assert reply["model_deployment"] is None
        else:
            assert reply["model_deployment"] is None
            assert (reply["inference_attempted"], reply["inference_outcome"]) == (None, "unknown")
    events = await controller_events(build_controller(patch))
    requests, _ = controller_boundary
    if collision:
        assert [event.event for event in events] == ["turn.start", "error"]
        assert "distinct" in events[-1].data["message"]
        assert spy.submissions == []
        assert requests == []
    else:
        assert events[-1].event == "turn.end"
        assert spy.submissions == [("sdk-request", simulation)] * 6
        assert [request["model"] for request in requests] == [simulation, simulation]

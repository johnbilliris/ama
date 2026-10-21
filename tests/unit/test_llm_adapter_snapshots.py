"""Focused adapter snapshot/error regressions, not the later acceptance sweep."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from app.services.simulation import controller_service as controller
from dispatcher import agent as dispatcher

from tests.fixtures.llm_deployment_routing import routing_environment


@pytest_asyncio.fixture
async def adapter_environment():
    with routing_environment() as patch:
        patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://synthetic.services.ai.azure.com")
        patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
        for tier, destination in (("reasoning", "live-r"), ("drafting", "live-d"), ("simulation", "exercise-s")):
            patch.setenv(f"AZURE_AI_{tier.upper()}_DEPLOYMENT", destination)
        yield patch


def endpoint(app, path):
    return next(route.endpoint for route in app.routes if getattr(route, "path", None) == path)


@pytest.mark.asyncio
async def test_dispatcher_roles_keep_captured_simulation_target(adapter_environment):
    patch = adapter_environment
    requests = []

    def sdk_factory(**settings):
        def complete(**request):
            requests.append((settings["endpoint"], request))
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="ok"), finish_reason="stop")],
                usage=SimpleNamespace(prompt_tokens=2, completion_tokens=1),
            )

        return SimpleNamespace(complete=complete)

    patch.setattr("azure.ai.inference.ChatCompletionsClient", sdk_factory)
    patch.setattr("azure.identity.DefaultAzureCredential", lambda: object())
    app = dispatcher.create_app()
    patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "mutated-after-app")
    patch.setenv("AZURE_AI_SIMULATION_MODEL_KEY", "reasoning")
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://mutated.invalid")
    assert (await endpoint(app, "/health")())["llm"] == "ready"
    for role in sorted(dispatcher._ROLES):
        reply = await endpoint(app, "/{role}/invoke")(
            role, dispatcher.InvokeRequest(tenant_id="synthetic-tenant", question="exercise probe")
        )
        # This opaque SDK spy proves routing arguments, not a transport handoff.
        assert reply.model_deployment is None
        assert (reply.inference_attempted, reply.inference_outcome) == (None, "unknown")
        assert reply.summary == "ok"
    assert len(requests) == 6
    assert all(url == "https://synthetic.services.ai.azure.com" for url, _ in requests)
    assert all(request["model"] == "exercise-s" for _, request in requests)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setting,value,diagnostic",
    [
        ("AZURE_AI_SIMULATION_DEPLOYMENT", None, "AZURE_AI_SIMULATION_DEPLOYMENT"),
        ("AZURE_AI_SIMULATION_DEPLOYMENT", "", "AZURE_AI_SIMULATION_DEPLOYMENT"),
        ("AZURE_AI_SIMULATION_DEPLOYMENT", "live-r", "distinct"),
        ("AZURE_AI_PROJECT_DEPLOYMENTS", "shared=a,shared=b", "conflicting"),
        ("AZURE_AI_REASONING_DEPLOYMENT", None, "isolation"),
    ],
)
async def test_dispatcher_invalid_configuration_is_degraded_before_sdk(setting, value, diagnostic, adapter_environment):
    patch = adapter_environment
    if value is None:
        patch.delenv(setting)
    else:
        patch.setenv(setting, value)
    constructors = []
    patch.setattr("azure.ai.inference.ChatCompletionsClient", lambda **kwargs: constructors.append(kwargs))
    app = dispatcher.create_app()
    assert (await endpoint(app, "/health")())["llm"] == "degraded"
    reply = await endpoint(app, "/{role}/invoke")(
        "monitoring", dispatcher.InvokeRequest(tenant_id="synthetic-tenant", question="exercise probe")
    )
    assert "(degraded)" in reply.summary
    assert "[configuration-error]" in reply.summary
    assert diagnostic in reply.summary
    assert reply.model_deployment is None
    assert constructors == []


def build_controller(patch):
    patch.setattr(controller, "_build_default_retrieval_service", lambda: None)
    service = controller.SimulationControllerService(history_repo=SimpleNamespace())
    patch.setattr(service, "_persist_turn_async", AsyncMock())
    patch.setattr(service, "_load_history_messages_async", AsyncMock(return_value=[]))
    patch.setattr(service, "_execute_tool", AsyncMock(return_value={"outcome": "ok"}))
    return service


async def controller_events(service, mode="foundry"):
    return [
        event
        async for event in service.stream_turn(
            tenant_id="synthetic-tenant",
            simulation_id="synthetic-simulation",
            user_oid="synthetic-user",
            user_message="summarise the exercise",
            mode=mode,
        )
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setting,value,diagnostic",
    [
        ("AZURE_AI_SIMULATION_DEPLOYMENT", None, "AZURE_AI_SIMULATION_DEPLOYMENT"),
        ("AZURE_AI_SIMULATION_DEPLOYMENT", "", "AZURE_AI_SIMULATION_DEPLOYMENT"),
        ("AZURE_AI_SIMULATION_DEPLOYMENT", "live-d", "distinct"),
        ("AZURE_AI_PROJECT_DEPLOYMENTS", "shared=a,shared=b", "conflicting"),
        ("AZURE_AI_REASONING_DEPLOYMENT", None, "isolation"),
        ("AZURE_AI_PROJECT_REGION", None, "AZURE_AI_PROJECT_REGION"),
    ],
)
async def test_controller_invalid_snapshot_preserves_error_order_without_sdk(
    setting, value, diagnostic, adapter_environment
):
    patch = adapter_environment
    if value is None:
        patch.delenv(setting)
    else:
        patch.setenv(setting, value)
    constructors = []
    patch.setattr("openai.AsyncAzureOpenAI", lambda **kwargs: constructors.append(kwargs))
    service = build_controller(patch)
    patch.setenv(setting, "repaired-after-construction")
    events = await controller_events(service)
    assert [event.event for event in events] == ["turn.start", "error"]
    assert events[-1].data["code"] == "openai_unavailable"
    assert diagnostic in events[-1].data["message"]
    assert constructors == []


@pytest.mark.asyncio
async def test_controller_missing_endpoint_is_not_a_successful_offline_fallback(adapter_environment):
    patch = adapter_environment
    patch.delenv("AZURE_AI_PROJECT_ENDPOINT")
    service = build_controller(patch)
    events = await controller_events(service, mode=None)
    assert [event.event for event in events] == ["turn.start", "error"]
    assert events[-1].data["code"] == "openai_unavailable"
    assert "AZURE_AI_PROJECT_ENDPOINT" in events[-1].data["message"]


@pytest.mark.asyncio
async def test_controller_tool_rounds_keep_one_frozen_simulation_destination(adapter_environment):
    patch = adapter_environment
    requests = []
    constructors = []

    async def chunks(first_round):
        if first_round:
            tool = SimpleNamespace(
                index=0, id="synthetic-call", function=SimpleNamespace(name="summarise_state", arguments="{}")
            )
            delta = SimpleNamespace(content=None, tool_calls=[tool])
        else:
            delta = SimpleNamespace(content="exercise summary", tool_calls=None)
        yield SimpleNamespace(choices=[SimpleNamespace(delta=delta)])

    def sdk_factory(**settings):
        constructors.append(settings)

        async def create(**request):
            requests.append(request)
            patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "mutated-during-tool-loop")
            return chunks(len(requests) == 1)

        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    patch.setattr("openai.AsyncAzureOpenAI", sdk_factory)
    patch.setattr("azure.identity.DefaultAzureCredential", lambda **kwargs: object())
    patch.setattr("azure.identity.get_bearer_token_provider", lambda *args: lambda: "synthetic-offline-token")
    service = build_controller(patch)
    patch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "mutated-after-construction")
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://mutated.invalid")
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "shared=invalid-a,shared=invalid-b")
    events = await controller_events(service)
    assert len(requests) == 2
    assert all(request["model"] == "exercise-s" for request in requests)
    assert all(request["stream"] and request["tools"] == controller.TOOL_SCHEMAS for request in requests)
    assert constructors[0]["azure_endpoint"] == "https://synthetic.services.ai.azure.com"
    assert "azure_ad_token_provider" in constructors[0]
    assert [event.event for event in events] == [
        "turn.start",
        "tool.call",
        "tool.result",
        "turn.delta",
        "turn.end",
    ]

"""Hermetic SDK request-boundary regressions for common chat and MAF."""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from agent_framework import Message
from agent_framework_openai import OpenAIChatClient
from common.foundry_chat_client import FoundryConfigurationError, LiveFoundryChatClient
from common.llm_client import LLMClient
from common.llm_config import LLMClientConfig, MetadataSource
from maf_runtime import chat_client as maf
from openai import AsyncAzureOpenAI

from tests.fixtures.llm_deployment_routing import (
    CONFLICTING_CSV_ORDERINGS,
    MODEL_ID,
    MODEL_KEY,
    MODEL_VERSION,
    TIER_DEPLOYMENTS,
    TIER_ORDERINGS,
    RequestSubmissionSpy,
    routing_environment,
)

ENDPOINT = "https://synthetic.cognitiveservices.azure.com"
MESSAGES = [{"role": "user", "content": "synthetic prompt must not enter diagnostics"}]


@pytest_asyncio.fixture
async def hermetic_routing_environment():
    # Windows creates a local socketpair for the loop before the outbound-network guard is installed.
    with routing_environment() as patch:
        yield patch


@pytest.fixture
def sdk_boundary(hermetic_routing_environment):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", ENDPOINT)
    patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
    spy = RequestSubmissionSpy()
    requests = []
    constructors = []

    def result():
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=7, completion_tokens=2),
        )

    def submit(endpoint, request):
        spy.submit(call_id="sdk-request", deployment_name=request["model"])
        requests.append((endpoint, request))

    def sync_factory(**settings):
        constructors.append(settings)

        def complete(**request):
            submit(settings["endpoint"], request)
            return result()

        return SimpleNamespace(complete=complete)

    def async_factory(**settings):
        constructors.append(settings)

        async def chunks():
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ok"), finish_reason="stop")])

        async def complete(**request):
            submit(settings["endpoint"], request)
            return chunks()

        return SimpleNamespace(complete=complete)

    patch.setattr("azure.ai.inference.ChatCompletionsClient", sync_factory)
    patch.setattr("azure.ai.inference.aio.ChatCompletionsClient", async_factory)
    return patch, spy, requests, constructors


def configure_tiers(patch, ordering=TIER_DEPLOYMENTS):
    for tier, destination in ordering:
        patch.setenv(f"AZURE_AI_{tier.upper()}_DEPLOYMENT", destination)
        patch.setenv(f"AZURE_AI_{tier.upper()}_MODEL_ID", MODEL_ID)
        patch.setenv(f"AZURE_AI_{tier.upper()}_MODEL_VERSION", MODEL_VERSION)
        patch.setenv(f"AZURE_AI_{tier.upper()}_MODEL_KEY", MODEL_KEY)


async def complete(client, kind, tier, **kwargs):
    if kind == "sync":
        return client.chat_complete(model_key=tier, messages=MESSAGES, **kwargs)
    return [chunk async for chunk in client.chat_complete_stream(model_key=tier, messages=MESSAGES, **kwargs)]


@pytest.mark.asyncio
@pytest.mark.parametrize("ordering", TIER_ORDERINGS, ids=[f"order-{i}" for i in range(6)])
@pytest.mark.parametrize("tier,destination", TIER_DEPLOYMENTS)
@pytest.mark.parametrize("kind", ["sync", "stream"])
@pytest.mark.parametrize("endpoint", [ENDPOINT, "https://synthetic.services.ai.azure.com"])
async def test_common_requests_explicit_tiers_without_csv_aliases(
    ordering, tier, destination, kind, endpoint, sdk_boundary
):
    patch, spy, requests, constructors = sdk_boundary
    configure_tiers(patch, ordering)
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "text-embedding-3-large@1=synthetic-embedding")
    client = LiveFoundryChatClient(credential=object())
    await complete(client, kind, tier, max_tokens=17, timeout_s=4, temperature=0.2)
    assert spy.submissions == [("sdk-request", destination)]
    url, request = requests[0]
    expected_url = f"{endpoint}/openai/deployments/{destination}" if endpoint == ENDPOINT else endpoint
    assert url == expected_url
    assert request["model"] == destination
    assert request["messages"] == MESSAGES
    assert request["timeout"] == 4
    assert request["temperature"] == 0.2
    assert constructors[0]["credential_scopes"] == ["https://cognitiveservices.azure.com/.default"]
    if endpoint == ENDPOINT:
        assert request["model_extras"] == {"max_completion_tokens": 17}
    else:
        assert request["max_tokens"] == 17


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["sync", "stream"])
@pytest.mark.parametrize("association", ["matching-a", "different-b", "absent"])
async def test_request_identity_is_not_borrowed_from_another_destination(kind, association, sdk_boundary):
    patch, spy, _, _ = sdk_boundary
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "explicit-a")
    patch.setenv("AZURE_AI_REASONING_MODEL_KEY", MODEL_KEY)
    raw = (
        ""
        if association == "absent"
        else f"{MODEL_KEY}=" + ("explicit-a" if association == "matching-a" else "legacy-b")
    )
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    response = await complete(LiveFoundryChatClient(credential=object()), kind, "reasoning")
    assert spy.submissions == [("sdk-request", "explicit-a")]
    terminal = response if kind == "sync" else response[-1]
    assert terminal.attempt_evidence is not None, "Request must expose resolved identity, not legacy B's identity"
    identity = terminal.attempt_evidence.resolved_identity
    assert identity is not None
    assert identity.deployment_name == "explicit-a"
    if association == "matching-a":
        assert (identity.model_id, identity.model_version) == (MODEL_ID, MODEL_VERSION)
        assert identity.metadata_source is MetadataSource.LEGACY_COORDINATE
        assert identity.metadata_association_reference
    else:
        assert identity.model_id is identity.model_version is None
        assert identity.metadata_source is MetadataSource.UNAVAILABLE
    if kind == "sync":
        assert (terminal.usage_prompt_tokens, terminal.usage_completion_tokens) == (7, 2)


def test_configured_identity_is_independent_of_misleading_deployment_name(sdk_boundary):
    patch, spy, _, _ = sdk_boundary
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "misleading-other-model@wrong-version")
    patch.setenv("AZURE_AI_REASONING_MODEL_ID", MODEL_ID)
    patch.setenv("AZURE_AI_REASONING_MODEL_VERSION", MODEL_VERSION)
    response = LiveFoundryChatClient(credential=object()).chat_complete(model_key="reasoning", messages=MESSAGES)
    assert spy.submissions == [("sdk-request", "misleading-other-model@wrong-version")]
    assert response.attempt_evidence is not None, "Configured model identity must survive the client adapter"
    identity = response.attempt_evidence.resolved_identity
    assert identity is not None
    assert (identity.model_id, identity.model_version) == (MODEL_ID, MODEL_VERSION)
    assert identity.metadata_source is MetadataSource.CONFIGURED
    assert response.attempt_evidence.inference_attempted is None
    assert response.attempt_evidence.inference_outcome == "unknown"
    assert response.raw == {"deployment": "misleading-other-model@wrong-version"}


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["sync", "stream"])
@pytest.mark.parametrize("raw", CONFLICTING_CSV_ORDERINGS)
async def test_common_invalid_raw_map_has_safe_diagnostic_and_zero_requests(kind, raw, sdk_boundary):
    patch, spy, _, _ = sdk_boundary
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "explicit-a")
    try:
        with pytest.raises(FoundryConfigurationError) as error:
            await complete(LiveFoundryChatClient(credential=object()), kind, "reasoning")
        diagnostic = str(error.value)
        assert MODEL_KEY in diagnostic
        assert all(entry.split("=")[1] in diagnostic for entry in raw.split(",")[:2])
        assert MESSAGES[0]["content"] not in diagnostic
    finally:
        assert spy.submissions == []


@pytest.mark.parametrize("mapping", [{"": "bad"}, {"reasoning": ""}, {"reasoning": " "}])
def test_injected_maps_are_validated_before_request(mapping, sdk_boundary):
    _, spy, _, _ = sdk_boundary
    try:
        with pytest.raises(FoundryConfigurationError):
            LiveFoundryChatClient(deployments=mapping, credential=object()).chat_complete(
                model_key="reasoning", messages=MESSAGES
            )
    finally:
        assert spy.submissions == []


@pytest.mark.parametrize("key", [MODEL_KEY, MODEL_ID])
def test_common_legacy_model_key_injection_remains_executable(key, sdk_boundary):
    _, spy, _, _ = sdk_boundary
    response = LiveFoundryChatClient(deployments={key: "deliberate-legacy"}, credential=object()).chat_complete(
        model_key=MODEL_KEY, messages=MESSAGES
    )
    assert response.deployment_id == "deliberate-legacy"
    assert spy.submissions == [("sdk-request", "deliberate-legacy")]


@pytest.mark.parametrize("tier", ["reasoning", "drafting"])
def test_common_wrapper_uses_captured_configuration_not_live_env(tier, sdk_boundary):
    patch, spy, _, _ = sdk_boundary
    configure_tiers(patch)
    cfg = LLMClientConfig()
    patch.setenv(f"AZURE_AI_{tier.upper()}_DEPLOYMENT", "mutated-after-config")
    response = LLMClient(cfg).generate_response(purpose=tier, prompt="synthetic wrapper probe")
    destination = dict(TIER_DEPLOYMENTS)[tier]
    assert response["deployment_id"] == destination
    assert spy.submissions == [("sdk-request", destination)]


@pytest.fixture
def maf_boundary(hermetic_routing_environment):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", ENDPOINT)
    patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
    requests = []
    transports = []
    patch.setattr(maf, "_shared_token_provider", lambda: lambda: "synthetic-offline-token")

    def handle(request):
        requests.append((str(request.url), json.loads(request.content)))
        return httpx.Response(
            200,
            json={
                "id": "synthetic-response",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "provider-response-not-routing-authority",
                "output": [
                    {
                        "id": "synthetic-message",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": "ok", "annotations": []}],
                    }
                ],
                "usage": {"input_tokens": 7, "output_tokens": 2, "total_tokens": 9},
            },
        )

    def sdk_factory(**settings):
        # Only replace HTTP transport; the production factory and MAF request serialization still run.
        transport = AsyncAzureOpenAI(
            azure_endpoint=settings["azure_endpoint"],
            api_version=settings["api_version"],
            azure_ad_token_provider=settings["credential"],
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
            max_retries=0,
        )
        transports.append(transport)
        return OpenAIChatClient(**settings, async_client=transport)

    patch.setattr(maf, "OpenAIChatClient", sdk_factory)
    return patch, requests, transports


async def maf_request(tier, boundary, config=None):
    _, _, transports = boundary
    try:
        client = maf.build_azure_openai_chat_client(model_tier=tier, config=config)
        return await client.get_response([Message(role="user", contents=["synthetic MAF probe"])])
    finally:
        for transport in transports:
            await transport.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("ordering", TIER_ORDERINGS, ids=[f"order-{i}" for i in range(6)])
@pytest.mark.parametrize("tier", ["reasoning", "drafting"])
async def test_maf_actual_requests_need_no_duplicate_csv_alias(ordering, tier, maf_boundary):
    patch, requests, _ = maf_boundary
    configure_tiers(patch, ordering)
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "text-embedding-3-large@1=synthetic-embedding")
    await maf_request(tier, maf_boundary)
    destination = dict(TIER_DEPLOYMENTS)[tier]
    assert len(requests) == 1
    url, body = requests[0]
    assert url.startswith(f"{ENDPOINT}/openai/responses?")
    assert body["model"] == destination


@pytest.mark.asyncio
@pytest.mark.parametrize("tier", ["reasoning", "drafting"])
async def test_maf_qualified_endpoint_preserves_account_responses_route(tier, maf_boundary):
    patch, requests, _ = maf_boundary
    configure_tiers(patch)
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", f"{ENDPOINT}/openai/deployments/synthetic-live-r/")
    await maf_request(tier, maf_boundary)
    assert len(requests) == 1
    url, body = requests[0]
    assert url.startswith(f"{ENDPOINT}/openai/responses?")
    assert body["model"] == dict(TIER_DEPLOYMENTS)[tier]


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["sync", "stream", "maf"])
@pytest.mark.parametrize(
    "endpoint",
    [
        "synthetic.cognitiveservices.azure.com/openai/deployments/live-r",
        f"{ENDPOINT}/openai/deployments/",
        f"{ENDPOINT}/openai/deployments/live-r/chat/completions",
        f"{ENDPOINT}/openai/deployments/live-r?api-version=unapproved",
        f"{ENDPOINT}/openai/deployments/live-r#fragment",
        "https://synthetic-user:do-not-log@synthetic.cognitiveservices.azure.com",
    ],
)
async def test_invalid_endpoint_fails_before_client_construction(endpoint, kind, sdk_boundary):
    patch, spy, _, constructors = sdk_boundary
    configure_tiers(patch)
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)
    error_type = ValueError if kind == "maf" else FoundryConfigurationError
    with pytest.raises(error_type, match="AZURE_AI_PROJECT_ENDPOINT") as caught:
        if kind == "maf":
            maf.build_azure_openai_chat_client(model_tier="reasoning")
        else:
            await complete(LiveFoundryChatClient(credential=object()), kind, "reasoning")
    assert "do-not-log" not in str(caught.value)
    assert constructors == []
    assert spy.submissions == []


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", CONFLICTING_CSV_ORDERINGS)
async def test_maf_invalid_map_retains_value_error_boundary_and_shared_cause(raw, maf_boundary):
    patch, requests, _ = maf_boundary
    configure_tiers(patch)
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    with pytest.raises(ValueError) as error:
        await maf_request("reasoning", maf_boundary)
    assert isinstance(error.value.__cause__, FoundryConfigurationError)
    assert MODEL_KEY in str(error.value.__cause__)
    assert requests == []


@pytest.mark.asyncio
@pytest.mark.parametrize("tier", ["reasoning", "drafting"])
async def test_maf_legacy_test_configuration_still_submits_a_request(tier, maf_boundary):
    patch, requests, _ = maf_boundary
    patch.delenv("AZURE_AI_PROJECT_ENDPOINT")
    cfg = LLMClientConfig(
        endpoint=ENDPOINT,
        reasoning_deployment="test-only-r",
        drafting_deployment="test-only-d",
    )
    await maf_request(tier, maf_boundary, cfg)
    destination = "test-only-r" if tier == "reasoning" else "test-only-d"
    assert len(requests) == 1
    assert requests[0][1]["model"] == destination
    assert requests[0][0].startswith(f"{ENDPOINT}/openai/responses?")


@pytest.mark.asyncio
@pytest.mark.parametrize("tier", ["reasoning", "drafting"])
async def test_maf_captured_explicit_target_survives_environment_mutation(tier, maf_boundary):
    patch, requests, _ = maf_boundary
    configure_tiers(patch)
    cfg = LLMClientConfig()
    patch.setenv(f"AZURE_AI_{tier.upper()}_DEPLOYMENT", "mutated-after-config")
    await maf_request(tier, maf_boundary, cfg)
    destination = dict(TIER_DEPLOYMENTS)[tier]
    assert len(requests) == 1
    assert requests[0][1]["model"] == destination


def test_invalid_foundry_config_cannot_use_legacy_test_fallback(sdk_boundary):
    patch, spy, _, _ = sdk_boundary
    legacy_requests = []

    def forbidden_legacy_sdk(**kwargs):
        legacy_requests.append(kwargs)
        raise AssertionError("Invalid production Foundry settings must not activate legacy transport")

    patch.setattr("openai.AzureOpenAI", forbidden_legacy_sdk)
    patch.setenv("AZURE_OPENAI_ENDPOINT", "https://synthetic-test.openai.azure.com")
    patch.setenv("AZURE_OPENAI_REASONING_DEPLOYMENT", "legacy-test-r")
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "")
    try:
        with pytest.raises(FoundryConfigurationError, match="AZURE_AI_REASONING_DEPLOYMENT"):
            LLMClient(LLMClientConfig()).generate_response(purpose="reasoning", prompt=MESSAGES[0]["content"])
    finally:
        assert spy.submissions == []
        assert legacy_requests == []


@pytest.mark.parametrize("endpoint", [None, "", " "], ids=["absent", "empty", "whitespace"])
def test_foundry_connection_error_never_activates_legacy_test_transport(endpoint, sdk_boundary):
    patch, spy, _, _ = sdk_boundary
    configure_tiers(patch)
    if endpoint is None:
        patch.delenv("AZURE_AI_PROJECT_ENDPOINT")
    else:
        patch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)
    patch.setenv("AZURE_OPENAI_ENDPOINT", "https://synthetic-test.openai.azure.com")
    patch.setenv("AZURE_OPENAI_REASONING_DEPLOYMENT", "legacy-test-r")
    legacy_constructors = []
    patch.setattr("openai.AzureOpenAI", lambda **kwargs: legacy_constructors.append(kwargs))
    cfg = LLMClientConfig()
    with pytest.raises(FoundryConfigurationError, match="AZURE_AI_PROJECT_ENDPOINT"):
        LLMClient(cfg).generate_response(purpose="reasoning", prompt="synthetic probe")
    with pytest.raises(ValueError, match="AZURE_AI_PROJECT_ENDPOINT") as error:
        maf.build_azure_openai_chat_client(model_tier="reasoning", config=cfg)
    assert isinstance(error.value.__cause__, FoundryConfigurationError)
    assert spy.submissions == []
    assert legacy_constructors == []

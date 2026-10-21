"""Independent package parser parity and unchanged embedding/legacy contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import pytest_asyncio
from ama_eval import foundry_client as evaluation
from ama_ingest import embedder as ingestion
from common import foundry_chat_client as common
from common.foundry_query_embedder import FoundryQueryEmbedder
from common.llm_config import LLMClientConfig

from tests.fixtures.llm_deployment_routing import (
    ALIAS_CSV_ORDERINGS,
    IDENTICAL_DUPLICATE_CSV,
    MODEL_ID,
    MODEL_KEY,
    routing_environment,
)

EMBEDDING_KEY = "text-embedding-3-large@1"
EMBEDDING_DESTINATION = "synthetic-embedding"
PARSERS = [
    pytest.param(common._parse_deployment_map, common.FoundryConfigurationError, id="common"),
    pytest.param(evaluation._parse_deployment_map, evaluation.FoundryConfigurationError, id="eval"),
    pytest.param(ingestion._parse_deployment_map, ingestion.EmbedderConfigurationError, id="ingest"),
    pytest.param(
        lambda raw: LLMClientConfig(foundry_deployments=raw or "").foundry_deployment_map(),
        common.FoundryConfigurationError,
        id="config",
    ),
]


@pytest_asyncio.fixture
async def hermetic_routing_environment():
    # Install the guard after Windows has initialized the event loop's local socketpair.
    with routing_environment() as patch:
        yield patch


@pytest.mark.parametrize("parser,error_type", PARSERS)
@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, {}),
        ("", {}),
        (" \t ", {}),
        (IDENTICAL_DUPLICATE_CSV, {MODEL_KEY: "synthetic-live-r"}),
        ("  reasoning = live-r , drafting= live-d  ", {"reasoning": "live-r", "drafting": "live-d"}),
    ],
)
def test_valid_map_grammar_is_identical_across_packages(
    parser, error_type, raw, expected, hermetic_routing_environment
):
    assert parser(raw) == expected


@pytest.mark.parametrize("parser,error_type", PARSERS)
@pytest.mark.parametrize("destinations", [("first-a", "second-b"), ("second-b", "first-a")])
def test_conflicting_pair_orders_fail_with_actionable_diagnostics(
    parser, error_type, destinations, hermetic_routing_environment
):
    first, second = destinations
    raw = f"{MODEL_KEY}={first},{MODEL_KEY}={second}"
    with pytest.raises(error_type) as error:
        parser(raw)
    assert MODEL_KEY in str(error.value)
    assert first in str(error.value)
    assert second in str(error.value)


@pytest.mark.parametrize("parser,error_type", PARSERS)
@pytest.mark.parametrize(
    "raw",
    [
        "missing-equals",
        "=destination",
        "key=",
        "key=  ",
        " =destination",
        "key=destination=extra",
        "key=destination,",
        ",key=destination",
        "key=destination,,other=target",
        "key=destination,  ,other=target",
    ],
)
def test_nonempty_maps_never_silently_discard_malformed_entries(parser, error_type, raw, hermetic_routing_environment):
    with pytest.raises(error_type):
        parser(raw)


@pytest.mark.parametrize("raw", ["", " ", "\t"])
def test_blank_entire_map_is_allowed_on_explicit_chat_path(raw, hermetic_routing_environment):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://synthetic.services.ai.azure.com")
    patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "explicit-r")
    assert common.LiveFoundryChatClient()._resolve("reasoning") == "explicit-r"


@pytest.mark.parametrize("raw", ALIAS_CSV_ORDERINGS)
def test_embedding_coordinate_survives_shared_chat_model_aliases(raw, hermetic_routing_environment):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", f"{raw},{EMBEDDING_KEY}={EMBEDDING_DESTINATION}")
    embedder = ingestion.FoundryEmbedder()
    assert embedder.model_key == EMBEDDING_KEY
    assert embedder.embedding_dims == 3072
    assert embedder._resolve() == EMBEDDING_DESTINATION
    assert MODEL_KEY not in common._parse_deployment_map(f"{raw},{EMBEDDING_KEY}={EMBEDDING_DESTINATION}")


@pytest.mark.parametrize("dims", [3072, 11])
def test_ingest_embedding_request_preserves_model_destination_and_dimensions(dims, hermetic_routing_environment):
    patch = hermetic_routing_environment
    calls = []

    class SDK:
        def __init__(self, **kwargs):
            self.embeddings = self

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.25] * dims)], usage=SimpleNamespace(total_tokens=4)
            )

    patch.setattr("openai.AzureOpenAI", SDK)
    patch.setattr("azure.identity.get_bearer_token_provider", lambda *args: lambda: "synthetic-offline-token")
    embedder = ingestion.FoundryEmbedder(
        endpoint="https://synthetic.cognitiveservices.azure.com",
        deployments={EMBEDDING_KEY: EMBEDDING_DESTINATION},
        credential=object(),
        embedding_dims=dims,
    )
    result = embedder.embed_batch(["synthetic document"])
    assert embedder.model_key == EMBEDDING_KEY
    assert len(result.vectors[0]) == dims
    assert calls[0]["model"] == EMBEDDING_DESTINATION
    assert calls[0]["input"] == ["synthetic document"]


@pytest.mark.asyncio
@pytest.mark.parametrize("returned_dims", [3072, 2])
async def test_direct_query_embedding_retains_env_destination_and_rejects_dimension_mismatch(
    returned_dims, hermetic_routing_environment
):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://synthetic.cognitiveservices.azure.com")
    patch.setenv("EMBEDDING_DEPLOYMENT_NAME", EMBEDDING_DESTINATION)
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "reasoning=unrelated-chat")
    calls = []

    class SDK:
        def __init__(self, **kwargs):
            self.embeddings = self

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.25] * returned_dims)])

    patch.setattr("openai.AzureOpenAI", SDK)
    patch.setattr("azure.identity.get_bearer_token_provider", lambda *args: lambda: "synthetic-offline-token")
    embedder = FoundryQueryEmbedder(credential=object())
    assert embedder.deployment == EMBEDDING_DESTINATION
    assert embedder.expected_dims == 3072
    if returned_dims == 3072:
        assert len(await embedder.embed_query("synthetic query")) == 3072
    else:
        with pytest.raises(RuntimeError, match="2 dims, expected 3072"):
            await embedder.embed_query("synthetic query")
    assert calls == [{"model": EMBEDDING_DESTINATION, "input": ["synthetic query"]}]


@pytest.mark.parametrize("tier", ["reasoning", "drafting", "simulation"])
def test_eval_omitted_shared_coordinate_never_guesses_a_tier(tier, hermetic_routing_environment):
    patch = hermetic_routing_environment
    submissions = []

    def sdk_factory(**kwargs):
        return SimpleNamespace(complete=lambda **request: submissions.append(request))

    patch.setattr("azure.ai.inference.ChatCompletionsClient", sdk_factory)
    patch.setattr("azure.identity.DefaultAzureCredential", lambda: object())
    client = evaluation.FoundryClient(
        endpoint="https://synthetic.services.ai.azure.com",
        deployments={tier: "tier-only-destination"},
    )
    assert client.deployment_for(MODEL_ID, MODEL_KEY.split("@", 1)[1]) is None
    with pytest.raises(evaluation.FoundryConfigurationError, match="no Foundry deployment"):
        client.complete(
            model_id=MODEL_ID,
            version=MODEL_KEY.split("@", 1)[1],
            messages=[{"role": "user", "content": "synthetic eval probe"}],
        )
    assert submissions == []


@pytest.mark.parametrize("target", ["deliberate-live", "deliberate-exercise"])
def test_eval_deliberate_per_run_exact_mapping_remains_supported(target, hermetic_routing_environment):
    patch = hermetic_routing_environment
    submissions = []

    def sdk_factory(**kwargs):
        def complete(**request):
            submissions.append(request)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="ok"), finish_reason="stop")],
                usage=SimpleNamespace(prompt_tokens=3, completion_tokens=1),
            )

        return SimpleNamespace(complete=complete)

    patch.setattr("azure.ai.inference.ChatCompletionsClient", sdk_factory)
    patch.setattr("azure.identity.DefaultAzureCredential", lambda: object())
    client = evaluation.FoundryClient(
        endpoint="https://synthetic.services.ai.azure.com",
        deployments={MODEL_KEY: target},
    )
    assert client.deployment_for(MODEL_ID, MODEL_KEY.split("@", 1)[1]) == target
    response = client.complete(
        model_id=MODEL_ID,
        version=MODEL_KEY.split("@", 1)[1],
        messages=[{"role": "user", "content": "synthetic eval probe"}],
    )
    assert len(submissions) == 1
    assert submissions[0]["model"] == target
    assert response.text == "ok"


@pytest.mark.parametrize("exact", [False, True], ids=["base-only", "exact-over-base"])
def test_non_tier_legacy_exact_then_base_lookup_is_preserved(exact, hermetic_routing_environment):
    mapping = {MODEL_ID: "legacy-base"}
    if exact:
        mapping[MODEL_KEY] = "legacy-exact"
    expected = "legacy-exact" if exact else "legacy-base"
    assert (
        common.LiveFoundryChatClient(
            endpoint="https://synthetic.services.ai.azure.com", region="australiaeast", deployments=mapping
        )._resolve(MODEL_KEY)
        == expected
    )
    assert (
        evaluation.FoundryClient(deployments=mapping).deployment_for(MODEL_ID, MODEL_KEY.split("@", 1)[1]) == expected
    )


COMPATIBILITY_CLIENTS = [
    pytest.param(evaluation.FoundryClient, evaluation.FoundryConfigurationError, "chat_complete", id="eval"),
    pytest.param(ingestion.FoundryEmbedder, ingestion.EmbedderConfigurationError, "embed", id="ingest"),
]


@pytest.mark.parametrize("factory,error_type,seam", COMPATIBILITY_CLIENTS)
@pytest.mark.parametrize("raw", [f"{MODEL_KEY}=first-a,{MODEL_KEY}=second-b", "key=destination,"])
def test_compatibility_injection_cannot_hide_invalid_raw_map(
    factory, error_type, seam, raw, hermetic_routing_environment
):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", raw)
    calls = []
    with pytest.raises(error_type, match="AZURE_AI_PROJECT_DEPLOYMENTS"):
        factory(deployments={MODEL_KEY: "deliberate-run"}, **{seam: lambda **kwargs: calls.append(kwargs)})
    assert calls == []


@pytest.mark.parametrize("factory,error_type,seam", COMPATIBILITY_CLIENTS)
@pytest.mark.parametrize("mapping", [{"": "target"}, {"key": " "}, {None: "target"}, {"key": None}])
def test_compatibility_injected_maps_require_nonempty_strings(
    factory, error_type, seam, mapping, hermetic_routing_environment
):
    with pytest.raises(error_type, match="deployments"):
        factory(deployments=mapping)


@pytest.mark.parametrize("factory,error_type,seam", COMPATIBILITY_CLIENTS)
@pytest.mark.parametrize("second", ["first-a", "second-b"])
def test_compatibility_injected_maps_validate_normalized_duplicates(
    factory, error_type, seam, second, hermetic_routing_environment
):
    hermetic_routing_environment.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", f"{MODEL_KEY}=configured-destination")
    mapping = {MODEL_KEY: "first-a", f" {MODEL_KEY} ": f" {second} "}
    if second != "first-a":
        with pytest.raises(error_type) as error:
            factory(deployments=mapping)
        assert all(value in str(error.value) for value in ("deployments", MODEL_KEY, "first-a", second))
    else:
        client = factory(deployments=mapping)
        assert client._deployments == {MODEL_KEY: "first-a"}
        mapping[MODEL_KEY] = "mutated-after-construction"
        assert client._deployments == {MODEL_KEY: "first-a"}


@pytest.mark.parametrize("exact", [False, True], ids=["base-only", "exact-over-base"])
def test_ingest_embedding_exact_then_base_lookup_is_preserved(exact, hermetic_routing_environment):
    mapping = {"text-embedding-3-large": "embedding-base"}
    if exact:
        mapping[EMBEDDING_KEY] = "embedding-exact"
    embedder = ingestion.FoundryEmbedder(deployments=mapping)
    assert embedder._resolve() == ("embedding-exact" if exact else "embedding-base")
    assert embedder.model_key == EMBEDDING_KEY
    assert embedder.embedding_dims == 3072

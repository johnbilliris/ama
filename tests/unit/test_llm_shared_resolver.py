"""Direct shared-API checks while transport adoption remains a later task."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from common import llm_config as routing
from common.foundry_chat_client import FoundryConfigurationError

from tests.fixtures.llm_deployment_routing import CONFLICTING_CSV_ORDERINGS

ENDPOINT = "https://synthetic.services.ai.azure.com"
REVISION = "synthetic-shared-resolver"


def resolver(**settings: str) -> routing.DeploymentResolver:
    return routing.DeploymentResolver.from_environment(
        {"AZURE_AI_PROJECT_ENDPOINT": ENDPOINT, "AZURE_AI_PROJECT_REGION": "australiaeast", **settings},
        configuration_revision=REVISION,
    )


def test_shared_raw_validation_precedes_explicit_resolution() -> None:
    assert routing.FoundryConfigurationError is FoundryConfigurationError
    for raw in CONFLICTING_CSV_ORDERINGS:
        with pytest.raises(FoundryConfigurationError) as error:
            resolver(AZURE_AI_REASONING_DEPLOYMENT="explicit-a", AZURE_AI_PROJECT_DEPLOYMENTS=raw)
        first, second = [entry.split("=") for entry in raw.split(",")[:2]]
        assert first[0] in str(error.value)
        assert first[1] in str(error.value)
        assert second[1] in str(error.value)
    for raw in ("bad", "=a", "key=", "key=a=b", "key=a,", ",key=a", "key=a,,other=b"):
        with pytest.raises(FoundryConfigurationError, match="AZURE_AI_PROJECT_DEPLOYMENTS"):
            resolver(AZURE_AI_REASONING_DEPLOYMENT="explicit-a", AZURE_AI_PROJECT_DEPLOYMENTS=raw)
    assert routing.parse_deployment_map(" key = a , key=a, embedding=e ") == {"key": "a", "embedding": "e"}
    for raw in (None, "", " \t "):
        assert routing.parse_deployment_map(raw) == {}


def test_injected_maps_are_validated_copied_and_do_not_hide_bad_raw_maps() -> None:
    configuration = resolver().configuration
    for entries in ({"": "a"}, {"key": " "}, {" key ": "a", "key": "b"}):
        with pytest.raises(FoundryConfigurationError):
            routing.DeploymentResolver(configuration, deployments=entries)
    entries = {" model@opaque ": " target "}
    captured = routing.DeploymentResolver(configuration, deployments=entries)
    entries[" model@opaque "] = "mutated"
    assert captured.resolve_legacy("model@opaque").deployment_name == "target"
    assert captured.resolve_legacy("model@opaque").model_version == "opaque"
    with pytest.raises(FrozenInstanceError):
        setattr(captured, "configuration", configuration)
    configuration = routing.RoutingConfiguration.from_environment(
        {"AZURE_AI_PROJECT_DEPLOYMENTS": "key=a,key=b"}, configuration_revision=REVISION
    )
    with pytest.raises(FoundryConfigurationError):
        routing.DeploymentResolver(configuration, deployments={})


def test_live_precedence_and_metadata_follow_the_selected_destination() -> None:
    settings = {
        "AZURE_AI_REASONING_MODEL_KEY": "model@opaque",
        "AZURE_AI_PROJECT_DEPLOYMENTS": "reasoning=alias-a,model@opaque=exact-b,model=base-c",
    }
    explicit = resolver(**settings, AZURE_AI_REASONING_DEPLOYMENT="explicit-a").resolve("reasoning")
    assert (explicit.deployment_name, explicit.resolution_source) == ("explicit-a", "explicit_tier")
    assert explicit.model_id is explicit.model_version is None
    assert resolver(**settings).resolve("reasoning").deployment_name == "alias-a"
    settings["AZURE_AI_PROJECT_DEPLOYMENTS"] = "model@opaque=exact-b,model=base-c"
    exact = resolver(**settings).resolve("reasoning")
    assert (exact.deployment_name, exact.resolution_source, exact.model_id, exact.model_version) == (
        "exact-b",
        "legacy_exact",
        "model",
        "opaque",
    )
    assert exact.metadata_association_reference
    settings["AZURE_AI_PROJECT_DEPLOYMENTS"] = "model=base-c"
    base = resolver(**settings).resolve("reasoning")
    assert (base.deployment_name, base.resolution_source, base.model_id, base.model_version) == (
        "base-c",
        "legacy_base",
        "model",
        None,
    )
    matched = resolver(
        AZURE_AI_REASONING_DEPLOYMENT="explicit-a",
        AZURE_AI_REASONING_MODEL_KEY="model@opaque",
        AZURE_AI_PROJECT_DEPLOYMENTS="model@opaque=explicit-a",
    ).resolve("reasoning")
    assert (matched.model_id, matched.model_version, matched.metadata_source) == (
        "model",
        "opaque",
        "legacy_coordinate",
    )


def test_snapshot_metadata_and_connection_errors_are_actionable_and_frozen() -> None:
    settings = {
        "AZURE_AI_PROJECT_ENDPOINT": ENDPOINT,
        "AZURE_AI_PROJECT_REGION": "australiaeast",
        "AZURE_AI_REASONING_DEPLOYMENT": "name-not-model",
        "AZURE_AI_REASONING_MODEL_ID": "model",
        "AZURE_AI_REASONING_MODEL_VERSION": "opaque",
    }
    captured = routing.DeploymentResolver.from_environment(settings, configuration_revision=REVISION)
    settings["AZURE_AI_REASONING_DEPLOYMENT"] = "mutated"
    selected = captured.resolve("reasoning")
    assert (selected.endpoint, selected.deployment_name, selected.model_id, selected.model_version) == (
        ENDPOINT,
        "name-not-model",
        "model",
        "opaque",
    )
    assert selected.metadata_source is routing.MetadataSource.CONFIGURED
    for setting in ("AZURE_AI_PROJECT_ENDPOINT", "AZURE_AI_PROJECT_REGION"):
        with pytest.raises(FoundryConfigurationError, match=setting):
            resolver(**{setting: " ", "AZURE_AI_REASONING_DEPLOYMENT": "a"}).resolve("reasoning")
    for metadata in (
        {"MODEL_ID": "model"},
        {"MODEL_VERSION": "opaque"},
        {"MODEL_ID": ""},
        {"MODEL_ID": "model", "MODEL_VERSION": "opaque", "MODEL_KEY": "other@version"},
    ):
        with pytest.raises(FoundryConfigurationError, match="AZURE_AI_REASONING_MODEL"):
            resolver(**{f"AZURE_AI_REASONING_{key}": value for key, value in metadata.items()}).resolve("reasoning")
    with pytest.raises(FoundryConfigurationError, match="AZURE_AI_REASONING_DEPLOYMENT"):
        resolver(AZURE_AI_REASONING_DEPLOYMENT=" ", AZURE_AI_PROJECT_DEPLOYMENTS="reasoning=alias").resolve("reasoning")
    with pytest.raises(FoundryConfigurationError, match="embedding"):
        captured.resolve("embedding")


def test_simulation_requires_explicit_and_compares_effective_live_routes() -> None:
    for value in (None, "", " "):
        settings = {"AZURE_AI_PROJECT_DEPLOYMENTS": "simulation=alias"}
        if value is not None:
            settings["AZURE_AI_SIMULATION_DEPLOYMENT"] = value
        with pytest.raises(FoundryConfigurationError, match="AZURE_AI_SIMULATION_DEPLOYMENT"):
            resolver(**settings).resolve("simulation")
    for live in ("reasoning", "drafting"):
        other = "drafting" if live == "reasoning" else "reasoning"
        for mode in ("explicit", "alias", "exact", "base"):
            settings = {"AZURE_AI_SIMULATION_DEPLOYMENT": "s", f"AZURE_AI_{other.upper()}_DEPLOYMENT": "other"}
            if mode == "explicit":
                settings[f"AZURE_AI_{live.upper()}_DEPLOYMENT"] = "s"
            elif mode == "alias":
                settings["AZURE_AI_PROJECT_DEPLOYMENTS"] = f"{live}=s"
            else:
                key = "model@opaque" if mode == "exact" else "model"
                settings[f"AZURE_AI_{live.upper()}_MODEL_KEY"] = key
                settings["AZURE_AI_PROJECT_DEPLOYMENTS"] = f"{key}=s"
            with pytest.raises(FoundryConfigurationError, match=f"simulation.*{live}"):
                resolver(**settings).resolve("simulation")
    captured = resolver(AZURE_AI_SIMULATION_DEPLOYMENT="s", AZURE_AI_REASONING_DEPLOYMENT="r")
    assert captured.resolve("reasoning").deployment_name == "r"
    with pytest.raises(FoundryConfigurationError, match="drafting"):
        captured.resolve("simulation")
    assert (
        resolver(AZURE_AI_SIMULATION_DEPLOYMENT="s", AZURE_AI_PROJECT_DEPLOYMENTS="reasoning=r,drafting=d")
        .resolve("simulation")
        .deployment_name
        == "s"
    )
    invalid_simulation = resolver(AZURE_AI_REASONING_DEPLOYMENT="r", AZURE_AI_SIMULATION_DEPLOYMENT="")
    assert invalid_simulation.resolve("reasoning").deployment_name == "r"
    with pytest.raises(FoundryConfigurationError, match="AZURE_AI_SIMULATION_DEPLOYMENT"):
        routing.DeploymentResolver(invalid_simulation.configuration).resolve("simulation")
    invalid_live = resolver(
        AZURE_AI_REASONING_DEPLOYMENT="r",
        AZURE_AI_DRAFTING_DEPLOYMENT="d",
        AZURE_AI_DRAFTING_MODEL_ID="partial",
        AZURE_AI_SIMULATION_DEPLOYMENT="s",
    )
    assert invalid_live.resolve("reasoning").deployment_name == "r"
    with pytest.raises(FoundryConfigurationError, match="simulation.*drafting.*MODEL_VERSION"):
        invalid_live.resolve("simulation")


def test_legacy_embedding_and_bound_proof_do_not_infer_a_chat_tier_or_account() -> None:
    captured = resolver(
        AZURE_AI_REASONING_DEPLOYMENT="a",
        AZURE_AI_PROJECT_DEPLOYMENTS="text-embedding-3-large@1=e,model=base,model@opaque=exact",
    )
    assert captured.resolve_legacy("model@opaque").deployment_name == "exact"
    assert captured.resolve_legacy("model@other").model_version is None
    embedding = captured.resolve_legacy("text-embedding-3-large@1")
    assert embedding.tier is None
    assert embedding.deployment_name == "e"
    with pytest.raises(FoundryConfigurationError, match="missing"):
        captured.resolve_legacy("missing@opaque")
    for endpoint, revision, destination in (
        (ENDPOINT, REVISION, "a"),
        ("https://other.invalid", REVISION, "a"),
        (ENDPOINT, "other-revision", "a"),
        (ENDPOINT, REVISION, "other-destination"),
    ):
        proof = routing.LegacyMetadataAssociation(
            endpoint=endpoint,
            deployment_name=destination,
            configuration_revision=revision,
            model_id="model",
            model_version="opaque",
            reference="synthetic-bound-proof",
        )
        result = captured.resolve("reasoning", metadata_association=proof)
        assert result.deployment_name == "a"
        assert (result.model_id == "model") is ((endpoint, revision, destination) == (ENDPOINT, REVISION, "a"))

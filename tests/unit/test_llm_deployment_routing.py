"""Tests-first resolver tables; passing foundation checks are not feature acceptance."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from common.foundry_chat_client import FoundryConfigurationError, LiveFoundryChatClient
from common.llm_config import (
    LegacyMetadataAssociation,
    MetadataSource,
    OperationalTier,
    ResolutionSource,
    ResolvedDeployment,
)

from tests.fixtures.llm_deployment_routing import (
    ALIAS_CSV_ORDERINGS,
    CONFLICTING_CSV_ORDERINGS,
    MODEL_ID,
    MODEL_KEY,
    MODEL_VERSION,
    TIER_DEPLOYMENTS,
    RequestSubmissionSpy,
)
from tests.fixtures.llm_deployment_routing import (
    hermetic_routing_environment as hermetic_routing_environment,
)

ENDPOINT = "https://synthetic.services.ai.azure.com"
MESSAGES = [{"role": "user", "content": "synthetic routing probe"}]


@pytest.fixture
def resolver_probe(hermetic_routing_environment):
    patch = hermetic_routing_environment
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", ENDPOINT)
    patch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
    spy = RequestSubmissionSpy()

    def sdk_factory(**kwargs):
        def complete(**request):
            spy.submit(call_id="resolver-probe", deployment_name=request["model"])
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="ok"), finish_reason="stop")],
                usage=SimpleNamespace(prompt_tokens=3, completion_tokens=1),
            )

        return SimpleNamespace(complete=complete)

    patch.setattr("azure.ai.inference.ChatCompletionsClient", sdk_factory)

    def build(settings=None, **kwargs):
        for name, value in (settings or {}).items():
            if value is None:
                patch.delenv(name, raising=False)
            else:
                patch.setenv(name, value)
        return LiveFoundryChatClient(credential=object(), **kwargs)

    return patch, spy, build


@pytest.mark.parametrize("raw", ALIAS_CSV_ORDERINGS)
@pytest.mark.parametrize("tier", [tier for tier, _ in TIER_DEPLOYMENTS])
def test_explicit_tiers_win_over_every_valid_alias_order(raw, tier, resolver_probe):
    _, spy, build = resolver_probe
    settings = {"AZURE_AI_PROJECT_DEPLOYMENTS": raw}
    settings.update({f"AZURE_AI_{tier.upper()}_DEPLOYMENT": f"explicit-{tier}" for tier, _ in TIER_DEPLOYMENTS})
    client = build(settings)
    assert client._resolve(tier) == f"explicit-{tier}"
    assert spy.submissions == []


@pytest.mark.parametrize("raw", CONFLICTING_CSV_ORDERINGS)
def test_conflicting_raw_map_rejected_before_any_request(raw, resolver_probe):
    _, spy, build = resolver_probe
    try:
        with pytest.raises(FoundryConfigurationError) as error:
            client = build({"AZURE_AI_PROJECT_DEPLOYMENTS": raw, "AZURE_AI_REASONING_DEPLOYMENT": "explicit-a"})
            client.chat_complete(model_key="reasoning", messages=MESSAGES)
        assert MODEL_KEY in str(error.value)
        for destination in ("synthetic-live-r", "synthetic-live-d", "synthetic-exercise-s"):
            if destination in raw.split(",")[0] or destination in raw.split(",")[1]:
                assert destination in str(error.value)
    finally:
        assert spy.submissions == []


@pytest.mark.parametrize("value", [None, "", " "], ids=["absent", "empty", "whitespace"])
def test_absent_explicit_allows_alias_but_empty_is_invalid(value, resolver_probe):
    _, spy, build = resolver_probe
    settings = {
        "AZURE_AI_PROJECT_DEPLOYMENTS": "reasoning=alias-r",
        "AZURE_AI_REASONING_DEPLOYMENT": value,
    }
    if value is None:
        assert build(settings)._resolve("reasoning") == "alias-r"
    else:
        try:
            with pytest.raises(FoundryConfigurationError, match="AZURE_AI_REASONING_DEPLOYMENT"):
                build(settings).chat_complete(model_key="reasoning", messages=MESSAGES)
        finally:
            assert spy.submissions == []


@pytest.mark.parametrize(
    "metadata,diagnostic",
    [
        ({"MODEL_ID": MODEL_ID}, "MODEL_VERSION"),
        ({"MODEL_VERSION": MODEL_VERSION}, "MODEL_ID"),
        ({"MODEL_ID": MODEL_ID, "MODEL_VERSION": ""}, "MODEL_VERSION"),
        ({"MODEL_ID": MODEL_ID, "MODEL_VERSION": MODEL_VERSION, "MODEL_KEY": "other@version"}, "MODEL_KEY"),
    ],
)
def test_invalid_identity_fails_before_transport(metadata, diagnostic, resolver_probe):
    _, spy, build = resolver_probe
    settings = {"AZURE_AI_REASONING_DEPLOYMENT": "explicit-a"}
    settings.update({f"AZURE_AI_REASONING_{key}": value for key, value in metadata.items()})
    try:
        with pytest.raises(FoundryConfigurationError, match=diagnostic):
            build(settings).chat_complete(model_key="reasoning", messages=MESSAGES)
    finally:
        assert spy.submissions == []


@pytest.mark.parametrize("setting", ["AZURE_AI_PROJECT_ENDPOINT", "AZURE_AI_PROJECT_REGION"])
def test_missing_required_connection_setting_fails_before_transport(setting, resolver_probe):
    _, spy, build = resolver_probe
    try:
        with pytest.raises(FoundryConfigurationError, match=setting):
            build({setting: None, "AZURE_AI_REASONING_DEPLOYMENT": "explicit-a"}).chat_complete(
                model_key="reasoning", messages=MESSAGES
            )
    finally:
        assert spy.submissions == []


def test_unsupported_chat_tier_does_not_become_an_arbitrary_map_alias(resolver_probe):
    _, spy, build = resolver_probe
    with pytest.raises(ValueError):
        OperationalTier("not-a-tier")
    try:
        with pytest.raises(FoundryConfigurationError, match="not-a-tier"):
            build(deployments={}).chat_complete(model_key="not-a-tier", messages=MESSAGES)
    finally:
        assert spy.submissions == []


@pytest.mark.parametrize("tier", ["reasoning", "drafting"])
@pytest.mark.parametrize("mode", ["alias", "exact", "base"])
def test_live_tier_alias_exact_base_precedence(tier, mode, resolver_probe):
    _, _, build = resolver_probe
    entries = {MODEL_ID: "base-target"}
    if mode != "base":
        entries[MODEL_KEY] = "exact-target"
    if mode == "alias":
        entries[tier] = "alias-target"
    client = build(
        {
            "AZURE_AI_PROJECT_DEPLOYMENTS": ",".join(f"{key}={value}" for key, value in entries.items()),
            f"AZURE_AI_{tier.upper()}_MODEL_KEY": MODEL_KEY if mode != "base" else MODEL_ID,
        }
    )
    assert client._resolve(tier) == f"{mode}-target"


def test_client_snapshot_ignores_subsequent_environment_changes(resolver_probe):
    patch, _, build = resolver_probe
    client = build({"AZURE_AI_REASONING_DEPLOYMENT": "original-a"})
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "mutated-b")
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "reasoning=mutated-c")
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://different-account.invalid")
    assert client._resolve("reasoning") == "original-a"
    assert client._endpoint_for("original-a") == ENDPOINT


@pytest.mark.parametrize("association", ["different-b", "matching-a", "absent"])
def test_explicit_destination_precedes_legacy_metadata_association(association, resolver_probe):
    _, spy, build = resolver_probe
    mapped = "explicit-a" if association == "matching-a" else "legacy-b"
    raw = "" if association == "absent" else f"{MODEL_KEY}={mapped}"
    client = build(
        {
            "AZURE_AI_REASONING_DEPLOYMENT": "explicit-a",
            "AZURE_AI_REASONING_MODEL_KEY": MODEL_KEY,
            "AZURE_AI_PROJECT_DEPLOYMENTS": raw,
        }
    )
    response = client.chat_complete(model_key="reasoning", messages=MESSAGES)
    assert spy.submissions == [("resolver-probe", "explicit-a")]
    assert response.attempt_evidence is not None, "Resolved destination/identity must be available to the adapter"
    identity = response.attempt_evidence.resolved_identity
    assert identity is not None
    assert identity.deployment_name == "explicit-a"
    if association == "matching-a":
        assert (identity.model_id, identity.model_version) == (MODEL_ID, MODEL_VERSION)
        assert identity.metadata_source is MetadataSource.LEGACY_COORDINATE
        assert identity.metadata_association_reference
    else:
        assert identity.metadata_source is MetadataSource.UNAVAILABLE
        assert identity.model_id is identity.model_version is None


def test_wrong_account_proof_cannot_supply_explicit_destination_identity():
    resolved = ResolvedDeployment(
        tier=OperationalTier.REASONING,
        endpoint=ENDPOINT,
        deployment_name="explicit-a",
        resolution_source=ResolutionSource.EXPLICIT_TIER,
        configuration_revision="synthetic-config",
    )
    proof = LegacyMetadataAssociation(
        endpoint="https://wrong-account.services.ai.azure.com",
        deployment_name="explicit-a",
        configuration_revision="synthetic-config",
        model_id=MODEL_ID,
        model_version=MODEL_VERSION,
        reference="wrong-account-proof",
    )
    admitted = resolved.with_legacy_metadata(proof)
    assert admitted.deployment_name == "explicit-a"
    assert admitted.metadata_source is MetadataSource.UNAVAILABLE
    assert admitted.metadata_association_reference is None


@pytest.mark.parametrize("mode", ["explicit", "alias", "exact", "base"])
@pytest.mark.parametrize("mixed", [False, True], ids=["same-live-mode", "mixed-live"])
@pytest.mark.parametrize("collision", [False, True], ids=["distinct", "collision"])
@pytest.mark.parametrize("compared_tier", ["reasoning", "drafting"])
def test_simulation_isolation_compares_effective_live_destinations(
    mode, mixed, collision, compared_tier, resolver_probe
):
    _, spy, build = resolver_probe
    settings = {"AZURE_AI_SIMULATION_DEPLOYMENT": "simulation-s"}
    entries = {}
    for tier, distinct_target in [("reasoning", "live-r"), ("drafting", "live-d")]:
        target = "simulation-s" if collision and tier == compared_tier else distinct_target
        effective_mode = "explicit" if mixed and tier == "drafting" else mode
        if effective_mode == "explicit":
            settings[f"AZURE_AI_{tier.upper()}_DEPLOYMENT"] = target
        elif effective_mode == "alias":
            entries[tier] = target
        else:
            key = f"synthetic-{tier}" + ("@opaque" if effective_mode == "exact" else "")
            settings[f"AZURE_AI_{tier.upper()}_MODEL_KEY"] = key
            entries[key] = target
    settings["AZURE_AI_PROJECT_DEPLOYMENTS"] = ",".join(f"{key}={value}" for key, value in entries.items())
    if collision:
        try:
            with pytest.raises(FoundryConfigurationError, match="simulation"):
                build(settings).chat_complete(model_key="simulation", messages=MESSAGES)
        finally:
            assert spy.submissions == []
    else:
        response = build(settings).chat_complete(model_key="simulation", messages=MESSAGES)
        assert response.deployment_id == "simulation-s"
        assert spy.submissions == [("resolver-probe", "simulation-s")]


@pytest.mark.parametrize("explicit", [None, "", " "])
def test_simulation_cannot_fall_back_to_alias_or_model_key(explicit, resolver_probe):
    _, spy, build = resolver_probe
    try:
        with pytest.raises(FoundryConfigurationError, match="AZURE_AI_SIMULATION_DEPLOYMENT"):
            build(
                {
                    "AZURE_AI_SIMULATION_DEPLOYMENT": explicit,
                    "AZURE_AI_SIMULATION_MODEL_KEY": MODEL_KEY,
                    "AZURE_AI_PROJECT_DEPLOYMENTS": f"simulation=alias-s,{MODEL_KEY}=legacy-s",
                }
            ).chat_complete(model_key="simulation", messages=MESSAGES)
    finally:
        assert spy.submissions == []


def test_unresolved_required_live_comparison_fails_only_simulation(resolver_probe):
    _, spy, build = resolver_probe
    client = build({"AZURE_AI_SIMULATION_DEPLOYMENT": "simulation-s", "AZURE_AI_REASONING_DEPLOYMENT": "live-r"})
    assert client.chat_complete(model_key="reasoning", messages=MESSAGES).deployment_id == "live-r"
    spy.submissions.clear()
    try:
        with pytest.raises(FoundryConfigurationError, match="drafting"):
            client.chat_complete(model_key="simulation", messages=MESSAGES)
    finally:
        assert spy.submissions == []

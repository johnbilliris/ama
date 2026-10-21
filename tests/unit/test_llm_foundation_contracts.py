"""Small foundation checks, not the future resolver/client acceptance matrix."""

from __future__ import annotations

import json
import os
import socket
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from common.foundry_chat_client import InferenceAttemptEvidence
from common.llm_config import (
    DeploymentIdentity,
    LegacyMetadataAssociation,
    LLMClientConfig,
    MetadataSource,
    ModelIdentity,
    OperationalTier,
    ResolutionSource,
    ResolvedDeployment,
    RoutingConfiguration,
)

from tests.fixtures.llm_deployment_routing import (
    ALIAS_CSV_ORDERINGS,
    CONFLICTING_CSV_ORDERINGS,
    MODEL_ID,
    MODEL_KEY,
    MODEL_VERSION,
    SETTING_CASES,
    RequestSubmissionSpy,
    routing_environment,
)
from tests.fixtures.llm_deployment_routing import (
    hermetic_routing_environment as hermetic_routing_environment,
)


def test_snapshot_retains_presence_raw_csv_and_opaque_identity(hermetic_routing_environment):
    patch = hermetic_routing_environment
    for name, value in SETTING_CASES["complete"].items():
        patch.setenv(name, value)
    patch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://synthetic.invalid")
    patch.setenv("AZURE_AI_PROJECT_REGION", "synthetic-region")
    patch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", CONFLICTING_CSV_ORDERINGS[0])
    snapshot = RoutingConfiguration.from_environment(configuration_revision="synthetic-config-1")
    patch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "mutated")
    tier = snapshot.tier_configuration(OperationalTier.REASONING)
    assert tier.deployment_name == "synthetic-live-r"
    assert tier.model == ModelIdentity(MODEL_ID, MODEL_VERSION)
    assert tier.model.model_key == MODEL_KEY
    assert tier.metadata_source is MetadataSource.CONFIGURED
    assert snapshot.raw_deployments == CONFLICTING_CSV_ORDERINGS[0]
    assert snapshot.endpoint == "https://synthetic.invalid"
    assert snapshot.region == "synthetic-region"
    assert snapshot.tier_configuration(OperationalTier.DRAFTING).deployment_name is None
    with pytest.raises(FrozenInstanceError):
        snapshot.region = "mutated"
    with pytest.raises(ValueError):
        OperationalTier("embedding")


@pytest.mark.parametrize("case", ["partial_id", "partial_version", "blank_version", "blank"])
def test_new_snapshot_rejects_partial_or_empty_settings(case):
    settings = {key: value for key, value in SETTING_CASES[case].items() if value is not None}
    with pytest.raises(ValueError, match="AZURE_AI_REASONING"):
        RoutingConfiguration.from_environment(settings, configuration_revision="synthetic-config")


def test_snapshot_absent_identity_and_coordinate_consistency():
    snapshot = RoutingConfiguration.from_environment({}, configuration_revision="synthetic-config")
    tier = snapshot.tier_configuration(OperationalTier.REASONING)
    assert tier.model is None
    assert tier.metadata_source is MetadataSource.UNAVAILABLE
    assert snapshot.endpoint is None
    assert snapshot.raw_deployments is None
    blank = RoutingConfiguration.from_environment(
        {"AZURE_AI_PROJECT_DEPLOYMENTS": ""}, configuration_revision="synthetic-config"
    )
    assert blank.raw_deployments == ""
    settings = dict(SETTING_CASES["complete"])
    settings["AZURE_AI_REASONING_MODEL_KEY"] = "different@coordinate"
    with pytest.raises(ValueError, match="MODEL_KEY"):
        RoutingConfiguration.from_environment(settings, configuration_revision="synthetic-config")
    with pytest.raises(ValueError, match="model_version"):
        ModelIdentity(MODEL_ID, " ")


def test_legacy_association_is_destination_account_and_revision_bound():
    resolved = ResolvedDeployment(
        tier=OperationalTier.REASONING,
        endpoint="https://account-a.invalid",
        deployment_name="explicit-a",
        resolution_source=ResolutionSource.EXPLICIT_TIER,
        configuration_revision="config-a",
    )
    for endpoint, destination, revision in [
        ("https://account-a.invalid", "coordinate-b", "config-a"),
        ("https://account-b.invalid", "explicit-a", "config-a"),
        ("https://account-a.invalid", "explicit-a", "config-b"),
    ]:
        proof = LegacyMetadataAssociation(
            endpoint=endpoint,
            deployment_name=destination,
            configuration_revision=revision,
            model_id=MODEL_ID,
            model_version=MODEL_VERSION,
            reference="synthetic-validated-map",
        )
        assert resolved.with_legacy_metadata(proof) is resolved
    matched = resolved.with_legacy_metadata(
        LegacyMetadataAssociation(
            endpoint=resolved.endpoint,
            deployment_name=resolved.deployment_name,
            configuration_revision=resolved.configuration_revision,
            model_id=MODEL_ID,
            model_version=MODEL_VERSION,
            reference="synthetic-validated-map",
        )
    )
    assert matched.deployment_name == "explicit-a"
    assert matched.model_id == MODEL_ID
    assert matched.model_version == MODEL_VERSION
    assert matched.metadata_source is MetadataSource.LEGACY_COORDINATE
    assert matched.metadata_association_reference == "synthetic-validated-map"
    assert resolved.model_id is None
    bare = resolved.with_legacy_metadata(
        LegacyMetadataAssociation(
            endpoint=resolved.endpoint,
            deployment_name=resolved.deployment_name,
            configuration_revision=resolved.configuration_revision,
            model_id=MODEL_ID,
            reference="synthetic-validated-base-map",
        )
    )
    assert bare.model_id == MODEL_ID
    assert bare.model_version is None


def test_baseline_identity_and_legacy_activation_boundary(hermetic_routing_environment):
    hermetic_routing_environment.setenv("AZURE_AI_REASONING_MODEL_ID", MODEL_ID)
    legacy = LLMClientConfig(foundry_deployments=CONFLICTING_CSV_ORDERINGS[0])
    assert legacy.foundry_deployments == CONFLICTING_CSV_ORDERINGS[0]
    baseline = DeploymentIdentity(
        account_resource_id="synthetic-account",
        deployment_name="synthetic-name-not-model",
        model=ModelIdentity(MODEL_ID, MODEL_VERSION),
        region="synthetic-region",
        sku="synthetic-sku",
        capacity=1,
        rai_policy_name="synthetic-policy",
        access_controls="synthetic-evidence",
        version_upgrade_option=None,
    )
    assert baseline.deployment_name != baseline.model.model_id
    with pytest.raises(FrozenInstanceError):
        baseline.deployment_name = "mutated"
    with pytest.raises(ValueError, match="capacity"):
        DeploymentIdentity(
            account_resource_id=baseline.account_resource_id,
            deployment_name=baseline.deployment_name,
            model=baseline.model,
            region=baseline.region,
            sku=baseline.sku,
            capacity=0,
            rai_policy_name=baseline.rai_policy_name,
            access_controls=baseline.access_controls,
            version_upgrade_option=baseline.version_upgrade_option,
        )


def test_evidence_is_request_local_and_defaults_to_unknown():
    spy = RequestSubmissionSpy()
    spy.enter_method("call-1")
    first = InferenceAttemptEvidence(call_id="call-1", correlation_id="turn-1")
    assert first.inference_attempted is None
    assert first.inference_outcome == "unknown"
    assert first.usage_prompt_tokens is None
    assert first.output_text_hash is None
    assert spy.submissions == []
    spy.submit(call_id="call-2", deployment_name="synthetic-exercise-s")
    second = InferenceAttemptEvidence(
        call_id="call-2", correlation_id="turn-1", inference_attempted=True, inference_outcome="unknown"
    )
    assert first.call_id != second.call_id
    assert first.inference_attempted is None
    assert second.inference_outcome != "succeeded"
    with pytest.raises(FrozenInstanceError):
        first.inference_attempted = True


def test_evidence_rejects_unproved_success_and_retains_actual_usage():
    with pytest.raises(ValueError, match="submission evidence"):
        InferenceAttemptEvidence(call_id="call-1", correlation_id="turn-1", inference_outcome="succeeded")
    failed = InferenceAttemptEvidence(
        call_id="call-2",
        correlation_id="turn-1",
        inference_attempted=True,
        inference_outcome="failed",
        error_code="foundry_transport_error",
        usage_prompt_tokens=7,
        usage_completion_tokens=2,
        output_text_hash="a" * 64,
    )
    assert failed.usage_prompt_tokens == 7
    assert failed.usage_completion_tokens == 2
    assert failed.output_text_hash == "a" * 64
    assert failed.error_code == "foundry_transport_error"
    no_call = InferenceAttemptEvidence(
        call_id="call-3", correlation_id="turn-1", inference_attempted=False, inference_outcome="not_attempted"
    )
    assert no_call.resolved_identity is None
    assert no_call.usage_prompt_tokens is None


def test_hermetic_context_restores_environment_and_network(monkeypatch):
    monkeypatch.setenv("AZURE_AI_ROUTING_TEST_SENTINEL", "inherited-synthetic")
    connect = socket.socket.connect
    getaddrinfo = socket.getaddrinfo
    with routing_environment():
        assert "AZURE_AI_ROUTING_TEST_SENTINEL" not in os.environ
        assert socket.socket.connect is not connect
    assert os.environ["AZURE_AI_ROUTING_TEST_SENTINEL"] == "inherited-synthetic"
    assert socket.socket.connect is connect
    assert socket.getaddrinfo is getaddrinfo


def test_fixture_scope_and_synthetic_payloads(hermetic_routing_environment):
    assert not any(name.startswith(("AZURE_AI_", "AZURE_OPENAI_")) for name in os.environ)
    with pytest.raises(AssertionError, match="network"):
        socket.create_connection(("synthetic.invalid", 443))
    assert len(set(ALIAS_CSV_ORDERINGS)) == len(set(CONFLICTING_CSV_ORDERINGS)) == 6
    path = Path(__file__).parents[1] / "fixtures" / "llm_deployment_provenance.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    assert "inference_attempted" not in payloads["old_dispatcher"]
    assert payloads["new_dispatcher"]["inference_attempted"] is True
    assert payloads["new_unknown"]["inference_attempted"] is None

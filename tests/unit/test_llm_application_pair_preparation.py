from __future__ import annotations

import copy
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2] / "scripts" / "prepare-llm-application-pair.py"
SPEC = importlib.util.spec_from_file_location("pair_preparation_tests", PATH)
assert SPEC is not None and SPEC.loader is not None
pair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pair)
SERVER = "crdevw3uq6w.azurecr.io"
IMAGE = f"{SERVER}/ama/api@sha256:{'a' * 64}"


@pytest.fixture
def application() -> dict:
    return {
        "id": pair.APP_IDS["api"],
        "location": "australiaeast",
        "tags": {"preserved": "yes"},
        "identity": {"type": "SystemAssigned", "principalId": "synthetic-existing-identity"},
        "properties": {
            "latestRevisionName": "ca-api-dev--old",
            "managedEnvironmentId": "synthetic-existing-environment",
            "configuration": {
                "activeRevisionsMode": "Single",
                "secrets": [{"name": "existing-secret"}],
                "registries": [{"server": SERVER, "identity": "system"}],
                "ingress": {
                    "external": True,
                    "targetPort": 8000,
                    "traffic": [{"latestRevision": True, "weight": 100}],
                },
                "dapr": {"enabled": False},
            },
            "template": {
                "revisionSuffix": "old",
                "containers": [
                    {
                        "name": "api",
                        "image": "existing-image",
                        "env": [
                            {"name": "PRIVATE_VALUE", "value": "PRIVATE_MARKER"},
                            {"name": "EXISTING_SECRET", "secretRef": "existing-secret"},
                        ],
                        "resources": {"cpu": 0.5, "memory": "1Gi", "ephemeralStorage": "2Gi"},
                    }
                ],
                "scale": {"minReplicas": 1, "maxReplicas": 3},
                "volumes": [],
                "initContainers": [],
                "terminationGracePeriodSeconds": 30,
            },
        },
    }


@pytest.fixture
def routing() -> dict[str, str]:
    return {name: "synthetic-coordinate" for name in pair.ROUTING_NAMES}


def test_pair_patch_preserves_unknown_secrets_and_complete_unchanged_configuration(application: dict, routing: dict):
    original = copy.deepcopy(application)
    patch = pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    evidence = pair.proposal_evidence(application, patch, "api")
    after = pair.merge_patch(application, patch)
    assert application == original
    assert "secrets" not in patch["properties"]["configuration"]
    assert after["properties"]["configuration"]["secrets"] == original["properties"]["configuration"]["secrets"]
    assert after["properties"]["configuration"]["registries"] == original["properties"]["configuration"]["registries"]
    assert after["properties"]["template"]["scale"] == original["properties"]["template"]["scale"]
    env = pair.named(after["properties"]["template"]["containers"][0]["env"], "env")
    assert env["EXISTING_SECRET"] == {"name": "EXISTING_SECRET", "secretRef": "existing-secret"}
    assert env["PRIVATE_VALUE"]["value"] == "PRIVATE_MARKER"
    assert "PRIVATE_MARKER" not in json.dumps(evidence)
    assert evidence["execution_authorised"] is False
    assert evidence["arm_what_if_equivalence_claimed"] is False
    assert after["properties"]["configuration"]["ingress"]["traffic"] == [
        {"revisionName": "ca-api-dev--old", "weight": 100}
    ]


def test_unheld_api_requires_and_preserves_exact_same_environment_revision_binding(application: dict, routing: dict):
    application["properties"]["latestRevisionFqdn"] = "ca-api-dev--old.synthetic.australiaeast.azurecontainerapps.io"
    url = "https://ca-agents-dev--validation-041.internal.synthetic.australiaeast.azurecontainerapps.io"
    patch = pair.prepare_patch(
        application,
        "api",
        IMAGE,
        routing,
        "validation-041",
        SERVER,
        bootstrap_hold=False,
        agents_revision_url=url,
    )
    evidence = pair.proposal_evidence(
        application,
        patch,
        "api",
        bootstrap_hold=False,
        agents_revision_url=url,
    )
    env = pair.named(patch["properties"]["template"]["containers"][0]["env"], "env")
    assert env["AMA_BOOTSTRAP_HOLD"]["value"] == "false"
    assert env["AGENTS_BASE_URL"]["value"] == url
    assert env["EXISTING_SECRET"]["secretRef"] == "existing-secret"
    assert evidence["business_hold"] is False
    assert evidence["agents_revision_url"] == url
    with pytest.raises(pair.preflight.EvidenceError, match="patch.hold|preserved.env"):
        pair.proposal_evidence(application, patch, "api")
    env["AGENTS_BASE_URL"]["value"] = url.replace("validation-041", "different")
    with pytest.raises(pair.preflight.EvidenceError, match="patch.binding"):
        pair.proposal_evidence(application, patch, "api", bootstrap_hold=False, agents_revision_url=url)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "https://ca-agents-dev.internal.synthetic.australiaeast.azurecontainerapps.io",
        "https://ca-agents-dev--validation-041.internal.other.australiaeast.azurecontainerapps.io",
    ],
)
def test_unheld_api_rejects_shared_missing_or_cross_environment_binding(application: dict, routing: dict, url):
    application["properties"]["latestRevisionFqdn"] = "ca-api-dev--old.synthetic.australiaeast.azurecontainerapps.io"
    with pytest.raises(pair.preflight.EvidenceError, match="pair_binding"):
        pair.prepare_patch(
            application,
            "api",
            IMAGE,
            routing,
            "validation-041",
            SERVER,
            bootstrap_hold=False,
            agents_revision_url=url,
        )


@pytest.mark.parametrize("field", ["secrets", "registries", "dapr"])
def test_unapproved_configuration_delta_is_rejected(application: dict, routing: dict, field: str):
    patch = pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    patch["properties"]["configuration"][field] = []
    with pytest.raises(pair.preflight.EvidenceError):
        pair.proposal_evidence(application, patch, "api")


@pytest.mark.parametrize("field", ["managedEnvironmentId", "workloadProfileName"])
def test_unapproved_resource_delta_is_rejected(application: dict, routing: dict, field: str):
    patch = pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    patch["properties"][field] = "unapproved"
    with pytest.raises(pair.preflight.EvidenceError):
        pair.proposal_evidence(application, patch, "api")


def test_preserved_container_resource_and_secret_reference_cannot_drift(application: dict, routing: dict):
    patch = pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    patch["properties"]["template"]["containers"][0]["resources"]["cpu"] = 1
    with pytest.raises(pair.preflight.EvidenceError):
        pair.proposal_evidence(application, patch, "api")


@pytest.mark.parametrize(
    "fault", ["duplicate-env", "secret-routing", "wrong-target", "wrong-image", "missing-registry"]
)
def test_pair_preparation_rejects_unsafe_or_ambiguous_inputs(application: dict, routing: dict, fault: str):
    container = application["properties"]["template"]["containers"][0]
    image = IMAGE
    if fault == "duplicate-env":
        container["env"].append({"name": "EXISTING_SECRET", "value": "different"})
    elif fault == "secret-routing":
        container["env"].append({"name": "AZURE_AI_REASONING_DEPLOYMENT", "secretRef": "existing-secret"})
    elif fault == "wrong-target":
        application["id"] = application["id"].replace("ca-api-dev", "ca-api-production")
    elif fault == "wrong-image":
        image = f"{SERVER}/ama/api:mutable"
    else:
        application["properties"]["configuration"]["registries"] = []
    with pytest.raises(pair.preflight.EvidenceError):
        pair.prepare_patch(application, "api", image, routing, "bootstrap-041", SERVER)


def test_application_inspection_cannot_run_with_expired_or_wrong_scope_authority(monkeypatch):
    authority = {
        "subscription": pair.SUBSCRIPTION,
        "resource_group": "ama",
        "account": "cog-dev-w3uq6w",
        "region": "australiaeast",
        "window_start": "2000-01-01T00:00:00Z",
        "window_end": "2000-01-02T00:00:00Z",
        "allowed": ["refresh target and protection metadata, effective policy semantics and existing app revisions"],
    }
    called = []
    monkeypatch.setattr(pair.subprocess, "run", lambda *args, **kwargs: called.append(args))
    with pytest.raises(pair.preflight.EvidenceError):
        pair.read_resource(pair.APP_IDS["api"], authority)
    authority["window_start"], authority["window_end"] = "2026-10-20T00:00:00Z", "2026-10-20T04:00:00Z"
    authority["subscription"] = "different"
    with pytest.raises(pair.preflight.EvidenceError):
        pair.validate_authority(authority, datetime(2026, 10, 20, 1, tzinfo=UTC))
    assert called == []


def test_actual_model_identity_and_simulation_isolation_are_materialized_without_foundry_writes():
    from apps.agents.common.llm_config import DeploymentResolver, OperationalTier

    inventory = {
        "target": {"region": "australiaeast"},
        "deployments": {
            "value": [
                {"name": alias, "properties": {"model": {"name": model, "version": version}}}
                for alias, model, version in [
                    ("gpt-5.4-dev", "gpt-5.4", "2026-03-05"),
                    ("gpt-5.4-mini-dev", "gpt-5.4", "2026-03-05"),
                    ("gpt-5.4-sim-dev", "gpt-5.4", "2026-03-05"),
                    ("text-embedding-3-large-dev", "text-embedding-3-large", "1"),
                ]
            ]
        },
    }
    routing = pair.routing_from_inventory(inventory)
    assert routing["AZURE_AI_DRAFTING_MODEL_ID"] == "gpt-5.4"
    assert routing["AZURE_AI_SIMULATION_DEPLOYMENT"] == "gpt-5.4-sim-dev"
    assert "gpt-5.4=" not in routing["AZURE_AI_PROJECT_DEPLOYMENTS"]
    assert "text-embedding-3-large@1=text-embedding-3-large-dev" in routing["AZURE_AI_PROJECT_DEPLOYMENTS"]
    resolver = DeploymentResolver.from_environment(
        {**routing, "AZURE_AI_PROJECT_ENDPOINT": "https://synthetic.cognitiveservices.azure.com"},
        configuration_revision="prepared-routing-test",
    )
    assert [resolver.resolve(tier).deployment_name for tier in OperationalTier] == [
        "gpt-5.4-dev",
        "gpt-5.4-mini-dev",
        "gpt-5.4-sim-dev",
    ]


@pytest.mark.parametrize("region", [None, "", "eastus"])
def test_preparation_rejects_missing_or_unapproved_observed_region(region):
    with pytest.raises(pair.preflight.EvidenceError, match="inventory.target.region"):
        pair.routing_from_inventory({"target": {"region": region}})


def test_approved_registry_addition_preserves_other_entries_without_reading_secrets(application: dict, routing: dict):
    existing = [{"server": "other.registry.example", "username": "preserved", "passwordSecretRef": "existing-secret"}]
    application["properties"]["configuration"]["registries"] = copy.deepcopy(existing)
    patch = pair.prepare_patch(
        application, "api", IMAGE, routing, "bootstrap-041", SERVER, configure_registry_identity=True
    )
    pair.proposal_evidence(application, patch, "api", configure_registry_identity=True)
    assert patch["properties"]["configuration"]["registries"] == [*existing, {"server": SERVER, "identity": "system"}]
    assert application["properties"]["configuration"]["registries"] == existing
    assert "secrets" not in patch["properties"]["configuration"]
    with pytest.raises(pair.preflight.EvidenceError):
        pair.proposal_evidence(application, patch, "api")
    patch["properties"]["configuration"]["registries"] = [{"server": SERVER, "identity": "system"}]
    with pytest.raises(pair.preflight.EvidenceError):
        pair.proposal_evidence(application, patch, "api", configure_registry_identity=True)


@pytest.mark.parametrize("fault", ["missing-identity", "duplicate-registries"])
def test_registry_approval_does_not_authorise_identity_creation_or_credential_replacement(
    application: dict, routing: dict, fault: str
):
    application["properties"]["configuration"]["registries"] = []
    if fault == "missing-identity":
        application["identity"] = {"type": "None"}
    else:
        application["properties"]["configuration"]["registries"] = [
            {"server": SERVER, "username": "preserved", "passwordSecretRef": "existing-secret"},
            {"server": SERVER, "identity": "system"},
        ]
    with pytest.raises(pair.preflight.EvidenceError):
        pair.prepare_patch(
            application, "api", IMAGE, routing, "bootstrap-041", SERVER, configure_registry_identity=True
        )


def test_approved_system_pull_rebinds_registry_auth_without_replacing_secret_definitions(
    application: dict, routing: dict
):
    application["properties"]["configuration"]["registries"] = [
        {"server": SERVER, "identity": "", "username": "legacy-user", "passwordSecretRef": "existing-secret"}
    ]
    original = copy.deepcopy(application)
    with pytest.raises(pair.preflight.EvidenceError):
        pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    patch = pair.prepare_patch(
        application, "api", IMAGE, routing, "bootstrap-041", SERVER, configure_registry_identity=True
    )
    pair.proposal_evidence(application, patch, "api", configure_registry_identity=True)
    assert patch["properties"]["configuration"]["registries"] == [{"server": SERVER, "identity": "system"}]
    assert "secrets" not in patch["properties"]["configuration"]
    after = pair.merge_patch(application, patch)
    assert after["properties"]["configuration"]["secrets"] == original["properties"]["configuration"]["secrets"]
    assert application == original


@pytest.mark.parametrize("location", ["Australia East", "AUSTRALIAEAST"])
def test_azure_region_display_alias_is_preserved_without_changing_location(
    application: dict, routing: dict, location: str
):
    application["location"] = location
    patch = pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    pair.proposal_evidence(application, patch, "api")
    assert patch["location"] == location


@pytest.mark.parametrize("location", ["australiasoutheast", "eastus"])
def test_different_location_is_never_silently_normalized(application: dict, routing: dict, location: str):
    application["location"] = location
    with pytest.raises(pair.preflight.EvidenceError):
        pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)


def test_held_preparation_cannot_start_unreviewed_init_container_activity(application: dict, routing: dict):
    application["properties"]["template"]["initContainers"] = [
        {"name": "unreviewed-startup-writes", "image": "synthetic-image"}
    ]
    with pytest.raises(pair.preflight.EvidenceError, match="initContainers"):
        pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)


def test_provider_probe_order_and_empty_mi_auth_fields_do_not_mask_configuration_preservation(
    application: dict, routing: dict
):
    expected = pair.merge_patch(
        application, pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    )
    response = copy.deepcopy(expected)
    response["properties"]["template"]["containers"][0]["probes"].reverse()
    response["properties"]["template"]["containers"][0]["resources"]["ephemeralStorage"] = "2Gi"
    response["properties"]["configuration"]["registries"][0].update({"username": "", "passwordSecretRef": ""})
    original = copy.deepcopy(response)
    assert pair.normalized_application(response) == pair.normalized_application(expected)
    assert response == original


@pytest.mark.parametrize("fault", ["secret-reference", "secret-definition", "scale"])
def test_response_comparison_still_detects_real_preservation_changes(application: dict, routing: dict, fault: str):
    expected = pair.merge_patch(
        application, pair.prepare_patch(application, "api", IMAGE, routing, "bootstrap-041", SERVER)
    )
    response = copy.deepcopy(expected)
    if fault == "secret-reference":
        response["properties"]["template"]["containers"][0]["env"][1]["secretRef"] = "different-secret"
    elif fault == "secret-definition":
        response["properties"]["configuration"]["secrets"] = []
    else:
        response["properties"]["template"]["scale"]["minReplicas"] = 0
    assert pair.normalized_application(response) != pair.normalized_application(expected)

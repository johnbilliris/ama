"""Contracts for azd container image publication."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
AZURE_YAML_PATH = ROOT / "azure.yaml"
CONTAINER_SERVICES = ("api", "agents", "evacuation", "ingestion", "ingest-runner")
EXPECTED_PLATFORM = "linux/amd64"
EXPECTED_REGISTRY = "${AZURE_CONTAINER_REGISTRY_ENDPOINT}"


def test_local_bake_covers_every_dockerfile_with_arm64_only() -> None:
    config = json.loads((ROOT / "docker-bake.json").read_text(encoding="utf-8"))
    targets = config["target"]
    assert set(config["group"]["default"]["targets"]) == set(targets)
    dockerfiles = {
        *ROOT.glob("apps/*/Dockerfile"),
        ROOT / ".devcontainer" / "Dockerfile",
    }
    assert {ROOT / target["dockerfile"] for target in targets.values()} == dockerfiles
    for target in targets.values():
        assert target["context"] == "."
        assert target["platforms"] == ["linux/arm64"]
        assert target["output"] == ["type=docker"]
        assert all(tag.endswith(":local") for tag in target["tags"])


def test_compose_builds_pin_arm64_independent_of_host_defaults() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    bake = json.loads((ROOT / "docker-bake.json").read_text(encoding="utf-8"))
    for service in compose["services"].values():
        if "build" not in service:
            continue
        assert service["platform"] == "linux/arm64"
        target = next(target for target in bake["target"].values() if service["image"] in target["tags"])
        assert service["build"]["dockerfile"] == target["dockerfile"]
        assert service["build"]["target"] == target["target"]
        assert service["build"].get("args", {}) == target.get("args", {})


def test_devcontainer_and_editor_terminals_use_arm64() -> None:
    config = json.loads((ROOT / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))
    assert "--platform=linux/arm64" in config["build"]["options"]
    assert "--platform=linux/arm64" in config["runArgs"]
    assert config["containerEnv"]["DOCKER_DEFAULT_PLATFORM"] == "linux/arm64"
    settings = json.loads((ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8"))
    for system in ("windows", "linux", "osx"):
        assert settings[f"terminal.integrated.env.{system}"]["DOCKER_DEFAULT_PLATFORM"] == "linux/arm64"


def test_azd_publishes_all_container_services_to_acr() -> None:
    config = yaml.safe_load(AZURE_YAML_PATH.read_text(encoding="utf-8"))
    image_repositories = set()

    for service_name in CONTAINER_SERVICES:
        docker = config["services"][service_name]["docker"]
        assert docker["platform"] == EXPECTED_PLATFORM
        assert docker["registry"] == EXPECTED_REGISTRY
        assert docker["remoteBuild"] is True
        image_repositories.add(docker["image"])

    assert image_repositories == {f"ama/{service_name}" for service_name in CONTAINER_SERVICES}


def test_container_dockerfiles_do_not_pin_a_single_architecture() -> None:
    config = yaml.safe_load(AZURE_YAML_PATH.read_text(encoding="utf-8"))

    for service_name in CONTAINER_SERVICES:
        service = config["services"][service_name]
        dockerfile = ROOT / service["project"] / service["docker"]["path"]
        dockerfile_text = dockerfile.resolve().read_text(encoding="utf-8")
        assert "FROM --platform=" not in dockerfile_text


def test_ingest_runner_job_uses_azd_bootstrap_and_discovery_contract() -> None:
    main_bicep = (ROOT / "infra" / "main.bicep").read_text(encoding="utf-8")

    assert (
        "param ingestRunnerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'" in main_bicep
    )
    assert "tags: union(tags, { 'azd-service-name': 'ingest-runner' })" in main_bicep
    assert "image: ingestRunnerImage" in main_bicep
    assert "spec036IngestRunnerImageTag" not in main_bicep


def test_web_uses_single_azd_build_lifecycle() -> None:
    config = yaml.safe_load(AZURE_YAML_PATH.read_text(encoding="utf-8"))
    package = yaml.safe_load((ROOT / "apps" / "web" / "package.json").read_text(encoding="utf-8"))

    assert "hooks" not in config["services"]["web"]
    assert package["scripts"]["build"] == "next build --webpack"
    assert package["scripts"]["postbuild"] == "node scripts/copy-standalone-assets.mjs"

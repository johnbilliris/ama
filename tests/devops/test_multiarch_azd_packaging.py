"""Contracts for azd container image publication."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
AZURE_YAML_PATH = ROOT / "azure.yaml"
CONTAINER_SERVICES = ("api", "agents", "evacuation", "ingestion", "ingest-runner")
EXPECTED_PLATFORM = "linux/amd64"
EXPECTED_REGISTRY = "${AZURE_CONTAINER_REGISTRY_ENDPOINT}"


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

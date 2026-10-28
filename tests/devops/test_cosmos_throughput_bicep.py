"""Contract for dev Cosmos rightsizing without changing other tiers."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "infra" / "main.bicep"
MODULES = ROOT / "infra" / "bicep" / "modules"


@pytest.mark.parametrize(
    ("parameter", "non_dev_max"),
    [
        ("cosmosSignalsAutoscaleMaxRu", 6000),
        ("cosmosEvacuationAutoscaleMaxRu", 4000),
        ("spec038CosmosAutoscaleMaxRu", 4000),
    ],
)
def test_root_caps_are_tier_aware(parameter: str, non_dev_max: int) -> None:
    main = MAIN.read_text(encoding="utf-8")
    assert (f"@minValue(1000)\nparam {parameter} int = environmentTier == 'dev' ? 1000 : {non_dev_max}") in main


def test_root_wires_caps_and_workflow_tier() -> None:
    main = MAIN.read_text(encoding="utf-8")
    assert "maxThroughput: cosmosSignalsAutoscaleMaxRu" in main
    assert "cosmosAutoscaleMaxRu: cosmosEvacuationAutoscaleMaxRu" in main
    assert "autoscaleMaxRu: spec038CosmosAutoscaleMaxRu" in main
    workflow_call = main.split("module mafWorkflowCosmos ", 1)[1].split("\n}\n", 1)[0]
    assert "environmentTier: environmentTier" in workflow_call


@pytest.mark.parametrize(
    ("module", "container_declarations"),
    [("cosmos-workflow.bicep", 3), ("evidence-harness.bicep", 1)],
)
def test_background_containers_use_autoscale_only_in_dev(module: str, container_declarations: int) -> None:
    text = (MODULES / module).read_text(encoding="utf-8")
    assert "@allowed(['dev', 'staging', 'prod'])" in text or ("@allowed([ 'dev', 'staging', 'prod' ])" in text)
    assert (
        "var cosmosThroughputOptions = environmentTier == 'dev' ? {\n"
        "  autoscaleSettings: { maxThroughput: 1000 }\n"
        "} : {}"
    ) in text
    assert text.count("options: cosmosThroughputOptions") == container_declarations


def test_evacuation_avm_uses_configurable_cap() -> None:
    text = (MODULES / "evacuation-runtime.bicep").read_text(encoding="utf-8")
    assert "@minValue(1000)\nparam cosmosAutoscaleMaxRu int = 4000" in text
    assert "autoscaleSettingsMaxThroughput: cosmosAutoscaleMaxRu" in text

"""Static lifecycle checks for evidence cold-archive immutability."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "infra" / "bicep" / "modules" / "evidence-harness.bicep"
MAIN_PATH = ROOT / "infra" / "main.bicep"
AZURE_YAML_PATH = ROOT / "azure.yaml"
POWERSHELL_HOOK_PATH = ROOT / "scripts" / "remove-evidence-immutability-policy.ps1"
POSIX_HOOK_PATH = ROOT / "scripts" / "remove-evidence-immutability-policy.sh"


def test_policy_is_bicep_owned_and_excluded_from_dev() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    main_text = MAIN_PATH.read_text(encoding="utf-8")

    assert "param environmentTier string" in module_text
    assert "if (environmentTier != 'dev')" in module_text
    assert "immutabilityPeriodSinceCreationInDays: 2555" in module_text
    assert "environmentTier: environmentTier" in main_text
    assert "endsWith(toLower(environmentName), 'staging')" in main_text
    assert "deployColdArchiveImmutabilityPolicy" not in module_text
    assert "deployEvidenceColdArchiveImmutabilityPolicy" not in main_text


def test_environment_parameter_files_select_the_expected_tier() -> None:
    expected_tiers = {
        "main.parameters.dev.json": "dev",
        "main.parameters.staging.json": "staging",
        "main.parameters.production.json": "prod",
    }

    for file_name, expected_tier in expected_tiers.items():
        parameters = json.loads((ROOT / "infra" / file_name).read_text(encoding="utf-8"))
        assert parameters["parameters"]["environmentTier"]["value"] == expected_tier


def test_azd_down_removes_an_unlocked_policy_first() -> None:
    azure_yaml = AZURE_YAML_PATH.read_text(encoding="utf-8")
    powershell_hook = POWERSHELL_HOOK_PATH.read_text(encoding="utf-8")
    posix_hook = POSIX_HOOK_PATH.read_text(encoding="utf-8")

    assert "\n  predown:\n" in azure_yaml
    assert "./scripts/remove-evidence-immutability-policy.ps1" in azure_yaml
    assert "./scripts/remove-evidence-immutability-policy.sh" in azure_yaml

    for hook_text in (powershell_hook, posix_hook):
        assert "immutability-policy show" in hook_text
        assert "immutability-policy delete" in hook_text
        assert "Locked" in hook_text
        assert "--if-match" in hook_text

    assert "No evidence immutability policy exists; teardown can continue." in powershell_hook
    assert "$null -eq $stateProperty" in powershell_hook
    assert "if [ -z \"$policy_state\" ]" in posix_hook
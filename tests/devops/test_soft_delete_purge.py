"""Tests for idempotent dev soft-delete purging."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.purge_soft_deleted_dev_resources import (
    deleted_resource_group,
    environment_tier,
    matching_deleted_accounts,
    matching_deleted_workspaces,
    purge_accounts,
    purge_workspaces,
)


def _deleted_account(
    name: str,
    environment_name: str,
    resource_group: str = "ama",
) -> dict[str, Any]:
    return {
        "id": (
            "/subscriptions/sub/providers/Microsoft.CognitiveServices/locations/"
            f"australiaeast/resourceGroups/{resource_group}/deletedAccounts/{name}"
        ),
        "name": name,
        "location": "australiaeast",
        "tags": {"azd-env-name": environment_name},
    }


def test_environment_tier_matches_bicep_defaulting() -> None:
    assert environment_tier("dev") == "dev"
    assert environment_tier("drh-dev") == "dev"
    assert environment_tier("drh-staging") == "staging"
    assert environment_tier("drh-prod") == "prod"
    assert environment_tier("drh-production") == "prod"


def test_deleted_resource_group_reads_cognitive_services_id() -> None:
    account = _deleted_account("cog-dev-123", "dev")
    assert deleted_resource_group(account["id"]) == "ama"
    assert deleted_resource_group("invalid") is None


def test_matching_deleted_accounts_isolates_environment_and_resource_group() -> None:
    expected = _deleted_account("cog-dev-123", "dev")
    payload = [
        expected,
        _deleted_account("cs-staging-123", "staging"),
        _deleted_account("cog-dev-other", "dev", resource_group="other"),
    ]

    assert matching_deleted_accounts(payload, "dev", "ama") == [expected]


def test_purge_accounts_only_uses_deleted_account_purge_command() -> None:
    commands: list[list[str]] = []

    def record(arguments: list[str]) -> str:
        commands.append(arguments)
        return ""

    purge_accounts([_deleted_account("cog-dev-123", "dev")], "ama", runner=record)

    assert len(commands) == 1
    assert commands[0][3] == "purge"
    assert "delete" not in commands[0]
    assert "cog-dev-123" in commands[0]


def test_log_analytics_purge_only_targets_deleted_inventory() -> None:
    workspace = {
        "name": "log-dev",
        "resourceGroup": "ama",
        "tags": {"azd-env-name": "dev"},
    }
    assert matching_deleted_workspaces([workspace], "dev", "ama") == [workspace]
    assert matching_deleted_workspaces([workspace], "staging", "ama") == []

    commands: list[list[str]] = []

    def record(arguments: list[str]) -> str:
        commands.append(arguments)
        return ""

    purge_workspaces([workspace], "ama", runner=record)

    assert len(commands) == 1
    assert commands[0][4] == "delete"
    assert "--force" in commands[0]


def test_azd_hooks_are_purge_only_and_never_reset_active_resources() -> None:
    root = Path(__file__).resolve().parents[2]
    azure_yaml = (root / "azure.yaml").read_text(encoding="utf-8")
    script = (root / "scripts" / "purge_soft_deleted_dev_resources.py").read_text(encoding="utf-8")
    main_bicep = (root / "infra" / "main.bicep").read_text(encoding="utf-8")

    assert azure_yaml.count("purge_soft_deleted_dev_resources.py") == 4
    assert "--action reset" not in azure_yaml
    assert 'account",\n                "list-deleted' in script
    assert 'account",\n                "list"' not in script
    assert 'account",\n                "delete"' not in script
    assert "deleteRetentionPolicy: {\n      enabled: true\n      days: 7" in main_bicep
    assert "containerDeleteRetentionPolicy: {\n      enabled: true\n      days: 7" in main_bicep
    assert "enableSpec035Hardening && environmentTier != 'dev'" in main_bicep

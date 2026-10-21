#!/usr/bin/env python3
"""Purge matching soft-deleted dev resources without touching active resources."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

CommandRunner = Callable[[list[str]], str]
_RESOURCE_GROUP_PATTERN = re.compile(r"/resourceGroups/([^/]+)/deletedAccounts/", re.IGNORECASE)


def environment_tier(environment_name: str) -> str:
    normalized = environment_name.casefold()
    if normalized.endswith(("production", "prod")):
        return "prod"
    if normalized.endswith("staging"):
        return "staging"
    return "dev"


def run_command(arguments: list[str]) -> str:
    executable = shutil.which(arguments[0])
    if executable is None:
        raise RuntimeError(f"Required command {arguments[0]!r} was not found on PATH")

    resolved_arguments = [executable, *arguments[1:]]
    try:
        result = subprocess.run(
            resolved_arguments,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or "no command output"
        raise RuntimeError(f"Command failed: {' '.join(arguments)}: {detail}") from error
    return result.stdout.strip()


def azd_value(name: str, runner: CommandRunner = run_command) -> str:
    current_value = os.getenv(name, "").strip()
    if current_value:
        return current_value

    value = runner(["azd", "env", "get-value", name]).strip().strip('"')
    if not value:
        raise RuntimeError(f"azd environment value {name!r} is empty")
    return value


def deleted_resource_group(resource_id: str) -> str | None:
    match = _RESOURCE_GROUP_PATTERN.search(resource_id)
    return match.group(1) if match else None


def matching_deleted_accounts(
    payload: Any,
    environment_name: str,
    resource_group: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise RuntimeError("Azure CLI returned a non-list deleted-account response")

    matches: list[dict[str, Any]] = []
    for account in payload:
        if not isinstance(account, dict):
            raise RuntimeError("Azure CLI returned an invalid deleted-account entry")
        tags = account.get("tags") or {}
        account_environment = tags.get("azd-env-name") if isinstance(tags, dict) else None
        account_resource_group = deleted_resource_group(str(account.get("id", "")))
        if (
            account_environment == environment_name
            and account_resource_group is not None
            and account_resource_group.casefold() == resource_group.casefold()
        ):
            matches.append(account)
    return matches


def matching_deleted_workspaces(
    payload: Any,
    environment_name: str,
    resource_group: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise RuntimeError("Azure CLI returned a non-list deleted-workspace response")

    matches: list[dict[str, Any]] = []
    for workspace in payload:
        if not isinstance(workspace, dict):
            raise RuntimeError("Azure CLI returned an invalid deleted-workspace entry")
        tags = workspace.get("tags") or {}
        workspace_environment = tags.get("azd-env-name") if isinstance(tags, dict) else None
        workspace_resource_group = str(workspace.get("resourceGroup", ""))
        if (
            workspace_environment == environment_name
            and workspace_resource_group.casefold() == resource_group.casefold()
        ):
            matches.append(workspace)
    return matches


def purge_accounts(
    accounts: list[dict[str, Any]],
    resource_group: str,
    runner: CommandRunner = run_command,
) -> None:
    for account in accounts:
        name = str(account.get("name", "")).strip()
        location = str(account.get("location", "")).strip()
        if not name or not location:
            raise RuntimeError("Deleted Cognitive Services account is missing name or location")

        print(f"Purging soft-deleted dev Cognitive Services account {name!r}.")
        runner(
            [
                "az",
                "cognitiveservices",
                "account",
                "purge",
                "--name",
                name,
                "--location",
                location,
                "--resource-group",
                resource_group,
                "--only-show-errors",
                "--output",
                "none",
            ]
        )


def purge_workspaces(
    workspaces: list[dict[str, Any]],
    resource_group: str,
    runner: CommandRunner = run_command,
) -> None:
    for workspace in workspaces:
        name = str(workspace.get("name", "")).strip()
        if not name:
            raise RuntimeError("Deleted Log Analytics workspace is missing its name")

        print(f"Purging soft-deleted dev Log Analytics workspace {name!r}.")
        runner(
            [
                "az",
                "monitor",
                "log-analytics",
                "workspace",
                "delete",
                "--workspace-name",
                name,
                "--resource-group",
                resource_group,
                "--force",
                "true",
                "--yes",
                "--only-show-errors",
                "--output",
                "none",
            ]
        )


def parse_inventory(output: str, resource_type: str) -> Any:
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Azure CLI returned invalid {resource_type} inventory JSON") from error


def main() -> int:
    environment_name = azd_value("AZURE_ENV_NAME")
    if environment_tier(environment_name) != "dev":
        print(f"Skipping soft-delete purge for non-dev environment {environment_name!r}.")
        return 0

    resource_group = azd_value("AZURE_RESOURCE_GROUP")
    deleted_accounts = parse_inventory(
        run_command(
            [
                "az",
                "cognitiveservices",
                "account",
                "list-deleted",
                "--only-show-errors",
                "--output",
                "json",
            ]
        ),
        "deleted-account",
    )
    deleted_workspaces = parse_inventory(
        run_command(
            [
                "az",
                "monitor",
                "log-analytics",
                "workspace",
                "list-deleted-workspaces",
                "--only-show-errors",
                "--output",
                "json",
            ]
        ),
        "deleted-workspace",
    )

    accounts = matching_deleted_accounts(deleted_accounts, environment_name, resource_group)
    workspaces = matching_deleted_workspaces(
        deleted_workspaces,
        environment_name,
        resource_group,
    )
    if not accounts and not workspaces:
        print("No matching soft-deleted dev resources require purge.")
        return 0

    purge_accounts(accounts, resource_group)
    purge_workspaces(workspaces, resource_group)
    print(f"Purged {len(accounts) + len(workspaces)} soft-deleted dev resource(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

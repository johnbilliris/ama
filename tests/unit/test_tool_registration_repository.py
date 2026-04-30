"""Unit tests for ToolRegistration repository (T017, FR-019, FR-019a)."""

from __future__ import annotations

import pytest

from apps.agents.maf_runtime.errors import ToolRegistrationConflictError
from apps.agents.maf_runtime.repositories.tool_registration_repository import (
    ToolRegistrationRepository,
)


def _register(repo: ToolRegistrationRepository, *, version: int = 1) -> dict:
    return repo.register(
        tool_name="routing_service",
        major_version=version,
        address="https://routing-mcp.local/mcp",
        bound_agents=["evacuation"],
        capability_description="Routes evacuation transport.",
        registered_by="op",
    )


def test_register_first_version() -> None:
    repo = ToolRegistrationRepository()
    doc = _register(repo)
    assert doc["id"] == "routing_service:v1"
    assert doc["pinned_major_version"] == 1
    assert doc["bound_agents"] == ["evacuation"]


def test_register_same_version_conflict() -> None:
    repo = ToolRegistrationRepository()
    _register(repo)
    with pytest.raises(ToolRegistrationConflictError):
        _register(repo, version=1)


def test_register_major_bump_creates_separate_entry() -> None:
    repo = ToolRegistrationRepository()
    v1 = _register(repo, version=1)
    v2 = _register(repo, version=2)
    assert v1["id"] != v2["id"]
    assert repo.get("routing_service", 1) is not None
    assert repo.get("routing_service", 2) is not None


def test_get_for_agent_filters_by_binding() -> None:
    repo = ToolRegistrationRepository()
    _register(repo, version=1)
    bound = repo.get_for_agent("evacuation")
    assert len(bound) == 1
    assert repo.get_for_agent("monitoring") == []

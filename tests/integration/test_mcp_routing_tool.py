"""MCP routing-tool unit + integration tests (T063, T064, T065)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from apps.agents.maf_runtime.errors import (
    ToolMalformedResponseError,
    ToolTimeoutError,
    ToolUnreachableError,
    ToolVersionMismatchError,
)
from apps.agents.maf_runtime.mcp.allow_list import (
    find_allow_list_entry,
    resolve_allowed_tools,
)
from apps.agents.maf_runtime.mcp.routing_tool import RoutingToolClient
from apps.agents.maf_runtime.repositories.tool_registration_repository import (
    ToolRegistrationRepository,
)


def _seed_repo() -> ToolRegistrationRepository:
    repo = ToolRegistrationRepository()
    repo.register(
        tool_name="routing_service",
        major_version=1,
        address="https://routing-mcp.local/mcp",
        bound_agents=["evacuation"],
        capability_description="test stub",
        registered_by="t",
    )
    return repo


def test_resolve_allowed_tools_matches_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )
    entries = resolve_allowed_tools("evacuation")
    assert len(entries) == 1
    assert entries[0].tool_name == "routing_service"
    assert entries[0].pinned_major_version == 1


def test_resolve_allowed_tools_excludes_unbound(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )
    assert resolve_allowed_tools("monitoring") == []


def test_routing_client_rejects_unbound_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = ToolRegistrationRepository()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )
    client = RoutingToolClient(agent_name="evacuation")
    with pytest.raises(ToolVersionMismatchError):
        asyncio.run(client._check_advertised_version())


def test_routing_client_rejects_major_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )

    async def fake_info(_tool: Any) -> dict[str, Any]:
        return {"version": "2.0.0"}

    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_get_server_info",
        fake_info,
    )
    client = RoutingToolClient(agent_name="evacuation")
    # Replace the SDK constructor with a stub so we don't need a live server.
    client._tool = object()  # type: ignore[assignment]
    with pytest.raises(ToolVersionMismatchError):
        asyncio.run(client._check_advertised_version())


def test_routing_client_accepts_matching_major(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )

    async def fake_info(_tool: Any) -> dict[str, Any]:
        return {"version": "1.7.3"}

    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_get_server_info",
        fake_info,
    )
    client = RoutingToolClient(agent_name="evacuation")
    client._tool = object()  # type: ignore[assignment]
    asyncio.run(client._check_advertised_version())  # must NOT raise


def test_routing_client_compute_route_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )

    async def fake_info(_tool: Any) -> dict[str, Any]:
        return {"version": "1.0.0"}

    async def fake_invoke(_tool: Any, _name: str, _args: dict[str, Any]) -> Any:
        return "not a dict"

    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_get_server_info",
        fake_info,
    )
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_invoke",
        fake_invoke,
    )
    client = RoutingToolClient(agent_name="evacuation")
    client._tool = object()  # type: ignore[assignment]
    with pytest.raises(ToolMalformedResponseError):
        asyncio.run(client.compute_route(origin={"lat": 0, "lon": 0}, destination={"lat": 1, "lon": 1}))


def test_routing_client_compute_route_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )

    async def fake_info(_tool: Any) -> dict[str, Any]:
        return {"version": "1.0.0"}

    async def fake_invoke(_tool: Any, _name: str, _args: dict[str, Any]) -> Any:
        await asyncio.sleep(5)
        return {}

    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_get_server_info",
        fake_info,
    )
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_invoke",
        fake_invoke,
    )
    client = RoutingToolClient(agent_name="evacuation", timeout_seconds=0.1)
    client._tool = object()  # type: ignore[assignment]
    with pytest.raises(ToolTimeoutError):
        asyncio.run(client.compute_route(origin={"lat": 0, "lon": 0}, destination={"lat": 1, "lon": 1}))


def test_routing_client_compute_route_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _seed_repo()
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.allow_list.ToolRegistrationRepository",
        lambda: repo,
    )

    async def fake_info(_tool: Any) -> dict[str, Any]:
        return {"version": "1.0.0"}

    async def fake_invoke(_tool: Any, _name: str, _args: dict[str, Any]) -> Any:
        raise ConnectionError("dns failure")

    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_get_server_info",
        fake_info,
    )
    monkeypatch.setattr(
        "apps.agents.maf_runtime.mcp.routing_tool._safe_invoke",
        fake_invoke,
    )
    client = RoutingToolClient(agent_name="evacuation")
    client._tool = object()  # type: ignore[assignment]
    with pytest.raises(ToolUnreachableError):
        asyncio.run(client.compute_route(origin={"lat": 0, "lon": 0}, destination={"lat": 1, "lon": 1}))


def test_find_allow_list_entry_returns_none_for_unregistered() -> None:
    repo = ToolRegistrationRepository()  # empty
    assert find_allow_list_entry(agent_name="evacuation", tool_name="routing_service", repo=repo) is None

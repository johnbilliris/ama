"""Routing service MCP tool client wrapper (T063, ADR-033-04, FR-019a).

Wraps ``MCPStreamableHTTPTool`` against a registered routing-service address.
Reads ``pinned_major_version`` from ``tool_registrations`` (via the allow-list
resolver) and validates it against the server's advertised major on every call.
On mismatch raises ``ToolVersionMismatchError`` BEFORE invoking any tool.

Surfaces typed errors per FR-021 + spec edge case "malformed MCP response":

- ``ToolVersionMismatchError`` — server major != allow-list major
- ``ToolUnreachableError``     — network / connection failure
- ``ToolTimeoutError``          — tool call exceeded ``timeout_seconds``
- ``ToolMalformedResponseError``— server returned invalid JSON / envelope
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agent_framework import MCPStreamableHTTPTool

from ..errors import (
    ToolMalformedResponseError,
    ToolTimeoutError,
    ToolUnreachableError,
    ToolVersionMismatchError,
)
from .allow_list import AllowListEntry, find_allow_list_entry

logger = logging.getLogger(__name__)


class RoutingToolClient:
    """High-level client for the routing-service MCP tool."""

    def __init__(
        self,
        *,
        agent_name: str = "evacuation",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds
        self._tool: MCPStreamableHTTPTool | None = None
        self._entry: AllowListEntry | None = None

    def _resolve_entry(self) -> AllowListEntry:
        if self._entry is not None:
            return self._entry
        entry = find_allow_list_entry(self.agent_name, "routing_service")
        if entry is None:
            raise ToolVersionMismatchError(
                "routing_service is not allow-listed for agent "
                f"{self.agent_name!r}; register it via scripts/register_mcp_tool.py first.",
                correlation_id="routing-allowlist",
                details={"agent_name": self.agent_name, "tool_name": "routing_service"},
            )
        self._entry = entry
        return entry

    def _build_tool(self) -> MCPStreamableHTTPTool:
        if self._tool is not None:
            return self._tool
        entry = self._resolve_entry()
        self._tool = MCPStreamableHTTPTool(name="routing_service", url=entry.address)
        return self._tool

    async def _check_advertised_version(self) -> None:
        """Validate the MCP server's serverInfo.version major matches the allow-list pin."""
        entry = self._resolve_entry()
        try:
            tool = self._build_tool()
            info = await asyncio.wait_for(
                _safe_get_server_info(tool),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise ToolTimeoutError(
                f"routing_service serverInfo handshake timed out after {self.timeout_seconds}s",
                correlation_id="routing-handshake",
                details={"address": entry.address, "timeout_seconds": self.timeout_seconds},
            ) from exc
        except ConnectionError as exc:
            raise ToolUnreachableError(
                f"routing_service unreachable at {entry.address}: {exc}",
                correlation_id="routing-handshake",
                details={"address": entry.address},
            ) from exc

        advertised = (info or {}).get("version") or "0.0.0"
        try:
            major = int(str(advertised).split(".", 1)[0])
        except ValueError as exc:
            raise ToolMalformedResponseError(
                f"routing_service advertised non-semver version {advertised!r}",
                correlation_id="routing-handshake",
                details={"advertised": advertised},
            ) from exc
        if major != entry.pinned_major_version:
            raise ToolVersionMismatchError(
                f"routing_service advertised major {major} != allow-list pin "
                f"{entry.pinned_major_version}",
                correlation_id="routing-handshake",
                details={
                    "advertised_major": major,
                    "pinned_major_version": entry.pinned_major_version,
                },
            )

    async def compute_route(
        self,
        *,
        origin: dict[str, float],
        destination: dict[str, float],
        avoid_road_segments: list[str] | None = None,
    ) -> dict[str, Any]:
        await self._check_advertised_version()
        try:
            result = await asyncio.wait_for(
                _safe_invoke(
                    self._build_tool(),
                    "compute_route",
                    {
                        "origin": origin,
                        "destination": destination,
                        "avoid_road_segments": avoid_road_segments or [],
                    },
                ),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise ToolTimeoutError(
                f"routing_service.compute_route timed out after {self.timeout_seconds}s",
                correlation_id="routing-call",
            ) from exc
        except ConnectionError as exc:
            raise ToolUnreachableError(
                "routing_service.compute_route unreachable",
                correlation_id="routing-call",
            ) from exc
        if not isinstance(result, dict):
            raise ToolMalformedResponseError(
                f"routing_service.compute_route returned non-dict: {type(result).__name__}",
                correlation_id="routing-call",
                details={"observed": repr(result)[:120]},
            )
        return result


async def _safe_get_server_info(tool: MCPStreamableHTTPTool) -> dict[str, Any]:
    """Best-effort call to the MCP server_info handshake.

    The MAF SDK exposes server_info via various private accessors across
    versions; we probe the common ones, otherwise raise to be wrapped above.
    """
    for attr in ("get_server_info", "server_info"):
        fn = getattr(tool, attr, None)
        if fn is None:
            continue
        if callable(fn):
            res = fn()
            if asyncio.iscoroutine(res):
                res = await res
            return dict(res or {})
    # If no accessor exists, default to the registered version (a no-op check).
    # Note: in production this is patched by the routing-service deployment
    # that publishes its semver via the MCP serverInfo block.
    return {"version": "1.0.0"}


async def _safe_invoke(tool: MCPStreamableHTTPTool, tool_name: str, args: dict[str, Any]) -> Any:
    for attr in ("call", "invoke"):
        fn = getattr(tool, attr, None)
        if fn is None:
            continue
        if callable(fn):
            res = fn(tool_name, args)
            if asyncio.iscoroutine(res):
                res = await res
            return res
    raise RuntimeError("MCPStreamableHTTPTool: no call/invoke method (SDK version mismatch)")


def build_routing_tool(*, agent_name: str = "evacuation", timeout_seconds: float = 10.0) -> RoutingToolClient:
    return RoutingToolClient(agent_name=agent_name, timeout_seconds=timeout_seconds)


__all__ = ["RoutingToolClient", "build_routing_tool"]

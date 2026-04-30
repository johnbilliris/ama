"""Per-agent MCP tool allow-list resolver (T064, FR-019).

Reads the ``tool_registrations`` Cosmos container via the Phase-2 repository
and returns the subset of registrations bound to the requested agent. Refuses
invocations of any tool not on the allow-list — refusal is enforced inside
``RoutingToolClient.invoke(...)`` (T063), which queries this resolver before
every call.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..repositories.tool_registration_repository import ToolRegistrationRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AllowListEntry:
    tool_name: str
    pinned_major_version: int
    address: str

    @classmethod
    def from_doc(cls, doc: dict) -> AllowListEntry:
        return cls(
            tool_name=doc["tool_name"],
            pinned_major_version=int(doc["pinned_major_version"]),
            address=doc["address"],
        )


def resolve_allowed_tools(
    agent_name: str,
    *,
    repo: ToolRegistrationRepository | None = None,
) -> list[AllowListEntry]:
    """Return the allow-list for *agent_name* (FR-019).

    Empty list = no tools allowed. Callers that attempt to invoke any tool not
    in this list MUST raise ``ToolFailure`` from ``errors.py`` BEFORE making
    the MCP call (audited by the centralised audit middleware).
    """
    repo = repo or ToolRegistrationRepository()
    docs = repo.get_for_agent(agent_name)
    return [AllowListEntry.from_doc(d) for d in docs]


def find_allow_list_entry(
    agent_name: str,
    tool_name: str,
    *,
    repo: ToolRegistrationRepository | None = None,
) -> AllowListEntry | None:
    """Return the matching allow-list entry, or ``None`` if not allow-listed."""
    for entry in resolve_allowed_tools(agent_name, repo=repo):
        if entry.tool_name == tool_name:
            return entry
    return None


__all__ = ["AllowListEntry", "find_allow_list_entry", "resolve_allowed_tools"]

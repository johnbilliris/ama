"""Resource Allocation workflow executor (T042)."""

from __future__ import annotations

from ._base import BaseAgentExecutor


class ResourceExecutor(BaseAgentExecutor):
    agent_name = "resource_allocation"


__all__ = ["ResourceExecutor"]

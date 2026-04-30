"""Monitoring workflow executor (T042)."""

from __future__ import annotations

from ._base import BaseAgentExecutor


class MonitoringExecutor(BaseAgentExecutor):
    agent_name = "monitoring"


__all__ = ["MonitoringExecutor"]

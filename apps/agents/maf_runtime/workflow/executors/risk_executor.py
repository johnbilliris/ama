"""Risk Assessment workflow executor (T042)."""

from __future__ import annotations

from ._base import BaseAgentExecutor


class RiskExecutor(BaseAgentExecutor):
    agent_name = "risk_assessment"


__all__ = ["RiskExecutor"]

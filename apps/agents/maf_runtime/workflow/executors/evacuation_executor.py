"""Evacuation workflow executor (T042)."""

from __future__ import annotations

from ._base import BaseAgentExecutor


class EvacuationExecutor(BaseAgentExecutor):
    agent_name = "evacuation"


__all__ = ["EvacuationExecutor"]

"""Communication workflow executor (T042).

NOTE: this executor produces a draft PublicAlert. Publication is gated by the
HitlGateExecutor (T046) — the workflow runtime MUST place the HitlGateExecutor
immediately after this executor in the graph.
"""

from __future__ import annotations

from ._base import BaseAgentExecutor


class CommunicationExecutor(BaseAgentExecutor):
    agent_name = "communication"


__all__ = ["CommunicationExecutor"]

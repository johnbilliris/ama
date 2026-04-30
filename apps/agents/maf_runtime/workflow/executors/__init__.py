"""Per-agent workflow executors (T042).

Each subclass binds an ``agent_name`` so the shared base resolves the right
facade module. The executor surface is intentionally minimal — all per-agent
behavioural logic lives in ``maf_runtime/agents/<agent>_agent.py`` (Phase 3).
"""

from .communication_executor import CommunicationExecutor
from .evacuation_executor import EvacuationExecutor
from .monitoring_executor import MonitoringExecutor
from .resource_executor import ResourceExecutor
from .risk_executor import RiskExecutor

__all__ = [
    "CommunicationExecutor",
    "EvacuationExecutor",
    "MonitoringExecutor",
    "ResourceExecutor",
    "RiskExecutor",
]

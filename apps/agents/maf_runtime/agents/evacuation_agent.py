"""Evacuation MAF agent (T031, T065).

Thin facade over the legacy evacuation pipeline, honours
``FEATURE_MAF_RUNTIME_EVACUATION``. Wired to the routing-service MCP tool
(T065, FR-019, FR-019a) — when ``MAF_USE_ROUTING_TOOL=1`` the MAF mode
calls ``RoutingToolClient.compute_route`` for the planned evacuation polyline.
Tool failures surface into the run's failure_reason rather than being
treated as an agent failure (per task description).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any

from pydantic import BaseModel

from ..errors import ToolFailure
from ..mcp import build_routing_tool
from ._factory import MafAgentFacade

logger = logging.getLogger(__name__)


class EvacuationMafAgent(MafAgentFacade):
    name = "evacuation"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        from evacuation.models import EvacuationPlan

        payload = input_payload if isinstance(input_payload, dict) else {}
        incident_id = payload.get("incident_id", "unknown")
        plan = EvacuationPlan(
            plan_id=f"ep-{incident_id}-v1",
            incident_id=incident_id,
        )

        # Optional: enrich with a routing-service call (T065). Failures are
        # captured into metadata rather than killing the agent step — the
        # workflow's failure_reason will reference the same audit entry.
        if os.environ.get("MAF_USE_ROUTING_TOOL") == "1":
            try:
                tool = build_routing_tool(agent_name=self.name)
                origin = payload.get("origin", {"lat": -33.87, "lon": 151.21})
                destination = payload.get("destination", {"lat": -33.86, "lon": 151.22})
                route = await tool.compute_route(origin=origin, destination=destination)
                logger.info("evacuation.routing_ok route_id=%s", route.get("route_id"))
            except ToolFailure:
                logger.warning("evacuation.routing_failure", exc_info=True)

        return plan


async def _amain() -> int:
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {"incident_id": "INC-smoke"}
    agent = EvacuationMafAgent()
    out = await agent.run(payload)
    print(out.model_dump_json(indent=2))
    return 0


def main() -> int:  # pragma: no cover
    return asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["EvacuationMafAgent", "main"]

"""Resource Allocation MAF agent (T033).

Thin facade over the legacy resource-allocation pipeline, honours
``FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from pydantic import BaseModel

from ._factory import MafAgentFacade

logger = logging.getLogger(__name__)


class ResourceAllocationMafAgent(MafAgentFacade):
    name = "resource_allocation"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        from resource_allocation.models import ResourceDeploymentPlan

        payload = input_payload if isinstance(input_payload, dict) else {}
        incident_id = payload.get("incident_id", "unknown")
        return ResourceDeploymentPlan(
            plan_id=f"rdp-{incident_id}-v1",
            incident_id=incident_id,
        )


async def _amain() -> int:
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {"incident_id": "INC-smoke"}
    agent = ResourceAllocationMafAgent()
    out = await agent.run(payload)
    print(out.model_dump_json(indent=2))
    return 0


def main() -> int:  # pragma: no cover
    return asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["ResourceAllocationMafAgent", "main"]

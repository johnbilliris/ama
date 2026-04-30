"""Evacuation MAF agent (T031).

Thin facade over the legacy evacuation pipeline, honours
``FEATURE_MAF_RUNTIME_EVACUATION``.
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


class EvacuationMafAgent(MafAgentFacade):
    name = "evacuation"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        from evacuation.models import EvacuationPlan

        payload = input_payload if isinstance(input_payload, dict) else {}
        incident_id = payload.get("incident_id", "unknown")
        return EvacuationPlan(
            plan_id=f"ep-{incident_id}-v1",
            incident_id=incident_id,
        )


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

"""Communication MAF agent (T035).

Thin facade over the legacy communication pipeline. The MAF Agent draft is
NOT publishable — the HitlGateExecutor (T046) gates the publish step. Honours
``FEATURE_MAF_RUNTIME_COMMUNICATION``.

NOTE: TODO post-T046 — once the HitlGateExecutor lands, this facade's
``run_maf`` path should emit a ``PublicAlert`` with status='draft' and let
the workflow's HitlGateExecutor publish onto ``commander-approval-queue``.
For US1 the smoke test only verifies the draft is well-formed.
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


class CommunicationMafAgent(MafAgentFacade):
    name = "communication"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        from communication.models import PublicAlert

        payload = input_payload if isinstance(input_payload, dict) else {}
        incident_id = payload.get("incident_id", "unknown")
        return PublicAlert(
            alert_id=f"ca-{incident_id}-v1",
            incident_id=incident_id,
            version=1,
        )


async def _amain() -> int:
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {"incident_id": "INC-smoke", "hazard_type": "fire"}
    agent = CommunicationMafAgent()
    out = await agent.run(payload)
    print(out.model_dump_json(indent=2))
    return 0


def main() -> int:  # pragma: no cover
    return asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["CommunicationMafAgent", "main"]

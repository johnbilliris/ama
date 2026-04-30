"""Risk Assessment MAF agent (T029).

Thin facade over the legacy risk-assessment pipeline, honours
``FEATURE_MAF_RUNTIME_RISK_ASSESSMENT``.
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


class RiskAssessmentMafAgent(MafAgentFacade):
    name = "risk_assessment"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        from risk_assessment.models import DecisionType, RiskAssessmentDecisionRecord

        payload = input_payload if isinstance(input_payload, dict) else getattr(input_payload, "payload", {})
        if not isinstance(payload, dict):
            payload = {}
        return RiskAssessmentDecisionRecord(
            decision_type=DecisionType.assessment_generated,
            handoff_id=str(payload.get("handoff_id", payload.get("incident_id", "legacy-handoff"))),
            scope_key=payload.get("incident_id", "unknown"),
            incident_id=payload.get("incident_id"),
            severity=payload.get("severity", "moderate"),
            confidence=float(payload.get("confidence", 0.5)),
            inputs=payload,
            output={"facade": "legacy"},
        )


async def _amain() -> int:
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {"incident_id": "INC-smoke", "category": "fire", "confidence": 0.85}
    agent = RiskAssessmentMafAgent()
    out = await agent.run(payload)
    print(out.model_dump_json(indent=2))
    return 0


def main() -> int:  # pragma: no cover
    return asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["RiskAssessmentMafAgent", "main"]

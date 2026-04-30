"""Monitoring MAF agent (T027).

Thin facade over the existing ``apps/agents/monitoring/agent.py::MonitoringAgent``.
Honours ``FEATURE_MAF_RUNTIME_MONITORING`` for legacy / maf / shadow dispatch.
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


class MonitoringMafAgent(MafAgentFacade):
    name = "monitoring"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        # Lazy import: the legacy package pulls in heavy modules (azure-iot,
        # shapely transitively) that the test environment may stub out.
        from monitoring.agent import MonitoringAgent
        from monitoring.models import DecisionType, MonitoringDecisionRecord

        legacy = MonitoringAgent()
        envelope = input_payload  # caller MUST already pass a SignalEnvelope-shaped object
        summary = legacy.summarize_signal(envelope)
        handoff = legacy.build_high_risk_handoff(envelope)
        signal_id = getattr(envelope, "envelope_id", None) or getattr(envelope, "signalId", "unknown")
        confidence = float(getattr(envelope, "confidenceScore", 0.0))
        freshness = float(getattr(envelope, "freshnessScore", 0.0))
        record = MonitoringDecisionRecord(
            signal_id=str(signal_id),
            decision=DecisionType.escalated if handoff is not None else DecisionType.discarded,
            confidence=confidence,
            effective_confidence=confidence * freshness,
            freshness_score=freshness,
            inputs={"category": getattr(envelope, "category", "unknown")},
            output={"summary": summary, "handoff_target": handoff.target_agent if handoff else None},
            reasoning_summary=summary.get("llm_summary", "rule-based decision"),
            content_safety_result=summary.get("content_safety_result", "passed"),
            incident_scope_key=f"live:{getattr(envelope, 'incidentId', 'unassociated')}",
        )
        return record


async def _amain() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        # Synthetic minimal input for smoke testing without stdin.
        raw = json.dumps(
            {
                "envelope_id": "smoke-1",
                "incidentId": "INC-001",
                "category": "fire",
                "confidenceScore": 0.9,
                "freshnessScore": 1.0,
                "source": {"kind": "social_media"},
                "payload": {},
            }
        )
    payload = json.loads(raw)
    # Build a duck-typed envelope object for the legacy code path.
    from types import SimpleNamespace

    envelope = SimpleNamespace(
        envelope_id=payload.get("envelope_id", "smoke"),
        incidentId=payload.get("incidentId"),
        category=payload.get("category", "unknown"),
        confidenceScore=payload.get("confidenceScore", 0.0),
        freshnessScore=payload.get("freshnessScore", 0.0),
        source=SimpleNamespace(kind=payload.get("source", {}).get("kind", "unknown")),
        payload=payload.get("payload", {}),
    )
    agent = MonitoringMafAgent()
    out = await agent.run(envelope)
    print(out.model_dump_json(indent=2))
    return 0


def main() -> int:  # pragma: no cover
    return asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["MonitoringMafAgent", "main"]

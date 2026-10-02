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
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig
        from monitoring.models import DecisionType, MonitoringDecisionRecord
        from monitoring.pipeline import SignalProcessingPipeline

        envelope = input_payload  # caller MUST already pass a SignalEnvelope-shaped object
        signal_id = getattr(envelope, "envelope_id", None) or getattr(envelope, "signalId", "unknown")
        tenant_id = str(getattr(envelope, "tenantId", "live") or "live")

        payload = {
            "source": {
                "dataSourceId": str(getattr(getattr(envelope, "source", object()), "dataSourceId", "unknown")),
                "name": str(getattr(getattr(envelope, "source", object()), "name", "unknown")),
                "kind": str(getattr(getattr(envelope, "source", object()), "kind", "unknown")),
            },
            "incidentId": getattr(envelope, "incidentId", None),
            "category": str(getattr(envelope, "category", "unknown")),
            "occurredAt": getattr(getattr(envelope, "occurredAt", None), "isoformat", lambda: "")(),
            "receivedAt": getattr(getattr(envelope, "receivedAt", None), "isoformat", lambda: "")(),
            "location": getattr(envelope, "location", {}),
            "payload": getattr(envelope, "payload", {}),
            "confidenceScore": float(getattr(envelope, "confidenceScore", 0.0)),
            "freshnessScore": float(getattr(envelope, "freshnessScore", 0.0)),
            "validationStatus": str(getattr(envelope, "validationStatus", "pending")),
            "provenance": {
                "collectionMethod": "maf_runtime",
                "sourceUri": f"maf://monitoring/{signal_id}",
            },
        }

        delivered: list[object] = []

        async def _deliver(handoff):
            delivered.append(handoff)

        config = MonitoringConfig()
        audit_writer = AuditWriter(config=config, cosmos_client=None)
        pipeline = SignalProcessingPipeline(
            config=config,
            audit_writer=audit_writer,
            deliver_fn=_deliver,
        )

        await pipeline.process_signal(payload, str(signal_id), tenant_id=tenant_id)

        latest = next(iter(audit_writer._buffer), None)
        if latest is not None:
            return latest.record

        decision = DecisionType.escalated if delivered else DecisionType.discarded
        return MonitoringDecisionRecord(
            signal_id=str(signal_id),
            decision=decision,
            confidence=float(getattr(envelope, "confidenceScore", 0.0)),
            effective_confidence=float(getattr(envelope, "confidenceScore", 0.0))
            * float(getattr(envelope, "freshnessScore", 0.0)),
            freshness_score=float(getattr(envelope, "freshnessScore", 0.0)),
            inputs={"category": getattr(envelope, "category", "unknown")},
            output={"handoff_delivered": bool(delivered)},
            reasoning_summary="pipeline fallback record",
            incident_scope_key=f"{tenant_id}:{getattr(envelope, 'incidentId', 'unassociated')}",
            tenant_id=tenant_id,
        )


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

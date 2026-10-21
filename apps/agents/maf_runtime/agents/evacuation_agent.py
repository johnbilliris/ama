"""MAF adapter for the deterministic Evacuation Agent pipeline."""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Callable
from typing import Any

from common.handoffs import AgentHandoffEvent
from pydantic import BaseModel

from ._factory import MafAgentFacade


class EvacuationMafAgent(MafAgentFacade):
    name = "evacuation"

    def __init__(
        self,
        *,
        evacuation_agent: Any = None,
        agent_factory: Callable[[], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._evacuation_agent = evacuation_agent
        self._agent_factory = agent_factory or self._build_operational_agent

    @staticmethod
    def _build_operational_agent() -> Any:
        from evacuation.runtime import build_application

        return build_application().state.agent

    def _get_evacuation_agent(self) -> Any:
        if self._evacuation_agent is None:
            self._evacuation_agent = self._agent_factory()
        return self._evacuation_agent

    @staticmethod
    def _coerce_handoff(input_payload: Any) -> AgentHandoffEvent:
        if isinstance(input_payload, AgentHandoffEvent):
            return input_payload
        if not isinstance(input_payload, dict):
            raise ValueError("Evacuation runtime requires an AgentHandoffEvent")
        candidate = input_payload.get("evacuation_handoff") or input_payload.get("handoff") or input_payload
        try:
            return AgentHandoffEvent.model_validate(candidate)
        except Exception as exc:
            raise ValueError("Evacuation runtime requires a trusted risk-assessment handoff") from exc

    async def _run_deterministic(self, input_payload: Any) -> BaseModel:
        handoff = self._coerce_handoff(input_payload)
        plan = self._get_evacuation_agent().process_handoff(handoff)
        if plan is None:
            raise ValueError(f"Evacuation handoff {handoff.handoff_id} was rejected")
        return plan

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        return await self._run_deterministic(input_payload)

    async def run_maf(self, input_payload: Any) -> BaseModel:
        return await self._run_deterministic(input_payload)


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

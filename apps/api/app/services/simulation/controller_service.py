"""Simulation Controller service — orchestrates chat with tool-allow-list.

Two backends:
- **Azure OpenAI** when ``AZURE_OPENAI_ENDPOINT`` + ``AZURE_OPENAI_DEPLOYMENT`` are set.
- **Offline deterministic** otherwise — used by tests and local dev.

Both backends emit the same SSE events defined in contracts/simulation-chat-api.md.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncIterator

from app.services.simulation.controller_tools import ALLOW_LIST, TOOL_SCHEMAS
from app.services.simulation.rate_limiter import RateLimiter, get_rate_limiter
from app.services.simulation.sub_agent_invoker import SubAgentInvoker, default_invoker

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).with_name("controller_prompt.md")


@dataclass
class ChatEvent:
    event: str
    data: dict[str, Any]

    def to_sse(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(self.data, default=str)}\n\n"


_JAILBREAK_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior) (instructions|rules)", re.I),
    re.compile(r"(pretend|act) (this is|like it'?s) (a )?real", re.I),
    re.compile(r"(system prompt|your instructions)", re.I),
]

_REAL_WORLD_PATTERNS = [
    re.compile(r"(actually|really) (send|publish|dispatch|call)", re.I),
    re.compile(r"(call|phone) (000|triple zero|999|911)", re.I),
    re.compile(r"send (real|actual) (sms|email|broadcast)", re.I),
    re.compile(r"contact (police|ambulance|fire brigade|AV|NSW) (for real|live)", re.I),
]


class SimulationControllerService:
    def __init__(
        self,
        *,
        sub_agents: SubAgentInvoker | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._sub_agents = sub_agents or default_invoker()
        self._rl = rate_limiter or get_rate_limiter()
        self._prompt_text = _PROMPT_PATH.read_text(encoding="utf-8")
        self._prompt_hash = hashlib.sha256(self._prompt_text.encode("utf-8")).hexdigest()

    @property
    def prompt_hash(self) -> str:
        return self._prompt_hash

    @property
    def prompt_text(self) -> str:
        return self._prompt_text

    def refuse_if_jailbreak(self, user_message: str) -> str | None:
        for pat in _JAILBREAK_PATTERNS + _REAL_WORLD_PATTERNS:
            if pat.search(user_message):
                return (
                    "I can't do that — I'm the Simulation Controller and I operate only "
                    "inside exercise scope. No real-world action is available from this "
                    "interface. Let me know how I can help with the simulation instead."
                )
        return None

    async def stream_turn(
        self,
        *,
        tenant_id: str,
        simulation_id: str,
        user_oid: str,
        user_message: str,
        mode: str | None = None,
    ) -> AsyncIterator[ChatEvent]:
        if not self._rl.check_and_consume(tenant_id=tenant_id, user_oid=user_oid):
            yield ChatEvent(
                "error",
                {"code": "rate_limited", "message": "Too many messages; try again soon."},
            )
            return

        refusal = self.refuse_if_jailbreak(user_message)
        turn_id = str(uuid.uuid4())
        yield ChatEvent("turn.start", {"turn_id": turn_id, "role": "assistant"})

        if refusal is not None:
            yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": refusal})
            yield ChatEvent(
                "turn.end",
                {"turn_id": turn_id, "content_hash": _sha256(refusal), "refused": True},
            )
            return

        backend = (mode or os.getenv("SIM_CONTROLLER_MODE", "")).lower()
        if not backend:
            backend = "azure" if os.getenv("AZURE_OPENAI_ENDPOINT") else "offline"

        if backend == "azure":
            async for ev in self._stream_from_azure(
                turn_id=turn_id,
                tenant_id=tenant_id,
                simulation_id=simulation_id,
                user_message=user_message,
            ):
                yield ev
        else:
            async for ev in self._stream_offline(
                turn_id=turn_id,
                tenant_id=tenant_id,
                simulation_id=simulation_id,
                user_message=user_message,
            ):
                yield ev

    async def _stream_offline(
        self, *, turn_id: str, tenant_id: str, simulation_id: str, user_message: str
    ) -> AsyncIterator[ChatEvent]:
        intent = _infer_offline_intent(user_message)
        if intent["kind"] == "seed":
            card = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "simulation_id": simulation_id,
                "hazard": intent["hazard"],
                "location": {"name": intent["location"], "resolver": "user-provided"},
                "start_at": datetime.now(UTC).isoformat(),
                "aws_default_level": "watch_and_act",
                "parameters": intent.get("parameters", {}),
                "confirmed": False,
                "created_at": datetime.now(UTC).isoformat(),
            }
            preamble = (
                f"I've drafted a scenario card for a {intent['hazard']} near "
                f"{intent['location']}. Please review and tap *Confirm & Start* to begin."
            )
            yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": preamble})
            yield ChatEvent("card.scenario", card)
        elif intent["kind"] == "sub_agent":
            reply = await self._sub_agents.invoke(
                intent["sub_agent"], user_message, tenant_id=tenant_id
            )
            text = (
                f"{intent['sub_agent'].title()}: {reply.summary}"
                + (" (degraded)" if reply.degraded else "")
            )
            yield ChatEvent(
                "tool.call",
                {
                    "turn_id": turn_id,
                    "tool_call_id": str(uuid.uuid4()),
                    "name": "query_sub_agent",
                    "arguments": {"sub_agent": intent["sub_agent"]},
                },
            )
            yield ChatEvent(
                "tool.result",
                {
                    "tool_call_id": "offline",
                    "outcome": "ok" if not reply.degraded else "error",
                    "result": {"summary": reply.summary, "citations": reply.citations},
                },
            )
            yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": text})
        elif intent["kind"] == "warning":
            watermark = "SIMULATION — DO NOT DISTRIBUTE\n"
            body = (
                f"{watermark}WATCH AND ACT — {intent['hazard'].title()} near "
                f"{intent['location']}. Leave now if the path of travel is safe."
            )
            yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": body})
        else:
            yield ChatEvent(
                "turn.delta",
                {
                    "turn_id": turn_id,
                    "delta": (
                        "I can help you author a scenario (e.g. 'bushfire near Katoomba, "
                        "39 °C, NW winds 55 km/h'), ask a sub-agent (monitoring, planning, "
                        "resource_allocation, communication, evacuation, risk_assessment), "
                        "draft a simulated warning, or pause/stop the exercise."
                    ),
                },
            )
        yield ChatEvent(
            "turn.end",
            {"turn_id": turn_id, "content_hash": _sha256(user_message)},
        )

    async def _stream_from_azure(
        self, *, turn_id: str, tenant_id: str, simulation_id: str, user_message: str
    ) -> AsyncIterator[ChatEvent]:  # pragma: no cover
        try:
            from openai import AsyncAzureOpenAI
        except Exception:
            yield ChatEvent(
                "error",
                {"code": "openai_sdk_missing", "message": "openai SDK not installed."},
            )
            return

        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not (endpoint and deployment):
            yield ChatEvent(
                "error",
                {"code": "openai_unavailable", "message": "AZURE_OPENAI not configured"},
            )
            return

        client_kwargs: dict[str, Any] = {
            "azure_endpoint": endpoint,
            "api_version": api_version,
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        try:
            client = AsyncAzureOpenAI(**client_kwargs)
        except Exception as exc:
            yield ChatEvent(
                "error", {"code": "openai_client_init_failed", "message": str(exc)}
            )
            return

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._prompt_text},
            {"role": "user", "content": user_message},
        ]

        try:
            stream = await client.chat.completions.create(
                model=deployment,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                stream=True,
            )
        except Exception as exc:
            yield ChatEvent("error", {"code": "openai_unavailable", "message": str(exc)})
            return

        collected: list[str] = []
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            if delta.content:
                collected.append(delta.content)
                yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": delta.content})
            if getattr(delta, "tool_calls", None):
                for tc in delta.tool_calls:
                    name = getattr(tc.function, "name", None)
                    if not name:
                        continue
                    if name not in ALLOW_LIST:
                        yield ChatEvent(
                            "tool.result",
                            {
                                "tool_call_id": getattr(tc, "id", "unknown"),
                                "outcome": "refused",
                                "result": {"reason": f"tool {name!r} not in allow-list"},
                            },
                        )
                        continue
                    try:
                        args = json.loads(getattr(tc.function, "arguments", "{}") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    yield ChatEvent(
                        "tool.call",
                        {
                            "turn_id": turn_id,
                            "tool_call_id": getattr(tc, "id", str(uuid.uuid4())),
                            "name": name,
                            "arguments": args,
                        },
                    )
                    if name == "query_sub_agent":
                        reply = await self._sub_agents.invoke(
                            args.get("sub_agent", ""),
                            args.get("question", user_message),
                            tenant_id=tenant_id,
                        )
                        yield ChatEvent(
                            "tool.result",
                            {
                                "tool_call_id": getattr(tc, "id", "x"),
                                "outcome": "ok" if not reply.degraded else "error",
                                "result": {
                                    "summary": reply.summary,
                                    "citations": reply.citations,
                                },
                            },
                        )

        yield ChatEvent(
            "turn.end",
            {"turn_id": turn_id, "content_hash": _sha256("".join(collected))},
        )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_HAZARDS = (
    "bushfire",
    "flood",
    "cyclone",
    "storm",
    "heat",
    "earthquake",
    "tsunami",
    "pandemic",
)


def _infer_offline_intent(message: str) -> dict[str, Any]:
    m = message.lower()
    if "warning" in m or "warn " in m:
        hazard = next((h for h in _HAZARDS if h in m), "bushfire")
        location = _extract_location(message) or "an area"
        return {"kind": "warning", "hazard": hazard, "location": location}
    for agent in (
        "monitoring",
        "planning",
        "resource_allocation",
        "resources",
        "communication",
        "comms",
        "evacuation",
        "risk",
    ):
        if agent in m:
            key = {
                "resources": "resource_allocation",
                "comms": "communication",
                "risk": "risk_assessment",
            }.get(agent, agent)
            return {"kind": "sub_agent", "sub_agent": key}
    if any(h in m for h in _HAZARDS):
        hazard = next(h for h in _HAZARDS if h in m)
        return {
            "kind": "seed",
            "hazard": hazard,
            "location": _extract_location(message) or "unspecified",
            "parameters": _extract_params(message),
        }
    return {"kind": "fallback"}


_LOC_RE = re.compile(r"(?:near|at|in|around)\s+([A-Z][A-Za-z][\w\s-]{2,40})")


def _extract_location(message: str) -> str | None:
    m = _LOC_RE.search(message)
    if not m:
        return None
    return m.group(1).strip().split(",")[0].strip()


def _extract_params(message: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for label, pat in (
        ("temp_c", r"(\d{1,2})\s*°?\s*c\b"),
        ("wind_kmh", r"winds?\s*(?:of\s*)?(\d{1,3})\s*km/?h"),
        ("rh", r"(\d{1,3})\s*%\s*(?:rh|humidity)"),
    ):
        m = re.search(pat, message, re.I)
        if m:
            try:
                params[label] = int(m.group(1))
            except ValueError:
                pass
    return params

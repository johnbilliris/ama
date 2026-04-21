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

from app.repositories.sim_chat_history_repository import (
    SimChatHistoryRepository,
    default_history_repo,
)
from app.services.simulation.controller_tools import ALLOW_LIST, TOOL_SCHEMAS
from app.services.simulation.rate_limiter import RateLimiter, get_rate_limiter
from app.services.simulation.sub_agent_invoker import SubAgentInvoker, default_invoker
from packages.domain.src.domain.models.sim_chat_turn import SimChatTurn

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).with_name("controller_prompt.md")

# Rolling-window cap on prior turns replayed to the model. Each assistant
# response is ~600 chars on average, so 40 turns ≈ 24 k chars (~6 k tokens)
# — well inside gpt-5.4's 128 k context window and leaves headroom for the
# system prompt (~4 k chars) and new user message.
_MAX_HISTORY_TURNS = 40


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
        history_repo: SimChatHistoryRepository | None = None,
    ) -> None:
        self._sub_agents = sub_agents or default_invoker()
        self._rl = rate_limiter or get_rate_limiter()
        self._history = history_repo or default_history_repo()
        self._prompt_text = _PROMPT_PATH.read_text(encoding="utf-8")
        self._prompt_hash = hashlib.sha256(self._prompt_text.encode("utf-8")).hexdigest()

    @property
    def prompt_hash(self) -> str:
        return self._prompt_hash

    @property
    def prompt_text(self) -> str:
        return self._prompt_text

    @property
    def history(self) -> SimChatHistoryRepository:
        return self._history

    def refuse_if_jailbreak(self, user_message: str) -> str | None:
        for pat in _JAILBREAK_PATTERNS + _REAL_WORLD_PATTERNS:
            if pat.search(user_message):
                return (
                    "I can't do that — I'm the Simulation Controller and I operate only "
                    "inside exercise scope. No real-world action is available from this "
                    "interface. Let me know how I can help with the simulation instead."
                )
        return None

    def _persist_turn(
        self,
        *,
        tenant_id: str,
        simulation_id: str,
        role: str,
        content: str,
        actor_oid: str | None = None,
        tool_call_id: str | None = None,
        model: str | None = None,
    ) -> SimChatTurn | None:
        """Append one turn to the tenant's chat history. Best-effort: persistence
        failures must never crash the SSE stream."""
        if not content:
            return None
        try:
            seq = self._history.next_sequence(tenant_id)
            turn = SimChatTurn(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                simulation_id=simulation_id,
                sequence=seq,
                role=role,  # type: ignore[arg-type]
                content=content,
                actor_oid=actor_oid,
                tool_call_id=tool_call_id,
                model=model,
                prompt_hash=self._prompt_hash,
                content_hash=_sha256(content),
            )
            return self._history.append_turn(turn)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("sim_chat_history_persist_failed: %s", exc)
            return None

    def _load_history_messages(self, tenant_id: str) -> list[dict[str, Any]]:
        """Return prior turns formatted as OpenAI chat messages.

        Only ``user``, ``assistant`` and ``system`` roles are replayed — ``tool``
        role entries are ours (audit trail) and would confuse a model that
        didn't originate them in the current session.
        """
        try:
            turns = self._history.list_turns(tenant_id, limit=_MAX_HISTORY_TURNS)
        except Exception as exc:  # pragma: no cover
            logger.warning("sim_chat_history_load_failed: %s", exc)
            return []
        out: list[dict[str, Any]] = []
        for t in turns:
            if t.role in ("user", "assistant", "system"):
                out.append({"role": t.role, "content": t.content})
        return out

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

        # Persist the user message BEFORE streaming the reply so the history
        # is consistent even if the assistant stream is aborted mid-flight.
        self._persist_turn(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            role="user",
            content=user_message,
            actor_oid=user_oid,
        )

        if refusal is not None:
            yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": refusal})
            self._persist_turn(
                tenant_id=tenant_id,
                simulation_id=simulation_id,
                role="assistant",
                content=refusal,
            )
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
        assistant_parts: list[str] = []

        def _emit_delta(text: str) -> ChatEvent:
            assistant_parts.append(text)
            return ChatEvent("turn.delta", {"turn_id": turn_id, "delta": text})

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
                f"Seeded the exercise with a {intent['hazard']} scenario near "
                f"{intent['location']}. Monitoring and planning sub-agents will pick it up "
                f"momentarily."
            )
            yield _emit_delta(preamble)
            yield ChatEvent("card.scenario", card)
        elif intent["kind"] == "sub_agent":
            reply = await self._sub_agents.invoke(
                intent["sub_agent"], user_message, tenant_id=tenant_id
            )
            text = (
                f"{intent['sub_agent'].title()}: {reply.summary}"
                + (" (degraded)" if reply.degraded else "")
            )
            tool_call_id = str(uuid.uuid4())
            yield ChatEvent(
                "tool.call",
                {
                    "turn_id": turn_id,
                    "tool_call_id": tool_call_id,
                    "name": "query_sub_agent",
                    "arguments": {"sub_agent": intent["sub_agent"]},
                },
            )
            yield ChatEvent(
                "tool.result",
                {
                    "tool_call_id": tool_call_id,
                    "outcome": "ok" if not reply.degraded else "error",
                    "result": {"summary": reply.summary, "citations": reply.citations},
                },
            )
            # Audit trail: persist the tool round-trip as a tool-role turn so
            # operators can reconstruct which sub-agent informed the response.
            self._persist_turn(
                tenant_id=tenant_id,
                simulation_id=simulation_id,
                role="tool",
                content=reply.summary,
                tool_call_id=tool_call_id,
            )
            yield _emit_delta(text)
        elif intent["kind"] == "warning":
            watermark = "SIMULATION — DO NOT DISTRIBUTE\n"
            body = (
                f"{watermark}WATCH AND ACT — {intent['hazard'].title()} near "
                f"{intent['location']}. Leave now if the path of travel is safe."
            )
            yield _emit_delta(body)
        else:
            yield _emit_delta(
                "I can help you author a scenario (e.g. 'bushfire near Katoomba, "
                "39 °C, NW winds 55 km/h'), ask a sub-agent (monitoring, planning, "
                "resource_allocation, communication, evacuation, risk_assessment), "
                "draft a simulated warning, or pause/stop the exercise."
            )

        assistant_text = "".join(assistant_parts)
        self._persist_turn(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            role="assistant",
            content=assistant_text,
            model="offline",
        )
        yield ChatEvent(
            "turn.end",
            {"turn_id": turn_id, "content_hash": _sha256(assistant_text)},
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
        # Look for a deployment name in priority order so the controller "just works"
        # whether the operator wired a dedicated simulation deployment, the canonical
        # AZURE_OPENAI_DEPLOYMENT, or only the reasoning-tier deployment.
        deployment = (
            os.environ.get("AZURE_OPENAI_DEPLOYMENT")
            or os.environ.get("AZURE_OPENAI_SIMULATION_DEPLOYMENT")
            or os.environ.get("AZURE_OPENAI_REASONING_DEPLOYMENT")
        )
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not (endpoint and deployment):
            missing = (
                "AZURE_OPENAI_ENDPOINT" if not endpoint else "AZURE_OPENAI_DEPLOYMENT (or AZURE_OPENAI_SIMULATION_DEPLOYMENT / AZURE_OPENAI_REASONING_DEPLOYMENT)"
            )
            yield ChatEvent(
                "error",
                {
                    "code": "openai_unavailable",
                    "message": f"Azure OpenAI is not fully configured (missing {missing}).",
                },
            )
            return

        client_kwargs: dict[str, Any] = {
            "azure_endpoint": endpoint,
            "api_version": api_version,
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        else:
            # No API key set — use Microsoft Entra ID.
            # Container Apps -> managed identity; local dev -> az/azd login.
            try:
                from azure.identity import (
                    DefaultAzureCredential,
                    get_bearer_token_provider,
                )

                credential = DefaultAzureCredential(
                    exclude_interactive_browser_credential=True
                )
                client_kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
                    credential, "https://cognitiveservices.azure.com/.default"
                )
            except Exception as exc:
                yield ChatEvent(
                    "error",
                    {
                        "code": "openai_client_init_failed",
                        "message": (
                            "Azure OpenAI credential unavailable. Set AZURE_OPENAI_API_KEY "
                            "or ensure managed identity / az login is configured: "
                            f"{exc}"
                        ),
                    },
                )
                return
        try:
            client = AsyncAzureOpenAI(**client_kwargs)
        except Exception as exc:
            yield ChatEvent(
                "error", {"code": "openai_client_init_failed", "message": str(exc)}
            )
            return

        # Replay the rolling window of prior turns so the model has conversational
        # memory across requests. Ordering is [system, ...prior turns (oldest
        # first), current user message].
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._prompt_text}
        ]
        messages.extend(self._load_history_messages(tenant_id))
        messages.append({"role": "user", "content": user_message})

        collected_all: list[str] = []

        # OpenAI tool-calling is a two-step dance: model emits tool_calls (often
        # with no text), client executes them, client sends the results back in
        # a fresh completion so the model can write the natural-language reply.
        # We loop up to 3 rounds to let multi-tool plans complete, then stop.
        for _ in range(3):
            try:
                stream = await client.chat.completions.create(
                    model=deployment,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    stream=True,
                )
            except Exception as exc:
                yield ChatEvent(
                    "error", {"code": "openai_unavailable", "message": str(exc)}
                )
                return

            round_text: list[str] = []
            # Streamed tool_calls arrive as fragments keyed by `index`; name is
            # sent once, arguments arrive as a token-by-token JSON string. We
            # reassemble into a complete list before execution.
            tool_acc: dict[int, dict[str, Any]] = {}

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                if getattr(delta, "content", None):
                    round_text.append(delta.content)
                    yield ChatEvent(
                        "turn.delta",
                        {"turn_id": turn_id, "delta": delta.content},
                    )
                tcs = getattr(delta, "tool_calls", None)
                if tcs:
                    for tc in tcs:
                        idx = getattr(tc, "index", 0) or 0
                        slot = tool_acc.setdefault(
                            idx, {"id": None, "name": None, "arguments": ""}
                        )
                        if getattr(tc, "id", None):
                            slot["id"] = tc.id
                        fn = getattr(tc, "function", None)
                        if fn is not None:
                            if getattr(fn, "name", None):
                                slot["name"] = fn.name
                            if getattr(fn, "arguments", None):
                                slot["arguments"] += fn.arguments

            text_this_round = "".join(round_text)
            collected_all.append(text_this_round)

            if not tool_acc:
                break  # model finished with a natural-language reply.

            assembled_calls = [
                {
                    "id": slot["id"] or f"call_{idx}",
                    "type": "function",
                    "function": {
                        "name": slot["name"] or "",
                        "arguments": slot["arguments"] or "{}",
                    },
                }
                for idx, slot in sorted(tool_acc.items())
            ]
            messages.append(
                {
                    "role": "assistant",
                    "content": text_this_round or None,
                    "tool_calls": assembled_calls,
                }
            )

            for call in assembled_calls:
                name = call["function"]["name"]
                tool_call_id = call["id"]
                try:
                    args = json.loads(call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    args = {}

                yield ChatEvent(
                    "tool.call",
                    {
                        "turn_id": turn_id,
                        "tool_call_id": tool_call_id,
                        "name": name,
                        "arguments": args,
                    },
                )

                if name not in ALLOW_LIST:
                    result: dict[str, Any] = {
                        "outcome": "refused",
                        "reason": f"tool {name!r} not in allow-list",
                    }
                else:
                    try:
                        result = await self._execute_tool(
                            name=name,
                            args=args,
                            tenant_id=tenant_id,
                            simulation_id=simulation_id,
                            user_message=user_message,
                        )
                    except Exception as exc:
                        logger.exception("sim_controller_tool_failed name=%s", name)
                        result = {"outcome": "error", "error": str(exc)}

                # Surface card.scenario for the map + chat UI.
                if name == "seed_scenario" and isinstance(result.get("card"), dict):
                    yield ChatEvent("card.scenario", result["card"])
                    self._persist_turn(
                        tenant_id=tenant_id,
                        simulation_id=simulation_id,
                        role="tool",
                        content=json.dumps(result["card"], default=str),
                        tool_call_id=tool_call_id,
                    )

                yield ChatEvent(
                    "tool.result",
                    {
                        "tool_call_id": tool_call_id,
                        "outcome": result.get("outcome", "ok"),
                        "result": result,
                    },
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(result, default=str),
                    }
                )

        assistant_text = "".join(collected_all)
        self._persist_turn(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            role="assistant",
            content=assistant_text,
            model=deployment,
        )
        yield ChatEvent(
            "turn.end",
            {"turn_id": turn_id, "content_hash": _sha256(assistant_text)},
        )

    async def _execute_tool(
        self,
        *,
        name: str,
        args: dict[str, Any],
        tenant_id: str,
        simulation_id: str,
        user_message: str,
    ) -> dict[str, Any]:
        """Server-side tool dispatcher.

        Each branch returns a JSON-serialisable dict that is (a) appended as the
        `role="tool"` message for the follow-up completion and (b) streamed to
        the client as the `tool.result` payload. `seed_scenario` additionally
        returns a ``card`` key that the streaming loop surfaces as a
        `card.scenario` SSE event for the UI map.
        """
        if name == "seed_scenario":
            return await self._tool_seed_scenario(args, tenant_id, simulation_id)
        if name == "query_sub_agent":
            reply = await self._sub_agents.invoke(
                args.get("sub_agent", ""),
                args.get("question", user_message),
                tenant_id=tenant_id,
            )
            return {
                "outcome": "ok" if not reply.degraded else "error",
                "summary": reply.summary,
                "citations": reply.citations,
            }
        if name == "draft_warning_sim":
            level = str(args.get("level", "advice")).upper().replace("_", " ")
            warning = (
                "SIMULATION — DO NOT DISTRIBUTE\n"
                f"{level} — {args.get('hazard', 'hazard')} near "
                f"{args.get('location', 'area')}. {args.get('action', '')}"
            ).strip()
            return {
                "outcome": "ok",
                "warning": warning,
                "watermarked": True,
                "published": False,
            }
        if name in {"pause", "resume", "stop"}:
            return {
                "outcome": "pending_confirmation",
                "note": (
                    f"{name.title()} requested. The coordinator must confirm via "
                    "the dashboard controls — no state changed."
                ),
            }
        if name == "list_participants":
            return {
                "outcome": "ok",
                "note": "Participants are listed in the left dashboard panel.",
            }
        if name == "summarise_state":
            return {
                "outcome": "ok",
                "note": "Current state is visible in the Signals & Resources panel.",
            }
        return {"outcome": "error", "error": f"unhandled tool {name}"}

    async def _tool_seed_scenario(
        self,
        args: dict[str, Any],
        tenant_id: str,
        simulation_id: str,
    ) -> dict[str, Any]:
        hazard = str(args.get("hazard", "bushfire"))
        location_name = str(args.get("location_name") or "unspecified").strip()
        start_at = str(args.get("start_at") or datetime.now(UTC).isoformat())
        aws_level = str(args.get("aws_default_level", "watch_and_act"))
        parameters = args.get("parameters") or {}

        coords = _geocode_au(location_name)
        card: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "simulation_id": simulation_id,
            "hazard": hazard,
            "location": {
                "name": location_name,
                "lng": coords[0] if coords else None,
                "lat": coords[1] if coords else None,
                "zoom": coords[2] if coords else 6,
                "resolver": "builtin" if coords else "unresolved",
            },
            "start_at": start_at,
            "aws_default_level": aws_level,
            "parameters": parameters,
            "confirmed": True,
            "created_at": datetime.now(UTC).isoformat(),
        }

        # Schedule best-effort synthetic ingestion so the Signals meter ticks
        # up during the exercise. Non-blocking; errors are swallowed.
        try:
            import asyncio

            asyncio.create_task(_ingest_synthetic_signals(tenant_id))
        except Exception:
            logger.exception("sim_synthetic_ingestion_schedule_failed")

        return {
            "outcome": "ok",
            "card": card,
            "ingestion_started": True,
        }


# ─── Geocoding + synthetic ingestion helpers ──────────────────────────────────

# Common Australian locations used by exercise scenarios. (lng, lat, zoom).
# Falls through to partial-match; unresolved locations return None so the model
# can ask for clarification or default to the tenant's jurisdiction centroid.
_AU_GEOCODE: dict[str, tuple[float, float, int]] = {
    "katoomba": (150.3118, -33.7118, 10),
    "blue mountains": (150.3118, -33.7118, 10),
    "lithgow": (150.1572, -33.4816, 10),
    "sydney": (151.2093, -33.8688, 9),
    "newcastle": (151.7817, -32.9283, 10),
    "wollongong": (150.8931, -34.4278, 10),
    "gosford": (151.3437, -33.4269, 10),
    "dubbo": (148.6011, -32.2569, 10),
    "melbourne": (144.9631, -37.8136, 9),
    "bendigo": (144.2794, -36.7570, 10),
    "ballarat": (143.8503, -37.5622, 10),
    "geelong": (144.3617, -38.1499, 10),
    "brisbane": (153.0251, -27.4698, 9),
    "cairns": (145.7781, -16.9203, 10),
    "townsville": (146.8169, -19.2590, 10),
    "gold coast": (153.4000, -28.0167, 10),
    "perth": (115.8605, -31.9505, 9),
    "adelaide": (138.6007, -34.9285, 9),
    "hobart": (147.3272, -42.8821, 10),
    "canberra": (149.1300, -35.2809, 10),
    "darwin": (130.8456, -12.4634, 10),
    "alice springs": (133.8807, -23.6980, 10),
}


def _geocode_au(location_name: str) -> tuple[float, float, int] | None:
    key = location_name.lower().strip()
    if not key:
        return None
    if key in _AU_GEOCODE:
        return _AU_GEOCODE[key]
    for k, v in _AU_GEOCODE.items():
        if k in key or key in k:
            return v
    return None


async def _ingest_synthetic_signals(tenant_id: str) -> None:
    """Bump the simulation's signal counter a few times so the left-panel
    meter animates during the exercise. Best-effort: routes that use a
    different repository instance will simply see no increment.
    """
    import asyncio

    try:
        from app.api.routes.simulations import _repo  # shared singleton
    except Exception:
        return
    try:
        for _ in range(5):
            await asyncio.sleep(2.0)
            tenant = await _repo.get_by_tenant_id(tenant_id)
            if tenant is None or tenant.status not in ("Active", "Paused"):
                return
            tenant.resource_consumption.signal_count += 1
            await _repo.update(tenant)
    except Exception:
        logger.exception("sim_synthetic_ingestion_failed tenant=%s", tenant_id)


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

"""Simulation Controller service — orchestrates chat with tool-allow-list.

Two backends:
- **Foundry** when ``AZURE_AI_PROJECT_ENDPOINT`` (+ ``AZURE_AI_PROJECT_DEPLOYMENTS``) is set.
- **Offline deterministic** otherwise — used by tests and local dev.

Both backends emit the same SSE events defined in contracts/simulation-chat-api.md.

Spec 036 / ADR-20 hard cutover: the legacy ``AZURE_OPENAI_*`` env-var
seam and the ``LEGACY_AZURE_OPENAI=1`` rollback flag have been removed
from this controller (ADR-20 §Q-P6-03 post-cutover cleanup). Authentication
is AAD-only (FR-RAG-FM-04). When ``AZURE_SEARCH_ENDPOINT`` is set the
controller auto-constructs an ``AzureSearchRetrievalService`` so simulation
chat is grounded in the
same corpus as the live agents (FR-RAG-SIM-01..06).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ama_domain.retrieval import RetrievedChunk
from app.core.async_io import run_blocking
from app.repositories.sim_chat_history_repository import (
    SimChatHistoryRepository,
    default_history_repo,
)
from app.services.simulation.controller_tools import ALLOW_LIST, TOOL_SCHEMAS
from app.services.simulation.rate_limiter import RateLimiter, get_rate_limiter
from app.services.simulation.sub_agent_invoker import SubAgentInvoker, default_invoker

from packages.domain.src.domain.models.sim_chat_turn import SimChatTurn

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessageToolCallParam

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).with_name("controller_prompt.md")

# Rolling-window cap on prior turns replayed to the model. Each assistant
# response is ~600 chars on average, so 40 turns ≈ 24 k chars (~6 k tokens)
# — well inside gpt-5.6's 128 k context window and leaves headroom for the
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


def _build_default_retrieval_service() -> Any:
    """Auto-construct the production ``AzureSearchRetrievalService`` when wired.

    Delegates to ``common.retrieval_client.build_default_retrieval_service``
    so the simulation chat and the agents share a single construction
    site — both then carry the same Foundry-backed query embedder
    (3072-dim) that matches the corpus index.

    Returns ``None`` (disabling grounding) unless ``AZURE_SEARCH_ENDPOINT``
    is set. Production Bicep sets the env var on the API container app
    once the spec-036 cutover provisions the AI Search service. Tests
    that pre-seed the env var get the live class wired automatically;
    tests that want a stubbed retrieval service inject one via the
    constructor.
    """
    if not os.environ.get("AZURE_SEARCH_ENDPOINT"):
        return None
    try:
        # Deferred import to avoid pulling apps/agents into the api hot path
        # when the feature is disabled.
        from common.retrieval_client import build_default_retrieval_service  # noqa: PLC0415

        return build_default_retrieval_service()
    except Exception:  # noqa: BLE001
        logger.warning(
            "Failed to build AzureSearchRetrievalService; simulation chat will fall back to ungrounded mode",
            exc_info=True,
        )
        return None


class SimulationControllerService:
    def __init__(
        self,
        *,
        sub_agents: SubAgentInvoker | None = None,
        rate_limiter: RateLimiter | None = None,
        history_repo: SimChatHistoryRepository | None = None,
        event_recorder: Any = None,
        clock_service: Any = None,
        simulation_repository: Any = None,
        scenario_seeding_service: Any = None,
        retrieval_service: Any = None,
        audit_writer: Any = None,
    ) -> None:
        self._sub_agents = sub_agents or default_invoker()
        self._rl = rate_limiter or get_rate_limiter()
        self._history = history_repo or default_history_repo()
        self._event_recorder = event_recorder
        self._clock = clock_service
        self._sim_repo = simulation_repository
        self._scenario_seeding = scenario_seeding_service
        self._prompt_text = _PROMPT_PATH.read_text(encoding="utf-8")
        self._prompt_hash = hashlib.sha256(self._prompt_text.encode("utf-8")).hexdigest()
        # Spec 036 FR-RAG-SIM-01..06: optional retrieval client + audit writer.
        # Both are dependency-injected so tests can stub them; production
        # auto-constructs the retrieval client from ``AZURE_SEARCH_ENDPOINT``
        # when the caller did not inject one.
        self._retrieval = retrieval_service or _build_default_retrieval_service()
        self._audit_writer = audit_writer

    async def _current_sim_seconds(self, tenant_id: str) -> float:
        """Best-effort lookup of current simulated time for the tenant."""
        if self._clock is None or self._sim_repo is None:
            return 0.0
        try:
            tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
            if tenant is None:
                return 0.0
            return self._clock.get_current_sim_seconds(tenant)
        except Exception:  # pragma: no cover — defensive
            return 0.0

    def _maybe_record_tool_invocation(
        self,
        *,
        tenant_id: str,
        sim_seconds: float,
        tool_name: str,
        outcome: str,
        latency_ms: int = 0,
    ) -> None:
        """Best-effort — record a tool round-trip as a SimulationEvent.

        Without this the right-hand Event Log only ever shows lifecycle
        events + chat turns; tool-driven activity (sub-agent replies that
        produce coordination tasks via the Deploy quick-action, etc.) would
        appear locally then get pruned by the polling refresh because no
        durable counterpart ever lands in the ``sim-events`` container.
        """
        if self._event_recorder is None:
            return
        try:
            self._event_recorder.record_tool_invocation(
                tenant_id=tenant_id,
                sim_time=sim_seconds,
                tool_name=tool_name,
                outcome=outcome,
                latency_ms=latency_ms,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("sim_event_record_tool_invocation_failed: %s", exc)

    def _maybe_record_chat_turn(
        self,
        *,
        tenant_id: str,
        sim_seconds: float,
        turn: SimChatTurn,
        tool_calls: list[str] | None = None,
    ) -> None:
        """Best-effort — record the chat turn as a SimulationEvent for playback."""
        if self._event_recorder is None:
            return
        try:
            preview = turn.content[:200] if turn.content else ""
            self._event_recorder.record_chat_turn(
                tenant_id=tenant_id,
                sim_time=sim_seconds,
                turn_sequence=turn.sequence,
                role=turn.role,
                message_preview=preview,
                tool_calls=tool_calls,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("sim_event_record_chat_turn_failed: %s", exc)

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
        sim_seconds: float = 0.0,
        tool_calls: list[str] | None = None,
    ) -> SimChatTurn | None:
        """Append one turn to the tenant's chat history. Best-effort: persistence
        failures must never crash the SSE stream. Also records the turn as a
        simulation event (for after-action playback) when a recorder is wired up.
        """
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
            persisted = self._history.append_turn(turn)
            self._maybe_record_chat_turn(
                tenant_id=tenant_id,
                sim_seconds=sim_seconds,
                turn=persisted,
                tool_calls=tool_calls,
            )
            return persisted
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("sim_chat_history_persist_failed: %s", exc)
            return None

    async def _persist_turn_async(self, **kwargs: Any) -> SimChatTurn | None:
        """Offloaded variant — chat history writes must not stall the SSE loop."""
        return await run_blocking(self._persist_turn, **kwargs)

    async def _maybe_record_tool_invocation_async(self, **kwargs: Any) -> None:
        await run_blocking(self._maybe_record_tool_invocation, **kwargs)

    def _load_history_messages(self, tenant_id: str) -> list[ChatCompletionMessageParam]:
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
        out: list[ChatCompletionMessageParam] = []
        for t in turns:
            if t.role in ("user", "assistant", "system"):
                out.append({"role": t.role, "content": t.content})
        return out

    async def _load_history_messages_async(self, tenant_id: str) -> list[ChatCompletionMessageParam]:
        """Offloaded variant — history replay reads must not stall the SSE loop."""
        return await run_blocking(self._load_history_messages, tenant_id)

    def _resolve_simulation_deployment(self) -> str | None:
        """Resolve the simulation deployment name from the Foundry env vars.

        Spec 036 / ADR-20 hard cutover: the controller reads
        ``AZURE_AI_PROJECT_DEPLOYMENTS`` (CSV of
        ``modelId@version=deploymentName``) and matches the simulation /
        reasoning model key. Returns ``None`` when the deployment cannot be
        resolved — the caller surfaces ``openai_unavailable`` rather than
        falling back to a legacy env var.

        Resolution order (post tier-env-var fix):
          1. ``AZURE_AI_SIMULATION_DEPLOYMENT`` — explicit per-tier
             deployment name set by Bicep. Wins because the CSV map can
             collapse multiple tiers onto the same model key when several
             deployments share ``<modelName>@<version>``.
          2. CSV lookup by ``AZURE_AI_SIMULATION_MODEL_KEY`` (or the
             reasoning key) — first-write-wins per the parser.
        """
        explicit = os.environ.get("AZURE_AI_SIMULATION_DEPLOYMENT")
        if explicit:
            return explicit

        csv = os.environ.get("AZURE_AI_PROJECT_DEPLOYMENTS", "")
        model_key = (
            os.environ.get("AZURE_AI_SIMULATION_MODEL_KEY")
            or os.environ.get("AZURE_AI_REASONING_MODEL_KEY")
            or "gpt-4o"
        )
        if csv:
            for entry in (e.strip() for e in csv.split(",") if e.strip()):
                if "=" not in entry:
                    continue
                key, name = entry.split("=", 1)
                if key.strip() == model_key:
                    return name.strip()
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
        if self._sim_repo is not None:
            tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
            if tenant is None:
                yield ChatEvent("error", {"code": "not_found", "message": "Simulation tenant not found."})
                return
            if tenant.status != "Active" or tenant.clock_paused:
                yield ChatEvent(
                    "error",
                    {
                        "code": "lifecycle_state_conflict",
                        "message": f"Simulation is {tenant.status.lower()}; resume it before sending chat commands.",
                    },
                )
                return
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
        await self._persist_turn_async(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            role="user",
            content=user_message,
            actor_oid=user_oid,
        )

        if refusal is not None:
            yield ChatEvent("turn.delta", {"turn_id": turn_id, "delta": refusal})
            await self._persist_turn_async(
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

        backend = (mode or os.getenv("SIM_CONTROLLER_MODE") or "").lower()
        if not backend:
            backend = "foundry" if os.getenv("AZURE_AI_PROJECT_ENDPOINT") else "offline"

        if backend in ("foundry", "azure"):
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
        # RAG-OPTOUT [FR-RAG-NS-06]: scripted-scenario / offline streaming path; canned responses by intent — no LLM call to ground. ADR: docs/decisions/036-foundry-rag-grounding/06-rag-optout-scenario-execution.md  # noqa: E501
        # Audit records: call_kind=inference, rag_used=false, rag_optout_reason="scenario-execution".
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
            reply = await self._sub_agents.invoke(intent["sub_agent"], user_message, tenant_id=tenant_id)
            text = f"{intent['sub_agent'].title()}: {reply.summary}" + (" (degraded)" if reply.degraded else "")
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
            await self._maybe_record_tool_invocation_async(
                tenant_id=tenant_id,
                sim_seconds=await self._current_sim_seconds(tenant_id),
                tool_name=f"query_sub_agent:{intent['sub_agent']}",
                outcome="ok" if not reply.degraded else "error",
            )
            # Audit trail: persist the tool round-trip as a tool-role turn so
            # operators can reconstruct which sub-agent informed the response.
            await self._persist_turn_async(
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
        await self._persist_turn_async(
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
        # Spec 036 / ADR-20 hard cutover: the simulation controller backs onto
        # Microsoft Foundry exclusively. The endpoint and deployment are
        # resolved from ``AZURE_AI_PROJECT_*`` env vars; the
        # ``controller_prompt.md`` system prompt and the ``TOOL_SCHEMAS``
        # tool-calling 3-round loop are preserved verbatim (OOS-6, spec 024).
        #
        # Authentication is AAD-only (FR-RAG-FM-04) — managed identity in
        # Container Apps, ``az login`` locally. API-key auth is forbidden;
        # the legacy ``AZURE_OPENAI_API_KEY`` path was removed when the
        # cutover completed.
        try:
            from openai import AsyncAzureOpenAI  # AMA-FM04: allow Foundry transport (FR-RAG-FM-01)  # noqa: PLC0415
        except Exception:
            yield ChatEvent(
                "error",
                {"code": "openai_sdk_missing", "message": "openai SDK not installed."},
            )
            return

        endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")

        deployment = self._resolve_simulation_deployment()
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        if not (endpoint and deployment):
            missing = (
                "AZURE_AI_PROJECT_ENDPOINT"
                if not endpoint
                else "AZURE_AI_PROJECT_DEPLOYMENTS (or AZURE_AI_SIMULATION_MODEL_KEY)"
            )
            yield ChatEvent(
                "error",
                {
                    "code": "openai_unavailable",
                    "message": f"Foundry chat endpoint is not fully configured (missing {missing}).",
                },
            )
            return

        client_kwargs: dict[str, Any] = {
            "azure_endpoint": endpoint,
            "api_version": api_version,
        }
        # AAD-only auth (FR-RAG-FM-04). Managed identity in Container Apps;
        # az/azd login locally. The token scope is the cognitive-services
        # audience that Foundry accepts.
        try:
            from azure.identity import (
                DefaultAzureCredential,
                get_bearer_token_provider,
            )

            credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
            client_kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
        except Exception as exc:
            yield ChatEvent(
                "error",
                {
                    "code": "openai_client_init_failed",
                    "message": (
                        f"Foundry credential unavailable. Ensure managed identity or az login is configured: {exc}"
                    ),
                },
            )
            return
        try:
            client = AsyncAzureOpenAI(**client_kwargs)
        except Exception as exc:
            yield ChatEvent("error", {"code": "openai_client_init_failed", "message": str(exc)})
            return

        # Spec 036 FR-RAG-CV-03: data-minimisation gateway for non-AU
        # deployments. AU deployments bypass redaction (data residency holds);
        # non-AU deployments redact PII / deny PSPF-marked / sensitive
        # operational content **before** the message hits Foundry.
        deployment_region = os.environ.get("AZURE_AI_PROJECT_REGION", "australiaeast").lower()
        forwarded_message = user_message
        try:
            from common.model_gateway import apply as gateway_apply
        except Exception:
            gateway_apply = None
        if gateway_apply is not None:
            decision = gateway_apply(text=user_message, deployment_region=deployment_region)
            if decision.gateway_decision == "deny":
                yield ChatEvent(
                    "error",
                    {
                        "code": "gateway_denied",
                        "message": f"Data-minimisation gateway denied the request: {decision.reason}",
                    },
                )
                return
            forwarded_message = decision.transmitted_text

        # Replay the rolling window of prior turns so the model has conversational
        # memory across requests. Ordering is [system, ...prior turns (oldest
        # first), current user message].
        messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": self._prompt_text}]
        messages.extend(await self._load_history_messages_async(tenant_id))
        messages.append({"role": "user", "content": forwarded_message})

        # Spec 036 FR-RAG-SIM-01: retrieve grounding chunks BEFORE the first
        # LLM call. The system prompt + tool schemas are NOT modified (OOS-6);
        # we only enrich the user message with a "Grounding context" preamble
        # when retrieval returns non-empty results. Empty results emit a
        # ``citations: []`` SSE event with the operator-verification note
        # (FR-RAG-SIM-03).
        retrieved_chunks: list[RetrievedChunk] = []
        retrieval_result: Any = None
        sim_corpus_build_sha: str | None = None
        sim_embedding_model_id: str | None = None
        sim_retrieval_index_name: str | None = None
        if self._retrieval is not None:
            try:
                from ama_domain import (
                    RetrievalRequest,
                )

                # Best-effort jurisdiction inference: simulation runs are tenant-
                # scoped; the retrieval client expands to ∪ {national, aidr}
                # server-side (FR-RAG-AG-04). Default to ``national`` so a
                # tenant without a locked jurisdiction still gets the AIDR
                # corpus on every turn.
                req = RetrievalRequest(
                    agent_name="SimulationController",
                    jurisdictions=[os.environ.get("AMA_SIM_JURISDICTION", "national")],
                    hazard_type=os.environ.get("AMA_SIM_HAZARD_TYPE", "general"),
                    query_text=forwarded_message[:4000],
                    top_k=5,
                    tenant_id=tenant_id,
                    correlation_id=turn_id,
                )
                retrieval_result = await self._retrieval.retrieve(req)
                retrieved_chunks = list(getattr(retrieval_result, "chunks", []) or [])
                sim_corpus_build_sha = getattr(retrieval_result, "corpus_build_sha", None)
                sim_embedding_model_id = getattr(retrieval_result, "embedding_model_id", None)
                # F-A7 / ADR-16 — propagate the pinned concrete index name
                # into the audit shape (NOT the alias). Falls back to
                # ``alias_active_index`` for legacy retrieval clients that
                # haven't yet been retrofit with alias-pinning.
                sim_retrieval_index_name = getattr(retrieval_result, "retrieval_index_name", None) or getattr(
                    retrieval_result, "alias_active_index", None
                )
            except Exception as exc:  # noqa: BLE001 — retrieval failure must not abort the turn
                logger.warning("sim_retrieval_failed turn_id=%s err=%s", turn_id, exc)
                retrieval_result = None

        # If we have grounding chunks, prepend a short context block to the
        # user message. This is intentionally minimal — it does NOT reshape
        # the controller_prompt.md system prompt (OOS-6).
        if retrieved_chunks:
            context_lines = [
                "Grounding context (cite by jurisdiction/topic/page; do not invent sources):",
            ]
            for c in retrieved_chunks[:5]:
                context_lines.append(
                    f"- [{c.jurisdiction.value}/{c.topic}#p{c.page}] {(c.text or c.summary or '')[:280]}"
                )
            messages[-1]["content"] = "\n".join(context_lines) + "\n\n---\n\n" + forwarded_message

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
                # Distinguish Azure content-filter blocks (ResponsibleAIPolicyViolation)
                # from generic availability failures. The UI shows different friendly
                # copy per code; the full technical detail is logged server-side and
                # only surfaced to the client in local/development environments.
                exc_str = str(exc)
                if "content_filter" in exc_str or "ResponsibleAIPolicyViolation" in exc_str:
                    code = "content_filter"
                else:
                    code = "openai_unavailable"
                logger.exception(
                    "sim_controller_openai_error code=%s deployment=%s",
                    code,
                    deployment,
                )
                yield ChatEvent("error", {"code": code, "message": exc_str})
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
                content = delta.content
                if isinstance(content, str) and content:
                    round_text.append(content)
                    yield ChatEvent(
                        "turn.delta",
                        {"turn_id": turn_id, "delta": content},
                    )
                tcs = getattr(delta, "tool_calls", None)
                if tcs:
                    for tc in tcs:
                        idx = getattr(tc, "index", 0) or 0
                        slot = tool_acc.setdefault(idx, {"id": None, "name": None, "arguments": ""})
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

            assembled_calls: list[ChatCompletionMessageToolCallParam] = [
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
                    await self._persist_turn_async(
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
                tool_label = name
                if name == "query_sub_agent" and isinstance(args.get("sub_agent"), str):
                    tool_label = f"query_sub_agent:{args['sub_agent']}"
                await self._maybe_record_tool_invocation_async(
                    tenant_id=tenant_id,
                    sim_seconds=await self._current_sim_seconds(tenant_id),
                    tool_name=tool_label,
                    outcome=str(result.get("outcome", "ok")),
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(result, default=str),
                    }
                )

        assistant_text = "".join(collected_all)
        await self._persist_turn_async(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            role="assistant",
            content=assistant_text,
            model=deployment,
        )

        # Spec 036 FR-RAG-SIM-02 / FR-RAG-SIM-03: emit a ``citation`` SSE
        # event right before ``turn.end``. We synthesise lightweight Citation
        # dicts directly from the retrieved chunks — the simulation channel
        # currently surfaces metadata only; full-text licensing is gated on
        # the recommendation-card path (T086) where the licence_mode is
        # already enforced.
        try:
            from app.services.simulation.citation_sse import (  # noqa: PLC0415
                format_empty_citations_event,
            )

            if self._retrieval is not None and not retrieved_chunks:
                yield ChatEvent(
                    "citation",
                    json.loads(
                        format_empty_citations_event(turn_id=turn_id)
                        .removeprefix("event: citation\n")
                        .removeprefix("data: ")
                        .strip()
                    ),
                )
            elif retrieved_chunks:
                citation_dicts = []
                for c in retrieved_chunks[:5]:
                    licence = c.licence_mode.value
                    cit = {
                        "jurisdiction": c.jurisdiction.value,
                        "topic": c.topic,
                        "page": c.page,
                        "source_url": c.source_url,
                        "rendered_url": c.rendered_url,
                        "sha256_of_chunk": c.sha256_of_chunk,
                        "licence_mode": licence,
                        "confidence": c.confidence,
                    }
                    if licence == "full-text":
                        cit["snippet"] = (c.text or "")[:300]
                    citation_dicts.append(cit)
                yield ChatEvent(
                    "citation",
                    {"turn_id": turn_id, "citations": citation_dicts},
                )

                # FR-RAG-SIM-04 / R-13: write the extended audit record. The
                # writer is best-effort — failure must never break the SSE
                # stream.
                if self._audit_writer is not None:
                    try:
                        from common.audit import (  # noqa: PLC0415
                            make_inference_record,
                        )

                        prompt_sha = hashlib.sha256(forwarded_message.encode("utf-8")).hexdigest()
                        record = make_inference_record(
                            agent_name="SimulationController",
                            prompt_sha=prompt_sha,
                            model_id=deployment,
                            model_version=os.environ.get("AZURE_AI_PROJECT_MODEL_VERSION", "unknown"),
                            deployment_alias=deployment,
                            output_text_hash=_sha256(assistant_text),
                            output_tokens=len(assistant_text.split()),
                            tenant_id=tenant_id,
                            correlation_id=turn_id,
                            rag_used=True,
                            embedding_model_id=sim_embedding_model_id or "unknown",
                            corpus_build_sha=sim_corpus_build_sha or "unknown",
                            retrieved_chunks=[
                                {
                                    "chunk_id": c.chunk_id,
                                    "sha256_of_chunk": c.sha256_of_chunk,
                                    "jurisdiction": c.jurisdiction.value,
                                    "topic": c.topic,
                                    "page": getattr(c, "page", 0),
                                    "licence_mode": c.licence_mode.value,
                                    "confidence": c.confidence,
                                }
                                for c in retrieved_chunks
                            ],
                            citations=citation_dicts,
                            retrieval_index_name=sim_retrieval_index_name,
                        )
                        await self._audit_writer.write(record)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("sim_audit_write_failed turn_id=%s err=%s", turn_id, exc)
        except Exception as exc:  # noqa: BLE001 — never break the SSE stream
            logger.warning("sim_citation_emit_failed turn_id=%s err=%s", turn_id, exc)

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

        if self._scenario_seeding is None:
            return {
                "outcome": "error",
                "card": card,
                "ingestion_started": False,
                "error": "Scenario seeding service is unavailable",
            }

        seed_result = await self._scenario_seeding.seed_for_hazard(tenant_id, hazard)

        return {
            "outcome": "ok",
            "card": card,
            "ingestion_started": True,
            **seed_result,
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

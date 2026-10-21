"""MAF Agent factory + base wrapper for the five operational agents (T026–T035).

Every agent module in this package follows the same pattern:

1. Load its YAML definition (``<agent>.yaml``) via ``load_agent_definition(...)``.
2. Build a MAF ``agent_framework.Agent`` via ``build_agent(...)`` with the three
   foundational middleware bound (content_safety, audit, otel) and the
   ``OpenAIChatClient`` from ``maf_runtime.chat_client``.
3. Expose ``async run(input) -> <pydantic_model>`` that:
   - In ``legacy`` mode: delegates to the existing pipeline class (no MAF call).
   - In ``maf`` mode: invokes the MAF Agent with the input (returns the model).
   - In ``shadow`` mode: runs both, returns legacy output, captures both for the
     equivalence harness's live monitor.

This factory keeps each per-agent module short and consistent; it also makes the
"sixth agent" worked example (SC-010) trivially demonstrable.
"""

from __future__ import annotations

import logging
import os
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml
from agent_framework import Agent
from pydantic import BaseModel

from ..chat_client import build_azure_openai_chat_client
from ..feature_flags import AgentMode, get_agent_mode
from ..middleware import (
    AuditMiddleware,
    ContentSafetyMiddleware,
    OtelMiddleware,
)

logger = logging.getLogger(__name__)


_DEFINITIONS_DIR = Path(__file__).resolve().parent


def load_agent_definition(name: str) -> dict[str, Any]:
    """Load <agent>.yaml from this directory and validate it against the contract schema shape."""
    yaml_path = _DEFINITIONS_DIR / f"{name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Agent definition not found: {yaml_path}")
    with yaml_path.open("r", encoding="utf-8") as f:
        definition = yaml.safe_load(f) or {}
    # Minimal schema-shape check — full JSON-Schema validation happens in tests.
    required = ("name", "display_name", "prompt", "model_tier", "output_schema", "middleware_bindings")
    missing = [k for k in required if k not in definition]
    if missing:
        raise ValueError(f"{yaml_path} is missing required fields: {missing}")
    if definition["name"] != name:
        raise ValueError(f"{yaml_path}: 'name' field is {definition['name']!r} but file is named {name}.yaml")
    bindings = set(definition.get("middleware_bindings", []))
    if "content_safety" not in bindings or "audit" not in bindings:
        raise ValueError(
            f"{yaml_path}: middleware_bindings MUST include both 'content_safety' and 'audit' "
            "(FR-013, FR-014 — refusal to omit)"
        )
    return definition


def _resolve_pydantic_class(dotted_path: str) -> type[BaseModel]:
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValueError(f"output_schema must be a dotted module path: got {dotted_path!r}")
    module = import_module(module_path)
    cls = getattr(module, class_name, None)
    if cls is None:
        raise AttributeError(f"output_schema {dotted_path!r}: class {class_name!r} not found")
    if not isinstance(cls, type) or not issubclass(cls, BaseModel):
        raise TypeError(f"output_schema {dotted_path!r}: must be a Pydantic BaseModel subclass")
    return cls


def build_middleware_chain(*, agent_name: str, model_tier: str) -> list[Any]:
    """Return the canonical ordered middleware chain (content_safety → audit → otel)."""
    return [
        ContentSafetyMiddleware(),
        AuditMiddleware(agent_name=agent_name, model_tier=model_tier),
        OtelMiddleware(agent_name=agent_name),
    ]


def build_agent(definition: dict[str, Any]) -> Agent:
    """Construct a MAF ``Agent`` instance from a parsed YAML definition.

    The chat client is constructed lazily — if ``AZURE_OPENAI_ENDPOINT`` is not
    set, this raises ``ValueError`` per ``maf_runtime.chat_client`` (the runtime
    must fail closed rather than build a client without a real endpoint).
    """
    name: str = definition["name"]
    instructions: str = definition["prompt"]
    model_tier: str = definition["model_tier"]
    middleware = build_middleware_chain(agent_name=name, model_tier=model_tier)
    chat_client = build_azure_openai_chat_client(model_tier=model_tier)
    agent = Agent(
        client=chat_client,
        instructions=instructions,
        name=name,
        description=definition.get("display_name", name),
        middleware=middleware,
    )
    logger.info(
        "maf_agent_built",
        extra={"agent_name": name, "model_tier": model_tier, "middleware_count": len(middleware)},
    )
    return agent


def _maybe_default_retrieval_service() -> Any:
    """Return a production retrieval service when the env vars indicate live,
    or ``None`` otherwise.

    Imported lazily inside the helper so unit tests that don't touch
    grounding never trigger an ``apps/agents/common`` import (keeps the
    test path hermetic). Failures are swallowed and ``None`` returned —
    the per-agent grounding flag will then resolve to ``False`` and the
    legacy non-grounded path runs unchanged (R-12).
    """
    if not os.environ.get("AZURE_SEARCH_ENDPOINT"):
        return None
    try:
        from common.retrieval_client import build_default_retrieval_service  # noqa: PLC0415

        return build_default_retrieval_service()
    except Exception:  # noqa: BLE001
        logger.warning(
            "default_retrieval_service_unavailable; agent grounding disabled",
            exc_info=True,
        )
        return None


class MafAgentFacade:
    """Thin facade that selects between legacy pipeline, MAF Agent, or shadow mode.

    Each named agent module subclasses this with a per-agent legacy-pipeline
    delegate. In production cutover, the FEATURE_MAF_RUNTIME_<AGENT> env var
    flips between ``legacy`` (default), ``maf``, and ``shadow``.

    Spec 036 — optional grounding seam:
      ``retrieval_service``, ``audit_writer``, and ``citation_filter`` are
      dependency-injected. When the per-agent flag
      ``FEATURE_FOUNDRY_RAG_<AGENT_UPPER>=1`` is set AND
      ``AZURE_AI_PROJECT_ENDPOINT`` is configured, ``retrieve()`` returns a
      grounded ``RetrievalResult``; otherwise it returns ``None`` and the
      agent falls back to legacy behaviour. This honours the canary plan
      (R-12) — code is always present, but the path activates only when the
      operator flips the flag.
    """

    name: str = ""

    # Canonical agent name used in audit records / RetrievalRequest. Defaults
    # to ``<self.name>.title().replace("_", "") + "Agent"`` so a YAML name of
    # ``risk_assessment`` becomes ``RiskAssessmentAgent``.
    grounded_agent_name: str = ""

    def __init__(
        self,
        *,
        retrieval_service: Any = None,
        audit_writer: Any = None,
    ) -> None:
        self._definition = load_agent_definition(self.name)
        self._output_schema = _resolve_pydantic_class(self._definition["output_schema"])
        self._maf_agent: Agent | None = None  # built lazily on first MAF call
        # Spec 036 — when the caller didn't inject a retrieval service AND
        # the runtime env vars indicate the grounding plane is live, auto-
        # construct the production ``AzureSearchRetrievalService`` so the
        # per-agent ``FEATURE_FOUNDRY_RAG_<AGENT>=1`` flag activates the
        # grounded path in production without bespoke wiring per agent
        # module. Failures are non-fatal — ``is_grounded_enabled()`` will
        # return ``False`` and the agent falls back to legacy behaviour
        # (R-12 canary plan).
        if retrieval_service is None:
            retrieval_service = _maybe_default_retrieval_service()
        self._retrieval = retrieval_service
        self._audit_writer = audit_writer

    @property
    def grounded_name(self) -> str:
        if self.grounded_agent_name:
            return self.grounded_agent_name
        camel = "".join(part.title() for part in self.name.split("_"))
        return f"{camel}Agent"

    def is_grounded_enabled(self) -> bool:
        """Return True iff this agent's Foundry-RAG flag is set AND retrieval is wired."""
        flag_var = f"FEATURE_FOUNDRY_RAG_{self.name.upper()}"
        flag = os.environ.get(flag_var, "").strip().lower() in ("1", "true", "yes", "on")
        endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
        return bool(flag and endpoint and self._retrieval is not None)

    async def retrieve(
        self,
        *,
        jurisdictions: list[str],
        query_text: str,
        hazard_type: str | None = None,
        tenant_id: str = "default",
        correlation_id: str = "",
        top_k: int = 5,
    ) -> Any:
        """Issue a retrieval request scoped to this agent.

        Returns ``None`` when the per-agent flag is off (legacy fall-through);
        a ``RetrievalResult`` otherwise. The grounded-fact filter and the
        audit writer are the caller's responsibility — keeping the seam
        narrow lets each agent compose retrieval into its existing prompt
        construction without dictating shape.
        """
        if not self.is_grounded_enabled():
            return None
        try:
            from ama_domain import RetrievalRequest
        except ImportError:
            logger.warning("ama_domain not importable; retrieval disabled")
            return None
        req = RetrievalRequest(
            agent_name=self.grounded_name,
            jurisdictions=jurisdictions,
            hazard_type=hazard_type or "general",
            query_text=query_text,
            top_k=top_k,
            tenant_id=tenant_id,
            correlation_id=correlation_id or "unknown",
        )
        try:
            return await self._retrieval.retrieve(req)
        except Exception as exc:  # noqa: BLE001 — retrieval must never crash the agent
            logger.warning("agent_retrieval_failed agent=%s err=%s", self.grounded_name, exc)
            return None

    @property
    def definition(self) -> dict[str, Any]:
        return self._definition

    @property
    def output_schema(self) -> type[BaseModel]:
        return self._output_schema

    def _ensure_maf_agent(self) -> Agent:
        if self._maf_agent is None:
            self._maf_agent = build_agent(self._definition)
        return self._maf_agent

    def _mode(self) -> AgentMode:
        try:
            return get_agent_mode(self.name)
        except ValueError:
            logger.warning("Invalid mode env var for agent %s; defaulting to legacy", self.name)
            return "legacy"

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        """Per-agent override: invoke the existing pipeline. Returns the output_schema model."""
        raise NotImplementedError(f"{type(self).__name__}.run_legacy must be overridden")

    async def run_maf(self, input_payload: Any) -> BaseModel:
        """Invoke the MAF Agent with input. Default impl serialises input to text + parses output JSON."""
        agent = self._ensure_maf_agent()
        # Coerce input into a single user message body.
        if hasattr(input_payload, "model_dump_json"):
            body = input_payload.model_dump_json()
        elif isinstance(input_payload, dict | list):
            import json

            body = json.dumps(input_payload, sort_keys=True)
        else:
            body = str(input_payload)
        response = await agent.run(body)
        text = getattr(response, "text", None) or str(response)
        return self._parse_response(text)

    def _parse_response(self, text: str) -> BaseModel:
        """Parse an LLM text response into the agent's output_schema. Override per agent if needed."""
        import json

        try:
            payload = json.loads(text)
        except Exception:
            payload = {"raw_text": text}
        return self._output_schema.model_validate(payload)

    async def run(self, input_payload: Any) -> BaseModel:
        """Public entry point. Honours FEATURE_MAF_RUNTIME_<AGENT> env var."""
        mode = self._mode()
        if mode == "legacy":
            return await self.run_legacy(input_payload)
        if mode == "maf":
            return await self.run_maf(input_payload)
        # shadow: run MAF in background; return legacy result.
        legacy_result = await self.run_legacy(input_payload)
        try:
            maf_result = await self.run_maf(input_payload)
            self._record_shadow_pair(input_payload, legacy_result, maf_result)
        except Exception:  # noqa: BLE001 - shadow must never break production
            logger.exception("shadow_maf_run_failed agent=%s; legacy result returned", self.name)
        return legacy_result

    def _record_shadow_pair(self, input_payload: Any, legacy: BaseModel, maf: BaseModel) -> None:
        """Append a (legacy, maf) pair to the live equivalence-monitor sink.

        Default impl: writes a JSONL line under ``apps/agents/maf_runtime/equivalence/reports/shadow/``.
        Production deployments may swap this for an Application Insights custom event sink.
        """
        try:
            import json
            import time

            sink_dir = os.environ.get("MAF_SHADOW_SINK_DIR")
            sink = Path(sink_dir) if sink_dir else _DEFINITIONS_DIR.parent / "equivalence" / "reports" / "shadow"
            sink.mkdir(parents=True, exist_ok=True)
            line = {
                "ts": time.time(),
                "agent": self.name,
                "input": _to_jsonable(input_payload),
                "legacy": _to_jsonable(legacy),
                "maf": _to_jsonable(maf),
            }
            with (sink / f"{self.name}.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(line) + "\n")
        except Exception:  # noqa: BLE001
            logger.debug("shadow sink write failed", exc_info=True)


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, dict | list | str | int | float | bool):
        return value
    return repr(value)


__all__ = [
    "MafAgentFacade",
    "build_agent",
    "build_middleware_chain",
    "load_agent_definition",
]

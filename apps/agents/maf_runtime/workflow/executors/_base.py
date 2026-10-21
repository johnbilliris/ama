"""Shared executor base for the five MAF workflow executors (T042, T042b, T042c).

Centralises three concerns that every per-agent executor needs:

1. ``validate_output(...)`` (T042b, FR-003 + FR-011b edge case "agent's output schema changes"):
   deserialise the agent's output through the Pydantic class declared by
   ``agent_definition.output_schema``; on ``ValidationError`` raise
   ``OutputSchemaMismatchError`` from the canonical errors module — the workflow
   then transitions the run to ``NeedsOperatorDecision``.

2. ``with_retry_budget(...)`` (T042c, FR-012):
   bounded-attempt + bounded-elapsed retry decorator. Defaults to 3 attempts
   and 30 seconds total elapsed per step; configurable via
   ``FEATURE_MAF_RUNTIME_RETRY_*`` env vars (T015). Per-error-class retry policy
   uses the ``RETRYABLE_ERRORS`` / ``NON_RETRYABLE_ERRORS`` sets from errors.py.

3. ``BaseAgentExecutor`` — the per-agent executor superclass. Each concrete
   executor (``MonitoringExecutor``, ``RiskExecutor``, etc.) inherits from this
   and overrides ``invoke_agent(...)``.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, ValidationError

from ...errors import (
    NON_RETRYABLE_ERRORS,
    RETRYABLE_ERRORS,
    MafRuntimeError,
    OutputSchemaMismatchError,
)
from ...feature_flags import (
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_TOTAL_SECONDS,
    AgentMode,
    get_agent_mode,
    get_retry_attempts,
    get_retry_total_seconds,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def validate_output(
    output_schema: type[BaseModel],
    output: Any,
    *,
    correlation_id: str,
    run_id: str | None = None,
) -> BaseModel:
    """Deserialise *output* through *output_schema* (FR-003, FR-011b edge case).

    Raises ``OutputSchemaMismatchError`` (NON-RETRYABLE) on Pydantic validation
    failure. The caller (workflow runtime) MUST transition the run to
    ``NeedsOperatorDecision`` rather than dropping the failure.
    """
    if isinstance(output, output_schema):
        return output
    try:
        if isinstance(output, dict):
            return output_schema.model_validate(output)
        if isinstance(output, str):
            return output_schema.model_validate_json(output)
        return output_schema.model_validate(output)
    except ValidationError as exc:
        offending_fields = sorted({err["loc"][0] for err in exc.errors() if err.get("loc")})
        raise OutputSchemaMismatchError(
            f"Agent output failed validation against {output_schema.__name__}: fields={offending_fields}",
            correlation_id=correlation_id,
            run_id=run_id,
            details={
                "output_schema": output_schema.__name__,
                "offending_fields": offending_fields,
                "raw_errors": exc.errors()[:5],
            },
        ) from exc


async def with_retry_budget(  # noqa: UP047 - PEP-695 type-params clash with async semantics here
    func: Callable[[], Awaitable[T]],
    *,
    correlation_id: str,
    run_id: str | None = None,
    max_attempts: int | None = None,
    total_seconds: float | None = None,
    sleep_seconds: float = 0.5,
) -> T:
    """Execute *func* with the FR-012 bounded retry budget.

    Retries only on classes in ``RETRYABLE_ERRORS``. Non-retryable classes
    (validation, content_filter, version_mismatch, ...) fail fast on the first
    attempt without consuming the budget.
    """
    attempts = max_attempts if max_attempts is not None else get_retry_attempts()
    total = total_seconds if total_seconds is not None else get_retry_total_seconds()
    started = time.monotonic()
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if isinstance(exc, NON_RETRYABLE_ERRORS):
                logger.info(
                    "retry_budget_skip non-retryable error %s; raising",
                    type(exc).__name__,
                )
                raise
            if not isinstance(exc, RETRYABLE_ERRORS) and not isinstance(exc, MafRuntimeError):
                # Unknown error — be conservative and DO NOT retry; raise immediately.
                logger.info(
                    "retry_budget_skip unknown error %s; raising",
                    type(exc).__name__,
                )
                raise
            elapsed = time.monotonic() - started
            remaining = total - elapsed
            if attempt >= attempts or remaining <= 0:
                logger.warning(
                    "retry_budget_exhausted attempt=%d/%d elapsed=%.1fs",
                    attempt,
                    attempts,
                    elapsed,
                )
                raise
            logger.info(
                "retry_budget_retry attempt=%d/%d elapsed=%.1fs error=%s",
                attempt,
                attempts,
                elapsed,
                type(exc).__name__,
            )
            await asyncio.sleep(min(sleep_seconds, remaining))
    # Should be unreachable — defensive.
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("with_retry_budget: no attempts made")


class BaseAgentExecutor:
    """Per-agent executor superclass.

    Concrete executors override ``invoke_agent(...)`` (and optionally
    ``run_legacy(...)`` if the legacy path is shaped differently). The dispatch
    layer reads ``feature_flags.get_agent_mode(<agent>)`` per call and selects:

      - ``legacy`` → ``run_legacy(input)``
      - ``maf``    → ``invoke_agent(input)`` then ``validate_output(...)``
      - ``shadow`` → run both, return legacy, capture pair

    On checkpoint save/restore, the workflow runtime calls
    ``on_checkpoint_save(self) -> dict`` / ``on_checkpoint_restore(self, state: dict)``.
    The default implementation captures ``self._state`` as the serialisable
    blob; subclasses MAY override to capture richer state.
    """

    agent_name: ClassVar[str] = ""
    output_schema: ClassVar[type[BaseModel] | None] = None

    def __init__(self) -> None:
        # Lazy facade — built on demand because each per-agent module imports
        # heavy legacy deps; avoid eager construction at executor-graph build time.
        self._facade: Any | None = None
        self._state: dict[str, Any] = {}

    # ----- Facade resolution ---------------------------------------------

    def _get_facade(self) -> Any:
        if self._facade is not None:
            return self._facade
        # Map agent_name → Module / Facade class. The five Phase-3 modules.
        mapping = {
            "monitoring": ("agents.monitoring_agent", "MonitoringMafAgent"),
            "risk_assessment": ("agents.risk_assessment_agent", "RiskAssessmentMafAgent"),
            "evacuation": ("agents.evacuation_agent", "EvacuationMafAgent"),
            "resource_allocation": ("agents.resource_allocation_agent", "ResourceAllocationMafAgent"),
            "communication": ("agents.communication_agent", "CommunicationMafAgent"),
        }
        if self.agent_name not in mapping:
            raise RuntimeError(f"BaseAgentExecutor: unknown agent_name {self.agent_name!r}")
        from importlib import import_module

        mod_name, cls_name = mapping[self.agent_name]
        mod = import_module(f"maf_runtime.{mod_name}")
        facade_cls = getattr(mod, cls_name)
        self._facade = facade_cls()
        if self.output_schema is None:
            type(self).output_schema = self._facade.output_schema
        return self._facade

    # ----- Execution -----------------------------------------------------

    async def run_legacy(self, input_payload: Any) -> BaseModel:
        return await self._get_facade().run_legacy(input_payload)

    async def invoke_agent(self, input_payload: Any) -> BaseModel:
        return await self._get_facade().run_maf(input_payload)

    def _mode(self) -> AgentMode:
        try:
            return get_agent_mode(self.agent_name)
        except ValueError:
            return "legacy"

    async def execute_step(
        self,
        input_payload: Any,
        *,
        correlation_id: str,
        run_id: str | None = None,
    ) -> BaseModel:
        """Public entry — applies the retry budget + output validation pipeline."""
        self._get_facade()  # ensure output_schema is bound
        schema = self.output_schema
        if schema is None:
            raise RuntimeError(f"{type(self).__name__}: output_schema unbound")

        async def _do() -> BaseModel:
            mode = self._mode()
            if mode == "legacy":
                raw = await self.run_legacy(input_payload)
            elif mode == "maf":
                raw = await self.invoke_agent(input_payload)
            else:  # shadow
                raw = await self.run_legacy(input_payload)
            return validate_output(schema, raw, correlation_id=correlation_id, run_id=run_id)

        return await with_retry_budget(_do, correlation_id=correlation_id, run_id=run_id)

    # ----- Checkpoint hooks ---------------------------------------------

    async def on_checkpoint_save(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of executor state."""
        return dict(self._state)

    async def on_checkpoint_restore(self, state: dict[str, Any]) -> None:
        self._state = dict(state)


__all__ = [
    "BaseAgentExecutor",
    "validate_output",
    "with_retry_budget",
    "DEFAULT_RETRY_ATTEMPTS",
    "DEFAULT_RETRY_TOTAL_SECONDS",
]


# Suppress unused-import warning for inspect (kept for future hook introspection).
_ = inspect

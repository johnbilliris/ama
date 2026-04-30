"""Canonical typed error hierarchy for the MAF runtime (FR-004).

Every error MUST carry a `correlation_id` and an optional `run_id` so that any
caught exception can be linked back to the OpenTelemetry trace that produced it
(per FR-016) and the workflow run document that owns the failing step.

Downstream modules under ``apps/agents/maf_runtime/`` MUST import error classes
from this module; locally-defined ``Exception`` subclasses inside the package
are forbidden by the static-analysis test ``tests/unit/test_maf_runtime_error_imports.py``
(T074b).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class _ErrorPayload:
    """Common payload carried by every MafRuntimeError."""

    correlation_id: str
    run_id: str | None = None
    error_code: str = "maf_runtime_error"
    details: dict[str, Any] = field(default_factory=dict)


class MafRuntimeError(Exception):
    """Base class for all errors raised inside ``apps/agents/maf_runtime/``."""

    error_code: str = "maf_runtime_error"

    def __init__(
        self,
        message: str,
        *,
        correlation_id: str,
        run_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.payload = _ErrorPayload(
            correlation_id=correlation_id,
            run_id=run_id,
            error_code=self.error_code,
            details=details or {},
        )

    @property
    def correlation_id(self) -> str:
        return self.payload.correlation_id

    @property
    def run_id(self) -> str | None:
        return self.payload.run_id

    @property
    def details(self) -> dict[str, Any]:
        return self.payload.details

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"{type(self).__name__}({super().__str__()!r}, "
            f"error_code={self.error_code!r}, correlation_id={self.correlation_id!r}, "
            f"run_id={self.run_id!r})"
        )


# ---------- LLM failures ----------------------------------------------------


class LlmFailure(MafRuntimeError):
    """Generic LLM-side failure. Subclasses drive per-class retry policy."""

    error_code = "llm_failure"


class LlmRateLimitError(LlmFailure):
    """Azure OpenAI 429 rate-limit response. RETRYABLE within budget."""

    error_code = "llm_rate_limit"


class LlmTimeoutError(LlmFailure):
    """LLM call did not return within the per-step timeout. RETRYABLE."""

    error_code = "llm_timeout"


class LlmContentFilterError(LlmFailure):
    """Azure OpenAI content filter blocked the request or response. NOT retryable."""

    error_code = "llm_content_filter"


class LlmQuotaError(LlmFailure):
    """Azure OpenAI deployment quota exceeded. NOT retryable; operator action required."""

    error_code = "llm_quota_exceeded"


class LlmServerError(LlmFailure):
    """Azure OpenAI 5xx response. RETRYABLE within budget."""

    error_code = "llm_server_error"


# ---------- Tool / MCP failures --------------------------------------------


class ToolFailure(MafRuntimeError):
    """Generic out-of-process tool failure (FR-021)."""

    error_code = "tool_failure"


class ToolVersionMismatchError(ToolFailure):
    """MCP server's advertised major version does not match the allow-list pin (FR-019a). NOT retryable."""

    error_code = "tool_version_mismatch"


class ToolUnreachableError(ToolFailure):
    """MCP server unreachable (DNS, TCP refusal, 503). RETRYABLE within budget."""

    error_code = "tool_unreachable"


class ToolTimeoutError(ToolFailure):
    """MCP server did not respond within the tool-call timeout. RETRYABLE within budget."""

    error_code = "tool_timeout"


class ToolMalformedResponseError(ToolFailure):
    """MCP server returned invalid JSON or violated the MCP envelope schema. NOT retryable."""

    error_code = "tool_malformed_response"


# ---------- Validation / policy failures -----------------------------------


class ValidationFailure(MafRuntimeError):
    """Generic validation failure (input or output)."""

    error_code = "validation_failure"


class OutputSchemaMismatchError(ValidationFailure):
    """Agent output failed Pydantic validation vs ``agent_definition.output_schema`` (FR-003)."""

    error_code = "output_schema_mismatch"


class PolicyFailure(MafRuntimeError):
    """Cross-cutting policy refused to proceed (e.g., content safety blocked)."""

    error_code = "policy_failure"


# ---------- Workflow / state failures --------------------------------------


class InvalidStateTransitionError(MafRuntimeError):
    """Run-state transition not permitted by the FR-011b state machine."""

    error_code = "invalid_state_transition"


class ActiveRunAlreadyExistsError(MafRuntimeError):
    """A second active workflow run for the same incident is forbidden (FR-011a)."""

    error_code = "active_run_already_exists"


class CheckpointStoreUnavailableError(MafRuntimeError):
    """Cosmos checkpoint store cannot be written. Edge case: workflow halts the run with a typed error."""

    error_code = "checkpoint_store_unavailable"


# ---------- Repository / governance failures -------------------------------


class ToolRegistrationConflictError(MafRuntimeError):
    """Attempt to re-register an existing (tool_name, major_version) tuple (FR-019a)."""

    error_code = "tool_registration_conflict"


# ---------- HITL failures --------------------------------------------------


class DuplicateDecisionConflictError(MafRuntimeError):
    """Two commanders attempted to decide the same approval simultaneously (spec edge case)."""

    error_code = "duplicate_decision_conflict"


__all__ = [
    "MafRuntimeError",
    # LLM
    "LlmFailure",
    "LlmRateLimitError",
    "LlmTimeoutError",
    "LlmContentFilterError",
    "LlmQuotaError",
    "LlmServerError",
    # Tool / MCP
    "ToolFailure",
    "ToolVersionMismatchError",
    "ToolUnreachableError",
    "ToolTimeoutError",
    "ToolMalformedResponseError",
    # Validation / policy
    "ValidationFailure",
    "OutputSchemaMismatchError",
    "PolicyFailure",
    # Workflow / state
    "InvalidStateTransitionError",
    "ActiveRunAlreadyExistsError",
    "CheckpointStoreUnavailableError",
    # Governance
    "ToolRegistrationConflictError",
    # HITL
    "DuplicateDecisionConflictError",
]


# Retryable / non-retryable classification used by the executor retry budget (T042c).
RETRYABLE_ERRORS: tuple[type[MafRuntimeError], ...] = (
    LlmRateLimitError,
    LlmTimeoutError,
    LlmServerError,
    ToolUnreachableError,
    ToolTimeoutError,
    CheckpointStoreUnavailableError,
)

NON_RETRYABLE_ERRORS: tuple[type[MafRuntimeError], ...] = (
    LlmContentFilterError,
    LlmQuotaError,
    OutputSchemaMismatchError,
    ValidationFailure,
    ToolVersionMismatchError,
    ToolMalformedResponseError,
    PolicyFailure,
    InvalidStateTransitionError,
    ActiveRunAlreadyExistsError,
    DuplicateDecisionConflictError,
)


def is_retryable(error: BaseException) -> bool:
    """Return True iff the error class is in the retryable set (T042c)."""
    return isinstance(error, RETRYABLE_ERRORS) and not isinstance(error, NON_RETRYABLE_ERRORS)

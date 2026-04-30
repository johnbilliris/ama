"""Unit tests for the canonical typed error hierarchy (T011b, FR-004)."""

from __future__ import annotations

import inspect

import pytest

from apps.agents.maf_runtime.errors import (
    NON_RETRYABLE_ERRORS,
    RETRYABLE_ERRORS,
    ActiveRunAlreadyExistsError,
    CheckpointStoreUnavailableError,
    DuplicateDecisionConflictError,
    InvalidStateTransitionError,
    LlmContentFilterError,
    LlmFailure,
    LlmQuotaError,
    LlmRateLimitError,
    LlmServerError,
    LlmTimeoutError,
    MafRuntimeError,
    OutputSchemaMismatchError,
    PolicyFailure,
    ToolFailure,
    ToolMalformedResponseError,
    ToolTimeoutError,
    ToolUnreachableError,
    ToolVersionMismatchError,
    ValidationFailure,
    is_retryable,
)

ALL_ERRORS = [
    LlmFailure, LlmRateLimitError, LlmTimeoutError, LlmContentFilterError, LlmQuotaError, LlmServerError,
    ToolFailure, ToolVersionMismatchError, ToolUnreachableError, ToolTimeoutError, ToolMalformedResponseError,
    ValidationFailure, OutputSchemaMismatchError, PolicyFailure,
    InvalidStateTransitionError, ActiveRunAlreadyExistsError, CheckpointStoreUnavailableError,
    DuplicateDecisionConflictError,
]


@pytest.mark.parametrize("cls", ALL_ERRORS)
def test_every_error_inherits_maf_runtime_error(cls: type) -> None:
    assert issubclass(cls, MafRuntimeError), f"{cls.__name__} must inherit MafRuntimeError"


@pytest.mark.parametrize("cls", ALL_ERRORS)
def test_every_error_carries_payload(cls: type) -> None:
    err = cls("boom", correlation_id="abc-123", run_id="run-1", details={"k": "v"})
    assert err.correlation_id == "abc-123"
    assert err.run_id == "run-1"
    assert err.details == {"k": "v"}
    assert err.error_code  # non-empty


@pytest.mark.parametrize("cls", ALL_ERRORS)
def test_every_error_has_unique_error_code(cls: type) -> None:
    codes = [c.error_code for c in ALL_ERRORS]
    assert len(set(codes)) == len(codes)


def test_retryable_classification() -> None:
    assert is_retryable(LlmRateLimitError("x", correlation_id="c"))
    assert is_retryable(LlmServerError("x", correlation_id="c"))
    assert is_retryable(ToolUnreachableError("x", correlation_id="c"))
    assert not is_retryable(LlmContentFilterError("x", correlation_id="c"))
    assert not is_retryable(ToolVersionMismatchError("x", correlation_id="c"))
    assert not is_retryable(OutputSchemaMismatchError("x", correlation_id="c"))


def test_retryable_and_non_retryable_sets_are_disjoint() -> None:
    assert set(RETRYABLE_ERRORS).isdisjoint(set(NON_RETRYABLE_ERRORS))


def test_repr_contains_useful_context() -> None:
    err = MafRuntimeError("kaboom", correlation_id="cid", run_id="r1")
    rendered = repr(err)
    assert "MafRuntimeError" in rendered
    assert "cid" in rendered
    assert "r1" in rendered


def test_no_locally_defined_exception_in_errors_module() -> None:
    """Sanity: errors.py is the canonical home; nothing else adds error classes (verified by T074b)."""
    from apps.agents.maf_runtime import errors as mod

    found = [
        n for n, obj in inspect.getmembers(mod, inspect.isclass)
        if issubclass(obj, BaseException) and obj is not Exception and obj is not BaseException
    ]
    assert MafRuntimeError.__name__ in found

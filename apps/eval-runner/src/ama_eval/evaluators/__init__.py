"""Evaluator package — auto-registers all default evaluators on import."""

from . import (
    judge,  # noqa: F401
    prompt_injection,  # noqa: F401
    retrieval,  # noqa: F401
    rule_based,  # noqa: F401
)
from .base import (
    EvalInput,
    EvalResult,
    Evaluator,
    ModelOutput,
    clear_registry,
    get,
    list_evaluators,
    register,
)

__all__ = [
    "EvalInput",
    "EvalResult",
    "Evaluator",
    "ModelOutput",
    "clear_registry",
    "get",
    "list_evaluators",
    "register",
]

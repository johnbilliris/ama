"""Evaluator base + registry.

Evaluators score a single (case, model_output) pair against a metric. They are
pure functions so the orchestrator can run thousands of them concurrently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class EvalInput:
    case_id: str
    case_inputs: dict
    expected_behaviour: dict
    sensitivity_labels: list[str]
    hazard_tags: list[str]
    severity: str
    language: str
    retrieval_scope: bool = False
    retrieved_context: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ModelOutput:
    text: str
    finish_reason: str
    safety_filter_triggered: bool
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class EvalResult:
    metric_id: str
    score: float
    pass_: bool
    rationale: str
    evidence: dict = field(default_factory=dict)


class Evaluator(Protocol):
    metric_id: str
    family: str
    tier: str

    def evaluate(self, inp: EvalInput, out: ModelOutput) -> EvalResult: ...


_REGISTRY: dict[str, Evaluator] = {}


def register(evaluator: Evaluator) -> Evaluator:
    _REGISTRY[evaluator.metric_id] = evaluator
    return evaluator


def get(metric_id: str) -> Evaluator | None:
    return _REGISTRY.get(metric_id)


def list_evaluators() -> list[Evaluator]:
    return list(_REGISTRY.values())


def clear_registry() -> None:
    _REGISTRY.clear()


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

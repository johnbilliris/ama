"""Evaluator base + registry.

Evaluators score a single (case, model_output) pair against a metric. They are
pure functions so the orchestrator can run thousands of them concurrently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

JsonObject = dict[str, object]


@dataclass(frozen=True)
class EvalInput:
    case_id: str
    case_inputs: JsonObject
    expected_behaviour: JsonObject
    sensitivity_labels: list[str]
    hazard_tags: list[str]
    severity: str
    language: str
    retrieval_scope: bool = False
    retrieved_context: list[JsonObject] = field(default_factory=list)


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
    evidence: JsonObject = field(default_factory=dict)


class Evaluator(Protocol):
    @property
    def metric_id(self) -> str: ...

    @property
    def family(self) -> str: ...

    @property
    def tier(self) -> str: ...

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

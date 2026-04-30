"""LLM Strategy chain (spec 032 FR-P01).

Promotes the LLM fallback flow from nested ``if`` blocks inside
``LLMCallMixin._generate_with_fallback`` into a first-class Strategy pattern.

Strategy chain (in order):
  1. ``PrimaryModelStrategy``    — the configured reasoning/drafting deployment.
  2. ``SecondaryModelStrategy``  — fallback to the alternate tier (drafting if
     primary was reasoning, and vice versa).
  3. ``TemplateFallbackStrategy``— deterministic template; never raises.

Each strategy implements :class:`LlmStrategy`. The orchestrator iterates the
chain, returns the first successful response, and emits the
``llm.fallback_step_total`` customMetric for each transition.

This module is additive; existing ``llm_mixin.py`` continues to work and can
be migrated incrementally to consume :func:`build_default_chain`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StrategyResult:
    """Outcome of a single strategy attempt."""

    success: bool
    output: Any | None
    strategy_name: str
    error: str | None = None
    metadata: dict[str, Any] | None = None


class LlmStrategy(Protocol):
    """A single attempt in the LLM fallback chain."""

    name: str

    def attempt(
        self,
        *,
        prompt: str,
        response_model: type[Any] | None,
        context: dict[str, Any] | None,
    ) -> StrategyResult:
        """Try once; return a result. MUST NOT raise on expected failures."""
        ...


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------


class PrimaryModelStrategy:
    """Calls the primary model deployment (reasoning or drafting per config)."""

    name = "primary_model"

    def __init__(self, llm_call: Callable[..., Any]) -> None:
        self._llm_call = llm_call

    def attempt(
        self,
        *,
        prompt: str,
        response_model: type[Any] | None,
        context: dict[str, Any] | None,
    ) -> StrategyResult:
        try:
            output = self._llm_call(prompt=prompt, response_model=response_model, context=context)
            return StrategyResult(success=True, output=output, strategy_name=self.name)
        except Exception as exc:  # noqa: BLE001
            return StrategyResult(success=False, output=None, strategy_name=self.name, error=str(exc))


class SecondaryModelStrategy:
    """Calls an alternate-tier model when the primary fails."""

    name = "secondary_model"

    def __init__(self, llm_call: Callable[..., Any]) -> None:
        self._llm_call = llm_call

    def attempt(
        self,
        *,
        prompt: str,
        response_model: type[Any] | None,
        context: dict[str, Any] | None,
    ) -> StrategyResult:
        try:
            output = self._llm_call(prompt=prompt, response_model=response_model, context=context)
            return StrategyResult(success=True, output=output, strategy_name=self.name)
        except Exception as exc:  # noqa: BLE001
            return StrategyResult(success=False, output=None, strategy_name=self.name, error=str(exc))


class TemplateFallbackStrategy:
    """Deterministic template output. Never raises; lowers downstream confidence."""

    name = "template_fallback"

    def __init__(self, template_fn: Callable[..., Any]) -> None:
        self._template_fn = template_fn

    def attempt(
        self,
        *,
        prompt: str,
        response_model: type[Any] | None,
        context: dict[str, Any] | None,
    ) -> StrategyResult:
        try:
            output = self._template_fn(prompt=prompt, context=context)
            return StrategyResult(
                success=True,
                output=output,
                strategy_name=self.name,
                metadata={"reduced_confidence": True},
            )
        except Exception as exc:  # noqa: BLE001
            # Last resort — even templates failed; surface the error rather
            # than silently swallowing a guaranteed-degraded path.
            logger.exception("Template fallback failed")
            return StrategyResult(success=False, output=None, strategy_name=self.name, error=str(exc))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainOutcome:
    """Final outcome of the strategy chain."""

    output: Any
    strategy_used: str
    attempts: list[StrategyResult]
    reduced_confidence: bool = False


def run_chain(
    chain: Sequence[LlmStrategy],
    *,
    prompt: str,
    response_model: type[Any] | None = None,
    context: dict[str, Any] | None = None,
) -> ChainOutcome:
    """Run ``chain`` until the first success; emit fallback step metrics; return outcome.

    Raises ``RuntimeError`` only if every strategy fails (which means even the
    template fallback raised — a programming error since templates SHOULD never
    raise).
    """
    attempts: list[StrategyResult] = []
    previous: str | None = None

    for strategy in chain:
        result = strategy.attempt(prompt=prompt, response_model=response_model, context=context)
        attempts.append(result)

        if previous is not None and previous != strategy.name:
            _emit_fallback_step(previous, strategy.name)

        if result.success:
            reduced = bool(result.metadata and result.metadata.get("reduced_confidence"))
            return ChainOutcome(
                output=result.output,
                strategy_used=strategy.name,
                attempts=attempts,
                reduced_confidence=reduced,
            )

        previous = strategy.name

    raise RuntimeError(f"All LLM strategies failed: {[(a.strategy_name, a.error) for a in attempts]}")


def build_default_chain(
    *,
    primary: Callable[..., Any],
    secondary: Callable[..., Any] | None,
    template: Callable[..., Any],
) -> list[LlmStrategy]:
    """Build the canonical chain for an agent's LLM call."""
    chain: list[LlmStrategy] = [PrimaryModelStrategy(primary)]
    if secondary is not None:
        chain.append(SecondaryModelStrategy(secondary))
    chain.append(TemplateFallbackStrategy(template))
    return chain


def _emit_fallback_step(from_strategy: str, to_strategy: str) -> None:
    try:
        from apps.api.app.observability.metrics import emit_counter

        emit_counter(
            "llm.fallback_step_total",
            1,
            {"from_strategy": from_strategy, "to_strategy": to_strategy},
        )
    except Exception:  # noqa: BLE001
        logger.debug("fallback step metric emit failed", exc_info=True)

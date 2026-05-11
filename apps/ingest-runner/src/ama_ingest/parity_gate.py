"""Parity gate (Spec 036 T046; FR-RAG-IDX-04; R-05).

Four-signal gate guarding the blue-green alias flip from ``corpus-v{N}`` to
``corpus-v{N+1}``. The gate is the contract specified by
``ingest-pipeline.md`` §3.3 — alias flip is permitted only when **all four**
signals pass.

================================== ===================================
Signal                             Threshold
================================== ===================================
1. Chunk-count delta              ±5% of the reference snapshot.
2. Embedding cost ratio           new total ≤ 1.3× old.
3. FR-023 decision-equivalence    ≥ 95% on the regression suite.
4. Single-``embedding_model_id``  exactly 1 distinct value per index.
================================== ===================================

Failure of any signal halts the flip; an SRE alert fires; the previous alias
remains the source of truth. Signal 4 is also a data-corruption signal — its
failure triggers automatic rollback per Architecture-memo R1 + Quality-memo R1.

This module is **pure logic** — it consumes pre-computed metric snapshots and
emits a verdict; no Azure clients are imported here. Tests pass synthetic
snapshots; production wires it into ``__main__`` after the ingest write phase.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants — bound by ``ingest-pipeline.md`` §3.3 + R-05.
# --------------------------------------------------------------------------- #


CHUNK_COUNT_TOLERANCE: float = 0.05
"""±5% of the reference chunk_count is the allowed drift."""

COST_RATIO_CEILING: float = 1.3
"""new_cost / old_cost must be ≤ this value."""

DECISION_EQUIVALENCE_FLOOR: float = 0.95
"""FR-023 decision-equivalence must be ≥ this value (spec 033 reuse)."""


SignalName = Literal[
    "chunk_count_delta",
    "cost_ratio",
    "decision_equivalence",
    "single_embedding_model",
]


# --------------------------------------------------------------------------- #
# Inputs + outputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ParityInputs:
    """Snapshot of the four signal inputs computed elsewhere."""

    old_chunk_count: int
    new_chunk_count: int
    old_embedding_cost_usd: float
    new_embedding_cost_usd: float
    decision_equivalence: float
    new_index_distinct_embedding_model_ids: int


@dataclass
class SignalResult:
    name: SignalName
    passed: bool
    actual: float
    threshold: float
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParityVerdict:
    status: Literal["PASS", "FAIL"]
    signals: list[SignalResult] = field(default_factory=list)

    @property
    def failed_signals(self) -> list[SignalResult]:
        return [s for s in self.signals if not s.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "signals": [s.to_dict() for s in self.signals],
        }


# --------------------------------------------------------------------------- #
# Gate implementation
# --------------------------------------------------------------------------- #


def evaluate(inputs: ParityInputs) -> ParityVerdict:
    """Evaluate all four signals against the inputs; return a verdict."""
    signals: list[SignalResult] = [
        _signal_chunk_count_delta(inputs),
        _signal_cost_ratio(inputs),
        _signal_decision_equivalence(inputs),
        _signal_single_model(inputs),
    ]
    status: Literal["PASS", "FAIL"] = "PASS" if all(s.passed for s in signals) else "FAIL"
    return ParityVerdict(status=status, signals=signals)


def _signal_chunk_count_delta(inputs: ParityInputs) -> SignalResult:
    if inputs.old_chunk_count == 0:
        # First-ever build — no prior baseline; signal passes trivially.
        return SignalResult(
            name="chunk_count_delta",
            passed=True,
            actual=0.0,
            threshold=CHUNK_COUNT_TOLERANCE,
            note="first build (no baseline)",
        )
    delta = abs(inputs.new_chunk_count - inputs.old_chunk_count) / inputs.old_chunk_count
    return SignalResult(
        name="chunk_count_delta",
        passed=delta <= CHUNK_COUNT_TOLERANCE,
        actual=delta,
        threshold=CHUNK_COUNT_TOLERANCE,
        note=f"new={inputs.new_chunk_count} old={inputs.old_chunk_count}",
    )


def _signal_cost_ratio(inputs: ParityInputs) -> SignalResult:
    if inputs.old_embedding_cost_usd <= 0:
        return SignalResult(
            name="cost_ratio",
            passed=True,
            actual=1.0,
            threshold=COST_RATIO_CEILING,
            note="no prior cost baseline",
        )
    ratio = inputs.new_embedding_cost_usd / inputs.old_embedding_cost_usd
    return SignalResult(
        name="cost_ratio",
        passed=ratio <= COST_RATIO_CEILING,
        actual=ratio,
        threshold=COST_RATIO_CEILING,
        note=f"new=${inputs.new_embedding_cost_usd:.2f} old=${inputs.old_embedding_cost_usd:.2f}",
    )


def _signal_decision_equivalence(inputs: ParityInputs) -> SignalResult:
    return SignalResult(
        name="decision_equivalence",
        passed=inputs.decision_equivalence >= DECISION_EQUIVALENCE_FLOOR,
        actual=inputs.decision_equivalence,
        threshold=DECISION_EQUIVALENCE_FLOOR,
        note="spec 033 FR-023 regression suite",
    )


def _signal_single_model(inputs: ParityInputs) -> SignalResult:
    return SignalResult(
        name="single_embedding_model",
        passed=inputs.new_index_distinct_embedding_model_ids == 1,
        actual=float(inputs.new_index_distinct_embedding_model_ids),
        threshold=1.0,
        note="R-05 signal 4 (data-corruption rollback trigger if fails)",
    )


__all__ = [
    "CHUNK_COUNT_TOLERANCE",
    "COST_RATIO_CEILING",
    "DECISION_EQUIVALENCE_FLOOR",
    "ParityInputs",
    "ParityVerdict",
    "SignalName",
    "SignalResult",
    "evaluate",
]

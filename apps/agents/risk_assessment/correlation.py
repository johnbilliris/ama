"""Multi-source signal correlation and contradiction detection.

Implements:
- Weighted confidence averaging: Σ(conf × weight × fresh) / Σ(weight × fresh)
- Stale signal identification
- Source diversity analysis
- Contradiction detection with multiplicative 0.7 penalty
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TypedDict

from risk_assessment.config import RiskAssessmentConfig


class RiskSignal(TypedDict, total=False):
    signal_id: str
    confidence_score: float
    freshness_score: float
    source_kind: str
    category: str
    risk_direction: str
    hazard_parameter: str
    payload: object
    provenance: dict[str, object]
    disaster_type: str | None
    evidence_state: str


logger = logging.getLogger(__name__)


@dataclass
class CorrelationResult:
    """Result of multi-source signal correlation."""

    weighted_confidence: float = 0.0
    stale_signal_ids: list[str] = field(default_factory=list)
    source_kinds: set[str] = field(default_factory=set)
    source_diversity: int = 0
    relies_on_unverified: bool = False
    signal_count: int = 0
    all_stale: bool = False


@dataclass
class ContradictionPair:
    """A pair of signals with opposing risk trajectories."""

    signal_id_a: str
    signal_id_b: str
    source_a: str
    source_b: str
    direction_a: str  # "increasing" or "decreasing"
    direction_b: str


@dataclass
class ContradictionResult:
    """Result of contradiction detection."""

    detected: bool = False
    pairs: list[ContradictionPair] = field(default_factory=list)
    details: list[dict[str, object]] = field(default_factory=list)


class SignalCorrelator:
    """Correlates multi-source signals with weighted confidence averaging."""

    def __init__(self, config: RiskAssessmentConfig | None = None) -> None:
        self._config = config or RiskAssessmentConfig()

    def compute_weighted_confidence(
        self,
        signals: list[RiskSignal],
    ) -> CorrelationResult:
        """Compute weighted confidence from a list of signal dicts.

        Each signal dict must have:
        - signal_id: str
        - confidence_score: float
        - freshness_score: float
        - source_kind: str (authoritative | iot | social)

        Formula: Σ(conf × weight × fresh) / Σ(weight × fresh)
        """
        if not signals:
            return CorrelationResult(weighted_confidence=0.0, all_stale=True)

        stale_ids: list[str] = []
        source_kinds: set[str] = set()
        numerator = 0.0
        denominator = 0.0
        unverified_weight = 0.0
        total_weight = 0.0

        for sig in signals:
            signal_id = sig.get("signal_id", "unknown")
            confidence = float(sig.get("confidence_score", 0.0))
            freshness = float(sig.get("freshness_score", 0.0))
            source_kind = sig.get("source_kind", "social")

            weight = self._config.source_weight_for(source_kind)
            source_kinds.add(source_kind)

            # Flag stale signals
            if freshness < self._config.stale_signal_threshold:
                stale_ids.append(signal_id)

            numerator += confidence * weight * freshness
            denominator += weight * freshness
            total_weight += weight

            if source_kind == "social":
                unverified_weight += weight

        all_stale = len(stale_ids) == len(signals)

        if all_stale:
            return CorrelationResult(
                weighted_confidence=0.0,
                stale_signal_ids=stale_ids,
                source_kinds=source_kinds,
                source_diversity=len(source_kinds),
                all_stale=True,
                signal_count=len(signals),
            )

        if denominator <= 0.0:
            return CorrelationResult(
                weighted_confidence=0.0,
                stale_signal_ids=stale_ids,
                source_kinds=source_kinds,
                source_diversity=len(source_kinds),
                all_stale=all_stale,
                signal_count=len(signals),
            )

        weighted_conf = numerator / denominator

        # Check if relies primarily on unverified sources
        relies_on_unverified = total_weight > 0.0 and unverified_weight / total_weight > 0.5

        return CorrelationResult(
            weighted_confidence=max(0.0, min(1.0, weighted_conf)),
            stale_signal_ids=stale_ids,
            source_kinds=source_kinds,
            source_diversity=len(source_kinds),
            relies_on_unverified=relies_on_unverified,
            signal_count=len(signals),
            all_stale=all_stale,
        )


class ContradictionDetector:
    """Detects opposing risk trajectories among signals.

    Two signals contradict when they have opposing risk_direction
    (one "increasing", one "decreasing") for the same hazard parameter
    and geographic area.
    """

    def __init__(self, config: RiskAssessmentConfig | None = None) -> None:
        self._config = config or RiskAssessmentConfig()

    def detect(self, signals: list[RiskSignal]) -> ContradictionResult:
        """Detect contradictions among signals.

        Each signal dict should have:
        - signal_id: str
        - source_kind: str
        - risk_direction: str ("increasing" | "decreasing" | "stable")
        - hazard_parameter: str (optional, for grouping)
        """
        if len(signals) < 2:
            return ContradictionResult()

        pairs: list[ContradictionPair] = []
        details: list[dict[str, object]] = []

        # Group signals by hazard parameter (default to "general" if not specified)
        by_param: dict[str, list[RiskSignal]] = {}
        for sig in signals:
            param = sig.get("hazard_parameter", "general")
            by_param.setdefault(param, []).append(sig)

        for param, group in by_param.items():
            increasing = [s for s in group if s.get("risk_direction") == "increasing"]
            decreasing = [s for s in group if s.get("risk_direction") == "decreasing"]

            if increasing and decreasing:
                # Report all cross-pairs
                for inc in increasing:
                    for dec in decreasing:
                        pair = ContradictionPair(
                            signal_id_a=inc.get("signal_id", "unknown"),
                            signal_id_b=dec.get("signal_id", "unknown"),
                            source_a=inc.get("source_kind", "unknown"),
                            source_b=dec.get("source_kind", "unknown"),
                            direction_a="increasing",
                            direction_b="decreasing",
                        )
                        pairs.append(pair)
                        details.append(
                            {
                                "signal_id_a": pair.signal_id_a,
                                "signal_id_b": pair.signal_id_b,
                                "source_a": pair.source_a,
                                "source_b": pair.source_b,
                                "hazard_parameter": param,
                                "direction_a": "increasing",
                                "direction_b": "decreasing",
                            }
                        )

        return ContradictionResult(
            detected=len(pairs) > 0,
            pairs=pairs,
            details=details,
        )

    def apply_contradiction_penalty(
        self,
        weighted_confidence: float,
        contradictions: ContradictionResult,
    ) -> float:
        """Apply multiplicative 0.7 penalty once if contradictions detected.

        Single reduction regardless of number of contradiction pairs.
        """
        if not contradictions.detected:
            return weighted_confidence

        adjusted = weighted_confidence * self._config.contradiction_reduction_factor
        return max(0.0, min(1.0, adjusted))

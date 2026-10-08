"""Health score calculation service.

Implements the weighted composite governance health score algorithm (R-004):
  constitutional_compliance × 0.40
  operational_readiness     × 0.25
  data_source_governance    × 0.20
  recovery_progress         × 0.15
"""

import logging
from datetime import UTC, datetime
from typing import TypedDict

from packages.domain.src.domain.models.governance_health_score import (
    DimensionScore,
    GovernanceHealthScore,
)


class ConstitutionalGate(TypedDict, total=False):
    status: str


class ReadinessData(TypedDict, total=False):
    exercise_completion_rate: float
    role_coverage_pct: float
    plan_currency_pct: float


class DataSourceStats(TypedDict, total=False):
    total: int
    compliant: int
    partially_compliant: int


class RecoveryDomainData(TypedDict, total=False):
    completion_pct: float


class RecoveryData(TypedDict, total=False):
    has_active_recovery: bool
    domains: list[RecoveryDomainData]


class DimensionResult(TypedDict):
    score: float
    input_count: int
    stale: bool


logger = logging.getLogger("health_score_service")

# Dimension weights per R-004
DIMENSION_WEIGHTS: dict[str, float] = {
    "constitutional_compliance": 0.40,
    "operational_readiness": 0.25,
    "data_source_governance": 0.20,
    "recovery_progress": 0.15,
}


class HealthScoreService:
    """Calculates composite governance health score from multiple data dimensions."""

    def calculate(
        self,
        *,
        constitutional_gates: list[ConstitutionalGate] | None = None,
        readiness_data: ReadinessData | None = None,
        data_source_stats: DataSourceStats | None = None,
        recovery_data: RecoveryData | None = None,
        tenant_id: str = "live",
        has_active_incident: bool = False,
    ) -> GovernanceHealthScore:
        """Calculate the composite health score from all four dimensions."""
        dimensions: list[DimensionScore] = []

        # 1. Constitutional compliance (40%)
        const_score = self._calculate_constitutional_score(constitutional_gates or [])
        dimensions.append(
            DimensionScore(
                dimension="constitutional_compliance",
                score=const_score["score"],
                weight=DIMENSION_WEIGHTS["constitutional_compliance"],
                weighted_score=const_score["score"] * DIMENSION_WEIGHTS["constitutional_compliance"],
                input_count=const_score["input_count"],
                stale=const_score.get("stale", False),
            )
        )

        # 2. Operational readiness (25%)
        ops_score = self._calculate_readiness_score(readiness_data or {})
        dimensions.append(
            DimensionScore(
                dimension="operational_readiness",
                score=ops_score["score"],
                weight=DIMENSION_WEIGHTS["operational_readiness"],
                weighted_score=ops_score["score"] * DIMENSION_WEIGHTS["operational_readiness"],
                input_count=ops_score["input_count"],
                stale=ops_score.get("stale", False),
            )
        )

        # 3. Data source governance (20%)
        ds_score = self._calculate_data_source_score(data_source_stats or {})
        dimensions.append(
            DimensionScore(
                dimension="data_source_governance",
                score=ds_score["score"],
                weight=DIMENSION_WEIGHTS["data_source_governance"],
                weighted_score=ds_score["score"] * DIMENSION_WEIGHTS["data_source_governance"],
                input_count=ds_score["input_count"],
                stale=ds_score.get("stale", False),
            )
        )

        # 4. Recovery progress (15%)
        rec_score = self._calculate_recovery_score(recovery_data or {})
        dimensions.append(
            DimensionScore(
                dimension="recovery_progress",
                score=rec_score["score"],
                weight=DIMENSION_WEIGHTS["recovery_progress"],
                weighted_score=rec_score["score"] * DIMENSION_WEIGHTS["recovery_progress"],
                input_count=rec_score["input_count"],
                stale=rec_score.get("stale", False),
            )
        )

        composite = sum(d.weighted_score for d in dimensions)
        status = GovernanceHealthScore.derive_status(composite)
        now = datetime.now(UTC)

        return GovernanceHealthScore(
            id=f"health-score-{tenant_id}-{int(now.timestamp())}",
            tenant_id=tenant_id,
            score=round(composite, 2),
            status=status,
            dimensions=dimensions,
            calculated_at=now,
            has_active_incident=has_active_incident,
        )

    def _calculate_constitutional_score(self, gates: list[ConstitutionalGate]) -> DimensionResult:
        """Score based on constitutional gate compliance.

        Gates with status 'assessment_pending' are excluded from the denominator.
        """
        if not gates:
            return {"score": 0.0, "input_count": 0, "stale": False}

        assessed = [g for g in gates if g.get("status") != "assessment_pending"]
        if not assessed:
            return {"score": 0.0, "input_count": len(gates), "stale": False}

        compliant = sum(1 for g in assessed if g.get("status") == "compliant")
        partial = sum(1 for g in assessed if g.get("status") == "partially_compliant")

        # Compliant = full credit, partially_compliant = half credit
        score = ((compliant + partial * 0.5) / len(assessed)) * 100
        return {"score": round(score, 2), "input_count": len(gates), "stale": False}

    def _calculate_readiness_score(self, data: ReadinessData) -> DimensionResult:
        """Score based on operational readiness metrics."""
        if not data:
            return {"score": 0.0, "input_count": 0, "stale": False}

        components: list[float] = []

        # Exercise completion rate (0-100)
        if "exercise_completion_rate" in data:
            components.append(data["exercise_completion_rate"])

        # Role coverage percentage (0-100)
        if "role_coverage_pct" in data:
            components.append(data["role_coverage_pct"])

        # Emergency plan currency (% not overdue)
        if "plan_currency_pct" in data:
            components.append(data["plan_currency_pct"])

        if not components:
            return {"score": 0.0, "input_count": 0, "stale": False}

        score = sum(components) / len(components)
        return {"score": round(score, 2), "input_count": len(components), "stale": False}

    def _calculate_data_source_score(self, stats: DataSourceStats) -> DimensionResult:
        """Score based on data source governance compliance."""
        if not stats:
            return {"score": 0.0, "input_count": 0, "stale": False}

        total = stats.get("total", 0)
        if total == 0:
            return {"score": 0.0, "input_count": 0, "stale": False}

        compliant = stats.get("compliant", 0)
        partial = stats.get("partially_compliant", 0)
        score = ((compliant + partial * 0.5) / total) * 100
        return {"score": round(score, 2), "input_count": total, "stale": False}

    def _calculate_recovery_score(self, data: RecoveryData) -> DimensionResult:
        """Score based on recovery progress.

        No active recovery = 100% (nothing to recover from).
        """
        if not data or not data.get("has_active_recovery", False):
            return {"score": 100.0, "input_count": 0, "stale": False}

        domains = data.get("domains", [])
        if not domains:
            return {"score": 100.0, "input_count": 0, "stale": False}

        # Average completion across all recovery domains
        avg = sum(d.get("completion_pct", 0) for d in domains) / len(domains)
        return {"score": round(avg, 2), "input_count": len(domains), "stale": False}

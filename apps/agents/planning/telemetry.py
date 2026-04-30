"""Planning-specific telemetry metrics.

NFR-007, R-013
"""

import logging

logger = logging.getLogger(__name__)

# Counters and gauges (stub — will integrate with OpenTelemetry when available)
_metrics: dict[str, float] = {
    "emergency_plan_activation_count": 0,
    "plan_currency_compliance_ratio": 0.0,
    "plan_section_completeness": 0.0,
}


def increment_activation_count() -> None:
    _metrics["emergency_plan_activation_count"] += 1
    logger.info("Metric: emergency_plan_activation_count=%d", _metrics["emergency_plan_activation_count"])


def update_currency_compliance(ratio: float) -> None:
    _metrics["plan_currency_compliance_ratio"] = ratio
    logger.info("Metric: plan_currency_compliance_ratio=%.2f", ratio)


def update_section_completeness(ratio: float) -> None:
    _metrics["plan_section_completeness"] = ratio
    logger.info("Metric: plan_section_completeness=%.2f", ratio)


def get_metrics() -> dict[str, float]:
    return dict(_metrics)

"""Distribution targets and validation for the disaster-response evaluation dataset."""

from __future__ import annotations

from typing import Any

HAZARD_TARGETS: dict[str, float] = {
    "structure-fire": 0.085,
    "bushfire": 0.080,
    "flood": 0.095,
    "storm": 0.075,
    "building-collapse": 0.065,
    "hazmat": 0.065,
    "mass-casualty": 0.070,
    "missing-person": 0.070,
    "fatality-report": 0.070,
    "remains-recovery": 0.055,
    "evacuation-order": 0.075,
    "public-info": 0.095,
    "crisis-distress": 0.100,
}

LANGUAGE_TARGETS: dict[str, float] = {
    "en-AU": 0.60,
    "en-NZ": 0.10,
    "vi-VN": 0.10,
    "zh-Hans-CN": 0.10,
    "ar-SA": 0.10,
}

ACTION_TARGETS: dict[str, float] = {
    "answer": 0.35,
    "refuse": 0.25,
    "escalate": 0.20,
    "clarify": 0.15,
    "redirect": 0.05,
}

SEVERITY_TARGETS: dict[str, float] = {
    "low": 0.15,
    "medium": 0.30,
    "high": 0.35,
    "critical": 0.20,
}

JURISDICTION_CODES: list[str] = [
    "AU-NSW",
    "AU-VIC",
    "AU-QLD",
    "AU-WA",
    "AU-SA",
    "AU-TAS",
    "AU-NT",
    "AU-ACT",
    "NZ-AUK",
]

SENSITIVITY_THRESHOLDS: dict[str, float] = {
    "graphic-fatality": 0.05,
    "human-remains": 0.05,
    "prompt-injection": 0.08,
    "crisis-distress": 0.04,
}


def _to_str(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def validate_distribution(cases: list) -> dict[str, dict]:
    """Compute counts and percentages across key dimensions.

    Returns a dict with keys: hazard, language, action, severity, sensitivity.
    Each value is a dict of {label: {"count": int, "percentage": float}}.
    """
    n = len(cases)
    if n == 0:
        return {}

    def _counts(values_fn) -> dict:
        counts: dict[str, int] = {}
        for case in cases:
            for v in values_fn(case):
                key = _to_str(v)
                counts[key] = counts.get(key, 0) + 1
        return {k: {"count": v, "percentage": round(v / n, 4)} for k, v in sorted(counts.items())}

    return {
        "hazard": _counts(lambda c: c.hazardTags),
        "language": _counts(lambda c: [c.language]),
        "action": _counts(lambda c: [c.expectedBehaviour.expectedAction]),
        "severity": _counts(lambda c: [c.severity]),
        "sensitivity": _counts(lambda c: c.sensitivityLabels),
    }

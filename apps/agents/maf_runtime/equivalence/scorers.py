"""Equivalence scorers (FR-023, T023).

The FR-023 rule:
- ≥95% decision-equivalence on enumerated **categorical** output fields, AND
- 100% schema-equivalence on populated fields,
evaluated against a per-agent fixture corpus; **free-text fields** are excluded.

Per-agent categorical-field maps are declared here; if a future agent needs a
different set, add to ``CATEGORICAL_FIELDS_BY_AGENT``. Free-text fields default
to all string-typed fields not in the categorical set.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


CATEGORICAL_FIELDS_BY_AGENT: dict[str, tuple[str, ...]] = {
    "monitoring": ("triage_decision", "category", "severity"),
    "risk_assessment": ("hazard_severity", "incident_level", "category"),
    "evacuation": ("evacuation_stage", "evacuation_type", "approach"),
    "resource_allocation": ("priority_tier", "deployment_status"),
    "communication": ("aws_tier", "approval_required", "channel_set"),
}


DECISION_EQUIVALENCE_THRESHOLD = 0.95
SCHEMA_EQUIVALENCE_THRESHOLD = 1.00


class EquivalenceVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class FieldDelta:
    field: str
    legacy: Any
    maf: Any


@dataclass
class CaseResult:
    case_id: str
    decision_match: bool
    schema_match: bool
    decision_deltas: list[FieldDelta] = field(default_factory=list)
    schema_deltas: list[str] = field(default_factory=list)


@dataclass
class EquivalenceReport:
    agent_name: str
    total_cases: int
    decision_match_count: int
    schema_match_count: int
    decision_match_rate: float
    schema_match_rate: float
    verdict: EquivalenceVerdict
    case_results: list[CaseResult]
    categorical_fields: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str, indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            f"# Equivalence report — `{self.agent_name}`",
            "",
            f"**Verdict**: {'✅ PASS' if self.verdict == EquivalenceVerdict.PASS else '❌ FAIL'}  ",
            f"**Decision-equivalence**: {self.decision_match_count}/{self.total_cases} "
            f"({self.decision_match_rate:.2%}); threshold ≥{DECISION_EQUIVALENCE_THRESHOLD:.0%}.  ",
            f"**Schema-equivalence**: {self.schema_match_count}/{self.total_cases} "
            f"({self.schema_match_rate:.2%}); threshold = {SCHEMA_EQUIVALENCE_THRESHOLD:.0%}.  ",
            f"**Categorical fields scored**: {', '.join(self.categorical_fields) or '(none)'}",
            "",
            "## Failing cases",
            "",
        ]
        failing = [c for c in self.case_results if not (c.decision_match and c.schema_match)]
        if not failing:
            lines.append("_All cases pass._")
        else:
            for c in failing:
                lines.append(f"### {c.case_id}")
                if not c.decision_match:
                    lines.append(f"- decision deltas: {[d.field for d in c.decision_deltas]}")
                if not c.schema_match:
                    lines.append(f"- schema deltas (missing populated fields): {c.schema_deltas}")
                lines.append("")
        return "\n".join(lines)


def _coerce_dict(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", by_alias=True)
    if hasattr(payload, "__dict__"):
        return {k: v for k, v in payload.__dict__.items() if not k.startswith("_")}
    return {"value": payload}


def _populated_keys(d: dict[str, Any]) -> set[str]:
    """A 'populated' field is non-None and non-empty (after dict/list/str empty checks)."""
    out: set[str] = set()
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, str | dict | list | tuple | set) and not v:
            continue
        out.add(k)
    return out


def score(
    *,
    agent_name: str,
    pairs: list[tuple[str, Any, Any]],
) -> EquivalenceReport:
    """Score a list of (case_id, legacy_output, maf_output) tuples.

    Args:
        agent_name: One of the keys in ``CATEGORICAL_FIELDS_BY_AGENT``.
        pairs: Per-case outputs to compare.
    """
    categorical = CATEGORICAL_FIELDS_BY_AGENT.get(agent_name, ())
    cases: list[CaseResult] = []
    decision_match_count = 0
    schema_match_count = 0

    for case_id, legacy, maf in pairs:
        legacy_d = _coerce_dict(legacy)
        maf_d = _coerce_dict(maf)

        # Decision equivalence: every categorical field must match (when present in legacy).
        decision_deltas: list[FieldDelta] = []
        for f in categorical:
            if f in legacy_d:
                if legacy_d.get(f) != maf_d.get(f):
                    decision_deltas.append(FieldDelta(field=f, legacy=legacy_d.get(f), maf=maf_d.get(f)))
        decision_match = not decision_deltas

        # Schema equivalence: every populated key in the legacy output must be populated in MAF.
        legacy_pop = _populated_keys(legacy_d)
        maf_pop = _populated_keys(maf_d)
        missing = sorted(legacy_pop - maf_pop)
        schema_match = not missing

        cases.append(
            CaseResult(
                case_id=case_id,
                decision_match=decision_match,
                schema_match=schema_match,
                decision_deltas=decision_deltas,
                schema_deltas=missing,
            )
        )
        if decision_match:
            decision_match_count += 1
        if schema_match:
            schema_match_count += 1

    total = len(pairs)
    decision_rate = (decision_match_count / total) if total else 1.0
    schema_rate = (schema_match_count / total) if total else 1.0
    verdict = (
        EquivalenceVerdict.PASS
        if decision_rate >= DECISION_EQUIVALENCE_THRESHOLD and schema_rate >= SCHEMA_EQUIVALENCE_THRESHOLD
        else EquivalenceVerdict.FAIL
    )
    return EquivalenceReport(
        agent_name=agent_name,
        total_cases=total,
        decision_match_count=decision_match_count,
        schema_match_count=schema_match_count,
        decision_match_rate=decision_rate,
        schema_match_rate=schema_rate,
        verdict=verdict,
        case_results=cases,
        categorical_fields=categorical,
    )


__all__ = [
    "CATEGORICAL_FIELDS_BY_AGENT",
    "DECISION_EQUIVALENCE_THRESHOLD",
    "SCHEMA_EQUIVALENCE_THRESHOLD",
    "EquivalenceReport",
    "EquivalenceVerdict",
    "FieldDelta",
    "CaseResult",
    "score",
]

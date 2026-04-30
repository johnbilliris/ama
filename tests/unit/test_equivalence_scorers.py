"""Unit tests for the equivalence scorers (T023, FR-023)."""

from __future__ import annotations

from apps.agents.maf_runtime.equivalence.scorers import (
    DECISION_EQUIVALENCE_THRESHOLD,
    SCHEMA_EQUIVALENCE_THRESHOLD,
    EquivalenceVerdict,
    score,
)


def test_score_pass_when_all_match() -> None:
    pairs = [
        (
            f"case-{i}",
            {"triage_decision": "escalate", "category": "fire", "narrative": "bushfire"},
            {"triage_decision": "escalate", "category": "fire", "narrative": "different prose"},
        )
        for i in range(20)
    ]
    report = score(agent_name="monitoring", pairs=pairs)
    assert report.verdict == EquivalenceVerdict.PASS
    assert report.decision_match_rate == 1.0
    assert report.schema_match_rate == 1.0


def test_score_pass_when_decision_matches_above_95_percent() -> None:
    # 19/20 categorical matches = 95.0% — exactly on the threshold.
    pairs: list[tuple[str, dict, dict]] = []
    for i in range(19):
        pairs.append((f"case-{i}", {"triage_decision": "escalate", "category": "fire"},
                      {"triage_decision": "escalate", "category": "fire"}))
    pairs.append(("case-bad", {"triage_decision": "escalate", "category": "fire"},
                  {"triage_decision": "suppress", "category": "fire"}))
    report = score(agent_name="monitoring", pairs=pairs)
    assert report.decision_match_rate >= DECISION_EQUIVALENCE_THRESHOLD
    assert report.verdict == EquivalenceVerdict.PASS


def test_score_fail_when_categorical_disagreement_above_5_percent() -> None:
    pairs = [
        ("c1", {"triage_decision": "escalate"}, {"triage_decision": "escalate"}),
        ("c2", {"triage_decision": "escalate"}, {"triage_decision": "suppress"}),
    ]
    report = score(agent_name="monitoring", pairs=pairs)
    assert report.decision_match_rate == 0.5
    assert report.verdict == EquivalenceVerdict.FAIL


def test_score_fail_when_populated_field_missing() -> None:
    pairs = [
        ("c1",
         {"triage_decision": "escalate", "category": "fire", "rationale": "..."},
         {"triage_decision": "escalate"}),
    ]
    report = score(agent_name="monitoring", pairs=pairs)
    assert report.schema_match_rate < SCHEMA_EQUIVALENCE_THRESHOLD
    assert report.verdict == EquivalenceVerdict.FAIL
    assert "category" in report.case_results[0].schema_deltas


def test_score_pass_when_only_free_text_differs() -> None:
    """Free-text fields are excluded from the categorical comparison."""
    pairs = [
        ("c1",
         {"triage_decision": "escalate", "category": "fire", "rationale": "long prose A"},
         {"triage_decision": "escalate", "category": "fire", "rationale": "long prose B (different)"}),
    ]
    report = score(agent_name="monitoring", pairs=pairs)
    assert report.verdict == EquivalenceVerdict.PASS


def test_zero_cases_passes() -> None:
    report = score(agent_name="monitoring", pairs=[])
    assert report.verdict == EquivalenceVerdict.PASS
    assert report.total_cases == 0

"""Unit tests for the SC-012 closure-ratio computation in
``scripts/web-coverage/review-log.py`` (T203).

Covers the pure-math helpers (``_compute_closure``, ``_is_escalated``)
to lock the CHK210/CHK211 numerator/denominator semantics. Integration
behaviour (``_open_meta_gap`` shelling out to ``gap-register.py``) is
exercised through the CLI smoke check + the cycle-1 acceptance gate.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "web-coverage" / "review-log.py"


@pytest.fixture(scope="module")
def review_log_module():
    """Load review-log.py as a module despite its hyphenated filename."""

    sys.path.insert(0, str(SCRIPT_PATH.parent))
    spec = importlib.util.spec_from_file_location("review_log_t203", SCRIPT_PATH)
    assert spec and spec.loader, "spec loader required"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CYCLE_A = "11111111-2222-4333-8444-555555555555"
CYCLE_B = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


def _mk(gap_id: str, **overrides) -> dict:
    base = {
        "gap_id": gap_id,
        "cycle_id": CYCLE_A,
        "status": "Open",
        "iteration_count": 0,
        "owner": "operations-officer",
    }
    base.update(overrides)
    return base


# ---------- _is_escalated ---------------------------------------------------


def test_is_escalated_iteration_ceiling(review_log_module) -> None:
    """iteration_count >= 4 is escalated (Q22 cycle ceiling)."""

    assert review_log_module._is_escalated(_mk("g1", iteration_count=4)) is True
    assert review_log_module._is_escalated(_mk("g2", iteration_count=5)) is True


def test_is_escalated_below_ceiling_not_escalated(review_log_module) -> None:
    """iteration_count < 4 alone is not escalated."""

    for n in (0, 1, 2, 3):
        assert review_log_module._is_escalated(_mk("g", iteration_count=n)) is False


def test_is_escalated_status_escalated(review_log_module) -> None:
    """status=Escalated is escalated even with low iteration_count."""

    assert review_log_module._is_escalated(_mk("g", status="Escalated")) is True


def test_is_escalated_owner_project_lead(review_log_module) -> None:
    """owner containing 'project-lead' is the escalated:project-lead marker."""

    assert review_log_module._is_escalated(_mk("g", owner="project-lead")) is True
    assert review_log_module._is_escalated(_mk("g", owner="ops-and-project-lead")) is True


# ---------- _compute_closure ------------------------------------------------


def test_compute_closure_all_closed_pass(review_log_module) -> None:
    entries = [
        _mk("g1", status="Closed"),
        _mk("g2", status="Closed"),
        _mk("g3", status="Closed"),
    ]
    summary = review_log_module._compute_closure(entries, CYCLE_A)
    assert summary["numerator"] == 3
    assert summary["denominator"] == 3
    assert summary["ratio"] == 1.0
    assert summary["passes_floor"] is True
    assert summary["closed_gap_ids"] == ["g1", "g2", "g3"]
    assert summary["escalated_gap_ids"] == []


def test_compute_closure_mixed_above_floor(review_log_module) -> None:
    """4 closed of 5 eligible = 0.80 — at the floor."""

    entries = [
        _mk("g1", status="Closed"),
        _mk("g2", status="Closed"),
        _mk("g3", status="Closed"),
        _mk("g4", status="Closed"),
        _mk("g5", status="Open"),
    ]
    summary = review_log_module._compute_closure(entries, CYCLE_A)
    assert summary["numerator"] == 4
    assert summary["denominator"] == 5
    assert summary["ratio"] == pytest.approx(0.8)
    assert summary["passes_floor"] is True


def test_compute_closure_below_floor(review_log_module) -> None:
    """3 closed of 5 eligible = 0.60 — below floor."""

    entries = [
        _mk(f"g{i}", status="Closed" if i < 4 else "Open")
        for i in range(1, 6)
    ]
    # entries: g1=Closed, g2=Closed, g3=Closed, g4=Open, g5=Open => 3/5 = 0.6
    summary = review_log_module._compute_closure(entries, CYCLE_A)
    assert summary["numerator"] == 3
    assert summary["denominator"] == 5
    assert summary["ratio"] == pytest.approx(0.6)
    assert summary["passes_floor"] is False


def test_compute_closure_escalated_excluded(review_log_module) -> None:
    """Escalated rows are excluded from BOTH numerator and denominator."""

    entries = [
        _mk("g1", status="Closed"),                       # eligible, closed
        _mk("g2", status="Closed", iteration_count=4),    # escalated -> excluded
        _mk("g3", status="Open", owner="project-lead"),   # escalated -> excluded
        _mk("g4", status="Open"),                         # eligible, open
    ]
    summary = review_log_module._compute_closure(entries, CYCLE_A)
    assert summary["numerator"] == 1
    assert summary["denominator"] == 2
    assert summary["ratio"] == pytest.approx(0.5)
    assert summary["escalated_gap_ids"] == ["g2", "g3"]
    assert summary["raw_objection_gap_ids"] == ["g1", "g4"]


def test_compute_closure_filters_by_cycle_id(review_log_module) -> None:
    """Entries from other cycles must not influence the numerator/denom."""

    entries = [
        _mk("g1", status="Closed"),                            # CYCLE_A
        _mk("g2", status="Closed", cycle_id=CYCLE_B),          # other cycle
        _mk("g3", status="Open", cycle_id=None),               # untagged
    ]
    summary = review_log_module._compute_closure(entries, CYCLE_A)
    assert summary["numerator"] == 1
    assert summary["denominator"] == 1
    assert summary["closed_gap_ids"] == ["g1"]


def test_compute_closure_empty_cycle_returns_perfect_ratio(review_log_module) -> None:
    """Defensive: zero gaps means nothing to close — treat as 1.0 pass."""

    summary = review_log_module._compute_closure([], CYCLE_A)
    assert summary["numerator"] == 0
    assert summary["denominator"] == 0
    assert summary["ratio"] == 1.0
    assert summary["passes_floor"] is True


def test_compute_closure_reopened_counts_as_eligible_not_closed(review_log_module) -> None:
    """A Reopened gap (post FR-027 regression) is in the denominator but not numerator."""

    entries = [
        _mk("g1", status="Closed"),
        _mk("g2", status="Reopened", iteration_count=2),
        _mk("g3", status="In-Progress"),
    ]
    summary = review_log_module._compute_closure(entries, CYCLE_A)
    assert summary["numerator"] == 1  # only g1
    assert summary["denominator"] == 3
    assert summary["closed_gap_ids"] == ["g1"]

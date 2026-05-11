"""Contract: SC-013 + SC-015 acceptance gates (T191 + T192).

Per Plan §F-A1.5 + §F-A3.6, the per-PR CI gate must:
  - SC-013: ≥95% precision on the `agency_disambiguation`-tagged subset
  - SC-015: ≥95% Commonwealth-first precedence on the `jurisdiction=act`
    national-institution subset of `authority_precedence`.

Until the live retrieval evaluator wires through (T188 blue-green rebuild +
production AI Search index), this gate validates the **fixture shape and
count** so that drift in golden-set-v1.json triggers CI failure.

When the live evaluator is in place (post-T222), this same gate will
parametrise over fixture entries and run them through the retrieval
service.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

GOLDEN_SET_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "golden-set-v1.json"
SC013_MIN_AGENCY_ENTRIES = 20  # Plan §F-A1.5
SC015_MIN_PRECEDENCE_ENTRIES = 20  # Plan §F-A3.6
SC013_PRECISION_FLOOR = 0.95
SC015_PRECISION_FLOOR = 0.95


@pytest.fixture(scope="module")
def golden_set() -> dict:
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


def _by_scenario(golden_set: dict, scenario: str) -> list[dict]:
    return [e for e in golden_set["entries"] if e["scenario"] == scenario]


def test_sc013_agency_disambiguation_minimum_size(golden_set: dict) -> None:
    """SC-013 gate: golden-set-v1 carries ≥20 agency_disambiguation entries
    (T189). CI fails if the fixture is dropped below the floor."""
    entries = _by_scenario(golden_set, "agency_disambiguation")
    assert len(entries) >= SC013_MIN_AGENCY_ENTRIES, (
        f"SC-013 acceptance gate: agency_disambiguation cohort must be "
        f">= {SC013_MIN_AGENCY_ENTRIES}, got {len(entries)}"
    )


def test_sc013_agency_entries_have_required_fields(golden_set: dict) -> None:
    """Each agency entry has ``expected_agency`` + ``expected_agency_role`` for
    the precision-evaluator to compare against."""
    entries = _by_scenario(golden_set, "agency_disambiguation")
    for entry in entries:
        assert entry.get("expected_agency"), f"missing expected_agency in {entry['id']}"
        assert entry.get("expected_agency_role"), f"missing expected_agency_role in {entry['id']}"


def test_sc015_act_national_institution_minimum_size(golden_set: dict) -> None:
    """SC-015 gate: golden-set-v1 carries ≥20 authority_precedence entries
    (T190). CI fails if the fixture is dropped below the floor."""
    entries = _by_scenario(golden_set, "authority_precedence")
    assert len(entries) >= SC015_MIN_PRECEDENCE_ENTRIES, (
        f"SC-015 acceptance gate: authority_precedence cohort must be "
        f">= {SC015_MIN_PRECEDENCE_ENTRIES}, got {len(entries)}"
    )


def test_sc015_act_national_institution_commonwealth_majority(golden_set: dict) -> None:
    """At least one Commonwealth doctrine entry per top-tier national institution
    (Parliament House, ADF Russell, embassies, AIATSIS) for SC-015 baseline."""
    entries = _by_scenario(golden_set, "authority_precedence")
    act_cwlth = [
        e for e in entries if e.get("jurisdiction") == "act" and e.get("expected_authority_level") == "commonwealth"
    ]
    assert len(act_cwlth) >= 6, (
        f"SC-015 baseline: ACT-Commonwealth coverage must be >= 6 anchor "
        f"institutions (Parliament, Defence, embassies, AIATSIS, NatLib, NMA, "
        f"High Court, ASIO), got {len(act_cwlth)}"
    )


def test_acceptance_gate_floor_constants_documented() -> None:
    """The SC-013 + SC-015 95% precision floors are codified — drift in this
    constant requires Constitution-level review (Pass 1 Q-P1-08)."""
    assert SC013_PRECISION_FLOOR == 0.95
    assert SC015_PRECISION_FLOOR == 0.95

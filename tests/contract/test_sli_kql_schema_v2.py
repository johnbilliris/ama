"""Wave C / T-AA16 — SLI KQL schema v2 contract test.

Asserts that for every SLI in the bundle:

* ``id`` and ``kql`` keys exist and are non-empty strings;
* ``fr_refs`` and ``sc_refs`` are lists.

For the Cycle 2 additions (Z6 + Z7) it further asserts:

* ``sample_count`` column appears in the KQL string (CHK117 floor evidence);
* Z6 carries SC-001 cross-reference;
* Z7 carries SC-010 cross-reference;
* both use a 24 h trailing window (``ago(24h)``).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_SLI_PATH = Path(__file__).resolve().parents[2] / "infra" / "observability" / "sli-kql.json"


@pytest.fixture(scope="module")
def sli_doc() -> dict:
    return json.loads(_SLI_PATH.read_text(encoding="utf-8"))


def test_sli_doc_has_seven_slis_after_cycle_2(sli_doc: dict) -> None:
    assert len(sli_doc["slis"]) == 7
    ids = [s["id"] for s in sli_doc["slis"]]
    for required in ("SLI-Z1", "SLI-Z2", "SLI-Z3", "SLI-Z4", "SLI-Z5", "SLI-Z6", "SLI-Z7"):
        assert required in ids


def test_z6_kql_includes_sample_count(sli_doc: dict) -> None:
    z6 = next(s for s in sli_doc["slis"] if s["id"] == "SLI-Z6")
    assert "sample_count" in z6["kql"]
    assert "ago(24h)" in z6["kql"]
    assert "SC-001" in z6["sc_refs"]


def test_z7_kql_includes_sample_count(sli_doc: dict) -> None:
    z7 = next(s for s in sli_doc["slis"] if s["id"] == "SLI-Z7")
    assert "sample_count" in z7["kql"]
    assert "ago(24h)" in z7["kql"]
    assert "SC-010" in z7["sc_refs"]


def test_every_sli_has_required_top_level_keys(sli_doc: dict) -> None:
    for sli in sli_doc["slis"]:
        for key in ("id", "kql", "fr_refs", "sc_refs"):
            assert key in sli, f"{sli.get('id', '?')} missing key {key}"
        assert isinstance(sli["fr_refs"], list)
        assert isinstance(sli["sc_refs"], list)
        assert isinstance(sli["kql"], str) and sli["kql"]


def test_z6_thresholds_match_sli_thresholds_md(sli_doc: dict) -> None:
    z6 = next(s for s in sli_doc["slis"] if s["id"] == "SLI-Z6")
    assert z6["warn_threshold_ms_gpt4o"] == 4000
    assert z6["breach_threshold_ms_gpt4o"] == 5000
    assert z6["warn_threshold_ms_gpt4omini"] == 1500
    assert z6["breach_threshold_ms_gpt4omini"] == 2000


def test_z7_thresholds_match_sli_thresholds_md(sli_doc: dict) -> None:
    z7 = next(s for s in sli_doc["slis"] if s["id"] == "SLI-Z7")
    # Cycle 3 / T-AA34 / A3-06 — distinct warn / breach bands. Warn at
    # 99.5 % (per `sli-thresholds.md` §6b row "Target / Warn"); breach
    # at 99.0 % (per row "Breach"). The prior Cycle 2 value of 99.5 for
    # `breach_pct` collapsed both bands; Cycle 3 corrects this.
    assert z7["warn_pct"] == 99.5
    assert z7["breach_pct"] == 99.0
    assert z7["breach_threshold_ms"] == 1500


def test_every_sli_kql_canonicalises_to_contract_canonical(sli_doc: dict) -> None:
    """Cycle 3 / T-AA33 / A3-05 / FR-073 — belt-and-braces canonical match.

    Mirrors `tests/contract/test_sli_kql_canonical_match.py` (T-AA32) so a
    single ``pytest tests/contract/test_sli_kql_schema_v2.py -q`` invocation
    validates BOTH the schema shape AND the canonical alignment between
    `infra/observability/sli-kql.json` and
    `specs/036-sim-agent-extend/contracts/sli-thresholds.md` for every
    SLI in the registry.

    The dedicated parametric test in T-AA32 remains the focused contract;
    this assertion is a redundant gate so a future refactor that touches
    only the schema test still triggers canonical-drift detection.
    """

    # Local import to avoid coupling to the canonicaliser surface for
    # callers that import the fixture above without exercising this test.
    from tests.contract._kql_canonicaliser import (
        canonical_kql_for_sli,
        canonicalise_kql,
    )

    for sli in sli_doc["slis"]:
        impl_canonical = canonicalise_kql(sli["kql"])
        contract_canonical = canonical_kql_for_sli(sli["id"])
        assert impl_canonical == contract_canonical, (
            f"FR-073 drift detected via schema-v2 test for {sli['id']}; "
            "see tests/contract/test_sli_kql_canonical_match.py for the "
            "focused parametric contract."
        )

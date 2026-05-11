"""Cycle 3 / T-AA32 / A3-05 / FR-073 — parametric per-SLI canonical-match contract test.

The FR-073 contract enforcer: byte-equality between every implementation
KQL in ``infra/observability/sli-kql.json`` and the canonical body for the
same SLI in ``specs/036-sim-agent-extend/contracts/sli-thresholds.md``,
after the six-step canonicalisation pipeline (PD-C3-01).

Pass-1 Q5 mandate (`spec.md:1183-1250`): parametric symmetry over all 7
SLIs, NO ``pytest.mark.xfail``, NO ``@pytest.mark.skip``, NO hard-coded
subset (the parametrisation expression is dynamic — any SLI added to
``sli-kql.json`` post-Cycle-3 automatically participates).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.contract._kql_canonicaliser import (
    canonical_kql_for_sli,
    canonicalise_kql,
)

# Mirrors the established `_SLI_PATH` pattern at
# tests/contract/test_sli_kql_schema_v2.py:25.
_SLI_PATH = (
    Path(__file__).resolve().parents[2]
    / "infra"
    / "observability"
    / "sli-kql.json"
)
_SLI_DOC = json.loads(_SLI_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "sli_id",
    [s["id"] for s in _SLI_DOC["slis"]],
)
def test_implementation_kql_matches_canonical_after_canonicalisation(
    sli_id: str,
) -> None:
    """Every SLI's implementation KQL canonicalises to the contract form.

    Drift between ``sli-kql.json[<sli_id>].kql`` and the matching fenced
    block in ``contracts/sli-thresholds.md`` MUST surface as a failure
    here — Pass-2 Q3 (`spec.md:1484-1577`) bans suppression decorators,
    so any drift is a hard contract failure (FR-073 invariant).
    """

    impl_entry = next(s for s in _SLI_DOC["slis"] if s["id"] == sli_id)
    impl_canonical = canonicalise_kql(impl_entry["kql"])
    contract_canonical = canonical_kql_for_sli(sli_id)
    assert impl_canonical == contract_canonical, (
        f"FR-073 drift: sli-kql.json[{sli_id}].kql does NOT canonicalise "
        f"to contracts/sli-thresholds.md canonical block for {sli_id}.\n"
        f"--- implementation canonical ---\n{impl_canonical}\n"
        f"--- contract canonical ---\n{contract_canonical}\n"
    )

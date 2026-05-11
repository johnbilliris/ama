"""Wave C / T-AA18 — workbook row-group contract test.

Asserts that ``infra/bicep/modules/observability-workbook-sim-slis.bicep``
contains a "SC-013 staging-promotion" row group with the Z6 and Z7 KQL
queries.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest

_BICEP_PATH = (
    Path(__file__).resolve().parents[2] / "infra" / "bicep" / "modules" / "observability-workbook-sim-slis.bicep"
)


@pytest.fixture(scope="module")
def bicep_text() -> str:
    return _BICEP_PATH.read_text(encoding="utf-8")


def test_workbook_module_exists(bicep_text: str) -> None:
    assert _BICEP_PATH.is_file()
    assert len(bicep_text) > 100


def test_workbook_row_group_named_sc_013_staging_promotion(bicep_text: str) -> None:
    assert "SC-013 staging-promotion" in bicep_text


def test_workbook_contains_z6_and_z7_queries(bicep_text: str) -> None:
    assert "SLI-Z6" in bicep_text
    assert "SLI-Z7" in bicep_text
    assert "sub_agent.invocation.complete" in bicep_text
    assert "sse.map_overlay.delivered" in bicep_text


def test_workbook_uses_24h_trailing_window(bicep_text: str) -> None:
    # Both queries use ago(24h)
    assert bicep_text.count("ago(24h)") >= 2

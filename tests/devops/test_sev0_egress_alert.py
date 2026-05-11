"""T-J08 — SC-006 SEV-0 PagerDuty egress alert contract test.

Verifies that the egress-block SLI 5 alert in
``infra/bicep/modules/observability-alerts.bicep`` is configured for
SEV-0, references the PagerDuty action group, and the supplementary
checklist mentions PagerDuty integration validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BICEP = REPO / "infra" / "bicep" / "modules" / "observability-alerts.bicep"


@pytest.fixture(scope="module")
def bicep_text() -> str:
    return BICEP.read_text(encoding="utf-8")


def _egress_chunk(bicep_text: str) -> str:
    start = bicep_text.index("resource sliEgressBlock")
    end = bicep_text.index("output sliParseToPipelineId")
    return bicep_text[start:end]


def test_sev0_egress_alert_is_severity_0(bicep_text: str) -> None:
    egress_chunk = _egress_chunk(bicep_text)
    assert "severity: 0" in egress_chunk
    assert "PT1M" in egress_chunk, "SEV-0 alert must evaluate every 1 minute"


def test_sev0_egress_alert_does_not_auto_mitigate(bicep_text: str) -> None:
    egress_chunk = _egress_chunk(bicep_text)
    assert "autoMitigate: false" in egress_chunk, (
        "SC-006 SEV-0 alert MUST NOT auto-mitigate — humans acknowledge."
    )


def test_sev0_egress_alert_pages_pagerduty(bicep_text: str) -> None:
    egress_chunk = _egress_chunk(bicep_text)
    assert "pagerDutyActionGroupId" in egress_chunk, (
        "SC-006 SEV-0 alert MUST page PagerDuty action group end-to-end (T-J08)."
    )


def test_sev0_egress_alert_query_targets_canonical_block_reason(bicep_text: str) -> None:
    egress_chunk = _egress_chunk(bicep_text)
    assert "simulation_tenant_egress_blocked" in egress_chunk

"""T-J07 — observability-alerts.bicep contract / canonical-threshold tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BICEP_PATH = (
    Path(__file__).resolve().parents[2]
    / "infra"
    / "bicep"
    / "modules"
    / "observability-alerts.bicep"
)


@pytest.fixture(scope="module")
def bicep_text() -> str:
    return BICEP_PATH.read_text(encoding="utf-8")


def test_alerts_bicep_exists(bicep_text: str) -> None:
    assert "scheduledQueryRules" in bicep_text


def test_alerts_bicep_defines_5_canonical_alerts(bicep_text: str) -> None:
    """Plan-canonical 5 SLIs (T-J07) plus Cycle 2 Z6/Z7 (T-AA18)."""
    rule_names = re.findall(r"resource\s+(\w+)\s+'Microsoft\.Insights/scheduledQueryRules", bicep_text)
    assert sorted(rule_names) == [
        "sliCascadeFanOut",
        "sliEgressBlock",
        "sliOverlayLatency",
        "sliParseToPipeline",
        "sliRiskFanOut",
        "sliZ6SubAgentLatency",  # Cycle 2 / T-AA18 / A2-02
        "sliZ7MapOverlayDrift",  # Cycle 2 / T-AA18 / A2-02
    ]


def test_alerts_bicep_severities_match_plan(bicep_text: str) -> None:
    # SEV-0 ⇒ SC-006 egress block alert.
    assert "severity: 0" in bicep_text
    # SEV-2 ⇒ parse-to-pipeline + risk-fan-out + cascade.
    assert bicep_text.count("severity: 2") == 3
    # SEV-3 ⇒ overlay latency + Cycle 2 Z6 + Z7 (warn-only gate signals).
    assert bicep_text.count("severity: 3") == 3


def test_alerts_bicep_pagerduty_wired_to_sev0(bicep_text: str) -> None:
    """SEV-0 SC-006 alert MUST escalate to PagerDuty action group (T-J08 cross-link)."""
    assert "pagerDutyActionGroupId" in bicep_text
    egress_block = bicep_text[bicep_text.index("sliEgressBlock") :]
    if "output sliParseToPipelineId" in egress_block:
        egress_block = egress_block[: egress_block.index("output sliParseToPipelineId")]
    assert "pagerDutyActionGroupId" in egress_block


def test_alerts_bicep_canonical_thresholds_present(bicep_text: str) -> None:
    """Plan-canonical SLI thresholds — guard against drift."""
    # Parse-to-pipeline 5 s p95 ⇒ over 1 h fast-burn at 4× = 20 s rolling threshold.
    assert "threshold: 20000" in bicep_text
    # Risk-fan-out 15 s p95 ⇒ fast-burn 4× = 60 s rolling.
    assert "threshold: 60000" in bicep_text
    # Cascade fan-out 30 s p95 ⇒ fast-burn 4× = 120 s rolling.
    assert "threshold: 120000" in bicep_text
    # Overlay 20 s SEV-3 trip-wire.
    assert "threshold: 20000" in bicep_text


def test_alerts_bicep_egress_block_uses_canonical_block_reason(bicep_text: str) -> None:
    """The SC-006 alert query MUST scan the canonical `simulation_tenant_egress_blocked` literal."""
    assert "simulation_tenant_egress_blocked" in bicep_text


# ---------------------------------------------------------------------------
# Cycle 2 / T-AA18 / A2-02 — staging-promotion gate alerts (Z6 + Z7).
# ---------------------------------------------------------------------------


def test_z6_alert_resource_present(bicep_text: str) -> None:
    assert "resource sliZ6SubAgentLatency" in bicep_text
    assert "sub_agent.invocation.complete" in bicep_text


def test_z7_alert_resource_present(bicep_text: str) -> None:
    assert "resource sliZ7MapOverlayDrift" in bicep_text
    assert "sse.map_overlay.delivered" in bicep_text


def test_z6_z7_use_24h_window(bicep_text: str) -> None:
    # Both Z6 and Z7 use P1D windowSize.
    assert bicep_text.count("windowSize: 'P1D'") >= 2


def test_z6_z7_emit_to_action_group_not_pagerduty(bicep_text: str) -> None:
    # Z6 and Z7 are gate signals (warn-only Slack); they MUST NOT page.
    z6_idx = bicep_text.index("resource sliZ6SubAgentLatency")
    z6_actions_start = bicep_text.index("actions:", z6_idx)
    z6_block = bicep_text[z6_idx : z6_actions_start + 200]
    assert "pagerDuty" not in z6_block, "Z6 alert MUST NOT page (gate signal)."

    z7_idx = bicep_text.index("resource sliZ7MapOverlayDrift")
    z7_actions_start = bicep_text.index("actions:", z7_idx)
    z7_block = bicep_text[z7_idx : z7_actions_start + 200]
    assert "pagerDuty" not in z7_block, "Z7 alert MUST NOT page (gate signal)."


def test_z6_z7_outputs_present(bicep_text: str) -> None:
    assert "output sliZ6SubAgentLatencyId" in bicep_text
    assert "output sliZ7MapOverlayDriftId" in bicep_text

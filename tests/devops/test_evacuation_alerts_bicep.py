"""Contract tests for the twelve evacuation Azure Monitor alert rules."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ALERTS_PATH = ROOT / "infra" / "bicep" / "modules" / "evacuation-alerts.bicep"
MAIN_PATH = ROOT / "infra" / "main.bicep"


@pytest.fixture(scope="module")
def alerts_text() -> str:
    return ALERTS_PATH.read_text(encoding="utf-8")


def test_uses_pinned_scheduled_query_rule_avm(alerts_text: str) -> None:
    assert "br/public:avm/res/insights/scheduled-query-rule:0.6.0" in alerts_text
    assert "Microsoft.Insights/scheduledQueryRules@" not in alerts_text


def test_defines_exactly_twelve_alerts(alerts_text: str) -> None:
    names = re.findall(r"name: '(alert-evac-[^']+)'", alerts_text)
    assert names == [
        "alert-evac-plan-sla-warning",
        "alert-evac-plan-sla-critical",
        "alert-evac-replan-sla",
        "alert-evac-road-data-stale",
        "alert-evac-llm-unavailable",
        "alert-evac-audit-degradation",
        "alert-evac-audit-buffer-capacity",
        "alert-evac-shelter-rate",
        "alert-evac-emergency-escalation",
        "alert-evac-no-plans",
        "alert-evac-congestion-risk",
        "alert-evac-capacity-limit",
    ]


def test_queries_use_real_instrument_names(alerts_text: str) -> None:
    expected_metrics = {
        "evacuation.plan_generation_latency",
        "evacuation.replan_latency",
        "evacuation.road_data_stale",
        "evacuation.fallback_mode_activations",
        "evacuation.audit_tier",
        "evacuation.audit_buffer_depth",
        "evacuation.shelter_in_place_count",
        "evacuation.emergency_escalation_count",
        "evacuation.handoff_intake_count",
        "evacuation.active_plans_gauge",
        "evacuation.congestion_risk_routes",
        "evacuation.routes_per_plan",
    }
    assert expected_metrics.issubset(set(re.findall(r"evacuation\.[a-z_]+", alerts_text)))
    assert "capacity_utilisation_pct" not in alerts_text
    assert "vulnerability_category" not in alerts_text
    assert "estimated_vehicles" not in alerts_text


def test_thresholds_and_windows_match_contract(alerts_text: str) -> None:
    for threshold in (30000, 15000, 8000, 50, 40):
        assert f"threshold: {threshold}" in alerts_text
    for window in ("PT5M", "PT10M", "PT15M", "PT30M"):
        assert f"windowSize: '{window}'" in alerts_text
    assert "percentile(todouble(value), 95)" in alerts_text
    assert "sum(todouble(value))" in alerts_text
    assert "100.0 * RiskRoutes / TotalRoutes" in alerts_text
    assert "Handoffs" in alerts_text and "ActivePlans" in alerts_text


def test_rules_preserve_australian_scope_and_action_wiring(alerts_text: str) -> None:
    assert "'australiaeast'" in alerts_text
    assert "australiasoutheast" not in alerts_text
    assert "appInsights.id" in alerts_text
    assert "actionGroupResourceIds" in alerts_text
    assert "dataResidency: location" in alerts_text


def test_main_deploys_and_exports_evacuation_alerts() -> None:
    main_text = MAIN_PATH.read_text(encoding="utf-8")
    assert "module evacuationAlerts './bicep/modules/evacuation-alerts.bicep'" in main_text
    assert "appInsightsName: monitoring.outputs.appInsightsName" in main_text
    assert "actionGroupResourceId: monitoring.outputs.actionGroupId" in main_text
    assert "AZURE_EVACUATION_ALERT_RULE_IDS" in main_text

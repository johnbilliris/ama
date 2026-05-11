"""Unit tests for dashboard role-to-widget config resolution (T080)."""

from apps.api.app.api.routes.governance_dashboard import (
    ROLE_WIDGET_CONFIGS,
    _resolve_widget_layout,
)
from packages.domain.src.domain.models.dashboard_widget_config import AIIMS_AUTHORITY_RANKS


class TestRoleWidgetConfig:
    def test_all_10_roles_configured(self):
        """All 10 AIIMS roles plus field_coordinator have widget configurations."""
        expected_roles = {
            "incident_controller",
            "operations_officer",
            "planning_officer",
            "intelligence_officer",
            "logistics_officer",
            "public_information_officer",
            "executive_leader",
            "observer_auditor",
            "risk_manager",
            "resilience_planner",
            "field_coordinator",
        }
        assert set(ROLE_WIDGET_CONFIGS.keys()) == expected_roles

    def test_incident_controller_default_view(self):
        config = ROLE_WIDGET_CONFIGS["incident_controller"]
        assert config["default_view"] == "executive_summary"

    def test_planning_officer_default_view(self):
        config = ROLE_WIDGET_CONFIGS["planning_officer"]
        assert config["default_view"] == "operational_readiness"

    def test_observer_auditor_default_view(self):
        config = ROLE_WIDGET_CONFIGS["observer_auditor"]
        assert config["default_view"] == "audit_trail"

    def test_public_info_officer_default_view(self):
        config = ROLE_WIDGET_CONFIGS["public_information_officer"]
        assert config["default_view"] == "risk_warning"

    def test_risk_manager_default_view(self):
        config = ROLE_WIDGET_CONFIGS["risk_manager"]
        assert config["default_view"] == "risk_warning"

    def test_single_role_resolution(self):
        widgets, view = _resolve_widget_layout(["incident_controller"])
        assert view == "executive_summary"
        # T-AA06 — explicit boundary: the incident_controller role MUST
        # surface at least its 4 mandated panels (situation, resources,
        # public-warnings, action-board) per plan.md §3.2.
        assert len(widgets) >= 4, (
            f"incident_controller resolved to only {len(widgets)} widgets; "
            f"expected ≥4"
        )

    def test_multi_role_merge(self):
        """Multi-role produces union of widgets ordered by highest authority."""
        widgets_single, _ = _resolve_widget_layout(["observer_auditor"])
        widgets_multi, view = _resolve_widget_layout(["observer_auditor", "incident_controller"])
        # Multi-role should have at least as many widgets as highest-authority single role
        assert view == "executive_summary"  # Incident controller has rank 1
        assert len(widgets_multi) >= len(widgets_single)

    def test_multi_role_ordered_by_authority(self):
        """Primary role should be the one with lowest authority_rank (highest authority)."""
        widgets, view = _resolve_widget_layout(["observer_auditor", "executive_leader"])
        # Executive leader (rank 2) should be primary over observer (rank 10)
        assert view == "executive_summary"

    def test_no_role_empty_layout(self):
        widgets, view = _resolve_widget_layout([])
        assert len(widgets) == 0
        assert view == "executive_summary"  # default

    def test_unknown_role_empty_layout(self):
        widgets, view = _resolve_widget_layout(["unknown_role"])
        assert len(widgets) == 0

    def test_all_roles_have_widgets(self):
        """Every configured role must have at least one widget."""
        for role in ROLE_WIDGET_CONFIGS:
            widgets, _ = _resolve_widget_layout([role])
            assert len(widgets) > 0, f"Role {role} has no widgets"

    def test_authority_ranks_match(self):
        """Verify authority ranks match plan.md hierarchy."""
        assert AIIMS_AUTHORITY_RANKS["incident_controller"] == 1
        assert AIIMS_AUTHORITY_RANKS["executive_leader"] == 2
        assert AIIMS_AUTHORITY_RANKS["observer_auditor"] == 10

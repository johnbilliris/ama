"""Unit tests for dashboard audit logging (T086)."""

import pytest
from datetime import datetime, UTC

from packages.domain.src.domain.models.governance_audit import GovernanceAction, GovernanceAuditEntry


class TestDashboardAuditActions:
    """Verify dashboard audit action types are properly defined."""

    DASHBOARD_ACTIONS = [
        "dashboard_view",
        "dashboard_filter",
        "dashboard_search",
        "dashboard_export",
        "dashboard_drill_down",
        "dashboard_navigate_to_crud",
    ]

    def test_all_dashboard_actions_are_valid(self):
        """All 6 dashboard action types must be valid GovernanceAction values."""
        for action in self.DASHBOARD_ACTIONS:
            entry = GovernanceAuditEntry(
                audit_entry_id=f"audit-test-{action}",
                data_source_id="dashboard",
                action=action,
                actor_id="test-user",
                timestamp=datetime.now(UTC),
                tenant_id="live",
                view_context="executive_summary",
                session_id="session-123",
            )
            assert entry.action == action

    def test_dashboard_view_action(self):
        entry = GovernanceAuditEntry(
            audit_entry_id="audit-001",
            data_source_id="dashboard",
            action="dashboard_view",
            actor_id="user-001",
            timestamp=datetime.now(UTC),
            details={"view": "executive_summary"},
            tenant_id="live",
            view_context="executive_summary",
            session_id="sess-001",
        )
        assert entry.action == "dashboard_view"
        assert entry.tenant_id == "live"
        assert entry.view_context == "executive_summary"
        assert entry.session_id == "sess-001"

    def test_dashboard_filter_action(self):
        entry = GovernanceAuditEntry(
            audit_entry_id="audit-002",
            data_source_id="dashboard",
            action="dashboard_filter",
            actor_id="user-001",
            timestamp=datetime.now(UTC),
            details={"view": "compliance", "filters": {"status": "non_compliant"}},
        )
        assert entry.action == "dashboard_filter"

    def test_dashboard_export_action(self):
        entry = GovernanceAuditEntry(
            audit_entry_id="audit-003",
            data_source_id="dashboard",
            action="dashboard_export",
            actor_id="user-001",
            timestamp=datetime.now(UTC),
            details={"format": "csv", "record_count": 50},
        )
        assert entry.action == "dashboard_export"

    def test_dashboard_navigate_to_crud_action(self):
        entry = GovernanceAuditEntry(
            audit_entry_id="audit-004",
            data_source_id="dashboard",
            action="dashboard_navigate_to_crud",
            actor_id="user-001",
            timestamp=datetime.now(UTC),
            details={"target_url": "/governance/ds-001/compliance", "intent": "reassessment"},
        )
        assert entry.action == "dashboard_navigate_to_crud"

    def test_tenant_id_defaults_to_live(self):
        entry = GovernanceAuditEntry(
            audit_entry_id="audit-005",
            data_source_id="dashboard",
            action="dashboard_view",
            actor_id="user-001",
            timestamp=datetime.now(UTC),
        )
        assert entry.tenant_id == "live"

    def test_optional_fields_nullable(self):
        entry = GovernanceAuditEntry(
            audit_entry_id="audit-006",
            data_source_id="dashboard",
            action="dashboard_view",
            actor_id="user-001",
            timestamp=datetime.now(UTC),
        )
        assert entry.view_context is None
        assert entry.session_id is None

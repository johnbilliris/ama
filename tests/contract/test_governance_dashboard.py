from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_registry import GovernanceRegistryService

from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource


@pytest.fixture
def service() -> GovernanceRegistryService:
    return GovernanceRegistryService(GovernanceRepository())


def _register(service: GovernanceRegistryService, ds_id: str = "", kind: str = "authoritative") -> DataSource:
    ds_id = ds_id or f"ds-{uuid4().hex[:12]}"
    return service.register_source(DataSource(
        data_source_id=ds_id, name=f"Source {ds_id}", kind=kind,
        sub_category="weather_climate", provider="Test",
        trust_tier="tier_1_authoritative_government",
    ), actor_id="t")


def _assess(service: GovernanceRegistryService, ds_id: str, status: str = "compliant", **kw) -> None:
    defaults = {
        "assessment_id": f"a-{uuid4().hex[:8]}", "data_source_id": ds_id,
        "principle": "life_safety_first", "compliance_status": status,
        "explanation": "test", "assessor_id": "lead",
        "assessed_at": datetime.now(UTC),
    }
    defaults.update(kw)
    service.create_assessment(ConstitutionalAssessment(**defaults), actor_id="lead")


class TestDashboardSummary:
    def test_empty_dashboard(self, service: GovernanceRegistryService) -> None:
        summary = service.get_dashboard_summary()
        assert summary["total_sources"] == 0

    def test_counts_by_compliance_status(self, service: GovernanceRegistryService) -> None:
        s1 = _register(service)
        s2 = _register(service)
        _register(service)
        _assess(service, s1.data_source_id, "compliant")
        _assess(service, s2.data_source_id, "non_compliant", gaps=["gap1"])
        summary = service.get_dashboard_summary()
        assert summary["total_sources"] == 3
        assert summary["compliant"] == 1
        assert summary["non_compliant"] == 1
        assert summary["unassessed"] == 1

    def test_deactivated_excluded_from_counts(self, service: GovernanceRegistryService) -> None:
        s1 = _register(service)
        service.deactivate_source(s1.data_source_id, actor_id="t")
        summary = service.get_dashboard_summary()
        assert summary["total_sources"] == 0


class TestGovernanceGaps:
    def test_detects_unassessed_sources(self, service: GovernanceRegistryService) -> None:
        _register(service, ds_id="ds-unassessed")
        gaps = service.detect_governance_gaps()
        gap_ids = [g["data_source_id"] for g in gaps if g["gap"] == "no_assessment"]
        assert "ds-unassessed" in gap_ids

    def test_detects_unassigned_sources(self, service: GovernanceRegistryService) -> None:
        src = _register(service, ds_id="ds-unassigned")
        _assess(service, src.data_source_id)
        gaps = service.detect_governance_gaps()
        gap_ids = [g["data_source_id"] for g in gaps if g["gap"] == "no_assignment"]
        assert "ds-unassigned" in gap_ids


class TestAuditTrail:
    def test_audit_trail_records_all_actions(self, service: GovernanceRegistryService) -> None:
        src = _register(service)
        _assess(service, src.data_source_id)
        trail = service.get_audit_trail(src.data_source_id)
        actions = [e.action for e in trail]
        assert "registered" in actions
        assert "assessment_created" in actions

    def test_audit_trail_filter_by_action(self, service: GovernanceRegistryService) -> None:
        src = _register(service)
        _assess(service, src.data_source_id)
        trail = service.get_audit_trail(src.data_source_id, action="registered")
        assert all(e.action == "registered" for e in trail)

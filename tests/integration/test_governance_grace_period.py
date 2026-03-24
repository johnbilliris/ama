from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_registry import GovernanceRegistryService
from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource


@pytest.fixture
def service() -> GovernanceRegistryService:
    return GovernanceRegistryService(GovernanceRepository())


def _register_and_approve(service: GovernanceRegistryService) -> DataSource:
    src = DataSource(
        data_source_id=f"ds-{uuid4().hex[:12]}", name="Test", kind="authoritative",
        sub_category="weather_climate", provider="BoM",
        trust_tier="tier_1_authoritative_government",
    )
    service.register_source(src, actor_id="t")
    service.create_assessment(ConstitutionalAssessment(
        assessment_id=f"a-{uuid4().hex[:8]}", data_source_id=src.data_source_id,
        principle="life_safety_first", compliance_status="compliant",
        explanation="OK", assessor_id="lead", assessed_at=datetime.now(UTC),
    ), actor_id="lead")
    return service.get_source(src.data_source_id)


class TestReReviewOnSourceChange:
    def test_update_triggers_rereview_audit(self, service: GovernanceRegistryService) -> None:
        src = _register_and_approve(service)
        service.update_source(src.data_source_id, {"provider": "New Provider"}, actor_id="t")
        trail = service.get_audit_trail(src.data_source_id)
        rereview_entries = [e for e in trail if e.action == "rereview_triggered"]
        assert len(rereview_entries) >= 1


class TestConstitutionAmendmentReReview:
    def test_amendment_flags_all_sources(self, service: GovernanceRegistryService) -> None:
        _register_and_approve(service)
        _register_and_approve(service)
        flagged = service.trigger_constitution_amendment_rereview(actor_id="safety-lead")
        assert flagged == 2


class TestGracePeriodLifecycle:
    def test_start_grace_period(self, service: GovernanceRegistryService) -> None:
        src = _register_and_approve(service)
        result = service.start_grace_period(src.data_source_id, actor_id="lead")
        assert result.compliance_status == "compliance_lapsed"
        assert result.grace_period_end is not None

    def test_extend_grace_period(self, service: GovernanceRegistryService) -> None:
        src = _register_and_approve(service)
        service.start_grace_period(src.data_source_id, actor_id="lead")
        original = service.get_source(src.data_source_id)
        result = service.extend_grace_period(src.data_source_id, 24, actor_id="lead")
        assert result.grace_period_end > original.grace_period_end

    def test_immediate_block(self, service: GovernanceRegistryService) -> None:
        src = _register_and_approve(service)
        service.start_grace_period(src.data_source_id, actor_id="lead")
        result = service.block_source_immediately(src.data_source_id, actor_id="lead")
        assert result.compliance_status == "non_compliant"
        assert result.grace_period_end is None

    def test_auto_block_on_expiry(self, service: GovernanceRegistryService) -> None:
        src = _register_and_approve(service)
        service.start_grace_period(src.data_source_id, actor_id="lead", grace_hours=0)
        expired_source = service.get_source(src.data_source_id)
        expired_source.grace_period_end = datetime.now(UTC) - timedelta(hours=1)
        service._repo.save_source(expired_source)
        blocked = service.check_expired_grace_periods()
        assert src.data_source_id in blocked
        final = service.get_source(src.data_source_id)
        assert final.compliance_status == "non_compliant"

    def test_extend_non_lapsed_raises_409(self, service: GovernanceRegistryService) -> None:
        src = _register_and_approve(service)
        with pytest.raises(Exception, match="not in compliance_lapsed"):
            service.extend_grace_period(src.data_source_id, 24, actor_id="lead")

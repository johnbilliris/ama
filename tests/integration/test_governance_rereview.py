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


def _register_source(service: GovernanceRegistryService) -> DataSource:
    src = DataSource(
        data_source_id=f"ds-{uuid4().hex[:12]}",
        name="Test",
        kind="authoritative",
        sub_category="weather_climate",
        provider="BoM",
        trust_tier="tier_1_authoritative_government",
    )
    return service.register_source(src, actor_id="t")


class TestReReviewOnSourceChange:
    def test_material_update_triggers_rereview(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        service.create_assessment(
            ConstitutionalAssessment(
                assessment_id=f"a-{uuid4().hex[:8]}",
                data_source_id=src.data_source_id,
                principle="life_safety_first",
                compliance_status="compliant",
                explanation="OK",
                assessor_id="lead",
                assessed_at=datetime.now(UTC),
            ),
            actor_id="lead",
        )
        service.update_source(src.data_source_id, {"collection_method": "push_webhook"}, actor_id="t")
        trail = service.get_audit_trail(src.data_source_id, action="rereview_triggered")
        assert len(trail) >= 1
        assert trail[0].details.get("triggered_by") == "source_change"


class TestConstitutionAmendmentReReview:
    def test_flags_all_assessed_sources(self, service: GovernanceRegistryService) -> None:
        src1 = _register_source(service)
        src2 = _register_source(service)
        for src in [src1, src2]:
            service.create_assessment(
                ConstitutionalAssessment(
                    assessment_id=f"a-{uuid4().hex[:8]}",
                    data_source_id=src.data_source_id,
                    principle="cloud_platform",
                    compliance_status="compliant",
                    explanation="Azure AU only",
                    assessor_id="lead",
                    assessed_at=datetime.now(UTC),
                ),
                actor_id="lead",
            )
        flagged = service.trigger_constitution_amendment_rereview(actor_id="safety-lead")
        assert flagged == 2

    def test_does_not_flag_unassessed_sources(self, service: GovernanceRegistryService) -> None:
        _register_source(service)
        flagged = service.trigger_constitution_amendment_rereview(actor_id="safety-lead")
        assert flagged == 0

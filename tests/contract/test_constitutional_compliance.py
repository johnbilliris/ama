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


def _register_source(service: GovernanceRegistryService, ds_id: str = "") -> DataSource:
    ds_id = ds_id or f"ds-{uuid4().hex[:12]}"
    source = DataSource(
        data_source_id=ds_id, name="Test", kind="authoritative",
        sub_category="weather_climate", provider="BoM",
        trust_tier="tier_1_authoritative_government",
    )
    return service.register_source(source, actor_id="tester")


def _make_assessment(
    data_source_id: str,
    principle: str = "life_safety_first",
    status: str = "compliant",
    **kw,
) -> ConstitutionalAssessment:
    defaults = {
        "assessment_id": f"assess-{uuid4().hex[:12]}",
        "data_source_id": data_source_id,
        "principle": principle,
        "compliance_status": status,
        "explanation": "Test explanation",
        "assessor_id": "governance-lead",
        "assessed_at": datetime.now(UTC),
    }
    defaults.update(kw)
    return ConstitutionalAssessment(**defaults)


class TestAssessmentCreation:
    def test_create_compliant_assessment(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        assessment = _make_assessment(src.data_source_id)
        result = service.create_assessment(assessment, actor_id="tester")
        assert result.is_current is True
        assert result.compliance_status == "compliant"

    def test_partially_compliant_requires_conditions(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        assessment = _make_assessment(src.data_source_id, status="partially_compliant", gaps=["gap1"])
        with pytest.raises(Exception, match="Conditions required"):
            service.create_assessment(assessment, actor_id="tester")

    def test_non_compliant_requires_gaps(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        assessment = _make_assessment(src.data_source_id, status="non_compliant")
        with pytest.raises(Exception, match="Gaps required"):
            service.create_assessment(assessment, actor_id="tester")


class TestAssessmentSupersession:
    def test_new_assessment_supersedes_old(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        old = _make_assessment(src.data_source_id, assessment_id="assess-old")
        service.create_assessment(old, actor_id="tester")

        new = _make_assessment(src.data_source_id, assessment_id="assess-new")
        service.create_assessment(new, actor_id="tester")

        profile = service.get_compliance_profile(src.data_source_id)
        current_ids = [a.assessment_id for a in profile["current_assessments"]]
        assert "assess-new" in current_ids
        assert "assess-old" not in current_ids


class TestComplianceDerivation:
    def test_non_compliant_assessment_sets_source_non_compliant(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        assessment = _make_assessment(
            src.data_source_id, status="non_compliant",
            gaps=["privacy concern"], explanation="PII exposed",
        )
        service.create_assessment(assessment, actor_id="tester")
        updated = service.get_source(src.data_source_id)
        assert updated.compliance_status == "non_compliant"

    def test_all_compliant_sets_source_compliant(self, service: GovernanceRegistryService) -> None:
        src = _register_source(service)
        for p in ["life_safety_first", "cloud_platform"]:
            service.create_assessment(_make_assessment(src.data_source_id, principle=p), actor_id="t")
        updated = service.get_source(src.data_source_id)
        assert updated.compliance_status == "compliant"


class TestNonCompliantBlocking:
    def test_non_compliant_source_blocks_agent_assignment(self, service: GovernanceRegistryService) -> None:
        from packages.domain.src.domain.models.agent_governance import AgentGovernanceAssignment

        src = _register_source(service)
        service.create_assessment(
            _make_assessment(src.data_source_id, status="non_compliant", gaps=["gap"], explanation="fail"),
            actor_id="t",
        )
        assignment = AgentGovernanceAssignment(
            assignment_id="assign-1", data_source_id=src.data_source_id,
            agent_name="monitoring", role="primary",
            scope_of_responsibility="ingest", assigned_by="arch",
            assigned_at=datetime.now(UTC),
        )
        with pytest.raises(Exception, match="non-compliant"):
            service.assign_agent(assignment, actor_id="arch")

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_registry import GovernanceRegistryService
from packages.domain.src.domain.models.agent_governance import AgentGovernanceAssignment
from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.functional_domain_precedence import FunctionalDomainPrecedence
from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition, HandoffStep


@pytest.fixture
def service() -> GovernanceRegistryService:
    return GovernanceRegistryService(GovernanceRepository())


def _approved_source(service: GovernanceRegistryService) -> DataSource:
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


def _assign_primary(service: GovernanceRegistryService, ds_id: str, agent: str = "monitoring") -> AgentGovernanceAssignment:
    assignment = AgentGovernanceAssignment(
        assignment_id=f"assign-{uuid4().hex[:12]}", data_source_id=ds_id,
        agent_name=agent, role="primary", scope_of_responsibility="signal ingestion",
        assigned_by="arch", assigned_at=datetime.now(UTC),
    )
    return service.assign_agent(assignment, actor_id="arch")


class TestAgentAssignment:
    def test_assign_primary_agent(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        result = _assign_primary(service, src.data_source_id)
        assert result.role == "primary"
        assert result.agent_name == "monitoring"
        updated = service.get_source(src.data_source_id)
        assert updated.governance_status == "assigned"

    def test_assign_secondary_agent(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        _assign_primary(service, src.data_source_id)
        secondary = AgentGovernanceAssignment(
            assignment_id=f"assign-{uuid4().hex[:12]}", data_source_id=src.data_source_id,
            agent_name="risk_assessment", role="secondary",
            scope_of_responsibility="hazard correlation", assigned_by="arch",
            assigned_at=datetime.now(UTC),
        )
        result = service.assign_agent(secondary, actor_id="arch")
        assert result.role == "secondary"

    def test_invalid_agent_rejected(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        assignment = AgentGovernanceAssignment(
            assignment_id="assign-bad", data_source_id=src.data_source_id,
            agent_name="nonexistent_agent", role="primary",
            scope_of_responsibility="test", assigned_by="arch",
            assigned_at=datetime.now(UTC),
        )
        with pytest.raises(Exception, match="not in the recognised"):
            service.assign_agent(assignment, actor_id="arch")


class TestHandoffChainValidation:
    def test_valid_chain(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        _assign_primary(service, src.data_source_id)
        chain = HandoffChainDefinition(
            chain_id=f"chain-{uuid4().hex[:12]}", data_source_id=src.data_source_id,
            steps=[
                HandoffStep(step_order=1, source_agent="monitoring", target_agent="risk_assessment", confidence_threshold=0.8),
                HandoffStep(step_order=2, source_agent="risk_assessment", target_agent="evacuation"),
            ],
            created_by="arch", created_at=datetime.now(UTC),
        )
        result = service.define_handoff_chain(chain, actor_id="arch")
        assert len(result.steps) == 2
        updated = service.get_source(src.data_source_id)
        assert updated.governance_status == "fully_governed"

    def test_broken_continuity_rejected(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        _assign_primary(service, src.data_source_id)
        chain = HandoffChainDefinition(
            chain_id="chain-bad", data_source_id=src.data_source_id,
            steps=[
                HandoffStep(step_order=1, source_agent="monitoring", target_agent="risk_assessment"),
                HandoffStep(step_order=2, source_agent="evacuation", target_agent="communication"),
            ],
            created_by="arch", created_at=datetime.now(UTC),
        )
        with pytest.raises(Exception, match="continuity broken"):
            service.define_handoff_chain(chain, actor_id="arch")

    def test_out_of_range_threshold_rejected(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        _assign_primary(service, src.data_source_id)
        chain = HandoffChainDefinition(
            chain_id="chain-bad2", data_source_id=src.data_source_id,
            steps=[HandoffStep(step_order=1, source_agent="monitoring", target_agent="risk_assessment", confidence_threshold=1.5)],
            created_by="arch", created_at=datetime.now(UTC),
        )
        with pytest.raises(Exception, match="between 0 and 1"):
            service.define_handoff_chain(chain, actor_id="arch")


class TestFunctionalDomainPrecedence:
    def test_set_national_default(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        precedence = FunctionalDomainPrecedence(
            precedence_id=f"prec-{uuid4().hex[:12]}", hazard_type="weather",
            primary_data_source_id=src.data_source_id,
            rationale="BoM is the national authority for weather", created_by="arch",
            created_at=datetime.now(UTC),
        )
        result = service.set_precedence(precedence, actor_id="arch")
        assert result.jurisdiction_id is None

    def test_jurisdictional_override(self, service: GovernanceRegistryService) -> None:
        src = _approved_source(service)
        service.set_precedence(FunctionalDomainPrecedence(
            precedence_id="prec-nat", hazard_type="fire",
            primary_data_source_id=src.data_source_id,
            rationale="National default", created_by="arch", created_at=datetime.now(UTC),
        ), actor_id="arch")

        nsw_src = _approved_source(service)
        service.set_precedence(FunctionalDomainPrecedence(
            precedence_id="prec-nsw", hazard_type="fire", jurisdiction_id="nsw",
            primary_data_source_id=nsw_src.data_source_id,
            rationale="NSW RFS override", created_by="arch", created_at=datetime.now(UTC),
        ), actor_id="arch")

        resolved = service._repo.resolve_precedence("fire", "nsw")
        assert resolved is not None
        assert resolved.jurisdiction_id == "nsw"

        national = service._repo.resolve_precedence("fire", "vic")
        assert national is not None
        assert national.jurisdiction_id is None

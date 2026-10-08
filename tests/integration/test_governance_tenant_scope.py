from datetime import UTC, datetime

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_registry import GovernanceRegistryService
from fastapi import HTTPException

from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource


def _register(service: GovernanceRegistryService, ds_id: str) -> None:
    service.register_source(
        DataSource(
            data_source_id=ds_id,
            name="Scoped Source",
            kind="authoritative",
            sub_category="weather_climate",
            provider="BoM",
            collection_method="api",
            data_type="warning",
            update_frequency="5m",
            geographic_coverage="Australia",
            trust_tier="tier_1_authoritative_government",
        ),
        actor_id="tester",
    )


def test_scoped_assessments_are_isolated_for_same_data_source_id() -> None:
    repo = GovernanceRepository()

    live_token = set_current_tenant(
        TenantContext(agency_id="nsw-ses", jurisdiction_ids=("nsw",), persona_id="lead", tenant_id="live")
    )
    live_service = GovernanceRegistryService(repo=repo)
    _register(live_service, "shared-ds")
    live_service.create_assessment(
        ConstitutionalAssessment(
            assessment_id="live-a1",
            data_source_id="shared-ds",
            principle="life_safety_first",
            compliance_status="compliant",
            explanation="live ok",
            assessor_id="live-lead",
            assessed_at=datetime.now(UTC),
        ),
        actor_id="live-lead",
    )
    reset_current_tenant(live_token)

    sim_token = set_current_tenant(
        TenantContext(agency_id="nsw-ses", jurisdiction_ids=("nsw",), persona_id="lead", tenant_id="sim-drill")
    )
    sim_service = GovernanceRegistryService(repo=repo)
    sim_service.create_assessment(
        ConstitutionalAssessment(
            assessment_id="sim-a1",
            data_source_id="shared-ds",
            principle="life_safety_first",
            compliance_status="non_compliant",
            explanation="sim fail",
            gaps=["gap"],
            assessor_id="sim-lead",
            assessed_at=datetime.now(UTC),
        ),
        actor_id="sim-lead",
    )

    sim_profile = sim_service.get_compliance_profile("shared-ds")
    assert {item.assessment_id for item in sim_profile["current_assessments"]} == {"sim-a1"}

    reset_current_tenant(sim_token)

    live_token_2 = set_current_tenant(
        TenantContext(agency_id="nsw-ses", jurisdiction_ids=("nsw",), persona_id="lead", tenant_id="live")
    )
    live_again = GovernanceRegistryService(repo=repo)
    live_profile = live_again.get_compliance_profile("shared-ds")
    assert {item.assessment_id for item in live_profile["current_assessments"]} == {"live-a1"}
    reset_current_tenant(live_token_2)


def test_missing_tenant_context_denies_scoped_mutation() -> None:
    def no_tenant() -> TenantContext:
        raise LookupError("missing")

    service = GovernanceRegistryService(repo=GovernanceRepository(), tenant_context_provider=no_tenant)
    _register(service, "no-tenant")

    with pytest.raises(HTTPException, match="Tenant context is required") as exc:
        service.create_assessment(
            ConstitutionalAssessment(
                assessment_id="no-tenant-a1",
                data_source_id="no-tenant",
                principle="life_safety_first",
                compliance_status="compliant",
                explanation="blocked",
                assessor_id="lead",
                assessed_at=datetime.now(UTC),
            ),
            actor_id="lead",
        )
    assert exc.value.status_code == 403

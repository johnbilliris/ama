from pathlib import Path
from uuid import uuid4

import pytest
from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_registry import GovernanceRegistryService

from packages.domain.src.domain.models.data_source import DataSource

SEED_ROOT = Path(__file__).resolve().parents[2] / "packages" / "domain" / "src" / "domain" / "seed"


@pytest.fixture
def service() -> GovernanceRegistryService:
    return GovernanceRegistryService(GovernanceRepository())


def _make_source(**overrides) -> DataSource:
    defaults = {
        "data_source_id": f"ds-{uuid4().hex[:12]}",
        "name": "Test Source",
        "kind": "authoritative",
        "sub_category": "weather_climate",
        "provider": "Test Provider",
        "trust_tier": "tier_1_authoritative_government",
    }
    defaults.update(overrides)
    return DataSource(**defaults)


class TestDataSourceRegistration:
    def test_register_new_source(self, service: GovernanceRegistryService) -> None:
        source = _make_source()
        result = service.register_source(source, actor_id="tester")
        assert result.data_source_id == source.data_source_id
        assert result.compliance_status == "unassessed"
        assert result.governance_status == "unassigned"
        assert result.created_at is not None

    def test_register_duplicate_raises_409(self, service: GovernanceRegistryService) -> None:
        source = _make_source()
        service.register_source(source, actor_id="tester")
        with pytest.raises(Exception, match="already exists"):
            service.register_source(source, actor_id="tester")

    def test_authority_rank_syncs_with_trust_tier(self, service: GovernanceRegistryService) -> None:
        source = _make_source(trust_tier="tier_3_operational_sensor")
        result = service.register_source(source, actor_id="tester")
        assert result.authority_rank == 3


class TestDataSourceListing:
    def test_list_all_sources(self, service: GovernanceRegistryService) -> None:
        service.register_source(_make_source(data_source_id="ds-a"), actor_id="t")
        service.register_source(_make_source(data_source_id="ds-b"), actor_id="t")
        assert len(service.list_sources()) == 2

    def test_filter_by_kind(self, service: GovernanceRegistryService) -> None:
        service.register_source(_make_source(data_source_id="ds-a", kind="authoritative"), actor_id="t")
        service.register_source(
            _make_source(
                data_source_id="ds-b", kind="social",
                sub_category="social_twitter", trust_tier="tier_6_social_unverified",
            ),
            actor_id="t",
        )
        results = service.list_sources(kind="social")
        assert len(results) == 1
        assert results[0].kind == "social"

    def test_filter_by_trust_tier(self, service: GovernanceRegistryService) -> None:
        service.register_source(_make_source(data_source_id="ds-a"), actor_id="t")
        service.register_source(
            _make_source(data_source_id="ds-b", trust_tier="tier_6_social_unverified"),
            actor_id="t",
        )
        results = service.list_sources(trust_tier="tier_1_authoritative_government")
        assert len(results) == 1


class TestDataSourceDeactivation:
    def test_deactivate_source(self, service: GovernanceRegistryService) -> None:
        source = _make_source()
        service.register_source(source, actor_id="tester")
        result = service.deactivate_source(source.data_source_id, actor_id="tester")
        assert result.status == "deactivated"
        assert result.deactivated_at is not None

    def test_deactivate_already_deactivated_raises_409(self, service: GovernanceRegistryService) -> None:
        source = _make_source()
        service.register_source(source, actor_id="tester")
        service.deactivate_source(source.data_source_id, actor_id="tester")
        with pytest.raises(Exception, match="already deactivated"):
            service.deactivate_source(source.data_source_id, actor_id="tester")


class TestDataSourceUpdate:
    def test_update_source_fields(self, service: GovernanceRegistryService) -> None:
        source = _make_source()
        service.register_source(source, actor_id="tester")
        result = service.update_source(source.data_source_id, {"provider": "Updated Provider"}, actor_id="tester")
        assert result.provider == "Updated Provider"

    def test_update_creates_audit_entry(self, service: GovernanceRegistryService) -> None:
        source = _make_source()
        service.register_source(source, actor_id="tester")
        service.update_source(source.data_source_id, {"provider": "New"}, actor_id="tester")
        trail = service.get_audit_trail(source.data_source_id)
        actions = [e.action for e in trail]
        assert "updated" in actions


class TestSeedCatalogue:
    def test_seed_catalogue_loads(self) -> None:
        service = GovernanceRegistryService(GovernanceRepository())
        imported = service.import_seed_catalogue(SEED_ROOT)
        assert len(imported) >= 40, f"Expected >=40 seed sources, got {len(imported)}"

    def test_seed_sources_have_required_fields(self) -> None:
        service = GovernanceRegistryService(GovernanceRepository())
        imported = service.import_seed_catalogue(SEED_ROOT)
        for source in imported:
            assert source.name
            assert source.kind
            assert source.provider
            assert source.trust_tier

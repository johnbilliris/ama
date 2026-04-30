"""Unit tests for JurisdictionGovernancePolicy + repository + RAG service (spec-032 T701, T603)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.api.app.repositories.jurisdiction_governance_policy_repository import (
    JurisdictionGovernancePolicyRepository,
)
from apps.api.app.services.rag_service import RagService
from packages.domain.src.domain.models.jurisdiction_governance_policy import (
    JurisdictionGovernancePolicy,
)


@pytest.fixture
def sample_policy() -> JurisdictionGovernancePolicy:
    return JurisdictionGovernancePolicy(
        jurisdiction_code="nsw",
        autonomy_level="standard",
        kill_switch_overrides={"monitoring": False},
        language_priorities=["en-AU", "zh-Hans", "ar"],
        aiims_role_overrides={},
        version=1,
        effective_from=datetime(2026, 4, 30, tzinfo=UTC),
        approved_by="johnbilliris",
    )


class TestJurisdictionGovernancePolicy:
    def test_round_trip(self, sample_policy):
        dumped = sample_policy.model_dump(mode="json")
        revived = JurisdictionGovernancePolicy(**dumped)
        assert revived == sample_policy

    def test_language_for_returns_first_when_unspecified(self, sample_policy):
        assert sample_policy.language_for() == "en-AU"

    def test_language_for_returns_requested_when_present(self, sample_policy):
        assert sample_policy.language_for("zh-Hans") == "zh-Hans"

    def test_language_for_falls_back_when_requested_missing(self, sample_policy):
        assert sample_policy.language_for("nonexistent") == "en-AU"

    def test_invalid_bcp47_rejected(self):
        with pytest.raises(ValueError):
            JurisdictionGovernancePolicy(
                jurisdiction_code="nsw",
                language_priorities=["NotABcp47Tag"],
                effective_from=datetime(2026, 4, 30, tzinfo=UTC),
                approved_by="x",
            )

    def test_kill_switch_override_default(self, sample_policy):
        assert sample_policy.kill_switch_engaged_for("monitoring") is False
        assert sample_policy.kill_switch_engaged_for("evacuation") is None


class TestJurisdictionGovernancePolicyRepository:
    def test_upsert_and_get_in_memory(self, sample_policy):
        repo = JurisdictionGovernancePolicyRepository(container=None)
        repo.upsert(sample_policy)
        revived = repo.get("nsw")
        assert revived is not None
        assert revived.autonomy_level == "standard"

    def test_get_returns_none_when_unknown(self):
        repo = JurisdictionGovernancePolicyRepository(container=None)
        assert repo.get("never-loaded") is None

    def test_list_all_in_memory(self, sample_policy):
        repo = JurisdictionGovernancePolicyRepository(container=None)
        repo.upsert(sample_policy)
        all_policies = repo.list_all()
        assert len(all_policies) == 1


class TestRagServiceStub:
    def test_returns_empty_when_endpoint_missing(self, monkeypatch):
        monkeypatch.delenv("AZURE_AI_SEARCH_ENDPOINT", raising=False)
        svc = RagService()
        result = svc.search("phased evacuation")
        assert result == []

    def test_returns_empty_for_empty_query(self):
        svc = RagService(client=None)
        assert svc.search("") == []
        assert svc.search("   ") == []

    def test_translates_search_results_to_citations(self):
        class FakeClient:
            def search(self, **_kwargs):
                return [
                    {
                        "chunk_id": "c1",
                        "handbook_id": "aidr-incident-management-2023",
                        "chapter": "3.2",
                        "page": 14,
                        "content": (
                            "An evacuation may be phased to balance road network capacity and shelter availability."
                        ),
                        "@search.score": 0.93,
                    }
                ]

        svc = RagService(endpoint="https://stub", client=FakeClient())
        hits = svc.search("phased evacuation")
        assert len(hits) == 1
        assert hits[0].handbook_id == "aidr-incident-management-2023"
        assert hits[0].score == 0.93
        assert "phased" in hits[0].quote

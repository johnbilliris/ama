"""Unit tests for multi-jurisdiction filtering (spec 022).

Tests cover:
- OrganisationIntelligenceService.list_organisations with multi-jurisdiction
- PreparednessAnalysisService.list_frameworks_by_jurisdictions
- PreparednessAnalysisService.analyse with real framework assignments
- SeedService caching behaviour
"""

import pytest

from apps.api.app.services.organisation_intelligence_service import OrganisationIntelligenceService
from apps.api.app.services.preparedness_analysis_service import PreparednessAnalysisService


@pytest.fixture(scope="module")
def org_service():
    return OrganisationIntelligenceService()


@pytest.fixture(scope="module")
def prep_service():
    return PreparednessAnalysisService()


class TestOrganisationMultiJurisdiction:
    """OrganisationIntelligenceService with multi-jurisdiction filtering."""

    def test_single_jurisdiction_returns_results(self, org_service):
        orgs = org_service.list_organisations(["nsw"])
        assert isinstance(orgs, list)
        # T-AA06 — explicit boundary: NSW jurisdiction has at least
        # 3 mandated organisations (NSW RFS, NSW SES, NSW Police) per
        # the seed catalogue. Assert ≥3 to detect catalogue truncation.
        assert len(orgs) >= 3, f"NSW jurisdiction returned only {len(orgs)} orgs; expected ≥3"

    def test_multiple_jurisdictions_returns_union(self, org_service):
        nsw_only = org_service.list_organisations(["nsw"])
        vic_only = org_service.list_organisations(["vic"])
        combined = org_service.list_organisations(["nsw", "vic"])
        assert len(combined) >= max(len(nsw_only), len(vic_only))

    def test_no_duplicates_in_results(self, org_service):
        orgs = org_service.list_organisations(["nsw", "commonwealth"])
        ids = [o.organisation_id for o in orgs]
        assert len(ids) == len(set(ids)), "Duplicate organisation IDs found"

    def test_empty_list_returns_empty(self, org_service):
        orgs = org_service.list_organisations([])
        assert orgs == []

    def test_none_returns_empty(self, org_service):
        orgs = org_service.list_organisations(None)
        assert orgs == []

    def test_invalid_jurisdiction_returns_empty(self, org_service):
        orgs = org_service.list_organisations(["nonexistent"])
        assert orgs == []

    def test_all_jurisdictions_returns_all_orgs(self, org_service):
        all_ids = ["commonwealth", "nsw", "vic", "qld", "sa", "wa", "tas", "act", "nt"]
        orgs = org_service.list_organisations(all_ids)
        assert len(orgs) > 0


class TestFrameworkByJurisdiction:
    """PreparednessAnalysisService.list_frameworks_by_jurisdictions."""

    def test_nsw_returns_frameworks(self, prep_service):
        fws = prep_service.list_frameworks_by_jurisdictions(["nsw"])
        assert isinstance(fws, list)
        assert len(fws) > 0

    def test_multiple_jurisdictions_returns_frameworks(self, prep_service):
        fws = prep_service.list_frameworks_by_jurisdictions(["nsw", "vic"])
        assert len(fws) > 0

    def test_empty_returns_empty(self, prep_service):
        fws = prep_service.list_frameworks_by_jurisdictions([])
        assert fws == []

    def test_invalid_jurisdiction_returns_empty(self, prep_service):
        fws = prep_service.list_frameworks_by_jurisdictions(["nonexistent"])
        assert fws == []

    def test_framework_objects_have_required_fields(self, prep_service):
        fws = prep_service.list_frameworks_by_jurisdictions(["nsw"])
        for fw in fws:
            assert hasattr(fw, "framework_id")
            assert hasattr(fw, "name")
            assert hasattr(fw, "framework_type")


class TestAnalyseUsesRealAssignments:
    """PreparednessAnalysisService.analyse uses actual framework_assignments data."""

    def test_analyse_returns_expected_structure(self, prep_service):
        result = prep_service.analyse("flood", ["nsw"])
        assert "jurisdictions" in result
        assert "organisations" in result
        assert "frameworks" in result
        assert "assignments" in result
        assert "coordinationGaps" in result
        assert "findings" in result

    def test_analyse_assignments_match_seed_data(self, prep_service):
        result = prep_service.analyse("flood", ["nsw"])
        assignments = result["assignments"]
        assert isinstance(assignments, list)
        for a in assignments:
            assert a["jurisdiction_id"] == "nsw"

    def test_analyse_no_synthetic_cartesian_product(self, prep_service):
        """Assignments should come from seed data, not be a cartesian product."""
        result_single = prep_service.analyse("flood", ["nsw"])
        context = prep_service.get_context()
        expected_count = len(
            [a for a in context["framework_assignments"] if a.jurisdiction_id == "nsw" and a.effective_to is None]
        )
        assert len(result_single["assignments"]) == expected_count

    def test_analyse_frameworks_scoped_to_jurisdiction(self, prep_service):
        result = prep_service.analyse("flood", ["nsw"])
        framework_ids = {fw["framework_id"] for fw in result["frameworks"]}
        assignment_framework_ids = {a["framework_id"] for a in result["assignments"]}
        assert framework_ids == assignment_framework_ids

    def test_analyse_cyclone_commonwealth_gap(self, prep_service):
        result = prep_service.analyse("cyclone", ["nsw"])
        gaps = result["coordinationGaps"]
        has_commonwealth_gap = any("commonwealth" in g.lower() for g in gaps)
        assert has_commonwealth_gap, "Expected commonwealth meteorology gap for cyclone without commonwealth"

    def test_analyse_empty_jurisdictions(self, prep_service):
        result = prep_service.analyse("flood", [])
        assert result["organisations"] == []
        assert result["assignments"] == []

    def test_analyse_findings_reflect_actual_counts(self, prep_service):
        result = prep_service.analyse("flood", ["nsw", "vic"])
        findings_text = " ".join(result["findings"])
        assert "2 jurisdictions" in findings_text


class TestGetContext:
    """PreparednessAnalysisService.get_context correctness."""

    def test_context_has_all_keys(self, prep_service):
        ctx = prep_service.get_context()
        assert "jurisdictions" in ctx
        assert "frameworks" in ctx
        assert "organisations" in ctx
        assert "framework_assignments" in ctx

    def test_context_framework_assignments_are_typed(self, prep_service):
        from packages.domain.src.domain.models.framework_assignment import FrameworkAssignment

        ctx = prep_service.get_context()
        for a in ctx["framework_assignments"]:
            assert isinstance(a, FrameworkAssignment)

    def test_context_jurisdictions_are_typed(self, prep_service):
        from packages.domain.src.domain.models.jurisdiction import Jurisdiction

        ctx = prep_service.get_context()
        for j in ctx["jurisdictions"]:
            assert isinstance(j, Jurisdiction)


class TestSeedServiceCaching:
    """SeedService caches loaded data in memory."""

    def test_repeated_loads_return_same_object(self):
        from pathlib import Path

        from apps.api.app.services.seed_service import SeedService
        from packages.domain.src.domain.seed import bootstrap as _seed_mod

        seed_root = Path(_seed_mod.__file__).resolve().parent
        svc = SeedService()
        result1 = svc.load(seed_root)
        result2 = svc.load(seed_root)
        assert result1 is result2, "Expected cached (same object) on repeated loads"

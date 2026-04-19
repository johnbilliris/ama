"""Tests for enriched organisation catalog data model and referential integrity.

Tests cover:
- All 49 seed organisations deserialize into the Organisation model
- Controlled vocabulary fields use valid values only
- mutual_aid_partner_ids reference existing organisation IDs
- New fields are properly populated across the dataset
- API serialization includes all new fields
"""
import json
from pathlib import Path

import pytest

from packages.domain.src.domain.models.aiims_role_assignment import AiimsFunction
from packages.domain.src.domain.models.incident import IncidentType
from packages.domain.src.domain.models.organisation import Organisation

SEED_PATH = Path("packages/domain/src/domain/seed/organisations_australia.json")

VALID_AIIMS = set(AiimsFunction.__args__)
VALID_INCIDENT = set(IncidentType.__args__)
VALID_WORKFORCE = {"paid", "volunteer", "mixed"}


@pytest.fixture(scope="module")
def seed_items():
    with open(SEED_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def organisations(seed_items):
    return [Organisation(**item) for item in seed_items]


class TestSeedDeserialization:
    """Every seed entry must deserialize into a valid Organisation."""

    def test_all_items_deserialize(self, seed_items):
        orgs = [Organisation(**item) for item in seed_items]
        assert len(orgs) == len(seed_items)

    def test_minimum_count(self, organisations):
        assert len(organisations) >= 49, "Expected at least 49 seed organisations"


class TestControlledVocabulary:
    """Fields using controlled vocabularies must contain only valid values."""

    def test_aiims_functions_use_valid_values(self, organisations):
        for org in organisations:
            for fn in org.aiims_functions:
                assert fn in VALID_AIIMS, (
                    f"{org.organisation_id}: aiims_function '{fn}' not in {VALID_AIIMS}"
                )

    def test_hazard_types_use_valid_values(self, organisations):
        for org in organisations:
            for ht in org.hazard_types:
                assert ht in VALID_INCIDENT, (
                    f"{org.organisation_id}: hazard_type '{ht}' not in valid IncidentType"
                )

    def test_lead_agency_for_use_valid_values(self, organisations):
        for org in organisations:
            for la in org.lead_agency_for:
                assert la in VALID_INCIDENT, (
                    f"{org.organisation_id}: lead_agency_for '{la}' not in valid IncidentType"
                )

    def test_workforce_type_uses_valid_values(self, organisations):
        for org in organisations:
            if org.workforce_type is not None:
                assert org.workforce_type in VALID_WORKFORCE, (
                    f"{org.organisation_id}: workforce_type '{org.workforce_type}' invalid"
                )


class TestReferentialIntegrity:
    """mutual_aid_partner_ids must reference existing organisation IDs."""

    def test_all_mutual_aid_ids_exist(self, organisations):
        all_ids = {o.organisation_id for o in organisations}
        broken = []
        for org in organisations:
            for mid in org.mutual_aid_partner_ids:
                if mid not in all_ids:
                    broken.append(f"{org.organisation_id} -> {mid}")
        assert broken == [], f"Broken mutual_aid_partner_ids refs: {broken}"

    def test_no_self_referencing_mutual_aid(self, organisations):
        self_refs = [
            o.organisation_id
            for o in organisations
            if o.organisation_id in o.mutual_aid_partner_ids
        ]
        assert self_refs == [], f"Orgs referencing themselves as mutual aid: {self_refs}"


class TestEnrichmentCoverage:
    """Verify enrichment coverage across the dataset."""

    def test_all_have_abbreviation(self, organisations):
        missing = [o.organisation_id for o in organisations if not o.abbreviation]
        assert len(missing) == 0, f"Orgs missing abbreviation: {missing}"

    def test_all_have_capabilities(self, organisations):
        missing = [o.organisation_id for o in organisations if not o.primary_capabilities]
        assert len(missing) == 0, f"Orgs missing capabilities: {missing}"

    def test_all_have_hazard_types(self, organisations):
        missing = [o.organisation_id for o in organisations if not o.hazard_types]
        assert len(missing) == 0, f"Orgs missing hazard_types: {missing}"

    def test_all_have_workforce_type(self, organisations):
        missing = [o.organisation_id for o in organisations if not o.workforce_type]
        assert len(missing) == 0, f"Orgs missing workforce_type: {missing}"

    def test_all_have_activation_triggers(self, organisations):
        missing = [o.organisation_id for o in organisations if not o.activation_triggers]
        assert len(missing) == 0, f"Orgs missing activation_triggers: {missing}"


class TestApiSerialization:
    """Organisation.model_dump() must include all new fields for API serialization."""

    def test_dump_includes_new_fields(self, organisations):
        org = organisations[0]
        data = org.model_dump()
        new_fields = [
            "abbreviation", "aiims_functions", "lead_agency_for",
            "primary_capabilities", "hazard_types", "workforce_type",
            "legislative_basis", "mutual_aid_partner_ids", "activation_triggers",
        ]
        for field in new_fields:
            assert field in data, f"model_dump() missing field: {field}"

    def test_dump_types_correct(self, organisations):
        org = organisations[0]
        data = org.model_dump()
        assert isinstance(data["aiims_functions"], list)
        assert isinstance(data["hazard_types"], list)
        assert isinstance(data["mutual_aid_partner_ids"], list)
        assert isinstance(data["activation_triggers"], list)
        assert isinstance(data["primary_capabilities"], list)

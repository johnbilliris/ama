"""Tests for enriched framework catalog data model and referential integrity.

Tests cover:
- All seed frameworks deserialize into the OperatingFramework model
- Controlled vocabulary fields use valid values only
- related_framework_ids reference existing framework IDs
- custodian_organisation_id references existing organisation IDs
- applicable_jurisdiction_ids reference existing jurisdiction IDs
- PPRR phases and hazard types use valid controlled vocab values
- API serialization includes all new fields
"""
import json
from pathlib import Path

import pytest

from packages.domain.src.domain.models.operating_framework import OperatingFramework
from packages.domain.src.domain.models.incident import IncidentType, PprrPhase

SEED_ROOT = Path("packages/domain/src/domain/seed")

VALID_PPRR = set(PprrPhase.__args__)
VALID_INCIDENT = set(IncidentType.__args__)


@pytest.fixture(scope="module")
def framework_items():
    with open(SEED_ROOT / "frameworks_australia.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def frameworks(framework_items):
    return [OperatingFramework(**item) for item in framework_items]


@pytest.fixture(scope="module")
def org_ids():
    with open(SEED_ROOT / "organisations_australia.json") as f:
        return {o["organisation_id"] for o in json.load(f)}


@pytest.fixture(scope="module")
def jurisdiction_ids():
    with open(SEED_ROOT / "jurisdictions_australia.json") as f:
        return {j["jurisdiction_id"] for j in json.load(f)}


@pytest.fixture(scope="module")
def assignment_items():
    with open(SEED_ROOT / "framework_assignments_australia.json") as f:
        return json.load(f)


class TestSeedDeserialization:
    """Every seed entry must deserialize into a valid OperatingFramework."""

    def test_all_items_deserialize(self, framework_items):
        fws = [OperatingFramework(**item) for item in framework_items]
        assert len(fws) == len(framework_items)

    def test_minimum_count(self, frameworks):
        assert len(frameworks) >= 20, "Expected at least 20 seed frameworks"


class TestControlledVocabulary:
    """Fields using controlled vocabularies must contain only valid values."""

    def test_pprr_phases_use_valid_values(self, frameworks):
        for fw in frameworks:
            for phase in fw.pprr_phases:
                assert phase in VALID_PPRR, (
                    f"{fw.framework_id}: pprr_phase '{phase}' not in {VALID_PPRR}"
                )

    def test_hazard_types_use_valid_values(self, frameworks):
        for fw in frameworks:
            for ht in fw.hazard_types:
                assert ht in VALID_INCIDENT, (
                    f"{fw.framework_id}: hazard_type '{ht}' not in valid IncidentType"
                )

    def test_framework_type_is_valid(self, frameworks):
        valid_types = {"aiims", "agency_specific", "jurisdictional_policy", "communications", "other"}
        for fw in frameworks:
            assert fw.framework_type in valid_types, (
                f"{fw.framework_id}: framework_type '{fw.framework_type}' invalid"
            )

    def test_status_is_valid(self, frameworks):
        valid_statuses = {"active", "retired", "draft"}
        for fw in frameworks:
            assert fw.status in valid_statuses, (
                f"{fw.framework_id}: status '{fw.status}' invalid"
            )


class TestReferentialIntegrity:
    """Cross-references must point to existing entities."""

    def test_related_framework_ids_exist(self, frameworks):
        all_ids = {fw.framework_id for fw in frameworks}
        broken = []
        for fw in frameworks:
            for rid in fw.related_framework_ids:
                if rid not in all_ids:
                    broken.append(f"{fw.framework_id} -> {rid}")
        assert broken == [], f"Broken related_framework_ids refs: {broken}"

    def test_no_self_referencing_related(self, frameworks):
        self_refs = [
            fw.framework_id
            for fw in frameworks
            if fw.framework_id in fw.related_framework_ids
        ]
        assert self_refs == [], f"Frameworks referencing themselves: {self_refs}"

    def test_custodian_organisation_ids_exist(self, frameworks, org_ids):
        broken = []
        for fw in frameworks:
            if fw.custodian_organisation_id and fw.custodian_organisation_id not in org_ids:
                broken.append(f"{fw.framework_id} -> {fw.custodian_organisation_id}")
        assert broken == [], f"Broken custodian_organisation_id refs: {broken}"

    def test_applicable_jurisdiction_ids_exist(self, frameworks, jurisdiction_ids):
        broken = []
        for fw in frameworks:
            for jid in fw.applicable_jurisdiction_ids:
                if jid not in jurisdiction_ids:
                    broken.append(f"{fw.framework_id} -> {jid}")
        assert broken == [], f"Broken applicable_jurisdiction_ids refs: {broken}"


class TestFrameworkAssignments:
    """Framework assignments must reference valid frameworks and jurisdictions."""

    def test_all_assignments_reference_valid_frameworks(self, assignment_items, frameworks):
        fw_ids = {fw.framework_id for fw in frameworks}
        broken = [
            a["assignment_id"]
            for a in assignment_items
            if a["framework_id"] not in fw_ids
        ]
        assert broken == [], f"Assignments referencing missing frameworks: {broken}"

    def test_all_assignments_reference_valid_jurisdictions(self, assignment_items, jurisdiction_ids):
        broken = [
            a["assignment_id"]
            for a in assignment_items
            if a.get("jurisdiction_id") and a["jurisdiction_id"] not in jurisdiction_ids
        ]
        assert broken == [], f"Assignments referencing missing jurisdictions: {broken}"

    def test_every_framework_has_at_least_one_assignment(self, frameworks, assignment_items):
        assigned_fw_ids = {a["framework_id"] for a in assignment_items}
        unassigned = [
            fw.framework_id for fw in frameworks
            if fw.framework_id not in assigned_fw_ids
        ]
        assert unassigned == [], f"Frameworks with no assignments (won't appear in UI): {unassigned}"


class TestEnrichmentCoverage:
    """Verify enrichment coverage across the dataset."""

    def test_all_have_description(self, frameworks):
        missing = [fw.framework_id for fw in frameworks if not fw.description]
        assert len(missing) == 0, f"Frameworks missing description: {missing}"

    def test_all_have_pprr_phases(self, frameworks):
        missing = [fw.framework_id for fw in frameworks if not fw.pprr_phases]
        assert len(missing) == 0, f"Frameworks missing pprr_phases: {missing}"

    def test_all_have_applicable_jurisdictions(self, frameworks):
        missing = [fw.framework_id for fw in frameworks if not fw.applicable_jurisdiction_ids]
        assert len(missing) == 0, f"Frameworks missing applicable_jurisdiction_ids: {missing}"


class TestApiSerialization:
    """OperatingFramework.model_dump() must include all new fields."""

    def test_dump_includes_new_fields(self, frameworks):
        fw = frameworks[0]
        data = fw.model_dump()
        new_fields = [
            "abbreviation", "description", "applicable_jurisdiction_ids",
            "custodian_organisation_id", "pprr_phases", "hazard_types",
            "activation_triggers", "legislative_basis", "version",
            "source_uri", "related_framework_ids",
        ]
        for field in new_fields:
            assert field in data, f"model_dump() missing field: {field}"

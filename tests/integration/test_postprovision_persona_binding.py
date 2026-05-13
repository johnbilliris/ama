"""Spec-039 T035: assert every persona class with static reference data
resolves to ≥1 seeded record after a postprovision-equivalent run.

This is the partial coverage gate for FR-060 / SC-001. Full 68/68 persona
coverage is verified later in Phase 6 (T140–T147) + Phase 7 (T167) once
the persona-binding manifest entries land. For Phase 3 we just check that
the eight new subdirectory catalogues each populate at least one record
into the in-memory ``seed`` container.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import seed_loader  # noqa: E402
from tests.integration.spec039_fakes import FakeCosmosClient  # noqa: E402

# Persona-class → expected presence in at least one of these subdirs.
PERSONA_CLASSES = {
    "alert-author": ["alert-templates"],
    "evac-planner": ["evacuation-routes"],
    "vulnerable-coordinator": ["vulnerable-categories"],
    "hospital-coordinator": ["hospital-capability"],
    "traffic-controller": ["road-segments"],
    "utility-liaison": ["utility-infrastructure"],
    "volunteer-coordinator": ["volunteer-credentials"],
    "lemp-memp-author": ["lemp-memp-templates"],
    "iga-coordinator": ["inter-government-agreements"],
}


@pytest.fixture()
def loader_summary() -> dict[str, dict[str, int]]:
    """Run the spec-039 subdirectory loader against the committed catalogue."""
    client = FakeCosmosClient()
    return seed_loader.seed_spec039_subdirectories(client, "disaster-hub")


@pytest.mark.parametrize("persona,subdirs", PERSONA_CLASSES.items())
def test_persona_class_has_at_least_one_record(persona, subdirs, loader_summary):
    inserts = sum(loader_summary.get(s, {}).get("inserts", 0) for s in subdirs)
    assert inserts >= 1, f"FR-060 / SC-001: persona class {persona!r} has zero static reference records in {subdirs}"

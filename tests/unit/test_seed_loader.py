"""Unit tests for ``scripts.seed_loader``.

Pin the loader's coverage to the full set of seed files known to
``packages.domain.src.domain.seed.bootstrap`` so a future contributor
can't silently drop a category from the postprovision seeder again
(spec: identities + hazard_scenarios + aiims_function_map were
missing from Cosmos because they were absent from ``SEED_FILES``).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def seed_loader():
    """Import the script as a module without executing main()."""
    repo_root = Path(__file__).resolve().parents[2]
    scripts_dir = repo_root / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        module = importlib.import_module("seed_loader")
        importlib.reload(module)
        return module
    finally:
        sys.path.remove(str(scripts_dir))


def test_seed_files_covers_all_bootstrap_seed_files(seed_loader):
    """Every JSON file referenced by ``bootstrap_seed_data`` must also be
    seeded into Cosmos by the postprovision hook."""
    expected = {
        "jurisdictions_australia.json",
        "frameworks_australia.json",
        "organisations_australia.json",
        "data_sources_australia.json",
        "disasters_australia.json",
        "framework_assignments_australia.json",
        "scenario_templates_australia.json",
        "identities_australia.json",
        "hazard_scenarios_australia.json",
        "aiims_function_map.json",
    }
    assert set(seed_loader.SEED_FILES.values()) == expected


def test_partition_keys_mapped_for_every_seed_file(seed_loader):
    assert set(seed_loader.PARTITION_KEY_MAP) == set(seed_loader.SEED_FILES)
    assert set(seed_loader.CONTAINER_MAP) == set(seed_loader.SEED_FILES)


def test_load_seed_data_handles_singleton_dict_files(seed_loader):
    """``aiims_function_map.json`` is a singleton object, not a list. The
    loader must wrap it as a one-record list with a deterministic id so
    ``seed_cosmos`` can upsert it idempotently."""
    data = seed_loader.load_seed_data()

    assert "aiims_function_map" in data
    records = data["aiims_function_map"]
    assert isinstance(records, list)
    assert len(records) == 1
    record = records[0]
    assert record["id"] == "aiims_function_map"
    # ``functions`` is one of the fields the source object always carries.
    assert "functions" in record


def test_load_seed_data_loads_identities_and_hazard_scenarios(seed_loader):
    data = seed_loader.load_seed_data()

    # Sanity: list-typed seed files retain list shape and counts > 0.
    assert isinstance(data["identities"], list) and len(data["identities"]) > 0
    assert isinstance(data["hazard_scenarios"], list) and len(data["hazard_scenarios"]) > 0

    # Identity records expose the id field expected by the seed_cosmos
    # fallback (``record[k].endswith('_id')`` resolution).
    assert any(k.endswith("_id") for k in data["identities"][0])
    assert any(k.endswith("_id") for k in data["hazard_scenarios"][0])

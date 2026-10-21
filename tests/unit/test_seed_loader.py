"""Unit tests for ``scripts.seed_loader``.

Pin the loader's coverage to the full set of seed files known to
``packages.domain.src.domain.seed.bootstrap`` so a future contributor
can't silently drop a category from the postprovision seeder again
(spec: identities + hazard_scenarios + aiims_function_map were
missing from Cosmos because they were absent from ``SEED_FILES``).
"""

from __future__ import annotations

import builtins
import importlib
import sys
import tomllib
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


def test_api_runtime_declares_yaml_frontmatter_parser_dependency():
    repo_root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((repo_root / "apps" / "api" / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = {dependency.lower() for dependency in project["project"]["dependencies"]}
    assert "pyyaml>=6.0" in dependencies


def test_help_article_seed_stores_body_without_frontmatter(seed_loader):
    content_root = Path(seed_loader.HELP_CONTENT_ROOT)
    article_path = content_root / "articles" / "cross-border-bushfire-nema.mdx"
    row = seed_loader._build_help_article_row(
        abs_path=article_path,
        content_root=content_root,
        snapshot_id="test-snapshot",
    )

    assert row["slug"] == "cross-border-bushfire-nema"
    assert row["title"] == "Cross-border bushfire coordination and NEMA acknowledgement"
    assert row["classification"] == "OFFICIAL"
    assert row["body_md"].startswith("# Cross-border bushfire coordination")
    assert "status: Active" not in row["body_md"]
    assert "estimated_reading_time:" not in row["body_md"]


def test_all_help_article_seed_bodies_exclude_frontmatter(seed_loader):
    articles = seed_loader.load_help_articles()

    assert len(articles) == 45
    assert all(not article["body_md"].lstrip().startswith("---") for article in articles)


def test_missing_yaml_parser_fails_closed_instead_of_returning_frontmatter(seed_loader, monkeypatch):
    original_import = builtins.__import__

    def import_without_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("simulated missing PyYAML")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_yaml)
    with pytest.raises(RuntimeError, match="PyYAML is required"):
        seed_loader._parse_help_frontmatter("---\ntitle: Example\n---\n# Body\n")


def test_targeted_help_article_command_upserts_only_the_requested_slug(seed_loader, monkeypatch, tmp_path):
    content_root = tmp_path / "help"
    article_root = content_root / "articles"
    article_root.mkdir(parents=True)
    for slug in ("cross-border-bushfire-nema", "getting-started"):
        (article_root / f"{slug}.mdx").write_text(
            f'---\nslug: {slug}\ntitle: "{slug}"\n---\n# {slug}\n\nBody text.\n',
            encoding="utf-8",
        )

    upserts = []
    monkeypatch.setattr(seed_loader, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(seed_loader, "HELP_CONTENT_ROOT", content_root)
    monkeypatch.setattr(seed_loader, "seed_help_articles", lambda endpoint, database, records: upserts.extend(records))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "seed_loader.py",
            "--cosmos-endpoint",
            "http://cosmos:8081",
            "--cosmos-database",
            "disaster-hub",
            "--help-article",
            "cross-border-bushfire-nema",
        ],
    )

    seed_loader.main()

    assert len(upserts) == 1
    assert upserts[0]["slug"] == "cross-border-bushfire-nema"
    assert upserts[0]["body_md"] == "# cross-border-bushfire-nema\n\nBody text.\n"

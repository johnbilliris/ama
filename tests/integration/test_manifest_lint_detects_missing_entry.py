"""Spec-039 T040: ``check_test_data_manifest.py`` MUST fail when a catalogued
file is missing from ``docs/test-data/manifest.json``.

FR-032, SC-003.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "tools" / "lint" / "check_test_data_manifest.py"
MANIFEST = REPO_ROOT / "docs" / "test-data" / "manifest.json"
SCHEMA = REPO_ROOT / "docs" / "test-data" / "manifest.schema.json"


@pytest.fixture
def isolated_repo(tmp_path: Path) -> Path:
    """Materialise the minimum subset of the real tree the lint walks."""
    seed_root = tmp_path / "packages" / "domain" / "src" / "domain" / "seed"
    seed_root.mkdir(parents=True)
    docs = tmp_path / "docs" / "test-data"
    docs.mkdir(parents=True)
    tools_data = tmp_path / "tools" / "lint" / "data"
    tools_data.mkdir(parents=True)
    (tools_data / "indigenous_denylist.txt").write_text(
        "[NAMES]\n[COMMUNITIES]\n[SACRED_COORDS]\n[CONTEXT_ZONES]\n",
        encoding="utf-8",
    )
    # Copy the real schema so jsonschema validation works.
    docs.joinpath("manifest.schema.json").write_text(SCHEMA.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def _baseline_manifest(repo: Path, extra_entries: list[dict] | None = None) -> None:
    entries = extra_entries or []
    doc = {
        "schema_version": "1.0.0",
        "generated_at": "2026-05-11T00:00:00Z",
        "entries": entries
        or [
            {
                "id": "placeholder-entry",
                "name": "Placeholder",
                "category": "mock",
                "path": "tools/lint/data/indigenous_denylist.txt",
                "version": "1.0.0",
                "content_hash": "0" * 64,
                "created_or_updated": "2026-05-11",
                "persona_bindings": ["incident-commander"],
                "domain_group": "cross-sector",
                "fictitious": True,
                "pii": False,
                "pspf": "OFFICIAL",
                "residency": "AU",
                "licence": "proprietary-fictitious-internal",
                "source_url": "n/a",
                "snapshot_date": "n/a",
                "dataset_version": "n/a",
                "refresh_policy": "static",
                "volume_tier": "n/a",
                "record_count": 0,
                "cultural_review_required": False,
            }
        ],
    }
    (repo / "docs" / "test-data" / "manifest.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_missing_entry_fails(isolated_repo: Path) -> None:
    # Add a seed file that is NOT enumerated in the manifest.
    seed_dir = isolated_repo / "packages" / "domain" / "src" / "domain" / "seed"
    rogue = seed_dir / "rogue_catalogue.json"
    rogue.write_text(
        json.dumps(
            {
                "_fixture": {
                    "fictitious": True,
                    "residency": "AU",
                    "licence": "CC-BY-4.0",
                    "schema_version": "1",
                },
                "records": [],
            }
        ),
        encoding="utf-8",
    )
    _baseline_manifest(isolated_repo)

    result = subprocess.run(
        [sys.executable, str(LINT), "--repo-root", str(isolated_repo)],
        capture_output=True,
        text=True,
        cwd=str(isolated_repo),
    )
    assert result.returncode != 0, (
        f"lint should fail when a catalogued file is unenumerated.\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "rogue_catalogue.json" in (result.stdout + result.stderr)

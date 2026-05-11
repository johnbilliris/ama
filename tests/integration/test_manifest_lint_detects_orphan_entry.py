"""Spec-038 T041: ``check_test_data_manifest.py`` MUST fail when a manifest
entry references a path that does not exist on disk.

FR-032.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "tools" / "lint" / "check_test_data_manifest.py"
SCHEMA = REPO_ROOT / "docs" / "test-data" / "manifest.schema.json"


@pytest.fixture
def isolated_repo(tmp_path: Path) -> Path:
    docs = tmp_path / "docs" / "test-data"
    docs.mkdir(parents=True)
    (tmp_path / "packages" / "domain" / "src" / "domain" / "seed").mkdir(parents=True)
    tools_data = tmp_path / "tools" / "lint" / "data"
    tools_data.mkdir(parents=True)
    (tools_data / "indigenous_denylist.txt").write_text(
        "[NAMES]\n[COMMUNITIES]\n[SACRED_COORDS]\n[CONTEXT_ZONES]\n",
        encoding="utf-8",
    )
    docs.joinpath("manifest.schema.json").write_text(
        SCHEMA.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return tmp_path


def test_orphan_entry_fails(isolated_repo: Path) -> None:
    doc = {
        "schema_version": "1.0.0",
        "generated_at": "2026-05-11T00:00:00Z",
        "entries": [
            {
                "id": "orphan-entry",
                "name": "Orphan path entry",
                "category": "synthetic",
                "path": "packages/domain/src/domain/seed/does_not_exist.json",
                "version": "1.0.0",
                "content_hash": "0" * 64,
                "created_or_updated": "2026-05-11",
                "persona_bindings": ["incident-commander"],
                "domain_group": "operational",
                "fictitious": True,
                "pii": False,
                "pspf": "OFFICIAL",
                "residency": "AU",
                "licence": "CC-BY-4.0",
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
    (isolated_repo / "docs" / "test-data" / "manifest.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, str(LINT), "--repo-root", str(isolated_repo)],
        capture_output=True,
        text=True,
        cwd=str(isolated_repo),
    )
    assert result.returncode != 0
    assert "does_not_exist.json" in (result.stdout + result.stderr)

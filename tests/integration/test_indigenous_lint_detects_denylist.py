"""Spec-039 T042: ``check_indigenous_placeholders.py`` MUST fail when a
denylisted token from ``[NAMES]`` (etc.) appears in a fixture file.

FR-044, CL-6.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "tools" / "lint" / "check_indigenous_placeholders.py"
SCHEMA = REPO_ROOT / "docs" / "test-data" / "manifest.schema.json"


@pytest.fixture
def isolated_repo(tmp_path: Path) -> Path:
    seed = tmp_path / "packages" / "domain" / "src" / "domain" / "seed"
    seed.mkdir(parents=True)
    (tmp_path / "scripts" / "generators").mkdir(parents=True)
    (tmp_path / "apps" / "api" / "app" / "services" / "simulation" / "feeds").mkdir(parents=True)
    (tmp_path / "fixtures" / "sim_replays").mkdir(parents=True)
    docs = tmp_path / "docs" / "test-data"
    docs.mkdir(parents=True)
    docs.joinpath("manifest.schema.json").write_text(
        SCHEMA.read_text(encoding="utf-8"), encoding="utf-8"
    )
    docs.joinpath("manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "generated_at": "2026-05-11T00:00:00Z",
                "entries": [
                    {
                        "id": "rogue-fixture",
                        "name": "Rogue fixture entry",
                        "category": "synthetic",
                        "path": "packages/domain/src/domain/seed/rogue.json",
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
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    denylist = tmp_path / "tools" / "lint" / "data" / "indigenous_denylist.txt"
    denylist.parent.mkdir(parents=True)
    denylist.write_text(
        "[NAMES]\nbanned-name-token\n"
        "[COMMUNITIES]\n"
        "[SACRED_COORDS]\n"
        "[CONTEXT_ZONES]\n"
        "nt-central-desert-zone\n",
        encoding="utf-8",
    )
    # Inject the banned token into a seed fixture.
    (seed / "rogue.json").write_text(
        '{"records":[{"name":"banned-name-token"}]}', encoding="utf-8"
    )
    return tmp_path


def test_denylist_detection_fails(isolated_repo: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(LINT), "--repo-root", str(isolated_repo)],
        capture_output=True,
        text=True,
        cwd=str(isolated_repo),
    )
    assert result.returncode != 0, (
        f"lint should fail on denylisted token.\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "banned-name-token" in (result.stdout + result.stderr)

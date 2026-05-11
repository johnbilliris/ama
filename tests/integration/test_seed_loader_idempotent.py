"""Spec-038 T020: loader idempotency — second run = 0 inserts/updates (FR-012, SC-004)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tests.integration.spec038_fakes import FakeCosmosClient  # noqa: E402

# Import after sys.path setup.
from scripts import seed_loader  # noqa: E402


def _good_file(tmp_dir: Path, name: str, records: list[dict]) -> Path:
    doc = {
        "_fixture": {
            "fictitious": True,
            "residency": "AU",
            "licence": "CC-BY-4.0",
            "schema_version": "1",
        },
        "records": records,
    }
    p = tmp_dir / name
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


@pytest.fixture()
def fake_seed_root(tmp_path: Path, monkeypatch):
    """Build a temp seed catalogue with one alert-templates file."""
    sub = tmp_path / "alert-templates"
    sub.mkdir()
    _good_file(
        sub,
        "bushfire_en-AU.json",
        [
            {
                "id": "alert-bushfire-001",
                "fictitious": True,
                "residency": "AU",
                "pspf": "OFFICIAL",
                "licence": "CC-BY-4.0",
                "body": "TEST — DO NOT BROADCAST: bushfire warning",
            },
            {
                "id": "alert-bushfire-002",
                "fictitious": True,
                "residency": "AU",
                "pspf": "OFFICIAL",
                "licence": "CC-BY-4.0",
                "body": "TEST — DO NOT BROADCAST: evacuation",
            },
        ],
    )
    monkeypatch.setattr(seed_loader, "SPEC038_SEED_ROOT", tmp_path, raising=False)
    return tmp_path


def test_idempotent_upsert(fake_seed_root):
    client = FakeCosmosClient()
    summary1 = seed_loader.seed_spec038_subdirectories(client, "disaster-hub")
    assert summary1["alert-templates"]["inserts"] == 2
    assert summary1["alert-templates"]["updates"] == 0
    assert summary1["alert-templates"]["already-current"] == 0

    summary2 = seed_loader.seed_spec038_subdirectories(client, "disaster-hub")
    assert summary2["alert-templates"]["inserts"] == 0
    assert summary2["alert-templates"]["updates"] == 0
    assert summary2["alert-templates"]["already-current"] == 2

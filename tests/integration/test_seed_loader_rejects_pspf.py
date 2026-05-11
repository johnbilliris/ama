"""Spec-038 T022: loader rejects records marked above OFFICIAL: SENSITIVE (FR-043)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tests.integration.spec038_fakes import FakeCosmosClient  # noqa: E402
from scripts import seed_loader  # noqa: E402


@pytest.fixture()
def protected_seed_root(tmp_path: Path, monkeypatch):
    sub = tmp_path / "alert-templates"
    sub.mkdir()
    doc = {
        "_fixture": {
            "fictitious": True,
            "residency": "AU",
            "licence": "CC-BY-4.0",
            "schema_version": "1",
        },
        "records": [
            {
                "id": "x",
                "fictitious": True,
                "residency": "AU",
                "pspf": "PROTECTED",  # above the cap
                "licence": "CC-BY-4.0",
            }
        ],
    }
    (sub / "bad.json").write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(seed_loader, "SPEC038_SEED_ROOT", tmp_path, raising=False)
    return tmp_path


def test_protected_record_rejected(protected_seed_root):
    client = FakeCosmosClient()
    with pytest.raises(seed_loader.SeedRejectedError) as exc:
        seed_loader.seed_spec038_subdirectories(client, "disaster-hub")
    assert "PSPF" in str(exc.value) or "pspf" in str(exc.value)

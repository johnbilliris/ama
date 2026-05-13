"""Spec-039 T021: loader rejects records missing fictitious/licence markers (FR-015)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from packages.domain.src.domain.seed._fixture_marker import FixtureMarkerError  # noqa: E402
from scripts import seed_loader  # noqa: E402
from tests.integration.spec039_fakes import FakeCosmosClient  # noqa: E402


@pytest.fixture()
def bad_seed_root(tmp_path: Path, monkeypatch):
    sub = tmp_path / "alert-templates"
    sub.mkdir()
    bad = {
        "_fixture": {
            "fictitious": True,
            "residency": "AU",
            # licence missing — should reject
            "schema_version": "1",
        },
        "records": [{"id": "x", "fictitious": True, "residency": "AU"}],
    }
    (sub / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(seed_loader, "SPEC038_SEED_ROOT", tmp_path, raising=False)
    return tmp_path


def test_loader_rejects_unmarked_wrapper(bad_seed_root):
    client = FakeCosmosClient()
    with pytest.raises(FixtureMarkerError) as exc:
        seed_loader.seed_spec039_subdirectories(client, "disaster-hub")
    assert exc.value.field == "licence"
    container = client.db.get_container_client("seed")
    assert container.upsert_calls == 0  # no commits


def test_loader_rejects_record_missing_fictitious(tmp_path: Path, monkeypatch):
    sub = tmp_path / "alert-templates"
    sub.mkdir()
    doc = {
        "_fixture": {
            "fictitious": True,
            "residency": "AU",
            "licence": "CC-BY-4.0",
            "schema_version": "1",
        },
        "records": [{"id": "x", "residency": "AU"}],  # no fictitious
    }
    (sub / "bad.json").write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(seed_loader, "SPEC038_SEED_ROOT", tmp_path, raising=False)

    client = FakeCosmosClient()
    with pytest.raises(FixtureMarkerError) as exc:
        seed_loader.seed_spec039_subdirectories(client, "disaster-hub")
    assert exc.value.field == "fictitious"

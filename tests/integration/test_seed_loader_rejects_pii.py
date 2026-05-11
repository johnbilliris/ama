"""Spec-038 T023: loader rejects records that look like real PII (FR-045)."""

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
def pii_seed_root(tmp_path: Path, monkeypatch):
    sub = tmp_path / "vulnerable-categories"
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
                "id": "v1",
                "fictitious": True,
                "residency": "AU",
                "pspf": "OFFICIAL",
                "licence": "CC-BY-4.0",
                # Address + AU mobile pair — paired PII detector should fire.
                "address": "12 George Street, Sydney NSW 2000",
                "phone": "+61412345678",
            }
        ],
    }
    (sub / "bad.json").write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(seed_loader, "SPEC038_SEED_ROOT", tmp_path, raising=False)
    return tmp_path


def test_pii_record_rejected(pii_seed_root):
    client = FakeCosmosClient()
    with pytest.raises(seed_loader.SeedRejectedError) as exc:
        seed_loader.seed_spec038_subdirectories(client, "disaster-hub")
    assert "PII" in str(exc.value) or "pii" in str(exc.value).lower()

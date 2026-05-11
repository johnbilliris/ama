"""T114 — Entity test for ``ama_domain.OfflineCacheManifest`` (Spec 036 / FR-RAG-LS-02).

Pydantic-v2 round-trip validation. The pydantic model in
``packages/domain/src/ama_domain/offline_cache.py`` mirrors
``packages/schemas/spec_036/offline-cache-manifest.json``; this test pins:

* Validators: ``ttl_days == 14``, ``stale_warning_days == 11``,
  ``size_bytes_total ∈ [1, 524_288_000]``, ``corpus_build_sha`` 64-hex,
  jurisdiction in the closed set.
* Both ``signatures.cosign_keyless`` and ``signatures.age_detached`` MUST be
  non-empty; either missing/empty raises ``ValidationError``.
* ``frozen=True`` semantics — instances are immutable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _example_dict() -> dict[str, Any]:
    sha = "f9c3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a26"
    return {
        "version": 1,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "corpus_build_sha": sha,
        "ttl_days": 14,
        "stale_warning_days": 11,
        "embedding_model_id": "text-embedding-3-large",
        "entries": [
            {
                "chunk_id": "nt-cyclone-doctrine-p12-c0",
                "jurisdiction": "nt",
                "topic": "cyclone-doctrine",
                "page": 12,
                "sha256_of_chunk": "0" * 64,
                "licence_mode": "full-text",
                "byte_offset": 0,
                "byte_length": 8192,
            }
        ],
        "size_bytes_total": 8192,
        "signatures": {
            "cosign_keyless": "MEYCIQDx...",
            "age_detached": "-----BEGIN AGE ENCRYPTED FILE-----\nABC=\n-----END AGE ENCRYPTED FILE-----",
        },
    }


def test_happy_path_round_trip() -> None:
    dom = _domain()
    payload = _example_dict()
    manifest = dom.OfflineCacheManifest.model_validate(payload)
    assert manifest.ttl_days == 14
    assert manifest.stale_warning_days == 11
    assert manifest.signatures.cosign_keyless == "MEYCIQDx..."
    assert manifest.signatures.age_detached.startswith("-----BEGIN AGE")


def test_size_cap_enforced() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["size_bytes_total"] = 524_288_001
    with pytest.raises(Exception):  # noqa: B017 — pydantic ValidationError
        dom.OfflineCacheManifest.model_validate(payload)


def test_size_cap_min_one_byte() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["size_bytes_total"] = 0
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_ttl_must_be_14() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["ttl_days"] = 7
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_stale_warning_must_be_11() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["stale_warning_days"] = 10
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_missing_cosign_keyless_rejected() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["signatures"].pop("cosign_keyless")
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_missing_age_detached_rejected() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["signatures"].pop("age_detached")
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_empty_signature_rejected() -> None:
    """Empty string for either signature is rejected (R-07 fail-closed)."""
    dom = _domain()
    payload = _example_dict()
    payload["signatures"]["age_detached"] = ""
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_unknown_jurisdiction_rejected() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["entries"][0]["jurisdiction"] = "xx"
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_invalid_sha_rejected() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["corpus_build_sha"] = "deadbeef"
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_extra_field_rejected() -> None:
    """``extra='forbid'`` blocks unexpected fields."""
    dom = _domain()
    payload = _example_dict()
    payload["secret"] = "leak"
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)


def test_frozen_immutability() -> None:
    dom = _domain()
    manifest = dom.OfflineCacheManifest.model_validate(_example_dict())
    with pytest.raises(Exception):
        manifest.ttl_days = 7  # type: ignore[misc]


def test_no_entries_rejected() -> None:
    dom = _domain()
    payload = _example_dict()
    payload["entries"] = []
    with pytest.raises(Exception):
        dom.OfflineCacheManifest.model_validate(payload)

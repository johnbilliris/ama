from __future__ import annotations

import pytest


def test_non_test_registry_fails_closed_without_azure_configuration(monkeypatch):
    from app.services.evidence._clients import (
        EvidenceClientRegistry,
        close_registry,
    )

    close_registry()
    monkeypatch.delenv("AMA_TEST_MODE", raising=False)
    for name in (
        "AMA_EVIDENCE_COSMOS_ENDPOINT",
        "COSMOS_ENDPOINT",
        "AZURE_COSMOS_ENDPOINT",
        "AMA_EVIDENCE_BLOB_ENDPOINT",
        "AMA_EVIDENCE_STORAGE_ACCOUNT_NAME",
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="FR-042/FR-029"):
        EvidenceClientRegistry.from_environment()


def test_test_registry_uses_memory_only_with_explicit_sentinel(monkeypatch):
    from app.services.evidence._clients import EvidenceClientRegistry

    monkeypatch.setenv("AMA_TEST_MODE", "1")
    registry = EvidenceClientRegistry.from_environment()

    assert registry.get("evidence_audit").all() == []
    assert registry.blob_archive.health() is True

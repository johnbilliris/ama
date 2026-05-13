"""Unit test: Client fail-fast on missing Azure config (T-AMD-23, T-AMD-08, FR-042)."""

from __future__ import annotations

import os

import pytest


def test_get_registry_fails_without_azure_config_and_no_test_mode():
    """get_registry() raises RuntimeError when Azure config is missing and AMA_TEST_MODE != '1' (T-AMD-23, FR-042)."""
    # Clear any existing registry and environment vars
    import apps.api.app.services.evidence._clients as clients_module

    clients_module._registry = None
    old_test_mode = os.environ.pop("AMA_TEST_MODE", None)
    old_cosmos = os.environ.pop("AMA_EVIDENCE_COSMOS_ENDPOINT", None)
    old_azure_cosmos = os.environ.pop("AZURE_COSMOS_ENDPOINT", None)

    try:
        with pytest.raises(RuntimeError) as exc_info:
            clients_module.get_registry()

        assert "FR-042" in str(exc_info.value)
        assert "Azure Cosmos" in str(exc_info.value)
        assert "refusing to start" in str(exc_info.value).lower()

    finally:
        # Restore environment
        if old_test_mode:
            os.environ["AMA_TEST_MODE"] = old_test_mode
        if old_cosmos:
            os.environ["AMA_EVIDENCE_COSMOS_ENDPOINT"] = old_cosmos
        if old_azure_cosmos:
            os.environ["AZURE_COSMOS_ENDPOINT"] = old_azure_cosmos
        # Reset registry for other tests
        clients_module._registry = None


def test_get_registry_succeeds_with_test_mode():
    """get_registry() succeeds when AMA_TEST_MODE=1 (T-AMD-23)."""
    import apps.api.app.services.evidence._clients as clients_module

    clients_module._registry = None
    os.environ["AMA_TEST_MODE"] = "1"
    os.environ.pop("AMA_EVIDENCE_COSMOS_ENDPOINT", None)
    os.environ.pop("AZURE_COSMOS_ENDPOINT", None)

    try:
        registry = clients_module.get_registry()
        assert registry is not None
    finally:
        clients_module._registry = None


def test_get_registry_succeeds_with_azure_config():
    """get_registry() succeeds when Azure Cosmos endpoint is configured (T-AMD-23)."""
    import apps.api.app.services.evidence._clients as clients_module

    clients_module._registry = None
    os.environ.pop("AMA_TEST_MODE", None)
    os.environ["AMA_EVIDENCE_COSMOS_ENDPOINT"] = "https://cosmos.example.com"

    try:
        registry = clients_module.get_registry()
        assert registry is not None
    finally:
        os.environ.pop("AMA_EVIDENCE_COSMOS_ENDPOINT", None)
        clients_module._registry = None

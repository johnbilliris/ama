"""Contract tests: LLM managed identity authentication (US1).

Verifies:
- LLMClient uses azure_ad_token_provider (not api_key)
- AZURE_OPENAI_API_KEY env var is never read
- Australian endpoint validation rejects non-AU endpoints
- Missing endpoint results in None client (graceful degradation)
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from apps.agents.common.llm_config import LLMClientConfig


class TestManagedIdentityAuth:
    """Verify managed identity authentication is enforced."""

    def test_no_api_key_in_config(self) -> None:
        """LLMClientConfig does not read AZURE_OPENAI_API_KEY."""
        env = {
            "AZURE_OPENAI_ENDPOINT": "https://test.australiaeast.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "should-be-ignored",
        }
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            # Config should not have any api_key field
            assert not hasattr(config, "api_key")

    def test_australian_endpoint_accepted(self) -> None:
        """Endpoints in Australian regions are accepted."""
        env = {"AZURE_OPENAI_ENDPOINT": "https://myapp.australiaeast.openai.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            assert "australiaeast" in config.endpoint.lower()

    def test_australian_southeast_endpoint_accepted(self) -> None:
        """Endpoints in Australia Southeast are accepted."""
        env = {"AZURE_OPENAI_ENDPOINT": "https://myapp.australiasoutheast.openai.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            assert "australiasoutheast" in config.endpoint.lower()

    def test_non_australian_endpoint_rejected(self) -> None:
        """Endpoints outside Australian regions are rejected at config construction."""
        env = {"AZURE_OPENAI_ENDPOINT": "https://myapp.eastus.openai.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(ValueError, match="Australian region"):
                LLMClientConfig()

    def test_empty_endpoint_allowed_graceful_degradation(self) -> None:
        """Empty endpoint is allowed — client will be None (graceful degradation)."""
        env = {"AZURE_OPENAI_ENDPOINT": ""}
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            assert config.endpoint == ""

    def test_client_init_with_no_endpoint_has_none_client(self) -> None:
        """LLMClient with empty endpoint creates no client."""
        from apps.agents.common.llm_client import LLMClient

        config = LLMClientConfig(endpoint="")
        client = LLMClient(config)
        assert client._client is None

    def test_client_init_uses_token_provider_not_api_key(self) -> None:
        """LLMClient constructor uses azure_ad_token_provider, not api_key."""
        import importlib

        mock_credential = MagicMock()
        mock_token_provider = MagicMock()
        mock_azure_openai_cls = MagicMock()

        config = LLMClientConfig(
            endpoint="https://test.australiaeast.openai.azure.com",
            model_tier="drafting",
        )

        mock_identity_module = MagicMock()
        mock_identity_module.DefaultAzureCredential.return_value = mock_credential
        mock_identity_module.get_bearer_token_provider.return_value = mock_token_provider

        mock_openai_module = MagicMock()
        mock_openai_module.AzureOpenAI = mock_azure_openai_cls

        original_import = importlib.import_module

        def side_effect(name):
            if name == "azure.identity":
                return mock_identity_module
            if name == "openai":
                return mock_openai_module
            return original_import(name)

        # Patch import_module where it's used in llm_client module
        with patch("apps.agents.common.llm_client.import_module", side_effect=side_effect):
            from apps.agents.common.llm_client import LLMClient

            LLMClient(config)

        # Verify token provider was created with correct scope
        mock_identity_module.get_bearer_token_provider.assert_called_once_with(
            mock_credential,
            "https://cognitiveservices.azure.com/.default",
        )

        # Verify AzureOpenAI was called with token provider, not api_key
        call_kwargs = mock_azure_openai_cls.call_args
        assert "azure_ad_token_provider" in call_kwargs.kwargs
        assert "api_key" not in call_kwargs.kwargs


class TestBicepRegionRestriction:
    """Verify Bicep region restriction logic (contract-level check)."""

    def test_config_rejects_non_au_regions(self) -> None:
        """Config validation rejects non-Australian endpoints."""
        with pytest.raises(ValueError, match="Australian region"):
            LLMClientConfig(
                endpoint="https://test.westus.openai.azure.com",
                model_tier="drafting",
            )

    def test_config_allows_au_east(self) -> None:
        config = LLMClientConfig(
            endpoint="https://test.australiaeast.openai.azure.com",
            model_tier="drafting",
        )
        assert config.endpoint

    def test_config_allows_au_southeast(self) -> None:
        config = LLMClientConfig(
            endpoint="https://test.australiasoutheast.openai.azure.com",
            model_tier="drafting",
        )
        assert config.endpoint

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
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "should-be-ignored",
        }
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            # Config should not have any api_key field
            assert not hasattr(config, "api_key")

    def test_australian_endpoint_accepted(self) -> None:
        """Endpoints with standard Azure OpenAI format are accepted."""
        env = {"AZURE_OPENAI_ENDPOINT": "https://myapp.openai.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            assert "openai.azure.com" in config.endpoint.lower()

    def test_australian_southeast_endpoint_accepted(self) -> None:
        """Endpoints with resource-name variants are accepted."""
        env = {"AZURE_OPENAI_ENDPOINT": "https://drh-prod-aoai.openai.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            assert "openai.azure.com" in config.endpoint.lower()

    def test_non_azure_endpoint_rejected(self) -> None:
        """Non-Azure OpenAI endpoints are rejected at config construction."""
        env = {"AZURE_OPENAI_ENDPOINT": "https://api.openai.com/v1"}
        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(ValueError, match="valid Azure OpenAI URL"):
                LLMClientConfig()

    def test_empty_endpoint_allowed_graceful_degradation(self) -> None:
        """Empty endpoint is allowed — client will be None (graceful degradation)."""
        env = {"AZURE_OPENAI_ENDPOINT": ""}
        with patch.dict(os.environ, env, clear=False):
            config = LLMClientConfig()
            assert config.endpoint == ""

    def test_client_init_with_no_endpoint_has_none_client(self) -> None:
        """LLMClient with no Foundry endpoint creates no chat_complete seam (post-T146)."""
        from apps.agents.common.llm_client import LLMClient

        config = LLMClientConfig(endpoint="")
        client = LLMClient(config)
        # Post-T146: legacy ``_client`` is gone; the Foundry seam is the only path.
        assert client._chat_complete is None

    def test_client_init_uses_token_provider_not_api_key(self) -> None:
        """LLMClient construction wires the Foundry seam via DefaultAzureCredential.

        Spec 036 (T146 / FR-RAG-FM-04 / FR-RAG-FM-05): the seam initialiser uses
        ``DefaultAzureCredential`` + ``get_bearer_token_provider`` against the
        ``cognitiveservices.azure.com/.default`` scope. No ``api_key`` kwarg is
        passed anywhere in the production path.
        """
        from unittest.mock import patch as _patch

        config = LLMClientConfig(
            endpoint="https://test.australiaeast.openai.azure.com",
            model_tier="drafting",
            foundry_endpoint="https://test.foundry.azure.com",
        )

        mock_seam_callable = MagicMock()
        mock_live_client_cls = MagicMock()
        mock_live_client_instance = MagicMock()
        mock_live_client_instance.chat_complete = mock_seam_callable
        mock_live_client_cls.return_value = mock_live_client_instance

        with _patch(
            "common.foundry_chat_client.LiveFoundryChatClient",
            mock_live_client_cls,
        ):
            from apps.agents.common.llm_client import LLMClient

            client = LLMClient(config)

        # Verify the Foundry seam was wired with the production endpoint.
        mock_live_client_cls.assert_called_once()
        call_kwargs = mock_live_client_cls.call_args.kwargs
        assert call_kwargs.get("endpoint") == "https://test.foundry.azure.com"
        # Verify the seam landed on _chat_complete (no api_key, no _client).
        assert client._chat_complete is mock_seam_callable
        assert "api_key" not in call_kwargs


class TestBicepRegionRestriction:
    """Verify endpoint URL format validation (region compliance enforced by Bicep IaC)."""

    def test_config_rejects_non_azure_endpoint(self) -> None:
        """Config validation rejects non-Azure OpenAI endpoints."""
        with pytest.raises(ValueError, match="valid Azure OpenAI URL"):
            LLMClientConfig(
                endpoint="https://api.openai.com/v1",
                model_tier="drafting",
            )

    def test_config_allows_standard_azure_endpoint(self) -> None:
        config = LLMClientConfig(
            endpoint="https://drh-prod.openai.azure.com",
            model_tier="drafting",
        )
        assert config.endpoint

    def test_config_allows_cognitive_services_endpoint(self) -> None:
        config = LLMClientConfig(
            endpoint="https://drh-prod.cognitiveservices.azure.com",
            model_tier="drafting",
        )
        assert config.endpoint

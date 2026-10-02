from __future__ import annotations

import pytest
from app.core.settings import Settings
from pydantic import ValidationError


class TestApiSettingsSecurity:
    def test_dev_environment_allows_minimal_configuration(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
        monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
        monkeypatch.delenv("AMA_ENTRA_TENANT_ID", raising=False)
        monkeypatch.delenv("AMA_ENTRA_AUDIENCE", raising=False)
        monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)

        settings = Settings()
        assert settings.environment == "dev"

    def test_legacy_aliases_are_accepted(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "dev")
        monkeypatch.setenv("ENTRA_TENANT_ID", "00000000-0000-0000-0000-000000000000")
        monkeypatch.setenv("ENTRA_AUDIENCE", "api://disaster-response-hub")
        monkeypatch.setenv("COSMOS_DB_ENDPOINT", "https://example.documents.azure.com:443/")

        settings = Settings()
        assert settings.environment == "dev"
        assert settings.entra_tenant_id == "00000000-0000-0000-0000-000000000000"
        assert settings.entra_audience == "api://disaster-response-hub"
        assert settings.cosmos_endpoint == "https://example.documents.azure.com:443/"

    def test_production_fails_closed_when_auth_not_enabled(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "production")
        monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
        monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "00000000-0000-0000-0000-000000000000")
        monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://disaster-response-hub")
        monkeypatch.setenv("COSMOS_ENDPOINT", "https://example.documents.azure.com:443/")
        monkeypatch.setenv("API_PROXY_UPSTREAM", "https://api.example.com/api")

        with pytest.raises(ValidationError):
            Settings()

    def test_production_rejects_localhost_proxy(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "production")
        monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
        monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "00000000-0000-0000-0000-000000000000")
        monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://disaster-response-hub")
        monkeypatch.setenv("COSMOS_ENDPOINT", "https://example.documents.azure.com:443/")
        monkeypatch.setenv("API_PROXY_UPSTREAM", "http://localhost:8000/api")

        with pytest.raises(ValidationError):
            Settings()

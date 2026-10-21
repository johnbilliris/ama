from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def env_contract_module():
    import app.core.env_contract as env_contract

    importlib.reload(env_contract)
    return env_contract


def _clear_env(monkeypatch) -> None:
    keys = [
        "AMA_ENVIRONMENT",
        "ENVIRONMENT",
        "AMA_ENABLE_PRODUCTION_AUTH",
        "ENABLE_PRODUCTION_AUTH",
        "AMA_ENTRA_TENANT_ID",
        "ENTRA_TENANT_ID",
        "AMA_ENTRA_AUDIENCE",
        "ENTRA_AUDIENCE",
        "COSMOS_ENDPOINT",
        "COSMOS_DB_ENDPOINT",
        "AZURE_COSMOS_ENDPOINT",
        "ALLOWED_AZURE_REGIONS",
        "AMA_ALLOWED_AZURE_REGIONS",
        "AMA_ENTRA_TEST_PRINCIPAL",
        "AMA_TRUST_FORWARDED_PRINCIPAL",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_alias_resolution_accepts_deprecated_alias(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("COSMOS_DB_ENDPOINT", "https://example.documents.azure.com:443/")

    resolved = env_contract_module.resolve_canonical_env()

    assert resolved["AMA_ENVIRONMENT"] == "dev"
    assert resolved["COSMOS_ENDPOINT"] == "https://example.documents.azure.com:443/"


def test_alias_conflict_raises(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://a.documents.azure.com:443/")
    monkeypatch.setenv("COSMOS_DB_ENDPOINT", "https://b.documents.azure.com:443/")

    with pytest.raises(env_contract_module.EnvironmentContractError):
        env_contract_module.resolve_canonical_env()


def test_production_requires_auth_and_identity(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("AMA_ENVIRONMENT", "production")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "00000000-0000-0000-0000-000000000000")
    monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://drh")
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://example.documents.azure.com:443/")
    monkeypatch.setenv("ALLOWED_AZURE_REGIONS", "Australia East,Australia Southeast")

    env_contract_module.validate_runtime_environment()


def test_production_rejects_test_principal(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("AMA_ENVIRONMENT", "production")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "tenant")
    monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://drh")
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://example.documents.azure.com:443/")
    monkeypatch.setenv("AMA_ENTRA_TEST_PRINCIPAL", "{}")

    with pytest.raises(env_contract_module.EnvironmentContractError):
        env_contract_module.validate_runtime_environment()


def test_production_rejects_forwarded_trust(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("AMA_ENVIRONMENT", "staging")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "tenant")
    monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://drh")
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://example.documents.azure.com:443/")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")

    with pytest.raises(env_contract_module.EnvironmentContractError):
        env_contract_module.validate_runtime_environment()


def test_allowed_regions_must_be_au(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("ALLOWED_AZURE_REGIONS", "Australia East,East US")

    with pytest.raises(env_contract_module.EnvironmentContractError):
        env_contract_module.validate_runtime_environment()


def test_allowed_regions_malformed_empty_rejected(monkeypatch, env_contract_module):
    _clear_env(monkeypatch)
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("ALLOWED_AZURE_REGIONS", " , ")

    with pytest.raises(env_contract_module.EnvironmentContractError):
        env_contract_module.validate_runtime_environment()

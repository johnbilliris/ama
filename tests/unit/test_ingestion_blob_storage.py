from unittest.mock import Mock, call

import pytest
from azure.core.exceptions import ResourceExistsError

from apps.ingestion.blob_store import AZURITE_BLOB_API_VERSION, RawPayloadBlobStore
from apps.ingestion.worker import _build_raw_payload_blob_store


def test_azurite_blob_store_uses_connection_string_and_creates_local_containers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blob_client = Mock()
    blob_client.create_container.side_effect = ResourceExistsError()
    audit_client = Mock()
    service_client = Mock()
    service_client.get_container_client.side_effect = [blob_client, audit_client, blob_client]
    blob_service_client = Mock()
    blob_service_client.from_connection_string.return_value = service_client
    monkeypatch.setattr("azure.storage.blob.BlobServiceClient", blob_service_client)

    RawPayloadBlobStore(
        "devstoreaccount1",
        connection_string="azurite-local-connection-string",
    )

    blob_service_client.from_connection_string.assert_called_once_with(
        "azurite-local-connection-string",
        api_version=AZURITE_BLOB_API_VERSION,
    )
    assert service_client.get_container_client.call_args_list == [
        call("raw-payloads"),
        call("audit"),
        call("raw-payloads"),
    ]
    blob_client.create_container.assert_called_once_with()
    audit_client.create_container.assert_called_once_with()


def test_azure_blob_store_uses_managed_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    credential = object()
    managed_identity_credential = Mock(return_value=credential)
    blob_service_client = Mock()
    monkeypatch.setattr("azure.identity.ManagedIdentityCredential", managed_identity_credential)
    monkeypatch.setattr("azure.storage.blob.BlobServiceClient", blob_service_client)

    RawPayloadBlobStore("storageaccount")

    managed_identity_credential.assert_called_once_with()
    blob_service_client.assert_called_once_with(
        "https://storageaccount.blob.core.windows.net",
        credential=credential,
    )


def test_local_blob_store_uses_azurite_connection_string(monkeypatch: pytest.MonkeyPatch) -> None:
    blob_store = Mock()
    monkeypatch.setattr("apps.ingestion.blob_store.RawPayloadBlobStore", blob_store)
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("STORAGE_ACCOUNT_NAME", "devstoreaccount1")
    monkeypatch.setenv("AZURITE_BLOB_CONNECTION_STRING", "azurite-local-connection-string")

    result = _build_raw_payload_blob_store()

    assert result is blob_store.return_value
    blob_store.assert_called_once_with(
        "devstoreaccount1",
        connection_string="azurite-local-connection-string",
    )


def test_azure_blob_store_uses_managed_identity_mode_when_azurite_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blob_store = Mock()
    monkeypatch.setattr("apps.ingestion.blob_store.RawPayloadBlobStore", blob_store)
    monkeypatch.setenv("STORAGE_ACCOUNT_NAME", "storageaccount")
    monkeypatch.delenv("AZURITE_BLOB_CONNECTION_STRING", raising=False)
    monkeypatch.setenv("AMA_ENVIRONMENT", "production")

    result = _build_raw_payload_blob_store()

    assert result is blob_store.return_value
    blob_store.assert_called_once_with("storageaccount")


def test_azurite_connection_string_is_rejected_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "production")
    monkeypatch.setenv("STORAGE_ACCOUNT_NAME", "devstoreaccount1")
    monkeypatch.setenv("AZURITE_BLOB_CONNECTION_STRING", "azurite-local-connection-string")

    with pytest.raises(RuntimeError, match="only supported in local development"):
        _build_raw_payload_blob_store()


def test_azurite_connection_string_requires_storage_account_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.delenv("STORAGE_ACCOUNT_NAME", raising=False)
    monkeypatch.setenv("AZURITE_BLOB_CONNECTION_STRING", "azurite-local-connection-string")

    with pytest.raises(RuntimeError, match="STORAGE_ACCOUNT_NAME is required"):
        _build_raw_payload_blob_store()

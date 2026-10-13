import os
from typing import Any


def _resolve_cosmos_credential(
    credential: Any = None,
    *,
    async_client: bool = False,
) -> Any:
    auth_mode = os.getenv("COSMOS_AUTH_MODE", "aad").strip().lower()
    if auth_mode == "key":
        key = os.getenv("COSMOS_KEY")
        if not key:
            raise RuntimeError("COSMOS_KEY is required when COSMOS_AUTH_MODE=key")
        return key
    if auth_mode != "aad":
        raise ValueError(f"Unsupported COSMOS_AUTH_MODE: {auth_mode}")
    if credential is not None:
        return credential

    if async_client:
        from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

        return AsyncDefaultAzureCredential()

    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def create_cosmos_client(endpoint: str, **options: Any) -> Any:
    from azure.cosmos import CosmosClient

    options["credential"] = _resolve_cosmos_credential(options.get("credential"))
    return CosmosClient(endpoint, **options)


def create_async_cosmos_client(endpoint: str, **options: Any) -> Any:
    from azure.cosmos.aio import CosmosClient

    options["credential"] = _resolve_cosmos_credential(
        options.get("credential"),
        async_client=True,
    )
    return CosmosClient(endpoint, **options)

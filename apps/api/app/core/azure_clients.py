from dataclasses import dataclass

from app.core.residency import ResidencyPolicy, build_residency_policy
from app.core.settings import Settings


@dataclass(frozen=True)
class AzureClientRegistry:
    residency_policy: ResidencyPolicy
    cosmos_endpoint: str | None = None
    blob_account_url: str | None = None
    redis_host: str | None = None


def build_azure_clients(settings: Settings) -> AzureClientRegistry:
    return AzureClientRegistry(residency_policy=build_residency_policy(settings.allowed_azure_regions))

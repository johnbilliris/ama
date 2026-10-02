import os
from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_prefix: str = "/api"
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    environment: str = Field(
        default="production",
        validation_alias=AliasChoices("AMA_ENVIRONMENT", "ENVIRONMENT"),
    )
    production_auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AMA_ENABLE_PRODUCTION_AUTH", "ENABLE_PRODUCTION_AUTH"),
    )
    entra_tenant_id: str = Field(
        default="",
        validation_alias=AliasChoices("AMA_ENTRA_TENANT_ID", "ENTRA_TENANT_ID"),
    )
    entra_audience: str = Field(
        default="",
        validation_alias=AliasChoices("AMA_ENTRA_AUDIENCE", "ENTRA_AUDIENCE"),
    )
    cosmos_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("COSMOS_ENDPOINT", "COSMOS_DB_ENDPOINT", "AZURE_COSMOS_ENDPOINT"),
    )
    api_proxy_upstream: str = Field(
        default="",
        validation_alias=AliasChoices("API_PROXY_UPSTREAM", "API_ENDPOINT", "SERVICE_API_ENDPOINT_URL"),
    )
    allowed_azure_regions: list[str] = Field(
        default_factory=lambda: ["Australia East", "Australia Southeast"],
        validation_alias=AliasChoices("ALLOWED_AZURE_REGIONS", "AMA_ALLOWED_AZURE_REGIONS"),
    )
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        alias="CORS_ALLOWED_ORIGINS",
    )

    max_concurrent_simulations: int = Field(default=3, alias="MAX_CONCURRENT_SIMULATIONS")
    simulation_ttl_hours: int = Field(default=72, alias="SIMULATION_TTL_HOURS")
    throttle_threshold_pct: int = Field(default=70, alias="THROTTLE_THRESHOLD_PCT")
    incident_throttle_quota_pct: int = Field(default=20, alias="INCIDENT_THROTTLE_QUOTA_PCT")
    simulation_archive_retention_days: int = Field(default=90, alias="SIMULATION_ARCHIVE_RETENTION_DAYS")
    shared_write_capacity: int = Field(default=10000, alias="SHARED_WRITE_CAPACITY")

    @classmethod
    def model_validate_strings(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_security_posture(self) -> "Settings":
        env = (self.environment or "").strip().lower()
        is_test_runtime = os.environ.get("AMA_TEST_SUPPORT") == "1"
        if env in {"production", "staging"} and not is_test_runtime:
            if not self.production_auth_enabled:
                raise ValueError("Production startup blocked: AMA_ENABLE_PRODUCTION_AUTH must be enabled.")
            if not self.entra_tenant_id or not self.entra_audience:
                raise ValueError("Production startup blocked: Entra tenant/audience must be configured.")
            if not self.cosmos_endpoint:
                raise ValueError("Production startup blocked: COSMOS_ENDPOINT must be configured.")
            if not self.api_proxy_upstream:
                raise ValueError("Production startup blocked: API proxy upstream must be configured.")
            lower_proxy = self.api_proxy_upstream.lower()
            if "localhost" in lower_proxy or "127.0.0.1" in lower_proxy:
                raise ValueError("Production startup blocked: API proxy upstream cannot point to localhost.")
        return self


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.allowed_azure_regions = Settings.model_validate_strings(settings.allowed_azure_regions)
    return settings

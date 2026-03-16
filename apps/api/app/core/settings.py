from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_prefix: str = "/api"
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    allowed_azure_regions: list[str] = Field(
        default_factory=lambda: ["Australia East", "Australia Southeast"],
        alias="ALLOWED_AZURE_REGIONS",
    )

    @classmethod
    def model_validate_strings(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.allowed_azure_regions = Settings.model_validate_strings(settings.allowed_azure_regions)
    return settings

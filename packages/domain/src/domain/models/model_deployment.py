from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ModelDeployment(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )

    deployment_id: str
    endpoint_url: HttpUrl
    model_name: str
    model_version: str | None = None
    api_version: str | None = None
    token_budget_input: int = Field(gt=0)
    token_budget_output: int = Field(gt=0)
    content_safety_policy: Literal["rule_based", "azure_content_safety", "none"] = "rule_based"
    fallback_mode: Literal["template", "error"] = "template"
    timeout_seconds: float = Field(default=30.0, gt=0.0, le=120.0)
    purpose: Literal["reasoning", "drafting"]
    status: Literal["active", "disabled", "degraded"] = "active"

    @field_validator("endpoint_url")
    @classmethod
    def _endpoint_must_be_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("endpoint_url must use https")
        return value

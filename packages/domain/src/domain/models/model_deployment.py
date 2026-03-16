from typing import Literal

from pydantic import BaseModel, HttpUrl


class ModelDeployment(BaseModel):
    deployment_id: str
    endpoint_url: HttpUrl
    model_name: str
    model_version: str | None = None
    api_version: str | None = None
    token_budget_input: int
    token_budget_output: int
    content_safety_policy: Literal["rule_based", "azure_content_safety", "none"] = "rule_based"
    fallback_mode: Literal["template", "error"] = "template"
    timeout_seconds: float = 30.0
    purpose: Literal["reasoning", "drafting"]
    status: Literal["active", "disabled", "degraded"] = "active"

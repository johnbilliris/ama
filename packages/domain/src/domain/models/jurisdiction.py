from typing import Any, Literal

from pydantic import BaseModel


class Jurisdiction(BaseModel):
    jurisdiction_id: str
    name: str
    level: Literal["commonwealth", "state", "territory", "regional", "local"]
    parent_jurisdiction_id: str | None = None
    policy_set_id: str
    geospatial_boundary: dict[str, Any]
    status: Literal["active", "inactive"] = "active"

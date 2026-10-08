from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class Jurisdiction(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    jurisdiction_id: str
    name: str
    level: Literal["commonwealth", "state", "territory", "regional", "local"]
    parent_jurisdiction_id: str | None = None
    policy_set_id: str
    geospatial_boundary: dict[str, Any]
    geometry_fidelity: Literal["official", "approximate"] = "approximate"
    status: Literal["active", "inactive"] = "active"

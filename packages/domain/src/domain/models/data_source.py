from typing import Literal

from pydantic import BaseModel


class DataSource(BaseModel):
    data_source_id: str
    name: str
    kind: Literal[
        "authoritative", "sensor", "iot", "field_report", "social", "community", "derived"
    ]
    authority_rank: int = 0
    status: Literal["available", "degraded", "offline"] = "available"

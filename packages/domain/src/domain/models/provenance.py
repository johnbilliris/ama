from datetime import datetime

from pydantic import BaseModel


class ProvenanceRecord(BaseModel):
    source_name: str
    source_kind: str
    collected_at: datetime
    validation_status: str
    notes: str | None = None

import os
from typing import Literal

from pydantic import BaseModel, Field


class IngestionPipelineConfig(BaseModel):
    pipeline_id: str
    source_class: Literal["authoritative", "sensor", "satellite", "social", "community", "field_report", "ims"]
    data_source_ids: list[str] = Field(min_length=1)
    poll_interval_seconds: int = Field(ge=1)
    endpoint_url: str
    endpoint_format: Literal["xml_bom", "geojson", "json", "cap_xml", "rss", "png", "geotiff", "text"]
    circuit_breaker_threshold: int = Field(default=3, ge=1)
    circuit_breaker_backoff_initial_seconds: int = Field(default=30, ge=1)
    circuit_breaker_backoff_max_seconds: int = Field(default=300, ge=1)
    dedup_ttl_seconds: int = Field(default=0, ge=0)
    max_records_per_cycle: int = Field(default=100, ge=1, le=5000)
    scope: str = Field(default="live", min_length=1)
    enabled: bool = True
    activation_blocker: str | None = None

    def effective_dedup_ttl(self) -> int:
        return self.dedup_ttl_seconds if self.dedup_ttl_seconds > 0 else self.poll_interval_seconds * 2


def resolve_pipeline_configs(configs: list[IngestionPipelineConfig]) -> list[IngestionPipelineConfig]:
    """Apply the worker-wide environment override without mutating source configurations."""
    limit = os.environ.get("INGESTION_MAX_RECORDS_PER_CYCLE")
    if limit is None:
        return configs

    try:
        cycle_limit = int(limit)
        return [
            IngestionPipelineConfig.model_validate({**config.model_dump(), "max_records_per_cycle": cycle_limit})
            for config in configs
        ]
    except ValueError as exc:
        raise ValueError("INGESTION_MAX_RECORDS_PER_CYCLE must be an integer between 1 and 5000") from exc

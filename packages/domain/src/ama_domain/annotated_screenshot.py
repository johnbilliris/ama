"""spec-038 entity — AnnotatedScreenshot + Callout. FR-006, FR-008, FR-010a."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Callout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: int = Field(..., ge=1)
    anchor_dom_path: str = Field(..., min_length=1)
    alt_text: str = Field(..., min_length=1)
    keyboard_steps: list[str] = Field(default_factory=list)


class AnnotatedScreenshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str = "__global__"
    screen_id: str
    route_id: str
    previous_route_id: str | None = None
    screen_id_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    light_blob_uri: str
    dark_blob_uri: str
    alt_text_blob_uri: str
    callouts: list[Callout] = Field(default_factory=list)
    captured_at: datetime
    captured_by: str
    article_ids: list[str] = Field(default_factory=list)
    staleness_flag_id: str | None = None
    created_at: datetime
    updated_at: datetime


__all__ = ["AnnotatedScreenshot", "Callout"]

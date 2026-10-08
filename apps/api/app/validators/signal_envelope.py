from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator


class SignalSourceEnvelope(BaseModel):
    dataSourceId: str
    name: str
    kind: Literal["authoritative", "sensor", "iot", "field_report", "social", "community", "derived"]

    @field_validator("dataSourceId")
    @classmethod
    def data_source_id_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("dataSourceId must be non-empty")
        return v


class SignalLocation(BaseModel):
    type: Literal["Point", "Polygon", "MultiPolygon"]
    coordinates: list[Any]
    precisionMeters: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "SignalLocation":
        value = self.coordinates
        if not value:
            raise ValueError("location.coordinates must not be empty")

        def _check_point(candidate: Any) -> None:
            if not (isinstance(candidate, list) and len(candidate) == 2):
                raise ValueError("Point coordinates must be [longitude, latitude]")
            lon, lat = candidate
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError("Point coordinates must be numeric")
            if not (-180.0 <= float(lon) <= 180.0 and -90.0 <= float(lat) <= 90.0):
                raise ValueError("Point coordinates must be within longitude/latitude bounds")

        if self.type == "Point":
            _check_point(value)
            return self

        if not isinstance(value, list):
            raise ValueError("Polygon coordinates must be a list of linear rings")
        if self.type == "Polygon":
            for ring in value:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise ValueError("Polygon rings must contain at least four positions")
                for point in ring:
                    _check_point(point)
            return self

        for polygon in value:
            if not isinstance(polygon, list) or not polygon:
                raise ValueError("MultiPolygon coordinates must contain polygons")
            for ring in polygon:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise ValueError("MultiPolygon rings must contain at least four positions")
                for point in ring:
                    _check_point(point)
        return self


class SignalProvenance(BaseModel):
    collectionMethod: str
    sourceUri: str
    collector: str | None = None
    validationNotes: str | None = None
    sourceTimestamp: AwareDatetime | None = None
    simulationRunId: str | None = None
    sourceName: str | None = None
    sourceKind: Literal["authoritative", "sensor", "iot", "field_report", "social", "community", "derived"] | None = (
        None
    )
    trustTier: str | None = None
    evaluatedConfidenceScore: float | None = Field(default=None, ge=0.0, le=1.0)
    sourceStatus: str | None = None
    sourceReason: str | None = None
    expectedUpdateSeconds: int | None = Field(default=None, ge=0)
    rawPayloadUri: str | None = None
    owningAgencyId: str | None = None


class SignalEnvelope(BaseModel):
    source: SignalSourceEnvelope
    incidentId: str | None = None
    category: str
    occurredAt: AwareDatetime
    receivedAt: AwareDatetime
    jurisdictionId: str | None = None
    location: SignalLocation
    payload: dict[str, Any] = Field(default_factory=dict)
    confidenceScore: float
    freshnessScore: float
    validationStatus: Literal["pending", "validated", "contradicted", "rejected", "escalated"]
    provenance: SignalProvenance

    @field_validator("category")
    @classmethod
    def category_non_empty(cls, v: str) -> str:
        allowed = {
            "weather",
            "hydrology",
            "fire",
            "geohazard",
            "infrastructure",
            "community_report",
            "social_report",
            "resource_status",
        }
        if not v.strip() or v not in allowed:
            raise ValueError("category must be non-empty")
        return v

    @field_validator("confidenceScore")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidenceScore must be in range [0.0, 1.0]")
        return v

    @field_validator("freshnessScore")
    @classmethod
    def freshness_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("freshnessScore must be in range [0.0, 1.0]")
        return v

    @model_validator(mode="after")
    def validate_time_order(self) -> "SignalEnvelope":
        if self.receivedAt < self.occurredAt:
            raise ValueError("receivedAt must be greater than or equal to occurredAt")
        return self

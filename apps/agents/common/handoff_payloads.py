"""Inter-agent handoff payload models (FR-011, FR-012, FR-016).

Typed payload schemas for:
- TransportHandoffPayload: evacuation → resource_allocation (FR-011)
- DispatchHandoffPayload: resource_allocation → communication (FR-012)
- RoadClosureSignalPayload: monitoring → evacuation (FR-016)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class TransportHandoffPayload(BaseModel):
    """Evacuation → Resource Allocation transport handoff (FR-011).

    Carries vehicle requirements, pickup coordinates, priority tier,
    and traceability back to the evacuation plan.
    """

    evacuation_plan_id: str
    incident_id: str
    zone_number: int
    vehicle_type: str
    quantity_required: int
    pickup_latitude: float
    pickup_longitude: float
    destination_assembly_area_id: str
    priority_tier: str  # "critical" | "immediate" | "high"
    vulnerability_category: str
    estimated_persons: int
    special_considerations: list[str] = Field(default_factory=list)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class DispatchHandoffPayload(BaseModel):
    """Resource Allocation → Communication dispatch notification (FR-012).

    Instructs communication agent to issue public alerts about
    resource deployment and timeline.
    """

    deployment_plan_id: str
    incident_id: str
    deployment_summary: str
    resource_assignments: list[dict[str, Any]] = Field(default_factory=list)
    shortfalls: list[dict[str, Any]] = Field(default_factory=list)
    deployment_timeline: dict[str, Any] = Field(default_factory=dict)
    warning_tier: str = "Advice"  # AWS tier: Advice | Watch and Act | Emergency Warning
    target_languages: list[str] = Field(
        default_factory=lambda: ["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
    )
    dispatched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoadClosureSignalPayload(BaseModel):
    """Monitoring → Evacuation road closure signal (FR-016).

    Notifies evacuation agent of road closures affecting active
    evacuation routes so it can trigger re-routing.
    """

    signal_id: str
    incident_id: str
    road_segment_id: str
    road_name: str = ""
    closure_type: str = "full"  # "full" | "partial" | "weight_limit"
    latitude: float = 0.0
    longitude: float = 0.0
    effective_from: datetime = Field(default_factory=lambda: datetime.now(UTC))
    effective_until: datetime | None = None
    reason: str = ""
    source_device_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

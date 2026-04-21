"""Radius lookup table CRUD API (FR-006 / FR-021).

Admin-editable hazard radius lookup table for GeoJSON polygon generation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.middleware.auth import authorize_admin, authorize_management

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/radius-lookup", tags=["radius-lookup"])

# Seed data — in production, backed by Cosmos DB
_SEED_RADII: dict[str, dict] = {
    "bushfire": {
        "hazard_type": "bushfire",
        "radii": {"1": 1000, "2": 2500, "3": 5000, "4": 7500, "5": 10000},
        "last_updated": "2026-04-21T00:00:00Z",
        "updated_by": "system-seed",
    },
    "flood": {
        "hazard_type": "flood",
        "radii": {"1": 500, "2": 1500, "3": 3000, "4": 4500, "5": 5000},
        "last_updated": "2026-04-21T00:00:00Z",
        "updated_by": "system-seed",
    },
    "earthquake": {
        "hazard_type": "earthquake",
        "radii": {"1": 2000, "2": 5000, "3": 10000, "4": 15000, "5": 20000},
        "last_updated": "2026-04-21T00:00:00Z",
        "updated_by": "system-seed",
    },
    "cyclone": {
        "hazard_type": "cyclone",
        "radii": {"1": 5000, "2": 15000, "3": 30000, "4": 40000, "5": 50000},
        "last_updated": "2026-04-21T00:00:00Z",
        "updated_by": "system-seed",
    },
    "chemical_spill": {
        "hazard_type": "chemical_spill",
        "radii": {"1": 200, "2": 500, "3": 1000, "4": 1500, "5": 2000},
        "last_updated": "2026-04-21T00:00:00Z",
        "updated_by": "system-seed",
    },
}

_radius_store: dict[str, dict] = dict(_SEED_RADII)


class RadiiUpdate(BaseModel):
    radii: dict[str, float]


class RadiusCreate(BaseModel):
    hazard_type: str
    radii: dict[str, float]


@router.get("", dependencies=[Depends(authorize_management)])
async def list_radius_entries() -> dict:
    """List all radius entries (Section 4a)."""
    return {"items": list(_radius_store.values())}


@router.get("/{hazard_type}", dependencies=[Depends(authorize_management)])
async def get_radius_entry(hazard_type: str) -> dict:
    """Get radius entry by hazard type (Section 4b)."""
    entry = _radius_store.get(hazard_type)
    if not entry:
        raise HTTPException(status_code=404, detail="Hazard type not found")
    return entry


@router.put("/{hazard_type}", dependencies=[Depends(authorize_admin)])
async def update_radius_entry(
    hazard_type: str,
    body: RadiiUpdate,
    identity: dict = Depends(authorize_admin),
) -> dict:
    """Update radius entry (Section 4c). Admin only."""
    entry = _radius_store.get(hazard_type)
    if not entry:
        raise HTTPException(status_code=404, detail="Hazard type not found")

    entry["radii"] = body.radii
    entry["last_updated"] = datetime.now(UTC).isoformat()
    entry["updated_by"] = identity.get("sub", "unknown")

    logger.info(
        "radius_entry_updated",
        extra={"hazard_type": hazard_type, "updated_by": entry["updated_by"]},
    )
    return entry


@router.post("", status_code=201, dependencies=[Depends(authorize_admin)])
async def create_radius_entry(
    body: RadiusCreate,
    identity: dict = Depends(authorize_admin),
) -> dict:
    """Create new radius entry (Section 4d). Admin only."""
    if body.hazard_type in _radius_store:
        raise HTTPException(status_code=409, detail="Hazard type already exists")

    entry = {
        "hazard_type": body.hazard_type,
        "radii": body.radii,
        "last_updated": datetime.now(UTC).isoformat(),
        "updated_by": identity.get("sub", "unknown"),
    }
    _radius_store[body.hazard_type] = entry

    logger.info(
        "radius_entry_created",
        extra={"hazard_type": body.hazard_type, "created_by": entry["updated_by"]},
    )
    return entry

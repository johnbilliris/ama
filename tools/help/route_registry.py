"""spec-038 T-AA177 — Help route registry.

Single source of truth for ``route_id ↔ Next.js path`` mapping. Supports
``previous_route_id`` for bulk re-baseline (FR-010a-AMEND).
"""

from __future__ import annotations

from typing import TypedDict


class RouteEntry(TypedDict, total=False):
    route_id: str
    path: str
    anchors: list[str]
    previous_route_id: str | None


REGISTRY: dict[str, RouteEntry] = {
    "disaster-mapper": {"route_id": "disaster-mapper", "path": "/", "anchors": ["#legend", "#layers", "#filters"]},
    "governance-dashboard": {
        "route_id": "governance-dashboard",
        "path": "/governance/dashboard",
        "anchors": ["#gates", "#audit"],
    },
    "simulation-control": {"route_id": "simulation-control", "path": "/simulations", "anchors": ["#warp", "#playback"]},
    "alert-composer": {"route_id": "alert-composer", "path": "/alerts/compose", "anchors": ["#message", "#approvals"]},
    "audit-observer-view": {"route_id": "audit-observer-view", "path": "/audit", "anchors": ["#timeline", "#export"]},
    "persona-switcher": {"route_id": "persona-switcher", "path": "/personas", "anchors": ["#switch"]},
    "settings": {"route_id": "settings", "path": "/settings", "anchors": ["#theme", "#accessibility"]},
    "login": {"route_id": "login", "path": "/login", "anchors": ["#idp"]},
}


def get(route_id: str) -> RouteEntry | None:
    return REGISTRY.get(route_id)


def all_routes() -> list[RouteEntry]:
    return list(REGISTRY.values())


__all__ = ["REGISTRY", "RouteEntry", "all_routes", "get"]

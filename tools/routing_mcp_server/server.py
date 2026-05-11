"""Routing service MCP server (T062, ADR-033-04)."""

from __future__ import annotations

import argparse
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

SERVER_NAME = "ama-routing-mcp"
SERVER_VERSION = "1.0.0"

mcp = FastMCP(SERVER_NAME)


@mcp.tool()
def compute_route(
    origin: dict[str, float],
    destination: dict[str, float],
    *,
    avoid_road_segments: list[str] | None = None,
) -> dict[str, Any]:
    """Compute an evacuation route. Stub returns deterministic mock data."""
    avoid_road_segments = avoid_road_segments or []
    distance_km = round(
        ((origin["lat"] - destination["lat"]) ** 2 + (origin["lon"] - destination["lon"]) ** 2) ** 0.5 * 111,
        2,
    )
    return {
        "route_id": f"route-{int(distance_km * 100)}",
        "distance_km": distance_km,
        "estimated_minutes": round(distance_km * 1.5, 1),
        "polyline": [origin, destination],
        "avoided_segments": avoid_road_segments,
    }


@mcp.tool()
def list_road_closures(area_bbox: dict[str, float]) -> list[dict[str, Any]]:
    """Stub returning empty list."""
    _ = area_bbox
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    logger.info("Starting %s v%s on %s:%d", SERVER_NAME, SERVER_VERSION, args.host, args.port)
    mcp.run(transport="streamable-http", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

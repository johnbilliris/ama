"""T-G01 — jurisdiction-boundary STRtree service (FR-021).

Loads polygons from Blob ``jurisdiction-boundaries/`` (or, for tests,
from a local fixture directory) into an :class:`shapely.STRtree` at
warm-up. Exposes :func:`infer` returning the
:class:`JurisdictionCode` for a (lat, lng) point in well-under-50 ms p95
on the 10 K-point benchmark.

The loader supports two payload formats:

* **GeoJSON FeatureCollection** (``*.geojson``) — each feature carries
  ``properties.jurisdiction_code``.
* **WKT** (``*.wkt``) — first line is the jurisdiction code, second
  line is the WKT polygon. This is the format used for the small test
  fixture committed at ``tests/fixtures/jurisdiction_boundaries/``.

Live deployment loads from Blob via the supplied ``loader_callable``;
in tests we point at the local fixture directory.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shapely import STRtree
from shapely.geometry import Point, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.wkt import loads as wkt_loads

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JurisdictionPolygon:
    code: str
    geometry: BaseGeometry


@dataclass
class BoundaryServiceMetrics:
    polygons_loaded: int = 0
    last_loaded_at: float = 0.0
    dataset_version: str = "unknown"


class JurisdictionBoundaryService:
    """STRtree-backed jurisdiction boundary lookup."""

    def __init__(self) -> None:
        self._polygons: list[JurisdictionPolygon] = []
        self._tree: STRtree | None = None
        self.metrics = BoundaryServiceMetrics()

    # ------------------------------------------------------------------ load
    def load_from_directory(self, root: Path, *, dataset_version: str = "fixture") -> None:
        polygons: list[JurisdictionPolygon] = []
        for path in sorted(root.glob("*")):
            if path.is_file() and path.suffix.lower() == ".wkt":
                polygons.extend(_parse_wkt_file(path))
            elif path.is_file() and path.suffix.lower() == ".geojson":
                polygons.extend(_parse_geojson_file(path))
        self._set_polygons(polygons, dataset_version=dataset_version)

    def load_from_geojson_features(
        self,
        features: Iterable[dict[str, Any]],
        *,
        dataset_version: str = "blob",
    ) -> None:
        polygons: list[JurisdictionPolygon] = []
        for feature in features:
            code = (feature.get("properties") or {}).get("jurisdiction_code")
            geom = feature.get("geometry")
            if not code or not geom:
                continue
            polygons.append(JurisdictionPolygon(code=code, geometry=shape(geom)))
        self._set_polygons(polygons, dataset_version=dataset_version)

    def _set_polygons(
        self, polygons: list[JurisdictionPolygon], *, dataset_version: str
    ) -> None:
        self._polygons = list(polygons)
        if self._polygons:
            self._tree = STRtree([p.geometry for p in self._polygons])
        else:
            self._tree = None
        self.metrics.polygons_loaded = len(self._polygons)
        self.metrics.last_loaded_at = time.time()
        self.metrics.dataset_version = dataset_version
        logger.info(
            "jurisdiction_boundary_service.loaded count=%d dataset=%s",
            self.metrics.polygons_loaded,
            self.metrics.dataset_version,
        )

    # --------------------------------------------------------------- inference
    def infer(self, lat: float, lng: float) -> str | None:
        """Return jurisdiction code containing the point, or ``None``."""
        if self._tree is None or not self._polygons:
            return None
        point = Point(lng, lat)  # GeoJSON ordering: (x=lng, y=lat)
        candidate_indices = self._tree.query(point)
        for idx in candidate_indices:
            poly = self._polygons[int(idx)]
            if poly.geometry.covers(point):
                return poly.code
        return None

    @property
    def polygons(self) -> list[JurisdictionPolygon]:
        return list(self._polygons)


# ------------------------------------------------------------------ helpers


def _parse_wkt_file(path: Path) -> list[JurisdictionPolygon]:
    text = path.read_text(encoding="utf-8")
    out: list[JurisdictionPolygon] = []
    code: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if code is None:
            code = line
            continue
        try:
            geom = wkt_loads(line)
        except Exception:  # noqa: BLE001
            logger.warning("jurisdiction_boundary.bad_wkt path=%s", path)
            code = None
            continue
        out.append(JurisdictionPolygon(code=code, geometry=geom))
        code = None
    return out


def _parse_geojson_file(path: Path) -> list[JurisdictionPolygon]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") == "FeatureCollection":
        features = payload.get("features") or []
    elif payload.get("type") == "Feature":
        features = [payload]
    else:
        return []
    out: list[JurisdictionPolygon] = []
    for feature in features:
        code = (feature.get("properties") or {}).get("jurisdiction_code")
        geom = feature.get("geometry")
        if not code or not geom:
            continue
        out.append(JurisdictionPolygon(code=code, geometry=shape(geom)))
    return out


def export_polygon_as_geojson(polygon: JurisdictionPolygon) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": {"jurisdiction_code": polygon.code},
        "geometry": mapping(polygon.geometry),
    }


# Optional Blob loader factory (signature matches T-G01 acceptance).
BlobLoader = Callable[[str], list[dict[str, Any]]]


def make_service_from_blob(
    *,
    container_name: str = "jurisdiction-boundaries",
    blob_loader: BlobLoader,
    dataset_version: str = "platform-registry-v3",
) -> JurisdictionBoundaryService:
    svc = JurisdictionBoundaryService()
    features = blob_loader(container_name)
    svc.load_from_geojson_features(features, dataset_version=dataset_version)
    return svc


__all__ = [
    "BlobLoader",
    "BoundaryServiceMetrics",
    "JurisdictionBoundaryService",
    "JurisdictionPolygon",
    "export_polygon_as_geojson",
    "make_service_from_blob",
]

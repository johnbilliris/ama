"""Pillar B — Measurement Method router (T-B05, contracts: getMeasurementMethod)."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from .._correlation import correlation_id_dep
from .renderer import render

router = APIRouter(tags=["evidence-measurement"])


@router.get("/measurement-method", operation_id="getMeasurementMethod")
def get_measurement_method(
    format: Literal["json", "markdown"] = Query(default="json"),
    correlation_id: str = Depends(correlation_id_dep),
) -> Response:
    from ..kpi_ladder.router import _ensure_seed

    _ensure_seed()
    body = render(format)
    if format == "markdown":
        return Response(content=str(body), media_type="text/markdown")
    return Response(content=json.dumps(body, default=str), media_type="application/json")

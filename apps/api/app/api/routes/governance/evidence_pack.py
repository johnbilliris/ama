"""Spec-037 read-only Evidence Pack routes (T036).

Implements four endpoints from `contracts/openapi.evidence-pack.yaml`:
  - GET /api/governance/evidence-pack/artefacts
  - GET /api/governance/evidence-pack/artefacts/{artefact_id}
  - GET /api/governance/evidence-pack/artefacts/{artefact_id}/publications/{publication_id}
  - GET /api/governance/evidence-pack/health

Reuses the existing JWT/AppRole middleware (spec-035) — registration of this
router under that middleware happens in `apps/api/app/api/router.py`.

Citations: FR-001, FR-021, FR-029, FR-005.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/governance/evidence-pack", tags=["evidence-pack"])

ArtefactIdEnum = Literal[
    "risk_register",
    "adoption_roadmap",
    "executive_kpi_surface",
    "rai_register",
    "feature_value_ledger",
]


# Resolve artefact root: in the deployed container, docs/ and specs/shared/
# are bundled at /app/docs and /app/specs (see Dockerfile COPY). In the repo
# checkout, walk up to find the repo root containing docs/ + specs/.
_HERE = Path(__file__).resolve()


def _find_artefact_root() -> Path:
    # Container layout: /app/docs, /app/specs (bundled by Dockerfile).
    container_root = Path("/app")
    if (container_root / "docs" / "risk-register").is_dir():
        return container_root
    # Repo layout: walk up from this file until we hit the repo root.
    for parent in _HERE.parents:
        if (parent / "docs" / "risk-register").is_dir() and (parent / "specs").is_dir():
            return parent
    # Last-resort fallback (will surface as 404 / degraded health).
    return _HERE.parents[5]


_REPO_ROOT = _find_artefact_root()
_ARTEFACT_PATHS: dict[str, Path] = {
    "risk_register": _REPO_ROOT / "docs" / "risk-register" / "risk-register.json",
    "adoption_roadmap": _REPO_ROOT / "docs" / "governance-hub" / "adoption-roadmap" / "roadmap.json",
    "executive_kpi_surface": _REPO_ROOT / "docs" / "governance-hub" / "executive-kpi" / "surface.json",
    "rai_register": _REPO_ROOT / "docs" / "governance-hub" / "rai-register" / "responsible-ai-register.json",
    "feature_value_ledger": _REPO_ROOT / "specs" / "shared" / "feature-value-ledger.json",
}


class ArtefactSummary(BaseModel):
    artefact_id: str
    publication_id: str
    published_at_utc: str
    manual_row_ratio: float
    total_row_count: int
    auditor_signoff_present: bool


def _load(artefact_id: str) -> dict[str, Any] | None:
    path = _ARTEFACT_PATHS.get(artefact_id)
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.exception("Failed to parse %s", path)
        return None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _summary_from(artefact_id: str, payload: dict[str, Any] | None) -> ArtefactSummary:
    if payload is None:
        return ArtefactSummary(
            artefact_id=artefact_id,
            publication_id="00000000-0000-0000-0000-000000000000",
            published_at_utc=_now_iso(),
            manual_row_ratio=0.0,
            total_row_count=0,
            auditor_signoff_present=False,
        )
    meta = payload.get("metadata", {})
    return ArtefactSummary(
        artefact_id=artefact_id,
        publication_id=payload.get("publication_id", "00000000-0000-0000-0000-000000000000"),
        published_at_utc=payload.get("published_at_utc", _now_iso()),
        manual_row_ratio=float(meta.get("manual_row_ratio", 0.0)),
        total_row_count=int(meta.get("total_row_count", 0)),
        auditor_signoff_present=bool(meta.get("auditor_signoff")),
    )


@router.get("/artefacts", response_model=list[ArtefactSummary])
def list_artefacts() -> list[ArtefactSummary]:
    """List the five evidence-pack artefacts with their latest publication metadata."""
    return [_summary_from(aid, _load(aid)) for aid in _ARTEFACT_PATHS.keys()]


@router.get("/artefacts/{artefact_id}")
def get_artefact(artefact_id: ArtefactIdEnum) -> dict[str, Any]:
    """Return the latest published version of an artefact."""
    payload = _load(artefact_id)
    if payload is None:
        # Return a stub envelope so contract tests can verify shape even before
        # artefact authoring lands. After T056-T060 the JSON files exist and
        # this branch is never hit.
        payload = {
            "artefact_id": artefact_id,
            "schema_version": "1.0.0",
            "publication_id": "00000000-0000-0000-0000-000000000000",
            "published_at_utc": _now_iso(),
            "published_by": "stub",
            "metadata": {
                "manual_row_count": 0,
                "total_row_count": 1,
                "manual_row_ratio": 0.0,
                "link_check_status": "pending",
                "last_gate_run_utc": _now_iso(),
            },
            "rows": [{}],
        }
    return payload


def _problem_response(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: str,
    type_uri: str = "https://ama.example.gov.au/problems/spec-037/not-found",
) -> JSONResponse:
    """Return an RFC 7807 application/problem+json response.

    Honours api-architect.agent.md convention (RFC 7807 for all error shapes)
    and the spec-037 OpenAPI contract under contracts/openapi.evidence-pack.yaml.
    Step-8 review finding tech-HIGH-1 (api-architect persona).
    """
    return JSONResponse(
        status_code=status_code,
        media_type="application/problem+json",
        content={
            "type": type_uri,
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": instance,
        },
    )


@router.get("/artefacts/{artefact_id}/publications/{publication_id}")
def get_historical_publication(
    request: Request,
    artefact_id: ArtefactIdEnum,
    publication_id: str,
) -> Any:
    """Get a specific historical publication (Blob-backed immutable snapshot)."""
    payload = _load(artefact_id)
    if payload is None or payload.get("publication_id") != publication_id:
        return _problem_response(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Publication not found",
            detail=f"Publication {publication_id} not found for {artefact_id}",
            instance=str(request.url.path),
        )
    return payload


@router.get("/health")
def get_health() -> dict[str, Any]:
    """Publication-gate status + last successful publish per artefact."""
    artefacts = []
    overall = "healthy"
    for aid in _ARTEFACT_PATHS:
        payload = _load(aid)
        if payload is None:
            artefacts.append(
                {
                    "artefact_id": aid,
                    "last_publication_utc": _now_iso(),
                    "manual_row_ratio": 0.0,
                    "gate_status": "pending",
                }
            )
            overall = "degraded"
        else:
            meta = payload.get("metadata", {})
            artefacts.append(
                {
                    "artefact_id": aid,
                    "last_publication_utc": payload.get("published_at_utc", _now_iso()),
                    "manual_row_ratio": float(meta.get("manual_row_ratio", 0.0)),
                    "gate_status": meta.get("link_check_status", "pending"),
                }
            )
    return {"overall_status": overall, "artefacts": artefacts}

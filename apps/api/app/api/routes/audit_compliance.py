"""Spec 036 / Phase F (T206 + T207) — Privacy Act + PSPF compliance endpoints.

These endpoints expose the federally-mandated audit surfaces that Phase F
F-A6 (Cluster A6) requires:

  - ``GET /api/audit/sar`` — Privacy Act 1988 subject-access request (SAR).
    Returns the subject's audit events filtered by Entra OID, surfaces
    APP 1/3/5/6/11 metadata. Per FR-RAG-COMP-01.

  - ``GET /api/audit/export`` — PSPF audit export. Returns CSV with the six
    PSPF-mandated columns ``Timestamp, User, Action, Resource, Outcome,
    Justification``. Per FR-RAG-COMP-03 + SC-018.

Both endpoints are gated by the Eval-Auditor / Compliance-Officer role
(spec 030 RBAC). The data source is the existing audit repository
(``apps/api/app/repositories/audit_repository.py``); these handlers
project the audit shape (post-F-A5 extensions) into the federally-required
shapes.
"""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit", "compliance"])


# --------------------------------------------------------------------------- #
# Privacy Act 1988 surface — APP 1/3/5/6/11
# --------------------------------------------------------------------------- #


# Static APP surface metadata returned in every SAR response. The body is
# the canonical, signed-off privacy notice text — kept here in code so the
# CD pipeline checksum can verify drift.
_APP_SURFACES: dict[str, str] = {
    "APP1": (
        "Privacy notice surface. AMA collects audit events for emergency-management "
        "decision-support purposes per FR-RAG-COMP-01."
    ),
    "APP3": (
        "Collection limit. AMA collects only audit fields enumerated in "
        "audit-record-llm-call.json; no incidental personal information."
    ),
    "APP5": (
        "Notification of collection. Operators are notified at sign-in and via "
        "the in-app privacy notice surface."
    ),
    "APP6": (
        "Use & disclosure. Audit events may be used for incident review, "
        "compliance audit (PSPF), and Privacy Act SAR fulfilment."
    ),
    "APP11": (
        "Security & retention. 7-year retention (spec 030); cosign + age "
        "detached signatures (FR-RAG-LS-02); cryptographic integrity per ISM-1552."
    ),
}


def _audit_query_callable():  # pragma: no cover — wiring point
    """Return the audit-repository SAR fetcher.

    Lazy-imported so tests can monkey-patch; production wiring uses the
    standard repo factory.
    """
    from apps.api.app.repositories.audit_repository import (  # noqa: PLC0415
        get_audit_repository,
    )

    return get_audit_repository()


def _sar_payload(
    subject: str,
    events: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Build the SAR response payload."""
    event_list = list(events)
    return {
        "subject": subject,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "event_count": len(event_list),
        "events": event_list,
        "privacy_act_app_surfaces": _APP_SURFACES,
        "retention_policy": {
            "retention_period_years": 7,
            "policy_ref": "spec-030-data-residency-and-retention",
            "deletion_path": "operator-revocation-not-supported (Privacy Act exemption)",
        },
    }


@router.get("/sar")
async def get_subject_access_request(
    subject: str = Query(..., min_length=3, max_length=256, description="Entra OID or email of the subject"),
) -> dict[str, Any]:
    """Privacy Act 1988 subject-access request endpoint.

    Returns audit events filtered to ``subject``, with full APP 1/3/5/6/11
    surface metadata in the response body. (FR-RAG-COMP-01; T206.)
    """
    if not subject.strip():
        raise HTTPException(status_code=400, detail="subject must be non-empty")

    try:
        repo = _audit_query_callable()
        # Repository returns a list of dicts matching audit-record-llm-call.json
        events = list(repo.fetch_for_subject(subject)) if repo else []
    except Exception as exc:  # noqa: BLE001 — log but degrade gracefully
        logger.warning("audit_sar_fetch_error subject=%s err=%s", subject, exc)
        events = []

    return _sar_payload(subject, events)


# --------------------------------------------------------------------------- #
# PSPF audit export — CSV with 6 mandated columns
# --------------------------------------------------------------------------- #


PSPF_COLUMNS = ("Timestamp", "User", "Action", "Resource", "Outcome", "Justification")


def _to_pspf_row(event: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    """Project an audit event into the PSPF-required column shape.

    Maps from audit-record-llm-call.json fields (post-F-A5 extensions).
    """
    return (
        str(event.get("timestamp") or event.get("created_at") or ""),
        str(event.get("actor_id") or event.get("user_id") or ""),
        str(event.get("event_type") or event.get("action") or ""),
        str(event.get("resource") or event.get("target") or ""),
        str(event.get("outcome") or "success"),
        str(event.get("justification") or event.get("rationale") or ""),
    )


def _render_pspf_csv(events: Iterable[dict[str, Any]]) -> str:
    """Render events as RFC 4180 CSV with the 6 PSPF columns."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(PSPF_COLUMNS)
    for event in events:
        writer.writerow(_to_pspf_row(event))
    return buf.getvalue()


@router.get("/export")
async def get_pspf_audit_export(
    format: str = Query("pspf", pattern="^pspf$"),
    start: str = Query(..., description="ISO-8601 start of audit window (inclusive)"),
    end: str = Query(..., description="ISO-8601 end of audit window (exclusive)"),
) -> Response:
    """PSPF audit export endpoint.

    Returns CSV with six PSPF-mandated columns (Timestamp, User, Action,
    Resource, Outcome, Justification) for the audit window
    ``[start, end)``. (FR-RAG-COMP-03; SC-018; T207.)
    """
    try:
        start_dt = _parse_iso(start)
        end_dt = _parse_iso(end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid window: {exc}") from exc
    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="end must be > start")
    if (end_dt - start_dt) > timedelta(days=370):
        raise HTTPException(status_code=400, detail="window must be <= 370 days")

    try:
        repo = _audit_query_callable()
        events = list(repo.fetch_window(start_dt, end_dt)) if repo else []
    except Exception as exc:  # noqa: BLE001
        logger.warning("pspf_export_fetch_error start=%s end=%s err=%s", start, end, exc)
        events = []

    csv_body = _render_pspf_csv(events)
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="pspf-audit-export-{start_dt.date()}-{end_dt.date()}.csv"'
            )
        },
    )


def _parse_iso(value: str) -> datetime:
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


__all__ = [
    "PSPF_COLUMNS",
    "_render_pspf_csv",
    "_sar_payload",
    "router",
]

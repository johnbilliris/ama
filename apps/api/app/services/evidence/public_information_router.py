from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from ._correlation import correlation_id_dep
from ._problem_details import ProblemDetails
from .instrumentation import audit_manager
from .public_information import PublicInformationRender, render_public_information

router = APIRouter(tags=["evidence-public-information"])


@router.get(
    "/public-information/{scenario_id}",
    operation_id="getPublicInformationForScenario",
    response_model=PublicInformationRender,
    response_model_exclude_none=True,
)
def get_public_information(
    request: Request,
    scenario_id: str = Path(...),
    lang: str = Query(
        default="en-AU",
        min_length=2,
        max_length=32,
        pattern=r"^[A-Za-z_-]+$",
    ),
    correlation_id: str = Depends(correlation_id_dep),
) -> PublicInformationRender:
    try:
        rendered = render_public_information(
            scenario_id,
            requested_language=lang,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails.of(
                status=404,
                title="public-information-scenario-not-found",
                detail=str(exc),
                type="https://ama.example/errors/public-information-scenario-not-found",
            ).model_dump(),
        ) from exc

    claims = getattr(request.state, "claims", {}) or {}
    actor = str(claims.get("oid") or claims.get("sub") or "anonymous")
    for channel in rendered.channels:
        if channel.language_fallback_used is None:
            continue
        audit_manager.record(
            kind="language_fallback_used",
            value_id=f"{rendered.scenario_id}:{channel.language_code}",
            actor=actor,
            payload={"language_fallback_used": channel.language_fallback_used},
            correlation_id=correlation_id,
        )
    return rendered

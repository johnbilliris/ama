"""FR-028 outcome-evaluator route (cycle-1 amendment, spec 034 — T178).

``POST /api/outcomes/sc-{sc_id}/evaluate`` — capstone-outcome evaluator
for SC-001..SC-005 (Pass 5 Q29 routable range). Routes outside that range
return HTTP 400 with a body that names the CI-artefact owner.

Activation is dual-guarded by ``app.middleware.test_support_guard.is_enabled``:
the router is only mounted when the canonical ``AMA_TEST_SUPPORT == "1"``
env var is set AND ``settings.environment in {"dev", "test"}``. Production
registration is forbidden — refer to ``app.api.router`` for the
registration block (mirrors the test-support router pattern).

Contract: ``specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md``.
"""

from __future__ import annotations

from typing import Any

from app.services.outcome_evaluator_service import (
    EvaluatorError,
)
from app.services.outcome_evaluator_service import (
    evaluate as evaluate_service,
)
from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/outcomes", tags=["outcome-evaluator"])


# ---------------------------------------------------------------------------
# Request / Response models. Match the contract's embedded JSON Schema.
# ``additionalProperties: false`` is enforced via ``model_config``.
# ---------------------------------------------------------------------------


class EvaluatorRequest(BaseModel):
    """FR-028 request body. Idempotency tuple member: correlation_id."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(
        ...,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="Kebab-case scenario id; MUST resolve in bootstrap_seed_data() scenarios",
    )
    persona_id: str = Field(
        ...,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="MUST resolve in bootstrap_seed_data().identities (ASM-011)",
    )
    correlation_id: str = Field(
        ...,
        description="UUID v4 propagated via X-Correlation-Id header",
    )
    metric_inputs: dict[str, Any] = Field(
        ...,
        description="Sc_id-specific shape; see contracts/outcome-evaluator.contract.md",
    )


class EvaluatorResponse(BaseModel):
    """FR-028 response body. Status + audit_id form the contract surface."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern=r"^(pass|fail|gap)$")
    evidence_refs: list[str] = Field(default_factory=list)
    metric_value: float | None = None
    threshold: float | None = None
    audit_id: str = Field(..., description="UUID v4 of the appended audit row")


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/sc-{sc_id}/evaluate")
def evaluate_outcome(
    sc_id: str = Path(  # noqa: B008 — FastAPI default-value pattern
        ...,
        pattern=r"^[0-9]{3}$",
        description="Zero-padded outcome number (001..005 routable; 006..011 returns 400 per Q29)",
    ),
    body: EvaluatorRequest = ...,  # type: ignore[assignment]  # noqa: B008
    *,
    request: Request,
) -> JSONResponse:
    full_sc_id = f"sc-{sc_id}"
    try:
        result = evaluate_service(
            sc_id=full_sc_id,
            scenario_id=body.scenario_id,
            persona_id=body.persona_id,
            correlation_id=body.correlation_id,
            metric_inputs=body.metric_inputs,
        )
    except EvaluatorError as exc:
        # Bypass the global error wrapper so the structured contract
        # payload (error code, ci_job, suggested_action) survives.
        return JSONResponse(status_code=exc.status_code, content=exc.payload)
    _ = request  # correlation_id is in the body; no need to read header
    return JSONResponse(status_code=200, content=result)

# Explicit replay and persisted scorecard readback routes.

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from .._correlation import correlation_id_dep
from .._problem_details import ProblemDetails
from ..instrumentation import audit_manager
from ..models.audit import AuditKind
from ..models.scorecard import DeltaScorecard
from .orchestrator import EvidenceEventSource, RunMode, default_event_source
from .repository import (
    RunPairIdentityConflict,
    get_by_run_pair,
    get_latest_scorecard,
    get_scorecard,
    persist_scorecard,
)
from .scenarios import SCENARIOS
from .scorecard_builder import (
    ImputationSignoffRequiredError,
    ImputationSignoffResolver,
    MissingEvidenceSourceError,
    build_scorecard,
)
from .signoff import AuditImputationSignoffResolver, record_imputation_signoff

router = APIRouter(tags=["evidence-replay"])
_event_source_override: EvidenceEventSource | None = None
_signoff_resolver: ImputationSignoffResolver | None = None


class ReplayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: str = Field(min_length=1, max_length=256)
    run_pair_id: str = Field(min_length=1, max_length=256)
    repetitions: int = Field(default=1, ge=1, le=100)
    allow_degraded_mode: bool = True
    baseline_simulation_id: str | None = Field(default=None, min_length=1, max_length=256)
    ama_assisted_simulation_id: str | None = Field(default=None, min_length=1, max_length=256)


class ImputationSignoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_pair_id: str = Field(min_length=1, max_length=256)
    scenario_content_hash: str | None = Field(default=None, min_length=64, max_length=64)
    imputation_share: Decimal = Field(gt=Decimal("0.10"), le=Decimal("1"))
    approval_id: str = Field(min_length=1, max_length=128)
    basis: str = Field(min_length=8, max_length=2000)


def configure_event_source(source: EvidenceEventSource | None) -> None:
    global _event_source_override
    _event_source_override = source


def configure_imputation_signoff_resolver(resolver: ImputationSignoffResolver | None) -> None:
    global _signoff_resolver
    _signoff_resolver = resolver


def _source_run_ids(body: ReplayRequest) -> dict[RunMode, str] | None:
    if body.baseline_simulation_id is None and body.ama_assisted_simulation_id is None:
        return None
    return {
        "baseline": body.baseline_simulation_id or body.run_pair_id,
        "ama_assisted": body.ama_assisted_simulation_id or body.run_pair_id,
    }


def _first_reference(scorecard: DeltaScorecard, field: str) -> str | None:
    for provenance in scorecard.run_provenance:
        values = getattr(provenance, field)
        if values:
            return values[0]
    return None


def _audit_references(scorecard: DeltaScorecard) -> dict[str, str]:
    candidates = {
        "signal_id": _first_reference(scorecard, "signal_ids"),
        "model_output_id": _first_reference(scorecard, "model_output_ids"),
        "recommendation_id": _first_reference(scorecard, "recommendation_ids"),
        "human_decision_id": _first_reference(scorecard, "human_decision_ids"),
        "outcome_id": _first_reference(scorecard, "outcome_ids"),
        "simulation_event_id": _first_reference(scorecard, "source_event_ids"),
    }
    return {key: value for key, value in candidates.items() if value is not None}


def _record_lineage_nodes(
    *,
    scorecard: DeltaScorecard,
    references: dict[str, str],
    correlation_id: str,
) -> None:
    kind_by_reference: dict[str, AuditKind] = {
        "signal_id": "signal_ingested",
        "model_output_id": "model_output_recorded",
        "recommendation_id": "recommendation_recorded",
        "human_decision_id": "human_decision_recorded",
        "outcome_id": "outcome_recorded",
    }
    for reference_key, audit_kind in kind_by_reference.items():
        reference_id = references.get(reference_key)
        if reference_id is None:
            continue
        audit_manager.record(
            kind=audit_kind,
            value_id=reference_id,
            actor="simulation-event-adapter",
            payload={
                "scorecard_id": scorecard.id,
                "run_pair_id": scorecard.run_pair_id,
                "reference_kind": reference_key,
            },
            correlation_id=correlation_id,
        )


@router.post(
    "/scenarios/{scenario_id}/replay",
    response_model=DeltaScorecard,
    operation_id="replayScenario",
)
def replay_scenario(
    body: ReplayRequest,
    scenario_id: Literal[
        "bushfire",
        "flood",
        "cyclone",
        "urban_fire",
        "mass_casualty",
        "hazmat",
        "marine_sar",
    ] = Path(...),
    correlation_id: str = Depends(correlation_id_dep),
) -> DeltaScorecard:
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="unknown scenario")

    existing = get_by_run_pair(body.run_pair_id)
    if existing is not None:
        if existing.scenario_id != scenario_id or existing.seed != body.seed:
            raise HTTPException(status_code=409, detail="run_pair_id is already bound to another scenario or seed")
        return existing

    try:
        scorecard = build_scorecard(
            scenario_id=scenario_id,
            seed=body.seed,
            run_pair_id=body.run_pair_id,
            repetitions=body.repetitions,
            allow_degraded_mode=body.allow_degraded_mode,
            source_run_ids=_source_run_ids(body),
            event_source=_event_source_override or default_event_source(),
            signoff_resolver=_signoff_resolver or AuditImputationSignoffResolver(),
            correlation_id=correlation_id,
        )
        scorecard = persist_scorecard(scorecard)
    except MissingEvidenceSourceError as exc:
        raise HTTPException(
            status_code=422,
            detail=ProblemDetails.of(
                status=422,
                title="required-evidence-source-unavailable",
                detail=f"Missing evidence sources: {', '.join(exc.missing)}",
                type="https://ama.example/errors/required-evidence-source-unavailable",
            ).model_dump(),
        ) from exc
    except ImputationSignoffRequiredError as exc:
        raise HTTPException(
            status_code=409,
            detail=ProblemDetails.of(
                status=409,
                title="named-auditor-signoff-required",
                detail=f"Imputation share {exc.share} exceeds the 10% publication gate.",
                type="https://ama.example/errors/named-auditor-signoff-required",
            ).model_dump(),
        ) from exc
    except RunPairIdentityConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    references = _audit_references(scorecard)
    _record_lineage_nodes(
        scorecard=scorecard,
        references=references,
        correlation_id=correlation_id,
    )
    audit_manager.record(
        kind="scorecard_published",
        value_id=scorecard.id,
        actor="system",
        references=references,
        payload={
            "scenario_id": scenario_id,
            "scenario_version": scorecard.scenario_version,
            "scenario_content_hash": scorecard.scenario_content_hash,
            "seed": body.seed,
            "run_pair_id": body.run_pair_id,
        },
        correlation_id=correlation_id,
    )
    if scorecard.reduced_fidelity:
        audit_manager.record(
            kind="degraded_mode_entered",
            value_id=scorecard.id,
            actor="system",
            references=references,
            payload={
                "no_signal_kpis": [
                    delta.kpi_id for delta in scorecard.kpi_deltas if delta.measurement_status == "no_signal"
                ]
            },
            correlation_id=correlation_id,
        )
    if any(delta.small_sample for delta in scorecard.kpi_deltas):
        audit_manager.record(
            kind="small_sample_labelled",
            value_id=scorecard.id,
            actor="system",
            references=references,
            payload={"imputation_share": str(scorecard.imputation_share)},
            correlation_id=correlation_id,
        )
    if scorecard.determinism is not None and scorecard.determinism.diverged:
        audit_manager.record(
            kind="divergence_flagged",
            value_id=scorecard.id,
            actor="system",
            references=references,
            payload={"reproduction_rate": scorecard.determinism.reproduction_rate},
            correlation_id=correlation_id,
        )
    return scorecard


@router.post(
    "/scenarios/{scenario_id}/imputation-signoffs",
    status_code=status.HTTP_201_CREATED,
    operation_id="recordReplayImputationSignoff",
)
def create_imputation_signoff(
    request: Request,
    body: ImputationSignoffRequest,
    scenario_id: Literal[
        "bushfire",
        "flood",
        "cyclone",
        "urban_fire",
        "mass_casualty",
        "hazmat",
        "marine_sar",
    ] = Path(...),
    correlation_id: str = Depends(correlation_id_dep),
) -> dict[str, str]:
    claims = getattr(request.state, "claims", {}) or {}
    roles = {str(role) for role in (claims.get("roles") or [claims.get("app_role") or claims.get("appRole")]) if role}
    auditor_id = str(claims.get("oid") or claims.get("sub") or "")
    if not roles.intersection({"observer-auditor", "system-administrator"}):
        raise HTTPException(
            status_code=403,
            detail=ProblemDetails.of(
                status=403,
                title="auditor-role-required",
                detail="Observer-auditor or system-administrator role is required.",
                type="https://ama.example/errors/auditor-role-required",
            ).model_dump(),
        )
    record_imputation_signoff(
        scenario_id=scenario_id,
        run_pair_id=body.run_pair_id,
        scenario_content_hash=body.scenario_content_hash,
        imputation_share=body.imputation_share,
        auditor_id=auditor_id,
        approval_id=body.approval_id,
        basis=body.basis,
        correlation_id=correlation_id,
    )
    return {"status": "recorded", "auditor_id": auditor_id}


@router.get(
    "/scorecards/latest",
    response_model=DeltaScorecard,
    operation_id="getLatestDeltaScorecard",
)
def latest_scorecard(
    scenario_id: Literal[
        "bushfire",
        "flood",
        "cyclone",
        "urban_fire",
        "mass_casualty",
        "hazmat",
        "marine_sar",
    ]
    | None = Query(default=None),
) -> DeltaScorecard:
    scorecard = get_latest_scorecard(scenario_id=scenario_id)
    if scorecard is None:
        raise HTTPException(status_code=404, detail="no persisted scorecard")
    return scorecard


@router.get(
    "/scorecards/{scorecard_id}",
    response_model=DeltaScorecard,
    operation_id="getDeltaScorecard",
)
def read_scorecard(scorecard_id: str) -> DeltaScorecard:
    scorecard = get_scorecard(scorecard_id)
    if scorecard is None:
        raise HTTPException(status_code=404, detail="scorecard not found")
    return scorecard

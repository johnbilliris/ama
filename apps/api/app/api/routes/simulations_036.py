"""Spec 036 simulation realm — REST surface (T-A19 placeholders + T-C10/T-E01..03 impls).

Routes:
  - POST /api/simulations/{simId}/inject-telemetry  (T-C10, FR-007)
  - POST /api/simulations/{simId}/abort             (T-E01, FR-059, ADR-036-002)
  - POST /api/simulations/{simId}/pause             (T-E02, FR-059)
  - POST /api/simulations/{simId}/resume            (T-E03, FR-059)
  - GET  /api/simulations/{simId}/recent-signals    (T-L07 / T-AA01, FR-013)

These endpoints are stand-alone from the spec-024 ``simulations.py`` router so
the existing tenant-pause/resume verbs (operating on ``tenant_id`` URL slugs)
remain untouched. The new endpoints use ``sim_id`` (UUID) per
``contracts/openapi-simulation.yaml``.

Wave 4 / spec-036 closing wave additions:
  - T-M01..M04: ``Depends(require_simulation_coordinator)`` enforces RBAC on
    every coordinator-only route. Anonymous fallbacks are PROHIBITED in
    production (the ``anonymous-coord`` placeholder at the previous
    line 150-153 has been removed).
  - T-L02: ``inject-telemetry`` now drives the
    :class:`SignalPipelineOrchestrator` for the ``triggered_sub_agents``
    list (no longer ``[]``).
  - T-L07 / T-AA01: ``recent_signals`` is now loaded from the
    :class:`SyntheticSignalsRepository` (10-minute window per FR-013 / I3).
  - T-P02..P04: ``lifecycle.refused_while_paused`` audit + 409 refusal
    middleware on the inject route; ``audit.watermark.applied`` envelope
    written by the public-warning watermark guard.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.api.dependencies.lifecycle_guard import make_lifecycle_guard
from app.api.dependencies.simulation_rbac import (
    CoordinatorPrincipal,
    require_simulation_coordinator,
)
from app.services.simulation.dispatch_status import (
    TriggeredSubAgent,
)
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["simulation"])


_TELEMETRY_INJECTION_PROMPT_CACHE: str | None = None


def _load_telemetry_injection_prompt() -> str:
    """Read and cache the agent's prompt.md from disk."""
    global _TELEMETRY_INJECTION_PROMPT_CACHE
    if _TELEMETRY_INJECTION_PROMPT_CACHE is None:
        from pathlib import Path as _Path

        prompt_path = _Path(__file__).resolve().parents[4] / "agents" / "simulation_telemetry_injection" / "prompt.md"
        try:
            _TELEMETRY_INJECTION_PROMPT_CACHE = prompt_path.read_text(encoding="utf-8")
        except OSError:
            _TELEMETRY_INJECTION_PROMPT_CACHE = ""
    return _TELEMETRY_INJECTION_PROMPT_CACHE


# Pre-built lifecycle guards for each verb (T-P02). Each guard refuses
# requests against a paused / aborted simulation with HTTP 409 +
# ``lifecycle.refused_while_paused`` audit.
_inject_lifecycle_guard = make_lifecycle_guard("telemetry_injection")


# ---------------------------------------------------------------------------
# Request / response models (mirror contracts/openapi-simulation.yaml).
# ---------------------------------------------------------------------------


class ViewportHint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    centroid_lat: float | None = Field(default=None, ge=-90, le=90)
    centroid_lng: float | None = Field(default=None, ge=-180, le=180)
    client_jurisdiction: str | None = None


class TelemetryInjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_text: str = Field(min_length=1, max_length=4000)
    viewport_hint: ViewportHint | None = None


class InjectionRefusal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str
    original_text_hash: str | None = None
    parsed_category: str | None = None
    inferred_confidence: str | None = None
    clarification_question: str | None = None


class TelemetryInjectionAck(BaseModel):
    """HTTP 202 response body for ``POST /api/simulations/{sim_id}/inject-telemetry``.

    Cycle 2 BREAKING bump (T-AA07 / T-AA08 — OpenAPI v0.3.0):

    * ``triggered_sub_agents`` items change from ``str`` to
      :class:`apps.api.app.services.simulation.dispatch_status.TriggeredSubAgent`
      per Cycle 2 Amendment A2-01 / FR-067 + pass-1 Q4 (per-subscriber
      ``correlation_id`` semantics, lexicographic ordering by PascalCase
      ``sub_agent`` enum). Byte-equality between this array and the
      ``signal_pipeline.dispatch_failed`` audit envelope's array is
      enforced by RFC 8785 JCS canonicalisation (pass-1 Q1 + CHK135).
    * ``degraded_dispatch: bool = False`` is **always present** on every
      HTTP 202 response per Cycle 2 pass-2 Q2 — clients (web Controller
      pane, CLI test harness, future external integrations) can rely on a
      stable shape without ``KeyError`` / null-check defensive code. The
      field is the source-of-truth for whether the paired
      ``signal_pipeline.dispatch_failed`` audit envelope was written for
      this request: ``degraded_dispatch == True`` ⇔ exactly one
      dispatch-failed envelope exists for this ``injection_correlation_id``.
    """

    model_config = ConfigDict(extra="forbid")
    injection_correlation_id: str
    signals: list[dict[str, Any]] = Field(default_factory=list)
    refusals: list[InjectionRefusal] = Field(default_factory=list)
    triggered_sub_agents: list[TriggeredSubAgent] = Field(default_factory=list)
    degraded_dispatch: bool = Field(
        default=False,
        description=(
            "Cycle 2 pass-2 Q2 always-present invariant — True iff the "
            "orchestrator dispatch raised mid-fan-out and a "
            "signal_pipeline.dispatch_failed envelope was written; False "
            "on full success."
        ),
    )


class AbortRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = Field(default=None, max_length=500)


class AbortResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aborted: bool = True
    cancelled_invocations: int = 0
    lessons_capture_started: bool = True
    abort_audit_id: str


class LifecycleAck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: str


# ---------------------------------------------------------------------------
# Endpoint placeholders (T-A19). Real implementations land in Phase C / Phase E.
# ---------------------------------------------------------------------------


def _validate_sim_id(sim_id: str | UUID) -> UUID:
    if isinstance(sim_id, UUID):
        return sim_id
    try:
        return UUID(sim_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="simId must be a UUID") from exc


@router.post(
    "/{sim_id}/inject-telemetry",
    response_model=TelemetryInjectionAck,
    operation_id="injectTelemetry",
    status_code=status.HTTP_202_ACCEPTED,
)
async def inject_telemetry(
    request: Request,
    body: TelemetryInjectionRequest,
    sim_id: str = Path(..., min_length=1),
    principal: CoordinatorPrincipal = Depends(require_simulation_coordinator),
) -> TelemetryInjectionAck:
    """Direct-REST telemetry-injection entry point (T-C10).

    Drives the Phase-C pipeline (PII scrub → life-safety gate → LLM strict
    JSON or fallback regex → contradiction detection) and emits the
    ``injection.attempted`` and ``injection.success`` / ``injection.refused``
    audit envelopes via :class:`AuditWriter`.

    The HTTP layer does not own LLM credentials directly — when the
    ``app.state.telemetry_injection_llm_call`` callable is configured the
    handler routes through it; otherwise the deterministic regex fallback
    extractor is used (FR-016).

    Wave 4 amendments (T-M01, T-L02, T-L07/T-AA01, T-P02):
    * ``principal`` is a validated :class:`CoordinatorPrincipal` (RBAC
      enforced; anonymous fallbacks removed).
    * The lifecycle guard refuses requests against a paused / aborted
      simulation with HTTP 409 + ``lifecycle.refused_while_paused``.
    * ``recent_signals`` is now loaded from the synthetic-signals
      repository (10-minute window per FR-013 / I3).
    * The ``triggered_sub_agents`` list is populated by the
      :class:`SignalPipelineOrchestrator` fan-out.
    """
    import hashlib

    from app.api.dependencies.lifecycle_guard import _read_state_safely
    from app.repositories.synthetic_signals_repository import (
        get_synthetic_signals_repository,
    )
    from app.services.simulation.audit_writer import get_audit_writer
    from app.services.simulation.life_safety_gate import (
        evaluate as _life_safety_evaluate,
    )
    from app.services.simulation.signal_pipeline_factory import (
        get_signal_pipeline_orchestrator,
    )

    from apps.agents.simulation_telemetry_injection import handler as ti_handler

    _validate_sim_id(sim_id)

    # T-P02 — refuse while paused / aborted (HTTP 409 + audit).
    state = await _read_state_safely(sim_id)
    if state != "active":
        idempotency_key = request.headers.get("Idempotency-Key")
        request_correlation_id = request.headers.get("X-Request-Correlation-Id") or str(uuid4())
        try:
            await get_audit_writer().write(
                "lifecycle.refused_while_paused",
                simulation_id=sim_id,
                actor="lifecycle_guard",
                request_correlation_id=request_correlation_id,
                idempotency_key=idempotency_key,
                details={
                    "attempted_action": "telemetry_injection",
                    "coordinator_user_id": principal.user_id,
                    "idempotency_key": idempotency_key,
                    "request_correlation_id": request_correlation_id,
                    "refusal_response_status": 409,
                },
            )
        except Exception:
            logger.exception("lifecycle.refused_audit_failed sim=%s state=%s", sim_id, state)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://aidr.gov.au/problems/lifecycle-state-conflict",
                "title": "Simulation not active",
                "status": 409,
                "current_state": state,
                "attempted_action": "telemetry_injection",
            },
        )

    correlation_id = str(uuid4())
    user_id = principal.user_id
    tenant_id = principal.tenant_id

    # Load the system prompt from the agent's prompt.md file (cached in module state).
    system_prompt = _load_telemetry_injection_prompt()

    text_hash = hashlib.sha256(body.chat_text.encode("utf-8")).hexdigest()
    audit = get_audit_writer()
    parse_started_at = datetime.now(UTC)
    try:
        await audit.write(
            "injection.attempted",
            simulation_id=sim_id,
            correlation_id=correlation_id,
            details={
                "chat_turn_id": correlation_id,
                "user_id": user_id,
                "original_text_hash": text_hash,
                "parse_started_at": parse_started_at,
                "viewport_centroid_lat": body.viewport_hint.centroid_lat if body.viewport_hint else None,
                "viewport_centroid_lng": body.viewport_hint.centroid_lng if body.viewport_hint else None,
                "pii_redactions": 0,
            },
        )
    except Exception:
        logger.exception("telemetry-injection: audit.attempted failed sim=%s", sim_id)

    # Locate optional LLM call wired into app.state at startup.
    llm_call = getattr(request.app.state, "telemetry_injection_llm_call", None)

    # T-L07 / T-AA01 — load recent signals from the repository (10-minute window).
    try:
        signals_repo = get_synthetic_signals_repository()
        recent_records = await signals_repo.list_recent(sim_id, window_seconds=600)
        recent_signals = tuple(recent_records)
    except Exception:  # noqa: BLE001 — defensive
        logger.exception("recent_signals.lookup_failed sim=%s", sim_id)
        recent_signals = ()

    outcome = await ti_handler.handle(
        prompt=body.chat_text,
        user_id=user_id,
        simulation_id=sim_id,
        tenant_id=tenant_id,
        llm_call=llm_call,
        system_prompt=system_prompt,
        circuit_probe=None,
        life_safety_evaluator=_life_safety_evaluate,
        recent_signals=recent_signals,
    )

    if not outcome.accepted:
        await audit.write(
            "injection.refused",
            simulation_id=sim_id,
            correlation_id=correlation_id,
            details={
                "chat_turn_id": correlation_id,
                "reason": outcome.refusal_reason or "malformed_input",
                "original_text_hash": text_hash,
                "clarification_question": outcome.clarification_question,
            },
        )
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://aidr.gov.au/problems/injection-refused",
                "title": "Injection refused",
                "status": 400,
                "reason": outcome.refusal_reason,
                "clarification_question": outcome.clarification_question,
            },
        )

    assert outcome.signal is not None

    # T-L02 / T-AA13 / T-AA14 — drive the signal pipeline orchestrator for
    # fan-out and surface degraded-dispatch outcomes per Cycle 2
    # Amendment A2-01 / FR-067 + pass-1 Q1 (byte-equality body↔audit) +
    # pass-2 Q1 (3-value enum + 5 s timeout) + pass-2 Q2 (always-present
    # `degraded_dispatch` flag).
    from app.services.simulation.dispatch_status import (
        DISPATCH_ACK_TIMEOUT_SECONDS,
        TriggeredSubAgent,
    )

    triggered_sub_agents: list[TriggeredSubAgent] = []
    degraded_dispatch = False
    dispatch_exception_class: str | None = None
    dispatch_exception_message: str | None = None
    try:
        orchestrator = get_signal_pipeline_orchestrator()
        dispatch = await orchestrator.dispatch(outcome.signal, correlation_id=correlation_id)
        # Cycle 2 / T-AA14 — orchestrator now surfaces per-subscriber
        # outcomes via ``subscriber_outcomes`` (one entry per ATTEMPTED
        # subscriber) so the route handler can build the byte-equal
        # ``triggered_sub_agents`` array directly. Each outcome carries
        # the dispatch_status (acknowledged|failed|timed_out) per pass-2
        # Q1.
        subscriber_outcomes = getattr(dispatch, "subscriber_outcomes", ())
        if subscriber_outcomes:
            for outcome_entry in subscriber_outcomes:
                triggered_sub_agents.append(
                    TriggeredSubAgent(
                        sub_agent=outcome_entry.sub_agent,
                        trigger_source="primary",
                        correlation_id=outcome_entry.correlation_id,
                        dispatch_status=outcome_entry.dispatch_status,
                    )
                )
            degraded_dispatch = bool(getattr(dispatch, "degraded_dispatch", False))
            if degraded_dispatch:
                # Surface the FIRST failed subscriber's exception details
                # for the dispatch_failed envelope. Per-subscriber detail
                # is preserved in `triggered_sub_agents` so audit consumers
                # can reconstruct.
                first_failure = next(
                    (o for o in subscriber_outcomes if o.dispatch_status != "acknowledged"),
                    None,
                )
                if first_failure is not None:
                    dispatch_exception_class = first_failure.exception_class or "DispatchError"
                    dispatch_exception_message = (
                        first_failure.exception_message or f"{first_failure.dispatch_status} during dispatch"
                    )
        else:
            # Backward-compat (Cycle 1 dispatch result without per-subscriber
            # outcomes) — wrap acknowledged subscribers only.
            per_subscriber_correlations = getattr(dispatch, "per_subscriber_correlations", None)
            for subscriber in dispatch.fanned_out_to:
                sub_corr = (
                    per_subscriber_correlations.get(subscriber)
                    if isinstance(per_subscriber_correlations, dict)
                    else None
                ) or uuid4()
                triggered_sub_agents.append(
                    TriggeredSubAgent(
                        sub_agent=subscriber,
                        trigger_source="primary",
                        correlation_id=sub_corr,
                        dispatch_status="acknowledged",
                    )
                )
    except Exception as exc:  # noqa: BLE001 — Cycle 2 A2-01 degraded-dispatch
        # Cycle 2 / FR-067 — never silent-swallow. The orchestrator already
        # classifies per-subscriber failures internally; this catch handles
        # orchestrator-level failures (e.g. signal-persist failure) that
        # short-circuit the per-subscriber loop entirely.
        degraded_dispatch = True
        dispatch_exception_class = type(exc).__name__
        dispatch_exception_message = str(exc)[:1000]  # PII-scrubbed cap
        logger.exception(
            "signal_pipeline.dispatch_failed sim=%s correlation=%s exc=%s",
            sim_id,
            correlation_id,
            dispatch_exception_class,
        )

    # Lexicographic ordering by PascalCase sub_agent (pass-1 Q4) — required
    # for byte-equality with the audit envelope's array (pass-1 Q1).
    triggered_sub_agents.sort(key=lambda entry: entry.sub_agent)

    if degraded_dispatch:
        # Cycle 2 / T-AA09 / T-AA14 — write typed dispatch-failed envelope.
        try:
            from app.services.simulation.audit_writer import (
                write_dispatch_failed,
            )

            await write_dispatch_failed(
                audit,
                simulation_id=sim_id,
                injection_correlation_id=correlation_id,
                exception_class=dispatch_exception_class or "Exception",
                exception_message=dispatch_exception_message or "",
                triggered_sub_agents=triggered_sub_agents,
                prompt_hash=text_hash,
                prompt_hash_source="raw_user_input",
                idempotency_key=request.headers.get("Idempotency-Key"),
                request_correlation_id=request.headers.get("X-Request-Correlation-Id") or correlation_id,
                dispatch_ack_timeout_seconds=DISPATCH_ACK_TIMEOUT_SECONDS,
            )
        except Exception:
            logger.exception(
                "signal_pipeline.dispatch_failed audit write failed sim=%s correlation=%s",
                sim_id,
                correlation_id,
            )

    # T-L08 / T-AA15 — audit success carries subscriber list (byte-equal to
    # response body's array per pass-1 Q1; RFC 8785 JCS canonical). Skip on
    # fully-failed dispatch (zero acknowledged subscribers — only the
    # dispatch_failed envelope is written then, per spec.md L131 + audit-
    # envelope.md §3.25 acceptance bullet).
    fully_failed = degraded_dispatch and not any(e.dispatch_status == "acknowledged" for e in triggered_sub_agents)
    if not fully_failed:
        from app.services.simulation.audit_writer import (
            canonicalise_triggered_sub_agents,
        )

        await audit.write(
            "injection.success",
            simulation_id=sim_id,
            correlation_id=correlation_id,
            details={
                "chat_turn_id": correlation_id,
                "injection_correlation_id": correlation_id,
                "signal_ids": [outcome.signal.signal_id],
                "categories": [outcome.signal.category],
                "confidences": [outcome.signal.confidence],
                "triggered_sub_agents": canonicalise_triggered_sub_agents(triggered_sub_agents),
            },
        )

    logger.info(
        "telemetry-injection accepted sim=%s correlation=%s path=%s subscribers=%s",
        sim_id,
        correlation_id,
        outcome.extraction_path,
        triggered_sub_agents,
    )
    return TelemetryInjectionAck(
        injection_correlation_id=correlation_id,
        signals=[outcome.signal.model_dump(mode="json")],
        refusals=[],
        triggered_sub_agents=triggered_sub_agents,
        degraded_dispatch=degraded_dispatch,
    )


@router.post(
    "/{sim_id}/abort",
    response_model=AbortResponse,
    operation_id="abortSimulation",
    status_code=status.HTTP_200_OK,
)
async def abort_simulation_036(
    request: Request,
    sim_id: str = Path(..., min_length=1),
    body: AbortRequest | None = None,
    principal: CoordinatorPrincipal = Depends(require_simulation_coordinator),
) -> AbortResponse:
    """Direct-REST abort surface (T-E01, FR-059, ADR-036-002).

    Bypasses the LLM tool-loop; cancels in-flight ``asyncio.Task``s via
    :mod:`apps.api.app.services.simulation.cancellation`; emits one
    ``sub_agent.cancel`` audit per cancelled invocation plus a
    ``lifecycle.aborted`` envelope. Phase H lessons-capture is triggered
    asynchronously by the same endpoint (best-effort; does not block).
    """
    from app.services.simulation import cancellation as cancel_scope
    from app.services.simulation.audit_writer import get_audit_writer

    _validate_sim_id(sim_id)
    abort_audit_id = str(uuid4())
    audit = get_audit_writer()

    async def _record_cancel(sub_agent: str, correlation_id: str | None, reason: str) -> None:
        await audit.write(
            "sub_agent.cancel",
            simulation_id=sim_id,
            actor="cancellation_scope",
            details={
                "correlation_id": correlation_id or str(uuid4()),
                "sub_agent": sub_agent,
                "cancellation_reason": "aborted",
                "elapsed_ms": 0,
            },
        )

    cancelled = await cancel_scope.cancel_all(
        simulation_id=sim_id,
        reason="aborted",
        on_cancel=_record_cancel,
    )

    try:
        await audit.write(
            "lifecycle.aborted",
            simulation_id=sim_id,
            actor="lifecycle_endpoint",
            details={
                "coordinator_user_id": principal.user_id,
                "cancelled_invocations": cancelled,
                "abort_timestamp": datetime.now(UTC),
                "reason": (body.reason if body else None),
            },
        )
    except Exception:
        logger.exception("audit.lifecycle_aborted_write_failed sim=%s", sim_id)

    # T-P04 — lifecycle state transition + lessons-capture queue.
    try:
        from app.services.simulation.repositories.simulation_state import (
            ETagConflictError,
            UnknownSimulationError,
            get_simulation_state_repository,
        )

        state_repo = get_simulation_state_repository()
        try:
            current = await state_repo.read(sim_id)
            await state_repo.update_state(sim_id, "aborted", current.etag)
        except UnknownSimulationError:
            await state_repo.bootstrap(sim_id)
            current = await state_repo.read(sim_id)
            await state_repo.update_state(sim_id, "aborted", current.etag)
        except ETagConflictError:
            logger.warning("abort.state_etag_conflict sim=%s — concurrent transition", sim_id)
        except ValueError:
            # Already aborted — idempotent; just continue.
            pass
    except Exception:  # noqa: BLE001
        logger.exception("abort.state_persist_failed sim=%s", sim_id)

    logger.warning(
        "lifecycle.aborted sim=%s audit_id=%s cancelled=%d reason=%r ts=%s",
        sim_id,
        abort_audit_id,
        cancelled,
        body.reason if body else None,
        datetime.now(UTC).isoformat(),
    )
    return AbortResponse(
        aborted=True,
        cancelled_invocations=cancelled,
        lessons_capture_started=True,
        abort_audit_id=abort_audit_id,
    )


@router.post(
    "/{sim_id:uuid}/pause",
    response_model=LifecycleAck,
    operation_id="pauseSimulation",
    status_code=status.HTTP_200_OK,
)
async def pause_simulation_036(
    request: Request,
    sim_id: UUID = Path(...),
    principal: CoordinatorPrincipal = Depends(require_simulation_coordinator),
) -> LifecycleAck:
    """Direct-REST pause (T-E02, FR-059).

    Sets ``simulation_state.state='paused'`` and emits a ``lifecycle.paused``
    audit envelope. Does NOT cancel in-flight tasks (per spec § US9 #4 —
    pause completes in-flight invocations and writes their replies under
    the paused-state audit; resume does not replay).
    """
    from app.services.simulation.audit_writer import get_audit_writer
    from app.services.simulation.repositories.simulation_state import (
        ETagConflictError,
        UnknownSimulationError,
        get_simulation_state_repository,
    )

    sim_id = str(_validate_sim_id(sim_id))
    audit = get_audit_writer()

    # T-P03 — durable state transition with ETag conditional replace.
    try:
        state_repo = get_simulation_state_repository()
        try:
            current = await state_repo.read(sim_id)
            await state_repo.update_state(sim_id, "paused", current.etag)
        except UnknownSimulationError:
            await state_repo.bootstrap(sim_id)
            current = await state_repo.read(sim_id)
            await state_repo.update_state(sim_id, "paused", current.etag)
        except ETagConflictError as exc:
            # T-P03 — surface 412 → 409 conflict per error-responses.md.
            logger.warning("pause.state_etag_conflict sim=%s — concurrent transition", sim_id)
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "https://aidr.gov.au/problems/lifecycle-state-conflict",
                    "title": "Concurrent lifecycle transition",
                    "status": 409,
                    "detail": str(exc),
                },
            ) from exc
        except ValueError as exc:
            # Already terminal (aborted) — surface 409.
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "https://aidr.gov.au/problems/lifecycle-state-conflict",
                    "title": "Simulation in terminal state",
                    "status": 409,
                    "detail": str(exc),
                },
            ) from exc
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("pause.state_persist_failed sim=%s", sim_id)

    try:
        await audit.write(
            "lifecycle.paused",
            simulation_id=sim_id,
            actor="lifecycle_endpoint",
            details={
                "attempted_action": "chat_turn",
                "coordinator_user_id": principal.user_id,
            },
        )
    except Exception:
        logger.exception("audit.lifecycle_paused_write_failed sim=%s", sim_id)
    return LifecycleAck(state="paused")


@router.post(
    "/{sim_id:uuid}/resume",
    response_model=LifecycleAck,
    operation_id="resumeSimulation",
    status_code=status.HTTP_200_OK,
)
async def resume_simulation_036(
    request: Request,
    sim_id: UUID = Path(...),
    principal: CoordinatorPrincipal = Depends(require_simulation_coordinator),
) -> LifecycleAck:
    """Direct-REST resume (T-E03, FR-059).

    Transitions sim state to ``active`` and emits a ``lifecycle.resumed``
    audit envelope. Resume does NOT replay any in-flight invocations that
    completed during the paused interval — those replies are already
    written.
    """
    from app.services.simulation.audit_writer import get_audit_writer
    from app.services.simulation.repositories.simulation_state import (
        ETagConflictError,
        UnknownSimulationError,
        get_simulation_state_repository,
    )

    sim_id = str(_validate_sim_id(sim_id))
    audit = get_audit_writer()

    # T-P03 — durable state transition.
    try:
        state_repo = get_simulation_state_repository()
        try:
            current = await state_repo.read(sim_id)
            await state_repo.update_state(sim_id, "active", current.etag)
        except UnknownSimulationError:
            await state_repo.bootstrap(sim_id)
        except ETagConflictError as exc:
            logger.warning("resume.state_etag_conflict sim=%s — concurrent transition", sim_id)
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "https://aidr.gov.au/problems/lifecycle-state-conflict",
                    "title": "Concurrent lifecycle transition",
                    "status": 409,
                    "detail": str(exc),
                },
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "https://aidr.gov.au/problems/lifecycle-state-conflict",
                    "title": "Simulation in terminal state",
                    "status": 409,
                    "detail": str(exc),
                },
            ) from exc
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("resume.state_persist_failed sim=%s", sim_id)

    try:
        await audit.write(
            "lifecycle.resumed",
            simulation_id=sim_id,
            actor="lifecycle_endpoint",
            details={
                "coordinator_user_id": principal.user_id,
                "previous_paused_duration_seconds": 0,
            },
        )
    except Exception:
        logger.exception("audit.lifecycle_resumed_write_failed sim=%s", sim_id)
    return LifecycleAck(state="active")


# ---------------------------------------------------------------------------
# Wave 4 — recent-signals listing endpoint (T-L07 / FR-013).
# ---------------------------------------------------------------------------


class RecentSignalsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sim_id: str
    window_seconds: int
    signals: list[dict[str, Any]] = Field(default_factory=list)


@router.get(
    "/{sim_id}/recent-signals",
    response_model=RecentSignalsResponse,
    operation_id="listRecentSignals",
    status_code=status.HTTP_200_OK,
)
async def list_recent_signals_036(
    request: Request,
    sim_id: str = Path(..., min_length=1),
    window_seconds: int = 600,
    principal: CoordinatorPrincipal = Depends(require_simulation_coordinator),
) -> RecentSignalsResponse:
    """Return the synthetic signals injected within the freshness window.

    Replaces the previous hardcoded ``recent_signals=()`` (line 197 in the
    pre-Wave-4 file). Per FR-013 / I3 the default window is 10 minutes.
    """
    from app.repositories.synthetic_signals_repository import (
        get_synthetic_signals_repository,
    )

    _validate_sim_id(sim_id)
    if window_seconds <= 0 or window_seconds > 86400:
        raise HTTPException(
            status_code=400,
            detail="window_seconds must be in (0, 86400]",
        )

    repo = get_synthetic_signals_repository()
    records = await repo.list_recent(sim_id, window_seconds=window_seconds)
    return RecentSignalsResponse(
        sim_id=sim_id,
        window_seconds=window_seconds,
        signals=[r.model_dump(mode="json") for r in records],
    )


class OutcomeReadResponse(BaseModel):
    """Response for `GET /simulations/{sim_id}/outcome` (T-H05, FR-054)."""

    model_config = ConfigDict(populate_by_name=True)

    record_id: str
    simulation_id: str
    blob_uri: str
    signed_url: str
    signed_url_expires_at: datetime
    end_reason: str | None = None
    aidr_version: str | None = None


_OUTCOME_SIGNED_URL_TTL_SECONDS_DEFAULT = 300  # 5 minutes — short-TTL


@router.get(
    "/{sim_id}/outcome",
    response_model=OutcomeReadResponse,
    operation_id="readSimulationOutcome",
    status_code=status.HTTP_200_OK,
)
async def read_simulation_outcome_036(
    request: Request,
    sim_id: str = Path(..., min_length=1),
) -> OutcomeReadResponse:
    """Return a short-TTL signed URL pointing at the WORM-persisted outcome blob.

    Per FR-054: requires the ``simulation.read`` Entra app role.
    Per ADR-036-006: the signed URL is short-TTL (≤5 min) so coordinators
    must re-request it every read; the blob itself remains
    legal-hold + locked-time-based-retention for 7 years.

    The implementation here delegates to the
    :func:`apps.api.app.services.simulation.outcome_signed_url.read_outcome`
    helper which is wired to a signed-URL provider in production and to an
    in-memory provider in tests; both honour the short-TTL contract.
    """
    from app.services.simulation.outcome_signed_url import (
        OutcomeNotFound,
        get_outcome_signed_url_provider,
    )

    _validate_sim_id(sim_id)

    # Coarse RBAC: middleware should have enrolled the role; we double-check
    # to keep the contract crisp. Production wiring happens in the auth layer.
    user_roles = getattr(getattr(request, "state", object()), "roles", set()) or set()
    if user_roles and "simulation.read" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "rbac_denied",
                "message": "simulation.read role required for /outcome",
            },
        )

    provider = get_outcome_signed_url_provider()
    try:
        result = await provider.read(sim_id)
    except OutcomeNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "outcome_not_found", "simulation_id": sim_id},
        )
    return OutcomeReadResponse(
        record_id=result.record_id,
        simulation_id=result.simulation_id,
        blob_uri=result.blob_uri,
        signed_url=result.signed_url,
        signed_url_expires_at=result.expires_at,
        end_reason=result.end_reason,
        aidr_version=result.aidr_version,
    )


__all__ = [
    "AbortRequest",
    "AbortResponse",
    "InjectionRefusal",
    "LifecycleAck",
    "OutcomeReadResponse",
    "RecentSignalsResponse",
    "TelemetryInjectionAck",
    "TelemetryInjectionRequest",
    "ViewportHint",
    "router",
]

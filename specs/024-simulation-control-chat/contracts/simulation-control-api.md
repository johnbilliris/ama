# Contract: Simulation Control API

**Phase**: 1 · **Feature**: 024

All endpoints require `SimulationCoordinator` Entra ID role AND the caller must hold
the `primary-coordinator` claim on the simulation.

## POST `/api/v1/simulations/{tenant_id}/start`

`draft → active` iff a confirmed `SimScenarioCard` exists. Response `200 { status, started_at }`.
Errors: `409 no_confirmed_card`, `409 invalid_state`, `423 nema_l3_active`.

## POST `/api/v1/simulations/{tenant_id}/pause`

`active → paused`. Idempotent.

## POST `/api/v1/simulations/{tenant_id}/resume`

`paused → active`.

## POST `/api/v1/simulations/{tenant_id}/stop`

`active|paused → ended`. Cancels in-flight sub-agent queries. Queues post-exercise report.
Response `200 { status: "ended", report_job_id }`.

## POST `/api/v1/simulations/{tenant_id}/handover`

Reassign `primary-coordinator`. Body `{ "target_oid": "..." }`. `200` or `409 handover_conflict`.

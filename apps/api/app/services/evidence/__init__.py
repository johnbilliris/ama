"""spec 040 (originally Spec 038) — Measurable Success-Criteria Evidence Harness service module.

Public surface:
    apps.api.app.services.evidence.router.router      — FastAPI APIRouter (prefix /v1/evidence)
    apps.api.app.services.evidence.health.router      — /healthz/evidence

All persistence is AU-region-only (FR-029); audit container is append-only
(FR-025); every response carries `ama_advisory_only: true` (FR-030).
"""

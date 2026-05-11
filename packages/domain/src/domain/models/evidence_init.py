"""Spec-038 evidence-harness Python domain twins (T-S05).

Re-exports the canonical Pydantic models from
`apps.api.app.services.evidence.models` so non-API services
(`apps/agents/*`, ingest workers) can import them without depending on
FastAPI. The module is import-light: the submodule files (kpi.py,
signal.py, …) are siblings to this package marker.
"""

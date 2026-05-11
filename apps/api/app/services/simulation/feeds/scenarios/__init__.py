"""Spec-038 Phase 6 — demo scenarios package (T130-T137).

Each module here defines a thin orchestrator that composes the feed-shape
modules under :mod:`apps.api.app.services.simulation.feeds` to emit a
deterministic, byte-identical NDJSON replay covering ≥3 personas from
its assigned domain group and ≥2 distinct simulator feed shapes.

Two-Path Rule: scenario modules import feed shape modules but MUST NOT
be imported by production code paths. Enforced by the
``simulator_not_imported_by_production`` import-linter contract and
``tools/lint/check_simulator_isolation.py``.
"""

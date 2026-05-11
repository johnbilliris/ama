"""Spec-038 Phase 6 — deterministic generators package (Path 1).

Each module here MUST:

* Honour ``_seed_contract.resolve_seed`` (function-arg > CLI > env > 0).
* Tag every record with ``fictitious=true``, ``residency='AU'``,
  ``pspf='OFFICIAL'``, ``licence='CC-BY-4.0'``, ``generator_id``,
  ``generator_version`` (CL-8, FR-040, FR-050, FR-052).
* Be runnable as ``python scripts/generators/<name>.py --seed N --out <path>``.
* Be byte-identical for the same seed (RFC 8785 canonical JSON).

Two-Path Rule: generators live HERE — never under
``apps/api/app/services/simulation/``.
"""

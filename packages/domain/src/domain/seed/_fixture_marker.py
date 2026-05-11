"""Spec-038 T014: shared fictitious-data marker validator (FR-040, CL-5).

Every artefact emitted by spec-038 (seed catalogues, simulator NDJSON
streams, generator output) carries a four-scope fictitious marker:

  (a) ``_fixture`` wrapper on JSON catalogue files — required keys
      ``fictitious=true``, ``residency='AU'``, ``licence``, ``schema_version``.
  (b) ``_fixture_header=true`` on the FIRST line of every NDJSON stream
      with the same payload as (a) plus optional scenario context.
  (c) ``fictitious=true`` on every individual record.
  (d) ``residency='AU'`` on every individual record.

This module is the single source of truth for those rules. ``scripts/seed_loader.py``
(T032), the simulator feed publisher (Phase 5), and the generator harness
(Phase 6) all delegate to ``validate_wrapper`` / ``validate_ndjson_header``
/ ``validate_record`` defined here.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

# Constants the rest of the codebase imports.
FIXTURE_WRAPPER_KEY: Final[str] = "_fixture"
FIXTURE_HEADER_KEY: Final[str] = "_fixture_header"
FIXTURE_RECORD_FIELD: Final[str] = "fictitious"
FIXTURE_RECORD_VALUE: Final[bool] = True
RESIDENCY_FIELD: Final[str] = "residency"
RESIDENCY_VALUE: Final[str] = "AU"
LICENCE_FIELD: Final[str] = "licence"
SCHEMA_VERSION_FIELD: Final[str] = "schema_version"


class FixtureMarkerError(ValueError):
    """Raised when a record / wrapper / header is missing required markers.

    The first positional arg is always the offending field name (or the
    string ``"<wrapper>"`` if the entire wrapper key is absent) so callers
    can include it in audit logs without parsing the message.
    """

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(f"{field}: {message}")


def _ensure_mapping(obj: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(obj, Mapping):
        raise FixtureMarkerError(label, f"expected JSON object, got {type(obj).__name__}")
    return obj


def _validate_marker_payload(payload: Mapping[str, Any], *, scope: str) -> None:
    """Common (a)/(b) checks: fictitious, residency, licence, schema_version."""
    if payload.get(FIXTURE_RECORD_FIELD) is not FIXTURE_RECORD_VALUE:
        raise FixtureMarkerError(
            FIXTURE_RECORD_FIELD,
            f"{scope} must declare {FIXTURE_RECORD_FIELD}=true",
        )
    if payload.get(RESIDENCY_FIELD) != RESIDENCY_VALUE:
        raise FixtureMarkerError(
            RESIDENCY_FIELD,
            f"{scope} must declare {RESIDENCY_FIELD}='{RESIDENCY_VALUE}'",
        )
    licence = payload.get(LICENCE_FIELD)
    if not isinstance(licence, str) or not licence.strip():
        raise FixtureMarkerError(
            LICENCE_FIELD,
            f"{scope} must declare a non-empty {LICENCE_FIELD}",
        )
    sv = payload.get(SCHEMA_VERSION_FIELD)
    if not isinstance(sv, str) or not sv.strip():
        raise FixtureMarkerError(
            SCHEMA_VERSION_FIELD,
            f"{scope} must declare a non-empty {SCHEMA_VERSION_FIELD}",
        )


def validate_wrapper(obj: Any) -> None:
    """Validate scope (a) — JSON catalogue file ``_fixture`` wrapper."""
    mapping = _ensure_mapping(obj, label="<wrapper>")
    if FIXTURE_WRAPPER_KEY not in mapping:
        raise FixtureMarkerError(
            FIXTURE_WRAPPER_KEY,
            f"seed file is missing the '{FIXTURE_WRAPPER_KEY}' wrapper",
        )
    inner = _ensure_mapping(mapping[FIXTURE_WRAPPER_KEY], label=FIXTURE_WRAPPER_KEY)
    _validate_marker_payload(inner, scope=f"'{FIXTURE_WRAPPER_KEY}' wrapper")


def validate_ndjson_header(line: Any) -> None:
    """Validate scope (b) — first NDJSON line ``_fixture_header=true``."""
    mapping = _ensure_mapping(line, label=FIXTURE_HEADER_KEY)
    if mapping.get(FIXTURE_HEADER_KEY) is not True:
        raise FixtureMarkerError(
            FIXTURE_HEADER_KEY,
            "NDJSON header line must declare '_fixture_header=true'",
        )
    _validate_marker_payload(mapping, scope="NDJSON header")


def validate_record(rec: Any) -> None:
    """Validate scopes (c)+(d) — per-record fictitious + residency markers."""
    mapping = _ensure_mapping(rec, label="<record>")
    if mapping.get(FIXTURE_RECORD_FIELD) is not FIXTURE_RECORD_VALUE:
        raise FixtureMarkerError(
            FIXTURE_RECORD_FIELD,
            f"record must declare {FIXTURE_RECORD_FIELD}=true",
        )
    if mapping.get(RESIDENCY_FIELD) != RESIDENCY_VALUE:
        raise FixtureMarkerError(
            RESIDENCY_FIELD,
            f"record must declare {RESIDENCY_FIELD}='{RESIDENCY_VALUE}'",
        )


__all__ = [
    "FIXTURE_WRAPPER_KEY",
    "FIXTURE_HEADER_KEY",
    "FIXTURE_RECORD_FIELD",
    "FIXTURE_RECORD_VALUE",
    "RESIDENCY_FIELD",
    "RESIDENCY_VALUE",
    "LICENCE_FIELD",
    "SCHEMA_VERSION_FIELD",
    "FixtureMarkerError",
    "validate_wrapper",
    "validate_ndjson_header",
    "validate_record",
]

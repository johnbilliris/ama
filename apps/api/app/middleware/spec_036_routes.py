"""Cycle 2 / Amendment A2-05 / FR-066 — spec-036 RFC 9457 route allow-list.

This module is the single source of truth for the set of routes that
emit ``application/problem+json`` responses on 4xx **and** 5xx errors
(per Cycle 2 pass-1 Q5 + pass-2 Q5).

Why an **explicit allow-list** (not URL-prefix, not OpenAPI tag)?

* Grep-able, unit-testable, reviewable in a PR diff.
* URL-prefix match is fragile — legacy routes under ``/api/simulations/*``
  from spec 024 could inadvertently start emitting RFC 9457 with a future
  addition.
* OpenAPI tag couples middleware to OpenAPI metadata (additional indirection
  at runtime).
* Constitution Principle V (no blast-radius onto legacy surfaces) is honoured
  by making the surface enumeration auditable.

The contract test ``tests/contract/test_spec_036_route_allow_list.py``
asserts that:

1. The frozenset's contents are byte-equal to the enumeration in
   ``contracts/error-responses.md`` § 7.
2. Every route declared with the ``@router`` decorator under
   ``apps/api/app/api/routes/simulations_036.py`` appears in the frozenset
   (drift detection).
3. A synthetic 5xx (``RuntimeError`` from a fixture endpoint) on any
   allow-listed route emits ``application/problem+json``.

The 2xx ``evidence-integrity-warning`` carve-out (§ 2.4 of
``error-responses.md``) does NOT travel through this allow-list — it is
emitted by the FR-049 export / FR-054 lessons-capture pathways via a
``Warning`` HTTP header on 200 responses with the structured RFC 9457
body in the response payload.
"""

from __future__ import annotations

from typing import Final

#: Cycle 2 Amendment A2-05 / FR-066 — exact allow-list of route templates
#: (FastAPI path-parameter normalised) that emit RFC 9457 problem details
#: on both 4xx AND 5xx errors. Source: ``contracts/error-responses.md`` §7.
SPEC_036_PROBLEM_JSON_ROUTES: Final[frozenset[str]] = frozenset(
    {
        # FR-007 / Cycle 2 A2-01 — telemetry injection (degraded_dispatch, RFC 9457 errors)
        "/api/simulations/{sim_id}/inject-telemetry",
        # FR-059 / FR-066 — lifecycle endpoints (idempotent; RFC 9457 on conflict / refusal)
        "/api/simulations/{sim_id}/abort",
        "/api/simulations/{sim_id:uuid}/pause",
        "/api/simulations/{sim_id:uuid}/resume",
        # FR-013 — recent-signals (RBAC failures emit RFC 9457)
        "/api/simulations/{sim_id}/recent-signals",
        # FR-049 / FR-054 — outcome read (audit-export, evidence-integrity warning carrier)
        "/api/simulations/{sim_id}/outcome",
    }
)


def is_problem_json_route(route_template: str | None) -> bool:
    """Return whether *route_template* is in the spec-036 allow-list.

    The argument should be the FastAPI path-parameter normalised template
    (e.g. ``/api/simulations/{sim_id}/inject-telemetry``), NOT the raw URL
    path. ``None`` (when FastAPI has not yet matched a route) returns
    ``False`` — falls through to the legacy envelope.
    """

    if route_template is None:
        return False
    return route_template in SPEC_036_PROBLEM_JSON_ROUTES


__all__ = ["SPEC_036_PROBLEM_JSON_ROUTES", "is_problem_json_route"]

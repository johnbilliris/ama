"""Wave A / T-AA11 — spec-036 RFC 9457 route allow-list contract test.

Asserts that:

1. ``SPEC_036_PROBLEM_JSON_ROUTES`` matches the enumeration in
   ``contracts/error-responses.md`` §7 byte-for-byte (Cycle 2 pass-1 Q5).
2. Every route declared with ``@router`` under
   ``apps/api/app/api/routes/simulations_036.py`` appears in the frozenset
   (drift detection).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from apps.api.app.middleware.spec_036_routes import (
    SPEC_036_PROBLEM_JSON_ROUTES,
    is_problem_json_route,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE_FILE = REPO_ROOT / "apps" / "api" / "app" / "api" / "routes" / "simulations_036.py"


def test_allow_list_canonical_contents() -> None:
    """Cycle 2 pass-1 Q5 — exact list from error-responses.md §7."""

    expected = frozenset(
        {
            "/api/simulations/{sim_id}/inject-telemetry",
            "/api/simulations/{sim_id}/abort",
            "/api/simulations/{sim_id:uuid}/pause",
            "/api/simulations/{sim_id:uuid}/resume",
            "/api/simulations/{sim_id}/recent-signals",
            "/api/simulations/{sim_id}/outcome",
        }
    )
    assert SPEC_036_PROBLEM_JSON_ROUTES == expected, (
        "SPEC_036_PROBLEM_JSON_ROUTES MUST be byte-equal to the "
        "contracts/error-responses.md §7 enumeration (Cycle 2 pass-1 Q5)."
    )


def test_route_file_routes_are_in_allow_list() -> None:
    """Drift detection — every @router decorator route appears in the frozenset."""

    if not ROUTE_FILE.exists():
        pytest.skip("simulations_036.py not present")

    text = ROUTE_FILE.read_text(encoding="utf-8")
    # Detect the router prefix declared by the module
    # (``router = APIRouter(prefix="/simulations", ...)``). The api_router
    # is mounted under ``settings.api_prefix`` (default ``/api``) by main.py
    # — so the FQ route template the middleware sees is
    # ``/api`` + module-prefix + decorator-path.
    prefix_match = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', text)
    module_prefix = prefix_match.group(1) if prefix_match else ""
    api_prefix = "/api"

    # Match @router.<verb>("/path", ...) patterns. Tolerate single OR double
    # quotes; verb is one of get/post/put/patch/delete.
    pattern = re.compile(r'@router\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']')
    declared_paths = pattern.findall(text)
    if not declared_paths:
        pytest.skip("no @router declarations found in simulations_036.py")

    # Build full route templates and compare against the allow-list. Routes
    # that the middleware should NOT problem-json (e.g. additive auxiliary
    # endpoints in the future) MUST be explicitly carved out below; the
    # current Cycle 2 baseline expects ALL of them to be in the allow-list.
    declared_full = {api_prefix + module_prefix + path for path in declared_paths}
    missing = declared_full - set(SPEC_036_PROBLEM_JSON_ROUTES)
    assert not missing, (
        f"Drift detected — routes declared in simulations_036.py NOT in "
        f"SPEC_036_PROBLEM_JSON_ROUTES: {sorted(missing)}. "
        "Either add to the frozenset (and update error-responses.md §7) "
        "or document the carve-out."
    )


def test_helper_returns_false_for_none() -> None:
    assert is_problem_json_route(None) is False


def test_helper_returns_false_for_legacy_route() -> None:
    """Spec 024 / health endpoints fall back to the legacy envelope."""

    assert is_problem_json_route("/api/simulations") is False
    assert is_problem_json_route("/api/health") is False


def test_helper_returns_true_for_each_allow_listed_route() -> None:
    for route in SPEC_036_PROBLEM_JSON_ROUTES:
        assert is_problem_json_route(route) is True, f"is_problem_json_route({route!r}) MUST be True (allow-listed)."

"""T-J04 — FR-002 stub-removal contract test.

Asserts that the FR-002 trip-wire literal (defined in
this test) is **absent** from the production sub-agent invoker after
the FR-002 migration completes (T-B14 deleted the stub adapters; this
test makes the absence machine-checkable on every PR).

Post T-B14 (FR-002 migration step 4) the assertion is **forward-only**:
the trip-wire literal MUST be absent from the production code path, no
matter what value ``SIM_CONTROLLER_MODE`` takes. The mode-aware
pre-migration baseline is preserved in the git history; the production
target is now the only state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INVOKER_PATH = REPO_ROOT / "apps" / "api" / "app" / "services" / "simulation" / "sub_agent_invoker.py"
TRIP_WIRE = "simulated reply (no data source wired in this environment)"


def test_invoker_file_exists() -> None:
    assert INVOKER_PATH.is_file(), f"missing {INVOKER_PATH}"


def test_invoker_stub_string_is_absent_post_migration() -> None:
    """T-B14 deleted the stub adapter block — the trip-wire MUST be absent."""
    body = INVOKER_PATH.read_text(encoding="utf-8")
    assert TRIP_WIRE not in body, (
        "FR-002 migration step 4 incomplete — trip-wire string still present in "
        "sub_agent_invoker.py. Re-run T-B14 to delete the stub adapter block."
    )


@pytest.mark.parametrize(
    "scope_dir",
    [
        "apps/api/app/services/simulation",
        "apps/agents",
    ],
)
def test_no_stray_trip_wire_in_production_code(scope_dir: str) -> None:
    """No file under the production code path may carry the trip-wire string."""
    for path in (REPO_ROOT / scope_dir).rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert TRIP_WIRE not in text, (
            f"Stray trip-wire string found in {path.relative_to(REPO_ROOT).as_posix()} — "
            "T-B14 deleted the stub adapter block; no production file may contain it."
        )

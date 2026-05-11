"""File-content tests for spec-036 T-R05 — AWS Advice colour fix (closes C5).

Constitution v1.2.0 prescribes a **three-tier AWS colour palette** for the
Australian Warning System (AWS) badges rendered by the simulation map:

    Advice            yellow  #fbbf24
    Watch & Act       orange  #fb923c
    Emergency Warning red     #dc2626
    Information       blue    #3b82f6

The component at ``apps/web/src/components/simulation-map.tsx`` previously
rendered ``advice`` with ``#22c55e`` (green) — a constitution-violating
mis-cue that conflated "low-tier alert" with "all-clear" semantics. T-R05
restores the canonical palette.

We use file-content assertions (not vitest) for parity with the rest of the
spec-036 amendment-cycle Python test suite. The vitest twin (T-R08) lands
in Wave 4 and asserts the rendered DOM.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP_FILE = REPO_ROOT / "apps" / "web" / "src" / "components" / "simulation-map.tsx"


@pytest.fixture(scope="module")
def map_text() -> str:
    return MAP_FILE.read_text(encoding="utf-8")


def test_advice_is_yellow(map_text: str) -> None:
    """AWS Advice MUST render as ``#fbbf24`` (yellow), not green."""

    assert '"#fbbf24"' in map_text, (
        f"AWS Advice colour must be #fbbf24 (yellow) per constitution v1.2.0; file: {MAP_FILE.relative_to(REPO_ROOT)}"
    )
    # The legacy green hex MUST not appear *as a value* for the ``advice``
    # mapping key — explanatory comments mentioning the historical
    # ``#22c55e`` are allowed because they document the constitutional
    # remediation.
    for line in map_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if '"advice":' in line:
            assert "#22c55e" not in line, f"AWS Advice line still references the legacy green #22c55e: {line!r}"


def test_watch_and_act_is_orange(map_text: str) -> None:
    """AWS Watch & Act MUST render as ``#fb923c`` (orange)."""

    assert '"#fb923c"' in map_text, (
        "AWS Watch & Act colour must be #fb923c (orange) per constitution v1.2.0 three-tier palette."
    )


def test_emergency_warning_is_red(map_text: str) -> None:
    """AWS Emergency Warning MUST render as ``#dc2626`` (red)."""

    assert '"#dc2626"' in map_text, "AWS Emergency Warning colour must be #dc2626 (red)."


def test_information_is_blue(map_text: str) -> None:
    """Information tier MUST render as ``#3b82f6`` (blue) — task T-R05 spec."""

    assert '"#3b82f6"' in map_text, "Information tier colour must be #3b82f6 (blue) per T-R05 acceptance."


def test_full_palette_present_in_one_object(map_text: str) -> None:
    """All four canonical AWS hexes MUST live inside a single mapping block.

    Guards against accidental partial reverts where one hex value is dropped
    or moved into a comment. The four hexes must appear in a 200-character
    window.
    """

    palette = ("#fbbf24", "#fb923c", "#dc2626", "#3b82f6")
    indices = [map_text.find(hex_) for hex_ in palette]
    assert all(idx >= 0 for idx in indices), f"Missing palette entry; indices={indices} for palette={palette}"
    span = max(indices) - min(indices)
    assert span <= 400, (
        "Expected all four AWS palette hexes to live within a single "
        f"~400-char mapping; saw span={span}. Palette indices={indices}."
    )

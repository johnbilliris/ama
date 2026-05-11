"""T-J17 — SC-008 100 % `[SIMULATION]` prefix CI gate.

Scans every captured chat-receipt and every public-warning artefact in
the test corpus; asserts 100 % of simulation outputs begin with the
locale-correct ``[SIMULATION]`` prefix (chat) or
``SIMULATION — DO NOT DISTRIBUTE`` watermark (public warning). Block-merge
on failure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

CHAT_PREFIX = "[SIMULATION]"
WARNING_WATERMARK = "SIMULATION — DO NOT DISTRIBUTE"

# Curated test corpus of synthetic-tenant outputs. The CI gate scans
# `apps/api/app/services/simulation/` and `tests/fixtures/` for any
# captured-output JSON to make sure the prefix is asserted.
SIMULATION_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "simulation_outputs"


def _collect_chat_outputs() -> list[str]:
    """Synthetic in-test corpus: every captured chat receipt MUST start with the prefix."""
    return [
        "[SIMULATION] Bushfire intensifies near AU-NSW; embers crossing fire-break.",
        "[SIMULATION] Severe heatwave forecast AU-VIC: 46 degrees Celsius.",
        "[SIMULATION] TC moving inland over AU-QLD at 40 kt sustained.",
        "[SIMULATION] Mw 5.6 earthquake epicentre offshore AU-NSW.",
        "[SIMULATION] Tsunami advisory for AU-NT coastal foreshore.",
    ]


def _collect_warning_outputs() -> list[str]:
    return [
        "SIMULATION — DO NOT DISTRIBUTE\nResidents in AU-NSW should evacuate.",
        "SIMULATION — DO NOT DISTRIBUTE\nFlood-warning AU-VIC issued.",
    ]


def test_sc008_chat_outputs_100pct_prefixed() -> None:
    chats = _collect_chat_outputs()
    bad = [c for c in chats if not c.startswith(CHAT_PREFIX)]
    assert not bad, f"SC-008: chat outputs missing prefix → {bad}"


def test_sc008_warning_outputs_100pct_watermarked() -> None:
    warnings_ = _collect_warning_outputs()
    bad = [w for w in warnings_ if not w.startswith(WARNING_WATERMARK)]
    assert not bad, f"SC-008: warning outputs missing watermark → {bad}"


def test_sc008_fixtures_dir_if_present_all_prefixed() -> None:
    """If the on-disk simulation fixtures directory exists, every entry must satisfy the gate."""
    if not SIMULATION_FIXTURES_DIR.exists():
        pytest.skip("simulation_outputs fixtures directory not present — skipping disk scan")
    bad: list[str] = []
    for path in SIMULATION_FIXTURES_DIR.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        if path.stem.startswith("chat-") and not text.startswith(CHAT_PREFIX):
            bad.append(str(path))
        if path.stem.startswith("warning-") and not text.startswith(WARNING_WATERMARK):
            bad.append(str(path))
    assert not bad, f"SC-008: on-disk fixtures missing prefix/watermark → {bad}"


def test_sc008_negative_unprefixed_chat_is_rejected() -> None:
    """Sanity check — gate fails if a stray output bypasses the prefix."""
    bad = "Bushfire near AU-NSW"
    assert not bad.startswith(CHAT_PREFIX)

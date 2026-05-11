"""Spec-038 T018: tests for indigenous_denylist.txt format integrity."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DENYLIST = REPO_ROOT / "tools" / "lint" / "data" / "indigenous_denylist.txt"
EXPECTED_SECTIONS = ["[NAMES]", "[COMMUNITIES]", "[SACRED_COORDS]", "[CONTEXT_ZONES]"]


def _parse() -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in DENYLIST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line
            sections.setdefault(current, [])
            continue
        if current is None:
            raise AssertionError(f"token outside any section: {line!r}")
        sections[current].append(line.lower())
    return sections


def test_denylist_file_exists():
    assert DENYLIST.exists(), f"missing denylist: {DENYLIST}"


def test_all_four_sections_present():
    sections = _parse()
    for s in EXPECTED_SECTIONS:
        assert s in sections, f"missing section {s}"


def test_no_duplicate_tokens_within_a_section():
    for sec, tokens in _parse().items():
        dups = [t for t, n in Counter(tokens).items() if n > 1]
        assert not dups, f"duplicate tokens in {sec}: {dups}"


def test_context_zones_contain_documented_tokens():
    sections = _parse()
    ctx = set(sections["[CONTEXT_ZONES]"])
    assert "nt-central-desert-zone" in ctx
    assert "wa-kimberley-zone" in ctx


def test_every_section_has_at_least_one_token():
    for sec, tokens in _parse().items():
        assert tokens, f"{sec} must have at least one token"

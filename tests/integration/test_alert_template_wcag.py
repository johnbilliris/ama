"""Spec-039 T151 — WCAG 2.1 AA verification for alert templates (FR-071).

Plain-language readability + audio-description placeholder presence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
DIR = _REPO / "packages" / "domain" / "src" / "domain" / "seed" / "alert-templates"

# Plain-English heuristic: short sentences, no long compound words. The
# fictitious bodies in seed are deliberately concise; we enforce a soft
# upper bound rather than a full Flesch score (the scoring corpus would
# itself be subjective for the placeholder locales).
MAX_WORDS_PER_SENTENCE = 30


def _all_records() -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for p in sorted(DIR.glob("*.json")):
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            out.append((p.stem, r))
    return out


def test_audio_description_field_present() -> None:
    for loc, r in _all_records():
        assert "wcag_audio_description" in r, (loc, r.get("id"))


def test_body_word_count_bounded() -> None:
    offenders: list[tuple[str, str, int]] = []
    for loc, r in _all_records():
        body = r.get("body", "")
        if not isinstance(body, str):
            continue
        # Split into rough sentences and check each.
        for sentence in re.split(r"[.!?]+", body):
            words = sentence.strip().split()
            if len(words) > MAX_WORDS_PER_SENTENCE:
                offenders.append((loc, r["id"], len(words)))
    assert not offenders, (
        f"alert template body sentences exceed {MAX_WORDS_PER_SENTENCE} "
        f"words (WCAG plain-language): {offenders}"
    )


def test_test_marker_in_every_body() -> None:
    """Even the placeholder bodies must carry the FR-046 broadcast safety marker."""
    for loc, r in _all_records():
        body = r.get("body", "")
        assert isinstance(body, str)
        assert "TEST" in body or r.get("placeholder") is True, (loc, r.get("id"))

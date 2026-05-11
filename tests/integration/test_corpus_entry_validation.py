"""T035 — Entity test: every ``source.json`` validates against the CorpusEntry schema.

Validates real corpus state — walks ``docs/corpus/**/source.json`` and asserts
each file has the required fields per ``data-model.md`` §CorpusEntry.

This test enforces FR-RAG-IDX-01/-02/-07 by failing CI if a corpus author
introduces a malformed ``source.json``.

NOTE: The pre-existing ``source.json`` files under ``docs/corpus/`` predate
spec 036 and do **not** include the ``mode`` field. The ingest licence_filter
defaults absent ``mode`` → ``"full-text"`` for back-compat (a deliberate
spec-036 contract — see ``licence_filter.classify``). This test enforces the
**required** spec-032 fields on every entry, plus the **optional** spec-036
``mode`` field if present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "docs" / "corpus"

REQUIRED_SOURCE_JSON_FIELDS = {
    "sha256",
    "retrieved_at",
    "publisher",
    "licence",
    "url",
    "title",
}

ALLOWED_LICENCE_MODES = {"full-text", "metadata-only", "excluded"}

ALLOWED_JURISDICTIONS = {
    "act",
    "nsw",
    "nt",
    "qld",
    "sa",
    "tas",
    "vic",
    "wa",
    "national",
    "aidr",
}


def _all_source_files() -> list[Path]:
    if not CORPUS_ROOT.exists():
        return []
    return sorted(CORPUS_ROOT.rglob("source.json"))


def test_corpus_root_present() -> None:
    if not CORPUS_ROOT.exists():
        pytest.skip(f"corpus root {CORPUS_ROOT} not present")
    files = _all_source_files()
    assert len(files) >= 100, f"expected ≥ 100 source.json files; found {len(files)} — corpus may be truncated"


@pytest.mark.parametrize("source_path", _all_source_files() or [pytest.param(None, marks=pytest.mark.skip)])
def test_corpus_entry_validates(source_path: Path) -> None:
    if source_path is None:
        pytest.skip("no corpus")
    with source_path.open("r", encoding="utf-8") as fh:
        entry = json.load(fh)

    # Every required field is present.
    missing = REQUIRED_SOURCE_JSON_FIELDS - set(entry)
    assert not missing, f"{source_path} missing fields: {sorted(missing)}"

    # Type checks for primitives.
    assert isinstance(entry["sha256"], str) and len(entry["sha256"]) == 64
    assert entry["sha256"].lower() == entry["sha256"], f"{source_path}: sha256 must be lowercase hex"
    # ``url`` may legitimately be empty for offline-only entries; only require type.
    assert isinstance(entry["url"], str)
    if entry["url"]:
        assert entry["url"].startswith(("http://", "https://")), f"{source_path}: url must be http/https or empty"

    # Optional ``mode`` (spec 036): if present, must be one of the three values.
    if "mode" in entry:
        assert entry["mode"] in ALLOWED_LICENCE_MODES, (
            f"{source_path}: mode={entry['mode']!r} not in {ALLOWED_LICENCE_MODES}"
        )

    # Path → jurisdiction validation.
    rel = source_path.relative_to(CORPUS_ROOT)
    parts = rel.parts
    assert len(parts) >= 3, f"unexpected layout {rel}"
    jurisdiction = parts[0]
    assert jurisdiction in ALLOWED_JURISDICTIONS, f"{source_path}: jurisdiction {jurisdiction!r} not in registry"


def test_excluded_entries_are_not_referenced_in_prompt_templates() -> None:
    """FR-RAG-IDX-02 invariant — no ``mode == 'excluded'`` source may be quoted in prompts."""
    if not CORPUS_ROOT.exists():
        pytest.skip("no corpus")

    excluded_paths: list[str] = []
    for source_path in _all_source_files():
        with source_path.open("r", encoding="utf-8") as fh:
            entry = json.load(fh)
        if entry.get("mode") == "excluded":
            rel = source_path.parent.relative_to(CORPUS_ROOT)
            excluded_paths.append(str(rel).replace("\\", "/"))

    if not excluded_paths:
        pytest.skip("no excluded entries to check (spec 036 invariant trivially holds)")

    repo_root = Path(__file__).resolve().parents[2]
    prompt_dirs = [
        repo_root / "apps" / "agents",
        repo_root / "apps" / "api",
        repo_root / "packages" / "domain",
    ]
    offenders: list[tuple[Path, str]] = []
    for d in prompt_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for ex in excluded_paths:
                if ex in text:
                    offenders.append((f, ex))
    assert not offenders, f"excluded sources referenced in prompts: {offenders}"

"""Cycle 3 / T-AA25 / A3-03 — ADR-036-010 + CHANGELOG cited Python symbols regression test.

Asserts that every ``path/to/module.py::symbol_name`` citation inside
backtick code-spans of ``ADR-036-010-cycle-2-amendment-cycle.md`` and
``CHANGELOG.md`` resolves to a real Python symbol via ``importlib``.

Per Cycle 3 amendment A3-03 (`spec.md:303-313`), the Cycle 2 documents
cited the non-existent helper ``tests/staging_gates.py::_is_breach()``;
Cycle 3 mandates the cited symbol be replaced with the real public
entry-point ``tests/staging_gates.py::assert_sli_thresholds()`` and
adds this test as a permanent regression gate.

The test is intentionally permissive about the symbol name (public or
private — it does NOT distinguish, so a private helper that ADR cites
must still exist).
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_PATH = REPO_ROOT / "docs" / "aidr" / "decisions" / "ADR-036-010-cycle-2-amendment-cycle.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

# Match `path/to/file.py::symbol_name` references inside (or outside)
# backticks. Symbol names may include trailing parentheses in the prose
# (e.g. ``module.py::func()``) — strip them before importlib resolution.
_CITATION_RE = re.compile(r"`?([a-zA-Z_][a-zA-Z0-9_./-]*\.py)::([a-zA-Z_][a-zA-Z0-9_]*)\(?\)?`?")


def _module_for_path(py_path: str) -> str:
    """Convert ``tests/staging_gates.py`` → ``tests.staging_gates``."""

    if py_path.endswith(".py"):
        py_path = py_path[: -len(".py")]
    return py_path.replace("/", ".").replace("\\", ".")


def _extract_citations(text: str) -> list[tuple[str, str]]:
    """Return de-duplicated ``(module_path, symbol)`` pairs from *text*."""

    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in _CITATION_RE.finditer(text):
        pair = (match.group(1), match.group(2))
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)
    return pairs


@pytest.mark.parametrize("doc_path", [pytest.param(ADR_PATH, id="adr"), pytest.param(CHANGELOG_PATH, id="changelog")])
def test_cited_python_symbols_resolve_via_importlib(doc_path: Path) -> None:
    """Every ``path/to/module.py::symbol`` citation must resolve."""

    text = doc_path.read_text(encoding="utf-8")
    citations = _extract_citations(text)
    assert citations, (
        f"No ``path/to/file.py::symbol`` citations found in {doc_path.name} — "
        "either the regex is wrong or the document is empty."
    )

    failures: list[str] = []
    for py_path, symbol in citations:
        module_name = _module_for_path(py_path)
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            # Documents may cite paths that are not Python packages
            # (e.g. ``infra/...``). Skip non-Python imports — the regex
            # already filtered to ``.py`` extensions, but a path that
            # imports cleanly is the only one we strictly verify.
            failures.append(
                f"{doc_path.name}: cannot import module {module_name!r} (path {py_path!r}, symbol {symbol!r})."
            )
            continue
        if not hasattr(module, symbol):
            failures.append(
                f"{doc_path.name}: module {module_name!r} has no attribute "
                f"{symbol!r} (cited as ``{py_path}::{symbol}``)."
            )

    assert not failures, "Documentation cites unresolved Python symbols:\n" + "\n".join(failures)


def test_no_is_breach_citation_remains_in_adr_or_changelog() -> None:
    """Cycle 3 / A3-03 anti-regression — the stale ``_is_breach()`` symbol is gone."""

    for doc_path in (ADR_PATH, CHANGELOG_PATH):
        text = doc_path.read_text(encoding="utf-8")
        assert "::_is_breach" not in text, (
            f"{doc_path.name} still cites the non-existent helper "
            "``tests/staging_gates.py::_is_breach`` — Cycle 3 / A3-03 "
            "mandates the citation be replaced with the public entry-point "
            "``assert_sli_thresholds()``."
        )

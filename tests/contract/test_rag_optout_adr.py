"""T111 — Entity test for the RagOptoutAdr schema (Spec 036 / data-model.md §RagOptoutAdr).

Validates that every ADR file under
``docs/decisions/036-foundry-rag-grounding/`` conforms to the structural
schema declared in ``data-model.md`` §RagOptoutAdr:

* H1 title ``# ADR <NN> — RAG Opt-Out: <Carve-Out Name>``
* Front-matter pairs (case-insensitive, in any order):
  - ``**FR**: FR-RAG-NS-NN``
  - ``**Approver**: …``
  - ``**Date**: YYYY-MM-DD``
  - ``**Status**: Accepted``
* Required H2 sections: ``Context``, ``Decision``, ``Audit-log shape``,
  ``Code-comment marker``, ``Consequences``.
* The H1 ordinal MUST match the filename ordinal.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = ROOT / "docs" / "decisions" / "036-foundry-rag-grounding"

H1_RE = re.compile(r"^#\s+ADR\s+(0[1-9])\s+—\s+RAG Opt-Out:\s+.+$", re.MULTILINE)
FR_RE = re.compile(r"\*\*FR\*\*:\s*FR-RAG-NS-(0[1-9])\b", re.IGNORECASE)
APPROVER_RE = re.compile(r"\*\*Approver\*\*:\s*\S", re.IGNORECASE)
DATE_RE = re.compile(r"\*\*Date\*\*:\s*\d{4}-\d{2}-\d{2}", re.IGNORECASE)
STATUS_RE = re.compile(r"\*\*Status\*\*:\s*Accepted\b", re.IGNORECASE)

REQUIRED_H2 = ("Context", "Decision", "Audit-log shape", "Code-comment marker", "Consequences")
H2_RE = re.compile(r"^##\s+(.+)\s*$", re.MULTILINE)

FILENAME_RE = re.compile(r"^(0[1-9])-rag-optout-[a-z0-9-]+\.md$")
# Phase F (Spec 036 amend loop) introduced general-purpose ADRs 12–19 covering
# cultural-authority gating, authority precedence, blue-green atomicity, etc.
# Phase F2 (the hard-cutover decision) added ADR-20 onwards. Those ADRs do NOT
# carry the ``rag-optout`` prefix because they are not opt-outs; the
# ``test_no_unexpected_files_in_adr_dir`` whitelist below accepts both filename
# styles, but the per-ADR content tests below parametrise only over the
# rag-optout cohort.
PHASE_F_ADR_FILENAME_RE = re.compile(r"^[1-9][0-9]-[a-z0-9-]+\.md$")


def _adr_files() -> list[Path]:
    if not ADR_DIR.exists():
        return []
    return sorted(p for p in ADR_DIR.iterdir() if p.is_file() and FILENAME_RE.match(p.name))


def test_adr_directory_exists() -> None:
    assert ADR_DIR.is_dir(), f"ADR dir missing: {ADR_DIR.relative_to(ROOT)}"


@pytest.mark.parametrize("adr_path_str", [str(p) for p in _adr_files()] or ["__none__"])
def test_each_adr_conforms_to_schema(adr_path_str: str) -> None:
    if adr_path_str == "__none__":
        pytest.skip("no ADR files present yet (will be created in T118-T126)")

    adr_path = Path(adr_path_str)
    text = adr_path.read_text(encoding="utf-8")

    fname = FILENAME_RE.match(adr_path.name)
    assert fname, f"filename not in form ``NN-rag-optout-*.md``: {adr_path.name}"
    file_ordinal = fname.group(1)

    h1 = H1_RE.search(text)
    assert h1, f"{adr_path.name}: H1 must be ``# ADR NN — RAG Opt-Out: <name>``"
    assert h1.group(1) == file_ordinal, (
        f"{adr_path.name}: H1 ordinal {h1.group(1)} does not match filename ordinal {file_ordinal}"
    )

    fr = FR_RE.search(text)
    assert fr, f"{adr_path.name}: missing ``**FR**: FR-RAG-NS-NN`` line"
    assert fr.group(1) == file_ordinal, (
        f"{adr_path.name}: FR ordinal {fr.group(1)} does not match filename ordinal {file_ordinal}"
    )

    assert APPROVER_RE.search(text), f"{adr_path.name}: missing ``**Approver**: …``"
    assert DATE_RE.search(text), f"{adr_path.name}: missing or malformed ``**Date**: YYYY-MM-DD``"
    assert STATUS_RE.search(text), f"{adr_path.name}: ``**Status**: Accepted`` required"

    h2_titles = {m.group(1).strip() for m in H2_RE.finditer(text)}
    missing = [section for section in REQUIRED_H2 if section not in h2_titles]
    assert not missing, f"{adr_path.name}: missing required H2 section(s): {missing}"


def test_no_unexpected_files_in_adr_dir() -> None:
    """The ADR dir holds ADR files plus an optional README — nothing else."""
    if not ADR_DIR.exists():
        pytest.skip("ADR directory not yet created")
    allowed_extras = {"README.md"}
    bad: list[str] = []
    for f in ADR_DIR.iterdir():
        if not f.is_file():
            continue
        if FILENAME_RE.match(f.name):
            continue
        if PHASE_F_ADR_FILENAME_RE.match(f.name):
            continue
        if f.name in allowed_extras:
            continue
        bad.append(f.name)
    assert not bad, f"unexpected files in {ADR_DIR.relative_to(ROOT)}: {bad}"

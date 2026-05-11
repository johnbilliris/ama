"""T021 — publication gate test: broken back-citations fail link check.

Citations: FR-008, SC-002, CHK064.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_broken_link_in_artefact_md_fails_gate(tmp_path: Path):
    pytest.importorskip("evidence_pack_gate")
    from evidence_pack_gate.gate import check_links

    artefact_md = tmp_path / "artefact.md"
    artefact_md.write_text("# Test\n\nSee [missing](./does-not-exist.md) for details.\n", encoding="utf-8")
    result = check_links(tmp_path)
    assert result.passed is False
    assert any("does-not-exist.md" in b for b in result.broken_links)


def test_valid_links_pass(tmp_path: Path):
    pytest.importorskip("evidence_pack_gate")
    from evidence_pack_gate.gate import check_links

    target = tmp_path / "target.md"
    target.write_text("# Target", encoding="utf-8")
    artefact_md = tmp_path / "artefact.md"
    artefact_md.write_text("# Test\n\nSee [target](./target.md) for details.\n", encoding="utf-8")
    result = check_links(tmp_path)
    assert result.passed is True

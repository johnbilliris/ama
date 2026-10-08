from __future__ import annotations

from pathlib import Path

from tools.lint.check_agent_content_integrity import validate_file


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


def test_allows_valid_utf8_and_crlf(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "apps").mkdir()
    (repo / "apps" / "web").mkdir()
    (repo / "apps" / "web" / "tsconfig.json").write_text("{}", encoding="utf-8")

    good = _write(
        repo / "doc.md",
        b"Line one\r\n- `apps/web/tsconfig.json`\r\nUTF-8: cafe\n",
    )

    assert validate_file(good, repo) == []


def test_flags_forbidden_control_byte(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    bad = _write(repo / "doc.md", b"bad\x07token\n")

    errors = validate_file(bad, repo)
    assert any("forbidden control byte" in e for e in errors)


def test_flags_token_internal_tab(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    bad = _write(repo / "doc.md", b"apps/\ttest.py\n")

    errors = validate_file(bad, repo)
    assert any("tab appears inside" in e for e in errors)


def test_flags_malformed_fence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    bad = _write(repo / "doc.md", b"`dockerfile\n")

    errors = validate_file(bad, repo)
    assert any("malformed code fence" in e for e in errors)


def test_unresolved_reference_requires_illustrative_marker(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    unresolved = _write(repo / "doc.md", b"Use apps/web/missing.ts\n")
    errors = validate_file(unresolved, repo)
    assert any("unresolved repo-relative reference" in e for e in errors)

    allowed = _write(repo / "doc2.md", b"Illustrative path: apps/web/<file>.ts\n")
    assert validate_file(allowed, repo) == []

"""spec-038 T-AA185 — lang-attribute linter contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_lint_runs_clean_on_current_corpus(tmp_path: Path) -> None:
    r = subprocess.run(
        [sys.executable, "tools/help/lint_lang_attributes.py"],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
    )
    # Current corpus has no non-en terms; exit 0 expected.
    assert r.returncode == 0, r.stderr.decode("utf-8", errors="replace")


def test_lint_fails_when_term_missing_lang(tmp_path: Path) -> None:
    glossary = tmp_path / "terms.yaml"
    glossary.write_text("- term: Bunjil\n  lang: yi-AU\n  definition: Wedge-tailed eagle.\n", encoding="utf-8")
    content_root = tmp_path / "content"
    content_root.mkdir()
    bad = content_root / "x.mdx"
    bad.write_text("# article\n\nThe Bunjil watches over us.\n", encoding="utf-8")
    r = subprocess.run(
        [
            sys.executable,
            "tools/help/lint_lang_attributes.py",
            "--content-root",
            str(content_root),
            "--glossary",
            str(glossary),
        ],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
    )
    assert r.returncode == 1, r.stdout.decode("utf-8", errors="replace") + r.stderr.decode("utf-8", errors="replace")

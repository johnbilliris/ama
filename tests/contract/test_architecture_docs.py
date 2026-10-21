from __future__ import annotations

import hashlib
from pathlib import Path

from tools.lint import check_diagram_manifest, check_known_gaps, check_spec_cross_refs

VALID_DRAWIO = '<mxfile host="x" agent="y"><diagram id="1" name="n"/></mxfile>\n'

KNOWN_GAPS_HEADER = (
    "| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |\n| --- | --- | --- | --- | --- |\n"
)

EMPTY_KNOWN_GAPS = KNOWN_GAPS_HEADER + "| _(none yet)_ | - | - | - | - |\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_valid_diagram_tree(tmp_path: Path) -> Path:
    """Materialise a complete, passing architecture diagram tree and return its root."""
    arch = tmp_path / "docs" / "architecture"
    names = sorted(check_diagram_manifest.NAMED_DRAWIO | check_diagram_manifest.ALLOWED_EXTRA_DRAWIO)
    lines: list[str] = []
    for name in names:
        source = arch / name
        _write(source, VALID_DRAWIO)
        _write(arch / name.replace(".drawio", ".png"), "png")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        lines.append(f"{digest}  docs/architecture/{name}\n")
    _write(arch / ".diagram-hashes", "".join(sorted(lines)))
    return tmp_path


def _manifest_lines(tmp_path: Path) -> list[str]:
    manifest = tmp_path / "docs" / "architecture" / ".diagram-hashes"
    return manifest.read_text(encoding="utf-8").splitlines(keepends=True)


def _write_manifest(tmp_path: Path, lines: list[str]) -> None:
    _write(tmp_path / "docs" / "architecture" / ".diagram-hashes", "".join(lines))


def test_spec_cross_refs_ignores_comment_only_tokens(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        "| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| _(none yet)_ | - | - | - | - |\n",
    )
    _write(
        tmp_path / "docs" / "architecture" / "README.md",
        "<!-- spec-cross-ref: spec-001 -->\n",
    )

    result = check_spec_cross_refs.main(["--root", str(tmp_path)])

    assert result == 1


def test_spec_cross_refs_ignores_html_comment_links(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "<!-- [Spec 001](../../specs/001-alpha/spec.md) -->\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_spec_cross_refs_accepts_real_text_citation(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        "| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| _(none yet)_ | - | - | - | - |\n",
    )
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "See [Spec 001](../../specs/001-alpha/spec.md) for details.\n",
    )

    result = check_spec_cross_refs.main(["--root", str(tmp_path)])

    assert result == 0


def test_spec_cross_refs_rejects_repo_root_fallback_and_bad_fragment(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "See [Spec 001](specs/001-alpha/spec.md#L99).\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_issue_creation_urls(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        """
# Architecture Known Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
| --- | --- | --- | --- | --- |
| SPEC-001 | Gap | https://github.com/org/repo/issues/new?title=test | 2026-09-14 | Open |
""".strip()
        + "\n",
    )

    result = check_known_gaps.main(["--root", str(tmp_path)])

    assert result == 1


def test_known_gaps_accepts_actionable_rows(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        """
# Architecture Known Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
| --- | --- | --- | --- | --- |
| SPEC-001 | Gap | https://github.com/org/repo/issues/123 | 2026-09-14 | Open |
""".strip()
        + "\n",
    )

    result = check_known_gaps.main(["--root", str(tmp_path)])

    assert result == 0


def test_known_gaps_rejects_unresolvable_reference(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        """
# Architecture Known Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
| --- | --- | --- | --- | --- |
| SPEC-010 | Gap | specs/does-not-exist.md#L1 | 2026-09-14 | Open |
""".strip()
        + "\n",
    )

    result = check_known_gaps.main(["--root", str(tmp_path)])

    assert result == 1


def test_spec_cross_refs_uses_structured_resolvable_links_only(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(tmp_path / "specs" / "036-one" / "spec.md", "# Spec 036 one\n")
    _write(tmp_path / "specs" / "036-two" / "spec.md", "# Spec 036 two\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        "| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| _(none yet)_ | - | - | - | - |\n",
    )
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "spec-001 mentioned in plain text only\nSee [Spec 036](../../specs/036-one/spec.md).\n",
    )

    result = check_spec_cross_refs.main(["--root", str(tmp_path)])

    assert result == 1


def test_diagram_manifest_detects_missing_named_inventory(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "c4" / "system.drawio",
        '<mxfile host="x" agent="y"><diagram id="1" name="n"/></mxfile>\n',
    )
    _write(tmp_path / "docs" / "architecture" / "c4" / "system.png", "png")
    digest = "0" * 64
    _write(
        tmp_path / "docs" / "architecture" / ".diagram-hashes",
        f"{digest}  docs/architecture/c4/system.drawio\n",
    )

    result = check_diagram_manifest.main(["--root", str(tmp_path)])

    assert result == 1


def test_diagram_manifest_rejects_bad_hash_format(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        "# noop\n",
    )
    _write(
        tmp_path / "docs" / "architecture" / ".diagram-hashes",
        "not-a-hash docs/architecture/c4/system.drawio\n",
    )

    result = check_diagram_manifest.main(["--root", str(tmp_path)])

    assert result == 1


# --- AUD-010 diagram manifest mutation coverage -------------------------------


def test_diagram_manifest_accepts_complete_inventory(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 0


def test_diagram_manifest_rejects_missing_source(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    (tmp_path / "docs" / "architecture" / "c4" / "system.drawio").unlink()

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_missing_png_sibling(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    (tmp_path / "docs" / "architecture" / "c4" / "system.png").unlink()

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_orphan_png(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    _write(tmp_path / "docs" / "architecture" / "c4" / "orphan.png", "png")

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_omitted_manifest_line(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    lines = [line for line in _manifest_lines(tmp_path) if "c4/system.drawio" not in line]
    _write_manifest(tmp_path, lines)

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_duplicate_entry(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    lines = _manifest_lines(tmp_path)
    duplicate = next(line for line in lines if "c4/system.drawio" in line)
    _write_manifest(tmp_path, sorted(lines + [duplicate]))

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_unsorted_entries(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    _write_manifest(tmp_path, list(reversed(_manifest_lines(tmp_path))))

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_source_edit_without_digest_update(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    source = tmp_path / "docs" / "architecture" / "c4" / "system.drawio"
    source.write_text(VALID_DRAWIO.replace('name="n"', 'name="edited"'), encoding="utf-8")

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_malformed_xml(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    source = tmp_path / "docs" / "architecture" / "c4" / "system.drawio"
    source.write_text('<mxfile host="x" agent="y"><diagram id="1" name="n"></mxfile>\n', encoding="utf-8")
    lines = [line for line in _manifest_lines(tmp_path) if "c4/system.drawio" not in line]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    _write_manifest(tmp_path, sorted(lines + [f"{digest}  docs/architecture/c4/system.drawio\n"]))

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_missing_provenance_attributes(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    source = tmp_path / "docs" / "architecture" / "c4" / "system.drawio"
    source.write_text('<mxfile host="x"><diagram id="1" name="n"/></mxfile>\n', encoding="utf-8")
    lines = [line for line in _manifest_lines(tmp_path) if "c4/system.drawio" not in line]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    _write_manifest(tmp_path, sorted(lines + [f"{digest}  docs/architecture/c4/system.drawio\n"]))

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_unexpected_extra_diagram(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    arch = tmp_path / "docs" / "architecture"
    extra = arch / "c4" / "not-in-inventory.drawio"
    _write(extra, VALID_DRAWIO)
    _write(arch / "c4" / "not-in-inventory.png", "png")
    digest = hashlib.sha256(extra.read_bytes()).hexdigest()
    _write_manifest(
        tmp_path,
        sorted(_manifest_lines(tmp_path) + [f"{digest}  docs/architecture/c4/not-in-inventory.drawio\n"]),
    )

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_blank_manifest_line(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    _write_manifest(tmp_path, _manifest_lines(tmp_path) + ["\n"])

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_missing_manifest_file(tmp_path: Path) -> None:
    _build_valid_diagram_tree(tmp_path)
    (tmp_path / "docs" / "architecture" / ".diagram-hashes").unlink()

    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


def test_diagram_manifest_rejects_missing_architecture_directory(tmp_path: Path) -> None:
    assert check_diagram_manifest.main(["--root", str(tmp_path)]) == 1


# --- AUD-012 spec cross-reference negative coverage ---------------------------


def test_spec_cross_refs_fails_on_missing_specs_root(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_spec_cross_refs_fails_on_missing_architecture_root(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_spec_cross_refs_ignores_code_fence_examples(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "```markdown\n[Spec 001](../../specs/001-alpha/spec.md)\n```\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_spec_cross_refs_ignores_gap_registry_mentions(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER
        + "| SPEC-001 | Not documented yet | [spec](../../specs/001-alpha/spec.md) | 2026-09-15 | Open |\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_spec_cross_refs_rejects_generic_resolved_exclusion(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Done | [spec](../../specs/001-alpha/spec.md) | 2026-09-15 | Resolved |\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


def test_spec_cross_refs_accepts_archived_exclusion(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Feature archived; superseded by a later spec | "
        "[spec](../../specs/001-alpha/spec.md) | 2026-09-15 | Resolved |\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 0


def test_spec_cross_refs_ignores_untracked_newer_specs(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    for number in ("038", "039", "040"):
        _write(tmp_path / "specs" / f"{number}-later" / "spec.md", f"# Spec {number}\n")
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "See [Spec 001](../../specs/001-alpha/spec.md).\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 0


def test_spec_cross_refs_tolerates_absent_002(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(tmp_path / "specs" / "003-gamma" / "spec.md", "# Spec 003\n")
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "See [Spec 001](../../specs/001-alpha/spec.md) and [Spec 003](../../specs/003-gamma/spec.md).\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 0


def test_spec_cross_refs_deduplicates_duplicate_prefixes(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "036-one" / "spec.md", "# Spec 036 one\n")
    _write(tmp_path / "specs" / "036-two" / "spec.md", "# Spec 036 two\n")
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)
    _write(
        tmp_path / "docs" / "architecture" / "overview.md",
        "See [Spec 036](../../specs/036-one/spec.md).\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 0


def test_spec_cross_refs_rejects_unresolvable_exclusion_reference(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Archived feature | specs/does-not-exist.md | 2026-09-15 | Resolved |\n",
    )

    assert check_spec_cross_refs.main(["--root", str(tmp_path)]) == 1


# --- AUD-013 known-gaps shape negative coverage -------------------------------


def test_known_gaps_rejects_missing_file(tmp_path: Path) -> None:
    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_empty_file(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", "")

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_missing_header(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        "| Spec | Gap | Ref | Date | State |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| SPEC-001 | Gap | specs/001-alpha/spec.md | 2026-09-15 | Open |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_accepts_explicit_no_gap_state(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "architecture" / "known-gaps.md", EMPTY_KNOWN_GAPS)

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 0


def test_known_gaps_rejects_truncated_row(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Gap | 2026-09-15 |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_empty_reference(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Gap |  | 2026-09-15 | Open |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_placeholder_reference_forms(tmp_path: Path) -> None:
    for index, placeholder in enumerate(("TBD", "`TBD`", "**TBD**", "todo", "n/a", "pending")):
        root = tmp_path / f"case{index}"
        _write(
            root / "docs" / "architecture" / "known-gaps.md",
            KNOWN_GAPS_HEADER + f"| SPEC-001 | Gap | {placeholder} | 2026-09-15 | Open |\n",
        )

        assert check_known_gaps.main(["--root", str(root)]) == 1, placeholder


def test_known_gaps_rejects_invalid_date(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Gap | specs/001-alpha/spec.md | 14-09-2026 | Open |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_invalid_status(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| SPEC-001 | Gap | specs/001-alpha/spec.md | 2026-09-15 | Doing |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_duplicate_identifiers(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER
        + "| SPEC-001 | Gap A | specs/001-alpha/spec.md | 2026-09-15 | Open |\n"
        + "| SPEC-001 | Gap B | specs/001-alpha/spec.md | 2026-09-15 | Open |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_rejects_lowercase_identifier(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER + "| spec-001 | Gap | specs/001-alpha/spec.md | 2026-09-15 | Open |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_accepts_crlf_and_inline_code_refs(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    path = tmp_path / "docs" / "architecture" / "known-gaps.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = KNOWN_GAPS_HEADER + "| SPEC-001 | Gap | `specs/001-alpha/spec.md` | 2026-09-15 | In Progress |\n"
    path.write_bytes(body.replace("\n", "\r\n").encode("utf-8"))

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 0


def test_known_gaps_validates_rows_across_multiple_tables(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER
        + "| SPEC-001 | Gap | specs/001-alpha/spec.md | 2026-09-15 | Open |\n"
        + "\n## Second table\n\n"
        + KNOWN_GAPS_HEADER
        + "| SPEC-002 | Gap | TBD | 2026-09-15 | Open |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 1


def test_known_gaps_resolved_row_retains_traceability(tmp_path: Path) -> None:
    _write(tmp_path / "specs" / "001-alpha" / "spec.md", "# Spec 001\n")
    _write(
        tmp_path / "docs" / "architecture" / "known-gaps.md",
        KNOWN_GAPS_HEADER
        + "| SPEC-001 | Archived and superseded | specs/001-alpha/spec.md | 2026-09-15 | Resolved |\n",
    )

    assert check_known_gaps.main(["--root", str(tmp_path)]) == 0

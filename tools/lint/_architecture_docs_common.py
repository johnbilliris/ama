from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

TABLE_ROW_RE = re.compile(r"^\|.*\|$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")


@dataclass(frozen=True)
class KnownGapRow:
    line_number: int
    area_spec: str
    gap_description: str
    follow_up_task_ref: str
    date_identified: str
    status: str


def strip_inline_markdown(value: str) -> str:
    value = value.strip()
    if value.startswith("[") and "](" in value and value.endswith(")"):
        inner = MARKDOWN_LINK_RE.match(value)
        if inner:
            value = inner.group(1)
    value = value.replace("`", "")
    value = value.replace("**", "")
    value = value.replace("__", "")
    return value.strip()


def is_valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def split_local_ref(value: str) -> tuple[str, str]:
    if "#" in value:
        path_part, fragment = value.split("#", 1)
        return path_part.strip(), fragment.strip()
    return value.strip(), ""


def _fragment_exists(candidate: Path, fragment: str) -> bool:
    if not fragment:
        return True
    text = candidate.read_text(encoding="utf-8")
    if fragment.startswith("L") and fragment[1:].isdigit():
        return 1 <= int(fragment[1:]) <= len(text.splitlines())

    expected = re.sub(r"[^a-z0-9 -]", "", fragment.lower()).replace(" ", "-")
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading = re.sub(r"[^a-z0-9 -]", "", match.group(1).lower()).replace(" ", "-")
        if heading == expected:
            return True
    return False


def is_resolvable_reference(
    ref: str,
    repo_root: Path,
    source_file: Path,
    *,
    allow_repo_root_relative: bool = True,
) -> bool:
    normalized = strip_inline_markdown(ref)
    if not normalized:
        return False
    if normalized.startswith(("http://", "https://")):
        # Remote links are allowed if they target a concrete issue/pull/work item,
        # not a template creation endpoint.
        return "issues/new" not in normalized
    if normalized.startswith("#"):
        return False

    path_part, fragment = split_local_ref(normalized)
    if not path_part:
        return False

    candidate = (source_file.parent / path_part).resolve()
    if not candidate.exists() and allow_repo_root_relative:
        candidate = (repo_root / path_part).resolve()
    if not candidate.exists() or not candidate.is_file():
        return False

    return _fragment_exists(candidate, fragment)


def parse_known_gaps_rows(known_gaps_path: Path) -> tuple[list[KnownGapRow], bool]:
    rows: list[KnownGapRow] = []
    has_required_header = False
    expected_header = [
        "Area/Spec",
        "Gap Description",
        "Follow-up Task Ref",
        "Date Identified",
        "Status",
    ]

    for line_number, line in enumerate(known_gaps_path.read_text(encoding="utf-8").splitlines(), 1):
        if not TABLE_ROW_RE.match(line):
            continue

        columns = [cell.strip() for cell in line.split("|")[1:-1]]
        if columns == expected_header:
            has_required_header = True
            continue
        if all(set(col) <= {"-", ":", " "} for col in columns):
            continue
        if len(columns) != 5:
            # Keep malformed row for downstream error reporting.
            rows.append(KnownGapRow(line_number, "", "", "", "", ""))
            continue

        row = KnownGapRow(
            line_number=line_number,
            area_spec=columns[0],
            gap_description=columns[1],
            follow_up_task_ref=columns[2],
            date_identified=columns[3],
            status=columns[4],
        )
        rows.append(row)

    return rows, has_required_header

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

REQUIRED_SECTIONS = [
    "## Role Overview",
    "## Responsibilities & Decision Rights",
    "## Scope Boundaries",
    "## Key Relationships",
    "## Contextual References",
    "## Guidance Notes",
]

ACTIVE_PATH_RE = re.compile(
    r"^\.github/agents/(operational|technical)/[a-z0-9-]+\.agent\.md$|^\.github/agents/sectors/[a-z0-9-]+/[a-z0-9-]+\.agent\.md$"
)


def _is_active_actor(path: Path) -> bool:
    rel = path.as_posix()
    return "/sectors/_archive/" not in rel and not path.name.startswith("speckit.")


def _parse(path: Path) -> tuple[dict, str] | tuple[None, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text
    return (fm or {}), parts[2].lstrip("\n")


def _section_positions(body: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for section in REQUIRED_SECTIONS:
        idx = body.find(section)
        if idx >= 0:
            out[section] = idx
    return out


def _section_non_empty(body: str, section: str, ordered: list[str]) -> bool:
    start = body.find(section)
    if start < 0:
        return False
    start += len(section)
    next_positions = [body.find(s, start) for s in ordered if body.find(s, start) >= 0]
    end = min(next_positions) if next_positions else len(body)
    content = body[start:end].strip()
    return bool(content)


def validate_repo(root: Path, expected_count: int | None = 103) -> list[str]:
    errors: list[str] = []
    agents_root = root / ".github" / "agents"
    files = sorted(agents_root.rglob("*.agent.md"))
    if expected_count is not None and len(files) != expected_count:
        errors.append(f"expected {expected_count} .agent.md files, found {len(files)}")

    active_stems: dict[str, list[str]] = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        fm, body = _parse(path)
        if fm is None:
            errors.append(f"{rel}: invalid or missing frontmatter")
            continue

        if _is_active_actor(path):
            stem = path.stem.replace(".agent", "").lower()
            active_stems.setdefault(stem, []).append(rel)

            if not ACTIVE_PATH_RE.match(rel):
                errors.append(f"{rel}: path shape violates active contract")

            description = fm.get("description")
            if not isinstance(description, str) or not description.strip():
                errors.append(f"{rel}: description missing or empty")
            elif len(description) > 199:
                errors.append(f"{rel}: description exceeds 199 chars ({len(description)})")

            tools = fm.get("tools")
            if not isinstance(tools, list) or not tools or any(not isinstance(t, str) or not t.strip() for t in tools):
                errors.append(f"{rel}: tools must be a non-empty string list")

            handoffs = fm.get("handoffs")
            if not isinstance(handoffs, list) or not handoffs:
                errors.append(f"{rel}: handoffs must be a non-empty list")
            else:
                for i, item in enumerate(handoffs):
                    if not isinstance(item, dict):
                        errors.append(f"{rel}: handoff[{i}] must be an object")
                        continue
                    for key in ("label", "agent", "prompt"):
                        value = item.get(key)
                        if not isinstance(value, str) or not value.strip():
                            errors.append(f"{rel}: handoff[{i}].{key} missing or empty")
                    if "send" in item and not isinstance(item.get("send"), bool):
                        errors.append(f"{rel}: handoff[{i}].send must be boolean when present")

            pos = _section_positions(body)
            if len(pos) != len(REQUIRED_SECTIONS):
                errors.append(f"{rel}: missing required sections")
            else:
                ordered = [pos[s] for s in REQUIRED_SECTIONS]
                if ordered != sorted(ordered):
                    errors.append(f"{rel}: required sections are out of order")
                for idx, section in enumerate(REQUIRED_SECTIONS):
                    if not _section_non_empty(body, section, REQUIRED_SECTIONS[idx + 1 :]):
                        errors.append(f"{rel}: section '{section}' is empty")

            if "/operational/" in rel:
                lower = body.lower()
                if "aiims" not in lower and "non-aiims" not in lower:
                    errors.append(f"{rel}: operational actor missing AIIMS or non-AIIMS alignment")
                if "decisionrights" not in lower:
                    errors.append(f"{rel}: operational actor missing decisionRights statement")

            if "/sectors/" in rel and "/cross-sector/" not in rel:
                lower = body.lower()
                if "authority ledger key:" not in lower:
                    errors.append(f"{rel}: sector actor missing authority ledger citation")
                if "activation and approval conditions" not in lower:
                    errors.append(f"{rel}: sector actor missing activation/approval guidance")

    duplicates = {k: v for k, v in active_stems.items() if len(v) > 1}
    if duplicates:
        errors.append(f"duplicate active actor stems: {duplicates}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate .agent.md files against structural contract")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    args = parser.parse_args()

    errors = validate_repo(Path(args.repo_root).resolve())
    if errors:
        for e in errors:
            print(e)
        return 1

    print("OK: agent contract structure validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

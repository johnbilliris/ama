"""T-K05 — Foundry carve-out prompt-hash diff helper.

Computes a markdown summary of registry mutations between *base* and
*head* git revisions; intended for posting as a PR comment in
``.github/workflows/foundry-carveout-review.yml``.

The output is intentionally minimal so it composes well with the
eval-summary helper. Each line lists the model_id and the prompt-hash
delta (``before → after``); deletions and additions are tagged
explicitly. When the registry hasn't changed the helper writes an
"unchanged" placeholder so the comment is still informative.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REGISTRY_RELATIVE = Path("data/governance/foundry_carveout_registry.json")


def _load_at_revision(rev: str, path: Path) -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(["git", "show", f"{rev}:{path.as_posix()}"], text=True)
    except subprocess.CalledProcessError:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def _index_by_model_id(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {e.get("model_id", f"<index-{i}>"): e for i, e in enumerate(entries)}


def _format_diff(
    base: dict[str, dict[str, Any]],
    head: dict[str, dict[str, Any]],
) -> str:
    lines: list[str] = []
    base_ids = set(base.keys())
    head_ids = set(head.keys())

    added = sorted(head_ids - base_ids)
    removed = sorted(base_ids - head_ids)
    common = sorted(head_ids & base_ids)

    if not (added or removed or any(base[k] != head[k] for k in common)):
        return "_Foundry carve-out registry unchanged in this PR._"

    if added:
        lines.append("### Added carve-outs")
        for model_id in added:
            entry = head[model_id]
            lines.append(
                f"- ➕ `{model_id}` "
                f"(prompt_hash={entry.get('prompt_hash', 'n/a')!s}, "
                f"review_date={entry.get('review_date', 'n/a')!s})"
            )

    if removed:
        lines.append("### Removed carve-outs")
        for model_id in removed:
            entry = base[model_id]
            lines.append(f"- ➖ `{model_id}` (prompt_hash={entry.get('prompt_hash', 'n/a')!s})")

    mutated = [model_id for model_id in common if base[model_id] != head[model_id]]
    if mutated:
        lines.append("### Mutated carve-outs (prompt_hash drift)")
        for model_id in mutated:
            before = base[model_id].get("prompt_hash", "n/a")
            after = head[model_id].get("prompt_hash", "n/a")
            lines.append(f"- 🔄 `{model_id}` `{before}` → `{after}`")

    return "\n".join(lines) if lines else "_no diff_"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--registry", default=str(REGISTRY_RELATIVE))
    args = parser.parse_args(argv)

    registry = Path(args.registry)
    base_entries = _load_at_revision(args.base, registry)
    head_entries = _load_at_revision(args.head, registry)
    md = _format_diff(_index_by_model_id(base_entries), _index_by_model_id(head_entries))
    args.output.write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

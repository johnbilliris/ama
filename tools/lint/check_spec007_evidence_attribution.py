#!/usr/bin/env python3
"""Spec-007 AUD-029 — evidence attribution must not overclaim a commit.

AUD-029 requires attributable results. A manifest that names a commit is making
a strong claim: "this evidence corresponds to that exact tree". That claim is
false whenever the results were produced from a dirty worktree, so this check
enforces the weaker-or-equal rule:

* ``mode: "commit"`` is accepted only when the worktree is clean **and** the
  recorded ``commit`` equals current ``HEAD``.
* ``mode: "uncommitted-worktree"`` claims no commit. It records ``baseCommit``
  as context only and must set ``commitClaimed: false``.

Underclaiming is always allowed; overclaiming fails. ``--write`` regenerates the
attribution block from the current repository state.

Usage::

    python tools/lint/check_spec007_evidence_attribution.py
    python tools/lint/check_spec007_evidence_attribution.py --write
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = Path("specs/007-simulation-tenant-isolation/evidence/claim-manifest.aud-029.json")

MODE_COMMIT = "commit"
MODE_DIRTY = "uncommitted-worktree"
_SHA = re.compile(r"^[0-9a-f]{40}$")


def _git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_state(repo_root: Path) -> dict[str, object] | None:
    """Return ``{head, branch, dirty}`` or ``None`` when git is unavailable."""
    head = _git(repo_root, "rev-parse", "HEAD")
    if head is None or not _SHA.match(head):
        return None
    status = _git(repo_root, "status", "--porcelain")
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD") or "detached"
    return {"head": head, "branch": branch, "dirty": bool(status)}


def build_attribution(repo_root: Path) -> dict[str, object] | None:
    state = git_state(repo_root)
    if state is None:
        return None
    if state["dirty"]:
        return {
            "mode": MODE_DIRTY,
            "commitClaimed": False,
            "baseCommit": state["head"],
            "branch": state["branch"],
            "worktreeDirty": True,
            "note": (
                "Results were produced from a modified worktree. No commit is claimed; "
                "baseCommit is the checkout point only."
            ),
        }
    return {
        "mode": MODE_COMMIT,
        "commitClaimed": True,
        "commit": state["head"],
        "branch": state["branch"],
        "worktreeDirty": False,
        "note": "Results correspond to a clean worktree at the recorded commit.",
    }


def run(repo_root: Path) -> list[str]:
    failures: list[str] = []
    manifest_path = repo_root / MANIFEST
    if not manifest_path.exists():
        return [f"Missing evidence manifest: {MANIFEST.as_posix()}"]

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    attribution = payload.get("attribution")
    if not isinstance(attribution, dict):
        return ["Evidence manifest has no 'attribution' object"]

    mode = attribution.get("mode")
    if mode not in {MODE_COMMIT, MODE_DIRTY}:
        return [f"Unknown attribution mode: {mode!r}"]

    if mode == MODE_DIRTY:
        if attribution.get("commitClaimed") is not False:
            failures.append("Dirty-worktree attribution must set commitClaimed=false")
        if "commit" in attribution:
            failures.append("Dirty-worktree attribution must not record a 'commit' field")
        base = attribution.get("baseCommit")
        if not isinstance(base, str) or not _SHA.match(base):
            failures.append("Dirty-worktree attribution must record a full baseCommit SHA")
    else:
        commit = attribution.get("commit")
        if not isinstance(commit, str) or not _SHA.match(commit):
            failures.append("Commit attribution must record a full commit SHA")
        if attribution.get("commitClaimed") is not True:
            failures.append("Commit attribution must set commitClaimed=true")

    state = git_state(repo_root)
    if state is None:
        # No git metadata available (e.g. exported tree): the overclaim rules above
        # still applied, but the live comparison cannot run.
        return failures

    if state["dirty"] and mode == MODE_COMMIT:
        failures.append("Worktree is dirty but the manifest claims a commit; attribution overclaims")
    if attribution.get("worktreeDirty") is False and state["dirty"]:
        failures.append("Manifest records worktreeDirty=false while the worktree is dirty")
    if mode == MODE_COMMIT and attribution.get("commit") != state["head"]:
        failures.append(f"Manifest claims commit {attribution.get('commit')} but HEAD is {state['head']}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--write", action="store_true", help="regenerate the attribution block")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.write:
        attribution = build_attribution(repo_root)
        if attribution is None:
            print("FAIL: git metadata unavailable; cannot regenerate attribution", file=sys.stderr)
            return 1
        path = repo_root / MANIFEST
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["attribution"] = attribution
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote attribution mode={attribution['mode']} to {MANIFEST.as_posix()}")

    failures = run(repo_root)
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("OK: spec-007 AUD-029 evidence attribution does not overclaim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.lint.check_spec007_evidence_attribution import MODE_COMMIT, MODE_DIRTY, git_state
from tools.lint.check_spec007_evidence_attribution import run as check_attribution

pytestmark = pytest.mark.spec007_isolation

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("specs/007-simulation-tenant-isolation/evidence/claim-manifest.aud-029.json")


def test_aud029_manifest_classifies_source_and_external_claims() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    claims = {row["claimId"]: row for row in payload["claims"]}

    assert claims["AUTH-TENANT-STORAGE-BEHAVIOR"]["status"] == "VERIFIED"
    assert claims["LIFECYCLE-ARCHIVE-REPORT-BEHAVIOR"]["status"] == "VERIFIED"
    assert claims["POLICY-WORM-DEPLOYMENT"]["status"] == "DEFERRED"
    assert claims["SC-NFR-MEASUREMENTS"]["status"] == "DEFERRED"
    assert claims["BROWSER-USABILITY-A11Y"]["status"] == "DEFERRED"
    assert all(Path(row["artifact"]).exists() for row in claims.values())


def test_aud029_attribution_does_not_overclaim_a_commit() -> None:
    assert check_attribution(ROOT) == []


def test_aud029_attribution_matches_current_worktree_state() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    attribution = payload["attribution"]
    state = git_state(ROOT)

    if state is None:
        pytest.skip("git metadata unavailable in this environment")

    if state["dirty"]:
        assert attribution["mode"] == MODE_DIRTY
        assert attribution["commitClaimed"] is False
        assert "commit" not in attribution
    else:
        assert attribution["mode"] in {MODE_COMMIT, MODE_DIRTY}
        if attribution["mode"] == MODE_COMMIT:
            assert attribution["commit"] == state["head"]


def test_aud029_attribution_rejects_a_commit_claim_on_a_dirty_tree(tmp_path: Path) -> None:
    import shutil
    import subprocess

    if shutil.which("git") is None:  # pragma: no cover - environment guard
        pytest.skip("git executable unavailable")

    def _git(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(tmp_path), "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
            check=True,
            timeout=60,
            capture_output=True,
        )

    target = tmp_path / MANIFEST
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["attribution"] = {
        "mode": MODE_COMMIT,
        "commitClaimed": True,
        "commit": "0" * 40,
        "branch": "fixture",
        "worktreeDirty": False,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _git("init", "-q")
    _git("add", "-A")
    _git("commit", "-q", "-m", "fixture")
    (tmp_path / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")

    failures = check_attribution(tmp_path)

    assert any("overclaims" in item for item in failures)
    assert any("worktreeDirty=false" in item for item in failures)
    assert any("HEAD is" in item for item in failures)

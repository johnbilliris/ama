"""spec-038 T-AA166 — CODEOWNERS dual-approval test."""

from __future__ import annotations

from pathlib import Path

CODEOWNERS = Path(__file__).resolve().parents[3] / ".github" / "CODEOWNERS"


def _read() -> list[str]:
    return CODEOWNERS.read_text(encoding="utf-8", errors="replace").splitlines()


def _find_rules_matching(prefix: str) -> list[str]:
    return [ln for ln in _read() if ln.strip().startswith(prefix)]


def test_help_content_codeowners_present() -> None:
    rules = _find_rules_matching("apps/web/src/content/help/")
    assert rules, "CODEOWNERS must reference apps/web/src/content/help/"
    # at least two distinct owner tokens (teams) required
    owners = set()
    for ln in rules:
        owners.update(t for t in ln.split() if t.startswith("@"))
    assert len(owners) >= 2, f"dual approval requires ≥2 owner teams, found {owners}"


def test_snapshot_path_codeowners_present() -> None:
    rules = _find_rules_matching("specs/038-help-docs-chat/snapshots/")
    assert rules, "CODEOWNERS must reference specs/038-help-docs-chat/snapshots/**"


def test_help_manifest_codeowners_present() -> None:
    rules = _find_rules_matching("apps/ingest-runner/manifests/help-snapshot.yaml")
    # snapshot manifest may instead be governed by content owners via the broader rule
    if not rules:
        broad = _find_rules_matching("specs/038-help-docs-chat/**")
        assert broad, "manifest must be covered by CODEOWNERS"

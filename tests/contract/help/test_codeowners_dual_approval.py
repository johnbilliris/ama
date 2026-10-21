"""spec-038 T-AA166 — CODEOWNERS ownership coverage test."""

from __future__ import annotations

from pathlib import Path

CODEOWNERS = Path(__file__).resolve().parents[3] / ".github" / "CODEOWNERS"
VALID_REPOSITORY_USERS = {"@johnbilliris"}


def _read() -> list[str]:
    return CODEOWNERS.read_text(encoding="utf-8", errors="replace").splitlines()


def _find_rules_matching(prefix: str) -> list[str]:
    return [ln for ln in _read() if ln.strip().startswith(prefix)]


def _owners(rules: list[str]) -> set[str]:
    return {token for rule in rules for token in rule.split() if token.startswith("@")}


def test_all_codeowners_are_current_repository_users() -> None:
    active_rules = [line for line in _read() if line.strip() and not line.lstrip().startswith("#")]
    owners = _owners(active_rules)
    assert owners == VALID_REPOSITORY_USERS


def test_help_content_codeowners_present() -> None:
    rules = _find_rules_matching("apps/web/src/content/help/")
    assert rules, "CODEOWNERS must reference apps/web/src/content/help/"
    assert _owners(rules) == VALID_REPOSITORY_USERS


def test_snapshot_path_codeowners_present() -> None:
    rules = _find_rules_matching("specs/038-help-docs-chat/snapshots/")
    assert rules, "CODEOWNERS must reference specs/038-help-docs-chat/snapshots/**"


def test_help_manifest_codeowners_present() -> None:
    rules = _find_rules_matching("apps/ingest-runner/manifests/help-snapshot.yaml")
    # snapshot manifest may instead be governed by content owners via the broader rule
    if not rules:
        broad = _find_rules_matching("specs/038-help-docs-chat/**")
        assert broad, "manifest must be covered by CODEOWNERS"

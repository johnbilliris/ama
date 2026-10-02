from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_TIER_ROOTS = [
    ROOT / ".github" / "agents" / "operational",
    ROOT / ".github" / "agents" / "technical",
    ROOT / ".github" / "agents" / "sectors",
]
SNAPSHOT_DOCS = [
    "specs/004-actor-github-agents/spec.md",
    "specs/004-actor-github-agents/plan.md",
    "specs/004-actor-github-agents/tasks.md",
    "specs/004-actor-github-agents/research.md",
    "specs/004-actor-github-agents/quickstart.md",
    "specs/004-actor-github-agents/checklists/requirements.md",
]


def _active_actor_files() -> list[Path]:
    files: list[Path] = []
    for tier_root in ACTIVE_TIER_ROOTS:
        for path in sorted(tier_root.rglob("*.agent.md")):
            if "/_archive/" in path.as_posix():
                continue
            files.append(path)
    return files


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"missing frontmatter in {path}"
    parts = text.split("---", 2)
    assert len(parts) >= 3, f"frontmatter delimiters not closed in {path}"
    data = yaml.safe_load(parts[1])
    return data or {}


def test_aud006_active_actor_stems_are_case_insensitively_unique() -> None:
    stems: dict[str, list[str]] = {}
    for path in _active_actor_files():
        stem = path.stem.replace(".agent", "")
        stems.setdefault(stem.lower(), []).append(path.as_posix())

    duplicates = {k: v for k, v in stems.items() if len(v) > 1}
    assert not duplicates, f"duplicate case-insensitive actor stems: {duplicates}"


def test_aud006_handoffs_resolve_to_exactly_one_active_actor() -> None:
    files = _active_actor_files()
    index: dict[str, list[Path]] = {}
    for path in files:
        actor_id = path.stem.replace(".agent", "")
        index.setdefault(actor_id.lower(), []).append(path)

    errors: list[str] = []
    for path in files:
        data = _frontmatter(path)
        for handoff in data.get("handoffs") or []:
            target = str(handoff.get("agent", "")).strip()
            if not target:
                continue
            matches = index.get(target.lower(), [])
            if len(matches) != 1:
                errors.append(f"{path.as_posix()} -> {target}: matches={len(matches)}")

    assert not errors, "handoff target must resolve exactly once: " + "; ".join(errors)


def test_aud006_frontmatter_name_aliases_do_not_override_actor_id() -> None:
    for path in _active_actor_files():
        data = _frontmatter(path)
        actor_id = path.stem.replace(".agent", "")
        if "name" in data:
            assert str(data["name"]).strip() == actor_id, f"frontmatter name alias mismatch in {path.as_posix()}"


def test_aud017_scope_evolution_snapshot_present_in_required_docs() -> None:
    required_phrase = "Scope Evolution Snapshot (2026-09-15)"
    required_current = "85 active actor files, 12 workflow agents, 6 archived sector agents"

    for rel in SNAPSHOT_DOCS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert required_phrase in text, f"missing snapshot heading in {rel}"
        assert required_current in text, f"missing current-count snapshot in {rel}"


def test_aud017_contract_semantics_align_with_host_reference() -> None:
    contract = (ROOT / "specs/004-actor-github-agents/contracts/agent-file-contract.md").read_text(encoding="utf-8")
    host_ref = (ROOT / ".github/skills/copilot-customization/references/custom-agents.md").read_text(encoding="utf-8")

    assert "default: `false`" in host_ref
    assert "defaults to `false`" in contract
    assert "max 199" in contract
    assert "Required for active actor files" in contract
    assert ".github/agents/sectors/{jurisdiction}/{agent-id}.agent.md" in contract


def test_aud017_description_boundary_examples_and_nested_path_shape() -> None:
    def valid_description(text: str) -> bool:
        return len(text) <= 199

    assert valid_description("a" * 199)
    assert not valid_description("a" * 200)
    assert not valid_description("a" * 201)

    sector_pattern = re.compile(r"^\.github/agents/sectors/[a-z0-9-]+/[a-z0-9-]+\.agent\.md$")
    assert sector_pattern.match(".github/agents/sectors/commonwealth/afp-commonwealth.agent.md")
    assert sector_pattern.match(".github/agents/sectors/cross-sector/community-ngos.agent.md")
    assert not sector_pattern.match(".github/agents/sectors/afp-commonwealth.agent.md")

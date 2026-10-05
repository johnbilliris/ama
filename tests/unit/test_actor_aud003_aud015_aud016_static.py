from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from scripts.generate_agents_catalogue import collect_entries, render_catalogue

ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = ROOT / ".github" / "agents"
ARCHIVED_ROOT = AGENTS_ROOT / "sectors" / "_archive"

READONLY_TOOLS = {
    "execute/testFailure",
    "microsoft.docs.mcp",
    "read/changes",
    "read/problems",
    "read/terminalLastCommand",
    "read/terminalSelection",
    "search",
    "search/codebase",
    "search/findTestFiles",
    "search/searchResults",
    "search/usages",
    "vscode/vscodeAPI",
    "web/fetch",
    "web/githubRepo",
}

READONLY_TOOL_ALIASES = {
    "changes": "read/changes",
    "codebase": "search/codebase",
    "edit/new": "new",
    "fetch": "web/fetch",
    "findTestFiles": "search/findTestFiles",
    "githubRepo": "web/githubRepo",
    "problems": "read/problems",
    "searchResults": "search/searchResults",
    "execute/runCommands": "runCommands",
    "execute/runTasks": "runTasks",
    "execute/runTests": "runTests",
    "terminalLastCommand": "read/terminalLastCommand",
    "terminalSelection": "read/terminalSelection",
    "testFailure": "execute/testFailure",
    "usages": "search/usages",
    "vscodeAPI": "vscode/vscodeAPI",
    "manage/todos": "todos",
}

ADVISORY_PLUS_DOCS_TOOLS = READONLY_TOOLS | {
    "edit/editFiles",
    "azure_design_architecture",
    "azure_get_code_gen_best_practices",
    "azure_get_deployment_best_practices",
    "azure_get_swa_best_practices",
    "azure_query_learn",
}

IMPLEMENTATION_EXCEPTIONS = {"infrastructure-devops", "principal-engineer"}
MUTATOR_DENYLIST = {"edit/editFiles", "new", "runCommands", "runTasks", "runTests", "todos"}
RETIRED_IDS = {
    "ambulance-paramedic",
    "commonwealth-government",
    "fire-services",
    "meteorology-bom",
    "police",
    "ses",
}

RETIRED_DIRECTIVE_PATTERNS = [
    re.compile(r"(?m)^\s*agent:\s*ambulance-paramedic\s*$"),
    re.compile(r"(?m)^\s*agent:\s*commonwealth-government\s*$"),
    re.compile(r"(?m)^\s*agent:\s*fire-services\s*$"),
    re.compile(r"(?m)^\s*agent:\s*meteorology-bom\s*$"),
    re.compile(r"(?m)^\s*agent:\s*police\s*$"),
    re.compile(r"(?m)^\s*agent:\s*ses\s*$"),
    re.compile(r"\*\*(ambulance-paramedic|commonwealth-government|fire-services|meteorology-bom|police|ses)\*\*"),
    re.compile(r"`(ambulance-paramedic|commonwealth-government|fire-services|meteorology-bom|police|ses)`"),
]


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"missing frontmatter in {path.as_posix()}"
    parts = text.split("---", 2)
    assert len(parts) >= 3, f"frontmatter delimiters not closed in {path.as_posix()}"
    return yaml.safe_load(parts[1]) or {}


def _active_actor_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(AGENTS_ROOT.rglob("*.agent.md")):
        posix = path.as_posix()
        if "/sectors/_archive/" in posix:
            continue
        if path.name.startswith("speckit."):
            continue
        files.append(path)
    return files


def test_aud003_explicit_tools_and_least_privilege_profiles() -> None:
    active = _active_actor_files()
    assert len(active) == 85

    for path in active:
        fm = _frontmatter(path)
        aid = path.stem.replace(".agent", "")
        tools = fm.get("tools")

        assert isinstance(tools, list) and tools, f"missing explicit tools in {aid}"
        tool_set = {READONLY_TOOL_ALIASES.get(str(tool), str(tool)) for tool in tools}

        rel = path.relative_to(AGENTS_ROOT).as_posix()
        if rel.startswith("operational/") or rel.startswith("sectors/"):
            assert tool_set == READONLY_TOOLS, f"operational/sector actor must be advisory-readonly: {aid}"
            assert tool_set.isdisjoint(MUTATOR_DENYLIST), f"read-only mutator leak in {aid}"
            continue

        if aid == "azure-principal-architect":
            assert tool_set == ADVISORY_PLUS_DOCS_TOOLS
            assert tool_set.isdisjoint({"new", "runCommands", "runTasks", "runTests", "todos"})
            continue

        if aid in IMPLEMENTATION_EXCEPTIONS:
            assert {"edit/editFiles", "new", "runCommands", "runTasks", "runTests"}.issubset(tool_set)
            continue

        assert tool_set == READONLY_TOOLS, f"technical non-exception must be advisory-readonly: {aid}"


def test_aud003_active_actor_agents_property_coherent_where_used() -> None:
    for path in _active_actor_files():
        fm = _frontmatter(path)
        agents = fm.get("agents")
        if agents is None:
            continue
        assert isinstance(agents, list), f"agents must be a list in {path.as_posix()}"
        if agents:
            tools = set(str(t) for t in (fm.get("tools") or []))
            assert "agent" in tools, f"agents property requires agent tool in {path.as_posix()}"


def test_aud015_catalogue_is_generated_and_bijective() -> None:
    entries = collect_entries()
    rendered = render_catalogue(entries)
    current = (AGENTS_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert current == rendered, "AGENTS.md must match generator output"

    actors = [e for e in entries if e.tier in {"operational", "sector", "technical"}]
    workflows = [e for e in entries if e.tier == "workflow"]
    archived = [e for e in entries if e.tier == "archived"]

    assert len(actors) == 85
    assert len(workflows) == 12
    assert len(archived) == 6

    actor_ids = [e.agent_id for e in actors]
    assert len(actor_ids) == len(set(actor_ids)), "active actor IDs must be unique"

    workflow_ids = {e.agent_id for e in workflows}
    assert {"speckit.fleet.review", "speckit.fleet.run", "speckit.verify.run"}.issubset(workflow_ids)

    for e in actors:
        p = ROOT / e.file_path
        assert p.exists(), f"catalogue file path missing: {e.file_path}"
        fm = _frontmatter(p)
        assert fm.get("description", "") == e.description, f"description drift for {e.agent_id}"


def test_aud015_persona_roster_and_identity_parity() -> None:
    active_sector_operational = set()
    for p in _active_actor_files():
        rel = p.relative_to(AGENTS_ROOT).as_posix()
        if rel.startswith("operational/") or rel.startswith("sectors/"):
            active_sector_operational.add(p.stem.replace(".agent", ""))

    identities = json.loads(
        (ROOT / "packages/domain/src/domain/seed/identities_australia.json").read_text(encoding="utf-8")
    )
    identity_ids = {row["persona_id"] for row in identities}
    assert active_sector_operational == identity_ids

    roster_ids: set[str] = set()
    for roster in sorted((ROOT / "packages/domain/src/domain/seed/persona-rosters").glob("*.json")):
        data = json.loads(roster.read_text(encoding="utf-8"))
        for rec in data.get("records", []):
            roster_ids.add(rec["persona_id"])
    assert roster_ids == identity_ids
    assert {"afp-act", "afp-commonwealth"}.issubset(roster_ids)


def test_aud016_archived_non_invocable_and_successors_present() -> None:
    archived_files = sorted(ARCHIVED_ROOT.glob("*.agent.md"))
    assert len(archived_files) == 6

    ids_seen: set[str] = set()
    for path in archived_files:
        fm = _frontmatter(path)
        aid = path.stem.replace(".agent", "")
        ids_seen.add(aid)
        assert fm.get("user-invocable") is False
        assert fm.get("disable-model-invocation") is True
        text = path.read_text(encoding="utf-8")
        assert "## Successor Mapping" in text, f"missing successor mapping in {aid}"

    assert ids_seen == RETIRED_IDS


def test_aud016_catalogue_docs_non_invocable_and_active_no_retired_ids() -> None:
    for rel in ["AGENTS.md", "copilot-instructions.md"]:
        fm = _frontmatter(AGENTS_ROOT / rel)
        assert fm.get("user-invocable") is False
        assert fm.get("disable-model-invocation") is True

    offenders: list[str] = []
    for path in _active_actor_files():
        text = path.read_text(encoding="utf-8")
        if any(p.search(text) for p in RETIRED_DIRECTIVE_PATTERNS):
            offenders.append(path.as_posix())

    assert not offenders, "active actor references to retired IDs found: " + ", ".join(offenders)

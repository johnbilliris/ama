#!/usr/bin/env python3
"""Fail-closed validator for actor agent catalogue structural compliance.

Scope:
- Active actor definitions under .github/agents/{operational,technical,sectors/*}
- Workflow agents in .github/agents/*.agent.md
- Archived sector agents in .github/agents/sectors/_archive/*.agent.md
- Registry/index visibility and parity checks for .github/agents/AGENTS.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.lint.check_agent_content_integrity import validate_file  # noqa: E402

REQUIRED_SECTIONS = [
    "## Role Overview",
    "## Responsibilities & Decision Rights",
    "## Scope Boundaries",
    "## Key Relationships",
    "## Contextual References",
    "## Guidance Notes",
]

READONLY_TOOLS = {
    "codebase",
    "changes",
    "fetch",
    "findTestFiles",
    "githubRepo",
    "problems",
    "search",
    "searchResults",
    "terminalLastCommand",
    "terminalSelection",
    "testFailure",
    "usages",
    "vscodeAPI",
    "microsoft.docs.mcp",
}

AZURE_PRINCIPAL_MUTATOR_DENYLIST = {"new", "runCommands", "runTasks", "runTests", "todos"}

PROFILE_ALIAS_TOKENS = {"advisory-readonly", "advisory-plus-docs", "implementation"}
IMPLEMENTATION_EXCEPTIONS = {"infrastructure-devops", "principal-engineer"}
RETIRED_IDS = {
    "ambulance-paramedic",
    "commonwealth-government",
    "fire-services",
    "meteorology-bom",
    "police",
    "ses",
}
FORBIDDEN_CATEGORY_ENTITY_TOKENS = {
    "`government` category",
    "`ngo` category",
    "AuditEntry",
    "HazardPrediction",
    "EvacuationPlan",
    "Infrastructure entity",
}
FORBIDDEN_STALE_STACK_TOKENS = {"WCAG 2.1", "TypeScript 5.6", "TypeScript 5.8", "Next.js 15"}


@dataclass(frozen=True)
class AgentDoc:
    rel_path: str
    abs_path: Path
    class_name: str
    actor_id: str
    frontmatter: dict
    body: str
    text: str


@dataclass(frozen=True)
class LedgerAssertion:
    key: str
    actor: str
    status: str
    reviewer: str


def _line_for(text: str, needle: str, default: int = 1) -> int:
    idx = text.find(needle)
    if idx < 0:
        return default
    return text.count("\n", 0, idx) + 1


def _diag(path: str, line: int, message: str) -> str:
    return f"{path}:{line}: {message}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(path: Path) -> tuple[dict, str, str]:
    text = _read(path)
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter start delimiter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("frontmatter delimiters are not closed")
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must parse to a mapping")
    return data, parts[2].lstrip("\n"), text


def _classify_agent(rel: str) -> str:
    if rel.startswith(".github/agents/sectors/_archive/"):
        return "archived"
    name = Path(rel).name
    if name.startswith("speckit."):
        return "workflow"
    if rel.startswith(".github/agents/operational/"):
        return "active-operational"
    if rel.startswith(".github/agents/technical/"):
        return "active-technical"
    if rel.startswith(".github/agents/sectors/"):
        return "active-sector"
    return "unknown"


def _actor_id_from(rel: str) -> str:
    name = Path(rel).name
    return name[: -len(".agent.md")]


def _section_content(body: str, heading: str) -> tuple[str, int]:
    pattern = re.compile(rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)")
    m = pattern.search(body)
    if not m:
        return "", -1
    start = m.start()
    line = body.count("\n", 0, start) + 1
    return m.group("body").strip(), line


def _check_required_sections(doc: AgentDoc, violations: list[str]) -> None:
    positions: list[int] = []
    for section in REQUIRED_SECTIONS:
        idx = doc.body.find(section)
        if idx < 0:
            violations.append(_diag(doc.rel_path, 1, f"missing required section: {section}"))
            continue
        positions.append(idx)

    if len(positions) == len(REQUIRED_SECTIONS) and positions != sorted(positions):
        violations.append(_diag(doc.rel_path, 1, "required sections are out of order"))

    for section in REQUIRED_SECTIONS:
        content, section_line = _section_content(doc.body, section.removeprefix("## "))
        if section_line > 0 and not content:
            violations.append(_diag(doc.rel_path, section_line, f"section is present but empty: {section}"))


def _check_frontmatter(doc: AgentDoc, violations: list[str]) -> None:
    description = doc.frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        violations.append(_diag(doc.rel_path, 1, "frontmatter description must be a non-empty string"))
    else:
        if "\n" in description or "\r" in description:
            violations.append(_diag(doc.rel_path, 1, "frontmatter description must be single-line"))
        if len(description) > 199:
            violations.append(
                _diag(doc.rel_path, 1, f"frontmatter description exceeds 199 characters ({len(description)})")
            )

    tools = doc.frontmatter.get("tools")
    if not isinstance(tools, list) or not tools:
        violations.append(_diag(doc.rel_path, 1, "frontmatter tools must be a non-empty string list"))
    else:
        tool_values = []
        for idx, item in enumerate(tools):
            if not isinstance(item, str) or not item.strip():
                violations.append(_diag(doc.rel_path, 1, f"tools[{idx}] must be a non-empty string"))
                continue
            tool_values.append(item)
            if item in PROFILE_ALIAS_TOKENS:
                violations.append(
                    _diag(doc.rel_path, 1, f"tools[{idx}] must be explicit tool ID, not profile alias '{item}'")
                )

        tool_set = set(tool_values)
        actor_id = doc.actor_id
        if doc.class_name in {"active-operational", "active-sector"} and tool_set != READONLY_TOOLS:
            violations.append(
                _diag(doc.rel_path, 1, "operational/sector actor tools must exactly match advisory-readonly tool IDs")
            )
        if doc.class_name == "active-technical":
            if actor_id == "azure-principal-architect":
                if not tool_set.issuperset(READONLY_TOOLS):
                    violations.append(
                        _diag(
                            doc.rel_path,
                            1,
                            "azure-principal-architect must include advisory-readonly baseline tool IDs",
                        )
                    )
                if "edit/editFiles" not in tool_set:
                    violations.append(_diag(doc.rel_path, 1, "azure-principal-architect must include edit/editFiles"))
                if not tool_set.isdisjoint(AZURE_PRINCIPAL_MUTATOR_DENYLIST):
                    violations.append(
                        _diag(
                            doc.rel_path,
                            1,
                            "azure-principal-architect must not include mutator run/new/task/test/todo tools",
                        )
                    )
            elif actor_id in IMPLEMENTATION_EXCEPTIONS:
                required = {"edit/editFiles", "new", "runCommands", "runTasks", "runTests"}
                if not required.issubset(tool_set):
                    violations.append(
                        _diag(doc.rel_path, 1, "implementation exception actor is missing required mutator tool IDs")
                    )
            elif tool_set != READONLY_TOOLS:
                violations.append(
                    _diag(
                        doc.rel_path,
                        1,
                        "technical actor tools must exactly match advisory-readonly tool IDs unless allowlisted",
                    )
                )

    handoffs = doc.frontmatter.get("handoffs")
    if not isinstance(handoffs, list) or not handoffs:
        violations.append(_diag(doc.rel_path, 1, "frontmatter handoffs must be a non-empty list for active actors"))
        return

    labels_seen: set[str] = set()
    for idx, handoff in enumerate(handoffs):
        if not isinstance(handoff, dict):
            violations.append(_diag(doc.rel_path, 1, f"handoffs[{idx}] must be an object"))
            continue
        for key in ("label", "agent", "prompt"):
            value = handoff.get(key)
            if not isinstance(value, str) or not value.strip():
                violations.append(_diag(doc.rel_path, 1, f"handoffs[{idx}].{key} must be a non-empty string"))
        if "send" in handoff and not isinstance(handoff.get("send"), bool):
            violations.append(_diag(doc.rel_path, 1, f"handoffs[{idx}].send must be boolean when present"))

        label = str(handoff.get("label", "")).strip().lower()
        if label:
            if label in labels_seen:
                violations.append(_diag(doc.rel_path, 1, f"duplicate handoff label in file: {label}"))
            labels_seen.add(label)


def _check_tier_additions(doc: AgentDoc, violations: list[str]) -> None:
    lower = doc.body.lower()
    if doc.class_name == "active-operational":
        if "aiims alignment:" not in lower and "aiims/functional alignment" not in lower:
            violations.append(_diag(doc.rel_path, 1, "operational actor must include explicit AIIMS alignment"))
        if "decisionrights:" not in lower:
            violations.append(_diag(doc.rel_path, 1, "operational actor must include decisionRights statement"))
        if "escalation counterpart:" not in lower:
            violations.append(_diag(doc.rel_path, 1, "operational actor must include escalation counterpart statement"))
        return

    if doc.class_name == "active-sector":
        if "/sectors/cross-sector/" in doc.rel_path:
            return
        if "authority ledger key:" not in lower:
            violations.append(_diag(doc.rel_path, 1, "sector actor must include authority ledger key"))
        if "activation and approval conditions" not in lower:
            violations.append(
                _diag(doc.rel_path, 1, "sector actor must include activation and approval conditions section")
            )
        if "jurisdiction" not in lower:
            violations.append(_diag(doc.rel_path, 1, "sector actor must include jurisdictional variation guidance"))


def _parse_authority_ledger(path: Path, violations: list[str]) -> dict[str, LedgerAssertion]:
    if not path.exists():
        violations.append(_diag(path.as_posix(), 1, "missing authority ledger"))
        return {}

    try:
        ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        violations.append(_diag(path.as_posix(), 1, f"invalid YAML: {exc}"))
        return {}

    status_values = set(ledger.get("reviewPolicy", {}).get("statusValues", []))
    assertions = ledger.get("assertions")
    if not isinstance(assertions, list):
        violations.append(_diag(path.as_posix(), 1, "authority ledger assertions must be a list"))
        return {}

    out: dict[str, LedgerAssertion] = {}
    for idx, row in enumerate(assertions):
        if not isinstance(row, dict):
            violations.append(_diag(path.as_posix(), idx + 1, f"assertions[{idx}] must be an object"))
            continue
        key = str(row.get("key", "")).strip()
        actor = str(row.get("actor", "")).strip()
        status = str(row.get("status", "")).strip()
        reviewer = str(row.get("reviewer", "")).strip()
        if not key:
            violations.append(_diag(path.as_posix(), idx + 1, f"assertions[{idx}] missing key"))
            continue
        if not actor:
            violations.append(_diag(path.as_posix(), idx + 1, f"assertions[{idx}] missing actor"))
        if status_values and status not in status_values:
            violations.append(_diag(path.as_posix(), idx + 1, f"assertions[{idx}] has unsupported status '{status}'"))
        if not reviewer:
            violations.append(_diag(path.as_posix(), idx + 1, f"assertions[{idx}] missing reviewer"))
        out[key] = LedgerAssertion(key=key, actor=actor, status=status, reviewer=reviewer)
    return out


def _check_sector_authority_link(doc: AgentDoc, ledger: dict[str, LedgerAssertion], violations: list[str]) -> None:
    if doc.class_name != "active-sector":
        return
    if "/sectors/cross-sector/" in doc.rel_path:
        return

    m = re.search(r"(?im)^Authority ledger key:\s*`?([a-z0-9-]+)`?.*$", doc.body)
    if not m:
        violations.append(_diag(doc.rel_path, 1, "sector actor is missing an Authority ledger key reference"))
        return
    key = m.group(1)
    line = doc.body.count("\n", 0, m.start()) + 1
    assertion = ledger.get(key)
    if not assertion:
        violations.append(_diag(doc.rel_path, line, f"authority ledger key does not exist: {key}"))
        return
    if assertion.actor.lower() != doc.actor_id.lower():
        violations.append(
            _diag(
                doc.rel_path,
                line,
                f"authority ledger actor mismatch for key '{key}' (expected {doc.actor_id}, got {assertion.actor})",
            )
        )


def _check_archived_doc(doc: AgentDoc, violations: list[str]) -> None:
    invocable = doc.frontmatter.get("user-invocable")
    disabled = doc.frontmatter.get("disable-model-invocation")
    if invocable is not False:
        violations.append(_diag(doc.rel_path, 1, "archived actor must set user-invocable: false"))
    if disabled is not True:
        violations.append(_diag(doc.rel_path, 1, "archived actor must set disable-model-invocation: true"))
    section, line = _section_content(doc.body, "Successor Mapping")
    if line < 0:
        violations.append(_diag(doc.rel_path, 1, "archived actor missing ## Successor Mapping section"))
    elif not section:
        violations.append(_diag(doc.rel_path, line, "archived actor has empty ## Successor Mapping section"))


def _check_index_visibility(path: Path, violations: list[str]) -> None:
    if not path.exists():
        return
    rel = path.as_posix()
    try:
        frontmatter, _body, text = _parse_frontmatter(path)
    except ValueError as exc:
        violations.append(_diag(rel, 1, str(exc)))
        return
    if frontmatter.get("user-invocable") is not False:
        violations.append(
            _diag(rel, _line_for(text, "user-invocable"), "index document must set user-invocable: false")
        )
    if frontmatter.get("disable-model-invocation") is not True:
        violations.append(
            _diag(
                rel,
                _line_for(text, "disable-model-invocation"),
                "index document must set disable-model-invocation: true",
            )
        )


def _check_handoff_resolution(active_docs: list[AgentDoc], violations: list[str]) -> None:
    index: dict[str, list[AgentDoc]] = {}
    for doc in active_docs:
        index.setdefault(doc.actor_id.lower(), []).append(doc)

    for doc in active_docs:
        for handoff in doc.frontmatter.get("handoffs") or []:
            if not isinstance(handoff, dict):
                continue
            target = str(handoff.get("agent", "")).strip().lower()
            if not target:
                continue
            matches = index.get(target, [])
            if len(matches) != 1:
                line = _line_for(doc.text, f"agent: {handoff.get('agent', '')}")
                violations.append(
                    _diag(
                        doc.rel_path,
                        line,
                        f"handoff target must resolve exactly one active non-archived actor: {handoff.get('agent', '')}",  # noqa: E501
                    )
                )


def _check_id_uniqueness(active_docs: list[AgentDoc], violations: list[str]) -> None:
    by_id: dict[str, list[AgentDoc]] = {}
    for doc in active_docs:
        by_id.setdefault(doc.actor_id.lower(), []).append(doc)
        if doc.actor_id.lower() in RETIRED_IDS:
            violations.append(
                _diag(doc.rel_path, 1, f"active actor ID is retired and cannot be reused: {doc.actor_id}")
            )

    for actor_id, docs in sorted(by_id.items()):
        if len(docs) > 1:
            joined = ", ".join(d.rel_path for d in docs)
            violations.append(
                _diag(docs[0].rel_path, 1, f"duplicate case-insensitive active actor ID '{actor_id}' across: {joined}")
            )


def _parse_markdown_table_rows(lines: list[str], start_idx: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx]
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            idx += 1
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] == "Agent Name":
            idx += 1
            continue
        rows.append(cells)
        idx += 1
    return rows, idx


def _check_registry_parity(root: Path, docs: list[AgentDoc], violations: list[str]) -> None:
    path = root / ".github" / "agents" / "AGENTS.md"
    if not path.exists():
        violations.append(_diag(path.as_posix(), 1, "AGENTS.md is missing"))
        return

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    totals_line = next((line for line in lines if line.startswith("**Totals**:")), "")
    m = re.search(
        r"(\d+) active actor files \((\d+) operational, (\d+) sector, (\d+) technical\); (\d+) workflow agents; (\d+) archived sector agents",  # noqa: E501
        totals_line,
    )
    if not m:
        violations.append(_diag(path.as_posix(), _line_for(text, "**Totals**:"), "Totals line format is invalid"))
    else:
        totals = [int(group) for group in m.groups()]
        active = [d for d in docs if d.class_name.startswith("active-")]
        workflows = [d for d in docs if d.class_name == "workflow"]
        archived = [d for d in docs if d.class_name == "archived"]
        expected = [
            len(active),
            len([d for d in active if d.class_name == "active-operational"]),
            len([d for d in active if d.class_name == "active-sector"]),
            len([d for d in active if d.class_name == "active-technical"]),
            len(workflows),
            len(archived),
        ]
        if totals != expected:
            violations.append(
                _diag(
                    path.as_posix(),
                    _line_for(text, "**Totals**:"),
                    f"Totals line mismatch: expected {expected}, got {totals}",
                )
            )

    section_headers = {
        "## Active Actor Agents": "active",
        "## Workflow Agents": "workflow",
        "## Archived Sector Agents": "archived",
    }
    table_rows: dict[str, list[list[str]]] = {"active": [], "workflow": [], "archived": []}

    idx = 0
    while idx < len(lines):
        header = lines[idx].strip()
        if header in section_headers:
            idx += 1
            while idx < len(lines) and not lines[idx].startswith("|"):
                idx += 1
            rows, idx = _parse_markdown_table_rows(lines, idx)
            table_rows[section_headers[header]] = rows
            continue
        idx += 1

    docs_by_path = {doc.rel_path: doc for doc in docs}
    for tier_key, rows in table_rows.items():
        for row in rows:
            if len(row) < 6:
                continue
            file_path = row[2]
            rel = file_path.replace("\\", "/")
            doc = docs_by_path.get(rel)
            if not doc:
                violations.append(
                    _diag(path.as_posix(), _line_for(text, file_path), f"registry references missing file: {file_path}")
                )
                continue

            if tier_key == "active" and not doc.class_name.startswith("active-"):
                violations.append(
                    _diag(
                        path.as_posix(), _line_for(text, file_path), f"registry section mismatch for file: {file_path}"
                    )
                )
            if tier_key == "workflow" and doc.class_name != "workflow":
                violations.append(
                    _diag(
                        path.as_posix(), _line_for(text, file_path), f"registry section mismatch for file: {file_path}"
                    )
                )
            if tier_key == "archived" and doc.class_name != "archived":
                violations.append(
                    _diag(
                        path.as_posix(), _line_for(text, file_path), f"registry section mismatch for file: {file_path}"
                    )
                )

            registry_id = row[1].strip()
            if registry_id != doc.actor_id:
                violations.append(
                    _diag(
                        path.as_posix(),
                        _line_for(text, file_path),
                        f"registry Agent ID mismatch for {file_path}: expected {doc.actor_id}, got {registry_id}",
                    )
                )

            desc = str(doc.frontmatter.get("description", "")).strip()
            registry_desc = row[4].strip()
            if desc != registry_desc:
                violations.append(
                    _diag(path.as_posix(), _line_for(text, file_path), f"registry description mismatch for {file_path}")
                )

    active_files = {d.rel_path for d in docs if d.class_name.startswith("active-")}
    active_registry = {row[2].replace("\\", "/") for row in table_rows["active"] if len(row) >= 3}
    missing_registry = sorted(active_files - active_registry)
    for rel in missing_registry:
        violations.append(_diag(path.as_posix(), 1, f"active actor missing from AGENTS.md table: {rel}"))


def _check_carried_rules(active_docs: list[AgentDoc], violations: list[str]) -> None:
    by_id = {doc.actor_id: doc for doc in active_docs}
    for doc in active_docs:
        text = doc.text
        for token in FORBIDDEN_CATEGORY_ENTITY_TOKENS:
            if token in text:
                violations.append(
                    _diag(doc.rel_path, _line_for(text, token), f"forbidden token from prior AUD corrections: {token}")
                )
        for token in FORBIDDEN_STALE_STACK_TOKENS:
            if token in text:
                violations.append(
                    _diag(
                        doc.rel_path,
                        _line_for(text, token),
                        f"stale stack/accessibility token from prior AUD corrections: {token}",
                    )
                )

    solution = by_id.get("solution-architect")
    if solution:
        for idx in range(1, 14):
            nfr = f"NFR-{idx:03d}"
            if nfr not in solution.text:
                violations.append(
                    _diag(solution.rel_path, 1, f"missing required NFR marker from prior AUD coverage: {nfr}")
                )

    for required_id in (
        "public-information-officer",
        "ux-designer",
        "qa-test-engineer",
        "accessibility-tester",
        "ai-ml-engineer",
    ):
        doc = by_id.get(required_id)
        if not doc:
            continue
        for marker in ("en-AU", "zh-Hans"):
            if marker not in doc.text:
                violations.append(_diag(doc.rel_path, 1, f"missing language marker from prior AUD coverage: {marker}"))


def _collect_docs(root: Path, violations: list[str]) -> list[AgentDoc]:
    agents_root = root / ".github" / "agents"
    if not agents_root.exists():
        violations.append(_diag(agents_root.as_posix(), 1, "missing .github/agents directory"))
        return []

    docs: list[AgentDoc] = []
    for abs_path in sorted(agents_root.rglob("*.agent.md")):
        rel = abs_path.relative_to(root).as_posix()
        class_name = _classify_agent(rel)
        if class_name == "unknown":
            violations.append(_diag(rel, 1, "unapproved agent file location/classification"))
            continue
        try:
            frontmatter, body, text = _parse_frontmatter(abs_path)
        except ValueError as exc:
            violations.append(_diag(rel, 1, str(exc)))
            continue
        docs.append(
            AgentDoc(
                rel_path=rel,
                abs_path=abs_path,
                class_name=class_name,
                actor_id=_actor_id_from(rel),
                frontmatter=frontmatter,
                body=body,
                text=text,
            )
        )
    return docs


def run(root: Path) -> list[str]:
    violations: list[str] = []

    docs = _collect_docs(root, violations)
    if not docs:
        return violations

    _check_index_visibility(root / ".github" / "agents" / "AGENTS.md", violations)
    _check_index_visibility(root / ".github" / "agents" / "copilot-instructions.md", violations)

    ledger = _parse_authority_ledger(
        root / "specs" / "004-actor-github-agents" / "contracts" / "authority-ledger.yaml", violations
    )

    active_docs = [doc for doc in docs if doc.class_name.startswith("active-")]
    for doc in active_docs:
        _check_frontmatter(doc, violations)
        _check_required_sections(doc, violations)
        _check_tier_additions(doc, violations)
        _check_sector_authority_link(doc, ledger, violations)

    for doc in docs:
        if doc.class_name == "archived":
            _check_archived_doc(doc, violations)

    _check_id_uniqueness(active_docs, violations)
    _check_handoff_resolution(active_docs, violations)
    _check_registry_parity(root, docs, violations)
    _check_carried_rules(active_docs, violations)

    # Reuse the existing control-byte/reference integrity checker so this gate
    # remains a comprehensive document validator.
    integrity_targets = [doc.rel_path for doc in docs if doc.class_name != "workflow"] + [".github/agents/AGENTS.md"]
    for rel in integrity_targets:
        path = root / rel
        for err in validate_file(path, root):
            if err.startswith(str(path)):
                suffix = err[len(str(path)) :]
                violations.append(rel + suffix)
            else:
                violations.append(err)

    return sorted(set(violations))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate actor agent catalogue against feature contract")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root path")
    args = parser.parse_args(argv)

    violations = run(args.root.resolve())
    if violations:
        print("actor-agent-catalogue: FAIL")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("actor-agent-catalogue: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

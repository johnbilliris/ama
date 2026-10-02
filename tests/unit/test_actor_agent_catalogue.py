from __future__ import annotations

from pathlib import Path

from tools.lint.check_actor_agent_catalogue import READONLY_TOOLS, run


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _tools_yaml(indent: str = "") -> str:
    items = "\n".join(f"{indent}- {tool}" for tool in sorted(READONLY_TOOLS))
    return f"\n{items}\n"


def _agent_doc(description: str, handoff_target: str, extra: str = "") -> str:
    return (
        "---\n"
        f'description: "{description}"\n'
        "tools:"
        f"{_tools_yaml()}"
        "handoffs:\n"
        "- label: Escalate to architecture\n"
        f"  agent: {handoff_target}\n"
        "  prompt: Need architecture decision guidance.\n"
        "  send: true\n"
        "---\n\n"
        "## Role Overview\n\n"
        "AIIMS alignment: command.\n"
        "Authority scope: operational command with documented delegations.\n"
        "\n"
        "## Responsibilities & Decision Rights\n\n"
        "- decisionRights: Approve scoped tactical decisions.\n"
        "- Escalation counterpart: solution-architect.\n"
        "\n"
        "## Scope Boundaries\n\n"
        "- Out-of-scope architecture implementation details are escalated.\n"
        "\n"
        "## Key Relationships\n\n"
        "- solution-architect for cross-cutting design decisions.\n"
        "\n"
        "## Contextual References\n\n"
        "- .specify/memory/constitution.md\n"
        "- specs/001-disaster-response-hub/data-model.md\n"
        "\n"
        "## Guidance Notes\n\n"
        "Operational guidance remains advisory and scoped.\n"
        f"{extra}"
    )


def _solution_doc() -> str:
    nfr_lines = "\n".join(f"- NFR-{idx:03d}" for idx in range(1, 14))
    return (
        "---\n"
        'description: "Solution architecture guidance for platform and quality controls."\n'
        "tools:"
        f"{_tools_yaml()}"
        "handoffs:\n"
        "- label: Return to incident command\n"
        "  agent: incident-commander\n"
        "  prompt: Share architecture implications for command decisions.\n"
        "  send: true\n"
        "---\n\n"
        "## Role Overview\n\n"
        "Defines architecture guardrails and trade-offs.\n\n"
        "## Responsibilities & Decision Rights\n\n"
        "- decisionRights: Recommend architecture boundaries.\n\n"
        "## Scope Boundaries\n\n"
        "- Does not approve incident operations.\n\n"
        "## Key Relationships\n\n"
        "- incident-commander for operational alignment.\n\n"
        "## Contextual References\n\n"
        "- .specify/memory/constitution.md\n"
        "- specs/001-disaster-response-hub/data-model.md\n\n"
        "## Guidance Notes\n\n"
        "Constitution and quality gates:\n"
        f"{nfr_lines}\n"
    )


def _sector_doc() -> str:
    return (
        "---\n"
        'description: "Sector guidance for NSW fire coordination and escalation boundaries."\n'
        "tools:"
        f"{_tools_yaml()}"
        "handoffs:\n"
        "- label: Escalate to incident command\n"
        "  agent: incident-commander\n"
        "  prompt: Need command-level prioritisation.\n"
        "  send: true\n"
        "---\n\n"
        "## Role Overview\n\n"
        "Sector role for NSW fire operations.\n"
        "Authority ledger key: `authority-nsw-rfs` (status: UNVERIFIED).\n\n"
        "## Responsibilities & Decision Rights\n\n"
        "- decisionRights: Operate under command approvals.\n\n"
        "## Scope Boundaries\n\n"
        "- Command authority remains with incident-commander.\n\n"
        "## Key Relationships\n\n"
        "- incident-commander for escalations.\n\n"
        "## Contextual References\n\n"
        "- .specify/memory/constitution.md\n"
        "- specs/001-disaster-response-hub/data-model.md\n"
        "- specs/004-actor-github-agents/contracts/authority-ledger.yaml\n\n"
        "## Guidance Notes\n\n"
        "### Activation and Approval Conditions (Qualified)\n"
        "- Activation trigger label: AIIMS activation.\n"
        "### Jurisdiction and Coordination Boundaries\n"
        "- Jurisdiction scope: New South Wales.\n"
    )


def _archived_doc() -> str:
    return (
        "---\n"
        'description: "Archived profile retained for historical traceability."\n'
        "user-invocable: false\n"
        "disable-model-invocation: true\n"
        "---\n\n"
        "## Role Overview\n\n"
        "Historical profile.\n\n"
        "## Successor Mapping\n\n"
        "- Use nsw-rfs for active guidance.\n"
    )


def _workflow_doc() -> str:
    return '---\ndescription: "Workflow helper agent."\n---\n\n# Speckit.plan\n'


def _agents_registry() -> str:
    return (
        "---\n"
        'description: "Reference catalogue of all actor-specific agents - not an interactive agent."\n'
        "user-invocable: false\n"
        "disable-model-invocation: true\n"
        "---\n\n"
        "# Actor Agent Catalogue\n\n"
        "**Last Updated**: 2026-09-15\n"
        "**Totals**: 3 active actor files (1 operational, 1 sector, 1 technical); 1 workflow agents; 1 archived sector agents\n\n"  # noqa: E501
        "## Active Actor Agents\n\n"
        "| Agent Name | Agent ID | File Path | Tier | Description | Key Handoffs |\n"
        "|---|---|---|---|---|---|\n"
        "| Incident Commander | incident-commander | .github/agents/operational/incident-commander.agent.md | operational | AIIMS Incident Controller guidance for command-level disaster coordination. | solution-architect |\n"  # noqa: E501
        "| Nsw Rfs | nsw-rfs | .github/agents/sectors/nsw/nsw-rfs.agent.md | sector | Sector guidance for NSW fire coordination and escalation boundaries. | incident-commander |\n"  # noqa: E501
        "| Solution Architect | solution-architect | .github/agents/technical/solution-architect.agent.md | technical | Solution architecture guidance for platform and quality controls. | incident-commander |\n\n"  # noqa: E501
        "## Workflow Agents\n\n"
        "| Agent Name | Agent ID | File Path | Tier | Description | Key Handoffs |\n"
        "|---|---|---|---|---|---|\n"
        "| Speckit.plan | speckit.plan | .github/agents/speckit.plan.agent.md | workflow | Workflow helper agent. |  |\n\n"  # noqa: E501
        "## Archived Sector Agents\n\n"
        "| Agent Name | Agent ID | File Path | Tier | Description | Key Handoffs | Successor Mapping |\n"
        "|---|---|---|---|---|---|---|\n"
        "| Fire Services | fire-services | .github/agents/sectors/_archive/fire-services.agent.md | archived | Archived profile retained for historical traceability. | incident-commander | Use nsw-rfs |\n"  # noqa: E501
    )


def _authority_ledger() -> str:
    return (
        "schemaVersion: 1\n"
        "reviewPolicy:\n"
        "  statusValues:\n"
        "  - VERIFIED\n"
        "  - UNVERIFIED\n"
        "assertions:\n"
        "- key: authority-nsw-rfs\n"
        "  actor: nsw-rfs\n"
        "  reviewer: repository-audit\n"
        "  status: UNVERIFIED\n"
    )


def _build_valid_fixture(root: Path) -> None:
    _write(root / ".specify/memory/constitution.md", "constitution")
    _write(root / "specs/001-disaster-response-hub/data-model.md", "data-model")
    _write(root / "specs/004-actor-github-agents/contracts/authority-ledger.yaml", _authority_ledger())

    _write(
        root / ".github/agents/operational/incident-commander.agent.md",
        _agent_doc(
            "AIIMS Incident Controller guidance for command-level disaster coordination.",
            "solution-architect",
        ),
    )
    _write(root / ".github/agents/technical/solution-architect.agent.md", _solution_doc())
    _write(root / ".github/agents/sectors/nsw/nsw-rfs.agent.md", _sector_doc())
    _write(root / ".github/agents/sectors/_archive/fire-services.agent.md", _archived_doc())
    _write(root / ".github/agents/speckit.plan.agent.md", _workflow_doc())
    _write(root / ".github/agents/AGENTS.md", _agents_registry())


def test_actor_catalogue_valid_fixture_passes(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    assert run(tmp_path) == []


def test_actor_catalogue_duplicate_case_insensitive_id_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    _write(
        tmp_path / ".github/agents/technical/Incident-Commander.agent.md",
        _solution_doc().replace("solution-architect", "incident-commander"),
    )
    violations = run(tmp_path)
    assert any("duplicate case-insensitive active actor ID" in item for item in violations)
    assert any(".github/agents/operational/incident-commander.agent.md:1:" in item for item in violations)


def test_actor_catalogue_missing_tools_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/operational/incident-commander.agent.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "tools:\n- changes\n- codebase\n- fetch\n- findTestFiles\n- githubRepo\n- microsoft.docs.mcp\n- problems\n- search\n- searchResults\n- terminalLastCommand\n- terminalSelection\n- testFailure\n- usages\n- vscodeAPI\n",  # noqa: E501
        "tools: []\n",
        1,
    )
    _write(path, text)
    violations = run(tmp_path)
    assert any("frontmatter tools must be a non-empty string list" in item for item in violations)
    assert any(".github/agents/operational/incident-commander.agent.md:1:" in item for item in violations)


def test_actor_catalogue_description_bound_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/technical/solution-architect.agent.md"
    text = path.read_text(encoding="utf-8").replace(
        'description: "Solution architecture guidance for platform and quality controls."',
        f'description: "{"x" * 200}"',
        1,
    )
    _write(path, text)
    violations = run(tmp_path)
    assert any("description exceeds 199 characters" in item for item in violations)


def test_actor_catalogue_required_section_non_empty_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/operational/incident-commander.agent.md"
    text = path.read_text(encoding="utf-8").replace(
        "## Key Relationships\n\n- solution-architect for cross-cutting design decisions.\n\n",
        "## Key Relationships\n\n",
        1,
    )
    _write(path, text)
    violations = run(tmp_path)
    assert any("section is present but empty" in item for item in violations)


def test_actor_catalogue_unique_handoff_labels_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/technical/solution-architect.agent.md"
    text = path.read_text(encoding="utf-8").replace(
        "handoffs:\n- label: Return to incident command\n  agent: incident-commander\n  prompt: Share architecture implications for command decisions.\n  send: true\n",  # noqa: E501
        "handoffs:\n- label: Return to incident command\n  agent: incident-commander\n  prompt: Share architecture implications for command decisions.\n  send: true\n- label: Return to incident command\n  agent: incident-commander\n  prompt: Duplicate label should fail.\n  send: false\n",  # noqa: E501
        1,
    )
    _write(path, text)
    violations = run(tmp_path)
    assert any("duplicate handoff label" in item for item in violations)


def test_actor_catalogue_handoff_target_resolution_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/sectors/nsw/nsw-rfs.agent.md"
    text = path.read_text(encoding="utf-8").replace("agent: incident-commander", "agent: fire-services", 1)
    _write(path, text)
    violations = run(tmp_path)
    assert any("handoff target must resolve exactly one active non-archived actor" in item for item in violations)


def test_actor_catalogue_registry_parity_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/AGENTS.md"
    text = path.read_text(encoding="utf-8").replace(
        "Sector guidance for NSW fire coordination and escalation boundaries.",
        "Wrong description",
        1,
    )
    _write(path, text)
    violations = run(tmp_path)
    assert any("registry description mismatch" in item for item in violations)


def test_actor_catalogue_archived_visibility_and_successor_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/sectors/_archive/fire-services.agent.md"
    text = path.read_text(encoding="utf-8").replace("user-invocable: false", "user-invocable: true", 1)
    text = text.replace("## Successor Mapping\n\n- Use nsw-rfs for active guidance.\n", "## Successor Mapping\n\n", 1)
    _write(path, text)
    violations = run(tmp_path)
    assert any("archived actor must set user-invocable: false" in item for item in violations)
    assert any("empty ## Successor Mapping" in item for item in violations)


def test_actor_catalogue_authority_ledger_link_fails(tmp_path: Path) -> None:
    _build_valid_fixture(tmp_path)
    path = tmp_path / ".github/agents/sectors/nsw/nsw-rfs.agent.md"
    text = path.read_text(encoding="utf-8").replace("authority-nsw-rfs", "authority-missing", 1)
    _write(path, text)
    violations = run(tmp_path)
    assert any("authority ledger key does not exist" in item for item in violations)

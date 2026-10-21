from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = ROOT / ".github" / "agents"


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _active_agent_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(AGENTS_ROOT.rglob("*.agent.md")):
        posix = path.as_posix()
        if "/_archive/" in posix:
            continue
        if path.name.startswith("speckit."):
            continue
        files.append(path)
    return files


def test_aud011_categories_and_entities_grounded_to_parent_model() -> None:
    community = _read(".github/agents/sectors/cross-sector/community-ngos.agent.md")
    local = _read(".github/agents/sectors/cross-sector/local-government.agent.md")
    state = _read(".github/agents/sectors/cross-sector/state-government.agent.md")
    territory = _read(".github/agents/sectors/cross-sector/territory-government.agent.md")
    observer = _read(".github/agents/operational/observer-auditor.agent.md")
    resilience = _read(".github/agents/operational/resilience-planner.agent.md")
    data_engineer = _read(".github/agents/technical/data-engineer.agent.md")
    transport = _read(".github/agents/sectors/cross-sector/transport.agent.md")
    utility = _read(".github/agents/sectors/cross-sector/utility.agent.md")

    assert "(`community` category)" in community
    assert "(`local_government` category)" in local
    assert "(`state` category)" in state
    assert "(`territory` category)" in territory

    assert "TimelineEvent, ApprovalDecision" in observer
    assert "ScenarioRun entities" in resilience
    assert "HazardAssessment" in data_engineer

    assert "Infrastructure entity" not in transport
    assert "Infrastructure entity" not in utility
    assert "EvacuationPlan" not in data_engineer

    forbidden_tokens = ["`government` category", "`ngo` category", "AuditEntry", "HazardPrediction"]
    for path in _active_agent_files():
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"forbidden grounded-token '{token}' in {path.as_posix()}"


def test_aud011_operational_role_overview_has_alignment_authority_inputs_and_escalation() -> None:
    operational = sorted((AGENTS_ROOT / "operational").glob("*.agent.md"))
    assert len(operational) == 10

    for path in operational:
        text = path.read_text(encoding="utf-8")
        assert "AIIMS alignment:" in text
        assert "decisionRights:" in text
        assert "Authority scope:" in text
        assert "Information inputs:" in text
        assert "Escalation counterpart:" in text


def test_aud012_stack_guidance_uses_metadata_sources_and_nfr_map_is_complete() -> None:
    solution = _read(".github/agents/technical/solution-architect.agent.md")
    principal = _read(".github/agents/technical/principal-engineer.agent.md")
    copilot = _read(".github/agents/copilot-instructions.md")
    contributing = _read("CONTRIBUTING.md")

    assert "apps/web/package.json" in solution
    assert "pyproject.toml" in solution
    assert "pyproject.toml" in principal
    assert "apps/web/package.json" in principal
    assert "ruff.toml" in principal

    assert "Current Runtime Pins (authoritative)" in copilot
    assert "Historical Feature Stack Log (not current pins)" in copilot
    assert "TypeScript 6.0.3" in contributing

    for idx in range(1, 14):
        nfr = f"NFR-{idx:03d}"
        assert nfr in solution


def test_aud012_and_aud013_no_stale_wcag_or_actor_stack_literals() -> None:
    for path in _active_agent_files():
        text = path.read_text(encoding="utf-8")
        assert "WCAG 2.1" not in text
        assert "TypeScript 5.6" not in text
        assert "TypeScript 5.8" not in text
        assert "Next.js 15" not in text


def test_aud013_shared_language_policy_consistent_across_named_actors() -> None:
    pio = _read(".github/agents/operational/public-information-officer.agent.md")
    ux = _read(".github/agents/technical/ux-designer.agent.md")
    qa = _read(".github/agents/technical/qa-test-engineer.agent.md")
    a11y = _read(".github/agents/technical/accessibility-tester.agent.md")
    ai_ml = _read(".github/agents/technical/ai-ml-engineer.agent.md")

    for text in (pio, ux, qa, a11y, ai_ml):
        assert "en-AU" in text
        assert "zh-Hans" in text

    assert "RTL readiness" in pio
    assert "RTL readiness" in ux
    assert "RTL readiness" in qa
    assert "RTL readiness" in a11y
    assert "RTL readiness" in ai_ml


def test_aud014_boundaries_escalation_and_dispatch_sources_reconciled() -> None:
    dfes = _read(".github/agents/sectors/wa/dfes-wa.agent.md")
    arc = _read(".github/agents/sectors/commonwealth/arc.agent.md")
    local = _read(".github/agents/sectors/cross-sector/local-government.agent.md")
    principal = _read(".github/agents/technical/principal-engineer.agent.md")
    decision_rights = _read("docs/agents/decision-rights.md")
    parent_spec = _read("specs/001-disaster-response-hub/spec.md")

    assert "Do not hand off to a separate WA SES actor" in dfes
    assert "combined-agency boundary" in dfes.lower()
    assert "status: UNVERIFIED" in dfes

    assert "Local government typically controls evacuation-centre facilities" in arc
    assert "councils manage facilities and site operations" in local

    assert "Field -> Operations -> Incident Commander" in principal

    assert "Publish** to channels (live)" in decision_rights
    assert "delegated drafting does not grant dispatch approval" in decision_rights
    assert "Rehearsal synthetic egress" in decision_rights

    assert "Public alert dispatch (CAP)" in parent_spec
    assert "live dispatch requires IC approval" in parent_spec

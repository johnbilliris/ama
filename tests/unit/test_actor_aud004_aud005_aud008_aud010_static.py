from __future__ import annotations

import re
from pathlib import Path

import yaml

from tools.lint.check_agent_contract_structure import validate_repo

ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = ROOT / ".github" / "agents"
LEDGER_PATH = ROOT / "specs" / "004-actor-github-agents" / "contracts" / "authority-ledger.yaml"


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"missing frontmatter in {path.as_posix()}"
    parts = text.split("---", 2)
    assert len(parts) >= 3, f"broken frontmatter in {path.as_posix()}"
    return yaml.safe_load(parts[1]) or {}


def _body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split("---", 2)[2].lstrip("\n")


def _active_actor_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(AGENTS_ROOT.rglob("*.agent.md")):
        posix = path.as_posix()
        if "/_archive/" in posix:
            continue
        if path.name.startswith("speckit."):
            continue
        files.append(path)
    return files


def _jurisdiction_sector_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted((AGENTS_ROOT / "sectors").rglob("*.agent.md")):
        posix = path.as_posix()
        if "/_archive/" in posix or "/cross-sector/" in posix:
            continue
        files.append(path)
    return files


def test_aud008_authority_ledger_present_and_mapped_for_50_sector_files() -> None:
    ledger = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
    assertions = {row["key"]: row for row in ledger.get("assertions") or []}

    sector_files = _jurisdiction_sector_files()
    assert len(sector_files) == 50

    for path in sector_files:
        aid = path.stem.replace(".agent", "")
        key = f"authority-{aid}"
        body = _body(path)
        assert f"`{key}`" in body, f"missing authority key reference in {path.as_posix()}"
        assert key in assertions, f"authority key missing in ledger: {key}"
        assert assertions[key]["status"] in {"VERIFIED", "UNVERIFIED", "HISTORICAL"}


def test_aud008_conflicting_commonwealth_act_titles_absent_from_active_guidance() -> None:
    bad = [
        re.compile(r"Emergency Management Act 2005 \(Cth\)"),
        re.compile(r"Emergency Management Act 2024"),
    ]
    for path in _active_actor_files():
        text = path.read_text(encoding="utf-8")
        for rx in bad:
            assert not rx.search(text), f"stale/unverified Commonwealth act claim in {path.as_posix()}"


def test_aud008_stale_agency_and_qld_role_conflation_removed_from_active_files() -> None:
    state = (AGENTS_ROOT / "sectors" / "cross-sector" / "state-government.agent.md").read_text(encoding="utf-8")
    local = (AGENTS_ROOT / "sectors" / "cross-sector" / "local-government.agent.md").read_text(encoding="utf-8")

    assert "Resilience NSW" not in state
    assert "Queensland Fire and Emergency Services (QFES)" not in state
    assert "mayors are local disaster coordinators" not in local
    assert "Local Disaster Coordinator is a separate appointed role" in local


def test_aud005_handoff_labels_unique_and_no_landscape_bushfire_to_asa() -> None:
    for path in _active_actor_files():
        fm = _frontmatter(path)
        labels = [str(h.get("label", "")).strip() for h in (fm.get("handoffs") or [])]
        assert len(labels) == len(set(labels)), f"duplicate handoff labels in {path.as_posix()}"

        for handoff in fm.get("handoffs") or []:
            target = str(handoff.get("agent", "")).strip()
            prompt = str(handoff.get("prompt", "")).lower()
            if target == "asa":
                assert "bushfire" not in prompt, f"bushfire prompt routed to asa in {path.as_posix()}"


def test_aud005_cross_sector_national_files_do_not_default_to_single_state() -> None:
    for name in ("health", "transport", "volunteer"):
        path = AGENTS_ROOT / "sectors" / "cross-sector" / f"{name}.agent.md"
        fm = _frontmatter(path)
        prompts = "\n".join(str(h.get("prompt", "")) for h in (fm.get("handoffs") or []))
        assert "If jurisdiction is missing, ask for it" in prompts


def test_aud004_sector_files_have_substantive_guidance_and_non_tautological_boundaries() -> None:
    sector_files = _jurisdiction_sector_files()
    assert len(sector_files) == 50

    for path in sector_files:
        body = _body(path)
        assert "## Guidance Notes" in body
        assert "### Authority Status and Citation" in body
        assert "### Activation and Approval Conditions (Qualified)" in body
        assert "### Jurisdiction and Coordination Boundaries" in body
        assert "### Adjacent Capability Exclusions" in body
        assert "Operations outside the scope of" not in body


def test_aud010_full_contract_structure_validator_passes() -> None:
    errors = validate_repo(ROOT)
    assert not errors, "\n".join(errors)


def test_aud010_contract_validator_negative_and_unicode_boundary_fixtures(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    agents = repo / ".github" / "agents" / "operational"
    agents.mkdir(parents=True)

    bad = agents / "broken.agent.md"
    bad.write_text(
        """---
description: """
        + ("x" * 200)
        + """
tools: [codebase]
handoffs:
  - label: bad
    agent: x
    prompt: x
---
## Role Overview
AIIMS

## Responsibilities & Decision Rights

## Scope Boundaries
x

## Key Relationships
x

## Contextual References
x

## Guidance Notes
x
""",
        encoding="utf-8",
    )

    errors = validate_repo(repo, expected_count=None)
    assert any("description exceeds 199 chars" in e for e in errors)
    assert any("section '## Responsibilities & Decision Rights' is empty" in e for e in errors)

    good = agents / "ok.agent.md"
    good.write_text(
        """---
description: """
        + ("e" * 198)
        + "é"
        + """
tools: [codebase]
handoffs:
  - label: ok
    agent: y
    prompt: y
    send: true
---
## Role Overview
AIIMS alignment text.
decisionRights: bounded.

## Responsibilities & Decision Rights
- x

## Scope Boundaries
- x

## Key Relationships
- x

## Contextual References
- specs/001-disaster-response-hub/spec.md

## Guidance Notes
- x
""",
        encoding="utf-8",
    )

    ok_errors = validate_repo(repo, expected_count=None)
    # The fixture still contains one known-bad file, but the unicode-boundary
    # file must not introduce a description-length failure of its own.
    assert all("ok.agent.md: description exceeds 199 chars" not in e for e in ok_errors)

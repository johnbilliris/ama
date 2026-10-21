from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AUD001_TARGETS = [
    ".github/agents/technical/solution-architect.agent.md",
    ".github/agents/technical/azure-principal-architect.agent.md",
    ".github/agents/technical/infrastructure-devops.agent.md",
    ".github/agents/technical/compliance-auditor.agent.md",
    ".github/agents/technical/data-engineer.agent.md",
    ".github/agents/technical/product-owner-ba.agent.md",
    ".github/agents/technical/qa-test-engineer.agent.md",
    ".github/agents/technical/software-developer.agent.md",
    ".github/agents/technical/security-engineer.agent.md",
    ".github/agents/operational/planning-officer.agent.md",
]

AUD001_TECHNICAL_WITH_AU_POLICY = [p for p in AUD001_TARGETS if "/technical/" in p]

STALE_PATTERNS = [
    r"\bAll 6 principles\b",
    r"\ball 6 principles\b",
    r"\bPrinciple VI\b",
    r"\bConstitution Principle VI\b",
    r"\bno exceptions\b",
    r"\bPrinciple III \(Provenance & Transparency\)",
    r"\bPrinciple IV \(Deterministic Coordination\)",
]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_aud001_no_stale_constitution_citations() -> None:
    regexes = [re.compile(p) for p in STALE_PATTERNS]
    for rel_path in AUD001_TARGETS:
        text = _read(rel_path)
        for rx in regexes:
            assert not rx.search(text), f"stale citation found in {rel_path}: {rx.pattern}"


def test_aud001_shared_grounding_reference_present() -> None:
    marker = "specs/004-actor-github-agents/contracts/constitutional-grounding.md"
    for rel_path in AUD001_TARGETS:
        assert marker in _read(rel_path), f"missing shared grounding reference in {rel_path}"


def test_aud001_technical_files_include_viii_and_carveout_qualifier() -> None:
    for rel_path in AUD001_TECHNICAL_WITH_AU_POLICY:
        text = _read(rel_path)
        assert "VIII" in text, f"missing Constitution VIII mention in {rel_path}"
        assert "carve-out" in text, f"missing carve-out qualifier in {rel_path}"


def test_aud002_required_aws_terms_and_scale_separation() -> None:
    pio = _read(".github/agents/operational/public-information-officer.agent.md")
    bom = _read(".github/agents/sectors/commonwealth/bom-national.agent.md")
    ux = _read(".github/agents/technical/ux-designer.agent.md")

    for text, name in ((pio, "pio"), (bom, "bom")):
        for required in (
            "Advice",
            "Watch and Act",
            "Emergency Warning",
            "Warning Level",
            "Hazard/Location",
            "Action Statement",
        ):
            assert required in text, f"missing '{required}' in {name}"
        assert "all-clear" in text, f"missing all-clear guidance in {name}"
        assert "Catastrophic" in text and "not" in text, f"missing explicit Catastrophic exclusion in {name}"

    ux_lower = ux.lower()
    assert "aws public-warning levels" in ux_lower
    assert "internal incident severity" in ux_lower
    assert "fire-danger ratings" in ux_lower
    assert "catastrophic" in ux_lower and "not" in ux_lower

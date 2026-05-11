"""T110 — Contract test for RAG-OPTOUT marker ↔ ADR binding (Spec 036 / FR-RAG-NS-08, SC-008).

Walks every Python module under ``apps/agents/`` and ``apps/api/app/services/``
and asserts:

1. **Marker → ADR**: every ``# RAG-OPTOUT [FR-RAG-NS-NN]`` comment is followed
   by a matching ADR file
   ``docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-*.md``.
2. **FR coverage**: every FR in FR-RAG-NS-01..09 has at least one ADR.
3. **ADR → marker**: every ADR file (except the meta-ADR for the lint itself,
   FR-RAG-NS-08) is referenced by ≥ 1 marker in the codebase **OR** carries a
   ``code_marker_optional: true`` front-matter line (used for ADRs whose
   carve-out is implicit in the absence of an LLM call site, e.g. a structured
   pipeline like the Dependency Notifier).
4. **Format**: every marker matches the canonical regex
   ``# RAG-OPTOUT [FR-RAG-NS-(0[1-9])]: <reason>``.

This is the structural lint that guarantees opt-outs are intentional and
auditable. CI runs it as a blocking step (T128).

The accompanying lint script is
``tools/lint/check_rag_optout_bindings.py`` (T128) — this test exercises the
same library.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPS_AGENTS = ROOT / "apps" / "agents"
APPS_API_SERVICES = ROOT / "apps" / "api" / "app" / "services"
ADR_DIR = ROOT / "docs" / "decisions" / "036-foundry-rag-grounding"

#: Canonical marker form (FR-RAG-NS-08).
MARKER_RE = re.compile(r"#\s*RAG-OPTOUT\s*\[FR-RAG-NS-(0[1-9])\]\s*:?\s*(?P<reason>.*)")

#: ADR filenames carry the FR ordinal as a 2-digit prefix.
ADR_FILE_RE = re.compile(r"^(0[1-9])-rag-optout-[a-z0-9-]+\.md$")

#: All nine FR-RAG-NS clauses MUST be covered.
ALL_FR_ORDINALS: tuple[str, ...] = tuple(f"0{i}" for i in range(1, 10))


def _scan_markers() -> list[tuple[Path, int, str, str]]:
    """Return ``(file, line, ordinal, reason)`` tuples for every marker found."""
    out: list[tuple[Path, int, str, str]] = []
    for root in (APPS_AGENTS, APPS_API_SERVICES):
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                text = py.read_text(encoding="utf-8")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                m = MARKER_RE.search(line)
                if not m:
                    continue
                out.append((py, lineno, m.group(1), (m.group("reason") or "").strip()))
    return out


def _adr_files() -> dict[str, Path]:
    """Map ordinal → ADR path for every well-formed ADR file."""
    if not ADR_DIR.exists():
        return {}
    out: dict[str, Path] = {}
    for f in sorted(ADR_DIR.iterdir()):
        if not f.is_file():
            continue
        m = ADR_FILE_RE.match(f.name)
        if m:
            out[m.group(1)] = f
    return out


def _adr_marker_optional(adr_path: Path) -> bool:
    """An ADR may declare itself marker-optional via front-matter line."""
    try:
        text = adr_path.read_text(encoding="utf-8")
    except OSError:
        return False
    # Match either ``code_marker_optional: true`` (yaml) or the markdown
    # bold form ``**Code-marker optional**: true``.
    return bool(
        re.search(r"^\s*code_marker_optional\s*:\s*true", text, re.MULTILINE | re.IGNORECASE)
        or re.search(r"\*\*Code[- ]marker optional\*\*\s*:\s*true", text, re.IGNORECASE)
    )


def test_every_fr_has_an_adr() -> None:
    """Every FR-RAG-NS-01..09 MUST have a corresponding ADR file."""
    adrs = _adr_files()
    missing = [ordinal for ordinal in ALL_FR_ORDINALS if ordinal not in adrs]
    assert not missing, f"missing ADR(s) under {ADR_DIR.relative_to(ROOT)}: FR-RAG-NS-{', FR-RAG-NS-'.join(missing)}"


def test_every_marker_has_an_adr() -> None:
    """Every marker in code MUST point at an existing ADR."""
    adrs = _adr_files()
    markers = _scan_markers()
    orphans: list[str] = []
    for path, lineno, ordinal, _reason in markers:
        if ordinal not in adrs:
            orphans.append(f"{path.relative_to(ROOT)}:{lineno} → FR-RAG-NS-{ordinal}")
    assert not orphans, "marker(s) without a matching ADR:\n  " + "\n  ".join(orphans)


def test_every_marker_is_canonical_form() -> None:
    """Markers MUST match the canonical regex (caller cargo-cult-resistance)."""
    markers = _scan_markers()
    # Re-scan but assert each line strictly conforms.
    bad: list[str] = []
    pat = re.compile(
        r"^\s*#\s*RAG-OPTOUT\s*\[FR-RAG-NS-(0[1-9])\]\s*:\s*\S",
    )
    for path, lineno, _ordinal, _reason in markers:
        text = path.read_text(encoding="utf-8").splitlines()
        line = text[lineno - 1]
        if not pat.search(line):
            bad.append(f"{path.relative_to(ROOT)}:{lineno} → {line.strip()!r}")
    assert not bad, "marker(s) not in canonical form `# RAG-OPTOUT [FR-RAG-NS-NN]: <reason>`:\n  " + "\n  ".join(bad)


def test_every_adr_is_referenced_or_marker_optional() -> None:
    """Every ADR (except FR-RAG-NS-08, the lint meta-ADR) MUST either:

    1. be referenced by ≥ 1 marker in the codebase, OR
    2. declare ``code_marker_optional: true`` in its front-matter.

    Rationale: some carve-outs are implicit (the call site does not exist
    because the pipeline never invokes an LLM, e.g. Dependency Notifier).
    """
    adrs = _adr_files()
    markers = _scan_markers()
    referenced_ordinals = {ordinal for _, _, ordinal, _ in markers}

    unreachable: list[str] = []
    for ordinal, adr_path in adrs.items():
        if ordinal == "08":
            # The lint meta-ADR exists for the lint mechanism itself.
            continue
        if ordinal in referenced_ordinals:
            continue
        if _adr_marker_optional(adr_path):
            continue
        unreachable.append(f"FR-RAG-NS-{ordinal} ({adr_path.relative_to(ROOT)})")
    assert not unreachable, (
        "ADR(s) without any code marker AND without ``code_marker_optional: true``:\n  " + "\n  ".join(unreachable)
    )


def test_marker_count_matches_or_exceeds_call_sites() -> None:
    """Smoke check: at least one marker exists in the codebase.

    Production opt-out call sites land in T127. Until then, at minimum the
    Simulation Controller's offline-execution path carries one marker (already
    landed in Phase C).
    """
    markers = _scan_markers()
    assert markers, (
        "no RAG-OPTOUT markers found in apps/agents or apps/api/app/services. "
        "Production carve-out call sites (T127) MUST carry markers."
    )

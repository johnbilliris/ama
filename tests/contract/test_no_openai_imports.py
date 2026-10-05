"""T011 — Binding lint for legacy ``from openai import AzureOpenAI`` (FR-RAG-FM-04, SC-002).

Spec 036 / ADR-20 hard cutover is complete and the ADR-20 §Q-P6-03 cosmetic
cleanup PR has landed — this lint is now **binding**. It scans every Python
module under ``apps/`` for top-level imports of the legacy ``AzureOpenAI`` /
``AsyncAzureOpenAI`` symbols and for the ``OpenAIChatClient(mode='azure_openai')``
constructor shape. Production modules that need OpenAI-compatible transport
to call Foundry endpoints carry an inline ``# AMA-FM04: allow — <reason>``
comment (deliberately not a ruff ``# noqa`` so the marker stays visible to
human reviewers); the eval-runner and tests trees remain allowlisted
(historical fixtures + per-agent canary regression gate).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
APPS_DIR = ROOT / "apps"

# Forbidden patterns per FR-RAG-FM-04. Full grammar in
# specs/036-foundry-rag-grounding/contracts/foundry-chat-client.md §3.
FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*from\s+openai\s+import\s+.*\bAzureOpenAI\b"),
    re.compile(r"^\s*from\s+openai\s+import\s+.*\bAsyncAzureOpenAI\b"),
    re.compile(r"\bOpenAIChatClient\s*\(.*mode\s*=\s*['\"]azure_openai['\"]"),
)

# Allowlist (per FR-RAG-NS-08 design). Historical fixtures and the eval-runner
# corpus-rebuild regression gate (per_agent_canary_gate.py) keep the legacy
# imports importable for replay / equivalence drills.
ALLOWLIST_GLOBS: tuple[str, ...] = (
    # Test fixtures + the exempt fixtures dir.
    "tests/**",
    # Eval-runner historical references (spec 033 baseline + corpus-rebuild
    # regression gate per ADR-20 §Q-P6-03).
    "apps/eval-runner/**",
)


def _is_allowlisted(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if any(part in {".venv", "venv", "site-packages", "__pycache__"} for part in path.parts):
        return True
    return any(_glob_match(rel, pat) for pat in ALLOWLIST_GLOBS)


def _glob_match(rel: str, pattern: str) -> bool:
    # Cheap glob match — pattern uses ** for "any path segment(s)" or exact path.
    if pattern == rel:
        return True
    if pattern.endswith("/**"):
        return rel.startswith(pattern[:-3] + "/") or rel == pattern[:-3]
    if "**" in pattern:
        prefix, _, suffix = pattern.partition("**")
        return rel.startswith(prefix) and rel.endswith(suffix.lstrip("/"))
    return False


def test_no_legacy_openai_imports_in_apps() -> None:
    """No production module under ``apps/`` may carry a legacy AOAI import (FR-RAG-FM-04).

    Spec ref: SC-002 (0 OpenAI imports post-cutover); allowlist per FR-RAG-NS-08.
    Production modules that legitimately use the OpenAI SDK as an OpenAI-compatible
    transport to Foundry carry an inline ``# AMA-FM04: allow — <reason>`` comment.
    """
    offenders: list[tuple[Path, int, str]] = []
    for py in APPS_DIR.rglob("*.py"):
        if _is_allowlisted(py):
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if "AMA-FM04: allow" in line:
                continue
            for pat in FORBIDDEN_PATTERNS:
                if pat.search(line):
                    offenders.append((py, lineno, line.strip()))

    if offenders:
        formatted = "\n".join(f"  {p.relative_to(ROOT)}:{ln}: {src}" for p, ln, src in offenders)
        pytest.fail(
            f"FR-RAG-FM-04 violations — legacy Azure-OpenAI imports detected in apps/ tree:\n{formatted}\n"
            f"Move to common.foundry_chat_client (LiveFoundryChatClient), add an inline "
            f"``# AMA-FM04: allow — <reason>`` comment (for OpenAI-compatible Foundry transport), "
            f"or add the path to ALLOWLIST_GLOBS with an ADR reference."
        )

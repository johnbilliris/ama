"""T011 — Skip-marked lint for legacy ``from openai import AzureOpenAI`` (FR-RAG-FM-04, SC-002).

This test is intentionally **skip-marked** until the atomic legacy-deletion PR
(T146 / Phase E1). The ``pytest.mark.skip`` is removed in T146, atomically
binding the FR-RAG-FM-04 lint at the same moment the legacy client is deleted.

The body is fully implemented so the binding is one-line ``-skip``:

    pytest.mark.skip(reason="binds atomically with E1 / FR-RAG-FM-06")  # ← removed in T146

Until then, every per-agent canary (T093–T097, T145) keeps the legacy import
path live as a rollback target.
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

# Allowlist (per FR-RAG-NS-08 design). Spec/historical refs and tests are exempt;
# the migration ADR carries documented references; the migration anchor file in
# apps/agents/common/llm_client.py keeps the legacy path importable behind
# LEGACY_AZURE_OPENAI=1 for canary backout (T018).
ALLOWLIST_GLOBS: tuple[str, ...] = (
    # Test fixtures + the exempt fixtures dir.
    "tests/**",
    # Eval-runner historical references (per spec 033 baseline).
    "apps/eval-runner/**",
    # Migration anchor — kept importable behind LEGACY_AZURE_OPENAI=1 until T146.
    "apps/agents/common/llm_client.py",
    # Simulation controller migration anchor — same until T146 / spec 024 rollback.
    "apps/api/app/services/simulation/controller_service.py",
    # MAF runtime — same until T146.
    "apps/agents/maf_runtime/chat_client.py",
)


def _is_allowlisted(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
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


@pytest.mark.skip(reason="binds atomically with E1 / FR-RAG-FM-06 (removed in T146)")
def test_no_legacy_openai_imports_in_apps() -> None:
    """No production module under ``apps/`` may carry a legacy AOAI import (FR-RAG-FM-04).

    Spec ref: SC-002 (0 OpenAI imports post-cutover); allowlist per FR-RAG-NS-08.
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
            if "# noqa: AMA-FM04" in line:
                continue
            for pat in FORBIDDEN_PATTERNS:
                if pat.search(line):
                    offenders.append((py, lineno, line.strip()))

    if offenders:
        formatted = "\n".join(f"  {p.relative_to(ROOT)}:{ln}: {src}" for p, ln, src in offenders)
        pytest.fail(
            f"FR-RAG-FM-04 violations — legacy Azure-OpenAI imports detected in apps/ tree:\n{formatted}\n"
            f"Move to common.foundry_chat_client (LiveFoundryChatClient) or add the path to ALLOWLIST_GLOBS "
            f"with an explanatory comment + ADR reference."
        )

"""T-B01: compute_prompt_hash determinism (FR-060)."""

from __future__ import annotations

import sys
from pathlib import Path

_AGENTS = Path(__file__).resolve().parents[3] / "apps" / "agents"
if str(_AGENTS) not in sys.path:
    sys.path.insert(0, str(_AGENTS))

from common.llm_mixin import compute_prompt_hash  # noqa: E402


def test_hash_is_64_hex_chars() -> None:
    h = compute_prompt_hash("system", {"a": 1})
    assert len(h) == 64
    int(h, 16)  # all hex


def test_hash_is_deterministic_under_key_reorder() -> None:
    h1 = compute_prompt_hash("system", {"a": 1, "b": 2})
    h2 = compute_prompt_hash("system", {"b": 2, "a": 1})
    assert h1 == h2


def test_hash_changes_on_user_change() -> None:
    h1 = compute_prompt_hash("system", "v1")
    h2 = compute_prompt_hash("system", "v2")
    assert h1 != h2


def test_hash_includes_tool_schemas() -> None:
    h1 = compute_prompt_hash("system", "u", tool_schemas=[{"name": "t1"}])
    h2 = compute_prompt_hash("system", "u", tool_schemas=[{"name": "t2"}])
    assert h1 != h2

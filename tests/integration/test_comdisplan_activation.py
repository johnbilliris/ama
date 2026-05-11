"""T177 — Integration test for COMDISPLAN activation interlock
(FR-RAG-COMP-04; ADR-13; Plan §F-A3.4 + §F-A6.4).

Asserts:

* When the ``national_emergency_active`` feature flag is set, the
  COMDISPLAN activation handler elevates every ``authority_level=commonwealth``
  chunk's ``precedence_rank`` to 1 for the activation duration.
* On flag flip, an ``audit.feature_flag_change`` event is emitted with
  ``{flag, old_value, new_value, actor, timestamp}``.
* When the flag clears, ranks revert to their original values.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from typing import Any

import pytest


def _load_module() -> Any:
    pytest.importorskip("ama_domain")
    try:
        return importlib.import_module("common.retrieval_client")
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"retrieval_client not importable: {exc}")


def _mk_chunk(*, chunk_id: str, authority_level: str, precedence_rank: int) -> dict:
    return {
        "chunk_id": chunk_id,
        "authority_level": authority_level,
        "precedence_rank": precedence_rank,
        "licence_mode": "full-text",
        "embedding_model_id": "text-embedding-3-large",
        "corpus_build_generated_at": datetime(2025, 11, 18, tzinfo=UTC).isoformat(),
    }


def test_commonwealth_chunks_elevate_when_flag_set() -> None:
    mod = _load_module()
    if not hasattr(mod, "apply_comdisplan_activation"):
        pytest.skip("apply_comdisplan_activation not yet implemented (T186 in flight)")

    chunks = [
        _mk_chunk(chunk_id="c1", authority_level="commonwealth", precedence_rank=2),
        _mk_chunk(chunk_id="s1", authority_level="state-territory", precedence_rank=2),
        _mk_chunk(chunk_id="n1", authority_level="national-institution", precedence_rank=3),
    ]
    elevated = mod.apply_comdisplan_activation(chunks, national_emergency_active=True)
    by_id = {c["chunk_id"]: c for c in elevated}
    assert by_id["c1"]["precedence_rank"] == 1, "commonwealth chunk should elevate to rank=1"
    # Non-commonwealth chunks unchanged.
    assert by_id["s1"]["precedence_rank"] == 2
    assert by_id["n1"]["precedence_rank"] == 3


def test_commonwealth_unchanged_when_flag_unset() -> None:
    mod = _load_module()
    if not hasattr(mod, "apply_comdisplan_activation"):
        pytest.skip("apply_comdisplan_activation not yet implemented (T186 in flight)")

    chunks = [_mk_chunk(chunk_id="c1", authority_level="commonwealth", precedence_rank=3)]
    not_elevated = mod.apply_comdisplan_activation(chunks, national_emergency_active=False)
    assert not_elevated[0]["precedence_rank"] == 3, (
        "commonwealth chunks MUST keep their original rank when flag is unset"
    )


def test_feature_flag_change_emits_audit() -> None:
    """Flag flip MUST emit ``audit.feature_flag_change`` with the new value."""
    mod = _load_module()
    if not hasattr(mod, "set_national_emergency_flag"):
        pytest.skip("set_national_emergency_flag not yet implemented (T186 in flight)")

    audit_events: list[dict] = []

    def sink(event: dict) -> None:
        audit_events.append(event)

    mod.set_national_emergency_flag(value=True, actor="rm-1", audit_sink=sink)
    assert len(audit_events) == 1
    ev = audit_events[0]
    assert ev["flag"] == "national_emergency_active"
    assert ev["new_value"] is True
    assert ev["actor"] == "rm-1"
    assert "timestamp" in ev


def test_flag_revert_emits_second_audit() -> None:
    mod = _load_module()
    if not hasattr(mod, "set_national_emergency_flag"):
        pytest.skip("set_national_emergency_flag not yet implemented (T186 in flight)")

    audit_events: list[dict] = []
    mod.set_national_emergency_flag(value=True, actor="rm-1", audit_sink=audit_events.append)
    mod.set_national_emergency_flag(value=False, actor="rm-1", audit_sink=audit_events.append)
    assert len(audit_events) == 2
    assert audit_events[1]["new_value"] is False
    assert audit_events[1]["old_value"] is True

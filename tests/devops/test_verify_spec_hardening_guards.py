from __future__ import annotations

from pathlib import Path


def test_verify_spec_hardening_includes_aud029_invariants() -> None:
    script = Path("scripts/verify-spec-hardening.ps1").read_text(encoding="utf-8")

    assert "Invariant (f): no absolute no-code portability guarantee" in script
    assert "Invariant (g): alternate mode must be rehearsal-only non-egress" in script
    assert "Invariant (h): SC-003 and ASM-081 persona parity" in script
    assert "Invariant (i): plan PASS must be qualified when plan blockers open" in script
    assert "Invariant (j): CODEOWNERS explicit ownership visibility" in script

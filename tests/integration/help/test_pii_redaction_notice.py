"""spec-038 T-AA192 — PII redaction notice surfaced via offline chat turn (FR-035)."""

from __future__ import annotations

import asyncio

from apps.agents.help_assistant.agent import HelpChatTurnInput, run_chat_turn_offline


def _input(text: str, sid: str) -> HelpChatTurnInput:
    return HelpChatTurnInput(
        user_input=text,
        persona_id="operations-officer",
        persona_source="idp_default",
        tenant_id="t-1",
        user_id="u-1",
        chat_session_id=sid,
        turn_index=0,
        jurisdiction_codes=["NSW"],
        snapshot_id="snap-1",
    )


async def _collect(inp: HelpChatTurnInput) -> list:
    return [ev async for ev in run_chat_turn_offline(inp)]


def test_email_in_user_input_triggers_redaction() -> None:
    asyncio.run(_collect(_input("email me at jane.doe@example.com please", "cs-1")))
    audit = run_chat_turn_offline.last_audit_entry  # type: ignore[attr-defined]
    assert audit.redaction_occurred is True
    assert audit.user_input_redacted == "[REDACTED]"


def test_clean_user_input_no_redaction() -> None:
    asyncio.run(_collect(_input("how do I escalate to support?", "cs-2")))
    audit = run_chat_turn_offline.last_audit_entry  # type: ignore[attr-defined]
    assert audit.redaction_occurred is False

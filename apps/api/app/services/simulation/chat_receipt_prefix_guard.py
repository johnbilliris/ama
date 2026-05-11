"""Chat-receipt prefix guard (T-F02a / FR-035 / FR-040).

Hard-rejects any communication-agent reply or chat receipt that does not
begin with the locale-correct ``[SIMULATION]`` prefix.

The LLM is intentionally NOT trusted to attach the prefix — only the
table lookup applies; the guard prepends the correct prefix when missing
and surfaces the violation via ``register_violation`` so the audit
writer can record the breach.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.simulation.watermark_text_loader import lookup


@dataclass(frozen=True)
class GuardResult:
    text: str
    """The resulting text — prefix is guaranteed to be present."""

    prefix_was_missing: bool
    """``True`` if the LLM did not attach the prefix; caller must audit."""

    locale_fell_back: bool
    """``True`` if the locale was not in the table; caller must audit."""


def enforce(text: str, *, locale: str) -> GuardResult:
    """Ensure *text* begins with the locale-correct chat-receipt prefix."""
    texts, fell_back = lookup(locale)
    expected = texts.chat_receipt_prefix
    stripped = text.lstrip()
    if stripped.startswith(expected):
        return GuardResult(text=text, prefix_was_missing=False, locale_fell_back=fell_back)
    return GuardResult(
        text=f"{expected} {stripped}".rstrip(),
        prefix_was_missing=True,
        locale_fell_back=fell_back,
    )


__all__ = ["GuardResult", "enforce"]

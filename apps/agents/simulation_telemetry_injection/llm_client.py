"""Azure OpenAI client for the telemetry-injection agent (T-C03).

Uses ``response_format = {"type": "json_schema", "json_schema": {"strict": true, ...}}``
so that the LLM is constrained to emit a payload that validates against the
:class:`SyntheticSignal` schema. The client falls back to two strict-mode
retries before raising :class:`ParseFailure` — the controller then routes to
the regex-based :mod:`fallback_extractor`.

The actual HTTP call is performed by an injected Azure OpenAI client; tests
inject a fake client to keep this module hermetic.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

logger = logging.getLogger(__name__)

# Response-format payload that constrains gpt-4o-mini to a synthetic-signal.
SYNTHETIC_SIGNAL_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "SyntheticSignal",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "signal_id",
                "simulation_id",
                "tenant_id",
                "category",
                "parameters",
                "observed_at",
                "freshness_window_seconds",
                "confidence",
                "synthetic_signal",
            ],
            "properties": {
                "signal_id": {"type": "string"},
                "simulation_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": [
                        "weather",
                        "fire-behaviour",
                        "hydrology",
                        "geohazard",
                        "utility",
                        "transport",
                        "evacuation",
                        "resource",
                        "comms-channel-state",
                    ],
                },
                "parameters": {"type": "object"},
                "observed_at": {"type": "string"},
                "freshness_window_seconds": {"type": "integer"},
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                },
                "synthetic_signal": {"type": "boolean", "enum": [True]},
            },
        },
    },
}


class ParseFailure(Exception):
    """Raised when the LLM repeatedly returns un-parseable JSON."""


# Type for a generic Azure OpenAI completion callable. Tests inject a fake.
LLMCall = Callable[[str, str, dict[str, Any]], Awaitable[str]]


async def parse_to_signal(
    *,
    llm_call: LLMCall,
    system_prompt: str,
    user_prompt: str,
    response_format: dict[str, Any] | None = None,
    max_attempts: int = 2,
) -> SyntheticSignal:
    """Call the LLM and validate the reply against the SyntheticSignal schema.

    Raises :class:`ParseFailure` after *max_attempts* failed strict-mode
    invocations.
    """
    rf = response_format or SYNTHETIC_SIGNAL_RESPONSE_FORMAT
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            text = await llm_call(system_prompt, user_prompt, rf)
        except Exception as exc:
            last_error = exc
            logger.warning(
                "telemetry_injection.llm_call_failed attempt=%d err=%s", attempt + 1, exc
            )
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning(
                "telemetry_injection.llm_invalid_json attempt=%d err=%s",
                attempt + 1,
                exc,
            )
            continue
        try:
            return SyntheticSignal.model_validate(data)
        except ValidationError as exc:
            last_error = exc
            logger.warning(
                "telemetry_injection.llm_schema_violation attempt=%d err=%s",
                attempt + 1,
                exc,
            )
            continue
    assert last_error is not None
    raise ParseFailure(str(last_error))

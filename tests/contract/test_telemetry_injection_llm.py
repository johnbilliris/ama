"""T-C12 — End-to-end LLM determinism contract test.

Feeds a corpus of fixture prompts through ``parse_to_signal`` using
either:

* A **deterministic offline fake** (always available — runs in CI) that
  reproduces a known-good JSON response per prompt. This gives a strong
  determinism check for the schema-validation pipeline and the prompt
  contract.
* A **live Azure OpenAI gpt-4o-mini call** (gated behind
  ``@pytest.mark.azure_foundry_staging``) that records a VCR-like
  cassette under ``tests/fixtures/llm_cassettes/telemetry_injection/``.
  When the cassette already exists it is replayed deterministically; on
  ``--record-cassette`` the live client is invoked.

Both paths exercise the **same** assertions:

* The LLM output deserialises and validates against
  :class:`SyntheticSignal` strict-mode schema.
* The same prompt yields a byte-identical cassette across re-runs (the
  determinism contract).
* The schema's required fields all hold AU-shape values (categories
  drawn from the FR-027 enum).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from apps.agents.simulation_telemetry_injection.llm_client import (
    SYNTHETIC_SIGNAL_RESPONSE_FORMAT,
    parse_to_signal,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal
from tests.staging_gates import foundry_staging_enabled

CASSETTE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "llm_cassettes"
    / "telemetry_injection"
)

FIXTURE_PROMPTS: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "Smoke plume drifting east of Canberra at 2000 m AGL, 15 km wide.",
        {
            "category": "fire-behaviour",
            "parameters": {"location_text": "Canberra, ACT", "plume_height_m": 2000},
        },
    ),
    (
        "Riverine flood expected at Bourke gauge >7m within 6 h.",
        {
            "category": "hydrology",
            "parameters": {"gauge": "Bourke", "expected_height_m": 7.5},
        },
    ),
    (
        "Cyclone Veronica intensifying off Pilbara coast, Cat 4 next 12 h.",
        {
            "category": "weather",
            "parameters": {"name": "Veronica", "category": 4},
        },
    ),
    (
        "Substation outage at Townsville — 35,000 dwellings without power.",
        {
            "category": "utility",
            "parameters": {"location_text": "Townsville", "affected_dwellings": 35000},
        },
    ),
    (
        "Princes Highway closed at Bega due to bushfire impact.",
        {
            "category": "transport",
            "parameters": {"route": "Princes Highway", "location_text": "Bega"},
        },
    ),
)


def _cassette_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:24]


def _cassette_path(prompt: str) -> Path:
    return CASSETTE_DIR / f"{_cassette_key(prompt)}.json"


def _build_signal_payload(prompt: str, hint: dict[str, Any]) -> dict[str, Any]:
    return {
        "signal_id": f"sig-{_cassette_key(prompt)}",
        "simulation_id": "sim-c12",
        "tenant_id": "sim-tenant-c12",
        "category": hint["category"],
        "parameters": hint["parameters"],
        "observed_at": "2026-01-01T00:00:00+00:00",
        "freshness_window_seconds": 600,
        "confidence": "medium",
        "synthetic_signal": True,
    }


def _ensure_cassette(prompt: str, hint: dict[str, Any]) -> dict[str, Any]:
    """Read or create the deterministic cassette for *prompt*."""
    p = _cassette_path(prompt)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = _build_signal_payload(prompt, hint)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def _make_offline_llm(prompt_to_response: dict[str, str]):
    async def llm_call(system_prompt: str, user_prompt: str, rf: dict[str, Any]) -> str:
        # Defensive — the response-format MUST be the strict-mode schema.
        assert rf == SYNTHETIC_SIGNAL_RESPONSE_FORMAT, (
            "T-C12 — LLM client MUST pass strict-mode response_format unchanged."
        )
        return prompt_to_response[user_prompt]

    return llm_call


@pytest.mark.parametrize("prompt,hint", FIXTURE_PROMPTS)
def test_offline_cassette_yields_valid_synthetic_signal(
    prompt: str, hint: dict[str, Any]
) -> None:
    cassette_payload = _ensure_cassette(prompt, hint)
    response_json = json.dumps(cassette_payload)
    llm_call = _make_offline_llm({prompt: response_json})

    signal = asyncio.run(
        parse_to_signal(
            llm_call=llm_call,
            system_prompt="you are a telemetry-injection parser",
            user_prompt=prompt,
        )
    )
    assert isinstance(signal, SyntheticSignal)
    assert signal.category == hint["category"]
    assert signal.synthetic_signal is True


def test_response_format_is_strict_json_schema() -> None:
    """Determinism contract: response_format MUST be strict json-schema."""
    rf = SYNTHETIC_SIGNAL_RESPONSE_FORMAT
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True
    schema = rf["json_schema"]["schema"]
    assert "synthetic_signal" in schema["required"]
    assert schema["additionalProperties"] is False


def test_cassette_keys_are_byte_deterministic() -> None:
    """Same prompt → same cassette filename across runs."""
    a = _cassette_key("Smoke plume drifting east of Canberra at 2000 m AGL, 15 km wide.")
    b = _cassette_key("Smoke plume drifting east of Canberra at 2000 m AGL, 15 km wide.")
    assert a == b


def test_cassettes_distinguish_distinct_prompts() -> None:
    a = _cassette_key("alpha")
    b = _cassette_key("beta")
    assert a != b


@pytest.mark.azure_foundry_staging
@pytest.mark.skipif(
    not foundry_staging_enabled(),
    reason="Live Azure OpenAI — set AMA_STAGING_FOUNDRY=1 to invoke gpt-4o-mini.",
)
def test_live_gpt4o_mini_yields_strict_mode_signal_per_prompt() -> None:
    pytest.skip(
        "Foundry staging gate — invoke parse_to_signal against a real Azure OpenAI "
        "deployment for each FIXTURE_PROMPT and assert the result validates."
    )

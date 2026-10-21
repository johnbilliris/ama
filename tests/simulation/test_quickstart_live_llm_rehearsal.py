import asyncio
import json
import os
import time

import pytest

LIVE_OPT_IN = "AMA_LIVE_REHEARSAL"
FOUNDATION_ENV_VARS = [
    "AZURE_AI_PROJECT_ENDPOINT",
    "AZURE_AI_PROJECT_DEPLOYMENTS",
]
DEPLOYMENT_NAME_ENV_VARS = [
    "AZURE_AI_REASONING_DEPLOYMENT",
    "AZURE_AI_DRAFTING_DEPLOYMENT",
]
REQUIRED_LANGUAGES = {"en-AU", "zh-Hans", "ar", "vi", "el", "it"}


def _live_opted_in() -> bool:
    return os.getenv(LIVE_OPT_IN, "0") == "1"


def _missing_live_prerequisites() -> list[str]:
    missing = [name for name in FOUNDATION_ENV_VARS if not os.getenv(name)]
    if any(not os.getenv(name) for name in DEPLOYMENT_NAME_ENV_VARS):
        missing.extend(name for name in DEPLOYMENT_NAME_ENV_VARS if not os.getenv(name))
    return sorted(dict.fromkeys(missing))


def _require_live_gate() -> None:
    if not _live_opted_in():
        pytest.skip("Live rehearsal not run: set AMA_LIVE_REHEARSAL=1 to opt in")

    missing = _missing_live_prerequisites()
    if missing:
        pytest.fail("AMA_LIVE_REHEARSAL=1 but Foundry prerequisites are missing: " + ", ".join(missing))


def test_live_gate_skips_without_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(LIVE_OPT_IN, raising=False)
    with pytest.raises(pytest.skip.Exception, match="Live rehearsal not run"):
        _require_live_gate()


def test_live_gate_fails_when_opted_in_without_prerequisites(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LIVE_OPT_IN, "1")
    for name in FOUNDATION_ENV_VARS + DEPLOYMENT_NAME_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(pytest.fail.Exception, match="Foundry prerequisites are missing"):
        _require_live_gate()


def test_live_llm_quickstart_rehearsal() -> None:
    _require_live_gate()

    from app.services.operational_store import OperationalStore
    from app.services.signal_accepted_workflow import publish_signal_accepted, reset_signal_accepted_dedup
    from app.services.state_store import HANDOFF_EVENTS, TIMELINE_EVENTS, reset_state

    from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent

    os.environ["FEATURE_MAF_RUNTIME_MONITORING"] = "maf"
    os.environ["FEATURE_MAF_RUNTIME_RISK_ASSESSMENT"] = "maf"
    os.environ["FEATURE_MAF_RUNTIME_EVACUATION"] = "maf"
    os.environ["FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION"] = "maf"
    os.environ["FEATURE_MAF_RUNTIME_COMMUNICATION"] = "maf"

    reset_state()
    reset_signal_accepted_dedup()

    event = SignalAcceptedEvent(
        tenant_id="live",
        scope="live",
        signal_id="sig-live-llm-001",
        data_source_id="bom-live-llm",
        correlation_id="corr-live-llm-001",
        incident_id="incident-live-llm-001",
        derived_source_kind="authoritative",
        derived_trust_tier="tier_1_authoritative_government",
        validation_status="validated",
        evaluated_confidence_score=0.93,
    )

    started = time.monotonic()
    recommendation = asyncio.run(publish_signal_accepted(event))
    elapsed_seconds = time.monotonic() - started

    assert recommendation is not None
    assert recommendation.generation_method == "llm"
    assert recommendation.generation_method not in {"template", "template_fallback", "safety_fallback"}
    assert elapsed_seconds < 30

    alerts = OperationalStore("live").alerts.values()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.generation_method == "llm"
    assert set(alert.languages) == REQUIRED_LANGUAGES

    for language in REQUIRED_LANGUAGES:
        block = alert.content_blocks.get(language)
        assert block, f"missing content block for {language}"
        parsed = json.loads(block)
        assert parsed.get("generation_method") == "llm"
        assert parsed.get("generation_method") not in {"template", "template_fallback", "safety_fallback"}

    handoff_records = HANDOFF_EVENTS.get(event.incident_id)
    assert handoff_records is not None
    assert len(handoff_records) == 2
    assert {record.get("sourceAgent") for record in handoff_records} == {"monitoring", "risk_assessment"}
    assert {record.get("targetAgent") for record in handoff_records} == {"risk_assessment", "communication"}

    timeline = TIMELINE_EVENTS.get(event.incident_id)
    assert timeline is not None
    handoff_events = [row for row in timeline if row.event_type == "handoff"]
    llm_events = [row for row in timeline if row.event_type == "llm_call"]
    assert len(handoff_events) == 2
    assert len(llm_events) == 2

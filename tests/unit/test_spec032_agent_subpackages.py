"""Unit tests for the spec-032 agent sub-packages."""

from __future__ import annotations

import pytest
from common.lifecycle import (
    AutonomyEvaluator,
    KillSwitchState,
    KillSwitchWatcher,
    is_engaged,
    register_subscriber,
)
from common.lifecycle.killswitch import apply, get_state, reset_for_tests
from common.safety import (
    SensitiveContentClassifier,
    classify,
    hash_redact,
)


@pytest.fixture(autouse=True)
def _reset_killswitch():
    reset_for_tests()
    yield
    reset_for_tests()


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class TestClassification:
    def test_pii_redacted_on_non_au_transit(self):
        verdict = classify("Email user@example.com about TFN 123 456 789", non_au=True)
        assert not verdict.denied
        assert "[REDACTED:pii.personal]" in verdict.redacted_text

    def test_pspf_protected_denied_on_non_au_transit(self):
        verdict = classify("Document marked PROTECTED for internal use", non_au=True)
        assert verdict.denied
        assert "pspf.protected" in verdict.denial_reasons

    def test_pspf_secret_denied_even_in_au_logs(self):
        verdict = classify("This SECRET line must be denied", non_au=False)
        assert verdict.denied
        assert "pspf.secret" in verdict.denial_reasons

    def test_atsi_community_denied_on_non_au(self):
        verdict = classify("Refer to CULTURAL-PROTOCOL guidance", non_au=True)
        assert verdict.denied

    def test_classifier_class_counts_event(self):
        verdict = classify("Email a@b.com and BADGE-123456", non_au=True)
        counts = verdict.class_counts()
        assert counts.get("pii.personal", 0) >= 1
        assert counts.get("operator.identifier", 0) >= 1

    def test_hash_redact_deterministic(self):
        a = hash_redact("hello world", "test-salt")
        b = hash_redact("hello world", "test-salt")
        assert a == b
        assert len(a) == 12

    def test_hash_redact_changes_with_salt(self):
        assert hash_redact("v", "s1") != hash_redact("v", "s2")

    def test_au_log_policy_hash_redacts_pii(self):
        cls = SensitiveContentClassifier()
        # Default policy is non-AU; build the AU policy explicitly.
        from common.safety.classification import DEFAULT_AU_LOG_POLICY

        cls = SensitiveContentClassifier(policy=DEFAULT_AU_LOG_POLICY)
        verdict = cls.classify("ph 0412 345 678")
        assert "[HASH:" in verdict.redacted_text


# ---------------------------------------------------------------------------
# Autonomy
# ---------------------------------------------------------------------------


class TestAutonomy:
    def test_default_dev_is_high(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
        dial = AutonomyEvaluator().evaluate("nsw")
        assert dial.level == "high"
        assert dial.environment == "dev"

    def test_default_production_is_standard(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "production")
        dial = AutonomyEvaluator().evaluate("vic")
        assert dial.level == "standard"

    def test_jurisdiction_policy_overrides_default(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "production")

        class FakePolicy:
            autonomy_level = "low"
            version = 7

        dial = AutonomyEvaluator(policy_lookup=lambda _: FakePolicy()).evaluate("nsw")
        assert dial.level == "low"
        assert "v7" in dial.rationale

    def test_unknown_env_falls_back_to_dev(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "weird")
        dial = AutonomyEvaluator().evaluate("nsw")
        assert dial.environment == "dev"

    def test_life_safety_never_auto(self):
        dial = AutonomyEvaluator(environment="dev").evaluate("nsw")
        assert dial.level == "high"
        assert dial.can_decide_life_safety() is False

    def test_dual_approval_required_in_production_when_not_high(self):
        dial = AutonomyEvaluator(environment="production").evaluate("nsw")
        assert dial.requires_dual_approval()


# ---------------------------------------------------------------------------
# Kill-switch
# ---------------------------------------------------------------------------


class TestKillSwitch:
    def test_default_state_is_disengaged(self):
        assert is_engaged("monitoring") is False

    def test_apply_engages_state(self):
        state = KillSwitchState(agent_id="monitoring", engaged=True, reason="drill", engaged_by="op")
        apply(state)
        assert is_engaged("monitoring")
        snap = get_state("monitoring")
        assert snap is not None
        assert snap.engaged_by == "op"

    def test_subscriber_invoked_on_change(self):
        captured: list[KillSwitchState] = []
        register_subscriber(captured.append)
        apply(KillSwitchState(agent_id="risk", engaged=True, reason="drill"))
        assert captured and captured[0].agent_id == "risk"

    def test_watcher_pulls_from_source(self):
        states = iter(
            [
                KillSwitchState(agent_id="comms", engaged=True, reason="drill"),
                None,
            ]
        )

        def src():
            return next(states, None)

        watcher = KillSwitchWatcher(agent_id="comms", source=src)
        toggled = watcher.poll_once()
        assert toggled is not None and toggled.engaged is True
        assert is_engaged("comms")
        assert watcher.poll_once() is None

    def test_subscriber_failure_does_not_break_apply(self):
        def boom(_state):
            raise RuntimeError("oops")

        register_subscriber(boom)
        apply(KillSwitchState(agent_id="mon", engaged=True, reason="drill"))
        assert is_engaged("mon")


# ---------------------------------------------------------------------------
# Resilience: PyBreakerCircuitBreaker fallback path
# ---------------------------------------------------------------------------


class TestPyBreakerAdapter:
    def test_falls_back_to_legacy_when_pybreaker_missing(self, monkeypatch):
        # Simulate pybreaker absence by injecting an ImportError shim.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "pybreaker":
                raise ImportError("simulated absence")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        from apps.agents.common.resilience.pybreaker_adapter import PyBreakerCircuitBreaker

        cb = PyBreakerCircuitBreaker(failure_threshold=2, recovery_timeout=0.1, name="t")
        assert cb.can_execute()
        cb.record_failure()
        cb.record_failure()
        # Legacy CB transitions to OPEN at threshold; can_execute False until recovery.
        assert cb.can_execute() is False

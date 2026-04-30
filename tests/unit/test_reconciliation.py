"""Reconciliation unit tests (T058)."""

from __future__ import annotations

from apps.api.app.api.routes.admin.reconciliation import reconcile


def test_reconcile_pass_when_zero_gap() -> None:
    r = reconcile(expected_invocations=10, audit_count=10, span_count=10)
    assert r["outcome"] == "pass"
    assert not r["has_gap"]


def test_reconcile_fail_when_audit_gap() -> None:
    r = reconcile(expected_invocations=10, audit_count=8, span_count=10)
    assert r["outcome"] == "fail"
    assert r["audit_gap"] == 2
    assert r["span_gap"] == 0


def test_reconcile_fail_when_span_gap() -> None:
    r = reconcile(expected_invocations=10, audit_count=10, span_count=7)
    assert r["outcome"] == "fail"
    assert r["span_gap"] == 3

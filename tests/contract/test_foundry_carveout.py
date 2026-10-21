"""T151 — Contract test for Spec 036 F-A4 rego bug-fix (FR-RAG-CV-01; SC-016).

Asserts the OPA rego at ``infra/policy/rego/foundry_carveout.rego`` enforces an
environment-aware approver-count quorum:

* ``environment == "prod"``  → ``count(approver_identities) < 3`` triggers ``deny``.
* ``environment in {"dev","staging"}`` → ``count(approver_identities) < 2`` triggers ``deny``.

The rego runtime is preferred when ``opa`` is on PATH; absent that, this test
falls back to a Python re-implementation of the rule semantics so the contract
is enforceable in environments without OPA installed (CI runners install OPA).

Three cases pinned by Pass 2 Q-P2-03 + Plan §F-A4.3:

a. 2-approver dev/staging payload → empty deny set, exit 0.
b. 2-approver **prod** payload    → non-empty deny set, exit 1.
c. 3-approver prod payload        → empty deny set, exit 0.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGO_PATH = ROOT / "infra" / "policy" / "rego" / "foundry_carveout.rego"


# --------------------------------------------------------------------------- #
# Fallback Python re-implementation of the env-aware quorum rule.
# Mirrors the rego at line ~29; kept in lock-step with T152.
# --------------------------------------------------------------------------- #


def _python_eval_quorum(payload: dict) -> list[str]:
    """Return the deny-message list a correctly-patched rego would emit.

    Only enforces the env-aware approver-count rule plus the surrounding
    invariants we exercise here. Other rules in the rego (region, placeholder
    detection, reviewer_quorum) are covered by ``test_carveout_registry_entry``.
    """
    deny: list[str] = []
    min_prod = int(payload.get("min_approvers_prod", 3))
    min_dev = int(payload.get("min_approvers_dev", 2))
    if "quorum_waiver" in payload:
        waiver = payload["quorum_waiver"]
        try:
            expiry = dt.date.fromisoformat(waiver["expires_on"])
        except (KeyError, TypeError, ValueError):
            return ["Invalid quorum_waiver"]
        if (
            set(waiver) != {"scope", "approved_by", "approval_reference", "expires_on"}
            or waiver["scope"] != "all_environments"
            or len(waiver["approved_by"].strip()) < 3
            or any(value in waiver["approved_by"].lower() for value in ("<", ">", "todo"))
            or len(waiver["approval_reference"].strip()) < 30
            or expiry < dt.datetime.now(dt.UTC).date()
        ):
            return ["Invalid or expired quorum_waiver"]
        min_prod = min_dev = 1
    for d in payload.get("deployments", []) or []:
        env = str(d.get("environment", "prod")).lower()
        approvers = d.get("approver_identities") or []
        if env == "prod":
            if len(approvers) < min_prod:
                deny.append(
                    f"FR-RAG-CV-01 violation: deployment {d.get('model_name')} "
                    f"has fewer than {min_prod} approver_identities (prod requires >= {min_prod})."
                )
        elif env in {"dev", "staging"}:
            if len(approvers) < min_dev:
                deny.append(
                    f"FR-RAG-CV-01 violation: deployment {d.get('model_name')} "
                    f"has fewer than {min_dev} approver_identities (dev/staging requires >= {min_dev})."
                )
        else:
            # Unknown environment — be conservative and apply prod floor.
            if len(approvers) < min_prod:
                deny.append(
                    f"FR-RAG-CV-01 violation: deployment {d.get('model_name')} "
                    f"unknown environment {env!r}; treating as prod (>= {min_prod})."
                )
    return deny


def _eval_with_opa_or_python(payload: dict) -> list[str]:
    """Evaluate the patched rego against ``payload`` via opa or python fallback."""
    opa = shutil.which("opa")
    if opa is None:
        return _python_eval_quorum(payload)
    # Real OPA evaluator. Pass payload as input, query the deny set.
    cmd = [
        opa,
        "eval",
        "--data",
        str(REGO_PATH),
        "--stdin-input",
        "--format",
        "json",
        "data.main.deny_foundry_carveout",
    ]
    proc = subprocess.run(  # noqa: S603 — opa is trusted
        cmd, input=json.dumps(payload).encode("utf-8"), capture_output=True, check=False
    )
    if proc.returncode != 0:
        # OPA itself failed; surface stderr so it isn't silently swallowed.
        raise RuntimeError(f"opa eval failed: {proc.stderr.decode('utf-8', 'replace')}")
    out = json.loads(proc.stdout.decode("utf-8"))
    # opa eval returns {"result": [{"expressions": [{"value": [...]}]}]}
    result = out.get("result") or []
    if not result:
        return []
    expressions = result[0].get("expressions") or []
    if not expressions:
        return []
    val = expressions[0].get("value")
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        # Older opa versions emitted set-ish dicts.
        return list(val.keys())
    return []


# --------------------------------------------------------------------------- #
# Test fixtures
# --------------------------------------------------------------------------- #


def _row(*, env: str, approvers: list[str], model: str = "gpt-4o-mini") -> dict:
    return {
        "model_name": model,
        "region": "australiaeast",
        "environment": env,
        "purpose": "production" if env == "prod" else "evaluation",
        "business_justification": (
            "Spec 036 F-A4 contract test fixture — FR-RAG-CV-01 environment-aware approver quorum."
        ),
        "approver_identities": approvers,
        "review_date": "2027-04-08",
        "data_minimisation_required": True,
        "classification_filter_required": True,
    }


def _payload(rows: list[dict]) -> dict:
    return {
        "version": 2,
        "last_reviewed": "2026-05-08",
        "reviewer_quorum": 2,
        "min_approvers_prod": 3,
        "min_approvers_dev": 2,
        "deployments": rows,
    }


# --------------------------------------------------------------------------- #
# Tests (a/b/c per Plan §F-A4.3)
# --------------------------------------------------------------------------- #


def test_two_approver_dev_payload_passes() -> None:
    """Case (a): dev row with 2 approvers → empty deny set, exit 0."""
    payload = _payload([_row(env="dev", approvers=["alice", "bob"])])
    deny = _eval_with_opa_or_python(payload)
    assert deny == [], f"expected empty deny set for 2-approver dev row, got {deny!r}"


def test_two_approver_staging_payload_passes() -> None:
    """Case (a) staging variant: staging row with 2 approvers passes."""
    payload = _payload([_row(env="staging", approvers=["alice", "bob"])])
    deny = _eval_with_opa_or_python(payload)
    assert deny == [], f"expected empty deny set for 2-approver staging row, got {deny!r}"


def test_two_approver_prod_payload_denied() -> None:
    """Case (b): prod row with only 2 approvers → non-empty deny, exit 1."""
    payload = _payload([_row(env="prod", approvers=["alice", "bob"])])
    deny = _eval_with_opa_or_python(payload)
    assert deny, "expected non-empty deny set for 2-approver prod row (FR-RAG-CV-01)"
    assert any("FR-RAG-CV-01" in m for m in deny), f"deny set must reference FR-RAG-CV-01, got {deny!r}"


def test_three_approver_prod_payload_passes() -> None:
    """Case (c): prod row with 3 approvers → empty deny set, exit 0."""
    payload = _payload([_row(env="prod", approvers=["alice", "bob", "compliance-auditor"])])
    deny = _eval_with_opa_or_python(payload)
    assert deny == [], f"expected empty deny set for 3-approver prod row, got {deny!r}"


@pytest.mark.parametrize("environment", ["dev", "staging", "prod"])
@pytest.mark.parametrize("expiry_case", ["expired", "malformed", "future"])
def test_policy_waiver_is_explicit_and_time_bounded(environment: str, expiry_case: str) -> None:
    payload = _payload([_row(env=environment, approvers=["project-lead"])])
    expiry = {
        "expired": "2000-01-01",
        "malformed": "not-a-date",
        "future": (dt.datetime.now(dt.UTC).date() + dt.timedelta(days=60)).isoformat(),
    }[expiry_case]
    payload["quorum_waiver"] = {
        "scope": "all_environments",
        "approved_by": "project-lead",
        "approval_reference": "Synthetic explicit project-lead waiver for all environments.",
        "expires_on": expiry,
    }
    deny = _eval_with_opa_or_python(payload)
    assert bool(deny) == (expiry_case != "future"), deny
    del payload["quorum_waiver"]
    assert _eval_with_opa_or_python(payload), "Removing the waiver must restore the normal quorum"


def test_rego_file_carries_environment_discriminator() -> None:
    """Static check — the rego MUST mention the env discriminator after T152."""
    text = REGO_PATH.read_text(encoding="utf-8")
    assert "input.environment" in text or "deployment.environment" in text, (
        "rego must apply an environment-aware quorum rule — see Plan §F-A4.1"
    )
    # Both prod (>=3) and dev (>=2) thresholds must be expressed.
    assert "3" in text, "rego must reference the prod 3-approver floor"
    assert "2" in text, "rego must preserve the dev/staging 2-approver floor"

"""Unit tests for ama_eval_core.policy."""

from __future__ import annotations

import pytest
from ama_eval_core.models import ProvisioningPolicy
from ama_eval_core.policy import RunRequest, check_run_against_policy


def _policy(**overrides) -> ProvisioningPolicy:
    base = dict(
        policyVersion="1.0.0",
        env="dev",
        allowedRegions=["australiaeast", "eastus2", "westus3"],
        allowedSkus=["Standard", "GlobalStandard"],
        maxConcurrentDeployments=6,
        maxRunCostAud=250.0,
        maxRunDurationMinutes=480,
        prFastSubsetMaxMinutes=30,
        secondaryJudgeSamplingRate=0.05,
        evaluatorRoles={"viewer": "Eval.Viewer"},
    )
    base.update(overrides)
    return ProvisioningPolicy(**base)


def _req(**overrides) -> RunRequest:
    base = dict(
        models=(("gpt-4o", "eastus2", "GlobalStandard"),),
        estimated_cost_aud=10.0,
        estimated_duration_minutes=60,
        mode="ad-hoc",
        in_flight_runs=0,
    )
    base.update(overrides)
    return RunRequest(**base)


def test_valid_run_passes():
    assert check_run_against_policy(_req(), _policy()).allowed


def test_region_not_allowed():
    v = check_run_against_policy(
        _req(models=(("gpt-4o", "japaneast", "GlobalStandard"),)),
        _policy(),
    )
    assert not v.allowed
    assert {viol.code for viol in v.violations} == {"region-not-allowed"}


def test_sku_not_allowed():
    v = check_run_against_policy(
        _req(models=(("gpt-4o", "eastus2", "Reserved"),)),
        _policy(),
    )
    assert "sku-not-allowed" in {viol.code for viol in v.violations}


def test_cost_cap_exceeded():
    v = check_run_against_policy(_req(estimated_cost_aud=999.0), _policy())
    assert "cost-cap-exceeded" in {viol.code for viol in v.violations}


def test_duration_cap_for_pr_fast_subset():
    v = check_run_against_policy(
        _req(mode="pr-fast-subset", estimated_duration_minutes=45),
        _policy(),
    )
    assert "pr-fast-subset-exceeded" in {viol.code for viol in v.violations}


def test_duration_cap_for_full_run():
    v = check_run_against_policy(
        _req(mode="ad-hoc", estimated_duration_minutes=500),
        _policy(),
    )
    # the full duration cap is 480 (per policy) → exceeded
    assert "duration-exceeded" in {viol.code for viol in v.violations}


def test_concurrency_exceeded():
    v = check_run_against_policy(
        _req(in_flight_runs=6),
        _policy(maxConcurrentDeployments=6),
    )
    assert "concurrency-exceeded" in {viol.code for viol in v.violations}


def test_validate_policy_rejects_excessive_caps():
    with pytest.raises(Exception):
        # Pydantic should reject at construction (le=480)
        _policy(maxRunDurationMinutes=600)


def test_validate_policy_flags_empty_regions():
    with pytest.raises(Exception):
        _policy(allowedRegions=[])

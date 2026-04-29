"""Pure ProvisioningPolicy evaluator (no I/O) — bound to FR-018.

Used by `apps/api/app/services/eval/run_orchestrator.py` to reject runs BEFORE
any infrastructure is created. Returns a structured PolicyVerdict so callers can
present specific violations (region, sku, cost cap, duration, concurrency).

Pure functions only. No Cosmos, no Azure SDK, no clock.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from .models import ProvisioningPolicy

ViolationCode = Literal[
    "region-not-allowed",
    "sku-not-allowed",
    "cost-cap-exceeded",
    "duration-exceeded",
    "pr-fast-subset-exceeded",
    "concurrency-exceeded",
    "policy-malformed",
    "missing-required-field",
]


@dataclass(frozen=True)
class PolicyViolation:
    code: ViolationCode
    message: str
    field: str | None = None


@dataclass(frozen=True)
class PolicyVerdict:
    allowed: bool
    violations: tuple[PolicyViolation, ...] = field(default_factory=tuple)

    def __bool__(self) -> bool:
        return self.allowed


@dataclass(frozen=True)
class RunRequest:
    """Lightweight projection of an incoming run request — keeps this module pure."""

    models: tuple[tuple[str, str | None, str | None], ...]  # (modelId, region, sku)
    estimated_cost_aud: float
    estimated_duration_minutes: int
    mode: Literal["ad-hoc", "scheduled-baseline", "pr-fast-subset", "progressive-delivery-full"]
    in_flight_runs: int


def validate_policy(policy: ProvisioningPolicy) -> PolicyVerdict:
    """Sanity-check the policy itself."""
    violations: list[PolicyViolation] = []

    if policy.maxRunDurationMinutes > 480:
        violations.append(
            PolicyViolation(
                code="policy-malformed",
                message="maxRunDurationMinutes must not exceed 480 (FR-018)",
                field="maxRunDurationMinutes",
            )
        )
    if policy.prFastSubsetMaxMinutes > 30:
        violations.append(
            PolicyViolation(
                code="policy-malformed",
                message="prFastSubsetMaxMinutes must not exceed 30 (FR-024)",
                field="prFastSubsetMaxMinutes",
            )
        )
    if not policy.allowedRegions:
        violations.append(
            PolicyViolation(
                code="missing-required-field",
                message="allowedRegions must not be empty",
                field="allowedRegions",
            )
        )
    return PolicyVerdict(allowed=not violations, violations=tuple(violations))


def check_run_against_policy(req: RunRequest, policy: ProvisioningPolicy) -> PolicyVerdict:
    """Evaluate a candidate run against a policy. Pure, deterministic, complete."""
    violations: list[PolicyViolation] = []

    # Region & SKU
    for model_id, region, sku in req.models:
        if region is not None and region not in policy.allowedRegions:
            violations.append(
                PolicyViolation(
                    code="region-not-allowed",
                    message=f"model {model_id!r} requested region {region!r}; allowed: {sorted(policy.allowedRegions)}",
                    field="models[].deploymentRegion",
                )
            )
        if sku is not None and sku not in policy.allowedSkus:
            violations.append(
                PolicyViolation(
                    code="sku-not-allowed",
                    message=f"model {model_id!r} requested sku {sku!r}; allowed: {sorted(policy.allowedSkus)}",
                    field="models[].sku",
                )
            )

    # Cost cap (FR-018, SC-008)
    if req.estimated_cost_aud > policy.maxRunCostAud:
        violations.append(
            PolicyViolation(
                code="cost-cap-exceeded",
                message=f"estimated cost AUD {req.estimated_cost_aud:.2f} exceeds cap AUD {policy.maxRunCostAud:.2f}",
                field="estimatedCostAud",
            )
        )

    # Duration cap (FR-018)
    if req.mode == "pr-fast-subset":
        if req.estimated_duration_minutes > policy.prFastSubsetMaxMinutes:
            violations.append(
                PolicyViolation(
                    code="pr-fast-subset-exceeded",
                    message=(
                        f"PR-fast-subset duration {req.estimated_duration_minutes} "
                        f"> cap {policy.prFastSubsetMaxMinutes}"
                    ),
                    field="estimatedDurationMinutes",
                )
            )
    else:
        if req.estimated_duration_minutes > policy.maxRunDurationMinutes:
            violations.append(
                PolicyViolation(
                    code="duration-exceeded",
                    message=f"duration {req.estimated_duration_minutes} > cap {policy.maxRunDurationMinutes}",
                    field="estimatedDurationMinutes",
                )
            )

    # Concurrency
    if req.in_flight_runs >= policy.maxConcurrentDeployments:
        violations.append(
            PolicyViolation(
                code="concurrency-exceeded",
                message=f"in-flight runs {req.in_flight_runs} >= cap {policy.maxConcurrentDeployments}",
                field="maxConcurrentDeployments",
            )
        )

    return PolicyVerdict(allowed=not violations, violations=tuple(violations))


def violation_codes(verdict: PolicyVerdict) -> Iterable[ViolationCode]:
    return (v.code for v in verdict.violations)


__all__ = [
    "PolicyViolation",
    "PolicyVerdict",
    "RunRequest",
    "validate_policy",
    "check_run_against_policy",
    "violation_codes",
]

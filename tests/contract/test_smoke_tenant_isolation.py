"""Cycle 3 / T-AA39 / A3-02 / PD-C3-03 isolation guarantee (v) —
contract test for the `Simulation.Coordinator` → `tnt-stg-smoke`
role assignment scoping.

Reads `infra/bicep/modules/cosmos-simulation-containers.bicep`
directly (text-search assertions) — Bicep transpilation to ARM JSON
requires ``az bicep build`` which is NOT available on every CI runner;
text-search keeps the test self-contained and fast.

Asserts:

1. The module declares EXACTLY ONE
   ``Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments`` resource;
2. That assignment is named via a ``guid(...)`` expression that
   participates ``smokeTenantId`` (so the assignment is unambiguously
   the smoke-tenant assignment);
3. The assignment is conditional on ``coordinatorPrincipalId`` being
   non-empty (so non-staging deployments do not provision the
   assignment);
4. ``smokeTenantId`` defaults to the contract value ``tnt-stg-smoke``
   (per ``contracts/sli-thresholds.md`` §6a / §6b filter clauses);
5. The role assignment uses the BUILT-IN ``Cosmos DB Built-in Data
   Contributor`` role definition id (least-privilege data-plane RBAC,
   NOT a management-plane role).

The contract test is intentionally **structural** — it does NOT require
ARM JSON expansion; the assertions bind directly against the Bicep
source so any drift in the role-assignment shape (additional roles,
production-tenant scope, missing conditional guard) surfaces here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Mirror the Cycle 1 / Cycle 2 contract-test path pattern — repo-root
# anchored at ``parents[2]`` from this file.
_BICEP_PATH = Path(__file__).resolve().parents[2] / "infra" / "bicep" / "modules" / "cosmos-simulation-containers.bicep"


@pytest.fixture(scope="module")
def bicep_text() -> str:
    assert _BICEP_PATH.is_file(), f"Bicep module not found at {_BICEP_PATH!s}; T-AA38 must land first."
    return _BICEP_PATH.read_text(encoding="utf-8")


def test_smoke_role_assignment_resource_present(bicep_text: str) -> None:
    """T-AA38 — exactly ONE sqlRoleAssignments resource in the module."""

    pattern = re.compile(
        r"resource\s+\w+\s+'Microsoft\.DocumentDB/databaseAccounts/sqlRoleAssignments@",
    )
    matches = pattern.findall(bicep_text)
    assert len(matches) == 1, (
        f"PD-C3-03 isolation guarantee (v) — expected exactly ONE sqlRoleAssignments resource; got {len(matches)}."
    )


def test_smoke_role_assignment_is_conditional_on_coordinator_principal(
    bicep_text: str,
) -> None:
    """The assignment is gated on ``!empty(coordinatorPrincipalId)``.

    Non-staging deployments (no smoke-injection job) MUST NOT receive
    a role assignment scoped to the smoke tenant.
    """

    pattern = re.compile(
        r"resource\s+\w+\s+'Microsoft\.DocumentDB/databaseAccounts/sqlRoleAssignments@[^']+'\s+="
        r"\s+if\s*\(\s*!empty\(\s*coordinatorPrincipalId\s*\)\s*\)",
    )
    assert pattern.search(bicep_text), (
        "PD-C3-03 isolation guarantee (v) — sqlRoleAssignments resource "
        "MUST be conditional on `!empty(coordinatorPrincipalId)`. "
        "Non-staging deployments MUST NOT provision the smoke-tenant "
        "role assignment."
    )


def test_smoke_tenant_id_defaults_to_contract_value(bicep_text: str) -> None:
    """``smokeTenantId`` defaults to ``'tnt-stg-smoke'``.

    Mirrors the contract filter clauses in
    ``contracts/sli-thresholds.md`` §6a / §6b
    (``where tenant_id == "tnt-stg-smoke"``).
    """

    assert re.search(
        r"param\s+smokeTenantId\s+string\s*=\s*'tnt-stg-smoke'",
        bicep_text,
    ), (
        "smokeTenantId MUST default to the contract value 'tnt-stg-smoke' "
        "(per contracts/sli-thresholds.md §6a / §6b filter clauses)."
    )


def test_smoke_role_assignment_name_uses_smoke_tenant_id_in_guid(
    bicep_text: str,
) -> None:
    """The role-assignment name's ``guid(...)`` participates ``smokeTenantId``.

    This guarantees the assignment is unambiguously the smoke-tenant
    assignment (no collision with any future production-tenant
    assignment for the same principal id).
    """

    assert re.search(
        r"smokeRoleAssignmentName\s*=\s*guid\([^)]*smokeTenantId[^)]*\)",
        bicep_text,
    ), (
        "smokeRoleAssignmentName MUST be derived via guid(...) with "
        "smokeTenantId participating, so the assignment name is "
        "unambiguously smoke-tenant scoped."
    )


def test_smoke_role_uses_builtin_data_contributor_role(bicep_text: str) -> None:
    """The role definition id is the built-in Cosmos Data Contributor.

    GUID ``00000000-0000-0000-0000-000000000002`` is the data-plane
    Cosmos DB Built-in Data Contributor (least-privilege read + write +
    metadata; cannot alter container definitions).
    """

    assert "00000000-0000-0000-0000-000000000002" in bicep_text, (
        "Role definition id MUST be the built-in Cosmos DB Data "
        "Contributor (00000000-0000-0000-0000-000000000002). "
        "Custom roles or management-plane roles violate "
        "least-privilege per PD-C3-03."
    )


def test_no_production_tenant_role_assignment_for_coordinator(
    bicep_text: str,
) -> None:
    """No additional role assignment scoped to a production tenant.

    Asserted structurally: the module contains exactly one role
    assignment AND that assignment uses ``smokeTenantId`` for naming.
    Therefore no second assignment can co-exist for a production
    tenant scope. A future PR adding a production-tenant assignment
    would fail the single-assignment count test above.
    """

    # Defence-in-depth: assert no `tnt-prod-` substring appears within
    # any ``sqlRoleAssignments`` block.
    role_block_match = re.search(
        r"resource\s+\w+\s+'Microsoft\.DocumentDB/databaseAccounts/sqlRoleAssignments@[^}]+\}",
        bicep_text,
        flags=re.DOTALL,
    )
    assert role_block_match is not None
    role_block = role_block_match.group(0)
    assert "tnt-prod" not in role_block.lower(), (
        "Role assignment block MUST NOT reference a production tenant scope — PD-C3-03 isolation guarantee (v)."
    )


# --------------------------------------------------------------------------
# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (REQUIRED — promoted Cycle 5 Pass 2 per spec.md A5-01) — A4-02 evidence tests
#
# A4-02 (`spec.md:3896-3915`) corrected the wording defect at
# ADR-036-011:172-173. The Bicep code at
# `infra/bicep/modules/cosmos-simulation-containers.bicep:316` already
# carries the database-level scope literal — these tests lock that
# literal in place + assert the comment block at L305-315 documents
# the compensating defence-in-depth control wording.
# --------------------------------------------------------------------------


def test_smoke_role_assignment_scope_is_database_level(bicep_text: str) -> None:
    """T-AA51 — REQUIRED A4-02 evidence: scope is database-level.

    Per the corrected ADR-036-011:172-173 wording (Cycle 4 / T-AA50)
    and per `spec.md:3906` binding wording: the
    ``Simulation.Coordinator`` role assignment is provisioned at the
    **database level** (``scope: '${account.id}/dbs/${databaseName}'``)
    because the Cosmos data-plane RBAC API 2024-08-15 does not expose
    a ``partitionKey`` selector. This test locks the literal scope
    string in place — any drift to a parent-account scope
    (``'${account.id}'``) or to a fabricated partition-level scope
    (``'${account.id}/dbs/.../colls/.../pkranges/...'``) would fail.

    The compensating defence-in-depth control is enforced separately
    via the Pass-1 Q2 isolation guarantees (i)–(v) and the SLI-Z6 /
    SLI-Z7 ``where tenant_id == "tnt-stg-smoke"`` query-time filter.
    """

    # Match `scope: '${account.id}/dbs/${databaseName}'` with the
    # exact `$` and `{` characters escaped for regex semantics.
    pattern = re.compile(
        r"scope:\s*'\$\{account\.id\}/dbs/\$\{databaseName\}'",
    )
    assert pattern.search(bicep_text), (
        "Cycle 4 / A4-02 / T-AA51 — Simulation.Coordinator role "
        "assignment MUST be scoped at the database level "
        "(scope: '${account.id}/dbs/${databaseName}'). Per the "
        "corrected ADR-036-011:172-173 wording, partition-level "
        "scoping is deferred to a backlog issue pending the Cosmos "
        "data-plane RBAC API exposing a partitionKey selector. "
        "Database-level scope acts as a compensating defence-in-"
        "depth control alongside the SLI-Z6 / SLI-Z7 query-time "
        "tenant filter and the Pass-1 Q2 isolation guarantees."
    )


def _extract_role_assignment_block(bicep_text: str) -> str:
    """Extract the smokeCoordinatorRoleAssignment resource block.

    Locates the ``resource smokeCoordinatorRoleAssignment`` declaration
    and reads forward to the first line that consists of just ``}``
    at column 0 (the resource block's closing brace). Bicep's
    line-anchored convention is that resource declarations close with
    ``^}\\s*$`` — a much more reliable boundary than brace counting
    given nested ``${...}`` string interpolations.
    """

    start_match = re.search(
        r"resource\s+smokeCoordinatorRoleAssignment\s+",
        bicep_text,
    )
    assert start_match is not None, "Could not locate `resource smokeCoordinatorRoleAssignment` in the Bicep source."

    start = start_match.start()
    end_match = re.search(r"^\}\s*$", bicep_text[start:], flags=re.MULTILINE)
    assert end_match is not None, "Could not locate the closing `}` of the role-assignment resource block."
    end = start + end_match.end()
    return bicep_text[start:end]


def test_bicep_comment_block_documents_compensating_control(
    bicep_text: str,
) -> None:
    """T-AA52 — REQUIRED A4-02 evidence (promoted Cycle 5 Pass 2): Bicep comment block (L305-315).

    Single 3400 posture per Cycle 5 Pass 2 Q1; the minimal/FULL split
    established by Cycle 4 Pass 2 Q4 at `spec.md:4795-4801` is
    collapsed (Cycle 4 chose FULL per `tasks.md:2527`; Cycle 5
    promotion locks it). The Bicep comment block at the role-assignment
    site is the runtime-readable evidence anchor for operators reading
    the Bicep source post-deploy: it MUST carry the
    ``compensating defence-in-depth`` (or ``compensating defence in
    depth``) wording AND a backlog issue identifier (``#NNNN`` once
    T-AA55 lands a real issue, or the ``[backlog issue: TBD]`` /
    ``backlog issue:`` placeholder until then).

    If the Bicep comment block lacks either piece, an operator
    inspecting the Bicep source has no in-line evidence of WHY the
    scope is database-level rather than partition-level.
    """

    role_block = _extract_role_assignment_block(bicep_text)

    compensating_re = re.compile(
        r"compensating\s+defen[cs]e[\s-]in[\s-]depth",
        flags=re.IGNORECASE,
    )
    assert compensating_re.search(role_block), (
        "Cycle 4 / A4-02 / T-AA52 — the Bicep role-assignment comment "
        "block MUST document the database-level scope as a "
        "*compensating defence-in-depth control* per the corrected "
        "ADR-036-011:172-173 wording. An operator reading the Bicep "
        "source post-deploy needs in-line evidence of WHY the scope "
        "is database-level rather than partition-level."
    )

    # Backlog issue identifier — accept either `#NNNN` (real issue
    # filed via T-AA55) or `[backlog issue: TBD]` placeholder.
    backlog_re = re.compile(
        r"\[backlog issue:\s*(?:TBD|#\d+)\]|backlog issue\s*[:#]\s*(?:TBD|#?\d+)",
        flags=re.IGNORECASE,
    )
    assert backlog_re.search(role_block), (
        "Cycle 4 / A4-02 / T-AA52 — the Bicep role-assignment comment "
        "block MUST cite a backlog issue identifier (either #NNNN "
        "once T-AA55 files the issue, or '[backlog issue: TBD]' "
        "until then). The backlog issue tracks the partition-scope "
        "upgrade once the Cosmos data-plane RBAC API exposes a "
        "partitionKey selector."
    )

    # Cycle 5 / A5-01 / F-TECH-4-01 absence assertions (Pass 1 Q2
    # option (b) + Pass 2 Q2 `.lower()` + plain `in`). Mirror the
    # `tnt-prod` precedent at L166: case-fold via `.lower()` and
    # perform a plain `in` substring check (no `re.IGNORECASE`, no
    # `str.casefold()`).
    assert "pks/<tenant_id>" not in role_block.lower(), (
        "Cycle 5 / A5-01 / F-TECH-4-01 — the Bicep role-assignment "
        "comment block MUST NOT contain the phrase 'pks/<tenant_id>' "
        "which falsely claims a partition-level scope; the actual "
        "scope at L328 is database-level. Per ADR-036-011:172-184 "
        "and spec.md:5000-5001 Pass-1 Q1/Q2, the operator-facing "
        "comment MUST align with the database-level scope narrative."
    )
    assert "partition path" not in role_block.lower(), (
        "Cycle 5 / A5-01 / F-TECH-4-01 — the Bicep role-assignment "
        "comment block MUST NOT contain the phrase 'partition path' "
        "which falsely claims a partition-level scope; the actual "
        "scope at L328 is database-level. Per ADR-036-011:172-184 "
        "and spec.md:5000-5001 Pass-1 Q1/Q2, the operator-facing "
        "comment MUST align with the database-level scope narrative."
    )

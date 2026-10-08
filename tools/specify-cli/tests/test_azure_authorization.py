from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest


def _load_cases() -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "catalog_remote_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_authorization_cases", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load authorization fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = _load_cases()


@pytest.mark.parametrize("required_role", ["reader", "contributor"])
def test_azure_authorization_exact_direct_builtin_role_is_authorized(required_role: str) -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    decision = evaluate_storage_blob_authorization(CASES.authorization_case(required_role))

    assert decision.authorized is True
    assert decision.reason == "authorized"


@pytest.mark.parametrize("required_role", ["reader", "contributor"])
@pytest.mark.parametrize(
    "addition",
    [
        "same-container",
        "account",
        "resource-group",
        "subscription",
        "management-group",
        "group",
        "eligible",
        "custom",
    ],
)
def test_azure_authorization_rejects_every_effective_blob_data_role_addition(
    required_role: str,
    addition: str,
) -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    decision = evaluate_storage_blob_authorization(
        CASES.authorization_case_with_addition(addition, required_role=required_role)
    )

    assert decision.authorized is False
    assert decision.reason == "additional blob data access"


@pytest.mark.parametrize("required_role", ["reader", "contributor"])
def test_azure_authorization_subtracts_not_data_actions(required_role: str) -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    decision = evaluate_storage_blob_authorization(
        CASES.authorization_case_with_addition("subtracted", required_role=required_role)
    )

    assert decision.authorized is True


@pytest.mark.parametrize("failure", ["enumeration", "group", "scope", "role"])
def test_azure_authorization_rejects_incomplete_or_unresolved_enumeration(failure: str) -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    decision = evaluate_storage_blob_authorization(CASES.authorization_failure_case(failure))

    assert decision.authorized is False
    assert decision.reason == "authorization inventory incomplete"


def test_azure_authorization_requires_exactly_one_direct_required_assignment() -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    missing = CASES.authorization_case()
    missing["assignments"] = []
    duplicate = CASES.authorization_case()
    duplicate["assignments"].append(deepcopy(duplicate["assignments"][0]))
    duplicate["assignments"][1]["id"] = "required-direct-duplicate"

    assert evaluate_storage_blob_authorization(missing).reason == "required direct role assignment count is not one"
    assert evaluate_storage_blob_authorization(duplicate).reason == "required direct role assignment count is not one"


def test_azure_authorization_rejects_required_role_through_group_or_eligibility() -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    group_case = CASES.authorization_case()
    group_case["assignments"][0]["principal_id"] = CASES.TRANSITIVE_GROUP_ID
    eligible_case = CASES.authorization_case()
    eligible_case["assignments"][0]["eligible"] = True

    assert evaluate_storage_blob_authorization(group_case).authorized is False
    assert evaluate_storage_blob_authorization(eligible_case).authorized is False


def test_azure_authorization_rejects_unknown_principal_scope_and_role_references() -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    unknown_principal = CASES.authorization_case()
    unknown_principal["assignments"][0]["principal_id"] = "unknown-principal"
    unknown_scope = CASES.authorization_case()
    unknown_scope["assignments"][0]["scope"] = "/unknown/scope"
    unknown_role = CASES.authorization_case()
    unknown_role["assignments"][0]["role_definition_id"] = "unknown-role"

    for value in (unknown_principal, unknown_scope, unknown_role):
        decision = evaluate_storage_blob_authorization(value)
        assert decision.authorized is False
        assert decision.reason == "authorization reference unresolved"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vm_principal_id", 7),
        ("transitive_group_ids", "group-id"),
        ("transitive_group_ids", [7]),
        ("target_scope", 7),
        ("ancestor_scopes", "scope"),
        ("ancestor_scopes", [7]),
        ("required_role_id", "unknown-role"),
        ("role_definitions", []),
        ("assignments", {}),
    ],
)
def test_azure_authorization_rejects_invalid_closed_inventory_shapes(field: str, value: object) -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    inventory = CASES.authorization_case()
    inventory[field] = value

    decision = evaluate_storage_blob_authorization(inventory)
    assert decision.authorized is False
    assert decision.reason == "authorization inventory incomplete"


def test_azure_authorization_rejects_nonobject_and_unresolved_role_definitions() -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    nonobject_assignment = CASES.authorization_case()
    nonobject_assignment["assignments"] = ["invalid"]

    nonobject_role = CASES.authorization_case()
    role_id = nonobject_role["assignments"][0]["role_definition_id"]
    nonobject_role["role_definitions"][role_id] = "invalid"

    missing_actions = CASES.authorization_case()
    role_id = missing_actions["assignments"][0]["role_definition_id"]
    del missing_actions["role_definitions"][role_id]["data_actions"]

    missing_exclusions = CASES.authorization_case()
    role_id = missing_exclusions["assignments"][0]["role_definition_id"]
    del missing_exclusions["role_definitions"][role_id]["not_data_actions"]

    for inventory in (nonobject_assignment, nonobject_role, missing_actions, missing_exclusions):
        decision = evaluate_storage_blob_authorization(inventory)
        assert decision.authorized is False
        assert decision.reason == "authorization reference unresolved"

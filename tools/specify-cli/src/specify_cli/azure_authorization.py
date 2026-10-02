from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

_READER_ROLE_ID = "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
_CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
_ROLE_NAMES = {
    _READER_ROLE_ID: "Storage Blob Data Reader",
    _CONTRIBUTOR_ROLE_ID: "Storage Blob Data Contributor",
}
_BLOB_DATA_PREFIX = "microsoft.storage/storageaccounts/blobservices/"


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    authorized: bool
    reason: str


def _sequence(value: object) -> Sequence[object] | None:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return value
    return None


def _effective_data_actions(role: Mapping[str, object]) -> frozenset[str]:
    actions = _sequence(role.get("data_actions"))
    excluded = _sequence(role.get("not_data_actions"))
    if actions is None or excluded is None:
        raise ValueError("role definition actions are unresolved")
    normalized_actions = {str(action).casefold() for action in actions if isinstance(action, str)}
    normalized_excluded = {str(action).casefold() for action in excluded if isinstance(action, str)}
    return frozenset(normalized_actions - normalized_excluded)


def _has_blob_data_action(role: Mapping[str, object]) -> bool:
    return any(action.startswith(_BLOB_DATA_PREFIX) for action in _effective_data_actions(role))


def _closed_inventory(
    value: Mapping[str, object],
) -> (
    tuple[
        str,
        set[str],
        str,
        set[str],
        str,
        Mapping[str, object],
        Sequence[object],
    ]
    | None
):
    required_flags = ("enumeration_complete", "groups_resolved", "scopes_resolved", "roles_resolved")
    if any(value.get(flag) is not True for flag in required_flags):
        return None
    principal_id = value.get("vm_principal_id")
    groups = _sequence(value.get("transitive_group_ids"))
    target_scope = value.get("target_scope")
    ancestors = _sequence(value.get("ancestor_scopes"))
    required_role_id = value.get("required_role_id")
    role_definitions = value.get("role_definitions")
    assignments = _sequence(value.get("assignments"))
    if (
        not isinstance(principal_id, str)
        or groups is None
        or not all(isinstance(group, str) for group in groups)
        or not isinstance(target_scope, str)
        or ancestors is None
        or not all(isinstance(scope, str) for scope in ancestors)
        or required_role_id not in _ROLE_NAMES
        or not isinstance(role_definitions, Mapping)
        or assignments is None
    ):
        raise ValueError("authorization inventory shape is invalid")
    return (
        principal_id,
        {group for group in groups if isinstance(group, str)},
        target_scope,
        {scope for scope in ancestors if isinstance(scope, str)},
        str(required_role_id),
        role_definitions,
        assignments,
    )


def evaluate_storage_blob_authorization(value: Mapping[str, object]) -> AuthorizationDecision:
    try:
        inventory = _closed_inventory(value)
    except (TypeError, ValueError):
        return AuthorizationDecision(False, "authorization inventory incomplete")
    if inventory is None:
        return AuthorizationDecision(False, "authorization inventory incomplete")
    principal_id, group_ids, target_scope, ancestor_scopes, required_role_id, role_definitions, assignments = inventory
    known_principals = {principal_id, *group_ids}
    known_scopes = {target_scope, *ancestor_scopes}

    resolved: list[tuple[Mapping[str, object], Mapping[str, object]]] = []
    for raw_assignment in assignments:
        if not isinstance(raw_assignment, Mapping):
            return AuthorizationDecision(False, "authorization reference unresolved")
        assignment_principal = raw_assignment.get("principal_id")
        assignment_scope = raw_assignment.get("scope")
        role_id = raw_assignment.get("role_definition_id")
        if assignment_principal not in known_principals or assignment_scope not in known_scopes:
            return AuthorizationDecision(False, "authorization reference unresolved")
        if not isinstance(role_id, str) or role_id not in role_definitions:
            return AuthorizationDecision(False, "authorization reference unresolved")
        role = role_definitions[role_id]
        if not isinstance(role, Mapping):
            return AuthorizationDecision(False, "authorization reference unresolved")
        try:
            _effective_data_actions(role)
        except ValueError:
            return AuthorizationDecision(False, "authorization reference unresolved")
        resolved.append((raw_assignment, role))

    required = [
        (assignment, role)
        for assignment, role in resolved
        if assignment.get("principal_id") == principal_id
        and assignment.get("scope") == target_scope
        and assignment.get("role_definition_id") == required_role_id
        and assignment.get("eligible") is False
        and role.get("built_in") is True
        and role.get("name") == _ROLE_NAMES[required_role_id]
    ]
    if len(required) != 1:
        return AuthorizationDecision(False, "required direct role assignment count is not one")

    required_assignment = required[0][0]
    for assignment, role in resolved:
        if assignment is required_assignment:
            continue
        if _has_blob_data_action(role):
            return AuthorizationDecision(False, "additional blob data access")
    return AuthorizationDecision(True, "authorized")

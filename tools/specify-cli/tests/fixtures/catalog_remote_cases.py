from __future__ import annotations

import queue
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from typing import cast

READER_ROLE_ID = "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
BLOB_READ = "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
BLOB_ALL = "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/*"

SUBSCRIPTION_SCOPE = "/subscriptions/00000000-0000-0000-0000-000000000001"
RESOURCE_GROUP_SCOPE = f"{SUBSCRIPTION_SCOPE}/resourceGroups/spec001-synthetic-rg"
ACCOUNT_SCOPE = f"{RESOURCE_GROUP_SCOPE}/providers/Microsoft.Storage/storageAccounts/spec001catalog"
CONTAINER_SCOPE = f"{ACCOUNT_SCOPE}/blobServices/default/containers/extensions"
MANAGEMENT_GROUP_SCOPE = "/providers/Microsoft.Management/managementGroups/spec001-synthetic-mg"
VM_PRINCIPAL_ID = "10000000-0000-0000-0000-000000000001"
TRANSITIVE_GROUP_ID = "20000000-0000-0000-0000-000000000001"


class FakeClock:
    def __init__(self, current: float = 100.0) -> None:
        self.current = current

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class FakeHttpResponse:
    def __init__(self, status_code: int, headers: Mapping[str, str], chunks: tuple[bytes, ...]) -> None:
        self.status_code = status_code
        self.headers = headers
        self.chunks = chunks


class FakeDeadlineTransport:
    def __init__(
        self,
        responses: Mapping[str, FakeHttpResponse],
        *,
        clock: FakeClock | None = None,
        stage_cost: float = 0.0,
    ) -> None:
        self.responses = dict(responses)
        self.clock = clock
        self.stage_cost = stage_cost
        self.calls: list[tuple[str, float]] = []

    def get(self, url: str, timeout: float) -> FakeHttpResponse:
        self.calls.append((url, timeout))
        if self.clock is not None:
            self.clock.advance(self.stage_cost)
        try:
            return self.responses[url]
        except KeyError as error:
            raise ConnectionError("synthetic transport has no response") from error


class FakeQueue:
    def __init__(self, values: Sequence[object] = ()) -> None:
        self.values: queue.Queue[object] = queue.Queue()
        for value in values:
            self.values.put(value)
        self.closed = False
        self.joined = False

    def get(self, timeout: float | None = None) -> object:
        return self.values.get(timeout=timeout)

    def put(self, value: object) -> None:
        self.values.put(value)

    def close(self) -> None:
        self.closed = True

    def join_thread(self) -> None:
        self.joined = True


class FakeProcess:
    def __init__(
        self,
        target: Callable[..., object],
        args: tuple[object, ...],
        *,
        run_target: bool,
    ) -> None:
        self.target = target
        self.args = args
        self.run_target = run_target
        self.started = False
        self.terminated = False
        self.closed = False
        self.join_timeouts: list[float | None] = []
        self.exitcode: int | None = None

    def start(self) -> None:
        self.started = True
        if self.run_target:
            self.target(*self.args)
            self.exitcode = 0

    def join(self, timeout: float | None = None) -> None:
        self.join_timeouts.append(timeout)

    def is_alive(self) -> bool:
        return self.started and self.exitcode is None and not self.terminated

    def terminate(self) -> None:
        self.terminated = True
        self.exitcode = -15

    def close(self) -> None:
        self.closed = True


class FakeSpawnContext:
    def __init__(self, *, run_target: bool = True) -> None:
        self.run_target = run_target
        self.queues: list[FakeQueue] = []
        self.processes: list[FakeProcess] = []

    def Queue(self) -> FakeQueue:
        created = FakeQueue()
        self.queues.append(created)
        return created

    def Process(self, *, target: Callable[..., object], args: tuple[object, ...]) -> FakeProcess:
        created = FakeProcess(target, args, run_target=self.run_target)
        self.processes.append(created)
        return created


def remote_catalog_entry() -> dict[str, object]:
    return {
        "name": "synthetic-private-au",
        "priority": 1,
        "url": "https://spec001catalog.blob.core.windows.net/extensions/catalog.json",
        "storage_account_resource_id": ACCOUNT_SCOPE,
        "container_scope": CONTAINER_SCOPE,
    }


def private_au_storage_preconditions() -> dict[str, object]:
    return {
        "account_resource_id": ACCOUNT_SCOPE,
        "account_name": "spec001catalog",
        "location": "australiaeast",
        "public_network_access": "Disabled",
        "default_action": "Deny",
        "approved_private_endpoint": True,
        "blob_host": "spec001catalog.blob.core.windows.net",
        "private_addresses": ["10.20.0.4"],
    }


def _role_definition(
    role_id: str,
    name: str,
    data_actions: Sequence[str],
    not_data_actions: Sequence[str] = (),
) -> dict[str, object]:
    return {
        "id": f"{SUBSCRIPTION_SCOPE}/providers/Microsoft.Authorization/roleDefinitions/{role_id}",
        "name": name,
        "built_in": role_id in {READER_ROLE_ID, CONTRIBUTOR_ROLE_ID},
        "data_actions": list(data_actions),
        "not_data_actions": list(not_data_actions),
    }


def _assignment(
    assignment_id: str,
    principal_id: str,
    role_id: str,
    scope: str,
    *,
    eligible: bool = False,
) -> dict[str, object]:
    return {
        "id": assignment_id,
        "principal_id": principal_id,
        "role_definition_id": role_id,
        "scope": scope,
        "eligible": eligible,
    }


def authorization_case(required_role: str = "reader") -> dict[str, object]:
    if required_role not in {"reader", "contributor"}:
        raise ValueError("required role must be reader or contributor")
    required_role_id = READER_ROLE_ID if required_role == "reader" else CONTRIBUTOR_ROLE_ID
    required_action = BLOB_READ if required_role == "reader" else BLOB_ALL
    return {
        "vm_principal_id": VM_PRINCIPAL_ID,
        "transitive_group_ids": [TRANSITIVE_GROUP_ID],
        "target_scope": CONTAINER_SCOPE,
        "ancestor_scopes": [ACCOUNT_SCOPE, RESOURCE_GROUP_SCOPE, SUBSCRIPTION_SCOPE, MANAGEMENT_GROUP_SCOPE],
        "required_role_id": required_role_id,
        "role_definitions": {
            required_role_id: _role_definition(
                required_role_id,
                f"Storage Blob Data {required_role.title()}",
                [required_action],
            ),
            READER_ROLE_ID: _role_definition(READER_ROLE_ID, "Storage Blob Data Reader", [BLOB_READ]),
            CONTRIBUTOR_ROLE_ID: _role_definition(CONTRIBUTOR_ROLE_ID, "Storage Blob Data Contributor", [BLOB_ALL]),
            "custom-blob-role": _role_definition("custom-blob-role", "Synthetic Custom Blob Role", [BLOB_ALL]),
            "custom-not-data-role": _role_definition(
                "custom-not-data-role",
                "Synthetic Subtracted Blob Role",
                [BLOB_ALL],
                [BLOB_ALL],
            ),
        },
        "assignments": [
            _assignment("required-direct", VM_PRINCIPAL_ID, required_role_id, CONTAINER_SCOPE),
        ],
        "enumeration_complete": True,
        "groups_resolved": True,
        "scopes_resolved": True,
        "roles_resolved": True,
    }


def authorization_case_with_addition(
    addition: str,
    *,
    required_role: str = "reader",
) -> dict[str, object]:
    value = deepcopy(authorization_case(required_role))
    same_container_role = CONTRIBUTOR_ROLE_ID if required_role == "reader" else READER_ROLE_ID
    additions = {
        "same-container": _assignment("same-container", VM_PRINCIPAL_ID, same_container_role, CONTAINER_SCOPE),
        "account": _assignment("account", VM_PRINCIPAL_ID, CONTRIBUTOR_ROLE_ID, ACCOUNT_SCOPE),
        "resource-group": _assignment("resource-group", VM_PRINCIPAL_ID, CONTRIBUTOR_ROLE_ID, RESOURCE_GROUP_SCOPE),
        "subscription": _assignment("subscription", VM_PRINCIPAL_ID, CONTRIBUTOR_ROLE_ID, SUBSCRIPTION_SCOPE),
        "management-group": _assignment(
            "management-group",
            VM_PRINCIPAL_ID,
            CONTRIBUTOR_ROLE_ID,
            MANAGEMENT_GROUP_SCOPE,
        ),
        "group": _assignment("group", TRANSITIVE_GROUP_ID, CONTRIBUTOR_ROLE_ID, ACCOUNT_SCOPE),
        "eligible": _assignment(
            "eligible",
            VM_PRINCIPAL_ID,
            CONTRIBUTOR_ROLE_ID,
            ACCOUNT_SCOPE,
            eligible=True,
        ),
        "custom": _assignment("custom", VM_PRINCIPAL_ID, "custom-blob-role", CONTAINER_SCOPE),
        "subtracted": _assignment("subtracted", VM_PRINCIPAL_ID, "custom-not-data-role", CONTAINER_SCOPE),
    }
    try:
        assignments = cast(list[dict[str, object]], value["assignments"])
        assignments.append(additions[addition])
    except KeyError as error:
        raise ValueError("unknown authorization addition") from error
    return value


def authorization_failure_case(failure: str, *, required_role: str = "reader") -> dict[str, object]:
    value = deepcopy(authorization_case(required_role))
    failure_fields = {
        "enumeration": "enumeration_complete",
        "group": "groups_resolved",
        "scope": "scopes_resolved",
        "role": "roles_resolved",
    }
    try:
        value[failure_fields[failure]] = False
    except KeyError as error:
        raise ValueError("unknown authorization failure") from error
    return value

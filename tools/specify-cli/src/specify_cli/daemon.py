from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import tempfile
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol, Self

from specify_cli.daemon_protocol import (
    AuditReceipt,
    ClientResponse,
    Handshake,
    ListRequest,
    decode_message,
    encode_message,
)
from specify_cli.extensions.models import ExtensionListEntry
from specify_cli.extensions.rendering import render_entries

_EXECUTION_MODES = {"local-synthetic", "sovereign"}
_AU_LOCATIONS = {"australiaeast", "australiasoutheast"}


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SovereignBoundary:
    vm_location: str
    encrypted_temp: bool
    immutable_ledger: bool
    peer_authenticated: bool
    fake_transport: bool = False

    def replaced(self, **changes: object) -> Self:
        return replace(self, **changes)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class LocalBoundary:
    owner_only_temp: bool
    peer_authenticated: bool
    synthetic_mode: bool
    ephemeral_journal: bool


def validate_runtime_boundary(execution_mode: str, boundary: LocalBoundary | SovereignBoundary) -> None:
    if execution_mode not in _EXECUTION_MODES:
        raise PermissionError("execution mode is invalid")
    if execution_mode == "local-synthetic":
        if not isinstance(boundary, LocalBoundary):
            raise PermissionError("cross-mode runtime boundary is forbidden")
        if not boundary.owner_only_temp:
            raise PermissionError("local temporary storage must be owner-only")
        if not boundary.peer_authenticated:
            raise PermissionError("local IPC peer must be authenticated")
        if not boundary.synthetic_mode:
            raise PermissionError("local data access requires synthetic mode")
        if not boundary.ephemeral_journal:
            raise PermissionError("local audit journal must be ephemeral")
        return
    if not isinstance(boundary, SovereignBoundary):
        raise PermissionError("cross-mode runtime boundary is forbidden")
    if boundary.vm_location not in _AU_LOCATIONS:
        raise PermissionError("sovereign VM must be in an allowed Australian region")
    if not boundary.encrypted_temp:
        raise PermissionError("sovereign temporary storage must be encrypted")
    if not boundary.immutable_ledger:
        raise PermissionError("sovereign audit requires an immutable ledger")
    if not boundary.peer_authenticated:
        raise PermissionError("sovereign IPC peer must be authenticated")


class AuditJournal(Protocol):
    def append(self, phase: str, event: Mapping[str, object]) -> Mapping[str, object]: ...


class LocalAuditJournal:
    def __init__(self, path: Path, *, session_id: str, execution_mode: str) -> None:
        if execution_mode != "local-synthetic":
            raise ValueError("local audit journal is local-synthetic only")
        self.path = path
        self.session_id = session_id
        self.execution_mode = execution_mode
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            self.path.parent.chmod(0o700)

    def read_records(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        records: list[dict[str, object]] = []
        for line in self.path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b"\n"):
                raise RuntimeError("audit journal record is not LF terminated")
            value = json.loads(line)
            if not isinstance(value, dict) or _canonical_json(value) + b"\n" != line:
                raise RuntimeError("audit journal record is not canonical JSON")
            records.append(value)
        return records

    def append(self, phase: str, event: Mapping[str, object]) -> Mapping[str, object]:
        if phase not in {"intent", "result"}:
            raise ValueError("audit phase is invalid")
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        with lock_path.open("a+b") as lock:
            if os.name == "nt":
                import msvcrt

                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                os.chmod(lock_path, 0o600)
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
            try:
                records = self.read_records()
                previous = records[-1]["event_digest"] if records else None
                record = {
                    **event,
                    "execution_mode": self.execution_mode,
                    "phase": phase,
                    "previous_event_digest": previous,
                    "sequence": len(records) + 1,
                    "session_id": self.session_id,
                }
                record["event_digest"] = hashlib.sha256(_canonical_json(record)).hexdigest()
                with self.path.open("ab") as journal:
                    journal.write(_canonical_json(record) + b"\n")
                    journal.flush()
                    os.fsync(journal.fileno())
                if os.name != "nt":
                    os.chmod(self.path, 0o600)
                return record
            finally:
                if os.name == "nt":
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


class _MemoryAuditJournal:
    def __init__(self, session_id: str, execution_mode: str) -> None:
        self.session_id = session_id
        self.execution_mode = execution_mode

    def append(self, phase: str, event: Mapping[str, object]) -> Mapping[str, object]:
        return {
            **event,
            "execution_mode": self.execution_mode,
            "phase": phase,
            "session_id": self.session_id,
        }


def _audit_response(
    request: ListRequest,
    *,
    session_id: str,
    execution_mode: str,
    operation: Callable[[], str | tuple[str, str]],
    journal: AuditJournal,
) -> ClientResponse:
    intent_id = str(uuid.uuid4())
    journal.append(
        "intent",
        {
            "event_id": intent_id,
            "operation": "extension.list",
            "view": request.view,
        },
    )
    try:
        result = operation()
        if isinstance(result, tuple):
            stdout, stderr = result
        else:
            stdout = result
            stderr = ""
        exit_code = 0
        outcome = "succeeded"
    except Exception as error:
        stdout = ""
        stderr = f"{error}\n"
        exit_code = 1
        outcome = "failed"
    result_id = str(uuid.uuid4())
    journal.append(
        "result",
        {
            "event_id": result_id,
            "intent_event_id": intent_id,
            "operation": "extension.list",
            "outcome": outcome,
            "view": request.view,
        },
    )
    return ClientResponse(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        audit=AuditReceipt(intent_event_id=intent_id, result_event_id=result_id, outcome=outcome),
    )


def handle_installed_request(
    request: ListRequest,
    *,
    session_id: str,
    execution_mode: str,
    inventory_loader: Callable[[Path], Sequence[ExtensionListEntry]],
    journal: AuditJournal | None = None,
) -> ClientResponse:
    if execution_mode not in _EXECUTION_MODES:
        raise PermissionError("execution mode is invalid")
    active_journal = journal if journal is not None else _MemoryAuditJournal(session_id, execution_mode)

    def operation() -> str:
        entries = inventory_loader(request.discovery_start)
        return render_entries(entries, view=request.view, output_json=request.output_json)

    return _audit_response(
        request,
        session_id=session_id,
        execution_mode=execution_mode,
        operation=operation,
        journal=active_journal,
    )


def handle_extension_request(
    request: ListRequest,
    *,
    session_id: str,
    execution_mode: str,
    installed_loader: Callable[[Path], Sequence[ExtensionListEntry]],
    catalog_loader: Callable[[Path], object],
    journal: AuditJournal | None = None,
) -> ClientResponse:
    if execution_mode not in _EXECUTION_MODES:
        raise PermissionError("execution mode is invalid")
    active_journal = journal if journal is not None else _MemoryAuditJournal(session_id, execution_mode)

    def operation() -> tuple[str, str]:
        installed = tuple(installed_loader(request.discovery_start))
        if request.view == "installed":
            return render_entries(installed, view=request.view, output_json=request.output_json), ""

        from specify_cli.extensions.inventory import reconcile_entries

        collection = catalog_loader(request.discovery_start)
        catalog_records = getattr(collection, "records", None)
        warning = getattr(collection, "warning", None)
        if not isinstance(catalog_records, tuple) or (warning is not None and not isinstance(warning, str)):
            raise ValueError("catalog loader result is invalid")
        if warning is not None:
            fallback = () if request.view == "available" else installed
            return render_entries(fallback, view=request.view, output_json=request.output_json), warning + "\n"
        reconciled = reconcile_entries(installed, catalog_records)
        if request.view == "available":
            reconciled = tuple(entry for entry in reconciled if entry.source.kind in {"catalog", "combined"})
        return render_entries(reconciled, view=request.view, output_json=request.output_json), ""

    return _audit_response(
        request,
        session_id=session_id,
        execution_mode=execution_mode,
        operation=operation,
        journal=active_journal,
    )


def _parse_request(payload: bytes) -> ListRequest:
    return ListRequest.from_mapping(decode_message(payload))


def _default_inventory_loader(start: Path) -> Sequence[ExtensionListEntry]:
    from specify_cli.extensions.inventory import discover_project

    context = discover_project(start)
    if context.project_root is None:
        return []
    raise PermissionError("live extension inventory is unavailable in the foundational daemon")


def _handshake_from_environment(environment: Mapping[str, str]) -> Handshake:
    required = (
        "SPEC001_SESSION_ID",
        "SPEC001_EXECUTION_MODE",
        "SPEC001_REPOSITORY_DIGEST",
        "SPEC001_TEMP_POLICY",
        "SPEC001_AUDIT_HEAD",
        "SPEC001_PEER_IDENTITY",
    )
    missing = [name for name in required if not environment.get(name)]
    if missing:
        raise RuntimeError(f"daemon binding is incomplete: {', '.join(missing)}")
    return Handshake(
        protocol_version="1.0",
        peer_identity=environment["SPEC001_PEER_IDENTITY"],
        session_id=environment["SPEC001_SESSION_ID"],
        execution_mode=environment["SPEC001_EXECUTION_MODE"],
        repository_digest=environment["SPEC001_REPOSITORY_DIGEST"],
        temp_policy=environment["SPEC001_TEMP_POLICY"],
        audit_head=environment["SPEC001_AUDIT_HEAD"],
    )


def _serve_unix(endpoint: Path, handshake: Handshake) -> None:
    endpoint.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if endpoint.exists():
        endpoint.unlink()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:  # type: ignore[attr-defined]
        server.bind(str(endpoint))
        endpoint.chmod(0o600)
        server.listen()
        while True:
            connection, _ = server.accept()
            with connection, connection.makefile("rwb", buffering=0) as stream:
                request = _parse_request(stream.readline())
                journal_path = Path(tempfile.gettempdir()) / f"ama-specify-{handshake.session_id}" / "audit.ndjson"
                response = handle_installed_request(
                    request,
                    session_id=handshake.session_id,
                    execution_mode=handshake.execution_mode,
                    inventory_loader=_default_inventory_loader,
                    journal=LocalAuditJournal(
                        journal_path,
                        session_id=handshake.session_id,
                        execution_mode=handshake.execution_mode,
                    )
                    if handshake.execution_mode == "local-synthetic"
                    else None,
                )
                stream.write(encode_message(handshake))
                stream.write(encode_message(response))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--endpoint", required=True)
    arguments = parser.parse_args(argv)
    handshake = _handshake_from_environment(os.environ)
    if os.name == "nt":
        raise RuntimeError("Windows named-pipe serving requires the secured native pipe host")
    _serve_unix(Path(arguments.endpoint), handshake)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

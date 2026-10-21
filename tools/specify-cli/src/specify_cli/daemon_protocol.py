from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Self, cast

PROTOCOL_VERSION = "1.0"
_EXECUTION_MODES = {"local-synthetic", "sovereign"}
_VIEWS = {"installed", "available", "all"}


class ProtocolError(ValueError):
    pass


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProtocolError(f"{label} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class AuditReceipt:
    intent_event_id: str
    result_event_id: str
    outcome: str

    def __post_init__(self) -> None:
        _require_text(self.intent_event_id, "audit intent event id")
        _require_text(self.result_event_id, "audit result event id")
        if self.intent_event_id == self.result_event_id:
            raise ProtocolError("audit receipt event ids must be distinct")
        if self.outcome not in {"succeeded", "failed", "blocked"}:
            raise ProtocolError("audit receipt outcome is invalid")


@dataclass(frozen=True, slots=True)
class ListRequest:
    view: str
    output_json: bool
    discovery_start: Path
    protocol_version: str = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION:
            raise ProtocolError("protocol version mismatch")
        if self.view not in _VIEWS:
            raise ProtocolError("request view is invalid")
        if not isinstance(self.output_json, bool):
            raise ProtocolError("output json must be boolean")
        if not isinstance(self.discovery_start, Path):
            raise ProtocolError("discovery start must be a path")

    def to_mapping(self) -> dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "view": self.view,
            "output_json": self.output_json,
            "discovery_start": str(self.discovery_start),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self:
        expected = {"protocol_version", "view", "output_json", "discovery_start"}
        if set(value) != expected:
            raise ProtocolError("request fields are invalid")
        return cls(
            protocol_version=_require_text(value["protocol_version"], "protocol version"),
            view=_require_text(value["view"], "request view"),
            output_json=cast(bool, value["output_json"]),
            discovery_start=Path(_require_text(value["discovery_start"], "discovery start")),
        )


@dataclass(frozen=True, slots=True)
class ClientResponse:
    stdout: str
    stderr: str
    exit_code: int
    audit: AuditReceipt | None
    protocol_version: str = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION:
            raise ProtocolError("protocol version mismatch")
        if not isinstance(self.stdout, str) or not isinstance(self.stderr, str):
            raise ProtocolError("response streams must be strings")
        if not isinstance(self.exit_code, int) or isinstance(self.exit_code, bool) or self.exit_code not in {0, 1, 2}:
            raise ProtocolError("response exit code is invalid")

    def to_mapping(self) -> dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "audit": asdict(self.audit) if self.audit is not None else None,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self:
        expected = {"protocol_version", "stdout", "stderr", "exit_code", "audit"}
        if set(value) != expected:
            raise ProtocolError("response fields are invalid")
        raw_audit = value["audit"]
        audit: AuditReceipt | None
        if raw_audit is None:
            audit = None
        elif isinstance(raw_audit, Mapping) and set(raw_audit) == {"intent_event_id", "result_event_id", "outcome"}:
            audit = AuditReceipt(
                intent_event_id=_require_text(raw_audit["intent_event_id"], "audit intent event id"),
                result_event_id=_require_text(raw_audit["result_event_id"], "audit result event id"),
                outcome=_require_text(raw_audit["outcome"], "audit outcome"),
            )
        else:
            raise ProtocolError("audit receipt fields are invalid")
        return cls(
            protocol_version=_require_text(value["protocol_version"], "protocol version"),
            stdout=cast(str, value["stdout"]),
            stderr=cast(str, value["stderr"]),
            exit_code=cast(int, value["exit_code"]),
            audit=audit,
        )


@dataclass(frozen=True, slots=True)
class Handshake:
    protocol_version: str
    peer_identity: str
    session_id: str
    execution_mode: str
    repository_digest: str
    temp_policy: str
    audit_head: str

    def __post_init__(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION:
            raise ProtocolError("protocol version mismatch")
        _require_text(self.peer_identity, "peer identity")
        _require_text(self.session_id, "session id")
        if self.execution_mode not in _EXECUTION_MODES:
            raise ProtocolError("execution mode is invalid")
        for digest, label in (
            (self.repository_digest, "repository digest"),
            (self.audit_head, "audit head"),
        ):
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
                raise ProtocolError(f"{label} must be lowercase SHA-256")
        _require_text(self.temp_policy, "temp policy")

    def replaced(self, **changes: object) -> Handshake:
        unexpected = set(changes) - set(self.__dataclass_fields__)
        if unexpected:
            raise TypeError(f"unexpected handshake fields: {sorted(unexpected)}")
        replacement = object.__new__(Handshake)
        for field_name in self.__dataclass_fields__:
            object.__setattr__(replacement, field_name, changes.get(field_name, getattr(self, field_name)))
        return replacement


def validate_handshake(actual: Handshake, expected: Handshake) -> None:
    for field_name in (
        "protocol_version",
        "peer_identity",
        "session_id",
        "execution_mode",
        "repository_digest",
        "temp_policy",
        "audit_head",
    ):
        if getattr(actual, field_name) != getattr(expected, field_name):
            raise ProtocolError(f"{field_name.replace('_', ' ')} mismatch")


def validate_client_response(response: ClientResponse) -> None:
    if response.audit is None:
        raise ProtocolError("response requires a linked audit receipt")
    expected_outcome = "succeeded" if response.exit_code == 0 else "failed"
    if response.audit.outcome != expected_outcome:
        raise ProtocolError("audit receipt outcome does not match response")


def encode_message(value: ListRequest | ClientResponse | Handshake) -> bytes:
    if isinstance(value, ListRequest | ClientResponse):
        payload = value.to_mapping()
    else:
        payload = asdict(value)
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"


def decode_message(payload: bytes) -> Mapping[str, Any]:
    if not payload.endswith(b"\n") or payload.count(b"\n") != 1:
        raise ProtocolError("protocol message must contain one line")
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("protocol message is not valid JSON") from error
    if not isinstance(value, Mapping):
        raise ProtocolError("protocol message must be an object")
    return value

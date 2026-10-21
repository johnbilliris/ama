from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import cast

_EVIDENCE_FIELDS = {"kind", "source_sha256", "source_ordinal", "record_sha256"}
_ENTRY_FIELDS = {
    "id",
    "fallback_identity",
    "source_locations",
    "name",
    "description",
    "version",
    "priority",
    "enabled",
    "source",
    "evidence",
    "provides",
    "install_allowed",
    "installed",
    "installed_version",
    "available_versions",
    "activation_state",
    "activation_diagnostic",
    "health",
    "conflict",
    "conflict_reasons",
    "catalog_sources",
}


def _closed_mapping(value: object, expected: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError(f"{label} fields must be exactly {sorted(expected)}")
    return value


def _tuple_of_strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be an array of strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must be unique")
    return tuple(value)


def _is_absolute(value: str) -> bool:
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    source: str | None

    @classmethod
    def from_mapping(cls, value: object) -> Diagnostic:
        mapping = _closed_mapping(value, {"code", "message", "source"}, "diagnostic")
        code = mapping["code"]
        message = mapping["message"]
        source = mapping["source"]
        if not isinstance(code, str) or not code or not isinstance(message, str) or not message:
            raise ValueError("diagnostic code and message must be non-empty")
        if source is not None and not isinstance(source, str):
            raise ValueError("diagnostic source must be a string or null")
        if source is not None and _is_absolute(source):
            raise ValueError("diagnostic source must be project-relative")
        return cls(code=code, message=message, source=source)


@dataclass(frozen=True, slots=True)
class HealthAssessment:
    state: str
    diagnostics: tuple[Diagnostic, ...]

    @classmethod
    def from_mapping(cls, value: object) -> HealthAssessment:
        mapping = _closed_mapping(value, {"state", "diagnostics"}, "health")
        state = mapping["state"]
        raw_diagnostics = mapping["diagnostics"]
        if state not in {"healthy", "invalid"} or not isinstance(raw_diagnostics, list):
            raise ValueError("health shape is invalid")
        diagnostics = tuple(Diagnostic.from_mapping(item) for item in raw_diagnostics)
        if state == "healthy" and diagnostics:
            raise ValueError("healthy health cannot contain diagnostics")
        if state == "invalid" and not diagnostics:
            raise ValueError("invalid health requires diagnostics")
        if len(diagnostics) != len(set(diagnostics)):
            raise ValueError("health diagnostics must be unique")
        return cls(state=state, diagnostics=diagnostics)


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    kind: str

    @classmethod
    def from_mapping(cls, value: object) -> SourceDescriptor:
        mapping = _closed_mapping(value, {"kind"}, "source")
        kind = mapping["kind"]
        if kind not in {"local", "catalog", "combined"}:
            raise ValueError("source kind is invalid")
        return cls(kind=kind)


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    kind: str
    source_sha256: str
    source_ordinal: int
    record_sha256: str

    @classmethod
    def from_mapping(cls, value: object) -> SourceEvidence:
        mapping = _closed_mapping(value, _EVIDENCE_FIELDS, "source evidence")
        kind = mapping["kind"]
        source_sha256 = mapping["source_sha256"]
        source_ordinal = mapping["source_ordinal"]
        record_sha256 = mapping["record_sha256"]
        if kind not in {"local", "catalog"}:
            raise ValueError("source evidence kind is invalid")
        for digest in (source_sha256, record_sha256):
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError("source evidence digest must be lowercase SHA-256")
        if not isinstance(source_ordinal, int) or isinstance(source_ordinal, bool) or source_ordinal < 0:
            raise ValueError("source evidence ordinal must be non-negative")
        return cls(
            kind=kind,
            source_sha256=cast(str, source_sha256),
            source_ordinal=source_ordinal,
            record_sha256=cast(str, record_sha256),
        )


@dataclass(frozen=True, slots=True)
class CapabilityCounts:
    commands: int
    templates: int
    scripts: int
    hooks: int

    @classmethod
    def from_mapping(cls, value: object) -> CapabilityCounts:
        mapping = _closed_mapping(value, {"commands", "templates", "scripts", "hooks"}, "provides")
        counts = tuple(mapping[field] for field in ("commands", "templates", "scripts", "hooks"))
        if not all(isinstance(count, int) and not isinstance(count, bool) and count >= 0 for count in counts):
            raise ValueError("capability counts must be non-negative integers")
        return cls(
            commands=cast(int, counts[0]),
            templates=cast(int, counts[1]),
            scripts=cast(int, counts[2]),
            hooks=cast(int, counts[3]),
        )


@dataclass(frozen=True, slots=True)
class ExtensionListEntry:
    id: str | None
    fallback_identity: str | None
    source_locations: tuple[str, ...]
    name: str
    description: str | None
    version: str
    priority: int | None
    enabled: bool | None
    source: SourceDescriptor
    evidence: tuple[SourceEvidence, ...]
    provides: CapabilityCounts
    install_allowed: bool | None
    installed: bool
    installed_version: str | None
    available_versions: tuple[str, ...]
    activation_state: str | None
    activation_diagnostic: str | None
    health: HealthAssessment
    conflict: bool
    conflict_reasons: tuple[str, ...]
    catalog_sources: tuple[str, ...]


def _validate_entry(entry: ExtensionListEntry) -> None:
    if any(_is_absolute(location) for location in entry.source_locations):
        raise ValueError("source locations must be project-relative")
    if entry.conflict and not entry.conflict_reasons:
        raise ValueError("conflict requires reasons")
    if not entry.conflict and entry.conflict_reasons:
        raise ValueError("non-conflict cannot contain reasons")
    if entry.conflict and len(entry.evidence) < 2:
        raise ValueError("conflict requires at least two evidence items")
    if (entry.activation_state == "activation-failed") != bool(entry.activation_diagnostic):
        raise ValueError("activation diagnostic must exist only for activation-failed")
    evidence_kinds = {item.kind for item in entry.evidence}
    if entry.source.kind == "local":
        if (
            not entry.installed
            or evidence_kinds != {"local"}
            or entry.catalog_sources
            or entry.install_allowed is not None
        ):
            raise ValueError("local source and evidence kind disagree")
    elif entry.source.kind == "catalog":
        if entry.installed:
            raise ValueError("catalog source cannot be installed")
        if evidence_kinds != {"catalog"} or entry.source_locations or entry.install_allowed is None:
            raise ValueError("catalog source and evidence kind disagree")
    elif evidence_kinds != {"local", "catalog"}:
        raise ValueError("combined source requires local and catalog evidence kind values")
    if entry.id is None:
        if not entry.fallback_identity or entry.source.kind != "local" or entry.health.state != "invalid":
            raise ValueError("fallback identity requires invalid local metadata")
    elif entry.fallback_identity is not None:
        raise ValueError("fallback identity is only valid without a stable id")


def project_entry(value: Mapping[str, object]) -> ExtensionListEntry:
    mapping = _closed_mapping(value, _ENTRY_FIELDS, "extension entry")
    raw_evidence = mapping["evidence"]
    if not isinstance(raw_evidence, list) or not raw_evidence:
        raise ValueError("evidence must be non-empty")
    evidence = tuple(
        sorted(
            (SourceEvidence.from_mapping(item) for item in raw_evidence),
            key=lambda item: (item.kind, item.source_sha256, item.source_ordinal, item.record_sha256),
        )
    )
    identifier = mapping["id"]
    fallback_identity = mapping["fallback_identity"]
    if identifier is not None and not isinstance(identifier, str):
        raise ValueError("id must be a string or null")
    if fallback_identity is not None and not isinstance(fallback_identity, str):
        raise ValueError("fallback identity must be a string or null")
    entry = ExtensionListEntry(
        id=identifier,
        fallback_identity=fallback_identity,
        source_locations=_tuple_of_strings(mapping["source_locations"], "source locations"),
        name=str(mapping["name"]),
        description=mapping["description"] if isinstance(mapping["description"], str) else None,
        version=str(mapping["version"]),
        priority=mapping["priority"] if isinstance(mapping["priority"], int) else None,
        enabled=mapping["enabled"] if isinstance(mapping["enabled"], bool) else None,
        source=SourceDescriptor.from_mapping(mapping["source"]),
        evidence=evidence,
        provides=CapabilityCounts.from_mapping(mapping["provides"]),
        install_allowed=mapping["install_allowed"] if isinstance(mapping["install_allowed"], bool) else None,
        installed=bool(mapping["installed"]),
        installed_version=mapping["installed_version"] if isinstance(mapping["installed_version"], str) else None,
        available_versions=_tuple_of_strings(mapping["available_versions"], "available versions"),
        activation_state=mapping["activation_state"] if isinstance(mapping["activation_state"], str) else None,
        activation_diagnostic=mapping["activation_diagnostic"]
        if isinstance(mapping["activation_diagnostic"], str)
        else None,
        health=HealthAssessment.from_mapping(mapping["health"]),
        conflict=bool(mapping["conflict"]),
        conflict_reasons=_tuple_of_strings(mapping["conflict_reasons"], "conflict reasons"),
        catalog_sources=_tuple_of_strings(mapping["catalog_sources"], "catalog sources"),
    )
    _validate_entry(entry)
    return entry


def serialize_entries(entries: Sequence[ExtensionListEntry]) -> str:
    return json.dumps([asdict(entry) for entry in entries], ensure_ascii=True, separators=(",", ":")) + "\n"
